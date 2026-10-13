#!/usr/bin/env python3
"""I225: adaptive all-pairs lune UF for reduced VR vs I224 / Ripser.

Same --reduced-vr path (shape-agnostic). Construction should drop vs I224's
|L|·deg neighbor walk. Identity must hold. Clock vs Ripser / default PITH.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402
from run_wave85 import (  # noqa: E402
    ensure_cloud,
    ess1,
    figure8,
    loglog_slope,
    pith_default,
    pith_reduced,
    two_circles,
    unit_square_path,
    write,
)

I224 = RESULTS / "iterations" / "I224_reduced_vr_engine.json"


def ripser(path, T, timeout=120):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def i224_build(name, n):
    if not I224.exists():
        return None
    data = json.loads(I224.read_text())
    for r in data.get("receipts", []):
        if r.get("name") == name and r.get("n") == n:
            return r.get("build_ms"), r.get("red_s")
    return None


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("unit_square", 4, 2.0, None),
        ("circle_noisy", 80, 1.2, circle_noisy),
        ("circle_noisy", 200, 1.5, circle_noisy),
        ("blobs", 200, 1.0, blobs),
        ("sphere", 200, 1.4, sphere),
        ("torus", 200, 1.6, torus),
        ("uniform2", 200, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 200, 1.2, two_circles),
        ("figure8", 200, 1.0, figure8),
        ("circle_noisy", 500, 1.5, circle_noisy),
        ("blobs", 500, 1.0, blobs),
        ("torus", 500, 1.6, torus),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r)),
    ]

    for name, n, T, fn in jobs:
        if name == "unit_square":
            path = unit_square_path()
        elif name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        timeout = 180 if n >= 500 else 90
        rto = 90 if n >= 500 else 45
        pr, tr = ripser(path, T, rto)
        ps, cs, ts = pith_reduced(path, T, timeout)
        fid = compare(pr, ps, 1)
        prev = i224_build(name, n)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_red": ess1(ps),
            "ess1_ripser": ess1(pr),
            "triangles": cs.get("simplices"),
            "build_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "red_s": ts,
            "ripser_s": tr,
            "vs_ripser": (tr / ts) if ts else None,
            "i224_build_ms": prev[0] if prev else None,
            "i224_s": prev[1] if prev else None,
            "build_vs_i224": ((prev[0] / cs["collapse_ms"]) if prev and prev[0] and cs.get("collapse_ms") else None),
        }
        try:
            _, _, td = pith_default(path, T, timeout)
            rec["default_s"] = td
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        print(f"I225 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(r.get("ess1_red") == r.get("ess1_ripser") for r in recs)
    builds = [r["build_vs_i224"] for r in recs if r.get("build_vs_i224")]
    med_build = sorted(builds)[len(builds) // 2] if builds else None
    n500 = [r for r in recs if r["n"] == 500]
    clock_vs_ripser = [r.get("vs_ripser") or 0 for r in n500]
    beats_ripser = any(x >= 1.0 for x in clock_vs_ripser)

    slopes = {}
    for fam in ("circle_noisy", "blobs", "torus", "uniform2"):
        rows = [r for r in recs if r["name"] == fam and r.get("triangles")]
        if len(rows) >= 2:
            slopes[fam] = {
                "triangles": loglog_slope([r["n"] for r in rows], [r["triangles"] for r in rows]),
                "time": loglog_slope([r["n"] for r in rows], [r["red_s"] for r in rows]),
            }

    if ident and ess_ok and med_build and med_build >= 1.5:
        status = "support"
        summary = (
            f"exact {len(recs)}/{len(recs)}; construction {med_build:.1f}× vs I224"
            + ("; beats Ripser on a scale row" if beats_ripser else "; still slower than Ripser")
        )
    elif ident and ess_ok:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; construction vs I224 median {med_build}"
    else:
        status = "reject"
        summary = "identity failed after all-pairs lune UF"

    write(
        {
            "id": "reduced_vr_allpairs_lune",
            "lever": "H07",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "median_build_vs_i224": med_build,
            "beats_ripser_n500": beats_ripser,
            "slopes": slopes,
            "receipts": recs,
        },
        "I225",
    )
    print(f"I225 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
