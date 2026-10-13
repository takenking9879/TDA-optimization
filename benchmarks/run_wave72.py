#!/usr/bin/env python3
"""I210: in-process --sparse-eps vs GUDHI Sheehy --edges vs Ripser."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, essential, parse_pith_text, run_cmd  # noqa: E402
from run_wave69 import bottleneck_h1, pith_edges, ripser, sheehy_skeleton, write_edges  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith_sparse(path, T, eps, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--sparse-eps", str(eps), "--collapse", "0", "--engine", "implicit",
         "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2),
        ("circle_noisy", 1000, 1.5),
        ("blobs", 2000, 1.0),
        ("torus", 2000, 1.6),
        ("uniform2", 2000, 0.35),
        ("two_circles", 400, 1.2),
        ("figure8", 500, 1.0),
    ]
    with tempfile.TemporaryDirectory(prefix="i210_") as tmp:
        tmp = Path(tmp)
        for name, n, T in jobs:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            if not path.exists():
                print(f"missing {path}", flush=True)
                continue
            pts = np.loadtxt(path, delimiter=",")
            vn, edges, skel_s, _ = sheehy_skeleton(pts, T, 0.5)
            epath = tmp / f"{name}_{n}.edges"
            write_edges(epath, vn, edges)
            pg, cg, tg = pith_edges(epath, T, 0, 120)
            po, co, to = pith_sparse(path, T, 0.5, 180)
            pr, tr = ripser(path, T, 90)
            fid_ess = len(essential(po, 1)) == len(essential(pr, 1))
            rec = {
                "name": name, "n": n, "T": T,
                "gudhi_edges": len(edges),
                "owned_edges": co.get("edges_in"),
                "gudhi_total": skel_s + tg,
                "owned_s": to,
                "ripser_s": tr,
                "vs_ripser_owned": tr / to if to else None,
                "vs_ripser_gudhi": tr / (skel_s + tg) if (skel_s + tg) else None,
                "ess_owned": len(essential(po, 1)),
                "ess_gudhi": len(essential(pg, 1)),
                "ess_vr": len(essential(pr, 1)),
                "ess_ok": fid_ess,
                "unmatched_owned_vs_vr": compare(pr, po, 1).get("unmatched"),
                "unmatched_owned_vs_gudhi": compare(pg, po, 1).get("unmatched"),
                "bn_owned_vs_vr": bottleneck_h1(pr, po),
                "bn_gudhi_vs_vr": bottleneck_h1(pr, pg),
            }
            print(f"I210 {rec}", flush=True)
            recs.append(rec)

    ess_ok = all(r.get("ess_ok") for r in recs) if recs else False
    torus = next((r for r in recs if r["name"] == "torus"), None)
    torus_ten = torus and (torus.get("vs_ripser_owned") or 0) >= 10
    write({
        "id": "owned_sparse_eps",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok and torus_ten else ("partial" if ess_ok else "reject"),
        "summary": "I210 in-process greedy-net --sparse-eps 0.5 vs GUDHI Sheehy and Ripser",
        "receipts": recs,
        "note": "Owned construction is greedy-net flag sparse Rips, not bit-identical to GUDHI Sheehy.",
    }, "I210")


if __name__ == "__main__":
    main()
