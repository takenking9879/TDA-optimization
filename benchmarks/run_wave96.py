#!/usr/bin/env python3
"""I235: --engine auto residual-frac dispatch vs Ripser / redzed / collapse.

Fat subsample E'/E → RedZeD (skip full collapse). Thin → collapse+implicit.
Shape-agnostic. Exact. Payoff is torus 10× without giving up circle collapse.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave85 import (  # noqa: E402
    bottleneck_h1,
    ensure_cloud,
    figure8,
    two_circles,
    unit_square_path,
    write,
)
from run_wave89 import pith_redzed, ripser  # noqa: E402
from run_wave95 import ess, ripser_d  # noqa: E402


def pith_collapse(path, T, dim=1, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_auto(path, T, dim=1, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "auto", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("blobs", 500, 1.0, blobs, 1),
        ("sphere", 500, 1.4, sphere, 1),
        ("torus", 500, 1.6, torus, 1),
        ("blobs", 1000, 1.0, blobs, 1),
        ("torus", 2000, 1.6, torus, 1),  # hard: collapse wall vs RedZeD
        ("circle_noisy", 1000, 1.5, circle_noisy, 1),
        ("sphere", 80, 1.4, sphere, 2),
    ]

    for name, n, T, fn, dim in jobs:
        if name == "unit_square":
            path = unit_square_path()
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 2000 else 60
        pto = 90
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_auto(path, T, dim, pto)
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
            "auto_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        try:
            _, _, td = pith_collapse(path, T, dim, pto)
            rec["collapse_s"] = td
            rec["vs_collapse"] = (td / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["collapse_err"] = str(ex)[:160]
        if n <= 1000 or name == "torus":
            try:
                _, _, tz = pith_redzed(path, T, pto)
                rec["redzed_s"] = tz
                rec["vs_redzed"] = (tz / ta) if ta else None
            except Exception as ex:  # noqa: BLE001
                rec["redzed_err"] = str(ex)[:160]
        print(f"I235 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    torus_rows = [r for r in recs if r["name"] == "torus" and r["n"] >= 500]
    torus_redzed = all(
        r.get("pipeline") == "pith:auto-redzed" or (r.get("residual_frac") or 0) > 0.04
        for r in torus_rows
        if r["n"] >= 400
    )
    torus_10x = any((r.get("vs_ripser") or 0) >= 10 and r["n"] >= 2000 for r in torus_rows)
    circle_rows = [r for r in recs if r["name"] == "circle_noisy" and r["n"] >= 400]
    circle_collapse = all(r.get("pipeline") == "pith:auto-collapse" for r in circle_rows)
    x10 = [r for r in recs if (r.get("vs_ripser") or 0) >= 10]

    if ident and ess_ok and torus_10x and torus_redzed and circle_collapse:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; torus RedZeD 10×; circle stayed collapse"
    elif ident and ess_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; torus_redzed={torus_redzed} "
            f"torus_10x={torus_10x} circle_collapse={circle_collapse} 10×={len(x10)}"
        )
    else:
        status = "reject"
        summary = "I235 auto-dispatch identity failed vs Ripser"

    write(
        {
            "id": "auto_residual_dispatch",
            "lever": "H09-dispatch",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "torus_redzed": torus_redzed,
            "torus_10x": torus_10x,
            "circle_collapse": circle_collapse,
            "n10x": len(x10),
            "receipts": recs,
        },
        "I235",
    )
    print(f"I235 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
