# Remaining directions (exact VR \(H_1\))

This is an audit, not a promise of a new algorithm.

**Original target:** a general \(\sim 10\times\) exact-VR \(H_1\) wall-clock or
algebraic-work win vs Ripser on \(G_T\).

**Current evidence:** that target is **not met**. Live 1-thread leftover
families (`leftover_10x.json`): **3/6 ≥10×**. Circle 31× is collapse, not
pairing. Worst-case \(H_1\) on a connected dense \(G_T\) is still the
Ripser / RedZeD pairing class.

**Consolidation result we do have:** a portfolio + dispatcher + sparse
representations + optional Euclidean scale path. See
[`WHAT_WE_BUILT.md`](WHAT_WE_BUILT.md) and
[`PRACTICAL_LIMITS.md`](PRACTICAL_LIMITS.md).

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
| Reduced VR (I224) | Exact, loses clock | \(O(n^2)\) triangles; construction loses. |
| Extra Morse / chunk on residual (H04) | Reject early | After collapse, circle remainder is tiny; torus remainder is \(\Theta(n^2)\) and matching is not a 10× lever. |
| Sparse FPS squared-distance | Reject | Same greedy net; no clock cut. Wall is \(\Theta(n^2)\) evaluations. |
| 3D Lawson bookkeeping (I307–I312) | Exhausted | Cheap locate/insphere skips done. Scale construction wall remains walk+insphere. |

Named leftover follow-ups after I202 are **spent**. That includes
`ae_seeded` inner-loop constants. Visiting leftovers on a connected fat
\(G_T\) is the pairing work RedZeD already pays.

## What literature still offers

Search on 2026-10-14:

- **RedZeD** (Kapulkin–Kershaw, arXiv:2606.06310) is the current
  published exact-VR alternative to Ripser. We already wrap vendor
  `22ef1bf`. Their paper claims RedZeD faster than Ripser in 21/22
  cases, most clearly in \(H_1\). Our leftover families show a
  **constant-factor** in that class, not a new Big-O, and not a
  general 10× on this box.
- **giotto-ph** is lock-free Ripser + collapse. We compared it at 1
  and 4 threads; it tracks Ripser on \(H_1\).
- **Dory** (`pydory` 1.1.137 oracle, **not vendored**). Live 1-thread
  (`dory.json`): tracks Ripser on leftover \(H_1\) (figure-8 \(n=2000\)
  2.84 vs 2.72 s; torus \(n=1000\) 0.43 vs 0.41 s; circle \(n=1000\)
  2.79 vs 2.73 s) and is **slower** on sphere \(H_2\) \(n=400\) (4.13
  vs 1.49 s). PITH exact is \(16\)–\(39\times\) faster than Dory on
  those cells. Not a 10× class. Literature parallel \(\sim 2\times\)
  does not change the 1-thread pairing class.
- No 2026 paper we found claims a better **worst-case** pairing class
  than Ripser/RedZeD on a connected dense flag.

## Remaining walls (not “try one more skip”)

| Wall | Why it is still there | What would count as progress |
| --- | --- | --- |
| Leftover `ae_seeded` on connected fat \(G_T\) | Output-sensitive AE / implicit reduce on \(\lvert R\rvert\sim\lvert E\rvert\) | A **new pairing algorithm** with a stated complexity in \(\lvert R\rvert\), or a theorem that most leftovers are skippable **without** inventing bars. Not another inner-loop flag. |
| Fat exact \(H_2\) | Tet tax; mixed 1D/2D/3D \(n=300\) times out | Lower \(T\), `--maxdim 1`, or `--mode scale` in \(d\in\{2,3\}\). Auto already refuses fat \(H_2\) sparse outside 2D/3D. |
| 3D Lawson + insphere | Expected \(O(n\log n)\) incremental Delaunay; 80k sphere is still walk + predicates | A different 3D location structure, not I307–I312 bookkeeping. |
| Sparse FPS \(\Theta(n^2)\) | Greedy net needs \(\Theta(n^2)\) distance evaluations | An approximate net with a **stated** interleaving change, or a subquadratic exact FPS in low \(d\). Squared-distance FPS is closed. |

## What would satisfy the original 10× goal

All of the following, together:

1. One exact-VR path, shape-agnostic, 0 unmatched vs Ripser.
2. \(\ge 10\times\) \(H_1\) wall-clock **or** algebraic work vs 1-thread
   Ripser on leftover families **and** on held-out families frozen
   after the dispatcher.
3. A complexity justification that is not “circle collapse”.
4. Reproduced on this hardware with `--threads 1`.

We have (1) for `--mode exact`. We do **not** have (2) or (3) as a
general leftover claim.

## What would exhaust the research budget

All of the following, together:

1. Spent table above is complete for leftover / collapse / owned AE /
   reduced VR / extra Morse / FPS sqrt / 3D bookkeeping.
2. No unpublished pairing algorithm is sitting in-tree unused.
3. Remaining walls require new theory or a different complex
   (already provided as `--mode scale` / `--mode sparse`).
4. Living docs state the 3/6 leftover 10× result and do not claim a
   general exact-\(H_1\) 10×.

(1)–(4) hold for the leftover / collapse / RedZeD / giotto / Dory
oracles timed on this box. This is **not** a completion certificate:
a genuinely new pairing idea would reopen the exact path. Dory is
now timed at 1 thread and is not a 10× engine.

## What a user should do instead of waiting for a general 10×

| Need | Command |
| --- | --- |
| Exact VR barcode | `--mode exact` |
| Probe chooses exact / scale / sparse | `--mode auto` |
| Large Euclidean \(d\in\{2,3\}\), essential topology | `--mode scale` |
| Feasibility before the expensive run | `--estimate --format json` |
