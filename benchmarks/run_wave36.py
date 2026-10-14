#!/usr/bin/env python3
"""I164: collapse live-degree trace (when does the 1-skeleton thin?)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from run_suite import PITH, RESULTS, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"
TRACE_RE = re.compile(
    r"# COLLAPSE_TRACE i=(\d+)/(\d+) live=(\d+) kept=(\d+) trims=(\d+)"
)


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def I164_trace():
    recs = []
    for name, n, T, timeout in (
        ("circle_noisy", 2000, 1.5, 60),
        ("blobs", 2000, 1.0, 60),
        ("sphere", 2000, 1.4, 60),
    ):
        path = BENCH / f"datasets/generated/{name}_n{n}.csv"
        import subprocess, time
        t0 = time.perf_counter()
        import os
        env = os.environ.copy()
        env["PITH_COLLAPSE_TRACE"] = "1"
        proc = subprocess.run(
            [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
             "--collapse", "1", "--engine", "implicit", "--no-enclosing"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout,
            env=env,
        )
        dt = time.perf_counter() - t0
        traces = []
        for m in TRACE_RE.finditer(proc.stderr):
            traces.append({
                "i": int(m.group(1)), "m": int(m.group(2)),
                "live": int(m.group(3)), "kept": int(m.group(4)),
                "trims": int(m.group(5)),
                "frac": int(m.group(1)) / int(m.group(2)),
            })
            print(f"I164 {name} {traces[-1]}", flush=True)
        recs.append({"name": name, "n": n, "T": T, "pith_s": dt, "traces": traces})
    write({
        "id": "collapse_live_trace",
        "lever": "H01-early-stop",
        "class": "experiment",
        "fidelity": "exact",
        "status": "support",
        "summary": "live 1-skeleton size vs backward scan fraction",
        "receipts": recs,
    }, "I164")


def main():
    I164_trace()


if __name__ == "__main__":
    main()
