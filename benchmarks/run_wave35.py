#!/usr/bin/env python3
"""I163: leftover-apparent ROI probe on I162 families + circle T=1.5."""

from __future__ import annotations

import json
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def parse_probe(text: str) -> dict:
    for line in text.splitlines():
        if line.startswith("# PROBE"):
            rec = {}
            for tok in line.split()[2:]:
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    try:
                        rec[k] = float(v) if "." in v else int(v)
                    except ValueError:
                        rec[k] = v
            return rec
    raise RuntimeError("no # PROBE line")


def I163_probe():
    cases = (
        ("circle_noisy", 2000, 1.5),
        ("circle_noisy", 2000, 1.2),
        ("blobs", 2000, 1.0),
        ("torus", 2000, 1.6),
        ("sphere", 2000, 1.4),
        ("uniform2", 2000, 0.35),
        ("circle_noisy", 200, 1.5),
    )
    recs = []
    for name, n, T in cases:
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        out, dt, _ = run_cmd(
            [str(PITH), "--points", str(path), "--threshold", str(T),
             "--probe-only", "--no-enclosing"],
            60,
        )
        rec = parse_probe(out)
        rec.update({"name": name, "n": n, "T": T, "probe_s": dt})
        recs.append(rec)
        print(f"I163 {name} n={n} T={T} apparent={rec.get('leftover_apparent')} "
              f"leftover={rec.get('leftover')} mean_deg={rec.get('mean_deg')} "
              f"mst_max={rec.get('mst_max')} leftover_median={rec.get('leftover_median')} "
              f"dom={rec.get('domination')} s={dt:.3f}", flush=True)
    write({
        "id": "roi_probe",
        "lever": "H01-roi",
        "class": "experiment",
        "fidelity": "exact",
        "status": "support",
        "summary": "leftover-apparent / MST / domination probe on I162 families",
        "i162_clock": {
            "circle_1.5": 7.20,
            "circle_1.2": 4.13,
            "torus": 0.74,
            "blobs": 0.32,
            "uniform2": 0.30,
            "sphere": 0.17,
        },
        "receipts": recs,
    }, "I163")


def main():
    I163_probe()


if __name__ == "__main__":
    main()
