#!/usr/bin/env python3
"""I319: same G_T as auto RedZeD + sparse young-cap (no DenseTimes).

I317/I318 paid an extra pairwise Graph + DenseTimes n² that auto does not.
This path uses persist_redzed_from_points_young_cap: spatial or lower-tri
G_T, I156 fast-trim only on neighbor lists, RedZeD AE on the residual.
Fast-trim-only is a subset of legal flag-edge trims ⇒ exact VR.
1 thread. τ frozen.
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
    grid_holes,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, compare, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("grid_holes", grid_holes, 4000, 0.12, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
]

KEEPS = (4096, 16384, 65536)


def run_young_fair(path: Path, T: float, maxdim: int, keep: int, timeout: float = 25):
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
        "collapse-redzed",
        "--collapse-alg",
        "young-cap",
        "--suffix-keep",
        str(keep),
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
    return {
        "method": f"pith:young-cap-fair-{keep}",
        "ok": err is None,
        "error": err,
        "timed_out": timed_out,
        "wall_s": None if err else dt,
        "collapse_ms": c.get("collapse_ms") if c else None,
        "reduce_ms": c.get("reduce_ms") if c else None,
        "metric_ms": c.get("metric_ms") if c else None,
        "n_edges_in": c.get("edges_in") if c else None,
        "n_edges_out": c.get("edges_out") if c else None,
        "pipeline": c.get("pipeline") if c else None,
        "n_pairs": len(pairs) if pairs else 0,
        "pairs": pairs,
    }


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "runs": {}, "vs_ripser": {}, "ratio": {}}
        recs = {}
        recs["auto"] = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        row["runs"]["auto"] = strip_pairs(recs["auto"])
        print(
            f"{name} n={n} auto: ok={recs['auto'].get('ok')} wall={recs['auto'].get('wall_s')} "
            f"reduce={recs['auto'].get('reduce_ms')} pipe={recs['auto'].get('pipeline')}",
            flush=True,
        )
        for keep in KEEPS:
            key = f"young{keep}"
            recs[key] = run_young_fair(path, T, dim, keep)
            row["runs"][key] = strip_pairs(recs[key])
            print(
                f"{name} n={n} young-fair-{keep}: ok={recs[key].get('ok')} "
                f"wall={recs[key].get('wall_s')} collapse={recs[key].get('collapse_ms')} "
                f"reduce={recs[key].get('reduce_ms')} "
                f"e={recs[key].get('n_edges_in')}->{recs[key].get('n_edges_out')} "
                f"pipe={recs[key].get('pipeline')} err={recs[key].get('error')}",
                flush=True,
            )
        rip = run_ripser(path, T, dim, timeout=30)
        recs["ripser"] = rip
        row["runs"]["ripser"] = strip_pairs(rip)
        rw = rip.get("wall_s")
        if rip.get("ok") and rip.get("pairs") is not None:
            for key, rec in recs.items():
                if key == "ripser":
                    continue
                if rec.get("ok") and rec.get("pairs") is not None:
                    row["vs_ripser"][key] = compare(rec["pairs"], rip["pairs"], dim)
                w = rec.get("wall_s")
                row["ratio"][key] = (rw / w) if w and rw else None
        series.append(row)
        print(f"  ratios { {k: row['ratio'].get(k) for k in row['ratio']} }", flush=True)

    unmatched = 0
    faster = 0
    n_cmp = 0
    ge10 = 0
    for row in series:
        for cmp in row.get("vs_ripser", {}).values():
            unmatched += int(cmp.get("unmatched") or 0)
        aw = row["runs"]["auto"].get("wall_s")
        best = None
        hit10 = False
        for keep in KEEPS:
            w = row["runs"][f"young{keep}"].get("wall_s")
            r = row["ratio"].get(f"young{keep}")
            if r and r >= 10:
                hit10 = True
            if w is not None:
                best = w if best is None else min(best, w)
        if hit10:
            ge10 += 1
        if best and aw:
            n_cmp += 1
            if best < aw:
                faster += 1

    out = {
        "note": "I319 fair G_T + sparse young-cap + RedZeD. No DenseTimes. τ frozen.",
        "unmatched_vs_ripser": unmatched,
        "any_young_ge10_families": ge10,
        "best_young_faster_than_auto": f"{faster}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "young_cap_fair.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched={unmatched} ge10={ge10} young<auto {faster}/{n_cmp}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
