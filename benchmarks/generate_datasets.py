#!/usr/bin/env python3
"""Generate small synthetic point clouds for the first benchmark round."""

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


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--sizes", default="200,500,1000")
    p.add_argument("--seed", type=int, default=0)
    args = p.parse_args()
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
