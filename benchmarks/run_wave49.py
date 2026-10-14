#!/usr/bin/env python3
"""I182: live-bit AND generate-C vs default back (collapse_ms, residual)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, parse_pith_text, run_cmd  # noqa: E402

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


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 30),
        ("circle_noisy", 2000, 1.5, 90),
        ("circle_noisy", 3000, 1.5, 180),
        ("blobs", 2000, 1.0, 90),
    ]
    for name, n, T, timeout in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back-bits"], timeout)
        fid = compare(pb, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_back": fid.get("exact_match_tol"),
            "unmatched_back": fid.get("unmatched"),
            "back_s": tb, "bits_s": ts,
            "vs_back": tb / ts if ts else None,
            "back_out": cb.get("edges_out"),
            "out": cs.get("edges_out"),
            "back_collapse_ms": cb.get("collapse_ms"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "collapse_ratio": (cb.get("collapse_ms") or 0) / (cs.get("collapse_ms") or 1),
            "back_probes": cb.get("collapse_c_probes"),
            "bits_probes": cs.get("collapse_c_probes"),
            "back_c_size": cb.get("collapse_c_size"),
            "bits_c_size": cs.get("collapse_c_size"),
        }
        print(f"I182 {rec}", flush=True)
        recs.append(rec)

    n2000 = next((r for r in recs if r["n"] == 2000 and r["name"] == "circle_noisy"), None)
    cut = n2000 and n2000.get("match_back") and (n2000.get("collapse_ratio") or 0) >= 1.3
    ident = all(r.get("match_back") for r in recs)
    write({
        "id": "bitand_generate_c",
        "lever": "H01-bitand-generate-c",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if cut else ("partial" if ident else "reject"),
        "summary": "I182 live-bit AND generate-C vs default back",
        "receipts": recs,
    }, "I182")


if __name__ == "__main__":
    main()
