#!/usr/bin/env python3
"""I243: incremental rbit neighborhoods on exact owned AE.

I242 pairing held. Generation was still a neighbor-list walk.
Word-AND rbits (advance by leftover diameter) replace that walk.
Same pairing. Hard case: connected uniform2 n=5000 H1 (hold vs I242).
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, uniform  # noqa: E402
from run_suite import compare  # noqa: E402
from run_wave85 import (  # noqa: E402
    bottleneck_h1,
    ensure_cloud,
    figure8,
    two_circles,
    unit_square_path,
    write,
)
from run_wave95 import ess, pith_active_d, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402
from run_wave100 import two_spheres  # noqa: E402


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("active", "unit_square", 4, 2.0, None, 1),
        ("active", "figure8", 200, 1.0, figure8, 1),
        ("active", "two_circles", 200, 1.2, two_circles, 1),
        ("active", "circle_noisy", 500, 1.5, circle_noisy, 1),
        ("active", "uniform2", 1000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("active", "sphere", 80, 1.4, sphere, 2),
        ("auto", "two_spheres", 200, 1.4, two_spheres, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "blobs", 4000, 1.0, blobs, 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 5000 else (60 if n >= 4000 or dim >= 2 else 45)
        pr, tr = ripser_d(path, T, dim, rto)
        if engine == "active":
            pa, cs, ta = pith_active_d(path, T, dim, rto)
            pz, cz, tz = pith_redzed_d(path, T, dim, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
            pz, cz, tz = (None, {}, None)
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
            "ess0_ripser": ess(pr, 0),
            "ess1": ess(pa, 1),
            "ess1_ripser": ess(pr, 1),
            "ess2": ess(pa, 2),
            "ess2_ripser": ess(pr, 2),
            "bottleneck_h1": bottleneck_h1(pr, pa),
            "pipeline": cs.get("pipeline"),
            "reduce_ms": cs.get("reduce_ms"),
            "probes": cs.get("cofacet_probes"),
            "n_cc": cs.get("collapse_trims"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        if tz is not None:
            rec["redzed_s"] = tz
            rec["vs_redzed"] = (tz / ta) if ta else None
        print(f"I243 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig_ok = any(r["name"] == "figure8" and r.get("ess1") == 2 and r.get("match_ripser") for r in recs)
    sph_ok = any(
        r["name"] == "sphere" and r.get("maxdim", 0) >= 2 and r.get("ess2") == 1 and r.get("match_ripser")
        for r in recs
    )
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 5000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    circ = next((r for r in recs if r["name"] == "circle_noisy" and r["engine"] == "active"), None)
    # I242 circle AE was 0.379s / 0.058× RedZeD. Need a real cut, not noise.
    circ_cut = bool(circ and circ.get("pith_s") and circ["pith_s"] < 0.30)
    circ_beats_zed = bool(circ and (circ.get("vs_redzed") or 0) >= 1.0)

    if ident and ess_ok and fig_ok and sph_ok and uni_ok and circ_beats_zed:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; rbit AE beats RedZeD"
    elif ident and ess_ok and fig_ok and sph_ok and uni_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; rbit identity; "
            f"circle_cut={circ_cut} vs_redzed={circ.get('vs_redzed') if circ else None}"
        )
    else:
        status = "reject"
        summary = "I243 rbit AE identity or H0–H2 hold failed"

    write(
        {
            "id": "rbit_owned_ae",
            "lever": "H09-owned-ae-rbit",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "circle_cut": circ_cut,
            "receipts": recs,
        },
        "I243",
    )
    print(f"I243 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
