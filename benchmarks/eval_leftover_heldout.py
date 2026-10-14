#!/usr/bin/env python3
"""Held-out leftover H1 ratio vs Ripser.

Families are not in leftover_10x.json (figure8 / torus / uniform2 /
sphere / blobs). Seed 19. Does not retune τ or edit leftover skips.
1 thread. Empirical.
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
    disconnected_circles,
    grid_holes,
    loops_with_bridges,
    many_loops,
    multi_scale_loops,
    nested_loops,
    nonuniform_circle,
)
from run_consolidation import run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402

OUT = BENCH / "results" / "consolidation"
TAU_H1 = 0.04

CASES = [
    ("nested_loops", nested_loops, 1000, 1.6, 1),
    ("nested_loops", nested_loops, 2000, 1.6, 1),
    ("loops_with_bridges", loops_with_bridges, 1000, 1.3, 1),
    ("loops_with_bridges", loops_with_bridges, 2000, 1.3, 1),
    ("many_loops", many_loops, 1000, 1.2, 1),
    ("many_loops", many_loops, 2000, 1.2, 1),
    ("disconnected_circles", disconnected_circles, 1000, 1.5, 1),
    ("disconnected_circles", disconnected_circles, 2000, 1.5, 1),
    ("nonuniform_circle", nonuniform_circle, 1000, 1.5, 1),
    ("anisotropic_blob", anisotropic_blob, 2000, 2.5, 1),
    ("grid_holes", grid_holes, 1600, 0.12, 1),
    ("multi_scale_loops", multi_scale_loops, 1000, 2.8, 1),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(19)
    recs = []
    for name, fn, n, T, dim in CASES:
        path = cloud(f"heldout_{name}", n, fn, rng)
        print(f"HELDOUT {name} n={n}", flush=True)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=20)
        rip = run_ripser(path, T, dim, timeout=30)
        pw, rw = pith.get("wall_s"), rip.get("wall_s")
        ratio = (rw / pw) if pw and rw else None
        resid = pith.get("residual_frac")
        collapse_wall = (
            resid is not None and resid >= 0 and resid <= TAU_H1
            and "collapse" in str(pith.get("pipeline") or "")
        )
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "pith_s": pw,
            "ripser_s": rw,
            "ratio": ratio,
            "pith_ok": pith.get("ok"),
            "ripser_ok": rip.get("ok"),
            "ripser_timeout": bool(
                rip.get("error") and "timed out" in str(rip.get("error")).lower()
            ),
            "pipeline": pith.get("pipeline"),
            "reduce_ms": pith.get("reduce_ms"),
            "collapse_ms": pith.get("collapse_ms"),
            "residual_frac": resid,
            "collapse_wall": collapse_wall,
            "threads": 1,
        }
        recs.append(rec)
        print(
            f"  pith={pw} ripser={rw} ratio={ratio} pipe={rec['pipeline']} "
            f"resid={resid} collapse_wall={collapse_wall}",
            flush=True,
        )
    leftover = [r for r in recs if r.get("pith_ok") and not r.get("collapse_wall") and r.get("ratio")]
    collapse = [r for r in recs if r.get("collapse_wall") and r.get("ratio")]
    n_ge10 = sum(1 for r in leftover if r["ratio"] >= 10)
    out = {
        "note": (
            "Seed 19. Families outside leftover_10x.json. "
            "collapse_wall = residual_frac≤τ=0.04 and collapse pipeline. "
            "n_ratio_ge10 counts leftover walls only. τ frozen."
        ),
        "n": len(recs),
        "n_leftover": len(leftover),
        "n_collapse": len(collapse),
        "n_ratio_ge10": n_ge10,
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leftover_heldout.json"
    path.write_text(json.dumps(out, indent=2))
    print(
        f"wrote {path} leftover ≥10× {n_ge10}/{len(leftover)} "
        f"(collapse cells {len(collapse)})",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
