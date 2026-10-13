# RESEARCH_LOG

Very short ledger. Classes: proposal / experiment / reproduced / verified.
Do not paste long reasoning here.

---

## 2026-10-13 — methodology transfer

- **Question:** What of CrocSwap/integer-mult-bounds applies to TDA PH?
- **Hypothesis:** Process (pin baseline, one lever, receipts, archive failures) transfers; multiplication math does not.
- **Work:** Inspected upstream repo; wrote `docs/METHODOLOGY.md`.
- **Result:** Transfer list + iteration loop + evidence classes A/B/C.
- **Decision:** Use that loop. Do not copy κ/certificates/Lean.
- **Next:** Complexes + frameworks + papers.
- **Class:** verified (process only)

## 2026-10-13 — complexes map

- **Question:** Which complexes for first benchmarks?
- **Hypothesis:** VR is the exact reference; collapse/Alpha/sparse/witness are the work-reduction candidates.
- **Work:** Literature survey → `docs/COMPLEXES.md`.
- **Result:** Keep VR, edge-collapsed VR, Alpha (low-d), sparse Rips, lazy witness, cubical-on-grids.
- **Decision:** Default kernel stays flag/VR; Alpha is a different exact geometric filtration.
- **Next:** Framework comparison.
- **Class:** proposal (no new benches yet)

## 2026-10-13 — frameworks

- **Question:** Which engine is the CPU parent, which ideas cut work?
- **Work:** `docs/ALGORITHM_COMPARISON.md`. Cloned Ripser `01add51`, Ripser++ `30243c0`.
- **Result:** Parent = Ripser (MIT). Work-cutting ideas: collapse, apparent+clearing+cohomology (already in Ripser), Morse remainder, enclosing radius, Alpha/cubical when data allow. giotto-ph AGPL — ideas only. No GPU here; Ripser++ not built.
- **Decision:** Own MIT engine (PITH). Ripser++ is an unmodified local clone, not a remote fork.
- **Next:** Papers + collapse spec + implement.
- **Class:** experiment (inspection)

## 2026-10-13 — papers

- **Question:** Which papers must we read before inventing?
- **Work:** `docs/PAPERS.md` + 26 arXiv/open PDFs in `papers/`.
- **Result:** Must-read: Bauer Ripser, de Silva dualities, Chen–Kerber twist, Boissonnat–Pritam collapse, Sheehy sparse, giotto-ph, RedZeD, Bauer–Edelsbrunner Morse Čech.
- **Decision:** Distilled VR isomorphism treated as unverified. Do not shard-and-union diagrams.
- **Next:** Implement collapse + harness.
- **Class:** reproduced (downloads)

## 2026-10-13 — hypotheses ledger

- **Question:** What independent levers could give 10× less algebraic work than Ripser?
- **Work:** `docs/ALGORITHM_HYPOTHESES.md` (16 levers). Architecture name: **PITH**.
- **Result:** P0 = H01 collapse, H02 residual implicit cohomology, H03 \(G_T\), H04 extra Morse, H05 H0–H1 contract.
- **Decision:** Implement PITH v1 = threshold + backward collapse + implicit cohomology.
- **Next:** Code + unit tests + smoke benches.
- **Class:** proposal

## 2026-10-13 — PITH v1 implementation

- **Question:** Can we own an exact collapse + residual PH engine?
- **Hypothesis:** Backward collapse (GUDHI/2022) + leftover-edge coboundary reduction is exact for VR≤T.
- **Work:** `src/pith/*`, unit tests C4 / C4+diagonal / triangle, dataset generator, `benchmarks/run_suite.py`.
- **Result:** Collapse unit tests pass. Smoke E3 (collapse→Ripser) identity **12/12 later in I001**. Own reducer matches circle n=80 with collapse, fails otherwise.
- **Decision:** Select collapse. Do not select owned reducer.
- **Next:** Measure ratios; iterate levers.
- **Class:** experiment / partially verified

## 2026-10-13 — I001 H01 collapse ratio

- **Question:** Is \(n/n_c \ge 10\) on typical clouds with exact identity?
- **Hypothesis:** Geometric low-d yes; high-d noise no.
- **Work:** E3 vs Ripser, n=80/200, six families.
- **Result:** All 12 E3 matches. Ratios: circle 14–29×, blobs 7–15×, sphere 5–12×, uniform2 4–10×, torus ~3.8×, uniform10 2–3.7×. Median-all = 7.3 (hold if high-d included). Typical geometric n=200 median ≥10×.
- **Decision:** Support H01 on low-d geometric; keep high-d as negative control. Selected pipeline PITH-E3.
- **Next:** iterated collapse; threshold sweep; own core.
- **Class:** reproduced

## 2026-10-13 — I002 iterated collapse

- **Question:** Do extra passes shrink circles further?
- **Result:** n=80: 93 stays. n=200: 283→281. Identity kept.
- **Decision:** Default `nb_iterations=1`. Extra passes not a 10× lever here.
- **Next:** H02 / H03.
- **Class:** experiment (negative, keep)

## 2026-10-13 — I003 own reducer without collapse

- **Question:** Is the PITH cohomology core exact on \(G_T\)?
- **Result:** Reject. circle80 1137 unmatched; blobs80 953 unmatched. Behaves like unreduced leftover edges (empty/failed coboundary reduction on dense graphs).
- **Decision:** Residual engine remains stock Ripser. Fix later.
- **Next:** H03.
- **Class:** experiment (failure archived)

## 2026-10-13 — I004 threshold sweep circle200

- **Question:** Does a larger \(T\) grow the residual?
- **Hypothesis:** Dominated chords trim; residual ~1-skeleton of the hole stays flat.
- **Result:** Residual **283 edges for every \(T\in[0.4,1.5]\)**. Ratio 9→38×. Residual Ripser 1.6 ms vs dense 15.8 ms at \(T=1.5\). All exact.
- **Decision:** Support H03 as the partner of H01. Enclosing-radius / large T is where collapse wins most.
- **Next:** larger n, \(H_2\), torus remainder, faster collapse, fix reducer.
- **Class:** reproduced

## 2026-10-13 — I005 scale + H2

- **Question:** Does the edge 10× survive n=500 and \(H_2\)?
- **Result:** circle500: 53× edges, identity, residual PH 48×, collapse ≈ Ripser time. sphere80/200 \(H_2\): identity. sphere200 \(H_2\): 12× edges, **6.8× total wall-clock**.
- **Decision:** \(H_2\) is where collapse pays in wall-clock. H1 still collapse-bound.
- **Next:** n=1000 / sphere500.
- **Class:** reproduced

## 2026-10-13 — I006 circle1000 + sphere500 H2

- **Result:** circle1000: **90× edges**, residual PH **175×**, collapse 1.64 s > Ripser 0.89 s (total 0.54×). sphere500 \(H_2\): **37× edges**, residual **502×**, **11.6× total wall-clock**, exact \(H_0\)–\(H_2\).
- **Decision:** 10× total time achieved on sphere \(H_2\). H1 needs faster collapse.
- **Next:** n=500 other families; dense collapse.
- **Class:** reproduced

## 2026-10-13 — I007 n=500 H1 others

- **Result:** blobs 32× edges, uniform2 25×, sphere 37×, torus 3.4×. All exact. Total wall-clock <1× (collapse). Residual 3–10×.
- **Decision:** Torus remains the geometric hold-out (~3–4× edges).
- **Next:** Faster collapse (implementation).
- **Class:** reproduced

## 2026-10-13 — I008 dense-lookup collapse

- **Question:** Can an implementation change realize more of the H01 work cut?
- **Result:** Same edge counts / identity. circle1000 collapse 1.64→0.48 s, total **2.0×** vs Ripser. sphere500 \(H_2\) total **25×**.
- **Decision:** Keep dense collapse as default for n≲4e3. Still not 10× total on H1.
- **Next:** Better collapse asymptotics, fix owned reducer, Alpha, torus Morse.
- **Class:** experiment (implementation)

## 2026-10-13 — I009 GUDHI collapse oracle + Alpha

- **Question:** Does our residual 1-skeleton match GUDHI `collapse_edges`?
- **Result:** Edge counts identical on circle80/200, blobs80, uniform2-200, sphere80. Alpha on circle200 is a *different* complex (long H1 dies; VR essential). GUDHI Alpha 1.9 ms vs GUDHI Rips 81 ms (empirical, not exact-VR).
- **Decision:** Collapse implementation verified against GUDHI. Alpha stays a separate Euclidean candidate, not a VR replacement.
- **Next:** Own reducer still rejected (map rewrite unchanged I003 failure). Torus Morse / faster collapse / larger H2.
- **Class:** reproduced (collapse); empirical (Alpha)

## 2026-10-13 — I010 owned H1 via triangle boundaries

- **Question:** Does reducing triangle boundaries over leftover edges fix H02?
- **Result:** Identity vs Ripser on 6/6, including collapse=0 dense circle/blobs. Previous coboundary-of-edges reducer was the bug.
- **Decision:** Select owned H1 reducer.
- **Next:** H2 + scale.
- **Class:** reproduced

## 2026-10-13 — I011 owned pipeline scale

- **Result:** 10/10 exact including sphere \(H_2\). sphere500 \(H_2\): **57×** vs Ripser. circle1000 \(H_1\): 90× edges, 2.6× time. Live-neighbor collapse 318 ms.
- **Decision:** Residual engine is ours; Ripser is oracle only.
- **Next:** GUDHI/Alpha/kNN/witness/torus.
- **Class:** reproduced

## 2026-10-13 — I012 GUDHI collapse time

- **Result:** Edge counts still match. Our collapse **faster** than GUDHI (circle1000 320 vs 574 ms).
- **Decision:** Keep our collapser.
- **Class:** reproduced

## 2026-10-13 — I013 Alpha vs VR

- **Result:** GUDHI Alpha sphere500 \(H_2\) 9 ms vs Ripser VR 3.6 s (396×) but **different complex**.
- **Decision:** Other-complex fast path only. Not selected for exact VR.
- **Class:** experiment (empirical)

## 2026-10-13 — I014–I015 kNN / witness

- **Result:** kNN k=16 matched VR on one circle (fluke). Witness 1-skeletons are tiny, different estimator.
- **Decision:** Reject as exact-VR.
- **Class:** experiment (negative)

## 2026-10-13 — I016 torus

- **Result:** Exact \(H_1\)/\(H_2\). Ratios 2–4×. n=500 \(H_1\) we lose wall-clock (0.26×).
- **Decision:** Thick remainder; try extra collapse passes later.
- **Class:** reproduced

## 2026-10-13 — I017 enclosing radius

- **Result:** \(T=\infty\) capped by \(R\) ≠ protocol \(T=1.2\) on circle200 (more edges, different module).
- **Decision:** Do not silently replace protocol \(T\).
- **Class:** experiment

## 2026-10-13 — I018 high-d noise

- **Result:** Exact. Ratios 2–3.7×. n=200 we are 36× slower (dense collapse).
- **Decision:** Negative control stands.
- **Class:** reproduced

## 2026-10-13 — I019 GUDHI explicit Rips

- **Result:** sphere500 \(H_2\): GUDHI 97 s / 1.17e8 simplices vs PITH 86 ms → **1134×**. Different baseline than Ripser.
- **Class:** reproduced

## 2026-10-13 — I020 circle n=1500

- **Result:** Exact. **127×** edges, 3.1× wall-clock, collapse 1.09 s / reduce 1.0 ms.
- **Decision:** H1 10× clock still collapse-bound; trend up with \(n\).
- **Class:** reproduced

## 2026-10-13 — I021 kNN more clouds

- **Result:** k=16 matches circles only; blobs/uniform/torus fail.
- **Decision:** Confirm reject-as-exact.
- **Class:** experiment (negative)

## 2026-10-13 — I022 H1 vs H2 cost

- **Result:** sphere500 collapse dominates; H2 adds ~0.6 ms after collapse.
- **Class:** experiment

## 2026-10-13 — I023 column work before/after collapse

- **Result:** circle80 **731×** fewer columns; blobs200 **505×**; sphere80 \(H_2\) **240×**.
- **Decision:** 10× algebraic-work target is met by a large margin on typical clouds.
- **Class:** reproduced

## 2026-10-13 — I024 owned reducer without collapse

- **Result:** Exact on circle200/500. Much slower than Ripser (materialized triangles).
- **Decision:** Collapse remains mandatory for speed.
- **Class:** reproduced

## 2026-10-13 — I025 cubical grid

- **Result:** 32² image, GUDHI cubical 1 ms, one \(H_1\). Not a point-cloud VR substitute.
- **Class:** experiment

## 2026-10-13 — I026 multi-pass collapse

- **Result:** Torus200: 1260→1023→977. Circle200: 283→281. Default stays 1 pass.
- **Class:** experiment

## 2026-10-13 — I027 degree-first collapse

- **Question:** Does trying high-degree apexes first speed collapse?
- **Result:** Exact, but **slower** (circle1000 453 vs 318 ms). Overhead > savings.
- **Decision:** Revert heuristic; keep buffer reuse + lazy `C_later` sort.
- **Class:** experiment (negative)

## 2026-10-13 — I028 torus multi-pass

- **Result:** torus500 3 passes: 8825→5735 edges, still 0.54× vs Ripser. Exact.
- **Class:** experiment

## 2026-10-13 — I029 sphere T sweep H2

- **Result:** All exact. Speedup **4.0× at T=0.8 → 14.4× at T=1.4**.
- **Decision:** Larger T favors PITH (Ripser clique work grows faster).
- **Class:** reproduced

## 2026-10-13 — I030 H0-only

- **Result:** Exact. We lose (0.25–0.36×). Collapse is wasted if only \(H_0\).
- **Decision:** Do not use PITH as an H0-only MST replacement.
- **Class:** experiment (negative)

## 2026-10-13 — I031–I034 more geometry

- **Result:** Exact on new seed, σ∈{0.01..0.2}, two circles (2 essential \(H_1\)), figure-8. Cleaner circles collapse more (40× at σ=0.01).
- **Class:** reproduced

## 2026-10-13 — I035–I037 annulus / swiss / 3d blobs

- **Result:** All exact. Annulus 23× / 1.7× time. Swiss 8.7× / 0.87×. Blobs3d 14× / 0.81×.
- **Class:** reproduced

## 2026-10-13 — I038–I039 residual density

- **Result:** Residual mean degree: circle 2.83, sphere 8.2, torus 12.6, uniform10 95. Explains who gets 10×.
- **Class:** experiment (diagnostic)

## 2026-10-13 — I040–I042 Alpha cells / RP2 / sphere H1

- **Result:** Alpha still other-complex. PITH has no distance-matrix CLI (I041 hold). Sphere H1 ~1.1–1.2×.
- **Class:** experiment

## 2026-10-13 — I043 adaptive collapse policy

- **Question:** Extra passes only when residual mean degree \(>6\)?
- **Result:** Exact. Circle unchanged. Torus200 1260→977 and **1.05×** vs Ripser (was 0.87×). Sphere200 819→624.
- **Decision:** Default CLI `--collapse -1` (adaptive).
- **Class:** reproduced

## 2026-10-13 — selected writeup

- **Decision:** PITH with owned PH + adaptive collapse. See `docs/SELECTED.md`.
- **Class:** verified (selection, scoped)

## 2026-10-13 — I044 sticky collapse

- **Question:** Does GUDHI’s sticky-dominator + lazy `C_later` heap speed exact collapse?
- **Result:** Identity 4/4 (circle/blobs/sphere). Counts unchanged. circle1000 collapse 324 ms (was 318). **No wall-clock win.**
- **Decision:** Keep (GUDHI-parity inner loop). Not a 10× lever.
- **Class:** experiment (implementation, negative for speed)

## 2026-10-13 — I045–I046 implicit cohomology

- **Question:** Does leftover-edge coboundary with *triangle* rows fix I003?
- **Result:** collapse=0: wrong (1147 unmatched) or OOM before F2 maps. After collapse: still wrong on blobs/torus/sphere/circle200. Only a near-cycle residual matches (I068 circle80).
- **Decision:** Reject as engine. `--engine implicit` stays experimental. Auto = homology.
- **Class:** experiment (failure archived)

## 2026-10-13 — I047 / I059 H1 scale

- **Result:** Exact. circle1500 **3.44×** / 124× edges. circle2000 **4.60×** / **159×** edges, collapse 2.63 s / reduce 1.7 ms.
- **Decision:** H1 10× clock still collapse-bound; ratio grows with n and with T (I062: 1.5× at T=0.6 → 4.6× at T=1.5 on n=500).
- **Class:** reproduced

## 2026-10-13 — I048 / I055 high-d skip

- **Question:** Skip collapse when domination probe is low?
- **Result:** Probe did not fire. Forced skip+homology on uniform10 n=200: **0.005×** vs Ripser (3.5 s). Collapse+homology 0.07× — still lose, but skip is worse.
- **Decision:** Do not skip collapse on high-d while the engine is `persist_sparse`.
- **Class:** experiment (negative)

## 2026-10-13 — I050 / I066 sphere H2

- **Result:** Exact. n=200 **14×**, n=500 **57×**. T-sweep still exact.
- **Class:** reproduced

## 2026-10-13 — I051 distance CLI

- **Result:** Square CSV `--distances` matches Ripser point-cloud (circle80).
- **Decision:** I041 hold closed for square matrices.
- **Class:** reproduced

## 2026-10-13 — I052 / I067 H0 skip

- **Result:** `--collapse -1` + `maxdim=0` skips collapse. circle1000 H0 **1.25×** vs Ripser (was 0.25–0.36×).
- **Decision:** Keep.
- **Class:** reproduced

## 2026-10-13 — I053 / I056 reduced VR (H07)

- **Result:** Essential H1 counts match n≤30; finite bars over-count (every triangle). Triangle count ≪ \(\binom{n}{3}\).
- **Decision:** Reject current prototype as exact PH. Size claim still interesting.
- **Class:** experiment (negative for barcodes)

## 2026-10-13 — I054 / I057 / I061

- **Result:** This GUDHI 3.13 wheel has no `flag_filtration`. Sheehy sparse ≠ exact VR (I057). RP2 n=600 `--distances` parses; collapse timed out at 180 s.
- **Class:** hold / reject-as-exact

## 2026-10-13 — I058 / I070 column remainder

- **Result:** Uncollapsed→collapsed columns: circle200 **1964×**, torus200 **18×**, sphere80 H2 **240×**. Residual after collapse is tiny on circles ⇒ H04 extra Morse is not a 10× lever.
- **Class:** experiment (diagnostic)

## 2026-10-13 — I060 / I063 / I064 / I069

- **Result:** Geometry recheck exact. Torus500 adaptive 0.78× vs Ripser (better than 1-pass 0.46×, still lose). blobs/uniform2/sphere n=500 H1 we lose wall-clock (0.57–0.79×) despite 25–34× edges. Seeds/σ exact.
- **Class:** reproduced

## 2026-10-13 — I065 Alpha

- **Result:** Alpha ≠ VR. Other-complex only.
- **Class:** experiment (empirical)

## 2026-10-13 — selected after I070

- **Decision:** Selected stack unchanged: collapse + triangle-boundary homology. Sticky inner loop kept. Implicit coh / reduced-VR-PH / high-d skip / Sheehy rejected. Distance CLI added. See `docs/SELECTED.md`.
- **Next:** faster collapse (still the only H1 10×-clock path); do not stop at 70 iterations.
- **Class:** verified (selection, scoped)

## 2026-10-13 — I071–I081 bitset domination

- **Question:** Does live-neighborhood bitset AND cut \(O(|C|^2)\) domination?
- **Result:** Exact (5/5 + matching I044 counts). **Slower**: circle2000 collapse 5.8 s vs 2.6 s. Existence-AND leaves too many Tm candidates.
- **Decision:** Revert bitset from the hot path (I081).
- **Class:** experiment (negative)

## 2026-10-13 — I082 degree filter

- **Question:** Skip apexes with live degree \(< |C|-1\)?
- **Result:** Exact. circle1000 315 ms (≈ I047 324 ms). Wash.
- **Decision:** Keep as a sound cheap filter.
- **Class:** experiment (implementation)

## 2026-10-13 — I083 / I096 large T

- **Result:** circle1000 T=1.5: **4.1×**. circle2000 T=1.5: residual still 5158 edges, Ripser 32.5 s, PITH 4.5 s → **7.2×**. T=1.8 on n=1000 residual grew and ratio fell to 3.2×.
- **Decision:** Larger T (below fill-in) is where H1 clock approaches 10×. Not yet 10× at n=2000.
- **Class:** reproduced

