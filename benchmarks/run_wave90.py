#!/usr/bin/env python3
"""I229: RedZeD scale — is exact H1 10× general at n=3000/4000?

I228 is 10× on torus/circle at n=2000 but only 5–8× on blobs/sphere/uniform2.
Same --engine redzed path (shape-agnostic). Quantify unmatched / ess H1 /
bottleneck vs Ripser and slopes including n=2000 from I228.
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
    bottleneck_h1,
    ensure_cloud,
    ess1,
    figure8,
    loglog_slope,
    pith_default,
    two_circles,
    write,
)
from run_wave89 import pith_redzed, ripser  # noqa: E402

I228 = RESULTS / "iterations" / "I228_redzed_owned_engine.json"


def i228_row(name, n):
    if not I228.exists():
        return None
    data = json.loads(I228.read_text())
    for r in data.get("receipts", []):
        if r.get("name") == name and r.get("n") == n:
            return r
    return None


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("two_circles", 500, 1.2, two_circles),
        ("figure8", 500, 1.0, figure8),
        ("blobs", 3000, 1.0, blobs),
        ("sphere", 3000, 1.4, sphere),
        ("uniform2", 3000, 0.35, lambda n, r: uniform(n, 2, r)),
        ("torus", 3000, 1.6, torus),
        ("blobs", 4000, 1.0, blobs),
        ("sphere", 4000, 1.4, sphere),
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r)),
    ]

    for name, n, T, fn in jobs:
        if name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        rto = 240 if n >= 4000 else 180
        pto = 240 if n >= 4000 else 180
        pr, tr = ripser(path, T, rto)
        pz, cs, tz = pith_redzed(path, T, pto)
        fid = compare(pr, pz, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_redzed": ess1(pz),
            "ess1_ripser": ess1(pr),
            "bottleneck": bottleneck_h1(pr, pz),
            "pipeline": cs.get("pipeline"),
            "redzed_s": tz,
            "ripser_s": tr,
            "vs_ripser": (tr / tz) if tz else None,
        }
        try:
            _, _, td = pith_default(path, T, pto)
            rec["default_s"] = td
            rec["vs_default"] = (td / tz) if tz else None
        except Exception as ex:  # noqa: BLE001
            rec["default_err"] = str(ex)[:200]
        print(f"I229 {rec}", flush=True)
        recs.append(rec)

    # Slopes use I228 n=200 plus I228/I229 n=2000+ when present.
    prior = []
    if I228.exists():
        prior = [
            r for r in json.loads(I228.read_text()).get("receipts", [])
            if r.get("name") in {"blobs", "sphere", "uniform2", "torus"} and r.get("n") in {200, 2000}
        ]
    all_rows = prior + recs
    slopes = {}
    for fam in ("blobs", "sphere", "uniform2", "torus"):
        rows = [r for r in all_rows if r["name"] == fam and r.get("redzed_s") and r.get("ripser_s")]
        if len(rows) >= 3:
            slopes[fam] = {
                "redzed_time": loglog_slope([r["n"] for r in rows], [r["redzed_s"] for r in rows]),
                "ripser_time": loglog_slope([r["n"] for r in rows], [r["ripser_s"] for r in rows]),
                "ns": [r["n"] for r in rows],
            }

    ident = all(r.get("match_ripser") for r in recs)
    ess_ok = all(r.get("ess1_redzed") == r.get("ess1_ripser") for r in recs)
    losers = [r for r in recs if r["name"] in {"blobs", "sphere", "uniform2"}]
    x10 = [r for r in losers if (r.get("vs_ripser") or 0) >= 10]
    mixed = [r for r in recs if r["name"] in {"figure8", "two_circles"}]
    mixed_ok = all(r.get("match_ripser") for r in mixed)

    if ident and ess_ok and mixed_ok and len(x10) >= 3:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; 10× on {len(x10)}/{len(losers)} loser-family scale rows"
    elif ident and ess_ok and mixed_ok and x10:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; 10× on {len(x10)}/{len(losers)} loser-family scale rows"
    elif ident and ess_ok:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; no new 10× on blobs/sphere/uniform2"
    else:
        status = "reject"
        summary = "RedZeD identity failed at scale"

    write(
        {
            "id": "redzed_scale_10x",
            "lever": "H09-scale",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "ess_ok": ess_ok,
            "mixed_ok": mixed_ok,
            "loser_10x": len(x10),
            "slopes": slopes,
            "receipts": recs,
        },
        "I229",
    )
    print(f"I229 status={status} {summary}", flush=True)
    print(f"I229 slopes={slopes}", flush=True)


if __name__ == "__main__":
    main()
