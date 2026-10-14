#!/usr/bin/env python3
"""I310: circumcenter+r² insphere (replace 4×4 det on non-sliver tets).

I309 cached tet orient and lost — the det itself is the 80k wall.
Parallel CircumBall so Tet stays compact. Hard: sphere n=100000
H0+H1+H2 and figure8 n=24000 H1. Exact auto hold.
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
        ("split", "sphere", 50000, 1.4, sphere, 2, False),
        ("split", "sphere", 80000, 1.4, sphere, 2, False),
        ("split", "sphere", 100000, 1.4, sphere, 2, False),
        ("split", "two_spheres", 400, 1.4, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 120 if n >= 80000 else (90 if n >= 30000 else 60)
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
        print(f"I310 {rec}", flush=True)
        recs.append(rec)

    fig2 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 2000), None)
    fig16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 16000), None)
    fig24 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 24000), None)
    sph4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 400), None)
    sph16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 16000), None)
    sph50 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 50000), None)
    sph80 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 80000), None)
    sph100 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 100000), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)
    circ = next((r for r in recs if r["name"] == "circle_noisy"), None)

    invented = any((r.get("unmatched") or 0) > 0 and r.get("engine") == "auto" for r in recs)
    fig_ok = bool(
        fig2 and fig2.get("ess1") == 2 and fig2.get("match")
        and fig16 and fig16.get("ess1") == 2
        and fig24 and fig24.get("ess1") == 2
    )
    sph_ok = bool(
        sph4 and sph4.get("ess2") == 1
        and sph16 and sph16.get("ess2") == 1 and sph16.get("n_dist") == 80641
        and sph50 and sph50.get("ess2") == 1
        and sph80 and sph80.get("ess2") == 1
        and sph100 and sph100.get("ess2") == 1
        and two and two.get("ess2") == 2
    )
    hold = bool(
        not invented
        and h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h2 and h2.get("match") and h2.get("ess2") == 1
        and circ and circ.get("match")
    )
    # I306: 50k 0.651s metric 303; 80k 1.09s metric 507.
    sph50_cut = bool(sph50 and sph50.get("pith_s") and sph50["pith_s"] < 0.55)
    sph80_cut = bool(sph80 and sph80.get("pith_s") and sph80["pith_s"] < 0.90)
    metric_cut = bool(sph80 and sph80.get("metric_ms") and sph80["metric_ms"] < 400)
    sph100_ok = bool(sph100 and sph100.get("pith_s") and sph100["pith_s"] < 1.80 and sph100.get("ess2") == 1)
    fig_hold = bool(fig16 and fig16.get("pith_s") and fig16["pith_s"] < 0.65 and fig16.get("ess1") == 2)
    fig24_ok = bool(fig24 and fig24.get("pith_s") and fig24["pith_s"] < 1.10 and fig24.get("ess1") == 2)
    slower = bool(
        (sph80 and sph80.get("pith_s") and sph80["pith_s"] > 1.25)
        or (sph50 and sph50.get("pith_s") and sph50["pith_s"] > 0.80)
    )
    if invented:
        status = "reject"
        summary = "I310 invented exact-default bars"
    elif not fig_ok or not sph_ok:
        status = "reject"
        summary = "I310 identity or ess failed"
    elif hold and slower:
        status = "reject"
        summary = f"slower than I306 (sphere n=80000 {sph80.get('pith_s')}s)"
    elif hold and fig_hold and (sph50_cut or sph80_cut or metric_cut or sph100_ok):
        status = "support"
        summary = (
            f"circumball insphere; sphere n=50000 {sph50.get('pith_s'):.3f}s metric {sph50.get('metric_ms')}ms; "
            f"n=80000 {sph80.get('pith_s'):.3f}s metric {sph80.get('metric_ms')}ms; "
            f"n=100000 {sph100.get('pith_s'):.3f}s |E|={sph100.get('n_dist')} ess2=1; "
            f"figure8 n=24000 {fig24.get('pith_s'):.3f}s ess1=2"
        )
    elif hold and fig_hold and sph_ok:
        status = "hold"
        summary = (
            f"ess held; no metric cut (sphere n=80000 {sph80.get('pith_s')}s "
            f"metric {sph80.get('metric_ms')}ms, n=100000 {sph100.get('pith_s')}s)"
        )
    else:
        status = "reject"
        summary = "I310 exact-default or 2D hold failed"

    write(
        {
            "id": "circumball_insphere",
            "lever": "H16-circumball-insphere",
            "class": "algorithm",
            "fidelity": "ess-h2 + empirical-h1-2d",
            "status": status,
            "summary": summary,
            "fig_ok": fig_ok,
            "sph_ok": sph_ok,
            "hold": hold,
            "sph50_cut": sph50_cut,
            "sph80_cut": sph80_cut,
            "metric_cut": metric_cut,
            "sph100_ok": sph100_ok,
            "fig_hold": fig_hold,
            "fig24_ok": fig24_ok,
            "slower": slower,
            "receipts": recs,
        },
        "I310",
    )
    print(f"I310 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
