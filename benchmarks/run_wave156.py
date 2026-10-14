#!/usr/bin/env python3
"""I296: memoize D(e) coboundaries for implicit V-adds.

Not reduced R (I290/I295). Same heap pushes. Hard: figure8 n=4000
collapse=0 (I289 24 s / 103M probes) and sphere n=16000 H0+H1+H2.
Collapse=1 identity must hold.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8, write  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402
from run_wave146 import pith_dvr_split  # noqa: E402


def pith_implicit(path, T, dim, collapse, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "implicit", "--collapse", str(collapse), "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("implicit1", "figure8", 200, 1.0, figure8, 1, True),
        ("implicit1", "circle_noisy", 500, 1.5, circle_noisy, 1, True),
        ("implicit0", "figure8", 200, 1.0, figure8, 1, True),
        ("implicit0", "figure8", 2000, 1.1, figure8, 1, True),
        ("implicit0", "figure8", 4000, 1.1, figure8, 1, True),
        ("split", "figure8", 2000, 1.1, figure8, 2, True),
        ("split", "figure8", 16000, 1.1, figure8, 2, False),
        ("split", "sphere", 400, 1.4, sphere, 2, True),
        ("split", "sphere", 16000, 1.4, sphere, 2, False),
        ("split", "two_spheres", 400, 1.4, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1, True),
    ]
    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 else 60
        if engine == "split":
            pa, cs, ta = pith_dvr_split(path, T, dim, rto)
        elif engine.startswith("implicit"):
            pa, cs, ta = pith_implicit(path, T, dim, 0 if engine == "implicit0" else 1, rto)
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
            "assembled": cs.get("cols_assembled"),
            "additions": cs.get("additions"),
            "probes": cs.get("cofacet_probes"),
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I296 {rec}", flush=True)
        recs.append(rec)

    fig2 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 2000), None)
    fig16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "figure8" and r["n"] == 16000), None)
    sph16 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 16000), None)
    sph4 = next((r for r in recs if r["engine"] == "split" and r["name"] == "sphere" and r["n"] == 400), None)
    two = next((r for r in recs if r["name"] == "two_spheres"), None)
    imp0_2 = next((r for r in recs if r["engine"] == "implicit0" and r["n"] == 2000), None)
    imp0_4 = next((r for r in recs if r["engine"] == "implicit0" and r["n"] == 4000), None)
    imp1s = [r for r in recs if r["engine"] == "implicit1"]
    h0 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "blobs"), None)
    h1 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h2 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere"), None)
    circ = next((r for r in recs if r["engine"] == "auto" and r["name"] == "circle_noisy"), None)

    invented = any((r.get("unmatched") or 0) > 0 and r.get("engine") in ("implicit0", "implicit1", "auto") for r in recs)
    collapse_ok = all(r.get("match") for r in imp1s) and bool(imp0_2 and imp0_2.get("match"))
    split_ok = bool(
        fig2 and fig2.get("ess1") == 2 and fig2.get("match")
        and fig16 and fig16.get("ess1") == 2 and fig16.get("n_dist") == 977068
        and sph4 and sph4.get("ess2") == 1
        and sph16 and sph16.get("ess2") == 1
        and two and two.get("ess2") == 2
    )
    hold = bool(
        not invented
        and h0 and h0.get("match")
        and h1 and h1.get("match") and h1.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 9.5
        and h2 and h2.get("match") and h2.get("ess2") == 1
        and circ and circ.get("match")
    )
    c0_cut = bool(imp0_4 and imp0_4.get("match") and imp0_4.get("pith_s") and imp0_4["pith_s"] < 8.0)
    c0_2_cut = bool(imp0_2 and imp0_2.get("pith_s") and imp0_2["pith_s"] < 1.5)
    sph16_cut = bool(sph16 and sph16.get("pith_s") and sph16["pith_s"] < 3.20)
    if invented or not collapse_ok:
        status = "reject"
        summary = "I296 D(e) memo invented bars; revert"
    elif not split_ok:
        status = "reject"
        summary = "I296 thicken identity failed"
    elif hold and (c0_cut or sph16_cut):
        status = "support"
        vs = f"{imp0_4.get('vs_ref'):.1f}× / " if imp0_4 and imp0_4.get("vs_ref") else ""
        summary = (
            f"exact; figure8 n=4000 collapse0 {vs}{imp0_4.get('pith_s'):.3f}s "
            f"(I289 24s); sphere n=16000 {sph16.get('pith_s'):.3f}s"
        )
    elif hold and c0_2_cut:
        status = "support"
        summary = (
            f"exact; figure8 n=2000 collapse0 {imp0_2.get('pith_s'):.3f}s "
            f"(I289 2.5s); n=4000 {imp0_4.get('pith_s') if imp0_4 else None}s"
        )
    elif hold:
        status = "hold"
        summary = (
            f"exact; no pith cut (collapse0 n=4000 {imp0_4.get('pith_s') if imp0_4 else None}s, "
            f"sphere n=16000 {sph16.get('pith_s')}s)"
        )
    else:
        status = "reject"
        summary = "I296 exact-default hold failed"

    write(
        {
            "id": "implicit_dcob_memo",
            "lever": "H02-implicit-dcob-memo",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "collapse_ok": collapse_ok,
            "split_ok": split_ok,
            "hold": hold,
            "c0_cut": c0_cut,
            "sph16_cut": sph16_cut,
            "receipts": recs,
        },
        "I296",
    )
    print(f"I296 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
