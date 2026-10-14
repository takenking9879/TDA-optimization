#!/usr/bin/env python3
"""I206: Sheehy sparse=0.5 simplex-count log-log slope vs n."""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import RESULTS  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def loglog_slope(xs, ys):
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
    import gudhi

    recs = []
    families = [
        ("circle_noisy", [500, 1000, 1500], 1.5),
        ("blobs", [500, 1000, 1500], 1.0),
        ("sphere", [500, 1000, 1500], 1.4),
        ("torus", [500, 1000, 1500], 1.6),
        ("uniform2", [500, 1000, 1500], 0.35),
    ]
    for name, ns, T in families:
        for n in ns:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            pts = np.loadtxt(path, delimiter=",")
            t0 = time.perf_counter()
            st = gudhi.RipsComplex(points=pts, max_edge_length=T, sparse=0.5).create_simplex_tree(
                max_dimension=2
            )
            nsim = int(st.num_simplices())
            dt = time.perf_counter() - t0
            rec = {"name": name, "n": n, "T": T, "sparse_simplices": nsim, "sparse_s": dt}
            print(f"I206 {rec}", flush=True)
            recs.append(rec)

    slopes = {}
    for name, ns, T in families:
        rows = [r for r in recs if r["name"] == name]
        xs = [r["n"] for r in rows]
        slopes[name] = {
            "slope_simplices": loglog_slope(xs, [r["sparse_simplices"] for r in rows]),
            "slope_time": loglog_slope(xs, [r["sparse_s"] for r in rows]),
            "simplices": [r["sparse_simplices"] for r in rows],
        }
        print(f"I206 slope {name} {slopes[name]}", flush=True)

    sim_slopes = [v["slope_simplices"] for v in slopes.values() if v["slope_simplices"] is not None]
    all_subquad = bool(sim_slopes) and all(s < 1.6 for s in sim_slopes)
    write({
        "id": "sheehy_size_scaling",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if all_subquad else "partial",
        "summary": "I206 Sheehy sparse=0.5 simplex-count vs n",
        "receipts": recs,
        "slopes": slopes,
        "all_subquadratic_size": all_subquad,
    }, "I206")


if __name__ == "__main__":
    main()
