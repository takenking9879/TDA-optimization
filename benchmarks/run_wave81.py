#!/usr/bin/env python3
"""I220: undirected kNN flag 1-skeleton vs Ripser; quantify H1 loss."""

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


def pith_knn(path, T, k, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--knn", str(k), "--collapse", "0", "--engine", "implicit", "--no-enclosing"],
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
        ("sphere", 2000, 1.4),
        ("torus", 2000, 1.6),
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
        for k in (16, 32):
            ps, cs, ts = pith_knn(path, T, k, 120)
            key = f"k{k}"
            row[f"{key}_s"] = ts
            row[f"{key}_edges"] = cs.get("edges_in")
            row[f"{key}_vs"] = tr / ts if ts else None
            row[f"{key}_ess"] = len(essential(ps, 1))
            row[f"{key}_ok"] = row[f"{key}_ess"] == row["ess_vr"]
            row[f"{key}_unmatched"] = compare(pr, ps, 1).get("unmatched")
            row[f"{key}_bn"] = bottleneck_h1(pr, ps)
        print(f"I220 {row}", flush=True)
        recs.append(row)

    def all_ok(key):
        return all(r.get(f"{key}_ok") for r in recs) if recs else False

    torus = next((r for r in recs if r["name"] == "torus"), None)
    k32_ok = all_ok("k32")
    k16_ok = all_ok("k16")
    torus_ten = torus and (torus.get("k32_vs") or 0) >= 10
    write({
        "id": "knn_flag_skeleton",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if k32_ok and torus_ten else ("partial" if k32_ok or k16_ok else "reject"),
        "summary": "I220 undirected kNN flag 1-skeleton K=16/32 vs Ripser",
        "receipts": recs,
        "k16_ess_ok": k16_ok,
        "k32_ess_ok": k32_ok,
        "note": "Not exact VR. |E|≤nK. Select optional only if ess H1 holds on mixed families.",
    }, "I220")


if __name__ == "__main__":
    main()
