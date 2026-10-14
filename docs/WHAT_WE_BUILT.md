# What we actually built

This is a precise account of PITH after iterations I001–I312.
It is **not** a claim that we found a new worst-case persistent-homology
algorithm. Claims are tagged **[citation]**, **[derivation]**, or
**[empirical]**. Complexity details: [`COMPLEXITY.md`](COMPLEXITY.md).

## One-sentence contribution

PITH is a **CPU portfolio** that (1) detects which exact VR engine is
cheaper on a given cloud, (2) avoids dense \(n\times n\) representations
when the threshold graph is sparse, and (3) offers a **controlled
Euclidean alternative complex** when exact VR becomes impractical.

That is a **dispatcher + sparse representations + optional different
complex**, plus a few owned data-structure cuts on sparse flags. It is
not a new exact-VR complexity class on a connected \(G_T\).

## What is existing vs owned

### Existing algorithms we implemented or wrapped

| Piece | Source | Role |
| --- | --- | --- |
| Ripser-style implicit cohomology | Bauer; de Silva dualities; Chen–Kerber twist **[citation]** | Exact residual \(H_1\) after collapse |
| Flag edge collapse | Boissonnat–Pritam / GUDHI sticky-dominator **[citation]** | Exact reduction of the 1-skeleton |
| RedZeD (active enumeration) | Kapulkin–Kershaw, arXiv:2606.06310, MIT vendor `22ef1bf` **[citation]** | Exact VR on the full metric when collapse is a tax |
| Kruskal \(H_0\) | Classical **[citation]** | Connected components |
| Sheehy sparse Rips (greedy net) | Sheehy **[citation]** | Optional approx path (`--mode sparse`) |
| Euclidean MST \(\subseteq\) Delaunay | Classical **[citation]** | Exact \(H_0\) on a \(\Theta(n)\) graph in \(d\in\{2,3\}\) |

### Representation improvements (owned, not new PH theorems)

- Spatial / hash \(G_T\) instead of a dense lower triangle when the cloud is hollow **[empirical, I256–I263]**.
- Growing adjacency for leftover cofaces and H2 streaming when \(\lvert E\rvert\le 16n\) **[derivation: \(O(\lvert E\rvert\deg)\) vs \(O(\lvert E\rvert n/64)\); I301–I306]**.
- Walk-locate 2D/3D Delaunay construction (Bowyer–Watson, no cavity-slot reuse) **[derivation: expected \(O(n\log n)\) incremental Delaunay under standard location; I271/I275]**.

### New dispatch logic (owned combination)

`--engine auto` probes a 250-point collapse residual and an edge-fraction
oracle, then picks **RedZeD** (fat or hollow) or **collapse + implicit**
(thin circle-like residuals). Thresholds \(\tau_{H_1}=0.04\),
\(\tau_{H_2}=0.15\), hollow if edge-frac \(<0.25\). The probe runs at
\(n\ge 64\) (was 400; the higher cutoff left small abstract metrics on
collapse). **[empirical, I235+I263 + consolidation]**

`--mode auto` runs the same probe and then **executes** the recommended
path (`exact` / `scale` / `sparse`). Default remains `--mode exact` so
existing scripts do not silently change complex. Held-out check: **8/8**
(phase 2) and **9/9** vs probe on post-freeze families (phase 3).
Engine choice inside exact can still be wrong (phase-3 oracle **5/9**;
waste 1.3–2.75×, tens of milliseconds). \(\tau\) was **not** retuned.

`--estimate` exposes that probe as a feasibility guess with a
**conservative |E| band** (probe fraction ×1.25), a residual-size band,
and a residual regime (`thin` / `fat` / `hollow` / `h0`). Confidence is
`medium` only when \(n\le 400\) and the residual is not near \(\tau\);
otherwise `low`. It is **not** a certificate. `--threads N` caps the
worker pool so 1-thread comparisons with Ripser are possible.

### New combinations of known algorithms

- Collapse then implicit cohomology on the residual (standard idea; our
  collapse implementation is owned).
- Delaunay 1-skeleton + local-radius thicken + RedZeD on that flag
  (`--mode scale`). The complex is **not** VR. **[empirical thicken constant \(\alpha\le 2.25\), I279/I305]**

### Genuinely new algorithmic ideas?

None that we will defend as a new exact-VR theorem. The leftover-adj /
CSR H2 stream and the Euclidean thicken split are **engineering
combinations** of known complexes and known reductions.

### Constant-factor vs regime size

| Kind | Where |
| --- | --- |
| Constant-factor exact H1 | RedZeD vs Ripser on connected \(G_T\): measured \(5\)–\(14\times\) **[empirical]**. vs giotto-ph 0.2.4 (1 thread) the same families are \(\sim 6\)–\(36\times\) **[empirical]**; giotto 4-thread does not close that gap on \(H_1\). Worst-case class unchanged. |
| Better size class, exact | \(H_0\) in \(d\in\{2,3\}\): Kruskal on Delaunay, \(\Theta(n)\) edges **[citation + derivation]**. |
| Better size class, **not** exact VR | `--mode scale`: \(\Theta(n)\)–\(O(n)\) flag of a Delaunay / thicken graph **[derivation of size; empirical topology]**. |
| Approx with a theorem | `--mode sparse` (Sheehy-style greedy net) **[citation]**; owned \(\varepsilon=0.6\) Max **does** thin the flag **[empirical]** (figure-8 \(n=8000\): 381k vs \(C(n,2)=32\)M). Construction is still \(\Theta(n^2)\). |

## Exact vs not exact

| Mode | Complex | Persistence vs Ripser VR\(\le T\) |
| --- | --- | --- |
| `--mode exact --engine auto` | VR\(\le T\) | Match (0 unmatched on the hold suite) **[empirical]** |
| `--mode exact --engine redzed` | VR\(\le T\) | Match **[empirical]** |
| `--mode scale` | Flag of Euclidean Delaunay \(\pm\) local-radius extras | Essential \(H_0/H_1/H_2\) kept on tested families; **finite bars differ** — quantify, do not treat as VR |
| `--mode sparse` | Sparse Rips 1-skeleton | Interleaving-style guarantee in the literature; owned defaults need measured bottleneck |

## What a user should remember

We did **not** beat Ripser’s worst-case VR algebra on a dense connected
graph. We **did** make exact PH practical on more everyday clouds by
picking the cheaper exact engine and a sparse metric, and we **did**
extend low-dimensional Euclidean analysis to tens of thousands of
points by switching complex (and saying so).
