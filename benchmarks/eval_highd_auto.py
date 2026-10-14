#!/usr/bin/env python3
"""Adversarial check of the high-d exact-vs-sparse clock-compare.

Held-out from the uniform4 n=5000 / uniform10 n=4000 cells that
motivated the override. Does not retune τ. 12 s, 1 thread.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import uniform, write_csv, write_lower_distance  # noqa: E402
from run_consolidation import run_estimate  # noqa: E402
from run_suite import PITH, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12


def run_mode(path: Path, T: float, maxdim: int, mode: str, distances: bool = False):
    cmd = [
        str(PITH),
        "--distances" if distances else "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        mode,
        "--engine",
        "auto",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        _, c = parse_pith_text(out)
        return {
            "ok": True,
            "wall_s": dt,
            "pipeline": c.get("pipeline"),
            "timed_out": False,
        }
    except Exception as e:
        err = str(e)
        return {
            "ok": False,
            "wall_s": None,
            "timed_out": "timed out" in err.lower(),
            "refused": "refusing" in err.lower(),
            "error": err[-400:],
        }


def estimate(path: Path, T: float, maxdim: int, distances: bool = False):
    if not distances:
        return run_estimate(path, T, maxdim, timeout=BUDGET_S)
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
        out, _, _ = run_cmd(cmd, BUDGET_S)
        return json.loads(out)
    except Exception as e:
        return {"error": str(e)}


def main() -> int:
    rng = np.random.default_rng(21)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("uniform6", 2000, 1.2, 1, 6, False),
        ("uniform6", 4000, 1.2, 1, 6, False),
        ("uniform8", 2000, 1.5, 1, 8, False),
        ("uniform8", 4000, 1.5, 1, 8, False),
        ("uniform5_sparseT", 3000, 0.7, 1, 5, False),
        ("uniform5_denseT", 3000, 1.6, 1, 5, False),
        ("uniform7", 2500, 1.3, 1, 7, False),
        ("uniform4_l1", 2000, 1.0, 1, 4, True),
        ("uniform6_h2_refuse", 200, 0.8, 2, 6, False),
    ]
    rows = []
    n_wrong = 0
    n_compared = 0
    for name, n, T, maxdim, dim, use_l1 in cases:
        pts = uniform(n, dim, rng)
        if use_l1:
            path = CLOUDS / f"adv_{name}_n{n}.ldist"
            write_lower_distance(path, pts, p=1.0)
        else:
            path = CLOUDS / f"adv_{name}_n{n}.csv"
            write_csv(path, pts)
        print(f"ADV {name} n={n} d={dim} T={T} maxdim={maxdim}", flush=True)
        est = estimate(path, T, maxdim, distances=use_l1)
        rec_mode = est.get("mode_recommended")
        print(
            f"  rec={rec_mode} exact_ok={est.get('exact_feasible')} "
            f"est_exact={est.get('est_exact_runtime_s')} "
            f"est_sparse={est.get('est_sparse_runtime_s')} "
            f"auto_will_run={est.get('auto_will_run')}",
            flush=True,
        )
        auto = run_mode(path, T, maxdim, "auto", distances=use_l1)
        print(
            f"  auto ok={auto.get('ok')} refused={auto.get('refused')} "
            f"wall={auto.get('wall_s')} pipe={auto.get('pipeline')}",
            flush=True,
        )
        exact = sparse = None
        if maxdim == 1:
            exact = run_mode(path, T, maxdim, "exact", distances=use_l1)
            sparse = run_mode(path, T, maxdim, "sparse", distances=use_l1)
            print(
                f"  exact={exact.get('wall_s')} sparse={sparse.get('wall_s')}",
                flush=True,
            )
        cheaper = None
        wrong = None
        if exact and sparse and exact.get("wall_s") and sparse.get("wall_s"):
            cheaper = "exact" if exact["wall_s"] <= sparse["wall_s"] else "sparse"
            n_compared += 1
            if rec_mode in ("exact", "sparse"):
                wrong = rec_mode != cheaper
                if wrong:
                    n_wrong += 1
        elif exact and exact.get("ok") and sparse and sparse.get("timed_out"):
            cheaper = "exact"
            n_compared += 1
            wrong = rec_mode == "sparse"
            if wrong:
                n_wrong += 1
        elif sparse and sparse.get("ok") and exact and exact.get("timed_out"):
            cheaper = "sparse"
            n_compared += 1
            wrong = rec_mode == "exact"
            if wrong:
                n_wrong += 1
        refuse_ok = None
        if maxdim >= 2:
            refuse_ok = bool(auto.get("refused")) and rec_mode == "sparse"
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "d": dim,
                "metric": "l1" if use_l1 else "euclidean",
                "estimate": {
                    k: est.get(k)
                    for k in (
                        "mode_recommended",
                        "engine_recommended",
                        "exact_feasible",
                        "auto_will_run",
                        "residual_regime",
                        "est_exact_runtime_s",
                        "est_sparse_runtime_s",
                        "reason",
                    )
                },
                "auto": auto,
                "exact": exact,
                "sparse": sparse,
                "cheaper": cheaper,
                "wrong": wrong,
                "refuse_ok": refuse_ok,
                "threads": 1,
                "budget_s": BUDGET_S,
            }
        )
    payload = {
        "note": (
            "Held-out high-d / L1 clock-compare. τ frozen. "
            "wrong=recommended mode was the slower of exact/sparse."
        ),
        "n_compared": n_compared,
        "n_wrong": n_wrong,
        "receipts": rows,
    }
    dest = OUT / "highd_auto.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest, f"{n_wrong}/{n_compared} wrong")
    return 0


if __name__ == "__main__":
    sys.exit(main())
