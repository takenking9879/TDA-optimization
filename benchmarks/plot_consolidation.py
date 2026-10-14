#!/usr/bin/env python3
"""SVG figures + markdown tables from consolidation/report.json."""

from __future__ import annotations

import json
import math
from pathlib import Path

BENCH = Path(__file__).resolve().parent
REP = json.loads((BENCH / "results" / "consolidation" / "report.json").read_text())
FIG = BENCH / "results" / "consolidation" / "figures"
FIG.mkdir(parents=True, exist_ok=True)


def svg_scatter(path, series, title, xlab, ylab, logx=True, logy=True, w=720, h=420):
    pad_l, pad_r, pad_t, pad_b = 64, 24, 36, 48
    pts = [(x, y) for s in series for x, y in s["xy"] if x and y and x > 0 and y > 0]
    if not pts:
        path.write_text("<svg xmlns='http://www.w3.org/2000/svg'/>")
        return
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    if logx:
        xs = [math.log10(x) for x in xs]
    if logy:
        ys = [math.log10(y) for y in ys]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    if xmax <= xmin:
        xmax = xmin + 1
    if ymax <= ymin:
        ymax = ymin + 1
    def X(v):
        return pad_l + (v - xmin) / (xmax - xmin) * (w - pad_l - pad_r)
    def Y(v):
        return pad_t + (1 - (v - ymin) / (ymax - ymin)) * (h - pad_t - pad_b)
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e"]
    out = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' font-family='sans-serif'>",
        f"<rect width='{w}' height='{h}' fill='white'/>",
        f"<text x='{w/2}' y='22' text-anchor='middle' font-size='14'>{title}</text>",
        f"<text x='{w/2}' y='{h-10}' text-anchor='middle' font-size='11'>{xlab}</text>",
        f"<text x='14' y='{h/2}' text-anchor='middle' font-size='11' transform='rotate(-90 14 {h/2})'>{ylab}</text>",
    ]
    for i, s in enumerate(series):
        col = colors[i % len(colors)]
        coords = []
        for x, y in s["xy"]:
            if not x or not y or x <= 0 or y <= 0:
                continue
            xx = math.log10(x) if logx else x
            yy = math.log10(y) if logy else y
            coords.append((X(xx), Y(yy)))
        if len(coords) >= 2:
            d = "M " + " L ".join(f"{a:.1f} {b:.1f}" for a, b in coords)
            out.append(f"<path d='{d}' fill='none' stroke='{col}' stroke-width='1.6'/>")
        for a, b in coords:
            out.append(f"<circle cx='{a:.1f}' cy='{b:.1f}' r='3.2' fill='{col}'/>")
        out.append(
            f"<text x='{w-pad_r-8}' y='{40+16*i}' text-anchor='end' font-size='11' fill='{col}'>{s['name']}</text>"
        )
    out.append("</svg>")
    path.write_text("\n".join(out))


def collect(name, method_key):
    xy = []
    for r in REP["receipts"]:
        if r["name"] != name:
            continue
        run = r["runs"].get(method_key)
        if run and run.get("ok") and run.get("wall_s"):
            xy.append((r["n"], run["wall_s"]))
    return sorted(xy)


svg_scatter(
    FIG / "runtime_exact.svg",
    [
        {"name": "circle PITH exact", "xy": collect("circle_noisy", "pith_exact")},
        {"name": "circle Ripser", "xy": collect("circle_noisy", "ripser")},
        {"name": "figure8 PITH exact", "xy": collect("figure8", "pith_exact")},
        {"name": "figure8 Ripser", "xy": collect("figure8", "ripser")},
        {"name": "uniform2 PITH exact", "xy": collect("uniform2", "pith_exact")},
    ],
    "Runtime vs n (exact VR, log-log)",
    "n",
    "wall seconds",
)

svg_scatter(
    FIG / "runtime_scale.svg",
    [
        {"name": "figure8 scale", "xy": collect("figure8", "pith_scale")},
        {"name": "sphere scale", "xy": collect("sphere", "pith_scale")},
        {"name": "figure8 exact (small n)", "xy": collect("figure8", "pith_exact")},
        {"name": "figure8 Ripser (small n)", "xy": collect("figure8", "ripser")},
    ],
    "Runtime vs n (scale path vs exact, log-log)",
    "n",
    "wall seconds",
)

