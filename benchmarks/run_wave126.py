#!/usr/bin/env python3
"""I265: unique-diam rbit-AND leftover-coface on the spatial hash path.

I255 was exact on all-pairs (no pith cut: matrix get is cheap).
Spatial leftover_coface pays two SparseDist hash gets per hit.
Unique leftover diameter ⇒ those gets are redundant.
Hard case: figure8 n=4000 T=1.1 (I263 reduce 866 ms). Dense 10× must hold.
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
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 or dim >= 2 or name == "torus" else 60
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
        print(f"I265 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig2 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] >= 4000), None)
    fig2_ok = bool(fig2 and fig2.get("match_ripser") and fig2.get("ess1") == 2)
    fig4_ok = bool(fig4 and fig4.get("match_ripser") and fig4.get("ess1") == 2)
    fig4_cut = bool(fig4 and fig4.get("reduce_ms") and fig4["reduce_ms"] < 780)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    sph1 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 2000), None)
    sph2 = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2), None)
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.38)
    spat5 = bool(uni and "spatial" in str(uni.get("pipeline") or ""))
    sph_ok = bool(sph2 and sph2.get("ess2") == 1 and sph2.get("match_ripser"))
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I265 unique-diam AND invented bars or broke H0–H2; revert"
    elif spat5 or not uni_hold:
        status = "reject"
        summary = "I265 unique-diam AND pulled/slowed dense n=5000; revert"
    elif ident and ess_ok and fig2_ok and fig4_ok and fig4_cut and sph_ok and uni_10x:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; figure8 n=4000 reduce {fig4.get('reduce_ms'):.0f} ms "
            f"{fig4.get('vs_ripser'):.2f}×; n=2000 {fig2.get('vs_ripser'):.2f}×; "
            f"dense {uni.get('vs_ripser'):.2f}×"
        )
    elif ident and ess_ok and fig2_ok and fig4_ok and sph_ok:
        status = "hold"
        red = fig4.get("reduce_ms") if fig4 else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; figure8 n=4000 reduce {red:.0f} ms cut={fig4_cut}; "
            f"dense {uni.get('vs_ripser') if uni else None}×"
        )
    else:
        status = "reject"
        summary = "I265 unique-diam AND identity or H0–H2 hold failed"

    write(
        {
            "id": "unique_diam_and_spatial",
            "lever": "H09-redzed-unique-diam-and-spatial",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "figure8_n4000_reduce_cut": fig4_cut,
            "uniform2_10x": uni_10x,
            "receipts": recs,
        },
        "I265",
    )
    print(f"I265 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
