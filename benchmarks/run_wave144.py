#!/usr/bin/env python3
"""I284: harder exact H0 — 2D Delaunay Kruskal at n=25000/50000.

I271 walk-locate is selected for n≤100000. Construction ~linear
(n=12000 27 ms). Hard case: blobs n=50000 vs Ripser H0 if it stays
under ~60s; else n=25000. H1/H2 hold on the exact default.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, sphere, uniform  # noqa: E402
from run_suite import compare  # noqa: E402
from run_wave85 import ensure_cloud, figure8, write  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("auto", "blobs", 12000, 1.0, blobs, 0, True),
        ("auto", "blobs", 25000, 1.0, blobs, 0, True),
        ("auto", "blobs", 50000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 25000 else 60
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
        print(f"I284 {rec}", flush=True)
        recs.append(rec)

    b12 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 12000), None)
    b25 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 25000), None)
    b50 = next((r for r in recs if r["name"] == "blobs" and r["n"] == 50000), None)
    fig = next((r for r in recs if r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    sph = next((r for r in recs if r["name"] == "sphere"), None)
    h0_ok = bool(
        b12 and b12.get("match") and b12.get("ess0") == 3
        and b25 and b25.get("ess0") == 3 and b25.get("pith_s") and b25["pith_s"] < 1.0
        and b50 and b50.get("ess0") == 3 and b50.get("pith_s") and b50["pith_s"] < 2.0
    )
    h0_exact = bool(b12 and b12.get("match") and b25 and b25.get("match") and b50 and b50.get("match"))
    hold_h1 = bool(
        fig and fig.get("match") and fig.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
    )
    hold_h2 = bool(sph and sph.get("match") and sph.get("ess2") == 1)
    delaunay = bool(b50 and b50.get("pipeline") and "delaunay" in str(b50.get("pipeline")))

    if h0_ok and h0_exact and hold_h1 and hold_h2 and delaunay:
        status = "support"
        summary = (
            f"exact H0; n=12000 {b12.get('vs_ref'):.1f}× / {b12.get('pith_s'):.3f}s; "
            f"n=25000 {b25.get('vs_ref'):.1f}× / {b25.get('pith_s'):.3f}s {b25.get('n_dist')}e; "
            f"n=50000 {b50.get('vs_ref'):.1f}× / {b50.get('pith_s'):.3f}s {b50.get('n_dist')}e"
        )
    elif h0_ok and hold_h1 and hold_h2:
        status = "hold"
        summary = (
            f"H0 fast ess=3; exact={h0_exact} n=50000 t={b50.get('pith_s') if b50 else None}s "
            f"match={b50.get('match') if b50 else None}"
        )
    else:
        status = "reject"
        summary = "I284 H0 scale or H1/H2 hold failed"

    write(
        {
            "id": "h0_scale_50k",
            "lever": "H16-h0-scale-50k",
            "class": "algorithm",
            "fidelity": "exact-claimed" if h0_exact else "ess-only",
            "status": status,
            "summary": summary,
            "h0_exact": h0_exact,
            "hold_h1": hold_h1,
            "hold_h2": hold_h2,
            "receipts": recs,
        },
        "I284",
    )
    print(f"I284 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
