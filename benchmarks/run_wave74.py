#!/usr/bin/env python3
"""I213: owned --sparse-eps 0.5/0.6/0.7 with max(λ) cap."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import RESULTS, compare, essential  # noqa: E402
from run_wave69 import bottleneck_h1, ripser  # noqa: E402
from run_wave73 import pith_sparse  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def main():
    recs = []
    jobs = [
        ("circle_noisy", 1000, 1.5),
        ("blobs", 2000, 1.0),
        ("torus", 2000, 1.6),
        ("uniform2", 2000, 0.35),
        ("two_circles", 400, 1.2),
        ("figure8", 500, 1.0),
    ]
    for name, n, T in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, 90)
        row = {"name": name, "n": n, "T": T, "ripser_s": tr, "ess_vr": len(essential(pr, 1))}
        for eps in (0.5, 0.6, 0.7):
            ps, cs, ts = pith_sparse(path, T, eps, "max")
            key = str(eps).replace(".", "")
            row[f"e{key}_s"] = ts
            row[f"e{key}_edges"] = cs.get("edges_in")
            row[f"e{key}_vs"] = tr / ts if ts else None
            row[f"e{key}_ess"] = len(essential(ps, 1))
            row[f"e{key}_ok"] = row[f"e{key}_ess"] == row["ess_vr"]
            row[f"e{key}_unmatched"] = compare(pr, ps, 1).get("unmatched")
            row[f"e{key}_bn"] = bottleneck_h1(pr, ps)
        print(f"I213 {row}", flush=True)
        recs.append(row)

    def all_ok(eps_key):
        return all(r.get(f"{eps_key}_ok") for r in recs) if recs else False

    torus = next((r for r in recs if r["name"] == "torus"), None)
    e06_ok = all_ok("e06")
    e07_ok = all_ok("e07")
    e06_win = e06_ok and torus and (torus.get("e06_vs") or 0) > (torus.get("e05_vs") or 0) * 1.15
    write({
        "id": "owned_sparse_eps_max_sweep",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if e06_win or e07_ok else ("partial" if e06_ok else "reject"),
        "summary": "I213 owned max(λ) ε∈{0.5,0.6,0.7}",
        "receipts": recs,
        "e06_ess_ok": e06_ok,
        "e07_ess_ok": e07_ok,
    }, "I213")


if __name__ == "__main__":
    main()
