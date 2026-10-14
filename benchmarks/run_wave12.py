#!/usr/bin/env python3
"""I114 reserve+inplace collapse; I115 circle3000 full collapse; I116–I118 hold-outs."""

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


def I114_reserve():
    recs = []
    for n, T, dim in ((80, 1.2, 1), (200, 1.2, 1), (2000, 1.2, 1), (2000, 1.5, 1)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, dim)
        pp, c, tp = pith(path, T, dim, 1)
        fid = compare(pr, pp, dim)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    write({"id": "reserve_inplace_collapse", "lever": "H01-reserve", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "C_now.reserve + in-place edge sort vs I096",
           "receipts": recs}, "I114")


def I115_circle3000():
    rng = np.random.default_rng(0)
    n = 3000
    t = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (n, 2))
    path = BENCH / "datasets/generated/circle_noisy_n3000.csv"
    np.savetxt(path, pts, delimiter=",")
    recs = []
    for T in (1.2, 1.5):
        pr, tr = ripser(path, T, 1, timeout=300)
        pp, c, tp = pith(path, T, 1, 1, timeout=300)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
    write({"id": "circle3000_h1_full", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle n=3000 H1 clock vs Ripser (full collapse)",
           "receipts": recs}, "I115")


def I116_sphere_h2():
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pr, tr = ripser(path, 1.4, 2)
    pp, c, tp = pith(path, 1.4, 2, 1)
    fid = compare(pr, pp, 2)
    write({"id": "sphere500_after_reserve", "lever": "H01", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "sphere500 H2 after reserve/inplace",
           "receipts": [{"match": fid.get("exact_match_tol"),
                         "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms"),
                         "edges_out": c.get("edges_out")}]}, "I116")


def main():
    I114_reserve()
    I115_circle3000()
    I116_sphere_h2()


if __name__ == "__main__":
    main()
