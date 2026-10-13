#!/usr/bin/env python3
"""I282 probe: mesh-irregularity α vs n-formula vs fixed 2.25."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
from scipy.spatial import Delaunay

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, torus, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8, two_circles
from run_wave95 import ess, pith_redzed_d, ripser_d


def spoke_stats(pts):
    tri = Delaunay(pts)
    n = len(pts)
    rad = np.zeros(n)
    for s in tri.simplices:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            i, j = int(s[a]), int(s[b])
            d = float(np.linalg.norm(pts[i] - pts[j]))
            rad[i] = max(rad[i], d)
            rad[j] = max(rad[j], d)
    med = float(np.median(rad))
    mx = float(np.max(rad))
    p90 = float(np.percentile(rad, 90))
    return {
        "med": med,
        "max": mx,
        "p90": p90,
        "max/med": mx / max(med, 1e-12),
        "p90/med": p90 / max(med, 1e-12),
    }


def pith_dvr(path, T, alpha, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
           "--delaunay-vr", "--delaunay-alpha", str(alpha), "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    rng = np.random.default_rng(0)
    jobs = [
        ("blobs", 400, 1.0, blobs),
        ("figure8", 2000, 1.1, figure8),
        ("figure8", 4000, 1.1, figure8),
        ("circle_noisy", 500, 1.5, circle_noisy),
        ("torus", 400, 1.6, torus),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 200, 1.2, two_circles),
    ]
    for name, n, T, fn in jobs:
        path = ensure_cloud(name, n, fn, rng)
        pts = np.loadtxt(path, delimiter=",")
        st = spoke_stats(pts)
        a_ratio = min(2.75, max(1.75, 1.15 * st["max/med"]))
        a_p90 = min(2.75, max(1.75, 1.4 * st["p90/med"]))
        a_n = min(2.75, 1.75 + 0.125 * math.log2(max(n / 400.0, 1.0)))
        print(
            f"{name} n={n} med={st['med']:.4f} max={st['max']:.4f} "
            f"max/med={st['max/med']:.3f} p90/med={st['p90/med']:.3f} "
            f"a_ratio={a_ratio:.3f} a_p90={a_p90:.3f} a_n={a_n:.3f}",
            flush=True,
        )
        pr, tr = ripser_d(path, T, 1, 60)
        for lab, a in (("ratio", a_ratio), ("p90", a_p90), ("nform", a_n), ("2.25", 2.25)):
            pa, cs, ta = pith_dvr(path, T, a)
            fid = compare(pr, pa, 1)
            print(
                f"  {lab} a={a:.3f} match={fid.get('exact_match_tol')} "
                f"un={fid.get('unmatched')} ess1={ess(pa,1)}/{ess(pr,1)} "
                f"e={cs.get('distances')} pith={ta:.3f}s",
                flush=True,
            )


if __name__ == "__main__":
    main()
