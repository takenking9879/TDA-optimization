#pragma once

#include "persist.hpp"

namespace pith {

// I231: owned H1 active enumeration (RedZeD idea, not the vendor copy).
// Process leftover edges in filtration order. A triangle is generated only
// when the leftover being processed is a youngest face — that skips most
// (n+1)-birth columns. Generation stops for that leftover once it is paired.
// Same leftover-boundary F₂ reduce as persist_sparse. Shape-agnostic: one
// path on every flag graph.
inline Result persist_active_h1(const Graph& g, int maxdim, value_t threshold,
                                value_t ratio) {
    Result r;
    Counters& c = r.counters;
    c.n_vertices = g.n;
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    c.pipeline = "pith:active-h1";
    const auto t0 = std::chrono::steady_clock::now();

    std::vector<Edge> edges = g.edges;
    std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t < b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });

    UnionFind uf(g.n);
    struct BirthEdge {
        index_t u, v;
        value_t t;
        int id;
    };
    std::vector<BirthEdge> leftover;
    leftover.reserve(edges.size());
    int components = g.n;
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        if (uf.unite(e.u, e.v)) {
            --components;
            r.pairs.push_back({0, 0, e.t});
            ++c.n_columns_cleared;
        } else {
            leftover.push_back({e.u, e.v, e.t, static_cast<int>(leftover.size())});
        }
    }
    for (int i = 0; i < components; ++i) r.pairs.push_back({0, 0, kInf});

    if (maxdim < 1) {
        const auto t1 = std::chrono::steady_clock::now();
        c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        c.rss_bytes_peak = peak_rss_bytes();
        return r;
    }

    std::unordered_map<std::uint64_t, int> edge_id;
    edge_id.reserve(leftover.size() * 2);
    for (const auto& e : leftover) edge_id[pack2(e.u, e.v)] = e.id;

    const int m = static_cast<int>(leftover.size());
    std::vector<std::vector<int>> reduced;
    reduced.reserve(static_cast<size_t>(m));
    std::vector<int> pivot_of(m, -1);
    std::vector<char> paired(m, 0);

    auto xor_sorted = [](std::vector<int>& a, const std::vector<int>& b) {
        std::vector<int> out;
        out.reserve(a.size() + b.size());
        size_t i = 0, j = 0;
        while (i < a.size() && j < b.size()) {
            if (a[i] == b[j]) {
                ++i;
                ++j;
            } else if (a[i] > b[j]) {
                out.push_back(a[i++]);
            } else {
                out.push_back(b[j++]);
            }
        }
        while (i < a.size()) out.push_back(a[i++]);
        while (j < b.size()) out.push_back(b[j++]);
        a.swap(out);
    };

    auto choose_pivot = [&](const std::vector<int>& col) -> int {
        int best = -1;
        value_t best_t = -1;
        for (int id : col) {
            const value_t t = leftover[static_cast<size_t>(id)].t;
            if (t > best_t || (t == best_t && id > best)) {
                best_t = t;
                best = id;
            }
        }
        return best;
    };

    auto reduce_tri = [&](int e0, int e1, int e2, value_t td) -> bool {
        int ids[3];
        int n_left = 0;
        if (e0 >= 0) ids[n_left++] = e0;
        if (e1 >= 0) ids[n_left++] = e1;
        if (e2 >= 0) ids[n_left++] = e2;
        if (!n_left) return false;
        ++c.n_simplices_enumerated;
        ++c.n_columns_assembled;
        std::vector<int> col(ids, ids + n_left);
        std::sort(col.begin(), col.end(), std::greater<int>());
        col.erase(std::unique(col.begin(), col.end()), col.end());
        ++c.n_columns_reduced;
        int guard = 0;
        while (!col.empty() && guard++ < 200000) {
            const int p = choose_pivot(col);
            if (p < 0 || pivot_of[static_cast<size_t>(p)] < 0) break;
            xor_sorted(col, reduced[static_cast<size_t>(pivot_of[static_cast<size_t>(p)])]);
            ++c.n_additions;
        }
        if (col.empty()) return false;
        const int p = choose_pivot(col);
        if (p < 0) return false;
        if (td > leftover[static_cast<size_t>(p)].t * ratio)
            r.pairs.push_back({1, leftover[static_cast<size_t>(p)].t, td});
        pivot_of[static_cast<size_t>(p)] = static_cast<int>(reduced.size());
        paired[static_cast<size_t>(p)] = 1;
        reduced.push_back(std::move(col));
        return true;
    };

    auto leftover_of = [&](index_t a, index_t b) -> int {
        auto it = edge_id.find(pack2(a, b));
        return it == edge_id.end() ? -1 : it->second;
    };

    // e is a youngest face of ⟨uvw⟩ (diameter, then later leftover id).
    auto e_youngest = [&](const BirthEdge& e, index_t w, value_t twu, value_t twv) {
        if (twu > e.t || twv > e.t) return false;
        if (twu == e.t) {
            const int oid = leftover_of(e.u, w);
            if (oid > e.id) return false;
        }
        if (twv == e.t) {
            const int oid = leftover_of(e.v, w);
            if (oid > e.id) return false;
        }
        return true;
    };

    for (const BirthEdge& e : leftover) {
        if (paired[static_cast<size_t>(e.id)]) continue;
        const auto& nu = g.neighbors[static_cast<size_t>(e.u)];
        const auto& nv = g.neighbors[static_cast<size_t>(e.v)];
        size_t i = 0, j = 0;
        while (i < nu.size() && j < nv.size()) {
            if (nu[i].first < nv[j].first) {
                ++i;
                continue;
            }
            if (nv[j].first < nu[i].first) {
                ++j;
                continue;
            }
            const index_t w = nu[i].first;
            ++c.n_cofacet_probes;
            if (w != e.u && w != e.v) {
                const value_t twu = nu[i].second;
                const value_t twv = nv[j].second;
                if (twu <= threshold && twv <= threshold && e_youngest(e, w, twu, twv)) {
                    const value_t td = e.t;
                    reduce_tri(e.id, leftover_of(e.u, w), leftover_of(e.v, w), td);
                }
            }
            ++i;
            ++j;
        }
    }

    for (int i = 0; i < m; ++i) {
        if (!paired[static_cast<size_t>(i)]) r.pairs.push_back({1, leftover[static_cast<size_t>(i)].t, kInf});
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
