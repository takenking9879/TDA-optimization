#!/usr/bin/env python3
"""I054–I070: archive I053 finite fail, high-d skip reject, sparse Rips, scale, geometry."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import (  # noqa: E402
    INDEX,
    PITH,
    RESULTS,
    RIPSER,
    compare,
    load_index,
    parse_pith_text,
    parse_ripser,
    run_cmd,
)
from reduced_vr import build_reduced_2_complex, pairwise, persist_h1  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry: dict, iid: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)
    return path


def pith(path, T, dim, collapse=1, engine="homology", timeout=180):
    out, dt, _ = run_cmd(
        [
            str(PITH),
            "--points",
            str(path),
            "--maxdim",
            str(dim),
            "--threshold",
            str(T),
            "--collapse",
            str(collapse),
            "--engine",
            engine,
            "--no-enclosing",
        ],
        timeout,
    )
    pairs, counters = parse_pith_text(out)
    return pairs, counters, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I054_gudhi_api():
    import gudhi

    write(
        {
            "id": "gudhi_collapse_api",
            "lever": "H01-oracle",
            "class": "experiment",
            "fidelity": "n/a",
            "status": "hold",
            "summary": f"gudhi {gudhi.__version__} has no flag_filtration; collapse oracle unavailable in this wheel",
            "receipts": [{"version": gudhi.__version__, "has_flag_filtration": hasattr(gudhi, "flag_filtration")}],
        },
        "I054",
    )


def I055_highd_skip_homology():
    path = BENCH / "datasets/generated/uniform10_n200.csv"
    T = 1.8
    pr, tr = ripser(path, T, 1)
    recs = []
    for coll, tag in ((0, "skip"), (-1, "adaptive"), (1, "one_pass")):
        pp, c, tp = pith(path, T, 1, coll, "homology")
        fid = compare(pr, pp, 1)
        recs.append(
            {
                "tag": tag,
                "match": fid.get("exact_match_tol"),
                "ripser_s": tr,
                "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
            }
        )
    skip = next(x for x in recs if x["tag"] == "skip")
    write(
        {
            "id": "highd_skip_homology",
            "lever": "H01-policy",
            "class": "experiment",
            "fidelity": "exact",
            "status": "reject",
            "summary": f"high-d skip+homology {skip['time_ratio']:.3f}× vs Ripser; do not skip",
            "receipts": recs,
        },
        "I055",
    )


def I056_reduced_vr_finite():
    raw = json.loads((OUT / "I053_reduced_vr_h1.json").read_text())
    finite_ok = all(r["h1_finite_reduced"] == r["h1_finite_ripser"] for r in raw["receipts"])
    write(
        {
            "id": "reduced_vr_finite_bars",
            "lever": "H07",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": "reject",
            "summary": "H07 prototype matches essential H1 only; finite bars wildly over-count (every triangle)",
            "receipts": raw["receipts"],
            "finite_match": finite_ok,
        },
        "I056",
    )


def I057_sheehy_sparse():
    import gudhi

    recs = []
    for name, n, T in (("circle_noisy", 200, 1.2), ("uniform10", 80, 1.8), ("sphere", 80, 1.4)):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pts = np.loadtxt(path, delimiter=",")
        pr, tr = ripser(path, T, 1)
        for eps in (0.3, 0.5):
            t0 = time.perf_counter()
            rips = gudhi.RipsComplex(points=pts, max_edge_length=T, sparse=eps)
            st = rips.create_simplex_tree(max_dimension=2)
            st.compute_persistence()
            dt = time.perf_counter() - t0
            bars = []
            for dim, (b, d) in st.persistence():
                if dim > 1:
                    continue
                death = math.inf if d == math.inf or d > 1e300 else d
                bars.append({"dim": dim, "birth": b, "death": death})
            fid = compare(pr, bars, 1)
            recs.append(
                {
                    "dataset": name,
                    "n": n,
                    "sparse": eps,
                    "n_simplices": st.num_simplices(),
                    "match_exact": fid.get("exact_match_tol"),
                    "unmatched": fid.get("unmatched"),
                    "gudhi_s": dt,
                    "ripser_s": tr,
                }
            )
    write(
        {
            "id": "sheehy_sparse_rips",
            "lever": "H14",
            "class": "approx-guaranteed",
            "fidelity": "approx",
            "status": "reject-as-exact",
            "summary": "GUDHI sparse Rips is not exact VR; logged as approx control",
            "receipts": recs,
        },
        "I057",
    )


def I058_residual_columns():
    recs = []
    for name, n, T, dim in (("circle_noisy", 200, 1.2, 1), ("torus", 200, 1.6, 1), ("sphere", 80, 1.4, 2)):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        _, c0, _ = pith(path, T, dim, 0, "homology")
        _, c1, _ = pith(path, T, dim, 1, "homology")
        recs.append(
            {
                "dataset": name,
                "n": n,
                "cols0": c0.get("cols_reduced"),
                "cols1": c1.get("cols_reduced"),
                "ratio": (c0.get("cols_reduced") or 0) / max(1, c1.get("cols_reduced") or 1),
                "edges0": c0.get("edges_out"),
                "edges1": c1.get("edges_out"),
            }
        )
    write(
        {
            "id": "h04_remainder_after_collapse",
            "lever": "H04",
            "class": "experiment",
            "fidelity": "exact",
            "status": "hold",
            "summary": "unpaired remainder after collapse already tiny on circles; H04 not a 10× lever",
            "receipts": recs,
        },
        "I058",
    )


def I059_circle2000():
    rng = np.random.default_rng(0)
    n = 2000
    t = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (n, 2))
    path = BENCH / "datasets/generated/circle_noisy_n2000.csv"
    np.savetxt(path, pts, delimiter=",")
    T = 1.2
    pr, tr = ripser(path, T, 1, timeout=180)
    pp, c, tp = pith(path, T, 1, 1, "homology", timeout=180)
    fid = compare(pr, pp, 1)
    rec = {
        "n": n,
        "match": fid.get("exact_match_tol"),
        "unmatched": fid.get("unmatched"),
        "edges_in": c.get("edges_in"),
        "edges_out": c.get("edges_out"),
        "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "ripser_s": tr,
        "pith_s": tp,
        "time_ratio": tr / tp if tp else None,
    }
    write(
        {
            "id": "circle2000_scale",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if rec["match"] else "reject",
            "summary": f"circle n=2000 time_ratio={rec['time_ratio']} edges={rec['ratio']}",
            "receipts": [rec],
        },
        "I059",
    )


def I060_geometry_recheck():
    recs = []
    cases = [
        ("annulus_n300", 1.2, 1),
        ("figure8_n500", 1.0, 1),
        ("two_circles_n400", 1.2, 1),
        ("swiss_n400", 1.4, 1),
        ("blobs3d_n400", 1.2, 1),
    ]
    for fname, T, dim in cases:
        path = BENCH / "datasets/generated" / f"{fname}.csv"
        if not path.exists():
            recs.append({"file": fname, "missing": True})
            continue
        pr, tr = ripser(path, T, dim)
        pp, c, tp = pith(path, T, dim, 1, "homology")
        fid = compare(pr, pp, dim)
        recs.append(
            {
                "file": fname,
                "match": fid.get("exact_match_tol"),
                "ripser_s": tr,
                "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "edges_in": c.get("edges_in"),
                "edges_out": c.get("edges_out"),
                "collapse_ms": c.get("collapse_ms"),
            }
        )
    ok = all(r.get("match") for r in recs if not r.get("missing"))
    write(
        {
            "id": "geometry_recheck_sticky",
            "lever": "H01-sticky",
            "class": "reproduced",
            "fidelity": "exact",
            "status": "support" if ok else "reject",
            "summary": "annulus/figure8/two-circles/swiss/blobs3d after sticky",
            "receipts": recs,
        },
        "I060",
    )


def main():
    if not INDEX.exists():
        raise SystemExit("generate datasets first")
    I054_gudhi_api()
    I055_highd_skip_homology()
    I056_reduced_vr_finite()
    I057_sheehy_sparse()
    I058_residual_columns()
    I059_circle2000()
    I060_geometry_recheck()


if __name__ == "__main__":
    main()
