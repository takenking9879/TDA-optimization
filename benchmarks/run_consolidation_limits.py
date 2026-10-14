#!/usr/bin/env python3
"""Phase-2 consolidation: limits, thread-fair times, topology distances, dispatcher oracle.

Does not re-run the first consolidation wave. Writes
benchmarks/results/consolidation/limits.json.

Hardware: 4 CPU / 16 GB. Timeouts are short so a family stops once a method
becomes impractical. Empirical, not a theorem.
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
    anisotropic_blob,
    blobs,
    circle_noisy,
    clustered,
    figure8,
    heavy_noise_circle,
    loops_with_bridges,
    many_loops,
    mixed_1d2d3d,
    multi_cavities,
    multi_scale_loops,
    near_degenerate,
    nested_loops,
    outliers_sphere,
    sphere,
    torus,
    uniform,
    write_csv,
    write_lower_distance,
)
from ph_metrics import bottleneck_h1, ess  # noqa: E402
from run_consolidation import (  # noqa: E402
    HAVE_GIOTTO,
    HAVE_GUDHI,
    GIOTTO_VER,
    GUDHI_VER,
    OUT,
    local_exp,
    run_estimate,
    run_gudhi_rips,
    run_ripser,
    strip_pairs,
)
from run_suite import PITH, RIPSER, compare, parse_pith_text, run_cmd  # noqa: E402

CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12
NPROC = os.cpu_count() or 4

try:
    import gudhi  # type: ignore
except Exception:
    gudhi = None


def _rss_child():
    try:
        return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024
    except Exception:
        return 0


def cloud(name, n, fn, rng):
    CLOUDS.mkdir(parents=True, exist_ok=True)
    path = CLOUDS / f"{name}_n{n}.csv"
    if not path.exists():
        write_csv(path, fn(n, rng))
    return path


def run_pith(path, T, maxdim, mode="exact", engine="auto", threads=None, timeout=BUDGET_S, distances=False):
    cmd = [
        str(PITH),
        "--distances" if distances else "--points",
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
    claimed = threads if threads and threads > 0 else NPROC
    if threads is not None:
        cmd.extend(["--threads", str(threads)])
    rss0 = _rss_child()
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    cpu = None
    try:
        ru = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = ru.ru_utime + ru.ru_stime
    except Exception:
        pass
    rss1 = _rss_child()
    timed_out = err is not None and "timed out" in (err or "").lower()
    oom = err is not None and ("memory" in (err or "").lower() or "std::bad_alloc" in (err or ""))
    return {
        "method": f"pith:{mode}:{engine}:t{claimed}",
        "ok": err is None,
        "error": err,
        "timed_out": timed_out,
        "oom": oom,
        "wall_s": None if err else dt,
        "cpu_s": cpu,
        "threads_claimed": claimed,
        "threads_pith": c.get("threads") if c else None,
        "rss_delta": max(0, rss1 - rss0),
        "rss_pith": c.get("rss") if c else None,
        "n_dist": c.get("distances"),
        "n_edges_in": c.get("edges_in"),
        "n_edges_out": c.get("edges_out"),
        "metric_ms": c.get("metric_ms"),
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "pipeline": c.get("pipeline"),
        "residual_frac": c.get("residual_frac"),
        "n_pairs": len(pairs) if pairs else 0,
        "ess0": ess(pairs, 0) if pairs else None,
        "ess1": ess(pairs, 1) if pairs else None,
        "ess2": ess(pairs, 2) if pairs else None,
        "pairs": pairs,
        "counters": c,
    }


def diag_arrays(pairs, dim):
    rows = []
    for p in pairs or []:
        if p["dim"] != dim:
            continue
        birth, death = p["birth"], p["death"]
        if math.isfinite(death) and death - birth <= 1e-6:
            continue
        rows.append([birth, death if math.isfinite(death) else math.inf])
    return np.asarray(rows, dtype=float) if rows else np.zeros((0, 2), dtype=float)


def topology_metrics(ref, other, maxdim):
    out = {"unmatched": None, "exact_match": None}
    try:
        fid = compare(ref, other, maxdim)
        out["unmatched"] = fid.get("unmatched")
        out["exact_match"] = fid.get("exact_match_tol")
        out["n_finite_ref"] = fid.get("n_finite_a")
        out["n_finite_other"] = fid.get("n_finite_b")
    except Exception as e:
        out["compare_error"] = str(e)
    out["ess"] = {d: {"ref": ess(ref, d), "other": ess(other, d)} for d in range(maxdim + 1)}
    out["bottleneck_greedy_h1"] = bottleneck_h1(ref, other)
    if gudhi is not None:
        for d in range(maxdim + 1):
            A, B = diag_arrays(ref, d), diag_arrays(other, d)
            key = f"bottleneck_h{d}"
            try:
                out[key] = float(gudhi.bottleneck_distance(A, B))
            except Exception as e:
                out[key] = None
                out[f"{key}_error"] = str(e)
            try:
                from gudhi.wasserstein import wasserstein_distance  # noqa: WPS433

                out[f"wasserstein1_h{d}"] = float(wasserstein_distance(A, B, order=1.0))
            except Exception as e:
                out[f"wasserstein1_h{d}"] = None
                out[f"wasserstein1_h{d}_error"] = str(e)
    return out


def run_gudhi_alpha(path, maxdim, timeout=BUDGET_S):
    if not HAVE_GUDHI:
        return {"method": "gudhi-alpha", "ok": False, "error": "gudhi not importable"}
    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    try:
        st = gudhi.AlphaComplex(points=pts).create_simplex_tree()
        st.compute_persistence()
        dt = time.perf_counter() - t0
        if dt > timeout:
            return {"method": "gudhi-alpha", "ok": False, "error": "timeout", "wall_s": dt}
        pairs = []
        for dim, (b, d) in st.persistence():
            if dim > maxdim:
                continue
            pairs.append({"dim": dim, "birth": float(b), "death": float(d) if d != float("inf") else float("inf")})
        return {
            "method": "gudhi-alpha",
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
        return {"method": "gudhi-alpha", "ok": False, "error": str(e), "wall_s": time.perf_counter() - t0}


def engine_from_pipeline(pipe):
    pipe = pipe or ""
    if "redzed" in pipe:
        return "redzed"
    if "collapse" in pipe or "implicit" in pipe:
        return "implicit"
    return pipe or "unknown"


def main():
    rng = np.random.default_rng(1)  # held-out seed, not the training seed 0
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "hardware": {
            "cpus": NPROC,
            "budget_s": BUDGET_S,
            "note": "4-CPU / 16GB; Ripser 1 thread; PITH --threads 1 vs hardware",
        },
        "gudhi": GUDHI_VER,
        "giotto": GIOTTO_VER,
        "have_gudhi": HAVE_GUDHI,
        "have_giotto": HAVE_GIOTTO,
        "threads": [],
        "engines": [],
        "limits": [],
        "topology": [],
        "dispatcher_oracle": [],
        "noneuclidean": [],
        "exponents": [],
        "max_practical": [],
    }

    print("=== thread-fair ===", flush=True)
    for name, fn, T, dim, n in (
        ("figure8", figure8, 1.1, 1, 1000),
        ("circle_noisy", circle_noisy, 1.5, 1, 1000),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, 1000),
        ("sphere", sphere, 1.4, 2, 400),
        ("blobs", blobs, 1.0, 0, 4000),
    ):
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "maxdim": dim, "runs": {}}
        row["runs"]["pith_t1"] = strip_pairs(run_pith(path, T, dim, "exact", "auto", threads=1))
        row["runs"]["pith_thw"] = strip_pairs(run_pith(path, T, dim, "exact", "auto", threads=0))
        row["runs"]["ripser"] = strip_pairs(run_ripser(path, T, dim, timeout=BUDGET_S))
        print(
            f"  {name} n={n} t1={row['runs']['pith_t1'].get('wall_s')} "
            f"thw={row['runs']['pith_thw'].get('wall_s')} ripser={row['runs']['ripser'].get('wall_s')}",
            flush=True,
        )
        report["threads"].append(row)

    print("=== forced engines ===", flush=True)
    for name, fn, T, dim, n in (
        ("figure8", figure8, 1.1, 1, 1000),
        ("circle_noisy", circle_noisy, 1.5, 1, 1000),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, 1000),
        ("torus", torus, 1.6, 1, 1000),
        ("nested_loops", nested_loops, 1.6, 1, 400),
        ("many_loops", many_loops, 1.2, 1, 400),
        ("heavy_noise_circle", heavy_noise_circle, 1.5, 1, 400),
        ("clustered", clustered, 0.8, 1, 400),
    ):
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "maxdim": dim, "estimate": run_estimate(path, T, dim), "runs": {}}
        for eng in ("auto", "redzed", "implicit"):
            row["runs"][eng] = strip_pairs(run_pith(path, T, dim, "exact", eng, threads=1))
            print(f"  {name} {eng} {row['runs'][eng].get('wall_s')} {row['runs'][eng].get('pipeline')}", flush=True)
        report["engines"].append(row)

    print("=== progressive limits ===", flush=True)
    series = [
        ("figure8", figure8, 1.1, 1, [2000, 4000], ["exact-auto", "exact-redzed", "ripser", "scale"]),
        ("circle_noisy", circle_noisy, 1.5, 1, [2000, 4000], ["exact-auto", "ripser"]),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, [4000], ["exact-auto", "ripser"]),
        ("torus", torus, 1.6, 1, [2000], ["exact-auto", "ripser"]),
        ("many_loops", many_loops, 1.2, 1, [1000, 2000], ["exact-auto", "ripser", "scale"]),
        ("nested_loops", nested_loops, 1.6, 1, [1000, 2000], ["exact-auto", "ripser", "scale"]),
        ("loops_with_bridges", loops_with_bridges, 1.2, 1, [400, 1000], ["exact-auto", "ripser", "scale"]),
        ("multi_scale_loops", multi_scale_loops, 1.5, 1, [400, 1000], ["exact-auto", "ripser", "scale"]),
        ("near_degenerate", near_degenerate, 0.15, 1, [400, 1000], ["exact-auto", "ripser"]),
        ("anisotropic_blob", anisotropic_blob, 2.5, 1, [1000], ["exact-auto", "ripser"]),
        ("mixed_1d2d3d", mixed_1d2d3d, 1.4, 2, [300, 600], ["exact-auto", "ripser", "scale"]),
        ("multi_cavities", multi_cavities, 1.4, 2, [300, 600], ["exact-auto", "ripser", "scale"]),
        ("outliers_sphere", outliers_sphere, 1.4, 2, [400], ["exact-auto", "ripser", "scale"]),
        ("sphere", sphere, 1.4, 2, [800], ["exact-auto", "ripser"]),
        ("blobs", blobs, 1.0, 0, [25000], ["exact-auto"]),
        ("figure8", figure8, 1.1, 1, [24000], ["scale"]),
        ("sphere", sphere, 1.4, 2, [80000], ["scale"]),
        ("circle_T", circle_noisy, 0.8, 1, [800], ["exact-auto", "ripser"]),
        ("circle_T", circle_noisy, 2.0, 1, [400], ["exact-auto", "ripser"]),
    ]
    dead = set()
    for name, fn, T, dim, ns, methods in series:
        for n in ns:
            path = cloud(name.replace("_T", "_noisy") if name.startswith("circle") else name, n, fn, rng)
            est = run_estimate(path, T, dim)
            row = {"name": name, "n": n, "T": T, "maxdim": dim, "estimate": est, "runs": {}}
            print(f"LIM {name} n={n} T={T} dim={dim}", flush=True)
            for spec in methods:
                key = spec.replace("-", "_")
                dead_key = (name, spec)
                if dead_key in dead:
                    row["runs"][key] = {"ok": False, "error": "skipped-after-fail", "method": spec}
                    continue
                if spec == "exact-auto":
                    rec = run_pith(path, T, dim, "exact", "auto", threads=1)
                elif spec == "exact-redzed":
                    rec = run_pith(path, T, dim, "exact", "redzed", threads=1)
                elif spec == "scale":
                    rec = run_pith(path, T, dim, "scale", "auto", threads=1)
                elif spec == "ripser":
                    rec = run_ripser(path, T, dim, timeout=BUDGET_S)
                else:
                    continue
                row["runs"][key] = strip_pairs(rec)
                print(f"  {spec} {rec.get('wall_s')} {rec.get('error') or rec.get('pipeline')}", flush=True)
                if not rec.get("ok"):
                    dead.add(dead_key)
            if HAVE_GUDHI and n <= 300 and "exact-auto" in methods:
                row["runs"]["gudhi_rips"] = strip_pairs(run_gudhi_rips(path, T, dim, timeout=min(BUDGET_S, 8)))
            report["limits"].append(row)

    print("=== topology distances ===", flush=True)
    for name, fn, T, dim, n in (
        ("figure8", figure8, 1.1, 1, 400),
        ("circle_noisy", circle_noisy, 1.5, 1, 400),
        ("sphere", sphere, 1.4, 2, 400),
        ("nested_loops", nested_loops, 1.6, 1, 400),
        ("many_loops", many_loops, 1.2, 1, 400),
        ("loops_with_bridges", loops_with_bridges, 1.2, 1, 400),
        ("heavy_noise_circle", heavy_noise_circle, 1.5, 1, 400),
        ("multi_scale_loops", multi_scale_loops, 1.5, 1, 400),
        ("mixed_1d2d3d", mixed_1d2d3d, 1.4, 2, 300),
        ("multi_cavities", multi_cavities, 1.4, 2, 300),
    ):
        path = cloud(name, n, fn, rng)
        exact = run_pith(path, T, dim, "exact", "auto", threads=1)
        rip = run_ripser(path, T, dim, timeout=BUDGET_S)
        scale = run_pith(path, T, dim, "scale", "auto", threads=1)
        sparse = run_pith(path, T, dim, "sparse", "auto", threads=1)
        alpha = run_gudhi_alpha(path, dim) if dim >= 1 and n <= 400 else {"ok": False, "pairs": []}
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "exact_vs_ripser": topology_metrics(rip.get("pairs") or [], exact.get("pairs") or [], dim)
            if rip.get("ok") and exact.get("ok")
            else {"error": "missing exact/ripser"},
            "scale_vs_ripser": topology_metrics(rip.get("pairs") or [], scale.get("pairs") or [], dim)
            if rip.get("ok") and scale.get("ok")
            else {"error": "missing scale/ripser"},
            "sparse_vs_ripser": topology_metrics(rip.get("pairs") or [], sparse.get("pairs") or [], dim)
            if rip.get("ok") and sparse.get("ok")
            else {"error": "missing sparse/ripser"},
            "alpha_vs_ripser": topology_metrics(rip.get("pairs") or [], alpha.get("pairs") or [], dim)
            if rip.get("ok") and alpha.get("ok")
            else {"error": "missing alpha/ripser"},
            "ess_exact": {0: exact.get("ess0"), 1: exact.get("ess1"), 2: exact.get("ess2")},
            "ess_ripser": {0: rip.get("ess0"), 1: rip.get("ess1"), 2: rip.get("ess2")},
            "ess_scale": {0: scale.get("ess0"), 1: scale.get("ess1"), 2: scale.get("ess2")},
            "ess_sparse": {0: sparse.get("ess0"), 1: sparse.get("ess1"), 2: sparse.get("ess2")},
            "ess_alpha": {0: alpha.get("ess0"), 1: alpha.get("ess1"), 2: alpha.get("ess2")},
            "walls": {
                "exact": exact.get("wall_s"),
                "ripser": rip.get("wall_s"),
                "scale": scale.get("wall_s"),
                "sparse": sparse.get("wall_s"),
                "alpha": alpha.get("wall_s"),
            },
        }
        print(
            f"TOPO {name} exact_match={rec['exact_vs_ripser'].get('exact_match')} "
            f"scale_un={rec['scale_vs_ripser'].get('unmatched')} "
            f"bn={rec['scale_vs_ripser'].get('bottleneck_h1')} "
            f"ess_scale={rec['ess_scale']}",
            flush=True,
        )
        report["topology"].append(rec)

    print("=== dispatcher oracle (1-thread engines vs estimate) ===", flush=True)
    for row in report["engines"]:
        est = row.get("estimate") or {}
        rec_e = est.get("engine_recommended")
        times = {}
        for eng in ("redzed", "implicit"):
            run = row["runs"].get(eng) or {}
            if run.get("ok") and run.get("wall_s"):
                times[eng] = run["wall_s"]
        if not times:
            continue
        oracle = min(times, key=times.get)
        rec_t = times.get(rec_e)
        waste = (rec_t / times[oracle]) if rec_t else None
        auto_pick = engine_from_pipeline((row["runs"].get("auto") or {}).get("pipeline"))
        report["dispatcher_oracle"].append(
            {
                "name": row["name"],
                "n": row["n"],
                "recommended": rec_e,
                "auto_picked": auto_pick,
                "oracle_faster": oracle,
                "times": times,
                "waste_if_follow_estimate": waste,
                "wrong": rec_e in times and rec_e != oracle,
                "mode_recommended": est.get("mode_recommended"),
                "exact_feasible": est.get("exact_feasible"),
                "regime": est.get("residual_regime"),
                "confidence": est.get("confidence"),
            }
        )
        print(f"DISP {report['dispatcher_oracle'][-1]}", flush=True)

    print("=== non-Euclidean L1 distances ===", flush=True)
    for n, T in ((200, 2.5), (400, 2.5)):
        pts = uniform(n, 8, rng)
        dpath = CLOUDS / f"uniform8_l1_n{n}.dist"
        if not dpath.exists():
            write_lower_distance(dpath, pts, p=1.0)
        ppath = CLOUDS / f"uniform8_l1_n{n}.csv"
        if not ppath.exists():
            write_csv(ppath, pts)
        try:
            out, dt, _ = run_cmd(
                [
                    str(PITH),
                    "--estimate",
                    "--distances",
                    str(dpath),
                    "--maxdim",
                    "1",
                    "--threshold",
                    str(T),
                    "--format",
                    "json",
                ],
                20,
            )
            est = json.loads(out)
            est["wall_s"] = dt
        except Exception as e:
            est = {"error": str(e)}
        exact = run_pith(dpath, T, 1, "exact", "auto", threads=1, distances=True)
        red = run_pith(dpath, T, 1, "exact", "redzed", threads=1, distances=True)
        rip = {
            "method": "ripser-distances",
            "ok": False,
            "error": None,
        }
        try:
            out, dt, _ = run_cmd(
                [str(RIPSER), "--format", "lower-distance", "--dim", "1", "--threshold", str(T), str(dpath)],
                BUDGET_S,
            )
            from run_suite import parse_ripser  # noqa: WPS433

            pairs = parse_ripser(out)
            rip = {
                "method": "ripser-distances",
                "ok": True,
                "wall_s": dt,
                "threads_claimed": 1,
                "n_pairs": len(pairs),
                "ess1": ess(pairs, 1),
                "pairs": pairs,
            }
        except Exception as e:
            rip["error"] = str(e)
        fid = {}
        if exact.get("ok") and rip.get("ok"):
            fid = topology_metrics(rip["pairs"], exact["pairs"], 1)
        report["noneuclidean"].append(
            {
                "name": "uniform8_l1",
                "n": n,
                "T": T,
                "estimate": est,
                "pith_auto": strip_pairs(exact),
                "pith_redzed": strip_pairs(red),
                "ripser": strip_pairs(rip),
                "exact_vs_ripser": fid,
            }
        )
        print(
            f"L1 n={n} pith={exact.get('wall_s')} redzed={red.get('wall_s')} "
            f"ripser={rip.get('wall_s')} match={fid.get('exact_match')}",
            flush=True,
        )

    # Local exponents on the new limit series
    by = {}
    for r in report["limits"]:
        by.setdefault((r["name"], r["maxdim"], r["T"]), []).append(r)
    for key, rows in by.items():
        rows = sorted(rows, key=lambda x: x["n"])
        for meth in ("exact_auto", "exact_redzed", "ripser", "scale"):
            pts = []
            for r in rows:
                run = r["runs"].get(meth)
                if run and run.get("ok") and run.get("wall_s"):
                    pts.append((r["n"], run["wall_s"], run.get("n_dist") or run.get("rss_pith")))
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

    # Max practical n under BUDGET_S from this wave + known first-wave points
    first = {}
    first_path = OUT / "report.json"
    if first_path.exists():
        first = json.loads(first_path.read_text())
    buckets = {}
    for src, meth_map in (
        (first.get("receipts") or [], {"pith_exact": "pith_exact", "ripser": "ripser", "pith_scale": "pith_scale"}),
        (report["limits"], {"exact_auto": "pith_exact", "ripser": "ripser", "scale": "pith_scale", "exact_redzed": "pith_redzed"}),
    ):
        for r in src:
            for raw, canon in meth_map.items():
                run = (r.get("runs") or {}).get(raw)
                if not run:
                    continue
                key = (r["name"], r.get("maxdim"), canon)
                buckets.setdefault(key, []).append((r["n"], bool(run.get("ok") and run.get("wall_s")), run.get("wall_s"), run.get("rss_pith")))
    for (name, dim, meth), pts in sorted(buckets.items()):
        ok = [p for p in pts if p[1] and p[2] is not None and p[2] <= BUDGET_S]
        fail = [p for p in pts if not p[1]]
        report["max_practical"].append(
            {
                "name": name,
                "maxdim": dim,
                "method": meth,
                "max_n_ok": max((p[0] for p in ok), default=None),
                "wall_at_max": max(ok, key=lambda p: p[0])[2] if ok else None,
                "rss_at_max": max(ok, key=lambda p: p[0])[3] if ok else None,
                "first_fail_n": min((p[0] for p in fail), default=None),
                "budget_s": BUDGET_S,
            }
        )

    path = OUT / "limits.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
