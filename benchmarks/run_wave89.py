#!/usr/bin/env python3
"""I228: in-tree --engine redzed (vendored MIT RedZeD) vs Ripser / I227 wheel.

Identity must hold on mixed homology. Clock should match the I227 PyPI
oracle and beat default PITH on torus n=2000.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402
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

I227 = RESULTS / "iterations" / "I227_redzed_real_engine.json"


def ripser(path, T, timeout=120):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def pith_redzed(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--engine", "redzed", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def i227_row(name, n):
    if not I227.exists():
        return None
    data = json.loads(I227.read_text())
    for r in data.get("receipts", []):
        if r.get("name") == name and r.get("n") == n:
            return r
    return None


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None),
        ("circle_noisy", 200, 1.5, circle_noisy),
        ("blobs", 200, 1.0, blobs),
        ("sphere", 200, 1.4, sphere),
        ("torus", 200, 1.6, torus),
        ("uniform2", 200, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 200, 1.2, two_circles),
        ("figure8", 200, 1.0, figure8),
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
        rto = 180 if n >= 2000 else 45
        pto = 180 if n >= 2000 else 90
        pr, tr = ripser(path, T, rto)
        pz, cs, tz = pith_redzed(path, T, pto)
        fid = compare(pr, pz, 1)
        prev = i227_row(name, n)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_redzed": ess1(pz),
            "ess1_ripser": ess1(pr),
            "bottleneck": bottleneck_h1(pr, pz),
            "pipeline": cs.get("pipeline"),
            "redzed_s": tz,
            "ripser_s": tr,
            "vs_ripser": (tr / tz) if tz else None,
            "i227_s": prev.get("redzed_s") if prev else None,
        }
        try:
            _, _, td = pith_default(path, T, pto)
            rec["default_s"] = td
            rec["vs_default"] = (td / tz) if tz else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        print(f"I228 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(r.get("ess1_redzed") == r.get("ess1_ripser") for r in recs)
    torus = next((r for r in recs if r["name"] == "torus" and r["n"] == 2000), None)
    torus_10 = bool(torus and (torus.get("vs_ripser") or 0) >= 10)

    if ident and ess_ok and torus_10:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; torus n=2000 {torus['vs_ripser']:.1f}×"
    elif ident and ess_ok:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; torus vs Ripser {None if not torus else torus.get('vs_ripser')}"
    else:
        status = "reject"
        summary = "in-tree RedZeD identity failed vs Ripser"

    write(
        {
            "id": "redzed_owned_engine",
            "lever": "H09",
            "class": "structural",
            "fidelity": "exact-claimed",
            "license": "MIT",
            "upstream": "22ef1bf8696bccad02b041a83863d12d4bd92766",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "torus_10x": torus_10,
            "receipts": recs,
        },
        "I228",
    )
    print(f"I228 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
