#!/usr/bin/env python3
"""Smoke new held-out generators and the giotto/GUDHI worker hooks."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (  # noqa: E402
    GENERATORS,
    disconnected_circles,
    grid_holes,
    random_geometric,
    two_spheres_apart,
    write_csv,
)
from run_consolidation import HAVE_GIOTTO, HAVE_GUDHI, run_giotto, run_gudhi_rips  # noqa: E402


def main():
    rng = np.random.default_rng(0)
    for name, fn, dim in (
        ("disconnected_circles", disconnected_circles, 2),
        ("random_geometric", random_geometric, 2),
        ("grid_holes", grid_holes, 2),
        ("two_spheres_apart", two_spheres_apart, 3),
    ):
        pts = fn(40, rng)
        if pts.shape != (40, dim):
            print(f"{name} shape {pts.shape} != (40, {dim})", file=sys.stderr)
            return 1
        if name not in GENERATORS:
            print(f"{name} missing from GENERATORS", file=sys.stderr)
            return 1
    path = BENCH / "datasets" / "generated" / "hook_smoke_n40.csv"
    write_csv(path, disconnected_circles(40, rng))
    if not HAVE_GIOTTO:
        print("giotto-ph not importable", file=sys.stderr)
        return 1
    g = run_giotto(path, 1.5, 1, n_threads=1, timeout=20)
    if not g.get("ok"):
        print("giotto smoke failed", g, file=sys.stderr)
        return 1
    if g.get("ess1") is None:
        print("giotto smoke missing ess1", g, file=sys.stderr)
        return 1
    if HAVE_GUDHI:
        u = run_gudhi_rips(path, 1.5, 1, timeout=20)
        if not u.get("ok"):
            print("gudhi smoke failed", u, file=sys.stderr)
            return 1
    print("ok baseline hooks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
