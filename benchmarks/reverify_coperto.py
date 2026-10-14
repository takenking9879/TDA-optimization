#!/usr/bin/env python3
"""Coperto (quotient-cover) vs PITH scale/sparse/exact and Ripser.

Not exact VR. Leitão arXiv:2602.22784 claims a log-3 interleaving with VR
for any metric. `greedy=True` (library default) drops H1 on our clouds;
this runner uses greedy=False (exact tie-breaking of *their* complex).

Does not vendor Coperto. Requires `pip install coperto`. Does not retune τ.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import (
    figure8,  # noqa: E402
    blobs,
    circle_noisy,
    nested_loops,
    sphere,
    torus,
    uniform,
    write_csv,
)
from ph_metrics import ess  # noqa: E402
from run_consolidation_limits import topology_metrics  # noqa: E402
from run_suite import PITH, RIPSER, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 20

try:
    import coperto  # type: ignore
except Exception as e:
    coperto = None
    IMPORT_ERR = str(e)
else:
    IMPORT_ERR = None

os.environ["OMP_NUM_THREADS"] = "1"


def _bars_to_pairs(bars):
    pairs = []
    for b in bars:
        dim, birth, death = int(b[0]), float(b[1]), float(b[2])
        if not math.isfinite(death) or death > 1e20:
            death = math.inf
        pairs.append({"dim": dim, "birth": birth, "death": death})
    return pairs


def _coperto_worker(csv_path: str, maxdim: int, greedy: str) -> None:
    pts = np.loadtxt(csv_path, delimiter=",")
    greedy_b = greedy == "1"
    bars = coperto.persistent_homology(pts, max_dim=int(maxdim), greedy=greedy_b)
    tower = None
    try:
        tower = int(coperto.tower_size(pts, int(maxdim) + 1, greedy_b))
    except Exception:
        tower = None
    pairs = _bars_to_pairs(bars)
    payload = {
        "n_bars": len(pairs),
        "ess0": ess(pairs, 0),
        "ess1": ess(pairs, 1),
        "ess2": ess(pairs, 2) if int(maxdim) >= 2 else None,
        "n_h1": sum(1 for p in pairs if p["dim"] == 1),
        "tower_size": tower,
        "greedy": greedy_b,
        "pairs": pairs,
    }
    print(json.dumps(payload))


def run_coperto(csv_path: Path, maxdim: int, greedy: bool = False):
    cmd = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        str(csv_path),
        str(maxdim),
        "1" if greedy else "0",
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
        "ess0": payload.get("ess0"),
        "ess1": payload.get("ess1"),
        "ess2": payload.get("ess2"),
        "n_h1": payload.get("n_h1"),
        "tower_size": payload.get("tower_size"),
        "greedy": greedy,
        "pairs": payload.get("pairs"),
        "method": "coperto:persistent_homology",
    }


def run_pith(path: Path, T: float, maxdim: int, mode: str):
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
        pairs, c = parse_pith_text(out)
        return {
            "ok": True,
            "wall_s": dt,
            "pipeline": c.get("pipeline"),
            "threads_used": 1,
            "pairs": pairs,
            "ess1": ess(pairs, 1),
            "ess2": ess(pairs, 2) if maxdim >= 2 else None,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "wall_s": None, "timed_out": "timed out" in str(e).lower()}


def run_ripser(path: Path, T: float, maxdim: int):
    cmd = [str(RIPSER), "--format", "point-cloud", "--dim", str(maxdim), "--threshold", str(T), str(path)]
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs = parse_ripser(out)
        return {"ok": True, "wall_s": dt, "threads_used": 1, "pairs": pairs, "ess1": ess(pairs, 1)}
    except Exception as e:
        return {"ok": False, "error": str(e), "wall_s": None, "timed_out": "timed out" in str(e).lower()}


def _strip_pairs(rec):
    if isinstance(rec, dict):
        rec = dict(rec)
        rec.pop("pairs", None)
    return rec


def main() -> int:
    if coperto is None:
        print("coperto not importable:", IMPORT_ERR, file=sys.stderr)
        return 2
    rng = np.random.default_rng(14)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    # Control: library default greedy=True drops H1 on a circle.
    ctrl_path = CLOUDS / "coperto_ctrl_circle400.csv"
    write_csv(ctrl_path, circle_noisy(400, rng))
    greedy_bad = run_coperto(ctrl_path, 1, greedy=True)
    print(
        f"control greedy=True ess1={greedy_bad.get('ess1')} n_h1={greedy_bad.get('n_h1')} "
        f"{greedy_bad.get('error') or ''}",
        flush=True,
    )

    timing_cases = [
        ("circle_noisy", 400, 1.5, 1, lambda: circle_noisy(400, rng)),
        ("circle_noisy", 1000, 1.5, 1, lambda: circle_noisy(1000, rng)),
        ("figure8", 1000, 1.1, 1, lambda: figure8(1000, rng)),
        ("figure8", 2000, 1.1, 1, lambda: figure8(2000, rng)),
        ("figure8", 8000, 1.1, 1, lambda: figure8(8000, rng)),
        ("torus", 1000, 1.6, 1, lambda: torus(1000, rng)),
        ("uniform2", 2000, 0.35, 1, lambda: uniform(2000, 2, rng)),
        ("sphere", 400, 1.4, 2, lambda: sphere(400, rng)),
        ("blobs", 2000, 1.0, 1, lambda: blobs(2000, rng)),
    ]
    timing = []
    for name, n, T, maxdim, maker in timing_cases:
        path = CLOUDS / f"coperto_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"Coperto {name} n={n} ...", flush=True)
        crec = run_coperto(path, maxdim, greedy=False)
        print(
            f"  coperto {crec.get('wall_s')} ess1={crec.get('ess1')} "
            f"tower={crec.get('tower_size')} {crec.get('error') or ''}",
            flush=True,
        )
        prec = run_pith(path, T, maxdim, "exact")
        print(f"  pith exact {prec.get('wall_s')}", flush=True)
        scale = run_pith(path, T, maxdim, "scale") if maxdim <= 2 else {"ok": False}
        if scale.get("ok"):
            print(f"  pith scale {scale.get('wall_s')} ess1={scale.get('ess1')}", flush=True)
        sparse = run_pith(path, T, maxdim, "sparse")
        print(f"  pith sparse {sparse.get('wall_s')}", flush=True)
        rrec = run_ripser(path, T, maxdim)
        print(f"  ripser {rrec.get('wall_s')}", flush=True)
        timing.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "coperto": _strip_pairs(crec),
                "pith_exact": _strip_pairs(prec),
                "pith_scale": _strip_pairs(scale) if isinstance(scale, dict) else scale,
                "pith_sparse": _strip_pairs(sparse),
                "ripser": _strip_pairs(rrec),
                "threads": THREADS,
            }
        )

    acc_cases = [
        ("figure8", 400, 1.1, 1, lambda: figure8(400, rng)),
        ("circle_noisy", 400, 1.5, 1, lambda: circle_noisy(400, rng)),
        ("nested_loops", 400, 1.6, 1, lambda: nested_loops(400, rng)),
        ("sphere", 400, 1.4, 2, lambda: sphere(400, rng)),
    ]
    accuracy = []
    for name, n, T, maxdim, maker in acc_cases:
        path = CLOUDS / f"coperto_acc_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"accuracy {name} n={n} ...", flush=True)
        crec = run_coperto(path, maxdim, greedy=False)
        rrec = run_ripser(path, T, maxdim)
        scale = run_pith(path, T, maxdim, "scale")
        sparse = run_pith(path, T, maxdim, "sparse")
        topo = {}
        if crec.get("ok") and rrec.get("ok"):
            topo["coperto_vs_ripser"] = topology_metrics(rrec["pairs"], crec["pairs"], maxdim)
        if scale.get("ok") and rrec.get("ok"):
            topo["scale_vs_ripser"] = topology_metrics(rrec["pairs"], scale["pairs"], maxdim)
        if sparse.get("ok") and rrec.get("ok"):
            topo["sparse_vs_ripser"] = topology_metrics(rrec["pairs"], sparse["pairs"], maxdim)
        print(
            f"  cop ess1={crec.get('ess1')} rip ess1={rrec.get('ess1')} "
            f"scale ess1={scale.get('ess1')}",
            flush=True,
        )
        accuracy.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "coperto": _strip_pairs(crec),
                "ripser": _strip_pairs(rrec),
                "pith_scale": _strip_pairs(scale),
                "pith_sparse": _strip_pairs(sparse),
                "topology": topo,
            }
        )

    payload = {
        "note": (
            "coperto 0.1.7 oracle, 1 thread, not vendored. Quotient-cover "
            "approximation of VR with a claimed log-3 interleaving "
            "(Leitão arXiv:2602.22784). greedy=False. Not exact VR."
        ),
        "coperto_version": "0.1.7",
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "greedy_default_control": _strip_pairs(greedy_bad),
        "timing": timing,
        "accuracy": accuracy,
    }
    dest = OUT / "coperto.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 5 and sys.argv[1] == "--worker":
        if coperto is None:
            raise SystemExit(IMPORT_ERR or "coperto missing")
        _coperto_worker(sys.argv[2], int(sys.argv[3]), sys.argv[4])
        raise SystemExit(0)
    sys.exit(main())
