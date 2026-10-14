#!/usr/bin/env python3
"""Fit empirical t ≈ C n^p models from consolidation receipts.

These are pre-asymptotic slopes on named families, not theorems.
Writes docs/GROWTH.md and a JSON sidecar.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

BENCH = Path(__file__).resolve().parent
ROOT = BENCH.parent
REP = json.loads((BENCH / "results" / "consolidation" / "report.json").read_text())
LIM_PATH = BENCH / "results" / "consolidation" / "limits.json"
LIM = json.loads(LIM_PATH.read_text()) if LIM_PATH.exists() else {}


def fit_power(xs, ys):
    pts = [(math.log(x), math.log(y)) for x, y in zip(xs, ys) if x and y and x > 0 and y > 0]
    if len(pts) < 2:
        return None
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    den = sum((p[0] - mx) ** 2 for p in pts)
    if den <= 0:
        return None
    p = sum((p0 - mx) * (p1 - my) for p0, p1 in pts) / den
    logc = my - p * mx
    c = math.exp(logc)
    pred = [c * (x**p) for x in xs]
    ss_res = sum((y - yh) ** 2 for y, yh in zip(ys, pred))
    ss_tot = sum((y - (sum(ys) / len(ys))) ** 2 for y in ys)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else None
    return {"C": c, "p": p, "r2": r2, "n_pts": n}


def collect():
    series = {}
    for r in REP.get("receipts") or []:
        for meth, run in (r.get("runs") or {}).items():
            if run and run.get("ok") and run.get("wall_s"):
                series.setdefault((r["name"], meth), []).append((r["n"], run["wall_s"]))
    alias = {"exact_auto": "pith_exact", "scale": "pith_scale", "ripser": "ripser"}
    for r in LIM.get("limits") or []:
        for raw, run in (r.get("runs") or {}).items():
            meth = alias.get(raw, raw)
            if run and run.get("ok") and run.get("wall_s"):
                series.setdefault((r["name"], meth), []).append((r["n"], run["wall_s"]))
    out = {}
    for key, pts in series.items():
        by = {}
        for n, t in pts:
            by[n] = t
        pts = sorted(by.items())
        if len(pts) < 2:
            continue
        fit = fit_power([p[0] for p in pts], [p[1] for p in pts])
        if not fit:
            continue
        locals_ = []
        for i in range(len(pts) - 1):
            n0, t0 = pts[i]
            n1, t1 = pts[i + 1]
            if t0 and t1 and n1 > n0:
                locals_.append(
                    {
                        "n0": n0,
                        "n1": n1,
                        "p": math.log(t1 / t0) / math.log(n1 / n0),
                    }
                )
        out[f"{key[0]}:{key[1]}"] = {
            "family": key[0],
            "method": key[1],
            "points": pts,
            "fit": fit,
            "local": locals_,
        }
    return out


def classify(p):
    if p is None:
        return "unknown"
    if p < 1.4:
        return "near-linear / low-polynomial"
    if p < 2.2:
        return "quadratic-ish polynomial"
    if p < 3.5:
        return "high polynomial (combinatorial leftover / tet tax)"
    return "faster than n^3.5 on this window (do not call exponential without more decades)"


def main():
    series = collect()
    lines = [
        "# Empirical growth models",
        "",
        r"Fits of \(t \approx C n^{p}\) on the consolidation receipts.",
        "These are **pre-asymptotic slopes**, not theorems.",
        r"Local exponents \(p_i = \log(t_{i+1}/t_i)/\log(n_{i+1}/n_i)\) detect regime changes.",
        "",
        "Hardware: 4 CPU / 16 GB. Phase-2 exact times are 1-thread unless noted.",
        "",
        "| series | n range | C | p | R² | local p | regime |",
        "| --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    rows = []
    for key in sorted(series):
        s = series[key]
        fit = s["fit"]
        ns = [p[0] for p in s["points"]]
        loc = ", ".join(f"{e['n0']}→{e['n1']}:{e['p']:.2f}" for e in s["local"])
        rows.append(
            f"| {s['family']} {s['method']} | {min(ns)}–{max(ns)} | {fit['C']:.3g} | {fit['p']:.2f} | "
            f"{'' if fit['r2'] is None else f'{fit['r2']:.2f}'} | {loc} | {classify(fit['p'])} |"
        )
    lines.extend(rows)
    lines += [
        "",
        "## How to read p",
        "",
        r"- \(p \approx 1\)–\(1.3\): scale path / Delaunay \(H_0\) on this window.",
        r"- \(p \approx 2\): listing a dense \(G_T\) or RedZeD on a connected graph.",
        r"- \(p \approx 2.8\)–\(3.5\): leftover visits or Ripser tet tax. Exact VR is leaving the cheap regime.",
        "- Do **not** call a 2-point slope “exponential.”",
        "",
        "The feasibility probe uses these regimes: fat `maxdim≥2` or conservative `|E|>8e6`",
        "means exact VR is marked impractical.",
        "",
    ]
    path = ROOT / "docs" / "GROWTH.md"
    path.write_text("\n".join(lines))
    (BENCH / "results" / "consolidation" / "growth.json").write_text(json.dumps(series, indent=2))
    print(f"wrote {path} ({len(series)} series)")


if __name__ == "__main__":
    main()
