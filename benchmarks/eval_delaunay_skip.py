#!/usr/bin/env python3
"""I323: empty-seed non-Delaunay leftover skip without ae_prepare.

I273 was exact but measured on figure8 (ae_seeded wall). I321 showed
leftover-miss is leftover_coface on |E|. This path skips prepare+coface
when ActiveReg is empty and the leftover is not a Delaunay edge.
Never skips ae_seeded (I272). Euclidean d∈{2,3} only.
1 thread. τ frozen. Default auto unchanged.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    anisotropic_blob,
    figure8,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 200, 1.1, 1),
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
]


def run_delskip(path: Path, T: float, maxdim: int, timeout: float = 25):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        "exact",
        "--engine",
        "redzed",
        "--delaunay-skip",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    leftover = c.get("cols_assembled") if c else None
    skipped = c.get("cols_cleared") if c else None
    return {
        "method": "pith:delaunay-skip",
        "ok": err is None,
        "error": err,
        "timed_out": err is not None and "timed out" in (err or "").lower(),
        "wall_s": None if err else dt,
        "reduce_ms": c.get("reduce_ms") if c else None,
        "pipeline": c.get("pipeline") if c else None,
        "leftover": leftover,
        "empty_skip": c.get("cols_apparent") if c else None,
        "del_skip": skipped,
        "coface": c.get("cofacet_probes") if c else None,
        "ae": c.get("cols_reduced") if c else None,
        "cover": (skipped / leftover) if leftover and skipped is not None else None,
        "n_pairs": len(pairs) if pairs else 0,
        "pairs": pairs,
    }


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        skip = run_delskip(path, T, dim)
        row = {
            "name": name,
            "n": n,
            "T": T,
            "auto": strip_pairs(auto),
            "delskip": strip_pairs(skip),
            "vs_auto": {},
            "vs_ripser": {},
            "ratio": {},
        }
        if auto.get("ok") and auto.get("pairs") is not None and skip.get("ok") and skip.get(
            "pairs"
        ) is not None:
            row["vs_auto"] = compare(skip["pairs"], auto["pairs"], dim)
        aw, sw = auto.get("wall_s"), skip.get("wall_s")
        row["ratio"]["skip_vs_auto"] = (aw / sw) if aw and sw else None
        row["skip_faster"] = bool(sw and aw and sw < aw)
        if n <= 200:
            rip = run_ripser(path, T, dim, timeout=20)
            row["ripser"] = strip_pairs(rip)
            if rip.get("ok") and rip.get("pairs") is not None:
                if skip.get("ok") and skip.get("pairs") is not None:
                    row["vs_ripser"]["delskip"] = compare(skip["pairs"], rip["pairs"], dim)
                rw = rip.get("wall_s")
                row["ratio"]["delskip"] = (rw / sw) if rw and sw else None
        series.append(row)
        print(
            f"{name} n={n} auto={auto.get('wall_s')} skip={skip.get('wall_s')} "
            f"faster={row['skip_faster']} unmatched="
            f"{(row.get('vs_auto') or {}).get('unmatched')} "
            f"cover={skip.get('cover')} leftover={skip.get('leftover')} "
            f"coface={skip.get('coface')} pipe={skip.get('pipeline')}",
            flush=True,
        )

    unmatched = sum(int((r.get("vs_auto") or {}).get("unmatched") or 0) for r in series)
    unmatched_rip = sum(
        int((r.get("vs_ripser") or {}).get("delskip", {}).get("unmatched") or 0) for r in series
    )
    n_cmp = sum(
        1
        for r in series
        if r.get("auto", {}).get("wall_s") and r.get("delskip", {}).get("wall_s")
    )
    faster = sum(1 for r in series if r.get("skip_faster"))
    out = {
        "note": "I323 empty-seed non-Delaunay skip, no prepare when act empty. τ frozen.",
        "unmatched_vs_auto": unmatched,
        "unmatched_vs_ripser": unmatched_rip,
        "skip_faster_than_auto": f"{faster}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "delaunay_skip.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"wrote {path} unmatched_auto={unmatched} unmatched_rip={unmatched_rip} "
        f"skip<auto {faster}/{n_cmp}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
