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
