#!/usr/bin/env python3
"""I131 sequential C-scan; I132 collapse-then-Ripser-sparse; I133/I134 hold-outs."""

from __future__ import annotations

import json
import sys
import tempfile
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


def pith(path, T, dim, collapse=1, timeout=300, extra=None):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
           "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"]
    if extra:
        cmd.extend(extra)
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt, out


def ripser_pts(path, T, dim, timeout=300):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I131_seqscan():
    recs = []
    for n, T in ((80, 1.2), (200, 1.2), (2000, 1.5), (3000, 1.5)):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        pr, tr = ripser_pts(path, T, 1)
        pp, c, tp, _ = pith(path, T, 1, 1)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "T": T, "match": fid.get("exact_match_tol"),
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out")})
        print(f"I131 n={n} T={T} ratio={recs[-1]['time_ratio']} collapse_ms={recs[-1]['collapse_ms']}",
              flush=True)
    ok = all(r["match"] for r in recs)
    write({"id": "seq_row_scan_collapse", "lever": "H01-seqscan", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "sequential Tm row scan on dense edges vs I121",
           "receipts": recs}, "I131")


def I132_residual_ripser():
    recs = []
    cases = (
        ("circle_noisy", 80, 1.2, 1),
        ("circle_noisy", 200, 1.2, 1),
        ("torus", 200, 1.6, 1),
        ("torus", 500, 1.6, 1),
    )
    for name, n, T, dim in cases:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pr, tr = ripser_pts(path, T, dim)
        # collapse only
        out, dt_c, _ = run_cmd(
            [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
             "--collapse", "1", "--sparse-only", "--no-enclosing"],
            180,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".sparse", delete=False) as f:
            f.write(out)
            spar = f.name
        rs_out, dt_r, _ = run_cmd(
            [str(RIPSER), "--format", "sparse", "--dim", str(dim), "--threshold", str(T), spar],
            180,
        )
        pp = parse_ripser(rs_out)
        fid = compare(pr, pp, dim)
        total = dt_c + dt_r
        recs.append({"dataset": name, "n": n, "match": fid.get("exact_match_tol"),
                     "unmatched": fid.get("unmatched"),
                     "collapse_s": dt_c, "ripser_residual_s": dt_r, "total_s": total,
                     "ripser_orig_s": tr, "time_ratio": tr / total if total else None})
        print(f"I132 {name} n={n} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']}",
              flush=True)
    ok = all(r["match"] for r in recs)
    write({"id": "collapse_then_ripser_sparse", "lever": "H02-E3", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if ok else "reject",
           "summary": "collapse + Ripser-sparse vs Ripser point-cloud",
           "receipts": recs}, "I132")


def I133_sphere():
    path = BENCH / "datasets/generated/sphere_n500.csv"
    pr, tr = ripser_pts(path, 1.4, 2)
    pp, c, tp, _ = pith(path, 1.4, 2, 1)
    fid = compare(pr, pp, 2)
    write({"id": "sphere500_after_seqscan", "lever": "H01-seqscan", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "sphere500 H2 after sequential C-scan",
           "receipts": [{"match": fid.get("exact_match_tol"),
                         "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms")}]}, "I133")


def I134_torus1000():
    rng = np.random.default_rng(0)
    n = 1000
    R, r = 2.0, 0.5
    u = rng.uniform(0, 2 * np.pi, n)
    v = rng.uniform(0, 2 * np.pi, n)
    pts = np.stack([(R + r * np.cos(v)) * np.cos(u),
                    (R + r * np.cos(v)) * np.sin(u),
                    r * np.sin(v)], 1)
    path = BENCH / "datasets/generated/torus_n1000.csv"
    np.savetxt(path, pts, delimiter=",")
    pr, tr = ripser_pts(path, 1.6, 1, timeout=180)
    recs = []
    for coll in (1, -1):
        pp, c, tp, _ = pith(path, 1.6, 1, coll, timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({"collapse": coll, "match": fid.get("exact_match_tol"),
                     "time_ratio": tr / tp if tp else None,
                     "edges_out": c.get("edges_out"), "pith_s": tp, "ripser_s": tr})
    write({"id": "torus1000_clock", "lever": "H01", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "torus n=1000 H1 vs Ripser",
           "receipts": recs}, "I134")


def main():
    I131_seqscan()
    I132_residual_ripser()
    I133_sphere()
    I134_torus1000()


if __name__ == "__main__":
    main()
