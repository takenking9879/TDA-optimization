#!/usr/bin/env python3
"""I200: remasure remaining I162 families on I193+I197 default."""

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


def pith_cmd(path, T, extra, timeout=240):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra,
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


def main():
    recs = []
    jobs = [
        ("uniform2", 2000, 0.35, 90, 90),
        ("circle_noisy", 2000, 1.2, 90, 90),
        ("torus", 1000, 1.6, 60, 60),
        ("blobs", 1000, 1.0, 60, 60),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
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
            "reduce_ms": cs.get("reduce_ms"),
            "trims": cs.get("collapse_trims"),
            "shifts": cs.get("collapse_shifts"),
        }
        print(f"I200 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs) if recs else False
    write({
        "id": "i197_other_families",
        "lever": "H01-multi-apex-and-eq",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "partial" if ident else "reject",
        "summary": "I200 I193+I197 remasure uniform2 / off-peak circle / smaller torus,blobs",
        "receipts": recs,
    }, "I200")


if __name__ == "__main__":
    main()
