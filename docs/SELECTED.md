# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I116.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + lazy heap + cheap degree filter) → **owned**
triangle/tet-boundary persistent homology.

- \(H_0\): Kruskal. `--collapse -1` **skips collapse** when `maxdim=0`.
- \(H_1\): triangle boundaries over leftover (non-MST) edges
- \(H_2\): tet boundaries over empty-boundary triangles

**Fidelity:** exact \(\mathrm{VR}_{\le T}\) vs Ripser `01add51` on the I044–I098 suite
after the I081 bitset revert.

**Rejected this wave (exact but not better)**

| Lever | Why |
| --- | --- |
| Bitset neighborhood AND (I071–I081) | Exact; **slower** (circle2000 collapse 5.8 s vs 2.6 s) |
| Implicit cohomology (I045–I046, I094) | Wrong barcodes except a thin cycle |
| Time-axis D&C (I088) | Parallel schedule, not less sequential work |
| High-d skip (I055) | Skip+homology 0.005× vs Ripser |
| Reduced VR prototype (I056) | Finite \(H_1\) wrong |
| Sheehy sparse (I057) | Not exact VR |

## 10× claim (honest scope)

**Algebraic (columns / edges), exact VR≤T** — still far past 10× on typical low-d.

| Dataset | metric | ratio |
| --- | --- | --- |
| circle80 | columns | **731×** (I095) |
| circle200 | columns | **1964×** (I058) |
| circle n=2000 | edges | **159×** |

**Wall-clock vs Ripser**

| Dataset | dim | n | T | vs Ripser |
| --- | --- | --- | --- | --- |
| sphere | \(H_2\) | 500 | 1.4 | **59×** (I085) |
| circle_noisy | \(H_1\) | 4000 | 1.5 | **8.38×** (I117) |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **8.0×** (I115) |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **7.2×** (I096) / 6.4× (I114, same machine) |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **3.8–4.8×** |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; thick torus; worst-case asymptotics.
I117: n=4000 T=1.5 is **8.38×** (Ripser 287 s / PITH 34 s). Gains vs n=3000 are diminishing; 10× H1 is not a pure-n play.

## Next levers (still open after I118)

1. T-sweep around 1.5 on n=3000 (I119) for a better large-T sweet spot
2. A collapse cheaper than \(O(n^3)\) sequential (progressive/bitset/budget all failed)
3. A correct Ripser-class residual engine (implicit still rejected; RedZeD unimplemented)
4. Thick torus / high-d remainder (torus200 adaptive 1.12× this run)
5. GPU later (Ripser++ reference only)
