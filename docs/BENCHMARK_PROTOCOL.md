# Benchmark protocol

## Parent

Ripser SHA `01add51ff64aaf40889483260cc5c3b7d0f2a1e7`, field \(\mathbb{F}_2\),
diameter convention, `--dim` as stated. Same threshold \(T\) on every exact
comparison.

## Suites

Synthetic (seed 0 unless noted):

| Dataset | Ambient | Feature | Default \(T\) | Notes |
| --- | --- | --- | --- | --- |
| `circle_noisy` | 2 | \(H_1\) | 1.2 | unit circle + \(N(0,0.05^2)\) |
| `sphere` | 3 | \(H_2\) | 1.4 | unit sphere |
| `torus` | 3 | \(H_1^{\oplus 2}\) | 1.6 | major 2, minor 0.5 |
| `blobs` | 2 | \(H_0\) | 1.0 | 3 isotropic Gaussians |
| `uniform2` | 2 | none | 0.35 | unit square |
| `uniform10` | 10 | none | 1.8 | high-d control |
| `mnist50` | 784→PCA-20 | empirical | 8.0 | 50 digits, if sklearn+openml available |

Sizes: 200, 500, 1000. Raise to 2000+ only when a run finishes in this
16 GB / 4-core image. **No GPU runs.**

## Metrics

Always: wall time (3 repeats when cheap), peak RSS, `n_vertices`,
`n_edges_in`, `n_edges_out`, stage times.

When instrumented: `n_columns_assembled`, `n_columns_reduced`,
`n_columns_apparent`, `n_columns_cleared`, `n_additions`,
`n_cofacet_probes`, `n_distances`.

## Fidelity

| Class | Test |
| --- | --- |
| exact | Persistence pairs match after sorting, death=\(\infty\) aligned, abs error \(< 10^{-4}\) on finite values (float32) |
| approx-guaranteed | Record the theorem and the \(\varepsilon\); do not require pair identity |
| empirical | Bottleneck / \(W_2\) / Betti curves, labeled empirical |
| unverified | Must not be selected |

Different complexes (Alpha vs VR) are never required to have identical diagrams.

## How to run

```sh
python3 benchmarks/generate_datasets.py
python3 benchmarks/run_suite.py --suite smoke
python3 benchmarks/run_suite.py --suite round1
```

Receipts go to `benchmarks/results/`.
