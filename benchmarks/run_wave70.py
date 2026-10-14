#!/usr/bin/env python3
"""I208: Sheehy ε ∈ {0.3, 0.5, 0.7} loss/speed frontier on thick families."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_wave69 import (  # noqa: E402
    bottleneck_h1,
    pith_edges,
    ripser,
    sheehy_skeleton,
    write_edges,
)
from run_suite import RESULTS, compare, essential  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def main():
    recs = []
    jobs = [
        ("torus", 2000, 1.6, 90),
        ("blobs", 2000, 1.0, 60),
        ("uniform2", 2000, 0.35, 60),
        ("two_circles", 400, 1.2, 30),
    ]
    epsilons = (0.3, 0.5, 0.7)
    with tempfile.TemporaryDirectory(prefix="i208_") as tmp:
        tmp = Path(tmp)
        for name, n, T, rto in jobs:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            pts = __import__("numpy").loadtxt(path, delimiter=",")
            pr, tr = ripser(path, T, rto)
            for eps in epsilons:
                vn, edges, skel_s, _ = sheehy_skeleton(pts, T, eps)
                epath = tmp / f"{name}_{n}_{eps}.edges"
                write_edges(epath, vn, edges)
                p0, c0, t0 = pith_edges(epath, T, 0, 90)
                fid = compare(pr, p0, 1)
                rec = {
                    "name": name, "n": n, "T": T, "eps": eps,
                    "skel_edges": len(edges),
                    "skel_s": skel_s,
                    "pith0_s": t0,
                    "total_s": skel_s + t0,
                    "ripser_s": tr,
                    "vs_ripser": tr / (skel_s + t0) if (skel_s + t0) else None,
                    "unmatched_ripser": fid.get("unmatched"),
                    "bottleneck_vs_vr": bottleneck_h1(pr, p0),
                    "ess_pith": len(essential(p0, 1)),
                    "ess_vr": len(essential(pr, 1)),
                    "edges_in": c0.get("edges_in"),
                }
                print(f"I208 {rec}", flush=True)
                recs.append(rec)

    ess_ok = all(r.get("ess_pith") == r.get("ess_vr") for r in recs) if recs else False
    torus = [r for r in recs if r["name"] == "torus"]
    # Prefer an ε that keeps torus ≥10× and cuts bottleneck vs 0.5.
    write({
        "id": "sheehy_eps_frontier",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok else "reject",
        "summary": "I208 Sheehy ε∈{0.3,0.5,0.7} loss/speed on thick families",
        "receipts": recs,
        "torus": torus,
    }, "I208")


if __name__ == "__main__":
    main()
