#!/usr/bin/env python3
"""I071–I082: bitset collapse speed, identity, scale, torus, H2, H0."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith(path, T, dim, collapse=1, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T),
         "--collapse", str(collapse), "--engine", "homology", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def I071_identity():
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
                     "collapse_ms": c.get("collapse_ms"), "ripser_s": tr, "pith_s": tp})
    ok = all(r["match"] for r in recs)
    write({"id": "bitset_collapse_identity", "lever": "H01-bitset", "class": "implementation",
           "fidelity": "exact", "status": "support" if ok else "reject",
           "summary": f"bitset collapse identity {sum(r['match'] for r in recs)}/{len(recs)}",
           "receipts": recs}, "I071")


def I072_circle_scale():
    recs = []
    for n in (500, 1000, 1500, 2000):
        path = BENCH / f"datasets/generated/circle_noisy_n{n}.csv"
        if not path.exists():
            recs.append({"n": n, "missing": True})
            continue
        pr, tr = ripser(path, 1.2, 1)
        pp, c, tp = pith(path, 1.2, 1, 1, timeout=180)
        fid = compare(pr, pp, 1)
        recs.append({
            "n": n, "match": fid.get("exact_match_tol"),
            "edges_in": c.get("edges_in"), "edges_out": c.get("edges_out"),
            "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
            "collapse_ms": c.get("collapse_ms"), "reduce_ms": c.get("reduce_ms"),
            "ripser_s": tr, "pith_s": tp, "time_ratio": tr / tp if tp else None,
        })
    ok = all(r.get("match") for r in recs if not r.get("missing"))
    write({"id": "bitset_circle_scale", "lever": "H01-bitset", "class": "implementation",
           "fidelity": "exact", "status": "support" if ok else "reject",
           "summary": "bitset collapse H1 scale vs I047/I059",
           "receipts": recs}, "I072")


def I073_sphere_h2():
    recs = []
    for n in (200, 500):
        path = BENCH / f"datasets/generated/sphere_n{n}.csv"
        pr, tr = ripser(path, 1.4, 2)
        pp, c, tp = pith(path, 1.4, 2, 1)
        fid = compare(pr, pp, 2)
        recs.append({"n": n, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms")})
    write({"id": "bitset_sphere_h2", "lever": "H01-bitset", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if recs and all(r["match"] for r in recs) else "hold",
           "summary": "sphere H2 after bitset collapse", "receipts": recs}, "I073")


def I074_torus():
    recs = []
    for n, coll in ((200, -1), (500, -1)):
        path = BENCH / f"datasets/generated/torus_n{n}.csv"
        pr, tr = ripser(path, 1.6, 1)
        pp, c, tp = pith(path, 1.6, 1, coll)
        fid = compare(pr, pp, 1)
        recs.append({"n": n, "match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                     "time_ratio": tr / tp if tp else None, "edges_out": c.get("edges_out"),
                     "collapse_ms": c.get("collapse_ms")})
    write({"id": "bitset_torus", "lever": "H01-bitset", "class": "implementation",
           "fidelity": "exact", "status": "experiment",
           "summary": "torus adaptive after bitset collapse", "receipts": recs}, "I074")


def I075_highd():
    path = BENCH / "datasets/generated/uniform10_n200.csv"
    pr, tr = ripser(path, 1.8, 1)
    pp, c, tp = pith(path, 1.8, 1, -1)
    fid = compare(pr, pp, 1)
    write({"id": "bitset_highd", "lever": "H01-bitset", "class": "implementation",
           "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "uniform10 n=200 after bitset (still expect lose vs Ripser)",
           "receipts": [{"match": fid.get("exact_match_tol"), "ripser_s": tr, "pith_s": tp,
                         "time_ratio": tr / tp if tp else None, "collapse_ms": c.get("collapse_ms"),
                         "edges_out": c.get("edges_out")}]}, "I075")


def I076_gudhi_counts():
    recs = []
    # Compare edge_out to previous I044 receipts (same datasets)
    prev = json.loads((OUT / "I044_sticky_collapse_identity.json").read_text())
    for old in prev["receipts"]:
        name, n = old["dataset"], old["n"]
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        T = {"circle_noisy": 1.2, "blobs": 1.0, "sphere": 1.4}.get(name, 1.2)
        dim = 2 if name == "sphere" else 1
        _, c, _ = pith(path, T, dim, 1)
        recs.append({"dataset": name, "n": n, "old_out": old.get("edges_out"),
                     "new_out": c.get("edges_out"),
                     "same": old.get("edges_out") == c.get("edges_out")})
    write({"id": "bitset_vs_sticky_counts", "lever": "H01-bitset", "class": "reproduced",
           "fidelity": "exact",
           "status": "support" if all(r["same"] for r in recs) else "hold",
           "summary": "bitset residual edge counts vs I044 sticky",
           "receipts": recs}, "I076")


def I077_T_sweep():
    path = BENCH / "datasets/generated/circle_noisy_n500.csv"
    recs = []
    for T in (0.8, 1.2, 1.5):
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith(path, T, 1, 1)
        fid = compare(pr, pp, 1)
        recs.append({"T": T, "match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                     "collapse_ms": c.get("collapse_ms"), "edges_out": c.get("edges_out")})
    write({"id": "bitset_circle500_T", "lever": "H03", "class": "reproduced", "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "circle500 T-sweep after bitset", "receipts": recs}, "I077")


def I078_h0():
    path = BENCH / "datasets/generated/circle_noisy_n1000.csv"
    pr, tr = ripser(path, 1.2, 0)
    pp, c, tp = pith(path, 1.2, 0, -1)
    fid = compare(pr, pp, 0)
    write({"id": "bitset_h0_skip", "lever": "H05", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "H0 skip still works after bitset change",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms") or 0}]}, "I078")


def I079_blobs500():
    path = BENCH / "datasets/generated/blobs_n500.csv"
    pr, tr = ripser(path, 1.0, 1)
    pp, c, tp = pith(path, 1.0, 1, 1)
    fid = compare(pr, pp, 1)
    write({"id": "bitset_blobs500", "lever": "H01-bitset", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "blobs n=500 after bitset",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "edge_ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
                         "collapse_ms": c.get("collapse_ms")}]}, "I079")


def I080_annulus():
    path = BENCH / "datasets/generated/annulus_n300.csv"
    if not path.exists():
        write({"id": "bitset_annulus", "lever": "H01", "status": "hold", "summary": "missing annulus"}, "I080")
        return
    pr, tr = ripser(path, 1.2, 1)
    pp, c, tp = pith(path, 1.2, 1, 1)
    fid = compare(pr, pp, 1)
    write({"id": "bitset_annulus", "lever": "H01-bitset", "class": "reproduced", "fidelity": "exact",
           "status": "support" if fid.get("exact_match_tol") else "reject",
           "summary": "annulus n=300 after bitset",
           "receipts": [{"match": fid.get("exact_match_tol"), "time_ratio": tr / tp if tp else None,
                         "collapse_ms": c.get("collapse_ms")}]}, "I080")


def main():
    I071_identity()
    I072_circle_scale()
    I073_sphere_h2()
    I074_torus()
    I075_highd()
    I076_gudhi_counts()
    I077_T_sweep()
    I078_h0()
    I079_blobs500()
    I080_annulus()


if __name__ == "__main__":
    main()
