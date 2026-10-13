#!/usr/bin/env python3
"""I267: tight H2 generate_stream (live word-range AND).

Vendor ANDs all n/64 neighborhood words per edge. H2 only needs the
live rlo/rhi intersection. Same triangles / tie order (comb_index).
Harder H2: forced redzed on sphere n=200 / n=400. H0–H1 must hold.
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
        ("redzed", "sphere", 200, 1.4, sphere, 2),
        ("redzed", "sphere", 400, 1.4, sphere, 2),
        ("auto", "two_spheres", 200, 1.4, two_spheres, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "figure8", 2000, 1.1, figure8, 1),
        ("auto", "torus", 2000, 1.6, torus, 1),
        ("auto", "sphere", 2000, 1.4, sphere, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 or (dim >= 2 and n >= 200) or name == "torus" else 60
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
        print(f"I267 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    sph80 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 80 and r.get("maxdim") == 2), None)
    sph200 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 200 and r.get("maxdim") == 2), None)
    sph400r = next(
        (r for r in recs if r["name"] == "sphere" and r["n"] == 400 and r.get("maxdim") == 2 and r["engine"] == "redzed"),
        None,
    )
    sph_ok = bool(sph80 and sph80.get("ess2") == 1 and sph80.get("match_ripser"))
    sph200_ok = bool(sph200 and sph200.get("ess2") == 1 and sph200.get("match_ripser"))
    sph400_ok = bool(sph400r and sph400r.get("ess2") == 1 and sph400r.get("match_ripser"))
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    fig = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.38)
    fig_ok = bool(fig and fig.get("ess1") == 2 and fig.get("match_ripser"))
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I267 tight H2 stream invented bars or broke H0–H2; revert"
    elif ident and ess_ok and sph_ok and sph200_ok and sph400_ok and fig_ok and uni_10x and uni_hold:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; sphere n=80 {sph80.get('vs_ripser'):.2f}×; "
            f"n=200 {sph200.get('vs_ripser'):.2f}× / {sph200.get('pith_s'):.3f}s; "
            f"n=400 redzed {sph400r.get('vs_ripser'):.2f}× / {sph400r.get('pith_s'):.3f}s; "
            f"dense {uni.get('vs_ripser'):.2f}×"
        )
    elif ident and ess_ok and sph_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; sph200={sph200_ok} sph400={sph400_ok}; "
            f"dense {uni.get('vs_ripser') if uni else None}×"
        )
    else:
        status = "reject"
        summary = "I267 tight H2 identity or H0–H2 hold failed"

    write(
        {
            "id": "tight_h2_generate_stream",
            "lever": "H09-redzed-tight-h2-stream",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "sphere_n200_h2": sph200_ok,
            "sphere_n400_h2": sph400_ok,
            "uniform2_10x": uni_10x,
            "receipts": recs,
        },
        "I267",
    )
    print(f"I267 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
