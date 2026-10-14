#!/usr/bin/env python3
"""Held-out stress of the Euclidean fat-H2 n_cc>=800 cutoff.

mixed_1d2d3d (seed 0) was used to pick 800. This suite uses seed 11 and
other families. Does not retune τ or the cutoff. 12 s, 1 thread.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    multi_cavities,
    outliers_sphere,
    sphere,
    two_spheres_apart,
    uniform,
    write_csv,
)
from run_consolidation import run_estimate  # noqa: E402
from run_consolidation_limits import run_pith  # noqa: E402
from run_suite import PITH  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12


def cage_and_ball(n: int, rng: np.random.Generator) -> np.ndarray:
    """Held-out: unit sphere plus a filled ball far away."""
    n0 = n // 2
    n1 = n - n0
    sph = sphere(n0, rng)
    ball = []
    while len(ball) < n1:
        p = rng.uniform(-1.0, 1.0, size=3)
        if float(np.dot(p, p)) <= 1.0:
            ball.append(p)
    return np.vstack([sph, np.asarray(ball) + np.array([8.0, 0.0, 0.0])])


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(11)
    cases = [
        ("two_spheres_apart", two_spheres_apart, 400, 1.4, 2),
        ("two_spheres_apart", two_spheres_apart, 1200, 1.4, 2),
        ("outliers_sphere", outliers_sphere, 400, 1.4, 2),
        ("outliers_sphere", outliers_sphere, 900, 1.4, 2),
        ("multi_cavities", multi_cavities, 400, 1.4, 2),
        ("multi_cavities", multi_cavities, 900, 1.4, 2),
        ("cage_and_ball", cage_and_ball, 400, 1.6, 2),
        ("cage_and_ball", cage_and_ball, 1600, 1.6, 2),
        ("uniform3", lambda n, r: uniform(n, 3, r), 400, 0.8, 2),
        ("sphere_complete", sphere, 400, 2.5, 2),
        ("sphere_complete", sphere, 700, 2.5, 2),
    ]
    recs = []
    n_timeout_miss = 0
    n_scale_miss = 0
    for name, fn, n, T, dim in cases:
        path = CLOUDS / f"ncc_{name}_n{n}.csv"
        write_csv(path, fn(n, rng))
        est = run_estimate(path, T, dim, timeout=15)
        exact = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=BUDGET_S)
        scale = run_pith(path, T, dim, "scale", "auto", threads=1, timeout=BUDGET_S)
        rec_mode = est.get("mode_recommended")
        exact_ok = bool(exact.get("ok"))
        exact_s = exact.get("wall_s")
        timeout_miss = rec_mode == "exact" and not exact_ok
        scale_miss = rec_mode == "scale" and exact_ok and exact_s is not None and exact_s < 8.0
        n_timeout_miss += int(timeout_miss)
        n_scale_miss += int(scale_miss)
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "n_cc_max": est.get("n_cc_max"),
            "n_components": est.get("n_components"),
            "mode_recommended": rec_mode,
            "exact_feasible": est.get("exact_feasible"),
            "est_exact_runtime_s": est.get("est_exact_runtime_s"),
            "exact_ok": exact_ok,
            "exact_s": exact_s,
            "scale_s": scale.get("wall_s"),
            "exact_pipeline": exact.get("pipeline"),
            "timeout_miss": timeout_miss,
            "scale_miss": scale_miss,
        }
        recs.append(rec)
        print(
            f"{name} n={n} n_cc={rec['n_cc_max']} rec={rec_mode} "
            f"exact={exact_s} scale={rec['scale_s']} "
            f"timeout_miss={timeout_miss} scale_miss={scale_miss}",
            flush=True,
        )
    out = {
        "note": (
            "Held-out seed 11. timeout_miss = recommended exact but 12 s fail. "
            "scale_miss = recommended scale but exact finished under 8 s "
            "(conservative; user loses exact VR). Euclidean fat H2 cutoff: "
            "n_cc>=800 or (edge_frac>=0.5 and n_cc>=600). τ frozen."
        ),
        "n": len(recs),
        "n_timeout_miss": n_timeout_miss,
        "n_scale_miss": n_scale_miss,
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "ncc_auto.json"
    path.write_text(json.dumps(out, indent=2))
    print(
        f"wrote {path} timeout_miss={n_timeout_miss}/{len(recs)} "
        f"scale_miss={n_scale_miss}/{len(recs)}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
