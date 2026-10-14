#!/usr/bin/env python3
"""I321: leftover algebraic work — RedZeD leftover/AE vs Ripser columns.

Not a pairing change. Counts leftover edges, empty-seed skips, AE visits
vs Ripser leftover / apparent / reduced columns / cofacet probes.
Also times GUDHI flag cohomology on two leftover-miss cells.
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
from generate_datasets import (  # noqa: E402
    anisotropic_blob,
    figure8,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import compare, parse_pith_text, run_cmd  # noqa: E402

OUT = BENCH / "results" / "consolidation"
RIPSER_COUNT = Path("/tmp/ripser_count")

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
]


def parse_alg(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("# ALG") or line.startswith("# COUNTERS"):
            out = {}
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        out[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        out[k] = v
            if out:
                return out
    return {}


def run_ripser_count(path: Path, T: float, maxdim: int, timeout: float = 30):
    cmd = [
        str(RIPSER_COUNT),
        "--format",
        "point-cloud",
        "--dim",
        str(maxdim),
        "--threshold",
        str(T),
        str(path),
    ]
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        err = None
    except Exception as e:
        out, dt, err = "", time.perf_counter() - t0, str(e)
    return {
        "ok": err is None,
        "error": err,
        "wall_s": None if err else dt,
        "alg": parse_alg(out),
    }


def run_gudhi_cohom(path: Path, T: float, maxdim: int, timeout: float = 15):
    cmd = [
        sys.executable,
        "-c",
        (
            "import time,sys,numpy as np,gudhi;"
            f"pts=np.loadtxt('{path}',delimiter=',');"
            "t0=time.perf_counter();"
            f"st=gudhi.RipsComplex(points=pts,max_edge_length={T}).create_simplex_tree(max_dimension={maxdim+1});"
            "st.compute_persistence();"
            "print('ok',time.perf_counter()-t0,st.num_simplices())"
        ),
    ]
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        err = None
        parts = out.strip().split()
        wall = float(parts[1]) if len(parts) >= 2 else dt
        nsimp = int(parts[2]) if len(parts) >= 3 else None
    except Exception as e:
        wall, nsimp, err = time.perf_counter() - t0, None, str(e)
    return {"ok": err is None, "error": err, "wall_s": None if err else wall, "n_simplices": nsimp}


def main() -> int:
    if not RIPSER_COUNT.exists():
        print("missing /tmp/ripser_count", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        pith = run_pith(path, T, dim, "exact", "auto", threads=1, timeout=25)
        rip = run_ripser_count(path, T, dim)
        row = {
            "name": name,
            "n": n,
            "T": T,
            "pith_wall": pith.get("wall_s"),
            "pith_reduce_ms": pith.get("reduce_ms"),
            "pith_pipeline": pith.get("pipeline"),
            "pith_alg": {
                "leftover": (pith.get("counters") or {}).get("cols_assembled"),
                "empty_skip": (pith.get("counters") or {}).get("cols_apparent"),
                "ae_or_keep": (pith.get("counters") or {}).get("cols_reduced"),
                "coface": (pith.get("counters") or {}).get("cofacet_probes"),
            },
            "ripser_wall": rip.get("wall_s"),
            "ripser_alg": rip.get("alg"),
            "ratio_wall": (rip["wall_s"] / pith["wall_s"])
            if pith.get("wall_s") and rip.get("wall_s")
            else None,
        }
        pl, rl = row["pith_alg"].get("leftover"), (rip.get("alg") or {}).get("leftover")
        pc, rc = row["pith_alg"].get("ae_or_keep"), (rip.get("alg") or {}).get("cols_reduced")
        pcf, rcf = row["pith_alg"].get("coface"), (rip.get("alg") or {}).get("cofacet_probes")
        row["ratio_leftover"] = (rl / pl) if pl and rl else None
        row["ratio_cols"] = (rc / pc) if pc and rc else None
        row["ratio_coface"] = (rcf / pcf) if pcf and rcf else None
        series.append(row)
        print(
            f"{name} n={n} pipe={row['pith_pipeline']} wall {row['ratio_wall']} "
            f"leftover pith/rip={pl}/{rl} cols={pc}/{rc} coface={pcf}/{rcf} "
            f"ratio_cols={row['ratio_cols']} ratio_coface={row['ratio_coface']}",
            flush=True,
        )

    gudhi_rows = []
    for name, fn, n, T, dim in (
        ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
        ("sphere", sphere, 2000, 1.4, 1),
    ):
        path = cloud(name, n, fn, rng)
        g = run_gudhi_cohom(path, T, dim)
        gudhi_rows.append({"name": name, "n": n, **g})
        print(f"gudhi-cohom {name} n={n} ok={g.get('ok')} wall={g.get('wall_s')} simp={g.get('n_simplices')} err={g.get('error')}", flush=True)

    n_alg10 = sum(
        1
        for r in series
        if (r.get("ratio_cols") and r["ratio_cols"] >= 10)
        or (r.get("ratio_coface") and r["ratio_coface"] >= 10)
    )
    out = {
        "note": "I321 algebraic leftover vs Ripser. Counts only. τ frozen.",
        "n_cells": len(series),
        "n_alg_ge10": n_alg10,
        "series": series,
        "gudhi_cohom": gudhi_rows,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "algebraic.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} alg_ge10={n_alg10}/{len(series)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
