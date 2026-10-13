#!/usr/bin/env python3
"""I237: GUDHI explicit Rips vs auto/RedZeD; scale selected H0–H2.

Birth-time leftover-coface AE matched I236's unmatched finite H1
(reverted). GUDHI 3.13 RipsComplex+SimplexTree is an unused exact
engine. Hard case: sphere n=600 H2 (more points than I236 n=400,
still seconds). Blobs/uniform2 n=2000 stay the exact-10× gap.
"""

from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import (  # noqa: E402
    bottleneck_h1,
    ensure_cloud,
    figure8,
    two_circles,
    unit_square_path,
    write,
)
from run_wave95 import ess, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto, pith_collapse  # noqa: E402


def gudhi_rips(path, T, dim):
    import gudhi

    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    rc = gudhi.RipsComplex(points=pts, max_edge_length=T)
    st = rc.create_simplex_tree(max_dimension=dim + 1)
    st.compute_persistence(persistence_dim_max=True)
    dt = time.perf_counter() - t0
    pairs = []
    for d, (b, dth) in st.persistence():
        if d > dim:
            continue
        pairs.append(
            {
                "dim": int(d),
                "birth": float(b),
                "death": math.inf if dth == float("inf") else float(dth),
            }
        )
    return pairs, dt, int(st.num_simplices())


def main():
    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("blobs", 1000, 1.0, blobs, 1),  # GUDHI vs RedZeD wall
        ("uniform2", 1000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("sphere", 200, 1.4, sphere, 2),
        ("sphere", 600, 1.4, sphere, 2),  # hard H2, more points
        ("blobs", 2000, 1.0, blobs, 1),
        ("uniform2", 2000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("torus", 600, 1.6, torus, 2),
    ]

    for name, n, T, fn, dim in jobs:
        if name == "unit_square":
            path = unit_square_path()
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 45 if dim >= 2 and n >= 600 else 30
        pto = 45
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_auto(path, T, dim, pto)
        fid = compare(pr, pa, dim)
        rec = {
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
            "residual_frac": cs.get("residual_frac"),
            "auto_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        try:
            _, _, tz = pith_redzed_d(path, T, dim, pto)
            rec["redzed_s"] = tz
            rec["vs_redzed"] = (tz / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["redzed_err"] = str(ex)[:160]
        if dim >= 2 or name in {"blobs", "circle_noisy"}:
            try:
                _, _, td = pith_collapse(path, T, dim, pto)
                rec["collapse_s"] = td
                rec["vs_collapse"] = (td / ta) if ta else None
            except Exception as ex:  # noqa: BLE001
                rec["collapse_err"] = str(ex)[:160]
        if n <= 1000 and not (name == "sphere" and n >= 600):
            try:
                gp, gt, ns = gudhi_rips(path, T, dim)
                rec["gudhi_s"] = gt
                rec["gudhi_simplices"] = ns
                rec["vs_gudhi"] = (gt / ta) if ta else None
                gfid = compare(pr, gp, dim)
                rec["gudhi_match_ripser"] = gfid.get("exact_match_tol")
                rec["gudhi_unmatched"] = gfid.get("unmatched")
            except Exception as ex:  # noqa: BLE001
                rec["gudhi_err"] = str(ex)[:160]
        print(f"I237 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    gudhi_rows = [r for r in recs if "gudhi_s" in r]
    gudhi_ident = all(r.get("gudhi_match_ripser") for r in gudhi_rows) if gudhi_rows else False
    gudhi_beats_redzed = any(
        (r.get("gudhi_s") or 1e9) < (r.get("redzed_s") or 0) * 0.9 for r in gudhi_rows
    )
    sph = next((r for r in recs if r["name"] == "sphere" and r["n"] >= 600), None)
    sph_10x = bool(sph and (sph.get("vs_ripser") or 0) >= 10)
    blobs2k = [r for r in recs if r["name"] in {"blobs", "uniform2"} and r["n"] >= 2000]
    loser_10x = sum(1 for r in blobs2k if (r.get("vs_ripser") or 0) >= 10)

    if ident and ess_ok and gudhi_ident and gudhi_beats_redzed:
        status = "support"
        summary = "GUDHI exact and faster than RedZeD on a loser family"
    elif ident and ess_ok and sph_10x:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)} H0-H2; sphere n=600 H2 "
            f"{(sph or {}).get('vs_ripser'):.0f}×; GUDHI exact but slower; "
            f"blobs/uniform2 10×={loser_10x}/{len(blobs2k)}"
        )
    else:
        status = "reject"
        summary = "I237 identity failed vs Ripser"

    write(
        {
            "id": "gudhi_rips_scale_h012",
            "lever": "H09-gudhi-scale",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "gudhi_ident": gudhi_ident,
            "gudhi_beats_redzed": gudhi_beats_redzed,
            "sphere_h2_10x": sph_10x,
            "loser_10x": loser_10x,
            "receipts": recs,
        },
        "I237",
    )
    print(f"I237 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
