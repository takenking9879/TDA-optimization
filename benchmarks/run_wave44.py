#!/usr/bin/env python3
"""I175: skip-collapse + owned implicit vs Ripser on I162 families + circle."""

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


def pith(path, T, collapse, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", str(collapse), "--collapse-alg", "back",
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


def one(name, n, T, timeout=180, rto=180):
    path = BENCH / f"datasets/generated/{name}_n{n}.csv"
    pr, tr = ripser(path, T, rto)
    recs = []
    for coll in (0, 1):
        pp, c, tp = pith(path, T, coll, timeout)
        fid = compare(pr, pp, 1)
        rec = {
            "name": name, "n": n, "T": T, "collapse": coll,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ripser_s": tr, "pith_s": tp,
            "vs_ripser": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "reduce_ms": c.get("reduce_ms"),
            "edges_in": c.get("edges_in"),
            "edges_out": c.get("edges_out"),
        }
        print(f"I175 {rec}", flush=True)
        recs.append(rec)
    return recs


def main():
    recs = []
    recs += one("circle_noisy", 2000, 1.5, 90, 90)
    recs += one("circle_noisy", 2000, 1.2, 90, 90)
    recs += one("blobs", 2000, 1.0, 60, 60)
    recs += one("sphere", 2000, 1.4, 90, 60)
    recs += one("uniform2", 2000, 0.35, 60, 60)
    recs += one("torus", 2000, 1.6, 90, 90)
    ok = all(r.get("match") for r in recs)
    write({
        "id": "skip_collapse_implicit",
        "lever": "H01-skip-collapse",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "collapse 0 vs 1 implicit vs Ripser on I162 families + circle",
        "receipts": recs,
    }, "I175")


if __name__ == "__main__":
    main()
