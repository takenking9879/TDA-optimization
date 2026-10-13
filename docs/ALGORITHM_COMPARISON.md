# Persistent homology frameworks: algorithmic comparison

This note compares existing persistent homology (PH) engines at the level of
**column reduction, pairing shortcuts, (co)homology duality, implicit
representation, sparsification, and parallelism**. It is written as a
research baseline for a CPU-first algorithm that should reduce *algebraic
work* (number of simplices, columns, and column additions), not only
hardware constants.

Sources are the original papers plus the cloned trees recorded in
§[Inspected trees](#inspected-trees). Upstream repositories were cloned
read-only under `/tmp/ph-frameworks` and were not modified.

**Scope.** Vietoris–Rips (VR) is the default comparison complex because it
is the common reference and the combinatorial worst case. Cubical, flag
(directed), Alpha/Čech, and generic cell complexes are included when a
framework contributes a distinct algorithm. Statistical “homology
inference” packages that consume already-computed diagrams are *not*
algebraic engines and are called out separately.

**How to read claims.**

| Class | Meaning |
| --- | --- |
| Exact | Same persistence module as the named filtration (up to field and tie-breaking). |
| Exact after reindexing | Zero-persistence pairs may appear from a simplexwise refinement and are discarded. |
| Approximate with guarantee | e.g. Sheehy sparse Rips, Flagser `--approximate`. |
| Implementation speedup | Same algebra, fewer wall-clock seconds (SIMD, threads, GPU, hash tables). |

---

## 1. Shared algebraic vocabulary

Almost every engine is a variant of **filtration (co)boundary matrix
reduction** (Edelsbrunner–Letscher–Zomorodian; Cohen-Steiner–Edelsbrunner–
Harer). Given a simplexwise refinement of a filtration, the index pairs
are the pivots of a reduced matrix \(R = D V\) with \(V\) invertible and
upper-triangular:

\[
\{(i,j) \mid i = \mathrm{Pivot}(R_j) \neq 0\}.
\]

The differences that matter are *which* matrix is reduced, *which*
columns are never formed, and *how* a column is represented.

### 1.1 Homology vs cohomology

de Silva–Morozov–Vejdemo-Johansson (2011) prove that the barcode of
absolute persistent homology equals that of relative persistent
cohomology (and dually). Computationally this is not a cosmetic duality:

- Homology reduces **boundary** matrices dimension-by-dimension
  *downward* (\(d, d-1, \dots\)) if clearing is used.
- Cohomology reduces **coboundary** matrices *upward* (\(0, 1, \dots\)).

**Clearing / twist** (Chen–Kerber 2011): a birth index that appears as a
pivot need not be reduced, because \(D^2 = 0\) already implies that
column is a cycle. Clearing therefore *skips entire columns*.

Bauer (Ripser, 2021) gives the counting argument that makes the
combination decisive for VR at low degree: a VR \(d\)-skeleton has
\(\binom{n}{d+1}\) simplices, so the coboundary matrix in dimension \(d\)
has far fewer *columns* than the homology boundary matrix in the same
dimension has *rows that must be cleared later*. Cohomology + clearing
together avoid reducing a combinatorial majority of columns. Either
optimization alone does not.

**Consequence.** For VR barcodes, cohomology is the correct default.
Homology is needed only when representative *cycles* (not cocycles) are
required. Involuted PH (Čufar–Virk) recovers cycles from a cohomology
pass without reducing the full homology matrix.

### 1.2 Apparent, shortcut, and emergent pairs

These are nested, not synonyms (Bauer; Zhang–Xiao–Wang):

\[
\text{apparent} \subset \text{shortcut} \subset \text{emergent} \subset \text{all pairs}.
\]

- **Apparent pair** \((\sigma,\tau)\): \(\sigma\) is the *youngest facet*
  of \(\tau\) and \(\tau\) is the *oldest cofacet* of \(\sigma\). The pair
  is a persistence pair of the simplexwise filtration and can be read
  from the (co)boundary matrix *without reduction*. Apparent pairs form a
  discrete gradient (a Morse matching). They are field-independent.
- **Shortcut / zero-persistence pair**: the pair is already visible from
  the *unreduced* coboundary of \(\sigma\) because the youngest cofacet
  has the same filtration value and is unpaired.
- **Emergent pair**: the pair becomes visible *during* reduction, as soon
  as the current pivot has no left-hand column claiming it. Ripser
  aborts coboundary enumeration early when the first cofacet of equal
  diameter is unpaired.

Empirically, apparent pairs are 90–99.9% of VR columns on typical point
clouds (Ripser++ Table 1; Oineus comments). That is a *structural*
reduction: those columns never enter the reduction loop.

Apparent pairs are local and independent, so they parallelize. Emergent
pairs are sequential: they depend on previously installed pivots.

### 1.3 Implicit complexes

A full VR \(d\)-skeleton has \(\Theta(n^{d+1})\) simplices. Storing \(D\)
is often the bottleneck (PHAT project observation; Bauer). Ripser-style
engines therefore store only:

1. the distance matrix (dense lower triangle, or sparse CSR/adjacency);
2. a **combinatorial number system** (binomial coefficient table) that
   bijection \(d\)-simplices \(\leftrightarrow \{0,\dots,\binom{n}{d+1}-1\}\);
3. a coboundary *enumerator* that, given a simplex index, emits cofacet
   indices and diameters by inserting one vertex at a time;
4. the much smaller **reduction matrix** \(V\) (or only a pivot hashmap)
   for columns that actually reduced.

The unreduced coboundary of a column is recomputed on every addition.
This *increases* arithmetic and *decreases* memory traffic. On current
CPUs the trade is a win; it is not a reduction of algebraic rank.

GUDHI’s simplex tree is the opposite design: the complex *is* stored,
\(O(|K|)\) memory, \(O(p^2 D_m)\) facet lookup. That is mandatory for
non-flag complexes and wasteful for dense VR.

### 1.4 Sparsification that changes the complex

| Method | Exact for original VR? | What shrinks |
| --- | --- | --- |
| Edge collapse (Boissonnat–Pritam 2020) | Yes, all degrees | 1-skeleton; residual is still flag |
| Apparent / Morse matching | Yes (pairs of persistence 0 in the refinement) | Columns, not the filtration graph |
| Discrete Morse (Perseus, distilled VR, PHAT chunk) | Yes for the Morse complex; distilled VR proves isomorphism to VR | Critical cells |
| Sheehy sparse Rips | No; \((1+\varepsilon)\)-interleaving | Vertices / edges |
| Witness / landmarks | Different complex | Vertices |
| Alpha / Delaunay | Different complex; homotopy-equivalent to Čech in the ambient metric | Simplices in low ambient dim |
| Enclosing radius | Exact for the *untruncated* VR of a finite metric space | Diameter cutoff |

Edge collapse is the most important *exact* preprocessor for flag
filtrations: domination is a 1-skeleton test
(\(N[e] \subseteq N[v']\)), so higher simplices are never built.

---

## 2. Required frameworks

### 2.1 Ripser

- Repo: https://github.com/Ripser/ripser
- Inspected SHA: `01add51ff64aaf40889483260cc5c3b7d0f2a1e7` (2023-06-19)
- Paper: Bauer, *J. Appl. Comput. Topol.* 2021; arXiv:1908.02518
- License: MIT
- Language: ~1000 lines of C++11 in one file (`ripser.cpp`)

**Column reduction / pairing.** Implicit reduction of the *coboundary*
matrix of the lexicographically refined VR filtration. Columns are
processed left-to-right. The working column is a heap of
`(diameter, index, coefficient)` entries; cancellation is XOR / modular
addition of equal indices. Only the reduction matrix \(V\) (compressed
sparse columns) and a pivot hashmap are retained. Apparent pivots are
*not* stored: they are recomputed by `get_zero_apparent_facet`.

**Apparent / emergent / clearing.**

- `get_zero_apparent_facet` / `get_zero_apparent_cofacet` implement the
  local youngest-facet / oldest-cofacet test for *zero-persistence*
  apparent pairs of the diameter filtration.
- `init_coboundary_and_get_pivot` stops coboundary enumeration at the
  first same-diameter cofacet that is not itself in an apparent pair
  (emergent / shortcut pair).
- `assemble_columns_to_reduce` drops every simplex that is already a
  pivot (clearing) or that sits in an apparent pair.
- Dimension 0 is union-find, not matrix reduction.

**Homology vs cohomology.** Persistent *cohomology* only. Barcodes match
homology. Representative *cycles* are not computed (a separate
representative-cycles branch exists upstream and is noted in GUDHI’s
port).

**Implicit representation.** Combinatorial number system + binomial
table; dense lower-triangle or sparse neighbor lists; cofacets generated
by inserting a vertex \(j\) and updating
`idx_above + C(j, k+1) + idx_below`. The full complex is never stored.
If no threshold is given, the **enclosing radius** (Henselman) is used:
homology is trivial beyond that diameter.

**Sparsification.** None beyond enclosing radius and optional sparse
distance input. No edge collapse, no Morse preprocessor.

**CPU / SIMD / threads / GPU.** Sequential CPU. No SIMD intrinsics, no
threads, no GPU. Optional `USE_ROBINHOOD_HASHMAP` is a constant-factor
memory/time tweak.

**What parallelizes.** Nothing in the reduction loop. Apparent-pair
*tests* are independent and *could* be parallel, but are not.

**Memory / communication.** Peak memory is the distance matrix
(\(O(n^2)\) dense or \(O(e)\) sparse) plus \(V\) for non-apparent
columns plus the pivot map. No communication.

**Exactness.** Exact barcode of the VR filtration over \(\mathbb{F}_p\)
(`USE_COEFFICIENTS`) or \(\mathbb{F}_2\). Tie-breaking is the reverse
colexicographic vertex order of the paper. Finite-precision distances
are used as given.

**Combinable.** Apparent + emergent + clearing + implicit cohomology is
the reference combination. Compatible with a *prior* edge collapse
(done by others). Compatible with lock-free out-of-order reduction
(giotto-ph, Oineus) and with a GPU apparent scan (Ripser++).

**Maintenance / compile.** Extremely easy: `make`, C++11, no required
dependencies. Last functional commit June 2023 (binomial table layout).
The algorithm is stable; the repo is intentionally minimal. Live demo
at live.ripser.org (Emscripten).

**Valuable even if not the whole base.** The implicit coboundary
enumerator, the cohomology+clearing counting argument, apparent pairs as
a discrete gradient, and the enclosing-radius cutoff. This is the
smallest correct kernel to modify.

---

### 2.2 Ripser++

- Repo: https://github.com/simonzhang00/ripser-plusplus
- Inspected SHA: `30243c0c752de26d7fdf6e41f08bf7b840ca4744` (2023-03-16)
- Paper: Zhang–Xiao–Wang, SoCG 2020; arXiv:2003.07989
- License: MIT (Ripser-derived)
- Language: CUDA + C++, Python bindings

**Column reduction / pairing.** Same implicit cohomology algorithm as
Ripser for the *remainder*. The new split is:

1. GPU: construct the cleared filtration and find apparent pairs
   (`coboundary_findapparent_*_kernel`).
2. CPU: sequential heap reduction of the non-apparent columns, with
   apparent pivots pre-inserted so the CPU never materializes those
   columns.

**Apparent / emergent / clearing.** Apparent pairs are lifted out of the
reduction loop and scanned independently per column (Apparent Pairs
Lemma / Corollary 1 of the paper). Emergent pairs that are *not*
apparent still require the sequential CPU loop. Clearing is applied
while assembling columns on the GPU.

**Homology vs cohomology.** Cohomology, as in Ripser.

**Implicit representation.** Same combinatorial number system, now with
device-side binomial tables and a dense or CSR distance matrix on the
GPU. The CPU no longer holds the full set of columns-to-reduce
diameters for apparent columns (paper: up to 2× less CPU RAM).

**Sparsification.** None beyond Ripser’s.

**CPU / SIMD / threads / GPU.** GPU SIMT for filtration + apparent scan.
CPU single-thread for the remaining reduction. No SIMD in the CPU
remainder. Requires a CUDA device; device RAM is the hard limit.

**What parallelizes vs stays sequential.**

| Stage | Where | Parallel? |
| --- | --- | --- |
| Distance / diameter assignment | GPU | Yes |
| Clearing / assemble columns | GPU | Yes |
| Apparent-pair test | GPU, one thread per column | Yes, embarrassingly |
| Emergent pairs and column addition | CPU | No |
| Pivot hashmap updates | CPU | No |

The paper’s “separation of parallelisms” (also HYPHA, ICS 2019) is the
right architectural cut: *independent local tests* go to the GPU;
*left-to-right column additions* stay sequential.

**Memory / communication.** Must fit the distance matrix and the
columns-to-reduce arrays on the device. Host↔device copies of
non-apparent columns and pivots. No multi-node communication.

**Exactness.** Same as Ripser (exact VR barcode). Apparent-pair
identification is exact, not heuristic.

**Combinable.** Compatible with a CPU edge-collapse preprocessor (not
implemented). Incompatible as a *kernel* with lock-free CPU reduction of
the remainder (would need a different remainder). Does not help if the
remainder is large (high-dimensional, or data with few apparent pairs).

**Maintenance / compile.** Needs CUDA toolkit, CMake, Python. Last
upstream merge March 2023. Harder to compile than Ripser; easy if a
matching CUDA stack exists. Without a GPU it is not a baseline.

**Valuable even if not the base.** (1) Apparent pairs are the GPU-shaped
part of PH. (2) Do not GPU-ize the sequential remainder first.
(3) Bounds on apparent-pair *rate* (paper) tell you when the split
pays off. Keep as the GPU *reference*, not as the CPU kernel.

---

### 2.3 giotto-ph

- Repo: https://github.com/giotto-ai/giotto-ph
- Inspected SHA: `21397fcefe2164f3f95f2c34ed494d7946e31998` (2024-05-30, v0.2.4)
- Paper: Burella Pérez–Hauke–Lupo–Caorsi–Dassatti, arXiv:2107.05412
- License: **GNU AGPL-3.0** (L2F SA; commercial relicensing offered)
- Language: C++ backend, Python API (`gph.ripser_parallel`)

**Column reduction / pairing.** Lock-free shared-memory reduction of
Ripser’s implicit coboundary, from Morozov–Nigmetov (SPAA 2020) plus
Ripser v1.2 apparent pairs. The pairing-uniqueness lemma
(Cohen-Steiner et al.) says any left-to-right addition order is valid.
Columns may therefore be reduced *out of filtration order*. If a thread
sees a pivot to its *right*, it retires the column and lets the other
thread finish; if the pivot is to the left, it adds as usual. The pivot
table is a concurrent hashmap with a CAS retry on the stored entry
(`ripser.h` around the `old_entry_column_to_add` loop). The comment in
source notes this is a *weaker* check than the original lock-free paper
(they store \(V\), not \(R\)).

**Apparent / emergent / clearing.** Parallel apparent-pair search *and*
the sequential-style emergent-pair abort inside `init_coboundary`.
Clearing as in Ripser. This is the first widely distributed package that
combines lock-free reduction + parallel apparent pairs + edge collapse.

**Homology vs cohomology.** Cohomology. Optional `return_generators`
exposes simplex pairs / essential simplices; mutually exclusive with
`collapse_edges`.

**Implicit representation.** Ripser-style. Extra: lock-free hash map and
an epoch-based `MemoryManager` (`gph/inc/common/`) so retired columns
can be reclaimed without stopping the world.

**Sparsification.** Rewritten GUDHI `Flag_complex_edge_collapser`
(`gph/src/Flag_complex_edge_collapser.h`): fewer dependencies, claimed
faster than GUDHI’s original. Collapse is a preprocessor: it shrinks the
flag 1-skeleton, then Ripser-style cohomology runs on the residual.
Also DTM-weighted VR.

**CPU / SIMD / threads / GPU.** Multicore CPU. No SIMD, no GPU. Apparent
search and column reduction both take `n_threads`. Paper claims the
backend beats Ripser++ at 5–10 CPU cores on their suite.

**What parallelizes vs stays sequential.**

| Stage | Parallel? |
| --- | --- |
| Distance matrix (sklearn/scipy) | Yes (`n_jobs`) |
| Edge collapse | Largely sequential graph walk (some neighbor tests independent) |
| Apparent-pair search | Yes |
| Column reduction | Yes, lock-free; additions still left-to-right |
| A single column’s heap reduction | Sequential on its thread |

**Memory / communication.** Shared-memory atomics only. Same
\(O(n^2)\) distance matrix as Ripser, plus per-thread working columns
and a concurrent pivot map. No cluster path.

**Exactness.** Exact VR (or collapsed flag) barcode over prime fields.
Edge collapse is exact for the original flag filtration
(Boissonnat–Pritam). Lock-free reordering does not change pairs.

**Combinable.** This *is* the combination of the best CPU techniques for
VR. The license is the blocker, not the algebra.

**Maintenance / compile.** CMake + setuptools, C++14-ish, OpenMP-style
parallelism, Python. Moderate. Last release May 2024. AGPL makes it
unsuitable as a code base for an MIT project.

**Valuable even if not the base.** (1) Lock-free out-of-order reduction
is the right CPU parallelization of the *remainder*. (2) Parallel
apparent search. (3) Edge collapse as a default preprocessor, with the
empirical caveat that it does not always pay. Reimplement these ideas;
do not copy the tree.

---

### 2.4 GUDHI

- Repo: https://github.com/GUDHI/gudhi-devel
- Inspected SHA: `1c4ba125edf2822f823fb6669cfac067dafd10d7` (2026-10-12)
- Papers: simplex tree (Boissonnat–Maria, Algorithmica 2014); compressed
  annotation matrix (Boissonnat–Dey–Maria, arXiv:1304.6813); edge
  collapse (Boissonnat–Pritam, SoCG 2020); plus a maintained Ripser
  port (`src/Ripser/include/gudhi/ripser.h`, based on Ripser
  `140670f2`)
- License: MIT (individual modules may carry extra copyright headers)
- Language: C++ / Python, CMake, Boost; CGAL for Alpha/Čech

GUDHI is a *toolbox*, not one algorithm. Three PH engines live in it.

#### 2.4.1 Persistent cohomology + compressed annotation matrix (CAM)

This is the classical GUDHI path (`Persistent_cohomology.h`).

**Column reduction / pairing.** Not Ripser-style implicit \(R=DV\).
Simplices are inserted in filtration order. Each simplex carries an
*annotation* (a sparse cohomology class). Inserting \(\sigma\):

- if the annotation of \(\partial\sigma\) is zero → \(\sigma\) creates a
  cocycle;
- otherwise the youngest nonzero annotation is destroyed (pairing).

CAM stores *distinct* annotation vectors once and points many simplices
at the same vector (union-find / dictionary). Time and memory track the
size of the *cohomology* being maintained, linearly in \(|K|\).

**Apparent / emergent / clearing.** Not present on this path. Pairing is
the annotation update itself.

**Homology vs cohomology.** Cohomology. Also **multi-field PH**:
`init_coefficients(pmin, pmax)` computes several \(\mathbb{Z}/p\)
barcodes in one pass (Maria–Boissonnat–Glisse–et al.). That is the “MPH”
in the GUDHI sense (multi-field, not multiparameter).

**Representation.** The **simplex tree** stores every simplex
explicitly, \(O(|K|)\) pointers. Facets are recovered by walking the
tree. This is the right structure for Alpha, Witness, Čech, and custom
complexes. For dense VR it is the reason GUDHI historically lost to
Ripser by large factors.

**Sparsification.** `collapse_edges` / `flag_complex_collapse_edges`
implements Boissonnat–Pritam on the 1-skeleton. The residual graph is
expanded (`expansion(d)`) and then CAM (or the Ripser port) is run.
Alpha complex uses Delaunay (CGAL) and is exact for the Čech homotopy
type in Euclidean space. Witness / strong witness reduce vertices.

**CPU / SIMD / threads / GPU.** Mostly sequential. Some construction
(Delaunay, edge collapse neighbor scans) can use TBB/OpenMP depending
on build flags. No GPU PH. No SIMD in CAM.

**Memory.** Simplex tree + CAM. Communication: none.

**Exactness.** Exact for the stored filtered complex, over \(\mathbb{Z}/p\)
with \(p \le 46337\) in the Python API. Multi-field is exact for each
field.

#### 2.4.2 Persistence matrix module

A PHAT-like reduction engine with interchangeable column representations
and homology *or* cohomology. Used when the user already has a boundary
matrix (or wants representative cycles, vineyards-style updates). This
is the modern “generic reduction” path inside GUDHI.

#### 2.4.3 Ripser port

`gudhi/ripser.h` is a refactored Ripser with the same apparent /
emergent / clearing / implicit cohomology algorithm, plus notes toward
representative (co)cycles and involuted homology. This is the VR path
GUDHI now recommends when the complex is flag.

**Combinable.** Edge collapse → Ripser port is the correct GUDHI VR
pipeline. CAM + simplex tree is the correct pipeline for non-flag
complexes. Do not run CAM on an uncollapsed dense VR.

**Maintenance / compile.** Very active (inspected commit is dated
2026-10-12). Compile is the hardest of the MIT C++ options: CMake,
Boost, optional CGAL/Eigen/TBB, Python. Worth it as a *library*, not as
a kernel to fork.

**Valuable even if not the base.** Simplex tree; CAM (when \(|H^*|\) is
tiny relative to \(|K|\)); edge collapse implementation; Alpha/Witness;
multi-field; zigzag (separate module); the fact that GUDHI now *contains*
Ripser rather than competing with it.

---

### 2.5 Oineus

- Repo: https://github.com/anigmetov/oineus
- Inspected SHA: `e52814a1ffb5b8a81e71ff1e93b4c14194673f0f` (2026-10-02, v0.9.39)
- Papers: Morozov–Nigmetov, SPAA 2020 (lock-free); Nigmetov–Morozov,
  arXiv:2203.16748 (critical sets / topological optimization);
  Vejdemo-Johansson–Matuszewski–Bauer, arXiv:2411.05495 (in-order VR
  generation)
- License: **modified BSD** (LBNL / UC / DOE). Enhancement-grant-back
  clause if you publish enhancements without a separate agreement.
- Language: C++20, Taskflow, nanobind, vendored Eigen/Hera

**Column reduction / pairing.** Generic shared-memory lock-free
reduction of an *explicit* (or on-the-fly generated) (co)boundary
matrix. Dualize flag selects cohomology. Column representations are
PHAT-style: Set, Heap, Full, BitTree. Clearing optional
(`use_clearing`). Can restore \(U\) from \(V\) after clearing
(`restore_elz`) for representative / optimization work.

**Apparent / emergent / clearing.** First-class `ApparentMatching`
(`include/oineus/apparent.h`). Detectors:

- `detect_apparent_generic` — first-column-to-contain-the-low test;
- `detect_apparent_local` — Bauer local test (youngest facet / oldest
  cofacet), **parallel over cells**, no atomics on the matching because
  each facet has at most one apparent cofacet;
- bruteforce oracle for tests.

Apparent columns are not materialized; a resolver hook rebuilds an
apparent \(R\) column on demand. Comments in-tree state the expected
90–99% skip rate for VR / cubical / Freudenthal.

**Homology vs cohomology.** Both. `dualize=true` is cohomology.
Kernel / image / cokernel persistence (mapping cylinder helper) is
unique among the required six.

**Representation.** Not Ripser-implicit for general filtrations: cells
are created (lower-star grid, Freudenthal triangulation of a grid, or
user simplices). VR uses **in-order generation** so simplices appear
already sorted, avoiding a huge sort. Cubical / Freudenthal cells use
packed `(anchor, type)` encodings with direct `boundary_into` /
`coboundary_into`.

**Sparsification.** Apparent matching is a Morse matching. No
Boissonnat–Pritam edge collapse. Critical-set method is for
*optimization* of a filter, not for shrinking a VR complex.

**CPU / SIMD / threads / GPU.** Multicore via Taskflow. No SIMD, no GPU.
C++20 required. No OpenMP/TBB system dependency (Taskflow is vendored).

**What parallelizes vs stays sequential.** Apparent local detection:
parallel, independent. Lock-free column reduction: parallel with CAS.
A single column: sequential. Filtration construction: parallelizable
per-cell for grids; VR generation is more serial. Vineyard /
transposition updates: sequential by nature.

**Memory / communication.** Explicit matrix for general complexes (the
PHAT problem). Apparent skip is the mitigation. Shared memory only.

**Exactness.** Exact over the chosen field. Apparent pairs
field-independent. Clearing + `restore_elz` is tested to reproduce \(U\).

**Combinable.** Lock-free + apparent + clearing + dualize is the right
generic-complex combination. Compatible in principle with an external
edge collapse feeding a VR filtration. Vineyards / dynamic updates are
incompatible with throwing away \(V\).

**Maintenance / compile.** Actively maintained (2026). CMake + Boost +
C++20; other deps vendored. Harder than Ripser, easier than full GUDHI
with CGAL. Python wheels on PyPI.

**Valuable even if not the VR base.** (1) Lock-free reduction as a
*generic* engine, not glued to Ripser’s implicit matrix. (2) Parallel
local apparent detection with a proven no-conflict write scheme.
(3) In-order VR generation. (4) Kernel/image/cokernel and differentiable
filtrations, if the project later cares about optimization. (5) Bit-tree
columns from PHAT, independently useful.

---

### 2.6 Ripserer.jl

- Repo: https://github.com/mtsch/Ripserer.jl
- Inspected SHA: `9def962dbc2a0bc9798509bdb15cc7002944a400` (2026-06-29)
- Paper: Čufar, JOSS 2020; involuted PH: Čufar–Virk, arXiv:2105.03629
- License: MIT
- Language: pure Julia

**Column reduction / pairing.** Generic Ripser: `CoboundaryMatrix` or
`BoundaryMatrix`, each with an `implicit` type parameter. Default
`alg=:cohomology` is implicit coboundary reduction with emergent-pair
abort in `initialize_coboundary!`. `alg=:homology` is significantly
slower and does not report infinite intervals above dimension 0.
`alg=:involuted` runs cohomology first, then reduces *only the death
simplices* as homology columns to recover representative cycles.

**Apparent / emergent / clearing.** Emergent pairs on by default for any
filtration that can emit (co)facets in the correct order
(`emergent_pairs(::Filtration) = true`). `find_apparent_pairs` is an
overridable hook; the default is a no-op because apparent pairs are
already discovered during coboundary init. A pre-pass (PR #93) exists
for Ripser++-style bulk insertion; comments say it is slower on CPU
unless the pre-pass is itself parallel/GPU.

Clearing is implicit in `columns_to_reduce` / `to_skip`.

**Homology vs cohomology.** All three modes, which is the unique
pedagogical and representative-cycle contribution.

**Implicit representation.** Filtration interface: `dist`, `threshold`,
`coboundary`, `boundary`, `simplex_type`. VR uses combinatorial indices
as in Ripser. Custom complexes (cubical, Alpha via other packages,
user types) plug in without storing a global boundary matrix if they
implement the iterators.

**Sparsification.** `EdgeCollapsedRips` — Boissonnat–Pritam on the
1-skeleton, then ordinary Ripserer. Documented to help most on data
*with boundary* and in high degree.

**CPU / SIMD / threads / GPU.** Sequential Julia. Julia can SIMD some
loops automatically; there is no hand-written SIMD PH kernel and no GPU
path. The apparent-pair hook is the intended GPU extension point.

**What parallelizes.** Complex construction and user-level `Threads.@threads`
around *independent datasets*. The reduction is sequential. Apparent
pre-pass *could* be parallel (not default).

**Memory / communication.** Same class as Ripser. Julia GC is an extra
constant-factor risk.

**Exactness.** Exact over `Mod{p}` / `Bool`. Involuted cycles match
homology representatives of the same filtration.

**Combinable.** Edge collapse + implicit cohomology + involuted
representatives is the cleanest *experimental* stack. Apparent pre-pass
+ GPU is designed but not production.

**Maintenance / compile.** Active (2026). `Pkg.add("Ripserer")` is easy
*if* Julia is acceptable. Wrong language for a C++/CUDA kernel, right
language for trying filtrations.

**Valuable even if not the base.** (1) Involuted PH — the correct way to
get cycles without paying full homology. (2) Filtration interface that
makes emergent-pair correctness an explicit contract. (3) Edge collapse
as a first-class filtration type. (4) Proof that apparent *pre-pass* on
CPU is usually wasted work.

---

## 3. Additional frameworks with unique algorithms

### 3.1 PHAT — reduction as a laboratory

- https://github.com/blazs/phat — SHA
  `ca9dc645221dcdf42ecf7bb171983b6a819a468d` (2018-06-09)
- License: **LGPL-3.0**
- Paper: Bauer–Kerber–Reininghaus–Wagner, JSC 2017

PHAT does **not** build a complex. It reduces an already-ordered
\(\mathbb{F}_2\) boundary matrix and is the cleanest comparison of
*reduction strategies*:

| Algorithm | Idea | Parallel? |
| --- | --- | --- |
| `standard` | Left-to-right full column reduction | No |
| `twist` (default) | Clearing by decreasing dimension | No |
| `row` / pHrow | Right-to-left row algorithm | No |
| `chunk` | Reduce two block-diagonals, delete local pairs (generalized discrete Morse), twist the rest | First two steps yes |
| `spectral_sequence` | Independent blocks on a diagonal (Edelsbrunner–Harer) | Yes, OpenMP |

Column stores: `vector`, `heap`, `full`, `sparse`, `bit_tree` (default).
`bit_tree` is a 64-ary dense bitset with \(O(1)\)-ish maximum and fast
iteration — a constant-factor structure, not less algebra.

**Unique idea.** The **chunk** algorithm is Morse theory in matrix form:
eliminate *local* persistence pairs (not necessarily incident) and
reduce a much smaller residual. That *does* cut algebraic work. Spectral
sequence parallelizes but often scales poorly (fine-grained
synchronization, fill-in).

**Status.** Essentially frozen (2018). Still the right citation for
column data structures and for “parallelize the *matrix*, not the
point cloud.”

### 3.2 DIPHA — distributed global PH

- https://github.com/DIPHA/dipha — SHA
  `0b874769fbd092c07a12cebc2459adb02117c2fd` (2017-05-25)
- License: **LGPL-3.0**
- Paper: Bauer–Kerber–Reininghaus, ALENEX 2014

MPI implementation of *one global* reduction. Inputs: lower-star cubical
images, (sparse) VR distance matrices, or explicit (co)boundary
matrices. Uses dualization, clearing, and PHAT column structures.

**What is distributed.** Columns of the global matrix live on ranks.
Each rank reduces its slice, then **communicates pivots / unreduced
columns** along the spectral / chunk schedule. This is *not* “PH on
each subset of points.” Correctness is global; communication is the
tax.

**Limits.** Memory per rank can still be large (historical complaint vs
Ripser). VR construction is not implicit-Ripser-class. Unmaintained
since 2017. Useful as the existence proof that global PH *can* be
distributed, and as a warning that partition-by-points is a different
(generally incorrect) algorithm.

Later “distributed PH” papers (e.g. PixHomology / Sparksistence,
arXiv:2404.08245) mostly distribute *many images* or \(H_0\) of 2-D
images — not general VR \(H_*\).

### 3.3 Dionysus 2 — vineyards, zigzag, omni-field

- https://github.com/mrzv/dionysus — SHA
  `a1703fe977f85540fa05b56e59192ba936173779` (2026-09-02)
- License: modified BSD (LBNL)
- Docs: https://mrzv.org/software/dionysus2/

Historically the first widely used **dual / cohomology** implementation.
Today it is not a VR speed contender (explicit filtration). It is the
reference for:

- **vineyards** — maintain \(R=DV\) (or \(U\)-trails) under adjacent
  transpositions of the simplex order;
- **zigzag** and apex representatives (Mayer–Vietoris pyramid);
- **omni-field** persistence (one reduction, all primes);
- circular coordinates from cocycles.

**Unique idea.** If the research question is *dynamic* filtrations,
Dionysus’s vineyard update is the algorithm; Ripser-style implicit
matrices fight you because they throw \(R\) away.

### 3.4 CubicalRipser — implicit cohomology on grids

- https://github.com/shizuo-kaji/CubicalRipser (clone of
  CubicalRipser_3dim) — SHA
  `12b7693948f04ea405be68ad4bca460e41b1ea00` (2026-10-08)
- Paper: Kaji–Sudo–Ahara, arXiv:2005.12692
- License of inspected tree: **GPL-3.0** (older `cripser` wheels were
  advertised as MIT; do not assume MIT without re-checking the tree you
  vendor)

Ripser’s implicit coboundary reduction specialized to weighted cubical
complexes (1-D–4-D). Extra structure:

- cubes indexed by location + type, not binomial numbers;
- \(H_0\) by **union-find**;
- **Alexander duality** for the top dimension (`--top_dim`, `--embedded`):
  \(H_{d-1}\) of a \(d\)-D image from dual union-find / dual filtration
  (Garin et al., duality of images);
- V-construction (pixels as 0-cells) and T-construction (pixels as
  top-cells);
- apparent-pair abort in `compute_pairs.cpp`;
- \(\mathbb{F}_2\) only.

**Unique idea.** On images, duality + union-find *removes* a full
cohomology pass. That is an algebraic-work reduction specific to
cubical duality, not portable to VR.

Related: GUDHI bitmap cubical complex (any dimension, CAM or persistence
matrix); DIPHA lower-star images (distributed); ripser.py lower-star
images (Ripser on a cubical 1-skeleton encoded as a sparse distance
matrix — a hack, not a cubical engine); Diamorse (discrete Morse on
images).

There is **no** `github.com/Ripser/ripser-image` repository. The
practical “Ripser for images” engines are CubicalRipser, GUDHI cubical,
and ripser.py’s lower-star wrapper.

### 3.5 flagser — directed flag complexes + approximation

- https://github.com/luetge/flagser — SHA
  `6763e964bc69c5bce3ed57491ea6dcd6e934d46b` (2026-04-21)
- Paper: Lütgehetmann–Govc–Smith–Levi, arXiv:1906.10458
- License: MIT (Ripser-derived; extra CONTRIBUTING clause)

Ripser-style cohomology on the **directed flag complex** of a directed
graph (cliques = directed complete subgraphs). Unique points:

- construction of the directed flag complex is **vertex-parallel**;
- coboundaries are often *precomputed and stored* for large complexes
  (`--in-memory`), the opposite of Ripser’s recompute-from-index
  choice, because directed cofacets are less regular;
- **`--approximate`**: stop reduction early and accept a user-bounded
  error on Betti / persistence — the only production engine that
  officially trades exactness for less algebra;
- odd-characteristic coefficients;
- **apparent pairs do not apply** in the same way: there is no
  consistent “youngest facet / oldest cofacet” shortcut once directions
  break the VR diameter order.

**Unique idea.** (1) Directed flag is a different complex, not a
faster VR. (2) Controlled approximation inside reduction. (3) When the
complex is irregular, *storing* coboundaries can beat implicit
recomputation.

### 3.6 Eirene.jl — matroids, Morse, Schur complements

- https://github.com/Eetion/Eirene.jl — SHA
  `16622d0aa1d7237895919e7fbdc1e8a6196425ab` (2025-01-28)
- Paper: Henselman–Ghrist, arXiv:1606.00199
- License: **GPL-3.0**

Not a Ripser clone. Persistent homology is computed via **matroid
filtrations**: discrete Morse simplification + Schur complements /
pivoting so that large parts of the boundary matrix are never stored.
Apparent pairs appear here as “minimal pairs of a linear order”
(Henselman thesis), independently of Bauer.

Historically Eirene was the memory champion on some large VR instances
and the reference for **cycle representatives**. Ripser later won raw
barcode time. Eirene remains the conceptual source for:

- Morse-theoretic avoidance of \(D\);
- the Schur-complement view of reduction (reused in the 2025
  “PH in matrix-multiplication time” line, SoCG 2025);
- enclosing radius (adopted by Ripser).

Harder to build on (Julia, GPL, idiosyncratic API). Steal the
*matroid / Schur / Morse* vocabulary, not the repo.

### 3.7 Perseus — Morse reduction of arbitrary filtrations

- Site: https://people.maths.ox.ac.uk/nanda/perseus/
- Paper: Mischaikow–Nanda, DCG 2013 (*Morse theory for filtrations*)
- No official maintained GitHub clone found in this pass

Perseus builds a discrete gradient on *any* filtered cell complex
(cubical, simplicial, VR, Morse complexes from images), collapses
pairs, and only then reduces the critical-cell boundary matrix.

**Unique idea.** Morse reduction as a **filtration-preserving
preprocessor** independent of VR tricks. PHAT’s chunk algorithm is the
linear-algebra analogue. Distilled Vietoris–Rips (below) is a 2024
VR-specific descendant.

### 3.8 JavaPlex — dual, zigzag, pedagogy

- https://github.com/appliedtopology/javaplex — SHA
  `05a288a4a99f27242d8f4b24e98d4cce749fb71a` (2019-12-22)
- License: BSD-3-Clause

Java port of the Plex lineage. Algorithms: standard reduction, dual
(cohomology), zigzag. Explicit complexes, JVM memory model, no implicit
VR, no apparent pairs. Frozen. Useful only as a historical dual/zigzag
reference and for reading the original Plex algorithm names.

### 3.9 Distilled Vietoris–Rips (2024) — Morse on reduced VR

- Paper: arXiv:2412.07805
- No production library cloned

Constructs a discrete Morse vector field on the *reduced* VR filtration
and proves the distilled filtration has **isomorphic PH** to standard
VR (the writeup emphasizes degree 1). Boundary-matrix construction and
reduction of the distilled complex are designed to be highly parallel
and memory-light. This is one of the few *recent* proposals that aims
at less algebra, not a faster kernel of the same matrix.

Treat as a candidate technique, not as a baseline implementation.

### 3.10 Lock-free Ripser forks and HYPHA / OpenPH

| Artifact | SHA / date | Unique point | License |
| --- | --- | --- | --- |
| ArGintum/PersistenceHomology | `b0cf2e70` (2021-08-01) | Lock-free Ripser + optional edge collapse; **no apparent pairs**; TBB | Unclear / academic |
| mrzv/ripser `lockfree` branch | cited by giotto-ph | Original lock-free Ripser (v1.1 era) | MIT-derived |
| HYPHA (Zhang et al., ICS 2019) | — | GPU SIMT *scan* for stable/leftmost columns; CPU does clearing + additions | — |
| OpenPH (pms) | — | CUDA parallel matrix reduction with a pivot set; fixed slots per column (memory hazard) | — |

giotto-ph is the maintained descendant of the lock-free Ripser line.
HYPHA/OpenPH confirm the same cut as Ripser++: scan-type work is
GPU-shaped; fill-in column addition is not.

### 3.11 Multiparameter PH and multi-field PH (“MPH”)

Two different “MPH”s appear in the literature:

1. **Multi-field** (GUDHI CAM): one complex, many primes, one pass.
   Algebraic work is shared across fields; output is a family of ordinary
   barcodes. Relevant if coefficient sensitivity matters.
2. **Multiparameter persistence** (`multipers`, DavidLapous/multipers;
   GUDHI SimplexTreeMulti; CuMPerLay/CMP for cubical 2-parameter on
   CUDA). The module is *not* interval-decomposable in general.
   Algorithms compute approximations (MMA), signed measures, or
   fibered barcodes — a different problem. Do not use these as a
   1-parameter VR baseline.

### 3.12 HomologyInference

No maintained *algebraic* engine under this name was found. Hits are
statistical inference on already-computed diagrams (`inphr`,
`TDAInference` / `universal_null`, TDAstats). Those filter bars; they
do not reduce \(D\). Out of scope for a PH kernel.

---

## 4. Cross-cutting comparison

### 4.1 Pairing and reduction

| Engine | Matrix | Order | Clearing | Apparent | Emergent | Extra |
| --- | --- | --- | --- | --- | --- | --- |
| Ripser | Implicit coboundary | Sequential L→R | Yes (upward) | Zero-persistence local | Yes, abort enumerate | Pivot hashmap |
| Ripser++ | Implicit coboundary | GPU scan then CPU L→R | Yes | Massively parallel | CPU remainder | — |
| giotto-ph | Implicit coboundary | Lock-free out-of-order | Yes | Parallel | Yes | CAS pivot map |
| GUDHI CAM | Annotations | Insert-order | n/a | No | No | Multi-field |
| GUDHI Ripser port | Implicit coboundary | Sequential L→R | Yes | Yes | Yes | Library form |
| Oineus | Explicit / generated (co)boundary | Lock-free | Optional | Parallel local matching | Via matching | BitTree, \(U\) restore |
| Ripserer | Implicit co/boundary | Sequential | Yes | Hook / during init | Default | Involuted |
| PHAT twist | Explicit boundary | Sequential, dim ↓ | Yes | No | No | bit_tree |
| PHAT chunk | Explicit | Local then twist | Yes | Local pairs (Morse-like) | No | Residual shrinks |
| DIPHA | Explicit, distributed | MPI schedule | Yes | No | No | Dualize |
| CubicalRipser | Implicit cubical coboundary | Sequential | Yes | Yes | Yes | UF + Alexander |
| flagser | Flag coboundary (often stored) | Sequential / approx | Yes | No (directed) | Limited | `--approximate` |
| Eirene | Morse + Schur | Custom | Morse | Minimal pairs | — | Representatives |
| Perseus | Morse then standard | Sequential | Morse first | Gradient pairs | — | Any complex |
| Dionysus | Explicit | Sequential / vineyard | Dual option | No | No | Zigzag, omni-field |

### 4.2 Complex representation

| Engine | Stores \(\|K\|\)? | How cofaces appear |
| --- | --- | --- |
| Ripser, Ripser++, giotto-ph, Ripserer VR, GUDHI Ripser | No | Combinatorial number system + distances |
| GUDHI CAM / simplex tree | Yes | Tree walk |
| Oineus VR | Generated in order, not a tree | In-order generator |
| Oineus grids | Packed cell ids | Closed-form facets |
| PHAT / DIPHA generic | Input matrix | Precomputed |
| flagser `--in-memory` | Yes | Stored coboundaries |
| CubicalRipser | No | Location+type arithmetic |
| Eirene | Avoids full \(D\) via Morse/Schur | Oracles |

### 4.3 Parallelism vs sequential remainder

The reduction of a column that *needs* additions is a sequential
left-to-right walk in the current pivot table. Every serious parallel
engine respects this:

```
independent:   distances, cofacet enum (per simplex), apparent tests,
               Morse / edge-collapse local checks, block-diagonal chunks
sequential:    column addition, emergent pairing, vineyard swaps,
               global pivot uniqueness
mixed:         lock-free remainder (parallel columns, serial additions
               per conflict), DIPHA (parallel ranks + MPI of pivots)
```

No inspected engine uses hand-written SIMD in the reduction kernel.
Hash maps, heaps, and bit-trees dominate. SIMD would help dense
distance construction and possibly heap/bitset words; it will not
change pivot count.

### 4.4 Exactness

All Ripser-line VR engines, GUDHI, Oineus, Ripserer, PHAT, DIPHA,
CubicalRipser (F2), Dionysus, Eirene, and Perseus are **exact** for
their declared filtration and field, up to floating-point input and
tie-breaking.

Approximate *by design*: Sheehy sparse Rips, Flagser `--approximate`,
witness complexes, and every multiparameter *approximation* (MMA).

Edge collapse, apparent pairs, clearing, lock-free reordering, involuted
PH, distilled VR (claimed), and Alexander duality on images are exact
transforms.

### 4.5 Hardware and compile difficulty

| Engine | Hardware | Compile | Maintenance |
| --- | --- | --- | --- |
| Ripser | CPU 1 core | Trivial (`make`, C++11) | Stable, minimal |
| Ripser++ | CUDA GPU + CPU | CUDA + CMake + Python | Quiet since 2023 |
| giotto-ph | CPU many cores | CMake / pip, moderate | 2024 release |
| GUDHI | CPU | Hard (Boost, optional CGAL) | Very active |
| Oineus | CPU many cores | C++20 + Boost + CMake | Active 2026 |
| Ripserer | CPU 1 core (Julia) | Easy in Julia | Active 2026 |
| PHAT | CPU, optional OpenMP | Easy C++ | Frozen 2018 |
| DIPHA | MPI cluster | MPI + CMake | Frozen 2017 |
| CubicalRipser | CPU | Easy C++ / pip | Active 2026 |
| flagser | CPU many cores (construction) | Moderate | Active 2026 |
| Eirene | CPU | Julia, picky | Low |
| Dionysus | CPU | CMake + Python | Active 2026 |
| JavaPlex | JVM | Maven / IDE | Frozen 2019 |

---

## 5. Combinable vs incompatible techniques

### 5.1 Combinations that preserve exact VR PH and cut work

These stack, and are the default research recipe:

1. **Edge collapse** on the flag 1-skeleton (exact, all degrees).
2. **Enclosing radius** (or an explicit threshold) so the residual VR
   is not the full simplex.
3. **Implicit coboundary** of the residual (do not store \(K\)).
4. **Cohomology + clearing** (skip birth columns; VR asymmetry).
5. **Apparent-pair matching** (skip 90–99% of remaining columns;
   parallel).
6. **Emergent-pair abort** on the sequential remainder.
7. Optional: **lock-free** scheduling of the remainder (CPU) or GPU
   scan of step 5.

Empirically this is giotto-ph (AGPL) and, minus lock-free, GUDHI
collapse + Ripser / Ripserer `EdgeCollapsedRips`.

Further exact shrinks, *after* or *instead of* (1), if they apply:

- PHAT **chunk** / Perseus / distilled-VR Morse on the residual;
- Alpha instead of VR when the data is low-dimensional Euclidean
  (different complex, usually far fewer simplices);
- Cubical + Alexander duality for images.

### 5.2 Combinations that are implementation-only

These do not change the number of non-apparent, non-cleared columns:

- robin-hood / boost flat hash maps;
- bit_tree / heap / set column stores;
- Taskflow / OpenMP / CUDA around the same loops;
- lock-free vs sequential *when apparent rate is already 99%*
  (you are parallelizing a tiny remainder);
- Julia vs C++.

Use them after the algebraic reduction is chosen.

### 5.3 Real incompatibilities

| Pair | Why they fight |
| --- | --- |
| Apparent pairs + directed flag | No consistent diameter / oldest-cofacet order (flagser). |
| Emergent pairs + unordered (co)facet iterators | Ripserer contract: set `emergent_pairs=false` or get wrong pairs. |
| Implicit \(V\)-only storage + vineyards / full \(U\) | Dionysus/Oineus need trails; Ripser throws \(R\) away. |
| Edge collapse + generators in giotto-ph | API forbids `return_generators` with collapse. |
| CAM / simplex tree + dense uncollapsed VR | Memory explodes; use Ripser port instead. |
| GPU apparent scan + lock-free remainder on device | Remainder is irregular, fill-in, hashmap-heavy. |
| DIPHA-style point-cloud split + independent PH | Not the global VR module. |
| Involuted homology + “never compute homology columns” | Involuted *is* a restricted homology pass. |
| Multiparameter algorithms + 1-parameter barcode kernel | Different invariant. |
| AGPL/GPL code + MIT product | Legal, not algebraic. See §7. |
| SIMD reduction of heap-columns of variable length | Poor SIMD shape; distances/bitsets are the SIMD targets. |

---

## 6. Ideas that are valuable without taking the framework

Ranked by expected reduction of **algebraic work** for a CPU VR-class
engine. This is the list to steal from even when the repo is the wrong
base.

1. **Edge collapse** (GUDHI / giotto-ph / Ripserer / ArGintum). Exact.
   Shrinks the flag graph before any \(\binom{n}{d+1}\) appears. Biggest
   lever on data with a boundary or a sparse thresholded graph. Not
   uniformly a win (giotto-ph paper); must be measured.
2. **Apparent pairs as a Morse matching** (Bauer, Eirene “minimal
   pairs”, Oineus `ApparentMatching`). Exact, field-independent,
   embarrassingly parallel, typically removes almost all columns.
3. **Cohomology + clearing together** (de Silva et al. + Chen–Kerber +
   Bauer’s counting argument). Exact. The VR-specific reason homology
   engines lose.
4. **Emergent-pair short-circuit** (Ripser). Exact. Saves coboundary
   construction on the residual columns, which is the next cost after
   apparent pairs.
5. **Discrete Morse / chunk / distilled VR / Perseus.** Exact
   (distilled VR: claimed isomorphic). Shrinks the *complex*, not just
   the reduction schedule. Distilled VR is the newest VR-specific
   variant and is not yet a library.
6. **Enclosing radius** (Eirene → Ripser). Exact for finite metric
   spaces. Avoids the useless tail of the VR filtration.
7. **In-order VR generation** (Oineus / arXiv:2411.05495). Does not
   shrink \(K\), but removes a global sort that is itself superlinear
   in \(|K|\).
8. **Involuted PH** (Ripserer / Čufar–Virk). Does not shrink the
   barcode computation; shrinks the *cycle* computation. Use when
   representatives are required.
9. **Alexander duality + union-find** (CubicalRipser). Image-only.
   Removes a dimension from the algebraic pass.
10. **CAM** (GUDHI). When the complex must be explicit and
    \(\dim H^*\) stays small (Alpha, small triangulations).
11. **Lock-free remainder** (Oineus, giotto-ph). Parallelizes leftover
    columns; does not reduce their number. Steal the pairing-uniqueness
    lemma, reimplement under MIT/BSD.
12. **Flagser-style bounded approximation.** Only if the project later
    accepts non-exact barcodes.
13. **Schur / matroid view** (Eirene; SoCG 2025 matrix-multiplication
    PH). Long-term algebraic direction; not a drop-in kernel.
14. **Separation of parallelisms** (HYPHA, Ripser++). Architectural:
    GPU/SIMD for independent scans; CPU for remainder.

---

## 7. License notes

The workspace is MIT. That constrains *code* reuse, not *ideas*.

| License | Engines | Can we vendor into an MIT tree? |
| --- | --- | --- |
| MIT | Ripser, Ripser++, GUDHI, Ripserer, flagser | Yes, keep notices. |
| Modified BSD (LBNL) | Oineus, Dionysus | Yes, keep the three clauses **and** the enhancement-grant-back paragraph. |
| BSD-3 | JavaPlex | Yes. |
| LGPL-3 | PHAT, DIPHA | Dynamic linking of unmodified library is the safe path; copy-paste of sources into a MIT binary is not. |
| AGPL-3 | **giotto-ph** | No. A linked or copied derivative forces the *whole product* AGPL, including network use. Reimplement ideas. |
| GPL-3 | Eirene, CubicalRipser (inspected tree) | No vendor. Reimplement cubical ideas if needed. Re-check CubicalRipser before any copy: older wheels said MIT. |

Ripser’s `COPYING.txt` also contains Bauer’s optional “if you publish
enhancements, you grant me a license” paragraph (same spirit as LBNL).
It is not copyleft.

**Practical consequence.** A CPU baseline that we actually modify should
start from **Ripser (MIT)** or the **GUDHI Ripser port (MIT)**, not from
giotto-ph, even though giotto-ph is currently the strongest CPU
*implementation*.

---

## 8. CPU baseline candidate

**Best CPU baseline to modify: Ripser (Bauer), MIT, SHA
`01add51ff64aaf40889483260cc5c3b7d0f2a1e7`.**

Reasons, in order:

1. It is the unique algorithmic core that later CPU/GPU engines wrap.
   A new representation or Morse/collapse transform is easiest to
   insert into a 1000-line implicit coboundary reducer.
2. License matches the project.
3. Compile difficulty is the lowest of any exact VR engine.
4. Exactness, tie-breaking, and the cohomology+clearing+apparent+
   emergent combination are fully specified in one paper + one file.
5. The project strategy is CPU-first, GPU-later. Ripser++ is the GPU
   *reference*, not the kernel. Oineus is the better *generic* parallel
   engine but stores more of the complex and is a larger C++20 surface.
6. GUDHI is the better *library* (collapse, Alpha, cubical, CAM) and
   should stay an independent dependency for preprocessors and
   non-VR complexes. It is the wrong place to prototype a new reducer.
7. Ripserer is the better *experimental playground* (involuted, custom
   filtrations) if the next experiments stay in Julia. It is the wrong
   long-term kernel if the GPU stage is CUDA.
8. giotto-ph is the better *performance oracle* on multicore CPUs
   (lock-free + parallel apparent + collapse). AGPL forbids using it as
   the base. Reproduce its *measurements*, not its sources.

**How to use the others without mixing trees.**

- Preprocess with GUDHI or Ripserer’s edge collapse; feed the residual
  sparse graph to a Ripser-style reducer.
- Keep Ripser++ unchanged as the GPU reference (local clone; no
  upstream edits).
- Reimplement lock-free remainder and parallel apparent scan against
  the Ripser kernel if multicore becomes the bottleneck *after* collapse
  + apparent have shrunk the matrix.
- Use Oineus when the filtration is a grid or a mapping cylinder, not
  as the VR kernel.
- Use CubicalRipser / GUDHI cubical only for image-shaped data.

---

## 9. Techniques most likely to reduce algebraic work

Not constants. Not “rewrite it in CUDA.”

1. **Edge collapse of the flag 1-skeleton** — fewer edges ⇒ fewer
   cliques in every dimension. Exact.
2. **Apparent-pair Morse matching (and stronger Morse / distilled VR /
   PHAT chunk)** — fewer columns enter reduction. Exact.
3. **Cohomology + clearing on VR** — fewer columns *by combinatorics of
   \(\binom{n}{\bullet}\)*, not by a faster inner loop. Exact.
4. **Threshold / enclosing radius / sparse distances** — do not generate
   the full simplex. Exact for the truncated (or, for enclosing radius,
   complete) filtration you actually want.
5. **Change of complex when the data allows it** — Alpha in low
   Euclidean dimension; cubical + Alexander duality for images; witness
   / sparse Rips only with an explicit approximation class.
6. **Emergent-pair abort** — fewer cofacet enumerations on residual
   columns. Exact; smaller effect than (1)–(3) but essentially free.

Lock-free reduction, GPU apparent scan, bit-trees, robin-hood, and
Julia/C++ choice are **stage-2 constant factors**. They become relevant
after (1)–(5) have cut the matrix.

---

## 10. Inspected trees

Cloned read-only into `/tmp/ph-frameworks`. SHAs are `git rev-parse HEAD`
on 2026-10-13.

| Path | Remote | SHA | HEAD date |
| --- | --- | --- | --- |
| `ripser` | github.com/Ripser/ripser | `01add51ff64aaf40889483260cc5c3b7d0f2a1e7` | 2023-06-19 |
| `ripser-plusplus` | github.com/simonzhang00/ripser-plusplus | `30243c0c752de26d7fdf6e41f08bf7b840ca4744` | 2023-03-16 |
| `giotto-ph` | github.com/giotto-ai/giotto-ph | `21397fcefe2164f3f95f2c34ed494d7946e31998` | 2024-05-30 |
| `gudhi-devel` | github.com/GUDHI/gudhi-devel | `1c4ba125edf2822f823fb6669cfac067dafd10d7` | 2026-10-12 |
| `oineus` | github.com/anigmetov/oineus | `e52814a1ffb5b8a81e71ff1e93b4c14194673f0f` | 2026-10-02 |
| `Ripserer.jl` | github.com/mtsch/Ripserer.jl | `9def962dbc2a0bc9798509bdb15cc7002944a400` | 2026-06-29 |
| `dionysus` | github.com/mrzv/dionysus | `a1703fe977f85540fa05b56e59192ba936173779` | 2026-09-02 |
| `phat` | github.com/blazs/phat | `ca9dc645221dcdf42ecf7bb171983b6a819a468d` | 2018-06-09 |
| `cubicalripser` | github.com/shizuo-kaji/CubicalRipser_3dim | `12b7693948f04ea405be68ad4bca460e41b1ea00` | 2026-10-08 |
| `Eirene.jl` | github.com/Eetion/Eirene.jl | `16622d0aa1d7237895919e7fbdc1e8a6196425ab` | 2025-01-28 |
| `javaplex` | github.com/appliedtopology/javaplex | `05a288a4a99f27242d8f4b24e98d4cce749fb71a` | 2019-12-22 |
| `flagser` | github.com/luetge/flagser | `6763e964bc69c5bce3ed57491ea6dcd6e934d46b` | 2026-04-21 |
| `dipha` | github.com/DIPHA/dipha | `0b874769fbd092c07a12cebc2459adb02117c2fd` | 2017-05-25 |
| `ripser.py` | github.com/scikit-tda/ripser.py | `505fa1c1817ea2a40909550a43e88dddd511ebb6` | 2026-08-03 |
| `PersistenceHomology` | github.com/ArGintum/PersistenceHomology | `b0cf2e7024ec60f24ea91484456c48101add87d6` | 2021-08-01 |

Not found as named remotes: `Ripser/ripser-image`,
`HomologyInference` (algebraic engine), official Perseus git.

Primary papers used (open versions): Bauer arXiv:1908.02518;
Zhang–Xiao–Wang arXiv:2003.07989 / SoCG 2020; giotto-ph arXiv:2107.05412;
Boissonnat–Dey–Maria arXiv:1304.6813; Boissonnat–Pritam SoCG 2020;
Morozov–Nigmetov SPAA 2020; Čufar–Virk arXiv:2105.03629; Henselman–Ghrist
arXiv:1606.00199; CubicalRipser arXiv:2005.12692; flagser arXiv:1906.10458;
distilled VR arXiv:2412.07805; Otter et al. roadmap (EPJDS 2017);
Mischaikow–Nanda DCG 2013; Bauer–Kerber–Reininghaus ALENEX 2014.

---

## 11. Verdict for this project

- **Write path:** `/workspace/docs/ALGORITHM_COMPARISON.md`
- **CPU baseline to modify:** Ripser (MIT, implicit cohomology).
- **CPU performance oracle (do not vendor):** giotto-ph (AGPL).
- **GPU reference (do not make the kernel):** Ripser++ (MIT).
- **Preprocessor to keep independent:** GUDHI / Ripserer edge collapse.
- **Generic parallel engine to steal from:** Oineus (BSD) — apparent
  matching + lock-free remainder + in-order VR generation.
- **Algebraic-work reducers to try first:** edge collapse, apparent Morse
  matching, cohomology+clearing, then Morse/chunk/distilled-VR on the
  residual. Hardware parallelism only after those are measured.