## 2026-10-13 — I084–I095 / I097–I100

- **Result:** Geometry/H2/H0/blobs/high-d exact after revert. Sphere500 \(H_2\) **59×**. Torus200 adaptive 0.96×. Alpha ≠ VR (9 ms vs Ripser VR 3.7 s). Time-axis D&C is parallel-only (I088). Implicit still rejected (I094). circle80 columns still **731×**. Residual deg: circle 4.5, sphere 7.2, torus 35, uniform10 95. Two circles: 2 essential \(H_1\). RedZeD still unimplemented (I099).
- **Decision:** Selected stack unchanged. See `docs/SELECTED.md`.
- **Class:** reproduced / hold

## 2026-10-13 — I100 named-iteration count

- **Result:** Receipts I001–I100 exist. Algebraic 10× holds. H1 wall-clock 10× is **not** general (best 7.2× at circle2000 T=1.5). Credible directions remain: cheaper collapse, correct implicit/RedZeD, thick-remainder engine.
- **Decision:** Do not declare the research goal complete.
- **Class:** verified (count only)

## 2026-10-13 — I101–I102 progressive intersection

- **Question:** Does ∧_w N_t[w] ∩ C with early empty abort beat first-candidate domination?
- **Result:** Exact (I101 5/5). **Reject on clock:** circle2000 T=1.5 still in collapse at 136 s vs I096 4.5 s. Same trap as bitset (I071): the common path is “first apex works”; a full intersection always pays O(|C|²).
- **Decision:** Revert hot path to `first_dominator_deg`. Keep `first_dominator_prog` archived in the header.
- **Next:** max-degree-first (I106); MST-apparent implicit fix (I111); incomplete collapse if residual PH stays cheap.
- **Class:** experiment (negative on time; identity archived)

## 2026-10-13 — I106 max-degree-first

- **Question:** Does trying the max-degree eligible apex first cut failed `dominated_by` scans?
- **Result:** Exact 5/5. circle2000 T=1.5 **6.2×** / 4495 ms collapse vs I096 **7.2×** / ~4.5 s total. circle1000 334 ms vs I082 315 ms. Extra argmax pass + worse sticky apex choice.
- **Decision:** Revert order to list-order `first_dominator_deg`. Keep `--dom-budget` for incomplete collapse (I107).
- **Class:** experiment (negative on clock)

## 2026-10-13 — I107 budgeted collapse

- **Question:** Can we skip failed domination searches (`--dom-budget 1`) and still get a thin residual?
- **Result:** Reject. circle2000 T=1.5 budget=1 still in pith at 142 s (full collapse 4.5 s). A first-candidate miss leaves a thick flag complex; `persist_sparse` then explodes.
- **Decision:** Do not cap domination search while the residual engine is triangle-boundary homology.
- **Class:** experiment (negative)

## 2026-10-13 — I108–I110

- **Result:** Held. I107 failed before identity/H2/n=3000 budgeted runs.
- **Class:** hold

## 2026-10-13 — I111–I113 implicit MST-apparent

- **Question:** Does recording Bauer-apparent pairs on MST facets fix leftover-as-cohomology?
- **Result:** C8 unit test matches homology. circle80 **collapse=1** matches Ripser (5 H1). Dense collapse=0 still ~1 bar per leftover (circle80 unmatched 1147, circle200 7913). circle200 collapse=1: 2 unmatched. Thick implicit killed (uniform10 65 s).
- **Decision:** Still reject implicit as engine. Thin-cycle residual is the only passing case.
- **Class:** experiment (failure archived; partial support on collapsed circle80)

## 2026-10-13 — I114 reserve + in-place sort

- **Result:** Exact. circle2000 T=1.5 **6.35×** / 4.28 s (Ripser 27.2 s this run; I096 Ripser was 32.5 s). Collapse 4212 ms. Hygiene, not a 10× lever.
- **Decision:** Keep reserve + in-place sort.
- **Class:** implementation

## 2026-10-13 — I115 circle n=3000

- **Result:** Exact. T=1.2 **5.1×** (Ripser 43.6 s / PITH 8.6 s, residual 8325). T=1.5 **8.0×** (Ripser 114.5 s / PITH 14.3 s, residual 9190). Ratio still rising with n at large T.
- **Decision:** Run n=4000 T=1.5 (I117). Do not claim H1 10× yet.
- **Class:** reproduced

## 2026-10-13 — I116 sphere500 H2

- **Result:** Exact. **45.7×** this run (I085 was 59×; Ripser variance). Residual 1900 edges.
- **Class:** reproduced

## 2026-10-13 — I117 circle n=4000

- **Result:** Exact. T=1.2 **5.94×**. T=1.5 **8.38×** (Ripser 287 s / PITH 34.3 s, residual 12562). Not 10×. Diminishing returns vs n=3000 (8.0×).
- **Decision:** Do not claim H1 10×. T-sweep next, not n=5000.
- **Class:** reproduced

## 2026-10-13 — I118 torus200

- **Result:** Exact. 1-pass 0.71×; adaptive **1.12×** (was 0.96×). Still a hold-out.
- **Class:** reproduced

## 2026-10-13 — I119 circle3000 T-sweep

- **Result:** Exact. T=1.35 **6.41×** / residual 8325. T=1.45 **7.52×** / 8325. T=1.55 **7.68×** / 11542. T=1.65 **6.59×** / 16770. Peak remains T≈1.5 (I115 **8.0×**).
- **Decision:** Do not move the protocol T off 1.5 for H1 clock claims.
- **Class:** reproduced

## 2026-10-13 — I120 high-d control

- **Result:** Exact. uniform10 n=200: 1-pass **0.05×**, adaptive **0.12×**. Still a negative control.
- **Class:** reproduced

## 2026-10-13 — I121 row pointers

- **Result:** Exact. circle2000 T=1.5 collapse 4137 ms vs I114 4212 ms (~2%). **6.63×**. circle3000 T=1.5 **8.13×** / 13833 ms vs I115 8.0× / 14123 ms.
- **Decision:** Keep row pointers + degree-reserve. Not a 10× lever.
- **Class:** implementation

## 2026-10-13 — I126–I127 same-diameter apparent

- **Question:** Does Ripser same-diameter apparent (not globally youngest cofacet) fix leftover-as-cohomology?
- **Result:** Still 1/7 (only collapsed circle80). Dense unmatched 1147/7913. Torus/sphere collapse=1 still wrong. Thick implicit slower and wrong.
- **Decision:** Implicit remains rejected. MST edges are short; same-diameter pairs are longest-edge triangles, so the I111 MST story was the wrong pairing class.
- **Class:** experiment (failure archived)

## 2026-10-13 — I128 -march=native -flto

- **Result:** Exact. **Slower**: circle2000 4475 ms / 6.24× vs I121 4137 ms / 6.63×. circle3000 7.68× vs 8.13×.
- **Decision:** Revert to `-O3` only.
- **Class:** experiment (negative)

## 2026-10-13 — I129 torus500

- **Result:** Exact. 1-pass **0.41×**, adaptive **0.71×**. Residual 9112 / 6078.
- **Decision:** Thick torus remains a hold-out.
- **Class:** reproduced

## 2026-10-13 — I131 sequential C-scan

- **Result:** Exact (same residuals 5169 / 9190). **Slower**: circle2000 5.83× / 4462 ms vs I121 6.63× / 4137 ms. circle3000 7.37× vs 8.13×. Different `C_now` order changes first-apex / sticky work.
- **Decision:** Revert to neighbor-list gather + row pointers.
- **Class:** experiment (negative)

## 2026-10-13 — I132 collapse + Ripser-sparse (E3)

- **Result:** Exact 4/4. torus500 **1.14×** vs Ripser (owned homology was 0.71×). circle80 0.75× (process overhead). torus200 0.76×.
- **Decision:** E3 is the better *thick-residual* engine. Not a circle H1 10× lever (collapse-bound).
- **Class:** reproduced

## 2026-10-13 — I133 / I134

- **Result:** sphere500 H2 **46.5×** after seqscan (still exact). torus1000 homology **0.21×** / adaptive **0.34×**, residual 27k–38k. Collapse already > Ripser (1.2 s vs 0.40 s).
- **Class:** reproduced

## 2026-10-13 — I135 E3 torus1000

- **Result:** Exact. 1-pass collapse 0.25 s + Ripser-sparse 0.056 s = **1.31×** vs Ripser 0.41 s. Adaptive extra collapse 0.97×. Owned homology was 0.21× because persist_sparse spent ~1.7 s on 38k residual edges.
- **Decision:** E3 is the correct thick-residual engine. persist_sparse stays for thin residuals only.
- **Class:** reproduced

## 2026-10-13 — I136 GUDHI Alpha circle3000

- **Result:** Alpha 0.023 s vs Ripser VR 123 s (~5400×) but 2745 \(H_1\) bars — **other complex**, not exact VR.
- **Decision:** Document only. Off the 10×-exact board.
- **Class:** experiment (empirical)

## 2026-10-13 — I103–I105

- **Result:** Skipped. They required the progressive binary on n=500–3000 after I102 failed.
- **Class:** hold

## 2026-10-13 — I137 Ripser-heap implicit

- **Question:** Does a faithful Ripser compute_pairs port (oldest F₂ pivot, same-diameter apparent/emergent, V-matrix) fix leftover-as-cohomology?
- **Hypothesis:** I045–I126 failed because the pivot was the youngest cofacet and apparent required an equilateral triangle (shortest facet = diameter).
- **Work:** Rewrote `persist_implicit_coh`. K6 unit test + I137 suite.
- **Result:** Exact **8/8** including circle80/200 **collapse=0** (I045 killer). circle80 c=0: 1177 apparent, 5 reduced, 0.73 ms.
- **Decision:** Select heap implicit. `--engine auto` → implicit.
- **Class:** reproduced / verified

## 2026-10-13 — I138 heap clock n=200

- **Result:** Exact. torus200 c=1 implicit **1.03×** (homology 0.79×). torus200 c=0 implicit **0.75×** (homology 0.10×).
- **Class:** reproduced

## 2026-10-13 — I139 torus1000 owned E3

- **Result:** Exact. implicit 1-pass **1.31×** (reduce 67 ms / collapse 226 ms) vs Ripser 0.40 s. Homology 0.20× (reduce 1744 ms). E3 1.25× (Ripser-sparse 57 ms). Adaptive implicit 1.04×.
- **Decision:** We **own** the thick-residual engine. E3 no longer required. persist_sparse stays as H2 fallback / A/B.
- **Class:** reproduced

## 2026-10-13 — I140 circle2000 implicit

- **Result:** Exact. implicit **6.30×** vs homology 6.32× (collapse-bound, residual 5169).
- **Decision:** Implicit is not a circle-H1 10× lever. Re-open budgeted collapse (I107 stale).
- **Class:** reproduced

## 2026-10-13 — I141 auto=implicit

- **Result:** Exact 3/3. Pipeline string `+implicit_coh`.
- **Decision:** Keep auto → implicit.
- **Class:** implementation

## 2026-10-13 — I142–I144 budget + implicit

- **Question:** Does `--dom-budget K` plus implicit beat full collapse now that thick residuals are cheap?
- **Result:** Exact but **reject on clock**. circle2000: full 5.94× / 4.3 s; budget=1 1.32× (collapse 10.4 s + reduce 8.9 s, residual 598k); budget=4 4.31×. No-collapse implicit 0.60× (42 s). circle3000: full **8.11×**; budget=1 **1.49×** (residual 1.51M). Incomplete collapse is *more* collapse work (failed trims keep high degree) plus a thick implicit.
- **Decision:** I107 rejection stands even with implicit. Do not cap domination search.
- **Class:** experiment (negative on clock; identity archived)

## 2026-10-13 — I149 forward collapse

- **Question:** Is Boissonnat–Pritam 2020 forward faster and exact vs backward?
- **Result:** **Reject.** Not exact: circle80 unmatched 4, circle200 39, torus80 62. Residual smaller than backward (88 vs 93; 240 vs 283). Also slower (circle200 4.95 ms vs 2.72 ms).
- **Decision:** Keep `--collapse-alg forward` as archived experiment. Default stays backward.
- **Class:** experiment (failure archived)

## 2026-10-13 — I150 time-axis D&C implemented

- **Question:** Does a 2-thread Glisse Lemma 6 schedule beat sequential collapse on wall-clock while staying exact?
- **Result:** PH match on n=80/200. **Fails** circle2000 (19 unmatched) and circle3000 (25 unmatched). Clock: **no win** (circle2000 4293 vs 4149 ms; circle3000 14120 vs 13943 ms). Extra left-call + merge ≥ sequential.
- **Decision:** Do not select. I088 stand holds: parallel schedule, not less work, and this merge is not yet Lemma-6-faithful at scale.
- **Class:** experiment (negative)

## 2026-10-13 — I148 circle4000 implicit

- **Question:** Does the selected implicit engine move the I117 H1 flagship?
- **Result:** Exact. **8.74×** (Ripser 293 s / PITH 33.5 s, collapse 33.2 s, reduce **6.6 ms**, residual 12562). I117 was 8.38× / 34.3 s homology. Implicit does not change the collapse wall. Not 10×.
- **Decision:** New best H1 clock, still collapse-bound. 10× H1 needs cheaper collapse.
- **Class:** reproduced

## 2026-10-13 — I147 AVX-512 domination

- **Question:** Do AVX-512 gathers speed the \(O(k)\) `dominated_by` row scan?
- **Result:** Exact. **No collapse_ms win.** circle2000 4222 ms vs I140 4212 ms; circle3000 14084 ms vs I144 13885 ms. Ratios 6.50× / 8.34× are Ripser variance. Gather latency ≥ scalar on this 4-core VM.
- **Decision:** Revert. Do not add SIMD to the selected path without a measured collapse_ms cut.
- **Class:** experiment (negative)

## 2026-10-13 — I146 sorted-merge C

- **Question:** Is a vertex-sorted merge cheaper than gathering the smaller neighborhood?
- **Result:** Exact. **Reject on clock.** circle2000 4.43× / 6329 ms vs I140 6.30× / 4212 ms. circle3000 5.32× / 22.1 s vs 8.11× / 13.9 s. Merge walks both lists; the smaller-nbr gather already skips non-commons after two loads and hits cache better.
- **Decision:** Revert to smaller-nbr gather + swap-drop.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I145 hybrid dominator

- **Question:** Does first-2 `dominated_by` then progressive ∩ cut leftover-edge \(O(k^2)\)?
- **Result:** Exact. **Reject on clock.** circle2000 5.88× / 4606 ms vs I140 6.30× / 4212 ms. circle3000 6.90× / 17.0 s vs I144 8.11× / 13.9 s. Too many edges miss the first two apexes and pay progressive.
- **Decision:** Revert call site to `first_dominator_deg`. Keep `first_dominator_hybrid` archived.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I143 dense implicit vs Ripser

- **Result:** Exact. collapse=0 implicit is **0.62×** vs Ripser at n=200/500/1000 T=1.5. Our heap port is correct but slower than Bauer on dense \(G_T\).
- **Decision:** Collapse remains mandatory for H1 clock. Implicit wins on *collapsed* thick residuals, not on raw \(G_T\).
- **Class:** reproduced

## 2026-10-13 — I151 collapse profile (counters not copied)

- **Question:** Is C-build or domination the collapse wall?
- **Result:** Identity exact, but printed `c_probes`/`dom_*` were **0** — persist Result overwrote Counters; main only copied trims/shifts.
- **Decision:** Do not trust I151 mix. Fix copy, remasure (I153).
- **Class:** experiment (instrumentation miss)

## 2026-10-13 — I152 forward at current grade

- **Question:** Does testing secondary domination at \(t(e_i)\) (not \(t(e_j)\)) make 2020 forward exact?
- **Result:** Exact **4/4** (circle/torus n=80/200). Residuals match backward (93/283). Small-n clock still slower than backward.
- **Decision:** I149 over-collapse was the wrong grade. Identity restored. Scale clock = I154.
- **Class:** reproduced / verified (identity)

## 2026-10-13 — I153 collapse profile v2

- **Question:** What is the C-probe vs domination mix with counters copied?
- **Result:** circle2000: 567M C-probes, 290M commons, 1.12M dom tests, **96%** first-apex hits, collapse 4253 ms, **6.47×**. circle3000: 1.92B probes, 90% hits, 14622 ms, **7.88×**. ~49% of probes miss and still paid two DenseTimes gathers.
- **Decision:** Domination is not the wall. C-build is. Next: store times on live nbr (I155).
- **Class:** reproduced

## 2026-10-13 — I154 exact forward at n=2000

- **Question:** Does exact forward beat backward on circle2000 T=1.5?
- **Result:** Exact, same residual 5169. Forward 6781 ms / 4.20× vs backward 4253 ms / **6.66×**.
- **Decision:** Reject on clock. Default stays backward.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I155 pair-nbr one-gather

- **Question:** Does storing `(w,t)` on live adjacency cut C-build from two gathers to one?
- **Result:** Exact 4/4. Residuals match I153 (93/283/5169/9190). Probe count unchanged. circle2000 collapse **4068 vs 4253 ms** (1.05×); **6.52×** vs Ripser. circle3000 **13536 vs 14622 ms** (1.08×); **8.18×**. Shift lookups 4799 vs 567M probes — shift is not the wall. Two-row gathers were already L1-resident; not a 2× lever.
- **Decision:** **Select** (small exact win). Next: skip the separate domination pass (I156).
- **Class:** reproduced

## 2026-10-13 — I156 fused first-apex

- **Question:** Trim when the first common dominates and `C_later` is empty, without materializing `C`?
- **Result:** Exact 4/4. Residuals unchanged. Fast-trims 1.04M / 1.07M on circle2000. collapse **3746 vs I155 4068 ms**. Ratios **7.20×** (n=2000), **8.89×** (n=3000).
- **Decision:** **Select.** Stack is pair-nbr + fused first-apex.
- **Class:** reproduced

## 2026-10-13 — I157 circle4000 after I155+I156

- **Question:** Does the new stack move the I148 H1 flagship (8.74×)?
- **Result:** Exact, residual 12562. Ripser 294 s / PITH 30.9 s, collapse 30.6 s, reduce 7.0 ms. **9.50×**. Need ~5% more collapse cut for 10× on this flagship.
- **Decision:** New best H1 clock. Still collapse-bound. Not 10×.
- **Class:** reproduced

## 2026-10-13 — I158 prefetch C-walk

- **Question:** Do +8 software prefetches of `r_other[w]` / `r_first[w]` cut collapse_ms?
- **Result:** Exact, same residuals. **Reject on clock.** circle2000 3912 vs I156 3746 ms; circle3000 13027 vs 12606 ms.
- **Decision:** Revert prefetch. Rows already L1-resident.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I159 vertex-sorted live stars

- **Question:** Does sorting each live star by vertex id make C-walk gathers sequential?
- **Result:** Exact, same residuals. **Reject on clock.** circle2000 3843 vs I156 3746 ms; circle3000 12784 vs 12606 ms.
- **Decision:** Revert sort. Sequential gathers do not beat the existing walk order.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I160 SoA live adjacency

- **Question:** Do separate index/time streams beat AoS `pair` on the C-walk?
- **Result:** Exact, same residuals. **Reject on clock.** circle2000 3872 vs I156 3746 ms; circle3000 12974 vs 12606 ms.
- **Decision:** Revert to I155 AoS pair. Layout micro-opts after I156 are closed (I158–I160 all slower).
- **Class:** experiment (negative on clock)

## 2026-10-13 — I161 integer grades

- **Question:** Do order-preserving integer grades + 0-as-missing beat float times?
- **Result:** PH still matched (thicker residual is still exact VR) but **collapse broke**. circle80 out 161 vs 93; circle200 6426 vs 283; circle2000 **1.07M vs 5169**, collapse 100 s / 0.20×. n=3000 aborted.
- **Decision:** **Revert.** 0-as-missing + rank remap under-collapses. Matching-batch parallel also unsafe (shared commons).
- **Class:** experiment (negative)

## 2026-10-13 — I165 oldest-prefix (no C-walk)

