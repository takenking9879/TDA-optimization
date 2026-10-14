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

## What did we improve?

| Kind | What |
| --- | --- |
| Exact VR, same barcode as Ripser | An **automatic engine**: collapse + implicit cohomology when the residual is thin; RedZeD (active enumeration) when it is not. Sparse \(G_T\) when the cloud is hollow. |
| Exact \(H_0\) in 2D/3D | Kruskal on the Delaunay 1-skeleton (the MST sits inside Delaunay). \(\Theta(n)\) edges instead of all pairs. |
| Large Euclidean clouds | `--mode scale`: flag of a Delaunay / local-radius graph. **Not** Vietoris–Rips. Essential loops and voids are kept on the tested families; finite bars differ. |
| Feasibility | `--estimate` guesses whether exact VR is reasonable before you pay for it. Heuristic, low confidence. |

Internal experiment numbers (I263, I297, …) live in
[`RESEARCH_LOG.md`](RESEARCH_LOG.md), not in the user interface.

## Is it exact?

**`--mode exact` (default)** is exact Vietoris–Rips up to the threshold \(T\).
On the hold suite the barcode matches Ripser (0 unmatched bars).

**`--mode scale`** is a **different complex** (Delaunay-flag, optional
thicken). Compare essential Betti numbers and unmatched finite bars;
do not treat the diagram as VR.

**`--mode sparse`** is a Sheehy-style sparse Rips approximation.

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

# Euclidean scale path (d = 2 or 3 only; not exact VR)
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 1 --threshold 1.1
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 2 --threshold 1.4

# Feasibility guess (no persistence)
./src/pith/build/pith --estimate --points cloud.csv --maxdim 1 --threshold 1.1 --format json
```

`--help` is the stable interface. `--help-experimental` lists research
flags kept for old scripts.

## When should I use each mode?

| Situation | Mode |
| --- | --- |
| You need the VR barcode (including finite bars) | `--mode exact` |
| Euclidean \(d\in\{2,3\}\), \(n\) in the tens of thousands, essential loops/voids | `--mode scale` |
| You only need \(H_0\) in 2D/3D | `--mode exact --maxdim 0` (Delaunay Kruskal) |
| Abstract / non-Euclidean distances | `--distances FILE --mode exact` |
| Exact VR looks infeasible and \(d\ge 4\) | `--mode sparse` or a smaller \(T\); do not use scale |

## How much larger can it go?

On **this** hardware (4 CPUs, 16 GB, no GPU), measured:

| Task | Ripser VR | PITH exact | PITH scale |
| --- | --- | --- | --- |
| Noisy circle \(H_1\), \(n=1000\) | ~0.3–1 s | tens of ms (collapse) | not needed |
| Figure-8 \(H_1\), \(n=4000\) | ~29 s | ~1.1 s | milliseconds–0.2 s |
| Figure-8 \(H_1\), \(n=16000\) | timeout / huge \(G_T\) | leftover wall | **0.54 s**, ess \(H_1=2\) |
| Sphere \(H_2\), \(n=800\) | ~30 s | **56 ms** (collapse) | small |
| Sphere \(H_0{+}H_1{+}H_2\), \(n=80000\) | impractical | impractical as dense VR | **1.09 s**, ess \(H_2=1\) |
| Blobs \(H_0\), \(n=25000\) | tens of seconds | **55 ms** (Delaunay) | n/a |

Scaling curves and local exponents: `benchmarks/results/consolidation/`
after `python3 benchmarks/run_consolidation.py`.

## How accurate is the scale path?

Essential topology on the measured families is kept (two loops on a
figure-8, one void on a sphere). Finite bars **do not** match VR —
typically tens to hundreds of unmatched short intervals at \(n=400\).
See [`docs/SCALE_PATH.md`](docs/SCALE_PATH.md) and the topology table
in the consolidation report.

## Limits (stated openly)

- Worst-case exact \(H_1\) on a **connected** dense \(G_T\) is still
  the same complexity class as Ripser (active leftover visits).
- `--estimate` is a 250-point probe plus conservative cutoffs. It can
  be wrong; that is reported in the dispatcher evaluation.
- `--mode scale` requires Euclidean \(d\in\{2,3\}\).
- giotto-ph is not wired here (not installed on this image). GUDHI
  Rips is available as a slow exact baseline. Ripser++ was not built
  (no GPU).
- PITH may use all available CPU threads for a few scans; Ripser is
  single-threaded. Ratios mix that difference — we record it.

## Layout

| Path | Role |
| --- | --- |
| `src/pith/` | Engine (C++17) |
| `docs/WHAT_WE_BUILT.md` | Contribution, exact vs approx |
| `docs/SCALE_PATH.md` | Euclidean alternative complex |
| `docs/COMPLEXITY.md` | Worst-case / regime / empirical |
| `docs/SELECTED.md` | Living selected path (research) |
| `RESEARCH_LOG.md` | Iteration ledger |
| `third_party/ripser` | Unmodified Ripser `01add51` |
| `benchmarks/` | Generators, consolidation runner, receipts |

## Reproduce

```sh
python3 benchmarks/generate_datasets.py --list
python3 benchmarks/test_cli_stable.py
python3 benchmarks/run_consolidation.py
```
