#!/usr/bin/env python3
"""I216: owned lazy witness (--witness-n) vs Ripser; quantify H1 loss."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, essential, parse_pith_text, run_cmd  # noqa: E402
from run_wave69 import bottleneck_h1, ripser  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith_witness(path, T, m, nu=1, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--witness-n", str(m), "--witness-nu", str(nu),
         "--collapse", "0", "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 40),
        ("circle_noisy", 1000, 1.5, 100),
        ("blobs", 2000, 1.0, 200),
        ("sphere", 2000, 1.4, 200),
        ("torus", 2000, 1.6, 200),
        ("two_circles", 400, 1.2, 80),
        ("figure8", 500, 1.0, 100),
    ]
    for name, n, T, m in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        pr, tr = ripser(path, T, 90)
        pw, cw, tw = pith_witness(path, T, m, 1, 120)
        ess_vr = len(essential(pr, 1))
        ess_w = len(essential(pw, 1))
        rec = {
            "name": name, "n": n, "T": T, "m": m,
            "ripser_s": tr, "wit_s": tw,
            "vs_ripser": tr / tw if tw else None,
            "edges": cw.get("edges_in"),
            "vertices": cw.get("n"),
            "ess_vr": ess_vr, "ess_w": ess_w,
            "ess_ok": ess_w == ess_vr,
            "unmatched": compare(pr, pw, 1).get("unmatched"),
            "bn": bottleneck_h1(pr, pw),
        }
        print(f"I216 {rec}", flush=True)
        recs.append(rec)

    ess_ok = all(r.get("ess_ok") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    torus_ten = torus and (torus.get("vs_ripser") or 0) >= 10
    write({
        "id": "lazy_witness_landmarks",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok and torus_ten else ("partial" if ess_ok else "reject"),
        "summary": "I216 owned lazy witness on farthest-point landmarks vs Ripser",
        "receipts": recs,
        "note": (
            "Not exact VR. PH is on m landmarks (O(n m²) build, flag on m). "
            "Select as optional only if essential H1 holds on mixed-homology families "
            "and torus ≥10×. Justify Big-O vs Ripser n³ / collapse residual n²."
        ),
    }, "I216")


if __name__ == "__main__":
    main()