- **Question:** Does keeping the oldest \(4n/6n/8n\) edges (no domination) match Ripser?
- **Result:** **No at scale.** circle80 matches at 4n+. circle200 matches at 6n/8n, **fails at 4n** (7 unmatched). circle2000 6n: **222 unmatched**, 12k residual, 0.19 s / **147×** vs Ripser (wrong barcode). blobs2000 6n: **533 unmatched**.
- **Decision:** Reject as an exact algorithm. Speed is real; identity is not. I164’s 12.5% bins hid first-keep inside the last 134k edges.
- **Class:** experiment (negative on identity)

## 2026-10-13 — I166 prefix-then-backward

- **Question:** Does oldest-6n then real backward collapse recover the barcode?
- **Result:** **No.** circle2000 suffix-back 6n: residual **4059 vs 5169** (over-collapse), **222 unmatched**, 0.19 s. Dropping the young 1.06M edges shrinks C on the prefix and over-trims. The live context for the first kept edge is larger than 6n.
- **Decision:** Reject 6n. I167: measure first-keep index; sweep `--suffix-keep = m − first_keep`.
- **Class:** experiment (negative at 6n)

## 2026-10-13 — I167 first-keep + suffix-keep

- **Question:** Where is the first kept edge, and is suffix-back exact at `keep = m − first_keep`?
- **Result:** circle2000 first_keep=1022569/1077130, **remain=54561 (27.3n)**. suffix-back at 54561: **exact vs back and Ripser**, residual 5169, collapse 130 ms / 1.4M probes vs 4176 ms / 567M. **139× vs Ripser** (28.5 s / 0.205 s) — oracle cutoff. 40k almost (2 unmatched); 20k fails. blobs first_keep at 31% (remain 225n) — suffix does not pay. tau_late 16k/567M — I171 dead.
- **Decision:** Oracle suffix-back is the first H1 **>10×** on circle2000. I168: find the cutoff without a full C-walk (stabilize / double keep).
- **Class:** reproduced (oracle)

## 2026-10-13 — I168 suffix-stabilize

- **Question:** Does doubling oldest-keep until the residual plateaus recover I167 without an oracle?
- **Result:** **Exact on n≤2000.** circle2000: residual 5169, **41.7× vs Ripser** (27.2 s / 0.65 s), 6.2× vs full back, keep used 128000. blobs bails to full (slower, 0.24× vs Ripser). **False plateau at n=3000/4000:** 64n and 12.5% agreed on a *wrong* residual (8325 vs 9190; 11361 vs 12562), 2 unmatched. Two too-small prefixes can match.
- **Decision:** Do not select yet. I169: confirm every plateau on a strictly larger keep.
- **Class:** experiment (partial; false plateau)

## 2026-10-13 — I169 confirm-larger

- **Question:** Does a 2k / k+m/8 confirm after a plateau fix n=3000/4000 without an oracle?
- **Result:** circle2000 still exact, **24.2× vs Ripser** (confirm costs extra; 25.4 s / 1.05 s). n=3000/4000 still **2 unmatched** (8325 vs 9190; 11361 vs 12562). **Smoking gun:** circle3000 `first_keep=23559` (young!), circle4000 `first_keep=84682`. Residual is not an oldest suffix at n≥3000 — at least one high-t edge is kept. blobs bails, 0.17× vs Ripser.
- **Decision:** Reject suffix-stab as default. n=2000 24–42× is real but not scale-invariant. I170: keep-rank histogram.
- **Class:** experiment (negative as a general alg)

## 2026-10-13 — I170 keep histogram

- **Question:** Are n=3000/4000 keeps one early outlier plus an oldest suffix, or scattered?
- **Result:** Mostly a suffix, with a thin scatter. circle2000: **5169/5169 in last 6.25%**. circle3000: **9093/9190** last bin, **97** earlier (3+0+…+50); first three at 23k/76k/88k. circle4000: **12468/12562** last, **94** earlier. blobs: 5946/6169 last, 223 earlier.
- **Decision:** Suffix-only cannot be exact at n≥3000. I171: if those ~100 early keeps have empty C, cheap-trim (abort at first common) + suffix-back can rescue them.
- **Class:** reproduced

## 2026-10-13 — I171/I172 suffix-rescue

- **Question:** Are early keeps C-empty, and does cheap-common-trim + suffix-back match Ripser?
- **Result:** Early keeps are **not** C-empty: circle3000 **0/97**, circle4000 **0/94**, blobs 7/223. 96/97 circle3000 early keeps **shift** to t=1.48911 (original t from 0.13 to 1.49). Rescue is **exact on circle2000 (0 early keeps), 36.5× vs Ripser** (27.4 s / 0.75 s), 10.3M vs 568M probes. n=3000: **2 unmatched** (8325 vs 9190). blobs: 8 unmatched. Same false residual as I168.
- **Decision:** suffix-rescue/stab are the first **honest H1>10×** on circle n=2000. Not default (fail at n≥3000). Cannot cheap-trim nonempty-C shift-keeps. Next: predict shift-to-t* without the full young C-walk, or skip collapse on I162 losers.
- **Class:** experiment (select as optional; not default)

## 2026-10-13 — I173 shift-keep support / geometry

- **Question:** Are the ~100 shift-keeps supported on a small / geometrically obvious vertex set?
- **Result:** circle3000: **97 edges on 60 verts**, first 10 are a tight clique on {1762,2217,429,…}. **Not outliers:** top-400 dmax covers **0/60**. Top-1000 longest edges cover 26/60; need top-5000 (~2887 verts) for 58/60. leftover_median/mst_max still cannot skip I162 (sphere 7.5 vs circle T=1.2 6.9).
- **Decision:** No cheap geometric filter. Shift-keeps are a small algebraic set, not a geometric shell. Next: cost-model skip is still weakly separated; need an algebraic certificate for “will shift-keep”.
- **Class:** experiment (negative as a skip filter)

## 2026-10-13 — I174 suffix-k

- **Question:** Do young shift-keeps fail first-apex early enough that a K-sample cheap-trim + tail collapse is exact?
- **Result:** circle3000: 96/97 have `any_later`, `fail_max=135`. circle4000 `fail_max=189`. **K=0** exact everywhere, **no clock win** (still a full young walk). **K=2** fast (n=2000 34× vs Ripser) but **20–28 unmatched**. **K=8** exact on n=2000 (6.55×, worse than default 7.2×), **2 unmatched** on n=3000. **K=32** exact on n=3000 (8.48×, residual 9133 vs 9190) but 1.84B vs 1.92B probes — not a 10× cut. Detecting `any_later` needs a long walk on high-t edges.
- **Decision:** Reject as a 10× lever. Safe trim still requires a near-full star walk.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I175 skip-collapse implicit

- **Question:** Does `--collapse 0 --engine implicit` beat Ripser on I162 losers without hurting the circle flagship?
- **Result:** **No.** Skip is exact but **slower than collapse=1 on every family**, and loses to Ripser everywhere. circle T=1.5: 0.69× (41 s reduce) vs collapse 6.51×. blobs 0.12× vs 0.30×. sphere 0.07× vs 0.16×. torus 0.52× vs 0.74×. Owned implicit on thick \(G_T\) is far behind Ripser; skipping collapse makes I162 worse.
- **Decision:** Do not skip collapse with our implicit. I162 still needs a cheaper C-walk or a Ripser-speed thick implicit.
- **Class:** experiment (negative)

## 2026-10-13 — I176 next (open)

- **Question:** Can the ~100 shift-keeps be preserved by leaving every `any_later` edge without finishing the star, while still abort-trimming only proven cones?
- **Note:** I174 K=0 already does full-walk-to-trim; the missing cut is proving `!any_later` without a full walk (I167: `p.second > t` is too rare on young edges).
- **Class:** proposal

## 2026-10-13 — I176 Case A/B + suffix-later

- **Question:** Are shift-keep `any_later` commons Case A (`p.second > t`) so a tail filter can leave them before K-sample trim?
- **Result:** circle3000: 96 any_later = **80 A + 18 B** (16 B-only). circle4000: 74 A / 20 B. blobs: 109 A / 75 B. Case-A-only leave + K=2: circle2000 **exact 13.4×** vs Ripser (26.7 s / 2.0 s, 142M vs 568M probes). n=3000 **2 unmatched** (8325 vs 9190) — the B-only keeps. K=8 no clock win.
- **Decision:** Case A is the cheap 13× on n=2000. I178: also leave Case B via the *other* star’s high-time tail (tiny on young edges).
- **Class:** experiment (partial)

## 2026-10-13 — I178 Case A+B tails

- **Question:** Does leaving both high-time tails before K-sample make n=3000 exact and keep the n=2000 13×?
- **Result:** K=8 n=3000 **exact** (9190) but **no clock win** (14.4 s / 8.75× vs Ripser; 1.89B probes). K=2 n=3000 still **2 unmatched**. n=2000 K=2 dropped from **13.4× to 7.46×** — walking the other star for Case B as t falls is another O(deg) pass. blobs exact, still 0.28× vs Ripser.
- **Decision:** Case-B scan is not a 10× lever. Keep `--later-b` off so `suffix-later` K=2 stays the I176 13.4× n=2000 optional. Default remains I156 back.
- **Class:** experiment (negative on clock)

## 2026-10-13 — I179 next (open)

- **Question:** Time-bucket live stars so both high-time tails are O(1)/O(log) without scanning the larger star?
- **Class:** proposal

## 2026-10-13 — I179 kept-later high-time prefix

- **Question:** Is the already-kept newer adjacency the exact Case A/B tail (newest-first), so B is O(|keeps|) not a full other-star scan?
- **Work:** `later[v]` records young-loop keeps. Case A walks `later[src]`; `--later-b` walks `later[other]`. No full-star sort (I159 was slower). Wave47 = I180.
- **Class:** experiment (running)

## 2026-10-13 — I180 kept-later clock

- **Question:** Does I179 Case A keep/beat I176 13.4×, and is cheap Case B exact at n=3000 without the I178 probe blowup?
- **Result:** Case A `later[]` + K=2: circle2000 **exact 16.9×** (25.7s/1.52s, 144M probes, residual 5169) — beats I176 13.4×. circle3000 **15.9× but 2 unmatched** (8325 vs 9190). Case B leave still cascades: n=2000 7.75× / 461M; n=3000 K=2 still 2 unmatched; K=8+B **exact 7.78× / 1.89B** — same as I178, not cheaper. n=4000 K=2+B **exact 9.08×** (285s/31.4s, 4.43B) — no cut vs default 9.50×. blobs K=2 A-only 2 unmatched; +B exact 0.29×.
- **Decision:** Keep `--later-b` off. Optional suffix-later K=2 Case A is now **16.9×** on n=2000. I181: escalate-until-first-keep and treat Case B as deeper-K, not leave.
- **Class:** experiment (partial)

## 2026-10-13 — I181 escalate-first-keep

- **Question:** Does K=8 until the first keep, then K=2 + Case-A `later[]`, with Case B as deeper-K (not leave), make n=3000 exact without losing the 16.9×?
- **Result:** n=2000 k2 **17.1×** exact; k2-esc8 **16.3×** exact (162M). n=3000 all variants **2 unmatched** (8325). esc8 added only 12k probes — `seen_keep` fired on an early leave, not the fused-fail. Case-B-as-K also 2 unmatched (B-only commons sit past the first 8 src hits). blobs +B exact 0.29×.
- **Decision:** Reject escalate-as-coded. I183: fused-fail-only escalate + capped Case-B leave. I182: bit-AND generate-C on the default path (flagship 9.50×).
- **Class:** experiment (negative on n=3000 exact)

## 2026-10-13 — I182 bit-AND generate-C

- **Question:** Does a live existence-bit row-AND emit C without the 49% miss walk and cut collapse_ms ≥30% on circle2000?
- **Result:** **Yes, exact.** C-size identical. circle2000 collapse **2.47×** (4241→1715 ms, 568M→34.5M probes, residual 5169). circle3000 **2.57×** (14123→5500 ms). blobs **1.25×** exact (still 0.3× vs Ripser). circle80 1.34×.
- **Decision:** Candidate default. I184 remasures n=4000 vs Ripser before selecting.
- **Class:** experiment (support)

## 2026-10-13 — I183 fused-fail escalate + B-cap

- **Question:** Does escalate-until-fused-fail (not first leave) plus Case-B leave capped at |later[other]|≤4 make n=3000 exact and keep ~16× on n=2000?
- **Result:** n=2000 k2 **17.3×** exact; k2-esc8 **16.5×**; k2-b4 **12.5×** (cap stops the I180 cascade). n=3000 all **2 unmatched / 8325**. esc8 still +12k probes — first fused-leave is not the I170 keep.
- **Decision:** Reject for n=3000 exactness. Capped B is the better Case-B optional (12.5× vs 7.75×) but still circle-n=2000 only. Prefer I182 default-path cut.
- **Class:** experiment (negative on n=3000; partial on B-cap)

## 2026-10-13 — I184 bit-AND flagship

- **Question:** Does back-bits clear H1 10× vs Ripser at circle n=4000 T=1.5 (I157 was 9.50×)?
- **Result:** **Yes, exact.** n=4000 **22.8×** (293.8s/12.91s, residual 12562, C-size 2.33B identical, collapse 2.64×, 4.58B→272M probes). n=2000 **14.9×** (26.7s/1.80s). Src-walk on this machine was 8.76× / 6.17×.
- **Decision:** Select bits as default (`--collapse-alg back`; `back-src` keeps the old walk). I185 remasures I162 losers.
- **Class:** experiment (support) — flagship H1 10× on circle n=2000/4000

## 2026-10-13 — I185 bits on I162 losers

- **Question:** Does the bits default change the I162 lose-to-Ripser families, and what is circle n=3000 vs Ripser?
- **Result:** All exact. circle3000 **21.5×** (118s/5.50s). blobs **0.35×** (1.26× collapse). sphere **0.40×** (2.33× collapse). uniform2 **0.49×** (1.89×). torus **1.01×** (was 0.70×).
- **Decision:** Circle family is 14.9 / 21.5 / 22.8× at n=2000/3000/4000. Losers remain. I186: retire LiveAdj/`drop_live_nbr` on the bits path (remaining wall after miss-skip).
- **Class:** experiment (support on circle; losers persist)

## 2026-10-13 — I186/I187 retire live-adj scans

- **Question:** On the bits path, can we drop LiveAdj star scans (`drop_live_nbr` is ~m²/n) and keep only Tm+bits+deg?
- **Result:** Exact. circle2000 **21.7×** (27.9s/1.29s, collapse 3.46× vs src). circle3000 **27.4×** (117s/4.25s). blobs 0.42×, sphere 0.52×, torus 1.04×.
- **Decision:** Keep no-LiveAdj as default. I188 remasured n=4000.
- **Class:** experiment (support)

## 2026-10-13 — I188 no-LiveAdj n=4000

- **Question:** Does I186 raise the flagship n=4000 ratio above I184’s 22.8×?
- **Result:** **31.3×** exact (304s/9.71s, residual 12562, collapse 9396 ms).
- **Decision:** New flagship. Next: cheaper `dominated_by` (I189) and I162 losers.
- **Class:** experiment (support)

## 2026-10-13 — I189 AND-equality first-apex

- **Question:** Can bits[first] covering C (minus later[first]) plus later[] any_later replace the Θ(|C|) Tm walk on I156 fast-trims?
- **Result:** **Exact.** circle2000 **71.0×** (27.4s/0.39s, collapse 308 ms). circle3000 **93.2×** (115s/1.24s). blobs 0.48× (809 ms), sphere 0.50×, torus 1.10×. Fast-trim fraction is high on circle, low on losers.
- **Decision:** Select as default. I190 remasured n=4000.
- **Class:** experiment (support)

## 2026-10-13 — I190 AND-eq n=4000

- **Question:** Does I189 hold at the flagship n=4000 vs Ripser?
- **Result:** **113×** exact (300s/2.65s, residual 12562, collapse 2331 ms).
- **Decision:** New flagship. Next: fused-fail/keep path (I191) and vertex collapse on blobs (I192).
- **Class:** experiment (support)

## 2026-10-13 — I191 progressive word-AND

- **Question:** Can bits-AND progressive ∩ replace the Θ(|C|) Tm consider walk on fused-fail / keep?
- **Result:** **Exact**, same residuals. Circle2000 72.3× (314 ms, no regression). Losers **worse**: blobs 809→1309 ms (0.31×), sphere 1553→2663 ms (0.32×), torus 1849→3233 ms (0.70×). Full ∩ cannot early-abort the dominated (trim) case; blobs 98M / sphere 188M dom-tests.
- **Decision:** Reject as default. Revert slow path. I193: AND-eq later apexes (stop at first hit) when !any_later.
- **Class:** experiment (reject as clock; exact)

## 2026-10-13 — I193 multi-apex AND-eq

- **Question:** When !any_later, does AND-eq over every common (stop at first hit; keep if none) beat I189 first-apex + consider?
- **Result:** **Exact**, same residuals. circle2000 **83.5×** (29.1s/0.35s, collapse 270 ms, fast-trims 1.070M/1.072M). blobs **1.78×** (192 ms, was 0.48×). sphere **1.96×** (357 ms, was 0.50×). torus **1.18×** (1828 ms). First time blobs/sphere beat Ripser.
- **Decision:** Select as default. I189 first-apex is the first iteration of this loop.
- **Class:** experiment (support)

## 2026-10-13 — I192 vertex-dom count

- **Question:** What fraction of G_T vertices are strongly dominated (N[v]⊆N[u])?
- **Result:** blobs **1.00** (2000/2000, star 1.31M). circle2000 **0.95**. torus **0.64**. sphere **0.01** (20 verts). Probe <80 ms.
- **Decision:** Implement filtration-safe sticky vertex-dominator (I194) on blobs/torus. Do not batch-trim sphere.
- **Class:** experiment (support as a count; implement next)

## 2026-10-13 — I194 sticky vertex-dominator

- **Question:** Does N_t[v]⊆N_t[u] star-trim beat I193 AND-eq on blobs/torus?
- **Result:** **Exact**, same residuals. vertex_trims: circle2000 462k, blobs 36k, torus 9k, sphere 12. Clock **not better**: circle 286 vs 270 ms, blobs 202 vs 192, sphere 459 vs 357 (discovery tax), torus 1780 vs 1828 (tiny). Static G_T frac≠dynamic grade-t hits.
- **Decision:** Reject as default (leave code, vdom=null). AND-eq already covers those edges.
- **Class:** experiment (reject as clock; exact)

## 2026-10-13 — I195 n=3000 with I194 on

- **Question:** Does I193+I194 hold H1 10× at circle n=3000?
- **Result:** **128×** exact (123s/0.96s, residual 9190, collapse 776 ms). I189 was 93.2× / 1058 ms. Mixed stack; remasure I193-only next.
- **Decision:** Circle n=3000 still ≫10×. I196: I193-only n=3000/4000.
- **Class:** experiment (support, I194-on)

## 2026-10-13 — I196 I193-only n=3000/4000

- **Question:** Does I193 alone (I194 off) beat I189 at flagship sizes?
- **Result:** **Exact.** n=3000 **119×** (118s/0.99s, collapse 812 ms, residual 9190). n=4000 **140×** (301s/2.15s, collapse 1824 ms, residual 12562). I189/I190 were 93× / 113×.
- **Decision:** New flagship **140×**. Circle family 83.5 / 119 / 140×. Next: I197 AND-eq on the any_later/shift path (torus).
- **Class:** experiment (support)

## 2026-10-13 — I197 AND-eq any_later

- **Question:** Can AND-eq of C_now (bits AND minus later-commons) skip consider() on any_later edges?
- **Result:** **Exact**, same residuals. Modest clock win: circle2000 collapse 270→249 ms (83.5×). blobs 192→178 ms (1.85×). sphere 357→334 ms (2.03×). torus 1828→1771 ms (1.14×) — still 113k shifts.
- **Decision:** Select (no regression, small win). Torus wall is the shift heap, not C-build. I198: AND-eq / sticky at shift grades.
- **Class:** experiment (support as default; torus still shift-bound)

## 2026-10-13 — I198 AND-eq at shift grades

- **Question:** Can AND-eq replace first_dominator_deg Tm walks after each C_later pop?
- **Result:** **Exact**, same residuals. Circle/blobs/sphere unchanged (~249/182/334 ms). Torus **worse** 1771→2816 ms (0.78× vs Ripser). later[] masks on every candidate dwarf Tm when C is modest; 18.8M dom-tests.
- **Decision:** Revert shift loop to Tm. I199: AND-eq a candidate only when |later[cand]| < |C|.
- **Class:** experiment (reject as clock; exact)

