# Remaining directions (exact VR \(H_1\))

This is an audit, not a promise of a new algorithm.

**Original target:** a general \(\sim 10\times\) exact-VR \(H_1\) wall-clock or
algebraic-work win vs Ripser on \(G_T\).

**Current evidence:** that target is **not met**. Live 1-thread leftover
families (`leftover_10x.json`): **3/6 ≥10×**. Circle 31× is collapse, not
pairing. Worst-case \(H_1\) on a connected dense \(G_T\) is still the
Ripser / RedZeD pairing class.

**Consolidation result we do have:** a portfolio + dispatcher + sparse
representations + optional Euclidean scale path. The public interface
does not mention I-numbers. See
[`WHAT_WE_BUILT.md`](WHAT_WE_BUILT.md),
[`PRACTICAL_LIMITS.md`](PRACTICAL_LIMITS.md), and
[`../benchmarks/README.md`](../benchmarks/README.md).

Do **not** treat a leftover skip as a new algorithm. \(\tau\) is frozen.
Do **not** mark the research goal complete on the strength of this file.

## Spent exact-\(H_1\) pairing levers

These were tried, logged, and must not be reopened as micro-opts.

| Direction | Status | Why it is closed |
| --- | --- | --- |
| I202 witness gate / I203 hi-walk early-stop | Selected | Torus reduce 450→172 ms. Further cofacet early-stop is the selected leftover cut. |
| Time-bucket / later-bits / CannotDom (I214/I215) | Reject | Exact or slower; tax on fail path. |
| Empty-seed / Gabriel / unique-diam leftover skips (I272/I273/I255/I265) | Reject | Not exact, or exact with no clock cut. Wall is `ae_seeded` visits, not leftover-coface internals. |
| Seeded XOR / noop (I288) | Reject | Exact; 848≈866 ms. Rare after mid-loop growth. |
| Add-\(R\) / \(D(e)\) memo (I290/I295/I296) | Reject | Slower or invents \(H_1\). |
| rbit layout / always-spatial / ae_prepare fusion (I262/I264/I266) | Reject | Exact; lost the 10× or no cut. |
| Leftover adj/hash on \(\lvert E\rvert>16n\) (I303/I304) | Reject | Fat-thicken insert tax. |
| Owned AE as clock (I242/I243) | Exact, dominated | 12× slower than RedZeD on circle AE. |
| Reduced VR (I224) / EuclideanPH1 | Exact, loses clock | I316 leftover scale: figure8 n=2000 **18 s vs auto 0.15 s**; uniform2/sphere/anisotropic timeout 20 s. Construction, not pairing. kd-tree lunes would need ~100× just to match RedZeD. Closed as a leftover 10× engine. |
| Collapse + RedZeD on residual (I317) | Exact, loses clock | Residual AE is cheap (figure8 reduce 1.1 ms; anisotropic n=8000 8 ms). Collapse is the tax (124 ms–9.3 s). Faster than auto **0/8**. GUDHI collapse is worse (up to 254 s). `--engine collapse-redzed` stays experimental. |
| Young-cap collapse + RedZeD (I318) | Exact, loses clock | Newest-K domination only. **0 unmatched**. Faster than auto **0/8**. DenseTimes n² init (anisotropic n=8000 2.65 s at K=4096) exceeds the AE cut (reduce 1018→427 ms). |
| Fair G_T young-cap + RedZeD (I319) | Exact, loses clock | Same G_T as auto; I156 trim only; no DenseTimes. **0 unmatched**, **0/8** vs auto (`young_cap_fair.json`). anisotropic n=8000 wall 3.79 s vs auto 1.30 s (reduce 1026→435 ms does not pay Graph+trim 1.36 s). Collapse preprocessors closed. |
| SparseDist \(G_T\) on dense leftover (I320) | Exact, loses wall | Reduce ~2.4× (anisotropic n=8000 1026→442 ms) but hash+EdgeList of \(\lvert E\rvert\sim 11\)M exceeds the save (wall 2.05 s / 5.5× vs old 1.22 s / 8.8×). **0 unmatched**. Reverted. |
| k-NN leftover witness mark (I322) | Exact, loses wall | Exact subset of leftover_coface. **0 unmatched**. Faster than auto **1/8** (`knn_mark.json`). Coverage 41%→1.1% (anisotropic n=8000 2.26 vs 1.28 s). Marks at most \(n\cdot C(k,2)\); fat \(\lvert L\rvert\sim n^2\) ⇒ coverage \(O(k^2/n)\). Sparse witness marks closed. |
| Empty-seed non-Delaunay leftover skip (I323) | Exact, no 10× wall | I273 remeasured on leftover-miss. **0 unmatched**, **6/8** faster (`delaunay_skip.json`). leftover_coface \(O(n)\) (anisotropic n=8000 25k / 10.9M) but wall 1.16 vs 1.29 s. Kruskal+leftover walk stays \(\Theta(\lvert E\rvert)\). Euclidean Delaunay leftover skips closed. |
| Leftover∩Delaunay pairing only (I324) | **Not exact** | Skips ae_seeded on non-Delaunay. **642 unmatched** (`delaunay_only.json`: figure8 n=200 4, n=2000 136; uniform2 284; torus 218). Faster by dropping necessary AE. Confirms I272: the leftover walk after keep_singleton is required. |
| Extra Morse / chunk on residual (H04) | Reject early | After collapse, circle remainder is tiny; torus remainder is \(\Theta(n^2)\) and matching is not a 10× lever. |
| Sparse FPS squared-distance | Reject | Same greedy net; no clock cut. Wall is \(\Theta(n^2)\) evaluations. |
| Sparse FPS AABB / axis reject (2D/3D) | Reject | Exact λ; fewer late evals; no clock cut (figure-8 \(n=8000\) 0.72 s, \(n=16000\) 2.51 s). Early insertions + Θ(n²) argmax remain. |
| 3D Lawson bookkeeping (I307–I312) | Exhausted | Cheap locate/insphere skips done. Scale construction wall remains walk+insphere. |

