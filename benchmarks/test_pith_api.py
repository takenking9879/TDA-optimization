#!/usr/bin/env python3
"""Smoke the stable Python wrapper. No I-numbers, no leftover hunting."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "python"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_datasets import circle_noisy, uniform4  # noqa: E402
import pith  # noqa: E402


def main() -> int:
    rng = np.random.default_rng(0)
    circle = circle_noisy(80, rng)
    est = pith.estimate(circle, maxdim=1, threshold=1.5)
    if est.get("kind") != "estimate" or est.get("mode_recommended") not in pith.MODES:
        print("estimate JSON incomplete", est, file=sys.stderr)
        return 1
    dgm = pith.rips(circle, maxdim=1, threshold=1.5, mode="exact", threads=1)
    if dgm.get("ess", {}).get(1, 0) != 1:
        print("circle exact ess H1 != 1", dgm.get("ess"), file=sys.stderr)
        return 1
    if "pipeline" not in dgm:
        print("rips missing pipeline", file=sys.stderr)
        return 1
    sc = pith.rips(circle, maxdim=1, threshold=1.5, mode="scale", threads=1)
    if sc.get("ess", {}).get(1, 0) != 1:
        print("circle scale ess H1 != 1", sc.get("ess"), file=sys.stderr)
        return 1
    fat250 = uniform4(250, rng)
    try:
        pith.rips(fat250, maxdim=2, threshold=0.6, mode="auto", threads=1, timeout=25)
        print("uniform4 n=250 maxdim=2 auto did not refuse", file=sys.stderr)
        return 1
    except pith.Refused:
        pass
    print("ok pith python API")
    return 0


if __name__ == "__main__":
    sys.exit(main())
