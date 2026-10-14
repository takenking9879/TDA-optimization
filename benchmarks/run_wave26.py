#!/usr/bin/env python3
"""I151 collapse profile; I152 forward domination-at-current-grade fix."""

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


def I151_profile():
    recs = []
    for n, T, timeout in ((200, 1.5, 60), (2000, 1.5, 180), (3000, 1.5, 300)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser(path, T, 1, timeout=timeout)
        pp, c, tp = pith(path, T, 1, 1, "back", timeout=timeout)
        fid = compare(pr, pp, 1)
        c_probes = c.get("collapse_c_probes") or 0
        dom_tests = c.get("collapse_dom_tests") or 0
        dom_hits = c.get("collapse_dom_hits") or 0
        recs.append({
            "n": n, "T": T, "match": fid.get("exact_match_tol"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "edges_in": c.get("edges_in"),
            "edges_out": c.get("edges_out"),
            "c_probes": c_probes,
            "dom_tests": dom_tests,
            "dom_hits": dom_hits,
            "hit_rate": (dom_hits / dom_tests) if dom_tests else None,
            "probes_per_edge": (c_probes / c["edges_in"]) if c.get("edges_in") else None,
        })
        print(f"I151 n={n} match={recs[-1]['match']} collapse_ms={recs[-1]['collapse_ms']} "
              f"c_probes={c_probes} dom_tests={dom_tests} hits={dom_hits} "
              f"hit_rate={recs[-1]['hit_rate']}", flush=True)
    ok = all(r["match"] for r in recs)
    write({"id": "collapse_profile", "lever": "H01-profile", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "C-probe vs domination-test mix on circle T=1.5",
           "receipts": recs}, "I151")


def I152_forward_fix():
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
                    "pith_s": tp, "ripser_s": tr,
                    "time_ratio": tr / tp if tp else None,
                    "collapse_ms": c.get("collapse_ms"),
                    "edges_out": c.get("edges_out"),
                })
            except Exception as ex:
                recs.append({"dataset": name, "n": n, "alg": alg, "error": str(ex)[:300]})
            print(f"I152 {name} n={n} {alg} {recs[-1]}", flush=True)
    fwd = [r for r in recs if r.get("alg") == "forward" and "error" not in r]
    ok = all(r.get("match") for r in fwd)
    write({"id": "forward_grade_fix", "lever": "H01-fwd", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"forward at current grade {sum(1 for r in fwd if r.get('match'))}/{len(fwd)}",
           "receipts": recs}, "I152")


def main():
    I151_profile()
    I152_forward_fix()


if __name__ == "__main__":
    main()
