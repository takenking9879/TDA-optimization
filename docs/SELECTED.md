# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I202. **Default collapse is I193
multi-apex AND-eq + I197 any_later C_now AND-eq + I202 witness rescan gated
on `|C_now|≥32`** on I182 live-bit C + I186 no LiveAdj. Flagship circle
n=4000 T=1.5 is **140×** vs Ripser (I196). That number is a
collapse-friendly regime, **not** the success criterion.

## Success criteria (goal amendment)

The final algorithm must be **shape-agnostic**: one path for real data with
mixed homology, not a circle/sphere/torus special case. It must target
**better Big-O than Ripser VR**, not only a 10× constant-factor win, and
**preserve as much topology as possible**. Complexity claims need a
justification (residual \(|E'(n)|\) slopes, column counts, or a different
complex with a proven size bound). Any information loss vs exact VR must be
quantified (unmatched bars / bottleneck / interleaving).

Current honest status: the **code path is shape-agnostic and exact** (0
unmatched vs Ripser on every measured family). **Worst-case Big-O is not
yet improved** — collapse is an extra \(O(E\cdot|C|)\) pass; torus residual
stays \(\Theta(n^2)\). I204 measures residual slopes; I203 cuts reduce work
on every residual without changing the pairing class.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + I182 live-bit AND generate-C + I186 no LiveAdj +
**I193 multi-apex AND-eq** + **I197 any_later C_now AND-eq** + **I202
`|C_now|≥32` witness rescan**; I189 is the first no-later candidate) →
**Ripser-heap implicit cohomology** on the residual (I137).
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
| Reduced-VR prototype (I056) | Finite \(H_1\) wrong |
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
| torus | \(H_1\) | 2000 | 1.6 | **1.31×** I202 (collapse 1512 ms, 113k shifts); residual 163k. I197 was 1.14× / 1771 ms |
| torus | \(H_1\) | 1000 | 1.6 | **1.63×** I200 (was I139 1.31×) |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; **worse-case / all-shape Big-O
better than Ripser**. Topology loss on the default path is **zero** (exact
VR≤T vs Ripser).
**Honest H1>10× (exact, no oracle, default path):** circle n=4000 T=1.5
**140×** (I196), n=3000 **119×**, n=2000 T=1.5 **84.4×** (I202), n=2000 T=1.2
**33.8×** (I200). These are **not** a general or asymptotic claim.
I202 vs Ripser at n=2000: blobs **1.77×**, sphere **1.84×**, torus **1.31×**.
I200 uniform2 **2.10×**. All measured families still beat Ripser; none but
circle is 10×.
I139: owned implicit **reduce 67 ms** on torus1000 residual 38k (homology was 1.7 s).
E3 (collapse + Ripser-sparse) is no longer required; we own that residual class.

**Alpha (I136)** is a different complex: GUDHI Alpha circle3000 0.023 s vs Ripser VR 123 s
(~5400× empirical) with 2745 \(H_1\) bars. Candidate for a **better Big-O in
low-d Euclidean** (Delaunay size) if we quantify barcode distance vs VR.
Not a drop-in exact-VR replacement.

## Next levers (still open after I202)

Circle family: **84.4 / 119 / 140×**. Other families ~1.3–2.1×. Default is
shape-agnostic and exact; residual complexity is not.

1. **Default:** I193 + I197 + I202 gated witness.
2. **I203:** cofacet-walk early-stop (shape-agnostic reduce; less work, same PH).
3. **I204:** residual \(|E'(n)|\) log-log slopes across families — required
   before any Big-O claim. If torus/sphere stay \(\Theta(n^2)\), next
   construction is Alpha / sparse Rips with quantified topology loss.
4. Torus shift heap: time-bucket / later-bits only if I204 says collapse
   (not reduce) is still the wall after I203.
5. GPU later.
