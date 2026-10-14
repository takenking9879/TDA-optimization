#!/usr/bin/env python3
"""I162: H1 clock on other families at n=2000 (hunt 10× off-circle)."""

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


def I162_families():
    cases = (
        ("circle_noisy", 2000, 1.2, 180),
        ("blobs", 2000, 1.0, 180),
        ("torus", 2000, 1.6, 300),
        ("sphere", 2000, 1.4, 300),
        ("uniform2", 2000, 0.35, 180),
    )
    recs = []
    for name, n, T, timeout in cases:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            recs.append({"name": name, "n": n, "T": T, "error": "missing dataset"})
            print(f"I162 {name} n={n} MISSING", flush=True)
            continue
        try:
            pr, tr = ripser(path, T, timeout=timeout)
            pp, c, tp = pith(path, T, timeout)
            fid = compare(pr, pp, 1)
            recs.append({
                "name": name, "n": n, "T": T,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr, "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "edges_in": c.get("edges_in"),
                "edges_out": c.get("edges_out"),
            })
        except Exception as ex:
            recs.append({"name": name, "n": n, "T": T, "error": str(ex)[:400]})
        print(f"I162 {recs[-1]}", flush=True)
    ok = all(r.get("match") for r in recs if "error" not in r)
    best = max((r.get("time_ratio") or 0) for r in recs if "error" not in r)
    write({
        "id": "h1_other_families_n2000",
        "lever": "H01-scope",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": f"H1 other families n=2000; best ratio {best:.2f}×",
        "receipts": recs,
    }, "I162")


def main():
    I162_families()


if __name__ == "__main__":
    main()
