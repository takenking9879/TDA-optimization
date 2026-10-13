#!/usr/bin/env python3
"""I289: grade-t rbit apparent pairs in implicit cohomology.

Same Ripser apparent test, G_t neighbors not G_T. Hard: figure8
n=4000 collapse=0 (was 25s) and auto hold. Exact vs Ripser.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, uniform  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import ensure_cloud, figure8, two_circles, unit_square_path, write  # noqa: E402
from run_wave95 import ess, pith_default_d, pith_redzed_d, ripser_d  # noqa: E402
from run_wave97 import pith_auto  # noqa: E402


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
        ("implicit0", "unit_square", 4, 2.0, None, 1, 0, True),
        ("implicit0", "figure8", 200, 1.0, figure8, 1, 0, True),
        ("implicit0", "two_circles", 200, 1.2, two_circles, 1, 0, True),
        ("implicit0", "figure8", 2000, 1.1, figure8, 1, 0, True),
        ("implicit0", "figure8", 4000, 1.1, figure8, 1, 0, True),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1, -1, True),
        ("auto", "blobs", 4000, 1.0, blobs, 0, -1, True),
        ("auto", "figure8", 2000, 1.1, figure8, 1, -1, True),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1, -1, True),
        ("auto", "sphere", 400, 1.4, sphere, 2, -1, True),
    ]
    for engine, name, n, T, fn, dim, col, vs in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 else 60
        if engine == "implicit0":
            pa, cs, ta = pith_implicit(path, T, dim, col, rto)
        else:
            pa, cs, ta = pith_auto(path, T, dim, rto)
        pr, tr = (None, None)
        fid = {}
        if vs:
            try:
                pr, tr = ripser_d(path, T, dim, rto)
                fid = compare(pr, pa, dim)
            except Exception as e:
                fid = {"error": str(e)}
        rec = {
            "engine": engine,
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "collapse": col,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0),
            "ess0_ref": ess(pr, 0) if pr is not None else None,
            "ess1": ess(pa, 1),
            "ess1_ref": ess(pr, 1) if pr is not None else None,
            "ess2": ess(pa, 2),
            "ess2_ref": ess(pr, 2) if pr is not None else None,
            "pipeline": cs.get("pipeline"),
            "reduce_ms": cs.get("reduce_ms"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ref_s": tr,
            "vs_ref": (tr / ta) if (tr and ta) else None,
        }
        print(f"I289 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match") for r in recs if r.get("match") is not None)
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 4000), None)
    fig2 = next((r for r in recs if r["engine"] == "implicit0" and r["n"] == 2000), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h0 = next((r for r in recs if r["name"] == "blobs"), None)
    h2 = next((r for r in recs if r["name"] == "sphere" and r.get("maxdim") == 2), None)
    circ = next((r for r in recs if r["name"] == "circle_noisy"), None)
    fig4_cut = bool(fig4 and fig4.get("pith_s") and fig4["pith_s"] < 2.0)
    hold = bool(
        ident
        and fig2 and fig2.get("ess1") == 2
        and fig4 and fig4.get("ess1") == 2
        and uni and uni.get("match") and (uni.get("vs_ref") or 0) >= 10
        and h0 and h0.get("match")
        and h2 and h2.get("match") and h2.get("ess2") == 1
        and circ and circ.get("match")
    )
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I289 rbit-apparent invented bars; revert"
    elif hold and fig4_cut:
        status = "support"
        vs = f"{fig4.get('vs_ref'):.1f}× / " if fig4.get("vs_ref") else ""
        summary = (
            f"exact; figure8 n=4000 collapse0 {vs}{fig4.get('pith_s'):.3f}s "
            f"reduce {fig4.get('reduce_ms')}ms"
        )
    elif hold:
        status = "hold"
        summary = (
            f"exact; figure8 n=4000 collapse0 {fig4.get('pith_s') if fig4 else None}s "
            f"(no <2s cut)"
        )
    else:
        status = "reject"
        summary = "I289 identity or H0–H2 hold failed"

    write(
        {
            "id": "implicit_rbit_apparent",
            "lever": "H02-implicit-rbit-apparent",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "fig4_cut": fig4_cut,
            "hold": hold,
            "receipts": recs,
        },
        "I289",
    )
    print(f"I289 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
