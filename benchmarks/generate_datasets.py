#!/usr/bin/env python3
"""Generate small synthetic point clouds for the first benchmark round.

Also exposes held-out / adversarial families used for PITH consolidation.
Each public generator is ``(n, rng) -> (n, d)`` except ``uniform(n, dim, rng)``.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "datasets" / "generated"


def write_csv(path: Path, pts: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        for row in pts:
            w.writerow([f"{x:.8f}" for x in row])


def write_lower_distance(path: Path, pts: np.ndarray, p: float = 1.0) -> None:
    """Ripser lower-distance format (row i has i entries) under an L_p metric."""
    path.parent.mkdir(parents=True, exist_ok=True)
    n = pts.shape[0]
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        for i in range(1, n):
            diffs = np.abs(pts[i] - pts[:i])
            if p == 1.0:
                d = diffs.sum(axis=1)
            elif p == 2.0:
                d = np.sqrt((diffs * diffs).sum(axis=1))
            else:
                d = np.power(np.power(diffs, p).sum(axis=1), 1.0 / p)
            w.writerow([f"{x:.8f}" for x in d])


def _split_n(n: int, k: int) -> list[int]:
    q, r = divmod(n, k)
    return [q + (i < r) for i in range(k)]


def _noisy_circle(
    n: int,
    rng: np.random.Generator,
    center: tuple[float, float] = (0.0, 0.0),
    radius: float = 1.0,
    sigma: float = 0.05,
) -> np.ndarray:
    t = rng.uniform(0, 2 * math.pi, size=n)
    c = np.asarray(center, dtype=float)
    pts = np.stack([np.cos(t), np.sin(t)], axis=1) * radius + c
    return pts + rng.normal(0, sigma, size=pts.shape)


def _filled_disk(
    n: int,
    rng: np.random.Generator,
    center: tuple[float, float] = (0.0, 0.0),
    radius: float = 1.0,
) -> np.ndarray:
    t = rng.uniform(0, 2 * math.pi, size=n)
    r = radius * np.sqrt(rng.uniform(0, 1, size=n))
    c = np.asarray(center, dtype=float)
    return np.stack([r * np.cos(t), r * np.sin(t)], axis=1) + c


def circle_noisy(n: int, rng: np.random.Generator, sigma: float = 0.05) -> np.ndarray:
    t = rng.uniform(0, 2 * math.pi, size=n)
    pts = np.stack([np.cos(t), np.sin(t)], axis=1)
    return pts + rng.normal(0, sigma, size=pts.shape)


def sphere(n: int, rng: np.random.Generator) -> np.ndarray:
    x = rng.normal(size=(n, 3))
    x /= np.linalg.norm(x, axis=1, keepdims=True)
    return x


def torus(n: int, rng: np.random.Generator, R: float = 2.0, r: float = 0.5) -> np.ndarray:
    u = rng.uniform(0, 2 * math.pi, size=n)
    v = rng.uniform(0, 2 * math.pi, size=n)
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    return np.stack([x, y, z], axis=1)


def blobs(n: int, rng: np.random.Generator) -> np.ndarray:
    centers = np.array([[0.0, 0.0], [3.0, 0.0], [1.5, 2.6]])
    labs = rng.integers(0, 3, size=n)
    return centers[labs] + rng.normal(0, 0.25, size=(n, 2))


def uniform(n: int, dim: int, rng: np.random.Generator) -> np.ndarray:
    return rng.uniform(0, 1, size=(n, dim))


def many_loops(n: int, rng: np.random.Generator) -> np.ndarray:
    k = 5
    counts = _split_n(n, k)
    parts = []
    for i, ni in enumerate(counts):
        ang = 2 * math.pi * i / k
        center = (4.5 * math.cos(ang), 4.5 * math.sin(ang))
        parts.append(_noisy_circle(ni, rng, center, radius=1.0, sigma=0.05))
    return np.vstack(parts)


def figure8(n: int, rng: np.random.Generator) -> np.ndarray:
    """Two unit circles meeting at a point. Public generator (not a wave helper)."""
    n0, n1 = _split_n(n, 2)
    a = _noisy_circle(n0, rng, (0.0, 0.0), radius=1.0, sigma=0.04)
    b = _noisy_circle(n1, rng, (2.0, 0.0), radius=1.0, sigma=0.04)
    return np.vstack([a, b])


def nested_loops(n: int, rng: np.random.Generator) -> np.ndarray:
    n0, n1 = _split_n(n, 2)
    inner = _noisy_circle(n0, rng, (0.0, 0.0), radius=1.0, sigma=0.04)
    outer = _noisy_circle(n1, rng, (0.0, 0.0), radius=2.5, sigma=0.04)
    return np.vstack([inner, outer])


def loops_with_bridges(n: int, rng: np.random.Generator) -> np.ndarray:
    n_bridge = max(1, n // 4)
    n_a, n_b = _split_n(n - n_bridge, 2)
    a = _noisy_circle(n_a, rng, (0.0, 0.0), radius=1.0, sigma=0.05)
    b = _noisy_circle(n_b, rng, (3.0, 0.0), radius=1.0, sigma=0.05)
    t = rng.uniform(0.0, 1.0, size=n_bridge)
    bridge = np.stack([1.0 + t, np.zeros(n_bridge)], axis=1)
    bridge = bridge + rng.normal(0, 0.03, size=bridge.shape)
    return np.vstack([a, b, bridge])


def multi_cavities(n: int, rng: np.random.Generator) -> np.ndarray:
    counts = _split_n(n, 3)
    offsets = (
        np.array([0.0, 0.0, 0.0]),
        np.array([5.0, 0.0, 0.0]),
        np.array([2.5, 4.3, 0.0]),
    )
    parts = [sphere(ni, rng) + off for ni, off in zip(counts, offsets)]
    return np.vstack(parts)


def anisotropic_blob(n: int, rng: np.random.Generator) -> np.ndarray:
    cov = np.array([[10.0, 0.0], [0.0, 1.0]])
    return rng.multivariate_normal(np.zeros(2), cov, size=n)


def clustered(n: int, rng: np.random.Generator) -> np.ndarray:
    centers = np.array([[x * 3.0, y * 3.0] for y in range(2) for x in range(4)])
    labs = rng.integers(0, 8, size=n)
    return centers[labs] + rng.normal(0, 0.1, size=(n, 2))


def heavy_noise_circle(n: int, rng: np.random.Generator) -> np.ndarray:
    n_out = int(round(0.30 * n))
    n_circ = n - n_out
    circ = circle_noisy(n_circ, rng, sigma=0.05)
    box = rng.uniform(-1.2, 1.2, size=(n_out, 2))
    return np.vstack([circ, box])


def outliers_sphere(n: int, rng: np.random.Generator) -> np.ndarray:
    n_out = int(round(0.05 * n))
    n_sph = n - n_out
    sph = sphere(n_sph, rng)
    out = rng.normal(size=(n_out, 3))
    out /= np.linalg.norm(out, axis=1, keepdims=True)
    out *= rng.uniform(10.0, 20.0, size=(n_out, 1))
    return np.vstack([sph, out])


def near_degenerate(n: int, rng: np.random.Generator) -> np.ndarray:
    x = rng.uniform(-1.0, 1.0, size=n)
    y = rng.normal(0.0, 1e-3, size=n)
    return np.stack([x, y], axis=1)


def mixed_1d2d3d(n: int, rng: np.random.Generator) -> np.ndarray:
    n_circ, n_disk, n_sph = _split_n(n, 3)
    circ = _noisy_circle(n_circ, rng, (0.0, 0.0), radius=1.0, sigma=0.04)
    circ3 = np.column_stack([circ, np.zeros(n_circ)])
    disk = _filled_disk(n_disk, rng, (3.0, 0.0), radius=1.0)
    disk3 = np.column_stack([disk, np.zeros(n_disk)])
    sph = sphere(n_sph, rng) * 0.4 + np.array([1.5, 3.0, 0.0])
    return np.vstack([circ3, disk3, sph])


def nonuniform_circle(n: int, rng: np.random.Generator) -> np.ndarray:
    labs = rng.integers(0, 3, size=n)
    mus = np.array([0.0, 2.2, 4.4])
    t = rng.vonmises(mus[labs], 12.0)
    pts = np.stack([np.cos(t), np.sin(t)], axis=1)
    return pts + rng.normal(0, 0.04, size=pts.shape)


def multi_scale_loops(n: int, rng: np.random.Generator) -> np.ndarray:
    n_small, n_large = _split_n(n, 2)
    small = _noisy_circle(n_small, rng, (0.0, 0.0), radius=0.35, sigma=0.03)
    large = _noisy_circle(n_large, rng, (6.0, 0.0), radius=2.5, sigma=0.05)
    return np.vstack([small, large])


def disconnected_circles(n: int, rng: np.random.Generator) -> np.ndarray:
    """Two unit circles far apart so a moderate T leaves G_T disconnected."""
    n0, n1 = _split_n(n, 2)
    a = _noisy_circle(n0, rng, (0.0, 0.0), radius=1.0, sigma=0.05)
    b = _noisy_circle(n1, rng, (20.0, 0.0), radius=1.0, sigma=0.05)
    return np.vstack([a, b])


def random_geometric(n: int, rng: np.random.Generator) -> np.ndarray:
    """Unit-square i.i.d. sample (random geometric graph at a chosen T)."""
    return uniform(n, 2, rng)


def grid_holes(n: int, rng: np.random.Generator) -> np.ndarray:
    """Post-freeze family: jittered lattice with two rectangular holes.

    Chosen after the feasibility / engine thresholds were frozen so it
    cannot have influenced τ or the hollow cutoff.
    """
    side = max(8, int(math.ceil(math.sqrt(n * 1.35))))
    xs, ys = np.linspace(0.0, 1.0, side), np.linspace(0.0, 1.0, side)
    xx, yy = np.meshgrid(xs, ys)
    pts = np.stack([xx.ravel(), yy.ravel()], axis=1)
    hole_a = (pts[:, 0] - 0.30) ** 2 + (pts[:, 1] - 0.30) ** 2 < 0.08**2
    hole_b = (np.abs(pts[:, 0] - 0.72) < 0.10) & (np.abs(pts[:, 1] - 0.68) < 0.10)
    pts = pts[~(hole_a | hole_b)]
    if len(pts) > n:
        pts = pts[rng.choice(len(pts), size=n, replace=False)]
    elif len(pts) < n:
        extra = rng.uniform(0.0, 1.0, size=(n - len(pts), 2))
        pts = np.vstack([pts, extra])
    return pts + rng.normal(0.0, 0.004, size=pts.shape)


def uniform4(n: int, rng: np.random.Generator) -> np.ndarray:
    """Held-out 4D cloud: no Delaunay scale path; `--mode auto` may pick sparse."""
    return uniform(n, 4, rng)


def swiss_roll(n: int, rng: np.random.Generator) -> np.ndarray:
    """Post-clock-gate family: 2D swiss roll in R^3."""
    t = rng.uniform(1.5 * math.pi, 4.5 * math.pi, size=n)
    h = rng.uniform(-1.0, 1.0, size=n)
    pts = np.stack([t * np.cos(t), h, t * np.sin(t)], axis=1)
    return pts + rng.normal(0.0, 0.05, size=pts.shape)


def linked_circles(n: int, rng: np.random.Generator) -> np.ndarray:
    """Post-clock-gate family: two interlocking noisy rings in R^3."""
    n0, n1 = _split_n(n, 2)
    t0 = rng.uniform(0.0, 2.0 * math.pi, size=n0)
    a = np.stack([np.cos(t0), np.sin(t0), np.zeros(n0)], axis=1)
    t1 = rng.uniform(0.0, 2.0 * math.pi, size=n1)
    b = np.stack([1.0 + np.cos(t1), np.zeros(n1), np.sin(t1)], axis=1)
    return np.vstack([a, b]) + rng.normal(0.0, 0.04, size=(n, 3))


def sheared_loops(n: int, rng: np.random.Generator) -> np.ndarray:
    """Post-clock-gate family: sheared figure-8 (anisotropic leftover H1)."""
    pts = figure8(n, rng)
    shear = np.array([[2.2, 0.7], [0.0, 0.45]])
    return pts @ shear.T + rng.normal(0.0, 0.02, size=pts.shape)


def two_spheres_apart(n: int, rng: np.random.Generator) -> np.ndarray:
    """Post-freeze: two unit spheres whose convex hulls do not meet at T=1.4."""
    n0, n1 = _split_n(n, 2)
    return np.vstack([sphere(n0, rng), sphere(n1, rng) + np.array([8.0, 0.0, 0.0])])


GENERATORS = {
    "circle_noisy": circle_noisy,
    "figure8": figure8,
    "sphere": sphere,
    "torus": torus,
    "blobs": blobs,
    "many_loops": many_loops,
    "nested_loops": nested_loops,
    "loops_with_bridges": loops_with_bridges,
    "multi_cavities": multi_cavities,
    "anisotropic_blob": anisotropic_blob,
    "clustered": clustered,
    "heavy_noise_circle": heavy_noise_circle,
    "outliers_sphere": outliers_sphere,
    "near_degenerate": near_degenerate,
    "mixed_1d2d3d": mixed_1d2d3d,
    "nonuniform_circle": nonuniform_circle,
    "multi_scale_loops": multi_scale_loops,
    "disconnected_circles": disconnected_circles,
    "random_geometric": random_geometric,
    "grid_holes": grid_holes,
    "two_spheres_apart": two_spheres_apart,
    "uniform4": uniform4,
    "swiss_roll": swiss_roll,
    "linked_circles": linked_circles,
    "sheared_loops": sheared_loops,
}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--list", action="store_true", help="print generator names")
    p.add_argument("--sizes", default="200,500,1000")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
    if args.list:
        for name in GENERATORS:
            print(name)
        return

    sizes = [int(s) for s in args.sizes.split(",") if s]
    rng = np.random.default_rng(args.seed)

    specs = [
        ("circle_noisy", lambda n: circle_noisy(n, rng), 1.2),
        ("sphere", lambda n: sphere(n, rng), 1.4),
        ("torus", lambda n: torus(n, rng), 1.6),
        ("blobs", lambda n: blobs(n, rng), 1.0),
        ("uniform2", lambda n: uniform(n, 2, rng), 0.35),
        ("uniform10", lambda n: uniform(n, 10, rng), 1.8),
    ]
    index = []
    for name, fn, T in specs:
        for n in sizes:
            pts = fn(n)
            path = OUT / f"{name}_n{n}.csv"
            write_csv(path, pts)
            index.append((name, n, T, str(path.relative_to(ROOT))))
            print(f"wrote {path} shape={pts.shape} T={T}")

    meta = OUT / "index.csv"
    with meta.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "n", "threshold", "path"])
        w.writerows(index)
    print(f"index {meta}")


if __name__ == "__main__":
    main()
