#!/usr/bin/env python3
"""I242: vendor-faithful owned H1 AE vs Ripser / RedZeD / auto.

Incremental register_active + leftover-coface erase-without-pair +
combinatorial coface_ready. I236/I237 paired on leftover-coface and
pre-registered every leftover — that invented finite H1. maxdim≥2 keeps
the I232 walk (vendor AE is H1-only). Shape-agnostic.

Hard case: connected uniform2 n=5000 H1 (more points than the I241
n=4000 wall, still seconds). H0–H2 identity must hold.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
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
    # engine, name, n, T, fn, dim
    jobs = [
        ("active", "unit_square", 4, 2.0, None, 1),
        ("active", "figure8", 200, 1.0, figure8, 1),  # I236 killer
        ("active", "two_circles", 200, 1.2, two_circles, 1),
        ("active", "circle_noisy", 500, 1.5, circle_noisy, 1),
        ("active", "torus", 200, 1.8, torus, 1),
        ("active", "blobs", 500, 1.0, blobs, 1),
        ("active", "uniform2", 1000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("active", "sphere", 80, 1.4, sphere, 2),
        ("auto", "two_spheres", 200, 1.4, two_spheres, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),  # hard
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
            if name == "uniform2" and dim == 1:
                pz, cz, tz = pith_redzed_d(path, T, dim, rto)
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
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "probes": cs.get("cofacet_probes"),
            "n_cc": cs.get("collapse_trims"),
            "n_distances": cs.get("distances"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        if tz is not None:
            rec["redzed_s"] = tz
            rec["redzed_pipe"] = cz.get("pipeline")
            rec["vs_redzed"] = (tz / ta) if ta else None
            rec["redzed_vs_ripser"] = (tr / tz) if tz else None
        print(f"I242 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig = next((r for r in recs if r["name"] == "figure8"), None)
    fig_ok = bool(fig and fig.get("match_ripser") and fig.get("ess1") == 2)
    sph = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2 and r["engine"] == "active"), None)
    sph_ok = bool(sph and sph.get("match_ripser") and sph.get("ess2") == 1)
    two_sph = next((r for r in recs if r["name"] == "two_spheres"), None)
    two_sph_ok = bool(two_sph and two_sph.get("match_ripser") and two_sph.get("ess2") == 2)
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 5000), None)
    uni_ok = bool(uni and uni.get("match_ripser"))
    ae_rows = [r for r in recs if r["engine"] == "active" and r.get("redzed_s")]
    ae_faster = sum(1 for r in ae_rows if (r.get("vs_redzed") or 0) >= 1.0)
    ae_10x = sum(1 for r in ae_rows if (r.get("vs_ripser") or 0) >= 10)

    if ident and ess_ok and fig_ok and sph_ok and two_sph_ok and uni_ok and ae_10x == len(ae_rows) and ae_faster == len(ae_rows):
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; owned AE 10× and beats RedZeD"
    elif ident and ess_ok and fig_ok and sph_ok and two_sph_ok and uni_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; AE identity (figure8 2=2); "
            f"vs_redzed_win={ae_faster}/{len(ae_rows)}; vs_ripser_10x={ae_10x}/{len(ae_rows)}"
        )
    else:
        status = "reject"
        summary = "I242 vendor-faithful AE identity or H0–H2 hold failed"

    write(
        {
            "id": "vendor_faithful_owned_ae",
            "lever": "H09-owned-ae-vendor-cf",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "figure8_ok": fig_ok,
            "sphere_h2_ok": sph_ok,
            "two_spheres_ok": two_sph_ok,
            "uniform2_hard_ok": uni_ok,
            "ae_faster_than_redzed": ae_faster,
            "ae_10x": ae_10x,
            "receipts": recs,
        },
        "I242",
    )
    print(f"I242 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
