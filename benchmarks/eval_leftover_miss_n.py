#!/usr/bin/env python3
"""Ratio vs n on leftover misses where Ripser is not already cheap.

anisotropic_blob n=2000 was 5.5× (Ripser 0.48 s). grid_holes n=1600
was 3.2× but Ripser was 44 ms — retry at sizes where Ripser is >0.3 s.
Seed 19 to match leftover_heldout.json. τ frozen. No leftover skips.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import anisotropic_blob, grid_holes  # noqa: E402
from run_consolidation import local_exp, run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402

OUT = BENCH / "results" / "consolidation"

SERIES = [
    ("anisotropic_blob", anisotropic_blob, 2.5, 1, [2000, 4000, 6000, 8000]),
    ("grid_holes", grid_holes, 0.12, 1, [1600, 4000, 8000]),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(19)
    recs = []
    for name, fn, T, dim, ns in SERIES:
        prev = None
        for n in ns:
            path = cloud(f"miss_{name}", n, fn, rng)
            print(f"MISS-N {name} n={n}", flush=True)
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
                "residual_frac": pith.get("residual_frac"),
                "reduce_ms": pith.get("reduce_ms"),
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
                f"p_pith={rec['p_pith']} p_ripser={rec['p_ripser']} "
                f"pipe={rec['pipeline']}",
                flush=True,
            )
            if pith.get("ok"):
                prev = rec
            if rec["ripser_timeout"]:
                break
    ge10 = [r for r in recs if r.get("ratio") and r["ratio"] >= 10]
    out = {
        "note": (
            "Seed 19. Leftover misses from leftover_heldout.json, "
            "scaled in n. τ frozen. Not a pairing-algorithm claim."
        ),
        "n": len(recs),
        "n_ratio_ge10": len(ge10),
        "receipts": recs,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "leftover_miss_n.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} {len(ge10)}/{len(recs)} ≥10×", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
