#!/usr/bin/env python3
"""I218: owned --sparse-eps 0.6 log-log |E(n)| / time slopes vs Ripser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, compare, essential, parse_pith_text, run_cmd  # noqa: E402
from run_wave66 import loglog_slope  # noqa: E402
from run_wave69 import bottleneck_h1, ripser  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def pith_sparse(path, T, timeout=120):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--sparse-eps", "0.6", "--sparse-cap", "max",
         "--collapse", "0", "--engine", "implicit", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def main():
    recs = []
    families = [
        ("circle_noisy", [500, 1000, 1500, 2000], 1.5),
        ("blobs", [500, 1000, 1500, 2000], 1.0),
        ("sphere", [500, 1000, 1500, 2000], 1.4),
        ("torus", [500, 1000, 1500, 2000], 1.6),
        ("uniform2", [500, 1000, 1500, 2000], 0.35),
    ]
    extra = [
        ("figure8", 500, 1.0),
        ("two_circles", 400, 1.2),
    ]
    for name, ns, T in families:
        for n in ns:
            path = BENCH / f"datasets/generated/{name}_n{n}.csv"
            if not path.exists():
                print(f"missing {path}", flush=True)
                continue
            rto = 180 if (name == "circle_noisy" and n >= 1500) else 90
            ps, cs, ts = pith_sparse(path, T, 120)
            pr, tr = ripser(path, T, rto)
            rec = {
                "name": name, "n": n, "T": T, "kind": "scale",
                "ess_ok": len(essential(ps, 1)) == len(essential(pr, 1)),
                "ess_vr": len(essential(pr, 1)),
                "ess_sp": len(essential(ps, 1)),
                "unmatched": compare(pr, ps, 1).get("unmatched"),
                "bn": bottleneck_h1(pr, ps),
                "pith_s": ts, "ripser_s": tr,
                "vs_ripser": tr / ts if ts else None,
                "edges": cs.get("edges_in"),
            }
            print(f"I218 {rec}", flush=True)
            recs.append(rec)

    for name, n, T in extra:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        if not path.exists():
            print(f"missing {path}", flush=True)
            continue
        ps, cs, ts = pith_sparse(path, T, 60)
        pr, tr = ripser(path, T, 60)
        rec = {
            "name": name, "n": n, "T": T, "kind": "extra-shape",
            "ess_ok": len(essential(ps, 1)) == len(essential(pr, 1)),
            "ess_vr": len(essential(pr, 1)),
            "ess_sp": len(essential(ps, 1)),
            "unmatched": compare(pr, ps, 1).get("unmatched"),
            "bn": bottleneck_h1(pr, ps),
            "pith_s": ts, "ripser_s": tr,
            "vs_ripser": tr / ts if ts else None,
            "edges": cs.get("edges_in"),
        }
        print(f"I218 extra {rec}", flush=True)
        recs.append(rec)

    slopes = {}
    for name, ns, T in families:
        rows = [r for r in recs if r["name"] == name and r.get("kind") == "scale"]
        if len(rows) < 2:
            continue
        xs = [r["n"] for r in rows]
        slopes[name] = {
            "n": xs,
            "slope_edges": loglog_slope(xs, [r.get("edges") or 0 for r in rows]),
            "slope_pith": loglog_slope(xs, [r.get("pith_s") or 0 for r in rows]),
            "slope_ripser": loglog_slope(xs, [r.get("ripser_s") or 0 for r in rows]),
            "ess_ok": all(r.get("ess_ok") for r in rows),
            "bn_max": max((r.get("bn") or 0) for r in rows),
        }
        print(f"I218 slope {name} {slopes[name]}", flush=True)

    edge_slopes = [v["slope_edges"] for v in slopes.values() if v.get("slope_edges") is not None]
    all_subquad = bool(edge_slopes) and all(s < 1.6 for s in edge_slopes)
    ess_ok = all(r.get("ess_ok") for r in recs) if recs else False
    write({
        "id": "owned_sparse_eps06_slopes",
        "lever": "H00-complexity",
        "class": "experiment",
        "fidelity": "approx",
        "status": "support" if ess_ok and all_subquad else ("partial" if ess_ok else "reject"),
        "summary": "I218 owned --sparse-eps 0.6 log-log |E(n)| / time vs Ripser",
        "receipts": recs,
        "slopes": slopes,
        "note": (
            "Justification for the optional approx Big-O claim. "
            "Sheehy/Cavanna–Jahanseir–Sheehy: greedy-net flag size is O(n) for fixed ε, k. "
            "Not exact VR; loss is bottleneck + unmatched short bars."
        ),
    }, "I218")


if __name__ == "__main__":
    main()
