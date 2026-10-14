#!/usr/bin/env python3
"""I181: escalate-until-first-keep + Case-B-as-deeper-K, not leave."""

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
    variants = [
        ("k2", ["--collapse-alg", "suffix-later", "--suffix-k", "2"]),
        ("k2-esc8", ["--collapse-alg", "suffix-later", "--suffix-k", "2",
                     "--later-escalate", "8"]),
        ("k2-esc8-b", ["--collapse-alg", "suffix-later", "--suffix-k", "2",
                       "--later-escalate", "8", "--later-b"]),
        ("k2-b", ["--collapse-alg", "suffix-later", "--suffix-k", "2", "--later-b"]),
    ]
    jobs = [
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("circle_noisy", 3000, 1.5, 180, 180),
        ("blobs", 2000, 1.0, 90, 60),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        for tag, extra in variants:
            ps, cs, ts = pith_cmd(path, T, extra, timeout)
            fid = compare(pb, ps, 1)
            fidr = compare(pr, ps, 1)
            rec = {
                "name": name, "n": n, "T": T, "variant": tag,
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
            print(f"I181 {rec}", flush=True)
            recs.append(rec)

    n3000_exact = any(
        r.get("name") == "circle_noisy" and r.get("n") == 3000 and r.get("match_ripser")
        and r.get("variant") in ("k2-esc8", "k2-esc8-b", "k2-b")
        for r in recs
    )
    n2000_win = any(
        r.get("name") == "circle_noisy" and r.get("n") == 2000 and r.get("match_ripser")
        and (r.get("vs_ripser") or 0) >= 10
        for r in recs
    )
    if n3000_exact:
        path = BENCH / "datasets/generated/circle_noisy_n4000.csv"
        pb, cb, tb = pith_cmd(path, 1.5, ["--collapse-alg", "back"], 240)
        pr, tr = ripser(path, 1.5, 360)
        for tag, extra in variants:
            if tag == "k2":
                continue
            ps, cs, ts = pith_cmd(path, 1.5, extra, 240)
            fid = compare(pb, ps, 1)
            fidr = compare(pr, ps, 1)
            rec = {
                "name": "circle_noisy", "n": 4000, "T": 1.5, "variant": tag,
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
            print(f"I181 {rec}", flush=True)
            recs.append(rec)

    write({
        "id": "escalate_first_keep",
        "lever": "H01-escalate-first-keep",
        "class": "experiment",
        "fidelity": "partial",
        "status": "support" if n3000_exact and n2000_win else ("partial" if n2000_win else "reject"),
        "summary": "I181 escalate-until-first-keep / Case-B-as-K vs back/Ripser",
        "receipts": recs,
    }, "I181")


if __name__ == "__main__":
    main()
