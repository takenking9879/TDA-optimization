# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I231. **CLI default is still
I193 + I197 + I202 + I203** collapse+implicit (circle n=4000 **140×**).
**Recommended general exact path:** `--engine redzed` (I228, vendored
MIT RedZeD). Shape-agnostic, 0 bars lost, first exact **torus n=2000
12.3×** vs Ripser. Circle 140× is a collapse-friendly regime, **not**
the success criterion.

## Success criteria (goal amendment)

The final algorithm must be **shape-agnostic**: one path for real data with
mixed homology, not a circle/sphere/torus special case. It must target
**better Big-O than Ripser VR**, not only a 10× constant-factor win, and
**preserve as much topology as possible**. Complexity claims need a
justification (residual \(|E'(n)|\) slopes, column counts, or a different
complex with a proven size bound). Any information loss vs exact VR must be
quantified (unmatched bars / bottleneck / interleaving).

Current honest status: the **CLI default is shape-agnostic** (0 unmatched
vs Ripser) but **worst-case Big-O is not improved** — collapse is an extra
\(O(E\cdot|C|)\) pass; torus residual stays \(\Theta(n^2)\) (I204).
**I228 `--engine redzed`** is the recommended general exact path: owned,
shape-agnostic, **0 unmatched** (13/13 + I227 18/18), first exact
**torus 10×** (12.3× at n=2000). Measured time \(n^{2.03–2.38}\) vs
Ripser \(n^{2.04–3.03}\) — better exponents on circle/torus, **not** a
proven worst-case class change. Topology loss: **0**. CLI default stays
collapse+implicit (faster on circle). **I224 reduced VR** is exact with
\(O(n^2)\) triangles but loses clock. The **optional** `--sparse-eps 0.6`
path keeps essential \(H_1\) and sits in a better size class (I218) at
quantified bottleneck 0.005–0.034.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + I182 live-bit AND generate-C + I186 no LiveAdj +
**I193 multi-apex AND-eq** + **I197 any_later C_now AND-eq** + **I202
`|C_now|≥32` witness rescan**; I189 is the first no-later candidate) →
**Ripser-heap implicit cohomology** on the residual (I137) with **I203
hi-walk early-stop** after the zero-pivot / emergent pair.
`--collapse-alg back` is this stack. `back-src` is the pre-I182 star walk.

- \(H_0\): Kruskal. `--collapse -1` **skips collapse** when `maxdim=0`.
- \(H_1\): leftover (non-MST, non-apparent) edges, youngest-first; F₂ heap
  coboundary; oldest remaining pivot; same-diameter apparent/emergent;
  V-matrix re-enumeration. `--engine auto` **is implicit** (I137).
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

## Next levers (still open after I231)

Collapse+implicit is shape-agnostic with **0 bars lost** and is **not**
a general 10×. `--engine redzed` is the first owned exact torus 10×
and a 5–8× exact win on the other families. Scale and NDEBUG do not
make blobs/uniform2 10×.

1. **CLI default:** I193 + I197 + I202 + I203. Faster on collapse-friendly
   circle.
2. **Recommended general exact:** `--engine redzed` (I228/I229). Exact,
   torus 12–14×, blobs/uniform2 ~5×, sphere 8.3× at n=4000. I231 owned
   active H1 is exact but **much slower** (no rbit / annotation skip).
   Next owned port must copy those data structures, not only the
   youngest-face filter.
3. **Owned optional approx:** `--sparse-eps 0.6 --sparse-cap max` (I213/I218).
4. H07 kd-tree / H08 distilled still open, lower priority.
5. GPU later.
