#!/usr/bin/env python3
"""I158: prefetch C-walk vs I156/I157."""

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


def pith(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"],
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


def I158_prefetch():
    recs = []
    for n, T, timeout in ((2000, 1.5, 180), (3000, 1.5, 360)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, timeout=timeout)
        pp, c, tp = pith(path, T, timeout)
        fid = compare(pr, pp, 1)
        recs.append({
            "n": n, "T": T, "match": fid.get("exact_match_tol"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "edges_out": c.get("edges_out"),
            "fast_trims": c.get("collapse_fast_trims"),
        })
        print(f"I158 n={n} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']} "
              f"ms={recs[-1]['collapse_ms']} out={recs[-1]['edges_out']}", flush=True)
    ok = all(r.get("match") for r in recs)
    write({
        "id": "prefetch_c_walk",
        "lever": "H01-prefetch",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "prefetch +8 C-walk vs I156",
        "baseline": {
            "I156_circle2000_collapse_ms": 3746.3351,
            "I156_circle2000_ratio": 7.204315563457339,
            "I156_circle3000_collapse_ms": 12605.784,
            "I156_circle3000_ratio": 8.887997792569863,
        },
        "receipts": recs,
    }, "I158")


def main():
    I158_prefetch()


if __name__ == "__main__":
    main()
