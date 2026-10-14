#!/usr/bin/env python3
"""I231: owned --engine active (H1 leftover youngest-face enum) vs Ripser.

Not the vendored RedZeD. Same path on every flag graph. Quantify unmatched /
ess H1 / bottleneck and clock vs Ripser, default PITH, and --engine redzed.
"""

from __future__ import annotations

import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
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


def pith_active(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--engine", "active", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


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
        ("torus", 500, 1.6, torus),
        ("circle_noisy", 2000, 1.5, circle_noisy),
        ("blobs", 2000, 1.0, blobs),
        ("torus", 2000, 1.6, torus),
    ]

    for name, n, T, fn in jobs:
        if name == "unit_square":
            path = unit_square_path()
        elif name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 180 if n >= 2000 else 60
        pto = 180 if n >= 2000 else 90
        pr, tr = ripser(path, T, rto)
        pa, cs, ta = pith_active(path, T, pto)
        fid = compare(pr, pa, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_active": ess1(pa),
            "ess1_ripser": ess1(pr),
            "bottleneck": bottleneck_h1(pr, pa),
            "simplices": cs.get("simplices"),
            "reduce_ms": cs.get("reduce_ms"),
            "active_s": ta,
            "ripser_s": tr,
            "vs_ripser": (tr / ta) if ta else None,
        }
        try:
            _, _, td = pith_default(path, T, pto)
            rec["default_s"] = td
            rec["vs_default"] = (td / ta) if ta else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        if n <= 500 or name in {"torus", "blobs"}:
            try:
                _, _, tz = pith_redzed(path, T, pto)
                rec["redzed_s"] = tz
                rec["vs_redzed"] = (tz / ta) if ta else None
            except Exception as ex:  # noqa: BLE001
                rec["redzed_err"] = str(ex)[:200]
        print(f"I231 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(r.get("ess1_active") == r.get("ess1_ripser") for r in recs)
    mixed = [r for r in recs if r["name"] in {"figure8", "two_circles", "unit_square"}]
    mixed_ok = all(r.get("match_ripser") for r in mixed)
    n2000 = [r for r in recs if r["n"] == 2000]
    x10 = [r for r in n2000 if (r.get("vs_ripser") or 0) >= 10]
    beats_redzed = any((r.get("vs_redzed") or 0) >= 1.1 and r["n"] >= 500 for r in recs)

    if ident and ess_ok and mixed_ok and (x10 or beats_redzed):
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; n=2000 10× on {len(x10)}/{len(n2000)}"
            + ("; beats RedZeD on a scale row" if beats_redzed else "")
        )
    elif ident and ess_ok and mixed_ok:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; no 10× / no RedZeD clock win"
    else:
        status = "reject"
        summary = "owned active H1 identity failed vs Ripser"

    write(
        {
            "id": "owned_active_h1",
            "lever": "H09-owned",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "mixed_ok": mixed_ok,
            "n2000_10x": len(x10),
            "beats_redzed": beats_redzed,
            "receipts": recs,
        },
        "I231",
    )
    print(f"I231 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
