#!/usr/bin/env python3
"""I314: all-pairs RedZeD (--dense-metric) vs automatic spatial G_T.

Hypothesis: bbox volume marks elongated leftover-miss clouds as hollow
and the spatial build is the wall (anisotropic n=8000: 1.83 s wall /
0.42 s reduce). Forcing the dense metric should not change the barcode.
τ frozen. 1 thread. Not a leftover-coface skip.
"""

from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    anisotropic_blob,
    figure8,
    grid_holes,
    uniform,
    write_csv,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER, compare, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"


def run_dense(path, T, maxdim, timeout=25):
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
        "--threads",
        "1",
        "--dense-metric",
        "--no-enclosing",
    ]
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    return {
        "method": "pith:exact:redzed:dense",
        "ok": err is None,
        "error": err,
        "wall_s": None if err else dt,
        "reduce_ms": c.get("reduce_ms"),
        "metric_ms": c.get("metric_ms"),
        "pipeline": c.get("pipeline"),
        "ess1": sum(1 for p in pairs if p["dim"] == 1 and not math.isfinite(p["death"]))
        if pairs
        else None,
        "pairs": pairs,
        "counters": c,
    }


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    series = []
    for name, fn, T, ns in (
        ("anisotropic_blob", anisotropic_blob, 2.5, [2000, 4000, 6000, 8000]),
        ("grid_holes", grid_holes, 0.12, [1600, 4000, 8000]),
        ("figure8", figure8, 1.1, [2000]),
        ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, [2000]),
    ):
        for n in ns:
            path = cloud(name, n, fn, rng)
            est = subprocess.check_output(
                [
                    str(PITH),
                    "--estimate",
                    "--points",
                    str(path),
                    "--maxdim",
                    "1",
                    "--threshold",
                    str(T),
                    "--format",
                    "json",
                ],
                text=True,
            )
            est_js = json.loads(est)
            auto = run_pith(path, T, 1, "exact", "auto", threads=1, timeout=25)
            dense = run_dense(path, T, 1, timeout=25)
            rip = run_ripser(path, T, 1, timeout=25)
            row = {
                "name": name,
                "n": n,
                "T": T,
                "estimate": {
                    k: est_js.get(k)
                    for k in (
                        "edge_frac_probe",
                        "residual_frac",
                        "residual_regime",
                        "engine_recommended",
                        "est_edges",
                    )
                },
                "auto": strip_pairs(auto),
                "dense": strip_pairs(dense),
                "ripser": strip_pairs(rip),
            }
            if auto.get("ok") and dense.get("ok"):
                row["unmatched_auto_dense"] = compare(auto["pairs"], dense["pairs"], 1).get(
                    "unmatched"
                )
            aw, dw, rw = auto.get("wall_s"), dense.get("wall_s"), rip.get("wall_s")
            row["ratio_auto"] = (rw / aw) if aw and rw else None
            row["ratio_dense"] = (rw / dw) if dw and rw else None
            series.append(row)
            print(
                f"{name} n={n} edge_frac={est_js.get('edge_frac_probe')} "
                f"auto={aw} {auto.get('pipeline')} dense={dw} {dense.get('pipeline')} "
                f"ripser={rw} ratio_auto={row['ratio_auto']} ratio_dense={row['ratio_dense']}",
                flush=True,
            )

    n_ge10_auto = sum(1 for r in series if r.get("ratio_auto") and r["ratio_auto"] >= 10)
    n_ge10_dense = sum(1 for r in series if r.get("ratio_dense") and r["ratio_dense"] >= 10)
    unmatched = sum(int(r.get("unmatched_auto_dense") or 0) for r in series)
    out = {
        "note": "I314 dense-metric vs spatial. τ frozen. 1 thread.",
        "n": len(series),
        "unmatched_auto_dense": unmatched,
        "n_ratio_ge10_auto": n_ge10_auto,
        "n_ratio_ge10_dense": n_ge10_dense,
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "dense_metric.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched={unmatched} ge10 auto={n_ge10_auto} dense={n_ge10_dense}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
