#!/usr/bin/env python3
"""I320: SparseDist+EdgeList on finite-T dense G_T (no collapse).

Same VR≤T as lower-tri RedZeD. I319 reduce was ~2.4× on this
representation; Graph+collapse hid the wall. 1 thread. τ frozen.
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
    blobs,
    figure8,
    grid_holes,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("blobs", blobs, 4000, 1.0, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
    ("grid_holes", grid_holes, 4000, 0.12, 1),
]


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        rip = run_ripser(path, T, dim, timeout=30)
        row = {
            "name": name,
            "n": n,
            "T": T,
            "auto": strip_pairs(auto),
            "ripser": strip_pairs(rip),
            "vs_ripser": {},
            "ratio": {},
        }
        if rip.get("ok") and rip.get("pairs") is not None:
            if auto.get("ok") and auto.get("pairs") is not None:
                row["vs_ripser"]["auto"] = compare(auto["pairs"], rip["pairs"], dim)
            rw, aw = rip.get("wall_s"), auto.get("wall_s")
            row["ratio"]["auto"] = (rw / aw) if rw and aw else None
        series.append(row)
        print(
            f"{name} n={n} pipe={auto.get('pipeline')} wall={auto.get('wall_s')} "
            f"reduce={auto.get('reduce_ms')} e={auto.get('n_edges_in')} "
            f"rip={rip.get('wall_s')} ratio={row['ratio'].get('auto')} "
            f"unmatched={(row.get('vs_ripser', {}).get('auto') or {}).get('unmatched')}",
            flush=True,
        )

    unmatched = sum(int((r.get("vs_ripser") or {}).get("auto", {}).get("unmatched") or 0) for r in series)
    ge10 = sum(1 for r in series if (r.get("ratio") or {}).get("auto") and r["ratio"]["auto"] >= 10)
    out = {
        "note": "I320 sparse G_T RedZeD (no collapse). Exact VR≤T. τ frozen.",
        "unmatched_vs_ripser": unmatched,
        "auto_ge10": f"{ge10}/{len(series)}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "sparsegt.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched={unmatched} ge10={ge10}/{len(series)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
