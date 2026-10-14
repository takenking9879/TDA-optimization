#!/usr/bin/env python3
"""One entry point for the stable PITH suite.

Default: cheap tests only (CLI + unit-style Python checks).
``--full`` re-runs the receipt scripts that already have JSON on disk.
It does not hunt for new micro-optimizations.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent
PITH_TEST = ROOT / "src" / "pith" / "build" / "pith_test"

FAST = [
    "test_cli_stable.py",
    "test_pith_api.py",
    "test_sparse_points.py",
    "test_baseline_hooks.py",
]

RECEIPTS = [
    "eval_mode_auto.py",
    "eval_engine_auto.py",
    "eval_estimate.py",
    "eval_ncc_auto.py",
    "eval_adversarial.py",
    "eval_highd_auto.py",
    "eval_wall_kind.py",
    "reverify_headlines.py",
    "reverify_leftover_10x.py",
    "reverify_fat_h2.py",
    "eval_implicit_h2.py",
    "eval_dense_metric.py",
    "eval_leftover_engines.py",
    "collect_topology_claims.py",
    "plot_consolidation.py",
    "plot_pd.py",
]


def run(script: str) -> int:
    path = BENCH / script
    print(f"\n=== {script} ===", flush=True)
    proc = subprocess.run([sys.executable, str(path)], cwd=str(ROOT))
    return proc.returncode


def main() -> int:
    p = argparse.ArgumentParser(description="Stable PITH tests / receipts")
    p.add_argument("--full", action="store_true", help="re-run consolidation receipts")
    args = p.parse_args()
    if PITH_TEST.exists():
        print("=== pith_test ===", flush=True)
        rc = subprocess.run([str(PITH_TEST)]).returncode
        if rc != 0:
            return rc
    else:
        print("pith_test missing; build src/pith first", file=sys.stderr)
        return 2
    for name in FAST:
        rc = run(name)
        if rc != 0:
            return rc
    if not args.full:
        print("ok stable tests (pass --full to re-measure receipts)")
        return 0
    for name in RECEIPTS:
        rc = run(name)
        if rc != 0:
            print(f"{name} failed with {rc}", file=sys.stderr)
            return rc
    print("ok full stable suite")
    return 0


if __name__ == "__main__":
    sys.exit(main())
