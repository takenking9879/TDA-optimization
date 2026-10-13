#pragma once

#include "types.hpp"

#include <utility>

namespace pith {

struct Graph {
    int n = 0;
    std::vector<Edge> edges;
    // neighbors[v] = sorted (u, t) with u != v
    std::vector<std::vector<std::pair<index_t, value_t>>> neighbors;
};

inline void rebuild_neighbors(Graph& g) {
    g.neighbors.assign(g.n, {});
    for (const Edge& e : g.edges) {
        g.neighbors[e.u].push_back({e.v, e.t});
        g.neighbors[e.v].push_back({e.u, e.t});
    }
    for (int i = 0; i < g.n; ++i) {
        std::sort(g.neighbors[i].begin(), g.neighbors[i].end());
    }
}

inline Graph graph_from_distance(const std::vector<std::vector<value_t>>& dist, value_t threshold) {
    Graph g;
    g.n = static_cast<int>(dist.size());
    for (int i = 0; i < g.n; ++i) {
        for (int j = i + 1; j < g.n; ++j) {
            const value_t t = dist[i][j];
            if (t <= threshold) g.edges.push_back({i, j, t});
        }
    }
    rebuild_neighbors(g);
    return g;
}

inline value_t lookup_time(const std::vector<std::pair<index_t, value_t>>& row, index_t v) {
    auto it = std::lower_bound(row.begin(), row.end(), std::make_pair(v, kNegInf));
    if (it == row.end() || it->first != v) return kInf;
    return it->second;
}

}  // namespace pith
