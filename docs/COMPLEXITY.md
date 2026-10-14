# Complexity notes for PITH

Updated 2026-10-14 after iterations I001–I312 plus consolidation measurements.
This is a **complexity ledger**,
not a theorem paper and not a selected-algorithm rewrite. It restates what the
literature already proves, what follows from those statements by a short
derivation, and what the I204 / I218 / I227–I312 receipts only measure.

**Honest contribution.** PITH does **not** introduce a new worst-case Big-O for
exact Vietoris–Rips (VR) \(H_1\) on a connected threshold graph \(G_T\). The
living selected path (`docs/SELECTED.md`) is a **portfolio**: a residual-frac /
edge-frac dispatcher, two exact engines (backward flag collapse + Ripser-style
implicit cohomology; vendored RedZeD), Kruskal / Delaunay \(H_0\), sparse
metric representations, and an **optional** Euclidean Delaunay-flag scale path
that is **not** exact VR. Owned extras that do change a *representation* cost
on sparse flags — walk-locate Delaunay construction, CSR / leftover-adjacency
instead of an \(n\times n\) rbit matrix — are charged below as data-structure
derivations, not as a new persistence theorem.

Every complexity sentence is tagged **[citation]**, **[derivation]**, or
**[empirical]**. Empirical power laws such as “residual \(\sim n^{1.2}\)” are
**pre-asymptotic slopes on a named suite**. They are not theorems.

---

## 0. How to read a claim

### 0.1 Three bound classes

Every method below is split into the same three boxes. Do not promote a claim
from a weaker box into a stronger one.

| Class | Meaning | Allowed language |
| --- | --- | --- |
| **Proven worst case** | Holds for every finite input the method accepts, in a named model (comparisons, field arithmetic, or a standard RAM cost for the cited algorithm). | \(O(\cdot)\), \(\Theta(\cdot)\), \(\Omega(\cdot)\) with a citation or a short derivation from one. |
| **Regime-specific bound** | Holds only under an extra hypothesis (planar / Euclidean \(d\in\{2,3\}\), doubling dimension, sparse \(T\)-ball, disconnected \(G_T\), \(\lvert E\rvert\le 16n\), …). | Same symbols, plus the hypothesis in the same sentence. |
| **Empirical-typical** | Measured on the I044–I312 families (circle, blobs, sphere, torus, uniform2, figure8, …) at the recorded \(n,T\). | “measured”, “on this suite”, “slope”, “ratio vs Ripser”. Never “theorem”, never “therefore \(O(n^{1.2})\)”. |

### 0.2 Three evidence labels

| Label | Meaning |
| --- | --- |
| **[citation]** | A numbered statement in a paper listed in §16, or a classical textbook theorem named there. |
| **[derivation]** | A short consequence of a citation plus definitions already in this file (flag size, MST \(\subseteq\) Delaunay \(\Rightarrow\) Kruskal on \(\mathrm{Del}\cap\{d\le T\}\), word-AND vs intersection). Not a new theorem. |
| **[empirical]** | A receipt in `RESEARCH_LOG.md` / `docs/SELECTED.md`. Reproducible, not general. |

### 0.3 What is forbidden here

- Inventing a theorem, or naming an empirical slope as if it were one.
- Claiming a new worst-case Big-O versus Ripser VR on a **connected** \(G_T\).
  `docs/SELECTED.md` states that part is still a portfolio.
- Treating Delaunay-flag, Sheehy sparse Rips, or `--sparse-eps` as exact VR.
- Treating Alpha / Čech / offsets as VR (they are a different module;
  Bauer–Edelsbrunner 2017). I205 rejected Alpha as a VR stand-in.

---

## 1. Notation

