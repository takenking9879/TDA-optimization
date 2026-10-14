# Empirical growth models

Fits of \(t \approx C n^{p}\) on the consolidation receipts.
These are **pre-asymptotic slopes**, not theorems.
Local exponents \(p_i = \log(t_{i+1}/t_i)/\log(n_{i+1}/n_i)\) detect regime changes.

Hardware: 4 CPU / 16 GB. Phase-2 exact times are 1-thread unless noted.

| series | n range | C | p | R² | local p | regime |
| --- | --- | ---: | ---: | ---: | --- | --- |
| anisotropic_blob pith_exact | 400–1000 | 5.77e-05 | 0.84 | 1.00 | 400→1000:0.84 | near-linear / low-polynomial |
| anisotropic_blob ripser | 400–1000 | 6.53e-08 | 2.06 | 1.00 | 400→1000:2.06 | quadratic-ish polynomial |
| blobs pith_exact | 1000–25000 | 6.91e-06 | 0.88 | 0.99 | 1000→4000:0.74, 4000→12000:0.98, 12000→25000:0.97 | near-linear / low-polynomial |
| blobs ripser | 1000–12000 | 1.3e-08 | 2.12 | 1.00 | 1000→4000:2.12, 4000→12000:2.11 | quadratic-ish polynomial |
| circle_T pith_exact | 400–800 | 0.207 | -0.38 | 1.00 | 400→800:-0.38 | near-linear / low-polynomial |
| circle_T ripser | 400–800 | 70.6 | -0.94 | 1.00 | 400→800:-0.94 | near-linear / low-polynomial |
| circle_noisy pith_exact | 200–4000 | 2.58e-07 | 1.87 | 0.82 | 200→500:0.77, 500→1000:2.01, 1000→2000:2.23, 2000→4000:2.70 | quadratic-ish polynomial |
| circle_noisy ripser | 200–1000 | 1.63e-09 | 3.05 | 1.00 | 200→500:3.17, 500→1000:2.87 | high polynomial (combinatorial leftover / tet tax) |
| figure8 exact_redzed | 2000–4000 | 9.16e-11 | 2.79 | 1.00 | 2000→4000:2.79 | high polynomial (combinatorial leftover / tet tax) |
| figure8 pith_exact | 200–4000 | 4.82e-08 | 1.98 | 0.84 | 200→500:1.49, 500→1000:1.42, 1000→2000:2.50, 2000→4000:2.79 | quadratic-ish polynomial |
| figure8 pith_scale | 200–24000 | 5.9e-06 | 1.16 | 0.99 | 200→500:0.71, 500→1000:1.10, 1000→2000:1.15, 2000→4000:1.31, 4000→8000:1.37, 8000→16000:1.20, 16000→24000:1.11 | near-linear / low-polynomial |
| figure8 ripser | 200–2000 | 4.36e-09 | 2.59 | 0.80 | 200→500:1.84, 500→1000:2.37, 1000→2000:4.00 | high polynomial (combinatorial leftover / tet tax) |
| loops_with_bridges pith_exact | 400–1000 | 2.24e-07 | 1.75 | 1.00 | 400→1000:1.75 | quadratic-ish polynomial |
| loops_with_bridges pith_scale | 400–1000 | 9.96e-06 | 1.06 | 1.00 | 400→1000:1.06 | near-linear / low-polynomial |
| loops_with_bridges ripser | 400–1000 | 8.64e-10 | 2.76 | 1.00 | 400→1000:2.76 | high polynomial (combinatorial leftover / tet tax) |
| many_loops pith_exact | 400–2000 | 2.08e-06 | 1.23 | 0.95 | 400→1000:0.89, 1000→2000:1.72 | near-linear / low-polynomial |
| many_loops pith_scale | 400–2000 | 1.03e-05 | 1.03 | 0.98 | 400→1000:0.85, 1000→2000:1.30 | near-linear / low-polynomial |
| many_loops ripser | 400–2000 | 7.9e-10 | 2.60 | 1.00 | 400→1000:2.46, 1000→2000:2.80 | high polynomial (combinatorial leftover / tet tax) |
| mixed_1d2d3d pith_scale | 300–600 | 1.27e-05 | 1.06 | 1.00 | 300→600:1.06 | near-linear / low-polynomial |
| mixed_1d2d3d ripser | 300–600 | 2.46e-09 | 3.12 | 1.00 | 300→600:3.12 | high polynomial (combinatorial leftover / tet tax) |
| multi_cavities pith_exact | 300–600 | 4.98e-12 | 3.65 | 1.00 | 300→600:3.65 | faster than n^3.5 on this window (do not call exponential without more decades) |
| multi_cavities pith_scale | 300–600 | 1.13e-05 | 1.06 | 1.00 | 300→600:1.06 | near-linear / low-polynomial |
| multi_cavities ripser | 300–600 | 6.21e-10 | 3.16 | 1.00 | 300→600:3.16 | high polynomial (combinatorial leftover / tet tax) |
| multi_scale_loops pith_exact | 400–1000 | 1.08e-06 | 1.44 | 1.00 | 400→1000:1.44 | quadratic-ish polynomial |
| multi_scale_loops pith_scale | 400–1000 | 7.01e-06 | 1.11 | 1.00 | 400→1000:1.11 | near-linear / low-polynomial |
| multi_scale_loops ripser | 400–1000 | 2.11e-10 | 3.09 | 1.00 | 400→1000:3.09 | high polynomial (combinatorial leftover / tet tax) |
| near_degenerate pith_exact | 400–1000 | 3.52e-06 | 1.17 | 1.00 | 400→1000:1.17 | near-linear / low-polynomial |
| near_degenerate ripser | 400–1000 | 7.61e-08 | 1.88 | 1.00 | 400→1000:1.88 | quadratic-ish polynomial |
| nested_loops pith_exact | 400–2000 | 4.9e-08 | 2.02 | 0.91 | 400→1000:1.36, 1000→2000:2.98 | quadratic-ish polynomial |
| nested_loops pith_scale | 400–2000 | 1.54e-05 | 1.02 | 1.00 | 400→1000:1.08, 1000→2000:0.94 | near-linear / low-polynomial |
| nested_loops ripser | 400–2000 | 4.71e-10 | 3.05 | 0.98 | 400→1000:2.71, 1000→2000:3.55 | high polynomial (combinatorial leftover / tet tax) |
| sphere pith_exact | 200–800 | 3.84e-07 | 1.78 | 1.00 | 200→400:1.82, 400→800:1.74 | quadratic-ish polynomial |
| sphere pith_scale | 200–80000 | 2.44e-05 | 0.95 | 1.00 | 200→400:0.55, 400→4000:1.20, 4000→16000:0.56, 16000→50000:1.07, 50000→80000:1.03 | near-linear / low-polynomial |
| sphere ripser | 200–400 | 1.31e-08 | 3.03 | 1.00 | 200→400:3.03 | high polynomial (combinatorial leftover / tet tax) |
| torus pith_exact | 400–2000 | 1.35e-07 | 1.86 | 0.99 | 400→1000:1.63, 1000→2000:2.18 | quadratic-ish polynomial |
| torus ripser | 400–2000 | 1.05e-09 | 2.85 | 1.00 | 400→1000:2.98, 1000→2000:2.66 | high polynomial (combinatorial leftover / tet tax) |
| uniform2 pith_exact | 500–4000 | 1.11e-06 | 1.46 | 0.93 | 500→1000:1.10, 1000→2000:1.23, 2000→4000:2.12 | quadratic-ish polynomial |
| uniform2 ripser | 500–4000 | 2.19e-08 | 2.21 | 1.00 | 500→1000:1.91, 1000→2000:2.44, 2000→4000:2.19 | high polynomial (combinatorial leftover / tet tax) |

