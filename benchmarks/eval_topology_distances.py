#!/usr/bin/env python3
"""GUDHI bottleneck + Hera/POT Wasserstein on scale vs Ripser at n<=400."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import circle_noisy, many_loops, nested_loops, sphere, write_csv  # noqa: E402
from run_consolidation import run_pith, run_ripser  # noqa: E402
from run_wave85 import figure8  # noqa: E402
import gudhi  # noqa: E402
from gudhi.hera import wasserstein_distance as hera_w  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"


def arr(pairs, dim):
    rows = []
    for p in pairs or []:
        if p["dim"] != dim:
            continue
        b, d = p["birth"], p["death"]
        if math.isfinite(d) and d - b <= 1e-6:
            continue
        rows.append([b, d if math.isfinite(d) else math.inf])
    return np.asarray(rows, dtype=float) if rows else np.zeros((0, 2), dtype=float)


def main():
    rng = np.random.default_rng(0)
    recs = []
    for name, fn, T, dim, n in (
        ("figure8", figure8, 1.1, 1, 400),
        ("circle_noisy", circle_noisy, 1.5, 1, 400),
        ("sphere", sphere, 1.4, 2, 400),
        ("nested_loops", nested_loops, 1.6, 1, 400),
        ("many_loops", many_loops, 1.2, 1, 400),
    ):
        path = CLOUDS / f"{name}_n{n}.csv"
        if not path.exists():
            write_csv(path, fn(n, rng))
        rip = run_ripser(path, T, dim, timeout=20)
        scale = run_pith(path, T, dim, "scale", "auto", timeout=20)
        exact = run_pith(path, T, dim, "exact", "auto", timeout=20)
        row = {"name": name, "n": n, "T": T}
        for lab, other in (("scale", scale), ("exact", exact)):
            ref, oth = rip.get("pairs") or [], other.get("pairs") or []
            for d in range(dim + 1):
                A, B = arr(ref, d), arr(oth, d)
                try:
                    bn = float(gudhi.bottleneck_distance(A, B))
                except Exception as e:
                    bn = None
                    row[f"{lab}_bn_h{d}_err"] = str(e)
                try:
                    w1 = float(hera_w(A, B, order=1.0, internal_p=float("inf")))
                except Exception as e:
                    w1 = None
                    row[f"{lab}_w1_h{d}_err"] = str(e)
                row[f"{lab}_bn_h{d}"] = bn
                row[f"{lab}_w1_h{d}"] = w1
        recs.append(row)
        print(row, flush=True)
    path = OUT / "wasserstein.json"
    path.write_text(json.dumps(recs, indent=2))
    print("wrote", path)


if __name__ == "__main__":
    main()
