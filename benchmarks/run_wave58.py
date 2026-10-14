#!/usr/bin/env python3
"""I196: I193-only remasure at circle n=3000/4000 (I194 off)."""

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


def pith_cmd(path, T, extra, timeout=300):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra,
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, timeout=360):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 3000, 1.5, 180, 180),
        ("circle_noisy", 4000, 1.5, 300, 360),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "bits_s": ts, "ripser_s": tr,
            "vs_ripser": tr / ts if ts else None,
            "out": cs.get("edges_out"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "fast_trims": cs.get("collapse_fast_trims"),
            "trims": cs.get("collapse_trims"),
            "vertex_trims": cs.get("collapse_vertex_trims"),
        }
        print(f"I196 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    n3000 = next((r for r in recs if r["n"] == 3000), None)
    n4000 = next((r for r in recs if r["n"] == 4000), None)
    ok = ident and n3000 and (n3000.get("vs_ripser") or 0) >= 70
    write({
        "id": "i193_n3000_n4000",
        "lever": "H01-multi-apex-and-eq",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if ok else "partial",
        "summary": "I196 I193-only remasure circle n=3000/4000 vs Ripser",
        "receipts": recs,
        "n3000_x": n3000.get("vs_ripser") if n3000 else None,
        "n4000_x": n4000.get("vs_ripser") if n4000 else None,
    }, "I196")


if __name__ == "__main__":
    main()
