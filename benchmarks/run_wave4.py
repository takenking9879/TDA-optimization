#!/usr/bin/env python3
"""Iterations I044–I060: sticky collapse, implicit coh, policy, reduced VR, distances."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import (  # noqa: E402
    INDEX,
    PITH,
    RESULTS,
    RIPSER,
    compare,
    load_index,
    parse_pith_text,
    parse_ripser,
    run_cmd,
)
from reduced_vr import build_reduced_2_complex, pairwise, persist_h1  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry: dict, iid: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)
    return path


def pith(path, T, dim, collapse, engine="auto", extra=None, timeout=180):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(dim),
        "--threshold",
        str(T),
        "--collapse",
        str(collapse),
        "--engine",
        engine,
        "--no-enclosing",
    ]
    if extra:
        cmd.extend(extra)
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, counters = parse_pith_text(out)
    return pairs, counters, dt


def ripser(path, T, dim, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def row(name, n):
    for r in load_index():
        if r["name"] == name and r["n"] == n:
            return r
    # extra generated files not in index
    p = BENCH / "datasets" / "generated" / f"{name}_n{n}.csv"
    if p.exists():
        defaults = {
            "circle_noisy": 1.2,
            "sphere": 1.4,
            "torus": 1.6,
            "blobs": 1.0,
            "uniform2": 0.35,
            "uniform10": 1.8,
        }
        return {"name": name, "n": n, "threshold": defaults.get(name, 1.2), "path": str(p.relative_to(BENCH))}
    raise KeyError(f"{name} n={n}")


def I044_sticky_identity():
    recs = []
    for name, n, dim in [("circle_noisy", 80, 1), ("circle_noisy", 200, 1), ("blobs", 80, 1), ("sphere", 80, 2)]:
        r = row(name, n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], dim)
        pp, c, tp = pith(path, r["threshold"], dim, 1, "homology")
        fid = compare(pr, pp, dim)
        recs.append(
            {
                "dataset": name,
                "n": n,
                "dim": dim,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "edges_in": c.get("edges_in"),
                "edges_out": c.get("edges_out"),
                "collapse_ms": c.get("collapse_ms"),
                "ripser_s": tr,
                "pith_s": tp,
            }
        )
    ok = all(x["match"] for x in recs)
    write(
        {
            "id": "sticky_collapse_identity",
            "lever": "H01-sticky",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if ok else "reject",
            "summary": f"sticky+heap identity {sum(x['match'] for x in recs)}/{len(recs)}",
            "receipts": recs,
        },
        "I044",
    )


def I045_implicit_no_collapse():
    recs = []
    for name, n in [("circle_noisy", 80), ("blobs", 80), ("uniform2", 80)]:
        r = row(name, n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], 1)
        pp, c, tp = pith(path, r["threshold"], 1, 0, "implicit")
        fid = compare(pr, pp, 1)
        recs.append(
            {
                "dataset": name,
                "n": n,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr,
                "pith_s": tp,
                "cols": c.get("cols_reduced"),
                "reduce_ms": c.get("reduce_ms"),
            }
        )
    ok = all(x["match"] for x in recs)
    write(
        {
            "id": "implicit_coh_no_collapse",
            "lever": "H02",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": "support" if ok else "reject",
            "summary": "implicit cohomology vs Ripser, collapse=0 (I003 killer)",
            "receipts": recs,
        },
        "I045",
    )


def I046_implicit_with_collapse():
    recs = []
    for name, n, dim in [("circle_noisy", 200, 1), ("sphere", 80, 2), ("torus", 80, 1)]:
        r = row(name, n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], dim)
        pp, c, tp = pith(path, r["threshold"], dim, 1, "implicit")
        fid = compare(pr, pp, dim)
        recs.append(
            {
                "dataset": name,
                "n": n,
                "match": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "ripser_s": tr,
                "pith_s": tp,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
            }
        )
    ok = all(x["match"] for x in recs)
    write(
        {
            "id": "implicit_coh_with_collapse",
            "lever": "H02",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if ok else "reject",
            "summary": f"implicit+collapse {sum(x['match'] for x in recs)}/{len(recs)}",
            "receipts": recs,
        },
        "I046",
    )


def I047_scale_h1():
    recs = []
    for n in (500, 1000, 1500):
        try:
            r = row("circle_noisy", n)
        except KeyError:
            continue
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], 1)
        pp, c, tp = pith(path, r["threshold"], 1, 1, "homology")
        fid = compare(pr, pp, 1)
        recs.append(
            {
                "n": n,
                "match": fid.get("exact_match_tol"),
                "edges_in": c.get("edges_in"),
                "edges_out": c.get("edges_out"),
                "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "ripser_s": tr,
                "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
            }
        )
    write(
        {
            "id": "sticky_circle_scale",
            "lever": "H01-sticky",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if recs and all(x["match"] for x in recs) else "hold",
            "summary": "circle H1 wall-clock after sticky collapse",
            "receipts": recs,
        },
        "I047",
    )


def I048_highd_policy():
    recs = []
    for n in (80, 200):
        r = row("uniform10", n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], 1)
        for coll, eng, tag in ((-1, "auto", "policy"), (1, "homology", "force_collapse"), (0, "implicit", "skip")):
            try:
                pp, c, tp = pith(path, r["threshold"], 1, coll, eng, timeout=180)
                fid = compare(pr, pp, 1)
                recs.append(
                    {
                        "n": n,
                        "tag": tag,
                        "match": fid.get("exact_match_tol"),
                        "unmatched": fid.get("unmatched"),
                        "ripser_s": tr,
                        "pith_s": tp,
                        "time_ratio": tr / tp if tp else None,
                        "collapse_ms": c.get("collapse_ms"),
                        "edges_out": c.get("edges_out"),
                        "engine": c.get("pipeline"),
                    }
                )
            except Exception as ex:  # noqa: BLE001
                recs.append({"n": n, "tag": tag, "error": str(ex)[:400]})
    write(
        {
            "id": "highd_skip_policy",
            "lever": "H01-policy",
            "class": "implementation",
            "fidelity": "exact",
            "status": "experiment",
            "summary": "high-d: probe-skip vs force collapse vs implicit",
            "receipts": recs,
        },
        "I048",
    )


def I049_torus_implicit():
    recs = []
    for n, dim in ((200, 1), (500, 1)):
        r = row("torus", n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], dim)
        for eng in ("homology", "implicit", "auto"):
            pp, c, tp = pith(path, r["threshold"], dim, -1, eng)
            fid = compare(pr, pp, dim)
            recs.append(
                {
                    "n": n,
                    "engine": eng,
                    "match": fid.get("exact_match_tol"),
                    "ripser_s": tr,
                    "pith_s": tp,
                    "time_ratio": tr / tp if tp else None,
                    "collapse_ms": c.get("collapse_ms"),
                    "reduce_ms": c.get("reduce_ms"),
                    "edges_out": c.get("edges_out"),
                }
            )
    write(
        {
            "id": "torus_engines",
            "lever": "H02",
            "class": "structural",
            "fidelity": "exact",
            "status": "experiment",
            "summary": "torus residual: homology vs implicit vs auto",
            "receipts": recs,
        },
        "I049",
    )


def I050_sphere_h2():
    recs = []
    for n in (200, 500):
        r = row("sphere", n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], 2)
        pp, c, tp = pith(path, r["threshold"], 2, 1, "homology")
        fid = compare(pr, pp, 2)
        recs.append(
            {
                "n": n,
                "match": fid.get("exact_match_tol"),
                "ripser_s": tr,
                "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
            }
        )
    write(
        {
            "id": "sphere_h2_sticky",
            "lever": "H01-sticky",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if recs and all(x["match"] for x in recs) else "hold",
            "summary": "sphere H2 after sticky collapse",
            "receipts": recs,
        },
        "I050",
    )


def I051_distances_cli():
    r = row("circle_noisy", 80)
    path = BENCH / r["path"]
    pts = np.loadtxt(path, delimiter=",")
    D = pairwise(pts)
    dpath = BENCH / "datasets" / "generated" / "circle80_dist.csv"
    np.savetxt(dpath, D, delimiter=",")
    pr, tr = ripser(path, r["threshold"], 1)
    out, tp, _ = run_cmd(
        [
            str(PITH),
            "--distances",
            str(dpath),
            "--maxdim",
            "1",
            "--threshold",
            str(r["threshold"]),
            "--collapse",
            "1",
            "--engine",
            "homology",
            "--no-enclosing",
        ],
        60,
    )
    pp, c = parse_pith_text(out)
    fid = compare(pr, pp, 1)
    write(
        {
            "id": "distance_matrix_cli",
            "lever": "I041-hold",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if fid.get("exact_match_tol") else "reject",
            "summary": "PITH --distances square CSV vs Ripser point-cloud",
            "receipts": [{"match": fid.get("exact_match_tol"), "pith_s": tp, "ripser_s": tr, "counters": c}],
        },
        "I051",
    )


def I052_h0_skip():
    recs = []
    for name, n in (("circle_noisy", 500), ("uniform10", 200)):
        r = row(name, n)
        path = BENCH / r["path"]
        pr, tr = ripser(path, r["threshold"], 0)
        pp, c, tp = pith(path, r["threshold"], 0, -1, "auto")
        fid = compare(pr, pp, 0)
        recs.append(
            {
                "dataset": name,
                "n": n,
                "match": fid.get("exact_match_tol"),
                "ripser_s": tr,
                "pith_s": tp,
                "time_ratio": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms") or 0,
            }
        )
    write(
        {
            "id": "h0_skip_collapse",
            "lever": "H05",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if all(x["match"] for x in recs) else "reject",
            "summary": "adaptive policy skips collapse on H0-only",
            "receipts": recs,
        },
        "I052",
    )


def I053_reduced_vr():
    recs = []
    rng = np.random.default_rng(0)

    def circle(n, sigma=0.02):
        t = rng.uniform(0, 2 * np.pi, n)
        return np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, sigma, (n, 2))

    def square(n):
        return rng.uniform(0, 1, (n, 2))

    cases = [("circle", circle(30), 1.2), ("square", square(25), 0.6), ("two_blobs", np.vstack([rng.normal(0, 0.1, (12, 2)), rng.normal((3, 0), 0.1, (12, 2))]), 1.5)]
    tmp = BENCH / "datasets" / "generated"
    tmp.mkdir(parents=True, exist_ok=True)
    for name, pts, T in cases:
        p = tmp / f"rvr_{name}.csv"
        np.savetxt(p, pts, delimiter=",")
        D = pairwise(pts)
        edges, tris = build_reduced_2_complex(D, T)
        red = persist_h1(len(pts), D, edges, tris)
        pr, _ = ripser(p, T, 1)
        # compare essential H1 count + finite bars loosely
        r_ess = sum(1 for x in pr if x["dim"] == 1 and not math_finite_death(x))
        recs.append(
            {
                "name": name,
                "n": len(pts),
                "n_edges": red["n_edges"],
                "n_triangles": red["n_triangles"],
                "full_triangles_bound": len(pts) * (len(pts) - 1) * (len(pts) - 2) // 6,
                "h1_ess_reduced": len(red["h1_ess"]),
                "h1_ess_ripser": r_ess,
                "h1_finite_reduced": len(red["h1_finite"]),
                "h1_finite_ripser": sum(1 for x in pr if x["dim"] == 1 and math_finite_death(x) and x["death"] - x["birth"] > 1e-6),
                "match_ess": len(red["h1_ess"]) == r_ess,
            }
        )
    ok = all(x["match_ess"] for x in recs)
    write(
        {
            "id": "reduced_vr_h1",
            "lever": "H07",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": "support" if ok else "reject",
            "summary": "reduced VR H1 essential bars vs Ripser n<=30",
            "receipts": recs,
        },
        "I053",
    )


def math_finite_death(p):
    d = p["death"]
    return d == d and d != float("inf")


def I054_gudhi_collapse_counts():
    import gudhi

    recs = []
    for name, n in (("circle_noisy", 200), ("blobs", 200), ("torus", 200)):
        r = row(name, n)
        path = BENCH / r["path"]
        pts = np.loadtxt(path, delimiter=",")
        D = pairwise(pts)
        T = r["threshold"]
        edges = []
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if D[i, j] <= T:
                    edges.append([i, j, float(D[i, j])])
        t0 = time.perf_counter()
        collapsed = gudhi.flag_filtration.edge_collapse.reduce_graph(edges, nb_iterations=1)
        tg = time.perf_counter() - t0
        _, c, _ = pith(path, T, 0, 1, "homology")
        recs.append(
            {
                "dataset": name,
                "n": n,
                "gudhi_out": len(collapsed),
                "pith_out": c.get("edges_out"),
                "match_count": len(collapsed) == c.get("edges_out"),
                "gudhi_s": tg,
                "pith_collapse_ms": c.get("collapse_ms"),
            }
        )
    write(
        {
            "id": "gudhi_collapse_counts_sticky",
            "lever": "H01-sticky",
            "class": "reproduced",
            "fidelity": "exact",
            "status": "support" if all(x["match_count"] for x in recs) else "hold",
            "summary": "sticky collapse edge counts vs GUDHI",
            "receipts": recs,
        },
        "I054",
    )


def main():
    if not INDEX.exists():
        raise SystemExit("generate datasets first")
    I044_sticky_identity()
    I045_implicit_no_collapse()
    I046_implicit_with_collapse()
    I047_scale_h1()
    I048_highd_policy()
    I049_torus_implicit()
    I050_sphere_h2()
    I051_distances_cli()
    I052_h0_skip()
    I053_reduced_vr()
    I054_gudhi_collapse_counts()


if __name__ == "__main__":
    main()
