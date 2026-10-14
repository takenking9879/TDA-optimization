#!/usr/bin/env python3
"""I322: k-NN witness mark of leftover_coface successes (exact subset).

After Kruskal leftover identification, mark leftovers that are a k-NN
triangle (k=12) with max(d(wu),d(wv))≤t_uv and coface_ready.
leftover_coface only runs on unmarked leftovers.
Marks at most n·C(k,2) leftovers. On a fat leftover G_T that is o(|L|).
1 thread. τ frozen. Default auto is unchanged.
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


def run_knn_mark(path: Path, T: float, maxdim: int, timeout: float = 25):
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
        "--knn-mark",
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
    timed_out = err is not None and "timed out" in (err or "").lower()
    leftover = c.get("cols_assembled") if c else None
    marked = c.get("cols_cleared") if c else None
    return {
        "method": "pith:knn-mark",
        "ok": err is None,
        "error": err,
        "timed_out": timed_out,
        "wall_s": None if err else dt,
        "reduce_ms": c.get("reduce_ms") if c else None,
        "metric_ms": c.get("metric_ms") if c else None,
        "n_edges_in": c.get("edges_in") if c else None,
        "pipeline": c.get("pipeline") if c else None,
        "leftover": leftover,
        "empty_skip": c.get("cols_apparent") if c else None,
        "knn_mark": marked,
        "coface": c.get("cofacet_probes") if c else None,
        "ae": c.get("cols_reduced") if c else None,
        "cover": (marked / leftover) if leftover and marked is not None else None,
        "n_pairs": len(pairs) if pairs else 0,
        "pairs": pairs,
    }


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        auto = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        knn = run_knn_mark(path, T, dim)
        row = {
            "name": name,
            "n": n,
            "T": T,
            "auto": strip_pairs(auto),
            "knn_mark": strip_pairs(knn),
            "vs_auto": {},
            "vs_ripser": {},
            "ratio": {},
        }
        if auto.get("ok") and auto.get("pairs") is not None and knn.get("ok") and knn.get(
            "pairs"
        ) is not None:
            row["vs_auto"] = compare(knn["pairs"], auto["pairs"], dim)
        aw, kw = auto.get("wall_s"), knn.get("wall_s")
        row["ratio"]["knn_vs_auto"] = (aw / kw) if aw and kw else None
        row["knn_faster"] = bool(kw and aw and kw < aw)
        if n <= 200:
            rip = run_ripser(path, T, dim, timeout=20)
            row["ripser"] = strip_pairs(rip)
            if rip.get("ok") and rip.get("pairs") is not None:
                if knn.get("ok") and knn.get("pairs") is not None:
                    row["vs_ripser"]["knn_mark"] = compare(knn["pairs"], rip["pairs"], dim)
                if auto.get("ok") and auto.get("pairs") is not None:
                    row["vs_ripser"]["auto"] = compare(auto["pairs"], rip["pairs"], dim)
                rw = rip.get("wall_s")
                row["ratio"]["auto"] = (rw / aw) if rw and aw else None
                row["ratio"]["knn_mark"] = (rw / kw) if rw and kw else None
        series.append(row)
        ac = auto.get("counters") or {}
        print(
            f"{name} n={n} auto={auto.get('wall_s')} knn={knn.get('wall_s')} "
            f"faster={row['knn_faster']} unmatched_auto="
            f"{(row.get('vs_auto') or {}).get('unmatched')} "
            f"cover={knn.get('cover')} leftover={knn.get('leftover')} "
            f"coface={knn.get('coface')} vs_auto_coface="
            f"{ac.get('cofacet_probes')} pipe={knn.get('pipeline')}",
            flush=True,
        )

    unmatched = sum(int((r.get("vs_auto") or {}).get("unmatched") or 0) for r in series)
    unmatched_rip = sum(
        int((r.get("vs_ripser") or {}).get("knn_mark", {}).get("unmatched") or 0) for r in series
    )
    n_cmp = sum(1 for r in series if r.get("auto", {}).get("wall_s") and r.get("knn_mark", {}).get("wall_s"))
    faster = sum(1 for r in series if r.get("knn_faster"))
    out = {
        "note": "I322 k-NN leftover mark (k=12). Exact subset of leftover_coface. τ frozen.",
        "unmatched_vs_auto": unmatched,
        "unmatched_vs_ripser": unmatched_rip,
        "knn_faster_than_auto": f"{faster}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "knn_mark.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched_auto={unmatched} unmatched_rip={unmatched_rip} knn<auto {faster}/{n_cmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
