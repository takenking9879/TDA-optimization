# Euclidean scale path

`--mode scale` is **not exact Vietoris–Rips**. It is a different flag
complex built from the Euclidean Delaunay 1-skeleton, optionally
thickened by a local radius, then reduced with the same RedZeD / implicit
engines used for exact VR.

Use it when exact VR on \(G_T\) is the bottleneck (dense leftover
visits) and the data are Euclidean in dimension 2 or 3.

## What is computed

1. Incremental Delaunay 1-skeleton in \(d=2\) or \(d=3\) (walk-locate
   Bowyer–Watson; MST \(\subseteq\) Delaunay, so \(H_0\) on this graph
   is exact for the Euclidean MST / Kruskal problem).
2. Optional **thicken**: add edges with \(d\le\min(T,\alpha\,r_v)\)
   where \(r_v\) is the longest Delaunay edge at \(v\).
   `auto` uses \(\alpha=\min(2.25,\,1.75+0.125\log_2\max(n/400,1))\).
   The 2.25 cap is the measured constant that kept essential \(H_1\) on
   the figure-8 suite (I279/I305). **[empirical]**
3. Persistence of the **flag** of that 1-skeleton (not the VR of all
   pairs \(\le T\)).
4. Split (2D, `maxdim≥2`): \(H_1\) on the thicken, \(H_2\) on \(\alpha=1\).
   3D `maxdim≥2` stays \(\alpha=1\) (thicken \(H_1\) on a sphere is
   noise; the void is in \(H_2\)).

## What is preserved

| Feature | Typical behavior on the measured suite |
| --- | --- |
| Essential \(H_0\) | Kept (components). |
| Essential \(H_1\) | Kept on figure-8, two circles, torus-like loops at the tested \(n\). |
| Essential \(H_2\) | Kept on a sphere / two spheres at \(\alpha=1\). |
| Finite bars | **Not** VR. Unmatched finite intervals are expected (3–200+ on small clouds). |

Always report essential Betti **and** unmatched finite bars / bottleneck
versus Ripser when \(n\) is small enough to run both.

Phase-2 measurements (GUDHI bottleneck + Hera Wasserstein \(W_1\)):

| Family | Scale unmatched vs VR | Bottleneck \(H_1\) | Essential |
| --- | ---: | ---: | --- |
| figure8, circle, nested, many_loops, bridges, multi_scale (\(n=400\)) | 0 | \(\sim 10^{-6}\) (W1 \(\sim 10^{-6}\)) | matches VR |
| sphere \(n=400\) | 52 | 0.024 (W1 \(H_1=0.21\), \(H_2=0.039\)) | \(H_2=1\) kept |
| multi_cavities \(n=300\) | 52 | 0.041 | \(H_2=3\) kept |
| mixed 1D/2D/3D \(n=300\) | 35 | 0.030 | \(H_1=1\) kept; exact VR timed out |

GUDHI Alpha on the same clouds dropped essential \(H_1/H_2\) to 0.
Phase-3 post-freeze: `grid_holes` scale unmatched 0 / ess \(H_1=2\);
`disconnected_circles` unmatched 0 / ess \(H_0=2,H_1=2\);
`two_spheres_apart` unmatched 45 / ess \(H_2=2\) (\(W_1(H_2)=0.026\)).
Alpha on those three reports ess \(H_1=H_2=0\) and merges the two
far circles / spheres into one \(H_0\).

Persistence-diagram overlays at \(n=400\) (`plot_pd.py`): exact sits on
Ripser; scale keeps essential bars on the 2D loops and the sphere void;
sparse keeps 2D ess with extra finite bars; GUDHI Alpha drops essential
\(H_1/H_2\). See `benchmarks/results/consolidation/figures/pd_*.svg`.

## What is lost

Short finite loops that need a denser 1-skeleton than Delaunay+\(\alpha r_v\).
Alpha complex (circumsphere filtration) is a **different** module and
was observed to drop essential \(H_1/H_2\) (I205/I283) — we do not use
it as a VR stand-in.

## Complexity (honest)

- Construction: incremental Delaunay, expected \(O(n\log n)\) location
  plus cavity work in fixed dimension **[citation: standard incremental
  Delaunay]**. Our 80k sphere wall is still walk + insphere **[empirical]**.
- Algebra: RedZeD / implicit on \(\lvert E\rvert=\Theta(n)\) (Delaunay)
  or \(O(n)\) after a bounded thicken. Mean degree \(\sim 6\)–\(100\),
  not \(\Theta(n)\). **[derivation of size; empirical constants]**
- This is a **regime-specific size class** (low-d Euclidean), not a
  better Big-O for abstract VR.

