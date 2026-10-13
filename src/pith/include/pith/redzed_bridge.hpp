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
Result persist_redzed_from_points(const std::vector<std::vector<value_t>>& pts, int maxdim,
                                 value_t threshold);

}  // namespace pith
