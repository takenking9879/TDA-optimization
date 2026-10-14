#!/usr/bin/env python3
"""Re-measure claimed ~10× exact H1 on leftover (non-collapse) families.

1-thread PITH --mode exact --engine auto vs 1-thread Ripser.
Does not retune τ. Empirical, not a Big-O claim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, figure8, sphere, torus, uniform  # noqa: E402
from run_consolidation import run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402
import numpy as np

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("blobs", blobs, 4000, 1.0, 1),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    recs = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        print(f"LEFTOVER {name} n={n} T={T}", flush=True)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=20)
        rip = run_ripser(path, T, dim, timeout=30)
        pw, rw = pith.get("wall_s"), rip.get("wall_s")
        ratio = (rw / pw) if pw and rw else None
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "pith_s": pw,
            "ripser_s": rw,
            "ratio": ratio,
            "pith_ok": pith.get("ok"),
            "ripser_ok": rip.get("ok"),
            "ripser_timeout": bool(rip.get("error") and "timed out" in str(rip.get("error")).lower()),
            "pipeline": pith.get("pipeline"),
            "reduce_ms": pith.get("reduce_ms"),
            "collapse_ms": pith.get("collapse_ms"),
            "residual_frac": pith.get("residual_frac"),
            "threads": 1,
        }
        recs.append(rec)
        print(
            f"  pith={pw} ripser={rw} ratio={ratio} pipe={rec['pipeline']} "
            f"reduce_ms={rec['reduce_ms']}",
            flush=True,
        )
    n_ge10 = sum(1 for r in recs if r.get("ratio") and r["ratio"] >= 10)
    n_ok = sum(1 for r in recs if r.get("pith_ok") and (r.get("ripser_ok") or r.get("ripser_timeout")))
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leftover_10x.json"
    path.write_text(
        json.dumps(
            {
                "receipts": recs,
                "n": len(recs),
                "n_pith_ok": n_ok,
                "n_ratio_ge10": n_ge10,
                "note": "1-thread exact auto vs Ripser on leftover-wall families. Not a Big-O claim.",
            },
            indent=2,
        )
    )
    print(f"wrote {path} {n_ge10}/{len(recs)} ≥10×")
    return 0 if all(r.get("pith_ok") for r in recs) else 1


if __name__ == "__main__":
    sys.exit(main())
