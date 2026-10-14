#!/usr/bin/env python3
"""Held-out / adversarial dispatcher + topology check.

Uses seed 17 (not the mixed/n_cc/engine-oracle seeds). Does not retune τ
or the n_cc / dense-flag cutoffs. 12 s, 1 thread.

Families cover loops, bridges, cavities, anisotropy, clusters, noise,
outliers, near-degeneracy, multi-scale T, random geometric graphs, and
a non-Euclidean L1 metric.
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
    circle_noisy,
    clustered,
    heavy_noise_circle,
    loops_with_bridges,
    many_loops,
    mixed_1d2d3d,
    multi_scale_loops,
    near_degenerate,
    torus,
    write_csv,
    write_lower_distance,
)
from ph_metrics import ess  # noqa: E402
from run_consolidation import run_estimate, run_ripser  # noqa: E402
from run_consolidation_limits import run_pith  # noqa: E402
from run_suite import PITH, compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12


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


def run_pith_distances(path: Path, T: float, maxdim: int, mode: str):
    from run_suite import parse_pith_text, run_cmd  # noqa: WPS433

    cmd = [
        str(PITH),
        "--distances",
        str(path),
        "--mode",
        mode,
        "--engine",
        "auto",
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--threads",
        "1",
        "--no-enclosing",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        return {
            "ok": True,
            "wall_s": dt,
            "pipeline": c.get("pipeline"),
            "pairs": pairs,
            "ess0": ess(pairs, 0),
            "ess1": ess(pairs, 1),
            "ess2": ess(pairs, 2),
        }
    except Exception as e:
        return {"ok": False, "wall_s": None, "error": str(e)[-400:]}


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(17)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("many_loops", many_loops, 400, 1.2, 1, False),
        ("loops_with_bridges", loops_with_bridges, 400, 1.3, 1, False),
        ("anisotropic_blob", anisotropic_blob, 400, 2.5, 1, False),
        ("clustered", clustered, 600, 0.8, 1, False),
        ("heavy_noise_circle", heavy_noise_circle, 400, 1.5, 1, False),
        ("near_degenerate", near_degenerate, 500, 0.12, 1, False),
        ("multi_scale_loops_smallT", multi_scale_loops, 400, 0.80, 1, False),
        ("multi_scale_loops_largeT", multi_scale_loops, 400, 2.80, 1, False),
        ("torus", torus, 400, 1.6, 1, False),
        ("mixed_1d2d3d", mixed_1d2d3d, 400, 1.4, 2, False),
        ("l1_circle", circle_noisy, 300, 1.5, 1, True),
    ]
    recs = []
    n_timeout_miss = 0
    n_scale_miss = 0
    n_exact_mismatch = 0
    n_exact_checked = 0
    for name, fn, n, T, dim, distances in cases:
        stem = name.replace("_smallT", "").replace("_largeT", "")
        if distances:
            path = CLOUDS / f"adv_{name}_n{n}.lower"
            write_lower_distance(path, fn(n, rng), p=1.0)
            est = estimate_distances(path, T, dim)
            exact = run_pith_distances(path, T, dim, "exact")
            scale = {"ok": False, "wall_s": None, "unsupported": True}
            rip = {"ok": False, "wall_s": None, "skipped": True}
        else:
            path = CLOUDS / f"adv_{stem}_n{n}.csv"
            write_csv(path, fn(n, rng))
            est = run_estimate(path, T, dim, timeout=15)
            exact = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
            scale = run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S)
            rip = (
                run_ripser(path, T, dim, timeout=BUDGET_S)
                if n <= 400
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
            "n_cc_max": est.get("n_cc_max"),
            "n_components": est.get("n_components"),
            "mode_recommended": rec_mode,
            "engine_recommended": est.get("engine_recommended"),
            "residual_regime": est.get("residual_regime"),
            "exact_feasible": est.get("exact_feasible"),
            "est_exact_runtime_s": est.get("est_exact_runtime_s"),
            "exact_ok": exact_ok,
            "exact_s": exact_s,
            "exact_pipeline": exact.get("pipeline"),
            "exact_ess": {
                "H0": exact.get("ess0"),
                "H1": exact.get("ess1"),
                "H2": exact.get("ess2"),
            },
            "scale_s": scale.get("wall_s"),
            "scale_ess": {
                "H0": scale.get("ess0"),
                "H1": scale.get("ess1"),
                "H2": scale.get("ess2"),
            },
            "ripser_s": rip.get("wall_s"),
            "ripser_ess": {
                "H0": rip.get("ess0"),
                "H1": rip.get("ess1"),
                "H2": rip.get("ess2"),
            },
            "exact_vs_ripser_unmatched": None if topo is None else topo.get("unmatched"),
            "timeout_miss": timeout_miss,
            "scale_miss": scale_miss,
        }
        recs.append(rec)
        print(
            f"{name} n={n} rec={rec_mode} exact={exact_s} scale={rec['scale_s']} "
            f"unmatched={rec['exact_vs_ripser_unmatched']} "
            f"timeout_miss={timeout_miss} scale_miss={scale_miss}",
            flush=True,
        )
        # Drop large pair lists from the receipt.
        exact.pop("pairs", None)
        rip.pop("pairs", None)
    out = {
        "note": (
            "Held-out seed 17. timeout_miss = recommended exact but 12 s fail. "
            "scale_miss = recommended scale but exact finished under 8 s. "
            "τ / n_cc / dense-flag frozen."
        ),
        "n": len(recs),
        "n_timeout_miss": n_timeout_miss,
        "n_scale_miss": n_scale_miss,
        "n_exact_checked": n_exact_checked,
        "n_exact_mismatch": n_exact_mismatch,
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "adversarial.json"
    path.write_text(json.dumps(out, indent=2))
    print(
        f"wrote {path} timeout_miss={n_timeout_miss}/{len(recs)} "
        f"scale_miss={n_scale_miss}/{len(recs)} "
        f"exact_mismatch={n_exact_mismatch}/{n_exact_checked}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
