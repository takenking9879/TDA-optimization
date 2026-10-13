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

## 2026-10-13 — I174 suffix-k (in progress)

- **Question:** Do young shift-keeps fail first-apex early enough that a K-sample cheap-trim + tail collapse is exact?
- **Hypothesis:** Fail→leave is always safe. Pass→trim is unsafe only if a sequential keep passes the sample. Measure `fail_at` / `any_later` on the 97, then sweep K=0,2,8,32.
- **Class:** experiment running

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
