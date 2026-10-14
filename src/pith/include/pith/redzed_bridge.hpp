#pragma once

#include "types.hpp"

namespace pith {

// I228: in-tree wrap of vendored RedZeD (MIT, Kapulkin–Kershaw).
// Same path on every distance matrix — not a circle/sphere/torus special
// case. Collapse is skipped: RedZeD works on the full metric, not a residual.
Result persist_redzed(const std::vector<std::vector<value_t>>& dist, int maxdim,
                      value_t threshold);

// I238: points → compact lower-tri metric (parallel fill). Skips the
// vector<vector> pairwise + copy that auto-redzed paid before reduce.
// I239: if G_T has >1 component, RedZeD each block (bounded pool) and
// merge bars. Exact: VR of a disjoint union is the direct sum.
// I240: low-d spatial UF finds those components without an n×n matrix;
// each block allocates only its own m×m metric.
// I241: maxdim=0 is spatial/matrix Kruskal (no RedZeD).
// I270/I271: 2D Delaunay MST (walk-locate) when n∈[256,100000].
// I274/I275: 3D Delaunay MST (walk-locate, no slot reuse) when n∈[256,50000].
// I244: finite T skips vendor enclosing (exact for VR≤T).
// I245: parallel build_edges (same buckets + finish_buckets).
Result persist_redzed_from_points(const std::vector<std::vector<value_t>>& pts, int maxdim,
                                 value_t threshold);

// I263: 250 evenly spaced points, |{d≤T}| / C(m,2). Used by auto
// dispatch so hollow/manifold clouds take RedZeD (spatial+hash) even
// when the collapse residual probe looks thin.
double probe_edge_frac_points(const std::vector<std::vector<value_t>>& pts, value_t T,
                              int sample = 250);

// I276: Euclidean Delaunay 1-skeleton (I271 2D / I275 3D). Flag of these
// edges is not exact VR; it is the optional `--delaunay-vr` scale path.
bool delaunay_one_skeleton(const std::vector<std::vector<value_t>>& pts, std::vector<Edge>& out);

// I277–I280: Delaunay plus edges with d≤min(T, R_v) from each vertex.
// r_v = longest incident Delaunay edge. Default R_v = α·r_v (I279 α=2.25).
// I280 adapt: R_v = α·max(r_v, max_{nbr} r_u), plus floor·median(r).
// Spatial query. H1-only; α=1 is I276.
bool delaunay_vr_skeleton(const std::vector<std::vector<value_t>>& pts, value_t T, value_t alpha,
                          std::vector<Edge>& out, value_t floor = 0, bool adapt = false);

// I298: append local-radius extras onto an existing Delaunay 1-skeleton
// (same edges as delaunay_vr_skeleton). Split builds Delaunay once.
bool delaunay_thicken_extras(const std::vector<std::vector<value_t>>& pts, value_t T, value_t alpha,
                             std::vector<Edge>& inout, value_t floor = 0, bool adapt = false);

// I282: α(n) = min(2.75, 1.75 + 0.125 log2(max(n/400, 1))).
// I305: cap 2.25 (I279 measured exact constant). Extra thicken past
// 2.25 was adding edges, not essential H1, at n≥8000.
inline value_t delaunay_auto_alpha(int n) {
    const double nn = std::max(static_cast<double>(n) / 400.0, 1.0);
    return static_cast<value_t>(std::min(2.25, 1.75 + 0.125 * std::log2(nn)));
}

// I291: α=1 Delaunay is ~3n–7n (I207 collapse tax). Auto-α thicken
// is mean-deg 40–100 and collapses like a circle G_T.
inline bool delaunay_thicken_should_collapse(int n, std::int64_t n_edges) {
    return n_edges >= 8 * static_cast<std::int64_t>(std::max(n, 1));
}

// I297: RedZeD on an explicit 1-skeleton (SparseDist + prebuilt EdgeList).
// Used for fat Delaunay thicken so H1 is AE, not implicit V-adds.
Result persist_redzed_from_edges(int n, const std::vector<Edge>& edges, int maxdim,
                                 value_t threshold);

}  // namespace pith
