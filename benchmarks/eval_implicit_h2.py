#!/usr/bin/env python3
"""Time I313 implicit cohomology H2 vs homology / RedZeD / Ripser.

--engine implicit now stays on persist_implicit_coh for H2 (no tet list).
--engine homology still splits fat flags to RedZeD H2. τ frozen.
1 thread. Compare barcodes to Ripser when Ripser finishes.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import mixed_1d2d3d, multi_cavities, sphere, write_csv  # noqa: E402
from run_consolidation import run_ripser, strip_pairs  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_suite import PITH, RIPSER, compare  # noqa: E402

OUT = BENCH / "results" / "consolidation"


def _local_p(n0, t0, n1, t1):
    if not (n0 and n1 and t0 and t1) or n0 == n1 or t0 <= 0 or t1 <= 0:
        return None
    return math.log(t1 / t0) / math.log(n1 / n0)


def main() -> int:
    if not PITH.exists() or not RIPSER.exists():
        print("PITH or Ripser missing", file=sys.stderr)
        return 2
    rng = np.random.default_rng(0)
    series = []
    for name, fn, T, dim, ns in (
        ("sphere", sphere, 1.4, 2, [80, 200, 400, 600]),
        ("mixed_1d2d3d", mixed_1d2d3d, 1.4, 2, [160, 300]),
        ("multi_cavities", multi_cavities, 1.4, 2, [160, 300]),
    ):
        prev = {}
        for n in ns:
            path = cloud(name, n, fn, rng)
            row = {"name": name, "n": n, "T": T, "maxdim": dim, "runs": {}, "vs_ripser": {}}
            methods = [
                ("implicit", lambda: run_pith(path, T, dim, "exact", "implicit", threads=1, timeout=20)),
                ("homology", lambda: run_pith(path, T, dim, "exact", "homology", threads=1, timeout=20)),
                ("redzed", lambda: run_pith(path, T, dim, "exact", "redzed", threads=1, timeout=20)),
                ("auto", lambda: run_pith(path, T, dim, "exact", "auto", threads=1, timeout=20)),
                ("ripser", lambda: run_ripser(path, T, dim, timeout=20)),
            ]
            recs = {}
            for key, fn_run in methods:
                rec = fn_run()
                recs[key] = rec
                row["runs"][key] = strip_pairs(rec)
                wall = rec.get("wall_s")
                pkey = f"{name}:{key}"
                if wall and pkey in prev:
                    row["runs"][key]["local_p"] = _local_p(prev[pkey][0], prev[pkey][1], n, wall)
                if wall:
                    prev[pkey] = (n, wall)
                print(
                    f"{name} n={n} {key}: ok={rec.get('ok')} wall={wall} "
                    f"ess2={rec.get('ess2')} pipe={rec.get('pipeline')} err={rec.get('error')}",
                    flush=True,
                )
            ref = recs.get("ripser")
            if ref and ref.get("ok") and ref.get("pairs") is not None:
                for key in ("implicit", "homology", "redzed", "auto"):
                    rec = recs[key]
                    if rec.get("ok") and rec.get("pairs") is not None:
                        row["vs_ripser"][key] = compare(rec["pairs"], ref["pairs"], dim)
            series.append(row)

    unmatched = 0
    implicit_wins = 0
    implicit_vs_redzed = []
    for row in series:
        for key, cmp in row.get("vs_ripser", {}).items():
            unmatched += int(cmp.get("unmatched") or 0)
        imp = (row["runs"].get("implicit") or {}).get("wall_s")
        rz = (row["runs"].get("redzed") or {}).get("wall_s")
        hom = (row["runs"].get("homology") or {}).get("wall_s")
        rip = (row["runs"].get("ripser") or {}).get("wall_s")
        if imp and rz:
            implicit_vs_redzed.append(rz / imp)
            if imp < rz:
                implicit_wins += 1
        if imp and hom and imp < hom:
            pass
        if imp and rip:
            print(f"  ratio {row['name']} n={row['n']} ripser/implicit={rip/imp:.2f}×", flush=True)

    out = {
        "note": "I313 implicit cohomology H2. 1 thread. τ frozen. Not a leftover pairing algorithm.",
        "unmatched_vs_ripser": unmatched,
        "implicit_faster_than_redzed": implicit_wins,
        "implicit_vs_redzed_ratios": implicit_vs_redzed,
        "series": series,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "implicit_h2.json"
    path.write_text(json.dumps(out, indent=2) + "\n")
    print(f"wrote {path} unmatched={unmatched} implicit<redzed {implicit_wins}/{len(implicit_vs_redzed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
