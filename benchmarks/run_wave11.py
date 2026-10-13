#!/usr/bin/env python3
"""I107–I110: budgeted (incomplete) collapse; I114+ hold-outs if implicit works."""

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


def pith(path, T, dim, collapse=1, engine="homology", budget=-1, timeout=180):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--collapse", str(collapse), "--engine", engine, "--no-enclosing",
           "--dom-budget", str(budget)]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I107_budget():
    recs = []
    path = BENCH / "datasets/generated/circle_noisy_n2000.csv"
    pr, tr = ripser(path, 1.5, 1, timeout=300)
    for budget in (1, 2, 4, -1):
        pp, c, tp = pith(path, 1.5, 1, 1, "homology", budget, timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({"budget": budget, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "pith_s": tp, "ripser_s": tr,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    # also T=1.2 budget=1
    pr2, tr2 = ripser(path, 1.2, 1, timeout=180)
    pp2, c2, tp2 = pith(path, 1.2, 1, 1, "homology", 1, timeout=180)
    fid2 = compare(pr2, pp2, 1)
    recs.append({"budget": 1, "T": 1.2, "match": fid2.get("exact_match_tol"),
                 "collapse_ms": c2.get("collapse_ms"), "pith_s": tp2, "ripser_s": tr2,
                 "time_ratio": tr2 / tp2 if tp2 else None,
                 "edges_out": c2.get("edges_out")})
    ok = all(r.get("match") for r in recs)
    write({"id": "budgeted_collapse_circle2000", "lever": "H01-budget", "class": "structural",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "max-degree budgeted collapse vs full (exact PH, thicker residual)",
           "receipts": recs}, "I107")


def I108_budget_identity():
    recs = []
    for name, n, T, dim in (("circle_noisy", 80, 1.2, 1), ("circle_noisy", 200, 1.2, 1),
                            ("blobs", 80, 1.0, 1), ("sphere", 80, 1.4, 2)):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, _ = ripser(path, T, dim)
        pp, c, _ = pith(path, T, dim, 1, "homology", 1)
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "n": n, "match": fid.get("exact_match_tol"),
                     "edges_out": c.get("edges_out")})
    write({"id": "budget1_identity", "lever": "H01-budget", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "dom-budget=1 identity on small suite",
           "receipts": recs}, "I108")


def I109_sphere_h2():
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pr, tr = ripser(path, 1.4, 2, timeout=180)
    recs = []
    for budget in (-1, 1):
        pp, c, tp = pith(path, 1.4, 2, 1, "homology", budget, timeout=180)
        fid = compare(pr, pp, 2)
        recs.append({"budget": budget, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"), "edges_out": c.get("edges_out")})
    write({"id": "sphere500_budget", "lever": "H01-budget", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "sphere500 H2 full vs budget=1",
           "receipts": recs}, "I109")


def I110_circle3000():
    import numpy as np
    rng = np.random.default_rng(0)
    n = 3000
    t = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (n, 2))
    path = BENCH / "datasets/generated/circle_noisy_n3000.csv"
    np.savetxt(path, pts, delimiter=",")
    recs = []
    for T, budget in ((1.2, -1), (1.5, -1), (1.5, 1)):
        pr, tr = ripser(path, T, 1, timeout=300)
        pp, c, tp = pith(path, T, 1, 1, "homology", budget, timeout=300)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "budget": budget, "match": fid.get("exact_match_tol"),
                     "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
    write({"id": "circle3000_h1", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle n=3000 H1 clock, full vs budget=1",
           "receipts": recs}, "I110")


def main():
    I107_budget()
    I108_budget_identity()
    I109_sphere_h2()
    I110_circle3000()


if __name__ == "__main__":
    main()
