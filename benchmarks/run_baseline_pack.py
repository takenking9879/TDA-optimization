#!/usr/bin/env python3
"""Phase-3 baselines: giotto-ph, GUDHI, post-freeze adversarial families.

Hardware: 4 CPU / 16 GB. Budget 12 s per run. Ripser is 1 thread.
giotto-ph 0.2.4 is AGPL — called as a pip oracle only (n_threads=1 and 4).
Empirical, not a theorem.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (  # noqa: E402
    circle_noisy,
    disconnected_circles,
    figure8,
    grid_holes,
    many_loops,
    mixed_1d2d3d,
    nested_loops,
    nonuniform_circle,
    random_geometric,
    sphere,
    torus,
    two_spheres_apart,
    uniform,
    write_csv,
)
from ph_metrics import ess  # noqa: E402
from run_consolidation import (  # noqa: E402
    GIOTTO_VER,
    GUDHI_VER,
    HAVE_GIOTTO,
    HAVE_GUDHI,
    OUT,
    local_exp,
    run_estimate,
    run_giotto,
    run_gudhi_alpha,
    run_gudhi_rips,
    run_ripser,
    strip_pairs,
)
from run_consolidation_limits import cloud, run_pith, topology_metrics  # noqa: E402
from run_suite import compare  # noqa: E402

BUDGET_S = 12
NPROC = os.cpu_count() or 4
CLOUDS = BENCH / "datasets" / "generated"


def _ok(run):
    return bool(run and run.get("ok") and run.get("wall_s"))


def main():
    rng = np.random.default_rng(3)  # post-freeze seed; not used to retune τ
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "hardware": {
            "cpus": NPROC,
            "budget_s": BUDGET_S,
            "note": "4-CPU / 16GB; Ripser 1 thread; giotto n_threads=1 and 4; PITH --threads 1",
        },
        "gudhi": GUDHI_VER,
        "giotto": GIOTTO_VER,
        "have_gudhi": HAVE_GUDHI,
        "have_giotto": HAVE_GIOTTO,
        "license_note": "giotto-ph is AGPLv3; used as an installed oracle only",
        "comparisons": [],
        "gudhi_limits": [],
        "topology": [],
        "dispatcher_heldout": [],
        "mode_auto_heldout": [],
        "exponents": [],
        "max_practical": [],
    }

    comparisons = [
        # training-ish (already measured; needed for giotto/GUDHI on the same clouds)
        ("circle_noisy", circle_noisy, 1.5, 1, [200, 500, 1000], True, True),
        ("figure8", figure8, 1.1, 1, [500, 1000, 2000], True, False),
        ("sphere", sphere, 1.4, 2, [200, 400], True, True),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, [500, 1000], True, False),
        ("nested_loops", nested_loops, 1.6, 1, [400, 1000], True, False),
        ("many_loops", many_loops, 1.2, 1, [400], True, False),
        ("torus", torus, 1.6, 1, [400, 1000], True, False),
        # held-out / post-freeze
        ("disconnected_circles", disconnected_circles, 1.5, 1, [400, 1000], True, False),
        ("random_geometric_sparse", random_geometric, 0.15, 1, [500, 1000], True, False),
        ("random_geometric_dense", random_geometric, 0.50, 1, [400, 800], True, False),
        ("grid_holes", grid_holes, 0.12, 1, [400, 800], True, False),
        ("two_spheres_apart", two_spheres_apart, 1.4, 2, [300], True, True),
        ("nonuniform_circle", nonuniform_circle, 1.5, 1, [400], True, False),
        ("mixed_1d2d3d", mixed_1d2d3d, 1.4, 2, [300], False, True),
    ]

    dead = set()  # (family, method) after first timeout
    print("=== equal-hardware baselines ===", flush=True)
    for name, fn, T, dim, ns, do_exact, do_scale in comparisons:
        for n in ns:
            path = cloud(name.split("_sparse")[0].split("_dense")[0], n, fn, rng)
            row = {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": dim,
                "held_out": name
                in (
                    "disconnected_circles",
                    "random_geometric_sparse",
                    "random_geometric_dense",
                    "grid_holes",
                    "two_spheres_apart",
                    "nonuniform_circle",
                    "mixed_1d2d3d",
                ),
                "post_freeze": name in ("grid_holes", "two_spheres_apart"),
                "runs": {},
            }
            print(f"BASE {name} n={n} T={T} dim={dim}", flush=True)

            def take(key, runner):
                if (name, key) in dead:
                    row["runs"][key] = {"ok": False, "error": "skipped after prior timeout", "skipped": True}
                    return
                rec = runner()
                row["runs"][key] = strip_pairs(rec) if rec.get("pairs") is not None else rec
                if rec.get("timed_out") or (rec.get("error") and "timed out" in str(rec.get("error")).lower()):
                    dead.add((name, key))
                wall = rec.get("wall_s")
                print(f"  {key} {wall} {rec.get('error') or rec.get('pipeline') or ''}", flush=True)
                return rec

            pith_exact = None
            rip = None
            if do_exact:
                pith_exact = take("pith_exact_t1", lambda: run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S))
                take("pith_redzed_t1", lambda: run_pith(path, T, dim, "exact", "redzed", threads=1, timeout=BUDGET_S))
                rip = take("ripser", lambda: run_ripser(path, T, dim, timeout=BUDGET_S))
                take("giotto_t1", lambda: run_giotto(path, T, dim, n_threads=1, collapse_edges=False, timeout=BUDGET_S))
                take("giotto_t4", lambda: run_giotto(path, T, dim, n_threads=4, collapse_edges=False, timeout=BUDGET_S))
                if n <= 500 and dim <= 1:
                    take(
                        "giotto_t1_collapse",
                        lambda: run_giotto(path, T, dim, n_threads=1, collapse_edges=True, timeout=BUDGET_S),
                    )
                take("gudhi_rips", lambda: run_gudhi_rips(path, T, dim, timeout=BUDGET_S))
            if do_scale or name in ("disconnected_circles", "grid_holes", "two_spheres_apart", "mixed_1d2d3d"):
                take("pith_scale_t1", lambda: run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S))
            if HAVE_GUDHI and n <= 800 and dim <= 2:
                take("gudhi_alpha", lambda: run_gudhi_alpha(path, dim, timeout=BUDGET_S))

            if pith_exact and rip and pith_exact.get("pairs") is not None and rip.get("pairs") is not None:
                try:
                    row["pith_vs_ripser"] = compare(rip["pairs"], pith_exact["pairs"], dim)
                except Exception as e:
                    row["pith_vs_ripser"] = {"error": str(e)}
            gi = row["runs"].get("giotto_t1")
            if rip and gi and rip.get("ok") and gi.get("ok"):
                # pairs were stripped; re-run compare only on small n via topology block
                pass
            report["comparisons"].append(row)

    print("=== topology (n<=400; keep pairs) ===", flush=True)
    for name, fn, T, dim, n in (
        ("circle_noisy", circle_noisy, 1.5, 1, 400),
        ("figure8", figure8, 1.1, 1, 400),
        ("disconnected_circles", disconnected_circles, 1.5, 1, 400),
        ("grid_holes", grid_holes, 0.12, 1, 400),
        ("nonuniform_circle", nonuniform_circle, 1.5, 1, 400),
        ("two_spheres_apart", two_spheres_apart, 1.4, 2, 300),
    ):
        path = cloud(name, n, fn, rng)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
        rip = run_ripser(path, T, dim, timeout=BUDGET_S)
        gio = run_giotto(path, T, dim, n_threads=1, timeout=BUDGET_S) if HAVE_GIOTTO else {}
        gud = run_gudhi_rips(path, T, dim, timeout=BUDGET_S) if HAVE_GUDHI and n <= 400 and dim <= 1 else {}
        scale = run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "ess_ripser": {d: ess(rip.get("pairs"), d) for d in range(dim + 1)} if rip.get("ok") else None,
            "ess_pith": {d: ess(pith.get("pairs"), d) for d in range(dim + 1)} if pith.get("ok") else None,
            "ess_giotto": {d: ess(gio.get("pairs"), d) for d in range(dim + 1)} if gio.get("ok") else None,
            "ess_gudhi": {d: ess(gud.get("pairs"), d) for d in range(dim + 1)} if gud.get("ok") else None,
            "ess_scale": {d: ess(scale.get("pairs"), d) for d in range(dim + 1)} if scale.get("ok") else None,
        }
        if pith.get("ok") and rip.get("ok"):
            rec["pith_vs_ripser"] = topology_metrics(rip["pairs"], pith["pairs"], dim)
        if gio.get("ok") and rip.get("ok"):
            rec["giotto_vs_ripser"] = topology_metrics(rip["pairs"], gio["pairs"], dim)
        if gud.get("ok") and rip.get("ok"):
            rec["gudhi_vs_ripser"] = topology_metrics(rip["pairs"], gud["pairs"], dim)
        if scale.get("ok") and rip.get("ok"):
            rec["scale_vs_ripser"] = topology_metrics(rip["pairs"], scale["pairs"], dim)
        if scale.get("ok") and HAVE_GUDHI:
            alp = run_gudhi_alpha(path, dim, timeout=BUDGET_S)
            rec["ess_alpha"] = {d: ess(alp.get("pairs"), d) for d in range(dim + 1)} if alp.get("ok") else None
            rec["alpha_wall_s"] = alp.get("wall_s")
        print(
            f"  TOPO {name} pith_match={rec.get('pith_vs_ripser', {}).get('exact_match')} "
            f"giotto_match={rec.get('giotto_vs_ripser', {}).get('exact_match')} "
            f"scale_unmatched={rec.get('scale_vs_ripser', {}).get('unmatched')}",
            flush=True,
        )
        report["topology"].append(rec)

    print("=== dispatcher on post-freeze / held-out ===", flush=True)
    for name, fn, T, dim, n in (
        ("disconnected_circles", disconnected_circles, 1.5, 1, 400),
        ("disconnected_circles", disconnected_circles, 1.5, 1, 1000),
        ("random_geometric_sparse", random_geometric, 0.15, 1, 500),
        ("random_geometric_dense", random_geometric, 0.50, 1, 400),
        ("grid_holes", grid_holes, 0.12, 1, 400),
        ("grid_holes", grid_holes, 0.12, 1, 800),
        ("two_spheres_apart", two_spheres_apart, 1.4, 2, 300),
        ("nonuniform_circle", nonuniform_circle, 1.5, 1, 400),
        ("nested_loops", nested_loops, 1.6, 1, 1000),
    ):
        path = cloud(name.split("_sparse")[0].split("_dense")[0], n, fn, rng)
        est = run_estimate(path, T, dim)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
        red = run_pith(path, T, dim, "exact", "redzed", threads=1, timeout=BUDGET_S)
        imp = run_pith(path, T, dim, "exact", "implicit", threads=1, timeout=BUDGET_S)
        times = {
            "redzed": red.get("wall_s"),
            "implicit": imp.get("wall_s"),
        }
        finished = {k: v for k, v in times.items() if v}
        oracle = min(finished, key=finished.get) if finished else None
        rec_e = est.get("engine_recommended")
        waste = None
        if oracle and rec_e in finished and finished[oracle]:
            waste = finished[rec_e] / finished[oracle]
        pipe = auto.get("pipeline") or ""
        picked = "redzed" if "redzed" in pipe else ("implicit" if "collapse" in pipe or "implicit" in pipe else pipe)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "recommended": rec_e,
            "auto_picked": picked,
            "oracle_faster": oracle,
            "wrong": bool(oracle and rec_e and rec_e != oracle),
            "waste_if_follow_estimate": waste,
            "regime": est.get("residual_regime"),
            "exact_feasible": est.get("exact_feasible"),
            "mode_recommended": est.get("mode_recommended"),
            "times": {"auto": auto.get("wall_s"), "redzed": red.get("wall_s"), "implicit": imp.get("wall_s")},
            "pipelines": {"auto": pipe, "redzed": red.get("pipeline"), "implicit": imp.get("pipeline")},
        }
        print(
            f"  DISP {name} n={n} rec={rec_e} oracle={oracle} wrong={rec['wrong']} waste={waste}",
            flush=True,
        )
        report["dispatcher_heldout"].append(rec)

        # --mode auto executes the probe
        import subprocess

        proc = subprocess.run(
            [
                str(Path(BENCH.parent) / "src/pith/build/pith"),
                "--points",
                str(path),
                "--mode",
                "auto",
                "--maxdim",
                str(dim),
                "--threshold",
                str(T),
                "--no-enclosing",
                "--threads",
                "1",
            ],
            text=True,
            capture_output=True,
            timeout=BUDGET_S,
            check=False,
        )
        selected = None
        for line in proc.stderr.splitlines():
            if line.startswith("# MODE auto selected"):
                selected = line.split()[4]
        report["mode_auto_heldout"].append(
            {
                "name": name,
                "n": n,
                "selected": selected,
                "ok": proc.returncode == 0,
                "mode_recommended": est.get("mode_recommended"),
                "match_probe": selected == est.get("mode_recommended"),
            }
        )

    # Local exponents + practical max n for giotto/GUDHI on the new receipts
    by = {}
    for r in report["comparisons"]:
        by.setdefault((r["name"], r["maxdim"], r["T"]), []).append(r)
    for key, rows in by.items():
        rows = sorted(rows, key=lambda x: x["n"])
        for meth in (
            "pith_exact_t1",
            "pith_redzed_t1",
            "ripser",
            "giotto_t1",
            "giotto_t4",
            "gudhi_rips",
            "pith_scale_t1",
        ):
            pts = []
            last_ok = None
            first_fail = None
            for r in rows:
                run = r["runs"].get(meth)
                if _ok(run):
                    pts.append((r["n"], run["wall_s"]))
                    last_ok = (r["n"], run["wall_s"])
                elif run and not run.get("skipped"):
                    first_fail = first_fail or r["n"]
            for i in range(len(pts) - 1):
                report["exponents"].append(
                    {
                        "name": key[0],
                        "method": meth,
                        "n0": pts[i][0],
                        "n1": pts[i + 1][0],
                        "p_time": local_exp(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]),
                    }
                )
            if last_ok or first_fail:
                report["max_practical"].append(
                    {
                        "name": key[0],
                        "maxdim": key[1],
                        "T": key[2],
                        "method": meth,
                        "max_n_ok": last_ok[0] if last_ok else None,
                        "wall_at_max": last_ok[1] if last_ok else None,
                        "first_fail_n": first_fail,
                    }
                )

    path = OUT / "baselines.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {path}", flush=True)

    print("\n=== 1-thread wall (PITH / Ripser / giotto / GUDHI) ===")
    for r in report["comparisons"]:
        bits = []
        for k in ("pith_exact_t1", "ripser", "giotto_t1", "giotto_t4", "gudhi_rips"):
            run = r["runs"].get(k) or {}
            if run.get("wall_s"):
                bits.append(f"{k}={run['wall_s']:.3f}")
            elif run.get("error"):
                bits.append(f"{k}=FAIL")
        print(f"{r['name']:28} n={r['n']:5} " + " ".join(bits))


if __name__ == "__main__":
    main()
