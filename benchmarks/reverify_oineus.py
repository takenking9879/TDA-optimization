#!/usr/bin/env python3
"""1-thread Oineus VR oracle vs PITH auto and Ripser on leftover families.

Does not vendor Oineus. Requires `pip install oineus` (BSD wheel).
Empirical, not a theorem. Does not retune τ.

Oineus `max_dim` is the largest *simplex* dimension, so H1 uses max_dim=2.
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
    import oineus  # type: ignore
except Exception as e:
    oineus = None
    IMPORT_ERR = str(e)
else:
    IMPORT_ERR = None

os.environ["OMP_NUM_THREADS"] = "1"


def _oineus_worker(csv_path: str, T: float, maxdim: int) -> None:
    pts = np.loadtxt(csv_path, delimiter=",")
    params = oineus.ReductionParams()
    params.n_threads = THREADS
    # simplex dim = homology dim + 1
    dgs = oineus.compute_diagrams_vr(pts, False, int(maxdim) + 1, float(T), params, True, True)
    h1 = np.asarray(dgs[1]) if len(dgs) > 1 else np.zeros((0, 2))
    finite = np.isfinite(h1[:, 1]) if len(h1) else np.array([], dtype=bool)
    ess1 = int((~finite).sum()) if len(h1) else 0
    print(json.dumps({"ess1": ess1, "n_h1": int(len(h1))}))


def run_oineus(csv_path: Path, T: float, maxdim: int):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(csv_path),
        str(T),
        str(maxdim),
    ]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        err = None
        payload = json.loads(out.strip().splitlines()[-1])
    except Exception as e:
        err = str(e)
        dt = None
        payload = {}
    return {
        "ok": err is None,
        "error": err,
        "timed_out": err is not None and "timed out" in (err or "").lower(),
        "wall_s": None if err else dt,
        "threads_used": THREADS,
        "ess1": payload.get("ess1"),
        "method": "oineus:compute_diagrams_vr",
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
    if oineus is None:
        print("oineus not importable:", IMPORT_ERR, file=sys.stderr)
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
        path = CLOUDS / f"oineus_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"Oineus {name} n={n} ...", flush=True)
        orec = run_oineus(path, T, maxdim)
        print(f"  oineus {orec.get('wall_s')} ess1={orec.get('ess1')} {orec.get('error') or ''}", flush=True)
        prec = run_pith(path, T, maxdim)
        print(f"  pith {prec.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        ratio_r = ratio_p = None
        if orec.get("ok") and rrec.get("ok") and orec.get("wall_s") and rrec.get("wall_s"):
            ratio_r = rrec["wall_s"] / orec["wall_s"]
        if prec.get("ok") and orec.get("ok") and prec.get("wall_s") and orec.get("wall_s"):
            ratio_p = orec["wall_s"] / prec["wall_s"]
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "oineus": orec,
                "pith": prec,
                "ripser": rrec,
                "ripser_over_oineus": ratio_r,
                "oineus_over_pith": ratio_p,
                "threads": THREADS,
            }
        )
    payload = {
        "note": "oineus 0.9.39 oracle, 1 thread, not vendored. In-order VR generation + lock-free reduce.",
        "oineus_version": "0.9.39",
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "oineus.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--worker":
        if oineus is None:
            raise SystemExit(IMPORT_ERR or "oineus missing")
        _oineus_worker(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]))
        raise SystemExit(0)
    sys.exit(main())
