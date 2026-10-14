# Parallelism and distribution (research only)

No distributed system is implemented in this stage. This note records
what is mathematically valid.

## Safe to parallelize (same global filtration)

| Stage | Dependency | Notes |
| --- | --- | --- |
| Pairwise distances / \(G_T\) | Embarrassingly parallel | Must keep one global metric |
| Apparent-pair scan | Local, independent | Ripser++ / giotto-ph already do this |
| Edge-collapse domination tests *within one grade* | Limited | Backward algorithm is sequential across decreasing \(t\) |
| Residual column reduction | Sequential emergent pairs | Lock-free hash (giotto-ph) helps occupancy, not asymptotic work |
| GPU remainder | Same algebra | Ripser++: GPU apparent, CPU reduce |

## Not valid

- Partition the point cloud, compute barcodes, **union the diagrams**.
  That is a different (nerve / mapper-like) estimator, not global VR PH.
- Independent per-shard edge collapse without ghost neighborhoods.
  Domination uses common neighbors that may sit across the cut.

## Promising later (not built)

1. **Reduce globally, reduce algebra locally.** Collapse the 1-skeleton
   with a distributed graph (ghost 2-hops), then shard residual columns.
2. **Landmarks / witness** — different estimator; work scales with \(|L|\).
3. **DIPHA-style** — explicit matrix, MPI; useful for cubical / general
   complexes, not the first VR kernel.
4. **Oineus / lock-free cohomology** — same work, more cores.

## Preference

Keep one global flag filtration. Cut work first (collapse, Morse,
threshold). Parallelize the remaining independent scans. Do not design
the CPU algorithm around CUDA.