## How to run

```sh
# 2D finite loops (figure-8, noisy circles)
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 1 --threshold 1.1

# 3D loops + voids (sphere, two spheres)
./src/pith/build/pith --points cloud.csv --mode scale --maxdim 2 --threshold 1.4
```

`--mode scale` is the stable name. `--delaunay-vr --delaunay-alpha auto`
is the same path (kept for old scripts).

## Practical sizes on this hardware (4 CPU, 16 GB)

Measured, not a guarantee:

| Family | \(n\) | Wall | \(\lvert E\rvert\) | Essential |
| --- | --- | --- | --- | --- |
| figure8, maxdim 1–2 | 16 000 | 0.54 s | 878k | \(H_1=2\) |
| figure8 | 24 000 | 0.83 s | 1.26M | \(H_1=2\) |
| sphere, maxdim 2 | 50 000 | 0.66 s | 252k | \(H_2=1\) |
| sphere | 80 000 | 1.09 s | 404k | \(H_2=1\) |
| sphere | 100 000 | ~1.6 s | 505k | \(H_2=1\) |

Exact VR on the same figure-8 at \(n=4000\) is already ~1 s / 27× vs
Ripser; at \(n=16000\) exact leftover visits are the wall. Scale is
how we go further.

## Versus `--mode sparse`

Owned sparse Rips (greedy net, ε=0.6, Max cap) has a Sheehy-style
interleaving **[citation]**. An earlier write-up used the `distances`
counter (\(C(n,2)\) pairwise evaluations) as \(\lvert E\rvert\); that was
wrong. The flag **is** thinner: figure-8 \(n=400\) has 5 563 edges
(vs 79 800 pairs / 19 060 exact-VR edges); \(n=8000\) has ~380k vs 32M
pairs. Euclidean `--points` now skip the n×n matrix (same edge set as
the dense constructor: unit + CLI adversarial). Farthest-point
insertion is still \(\Theta(n^2)\) **[derivation]**; emit is a \(T\)-ball
hash when \(d\in\{2,3\}\). figure-8 \(n=8000\): **0.65 s / 28 MB**;
\(n=24000\): **5.56 s / 101 MB / ess \(H_1=2\)** (local \(p\approx 2\)).
Scale on that \(n=24000\) cloud is **0.82 s**. Essential \(H_1\) is usually kept
**[empirical]**. Consolidation receipts (`sparse_limits.json`, \(n=400\)):
figure-8 / circle bn \(H_1\approx 0.006\)–\(0.007\), \(W_1\approx 0.023\)–\(0.034\);
`nested_loops` ess \(H_1=1\) but \(W_1\approx 1.05\) (52 unmatched). Some
seeds of `nested_loops` invent extra essential loops (4 vs VR 1).
\(H_2\) is slow or times out. Scale is still the faster Euclidean
alternative (0.22 s at \(n=8000\), 0.82 s at \(n=24000\)).

## Versus Coperto (quotient covers)

Coperto 0.1.7 (Leitão, arXiv:2602.22784) is a **different**
approximation: quotient the cover by a persistent partition, claimed
**log-3 interleaving** with VR on any metric **[citation]**. It is
**not** exact VR. Live 1-thread (`coperto.json`, `greedy=False`):

- Library default `greedy=True` drops all \(H_1\) on a noisy circle
  (\(n_{H_1}=0\)).
- With exact tie-breaking, the tower is linear (\(\sim 3n\)–\(4n\))
  but essential loops/voids become **finite** (figure-8 / circle ess
  \(H_1=0\) vs VR 2 / 1; sphere ess \(H_2=0\) vs 1). \(n=400\)
  unmatched 24–123; bottleneck/Wasserstein are \(\infty\) when
  essential cardinality differs. Scale on the same 2D loops is
  unmatched 0.
- figure-8 \(n=8000\): Coperto 6.74 s vs scale 0.21 s vs sparse 0.66 s.
  Faster than Ripser; slower and less faithful than scale on
  Euclidean \(d\in\{2,3\}\).

Use Coperto only if you need a metric-space theorem and can accept
finite (not essential) long bars. Do not treat it as a VR barcode
or as a 10× exact engine.

## When not to use it

- Non-Euclidean metrics (`--distances`) — there is no Delaunay.
- \(d\ge 4\) — we do not build Delaunay there. `--mode auto` may recommend
  `--mode sparse` for \(H_1\); fat \(H_2\) on those metrics is refused
  (exit 3) rather than started.
- You need the VR barcode, including finite bars, as a legal invariant.
- Very dense \(T\) where you already can afford exact VR (use `--mode exact`).
