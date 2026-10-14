#!/usr/bin/env python3
"""Smoke the stable CLI: --mode, --estimate, --help (no I-numbers in help)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import circle_noisy, uniform4, write_csv  # noqa: E402
from run_suite import PITH  # noqa: E402


def main():
    if not PITH.exists():
        print("PITH binary missing", file=sys.stderr)
        return 2
    help_txt = subprocess.check_output([str(PITH), "--help"], text=True, stderr=subprocess.STDOUT)
    if "I263" in help_txt or "I297" in help_txt or "suffix-later" in help_txt:
        print("stable --help still exposes research flags or I-numbers", file=sys.stderr)
        return 1
    if "--mode" not in help_txt or "--estimate" not in help_txt or "--threads" not in help_txt:
        print("stable --help missing --mode/--estimate/--threads", file=sys.stderr)
        return 1
    if "exact|scale|sparse|auto" not in help_txt:
        print("stable --help missing --mode auto", file=sys.stderr)
        return 1
    exp = subprocess.check_output([str(PITH), "--help-experimental"], text=True, stderr=subprocess.STDOUT)
    if "--delaunay-vr" not in exp or "--dense-metric" not in exp:
        print("experimental help missing compat flags", file=sys.stderr)
        return 1

    rng = np.random.default_rng(0)
    path = BENCH / "datasets" / "generated" / "cli_smoke_n80.csv"
    write_csv(path, circle_noisy(80, rng))
    est = subprocess.check_output(
        [str(PITH), "--estimate", "--points", str(path), "--maxdim", "1", "--threshold", "1.5", "--format", "json"],
        text=True,
    )
    js = json.loads(est)
    if js.get("kind") != "estimate" or "engine_recommended" not in js:
        print("estimate JSON incomplete", js, file=sys.stderr)
        return 1
    for key in (
        "residual_regime",
        "est_edges_hi",
        "est_residual_edges",
        "confidence",
        "threads",
        "est_runtime_lo_s",
        "est_runtime_hi_s",
        "growth_p",
        "leaving_cheap_regime",
        "est_sparse_runtime_s",
        "est_exact_runtime_s",
        "n_components",
        "n_cc_max",
        "skips_dense_matrix",
        "auto_will_run",
        "wall_kind",
    ):
        if key not in js:
            print("estimate JSON missing", key, js, file=sys.stderr)
            return 1

    out = subprocess.check_output(
        [str(PITH), "--points", str(path), "--mode", "exact", "--maxdim", "1", "--threshold", "1.5", "--no-enclosing"],
        text=True,
    )
    if "persistence intervals in dim 1" not in out:
        print("exact mode produced no H1 block", file=sys.stderr)
        return 1
    out1 = subprocess.check_output(
        [
            str(PITH),
            "--points",
            str(path),
            "--mode",
            "exact",
            "--threads",
            "1",
            "--maxdim",
            "1",
            "--threshold",
            "1.5",
            "--no-enclosing",
        ],
        text=True,
    )
    if "threads=1" not in out1:
        print(" --threads 1 did not appear in counters", file=sys.stderr)
        return 1
    auto = subprocess.run(
        [
            str(PITH),
            "--points",
            str(path),
            "--mode",
            "auto",
            "--maxdim",
            "1",
            "--threshold",
            "1.5",
            "--no-enclosing",
            "--threads",
            "1",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if auto.returncode != 0 or "persistence intervals in dim 1" not in auto.stdout:
        print("mode auto failed", auto.stderr, file=sys.stderr)
        return 1
    if "MODE auto selected" not in auto.stderr:
        print("mode auto did not report the selected path", auto.stderr, file=sys.stderr)
        return 1
    sparse = subprocess.check_output(
        [
            str(PITH),
            "--points",
            str(path),
            "--mode",
            "sparse",
            "--maxdim",
            "1",
            "--threshold",
            "1.5",
            "--no-enclosing",
            "--threads",
            "1",
        ],
        text=True,
    )
    if "pipeline=pith:sparse" not in sparse:
        print("sparse mode did not tag pipeline=pith:sparse", file=sys.stderr)
        return 1

    # Fat 4D H2: probe recommends sparse, but auto must refuse (exit 3)
    # instead of hanging. Explicit --mode sparse is still allowed.
    four = BENCH / "datasets" / "generated" / "cli_refuse_uniform4_n250.csv"
    write_csv(four, uniform4(250, np.random.default_rng(4)))
    est4 = json.loads(
        subprocess.check_output(
            [
                str(PITH),
                "--estimate",
                "--points",
                str(four),
                "--maxdim",
                "2",
                "--threshold",
                "0.6",
                "--format",
                "json",
            ],
            text=True,
        )
    )
    if est4.get("mode_recommended") != "sparse" or est4.get("auto_will_run") is not False:
        print("4D fat H2 estimate should recommend sparse and auto_will_run=false", est4, file=sys.stderr)
        return 1
    refuse = subprocess.run(
        [
            str(PITH),
            "--points",
            str(four),
            "--mode",
            "auto",
            "--maxdim",
            "2",
            "--threshold",
            "0.6",
            "--no-enclosing",
            "--threads",
            "1",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if refuse.returncode != 3 or "refusing" not in refuse.stderr:
        print("mode auto should refuse fat H2 sparse on d=4", refuse.returncode, refuse.stderr, file=sys.stderr)
        return 1
    if "MODE auto selected sparse" not in refuse.stderr:
        print("refuse path should still report the probe selection", refuse.stderr, file=sys.stderr)
        return 1
    h1_auto = subprocess.run(
        [
            str(PITH),
            "--points",
            str(four),
            "--mode",
            "auto",
            "--maxdim",
            "1",
            "--threshold",
            "0.6",
            "--no-enclosing",
            "--threads",
            "1",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if h1_auto.returncode != 0 or "refusing" in h1_auto.stderr:
        print("4D H1 auto should still run", h1_auto.returncode, h1_auto.stderr, file=sys.stderr)
        return 1
    print("ok stable CLI")
    return 0


if __name__ == "__main__":
    sys.exit(main())
