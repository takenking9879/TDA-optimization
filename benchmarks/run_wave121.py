#!/usr/bin/env python3
"""I260: tighter spatial hash (load ~0.75, occupancy bitmap, no Slot zero).

I259 table-zero wrote 256 MB at n=20000 (metric 192 vs I258 118).
Miss still +∞. Dense stays I238. Hold torus + n=20000 + H0–H2.
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
        ("auto", "torus", 2000, 1.6, torus, 1),
        ("auto", "sphere", 2000, 1.4, sphere, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "uniform2", 20000, 0.09, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 180 if n >= 15000 else (90 if n >= 5000 else (60 if n >= 4000 or dim >= 2 or name == "torus" else 45))
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
        print(f"I260 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig_ok = any(r["name"] == "figure8" and r.get("ess1") == 2 and r.get("match_ripser") for r in recs)
    sph_ok = any(
        r["name"] == "sphere" and r.get("maxdim", 0) >= 2 and r.get("ess2") == 1 and r.get("match_ripser")
        for r in recs
    )
    sph1 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 2000 and r.get("maxdim") == 1), None)
    sph1_ok = bool(sph1 and sph1.get("match_ripser"))
    tor = next((r for r in recs if r["name"] == "torus"), None)
    tor_ok = bool(tor and tor.get("match_ripser") and (tor.get("ess1") == tor.get("ess1_ripser")))
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    uni20 = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 20000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    uni20_ok = bool(uni20 and uni20.get("match_ripser"))
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.34)
    spat20 = bool(uni20 and "spatial" in str(uni20.get("pipeline") or ""))
    dense = bool(uni and "spatial" not in str(uni.get("pipeline") or ""))
    uni_slow = bool(uni and uni.get("pith_s") and uni["pith_s"] > 0.34)
    uni20_slow = bool(uni20 and uni20.get("pith_s") and uni20["pith_s"] > 1.20)
    tor_10x = bool(tor and (tor.get("vs_ripser") or 0) >= 10)
    tor_slow = bool(tor and tor.get("pith_s") and tor["pith_s"] > 0.28)
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)
    # I259 n=20000 metric 192 / pith 1.04; I258 metric 118 / pith 0.99.
    met20 = (uni20.get("metric_ms") or 0) if uni20 else 0
    met_cut = bool(uni20 and met20 and met20 < 140)
    pith20_cut = bool(uni20 and uni20.get("pith_s") and uni20["pith_s"] < 1.00)

    if invented or not ident:
        status = "reject"
        summary = "I260 tight-hash invented bars or broke H0–H2 identity; revert"
    elif uni_slow or uni20_slow or tor_slow:
        status = "reject"
        summary = "I260 tight-hash slowed dense n=5000, n=20000, or torus; revert"
    elif ident and ess_ok and fig_ok and sph_ok and sph1_ok and tor_ok and uni_ok and uni20_ok and uni_10x and spat20 and (met_cut or pith20_cut):
        status = "support"
        vs = uni.get("vs_ripser")
        vs20 = uni20.get("vs_ripser")
        tvs = tor.get("vs_ripser") if tor else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; dense n=5000 {vs:.2f}× hold={uni_hold}; "
            f"n=20000 {vs20:.2f}× metric={met20:.0f} pith={uni20.get('pith_s'):.2f}; "
            f"torus {tvs:.2f}×"
        )
    elif ident and ess_ok and fig_ok and sph_ok and sph1_ok and tor_ok and uni_ok and uni20_ok:
        status = "hold"
        vs = uni.get("vs_ripser") if uni else None
        vs20 = uni20.get("vs_ripser") if uni20 else None
        tvs = tor.get("vs_ripser") if tor else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; spat20={spat20} dense={dense}; "
            f"n=5000 {vs:.2f}×; n=20000 {vs20:.2f}× metric={met20:.0f}; "
            f"torus {tvs:.2f}× t10={tor_10x}"
        )
    else:
        status = "reject"
        summary = "I260 tight-hash identity or H0–H2 hold failed"

    write(
        {
            "id": "sparse_hash_tight",
            "lever": "H09-redzed-sparse-hash-tight",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "spatial_n20000": spat20,
            "dense_n5000": dense,
            "uniform2_10x": uni_10x,
            "torus_10x": tor_10x,
            "n20000_metric_cut": met_cut,
            "receipts": recs,
        },
        "I260",
    )
    print(f"I260 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
