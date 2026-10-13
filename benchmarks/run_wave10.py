#!/usr/bin/env python3
"""I111–I120: implicit cohomology MST-apparent fix + hold-out clocks."""

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


def pith(path, T, dim, collapse=1, engine="homology", timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", engine, "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I106_maxdeg_circle():
    recs = []
    for n, T in ((80, 1.2), (200, 1.2), (1000, 1.2), (2000, 1.2), (2000, 1.5)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "T": T, "missing": True})
            continue
        pr, tr = ripser(path, T, 1, timeout=300)
        pp, c, tp = pith(path, T, 1, 1, "homology", timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    ok = all(r.get("match") for r in recs if not r.get("missing"))
    write({"id": "maxdeg_first_circle", "lever": "H01-maxdeg", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "max-degree-first dominator vs I082/I096",
           "receipts": recs}, "I106")


def I111_implicit_vs_ripser():
    recs = []
    for name, n, T, dim, coll in (
        ("circle_noisy", 80, 1.2, 1, 0),
        ("circle_noisy", 80, 1.2, 1, 1),
        ("circle_noisy", 200, 1.2, 1, 0),
        ("circle_noisy", 200, 1.2, 1, 1),
        ("blobs", 80, 1.0, 1, 0),
        ("sphere", 80, 1.4, 2, 1),
        ("torus", 80, 1.6, 1, 1),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, _ = ripser(path, T, dim)
        pp, c, _ = pith(path, T, dim, coll, "implicit")
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "n": n, "collapse": coll, "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched"),
                     "h1_pith": sum(1 for p in pp if p[0] == 1),
                     "apparent": c.get("columns_apparent")})
    ok = all(r["match"] for r in recs)
    write({"id": "implicit_mst_apparent", "lever": "H02", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"implicit vs Ripser after MST-apparent fix {sum(r['match'] for r in recs)}/{len(recs)}",
           "receipts": recs}, "I111")
    return ok


def I112_implicit_vs_homology():
    recs = []
    for name, n, T, dim, coll in (
        ("circle_noisy", 80, 1.2, 1, 0),
        ("circle_noisy", 200, 1.2, 1, 0),
        ("torus", 80, 1.6, 1, 0),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        ph, _, _ = pith(path, T, dim, coll, "homology")
        pi, _, _ = pith(path, T, dim, coll, "implicit")
        fid = compare(ph, pi, dim)
        recs.append({"dataset": name, "n": n, "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched")})
    write({"id": "implicit_vs_owned_homology", "lever": "H02", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "implicit vs persist_sparse after I111",
           "receipts": recs}, "I112")


def I113_thick_clock():
    recs = []
    for name, n, T, dim in (("torus", 200, 1.6, 1), ("uniform10", 200, 1.8, 1)):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            recs.append({"dataset": name, "n": n, "missing": True})
            continue
        pr, tr = ripser(path, T, dim)
        for eng, coll in (("homology", 1), ("homology", -1), ("implicit", 0), ("implicit", 1)):
            pp, c, tp = pith(path, T, dim, coll, eng, timeout=180)
            fid = compare(pr, pp, dim)
            recs.append({"dataset": name, "n": n, "engine": eng, "collapse": coll,
                         "match": fid.get("exact_match_tol"),
                         "ripser_s": tr, "pith_s": tp,
                         "time_ratio": (tr / tp) if tp else None,
                         "edges_out": c.get("edges_out")})
    write({"id": "thick_remainder_clock", "lever": "H02", "class": "experiment",
           "fidelity": "exact",
           "status": "hold",
           "summary": "torus/high-d: implicit vs homology vs Ripser",
           "receipts": recs}, "I113")


def main():
    I106_maxdeg_circle()
    I111_implicit_vs_ripser()
    I112_implicit_vs_homology()
    I113_thick_clock()


if __name__ == "__main__":
    main()
