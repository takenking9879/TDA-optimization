#!/usr/bin/env python3
"""1-thread Dionysus 2 explicit VR oracle vs PITH auto and Ripser.

Does not vendor Dionysus. Requires `pip install dionysus` (BSD wheel).
Empirical, not a theorem. Does not retune τ.

`fill_rips` materializes the VR skeleton; homology dim k uses skeleton k+1.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import blobs, circle_noisy, sphere, torus, uniform, write_csv  # noqa: E402
from run_suite import PITH, RIPSER, parse_pith_text, parse_ripser, run_cmd  # noqa: E402
from run_wave85 import figure8  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 20

try:
    import dionysus  # type: ignore
except Exception as e:
    dionysus = None
    IMPORT_ERR = str(e)
else:
    IMPORT_ERR = None

os.environ["OMP_NUM_THREADS"] = "1"


def _dionysus_worker(csv_path: str, T: float, maxdim: int) -> None:
    pts = np.loadtxt(csv_path, delimiter=",")
    skel = int(maxdim) + 1
    filt = dionysus.fill_rips(pts, skel, float(T))
    red = dionysus.homology_persistence(filt, prime=2)
    dgms = dionysus.init_diagrams(red, filt)
    h1 = list(dgms[1]) if len(dgms) > 1 else []
    ess1 = 0
    for pt in h1:
        death = float(pt.death)
        if not np.isfinite(death) or death > 1e20:
            ess1 += 1
    print(
        json.dumps(
            {
                "ess1": ess1,
                "n_h1": int(len(h1)),
                "n_simplices": int(len(filt)),
            }
        )
    )


def run_dionysus(csv_path: Path, T: float, maxdim: int):
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
        "n_simplices": payload.get("n_simplices"),
        "method": "dionysus:fill_rips+homology_persistence",
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
    if dionysus is None:
        print("dionysus not importable:", IMPORT_ERR, file=sys.stderr)
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
        path = CLOUDS / f"dionysus_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"Dionysus {name} n={n} ...", flush=True)
        drec = run_dionysus(path, T, maxdim)
        print(
            f"  dionysus {drec.get('wall_s')} ess1={drec.get('ess1')} "
            f"simplices={drec.get('n_simplices')} {drec.get('error') or ''}",
            flush=True,
        )
        prec = run_pith(path, T, maxdim)
        print(f"  pith {prec.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        ratio_r = ratio_p = None
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
                "dionysus": drec,
                "pith": prec,
                "ripser": rrec,
                "ripser_over_dionysus": ratio_r,
                "dionysus_over_pith": ratio_p,
                "threads": THREADS,
            }
        )
    payload = {
        "note": (
            "dionysus 2.2.3 oracle, 1 thread, not vendored. "
            "Explicit fill_rips + homology_persistence(prime=2)."
        ),
        "dionysus_version": "2.2.3",
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "dionysus.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--worker":
        if dionysus is None:
            raise SystemExit(IMPORT_ERR or "dionysus missing")
        _dionysus_worker(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]))
        raise SystemExit(0)
    sys.exit(main())
