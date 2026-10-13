#pragma once

#include "persist.hpp"

namespace pith {

// I231/I232: owned H1 active enumeration (RedZeD idea, not the vendor copy).
// Process leftover edges in filtration order. A triangle is generated only
// when the leftover being processed is a youngest face. I232: F₂ annotations
// R / Ri (Kapulkin–Kershaw resolve_bar) skip empty-XOR (H₂-birth) columns
// instead of running persist_sparse reduce on every triangle. Shape-agnostic.
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
    // I232: R[x] = annotation of leftover x; Ri[y] = leftovers whose R
    // contains y. Live birth ⇔ Ri nonempty (RedZeD emit_infinite). R may
    // stay after pairing so a later triangle can XOR the transferred
    // annotation — clearing R[j] on pair missed the unit-square death
    // (I231: 023 after 012 dead still reduces onto the older leftover).
    std::vector<std::vector<int>> R(static_cast<size_t>(m)), Ri(static_cast<size_t>(m));
    for (int i = 0; i < m; ++i) {
        R[static_cast<size_t>(i)] = {i};
        Ri[static_cast<size_t>(i)] = {i};
    }

    auto xor_sorted = [](std::vector<int>& a, const std::vector<int>& b) {
        std::vector<int> out;
        out.reserve(a.size() + b.size());
        size_t i = 0, j = 0;
        while (i < a.size() && j < b.size()) {
            if (a[i] == b[j]) {
                ++i;
                ++j;
            } else if (a[i] < b[j]) {
                out.push_back(a[i++]);
            } else {
                out.push_back(b[j++]);
            }
        }
        while (i < a.size()) out.push_back(a[i++]);
        while (j < b.size()) out.push_back(b[j++]);
        a.swap(out);
    };

    auto remove_elem = [](std::vector<int>& a, int y) {
        auto it = std::lower_bound(a.begin(), a.end(), y);
        if (it != a.end() && *it == y) a.erase(it);
    };

    auto resolve_bar = [&](std::vector<int>& bar, value_t td) {
        if (bar.empty()) return;
        const int j = bar.back();
        if (td > leftover[static_cast<size_t>(j)].t * ratio)
            r.pairs.push_back({1, leftover[static_cast<size_t>(j)].t, td});
        ++c.n_columns_reduced;
        std::vector<int> touched = Ri[static_cast<size_t>(j)];
        if (bar.size() == 1) {
            Ri[static_cast<size_t>(j)].clear();
            for (int z : touched) {
                remove_elem(R[static_cast<size_t>(z)], j);
                if (R[static_cast<size_t>(z)].empty()) Ri[static_cast<size_t>(z)].clear();
            }
            return;
        }
        std::vector<int> others;
        others.reserve(bar.size() - 1);
        for (int y : bar)
            if (y != j) others.push_back(y);
        for (int z : touched) {
            xor_sorted(R[static_cast<size_t>(z)], bar);
            ++c.n_additions;
            if (R[static_cast<size_t>(z)].empty()) Ri[static_cast<size_t>(z)].clear();
        }
        for (int y : others) xor_sorted(Ri[static_cast<size_t>(y)], touched);
        Ri[static_cast<size_t>(j)].clear();
        // R[j] stays if nonempty — annotation carrier for later cofaces.
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
        std::vector<int> bar;
        for (int k = 0; k < n_left; ++k) {
            const int f = ids[k];
            if (f < 0 || R[static_cast<size_t>(f)].empty()) continue;
            xor_sorted(bar, R[static_cast<size_t>(f)]);
        }
        if (bar.empty()) {
            ++c.n_columns_apparent;  // I232: empty XOR = H2 birth, skip
            return false;
        }
        resolve_bar(bar, td);
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
        if (!Ri[static_cast<size_t>(i)].empty())
            r.pairs.push_back({1, leftover[static_cast<size_t>(i)].t, kInf});
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
