# Simplicial and cell complexes for persistent homology

A comparison of representations used to compute persistent homology (PH), written as the first-stage map for this project. Vietoris–Rips (VR) is the main reference. Diagrams of different complexes are **not** assumed to match.

Status of this note: literature and official-documentation survey (October 2026). No new benchmarks are claimed here.

---

## How to read this document

### Equivalence classes (do not mix them)

| Class | Meaning | Valid comparison |
| --- | --- | --- |
| **Exact same filtration** | Same filtered complex (up to a documented convention on scale, e.g. diameter vs radius, squared vs unsquared). | Persistence diagrams must match within numerical tolerance. |
| **Exact same persistence module** | Different complex / fewer cells, but a theorem gives isomorphic PH (often via homotopy equivalences or Morse collapse compatible with the filtration). | Diagrams must match. Cell counts need not. |
| **Homotopy-equivalent at each scale to the same geometric filtration** | E.g. Alpha / Čech / Euclidean offsets of the same radius. | Diagrams of the *geometric* scale parameter match. Individual simplex filtration values may differ. |
| **Multiplicative interleaving** | Inclusions such as \(A_{\alpha/c} \subseteq B_\alpha \subseteq A_{c\alpha}\). Persistence diagrams are a \(c\)-approximation on a log scale (bottleneck after log reparameterization). | Compare via the stated factor, not by requiring equal barcodes. |
| **Additive / Gromov–Hausdorff stability** | Perturbing the metric or the sample moves diagrams by a controlled bottleneck distance. | Stability bound, not equality. |
| **Empirical similarity** | Observed bottleneck / Wasserstein / Betti-curve closeness with no theorem covering the experiment. | Report as empirical only. |

A faster method is not “better” unless the cost / memory / information tradeoff is stated in one of these classes.

### Scale conventions

Two VR conventions appear in the literature and in software:

1. **Diameter convention** (Ripser, GUDHI Rips): a simplex enters at the maximum pairwise distance among its vertices. An edge \(pq\) enters at \(d(p,q)\).
2. **Radius convention** (some older geometric papers): a simplex enters when all pairwise distances are \(\le 2\alpha\).

Čech typically uses **ball radius**: \(\sigma\) enters when \(\bigcap_{p\in\sigma} B(p,r)\neq\emptyset\), i.e. the radius of a minimal enclosing ball (MEB).

GUDHI documents that after matching the 1-skeleton (Rips uses edge length, Čech uses half-length), the two filtrations “share the same 1-skeleton and are multiplicatively 2-interleaved or better.” Alpha and Delaunay–Čech in GUDHI often store **squared** radii. Always record the convention before comparing numbers.

### Combinatorial size vs algebraic work

PH cost is not determined by vertex count alone. For a \(k\)-skeleton the naive VR size is \(\Theta(n^{k+1})\). Matrix reduction is \(O(m^\omega)\) in the worst case (\(m\) = number of cells; \(\omega\) is the matrix-multiplication exponent; the classical algorithm is cubic). Methods that cut \(m\) by a factor \(\rho\) can cut algebraic work by roughly \(\rho^\omega\), but only if the reduction itself is cheaper than the saved reduction. Implicit algorithms (Ripser) never materialize \(m\) fully; their bottleneck is the number of *unpaired / non-apparent* columns that must be reduced.

---

## 1. Vietoris–Rips (main reference)

**Definition.** On a finite metric space \((X,d)\), the VR complex at scale \(t\) is the clique (flag) complex of the graph with an edge for every pair at distance \(\le t\) (diameter convention). Equivalently, \(\sigma\in\mathrm{VR}_t(X)\) iff \(\mathrm{diam}(\sigma)\le t\). The filtration is nested: \(t\le t'\) implies \(\mathrm{VR}_t\subseteq\mathrm{VR}_{t'}\).

VR is the flag complex of its 1-skeleton. That is why it can be stored as a distance matrix / proximity graph and why clique-complex algorithms apply.

### Compatible data / metrics

Any finite dissimilarity that can be treated as a symmetric matrix: Euclidean point clouds, geodesic / graph distances, correlation distances, and non-metric dissimilarities. No embedding is required.

### Geometric hypotheses

None for construction or for computing the VR barcode. Reconstruction theorems that relate \(\mathrm{VR}_t(X)\) to the homotopy type of an unknown manifold \(M\supset X\) need sampling conditions (reach / \(\mu\)-reach, density, scale windows). Those are *inference* hypotheses, not computational ones.

### Persistence guarantee

- **Exact** for the VR filtration itself.
- **Not equal** to Čech / Alpha / offset PH. After matching conventions, a standard inclusion is
  \[
  \check{\mathrm{C}}_r \;\subseteq\; \mathrm{VR}_{2r} \;\subseteq\; \check{\mathrm{C}}_{2r}
  \]
  (radius Čech, diameter VR), i.e. a multiplicative 2-interleaving. Euclidean Jung-type bounds can be tighter (\(\sqrt{2}\) in the plane after suitable scaling). GUDHI: “multiplicatively 2-interleaved or better.”
