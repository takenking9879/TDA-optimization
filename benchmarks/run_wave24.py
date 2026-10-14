#!/usr/bin/env python3
"""I148: remasure circle4000 T=1.5 with selected implicit engine."""

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


def main():
    path = BENCH / "datasets/generated/circle_noisy_n4000.csv"
    if not path.exists():
        write({"id": "circle4000_implicit", "lever": "H01+H02", "class": "reproduced",
               "fidelity": "exact", "status": "hold", "summary": "missing circle4000",
               "receipts": []}, "I148")
        return
    pr, tr, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", "1.5", str(path)],
        600,
    )
    pr = parse_ripser(pr)
    out, tp, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", "1.5",
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"],
        600,
    )
    pp, c = parse_pith_text(out)
    fid = compare(pr, pp, 1)
    rec = {
        "n": 4000, "T": 1.5, "engine": "implicit",
        "match": fid.get("exact_match_tol"),
        "unmatched": fid.get("unmatched"),
        "ripser_s": tr, "pith_s": tp,
        "time_ratio": tr / tp if tp else None,
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "edges_out": c.get("edges_out"),
    }
    print(f"I148 {rec}", flush=True)
    write({"id": "circle4000_implicit", "lever": "H01+H02", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if rec["match"] else "reject",
           "summary": f"circle4000 T=1.5 implicit {rec['time_ratio']}× (I117 was 8.38×)",
           "receipts": [rec]}, "I148")


if __name__ == "__main__":
    main()
