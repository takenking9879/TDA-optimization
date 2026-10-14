#!/usr/bin/env python3
"""I238: lazy parallel points→RedZeD metric (skip n×n vector<vector>).

Auto-redzed no longer builds a full pairwise matrix before reduce.
Probe uses a 250-point subsample from the cloud. Collapse path unchanged.
Hard case: blobs/uniform2 n=4000 (RedZeD reduce wall, still seconds).
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import compare, parse_pith_text  # noqa: E402
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


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("sphere", 400, 1.4, sphere, 2),
        ("blobs", 2000, 1.0, blobs, 1),
        ("uniform2", 2000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("torus", 2000, 1.6, torus, 1),
        ("blobs", 4000, 1.0, blobs, 1),  # hard: reduce wall
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r), 1),
    ]

    for name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 60 if n >= 4000 else 45
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
            "auto_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        if n <= 2000 and dim == 1:
            try:
                _, _, tz = pith_redzed_d(path, T, dim, rto)
                rec["forced_redzed_s"] = tz
            except Exception as ex:  # noqa: BLE001
                rec["redzed_err"] = str(ex)[:160]
        print(f"I238 {rec}", flush=True)
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
    losers = [r for r in recs if r["name"] in {"blobs", "uniform2"} and r["n"] >= 4000]
    loser_10x = sum(1 for r in losers if (r.get("vs_ripser") or 0) >= 10)
    sph = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim", 0) >= 2), None)
    sph_ok = bool(sph and sph.get("pipeline") == "pith:auto-collapse" and sph.get("match_ripser"))

    if ident and ess_ok and circle_ok and sph_ok and loser_10x == len(losers) and losers:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; blobs/uniform2 n=4000 now 10×"
    elif ident and ess_ok and circle_ok and sph_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; lazy metric; "
            f"loser_10x={loser_10x}/{len(losers)}"
        )
    else:
        status = "reject"
        summary = "I238 lazy-metric identity or dispatch failed"

    write(
        {
            "id": "lazy_redzed_metric",
            "lever": "H09-lazy-metric",
            "class": "implementation",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "circle_collapse": circle_ok,
            "sphere_h2_collapse": sph_ok,
            "loser_10x": loser_10x,
            "receipts": recs,
        },
        "I238",
    )
    print(f"I238 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
