# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I070.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + lazy heap, I044) → **owned** persistent homology
on the residual flag filtration.

- \(H_0\): Kruskal / union-find. Adaptive `--collapse -1` **skips collapse**
  when `maxdim=0` (I052, I067).
- \(H_1\): reduce **triangle boundaries** over leftover (non-MST) edges
- \(H_2\): reduce tetrahedron boundaries over triangles whose \(H_1\) boundary vanished

**Fidelity:** exact persistence module of \(\mathrm{VR}_{\le T}\). Identity vs
Ripser `01add51` on I010–I011, I016, I018, I020, I024, I044, I047, I050,
I059–I060, I062, I064, I066–I067, I069.

**What is selected, and what is not**

| Piece | Status |
| --- | --- |
| Ripser `01add51` | Pinned **parent / oracle**, not required at run time |
| Backward edge collapse (sticky + heap) | Selected. Exact; **not** faster than I027 first-match (I044) |
| Owned triangle-boundary PH | **Selected**. Implicit cohomology **rejected** (I045–I046) except a thin cycle (I068) |
| `--distances` CLI | Selected for square CSV (I051). Ripser lower-distance parsed; RP2 n=600 collapse timed out (I061) |
| Adaptive `--collapse -1` | One pass, then two more if residual mean degree \(>6\). **H0 skips collapse.** Do **not** skip on high-d (I055) |
| Ripser++ | Unmodified GPU reference. No GPU here; not built |
| Alpha / kNN / witness / cubical / Sheehy | Not exact-VR |
| Reduced VR (H07) | Size smaller; **finite H1 bars wrong** in the prototype (I056) |

## 10× claim (honest scope)

**Algebraic work (columns after vs before collapse), exact VR≤T**

| Dataset | dim | cols uncollapsed → collapsed | ratio |
| --- | --- | --- | --- |
| circle n=200 | \(H_1\) | 166935 → 85 | **1964×** (I058) |
| circle n=80 | \(H_1\) | 9500 → 13 | **731×** |
| blobs n=200 | \(H_1\) | 137982 → 273 | **505×** |
| sphere n=80 | \(H_2\) | 82901 → 345 | **240×** |
| torus n=200 | \(H_1\) | 55843 → 3098 | **18×** |

**Edges, exact**

| Dataset | n | edges in → out | ratio |
| --- | --- | --- | --- |
| circle_noisy | 2000 | 818703 → 5158 | **159×** (I059) |
| circle_noisy | 1500 | 459662 → 3710 | **124×** |
| circle_noisy | 1000 | 204915 → 2265 | **90×** |
| sphere | 500 | — | **34×** |

**Wall-clock vs pinned Ripser (owned PITH, collapse charged)**

| Dataset | dim | n | total vs Ripser |
| --- | --- | --- | --- |
| sphere | \(H_2\) | 500 | **57×** |
| sphere | \(H_2\) | 200 | **14×** |
| circle_noisy | \(H_1\) | 2000 | **4.6×** |
| circle_noisy | \(H_1\) | 1500 | **3.4×** |
| circle_noisy | \(H_1\) | 1000 | **2.6–2.8×** |

vs GUDHI *explicit* Rips (sphere \(n=500\), \(H_2\)): **1134×**. Different baseline.

**Not claimed**

- 10× wall-clock on \(H_1\) at \(n\le 2000\) (collapse still dominates; **trend is up with \(n\) and \(T\)**)
- 10× on high-d i.i.d. noise (0.07×) or a thick torus (0.78× adaptive at n=500)
- Worst-case asymptotic improvement
- Implicit cohomology, reduced-VR PH, Sheehy, Alpha as exact VR

## Next levers

1. Asymptotically faster collapse (the only remaining H1 10×-clock path)
2. A *correct* implicit / Ripser-class residual engine for thick remainders and high-d
3. Alpha as a documented other-complex Euclidean fast path
4. GPU later (Ripser++ reference only)
