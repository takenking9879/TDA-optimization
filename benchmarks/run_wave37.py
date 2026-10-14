#!/usr/bin/env python3
"""I165/I166: oldest-prefix residual (no C-walk) and prefix-then-collapse."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith(path, T, alg, mult, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--collapse-alg", alg, "--suffix-mult", str(mult),
         "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def one(name, n, T, alg, mult, timeout=180):
    path = BENCH / f"datasets/generated/{name}_n{n}.csv"
    pr, tr = ripser(path, T, timeout=timeout)
    pp, c, tp = pith(path, T, alg, mult, timeout)
    fid = compare(pr, pp, 1)
    rec = {
        "name": name, "n": n, "T": T, "alg": alg, "mult": mult,
        "match": fid.get("exact_match_tol"),
        "unmatched": fid.get("unmatched"),
        "ripser_s": tr, "pith_s": tp,
        "time_ratio": tr / tp if tp else None,
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "edges_in": c.get("edges_in"),
        "edges_out": c.get("edges_out"),
    }
    print(f"I165/6 {rec}", flush=True)
    return rec


def main():
    recs = []
    for mult in (4, 6, 8):
        recs.append(one("circle_noisy", 80, 1.2, "suffix", mult, 60))
        recs.append(one("circle_noisy", 200, 1.5, "suffix", mult, 60))
    recs.append(one("circle_noisy", 2000, 1.5, "suffix", 6, 180))
    recs.append(one("circle_noisy", 2000, 1.5, "suffix-back", 6, 180))
    recs.append(one("blobs", 2000, 1.0, "suffix", 6, 180))
    ok = any(r.get("match") for r in recs)
    write({
        "id": "oldest_prefix",
        "lever": "H01-suffix",
        "class": "experiment",
        "fidelity": "exact" if all(r.get("match") for r in recs) else "unverified",
        "status": "support" if all(r.get("match") for r in recs) else "reject",
        "summary": "oldest-k n prefix / prefix-then-collapse vs Ripser",
        "any_match": ok,
        "receipts": recs,
    }, "I165")


if __name__ == "__main__":
    main()
