#!/usr/bin/env python3
"""I203: cofacet-walk early-stop vs src / Ripser (shape-agnostic reduce)."""

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


def pith_cmd(path, T, extra, timeout=240):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra,
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


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("blobs", 2000, 1.0, 90, 60),
        ("sphere", 2000, 1.4, 90, 60),
        ("torus", 2000, 1.6, 90, 90),
        ("figure8", 500, 1.0, 60, 60),
        ("two_circles", 400, 1.2, 60, 60),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back-src"], timeout)
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        fid = compare(pb, ps, 1)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_src": fid.get("exact_match_tol"),
            "unmatched_src": fid.get("unmatched"),
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "bits_s": ts, "ripser_s": tr,
            "vs_ripser": tr / ts if ts else None,
            "out": cs.get("edges_out"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "cofacet_probes": cs.get("cofacet_probes"),
            "cofacet_apparent_probes": cs.get("cofacet_apparent_probes"),
            "cols_apparent": cs.get("cols_apparent"),
            "cols_reduced": cs.get("cols_reduced"),
        }
        print(f"I203 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    other = [r for r in recs if r["name"] != "torus" and r.get("reduce_ms") is not None]
    torus_ok = torus and torus.get("match_ripser")
    write({
        "id": "cofacet_early_stop",
        "lever": "H09-cofacet-early-stop",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if ident and torus_ok else "reject",
        "summary": "I203 hi-walk early-stop after zero-pivot / emergent",
        "receipts": recs,
        "note": "Select as default only if exact and reduce_ms drops vs I202 on torus and another family.",
    }, "I203")


if __name__ == "__main__":
    main()
