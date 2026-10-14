#!/usr/bin/env python3
"""I239: exact G_T component split + parallel RedZeD.

VR≤T of a disconnected threshold graph is the direct sum of the
components. Split, RedZeD each block (bounded thread pool), merge bars.
Hard case: blobs n=4000 / n=6000 (3 clusters, T=1; more points, still
seconds). Must hold H0–H2 identity and circle/sphere collapse.
Connected uniform2 is the remaining 10× wall (1 component).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

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
from run_wave95 import ess, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402


def two_spheres(n, rng):
    half = n // 2
    a = sphere(half, rng)
    b = sphere(n - half, rng) + np.array([5.0, 0.0, 0.0])
    return np.vstack([a, b])


def main():
    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("sphere", 400, 1.4, sphere, 2),
        ("two_spheres", 200, 1.4, two_spheres, 2),  # H0+H2 wedge
        ("blobs", 2000, 1.0, blobs, 1),
        ("blobs", 4000, 1.0, blobs, 1),  # hard: 3-way split
        ("blobs", 6000, 1.0, blobs, 1),  # more points, still seconds
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r), 1),
    ]

    for name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 6000 else (60 if n >= 4000 or dim >= 2 else 45)
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_auto(path, T, dim, rto)
        fid = compare(pr, pa, dim)
        rec = {
            "name": name, "n": n, "T": T, "maxdim": dim,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0), "ess0_ripser": ess(pr, 0),
            "ess1": ess(pa, 1), "ess1_ripser": ess(pr, 1),
            "ess2": ess(pa, 2), "ess2_ripser": ess(pr, 2),
            "bottleneck_h1": bottleneck_h1(pr, pa),
            "pipeline": cs.get("pipeline"),
            "residual_frac": cs.get("residual_frac"),
            "metric_ms": cs.get("metric_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_cc": cs.get("collapse_trims"),
            "auto_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        if name != "unit_square" and (n <= 2000 or name == "two_spheres"):
            try:
                pz, cz, tz = pith_redzed_d(path, T, dim, rto)
                zfid = compare(pr, pz, dim)
                rec["forced_redzed_s"] = tz
                rec["forced_redzed_cc"] = cz.get("collapse_trims")
                rec["forced_redzed_pipe"] = cz.get("pipeline")
                rec["forced_redzed_match"] = zfid.get("exact_match_tol")
                rec["forced_redzed_unmatched"] = zfid.get("unmatched")
            except Exception as ex:  # noqa: BLE001
                rec["redzed_err"] = str(ex)[:160]
        print(f"I239 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    circle_ok = all(
        r.get("pipeline") == "pith:auto-collapse"
        for r in recs if r["name"] == "circle_noisy" and r["n"] >= 400
    )
    sph = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2), None)
    sph_ok = bool(sph and sph.get("pipeline") == "pith:auto-collapse" and sph.get("match_ripser"))
    two_sph = next((r for r in recs if r["name"] == "two_spheres"), None)
    two_sph_ok = bool(
        two_sph
        and two_sph.get("match_ripser")
        and two_sph.get("ess0") == 2
        and two_sph.get("ess2") == 2
    )
    blob_rows = [r for r in recs if r["name"] == "blobs" and r["n"] >= 4000]
    blob_cc = all((r.get("n_cc") or 0) >= 2 and "redzed-cc" in (r.get("pipeline") or "")
                  for r in blob_rows)
    blob_10x = sum(1 for r in blob_rows if (r.get("vs_ripser") or 0) >= 10)
    uni = next((r for r in recs if r["name"] == "uniform2" and r["n"] >= 4000), None)
    uni_10x = bool(uni and (uni.get("vs_ripser") or 0) >= 10)

    if ident and ess_ok and circle_ok and sph_ok and two_sph_ok and blob_cc and blob_10x == len(blob_rows) and uni_10x:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; blobs n=4000+ 10× and uniform2 10×"
    elif ident and ess_ok and circle_ok and sph_ok and two_sph_ok and blob_cc and blob_10x == len(blob_rows):
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; disconnected blobs 10× "
            f"({blob_10x}/{len(blob_rows)}); uniform2 connected still <10×"
        )
    elif ident and ess_ok and circle_ok and sph_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; cc-split identity; "
            f"blob_10x={blob_10x}/{len(blob_rows)} blob_cc={blob_cc}"
        )
    else:
        status = "reject"
        summary = "I239 component-split identity or dispatch failed"

    write(
        {
            "id": "redzed_component_split",
            "lever": "H09-cc-split",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "circle_collapse": circle_ok,
            "sphere_h2_collapse": sph_ok,
            "two_spheres_h2": two_sph_ok,
            "blob_cc": blob_cc,
            "blob_10x": blob_10x,
            "uniform2_10x": uni_10x,
            "receipts": recs,
        },
        "I239",
    )
    print(f"I239 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
