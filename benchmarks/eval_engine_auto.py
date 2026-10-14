#!/usr/bin/env python3
"""Live engine-oracle check on the frozen held-out pack.

Does not retune τ. Known misses are waived with a waste cap so a new
wrong pick, or a known miss getting much more expensive, fails.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    disconnected_circles,
    grid_holes,
    nested_loops,
    nonuniform_circle,
    random_geometric,
    two_spheres_apart,
)
from run_consolidation import run_estimate  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH  # noqa: E402
import numpy as np

OUT = BENCH / "results" / "consolidation"

# Frozen after phase-3. Do not expand to retune τ.
WAIVERS = {
    ("disconnected_circles", 400): {"max_waste": 2.0},
    ("disconnected_circles", 1000): {"max_waste": 2.0},
    ("two_spheres_apart", 300): {"max_waste": 4.0},
    ("nonuniform_circle", 400): {"max_waste": 2.5},
}

CASES = [
    ("disconnected_circles", disconnected_circles, 400, 1.5, 1),
    ("disconnected_circles", disconnected_circles, 1000, 1.5, 1),
    ("random_geometric_sparse", random_geometric, 500, 0.15, 1),
    ("random_geometric_dense", random_geometric, 400, 0.50, 1),
    ("grid_holes", grid_holes, 400, 0.12, 1),
    ("grid_holes", grid_holes, 800, 0.12, 1),
    ("two_spheres_apart", two_spheres_apart, 300, 1.4, 2),
    ("nonuniform_circle", nonuniform_circle, 400, 1.5, 1),
    ("nested_loops", nested_loops, 1000, 1.6, 1),
]


def stem(name: str) -> str:
    return name.replace("_sparse", "").replace("_dense", "")


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(3)
    recs = []
    new_misses = []
    over_cap = []
    for name, fn, n, T, dim in CASES:
        path = cloud(stem(name), n, fn, rng)
        est = run_estimate(path, T, dim, timeout=15)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=8)
        red = run_pith(path, T, dim, "exact", "redzed", threads=1, timeout=8)
        imp = run_pith(path, T, dim, "exact", "implicit", threads=1, timeout=8)
        finished = {}
        if red.get("ok") and red.get("wall_s"):
            finished["redzed"] = red["wall_s"]
        if imp.get("ok") and imp.get("wall_s"):
            finished["implicit"] = imp["wall_s"]
        oracle = min(finished, key=finished.get) if finished else None
        rec_e = est.get("engine_recommended")
        waste = None
        if oracle and rec_e in finished and finished[oracle]:
            waste = finished[rec_e] / finished[oracle]
        pipe = auto.get("pipeline") or ""
        picked = "redzed" if "redzed" in pipe else (
            "implicit" if "collapse" in pipe or "implicit" in pipe else pipe
        )
        wrong = bool(oracle and rec_e and rec_e != oracle)
        key = (name, n)
        waiver = WAIVERS.get(key)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "recommended": rec_e,
            "auto_picked": picked,
            "oracle_faster": oracle,
            "wrong": wrong,
            "waived": bool(waiver),
            "waste_if_follow_estimate": waste,
            "regime": est.get("residual_regime"),
            "times": {
                "auto": auto.get("wall_s"),
                "redzed": red.get("wall_s"),
                "implicit": imp.get("wall_s"),
            },
        }
        recs.append(rec)
        print(
            f"ENG {name} n={n} rec={rec_e} oracle={oracle} wrong={wrong} "
            f"waste={waste} waived={bool(waiver)}",
            flush=True,
        )
        if wrong and waiver is None:
            new_misses.append(rec)
        if wrong and waiver and waste is not None and waste > waiver["max_waste"]:
            over_cap.append(rec)

    n_wrong = sum(1 for r in recs if r["wrong"])
    n_ok = sum(1 for r in recs if not r["wrong"])
    OUT.mkdir(parents=True, exist_ok=True)
    out = {
        "receipts": recs,
        "n": len(recs),
        "n_oracle_ok": n_ok,
        "n_wrong": n_wrong,
        "new_misses": [f"{r['name']} n={r['n']}" for r in new_misses],
        "over_cap": [f"{r['name']} n={r['n']} waste={r['waste_if_follow_estimate']}" for r in over_cap],
        "note": "Known misses are waived. τ is frozen. Do not retune from this eval.",
    }
    path = OUT / "engine_auto.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} oracle {n_ok}/{len(recs)} new_misses={len(new_misses)} over_cap={len(over_cap)}")
    if new_misses or over_cap:
        print("engine oracle regression", new_misses, over_cap, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
