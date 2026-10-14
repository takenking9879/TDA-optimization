#!/usr/bin/env python3
"""Check that --estimate wall_kind matches measured construct/collapse/reduce.

Does not retune τ. Small-n noise (<1 ms) is skipped. A mismatch is a
miss, not a retune signal.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_consolidation import run_estimate  # noqa: E402
from run_suite import PITH  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BASE = json.loads((OUT / "baselines.json").read_text())


def measured_kind(run: dict) -> str | None:
    met = float(run.get("metric_ms") or 0)
    col = float(run.get("collapse_ms") or 0)
    red = float(run.get("reduce_ms") or 0)
    mx = max(met, col, red)
    if mx < 1.0:
        return None
    if col >= red and col >= met:
        return "collapse"
    if red >= col and red >= met:
        return "leftover"
    return "construction"


def stem(name: str) -> str:
    return name.replace("_sparse", "").replace("_dense", "")


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    recs = []
    for r in BASE.get("comparisons") or []:
        run = (r.get("runs") or {}).get("pith_exact_t1") or {}
        if not (run.get("ok") and r.get("n", 0) >= 400):
            continue
        mk = measured_kind(run)
        if mk is None:
            continue
        path = CLOUDS / f"{stem(r['name'])}_n{r['n']}.csv"
        if not path.exists():
            continue
        est = run_estimate(path, r["T"], r.get("maxdim", 1), timeout=15)
        got = est.get("wall_kind")
        mode = est.get("mode_recommended")
        # Scale/sparse walls are construction; do not compare to exact counters.
        expect = "construction" if mode in ("scale", "sparse") else mk
        rec = {
            "name": r["name"],
            "n": r["n"],
            "T": r["T"],
            "maxdim": r.get("maxdim", 1),
            "measured": mk,
            "estimate": got,
            "mode_recommended": mode,
            "regime": est.get("residual_regime"),
            "agree": got == expect,
            "collapse_ms": run.get("collapse_ms"),
            "reduce_ms": run.get("reduce_ms"),
            "metric_ms": run.get("metric_ms"),
        }
        recs.append(rec)
        print(
            f"WALL {r['name']} n={r['n']} measured={mk} estimate={got} "
            f"agree={rec['agree']} regime={est.get('residual_regime')}",
            flush=True,
        )
    n_ok = sum(1 for r in recs if r["agree"])
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "wall_kind.json"
    path.write_text(
        json.dumps(
            {
                "receipts": recs,
                "n": len(recs),
                "n_agree": n_ok,
                "note": "Compare estimate wall_kind to the largest of metric/collapse/reduce. τ frozen.",
            },
            indent=2,
        )
    )
    print(f"wrote {path} {n_ok}/{len(recs)} agree")
    return 0 if recs and n_ok == len(recs) else 1


if __name__ == "__main__":
    sys.exit(main())
