#!/usr/bin/env python3
"""I286: split H1 thicken from α=1 H2 so one Euclidean path keeps both.

`--delaunay-vr --delaunay-alpha auto --maxdim 2` used to force α=1
(H2 thicken explodes). Split: H0/H1 on the thickened 1-skeleton,
H2 on the α=1 Delaunay flag. Hard case: sphere n=2000 H0+H1+H2
(pith-only) plus figure8 n=4000 H1 under maxdim=2.
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


def pith_dvr_split(path, T, dim, timeout=60):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--delaunay-vr", "--delaunay-alpha", "auto", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("split", "figure8", 2000, 1.1, figure8, 2, True, 1),
        ("split", "figure8", 4000, 1.1, figure8, 2, False, None),
        ("split", "sphere", 400, 1.4, sphere, 2, True, 2),
        ("split", "sphere", 2000, 1.4, sphere, 2, False, None),
        ("split", "two_spheres", 200, 1.4, two_spheres, 2, True, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True, 0),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2, True, 2),
    ]
    for engine, name, n, T, fn, dim, vs, cmp_dim in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 60
        if engine == "split":
            pa, cs, ta = pith_dvr_split(path, T, dim, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            try:
                # figure8 dim=2 vs Ripser H2 is tet-heavy; compare H1 only.
                rdim = cmp_dim if cmp_dim is not None else dim
                pr, tr = ripser_d(path, T, rdim, rto)
                fid = compare(pr, pa, rdim)
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
        print(f"I286 {rec}", flush=True)
        recs.append(rec)

    fig2 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 2000), None)
    fig4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 4000), None)
    sph4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 400), None)
    sph2k = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 2000), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)

    split_ok = bool(
        fig2 and fig2.get("pipeline") == "pith:delaunay-vr-split"
        and fig2.get("ess1") == 2 and fig2.get("match")
        and fig4 and fig4.get("pipeline") == "pith:delaunay-vr-split"
        and fig4.get("ess1") == 2 and fig4.get("pith_s") and fig4["pith_s"] < 1.5
        and sph4 and sph4.get("ess2") == 1
        and sph2k and sph2k.get("ess2") == 1 and sph2k.get("pith_s") and sph2k["pith_s"] < 2.0
        and two and two.get("ess2") == 2
    )
    hold = bool(
        h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h2 and h2.get("match") and h2.get("ess2") == 1
    )
    if split_ok and hold:
        status = "support"
        vs = f"{fig2.get('vs_ref'):.1f}× / " if fig2.get("vs_ref") else ""
        summary = (
            f"split figure8 n=2000 H1 match ess1=2 {vs}{fig2.get('pith_s'):.3f}s; "
            f"n=4000 {fig4.get('pith_s'):.3f}s {fig4.get('n_dist')}e; "
            f"sphere n=400 ess2=1; n=2000 {sph2k.get('pith_s'):.3f}s ess2=1; "
            f"two_spheres ess2=2"
        )
    elif split_ok:
        status = "hold"
        summary = "split identity held; exact-default hold failed"
    else:
        status = "reject"
        summary = "I286 split H1/H2 failed"

    write(
        {
            "id": "delaunay_vr_split_h1h2",
            "lever": "H16-delaunay-vr-split-h1h2",
            "class": "algorithm",
            "fidelity": "ess-h2 + empirical-h1",
            "status": status,
            "summary": summary,
            "split_ok": split_ok,
            "hold": hold,
            "receipts": recs,
        },
        "I286",
    )
    print(f"I286 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
