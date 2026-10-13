# Selected algorithm (living)

Updated 2026-10-13 after iterations I001–I157. I158 prefetch is the live collapse cut.

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
| circle_noisy | \(H_1\) | 4000 | 1.5 | **9.50×** (I157 pair-nbr+fused) / 8.74× (I148) / 8.38× (I117) |
| circle_noisy | \(H_1\) | 3000 | 1.5 | **8.89×** (I156) / 8.13× (I121) / 8.0× (I115) |
| circle_noisy | \(H_1\) | 2000 | 1.5 | **7.20×** (I156) / 6.52× (I155) / 6.30× (I140) |
| torus | \(H_1\) | 1000 | 1.6 | **1.31×** owned implicit (I139); E3 1.25× same run |
| circle_noisy | \(H_1\) | 2000 | 1.2 | **3.8–4.8×** |
| circle_noisy | \(H_1\) | 1000 | 1.5 | **4.1×** (I083) |

**Not claimed:** H1 10× clock in general; high-d; worst-case asymptotics.
I157: n=4000 T=1.5 is **9.50×** (Ripser 294 s / PITH 30.9 s, collapse 30.6 s, reduce 7.0 ms).
I148 was 8.74× / 33.5 s. Still collapse-bound; ~5% more collapse cut would hit 10× here.
I139: owned implicit **reduce 67 ms** on torus1000 residual 38k (homology was 1.7 s).
E3 (collapse + Ripser-sparse) is no longer required; we own that residual class.

**Alpha (I136)** is a different complex: GUDHI Alpha circle3000 0.023 s vs Ripser VR 123 s
(~5400× empirical) with 2745 \(H_1\) bars. Off the exact-VR 10× board.

## Next levers (still open after I154)

I153: C-build is the wall (567M probes / 1.12M dom tests / 96% first-apex hits).
~49% of probes miss and still paid two gathers. Domination levers are closed.

1. **I155 pair-nbr + I156 fused first-apex — selected.** Flagship **9.50×** (I157).
2. **I160 SoA live adjacency** (in flight). Layout only; probe count unchanged.
3. I158 prefetch and I159 sorted stars rejected on clock.
4. Fix D&C merge (I150) — parallel schedule only.
5. GPU later (Ripser++ reference only)
