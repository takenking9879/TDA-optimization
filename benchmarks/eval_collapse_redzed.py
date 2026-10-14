#!/usr/bin/env python3
"""I317: collapse then RedZeD on the residual flag, vs auto RedZeD.

Not a leftover-coface skip. Exact VR if flag-edge-collapse is exact.
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
    grid_holes,
    sphere,
    torus,
    uniform,
)
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"

CASES = [
    ("figure8", figure8, 2000, 1.1, 1),
    ("torus", torus, 2000, 1.6, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 2000, 0.35, 1),
    ("sphere", sphere, 2000, 1.4, 1),
    ("anisotropic_blob", anisotropic_blob, 4000, 2.5, 1),
    ("grid_holes", grid_holes, 4000, 0.12, 1),
    ("anisotropic_blob", anisotropic_blob, 8000, 2.5, 1),
    ("uniform2", lambda n, r: uniform(n, 2, r), 5000, 0.35, 1),
]


def load_pts(path: Path) -> np.ndarray:
    return np.loadtxt(path, delimiter=",", dtype=np.float64)


def run_gudhi_collapse(pts: np.ndarray, T: float, maxdim: int):
    import gudhi

    t0 = time.perf_counter()
    st = gudhi.RipsComplex(points=pts, max_edge_length=float(T)).create_simplex_tree(
        max_dimension=1
    )
    n_in = st.num_simplices()
    t_build = time.perf_counter()
    st.collapse_edges(nb_iterations=1)
    n_out = st.num_simplices()
    t_col = time.perf_counter()
    st.expansion(maxdim + 1)
    st.persistence(homology_coeff_field=2, persistence_dim_max=True)
    t1 = time.perf_counter()
    pairs = []
    for dim in range(maxdim + 1):
        for birth, death in st.persistence_intervals_in_dimension(dim):
            pairs.append({"dim": dim, "birth": float(birth), "death": float(death)})
    return {
        "method": "gudhi:collapse+persist",
        "ok": True,
        "error": None,
        "timed_out": False,
        "wall_s": t1 - t0,
        "build_s": t_build - t0,
        "collapse_s": t_col - t_build,
        "persist_s": t1 - t_col,
        "n_simplices_in": int(n_in),
        "n_simplices_out": int(n_out),
        "n_pairs": len(pairs),
        "pairs": pairs,
    }


def main() -> int:
    rng = np.random.default_rng(0)
    series = []
    for name, fn, n, T, dim in CASES:
        path = cloud(name, n, fn, rng)
        row = {"name": name, "n": n, "T": T, "runs": {}, "vs_ripser": {}, "ratio": {}}
        recs = {}
        for eng in ("auto", "collapse-redzed"):
            rec = run_pith(path, T, dim, "exact", eng, threads=1, timeout=25)
            recs[eng] = rec
            row["runs"][eng] = strip_pairs(rec)
            print(
                f"{name} n={n} {eng}: ok={rec.get('ok')} wall={rec.get('wall_s')} "
                f"collapse={rec.get('collapse_ms')} reduce={rec.get('reduce_ms')} "
                f"pipe={rec.get('pipeline')} err={rec.get('error')}",
                flush=True,
            )
        pts = load_pts(path)
        try:
            gud = run_gudhi_collapse(pts, T, dim)
        except Exception as e:
            gud = {
                "method": "gudhi:collapse+persist",
                "ok": False,
                "error": str(e),
                "timed_out": "timed out" in str(e).lower(),
                "wall_s": None,
                "pairs": None,
            }
        recs["gudhi"] = gud
        row["runs"]["gudhi"] = strip_pairs(gud)
        print(
            f"{name} n={n} gudhi: ok={gud.get('ok')} wall={gud.get('wall_s')} "
            f"collapse={gud.get('collapse_s')} persist={gud.get('persist_s')} "
            f"sim={gud.get('n_simplices_in')}->{gud.get('n_simplices_out')} err={gud.get('error')}",
            flush=True,
        )
        rip = run_ripser(path, T, dim, timeout=30)
        recs["ripser"] = rip
        row["runs"]["ripser"] = strip_pairs(rip)
        rw = rip.get("wall_s")
        if rip.get("ok") and rip.get("pairs") is not None:
            for eng in ("auto", "collapse-redzed", "gudhi"):
                rec = recs[eng]
                if rec.get("ok") and rec.get("pairs") is not None:
                    row["vs_ripser"][eng] = compare(rec["pairs"], rip["pairs"], dim)
                w = rec.get("wall_s")
                row["ratio"][eng] = (rw / w) if w and rw else None
        series.append(row)
        print(
            f"  ratios auto={row['ratio'].get('auto')} "
            f"collapse-redzed={row['ratio'].get('collapse-redzed')} "
            f"gudhi={row['ratio'].get('gudhi')} ripser={rw}",
            flush=True,
        )

    unmatched = 0
    cr_faster = 0
    n_cmp = 0
    cr_ge10 = 0
    auto_ge10 = 0
    for row in series:
        for eng, cmp in row.get("vs_ripser", {}).items():
            unmatched += int(cmp.get("unmatched") or 0)
        if (row["ratio"].get("collapse-redzed") or 0) >= 10:
            cr_ge10 += 1
        if (row["ratio"].get("auto") or 0) >= 10:
            auto_ge10 += 1
        a, b = row["runs"]["collapse-redzed"].get("wall_s"), row["runs"]["auto"].get("wall_s")
        if a and b:
            n_cmp += 1
            if a < b:
                cr_faster += 1

    out = {
        "note": "I317 collapse+RedZeD residual. τ frozen. 1 thread. Not a leftover-skip.",
        "unmatched_vs_ripser": unmatched,
        "auto_ge10": auto_ge10,
        "collapse_redzed_ge10": cr_ge10,
        "collapse_redzed_faster_than_auto": f"{cr_faster}/{n_cmp}",
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "collapse_redzed.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(
        f"wrote {path} unmatched={unmatched} auto≥10 {auto_ge10} "
        f"collapse-redzed≥10 {cr_ge10} collapse-redzed<auto {cr_faster}/{n_cmp}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
