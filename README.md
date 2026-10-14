# PITH — practical persistent homology on CPUs

PITH computes **persistent homology** of a point cloud: which components,
loops, and voids appear and disappear as you thicken the cloud.

It is a **CPU tool**, not a GPU rewrite of Ripser. The gain comes from
choosing the right exact engine, avoiding a dense distance matrix when
the cloud is sparse, and — when exact Vietoris–Rips is no longer
practical — switching to a smaller Euclidean complex and saying so.

We did **not** invent a faster worst-case VR algorithm for every graph.
We **did** make everyday low-dimensional clouds usable at sizes where
stock VR engines time out.

Details: [`docs/WHAT_WE_BUILT.md`](docs/WHAT_WE_BUILT.md),
[`docs/SCALE_PATH.md`](docs/SCALE_PATH.md),
[`docs/COMPLEXITY.md`](docs/COMPLEXITY.md).

## What is this?

A **portfolio**: two exact VR engines, a small dispatcher that picks
between them, sparse graph representations when the threshold graph is
hollow, exact \(H_0\) on the 2D/3D Delaunay skeleton, and an optional
**different** Euclidean complex when exact VR becomes impractical.

## What did we improve?

| Kind | What |
| --- | --- |
| Exact VR, same barcode as Ripser | An **automatic engine**: collapse + implicit cohomology when the residual is thin; RedZeD (active enumeration) when it is not. Sparse \(G_T\) when the cloud is hollow. |
| Exact \(H_0\) in 2D/3D | Kruskal on the Delaunay 1-skeleton (the MST sits inside Delaunay). \(\Theta(n)\) edges instead of all pairs. |
| Large Euclidean clouds | `--mode scale`: flag of a Delaunay / local-radius graph. **Not** Vietoris–Rips. Essential loops and voids are kept on the tested families; finite bars differ. |
| Feasibility | `--estimate` guesses graph size, residual regime, and whether exact VR is reasonable. `--mode auto` follows that probe (default stays `--mode exact` so scripts do not silently change complex). |
| Fair timing | `--threads N` caps workers. Measured 1-thread vs hardware vs Ripser (always 1 thread). |

Internal experiment numbers live in [`RESEARCH_LOG.md`](RESEARCH_LOG.md),
not in the user interface.

## Is it exact?

**`--mode exact` (default)** is exact Vietoris–Rips up to the threshold \(T\).
On the hold suite the barcode matches Ripser (0 unmatched bars), including
a non-Euclidean L1 distance matrix.

**`--mode scale`** is a **different complex** (Delaunay-flag, optional
thicken). Compare essential Betti numbers and unmatched finite bars;
do not treat the diagram as VR.

**`--mode sparse`** is a Sheehy-style sparse Rips approximation.

GUDHI **Alpha** is a third complex: on this suite it **drops** essential
\(H_1/H_2\) (loops and voids become 0). We do not use it as a VR stand-in.

## How to run

```sh
cmake -S src/pith -B src/pith/build -DCMAKE_CXX_COMPILER=g++
cmake --build src/pith/build -j
./src/pith/build/pith_test
```

```sh
# Exact VR (automatic engine)
./src/pith/build/pith --points cloud.csv --maxdim 1 --threshold 1.1

# Force one exact engine (benchmarking)
./src/pith/build/pith --points cloud.csv --mode exact --engine redzed --maxdim 1 --threshold 1.1

# Equal-thread comparison with Ripser
./src/pith/build/pith --points cloud.csv --threads 1 --mode exact --maxdim 1 --threshold 1.1

# Euclidean scale path (d = 2 or 3 only; not exact VR)
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 1 --threshold 1.1
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 2 --threshold 1.4

# Feasibility guess (no persistence)
./src/pith/build/pith --estimate --points cloud.csv --maxdim 1 --threshold 1.1 --format json

# Follow the probe: exact if feasible, else scale (d=2,3) or sparse
./src/pith/build/pith --points cloud.csv --mode auto --maxdim 2 --threshold 1.4
```

