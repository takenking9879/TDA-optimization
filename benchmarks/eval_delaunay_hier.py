#!/usr/bin/env python3
"""I329: 2-level 3D Delaunay hierarchy vs Morton + last-cavity walk.

`--delaunay-hier` inserts every 16th Morton point first, then locates
later points from the nearest landmark's incident tet. Same Delaunay
when it succeeds. Default scale path unchanged. 1 thread. τ frozen.
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import sphere, write_csv  # noqa: E402
from run_suite import PITH, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 40


def run_scale(path: Path, T: float, maxdim: int, hier: bool):
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
    if hier:
        cmd.append("--delaunay-hier")
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    ess2 = sum(1 for p in pairs if p["dim"] == 2 and not math.isfinite(p["death"]))
    return {
        "ok": err is None,
        "error": err,
        "timed_out": err is not None and "timed out" in (err or "").lower(),
        "wall_s": None if err else dt,
        "pipeline": c.get("pipeline"),
        "edges_in": c.get("edges_in"),
        "metric_ms": c.get("metric_ms"),
        "ess2": ess2,
        "n_pairs": len(pairs),
        "hier": hier,
        "threads_used": THREADS,
    }


def main() -> int:
    rng = np.random.default_rng(28)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("sphere", 2000, 1.4, 2),
        ("sphere", 8000, 1.4, 2),
        ("sphere", 16000, 1.4, 2),
        ("sphere", 30000, 1.4, 2),
        ("sphere", 80000, 1.4, 2),
    ]
    rows = []
    for name, n, T, maxdim in cases:
        path = CLOUDS / f"delhier_{name}_n{n}.csv"
        write_csv(path, sphere(n, rng))
        print(f"delaunay-hier {name} n={n} ...", flush=True)
        base = run_scale(path, T, maxdim, False)
        print(
            f"  walk {base.get('wall_s')} ess2={base.get('ess2')} "
            f"edges={base.get('edges_in')} metric_ms={base.get('metric_ms')} {base.get('error') or ''}",
            flush=True,
        )
        hier = run_scale(path, T, maxdim, True)
        print(
            f"  hier {hier.get('wall_s')} ess2={hier.get('ess2')} "
            f"edges={hier.get('edges_in')} metric_ms={hier.get('metric_ms')} {hier.get('error') or ''}",
            flush=True,
        )
        ratio = None
        if base.get("ok") and hier.get("ok") and base.get("wall_s") and hier.get("wall_s"):
            ratio = base["wall_s"] / hier["wall_s"]
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "walk": base,
                "hier": hier,
                "walk_over_hier": ratio,
                "same_edges": (
                    base.get("ok")
                    and hier.get("ok")
                    and base.get("edges_in") == hier.get("edges_in")
                ),
                "same_ess2": base.get("ess2") == hier.get("ess2"),
                "threads": THREADS,
            }
        )
    payload = {
        "note": (
            "I329 2-level Devillers-lite (Morton subsample first, then "
            "nearest-landmark walk) vs last-cavity hint. Same Delaunay "
            "when both succeed. Default --mode scale unchanged."
        ),
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "delaunay_hier.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
