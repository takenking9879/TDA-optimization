#!/usr/bin/env python3
"""I269: tight LiveBits AND-eq + Morton on the collapse path.

I268 A/B: figure8 n=4000 collapse is 845 ms / 1.97M fast trims — same
Θ(|E|) as RedZeD leftover visits. AND-eq still scanned all n/64 words.
Morton + [rlo,rhi] is for collapse only (I268 layout on RedZeD was 5%).
Hard case: --engine implicit figure8 n=4000. H0–H2 auto must hold.
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
from run_suite import PITH, parse_pith_text, run_cmd  # noqa: E402
from run_wave95 import ess, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402


def pith_implicit_d(path, T, dim, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


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
        ("implicit", "figure8", 2000, 1.1, figure8, 1),
        ("implicit", "figure8", 4000, 1.1, figure8, 1),
        ("auto", "figure8", 2000, 1.1, figure8, 1),
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
        if engine == "redzed":
            pa, cs, ta = pith_redzed_d(path, T, dim, rto)
        elif engine == "implicit":
            pa, cs, ta = pith_implicit_d(path, T, dim, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
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
            "collapse_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_dist": cs.get("distances"),
            "n_cc": cs.get("collapse_trims"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        print(f"I269 {rec}", flush=True)
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
    fig_imp = next(
        (r for r in recs if r["name"] == "figure8" and r["n"] == 4000 and r["engine"] == "implicit"),
        None,
    )
    fig_auto = next(
        (r for r in recs if r["name"] == "figure8" and r["n"] == 2000 and r["engine"] == "auto"),
        None,
    )
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)
    uni_hold = bool(uni and uni.get("pith_s") and uni["pith_s"] < 0.38)
    fig_imp_ok = bool(fig_imp and fig_imp.get("ess1") == 2 and fig_imp.get("match_ripser"))
    fig_auto_ok = bool(fig_auto and fig_auto.get("ess1") == 2 and fig_auto.get("match_ripser"))
    # I268 A/B collapse_ms 845. Need a real trim-walk cut.
    fig_cut = bool(fig_imp and fig_imp.get("collapse_ms") and fig_imp["collapse_ms"] < 700)
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I269 collapse live-range invented bars or broke H0–H2; revert"
    elif ident and ess_ok and sph_ok and sph400_ok and fig_imp_ok and fig_auto_ok and fig_cut and uni_10x and uni_hold:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; implicit figure8 n=4000 collapse "
            f"{fig_imp.get('collapse_ms'):.0f} vs I268 845 ms / {fig_imp.get('vs_ripser'):.1f}×; "
            f"dense {uni.get('vs_ripser'):.2f}×"
        )
    elif ident and ess_ok and sph_ok and fig_imp_ok:
        status = "hold"
        cms = fig_imp.get("collapse_ms") if fig_imp else None
        summary = (
            f"exact {len(recs)}/{len(recs)}; implicit figure8 n=4000 collapse {cms} vs 845; "
            f"dense {uni.get('vs_ripser') if uni else None}×"
        )
    else:
        status = "reject"
        summary = "I269 identity or H0–H2 hold failed"

    write(
        {
            "id": "collapse_live_and_morton",
            "lever": "H04-collapse-live-and-morton",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "figure8_collapse_cut": fig_cut,
            "uniform2_10x": uni_10x,
            "receipts": recs,
        },
        "I269",
    )
    print(f"I269 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
