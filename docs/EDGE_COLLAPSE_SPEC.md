# Filtration-preserving edge collapse for flag / Vietoris–Rips complexes

Implementable specification of the exact 1-skeleton reduction of
Boissonnat–Pritam (SoCG 2020) as clarified by Glisse–Pritam (2022) and as
shipped by GUDHI (`Flag_complex_edge_collapser`, 2021 rewrite) and
giotto-ph. After this note, the 1-skeleton collapse can be coded without
re-opening the PDFs.

Status: extracted from the papers and from the inspected implementations
(2026-10-13). No new theorem is claimed.

| Source | Role |
| --- | --- |
| Boissonnat–Pritam, *Edge Collapse and Persistence of Flag Complexes*, SoCG 2020, [LIPIcs.SoCG.2020.19](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SoCG.2020.19); local `papers/boissonnat-2020-edge-collapse.pdf` | Dominated simplex, Lemma 2 (flag test), Theorem 4 (PH), Algorithm 1 (forward), complexity \(O(n n_c k^2)\) |
| Glisse–Pritam, *Swap, Shift and Trim to Edge Collapse a Filtration*, arXiv:2203.07022; local `papers/glisse-2022-edge-collapse-extensions.pdf` | Swap / Shift / Trim lemmas; backward Algorithm 1 (what GUDHI runs); approximation; zigzag; complexity \(O(n_e k^3)\) |
| Boissonnat–Pritam–Pareek, *Strong Collapse for Persistence*, arXiv:1809.10945; local `papers/boissonnat-2018-strong-collapse.pdf` | Ancestry: 0-collapse (dominated *vertices*). Different algorithm; produces a tower, not a flag filtration |
| GUDHI `src/Collapse/include/gudhi/Flag_complex_edge_collapser.h` (SHA `1c4ba125`, 2026-10-12) | Production backward implementation. Comment: “Flag complex sparse matrix data structure.” Authors Pritam / Glisse rewrite 2021 |
| giotto-ph `gph/src/Flag_complex_edge_collapser.h` (v0.2.4) | Forward Algorithm 1 of 2020; AGPL; do not vendor |
| GUDHI tests: `src/Collapse/test/collapse_unit_test.cpp`, `src/Collapse/example/edge_collapse_basic_example.cpp` | Ground-truth tiny graphs |

The PDF extractors render the neighborhood intersection as a backslash.
In both papers, \(N_G[xy] := N_G[x] \cap N_G[y]\) (see the displayed
formula \(N_G[\sigma] := \bigcap_{v_i \in \sigma} N[v_i]\) and Lemma 2).
GUDHI’s `common_neighbors` is a sorted-list intersection. **Use
intersection, never set difference.**

---

## 0. Input / output contract

**Input.** An undirected filtered graph, given as a list of triples
\((u, v, t)\) with \(u \neq v\) integer vertex ids and
\(t \in \mathbb{R}\) (or a totally ordered filtration type). This *is*
the 1-skeleton of a flag filtration \(\mathcal{F}\): at scale \(t\),

\[
G_t = \bigl\{ \{u,v\} \;\big|\; t(\{u,v\}) \le t \bigr\},
\qquad
K_t = \mathrm{Flag}(G_t).
\]

Vietoris–Rips (diameter convention) is the special case
\(t(\{p,q\}) = d(p,q)\). Vertex filtration values are ignored
(GUDHI: “the filtration value of vertices is irrelevant”). Isolated
vertices are untouched.

