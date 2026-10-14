#!/usr/bin/env python3
"""Compare --estimate bands to measured walls. Does not retune τ."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import GENERATORS, write_csv  # noqa: E402
from run_consolidation import run_estimate  # noqa: E402
from run_suite import PITH  # noqa: E402
import numpy as np

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"

GENS = dict(GENERATORS)

def _load(name: str) -> dict:
    path = OUT / name
    return json.loads(path.read_text()) if path.exists() else {}


def collect_measured() -> list[dict]:
    rows = []
    base = _load("baselines.json")
    for r in base.get("comparisons") or []:
        run = (r.get("runs") or {}).get("pith_exact_t1") or {}
        if run.get("ok") and run.get("wall_s"):
            rows.append(
                {
                    "name": r["name"],
                    "n": r["n"],
                    "T": r["T"],
                    "maxdim": r.get("maxdim", 1),
                    "mode": "exact",
                    "wall_s": run["wall_s"],
                    "source": "baselines",
                }
            )
        sc = (r.get("runs") or {}).get("pith_scale_t1") or {}
        if sc.get("ok") and sc.get("wall_s"):
            rows.append(
                {
                    "name": r["name"],
                    "n": r["n"],
                    "T": r["T"],
                    "maxdim": r.get("maxdim", 1),
                    "mode": "scale",
                    "wall_s": sc["wall_s"],
                    "source": "baselines",
                }
            )
    sl = _load("sparse_limits.json")
    for t in sl.get("sparse") or []:
        walls = t.get("walls") or {}
        for mode in ("exact", "scale", "sparse"):
            if walls.get(mode):
                rows.append(
                    {
                        "name": t["name"],
                        "n": t["n"],
                        "T": t["T"],
                        "maxdim": t.get("maxdim", 1),
                        "mode": mode,
                        "wall_s": walls[mode],
                        "source": "sparse_limits",
                    }
                )
    ss = _load("sparse_scale.json")
    for r in ss.get("series") or []:
        if r.get("ok") and r.get("wall_s"):
            rows.append(
                {
                    "name": r["name"],
                    "n": r["n"],
                    "T": r["T"],
                    "maxdim": r.get("maxdim", 1),
                    "mode": r.get("mode"),
                    "wall_s": r["wall_s"],
                    "source": "sparse_scale",
                }
            )
    lim = _load("limits.json")
    for r in lim.get("series") or lim.get("scaling") or []:
        for mode, key in (("exact", "pith_exact"), ("scale", "pith_scale")):
            run = (r.get("runs") or {}).get(key) or {}
            if run.get("ok") and run.get("wall_s"):
                rows.append(
                    {
                        "name": r.get("name"),
                        "n": r.get("n"),
                        "T": r.get("T"),
                        "maxdim": r.get("maxdim", 1),
                        "mode": mode,
                        "wall_s": run["wall_s"],
                        "source": "limits",
                    }
                )
    for pack in (
        "leftover_10x.json",
        "leftover_ratio_n.json",
        "leftover_heldout.json",
        "leftover_miss_n.json",
        "linked_ratio_n.json",
    ):
        src = pack.replace(".json", "")
        for r in _load(pack).get("receipts") or []:
            if r.get("pith_ok") and r.get("pith_s"):
                rows.append(
                    {
                        "name": r.get("name"),
                        "n": r.get("n"),
                        "T": r.get("T"),
                        "maxdim": r.get("maxdim", 1),
                        "mode": "exact",
                        "wall_s": r["pith_s"],
                        "source": src,
                    }
                )
    for r in _load("postfreeze.json").get("receipts") or []:
        if r.get("exact_ok") and r.get("exact_s"):
            rows.append(
                {
                    "name": r.get("name"),
                    "n": r.get("n"),
                    "T": r.get("T"),
                    "maxdim": r.get("maxdim", 1),
                    "mode": "exact",
                    "wall_s": r["exact_s"],
                    "source": "postfreeze",
                }
            )
    fat = _load("fat_h2.json")
    for r in fat.get("series") or []:
        runs = r.get("runs") or {}
        for mode, key in (("exact", "exact_auto"), ("scale", "scale")):
            run = runs.get(key) or {}
            if run.get("ok") and run.get("wall_s"):
                rows.append(
                    {
                        "name": r.get("name"),
                        "n": r.get("n"),
                        "T": r.get("T"),
                        "maxdim": r.get("maxdim", 2),
                        "mode": mode,
                        "wall_s": run["wall_s"],
                        "source": "fat_h2",
                    }
                )
    # Prefer later sources (sparse_scale over sparse_limits over baselines).
    best = {}
    for r in rows:
        key = (r["name"], r["n"], r["T"], r["maxdim"], r["mode"])
        best[key] = r
    return list(best.values())


def main() -> int:
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    measured = collect_measured()
    by_cloud = {}
    for r in measured:
        by_cloud.setdefault((r["name"], r["n"], r["T"], r["maxdim"]), []).append(r)

    rng = np.random.default_rng(3)
    recs = []
    for (name, n, T, maxdim), walls in sorted(by_cloud.items()):
        path = CLOUDS / f"{name}_n{n}.csv"
        if not path.exists():
            fn = GENS.get(name)
            if fn is None:
                continue
            write_csv(path, fn(int(n), rng))
        est = run_estimate(path, T, maxdim, timeout=15)
        if est.get("error"):
            recs.append({"name": name, "n": n, "T": T, "maxdim": maxdim, "error": est["error"]})
            continue
        rec = {
            "name": name,
            "n": n,
            "T": T,
            "maxdim": maxdim,
            "mode_recommended": est.get("mode_recommended"),
            "engine_recommended": est.get("engine_recommended"),
            "auto_will_run": est.get("auto_will_run"),
            "est_runtime_s": est.get("est_runtime_s"),
            "est_runtime_lo_s": est.get("est_runtime_lo_s"),
            "est_runtime_hi_s": est.get("est_runtime_hi_s"),
            "growth_p": est.get("growth_p"),
            "leaving_cheap_regime": est.get("leaving_cheap_regime"),
            "exact_feasible": est.get("exact_feasible"),
            "residual_regime": est.get("residual_regime"),
            "walls": {w["mode"]: w["wall_s"] for w in walls},
        }
        rec_mode = rec["mode_recommended"]
        wall = rec["walls"].get(rec_mode)
        rec["measured_recommended_wall_s"] = wall
        lo, hi, mid = rec["est_runtime_lo_s"], rec["est_runtime_hi_s"], rec["est_runtime_s"]
        if wall is not None and lo is not None and hi is not None:
            rec["in_band"] = lo <= wall <= hi
            rec["ratio_actual_over_mid"] = wall / mid if mid else None
        elif rec_mode == "sparse" and rec.get("auto_will_run") is False:
            rec["in_band"] = True
            rec["refused"] = True
        else:
            rec["in_band"] = None
        recs.append(rec)
        flag = rec.get("in_band")
        print(
            f"{name} n={n} rec={rec_mode} wall={wall} "
            f"band=[{lo},{hi}] in_band={flag}",
            flush=True,
        )

    scored = [r for r in recs if r.get("in_band") is not None]
    n_in = sum(1 for r in scored if r["in_band"])
    OUT.mkdir(parents=True, exist_ok=True)
    out = {
        "receipts": recs,
        "n_scored": len(scored),
        "n_in_band": n_in,
        "note": "in_band compares the recommended-mode wall to est_runtime_lo/hi. τ unchanged.",
    }
    path = OUT / "estimate_accuracy.json"
    path.write_text(json.dumps(out, indent=2))
    print(f"wrote {path} {n_in}/{len(scored)} in band")
    return 0


if __name__ == "__main__":
    sys.exit(main())
