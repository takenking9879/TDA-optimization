# Methodology for LLM-assisted persistent homology research

This document extracts the *research process* of
[CrocSwap/integer-mult-bounds](https://github.com/CrocSwap/integer-mult-bounds)
and adapts it to Topological Data Analysis (TDA) persistent homology (PH).

It is a **process reference**, not a math transfer. Integer-multiplication
circuits, κ-exponents, Gaussian resampling, and tape models do **not** carry
over. What we reuse is how they organize proposals, search, evidence,
rejection, and reproducibility so an LLM can iterate without promoting
unchecked claims.

Inspected snapshot: cloned 2026-10-13 from
`https://github.com/CrocSwap/integer-mult-bounds` (default branch `main`).
Primary sources are cited by path or URL below.

---

## 0. Transferable practices (one-page summary)

Keep these habits. Drop their multiplication-specific objects.

1. **Pin an unmodified baseline.** They freeze OpenAI #109 at commit
   `adc7f1241b42e322a6451854ab7e4b4c146bf78a` under `upstream/` with SHA-256
   in `upstream/manifest.json`. We pin Ripser, Ripser++, GUDHI, etc. the same
   way: URL, license, commit, hash, purpose. Never silently edit the reference.

2. **Treat variations as alternatives, not a mutating stack.** Historical
   patches apply independently to the *unmodified* snapshot
   ([PATCHING.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/PATCHING.md)).
   For PH: keep each complex, collapse, or reduction idea as a named variant
   against the same datasets and pinned baselines.

3. **One selected result, many frozen checkpoints.** `certificates/selected-result.json`
   names the current reviewed witness; older κ values remain replayable via
   `certificates/checkpoints/` and `make frontierNNN-verify`. We need one
   *selected algorithm/config* plus frozen benchmark receipts.

4. **Separate search from acceptance.** Floating-point or heuristic search
   may nominate candidates; acceptance uses exact or justified checks
   (`scripts/certify.py`: “No floating-point arithmetic is used in a
   certificate”). For PH: search may minimize simplex/column counts; a claim
   of exact persistence requires diagram identity or a theorem.

5. **Write the scope on every claim.** README and reviews repeat: this is
   *conditional*, *not a runtime benchmark*, *not a complete Lean theorem*,
   *not independent peer review*. We must label every result:
   implementation / structural / theoretical, and
   exact / theoretically approximate / empirically similar / unverified.

6. **Archive failures with retry conditions.**
   `research/experiment-log/` keeps losers, timeouts, and environment errors
   in different buckets. A time limit is not infeasibility; a finite no-gain
   search is not a global impossibility; a compiler error is not a
   mathematical rejection.

7. **Do not overwrite history.** Supersede with a new entry. Keep successful
   and failed runs together so the baseline stays reconstructable
   (`ENTRY-TEMPLATE.json` field `supersedes`).

8. **Charge every cost.** Their proofs reject “free” savings that omit
   restoration, routing, or fallback. For PH: a collapse that drops simplices
   must still pay construction, filtration encoding, and any extra
   bookkeeping. Wall-clock wins that increase work are implementation, not
   algorithm.

9. **Integrate research that does not change the headline.**
   `docs/research/research-notes-20261011.md`: “No change to the selected κ.
   Research notes, negative results… are integrated on their own merits.”
   Negative PH screens, tooling, and papers belong in the log even when the
   selected complex stays Vietoris–Rips + Ripser.

10. **Replay must regenerate artifacts.** `make verify` rewrites certificates
    and fails if `git diff` is nonempty. Our benchmarks must regenerate
    receipts; committed numbers that cannot be rebuilt are not evidence.

11. **Record local vs CI separately.** Integration JSON files distinguish
    maintainer laptop runs from Linux CI. Missing GPU here is a recorded
    limit, not a fabricated result.

12. **Credit and pin dependencies.** `CONTRIBUTORS.md`, `NOTICE`,
    `SOURCES.json`, and per-PR heads in `selected-result.json`. For PH:
    paper, library, dataset license, and commit of every comparison target.

That is the whole transferable core. The rest of this file makes it
operational for this repository.

---

## 1. Source and inspection scope

| Artifact | URL / path | Role |
|---|---|---|
| Repository | https://github.com/CrocSwap/integer-mult-bounds | Community research on OpenAI problem #109 |
| README | https://github.com/CrocSwap/integer-mult-bounds/blob/main/README.md | Selected result, checkpoints, limits, reproduce commands |
| Reproducibility | `docs/reproducibility.md` | Layered `make` targets, exact vs exploratory arithmetic |
| CI layout | `docs/ci-verification.md` | Split verify groups; `git diff --exit-code` on regenerated files |
| Result history | `docs/research/result-history.md` | Chronology of mechanisms and scoped ceilings |
| Preserved research | `docs/research/preserved-research.md` | Intermediate screens, negative results, reusable rejection tools |
| Current status | `docs/research/current-status.md` | Authoritative selected κ; older “selected” text is historical |
| PR ledger | `docs/research/pr-ledger.md` | Disposition: incorporated / partially reviewed / unreviewed / changed |
| Experiment log | `research/experiment-log/README.md` | Ideas, trials, negatives, execution failures, receipts |
| Entry template | `research/experiment-log/ENTRY-TEMPLATE.json` | Canonical experiment record |
| Certificates | `certificates/`, `certificates/checkpoints/` | Exact accepted witnesses |
| Patches | `patches/` | Independent alternatives on pinned upstream |
| Scripts | `scripts/certify.py`, `search_network.py`, `audit_*.py` | Search, certify, reject |
| Reviews | `docs/research/community-frontier799-review.md` and siblings | Scoped maintainer review |
| Integration receipts | `docs/research/community-frontier799-integration.json` | Hashed artifacts, heads, CI status |
| OpenAI baseline | pinned at `adc7f1241b42e322a6451854ab7e4b4c146bf78a` | Unmodified manuscript under `upstream/` |

This project’s parent brief is [`INSTRUCTIONS.md`](../INSTRUCTIONS.md).
That file already asks for `RESEARCH_LOG.md`, comparison docs, a benchmark
protocol, and a repo manifest. The protocol below is how those files should
be *used*, not a second competing document tree.

---

## 2. How integer-mult-bounds organizes research

### 2.1 Proposals and variations

They run a **proposal → scoped experiment → review → select or archive**
pipeline, not a single evolving codebase.

- **Idea campaigns.** `research/experiment-log/campaign-100/` stores 100
  proposals across eight topic files. Statuses include `partial_gain`,
  `bounded_no_gain`, `not_evidenced`, `analysis_only`, `blocked`,
  `partial_experiment`, `bounded_infeasible`, `implemented`. Forty ideas
  have *no execution evidence* and are labeled as such, not as failures
  (`campaign-100/README.md`).
- **Alternative patches.** Early work ships as independent patches against
  the same OpenAI snapshot (`README` table: `frozen-154` … `ternary-30`).
  They are alternatives, not a sequence (`PATCHING.md`).
- **Research packages.** Later work lives under `research/<name>/` with
  `PROOF.md` or `README.md`, `certificate.json`, vendor pins, and a
  dedicated `make <name>-verify` target. Example:
  `research/coordinated-frames-and-entrance-banks/PROOF.md` states the exact
  claim, inventories, paid costs, and inherited hypotheses in one place.
- **PR ledger.** Every contribution has a disposition and an exact head
  (`docs/research/pr-ledger.md`, `pr-ledger.json`). A mention in a note does
  not certify a PR. “Changed since review” means the current head is no
  longer the reviewed object.
- **Parallel credit without headline capture.** Superseded witnesses stay
  attributed (`CONTRIBUTORS.md`, round-two review). Selection is not a
  ranking of people.

**Process pattern:** name the variant, pin its parent, state what it changes,
run a finite check, then either promote it to the selected record or keep it
as an alternative/research package.

### 2.2 Parameter search

Search is systematic and *bounded*, then recertified exactly.

- `scripts/search_network.py` enumerates a finite `h` family, rejects illegal
  candidates, and bounds an infinite tail. Logarithms are enclosed with
  `fractions.Fraction`; the docstring says the result “concerns the counting
  formulas, conditional on the network proof.”
- Exploratory screens may use floating point to *rank* candidates, then
  enclose scores exactly (`docs/reproducibility.md`). Those screens “certify
  neither a new construction nor optimality.”
- Batch searches (100-trial kernel campaigns, 80,000-exchange screens, 476
  gauge trials) write ledgers of *every* trial, including losers
  (`research/experiment-log/`).
- A necessary bound under fixed primitives is recorded as a *ceiling for
  that model*, not a world optimum (`docs/research/result-history.md`:
  `kappa < a^2/(20(1-a))` under those exponents).
- Search reports are not theorems. The #799 review: contributor reports of
  “broad read-exchange searches or frame optimality… are retained as search
  reports, not promoted to independently established optimality theorems.”

**Process pattern:** define the neighborhood, enumerate or sample it, keep
the ledger, recertify the winner with a stricter checker, state the
neighborhood in the claim.

### 2.3 Result comparison

They compare **one primary scalar** (conditional κ) but never confuse it with
runtime.

- Headline metric: exact rational κ in
  `T(n)=O(n (log n)^{1-κ})`.
- Comparison language is explicit: “approximately 0.026005% above the
  previous selected exponent saving, **not a practical runtime claim**”
  (README, #799).
- Secondary metrics are *paid inventories*: roles, rank, deficit, children,
  margins (`PROOF.md` examples). A smaller addition count that increases
  auxiliary roles can lose.
- Tooling speedups are classified separately. #707 “shows determinant-level
  benefit, not a reliable whole-process speedup.” Circuit-count savings in
  #681 “do not improve κ or establish measured runtime gains.”
- Composition uses an explicit binding rule: the weaker of two suppliers
  can bind the final κ (`PROOF.md` for #186: complex side binds).
- Historical results stay in `docs/research/result-history.md` and
  checkpoints so later agents do not re-litigate closed comparisons.

**Process pattern:** one selected scoreboard; multiple supporting inventories;
implementation speed in a different column; previous scores frozen.

### 2.4 Correctness checks

Checks are layered. Passing a lower layer never implies the top theorem.

| Layer | What it is | Example |
|---|---|---|
| Hash / provenance | Source bytes match pins | `upstream/manifest.json`, `selected-result.json` heads |
| Finite identities | Exact replay of a frozen word/profile | `make frontier799-verify` rebuilds ancestry + X4 |
| Negative / mutation controls | Rejected bad edits, omitted shears, dangling nodes | #799 seven recipe controls; ReportO dangling-node artifact |
| Independent engines | Two arithmetic or moment implementations agree | dual rational engines; two moment engines |
| Written argument | LaTeX/PROOF note charges all transitions | `notes/*.tex`, `research/*/PROOF.md` |
| Scoped formalization | Lean for a *stated* contract only | “not a complete Lean multiplication theorem” |
| Inherited hypotheses | All-size, tape, analytic interfaces remain assumptions | every review’s closing paragraph |

Other rules:

- Assertions stay on (`PYTHONOPTIMIZE` rejected).
- Regeneration must be byte-stable for JSON/patches; PDFs are allowed to
  differ (`docs/reproducibility.md`).
- Local replay and Linux CI are separate statuses.
- Counterexamples become checkers (rfu08’s cancelling-scatter case in
  `docs/reproducibility.md`).

### 2.5 Conjecture vs empirical vs proof

They maintain a strict vocabulary. Adapted names for us are in §4.2; their
native distinctions are:

| Their class | Meaning | Must not be sold as |
|---|---|---|
| **Proposal / idea** | Written hypothesis, maybe no run | Experiment |
| **Search report** | Bounded enumeration or heuristic | Optimum or theorem |
| **Finite certificate** | Exact arithmetic on a pinned instance | All-size theorem |
| **Conditional witness** | Finite construction + inherited hypotheses | Unconditional complexity result |
| **Written proof** | Human-readable argument for a scoped claim | Independent peer review |
| **Lean/formal package** | Machine-checked *stated* contract | Full algorithm formalization |
| **Verification tooling** | Faster or leaner checkers | Better κ or better PH |
| **Negative screen** | No gain in a named neighborhood | Impossibility |
| **Execution failure** | Compiler, disk, hash, path | Mathematical rejection |

README and `current-status.md` repeat the same disclaimer so agents cannot
“upgrade” a checkpoint by omission.

### 2.6 Failed and successful experiment logging

`research/experiment-log/README.md` is the operational memory:

| Bucket | Contents |
|---|---|
| `campaign-100/` | Ideas, including 40 with no evidence |
| `kernel-search/` | Full trial ledgers, winners and losers |
| `negative-searches/` | No-gain neighborhoods + retry guidance |
| `execution-failures/` | Storage, compiler, dependency, path, serialization, metadata, assertion |
| `verification/` | Completed receipts with explicit scope |

Rules they actually use:

- Read the matching record *before* repeating an experiment.
- Compare source hash, baseline, assumptions, objective, seeds, verifier
  scope.
- A retry needs a *changed* assumption, input, neighborhood, or repaired
  environment. “Run it again” is not a reason.
- Keep raw failures; add a superseding entry.
- One file per coherent batch; stable IDs; evidence paths/hashes.
- Successful and failed runs live together.
- `COUNTS.json` tracks ideas vs trials vs artifacts vs attempts so agents
  do not treat 100 ideas as 100 tests.

Example of a good negative write-up:
`research/experiment-log/negative-searches/pr485-composition/README.md`
states the pin, the five variants, the two distinct words, both projected
κ values, what passed, what is *not* claimed, and the exact neighborhood
that would justify a retry.

### 2.7 Reproducibility

The reproducibility stack is the product, not an afterthought.

1. **Pinned upstream** never overwritten (`make fetch` refuses dirty trees).
2. **Selected record** binds κ, certificate hash, proof path, reproduce
   command, previous κ, audited heads
   (`certificates/selected-result.json`).
3. **One public command per checkpoint** (`make frontier799-verify`,
   `make entrance-bank-verify`, …).
4. **Fresh output directory**; reuse of ancestry only after a binding
   checker (`docs/reproducibility.md`, #799 `--ancestor`).
5. **CI splits** expensive groups but does not drop historical checks
   (`docs/ci-verification.md`).
6. **Research that is not selected still verifies** via
   `make verify-research`.
7. **AI assistance is disclosed** (NOTICE, review signatures, Codex
   mentions). That is part of provenance, not decoration.

---

## 3. What transfers to TDA persistent homology — and what does not

### 3.1 Transfers (reuse the process)

| integer-mult-bounds habit | PH analog |
|---|---|
| Unmodified `upstream/` + hashes | Vendor clones of Ripser / Ripser++ / GUDHI / … with commit + license |
| Alternative patches | Named algorithm variants (complex × reduction × collapse) on a shared harness |
| Selected record + checkpoints | Selected PH pipeline + frozen benchmark receipts |
| Exact certificate vs float search | Exact persistence identity vs heuristic simplex-count search |
| Paid-cost accounting | Count simplices, columns, reductions, extra index work — not just seconds |
| Scope sentences on every claim | Implementation / structural / theoretical + fidelity class |
| Experiment log + retry_when | `RESEARCH_LOG.md` + per-experiment JSON |
| Separate execution vs math failure | OOM / no GPU / compile fail ≠ “collapse is wrong” |
| Mutation / negative controls | Corrupt a filtration, drop a clear, permute ties; diagrams must change or stay as predicted |
| Independent engines | Two PH libraries on the same exact filtration |
| Research notes without changing κ | Papers, negative screens, GPU notes that do not change the selected complex |
| Local vs CI | Laptop CPU-only vs later GPU box |
| Contributor / source pins | Dataset license, paper DOI, library commit |

### 3.2 Does not transfer (do not copy the math objects)

| Their object | Why it does not move |
|---|---|
| κ in `O(n (log n)^{1-κ})` | PH has no single shared recurrence. Work is filtration- and complex-dependent. |
| Bit vs complex supplier split | No corresponding two-network assembly. |
| Role / frame / tape / Gaussian certificates | Different computational model. |
| Independent TeX patches on a manuscript | Our baseline is executable libraries, not a single preprint to patch. |
| Exact `Fraction` assembly of 47 inequalities | Our “certificate” is a persistence diagram (or a proven homotopy equivalence), plus resource counts. |
| Lean multiplication packages | Optional later; not a gate for the first research stage. |
| Community PR-scale ledger (500+ PRs) | We are a small project. Use a short proposal ledger, not a 446-row PR table. |
| “Conditional on OpenAI #109” | Our conditions are geometric (Euclidean vs metric, dimension, exact vs approximate complex). |
| Headline = larger κ | Our headline is a *tradeoff*: resources × topological fidelity, under a named guarantee. |

### 3.3 Traps this project must avoid

These are the ways their process would be *mis*-applied:

1. Treating a faster Ripser++ run as a structural or theoretical win.
2. Comparing Alpha vs Rips diagrams as if they must coincide.
3. Declaring a collapse “exact” because bottleneck distance was small on
   one dataset.
4. Treating an OOM or missing CUDA device as evidence against an algorithm.
5. Overwriting an old benchmark instead of checkpointing it.
6. Copying their certificate JSON schema instead of defining PH receipts.
7. Formalizing Lean before we have an invariant we can state.
8. Searching parameters (thresholds, landmarks) and calling the best
   setting a new algorithm.

---

## 4. Adapted methodology for this TDA project

### 4.1 Iteration protocol

Use this loop on every algorithmic idea. Do not skip classification.

```
P0  Read RESEARCH_LOG.md + this file + the selected record.
P1  State a proposal in the ledger (one idea, one neighborhood).
P2  Classify the intended evidence class *before* coding:
      implementation | structural | theoretical
    and the intended fidelity class:
      exact | approx-guaranteed | empirical | unverified
P3  Name the baseline(s) and the invariant that must hold.
P4  Design the cheapest experiment that can reject the idea.
P5  Run it on the pinned harness. Write a receipt (pass or fail).
P6  Apply the verification gates in §4.3 for that class.
P7  Decision:
      reject     → log neighborhood + retry_when; do not “fix” the claim
      hold       → keep as research package; selected record unchanged
      promote    → only if gates for the claimed class all pass
P8  Update RESEARCH_LOG.md (short) and the experiment JSON (complete).
P9  If selected record changes, freeze the previous receipt as a checkpoint.
```

**Proposal template (required fields):**

- `id`, `date`, `question`
- `hypothesis` (what work is removed; what must be preserved)
- `parent` (baseline algorithm + commit)
- `neighborhood` (which complexes, dimensions, n, homology degrees)
- `intended_class` (`implementation` / `structural` / `theoretical`)
- `intended_fidelity` (`exact` / `approx-guaranteed` / `empirical`)
- `reject_experiment` (the cheapest test that would kill the idea)
- `invariant` (e.g. “same Rips filtration ⇒ identical H1 diagram”)
- `risks` (counterexample classes: high-d, ties, sparse landmarks, …)

**Hard rules for the LLM agent:**

- Do not implement a new PH algorithm before a written comparison of
  complexes and frameworks (`INSTRUCTIONS.md` §1–3). First iterations
  are *investigation proposals*, not CUDA kernels.
- Do not change more than one research lever per experiment: complex,
  collapse, reduction heuristic, or implementation backend.
- Do not promote a result by rewriting its class after seeing the numbers.
- If the experiment cannot run (no GPU, dataset missing), log an
  `execution_failure` and stop. Do not invent timings.

**First-stage loop (this repository, now):**

1. Complex comparison (Rips, Alpha, edge-collapsed Rips, sparse Rips,
   witness, cubical, Morse / distilled).
2. Framework comparison (Ripser, Ripser++, giotto-ph, GUDHI, Oineus,
   Ripserer) — ideas, not code merges.
3. Pin Ripser++ as GPU *reference* only; CPU algorithm remains the
   development target.
4. Small reproducible benchmark on synthetic + one licensed real set.
5. Only then write competing *algorithm* proposals that remove work.

### 4.2 Evidence classes

Three result classes, as required by `INSTRUCTIONS.md`. They are
incompatible as headlines.

#### A. Implementation

Faster or leaner execution of the *same* mathematical work.

Examples: SIMD, OpenMP, CUDA, cache layout, clearing order that does not
change the reduced column set in the exact sense, I/O.

Required evidence:

- Same complex, same filtration, same exactness class as the parent.
- Persistence diagrams match the pinned CPU reference within a stated
  numeric policy (prefer exact match on a discrete filtration).
- Report wall time, stage time, RAM, GPU memory *and* the work counters
  (simplices, columns, reductions). If work counters do not drop, the
  win is implementation-only.
- Hardware and compiler recorded. A GPU number is not comparable to a
  CPU number as an algorithm claim.

Forbidden promotion: “O(n) improvement” or “better complexity” from a
timing table.

#### B. Structural

Less combinatorial or algebraic work: fewer simplices, columns,
pairs, or dependencies, with a stated topological guarantee.

Examples: edge collapse that preserves persistent homology; apparent /
emergent pairs; discrete Morse reduction; landmark / sparse complexes
*when the guarantee is stated*; clearing that skips proven-zero columns.

Required evidence:

- Work counters drop on the stated family of inputs.
- A correctness argument matching the fidelity class:
  - **exact:** theorem or reduction to a known theorem (e.g. edge
    collapse of Vietoris–Rips preserving PH), plus diagram identity vs
    an exact reference on the test suite;
  - **approx-guaranteed:** cite the approximation theorem and check the
    hypothesis (interleaving, sparse parameter, landmark density);
  - **empirical:** bottleneck / Wasserstein / Betti curves, labeled
    *empirical only*.
- Construction cost of the reduction is charged (collapse time, Morse
  matching time, landmark selection).

Forbidden promotion: a smaller complex that computes a *different*
filtration sold as “the same PH, cheaper.”

#### C. Theoretical

A complexity, correctness, or information-preservation statement that
holds beyond the tested n.

Examples: “edge collapse yields a homotopy-equivalent filtration”;
“sparse Rips is multiplicatively interleaved with Rips”; “this
distributed merge does *not* compute global PH.”

Required evidence:

- Written proof or precise reduction to a published theorem.
- Explicit hypotheses (metric, Euclidean dimension, field, stability).
- Finite checks are *illustrations*, never the proof.
- If only a conjecture exists, status stays `conjecture` even if all
  tests pass.

Forbidden promotion: “appears O(n²) on n ≤ 10⁴, therefore quadratic.”

#### Cross-cutting fidelity labels

Use these on every structural or theoretical claim, including
benchmarks (`INSTRUCTIONS.md` §4):

| Label | Meaning | Typical PH check |
|---|---|---|
| `exact` | Same persistence module (up to stated field / tie-break) | Diagram identity vs reference on the same filtration |
| `approx-guaranteed` | Proven interleaving or approximation | Hypothesis check + optional distance vs exact method |
| `empirical` | Observed similarity, no theorem used | Bottleneck / Wasserstein / Betti, scoped to datasets |
| `unverified` | Not yet checked | Cannot be selected |

Implementation results are usually `exact` (same algorithm) or they are
misclassified.

### 4.3 Verification gates

A result may be logged after P5. It may be **selected** only after the
gates for its class pass. Gates are fail-closed.

#### Gate G0 — Provenance (all classes)

- [ ] Baseline and variant commits recorded.
- [ ] Dataset name, license, generator seed, n, ambient dim, metric,
      filtration threshold, homology degrees, tie policy.
- [ ] Command line and package versions recorded.
- [ ] Output written to a *new* directory; hashes of receipts stored.

#### Gate G1 — Execution honesty (all classes)

- [ ] Exit status, OOM, timeout, missing GPU recorded as
      `execution_failure` when they occur.
- [ ] No result invented for a skipped backend.
- [ ] Repeated timings (minimum 3 when claiming a speedup) with median
      and range.

#### Gate G2 — Implementation acceptance

- [ ] G0–G1.
- [ ] Diagrams match the exact parent on all `exact` suite cases.
- [ ] Work counters reported; if they did not drop, the write-up says
      “implementation only.”
- [ ] No complexity claim.

#### Gate G3 — Structural acceptance

- [ ] G0–G1.
- [ ] Work counters drop on the declared neighborhood.
- [ ] Construction overhead charged.
- [ ] Fidelity gate:
      - `exact`: identity vs reference *or* a cited theorem plus
        identity on the suite;
      - `approx-guaranteed`: theorem citation + hypothesis check;
      - `empirical`: distances reported; status remains empirical.
- [ ] At least one predicted counterexample class tested (high-d,
      noisy circle, ties, disconnected data, as relevant).

#### Gate G4 — Theoretical acceptance

- [ ] Written argument with hypotheses and cited lemmas.
- [ ] Finite examples do not substitute for the argument.
- [ ] Status is `theorem`, `conditional-theorem`, or `conjecture`.
- [ ] If `conjecture`, selected algorithm may *use* it only with an
      empirical/unverified fidelity label.

#### Gate G5 — Selection (change the project headline)

- [ ] Class-appropriate gate G2/G3/G4 passed.
- [ ] Comparison against the current selected record on the shared
      benchmark protocol.
- [ ] Previous selected receipt frozen under `benchmarks/checkpoints/`.
- [ ] `RESEARCH_LOG.md` and the selected-record JSON updated in the
      same change.
- [ ] No license-incompatible code merge.

#### Built-in rejection screens (PH-specific)

Record these as reusable negative tools, analogous to their topology
screens:

1. **Different-complex screen:** refuse diagram identity tests between
   Rips and Alpha / witness / cubical unless a theorem says they agree.
2. **Partition screen:** refuse “compute PH on shards and union barcodes”
   as a global-PH claim without a merge theorem.
3. **Landmark screen:** witness / sparse methods default to
   `approx-guaranteed` or `empirical`, never `exact`, until proved.
4. **Work-vs-time screen:** if time drops and columns do not, classify
   implementation.
5. **Tie-break screen:** order of equal filtration values is part of
   the filtration; document it.

### 4.4 Logging format

Two layers, as in CrocSwap: a short human log plus machine receipts.

#### Layer A — `RESEARCH_LOG.md` (root, short)

One entry per session or significant experiment. No transcripts.

```markdown
## YYYY-MM-DD — <short title>

- Question:
- Hypothesis / proposal:
- Class / fidelity: implementation|structural|theoretical / exact|...
- Experiment:
- Result + evidence path:
- Decision: pending | rejected | hold | selected
- Next step:
```

Statuses allowed in the running index at the top of the file:

- `proposal`
- `experimented`
- `reproduced`
- `verified` (gates for its class passed)
- `selected`
- `rejected`
- `execution_failure`

#### Layer B — experiment receipt JSON

One file per experiment or batch:
`benchmarks/results/<id>/ENTRY.json`
(or `research/experiments/<id>/ENTRY.json` before the harness exists).

Schema adapted from
[`ENTRY-TEMPLATE.json`](https://github.com/CrocSwap/integer-mult-bounds/blob/main/research/experiment-log/ENTRY-TEMPLATE.json):

```json
{
  "id": "ph-0001",
  "category": "complex-comparison|framework|collapse|reduction|implementation|theory|negative|execution-failure",
  "date_utc": "2026-10-13",
  "source_commit": "",
  "baseline": {
    "name": "ripser",
    "commit": "",
    "complex": "vietoris-rips",
    "scope": "exact PH of the stated Rips filtration"
  },
  "variant": {
    "name": "",
    "complex": "",
    "reduction": "",
    "backend": "cpu|gpu|na"
  },
  "hypothesis": "",
  "intended_class": "implementation|structural|theoretical",
  "intended_fidelity": "exact|approx-guaranteed|empirical|unverified",
  "command_or_script": "",
  "parameters": {
    "n": null,
    "dim": null,
    "maxdim": null,
    "threshold": null,
    "metric": "euclidean",
    "field": 2,
    "seed": null
  },
  "datasets": [],
  "status": "pending|pass|no_gain|rejected|execution_failure|blocked",
  "result": {
    "time_s_median": null,
    "rss_bytes_peak": null,
    "gpu_mem_bytes_peak": null,
    "n_vertices": null,
    "n_edges": null,
    "n_simplices": null,
    "n_columns_reduced": null,
    "collapse_ratio": null,
    "diagram_identity": null,
    "bottleneck": null,
    "wasserstein": null
  },
  "failure_kind": null,
  "failure_reason": null,
  "verification_scope": "",
  "gates_passed": [],
  "evidence": [],
  "do_not_repeat_scope": "",
  "retry_when": "",
  "supersedes": null
}
```

#### Layer C — selected record

When something is selected, write
`benchmarks/selected-result.json` (create later; do not invent numbers now):

- selected pipeline name
- class + fidelity
- parent checkpoints
- reproduce command
- receipt hashes
- scope sentence (what is *not* claimed)
- previous selected id

This is our analog of `certificates/selected-result.json`, without
pretending to have a κ.

#### Layer D — proposal ledger

A short table, not a 500-row PR dump:

`docs/PROPOSAL_LEDGER.md` (create when the first algorithm proposal
exists)

| id | idea | class | status | evidence | disposition |
|---|---|---|---|---|---|

Dispositions: `proposed`, `experimented`, `hold`, `rejected`,
`selected`, `superseded`.

#### What not to log

- Full chat transcripts.
- Regenerable huge diagrams in git (hash + path is enough).
- “Active” status that will rot; use `current` vs `historical` pages
  the way they use `current-status.md` vs `result-history.md`.

---

## 5. Concrete mapping onto this repository

`INSTRUCTIONS.md` already names the files. Use them with the protocol
above; do not grow a parallel tree.

| File | Responsibility | CrocSwap analog |
|---|---|---|
| `RESEARCH_LOG.md` | Short session memory | experiment-log README + current-status |
| `docs/METHODOLOGY.md` | This process | implicit in README + reproducibility |
| `docs/RESEARCH_PLAN.md` | Questions, stages, decision criteria | `next-steps.md` (historical) + current-status |
| `docs/ALGORITHM_COMPARISON.md` | Complexes + frameworks | construction notes + reviews |
| `docs/PAPERS.md` | Annotated bibliography | `references/`, CITATION, NOTES |
| `docs/BENCHMARK_PROTOCOL.md` | How we measure and compare | `docs/reproducibility.md` + CI doc |
| `docs/PROPOSAL_LEDGER.md` | Idea dispositions | `pr-ledger.md` (lite) |
| `benchmarks/` | Scripts, configs, receipts | `research/*/`, `certificates/` |
| `vendor/` or repo manifest | Pinned externals | `upstream/manifest.json`, `SOURCES.json` |

Keep the CrocSwap-scale machinery **out** until it earns its keep:

- No Lean unless we have a lemma worth checking.
- No patch-against-TeX workflow.
- No 28-audit `verify-research` suite until we have 28 audits.
- Yes to: pins, receipts, scopes, negative logs, one selected record.

---

## 6. Proposed iteration loop for the current project

Until a new algorithm is justified, the loop is investigative:

```
read logs
  → pick the next unanswered question from RESEARCH_PLAN
  → write a proposal row (class + reject experiment)
  → gather evidence (papers, code read, small benchmark)
  → apply gates (many first-stage items are "hold" not "selected")
  → log
  → only then allow an algorithm-change experiment
```

Immediate neighborhood (from `INSTRUCTIONS.md`, not from κ-search):

1. Complex family recommendation for the first benchmark round.
2. Framework idea map (clearing, cohomology, collapse, GPU).
3. Ripser++ pinned as GPU reference; compile/run limits recorded honestly.
4. Tiny exact-suite (noisy circle, sphere, torus, Gaussians, uniform,
   one licensed real subset) at n the machine can finish.
5. Identify the dominant cost: distance, simplex generation, reduction,
   memory.
6. Propose ≥3 structural directions that remove work, each with a
   reject experiment.

CPU-first, GPU-later remains a development constraint, not a research
conclusion (`INSTRUCTIONS.md` strategy section).

---

## 7. Citation of practices (quick index)

- Alternatives, not stacks: [PATCHING.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/PATCHING.md)
- Selected vs historical: [README](https://github.com/CrocSwap/integer-mult-bounds/blob/main/README.md),
  [current-status.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/research/current-status.md)
- Exact vs exploratory: [docs/reproducibility.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/reproducibility.md),
  `scripts/certify.py`
- Negative + retry: [experiment-log/README.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/research/experiment-log/README.md),
  [ENTRY-TEMPLATE.json](https://github.com/CrocSwap/integer-mult-bounds/blob/main/research/experiment-log/ENTRY-TEMPLATE.json)
- Research without moving the headline:
  [research-notes-20261011.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/research/research-notes-20261011.md)
- Scoped review:
  [community-frontier799-review.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/research/community-frontier799-review.md)
- Paid costs and inherited hypotheses:
  [PROOF.md (entrance banks)](https://github.com/CrocSwap/integer-mult-bounds/blob/main/research/coordinated-frames-and-entrance-banks/PROOF.md)
- Search neighborhood + ceiling:
  [network-search-log.md](https://github.com/CrocSwap/integer-mult-bounds/blob/main/docs/research/network-search-log.md)
- Frozen selected record:
  [certificates/selected-result.json](https://github.com/CrocSwap/integer-mult-bounds/blob/main/certificates/selected-result.json)
