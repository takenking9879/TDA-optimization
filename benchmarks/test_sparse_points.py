#!/usr/bin/env python3
"""CLI check: Euclidean --mode sparse matches the matrix path on held-out clouds."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    anisotropic_blob,
    clustered,
    circle_noisy,
    disconnected_circles,
    grid_holes,
    write_csv,
    write_lower_distance,
)
from run_suite import PITH, parse_pith_text  # noqa: E402
from run_wave85 import figure8  # noqa: E402
from run_wave95 import ess  # noqa: E402

GEN = BENCH / "datasets" / "generated"


def _edges(text: str) -> list[tuple[int, int]]:
    out = []
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        try:
            u, v = int(parts[0]), int(parts[1])
        except ValueError:
            continue
        if u == v:
            continue
        if u > v:
            u, v = v, u
        out.append((u, v))
    return sorted(out)


def _run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(7)
    families = (
        ("c4", np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]), 1.2, 1),
        ("figure8", figure8(120, rng), 1.1, 1),
        ("circle_noisy", circle_noisy(120, rng), 1.5, 1),
        ("grid_holes", grid_holes(120, rng), 0.12, 1),
        ("disconnected_circles", disconnected_circles(120, rng), 1.5, 1),
        ("clustered", clustered(120, rng), 1.2, 1),
        ("anisotropic_blob", anisotropic_blob(120, rng), 1.2, 1),
    )
    GEN.mkdir(parents=True, exist_ok=True)
    for name, pts, T, dim in families:
        csv_path = GEN / f"sparse_pts_{name}.csv"
        dist_path = GEN / f"sparse_pts_{name}.dist"
        write_csv(csv_path, pts)
        write_lower_distance(dist_path, pts, p=2.0)
        common = [
            str(PITH),
            "--threshold",
            str(T),
            "--maxdim",
            str(dim),
            "--threads",
            "1",
            "--no-enclosing",
            "--mode",
            "sparse",
        ]
        e_pts = _run(common + ["--points", str(csv_path), "--sparse-only"])
        e_mat = _run(common + ["--distances", str(dist_path), "--sparse-only"])
        if e_pts.returncode != 0 or e_mat.returncode != 0:
            print(f"{name}: sparse-only failed", e_pts.stderr, e_mat.stderr, file=sys.stderr)
            return 1
        a, b = set(_edges(e_pts.stdout)), set(_edges(e_mat.stdout))
        if a != b:
            print(
                f"{name}: edge-set mismatch |pts|={len(a)} |mat|={len(b)} "
                f"only_pts={len(a - b)} only_mat={len(b - a)}",
                file=sys.stderr,
            )
            return 1
        p_pts = _run(common + ["--points", str(csv_path)])
        p_mat = _run(common + ["--distances", str(dist_path)])
        if p_pts.returncode != 0 or p_mat.returncode != 0:
            print(f"{name}: persist failed", p_pts.stderr, p_mat.stderr, file=sys.stderr)
            return 1
        pairs_p, c_p = parse_pith_text(p_pts.stdout)
        pairs_m, _c_m = parse_pith_text(p_mat.stdout)
        if "pipeline=pith:sparse" not in p_pts.stdout:
            print(f"{name}: missing pith:sparse tag", file=sys.stderr)
            return 1
        if ess(pairs_p, dim) != ess(pairs_m, dim):
            print(f"{name}: essential mismatch {ess(pairs_p, dim)} vs {ess(pairs_m, dim)}", file=sys.stderr)
            return 1
        print(
            f"ok {name} n={len(pts)} edges={len(a)} ess={ess(pairs_p, dim)} "
            f"edges_in={c_p.get('edges_in')} distances={c_p.get('distances')}"
        )
    print("ok sparse points==matrix CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
