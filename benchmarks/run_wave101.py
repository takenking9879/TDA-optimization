#!/usr/bin/env python3
"""I240: spatial UF + per-component RedZeD matrices (no full n×n).

I239 still filled n² distances then split. Low-d spatial hash (cell=T,
Moore neighborhood) finds G_T components in O(n·deg) and each block
allocates only m×m. Exact: same components as the dense UF.
Hard case: blobs n=6000/8000 (more points, still seconds).
Connected uniform2 is unchanged (1 component).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, uniform  # noqa: E402
from run_suite import compare  # noqa: E402
from run_wave85 import (  # noqa: E402
    bottleneck_h1,
    ensure_cloud,
    figure8,
    two_circles,
    unit_square_path,
    write,
)
from run_wave95 import ess, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402


def main():
    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("sphere", 400, 1.4, sphere, 2),
        ("two_spheres", 200, 1.4, two_spheres, 2),
        ("blobs", 4000, 1.0, blobs, 1),
        ("blobs", 6000, 1.0, blobs, 1),
        ("blobs", 8000, 1.0, blobs, 1),  # more points, still seconds
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r), 1),
    ]

    for name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 6000 else (60 if n >= 4000 or dim >= 2 else 45)
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_auto(path, T, dim, rto)
        fid = compare(pr, pa, dim)
        rec = {
            "name": name, "n": n, "T": T, "maxdim": dim,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0), "ess0_ripser": ess(pr, 0),
            "ess1": ess(pa, 1), "ess1_ripser": ess(pr, 1),
            "ess2": ess(pa, 2), "ess2_ripser": ess(pr, 2),
            "bottleneck_h1": bottleneck_h1(pr, pa),
            "pipeline": cs.get("pipeline"),
            "residual_frac": cs.get("residual_frac"),
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_cc": cs.get("collapse_trims"),
            "n_distances": cs.get("distances"),
            "auto_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        if name == "two_spheres":
            pz, cz, tz = pith_redzed_d(path, T, dim, rto)
            zfid = compare(pr, pz, dim)
            rec["forced_redzed_s"] = tz
            rec["forced_redzed_cc"] = cz.get("collapse_trims")
            rec["forced_redzed_pipe"] = cz.get("pipeline")
            rec["forced_redzed_match"] = zfid.get("exact_match_tol")
            rec["forced_redzed_distances"] = cz.get("distances")
        print(f"I240 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    circle_ok = all(
        r.get("pipeline") == "pith:auto-collapse"
        for r in recs if r["name"] == "circle_noisy" and r["n"] >= 400
    )
    sph = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2), None)
    sph_ok = bool(sph and sph.get("pipeline") == "pith:auto-collapse" and sph.get("match_ripser"))
    two_sph = next((r for r in recs if r["name"] == "two_spheres"), None)
    two_sph_ok = bool(
        two_sph
        and two_sph.get("match_ripser")
        and two_sph.get("ess0") == 2
        and two_sph.get("ess2") == 2
        and two_sph.get("forced_redzed_match")
        and (two_sph.get("forced_redzed_distances") or 0) < 200 * 199 // 2
    )
    blob_rows = [r for r in recs if r["name"] == "blobs" and r["n"] >= 4000]
    blob_sparse = all(
        (r.get("n_distances") or 0) > 0
        and (r.get("n_distances") or 0) < r["n"] * (r["n"] - 1) // 2
        and "redzed-cc" in (r.get("pipeline") or "")
        for r in blob_rows
    )
    blob_10x = sum(1 for r in blob_rows if (r.get("vs_ripser") or 0) >= 10)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    uni_ok = bool(uni and uni.get("match_ripser") and uni.get("pipeline") == "pith:auto-redzed")

    if ident and ess_ok and circle_ok and sph_ok and two_sph_ok and blob_sparse and blob_10x == len(blob_rows) and uni_ok:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; spatial cc metric; "
            f"blobs 10× {blob_10x}/{len(blob_rows)}"
        )
    elif ident and ess_ok and circle_ok and sph_ok and uni_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; blob_sparse={blob_sparse} "
            f"blob_10x={blob_10x}/{len(blob_rows)}"
        )
    else:
        status = "reject"
        summary = "I240 spatial-cc identity or dispatch failed"

    write(
        {
            "id": "spatial_redzed_cc",
            "lever": "H07-spatial-cc",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "circle_collapse": circle_ok,
            "sphere_h2_collapse": sph_ok,
            "two_spheres_h2": two_sph_ok,
            "blob_sparse": blob_sparse,
            "blob_10x": blob_10x,
            "receipts": recs,
        },
        "I240",
    )
    print(f"I240 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
