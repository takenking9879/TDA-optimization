#!/usr/bin/env python3
"""Axis scaling: T, noise, density, dimension — until a method becomes impractical.

1-thread PITH vs 1-thread Ripser (and giotto/GUDHI when cheap).
Empirical, not a theorem. Does not retune τ.
Writes benchmarks/results/consolidation/axis_scaling.json.
"""

from __future__ import annotations

import json
import math
import os
import resource
import sys
import time
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))

from generate_datasets import circle_noisy, figure8, uniform, write_csv  # noqa: E402
from ph_metrics import ess  # noqa: E402
from run_consolidation import (  # noqa: E402
    HAVE_GIOTTO,
    HAVE_GUDHI,
    GIOTTO_VER,
    GUDHI_VER,
    OUT,
    local_exp,
    run_estimate,
    run_giotto,
    run_gudhi_rips,
    run_ripser,
)
from run_suite import PITH, parse_pith_text, run_cmd  # noqa: E402

CLOUDS = BENCH / "datasets" / "generated"
NPROC = os.cpu_count() or 4
BUDGET_S = 8
THREADS = 1


def _rss_child():
    try:
        return resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss * 1024
    except Exception:
        return 0


def _cpu():
    try:
        ru = resource.getrusage(resource.RUSAGE_CHILDREN)
        return ru.ru_utime + ru.ru_stime
    except Exception:
        return 0.0


def run_pith(path, T, maxdim, mode="exact", engine="auto", threads=THREADS, timeout=BUDGET_S):
    cmd = [
        str(PITH),
        "--points",
        str(path),
        "--maxdim",
        str(maxdim),
        "--threshold",
        str(T),
        "--mode",
        mode,
        "--engine",
        engine,
        "--threads",
        str(threads),
        "--no-enclosing",
    ]
    rss0 = _rss_child()
    cpu0 = _cpu()
    t0 = time.perf_counter()
    try:
        out, dt, _ = run_cmd(cmd, timeout)
        pairs, c = parse_pith_text(out)
        err = None
    except Exception as e:
        pairs, c, dt, err = [], {}, time.perf_counter() - t0, str(e)
    cpu = max(0.0, _cpu() - cpu0)
    rss1 = _rss_child()
    timed_out = err is not None and "timed out" in (err or "").lower()
    return {
        "method": f"pith:{mode}:{engine}",
        "ok": err is None,
        "error": err,
        "timed_out": timed_out,
        "wall_s": None if err else dt,
        "cpu_s": cpu,
        "threads_used": threads,
        "hardware_cpus": NPROC,
        "rss_delta": max(0, rss1 - rss0),
        "rss_pith": c.get("rss") if c else None,
        "n_edges": c.get("n_edges_in") or c.get("edges_in") or c.get("n_edges"),
        "n_dist": c.get("distances"),
        "metric_ms": c.get("metric_ms"),
        "collapse_ms": c.get("collapse_ms"),
        "reduce_ms": c.get("reduce_ms"),
        "residual_frac": c.get("residual_frac"),
        "pipeline": c.get("pipeline"),
        "n_pairs": len(pairs) if pairs else 0,
        "ess0": ess(pairs, 0) if pairs else None,
        "ess1": ess(pairs, 1) if pairs else None,
        "ess2": ess(pairs, 2) if pairs else None,
        "counters": {k: c[k] for k in c if k not in ("pipeline",)},
    }


def cloud(name, n, fn):
    CLOUDS.mkdir(parents=True, exist_ok=True)
    path = CLOUDS / f"axis_{name}_n{n}.csv"
    write_csv(path, fn())
    return path


def slim(rec):
    keep = (
        "method",
        "ok",
        "error",
        "timed_out",
        "wall_s",
        "cpu_s",
        "threads_used",
        "threads_claimed",
        "hardware_cpus",
        "rss_delta",
        "rss_pith",
        "n_edges",
        "n_dist",
        "metric_ms",
        "collapse_ms",
        "reduce_ms",
        "residual_frac",
        "pipeline",
        "n_pairs",
        "ess0",
        "ess1",
        "ess2",
    )
    return {k: rec.get(k) for k in keep if k in rec}


