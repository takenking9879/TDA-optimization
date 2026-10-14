#!/usr/bin/env python3
"""I292: skip out-of-ball grid cells in Delaunay thicken.

Same edges as I277–I287 (cell lower-bound is exact). Hard:
figure8 n=16000 and sphere n=16000 H0+H1+H2. Auto H0–H2 hold.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, sphere, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
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
        ("split", "figure8", 4000, 1.1, figure8, 2, False),
        ("split", "figure8", 16000, 1.1, figure8, 2, False),
        ("split", "sphere", 400, 1.4, sphere, 2, True),
        ("split", "sphere", 8000, 1.4, sphere, 2, False),
        ("split", "sphere", 16000, 1.4, sphere, 2, False),
        ("split", "two_spheres", 400, 1.4, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
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
                pr, tr = ripser_d(path, T, min(dim, 1) if name == "figure8" else dim, rto)
                fid = compare(pr, pa, min(dim, 1) if name == "figure8" else dim)
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
        print(f"I292 {rec}", flush=True)
        recs.append(rec)

    fig2 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 2000), None)
    fig4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 4000), None)
    fig16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 16000), None)
    sph4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 400), None)
    sph8 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 8000), None)
    sph16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 16000), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)

    edges_ok = bool(
        fig4 and fig4.get("n_dist") == 186241
        and fig16 and fig16.get("n_dist") == 977068
        and sph8 and sph8.get("n_dist") == 1073583
    )
    split_ok = bool(
        fig2 and fig2.get("ess1") == 2 and fig2.get("match")
        and fig4 and fig4.get("ess1") == 2
        and fig16 and fig16.get("ess1") == 2 and fig16.get("pith_s") and fig16["pith_s"] < 3.0
        and sph4 and sph4.get("ess2") == 1
        and sph8 and sph8.get("ess2") == 1
        and sph16 and sph16.get("ess2") == 1 and sph16.get("pith_s") and sph16["pith_s"] < 8.0
        and two and two.get("ess2") == 2
        and edges_ok
    )
    hold = bool(
        h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h2 and h2.get("match") and h2.get("ess2") == 1
    )
    fig16_cut = bool(fig16 and fig16.get("pith_s") and fig16["pith_s"] < 0.80)
    sph8_cut = bool(sph8 and sph8.get("pith_s") and sph8["pith_s"] < 1.15)
    if not edges_ok:
        status = "reject"
        summary = "I292 cell skip dropped thicken edges; revert"
    elif not split_ok:
        status = "reject"
        summary = "I292 identity or hard-case scale failed"
    elif hold and (fig16_cut or sph8_cut):
        status = "support"
        summary = (
            f"same edges; figure8 n=16000 {fig16.get('pith_s'):.3f}s "
            f"metric {fig16.get('metric_ms')}ms; "
            f"sphere n=8000 {sph8.get('pith_s'):.3f}s (I287 1.42s); "
            f"n=16000 {sph16.get('pith_s'):.3f}s ess2=1"
        )
    elif hold:
        status = "hold"
        summary = (
            f"same edges; no pith cut (figure8 n=16000 {fig16.get('pith_s')}s, "
            f"sphere n=8000 {sph8.get('pith_s')}s)"
        )
    else:
        status = "reject"
        summary = "I292 exact-default hold failed"

    write(
        {
            "id": "delaunay_thicken_cell_skip",
            "lever": "H16-delaunay-thicken-cell-skip",
            "class": "algorithm",
            "fidelity": "ess-h2 + empirical-h1",
            "status": status,
            "summary": summary,
            "split_ok": split_ok,
            "hold": hold,
            "edges_ok": edges_ok,
            "fig16_cut": fig16_cut,
            "sph8_cut": sph8_cut,
            "receipts": recs,
        },
        "I292",
    )
    print(f"I292 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