Named leftover follow-ups after I202 are **spent**. That includes
`ae_seeded`, leftover_coface **inner-loop** constants, **sparse
witness marks** (I322), and **Euclidean Delaunay leftover skips**
(I273/I323). I321 shows leftover-miss leftover_coface is \(\sim\lvert E\rvert\).
I323 can drop those *tests* to \(O(n)\) and still leave a \(\Theta(\lvert E\rvert)\)
Kruskal/leftover walk.

## What literature still offers

Search on 2026-10-14 (third pass the same day):

- **RedZeD** (Kapulkin–Kershaw, arXiv:2606.06310) is the current
  published exact-VR alternative to Ripser. We already wrap vendor
  `22ef1bf`. Their paper claims RedZeD faster than Ripser in 21/22
  cases, most clearly in \(H_1\). Our leftover families show a
  **constant-factor** in that class, not a new Big-O, and not a
  general 10× on this box.
- **giotto-ph** is lock-free Ripser + collapse. We compared it at 1
  and 4 threads; it tracks Ripser on \(H_1\).
- **Dory** (`pydory` 1.1.137 oracle, **not vendored**). Live 1-thread
  leftover (`dory.json`): tracks Ripser on leftover \(H_1\) (figure-8
  \(n=2000\) 2.84 vs 2.72 s; torus \(n=1000\) 0.43 vs 0.41 s; circle
  \(n=1000\) 2.79 vs 2.73 s) and is **slower** on sphere \(H_2\)
  \(n=400\) (4.13 vs 1.49 s). 12 s first-fail (`dory_limits.json`):
  circle \(n=2000\) and figure-8 \(n=4000\) timeout **with Ripser**;
  sphere \(H_2\) \(n=600\) Dory timeouts while Ripser still finishes
  (5.3 s) and PITH is 34 ms. Not a 10× class. Literature parallel
  \(\sim 2\times\) does not change the 1-thread pairing class.
- **Oineus** (`oineus` 0.9.39 oracle, **not vendored**). Lock-free
  reduction (Morozov–Nigmetov, SPAA 2020) + in-order VR generation
  (Vejdemo-Johansson–Matuszewski–Bauer, arXiv:2411.05495). Live
  1-thread leftover (`oineus.json`): **slower than Ripser** on every
  finished cell (circle \(n=400\) 1.54 vs 0.13 s; figure-8 \(n=1000\)
  4.68 vs 0.61 s; torus \(n=1000\) 4.27 vs 0.40 s). 20 s timeouts at
  circle \(n=1000\), figure-8 \(n=2000\), uniform2 \(n=2000\), blobs
  \(n=2000\), and sphere \(H_2\) \(n=400\) — all cells Ripser still
  finishes. Sphere \(H_2\) \(n=400\) is **earlier** than Dory (Dory
  4.13 s). Same pairing class; the published win is multi-core, not a
  1-thread 10×. giotto-ph is the same lock-free family already timed
  at 4 threads on \(H_1\) (no win).
- **Dionysus 2.2.3** (explicit `fill_rips` + homology, **not vendored**).
  Live 1-thread leftover (`dionysus.json`): circle \(n=400\) **11.68 s /
  2.38M simplices** vs Ripser 0.18 s (**65× slower**). Every other
  leftover cell timeouts at 20 s while Ripser still finishes. Same
  explicit-complex class as GUDHI Rips. First-fail is **earlier** than
  Oineus.
- **Ripserer.jl** (literature): same Ripser algorithm, usually within
  ~30%. Julia is not on this box. Not a new pairing class.
- **Coperto** (Leitão, arXiv:2602.22784): quotient-cover
  **approximation** with a claimed log-3 interleaving, not exact VR.
  Live (`coperto.json`, `greedy=False`, 1 thread): linear tower, but
  essential \(H_1/H_2\) become finite (figure-8 unmatched 24 vs scale
  0). figure-8 \(n=8000\) 6.74 s vs scale 0.21 s. Default
  `greedy=True` drops all loops. Not a leftover engine. Not vendored.
