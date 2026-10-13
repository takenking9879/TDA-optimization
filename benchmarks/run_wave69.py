#!/usr/bin/env python3
"""I207: owned implicit cohomology on a Sheehy 1-skeleton (--edges)."""

from __future__ import annotations

import json
import math
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import (  # noqa: E402
    PITH,
    RESULTS,
    RIPSER,
    compare,
    essential,
    parse_pith_text,
    parse_ripser,
    run_cmd,
)

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def ripser(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def pith_edges(edge_path, T, collapse, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--edges", str(edge_path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def st_bars(st, maxdim=1):
    bars = []
    for dim, (b, d) in st.persistence():
        if dim > maxdim:
            continue
        death = math.inf if d == math.inf or d > 1e300 else float(d)
        bars.append({"dim": dim, "birth": float(b), "death": death})
    return bars


def finite_h1(pairs):
    xs = []
    for p in pairs:
        if p["dim"] != 1:
            continue
        if not math.isfinite(p["death"]):
            continue
        if p["death"] - p["birth"] <= 1e-6:
            continue
        xs.append((p["birth"], p["death"]))
    return xs


def bottleneck_h1(a, b):
    import gudhi

    fa, fb = finite_h1(a), finite_h1(b)
    if not fa and not fb:
        return 0.0
    A = np.array(fa, dtype=float) if fa else np.zeros((0, 2))
    B = np.array(fb, dtype=float) if fb else np.zeros((0, 2))
    return float(gudhi.bottleneck_distance(A, B))


def sheehy_skeleton(pts, T, eps=0.5):
    import gudhi

    t0 = time.perf_counter()
    st = gudhi.RipsComplex(points=pts, max_edge_length=T, sparse=eps).create_simplex_tree(
        max_dimension=1
    )
    n = int(st.num_vertices())
    edges = []
    for s, tval in st.get_skeleton(1):
        if len(s) != 2:
            continue
        u, v = (s[0], s[1]) if s[0] < s[1] else (s[1], s[0])
        edges.append((int(u), int(v), float(tval)))
    dt = time.perf_counter() - t0
    return n, edges, dt, st


def write_edges(path, n, edges):
    with path.open("w") as f:
        f.write(f"# n={n}\n")
        for u, v, t in edges:
            f.write(f"{u} {v} {t:.9g}\n")


def gudhi_sparse_ph(pts, T, eps=0.5):
    import gudhi

    t0 = time.perf_counter()
    st = gudhi.RipsComplex(points=pts, max_edge_length=T, sparse=eps).create_simplex_tree(
        max_dimension=2
    )
    st.compute_persistence()
    dt = time.perf_counter() - t0
    return st_bars(st), dt, int(st.num_simplices())


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 1000, 1.5, 90, 90),
        ("blobs", 1000, 1.0, 60, 60),
        ("sphere", 1000, 1.4, 60, 60),
        ("torus", 1000, 1.6, 60, 60),
        ("uniform2", 1000, 0.35, 60, 60),
        ("blobs", 2000, 1.0, 90, 60),
        ("torus", 2000, 1.6, 90, 90),
        ("uniform2", 2000, 0.35, 90, 60),
        ("figure8", 500, 1.0, 60, 60),
        ("two_circles", 400, 1.2, 60, 60),
    ]
    with tempfile.TemporaryDirectory(prefix="i207_") as tmp:
        tmp = Path(tmp)
        for name, n, T, timeout, rto in jobs:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            if not path.exists():
                print(f"missing {path}", flush=True)
                continue
            pts = np.loadtxt(path, delimiter=",")
            vn, edges, skel_s, _ = sheehy_skeleton(pts, T)
            epath = tmp / f"{name}_{n}.edges"
            write_edges(epath, vn, edges)
            p0, c0, t0 = pith_edges(epath, T, 0, timeout)
            p1, c1, t1 = pith_edges(epath, T, 1, timeout)
            gs, gdt, nsim = gudhi_sparse_ph(pts, T)
            pr, tr = ripser(path, T, rto)
            fid_g = compare(gs, p0, 1)
            fid_r0 = compare(pr, p0, 1)
            rec = {
                "name": name, "n": n, "T": T,
                "skel_n": vn,
                "skel_edges": len(edges),
                "skel_s": skel_s,
                "gudhi_s": gdt,
                "gudhi_simplices": nsim,
                "pith0_s": t0,
                "pith1_s": t1,
                "pith0_total": skel_s + t0,
                "pith1_total": skel_s + t1,
                "ripser_s": tr,
                "vs_ripser_0": tr / (skel_s + t0) if (skel_s + t0) else None,
                "vs_ripser_1": tr / (skel_s + t1) if (skel_s + t1) else None,
                "match_gudhi_sparse": fid_g.get("exact_match_tol"),
                "unmatched_gudhi": fid_g.get("unmatched"),
                "unmatched_ripser": fid_r0.get("unmatched"),
                "bottleneck_vs_vr": bottleneck_h1(pr, p0),
                "ess_pith": len(essential(p0, 1)),
                "ess_vr": len(essential(pr, 1)),
                "ess_gudhi": len(essential(gs, 1)),
                "edges_in0": c0.get("edges_in"),
                "edges_out1": c1.get("edges_out"),
                "collapse_ms1": c1.get("collapse_ms"),
                "reduce_ms0": c0.get("reduce_ms"),
            }
            print(f"I207 {rec}", flush=True)
            recs.append(rec)

    flag = all(r.get("match_gudhi_sparse") for r in recs) if recs else False
    ess_ok = all(r.get("ess_pith") == r.get("ess_vr") for r in recs) if recs else False
    # Beat Ripser on the two I205 losers (blobs/uniform2 n=1000) and keep torus.
    losers = [r for r in recs if r["name"] in ("blobs", "uniform2") and r["n"] == 1000]
    beat_losers = bool(losers) and all((r.get("vs_ripser_0") or 0) > 1.05 for r in losers)
    write({
        "id": "sheehy_owned_implicit",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx" if recs else "unverified",
        "status": "support" if ess_ok and beat_losers else (
            "partial" if ess_ok else "reject"
        ),
        "summary": "I207 owned implicit on Sheehy 1-skeleton",
        "receipts": recs,
        "sheehy_is_flag": flag,
        "essential_h1_vs_vr": ess_ok,
        "note": "Approx path. Loss vs VR is unmatched + bottleneck. "
                "Identity vs GUDHI sparse tests whether Sheehy is flag.",
    }, "I207")


if __name__ == "__main__":
    main()
