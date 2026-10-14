#!/usr/bin/env python3
"""I251: inline the empty-seed leftover-coface skip in the H1 loop.

I250 skip-collect stays. 97% of leftovers never enter active_enum_lazy.
Hard cases: uniform2 n=5000 (I250 10.0× / 0.34s) and n=6000 (10.1× /
0.43s). Reconfirm torus n=2000 (historical RedZeD 12× holdout).
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
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "uniform2", 6000, 0.32, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 5000 else (60 if n >= 4000 or dim >= 2 or name == "torus" else 45)
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
        print(f"I251 {rec}", flush=True)
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
    tor = next((r for r in recs if r["name"] == "torus"), None)
    tor_ok = bool(tor and tor.get("match_ripser") and (tor.get("ess1") == tor.get("ess1_ripser")))
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    uni6 = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 6000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    uni6_ok = bool(uni6 and uni6.get("match_ripser"))
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni6_10x = bool(uni6 and (uni6.get("vs_ripser") or 0) >= 10)
    uni_cut = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.34)
    tor_10x = bool(tor and (tor.get("vs_ripser") or 0) >= 10)

    if ident and ess_ok and fig_ok and sph_ok and tor_ok and uni_ok and uni6_ok and uni_10x and uni6_10x:
        status = "support"
        vs = uni.get("vs_ripser")
        vs6 = uni6.get("vs_ripser")
        tvs = tor.get("vs_ripser") if tor else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; uniform2 10× ({vs:.2f}×/{vs6:.2f}×); "
            f"torus {tvs:.2f}×"
        )
    elif ident and ess_ok and fig_ok and sph_ok and tor_ok and uni_ok and uni6_ok:
        status = "hold"
        vs = uni.get("vs_ripser") if uni else None
        vs6 = uni6.get("vs_ripser") if uni6 else None
        tvs = tor.get("vs_ripser") if tor else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; inline skip; "
            f"uniform2 n=5000 {vs:.2f}× cut={uni_cut}; n=6000 {vs6:.2f}×; "
            f"torus {tvs:.2f}× t10={tor_10x}"
        )
    else:
        status = "reject"
        summary = "I251 inline-skip identity or H0–H2 hold failed"

    write(
        {
            "id": "inline_empty_seed_skip",
            "lever": "H09-redzed-inline-skip",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "uniform2_cut": uni_cut,
            "uniform2_10x": uni_10x,
            "uniform2_n6000_10x": uni6_10x,
            "torus_10x": tor_10x,
            "receipts": recs,
        },
        "I251",
    )
    print(f"I251 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
