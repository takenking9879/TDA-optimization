#!/usr/bin/env python3
"""I233: active leftover-star generation vs I232 / Ripser / RedZeD.

Apparent 1-leftover triangles via MST-star intersection. Multi-leftover
triangles from leftovers with nonempty R only. Shape-agnostic.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, RESULTS, compare, parse_pith_text, run_cmd  # noqa: E402
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

I232 = RESULTS / "iterations" / "I232_active_annotation_skip.json"


def prev_time(path, name, n, key="active_s"):
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    for r in data.get("receipts", []):
        if r.get("name") == name and r.get("n") == n:
            return r.get(key)
    return None


def main():
    import numpy as np

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
        ("sphere", 500, 1.4, sphere),
        ("torus", 500, 1.6, torus),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 500, 1.2, two_circles),
        ("figure8", 500, 1.0, figure8),
    ]

    for name, n, T, fn in jobs:
        if name == "unit_square":
            path = unit_square_path()
        elif name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        pr, tr = ripser(path, T, 60)
        pa, cs, ta = pith_active(path, T, 90)
        fid = compare(pr, pa, 1)
        simp = cs.get("simplices") or 0
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_active": ess1(pa),
            "ess1_ripser": ess1(pr),
            "bottleneck": bottleneck_h1(pr, pa),
            "simplices": simp,
            "cols_apparent": cs.get("cols_apparent"),
            "cols_reduced": cs.get("cols_reduced"),
            "cofacet_probes": cs.get("cofacet_probes") or cs.get("n_cofacet_probes"),
            "reduce_ms": cs.get("reduce_ms"),
            "active_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        old = prev_time(I232, name, n)
        if old:
            rec["i232_s"] = old
            rec["vs_i232"] = (old / ta) if ta else None
        try:
            _, _, td = pith_default(path, T, 90)
            rec["default_s"] = td
            rec["vs_default"] = (td / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        if n <= 500:
            try:
                _, _, tz = pith_redzed(path, T, 90)
                rec["redzed_s"] = tz
                rec["vs_redzed"] = (tz / ta) if ta else None
            except Exception as ex:  # noqa: BLE001
                rec["redzed_err"] = str(ex)[:200]
        print(f"I233 {rec}", flush=True)
        recs.append(rec)

    circle500 = next((r for r in recs if r["name"] == "circle_noisy" and r["n"] == 500), None)
    scale = bool(
        circle500
        and ((circle500.get("vs_i232") or 0) >= 2 or (circle500.get("vs_ripser") or 0) >= 1)
    )
    if scale:
        for name, n, T, fn in [
            ("circle_noisy", 1000, 1.5, circle_noisy),
            ("blobs", 1000, 1.0, blobs),
            ("torus", 1000, 1.6, torus),
        ]:
            path = ensure_cloud(name, n, fn, rng)
            try:
                pr, tr = ripser(path, T, 90)
                pa, cs, ta = pith_active(path, T, 90)
            except Exception as ex:  # noqa: BLE001
                recs.append({"name": name, "n": n, "T": T, "err": str(ex)[:200]})
                print(f"I233 {name} n={n} err={ex}", flush=True)
                continue
            fid = compare(pr, pa, 1)
            rec = {
                "name": name, "n": n, "T": T,
                "match_ripser": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ess1_active": ess1(pa),
                "ess1_ripser": ess1(pr),
                "bottleneck": bottleneck_h1(pr, pa),
                "simplices": cs.get("simplices"),
                "cols_apparent": cs.get("cols_apparent"),
                "cols_reduced": cs.get("cols_reduced"),
                "reduce_ms": cs.get("reduce_ms"),
                "active_s": ta,
                "ripser_s": tr,
                "vs_ripser": (tr / ta) if ta else None,
            }
            old = prev_time(I232, name, n)
            if old:
                rec["i232_s"] = old
                rec["vs_i232"] = (old / ta) if ta else None
            print(f"I233 {rec}", flush=True)
            recs.append(rec)

    done = [r for r in recs if "err" not in r]
    ident = bool(done) and all(r.get("match_ripser") for r in done)
    ess_ok = bool(done) and all(r.get("ess1_active") == r.get("ess1_ripser") for r in done)
    mixed = [r for r in done if r["name"] in {"figure8", "two_circles", "unit_square"}]
    mixed_ok = bool(mixed) and all(r.get("match_ripser") for r in mixed)
    faster = [r for r in done if (r.get("vs_i232") or 0) >= 2]
    beats_ripser = any((r.get("vs_ripser") or 0) >= 1.0 and r["n"] >= 200 for r in done)
    beats_redzed = any((r.get("vs_redzed") or 0) >= 1.1 and r["n"] >= 200 for r in done)

    if ident and ess_ok and mixed_ok and (beats_ripser or beats_redzed):
        status = "support"
        summary = f"exact {len(done)}/{len(done)}; ≥2× I232 on {len(faster)}; Ripser/RedZeD clock win"
    elif ident and ess_ok and mixed_ok:
        status = "hold"
        summary = f"exact {len(done)}/{len(done)}; ≥2× I232 on {len(faster)}; no Ripser/RedZeD clock win"
    else:
        status = "reject"
        summary = "I233 active-star identity failed vs Ripser"

    write(
        {
            "id": "active_star_generation",
            "lever": "H09-owned",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "mixed_ok": mixed_ok,
            "beats_ripser": beats_ripser,
            "beats_redzed": beats_redzed,
            "scaled_n1000": scale,
            "receipts": recs,
        },
        "I233",
    )
    print(f"I233 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
