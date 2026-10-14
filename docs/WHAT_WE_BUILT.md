# What we actually built

This is a precise account of what PITH is after the consolidation
campaign. It is **not** a claim that we found a new worst-case
persistent-homology algorithm. Claims are tagged **[citation]**,
**[derivation]**, or **[empirical]**. Iteration numbers live in
[`RESEARCH_LOG.md`](../RESEARCH_LOG.md). Complexity details:
[`COMPLEXITY.md`](COMPLEXITY.md).

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

- Spatial / hash \(G_T\) instead of a dense lower triangle when the cloud is hollow **[empirical]**.
- Growing adjacency for leftover cofaces and H2 streaming when \(\lvert E\rvert\le 16n\) **[derivation: \(O(\lvert E\rvert\deg)\) vs \(O(\lvert E\rvert n/64)\)]**.
- Walk-locate 2D/3D Delaunay construction (Bowyer–Watson, no cavity-slot reuse) **[derivation: expected \(O(n\log n)\) incremental Delaunay under standard location]**.

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
(phase 2) and **11/11** on `eval_mode_auto.py` (10 execute + 1 refuse).
Fat \(H_2\) on \(d\notin\{2,3\}\) is an exception: the probe still names
`sparse`, but auto **refuses** (exit 3, `auto_will_run=false`) because
that path timed out at 25 s on held-out `uniform4` \(n=250\) (same refuse
on `uniform10` \(n=250\)). Explicit `--mode sparse` is unchanged. Engine
choice inside exact can still be wrong (phase-3 oracle **5/9**; waste
1.3–2.75×, tens of milliseconds). A post-freeze high-d control
(`uniform10` \(n=4000\), \(T=1.8\)) used to mark exact infeasible and run
sparse in 18 s vs exact 0.65 s (**28×**). `--mode auto` now compares the
exact vs sparse clock models and **stays on exact** when scale is
unavailable and sparse is not clearly cheaper (live auto 0.74 s)
**[empirical, uniform10.json]**. A later held-out sweep
(`highd_auto.json`) is **0/8** wrong on uniform5/6/7/8 and L1 \(d=4\).
\(\tau\) / engine_rec were **not** retuned. Fat \(H_2\) refuse on
\(d\notin\{2,3\}\) is unchanged. Euclidean fat \(H_2\) no longer uses
the blunt \(n\ge 200\) cutoff: `--estimate` measures the largest
T-component \(n_{cc}\) and marks exact impractical at \(n_{cc}\ge 800\)
or a dense flag (`edge_frac≥0.5`, \(n_{cc}\ge 600\)). Leftover \(H_1\)
`--mode auto` no longer jumps to scale on a fat residual just because
`|E|>8e6` or \(n>6000\) when `est_exact≤4` s (anisotropic / grid_holes
\(n=8000\) stay exact). Hollow leftover with `|E|>8e6` still goes to
scale — that clock lies on figure8 \(n=16000\) **[empirical,
leftover_miss_dispatch.json; eval_mode_auto 11/11]**. Held-out
`ncc_auto.json` (seed 11): **0/11** timeout misses after that clause
(complete sphere \(n=700\) T=2.5 was the miss that forced it). Mixed
\(n=300\) is exact RedZeD-cc at 33 ms; mixed \(n=2000\) goes to scale. The old mixed \(n=300\) “exact timeout” was forced
`--engine implicit` tet enumeration; implicit now uses RedZeD for H2
when \(\lvert E\rvert>16n\) or \(\Delta>24\) (53 ms, unmatched 0)
**[empirical, fat_h2.json]**. Held-out seed-17 `adversarial.json`:
**0/11** timeout misses, **0/8** exact-vs-Ripser mismatches.
Post-freeze seed 23 (`postfreeze.json`): **0/10** timeout misses;
one thin-circle `|E|>8e6` scale miss (nonuniform_circle \(n=6000\),
exact 5.67 s) is now overridden when the thin leftover H1 clock is
under 4 s **[empirical]**.

