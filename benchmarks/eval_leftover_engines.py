#!/usr/bin/env python3
"""I315: leftover-miss engines. implicit (collapse+coh) vs RedZeD vs auto.

Does not retune τ. Does not touch leftover-coface skips.
1 thread. Exact VR: compare barcodes to Ripser when Ripser finishes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    anisotropic_blob,
    figure8,
    grid_holes,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER, compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
    ("grid_holes", grid_holes, 4000, 0.12, 1),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "runs": {}, "vs_ripser": {}, "ratio": {}}
        recs = {}
        for eng in ("auto", "redzed", "implicit"):
            rec = run_pith(path, T, dim, "exact", eng, threads=1, timeout=25)
            recs[eng] = rec
            row["runs"][eng] = strip_pairs(rec)
            print(
                f"{name} n={n} {eng}: ok={rec.get('ok')} wall={rec.get('wall_s')} "
                f"reduce={rec.get('reduce_ms')} pipe={rec.get('pipeline')} err={rec.get('error')}",
                flush=True,
            )
        rip = run_ripser(path, T, dim, timeout=30)
        recs["ripser"] = rip
        row["runs"]["ripser"] = strip_pairs(rip)
        rw = rip.get("wall_s")
        if rip.get("ok") and rip.get("pairs") is not None:
            for eng in ("auto", "redzed", "implicit"):
                rec = recs[eng]
                if rec.get("ok") and rec.get("pairs") is not None:
                    row["vs_ripser"][eng] = compare(rec["pairs"], rip["pairs"], dim)
                w = rec.get("wall_s")
                row["ratio"][eng] = (rw / w) if w and rw else None
        series.append(row)
        print(
            f"  ratios auto={row['ratio'].get('auto')} redzed={row['ratio'].get('redzed')} "
            f"implicit={row['ratio'].get('implicit')} ripser={rw}",
            flush=True,
        )

    unmatched = 0
    implicit_ge10 = 0
    auto_ge10 = 0
    implicit_wins = 0
    n_cmp = 0
    for row in series:
        for eng, cmp in row.get("vs_ripser", {}).items():
            unmatched += int(cmp.get("unmatched") or 0)
        if (row["ratio"].get("implicit") or 0) >= 10:
            implicit_ge10 += 1
        if (row["ratio"].get("auto") or 0) >= 10:
            auto_ge10 += 1
        ia, ra = row["runs"]["implicit"].get("wall_s"), row["runs"]["redzed"].get("wall_s")
        if ia and ra:
            n_cmp += 1
            if ia < ra:
                implicit_wins += 1

    out = {
        "note": "I315 leftover engines. τ frozen. 1 thread. Not a leftover-skip.",
        "unmatched_vs_ripser": unmatched,
        "auto_ge10": auto_ge10,
        "implicit_ge10": implicit_ge10,
        "implicit_faster_than_redzed": f"{implicit_wins}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leftover_engines.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"wrote {path} unmatched={unmatched} auto≥10 {auto_ge10} "
        f"implicit≥10 {implicit_ge10} implicit<redzed {implicit_wins}/{n_cmp}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
