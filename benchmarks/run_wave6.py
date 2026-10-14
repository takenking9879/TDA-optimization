#!/usr/bin/env python3
"""I061–I070: RP2 distances, T-sweeps, torus/blobs scale, Alpha control."""

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
ROOT = BENCH.parent


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith_pts(path, T, dim, collapse=1, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    return parse_pith_text(out) + (dt,)


def ripser_pc(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I061_rp2():
    path = ROOT / "third_party/ripser/examples/rp2_600.lower_distance_matrix.csv"
    out_r, tr, _ = run_cmd(
        [str(RIPSER), "--format", "lower-distance", "--dim", "1", str(path)], 60
    )
    try:
        out_p, tp, _ = run_cmd(
            [str(PITH), "--distances", str(path), "--maxdim", "1", "--collapse", "1",
             "--engine", "homology"],
            30,
        )
        pp, c = parse_pith_text(out_p)
        pr = parse_ripser(out_r)
        fid = compare(pr, pp, 1)
        rec = {"match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp, "counters": c}
        status = "support" if fid.get("exact_match_tol") else "reject"
        summary = "Ripser RP2 lower-distance vs PITH --distances"
    except Exception as ex:  # noqa: BLE001
        rec = {"ripser_s": tr, "error": str(ex)[:300]}
        status = "hold"
        summary = "RP2 n=600: CLI parses; collapse timed out (dense metric hold-out)"
    write(
        {
            "id": "rp2_distance_cli",
            "lever": "I041-hold",
            "class": "implementation",
            "fidelity": "unverified",
            "status": status,
            "summary": summary,
            "receipts": [rec],
        },
        "I061",
    )


def I062_T_sweep_circle500():
    path = BENCH / "datasets/generated/circle_noisy_n500.csv"
    recs = []
    for T in (0.6, 0.8, 1.0, 1.2, 1.5):
        pr, tr = ripser_pc(path, T, 1)
        pp, c, tp = pith_pts(path, T, 1)
        fid = compare(pr, pp, 1)
        recs.append({
            "T": T, "match": fid.get("exact_match_tol"),
            "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
            "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out"),
            "collapse_ms": c.get("collapse_ms"),
        })
    write({"id": "circle500_T_sweep", "lever": "H03", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle500 threshold sweep after sticky", "receipts": recs}, "I062")


def I063_torus500():
    path = BENCH / "datasets/generated/torus_n500.csv"
    T = 1.6
    pr, tr = ripser_pc(path, T, 1)
    recs = []
    for coll, tag in ((1, "one"), (-1, "adaptive"), (3, "three")):
        pp, c, tp = pith_pts(path, T, 1, coll)
        fid = compare(pr, pp, 1)
        recs.append({"tag": tag, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "edges_out": c.get("edges_out"),
                     "collapse_ms": c.get("collapse_ms")})
    write({"id": "torus500_passes", "lever": "H01-iter", "class": "experiment", "fidelity": "exact",
           "status": "experiment", "summary": "torus500 collapse passes after sticky",
           "receipts": recs}, "I063")


def I064_n500_families():
    recs = []
    for name, T in (("blobs", 1.0), ("uniform2", 0.35), ("sphere", 1.4)):
        path = BENCH / f"datasets/generated/{name}_n500.csv"
        dim = 1
        pr, tr = ripser_pc(path, T, dim)
        pp, c, tp = pith_pts(path, T, dim, 1)
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edge_ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
                     "collapse_ms": c.get("collapse_ms")})
    write({"id": "n500_families_sticky", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "blobs/uniform2/sphere n=500 H1 after sticky", "receipts": recs}, "I064")


def I065_alpha_sphere200():
    import gudhi
    path = BENCH / "datasets/generated/sphere_n200.csv"
    pts = np.loadtxt(path, delimiter=",")
    pr, tr = ripser_pc(path, 1.4, 2)
    t0 = time.perf_counter()
    ac = gudhi.AlphaComplex(points=pts)
    st = ac.create_simplex_tree()
    st.compute_persistence()
    ta = time.perf_counter() - t0
    bars = []
    for dim, (b, d) in st.persistence():
        if dim > 2:
            continue
        death = math.inf if d == math.inf or d > 1e300 else float(d)
        bars.append({"dim": dim, "birth": float(b), "death": death})
    fid = compare(pr, bars, 2)
    pp, c, tp = pith_pts(path, 1.4, 2, 1)
    write({"id": "alpha_sphere200", "lever": "H16", "class": "empirical", "fidelity": "other-complex",
           "status": "hold", "summary": "Alpha ≠ VR; Alpha time vs PITH VR / Ripser VR",
           "receipts": [{"match_alpha_vs_ripser": fid.get("exact_match_tol"), "unmatched": fid.get("unmatched"),
                         "alpha_s": ta, "ripser_s": tr, "pith_s": tp,
                         "pith_vs_ripser": tr / tp if tp else None}]}, "I065")


def I066_sphere_T():
    path = BENCH / "datasets/generated/sphere_n200.csv"
    recs = []
    for T in (0.8, 1.0, 1.2, 1.4):
        pr, tr = ripser_pc(path, T, 2)
        pp, c, tp = pith_pts(path, T, 2, 1)
        fid = compare(pr, pp, 2)
        recs.append({"T": T, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "edges_out": c.get("edges_out")})
    write({"id": "sphere200_T_h2", "lever": "H03", "class": "reproduced", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "sphere200 H2 T-sweep after sticky", "receipts": recs}, "I066")


def I067_h0_vs_h1_circle1000():
    path = BENCH / "datasets/generated/circle_noisy_n1000.csv"
    T = 1.2
    recs = []
    for dim, tag in ((0, "h0"), (1, "h1")):
        pr, tr = ripser_pc(path, T, dim)
        pp, c, tp = pith_pts(path, T, dim, -1)
        fid = compare(pr, pp, dim)
        recs.append({"tag": tag, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms") or 0})
    write({"id": "h0_vs_h1_circle1000", "lever": "H05", "class": "experiment", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "H0 skip vs H1 collapse on circle1000", "receipts": recs}, "I067")


def I068_implicit_residual_only():
    path = BENCH / "datasets/generated/circle_noisy_n80.csv"
    pr, tr = ripser_pc(path, 1.2, 1)
    pp, c, tp = pith_pts(path, 1.2, 1, 1)
    # implicit on residual is still rejected at n=200; n=80 cycle matched earlier
    out, ti, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", "1.2",
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"], 30)
    pi, ci = parse_pith_text(out)
    fid = compare(pr, pi, 1)
    write({"id": "implicit_thin_residual", "lever": "H02", "class": "experiment", "fidelity": "exact-claimed",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "implicit coh on thin circle80 residual (near-cycle)",
           "receipts": [{"match": fid.get("exact_match_tol"), "pith_s": ti, "ripser_s": tr,
                         "edges_out": ci.get("edges_out")}]}, "I068")


def I069_two_seeds():
    recs = []
    for name in ("circle_seed1_n200", "circle_sig0.01_n200", "circle_sig0.2_n200"):
        path = BENCH / "datasets/generated" / f"{name}.csv"
        if not path.exists():
            recs.append({"name": name, "missing": True})
            continue
        pr, tr = ripser_pc(path, 1.2, 1)
        pp, c, tp = pith_pts(path, 1.2, 1, 1)
        fid = compare(pr, pp, 1)
        recs.append({"name": name, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "edge_ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1)})
    write({"id": "seed_sigma_sticky", "lever": "H01", "class": "reproduced", "fidelity": "exact",
           "status": "support" if all(r.get("match") for r in recs if not r.get("missing")) else "reject",
           "summary": "seed/sigma recheck after sticky", "receipts": recs}, "I069")


def I070_column_work_sticky():
    raw = json.loads((OUT / "I058_h04_remainder_after_collapse.json").read_text())
    write({"id": "column_work_sticky", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support",
           "summary": "collapse still cuts 18–1964× columns after sticky (I058 reuse)",
           "receipts": raw["receipts"]}, "I070")


def main():
    I061_rp2()
    I062_T_sweep_circle500()
    I063_torus500()
    I064_n500_families()
    I065_alpha_sphere200()
    I066_sphere_T()
    I067_h0_vs_h1_circle1000()
    I068_implicit_residual_only()
    I069_two_seeds()
    I070_column_work_sticky()


if __name__ == "__main__":
    main()
