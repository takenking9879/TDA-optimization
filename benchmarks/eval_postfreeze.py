#!/usr/bin/env python3
"""Dispatcher stress pack chosen after the leftover-H1 clock gate.

Seed 23. New generators (swiss_roll / linked_circles / sheared_loops)
plus unused size/T combinations. Does not retune τ, the 4 s leftover
clock, hollow |E|>8e6, or fat-H2 cuts. 1 thread. Empirical.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (  # noqa: E402
    clustered,
    linked_circles,
    nonuniform_circle,
    outliers_sphere,
    random_geometric,
    sheared_loops,
    swiss_roll,
    write_csv,
    write_lower_distance,
    circle_noisy,
)
from run_consolidation import run_estimate, run_ripser  # noqa: E402
from run_consolidation_limits import run_pith  # noqa: E402
from run_suite import PITH, compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 15


def estimate_distances(path: Path, T: float, maxdim: int):
    from run_suite import run_cmd  # noqa: WPS433

    cmd = [
        str(PITH),
        "--estimate",
        "--distances",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--format",
        "json",
    ]
    try:
        out, _, _ = run_cmd(cmd, 15)
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}


def run_pith_distances(path: Path, T: float, maxdim: int):
    from run_suite import parse_pith_text, run_cmd  # noqa: WPS433

    cmd = [
        str(PITH),
        "--distances",
        str(path),
        "--mode",
        "exact",
        "--engine",
        "auto",
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--threads",
        "1",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        return {"ok": True, "wall_s": dt, "pairs": pairs, "pipeline": c.get("pipeline")}
    except Exception as e:
        return {"ok": False, "wall_s": None, "error": str(e)[-400:]}


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(23)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("swiss_roll", swiss_roll, 2000, 2.2, 1, False),
        ("swiss_roll", swiss_roll, 8000, 2.2, 1, False),
        ("linked_circles", linked_circles, 1200, 1.3, 1, False),
        ("sheared_loops", sheared_loops, 2000, 1.3, 1, False),
        ("sheared_loops", sheared_loops, 8000, 1.3, 1, False),
        ("random_geometric", random_geometric, 6000, 0.08, 1, False),
        ("clustered", clustered, 5000, 0.55, 1, False),
        ("nonuniform_circle", nonuniform_circle, 6000, 1.5, 1, False),
        ("outliers_sphere", outliers_sphere, 400, 1.4, 2, False),
        ("l1_blobs", clustered, 800, 1.8, 1, True),
    ]
    recs = []
    n_timeout_miss = 0
    n_scale_miss = 0
    n_exact_mismatch = 0
    n_exact_checked = 0
    n_in_band = 0
    n_scored_band = 0
    for name, fn, n, T, dim, distances in cases:
        print(f"POST {name} n={n} T={T} dim={dim}", flush=True)
        if distances:
            path = CLOUDS / f"post_{name}_n{n}.lower"
            write_lower_distance(path, fn(n, rng), p=1.0)
            est = estimate_distances(path, T, dim)
            exact = run_pith_distances(path, T, dim)
            scale = {"ok": False, "wall_s": None, "unsupported": True}
            rip = {"ok": False, "skipped": True}
        else:
            path = CLOUDS / f"post_{name}_n{n}.csv"
            write_csv(path, fn(n, rng))
            est = run_estimate(path, T, dim, timeout=15)
            exact = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
            scale = run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S)
            rip = (
                run_ripser(path, T, dim, timeout=BUDGET_S)
                if n <= 1200
                else {"ok": False, "skipped": True}
            )
        rec_mode = est.get("mode_recommended")
        exact_ok = bool(exact.get("ok"))
        exact_s = exact.get("wall_s")
        timeout_miss = rec_mode == "exact" and not exact_ok
        scale_miss = (
            rec_mode == "scale"
            and exact_ok
            and exact_s is not None
            and exact_s < 8.0
        )
        n_timeout_miss += int(timeout_miss)
        n_scale_miss += int(scale_miss)
        lo, hi, mid = (
            est.get("est_runtime_lo_s"),
            est.get("est_runtime_hi_s"),
            est.get("est_runtime_s"),
        )
        wall = exact_s if rec_mode == "exact" else scale.get("wall_s")
        in_band = None
        if wall is not None and lo is not None and hi is not None:
            in_band = lo <= wall <= hi
            n_scored_band += 1
            n_in_band += int(in_band)
        topo = None
        if exact_ok and rip.get("ok") and exact.get("pairs") is not None:
            n_exact_checked += 1
            topo = compare(exact["pairs"], rip["pairs"], dim)
            if topo.get("unmatched", 0) > 0:
                n_exact_mismatch += 1
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "distances": distances,
            "mode_recommended": rec_mode,
            "engine_recommended": est.get("engine_recommended"),
            "residual_regime": est.get("residual_regime"),
            "exact_feasible": est.get("exact_feasible"),
            "est_exact_runtime_s": est.get("est_exact_runtime_s"),
            "est_runtime_s": mid,
            "est_runtime_lo_s": lo,
            "est_runtime_hi_s": hi,
            "in_band": in_band,
            "exact_ok": exact_ok,
            "exact_s": exact_s,
            "exact_pipeline": exact.get("pipeline"),
            "scale_s": scale.get("wall_s"),
            "ripser_s": rip.get("wall_s"),
            "exact_vs_ripser_unmatched": None if topo is None else topo.get("unmatched"),
            "timeout_miss": timeout_miss,
            "scale_miss": scale_miss,
            "threads": 1,
        }
        recs.append(rec)
        print(
            f"  rec={rec_mode} exact={exact_s} scale={rec['scale_s']} "
            f"ripser={rec['ripser_s']} unmatched={rec['exact_vs_ripser_unmatched']} "
            f"in_band={in_band} timeout_miss={timeout_miss} scale_miss={scale_miss} "
            f"regime={rec['residual_regime']} pipe={rec['exact_pipeline']}",
            flush=True,
        )
        exact.pop("pairs", None)
        rip.pop("pairs", None)
    out = {
        "note": (
            "Seed 23. Chosen after leftover-H1 clock gate / hollow |E| split / "
            "hollow hi_mult=6. timeout_miss = recommended exact but 15 s fail. "
            "scale_miss = recommended scale but exact finished under 8 s. "
            "τ / clock / fat-H2 frozen."
        ),
        "n": len(recs),
        "n_timeout_miss": n_timeout_miss,
        "n_scale_miss": n_scale_miss,
        "n_exact_checked": n_exact_checked,
        "n_exact_mismatch": n_exact_mismatch,
        "n_in_band": n_in_band,
        "n_scored_band": n_scored_band,
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "postfreeze.json"
    path.write_text(json.dumps(out, indent=2))
    print(
        f"wrote {path} timeout_miss={n_timeout_miss}/{len(recs)} "
        f"scale_miss={n_scale_miss}/{len(recs)} "
        f"exact_mismatch={n_exact_mismatch}/{n_exact_checked} "
        f"in_band={n_in_band}/{n_scored_band}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
