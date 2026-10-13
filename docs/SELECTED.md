# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I172. Default collapse is I155 pair-nbr + I156 fused first-apex. Optional `--collapse-alg suffix-rescue` / `suffix-stab` are exact H1>10× on circle n=2000 T=1.5 only.

## Selected exact-VR CPU pipeline

**Name:** **PITH** — threshold graph \(G_T\) → backward flag **edge collapse**
(GUDHI sticky-dominator + lazy heap + cheap degree filter + I155 pair-nbr
times on live adjacency) → **Ripser-heap implicit cohomology** on the residual
flag graph (I137). I156 fused first-apex is selected on top of this.

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
| circle_noisy | \(H_1\) | 4000 | 1.5 | **9.50×** default back (I157). suffix-* not exact (I168–I172) |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **8.89×** default back (I156). suffix-* 2 unmatched |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **41.7×** suffix-stab (I168) / **36.5×** suffix-rescue (I172) / 7.20× default |
| torus | \(H_1\) | 1000 | 1.6 | **1.31×** owned implicit (I139); E3 1.25× same run |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **4.13×** (I162) / 3.8–4.8× earlier |
| blobs / sphere / uniform2 | \(H_1\) | 2000 | default T | **0.17–0.32×** (I162) — collapse loses to Ripser |
| torus | \(H_1\) | 2000 | 1.6 | **0.74×** (I162); residual 163k |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; worst-case asymptotics.
**Honest H1>10× (exact, no oracle):** circle n=2000 T=1.5 via `--collapse-alg suffix-stab` **41.7×** (I168) or `suffix-rescue` **36.5×** (I172). Both fail at n=3000/4000 (2 unmatched): ~100 nonempty-C **shift-keeps** (I170–I171) are not an oldest suffix.
I157 default back: n=4000 T=1.5 is **9.50×** (Ripser 294 s / PITH 30.9 s).
I162: at n=2000 the same default **loses** on blobs (0.32×), sphere (0.17×), uniform2 (0.30×), torus (0.74×).
I139: owned implicit **reduce 67 ms** on torus1000 residual 38k (homology was 1.7 s).
E3 (collapse + Ripser-sparse) is no longer required; we own that residual class.

**Alpha (I136)** is a different complex: GUDHI Alpha circle3000 0.023 s vs Ripser VR 123 s
(~5400× empirical) with 2745 \(H_1\) bars. Off the exact-VR 10× board.

## Next levers (still open after I172)

I153: C-build is the wall (567M probes / 1.12M dom tests / 96% first-apex hits).
I164/I170: n=2000 circle residual **is** an oldest suffix (5169/5169 last 6.25%). n=3000/4000 add ~100 earlier **shift-keeps** (nonempty C, almost all shifted to one grade ≈1.489). Early-stop and 6n prefix are dead. I171: those keeps are not C-empty, so abort-at-first-common over-trims.

1. **Default:** I155 pair-nbr + I156 fused first-apex. Flagship **9.50×** (I157).
2. **Optional exact H1>10× on circle n=2000:** `suffix-stab` 41.7× / `suffix-rescue` 36.5×. Do not default.
3. Predict / preserve the ~100 shift-keeps without walking every young star (needed for n=3000/4000 10×).
4. Skip-collapse cost model on I162 losers (Ripser is already cheaper than our C-walk).
5. Geometry C-query ceiling still ~2× on C-build. D&C merge (I150) still broken. GPU later.
