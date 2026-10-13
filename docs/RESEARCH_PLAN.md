# Research plan

Living plan for a CPU-first persistent-homology engine that aims at
**~10× less algebraic work** than pinned Ripser on the same Vietoris–Rips
filtration, not merely faster constants.

## Questions

1. Which complex should be the default for which data class?
2. Which existing techniques cut *work* (edges, columns, additions) rather than wall-clock?
3. Can flag edge collapse plus residual implicit cohomology beat Ripser by ≥10× on typical clouds while staying exact?
4. After collapse, is the remainder still apparent-pair rich, or do we need extra Morse / reduced VR / RedZeD?
5. Which parallel or distributed ideas are mathematically valid?

## Stages

| Stage | Exit criterion |
| --- | --- |
| S0 Survey | Complexes, frameworks, papers, methodology documented |
| S1 Harness | Pinned Ripser runs; receipts regenerate; diagrams parse |
| S2 Collapse | Own exact edge-collapse; identity vs Ripser; edge ratio measured |
| S3 PITH residual | Implicit cohomology on the collapsed graph; identity; counters |
| S4 Challenge | Alternative levers (Morse, reduced VR, Alpha, sparse, witness) one at a time |
| S5 Select | Freeze a selected pipeline if 10× holds, or report the honest ceiling |

## Decision criteria

A variant **replaces** the selected algorithm only if:

- fidelity class is at least as strong as the claim (exact VR vs approx);
- a named work counter drops with the construction cost charged;
- diagrams match (exact) or the stated interleaving/bottleneck bound holds;
- the receipt is replayable.

Wall-clock alone never promotes a variant.

## Selected (current)

- **Baseline:** unmodified Ripser `01add51`.
- **Candidate kernel:** PITH = threshold graph → backward edge collapse → implicit cohomology.
- **GPU reference:** Ripser++ clone; not runnable here.