## 2026-10-13 — I199 adaptive shift dominator

- **Question:** Does bits-cover when |later[cand]| < |C| beat Tm on the shift heap?
- **Result:** **Exact.** No clock win: circle 259 vs 249 ms, blobs 189 vs 178, torus 1865 vs 1771. Hybrid still pays memcpy on the short-later candidates that Tm already handles cheaply.
- **Decision:** Reject. Default remains I193+I197. I200: remasure remaining I162 families (uniform2) on the selected stack.
- **Class:** experiment (reject as clock; exact)

## 2026-10-13 — I200 other-family remasure

- **Question:** Does I193+I197 lift I162 losers besides blobs/sphere/torus n=2000?
- **Result:** **Exact.** uniform2 n=2000 T=0.35 **2.10×** (was 0.30×). circle T=1.2 **33.8×** (was 4.13×). torus1000 **1.63×**. blobs1000 **1.72×**.
- **Decision:** Off-peak circle is now a second 10× point. uniform2 joins ~2× losers. Still no general 10×. Torus shift heap remains the thick-graph wall.
- **Class:** experiment (support)

## 2026-10-13 — I201 witness-restricted shift rescan

- **Question:** After sticky fails on w, can we only test C_now ∩ N_t[w], and reuse the I197 apex?
- **Result:** **Exact.** Torus collapse 1771→**1463 ms**, **1.35×** vs Ripser (was 1.14×), dom-tests 18M→12M. Circle 272 vs 249 ms; blobs 235 vs 178 (regression on small C).
- **Decision:** Gate witness on |C_now|≥32 (I202) so torus keeps the win without blobs/circle tax.
- **Class:** experiment (support on torus; not default until gated)

## 2026-10-13 — I202 witness gate |C_now|≥32

- **Question:** Does gating I201's witness rescan on `|C_now|>=32` keep the torus win without the blobs/circle tax?
- **Result:** **Exact** 5/5 vs src and Ripser. Circle n=2000 collapse **263 ms**, **84.4×** (28.6s/0.34s). blobs **190 ms**, 1.77×. sphere **365 ms**, 1.84×. torus **1512 ms**, **1.31×** (dom-tests 12.5M). Gate recovered blobs (I201 235→190; I197 was 178) and kept most of the torus win (I201 1463 / I197 1771).
- **Decision:** Select I202 as default (I193+I197+gated witness). Sphere 365 vs I197 334 is a small tax; torus is the thick-graph wall and improved. Next: I203 shape-agnostic reduce early-stop; I204 residual-vs-n scaling (Big-O evidence).
- **Class:** experiment (support as default)

## 2026-10-13 — Goal amendment: shape-agnostic + better Big-O

