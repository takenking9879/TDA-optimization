#pragma once

#include "graph.hpp"

#include <algorithm>
#include <vector>

namespace pith {

// I210: insertion radii of a farthest-point (greedy) permutation.
// λ[p_0] is the covering radius after the first point; later λ[p] is the
// distance from p to the already-chosen net. O(n²) on a dense distance matrix.
inline std::vector<value_t> greedy_insertion_radii(const std::vector<std::vector<value_t>>& dist) {
    const int n = static_cast<int>(dist.size());
    std::vector<value_t> lam(static_cast<size_t>(n), 0);
    if (n == 0) return lam;
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<value_t> mind(static_cast<size_t>(n), kInf);
    used[0] = 1;
    value_t cover = 0;
    for (int j = 1; j < n; ++j) {
        mind[static_cast<size_t>(j)] = dist[0][static_cast<size_t>(j)];
        cover = std::max(cover, mind[static_cast<size_t>(j)]);
    }
    lam[0] = cover;
    for (int k = 1; k < n; ++k) {
        int best = -1;
        value_t best_d = -1;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            if (mind[static_cast<size_t>(j)] > best_d) {
                best_d = mind[static_cast<size_t>(j)];
                best = j;
            }
        }
        if (best < 0) break;
        used[static_cast<size_t>(best)] = 1;
        lam[static_cast<size_t>(best)] = best_d;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            mind[static_cast<size_t>(j)] =
                std::min(mind[static_cast<size_t>(j)], dist[static_cast<size_t>(best)][static_cast<size_t>(j)]);
        }
    }
    return lam;
}

// Cavanna–Jahanseir–Sheehy / GUDHI-style sparse Rips 1-skeleton.
// Keep (i,j) iff d(i,j) ≤ T and d(i,j) ≤ ((1+ε)/ε) · max(λ_i, λ_j).
// This is exact PH of the *flag* of that subgraph, not of VR(G_T).
inline Graph sparse_rips_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                               value_t eps) {
    if (eps <= 0 || eps >= 1) return graph_from_distance(dist, T);
    const int n = static_cast<int>(dist.size());
    Graph g;
    g.n = n;
    const auto lam = greedy_insertion_radii(dist);
    const value_t c = (1 + eps) / eps;
    g.edges.reserve(static_cast<size_t>(n) * 8);
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            const value_t d = dist[static_cast<size_t>(i)][static_cast<size_t>(j)];
            if (d > T) continue;
            const value_t cap = c * std::max(lam[static_cast<size_t>(i)], lam[static_cast<size_t>(j)]);
            if (d <= cap) g.edges.push_back({i, j, d});
        }
    }
    rebuild_neighbors(g);
    return g;
}

}  // namespace pith
