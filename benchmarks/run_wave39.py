#!/usr/bin/env python3
"""I168: suffix-stabilize (no first-keep oracle) identity + clock."""

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


def pith_cmd(path, T, alg, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--collapse-alg", alg, "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def one(name, n, T, vs_ripser=True, timeout=180, ripser_timeout=180):
    path = BENCH / f"datasets/generated/{name}_n{n}.csv"
    pb, cb, tb = pith_cmd(path, T, "back", timeout)
    ps, cs, ts = pith_cmd(path, T, "suffix-stab", timeout)
    fid_b = compare(pb, ps, 1)
    rec = {
        "name": name, "n": n, "T": T,
        "match_back": fid_b.get("exact_match_tol"),
        "unmatched_back": fid_b.get("unmatched"),
        "back_s": tb, "stab_s": ts,
        "vs_back": tb / ts if ts else None,
        "back_collapse_ms": cb.get("collapse_ms"),
        "stab_collapse_ms": cs.get("collapse_ms"),
        "back_out": cb.get("edges_out"),
        "stab_out": cs.get("edges_out"),
        "stab_keep": cs.get("collapse_first_keep"),
        "stab_probes": cs.get("collapse_c_probes"),
        "back_probes": cb.get("collapse_c_probes"),
    }
    if vs_ripser:
        pr, tr = ripser(path, T, ripser_timeout)
        fid_r = compare(pr, ps, 1)
        rec["match_ripser"] = fid_r.get("exact_match_tol")
        rec["unmatched_ripser"] = fid_r.get("unmatched")
        rec["ripser_s"] = tr
        rec["vs_ripser"] = tr / ts if ts else None
    print(f"I168 {rec}", flush=True)
    return rec


def main():
    recs = []
    recs.append(one("circle_noisy", 80, 1.2, True, 30, 30))
    recs.append(one("circle_noisy", 200, 1.5, True, 30, 30))
    recs.append(one("circle_noisy", 2000, 1.5, True, 90, 90))
    recs.append(one("blobs", 2000, 1.0, True, 90, 60))
    recs.append(one("circle_noisy", 3000, 1.5, True, 180, 180))
    recs.append(one("circle_noisy", 4000, 1.5, False, 180, 360))
    ok = all(r.get("match_back") for r in recs) and all(
        r.get("match_ripser", True) for r in recs
    )
    write({
        "id": "suffix_stabilize",
        "lever": "H01-suffix-stab",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "suffix-stabilize vs full backward / Ripser (no first-keep oracle)",
        "receipts": recs,
    }, "I168")


if __name__ == "__main__":
    main()
