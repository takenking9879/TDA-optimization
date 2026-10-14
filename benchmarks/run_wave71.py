#!/usr/bin/env python3
"""I209: Sheehy+implicit scaling — does 10× appear on blobs/uniform2/sphere?"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, sphere, torus, uniform, write_csv  # noqa: E402
from run_suite import RESULTS, compare, essential  # noqa: E402
from run_wave66 import loglog_slope  # noqa: E402
from run_wave69 import bottleneck_h1, pith_edges, ripser, sheehy_skeleton, write_edges  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def ensure(name, n, fn):
    path = BENCH / f"datasets/generated/{name}_n{n}.csv"
    if not path.exists():
        write_csv(path, fn(n))
        print(f"generated {path}", flush=True)
    return path


def main():
    recs = []
    families = [
        ("blobs", 1.0, lambda n: blobs(n, np.random.default_rng(0))),
        ("uniform2", 0.35, lambda n: uniform(n, 2, np.random.default_rng(0))),
        ("sphere", 1.4, lambda n: sphere(n, np.random.default_rng(0))),
        ("torus", 1.6, lambda n: torus(n, np.random.default_rng(0))),
    ]
    sizes = [500, 1000, 1500, 2000, 3000]
    with tempfile.TemporaryDirectory(prefix="i209_") as tmp:
        tmp = Path(tmp)
        for name, T, fn in families:
            for n in sizes:
                path = ensure(name, n, fn)
                pts = np.loadtxt(path, delimiter=",")
                vn, edges, skel_s, _ = sheehy_skeleton(pts, T, 0.5)
                epath = tmp / f"{name}_{n}.edges"
                write_edges(epath, vn, edges)
                rto = 180 if (name == "torus" and n >= 3000) else 90
                p0, c0, t0 = pith_edges(epath, T, 0, 120)
                pr, tr = ripser(path, T, rto)
                fid = compare(pr, p0, 1)
                rec = {
                    "name": name, "n": n, "T": T,
                    "skel_edges": len(edges),
                    "total_s": skel_s + t0,
                    "ripser_s": tr,
                    "vs_ripser": tr / (skel_s + t0) if (skel_s + t0) else None,
                    "unmatched_ripser": fid.get("unmatched"),
                    "bottleneck_vs_vr": bottleneck_h1(pr, p0),
                    "ess_pith": len(essential(p0, 1)),
                    "ess_vr": len(essential(pr, 1)),
                    "edges_in": c0.get("edges_in"),
                }
                print(f"I209 {rec}", flush=True)
                recs.append(rec)

    slopes = {}
    tenx = {}
    for name, T, _ in families:
        rows = [r for r in recs if r["name"] == name]
        xs = [r["n"] for r in rows]
        slopes[name] = {
            "slope_edges": loglog_slope(xs, [r["skel_edges"] for r in rows]),
            "slope_total": loglog_slope(xs, [r["total_s"] for r in rows]),
            "slope_ripser": loglog_slope(xs, [r["ripser_s"] for r in rows]),
            "vs": [r["vs_ripser"] for r in rows],
        }
        tenx[name] = any((r.get("vs_ripser") or 0) >= 10 for r in rows if r["n"] >= 2000)
        print(f"I209 slope {name} {slopes[name]} tenx={tenx[name]}", flush=True)

    ess_ok = all(r.get("ess_pith") == r.get("ess_vr") for r in recs) if recs else False
    any_ten = any(tenx.values())
    write({
        "id": "sheehy_implicit_scaling",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok and any_ten else ("partial" if ess_ok else "reject"),
        "summary": "I209 Sheehy+implicit vs-n scaling on non-circle families",
        "receipts": recs,
        "slopes": slopes,
        "tenx_at_or_above_2000": tenx,
        "topology_loss": "essential H1 match; finite bottleneck in receipts" if ess_ok else "ess mismatch",
    }, "I209")


if __name__ == "__main__":
    main()
