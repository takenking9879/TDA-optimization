#!/usr/bin/env python3
"""I277: Delaunay-VR local-radius thicken (H1).

α=1.5 added edges with d≤1.5·r_v (r_v = longest Delaunay spoke).
Probe recovered exact H1 on figure8/circle/torus/blobs/uniform2.
H2 stays I276 (thicken explodes tets). Hard: figure8 n=4000 H1 vs Ripser
if it stays under ~20s; else n=2000 exact + n=8000 clock-only.
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
from run_wave100 import two_spheres  # noqa: E402


def pith_dvr(path, T, dim, alpha=1.5, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--no-enclosing"]
    if dim <= 1:
        cmd += ["--delaunay-alpha", str(alpha)]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("dvr", "unit_square", 4, 2.0, None, 1, True),
        ("dvr", "figure8", 200, 1.0, figure8, 1, True),
        ("dvr", "two_circles", 200, 1.2, two_circles, 1, True),
        ("dvr", "circle_noisy", 500, 1.5, circle_noisy, 1, True),
        ("dvr", "torus", 400, 1.6, torus, 1, True),
        ("dvr", "blobs", 400, 1.0, blobs, 1, True),
        ("dvr", "uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("dvr", "figure8", 2000, 1.1, figure8, 1, True),
        ("dvr", "figure8", 4000, 1.1, figure8, 1, True),
        ("dvr0", "sphere", 80, 1.4, sphere, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
    ]

    for engine, name, n, T, fn, dim, vs_rip in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 or dim >= 2 else 60
        if engine == "dvr":
            pa, cs, ta = pith_dvr(path, T, dim, 1.5, rto)
        elif engine == "dvr0":
            pa, cs, ta = pith_dvr(path, T, dim, 1.0, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs_rip:
            pr, tr = ripser_d(path, T, dim, rto)
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
            "ess0_ripser": ess(pr, 0) if pr is not None else None,
            "ess1": ess(pa, 1),
            "ess1_ripser": ess(pr, 1) if pr is not None else None,
            "ess2": ess(pa, 2),
            "ess2_ripser": ess(pr, 2) if pr is not None else None,
            "bottleneck_h1": bottleneck_h1(pr, pa) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if (tr and ta) else None,
        }
        print(f"I277 {rec}", flush=True)
        recs.append(rec)

    dvr = [r for r in recs if r["engine"] == "dvr" and r.get("ess0_ripser") is not None]
    exact = all(r.get("match_ripser") for r in dvr)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in dvr
    )
    fig2 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 4000), None)
    sph = next((r for r in recs if r["name"] == "sphere" and r["n"] == 80), None)
    b4 = next((r for r in recs if r["name"] == "blobs" and r.get("maxdim") == 0), None)
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] == 5000), None)
    sph400 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 400), None)
    fig2_ok = bool(fig2 and fig2.get("match_ripser") and fig2.get("ess1") == 2)
    fig4_ok = bool(fig4 and fig4.get("match_ripser") and fig4.get("ess1") == 2)
    fig4_fast = bool(fig4 and fig4.get("pith_s") and fig4["pith_s"] < 1.0)
    sph_ok = bool(sph and sph.get("ess2") == 1)
    hold_h0 = bool(b4 and b4.get("ess0") == 3 and b4.get("match_ripser"))
    hold_h1 = bool(uni and uni.get("match_ripser") and (uni.get("vs_ripser") or 0) >= 10)
    hold_h2 = bool(sph400 and sph400.get("ess2") == 1 and sph400.get("match_ripser"))
    invented = any(
        r.get("ess1_ripser") is not None and r.get("ess1") != r.get("ess1_ripser") for r in recs if r["engine"].startswith("dvr")
    )

    if invented or not ess_ok:
        status = "reject"
        summary = "I277 thicken dropped/invented essential bars; revert"
    elif exact and fig2_ok and fig4_ok and fig4_fast and sph_ok and hold_h0 and hold_h1 and hold_h2:
        status = "support"
        summary = (
            f"exact H1 {len(dvr)}/{len(dvr)}; figure8 n=2000 {fig2.get('vs_ripser'):.1f}× / "
            f"{fig2.get('pith_s'):.3f}s {fig2.get('n_dist')}e; n=4000 {fig4.get('vs_ripser'):.1f}× / "
            f"{fig4.get('pith_s'):.3f}s {fig4.get('n_dist')}e"
        )
    elif ess_ok and fig2_ok:
        status = "hold"
        summary = (
            f"ess ok exact={exact}; fig2000 un={fig2.get('unmatched')} "
            f"fig4000 un={fig4.get('unmatched') if fig4 else None} "
            f"t={fig4.get('pith_s') if fig4 else None}s"
        )
    else:
        status = "reject"
        summary = "I277 thicken identity or H0–H2 hold failed"

    write(
        {
            "id": "delaunay_vr_alpha",
            "lever": "H16-delaunay-vr-alpha",
            "class": "algorithm",
            "fidelity": "exact-claimed" if exact else "approx-ess",
            "status": status,
            "summary": summary,
            "all_match": exact,
            "ess_ok": ess_ok,
            "figure8_4000_fast": fig4_fast,
            "hold_h0": hold_h0,
            "hold_h1": hold_h1,
            "hold_h2": hold_h2,
            "receipts": recs,
        },
        "I277",
    )
    print(f"I277 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
