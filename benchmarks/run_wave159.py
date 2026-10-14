#!/usr/bin/env python3
"""I299: RCM relabel fat thicken before RedZeD leftover.

rbit AND walks a contiguous word range. Input IDs need not be local.
Same flag complex. Hard: figure8 n=24000 and sphere n=20000 H0+H1+H2.
Do not apply RCM to persist_redzed_from_points (I268).
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, uniform  # noqa: E402
from run_suite import compare  # noqa: E402
from run_wave85 import ensure_cloud, figure8, write  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402
from run_wave146 import pith_dvr_split  # noqa: E402


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("split", "figure8", 2000, 1.1, figure8, 2, True),
        ("split", "figure8", 16000, 1.1, figure8, 2, False),
        ("split", "figure8", 24000, 1.1, figure8, 2, False),
        ("split", "sphere", 400, 1.4, sphere, 2, True),
        ("split", "sphere", 16000, 1.4, sphere, 2, False),
        ("split", "sphere", 20000, 1.4, sphere, 2, False),
        ("split", "two_spheres", 400, 1.4, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 16000 else 60
        if engine == "split":
            pa, cs, ta = pith_dvr_split(path, T, dim, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            try:
                cmp_dim = min(dim, 1) if name == "figure8" else dim
                pr, tr = ripser_d(path, T, cmp_dim, rto)
                fid = compare(pr, pa, cmp_dim)
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
            "ess1": ess(pa, 1),
            "ess1_ref": ess(pr, 1) if pr is not None else None,
            "ess2": ess(pa, 2),
            "ess2_ref": ess(pr, 2) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "n_dist": cs.get("distances"),
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I299 {rec}", flush=True)
        recs.append(rec)

    fig2 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 2000), None)
    fig16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 16000), None)
    fig24 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 24000), None)
    sph4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 400), None)
    sph16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 16000), None)
    sph20 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 20000), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)
    circ = next((r for r in recs if r["name"] == "circle_noisy"), None)

    invented = any((r.get("unmatched") or 0) > 0 and r.get("engine") == "auto" for r in recs)
    edges_ok = bool(
        fig16 and fig16.get("n_dist") == 977068
        and sph16 and sph16.get("n_dist") == 2283282
        and fig24 and fig24.get("n_dist") == 1490848
        and sph20 and sph20.get("n_dist") == 2904919
    )
    split_ok = bool(
        fig2 and fig2.get("ess1") == 2 and fig2.get("match")
        and fig16 and fig16.get("ess1") == 2
        and fig24 and fig24.get("ess1") == 2
        and sph4 and sph4.get("ess2") == 1
        and sph16 and sph16.get("ess2") == 1
        and sph20 and sph20.get("ess2") == 1
        and two and two.get("ess2") == 2
        and edges_ok
    )
    hold = bool(
        not invented
        and h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h2 and h2.get("match") and h2.get("ess2") == 1
        and circ and circ.get("match")
    )
    # I298: figure8 16k 0.623s reduce 195; 24k 1.02s; sphere 16k 3.08s reduce 1988; 20k 3.92s.
    fig16_cut = bool(fig16 and fig16.get("pith_s") and fig16["pith_s"] < 0.55)
    sph16_cut = bool(sph16 and sph16.get("pith_s") and sph16["pith_s"] < 2.70)
    sph20_cut = bool(sph20 and sph20.get("pith_s") and sph20["pith_s"] < 3.40)
    reduce_cut = bool(sph16 and sph16.get("reduce_ms") and sph16["reduce_ms"] < 1600)
    if invented or not edges_ok:
        status = "reject"
        summary = "I299 RCM-on-thicken dropped edges or invented bars"
    elif not split_ok:
        status = "reject"
        summary = "I299 identity or scale failed"
    elif hold and (fig16_cut or sph16_cut or sph20_cut or reduce_cut):
        status = "support"
        summary = (
            f"same edges; figure8 n=16000 {fig16.get('pith_s'):.3f}s reduce {fig16.get('reduce_ms')}ms; "
            f"n=24000 {fig24.get('pith_s'):.3f}s; "
            f"sphere n=16000 {sph16.get('pith_s'):.3f}s reduce {sph16.get('reduce_ms')}ms; "
            f"n=20000 {sph20.get('pith_s'):.3f}s ess2=1"
        )
    elif hold:
        status = "hold"
        summary = (
            f"same edges; no pith cut (figure8 n=16000 {fig16.get('pith_s')}s reduce {fig16.get('reduce_ms')}ms, "
            f"sphere n=16000 {sph16.get('pith_s')}s reduce {sph16.get('reduce_ms')}ms)"
        )
    else:
        status = "reject"
        summary = "I299 exact-default hold failed"

    write(
        {
            "id": "rcm_thicken_redzed",
            "lever": "H16-rcm-thicken-redzed",
            "class": "algorithm",
            "fidelity": "ess-h2 + empirical-h1",
            "status": status,
            "summary": summary,
            "split_ok": split_ok,
            "hold": hold,
            "edges_ok": edges_ok,
            "fig16_cut": fig16_cut,
            "sph16_cut": sph16_cut,
            "sph20_cut": sph20_cut,
            "reduce_cut": reduce_cut,
            "receipts": recs,
        },
        "I299",
    )
    print(f"I299 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
