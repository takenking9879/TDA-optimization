#!/usr/bin/env python3
"""Consolidation runner: scaling, dispatcher, topology, local exponents.

Hardware note: this Cloud image is 4 CPUs / 16 GB. Ripser is 1 thread.
PITH uses std::thread for a few scans (hardware_concurrency, typically 4).
GUDHI Rips (if importable) is treated as 1 thread. Times are wall-clock;
CPU-time is ru_utime+ru_stime of the child. Empirical, not a theorem.
"""

from __future__ import annotations

import json
import math
import os
import resource
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (  # noqa: E402
    GENERATORS,
    anisotropic_blob,
    blobs,
    circle_noisy,
    clustered,
    heavy_noise_circle,
    many_loops,
    nested_loops,
    sphere,
    torus,
    uniform,
    write_csv,
)
from run_suite import PITH, RIPSER, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import figure8  # noqa: E402
from run_wave95 import ess  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
NPROC = os.cpu_count() or 4

try:
    import gudhi  # type: ignore

    HAVE_GUDHI = True
    GUDHI_VER = getattr(gudhi, "__version__", "?")
except Exception:
    HAVE_GUDHI = False
    GUDHI_VER = None

HAVE_GIOTTO = False
try:
    import gtda  # type: ignore

    HAVE_GIOTTO = True
    GIOTTO_VER = getattr(gtda, "__version__", "?")
except Exception:
    GIOTTO_VER = None


def local_exp(n0, t0, n1, t1):
    if not t0 or not t1 or n0 <= 0 or n1 <= n0:
        return None
    return math.log(t1 / t0) / math.log(n1 / n0)


def _rss_child():
    try:
        return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024
    except Exception:
        return 0