`--help` is the stable interface. `--help-experimental` lists research
flags kept for old scripts.

## When should I use each mode?

| Situation | Mode |
| --- | --- |
| You need the VR barcode (including finite bars) | `--mode exact` |
| You want the probe to choose exact / scale / sparse | `--mode auto` |
| Euclidean \(d\in\{2,3\}\), \(n\) in the tens of thousands, essential loops/voids | `--mode scale` |
| You only need \(H_0\) in 2D/3D | `--mode exact --maxdim 0` (Delaunay Kruskal) |
| Abstract / non-Euclidean distances | `--distances FILE --mode exact` |
| Fat residual and `maxdim≥2` (mixed 3D structure) | `--mode scale` if \(d\in\{2,3\}\); else lower \(T\) |
| Exact VR looks infeasible and \(d\ge 4\) | `--mode sparse` or a smaller \(T\); do not use scale |

## How much larger can it go?

On **this** hardware (4 CPUs, 16 GB, no GPU), under a **12 s** wall budget.
1-thread PITH vs 1-thread Ripser unless noted.

| Task | Ripser VR | PITH exact (1 thr) | PITH scale |
| --- | --- | --- | --- |
| Noisy circle \(H_1\), \(n=1000\) | 2.21 s | **0.070 s (31×)** | not needed |
| Noisy circle \(H_1\), \(n=2000\) | timeout (>12 s) | 0.43 s (phase 2) | not needed |
| Figure-8 \(H_1\), \(n=4000\) | timeout (>12 s) | **1.03 s** | 0.09 s, ess \(H_1=2\) |
| Figure-8 \(H_1\), \(n=24000\) | impractical | leftover wall | **0.79 s**, ess \(H_1=2\) |
| Sphere \(H_2\), \(n=400\) | 1.02 s | **0.017 s (60×)** | 6 ms, ess \(H_2=1\) |
| Sphere \(H_2\), \(n=800\) | timeout (>12 s) | **0.057 s** | small |
| Sphere \(H_0{+}H_1{+}H_2\), \(n=80000\) | impractical | impractical as dense VR | **1.08 s**, ess \(H_2=1\) |
| Nested loops \(H_1\), \(n=2000\) | 6.44 s | **0.29 s** | 0.036 s |
| Blobs \(H_0\), \(n=25000\) | tens of seconds | **0.053 s** (Delaunay) | n/a |
| Mixed 1D/2D/3D, \(n=300\), `maxdim=2` | 0.13 s | **timeout** (fat H2) | **5 ms** |

The headline exact ratios **hold at 1 thread**. Hardware threads (4) change
circle \(n=1000\) from 0.070 s to 0.069 s — not the source of the 31×.

![Exact VR runtime](benchmarks/results/consolidation/figures/runtime_exact.svg)

![Peak memory](benchmarks/results/consolidation/figures/memory_exact.svg)

![Local exponents](benchmarks/results/consolidation/figures/exponents.svg)

![Largest n under 12 s](benchmarks/results/consolidation/figures/max_practical.svg)

![Scale path vs exact](benchmarks/results/consolidation/figures/runtime_scale.svg)

Local time exponents (empirical, not theorems): scale stays \(p\approx 1.0\)–\(1.3\);
exact figure-8 / nested-loop \(H_1\) leaves that regime around a few thousand
points (\(p\approx 2.8\)–\(3.0\)); Ripser on the same series is \(p\approx 2.7\)–\(3.5\).

## How accurate is the scale path?

Essential topology on the measured families matches exact VR (two loops on a
figure-8, five on `many_loops`, one void on a sphere, three voids on
`multi_cavities`). Finite bars **do not** match VR.

