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

// How the insertion-radius cap is combined. I210 used Max (looser, denser).
// I212 tries Min (closer to GUDHI's thinner 1-skeleton).
enum class SparseCap { Max, Min };

// Cavanna–Jahanseir–Sheehy / GUDHI-style sparse Rips 1-skeleton.
// Keep (i,j) iff d(i,j) ≤ T and d(i,j) ≤ ((1+ε)/ε) · cap(λ_i, λ_j).
// This is exact PH of the *flag* of that subgraph, not of VR(G_T).
inline Graph sparse_rips_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                               value_t eps, SparseCap cap = SparseCap::Max) {
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
            const value_t li = lam[static_cast<size_t>(i)];
            const value_t lj = lam[static_cast<size_t>(j)];
            const value_t rad = (cap == SparseCap::Min) ? std::min(li, lj) : std::max(li, lj);
            if (d <= c * rad) g.edges.push_back({i, j, d});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I220: undirected kNN 1-skeleton. Keep (i,j) iff d≤T and i is among j's
// K nearest (or vice versa). Flag PH of this graph is not exact VR.
// |E| ≤ nK. Shape-agnostic. I021 rejected k=16 as exact-VR.
inline Graph knn_flag_graph(const std::vector<std::vector<value_t>>& dist, value_t T, int K) {
    const int n = static_cast<int>(dist.size());
    Graph g;
    g.n = n;
    if (n < 2 || K <= 0) return g;
    std::vector<char> keep(static_cast<size_t>(n) * static_cast<size_t>(n), 0);
    std::vector<std::pair<value_t, int>> row;
    row.reserve(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        row.clear();
        const value_t* di = dist[static_cast<size_t>(i)].data();
        for (int j = 0; j < n; ++j) {
            if (j == i) continue;
            const value_t d = di[j];
            if (d <= T) row.push_back({d, j});
        }
        const int k = std::min(K, static_cast<int>(row.size()));
        if (k > 0 && k < static_cast<int>(row.size()))
            std::nth_element(row.begin(), row.begin() + k, row.end());
        for (int t = 0; t < k; ++t) {
            const int j = row[static_cast<size_t>(t)].second;
            keep[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)] = 1;
        }
    }
    g.edges.reserve(static_cast<size_t>(n) * static_cast<size_t>(std::max(K, 1)));
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            const size_t ij = static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j);
            const size_t ji = static_cast<size_t>(j) * static_cast<size_t>(n) + static_cast<size_t>(i);
            if (keep[ij] || keep[ji])
                g.edges.push_back({static_cast<index_t>(i), static_cast<index_t>(j),
                                   dist[static_cast<size_t>(i)][static_cast<size_t>(j)]});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I216: first `m` vertices of a farthest-point (greedy) permutation.
inline std::vector<index_t> greedy_landmarks(const std::vector<std::vector<value_t>>& dist, int m) {
    const int n = static_cast<int>(dist.size());
    if (m > n) m = n;
    std::vector<index_t> L;
    if (n <= 0 || m <= 0) return L;
    L.reserve(static_cast<size_t>(m));
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<value_t> mind(static_cast<size_t>(n), kInf);
    L.push_back(0);
    used[0] = 1;
    for (int j = 1; j < n; ++j) mind[static_cast<size_t>(j)] = dist[0][static_cast<size_t>(j)];
    for (int k = 1; k < m; ++k) {
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
        L.push_back(static_cast<index_t>(best));
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            mind[static_cast<size_t>(j)] =
                std::min(mind[static_cast<size_t>(j)],
                         dist[static_cast<size_t>(best)][static_cast<size_t>(j)]);
        }
    }
    return L;
}

