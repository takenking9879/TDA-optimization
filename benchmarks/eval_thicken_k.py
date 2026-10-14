#!/usr/bin/env python3
"""I334: per-vertex k-nearest thicken extras vs unlimited auto-α.

`--thicken-k K` keeps K nearest non-Delaunay extras inside the existing
α-ball. Default `--mode scale` is unchanged (K=0, unlimited). Not exact VR.
1 thread. τ frozen.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import figure8, torus, write_csv  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 40


def run_scale(path: Path, T: float, maxdim: int, k: int):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        "scale",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    if k > 0:
        cmd.extend(["--thicken-k", str(k)])
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    ess1 = sum(1 for p in pairs if p["dim"] == 1 and not np.isfinite(p["death"]))
    ess2 = sum(1 for p in pairs if p["dim"] == 2 and not np.isfinite(p["death"]))
    return {
        "ok": err is None,
        "error": err,
        "timed_out": err is not None and "timed out" in (err or "").lower(),
        "wall_s": None if err else dt,
        "pipeline": c.get("pipeline"),
        "n_vertices": c.get("n_vertices"),
        "edges_in": c.get("edges_in"),
        "distances": c.get("distances"),
        "metric_ms": c.get("metric_ms"),
        "ess1": ess1,
        "ess2": ess2,
        "n_pairs": len(pairs),
        "pairs": pairs,
        "threads_used": THREADS,
        "thicken_k": k,
    }


def main() -> int:
    rng = np.random.default_rng(34)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("figure8", 2000, 1.1, 1, [0, 16], lambda: figure8(2000, rng)),
        ("torus", 2000, 1.6, 1, [0, 16, 32], lambda: torus(2000, rng)),
        ("torus", 8000, 1.6, 1, [0, 16, 32], lambda: torus(8000, rng)),
    ]
    rows = []
    for name, n, T, maxdim, ks, maker in cases:
        path = CLOUDS / f"thickenk_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"thicken-k {name} n={n} ...", flush=True)
        recs = {}
        for k in ks:
            rec = run_scale(path, T, maxdim, k)
            recs[k] = rec
            print(
                f"  k={k} {rec.get('wall_s')} ess1={rec.get('ess1')} "
                f"edges={rec.get('edges_in')} metric={rec.get('metric_ms')} "
                f"{rec.get('pipeline')} {rec.get('error') or ''}",
                flush=True,
            )
        base = recs.get(0)
        for k, rec in recs.items():
            vs_base = None
            ratio = None
            if k != 0 and rec.get("ok") and base and base.get("ok"):
                vs_base = compare(rec["pairs"], base["pairs"], maxdim)
                if rec.get("wall_s") and base.get("wall_s"):
                    ratio = base["wall_s"] / rec["wall_s"]
            rows.append(
                {
                    "name": name,
                    "n": n,
                    "T": T,
                    "maxdim": maxdim,
                    "thicken_k": k,
                    "run": {kk: vv for kk, vv in rec.items() if kk != "pairs"},
                    "unlimited_over_k": ratio,
                    "unmatched_vs_unlimited": None
                    if vs_base is None
                    else vs_base.get("unmatched"),
                    "threads": THREADS,
                }
            )
    payload = {
        "note": (
            "I334 per-vertex k-nearest thicken extras vs unlimited auto-α. "
            "Not exact VR. Default --mode scale stays K=0 (unlimited). "
            "Named wall: 3D torus n=8000 maxdim=1 auto-α thicken."
        ),
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "thicken_k.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
