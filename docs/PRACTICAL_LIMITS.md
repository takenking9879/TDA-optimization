# Practical limits (this hardware)

4 CPU / 16 GB. Budget 12 s unless noted. Ripser is 1 thread. PITH
`--threads 1` unless noted. Empirical, not theorems.

This is the single “how far can each method go” table. Receipts:
`leftover_10x.json`, `baselines.json`, `limits.json`, `sparse_scale.json`,
`axis_scaling.json`, `headline_reverify.json`, `dory.json`,
`dory_limits.json`, `uniform10.json`.

## Exact VR (barcode must match Ripser)

| Method | Typical last-OK on this box | First clear failure | Threads | Notes |
| --- | --- | --- | ---: | --- |
| PITH `--mode exact --engine auto` | circle \(H_1\) \(n=4000\) 0.43 s; figure-8 \(n=4000\) 1.03 s; sphere \(H_2\) \(n=800\) 0.057 s; leftover figure-8 \(n=2000\) 0.15 s | mixed 1D/2D/3D \(n=300\) `maxdim=2` timeout (fat \(H_2\)); connected leftover leaves cheap regime near a few thousand points (\(p_n\approx 2.8\)) | 1 | Portfolio. Circle 31× is **collapse**. Leftover 3/6 families ≥10×. |
| PITH `--engine redzed` | same leftover families; torus \(n=2000\) 0.21 s | same fat-\(H_2\) / leftover visit wall | 1 | Forced AE. Same pairing class as Ripser. |
| Ripser | circle \(n=1000\) 2.2 s / \(n=1500\) 8.45 s; figure-8 \(n=2000\) 2.5 s / \(n=3000\) 5.42 s; sphere \(H_2\) \(n=400\) 1.0 s / \(n=600\) 5.30 s | circle \(n=2000\); figure-8 \(n=4000\); sphere \(H_2\) \(n=800\) | 1 | Reference exact VR. \(n=1500/3000/600\) from paired `dory_limits.json`. |
| giotto-ph 0.2.4 | tracks Ripser on this suite | same n as Ripser on \(H_1\); 4 threads help sphere \(H_2\) only (1.12→0.62 s) | 1 or 4 | AGPL oracle. |
| GUDHI 3.13 Rips (explicit) | circle \(n=400\) \(T=2.0\) 3.2 s; figure-8 \(n=800\) \(T=1.4\) 3.0 s | circle \(n=1000\) \(H_1\); uniform2 \(n=800\) \(T=0.55\) (8 s axis budget) | 1 | First to leave the budget as \(T\) or \(n\) grows. |
| Dory (`pydory` 1.1.137 oracle) | leftover \(H_1\): circle \(n=1500\) 9.45 s, figure-8 \(n=3000\) 5.70 s; sphere \(H_2\) \(n=400\) 4.13 s (20 s receipt) | circle \(n=2000\) (same as Ripser); figure-8 \(n=4000\) (same as Ripser); sphere \(H_2\) \(n=600\) (Ripser still 5.3 s) | 1 | Tracks Ripser on leftover \(H_1\). Fails \(H_2\) **earlier** than Ripser. Not vendored. 12 s budget (`dory_limits.json`). |

## Not exact VR

| Method | Typical last-OK | First clear failure | Threads | Topology vs VR |
| --- | --- | --- | ---: | --- |
| PITH `--mode scale` | figure-8 \(n=24000\) 0.79 s ess \(H_1=2\); sphere \(n=80000\) 1.08 s ess \(H_2=1\) | \(d\notin\{2,3\}\) unsupported | 1 | Essential loops/voids kept on the measured suite; finite bars differ (sphere \(n=400\): 52 unmatched, bn \(H_1=0.024\)). |
| PITH `--mode sparse` | figure-8 \(n=24000\) 5.56 s / 1.56M edges / ess \(H_1=2\) | FPS \(\Theta(n^2)\) (\(p\approx 2\)); fat \(H_2\) on 4D timed out (25 s) | 1 | Sheehy-style. 2D loops usually kept; `nested_loops` \(W_1\approx 1.05\). |
| GUDHI Alpha | fast at these n | not a VR stand-in | 1 | Drops essential \(H_1/H_2\) on this suite. |

## High-d control (`uniform10`, \(d=10\), \(T=1.8\))

No `--mode scale`. 12 s, 1 thread (`uniform10.json`).

| Method | Last OK | First 12 s fail | Notes |
| --- | --- | --- | --- |
| PITH `--mode exact` | \(n=8000\) 2.79 s (RedZeD) | none in this sweep | \(n=200\) is **2× slower** than Ripser (historical negative control). \(n\ge 800\) is faster. |
| Ripser | \(n=1600\) 2.37 s | \(n=4000\) | Same pairing class; all-pairs at this \(T\). |
| PITH `--mode sparse` | \(n=1600\) 2.16 s | \(n=4000\) | FPS + 6.5M edges at \(n=4000\) (~18 s if allowed). |
| `--mode auto` | \(n=4000\) now exact 0.74 s | previously sparse 18 s | Clock-compare override: stay exact when scale is unavailable and sparse is not clearly cheaper. τ frozen. |
| `--mode auto` fat \(H_2\) \(n=250\) | refuse (exit 3) | — | Same refuse as `uniform4`. Held-out `uniform6` \(n=200\) also refuses. |

Held-out clock-compare (`highd_auto.json`, not used to pick the 1.5 margin):
**0/8** wrong on uniform5/6/7/8 and L1 \(d=4\). Exact was cheaper on every
timed pair.

## `--mode auto` refuse

Fat \(H_2\) + recommended sparse + \(d\notin\{2,3\}\): exit 3 (`auto_will_run=false`).
Examples: `uniform4` \(n=250\), \(T=0.6\), `maxdim=2`; `uniform10` \(n=250\), \(T=1.8\), `maxdim=2`.
Explicit `--mode sparse` still runs.

## Axis (fixed n, 8 s, 1 thread)

| Axis | What explodes first | What stays cheap |
| --- | --- | --- |
| Threshold \(T\), circle \(n=400\) | GUDHI \(0.037\to 3.2\) s, Ripser \(0.007\to 0.26\) s (\(p_T\approx 3\)) | PITH exact \(4\to 23\) ms; scale 4–6 ms |
| Noise \(\sigma\), circle \(n=500\) | Topology (ess \(H_1\) dies at \(\sigma\ge 0.15\)) | Exact VR gets *cheaper* as the loop washes out |
| Density \(T\), uniform2 \(n=800\) | GUDHI timeout at \(T=0.55\) | PITH 19 ms, Ripser 104 ms, scale 10 ms |
| Ambient dim, uniform, fixed \(T\) | nothing at \(n\le 800\) | Higher \(d\) is sparser/faster. Not a hardness proxy. |

## CPU

PITH `--threads 1`: `cpu_s / wall_s ≈ 1` on the axis sweep. Ripser and GUDHI
are 1 thread. giotto 4-thread does not close the \(H_1\) gap. Headline
31–58× ratios are not a 4-core artifact.
