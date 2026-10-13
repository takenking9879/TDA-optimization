#!/usr/bin/env python3
"""I083–I095: post-revert challenges — T-scale, geometry, H2, D&C note, Alpha."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith(path, T, dim, collapse=1, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    return parse_pith_text(out) + (dt,)


def pith3(path, T, dim, collapse=1, timeout=180):
    pairs, c, dt = pith(path, T, dim, collapse, timeout)
    return pairs, c, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I083_large_T():
    recs = []
    path = BENCH / "datasets/generated/circle_noisy_n1000.csv"
    for T in (1.2, 1.5, 1.8):
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith3(path, T, 1)
        fid = compare(pr, pp, 1)
        recs.append({"T": T, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
    write({"id": "circle1000_large_T", "lever": "H03", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle1000 larger T: does H1 clock approach 10×?",
           "receipts": recs}, "I083")


def I084_geometry():
    recs = []
    for fname, T in (("figure8_n500.csv", 1.0), ("two_circles_n400.csv", 1.2),
                     ("swiss_n400.csv", 1.4), ("annulus_n300.csv", 1.2)):
        path = BENCH / "datasets/generated" / fname
        if not path.exists():
            recs.append({"file": fname, "missing": True})
            continue
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith3(path, T, 1)
        fid = compare(pr, pp, 1)
        recs.append({"file": fname, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms")})
    write({"id": "geometry_after_revert", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if all(r.get("match") for r in recs if not r.get("missing")) else "reject",
           "summary": "geometry recheck after bitset revert + degree filter",
           "receipts": recs}, "I084")


def I085_sphere500():
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pr, tr = ripser(path, 1.4, 2)
    pp, c, tp = pith3(path, 1.4, 2)
    fid = compare(pr, pp, 2)
    write({"id": "sphere500_h2_reverted", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "sphere500 H2 after bitset revert",
           "receipts": [{"match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                         "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms")}]}, "I085")


def I086_torus_adaptive():
    path = BENCH / "datasets/generated/torus_n200.csv"
    pr, tr = ripser(path, 1.6, 1)
    recs = []
    for coll, tag in ((1, "one"), (-1, "adaptive")):
        pp, c, tp = pith3(path, 1.6, 1, coll)
        fid = compare(pr, pp, 1)
        recs.append({"tag": tag, "match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    write({"id": "torus200_adaptive_reverted", "lever": "H01-iter", "class": "reproduced", "fidelity": "exact",
           "status": "experiment", "summary": "torus200 adaptive after revert",
           "receipts": recs}, "I086")


def I087_alpha():
    import gudhi
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pts = np.loadtxt(path, delimiter=",")
    pr, tr = ripser(path, 1.4, 2)
    t0 = time.perf_counter()
    st = gudhi.AlphaComplex(points=pts).create_simplex_tree()
    st.compute_persistence()
    ta = time.perf_counter() - t0
    bars = []
    for dim, (b, d) in st.persistence():
        if dim > 2:
            continue
        death = math.inf if d == math.inf or d > 1e300 else float(d)
        bars.append({"dim": dim, "birth": float(b), "death": death})
    fid = compare(pr, bars, 2)
    write({"id": "alpha_sphere500_again", "lever": "H16", "class": "empirical", "fidelity": "other-complex",
           "status": "hold", "summary": "Alpha still ≠ VR; time-only control",
           "receipts": [{"match_vs_ripser_vr": fid.get("exact_match_tol"), "unmatched": fid.get("unmatched"),
                         "alpha_s": ta, "ripser_vr_s": tr}]}, "I087")


def I088_dc_note():
    write({"id": "time_axis_dc_collapse", "lever": "H01-dc", "class": "proposal",
           "fidelity": "exact-claimed", "status": "hold",
           "summary": "Glisse 2022 Lemma 6 time-axis D&C is a parallel schedule, not less sequential work",
           "receipts": [{"source": "papers/glisse-2022-edge-collapse-extensions.pdf §5",
                         "decision": "do not implement as a sequential 10× lever"}]}, "I088")


def I089_uniform2():
    path = BENCH / "datasets/generated/uniform2_n500.csv"
    pr, tr = ripser(path, 0.35, 1)
    pp, c, tp = pith3(path, 0.35, 1)
    fid = compare(pr, pp, 1)
    write({"id": "uniform2_n500_reverted", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "uniform2 n=500 after revert",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "edge_ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1)}]}, "I089")


def I090_highd():
    path = BENCH / "datasets/generated/uniform10_n200.csv"
    pr, tr = ripser(path, 1.8, 1)
    pp, c, tp = pith3(path, 1.8, 1, -1)
    fid = compare(pr, pp, 1)
    write({"id": "highd_after_revert", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "high-d still exact, still lose wall-clock",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms")}]}, "I090")


def I091_h0_circle1500():
    path = BENCH / "datasets/generated/circle_noisy_n1500.csv"
    pr, tr = ripser(path, 1.2, 0)
    pp, c, tp = pith3(path, 1.2, 0, -1)
    fid = compare(pr, pp, 0)
    write({"id": "h0_circle1500", "lever": "H05", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "H0 skip on circle1500",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms") or 0}]}, "I091")


def I092_blobs200():
    path = BENCH / "datasets/generated/blobs_n200.csv"
    pr, tr = ripser(path, 1.0, 1)
    pp, c, tp = pith3(path, 1.0, 1)
    fid = compare(pr, pp, 1)
    write({"id": "blobs200_reverted", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "blobs200 after revert",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "edge_ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1)}]}, "I092")


def I093_sphere200_h1():
    path = BENCH / "datasets/generated/sphere_n200.csv"
    pr, tr = ripser(path, 1.4, 1)
    pp, c, tp = pith3(path, 1.4, 1)
    fid = compare(pr, pp, 1)
    write({"id": "sphere200_h1_reverted", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "sphere200 H1 after revert",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None}]}, "I093")


def I094_implicit_still():
    path = BENCH / "datasets/generated/circle_noisy_n80.csv"
    pr, tr = ripser(path, 1.2, 1)
    out, tp, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", "1.2",
         "--collapse", "0", "--engine", "implicit", "--no-enclosing"], 30)
    pp, c = parse_pith_text(out)
    fid = compare(pr, pp, 1)
    write({"id": "implicit_still_rejected", "lever": "H02", "class": "experiment",
           "fidelity": "exact-claimed",
           "status": "reject" if not fid.get("exact_match_tol") else "support",
           "summary": "implicit collapse=0 still fails after I045 fix attempts",
           "receipts": [{"match": fid.get("exact_match_tol"), "unmatched": fid.get("unmatched")}]}, "I094")


def I095_counts_vs_i023():
    path = BENCH / "datasets/generated/circle_noisy_n80.csv"
    _, c0, _ = pith3(path, 1.2, 1, 0)
    _, c1, _ = pith3(path, 1.2, 1, 1)
    ratio = (c0.get("cols_reduced") or 0) / max(1, c1.get("cols_reduced") or 1)
    write({"id": "column_ratio_circle80", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support",
           "summary": f"circle80 columns {c0.get('cols_reduced')}→{c1.get('cols_reduced')} = {ratio:.0f}×",
           "receipts": [{"cols0": c0.get("cols_reduced"), "cols1": c1.get("cols_reduced"), "ratio": ratio}]}, "I095")


def main():
    I083_large_T()
    I084_geometry()
    I085_sphere500()
    I086_torus_adaptive()
    I087_alpha()
    I088_dc_note()
    I089_uniform2()
    I090_highd()
    I091_h0_circle1500()
    I092_blobs200()
    I093_sphere200_h1()
    I094_implicit_still()
    I095_counts_vs_i023()


if __name__ == "__main__":
    main()