- **Involuted PH** (Čufar 2023) and **wrapping cycles** (Bauer 2024)
  are representative / geometric papers. They do not change the
  leftover pairing class on a connected fat \(G_T\).
- **Reduced VR** (Koyama–Mémoli–Robins–Turner) is exact \(H_1\) on a
  thinner 2-complex; we already timed it (I224) and lost the clock to
  construction. Not a leftover pairing class.
- No 2026 paper we found claims a better **worst-case** pairing class
  than Ripser/RedZeD on a connected dense flag. `redzed-tda` on PyPI
  is the same RedZeD we already wrap.

## Remaining walls (not “try one more skip”)

| Wall | Why it is still there | What would count as progress |
| --- | --- | --- |
| Leftover empty-seed `leftover_coface` on connected fat \(G_T\) | I321: leftover count **equals** Ripser. I323: leftover_coface on non-Delaunay is skippable (\(O(n)\) tests) but the leftover *walk* stays \(\Theta(\lvert E\rvert)\). I324: dropping that walk (pair leftover∩Del only) **invents bars**. Collapse / SparseDist / sparse-witness / Delaunay-skip / Del-only pairing closed (I315–I324) | A **new pairing algorithm** that finds the seeded leftovers from ActiveReg in \(o(\lvert E\rvert)\) (complexity in \(\lvert R\rvert\)), not a filter that drops ae_seeded. |
| Fat exact \(H_2\) | Default exact-auto is still RedZeD-cc (mixed \(n=300\) 22 ms vs implicit 73 ms; mixed \(n=1000\) 1.07 s vs Ripser 7.25 s). I313 gives `--engine implicit` tet-free Ripser-style H2: mixed \(n=300\) **73 ms / unmatched 0** (the old persist_sparse timeout). Thin collapse residuals stay collapse-dominated (sphere \(n=600\) 31 ms, **139×** vs Ripser). Both exact and Ripser leave a 12 s budget near mixed \(n=2000\) | A faster pairing than RedZeD on a connected fat flag, or `--mode scale` when \(n_{cc}\ge 800\). High-d fat H2 sparse remains refused. Implicit H2 is the Ripser class, not a new Big-O. |
| 3D Lawson + insphere | Expected \(O(n\log n)\) incremental Delaunay; 80k sphere is still walk + predicates | A different 3D location structure, not I307–I312 bookkeeping. |
| Sparse FPS \(\Theta(n^2)\) | Greedy net needs \(\Theta(n^2)\) distance evaluations | An approximate net with a **stated** interleaving change, or a subquadratic exact FPS in low \(d\). Squared-distance and AABB/axis-reject are closed. |

## What would satisfy the original 10× goal

All of the following, together:

1. One exact-VR path, shape-agnostic, 0 unmatched vs Ripser.
2. \(\ge 10\times\) \(H_1\) wall-clock **or** algebraic work vs 1-thread
   Ripser on leftover families **and** on held-out families frozen
   after the dispatcher. Live: frozen pack **3/6**, held-out leftover
   **4/7** (`leftover_heldout.json`), leftover-miss n-series **0/7**
   (`leftover_miss_n.json`; anisotropic 7.4→8.8× after I314, still
   not 10×).
   Post-freeze linked_circles grows 6.6→32.2×; sheared_loops peaks
   9.87× then recedes to 8.53× (`linked_ratio_n.json`, 4/11 ≥10×).
   Post-16× offset_rings grows 15.8→20.6× (`postband.json`, 3/3 timed
   ≥10×; estimate 2/4 — hi_mult not retuned).
3. A complexity justification that is not “circle collapse”.
4. Reproduced on this hardware with `--threads 1`.

We have (1) for `--mode exact`. We do **not** have (2) or (3) as a
general leftover claim.

## What would exhaust the research budget

All of the following, together:

1. Spent table above is complete for leftover / collapse / owned AE /
   reduced VR / extra Morse / FPS sqrt / FPS AABB / 3D bookkeeping.
2. No unpublished pairing algorithm is sitting in-tree unused.
3. Remaining walls require new theory or a different complex
   (already provided as `--mode scale` / `--mode sparse`).
4. Living docs state the 3/6 leftover 10× result and do not claim a
   general exact-\(H_1\) 10×.

(1)–(4) hold for the leftover / collapse / RedZeD / giotto / Dory /
Oineus / Dionysus oracles timed on this box. This is **not** a
completion certificate: a genuinely new pairing idea would reopen the
exact path. Dory tracks Ripser; Oineus and Dionysus are slower than
Ripser at 1 thread. None of them is a 10× engine.

## What a user should do instead of waiting for a general 10×

| Need | Command |
| --- | --- |
| Exact VR barcode | `--mode exact` |
| Probe chooses exact / scale / sparse | `--mode auto` |
| Large Euclidean \(d\in\{2,3\}\), essential topology | `--mode scale` |
| Feasibility before the expensive run | `--estimate --format json` |
| High-d \(d\ge 4\) \(H_1\) | `--mode exact` or `--mode auto` (auto stays exact unless sparse is clearly cheaper) |
