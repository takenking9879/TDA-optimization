#!/usr/bin/env python3
"""Leftover exact-H1 ratio vs n. Does not retune τ or edit leftover skips.

Asks whether the 8× leftover families (uniform2, sphere H1) reach 10×
as n grows, which RedZeD's paper also flags as the weak unit-square case.
1 thread. Empirical, not a new pairing algorithm.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import figure8, sphere, uniform  # noqa: E402
from run_consolidation import local_exp, run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402

OUT = BENCH / "results" / "consolidation"

SERIES = [
    ("figure8", figure8, 1.1, 1, [1000, 2000, 3000]),
    ("uniform2", lambda n, r: uniform(n, 2, r), 0.35, 1, [2000, 3500, 5000, 7000]),
    ("sphere", sphere, 1.4, 1, [1000, 2000, 3000, 4000]),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    recs = []
    for name, fn, T, dim, ns in SERIES:
        prev = None
        for n in ns:
            path = cloud(name, n, fn, rng)
            print(f"RATIO-N {name} n={n}", flush=True)
            pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=20)
            rip = run_ripser(path, T, dim, timeout=30)
            pw, rw = pith.get("wall_s"), rip.get("wall_s")
            ratio = (rw / pw) if pw and rw else None
            rec = {
                "name": name,
                "n": n,
                "T": T,
                "pith_s": pw,
                "ripser_s": rw,
                "ratio": ratio,
                "pith_ok": pith.get("ok"),
                "ripser_ok": rip.get("ok"),
                "ripser_timeout": bool(
                    rip.get("error") and "timed out" in str(rip.get("error")).lower()
                ),
                "pipeline": pith.get("pipeline"),
                "reduce_ms": pith.get("reduce_ms"),
                "residual_frac": pith.get("residual_frac"),
                "p_pith": None,
                "p_ripser": None,
            }
            if prev and pw and prev.get("pith_s"):
                rec["p_pith"] = local_exp(prev["n"], prev["pith_s"], n, pw)
            if prev and rw and prev.get("ripser_s"):
                rec["p_ripser"] = local_exp(prev["n"], prev["ripser_s"], n, rw)
            recs.append(rec)
            print(
                f"  pith={pw} ripser={rw} ratio={ratio} "
                f"p_pith={rec['p_pith']} p_ripser={rec['p_ripser']}",
                flush=True,
            )
            if pith.get("ok"):
                prev = rec
            if rip.get("error") and "timed out" in str(rip.get("error")).lower():
                break
    ge10 = [r for r in recs if r.get("ratio") and r["ratio"] >= 10]
    out = {
        "note": (
            "1-thread leftover ratio vs n. Frozen leftover_10x.json pack is "
            "unchanged. Not a pairing-algorithm claim. τ frozen."
        ),
        "n": len(recs),
        "n_ratio_ge10": len(ge10),
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leftover_ratio_n.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} {len(ge10)}/{len(recs)} ≥10×", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
