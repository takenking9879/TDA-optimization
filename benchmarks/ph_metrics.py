"""Shared persistence helpers for the stable benchmark suite.

Wave scripts may keep their own copies. New runners should import from here
or ``generate_datasets``, not from ``run_wave*.py``.
"""

from __future__ import annotations

import math


def ess(pairs, d):
    return sum(1 for p in pairs if p["dim"] == d and not math.isfinite(p["death"]))


def finite_bars(pairs, d):
    out = []
    for p in pairs:
        if p["dim"] != d:
            continue
        birth, death = p["birth"], p["death"]
        if math.isfinite(death) and death - birth > 1e-6:
            out.append((birth, death))
    return out


def bottleneck_h1(a, b):
    """Greedy L∞ matching on dim-1 bars (finite + essential as death=1e9)."""

    def bars(pairs):
        out = []
        for p in pairs:
            if p["dim"] != 1:
                continue
            birth, death = p["birth"], p["death"]
            if math.isfinite(death) and death - birth <= 1e-6:
                continue
            out.append((birth, death if math.isfinite(death) else 1e9))
        return out

    aa, bb = bars(a), bars(b)
    used = [False] * len(bb)
    worst = 0.0
    unmatched = 0
    for birth, death in aa:
        best = None
        best_j = None
        for j, (b2, d2) in enumerate(bb):
            if used[j]:
                continue
            if death < 1e8 and d2 < 1e8:
                sc = max(abs(birth - b2), abs(death - d2))
            elif death >= 1e8 and d2 >= 1e8:
                sc = 0.0
            else:
                sc = 1e9
            if best is None or sc < best:
                best, best_j = sc, j
        if best is not None and best < 1e8:
            used[best_j] = True
            worst = max(worst, best)
        else:
            unmatched += 1
            worst = max(worst, 1e9)
    unmatched += sum(1 for u in used if not u)
    if unmatched:
        return None
    return worst
