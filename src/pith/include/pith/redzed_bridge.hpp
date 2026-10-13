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

}  // namespace pith
