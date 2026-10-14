#!/usr/bin/env python3
"""I278 probe: larger α to zero blobs unmatched; figure8 n=8000 clock."""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8, two_circles
from run_wave95 import ess, ripser_d


def pith_dvr(path, T, dim, alpha, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--delaunay-alpha", str(alpha), "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    jobs = [
        ("blobs", 400, 1.0, blobs, 1, True),
        ("figure8", 2000, 1.1, figure8, 1, True),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("two_circles", 200, 1.2, two_circles, 1, True),
        ("circle_noisy", 500, 1.5, circle_noisy, 1, True),
    ]
    for alpha in (1.75, 2.0, 2.5):
        print(f"=== alpha={alpha} ===", flush=True)
        for name, n, T, fn, dim, vs in jobs:
            path = ensure_cloud(name, n, fn, rng)
            pa, cs, ta = pith_dvr(path, T, dim, alpha)
            pr, tr = ripser_d(path, T, dim, 60) if vs else (None, None)
            fid = compare(pr, pa, dim) if pr is not None else {}
            print(
                f"  {name} n={n} a={alpha} match={fid.get('exact_match_tol')} "
                f"un={fid.get('unmatched')} ess1={ess(pa, 1)}/{ess(pr, 1) if pr else None} "
                f"e={cs.get('distances')} pith={ta:.3f}s "
                f"vs={(tr / ta) if tr and ta else None}",
                flush=True,
            )
    # harder scale, pith only
    path = ensure_cloud("figure8", 8000, figure8, rng)
    for alpha in (1.5, 2.0):
        pa, cs, ta = pith_dvr(path, 1.1, 1, alpha, 90)
        print(
            f"SCALE figure8 n=8000 a={alpha} ess1={ess(pa, 1)} e={cs.get('distances')} "
            f"pith={ta:.3f}s pipe={cs.get('pipeline')}",
            flush=True,
        )


if __name__ == "__main__":
    main()
