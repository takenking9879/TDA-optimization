#!/usr/bin/env python3
"""Evaluate --mode auto against the frozen feasibility probe on held-out families."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    circle_noisy,
    mixed_1d2d3d,
    many_loops,
    nested_loops,
    sphere,
    uniform4,
    write_csv,
)
from run_suite import PITH  # noqa: E402
from run_wave85 import figure8  # noqa: E402
import numpy as np

OUT = BENCH / "results" / "consolidation"
CLOUDS = BENCH / "datasets" / "generated"


def run_auto(path, T, maxdim, timeout=20):
    proc = subprocess.run(
        [
            str(PITH),
            "--points",
            str(path),
            "--mode",
            "auto",
            "--maxdim",
            str(maxdim),
            "--threshold",
            str(T),
            "--no-enclosing",
            "--threads",
            "1",
        ],
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    selected = None
    for line in proc.stderr.splitlines():
        if line.startswith("# MODE auto selected"):
            selected = line.split()[4]
    return {
        "ok": proc.returncode == 0,
        "selected": selected,
        "stderr": proc.stderr[-800:],
        "has_h1": "persistence intervals in dim 1" in proc.stdout,
        "pipeline": next(
            (tok.split("=", 1)[1] for tok in proc.stdout.split() if tok.startswith("pipeline=")),
            None,
        ),
    }


def main():
    rng = np.random.default_rng(2)
    cases = [
        ("circle_noisy", circle_noisy, 400, 1.5, 1, "exact"),
        ("figure8", figure8, 400, 1.1, 1, "exact"),
        ("many_loops", many_loops, 400, 1.2, 1, "exact"),
        ("nested_loops", nested_loops, 400, 1.6, 1, "exact"),
        ("sphere", sphere, 400, 1.4, 2, "exact"),
        ("mixed_1d2d3d", mixed_1d2d3d, 300, 1.4, 2, "scale"),
        ("figure8", figure8, 16000, 1.1, 1, "scale"),
        ("sphere", sphere, 16000, 1.4, 2, "scale"),
        ("uniform4", uniform4, 5000, 1.0, 1, "sparse"),
    ]
    recs = []
    for name, fn, n, T, dim, expect in cases:
        path = CLOUDS / f"{name}_n{n}.csv"
        if not path.exists():
            write_csv(path, fn(n, rng))
        print(f"AUTO {name} n={n} expect={expect}", flush=True)
        got = run_auto(path, T, dim, timeout=25)
        got.update({"name": name, "n": n, "T": T, "maxdim": dim, "expect": expect})
        got["agree"] = got.get("selected") == expect
        print(f"  selected={got.get('selected')} pipeline={got.get('pipeline')} agree={got['agree']}", flush=True)
        recs.append(got)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "mode_auto.json"
    path.write_text(json.dumps({"receipts": recs, "n_agree": sum(1 for r in recs if r["agree"]), "n": len(recs)}, indent=2))
    print(f"wrote {path} {sum(1 for r in recs if r['agree'])}/{len(recs)} agree")


if __name__ == "__main__":
    main()
