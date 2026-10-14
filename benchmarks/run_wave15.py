#!/usr/bin/env python3
"""I121 row-pointer collapse; I126 same-diameter apparent implicit."""

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


def pith(path, T, dim, collapse=1, engine="homology", timeout=300):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", engine, "--no-enclosing"],
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


def I121_rowptr():
    recs = []
    for n, T in ((80, 1.2), (200, 1.2), (2000, 1.5), (3000, 1.5)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "T": T, "missing": True})
            continue
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith(path, T, 1, 1, "homology")
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
        print(f"I121 n={n} T={T} ratio={recs[-1].get('time_ratio')} match={recs[-1].get('match')}",
              flush=True)
    ok = all(r.get("match") for r in recs if not r.get("missing"))
    write({"id": "rowptr_collapse", "lever": "H01-row", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "DenseTimes row pointers vs I114/I115",
           "receipts": recs}, "I121")


def I126_implicit():
    recs = []
    for name, n, T, dim, coll in (
        ("circle_noisy", 80, 1.2, 1, 0),
        ("circle_noisy", 80, 1.2, 1, 1),
        ("circle_noisy", 200, 1.2, 1, 0),
        ("circle_noisy", 200, 1.2, 1, 1),
        ("blobs", 80, 1.0, 1, 0),
        ("torus", 80, 1.6, 1, 1),
        ("sphere", 80, 1.4, 2, 1),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, _ = ripser(path, T, dim)
        pp, c, _ = pith(path, T, dim, coll, "implicit")
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "n": n, "collapse": coll,
                     "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched"),
                     "h1_pith": sum(1 for p in pp if p.get("dim") == 1),
                     "apparent": c.get("cols_apparent") or c.get("columns_apparent")})
        print(f"I126 {name} n={n} c={coll} match={recs[-1]['match']} unmatched={recs[-1]['unmatched']}",
              flush=True)
    ok = all(r["match"] for r in recs)
    write({"id": "implicit_same_diameter_apparent", "lever": "H02", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"same-diameter apparent implicit {sum(r['match'] for r in recs)}/{len(recs)}",
           "receipts": recs}, "I126")


def I127_thick_implicit():
    recs = []
    for name, n, T in (("torus", 200, 1.6), ("uniform10", 200, 1.8)):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, 1)
        for eng, coll in (("homology", 1), ("homology", -1), ("implicit", 1)):
            pp, c, tp = pith(path, T, 1, coll, eng, timeout=180)
            fid = compare(pr, pp, 1)
            recs.append({"dataset": name, "engine": eng, "collapse": coll,
                         "match": fid.get("exact_match_tol"),
                         "time_ratio": tr / tp if tp else None,
                         "pith_s": tp, "ripser_s": tr,
                         "edges_out": c.get("edges_out")})
    write({"id": "thick_implicit_clock", "lever": "H02", "class": "experiment",
           "fidelity": "exact",
           "status": "hold",
           "summary": "torus/high-d implicit after same-diameter apparent",
           "receipts": recs}, "I127")


def main():
    I126_implicit()
    I121_rowptr()
    I127_thick_implicit()


if __name__ == "__main__":
    main()
