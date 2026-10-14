#!/usr/bin/env python3
"""SVG figures + markdown tables from consolidation/report.json and limits.json."""

from __future__ import annotations

import json
import math
from pathlib import Path

BENCH = Path(__file__).resolve().parent
REP = json.loads((BENCH / "results" / "consolidation" / "report.json").read_text())
LIM_PATH = BENCH / "results" / "consolidation" / "limits.json"
LIM = json.loads(LIM_PATH.read_text()) if LIM_PATH.exists() else {}
BASE_PATH = BENCH / "results" / "consolidation" / "baselines.json"
BASE = json.loads(BASE_PATH.read_text()) if BASE_PATH.exists() else {}
SPARSE_PATH = BENCH / "results" / "consolidation" / "sparse_limits.json"
SPARSE = json.loads(SPARSE_PATH.read_text()) if SPARSE_PATH.exists() else {}
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

    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#ff7f0e", "#8c564b"]
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


def collect(name, method_key, rss=False):
    xy = []
    for r in REP.get("receipts") or []:
        if r["name"] != name:
            continue
        run = r["runs"].get(method_key)
        if not (run and run.get("ok") and run.get("wall_s")):
            continue
        y = run.get("rss_pith") if rss else run.get("wall_s")
        if y:
            xy.append((r["n"], y))
    alias = {
        "pith_exact": "exact_auto",
        "pith_scale": "scale",
        "ripser": "ripser",
        "pith_redzed": "exact_redzed",
    }
    lim_key = alias.get(method_key, method_key)
    for r in LIM.get("limits") or []:
        if r["name"] != name:
            continue
        run = r["runs"].get(lim_key) or r["runs"].get(method_key)
        if not (run and run.get("ok") and run.get("wall_s")):
            continue
        y = run.get("rss_pith") if rss else run.get("wall_s")
        if y:
            xy.append((r["n"], y))
    # unique by n, keep last
    by = {}
    for x, y in xy:
        by[x] = y
    return sorted(by.items())


svg_scatter(
    FIG / "runtime_exact.svg",
    [
        {"name": "circle PITH exact", "xy": collect("circle_noisy", "pith_exact")},
        {"name": "circle Ripser", "xy": collect("circle_noisy", "ripser")},
        {"name": "figure8 PITH exact", "xy": collect("figure8", "pith_exact")},
        {"name": "figure8 Ripser", "xy": collect("figure8", "ripser")},
        {"name": "uniform2 PITH exact", "xy": collect("uniform2", "pith_exact")},
        {"name": "torus PITH exact", "xy": collect("torus", "pith_exact")},
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
        {"name": "many_loops scale", "xy": collect("many_loops", "pith_scale")},
    ],
    "Runtime vs n (scale path vs exact, log-log)",
    "n",
    "wall seconds",
)

svg_scatter(
    FIG / "memory_exact.svg",
    [
        {"name": "circle PITH", "xy": collect("circle_noisy", "pith_exact", rss=True)},
        {"name": "figure8 PITH", "xy": collect("figure8", "pith_exact", rss=True)},
        {"name": "figure8 scale", "xy": collect("figure8", "pith_scale", rss=True)},
        {"name": "sphere scale", "xy": collect("sphere", "pith_scale", rss=True)},
        {"name": "blobs H0 PITH", "xy": collect("blobs", "pith_exact", rss=True)},
    ],
    "Peak RSS vs n (PITH VmHWM, log-log)",
    "n",
    "bytes",
)

