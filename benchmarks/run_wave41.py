#!/usr/bin/env python3
"""I170: keep-rank histogram on full backward (is the residual an oldest suffix?)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, parse_pith_text, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def one(name, n, T, timeout=180):
    path = BENCH / f"datasets/generated/{name}_n{n}.csv"
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--collapse-alg", "back", "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    _, c = parse_pith_text(out)
    rec = {
        "name": name, "n": n, "T": T, "pith_s": dt,
        "edges_in": c.get("edges_in"),
        "edges_out": c.get("edges_out"),
        "first_keep": c.get("collapse_first_keep"),
        "keep_hist": c.get("collapse_keep_hist"),
        "early_keeps": c.get("collapse_early_keeps"),
        "collapse_ms": c.get("collapse_ms"),
    }
    print(f"I170 {rec}", flush=True)
    return rec


def main():
    recs = [
        one("circle_noisy", 2000, 1.5, 60),
        one("circle_noisy", 3000, 1.5, 90),
        one("circle_noisy", 4000, 1.5, 120),
        one("blobs", 2000, 1.0, 60),
    ]
    write({
        "id": "keep_histogram",
        "lever": "H01-keep-hist",
        "class": "experiment",
        "fidelity": "exact",
        "status": "support",
        "summary": "16-bin newest-first keep histogram + first 8 keep indices",
        "receipts": recs,
    }, "I170")


if __name__ == "__main__":
    main()