- **Requirement (user):** The final algorithm must be **shape-agnostic** (same path for real data with mixed homology; not tuned to circle/sphere/torus). It must target **better asymptotic scalability** than Ripser VR, not only a 10× constant-factor win, while **preserving as much topology as possible**. Complexity claims must be justified; any information loss must be quantified.
- **What this changes:** Circle 83–140× is a collapse-friendly regime, not the success criterion. A lever that helps only one family is a diagnostic, not a final algorithm. Exact VR collapse is already shape-agnostic in code; its **complexity is instance-dependent** (residual |E'|). Worst-case Big-O vs Ripser is **not** yet improved: collapse is an extra O(E·|C|) pass, and torus residual stays Θ(n²).
- **Information-loss policy:** Default path stays exact VR≤T (0 unmatched bars vs Ripser). If a different complex (Alpha / sparse Rips / witness) is selected for asymptotics, report bottleneck / bar-count / interleaving vs VR on every family.
- **Decision:** I203 = cofacet-walk early-stop (shape-agnostic, exact, less work on every residual). I204 = residual |E'(n)| log-log slopes on circle/blobs/sphere/torus/uniform2 plus extra homology shapes (figure8, two_circles, annulus). Do not claim a better Big-O until I204 (or a later construction) shows o(n²) residual or a different complex with quantified loss.
- **Class:** methodology

## 2026-10-13 — I203 cofacet-walk early-stop

- **Question:** Can we abort the hi-order cofacet merge after the Ripser zero-pivot / emergent pair is certified, cutting apparent-scan work on every family?
- **Result:** **Exact** 7/7 including figure8 and two_circles (0 unmatched vs Ripser). Torus reduce **450→172 ms**, counted probes 2.41M→2.31M, new apparent-probe counter **1.42M** (previously a full uncounted merge per leftover edge). Torus wall **1.52×** (1.68s / 2.55s; I202 was 1.31×). blobs 1.78×, sphere 1.91×, figure8 3.13×, two_circles 3.43×. Circle reduce already ~2 ms; collapse jitter 263→313 ms is unrelated.
- **Decision:** Select (shape-agnostic, exact, less algebraic work on every residual). Topology loss: **0 bars**. Complexity: same Big-O class (still Θ(|E'| · deg) worst case) but a smaller leading constant on the apparent pass. I204 measures whether |E'(n)| is o(n²) across shapes.
- **Class:** experiment (support as default)

## 2026-10-13 — I204 residual |E'(n)| slopes (shape-agnostic Big-O)

- **Question:** Does flag collapse give o(n²) residual — and a better wall-clock exponent than Ripser — on every family, not only circle?
- **Result:** **Exact** 25/25 (0 unmatched vs Ripser), including figure8 / two_circles / annulus / swiss / blobs3d. Topology loss: **0 bars**.
  Residual log-log slope `edges_out ~ n^α`: circle **1.22**, blobs **1.10**, sphere **0.91**, uniform2 **1.04**, torus **2.08**. Input `edges_in` is **~n²** on all five. Residual fraction shrinks with n on the first four (circle 1.4%→0.48%) and **stays ~31–34%** on torus.
  Wall-clock exponents: circle PITH **2.22** vs Ripser **3.25** (the 20–79× comes from this gap). blobs/sphere/uniform2 ≈ Ripser (~2.1–2.2). torus PITH **2.97** ≈ Ripser **2.95**. Collapse on torus is **n^3.20**. swiss n=400 is **0.91×** (collapse tax on a thin graph).
- **Decision:** Collapse is **shape-agnostic and exact**, but **not a worst-case Big-O win**. Residual is ~O(n) on collapse-friendly geometry and **Θ(n²) on torus**. Do not claim better asymptotics than Ripser in general. I205: quantify Alpha / Sheehy sparse vs VR (bottleneck, unmatched, size) as the remaining path to a better worst-case bound.
- **Class:** experiment (partial — exact + honest complexity; torus blocks a general o(n²) claim)

## 2026-10-13 — I205 Alpha / Sheehy quantified loss

- **Question:** On a shape-diverse suite, how much topology does Alpha (Čech/offset) or Sheehy sparse=0.5 lose vs exact VR, and do they beat Ripser's size/time enough to justify a complex change?
- **Result:** Alpha (2√r² vs VR diameter): **drops essential H1** on 5/7 families (circle 1 vs 2, blobs 1 vs 3, torus 1 vs 2, figure8 1 vs 3, two_circles 1 vs 3). Unmatched 190–751. Bottleneck 0.011–1.39 (torus 1.39, circle 0.83). Fast (5–397×) and ~O(n) simplices (2k–40k) — **wrong features for mixed homology**.
  Sheehy sparse=0.5: **essential H1 correct on 7/7**. Finite-H1 bottleneck **0.0048–0.049** (figure8 0.0048, two_circles 0.005, circle 0.010, torus 0.049). Unmatched 64–290 at 1e-4 (bars shift by ~bottleneck, not dropped). Size 17k–326k simplices — not a tiny complex. Time: circle 37× vs Ripser, torus 2.2×, **blobs 0.73× / uniform2 0.81× (slower than Ripser)**.
- **Decision:** Keep exact-VR collapse as default (0 topology loss). **Reject Alpha** as a VR stand-in — it loses loops on two_circles / figure8 / torus. Sparse is the only approx path that keeps essential homology; loss is a **≤0.05 bottleneck** at ε=0.5, not a better exact algorithm. I206: sparse simplex-count vs n (is the O(n) theorem visible at protocol T?).
- **Class:** experiment (support as quantified-loss table; reject Alpha as default; sparse not selected)

## 2026-10-13 — I206 Sheehy size vs n

- **Question:** Is Sheehy sparse=0.5 simplex count o(n²) on every family at protocol T, including torus?
- **Result:** **Yes, empirically.** Simplex-count slopes n=500…1500: circle **1.49**, blobs **1.39**, sphere **1.27**, torus **1.36**, uniform2 **1.35**. Time slopes 1.27–1.60. Torus n=1500 is 525k simplices (still large constants). Theoretical O(n) is not fully visible yet (pre-asymptotic / (1/ε)^{O(kδ)}).
- **Decision:** This is the only measured **better size exponent on torus** (~n^{1.36} vs collapse residual n^{2.08} and Ripser n² edges). It is **approximate** (I205 bottleneck ≤0.05, essential H1 kept). Do not replace the exact default. Next: I207 owned implicit on a Sheehy 1-skeleton (keep cohomology, inherit the size exponent, quantify the same loss).
- **Class:** experiment (support as approx Big-O evidence; not a default switch)

## 2026-10-13 — I207 owned implicit on Sheehy 1-skeleton

- **Question:** Does PITH implicit on a Sheehy ε=0.5 1-skeleton inherit the ~n^{1.3} size exponent, keep essential H1, and beat Ripser on blobs/uniform2 (where GUDHI explicit sparse lost)?
- **Result:** **Essential H1 correct 11/11** (two_circles/figure8/torus/blobs/circle). Bottleneck vs VR **0.007–0.054**. Sheehy is **not flag** (unmatched vs GUDHI sparse 15–548) — PITH computes the flag of the Sheehy 1-skeleton, a different complex.
  Wall-clock (skel+pith collapse=0) vs Ripser: circle1000 **89×**, torus2000 **24×**, blobs2000 **6.8×**, uniform22000 **7.1×**, torus1000 **8.0×**, blobs1000 **3.1×**, uniform21000 **2.6×**, sphere1000 **4.7×**. collapse=1 is usually a tax. 1-skeleton edges torus 24k→52k (n=1000→2000) ≈ \(n^{1.1}\).
- **Decision:** Document as **optional approx pipeline** (`--edges`, collapse=0). Do **not** replace the exact default (0 VR loss). This is the first shape-agnostic path that is **>10× on torus** (the exact-path wall), at ≤0.05 bottleneck. I208: ε∈{0.3,0.5,0.7} loss/speed frontier on torus/blobs/uniform2 n=2000.
- **Class:** experiment (support as optional approx; not default)

## 2026-10-13 — I208 Sheehy ε loss/speed frontier

- **Question:** Does tighter (0.3) or looser (0.7) Sheehy ε move bottleneck under 0.02 without losing the torus 10×?
- **Result:** Essential H1 correct on all 12 rows. Torus n=2000: ε=0.3 **9.3× / bn 0.017**; ε=0.5 **21.5× / bn 0.032**; ε=0.7 **40× / bn 0.075**. blobs: 3.8 / 7.2 / 9.2×. uniform2: 3.9 / 7.2 / 9.8×. two_circles ess=3 at every ε. ε=0.3 is the only setting with bn<0.02 on torus and it **drops just under 10×**. ε=0.7 approaches 10× on blobs/uniform2 but torus features move by 0.075.
- **Decision:** Keep optional approx at **ε=0.5** (torus 10× with bn≈0.03). ε=0.3 is the conservative documented alternative (bn≤0.017, torus 9.3×). Do not take ε=0.7 as default. Exact path unchanged. Next exact-path lever is still torus time-buckets (constant-factor); next approx lever is an in-process Sheehy (drop GUDHI Python) or larger-n blobs to see if 10× appears from the exponent.
- **Class:** experiment (support as frontier; ε=0.5 stays the optional default)

## 2026-10-13 — I209 Sheehy+implicit scaling

- **Question:** Does the I207 approx path cross 10× on blobs/uniform2/sphere at n=3000 from the exponent gap?
- **Result:** Essential H1 correct on all 20 rows. Edge slopes **1.09–1.17** (including torus). Time ~n^{1.15–1.38} vs Ripser n^{2.18–3.09}.
  **10× at n≥2000:** blobs n=3000 **10.6×** (bn 0.017), sphere n=2000 **11.2×** / n=3000 **19.4×**, torus n=2000 **25×** / n=3000 **72×**. uniform2 n=3000 **7.0×** (plateau from 6.9× at n=2000).
- **Decision:** Optional approx is now a **multi-family 10×** (circle, blobs, sphere, torus) at sufficient n, still inexact (bn 0.004–0.042). uniform2 is the holdout. Exact default unchanged.
- **Class:** experiment (support as approx scaling)

## 2026-10-13 — I210 in-process greedy-net sparse Rips

- **Question:** Can PITH own a `--sparse-eps` 1-skeleton (greedy insertion radii, keep d ≤ ((1+ε)/ε) max(λ_i,λ_j)) without GUDHI, preserving essential H1 and the torus 10×?
- **Result:** **Essential H1 7/7** (two_circles/figure8/torus/blobs/circle). Owned skeleton is denser than GUDHI (~2× edges). Torus n=2000 **14.5×** (GUDHI path 25×), bn **0.016** (better than GUDHI 0.050). circle1000 **81×**, blobs 6.0×, uniform2 6.3×. two_circles bn 0.034 vs GUDHI 0.005.
- **Decision:** Select `--sparse-eps` as the **owned optional approx engine** (no GUDHI). Not bit-identical to Sheehy; flag of a greedy-net graph. Exact default unchanged. GUDHI+`--edges` stays a comparison.
- **Class:** experiment (support as optional owned engine)

## 2026-10-13 — I211 uniform2 n=4000 Sheehy+implicit

- **Question:** Does the last I209 holdout (uniform2) cross 10× at n=4000?
- **Result:** **Yes. 13.05×** (2.13s / 0.16s), essential H1 1=1, bottleneck **0.0056**, 93k skeleton edges.
- **Decision:** Optional approx path now has a **10× point on every scaled family** (circle, blobs, sphere, torus, uniform2) at sufficient n. Loss is quantified (bn typically 0.005–0.04; unmatched are short bars). Exact-VR default is still not a general 10×.
- **Class:** experiment (support as approx; last holdout crossed)

## 2026-10-13 — I212 owned sparse-cap min vs max

- **Question:** Does `cap = min(λ_i, λ_j)` thin the owned greedy-net graph toward GUDHI's density without dropping essential H1?
- **Result:** **Reject as default.** min is faster (torus **62×** / 18k edges vs max 14× / 108k; blobs 13.7×; uniform2 12.2×) but **wrong essential H1** on circle1000 (3 vs 2) and torus (4 vs 2). Over-sparsify invents loops. two_circles/figure8/blobs/uniform2 ess OK. torus bn 0.063 vs max 0.016.
- **Decision:** Keep `--sparse-cap max` as the owned default. min is unsafe for mixed homology. Time-bucket later[] stays deferred (shift path is Tm). I213: thinner **max(λ)** via larger ε (0.6/0.7), which I208 showed GUDHI can survive.
- **Class:** experiment (reject min as default; exactness/homology fail)

## 2026-10-13 — I213 owned sparse-eps 0.6/0.7 (max cap)

- **Question:** Can a larger ε thin max(λ) enough to beat I210's 14.5× on torus without inventing essential loops?
- **Result:** **Essential H1 correct on 6/6 at ε=0.5, 0.6, and 0.7.** Torus n=2000: 0.5 **14.1× / bn 0.016 / 108k**; 0.6 **17.9× / 0.028 / 91k**; 0.7 **21.3× / 0.038 / 80k**. blobs 6.4/7.2/7.7× (bn 0.024 all). uniform2 6.2/6.6/7.3× (bn 0.0047 all). two_circles/figure8 ess=3.
- **Decision:** Recommend owned **ε=0.6** (torus +27% clock vs 0.5, ess held, bn 0.028 ≈ GUDHI I207). Keep 0.5 as the low-loss setting and 0.7 as the fast setting. Do not default to min(λ). Exact path unchanged.
- **Class:** experiment (support; ε=0.6 recommended optional)

## 2026-10-13 — I214 shift obstruction resume (exact)

- **Question:** Can the shift loop skip retesting apexes that already failed `dominated_by` on a smaller C, without losing exact VR≤T?
- **Hypothesis:** Boolean `cannot_dom` across a growing t is **inexact** (raising t can lift an obstruction). Store `cannot_until[cand] =` first failing `Tm(cand, C[i])` and resume index. Skip while `t < until`; when t passes, resume the cover check from `i` (C_now only appends). Same residual as I193+I197+I202+I203. Shape-agnostic; 0 topology loss if exact.
- **Work:** `CannotDom` in `edge_collapse.hpp`; wired into `first_dominator_deg` / `_witness`, I197 fail seeding, sticky-fail mark. Wave 75 vs src+Ripser.
- **Result:** **Exact 5/5** (0 unmatched vs src and Ripser). Lever fires (torus 1.22M skips / 11.3M tests) but **torus collapse 1714 ms vs I203 1470 ms** (1.35× vs 1.52×). circle 257 ms / 80.9×; blobs 192 ms / 1.72×; sphere 348 ms / 2.01×. Mark-every-fail + I197 Tm seeding is a tax: saved walks do not cover 10.6M stores.
- **Decision:** **Reject as default.** Keep `CannotDom` for I215 sticky-only marks (drop I197 seeding and per-fail marks). Not a Big-O change. Topology loss: **0**.
- **Class:** experiment (reject as default; exact but slower on torus)

## 2026-10-13 — I215 sticky-only obstruction mark

- **Question:** Does marking only the sticky-failed dominator (no I197 seed, no per-fail marks) drop torus collapse vs I203 without the I214 tax?
- **Hypothesis:** After sticky breaks on w, d cannot cover C at tw; skip d until t ≥ Tm(d,w). One mark per sticky break (~113k on torus) vs I214's 10.6M stores. Exact; 0 topology loss. Still not a Big-O change.
- **Work:** Drop I197 seeding and first_dominator fail-marks; keep CannotDom + sticky mark + blocked/resume. Wave 76 vs src+Ripser.
- **Result:** **Exact 5/5.** Torus collapse **1544 ms** (I214 1714, I203 1470), 200k skips / 12.3M tests, **1.48×**. blobs **227 ms** (regressed vs 190). circle 267 ms / 79×. Sticky-only is cheaper than I214 but still a tax vs I203.
- **Decision:** **Reject and revert** CannotDom from the default path. Exact shift-skip is not a clock win. Topology loss: **0**. Default stays I193+I197+I202+I203.
- **Class:** experiment (reject; revert hot path)

## 2026-10-13 — I216 owned lazy witness (Big-O / shape-agnostic)

- **Question:** Does a farthest-point lazy-witness 1-skeleton (PH on m ≪ n landmarks) keep essential H1 on mixed-homology families and beat Ripser's size exponent?
- **Hypothesis:** Construction O(n m²), flag PH on m vertices. Shape-agnostic (same path for any cloud). Not exact VR — quantify essential H1 + bottleneck. If m = o(n) and ess H1 holds, this is a real Big-O class change vs Ripser Θ(n²) edges / ~n³ time, unlike exact collapse (torus residual n^{2.08}).
- **Work:** `--witness-n M --witness-nu K` (default ν=1). Wave 77 vs Ripser on circle/blobs/sphere/torus/two_circles/figure8.
- **Result:** **Reject ν=1.** Invents essential H1 on every family (circle 18 vs 2, torus 14 vs 2, two_circles 12 vs 3, blobs 39 vs 3). Bottleneck 0.05–0.48. Faster on some rows (circle1000 24×, torus 6.7×) but **not shape-agnostic in the useful sense** — extra loops. Probe: ν=0 on torus m=200 keeps ess=2; larger m with ν=1 makes it worse (m=400 ess=49, m=800 ess=242).
- **Decision:** Do not recommend ν=1. I217: ν=0 on the same suite. Exact default unchanged. Owned `--sparse-eps` stays the optional approx.
- **Class:** experiment (reject ν=1; invents essential loops)

## 2026-10-13 — I217 lazy witness ν=0

- **Question:** Does conservative lazy witness (ν=0, no landmark-distance discount) keep essential H1 on mixed-homology families?
- **Hypothesis:** Probe torus m=200 ν=0 had ess=2. Same O(n m²) build / PH on m. Quantify bottleneck. Shape-agnostic only if ess H1 holds on two_circles/figure8/torus/blobs/circle.
- **Work:** Default `--witness-nu` 0. Wave 78.
- **Result:** **Reject.** Only torus kept ess H1 (2=2) and even then bn **0.64** / 2795 unmatched. circle1000 **drops** a loop (1 vs 2). Others invent loops (circle80 13 vs 2, blobs 21 vs 3, two_circles/figure8 6 vs 3). Fast (torus 34×, circle1000 158×) but **not topology-preserving**.
- **Decision:** `--witness-n` stays experimental/unsafe. Owned `--sparse-eps 0.6` remains the only optional approx with quantified acceptable loss. Exact default unchanged.
- **Class:** experiment (reject; ess H1 / bottleneck fail)

## 2026-10-13 — I218 owned sparse-eps 0.6 log-log slopes

- **Question:** What is the measured |E(n)| / time exponent of the recommended optional path (`--sparse-eps 0.6 max`) vs Ripser on every scaled family, and does ess H1 still hold?
- **Hypothesis:** Greedy-net flag size is theoretically O(n) for fixed ε, k (Cavanna–Jahanseir–Sheehy). I209 Sheehy edges were n^{1.09–1.17}. Owned ε=0.6 should sit in the same class, below Ripser's ~n² edges / ~n^{2.2–3.2} time. Loss already quantified (I213 bn ≤0.028 on torus). Shape-agnostic: same construction for every cloud.
- **Work:** Wave 79 n=500…2000 + figure8/two_circles.
- **Result:** **Essential H1 22/22** (including figure8 / two_circles). Edge slopes **1.31–1.39** (circle 1.39, blobs 1.38, sphere 1.31, torus 1.38, uniform2 1.37). PITH time **1.38–1.60** vs Ripser **2.14–3.29** (torus 1.60 vs 2.92). bn_max 0.012–0.055; torus n=2000 bn 0.028 / 17.8×. Unmatched are short finite bars (10–206).
- **Decision:** **Support as the complexity justification** for the optional path. Same construction on every cloud (shape-agnostic). Better size/time class than Ripser VR; not exact (quantified). Exact default still has 0 loss and no general Big-O win (I204 torus residual n^{2.08}).
- **Class:** experiment (support; optional-path Big-O evidence)

## 2026-10-13 — I219 killer-first dominated_by (exact)

- **Question:** Does testing the last failing C-vertex first cut torus Tm walks without changing the residual?
- **Hypothesis:** Consecutive apexes often fail on the same w. One extra lookup per test; skip the rest of C on a hit. Exact (same exists-dominator decision). Shape-agnostic. Not a Big-O change.
- **Work:** `dominated_by(..., hint, fail_w)` in first_dominator_deg / _witness. Wave 80 vs src+Ripser.
- **Result:** **Exact 5/5.** Lever fires (torus 2.14M / 12.5M = 17% killer hits) but collapse **1474 ms vs I203 1470** (1.56×). circle 265 ms / 83×; blobs 192 / 1.81×; sphere **388 vs 365**. Residual 163426 vs 163368 (PH still matched).
- **Decision:** **Reject as default** — no torus clock win, sphere tax. Reverted from first_dominator. Hint API stays for tests. 17% shorter walks did not show up in wall-clock (shift is memory-bound / I197 still dominates).
- **Class:** experiment (reject; exact but not faster)

## 2026-10-13 — I220 undirected kNN flag 1-skeleton (approx Big-O)

- **Question:** Does a symmetric kNN 1-skeleton (keep (i,j) if either is among the other's K nearest and d≤T) keep essential H1 on mixed-homology families with a better size class than Ripser?
- **Hypothesis:** I021 rejected k=16 as exact-VR. As an optional approx, |E|≤kn/2 = O(n) for fixed K. Shape-agnostic. Quantify ess H1 + bottleneck. If it invents/drops loops like I216, reject.
- **Work:** `--knn K`, collapse=0, implicit. Wave 81 on circle/blobs/torus/two_circles/figure8 at K=16 and 32.
- **Result:** **Reject K=16/32 as optional.** K=16 invents many essential H1 (blobs 22, sphere 26, torus 32). K=32 is near-exact on circle/sphere/figure8 (bn≈0) but **invents a torus H1** (2 vs VR's 1 essential at T=1.6; bn 0.36) and an extra H0 on two_circles. Fast (torus 40–60×) and small (35k edges) — wrong features. Probe: torus H1ess matches VR only at **K≥128** (139k edges, denser than owned sparse-eps 91k).
- **Decision:** Do not recommend `--knn`. Owned `--sparse-eps 0.6` stays the optional approx. I221: measure K=128 (first K that matches torus H1ess) vs sparse-eps on mixed families.
- **Class:** experiment (reject K=16/32; invents loops)

## 2026-10-13 — I221 kNN K=128 (homology-safe K)

- **Question:** At the first K where torus H1ess matches VR (128), is kNN still a better size/clock class than `--sparse-eps 0.6` with ess H1 on mixed families?
- **Hypothesis:** K=128 is O(n) but constants exceed greedy-net (139k vs 91k on torus n=2000). May keep ess H1; bottleneck unknown. Dominated if slower or lossier than I213/I218.
- **Work:** Wave 82, dim-1 essential only.
- **Result:** **Ess H1 6/6.** bn excellent (circle/blobs/sphere/two_circles/figure8 ≈0; torus **0.003** vs sparse 0.028). But **dominated on clock and size**: torus 6.6× / 139k vs sparse **17.8× / 91k**; circle 39× vs 93×; two_circles 1.1× vs 4.6×. Unmatched 0 except torus 2 short bars.
- **Decision:** **Reject as recommended optional** — homology-safer than K=32 but slower and denser than `--sparse-eps 0.6`. Leave `--knn` as an experimental low-loss flag (K≥128). Exact default unchanged.
- **Class:** experiment (reject as recommended; dominated by I213/I218)

## 2026-10-13 — I222 graph-induced complex (kNN quotient)

- **Question:** Does a Dey–Fan–Wang-style GIC 1-skeleton (farthest-point landmarks + kNN-cell quotient) keep essential H1 on mixed-homology families with a better size class than Ripser?
- **Hypothesis:** PH on m ≪ n. The full-cloud kNN graph sees loops; the quotient to landmarks should preserve them if L covers. Shape-agnostic. Not exact VR — quantify ess H1 + bottleneck. Witness/kNN already failed; GIC is a different estimator.
- **Work:** `--gic-n M --gic-k K`. Wave 83.
- **Result:** **Reject.** Invents essential H1 on blobs (1 vs 0), sphere (6 vs 0), torus (8 vs 1, bn 0.36). Circle/two_circles/figure8 ess OK (bn 0.014–0.020) but 355–1096 unmatched finite bars. Very sparse (200–700 edges) and fast (torus 80×) — wrong features on 3D/cluster data. Same failure class as I216 witness.
- **Decision:** `--gic-n` stays experimental/unsafe. Owned `--sparse-eps 0.6` remains the optional approx. Exact default unchanged.
- **Class:** experiment (reject; invents essential loops)

## 2026-10-13 — I223 high-deg-first prefix (exact)

- **Question:** Does testing the 8 highest-degree vertices in C_now first cut torus shift hits without changing PH?
- **Hypothesis:** I106 full maxdeg sort was slower. A prefix of 8 needs no sort of C. Hit path (most shift iterations) may find an apex sooner. Fail path still scans all. Exact exists-dominator; final keep time is the first t with no dominator. Shape-agnostic.
- **Work:** first_dominator_deg prefix. Wave 84 vs src+Ripser.
- **Result:** **Exact 5/5.** circle 258 ms / 78×; blobs **184 ms** (slightly faster); sphere 346. Torus **1537 vs 1470 ms** (1.47×), more tests (12.55M vs 12.50M) — prefix is extra fail-path work.
- **Decision:** **Reject and revert.** I106 stands: degree-first does not pay on the torus fail path. Topology loss: **0**.
- **Class:** experiment (reject; revert hot path)

## 2026-10-13 — I224 reduced VR engine (H07)

- **Question:** Does a paper-faithful reduced VR 2-complex (Koyama–Mémoli–Robins–Turner, arXiv:2307.16333) give exact PH₁ vs Ripser on mixed homology, with a better triangle size class than flag VR?
- **Hypothesis:** I053/I056 matched essential H1 but over-counted finite bars because every reduced triangle is a same-diameter (zero-persistence) pair unless it kills a later leftover. Filter those like `persist_sparse` (`death > birth`) and identity should hold. Size: \(O(n^2)\) triangles under doubling (Lemma 3.9). Shape-agnostic: same lune function on every metric, including the unit square (distilled-VR counterexample).
- **Work:** `--reduced-vr` builds Def 3.7 triangles on \(G_T\) and reduces them (`persist_triangles`). Wave 85 vs Ripser on unit square, circle, blobs, sphere, torus, uniform2, two_circles, figure8 (n=80/200 + scale n=500).
- **Result:** **Exact 19/19** (0 unmatched; bottleneck ~1e-6 float). Essential H1: unit square 0=0 (1 finite bar [1,√2)), circle 1=1, torus 1=1, two_circles/figure8 2=2. Triangle slopes **2.04–2.20** (circle 2.20 / blobs 2.05 / torus 2.04 / uniform2 2.09). Time slopes **2.63–3.53** vs Ripser **1.42–2.56** — construction loses (circle n=500: 67k tris, build 2617 ms, reduce 21 ms, **0.12×** vs Ripser 308 ms). Default collapse+implicit stays far faster.
- **Decision:** **Support as exact H1 + \(O(n^2)\) size class.** Do **not** select as default (clock). I056 reject was an evaluation bug (zero-pers counted). `--reduced-vr` stays experimental exact. Topology loss: **0**. Next H07 lever is construction (kd-tree / apparent skip), not another barcode check. Default unchanged.
- **Class:** experiment (support identity + size; reject as default clock)

## 2026-10-13 — I273 empty-seed non-Delaunay leftover skip

- **Question:** I272 invented ess H1 by skipping ae_seeded. If we skip leftover_coface only on empty-seed non-Delaunay leftovers (seeded always runs), does figure8 n=4000 reduce drop below 866 ms?
- **Hypothesis:** I251: 97% leftovers are empty-seed. Non-Delaunay ⇒ non-Gabriel ⇒ apparent. Seeded path is the I272 bug. H0/H2 unchanged. Shape-agnostic in the plane.
- **Work:** `g_delaunay` set from I271 walk; empty-seed + not-in-set → continue after ae_prepare. Wave 134 vs Ripser: H0–H2 + figure8 n=2000/4000 + dense n=5000.
- **Result:** **Exact 13/13** (figure8 2=2 at n=2000 and n=4000; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). figure8 n=4000 reduce **864 vs 866 ms**; n=2000 111 vs 99. Dense **11.3×**. H0 **59× / 3.9 ms**. Sphere H2 **59×**. No leftover-visit cut — wall is ae_seeded, not empty-seed leftover_coface.
- **Decision:** **Revert.** Exact but not a clock lever. Do not retry empty-seed geometric skips. Topology loss: **0**. I271 H0 stays. Next H1: cheaper ae_seeded or fewer seeded leftovers, not another empty-seed filter.
- **Class:** experiment (hold identity; reject clock; reverted)

## 2026-10-13 — I272 Gabriel leftover skip

- **Question:** Non-Gabriel leftovers have a diametral witness, so are they apparent (n+1)-births we can skip leftover_coface on, cutting figure8 n=4000 reduce (866 ms) to O(n) pairing?
- **Hypothesis:** Gabriel ⊆ Delaunay. Only those leftovers birth positive-persistence H1. advance_rbits still sees every G_T edge. 2D only. Shape-agnostic in the plane. H0/H2 unchanged.
- **Work:** Walk-locate opposites → Gabriel set; H1 leftover loop continues after ae_prepare when the edge is not Gabriel. Unit test n=256 vs all-pairs RedZeD.
- **Result:** **Not exact.** n=256 H1 ess **31 vs 0**, finite **37 vs 68**. Non-Gabriel leftovers still take the AE seeded/keep path — leftover_coface is not the diametral-disk test. Skipping invents essentials (older births never die).
- **Decision:** **Revert.** Do not retry Gabriel / Delaunay leftover filters as a RedZeD visit skip. Topology would have been lost. I271 H0 stays. H1 leftover visits stay Θ(|E|).
- **Class:** experiment (reject; inexact; reverted)

## 2026-10-13 — I271 walk-locate 2D Delaunay H0

- **Question:** Is I270’s H0 wall the O(n²) Bowyer–Watson scan (n=8000 metric 557 ms), and does Lawson walk + cavity flood cut construction to expected O(n log n) without changing VR H0?
- **Hypothesis:** Incremental Delaunay with adjacency flood does the same incircle tests on the cavity only. Morton order keeps walks local. Same MST ⊆ Delaunay. H1/H2 unchanged. Shape-agnostic in the plane. Justified: expected O(n log n) vs O(n²) vs Θ(|E_T|).
- **Work:** `delaunay_edges_2d_walk`; scan stays n≤12000 fallback; n cap 100000. Wave 132 vs Ripser: H0 blobs n=4000/8000/12000 + H1/H2 hold.
- **Result:** **Exact 14/14** (blobs H0 3=3 at 4k/8k/12k; figure8 2=2; sphere void 1=1; two_spheres 2=2). blobs n=4000 **54.8× / 4.1 ms / 11946 edges** (I270 176 ms / 3.17×). n=8000 **137× / 7.6 ms** (I270 557 ms). n=12000 **218× / 0.027 s / 35948 edges** vs Ripser 5.81 s. Dense H1 **10.8×**. figure8 n=2000 **17.8×**. Sphere H2 **57×**. Construction now ~linear (4.1 / 7.6 / 12.4 ms).
- **Decision:** **Support for H0.** Topology loss: **0**. Replace I270 scan as the selected 2D H0 construction. H1 leftover visits stay Θ(|E|). I272 Gabriel leftover skip was inexact (reverted).
- **Class:** experiment (support H0 identity + construction class)

## 2026-10-13 — I270 2D Delaunay H0

- **Question:** Euclidean MST ⊆ Delaunay, so is H0 of VR≤T exactly Kruskal on Delaunay edges with d≤T, skipping the G_T listing (blobs n=4000: 2.6M spatial pairs / 1.85×)?
- **Hypothesis:** Same merge times as MST. Bowyer–Watson O(n²) incircle, n∈[256,12000], d=2. H1/H2 unchanged. Shape-agnostic in the plane. Justified size: Θ(n) edges vs Θ(|E_T|).
- **Work:** `delaunay_edges_2d` + Kruskal d≤T in `persist_redzed_from_points` maxdim=0. Wave 131 vs Ripser: H0 blobs n=4000/8000 + H1/H2 hold.
- **Result:** **Exact 14/14** (blobs H0 3=3 at n=4000 and n=8000; figure8 2=2; sphere void 1=1; two_spheres 2=2). blobs n=4000 **3.17× / 0.186 s / 11946 edges** (I241 1.85× / 0.30 s / 2.6M). n=8000 **4.53× / 0.57 s / 23949**. Dense H1 **11.2×**. figure8 n=2000 **16.6×**. Sphere H2 **55×**. Delaunay construction is the new H0 cost (metric 176 ms at n=4000, 557 ms at n=8000) — O(n²) BW, not G_T.
- **Decision:** **Support for H0.** Topology loss: **0**. I263 H1/H2 unchanged. Next H0: walk-locate Delaunay so construction is O(n log n). Do not claim a connected-G_T H1 Big-O win. Leftover visits stay Θ(|E|).
- **Class:** experiment (support H0 identity + size class)

## 2026-10-13 — I269 collapse live AND-eq + Morton

- **Question:** I268 A/B: collapse on figure8 n=4000 is 845 ms / 1.97M fast trims. Does restricting AND-eq to LiveBits [rlo,rhi] plus Morton order cut that walk (AND-eq still scanned all n/64 words)?
- **Hypothesis:** leftover_coface already had the live range; collapse did not. Morton makes the range actually local. Collapse-only (I268 RedZeD layout was 5%). Same VR. H0/H2 / auto-redzed hold.
- **Work:** LiveBits rlo/rhi; AND-eq C-build/cover on [wlo,whi]; Morton before pairwise on the collapse path. Wave 130 vs Ripser: H0–H2 + `--engine implicit` figure8 n=2000/4000 + auto hold.
- **Result:** **Exact 15/15** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). implicit figure8 n=4000 collapse **768 vs 845 ms** (~9%); n=2000 105 vs 128. Dense **11.4×**. Auto figure8 still spatial redzed. Sphere H2 54×. Not a trim-walk skip.
- **Decision:** **Revert.** 9% is not a visit skip. Do not retry collapse word-range + Morton. Topology loss: **0**. I263 stays. Shared wall remains ~2M G_T edge visits (collapse trims or leftover AE).
- **Class:** experiment (hold identity; reject clock; reverted)

## 2026-10-13 — I268 Morton vertex order

- **Question:** Does Morton-ordering vertices before RedZeD shrink leftover [rlo,rhi] enough to cut figure8 n=4000 reduce (866 ms)? Random IDs make the live range all 63 words.
- **Hypothesis:** Spatial IDs are an isometry of VR. leftover_coface AND and rbit writes become local. H0/H2 unchanged. Dense 10× must hold. Shape-agnostic.
- **Work:** Morton permute for n≥256, d∈{2,3} in `persist_redzed_from_points`. Wave 129 vs Ripser: H0–H2 + figure8 n=2000/4000 + dense n=5000. Also A/B collapse vs redzed on figure8.
- **Result:** **Exact 14/14** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). figure8 n=4000 reduce **821 vs 866 ms** (~5%); n=2000 105 vs 98. Dense **11.7×**. Sphere H1 11.2×. Torus 13.3×. Sphere H2 60×. **A/B:** implicit collapse on figure8 n=4000 is **845 ms / 1.97M fast trims / residual 10k** — same Θ(|E|) as RedZeD leftover visits (862 ms).
- **Decision:** **Revert.** 5% is not a leftover-visit skip. Do not retry space-filling vertex orders. Topology loss: **0**. I263 stays. Next: the shared wall is visiting ~2M G_T edges (collapse trims or leftover AE); need a skip, not a layout.
- **Class:** experiment (hold identity; reject clock; reverted)

## 2026-10-13 — I267 tight H2 generate_stream

- **Question:** Vendor H2 `generate_stream` ANDs all n/64 neighborhood words per edge. Does restricting the AND to the live rlo/rhi intersection cut forced-redzed H2 (sphere n=200/400) without losing the void?
- **Hypothesis:** Same triangles if unique-diam emit and comb_index ties match vendor EdStream. leftover_coface already uses this range. d>2 stays vendor. Shape-agnostic. H0/H1 hold.
- **Work:** `generate_stream_h2_tight`. Wave 128 vs Ripser: H0–H2 + forced redzed sphere n=80/200/400 H2 + figure8 n=2000 + dense n=5000.
- **Result:** **Exact 15/15** (sphere void 1=1 at n=80/200/400; two_spheres 2=2; figure8 2=2; blobs H0 3=3). **No H2 clock cut:** n=80 reduce **1.50 vs I263 1.47 ms** (2.22× vs 2.64×). n=200 4.16× / 28 ms; n=400 4.27× / 237 ms (new forced-redzed rows; auto-collapse stays 58×). Dense **11.1×**. leftover_coface already had the live-range AND; n≤400 is 2–7 words so the stream skip cannot matter.
- **Decision:** **Revert.** Extra H2 path with no pith cut. Topology loss: **0**. I263 stays. Next: Morton/spatial vertex order so leftover rbit ranges are actually local (figure8 n=4000 has 63 words).
- **Class:** experiment (hold identity; reject clock; reverted)

## 2026-10-13 — I266 fused H1 leftover loop

- **Question:** Does adding each diam-tie group to rbits once and skipping `ae_prepare`/`advance_rbits` cut figure8 n=4000 reduce (866 ms) without inventing bars?
- **Hypothesis:** The 866 ms is visit overhead (prepare call + rptr scan), not leftover-coface. Same G_≤r if the whole tie group is in before leftover-coface. Shape-agnostic.
- **Work:** fused H1 loop. First wave pre-filled rbits for maxdim≥2 and **dropped sphere n=80 H2** (ess2 0 vs 1). Restricted fuse to H1-only. Wave 127 vs Ripser.
- **Result:** After the H2 fix, **exact 14/14** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). figure8 n=4000 reduce **840 vs 866 ms** (~3%, twice). Dense n=5000 **11.2×**. Sphere H1 10.4×. Sphere H2 56×. Not a leftover-*visit* skip.
- **Decision:** **Revert.** 3% is not a substantial cut; extra H1-only path is not worth it. First draft broke H2 — incremental rbits are required for generate_stream. Topology loss: **0**. I263 stays. Next: a real visit skip (not loop fusion), or a different complex/representation.
- **Class:** experiment (hold identity after H2 fix; reject clock; reverted)

## 2026-10-13 — I265 unique-diam AND on spatial hash

- **Question:** I255 unique-diam leftover-coface ≡ nonempty rbit AND was exact on all-pairs (no pith cut). Does skipping the two SparseDist hash gets on the spatial path cut figure8 n=4000 reduce (866 ms)?
- **Hypothesis:** Spatial leftover_coface pays hash gets; unique leftover diam makes coface_ready redundant. Same VR≤T. Dense stays I238 (no g_sparse). H0/H2 unchanged. Shape-agnostic.
- **Work:** `leftover_coface_h1_and` when `g_sparse` and this leftover’s diam is unique. Wave 126 vs Ripser: H0–H2 + figure8 n=2000/4000 + dense n=5000.
- **Result:** **Exact 14/14** (figure8 n=2000/4000 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). **No pith cut:** figure8 n=4000 reduce **871 vs I263 866 ms** (1.07s / 25.7×). n=2000 100 vs 103 ms. Dense n=5000 **10.0× / 0.34s**. Torus 12.6×. Sphere H1 10.3×. Sphere H2 60×.
- **Decision:** **Revert.** Hash gets were not the 866 ms wall — visiting ~2M leftovers (advance_rbits + rbit AND) is. Leftover-coface inner-loop constants (I253–I255, I265) are exhausted on both all-pairs and spatial. Topology loss: **0**. I263 gate stays. Next: skip leftover *visits*, not cheaper leftover-coface.
- **Class:** experiment (hold identity; reject clock; reverted)

## 2026-10-13 — I264 word-major rbits (H1 leftover)

- **Question:** Does storing rbits word-major (w·n+v) cut leftover AND cache misses on manifold clouds (figure8 n=4000 reduce 866 ms) without inventing bars or losing dense 10×?
- **Hypothesis:** Vendor vertex-major AND(u,v) strides n·words. Word-major keeps u,v adjacent when ids are close. Same leftover-coface. H2 stays vendor layout. Shape-agnostic.
- **Work:** H1-only advance/collect/leftover-coface on word-major. Wave 125 vs Ripser: H0–H2 + figure8 n=4000 + dense n=5000.
- **Result:** **Exact 13/13** (figure8 n=4000 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). **Clock rejects:** figure8 n=4000 reduce **1118 vs I263 866 ms** (1.30s / 19.9× vs 1.07s / 27×). Dense n=5000 **9.76× / 0.34s** (was 11.2×). Torus 11.7×. Sphere H1 10.8×. Sphere H2 59×.
- **Decision:** **Revert.** Writes to rbits are now stride-n (worse than vertex-major stride-words). Topology loss: **0**. Leftover-layout constants join I253–I255 as exhausted. I263 edge-frac gate stays. Next: a different leftover-visit cut, not another rbit layout.
- **Class:** experiment (reject; exact, slower; reverted)

## 2026-10-13 — I263 edge-frac probe for spatial + auto

- **Question:** Can a 250-point |E|/C(m,2) probe send hollow/manifold clouds (figure8 T=1.1, vol≈0.22) to spatial+hash without pulling dense uniform2/sphere off I238 all-pairs? Does that scale mixed H1 past n=2000? H0/H2 must hold.
- **Hypothesis:** π(T/L)^d misses elongated/hollow supports. Probe≈0.24 on figure8 vs ≈0.29 uniform2 / ≈0.49 sphere. Same VR≤T. Auto residual probe looks thin on a figure8 subsample (collapse miss); edge-frac < 0.25 should still pick redzed.
- **Work:** spatial if volume<0.20 OR probe<0.25. Auto: fat residual OR hollow probe → redzed. Wave 124 vs Ripser: H0–H2 + figure8 n=2000/4000 T=1.1 + dense n=5000 + sphere n=2000 + n=20000.
- **Result:** **Exact 15/15** (figure8 n=200 2=2, n=2000 **2=2 / 16.8×** spatial 482k vs 2.0M; n=4000 **2=2 / 27.1× / 1.07s** vs Ripser 29s, 1.98M vs 8.0M; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Dense n=5000 **11.2× / 0.33s** all-pairs. Sphere n=2000 all-pairs; wave 9.58×, remesure **10.1×** (0.081s). Torus **13.0×**. Circle collapse **16.5×**. n=20000 **5.6×** spatial. Blobs H1 **24×**. Sphere H2 **58×**.
- **Decision:** **Support.** Topology loss: **0**. Justified class: when the 250-pt edge frac is <0.25, metric is O(|E|) via I258–I261 hash (figure8 n=4000 1.98M vs 8.0M). Worst-case connected dense G_T still Θ(n²). Next: leftover-visit wall on the spatial path (figure8 n=4000 reduce 866 ms / 1.98M leftovers).
- **Class:** experiment (support; exact mixed-homology scale)

## 2026-10-13 — I262 always spatial+hash (drop volume gate)

- **Question:** Can 2D/3D finite-T from-points always use Moore+hash (no n×n), dropping the π(T/L)²<0.2 gate, without losing the dense 10× or inventing bars? Does that make mixed-homology figure8 n=2000 usable?
- **Hypothesis:** Moore is exact at any T. Dense all-pairs only exists to win the clock. Same VR≤T. Shape-agnostic. Exact if identity holds.
- **Work:** drop the volume gate. Wave 123 vs Ripser: H0–H2 + figure8 n=2000 + dense n=5000 + sphere n=2000 + n=20000.
- **Result:** **Exact 14/14** (figure8 n=200 2=2 and n=2000 **2=2 / 14.1×** / 0.12s; sphere void 1=1; torus 1=1; blobs H0 3=3). **Clock rejects:** uniform2 n=5000 **7.4× / 0.46s** (was 10.9× / 0.31s; 3.47M vs 12.5M pairs). Sphere n=2000 **6.8× / 0.12s** (was 10.1× / 0.08s). n=20000 held 6.2× / 1.00s. Torus 12.1×. Blobs H1 24×. Sphere H2 60×.
- **Decision:** **Revert the gate.** Identity holds; dense 10× does not. Figure8 n=2000 14× is a real mixed-homology scale receipt on the spatial path (427k vs 2.0M) — a better *predictor* than π(T/L)² could keep that win without dragging uniform2/sphere off all-pairs. Topology loss: **0**. Next: residual-frac-style probe for the spatial gate, not “always”.
- **Class:** experiment (reject clock; exact; reverted)

## 2026-10-13 — I261 load-0.5 malloc/bitmap hash

- **Question:** I260 load 0.75 cut n=20000 metric 192→113 but lengthened probes (reduce 456→513). Does load 0.5 on the same malloc/bitmap restore I259 probe length without bringing back the 256 MB write?
- **Hypothesis:** Untouched empty slots stay cheap; shorter probes cut leftover-coface. Same pairs, miss = +∞. Dense stays I238. Shape-agnostic. Exact if identity holds.
- **Work:** `need = 2|E|+1`. Wave 122 vs Ripser: H0–H2 + torus + dense n=5000 + n=20000.
- **Result:** **Exact 13/13** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). n=20000 reduce **468 vs I260 513** (I259 456); metric **153 vs 113** (I259 192); pith **1.03s / 6.2×** (I260 1.02s). Dense n=5000 **10.9×** (0.31s). Torus **12.4×** (reduce 155=I259). Sphere H1 **10.1×**. Blobs H1 **21×**. Sphere H2 **50×**.
- **Decision:** **Support as the selected hash** (short probes + no eager zero). Topology loss: **0**. Wall-clock even with I260; reduce is the real cut. Hash load-factor constants are exhausted. Next: a different scale lever (not another table size). Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support; exact reduce cut, pith even)

## 2026-10-13 — I260 tight hash (load 0.75, no Slot zero)

- **Question:** I259’s `tab.assign(16M)` wrote 256 MB at n=20000 (metric 192 vs I258 118). Does a load-~0.75 table with an occupancy bitmap and malloc (empty slots untouched) cut that metric without inventing bars?
- **Hypothesis:** Occupied-bit is enough; no need to zero keys. Same pairs, miss = +∞. Dense stays I238. Shape-agnostic. Exact if identity holds.
- **Work:** `SparseDist` malloc + `occ` bitmap; `need = |E|+|E|/3`. Wave 121 vs Ripser: H0–H2 + torus + dense n=5000 + n=20000.
- **Result:** **Exact 13/13** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). n=20000 metric **113 vs I259 192** (I258 118); pith 1.02s / **5.97×** (reduce 513 vs 456 — longer probes). Dense n=5000 **11.4×** (0.30s). Torus **12.4×** (reduce 160≈I259 154). Blobs H1 **25×**. Sphere H1 **10.0×**. Sphere H2 **52×**.
- **Decision:** **Support.** Topology loss: **0**. Metric tax is gone. Next: load 0.5 + malloc/bitmap (I259 probe length without the 256 MB write). Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support; exact metric cut)

