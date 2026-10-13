#!/usr/bin/env python3
"""I149 forward 2020 collapse; I150 time-axis D&C collapse."""

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


def I149_forward():
    recs = []
    for name, n, T, timeout in (
        ("circle_noisy", 80, 1.2, 60),
        ("circle_noisy", 200, 1.2, 60),
        ("torus", 80, 1.6, 60),
        ("circle_noisy", 200, 1.5, 120),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        for alg in ("back", "forward"):
            try:
                pp, c, tp = pith(path, T, 1, 1, alg, timeout=timeout)
                fid = compare(pr, pp, 1)
                recs.append({
                    "dataset": name, "n": n, "T": T, "alg": alg,
                    "match": fid.get("exact_match_tol"),
                    "unmatched": fid.get("unmatched"),
                    "ripser_s": tr, "pith_s": tp,
                    "time_ratio": tr / tp if tp else None,
                    "collapse_ms": c.get("collapse_ms"),
                    "edges_out": c.get("edges_out"),
                })
            except Exception as ex:
                recs.append({"dataset": name, "n": n, "alg": alg, "error": str(ex)[:300]})
            print(f"I149 {name} n={n} {alg} {recs[-1]}", flush=True)
    ok = all(r.get("match") for r in recs if "error" not in r)
    write({"id": "forward_collapse", "lever": "H01-fwd", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"forward 2020 vs backward {sum(1 for r in recs if r.get('match'))}/{len(recs)}",
           "receipts": recs}, "I149")


def I150_dc():
    recs = []
    for name, n, T, timeout in (
        ("circle_noisy", 80, 1.2, 60),
        ("circle_noisy", 200, 1.2, 60),
        ("torus", 200, 1.6, 60),
        ("circle_noisy", 2000, 1.5, 180),
        ("circle_noisy", 3000, 1.5, 300),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        for alg in ("back", "dc"):
            try:
                pp, c, tp = pith(path, T, 1, 1, alg, timeout=timeout)
                fid = compare(pr, pp, 1)
                recs.append({
                    "dataset": name, "n": n, "T": T, "alg": alg,
                    "match": fid.get("exact_match_tol"),
                    "unmatched": fid.get("unmatched"),
                    "ripser_s": tr, "pith_s": tp,
                    "time_ratio": tr / tp if tp else None,
                    "collapse_ms": c.get("collapse_ms"),
                    "edges_out": c.get("edges_out"),
                })
            except Exception as ex:
                recs.append({"dataset": name, "n": n, "alg": alg, "error": str(ex)[:300]})
            print(f"I150 {name} n={n} {alg} {recs[-1]}", flush=True)
    ok = all(r.get("match") for r in recs if "error" not in r)
    c2d = next((r for r in recs if r.get("n") == 2000 and r.get("alg") == "dc"), {})
    c2b = next((r for r in recs if r.get("n") == 2000 and r.get("alg") == "back"), {})
    write({"id": "time_axis_dc_impl", "lever": "H01-dc", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": (f"D&C identity {ok}; circle2000 dc {c2d.get('time_ratio')}× / "
                       f"{c2d.get('collapse_ms')} ms vs back {c2b.get('time_ratio')}× / "
                       f"{c2b.get('collapse_ms')} ms"),
           "receipts": recs}, "I150")


def main():
    I149_forward()
    I150_dc()


if __name__ == "__main__":
    main()