## How to read p

- \(p \approx 1\)–\(1.3\): scale path / Delaunay \(H_0\) on this window.
- \(p \approx 2\): listing a dense \(G_T\) or RedZeD on a connected graph.
- \(p \approx 2.8\)–\(3.5\): leftover visits or Ripser tet tax. Exact VR is leaving the cheap regime.
- Do **not** call a 2-point slope “exponential.”

The feasibility probe uses these regimes: fat `maxdim≥2` or conservative `|E|>8e6`
means exact VR is marked impractical.

## Phase-3 baselines (giotto-ph / GUDHI, local \(p\) only)

Two-point slopes from `baselines.json`. Same hardware. Not theorems.

| series | n0→n1 | p_time |
| --- | --- | ---: |
| circle PITH exact | 500→1000 | 1.98 |
| circle Ripser | 500→1000 | 2.85 |
| circle giotto t1 | 500→1000 | 2.82 |
| circle GUDHI Rips | 200→500 | 3.28 (then timeout at 1000) |
| figure8 PITH exact | 1000→2000 | 2.74 |
| figure8 Ripser | 1000→2000 | 4.00 |
| figure8 giotto t1 | 1000→2000 | 3.87 |
| sphere Ripser / giotto t1 | 200→400 | 3.03 / 2.98 |
| disconnected_circles Ripser / giotto | 400→1000 | 2.96 / 2.87 |
| dense RGG GUDHI Rips | 400→800 | 3.32 |

giotto-ph tracks Ripser’s slope. 4 threads do not change the \(H_1\)
exponent. GUDHI’s explicit tree is the first to leave the 12 s budget.

`--estimate` now emits that \(p\) as `growth_p` plus a conservative
runtime band (`est_runtime_lo_s` / `est_runtime_hi_s`) and
`leaving_cheap_regime`. Engine \(\tau\) is unchanged. On mixed 1D/2D/3D
\(n=300\) it reports leave=true / mode=scale; sphere \(n=400\) predicted
0.006–0.019 s and measured 0.017 s.

