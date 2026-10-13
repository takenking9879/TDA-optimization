#!/usr/bin/env python3
"""I128 -march=native collapse clock; I129 torus500 adaptive."""

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


def I128_native():
    recs = []
    for n, T in ((2000, 1.5), (3000, 1.5)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith(path, T, 1, 1)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
        print(f"I128 n={n} ratio={recs[-1]['time_ratio']} collapse_ms={recs[-1]['collapse_ms']}",
              flush=True)
    write({"id": "march_native_collapse", "lever": "H01-native", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "-march=native -flto vs I121",
           "receipts": recs}, "I128")


def I129_torus500():
    path = BENCH / "datasets/generated/torus_n500.csv"
    if not path.exists():
        write({"id": "torus500_adaptive", "lever": "H01", "class": "reproduced",
               "fidelity": "exact", "status": "hold", "summary": "missing torus_n500",
               "receipts": []}, "I129")
        return
    pr, tr = ripser(path, 1.6, 1, timeout=180)
    recs = []
    for coll in (1, -1):
        pp, c, tp = pith(path, 1.6, 1, coll, timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({"collapse": coll, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out"), "pith_s": tp, "ripser_s": tr})
    write({"id": "torus500_adaptive", "lever": "H01", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "torus500 1-pass vs adaptive",
           "receipts": recs}, "I129")


def main():
    I128_native()
    I129_torus500()


if __name__ == "__main__":
    main()
