#!/usr/bin/env python3
"""I171/I172: early-keep C-empty rate + suffix-rescue identity/clock."""

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


def pith_cmd(path, T, alg, timeout=240, env=None):
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


def main():
    recs = []
    for name, n, T, timeout in (
        ("circle_noisy", 2000, 1.5, 60),
        ("circle_noisy", 3000, 1.5, 90),
        ("circle_noisy", 4000, 1.5, 120),
        ("blobs", 2000, 1.0, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, "back", timeout)
        rec = {
            "phase": "early_c",
            "name": name, "n": n, "T": T,
            "first_keep": cb.get("collapse_first_keep"),
            "early_keep_n": cb.get("collapse_early_keep_n"),
            "early_empty_c": cb.get("collapse_early_empty_c"),
            "edges_out": cb.get("edges_out"),
            "back_s": tb,
        }
        print(f"I171 early {rec}", flush=True)
        recs.append(rec)

    ident = []
    for name, n, T, vs_r, timeout, rto in (
        ("circle_noisy", 80, 1.2, True, 30, 30),
        ("circle_noisy", 2000, 1.5, True, 90, 90),
        ("circle_noisy", 3000, 1.5, True, 180, 180),
        ("blobs", 2000, 1.0, True, 90, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, "back", timeout)
        ps, cs, ts = pith_cmd(path, T, "suffix-rescue", timeout)
        fid = compare(pb, ps, 1)
        rec = {
            "phase": "rescue",
            "name": name, "n": n, "T": T,
            "match_back": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "back_s": tb, "rescue_s": ts,
            "vs_back": tb / ts if ts else None,
            "back_out": cb.get("edges_out"),
            "rescue_out": cs.get("edges_out"),
            "rescue_collapse_ms": cs.get("collapse_ms"),
            "rescue_probes": cs.get("collapse_c_probes"),
            "back_probes": cb.get("collapse_c_probes"),
        }
        if vs_r:
            pr, tr = ripser(path, T, rto)
            fidr = compare(pr, ps, 1)
            rec["match_ripser"] = fidr.get("exact_match_tol")
            rec["unmatched_ripser"] = fidr.get("unmatched")
            rec["ripser_s"] = tr
            rec["vs_ripser"] = tr / ts if ts else None
        print(f"I172 rescue {rec}", flush=True)
        ident.append(rec)
        recs.append(rec)

    ok = all(r.get("match_back") for r in ident) and all(r.get("match_ripser", True) for r in ident)
    write({
        "id": "suffix_rescue",
        "lever": "H01-suffix-rescue",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "early-keep C-empty rate + cheap-common-trim rescue vs back/Ripser",
        "receipts": recs,
    }, "I171")


if __name__ == "__main__":
    main()