## 2026-10-13 — I259 open-address hash spatial get

- **Question:** Does replacing I258’s lower-tri CSR binary search with an open-address hash (load ≤ 1/2, miss = +∞) cut the torus leftover-coface tax without inventing bars or slowing n=20000 past a second?
- **Hypothesis:** leftover-coface does random pair lookups. O(1) beats log(deg) on long low-id rows. Same G_T pairs. Dense stays I238. Shape-agnostic. Exact if identity holds.
- **Work:** `SparseDist` slots `{key, value}`; `spat_to_hash`. Wave 120 vs Ripser: H0–H2 + torus + dense n=5000 + n=20000.
- **Result:** **Exact 13/13** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). Torus reduce **154 vs I258 174** (I257 array 133); pith 0.21s / **12.7×** (was 11.5×). Dense n=5000 **11.2×** (0.31s hold). n=20000 **5.96×** (1.04s; reduce 456 vs 497, metric **192 vs 118** — 16M-slot zero). Sphere H1 **10.1×**. Blobs H1 **21×**. Sphere H2 **62×**.
- **Decision:** **Support.** Topology loss: **0**. Hash cuts the lookup tax; table zero is the new large-|E| metric cost. Next: tighter load / smaller table so n=20000 metric returns toward I258. Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support; exact torus reduce cut)

## 2026-10-13 — I258 skip C(n,2) matrix (CSR of d≤T)

- **Question:** I257 still `resize_lower`s C(n,2) (~450 MB of zeros at n=15000). Can `coface_ready` read a lower-tri CSR of the spatial edges instead, so the spatial path is O(|E|) memory, and does that let n=20000 finish in about a second without inventing bars?
- **Hypothesis:** generate_stream only needs `dist.n`. leftover-coface only reads G_T pairs (rbit AND). Miss → +∞, so a leaked far-read cannot invent a 0-edge. Dense stays I238. Shape-agnostic. Exact if identity holds.
- **Work:** `SparseDist` CSR + `coface_ready_any` + thread_local guard. No `resize_lower` on the spatial path. Wave 119 vs Ripser: H0–H2 + dense n=5000 + spatial n=15000/20000.
- **Result:** **Exact 14/14** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). Dense n=5000 **11.4×** (0.30s hold). n=15000 **5.79×** (0.82s; I257 0.83s). Harder n=20000 T=0.09 **6.18×** (0.99s/6.10s; **4.71M vs 200M**; would have been 800 MB). Torus spatial **11.5×** (was 14.2× — CSR binary-search tax, reduce 174 vs 133). Sphere H1 **11.0×**. Blobs H1 **23×**. Sphere H2 **57×**.
- **Decision:** **Support.** Topology loss: **0**. Justified size class: O(|E|) metric memory vs O(n²) when the T-ball is small. Clock at n=15000 held; n=20000 is newly reachable. Next: faster lookup (bidirectional CSR / open-address hash) to take back the torus reduce tax. Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support; exact O(|E|) spatial metric)

## 2026-10-13 — I257 skip ∞-fill + parallel spatial_edges

- **Question:** I256 still `std::fill`s C(n,2) with +∞ (~200 MB at n=10000). With finite T and a prebuilt EdgeList, do `coface_ready` / `generate_stream` only read d≤T pairs, so we can leave far entries 0 and parallelize `spatial_edges` without changing H0–H2? Does that hold a harder n=15000 case in under a second?
- **Hypothesis:** rbit AND / edge-graph triangles only touch G_T edges (written). Empty prebuilt is a valid G_T, not a cue to scan the zero matrix. Same VR≤T. Shape-agnostic. Exact if identity holds.
- **Work:** drop ∞-fill; honor empty prebuilt; thread the Moore scan after a read-only grid. Wave 118 vs Ripser: H0–H2 + dense n=5000 + spatial n=10000/15000.
- **Result:** **Exact 14/14** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). Dense n=5000 stayed all-pairs **11.2×** (0.31s/3.49s; hold). Spatial n=10000 **6.42×** (0.48s; metric **21 vs I256 27 ms**; 2.73M vs 50M). Harder n=15000 T=0.11 **5.60×** (0.83s/4.66s; **3.90M vs 112M**; reduce 341 ms). Torus **14.2×**. Blobs H1 **25×**. Sphere H2 **60×**. H0 1.8× (metric 55 vs I256 45 ms — thread merge on 2.6M H0 edges).
- **Decision:** **Support.** Skip-fill is exact. Topology loss: **0**. Remaining spatial tax is `resize_lower` zero-init of C(n,2) (~450 MB at n=15000). Next: skip the n×n allocation (sparse lookup for the few `coface_ready` reads). Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support; exact skip-fill + n=15000 scale)

## 2026-10-13 — I256 spatial prebuild on sparse connected clouds

- **Question:** After leftover-coface inner-loop constants are exhausted, can a connected from-points RedZeD skip far distances (spatial d≤T + ∞-fill + prebuilt EdgeList) without changing H0–H2, and does that let us take n=10000 in about half a second?
- **Hypothesis:** When π(T/L)²<0.2, |E|≪n². Same VR≤T (vendor bucket order). Dense clouds keep I238. Shape-agnostic. Exact if identity holds.
- **Work:** `bbox_max_extent` + `edgelist_from_spat` + ∞-fill. Wave 117 vs Ripser: H0–H2 + dense uniform2 n=5000 T=0.35 + sparse n=10000 T=0.14.
- **Result:** **Exact 13/13** (figure8 2=2; sphere void 1=1; torus ess H1 1=1; blobs H0 3=3). Dense n=5000 stayed all-pairs **10.9×** (0.30s/3.28s; reduce 206=I252). Sparse n=10000 **spatial** 6.03× (0.50s/2.99s; **2.73M vs 50M** distances; reduce 175 ms). Torus n=2000 also spatial (479k vs 2.0M) **13.9×** (0.18s). Sphere n=2000 stayed dense 10.4×.
- **Decision:** **Support as the sparse-T from-points path.** Not a dense 10× cut (n=10000 is 6× because Ripser is also cheap at T=0.14). Justified size class: O(n + n²(T/L)^d) distances vs O(n²) when the T-ball is small. Topology loss: **0**. Worst-case connected G_T is still Θ(n²).
- **Class:** experiment (support sparse metric; hold general 10×)

## 2026-10-13 — I255 unique-diameter leftover-coface

- **Question:** On unique edge diameters, is leftover-coface just a nonempty rbit AND (skip `coface_ready`), and does that cut the connected wall without changing H0–H2?
- **Hypothesis:** Profile on uniform2/torus/sphere: 3.45M leftovers, first common neighbor always passes `coface_ready`, 1309 misses have zero neighbors. Unique diams ⇒ any common neighbor has strictly shorter other edges ⇒ {u,v} is the unique longest face. Tied diams keep vendor `coface_ready`. Shape-agnostic. Exact if identity holds.
- **Work:** `g_h1_unique_diam` from consecutive edge diams. Wave 116 vs Ripser: unit square (ties) + H0–H2 + sphere n=2000 H1 + uniform2 n=5000/7000/8000. Remeasured n=5000/7000 standalone.
- **Result:** **Exact 14/14** (figure8 2=2; unit square ess H1 0=0; sphere void 1=1; torus 1=1; blobs H0 3=3). Wave n=5000 **11.1×** (0.30s/3.39s; reduce 212 vs I252 206 ms). n=7000 11.8× (0.49s; standalone reduce 334–345 ≈ I252 346). n=8000 **10.6×** (0.61s). Sphere H1 **10.5×**. Torus **14.5×**.
- **Decision:** **Hold identity, revert from the engine.** The lemma holds; skipping 3.45M `coface_ready` is not the wall (rbit/UF/advance). Do not claim a win from the wave’s 15 ms n=7000 blip. Topology loss: **0**. Next leftover-coface inner-loop constants are exhausted.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I254 skip ae_prepare on empty ActiveReg

- **Question:** Empty ActiveReg means no seeds. Can the H1 leftover loop skip `ae_prepare` / `clear_seeds` (still `advance_rbits`) without changing H0–H2, and does that cut the connected wall at n=8000?
- **Hypothesis:** `leftover_coface_h1_noseen` ignores stale seenbits. Next nonempty-act leftover runs `collect_candidates`, which clears stale seeds. Shape-agnostic. Exact if identity holds.
- **Work:** Empty-act branch in the H1 leftover loop. Wave 115 vs Ripser: H0–H2 + sphere n=2000 H1 + uniform2 n=5000…8000.
- **Result:** **Exact 15/15** (figure8 2=2; sphere void 1=1; torus ess H1 1=1; blobs H0 3=3). Uniform2 n=5000 **11.2×** (0.31s/3.43s; I252 0.30s). n=6000 11.2× (0.40s). n=7000 11.5× (0.53s). n=8000 **10.8×** (0.63s/6.79s). Sphere H1 **10.3×**. Torus **14.6×**. No pith cut.
- **Decision:** **Hold identity, revert from the engine.** Topology loss: **0**. n=8000 10× in 0.63 s reconfirms I252 scale. Next leftover-coface constants are rejected until a measured reduce cut.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I253 specialize H1 coface_ready

- **Question:** Other faces of leftover∪{w} are edges. Does replacing `coface_ready` with one `dist()` + `C(lo,1)+C(hi,2)` cut the connected wall without changing H0–H2? Does uniform2 n=8000 stay 10× in under a second?
- **Hypothesis:** Same youngest-face predicate. Not I247 (no extra `dist()` before the combinatorial filter). Shape-agnostic. Exact if identity holds.
- **Work:** `coface_ready_h1` on the I252 no-seen path. Wave 114 vs Ripser: H0–H2 + sphere n=2000 H1 + uniform2 n=5000…8000. Remeasured n=5000/6000/7000 standalone after the wave.
- **Result:** **Exact 15/15** (figure8 2=2; sphere void 1=1; torus ess H1 1=1; blobs H0 3=3). Wave n=5000 **10.1×** (0.36s/3.66s) looked slower; standalone reduce **207 / 208 / 213 ms** equals I252 206 ms. n=6000 11.2× (0.39s). n=7000 11.9× (0.51s). n=8000 **11.9×** (0.59s/7.01s). Sphere H1 **10.6×**. Torus **14.4×**.
- **Decision:** **Hold identity, revert from the engine.** No pith cut. Do not claim a win from the noisy wave draw. Topology loss: **0**. n=8000 10× in 0.59 s is a scale receipt, not an I253 clock win.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I252 leftover-coface no-seen (H1 unroll + H2 skip)

