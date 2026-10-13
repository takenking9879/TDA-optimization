#!/usr/bin/env python3
"""I119 T-sweep on circle3000 for peak H1 clock; I120 high-d control."""

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


def pith(path, T, dim, collapse=1, timeout=300):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=300):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I119_Tsweep():
    path = BENCH / "datasets/generated/circle_noisy_n3000.csv"
    recs = []
    for T in (1.35, 1.45, 1.55, 1.65):
        pr, tr = ripser(path, T, 1, timeout=300)
        pp, c, tp = pith(path, T, 1, 1, timeout=300)
        fid = compare(pr, pp, 1)
        recs.append({"n": 3000, "T": T, "match": fid.get("exact_match_tol"),
                     "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
        print(f"I119 T={T} ratio={recs[-1]['time_ratio']} edges_out={recs[-1]['edges_out']}",
              flush=True)
    best = max((r["time_ratio"] or 0) for r in recs)
    write({"id": "circle3000_T_sweep", "lever": "H03", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": f"circle3000 T-sweep peak {best:.2f}×",
           "receipts": recs}, "I119")


def I120_highd():
    path = BENCH / "datasets/generated/uniform10_n200.csv"
    pr, tr = ripser(path, 1.8, 1)
    recs = []
    for coll in (1, -1):
        pp, c, tp = pith(path, 1.8, 1, coll)
        fid = compare(pr, pp, 1)
        recs.append({"collapse": coll, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    write({"id": "uniform10_n200_control", "lever": "H01", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "high-d control after reserve collapse",
           "receipts": recs}, "I120")


def main():
    I119_Tsweep()
    I120_highd()


if __name__ == "__main__":
    main()