| Symbol | Meaning |
| --- | --- |
| \(n\) | Number of vertices. |
| \(G_T=(V,E)\) | Threshold graph of the (diameter) VR filtration at finite \(T\): \(\{u,v\}\in E\) iff \(d(u,v)\le T\). |
| \(\lvert E\rvert\) | Edges of the **working** 1-skeleton (full \(G_T\), collapsed residual, Delaunay 1-skeleton, or thicken). |
| \(\Delta\) | Maximum degree in that 1-skeleton. \(\bar d=2\lvert E\rvert/n\) is the mean. |
| \(\lvert K_k\rvert\) | Number of \(k\)-simplices in the working flag complex. |
| \(\lvert R\rvert\) | Residual 1-skeleton after exact flag edge collapse: edges that survive (possibly delayed). Same as \(E'\) / \(n_c\) in I204 / Boissonnat–Pritam. |
| \(C\) | Columns that actually enter reduction (non-apparent, non-cleared, non-skipped births). Output-sensitive remainder. |
| \(s_{\mathrm{col}}\) | Maximum number of nonzero heap entries seen while reducing one residual column. |
| \(k\) | Homology degree under discussion. Collapse-paper \(k\) (max degree) is written \(\Delta\) here to avoid the clash. |
| \(\delta\) | Doubling dimension (Sheehy). |
| \(\lvert A\rvert\) | Number of **active** \(k\)-simplices in RedZeD (keys of \(R_k\)). |

**Flag size (definition + [derivation]).** The VR / flag \(k\)-skeleton of a
graph satisfies

\[
\lvert K_k\rvert \;\le\; \binom{n}{k+1}
\qquad\text{and}\qquad
\lvert K_k\rvert \;\le\; \sum_{v\in V}\binom{\deg(v)}{k}.
\]

The first is the complete-complex bound; the second is the clique bound on a
graph of those degrees. Neither is a persistence theorem.

**Diameter convention.** Ripser, GUDHI Rips, and PITH use edge length =
filtration value. Čech / Alpha use a radius (or squared radius). Do not
compare those numbers as if they were the same filtration
(`docs/COMPLEXES.md`).

---

## 2. Shared algebraic baseline (every exact engine)

These facts are inherited. PITH does not improve them.

### 2.1 Standard reduction

**Proven worst case**

- Over a field, the persistence barcode of a simplexwise filtration is the
  pivot pairing of a reduced (co)boundary matrix \(R=DV\)
  (Edelsbrunner–Letscher–Zomorodian 2002; Zomorodian–Carlsson 2005)
  **[citation]**.
- Classical left-to-right column reduction is cubic in the number of cells:
  \(O(\lvert K\rvert^3)\) field operations in the worst case
  (Chen–Kerber 2011, citing the standard analysis; Bauer 2021 §3.1)
  **[citation]**.
- Fast-matrix-multiplication algorithms achieve \(O(\lvert K\rvert^\omega)\)
  with \(\omega<2.373\), and are not the practical engine
  **[citation]** (survey remark; not used here).
- Sparsity of \(D\) does **not** give a sub-cubic worst-case bound for
  Gaussian-elimination-style reduction: fill-in can densify the matrix
  **[citation]** (standard; restated in later output-sensitive analyses).

**Regime-specific bound**

- Chen–Kerber (2011) give an **output-sensitive** twist analysis: reducing a
  death column of index persistence \(j-i\) costs \(O((k+1)(j-i)^2)\) in their
  model, while an uncleared birth at index \(i\) costs \(O((k+1)i^2)\)
  **[citation]**. This is still cubic in the worst case (\(j-i=\Theta(\lvert K\rvert)\)).
- An implicit heap column of length \(s_{\mathrm{col}}\) with \(C\) residual
  additions is \(O(C\,s_{\mathrm{col}}\log s_{\mathrm{col}})\) heap operations
  **[derivation]** from Bauer’s heap representation (2021 §3.4). Worst case
  \(C,s_{\mathrm{col}}=\Theta(\lvert K_k\rvert)\).

**Empirical-typical**

- On typical point-cloud VR, most pairs have small index persistence and a
  large fraction of columns never enter the heap (apparent / clearing)
  **[empirical]** (Bauer 2021 §5; Ripser++ Table 1; I204 suite). This is not a
  rate theorem for general metrics.

### 2.2 Duality and clearing (why cohomology)

**Proven worst case**

- Absolute persistent homology and relative persistent cohomology have the
  same barcode (de Silva–Morozov–Vejdemo-Johansson 2011)
  **[citation]**.
- Clearing / twist (Chen–Kerber 2011): a birth index that appears as a pivot
  need not be reduced, because \(D^2=0\) already implies that column is a
  cycle **[citation]**. Clearing **skips columns**; it does not change the
  worst-case cubic class.

**Regime-specific bound**

- Bauer’s counting argument (2021 §3.2–3.3) **[citation]**: a VR \(d\)-skeleton
  has \(\binom{n}{d+1}\) simplices. The coboundary matrix in dimension \(d\)
  has far fewer *columns* than the homology boundary matrix in the same
  dimension has *rows that must later be cleared*. Cohomology + clearing
  together avoid reducing a combinatorial majority of columns on VR at low
  degree. **Either optimization alone does not.** This is a counting argument
  for the complete (or dense) VR skeleton, not a better Big-O than
  \(O(n^{3(k+1)})\) in the worst case.

**Empirical-typical**

- de Silva et al. and Bauer et al. (2017) observe cohomology faster than
  homology on VR **[empirical / citation]**. PITH and Ripser both take this
  as the default barcode engine.

### 2.3 Apparent and emergent pairs

**Proven worst case**

- An **apparent pair** \((\sigma,\tau)\) (youngest facet / oldest cofacet) is a
  persistence pair of the simplexwise filtration and a discrete Morse pair,
  field-independent (Bauer 2021) **[citation]**. Skipping those columns is
  exact. There is **no** proven worst-case apparent-pair *rate* better than
  “all or nothing.”
- An **emergent** same-diameter unpaired cofacet lets the cofacet enumerator
  abort early (Bauer 2021) **[citation]**. Exact if cofacets are generated in
  the legal order.

**Regime-specific bound**

- On finite \(\delta\)-hyperbolic \(\nu\)-geodesic spaces, a compatible
  apparent-pair gradient collapses \(\mathrm{Rips}_u\to\mathrm{Rips}_t\) in a
  scale window (Bauer–Roll 2022) **[citation]**. Tree metrics look easy.
  This is a geometric regime, not a VR-complexity theorem.

**Empirical-typical**

- Apparent pairs are often 90–99.9% of VR columns on typical clouds
  **[empirical]** (Ripser++ ; Oineus comments; I293 thicken 99% apparent).
  High-loop / high-d noise is the counter-regime (Bauer–Roll; torus I204).

---

## 3. Ripser implicit cohomology VR

Parent: Bauer, *Ripser*, *J. Appl. Comput. Topol.* 2021; arXiv:1908.02518.
Pinned SHA `01add51`. PITH `--engine implicit` is this algorithm on a
(possibly collapsed) flag 1-skeleton.

### Proven worst case

- The full VR \(k\)-skeleton has \(\lvert K_k\rvert=\Theta(n^{k+1})\)
  simplices **[citation]** (definition; Bauer 2021).
- Implicit representation **does not store** \(K\) or \(D\). Cofacets and
  diameters are recomputed from the distance matrix and the combinadic index
  **[citation]** (Bauer 2021 §3.4). Memory is the dense lower triangle
  \(O(n^2)\) (or a sparse neighbor list \(O(\lvert E\rvert)\)) plus \(V\) for
  death / residual columns plus a pivot map. Implicitization is a **memory /
  traffic** change, not a smaller algebraic rank **[derivation]**.
- Time is still governed by (i) enumerating cofacets of columns that are
  assembled and (ii) reducing those columns. In the worst case every
  \(k\)-simplex is assembled and residual reduction is cubic in
  \(\lvert K_k\rvert\) **[derivation]** from §2.1 + implicit recomputation
  (each addition re-enumerates a coboundary).
- Dense cofacet insertion from a \(k\)-simplex tries \(\Theta(n)\) vertices
  **[derivation]**. Sparse input restricts that to neighbors
  (\(O(\Delta)\)).
- \(H_0\) is union-find, not matrix reduction **[citation]** (Bauer 2021).
- **No** published Ripser bound is a better worst-case class than “implicit
  reduction of the VR \(k\)-skeleton.” Bauer does not claim one
  **[citation]**.

### Regime-specific bound

- Finite threshold \(T\) (or enclosing radius): only simplices of diameter
  \(\le T\) exist. Then \(\lvert K_k\rvert\le\sum_v\binom{\deg_{G_T}(v)}{k}\)
  and cofacet probes are \(O(\Delta)\) **[derivation]**. Worst-case \(G_T\)
  is still complete, \(\lvert E\rvert=\Theta(n^2)\).
- Output-sensitive form, residual cohomology:

  \[
  T_{\mathrm{Ripser}}
  \;=\;
  O\!\bigl(n^2 + \lvert K_k\rvert\cdot\mathrm{probe}
  + C\cdot s_{\mathrm{col}}\log s_{\mathrm{col}}\bigr)
  \]

  with \(\mathrm{probe}=O(n)\) dense or \(O(\Delta)\) sparse
  **[derivation]** from Bauer’s loops. This is *not* \(o(n^{3(k+1)})\) in the
  worst case.
- Clearing + cohomology: remaining assembled columns in degree \(k\) are
  essentially the death columns plus essential births (Bauer counting)
  **[citation]**. \(C\le\lvert K_k\rvert\) always; \(C\ll\lvert K_k\rvert\)
  is regime, not worst case.

### Empirical-typical

- I204, \(n=500\ldots2000\), fixed \(T\): Ripser wall-clock slopes
  \(\sim n^{2.14}\) (uniform2) to \(\sim n^{3.25}\) (circle) to
  \(\sim n^{2.95}\) (torus) **[empirical]**. Circle’s steep slope is tet /
  triangle work on a dense noisy loop, not a theorem.
- Apparent-pair abort + implicit \(V\) is why Ripser beats explicit simplex
  trees on VR (GUDHI CAM / I237: blobs \(n=1000\) 15.9 s / 17.8M simplices
  vs auto 21 ms) **[empirical]**.

---

## 4. Flag edge collapse (Boissonnat–Pritam)

Parent: Boissonnat–Pritam, SoCG 2020 (LIPIcs.SoCG.2020.19);
Glisse–Pritam 2022, arXiv:2203.07022 (backward rewrite). PITH
`--collapse-alg back` is the 2022 backward scan (GUDHI sticky-dominator
lineage; I182–I202 implementation levers).

### Proven worst case

- A dominated edge (link is a cone; equivalently
  \(N[a]\cap N[b]\subseteq N[v']\)) may be removed; the residual is still
  flag; the collapsed flag **filtration** has the same persistence module
  in every degree (Boissonnat–Pritam 2020, Lemma 2 + Theorem 4)
  **[citation]**. Exact VR.
- Collapse uses **only the 1-skeleton**. Higher faces are never built
  **[citation]**.
- Forward Algorithm 1 (2020): \(O(\lvert E\rvert\,\lvert R\rvert\,\Delta^2)\)
  **[citation]** (paper; \(n_e,n_c,k\) in their notation).
- Backward Algorithm 1 (Glisse–Pritam 2022): \(O(\lvert E\rvert\,\Delta^3)\)
  **[citation]**. One domination test is \(O(\Delta)\) to build \(N[e]\) and
  \(O(\Delta^2)\) to try apices **[citation]** (`docs/EDGE_COLLAPSE_SPEC.md`
  §4.2).
- After collapse, any exact VR engine on the residual flag graph is still
  in the Ripser class of §3 with \(\lvert E\rvert\) replaced by
  \(\lvert R\rvert\) **[derivation]**. If \(\lvert R\rvert=\Theta(\lvert E\rvert)\),
  collapse does **not** change the worst-case \(H_1\) class.
- One pass is exact for PH, not 1-core-minimal; extra iterations stay exact
  **[citation]** (2022 “Optimality”; GUDHI `nb_iterations`).

### Regime-specific bound

- The 2022 \(O(\lvert E\rvert\Delta^3)\) bound is pessimistic: a trimmed
  edge cheapens later tests; a never-shifted critical edge is \(O(\Delta^2)\)
  **[citation]** (Glisse–Pritam 2022).
- Geometric samples with a locally cone-like link: \(\lvert R\rvert\ll\lvert E\rvert\)
  is possible. High-d noise / fat torus: \(\lvert R\rvert\sim\lvert E\rvert\)
  **[citation]** (paper discussion) + **[empirical]** (I204 torus).
- Collapse then **implicit** residual PH (giotto-ph / PITH): residual
  \(\lvert K_k\rvert\le\sum\binom{\deg_R(v)}{k}\), not an expanded simplex
  tree **[derivation]** (hypothesis H02; selected). Expanding the residual
  (GUDHI `expansion`) reintroduces \(O(\lvert R\rvert^{k+1})\) storage and
  is the I237 loser.

### Empirical-typical

- SoCG 2020 Table 1: \(\sim 12\)–\(31\times\) fewer edges on their graphs
  (torus 428K\(\to\)14K) **[empirical / citation]**.
- I204 residual slopes at \(n=500\ldots2000\), **not theorems**:

  | Family | \(\lvert E\rvert\sim n^{}\) | \(\lvert R\rvert\sim n^{}\) | \(\lvert R\rvert/\lvert E\rvert\) at \(n=2000\) |
  | --- | ---: | ---: | ---: |
  | circle | 2.00 | **1.22** | 0.48% |
  | blobs | 2.00 | **1.10** | 0.94% |
  | sphere | 2.00 | **0.91** | 0.68% |
  | uniform2 | 1.99 | **1.04** | 1.08% |
  | torus | 2.01 | **2.08** | **34%** |

  **[empirical]** (I204). Collapse-friendly residuals look near-linear;
  input \(G_T\) is still \(\Theta(n^2)\) and the backward scan **visits
  essentially every edge** (I164: live edges drop 1:1 with the scan)
  **[empirical]**. Torus residual is \(\Theta(n^2)\) on this suite —
  **no general Big-O win**.
- PITH backward collapse is **faster** than GUDHI 3.13
  `flag_complex_collapse_edges` on the same \(n=2000\) graphs (circle
  273 ms vs 7.94 s; torus 1.40 s vs 4.05 s) with matching
  \(\lvert R\rvert\) (5169 / 163426) **[empirical]** (I227). The torus
  collapse wall is algorithmic, not an implementation gap vs GUDHI.

---

## 5. Ripser implicit cohomology on a collapsed residual

This is the selected **thin-residual** exact path (`--engine implicit` /
auto-collapse). It is §3 after §4, not a third algorithm.

### Proven worst case

- Exact VR\(\le T\) **[citation]** (Boissonnat–Pritam + Bauer).
- Worst-case time is collapse \(O(\lvert E\rvert\Delta^3)\) plus Ripser on
  \(\lvert R\rvert\) edges **[derivation]**. On a connected dense \(G_T\)
  one may have \(\lvert E\rvert=\Theta(n^2)\), \(\Delta=\Theta(n)\),
  \(\lvert R\rvert=\Theta(n^2)\). Then the class is **not** better than
  Ripser VR **[derivation]**. This is the SELECTED sentence: *worst-case
  \(H_1\) Big-O is not improved on a connected \(G_T\)*.

### Regime-specific bound

- If a regime has \(\lvert R\rvert=O(n)\) and bounded residual degree, residual
  reduce is cheap and the wall is the \(\Theta(\lvert E\rvert)\) collapse
  walk **[derivation]** from I164 + flag size. That is still
  \(\Omega(n^2)\) on a dense \(G_T\) because collapse must see \(E\).
- Output-sensitive:

  \[
  T_{\mathrm{collapse+implicit}}
  \;=\;
  O\!\bigl(\lvert E\rvert\,\Delta^3 + n^2_{\mathrm{metric}}
  + C(\lvert R\rvert)\,s_{\mathrm{col}}\log s_{\mathrm{col}}\bigr).
  \]

  **[derivation]**. The first term is the 2022 collapse bound; the last is
  Ripser on the residual.

### Empirical-typical

- I204 PITH time \(\sim n^{2.14}\)–\(n^{2.22}\) on collapse-friendly families
  vs Ripser \(\sim n^{2.14}\)–\(n^{3.25}\); torus \(\sim n^{2.97}\) vs
  Ripser \(\sim n^{2.95}\) **[empirical]**. Circle 10×–140× is the
  **exponent gap vs Ripser on that family**, not a better worst-case class.
- Circle \(n=4000\) \(T=1.5\): **140×** (I196); \(n=2000\): **84.4×** (I202)
  **[empirical]**. Blobs / sphere / torus at \(n=2000\) were \(\sim 1.5\)–\(2\times\)
  on collapse+implicit before RedZeD dispatch **[empirical]** (I202/I203).
- swiss \(n=400\) is **0.91×** — collapse can lose on thin graphs
  **[empirical]** (SELECTED).

---

## 6. RedZeD (Kapulkin–Kershaw)

Parent: Kapulkin–Kershaw, *RedZeD: computing persistent homology by
reduction to zero differentials*, arXiv:2606.06310. Vendored
`third_party/redzed/redzed.cpp` (`22ef1bf`, MIT). PITH
`persist_redzed` / `--engine redzed` (I228) plus from-points wrap
(I238–I263, I270–I275).

### Proven worst case

- Theorem 2.1: a filtration of chain complexes over a field may be replaced
  by a sequence of quasi-isomorphic complexes with **zero differentials**;
  the barcode is that of the original filtration **[citation]**.
- Theorem 2.6: NaiveRedZeD computes the persistence pairs of an elementwise
  filtration **[citation]**.
- RedZeD implements compression + exhaustive + retrospective reduction in
  annotation dictionaries \(R_p\) **[citation]** (§2). On its own the paper
  says this “does not offer significant improvements” and is “in general
  significantly slower” than existing methods **[citation]**.
- **Active enumeration** (RedZeD VR, §3): after a birth \(k\)-simplex
  \(\sigma\), only \((k+1)\)-simplices that have at least one **active**
  face and \(\sigma\) as youngest face are enumerated. A simplex is active
  at time \(i\) iff \(r_i(\sigma)\ne 0\) (keys of \(R_k\))
  **[citation]** (Definition 3.1).
- Proposition 3.2: a death \(k\)-simplex is not the youngest face of any
  \((k+1)\)-simplex (else it would form a Bauer apparent pair)
  **[citation]**.
- Completeness: \((k+1)\)-simplices with only inactive faces have
  \(r\partial\tau=0\), hence are \((k+1)\)-births and may be skipped when
  computing degree-\(k\) PH **[citation]** (§3).
- The paper **does not** state a worst-case Big-O better than standard
  pairing / Ripser VR **[citation]**. Active enumeration is a structural
  skip of many birth columns, still output-sensitive in \(\lvert A\rvert\)
  and in leftover cofaces. Worst-case \(\lvert A\rvert\) and leftover visits
  can be \(\Theta(\lvert E\rvert)\) on a connected dense \(G_T\).
- PITH I232/I234 owned AE without the vendor dictionaries is
  \(\Theta(\lvert E\rvert\cdot\Delta)\) triangle visits — the persist_sparse
  class — and loses to Ripser **[empirical]** (I231–I234). That is evidence
  that “youngest-face filter alone” is **not** a better Big-O
  **[derivation]**.

### Regime-specific bound

- Output-sensitive sketch (not a paper theorem):

  \[
  T_{\mathrm{RedZeD}}
  \;=\;
  O\!\bigl(n^2_{\mathrm{metric}}
  + \lvert E\rvert\cdot T_{\mathrm{leftover}}
  + \lvert A\rvert\cdot T_{\mathrm{AE}}
  + T_{\mathrm{annot}}\bigr).
  \]

  Leftover-coface / `has_leftover_coface` is a neighborhood AND
  (\(O(n/64)\) words on the vendor rbit matrix, or \(O(\Delta)\) on the
  I302 leftover-adj path when \(\lvert E\rvert\le 16n\)). AE Step 1 loops
  keys of \(R_k\) **[derivation]** from arXiv:2606.06310 §3 + PITH wrap.
- Finite \(T\): skip vendor enclosing radius (I244); exact for VR\(\le T\)
  **[derivation]** (Henselman / Bauer enclosing is for the untruncated
  complex).
- Disconnected \(G_T\): VR of a disjoint union is the direct sum of the
  blocks **[derivation]** (standard). I239/I240 run RedZeD per component.
  If RedZeD is superadditive of order \(\alpha>1\), \(k\) equal blocks of
  size \(n/k\) cost \(\sim k\cdot(n/k)^\alpha\) **[derivation]** (I239).
  **Connected \(G_T\) is unchanged** — not a better worst-case class.
- Sparse \(T\)-ball (I256–I261, I263): metric memory \(O(\lvert E\rvert)\)
  vs \(O(n^2)\) when the spatial / edge-frac gate fires **[derivation]**.
  Worst-case connected \(G_T\) remains \(\Theta(n^2)\).

### Empirical-typical

- Paper: faster than Ripser on 21/22 tests; Ripser wins some high-degree,
  low-signal cases; peak memory usually lower in \(H_1\) **[empirical /
  citation]** (arXiv:2606.06310 Table 1). Treat as the authors’ suite, not
  ours.
- I227/I228 vs Ripser, same clouds, in-tree wrap:

  | Family | \(n\) | \(T\) | vs Ripser | vs collapse+implicit |
  | --- | ---: | ---: | ---: | ---: |
  | circle_noisy | 2000 | 1.5 | 33.4× | 0.45× (collapse still faster) |
  | torus | 2000 | 1.6 | 11.7–12.3× | 7.5–8.3× |
  | sphere | 2000 | 1.4 | 6.9× | 3.6× |
  | blobs | 2000 | 1.0 | 4.9× | 3.0× |
  | uniform2 | 2000 | 0.35 | 4.5× | 2.4× |

  **[empirical]**. Time slopes I227: RedZeD \(n^{2.03}\)–\(n^{2.38}\) vs
  Ripser \(n^{2.04}\)–\(n^{3.03}\) vs PITH default \(n^{1.72}\)–\(n^{2.67}\).
- I229: blobs / uniform2 / sphere at \(n=4000\) stay \(\sim 5\)–\(8\times\);
  high-\(n\) exponents match Ripser (\(\sim n^{2.3}\)) — **constant-factor,
  not an exponent gap** **[empirical]**. Torus \(n=3000\) **14.2×**.
- I263 mixed figure8 \(n=4000\) \(T=1.1\): **27.1× / 1.07 s**, 1.98M vs 8.0M
  pairs **[empirical]**. Spatial leftover wall: 866 ms / 1.98M leftover
  **visits** (I263). Inner-loop leftover-coface skips (I253–I255, I265) did
  not cut that visit term **[empirical]**.
- I235+I263 auto: torus residual-frac \(0.28\) → RedZeD **13.0×**
  (I-wave); live 1-thread leftover re-measure is **12.6×**
  (`leftover_10x.json`). Circle frac \(0.021\) → collapse **28×** at
  \(n=1000\) **[empirical]**. Dispatch is \(O(s^2)\) with \(s=250\), not
  a function of \(n\) **[derivation]**. **Not** a better Big-O.

---

## 7. Kruskal \(H_0\)

VR \(H_0\) is the connected components of \(G_t\) as \(t\) grows. Ripser
already uses union-find in dimension 0 (Bauer 2021) **[citation]**. PITH
`maxdim=0` never starts RedZeD (I241).

### Proven worst case

- Kruskal on edges sorted by length, union-find with path compression +
  union-by-rank: \(O(\lvert E\rvert\log\lvert E\rvert)\) to sort plus
  \(O(\lvert E\rvert\,\alpha(n))\) merges (Tarjan) **[citation]** (classical).
- This is **exactly** \(H_0\) of VR\(\le T\) (and of the full VR filtration
  if all pairs are listed) **[derivation]** from the definition of VR
  \(H_0\).
- Listing \(E(G_T)\) is \(O(n^2)\) pairwise or \(O(\lvert E\rvert)\) after a
  spatial filter. On a connected dense instance the listing dominates and
  the class is \(\Theta(n^2)\) **[derivation]**. Ripser \(H_0\) is in the
  same class.

### Regime-specific bound

- Spatial \(T\)-cells (I240/I241): only pairs with \(\lvert\Delta\mathrm{cell}\rvert\le 1\)
  can have \(d\le T\) (Moore neighborhood). Listing is
  \(O(n+\lvert E\rvert)\) in that Euclidean grid model **[derivation]**.
  Still \(\Theta(n^2)\) if the \(T\)-ball is the whole domain.
- Euclidean \(d\in\{2,3\}\): do **not** list \(G_T\); see §8.

### Empirical-typical

- I241 vs Ripser dim 0: only \(\sim 1.9\times\) (blobs \(n=8000\) 1.27 s /
  2.46 s) **[empirical]**. Ripser \(H_0\) is already union-find; the cost is
  emitting \(\lvert E(G_T)\rvert\).
- T-capped 1-component fill was **reverted** (uniform2 metric 7→80 ms)
  **[empirical]** (I241).

---

## 8. 2D / 3D Delaunay for \(H_0\) (MST \(\subseteq\) Delaunay)

Euclidean only. Gates: I271 walk-locate 2D for `maxdim=0`, \(n\in[256,10^5]\);
I275 walk-locate 3D for `maxdim=0`, \(n\in[256,5\cdot10^4]\) (I306 later
raised the 3D cap to \(10^5\) on the Delaunay-flag path). I274 3D scan is
fallback only (\(n\le 8000\)).

### Proven worst case

- The Euclidean MST is a subgraph of the Delaunay triangulation (empty-circle
  / empty-sphere property: any MST edge is a Delaunay edge). Classical:
  Shamos–Hoey 1975; Preparata–Shamos **[citation]**.
- Therefore the MST of \(G_T\) equals the MST of
  \(\mathrm{Del}(X)\cap\{e:d(e)\le T\}\) **[derivation]**. Kruskal on those
  edges is exact \(H_0\) of VR\(\le T\) in Euclidean space. Topology loss:
  **0** on this path (I270–I275, I284–I285) **[empirical]** for identity;
  exactness is the derivation above, not a new theorem.
- **2D size.** A planar triangulation has \(\lvert E_{\mathrm{Del}}\rvert\le 3n-6\)
  (\(n\ge 3\)) **[citation]** (Euler). So \(\lvert E\rvert=\Theta(n)\) in 2D.
- **2D construction.** Fortune sweep / reduced incremental constructions
  compute \(\mathrm{Del}_2\) in \(O(n\log n)\) worst-case time and \(O(n)\)
  space **[citation]** (Fortune 1987; standard CG). PITH’s Lawson
  walk-locate + cavity flood is the *incremental* algorithm; its
  **worst-case** walk can be quadratic on hostile insertion orders
  **[citation]** (standard incremental-Delaunay caveat). We do **not**
  claim the owned walk is \(O(n\log n)\) worst case.
- **3D size.** \(\lvert\mathrm{Del}_3\rvert=\Theta(n^2)\) in the worst case
  (moment curve / neighborly polytopes) **[citation]** (Seidel; the
  \(\Theta(n^{\lceil d/2\rceil})\) Delaunay bound). Construction is
  \(O(n^2)\) in that case.
- I274 all-pairs / scan Bowyer–Watson is \(O(n^2)\) incircle tests
  **[derivation]**.

### Regime-specific bound

- Randomized incremental construction with good location, or points in
  random order with a walk that stays local, has **expected**
  \(O(n\log n)\) time in 2D (Guibas–Knuth–Sharir 1992)
  **[citation]**. I271/I275 use Morton insertion + walk-locate and justify
  “expected \(O(n\log n)\)” in that standard sense **[derivation / citation]**.
  This is **not** a new theorem and **not** a worst-case claim for the
  owned walk.
- Well-distributed samples in 3D typically have \(\lvert E_{\mathrm{Del}}\rvert=\Theta(n)\)
  (constant mean degree \(\sim 6\)–\(15\)) **[citation]** (standard CG /
  COMPLEXES.md). Then Kruskal on Delaunay is \(O(n\log n)\) after
  construction, versus \(\Theta(\lvert E_T\rvert)\) listing of a fat
  \(G_T\) **[derivation]**.
- Hostile 3D configurations remain \(\Theta(n^2)\) edges. The owned walk
  does not beat that.

### Empirical-typical

- I271 2D blobs: \(n=4000\) **54.8× / 4.1 ms / 12k edges** (I270 scan was
  176 ms); \(n=8000\) **137× / 7.6 ms**; \(n=12000\) **218× / 0.027 s /
  36k**; I284 \(n=25000\) **515× / 55 ms**; \(n=50000\) **113 ms / 150k**
  **[empirical]**. Construction 4.1 / 7.6 / 12.4 ms at 4k/8k/12k looks
  linear on this family — **empirical**, not \(O(n)\).
- I275 3D sphere: \(n=4000\) **29× / 22 ms / 20k** (I274 scan 578 ms);
  \(n=8000\) **65× / 56 ms / 40k**; \(n=16000\) **147× / 0.112 s / 81k**;
  I285 \(n=30000\) **288× / 0.221 s / 151k** vs Ripser 63.6 s;
  \(n=50000\) **367 ms / 252k** **[empirical]**.
- I310 replacing the 4×4 `insphere` det by \(\lVert p-c\rVert^2<r^2\) is
  **not exact** (sphere \(n=16000\) \(\lvert E\rvert\) 80659 vs 80641;
  \(n=50000\) ess \(H_2\) 2 vs 1) **[empirical]**. Do not treat a
  circumcenter filter as the Delaunay predicate.
- I307–I312 cheap walk/locate bookkeeping did not cut the 80k metric wall
  **[empirical]**. Identity held on I311/I312; I310 did not.
- **\(H_1\) leftover visits remain \(\Theta(\lvert E\rvert)\)** on the exact
  VR path (I271/I275 decisions). Delaunay \(H_0\) does not shrink exact
  \(H_1\). I272 Gabriel leftover skip invented bars **[empirical]**.

---

## 9. Delaunay-flag Euclidean scale path (not exact VR)

CLI: `--delaunay-vr` (I276). Recommended thicken:
`--delaunay-alpha auto` (I282, I305 cap 2.25). 3D `maxdim≥2`: I300
\(\alpha=1\) RedZeD, **no** H1 thicken. Fat 2D thicken persist: I297
RedZeD-on-edges. H2 is never thickened (I277+).

This is the flag complex of a Euclidean 1-skeleton (Delaunay edges, or
Delaunay plus local-radius extras). It is a **different filtration** from
VR. Compare with bottleneck / unmatched counts, never with barcode
equality, unless an oracle row happens to match.

### Proven worst case

- The 1-skeleton size is the Delaunay size of §8: \(\Theta(n)\) in 2D,
  \(O(n^2)\) in 3D **[citation]**.
- The flag \(k\)-skeleton of that graph has
  \(\lvert K_k\rvert\le\sum\binom{\deg_{\mathrm{Del}}(v)}{k}\)
  **[derivation]**. In 2D, \(\Delta\) is not \(O(1)\) in the worst case
  (one vertex can have degree \(\Theta(n)\)), so flag triangles are
  \(O(n^2)\) worst case even though \(\lvert E\rvert=O(n)\)
  **[derivation]**.
- Persist on that flag is Ripser-implicit or RedZeD of §3 / §6 with this
  \(\lvert E\rvert\) **[derivation]**. Same pairing theorems; **different
  complex**.
- **There is no theorem** that
  \(\mathrm{PH}(\mathrm{Flag}(\mathrm{Del}(X)))\cong\mathrm{PH}(\mathrm{VR}(X))\).
  I205 Alpha (circumradius / offset module) dropped essential \(H_1\) on
  mixed families **[empirical]**. I276 is not Alpha and is not a VR
  identity. I279–I305 \(\alpha\) values are **measured constants**, not a
  reconstruction theorem.

### Regime-specific bound

- Typical well-distributed 2D/3D samples: \(\bar d=O(1)\), so
  \(\lvert K_k\rvert=O(n)\) for fixed \(k\) **[derivation]** from bounded
  degree + flag size. Then persist is output-sensitive in \(C=O(n)\)
  residual columns on that flag.
- Thicken (I277–I286): extras \(\{u,v\}\) with
  \(d(u,v)\le\min(T,\alpha\cdot r_v)\) (and the symmetric end). Edge count
  is \(O(n\cdot \mathrm{vol}(B(\alpha r)))\) in a packing regime, not a
  proven linear bound for arbitrary Euclidean clouds **[derivation /
  caveat]**. I305 caps \(\alpha\le 2.25\); I291/I297 treat
  \(\lvert E\rvert\ge 8n\) as “fat” and send persist to RedZeD.
- I286 split: \(H_1\) on the thicken, \(H_2\) on the \(\alpha=1\) flag.
  Do not thicken \(H_2\) (I277 timeout / tax) **[empirical]**.
- I300: 3D `maxdim≥2` stays \(\alpha=1\) because thicken \(H_1\) was noise
  loops, not the void **[empirical]**. Finite 3D \(H_1\) on that path is
  I276-flag.

### Empirical-typical

- I276 \(\alpha=1\) flag, essential homology **8/8** (figure8 2=2; circle
  1=1; torus 1=1; sphere void 1=1; two_spheres 2=2). Finite unmatched
  **3–209** (figure8 \(n=2000\) **209**). figure8 \(n=2000\)
  **419× / 6 ms / 5.9k edges**; \(n=8000\) **24 ms / 24k / ess1=2**
  **[empirical]**.
- I279 \(\alpha=2.25\): exact \(H_1\) on 9/9 measured oracles; figure8
  \(n=4000\) **156× / 152 ms / 194k**; \(n=8000\) **67× / 390 ms / 428k**
  **[empirical]**. \(\alpha\) **grew with \(n\)** on the way here (1.5 →
  2.25). That treadmill is why it is not the exact default.
- I282/I305 auto: \(\alpha(n)=\min(2.25,\,1.75+0.125\log_2\max(n/400,1))\).
  figure8 \(n=16000\) **0.54 s / 878k / ess1=2**; \(n=24000\) **0.82 s**
  **[empirical]**. Extra thicken past 2.25 added edges, not essential
  \(H_1\) (I305).
- I300 3D \(\alpha=1\) RedZeD: sphere \(n=16000\) **0.27 s / 80k / ess2=1**
  (I297 thicken was 3.02 s); I302 \(n=30000\) **0.39 s**; I306
  \(n=50000\) **0.65 s / 252k**; \(n=80000\) **1.09 s / 404k / ess2=1**;
  I311 \(n=10^5\) **\(\sim 1.6\) s / 505k / ess2=1** **[empirical]**.
- I301/I302 on this \(\Theta(n)\) flag: CSR H2 stream + leftover-adj beat
  vendor rbits (sphere \(n=50000\) 0.84 s → 0.68 s) **[empirical]**. See
  §12.
- I291 thicken-collapse: exact-on-flag, **slower** at \(n\ge 4000\)
  **[empirical]**. Do not collapse the optional thicken.

---

## 10. Sheehy sparse Rips (approximation)

Parent: Sheehy, *Linear-size approximations to the Vietoris–Rips
filtration*, SoCG 2012 / *Discrete Comput. Geom.* 2013; arXiv:1203.6786.
GUDHI ships the Cavanna–Jahanseir–Sheehy geometric variant (CCCG 2015).
PITH `--sparse-eps` is an **owned greedy-net flag graph** (I210/I213),
motivated by that size class, not a re-proof of Sheehy’s net-tree.

### Proven worst case

- Sheehy: a (zigzag or equivalent non-zigzag) sparse filtration of size
  \(O(n)\) built in \(O(n\log n)\) time, with constants
  \((1/\varepsilon)^{O(k\delta)}\) for the \(k\)-skeleton in doubling
  dimension \(\delta\) **[citation]** (Sheehy 2013).
- Persistence diagram is a **multiplicative** approximation of VR. Sheehy:
  factor \(c=1/(1-2\varepsilon)\). GUDHI’s CJS variant is documented as a
  \((1,\,1/(1-\varepsilon))\)-interleaving; guarantees need
  \(\varepsilon<1\) **[citation]** (Sheehy; GUDHI sparse-Rips manual).
- **Not exact VR.** Short bars are the first to move. Never claim barcode
  equality with Ripser **[citation]**.
- Without a doubling bound the “linear” size is linear with a huge
  constant; high-\(\delta\) metrics are the hostile regime **[citation]**.
- Owned `--sparse-eps` does **not** inherit Sheehy’s theorem automatically.
  It is a greedy-net 1-skeleton + implicit PH, `cap = max(λ)` (I210/I213).
  `--sparse-cap min` invented extra essential \(H_1\) (I212)
  **[empirical]**. Treat owned sparse as **empirical approximation** unless
  a net-tree proof is written.

### Regime-specific bound

- Fixed \(\varepsilon\), fixed homology degree, bounded \(\delta\):
  \(\lvert E\rvert=O(n)\) and \(\lvert K_k\rvert=O(n)\) **[citation]**
  (Sheehy; CJS). Persist then sits in the Ripser / RedZeD class of an
  \(O(n)\)-edge flag **[derivation]**.
- Euclidean \(\mathbb{R}^d\) has \(\delta=\Theta(d)\) **[citation]**.
  Constants explode in high \(d\); SimBa exists because Sparse Rips stayed
  huge there (COMPLEXES.md).

### Empirical-typical

- I218 `--sparse-eps 0.6`, \(n=500\ldots2000\), **pre-asymptotic slopes,
  not theorems**:

  | Family | edges \(n^{}\) | PITH time \(n^{}\) | Ripser time \(n^{}\) | bn max | ess \(H_1\) |
  | --- | ---: | ---: | ---: | ---: | ---: |
  | circle | **1.39** | 1.52 | 3.29 | 0.012 | 2=2 |
  | blobs | **1.38** | 1.38 | 2.21 | 0.024 | 3=3 |
  | sphere | **1.31** | 1.38 | 2.17 | 0.034 | 1=1 |
  | torus | **1.38** | 1.60 | 2.92 | 0.055 | 2=2 |
  | uniform2 | **1.37** | 1.40 | 2.14 | 0.014 | 1=1 |

  **[empirical]**. The torus edge exponent is subquadratic here; exact
  collapse was \(n^{2.08}\) on the same family (I204). That is why sparse
  is the scale path when exact VR is too fat — **and** why it is not
  exact.
- Essential \(H_1\) held on every measured family; finite-bar bottleneck
  typically 0.005–0.055 **[empirical]** (I207–I218). figure8 / two_circles:
  ess \(H_1\) 3=3, bn 0.011 / 0.034. Consolidation `nested_loops` \(n=400\)
  can report extra essential loops (4 vs VR 1) **[empirical]**.
- Euclidean `--points` skip the n×n matrix: FPS is still \(\Theta(n^2)\)
  evaluations, emit is a finite-\(T\) hash in \(d\in\{2,3\}\). figure-8
  \(n=8000\): 0.75 s / 28 MB vs 1.01 s with a dense store **[empirical]**.
  This is **not** Sheehy’s \(O(n\log n)\) net-tree construction.
- Do **not** write “\(O(n^{1.2})\)” as a complexity theorem. I218’s
  \(n^{1.3}\)–\(n^{1.4}\) edge slopes are the measured pre-asymptotic
  window.

---

## 11. Sparse representations (owned; not a new PH theorem)

These change **how** \(G_T\) or a sparse flag is stored and how leftover /
H2 streams probe it. Exactness is “same pairs / same triangles as the
vendor loops,” not a smaller module.

### 11.1 Spatial metric + hash / CSR (I256–I263)

**Proven worst case.** Building \(G_T\) is \(\Theta(n^2)\) distances on a
connected dense instance **[derivation]**. A hash table or CSR of those
pairs is \(O(\lvert E\rvert)\) memory and expected \(O(1)\) or
\(O(\log\Delta)\) lookup **[derivation]** (standard). Worst-case
\(\lvert E\rvert=\Theta(n^2)\).

**Regime-specific bound.** Euclidean box of extent \(L\), finite \(T\):
if the \(T\)-ball volume fraction \(\pi(T/L)^d\) is small, a Moore grid
emits \(O(n+n\cdot(T/L)^d\cdot n_{\mathrm{cell}})\) candidate pairs
**[derivation]** (I256). I263 adds a 250-pt probe: spatial also if
\(\lvert E\rvert/C(m,2)<0.25\). Then metric memory is \(O(\lvert E\rvert)\)
(I258 CSR; I261 hash) **[derivation]**. I262 always-spatial **lost** the
dense 10× and was reverted **[empirical]**.

**Empirical-typical.** figure8 \(n=4000\) \(T=1.1\): 1.98M vs 8.0M pairs,
**27×** **[empirical]** (I263). Sparse connected \(n=20000\) \(T=0.09\):
4.71M vs 200M, **5.6–6.2×** **[empirical]** (I258–I261). Dense uniform2
\(n=5000\) I-wave all-pairs was **11.2×**; live 1-thread leftover
re-measure is **8.1×** (`leftover_10x.json`). Worst-case connected
\(G_T\) still \(\Theta(n^2)\).

### 11.2 CSR leftover-adjacency on sparse flags (I301–I306)

**Proven worst case.** Vendor `generate_stream` / leftover-coface ANDs an
\(n\)-bit neighborhood row: \(\Theta(n/64)\) word operations per edge /
leftover **[derivation]** from the rbit layout. Intersection of two sorted
adjacency lists of length \(\le\Delta\) is \(O(\Delta)\)
**[derivation]** (standard merge). Building those lists by sorted insert
is \(O(\lvert E\rvert\Delta)\) **[derivation]**. On a dense \(G_T\)
(\(\Delta=\Theta(n)\)) this is **not** cheaper than word-AND, and the
insert tax is worse (I303/I304) **[empirical]**.

**Regime-specific bound.** Gate \(\lvert E\rvert\le 16n\) (mean degree
\(\le 32\)):

\[
T_{\mathrm{H2\,stream}}^{\mathrm{CSR}}
=O(\lvert E\rvert\,\Delta)
\quad\text{vs}\quad
O(\lvert E\rvert\,n/64),
\qquad
T_{\mathrm{leftover\_coface}}^{\mathrm{adj}}
=O(\Delta)
\quad\text{vs}\quad
O(n/64),
\]

memory \(O(\lvert E\rvert)\) vs \(O(n^2/64)\) rbits **[derivation]**
(I301, I302). Dense \(G_T\) and fat 2D thicken (\(\lvert E\rvert>16n\))
**keep vendor rbits** (I303 mean-deg gate reverted; I304 hash leftover
reverted). I306 shares one growing \(G_r\) between the H2 stream and
leftover-coface: same asymptotics, less duplicate build
**[derivation]**.

**Empirical-typical.** Sphere Delaunay-flag: I301 \(n=30000\) 0.62→0.44 s;
I302 0.44→0.39 s; I306 \(n=50000\) 0.68→0.65 s; \(n=80000\) **1.09 s /
404k / ess2=1** **[empirical]**. figure8 fat thicken \(n=16000\) on
leftover-adj/hash **lost** (0.85 s / 1.55 s vs 0.63 s rbits)
**[empirical]**.

---

## 12. Auto dispatcher (portfolio, not a class)

`--engine auto` (I235+I236+I239+I240+I241+I263+I271+I275): 250-pt stride
collapse probe, \(\tau=0.04\) (\(H_1\)) / \(\tau=0.15\) (\(H_2\)); hollow
edge-frac \(<0.25\) → RedZeD; `maxdim=0` → Kruskal / Delaunay.

### Proven worst case

- Both engines are exact VR engines (§4+§5 and §6). A dispatcher that
  picks one of them is exact VR **[derivation]**. Topology loss: **0** on
  the measured suite **[empirical]** (I235–I263 waves).
- Probe cost \(O(s^2)\) with \(s=250\) fixed, independent of \(n\)
  **[derivation]** (I235). Full work is whichever engine is chosen.
- **Worst-case \(H_1\)** on a connected dense \(G_T\) is the worse of the
  two engines — i.e. still the Ripser / RedZeD class of §3 / §6
  **[derivation]**. Dispatch does not create a new Big-O.

### Regime-specific bound

- Fat residual (\(\lvert R\rvert/\lvert E\rvert\gtrsim\tau\)) or hollow
  edge-frac: skip the \(\Theta(\lvert E\rvert\Delta^3)\) collapse walk and
  pay RedZeD **[derivation]** (I235/I263). Thin residual: skip RedZeD
  leftover visits and pay collapse+implicit.
- Disconnected \(G_T\): spatial UF + per-component metric
  \(\sum_k m_k^2/2\) instead of \(n^2/2\) **[derivation]** (I240). Reduce
  \(\sim(n/k)^{\alpha}\) per block with \(\alpha\approx 2.3\) measured
  **[empirical]** (I229/I239). Connected \(G_T\) unchanged.
- Euclidean `maxdim=0`, \(d\in\{2,3\}\): §8 replaces listing \(G_T\).

### Empirical-typical

- Live 1-thread leftover-family re-measure (`leftover_10x.json`)
  **[empirical]**: torus \(n=2000\) H1 **12.6×**; figure8 \(n=2000\)
  **17.0×**; blobs \(n=4000\) H1 **12.9×**; uniform2 \(n=5000\)
  **8.1×**; sphere \(n=2000\) H1 **8.5×**; **3/6 leftover families
  ≥10×**. Circle \(n=1000\) **31×** is collapse, not leftover.
  I-wave mixed figure8 \(n=4000\) **27× / 1.07 s**; sphere \(n=400\)
  H2 **58×**; sphere \(n=800\) H2 **527× / 56 ms** (Ripser tet tax);
  sparse \(n=20000\) **5.6×** **[empirical]** (SELECTED; I281).
- Not a general \(H_1\) 10×. Historical I-wave 11.2× / 10.1× /
  13.0× leftover lines do **not** hold on this box. Not a better
  worst-case class.
- Consolidation phase-2, **1 thread**, 12 s budget **[empirical]**:
  circle \(n=1000\) **31×** (0.070 vs 2.21 s); sphere \(n=400\) H2 **60×**.
  Hardware threads do not move those ratios. Ripser timed out on circle
  \(n=2000\), figure8 \(n=4000\), sphere \(H_2\) \(n=800\). Mixed 1D/2D/3D
  \(n=300\) `maxdim=2` fat residual: exact **timeout**; `--estimate` now
  treats fat `maxdim≥2` as exact-infeasible. Local time exponents: scale
  \(p\approx 1.0\)–\(1.3\); exact leftover \(H_1\) \(p\approx 2.8\) on
  figure8 2k→4k (polynomial explosion, not a claimed exponential).
  1-thread engine oracle **7/8**; `heavy_noise_circle` waste 2.1×.

---

## 13. Side-by-side (what each method is allowed to claim)

| Method | Exact VR? | Proven worst-case class | Regime cut | Empirical-typical (this project) |
| --- | --- | --- | --- | --- |
| Ripser implicit coh. | Yes | VR \(k\)-skeleton + cubic residual reduce; implicit \(\neq\) smaller rank | Sparse \(G_T\): probes \(O(\Delta)\); coh+clearing skips births | Time \(n^{2.1}\)–\(n^{3.3}\) on I204 |
| Collapse (B–P) | Yes | \(O(\lvert E\rvert\Delta^3)\) back; \(\lvert R\rvert\le\lvert E\rvert\) | Geometric cone-like links: \(\lvert R\rvert\ll\lvert E\rvert\) | \(\lvert R\rvert\sim n^{0.9}\)–\(n^{1.2}\) except torus \(\Theta(n^2)\) |
| Collapse+implicit | Yes | **Same as Ripser if \(\lvert R\rvert\sim\lvert E\rvert\)** | Thin \(\lvert R\rvert\): wall is the \(\Theta(\lvert E\rvert)\) walk | Circle 28–140×; torus collapse loses |
| RedZeD AE | Yes | Same pairing class; AE skips many \((k+1)\)-births, not worst-case \(o(\cdot)\) | Active-set / leftover output-sensitive; split on disconnected \(G_T\) | Torus **12.6×** live; leftover 3/6 ≥10×; time \(n^{2.0}\)–\(n^{2.4}\); connected 10× is not general |
| Kruskal \(H_0\) | Yes (\(H_0\)) | \(O(\lvert E\rvert\log\lvert E\rvert)\) after listing | Spatial listing \(O(\lvert E\rvert)\) | \(\sim 1.9\times\) vs Ripser \(H_0\) if \(G_T\) is listed |
| 2D/3D Del \(H_0\) | Yes (\(H_0\), Euclidean) | 2D size \(\Theta(n)\), construct \(O(n\log n)\) (classical Del); 3D size \(O(n^2)\) worst | Expected \(O(n\log n)\) walk under standard RIC hypotheses | Blobs 25k **515×**; sphere 30k **288×** |
| Delaunay-flag | **No** | Flag of Del: 2D \(\lvert E\rvert=\Theta(n)\); persist as §3/§6 on that graph | Typical \(\bar d=O(1)\Rightarrow\lvert K_k\rvert=O(n)\) | Ess kept; finite unmatched 3–209; 3D 80k **1.09 s** |
| Sheehy sparse | **No** (interleaving) | \(O(n)\) size, \(O(n\log n)\) build, \((1/\varepsilon)^{O(k\delta)}\) | Bounded doubling | Owned \(\varepsilon=0.6\) Max **thins** the flag (figure-8 8k: 380k vs 32M pairs) **[empirical]**; FPS build is still \(\Theta(n^2)\) (no n×n store on Euclidean `--points`); \(H_2\) timeout at \(n=400\) |
| Auto dispatch | Yes (exact engines only) | Worse engine on connected dense \(G_T\) | Probe \(O(1)\) in \(n\); pick thin vs fat vs hollow vs \(H_0\); refuse fat \(H_2\) sparse when \(d\notin\{2,3\}\) | Shape-agnostic 0 unmatched; portfolio ratios above; 4D fat \(H_2\) auto exits 3 **[empirical]** |
| CSR leftover-adj | Yes (same flag) | Dense: no win | \(\lvert E\rvert\le 16n\): \(O(\lvert E\rvert\Delta)\) vs \(O(\lvert E\rvert n/64)\) | Sphere 50k 0.84→0.65 s; fat thicken stays rbits |

---

## 14. Output-sensitive cheat sheet

Collecting the expressions that are actually used. All are
**[derivation]** from the citations in §§2–11 unless marked.

| Work item | Expression | Notes |
| --- | --- | --- |
| Dense metric | \(\Theta(n^2)\) | Worst-case \(G_T\) |
| Sparse / spatial metric | \(O(\lvert E\rvert)\) memory; emit \(O(\lvert E\rvert)\) | Gate I256/I263; not worst case |
| Collapse (backward) | \(O(\lvert E\rvert\Delta^3)\) | **[citation]** Glisse–Pritam |
| Collapse (forward) | \(O(\lvert E\rvert\,\lvert R\rvert\,\Delta^2)\) | **[citation]** Boissonnat–Pritam |
| Flag \(k\)-simplices | \(\lvert K_k\rvert\le\sum_v\binom{\deg v}{k}\le\binom{n}{k+1}\) | Definition |
| Implicit cofacet probe | \(O(n)\) dense / \(O(\Delta)\) sparse | Bauer enumerator |
| Residual reduce | \(O(C\,s_{\mathrm{col}}\log s_{\mathrm{col}})\) heap; \(O(C^3)\) classical worst | §2.1 |
| RedZeD leftover visit | \(\Theta(\lvert E\rvert)\) visits; each leftover-coface \(O(n/64)\) or \(O(\Delta)\) | Vendor vs I302 |
| RedZeD AE | Loop \(\lvert A\rvert\) active faces per birth leftover | **[citation]** §3 |
| Kruskal | \(O(\lvert E\rvert\log\lvert E\rvert+\lvert E\rvert\alpha(n))\) | Classical |
| 2D Del construct | \(O(n\log n)\) worst case (Fortune); owned walk expected \(O(n\log n)\) | **[citation]**; walk not a new WC theorem |
| 3D Del construct | \(O(n^2)\) worst case; expected \(O(n\log n)\) in the RIC / well-distributed regime | **[citation]** |
| Sheehy build | \(O(n\log n)\), \(\lvert K\rvert=O(n)\cdot(1/\varepsilon)^{O(k\delta)}\) | **[citation]** |
| Auto probe | \(O(s^2)\), \(s=250\) | I235 |
| CSR H2 / leftover-adj | \(O(\lvert E\rvert\Delta)\) on \(\lvert E\rvert\le 16n\) | I301/I302 |

---

## 14.1 Equal-hardware baselines (empirical, phase 3)

Same 4 CPU / 16 GB image, 12 s budget. PITH `--threads 1`. Ripser 1
thread. giotto-ph 0.2.4 `n_threads=1` and `4` (AGPL oracle; collapse
off unless noted). GUDHI 3.13 Rips is an explicit simplex tree (1 thread).
**[empirical]**

| Family | \(n\) | PITH 1-thr | Ripser | giotto t1 | giotto t4 | GUDHI Rips |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| circle \(H_1\) | 1000 | 0.068 s | 2.16 s | 2.47 s | 2.44 s | timeout |
| figure-8 \(H_1\) | 2000 | 0.152 s | 2.51 s | 2.81 s | 2.78 s | timeout |
| sphere \(H_2\) | 400 | 0.017 s | 1.02 s | 1.12 s | 0.62 s | timeout |
| torus \(H_1\) | 1000 | 0.040 s | 0.381 s | 0.461 s | 0.417 s | 2.85 s |
| dense RGG \(H_1\) | 800 | 0.018 s | 0.089 s | 0.119 s | 0.107 s | 6.44 s |

Local slopes on the same windows: Ripser / giotto \(p\approx 2.8\)–\(4.0\);
GUDHI Rips \(p\approx 3.2\)–\(3.4\) until timeout; PITH exact \(p\approx 1.2\)–\(2.7\)
then leftover \(p\approx 2.7\) on figure-8. giotto 4-thread is **not** a
4× wall cut on \(H_1\) (often slower than 1-thread). The 31–60× vs Ripser
therefore also holds against 4-thread giotto-ph on these families.

GUDHI Rips becomes impractical (timeout) by \(n\sim 10^3\) on a noisy
circle \(H_1\) and by \(n=400\) on sphere \(H_2\). That is the explicit
complex, not a pairing-class win for PITH.

---

## 15. What PITH is allowed to say in one paragraph

PITH’s exact default is a **portfolio of existing exact algorithms**
(Bauer implicit cohomology + Chen–Kerber clearing + Boissonnat–Pritam
collapse + Kapulkin–Kershaw RedZeD + Kruskal), plus a constant-size
subsample dispatcher and sparse *representations* of \(G_T\). On a
**connected** dense threshold graph the worst-case \(H_1\) class is the
same as Ripser VR: collapse may leave \(\lvert R\rvert=\Theta(\lvert E\rvert)\),
and RedZeD leftover visits remain \(\Theta(\lvert E\rvert)\). Clock wins
on circle / torus / figure8 / blobs are **regime + implementation**
(thin residual, active-enumeration skip of \((k+1)\)-births, component
split, \(O(\lvert E\rvert)\) metric). Euclidean `maxdim=0` in \(d\in\{2,3\}\)
is a **better size + construction class** for \(H_0\) because
MST \(\subseteq\) Delaunay (classical), not because pairing got cheaper.
The optional Delaunay-flag / Sheehy-sparse paths sit in a better *size*
class and are **not** exact VR; their loss is quantified (unmatched finite
bars / bottleneck / interleaving), not wished away. Owned Delaunay
walk-locate and CSR leftover-adjacency are the project-specific
construction / representation cuts on sparse flags. None of this is a new
worst-case Big-O theorem versus Ripser on connected \(G_T\).

---

## 16. Primary sources

| Source | Used for |
| --- | --- |
| Bauer, *Ripser*, *J. Appl. Comput. Topol.* 2021; arXiv:1908.02518 | Implicit coboundary, apparent / emergent pairs, cohomology+clearing counting, enclosing radius |
| de Silva–Morozov–Vejdemo-Johansson, *Dualities in persistent (co)homology*, 2011; arXiv:1107.5665 | Homology \(\leftrightarrow\) cohomology barcodes; why cohomology |
| Chen–Kerber, *Persistent homology computation with a twist*, EuroCG 2011 | Clearing / twist; output-sensitive column cost |
| Edelsbrunner–Letscher–Zomorodian, *Topological persistence and simplification*, 2002 | Standard pairing |
| Zomorodian–Carlsson, *Computing persistent homology*, 2005 | Barcodes over a field |
| Boissonnat–Pritam, *Edge collapse and persistence of flag complexes*, SoCG 2020 | Exact flag collapse; \(O(\lvert E\rvert\,\lvert R\rvert\,\Delta^2)\) |
| Glisse–Pritam, *Swap, shift and trim*, arXiv:2203.07022 | Backward collapse; \(O(\lvert E\rvert\Delta^3)\) |
| Sheehy, *Linear-size approximations to the VR filtration*, DCG 2013; arXiv:1203.6786 | \(O(n)\) sparse Rips, \(O(n\log n)\) build, multiplicative guarantee |
| Cavanna–Jahanseir–Sheehy, CCCG 2015 | Geometric / GUDHI sparse variant |
| Kapulkin–Kershaw, *RedZeD*, arXiv:2606.06310 | Zero-differential reduction; active enumeration; Prop. 3.2 |
| Burella Pérez et al., *giotto-ph*, arXiv:2107.05412 | Parallel CPU VR + collapse; AGPL oracle only (not vendored) |
| Bauer–Edelsbrunner, *Morse theory of Čech and Delaunay*, 2017 | Alpha / Čech / Del–Čech \(\neq\) VR |
| Bauer–Roll, *Gromov hyperbolicity… and apparent pairs*, SoCG 2022 | Apparent-pair rate is geometric |
| Shamos–Hoey 1975; Preparata–Shamos | Euclidean MST \(\subseteq\) Delaunay |
| Fortune 1987; Guibas–Knuth–Sharir 1992 | 2D Delaunay \(O(n\log n)\); RIC expected time |
| Seidel (Delaunay size) | 3D \(\Theta(n^2)\) worst case; \(\Theta(n^{\lceil d/2\rceil})\) |
| Kruskal 1956; Tarjan union-find | \(H_0\) |

Project ledgers: `docs/SELECTED.md` (living algorithm, through I312),
`docs/PAPERS.md`, `docs/ALGORITHM_COMPARISON.md`, `docs/COMPLEXES.md`,
`docs/EDGE_COLLAPSE_SPEC.md`, `src/pith/include/pith/redzed_bridge.hpp`,
`RESEARCH_LOG.md` I228, I235, I263, I271, I275, I276, I282, I300–I306,
I310–I312.

---

## 17. Status of this draft

Evidence class: **ledger** (citations + derivations + named empirical
slopes). No new theorem. No goal marked complete. If a later iteration
proves a worst-case \(H_1\) bound better than Ripser VR on every connected
\(G_T\), it must be written as a numbered statement with a proof; it must
not be inferred from an I204 / I218 exponent.