// de Silva–Carlsson lazy witness 1-skeleton on farthest-point landmarks.
// Edge {a,b} ⊂ L enters at t = min_w max(0, max(d(w,a), d(w,b)) − m_ν(w)),
// where m_0 = 0 and m_ν (ν≥1) is the distance from w to its ν-th nearest
// landmark. Flag PH of this graph is a different complex than VR≤T.
// Construction O(n m²); PH is on m vertices (not n). Shape-agnostic.
inline Graph lazy_witness_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                                int nland, int nu) {
    const int n = static_cast<int>(dist.size());
    const auto L = greedy_landmarks(dist, nland);
    const int m = static_cast<int>(L.size());
    Graph g;
    g.n = m;
    if (m < 2) return g;
    std::vector<value_t> tpair(static_cast<size_t>(m) * static_cast<size_t>(m), kInf);
    std::vector<value_t> dw(static_cast<size_t>(m));
    std::vector<value_t> tmp(static_cast<size_t>(m));
    for (int w = 0; w < n; ++w) {
        for (int i = 0; i < m; ++i)
            dw[static_cast<size_t>(i)] = dist[static_cast<size_t>(w)][static_cast<size_t>(L[static_cast<size_t>(i)])];
        value_t mnu = 0;
        if (nu > 0 && m > 0) {
            tmp = dw;
            const int kth = std::min(nu, m);
            std::nth_element(tmp.begin(), tmp.begin() + (kth - 1), tmp.end());
            mnu = tmp[static_cast<size_t>(kth - 1)];
        }
        for (int i = 0; i < m; ++i) {
            for (int j = i + 1; j < m; ++j) {
                value_t t = std::max(dw[static_cast<size_t>(i)], dw[static_cast<size_t>(j)]) - mnu;
                if (t < 0) t = 0;
                value_t& slot = tpair[static_cast<size_t>(i) * static_cast<size_t>(m) + static_cast<size_t>(j)];
                if (t < slot) slot = t;
            }
        }
    }
    g.edges.reserve(static_cast<size_t>(m) * 4);
    for (int i = 0; i < m; ++i) {
        for (int j = i + 1; j < m; ++j) {
            const value_t t = tpair[static_cast<size_t>(i) * static_cast<size_t>(m) + static_cast<size_t>(j)];
            if (t <= T) g.edges.push_back({static_cast<index_t>(i), static_cast<index_t>(j), t});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I222: graph-induced 1-skeleton (Dey–Fan–Wang style, flag of the quotient).
// Farthest-point landmarks L; each point maps to its nearest landmark;
// a kNN edge that crosses two cells gives a landmark edge at that length.
// PH is on |L| vertices. Not exact VR — quantify loss.
inline Graph gic_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                       int nland, int K) {
    const int n = static_cast<int>(dist.size());
    const auto L = greedy_landmarks(dist, nland);
    const int m = static_cast<int>(L.size());
    Graph g;
    g.n = m;
    if (m < 2 || K <= 0) return g;
    std::vector<int> assign(static_cast<size_t>(n), 0);
    for (int i = 0; i < n; ++i) {
        int best = 0;
        value_t bd = dist[static_cast<size_t>(i)][static_cast<size_t>(L[0])];
        for (int a = 1; a < m; ++a) {
            const value_t d = dist[static_cast<size_t>(i)][static_cast<size_t>(L[static_cast<size_t>(a)])];
            if (d < bd) {
                bd = d;
                best = a;
            }
        }
        assign[static_cast<size_t>(i)] = best;
    }
    std::vector<value_t> tpair(static_cast<size_t>(m) * static_cast<size_t>(m), kInf);
    std::vector<std::pair<value_t, int>> row;
    row.reserve(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        row.clear();
        const value_t* di = dist[static_cast<size_t>(i)].data();
        for (int j = 0; j < n; ++j) {
            if (j == i) continue;
            if (di[j] <= T) row.push_back({di[j], j});
        }
        const int k = std::min(K, static_cast<int>(row.size()));
        if (k > 0 && k < static_cast<int>(row.size()))
            std::nth_element(row.begin(), row.begin() + k, row.end());
        const int ai = assign[static_cast<size_t>(i)];
        for (int t = 0; t < k; ++t) {
            const int j = row[static_cast<size_t>(t)].second;
            const int aj = assign[static_cast<size_t>(j)];
            if (ai == aj) continue;
            const int a = std::min(ai, aj);
            const int b = std::max(ai, aj);
            value_t& slot = tpair[static_cast<size_t>(a) * static_cast<size_t>(m) + static_cast<size_t>(b)];
            if (di[j] < slot) slot = di[j];
        }
    }
    g.edges.reserve(static_cast<size_t>(m) * 4);
    for (int a = 0; a < m; ++a) {
        for (int b = a + 1; b < m; ++b) {
            const value_t t = tpair[static_cast<size_t>(a) * static_cast<size_t>(m) + static_cast<size_t>(b)];
            if (t <= T) g.edges.push_back({static_cast<index_t>(a), static_cast<index_t>(b), t});
        }
    }
    rebuild_neighbors(g);
    return g;
}

}  // namespace pith
