#!/usr/bin/env python3
"""I141–I144: select implicit default; retry budgeted collapse with implicit."""

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


def pith(path, T, dim, collapse=1, engine="auto", budget=-1, timeout=180):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--collapse", str(collapse), "--engine", engine, "--dom-budget", str(budget),
           "--no-enclosing"]
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I141_auto_default():
    recs = []
    for name, n, T, dim, coll in (
        ("circle_noisy", 80, 1.2, 1, 0),
        ("circle_noisy", 200, 1.2, 1, 1),
        ("torus", 200, 1.6, 1, 1),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, _ = ripser(path, T, dim)
        pp, c, dt = pith(path, T, dim, coll, "auto")
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "n": n, "collapse": coll,
                     "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched"),
                     "pipeline": c.get("pipeline"), "pith_s": dt})
        print(f"I141 {name} n={n} match={recs[-1]['match']} pipe={recs[-1]['pipeline']}", flush=True)
    ok = all(r["match"] for r in recs)
    write({"id": "auto_is_implicit", "lever": "H02-heap", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": f"auto=implicit identity {sum(r['match'] for r in recs)}/{len(recs)}",
           "receipts": recs}, "I141")


def I142_budget_implicit():
    recs = []
    path = BENCH / "datasets/generated/circle_noisy_n2000.csv"
    pr, tr = ripser(path, 1.5, 1, timeout=180)
    for budget, coll in ((-1, 1), (1, 1), (2, 1), (4, 1), (1, 0)):
        label_coll = coll
        try:
            pp, c, tp = pith(path, 1.5, 1, coll, "implicit", budget, timeout=180)
            fid = compare(pr, pp, 1)
            recs.append({
                "budget": budget, "collapse": label_coll,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr, "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
                "cols_apparent": c.get("cols_apparent"),
            })
        except Exception as ex:
            recs.append({"budget": budget, "collapse": coll, "error": str(ex)[:300]})
        print(f"I142 budget={budget} c={coll} {recs[-1]}", flush=True)
    ok = all(r.get("match") for r in recs if "error" not in r)
    best = max((r.get("time_ratio") or 0) for r in recs if "error" not in r)
    write({"id": "budget_implicit_circle2000", "lever": "H01-budget-implicit",
           "class": "experiment", "fidelity": "exact",
           "status": "support" if ok and best > 6.4 else ("support" if ok else "reject"),
           "summary": f"budget+implicit circle2000 best {best:.2f}× match={ok}",
           "receipts": recs}, "I142")
    return recs


def I143_dense_implicit():
    recs = []
    for n, T, timeout in ((200, 1.5, 60), (500, 1.5, 120), (1000, 1.5, 180)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "missing": True})
            continue
        pr, tr = ripser(path, T, 1, timeout=timeout)
        try:
            pp, c, tp = pith(path, T, 1, 0, "implicit", -1, timeout=timeout)
            fid = compare(pr, pp, 1)
            recs.append({
                "n": n, "T": T, "collapse": 0,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr, "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
                "cols_apparent": c.get("cols_apparent"),
            })
        except Exception as ex:
            recs.append({"n": n, "error": str(ex)[:300]})
        print(f"I143 n={n} {recs[-1]}", flush=True)
    write({"id": "dense_implicit_no_collapse", "lever": "H02-heap",
           "class": "experiment", "fidelity": "exact",
           "status": "support" if all(r.get("match") for r in recs if not r.get("missing") and "error" not in r) else "reject",
           "summary": "implicit on dense G_T (no collapse) vs Ripser",
           "receipts": recs}, "I143")


def I144_scale_if_budget_wins():
    recs = []
    for n, T, timeout in ((3000, 1.5, 300),):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "missing": True})
            continue
        pr, tr = ripser(path, T, 1, timeout=timeout)
        for budget in (-1, 1):
            try:
                pp, c, tp = pith(path, T, 1, 1, "implicit", budget, timeout=timeout)
                fid = compare(pr, pp, 1)
                recs.append({
                    "n": n, "budget": budget,
                    "match": fid.get("exact_match_tol"),
                    "unmatched": fid.get("unmatched"),
                    "ripser_s": tr, "pith_s": tp,
                    "time_ratio": tr / tp if tp else None,
                    "collapse_ms": c.get("collapse_ms"),
                    "reduce_ms": c.get("reduce_ms"),
                    "edges_out": c.get("edges_out"),
                })
            except Exception as ex:
                recs.append({"n": n, "budget": budget, "error": str(ex)[:300]})
            print(f"I144 n={n} budget={budget} {recs[-1]}", flush=True)
    write({"id": "budget_implicit_circle3000", "lever": "H01-budget-implicit",
           "class": "experiment", "fidelity": "exact",
           "status": "hold" if any(r.get("missing") for r in recs) else "support",
           "summary": "circle3000 budget+implicit vs full collapse",
           "receipts": recs}, "I144")


def main():
    I141_auto_default()
    I142_budget_implicit()
    I143_dense_implicit()
    I144_scale_if_budget_wins()


if __name__ == "__main__":
    main()
