#pragma once

#include "types.hpp"

#include <utility>

namespace pith {

// I269: Morton-order points so collapse LiveBits AND-eq stays in a
// short [rlo,rhi] span. Same VR (isometry). n<256 unchanged.
inline std::uint64_t morton_split1(std::uint32_t v) {
    std::uint64_t x = v;
    x = (x | (x << 16)) & 0x0000FFFF0000FFFFULL;
    x = (x | (x << 8)) & 0x00FF00FF00FF00FFULL;
    x = (x | (x << 4)) & 0x0F0F0F0F0F0F0F0FULL;
    x = (x | (x << 2)) & 0x3333333333333333ULL;
    x = (x | (x << 1)) & 0x5555555555555555ULL;
    return x;
}

inline std::uint32_t morton_part1by2(std::uint32_t n) {
    n &= 0x000003FFu;
    n = (n | (n << 16)) & 0x030000FFu;
    n = (n | (n << 8)) & 0x0300F00Fu;
    n = (n | (n << 4)) & 0x030C30C3u;
    n = (n | (n << 2)) & 0x09249249u;
    return n;
}

inline void morton_permute_points(std::vector<std::vector<value_t>>& pts) {
    const int n = static_cast<int>(pts.size());
    if (n < 256) return;
    const int d = static_cast<int>(pts[0].size());
    if (d < 2 || d > 3) return;
    std::vector<double> lo(static_cast<size_t>(d)), hi(static_cast<size_t>(d));
    for (int k = 0; k < d; ++k) {
        lo[static_cast<size_t>(k)] = static_cast<double>(pts[0][static_cast<size_t>(k)]);
        hi[static_cast<size_t>(k)] = lo[static_cast<size_t>(k)];
    }
    for (int i = 1; i < n; ++i) {
        for (int k = 0; k < d; ++k) {
            const double x = static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]);
            if (x < lo[static_cast<size_t>(k)]) lo[static_cast<size_t>(k)] = x;
            if (x > hi[static_cast<size_t>(k)]) hi[static_cast<size_t>(k)] = x;
        }
    }
    const double qmax = (d == 2) ? 65535.0 : 1023.0;
    std::vector<std::pair<std::uint64_t, int>> keys(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        std::uint32_t q[3] = {0, 0, 0};
        for (int k = 0; k < d; ++k) {
            const double span = hi[static_cast<size_t>(k)] - lo[static_cast<size_t>(k)];
            double t = (span > 0.0)
                           ? (static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) -
                              lo[static_cast<size_t>(k)]) /
                                 span
                           : 0.0;
            if (t < 0.0) t = 0.0;
            if (t > 1.0) t = 1.0;
            q[static_cast<size_t>(k)] = static_cast<std::uint32_t>(t * qmax + 0.5);
        }
        const std::uint64_t code = (d == 2) ? (morton_split1(q[0]) | (morton_split1(q[1]) << 1))
                                       : (static_cast<std::uint64_t>(morton_part1by2(q[0])) |
                                          (static_cast<std::uint64_t>(morton_part1by2(q[1])) << 1) |
                                          (static_cast<std::uint64_t>(morton_part1by2(q[2])) << 2));
        keys[static_cast<size_t>(i)] = {code, i};
    }
    std::sort(keys.begin(), keys.end());
    bool ident = true;
    for (int i = 0; i < n; ++i) {
        if (keys[static_cast<size_t>(i)].second != i) {
            ident = false;
            break;
        }
    }
    if (ident) return;
    std::vector<std::vector<value_t>> nxt(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i)
        nxt[static_cast<size_t>(i)] = std::move(pts[static_cast<size_t>(keys[static_cast<size_t>(i)].second)]);
    pts.swap(nxt);
}

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

// I207: consume an arbitrary 1-skeleton (Sheehy / witness / kNN). Isolated
// vertices are kept via n so H0 is well-defined.
inline Graph graph_from_edge_list(int n, const std::vector<Edge>& edges, value_t threshold) {
    Graph g;
    g.n = n;
    g.edges.reserve(edges.size());
    for (Edge e : edges) {
        normalize_edge(e);
        if (e.u == e.v) continue;
        if (e.u < 0 || e.v >= n) continue;
        if (e.t <= threshold) g.edges.push_back(e);
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
