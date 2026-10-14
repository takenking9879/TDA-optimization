#!/usr/bin/env python3
"""Persistence-diagram SVGs: Ripser, exact, scale, sparse, GUDHI Alpha.

Makes the accuracy tradeoff visible. Not exact VR for scale / sparse / Alpha.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

BENCH = Path(__file__).resolve().parent
sys.path.insert(0, str(BENCH))
from generate_datasets import circle_noisy, figure8, nested_loops, sphere, write_csv  # noqa: E402
from ph_metrics import ess  # noqa: E402
from run_consolidation import run_gudhi_alpha, run_pith, run_ripser  # noqa: E402

FIG = BENCH / "results" / "consolidation" / "figures"
OUT = BENCH / "results" / "consolidation"


def finite_or_ess(pairs, dim):
    pts = []
    for p in pairs or []:
        if p["dim"] != dim:
            continue
        b, d = p["birth"], p["death"]
        if math.isfinite(d) and d - b <= 1e-6:
            continue
        pts.append((b, d if math.isfinite(d) else math.inf))
    return pts


def svg_pd(path, title, series, dim=1, w=520, h=520):
    pad = 48
    pts = [xy for s in series for xy in s["xy"]]
    if not pts:
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        return
    finite = [d for _, d in pts if math.isfinite(d)]
    births = [b for b, _ in pts]
    xmax = max(births + finite + [1e-6])
    ymax = max(finite + [xmax])
    # essential bars sit just below the top
    inf_y = ymax * 1.08 if ymax > 0 else 1.0
    xmax = max(xmax, inf_y)

    def X(v):
        return pad + (v / xmax) * (w - 2 * pad)

    def Y(v):
        return h - pad - (v / xmax) * (h - 2 * pad)

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#7f7f7f"]
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' font-family='sans-serif'>",
        f"<rect width='{w}' height='{h}' fill='white'/>",
        f"<text x='{w/2}' y='20' text-anchor='middle' font-size='13'>{title}</text>",
        f"<line x1='{X(0):.1f}' y1='{Y(0):.1f}' x2='{X(xmax):.1f}' y2='{Y(xmax):.1f}' stroke='#bbb'/>",
        f"<line x1='{X(0):.1f}' y1='{Y(0):.1f}' x2='{X(xmax):.1f}' y2='{Y(0):.1f}' stroke='#444'/>",
        f"<line x1='{X(0):.1f}' y1='{Y(0):.1f}' x2='{X(0):.1f}' y2='{Y(xmax):.1f}' stroke='#444'/>",
        f"<text x='{w/2}' y='{h-12}' text-anchor='middle' font-size='11'>birth</text>",
        f"<text x='14' y='{h/2}' text-anchor='middle' font-size='11' transform='rotate(-90 14 {h/2})'>death</text>",
    ]
    for i, s in enumerate(series):
        col = colors[i % len(colors)]
        for b, d in s["xy"]:
            yy = inf_y if not math.isfinite(d) else d
            filled = not math.isfinite(d)
            if filled:
                out.append(f"<circle cx='{X(b):.1f}' cy='{Y(yy):.1f}' r='4.5' fill='{col}'/>")
            else:
                out.append(
                    f"<circle cx='{X(b):.1f}' cy='{Y(yy):.1f}' r='3' fill='none' "
                    f"stroke='{col}' stroke-width='1.3'/>"
                )
        out.append(
            f"<text x='{w-10}' y='{36+16*i}' text-anchor='end' font-size='11' fill='{col}'>{s['name']}</text>"
        )
    out.append("</svg>")
    path.write_text("\n".join(out))


def main():
    rng = np.random.default_rng(0)
    FIG.mkdir(parents=True, exist_ok=True)
    recs = []
    families = (
        ("figure8", figure8, 1.1, 1, 400),
        ("circle_noisy", circle_noisy, 1.5, 1, 400),
        ("nested_loops", nested_loops, 1.6, 1, 400),
        ("sphere", sphere, 1.4, 2, 400),
    )
    for name, fn, T, dim, n in families:
        path = BENCH / "datasets" / "generated" / f"{name}_n{n}.csv"
        if not path.exists():
            write_csv(path, fn(n, rng))
        rip = run_ripser(path, T, dim, timeout=20)
        exact = run_pith(path, T, dim, "exact", "auto", timeout=20)
        scale = run_pith(path, T, dim, "scale", "auto", timeout=20)
        sparse = run_pith(path, T, dim, "sparse", "auto", timeout=20)
        alpha = run_gudhi_alpha(path, dim, timeout=20)
        plot_dim = 2 if name == "sphere" else 1
        series = []
        metrics = {"name": name, "n": n, "T": T, "plot_dim": plot_dim}
        for lab, run in (
            ("Ripser VR", rip),
            ("PITH exact", exact),
            ("PITH scale", scale),
            ("PITH sparse", sparse),
            ("GUDHI Alpha", alpha),
        ):
            pairs = run.get("pairs") or []
            series.append({"name": lab, "xy": finite_or_ess(pairs, plot_dim)})
            metrics[lab] = {
                "ok": run.get("ok"),
                "ess": {d: ess(pairs, d) for d in range(dim + 1)},
                "n_finite": sum(
                    1
                    for p in pairs
                    if p["dim"] == plot_dim and math.isfinite(p["death"]) and p["death"] - p["birth"] > 1e-6
                ),
            }
        svg_pd(
            FIG / f"pd_{name}.svg",
            f"{name} n={n} H{plot_dim}  (filled = essential)",
            series,
            dim=plot_dim,
        )
        recs.append(metrics)
        print(
            f"{name} H{plot_dim} ess "
            f"rip={metrics['Ripser VR']['ess']} exact={metrics['PITH exact']['ess']} "
            f"scale={metrics['PITH scale']['ess']} sparse={metrics['PITH sparse']['ess']} "
            f"alpha={metrics['GUDHI Alpha']['ess']}",
            flush=True,
        )
    (OUT / "pd_metrics.json").write_text(json.dumps(recs, indent=2))
    print("wrote PD figures and pd_metrics.json")


if __name__ == "__main__":
    main()