- Stability (Chazal–de Silva–Oudot, *Geometriae Dedicata* 2014; [arXiv:1207.3885](https://arxiv.org/abs/1207.3885)): for totally bounded metric spaces,
  \[
  d_b\bigl(\mathrm{dgm}\,H(\mathrm{Rips}(X)),\,\mathrm{dgm}\,H(\mathrm{Rips}(Y))\bigr) \le 2\,d_{\mathrm{GH}}(X,Y).
  \]
  The factor 2 is tight for Rips.

### Time / memory

- Full complex: \(2^n-1\) simplices.
- \(k\)-skeleton: \(O(n^{k+1})\) simplices, \(O(n^2)\) to write the distance matrix.
- Implicit cohomology (Ripser): coboundary and simplex order are generated on the fly; memory is dominated by the reduction hash / pivot structure, not by an explicit boundary matrix. Still exponential in homology dimension in the worst case.
- Clearing, apparent pairs, and emergent pairs remove a large fraction of columns in practice; there is no useful worst-case size bound better than the \(k\)-skeleton.

### Sensitivity to ambient dimension and \(n\)

Depends on **\(n\)** and on the **homology dimension \(k\)**, not on ambient Euclidean dimension \(d\) except insofar as \(d\) affects the distance graph. High ambient \(d\) with generic distances yields a dense graph and the full \(O(n^{k+1})\) blow-up. Low-dimensional geometric samples stay sparser at small scales.

Practical ceiling with current implicit codes (Ripser / Ripser++ / giotto-ph): \(H_0\)–\(H_1\) on \(n\sim 10^3\)–\(10^4\) is routine at moderate thresholds; \(n\sim 10^5\) for \(H_1\) is described as supercomputer-scale without a small stopping radius (Koyama–Robins–Turner, [arXiv:2412.07805](https://arxiv.org/abs/2412.07805)). \(H_2\) and above become expensive much earlier.

### CPU / GPU / distributed

| Path | Status |
| --- | --- |
| Sequential CPU | Ripser (reference). Apparent pairs + cohomology + clearing. |
| Multi-core CPU | giotto-ph (lock-free Ripser + parallel apparent pairs); Oineus; Ripserer.jl threads. |
| GPU | Ripser++ (finds apparent pairs and builds the cleared filtration on GPU; reduction still irregular). |
| Distributed | DIPHA can take a (sparse) distance matrix as VR. Partitioning the *point cloud* and computing independent VR barcodes does **not** give global VR PH. |

### Topological information quality

The standard, general-purpose barcode for metric data. Encodes more (and noisier) features than a sparsified or landmark complex. Can create “spurious” cycles relative to the union of balls; the 2-interleaving bounds that discrepancy but does not remove it.

### Implementations and maintenance

| Software | Role | Maintenance (as of 2026) |
| --- | --- | --- |
| [Ripser](https://github.com/Ripser/ripser) (Bauer; [arXiv:1908.02518](https://arxiv.org/abs/1908.02518), *J. Appl. Comput. Topol.* 2021) | Implicit VR cohomology. MIT. | Stable reference; low commit rate, algorithm frozen. |
| [Ripser++](https://github.com/simonzhang00/ripser-plusplus) | GPU VR. | Research code; keep as GPU baseline. |
| [giotto-ph](https://github.com/giotto-ai/giotto-ph) | Parallel CPU VR + edge collapse + weighted VR. AGPLv3. | Library exists; slower release cadence than GUDHI. |
| [GUDHI](https://gudhi.inria.fr/) Rips + Simplex tree | Explicit expansion; optional sparse / collapse. MIT. | Actively maintained (docs 3.13.x). |
| [Ripserer.jl](https://github.com/mtsch/Ripserer.jl) | Generic Ripser-style; `Rips(; sparse=true)`. MIT. | Maintained (v0.16.x). |
| [Dionysus 2](https://github.com/mrzv/dionysus) | Explicit VR among other complexes. BSD. | Maintained (v2.2.3). Timed here as a 1-thread oracle: circle \(n=400\) 11.68 s / 2.38M simplices vs Ripser 0.18 s; later leftover cells timeout (`dionysus.json`). Not vendored. |
| [DIPHA](https://github.com/DIPHA/dipha) | MPI VR / cubical / general. | Mature, little recent development. |
| [HomCloud](https://homcloud.dev/) | Wraps Ripser among other pipelines. GPL-3. | Actively maintained (v5.4.0, 2026-06). |
| [Oineus](https://github.com/anigmetov/oineus) | Shared-memory VR + grids. BSD. | PyPI v0.9.39. Timed here as a 1-thread oracle: slower than Ripser on leftover \(H_1\); times out earlier than Ripser and Dory (`oineus.json`). Not vendored. |
| [Dory](https://doi.org/10.1016/j.jocs.2024.102290) | Large VR up to dim 2 with a stopping radius. | Research (2024). Timed here as `pydory` 1.1.137, 1 thread: tracks Ripser on leftover \(H_1\); slower on sphere \(H_2\) \(n=400\). Oracle only, not vendored. |

### Valid equivalence

Exact VR PH. Interleaved with Čech / offsets, not equal. GH-stable with factor 2.

---

## 2. Čech complex

**Definition.** \(\sigma\in\check{\mathrm{C}}_r(X)\) iff the closed (or open) balls of radius \(r\) centered at the vertices of \(\sigma\) have nonempty common intersection. Filtration value = MEB radius (GUDHI can store the square).

### Compatible data / metrics

Intrinsically defined for any metric. Efficient MEB / intersection tests are practical mainly in **Euclidean** (or other Minkowski) space. Abstract Čech of a cover is the nerve; that is a different input type (see Cover / Nerve below).

### Geometric hypotheses

Nerve theorem: if every nonempty finite intersection of the covering sets is contractible, the nerve is homotopy-equivalent to the union. Euclidean closed/open balls are convex, so
\[
\check{\mathrm{C}}_r(X) \;\simeq\; \bigcup_{p\in X} B(p,r).
\]
This is the geometric filtration one usually *wants* for shape reconstruction. Positive-reach / \(\mu\)-reach hypotheses enter when relating that union to an unknown \(M\) (Kim–Mémoli–Stefanou and related SoCG 2020 work).

### Persistence guarantee

- **Exact** for the offset / ball-union filtration (nerve theorem, scale by scale).
- **Not equal** to VR. Multiplicative 2-interleaving as above.
- Same GH stability bound as VR: \(d_b\le 2\,d_{\mathrm{GH}}\) (Chazal–de Silva–Oudot).

### Time / memory

\(k\)-skeleton still \(O(n^{k+1})\) in the worst case. Each candidate simplex needs an MEB (or a higher-order intersection test), which is why GUDHI states that Čech “is taking much more time to be computed than the Rips complex but it offers more topological guarantees.” No implicit coboundary trick as clean as VR’s clique rule.

### Sensitivity to dimension and \(n\)

Combinatorial explosion in \(n\) and \(k\), plus MEB cost growing with ambient \(d\). In high \(d\), prefer a radius cap; GUDHI notes that Čech “can still make sense in higher dimension precisely because you can bound the radii,” whereas the full Delaunay substitute becomes impossible.

### CPU / GPU / distributed

CPU: GUDHI `Cech_complex` (CGAL kernels Epick_d / Epeck_d), Dionysus. No competitive GPU Čech pipeline. Not a good distributed primitive (MEB tests are local, but the complex is global).

### Topological information quality

The geometrically correct nerve of the offset filtration. Fewer “VR-only” cycles. The price is construction cost. In low-d Euclidean space, Alpha (below) realizes the *same* PH with far fewer simplices.

### Implementations

GUDHI Čech (MIT; Euclidean via CGAL). Dionysus. Rarely used as a production PH engine on large clouds.

### Valid equivalence

PH(Čech) = PH(Euclidean offsets). PH(Čech) \(\neq\) PH(VR). Alpha and Delaunay–Čech target this same module in Euclidean space.

---

## 3. Alpha complex (and Delaunay, Delaunay–Čech)

**Sources.** Edelsbrunner–Kirkpatrick–Seidel (alpha shapes); Edelsbrunner–Mücke, *ACM Trans. Graph.* 1994; Edelsbrunner–Letscher–Zomorodian persistence (originally demonstrated on alpha filtrations); survey: Edelsbrunner, “Alpha Shapes — a Survey” (2011). GUDHI Alpha / Delaunay manuals.

**Definition.** Let \(\mathrm{Del}(X)\) be the Delaunay triangulation (nerve of the Voronoi diagram). The **alpha complex** \(A_r\) is the subcomplex of \(\mathrm{Del}(X)\) consisting of simplices whose corresponding Voronoi cells meet the balls of radius \(r\) (equivalently: filtration value = squared radius of the smallest *empty* circumsphere / Delaunay ball). The **Delaunay–Čech** complex uses the same underlying triangulation but assigns each simplex its MEB radius. The unfiltered **Delaunay complex** is \(\mathrm{Del}(X)\) itself.

### Compatible data / metrics

Finite point sets in **Euclidean** \(\mathbb{R}^d\) (or a space with a well-defined empty-sphere Delaunay property). Weighted / regular triangulations give weighted alpha (power distance). Periodic variants exist in 3D (CGAL / GUDHI `Alpha_complex_3d`). Not defined from an arbitrary distance matrix.

### Geometric hypotheses

General position (no \(d+2\) cospherical points) is assumed or handled symbolically. Delaunay is dual to Voronoi; alpha is the nerve of \(\{\mathrm{Vor}(p)\cap B(p,r)\}\). Those sets are convex, so the nerve theorem gives
\[
A_r \;\simeq\; \bigcup_{p\in X} B(p,r) \;\simeq\; \check{\mathrm{C}}_r(X).
\]
This is Euclidean-specific.

### Persistence guarantee

- **Exact** for the offset / Čech persistence module (same scale parameter \(r\)).
- Alpha vs Delaunay–Čech: GUDHI, “the resulting filtration values will be different.” For acute simplices circumradius = MEB radius; for obtuse simplices they differ. Both sublevel sets remain homotopy-equivalent to the same union of balls, so the **persistence modules as functions of \(r\)** agree with Čech / offsets. Simplex-wise values and intermediate combinatorial complexes differ.
- **Not equal** to VR PH. Compare with the VR–Čech interleaving, or compare diagrams only after stating that one is VR and one is offset PH.

### Time / memory

Bottleneck is computing \(\mathrm{Del}(X)\):

- Worst-case number of simplices: \(\Theta\bigl(n^{\lceil d/2\rceil}\bigr)\) (classic Delaunay bounds; often quoted as \(O(n^{\lceil d/2\rceil})\) or \(O(n^{\lceil(d+1)/2\rceil})\) depending on counting infinite cells / dimension indexing). See e.g. the discussion in JoCG 14 (2023) on coupled alpha complexes.
- \(d=2\): linear expected / \(O(n\log n)\) time, \(O(n)\) size.
- \(d=3\): \(O(n^2)\) worst case, typically nearer linear for well-distributed samples. Uniform random point clouds: \(O(n)\) simplices in expectation.
- \(d\ge 5\): construction is usually infeasible at interesting \(n\).
- GUDHI always builds the Delaunay triangulation first; `max_alpha_square` does **not** reduce construction time.

Quadratic-programming methods that seek alpha simplices without the full Delaunay triangulation exist (e.g. *BMC Bioinformatics* / PMC11350180, 2024) but are not the production default.

### Sensitivity to dimension and \(n\)

**Dominated by ambient \(d\).** Excellent for \(d\le 3\), sometimes usable at \(d=4\), the wrong tool for high-\(d\) or general metrics. For fixed small \(d\), scales to much larger \(n\) than VR (\(n\sim 10^5\)–\(10^6\) in 2D/3D is realistic).

### CPU / GPU / distributed

CPU via CGAL (GUDHI, HomCloud, Dionysus alpha). Incremental Delaunay is sequential by nature; some CGAL spatial locks exist but this is not a GPU problem. Distributed Delaunay exists in the meshing literature and is out of scope for a first PH benchmark.

### Topological information quality

Best available exact geometric PH for low-d Euclidean clouds: same information as the union of balls, linearly or quadratically many cells instead of \(\Theta(n^{k+1})\). Weighted alpha is the right object for atoms of different radii (molecules).

### Implementations

| Software | Notes |
| --- | --- |
| GUDHI `AlphaComplex`, `DelaunayComplex`, `DelaunayCechComplex` | CGAL + Eigen. MIT with GPL pieces for incremental Delaunay. Exact or inexact kernels; GUDHI guarantees a valid (non-decreasing) filtration. |
| GUDHI `Alpha_complex_3d` | Specialized 3D, weighted, periodic. |
| HomCloud | Production alpha pipelines; 2026: coupled alpha / relative PDs. |
| Dionysus 2 | Alpha among other complexes. |
| CGAL 3D alpha shapes | Geometry library, not a PH engine. |

### Valid equivalence

PH(Alpha(\(r\))) = PH(Čech(\(r\))) = PH(offsets(\(r\))) as persistence modules. PH(Alpha) \(\neq\) PH(VR). Squared vs unsquared radii must be documented.

---

## 4. Edge-collapsed Vietoris–Rips

**Sources.** Boissonnat–Pritam, “Edge Collapse and Persistence of Flag Complexes,” SoCG 2020, [LIPIcs.SoCG.2020.19](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2020.19). Predecessor: strong (vertex) collapses, SoCG 2019, [LIPIcs.SoCG.2019.55](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2019.55). Follow-up: Glisse–Pritam, SoCG 2022 (simpler explanation, iterated collapse). GUDHI edge-collapse module (since 3.3.0); giotto-ph reimplementation.

**Definition.** In a flag complex, an edge \(e\) is *dominated* if its link is a cone, equivalently (Boissonnat–Pritam, Lemma 2) \(N[e]\subseteq N[v_0]\) for some vertex \(v_0\notin e\). An edge collapse removes dominated edges; the residual is still flag. On a flag *filtration*, collapse is implemented by raising an edge’s filtration value or deleting it, using only the 1-skeleton, producing a smaller flag filtration \(\mathcal{F}^c\).

### Compatible data / metrics

Any **flag / clique filtration**: VR from a metric or distance matrix, or the clique complex of a filtered graph. No Euclidean hypothesis.

### Geometric hypotheses

None. The algorithm is combinatorial.

### Persistence guarantee

**Exact.** \(\mathcal{F}^c\) has the same persistence module as \(\mathcal{F}\). \(k\)-collapses decompose into elementary simple collapses and induce strong deformation retracts; the paper lifts this to filtrations so that the reduced sequence is again a flag *filtration* (not a tower of simplicial maps). Valid in every homology dimension.

An optional approximate mode (raise values more aggressively) is mentioned; GUDHI’s default `flag_complex_collapse_edges` is the exact reduction.

### Time / memory

- Collapse uses only the graph: time \(O(n\,n_c\,k^2)\) where \(n\) = input edges, \(n_c\) = output (“critical”) edges, \(k\) = max degree (SoCG 2020).
- Strong collapse of a flag complex: \(O(k^2 v^2)\) in \(v\) vertices (SoCG 2019); empirically much slower than edge collapse because it produces a tower that must be converted back to a filtration.
- Reported edge reductions (SoCG 2020, Table 1):

  | Dataset | \(n\) pts | Edges in \(\to\) out | Ratio |
  | --- | ---: | ---: | ---: |
  | netw-sc | 379 | 8.4K \(\to\) 417 | \(\approx 20\times\) |
  | senate | 103 | 2.7K \(\to\) 234 | \(\approx 12\times\) |
  | eleg | 297 | 9.8K \(\to\) 562 | \(\approx 17\times\) |
  | HIV | 1088 | 182K \(\to\) 6.9K | \(\approx 26\times\) |
  | torus | 2000 | 428K \(\to\) 14K | \(\approx 31\times\) |

  The paper’s rule of thumb: \(\sim 20\times\) fewer edges, hence up to \(O(20^{k})\) fewer \(k\)-simplices after expansion. On torus, collapse + GUDHI PH finished in 289 s while Ripser on the uncollapsed filtration hit the 12 h / memory wall at dim 3.

GUDHI Python: `gudhi.flag_filtration.edge_collapse.reduce_graph(..., nb_iterations=1)`. Iterating can shrink further (SoCG 2022).

### Sensitivity to dimension and \(n\)

Independent of ambient \(d\). Helps most when the proximity graph is locally cone-like (geometric samples, not i.i.d. high-d noise). HIV-scale graphs (\(10^5\) edges) already make collapse itself take minutes; the payoff is the subsequent expansion / reduction. High \(k\) after a 20\(\times\) edge cut is still the difference between feasible and impossible.

### CPU / GPU / distributed

CPU, essentially sequential on the filtration order (backward scan for removable edges). giotto-ph ships a reimplementation next to a parallel Ripser core; the collapse itself is not the GPU part. In principle the 1-skeleton can be built in parallel; the domination tests are local but the filtration rewrite is ordered. A good candidate to run *before* distributing algebraic reduction.

### Topological information quality

Identical to VR. This is a **work-reduction of the reference**, not a different topological estimator.

### Implementations

GUDHI (Pritam–Glisse; MIT) — production. giotto-ph — “improved reimplementation.” Sophia (Schreiber) is a related research code cited in the paper. Not in stock Ripser / Ripser++.

### Valid equivalence

Exact VR PH. The only valid diagram comparison against Ripser is **equality** (same threshold, same dimension cap, same field, same scale convention).

---

## 5. Sparse Rips (Sheehy and later variants)

### 5.1 Sheehy sparse VR (2012 / DCG 2013)

**Source.** Sheehy, “Linear-Size Approximations to the Vietoris–Rips Filtration,” SoCG 2012; *Discrete Comput. Geom.* 49:778–796, 2013. [arXiv:1203.6786](https://arxiv.org/abs/1203.6786).

**Construction.** Hierarchical net-tree (Har-Peled–Mendel). Points are removed at larger scales (they are already covered). Two outputs: a zigzag filtration, and a non-zigzag “union” filtration with the same PH. Metric perturbation (weighted distances) removes homology zigzags.

### Compatible data / metrics

Any finite metric. **Theoretical size / time** need a bound on **doubling dimension** \(\delta\) (every ball of radius \(2r\) is coverable by \(2^\delta\) balls of radius \(r\)).

### Geometric hypotheses

Doubling. Euclidean \(\mathbb{R}^d\) has \(\delta=\Theta(d)\). High-d cubes, expanders, and many graph metrics have large \(\delta\); then the “linear” size is linear with a huge constant.

### Persistence guarantee

**Multiplicative \((1+\varepsilon)\)-approximation** of the VR persistence diagram (births and deaths each off by at most a factor \(1+\varepsilon\)). Persistence Approximation Lemma: nested inclusions after reparameterization. This is **not** exact VR PH.

GUDHI implements the Cavanna–Jahanseir–Sheehy geometric variant ([CCCG 2015](https://donsheehy.net/research/cavanna15geometric.pdf); also applies to Čech for convex metrics), multiplying filtration values by 2 to match diameter VR. GUDHI cites a \((1,\,1/(1-\varepsilon))\)-interleaving; “in practice the error is usually smaller.” Guarantees are stated for \(\varepsilon<1\). Larger \(\varepsilon\) still builds a smaller complex with **no quality guarantee**.

### Time / memory

Sheehy: \(O(n)\) simplices and \(O(n\log n)\) construction time, constants \(\bigl(1/\varepsilon\bigr)^{O(k\delta)}\) for the \(k\)-skeleton. Landmark result: first construction that is linear in \(n\) for the *whole* scale range.

### Sensitivity to dimension and \(n\)

Linear in \(n\), exponential in \(\delta k/\varepsilon\). Sheehy’s constants explode in high doubling dimension. SimBa (below) was written specifically because Sparse Rips complexes stayed huge on moderate high-d data.

### CPU / GPU / distributed

CPU. GUDHI `RipsComplex(..., sparse=ε)` / `Sparse_rips_complex`. Net-tree construction is sequential. No standard GPU sparse-Rips. The net-tree is a natural hierarchical partition, but the *approximation* is global (projection onto nets); splitting the cloud independently would be a different (weaker) estimator.

### Topological information quality

Controlled approximation to **VR**, hence two hops away from offsets (sparse\(\approx_\varepsilon\)VR \(\approx_2\) Čech). Short bars are the first to be unreliable. Fine for exploratory PH when VR is impossible; not a substitute when the scientific claim needs the exact VR barcode.

### Implementations

GUDHI (maintained). Ripserer.jl: `Rips(...; sparse=true)` (older `SparseRips` deprecated). Original Sheehy code is not a modern dependency.

### 5.2 Cavanna–Jahanseir–Sheehy (2015)

Geometric rewrite: sparse Čech as the nerve of grown balls that become empty as points are removed; vertex removal = sequence of elementary edge collapses. Simpler proofs; works for Rips and Čech in convex metrics. This is what GUDHI documents as its sparse Rips.

### 5.3 Batch-collapsed Rips and SimBa

**Source.** Dey–Shi–Wang, “SimBa: An Efficient Tool for Approximating Rips-filtration Persistence via Simplicial Batch-collapse,” ESA 2016 / *ACM J. Exp. Algorithmics* 2019. [arXiv:1609.07517](https://arxiv.org/abs/1609.07517). Builds on Dey–Fan–Wang persistence for simplicial maps (SoCG 2014).

**Idea.** Collapse vertices in batches as the scale grows; connect complexes by simplicial maps, not only inclusions. A new sparse Rips-like edge rule avoids over-connecting. Empirically much smaller than Sheehy / sparse-Rips-with-collapse on high-d data; the paper reports order-of-magnitude speedups and cases where Sparse Rips does not finish.

**Guarantee.** Approximation of VR PH with quality controlled by the batch / net parameters (not the same theorem as Sheehy’s \((1+\varepsilon)\) linear-size filtration).

**Implementation.** Academic SimBa binary ([Purdue page](https://www.cs.purdue.edu/homes/tamaldey/SimBa/Simba.html)); authors “do not intend to be responsible for the maintenance.” Not in GUDHI. Treat as a historical / experimental baseline, not a first-round dependency.

### Valid equivalence (all sparse variants)

Approximate VR, with the specific interleaving / factor of the variant. Never claim equality with Ripser diagrams.

---

## 6. Witness complexes and landmark variants

**Source.** de Silva–Carlsson, “Topological estimation using witness complexes,” SPBG 2004. [EG digital library](https://diglib.eg.org/handle/10.2312/SPBG.SPBG04.157-166).

**Definition.** Choose landmarks \(L\subset W\) (or \(L\) not necessarily in the sample). Non-landmark points (or all of \(W\)) *witness* simplices on \(L\). With distance table \(D(L,W)\):

- **Strict / weak witness** (\(R=0\)): \(\sigma\subset L\) is witnessed by \(w\) if every landmark in \(\sigma\) is among the nearest landmarks to \(w\) (weak: nearest among \(L\setminus\sigma\) vs \(\sigma\); strong: nearest among all of \(L\)).
- **Relaxed:** allow slack \(\alpha\) (GUDHI uses \(\alpha^2\) in Euclidean versions).
- **Lazy witness:** take the 1-skeleton of the (relaxed) witness complex and form its **clique complex**. The whole filtration is determined by edges. de Silva–Carlsson already flag lazy witness as the practical choice for low-dimensional homology.

Landmark selection: random, or **maxmin / farthest-point** (iteratively add the point maximizing distance to the current set). Maxmin covers well but is outlier-sensitive.

### Compatible data / metrics

Any metric: only landmark–witness distances are required. Euclidean GUDHI classes build a kd-tree on landmarks. Graph geodesics are allowed (already in the 2004 paper).

### Geometric hypotheses

Intended as a Delaunay-like nerve with landmarks as vertices. Reconstruction theorems exist under sampling + landmark-density conditions (later work of Guibas, Oudot, et al. on weak witnesses), but they are stricter and less routinely checked than Alpha’s nerve theorem. The 2004 paper **does not** prove correctness.

### Persistence guarantee

**Not exact VR or Čech PH.** Changing \(|L|\), the landmark rule, \(\nu\) (lazy parameter), or \(\alpha\) changes the filtration. Chazal–de Silva–Oudot treat witness complexes in the same GH-stability framework, but that is stability of *a given* witness construction, not equality with VR.

Lazy witness PH equals the PH of that lazy flag filtration — exact for that object, approximate for VR / offsets.

### Time / memory

Vertices = \(|L|=m\), not \(n=|W|\). Naive \(k\)-skeleton \(O(m^{k+1})\). Building nearest-landmark lists: \(O(n\,m)\) naive, better with a kd-tree in low-d Euclidean. Lazy: build \(O(m^2)\) possible edges from witnesses, then expand cliques.

This is the original motivation: homotopy types of data are often realizable on far fewer vertices than \(n\).

### Sensitivity to dimension and \(n\)

Linear in \(n\) for the witness pass if \(m\) is fixed. Quality and size are governed by \(m\) and by how well \(L\) covers. In high-d, maxmin landmarks still exist, but witnessing becomes less geometric (almost all nearest-neighbor relations look the same). Dey–Fan–Wang (GIC paper) argue that plain witness complexes “fail to capture the topology in high dimensions” relative to their graph-induced complex.

### CPU / GPU / distributed

CPU. GUDHI: `WitnessComplex` (nearest-landmark table), `EuclideanWitnessComplex`, strong variants. Landmark selection (`choose_n_farthest_points`) is sequential greedy. Distance-to-landmarks is embarrassingly parallel. The *complex on \(L\)* is a single global object; one can distribute the witness scan, not the PH of independent subsets.

### Topological information quality

Often *cleaner* barcodes than full VR (de Silva–Carlsson: “less noise”) because \(m\ll n\) kills small cycles — and can kill real small features. Quality is a function of landmark design. Treat as a **different estimator**, then measure bottleneck to VR / Alpha on small instances.

### Implementations

| Software | Notes |
| --- | --- |
| GUDHI witness module (since 1.3 / 2.0) | Weak and strong, Euclidean (MIT+GPL via CGAL) and table-based (MIT). |
| JavaPlex | Historical lazy-witness tutorial code. Last release 4.3.4 (2018). Do not depend on it. |
| Dionysus | Witness experiments in the broader ecosystem; not the modern default. |

GUDHI’s built-in API is weak/strong witness, not the clique-lazy construction; lazy is typically “1-skeleton then `expansion()`” (or a custom flag filtration).

### Valid equivalence

Exact PH of the chosen witness filtration. No theorem that the diagram equals VR or Čech. Compare with bottleneck / interleaving only if a specific reconstruction theorem applies; otherwise empirical.

---

## 7. Cubical complexes

**Sources.** Kaczynski–Mischaikow–Mrozek, *Computational Homology* (Springer, 2004); Wagner–Chen–Vuçini cubical PH; Bauer–Kerber–Reininghaus DIPHA; Kaji–Sudo–Ahara, CubicalRipser, [arXiv:2005.12692](https://arxiv.org/abs/2005.12692). GUDHI cubical user manual.

**Definition.** Cells are products of intervals (vertices, edges, squares, cubes, …) filling a rectangular grid. A **lower-star / V-construction** filtration is induced by values on vertices (or voxels interpreted as vertices): a cell enters at the max of its vertices. A **T-construction** puts values on top-dimensional cells and extends downward (GUDHI and CubicalRipser support both). Periodic boundary conditions turn the grid into a torus.

### Compatible data / metrics

Scalar grids: 1D series, 2D images, 3D/4D volumes, regular lattices. **Not** a general point-cloud complex. Voxelizing a cloud is a different pipeline (and a different filtration).

### Geometric hypotheses

The domain is a product grid. Topology is that of the cubical set / sublevel set of the scalar field, not of a sampling of a manifold in \(\mathbb{R}^d\) (unless the grid *is* that sampling).

### Persistence guarantee

**Exact** for the chosen cubical filtration (V or T). V and T are **not** the same filtration; barcodes can differ. Cubical PH is not VR PH of the voxel centers.

### Time / memory

Number of cells is \(O(3^d N)\) or \(O(2^d N)\) depending on whether one stores all faces of \(N\) top cells in dimension \(d\). For 2D/3D images this is linear in pixels/voxels with a small constant — the reason cubical beats triangulation (a triangulation of a 3D grid inflates the cell count substantially; Wagner–Chen–Vuçini already measured this). Bitmap encodings store a value array plus shape; faces/cofaces are index arithmetic (GUDHI “bitmap cubical complex”).

CubicalRipser adapts Ripser’s implicit reduction (apparent pairs, clearing) to cubes; \(\mathbb{F}_2\) only; 1D–4D. DIPHA is MPI-parallel but memory-heavy (CubicalRipser 2020: DIPHA did not finish a \(512^3\) volume on the test machine). cuCube (Glisse, ESA 2026): GPU \(H_0/H_1\) for 1D/2D lower-star, up to \(\sim 200\times\) vs sequential GUDHI CubicalPersistence on the reported tests.

### Sensitivity to dimension and \(n\)

Linear in voxels, exponential in grid dimension \(d\) (number of faces per cell). Fine for \(d\le 3\), usable at 4, wrong for a \(100\)-D grid. Independent of “ambient Euclidean dimension” in the point-cloud sense.

### CPU / GPU / distributed

| Software | Parallelism | Notes |
| --- | --- | --- |
| CubicalRipser | Fast sequential CPU; Python / PyTorch helpers | Active (v0.0.34+). |
| GUDHI cubical | Sequential, arbitrary \(d\), V and T, periodic | Usability / generality. |
| DIPHA | MPI cluster | V-construction; large memory. |
| Oineus | Shared-memory lock-free | Grids + custom filtrations; image/kernel/cokernel. |
| HomCloud / HomCube | CPU; can call CubicalRipser | Active. |
| cuCube | GPU 1D/2D | Research (2026). |
| FlashCubical | CPU 2D/3D V-filtration | Research (2026). |
| Perseus | Sequential Morse + cubical | Aging. |

### Topological information quality

The correct object for image / volume sublevel sets (connected components, loops, voids of a grayscale function). Do not use as a universal replacement for VR on point clouds.

### Valid equivalence

Exact PH of that cubical filtration. Equal to another cubical code only if V/T, periodicity, field, and tie-breaking match. Not comparable by equality to VR / Alpha of a related point set.

---

## 8. Discrete Morse theory, apparent pairs, reduced and distilled VR

These are **reductions of a filtration**, not a new sampling complex. They belong in the same design space because they attack “work” rather than “implementation constants.”

### 8.1 Discrete Morse for filtrations (Mischaikow–Nanda)

**Source.** Mischaikow–Nanda, “Morse Theory for Filtrations…,” *Discrete Comput. Geom.* 50:330–353, 2013. [authors’ PDF](https://people.maths.ox.ac.uk/nanda/source/DMPers-Final.pdf). Software: [Perseus](https://people.maths.ox.ac.uk/nanda/perseus/).

**Guarantee.** A filtered acyclic matching produces a Morse filtration with **identical PH**. Works for general cell complexes (simplicial, cubical, …).

**Complexity.** MorseReduce: \(O(n\cdot p\cdot \tilde m)\) with \(n\) input size, \(p\) coboundary mass, \(\tilde m=\sum m_i^2\) on the Morse complex. Then classical persistence \(O(m^3)\) on the reduced complex. If \(m\ll n\), total cost is essentially linear in \(n\). **No reduction is guaranteed**; worst case \(m\approx n\).

**Implementation.** Perseus (GPL; last academic snapshot, not a modern dependency). The *idea* is live in every apparent-pair / collapse pipeline.

### 8.2 Apparent pairs as implicit Morse (Ripser, Eirene)

**Sources.** Bauer, Ripser paper [arXiv:1908.02518](https://arxiv.org/abs/1908.02518). Independently: Henselman-Petrusek “minimal pairs” in Eirene ([arXiv:1606.00199](https://arxiv.org/abs/1606.00199)). Close pairs: Delgado-Friedrichs et al. (2015). Kahle (2011) discrete gradient on VR via a vertex order = lexicographic apparent pairs (Bauer, Lemma 3.8 / 3.9).

**Definition.** In a simplexwise filtration, \((\tau,\sigma)\) is an **apparent pair** if \(\sigma\) is the youngest facet of \(\tau\) and \(\tau\) is the oldest cofacet of \(\sigma\). Apparent pairs form an acyclic partial matching (a discrete gradient) compatible with the filtration, and they are persistence pairs of the simplexwise refinement.

**Guarantee.** Exact. Using them to skip columns does not change the barcode.

**Work reduction.** In VR, a huge fraction of pairs are apparent (especially with a well-chosen simplex order). Ripser never writes those columns. This is already the largest practical reduction *inside* the VR reference implementation. Ripser++ pulls “find apparent pairs” out as a GPU kernel. Mendoza-Smith–Tanner and later GPU PH work do the same.

Apparent pairs are **not** a smaller complex one stores; they are an implicit Morse matching. Distilled VR (below) turns a related matching into an explicit subcomplex.

### 8.3 Reduced Vietoris–Rips (Koyama–Mémoli–Robins–Turner)

**Source.** [arXiv:2307.16333](https://arxiv.org/abs/2307.16333) (v2, 2024).

**Guarantee.** Degree-1 PH of the reduced filtration \(\mathcal{R}_\bullet(X)\) is isomorphic to degree-1 VR PH, for any finite metric space. A higher-degree version is indicated. 2-simplices drop from \(O(n^3)\) to \(O(n^2)\) when \(X\) has bounded doubling dimension.

**Implementation.** Research; not in GUDHI / Ripser. The Euclidean geometry is used for *speed* of construction; the isomorphism is metric-general.

### 8.4 Distilled Vietoris–Rips

**Source.** Koyama–Robins–Turner, [arXiv:2412.07805](https://arxiv.org/abs/2412.07805).

**Construction.** On the reduced VR complex, take the apparent-pair Morse matching \(\mu_q\). Keep simplices reachable from critical \((q+1)\)-simplices in the matching graph, plus faces. That is the distilled complex \(D^q_r(X)\).

**Guarantee.** Theorem 3.9: for every finite metric space and every \(q>0\),
\[
\mathrm{PH}_q(D^q_\bullet(X)) \;\cong\; \mathrm{PH}_q(R^q_\bullet(X)) \;\cong\; \mathrm{PH}_q(\mathrm{VR}_\bullet(X)).
\]
Exact VR PH in degree \(q\). Construction needs only the distance matrix.

**Complexity / parallelism.** Aimed at **memory**: do not store the full VR boundary matrix. The authors describe the build + reduce as highly parallelisable; runtime may still need many cores. No production library as of this survey. Not a first-round benchmark *implementation*, but a first-class *algorithmic candidate* for a new CPU core.

### Valid equivalence

All four (MorseReduce, apparent pairs, reduced VR, distilled VR) claim **exact** PH of the original (VR or input) filtration, in the degrees they cover. They should match Ripser diagrams when implemented correctly. They do not change the topological estimator; they change the work.

---

## 9. Other relevant representations

### 9.1 Clique / flag complexes

VR *is* the clique complex of the threshold graph. Any algorithm for flag filtrations (edge collapse, Ripser-style implicit coboundaries, tidy sets of Zomorodian 2010) applies. Weighted VR (giotto-ph, GUDHI) is the clique complex of a weighted graph (outlier-robust variants). **Guarantee:** exact PH of that flag filtration.

### 9.2 Strong collapses (Barmak–Minian / Boissonnat–Pritam 2019)

0-collapse: remove dominated *vertices*. Exact PH for flag towers; \(O(k^2v^2)\). Empirically superseded by edge collapse (SoCG 2020: EdgeCollapser “several orders of magnitude” faster; VertexCollapser on torus did not finish in 12 h). Keep as ancestry, not as a first-round method.

### 9.3 Graph-induced complex (GIC)

**Source.** Dey–Fan–Wang, SoCG 2013, [arXiv:1304.0662](https://arxiv.org/abs/1304.0662). GUDHI `CoverComplex` / `GraphInducedComplex`.

Landmarks \(Q\) plus a graph \(G\) on the full sample \(P\). A simplex on \(Q\) appears when a clique of \(G\) has vertices in distinct Voronoi cells of \(Q\). Sparser than VR on the same landmarks (it does not take all Rips cliques on \(Q\)). Theorems for \(H_1\) inference and surface reconstruction under sampling hypotheses. **Not** exact VR. GUDHI implementation is maintained as part of the Mapper / Nerve / GIC family.

### 9.4 Cover, Nerve, Mapper

Nerve of a cover (functional or Voronoi). Exact PH of that nerve, which is a *different* object (often a graph or low-dimensional complex for visualization). GUDHI cover-complex module. Useful as a qualitative map, not as a VR substitute.

### 9.5 Dowker complexes

Nerve of a relation (Dowker 1952). Witness complexes are a geometric Dowker construction. Chazal–de Silva–Oudot prove stability for Dowker persistence. Same warning: do not equate to VR.

### 9.6 Sparsified Čech and permutahedral / digitization approximations

- Kerber–Sharathkumar, ISAAC 2013: approximate Čech.
- Choudhary–Kerber–Raghvendra: WSSD linear-size Čech in fixed \(d\); interpolating Čech–Rips complexes of size about \(O(n d^{\lceil 1/(2\varepsilon)\rceil})\) without hidden dependence on ambient dimension ([Approximate Čech Complexes](https://page.mi.fu-berlin.de/arunich/Files/Papers/ApproximateCech.pdf)).
- Permutahedral towers: polynomial-size \((1+\varepsilon)\) approximations, size \(n\,2^{O(d\log d)}\) in expectation (*Discrete Comput. Geom.*).
- Digitization [arXiv:1812.04966](https://arxiv.org/abs/1812.04966): \((1+\varepsilon)\)-approx Čech of size \(n(1/\varepsilon)^{O(d)}\) in fixed \(d\), spread-independent.

**Guarantee:** approximate Čech / offset PH, not VR. **Implementations:** research prototypes, not GUDHI defaults. Relevant as existence proofs that linear / near-linear *Čech* approximations exist in fixed \(d\); not first-round software.

### 9.7 Tangential complex (GUDHI)

Local \(k\)-dimensional Delaunay in estimated tangent spaces. Runtime linear in ambient \(d\), exponential in intrinsic \(k\). Reconstruction-oriented; not a standard PH filtration baseline.

### 9.8 Incremental Delaunay (GUDHI)

Filtration of Delaunay triangulations as points are inserted, plus conflict simplices. Usually dimension \(d+1\). Different from alpha. Niche.

---

## 10. Side-by-side comparison

Legend: **E** = exact for the named object; **A** = approximate with a theorem; **G** = geometric reconstruction hypotheses; **n/a** = not applicable.

| Complex | Data | Geometry needed | PH vs VR | PH vs offsets / Čech | Size (typical / worst) | Ambient \(d\) | \(n\) scaling | CPU | GPU | Distributed | Info quality | Impl. health |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Vietoris–Rips** | Any metric / matrix | None | **E** (it is VR) | 2-interleaved | \(O(n^{k+1})\) \(k\)-skel.; implicit in Ripser | Weak (via distances) | Harsh in \(n,k\) | Excellent | Ripser++ | DIPHA matrix only | Reference | Ripser / GUDHI / giotto-ph |
| **Čech** | Metric; Euclidean in practice | Nerve + convex balls | 2-interleaved | **E** | \(O(n^{k+1})\) + MEB | MEB cost grows | Harsh | GUDHI / Dionysus | No | No | Gold geometric | Niche |
| **Alpha / Del–Čech** | Euclidean \(\mathbb{R}^d\) | Delaunay | Interleaved only | **E** (as modules in \(r\)) | \(O(n)\)–\(O(n^{\lceil d/2\rceil})\) | **Hard wall** \(d\gtrsim 5\) | Best low-\(d\) | GUDHI+CGAL | No | Meshing lit. | Best low-\(d\) geometric | Strong |
| **Edge-collapsed VR** | Flag filtrations | None | **E** | Same as VR | \(\sim 10\)–\(30\times\) fewer edges in paper | None | Collapse \(O(n n_c k^2)\) | GUDHI, giotto-ph | Not yet | Preprocess, then reduce | = VR | Strong (GUDHI) |
| **Sparse Rips (Sheehy / CJS)** | Doubling metrics | Doubling for bounds | **A** \((1+\varepsilon)\) or \((1,1/(1-\varepsilon))\) | A then 2-interleave | \(O(n)\) with \((1/\varepsilon)^{O(k\delta)}\) | Via \(\delta\) | Linear \(n\), bad \(\delta\) | GUDHI | No | Hierarchical, global | Approx VR | GUDHI yes; SimBa no |
| **SimBa** | Point clouds | Nets / batches | **A** | A | Often \(\ll\) Sheehy in high-\(d\) | Better practically | Aggressive | Academic binary | No | Maps / batches | Approx VR | Unmaintained |
| **Witness / lazy** | Any metric + landmarks | Landmark quality | Empirical / special thms | Empirical | \(O(m^{k+1})\), \(m=\|L\|\) | Weak | Linear in \(n\) if \(m\) fixed | GUDHI | Distances only | Witness scan | Different estimator | GUDHI yes |
| **GIC** | Graph + landmarks | Sampling for inference | Not VR | Inference thms | Very small in examples | Designed for high-\(d\) \(H_1\) | \(m\)-scale | GUDHI | No | No | Lean \(H_1\) | GUDHI yes |
| **Cubical** | Grids / images | Rectangular domain | n/a | n/a (different input) | Linear in voxels | Grid dim \(d\) | Linear | Many | cuCube 2D | DIPHA MPI | Correct for images | Strong |
| **Morse-reduced** | Any filtered cells | Matching quality | **E** if input is VR | **E** if input is Čech | Heuristic \(m\ll n\) | n/a | Depends on matching | Perseus (old) | Apparent on GPU | Hard | = input | Idea lives; Perseus stale |
| **Apparent pairs** | Implicit on VR / cubes | Simplex order | **E** | n/a | Skips most columns | n/a | Already in Ripser | Ripser et al. | Ripser++, cuCube | Local tests | = input | Production |
| **Reduced / distilled VR** | Distance matrix | Doubling helps size | **E** (stated degrees) | Same as VR | \(O(n^2)\) triangles (H1, doubling) | Weak | Memory-oriented | Research | Designed parallel | Unknown | = VR | Preprint only |
| **Sparse Čech / digitization** | Euclidean fixed \(d\) | Euclidean | A to VR via Čech | **A** \((1+\varepsilon)\) | \(n(1/\varepsilon)^{O(d)}\) | Fixed-\(d\) theory | Linear \(n\) | Research | No | No | Approx offsets | No product impl. |

---

## 11. Implementation map (complex \(\times\) library)

| | Ripser | Ripser++ | giotto-ph | GUDHI | Ripserer.jl | Oineus | DIPHA | Dionysus 2 | HomCloud | CubicalRipser | Perseus | SimBa |
| --- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| VR implicit | ● | ● | ● | | ● | ● | | | wraps Ripser | | | |
| VR explicit | | | | ● | | | ● | ● | | | ● | |
| Edge collapse | | | ● | ● | | | | | | | | |
| Sparse Rips | | | | ● | ● | | | | | | | |
| Alpha / Delaunay | | | | ● | | | input matrix | ● | ● | | | |
| Čech | | | | ● | | | | ● | | | | |
| Witness | | | | ● | | | | | | | | |
| Cubical | | | | ● | ● | ● | ● | | ● | ● | ● | |
| Morse preprocess | apparent | apparent | apparent | collapse | `find_apparent_pairs` | | | | | apparent | ● | batch maps |
| GPU | | ● | | | | | | | | | | |
| MPI / cluster | | | | | | | ● | | | | | |

Maintenance shortlist for dependencies: **GUDHI, Ripser, HomCloud, Dionysus 2, CubicalRipser, Ripserer.jl, Oineus** are alive in 2025–2026. **JavaPlex** and **Perseus** are historical. **SimBa** is unsupported. **Ripser++** is the GPU *reference*, not necessarily the future core. **Distilled VR** has no library.

---

## 12. Recommendation: first benchmark round

Keep two tracks. Do not force every complex onto every dataset.

### Track A — Euclidean low dimension (\(d\le 3\), exploratory \(d=4\))

| Keep | Why | Equivalence class in the protocol |
| --- | --- | --- |
| **VR (Ripser, plus giotto-ph and/or GUDHI)** | Reference estimator; implicit apparent-pair baseline. | Exact VR. |
| **Edge-collapsed VR (GUDHI or giotto-ph, then expand / Ripser-style PH)** | Same diagrams as VR; measures how much *exact* work reduction the 1-skeleton admits. | Exact VR. Require diagram equality. |
| **Alpha and/or Delaunay–Čech (GUDHI)** | Exact offset / Čech PH; the only cheap exact geometric nerve in low \(d\). | Exact Čech/offsets. Compare to VR via interleaving / bottleneck, **not** equality. |
| **Cubical (CubicalRipser or GUDHI)** | Only when the datum *is* a grid (or a documented voxelization experiment). | Exact cubical (record V vs T). |

Skip as first-round *engines* on this track: full Čech (Alpha already has the same module), witness (redundant once Alpha and VR exist, except as a landmark sanity check), sparse Rips (the exact methods still fit).

### Track B — high-\(d\) Euclidean and general metrics

| Keep | Why | Equivalence class |
| --- | --- | --- |
| **VR (Ripser / Ripser++ / giotto-ph)** | Only general exact reference. GPU row = Ripser++. | Exact VR. |
| **Edge-collapsed VR** | Strongest *exact* size cut that is implemented and metric-agnostic. | Exact VR. |
| **Sparse Rips (GUDHI, a few \(\varepsilon\in(0,1)\))** | Only maintained linear-size VR approximation with a written interleaving. | Approx VR; log-bottleneck vs Ripser on instances Ripser can finish. |
| **Lazy witness + maxmin landmarks (GUDHI 1-skeleton + expansion)** | Standard landmark baseline; cost \(\sim m\) not \(n\). | Empirical vs VR; no equality. |

Optional one-off (not a dependency): GIC on a high-d \(H_1\) example from the GUDHI docs, to see a lean landmark complex that is not lazy VR.

Skip: Alpha / Delaunay (infeasible or meaningless), cubical (wrong data type), SimBa (unmaintained), distilled / reduced VR (no library yet — schedule as a *design* experiment after the first numbers), strong collapse (dominated by edge collapse), research sparse Čech.

### What the first round is for

1. Confirm VR codes agree (class: exact same filtration).
2. Confirm edge collapse agrees with VR and record edge / simplex / time / memory ratios.
3. On low-\(d\) Euclidean data, measure Alpha vs VR: cost ratio and bottleneck (expected nonzero).
4. On high-\(d\) / metric data, measure Sparse Rips and lazy witness vs VR while VR still runs; then push \(n\) where only the reduced / approximate families finish.
5. Identify whether the bottleneck is **graph construction**, **expansion**, or **column reduction** — that decides whether the next algorithm should look like collapse, like Morse/distilled VR, or like Ripser++-style parallel apparent pairs.

---

## 13. Strongest \(10\times\)-work-reduction candidates

“Work” here means cells, columns, or reduction operations, not FLOPs from a CUDA port. Ordered by a combination of **proven exactness**, **observed reduction**, and **implementability**.

1. **Edge-collapsed VR (exact)**  
   \(\sim 12\)–\(30\times\) fewer edges in the SoCG 2020 suite; simplex count can fall as \(\sim\rho^{k}\). Already in GUDHI / giotto-ph. First thing to measure on *our* data. If we see \(\ge 10\times\) fewer edges at the thresholds we care about, this is the default preprocess for every exact VR run.

2. **Alpha instead of VR in \(d\le 3\) (exact for offsets, not for VR)**  
   From \(\Theta(n^{k+1})\) to \(O(n)\)–\(O(n^2)\) cells. Often far more than \(10\times\) at \(H_1/H_2\). Valid only on Euclidean low-\(d\) and only if the scientific target is offset / Čech PH. For a *new VR algorithm* this is a baseline, not a kernel.

3. **Apparent pairs / implicit Morse (exact, already inside Ripser)**  
   Frequently removes the majority of columns. Any new representation should expose a local pairing test of this type (or reuse it). GPU-friendly. Distilled VR is the “make the Morse complex explicit and smaller” sequel.

4. **Sparse Rips / net-tree sparsification (approximate)**  
   Asymptotic \(O(n^{k+1})\to O(n)\). Real \(10\times\) needs moderate doubling dimension and a not-too-small \(\varepsilon\). First-round GUDHI `sparse=` sweep will tell us whether the constants are usable on our metrics.

5. **Landmark / lazy witness / GIC (different estimator)**  
   Work scales with \(m=\|L\|\). \(m=n/10\) is already a \(10^{k}\) cut in the \(k\)-skeleton if one were comparing full VR on \(n\) vs VR-like expansion on \(m\). Information loss is not controlled like Sheehy’s \(\varepsilon\).

6. **Cubical vs triangulated images (exact for grids)**  
   Linear cells vs a simplicial blow-up of the same grid. Relevant only on image / volume benchmarks.

7. **Reduced / distilled VR (exact, research)**  
   Documented \(O(n^3)\to O(n^2)\) triangles for \(H_1\) under doubling (reduced VR); distilled adds a Morse cut for memory and parallel reduction. Strongest *new-algorithm* candidate if first-round numbers show memory / unpaired columns as the wall after edge collapse. Not available as a library for the first benchmark.

**Not a \(10\times\) candidate by itself:** rewriting Ripser in another language, or a CUDA port of the same columns (Ripser++). That is an implementation gain. It should still be measured, on a separate axis from structural reduction.

**Combinations that look compatible**

- Edge collapse \(\to\) implicit Ripser-style PH on the collapsed flag filtration (exact). GUDHI already advertises “Rips dim 1 \(\to\) `collapse_edges` \(\to\) `expansion`.”
- Edge collapse \(\to\) apparent-pair reduction (exact). Natural CPU core.
- Sparse Rips *or* landmarks \(\to\) edge collapse (approximate then exact-on-the-approximation). Only if the approximation is the chosen estimator.
- Apparent-pair Morse \(\to\) distilled complex (exact). Research path.
- Alpha and VR in parallel on low-\(d\) data, never mixed into one “accuracy” number.

**Likely incompatibilities**

- Delaunay / Alpha with general distance matrices.
- Cubical with unstructured clouds (without a defined voxelization).
- Comparing Sparse Rips or witness diagrams to Ripser with an equality test.
- Distributing independent subset VR and claiming global VR PH.

---

## 14. Primary sources

| Paper | Year | Where | Technique | Read for |
| --- | --- | --- | --- | --- |
| Edelsbrunner–Mücke, Three-dimensional alpha shapes | 1994 | *ACM Trans. Graph.* | Alpha | Geometry of \(A_r\) |
| Edelsbrunner–Letscher–Zomorodian, Topological persistence and simplification | 2002 | *DCG* | Persistence + alpha | Original PH algorithm |
| de Silva–Carlsson, Topological estimation using witness complexes | 2004 | SPBG | Witness / lazy | Landmark idea; no correctness proof |
| Kaczynski–Mischaikow–Mrozek, *Computational Homology* | 2004 | Springer | Cubical | Cubical chains |
| Zomorodian–Carlsson, Computing persistent homology | 2005 | *DCG* | Matrix reduction | Algebraic baseline |
| Sheehy, Linear-size approximations to the VR filtration | 2012/13 | SoCG / *DCG*; [arXiv:1203.6786](https://arxiv.org/abs/1203.6786) | Sparse Rips | \((1+\varepsilon)\), \(O(n)\), doubling |
| Chazal–de Silva–Oudot, Persistence stability for geometric complexes | 2014 | *Geom. Dedicata*; [arXiv:1207.3885](https://arxiv.org/abs/1207.3885) | Stability | VR / Čech / witness vs \(d_{\mathrm{GH}}\) |
| Dey–Fan–Wang, Graph induced complex | 2013 | SoCG; [arXiv:1304.0662](https://arxiv.org/abs/1304.0662) | GIC | Lean landmark complex |
| Mischaikow–Nanda, Morse theory for filtrations | 2013 | *DCG* | MorseReduce | Exact Morse PH |
| Cavanna–Jahanseir–Sheehy, A geometric perspective on sparse filtrations | 2015 | CCCG | Sparse Rips/Čech | GUDHI’s variant |
| Dey–Shi–Wang, SimBa | 2016 | ESA; [arXiv:1609.07517](https://arxiv.org/abs/1609.07517) | Batch collapse | Practical high-d approx |
| Bauer, Ripser | 2021 | *JACT*; [arXiv:1908.02518](https://arxiv.org/abs/1908.02518) | Implicit VR, apparent pairs | Reference algorithm |
| Boissonnat–Pritam, Strong collapses of flag complexes | 2019 | SoCG | Vertex collapse | Ancestry of edge collapse |
| Boissonnat–Pritam, Edge collapse and persistence of flag complexes | 2020 | SoCG | Edge collapse | Exact flag reduction |
| Zhang et al., Ripser++ | 2020 | [arXiv:2003.07989](https://arxiv.org/abs/2003.07989) | GPU apparent pairs | GPU baseline |
| Kaji et al., CubicalRipser | 2020 | [arXiv:2005.12692](https://arxiv.org/abs/2005.12692) | Cubical Ripser | Image PH |
| Koyama–Mémoli–Robins–Turner, Reduced VR | 2024 | [arXiv:2307.16333](https://arxiv.org/abs/2307.16333) | Reduced VR | Exact \(H_1\), fewer triangles |
| Koyama–Robins–Turner, Distilled VR | 2024 | [arXiv:2412.07805](https://arxiv.org/abs/2412.07805) | Morse on reduced VR | Exact, memory, parallel |
| GUDHI manuals | 3.13.x | [gudhi.inria.fr](https://gudhi.inria.fr/) | All complexes above that GUDHI ships | Conventions, sparse \(\varepsilon\), collapse API |

Official docs consulted: GUDHI Rips, Sparse Rips, Edge collapse, Alpha / Delaunay, Čech, Witness, Cubical, Cover/GIC; Ripser paper; CubicalRipser README; Oineus README; Ripserer.jl changelog; HomCloud 5.4 news; Dionysus 2 docs.

---

## 15. Decision (for this stage)

- **Exact VR baseline:** Ripser (CPU) and Ripser++ (GPU), with giotto-ph as the parallel-CPU / collapse-enabled VR code.
- **Exact VR reduction to measure first:** edge-collapsed flag filtrations (GUDHI).
- **Exact geometric baseline on low-\(d\) Euclidean data:** Alpha (GUDHI), not full Čech.
- **Exact grid baseline:** CubicalRipser / GUDHI cubical, only on grid data.
- **Approximate metric baseline:** GUDHI sparse Rips + lazy witness (two different approximation philosophies: net-tree interleaving vs landmarks).
- **Do not build a new algorithm on Delaunay in high \(d\), on cubical for clouds, or on unmaintained SimBa.**
- **Most promising structural idea for a later CPU core:** edge collapse + Ripser-style apparent pairs, with reduced/distilled VR as the research branch if collapse + implicit reduction still dies on memory / unpaired columns.
