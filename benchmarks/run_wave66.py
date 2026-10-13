#!/usr/bin/env python3
"""I204: residual |E'(n)| and wall-clock log-log slopes across shapes.

Shape-agnostic Big-O evidence: same default path, several homology types,
fixed T per family. Does not change the algorithm.
"""

from __future__ import annotations

import json
import math
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


def pith_cmd(path, T, timeout=240):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing",
         "--collapse-alg", "back"],
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


def loglog_slope(xs, ys):
    """Least-squares slope of log y vs log x. None if <2 finite points."""
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x and y and x > 0 and y > 0]
    if len(pts) < 2:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den <= 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


def main():
    recs = []
    families = [
        ("circle_noisy", [500, 1000, 1500, 2000], 1.5),
        ("blobs", [500, 1000, 1500, 2000], 1.0),
        ("sphere", [500, 1000, 1500, 2000], 1.4),
        ("torus", [500, 1000, 1500, 2000], 1.6),
        ("uniform2", [500, 1000, 1500, 2000], 0.35),
    ]
    extra = [
        ("figure8", 500, 1.0),
        ("two_circles", 400, 1.2),
        ("annulus", 300, 1.2),
        ("swiss", 400, 1.4),
        ("blobs3d", 400, 1.2),
    ]
    for name, ns, T in families:
        for n in ns:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            if not path.exists():
                print(f"missing {path}", flush=True)
                continue
            rto = 180 if (name == "circle_noisy" and n >= 1500) else 90
            ps, cs, ts = pith_cmd(path, T, 180)
            pr, tr = ripser(path, T, rto)
            fidr = compare(pr, ps, 1)
            rec = {
                "name": name, "n": n, "T": T, "kind": "scale",
                "match_ripser": fidr.get("exact_match_tol"),
                "unmatched_ripser": fidr.get("unmatched"),
                "pith_s": ts, "ripser_s": tr,
                "vs_ripser": tr / ts if ts else None,
                "edges_in": cs.get("edges_in"),
                "edges_out": cs.get("edges_out"),
                "collapse_ms": cs.get("collapse_ms"),
                "reduce_ms": cs.get("reduce_ms"),
                "cols_reduced": cs.get("cols_reduced"),
                "cols_apparent": cs.get("cols_apparent"),
            }
            print(f"I204 {rec}", flush=True)
            recs.append(rec)

    for name, n, T in extra:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        ps, cs, ts = pith_cmd(path, T, 90)
        pr, tr = ripser(path, T, 60)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T, "kind": "extra-shape",
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "pith_s": ts, "ripser_s": tr,
            "vs_ripser": tr / ts if ts else None,
            "edges_in": cs.get("edges_in"),
            "edges_out": cs.get("edges_out"),
            "collapse_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
        }
        print(f"I204 extra {rec}", flush=True)
        recs.append(rec)

    slopes = {}
    for name, ns, T in families:
        rows = [r for r in recs if r["name"] == name and r.get("kind") == "scale"]
        if len(rows) < 2:
            continue
        xs = [r["n"] for r in rows]
        slopes[name] = {
            "T": T,
            "n": xs,
            "edges_in": [r.get("edges_in") for r in rows],
            "edges_out": [r.get("edges_out") for r in rows],
            "slope_edges_in": loglog_slope(xs, [r.get("edges_in") or 0 for r in rows]),
            "slope_edges_out": loglog_slope(xs, [r.get("edges_out") or 0 for r in rows]),
            "slope_collapse_ms": loglog_slope(xs, [r.get("collapse_ms") or 0 for r in rows]),
            "slope_pith_s": loglog_slope(xs, [r.get("pith_s") or 0 for r in rows]),
            "slope_ripser_s": loglog_slope(xs, [r.get("ripser_s") or 0 for r in rows]),
            "residual_frac": [
                (r.get("edges_out") or 0) / max(1, r.get("edges_in") or 1) for r in rows
            ],
        }
        print(f"I204 slope {name} {slopes[name]}", flush=True)

    ident = all(r.get("match_ripser") for r in recs) if recs else False
    # Better residual Big-O: residual slope clearly below ~2 (dense G_T) on
    # every scaled family, not only circle.
    out_slopes = [v.get("slope_edges_out") for v in slopes.values() if v.get("slope_edges_out") is not None]
    all_subquadratic = bool(out_slopes) and all(s < 1.6 for s in out_slopes)
    write({
        "id": "residual_scaling_shape_agnostic",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if ident and all_subquadratic else (
            "partial" if ident else "reject"
        ),
        "summary": "I204 residual |E'(n)| log-log slopes across shapes",
        "receipts": recs,
        "slopes": slopes,
        "all_subquadratic_residual": all_subquadratic,
        "topology_loss": "0 unmatched bars vs Ripser on every measured family"
                         if ident else "unverified",
    }, "I204")


if __name__ == "__main__":
    main()