**Output.** A (usually strictly smaller) list of triples
\((u, v, t')\) with \(t' \ge t\) on each surviving edge, defining a
flag filtration \(\mathcal{F}^c\) such that, in every homological
degree and over every field,

\[
\mathrm{PH}(\mathcal{F}^c) \;\cong\; \mathrm{PH}(\mathcal{F}).
\]

Some input edges are **deleted** (\(t' = +\infty\)). Some are
**delayed** (\(t < t' < +\infty\)). Some are copied unchanged.
The residual is still a flag filtration (2020 Lemma 3), so any VR /
Ripser-style engine can consume it as a sparse distance graph.

**Preconditions (undefined otherwise).**

- No self-loop \(u = v\).
- No duplicate unordered pair \(\{u,v\}\) (listing both \((i,j,t)\)
  and \((j,i,t')\) is undefined; GUDHI Python docs).
- Undirected: if the source distances are asymmetric, symmetrize
  *before* collapse (e.g. \(t \leftarrow \max(d_{ij}, d_{ji})\)) and
  document it. Directed flag complexes are a different object
  (flagser); this spec does not apply to them.
- Missing pair = edge absent, i.e. filtration \(+\infty\).

**One pass is exact for PH, not 1-core-minimal.** Running the
algorithm a second time on its own output can delete / delay more
edges (2022 “Optimality”; GUDHI `nb_iterations`). Each additional
pass remains exact. There is no claim that the greedy output is the
smallest possible equivalent flag filtration.

---

## 1. Exact mathematical definition of a dominated edge

### 1.1 Unfiltered flag complex

Let \(G = (V,E)\) be a simple undirected graph and
\(K = \mathrm{Flag}(G)\). Write \(N(x)\) for the open neighborhood of
a vertex and \(N[x] := N(x) \cup \{x\}\) for the closed neighborhood.

For an edge \(e = \{a,b\} \in E\):

\[
N[e] \;:=\; N[a] \cap N[b],
\qquad
N(e) \;:=\; N[e] \setminus \{a,b\}.
\]

\(N[e]\) always contains \(a\) and \(b\). \(N(e)\) is the set of
**common neighbors** of the two endpoints.

**Definition (dominated simplex, 2020).** A simplex \(\sigma \in K\)
is *dominated* by a vertex \(v' \notin \sigma\) if the link
\(\mathrm{lk}_K(\sigma)\) is a simplicial cone with apex \(v'\):
there is a subcomplex \(L\) with \(\mathrm{lk}_K(\sigma) = v' L\).
Notation: \(\sigma \prec v'\).

**Lemma 1 (2020, maximal-simplex test, any complex).**
\(\sigma \prec v'\) if and only if every maximal simplex that
contains \(\sigma\) also contains \(v'\), i.e.
\(v' \in \bigcap \Sigma_\sigma\).

**Lemma 2 (2020, 1-skeleton test, flag complexes only).**
For \(\sigma \in K = \mathrm{Flag}(G)\),

\[
\sigma \prec v'
\quad\Longleftrightarrow\quad
N[\sigma] \subseteq N[v'],
\]

where \(N[\sigma] := \bigcap_{x \in \sigma} N[x]\).

Specializing to an edge \(e = \{a,b\}\):

\[
\boxed{\;e\text{ is dominated by }v'\notin e
\;\Longleftrightarrow\;
N[a]\cap N[b] \;\subseteq\; N[v'].\;}
\]

Equivalent forms, all used in code:

1. **Closed-neighborhood inclusion.** \(N[e] \subseteq N[v']\).
2. **Common-neighbor form (what GUDHI tests).** Let
   \(C = N(e)\). Then \(e\) is dominated iff \(C \neq \emptyset\) and
   there exists \(c \in C\) such that every \(w \in C\) is equal to
   \(c\) or adjacent to \(c\). (The endpoints \(a,b\) sit in \(N[c]\)
   automatically because \(c \in C\).)
3. **GUDHI prose.** “All the vertices that have an edge with both
   vertices of \(e\) also have an edge with \(v'\).”
4. **Link is a cone.** \(\mathrm{lk}_K(e) = v' L\).

If \(C = \emptyset\) (no common neighbor), \(e\) is **never**
dominated. In particular every edge of a chordless cycle is
undominated.

**Elementary edge collapse (1-collapse).** Delete a dominated edge
\(e\) *and all of its cofaces*. The residual is still a flag complex
(2020 Lemma 3). An elementary 1-collapse decomposes into elementary
simple collapses (Welker 1999, Lemma 2.7; Attali–Lieutier–Salinas
2013, Lemma 8) and is therefore a strong deformation retract.

A 0-collapse (delete a *dominated vertex*) is the strong collapse of
Barmak–Minian / Boissonnat–Pritam 2018–2019. It is the \(k=0\) case
of the same definition, \(N[v] \subseteq N[v']\). It is **not** the
algorithm specified here: on a filtration it produces a tower of
simplicial maps, not a flag filtration.

### 1.2 Filtered flag complex (the condition the code must test)

Let each edge carry a filtration value \(t(e)\). At time \(t\),
neighborhoods use **only edges with filtration \(\le t\)**:

\[
N_t[x] \;:=\; \{x\} \cup \bigl\{ y \;\big|\; t(\{x,y\}) \le t \bigr\},
\qquad
N_t[e] \;:=\; N_t[a] \cap N_t[b].
\]

**Dominated at time \(t\).** An edge \(e = \{a,b\}\) with
\(t(e) \le t\) is dominated in \(G_t\) iff there exists
\(v' \notin e\) such that \(N_t[e] \subseteq N_t[v']\).

Implementable predicate (open form, matches
`Flag_complex_edge_collapser::is_dominated_by`):

```
dominated_at(e={a,b}, t):
    C ← { w ∉ {a,b} | t({a,w}) ≤ t and t({b,w}) ≤ t }
    if C is empty: return false
    for c in C:
        if ∀ w in C:  w = c  or  t({c,w}) ≤ t:
            return true          # c dominates e at time t
    return false
```

Self-time convention: \(t(\{c,c\}) := -\infty\), so the
\(w = c\) case always holds. GUDHI stores this as a closed
neighborhood with a self-loop of filtration \(-\infty\).

### 1.3 What the reduction does to a filtration

Inserting a dominated edge does not change homology at that grade
(the inclusion \(K_t \setminus e \hookrightarrow K_t\) is a homotopy
equivalence). Three elementary operations therefore preserve the
persistence *diagram* (2022 Lemmas 1–3):

| Operation | Statement | Effect on the edge list |
| --- | --- | --- |
| **Swap** | Edges with the *same* filtration value may be reordered | permute a same-\(t\) block |
| **Shift** | If \(e\) is dominated in \(G_{t_i}\), delay its insertion to the next grade \(t_{i+1}\) | replace \(t(e)\) by \(t_{i+1}\) |
| **Trim** | If the last edge of the filtration is dominated, delete it | drop \(e\) (shift to \(+\infty\)) |

**Adjacency (2022 Lemma 4).** If \(e\) is dominated in \(G\) and a
new edge \(e'\) does not share a triangle with \(e\)
(\(N(e) = N'(e)\)), then \(e\) stays dominated in \(G \cup e'\).
Hence a shift may jump directly to the next time a *common neighbor*
appears, skipping unrelated grades. GUDHI implements this with the
`e_ngb_later` heap.

Any algorithm that rewrites the edge list by a finite sequence of
Swap / Shift / Trim produces a flag filtration with the same
persistence diagram as the input (2022 Theorem 5). Both the 2020
forward algorithm and the 2022 backward algorithm are such
sequences. They are exact in **every** homological degree.

They are **not** required to produce the same remaining *edges* when
several edges share a filtration value (2022 Table 1, complete graph
on 900 vertices: forward 24 540 vs backward 5 980). When all
filtration values are distinct, both algorithms output the same list.

---

## 2. Proof sketch that persistent homology is preserved

Citations are to *Edge Collapse and Persistence of Flag Complexes*
(SoCG 2020) and *Swap, Shift and Trim* (2022).

**Step A — one collapse is a homotopy equivalence.**
A \(k\)-collapse is an “extended collapse” (Attali–Lieutier–Salinas).
Each elementary \(k\)-collapse decomposes into elementary simple
collapses (Welker, Lemma 2.7; ALS 2013, Lemma 8). A simple collapse
is a strong deformation retract of geometric realizations
(\(|K| \simeq |K \setminus \sigma|\)). In particular an edge collapse
induces isomorphisms \(H_p(K \setminus e) \xrightarrow{\sim} H_p(K)\)
in every degree \(p\).

**Step B — collapses compatible with a map preserve persistence
(2020 Theorem 4).**
Let \(f \colon K \to L\) be simplicial and let \(K \searrow K'\),
\(L \searrow L'\) be simple collapses, with deformation retractions
\(|r_K|\), \(|r_L|\) and inclusions \(|i_K|\), \(|i_L|\). The induced
map \(|f'| := |r_L| \circ |f| \circ |i_K|\) makes the homology square
commute up to homotopy (\(|i_K| \circ |r_K| \simeq \mathrm{id}_K\)),
and the vertical maps are isomorphisms. Hence
\(f_* \colon H_p(K) \to H_p(L)\) and
\(f'_* \colon H_p(K') \to H_p(L')\) define the same persistence
module. (The argument is written in singular homology because the
retraction of a simple collapse is not itself a simplicial map;
simplicial and singular homology agree on complexes.)

Naive application of Theorem 4 to each \(K_t\) independently would
yield a *tower*, not a filtration — that was the cost of strong
(vertex) collapse in 2018–2019. Edge collapse of a *filtration* is
restricted so the residual stays nested.

**Step C — Swap / Shift / Trim are Theorem 4 plus reindexing
(2022 §§3, A).**

- *Shift.* If \(e\) is dominated in \(G_{t_i}\), the inclusion
  \(G_{t_i} \setminus e \hookrightarrow G_{t_i}\) is a homotopy
  equivalence, so the module
  \(H(G_{t_{i-1}}) \to H(G_{t_i}) \to H(G_{t_{i+1}})\) is isomorphic
  to \(H(G_{t_{i-1}}) \to H(G_{t_i} \setminus e) \to H(G_{t_{i+1}})\).
  No non-trivial interval can start or end at a grade whose incoming
  map is an iso, so replacing \(t_i(e)\) by any value in
  \([t_{i-1}, t_{i+1}]\) does not change the diagram (2022 Lemma 10).
- *Swap.* Equal-filtration edges may be exchanged; this is a vineyard
  transposition at a repeated critical value and only creates /
  destroys zero-persistence pairs on the diagonal (2022 Lemma 11).
- *Trim.* Deleting a dominated last edge is Shift to \(+\infty\)
  (2022 Lemma 12).

**Step D — the algorithms only apply C.**
The backward algorithm (GUDHI) considers edges from the largest
filtration downward. While the current edge is treated as last at
its grade (implicit Swap), the code either Trims it, or Shifts it to
the next time a common neighbor appears (Adjacency), or outputs it
as critical. Inductively every rewrite is an operation from C, so
2022 Theorem 5 gives \(\mathrm{PD}(\mathcal{F}^c) = \mathrm{PD}(\mathcal{F})\).

The 2020 forward algorithm is the same operations in the other
direction: a “train” of dominated edges is shifted right until a
primary critical edge stops the ones that become non-dominated
(secondary critical, new filtration = the stopper’s time); the
train leftover at the end is trimmed. 2020 Theorem 8 + Lemma 7 is
the corresponding statement.

**What this does *not* prove.** The residual need not be
1-collapse-minimal. Different execution orders (and forward vs
backward, when ties exist) can yield different 1-skeletons with
the same barcode. The reduction is exact for the *flag filtration
of the given 1-skeleton*, not for a different complex (Čech, Alpha,
directed flag, a Witness complex, …).

---

## 3. Sequential algorithms

Two production sequential algorithms exist. **Implement the
backward one** (GUDHI 2021 / Glisse–Pritam 2022). It is faster in
the published tables, simpler, and is what `gudhi::collapse` runs
today. giotto-ph still ships the 2020 forward algorithm; when all
\(t(e)\) are distinct the two outputs coincide.

### 3.1 Backward algorithm (GUDHI, recommended)

Input: vector `E` of triples `(u, v, t)` with `u != v`.
Output: vector `Ec` of surviving triples, unsorted.

```
BACKWARD-COLLAPSE(E):
    if E is empty: return []

    # 1. Normalise and index
    for each e in E: if u > v: swap(u, v)          # optional, for uniqueness
    n_v ← 1 + max vertex id in E
    sort E by t decreasing                       # ties: any order (see §5)

    # 2. Closed neighborhood maps (symmetric)
    # N[x] is a map  y ↦ t({x,y}), kept sorted on y
    N[0 … n_v) ← empty
    for (u, v, t) in E:
        N[u][v] ← t;  N[v][u] ← t
    for x in 0 … n_v-1:
        N[x][x] ← −∞                             # closed neighbourhood

    Ec ← []
    for e = (u, v, t_in) in E:                   # already high → low
        t ← t_in
        # Open common neighbours now / later
        C_now, C_later ← COMMON-NEIGHBORS(N, u, v, t)
        # C_now  : vertices w ≠ u,v with max(N[u][w], N[v][w]) ≤ t
        # C_later: pairs (max(N[u][w], N[v][w]), w) with that max > t

        loop:
            # Find any dominator of e at the current time t
            dominator ← none
            for c in C_now:
                if IS-DOMINATED-BY(N, C_now, c, t):
                    dominator ← c; break
            if dominator is none:
                Ec.append( (u, v, t_in if t == t_in else t) )
                if t ≠ t_in:
                    N[u][v] ← t; N[v][u] ← t     # delay in the maps
                break

            # e is dominated: shift to the next common-neighbour event,
            # or trim if none remain (2022 Adjacency / Trim)
            if C_later is empty:
                erase N[u][v] and N[v][u]        # trim
                break
            t ← min { τ | (τ, w) in C_later }
            move every (τ, w) in C_later with τ ≤ t into C_now
            # cheap check: if the old dominator still works, skip the
            # full scan on the next iteration (GUDHI does the full scan;
            # 2022 notes the cheap check as an optional win)

    return Ec


COMMON-NEIGHBORS(N, u, v, t):
    # simultaneous walk of two sorted maps (GUDHI)
    C_now ← []; C_later ← []
    for each w in keys(N[u]) ∩ keys(N[v]):
        if w == u or w == v: continue
        τ ← max(N[u][w], N[v][w])
        if τ ≤ t: C_now.append(w)
        else:     C_later.append((τ, w))
    return C_now, C_later


IS-DOMINATED-BY(N, C, c, t):
    # N[c] is sorted; C is sorted. GUDHI walks both.
    # Dense variant: for each w in C, reject if dense[w,c] > t.
    for w in C:
        if w not in N[c] or N[c][w] > t:
            return false
    return true
```

**Invariants the implementer must not “simplify” away.**

1. Process **strictly decreasing** filtration. Higher edges are
   finalized (kept at a final \(t'\), or deleted) *before* lower
   edges are considered. Lower, not-yet-processed edges stay in `N`
   at their *original* times. That is the induction of 2022
   Theorem 5. Do not first collapse the low edges.
2. After a delay, write the new \(t'\) back into `N` so later
   (lower) edges see the delayed value.
3. After a trim, erase both directions from `N`.
4. `C_now` is the *open* common neighborhood. The closed-neighborhood
   inclusion \(N_t[e] \subseteq N_t[c]\) is equivalent because
   \(c \in C_now\) already guarantees \(a,b \in N_t[c]\).
5. Optional dense \(n_v \times n_v\) array of filtration values
   (`GUDHI_COLLAPSE_USE_DENSE_ARRAY`): speeds `IS-DOMINATED-BY` on
   dense graphs; on sparse graphs the \(n_v^2\) fill dominates.
   Default off. Missing entry = \(+\infty\); diagonal = \(-\infty\).
6. GUDHI’s `Delay` functor is the exact-vs-approximate hook: the
   first domination check starts at `delay(t_in)` instead of
   `t_in`. Identity ⇒ exact. See §5.

**Worked control flow for one edge.**

```
t = t_in
compute C_now, C_later at t
while true:
    if no c in C_now dominates C_now at t:
        output edge at (t_in if never shifted else t); return
    if C_later empty:
        delete edge; return
    t = next event in C_later
    absorb new common neighbours into C_now
```

### 3.2 Forward algorithm (SoCG 2020 / giotto-ph)

Kept here so giotto-ph output and the 2020 paper can be read against
the same spec. Do not implement this as the default.

Edges are indexed \(e_1,\dots,e_n\) in **increasing** filtration
(ties broken by a fixed total order). \(G_i = \{e_1,\dots,e_i\}\).
`Ec` collects *critical* edges, each with a **critical index** \(j\)
(the grade at which it first becomes non-removable). Output
filtration of \(e_i\) is \(t(e_j)\). Non-critical edges
(\(j = +\infty\)) are trimmed.

```
FORWARD-COLLAPSE(E):
    sort E by t increasing
    Ec ← ∅
    for i = 1 … n:                               # insert e_i into G_i
        if e_i is NOT dominated in G_i:          # primary critical
            insert (e_i, critical_index = i) in Ec
            G ← G_i
            Enbd ← edge-neighbourhood of e_i in G_i
            # EN(e={u,v}) = { {x,y} | x ∈ {u,v}, y ∈ N[e] }
            for j = i-1 down to 1:
                if e_j already in Ec: continue
                if e_j ∉ Enbd:
                    G ← G \ e_j                  # still dominated, drop from temp G
                else if e_j is dominated in G:
                    G ← G \ e_j
                else:                            # secondary critical
                    insert (e_j, critical_index = i) in Ec
                    Enbd ← Enbd ∪ EN_G(e_j)
    return { (e, t(e_{j})) | (e, j) in Ec }
```

2020 Lemma 5 justifies restricting the backward search to `Enbd`:
a dominated edge that does not share a triangle with the newly
critical edge stays dominated. 2020 Lemma 6: a non-critical edge,
and a secondary-critical edge before its critical index, is
removable. 2020 Lemma 7: \(K_i \searrow\searrow_1 K^c_i\) for each
\(i\). Theorem 8: \(\mathrm{PD}(\mathcal{F}^c) = \mathrm{PD}(\mathcal{F})\).

giotto-ph stores this as a sparse adjacency (`Sparse_row_matrix`)
with an MSB flag “already critical” on the edge index; the first
edge is always emitted as critical. That is the 2020 algorithm, not
a different test.

### 3.3 Iterations

```
reduce(E, n_iter):
    for k = 1 … n_iter:
        E ← BACKWARD-COLLAPSE(E)
    return E
```

GUDHI default `nb_iterations = 1`. The 2022 complete-graph example
needs five passes to reach a 1-core (244 650 → 5 340 → 3 086 →
1 307 → 788 → 699). One pass already removes most edges and is the
right default before measuring.

### 3.4 Recommended pipeline

```
distance / threshold graph  →  collapse (1+ passes)  →  Ripser-style PH
                                                       on the residual flag filtration
```

This is GUDHI’s documented `Rips dim 1 → collapse_edges → expansion`
path, except a Ripser-style engine never needs the expansion: it
consumes the residual 1-skeleton directly. Do **not** expand the
*uncollapsed* VR graph into a simplex tree.

---

## 4. Data structures and complexity

### 4.1 Structures (mirror GUDHI 2021)

| Structure | Layout | Purpose |
| --- | --- | --- |
| `E` | `vector<tuple<V,V,F>>` | input / working edge list |
| `N[x]` | sorted map `V → F` (`flat_map` in GUDHI; `vector<pair>` + binary search is enough) | closed neighborhood of vertex \(x\), including \(N[x][x] = -\infty\) |
| `N_dense` (optional) | `vector<F>` of length \(n_v^2\), row-major, init \(+\infty\) | \(O(1)\) domination probes on dense graphs |
| `C_now` | sorted set / flat_set of vertices | open common neighborhood at the current time |
| `C_later` | binary heap of `(F, V)` keyed by *decreasing* time (GUDHI `cmp1`) | future common neighbors; pop equals the next shift target |
| `Ec` | `vector<tuple<V,V,F>>` | output; **not** sorted in the backward algorithm |

Vertex ids are integers in \(0 \ldots n_v-1\) after a dense relabel,
or raw ids with `n_v = 1 + max_id` (GUDHI). Relabeling is optional;
it only shrinks the dense array.

Do not store any simplex of dimension \(\ge 2\). Domination is a
graph test (Lemma 2).

### 4.2 Costs

Write \(n_e\) = number of input edges, \(n_v\) = number of vertices,
\(k\) = maximum degree in the *last* graph \(G_{t_{\max}}\),
\(n_c\) = number of *primary* critical edges (forward only).

| Algorithm | Time (paper) | Space | Notes |
| --- | --- | --- | --- |
| Forward (2020 Alg. 1) | \(O(n_e\, n_c\, k^2)\) | \(O(n_e)\) | each primary critical edge can trigger a backward scan of all earlier edges; each domination test is \(O(k^2)\) (scan \(\le k\) candidates, each an \(O(k)\) subset test on sorted lists) |
| Backward (2022 Alg. 1) | \(O(n_e k^3)\) | \(O(n_e)\) or \(O(n_v^2)\) dense | per edge: \(\le k\) shifts, each a domination test \(O(k^2)\) |
| One domination test | \(O(k)\) to build \(N[e]\); \(O(k^2)\) to try all candidate apices | — | building \(N[e]\) is a merge of two sorted neighborhoods, \(O(k)\) |
| Insert / delete an edge in `N` | \(O(k)\) on a sorted vector | — | |

The \(O(n_e k^3)\) bound is pessimistic (2022): a trimmed edge makes
later tests cheaper; a never-shifted critical edge costs only
\(O(k^2)\); after a shift, re-testing the previous dominator is
often enough. Empirically \(n_c \approx n_e / 20\) on the SoCG 2020
suite (netw-sc 8.4K→417, senate 2.7K→234, HIV 182K→6.9K,
torus 428K→14K).

### 4.3 Parallelism (out of scope for v1, recorded for later)

- Domination tests of *distinct* edges at a *fixed* snapshot are
  independent. The sequential dependence is the left-to-right
  (forward) or right-to-left (backward) rewrite of `N`.
- 2022 §5: divide the *time* axis, collapse the high half and the
  low half, then resume the high pass on the edges the low pass
  trimmed. Same output as sequential (Lemma 6). GUDHI does not
  ship this; a TBB prototype is mentioned.
- giotto-ph’s collapse is “largely sequential” (their paper); the
  lock-free part is the *Ripser remainder*, not collapse.
- Do not split the *point cloud* and collapse independently:
  that is a different (generally inequivalent) filtration.

---

## 5. Pitfalls

### 5.1 Tie-breaking

Same-\(t\) edges may be swapped freely (Swap lemma). The
**barcode is invariant**; the **remaining edge set is not**.

- GUDHI sorts with `t(a) > t(b)` only. `std::sort` is not stable;
  equal-\(t\) order is arbitrary. The official example
  (C4 + both diagonals at time 2) keeps one diagonal; *which*
  diagonal depends on that order. Both answers are correct.
- Forward vs backward can differ in **count** when many edges share
  a value (2022 complete graph, 900 vertices).
- A unit test that asserts a *specific* surviving edge among a
  same-\(t\) pair is flaky unless the comparator is a strict total
  order. Assert either (i) the barcode, or (ii) an invariant that
  does not depend on the swap (e.g. “exactly one of the two
  diagonals remains”, “exactly 5 edges”, “the unique strictly later
  diagonal is gone”).
- Recommended deterministic comparator for tests:

  ```
  key(e) = (−t, min(u,v), max(u,v))     # backward: decreasing t, then lex
  ```

### 5.2 Threshold / enclosing radius

Collapse of the graph \(\{ e \mid t(e) \le T \}\) is exact for the
**truncated** flag filtration, not for the untruncated one. If the
scientific target is full VR, either pass every finite edge or use
the enclosing-radius cutoff *of the original metric* (Ripser /
Henselman), which is exact for the complete finite metric space.
Do not collapse at \(T\) and then compare barcodes to untruncated
Ripser.

### 5.3 Directed vs undirected

The Lemma 2 test is for an **undirected** flag complex. Directed
flag complexes (flagser) use directed cliques; there is no
“common undirected neighborhood” test, and apparent pairs already
fail there for the same reason. Collapse as specified here on a
directed graph that was silently symmetrized is exact for the
*undirected* flag filtration of that symmetrization, nothing else.

### 5.4 When the reduction is NOT exact

| Situation | What you get |
| --- | --- |
| Default GUDHI / this spec, `Delay = id`, any `nb_iterations ≥ 1` | **Exact** VR / flag PH, all degrees |
| `Delay(t) = t + ε` (2022 §6; GUDHI `Delay` functor) | Modules \((0,\varepsilon)\)-interleaved, **not** equal. Start the first domination check at \(t+\varepsilon\); if the edge is *not* dominated there, keep the **original** \(t\) (do not shift the whole sequence). If it *is* dominated, resume exact backward from \(t+\varepsilon\) |
| Multiplicative rounding \(t \mapsto \alpha t\) or snap to a grid of step \(\varepsilon\) | Interleaving with the corresponding factor; 2022 Table 2 |
| Sparse Rips / Sheehy / landmarks *then* collapse | Exact for the *already approximate* filtration |
| One pass vs 1-core | Exact PH either way; residual may still contain dominated edges |
| Non-flag input (use Lemma 2 anyway) | **Wrong.** Lemma 2 needs the clique property. General complexes need Lemma 1 (maximal simplices) |
| Strong / vertex collapse (2018) | Exact PH but the output is a *tower*, not a flag filtration. Different algorithm |
| Comparing remaining *edges* across GUDHI vs giotto-ph on tied filtrations | May differ; barcodes must still match |
| `return_generators` + collapse in giotto-ph | API forbids it; not a math obstruction |
| Vertex-weighted filtrations that are not implied by incident edges | This algorithm ignores vertex times. If vertices enter after time 0 independently of edges, encode that *before* building \(E\) or do not claim exactness |
| Duplicate / self-loop / directed-asymmetric input | Undefined |
| Homology of a *different* complex (Čech, Alpha, cubical, Witness) | Unrelated. Collapse does not turn VR into Čech |

### 5.5 Implementation traps

- **PDF backslash is \(\cap\).** Implementing \(N[x] \setminus N[y]\)
  is a hard correctness bug.
- **Closed vs open.** The mathematical test uses closed
  neighborhoods. The code test uses the open common neighborhood
  plus “\(c\) is one of those neighbors.” Do not forget that a
  size-1 common neighborhood is *always* dominated (the unique
  common neighbor is the apex). Do not treat a size-0 neighborhood
  as dominated.
- **Processing order is part of the proof.** Collapsing low edges
  first, or testing domination in the *final* residual graph, is
  not the algorithm and is not covered by Theorem 5.
- **Delay writes back.** Forgetting to update `N` after a shift
  makes later domination tests read a stale (too-early) time.
- **Dense init cost.** Zeroing \(n_v^2\) entries can dominate a
  sparse instance (GUDHI comment). Gate it.
- **Floating keys.** Filtration comparisons must be consistent
  with the rest of the PH pipeline (the same `<` that Ripser will
  use). Do not re-square or re-sqrt distances during collapse.
- **Output order.** Backward output is insertion-order of the
  high-to-low scan, not sorted. Sort before comparing lists.
- **Iterations and identity.** `nb_iterations < 1` is a no-op in
  GUDHI Python. Treat `< 1` as a caller error in our API.
- **Higher faces.** `SimplexTree.collapse_edges` *discards*
  dimension \(\ge 2\) and does not put them back. If we ever wrap a
  simplex tree, document that. A Ripser-style consumer does not
  care.

### 5.6 When collapse is a bad idea

2022 §8: collapse before PH “helps a lot for dimension 2 or
higher”, is “a terrible idea” for dimension 0 only (union-find is
cheaper than the collapse), and is mixed for dimension 1. giotto-ph
reports cases where collapse does not pay. Measure; do not hard-wire
collapse in front of every \(H_0\) run.

---

## 6. Minimal test cases

Vertices are integers. Edges are written `(u, v, t)` with
\(u < v\). “Remaining” is an unordered multiset of triples.
Unless noted, one backward pass, `Delay = id`, deterministic
tie-break `(-t, u, v)`.

These are small enough to check by hand with the predicate of §1.2.
They are also the first unit tests the C++ implementation must pass
*before* any barcode comparison against Ripser.

### T1 — C4, nothing to collapse

```
#   1 —— 2
#   |    |
#   0 —— 3
E      = (0,1,1), (1,2,1), (2,3,1), (0,3,1)
remain = (0,1,1), (1,2,1), (2,3,1), (0,3,1)
```

Each edge has \(N(e) = \emptyset\), so none is dominated at time 1.
A chordless cycle is a 1-core. \(H_1\) is born at 1 and never dies.

### T2 — C4 + one late diagonal (unique later edge is deleted)

```
#   1 —— 2
#   | ×  |
#   0 —— 3
E      = (0,1,1), (1,2,1), (2,3,1), (0,3,1), (0,2,2), (1,3,2.1)
remain = (0,1,1), (1,2,1), (2,3,1), (0,3,1), (0,2,2)
# deleted: (1,3,2.1)
```

This is GUDHI `collapse_unit_test.cpp` (second graph) and the
official basic example with the second diagonal moved to 2.1 so the
winner is unique.

Why: process `(1,3)` first (largest \(t\)). Common neighbors
\(\{0,2\}\); \(0\)–\(2\) exists at 2, so \(0\) dominates. No later
neighbor → **trim** `(1,3)`. Then `(0,2)` at 2: common neighbors
\(\{1,3\}\), but `1–3` has been erased, so neither 1 nor 3 dominates
→ **keep** at 2. Cycle edges at time 1 have empty common
neighborhood → **keep**. PH: \(H_1\) born at 1, dies at 2. Same as
the uncollapsed K4-minus-an-edge (the later diagonal was a cone
from the moment it appeared).

### T3 — both diagonals at the *same* time (tie; do not pin which)

```
E      = (0,1,1), (1,2,1), (2,3,1), (0,3,1), (0,2,2), (1,3,2)
remain = the four cycle edges at 1, plus exactly one of
         { (0,2,2), (1,3,2) }
```

GUDHI’s printed example keeps `(0,2,2)`; a different equal-\(t\)
order keeps `(1,3,2)`. Assert `len == 5` and
`|(remain ∩ diagonals)| == 1`, not a specific diagonal.

### T4 — isolated triangle, all times equal

```
E      = (0,1,1), (1,2,1), (0,2,1)
remain = any 2 of the 3 edges, both at time 1
```

Each edge is dominated by the opposite vertex (size-1 common
neighborhood). Backward trims the first one it sees and the other
two lose their common neighbor, so they stay. Residual is a path
\(\simeq *\); the triangle is also \(\simeq *\). Assert
`len == 2` and trivial barcode, not a specific pair.

### T5 — triangle with a late closer (late edge trimmed)

```
E      = (0,1,1), (1,2,1), (0,2,2)
remain = (0,1,1), (1,2,1)
# deleted: (0,2,2)
```

At time 2 the closer is dominated by 1 and has no future neighbor
→ trim. At time 1 the path is undominated. PH is trivial on both
sides (path, then filled triangle).

### T6 — genuine delay (secondary critical)

Vertices \(0,1,2=a,3=w,4=z\).

```
E      = (0,2,1), (1,2,2), (0,1,3), (1,3,4), (3,4,5), (0,4,6), (0,3,7)
remain = (0,2,1), (1,2,2), (0,1,7), (1,3,4), (3,4,5), (0,4,6), (0,3,7)
# delayed: (0,1) from 3 → 7
# nothing deleted
```

Hand check of the backward scan (all times distinct):

| process | \(C_{\mathrm{now}}\) | verdict |
| --- | --- | --- |
| `(0,3)` at 7 | \(\{1,4\}\), \(1\)–\(4\) missing | keep at 7 |
| `(0,4)` at 6 | \(\emptyset\) (the other C4 edges are later) | keep at 6 |
| `(3,4)` at 5 | \(\emptyset\) | keep at 5 |
| `(1,3)` at 4 | \(\emptyset\) | keep at 4 |
| `(0,1)` at 3 | \(\{2\}\); later neighbour \(3\) at time 7 | dominated by 2 → shift to 7 → \(C=\{2,3\}\), \(2\)–\(3\) missing → **emit at 7** |
| `(1,2)` at 2 | \(\emptyset\) | keep |
| `(0,2)` at 1 | \(\emptyset\) | keep |

PH on both sides: everything contractible until time 6, then a
4-cycle \(0{-}1{-}3{-}4\) is born, and it dies at 7 when the
diagonal `(0,3)` (and the delayed `(0,1)`) appear. Barcodes must
match; the witness that collapse did a *shift* rather than a trim
is `t'(0,1) == 7`.

### T7 — empty / single edge / path

```
E = []                          remain = []
E = (0,1,1)                     remain = (0,1,1)
E = (0,1,1), (1,2,2)            remain = (0,1,1), (1,2,2)
```

No common neighbors anywhere.

### T8 — GUDHI Python negative-weight chord

```
E      = (0,1,0.1), (1,2,0.2), (2,3,0.3), (0,3,0.4), (1,3,−0.6)
remain = (0,1,0.1), (1,2,0.2), (1,3,−0.6)
# deleted: (2,3,0.3), (0,3,0.4)
```

The early chord `(1,3)` makes `(0,3)` a size-1 cone at 0.4 and
`(2,3)` a size-1 cone at 0.3; both trim. Matches
`test_collapse_edges.py` (`len == 3`).

### Oracle for any further graph

On instances small enough for Ripser on the *uncollapsed* graph
(\(n_v \le 40\), modest \(T\)):

1. collapse `E` → `Ec`;
2. run the same PH engine on `E` and on `Ec` (same field, same
   dimension cap, same threshold, same diameter convention);
3. require identical finite bars up to the engine’s tie-breaking
   of zero-length pairs (drop pairs with `birth == death`).

That is the only acceptance test that may pin *edges* to a library
oracle, and only when all \(t(e)\) are distinct (otherwise compare
barcodes, not edge lists, across GUDHI vs our code vs giotto-ph).

---

## 7. Recommended C++ API

Constraints: MIT tree, Ripser-style consumer, no Boost/CGAL
requirement, no AGPL giotto-ph sources. Header-only is acceptable
for v1. Vertex type is a signed integer; filtration is any
strict-weak-ordered arithmetic type that Ripser can also use
(`float` / `double`).

```cpp
#pragma once
#include <algorithm>
#include <limits>
#include <utility>
#include <vector>

namespace tda::collapse {

/// Undirected filtered edge. `u == v` is a precondition violation.
template <class Vertex, class Filtration>
struct FilteredEdge {
    Vertex u;
    Vertex v;
    Filtration t;
};

struct CollapseParams {
    /// Number of backward passes. Must be >= 1.
    int iterations = 1;
    /// Allocate an n_v × n_v table of filtration values.
    /// Faster on dense graphs; expensive on sparse graphs with n_v^2 >> n_e.
    bool dense_adjacency = false;
};

/// Identity: exact collapse (default).
template <class Filtration>
struct IdentityDelay {
    Filtration operator()(Filtration t) const { return t; }
};

/// Additive ε-approximation of Glisse–Pritam 2022 §6.
/// First domination check is at t+eps; if that fails, the original
/// t is kept. Output module is (0, eps)-interleaved with the input.
/// Do not use this when the caller asked for exact VR PH.
template <class Filtration>
struct AdditiveDelay {
    Filtration eps;
    Filtration operator()(Filtration t) const { return t + eps; }
};

/// Collapse a flag 1-skeleton.
///
/// Pre: no self-loops; each unordered pair appears at most once;
///      the graph is undirected (the implementation treats (u,v)
///      as {u,v} and writes both directions internally).
/// Post: the returned edges define a flag filtration with the same
///       persistence module as Flag(edges) when Delay is IdentityDelay.
///       Output is unsorted. Filtration values only increase.
///
/// `delay` is applied only to the *first* domination probe of each
/// edge (GUDHI's Delay functor). Identity ⇒ exact.
template <class Vertex,
          class Filtration,
          class Delay = IdentityDelay<Filtration>>
std::vector<FilteredEdge<Vertex, Filtration>>
collapse_flag_edges(
    std::vector<FilteredEdge<Vertex, Filtration>> edges,
    CollapseParams params = {},
    Delay delay = {});

/// Convenience: build edges from a dense n×n distance matrix
/// (only the strict upper triangle is read) and drop t > threshold.
/// `threshold` default +∞ means “all finite entries”.
template <class Filtration>
std::vector<FilteredEdge<int, Filtration>>
edges_from_distance_matrix(
    const Filtration* dist, int n,
    Filtration threshold = std::numeric_limits<Filtration>::infinity());

/// The Lemma 2 predicate, exposed for unit tests.
/// `closed_N[x]` is the sorted list of (y, t({x,y})) including (x, −∞).
/// Returns true iff {u,v} is dominated in G_t.
template <class Vertex, class Filtration>
bool edge_dominated_at(
    Vertex u, Vertex v, Filtration t,
    const std::vector<std::vector<std::pair<Vertex, Filtration>>>& closed_N);

}  // namespace tda::collapse
```

**Implementation file responsibilities** (when we write it):

- `collapse_flag_edges` is exactly §3.1, looped `params.iterations`
  times, with the first probe of each edge at `delay(t_in)`.
- Reject `u == v` and `iterations < 1` in debug (assert) and in
  tests; in release, skip self-loops and treat `iterations < 1` as
  “return the input unchanged” only if we decide to match GUDHI
  Python — prefer asserting, GUDHI’s silent no-op hid caller bugs.
- Do not depend on Boost. Sorted `vector<pair>` + `std::lower_bound`
  replaces `boost::container::flat_map` / `flat_set`.
- Do not vendor giotto-ph. The 2020 forward algorithm is specified
  above if a streaming variant is ever needed; it is not v1.

**Consumer contract with the Ripser kernel.**

```cpp
auto residual = tda::collapse::collapse_flag_edges(edges);
// residual is a sparse undirected distance graph.
// Feed it to implicit cohomology as the 1-skeleton; do not expand.
```

Thresholding, enclosing radius, and field characteristic stay on
the PH side. Collapse does not see them except insofar as the
caller already dropped edges above \(T\).

**Python surface (later, not required to implement the spec).**
A single function
`collapse_edges(row, col, data, iterations=1) -> (row, col, data)`
matching GUDHI’s `gudhi.flag_filtration.edge_collapse.reduce_graph`
is enough for barcode-vs-GUDHI tests. License: our code, MIT.

### Acceptance gates before this preprocessor is called “done”

1. T1–T8 pass on the C++ implementation.
2. On every tiny graph with distinct times, Ripser barcodes of
   `E` and of `collapse_flag_edges(E)` are equal
   (finite bars, \(H_0\)–\(H_2\), \(\mathbb{F}_2\)).
3. On a graph with a same-\(t\) pair (T3, T4), barcodes match and
   the edge-count invariant of the test holds.
4. `AdditiveDelay{eps}` on T2 with `eps` larger than `2.1 - 2`
   is *allowed* to drop `(0,2)` as well; the barcode then
   \(\varepsilon\)-interleaves, it must **not** be asserted equal.
   This guards against accidentally wiring the approximate functor
   into the exact path.

---

## 8. Pointers into the inspected code

| What | Where |
| --- | --- |
| Backward collapse (copy ideas, not Boost) | `/tmp/ph-frameworks/gudhi-devel/src/Collapse/include/gudhi/Flag_complex_edge_collapser.h` `process_edges`, `common_neighbors`, `is_dominated_by` |
| `Delay` hook / exact default | same file, `flag_complex_collapse_edges(edges, Delay)` and the identity overload |
| Forward collapse | `/tmp/ph-frameworks/giotto-ph/gph/src/Flag_complex_edge_collapser.h` `process_edges`, `edge_is_dominated`, `set_edge_critical` |
| Ripserer forward-style | `/tmp/ph-frameworks/Ripserer.jl/src/filtrations/edgecollapse.jl` `_not_dominated`, `_core_graph` |
| C++ tests (T1–T3 family) | `/tmp/ph-frameworks/gudhi-devel/src/Collapse/test/collapse_unit_test.cpp` |
| Official 5-edge example | `/tmp/ph-frameworks/gudhi-devel/src/Collapse/example/edge_collapse_basic_example.cpp` |
| Python `nb_iterations` | GUDHI `gudhi/flag_filtration/edge_collapse.py` `reduce_graph` |

GUDHI’s public name for the original 2020 structure was “flag
complex sparse matrix”; the 2021 rewrite kept that comment on
`Flag_complex_edge_collapser`. There is no remaining type named
`FlagComplexSparseMatrix` in current gudhi-devel. giotto-ph’s
private `Sparse_row_matrix` is that older layout.

---

## 9. What to implement first

1. `edge_dominated_at` + T1, T4, T5, T7 (no shift, predicate only).
2. `collapse_flag_edges` backward, one iteration, identity delay.
3. T2, T6, T8 (trim + delay).
4. T3 / T4 as barcode + count invariants.
5. Ripser-oracle equality on random distinct-time graphs,
   \(n_v \le 30\).
6. Only then: iterations, dense array, `AdditiveDelay`, a
   distance-matrix helper.

Do not implement the forward algorithm, zigzag collapse, or the
2022 divide-and-conquer parallel merge in v1. They are specified
above only so a later change can stay aligned with the papers.
