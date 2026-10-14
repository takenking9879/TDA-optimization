#!/usr/bin/env python3
"""I227: first real RedZeD engine (MIT redzed-tda) + GUDHI collapse timing.

H09 was I122–I125 fake (enumerated every leftover triangle). redzed-tda 0.1.1
is MIT (Kapulkin–Kershaw, arXiv:2606.06310): active enumeration of (n+1)
cofaces that have an active face. Shape-agnostic: one path on any distance
matrix. Exact VR claimed. Measure unmatched / ess H1 / bottleneck vs Ripser
and wall-clock vs Ripser + default PITH. GUDHI flag collapse on n=2000
answers whether the torus collapse wall is an implementation gap.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import redzed_tda as rz

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402
from run_wave85 import (  # noqa: E402
    bottleneck_h1,
    ensure_cloud,
    ess1,
    figure8,
    loglog_slope,
    pith_default,
    two_circles,
    unit_square_path,
    write,
)


def ripser(path, T, timeout=120):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def redzed(path, T):
    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    D = rz.pairwise_distances(pts)
    diags = rz.rips(D, maxdim=1, threshold=float(T))
    dt = time.perf_counter() - t0
    pairs = []
    for dim, arr in enumerate(diags):
        if arr is None or len(arr) == 0:
            continue
        for birth, death in np.asarray(arr, dtype=float):
            pairs.append({"dim": int(dim), "birth": float(birth), "death": float(death)})
    return pairs, dt, int(len(pts))


def gudhi_collapse(path, T):
    from gudhi.flag_filtration.edge_collapse import reduce_graph
    from scipy.sparse import coo_matrix
    from scipy.spatial.distance import pdist, squareform

    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    D = squareform(pdist(pts))
    n = len(pts)
    ii, jj = np.triu_indices(n, 1)
    vals = D[ii, jj]
    mask = vals <= T
    M = coo_matrix((vals[mask], (ii[mask], jj[mask])), shape=(n, n))
    t_built = time.perf_counter()
    R = reduce_graph(M, nb_iterations=1)
    t1 = time.perf_counter()
    return {
        "n": n,
        "edges_in": int(mask.sum()),
        "edges_out": int(R.nnz),
        "graph_s": t_built - t0,
        "collapse_s": t1 - t_built,
        "total_s": t1 - t0,
    }


def main():
    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None),
        ("circle_noisy", 80, 1.2, circle_noisy),
        ("circle_noisy", 200, 1.5, circle_noisy),
        ("blobs", 200, 1.0, blobs),
        ("sphere", 200, 1.4, sphere),
        ("torus", 200, 1.6, torus),
        ("uniform2", 200, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 200, 1.2, two_circles),
        ("figure8", 200, 1.0, figure8),
        ("circle_noisy", 500, 1.5, circle_noisy),
        ("blobs", 500, 1.0, blobs),
        ("torus", 500, 1.6, torus),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r)),
        ("circle_noisy", 2000, 1.5, circle_noisy),
        ("blobs", 2000, 1.0, blobs),
        ("sphere", 2000, 1.4, sphere),
        ("torus", 2000, 1.6, torus),
        ("uniform2", 2000, 0.35, lambda n, r: uniform(n, 2, r)),
    ]

    for name, n, T, fn in jobs:
        if name == "unit_square":
            path = unit_square_path()
        elif name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 180 if n >= 2000 else (90 if n >= 500 else 45)
        pto = 180 if n >= 2000 else 90
        pr, tr = ripser(path, T, rto)
        pz, tz, _ = redzed(path, T)
        fid = compare(pr, pz, 1)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_redzed": ess1(pz),
            "ess1_ripser": ess1(pr),
            "n_finite_redzed": fid.get("n_finite_b"),
            "n_finite_ripser": fid.get("n_finite_a"),
            "bottleneck": bottleneck_h1(pr, pz),
            "redzed_s": tz,
            "ripser_s": tr,
            "vs_ripser": (tr / tz) if tz else None,
        }
        try:
            _, cs, td = pith_default(path, T, pto)
            rec["default_s"] = td
            rec["default_collapse_ms"] = cs.get("collapse_ms")
            rec["vs_default"] = (td / tz) if tz else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        print(f"I227 {rec}", flush=True)
        recs.append(rec)

    collapse_cmp = []
    for name, n, T, fn in (
        ("circle_noisy", 2000, 1.5, circle_noisy),
        ("blobs", 2000, 1.0, blobs),
        ("torus", 2000, 1.6, torus),
    ):
        path = ensure_cloud(name, n, fn, rng)
        try:
            g = gudhi_collapse(path, T)
            pith_ms = next(
                (r.get("default_collapse_ms") for r in recs if r["name"] == name and r["n"] == n),
                None,
            )
            row = {
                "name": name,
                "n": n,
                "T": T,
                **g,
                "pith_collapse_ms": pith_ms,
                "gudhi_vs_pith": (
                    (pith_ms / 1000.0) / g["collapse_s"] if pith_ms and g["collapse_s"] else None
                ),
            }
            print(f"I227 gudhi_collapse {row}", flush=True)
            collapse_cmp.append(row)
        except Exception as ex:  # noqa: BLE001
            collapse_cmp.append({"name": name, "n": n, "err": str(ex)[:300]})
            print(f"I227 gudhi_collapse FAIL {name}: {ex}", flush=True)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(r.get("ess1_redzed") == r.get("ess1_ripser") for r in recs)
    mixed = [r for r in recs if r["name"] in {"figure8", "two_circles", "unit_square", "blobs", "torus"}]
    mixed_ok = all(r.get("match_ripser") for r in mixed)
    n2000 = [r for r in recs if r["n"] == 2000]
    x10 = [r for r in n2000 if (r.get("vs_ripser") or 0) >= 10]
    torus2000 = next((r for r in recs if r["name"] == "torus" and r["n"] == 2000), None)

    slopes = {}
    for fam in ("circle_noisy", "blobs", "torus", "uniform2"):
        rows = [r for r in recs if r["name"] == fam and r.get("redzed_s") and r.get("ripser_s")]
        if len(rows) >= 2:
            slopes[fam] = {
                "redzed_time": loglog_slope([r["n"] for r in rows], [r["redzed_s"] for r in rows]),
                "ripser_time": loglog_slope([r["n"] for r in rows], [r["ripser_s"] for r in rows]),
                "pith_time": loglog_slope(
                    [r["n"] for r in rows if r.get("default_s")],
                    [r["default_s"] for r in rows if r.get("default_s")],
                ),
            }

    if ident and ess_ok and mixed_ok and len(x10) >= 2:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; n=2000 10× on {len(x10)}/{len(n2000)} families"
            + (f"; torus {torus2000['vs_ripser']:.1f}×" if torus2000 and torus2000.get("vs_ripser") else "")
        )
    elif ident and ess_ok and mixed_ok:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; n=2000 10× on {len(x10)}/{len(n2000)}"
    else:
        status = "reject"
        summary = "RedZeD H1 identity failed vs Ripser"

    write(
        {
            "id": "redzed_real_engine",
            "lever": "H09",
            "class": "structural",
            "fidelity": "exact-claimed",
            "license": "MIT",
            "package": "redzed-tda==0.1.1",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "mixed_ok": mixed_ok,
            "n2000_10x": len(x10),
            "slopes": slopes,
            "gudhi_collapse": collapse_cmp,
            "receipts": recs,
        },
        "I227",
    )
    print(f"I227 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
