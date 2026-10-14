#!/usr/bin/env python3
"""I280: 2-hop adaptive Delaunay thicken.

R_v = α · max(r_v, max_{Delaunay nbr} r_u), optional floor · median(r).
Goal: keep a small stable α instead of raising 1.5→2.25 with n.
Config chosen after probe_i280_adapt.py; default wave uses α=1.5+adapt.
Hard: figure8 n=8000 vs RedZeD. H2 stays α=1. Exact default hold.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
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


ALPHA = 1.5
FLOOR = 0.0
ADAPT = True


def pith_dvr(path, T, dim, alpha=ALPHA, adapt=ADAPT, floor=FLOOR, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--no-enclosing"]
    if dim <= 1:
        cmd += ["--delaunay-alpha", str(alpha)]
        if adapt:
            cmd.append("--delaunay-adapt")
        if floor:
            cmd += ["--delaunay-floor", str(floor)]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("dvr", "figure8", 200, 1.0, figure8, 1, "rip"),
        ("dvr", "two_circles", 200, 1.2, two_circles, 1, "rip"),
        ("dvr", "circle_noisy", 500, 1.5, circle_noisy, 1, "rip"),
        ("dvr", "torus", 400, 1.6, torus, 1, "rip"),
        ("dvr", "blobs", 400, 1.0, blobs, 1, "rip"),
        ("dvr", "uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r), 1, "rip"),
        ("dvr", "figure8", 2000, 1.1, figure8, 1, "rip"),
        ("dvr", "figure8", 4000, 1.1, figure8, 1, "rip"),
        ("dvr", "figure8", 8000, 1.1, figure8, 1, "redzed"),
        ("dvr0", "sphere", 80, 1.4, sphere, 2, "rip"),
        ("auto", "blobs", 4000, 1.0, blobs, 0, "rip"),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, "rip"),
        ("auto", "sphere", 400, 1.4, sphere, 2, "rip"),
    ]

    for engine, name, n, T, fn, dim, oracle in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 120 if n >= 8000 else (90 if n >= 4000 or dim >= 2 else 60)
        if engine == "dvr":
            pa, cs, ta = pith_dvr(path, T, dim, ALPHA, ADAPT, FLOOR, rto)
        elif engine == "dvr0":
            pa, cs, ta = pith_dvr(path, T, dim, 1.0, False, 0, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if oracle == "rip":
            pr, tr = ripser_d(path, T, dim, rto)
            fid = compare(pr, pa, dim)
        elif oracle == "redzed":
            pr, _, tr = pith_redzed_d(path, T, dim, rto)
            fid = compare(pr, pa, dim)
        rec = {
            "engine": engine,
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "oracle": oracle,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0),
            "ess0_ref": ess(pr, 0) if pr is not None else None,
            "ess1": ess(pa, 1),
            "ess1_ref": ess(pr, 1) if pr is not None else None,
            "ess2": ess(pa, 2),
            "ess2_ref": ess(pr, 2) if pr is not None else None,
            "bottleneck_h1": bottleneck_h1(pr, pa) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I280 {rec}", flush=True)
        recs.append(rec)

    dvr = [r for r in recs if r["engine"] == "dvr" and r.get("ess0_ref") is not None]
    exact = all(r.get("match") for r in dvr)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ref")
        and r.get("ess1") == r.get("ess1_ref")
        and r.get("ess2") == r.get("ess2_ref")
        for r in dvr
    )
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 4000), None)
    fig8 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 8000), None)
    blobs_r = next((r for r in recs if r["name"] == "blobs" and r["engine"] == "dvr"), None)
    sph = next((r for r in recs if r["name"] == "sphere" and r["n"] == 80), None)
    b4 = next((r for r in recs if r["name"] == "blobs" and r.get("maxdim") == 0), None)
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    sph400 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 400), None)
    fig4_ok = bool(fig4 and fig4.get("match") and fig4.get("ess1") == 2)
    fig8_ok = bool(fig8 and fig8.get("match") and fig8.get("ess1") == 2)
    blobs_ok = bool(blobs_r and blobs_r.get("match"))
    sph_ok = bool(sph and sph.get("ess2") == 1)
    hold_h0 = bool(b4 and b4.get("ess0") == 3 and b4.get("match"))
    hold_h1 = bool(uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10)
    hold_h2 = bool(sph400 and sph400.get("ess2") == 1 and sph400.get("match"))
    invented = any(
        r.get("ess1_ref") is not None and r.get("ess1") != r.get("ess1_ref")
        for r in recs
        if r["engine"].startswith("dvr")
    )
    fewer_than_i279 = bool(fig8 and fig8.get("n_dist") and fig8["n_dist"] < 428139)

    if invented or not ess_ok:
        status = "reject"
        summary = "I280 adapt dropped/invented essential bars"
    elif exact and fig4_ok and fig8_ok and blobs_ok and sph_ok and hold_h0 and hold_h1 and hold_h2:
        status = "support"
        summary = (
            f"exact H1 {len(dvr)}/{len(dvr)} α=1.5+adapt; n=4000 {fig4.get('vs_ref'):.1f}× / "
            f"{fig4.get('pith_s'):.3f}s; n=8000 {fig8.get('vs_ref'):.1f}× / {fig8.get('pith_s'):.3f}s "
            f"{fig8.get('n_dist')}e fewer_than_I279={fewer_than_i279}"
        )
    elif ess_ok:
        status = "hold"
        summary = (
            f"ess ok exact={exact}; blobs un={blobs_r.get('unmatched') if blobs_r else None} "
            f"fig8000 un={fig8.get('unmatched') if fig8 else None}"
        )
    else:
        status = "reject"
        summary = "I280 adapt identity or H0–H2 hold failed"

    write(
        {
            "id": "delaunay_vr_adapt",
            "lever": "H16-delaunay-vr-adapt",
            "class": "algorithm",
            "fidelity": "exact-claimed" if exact else "approx-ess",
            "status": status,
            "summary": summary,
            "all_match": exact,
            "ess_ok": ess_ok,
            "fewer_than_i279": fewer_than_i279,
            "hold_h0": hold_h0,
            "hold_h1": hold_h1,
            "hold_h2": hold_h2,
            "receipts": recs,
        },
        "I280",
    )
    print(f"I280 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
