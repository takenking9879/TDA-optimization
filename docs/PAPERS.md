# Annotated bibliography — persistent-homology algorithms

This file is the project bibliography for designing a new persistent-homology
(PH) algorithm. It is **not** an implementation plan. Entries are original or
authorised open-access versions, selected for algorithm design rather than
coverage of TDA applications.

Collected 13 October 2026. PDFs were downloaded only from arXiv, LIPIcs,
author pages, official project pages, or GitHub release trees. Paywalled
publisher PDFs were not downloaded. HAL blocked automated download of the
short GUDHI library report; that paper is cited by official URL only.

**How to use.** Start with the eight must-read papers, then the topic that
matches the next design decision (complex, reduction, or parallel strategy).
Treat 2022–2026 speed claims as hypotheses to re-benchmark, not as settled
complexity improvements.

---

## 8 must-read papers for algorithm design

These eight are the minimum set for choosing a representation, a reduction
strategy, and a first CPU baseline. Read them in this order.

| # | Paper | Why it is required |
|---|---|---|
| 1 | Bauer, *Ripser* (2019/2021) | Current implicit-cohomology baseline: coboundary-on-the-fly, apparent pairs, emergent pairs, clearing. |
| 2 | de Silva, Morozov, Vejdemo-Johansson, *Dualities* (2011) | Why cohomology is usually faster than homology, and when that advantage disappears. |
| 3 | Chen and Kerber, *Twist* (2011) | Clearing: skip roughly half the columns after pairing in the next dimension. |
| 4 | Boissonnat and Pritam, *Edge Collapse* (2020) | Exact 1-skeleton reduction of flag/VR filtrations before any matrix work. |
| 5 | Sheehy, *Sparse Rips* (2013) | Linear-size VR approximation with a multiplicative bottleneck guarantee. |
| 6 | Burella Pérez et al., *giotto-ph* (2021) | Best documented CPU combination of lock-free reduction, apparent pairs, and edge collapse. |
| 7 | Kapulkin and Kershaw, *RedZeD* (2026) | Recent alternative to Ripser-style implicit cohomology (active enumeration / zero differentials). Must re-benchmark. |
| 8 | Bauer and Edelsbrunner, *Morse theory of Čech and Delaunay* (2017) | Exact homotopy relation among Čech, Alpha, Delaunay–Čech, and Wrap; grounds the complex choice. |

---

## Downloaded PDFs

All files live in `/workspace/papers/`. Sizes are as downloaded.

| Local path | Paper |
|---|---|
| `papers/bauer-2019-ripser.pdf` | Bauer, Ripser |
| `papers/de-silva-2011-dualities.pdf` | Dualities in persistent (co)homology |
| `papers/chen-2011-twist.pdf` | Persistent homology computation with a twist |
| `papers/bauer-2013-clear-compress.pdf` | Clear and compress |
| `papers/edelsbrunner-2002-persistence.pdf` | Topological persistence and simplification |
| `papers/zhang-2020-ripserpp.pdf` | Ripser++ |
| `papers/burella-perez-2021-giotto-ph.pdf` | giotto-ph |
| `papers/boissonnat-2014-simplex-tree.pdf` | Simplex tree |
| `papers/boissonnat-2013-annotation-matrix.pdf` | Compressed annotation matrix |
| `papers/edelsbrunner-1994-alpha-shapes.pdf` | Three-dimensional alpha shapes |
| `papers/bauer-2017-morse-cech-delaunay.pdf` | Morse theory of Čech and Delaunay |
| `papers/boissonnat-2020-edge-collapse.pdf` | Edge collapse of flag complexes |
| `papers/glisse-2022-edge-collapse-extensions.pdf` | Swap, shift and trim |
| `papers/boissonnat-2018-strong-collapse.pdf` | Strong collapse for persistence |
| `papers/sheehy-2013-sparse-rips.pdf` | Linear-size sparse Rips |
| `papers/de-silva-2004-witness.pdf` | Witness complexes |
| `papers/mischaikow-2013-morse-filtrations.pdf` | Morse theory for filtrations |
| `papers/koyama-2024-distilled-vr.pdf` | Distilled Vietoris–Rips |
| `papers/bauer-2022-apparent-pairs-hyperbolic.pdf` | Apparent pairs / hyperbolicity |
| `papers/bauer-2024-wrapping-cycles.pdf` | Wrapping cycles |
| `papers/bauer-2013-distributed-ph.pdf` | DIPHA / distributed PH |
| `papers/lewis-2015-blowup.pdf` | Mayer–Vietoris blowup PH |
| `papers/nigmetov-2024-distributed-cohomology.pdf` | Cadmus / distributed cohomology |
| `papers/kapulkin-2026-redzed.pdf` | RedZeD |
| `papers/cufar-2023-involuted-ph.pdf` | Involuted persistent homology |
| `papers/openai-2026-integer-multiplication.pdf` | Integer multiplication below \(n\log n\) (methodology only) |

**Not downloaded (open citation only).**

- Maria et al., GUDHI library report — HAL served a bot-check page.
- Zomorodian and Carlsson, *Computing persistent homology* — Stanford host returned 403.
- Morozov and Nigmetov, *Towards lockfree persistent homology* — ACM is paywalled; the author PDF URL 404s. Use the author HTML page.
- CrocSwap `integer-mult-bounds` — research repository, not a paper.

