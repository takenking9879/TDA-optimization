#!/usr/bin/env python3
"""Sparse-Rips accuracy plus a few failure-point pushes.

Theorem-backed path is Sheehy-style greedy-net (`--mode sparse`, ε=0.6).
Not exact VR. Hardware: 4 CPU / 16 GB, 12 s budget. Empirical.
"""

from __future__ import annotations

import json
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
    sphere,
    two_spheres_apart,
)
from ph_metrics import ess  # noqa: E402
from run_consolidation import OUT, local_exp, run_estimate, run_giotto, run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith, topology_metrics  # noqa: E402

BUDGET_S = 12


def main():
    rng = np.random.default_rng(4)
    OUT.mkdir(parents=True, exist_ok=True)
    report = {"budget_s": BUDGET_S, "sparse": [], "failures": [], "estimates": []}

    print("=== sparse vs exact vs scale ===", flush=True)
    for name, fn, T, dim, n in (
        ("figure8", figure8, 1.1, 1, 400),
        ("circle_noisy", circle_noisy, 1.5, 1, 400),
        ("nested_loops", nested_loops, 1.6, 1, 400),
        ("many_loops", many_loops, 1.2, 1, 400),
        ("disconnected_circles", disconnected_circles, 1.5, 1, 400),
        ("grid_holes", grid_holes, 0.12, 1, 400),
        ("sphere", sphere, 1.4, 2, 400),
        ("two_spheres_apart", two_spheres_apart, 1.4, 2, 300),
    ):
        path = cloud(name, n, fn, rng)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
        rip = run_ripser(path, T, dim, timeout=BUDGET_S)
        scale = run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S)
        sparse = run_pith(path, T, dim, "sparse", "auto", threads=1, timeout=BUDGET_S)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "walls": {
                "exact": pith.get("wall_s"),
                "ripser": rip.get("wall_s"),
                "scale": scale.get("wall_s"),
                "sparse": sparse.get("wall_s"),
            },
            "n_dist": {
                "exact": pith.get("n_edges_in") or pith.get("n_dist"),
                "scale": scale.get("n_edges_in") or scale.get("n_dist"),
                "sparse": sparse.get("n_edges_in") or sparse.get("n_dist"),
            },
            "n_metric": {
                "exact": pith.get("n_dist"),
                "scale": scale.get("n_dist"),
                "sparse": sparse.get("n_dist"),
            },
            "ess_ripser": {d: ess(rip.get("pairs"), d) for d in range(dim + 1)} if rip.get("ok") else None,
            "ess_exact": {d: ess(pith.get("pairs"), d) for d in range(dim + 1)} if pith.get("ok") else None,
            "ess_scale": {d: ess(scale.get("pairs"), d) for d in range(dim + 1)} if scale.get("ok") else None,
            "ess_sparse": {d: ess(sparse.get("pairs"), d) for d in range(dim + 1)} if sparse.get("ok") else None,
            "sparse_ok": sparse.get("ok"),
            "sparse_error": sparse.get("error"),
        }
        if pith.get("ok") and rip.get("ok"):
            rec["exact_vs_ripser"] = topology_metrics(rip["pairs"], pith["pairs"], dim)
        if scale.get("ok") and rip.get("ok"):
            rec["scale_vs_ripser"] = topology_metrics(rip["pairs"], scale["pairs"], dim)
        if sparse.get("ok") and rip.get("ok"):
            rec["sparse_vs_ripser"] = topology_metrics(rip["pairs"], sparse["pairs"], dim)
        print(
            f"  {name} n={n} sparse={sparse.get('wall_s')} |E|={sparse.get('n_dist')} "
            f"unmatched={(rec.get('sparse_vs_ripser') or {}).get('unmatched')} "
            f"ess={rec.get('ess_sparse')}",
            flush=True,
        )
        rec = {k: (strip_pairs(v) if isinstance(v, dict) and "pairs" in v else v) for k, v in rec.items()}
        report["sparse"].append(rec)

    print("=== larger sparse timings ===", flush=True)
    for name, fn, T, dim, ns in (
        ("figure8", figure8, 1.1, 1, [2000, 8000]),
        ("sphere", sphere, 1.4, 2, [400, 4000]),
        ("grid_holes", grid_holes, 0.12, 1, [800]),
    ):
        prev = None
        for n in ns:
            path = cloud(name, n, fn, rng)
            sparse = strip_pairs(run_pith(path, T, dim, "sparse", "auto", threads=1, timeout=BUDGET_S))
            scale = strip_pairs(run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S))
            row = {"name": name, "n": n, "T": T, "maxdim": dim, "sparse": sparse, "scale": scale}
            if prev and prev.get("wall_s") and sparse.get("wall_s"):
                row["p_sparse"] = local_exp(prev["n"], prev["wall_s"], n, sparse["wall_s"])
            print(
                f"  {name} n={n} sparse={sparse.get('wall_s')} scale={scale.get('wall_s')} "
                f"|E|_s={sparse.get('n_dist')}",
                flush=True,
            )
            report["sparse"].append({"name": name, "n": n, "T": T, "maxdim": dim, "larger": True, **row})
            prev = {"n": n, "wall_s": sparse.get("wall_s")}

    print("=== failure pushes (12 s) ===", flush=True)
    for name, fn, T, dim, n, methods in (
        ("circle_noisy", circle_noisy, 1.5, 1, 2000, ["exact", "ripser", "giotto"]),
        ("figure8", figure8, 1.1, 1, 4000, ["exact", "giotto"]),
        ("sphere", sphere, 1.4, 2, 800, ["exact", "giotto"]),
        ("nested_loops", nested_loops, 1.6, 1, 2000, ["exact", "giotto"]),
    ):
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "maxdim": dim, "runs": {}}
        if "exact" in methods:
            row["runs"]["pith_exact"] = strip_pairs(
                run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
            )
        if "ripser" in methods:
            row["runs"]["ripser"] = strip_pairs(run_ripser(path, T, dim, timeout=BUDGET_S))
        if "giotto" in methods:
            row["runs"]["giotto_t1"] = strip_pairs(run_giotto(path, T, dim, n_threads=1, timeout=BUDGET_S))
        print(
            f"  FAIL {name} n={n} "
            + " ".join(f"{k}={v.get('wall_s') or v.get('error')}" for k, v in row["runs"].items()),
            flush=True,
        )
        report["failures"].append(row)

    print("=== estimate growth bands (τ frozen) ===", flush=True)
    for name, fn, T, dim, n in (
        ("circle_noisy", circle_noisy, 1.5, 1, 80),
        ("figure8", figure8, 1.1, 1, 2000),
        ("sphere", sphere, 1.4, 2, 400),
        ("mixed_1d2d3d", mixed_1d2d3d, 1.4, 2, 300),
    ):
        path = cloud(name, n, fn, rng)
        est = run_estimate(path, T, dim)
        report["estimates"].append({"name": name, "n": n, "estimate": est})
        print(
            f"  EST {name} n={n} p={est.get('growth_p')} leave={est.get('leaving_cheap_regime')} "
            f"rt={est.get('est_runtime_s')}..{est.get('est_runtime_hi_s')} mode={est.get('mode_recommended')}",
            flush=True,
        )

    path = OUT / "sparse_limits.json"
    path.write_text(json.dumps(report, indent=2, default=str))
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
