#!/usr/bin/env python3
"""I236: H2-aware auto dispatch + H0–H2 at more points.

I235 τ=0.04 sent sphere (frac~0.057) to RedZeD. That is right for H1
and wrong for H2 — collapse tets on the thin residual beat RedZeD
(I234 sphere n=200: 26× vs 3.2×). τ=0.15 when maxdim≥2; torus ~0.28
stays RedZeD. Owned AE leftover-coface is reverted (invents finite H1).

Hard case: sphere n=400 H2 (more points than I234 n=200, still seconds).
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
from run_wave95 import ess, pith_default_d, pith_redzed_d, ripser_d  # noqa: E402


def pith_auto(path, T, dim=1, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "auto", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_collapse(path, T, dim=1, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "implicit", "--no-enclosing"],
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
        ("sphere", 80, 1.4, sphere, 2),
        ("sphere", 400, 1.4, sphere, 2),  # hard H2, more points, time-bounded
        ("torus", 400, 1.6, torus, 2),  # fat residual H2 → RedZeD
        ("blobs", 1000, 1.0, blobs, 1),
    ]

    for name, n, T, fn, dim in jobs:
        if name == "unit_square":
            path = unit_square_path()
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 60 if dim >= 2 and n >= 400 else 45
        pto = 60
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
        try:
            _, _, tz = pith_redzed_d(path, T, dim, pto)
            rec["redzed_s"] = tz
            rec["vs_redzed"] = (tz / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["redzed_err"] = str(ex)[:160]
        print(f"I236 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    sph_h2 = next((r for r in recs if r["name"] == "sphere" and r["n"] >= 400), None)
    tor_h2 = next((r for r in recs if r["name"] == "torus" and r.get("maxdim", 0) >= 2), None)
    sph_collapse = bool(
        sph_h2 and (
            sph_h2.get("pipeline") == "pith:auto-collapse"
            or (sph_h2.get("residual_frac") or 0) <= 0.15
        )
    )
    tor_redzed = bool(
        tor_h2 and (
            tor_h2.get("pipeline") == "pith:auto-redzed"
            or (tor_h2.get("residual_frac") or 0) > 0.15
        )
    )
    sph_beats_redzed = bool(sph_h2 and (sph_h2.get("vs_redzed") or 0) >= 1.2)
    h2_ok = all(r.get("match_ripser") for r in recs if r.get("maxdim", 0) >= 2)
    x10 = [r for r in recs if (r.get("vs_ripser") or 0) >= 10]

    if ident and ess_ok and h2_ok and sph_collapse and tor_redzed and sph_beats_redzed:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)} H0-H2; sphere n=400 H2 stayed collapse; "
            f"torus H2 RedZeD"
        )
    elif ident and ess_ok and h2_ok:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)} H0-H2; sph_collapse={sph_collapse} "
            f"tor_redzed={tor_redzed} sph_beats_redzed={sph_beats_redzed} 10×={len(x10)}"
        )
    else:
        status = "reject"
        summary = "I236 H2-aware auto identity failed vs Ripser"

    write(
        {
            "id": "h2_auto_dispatch",
            "lever": "H09-dispatch-h2",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "h2_ok": h2_ok,
            "sphere_h2_collapse": sph_collapse,
            "torus_h2_redzed": tor_redzed,
            "sphere_beats_redzed": sph_beats_redzed,
            "n10x": len(x10),
            "receipts": recs,
        },
        "I236",
    )
    print(f"I236 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
