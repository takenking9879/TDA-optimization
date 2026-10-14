#!/usr/bin/env python3
"""High-d control: uniform10 last-OK / first-fail (12 s, 1 thread).

No Delaunay scale path in d=10. Records exact / sparse / Ripser / estimate
and the fat-H2 auto refuse. Does not retune τ.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import uniform, write_csv  # noqa: E402
from run_consolidation import run_estimate  # noqa: E402
from run_suite import PITH, RIPSER, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
BUDGET_S = 12
T = 1.8


def run_pith_mode(path: Path, maxdim: int, mode: str):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        mode,
        "--engine",
        "auto",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        _, c = parse_pith_text(out)
        return {
            "ok": True,
            "wall_s": dt,
            "pipeline": c.get("pipeline"),
            "n_edges": c.get("edges") or c.get("n_edges"),
            "threads_used": 1,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "wall_s": None,
            "timed_out": "timed out" in str(e).lower(),
            "returncode": 3 if "refusing" in str(e).lower() else None,
        }


def run_auto(path: Path, maxdim: int):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        "auto",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        _, c = parse_pith_text(out)
        return {"ok": True, "wall_s": dt, "pipeline": c.get("pipeline"), "refused": False}
    except Exception as e:
        err = str(e)
        return {
            "ok": False,
            "error": err,
            "wall_s": None,
            "timed_out": "timed out" in err.lower(),
            "refused": "refusing" in err.lower() or "auto_will_run" in err.lower(),
        }


def run_ripser(path: Path, maxdim: int):
    cmd = [
        str(RIPSER),
        "--format",
        "point-cloud",
        "--dim",
        str(maxdim),
        "--threshold",
        str(T),
        str(path),
    ]
    try:
        _, dt, _ = run_cmd(cmd, BUDGET_S)
        return {"ok": True, "wall_s": dt, "threads_used": 1}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "wall_s": None,
            "timed_out": "timed out" in str(e).lower(),
        }


def main() -> int:
    rng = np.random.default_rng(10)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    rows = []
    first_fail = {}
    for n in (80, 200, 400, 800, 1600, 4000, 8000):
        path = CLOUDS / f"uniform10_n{n}.csv"
        write_csv(path, uniform(n, 10, rng))
        print(f"uniform10 n={n} maxdim=1 ...", flush=True)
        est = run_estimate(path, T, 1, timeout=BUDGET_S)
        exact = (
            {"ok": False, "skipped_after_fail": True}
            if "exact" in first_fail
            else run_pith_mode(path, 1, "exact")
        )
        sparse = (
            {"ok": False, "skipped_after_fail": True}
            if "sparse" in first_fail
            else run_pith_mode(path, 1, "sparse")
        )
        rip = (
            {"ok": False, "skipped_after_fail": True}
            if "ripser" in first_fail
            else run_ripser(path, 1)
        )
        print(
            f"  est mode={est.get('mode_recommended')} engine={est.get('engine_recommended')} "
            f"auto_will_run={est.get('auto_will_run')}",
            flush=True,
        )
        print(
            f"  exact={exact.get('wall_s')} sparse={sparse.get('wall_s')} ripser={rip.get('wall_s')}",
            flush=True,
        )
        rec = {
            "name": "uniform10",
            "n": n,
            "T": T,
            "maxdim": 1,
            "d": 10,
            "estimate": {
                k: est.get(k)
                for k in (
                    "mode_recommended",
                    "engine_recommended",
                    "auto_will_run",
                    "exact_feasible",
                    "residual_regime",
                    "edge_frac_probe",
                    "residual_frac_probe",
                    "est_edges",
                    "est_residual_edges",
                    "est_runtime_s",
                    "reason",
                )
            },
            "exact": exact,
            "sparse": sparse,
            "ripser": rip,
            "threads": 1,
            "budget_s": BUDGET_S,
        }
        rows.append(rec)
        for meth, rec_m in (("exact", exact), ("sparse", sparse), ("ripser", rip)):
            if not rec_m.get("ok") and meth not in first_fail:
                first_fail[meth] = {"n": n, "timed_out": bool(rec_m.get("timed_out"))}
        if all(m in first_fail for m in ("exact", "sparse", "ripser")):
            break

    path = CLOUDS / "uniform10_n250.csv"
    write_csv(path, uniform(250, 10, rng))
    print("uniform10 n=250 maxdim=2 (expect refuse) ...", flush=True)
    est2 = run_estimate(path, T, 2, timeout=BUDGET_S)
    auto2 = run_auto(path, 2)
    print(
        f"  est mode={est2.get('mode_recommended')} auto_will_run={est2.get('auto_will_run')} "
        f"auto refused={auto2.get('refused')} rc_err={auto2.get('error')}",
        flush=True,
    )
    refuse = {
        "name": "uniform10",
        "n": 250,
        "T": T,
        "maxdim": 2,
        "d": 10,
        "estimate": {
            k: est2.get(k)
            for k in ("mode_recommended", "engine_recommended", "auto_will_run", "regime")
        },
        "auto": auto2,
        "expect_refuse": True,
    }

    payload = {
        "note": (
            "High-d Euclidean control, d=10. No --mode scale. "
            "12 s, 1 thread. T=1.8 for H1 and fat-H2 refuse."
        ),
        "threads": 1,
        "budget_s": BUDGET_S,
        "first_fail": first_fail,
        "receipts": rows,
        "fat_h2": refuse,
    }
    dest = OUT / "uniform10.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
