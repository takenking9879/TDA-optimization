#!/usr/bin/env python3
"""I255: unique-diameter leftover-coface = nonempty rbit AND.

When every edge diameter is unique, any common neighbor of leftover {u,v}
at time r has strictly shorter other edges, so {u,v} is the youngest face.
Skip coface_ready. Tied diameters keep vendor coface_ready (unit square).
H2 unchanged. Harder scale: uniform2 n=8000.
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
        ("auto", "uniform2", 7000, 0.30, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "uniform2", 8000, 0.28, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 150 if n >= 8000 else (120 if n >= 7000 else (90 if n >= 5000 else (60 if n >= 4000 or dim >= 2 or name == "torus" else 45)))
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
            "n_cc": cs.get("collapse_trims"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        print(f"I255 {rec}", flush=True)
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
    sq = next((r for r in recs if r["name"] == "unit_square"), None)
    sq_ok = bool(sq and sq.get("match_ripser") and sq.get("ess1") == 0)
    sph1 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 2000 and r.get("maxdim") == 1), None)
    sph1_ok = bool(sph1 and sph1.get("match_ripser") and sph1.get("ess1") == sph1.get("ess1_ripser"))
    sph1_10x = bool(sph1 and (sph1.get("vs_ripser") or 0) >= 10)
    tor = next((r for r in recs if r["name"] == "torus"), None)
    tor_ok = bool(tor and tor.get("match_ripser") and (tor.get("ess1") == tor.get("ess1_ripser")))
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    uni7 = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 7000), None)
    uni8 = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 8000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    uni7_ok = bool(uni7 and uni7.get("match_ripser"))
    uni8_ok = bool(uni8 and uni8.get("match_ripser"))
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni7_10x = bool(uni7 and (uni7.get("vs_ripser") or 0) >= 10)
    uni8_10x = bool(uni8 and (uni8.get("vs_ripser") or 0) >= 10)
    # I252 pith: n=5000 0.298s, n=7000 0.506s.
    uni_cut = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.29)
    uni7_cut = bool(uni7 and uni7.get("pith_s") and uni7["pith_s"] < 0.50)
    uni_slow = bool(uni and uni.get("pith_s") and uni["pith_s"] > 0.32)
    tor_10x = bool(tor and (tor.get("vs_ripser") or 0) >= 10)

    if uni_slow:
        status = "reject"
        summary = "I255 unique-diam leftover-coface slower than I252; revert"
    elif (
        ident
        and ess_ok
        and fig_ok
        and sph_ok
        and sq_ok
        and sph1_ok
        and tor_ok
        and uni_ok
        and uni7_ok
        and uni8_ok
        and uni_10x
        and (uni_cut or uni7_cut)
    ):
        status = "support"
        vs = uni.get("vs_ripser")
        vs7 = uni7.get("vs_ripser") if uni7 else None
        vs8 = uni8.get("vs_ripser") if uni8 else None
        tvs = tor.get("vs_ripser") if tor else None
        svs = sph1.get("vs_ripser") if sph1 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; uniform2 10× ({vs:.2f}×); "
            f"n=7000 {vs7:.2f}×; n=8000 {vs8:.2f}×; sphere H1 {svs:.2f}×; torus {tvs:.2f}×"
        )
    elif ident and ess_ok and fig_ok and sph_ok and sq_ok and sph1_ok and tor_ok and uni_ok and uni7_ok and uni8_ok:
        status = "hold"
        vs = uni.get("vs_ripser") if uni else None
        vs7 = uni7.get("vs_ripser") if uni7 else None
        vs8 = uni8.get("vs_ripser") if uni8 else None
        tvs = tor.get("vs_ripser") if tor else None
        svs = sph1.get("vs_ripser") if sph1 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; unique-diam leftover-coface; "
            f"uniform2 n=5000 {vs:.2f}× cut={uni_cut}; n=7000 {vs7:.2f}× t10={uni7_10x}; "
            f"n=8000 {vs8:.2f}× t10={uni8_10x}; sphere H1 {svs:.2f}× t10={sph1_10x}; "
            f"torus {tvs:.2f}× t10={tor_10x}"
        )
    else:
        status = "reject"
        summary = "I255 unique-diam leftover-coface identity or H0–H2 hold failed"

    write(
        {
            "id": "unique_diam_leftover_coface",
            "lever": "H09-redzed-unique-diam-leftover-coface",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "uniform2_cut": uni_cut,
            "uniform2_n7000_cut": uni7_cut,
            "uniform2_10x": uni_10x,
            "uniform2_n7000_10x": uni7_10x,
            "uniform2_n8000_10x": uni8_10x,
            "sphere_h1_10x": sph1_10x,
            "torus_10x": tor_10x,
            "receipts": recs,
        },
        "I255",
    )
    print(f"I255 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
