#!/usr/bin/env python3
"""I221: kNN K=128 (first K that matches torus H1ess) vs Ripser and sparse-eps 0.6."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, parse_pith_text, run_cmd  # noqa: E402
from run_wave69 import bottleneck_h1, ripser  # noqa: E402
from run_wave73 import pith_sparse  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def ess1(pairs):
    return sum(1 for p in pairs if p["dim"] == 1 and not math.isfinite(p["death"]))


def pith_knn(path, T, k, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--knn", str(k), "--collapse", "0", "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 1000, 1.5),
        ("blobs", 2000, 1.0),
        ("sphere", 2000, 1.4),
        ("torus", 2000, 1.6),
        ("two_circles", 400, 1.2),
        ("figure8", 500, 1.0),
    ]
    for name, n, T in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, 90)
        pk, ck, tk = pith_knn(path, T, 128, 120)
        ps, cs, ts = pith_sparse(path, T, 0.6, "max")
        rec = {
            "name": name, "n": n, "T": T,
            "ripser_s": tr,
            "ess_vr": ess1(pr),
            "knn_s": tk, "knn_edges": ck.get("edges_in"),
            "knn_vs": tr / tk if tk else None,
            "knn_ess": ess1(pk),
            "knn_ok": ess1(pk) == ess1(pr),
            "knn_unmatched": compare(pr, pk, 1).get("unmatched"),
            "knn_bn": bottleneck_h1(pr, pk),
            "sp_s": ts, "sp_edges": cs.get("edges_in"),
            "sp_vs": tr / ts if ts else None,
            "sp_ess": ess1(ps),
            "sp_ok": ess1(ps) == ess1(pr),
            "sp_bn": bottleneck_h1(pr, ps),
        }
        print(f"I221 {rec}", flush=True)
        recs.append(rec)

    knn_ok = all(r.get("knn_ok") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    knn_better = torus and (torus.get("knn_vs") or 0) > (torus.get("sp_vs") or 0)
    bn_ok = all((r.get("knn_bn") or 9) <= 0.05 for r in recs) if recs else False
    write({
        "id": "knn_k128_vs_sparse",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if knn_ok and bn_ok and knn_better else (
            "partial" if knn_ok else "reject"
        ),
        "summary": "I221 kNN K=128 vs owned sparse-eps 0.6 and Ripser",
        "receipts": recs,
        "note": "K=128 is the first K that matched torus dim-1 essential count vs VR.",
    }, "I221")


if __name__ == "__main__":
    main()