def local_p(xs, ys):
    out = []
    for i in range(len(xs) - 1):
        p = local_exp(xs[i], ys[i], xs[i + 1], ys[i + 1])
        if p is not None:
            out.append({"x0": xs[i], "x1": xs[i + 1], "p": p})
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(14)
    dead = set()
    rows = []

    series = [
        {
            "axis": "threshold",
            "family": "circle_noisy",
            "n": 400,
            "maxdim": 1,
            "points": [
                (T, lambda T=T: circle_noisy(400, rng, 0.05), T) for T in (0.4, 0.8, 1.2, 1.6, 2.0)
            ],
        },
        {
            "axis": "threshold",
            "family": "figure8",
            "n": 800,
            "maxdim": 1,
            "points": [
                (T, lambda T=T: figure8(800, rng), T) for T in (0.5, 0.8, 1.1, 1.4)
            ],
        },
        {
            "axis": "noise",
            "family": "circle_noisy",
            "n": 500,
            "maxdim": 1,
            "points": [
                (sig, lambda sig=sig: circle_noisy(500, rng, sig), 1.5)
                for sig in (0.0, 0.05, 0.15, 0.30)
            ],
        },
        {
            "axis": "density",
            "family": "uniform2",
            "n": 800,
            "maxdim": 1,
            "points": [
                (T, lambda T=T: uniform(800, 2, rng), T) for T in (0.12, 0.20, 0.35, 0.55)
            ],
        },
        {
            "axis": "dimension",
            "family": "uniform",
            "n": 400,
            "maxdim": 1,
            "points": [
                (d, lambda d=d: uniform(400, d, rng), 0.45) for d in (2, 3, 4)
            ],
        },
        {
            "axis": "dimension",
            "family": "uniform",
            "n": 800,
            "maxdim": 1,
            "points": [
                (d, lambda d=d: uniform(800, d, rng), 0.40) for d in (2, 3)
            ],
        },
    ]

    methods = [
        ("pith_exact_auto", lambda p, T, md, d: run_pith(p, T, md, "exact", "auto")),
        ("pith_exact_redzed", lambda p, T, md, d: run_pith(p, T, md, "exact", "redzed")),
        ("ripser", lambda p, T, md, d: run_ripser(p, T, md, timeout=BUDGET_S)),
        ("pith_scale", lambda p, T, md, d: run_pith(p, T, md, "scale", "auto") if d in (2, 3) else {"method": "pith:scale:auto", "ok": False, "error": "scale requires d=2,3", "skip": True}),
        ("pith_sparse", lambda p, T, md, d: run_pith(p, T, md, "sparse", "auto")),
        ("giotto_t1", lambda p, T, md, d: run_giotto(p, T, md, n_threads=1, timeout=BUDGET_S) if HAVE_GIOTTO else {"method": "giotto-ph:t1", "ok": False, "error": "giotto missing", "skip": True}),
        ("gudhi_rips", lambda p, T, md, d: run_gudhi_rips(p, T, md, timeout=min(6, BUDGET_S)) if HAVE_GUDHI else {"method": "gudhi-rips", "ok": False, "error": "gudhi missing", "skip": True}),
    ]

    for ser in series:
        for x, maker, T in ser["points"]:
            pts = maker()
            d = int(pts.shape[1])
            path = cloud(f"{ser['axis']}_{ser['family']}_x{x}", ser["n"], lambda pts=pts: pts)
            est = run_estimate(path, T, ser["maxdim"])
            for mname, fn in methods:
                key = (ser["axis"], ser["family"], ser["n"], mname)
                if key in dead:
                    rows.append(
                        {
                            "axis": ser["axis"],
                            "family": ser["family"],
                            "n": ser["n"],
                            "x": x,
                            "T": T,
                            "dim": d,
                            "maxdim": ser["maxdim"],
                            "method": mname,
                            "ok": False,
                            "skipped_after_fail": True,
                        }
                    )
                    continue
                rec = fn(path, T, ser["maxdim"], d)
                if rec.get("skip"):
                    continue
                if mname == "ripser":
                    rec["threads_used"] = 1
                    rec["hardware_cpus"] = NPROC
                elif "threads_used" not in rec:
                    rec["threads_used"] = rec.get("threads_claimed", 1)
                    rec["hardware_cpus"] = NPROC
                row = {
                    "axis": ser["axis"],
                    "family": ser["family"],
                    "n": ser["n"],
                    "x": x,
                    "T": T,
                    "dim": d,
                    "maxdim": ser["maxdim"],
                    "method": mname,
                    "estimate": {
                        k: est.get(k)
                        for k in (
                            "engine_recommended",
                            "mode_recommended",
                            "residual_regime",
                            "wall_kind",
                            "growth_p",
                            "est_edges_hi",
                            "est_runtime_lo_s",
                            "est_runtime_hi_s",
                            "leaving_cheap_regime",
                            "auto_will_run",
                        )
                        if k in est
                    },
                    **slim(rec),
                }
                rows.append(row)
                failed = (not rec.get("ok")) or (
                    rec.get("wall_s") is not None and rec["wall_s"] > BUDGET_S * 0.95
                )
                if failed and not rec.get("skip"):
                    dead.add(key)
                print(
                    f"{ser['axis']} {ser['family']} n={ser['n']} x={x} {mname}: "
                    f"{'ok '+format(rec.get('wall_s') or 0, '.3f')+'s' if rec.get('ok') else rec.get('error','fail')[:80]}",
                    flush=True,
                )

    # Local exponents along each (axis, family, n, method) where x increases.
    exponents = []
    grouped = {}
    for r in rows:
        if not r.get("ok") or r.get("wall_s") is None:
            continue
        k = (r["axis"], r["family"], r["n"], r["method"])
        grouped.setdefault(k, []).append(r)
    for k, rs in grouped.items():
        rs = sorted(rs, key=lambda z: float(z["x"]))
        xs = [float(z["x"]) for z in rs]
        ts = [z["wall_s"] for z in rs]
        es = [z.get("n_edges") for z in rs]
        exponents.append(
            {
                "axis": k[0],
                "family": k[1],
                "n": k[2],
                "method": k[3],
                "p_time": local_p(xs, ts),
                "p_edges": local_p(xs, [float(e) for e in es])
                if all(e not in (None, 0) for e in es)
                else [],
            }
        )

    limits = []
    for (axis, family, n, method), rs in grouped.items():
        last = max(rs, key=lambda z: float(z["x"]))
        limits.append(
            {
                "axis": axis,
                "family": family,
                "n": n,
                "method": method,
                "last_ok_x": last["x"],
                "last_ok_wall_s": last["wall_s"],
                "failed_later": any(
                    r.get("skipped_after_fail") or (not r.get("ok") and r.get("method") == method)
                    for r in rows
                    if r["axis"] == axis
                    and r["family"] == family
                    and r["n"] == n
                    and r["method"] == method
                    and not r.get("ok")
                ),
            }
        )

    payload = {
        "hardware": {
            "cpus": NPROC,
            "threads_pith": THREADS,
            "threads_ripser": 1,
            "budget_s": BUDGET_S,
            "note": "axis scaling; 1-thread PITH vs 1-thread Ripser; empirical",
        },
        "giotto": GIOTTO_VER,
        "gudhi": GUDHI_VER,
        "receipts": rows,
        "exponents": exponents,
        "limits": limits,
    }
    dest = OUT / "axis_scaling.json"
    dest.write_text(json.dumps(payload, indent=2))
    print(f"wrote {dest} rows={len(rows)} exponents={len(exponents)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
