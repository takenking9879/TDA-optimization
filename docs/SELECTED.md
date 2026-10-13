# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I193. **Default collapse is I193 multi-apex AND-eq** (I189 is the first candidate) on I182 live-bit C + I186 no LiveAdj. Flagship circle n=4000 T=1.5 is **113×** vs Ripser (I190); n=2000 is now **83.5×** (I193). I191 progressive ∩ was exact but slower on I162 losers — not selected. Optional suffix-* are no longer the clock leaders. `--collapse-alg back-src` is the pre-I182 src walk.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + I182 live-bit AND generate-C + I186 no LiveAdj +
**I193 multi-apex AND-eq** / later[] any_later; I189 is the first candidate)
→ **Ripser-heap implicit cohomology** on the residual (I137). `--collapse-alg
back` is this stack. `back-src` is the pre-I182 star walk.

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
| circle_noisy | \(H_1\) | 4000 | 1.5 | **113×** I190 AND-eq (300s/2.65s). I196 remasure pending |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **128×** I195 I193+I194 (123s/0.96s); I196 I193-only pending |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **83.5×** default I193 (29.1s/0.35s, collapse 270 ms). I189 was 71.0× |
| torus | \(H_1\) | 1000 | 1.6 | **1.31×** owned implicit (I139); E3 1.25× same run |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **4.13×** (I162) / 3.8–4.8× earlier |
| blobs | \(H_1\) | 2000 | 1.0 | **1.78×** I193 (was I189 0.48× / I162 0.32×) |
| sphere | \(H_1\) | 2000 | 1.4 | **1.96×** I193 (was I189 0.50× / I162 0.17×) |
| torus | \(H_1\) | 2000 | 1.6 | **1.18×** I193 (was I189 1.10× / I162 0.74×); residual 163k |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; worst-case asymptotics.
**Honest H1>10× (exact, no oracle, default path):** circle n=4000 T=1.5 **113×** (I190), n=3000 **93.2×** (I189), n=2000 **83.5×** (I193).
I193 vs Ripser at n=2000: blobs **1.78×**, sphere **1.96×**, torus **1.18×**. Still not a second-family 10×, but losers now beat Ripser.
I139: owned implicit **reduce 67 ms** on torus1000 residual 38k (homology was 1.7 s).
E3 (collapse + Ripser-sparse) is no longer required; we own that residual class.

**Alpha (I136)** is a different complex: GUDHI Alpha circle3000 0.023 s vs Ripser VR 123 s
(~5400× empirical) with 2745 \(H_1\) bars. Off the exact-VR 10× board.

## Next levers (still open after I195)

Circle family: **83.5 / 128× (I194-on) / 113×** at n=2000/3000/4000. I193 made blobs/sphere beat Ripser (1.78× / 1.96×). I194 rejected as default.

1. **Default:** I193 multi-apex AND-eq (I194 off). n=2000 **83.5×**.
2. I196: I193-only remasure n=3000/4000.
3. Shift-train AND-eq on torus `any_later` tail (~100k non-fast trims).
4. Second-pass collapse / RedZeD on torus residual 163k.
5. GPU later.
