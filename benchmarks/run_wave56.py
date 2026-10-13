#!/usr/bin/env python3
"""I193 multi-apex AND-eq + I192 vertex-domination count on G_T."""

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


def vertex_probe(path, T, timeout=60):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--threshold", str(T),
         "--probe-vertex", "--no-enclosing"],
        timeout,
    )
    rec = {"probe_s": dt, "raw": out.strip().splitlines()[-1] if out.strip() else ""}
    for tok in rec["raw"].split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            try:
                rec[k] = float(v) if "." in v else int(v)
            except ValueError:
                rec[k] = v
    return rec


def main():
    recs = []
    jobs = [
        ("circle_noisy", 80, 1.2, 30, 30),
        ("circle_noisy", 2000, 1.5, 90, 90),
        ("blobs", 2000, 1.0, 90, 60),
        ("sphere", 2000, 1.4, 90, 60),
        ("torus", 2000, 1.6, 90, 90),
    ]
    for name, n, T, timeout, rto in jobs:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        pb, cb, tb = pith_cmd(path, T, ["--collapse-alg", "back-src"], timeout)
        ps, cs, ts = pith_cmd(path, T, ["--collapse-alg", "back"], timeout)
        pr, tr = ripser(path, T, rto)
        fid = compare(pb, ps, 1)
        fidr = compare(pr, ps, 1)
        rec = {
            "name": name, "n": n, "T": T,
            "match_src": fid.get("exact_match_tol"),
            "unmatched_src": fid.get("unmatched"),
            "match_ripser": fidr.get("exact_match_tol"),
            "unmatched_ripser": fidr.get("unmatched"),
            "src_s": tb, "bits_s": ts, "ripser_s": tr,
            "vs_src": tb / ts if ts else None,
            "vs_ripser": tr / ts if ts else None,
            "src_out": cb.get("edges_out"),
            "out": cs.get("edges_out"),
            "src_collapse_ms": cb.get("collapse_ms"),
            "bits_collapse_ms": cs.get("collapse_ms"),
            "collapse_ratio": (cb.get("collapse_ms") or 0) / (cs.get("collapse_ms") or 1),
            "fast_trims": cs.get("collapse_fast_trims"),
            "trims": cs.get("collapse_trims"),
            "dom_tests": cs.get("collapse_dom_tests"),
        }
        print(f"I193 {rec}", flush=True)
        recs.append(rec)

    ident = all(r.get("match_ripser") for r in recs)
    n2000 = next((r for r in recs if r["name"] == "circle_noisy" and r["n"] == 2000), None)
    circle_ok = n2000 and n2000.get("match_ripser") and (n2000.get("bits_collapse_ms") or 9e9) < 400
    i189 = {"blobs": 809, "sphere": 1553, "torus": 1849}
    loser_gain = any(
        r["name"] in i189 and (r.get("bits_collapse_ms") or 9e9) < 0.85 * i189[r["name"]]
        for r in recs
    )
    write({
        "id": "multi_apex_and_eq",
        "lever": "H01-multi-apex-and-eq",
        "class": "experiment",
        "fidelity": "exact" if ident else "unverified",
        "status": "support" if ident and circle_ok and loser_gain else (
            "partial" if ident and circle_ok else "reject"
        ),
        "summary": "I193 multi-apex AND-eq when !any_later vs src/Ripser",
        "receipts": recs,
    }, "I193")

    vrecs = []
    for name, n, T, _, _ in jobs:
        if n < 200:
            continue
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        rec = vertex_probe(path, T)
        rec["name"] = name
        rec["n"] = n
        rec["T"] = T
        print(f"I192 {rec}", flush=True)
        vrecs.append(rec)
    blobs = next((r for r in vrecs if r.get("name") == "blobs"), None)
    enough = blobs and (blobs.get("frac") or 0) >= 0.30
    write({
        "id": "vertex_dom_count",
        "lever": "H01-vertex-collapse",
        "class": "experiment",
        "fidelity": "n/a",
        "status": "support" if enough else "reject",
        "summary": "I192 dominated-vertex fraction on G_T (need ≥0.30 on blobs to implement)",
        "receipts": vrecs,
    }, "I192")


if __name__ == "__main__":
    main()
