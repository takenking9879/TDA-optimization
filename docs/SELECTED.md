# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I184. **Default collapse is I182 live-bit AND generate-C** on top of I155 pair-nbr + I156 fused first-apex. Flagship circle n=4000 T=1.5 is **22.8×** vs Ripser (I184). Optional suffix-* remain exact H1>10× on circle n=2000 T=1.5 only. `--collapse-alg back-src` is the pre-I182 src walk.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + lazy heap + cheap degree filter + I155 pair-nbr
times on live adjacency + **I182 live-bit AND generate-C**) → **Ripser-heap
implicit cohomology** on the residual flag graph (I137). I156 fused first-apex
is selected on top of this. `--collapse-alg back` uses bits (I184).

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
| circle_noisy | \(H_1\) | 4000 | 1.5 | **22.8×** default back-bits (I184: 293.8s/12.91s). I157 src-walk was 9.50× |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **8.89×** src-walk (I156); bits ~2.57× collapse (I182). suffix-* 2 unmatched |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **14.9×** default bits (I184) / **41.7×** suffix-stab (I168) / **17.1×** suffix-later K=2 (I181) |
| torus | \(H_1\) | 1000 | 1.6 | **1.31×** owned implicit (I139); E3 1.25× same run |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **4.13×** (I162) / 3.8–4.8× earlier |
| blobs / sphere / uniform2 | \(H_1\) | 2000 | default T | **0.17–0.32×** (I162) — collapse loses to Ripser |
| torus | \(H_1\) | 2000 | 1.6 | **0.74×** (I162); residual 163k |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; worst-case asymptotics.
**Honest H1>10× (exact, no oracle, default path):** circle n=4000 T=1.5 **22.8×** and n=2000 **14.9×** via I182/I184 bit-AND generate-C. Optional still higher on n=2000 only: suffix-stab **41.7×** (I168), suffix-later K=2 **17.1×** (I181).
I162: src-walk **loses** on blobs (0.32×), sphere (0.17×), uniform2 (0.30×), torus (0.74×). I182 blobs bits is only 1.25× collapse — I185 remasures losers under the new default.
I139: owned implicit **reduce 67 ms** on torus1000 residual 38k (homology was 1.7 s).
E3 (collapse + Ripser-sparse) is no longer required; we own that residual class.

**Alpha (I136)** is a different complex: GUDHI Alpha circle3000 0.023 s vs Ripser VR 123 s
(~5400× empirical) with 2745 \(H_1\) bars. Off the exact-VR 10× board.

## Next levers (still open after I184)

I184 selected bit-AND generate-C as default. Flagship **22.8×**. I162 losers and drop_live_nbr (`~m²/n` star scans) are the remaining collapse wall.

1. **Default:** I182/I184 back-bits. Flagship **22.8×** (circle n=4000 T=1.5).
2. I185: remasure I162 losers + circle n=3000 under bits default.
3. I186: O(1) drop_live_nbr (retire the swap-pop star scan).
4. Optional suffix-* still n=2000-only. GPU later.
