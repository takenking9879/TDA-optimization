#!/usr/bin/env python3
"""I287: harder I286 split — H0+H1+H2 at more 3D points.

I286 sphere n=2000 maxdim=2 is 203 ms / ess2=1. Push n=4000/8000
on the same split (H1 thicken + α=1 H2). Keep the wave short:
pith-only at large n; Ripser only on two_spheres n=400 + holds.
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
        ("split", "sphere", 2000, 1.4, sphere, 2, False),
        ("split", "sphere", 4000, 1.4, sphere, 2, False),
        ("split", "sphere", 8000, 1.4, sphere, 2, False),
        ("split", "figure8", 8000, 1.1, figure8, 2, False),
        ("split", "two_spheres", 400, 1.4, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 45 if n >= 8000 else 30
        if engine == "split":
            pa, cs, ta = pith_dvr_split(path, T, dim, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            try:
                rdim = 2 if dim >= 2 and name != "figure8" else min(dim, 1)
                pr, tr = ripser_d(path, T, rdim, 60)
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
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I287 {rec}", flush=True)
        recs.append(rec)

    s2 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 2000), None)
    s4 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 4000), None)
    s8 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 8000), None)
    fig = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8"), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)

    scale_ok = bool(
        s2 and s2.get("pipeline") == "pith:delaunay-vr-split" and s2.get("ess2") == 1
        and s4 and s4.get("ess2") == 1 and s4.get("pith_s") and s4["pith_s"] < 2.0
        and s8 and s8.get("ess2") == 1 and s8.get("pith_s") and s8["pith_s"] < 5.0
        and fig and fig.get("ess1") == 2 and fig.get("pith_s") and fig["pith_s"] < 2.0
        and two and two.get("ess2") == 2
    )
    hold = bool(
        h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h2 and h2.get("match") and h2.get("ess2") == 1
    )
    if scale_ok and hold:
        status = "support"
        summary = (
            f"split sphere n=2k {s2.get('pith_s'):.3f}s; n=4k {s4.get('pith_s'):.3f}s "
            f"{s4.get('n_dist')}e ess2=1; n=8k {s8.get('pith_s'):.3f}s {s8.get('n_dist')}e; "
            f"figure8 n=8k {fig.get('pith_s'):.3f}s ess1=2; two_spheres ess2=2"
        )
    elif scale_ok:
        status = "hold"
        summary = "split scale held; exact-default hold failed"
    else:
        status = "reject"
        summary = "I287 split scale failed"

    write(
        {
            "id": "delaunay_vr_split_scale",
            "lever": "H16-delaunay-vr-split-scale",
            "class": "algorithm",
            "fidelity": "ess-h2 + empirical-h1",
            "status": status,
            "summary": summary,
            "scale_ok": scale_ok,
            "hold": hold,
            "receipts": recs,
        },
        "I287",
    )
    print(f"I287 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