---

## 1. Ripser and persistent cohomology

### 1.1 Ripser: efficient computation of Vietoris–Rips persistence barcodes

- **Authors:** Ulrich Bauer
- **Year:** 2019 preprint; journal 2021
- **DOI / arXiv / URL:** [arXiv:1908.02518](https://arxiv.org/abs/1908.02518); DOI [10.1007/s41468-021-00071-5](https://doi.org/10.1007/s41468-021-00071-5); software [ripser.org](http://ripser.org)
- **Local PDF:** `papers/bauer-2019-ripser.pdf`
- **Main technique:** Implicit coboundary: never store the filtration or coboundary matrix. Recompute cofacets and diameters on demand. Apparent pairs give a discrete gradient from the simplex order. Emergent (zero-persistence) cofacet pairs stop column construction early. Clearing is applied in cohomology.
- **What we should read:** §§2–4 (implicit representation, apparent/emergent pairs, clearing, combinatorial numbering of simplices). The experimental section is the baseline we must beat or match.
- **Usable idea:** A new algorithm should not materialise the full VR coboundary matrix. Apparent pairs plus emergent-pair early abort are the cheapest exact reductions we have. Combinatorial simplex IDs (combinadic numbering) are the default encoding.

### 1.2 Dualities in persistent (co)homology

- **Authors:** Vin de Silva, Dmitriy Morozov, Mikael Vejdemo-Johansson
- **Year:** 2011
- **DOI / arXiv / URL:** [arXiv:1107.5665](https://arxiv.org/abs/1107.5665); DOI [10.1088/0266-5611/27/12/124003](https://doi.org/10.1088/0266-5611/27/12/124003); author page [mrzv.org](https://mrzv.org/publications/dualities-persistence/)
- **Local PDF:** `papers/de-silva-2011-dualities.pdf`
- **Main technique:** Absolute/relative homology and cohomology persistence modules carry the same barcode. Algorithms: `pHcol` (classic column reduction), `pHrow`, and optimised `pCoh`.
- **What we should read:** The four persistence modules and the `pCoh` optimisation. The experiments explain why cohomology wins on VR.
- **Usable idea:** Prefer cohomology for VR barcodes. If we need representative cycles, do **not** switch the whole computation to homology; use involuted PH (Čufar–Virk) on top of cohomology.

---

## 2. Ripser++ (GPU)

### 2.1 GPU-accelerated computation of Vietoris–Rips persistence barcodes

- **Authors:** Simon Zhang, Mengbai Xiao, Hao Wang
- **Year:** 2020 (SoCG; arXiv v4 updated 2026)
- **DOI / arXiv / URL:** [arXiv:2003.07989](https://arxiv.org/abs/2003.07989); DOI [10.4230/LIPIcs.SoCG.2020.70](https://doi.org/10.4230/LIPIcs.SoCG.2020.70); code [github.com/simonzhang00/ripser-plusplus](https://github.com/simonzhang00/ripser-plusplus)
- **Local PDF:** `papers/zhang-2020-ripserpp.pdf`
- **Main technique:** Split Ripser into (i) filtration construction + clearing + apparent-pair search on GPU and (ii) residual non-apparent column reduction on CPU. Gives bounds on apparent-pair rate (often >99% of columns).
- **What we should read:** The two-stage split, apparent-pair rate theorems, and the “separation of parallelisms” argument. Ignore marketing speedups until we reproduce them.
- **Usable idea:** Apparent-pair search is data-parallel and GPU-friendly; residual reduction is sequential and should stay on CPU. This is a **later** GPU extension, not the first CPU core. Keep Ripser++ as the GPU reference, not as the new kernel.

Related (not downloaded): Zhang et al., *HYPHA* (ICS 2019) — earlier CPU/GPU split of matrix reduction.

---

## 3. giotto-ph parallelization

### 3.1 giotto-ph: a Python library for high-performance computation of PH of Vietoris–Rips filtrations

- **Authors:** Julián Burella Pérez, Sydney Hauke, Umberto Lupo, Matteo Caorsi, Alberto Dassatti
- **Year:** 2021
- **DOI / arXiv / URL:** [arXiv:2107.05412](https://arxiv.org/abs/2107.05412); code [github.com/giotto-ai/giotto-ph](https://github.com/giotto-ai/giotto-ph)
- **Local PDF:** `papers/burella-perez-2021-giotto-ph.pdf`
- **Main technique:** Lock-free multicore Ripser (Morozov–Nigmetov) + parallel apparent-pair search + a reworked GUDHI edge collapser. Claims to beat Ripser++ on 5–10 CPU cores on their suite.
- **What we should read:** How the three ideas are combined, which data structures changed, and the edge-collapser rewrite (fewer dependencies than GUDHI).
- **Usable idea:** The **combination** is the product: collapse the 1-skeleton, find apparent pairs in parallel, reduce the rest lock-free. This is the strongest existing CPU recipe and the first thing our benchmarks must include. Do not treat the “beats GPU” claim as general.

---

## 4. GUDHI complexes

### 4.1 The GUDHI library: simplicial complexes and persistent homology

- **Authors:** Clément Maria, Jean-Daniel Boissonnat, Marc Glisse, Mariette Yvinec
- **Year:** 2014
- **DOI / arXiv / URL:** HAL [hal-01005601](https://hal.inria.fr/hal-01005601); ICMS DOI [10.1007/978-3-662-44199-2_28](https://doi.org/10.1007/978-3-662-44199-2_28); docs [gudhi.inria.fr](https://gudhi.inria.fr)
- **Local PDF:** *not downloaded* (HAL bot-check)
- **Main technique:** Simplex tree as the generic filtered complex; persistent cohomology via the compressed annotation matrix; multi-field coefficients.
- **What we should read:** The software architecture: `FilteredComplex` + `Persistent_cohomology`. Use it as a map of which GUDHI packages implement which complexes.
- **Usable idea:** GUDHI is the reference for **explicit** complexes (Alpha, Witness, Čech, cubical, collapsed Rips). It is not the VR-speed champion. Keep it as the complex-construction baseline.

### 4.2 The simplex tree: an efficient data structure for general simplicial complexes

- **Authors:** Jean-Daniel Boissonnat, Clément Maria
- **Year:** 2014 (Algorithmica; arXiv 2020)
- **DOI / arXiv / URL:** [arXiv:2001.02581](https://arxiv.org/abs/2001.02581); DOI [10.1007/s00453-014-9887-3](https://doi.org/10.1007/s00453-014-9887-3)
- **Local PDF:** `papers/boissonnat-2014-simplex-tree.pdf`
- **Main technique:** Trie on lexicographic vertex words; nodes ↔ simplices; fast coface/face queries. Experiments on Rips and Witness.
- **What we should read:** Construction cost, memory, and the Rips/Witness experiments.
- **Usable idea:** Use a simplex tree when the complex is **not** a flag complex we can keep implicit. For VR, Ripser’s implicit scheme is smaller. For Alpha/Witness/collapsed complexes that we actually store, this is the default.

### 4.3 The compressed annotation matrix: an efficient data structure for computing persistent cohomology

- **Authors:** Jean-Daniel Boissonnat, Tamal K. Dey, Clément Maria
- **Year:** 2013 (ESA; Algorithmica 2015)
- **DOI / arXiv / URL:** [arXiv:1304.6813](https://arxiv.org/abs/1304.6813)
- **Local PDF:** `papers/boissonnat-2013-annotation-matrix.pdf`
- **Main technique:** Annotation vectors on simplices, stored in a compressed matrix, implementing the Dey–Fan–Wang cohomology algorithm with a simplification heuristic.
- **What we should read:** How annotations differ from Ripser’s implicit coboundary columns.
- **Usable idea:** Useful when the complex is explicit and we want cohomology without Ripser’s VR-specific numbering. Not a replacement for implicit VR.

---

## 5. Alpha complexes

### 5.1 Three-dimensional alpha shapes

- **Authors:** Herbert Edelsbrunner, Ernst P. Mücke
- **Year:** 1994
- **DOI / arXiv / URL:** [arXiv:math/9410208](https://arxiv.org/abs/math/9410208); DOI [10.1145/174462.156635](https://doi.org/10.1145/174462.156635)
- **Local PDF:** `papers/edelsbrunner-1994-alpha-shapes.pdf`
- **Main technique:** Family of polytopes from the 3D Delaunay triangulation, parameter \(\alpha\) = empty circumsphere radius. \(O(n^2)\) construction of the whole family.
- **What we should read:** The Delaunay-subcomplex definition and the filtration by \(\alpha\).
- **Usable idea:** For Euclidean point clouds in dimension 2–3, Alpha is exact for the Čech homotopy type (with the Morse paper below) and has size \(\Theta(n^{\lceil d/2\rceil})\) rather than \(\binom{n}{k+1}\). First-round benchmark family for low-d Euclidean data. Do **not** use it as a general metric-space complex.

### 5.2 The Morse theory of Čech and Delaunay complexes

- **Authors:** Ulrich Bauer, Herbert Edelsbrunner
- **Year:** 2017 (arXiv 2013)
- **DOI / arXiv / URL:** [arXiv:1312.1231](https://arxiv.org/abs/1312.1231); DOI [10.1090/tran/6991](https://doi.org/10.1090/tran/6991)
- **Local PDF:** `papers/bauer-2017-morse-cech-delaunay.pdf`
- **Main technique:** Čech and Delaunay (Alpha) as sublevel sets of generalized discrete Morse functions. One discrete gradient realises the collapses Čech \(\searrow\) Delaunay–Čech \(\searrow\) Alpha \(\searrow\) Wrap.
- **What we should read:** The collapsing theorem and the Wrap construction.
- **Usable idea:** Alpha and Čech have the same persistent homology (simple-homotopy equivalent at each scale). Wrap is a still-smaller complex supporting the same cycles (see also wrapping-cycles, 2024). This is the mathematical licence to benchmark Alpha instead of Čech in Euclidean space.

---

## 6. Edge collapse for Vietoris–Rips

### 6.1 Edge collapse and persistence of flag complexes

- **Authors:** Jean-Daniel Boissonnat, Siddharth Pritam
- **Year:** 2020
- **DOI / arXiv / URL:** DOI [10.4230/LIPIcs.SoCG.2020.19](https://doi.org/10.4230/LIPIcs.SoCG.2020.19) (LIPIcs, CC-BY; no arXiv)
- **Local PDF:** `papers/boissonnat-2020-edge-collapse.pdf`
- **Main technique:** Dominated edges (link is a cone) can be removed using only the 1-skeleton. The residual is still flag. The collapsed flag filtration has the **same persistence** as the original.
- **What we should read:** Definitions of domination, the 1-skeleton algorithm, and the exactness theorem. Experiments: orders-of-magnitude fewer simplices before reduction.
- **Usable idea:** Highest-priority **exact** preprocessor for VR/flag filtrations. Combine with Ripser-style implicit cohomology (as giotto-ph does). Measure collapse ratio on every dataset; it is data-dependent.

### 6.2 Swap, shift and trim to edge collapse a filtration

- **Authors:** Marc Glisse, Siddharth Pritam
- **Year:** 2022
- **DOI / arXiv / URL:** [arXiv:2203.07022](https://arxiv.org/abs/2203.07022)
- **Local PDF:** `papers/glisse-2022-edge-collapse-extensions.pdf`
- **Main technique:** Re-explains edge collapse as swap/shift/trim on the 1-skeleton; extends the method to zigzag filtrations.
- **What we should read:** The intuitive rewrite of domination, and the zigzag extension.
- **Usable idea:** Prefer this paper when implementing or debugging a collapser. Zigzag support is optional for v1.

### 6.3 Strong collapse for persistence

- **Authors:** Jean-Daniel Boissonnat, Siddharth Pritam, Divyansh Pareek
- **Year:** 2018
- **DOI / arXiv / URL:** [arXiv:1809.10945](https://arxiv.org/abs/1809.10945); flag-complex SoCG version DOI [10.4230/LIPIcs.SoCG.2019.55](https://doi.org/10.4230/LIPIcs.SoCG.2019.55)
- **Local PDF:** `papers/boissonnat-2018-strong-collapse.pdf`
- **Main technique:** Barmak–Minian strong collapses (dominated vertices) as a PH preprocessor; works for towers and zigzags; only maximal simplices need to be stored; collapses can run in parallel.
- **What we should read:** How strong collapse differs from edge collapse (vertices vs edges; towers vs filtrations).
- **Usable idea:** Edge collapse superseded this for flag filtrations. Keep strong collapse for non-flag towers. Do not run both as a default stack without measuring.

---

## 7. Sparse Rips and guarantees

### 7.1 Linear-size approximations to the Vietoris–Rips filtration

- **Authors:** Donald R. Sheehy
- **Year:** 2013 (SoCG 2012)
- **DOI / arXiv / URL:** [arXiv:1203.6786](https://arxiv.org/abs/1203.6786); DOI [10.1007/s00454-013-9513-1](https://doi.org/10.1007/s00454-013-9513-1)
- **Local PDF:** `papers/sheehy-2013-sparse-rips.pdf`
- **Main technique:** Hierarchical net-tree. Points are deleted as the scale grows. Produces a zigzag sparse filtration or an equivalent non-zigzag filtration of size \(O(n)\), built in \(O(n\log n)\). Persistence diagram is a multiplicative \(c\)-approximation of VR, \(c = 1/(1-2\varepsilon)\); \(k\)-skeleton constants \((1/\varepsilon)^{O(kd)}\) in doubling dimension \(d\).
- **What we should read:** Guarantee statements (Theorems 9.x), the net-tree construction, and the zigzag vs non-zigzag variants.
- **Usable idea:** The only VR sparsifier in this list with a **theorem**. Use when exact VR is infeasible. Label results “approximation with guarantee”, never “same barcode”. Constants explode with ambient/doubling dimension — measure that before promising scale.

---

## 8. Witness complexes

### 8.1 Topological estimation using witness complexes

- **Authors:** Vin de Silva, Gunnar Carlsson
- **Year:** 2004
- **DOI / arXiv / URL:** Eurographics [10.2312/SPBG.SPBG04.157-166](https://diglib.eg.org/items/fd03e9fe-d315-4c7d-8220-7b0ff2449fff) (conference OA)
- **Local PDF:** `papers/de-silva-2004-witness.pdf`
- **Main technique:** Choose landmarks \(L\); remaining points are witnesses for simplices on \(L\). Strong vs weak witnesses; nested families \(W(D;R)\) for persistence. Input is the landmark–data distance matrix, any metric.
- **What we should read:** Definitions of \(W(D)\) and the weak-witness theorem; the landmark-size vs noise discussion.
- **Usable idea:** Landmarking is a **vertex** reduction, complementary to edge collapse (edge reduction). Persistence is not automatically that of full VR. Treat as a third class: empirical / landmark-dependent. GUDHI implements this; include it in the first benchmark round for large \(n\).

---

## 9. Discrete Morse theory and distilled VR

### 9.1 Morse theory for filtrations and efficient computation of persistent homology

- **Authors:** Konstantin Mischaikow, Vidit Nanda
- **Year:** 2013
- **DOI / arXiv / URL:** DOI [10.1007/s00454-013-9529-6](https://doi.org/10.1007/s00454-013-9529-6); author PDF [people.maths.ox.ac.uk/nanda](https://people.maths.ox.ac.uk/nanda/source/DMPers-Final.pdf)
- **Local PDF:** `papers/mischaikow-2013-morse-filtrations.pdf`
- **Main technique:** Extends Forman discrete Morse theory from a complex to a filtration. `MorseReduce` outputs a smaller Morse filtration with identical PH.
- **What we should read:** Theorem 4.3 (Morse filtration ≡ original PH) and Algorithm `MorseReduce`.
- **Usable idea:** Exact algebraic/combinatorial reduction that is not VR-specific. Apparent pairs are a cheap special Morse matching. A custom matching could remove more, at the cost of building the complex. Use on explicit complexes (Alpha, cubical, collapsed Rips).

### 9.2 The distilled Vietoris–Rips filtration and a new memory-efficient algorithm

- **Authors:** Musashi Ayrton Koyama, Vanessa Robins, Katharine Turner
- **Year:** 2024
- **DOI / arXiv / URL:** [arXiv:2412.07805](https://arxiv.org/abs/2412.07805)
- **Local PDF:** `papers/koyama-2024-distilled-vr.pdf`
- **Main technique:** Discrete Morse matching on a reduced VR complex; keep only simplices reachable from critical \((q+1)\)-simplices. Claims PH isomorphic to standard VR; parallel, memory-light \(H_1\) algorithm from the distance matrix.
- **What we should read:** Definitions of reduced vs distilled VR and Theorem 3.9. Then treat the isomorphism as **unverified**.
- **Usable idea:** The *intent* — store only simplices that can affect degree-\(q\) PH — is the right research direction. A reported counterexample (unit square: standard VR has \(H_1\cong\mathbb{Z}_2\) at scale 1, distilled complex empty) means we must not implement this as a correct preprocessor until the proof is repaired or the counterexample is refuted. Classify as “proposal, not established”.

---

## 10. Matrix reduction for PH

### 10.1 Topological persistence and simplification

- **Authors:** Herbert Edelsbrunner, David Letscher, Afra Zomorodian
- **Year:** 2002
- **DOI / arXiv / URL:** DOI [10.1007/s00454-002-2885-2](https://doi.org/10.1007/s00454-002-2885-2); author PDF [pub.ista.ac.at/~edels](https://pub.ista.ac.at/~edels/Papers/2002-04-TopologicalPersistence.pdf)
- **Local PDF:** `papers/edelsbrunner-2002-persistence.pdf`
- **Main technique:** Original incremental pairing algorithm on a filtration (developed for Alpha complexes). Positive/negative simplices; persistence of a cycle is its lifetime.
- **What we should read:** The pairing algorithm (Section 4) and the filtration viewpoint.
- **Usable idea:** Historical root of every column-reduction code. Necessary to see what later optimisations (twist, clearing, cohomology) actually change.

### 10.2 Computing persistent homology

- **Authors:** Afra Zomorodian, Gunnar Carlsson
- **Year:** 2005
- **DOI / arXiv / URL:** DOI [10.1007/s00454-004-1146-y](https://doi.org/10.1007/s00454-004-1146-y); official PDF [geometry.stanford.edu/papers/zc-cph-05/zc-cph-05.pdf](https://geometry.stanford.edu/papers/zc-cph-05/zc-cph-05.pdf)
- **Local PDF:** *not downloaded* (host returned 403)
- **Main technique:** PH as graded \(F[t]\)-module homology. Structure theorem over fields ⇒ barcodes. Standard reduction over any field, any dimension.
- **What we should read:** The algebraic justification of the reduction algorithm and why it fails over \(\mathbb{Z}\).
- **Usable idea:** Barcodes exist over fields. Our default coefficient field is \(\mathbb{F}_2\) unless we have a torsion reason to change it.

### 10.3 Persistent homology computation with a twist

- **Authors:** Chao Chen, Michael Kerber
- **Year:** 2011
- **DOI / arXiv / URL:** EuroCG 2011; author PDFs [chaochen.github.io](https://chaochen.github.io/publications/chen_eurocg_2011.pdf), [kerber, TU Graz](https://www.geometrie.tugraz.at/kerber/kerber_papers/ck-phcwat-11.pdf)
- **Local PDF:** `papers/chen-2011-twist.pdf`
- **Main technique:** Process dimensions decreasingly. Once \((\sigma,\tau)\) is paired, the column of \(\sigma\) can be zeroed without reduction (“clearing” / “twist”). Avoids reduction of about half the columns. Output-sensitive analysis.
- **What we should read:** The whole 4-page note. It is the clearing optimisation used by Ripser, PHAT, DIPHA, giotto-ph.
- **Usable idea:** Mandatory in any homology-style reduction. In cohomology the same idea clears *death* columns after pairing. Do not reinvent this.

### 10.4 Clear and compress: computing persistent homology in chunks

- **Authors:** Ulrich Bauer, Michael Kerber, Jan Reininghaus
- **Year:** 2013
- **DOI / arXiv / URL:** [arXiv:1303.0477](https://arxiv.org/abs/1303.0477); DOI [10.1007/978-3-319-04099-8_7](https://doi.org/10.1007/978-3-319-04099-8_7)
- **Local PDF:** `papers/bauer-2013-clear-compress.pdf`
- **Main technique:** (1) Reduce local chunks, (2) compress unpaired/global columns, (3) twist-reduce the small remainder. Parallelisable; generalises a Morse-theoretic chunk method. Implemented in PHAT.
- **What we should read:** The three-stage algorithm and which steps parallelise.
- **Usable idea:** Chunking is the shared-memory ancestor of DIPHA. Useful if we store an explicit boundary matrix (Alpha, cubical, Morse-reduced). Less relevant for fully implicit VR.

---

## 11. Oineus / parallel PH

### 11.1 Towards lockfree persistent homology

- **Authors:** Dmitriy Morozov, Arnur Nigmetov
- **Year:** 2020 (SPAA brief announcement)
- **DOI / arXiv / URL:** DOI [10.1145/3350755.3400244](https://doi.org/10.1145/3350755.3400244); author page [mrzv.org/publications/lockfree-persistence](https://mrzv.org/publications/lockfree-persistence/); software [github.com/anigmetov/oineus](https://github.com/anigmetov/oineus)
- **Local PDF:** *not downloaded* (ACM paywalled; author `.pdf` 404). Read the author HTML.
- **Main technique:** Do **not** partition domain or filtration range. Parallelise the reduction itself with compare-and-swap on column writes. Drop-in replacement for sequential reduction; combinable with Ripser optimisations. Main inner loop is wait-free; outer loop is not.
- **What we should read:** The contrast with PHAT (range) and blowup (domain); the CAS reduction sketch.
- **Usable idea:** This is the parallel reduction inside giotto-ph and Oineus. Prefer it over inventing a data partition. Open question they state: make the whole algorithm wait-free.

Oineus also implements Nigmetov–Morozov *Topological optimization with big steps*, [arXiv:2203.16748](https://arxiv.org/abs/2203.16748) (critical sets; not a barcode-speed paper).

---

## 12. Distributed persistent homology

### 12.1 Distributed computation of persistent homology

- **Authors:** Ulrich Bauer, Michael Kerber, Jan Reininghaus
- **Year:** 2013/2014 (ALENEX; DIPHA)
- **DOI / arXiv / URL:** [arXiv:1310.0710](https://arxiv.org/abs/1310.0710); code [github.com/DIPHA/dipha](https://github.com/DIPHA/dipha)
- **Local PDF:** `papers/bauer-2013-distributed-ph.pdf`
- **Main technique:** MPI distribution of boundary-matrix **columns** with no replica of the full matrix. Communication pays for itself vs sequential/shared-memory on large instances. Reports \(>10^9\) cells on 32 nodes, <10 GB/node.
- **What we should read:** Data layout and communication pattern. Inputs: cubical images, (sparse) distance matrices, explicit weighted boundary matrices.
- **Usable idea:** This distributes **one global filtration**, not independent subset barcodes. Use as the correctness test for any “distributed PH” proposal. Communication of pivot columns is the bottleneck.

### 12.2 Parallel computation of persistent homology using the blowup complex

- **Authors:** Ryan Lewis, Dmitriy Morozov
- **Year:** 2015
- **DOI / arXiv / URL:** DOI [10.1145/2755573.2755587](https://doi.org/10.1145/2755573.2755587); LBNL PDF [dav.lbl.gov/.../LBNL-177165.pdf](https://dav.lbl.gov/archive/Publications/2015/LBNL-177165.pdf)
- **Local PDF:** `papers/lewis-2015-blowup.pdf`
- **Main technique:** Spatial (domain) partition. Glue local PH with the Mayer–Vietoris blowup complex. `Cascade` merges pairs from subspaces.
- **What we should read:** Why domain partition is harder than column partition, and the limitations section.
- **Usable idea:** The only mathematically honest way to split a point cloud spatially and still get **global** PH. Blowup size is the cost. Do not “compute PH on shards and union the diagrams”.

### 12.3 Distributed computation of persistent cohomology

- **Authors:** Arnur Nigmetov, Dmitriy Morozov
- **Year:** 2024 preprint; ALENEX 2026
- **DOI / arXiv / URL:** [arXiv:2410.16553](https://arxiv.org/abs/2410.16553); author page [mrzv.org](https://www.mrzv.org/publications/distributed-computation-of-persistent-cohomology/)
- **Local PDF:** `papers/nigmetov-2024-distributed-cohomology.pdf`
- **Main technique:** Cadmus: local domain/range partition to reduce and sparsify coboundary blocks, then redistribute for global cohomology reduction. MPI + DIY. Strong-scaling win vs DIPHA on Perlmutter.
- **What we should read:** The two-phase local-then-global schedule and the comparison with DIPHA.
- **Usable idea:** Most recent distributed **cohomology** algorithm. If we later distribute implicit VR cohomology, start here rather than from 2013 DIPHA homology.

---

## 13. Apparent and emergent pairs

Apparent and emergent pairs are defined and used in Bauer’s Ripser paper (entry 1.1). The two papers below give the geometric meaning and a reconstruction link.

### 13.1 Gromov hyperbolicity, geodesic defect, and apparent pairs in Vietoris–Rips filtrations

- **Authors:** Ulrich Bauer, Fabian Roll
- **Year:** 2022 (SoCG)
- **DOI / arXiv / URL:** [arXiv:2112.06781](https://arxiv.org/abs/2112.06781); DOI [10.4230/LIPIcs.SoCG.2022.15](https://doi.org/10.4230/LIPIcs.SoCG.2022.15)
- **Local PDF:** `papers/bauer-2022-apparent-pairs-hyperbolic.pdf`
- **Main technique:** Apparent pairs = discrete gradient. On finite \(\delta\)-hyperbolic \(\nu\)-geodesic spaces, a compatible gradient collapses \(\mathrm{Rips}_u\to\mathrm{Rips}_t\to\{\ast\}\) for \(u>t\ge 4\delta+2\nu\). On tree metrics, the **apparent-pair** gradient collapses Rips to the subforest — which is why Ripser is unusually fast on tree-like data.
- **What we should read:** Theorems 3 and 5, and the definition of geodesic defect.
- **Usable idea:** Apparent-pair rate is a **geometric** property, not just an implementation trick. Datasets that are tree-like or hyperbolic will look artificially easy. Benchmarks must include non-hyperbolic, high-loop data (tori, spheres, high-d noise).

### 13.2 Wrapping cycles in Delaunay complexes: bridging persistent homology and discrete Morse theory

- **Authors:** Ulrich Bauer, Fabian Roll
- **Year:** 2024 (SoCG; arXiv 2022)
- **DOI / arXiv / URL:** [arXiv:2212.02345](https://arxiv.org/abs/2212.02345); DOI [10.4230/LIPIcs.SoCG.2024.15](https://doi.org/10.4230/LIPIcs.SoCG.2024.15)
- **Local PDF:** `papers/bauer-2024-wrapping-cycles.pdf`
- **Main technique:** Persistence reduction ≡ algebraic discrete-Morse gradient flow. Lexicographically optimal homologous cycles in a Delaunay complex live on the Wrap complex.
- **What we should read:** The identification of reduction with gradient flow, and the Wrap support theorem.
- **Usable idea:** A reduced cycle basis can be forced onto a Morse/Wrap subcomplex. Suggests: compute Alpha/Delaunay, reduce onto Wrap, skip full Čech. Complementary to edge collapse (which is flag-specific).

**Definitions (from Ripser).** An **apparent pair** \((\sigma,\tau)\) has \(\sigma\) the youngest facet of \(\tau\) and \(\tau\) the oldest cofacet of \(\sigma\). It is already a persistence pair and a Morse gradient pair, coefficient-independent. An **emergent cofacet pair** is a persistence pair in which \(\tau\) is the earliest cofacet of \(\sigma\); zero-persistence emergent pairs can be detected before the full cofacet list is built.

---

## 14. Recent results that may beat or refine Ripser-style implicit cohomology

### 14.1 RedZeD: computing persistent homology by reduction to zero differentials

- **Authors:** Krzysztof (Chris) Kapulkin, Nathan Kershaw
- **Year:** 2026
- **DOI / arXiv / URL:** [arXiv:2606.06310](https://arxiv.org/abs/2606.06310); package [pypi.org/project/redzed-tda](https://pypi.org/project/redzed-tda/)
- **Local PDF:** `papers/kapulkin-2026-redzed.pdf`
- **Main technique:** Recasts pairing as reduction to zero differentials. **Active enumeration** avoids enumerating many VR birth columns. Borrows Ripser’s combinadic simplex IDs. Reports faster runtime than Ripser on 21/22 tests, especially \(H_1\) with topological signal, and lower peak memory in \(H_1\). Ripser still wins some high-degree, low-signal cases.
- **What we should read:** The RedZeD framework, the active-enumeration loop, and the benchmark table vs Ripser. Re-run those tests ourselves.
- **Usable idea:** This is the most direct 2022–2026 **competitor** to implicit cohomology. If active enumeration is correct, it is a structural reduction of work (fewer birth columns), not a hardware trick. Until we reproduce the suite, treat speedups as unverified. Add `redzed-tda` to the first benchmark round if it installs.

### 14.2 Fast computation of persistent homology representatives with involuted persistent homology

- **Authors:** Matija Čufar, Žiga Virk
- **Year:** 2023 (arXiv 2021)
- **DOI / arXiv / URL:** [arXiv:2105.03629](https://arxiv.org/abs/2105.03629); DOI [10.3934/fods.2023006](https://doi.org/10.3934/fods.2023006)
- **Local PDF:** `papers/cufar-2023-involuted-ph.pdf`
- **Main technique:** Reduce cohomology first; keep only death/essential columns; reduce that tiny homology submatrix to recover cycles. Runtime close to cohomology, far from naive homology, usually faster than Eirene for representatives.
- **What we should read:** The two-stage “involuted” procedure.
- **Usable idea:** Keep cohomology as the barcode engine. Add this only if the project needs representatives. Implemented in Ripserer.jl.

### 14.3 Other 2022–2026 pointers (not downloaded)

- Glisse–Pritam 2022 edge-collapse rewrite — already in §6.2.
- Distilled VR 2024 — already in §9.2; **do not trust the isomorphism yet**.
- Nigmetov–Morozov Cadmus 2024/26 — already in §12.3.
- Bauer–Roll wrapping cycles 2024 — already in §13.2.
- Image/cubical GPU (TopoGPU, [arXiv:2610.10959](https://arxiv.org/abs/2610.10959)) — relevant only if we later do grids, not point-cloud VR.

No 2022–2026 paper in this set gives a better **worst-case** complexity than matrix reduction. Gains are structural (fewer columns/simplices) or implementation (parallel/GPU).

---

## 15. Methodology only — integer multiplication

**Do not import the mathematics of integer multiplication into TDA.** These two items are here because INSTRUCTIONS.md asks us to reuse the *research process*, not the algorithm.

### 15.1 Integer multiplication below \(n\log n\)

- **Authors:** OpenAI
- **Year:** 2026-09-23
- **DOI / arXiv / URL:** OpenAI Math Release family #109, [github.com/openai/math/.../paper.pdf](https://github.com/openai/math/blob/main/preprints/Integer-multiplication-below-n-log-n-September-23-2026/paper.pdf)
- **Local PDF:** `papers/openai-2026-integer-multiplication.pdf`
- **Main technique:** Deterministic multitape Turing-machine algorithm claiming \(T(n)=O(n(\log n)^{1-\kappa})\) with \(\kappa=2^{-182}\), i.e. a strict power saving below Harvey–van der Hoeven \(O(n\log n)\). Constants are enormous; not a practical multiplier.
- **What we should read:** Only the *shape* of the claim: one fixed machine, worst-case, every input length, explicit model. Skim the construction; do not port FFT/tape tricks to PH.
- **Usable idea:** How a research programme states a bound (model, \(\kappa\), what is and is not claimed). Useful as a template for writing *our* complexity claims: implementation speed ≠ asymptotic improvement.

### 15.2 CrocSwap / integer-mult-bounds (repository)

- **Authors:** Douglas Colkitt and community; pinned OpenAI manuscript under `upstream/`
- **Year:** 2026 (living repo)
- **DOI / arXiv / URL:** [github.com/CrocSwap/integer-mult-bounds](https://github.com/CrocSwap/integer-mult-bounds)
- **Local PDF:** none (not a paper)
- **Main technique:** Community search over variations of a construction. Patches apply independently to a **frozen** upstream snapshot. Certificates, `make verify-*`, PR ledger, result history, and explicit labels: conditional witness vs formal theorem vs finite check. Failed and superseded patches are kept.
- **What we should read:** `README.md`, `PATCHING.md`, `docs/reproducibility.md`, `docs/research/result-history.md`, `docs/research/pr-ledger.md`. Ignore the actual \(\kappa\) values.
- **Usable idea for this project:**
  1. Pin a baseline (Ripser / Ripser++ commit) and never silently edit it.
  2. One hypothesis per change; patches/branches are alternatives, not a pile.
  3. Distinguish: implementation speedup / exact structural reduction / theorem.
  4. Keep negative results with a short certificate (dataset, command, output).
  5. Finite tests and diagrams do not replace a persistence-preserving proof.
  6. Automated search is allowed; a better constant is not a better algorithm.

---

## Coverage map

| Requested topic | Primary entries |
|---|---|
| Ripser and persistent cohomology | 1.1, 1.2 |
| Ripser++ GPU | 2.1 |
| giotto-ph parallelization | 3.1, 11.1 |
| GUDHI complexes | 4.1–4.3 |
| Alpha complexes | 5.1, 5.2, 13.2 |
| Edge collapse for VR | 6.1–6.3 |
| Sparse Rips and guarantees | 7.1 |
| Witness complexes | 8.1 |
| Discrete Morse / distilled VR | 9.1, 9.2, 5.2, 13.1–13.2 |
| Matrix reduction (standard, clearing, twist, cohomology) | 10.1–10.4, 1.2 |
| Oineus / parallel PH | 11.1, 3.1 |
| Distributed PH | 12.1–12.3 |
| Apparent / emergent pairs | 1.1, 13.1, 2.1 |
| Recent 2022–2026 vs Ripser-style cohomology | 14.1, 14.2, 9.2, 12.3, 6.2, 13.2 |
| OpenAI / CrocSwap methodology | 15.1, 15.2 |

---

## Working conclusions (bibliography only)

These are reading conclusions, not benchmark results.

1. **Exact VR on a CPU** still means: implicit cohomology + clearing + apparent/emergent pairs, optionally after edge collapse, optionally lock-free. giotto-ph is the integrated instance; Ripser is the sequential reference.
2. **Exact Euclidean low-d** should use Alpha (or Wrap), justified by Bauer–Edelsbrunner, not VR.
3. **Approximate VR** should use Sheehy sparse Rips and quote the multiplicative guarantee.
4. **Vertex reduction** (Witness / landmarks) is a different guarantee class from edge collapse.
5. **New work that might beat Ripser** is RedZeD (active enumeration) and, if repaired, distilled VR. Both need independent checks. Distilled VR is not safe to implement yet.
6. **Distribution:** never shard the point cloud and merge diagrams. Use DIPHA/Cadmus (column/range) or blowup (domain).
7. **Methodology to copy from CrocSwap:** pinned baseline, one lever per experiment, certificates, and a hard line between conjecture, measurement, and proof.

Next reading after the eight must-reads: edge-collapse implementation details (6.1–6.2) and RedZeD (14.1), then lock-free reduction (11.1) once a sequential prototype exists.