exp = list(REP.get("exponents") or []) + list(LIM.get("exponents") or [])
lines = [
    "<svg xmlns='http://www.w3.org/2000/svg' width='760' height='520' font-family='sans-serif'>",
    "<rect width='760' height='520' fill='white'/>",
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
    lines.append(f"<rect x='360' y='{y-10}' width='{bar:.1f}' height='10' fill='{col}'/>")
    y += 16
    if y > 500:
        break
lines.append("</svg>")
(FIG / "exponents.svg").write_text("\n".join(lines))

# max practical N bars
mp = LIM.get("max_practical") or []
# collapse to method x family max
want = ["pith_exact", "pith_redzed", "ripser", "pith_scale"]
families = []
for row in mp:
    if row.get("method") in want and row.get("max_n_ok"):
        families.append(row)
h = max(220, 36 + 16 * min(len(families), 24))
out = [
    f"<svg xmlns='http://www.w3.org/2000/svg' width='760' height='{h}' font-family='sans-serif'>",
    f"<rect width='760' height='{h}' fill='white'/>",
    "<text x='380' y='22' text-anchor='middle' font-size='14'>Largest n finished under the 12s budget (this hardware)</text>",
]
ymax_n = max((r["max_n_ok"] for r in families), default=1)
y = 44
colors = {"pith_exact": "#1f77b4", "pith_redzed": "#9467bd", "ripser": "#d62728", "pith_scale": "#2ca02c"}
for r in families[:24]:
    n = r["max_n_ok"]
    bar = 20 + 480 * (math.log10(n) / math.log10(max(ymax_n, 10)))
    col = colors.get(r["method"], "#333")
    label = f"{r['name']} {r['method']} dim{r.get('maxdim')}  n≤{n}"
    out.append(f"<text x='12' y='{y}' font-size='11'>{label}</text>")
    out.append(f"<rect x='360' y='{y-10}' width='{bar:.1f}' height='10' fill='{col}'/>")
    y += 16
out.append("</svg>")
(FIG / "max_practical.svg").write_text("\n".join(out))

# dispatcher regime map: residual_frac vs edge_frac
disp = LIM.get("dispatcher_oracle") or REP.get("dispatcher") or []
# pull probe coords from engines rows
eng = { (r["name"], r["n"]): r for r in (LIM.get("engines") or []) }
w, h = 640, 420
pad_l, pad_r, pad_t, pad_b = 56, 20, 36, 48
out = [
    f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' font-family='sans-serif'>",
    f"<rect width='{w}' height='{h}' fill='white'/>",
    "<text x='320' y='22' text-anchor='middle' font-size='14'>Dispatcher regime (edge-frac vs residual-frac)</text>",
    "<text x='320' y='408' text-anchor='middle' font-size='11'>edge_frac probe</text>",
    "<text x='14' y='210' text-anchor='middle' font-size='11' transform='rotate(-90 14 210)'>residual_frac probe</text>",
]
pts = []
for d in disp:
    row = eng.get((d.get("name"), d.get("n")))
    est = (row or {}).get("estimate") or {}
    x, yv = est.get("edge_frac_probe"), est.get("residual_frac_probe")
    if x is None or yv is None or x < 0 or yv < 0:
        continue
    pts.append((x, yv, d))
if pts:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    xmin, xmax = min(0, min(xs)), max(1, max(xs))
    ymin, ymax = min(0, min(ys)), max(0.2, max(ys))

    def X(v):
        return pad_l + (v - xmin) / (xmax - xmin) * (w - pad_l - pad_r)

    def Y(v):
        return pad_t + (1 - (v - ymin) / (ymax - ymin)) * (h - pad_t - pad_b)

    for x, yv, d in pts:
        col = "#d62728" if d.get("wrong") else ("#9467bd" if d.get("recommended") == "redzed" else "#1f77b4")
        mark = "X" if d.get("wrong") else "o"
        if mark == "X":
            out.append(
                f"<text x='{X(x):.1f}' y='{Y(yv):.1f}' text-anchor='middle' font-size='14' fill='{col}'>x</text>"
            )
        else:
            out.append(f"<circle cx='{X(x):.1f}' cy='{Y(yv):.1f}' r='5' fill='{col}'/>")
        out.append(
            f"<text x='{X(x)+8:.1f}' y='{Y(yv)-8:.1f}' font-size='10' fill='#333'>{d.get('name')}</text>"
        )
    out.append("<text x='520' y='50' font-size='11' fill='#9467bd'>redzed (correct)</text>")
    out.append("<text x='520' y='66' font-size='11' fill='#1f77b4'>implicit (correct)</text>")
    out.append("<text x='520' y='82' font-size='11' fill='#d62728'>x = wrong vs 1-thread oracle</text>")
out.append("</svg>")
(FIG / "dispatcher.svg").write_text("\n".join(out))

# tables
rows = []
rows.append("# Consolidation tables (this hardware: 4 CPU, 16 GB)")
rows.append("")
rows.append("Ripser is 1 thread. Phase-2 PITH times use `--threads 1` unless noted.")
if BASE.get("have_giotto"):
    rows.append(
        f"giotto-ph {BASE.get('giotto')} (AGPL oracle) and GUDHI {BASE.get('gudhi')} "
        "are compared at equal hardware in the phase-3 tables below."
    )
else:
    rows.append("giotto-ph was not installed. GUDHI Rips/Alpha used where n is small enough.")
rows.append("")
rows.append("## Exact VR wall time (phase 1, PITH may use 4 threads)")
rows.append("| family | n | T | dim | PITH exact (s) | Ripser (s) | ratio | pipeline |")
rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
for r in REP.get("receipts") or []:
    a = r["runs"].get("pith_exact")
    b = r["runs"].get("ripser")
    if not (a and b and a.get("wall_s") and b.get("wall_s")):
        continue
    rows.append(
        f"| {r['name']} | {r['n']} | {r['T']} | {r['maxdim']} | {a['wall_s']:.3f} | {b['wall_s']:.3f} | {b['wall_s']/a['wall_s']:.2f}× | {a.get('pipeline','')} |"
    )

rows.append("")
rows.append("## Thread-fair exact VR (`--threads 1` vs hardware vs Ripser)")
rows.append("| family | n | PITH 1-thr (s) | PITH hw-thr (s) | Ripser 1-thr (s) | 1-thr ratio | hw-thr ratio |")
rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
for r in LIM.get("threads") or []:
    a = r["runs"].get("pith_t1") or {}
    h = r["runs"].get("pith_thw") or {}
    b = r["runs"].get("ripser") or {}
    if not (a.get("wall_s") and b.get("wall_s")):
        continue
    hw = f"{h['wall_s']:.3f}" if h.get("wall_s") else ""
    hw_r = f"{b['wall_s']/h['wall_s']:.2f}×" if h.get("wall_s") else ""
    rows.append(
        f"| {r['name']} | {r['n']} | {a['wall_s']:.3f} | {hw} | {b['wall_s']:.3f} | {b['wall_s']/a['wall_s']:.2f}× | {hw_r} |"
    )

rows.append("")
rows.append("## Forced engines (1 thread)")
rows.append("| family | n | auto (s) | redzed (s) | implicit (s) | estimate | oracle | waste |")
rows.append("| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |")
oracle = { (d["name"], d["n"]): d for d in LIM.get("dispatcher_oracle") or [] }
for r in LIM.get("engines") or []:
    a, z, i = r["runs"].get("auto") or {}, r["runs"].get("redzed") or {}, r["runs"].get("implicit") or {}
    d = oracle.get((r["name"], r["n"])) or {}
    rows.append(
        f"| {r['name']} | {r['n']} | {a.get('wall_s') or ''} | {z.get('wall_s') or ''} | {i.get('wall_s') or ''} | "
        f"{(r.get('estimate') or {}).get('engine_recommended')} | {d.get('oracle_faster')} | {d.get('waste_if_follow_estimate') or ''} |"
    )

rows.append("")
rows.append("## Scale path")
rows.append("| family | n | PITH scale (s) | |E| | ess H1 | ess H2 | RSS |")
rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: |")
seen = set()
for src, key in ((REP.get("receipts") or [], "pith_scale"), (LIM.get("limits") or [], "scale")):
    for r in src:
        s = r["runs"].get(key)
        if not (s and s.get("ok") and s.get("wall_s")):
            continue
        tok = (r["name"], r["n"], r.get("T"))
        if tok in seen:
            continue
        seen.add(tok)
        rows.append(
            f"| {r['name']} | {r['n']} | {s['wall_s']:.3f} | {s.get('n_dist')} | {s.get('ess1')} | {s.get('ess2')} | {s.get('rss_pith')} |"
        )

rows.append("")
rows.append("## Topology vs Ripser (phase 2, bottleneck/Wasserstein when GUDHI provides them)")
rows.append("| family | n | exact match | scale unmatched | scale bn H1 | scale W1 H1 | ess scale | ess sparse |")
rows.append("| --- | ---: | --- | ---: | ---: | ---: | --- | --- |")
for t in LIM.get("topology") or REP.get("topology") or []:
    ex = t.get("exact_vs_ripser") or {}
    sc = t.get("scale_vs_ripser") or {}
    bn = sc.get("bottleneck_h1")
    w1 = sc.get("wasserstein1_h1")
    ess_s = t.get("ess_scale") or {}
    ess_p = t.get("ess_sparse") or {}
    rows.append(
        f"| {t['name']} | {t.get('n')} | {ex.get('exact_match')} | {sc.get('unmatched')} | "
        f"{'' if bn is None else (f'{bn:.4g}' if isinstance(bn, float) else bn)} | "
        f"{'' if w1 is None else (f'{w1:.4g}' if isinstance(w1, float) else w1)} | "
        f"H1={ess_s.get(1, ess_s.get('1'))} H2={ess_s.get(2, ess_s.get('2'))} | "
        f"H1={ess_p.get(1, ess_p.get('1'))} H2={ess_p.get(2, ess_p.get('2'))} |"
    )

rows.append("")
rows.append("## Dispatcher oracle (1-thread; wrong = estimate ≠ faster engine)")
rows.append("| family | n | recommended | auto | oracle | wrong | waste | regime |")
rows.append("| --- | ---: | --- | --- | --- | --- | ---: | --- |")
for d in LIM.get("dispatcher_oracle") or []:
    rows.append(
        f"| {d['name']} | {d['n']} | {d.get('recommended')} | {d.get('auto_picked')} | {d.get('oracle_faster')} | "
        f"{d.get('wrong')} | {d.get('waste_if_follow_estimate') or ''} | {d.get('regime')} |"
    )

rows.append("")
rows.append("## Practical limits under a 12 s budget")
rows.append("| family | dim | method | max n ok | wall (s) | first fail n |")
rows.append("| --- | ---: | --- | ---: | ---: | ---: |")
for r in LIM.get("max_practical") or []:
    rows.append(
        f"| {r['name']} | {r.get('maxdim')} | {r['method']} | {r.get('max_n_ok')} | "
        f"{'' if r.get('wall_at_max') is None else f'{r['wall_at_max']:.3f}'} | {r.get('first_fail_n')} |"
    )

rows.append("")
rows.append("## Non-Euclidean L1 (exact engine only)")
rows.append("| n | PITH auto (s) | PITH redzed (s) | Ripser (s) | exact match |")
rows.append("| ---: | ---: | ---: | ---: | --- |")
for r in LIM.get("noneuclidean") or []:
    a, z, b = r.get("pith_auto") or {}, r.get("pith_redzed") or {}, r.get("ripser") or {}
    fid = r.get("exact_vs_ripser") or {}
    rows.append(
        f"| {r['n']} | {a.get('wall_s') or ''} | {z.get('wall_s') or ''} | {b.get('wall_s') or ''} | {fid.get('exact_match')} |"
    )

rows.append("")
rows.append("## Local time exponents (empirical slopes, not theorems)")
rows.append("| family | method | n0 | n1 | p_time | p_edges |")
rows.append("| --- | --- | ---: | ---: | ---: | ---: |")
for e in exp:
    pt = f"{e['p_time']:.2f}" if e.get("p_time") is not None else ""
    pe = f"{e['p_edges']:.2f}" if e.get("p_edges") is not None else ""
    rows.append(f"| {e['name']} | {e['method']} | {e['n0']} | {e['n1']} | {pt} | {pe} |")

if BASE:
    rows.append("")
    rows.append("## Phase-3 equal-hardware baselines (giotto-ph + GUDHI)")
    rows.append(
        "PITH `--threads 1`. Ripser 1 thread. giotto-ph `n_threads=1` and `n_threads=4` "
        "(no edge collapse unless noted). GUDHI Rips is explicit (1 thread). "
        f"giotto-ph {BASE.get('giotto')} is AGPLv3 — oracle only."
    )
    rows.append("| family | n | T | dim | PITH 1-thr | Ripser | giotto t1 | giotto t4 | GUDHI Rips |")
    rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    for r in BASE.get("comparisons") or []:
        def w(key):
            run = (r.get("runs") or {}).get(key) or {}
            if run.get("wall_s"):
                return f"{run['wall_s']:.3f}"
            if run.get("timed_out") or (run.get("error") and "timed out" in str(run.get("error")).lower()):
                return "timeout"
            if run.get("skipped"):
                return "skip"
            if run.get("error"):
                return "fail"
            return ""

        rows.append(
            f"| {r['name']} | {r['n']} | {r['T']} | {r['maxdim']} | {w('pith_exact_t1')} | "
            f"{w('ripser')} | {w('giotto_t1')} | {w('giotto_t4')} | {w('gudhi_rips')} |"
        )

    rows.append("")
    rows.append("## Phase-3 topology (exact engines vs Ripser; scale unmatched)")
    rows.append("| family | n | PITH match | giotto match | GUDHI match | scale unmatched | scale bn H1 |")
    rows.append("| --- | ---: | --- | --- | --- | ---: | ---: |")
    for t in BASE.get("topology") or []:
        pith = (t.get("pith_vs_ripser") or {}).get("exact_match")
        gio = (t.get("giotto_vs_ripser") or {}).get("exact_match")
        gud = (t.get("gudhi_vs_ripser") or {}).get("exact_match")
        sc = t.get("scale_vs_ripser") or {}
        bn = sc.get("bottleneck_h1")
        rows.append(
            f"| {t['name']} | {t.get('n')} | {pith} | {gio} | {gud} | {sc.get('unmatched')} | "
            f"{'' if bn is None else (f'{bn:.4g}' if isinstance(bn, float) else bn)} |"
        )

    rows.append("")
    rows.append("## Phase-3 held-out / post-freeze dispatcher")
    rows.append("| family | n | recommended | auto | oracle | wrong | waste | regime |")
    rows.append("| --- | ---: | --- | --- | --- | --- | ---: | --- |")
    for d in BASE.get("dispatcher_heldout") or []:
        waste = d.get("waste_if_follow_estimate")
        rows.append(
            f"| {d['name']} | {d['n']} | {d.get('recommended')} | {d.get('auto_picked')} | "
            f"{d.get('oracle_faster')} | {d.get('wrong')} | "
            f"{'' if waste is None else (f'{waste:.2f}' if isinstance(waste, float) else waste)} | "
            f"{d.get('regime')} |"
        )

    rows.append("")
    rows.append("## Phase-3 `--mode auto` vs probe")
    rows.append("| family | n | selected | probe | match |")
    rows.append("| --- | ---: | --- | --- | --- |")
    for d in BASE.get("mode_auto_heldout") or []:
        rows.append(
            f"| {d['name']} | {d['n']} | {d.get('selected')} | {d.get('mode_recommended')} | {d.get('match_probe')} |"
        )

    rows.append("")
    rows.append("## Phase-3 local exponents (new series)")
    rows.append("| family | method | n0 | n1 | p_time |")
    rows.append("| --- | --- | ---: | ---: | ---: |")
    for e in BASE.get("exponents") or []:
        pt = f"{e['p_time']:.2f}" if e.get("p_time") is not None else ""
        rows.append(f"| {e['name']} | {e['method']} | {e['n0']} | {e['n1']} | {pt} |")

    # runtime figure including giotto/GUDHI on circle + figure8 + held-out
    series = []
    for fam, label in (
        ("circle_noisy", "circle"),
        ("figure8", "figure8"),
        ("disconnected_circles", "disc. circles"),
        ("grid_holes", "grid holes"),
    ):
        for meth, mlab, color_i in (
            ("pith_exact_t1", "PITH", 0),
            ("ripser", "Ripser", 1),
            ("giotto_t1", "giotto t1", 2),
            ("gudhi_rips", "GUDHI", 3),
        ):
            xy = []
            for r in BASE.get("comparisons") or []:
                if r["name"] != fam:
                    continue
                run = (r.get("runs") or {}).get(meth) or {}
                if run.get("wall_s"):
                    xy.append((r["n"], run["wall_s"]))
            if xy:
                series.append({"name": f"{label} {mlab}", "xy": xy})
    if series:
        svg_scatter(
            FIG / "runtime_baselines.svg",
            series,
            "1-thread exact VR: PITH vs Ripser vs giotto-ph vs GUDHI",
            "n",
            "wall seconds",
        )

if SPARSE:
    rows.append("")
    rows.append("## Sparse Rips (ε=0.6 greedy net) vs VR / scale")
    rows.append("Not exact VR. Sheehy-style interleaving is the literature guarantee; numbers are measured.")
    rows.append("| family | n | exact (s) | scale (s) | sparse (s) | sparse |E| | sparse unmatched | sparse ess | scale unmatched |")
    rows.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
    for t in SPARSE.get("sparse") or []:
        if t.get("larger"):
            continue
        sp = t.get("sparse_vs_ripser") or {}
        sc = t.get("scale_vs_ripser") or {}
        walls = t.get("walls") or {}
        nd = t.get("n_dist") or {}
        ess_s = t.get("ess_sparse") or {}
        rows.append(
            f"| {t['name']} | {t['n']} | {'' if walls.get('exact') is None else f'{walls['exact']:.3f}'} | "
            f"{'' if walls.get('scale') is None else f'{walls['scale']:.3f}'} | "
            f"{'' if walls.get('sparse') is None else f'{walls['sparse']:.3f}'} | {nd.get('sparse')} | "
            f"{sp.get('unmatched')} | H1={ess_s.get(1, ess_s.get('1'))} H2={ess_s.get(2, ess_s.get('2'))} | "
            f"{sc.get('unmatched')} |"
        )
    rows.append("")
    rows.append("## Failure pushes (12 s)")
    rows.append("| family | n | PITH exact | Ripser | giotto t1 |")
    rows.append("| --- | ---: | --- | --- | --- |")
    for r in SPARSE.get("failures") or []:
        def w(key):
            run = (r.get("runs") or {}).get(key) or {}
            if run.get("wall_s"):
                return f"{run['wall_s']:.3f}"
            if run.get("error") and "timed out" in str(run.get("error")).lower():
                return "timeout"
            return run.get("error") or ""

        rows.append(f"| {r['name']} | {r['n']} | {w('pith_exact')} | {w('ripser')} | {w('giotto_t1')} |")

(BENCH / "results" / "consolidation" / "TABLES.md").write_text("\n".join(rows) + "\n")
print("wrote figures and TABLES.md")
