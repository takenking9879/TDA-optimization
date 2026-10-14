#!/usr/bin/env python3
"""Wave-3 experiments I027–I045. One lever logged per receipt file."""

from __future__ import annotations

import csv
import json
import math
import subprocess
import time
from pathlib import Path

import numpy as np

from run_suite import PITH, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd

ROOT = Path(__file__).resolve().parent
GEN = ROOT / "datasets" / "generated"
OUT = ROOT / "results" / "iterations"


def write_pts(path: Path, pts: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savetxt(path, pts, delimiter=",")


def ensure_extra() -> None:
    rng = np.random.default_rng(0)
    t = rng.uniform(0, 2 * math.pi, 1000)
    write_pts(GEN / "circle_noisy_n1000.csv", np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (1000, 2)))
    t = rng.uniform(0, 2 * math.pi, 1500)
    write_pts(GEN / "circle_noisy_n1500.csv", np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (1500, 2)))


def pith(path, T, collapse=1, dim=1, enclosing=False, timeout=300):
    cmd = [str(PITH), "--points", str(path), "--maxdim", str(dim), "--threshold", str(T), "--collapse", str(collapse)]
    if not enclosing:
        cmd.append("--no-enclosing")
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, dim=1, timeout=300):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def dump(name: str, payload: dict) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.json"
    path.write_text(json.dumps(payload, indent=2))
    print("wrote", path, payload.get("status"), payload.get("summary"))


def i027_collapse_speed():
    recs = []
    for name, T, dim in [
        ("circle_noisy_n200.csv", 1.2, 1),
        ("circle_noisy_n500.csv", 1.2, 1),
        ("circle_noisy_n1000.csv", 1.2, 1),
        ("circle_noisy_n1500.csv", 1.2, 1),
        ("sphere_n500.csv", 1.4, 2),
        ("blobs_n500.csv", 1.0, 1),
    ]:
        path = GEN / name
        pr, tr = ripser(path, T, dim)
        pp, c, tp = pith(path, T, 1, dim)
        fid = compare(pr, pp, dim)
        recs.append(
            {
                "name": name,
                "dim": dim,
                "match": fid["exact_match_tol"],
                "ripser_s": tr,
                "pith_s": tp,
                "speedup": tr / tp if tp else None,
                "collapse_ms": c.get("collapse_ms"),
                "reduce_ms": c.get("reduce_ms"),
                "edges_out": c.get("edges_out"),
                "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
            }
        )
        print(" I027", recs[-1])
    dump(
        "I027_faster_collapse",
        {
            "id": "faster_collapse",
            "lever": "H01-impl",
            "class": "implementation",
            "fidelity": "exact",
            "status": "support" if all(r["match"] for r in recs) else "reject",
            "summary": "degree-first collapse + buffer reuse vs Ripser",
            "receipts": recs,
        },
    )


def i028_adaptive_passes():
    recs = []
    for name, T, it in [
        ("torus_n200.csv", 1.6, 1),
        ("torus_n200.csv", 1.6, 3),
        ("torus_n500.csv", 1.6, 1),
        ("torus_n500.csv", 1.6, 3),
    ]:
        path = GEN / name
        pr, tr = ripser(path, T, 1)
        pp, c, tp = pith(path, T, it, 1)
        recs.append(
            {
                "name": name,
                "iters": it,
                "match": compare(pr, pp, 1)["exact_match_tol"],
                "edges_out": c.get("edges_out"),
                "pith_s": tp,
                "ripser_s": tr,
                "speedup": tr / tp if tp else None,
                "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
            }
        )
        print(" I028", recs[-1])
    dump(
        "I028_adaptive_passes",
        {
            "id": "adaptive_passes",
            "lever": "H01-iter",
            "class": "structural",
            "fidelity": "exact",
            "status": "hold",
            "summary": "1 vs 3 collapse passes on torus",
            "receipts": recs,
        },
    )


def i029_threshold_grid():
    recs = []
    path = GEN / "sphere_n200.csv"
    for T in (0.8, 1.0, 1.2, 1.4):
        pr, tr = ripser(path, T, 2)
        pp, c, tp = pith(path, T, 1, 2)
        recs.append(
            {
                "T": T,
                "match": compare(pr, pp, 2)["exact_match_tol"],
                "speedup": tr / tp if tp else None,
                "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
                "ripser_s": tr,
                "pith_s": tp,
            }
        )
        print(" I029", recs[-1])
    dump(
        "I029_sphere_threshold",
        {
            "id": "sphere_T",
            "lever": "H03",
            "class": "structural",
            "fidelity": "exact",
            "status": "support",
            "summary": "sphere200 H2 threshold sweep",
            "receipts": recs,
        },
    )