# exponent bars as a simple table-like svg
exp = REP.get("exponents") or []
lines = [
    "<svg xmlns='http://www.w3.org/2000/svg' width='760' height='420' font-family='sans-serif'>",
    "<rect width='760' height='420' fill='white'/>",
    "<text x='380' y='22' text-anchor='middle' font-size='14'>Local time exponent p = log(t1/t0)/log(n1/n0)</text>",
]
y = 48
for e in exp:
    if e.get("p_time") is None:
        continue
    p = e["p_time"]
    bar = max(4, min(400, abs(p) * 80))
    col = "#d62728" if p > 2.5 else ("#ff7f0e" if p > 1.8 else "#2ca02c")
    label = f"{e['name']} {e['method']} {e['n0']}→{e['n1']}  p={p:.2f}"
    lines.append(f"<text x='12' y='{y}' font-size='11'>{label}</text>")
    lines.append(f"<rect x='340' y='{y-10}' width='{bar:.1f}' height='10' fill='{col}'/>")
    y += 16
    if y > 400:
        break
lines.append("</svg>")
(FIG / "exponents.svg").write_text("\n".join(lines))

# tables
rows = []
rows.append("# Consolidation tables (this hardware: 4 CPU, 16 GB)")
rows.append("")
rows.append("Ripser is 1 thread. PITH may use up to 4 threads for a few scans.")
rows.append("giotto-ph was not installed. GUDHI Rips ran only at n=200 (circle 0.085 s).")
rows.append("")
rows.append("## Exact VR wall time")
rows.append("| family | n | T | dim | PITH exact (s) | Ripser (s) | ratio | pipeline |")
rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
for r in REP["receipts"]:
    a = r["runs"].get("pith_exact")
    b = r["runs"].get("ripser")
    if not (a and b and a.get("wall_s") and b.get("wall_s")):
        continue
    rows.append(
        f"| {r['name']} | {r['n']} | {r['T']} | {r['maxdim']} | {a['wall_s']:.3f} | {b['wall_s']:.3f} | {b['wall_s']/a['wall_s']:.2f}× | {a.get('pipeline','')} |"
    )
rows.append("")
rows.append("## Scale path")
rows.append("| family | n | PITH scale (s) | |E| | ess H1 | ess H2 |")
rows.append("| --- | ---: | ---: | ---: | ---: | ---: |")
for r in REP["receipts"]:
    s = r["runs"].get("pith_scale")
    if not (s and s.get("ok") and s.get("wall_s")):
        continue
    rows.append(
        f"| {r['name']} | {r['n']} | {s['wall_s']:.3f} | {s.get('n_dist')} | {s.get('ess1')} | {s.get('ess2')} |"
    )
rows.append("")
rows.append("## Topology at n=400 vs Ripser")
rows.append("| family | exact match | exact unmatched | scale unmatched | ess exact | ess Ripser | ess scale |")
rows.append("| --- | --- | ---: | ---: | --- | --- | --- |")
for t in REP["topology"]:
    rows.append(
        f"| {t['name']} | {t.get('exact_match')} | {t.get('exact_unmatched')} | {t.get('scale_unmatched')} | "
        f"H1={t.get('ess1_exact')} H2={t.get('ess2_exact')} | H1={t.get('ess1_ripser')} H2={t.get('ess2_ripser')} | "
        f"H1={t.get('ess1_scale')} H2={t.get('ess2_scale')} |"
    )
rows.append("")
rows.append("## Dispatcher (same 250-pt probe as `--engine auto`)")
rows.append("| family | recommended | picked | agree | exact feasible | wall (s) |")
rows.append("| --- | --- | --- | --- | --- | ---: |")
for d in REP["dispatcher"]:
    rows.append(
        f"| {d['name']} | {d.get('recommended')} | {d.get('picked')} | {d.get('match')} | {d.get('exact_feasible')} | {d.get('wall_s'):.3f} |"
    )
rows.append("")
rows.append("## Local time exponents (empirical slopes, not theorems)")
rows.append("| family | method | n0 | n1 | p_time | p_edges |")
rows.append("| --- | --- | ---: | ---: | ---: | ---: |")
for e in exp:
    pt = f"{e['p_time']:.2f}" if e.get("p_time") is not None else ""
    pe = f"{e['p_edges']:.2f}" if e.get("p_edges") is not None else ""
    rows.append(f"| {e['name']} | {e['method']} | {e['n0']} | {e['n1']} | {pt} | {pe} |")

(BENCH / "results" / "consolidation" / "TABLES.md").write_text("\n".join(rows) + "\n")
print("wrote figures and TABLES.md")
