# TDA-optimization

CPU-first research toward a persistent-homology algorithm that does
**less algebraic work** than Ripser, not just faster constants.

Target: about **10×** fewer edges / columns on typical point clouds,
**exact** for Vietoris–Rips whenever exactness is claimed.

## Current selected pipeline

**PITH-E3:** build the threshold graph \(G_T\) → filtration-preserving
**edge collapse** → run pinned **Ripser** on the residual sparse
1-skeleton.

This is exact for \(\mathrm{VR}_{\le T}\). On noisy circles, blobs, and
spheres at \(n=200\) the residual has **10–29×** fewer edges than
\(G_T\), and diagrams match Ripser. Details: [`docs/SELECTED.md`](docs/SELECTED.md).

Our own cohomology reducer is **not** selected yet (diagrams fail on
dense uncollapsed graphs).

## Layout

| Path | Role |
| --- | --- |
| `INSTRUCTIONS.md` | Research brief |
| `RESEARCH_LOG.md` | Short session ledger |
| `docs/` | Methodology, complexes, frameworks, papers, protocol |
| `src/pith/` | MIT engine: collapse + experimental reducer |
| `third_party/ripser` | Unmodified CPU parent (`01add51`) |
| `third_party/ripser-plusplus` | Unmodified GPU reference (not built: no GPU) |
| `papers/` | Open-access PDFs |
| `benchmarks/` | Datasets, harness, receipts |

## Build

```sh
g++ -std=c++11 -O3 -DNDEBUG third_party/ripser/ripser.cpp -o third_party/ripser/ripser
cmake -S src/pith -B src/pith/build -DCMAKE_CXX_COMPILER=g++
cmake --build src/pith/build -j
./src/pith/build/pith_test
```

## Benchmarks

```sh
python3 benchmarks/generate_datasets.py --sizes 80,200,500
python3 benchmarks/run_suite.py --suite smoke
python3 benchmarks/run_iterations.py
```

## Environment limits (this Cloud Agent image)

- 4 CPUs, 16 GB RAM, **no GPU / CUDA**
- Ripser++ is a local clone, not a remote fork, and was not compiled
- Julia / GUDHI / giotto-ph are not assumed installed