| Family (\(n=300\)–\(400\)) | Exact vs Ripser | Scale unmatched | Scale bottleneck \(H_1\) | Scale \(W_1\) \(H_1\) | Notes |
| --- | --- | ---: | ---: | ---: | --- |
| figure8, circle, nested, many_loops | match | 0 | \(\sim 10^{-6}\) | \(\sim 10^{-6}\) | 2D loops ≈ VR |
| sphere | match | 52 | 0.024 | 0.21 | ess \(H_2=1\) kept |
| multi_cavities | match | 52 | 0.041 | — | ess \(H_2=3\) kept |
| mixed 1D/2D/3D | exact timed out | 35 | 0.030 | — | `--mode auto` → scale |

GUDHI Alpha on the same clouds reports ess \(H_1=H_2=0\). Sparse Rips
kept essential 2D loops; it failed / was slow on some 3D clouds.

Persistence diagrams at \(n=400\) (filled = essential; scale is **not** VR):

![figure8 PD](benchmarks/results/consolidation/figures/pd_figure8.svg)
![circle PD](benchmarks/results/consolidation/figures/pd_circle_noisy.svg)
![sphere PD](benchmarks/results/consolidation/figures/pd_sphere.svg)

## Dispatcher: when it is right, and when it is wrong

`--estimate` and `--engine auto` share a 250-point residual / edge-fraction
probe. A **1-thread oracle** (run both exact engines) on held-out families:

| Result | Count |
| --- | --- |
| Recommended engine was the faster one | 7 / 8 |
| Wrong: `heavy_noise_circle` \(n=400\) (thin residual → implicit) | waste **2.1×** (11 ms vs 5 ms RedZeD) |

A second miss, caught by the adversarial suite: mixed 1D/2D/3D at
`maxdim=2` is a **fat H2** residual. Exact timed out at \(n=300\); `--estimate`
now marks exact infeasible and recommends `--mode scale`. Auto-dispatch now
probes from \(n\ge 64\) (was 400), so a 200-point L1 matrix uses RedZeD
instead of paying for collapse.

![Dispatcher regime](benchmarks/results/consolidation/figures/dispatcher.svg)

Full numbers: [`benchmarks/results/consolidation/TABLES.md`](benchmarks/results/consolidation/TABLES.md).

## Limits (stated openly)

- Worst-case exact \(H_1\) on a **connected** dense \(G_T\) is still
  the same complexity class as Ripser (active leftover visits).
- Exact \(H_2\) on a **fat** residual can time out at a few hundred points
  (mixed 1D/2D/3D). Use `--estimate` or `--mode scale`.
- `--estimate` is a probe plus conservative cutoffs. It can still be wrong
  (see `heavy_noise_circle`).
- `--mode scale` requires Euclidean \(d\in\{2,3\}\) and is not a VR barcode.
- giotto-ph is not installed here. GUDHI Rips is a slow exact baseline;
  GUDHI Wasserstein was skipped (POT missing). Ripser++ was not built (no GPU).
- `--threads 1` is the fair comparison. Default PITH may use every core for
  a few scans; that is **not** where the 30–60× exact ratios come from.

## Layout

| Path | Role |
| --- | --- |
| `src/pith/` | Engine (C++17) |
| `docs/WHAT_WE_BUILT.md` | Contribution, exact vs approx |
| `docs/SCALE_PATH.md` | Euclidean alternative complex |
| `docs/COMPLEXITY.md` | Worst-case / regime / empirical |
| `docs/GROWTH.md` | Fitted \(t\\approx Cn^p\) slopes (empirical) |
| `docs/SELECTED.md` | Living selected path (research) |
| `RESEARCH_LOG.md` | Iteration ledger |
| `third_party/ripser` | Unmodified Ripser `01add51` |
| `benchmarks/` | Generators, consolidation runners, receipts |

## Reproduce

```sh
python3 benchmarks/generate_datasets.py --list
python3 benchmarks/test_cli_stable.py
python3 benchmarks/test_baseline_hooks.py
python3 benchmarks/run_consolidation.py
python3 benchmarks/run_consolidation_limits.py
python3 benchmarks/eval_mode_auto.py
python3 benchmarks/run_baseline_pack.py
python3 benchmarks/fit_growth.py
python3 benchmarks/plot_consolidation.py
```
