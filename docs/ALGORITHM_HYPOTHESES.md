# Algorithmic hypotheses for a CPU-first Vietoris–Rips engine

Status: **proposal ledger** (2026-10-13). No new code. No diagrams claimed.
Evidence class of this file: written hypotheses + cheapest reject experiments.
Nothing here is selected.

**Target.** A CPU algorithm that does about **10× less algebraic work** than
unmodified [Ripser](https://github.com/Ripser/ripser) on typical point clouds,
and that remains **exact for the Vietoris–Rips (VR) filtration** whenever
exactness is claimed.

**Algebraic work** (the scoreboard) is not wall-clock time. Count, in order:

1. distances evaluated or stored;
2. simplices generated or enumerated;
3. columns assembled;
4. columns reduced (non-apparent, non-cleared);
5. column additions / heap cancellations;
6. cofacet / facet enumerations.

A run that is faster but performs the same counts is an **implementation**
result (`docs/METHODOLOGY.md` class A). A 10× claim against Ripser must be
class B (structural) or C (theoretical), with fidelity `exact` for the same
VR filtration, or must be labeled `approx-guaranteed` / `empirical` and
taken off the 10×-exact scoreboard.

**Pinned exact parent.** Ripser, MIT, SHA
`01add51ff64aaf40889483260cc5c3b7d0f2a1e7` (`docs/ALGORITHM_COMPARISON.md` §8).
Same diameter convention, same reverse-colex tie-break, same field
(\(\mathbb{F}_2\) default). GPU (Ripser++) is a later reference, not the kernel.

**Architecture proposed below.** **PITH** — Preprocessed Implicit Topology
Homology. A small MIT C++ CPU engine we own: pluggable exact (or honestly
labeled) preprocessors feeding a Ripser-style implicit cohomology core.

---

## 0. How to read a hypothesis

Each item is an **independent lever**. Do not stack two levers in the same
experiment (`docs/METHODOLOGY.md` §4.1). A combination is a *later*
hypothesis, named as such.

Required fields match `INSTRUCTIONS.md` §8 and the proposal template in
`docs/METHODOLOGY.md` §4.1.

Independence test used here: two directions are independent if they remove
**different work** (edges vs birth columns vs residual additions vs
distances vs sort vs indexing) or rest on **different theorems**. Variants
of the same theorem (one-pass vs iterated edge collapse) are listed
separately only when the cheapest reject experiment can kill one and spare
the other.

Priority:

| Tag | Meaning |
| --- | --- |
| **P0** | First wave toward 10× exact VR vs unmodified Ripser on \(H_0\)–\(H_1\). |
| **P1** | Next wave if P0 is short of 10×, or the natural stack after P0. |
| **P2** | Different guarantee, unverified theorem, or constant-factor only. |

Predicted class: `implementation` / `structural` / `theoretical`.

Sources that constrain the list: `docs/COMPLEXES.md` §13–15,
`docs/ALGORITHM_COMPARISON.md` §5–9 and §11, `docs/PAPERS.md` must-reads
and §14 (RedZeD, distilled VR caveat), `INSTRUCTIONS.md` CPU-first strategy.

---

## 1. Working picture of Ripser’s work (what we are allowed to cut)

On a typical point cloud, unmodified Ripser already:

- never stores the VR complex;
- uses cohomology + clearing, which avoids a combinatorial majority of
  columns (Bauer’s counting argument);
- skips apparent pairs (often 90–99% of columns);
- aborts coboundary enumeration on emergent / shortcut pairs;
- cuts the useless tail of the filtration with the enclosing radius when
  no threshold is given;
- spends the residual time on (i) the dense distance matrix, (ii)
  combinadic cofacet enumeration, (iii) heap reduction of the unpaired
  remainder.

So “10× less than Ripser” cannot mean “add apparent pairs.” They are
already there. The remaining exact levers are: **shrink the flag
1-skeleton**, **do not generate the full clique complex of that skeleton**,
**skip more of the remainder than apparent/emergent already skip**, or
**prove a smaller degree-\(q\) complex with the same \(\mathrm{PH}_q\)**.

Approximate levers (Sheehy, witness, Alpha-as-VR) are kept in this ledger
because they can beat 10× in *cells*, but they are **not** 10×-exact-VR
and must never be sold as such.

---

## 2. Hypotheses

### H01 — Flag edge collapse before any coboundary work

| Field | Content |
| --- | --- |
| **Concrete problem** | Dense VR 1-skeletons force \(\Theta(n^{k+1})\) \(k\)-cliques. Ripser pays cofacet enumeration on that graph even when most edges are dominated. |
| **Starting technique** | Boissonnat–Pritam edge collapse (SoCG 2020): delete / raise dominated edges (\(N[e]\subseteq N[v']\)); residual stays flag. Glisse–Pritam swap/shift/trim as the implementation reading. GUDHI `flag_complex_collapse_edges` as the oracle, **not** as vendored code. |
| **Work it hopes to eliminate** | Edges first (\(\sim 12\)–\(30\times\) in the SoCG 2020 table). Then \(k\)-simplices as \(\sim\rho^k\), columns assembled, cofacet enumerations, and additions on the deleted cliques. Distances among non-residual pairs can be dropped after collapse. |
| **Topological properties preserved** | Exact persistence module of the original flag / VR filtration, all degrees. Simple-homotopy / filtration-compatible collapses. |
| **Hypotheses required** | Input is a flag filtration. Domination tests see the correct closed neighborhoods. Filtration rewrite stays a filtration (values only increase). Same field and tie policy as the parent after reindexing. |
| **Complexity before / after** | Collapse: \(O(n\,n_c\,k^2)\) on the graph (\(n\) input edges, \(n_c\) critical edges, \(k\) max degree). Residual VR \(k\)-skeleton \(O(n_c^{k})\) cliques vs \(O(n^{k})\) if one expands, or implicit in the residual graph. No better *worst-case* than Ripser if \(n_c\sim n\) (high-d noise). |
| **Risks / counterexamples** | giotto-ph: collapse does not always pay. High-d i.i.d. noise: few dominated edges, collapse time dominates. After collapse the remainder may be *less* apparent-pair rich, so column reductions may not fall as \(\rho^k\). HIV-scale graphs: collapse itself takes minutes. |
| **How to verify correctness** | Diagram identity vs pinned Ripser on the **same** thresholded VR filtration (class `exact`). Cite Boissonnat–Pritam for the general statement; suite identity is not the proof. |
| **Cheapest reject / support** | GUDHI collapse on the protocol clouds (\(n\le 2\cdot 10^3\), \(H_0\)–\(H_1\)). If median edge ratio \(n/n_c < 3\) **and** collapse time \(\ge\) Ripser barcode time, reject as a *default* preprocessor on that neighborhood (`retry_when`: geometric samples with boundary, higher \(k\), iterated collapse). Support if \(n/n_c\ge 10\) on \(\ge\) half the typical-cloud suite with diagram identity. |
| **Predicted class** | structural (exact) |
| **Priority** | **P0** |

---

### H02 — Residual-graph implicit cohomology (do not expand the collapsed flag complex)

| Field | Content |
| --- | --- |
| **Concrete problem** | The usual collapse pipeline expands the residual flag complex (simplex tree) and then reduces. That reintroduces \(O(n_c^{k+1})\) storage and throws away Ripser’s implicit coboundary. Collapse then loses to Ripser on memory even when \(n_c\ll n\). |
| **Starting technique** | Ripser combinadic coboundary enumerator, but the 1-skeleton is the **collapsed sparse graph**, not \(K_n\). Cofacet of \(\sigma\): insert a vertex adjacent to *all* vertices of \(\sigma\). Reindex surviving vertices to \(0..n'-1\). |
| **Work it hopes to eliminate** | Materialized residual simplices; cofacet probes against non-neighbors; binomial-table walks over vertices that are no longer eligible. Additions only on implicit columns of the residual. |
| **Topological properties preserved** | Exact PH of the collapsed flag filtration, hence of original VR (H01). |
| **Hypotheses required** | Residual is flag. Enumerator emits cofacets in the same diameter / colex order Ripser uses, or emergent-pair abort is disabled. Vertex reindexing is an order-isomorphism of the refined filtration (document the induced tie-break). |
| **Complexity before / after** | Before: expand \(O(n_c^{d+1})\) then reduce, or Ripser on the original \(O(n^{d+1})\) implicit skeleton. After: implicit in a graph with \(n_c\) edges; cofacet degree \(\le\) residual min-degree, not \(n\). |
| **Risks / counterexamples** | Wrong adjacency test ⇒ missing / extra cofacets ⇒ wrong barcode. Reindexing that changes colex order vs Ripser can change *simplexwise* pairs even if the *diameter* barcode matches; tests must use the documented parent convention. Sparse enumerator can be slower per cofacet than dense combinadic if CSR gathers miss cache. |
| **How to verify correctness** | Identity vs (i) Ripser on the original filtration and (ii) GUDHI collapse+expansion+PH on the residual, same field. Mutation control: corrupt one adjacency; diagrams must change. |
| **Cheapest reject / support** | \(n=200\) noisy circle. Implement only the enumerator + Ripser reduction on the GUDHI-collapsed graph (no new collapser). Reject if diagrams differ or if cofacet enumerations do not drop vs Ripser by \(\gtrsim n/n_c\). |
| **Predicted class** | structural (exact), with an implementation face (CSR vs dense) |
| **Priority** | **P0** |

H01 without H02 is “collapse then GUDHI.” H02 without H01 is “Ripser on a
sparse threshold graph.” They are independent levers.

---

### H03 — Thresholded sparse 1-skeleton as the default exact VR input

| Field | Content |
| --- | --- |
| **Concrete problem** | Ripser’s dense lower-triangle matrix is \(O(n^2)\) distances and makes every vertex a candidate cofacet. Typical clouds are run with a finite threshold \(T\) (or enclosing radius). The unused tail still pollutes enumeration and memory. |
| **Starting technique** | Build the undirected graph \(G_T=(X,\{pq:d(p,q)\le T\})\) once (CSR / neighbor lists). Implicit VR is the clique filtration of \(G_T\). This is exactly Ripser’s sparse-distance path, made mandatory and instrumented. |
| **Work it hopes to eliminate** | Distances \(>T\); cofacet insertions of non-neighbors; \(O(n^2)\) RAM when \(e\ll n^2\). Columns of simplices that never exist at \(T\). |
| **Topological properties preserved** | Exact PH of the **truncated** VR filtration \(\mathrm{VR}_{\le T}\). Not the untruncated VR module unless \(T\) is at least the enclosing radius (or the diameter). |
| **Hypotheses required** | The scientific claim is \(\mathrm{VR}_{\le T}\), and the Ripser parent is run with the **same** \(T\). Metric is symmetric. Isolated vertices remain. |
| **Complexity before / after** | Distances: \(O(n^2)\) vs \(O(n^2)\) compute still, but storage \(O(e)\) and cofacet probes \(O(\deg)\) not \(O(n)\). Clique count \(\le O(\sum_v \binom{\deg v}{k})\). |
| **Risks / counterexamples** | Comparing to Ripser *without* \(T\) (or with enclosing radius \(\gg T\)) is a different filtration. High-d noise at interesting \(T\) is still dense. Building \(G_T\) can dominate \(H_0\)–\(H_1\) on small \(n\). |
| **How to verify correctness** | Identity vs Ripser `--threshold T` (sparse or dense input). Report \(e\), mean degree, and columns assembled. |
| **Cheapest reject / support** | Same \(T\) as the protocol. If \(e/n^2 > 1/2\) on typical clouds, sparse representation cannot give 10× (reject as a *10×* lever; keep as a memory layout). Support if \(e/n^2\le 1/10\) and cofacet enumerations drop proportionally, diagrams identical. |
| **Predicted class** | structural (exact for the truncated filtration) |
| **Priority** | **P0** |

---

### H04 — Stronger discrete Morse / chunk matching on the residual

| Field | Content |
| --- | --- |
| **Concrete problem** | Apparent pairs already skip 90–99% of VR columns. The 10× gap vs Ripser, if it exists after H01–H03, lives in the **unpaired remainder**. Apparent matching is a *greedy local* gradient, not a maximum one. |
| **Starting technique** | Mischaikow–Nanda `MorseReduce`; PHAT `chunk` (local pairs, not necessarily incident); Oineus `ApparentMatching` local detector as the cheap end of the spectrum. Goal: a filtration-compatible acyclic matching strictly larger than Ripser’s zero-persistence apparent pairs, then implicit (or explicit residual) reduction of critical cells only. |
| **Work it hopes to eliminate** | Residual columns and additions that are persistence-0 or locally paired but not apparent in Bauer’s sense. Optionally, store only critical cells (Perseus). |
| **Topological properties preserved** | Exact PH of the input filtration if the matching is a filtered discrete gradient (Mischaikow–Nanda Thm. 4.3; PHAT chunk). Apparent pairs remain a subset. |
| **Hypotheses required** | Matching is acyclic and non-decreasing in filtration value. If we only claim zero-persistence extra pairs, they must be pairs of the simplexwise refinement. Field-independent matchings preferred. |
| **Complexity before / after** | MorseReduce \(O(n\cdot p\cdot \tilde m)\) then \(O(m^3)\) on \(m\) critical cells. Win only if \(m\ll\) Ripser’s unpaired count *and* matching cost \(<\) saved reductions. Worst case \(m\approx n\). |
| **Risks / counterexamples** | Matching construction can exceed Ripser’s whole runtime (Perseus on VR). A matching that needs the explicit complex fights H02. Distilled-VR-style “reachable from critical cells” has a reported counterexample (H08). Extra pairs that are not gradient pairs change the barcode. |
| **How to verify correctness** | Identity vs Ripser. Count `columns_reduced` and `additions`. The matching must be dumpable and checked acyclic. |
| **Cheapest reject / support** | On the residual after H01 (or on raw VR if collapse is off), compute Ripser unpaired columns \(U\). Run PHAT chunk or a local extra-pair pass on a **tiny explicit** \(H_1\) instance (\(n\le 80\)). Reject if critical columns \(\ge 0.7|U|\) or matching time \(\ge\) Ripser time. Support if critical columns \(\le |U|/10\) with identity. |
| **Predicted class** | structural (exact); the *existence* of a larger gradient on typical VR is theoretical until proved |
| **Priority** | **P0** |

---

### H05 — Degree-specialized \(H_0\)–\(H_1\) pipeline (no \(H_2\) machinery)

| Field | Content |
| --- | --- |
| **Concrete problem** | The 10× target is \(H_0\)–\(H_1\) first. A generic \(d\)-skeleton enumerator still walks 2-cofacets and binomial \(C(\cdot,3)\) while computing \(H_1\). Clearing already skips many \(H_1\) births, but construction and apparent tests in unused dimensions remain. |
| **Starting technique** | Ripser’s dim-0 union-find; stop the filtration at the 2-skeleton; \(H_1\) coboundaries only (edges \(\to\) triangles). Optional: reduced VR (H07) as the \(H_1\)-only complex. Involuted PH is *out of scope* (cycles, not barcodes). |
| **Work it hopes to eliminate** | Tetrahedra and higher; 3-cofacet enumerations; binomial rows for \(k\ge 3\); clearing bookkeeping for unused dimensions. Distances still needed for triangles. |
| **Topological properties preserved** | Exact \(\mathrm{PH}_0\) and \(\mathrm{PH}_1\) of the stated VR filtration. No claim on \(\mathrm{PH}_{\ge 2}\). |
| **Hypotheses required** | `maxdim = 1`. Clearing that would have used \(H_2\) pairs is not required for \(H_1\) cohomology (cohomology goes upward). |
| **Complexity before / after** | Before: implicit 2-skeleton is already Ripser’s `dim 1` mode. After: only a win if we *also* skip a large set of triangles (via H01/H07) or skip birth edges (H09). Alone, this is mostly not generating \(H_2\). |
| **Risks / counterexamples** | Comparing to Ripser `dim 2` is a different work target. Will not give 10× by itself on \(H_1\) (Ripser already has `dim 1`). Useful as a **contract** for PITH v1, not as a 10× lever. |
| **How to verify correctness** | Identity of \(H_0,H_1\) vs Ripser `--dim 1`. |
| **Cheapest reject / support** | Instrument Ripser `dim 1` vs `dim 2` on the same cloud: if `dim 1` algebraic counts are already the \(H_1\) scoreboard, H05 is accepted as an API constraint and **rejected as a 10× hypothesis**. |
| **Predicted class** | implementation (API / skipped unused dimension), unless stacked with H07 |
| **Priority** | **P0** (as the v1 contract; not as the 10× bet) |

---

### H06 — Smarter enclosing-radius and essential-death cutoffs

| Field | Content |
| --- | --- |
| **Concrete problem** | Ripser already sets \(T\) to the enclosing radius \(R\) (Henselman) when the user omits a threshold: above \(R\) the VR complex is a cone. Typical *benchmark* runs still pass a looser \(T\) or compute \(R\) naively (\(O(n^2)\)). Features that die before a cheap upper bound still generate later columns. |
| **Starting technique** | Enclosing radius as a first-class preprocessor: \(R=\min_p\max_q d(p,q)\), plus optional tighter *homology-death* bounds (e.g. all points in a ball of radius \(r\) ⇒ no \(H_{>0}\) after \(2r\) in diameter convention). Feed \(T=\min(T_{\mathrm{user}},R,T_{\mathrm{bound}})\) into H03. |
| **Work it hopes to eliminate** | Distances, simplices, and columns with diameter \(>T^\*\). The useless tail of the filtration. |
| **Topological properties preserved** | Exact PH of untruncated VR if \(T^\*\ge R\). Exact PH of \(\mathrm{VR}_{\le T}\) if the user asked for \(T\). A *tighter* bound than \(R\) must be proved; otherwise it is a different truncation. |
| **Hypotheses required** | Finite metric space. Cone argument for enclosing radius (standard). Any stricter cutoff needs a lemma (do not guess). |
| **Complexity before / after** | Computing \(R\): \(O(n^2)\) naive, or \(O(n)\) after the distance matrix exists. Saving: all work at diameters in \((T^\*,T_{\mathrm{old}}]\). Zero saving if the parent already used \(R\). |
| **Risks / counterexamples** | Unmodified Ripser already uses \(R\) when \(T\) is omitted — then H06 is not a 10× lever vs that parent. Wrong tighter bound kills long bars (circle of diameter \(\approx 2\): \(R\) is correct; a ball-radius mix-up of 2 vs \(1\) is a classic scale bug). |
| **How to verify correctness** | Identity vs Ripser with no threshold (both must use \(R\)) and vs Ripser `--threshold T`. If we ship a stricter bound, prove it or drop the `exact` label. |
| **Cheapest reject / support** | On the protocol, compute \(R\) and the user \(T\). If Ripser’s effective threshold is already \(\le R\) and the mass of simplices above \(0.8R\) is \(<10\%\) of enumerations, reject H06 as a 10× lever. Support if a large fraction of Ripser enumerations have diameter \(>R\) because the harness omitted the cutoff. |
| **Predicted class** | structural (exact) when it only applies \(R\); theoretical if a new bound is claimed |
| **Priority** | **P1** |

---

### H07 — Reduced Vietoris–Rips for exact \(H_1\)

| Field | Content |
| --- | --- |
| **Concrete problem** | Even after collapse, \(H_1\) still enumerates \(O(n^3)\) triangles in the worst case. Reduced VR claims an \(H_1\)-isomorphic filtration with \(O(n^2)\) triangles under bounded doubling dimension. |
| **Starting technique** | Koyama–Mémoli–Robins–Turner, arXiv:2307.16333. Build the reduced filtration \(\mathcal{R}_\bullet(X)\) from the distance matrix; run implicit cohomology only on that 2-complex. |
| **Work it hopes to eliminate** | Triangles (simplices), their coboundary columns, and additions: \(O(n^3)\to O(n^2)\) in the doubling case. Distances unchanged. |
| **Topological properties preserved** | Exact \(\mathrm{PH}_1\) of VR for any finite metric space (paper). Higher-degree extension is only indicated — **not** assumed. |
| **Hypotheses required** | We only claim \(H_1\). Doubling dimension enters *size*, not correctness. Construction must match the paper’s reduced star / edge rule. |
| **Complexity before / after** | Construction from \(O(n^2)\) distances. Size \(O(n^2)\) triangles if doubling is bounded; no such bound in high-d noise. |
| **Risks / counterexamples** | No production library. Easy to build a *different* 2-complex that looks smaller and is wrong. High doubling ⇒ no 10×. Must not silently emit \(H_2\). |
| **How to verify correctness** | Identity of \(H_1\) (and \(H_0\)) vs Ripser on many metrics, including the unit-square / grid cases used against distilled VR. Finite checks illustrate; the paper is the general claim. |
| **Cheapest reject / support** | Hand-build reduced VR on \(n\le 40\) (circle, two clusters, unit square). If any \(H_1\) bar differs from Ripser, reject the implementation (and stress-test the paper). Support if identity holds and triangle count \(\le 1/10\) of Ripser’s enumerated 2-simplices on a doubling sample. |
| **Predicted class** | structural + theoretical (exact \(H_1\)) |
| **Priority** | **P1** |

---

### H08 — Distilled Vietoris–Rips (Morse on reduced VR)

| Field | Content |
| --- | --- |
| **Concrete problem** | Memory of unpaired columns, not just their number. Distilled VR keeps only cells reachable from critical \((q+1)\)-simplices in an apparent matching on reduced VR. |
| **Starting technique** | Koyama–Robins–Turner, arXiv:2412.07805, Thm. 3.9 (claimed \(\mathrm{PH}_q(D^q)\cong\mathrm{PH}_q(\mathrm{VR})\)). |
| **Work it hopes to eliminate** | Stored simplices and residual columns that cannot affect degree \(q\). Aimed at memory and parallel build; runtime may still need many cores. |
| **Topological properties preserved** | **Claimed** exact \(\mathrm{PH}_q\) of VR. Treat as **unverified** (`docs/PAPERS.md` §9.2). |
| **Hypotheses required** | The isomorphism. Finite metric space. Degree \(q>0\). Apparent matching \(\mu_q\) as in the paper. |
| **Complexity before / after** | If the theorem holds and doubling is bounded: a much smaller explicit \(q\)-complex than VR. No worst-case bound better than VR if almost all cells are reachable. |
| **Risks / counterexamples** | Reported counterexample: unit square, standard VR has \(H_1\cong\mathbb{Z}_2\) at scale 1, distilled complex empty. **Do not ship as an exact preprocessor** until the proof is repaired or the counterexample is refuted. Parallel-build claims are not algebraic-work claims. |
| **How to verify correctness** | First: the unit-square instance. If empty vs Ripser \(H_1\neq 0\), the direction stays `rejected` / `conjecture`. Only then a broader identity suite. |
| **Cheapest reject / support** | Unit square (and a regular polygon). Reject immediately on barcode mismatch. No support path until that case is explained. |
| **Predicted class** | theoretical (currently `conjecture` / `unverified`) |
| **Priority** | **P2** |

---

### H09 — Active enumeration / RedZeD (skip VR birth columns)

| Field | Content |
| --- | --- |
| **Concrete problem** | Ripser still *assembles* many birth columns that clearing will later skip or that reduce to zero after a few additions. The work is coboundary construction, not pairing. |
| **Starting technique** | Kapulkin–Kershaw RedZeD (2026): pairing as reduction to zero differentials; **active enumeration** avoids enumerating many VR birth columns. Combinadic IDs borrowed from Ripser. |
| **Work it hopes to eliminate** | Birth-column assemblies, their cofacet enumerations, and the additions inside those columns. Not the 1-skeleton. |
| **Topological properties preserved** | Exact VR barcode if the reduction-to-zero-differentials reformulation is equivalent to standard pairing (paper). Same field. |
| **Hypotheses required** | Active-enumeration completeness: every non-zero class is hit. Tie-break compatible with the parent or documented. Treat published speedups as **unverified**. |
| **Complexity before / after** | Same worst-case matrix reduction. After: output-sensitive in the number of *active* columns. Paper: faster than Ripser on 21/22 tests, especially \(H_1\) with signal; Ripser wins some high-degree, low-signal cases. |
| **Risks / counterexamples** | High-degree, low-signal clouds (the paper’s losing neighborhood). Completeness bugs look like missing bars. AGPL/other license on `redzed-tda` — **reimplement ideas**, do not vendor, until the license is checked. Must re-benchmark. |
| **How to verify correctness** | Identity vs Ripser on the paper’s suite *and* our protocol. Count assembled columns, not just time. |
| **Cheapest reject / support** | Install or reimplement active enumeration for \(H_1\) only, \(n\le 300\) noisy circle + high-d noise. Reject if any bar differs, or if assembled columns do not drop on the *signal* set. Support if columns drop \(\ge 5\times\) on signal and identity holds; do not generalize to high-d noise without a run. |
| **Predicted class** | structural (exact), pending reproduction |
| **Priority** | **P1** |

---

### H10 — Deeper emergent / shortcut abort (pay only the pivot cofacet)

| Field | Content |
| --- | --- |
| **Concrete problem** | After apparent pairs, Ripser’s next cost is enumerating cofacets of residual columns. Emergent abort already stops at the first same-diameter unpaired cofacet. Many residual columns still build a long heap before the pivot stabilizes. |
| **Starting technique** | Bauer emergent / shortcut pairs; flagser-style “stop early” only as a *non-exact* cousin. Exact idea: certify the pivot with a cheaper oracle (oldest cofacet among a candidate set, or a diameter-sorted neighbor intersection) without listing every cofacet. |
| **Work it hopes to eliminate** | Cofacet enumerations and heap insertions / cancellations on residual columns. Not simplices of the complex, not distances. |
| **Topological properties preserved** | Exact pairing iff the aborted column’s pivot equals the fully reduced pivot (Ripserer contract: cofacets must be generated in the legal order). |
| **Hypotheses required** | Enumerator monotonicity in (diameter, index). Any new oracle must imply the same pivot as full reduction, not merely a zero-persistence guess. |
| **Complexity before / after** | Per residual column: \(O(|\delta\sigma|)\) now, hopefully \(O(\#\mathrm{neighbors})\) or \(O(1)\) for shortcut pairs. Saves a factor proportional to mean cofacet list length, **not** \(n\). Typical gain \(\ll 10\times\) unless residual columns are huge. |
| **Risks / counterexamples** | Unordered cofacet iterators (Ripserer: set `emergent_pairs=false` or get wrong pairs). Shortcut \(\neq\) apparent \(\neq\) emergent. Over-abort drops finite bars. |
| **How to verify correctness** | Identity vs Ripser; plus a mode that records pivot indices and compares to a no-abort build on \(n\le 80\). |
| **Cheapest reject / support** | Instrument Ripser: fraction of residual-column cofacets *after* the eventual pivot. If that fraction is \(<20\%\), H10 cannot be 10× (reject as a 10× lever; keep the existing abort). Support if the wasted tail is \(\ge 5\times\) the prefix *and* a cheaper oracle matches pivots. |
| **Predicted class** | structural (exact) if the oracle is proved; otherwise implementation of the same pairs |
| **Priority** | **P1** |

---

### H11 — Schur / matroid reduction of the residual matrix

| Field | Content |
| --- | --- |
| **Concrete problem** | Residual unpaired columns can still be large. Implicit \(R=DV\) heap reduction is cubic in the worst case in the number of those columns. Eirene and the SoCG 2025 “PH in matrix-multiplication time” line treat reduction as Schur complements / pivoting so large blocks of \(D\) are never stored. |
| **Starting technique** | Henselman–Ghrist (Eirene): Morse + Schur / matroid filtration. Use only the vocabulary and the residual matrix after H01–H04, not the GPL repo. |
| **Work it hopes to eliminate** | Stored coboundary entries; additions inside blocks that a Schur step can skip. Rank work toward \(O(m^\omega)\) instead of naive \(O(m^3)\) on \(m\) residual cells. |
| **Topological properties preserved** | Exact PH if the Schur / pivot sequence realises the same pairing (standard linear algebra over the field). |
| **Hypotheses required** | Residual matrix is explicit enough to pivot, **or** we have a matroid oracle compatible with implicit VR. Field operations exact. |
| **Complexity before / after** | Before: Ripser-like, output-sensitive but not matrix-multiplication. After (optimistic): \(O(m^\omega)\) with \(\omega<2.4\) on residual \(m\). Constants in fast MM are hostile at our \(m\). |
| **Risks / counterexamples** | Implicit VR fights stored \(D\). Fast MM is an implementation fantasy at PH scales. Eirene is GPL — ideas only. Easy to spend more than heap reduction. |
| **How to verify correctness** | Tiny residual matrices: pairing identity vs PHAT / Ripser. No complexity claim from timings. |
| **Cheapest reject / support** | Take the residual \(H_1\) matrix of an \(n\le 60\) cloud. Dense Gaussian elimination vs Ripser pairing. Reject if pivots differ or if \(m\) is already small enough that H01–H04 ate the 10×. Support only as a *theoretical* path if \(m\) stays \(>10^5\) after P0. |
| **Predicted class** | theoretical (complexity) + structural if it skips stored blocks |
| **Priority** | **P2** |

---

### H12 — In-order VR generation (kill the global sort, not the complex)

| Field | Content |
| --- | --- |
| **Concrete problem** | Engines that *materialize* simplices pay a sort of size \(\|K\|\). Oineus / Vejdemo-Johansson–Matuszewski–Bauer (arXiv:2411.05495) generate VR already in filtration order. |
| **Starting technique** | In-order VR generation feeding an implicit or lock-free reducer. |
| **Work it hopes to eliminate** | Comparisons in a global sort, not algebraic rank. Zero columns removed. |
| **Topological properties preserved** | Exact VR if the generated order is a legal simplexwise refinement. |
| **Hypotheses required** | We were going to materialize \(K\). PITH’s implicit core does **not**, so H12 is idle unless H04/H08 forces an explicit residual. |
| **Complexity before / after** | Sort \(O(\|K\|\log\|K\|)\) removed; generation still \(\Theta(\|K\|)\). |
| **Risks / counterexamples** | Measuring sort-less generation against implicit Ripser and calling it 10× algebraic work. It is not. |
| **How to verify correctness** | Order is non-decreasing in diameter; identity vs Ripser. |
| **Cheapest reject / support** | Profile pinned Ripser: if there is no \(\|K\|\log\|K\|\) sort, reject H12 for PITH’s implicit path. Reopen only if we store a Morse residual. |
| **Predicted class** | implementation |
| **Priority** | **P2** |

---

### H13 — Geometry-conditioned pairing (hyperbolicity / geodesic defect)

| Field | Content |
| --- | --- |
| **Concrete problem** | Apparent-pair *rate* is geometric (Bauer–Roll 2022): on trees / \(\delta\)-hyperbolic geodesic spaces the apparent gradient collapses large sublevel sets. Ripser is then “fast” without a new algorithm. Conversely, tori / high-loop / high-d noise are the hard neighborhood. A detector could skip whole diameter ranges. |
| **Starting technique** | Bauer–Roll: apparent pairs as a discrete gradient; collapse \(\mathrm{Rips}_u\to\mathrm{Rips}_t\to\{\ast\}\) under hyperbolicity hypotheses. Use a cheap \(\delta\) / treewidth proxy to *select* a cutoff or a matching, not to change the barcode by fiat. |
| **Work it hopes to eliminate** | Columns and distances in diameter ranges that the theorem already collapses to a point. |
| **Topological properties preserved** | Exact VR if we only skip pairs the theorem identifies. If we *assume* hyperbolicity that fails, essential bars die. |
| **Hypotheses required** | \(\delta\)-hyperbolicity and geodesic defect bounds that we **check**, not guess. Finite sample vs continuous space gap. |
| **Complexity before / after** | Checking hyperbolicity is not free (often worse than PH). After: if the space is a tree metric, almost all work is apparent — but Ripser already wins there. |
| **Risks / counterexamples** | Noisy circle and torus are not trees. Using a “looks hyperbolic” heuristic as an exact cutoff. Benchmarks that only contain clusters / trees overstate 10×. |
| **How to verify correctness** | Identity vs Ripser on hyperbolic *and* non-hyperbolic suites. Any skipped range must be justified by a cited lemma on that instance. |
| **Cheapest reject / support** | Compute apparent-pair rate on (tree, circle, torus, high-d noise). If the 10× target neighborhood (circle/torus/noise) already has apparent rate \(>99\%\), extra geometry does not cut residual work (reject as a 10× lever). Keep the observation for benchmark design. |
| **Predicted class** | theoretical (when to skip), not a default preprocessor |
| **Priority** | **P2** |

---

### H14 — Sheehy sparse Rips (linear-size **approximate** VR)

| Field | Content |
| --- | --- |
| **Concrete problem** | Exact VR \(k\)-skeletons are \(\Theta(n^{k+1})\). When \(n\) is large and doubling dimension is moderate, we may want a linear-size filtration with a theorem. |
| **Starting technique** | Sheehy sparse Rips / Cavanna–Jahanseir–Sheehy (GUDHI `sparse=ε`). Net-tree, \((1+\varepsilon)\)-style multiplicative interleaving. |
| **Work it hopes to eliminate** | Vertices / edges / simplices down to \(O(n)\) with constants \((1/\varepsilon)^{O(k\delta)}\). All subsequent columns. |
| **Topological properties preserved** | **Not** exact VR. Multiplicative approximation of the VR diagram (quote Sheehy / GUDHI’s \((1,1/(1-\varepsilon))\) form). Then 2-interleaved with Čech. |
| **Hypotheses required** | Doubling dimension \(\delta\) for the size theorem. \(\varepsilon<1\) for the guarantee GUDHI states. Never identity-test against Ripser. |
| **Complexity before / after** | \(O(n\log n)\) build, \(O(n)\) simplices vs \(O(n^{k+1})\). Constants explode with \(\delta\). |
| **Risks / counterexamples** | High-d cubes / expanders: “linear” with a huge constant (SimBa’s reason to exist). Short bars move. Selling this as 10× vs Ripser on the exact scoreboard. |
| **How to verify correctness** | Check \(\varepsilon\), report log-bottleneck vs Ripser on instances Ripser finishes. Hypothesis check, not identity. |
| **Cheapest reject / support** | GUDHI sparse \(\varepsilon\in\{0.3,0.5,0.8\}\) on one doubling sample and one high-d noise. Reject as a *default exact* tool immediately (wrong class). Support as the approx baseline if size drops \(\ge 10\times\) and the interleaving hypotheses hold. |
| **Predicted class** | structural + theoretical, fidelity `approx-guaranteed` |
| **Priority** | **P2** (off the exact 10× board) |

---

### H15 — Lock-free remainder and parallel apparent scan (same columns)

| Field | Content |
| --- | --- |
| **Concrete problem** | After exact shrinks, the unpaired remainder may still be sequential in Ripser. giotto-ph / Oineus reduce remaining columns out of order (pairing-uniqueness). Ripser++ scans apparent pairs in parallel. |
| **Starting technique** | Morozov–Nigmetov lock-free reduction; Ripser++ separation of parallelisms. **Reimplement under MIT/BSD.** Do not vendor AGPL giotto-ph. |
| **Work it hopes to eliminate** | Wall-clock waiting. **Zero** simplices / columns / additions. |
| **Topological properties preserved** | Exact VR (reordering does not change pairs). |
| **Hypotheses required** | Shared-memory atomics; CAS pivot table; leftover columns still left-to-right vs stored pivots. |
| **Complexity before / after** | Same algebraic counts. Wall-clock \(\approx\) sequential / \(\#\)cores in the ideal case, often much worse if apparent rate is already 99%. |
| **Risks / counterexamples** | Parallelizing a tiny remainder. Work-vs-time screen (`docs/METHODOLOGY.md` G5 tools) will reclassify any “10×” here as implementation. |
| **How to verify correctness** | Diagram identity vs sequential PITH / Ripser; work counters **equal**. |
| **Cheapest reject / support** | After P0, if `columns_reduced < 10^4`, reject H15 as a 10× project goal (keep as a later CPU opt). Support as implementation if counters match and median time drops on \(\ge 8\) cores. |
| **Predicted class** | implementation |
| **Priority** | **P2** |

---

### H16 — Alpha / Wrap as a **different** exact geometric complex

| Field | Content |
| --- | --- |
| **Concrete problem** | In Euclidean \(d\le 3\), VR pays \(\Theta(n^{k+1})\) for a module that is only 2-interleaved with the offset filtration. Alpha (and Wrap) realize offset / Čech PH on \(O(n)\)–\(O(n^{\lceil d/2\rceil})\) cells. |
| **Starting technique** | Delaunay → alpha / Delaunay–Čech; Bauer–Edelsbrunner Morse theory of Čech and Delaunay; Wrap for a still-smaller carrier of the same cycles. GUDHI Alpha as the oracle. |
| **Work it hopes to eliminate** | Almost all VR cliques that are not Delaunay. Often \(\gg 10\times\) cells at \(H_1/H_2\). |
| **Topological properties preserved** | Exact PH of **offsets / Čech**, not of VR. Simplexwise values differ from VR. |
| **Hypotheses required** | Euclidean \(\mathbb{R}^d\), \(d\le 3\) (exploratory \(d=4\)). General position or a symbolic kernel. The scientific target is offset PH. |
| **Complexity before / after** | Delaunay \(O(n\log n)\) typical in 2D, \(O(n^2)\) worst 3D, infeasible for \(d\gtrsim 5\). Then linear-ish PH. |
| **Risks / counterexamples** | Distance matrices, high-\(d\), non-Euclidean metrics. Identity vs Ripser **must fail** in general (different-complex screen). CGAL/GPL pieces in incremental Delaunay. |
| **How to verify correctness** | Identity vs GUDHI Alpha, not vs Ripser. Bottleneck vs VR reported only as interleaving illustration. |
| **Cheapest reject / support** | \(n=500\) in \(\mathbb{R}^2\): Alpha cell count vs VR 2-skeleton. Reject as a VR kernel (always). Support as the low-\(d\) **geometric** baseline if cells drop \(\ge 10\times\) and Alpha diagrams match GUDHI. |
| **Predicted class** | structural, exact for offsets; **not** exact VR |
| **Priority** | **P2** (baseline, not PITH’s VR kernel) |

---

## 3. Independence map (what each lever actually cuts)

| ID | Distances | Edges / verts | Simplices | Columns assembled | Columns reduced | Additions | Cofacet enum | Exact VR? |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| H01 edge collapse | after | **yes** | yes | yes | maybe | maybe | yes | yes |
| H02 residual implicit | — | — | **stored** | yes | — | — | **yes** | yes |
| H03 sparse \(G_T\) | stored | — | yes | yes | yes | yes | yes | truncated |
| H04 extra Morse | — | — | critical | yes | **yes** | **yes** | yes | yes |
| H05 \(H_0\)–\(H_1\) only | — | — | \(k\ge 3\) | unused dim | — | — | unused dim | yes, \(\le 1\) |
| H06 enclosing radius | tail | — | tail | tail | tail | tail | tail | if \(T\ge R\) |
| H07 reduced VR | — | — | **triangles** | \(H_1\) | \(H_1\) | \(H_1\) | \(H_1\) | \(H_1\) only |
| H08 distilled VR | — | — | memory | claimed | claimed | claimed | claimed | **unverified** |
| H09 RedZeD | — | — | — | **births** | maybe | maybe | births | claimed |
| H10 deeper abort | — | — | — | — | — | heap | **residual** | if oracle ok |
| H11 Schur | — | — | stored \(D\) | — | MM | block | — | if pivots ok |
| H12 in-order gen | — | — | sort only | — | no | no | no | yes |
| H13 hyperbolic skip | ranges | — | ranges | ranges | ranges | ranges | ranges | if lemma applies |
| H14 sparse Rips | nets | **yes** | yes | yes | yes | yes | yes | **no** |
| H15 lock-free | — | — | — | no | no | no | no | yes |
| H16 Alpha | Euclidean | Delaunay | **yes** | yes | yes | yes | yes | **no** (offsets) |

Sixteen directions. H12 and H15 cannot produce a 10× *algebraic* win.
H08, H14, H16 are excluded from the exact-VR 10× board.

---

## 4. First experimental architecture: **PITH**

**Name.** **PITH** — Preprocessed Implicit Topology Homology.

**Why this name.** The product is the *pith* of the VR filtration: whatever
remains after exact, pluggable peels (threshold, enclosing radius, edge
collapse, Morse). The core is implicit cohomology, not a new matrix
format.

**Why this cut.** `docs/ALGORITHM_COMPARISON.md` §5.1 and §8–9: the
combinable exact stack is collapse → enclosing radius / threshold →
implicit coboundary → cohomology + clearing → apparent pairs → emergent
abort. giotto-ph already ships that combination under AGPL. We own an MIT
C++ CPU engine so we can change the representation; we reimplement
ideas, we do not vendor giotto-ph, Eirene, or CubicalRipser.

**License.** MIT for all PITH sources. Ideas from AGPL/GPL engines are
reimplemented; GUDHI (MIT) may be an *external* collapse oracle in
experiments before we own a collapser.

**Language / hardware.** C++17, CMake, no CUDA in v1, no required Boost /
CGAL. Optional OpenMP only around independent scans (apparent tests,
distance assembly), never as a substitute for a smaller matrix. SIMD and
GPU are stage 3–4 (`INSTRUCTIONS.md` CPU-first).

**Exactness contract.** Default pipeline is `exact` for a named VR
filtration (full, truncated at \(T\), or collapsed-flag equivalent).
Any preprocessor that is not exact must set `fidelity =
approx-guaranteed` and is compiled out of the default binary path.

### 4.1 Pipeline

```
points / distance matrix
        │
        ▼
┌───────────────────┐
│  pith.metric      │  dense triangle  or  CSR G_T
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  preprocessors    │  each: Graph → Graph + Counters
│  (plugins, MIT)   │  default order below
└─────────┬─────────┘
          ▼
┌───────────────────┐
│  pith.core        │  Ripser-style implicit cohomology
│                   │  combinadic on the residual vertex set
│                   │  cofacets = common neighbors in G
│                   │  apparent + clearing + emergent abort
│                   │  H0 = union-find
└─────────┬─────────┘
          ▼
   diagram + COUNTERS
```

**Default preprocessor order** (each optional, each independently
disableable):

1. `enclosing_radius` — set \(T\leftarrow\min(T,R)\) (H06);
2. `sparse_threshold` — materialize \(G_T\) (H03);
3. `edge_collapse` — Boissonnat–Pritam on \(G_T\) (H01);
4. `morse` — matching interface; v1 = apparent pairs already inside the
   core; v2 = extra gradient (H04).

Sparse Rips (H14) may exist as a plugin with `fidelity=approx-guaranteed`.
It is not in the default chain.

### 4.2 Modules we would own

| Module | Path (proposed) | Responsibility | Not responsible for |
| --- | --- | --- | --- |
| **types** | `include/pith/types.hpp` | Field (\(\mathbb{F}_2\) default), `simplex_id`, diameter scalar, tie policy = reverse colex, fidelity enum | IO formats |
| **metric** | `include/pith/metric.hpp` | `DistanceOracle`: dense lower triangle *or* CSR neighbors; build from points (Euclidean) or a matrix | Approximate distances |
| **filtration** | `include/pith/filtration.hpp` | VR diameter convention; threshold; enclosing radius hook; documented simplexwise refinement | Alpha / cubical |
| **preprocess.enclosing_radius** | `include/pith/preprocess/enclosing_radius.hpp` | Compute \(R\); write effective \(T\) | New unproved death bounds |
| **preprocess.sparse_threshold** | `include/pith/preprocess/sparse_threshold.hpp` | Build \(G_T\); drop \(d>T\) | Changing \(T\) silently |
| **preprocess.edge_collapse** | `include/pith/preprocess/edge_collapse.hpp` | Dominated-edge collapse; iterate \(nb_iterations\); emit residual flag graph | Vertex/strong collapse by default |
| **preprocess.morse** | `include/pith/preprocess/morse.hpp` | `Matching` plugin: apparent (v1), extra gradient / chunk (v2) | Distilled VR until H08 is repaired |
| **core.combinadic** | `include/pith/core/combinadic.hpp` | Binomial table on the **residual** vertex ids | Full \(K_n\) assumption |
| **core.coboundary** | `include/pith/core/coboundary.hpp` | Cofacet enumerator: insert a common neighbor; diameters from the oracle | Stored coboundary matrix |
| **core.reduce** | `include/pith/core/reduce.hpp` | Implicit coboundary reduction, pivot hashmap, heap columns, clearing, emergent abort | Lock-free (H15), vineyards, \(U\) restore |
| **core.union_find** | `include/pith/core/union_find.hpp` | \(H_0\) only | Higher homology |
| **io.diagram** | `include/pith/io/diagram.hpp` | Birth/death pairs, essential bars, field, convention | Plotting |
| **io.counters** | `include/pith/io/counters.hpp` | The scoreboard: distances, edges in/out, simplices enumerated, columns assembled / reduced / cleared / apparent, additions, cofacet probes, peak RSS, stage times | “Speedup” without counts |
| **bench** | `bench/` | Pin Ripser SHA; run parent vs PITH; identity + counters; write `ENTRY.json` | GPU |

**Plugin interface (design only):**

```
struct Preprocessor {
  virtual std::string name() const = 0;
  virtual Fidelity fidelity() const = 0;   // exact | approx_guaranteed
  virtual Graph apply(Graph g, Counters& c) const = 0;
};
```

**Core interface (design only):**

```
Diagram persist(const Graph& residual,
                const DistanceOracle& dist,
                Params p,           // maxdim, field, T
                Counters& c);
```

### 4.3 What PITH is not

- Not a fork of Ripser++ and not a CUDA kernel.
- Not a GUDHI module (GUDHI stays the independent collapse / Alpha oracle).
- Not a vendor of giotto-ph, Eirene, PHAT, or CubicalRipser.
- Not a distributed shard-and-union barcode merger.
- Not an approximate VR engine unless a plugin says so.

### 4.4 Work-counter contract (non-negotiable)

Every PITH run and every Ripser parent run in this project must emit the
same counter names. A 10× claim is a 10× drop on a named subset of those
counters, on a named suite, with diagram identity. Wall-clock is a
footnote.

Suggested names: `n_vertices`, `n_edges_in`, `n_edges_out`,
`n_distances`, `n_simplices_enumerated`, `n_columns_assembled`,
`n_columns_apparent`, `n_columns_cleared`, `n_columns_reduced`,
`n_additions`, `n_cofacet_probes`, `collapse_ms`, `reduce_ms`,
`rss_bytes_peak`.

---

## 5. First eight experiments (priority order)

Goal of the sequence: decide whether an exact PITH stack can do **10×
less algebraic work** than unmodified Ripser on the **same** VR
filtration, \(H_0\)–\(H_1\) first, then \(H_2\). One lever per
experiment. Neighborhood: typical point clouds from the protocol
(noisy circle, sphere, torus, Gaussian mixtures, uniform, one licensed
real subset), \(n\) the machine can finish, Euclidean and at least one
high-d noise control.

Parent: Ripser SHA `01add51ff64aaf40889483260cc5c3b7d0f2a1e7`,
`--dim 1` for E1–E7, `--dim 2` for E8. Same \(T\), same field, same
ties.

| # | Experiment | Lever | Question | Support | Reject | Fidelity |
| --- | --- | --- | --- | --- | --- | --- |
| **E1** | Instrument unmodified Ripser | none (scoreboard) | Where is the algebraic work on *our* clouds? Apparent rate, cofacet probes, additions, effective \(T\) vs \(R\). | Counters exist and are repeatable (3 runs). | Harness cannot emit counts — stop; do not invent 10×. | exact (parent) |
| **E2** | Edge-collapse ratio via GUDHI oracle | H01 | Is \(n/n_c\) large on typical clouds at the protocol \(T\)? | Median \(n/n_c\ge 10\) on \(\ge\) half the typical (non high-d-noise) set; collapse receipt logged. | Median \(n/n_c<3\) on that set. High-d noise is a *control*, not the median. | exact (theorem + later identity) |
| **E3** | Collapse + **existing** Ripser on the residual sparse matrix | H01 only | Does the residual flag filtration already cut Ripser’s *own* counters by \(\ge 10\times\)? | `n_columns_reduced` and `n_cofacet_probes` drop \(\ge 10\times\) vs E1; \(H_0,H_1\) identity. | Identity fails, **or** counts drop \(<3\times\) after charging collapse time/work. | exact |
| **E4** | Residual implicit enumerator (PITH core contract) | H02 | Must we own implicit-on-\(G\) or is “collapse then stock Ripser sparse” enough? | Cofacet probes \(\le\) E3 and identity vs E3. | Identity fails, or probes do not drop vs E3 — keep stock Ripser as the residual engine. | exact |
| **E5** | Mandatory \(G_T\) / enclosing radius vs dense parent | H03 (+ H06 diagnostic) | Is the parent leaving a dense tail that a CSR \(G_T\) removes at equal \(T\)? | Same \(T\); `n_distances` stored and probes drop \(\ge 5\times\); identity. | Parent already sparse / already at \(R\); \(e/n^2>1/2\). | exact for \(\mathrm{VR}_{\le T}\) |
| **E6** | Apparent / unpaired remainder **after** collapse | H01 × H04 diagnostic (measure only) | Did collapse steal the easy apparent pairs and leave a hard remainder? | Report `n_columns_reduced` / `n_columns_assembled` before vs after collapse. | — (measurement). If remainder **grows** as a fraction, H04 becomes mandatory; if remainder already \(\le 1/10\) of E1, H04 is postponed. | exact (counts only) |
| **E7** | Extra Morse **or** RedZeD **or** reduced VR on the residual \(H_1\) | H04 / H09 / H07 — **pick one**, the winner of E6 | Can the residual unpaired \(H_1\) work drop another \(\ge 3\times\) without breaking identity? | Identity + named counter drop; construction cost charged. | Identity fail, or net work (matching + reduce) \(\ge\) E3. Try the next of {H04, H09, H07} as a **new** experiment, do not stack. | exact (or unverified→stop) |
| **E8** | Same winning exact stack at \(H_2\) | stack frozen from E3–E7 | Does the 10× survive `maxdim=2`? | \(H_0\)–\(H_2\) identity vs Ripser `--dim 2`; \(H_2\) columns/probes \(\ge 10\times\) down **or** honest “\(H_1\) only 10×”. | Identity fail. If only \(H_1\) hit 10×, **do not** claim \(H_2\). | exact |

**Decision rule after E8.**

- If E3 or E3+E7 shows \(\ge 10\times\) drop on `n_columns_reduced` **and**
  `n_cofacet_probes` for \(H_0\)–\(H_1\) with identity, **select** that
  PITH pipeline as the exact-VR CPU candidate (class structural / exact).
- If only edges drop 10× but residual reductions do not, the 10× is
  **real for expansion-based engines** and **not yet** real vs Ripser;
  H02/H04/H09 stay open.
- If nothing drops 10× on typical clouds, the 10× claim is **not
  evidenced** in that neighborhood; retry_when = different \(T\), data
  with boundary, or \(H_2\)-only (E8 may still win).
- H08, H14, H15, H16 never promote a 10×-exact-VR headline.

---

## 6. P0 list

These are the only P0 hypotheses. They are the first wave toward 10×
exact VR vs unmodified Ripser.

| ID | Title | Class | Why P0 |
| --- | --- | --- | --- |
| **H01** | Flag edge collapse | structural / exact | Only published exact lever with documented \(\sim 12\)–\(30\times\) edge cuts. |
| **H02** | Residual-graph implicit cohomology | structural / exact | Makes H01 compatible with a Ripser-class core; otherwise we expand and lose. |
| **H03** | Thresholded sparse 1-skeleton | structural / exact (truncated) | Default exact representation of the filtration we actually run. |
| **H04** | Stronger Morse / chunk on the residual | structural / exact | Only exact attack on the unpaired remainder Ripser already pays. |
| **H05** | \(H_0\)–\(H_1\)-only contract | implementation / API | v1 scoreboard is \(H_0\)–\(H_1\); forbids accidental \(H_2\) work in E1–E7. |

H06–H07–H09–H10 are P1 (stack or reproduce). H08 is P2 until the unit
square is resolved. H11–H16 do not advance the exact-VR 10× headline.

---

## 7. What this file is not

- Not an implementation plan with dates. CPU-first still means: prove
  the peel + implicit core before SIMD or CUDA.
- Not a selected algorithm. Selection requires gates G0–G3
  (`docs/METHODOLOGY.md`) and frozen receipts.
- Not a complexity improvement. No hypothesis here claims a better
  worst-case than matrix reduction.
- Not a license to compare Alpha, sparse Rips, or witness diagrams to
  Ripser by equality.

**Next concrete step (when code is allowed):** E1, instrument pinned
Ripser, write `benchmarks/results/ph-0001/ENTRY.json`. Do not implement
PITH until E1–E2 exist.

---

## 8. Pointers

- Complex recommendation: `docs/COMPLEXES.md` §12–15.
- Framework recommendation: `docs/ALGORITHM_COMPARISON.md` §8–11.
- Must-read papers: `docs/PAPERS.md` (eight-paper list).
- Iteration / classes / gates: `docs/METHODOLOGY.md` §4.
- Process fields: `INSTRUCTIONS.md` §8–9 and CPU-first strategy.
