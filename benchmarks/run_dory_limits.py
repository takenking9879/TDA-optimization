#!/usr/bin/env python3
"""Push Dory to first 12 s timeout on leftover / H2 families.

Same 1-thread, not-vendored oracle as reverify_dory.py. Budget matches
PRACTICAL_LIMITS.md (12 s). Stops a family after the first timeout.
Does not overwrite dory.json leftover receipts.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import circle_noisy, sphere, write_csv  # noqa: E402
from reverify_dory import IMPORT_ERR, pydory, run_dory, run_pith, run_ripser  # noqa: E402
from run_wave85 import figure8  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12


def main() -> int:
    if pydory is None:
        print("pydory not importable:", IMPORT_ERR, file=sys.stderr)
        return 2
    # Patch the leftover runner budget for this process (worker is a new process).
    import reverify_dory as rd

    rd.BUDGET_S = BUDGET_S
    rng = np.random.default_rng(14)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    series = [
        ("circle_noisy", 1.5, 1, [1500, 2000], lambda n: circle_noisy(n, rng)),
        ("figure8", 1.1, 1, [3000, 4000], lambda n: figure8(n, rng)),
        ("sphere", 1.4, 2, [600, 800], lambda n: sphere(n, rng)),
    ]
    rows = []
    first_fail = {}
    for name, T, maxdim, ns, maker in series:
        for n in ns:
            path = CLOUDS / f"dory_lim_{name}_n{n}.csv"
            write_csv(path, maker(n))
            prefix = OUT / "dory_out" / f"lim_{name}_n{n}"
            print(f"Dory limit {name} n={n} budget={BUDGET_S}s ...", flush=True)
            drec = run_dory(path, T, maxdim, prefix)
            print(
                f"  dory wall={drec.get('wall_s')} timeout={drec.get('timed_out')} "
                f"{drec.get('error') or ''}",
                flush=True,
            )
            prec = run_pith(path, T, maxdim)
            print(f"  pith wall={prec.get('wall_s')} timeout={prec.get('timed_out')}", flush=True)
            rrec = run_ripser(path, T, maxdim)
            print(f"  ripser wall={rrec.get('wall_s')} timeout={rrec.get('timed_out')}", flush=True)
            rec = {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "budget_s": BUDGET_S,
                "dory": drec,
                "pith": prec,
                "ripser": rrec,
                "threads": 1,
            }
            rows.append(rec)
            if (not drec.get("ok")) and name not in first_fail:
                first_fail[name] = {
                    "n": n,
                    "timed_out": bool(drec.get("timed_out")),
                    "error": drec.get("error"),
                }
                break
    payload = {
        "note": (
            "pydory 1.1.137 oracle, 1 thread, 12 s budget, not vendored. "
            "Stops a family after first Dory failure. Complements dory.json."
        ),
        "pydory_version": "1.1.137",
        "threads": 1,
        "budget_s": BUDGET_S,
        "first_fail": first_fail,
        "receipts": rows,
    }
    dest = OUT / "dory_limits.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    print("first_fail", json.dumps(first_fail))
    return 0


if __name__ == "__main__":
    os.environ["OMP_NUM_THREADS"] = "1"
    sys.exit(main())
