#!/usr/bin/env python3
"""I176/I177: Case A/B any_later + suffix-later identity/clock."""

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


def pith_cmd(path, T, extra, timeout=240):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing"] + extra,
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
        _, c, dt = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        rec = {
            "phase": "later_ab",
            "name": name, "n": n, "T": T, "back_s": dt,
            "early_keep_n": c.get("collapse_early_keep_n"),
            "early_any_later": c.get("collapse_early_any_later"),
            "early_later_a": c.get("collapse_early_later_a"),
            "early_later_b": c.get("collapse_early_later_b"),
            "early_fail_max": c.get("collapse_early_fail_max"),
            "edges_out": c.get("edges_out"),
        }
        print(f"I176 laterAB {rec}", flush=True)
        recs.append(rec)

    ident = []
    for name, n, T, timeout, vs_r, rto in (
        ("circle_noisy", 80, 1.2, 30, True, 30),
        ("circle_noisy", 2000, 1.5, 90, True, 90),
        ("circle_noisy", 3000, 1.5, 180, True, 180),
        ("blobs", 2000, 1.0, 90, True, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr = tr = None
        if vs_r:
            pr, tr = ripser(path, T, rto)
        for k in (2, 8):
            ps, cs, ts = pith_cmd(
                path, T, ["--collapse-alg", "suffix-later", "--suffix-k", str(k)], timeout
            )
            fid = compare(pb, ps, 1)
            rec = {
                "phase": "suffix_later",
                "name": name, "n": n, "T": T, "K": k,
                "match_back": fid.get("exact_match_tol"),
                "unmatched": fid.get("unmatched"),
                "back_s": tb, "pith_s": ts,
                "vs_back": tb / ts if ts else None,
                "back_out": cb.get("edges_out"),
                "out": cs.get("edges_out"),
                "collapse_ms": cs.get("collapse_ms"),
                "probes": cs.get("collapse_c_probes"),
                "back_probes": cb.get("collapse_c_probes"),
            }
            if pr is not None:
                fidr = compare(pr, ps, 1)
                rec["match_ripser"] = fidr.get("exact_match_tol")
                rec["unmatched_ripser"] = fidr.get("unmatched")
                rec["ripser_s"] = tr
                rec["vs_ripser"] = tr / ts if ts else None
            print(f"I177 later {rec}", flush=True)
            ident.append(rec)
            recs.append(rec)

    ok = all(r.get("match_back") for r in ident)
    write({
        "id": "suffix_later",
        "lever": "H01-suffix-later",
        "class": "experiment",
        "fidelity": "exact" if ok else "unverified",
        "status": "support" if ok else "reject",
        "summary": "Case A/B any_later + suffix-later (Case-A leave then K-sample) vs back/Ripser",
        "receipts": recs,
    }, "I176")


if __name__ == "__main__":
    main()