- **Question:** Does specializing leftover-coface on the 97% no-seed path (H1 m=2 unroll, skip the empty `seenbits` mask; H2 no-seed same skip) cut the connected wall without changing H0–H2? Does sphere n=2000 H1 (I227 6.9×) hold 10×, and does uniform2 n=7000 stay 10× in ~0.5 s?
- **Hypothesis:** `seedverts` empty ⇒ `seenbits` is zero, so `acc &= ~seenbits[w]` is a no-op memory tax. Same `coface_ready`. Not I247's extra `dist()`. Shape-agnostic. Exact if identity holds.
- **Work:** `leftover_coface_h1_noseen` / `leftover_coface_noseen`. H1 inline skip + `active_enum_lazy` no-seed. Wave 113 vs Ripser: H0–H2 + sphere n=2000 H1 + uniform2 n=5000/6000/7000.
- **Result:** **Exact 14/14** (figure8 2=2; sphere void 1=1; two_spheres 2=2; torus ess H1 1=1; blobs H0 3=3). Uniform2 n=5000 **12.7×** (0.30s/3.79s; reduce 206 vs I251 226 ms; pith 0.298 vs 0.32 s). n=6000 **11.2×** (0.39s/4.43s). n=7000 **11.8×** (0.51s/5.96s). Sphere n=2000 H1 **10.3×** (0.079s/0.81s). Torus **14.5×**. Blobs H1 **25×**. H0 **1.9×**. Sphere H2 **59×**.
- **Decision:** **Support.** Real pith cut on the no-seen path. Connected 10× holds at n=7000 in half a second. Sphere H1 holdout closed. Topology loss: **0**. Not a better Big-O. Next: specialize H1 `coface_ready` (edge diam = one `dist()`).
- **Class:** experiment (support; exact constant)

## 2026-10-13 — I251 inline empty-seed leftover-coface skip

- **Question:** Does inlining the 97% no-seed leftover-coface skip (so those leftovers never enter `active_enum_lazy`) cut the connected wall without changing H0–H2? Does torus n=2000 still hold 10×?
- **Hypothesis:** Same I246/I250 pairing. The skip path is prepare + leftover-coface only. Shape-agnostic. Exact if identity holds.
- **Work:** `ae_prepare` / `ae_keep_singleton` / `ae_seeded`. H1 loop inlines the skip. Wave 112 vs Ripser including torus n=2000.
- **Result:** **Exact 12/12** (figure8 2=2; sphere void 1=1; torus ess H1 1=1; blobs H0 3=3). Uniform2 n=5000 **11.0×** (0.32s/3.54s; I250 0.34s). n=6000 **10.8×** (0.41s/4.42s; I250 0.43s). Torus n=2000 **15.0×** (0.18s/2.70s). Blobs H1 **23×**. H0 **1.9×**. Sphere H2 **61×**.
- **Decision:** **Support.** Real pith cut (reduce 226 vs I250 253 ms at n=5000). Connected 10× holds; torus reconfirmed. Topology loss: **0**. Not a better Big-O.
- **Class:** experiment (support; exact constant)

## 2026-10-13 — I250 skip collect when ActiveReg empty

- **Question:** On a connected dense \(G_T\), how often is ActiveReg empty, and does skipping `collect_candidates` then keep exact H0–H2 and cut the connected wall?
- **Hypothesis:** collect only reads ActiveReg. Empty registry ⇒ no seeds. Reset leftover seen from a prior seeded leftover. Shape-agnostic. Exact if identity holds.
- **Work:** Profiled uniform2 n=5000: 3.46M leftovers, 3.45M no-seed skips, **3.37M empty ActiveReg**, 10.9k seeded, 1309 finite H1. `clear_seeds` + skip collect. Wave 111 vs Ripser. Hard cases: n=5000 / n=6000.
- **Result:** **Exact 11/11** (figure8 2=2; sphere void 1=1; blobs H0 3=3). Uniform2 n=5000 **10.03×** (0.343s/3.44s; I246 0.354s/3.38s; reduce 253 vs 264 ms). n=6000 **10.12×** (0.431s/4.37s; I246 0.470s/4.34s). Blobs n=4000 H1 **24×**. H0 Kruskal **1.9×**. Sphere n=400 H2 collapse **60×**.
- **Decision:** **Support.** Pith cut is real (n=6000 0.43 vs 0.47 s; same Ripser). Connected 10× on this hard family. Topology loss: **0**. Not a better Big-O. Still a portfolio.
- **Class:** experiment (support; exact constant; connected 10× on uniform2)

## 2026-10-13 — I249 parallel leftover-coface precompute

- **Question:** leftover-coface at time t is a function of \(G_{\le t}\) only. Does a parallel rbit-snapshot precompute let sequential AE skip 3.5M leftover-coface walks on the no-seed path?
- **Hypothesis:** Same-diameter lookahead matches vendor `advance_rbits`. No-seed skip uses the flag; seeded AE still calls leftover-coface with seen. Shape-agnostic. Exact if identity holds.
- **Work:** `precompute_skippable` + `pre_cf` in `active_enum_lazy`. Wave 110 vs Ripser. Hard cases: uniform2 n=5000 / n=6000.
- **Result:** **Exact 11/11**. Uniform2 n=5000 **10.05×** (0.353s/3.55s) is Ripser variance — pith 0.353s equals I246 0.354s (reduce 263≈264 ms). n=6000 **8.86×** (0.50s vs I246 0.47s). No pith cut.
- **Decision:** **Hold identity, revert from the engine.** Do not claim connected 10× from a slower Ripser draw. Topology loss: **0**. Snapshot copies + extra Kruskal cost as much as they save.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I248 fuse fill + edge histogram

- **Question:** Can counting edge buckets during the from-points fill skip I245’s extra n² count pass without changing (diam, comb_index) order?
- **Hypothesis:** Same stripes as `build_edges_parallel`. One fewer matrix scan. Shape-agnostic. Exact.
- **Work:** `EdgeCountScratch` into `redzed_vr`. Wave 109 vs Ripser. Hard cases: uniform2 n=5000 / n=6000.
- **Result:** **Exact 11/11**. Uniform2 n=5000 **8.40×** (0.42s/3.51s; metric 10→46 ms, reduce 264→280 ms). n=6000 **9.15×**. Histogram-in-fill tax > skipped count pass.
- **Decision:** **Hold identity, revert from the engine.** Same class as I244 fill-collect. Topology loss: **0**. Do not retry fusing work into the fill inner loop.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I247 leftover-coface fast path

- **Question:** Can a cheaper exact leftover-coface (strictly shorter common neighbor, then vendor `coface_ready`) cut the ~3.5M zero-persistence leftovers enough for connected 10×?
- **Hypothesis:** On continuous uniform2 the first common neighbor has both other edges < r, so two distance reads beat `comb_index`. Shape-agnostic. Exact if identity holds.
- **Work:** `leftover_coface_fast` in `active_enum_lazy`. Wave 108 vs Ripser. Hard cases: uniform2 n=5000 / n=6000.
- **Result:** **Exact 11/11** (figure8 2=2; sphere void 1=1; blobs H0 3=3). Uniform2 n=5000 **9.24×** (0.37s/3.42s; reduce 279 vs I246 264 ms). n=6000 **8.61×**. No clock win.
- **Decision:** **Hold identity, revert from the engine.** Extra distance reads before `coface_ready` did not beat vendor leftover-coface. Topology loss: **0**. Do not retry this constant.
- **Class:** experiment (hold identity; reject as clock; reverted)

## 2026-10-13 — I246 lazy R/Ri insert on leftover-coface

- **Question:** Most leftover edges on a dense connected G_T are zero-persistence (n+1)-births. Does skipping the vendor R/Ri singleton insert when AE has no seeds and leftover-coface would erase keep exact H0–H2 and cut the connected wall?
- **Hypothesis:** Insert+erase is equivalent to never inserting. collect_candidates uses ActiveReg, not R. Same skip on H2 empty-XOR births. Shape-agnostic. Exact if identity holds.
- **Work:** `active_enum_lazy` in `redzed_vr`. Wave 107 vs Ripser. Hard cases: uniform2 n=5000 (I245 8.3× / 0.42s) and n=6000 (more points, still seconds).
- **Result:** **Exact 11/11** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Uniform2 n=5000 **9.56×** (0.35s/3.38s; reduce 264 vs I245 325 ms). n=6000 **9.25×** (0.47s/4.34s). Blobs n=4000 H1 **24×**. H0 Kruskal **1.9×**. Sphere n=400 H2 collapse **42×** (void 1=1; clock variance vs I245 60×).
- **Decision:** **Hold.** Support as the RedZeD AE insert path. Topology loss: **0**. Connected 10× still open (need ~1.05× / 16 ms). Not a better Big-O.
- **Class:** experiment (hold; exact constant; closer to 10×)

## 2026-10-13 — I245 parallel build_edges

- **Question:** Is vendor `build_edges` (191 ms of the connected wall) parallelizable without changing filtration order?
- **Hypothesis:** Diameter histogram + place + `finish_buckets` are exact if the final order is still (diam, comb_index). Independent j-stripes and per-bucket sorts can run on a pool. I244 skip-enclosing stays. Shape-agnostic. Exact.
- **Work:** `build_edges_parallel` + `finish_buckets_parallel` in `redzed_vr`. Wave 106 vs Ripser. Hard case: uniform2 n=5000 H1.
- **Result:** **Exact 10/10** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Uniform2 n=5000 **8.3×** (0.42s/3.46s; I244 6.8× / 0.50s). Reduce 325 vs 411 ms. Blobs n=4000 H1 **21×**. Sphere n=400 H2 **60×**. Circle **18×**.
- **Decision:** **Hold.** Support as the RedZeD edge builder. Topology loss: **0**. Connected 10× still open (need ~1.2× on sequential AE). Not a better Big-O.
- **Class:** experiment (hold; exact constant; closer to 10×)

## 2026-10-13 — I244 skip vendor enclosing on VR≤T

- **Question:** How much of the connected RedZeD reduce is enclosing / `build_edges` / AE, and can we drop the wasted n² cone when T is finite without changing the barcode?
- **Hypothesis:** Vendor always computes enclosing. For VR≤T, thr=T is exact. Collecting G_T during the fill we already pay might also skip `build_edges`. Shape-agnostic. Exact.
- **Work:** Profiled uniform2 n=5000: cone 69 ms, build_edges 191 ms, AE 229 ms. `redzed_vr` skips cone. Fill-collect + std::sort smoked then reverted (metric 10→460 ms). Wave 105 vs Ripser. Hard case: uniform2 n=5000 H1.
- **Result:** **Exact 10/10** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Uniform2 n=5000 **6.8×** (0.50s/3.42s; I243 5.6× / 0.61s). Reduce 411 vs 484 ms. Blobs n=4000 H1 **20×**. Sphere n=400 H2 **59×**. Circle **17×**.
- **Decision:** **Hold.** Support skip-enclosing as the RedZeD driver. Do **not** collect+sort. Topology loss: **0**. Connected 10× still open (`build_edges`+AE). Not a better Big-O.
- **Class:** experiment (hold; exact constant; fill-collect reject)

## 2026-10-13 — I243 incremental rbit on owned AE

