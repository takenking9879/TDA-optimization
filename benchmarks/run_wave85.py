#!/usr/bin/env python3
"""I224: paper-faithful reduced VR (H07) vs Ripser on mixed homology.

Shape-agnostic: same --reduced-vr path for circle / blobs / sphere / torus /
uniform / figure8 / two_circles / unit square. Quantify topology (unmatched,
essential H1, bottleneck) and triangle-count slopes vs Ripser / default PITH.
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import blobs, circle_noisy, sphere, torus, uniform, write_csv  # noqa: E402
from run_suite import PITH, RESULTS, RIPSER, compare, parse_pith_text, parse_ripser, run_cmd  # noqa: E402

OUT = RESULTS / "iterations"
GEN = BENCH / "datasets" / "generated"


def write(entry, iid):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{iid}_{entry['id']}.json"
    path.write_text(json.dumps(entry, indent=2))
    print(f"wrote {path} status={entry.get('status')} {entry.get('summary')}", flush=True)


def ensure_cloud(name, n, fn, rng):
    GEN.mkdir(parents=True, exist_ok=True)
    path = GEN / f"{name}_n{n}.csv"
    if not path.exists():
        write_csv(path, fn(n, rng))
    return path


def two_circles(n, rng):
    half = n // 2
    t = rng.uniform(0, 2 * math.pi, half)
    a = np.stack([np.cos(t), np.sin(t)], 1) + rng.normal(0, 0.05, (half, 2))
    t = rng.uniform(0, 2 * math.pi, n - half)
    b = np.stack([np.cos(t) + 3, np.sin(t)], 1) + rng.normal(0, 0.05, (n - half, 2))
    return np.vstack([a, b])


def figure8(n, rng):
    half = n // 2
    t = rng.uniform(0, 2 * math.pi, half)
    a = np.stack([np.cos(t), np.sin(t)], 1)
    t = rng.uniform(0, 2 * math.pi, n - half)
    b = np.stack([np.cos(t) + 2, np.sin(t)], 1)
    return np.vstack([a, b]) + rng.normal(0, 0.04, (n, 2))


def unit_square_path():
    GEN.mkdir(parents=True, exist_ok=True)
    path = GEN / "unit_square_n4.csv"
    write_csv(path, np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]]))
    return path


def pith_reduced(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "0", "--reduced-vr", "--no-enclosing"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def pith_default(path, T, timeout=180):
    out, dt, _ = run_cmd(
        [str(PITH), "--points", str(path), "--maxdim", "1", "--threshold", str(T),
         "--collapse", "1", "--engine", "implicit", "--no-enclosing",
         "--collapse-alg", "back"],
        timeout,
    )
    pairs, c = parse_pith_text(out)
    return pairs, c, dt


def ripser(path, T, timeout=120):
    out, dt, _ = run_cmd(
        [str(RIPSER), "--format", "point-cloud", "--dim", "1", "--threshold", str(T), str(path)],
        timeout,
    )
    return parse_ripser(out), dt


def ess1(pairs):
    return sum(1 for p in pairs if p["dim"] == 1 and not math.isfinite(p["death"]))


def loglog_slope(xs, ys):
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x and y and x > 0 and y > 0]
    if len(pts) < 2:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den <= 0:
        return None
    return sum((p[0] - mx) * (p[1] - my) for p in pts) / den


def bottleneck_h1(a, b):
    """Greedy L∞ matching on dim-1 bars (finite + essential as death=1e9)."""
    def bars(pairs):
        out = []
        for p in pairs:
            if p["dim"] != 1:
                continue
            birth, death = p["birth"], p["death"]
            if math.isfinite(death) and death - birth <= 1e-6:
                continue
            out.append((birth, death if math.isfinite(death) else 1e9))
        return out

    aa, bb = bars(a), bars(b)
    used = [False] * len(bb)
    worst = 0.0
    unmatched = 0
    for birth, death in aa:
        best = None
        best_j = None
        for j, (b2, d2) in enumerate(bb):
            if used[j]:
                continue
            sc = max(abs(birth - b2), abs(death - d2) if (death < 1e8 and d2 < 1e8) else (0.0 if death >= 1e8 and d2 >= 1e8 else 1e9))
            if best is None or sc < best:
                best, best_j = sc, j
        if best is not None and best < 1e8:
            used[best_j] = True
            worst = max(worst, best)
        else:
            unmatched += 1
            worst = max(worst, 1e9)
    unmatched += sum(1 for u in used if not u)
    if unmatched:
        return None
    return worst


def main():
    rng = np.random.default_rng(0)
    recs = []

    jobs = [
        ("unit_square", 4, 2.0, lambda n, r: np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0]])),
        ("circle_noisy", 80, 1.2, circle_noisy),
        ("circle_noisy", 200, 1.5, circle_noisy),
        ("blobs", 80, 1.0, blobs),
        ("blobs", 200, 1.0, blobs),
        ("sphere", 80, 1.4, sphere),
        ("sphere", 200, 1.4, sphere),
        ("torus", 80, 1.6, torus),
        ("torus", 200, 1.6, torus),
        ("uniform2", 80, 0.35, lambda n, r: uniform(n, 2, r)),
        ("uniform2", 200, 0.35, lambda n, r: uniform(n, 2, r)),
        ("two_circles", 80, 1.2, two_circles),
        ("two_circles", 200, 1.2, two_circles),
        ("figure8", 80, 1.0, figure8),
        ("figure8", 200, 1.0, figure8),
    ]
    # scale rows for triangle-count slopes (same families, more n)
    scale = [
        ("circle_noisy", 500, 1.5, circle_noisy),
        ("blobs", 500, 1.0, blobs),
        ("torus", 500, 1.6, torus),
        ("uniform2", 500, 0.35, lambda n, r: uniform(n, 2, r)),
    ]

    def run_one(name, n, T, fn, timeout=120, rto=60):
        if name == "unit_square":
            path = unit_square_path()
        elif name == "uniform2":
            path = ensure_cloud(name, n, lambda m, r: uniform(m, 2, r), rng)
        else:
            path = ensure_cloud(name, n, fn, rng)
        pr, tr = ripser(path, T, rto)
        ps, cs, ts = pith_reduced(path, T, timeout)
        pd, cd, td = None, None, None
        try:
            pd, cd, td = pith_default(path, T, timeout)
        except Exception as ex:  # noqa: BLE001
            print(f"default failed {name} n={n}: {ex}", flush=True)
        fid = compare(pr, ps, 1)
        bn = bottleneck_h1(pr, ps)
        rec = {
            "name": name, "n": n, "T": T,
            "match_ripser": fid.get("exact_match_tol"),
            "unmatched": fid.get("unmatched"),
            "ess1_red": ess1(ps),
            "ess1_ripser": ess1(pr),
            "n_finite_red": fid.get("n_finite_b"),
            "n_finite_ripser": fid.get("n_finite_a"),
            "bottleneck": bn,
            "triangles": cs.get("simplices"),
            "edges": cs.get("edges_out") or cs.get("edges_in"),
            "build_ms": cs.get("collapse_ms"),
            "reduce_ms": cs.get("reduce_ms"),
            "red_s": ts,
            "ripser_s": tr,
            "vs_ripser": (tr / ts) if ts else None,
            "default_s": td,
            "default_edges": (cd or {}).get("edges_out"),
        }
        print(f"I224 {rec}", flush=True)
        recs.append(rec)
        return rec

    for name, n, T, fn in jobs:
        run_one(name, n, T, fn, timeout=90, rto=45)
    for name, n, T, fn in scale:
        run_one(name, n, T, fn, timeout=180, rto=90)

    ident = [r for r in recs if r["n"] <= 200]
    all_match = all(r.get("match_ripser") for r in ident)
    ess_ok = all(r.get("ess1_red") == r.get("ess1_ripser") for r in ident)
    mixed = [r for r in ident if r["name"] in {"figure8", "two_circles", "unit_square", "blobs", "torus"}]
    mixed_ok = all(r.get("match_ripser") for r in mixed) if mixed else False

    slopes = {}
    for fam in ("circle_noisy", "blobs", "torus", "uniform2"):
        rows = [r for r in recs if r["name"] == fam and r.get("triangles")]
        if len(rows) >= 2:
            slopes[fam] = {
                "triangles": loglog_slope([r["n"] for r in rows], [r["triangles"] for r in rows]),
                "time": loglog_slope([r["n"] for r in rows], [r["red_s"] for r in rows]),
                "ripser_time": loglog_slope([r["n"] for r in rows], [r["ripser_s"] for r in rows]),
            }

    # Select only if identity holds on mixed homology AND triangles are a
    # smaller size class than flag Θ(n³) — paper claims O(n²) under doubling.
    tri_slopes = [v["triangles"] for v in slopes.values() if v["triangles"] is not None]
    size_win = bool(tri_slopes) and max(tri_slopes) <= 2.3
    clock_win = any((r.get("vs_ripser") or 0) >= 3 and r["n"] >= 200 for r in recs)

    if all_match and ess_ok and mixed_ok:
        status = "support"
        summary = (
            f"reduced VR exact vs Ripser on {len(ident)} mixed-shape rows; "
            f"triangle slopes { {k: round(v['triangles'], 2) if v['triangles'] else None for k, v in slopes.items()} }"
        )
        if not size_win:
            status = "hold"
            summary += " — identity ok but size class not yet sub-cubic / ≤n^{2.3}"
    elif ess_ok and not all_match:
        status = "reject"
        summary = "essential H1 matches; finite bars still differ (I056 class)"
    else:
        status = "reject"
        summary = "reduced VR H1 identity failed on mixed shapes"

    write(
        {
            "id": "reduced_vr_engine",
            "lever": "H07",
            "class": "structural",
            "fidelity": "exact-claimed",
            "status": status,
            "summary": summary,
            "all_match": all_match,
            "ess_ok": ess_ok,
            "mixed_ok": mixed_ok,
            "size_win": size_win,
            "clock_win": clock_win,
            "slopes": slopes,
            "receipts": recs,
        },
        "I224",
    )
    print(f"I224 status={status} {summary}", flush=True)


if __name__ == "__main__":
    main()
