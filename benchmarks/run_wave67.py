#!/usr/bin/env python3
"""I205: quantify Alpha / Sheehy sparse vs exact VR (topology loss + size)."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import RESULTS, RIPSER, compare, essential, parse_ripser, run_cmd  # noqa: E402

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


def st_bars(st, maxdim=1):
    bars = []
    for dim, (b, d) in st.persistence():
        if dim > maxdim:
            continue
        death = math.inf if d == math.inf or d > 1e300 else float(d)
        bars.append({"dim": dim, "birth": float(b), "death": death})
    return bars


def scale_alpha_to_vr_diameter(bars):
    """GUDHI Alpha filtration is r^2; Čech radius r; VR diameter ~ 2r."""
    out = []
    for p in bars:
        b = 2.0 * math.sqrt(max(p["birth"], 0.0))
        d = p["death"]
        if math.isfinite(d):
            d = 2.0 * math.sqrt(max(d, 0.0))
        out.append({"dim": p["dim"], "birth": b, "death": d})
    return out


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


def n_ess(pairs):
    return len(essential(pairs, 1))


def n_fin(pairs):
    return len(finite_h1(pairs))


def main():
    import gudhi

    recs = []
    jobs = [
        ("circle_noisy", 1000, 1.5),
        ("blobs", 1000, 1.0),
        ("sphere", 1000, 1.4),
        ("torus", 1000, 1.6),
        ("uniform2", 1000, 0.35),
        ("figure8", 500, 1.0),
        ("two_circles", 400, 1.2),
    ]
    for name, n, T in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        pts = np.loadtxt(path, delimiter=",")
        pr, tr = ripser(path, T, 120)
        row = {
            "name": name, "n": n, "T": T,
            "ripser_s": tr,
            "vr_h1_finite": n_fin(pr),
            "vr_h1_ess": n_ess(pr),
        }

        t0 = time.perf_counter()
        ast = gudhi.AlphaComplex(points=pts).create_simplex_tree()
        ast.compute_persistence()
        alpha_s = time.perf_counter() - t0
        ab = st_bars(ast)
        ab_vr = scale_alpha_to_vr_diameter(ab)
        fid_a = compare(pr, ab_vr, 1, tol=0.15)
        row.update({
            "alpha_s": alpha_s,
            "alpha_simplices": int(ast.num_simplices()),
            "alpha_h1_finite": n_fin(ab_vr),
            "alpha_h1_ess": n_ess(ab_vr),
            "alpha_unmatched_scaled": fid_a.get("unmatched"),
            "alpha_bottleneck_scaled": bottleneck_h1(pr, ab_vr),
            "alpha_vs_ripser": tr / alpha_s if alpha_s else None,
        })

        t0 = time.perf_counter()
        rips = gudhi.RipsComplex(points=pts, max_edge_length=T, sparse=0.5)
        sst = rips.create_simplex_tree(max_dimension=2)
        sst.compute_persistence()
        sparse_s = time.perf_counter() - t0
        sb = st_bars(sst)
        fid_s = compare(pr, sb, 1, tol=1e-4)
        row.update({
            "sparse_eps": 0.5,
            "sparse_s": sparse_s,
            "sparse_simplices": int(sst.num_simplices()),
            "sparse_h1_finite": n_fin(sb),
            "sparse_h1_ess": n_ess(sb),
            "sparse_unmatched": fid_s.get("unmatched"),
            "sparse_bottleneck": bottleneck_h1(pr, sb),
            "sparse_vs_ripser": tr / sparse_s if sparse_s else None,
        })
        print(f"I205 {row}", flush=True)
        recs.append(row)

    ident_sparse = all(r.get("sparse_unmatched", 1) == 0 for r in recs)
    write({
        "id": "alt_complex_quantified_loss",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "exact" if ident_sparse else "approx-or-other-complex",
        "status": "support" if recs else "hold",
        "summary": "I205 Alpha (scaled 2√r²) and Sheehy sparse=0.5 vs Ripser VR",
        "receipts": recs,
        "note": (
            "Alpha is Čech/offset PH, not VR. sparse=0.5 is (1, 1/(1-ε)) "
            "interleaved VR. Neither is a drop-in exact-VR replacement. "
            "Loss is unmatched bars + finite-H1 bottleneck vs Ripser."
        ),
    }, "I205")


if __name__ == "__main__":
    main()
