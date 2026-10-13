#!/usr/bin/env python3
"""I280 probe: 2-hop adapt / median floor vs I279 global α=2.25."""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8
from run_wave95 import ess, pith_redzed_d, ripser_d


def pith_dvr(path, T, dim, alpha, adapt=False, floor=0, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--delaunay-alpha", str(alpha), "--no-enclosing"]
    if adapt:
        cmd.append("--delaunay-adapt")
    if floor:
        cmd += ["--delaunay-floor", str(floor)]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    cfgs = [
        ("a1.5", 1.5, False, 0),
        ("a1.5+adapt", 1.5, True, 0),
        ("a1.5+adapt+f1.5", 1.5, True, 1.5),
        ("a1.75+adapt", 1.75, True, 0),
        ("a2.0+adapt", 2.0, True, 0),
    ]
    jobs = [
        ("blobs", 400, 1.0, blobs, "rip"),
        ("figure8", 2000, 1.1, figure8, "rip"),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r), "rip"),
        ("circle_noisy", 500, 1.5, circle_noisy, "rip"),
    ]
    for name, n, T, fn, oracle in jobs:
        path = ensure_cloud(name, n, fn, rng)
        if oracle == "rip":
            pr, tr = ripser_d(path, T, 1, 60)
        else:
            pr, _, tr = pith_redzed_d(path, T, 1, 90)
        print(f"=== {name} n={n} ref={tr:.3f}s ess1={ess(pr,1)} ===", flush=True)
        for lab, a, ad, fl in cfgs:
            pa, cs, ta = pith_dvr(path, T, 1, a, ad, fl)
            fid = compare(pr, pa, 1)
            print(
                f"  {lab} match={fid.get('exact_match_tol')} un={fid.get('unmatched')} "
                f"ess1={ess(pa,1)} e={cs.get('distances')} pith={ta:.3f}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
