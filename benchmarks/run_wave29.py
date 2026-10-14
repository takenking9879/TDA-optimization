#!/usr/bin/env python3
"""I156: fused first-apex C-walk; I157: remasure flagship circle4000."""

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


def pith(path, T, dim, collapse=1, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "implicit", "--no-enclosing"],
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


def rec(n, T, pr, tr, pp, c, tp):
    fid = compare(pr, pp, 1)
    return {
        "n": n, "T": T, "match": fid.get("exact_match_tol"),
        "unmatched": fid.get("unmatched"),
        "ripser_s": tr, "pith_s": tp,
        "time_ratio": tr / tp if tp else None,
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "edges_in": c.get("edges_in"),
        "edges_out": c.get("edges_out"),
        "c_probes": c.get("collapse_c_probes"),
        "c_size": c.get("collapse_c_size"),
        "fast_trims": c.get("collapse_fast_trims"),
        "trims": c.get("collapse_trims"),
        "shifts": c.get("collapse_shifts"),
        "dom_hits": c.get("collapse_dom_hits"),
    }


def I156_fused():
    recs = []
    for n, T, timeout in ((80, 1.2, 60), (200, 1.5, 60), (2000, 1.5, 180), (3000, 1.5, 360)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        pp, c, tp = pith(path, T, 1, 1, timeout=timeout)
        recs.append(rec(n, T, pr, tr, pp, c, tp))
        print(f"I156 n={n} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']} "
              f"ms={recs[-1]['collapse_ms']} out={recs[-1]['edges_out']} "
              f"fast_trims={recs[-1]['fast_trims']}", flush=True)
    ok = all(r.get("match") for r in recs)
    write({
        "id": "fused_first_apex",
        "lever": "H01-fused-apex",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "fused first-apex C-walk vs I155 pair-nbr",
        "baseline": {
            "I155_circle2000_collapse_ms": 4068.3185,
            "I155_circle2000_ratio": 6.519576098410856,
            "I155_circle2000_out": 5169,
            "I155_circle3000_collapse_ms": 13535.812,
            "I155_circle3000_ratio": 8.176628254638509,
            "I155_circle3000_out": 9190,
        },
        "receipts": recs,
    }, "I156")
    return recs


def I157_circle4000():
    path = BENCH / "datasets/generated/circle_noisy_n4000.csv"
    pr, tr = ripser(path, 1.5, 1, timeout=600)
    pp, c, tp = pith(path, 1.5, 1, 1, timeout=180)
    r = rec(4000, 1.5, pr, tr, pp, c, tp)
    print(f"I157 n=4000 match={r['match']} ratio={r['time_ratio']} "
          f"ms={r['collapse_ms']} out={r['edges_out']}", flush=True)
    write({
        "id": "circle4000_fused",
        "lever": "H01-flagship",
        "class": "experiment",
        "fidelity": "exact" if r.get("match") else "unverified",
        "status": "support" if r.get("match") else "reject",
        "summary": "circle4000 T=1.5 after I155+I156 vs I148 8.74×",
        "baseline": {
            "I148_ratio": 8.74,
            "I148_ripser_s": 293,
            "I148_pith_s": 33.5,
            "I148_collapse_ms": 33200,
            "I148_out": 12562,
        },
        "receipts": [r],
    }, "I157")


def main():
    I156_fused()
    I157_circle4000()


if __name__ == "__main__":
    main()
