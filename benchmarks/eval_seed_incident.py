#!/usr/bin/env python3
"""I325: skip non-Delaunay leftovers that do not touch an active vertex.

I323 skips non-Del when ActiveReg is empty. After keep_singleton, I323
still ae_prepare every leftover. H1 seeds only exist if a leftover
shares a vertex with an active. This path skips the rest. Never skips
ae_seeded on incident leftovers (I324/I272).
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


def run_flag(path: Path, T: float, maxdim: int, flag: str, timeout: float = 25):
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
        flag,
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
        "method": f"pith:{flag.lstrip('-')}",
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


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        inc = run_flag(path, T, dim, "--seed-incident")
        dsk = run_flag(path, T, dim, "--delaunay-skip")
        row = {
            "name": name,
            "n": n,
            "T": T,
            "auto": strip_pairs(auto),
            "seedinc": strip_pairs(inc),
            "delskip": strip_pairs(dsk),
            "vs_auto": {},
            "vs_ripser": {},
            "ratio": {},
        }
        if auto.get("ok") and auto.get("pairs") is not None and inc.get("ok") and inc.get(
            "pairs"
        ) is not None:
            row["vs_auto"] = compare(inc["pairs"], auto["pairs"], dim)
        aw, iw, dw = auto.get("wall_s"), inc.get("wall_s"), dsk.get("wall_s")
        row["ratio"]["inc_vs_auto"] = (aw / iw) if aw and iw else None
        row["ratio"]["inc_vs_delskip"] = (dw / iw) if dw and iw else None
        row["inc_faster_auto"] = bool(iw and aw and iw < aw)
        row["inc_faster_delskip"] = bool(iw and dw and iw < dw)
        if n <= 200:
            rip = run_ripser(path, T, dim, timeout=20)
            row["ripser"] = strip_pairs(rip)
            if rip.get("ok") and rip.get("pairs") is not None and inc.get("ok") and inc.get(
                "pairs"
            ) is not None:
                row["vs_ripser"]["seedinc"] = compare(inc["pairs"], rip["pairs"], dim)
        series.append(row)
        print(
            f"{name} n={n} auto={auto.get('wall_s')} inc={inc.get('wall_s')} "
            f"delskip={dsk.get('wall_s')} unmatched="
            f"{(row.get('vs_auto') or {}).get('unmatched')} "
            f"ae={inc.get('ae')} coface={inc.get('coface')} pipe={inc.get('pipeline')}",
            flush=True,
        )

    unmatched = sum(int((r.get("vs_auto") or {}).get("unmatched") or 0) for r in series)
    n_cmp = sum(
        1
        for r in series
        if r.get("auto", {}).get("wall_s") and r.get("seedinc", {}).get("wall_s")
    )
    faster = sum(1 for r in series if r.get("inc_faster_auto"))
    vs_dsk = sum(1 for r in series if r.get("inc_faster_delskip"))
    out = {
        "note": "I325 seed-incident non-Del skip. Exact if H1 seeds need a shared vertex. τ frozen.",
        "unmatched_vs_auto": unmatched,
        "inc_faster_than_auto": f"{faster}/{n_cmp}",
        "inc_faster_than_delskip": f"{vs_dsk}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "seed_incident.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched={unmatched} inc<auto {faster}/{n_cmp} inc<delskip {vs_dsk}/{n_cmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
