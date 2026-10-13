# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I008.

## Selected exact-VR CPU pipeline

**Name:** PITH-E3 — threshold graph → backward flag edge collapse → stock Ripser on the residual sparse 1-skeleton.

**Fidelity:** exact persistence module of \(\mathrm{VR}_{\le T}\) (Boissonnat–Pritam 2020; Glisse–Pritam 2022). Identity vs unmodified Ripser on the same \(T\) is **reproduced** on the smoke + I001 suite (12/12 E3 matches).

**What is selected, and what is not**

| Piece | Status |
| --- | --- |
| Ripser `01add51` | Pinned parent / residual engine |
| Backward edge collapse (our MIT code) | Selected preprocessor. Unit tests C4 / C4+diagonal. |
| Our implicit cohomology core | **Not selected.** H02 rejected: diagrams fail on uncollapsed graphs. |
| Ripser++ | Unmodified GPU reference. No GPU here; not built. |
| Extra collapse passes | Hold. Circles: 283 → 281 edges. Not worth a default second pass. |
| Alpha / sparse Rips / witness | Not selected for exact-VR. Still open as different complexes. |

## 10× claim (honest scope)

**Structural, exact, typical low-d geometric clouds, metric = residual edges (and therefore residual cliques).**

| Dataset | n | T | edges in → out | ratio | E3 identity |
| --- | --- | --- | --- | --- | --- |
| circle_noisy | 200 | 1.2 | 8197 → 283 | **29×** | yes |
| blobs | 200 | 1.0 | 6495 → 445 | **15×** | yes |
| sphere | 200 | 1.4 | 9675 → 819 | **12×** | yes |
| uniform2 | 200 | 0.35 | 5405 → 528 | **10×** | yes |
| torus | 200 | 1.6 | 4789 → 1260 | 3.8× | yes |
| uniform10 | 200 | 1.8 | 19622 → 9543 | 2.1× | yes |

On a noisy circle the residual 1-skeleton **stops growing with \(T\)** (I004: 283 edges for every \(T\ge 0.4\)). Ripser’s input keeps filling in; collapse trims the dominated chords. At \(T=1.5\), edge ratio **38×** and residual Ripser time **~10×** below dense Ripser (15.8 ms → 1.6 ms). Collapse time is still charged.

Headline wall-clock (dense-lookup collapse, I008, exact):

| Dataset | dim | n | edges | residual PH | **total vs Ripser** |
| --- | --- | --- | --- | --- | --- |
| sphere | \(H_2\) | 500 | 37× | 425× | **25×** |
| circle_noisy | \(H_1\) | 1000 | 90× | 175× | 2.0× |
| circle_noisy | \(H_1\) | 500 | 53× | 41× | 2.2× |

So the **10× total-time** goal is met on Euclidean \(H_2\) (sphere \(n=500\)). On \(H_1\) the work cut is larger (53–90× edges) but collapse still dominates the clock.

**Not claimed**

- 10× wall-clock of *collapse + residual* vs Ripser at \(n\le 200\) (collapse dominates).
- 10× on high-d i.i.d. noise or on a thick torus at these \(T\).
- 10× from our own reducer (incorrect).
- Asymptotic worst-case improvement (high-d dense graphs remain \(\Theta(n^2)\)).

## Next levers

1. Faster collapse (dominates wall-clock) — implementation, not a new theorem.
2. Fix the owned residual reducer (H02) so we do not depend on Ripser for the remainder.
3. Extra Morse / reduced VR only if the collapsed remainder is still expensive (torus, \(H_2\)).
4. Alpha for Euclidean \(d\le 3\) as a *different* exact filtration.
5. Larger \(n\) (500–2000) where Ripser clique work should overtake collapse.
