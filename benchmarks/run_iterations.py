#!/usr/bin/env python3
"""Systematic experiment loop: one lever at a time, write receipts."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

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

OUT = RESULTS / "iterations"


def datasets(max_n: int = 200, names=None):
    rows = load_index()
    rows = [r for r in rows if r["n"] <= max_n]
    if names:
        rows = [r for r in rows if r["name"] in names]
    return rows


def ripser_on(path: Path, T: float, dim: int, sparse_text: str | None = None):
    if sparse_text is None:
        out, dt, _ = run_cmd(
            [str(RIPSER), "--format", "point-cloud", "--dim", str(dim), "--threshold", str(T), str(path)],
            120,
        )
        return parse_ripser(out), dt
    t0 = time.perf_counter()
    proc = subprocess.run(
        [str(RIPSER), "--format", "sparse", "--dim", str(dim), "--threshold", str(T)],
        input=sparse_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=120,
        check=False,
    )
    dt = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-500:])
    return parse_ripser(proc.stdout), dt


def pith_sparse(path: Path, T: float, collapse: int) -> str:
    return subprocess.check_output(
        [
            str(PITH),
            "--points",
            str(path),
            "--threshold",
            str(T),
            "--collapse",
            str(collapse),
            "--no-enclosing",
            "--sparse-only",
        ],
        text=True,
        timeout=120,
    )


def pith_full(path: Path, T: float, collapse: int, dim: int):
    out, dt, _ = run_cmd(
        [
            str(PITH),
            "--points",
            str(path),
            "--maxdim",
            str(dim),
            "--threshold",
            str(T),
            "--collapse",
            str(collapse),
            "--no-enclosing",
        ],
        120,
    )
    pairs, counters = parse_pith_text(out)
    return pairs, counters, dt


def write(entry: dict) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    n = len(list(OUT.glob("I*.json"))) + 1
    path = OUT / f"I{n:03d}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} note={entry.get('summary')}")
    return path


def iter_collapse_ratio():
    """H01: edge ratio vs Ripser identity via E3."""
    rows = datasets(200)
    recs = []
    for row in rows:
        path = BENCH / row["path"]
        pr, tr = ripser_on(path, row["threshold"], 1)
        sparse = pith_sparse(path, row["threshold"], 1)
        n_out = len([ln for ln in sparse.splitlines() if ln.strip()])
        pe, te = ripser_on(path, row["threshold"], 1, sparse)
        fid = compare(pr, pe, 1)
        # edges in from complete threshold graph via pith counters
        _, c, _ = pith_full(path, row["threshold"], 1, 0)
        recs.append(
            {
                "dataset": row["name"],
                "n": row["n"],
                "edges_in": c.get("edges_in"),
                "edges_out": n_out,
                "ratio": (c.get("edges_in") or 0) / max(1, n_out),
                "e3_match": fid.get("exact_match_tol"),
                "ripser_s": tr,
                "e3_s": te,
            }
        )
    ratios = [r["ratio"] for r in recs if r["e3_match"]]
    write(
        {
            "id": "H01_collapse_ratio",
            "lever": "H01",
            "class": "structural",
            "fidelity": "exact",
            "status": "support" if ratios and sorted(ratios)[len(ratios) // 2] >= 10 else "hold",
            "summary": f"median_ratio={sorted(ratios)[len(ratios)//2] if ratios else None} n={len(recs)}",
            "receipts": recs,
        }
    )


def iter_collapse_passes():
    rows = [r for r in datasets(200) if r["name"] == "circle_noisy"]
    recs = []
    for row in rows:
        path = BENCH / row["path"]
        pr, _ = ripser_on(path, row["threshold"], 1)
        for it in (1, 2, 3, 5):
            sparse = pith_sparse(path, row["threshold"], it)
            n_out = len([ln for ln in sparse.splitlines() if ln.strip()])
            pe, _ = ripser_on(path, row["threshold"], 1, sparse)
            recs.append(
                {
                    "n": row["n"],
                    "iters": it,
                    "edges_out": n_out,
                    "match": compare(pr, pe, 1).get("exact_match_tol"),
                }
            )
    write(
        {
            "id": "H01b_iterated_collapse",
            "lever": "H01-iter",
            "class": "structural",
            "fidelity": "exact",
            "status": "hold",
            "summary": "extra passes vs 1-core size on circles",
            "receipts": recs,
        }
    )


def iter_no_collapse_pith():
    rows = [r for r in datasets(80) if r["name"] in {"circle_noisy", "blobs"}]
    recs = []
    for row in rows:
        path = BENCH / row["path"]
        pr, tr = ripser_on(path, row["threshold"], 1)
        pp, c, tp = pith_full(path, row["threshold"], 0, 1)
        recs.append(
            {
                "dataset": row["name"],
                "n": row["n"],
                "match": compare(pr, pp, 1).get("exact_match_tol"),
                "unmatched": compare(pr, pp, 1).get("unmatched"),
                "ripser_s": tr,
                "pith_s": tp,
                "cols": c.get("cols_reduced"),
            }
        )
    write(
        {
            "id": "H02_pith_core_no_collapse",
            "lever": "H02",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": "reject" if any(not r["match"] for r in recs) else "support",
            "summary": "own reducer vs Ripser without collapse",
            "receipts": recs,
        }
    )


def iter_threshold_sweep():
    row = next(r for r in datasets(200) if r["name"] == "circle_noisy" and r["n"] == 200)
    path = BENCH / row["path"]
    recs = []
    for T in (0.4, 0.6, 0.8, 1.0, 1.2, 1.5):
        pr, tr = ripser_on(path, T, 1)
        sparse = pith_sparse(path, T, 1)
        n_out = len([ln for ln in sparse.splitlines() if ln.strip()])
        pe, te = ripser_on(path, T, 1, sparse)
        _, c, _ = pith_full(path, T, 1, 0)
        recs.append(
            {
                "T": T,
                "edges_in": c.get("edges_in"),
                "edges_out": n_out,
                "ratio": (c.get("edges_in") or 0) / max(1, n_out),
                "match": compare(pr, pe, 1).get("exact_match_tol"),
                "ripser_s": tr,
                "e3_s": te,
            }
        )
    write(
        {
            "id": "H03_threshold_sweep",
            "lever": "H03",
            "class": "structural",
            "fidelity": "exact_VR_le_T",
            "status": "support",
            "summary": "circle200 threshold sweep",
            "receipts": recs,
        }
    )


def main():
    if not INDEX.exists():
        raise SystemExit("generate datasets first")
    iter_collapse_ratio()
    iter_collapse_passes()
    iter_no_collapse_pith()
    iter_threshold_sweep()


if __name__ == "__main__":
    main()