`--estimate` bands cover **82/82** scored recommended-mode walls
(`eval_estimate.py`, leftover / post-freeze packs included)
**[empirical]**. Leftover \(H_1\) at \(n\ge 2000\) uses a 16× hi band
so pairing explosions stay inside it; mid / mode_rec / τ unchanged.
Hollow leftover \(H_1\) still uses a 6× hi band. Mixed \(n=300\) exact
matches Ripser (unmatched 0, 355 bars) **[empirical]**. `--estimate` exposes that probe as a feasibility guess with a
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
| Constant-factor exact H1 | RedZeD vs Ripser on leftover-wall families: live 1-thread \(5.8\)–\(17\times\), **3/6 ≥10×** at the frozen sizes (`leftover_10x.json`) **[empirical]**. Ratio vs n (`leftover_ratio_n.json`): sphere H1 crosses 10× near \(n=4000\) (11.4×); uniform2 is still **9.1×** at \(n=7000\) (RedZeD’s own weak unit-square case); figure8 plateaus ~16× once both engines explode (\(p\approx 6\)). Held-out leftover families (`leftover_heldout.json`, seed 19): **4/7 ≥10×** after dropping collapse walls. Leftover-miss n-series (`leftover_miss_n.json`): anisotropic 5.3→6.0→8.8→6.6× and grid_holes 3.0→5.0→6.1×, **0/7 ≥10×** (ratio can recede when the representation flips). Post-freeze leftover n-series (`linked_ratio_n.json`): linked_circles 6.6→13.7→32.2× (**grows**); sheared_loops 2.93→9.87→8.53× (peaks just under 10× then recedes; **never ≥10×**). Pack **4/11 ≥10×**. | vs giotto-ph 0.2.4 (1 thread) the same families are \(\sim 6\)–\(36\times\) **[empirical]**; giotto 4-thread does not close that gap on \(H_1\). Dory (`pydory` 1.1.137, 1 thread) **tracks Ripser** on leftover \(H_1\) (Ripser/Dory \(0.90\)–\(1.00\)) and is slower on sphere \(H_2\) \(n=400\): 4.13 vs 1.49 s **[empirical, dory.json]**. 12 s first-fail matches Ripser on leftover \(H_1\) and is **earlier** on sphere \(H_2\) (\(n=600\)) **[empirical, dory_limits.json]**. Oineus 0.9.39 (1 thread) is **slower than Ripser** on leftover \(H_1\) (7.7–11.7×) and times out earlier, including sphere \(H_2\) \(n=400\) **[empirical, oineus.json]**. Dionysus 2.2.3 is explicit VR: circle \(n=400\) 11.68 s / 2.38M simplices vs Ripser 0.18 s (**65× slower**); later leftover cells timeout **[empirical, dionysus.json]**. Dory / Oineus / Dionysus are not vendored. Worst-case class unchanged. |
| Better size class, exact | \(H_0\) in \(d\in\{2,3\}\): Kruskal on Delaunay, \(\Theta(n)\) edges **[citation + derivation]**. |
| Better size class, **not** exact VR | `--mode scale`: \(\Theta(n)\)–\(O(n)\) flag of a Delaunay / thicken graph **[derivation of size; empirical topology]**. |
| Approx with a theorem | `--mode sparse` (Sheehy-style greedy net) **[citation]**; owned \(\varepsilon=0.6\) Max **does** thin the flag **[empirical]** (figure-8 \(n=24000\): 1.56M edges / 5.56 s / ess \(H_1=2\)). Euclidean `--points` skip the n×n store; FPS is still \(\Theta(n^2)\) (local \(p\approx 2\)) **[derivation + empirical]**. Coperto 0.1.7 (Leitão arXiv:2602.22784) is another theorem-backed path (log-3 interleaving) **[citation]**; live leftover/accuracy (`coperto.json`) shows linear tower but **lost essential** \(H_1/H_2\) vs VR, and it loses the Euclidean clock to `--mode scale` **[empirical]**. |

## Exact vs not exact

| Mode | Complex | Persistence vs Ripser VR\(\le T\) |
| --- | --- | --- |
| `--mode exact --engine auto` | VR\(\le T\) | Match (0 unmatched on the hold suite) **[empirical]** |
| `--mode exact --engine redzed` | VR\(\le T\) | Match **[empirical]** |
| `--mode scale` | Flag of Euclidean Delaunay \(\pm\) local-radius extras | Essential \(H_0/H_1/H_2\) kept on tested families; **finite bars differ** — quantify, do not treat as VR |
| `--mode sparse` | Sparse Rips 1-skeleton | Interleaving-style guarantee in the literature **[citation]**; owned ε=0.6 Max: ess \(H_1\) usually kept; \(n=400\) bn \(H_1\approx 0.006\)–\(0.028\) on 2D loops, \(W_1\approx 0.023\)–\(0.059\); `nested_loops` \(W_1\approx 1.05\) **[empirical, sparse_limits.json]** |

## What a user should remember

We did **not** beat Ripser’s worst-case VR algebra on a dense connected
graph. We **did** make exact PH practical on more everyday clouds by
picking the cheaper exact engine and a sparse metric, and we **did**
extend low-dimensional Euclidean analysis to tens of thousands of
points by switching complex (and saying so).

The public interface is `--mode exact|scale|sparse|auto`, `--engine
auto|redzed|implicit`, `--estimate`, and `--threads`. Iteration numbers
and `run_wave*.py` are the research ledger (`benchmarks/README.md`).

Spent leftover / pairing micro-opts and the remaining walls are listed
in [`REMAINING.md`](REMAINING.md). A general exact-\(H_1\) 10× is **not**
claimed.
