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

Phase-2 measurements (GUDHI bottleneck; Wasserstein skipped — POT missing):

| Family | Scale unmatched vs VR | Bottleneck \(H_1\) | Essential |
| --- | ---: | ---: | --- |
| figure8, circle, nested, many_loops, bridges, multi_scale (\(n=400\)) | 0 | \(\sim 10^{-6}\) | matches VR |
| sphere \(n=400\) | 52 | 0.024 | \(H_2=1\) kept |
| multi_cavities \(n=300\) | 52 | 0.041 | \(H_2=3\) kept |
| mixed 1D/2D/3D \(n=300\) | 35 | 0.030 | \(H_1=1\) kept; exact VR timed out |

GUDHI Alpha on the same clouds dropped essential \(H_1/H_2\) to 0.

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

## When not to use it

- Non-Euclidean metrics (`--distances`) — there is no Delaunay.
- \(d\ge 4\) — we do not build Delaunay there.
- You need the VR barcode, including finite bars, as a legal invariant.
- Very dense \(T\) where you already can afford exact VR (use `--mode exact`).
