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
