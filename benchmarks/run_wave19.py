#!/usr/bin/env python3
"""I137–I140: Ripser-style heap cohomology on Graph (own E3)."""

from __future__ import annotations

import json
import sys
import tempfile
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


def pith(path, T, dim, collapse=1, engine="implicit", timeout=180):
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


def I137_identity():
    recs = []
    cases = (
        ("circle_noisy", 80, 1.2, 1, 0),
        ("circle_noisy", 80, 1.2, 1, 1),
        ("circle_noisy", 200, 1.2, 1, 0),
        ("circle_noisy", 200, 1.2, 1, 1),
        ("blobs", 80, 1.0, 1, 0),
        ("torus", 80, 1.6, 1, 1),
        ("torus", 200, 1.6, 1, 1),
        ("sphere", 80, 1.4, 2, 1),
    )
    for name, n, T, dim, coll in cases:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            recs.append({"dataset": name, "n": n, "collapse": coll, "missing": True})
            continue
        pr, _ = ripser(path, T, dim)
        pp, c, dt = pith(path, T, dim, coll, "implicit")
        fid = compare(pr, pp, dim)
        recs.append({
            "dataset": name, "n": n, "T": T, "dim": dim, "collapse": coll,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "h1_pith": sum(1 for p in pp if p.get("dim") == 1),
            "h1_ripser": sum(1 for p in pr if p.get("dim") == 1),
            "cols_apparent": c.get("cols_apparent"),
            "cols_reduced": c.get("cols_reduced"),
            "reduce_ms": c.get("reduce_ms"),
            "pith_s": dt,
        })
        print(f"I137 {name} n={n} c={coll} match={recs[-1]['match']} "
              f"unmatched={recs[-1]['unmatched']} pith={dt:.3f}s", flush=True)
    ok = all(r.get("match") for r in recs if not r.get("missing"))
    write({"id": "ripser_heap_coh_identity", "lever": "H02-heap", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"Ripser-heap implicit {sum(1 for r in recs if r.get('match'))}/{len(recs)}",
           "receipts": recs}, "I137")
    return ok


def I138_clock_small():
    recs = []
    for name, n, T, dim, coll in (
        ("circle_noisy", 200, 1.2, 1, 1),
        ("torus", 200, 1.6, 1, 1),
        ("torus", 200, 1.6, 1, 0),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, dim)
        for eng in ("homology", "implicit"):
            pp, c, tp = pith(path, T, dim, coll, eng)
            fid = compare(pr, pp, dim)
            recs.append({
                "dataset": name, "n": n, "collapse": coll, "engine": eng,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr, "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
            })
            print(f"I138 {name} n={n} c={coll} {eng} match={recs[-1]['match']} "
                  f"ratio={recs[-1]['time_ratio']}", flush=True)
    write({"id": "heap_coh_clock_small", "lever": "H02-heap", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "heap coh vs homology vs Ripser on n=200",
           "receipts": recs}, "I138")


def I139_torus1000():
    path = BENCH / "datasets/generated/torus_n1000.csv"
    if not path.exists():
        write({"id": "heap_coh_torus1000", "lever": "H02-heap", "class": "experiment",
               "fidelity": "exact", "status": "hold", "summary": "missing torus_n1000",
               "receipts": []}, "I139")
        return
    pr, tr = ripser(path, 1.6, 1, timeout=180)
    recs = []
    for coll, eng, timeout in ((1, "implicit", 180), (1, "homology", 180), (-1, "implicit", 180)):
        try:
            pp, c, tp = pith(path, 1.6, 1, coll, eng, timeout=timeout)
            fid = compare(pr, pp, 1)
            recs.append({
                "collapse": coll, "engine": eng,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr, "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "reduce_ms": c.get("reduce_ms"),
                "collapse_ms": c.get("collapse_ms"),
                "edges_out": c.get("edges_out"),
                "cols_apparent": c.get("cols_apparent"),
            })
        except Exception as ex:
            recs.append({"collapse": coll, "engine": eng, "error": str(ex)[:300]})
        print(f"I139 coll={coll} {eng} {recs[-1]}", flush=True)

    # E3 reference on same residual
    out, dt_c, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", "1.6",
         "--collapse", "1", "--sparse-only", "--no-enclosing"],
        180,
    )
    with tempfile.NamedTemporaryFile("w", suffix=".sparse", delete=False) as f:
        f.write(out)
        spar = f.name
    rs, dt_r, _ = run_cmd(
        [str(RIPSER), "--format", "sparse", "--dim", "1", "--threshold", "1.6", spar],
        180,
    )
    pp = parse_ripser(rs)
    fid = compare(pr, pp, 1)
    e3_total = dt_c + dt_r
    recs.append({
        "engine": "E3", "collapse": 1,
        "match": fid.get("exact_match_tol"),
        "collapse_s": dt_c, "ripser_residual_s": dt_r, "total_s": e3_total,
        "ripser_orig_s": tr, "time_ratio": tr / e3_total if e3_total else None,
    })
    print(f"I139 E3 match={fid.get('exact_match_tol')} ratio={tr / e3_total if e3_total else None}",
          flush=True)
    ok = all(r.get("match") for r in recs if "error" not in r)
    write({"id": "heap_coh_torus1000", "lever": "H02-heap", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "torus1000 heap-coh vs homology vs E3 vs Ripser",
           "receipts": recs}, "I139")


def I140_circle2000_implicit():
    path = BENCH / "datasets/generated/circle_noisy_n2000.csv"
    if not path.exists():
        write({"id": "heap_coh_circle2000", "lever": "H02-heap", "class": "experiment",
               "fidelity": "exact", "status": "hold", "summary": "missing circle2000",
               "receipts": []}, "I140")
        return
    pr, tr = ripser(path, 1.5, 1, timeout=180)
    recs = []
    for eng in ("homology", "implicit"):
        pp, c, tp = pith(path, 1.5, 1, 1, eng, timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({
            "engine": eng, "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "reduce_ms": c.get("reduce_ms"),
            "collapse_ms": c.get("collapse_ms"),
            "edges_out": c.get("edges_out"),
        })
        print(f"I140 {eng} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']}", flush=True)
    write({"id": "heap_coh_circle2000", "lever": "H02-heap", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle2000 T=1.5 heap-coh vs homology",
           "receipts": recs}, "I140")


def main():
    I137_identity()
    I138_clock_small()
    I139_torus1000()
    I140_circle2000_implicit()


if __name__ == "__main__":
    main()
