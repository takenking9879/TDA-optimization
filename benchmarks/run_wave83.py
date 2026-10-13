#!/usr/bin/env python3
"""I222: graph-induced complex (landmarks + kNN quotient) vs Ripser."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave69 import bottleneck_h1, ripser  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def ess1(pairs):
    return sum(1 for p in pairs if p["dim"] == 1 and not math.isfinite(p["death"]))


def pith_gic(path, T, m, k, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--gic-n", str(m), "--gic-k", str(k),
         "--collapse", "0", "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 40, 8),
        ("circle_noisy", 1000, 1.5, 100, 16),
        ("blobs", 2000, 1.0, 200, 16),
        ("sphere", 2000, 1.4, 200, 16),
        ("torus", 2000, 1.6, 200, 16),
        ("two_circles", 400, 1.2, 80, 16),
        ("figure8", 500, 1.0, 100, 16),
    ]
    for name, n, T, m, k in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        pr, tr = ripser(path, T, 90)
        pg, cg, tg = pith_gic(path, T, m, k, 120)
        rec = {
            "name": name, "n": n, "T": T, "m": m, "k": k,
            "ripser_s": tr, "gic_s": tg,
            "vs_ripser": tr / tg if tg else None,
            "edges": cg.get("edges_in"),
            "vertices": cg.get("n"),
            "ess_vr": ess1(pr), "ess_gic": ess1(pg),
            "ess_ok": ess1(pg) == ess1(pr),
            "unmatched": compare(pr, pg, 1).get("unmatched"),
            "bn": bottleneck_h1(pr, pg),
        }
        print(f"I222 {rec}", flush=True)
        recs.append(rec)

    ess_ok = all(r.get("ess_ok") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    torus_ten = torus and (torus.get("vs_ripser") or 0) >= 10
    bn_ok = all((r.get("bn") or 9) <= 0.05 for r in recs) if recs else False
    write({
        "id": "gic_knn_quotient",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok and (torus_ten or bn_ok) else (
            "partial" if ess_ok else "reject"
        ),
        "summary": "I222 graph-induced complex (farthest-point L + kNN quotient) vs Ripser",
        "receipts": recs,
        "note": "Not exact VR. PH on m landmarks. Select optional only if ess H1 holds and not dominated by sparse-eps 0.6.",
    }, "I222")


if __name__ == "__main__":
    main()
