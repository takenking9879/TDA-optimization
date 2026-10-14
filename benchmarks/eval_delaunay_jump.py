#!/usr/bin/env python3
"""I328: 3D nearest-vertex jump locate vs last-cavity walk.

`--delaunay-jump` starts the Bowyer–Watson walk at a tet incident to a
spatially nearby inserted vertex. Same Delaunay (exact) when it succeeds.
Default scale path unchanged. 1 thread. τ frozen.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import sphere, write_csv  # noqa: E402
from run_suite import PITH, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 40


def run_scale(path: Path, T: float, maxdim: int, jump: bool):
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
    if jump:
        cmd.append("--delaunay-jump")
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    import math

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
        "jump": jump,
        "threads_used": THREADS,
    }


def main() -> int:
    import numpy as np

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
        path = CLOUDS / f"deljump_{name}_n{n}.csv"
        write_csv(path, sphere(n, rng))
        print(f"delaunay-jump {name} n={n} ...", flush=True)
        base = run_scale(path, T, maxdim, False)
        print(
            f"  walk {base.get('wall_s')} ess2={base.get('ess2')} "
            f"edges={base.get('edges_in')} metric_ms={base.get('metric_ms')} {base.get('error') or ''}",
            flush=True,
        )
        jump = run_scale(path, T, maxdim, True)
        print(
            f"  jump {jump.get('wall_s')} ess2={jump.get('ess2')} "
            f"edges={jump.get('edges_in')} metric_ms={jump.get('metric_ms')} {jump.get('error') or ''}",
            flush=True,
        )
        ratio = None
        if base.get("ok") and jump.get("ok") and base.get("wall_s") and jump.get("wall_s"):
            ratio = base["wall_s"] / jump["wall_s"]
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "walk": base,
                "jump": jump,
                "walk_over_jump": ratio,
                "same_edges": (
                    base.get("ok")
                    and jump.get("ok")
                    and base.get("edges_in") == jump.get("edges_in")
                ),
                "same_ess2": base.get("ess2") == jump.get("ess2"),
                "threads": THREADS,
            }
        )
    payload = {
        "note": (
            "I328 3D nearest-vertex jump locate vs last-cavity walk. "
            "Same Delaunay when both succeed. Default --mode scale unchanged."
        ),
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "delaunay_jump.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