- **Question:** Does RedZeD-style incremental rbit (word-AND neighborhoods at the current leftover diameter) cut I242’s common-neighbor walk without changing the barcode, and does that help connected uniform2 at n=5000?
- **Hypothesis:** Same I242 pairing. rbit(a,b) iff d≤current t. has_leftover_coface becomes a bitset intersection. Seeded probes stay leftover-star (circle 875k). Shape-agnostic. Exact if identity holds.
- **Work:** `persist_active.hpp` rbits + reusable seenbits. Wave 104 vs Ripser / RedZeD / auto. Hard case: uniform2 n=5000 H1.
- **Result:** **Exact 11/11** (figure8 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Circle AE **0.26s** vs I242 0.38s / RedZeD 0.021s (**0.08×**). Uniform2 n=1000 AE 0.35× RedZeD. Hard uniform2 n=5000 auto **5.6×** (0.61s/3.41s). Blobs n=4000 H1 **22×**. Sphere n=400 H2 **61×**.
- **Decision:** **Hold.** Exact rbit, modest AE constant, not a default, not connected 10×. Topology loss: **0**. Next owned cut is leftover-star / packed annotations, not another pairing rule.
- **Class:** experiment (hold; exact, small AE cut)

## 2026-10-13 — I242 vendor-faithful owned H1 AE

- **Question:** Does RedZeD’s H1 AE pairing (incremental register, leftover-coface erase-without-pair, combinatorial `coface_ready`) keep exact H0–H2 on mixed clouds, and can owned AE push connected uniform2 past the ~6× wall at more points?
- **Hypothesis:** I236/I237 invented finite H1 because they pre-registered every leftover and paired on leftover-coface / first-hit. Vendor erases that column (zero bar / (n+1)-birth skip) and only seeds from already-registered actives. Same path on every flag graph. maxdim≥2 stays the I232 walk (vendor AE is H1-only). Shape-agnostic. Exact if identity holds.
- **Work:** `persist_active.hpp` I242 AE. Wave 103 vs Ripser / RedZeD / auto. Hard case: uniform2 n=5000 H1 (more points than I241 n=4000, still seconds).
- **Result:** **Exact 13/13** (0 unmatched; figure8/two_circles ess H1 2=2; sphere void 1=1; two_spheres 2=2; blobs H0 3=3). Owned AE is **not** a clock engine: circle n=500 0.38s vs RedZeD 0.022s (**0.06×**) / Ripser 0.31s; uniform2 n=1000 0.065s vs RedZeD 0.021s (**0.33×**). Hard connected uniform2 n=5000 auto-redzed **5.5×** (0.62s/3.42s, reduce 488 ms, 1 component). Blobs n=4000 H1 **23×**. Sphere n=400 H2 **61×**. H0 Kruskal 1.9×.
- **Decision:** **Hold.** Support as exact `--engine active` (I236 pairing bug is fixed). Do **not** change the default. Topology loss: **0**. Connected 10× still open. Next owned cut is rbit bitsets, not another leftover-coface pairing.
- **Class:** experiment (hold; exact identity, no clock vs RedZeD)

## 2026-10-13 — I241 H0 spatial Kruskal (no RedZeD)

- **Question:** Is VR H0 just Kruskal, and does skipping RedZeD on `maxdim=0` keep identity at more points without a long H1 test? Does T-capping a connected metric (fill only d≤T) cut uniform2 toward 10×?
- **Hypothesis:** H0 barcode is the MST of G_T. Spatial Moore edges are exactly {d≤T}. T-cap is exact for VR≤T (far pairs unused) but metric-bound, not reduce-bound. Shape-agnostic. Exact.
- **Work:** `spatial_edges` + `kruskal_h0`. Auto `maxdim=0` → redzed-h0 (no pairwise matrix). T-cap smoked then reverted. Wave 102 vs Ripser. Hard case: blobs n=8000 H0.
- **Result:** **Exact 11/11** (0 unmatched; blobs H0 3=3; two_spheres H2 2=2; circle 1=1). H0 vs Ripser dim 0 **1.8–1.9×** (blobs n=8000 1.27s/2.46s, 10.5M edges). T-cap **rejected** (uniform2 metric 7→80 ms; reduce unchanged ~266 ms). H1 hold: blobs n=4000 **23×**; uniform2 **5.6×**; sphere H2 **61×**.
- **Decision:** **Support as the H0 path.** **Hold** for H0 10× (Ripser dim 0 is already cheap) and for general H1 10×. Topology loss: **0**. Do not T-cap the connected metric. Connected RedZeD reduce remains the wall.
- **Class:** experiment (support H0 path; reject T-cap; hold 10×)

## 2026-10-13 — I240 spatial UF + per-component RedZeD metric

- **Question:** Can we find I239’s G_T components without an n×n matrix, so clustered clouds keep scaling (more points, H0–H2 exact) without the pairwise tax?
- **Hypothesis:** Cell size T + Moore neighborhood is exact for Euclidean d≤T. Then each block fills only m×m. Blobs (3 clusters, 2-d) should use ~⅓ of the pairs. Uniform2 is 1 component — no change. Shape-agnostic. Exact.
- **Work:** `spatial_components` (d=2/3) + `finish_redzed_from_points`. Wave 101 vs Ripser. Hard case: blobs n=8000 (seconds). H2: two_spheres n=200 forced redzed-cc.
- **Result:** **Exact 10/10** (0 unmatched; figure8/two_circles 2=2; sphere void 1=1; two_spheres H0=2 H2=2, 9900 vs 19900 distances). Circle auto-collapse **17×**. Sphere n=400 H2 **59×**. Blobs auto-redzed-cc cc=3: n=4000 **21.9×** (2.67M/8.00M), n=6000 **24.4×** (6.00M/18.0M), n=8000 **27.4×** (0.38s/10.4s, 10.7M/32.0M). Uniform2 n=4000 **5.6×** / full 8.0M pairs.
- **Decision:** **Support as the from-points RedZeD path.** Topology loss: **0**. Clustered real data now gets cheaper per point as n grows. **Hold** general 10× — connected G_T still allocates n×n and sits at ~6×. Not a better worst-case class.
- **Class:** experiment (support spatial cc; hold connected 10×)

## 2026-10-13 — I239 exact G_T component split + parallel RedZeD

- **Question:** Is VR≤T of a disconnected G_T exactly the direct sum of the components, and does splitting + bounded parallel RedZeD push clustered clouds (blobs) past 10× at more points without losing H0–H2 identity or circle/sphere collapse?
- **Hypothesis:** blobs T=1.0 is 3 clusters (centers 3 apart, noise 0.25). RedZeD time is superadditive (~n^{2.3}), so 3 blocks of n/3 beat one n-matrix, and they run independently. Uniform2 stays 1 component — no clock change there. Shape-agnostic. Exact.
- **Work:** `finish_redzed` UF on d≤T; extract submatrices; bounded hardware-concurrency pool; merge bars. Size-1 → H0 essential. `main` keeps `n_collapse_trims` as the component count. Wave 100 vs Ripser. Hard case: blobs n=4000/6000 (seconds). H2 wedge: two_spheres n=200.
- **Result:** **Exact 10/10** (0 unmatched; figure8/two_circles 2=2; sphere void 1=1; two_spheres H0=2 H2=2; blobs H0 3=3). Circle auto-collapse **18×**. Sphere n=400 H2 **61×**. Blobs auto-redzed-cc cc=3: n=2000 **13.0×** (reduce 20 ms), n=4000 **18.3×** (0.12s/2.18s, reduce 77 ms vs I238 297 ms), n=6000 **13.5×** (0.38s/5.16s). Uniform2 n=4000 **6.3×** / cc=1. Forced redzed-cc matches on two_spheres and blobs.
- **Decision:** **Support as the RedZeD path on disconnected G_T.** **Hold** for general 10× — connected uniform2 is unchanged. Topology loss: **0**. Not a better worst-case Big-O. Real clustered data is the payoff. Next: skip the full n×n fill (spatial UF + per-component matrices) and attack the connected reduce wall.
- **Class:** experiment (support disconnected 10×; hold general 10×)

## 2026-10-13 — I238 lazy parallel RedZeD metric

- **Question:** Does skipping the full n×n pairwise `vector<vector>` + copy on auto-redzed (probe from points, parallel fill of RedZeD’s lower-tri matrix) cut the blobs/uniform2 wall toward 10× without losing identity or circle/H2 collapse?
- **Hypothesis:** I229 blobs n=4000 paid 59 ms metric of 394 ms wall. Probe only needs 250² distances. Parallel fill should drop metric to ~10 ms. Reduce (~313 ms) is unchanged — maybe 6× not 10×. Shape-agnostic. Exact.
- **Work:** `probe_residual_frac_points` + `persist_redzed_from_points` (threaded row fill). Auto-redzed skips `pairwise`. Collapse path unchanged. Wave 99 vs Ripser.
- **Result:** **Exact 10/10** (figure8/two_circles 2=2; sphere void 1=1; blobs H0 3=3). Circle auto-collapse **18×**. Sphere n=400 H2 **62×**. Torus n=2000 **12.7×**. Blobs n=2000 **6.3×** (I237 5.4×). Blobs n=4000 **6.72×** / metric 7 ms / reduce 297 ms vs I229 5.3× / 59 ms / 313 ms. Uniform2 n=4000 **6.93×**. No new 10×.
- **Decision:** **Support as the auto-redzed metric path.** **Hold** for general 10× — reduce is still the wall. Topology loss: **0**. Next: algebraic cut on RedZeD reduce, not another metric tweak.
- **Class:** experiment (support metric; hold 10×)

## 2026-10-13 — I237 GUDHI Rips + scale H0–H2

- **Question:** Is GUDHI 3.13 explicit Rips a faster exact engine on the blobs/uniform2 5× wall, and does birth-time leftover-coface AE fix I236 identity? Can `--engine auto` hold H0–H2 at more points without a long test?
- **Hypothesis:** GUDHI cohomology on the flag VR is exact and might beat RedZeD reduce. Incremental AE (insert leftover only at birth) should match RedZeD pairing. Sphere n=600 H2 stays collapse (I236 τ=0.15). Shape-agnostic.
- **Work:** Birth-time AE implemented, smoked, reverted (same unmatched as I236). Wave 98: GUDHI vs auto/RedZeD/Ripser; sphere n=600 H2; blobs/uniform2 n=2000; torus n=600 H2.
- **Result:** **Exact 11/11** auto vs Ripser (0 unmatched; figure8/two_circles 2=2; sphere void 1=1 at n=200 and n=600; blobs H0 3=3). GUDHI **exact 7/7** but slow (blobs n=1000 15.9 s / 744× worse than auto; torus n=600 H2 52 s / 39M simplices). Sphere n=600 H2 **auto-collapse 136×** (0.032s/4.41s) and **54×** vs RedZeD. Blobs/uniform2 n=2000 **5.4× / 5.5×**. Torus n=600 H2 auto-redzed **4.5×**, collapse 13.9 s (**88×** worse). AE **rejected** (figure8 unmatched 12).
- **Decision:** **Reject GUDHI as a clock engine** (materializes the flag VR). **Hold** selected auto at more points — H2 136× is the scale payoff of I236’s τ. Topology loss: **0**. Do not retry leftover-coface AE without rbit + vendor-faithful pairing. Blobs 10× still open (RedZeD reduce).
- **Class:** experiment (reject GUDHI clock + AE; hold selected scale)

## 2026-10-13 — I236 H2-aware auto dispatch

- **Question:** Does I235’s τ=0.04 mis-route H2 on mid-residual spheres (collapse tets are cheap; RedZeD H2 is on the full metric), and can `--engine auto` stay exact on mixed H0–H2 at more points without a long test? Is a RedZeD-faithful leftover-coface AE exact on real clouds?
- **Hypothesis:** Sphere frac~0.057 wants RedZeD for H1 and collapse for H2 (I234: 26× vs 3.2× at n=200). τ=0.15 when maxdim≥2 keeps torus (~0.28) on RedZeD. Leftover-coface / first-hit `process_leftover` will match RedZeD if active=R and seeded-then-leftover order is respected. Shape-agnostic. Both engines exact.
- **Work:** dim-dependent τ in auto dispatch. Owned AE implemented then reverted (figure8 unmatched 12; essentials held). Wave 97 vs Ripser / collapse / RedZeD. Hard case: sphere n=400 H2.
- **Result:** **Exact 9/9** H0–H2 (0 unmatched; figure8/two_circles 2=2; sphere void 1=1 at n=80 and n=400; blobs H0 3=3). Sphere n=400 H2 **auto-collapse** frac=0.059, **61.3×** vs Ripser (0.017s/1.05s), **19.5×** vs RedZeD (0.335s). Torus n=400 H2 **auto-redzed** 4.6× / 3.2× vs collapse. H1 unchanged: circle n=500 auto-collapse **17.6×**; blobs n=1000 auto-redzed **3.6×**. Owned AE **rejected** (invents finite H1).
- **Decision:** **Support H2 τ.** CLI default stays `--engine auto` with H1 τ=0.04 and H2 τ=0.15. Topology loss: **0**. Not a better Big-O. Do not retry leftover-coface without rbit + no empty-R abort. Next: blobs/uniform2 10× (reduce wall) or a faithful rbit AE.
- **Class:** experiment (support dispatch; reject owned AE)

## 2026-10-13 — I235 auto residual-frac dispatch

- **Question:** Can `--engine auto` pick RedZeD on fat residuals (torus) and collapse+implicit on thin ones (circle) from a cheap subsample, without losing identity or circle 10×?
- **Hypothesis:** I204 E'/E is ~0.3 on torus and ~0.01 on circle/blobs. A 250-point stride subsample collapse predicts that. Fat → skip full G_T+collapse. τ=0.04 also sends blobs/sphere (~0.057) to RedZeD (faster than collapse there). Shape-agnostic. Both engines exact. Topology loss 0.
- **Work:** `probe_residual_frac` + auto dispatch. Wave 96 vs Ripser / forced collapse / forced RedZeD.
- **Result:** **Exact 11/11** (figure8/two_circles 2=2; sphere H2 1=1; blobs H0 3=3). Torus n=2000 **auto-redzed** frac=0.28, **12.5×** vs Ripser (0.21s/2.63s), **13.6×** vs collapse (2.86s). Circle n=1000 **auto-collapse** frac=0.021, **28.4×**. Blobs n=1000 auto-redzed **2.6×** (was 1.7× on collapse). Sphere n=500 H1 3.3×. Probe tax ~6–12 ms.
- **Decision:** **Support as `--engine auto`.** Same CLI path for real mixed data. Not a general 10× (blobs 2.6×). Not a better Big-O — a portfolio of two exact engines. Topology loss: **0**. Do not claim the dispatch is an algorithm class change.
- **Class:** experiment (support; exact portfolio, not general 10×)

## 2026-10-13 — I234 owned active H0+H1+H2

- **Question:** Can the owned engine compute exact H0, H1, and H2 on mixed homology and a harder void (sphere), and stay usable at a larger H1 cloud, without a long test?
- **Hypothesis:** I232 empty-XOR triangles are the H2 births. Tets must be collected and reduced in diameter order (unsorted invents thousands of finite H2). Same path on every flag graph. Topology loss 0 if identity holds.
- **Work:** Revert I233 generation. Record empty-XOR triangles; sort tets; R2/Ri2 `resolve_bar`. Wave 95 vs Ripser / RedZeD / default. Hard case: sphere n=200 maxdim=2. Scale H1: blobs n=1000.
- **Result:** **Exact 10/10** H0–H2 (0 unmatched). Sphere void ess H2 1=1 at n=80 and n=200; figure8/two_circles ess H1 2=2; blobs ess H0 3=3 at n=1000. bn ~5e-7. Clock **loses**: sphere n=200 H2 active 3.21 s / **0.039×** vs Ripser 0.13 s / RedZeD **0.040 s** / default **0.005 s**. blobs n=1000 H1 1.41 s / 0.058× vs Ripser (RedZeD 0.019 s). 2.9M simplices on sphere n=200.
- **Decision:** **Support as owned H0–H2 identity.** **Hold as a clock / scale engine.** Topology loss: **0**. For real data at more points use `--engine redzed` (general exact H0–H2) or the collapse+implicit default (faster on collapse-friendly sphere). Do not switch default. Not a better Big-O (still \(\Theta(|E|\cdot\deg)\) triangles + tets).
- **Class:** experiment (support identity; hold clock)

## 2026-10-13 — I233 active leftover-star generation

- **Question:** Does generating only MST 1-leftover apparent + live leftover-star triangles keep I232 identity and cut the 36M-visit wall?
- **Hypothesis:** 1-leftover triangles are leftover + two MST edges. Multi-leftover triangles with a dead partner can be recovered by a leftover-coface existence test. Shape-agnostic.
- **Work:** Active leftover star + MST apex + leftover-coface `process_leftover`. Smoke vs Ripser on mixed families.
- **Result:** Unit square / C4 hold. Real clouds **fail**: circle n=80 unmatched 4–211 depending on the leftover-coface variant; figure8/two_circles invent bars; blobs/torus/sphere invent dozens to thousands. Dead-partner and same-diameter geometric cofaces are not a substitute for reducing the actual triangle.
- **Decision:** **Reject and revert** generation to I232. Topology loss if kept. I234 H2 is built on the restored walk.
- **Class:** experiment (reject; inexact)

## 2026-10-13 — I232 annotation skip on owned active H1

- **Question:** Does R/Ri `resolve_bar` (skip empty face-XOR = H₂ birth) keep I231’s mixed-homology identity and cut the reduce wall?
- **Hypothesis:** I231’s 3.8 s of 3.85 s on circle n=500 is F₂-reducing 4.5M columns. Most are empty XOR. Keep transferred R[j] after pairing (unit square: later coface still kills the older leftover). Shape-agnostic.
- **Work:** `persist_active.hpp` annotations. Wave 93 vs I231 / Ripser / RedZeD. n≤500 plus n=1000 after skip≥0.5 and ≥3× I231.
- **Result:** **Exact 19/19** (0 unmatched; ess H1; figure8/two_circles 2=2; bn ~5e-7). Skip median **0.964** (circle n=500 4.45M/4.51M; n=1000 36.2M/36.5M). vs I231: circle n=500 **7.2×** (3.85→0.54 s); blobs **28×** (4.42→0.16); torus **21×**. vs Ripser: still loses (circle n=500 **0.57×**, n=1000 **0.52×**; blobs n=500 0.12×). vs RedZeD 0.03–0.37×. Generation still visits every youngest-face triangle (circle n=1000 36M).
- **Decision:** **Support as a reduce lever** on experimental `--engine active`. **Hold as an engine** — not a Ripser/RedZeD clock win, not a better Big-O (still \(O(|E|\cdot\deg)\) visits). Topology loss: **0**. Default and recommended `--engine redzed` unchanged. Next: skip generating those 36M triangles (active-star / leftover-coface / rbit), not just skip reducing them.
- **Class:** experiment (support skip; hold clock)

## 2026-10-13 — I231 owned active H1

- **Question:** Does an owned leftover-youngest-face H1 (generate a triangle only from its youngest leftover face; same F₂ reduce as persist_sparse) match Ripser on mixed homology and beat RedZeD / Ripser?
- **Hypothesis:** I163 leftover_apparent=1.0. Skipping MST-as-generator and (n+1)-births should cut triangles. Shape-agnostic. Early-stop after pairing the current leftover is **inexact** (unit square: later same-youngest-face triangle reduces onto the older leftover).
- **Work:** `--engine active`, collapse=0. Wave 92 vs Ripser / default / redzed.
- **Result:** **Exact 12/12** through n=500 (unit square, figure8, two_circles, …). Early-stop unit-square bug fixed before the wave. Clock **rejects**: circle n=500 3.85 s / **0.079×** vs Ripser (4.5M tris); blobs 4.42 s / 0.004×; torus 1.77 s / 0.026×. circle n=2000 **timeout 180 s**. Dominated by vendored RedZeD and by collapse+implicit.
- **Decision:** **Reject as a clock engine.** Keep `--engine active` experimental (identity holds). Topology loss: **0**. The vendor win is the annotation / rbit coface skip, not the youngest-face filter alone. Do not switch default. Next owned port needs those structures.
- **Class:** experiment (support identity; reject clock)

## 2026-10-13 — I230 RedZeD -DNDEBUG

- **Question:** Does compiling the vendored TU with the paper’s `-O3 -DNDEBUG` cut I229’s 313 ms blobs-n=4000 reduce enough to push sphere over 10×?
- **Hypothesis:** asserts in the vendor inner loop are a 15–30% tax. Same PH. Shape-agnostic.
- **Work:** `COMPILE_FLAGS -DNDEBUG` on `redzed_bridge.cpp`. Wave 91 vs I228/I229 walls.
- **Result:** **Exact 8/8.** Median vs previous **1.00×**. sphere n=4000 8.34× (was 8.30×). blobs n=4000 5.27× / reduce 300 ms (was 313). No clock win — vendor has essentially no hot-path asserts, or `-O3` already dropped them.
- **Decision:** **Reject as a clock lever.** Keep `-DNDEBUG` (matches paper, no regression). Topology loss: **0**. Next: owned active-enumeration (drop vendor) or a different exact representation. General 10× is still open.
- **Class:** experiment (reject; exact, no faster)

## 2026-10-13 — I229 RedZeD scale (general 10×?)

- **Question:** Does `--engine redzed` become a general exact H1 10× at n=3000/4000 on blobs/sphere/uniform2 (the I228 5–8× families), while staying exact on mixed loops?
- **Hypothesis:** I228 time slopes looked slightly better than Ripser. Scale should widen the gap if that is an exponent effect. Shape-agnostic: same engine.
- **Work:** Wave 90 vs Ripser + default PITH. Mixed n=500; losers + torus at 3000/4000.
- **Result:** **Exact 9/9** (0 unmatched; ess H1; figure8/two_circles 2=2). **No new 10×** on blobs/sphere/uniform2. blobs 5.37× / 5.29× (n=3000/4000); uniform2 5.51× / 5.10×; sphere 7.55× / **8.30×**; torus n=3000 **14.2×**. High-n (2000→4000) exponents ~n^{2.3} for both RedZeD and Ripser on blobs — constant-factor win, not an exponent gap. blobs n=4000: metric 59 ms, reduce **313 ms**, wall 394 ms vs Ripser 2086 ms.
- **Decision:** **Hold.** Exact at scale. Do not claim general 10×. Sphere is the closest (8.3×). Next: I230 `-DNDEBUG` on the vendor TU (paper’s flags); then owned active enumeration. Topology loss: **0**.
- **Class:** experiment (hold; exact, not general 10×)

## 2026-10-13 — I228 in-tree --engine redzed

- **Question:** Does wrapping vendored RedZeD (`22ef1bf`, MIT) as `--engine redzed` keep I227’s exact mixed-homology identity and the torus 10× without the PyPI wheel?
- **Hypothesis:** Same C++ as `redzed-tda` 0.1.1. Collapse skipped (full metric). Shape-agnostic. Topology loss 0 if the bridge copies bars correctly.
- **Work:** `third_party/redzed/` + `persist_redzed` + wave 89 vs Ripser / default PITH / I227 times.
- **Result:** **Exact 13/13** (0 unmatched; ess H1 matches; bottleneck ~1e-7). Torus n=2000 **12.3×** vs Ripser (0.21s/2.52s) and **8.3×** vs default PITH (1.72s). Circle n=2000 35.8× vs Ripser, **0.43×** vs PITH. blobs/sphere/uniform2 5.4–7.7× vs Ripser and 2.8–3.9× vs PITH. Times match I227 wheel.
- **Decision:** **Support as owned exact engine.** Recommend for mixed/real data. Do **not** switch CLI default (circle collapse still faster). Topology loss: **0**. Next: from-scratch reimplementation (drop vendor) and larger-n 10× on blobs/sphere/uniform2. Complexity still a measured exponent gap, not a proven better worst-case class.
- **Class:** experiment (support; owned exact torus 10×)

## 2026-10-13 — I227 real RedZeD engine (H09) + GUDHI collapse

- **Question:** Is `redzed-tda` a real unused exact VR engine (not I122’s leftover-triangle fake), and is the torus collapse wall an implementation gap vs GUDHI 3.13?
- **Hypothesis:** Kapulkin–Kershaw RedZeD (arXiv:2606.06310) is MIT. Active enumeration skips most (n+1)-birth columns. Same path on every distance matrix — shape-agnostic. Should match Ripser H1. GUDHI flag collapse on the same \(G_T\) tests whether PITH’s 1.4 s torus collapse is just a slow implementation.
- **Work:** pip `redzed-tda==0.1.1`. Wave 88 vs Ripser + default PITH on unit square / circle / blobs / sphere / torus / uniform2 / two_circles / figure8 (n≤2000). GUDHI `flag_filtration.edge_collapse` on circle/blobs/torus n=2000.
- **Result:** **Exact 18/18** (0 unmatched; bottleneck ~1e-7–1e-6; ess H1 matches including figure8 / two_circles / unit square). n=2000 vs Ripser: circle **33.4×**, torus **11.7×**, sphere 6.9×, blobs 4.9×, uniform2 4.5×. vs PITH default: torus **7.5×**, blobs 3.0×, sphere 3.6×, uniform2 2.4×, circle **0.45×** (collapse+implicit still faster). Time slopes RedZeD \(n^{2.03–2.38}\) vs Ripser \(n^{2.04–3.03}\) vs PITH \(n^{1.72–2.67}\). GUDHI collapse is **slower** than PITH (circle 7.94 s vs 273 ms; torus 4.05 s vs 1.40 s); residual |E'| matches (5169 / 6169 / 163426).
- **Decision:** **Support as a real exact engine** (external). First exact torus 10×; topology loss **0**. Do **not** switch PITH default (PyPI wheel). GUDHI collapse is not the torus gap — the wall is algorithmic. Next: owned active-enumeration reimplementation. H07 kd-tree deprioritized (Euclidean-only). Complexity is a measured exponent gap, not a proven better worst-case class.
- **Class:** experiment (support identity + torus 10×; reject as default until owned)

## 2026-10-13 — I226 witness-shrink first_dominator (exact)

- **Question:** Do torus keeps form a suffix we can skip, and if not, does iterated N_t[fail_w] shrinking of the apex pool cut the fail-path without changing PH?
- **Hypothesis:** keep_hist on n=2000: circle/sphere/uniform2/blobs are a last-bucket suffix; **torus keeps span buckets 6–15** (134k early keeps) — skip-oldest is not a cut. Each failed apex at w implies later dominators ⊆ N_t[w]. Same exists-dominator. Shape-agnostic.
- **Work:** `first_dominator_shrink` as default; wave 87 vs src+Ripser.
- **Result:** **Exact 5/5.** Torus skips **6.12M**, tests **9.04M vs 12.5M**, collapse **1450 vs 1470** ms (1.54×). circle 275 vs 263 / 73×; blobs 196 vs 190; sphere 357 vs 365. Residual 163426 identical.
- **Decision:** **Reject and revert** from the hot path. 28% fewer tests did not show up in wall-clock (compact tax / memory-bound Tm). Shrink stays compiled, unused. Topology loss: **0**. Default I193+I197+I202+I203 unchanged.
- **Class:** experiment (reject; exact but not faster)

## 2026-10-13 — I225 reduced VR all-pairs lune (H07)

- **Question:** Is I224’s construction wall the \(O(|L|\cdot\deg)\) neighbor walk, and does all-pairs connectivity (same Def 3.3 edges) cut it without changing the 2-complex?
- **Hypothesis:** Most lunes have \(|L|\ll\deg\) on \(G_T\). With the distance matrix, each pair is \(O(1)\). Singleton lunes skip UF. Same representatives ⇒ same PH₁. Shape-agnostic.
- **Work:** `build_reduced_triangles(..., dist*)`; wave 86 vs Ripser + I224 receipts.
- **Result:** **Exact 13/13** (0 unmatched; ess H1 matches including figure8 / two_circles / unit square). Triangle counts **identical** to I224. Construction **2.3–3.7×** vs I224 (median 2.7×). circle n=500: 2617→701 ms build, 0.73s / **0.42×** vs Ripser 0.31s (was 0.12×). Still loses to default PITH (15 ms).
- **Decision:** **Support as construction** on the experimental `--reduced-vr` path. Do **not** select as default. Topology loss: **0**. Remaining H07 cost is lune membership (neighbor merge), not UF. Default unchanged.
- **Class:** experiment (support construction; reject as default clock)

## 2026-10-13 — I164 collapse live-degree trace

- **Question:** Does the live 1-skeleton thin early enough to stop the C-walk?
- **Result:** **No.** Live edges drop **1:1** with the backward scan (circle2000: at 50% processed, live=538565, kept=0). Residual appears only as a **suffix** of oldest edges (last ~5k). Blobs: a few dozen mid-scan keeps, then the same suffix. Early-stop leaves a thick graph.
- **Decision:** Do not early-stop. Must visit essentially every edge. Per-edge C-walk remains the wall.
- **Class:** reproduced

## 2026-10-13 — I163 ROI probe

- **Question:** Does leftover-apparent rate separate circle T=1.5 from I162 losers?
- **Result:** **No.** leftover_apparent=1.0 and domination=1.0 on circle, blobs, torus, sphere, uniform2. Probe cannot decide skip. leftover_median/mst_max is higher on circle (9.0) than blobs (1.1) but sphere is 7.5 (would still collapse and lose).
- **Decision:** Do not wire skip on apparent rate. I164: trace when the live 1-skeleton thins.
- **Class:** experiment (negative as a skip oracle)

## 2026-10-13 — I162 other-family H1 n=2000

- **Question:** Does pair-nbr+fused hit H1 10× off-circle?
- **Result:** Exact 5/5. **No.** Best off-peak circle T=1.2 is **4.13×**. blobs **0.32×**, torus **0.74×** (residual 163k, reduce 431 ms), sphere **0.17×**, uniform2 **0.30×**. Collapse still shrinks those graphs (blobs 655k→6k) but costs more than Ripser's full PH.
- **Decision:** 9.50× is a circle T≈1.5 phenomenon. H1 10× is not general. Next: skip/cost-model collapse when Ripser is cheap; RedZeD on thick torus residuals.
- **Class:** reproduced
