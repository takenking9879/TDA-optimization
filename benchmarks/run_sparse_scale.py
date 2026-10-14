#!/usr/bin/env python3
"""Push fused Euclidean --mode sparse until it leaves the 12 s budget.

Compares scale on the same clouds. Records local exponents. Empirical.
Hardware: 4 CPU / 16 GB. PITH --threads 1. Does not retune τ.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import (  # noqa: E402
    circle_noisy,
    disconnected_circles,
    nested_loops,
    uniform4,
    write_csv,
)
from run_consolidation import local_exp, run_estimate  # noqa: E402
from run_consolidation_limits import cloud, run_pith  # noqa: E402
from run_wave85 import figure8  # noqa: E402
from run_wave95 import ess  # noqa: E402

OUT = BENCH / "results" / "consolidation"
BUDGET_S = 12


def main() -> int:
    rng = np.random.default_rng(11)
    report = {"budget_s": BUDGET_S, "threads": 1, "series": [], "exponents": [], "estimates": []}
    families = (
        ("figure8", figure8, 1.1, 1, (2000, 4000, 8000, 12000, 16000, 24000)),
        ("circle_noisy", circle_noisy, 1.5, 1, (2000, 4000, 8000, 12000)),
        ("nested_loops", nested_loops, 1.6, 1, (2000, 4000, 8000)),
        ("disconnected_circles", disconnected_circles, 1.5, 1, (2000, 4000, 8000)),
        ("uniform4", uniform4, 1.0, 1, (400, 800, 1600)),
    )
    for name, fn, T, dim, ns in families:
        prev = {}
        for n in ns:
            path = cloud(f"sparse_scale_{name}", n, fn, rng)
            est = run_estimate(path, T, dim, timeout=20)
            report["estimates"].append({"name": name, "n": n, "T": T, "maxdim": dim, **est})
            for mode in ("sparse", "scale"):
                if name == "uniform4" and mode == "scale":
                    rec = {"name": name, "n": n, "mode": mode, "ok": False, "error": "no-delaunay-d4"}
                    report["series"].append(rec)
                    print(f"{name} n={n} {mode}: skipped (d=4)", flush=True)
                    continue
                run = run_pith(path, T, dim, mode, "auto", threads=1, timeout=BUDGET_S)
                rec = {
                    "name": name,
                    "n": n,
                    "T": T,
                    "maxdim": dim,
                    "mode": mode,
                    "ok": run.get("ok"),
                    "timed_out": run.get("timed_out"),
                    "wall_s": run.get("wall_s"),
                    "metric_ms": run.get("metric_ms"),
                    "reduce_ms": run.get("reduce_ms"),
                    "n_edges_in": run.get("n_edges_in"),
                    "n_dist": run.get("n_dist"),
                    "rss": run.get("rss_pith"),
                    "threads": run.get("threads_pith"),
                    "ess1": run.get("ess1"),
                    "pipeline": run.get("pipeline"),
                }
                key = (name, mode)
                if key in prev and prev[key].get("ok") and rec.get("ok"):
                    rec["local_p"] = local_exp(prev[key]["n"], prev[key]["wall_s"], n, rec["wall_s"])
                    rec["local_p_edges"] = local_exp(
                        prev[key]["n"], prev[key].get("n_edges_in") or 1, n, rec.get("n_edges_in") or 1
                    )
                    report["exponents"].append(
                        {
                            "name": name,
                            "mode": mode,
                            "n0": prev[key]["n"],
                            "n1": n,
                            "p_wall": rec["local_p"],
                            "p_edges": rec["local_p_edges"],
                        }
                    )
                prev[key] = {"n": n, **rec}
                report["series"].append(rec)
                print(
                    f"{name} n={n} {mode}: ok={rec['ok']} wall={rec['wall_s']} "
                    f"edges={rec['n_edges_in']} ess1={rec['ess1']} p={rec.get('local_p')}",
                    flush=True,
                )
                if mode == "sparse" and (run.get("timed_out") or not run.get("ok")):
                    break

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "sparse_scale.json"
    path.write_text(json.dumps(report, indent=2))
    print(f"wrote {path} series={len(report['series'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
