#!/usr/bin/env python3
"""I212: owned --sparse-cap min vs max vs GUDHI Sheehy (essential H1 + clock)."""

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


def pith_sparse(path, T, eps, cap, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--sparse-eps", str(eps), "--sparse-cap", cap, "--collapse", "0",
         "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2),
        ("circle_noisy", 1000, 1.5),
        ("blobs", 2000, 1.0),
        ("torus", 2000, 1.6),
        ("uniform2", 2000, 0.35),
        ("two_circles", 400, 1.2),
        ("figure8", 500, 1.0),
    ]
    for name, n, T in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        pr, tr = ripser(path, T, 90)
        row = {"name": name, "n": n, "T": T, "ripser_s": tr, "ess_vr": len(essential(pr, 1))}
        for cap in ("max", "min"):
            ps, cs, ts = pith_sparse(path, T, 0.5, cap)
            row[f"{cap}_s"] = ts
            row[f"{cap}_edges"] = cs.get("edges_in")
            row[f"{cap}_vs"] = tr / ts if ts else None
            row[f"{cap}_ess"] = len(essential(ps, 1))
            row[f"{cap}_ess_ok"] = row[f"{cap}_ess"] == row["ess_vr"]
            row[f"{cap}_unmatched"] = compare(pr, ps, 1).get("unmatched")
            row[f"{cap}_bn"] = bottleneck_h1(pr, ps)
        print(f"I212 {row}", flush=True)
        recs.append(row)

    min_ess = all(r.get("min_ess_ok") for r in recs) if recs else False
    max_ess = all(r.get("max_ess_ok") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    min_faster = torus and torus.get("min_s") and torus.get("max_s") and torus["min_s"] < 0.9 * torus["max_s"]
    min_ten = torus and (torus.get("min_vs") or 0) >= 10
    write({
        "id": "sparse_cap_min_vs_max",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if min_ess and min_ten and min_faster else (
            "partial" if min_ess else "reject"
        ),
        "summary": "I212 --sparse-cap min vs max (ε=0.5)",
        "receipts": recs,
        "max_ess_ok": max_ess,
        "min_ess_ok": min_ess,
        "note": "Select min as owned default only if ess H1 holds everywhere and torus is faster than max.",
    }, "I212")


if __name__ == "__main__":
    main()
