#!/usr/bin/env python3
"""I247: exact leftover-coface fast path (H1 strict-shorter common neighbor).

I246 skip-insert stays. Equal-diameter youngest-face still uses vendor
coface_ready. Hard cases: connected uniform2 n=5000 (I246 9.56× / 0.35s)
and n=6000 (more points, still seconds).
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
        ("redzed", "unit_square", 4, 2.0, None, 1),
        ("redzed", "figure8", 200, 1.0, figure8, 1),
        ("redzed", "two_circles", 200, 1.2, two_circles, 1),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1),
        ("redzed", "sphere", 80, 1.4, sphere, 2),
        ("auto", "two_spheres", 200, 1.4, two_spheres, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "uniform2", 6000, 0.32, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 5000 else (60 if n >= 4000 or dim >= 2 else 45)
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
        print(f"I247 {rec}", flush=True)
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
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    uni6 = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 6000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    uni6_ok = bool(uni6 and uni6.get("match_ripser"))
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_cut = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.35)  # I246 was 0.35s

    if ident and ess_ok and fig_ok and sph_ok and uni_ok and uni6_ok and uni_10x:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; connected uniform2 n=5000 10×"
    elif ident and ess_ok and fig_ok and sph_ok and uni_ok and uni6_ok:
        status = "hold"
        vs = uni.get("vs_ripser") if uni else None
        vs6 = uni6.get("vs_ripser") if uni6 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; leftover-coface fast; "
            f"uniform2 n=5000 {vs:.2f}× cut={uni_cut}; n=6000 {vs6:.2f}×"
        )
    else:
        status = "reject"
        summary = "I247 leftover-coface fast identity or H0–H2 hold failed"

    write(
        {
            "id": "leftover_coface_fast",
            "lever": "H09-redzed-coface-fast",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "uniform2_cut": uni_cut,
            "uniform2_10x": uni_10x,
            "uniform2_n6000_ok": uni6_ok,
            "receipts": recs,
        },
        "I247",
    )
    print(f"I247 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
