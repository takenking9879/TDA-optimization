#!/usr/bin/env python3
"""I288: extend seeded_is_noop to equal non-singleton annotations.

Vendor skip is {a} XOR {a} singletons only. {A} XOR {A} is empty for
any equal F₂ set — skip XOR + resolve_bar. Hard H1: figure8 n=4000
(I263 reduce 866 ms). H0/H2 hold.
"""

from __future__ import annotations

import sys
from pathlib import Path

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


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("redzed", "unit_square", 4, 2.0, None, 1),
        ("redzed", "figure8", 200, 1.0, figure8, 1),
        ("redzed", "two_circles", 200, 1.2, two_circles, 1),
        ("auto", "circle_noisy", 500, 1.5, circle_noisy, 1),
        ("redzed", "sphere", 80, 1.4, sphere, 2),
        ("auto", "blobs", 4000, 1.0, blobs, 0),
        ("auto", "figure8", 2000, 1.1, figure8, 1),
        ("auto", "figure8", 4000, 1.1, figure8, 1),
        ("auto", "uniform2", 5000, 0.35, lambda n, r: uniform(n, 2, r), 1),
        ("auto", "sphere", 400, 1.4, sphere, 2),
    ]

    for engine, name, n, T, fn, dim in jobs:
        path = unit_square_path() if name == "unit_square" else ensure_cloud(name, n, fn, rng)
        rto = 90 if n >= 4000 or dim >= 2 else 60
        pr, tr = ripser_d(path, T, dim, rto)
        pa, cs, ta = pith_redzed_d(path, T, dim, rto) if engine == "redzed" else pith_auto(path, T, dim, rto)
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
            "reduce_ms": cs.get("reduce_ms"),
            "n_dist": cs.get("distances"),
            "pith_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        print(f"I288 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(
        r.get("ess0") == r.get("ess0_ripser")
        and r.get("ess1") == r.get("ess1_ripser")
        and r.get("ess2") == r.get("ess2_ripser")
        for r in recs
    )
    fig4 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 4000), None)
    fig2 = next((r for r in recs if r["name"] == "figure8" and r["n"] == 2000), None)
    uni = next((r for r in recs if r["name"] == "uniform2"), None)
    h0 = next((r for r in recs if r["name"] == "blobs" and r.get("maxdim") == 0), None)
    h2 = next((r for r in recs if r["name"] == "sphere" and r["n"] == 400), None)
    fig4_cut = bool(fig4 and fig4.get("reduce_ms") is not None and fig4["reduce_ms"] < 780)
    hold_clock = bool(
        fig2 and fig2.get("match_ripser") and fig2.get("ess1") == 2
        and fig4 and fig4.get("match_ripser") and fig4.get("ess1") == 2
        and uni and uni.get("match_ripser") and (uni.get("vs_ripser") or 0) >= 10
        and h0 and h0.get("match_ripser")
        and h2 and h2.get("match_ripser") and h2.get("ess2") == 1
    )
    invented = any((r.get("unmatched") or 0) > 0 for r in recs)

    if invented or not ident:
        status = "reject"
        summary = "I288 seeded-eq invented bars or broke identity; revert"
    elif ident and ess_ok and hold_clock and fig4_cut:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; figure8 n=4000 {fig4.get('vs_ripser'):.1f}× / "
            f"reduce {fig4.get('reduce_ms'):.0f}ms (was 866)"
        )
    elif ident and ess_ok and hold_clock:
        status = "hold"
        summary = (
            f"exact {len(recs)}/{len(recs)}; fig4 reduce {fig4.get('reduce_ms')}ms "
            f"(no <780 cut vs 866)"
        )
    else:
        status = "reject"
        summary = "I288 identity or H0–H2 hold failed"

    write(
        {
            "id": "seeded_noop_equal_sets",
            "lever": "H09-seeded-noop-equal-sets",
            "class": "algorithm",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "fig4_reduce_ms": fig4.get("reduce_ms") if fig4 else None,
            "hold_clock": hold_clock,
            "receipts": recs,
        },
        "I288",
    )
    print(f"I288 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
