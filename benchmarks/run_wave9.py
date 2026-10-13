#!/usr/bin/env python3
"""I101–I110: progressive-intersection collapse identity + H1 scale."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith(path, T, dim, collapse=1, timeout=300):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=300):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I101_identity():
    recs = []
    for name, n, T, dim in (
        ("circle_noisy", 80, 1.2, 1),
        ("circle_noisy", 200, 1.2, 1),
        ("blobs", 80, 1.0, 1),
        ("sphere", 80, 1.4, 2),
        ("torus", 80, 1.6, 1),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser(path, T, dim)
        pp, c, tp = pith(path, T, dim, 1)
        fid = compare(pr, pp, dim)
        recs.append({"dataset": name, "n": n, "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched"), "edges_out": c.get("edges_out"),
                     "collapse_ms": c.get("collapse_ms")})
    write({"id": "prog_collapse_identity", "lever": "H01-prog", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": f"progressive intersection identity {sum(r['match'] for r in recs)}/{len(recs)}",
           "receipts": recs}, "I101")


def I102_circle_scale():
    recs = []
    for n, T in ((1000, 1.2), (1500, 1.2), (2000, 1.2), (2000, 1.5)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "T": T, "missing": True})
            continue
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith(path, T, 1, 1)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
    write({"id": "prog_circle_scale", "lever": "H01-prog", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if all(r.get("match") for r in recs if not r.get("missing")) else "reject",
           "summary": "progressive collapse vs I082/I096 baselines",
           "receipts": recs}, "I102")


def I103_sphere_h2():
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pr, tr = ripser(path, 1.4, 2)
    pp, c, tp = pith(path, 1.4, 2, 1)
    fid = compare(pr, pp, 2)
    write({"id": "prog_sphere_h2", "lever": "H01-prog", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "sphere500 H2 after progressive collapse",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms")}]}, "I103")


def I104_counts():
    prev = json.loads((OUT / "I044_sticky_collapse_identity.json").read_text())
    recs = []
    for old in prev["receipts"]:
        name, n = old["dataset"], old["n"]
        T = {"circle_noisy": 1.2, "blobs": 1.0, "sphere": 1.4}.get(name, 1.2)
        dim = 2 if name == "sphere" else 1
        _, c, _ = pith(BENCH / f"datasets/generated/{name}_n{n}.csv", T, dim, 1)
        recs.append({"dataset": name, "n": n, "old": old.get("edges_out"), "new": c.get("edges_out"),
                     "same": old.get("edges_out") == c.get("edges_out")})
    write({"id": "prog_vs_sticky_counts", "lever": "H01-prog", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["same"] for r in recs) else "hold",
           "summary": "progressive residual counts vs I044",
           "receipts": recs}, "I104")


def I105_circle3000():
    rng = np.random.default_rng(0)
    n = 3000
    t = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (n, 2))
    path = BENCH / "datasets/generated/circle_noisy_n3000.csv"
    np.savetxt(path, pts, delimiter=",")
    recs = []
    for T in (1.2, 1.5):
        pr, tr = ripser(path, T, 1, timeout=300)
        pp, c, tp = pith(path, T, 1, 1, timeout=300)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"),
                     "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out")})
    write({"id": "circle3000_h1", "lever": "H01", "class": "structural", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle n=3000 H1 clock vs Ripser",
           "receipts": recs}, "I105")


def main():
    I101_identity()
    I102_circle_scale()
    I103_sphere_h2()
    I104_counts()
    I105_circle3000()


if __name__ == "__main__":
    main()
