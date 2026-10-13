#!/usr/bin/env python3
"""I279 probe: α=2.0/2.5 on figure8 n=8000 vs redzed; n=16000 clock."""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8
from run_wave95 import ess, pith_redzed_d


def pith_dvr(path, T, dim, alpha, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--delaunay-alpha", str(alpha), "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    path8 = ensure_cloud("figure8", 8000, figure8, rng)
    print("redzed n=8000...", flush=True)
    pr, cref, tr = pith_redzed_d(path8, 1.1, 1, 120)
    print(f"  redzed ess1={ess(pr, 1)} e={cref.get('distances')} t={tr:.3f}s", flush=True)
    for alpha in (2.0, 2.25, 2.5):
        pa, cs, ta = pith_dvr(path8, 1.1, 1, alpha, 60)
        fid = compare(pr, pa, 1)
        print(
            f"  a={alpha} match={fid.get('exact_match_tol')} un={fid.get('unmatched')} "
            f"ess1={ess(pa, 1)} e={cs.get('distances')} pith={ta:.3f}s vs={tr/ta:.1f}×",
            flush=True,
        )
    path16 = ensure_cloud("figure8", 16000, figure8, rng)
    for alpha in (1.75, 2.0):
        pa, cs, ta = pith_dvr(path16, 1.1, 1, alpha, 90)
        print(
            f"SCALE n=16000 a={alpha} ess1={ess(pa, 1)} e={cs.get('distances')} pith={ta:.3f}s",
            flush=True,
        )


if __name__ == "__main__":
    main()
