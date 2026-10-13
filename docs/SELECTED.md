# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I043.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse** → **owned** persistent homology on the residual flag filtration.

- \(H_0\): Kruskal / union-find
- \(H_1\): reduce **triangle boundaries** over leftover (non-MST) edges
- \(H_2\): reduce tetrahedron boundaries over triangles whose \(H_1\) boundary vanished

**Fidelity:** exact persistence module of \(\mathrm{VR}_{\le T}\). Identity vs Ripser `01add51` reproduced on I010–I011, I016, I018, I020, I024 (owned engine) and I001–I008 (collapse+Ripser residual). Collapse edge counts match GUDHI (I009, I012).

**What is selected, and what is not**

| Piece | Status |
| --- | --- |
| Ripser `01add51` | Pinned **parent / oracle**, not required at run time |
| Backward edge collapse (our MIT code) | Selected. Faster than GUDHI collapse on I012; counts match |
| Owned triangle-boundary PH | **Selected** as of I010. Replaces stock Ripser on the residual |
| Ripser++ | Unmodified GPU reference. No GPU here; not built |
| Extra collapse passes | **Default adaptive (`--collapse -1`)**: one pass, then two more if residual mean degree \(>6\) (I043). Circle unchanged (deg 2.8). Torus200 1260→977 and now slightly beats Ripser. |
| Alpha / kNN / witness / cubical | Not exact-VR. Alpha is the fastest *other* Euclidean complex (I013) |

## 10× claim (honest scope)

**Algebraic work (columns after vs before collapse), exact VR≤T**

| Dataset | dim | cols uncollapsed → collapsed | ratio |
| --- | --- | --- | --- |
| circle n=80 | \(H_1\) | 9500 → 13 | **731×** |
| blobs n=200 | \(H_1\) | 137982 → 273 | **505×** |
| sphere n=80 | \(H_2\) | 82901 → 345 | **240×** |

**Edges, exact**

| Dataset | n | edges in → out | ratio |
| --- | --- | --- | --- |
| circle_noisy | 1500 | — → — | **127×** |
| circle_noisy | 1000 | 204915 → 2265 | **90×** |
| sphere | 500 | 61225 → 1805 | **34×** |

**Wall-clock vs pinned Ripser (owned PITH, collapse charged)**

| Dataset | dim | n | total vs Ripser |
| --- | --- | --- | --- |
| sphere | \(H_2\) | 500 | **57×** |
| sphere | \(H_2\) | 200 | **14×** |
| circle_noisy | \(H_1\) | 1500 | 3.1× |
| circle_noisy | \(H_1\) | 1000 | 2.6× |

vs GUDHI *explicit* Rips (sphere \(n=500\), \(H_2\)): **1134×** (GUDHI built 1.17e8 simplices). That is a different baseline than Ripser.

**Not claimed**

- 10× wall-clock on \(H_1\) at \(n\le 1500\) (collapse still dominates; trend is up with \(n\))
- 10× on high-d i.i.d. noise or a thick torus (2–4× edges; we can be slower)
- Worst-case asymptotic improvement
- kNN / witness / Alpha as exact VR (I014, I015, I021 reject or other-complex)

## Next levers

1. Asymptotically faster collapse (still the \(H_1\) clock)
2. Optional second collapse pass on thick remainders (torus)
3. Alpha as a *documented other-complex* Euclidean fast path
4. GPU later (Ripser++ reference only)
