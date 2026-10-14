#!/usr/bin/env python3
"""I155: pair-nbr one-gather C-build identity + clock vs I153/I154."""

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


def pith(path, T, dim, collapse=1, alg="back", timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--collapse-alg", alg, "--engine", "implicit",
         "--no-enclosing"],
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


def I155_pair_nbr():
    recs = []
    cases = (
        (80, 1.2, 60),
        (200, 1.5, 60),
        (2000, 1.5, 180),
        (3000, 1.5, 360),
    )
    for n, T, timeout in cases:
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        pp, c, tp = pith(path, T, 1, 1, "back", timeout=timeout)
        fid = compare(pr, pp, 1)
        c_probes = c.get("collapse_c_probes") or 0
        c_size = c.get("collapse_c_size") or 0
        recs.append({
            "n": n, "T": T, "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "reduce_ms": c.get("reduce_ms"),
            "edges_in": c.get("edges_in"),
            "edges_out": c.get("edges_out"),
            "c_probes": c_probes,
            "c_size": c_size,
            "dom_tests": c.get("collapse_dom_tests"),
            "dom_hits": c.get("collapse_dom_hits"),
            "shift_lookups": c.get("collapse_shift_lookups"),
            "shifts": c.get("collapse_shifts"),
            "trims": c.get("collapse_trims"),
        })
        print(f"I155 n={n} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']} "
              f"ms={recs[-1]['collapse_ms']} out={recs[-1]['edges_out']} "
              f"probes={c_probes} c_size={c_size} shift_lookups={recs[-1]['shift_lookups']}",
              flush=True)
    ok = all(r.get("match") for r in recs)
    write({
        "id": "pair_nbr_one_gather",
        "lever": "H01-pair-nbr",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "pair-nbr one-gather C-build vs I153/I154 backward",
        "baseline": {
            "I153_circle2000_collapse_ms": 4253.1195,
            "I153_circle2000_ratio": 6.471264596582511,
            "I153_circle2000_out": 5169,
            "I153_circle3000_collapse_ms": 14621.864,
            "I153_circle3000_ratio": 7.880558375832178,
            "I153_circle3000_out": 9190,
        },
        "receipts": recs,
    }, "I155")
    return recs


def main():
    I155_pair_nbr()


if __name__ == "__main__":
    main()
