#!/usr/bin/env python3
"""I117 circle n=4000 H1 clock; I118 torus hold-out; I119 two-circle sanity."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith(path, T, dim, collapse=1, timeout=600):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=600):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I117_circle4000():
    rng = np.random.default_rng(0)
    n = 4000
    t = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (n, 2))
    path = BENCH / "datasets/generated/circle_noisy_n4000.csv"
    np.savetxt(path, pts, delimiter=",")
    recs = []
    for T in (1.2, 1.5):
        pr, tr = ripser(path, T, 1, timeout=600)
        pp, c, tp = pith(path, T, 1, 1, timeout=600)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
        print(f"I117 n=4000 T={T} ratio={recs[-1]['time_ratio']} match={recs[-1]['match']}",
              flush=True)
    best = max((r["time_ratio"] or 0) for r in recs)
    write({"id": "circle4000_h1", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": f"circle n=4000 H1 clock best {best:.2f}×",
           "receipts": recs}, "I117")


def I118_torus():
    path = BENCH / "datasets/generated/torus_n200.csv"
    recs = []
    for coll in (1, -1):
        pr, tr = ripser(path, 1.6, 1)
        pp, c, tp = pith(path, 1.6, 1, coll)
        fid = compare(pr, pp, 1)
        recs.append({"collapse": coll, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    write({"id": "torus200_after_reserve", "lever": "H01", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "torus200 hold-out after reserve collapse",
           "receipts": recs}, "I118")


def main():
    I117_circle4000()
    I118_torus()


if __name__ == "__main__":
    main()
