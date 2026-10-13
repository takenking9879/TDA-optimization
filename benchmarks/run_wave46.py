#!/usr/bin/env python3
"""I178: Case A+B tail leave + K-sample vs back/Ripser."""

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
    for name, n, T, timeout, rto in (
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("circle_noisy", 3000, 1.5, 180, 180),
        ("blobs", 2000, 1.0, 90, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        for k in (2, 8):
            ps, cs, ts = pith_cmd(
                path, T, ["--collapse-alg", "suffix-later", "--suffix-k", str(k)], timeout
            )
            fid = compare(pb, ps, 1)
            fidr = compare(pr, ps, 1)
            rec = {
                "name": name, "n": n, "T": T, "K": k,
                "match_back": fid.get("exact_match_tol"),
                "unmatched_back": fid.get("unmatched"),
                "match_ripser": fidr.get("exact_match_tol"),
                "unmatched_ripser": fidr.get("unmatched"),
                "back_s": tb, "pith_s": ts, "ripser_s": tr,
                "vs_back": tb / ts if ts else None,
                "vs_ripser": tr / ts if ts else None,
                "back_out": cb.get("edges_out"),
                "out": cs.get("edges_out"),
                "collapse_ms": cs.get("collapse_ms"),
                "probes": cs.get("collapse_c_probes"),
                "back_probes": cb.get("collapse_c_probes"),
            }
            print(f"I178 {rec}", flush=True)
            recs.append(rec)
    ok = all(r.get("match_ripser") for r in recs)
    write({
        "id": "suffix_later_ab",
        "lever": "H01-suffix-later-ab",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "Case A+B high-time tail leave + K-sample vs back/Ripser",
        "receipts": recs,
    }, "I178")


if __name__ == "__main__":
    main()
