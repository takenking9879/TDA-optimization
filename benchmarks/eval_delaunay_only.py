#!/usr/bin/env python3
"""I324: pair only leftover ∩ Delaunay (skip ae_seeded on non-Delaunay).

I323 still walks |E| leftovers after the first keep_singleton so AE can
run. This path never processes non-Delaunay leftovers. I272 says that
invents bars. Identity first; leftover-miss wall only if exact.
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

ID_CASES = [
    ("figure8", figure8, 200, 1.1, 1),
    ("figure8", figure8, 2000, 1.1, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("torus", torus, 2000, 1.6, 1),
]

WALL_CASES = [
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
]


def run_delonly(path: Path, T: float, maxdim: int, timeout: float = 25):
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
        "--delaunay-only",
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
        "method": "pith:delaunay-only",
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
        "n_pairs": len(pairs) if pairs else 0,
        "pairs": pairs,
    }


def run_cases(cases, rng, vs_rip_n=200):
    series = []
    unmatched = 0
    for name, fn, n, T, dim in cases:
        path = cloud(name, n, fn, rng)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        only = run_delonly(path, T, dim)
        row = {
            "name": name,
            "n": n,
            "T": T,
            "auto": strip_pairs(auto),
            "delonly": strip_pairs(only),
            "vs_auto": {},
            "vs_ripser": {},
            "ratio": {},
        }
        if auto.get("ok") and auto.get("pairs") is not None and only.get("ok") and only.get(
            "pairs"
        ) is not None:
            row["vs_auto"] = compare(only["pairs"], auto["pairs"], dim)
            unmatched += int(row["vs_auto"].get("unmatched") or 0)
        aw, ow = auto.get("wall_s"), only.get("wall_s")
        row["ratio"]["only_vs_auto"] = (aw / ow) if aw and ow else None
        row["only_faster"] = bool(ow and aw and ow < aw)
        if n <= vs_rip_n:
            rip = run_ripser(path, T, dim, timeout=20)
            row["ripser"] = strip_pairs(rip)
            if rip.get("ok") and rip.get("pairs") is not None and only.get("ok") and only.get(
                "pairs"
            ) is not None:
                row["vs_ripser"]["delonly"] = compare(only["pairs"], rip["pairs"], dim)
        series.append(row)
        print(
            f"{name} n={n} auto={auto.get('wall_s')} only={only.get('wall_s')} "
            f"unmatched={(row.get('vs_auto') or {}).get('unmatched')} "
            f"ae={only.get('ae')} coface={only.get('coface')} "
            f"pipe={only.get('pipeline')}",
            flush=True,
        )
    return series, unmatched


def main() -> int:
    rng = np.random.default_rng(0)
    id_series, id_un = run_cases(ID_CASES, rng)
    wall_series, wall_un = [], 0
    if id_un == 0:
        wall_series, wall_un = run_cases(WALL_CASES, rng, vs_rip_n=0)
    else:
        print(f"identity failed unmatched={id_un}; skip leftover-miss wall", flush=True)

    series = id_series + wall_series
    unmatched = id_un + wall_un
    n_cmp = sum(
        1
        for r in series
        if r.get("auto", {}).get("wall_s") and r.get("delonly", {}).get("wall_s")
    )
    faster = sum(1 for r in series if r.get("only_faster"))
    out = {
        "note": "I324 leftover∩Delaunay only (skips ae_seeded on non-Del). τ frozen.",
        "unmatched_vs_auto": unmatched,
        "identity_unmatched": id_un,
        "only_faster_than_auto": f"{faster}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "delaunay_only.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched_auto={unmatched} identity={id_un} only<auto {faster}/{n_cmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
