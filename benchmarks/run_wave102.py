#!/usr/bin/env python3
"""I241: H0 is Kruskal (no RedZeD); H1/H2 hold.

maxdim=0 on points uses spatial edges + Kruskal. Exact H0 of VR≤T.
T-capped 1-component fill was smoked and reverted (slower than
parallel all-pairs). Hard case: blobs n=8000 H0 (more points, seconds).
Connected uniform2 H1 remains the 10× wall.
"""

from __future__ import annotations

import sys
from pathlib import Path

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
    import numpy as np

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
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("blobs", 4000, 1.0, blobs, 0),
        ("blobs", 8000, 1.0, blobs, 0),  # hard H0, more points
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r), 0),
    ]

    for name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 8000 else (60 if n >= 4000 or dim >= 2 else 45)
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
            rec["forced_redzed_match"] = zfid.get("exact_match_tol")
            rec["forced_redzed_s"] = tz
            rec["forced_redzed_pipe"] = cz.get("pipeline")
        print(f"I241 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    h0_rows = [r for r in recs if r.get("maxdim", 1) == 0]
    h0_pipe = all("h0" in (r.get("pipeline") or "") for r in h0_rows)
    h0_10x = sum(1 for r in h0_rows if (r.get("vs_ripser") or 0) >= 10)
    circle_ok = all(
        r.get("pipeline") == "pith:auto-collapse"
        for r in recs if r["name"] == "circle_noisy" and r["n"] >= 400 and r.get("maxdim", 1) >= 1
    )
    sph = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2), None)
    sph_ok = bool(sph and sph.get("pipeline") == "pith:auto-collapse" and sph.get("match_ripser"))
    two_sph = next((r for r in recs if r["name"] == "two_spheres"), None)
    two_sph_ok = bool(two_sph and two_sph.get("match_ripser") and two_sph.get("ess2") == 2)
    blob_h1 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 4000 and r.get("maxdim") == 1), None)
    blob_hold = bool(blob_h1 and (blob_h1.get("vs_ripser") or 0) >= 10 and "redzed-cc" in (blob_h1.get("pipeline") or ""))
    uni = next((r for r in recs if r["name"] == "uniform2" and r.get("maxdim") == 1), None)
    uni_ok = bool(uni and uni.get("match_ripser"))

    if ident and ess_ok and h0_pipe and circle_ok and sph_ok and two_sph_ok and blob_hold and uni_ok and h0_10x == len(h0_rows):
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; H0 Kruskal 10×"
    elif ident and ess_ok and h0_pipe and circle_ok and sph_ok and two_sph_ok and blob_hold and uni_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; H0 Kruskal path; "
            f"h0_10x={h0_10x}/{len(h0_rows)}"
        )
    else:
        status = "reject"
        summary = "I241 H0 Kruskal identity or H1/H2 hold failed"

    write(
        {
            "id": "h0_spatial_kruskal",
            "lever": "H05-h0-kruskal",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "h0_pipe": h0_pipe,
            "h0_10x": h0_10x,
            "circle_collapse": circle_ok,
            "sphere_h2_collapse": sph_ok,
            "receipts": recs,
        },
        "I241",
    )
    print(f"I241 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
