#!/usr/bin/env python3
"""Leftover H1 ratio vs n on post-freeze linked_circles.

linked_circles n=1200 was 10.7× (Ripser 0.48 s) on seed 23. Scale n
to see if that holds. Also sheared_loops at sizes where Ripser is
measurable. τ frozen. No leftover-skip edits.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import linked_circles, sheared_loops  # noqa: E402
from run_consolidation import local_exp, run_ripser  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER  # noqa: E402

OUT = BENCH / "results" / "consolidation"

SERIES = [
    ("linked_circles", linked_circles, 1.3, 1, [800, 1200, 2000, 3000, 4000]),
    ("sheared_loops", sheared_loops, 1.3, 1, [800, 1200, 2000, 3000, 4000, 5000]),
]


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rng = np.random.default_rng(23)
    recs = []
    for name, fn, T, dim, ns in SERIES:
        if only and name != only:
            continue
        prev = None
        for n in ns:
            path = cloud(f"link_{name}", n, fn, rng)
            print(f"LINK-N {name} n={n}", flush=True)
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
                "cpu_s": pith.get("cpu_s"),
                "threads": 1,
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
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "linked_ratio_n.json"
    if only and path.exists():
        prev = json.loads(path.read_text())
        keep = [r for r in prev.get("receipts") or [] if r.get("name") != only]
        recs = keep + recs
    ge10 = [r for r in recs if r.get("ratio") and r["ratio"] >= 10]
    out = {
        "note": (
            "Seed 23. Post-freeze leftover families scaled in n. "
            "τ frozen. Not a pairing-algorithm claim."
        ),
        "n": len(recs),
        "n_ratio_ge10": len(ge10),
        "receipts": recs,
    }
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} {len(ge10)}/{len(recs)} ≥10×", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
