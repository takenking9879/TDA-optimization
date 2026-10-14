#!/usr/bin/env python3
"""I326: HomCloud 5.4.0 leftover oracle vs PITH auto and C++ Ripser.

Does not vendor HomCloud (GPL). Default VR is a Python Ripser wrap
(`simplicial=False`). `simplicial=True` + `phat-twist` is PHAT on an
explicit 2-skeleton. Empirical, not a theorem. Does not retune τ.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (  # noqa: E402
    circle_noisy,
    figure8,
    torus,
    uniform,
    write_csv,
)
from run_suite import PITH, RIPSER, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 20

try:
    import homcloud.interface as hc  # type: ignore
except Exception as e:
    hc = None
    IMPORT_ERR = str(e)
else:
    IMPORT_ERR = None

os.environ["OMP_NUM_THREADS"] = "1"


def _dist(pts: np.ndarray) -> np.ndarray:
    diff = pts[:, None, :] - pts[None, :, :]
    return np.sqrt(np.einsum("ijk,ijk->ij", diff, diff), dtype=np.float64)


def _homcloud_worker(csv_path: str, T: float, maxdim: int, kind: str) -> None:
    pts = np.loadtxt(csv_path, delimiter=",")
    D = _dist(pts)
    if kind == "ripser":
        pdl = hc.PDList.from_rips_filtration(
            D, int(maxdim), maxvalue=float(T), simplicial=False
        )
        method = "homcloud:ripser"
    elif kind == "phat":
        pdl = hc.PDList.from_rips_filtration(
            D,
            int(maxdim),
            maxvalue=float(T),
            simplicial=True,
            algorithm="phat-twist",
        )
        method = "homcloud:phat-twist"
    else:
        raise SystemExit(f"unknown kind {kind}")
    pd1 = pdl.dth_diagram(1) if int(maxdim) >= 1 else None
    ess1 = 0
    n_h1 = 0
    if pd1 is not None:
        ess = getattr(pd1, "essential_births", None)
        ess1 = int(len(ess)) if ess is not None else 0
        n_h1 = int(len(list(pd1.pairs()))) + ess1
    print(json.dumps({"ess1": ess1, "n_h1": n_h1, "method": method}))


def run_homcloud(csv_path: Path, T: float, maxdim: int, kind: str):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(csv_path),
        str(T),
        str(maxdim),
        kind,
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
        "n_h1": payload.get("n_h1"),
        "method": payload.get("method") or f"homcloud:{kind}",
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
        return {
            "ok": False,
            "error": str(e),
            "wall_s": None,
            "timed_out": "timed out" in str(e).lower(),
        }


def run_ripser(path: Path, T: float, maxdim: int):
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
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        parse_ripser(out)
        return {"ok": True, "wall_s": dt, "threads_used": 1}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "wall_s": None,
            "timed_out": "timed out" in str(e).lower(),
        }


def _ratio(a, b):
    if a and b and a.get("ok") and b.get("ok") and a.get("wall_s") and b.get("wall_s"):
        return a["wall_s"] / b["wall_s"]
    return None


def main() -> int:
    if hc is None:
        print("homcloud not importable:", IMPORT_ERR, file=sys.stderr)
        return 2
    rng = np.random.default_rng(14)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    default_cases = [
        ("figure8", 200, 1.1, 1, lambda: figure8(200, rng)),
        ("figure8", 2000, 1.1, 1, lambda: figure8(2000, rng)),
        ("circle_noisy", 400, 1.5, 1, lambda: circle_noisy(400, rng)),
        ("uniform2", 2000, 0.35, 1, lambda: uniform(2000, 2, rng)),
        ("torus", 1000, 1.6, 1, lambda: torus(1000, rng)),
    ]
    phat_cases = [
        ("figure8", 80, 1.1, 1, lambda: figure8(80, rng)),
        ("figure8", 200, 1.1, 1, lambda: figure8(200, rng)),
        ("circle_noisy", 400, 1.5, 1, lambda: circle_noisy(400, rng)),
    ]
    rows = []
    for name, n, T, maxdim, maker in default_cases:
        path = CLOUDS / f"homcloud_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"HomCloud-ripser {name} n={n} ...", flush=True)
        hrec = run_homcloud(path, T, maxdim, "ripser")
        print(
            f"  homcloud {hrec.get('wall_s')} ess1={hrec.get('ess1')} {hrec.get('error') or ''}",
            flush=True,
        )
        prec = run_pith(path, T, maxdim)
        print(f"  pith {prec.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "kind": "ripser",
                "homcloud": hrec,
                "pith": prec,
                "ripser": rrec,
                "ripser_over_homcloud": _ratio(rrec, hrec),
                "homcloud_over_pith": _ratio(hrec, prec),
                "threads": THREADS,
            }
        )
    for name, n, T, maxdim, maker in phat_cases:
        path = CLOUDS / f"homcloud_phat_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"HomCloud-phat {name} n={n} ...", flush=True)
        hrec = run_homcloud(path, T, maxdim, "phat")
        print(
            f"  phat {hrec.get('wall_s')} ess1={hrec.get('ess1')} {hrec.get('error') or ''}",
            flush=True,
        )
        prec = run_pith(path, T, maxdim)
        print(f"  pith {prec.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "kind": "phat-twist",
                "homcloud": hrec,
                "pith": prec,
                "ripser": rrec,
                "ripser_over_homcloud": _ratio(rrec, hrec),
                "homcloud_over_pith": _ratio(hrec, prec),
                "threads": THREADS,
            }
        )
    payload = {
        "note": (
            "homcloud 5.4.0 oracle, 1 thread, GPL, not vendored. "
            "Default from_rips_filtration is Python ripser. "
            "simplicial=True algorithm=phat-twist is PHAT on an explicit complex."
        ),
        "homcloud_version": "5.4.0",
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "homcloud.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 6 and sys.argv[1] == "--worker":
        if hc is None:
            raise SystemExit(IMPORT_ERR or "homcloud missing")
        _homcloud_worker(sys.argv[2], float(sys.argv[3]), int(sys.argv[4]), sys.argv[5])
        raise SystemExit(0)
    sys.exit(main())
