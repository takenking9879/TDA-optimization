#!/usr/bin/env python3
"""I184: back-bits vs back vs Ripser at circle n=4000 (flagship 10× test)."""

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


def pith_cmd(path, T, extra, timeout=400):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra,
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    for name, n, T, timeout, rto in (
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("circle_noisy", 4000, 1.5, 240, 400),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back-bits"], timeout)
        out_r, tr, _ = run_cmd(
            [str(RIPSER), "--format", "point-cloud", "--dim", "1",
             "--threshold", str(T), str(path)],
            rto,
        )
        pr = parse_ripser(out_r)
        fid = compare(pb, ps, 1)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_back": fid.get("exact_match_tol"),
            "unmatched_back": fid.get("unmatched"),
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "back_s": tb, "bits_s": ts, "ripser_s": tr,
            "vs_back": tb / ts if ts else None,
            "vs_ripser": tr / ts if ts else None,
            "back_vs_ripser": tr / tb if tb else None,
            "back_out": cb.get("edges_out"),
            "out": cs.get("edges_out"),
            "back_collapse_ms": cb.get("collapse_ms"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "collapse_ratio": (cb.get("collapse_ms") or 0) / (cs.get("collapse_ms") or 1),
            "back_probes": cb.get("collapse_c_probes"),
            "bits_probes": cs.get("collapse_c_probes"),
            "back_c_size": cb.get("collapse_c_size"),
            "bits_c_size": cs.get("collapse_c_size"),
        }
        print(f"I184 {rec}", flush=True)
        recs.append(rec)

    n4000 = next((r for r in recs if r["n"] == 4000), None)
    win = n4000 and n4000.get("match_ripser") and (n4000.get("vs_ripser") or 0) >= 10
    write({
        "id": "bitand_flagship",
        "lever": "H01-bitand-flagship",
        "class": "experiment",
        "fidelity": "exact" if all(r.get("match_ripser") for r in recs) else "unverified",
        "status": "support" if win else "partial",
        "summary": "I184 back-bits vs back/Ripser at n=2000/4000",
        "receipts": recs,
    }, "I184")


if __name__ == "__main__":
    main()
