#!/usr/bin/env python3
"""I283 probe: Delaunay complex (max-edge filtration) vs VR and I276 flag.

Insert every Delaunay simplex with t = max edge. Θ(n) in d=2,3.
I205 Alpha (circumradius) dropped ess H1. This is diameter, like I276
flag, but only Delaunay faces — no extra flag tets.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from gudhi import SimplexTree
from scipy.spatial import Delaunay

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8, two_circles
from run_wave95 import ess, ripser_d
from run_wave100 import two_spheres


def pith_dvr(path, T, dim, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def edge_len(pts, i, j):
    return float(np.linalg.norm(pts[i] - pts[j]))


def delaunay_complex_pairs(pts, T, dim):
    dln = Delaunay(pts)
    st = SimplexTree()
    n = len(pts)
    for i in range(n):
        st.insert([i], 0.0)
    seen_e = set()
    seen_f = set()
    n_tet = 0
    n_tri = 0
    n_ed = 0
    for s in dln.simplices:
        s = [int(x) for x in s]
        # edges
        for a in range(len(s)):
            for b in range(a + 1, len(s)):
                i, j = s[a], s[b]
                if i > j:
                    i, j = j, i
                if (i, j) in seen_e:
                    continue
                seen_e.add((i, j))
                t = edge_len(pts, i, j)
                if t <= T:
                    st.insert([i, j], t)
                    n_ed += 1
        if len(s) >= 3:
            # triangles of this simplex
            from itertools import combinations
            for face in combinations(s, 3):
                f = tuple(sorted(face))
                if f in seen_f:
                    continue
                seen_f.add(f)
                t = max(edge_len(pts, f[0], f[1]), edge_len(pts, f[0], f[2]), edge_len(pts, f[1], f[2]))
                if t <= T:
                    st.insert(list(f), t)
                    n_tri += 1
        if len(s) == 4:
            t = 0.0
            for a in range(4):
                for b in range(a + 1, 4):
                    t = max(t, edge_len(pts, s[a], s[b]))
            if t <= T:
                st.insert(s, t)
                n_tet += 1
    st.compute_persistence()
    pairs = []
    for pdim, (b, d) in st.persistence():
        if pdim > dim:
            continue
        if np.isfinite(d) and d - b <= 1e-6:
            continue
        pairs.append({"dim": int(pdim), "birth": float(b), "death": float(d) if np.isfinite(d) else float("inf")})
    return pairs, {"edges": n_ed, "tris": n_tri, "tets": n_tet}


def main():
    rng = np.random.default_rng(0)
    jobs = [
        ("sphere", 80, 1.4, sphere, 2),
        ("sphere", 400, 1.4, sphere, 2),
        ("two_spheres", 200, 1.5, two_spheres, 2),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("torus", 400, 1.6, torus, 1),
        ("blobs", 400, 1.0, blobs, 1),
    ]
    for name, n, T, fn, dim in jobs:
        path = ensure_cloud(name, n, fn, rng)
        pts = np.loadtxt(path, delimiter=",")
        pr, tr = ripser_d(path, T, dim, 60)
        pa, cs, ta = pith_dvr(path, T, dim)
        dc, cnt = delaunay_complex_pairs(pts, T, dim)
        fid_dc = compare(pr, dc, dim)
        fid_fl = compare(pr, pa, dim)
        print(
            f"{name} n={n} dim={dim} "
            f"DC match={fid_dc.get('exact_match_tol')} un={fid_dc.get('unmatched')} "
            f"ess={ess(dc,0)}/{ess(dc,1)}/{ess(dc,2)} "
            f"ref_ess={ess(pr,0)}/{ess(pr,1)}/{ess(pr,2)} "
            f"flag un={fid_fl.get('unmatched')} ess2_flag={ess(pa,2)} "
            f"DC {cnt} rip={tr:.3f}s flag={ta:.3f}s",
            flush=True,
        )


if __name__ == "__main__":
    main()
