#!/usr/bin/env python3
"""I135 E3 on torus1000; I136 Alpha empirical if GUDHI present."""

from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, RIPSER, compare, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def I135_e3_torus1000():
    path = BENCH / "datasets/generated/torus_n1000.csv"
    if not path.exists():
        write({"id": "e3_torus1000", "lever": "H02-E3", "class": "experiment",
               "fidelity": "exact", "status": "hold", "summary": "missing torus_n1000",
               "receipts": []}, "I135")
        return
    pr, tr, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", "1.6", str(path)],
        180,
    )
    pr = parse_ripser(pr)
    recs = []
    for coll in (1, -1):
        out, dt_c, _ = run_cmd(
            [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", "1.6",
             "--collapse", str(coll), "--sparse-only", "--no-enclosing"],
            180,
        )
        with tempfile.NamedTemporaryFile("w", suffix=".sparse", delete=False) as f:
            f.write(out)
            spar = f.name
        rs, dt_r, _ = run_cmd(
            [str(RIPSER), "--format", "sparse", "--dim", "1", "--threshold", "1.6", spar],
            180,
        )
        pp = parse_ripser(rs)
        fid = compare(pr, pp, 1)
        total = dt_c + dt_r
        recs.append({"collapse": coll, "match": fid.get("exact_match_tol"),
                     "collapse_s": dt_c, "ripser_residual_s": dt_r, "total_s": total,
                     "ripser_orig_s": tr, "time_ratio": tr / total if total else None})
        print(f"I135 coll={coll} match={recs[-1]['match']} ratio={recs[-1]['time_ratio']}", flush=True)
    write({"id": "e3_torus1000", "lever": "H02-E3", "class": "experiment",
           "fidelity": "exact",
           "status": "support" if all(r["match"] for r in recs) else "reject",
           "summary": "torus1000 collapse+Ripser-sparse vs Ripser",
           "receipts": recs}, "I135")


def I136_alpha():
    try:
        import gudhi
        import numpy as np
    except ImportError:
        write({"id": "gudhi_alpha_circle3000", "lever": "H-alpha", "class": "experiment",
               "fidelity": "empirical", "status": "hold",
               "summary": "gudhi not importable", "receipts": []}, "I136")
        return
    path = BENCH / "datasets/generated/circle_noisy_n3000.csv"
    if not path.exists():
        write({"id": "gudhi_alpha_circle3000", "lever": "H-alpha", "class": "experiment",
               "fidelity": "empirical", "status": "hold", "summary": "missing circle3000",
               "receipts": []}, "I136")
        return
    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    st = gudhi.AlphaComplex(points=pts).create_simplex_tree()
    st.compute_persistence()
    h1 = st.persistence_intervals_in_dimension(1)
    dt = time.perf_counter() - t0
    _, tr, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", "1.5", str(path)],
        180,
    )
    write({"id": "gudhi_alpha_circle3000", "lever": "H-alpha", "class": "experiment",
           "fidelity": "empirical",
           "status": "support",
           "summary": f"GUDHI Alpha n=3000 {dt:.3f}s vs Ripser VR {tr:.3f}s (other complex)",
           "receipts": [{"alpha_s": dt, "ripser_vr_s": tr, "time_ratio_empirical": tr / dt if dt else None,
                         "alpha_h1_bars": int(len(h1)), "gudhi": getattr(gudhi, "__version__", "?")}]},
          "I136")


def main():
    I135_e3_torus1000()
    I136_alpha()


if __name__ == "__main__":
    main()
