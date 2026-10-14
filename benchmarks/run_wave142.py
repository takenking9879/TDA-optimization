#!/usr/bin/env python3
"""I281: harder H2 scale (exact + optional Delaunay-flag).

H0 and H1 already have linear Delaunay paths (I271/I275/I279).
H2 thicken explodes. This wave pushes exact auto H2 past n=400
and measures optional `--delaunay-vr` H2 at n=400/800 vs Ripser.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, sphere, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import bottleneck_h1, ensure_cloud, figure8, write  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402


def pith_dvr(path, T, dim, timeout=60):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--delaunay-vr", "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("auto", "sphere", 400, 1.4, sphere, 2, True),
        ("auto", "sphere", 800, 1.4, sphere, 2, True),
        ("dvr", "sphere", 80, 1.4, sphere, 2, True),
        ("dvr", "sphere", 400, 1.4, sphere, 2, True),
        ("dvr", "sphere", 800, 1.4, sphere, 2, True),
        ("dvr", "two_spheres", 200, 1.5, two_spheres, 2, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, True),
        ("dvr1", "figure8", 4000, 1.1, figure8, 1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, True),
    ]

    for engine, name, n, T, fn, dim, vs in jobs:
        path = ensure_cloud(name, n, fn, rng)
        rto = 90 if (n >= 800 and dim >= 2) or n >= 4000 else 60
        if engine == "dvr":
            pa, cs, ta = pith_dvr(path, T, dim, rto)
        elif engine == "dvr1":
            cmd = [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
                   "--delaunay-vr", "--delaunay-alpha", "2.25", "--no-enclosing"]
            out, ta, _ = run_cmd(cmd, rto)
            pa, cs = parse_pith_text(out)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            pr, tr = ripser_d(path, T, dim, rto)
            fid = compare(pr, pa, dim)
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
            "bottleneck_h1": bottleneck_h1(pr, pa) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I281 {rec}", flush=True)
        recs.append(rec)

    a400 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere" and r["n"] == 400), None)
    a800 = next((r for r in recs if r["engine"] == "auto" and r["name"] == "sphere" and r["n"] == 800), None)
    d400 = next((r for r in recs if r["engine"] == "dvr" and r["name"] == "sphere" and r["n"] == 400), None)
    d800 = next((r for r in recs if r["engine"] == "dvr" and r["name"] == "sphere" and r["n"] == 800), None)
    ts = next((r for r in recs if r["name"] == "two_spheres"), None)
    b4 = next((r for r in recs if r["name"] == "blobs"), None)
    fig = next((r for r in recs if r["name"] == "figure8"), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    exact_h2 = bool(a400 and a400.get("match") and a400.get("ess2") == 1)
    hard_h2 = bool(a800 and a800.get("match") and a800.get("ess2") == 1)
    dvr_ess = bool(
        d400 and d400.get("ess2") == 1
        and d800 and d800.get("ess2") == 1
        and ts and ts.get("ess2") == ts.get("ess2_ref")
    )
    hold_h0 = bool(b4 and b4.get("match") and b4.get("ess0") == 3)
    hold_h1 = bool(
        fig and fig.get("match") and fig.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
    )
    invented = any(
        r.get("ess2_ref") is not None and r.get("ess2") != r.get("ess2_ref") for r in recs if r["maxdim"] >= 2
    )

    if invented:
        status = "reject"
        summary = "I281 H2 dropped/invented essential voids"
    elif exact_h2 and hard_h2 and dvr_ess and hold_h0 and hold_h1:
        status = "support"
        summary = (
            f"exact H2 n=400 {a400.get('vs_ref'):.1f}× / {a400.get('pith_s'):.3f}s; "
            f"n=800 {a800.get('vs_ref'):.1f}× / {a800.get('pith_s'):.3f}s; "
            f"dvr n=400 ess2=1 un={d400.get('unmatched')} {d400.get('pith_s'):.3f}s; "
            f"n=800 un={d800.get('unmatched')} {d800.get('pith_s'):.3f}s"
        )
    elif exact_h2 and dvr_ess and hold_h0 and hold_h1:
        status = "hold"
        summary = f"exact n=400 hold; hard n=800 match={a800.get('match') if a800 else None}"
    else:
        status = "reject"
        summary = "I281 H2 scale or H0/H1 hold failed"

    write(
        {
            "id": "h2_scale",
            "lever": "H16-h2-scale",
            "class": "algorithm",
            "fidelity": "exact-claimed" if hard_h2 else "mixed",
            "status": status,
            "summary": summary,
            "exact_h2_800": hard_h2,
            "dvr_ess": dvr_ess,
            "hold_h0": hold_h0,
            "hold_h1": hold_h1,
            "receipts": recs,
        },
        "I281",
    )
    print(f"I281 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
