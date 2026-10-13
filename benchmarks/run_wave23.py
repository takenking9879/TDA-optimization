#!/usr/bin/env python3
"""I147: AVX-512 gather domination on the collapse hot path."""

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


def main():
    recs = []
    for n, T, timeout in ((200, 1.2, 60), (2000, 1.5, 180), (3000, 1.5, 300)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        pp, c, tp = pith(path, T, 1, 1, timeout=timeout)
        fid = compare(pr, pp, 1)
        recs.append({
            "n": n, "T": T,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "edges_out": c.get("edges_out"),
        })
        print(f"I147 n={n} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']} "
              f"collapse_ms={recs[-1]['collapse_ms']}", flush=True)
    ok = all(r["match"] for r in recs)
    c2 = next(r for r in recs if r["n"] == 2000)
    c3 = next(r for r in recs if r["n"] == 3000)
    write({"id": "avx512_dominate", "lever": "H01-avx", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": (f"AVX-512 dominate circle2000 {c2['time_ratio']:.2f}× / {c2['collapse_ms']} ms; "
                       f"circle3000 {c3['time_ratio']:.2f}× / {c3['collapse_ms']} ms "
                       f"(I140 6.30×/4212; I144 8.11×/13885)"),
           "receipts": recs}, "I147")


if __name__ == "__main__":
    main()
