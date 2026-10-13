#!/usr/bin/env python3
"""I215: sticky-only obstruction mark vs src / Ripser (exact default)."""

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
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("blobs", 2000, 1.0, 90, 60),
        ("sphere", 2000, 1.4, 90, 60),
        ("torus", 2000, 1.6, 90, 90),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back-src"], timeout)
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        fid = compare(pb, ps, 1)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_src": fid.get("exact_match_tol"),
            "unmatched_src": fid.get("unmatched"),
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "bits_s": ts, "ripser_s": tr,
            "vs_ripser": tr / ts if ts else None,
            "out": cs.get("edges_out"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "shifts": cs.get("collapse_shifts"),
            "dom_tests": cs.get("collapse_dom_tests"),
            "dom_skips": cs.get("collapse_dom_skips"),
            "dom_hits": cs.get("collapse_dom_hits"),
        }
        print(f"I215 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    n2000 = next((r for r in recs if r["name"] == "circle_noisy" and r["n"] == 2000), None)
    blobs = next((r for r in recs if r["name"] == "blobs"), None)
    torus = next((r for r in recs if r["name"] == "torus"), None)
    circle_ok = n2000 and n2000.get("match_ripser") and (n2000.get("bits_collapse_ms") or 9e9) < 280
    blobs_ok = blobs and (blobs.get("bits_collapse_ms") or 9e9) < 200
    torus_gain = torus and (torus.get("bits_collapse_ms") or 9e9) < 1400
    write({
        "id": "sticky_only_obstruction",
        "lever": "H01-sticky-cannot-until",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if ident and circle_ok and blobs_ok and torus_gain else (
            "partial" if ident and circle_ok and blobs_ok else "reject"
        ),
        "summary": "I215 mark only the sticky-failed dominator; skip it until t reaches Tm(d,w)",
        "receipts": recs,
        "note": "I214 marked every fail (torus 1714 ms). Select only if exact and torus collapse <1400 ms.",
    }, "I215")


if __name__ == "__main__":
    main()
