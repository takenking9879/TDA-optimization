#!/usr/bin/env python3
"""I234: owned active H0+H1+H2 vs Ripser / RedZeD / default.

Shape-agnostic. H2 uses empty-XOR triangles + filtration-sorted tets.
Hard case is sphere H2 (void) at n=200 — large enough to stress H2,
small enough to finish quickly. One larger H1 row (blobs n=1000).
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
    ess1,
    figure8,
    pith_default,
    two_circles,
    unit_square_path,
    write,
)
from run_wave89 import pith_redzed, ripser  # noqa: E402
from run_wave93 import pith_active  # noqa: E402


def ess(pairs, d):
    return sum(1 for p in pairs if p["dim"] == d and not math.isfinite(p["death"]))


def pith_active_d(path, T, dim, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "active", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_redzed_d(path, T, dim, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--engine", "redzed", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_default_d(path, T, dim, timeout=90):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser_d(path, T, dim, timeout=60):
    from run_suite import RIPSER, parse_ripser
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None, 1),
        ("circle_noisy", 80, 1.2, circle_noisy, 1),
        ("figure8", 200, 1.0, figure8, 1),
        ("two_circles", 200, 1.2, two_circles, 1),
        ("blobs", 200, 1.0, blobs, 1),
        ("torus", 200, 1.6, torus, 1),
        ("sphere", 80, 1.4, sphere, 2),
        ("sphere", 200, 1.4, sphere, 2),  # hard H2, time-bounded
        ("circle_noisy", 500, 1.5, circle_noisy, 1),
        ("blobs", 1000, 1.0, blobs, 1),  # more points, H1
    ]

    for name, n, T, fn, dim in jobs:
        if name == "unit_square":
            path = unit_square_path()
        else:
            path = ensure_cloud(name, n, fn, rng)
        pr, tr = ripser_d(path, T, dim, 60)
        pa, cs, ta = pith_active_d(path, T, dim, 90)
        fid = compare(pr, pa, dim)
        rec = {
            "name": name, "n": n, "T": T, "maxdim": dim,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess0": ess(pa, 0), "ess0_ripser": ess(pr, 0),
            "ess1": ess(pa, 1), "ess1_ripser": ess(pr, 1),
            "ess2": ess(pa, 2), "ess2_ripser": ess(pr, 2),
            "bottleneck_h1": bottleneck_h1(pr, pa),
            "simplices": cs.get("simplices"),
            "cols_apparent": cs.get("cols_apparent"),
            "cols_reduced": cs.get("cols_reduced"),
            "active_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        try:
            _, _, td = pith_default_d(path, T, dim, 90)
            rec["default_s"] = td
            rec["vs_default"] = (td / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        try:
            _, _, tz = pith_redzed_d(path, T, dim, 90)
            rec["redzed_s"] = tz
            rec["vs_redzed"] = (tz / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["redzed_err"] = str(ex)[:200]
        print(f"I234 {rec}", flush=True)
        recs.append(rec)

    done = recs
    ident = all(r.get("match_ripser") for r in done)
    h012 = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in done
    )
    mixed = [r for r in done if r["name"] in {"figure8", "two_circles", "unit_square", "sphere"}]
    mixed_ok = all(r.get("match_ripser") for r in mixed)
    h2 = [r for r in done if r["maxdim"] >= 2]
    h2_ok = all(r.get("match_ripser") for r in h2)
    scale = [r for r in done if r["n"] >= 1000]
    beats_ripser = any((r.get("vs_ripser") or 0) >= 1.0 and r["n"] >= 200 for r in done)

    if ident and h012 and mixed_ok and h2_ok and beats_ripser:
        status = "support"
        summary = f"exact {len(done)}/{len(done)} H0-H2; clock win vs Ripser"
    elif ident and h012 and mixed_ok and h2_ok:
        status = "hold"
        summary = f"exact {len(done)}/{len(done)} H0-H2 including sphere void; no Ripser clock win"
    else:
        status = "reject"
        summary = "I234 H0-H2 identity failed vs Ripser"

    write(
        {
            "id": "active_h012",
            "lever": "H09-owned",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "h012_ess_ok": h012,
            "mixed_ok": mixed_ok,
            "h2_ok": h2_ok,
            "n_scale": len(scale),
            "beats_ripser": beats_ripser,
            "receipts": recs,
        },
        "I234",
    )
    print(f"I234 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
