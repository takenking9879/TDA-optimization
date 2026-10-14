#!/usr/bin/env python3
"""I285: harder exact 3D H0 — walk-locate Delaunay Kruskal at n=30k/50k.

I275 is selected for d=3, n∈[256,50000]. I284 did 2D blobs n=25k/50k.
Hard 3D: sphere n=30000/50000 vs Ripser H0 if it stays under ~90s.
H1/H2 hold on the exact default.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import sphere, uniform  # noqa: E402
from run_suite import compare  # noqa: E402
from run_wave85 import ensure_cloud, figure8, write  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("auto", "sphere", 16000, 1.4, sphere, 0, True),
        ("auto", "sphere", 30000, 1.4, sphere, 0, True),
        ("auto", "sphere", 50000, 1.4, sphere, 0, False),  # pith-only; Ripser H0 too slow
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 16000 else 60
        pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            try:
                pr, tr = ripser_d(path, T, dim, rto)
                fid = compare(pr, pa, dim)
            except Exception as e:
                fid = {"error": str(e)}
        rec = {
            "engine": engine,
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0),
            "ess0_ref": ess(pr, 0) if pr is not None else None,
            "ess1": ess(pa, 1),
            "ess1_ref": ess(pr, 1) if pr is not None else None,
            "ess2": ess(pa, 2),
            "ess2_ref": ess(pr, 2) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "n_dist": cs.get("distances"),
            "metric_ms": cs.get("metric_ms"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I285 {rec}", flush=True)
        recs.append(rec)

    s16 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 16000 and r["maxdim"] == 0), None)
    s30 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 30000 and r["maxdim"] == 0), None)
    s50 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 50000 and r["maxdim"] == 0), None)
    fig = next((r for r in recs if r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    sph2 = next((r for r in recs if r["name"] == "sphere" and r["maxdim"] == 2), None)
    delaunay = all(
        r.get("pipeline") and "delaunay" in str(r.get("pipeline"))
        for r in (s16, s30, s50)
        if r
    )
    h0_ok = bool(
        s16 and s16.get("match") and s16.get("ess0") == 1
        and s30 and s30.get("ess0") == 1 and s30.get("pith_s") and s30["pith_s"] < 2.0
        and s50 and s50.get("ess0") == 1 and s50.get("pith_s") and s50["pith_s"] < 2.0
        and delaunay
    )
    h0_exact = bool(s16 and s16.get("match") and s30 and s30.get("match"))
    hold_h1 = bool(
        fig and fig.get("match") and fig.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
    )
    hold_h2 = bool(sph2 and sph2.get("match") and sph2.get("ess2") == 1)

    if h0_ok and h0_exact and hold_h1 and hold_h2:
        status = "support"
        summary = (
            f"exact 3D H0 n=16k {s16.get('vs_ref'):.1f}× / {s16.get('pith_s'):.3f}s; "
            f"n=30k {s30.get('vs_ref'):.1f}× / {s30.get('pith_s'):.3f}s {s30.get('n_dist')}e; "
            f"n=50k {s50.get('pith_s'):.3f}s {s50.get('n_dist')}e"
        )
    elif h0_ok and hold_h1 and hold_h2:
        status = "hold"
        summary = (
            f"3D H0 fast; exact={h0_exact} n=30k match={s30.get('match') if s30 else None} "
            f"n=50k t={s50.get('pith_s') if s50 else None}s"
        )
    else:
        status = "reject"
        summary = "I285 3D H0 scale or H1/H2 hold failed"

    write(
        {
            "id": "h0_3d_scale_50k",
            "lever": "H16-h0-3d-scale-50k",
            "class": "algorithm",
            "fidelity": "exact-claimed" if h0_exact else "ess-only",
            "status": status,
            "summary": summary,
            "h0_exact": h0_exact,
            "hold_h1": hold_h1,
            "hold_h2": hold_h2,
            "receipts": recs,
        },
        "I285",
    )
    print(f"I285 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