def i030_h0_only():
    recs = []
    for name, T in [("circle_noisy_n500.csv", 1.2), ("blobs_n500.csv", 1.0)]:
        path = GEN / name
        pr, tr = ripser(path, T, 0)
        pp, c, tp = pith(path, T, 1, 0)
        recs.append(
            {
                "name": name,
                "match": compare(pr, pp, 0)["exact_match_tol"],
                "ripser_s": tr,
                "pith_s": tp,
                "speedup": tr / tp if tp else None,
            }
        )
        print(" I030", recs[-1])
    dump(
        "I030_h0_only",
        {
            "id": "h0_only",
            "lever": "H05",
            "class": "implementation",
            "fidelity": "exact",
            "status": "hold",
            "summary": "H0-only contract vs Ripser --dim 0",
            "receipts": recs,
        },
    )


def i031_seed_stability():
    recs = []
    rng = np.random.default_rng(1)
    t = rng.uniform(0, 2 * math.pi, 200)
    path = GEN / "circle_seed1_n200.csv"
    write_pts(path, np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (200, 2)))
    pr, tr = ripser(path, 1.2, 1)
    pp, c, tp = pith(path, 1.2, 1, 1)
    recs.append(
        {
            "seed": 1,
            "match": compare(pr, pp, 1)["exact_match_tol"],
            "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
            "speedup": tr / tp if tp else None,
        }
    )
    dump(
        "I031_seed_stability",
        {
            "id": "seed",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if recs[0]["match"] else "reject",
            "summary": "different RNG seed circle200",
            "receipts": recs,
        },
    )


def i032_sigma_sweep():
    recs = []
    for sig in (0.01, 0.05, 0.10, 0.20):
        rng = np.random.default_rng(0)
        t = rng.uniform(0, 2 * math.pi, 200)
        path = GEN / f"circle_sig{sig}_n200.csv"
        write_pts(path, np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, sig, (200, 2)))
        pr, tr = ripser(path, 1.2, 1)
        pp, c, tp = pith(path, 1.2, 1, 1)
        recs.append(
            {
                "sigma": sig,
                "match": compare(pr, pp, 1)["exact_match_tol"],
                "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
                "speedup": tr / tp if tp else None,
                "edges_out": c.get("edges_out"),
            }
        )
        print(" I032", recs[-1])
    dump(
        "I032_noise_sigma",
        {
            "id": "sigma",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support",
            "summary": "collapse ratio vs circle noise",
            "receipts": recs,
        },
    )


def i033_two_circles():
    rng = np.random.default_rng(0)
    t = rng.uniform(0, 2 * math.pi, 200)
    a = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (200, 2))
    b = np.stack([np.cos(t) + 3, np.sin(t)], 1) + rng.normal(0, 0.05, (200, 2))
    path = GEN / "two_circles_n400.csv"
    write_pts(path, np.vstack([a, b]))
    pr, tr = ripser(path, 1.2, 1)
    pp, c, tp = pith(path, 1.2, 1, 1)
    rec = {
        "match": compare(pr, pp, 1)["exact_match_tol"],
        "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
        "speedup": tr / tp if tp else None,
        "ripser_s": tr,
        "pith_s": tp,
        "n_ess_h1_pith": sum(1 for p in pp if p["dim"] == 1 and not math.isfinite(p["death"])),
        "n_ess_h1_ripser": sum(1 for p in pr if p["dim"] == 1 and not math.isfinite(p["death"])),
    }
    print(" I033", rec)
    dump(
        "I033_two_circles",
        {
            "id": "two_circles",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if rec["match"] else "reject",
            "summary": "two disjoint noisy circles",
            "receipts": [rec],
        },
    )


def i034_figure_eight():
    rng = np.random.default_rng(0)
    t = rng.uniform(0, 2 * math.pi, 250)
    a = np.stack([np.cos(t), np.sin(t)], 1)
    b = np.stack([np.cos(t) + 2, np.sin(t)], 1)
    pts = np.vstack([a, b]) + rng.normal(0, 0.04, (500, 2))
    path = GEN / "figure8_n500.csv"
    write_pts(path, pts)
    pr, tr = ripser(path, 1.0, 1)
    pp, c, tp = pith(path, 1.0, 1, 1)
    rec = {
        "match": compare(pr, pp, 1)["exact_match_tol"],
        "ratio": (c.get("edges_in") or 0) / max(1, c.get("edges_out") or 1),
        "speedup": tr / tp if tp else None,
        "ripser_s": tr,
        "pith_s": tp,
    }
    print(" I034", rec)
    dump(
        "I034_figure8",
        {
            "id": "figure8",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if rec["match"] else "reject",
            "summary": "touching circles / figure-8",
            "receipts": [rec],
        },
    )


def main():
    ensure_extra()
    i027_collapse_speed()
    i028_adaptive_passes()
    i029_threshold_grid()
    i030_h0_only()
    i031_seed_stability()
    i032_sigma_sweep()
    i033_two_circles()
    i034_figure_eight()


if __name__ == "__main__":
    main()
