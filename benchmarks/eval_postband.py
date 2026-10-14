#!/usr/bin/env python3
"""Post-16× leftover-band stress pack.

offset_rings was added after leftover H1 hi_mult=16 was frozen.
Measures leftover H1 vs Ripser along n and checks --estimate bands.
τ / hi_mult / mode_rec rules unchanged. Seed 29. 1 thread.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import offset_rings  # noqa: E402
from run_consolidation import local_exp, run_estimate, run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402

OUT = BENCH / "results" / "consolidation"

SERIES = [
    ("offset_rings", offset_rings, 1.2, 1, [800, 2000, 3000, 4000]),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(29)
    recs = []
    prev = None
    for name, fn, T, dim, ns in SERIES:
        for n in ns:
            path = cloud(f"postband_{name}", n, fn, rng)
            print(f"POSTBAND {name} n={n}", flush=True)
            est = run_estimate(path, T, dim, timeout=15)
            pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=20)
            rip = run_ripser(path, T, dim, timeout=30)
            pw, rw = pith.get("wall_s"), rip.get("wall_s")
            ratio = (rw / pw) if pw and rw else None
            lo, hi, mid = (
                est.get("est_runtime_lo_s"),
                est.get("est_runtime_hi_s"),
                est.get("est_runtime_s"),
            )
            rec_mode = est.get("mode_recommended")
            wall = pw if rec_mode == "exact" else None
            in_band = (
                lo is not None and hi is not None and wall is not None and lo <= wall <= hi
            )
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
                "residual_frac": pith.get("residual_frac"),
                "reduce_ms": pith.get("reduce_ms"),
                "cpu_s": pith.get("cpu_s"),
                "threads": 1,
                "mode_recommended": rec_mode,
                "est_runtime_s": mid,
                "est_runtime_lo_s": lo,
                "est_runtime_hi_s": hi,
                "in_band": in_band,
                "p_pith": None,
                "p_ripser": None,
            }
            if prev and pw and prev.get("pith_s"):
                rec["p_pith"] = local_exp(prev["n"], prev["pith_s"], n, pw)
            if prev and rw and prev.get("ripser_s"):
                rec["p_ripser"] = local_exp(prev["n"], prev["ripser_s"], n, rw)
            recs.append(rec)
            print(
                f"  pith={pw} ripser={rw} ratio={ratio} rec={rec_mode} "
                f"band=[{lo},{hi}] in_band={in_band} pipe={rec['pipeline']}",
                flush=True,
            )
            if pith.get("ok"):
                prev = rec
            if rec["ripser_timeout"]:
                break
    ge10 = [r for r in recs if r.get("ratio") and r["ratio"] >= 10]
    scored = [r for r in recs if r.get("in_band") is not None]
    n_in = sum(1 for r in scored if r["in_band"])
    OUT.mkdir(parents=True, exist_ok=True)
    out = {
        "note": (
            "Seed 29. offset_rings chosen after leftover H1 hi_mult=16. "
            "τ / hi_mult / mode_rec frozen. Not a pairing-algorithm claim."
        ),
        "n": len(recs),
        "n_ratio_ge10": len(ge10),
        "n_scored_band": len(scored),
        "n_in_band": n_in,
        "receipts": recs,
    }
    path = OUT / "postband.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} {len(ge10)}/{len(recs)} ≥10×  {n_in}/{len(scored)} in band")
    return 0


if __name__ == "__main__":
    sys.exit(main())
