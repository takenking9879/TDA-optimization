# Benchmarks

This folder has two layers.

## Stable suite (use these)

Public runners and receipts. They talk only in `--mode` / `--engine` /
`--estimate` language. Iteration numbers stay in `RESEARCH_LOG.md`.

| Script | What it checks |
| --- | --- |
| `test_cli_stable.py` | Stable CLI, estimate JSON, `--mode auto` refuse |
| `test_sparse_points.py` | Euclidean sparse constructor |
| `test_baseline_hooks.py` | Optional oracle imports |
| `generate_datasets.py` | Public point-cloud generators |
| `run_stable.py` | One entry: tests, or `--full` receipts |
| `eval_mode_auto.py` | `--mode auto` vs the frozen probe |
| `eval_engine_auto.py` | Exact-engine oracle (τ frozen) |
| `eval_estimate.py` | Feasibility bands vs measured walls |
| `eval_ncc_auto.py` | Euclidean fat-H2 \(n_{cc}\) / dense-flag |
| `eval_adversarial.py` | Held-out families, seed 17 |
| `eval_leftover_ratio_n.py` | Leftover H1 ratio vs n (frozen pack) |
| `eval_leftover_heldout.py` | Held-out leftover H1 ratios, seed 19 |
| `eval_leftover_miss_n.py` | Leftover-miss families scaled in n |
| `eval_postfreeze.py` | Dispatcher pack chosen after the leftover-H1 clock gate |
| `eval_linked_n.py` | Post-freeze leftover H1 ratio vs n |
| `leftover_miss_dispatch.json` | `--mode auto` on those n=8000 cells after the clock gate |
| `eval_highd_auto.py` | High-d / L1 clock-compare |
| `eval_wall_kind.py` | collapse vs leftover vs construction |
| `reverify_*.py` | Headline / leftover / oracle re-measures |
| `eval_homcloud.py` | HomCloud 5.4.0 / PHAT leftover oracle (GPL, not vendored) |
| `eval_dyadic_net.py` | Dyadic s-net vs FPS sparse Rips (not exact VR) |
| `run_consolidation.py` | Main scaling pack |
| `plot_consolidation.py` | Figures + `TABLES.md` |
| `plot_pd.py` | Persistence-diagram figures |

Receipts live in `results/consolidation/`.

```sh
python3 benchmarks/run_stable.py          # cheap tests
python3 benchmarks/run_stable.py --full   # re-measure receipts (minutes)
```

## Research ledger (do not use as the API)

`run_wave*.py` and `probe_i*.py` are the iteration history. They import
each other and mention I-numbers. Keep them for the log; do not add new
user-facing flags from them.

Shared helpers for new work:

- `generate_datasets.py` — clouds
- `ph_metrics.py` — `ess`, bottleneck
- `run_suite.py` — Ripser / PITH parsers
- `run_consolidation.py` — `run_estimate` / `run_pith` / `run_ripser`