When the probe recommends sparse it also reports `est_sparse_runtime_s`
(\(t\approx C n^2\): \(C=1.3\times 10^{-8}\) in \(d\in\{2,3\}\),
\(8\times 10^{-8}\) otherwise) and `skips_dense_matrix`.

## Fused sparse vs scale (local \(p\), 1 thread)

From `sparse_scale.json`. Not theorems.

| series | n0→n1 | p_wall | p_edges |
| --- | --- | ---: | ---: |
| figure8 sparse | 8k→12k / 12k→16k / 16k→24k | 2.01 / 2.00 / 1.89 | ~1.4 |
| figure8 scale | same | 1.24 / 1.11 / 1.22 | ~1.1 |
| circle sparse | 4k→8k / 8k→12k | 1.96 / 1.68 | ~1.3 |
| circle scale | same | 1.34 / 1.10 | ~1.1 |
| nested / disconnected sparse | 4k→8k | 2.17 / 1.93 | ~1.3 |
| uniform4 sparse (d=4) | 800→1600 | 1.91 | ~1.5 |

Sparse \(H_1\) stays inside the 12 s budget through figure-8 \(n=24000\)
(**5.56 s / 101 MB / ess \(H_1=2\)**). Scale is still ~7× faster there.
The sparse exponent is the FPS \(\Theta(n^2)\) wall, not leftover algebra.

## `--estimate` bands (empirical, τ frozen)

`growth_p` is a **regime bucket** (H0 1.0 / scale 1.2 / sparse 2.0 / fat H2 3.2 /
thin 2.2 / hollow 1.8 / else 2.4), not a per-series fit from this file.
`eval_estimate.py` scores the recommended-mode wall against
`[est_runtime_lo, est_runtime_hi]`. After a 5 ms exact overhead and a
25 ms hi-floor (small-n process tax), **32/32** scored walls sit in band.
It does **not** change `engine_rec` or \(\tau\).
`--estimate` also emits `wall_kind`: `collapse` on thin residuals
(circle 32× is collapse, not pairing), `leftover` on fat/hollow exact
(figure-8 \(n=2000\) / torus), `construction` on H0 / scale / sparse.

## Axis scaling (T / noise / density / dimension)

1-thread, 8 s budget, `axis_scaling.json`. Local \(p\) here is
\(\log(t_{i+1}/t_i)/\log(x_{i+1}/x_i)\) along the **axis**, not \(n\).
Empirical. \(\tau\) unchanged.

### Threshold \(T\) (circle \(n=400\))

| \(T\) | PITH exact | RedZeD | Ripser | giotto t1 | GUDHI | scale |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.4 | 0.004 | 0.003 | 0.007 | 0.011 | 0.037 | 0.004 |
| 1.2 | 0.010 | 0.007 | 0.061 | 0.075 | 0.452 | 0.005 |
| 2.0 | 0.023 | 0.013 | 0.261 | 0.314 | 3.207 | 0.006 |

Ripser / giotto \(p_T\approx 2.6\)–\(3.2\) after \(T>0.8\). GUDHI
\(p_T=5.37\) on \(1.6\to 2.0\) (explicit simplex tree; combinatorial,
not a claimed exponential). PITH exact \(p_T\approx 0.5\)–\(1.9\).
Scale / sparse stay 4–7 ms. At \(T\ge 1.6\) the circle fills
(ess \(H_1=0\)). Figure-8 \(n=800\), \(T=1.1\to 1.4\): Ripser
\(p_T=5.02\), PITH auto \(0.90\).

### Noise \(\sigma\) (circle \(n=500\), \(T=1.5\))

More noise makes exact VR **cheaper**: Ripser \(0.30\) s at \(\sigma=0\)
→ \(0.034\) s at \(\sigma=0.3\). ess \(H_1\) is lost at \(\sigma\ge 0.15\).
That is residual thinning, not a speedup to keep. Scale stays 5–9 ms.

### Density \(T\) (uniform2 \(n=800\))

GUDHI explicit is the **first failure** on this axis: timeout at
\(T=0.55\). At that point PITH exact is 19 ms, Ripser 104 ms, scale 10 ms.
GUDHI \(p_T=3.6\)–\(4.1\) on \(0.12\to 0.35\).

### Ambient dimension (uniform, fixed \(T\))

Higher \(d\) at the same \(T\) is **sparser** (typical distances grow)
and faster: Ripser \(n=400\) \(d=2\to 4\) is \(17\to 8\) ms. Do **not**
treat ambient dimension as a hardness proxy; use edge-frac / \(\lvert E\rvert\).
`--mode scale` exists only for \(d\in\{2,3\}\).

### CPU (1-thread cells)

PITH `--threads 1`: `cpu_s / wall_s` \(\approx 1\). Ripser is 1 thread.
giotto’s first cell includes interpreter import (cpu \(\gg\) wall);
later cells track wall. GUDHI cpu tracks wall at large \(T\).
The T-axis ratios are not a multi-core artifact.
