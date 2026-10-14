#!/usr/bin/env python3
"""1-thread Dory (pydory oracle) vs PITH auto and Ripser on leftover families.

Does not vendor Dory. Requires `pip install pydory` (OpenMP build).
Empirical, not a theorem. Does not retune τ.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import blobs, circle_noisy, figure8, sphere, torus, uniform, write_csv  # noqa: E402
from run_suite import PITH, RIPSER, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 20

try:
    import pydory  # type: ignore
except Exception as e:
    pydory = None
    IMPORT_ERR = str(e)
else:
    IMPORT_ERR = None

os.environ["OMP_NUM_THREADS"] = "1"


def ess_from_dory_h1(path: Path) -> int:
    if not path.exists():
        return 0
    n = 0
    for line in path.read_text().splitlines():
        parts = [p.strip() for p in line.replace(",", " ").split() if p.strip()]
        if len(parts) < 2:
            continue
        death = float(parts[1])
        if death < 0:
            n += 1
    return n


def _dory_worker(csv_path: str, T: float, maxdim: int, prefix: str) -> None:
    os.environ["OMP_NUM_THREADS"] = "1"
    pydory.compute_PH(
        csv_path,
        0.0,
        float(T),
        1,
        THREADS,
        prefix + "_",
        int(maxdim),
        0,
        0,
        0.0,
        1,
        1000,
        100,
    )


def run_dory(csv_path: Path, T: float, maxdim: int, prefix: Path):
    prefix.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(csv_path),
        str(T),
        str(maxdim),
        str(prefix),
    ]
    try:
        _, dt, _ = run_cmd(cmd, BUDGET_S)
        err = None
    except Exception as e:
        err = str(e)
        dt = None
    timed_out = err is not None and "timed out" in (err or "").lower()
    h1 = prefix.parent / (prefix.name + "_H1_pers_data.txt")
    return {
        "ok": err is None,
        "error": err,
        "timed_out": timed_out,
        "wall_s": None if err else dt,
        "threads_used": THREADS,
        "ess1": ess_from_dory_h1(h1) if err is None else None,
        "method": "dory:pydory",
    }


def run_pith(path: Path, T: float, maxdim: int):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        "exact",
        "--engine",
        "auto",
        "--threads",
        "1",
        "--no-enclosing",
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        _, c = parse_pith_text(out)
        return {"ok": True, "wall_s": dt, "pipeline": c.get("pipeline"), "threads_used": 1}
    except Exception as e:
        return {"ok": False, "error": str(e), "wall_s": None, "timed_out": "timed out" in str(e).lower()}


def run_ripser(path: Path, T: float, maxdim: int):
    cmd = [str(RIPSER), "--format", "point-cloud", "--dim", str(maxdim), "--threshold", str(T), str(path)]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        parse_ripser(out)
        return {"ok": True, "wall_s": dt, "threads_used": 1}
    except Exception as e:
        return {"ok": False, "error": str(e), "wall_s": None, "timed_out": "timed out" in str(e).lower()}


def main() -> int:
    if pydory is None:
        print("pydory not importable:", IMPORT_ERR, file=sys.stderr)
        return 2
    rng = np.random.default_rng(14)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("circle_noisy", 400, 1.5, 1, lambda: circle_noisy(400, rng)),
        ("circle_noisy", 1000, 1.5, 1, lambda: circle_noisy(1000, rng)),
        ("figure8", 1000, 1.1, 1, lambda: figure8(1000, rng)),
        ("figure8", 2000, 1.1, 1, lambda: figure8(2000, rng)),
        ("torus", 1000, 1.6, 1, lambda: torus(1000, rng)),
        ("uniform2", 2000, 0.35, 1, lambda: uniform(2000, 2, rng)),
        ("sphere", 400, 1.4, 2, lambda: sphere(400, rng)),
        ("blobs", 2000, 1.0, 1, lambda: blobs(2000, rng)),
    ]
    rows = []
    for name, n, T, maxdim, maker in cases:
        path = CLOUDS / f"dory_{name}_n{n}.csv"
        write_csv(path, maker())
        prefix = OUT / "dory_out" / f"{name}_n{n}"
        print(f"Dory {name} n={n} ...", flush=True)
        drec = run_dory(path, T, maxdim, prefix)
        print(f"  dory {drec.get('wall_s')} ess1={drec.get('ess1')} {drec.get('error') or ''}", flush=True)
        prec = run_pith(path, T, maxdim)
        print(f"  pith {prec.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        ratio_r = None
        ratio_p = None
        if drec.get("ok") and rrec.get("ok") and drec.get("wall_s") and rrec.get("wall_s"):
            ratio_r = rrec["wall_s"] / drec["wall_s"]
        if prec.get("ok") and drec.get("ok") and prec.get("wall_s") and drec.get("wall_s"):
            ratio_p = drec["wall_s"] / prec["wall_s"]
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "dory": drec,
                "pith": prec,
                "ripser": rrec,
                "ripser_over_dory": ratio_r,
                "dory_over_pith": ratio_p,
                "threads": THREADS,
            }
        )
    payload = {
        "note": "pydory 1.1.137 oracle, 1 thread, not vendored. Same pairing class as VR.",
        "pydory_version": "1.1.137",
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    dest = OUT / "dory.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 6 and sys.argv[1] == "--worker":
        if pydory is None:
            raise SystemExit(IMPORT_ERR or "pydory missing")
        _dory_worker(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
        raise SystemExit(0)
    sys.exit(main())
