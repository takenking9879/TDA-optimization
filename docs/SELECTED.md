# Selected algorithm (living)

Updated 2026-10-14 after iterations I001–I312 plus consolidation (phase 3).
**Stable CLI:** `--mode exact|scale|sparse`, `--engine auto|redzed|implicit`,
`--estimate`, `--threads N`, `--mode auto`. Auto-dispatch probes at \(n\ge 64\).
`--estimate` marks fat `maxdim≥2` residuals as exact-infeasible.
`--mode auto` follows that recommendation (phase-2 8/8; phase-3 post-freeze 9/9 vs probe).
Engine oracle on new held-out families is **5/9** (do not retune \(\tau\)).
Equal-hardware: PITH `--threads 1` still beats Ripser, giotto-ph 0.2.4
(`n_threads=1` and `4`), and GUDHI 3.13 Rips on the measured suite.
`--estimate` reports empirical `growth_p` and a runtime band; τ is frozen.
`--mode sparse` (ε=0.6 Max) thins the flag (figure-8 \(n=8000\): 381k vs 32M pairs)
but still builds a dense metric. An earlier note that \(\lvert E\rvert=C(n,2)\)
confused the `distances` counter with `edges_in`.
Iteration numbers stay in this file and `RESEARCH_LOG.md`.
**CLI default `--engine`
auto` (I235+I236+I239+I240+I241+I263+I270+I271+I275):** subsample residual-frac dispatch,
plus I263 edge-frac so hollow/manifold clouds take RedZeD. Fat →
RedZeD (torus n=2000 **13.0×**). Thin-circle → collapse+implicit
(n=1000 **28×**; n=4000 still **140×**). Mixed figure8 n=4000 T=1.1
**27× / 1.07 s** spatial. Disconnected G_T → spatial UF
+ parallel RedZeD per component (blobs n=4000 **24×**). **H0** is Kruskal; **I271** 2D and **I275** 3D
walk-locate Delaunay (MST ⊆ Delaunay) so H0 does not list G_T — blobs n=12000
**218× / 0.027 s**, n=25000 **515× / 0.055 s** (I284), sphere n=16000 **147× / 0.112 s**,
n=30000 **288× / 0.221 s** (I285), n=50000 **367 ms**. **H2:** τ=0.15 so sphere void stays collapse
(**58×** at n=400; **527× / 56 ms** at n=800 — I281). Shape-agnostic, 0 bars lost. Circle 140× is a
collapse-friendly regime, **not** the success criterion.

## Success criteria (goal amendment)

The final algorithm must be **shape-agnostic**: one path for real data with
mixed homology, not a circle/sphere/torus special case. It must target
**better Big-O than Ripser VR**, not only a 10× constant-factor win, and
**preserve as much topology as possible**. Complexity claims need a
justification (residual \(|E'(n)|\) slopes, column counts, or a different
complex with a proven size bound). Any information loss vs exact VR must be
quantified (unmatched bars / bottleneck / interleaving).

Current honest status: **`--engine auto` (I235+I236+I238+I239+I240+I241+I263+I270+I271+I275)** is
shape-agnostic (0 unmatched) and picks the better exact engine from a
250-point collapse probe plus I263 edge-frac. H1 τ=0.04; H2 τ=0.15;
hollow edge-frac <0.25 → redzed. Torus n=2000 H1 **13.0×**;
circle n=1000 **28×**; mixed figure8 n=4000 **27× / 1.07 s**.
Disconnected clouds (blobs) **24×** at n=4000 via I239 split +
I240 spatial metric. **H0 is a better size+construction class** in
d=2,3: Θ(n) Delaunay edges, expected O(n log n) walk (blobs n=12000
**218× / 0.027 s**; sphere n=16000 **147× / 0.112 s**;
sphere n=30000 **288× / 0.221 s** — I285).
**Worst-case H1 Big-O is not improved** on a connected G_T — that
part is still a portfolio, not a new complexity class.
Torus residual stays \(\Theta(n^2)\) (I204). Connected uniform2
n=5000 H1 is **11.2×** (0.33 s). Sphere n=2000 H1 **10.1×**.
Sparse n=20000 **5.6×** (1.11 s, 4.71M vs 200M).
**I228 `--engine redzed`** (with I239/I240 split) remains the
single-engine general exact path. **I242 `--engine active`** is exact H1 AE (I236 pairing bug fixed)
but loses to RedZeD (circle n=500 0.06×; uniform2 n=1000 0.33×).
Topology loss: **0**. **I224 reduced VR** is exact with \(O(n^2)\)
triangles but loses clock. The **optional** `--sparse-eps 0.6` path keeps
essential \(H_1\) and sits in a better size class (I218) at quantified
bottleneck 0.005–0.034.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + I182 live-bit AND generate-C + I186 no LiveAdj +
**I193 multi-apex AND-eq** + **I197 any_later C_now AND-eq** + **I202
`|C_now|≥32` witness rescan**; I189 is the first no-later candidate) →
**Ripser-heap implicit cohomology** on the residual (I137) with **I203
hi-walk early-stop** after the zero-pivot / emergent pair.
`--collapse-alg back` is this stack. `back-src` is the pre-I182 star walk.

- \(H_0\): Kruskal. **I271** walk-locate 2D Delaunay when n∈[256,100000];
  **I275** walk-locate 3D Delaunay when n∈[256,50000] (MST ⊆ Delaunay;
  Θ(n) edges, expected O(n log n) construction; I274 scan is fallback;
  I284 2D n=25k **515×**; I285 3D n=30k **288×**).
  `--collapse -1` **skips collapse** when `maxdim=0`.
- \(H_1\): leftover (non-MST, non-apparent) edges, youngest-first; F₂ heap
  coboundary; oldest remaining pivot; same-diameter apparent/emergent;
  V-matrix re-enumeration. **I293** parallel first-pass apparent when
  leftover≥4096. `--engine auto` **is implicit** (I137).
- \(H_2\): tet-boundary homology fallback on the residual (thin after collapse).

**Fidelity:** exact \(\mathrm{VR}_{\le T}\) vs Ripser `01add51` on the I044–I098
suite and I137 8/8 (including dense circle80/200 **collapse=0**, the I045 killer).

**Rejected this wave (exact but not better, or wrong)**

| Lever | Why |
| --- | --- |
| Bitset neighborhood AND (I071–I081) | Exact; **slower** (circle2000 collapse 5.8 s vs 2.6 s) |
| Leftover-as-cohomology (I045–I046, I094, I111, I126) | Wrong pivot (youngest cofacet) + equilateral-only apparent; ~1 bar/leftover on dense \(G_T\) |
| Time-axis D&C (I088) | Parallel schedule, not less sequential work |
| High-d skip (I055) | Skip+homology 0.005× vs Ripser |
| Reduced-VR prototype (I056) | Finite \(H_1\) **count** wrong — zero-persistence bars; I224 engine is exact |
| Sheehy sparse (I057) | Not exact VR |
| Progressive ∩ / maxdeg / budget+homology (I102–I107) | Exact or thicker residual; all slower **while residual was persist_sparse** |
| Sequential Tm scan (I131) | Exact; slower |
| `-march=native -flto` (I128) | Exact; **slower** than `-O3` |
| Fake RedZeD (I122–I125) | Still enumerated all leftover triangles |
| Hybrid first-apex + progressive (I145) | Exact; **slower** (circle3000 6.90× vs 8.11×) |
| Sorted-merge C (I146) | Exact; **slower** (circle2000 4.43× / 6.3 s vs 6.30× / 4.2 s) |
| AVX-512 `dominated_by` (I147) | Exact; **no collapse_ms win** (gather latency) |
| Prefetch C-walk (I158) | Exact; **slower** (circle2000 3912 vs 3746 ms) |
| Vertex-sorted stars (I159) | Exact; **slower** (circle2000 3843 vs 3746 ms) |
| SoA live adjacency (I160) | Exact; **slower** (circle2000 3872 vs 3746 ms) |
| Integer grades (I161) | PH match but **under-collapse** (circle2000 1.07M vs 5169 residual) |
| Matching-batch parallel | **Unsafe** (shared common neighbors change deg + Tm) |
| Forward 2020 collapse (I149) | **Not exact** (over-collapse; circle80 unmatched 4). Also slower |
| Time-axis D&C impl (I150) | PH match on n≤200; **fails** n=2000/3000 (19–25 unmatched). No clock win |
| Forward at current grade (I152/I154) | Exact (same residual as backward). **Slower** (circle2000 6.8 s vs 4.3 s) |
| Oldest 6n / suffix-back 6n (I165/I166) | **Not exact** at n=2000 (222 unmatched; over-collapse 4059 vs 5169) |
| suffix-stab / suffix-rescue as default (I168–I172) | Exact **41.7× / 36.5×** on circle n=2000; **2 unmatched** at n=3000/4000 |
| suffix-k K-sample (I174) | K=0 exact, no clock win. K=2 fast but wrong. K=32 exact at n=3000, 4% probe cut |
| Skip-collapse + implicit (I175) | Exact; **slower** than collapse=1 and than Ripser on every I162 family |
| suffix-later Case B other-star (I178) | K=8 exact at n=3000; other-star scan kills the I176 13.4× |
| kept-later Case B leave (I180) | Exact at n=4000 K=2 (9.08×) and n=3000 K=8 (7.78×); leave-cascade kills the 16.9× |
| escalate-until-keep (I181/I183) | n=3000 still 2 unmatched (8325). Early leave turns escalate off |
| Progressive word-AND on fused-fail (I191) | Exact; **slower** on losers (blobs 809→1309 ms). Full ∩ cannot early-abort trims |
| Sticky vertex-dominator (I194) | Exact; **no clock win** (sphere 357→459 ms discovery tax). Static G_T frac ≠ grade-t hits |
| AND-eq at shift grades (I198) | Exact; torus **1771→2816 ms**. later[] masks dwarf Tm |
| Adaptive bits/Tm shift (I199) | Exact; **no clock win** (torus 1865 vs 1771) |
| Ungated I201 witness rescan | Exact; torus 1771→1463 ms but blobs 178→235 ms |
| Shift obstruction resume (I214) | Exact 5/5; torus **1714 vs 1470 ms**. 1.22M skips, mark-every-fail tax |
| Sticky-only obstruction (I215) | Exact 5/5; torus 1544 ms, blobs **227 vs 190**. Reverted from default |
| Lazy witness ν=1 (I216) | Invents essential H1 on every family (torus 14 vs 2; bn 0.05–0.48) |
| Lazy witness ν=0 (I217) | torus ess OK but bn 0.64; circle1000 drops a loop; others invent |
| Killer-first dominated_by (I219) | Exact 5/5; 17% torus hits; collapse 1474≈1470; sphere 388 vs 365. Reverted |
| kNN flag K=16/32 (I220) | Invents torus H1 at K=32 (bn 0.36); K=16 invents many loops. Fast but unsafe |
| kNN K=128 (I221) | Ess H1 6/6, torus bn 0.003, but 6.6× / 139k vs sparse 17.8× / 91k. Dominated |
| GIC kNN quotient (I222) | Invents ess H1 on blobs/sphere/torus (8 vs 1, bn 0.36). Fast, wrong features |
| High-deg prefix-8 (I223) | Exact 5/5; torus 1537 vs 1470 ms. Fail-path tax. Reverted |
| Reduced VR as default (I224) | **Exact H1** on 19/19 mixed rows (unit square, figure8, two_circles, …). Triangles \(n^{2.04–2.20}\). Construction loses clock (circle n=500 2.65s vs Ripser 0.31s). Keep `--reduced-vr` experimental |
| Reduced VR lune walk (I224 path) | I225 all-pairs is **2.7×** faster construction, still exact; still slower than Ripser (circle n=500 0.73s / 0.42×) |
| Witness-shrink first_dominator (I226) | Exact 5/5; torus tests 12.5M→9.0M / 6.1M skips; collapse **1450 vs 1470** ms. Circle 275 vs 263. Reverted |
| Live leftover-star generation (I233) | **Not exact** on real clouds (invents H1). Unit square held. Reverted |
| Leftover-coface AE (I236) | **Not exact** (figure8 unmatched 12; essentials held). First-hit `process_leftover` / empty-R abort skipped later same-diameter deaths. Reverted. I242 pairing is exact |
| Birth-time leftover-coface AE (I237) | **Not exact** — same unmatched counts as I236. Incremental insert did not change the barcode. Reverted. I242 pairing is exact |
| Vendor-faithful owned AE as clock (I242) | **Exact 13/13** (figure8 2=2; sphere void 1=1). **Slower** than RedZeD (circle n=500 0.06×; uniform2 n=1000 0.33×). Keep `--engine active` experimental |
| rbit owned AE as clock (I243) | **Exact 11/11.** Circle AE 0.38→0.26 s (~1.5× vs I242) still **0.08×** vs RedZeD. Probe count unchanged (leftover-star). Default unchanged |
| Fill-collect + std::sort EdgeList (I244 try) | Exact; **slower** metric (10→460 ms on uniform2 n=5000). Vendor `build_edges` stays |
| leftover-coface fast (I247) | Exact 11/11; **slower** (uniform2 n=5000 9.24× / 279 ms vs I246 9.56× / 264 ms). Reverted |
| Fuse fill + histogram (I248) | Exact 11/11; **slower** (metric 10→46 ms; 8.40× vs I246 9.56×). Reverted |
| Parallel leftover-coface precompute (I249) | Exact 11/11; pith **unchanged** (0.353≈0.354 s). Apparent 10.05× was Ripser 3.55 vs 3.38 s. n=6000 slower. Reverted |
| H1 coface_ready specialize (I253) | Exact 15/15; **no pith cut**. Wave n=5000 0.36s was noise (standalone reduce 207≈I252 206 ms). n=8000 **11.9×** / 0.59 s. Reverted |
| Empty-act skip-prepare (I254) | Exact 15/15; **no pith cut** (n=5000 0.31≈I252 0.30 s; n=8000 10.8× / 0.63 s). Reverted |
| Unique-diam leftover-coface (I255) | Exact 14/14 (lemma: unique edge diams ⇒ leftover-coface ≡ nonempty rbit AND). **No pith cut** (n=5000 reduce 211 vs I252 206 ms). Profile: 3.45M leftovers, first common neighbor always decides, 1309 misses have 0 neighbors. Reverted |
| GUDHI 3.13 explicit Rips (I237) | Exact 7/7; **slower** (blobs n=1000 15.9 s / 17.8M simplices vs auto 21 ms) |
| Gabriel leftover skip (I272) | **Not exact.** n=256 H1 invented ess 31 vs 0 and dropped finite 37 vs 68. Non-Gabriel leftovers still reduce in AE (not all leftover_coface). Reverted. Do not retry. |
| Empty-seed non-Delaunay leftover skip (I273) | **Exact 13/13** but **no clock cut**. figure8 n=4000 reduce **864≈866 ms**. Wall is ae_seeded, not empty-seed leftover_coface. Reverted. Do not retry empty-seed geometric skips. |
| Equal-set seeded_is_noop (I288) | **Exact 10/10.** figure8 n=4000 reduce **848≈866 ms**. `{A} XOR {A}` skip is valid and rare after mid-loop growth. Reverted. Do not retry seeded XOR/noop constants. |
| Grade-t rbit apparent (I289) | Implicit collapse=0 exact (unit tests; same 892 cols). figure8 n=4000 **24424≈25463 ms**. Apparent probes 64M→3.2M; wall is 103M cofacet probes on surviving columns. Reverted. Do not retry as a clock lever. |
| Implicit R-column cache (I290) | collapse=0 exact but **27.7 s vs 24.5 s**. collapse=1 invented H1 (figure8 ess1 117 vs 2; circle 12 vs 1). Emergent \(R\) is only the pivot; dump of fat \(R\) is slower than re-walking \(V\). Reverted. Do not retry add-\(R\) without full \(D(e_j)\) on emergent. |
| Thicken-collapse (I291) | Flag identity held (figure8 n=2000 exact H1, 256-pt circle 2857→256). **Slower** at n≥4000: figure8 n=8000 1.16 vs 0.43 s; n=16000 collapse 4.05 s. Reverted. Do not collapse thicken at scale. |
| Thicken cell skip (I292) | Same edges as I286. No pith cut (figure8 n=16000 1.03≈1.01 s). Keep as correct range query. Persist on the thicken is the wall (sphere n=16000 reduce 3.46 s / 2.28M). |
| Parallel thicken scan (I294) | Same edges. Metric 1131→955 ms; pith 4.12→3.95 s. Keep. Reduce (2.96 s / 199k cols) remains the wall. |
| R-cache + full emergent (I295) | Collapse=1 exact (I290’s invent-H1 fixed). **Slower** thicken (sphere n=16000 5.26 vs 3.95 s). Reverted. Do not retry add-\(R\). |
| D(e) coboundary memo (I296) | Exact collapse=0/1. figure8 n=4000 collapse=0 still **25.6 s / 103M probes**. Adds are unique apparent-facet edges. Reverted. Do not retry \(D(e)\) memo. |
| Reuse-Delaunay split (I298) | Same edges as I297. Keep one walk. Metric 916→905 ms; pith 3.08≈3.02 s. Not a selected pith lever. |
| RCM-on-thicken (I299) | Exact (same edges / ess). figure8 n=16000 reduce 195→164 ms but pith **0.67 vs 0.62 s**. Sphere 16k **3.20 vs 3.08 s**. Reverted. Do not retry bandwidth/Morton orders on thicken. |

I107 (`--dom-budget 1`) **still rejected** with implicit (I142–I144): thicker
residual makes collapse *and* reduce slower (circle3000 1.49× vs full 8.11×).

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
| sphere | \(H_2\) | 500 | 1.4 | **59×** (I085) / 46× later |
| sphere | \(H_2\) | 400 | 1.4 | **61×** I236 auto-collapse (1.05s/0.017s). I235 τ=0.04 would RedZeD at 3.1× |
| sphere | \(H_2\) | 600 | 1.4 | **136×** I237 auto-collapse (4.41s/0.032s); **54×** vs RedZeD |
| circle_noisy | \(H_1\) | 4000 | 1.5 | **140×** I196 I193 (301s/2.15s, collapse 1824 ms). I190 first-apex was 113× |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **119×** I196 I193 (118s/0.99s, collapse 812 ms). I189 was 93.2× |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **84.4×** I202 (28.6s/0.34s, collapse 263 ms). I197 was 83.5× / 249 ms |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **33.8×** I200 I197 (10.6s/0.31s). I162 was 4.13× |
| blobs | \(H_1\) | 2000 | 1.0 | **1.77×** I202 (collapse 190 ms). I197 was 1.85× / 178 ms |
| sphere | \(H_1\) | 2000 | 1.4 | **1.84×** I202 (collapse 365 ms). I197 was 2.03× / 334 ms |
| uniform2 | \(H_1\) | 2000 | 0.35 | **2.10×** I200 (was I162 0.30×) |
| torus | \(H_1\) | 2000 | 1.6 | **1.52×** I203 (1.68s/2.55s, collapse 1470 ms, reduce 172 ms). I202 was 1.31× / 1512 ms collapse / ~450 ms reduce |
| torus | \(H_1\) | 1000 | 1.6 | **1.63×** I200 (was I139 1.31×) |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**I227/I228 RedZeD** vs Ripser, same clouds (I228 in-tree times):

| Dataset | n | T | vs Ripser | vs PITH default | ess H1 |
| --- | --- | --- | --- | --- | --- |
| circle_noisy | 2000 | 1.5 | **33.4×** | 0.45× (PITH still faster) | 1=1 |
| torus | 2000 | 1.6 | **11.7×** | **7.5×** | 1=1 |
| sphere | 2000 | 1.4 | 6.9× | 3.6× | 0=0 |
| blobs | 2000 | 1.0 | 4.9× | 3.0× | 0=0 |
| uniform2 | 2000 | 0.35 | 4.5× | 2.4× | 0=0 |

**Not claimed:** H1 10× clock in general; high-d; **worst-case / all-shape Big-O
better than Ripser**. Topology loss on the default path is **zero** (exact
VR≤T vs Ripser on I204's 25/25 including figure8, two_circles, annulus,
swiss, blobs3d). swiss n=400 is **0.91×** — collapse can lose on thin graphs.

**Honest H1>10× (exact, no oracle, default path):** circle n=4000 T=1.5
**140×** (I196), n=3000 **119×**, n=2000 T=1.5 **84.4×** (I202) / **79×**
(I204 remasure). These are **not** a general or asymptotic claim.

### Complexity (I204, n=500…2000, fixed T)

| Family | \(E \sim n^{}\) | residual \(E' \sim n^{}\) | \(E'/E\) at n=2000 | PITH time \(n^{}\) | Ripser time \(n^{}\) |
| --- | --- | --- | --- | --- | --- |
| circle | 2.00 | **1.22** | 0.48% | 2.22 | **3.25** |
| blobs | 2.00 | **1.10** | 0.94% | 2.16 | 2.25 |
| sphere | 2.00 | **0.91** | 0.68% | 2.22 | 2.20 |
| uniform2 | 1.99 | **1.04** | 1.08% | 2.14 | 2.14 |
| torus | 2.01 | **2.08** | **34%** | 2.97 | 2.95 |

Justification: collapse-friendly residuals are ~\(O(n)\), so reduce is cheap;
input \(G_T\) is still \(\Theta(n^2)\) and collapse walks it, so wall-clock
stays \(\sim n^{2.2}\) except torus \(\sim n^3\). Circle's 10×–80× is the
**exponent gap** vs Ripser \(n^{3.25}\), not a better worst-case class.
Torus residual is \(\Theta(n^2)\) — **no general Big-O win**.

**Alpha (I205, n=1000 / extras):** other complex. Fast (5–397× vs Ripser) and
small (2k–40k simplices) but **drops essential \(H_1\)** on two_circles /
figure8 / torus / blobs / circle. Bottleneck after \(2\sqrt{r^2}\) scale
is **0.01–1.39**. **Rejected as a VR stand-in** — not shape-agnostic
enough for mixed homology.

**Optional approx (I207–I211):** sparse 1-skeleton → implicit, collapse=0.
Essential \(H_1\) **correct on every measured family**. Finite-H1 bottleneck
typically **0.005–0.04**. 1-skeleton size \(\sim n^{1.1}\). This is **not
exact VR**. Two constructions:

- GUDHI Sheehy ε=0.5 → `--edges` (I207).
- Owned `--sparse-eps` greedy-net flag graph, **cap = max(λ)** (I210/I213).
  Recommended **ε=0.6** (torus n=2000 **17.9×**, bn 0.028). ε=0.5 is
  low-loss (14× / 0.016); ε=0.7 is fast (21× / 0.038). `--sparse-cap min`
  rejected (I212): extra essential \(H_1\) on circle/torus. No GUDHI.

**Approx 10× vs Ripser (essential \(H_1\) kept)**

| Family | n | T | vs Ripser | bottleneck | construction |
| --- | --- | --- | --- | --- | --- |
| circle | 1000 | 1.5 | **89×** / **81×** | 0.013 / 0.007 | GUDHI / owned |
| torus | 2000 | 1.6 | **25×** / **14.5×** | 0.026 / 0.016 | GUDHI / owned |
| torus | 3000 | 1.6 | **72×** | 0.026 | GUDHI |
| blobs | 3000 | 1.0 | **10.6×** | 0.017 | GUDHI |
| sphere | 2000 | 1.4 | **11.2×** | 0.013 | GUDHI |
| sphere | 3000 | 1.4 | **19.4×** | 0.016 | GUDHI |
| uniform2 | 4000 | 0.35 | **13.1×** | 0.006 | GUDHI |

At n=2000, blobs/uniform2 are still 6–7×. 10× on those families is a
**scale** effect from the exponent gap (sparse time \(\sim n^{1.2}\),
Ripser \(\sim n^{2.2}\)).

### Optional-path complexity (I218, `--sparse-eps 0.6`, n=500…2000)

Justification: Cavanna–Jahanseir–Sheehy greedy-net flag complexes have
size \(O(n)\) for fixed \(\varepsilon\) and homology degree. Measured
pre-asymptotic edge exponents are **subquadratic on every family**,
including torus (exact collapse was \(n^{2.08}\) there). Same code path
for every cloud — not a circle/sphere/torus special case. Loss vs exact
VR is the unmatched short finite bars; essential \(H_1\) is preserved.

| Family | edges \(n^{}\) | PITH time \(n^{}\) | Ripser time \(n^{}\) | bn max | ess H1 |
| --- | --- | --- | --- | --- | --- |
| circle | **1.39** | 1.52 | **3.29** | 0.012 | 2=2 |
| blobs | **1.38** | 1.38 | 2.21 | 0.024 | 3=3 |
| sphere | **1.31** | 1.38 | 2.17 | 0.034 | 1=1 |
| torus | **1.38** | 1.60 | **2.92** | 0.055 | 2=2 |
| uniform2 | **1.37** | 1.40 | 2.14 | 0.014 | 1=1 |

figure8 / two_circles (mixed loops): ess H1 3=3, bn 0.011 / 0.034.

This is **not** exact VR. The exact default remains 0 topology loss and
is **not** a general Big-O win.

### Exact reduced VR (I224, `--reduced-vr`, not default)

Paper-faithful Koyama–Mémoli–Robins–Turner 2-complex. Same construction
for every finite metric (shape-agnostic). **Topology loss: 0** vs Ripser
on unit square, circle, blobs, sphere, torus, uniform2, two_circles,
figure8 (n≤500). I056’s “every triangle is a finite bar” was unfiltered
zero-persistence pairs.

| Family | triangles \(n^{}\) | PITH time \(n^{}\) | Ripser time \(n^{}\) | vs Ripser at n=500 |
| --- | --- | --- | --- | --- |
| circle | **2.20** | 3.53 | 2.56 | **0.12×** (67k tris, build 2.6s) |
| blobs | **2.05** | 3.14 | 1.43 | 0.024× |
| torus | **2.04** | 2.63 | 1.83 | 0.14× |
| uniform2 | **2.09** | 2.91 | 1.42 | 0.040× |

Justification: Lemma 3.9 — lune components are \(O(1)\) in fixed
dimension, so \(|\Delta_2|=O(n^2)\). Measured pre-asymptotic slopes sit
on that class (flag VR is \(O(n^3)\) triangles). Construction walks
lunes explicitly, so **time is not** a better class than Ripser’s
implicit cofacet heap. Do not select as default. `--reduced-vr` stays
an exact experimental H1 engine.

**I225 construction:** all-pairs lune UF (+ singleton skip) when a
distance matrix is present. Same triangles as I224. Construction
**2.3–3.7×** vs I224 (median 2.7×; circle n=500 2617→701 ms). Still
**0.42×** vs Ripser there; default collapse+implicit is 15 ms. The
remaining build cost is finding the lune (neighbor merge), not
connectivity. Not selected as default. Topology loss: **0**.

### I227 real RedZeD (H09, MIT, not default)

I122–I125 enumerated every leftover triangle. `redzed-tda` 0.1.1 is the
Kapulkin–Kershaw engine (arXiv:2606.06310, **MIT**). Same path on every
distance matrix — not a circle/sphere/torus special case. Active
enumeration only considers \((n+1)\)-cofaces that have an active face,
so most \((n+1)\)-birth columns are never built.

**Topology loss: 0.** Wave 88: exact 18/18 vs Ripser (unit square,
circle, blobs, sphere, torus, uniform2, two_circles, figure8; n≤2000).
Bottleneck \(\sim 10^{-7}\)–\(10^{-6}\) (float). Essential \(H_1\)
matches on every mixed-loop row.

| Family | RedZeD time \(n^{}\) | Ripser \(n^{}\) | PITH default \(n^{}\) |
| --- | --- | --- | --- |
| circle | 2.38 | **3.03** | **1.72** |
| blobs | 2.04 | 2.07 | 1.85 |
| torus | **2.30** | 2.76 | 2.67 |
| uniform2 | 2.03 | 2.04 | 1.92 |

Justification: the paper’s active-enumeration skip of \((n+1)\)-birth
columns. Measured pre-asymptotic time is still \(\sim n^2\)–\(n^{2.4}\),
not a proven better worst-case class than Ripser. The torus exponent gap
(2.30 vs 2.76) is the first **exact** clock that is 10× on the collapse
wall family. Circle 33× is real but PITH collapse+implicit remains
faster there (0.35 s vs 0.79 s). Blobs/sphere/uniform2 are 4.5–6.9× at
n=2000. **I229:** scale does **not** make those 10× (blobs n=4000 5.3×,
uniform2 5.1×, sphere 8.3×). High-n exponents match Ripser (~n^{2.3});
the win is a constant. Torus n=3000 **14.2×**. Topology loss: **0**.

**GUDHI 3.13 flag collapse** on the same n=2000 graphs is **slower**
than PITH (circle 7.94 s vs 273 ms; torus 4.05 s vs 1.40 s). Residual
\(|E'|\) matches (5169 / 6169 / 163426). The torus collapse wall is
**algorithmic**, not an implementation gap vs GUDHI.

**I228 in-tree wrap:** `--engine redzed` compiles vendored
`third_party/redzed/redzed.cpp` (`22ef1bf`, MIT). Wave 89: **exact
13/13** vs Ripser (unit square, figure8, two_circles, circle, blobs,
sphere, torus, uniform2). Torus n=2000 **12.3×** vs Ripser / **8.3×**
vs default PITH (0.21 s / 2.52 s / 1.72 s). Matches I227 wheel times.
CLI default **not** switched: collapse+implicit still wins on circle
(0.34 s vs 0.79 s / 35.8× vs Ripser). Recommended for real mixed data.

**I229 scale:** exact 9/9 including figure8/two_circles n=500. Loser
families stay ~5–8× at n=4000 (sphere 8.3× is closest). blobs n=4000
reduce_ms=313 of wall 394 (metric 59). Algebra needs ~2× for a 10×
wall. Not a general exact 10×.

**I230 `-DNDEBUG`:** exact 8/8, median 1.00× vs I229. Not a clock win.
Keep the flag. Topology loss: **0**.

**I231 owned `--engine active`:** leftover youngest-face H1 (RedZeD idea,
not the vendor). **Exact 12/12** through n=500 including figure8 /
two_circles / unit square. Topology loss: **0**. Clock **rejects**:
circle n=500 0.079× vs Ripser (3.85 s / 0.30 s, 4.5M triangles);
blobs n=500 0.004×; circle n=2000 **timeout 180 s**. Same O(|E|·deg)
triangle walk as persist_sparse without the annotation dictionaries /
rbit coface skip that make RedZeD fast. Leave `--engine active`
experimental. Vendored `--engine redzed` stays the recommended exact
path.

**I232 annotation skip:** R/Ri `resolve_bar` on the same walk. Empty
face-XOR counted as H₂ birth and not reduced. **Exact 19/19** through
n=1000 (unit square, figure8, two_circles, circle, blobs, sphere,
torus, uniform2). Topology loss: **0**. Skip median **0.964**. vs I231
circle n=500 **7.2×** / blobs **28×** / torus **21×**. vs Ripser still
loses (circle n=500 0.57×, n=1000 0.52×). Justification: reduce work
drops from every youngest-face triangle to the leftover-column count
(~67k vs 4.5M at circle n=500), but generation still visits
\(\Theta(|E|\cdot\deg)\) triangles (36M at circle n=1000). **Not** a
better Big-O than Ripser VR. Hold as an engine; keep the skip on
`--engine active`.

**I233 live-star generation:** **rejected.** MST 1-leftover + live
leftover-star (and leftover-coface existence) invented H1 bars on
circle / figure8 / blobs / torus / sphere. Reverted to I232.

**I234 owned H0+H1+H2:** empty-XOR triangles are H2 births; tets sorted
by diameter; R2/Ri2 `resolve_bar`. **Exact 10/10** vs Ripser including
sphere void (ess H2 1=1 at n=80 and n=200), figure8 / two_circles
(ess H1 2=2), blobs (ess H0 3=3 at n=1000). Topology loss: **0**.
Hard case sphere n=200 maxdim=2: active **3.21 s / 0.039×** vs Ripser
0.13 s; RedZeD **0.040 s (3.2×)**; default collapse **0.005 s (26×)**.
blobs n=1000 H1: active 1.41 s / 0.058×; RedZeD 0.019 s. Justification:
H2 adds a tet pass on the H2-birth 2-skeleton. Size is still the flag
VR class, not a better Big-O. Usable real-data H0–H2 at more points is
`--engine redzed` or the collapse default, not owned active (yet).

**I235 `--engine auto` residual-frac dispatch:** 250-point stride
subsample collapse; τ=0.04. **Exact 11/11.** Torus frac=0.28 → RedZeD
**12.5×** at n=2000 (skips 2.86 s collapse). Circle frac=0.021 →
collapse **28×** at n=1000. Blobs/sphere frac≈0.057 → RedZeD 2.6× /
3.3× (faster than collapse there). Topology loss: **0**. Justification:
the probe is \(O(s^2)\) with \(s=250\), not a function of n; full work
is whichever exact engine is cheaper. **Not** a better Big-O. Not a
general 10× (blobs stay ~3–5×).

**I236 H2-aware τ + leftover-coface AE reject:** maxdim≥2 uses τ=0.15.
Wave 97 **exact 9/9** H0–H2 (figure8/two_circles ess H1 2=2; sphere void
ess H2 1=1 at n=80 and n=400; blobs ess H0 3=3). Sphere n=400 H2
**auto-collapse** frac=0.059, **61×** vs Ripser (0.017s/1.05s) and
**19.5×** vs RedZeD (0.335s). Torus n=400 H2 **auto-redzed** frac=0.29,
4.6× vs Ripser / 3.2× vs collapse. H1 dispatch unchanged (circle
auto-collapse 18×; blobs auto-redzed 3.6×). Topology loss: **0**.
Owned leftover-coface / first-hit `process_leftover` invented finite H1
on every mixed cloud (essentials held; figure8 unmatched 12) — reverted
to the I232 walk. Justification: H2 tet work is on the residual, so a
mid frac that wants RedZeD for H1 wants collapse for H2. Still a
portfolio, not a better Big-O.

**I238 lazy parallel RedZeD metric:** auto-redzed no longer builds an
n×n `vector<vector>` before reduce. Probe is O(s²) on 250 points from
the cloud; fat dispatch fills RedZeD’s lower-tri matrix in parallel.
**Exact 10/10.** Circle stays collapse **18×**. Sphere n=400 H2 stays
collapse **62×**. Torus n=2000 **12.7×**. Blobs n=4000 was **6.72×**
(0.32s/2.17s; I229 was 5.3× / 394 ms — metric 59→7 ms, reduce still
297 ms) until I239. Uniform2 n=4000 **6.93×**. Topology loss: **0**.
Constant-factor cut, not a better Big-O, not a general 10×.

**I239 exact G_T component split:** VR≤T of a disconnected threshold
graph is the direct sum of the blocks. Union-find on d≤T, extract
submatrices, bounded thread-pool RedZeD, merge bars. One component →
I228 unchanged. **Exact 10/10** H0–H2 (figure8/two_circles 2=2; sphere
void 1=1; two_spheres void 2=2; blobs H0 3=3). Circle auto-collapse
**18×**. Sphere n=400 H2 **61×**. Blobs n=2000 **13×** / n=4000
**18.3×** (0.12s/2.18s, reduce 77 ms, cc=3) / n=6000 **13.5×**
(0.38s/5.16s) before I240. Uniform2 n=4000 stays **6.3×** (cc=1).
Topology loss: **0**. Justification: RedZeD time is superadditive in n,
so k equal blocks cost ~k·(n/k)^α with α≈2.3. **Not** a better
worst-case class (connected G_T is unchanged). Real clustered data is
the payoff.

**I240 spatial UF + per-component metric:** cell size T, Moore
neighborhood (if d≤T then |Δcell|≤1). Components are found without an
n×n matrix; each block allocates only m×m. **Exact 10/10** H0–H2
(two_spheres forced redzed-cc: 9900 vs 19900 distances, void 2=2;
blobs H0 3=3). Circle auto-collapse **17×**. Sphere n=400 H2 **59×**.
Blobs auto-redzed-cc: n=4000 **21.9×** (2.67M/8.00M pairs), n=6000
**24.4×** (6.00M/18.0M), n=8000 **27.4×** (0.38s/10.4s, 10.7M/32.0M).
Uniform2 n=4000 **5.6×** / 1 component / full matrix. Topology loss:
**0**. Justification: metric and memory are \(\sum_k m_k^2/2\) instead
of \(n^2/2\). On k equal clusters that is a \(k\times\) cut. Reduce
still \(\sim(n/k)^{2.3}\) per block — the I239 class, now without the
n×n tax. Connected G_T is unchanged. This is the first exact path that
gets **cheaper per point** as a clustered cloud grows.

**I237 GUDHI explicit Rips + scale H0–H2:** GUDHI 3.13
`RipsComplex`+`SimplexTree` is **exact** (7/7 vs Ripser including
figure8 / sphere void / torus H2) but **not a clock engine**: blobs
n=1000 15.9 s / 17.8M simplices vs auto 21 ms (**0.001×**). Birth-time
leftover-coface AE matched I236’s unmatched finite H1 (figure8 +12) —
reverted. Selected `--engine auto` at more points: sphere n=600 H2
**136×** (void 1=1); blobs/uniform2 n=2000 H1 **5.4× / 5.5×**; torus
n=600 H2 auto-redzed **4.5×** and **88×** vs collapse (13.9 s). Topology
loss: **0**. Still not a general H1 10×. Not a better Big-O.

**I241 H0 Kruskal:** `maxdim=0` never starts RedZeD. Spatial T-cell
edges + Kruskal is exact H0 of VR≤T. Wave 102 **exact 11/11** (blobs
H0 3=3 at n=4000 and n=8000; uniform2 H0 1=1; figure8/two_circles 2=2;
sphere void 1=1; two_spheres void 2=2). H0 clock vs Ripser dim 0 is
only **~1.9×** (blobs n=8000 1.27s/2.46s) — Ripser H0 is already
union-find; the cost is emitting |E(G_T)|. T-capped 1-component fill
was **reverted** (uniform2 metric 7→80 ms). H1 holds: blobs n=4000
**23×**, circle **18×**, sphere H2 **61×**, uniform2 **5.6×**. Topology
loss: **0**. Support as the H0 path. Hold for H0 10× and for general
H1 10×.

**I242 vendor-faithful owned H1 AE:** incremental `register_active`,
leftover-coface erase-without-pair, combinatorial `coface_ready`.
maxdim≥2 keeps the I232 walk (vendor AE is H1-only). Wave 103
**exact 13/13** H0–H2 (figure8 2=2; two_circles 2=2; sphere void 1=1;
two_spheres 2=2; blobs H0 3=3). Hard connected uniform2 n=5000 auto
**5.5×** (0.62s/3.42s, reduce 488 ms, 1 component). Blobs n=4000 H1
**23×**. Sphere n=400 H2 **61×**. Owned AE vs RedZeD: figure8 1.3×
(tiny), circle n=500 **0.06×**, uniform2 n=1000 **0.33×**. Topology
loss: **0**. Justification: I236 invented bars by pairing on leftover
coface and pre-registering later leftovers into earlier stars. Vendor
erases that column and only seeds from already-registered actives.
Exact, not a clock engine, not a better Big-O. Do not change the
default.

**I243 incremental rbit AE:** word-AND neighborhoods advance by leftover
diameter (vendor `advance_rbits`). Same I242 pairing. Wave 104
**exact 11/11** H0–H2. Circle AE **0.26s** (I242 0.38s, RedZeD 0.021s).
Uniform2 n=5000 auto **5.6×**. Blobs n=4000 H1 **22×**. Sphere n=400
H2 **61×**. Topology loss: **0**. Constant-factor AE cut, not a better
Big-O, not a default.

**I244 skip enclosing on finite VR≤T:** vendor `redzed()` always computed
the enclosing radius (n² max). For a finite T that is wasted.
`redzed_vr` uses thr=T. Wave 105 **exact 10/10** H0–H2. Connected
uniform2 n=5000 **6.8×** (0.50s/3.42s; I243 was 5.6× / 0.61s). Reduce
411 vs 484 ms. Blobs n=4000 H1 **20×**. Sphere n=400 H2 **59×**. Circle
auto-collapse **17×**. Fill-collect EdgeList **rejected** (sort tax).
Topology loss: **0**. Constant-factor, not 10×, not a better Big-O.

**I245 parallel build_edges:** same vendor buckets + `(diam, comb_index)`
sort; the two n² scans and per-bucket sorts run on a pool. Wave 106
**exact 10/10** H0–H2. Connected uniform2 n=5000 **8.3×** (0.42s/3.46s;
I244 6.8× / 0.50s). Reduce 325 vs 411 ms. Blobs n=4000 H1 **21×**.
Sphere n=400 H2 **60×**. Circle **18×**. Topology loss: **0**. Still
not 10×, not a better Big-O.

**I246 lazy R/Ri insert:** skip the singleton when top-dimension AE has
no seeds and leftover-coface would erase (zero bar / (n+1)-birth). Same
path for H1 leftovers and H2 empty-XOR births. Wave 107 **exact 11/11**
H0–H2. Connected uniform2 n=5000 **9.56×** (0.35s/3.38s; reduce 264 vs
I245 325 ms). n=6000 **9.25×** (0.47s/4.34s). Blobs n=4000 H1 **24×**.
H0 Kruskal **1.9×**. Sphere n=400 H2 collapse void 1=1. Topology loss:
**0**. Constant-factor AE cut, not 10×, not a better Big-O.

**I250 skip collect on empty ActiveReg:** collect only reads the
registry. Profile: 3.37M / 3.46M leftovers have no actives. Wave 111
**exact 11/11** H0–H2. Connected uniform2 n=5000 **10.03×**
(0.34s/3.44s; pith cut vs I246 0.35s). n=6000 **10.12×** (0.43s/4.37s;
I246 0.47s). Blobs n=4000 H1 **24×**. H0 **1.9×**. Sphere H2 **60×**.
Topology loss: **0**. Connected 10× on this hard family. Still not a
better Big-O.

**I251 inline empty-seed skip:** 97% of leftovers never enter
`active_enum_lazy`. Wave 112 **exact 12/12**. Uniform2 n=5000 **11.0×**
(0.32s/3.54s). n=6000 **10.8×** (0.41s). Torus n=2000 **15.0×**
(0.18s/2.70s, ess H1 1=1). Blobs H1 **23×**. Sphere H2 **61×**. Topology
loss: **0**. Real pith cut on top of I250. Not a better Big-O.

**I252 leftover-coface no-seen:** H1 unrolls m=2 and skips the empty
`seenbits` mask; H2 no-seed uses the same skip. Same `coface_ready`
(no I247 extra `dist()`). Wave 113 **exact 14/14** H0–H2. Uniform2
n=5000 **12.7×** (0.30s/3.79s; reduce 206 vs I251 226 ms). n=6000
**11.2×** (0.39s). Harder connected n=7000 **11.8×** (0.51s/5.96s).
Sphere n=2000 H1 **10.3×** (0.079s/0.81s). Torus **14.5×**. Blobs H1
**25×**. H0 **1.9×**. Sphere H2 **59×** (void 1=1). Topology loss:
**0**. Real pith cut. Not a better Big-O.

**I256 spatial prebuild (sparse T):** when π(T/L)²<0.2, ∞-fill far
pairs, write only d≤T, pass a spatial EdgeList. Wave 117 **exact
13/13**. Dense uniform2 n=5000 stays all-pairs **10.9×** (0.30s).
Sparse n=10000 T=0.14 **2.73M vs 50M** distances, 0.50s / 6.0× vs
Ripser (Ripser is also cheap at that T). Torus n=2000 used spatial
(479k vs 2.0M) **13.9×**. Topology loss: **0**. Better distance
class when the T-ball is small; worst-case G_T still Θ(n²).

**I257 skip ∞-fill + parallel spatial_edges:** far matrix entries stay
0 (`resize_lower`); empty prebuilt is a valid G_T. Wave 118 **exact
14/14**. Dense n=5000 held **11.2×** (0.31s). Spatial n=10000 metric
**21 vs 27 ms**, 0.48s / **6.42×**. Harder n=15000 T=0.11 **5.60×**
(0.83s/4.66s; **3.90M vs 112M**). Torus **14.2×**. Sphere H2 **60×**.
Topology loss: **0**. Remaining spatial tax is the C(n,2) zero-init
(~450 MB at n=15000).

**I258 skip C(n,2) matrix (CSR):** spatial `coface_ready` reads a
lower-tri CSR of d≤T pairs (miss = +∞). Wave 119 **exact 14/14**.
Dense n=5000 held **11.4×** (0.30s). n=15000 **5.79×** (0.82s).
Harder n=20000 T=0.09 **6.18×** (0.99s/6.10s; **4.71M vs 200M** —
an 800 MB matrix is gone). Torus **11.5×** (CSR lookup tax vs I257
14.2×). Sphere H2 **57×**. Topology loss: **0**. Justified class:
O(|E|) metric memory vs O(n²) when the T-ball is small.

**I259 open-address hash get:** same sparse path, O(1) expected
lookup. Wave 120 **exact 13/13**. Torus reduce **154 vs 174**,
**12.7×** (0.21s). Dense n=5000 **11.2×**. n=20000 **5.96×**
(1.04s; reduce 456 vs 497, table-zero metric 192 vs 118). Sphere
H2 **62×**. Topology loss: **0**.

**I260 tight hash (no Slot zero):** load ~0.75 + occupancy bitmap +
malloc. Wave 121 **exact 13/13**. n=20000 metric **113 vs 192**,
pith 1.02s / **6.0×**. Dense n=5000 **11.4×**. Torus **12.4×**.
Sphere H2 **52×**. Topology loss: **0**. Reduce a bit longer
(load 0.75 probes).

**I261 load-0.5 malloc/bitmap:** I259 probe length without
`tab.assign(16M)`. Wave 122 **exact 13/13**. n=20000 reduce
**468 vs I260 513**, metric 153, pith 1.03s / **6.2×**. Dense
n=5000 **10.9×**. Torus **12.4×** (reduce 155). Sphere H2 **50×**.
Topology loss: **0**. Selected spatial hash.

**I262 always-spatial (reverted):** drop π(T/L)² gate. Wave 123
**exact 14/14**. figure8 n=2000 **14.1×** (ess H1 2=2, 427k vs
2.0M). Dense n=5000 **7.4× / 0.46s** and sphere n=2000 **6.8×**
lost the 10× — gate restored. Topology loss: **0**.

**I263 edge-frac spatial + auto:** spatial if π(T/L)^d<0.20 **or**
250-pt |E|/C(m,2)<0.25. Auto also prefers RedZeD on that probe
(figure8 subsample collapse looked thin). Wave 124 **exact 15/15**.
figure8 n=2000 T=1.1 **16.8×** spatial (482k vs 2.0M, ess H1 2=2).
Hard mixed case figure8 n=4000 T=1.1 **27.1× / 1.07 s** vs Ripser
29 s (1.98M vs 8.0M, 2=2). Dense n=5000 **11.2×** all-pairs.
Sphere n=2000 all-pairs, remesure **10.1×** (wave 9.58× noise).
Torus **13.0×**. Circle collapse **16.5×**. Sphere H2 **58×**.
Blobs H0 **1.8×** / H1 **24×**. Topology loss: **0**.

## Next levers (still open after I275)

`--engine auto` is a shape-agnostic exact H0–H2 portfolio: circle H1
10×, torus H1 **13.0×**, sphere H1 **10.1×** at n=2000, mixed
figure8 n=4000 **27×**, sphere H2 **58×** at n=400, **disconnected
blobs 24×** at n=4000 on one CLI path. Connected uniform2 H1 is
**11.2×** at n=5000 (0.33 s). Sparse connected n=20000 **5.6×**
(1.11 s, 4.71M vs 200M). I242/I243 owned AE is exact; rbit is
~1.5× on circle AE and still 12× slower than RedZeD. GUDHI explicit
Rips is exact and too slow.

1. **CLI default:** `--engine auto` (I235+I236+I239+I240+I241+I263+I271+I275). H1 τ=0.04; H2 τ=0.15; hollow edge-frac <0.25 → redzed.
2. **Forced engines:** `--engine implicit` = I193+I197+I202+I203 only;
   `--engine redzed` = I228+I239+I240+I244+I245+I246+I250+I251+I252+I256+I257+I258+I259+I260+I261+I263+I270+I271+I275; H0 = Kruskal / I271 2D / I275 3D walk-locate Delaunay.
3. **Owned optional approx:** `--sparse-eps 0.6 --sparse-cap max` (I213/I218)
   when n grows past exact VR. **`--delaunay-vr` (I276)** for Euclidean
   d∈{2,3}: flag of the Delaunay 1-skeleton, Θ(n) edges, **essential
   H0/H1/H2 kept** on mixed families (figure8 n=2000 **419× / 6 ms /
   5.9k edges**, 209 unmatched finite; n=8000 **24 ms / ess1=2**).
   **`--delaunay-alpha auto` (I282/I286)** is the recommended
   optional Euclidean path. α(n)=min(2.75, 1.75+0.125 log2(n/400)).
   maxdim=1: H1 thicken (I282). maxdim≥2: **I286 split** — H1 on
   the thicken, H2 on the α=1 flag (do not thicken H2). figure8
   n=2000 maxdim=2 **exact H1 33× / 75 ms**; n=4000 **158 ms /
   186k / ess1=2**; n=8000 **430 ms / ess1=2**. sphere n=2000
   H0+H1+H2 **203 ms / ess2=1**; n=4000 **621 ms**; n=8000
   **1.42 s / 1.07M / ess2=1** (I287);    n=16000 **0.27 s / 80k / ess2=1** (I300 3D α=1 RedZeD; I297 thicken was 3.02 s).
   n=30000 **0.62 s**. n=400 unmatched 52 (I276 flag; I286 split was 3).
   flag 52. two_spheres n=400 ess2 2=2, unmatched 2.
   I279 fixed 2.25 is the measured H1 constant. Default α=1 stays
   I276 ess-only. Not a VR identity.
4. Connected uniform2 is **11.2×** at n=5000 (0.33 s).
   Sphere n=2000 H1 **10.1×**. Torus n=2000 **13.0×**. Mixed
   figure8 n=4000 is **27× / 1.07 s**. Sparse n=20000 is **5.6×**.
   Remaining spatial-path wall is leftover *visits* (figure8 n=4000
   reduce 866 ms / 1.98M leftovers), not leftover-coface internals.
   I253–I255 / I265 leftover-coface skips are exact and reverted.
   Do not retry always-spatial (I262) or rbit layout (I264).
5. Hash load-factor constants are exhausted (I259–I261). I263
   edge-frac probe is the selected spatial gate. Dense path stays
   I238 all-pairs when volume≥0.2 **and** probe≥0.25. I264
   word-major rbits is exact and reverted (figure8 reduce 866→1118
   ms; dense 9.8×). Do not retry rbit layout. I265 unique-diam AND
   on spatial hash is exact and reverted (figure8 reduce 871≈866).
   Do not retry leftover-coface inner-loop skips. I266 fused H1
   leftover loop is exact after an H2-only fix and reverted (840 vs
   866 ms). Do not retry ae_prepare fusion. Incremental rbits are
   required for maxdim≥2. I267 tight H2 generate_stream is exact
   15/15 and reverted (n=80 reduce 1.50 vs 1.47 ms). leftover_coface
   already ANDs the live word range; do not retry H2 stream word
   skips at n≲400 (2–7 words). I268 Morton vertex order is exact
   14/14 and reverted (figure8 n=4000 reduce 821 vs 866 ms). Do
   not retry space-filling vertex orders. Collapse on the same
   cloud is 845 ms / 1.97M fast trims — same Θ(|E|) wall. I269
   collapse live AND-eq + Morton is exact 15/15 and reverted
   (figure8 n=4000 collapse 768 vs 845 ms). Do not retry collapse
   word-range + Morton. **I271 walk-locate 2D Delaunay H0 is selected**
   for maxdim=0, d=2, n∈[256,100000]: exact 14/14, blobs n=4000
   **55× / 4.1 ms / 12k edges** (I270 scan was 176 ms / 3.17×),
   n=8000 **7.6 ms / 137×** (I270 557 ms), n=12000 **218× / 0.027 s /
   36k edges**. Justified: MST ⊆ Delaunay, expected O(n log n)
   incircle vs O(n²) scan vs Θ(|E_T|) listing. H1 leftover visits
   remain Θ(|E|). I272 Gabriel leftover skip is **not exact**
   (n=256 ess H1 31 vs 0). I273 empty-seed-only non-Delaunay skip
   is exact 13/13 but figure8 n=4000 reduce **864≈866 ms** — the
   wall is ae_seeded, not empty-seed leftover_coface. Do not retry
   empty-seed geometric leftover skips. **I274 3D scan is fallback
   only** (n≤8000). **I275 walk-locate 3D Delaunay H0 is selected**
   for maxdim=0, d=3, n∈[256,50000]: exact 13/13, Θ(n) edges,
   expected O(n log n) construction. sphere n=4000 **29× / 22 ms /
   20k** (I274 scan 578 ms), n=8000 **65× / 0.056 s / 40k** (I274
   2.39 s), hard n=16000 **147× / 0.112 s / 81k**. I274 walk failed
   on `F_b >= T` (false for a 3-ball) and cavity-slot reuse. Do not
   retry leftover empty-seed skips. H1 leftover visits remain Θ(|E|).
   **I276 `--delaunay-vr` is the owned optional Euclidean scale path**
   (not default): ess 8/8, figure8 n=2000 **419× / 6 ms**, n=8000
   **24 ms**. Finite unmatched 3–209. **I277 α=1.5 hold** (blobs 2
   unmatched). **I278 α=1.75 hold** (n=8000 unmatched 2). **I279
   α=2.25 is the measured exact constant**: 9/9 oracles, figure8
   n=4000 **156× / 152 ms**, n=8000 **67× / 390 ms / 428k**.
   **I282 auto** is the recommended CLI. Do not thicken H2. Do
   not make it the exact default. **I280 `--delaunay-adapt` is an
   exact alternate at stable α=1.5** (9/9) but ~2× edges / 3× clock
   vs I279 — hold, do not replace. **I281 exact H2 scale:** sphere
   n=800 **527× / 56 ms** vs Ripser 29.6 s (auto-collapse, 0 unmatched).
   Optional Delaunay-flag H2 keeps the void at n=800 (17 ms, 86
   unmatched finite).    **I282 `--delaunay-alpha auto` (I305 cap 2.25) is the
   recommended H1 thicken CLI** (exact 9/9, n=8000 65×). **I286
   split** makes auto work at maxdim≥2 (figure8 n=4000 158 ms;
   sphere n=2000 H0+H1+H2 203 ms). **I287 split scale:** sphere
   n=8000 H0+H1+H2 **0.865 s / ess2=1** (I297 thicken). **I300 3D
   α=1 RedZeD** is the selected H0+H1+H2 path in \(d=3\): sphere
   n=16000 **0.20 s / 80k / ess2=1** (I302); n=30000 **0.39 s**;
   n=50000 **0.65 s / 252k** (I306); n=80000 **1.09 s / 404k /
   ess2=1**. figure8 (2D) still thickens: n=16000
   **0.54 s / 878k / ess1=2** (I305 α≤2.25); n=24000 **0.82 s**.
   **I297 RedZeD-on-thicken is selected** for fat 2D / maxdim=1
   thicken H1 (`|E|≥8n`). H2 on 2D split stays implicit.
   **I283
   Delaunay 2-complex hold:** ess kept, sphere n=400 un 52→33, but
   two_spheres worse (28→32). Alpha drops ess H2. I276 flag stays.
   **I284 H0 scale:** blobs n=25000 **515× / 55 ms** exact;
   n=50000 **113 ms / 150k** (Ripser timeout). **I285 3D H0 scale:**
   sphere n=16000 **139× / 116 ms** exact; n=30000 **288× / 221 ms /
   151k** vs Ripser 63.6 s; n=50000 **367 ms / 252k**. Next: one
   Euclidean H0+H1+H2 path is I286 split (I287: sphere n=8000
   1.42 s). **I288 equal-set seeded_is_noop:** exact 10/10,
   figure8 n=4000 reduce **848≈866 ms** — reverted. Do not retry
   leftover XOR/noop constants. **I289 G_t rbit apparent:** exact,
   collapse=0 still ~24 s — coboundary assembly of 892 cols is the
   wall. Reverted. **I290 implicit R-cache:** collapse=0 exact but
   27.7 s (slower); collapse=1 invented H1. Reverted. Do not retry
   add-\(R\) without a full emergent coboundary. **I291 thicken-collapse:**
   exact-on-flag, slower at n≥4000 (figure8 n=16000 collapse 4.05 s).
   Reverted. Do not collapse the optional thicken. **I292 cell skip:**
   same edges, no pith cut. **I293 parallel apparent:** exact,
   figure8 n=16000 **0.876 vs 1.03 s**; sphere n=16000 **4.12 vs
   4.73 s / ess2=1**. 199k surviving columns remain the thicken
   persist wall. **I294 parallel thicken:** same edges, metric
   1131→955 ms, pith 4.12→3.95 s — keep, not a selected pith lever.
   **I295 R-cache + full emergent \(D(e_j)\):** collapse=1 identity
   held; slower on thicken. Reverted.    **I296 \(D(e)\) memo:** exact,
   collapse=0 still 103M probes (unique apparent-facet adds). Reverted.
   Do not retry add-\(R\) or \(D(e)\) memo. **I297 RedZeD-on-thicken
   is selected** for fat thicken persist: figure8 n=16000 **0.621 vs
   0.838 s**; sphere n=16000 **3.02 vs 3.95 s / ess2=1**. Harder
   figure8 n=24000 **1.06 s**; sphere n=20000 **3.89 s**. Remaining
   optional-path wall is AE leftover on 2–3M thicken edges (reduce
   2.0–2.5 s). **I298 reuse-Delaunay split:** same edges, keep (one
   walk); metric 916→905 ms — not a pith cut. **I299 RCM-on-thicken:**
   exact, figure8 reduce 195→164 ms, pith worse (0.67 vs 0.62 s).
   Reverted. Do not retry bandwidth/Morton orders on thicken.
   **I300 3D α=1 RedZeD is selected** for Euclidean maxdim≥2 in \(d=3\):
   no H1 thicken (noise loops). sphere n=16000 **0.27 s / ess2=1**
   (I297 thicken 3.02 s); n=30000 **0.62 s / 151k**. 2D still
   thickens (figure8 n=16000 **0.67 s / ess1=2**). Finite 3D H1 on
   this path is I276-flag. **I301 CSR H2 stream is selected** on
   \(|E|\le 16n\): sphere n=30000 **0.44 vs 0.62 s**; n=50000
   **0.84 s / 252k / ess2=1**. \(O(|E|\deg)\) vs \(O(|E|\,n/64)\).
   Dense \(G_T\) keeps vendor `generate_stream`. **I302 growing-adj
   leftover_coface is selected** on the same gate: skip the n×n
   rbit matrix. sphere n=30000 **0.39 vs 0.44 s**; n=50000
   **0.68 vs 0.84 s / 252k / ess2=1**. leftover_coface \(O(\deg)\)
   vs \(O(n/64)\). Fat 2D thicken (\(|E|>16n\)) still uses rbits.
   **I303 mean-deg leftover-adj gate reject/revert:** figure8 n=16000
   **0.85 vs 0.63 s** (sorted insert \(\Theta(|E|\deg)\)). **I304
   hash leftover reject/revert:** figure8 n=16000 **1.55 vs 0.63 s**
   (reduce 1121 vs 201 ms). Do not retry leftover adj/hash on
   \(|E|>16n\). Fat thicken stays on rbits. **I305 auto-α cap 2.25
   is selected:** figure8 n=16000 **0.54 vs 0.63 s / 878k vs 977k /
   ess1=2**; n=24000 **0.82 s**. Extra thicken past I279’s exact
   constant was noise, not essential H1. 3D stays α=1.
   **I306 share H2/leftover adj hold/keep:** sphere n=50000
   **0.65 vs 0.68 s** (reduce 273 vs 304 ms); n=80000
   **1.09 s / 404k / ess2=1**. Duplicate \(G_r\) build was a ~10%
   reduce tax. Keep; not a selected pith lever. Metric (Delaunay
   walk) is the 80k wall. **I307 fsign-walk reject/revert:** 80k
   **1.14 vs 1.09 s** (metric 539 vs 507). Do not retry face-sign
   caching. **I308 live-tet list hold/keep:** 80k **1.12 vs 1.09 s**
   (metric 527 vs 507). `locate_scan` is O(live); not a pith cut.
   Do not retry dead-tet extract skips. **I309 insphere-osign
   reject/revert:** 80k **1.47 vs 1.09 s**. The 4×4 det dominates;
   do not retry tet-orient caching. Cheap Delaunay-predicate
   bookkeeping (I307–I309) is exhausted. **I310 circumball-insphere
   reject/revert:** replacing the det with `||p-c||²<r²` is **not
   exact** (sphere n=16000 |E| 80659 vs 80641; n=50000 ess2 2 vs 1;
   n=100000 15 s / ess2=3). Do not retry a non-conservative
   circumcenter predicate. 2D thicken still holds (figure8 n=24000
   **0.86 s / ess1=2**). **I311 entered-face walk reject/revert:**
   identity held (80k/100k ess2=1, |E| 80641 at 16k) but 80k
   **1.28 vs 1.09 s**. Reverse-nbor scan ate the skipped orient.
   Do not retry without a stored reverse-face index. n=100000
   H0+H1+H2 is **~1.6 s / 505k / ess2=1** on the I306 path.
   **I312 skip post-walk contains hold/keep:** identity held
   (80k 1.09 s / 404k / ess2=1; figure8 n=24000 **0.83 s /
   ess1=2**). Not a pith cut. I307–I312 exhausted cheap 3D
   walk/locate bookkeeping.
   ae_seeded visits remain the exact-H1 wall.
6. Owned AE leftover-star walk is still Θ(|leftover|·deg★) — rbit cut
   has_leftover_coface, not seeded probes (circle still 875k). I288
   equal-set seeded_is_noop is exact and reverted (848≈866). Packed
   annotations are memory-hostile vs sorted-set XOR on sparse R.
   Do not retry leftover XOR/noop constants.
7. I241 T-cap fill is rejected (slower metric). Do not retry without
   a reduce cut.
8. GPU later.