def run_pith(path, T, maxdim, mode="exact", engine="auto", timeout=25):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        mode,
        "--engine",
        engine,
        "--no-enclosing",
    ]
    rss0 = _rss_child()
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, None, str(e)
    cpu = None
    try:
        ru = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = ru.ru_utime + ru.ru_stime
    except Exception:
        pass
    rss1 = _rss_child()
    return {
        "method": f"pith:{mode}:{engine}",
        "ok": err is None,
        "error": err,
        "wall_s": dt,
        "cpu_s": cpu,
        "threads_claimed": NPROC if mode in ("exact", "scale") else 1,
        "rss_delta": max(0, rss1 - rss0),
        "rss_pith": c.get("rss") if c else None,
        "n_dist": c.get("distances"),
        "metric_ms": c.get("metric_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "pipeline": c.get("pipeline"),
        "n_pairs": len(pairs) if pairs else 0,
        "ess0": ess(pairs, 0) if pairs else None,
        "ess1": ess(pairs, 1) if pairs else None,
        "ess2": ess(pairs, 2) if pairs else None,
        "pairs": pairs,
        "counters": c,
    }


def run_estimate(path, T, maxdim, timeout=20):
    cmd = [
        str(PITH),
        "--estimate",
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--format",
        "json",
    ]
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        est = json.loads(out)
        est["wall_s"] = dt
        return est
    except Exception as e:
        return {"error": str(e)}


def run_ripser(path, T, maxdim, timeout=25):
    cmd = [str(RIPSER), "--format", "point-cloud", "--dim", str(maxdim), "--threshold", str(T), str(path)]
    rss0 = _rss_child()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        from run_suite import parse_ripser  # noqa: WPS433

        pairs = parse_ripser(out)
        err = None
    except Exception as e:
        pairs, dt, err = [], None, str(e)
    rss1 = _rss_child()
    return {
        "method": "ripser",
        "ok": err is None,
        "error": err,
        "wall_s": dt,
        "threads_claimed": 1,
        "rss_delta": max(0, rss1 - rss0),
        "n_pairs": len(pairs) if pairs else 0,
        "ess0": ess(pairs, 0) if pairs else None,
        "ess1": ess(pairs, 1) if pairs else None,
        "ess2": ess(pairs, 2) if pairs else None,
        "pairs": pairs,
    }


def run_gudhi_rips(path, T, maxdim, timeout=25):
    if not HAVE_GUDHI:
        return {"method": "gudhi-rips", "ok": False, "error": "gudhi not importable"}
    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    try:
        st = gudhi.RipsComplex(points=pts, max_edge_length=float(T)).create_simplex_tree(
            max_dimension=maxdim + 1
        )
        pers = st.persistence()
        dt = time.perf_counter() - t0
        pairs = []
        for dim, (b, d) in pers:
            if dim > maxdim:
                continue
            pairs.append({"dim": dim, "birth": b, "death": d if d != float("inf") else float("inf")})
        return {
            "method": "gudhi-rips",
            "ok": True,
            "wall_s": dt,
            "threads_claimed": 1,
            "n_pairs": len(pairs),
            "ess0": ess(pairs, 0),
            "ess1": ess(pairs, 1),
            "ess2": ess(pairs, 2),
            "pairs": pairs,
        }
    except Exception as e:
        return {"method": "gudhi-rips", "ok": False, "error": str(e), "wall_s": time.perf_counter() - t0}


def cloud(name, n, fn, rng):
    CLOUDS.mkdir(parents=True, exist_ok=True)
    path = CLOUDS / f"{name}_n{n}.csv"
    if not path.exists():
        write_csv(path, fn(n, rng))
    return path


def strip_pairs(rec):
    rec = dict(rec)
    rec.pop("pairs", None)
    rec.pop("counters", None)
    return rec


def main():
    rng = np.random.default_rng(0)
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []

    scaling = [
        # training families
        ("circle_noisy", circle_noisy, 1.5, 1, [200, 500, 1000], ["exact-auto", "ripser", "gudhi"]),
        ("figure8", figure8, 1.1, 1, [200, 500, 1000, 2000], ["exact-auto", "ripser", "scale"]),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, [500, 1000, 2000], ["exact-auto", "ripser"]),
        ("blobs", blobs, 1.0, 0, [1000, 4000, 12000], ["exact-auto", "ripser"]),
        ("sphere", sphere, 1.4, 2, [200, 400], ["exact-auto", "ripser", "scale"]),
        ("sphere", sphere, 1.4, 2, [4000, 16000, 50000], ["scale"]),
        ("figure8", figure8, 1.1, 1, [8000, 16000], ["scale"]),
        # T-sweep
        ("circle_T", circle_noisy, 0.6, 1, [400], ["exact-auto", "ripser"]),
        ("circle_T", circle_noisy, 1.0, 1, [400], ["exact-auto", "ripser"]),
        ("circle_T", circle_noisy, 1.5, 1, [400], ["exact-auto", "ripser"]),
        # held-out
        ("many_loops", many_loops, 1.2, 1, [400], ["exact-auto", "ripser", "scale"]),
        ("nested_loops", nested_loops, 1.6, 1, [400], ["exact-auto", "ripser", "scale"]),
        ("clustered", clustered, 0.8, 1, [400], ["exact-auto", "ripser"]),
        ("heavy_noise_circle", heavy_noise_circle, 1.5, 1, [400], ["exact-auto", "ripser", "scale"]),
        ("anisotropic_blob", anisotropic_blob, 2.5, 1, [400], ["exact-auto", "ripser"]),
        ("torus", torus, 1.6, 1, [400, 1000], ["exact-auto", "ripser"]),
    ]

    for name, fn, T, dim, ns, methods in scaling:
        for n in ns:
            path = cloud(name.replace("_T", "_noisy") if name.startswith("circle") else name, n, fn, rng)
            est = run_estimate(path, T, dim)
            row = {"name": name, "n": n, "T": T, "maxdim": dim, "estimate": est, "runs": {}}
            print(f"CONS {name} n={n} T={T} dim={dim}", flush=True)
            if "exact-auto" in methods:
                row["runs"]["pith_exact"] = strip_pairs(run_pith(path, T, dim, "exact", "auto"))
                print(f"  exact {row['runs']['pith_exact'].get('wall_s')} {row['runs']['pith_exact'].get('pipeline')}", flush=True)
            if "scale" in methods:
                row["runs"]["pith_scale"] = strip_pairs(run_pith(path, T, dim, "scale", "auto"))
                print(f"  scale {row['runs']['pith_scale'].get('wall_s')} |E|={row['runs']['pith_scale'].get('n_dist')}", flush=True)
            if "ripser" in methods:
                row["runs"]["ripser"] = strip_pairs(run_ripser(path, T, dim))
                print(f"  ripser {row['runs']['ripser'].get('wall_s')}", flush=True)
            if "gudhi" in methods and n <= 200:
                row["runs"]["gudhi_rips"] = strip_pairs(run_gudhi_rips(path, T, dim))
                print(f"  gudhi {row['runs']['gudhi_rips'].get('wall_s')}", flush=True)
            recs.append(row)

    # Topology: exact vs Ripser vs scale on a small mixed cloud
    topo = []
    for name, fn, T, dim in (("figure8", figure8, 1.1, 1), ("circle_noisy", circle_noisy, 1.5, 1), ("sphere", sphere, 1.4, 2)):
        path = cloud(name, 400, fn, rng)
        a = run_pith(path, T, dim, "exact", "auto")
        b = run_ripser(path, T, dim)
        s = run_pith(path, T, dim, "scale", "auto")
        fid_exact = {}
        fid_scale = {}
        try:
            fid_exact = compare(b["pairs"], a["pairs"], dim)
        except Exception as e:
            fid_exact = {"error": str(e)}
        try:
            fid_scale = compare(b["pairs"], s["pairs"], min(dim, 1) if name == "figure8" else dim)
        except Exception as e:
            fid_scale = {"error": str(e)}
        topo.append(
            {
                "name": name,
                "n": 400,
                "T": T,
                "exact_match": fid_exact.get("exact_match_tol"),
                "exact_unmatched": fid_exact.get("unmatched"),
                "scale_unmatched": fid_scale.get("unmatched"),
                "ess1_exact": a.get("ess1"),
                "ess1_ripser": b.get("ess1"),
                "ess1_scale": s.get("ess1"),
                "ess2_exact": a.get("ess2"),
                "ess2_ripser": b.get("ess2"),
                "ess2_scale": s.get("ess2"),
            }
        )
        print(f"TOPO {topo[-1]}", flush=True)

    # Dispatcher: estimate vs what auto actually picked
    disp = []
    for name, fn, T, dim in (
        ("many_loops", many_loops, 1.2, 1),
        ("nested_loops", nested_loops, 1.6, 1),
        ("clustered", clustered, 0.8, 1),
        ("heavy_noise_circle", heavy_noise_circle, 1.5, 1),
        ("figure8", figure8, 1.1, 1),
        ("circle_noisy", circle_noisy, 1.5, 1),
    ):
        path = cloud(name, 500, fn, rng)
        est = run_estimate(path, T, dim)
        got = run_pith(path, T, dim, "exact", "auto")
        pipe = (got.get("pipeline") or "")
        picked = "redzed" if "redzed" in pipe else ("implicit" if "collapse" in pipe or "implicit" in pipe else pipe)
        rec_e = est.get("engine_recommended")
        disp.append(
            {
                "name": name,
                "recommended": rec_e,
                "picked": picked,
                "pipeline": pipe,
                "match": rec_e in (picked or "") or (rec_e == "implicit" and "collapse" in pipe),
                "exact_feasible": est.get("exact_feasible"),
                "wall_s": got.get("wall_s"),
            }
        )
        print(f"DISP {disp[-1]}", flush=True)

    # Local exponents on series with ≥2 successful exact times
    exponents = []
    by = {}
    for r in recs:
        key = (r["name"], r["maxdim"], r["T"])
        by.setdefault(key, []).append(r)
    for key, rows in by.items():
        rows = sorted(rows, key=lambda x: x["n"])
        for meth in ("pith_exact", "ripser", "pith_scale"):
            pts = []
            for r in rows:
                run = r["runs"].get(meth)
                if run and run.get("ok") and run.get("wall_s"):
                    pts.append((r["n"], run["wall_s"], run.get("n_dist")))
            for i in range(len(pts) - 1):
                exponents.append(
                    {
                        "name": key[0],
                        "method": meth,
                        "n0": pts[i][0],
                        "n1": pts[i + 1][0],
                        "p_time": local_exp(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1]),
                        "p_edges": local_exp(pts[i][0], pts[i][2], pts[i + 1][0], pts[i + 1][2])
                        if pts[i][2] and pts[i + 1][2]
                        else None,
                    }
                )

    report = {
        "hardware": {"cpus": NPROC, "note": "4-CPU / 16GB cloud image; Ripser 1 thread; PITH may use nproc threads"},
        "gudhi": GUDHI_VER,
        "giotto": GIOTTO_VER,
        "have_gudhi": HAVE_GUDHI,
        "have_giotto": HAVE_GIOTTO,
        "receipts": recs,
        "topology": topo,
        "dispatcher": disp,
        "exponents": exponents,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {path}", flush=True)

    # Compact tables
    print("\n=== exact vs ripser (successful) ===")
    for r in recs:
        a = r["runs"].get("pith_exact")
        b = r["runs"].get("ripser")
        if a and b and a.get("wall_s") and b.get("wall_s"):
            print(f"{r['name']:20} n={r['n']:5} pith={a['wall_s']:.3f}s ripser={b['wall_s']:.3f}s  {b['wall_s']/a['wall_s']:.2f}×")


if __name__ == "__main__":
    main()
