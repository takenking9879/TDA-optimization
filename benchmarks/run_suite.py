#!/usr/bin/env python3
"""Run Ripser vs PITH on generated datasets and write receipts."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BENCH = Path(__file__).resolve().parent
RIPSER = ROOT / "third_party" / "ripser" / "ripser"
PITH = ROOT / "src" / "pith" / "build" / "pith"
INDEX = BENCH / "datasets" / "generated" / "index.csv"
RESULTS = BENCH / "results"


def parse_ripser(text: str) -> list[dict]:
    pairs = []
    dim = None
    for line in text.splitlines():
        m = re.match(r"persistence intervals in dim (\d+):", line)
        if m:
            dim = int(m.group(1))
            continue
        m = re.match(r"\s*\[([^,]+),\s*([^\)]*)\)", line)
        if m and dim is not None:
            birth = float(m.group(1))
            death_s = m.group(2).strip()
            death = math.inf if death_s == "" else float(death_s)
            pairs.append({"dim": dim, "birth": birth, "death": death})
    return pairs


def parse_pith_text(text: str) -> tuple[list[dict], dict]:
    pairs = parse_ripser(text)
    counters = {}
    for line in text.splitlines():
        if line.startswith("# COUNTERS"):
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        counters[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        counters[k] = v
    return pairs, counters


def finite_pairs(pairs: list[dict], maxdim: int) -> list[tuple]:
    out = []
    for p in pairs:
        if p["dim"] > maxdim:
            continue
        d = p["death"]
        if not math.isfinite(d):
            continue
        # drop near-diagonal noise
        if d - p["birth"] <= 1e-6:
            continue
        out.append((p["dim"], round(p["birth"], 5), round(d, 5)))
    return sorted(out)


def essential(pairs: list[dict], maxdim: int) -> list[tuple]:
    out = []
    for p in pairs:
        if p["dim"] > maxdim:
            continue
        if not math.isfinite(p["death"]):
            out.append((p["dim"], round(p["birth"], 5)))
    return sorted(out)


def run_cmd(cmd: list[str], timeout: int) -> tuple[str, float, int]:
    t0 = time.perf_counter()
    usage0 = resource.getrusage(resource.RUSAGE_CHILDREN)
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    dt = time.perf_counter() - t0
    usage1 = resource.getrusage(resource.RUSAGE_CHILDREN)
    rss = int((usage1.ru_maxrss - usage0.ru_maxrss))  # kB on Linux, incremental-ish
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed {cmd}\n{proc.stderr[-2000:]}")
    return proc.stdout, dt, rss


def compare(a: list[dict], b: list[dict], maxdim: int, tol: float = 1e-4) -> dict:
    def filt(pairs):
        out = []
        for p in pairs:
            if p["dim"] > maxdim:
                continue
            if math.isfinite(p["death"]) and p["death"] - p["birth"] <= 1e-6:
                continue
            out.append(p)
        return out

    aa, bb = filt(a), filt(b)
    used = [False] * len(bb)
    unmatched = 0
    for p in aa:
        best = None
        best_j = None
        for j, q in enumerate(bb):
            if used[j] or q["dim"] != p["dim"]:
                continue
            db = abs(p["birth"] - q["birth"])
            if math.isinf(p["death"]) and math.isinf(q["death"]):
                dd = 0.0
            elif math.isinf(p["death"]) or math.isinf(q["death"]):
                dd = 1e9
            else:
                dd = abs(p["death"] - q["death"])
            sc = max(db, dd)
            if best is None or sc < best:
                best, best_j = sc, j
        if best is not None and best <= tol:
            used[best_j] = True
        else:
            unmatched += 1
    unmatched += sum(1 for u in used if not u)
    ok = unmatched == 0
    return {
        "exact_match_tol": ok,
        "unmatched": unmatched,
        "n_finite_a": len(finite_pairs(a, maxdim)),
        "n_finite_b": len(finite_pairs(b, maxdim)),
        "n_essential_a": len(essential(a, maxdim)),
        "n_essential_b": len(essential(b, maxdim)),
        "class": "exact" if ok else "unverified",
    }


def load_index() -> list[dict]:
    rows = []
    with INDEX.open() as f:
        for row in csv.DictReader(f):
            row["n"] = int(row["n"])
            row["threshold"] = float(row["threshold"])
            rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", choices=["smoke", "round1", "challenge"], default="smoke")
    ap.add_argument("--maxdim", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--collapse", type=int, default=1)
    args = ap.parse_args()

    if not RIPSER.exists():
        print("Ripser binary missing", file=sys.stderr)
        sys.exit(1)
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        sys.exit(1)
    if not INDEX.exists():
        print("datasets missing; run generate_datasets.py", file=sys.stderr)
        sys.exit(1)

    rows = load_index()
    if args.suite == "smoke":
        rows = [r for r in rows if r["n"] <= 200 and r["name"] in {"circle_noisy", "blobs", "uniform2"}]
    elif args.suite == "round1":
        rows = [r for r in rows if r["n"] <= 500]
    # challenge: all

    RESULTS.mkdir(parents=True, exist_ok=True)
    receipts = []
    for row in rows:
        path = BENCH / row["path"]
        rec = {
            "dataset": row["name"],
            "n": row["n"],
            "threshold": row["threshold"],
            "maxdim": args.maxdim,
            "path": str(path),
        }
        print(f"== {row['name']} n={row['n']} T={row['threshold']} ==", flush=True)
        try:
            out_r, t_r, _ = run_cmd(
                [
                    str(RIPSER),
                    "--format",
                    "point-cloud",
                    "--dim",
                    str(args.maxdim),
                    "--threshold",
                    str(row["threshold"]),
                    str(path),
                ],
                args.timeout,
            )
            pairs_r = parse_ripser(out_r)
            rec["ripser"] = {"seconds": t_r, "n_pairs": len(pairs_r)}

            out_p, t_p, _ = run_cmd(
                [
                    str(PITH),
                    "--points",
                    str(path),
                    "--maxdim",
                    str(args.maxdim),
                    "--threshold",
                    str(row["threshold"]),
                    "--collapse",
                    str(args.collapse),
                    "--no-enclosing",
                ],
                args.timeout,
            )
            pairs_p, counters = parse_pith_text(out_p)
            rec["pith"] = {"seconds": t_p, "n_pairs": len(pairs_p), "counters": counters}
            rec["fidelity_pith"] = compare(pairs_r, pairs_p, args.maxdim)

            # E3: collapse then stock Ripser on the residual sparse graph
            sparse = subprocess.check_output(
                [
                    str(PITH),
                    "--points",
                    str(path),
                    "--threshold",
                    str(row["threshold"]),
                    "--collapse",
                    str(args.collapse),
                    "--no-enclosing",
                    "--sparse-only",
                ],
                text=True,
                timeout=args.timeout,
            )
            t0 = time.perf_counter()
            proc = subprocess.run(
                [
                    str(RIPSER),
                    "--format",
                    "sparse",
                    "--dim",
                    str(args.maxdim),
                    "--threshold",
                    str(row["threshold"]),
                ],
                input=sparse,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=args.timeout,
                check=False,
            )
            t_e3 = time.perf_counter() - t0
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr[-800:])
            pairs_e3 = parse_ripser(proc.stdout)
            rec["collapse_then_ripser"] = {"seconds": t_e3, "n_pairs": len(pairs_e3)}
            rec["fidelity_e3"] = compare(pairs_r, pairs_e3, args.maxdim)
            rec["fidelity"] = rec["fidelity_e3"]
            if counters.get("edges_in") and counters.get("edges_out"):
                rec["edge_ratio"] = counters["edges_in"] / max(1, counters["edges_out"])
            rec["time_ratio_ripser_over_pith"] = t_r / t_p if t_p > 0 else None
            rec["status"] = "ok"
        except Exception as ex:  # noqa: BLE001
            rec["status"] = "error"
            rec["error"] = str(ex)[:800]
            print("  ERROR", rec["error"])
        receipts.append(rec)
        print(
            "  ",
            rec.get("status"),
            "edge_ratio",
            rec.get("edge_ratio"),
            "time_ratio",
            rec.get("time_ratio_ripser_over_pith"),
            "match_e3",
            rec.get("fidelity_e3", {}).get("exact_match_tol"),
            "match_pith",
            rec.get("fidelity_pith", {}).get("exact_match_tol"),
        )

    out = RESULTS / f"{args.suite}.json"
    payload = {
        "suite": args.suite,
        "maxdim": args.maxdim,
        "collapse": args.collapse,
        "parent_ripser": "01add51ff64aaf40889483260cc5c3b7d0f2a1e7",
        "receipts": receipts,
    }
    out.write_text(json.dumps(payload, indent=2))
    print("wrote", out)


if __name__ == "__main__":
    main()
