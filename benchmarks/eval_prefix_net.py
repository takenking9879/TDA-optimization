#!/usr/bin/env python3
"""I333: prefix Gonzalez net vs full-n farthest-point sparse Rips.

`--sparse-net prefix` keeps only m=max(64, ceil(4*sqrt(n))) landmarks as
vertices. Not exact VR. Default `--mode sparse` is unchanged (FPS).
1 thread. τ frozen.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import circle_noisy, figure8, sphere, write_csv  # noqa: E402
from run_suite import PITH, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"
THREADS = 1
BUDGET_S = 30


def run_sparse(path: Path, T: float, maxdim: int, net: str):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        "sparse",
        "--sparse-net",
        net,
        "--threads",
        "1",
        "--no-enclosing",
    ]
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, BUDGET_S)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    ess1 = sum(1 for p in pairs if p["dim"] == 1 and not np.isfinite(p["death"]))
    return {
        "ok": err is None,
        "error": err,
        "timed_out": err is not None and "timed out" in (err or "").lower(),
        "wall_s": None if err else dt,
        "pipeline": c.get("pipeline"),
        "n_vertices": c.get("n_vertices"),
        "edges_in": c.get("edges_in"),
        "distances": c.get("distances"),
        "ess1": ess1,
        "n_pairs": len(pairs),
        "pairs": pairs,
        "threads_used": THREADS,
        "net": net,
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
        pairs = parse_ripser(out)
        return {"ok": True, "wall_s": dt, "pairs": pairs, "threads_used": 1}
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "wall_s": None,
            "timed_out": "timed out" in str(e).lower(),
            "pairs": [],
        }


def main() -> int:
    rng = np.random.default_rng(33)
    CLOUDS.mkdir(parents=True, exist_ok=True)
    cases = [
        ("figure8", 400, 1.1, 1, lambda: figure8(400, rng)),
        ("figure8", 2000, 1.1, 1, lambda: figure8(2000, rng)),
        ("figure8", 8000, 1.1, 1, lambda: figure8(8000, rng)),
        ("figure8", 16000, 1.1, 1, lambda: figure8(16000, rng)),
        ("circle_noisy", 2000, 1.5, 1, lambda: circle_noisy(2000, rng)),
        ("sphere", 2000, 1.4, 2, lambda: sphere(2000, rng)),
    ]
    rows = []
    for name, n, T, maxdim, maker in cases:
        path = CLOUDS / f"prefix_{name}_n{n}.csv"
        write_csv(path, maker())
        print(f"prefix-net {name} n={n} ...", flush=True)
        fps = run_sparse(path, T, maxdim, "fps")
        print(
            f"  fps {fps.get('wall_s')} ess1={fps.get('ess1')} "
            f"verts={fps.get('n_vertices')} edges={fps.get('edges_in')} "
            f"dist={fps.get('distances')} {fps.get('error') or ''}",
            flush=True,
        )
        pr = run_sparse(path, T, maxdim, "prefix")
        print(
            f"  prefix {pr.get('wall_s')} ess1={pr.get('ess1')} "
            f"verts={pr.get('n_vertices')} edges={pr.get('edges_in')} "
            f"dist={pr.get('distances')} {pr.get('error') or ''}",
            flush=True,
        )
        rrec = None
        vs_vr = None
        if n <= 2000 and maxdim == 1:
            rrec = run_ripser(path, T, maxdim)
            print(f"  ripser {rrec.get('wall_s')}", flush=True)
            if pr.get("ok") and rrec.get("ok"):
                vs_vr = compare(pr["pairs"], rrec["pairs"], maxdim)
        vs_fps = None
        if pr.get("ok") and fps.get("ok"):
            vs_fps = compare(pr["pairs"], fps["pairs"], maxdim)
        ratio = None
        if pr.get("ok") and fps.get("ok") and pr.get("wall_s") and fps.get("wall_s"):
            ratio = fps["wall_s"] / pr["wall_s"]
        rows.append(
            {
                "name": name,
                "n": n,
                "T": T,
                "maxdim": maxdim,
                "fps": {k: v for k, v in fps.items() if k != "pairs"},
                "prefix": {k: v for k, v in pr.items() if k != "pairs"},
                "ripser": None
                if rrec is None
                else {k: v for k, v in rrec.items() if k != "pairs"},
                "fps_over_prefix": ratio,
                "unmatched_vs_fps": None if vs_fps is None else vs_fps.get("unmatched"),
                "unmatched_vs_vr": None if vs_vr is None else vs_vr.get("unmatched"),
                "threads": THREADS,
            }
        )
    payload = {
        "note": (
            "I333 prefix Gonzalez net (m=max(64, 4*sqrt(n)) vertices) vs "
            "full-n FPS sparse Rips. Not exact VR. Default --mode sparse "
            "stays FPS. Stated slack: Sheehy on an ε-net."
        ),
        "threads": THREADS,
        "budget_s": BUDGET_S,
        "receipts": rows,
    }
    dest = OUT / "prefix_net.json"
    dest.write_text(json.dumps(payload, indent=2))
    print("wrote", dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
