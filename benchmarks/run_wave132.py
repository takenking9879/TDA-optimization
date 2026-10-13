#!/usr/bin/env python3
"""I271: walk-locate 2D Delaunay H0.

Same MST ⊆ Delaunay identity as I270, but Lawson walk + cavity flood
instead of O(n²) incircle scan. Harder H0: blobs n=12000. H1/H2 hold.
Keep the wave short (no figure8 n=4000 Ripser).
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
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
        ("redzed", "unit_square", 4, 2.0, None, 1),
        ("redzed", "figure8", 200, 1.0, figure8, 1),
        ("redzed", "two_circles", 200, 1.2, two_circles, 1),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1),
        ("redzed", "sphere", 80, 1.4, sphere, 2),
        ("auto", "two_spheres", 200, 1.4, two_spheres, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "blobs", 8000, 1.0, blobs, 0),
        ("auto", "blobs", 12000, 1.0, blobs, 0),
        ("auto", "figure8", 2000, 1.1, figure8, 1),
        ("auto", "torus", 2000, 1.6, torus, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 8000 or dim >= 2 or name == "torus" else 60
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_redzed_d(path, T, dim, rto) if engine == "redzed" else pith_auto(path, T, dim, rto)
        fid = compare(pr, pa, dim)
        rec = {
            "engine": engine,
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0),
            "ess0_ripser": ess(pr, 0),
            "ess1": ess(pa, 1),
            "ess1_ripser": ess(pr, 1),
            "ess2": ess(pa, 2),
            "ess2_ripser": ess(pr, 2),
            "bottleneck_h1": bottleneck_h1(pr, pa),
            "pipeline": cs.get("pipeline"),
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_dist": cs.get("distances"),
            "n_cc": cs.get("collapse_trims"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        print(f"I271 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    sph = next((r for r in recs if r["name"] == "sphere" and r["n"] == 80 and r.get("maxdim") == 2), None)
    sph400 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 400 and r.get("maxdim") == 2), None)
    sph_ok = bool(sph and sph.get("ess2") == 1 and sph.get("match_ripser"))
    sph400_ok = bool(sph400 and sph400.get("ess2") == 1 and sph400.get("match_ripser"))
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    fig = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    b4 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 4000 and r.get("maxdim") == 0), None)
    b8 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 8000 and r.get("maxdim") == 0), None)
    b12 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 12000 and r.get("maxdim") == 0), None)
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.38)
    fig_ok = bool(fig and fig.get("ess1") == 2 and fig.get("match_ripser"))
    b4_ok = bool(b4 and b4.get("ess0") == 3 and b4.get("match_ripser"))
    b8_ok = bool(b8 and b8.get("ess0") == 3 and b8.get("match_ripser"))
    b12_ok = bool(b12 and b12.get("ess0") == 3 and b12.get("match_ripser"))
    del4 = bool(b4 and b4.get("pipeline") and "delaunay" in str(b4.get("pipeline")))
    del12 = bool(b12 and b12.get("pipeline") and "delaunay" in str(b12.get("pipeline")))
    # I270: n=4000 metric 176ms / 0.186s; n=8000 metric 557ms / 0.57s.
    b4_cut = bool(b4 and b4.get("metric_ms") is not None and b4["metric_ms"] < 80)
    b8_cut = bool(b8 and b8.get("metric_ms") is not None and b8["metric_ms"] < 150)
    b12_cut = bool(b12 and b12.get("pith_s") and b12["pith_s"] < 0.45)
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I271 walk-locate H0 invented bars or broke H0–H2; revert"
    elif (
        ident
        and ess_ok
        and sph_ok
        and sph400_ok
        and fig_ok
        and b4_ok
        and b8_ok
        and b12_ok
        and del4
        and del12
        and b4_cut
        and b8_cut
        and b12_cut
        and uni_10x
        and uni_hold
    ):
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; blobs n=4000 H0 {b4.get('vs_ripser'):.2f}× / "
            f"{b4.get('metric_ms'):.1f}ms {b4.get('n_dist')}e; n=8000 {b8.get('metric_ms'):.1f}ms; "
            f"n=12000 {b12.get('vs_ripser'):.2f}× / {b12.get('pith_s'):.3f}s; "
            f"dense {uni.get('vs_ripser'):.2f}×"
        )
    elif ident and ess_ok and sph_ok and b4_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; del={del4}/{del12} "
            f"m4={b4.get('metric_ms')} m8={b8.get('metric_ms')} "
            f"n12={b12.get('pith_s') if b12 else None}s dense {uni.get('vs_ripser') if uni else None}×"
        )
    else:
        status = "reject"
        summary = "I271 walk-locate identity or H0–H2 hold failed"

    write(
        {
            "id": "walk_locate_h0",
            "lever": "H16-walk-locate-h0",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "delaunay_n4000": del4,
            "delaunay_n12000": del12,
            "blobs4000_cut": b4_cut,
            "blobs8000_cut": b8_cut,
            "blobs12000_cut": b12_cut,
            "uniform2_10x": uni_10x,
            "receipts": recs,
        },
        "I271",
    )
    print(f"I271 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
