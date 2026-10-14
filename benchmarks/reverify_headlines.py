#!/usr/bin/env python3
"""Re-measure the two headline 1-thread exact ratios on this box."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import circle_noisy, sphere  # noqa: E402
from run_consolidation import run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402
import numpy as np

OUT = BENCH / "results" / "consolidation"


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    recs = []
    for name, fn, n, T, dim in (
        ("circle_noisy", circle_noisy, 1000, 1.5, 1),
        ("sphere", sphere, 400, 1.4, 2),
    ):
        path = cloud(name, n, fn, rng)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=12)
        rip = run_ripser(path, T, dim, timeout=12)
        pw, rw = pith.get("wall_s"), rip.get("wall_s")
        ratio = (rw / pw) if pw and rw else None
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": dim,
            "pith_s": pw,
            "ripser_s": rw,
            "ratio": ratio,
            "pith_ok": pith.get("ok"),
            "ripser_ok": rip.get("ok"),
            "threads": 1,
        }
        recs.append(rec)
        print(f"{name} n={n} pith={pw} ripser={rw} ratio={ratio}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "headline_reverify.json"
    path.write_text(json.dumps({"receipts": recs, "threads": 1}, indent=2))
    print("wrote", path)
    return 0 if all(r.get("pith_ok") and r.get("ripser_ok") for r in recs) else 1


if __name__ == "__main__":
    sys.exit(main())
