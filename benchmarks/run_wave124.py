#!/usr/bin/env python3
"""I263: edge-frac probe for the spatial gate.

Volume π(T/L)^d<0.2 stays. A 250-point |E|/C(m,2) probe additionally
sends hollow/manifold clouds (figure8 T=1.1: vol≈0.22, probe≈0.24) to
spatial+hash without moving dense uniform2 / sphere off I238 all-pairs.
Hard mixed-homology scale: figure8 n=4000 T=1.1 (ess H1 = 2).
H0 / H1 / H2 identity must hold.
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
        ("auto", "figure8", 2000, 1.1, figure8, 1),
        ("auto", "figure8", 4000, 1.1, figure8, 1),
        ("auto", "torus", 2000, 1.6, torus, 1),
        ("auto", "sphere", 2000, 1.4, sphere, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "uniform2", 20000, 0.09, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 180 if n >= 15000 else (90 if n >= 4000 or dim >= 2 or name == "torus" else 60)
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
        print(f"I263 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig_ok = any(r["name"] == "figure8" and r["n"] == 200 and r.get("ess1") == 2 and r.get("match_ripser") for r in recs)
    fig2 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] >= 4000), None)
    fig2_ok = bool(fig2 and fig2.get("match_ripser") and fig2.get("ess1") == 2)
    fig4_ok = bool(fig4 and fig4.get("match_ripser") and fig4.get("ess1") == 2)
    fig2_spat = bool(fig2 and "spatial" in str(fig2.get("pipeline") or ""))
    fig4_spat = bool(fig4 and "spatial" in str(fig4.get("pipeline") or ""))
    sph_ok = any(
        r["name"] == "sphere" and r.get("maxdim", 0) >= 2 and r.get("ess2") == 1 and r.get("match_ripser")
        for r in recs
    )
    sph1 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 2000 and r.get("maxdim") == 1), None)
    sph1_ok = bool(sph1 and sph1.get("match_ripser"))
    sph1_10x = bool(sph1 and (sph1.get("vs_ripser") or 0) >= 10)
    sph1_spat = bool(sph1 and "spatial" in str(sph1.get("pipeline") or ""))
    tor = next((r for r in recs if r["name"] == "torus"), None)
    tor_ok = bool(tor and tor.get("match_ripser") and (tor.get("ess1") == tor.get("ess1_ripser")))
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    uni20 = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 20000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    uni20_ok = bool(uni20 and uni20.get("match_ripser"))
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.38)
    spat5 = bool(uni and "spatial" in str(uni.get("pipeline") or ""))
    spat20 = bool(uni20 and "spatial" in str(uni20.get("pipeline") or ""))
    uni_slow = bool(uni and uni.get("pith_s") and uni["pith_s"] > 0.38)
    uni20_slow = bool(uni20 and uni20.get("pith_s") and uni20["pith_s"] > 1.20)
    tor_10x = bool(tor and (tor.get("vs_ripser") or 0) >= 10)
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I263 edge-frac probe invented bars or broke H0–H2; revert"
    elif spat5 or sph1_spat or uni_slow or not sph1_10x:
        status = "reject"
        summary = "I263 probe pulled dense n=5000 / sphere off all-pairs; revert"
    elif ident and ess_ok and fig_ok and fig2_ok and fig4_ok and fig2_spat and sph_ok and sph1_ok and tor_ok and uni_ok and uni20_ok and uni_10x and uni_hold:
        status = "support"
        vs = uni.get("vs_ripser")
        vs20 = uni20.get("vs_ripser")
        tvs = tor.get("vs_ripser") if tor else None
        svs = sph1.get("vs_ripser") if sph1 else None
        fvs = fig2.get("vs_ripser") if fig2 else None
        f4 = fig4.get("vs_ripser") if fig4 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; figure8 n=2000 spat {fvs:.2f}×; "
            f"n=4000 spat={fig4_spat} {f4:.2f}×; dense n=5000 {vs:.2f}× hold={uni_hold}; "
            f"sphere {svs:.2f}×; n=20000 {vs20:.2f}× spat20={spat20}; torus {tvs:.2f}×"
        )
    elif ident and ess_ok and fig_ok and sph_ok and sph1_ok and tor_ok and uni_ok and uni20_ok:
        status = "hold"
        vs = uni.get("vs_ripser") if uni else None
        vs20 = uni20.get("vs_ripser") if uni20 else None
        tvs = tor.get("vs_ripser") if tor else None
        fvs = fig2.get("vs_ripser") if fig2 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; fig2_spat={fig2_spat} fig4_spat={fig4_spat} "
            f"fig2={fvs}; spat5={spat5}; n=5000 {vs:.2f}×; n=20000 {vs20:.2f}×; "
            f"torus {tvs:.2f}× t10={tor_10x}"
        )
    else:
        status = "reject"
        summary = "I263 edge-frac identity or H0–H2 hold failed"

    write(
        {
            "id": "edge_frac_spatial_gate",
            "lever": "H09-redzed-edge-frac-probe",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "figure8_n2000_spatial": fig2_spat,
            "figure8_n4000_spatial": fig4_spat,
            "figure8_n4000": fig4_ok,
            "spatial_n5000": spat5,
            "spatial_n20000": spat20,
            "uniform2_10x": uni_10x,
            "sphere_10x": sph1_10x,
            "torus_10x": tor_10x,
            "receipts": recs,
        },
        "I263",
    )
    print(f"I263 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
