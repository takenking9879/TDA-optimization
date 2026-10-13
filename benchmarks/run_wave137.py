#!/usr/bin/env python3
"""I276: Delaunay-flag VR (optional, not exact).

Flag of the Euclidean Delaunay 1-skeleton. Θ(n) edges. Keep essential
H0/H1/H2; quantify unmatched finite bars vs Ripser. Hard H1: figure8
n=8000 (skip Ripser — too slow). H0/H2 hold on the exact default.
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


def pith_delaunay_vr(path, T, dim, timeout=60):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--delaunay-vr", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_sparse(path, T, dim, timeout=60):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--sparse-eps", "0.6", "--no-enclosing"],
        timeout,
    )
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
        ("dvr", "sphere", 80, 1.4, sphere, 2, True),
        ("dvr", "two_spheres", 200, 1.4, two_spheres, 2, True),
        ("dvr", "torus", 400, 1.6, torus, 1, True),
        ("dvr", "figure8", 2000, 1.1, figure8, 1, True),
        ("dvr", "figure8", 8000, 1.1, figure8, 1, False),
        ("sparse", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
    ]

    for engine, name, n, T, fn, dim, vs_rip in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 or dim >= 2 else 60
        if engine == "dvr":
            pa, cs, ta = pith_delaunay_vr(path, T, dim, rto)
        elif engine == "sparse":
            pa, cs, ta = pith_sparse(path, T, dim, rto)
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
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if (tr and ta) else None,
        }
        print(f"I276 {rec}", flush=True)
        recs.append(rec)

    dvr = [r for r in recs if r["engine"] == "dvr" and r.get("ess0_ripser") is not None]
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in dvr
    )
    fig = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000 and r["engine"] == "dvr"), None)
    fig8k = next((r for r in recs if r["name"] == "figure8" and r["n"] == 8000 and r["engine"] == "dvr"), None)
    sph = next((r for r in recs if r["name"] == "sphere" and r["n"] == 80), None)
    two_c = next((r for r in recs if r["name"] == "two_circles"), None)
    sparse = next((r for r in recs if r["engine"] == "sparse"), None)
    b4 = next((r for r in recs if r["name"] == "blobs" and r.get("maxdim") == 0), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    sph400 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 400), None)
    fig_ok = bool(fig and fig.get("ess1") == 2 and fig.get("ess1_ripser") == 2)
    fig8k_ok = bool(fig8k and fig8k.get("ess1") == 2 and fig8k.get("pith_s") and fig8k["pith_s"] < 0.10)
    sph_ok = bool(sph and sph.get("ess2") == 1)
    two_ok = bool(two_c and two_c.get("ess1") == 2)
    hold_h0 = bool(b4 and b4.get("ess0") == 3 and b4.get("match_ripser"))
    hold_h1 = bool(uni and uni.get("match_ripser") and (uni.get("vs_ripser") or 0) >= 10)
    hold_h2 = bool(sph400 and sph400.get("ess2") == 1 and sph400.get("match_ripser"))
    size_ok = bool(fig and fig.get("n_dist") is not None and fig["n_dist"] < 20000)
    invented_ess = any(
        r.get("ess1_ripser") is not None and r.get("ess1") != r.get("ess1_ripser") for r in dvr
    ) or any(r.get("ess2_ripser") is not None and r.get("ess2") != r.get("ess2_ripser") for r in dvr)

    if invented_ess or not ess_ok:
        status = "reject"
        summary = "I276 Delaunay-VR dropped or invented essential bars; revert"
    elif ess_ok and fig_ok and fig8k_ok and sph_ok and two_ok and hold_h0 and hold_h1 and hold_h2 and size_ok:
        status = "support"
        summary = (
            f"ess {len(dvr)}/{len(dvr)}; figure8 n=2000 {fig.get('vs_ripser'):.1f}× / "
            f"{fig.get('pith_s'):.3f}s {fig.get('n_dist')}e un={fig.get('unmatched')}; "
            f"n=8000 {fig8k.get('pith_s'):.3f}s ess1=2; sparse {sparse.get('vs_ripser') if sparse else None}×"
        )
    elif ess_ok and fig_ok and sph_ok:
        status = "hold"
        summary = (
            f"ess ok; fig2000={fig.get('pith_s')}s un={fig.get('unmatched')} "
            f"fig8000={fig8k.get('pith_s') if fig8k else None}s"
        )
    else:
        status = "reject"
        summary = "I276 Delaunay-VR identity or H0–H2 hold failed"

    write(
        {
            "id": "delaunay_vr",
            "lever": "H16-delaunay-vr",
            "class": "algorithm",
            "fidelity": "approx-ess",
            "status": status,
            "summary": summary,
            "ess_ok": ess_ok,
            "figure8_2000_10x": bool(fig and (fig.get("vs_ripser") or 0) >= 10),
            "figure8_8000_fast": fig8k_ok,
            "size_ok": size_ok,
            "hold_h0": hold_h0,
            "hold_h1": hold_h1,
            "hold_h2": hold_h2,
            "receipts": recs,
        },
        "I276",
    )
    print(f"I276 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
