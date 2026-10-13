#!/usr/bin/env python3
"""I230: -DNDEBUG on the vendored RedZeD TU vs I229 wall.

Paper builds with -O3 -DNDEBUG. I229 blobs n=4000 is 313 ms reduce of
394 ms wall — a 20–30% assert tax would push sphere over 10× and cut
the blobs gap. Same --engine redzed; identity must hold.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform  # noqa: E402
from run_suite import RESULTS, compare  # noqa: E402
from run_wave85 import bottleneck_h1, ensure_cloud, ess1, write  # noqa: E402
from run_wave89 import pith_redzed, ripser  # noqa: E402

I229 = RESULTS / "iterations" / "I229_redzed_scale_10x.json"
I228 = RESULTS / "iterations" / "I228_redzed_owned_engine.json"


def prev(name, n):
    for path in (I229, I228):
        if not path.exists():
            continue
        for r in json.loads(path.read_text()).get("receipts", []):
            if r.get("name") == name and r.get("n") == n:
                return r
    return None


def main():
    import numpy as np

    rng = np.random.default_rng(0)
    recs = []
    jobs = [
        ("circle_noisy", 2000, 1.5, circle_noisy),
        ("blobs", 2000, 1.0, blobs),
        ("sphere", 2000, 1.4, sphere),
        ("torus", 2000, 1.6, torus),
        ("uniform2", 2000, 0.35, lambda n, r: uniform(n, 2, r)),
        ("blobs", 4000, 1.0, blobs),
        ("sphere", 4000, 1.4, sphere),
        ("uniform2", 4000, 0.35, lambda n, r: uniform(n, 2, r)),
    ]

    for name, n, T, fn in jobs:
        path = ensure_cloud(
            name, n, (lambda m, r: uniform(m, 2, r)) if name == "uniform2" else fn, rng
        )
        rto = 180 if n >= 4000 else 120
        pr, tr = ripser(path, T, rto)
        pz, cs, tz = pith_redzed(path, T, 180)
        fid = compare(pr, pz, 1)
        old = prev(name, n)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_redzed": ess1(pz),
            "ess1_ripser": ess1(pr),
            "bottleneck": bottleneck_h1(pr, pz),
            "redzed_s": tz,
            "reduce_ms": cs.get("reduce_ms"),
            "metric_ms": cs.get("metric_ms"),
            "ripser_s": tr,
            "vs_ripser": (tr / tz) if tz else None,
            "prev_s": old.get("redzed_s") if old else None,
            "vs_prev": ((old["redzed_s"] / tz) if old and old.get("redzed_s") and tz else None),
        }
        print(f"I230 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    gains = [r["vs_prev"] for r in recs if r.get("vs_prev")]
    med = sorted(gains)[len(gains) // 2] if gains else None
    n4000 = [r for r in recs if r["n"] == 4000]
    x10 = [r for r in n4000 if (r.get("vs_ripser") or 0) >= 10]

    if ident and med and med >= 1.15 and x10:
        status = "support"
        summary = f"exact {len(recs)}/{len(recs)}; NDEBUG {med:.2f}× vs I229; 10× on {len(x10)} n=4000 rows"
    elif ident and med and med >= 1.08:
        status = "hold"
        summary = f"exact {len(recs)}/{len(recs)}; NDEBUG {med:.2f}× vs I229; 10× on {len(x10)} n=4000"
    elif ident:
        status = "reject"
        summary = f"exact {len(recs)}/{len(recs)}; NDEBUG median {med} — no clock win"
    else:
        status = "reject"
        summary = "identity failed after -DNDEBUG"

    write(
        {
            "id": "redzed_ndebug",
            "lever": "H09-ndebug",
            "class": "implementation",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": ident,
            "median_vs_prev": med,
            "n4000_10x": len(x10),
            "receipts": recs,
        },
        "I230",
    )
    print(f"I230 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
