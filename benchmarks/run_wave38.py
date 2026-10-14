#!/usr/bin/env python3
"""I167: first-keep rank + suffix-keep sweep (prefix large enough to include residual)."""

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


def pith_cmd(path, T, extra, timeout=180):
    cmd = [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
           "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra
    out, dt, _ = run_cmd(cmd, timeout)
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def main():
    recs = []
    # --- first-keep + tau stats on full backward ---
    for name, n, T, timeout in (
        ("circle_noisy", 80, 1.2, 30),
        ("circle_noisy", 200, 1.5, 30),
        ("circle_noisy", 2000, 1.5, 60),
        ("blobs", 2000, 1.0, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pp, c, tp = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        m = int(c.get("edges_in") or 0)
        fk = int(c.get("collapse_first_keep") if c.get("collapse_first_keep") is not None else -1)
        remain = (m - fk) if fk >= 0 else None
        rec = {
            "phase": "first_keep",
            "name": name, "n": n, "T": T,
            "pith_s": tp,
            "edges_in": m,
            "edges_out": c.get("edges_out"),
            "first_keep": fk,
            "remain": remain,
            "remain_mult": (remain / n) if remain else None,
            "c_probes": c.get("collapse_c_probes"),
            "tau_late": c.get("collapse_tau_late"),
            "tau_late_common": c.get("collapse_tau_late_common"),
            "fast_trims": c.get("collapse_fast_trims"),
            "collapse_ms": c.get("collapse_ms"),
        }
        print(f"I167 first_keep {rec}", flush=True)
        recs.append(rec)

    # --- suffix-back vs full-back identity on circle2000 ---
    path = BENCH / "datasets/generated/circle_noisy_n2000.csv"
    T = 1.5
    base_pairs, base_c, base_t = pith_cmd(path, T, ["--collapse-alg", "back"], 60)
    m = int(base_c.get("edges_in") or 0)
    fk = int(base_c.get("collapse_first_keep") if base_c.get("collapse_first_keep") is not None else -1)
    remain = (m - fk) if fk >= 0 else 134642
    keeps = sorted(set([
        20000, 40000, 80000, 134642, remain, remain + 2000, max(remain * 2, remain + 10000)
    ]))
    identity = []
    for keep in keeps:
        if keep <= 0 or keep > m:
            continue
        pp, c, tp = pith_cmd(path, T, ["--collapse-alg", "suffix-back", "--suffix-keep", str(keep)], 60)
        fid = compare(base_pairs, pp, 1)
        rec = {
            "phase": "suffix_back_vs_back",
            "name": "circle_noisy", "n": 2000, "T": T, "keep": keep,
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "pith_s": tp,
            "base_s": base_t,
            "time_ratio_vs_back": base_t / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "edges_out": c.get("edges_out"),
            "base_edges_out": base_c.get("edges_out"),
            "c_probes": c.get("collapse_c_probes"),
        }
        print(f"I167 suffix-back {rec}", flush=True)
        identity.append(rec)
        recs.append(rec)

    winners = [r for r in identity if r.get("match")]
    ripser_recs = []
    if winners:
        pr, tr = ripser(path, T, 90)
        best = min(winners, key=lambda r: r["keep"])
        pp, c, tp = pith_cmd(path, T, ["--collapse-alg", "suffix-back", "--suffix-keep", str(best["keep"])], 60)
        fid = compare(pr, pp, 1)
        rec = {
            "phase": "vs_ripser",
            "name": "circle_noisy", "n": 2000, "T": T, "keep": best["keep"],
            "match": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ripser_s": tr, "pith_s": tp,
            "time_ratio": tr / tp if tp else None,
            "collapse_ms": c.get("collapse_ms"),
            "edges_out": c.get("edges_out"),
        }
        print(f"I167 vs Ripser {rec}", flush=True)
        ripser_recs.append(rec)
        recs.append(rec)

    ok = bool(winners) and all(r.get("match") for r in ripser_recs)
    write({
        "id": "first_keep_suffix",
        "lever": "H01-suffix-keep",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if winners else "reject",
        "summary": "first-keep index + suffix-keep sweep vs full backward / Ripser",
        "any_match": bool(winners),
        "receipts": recs,
    }, "I167")


if __name__ == "__main__":
    main()
