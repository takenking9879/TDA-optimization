#pragma once

#include "persist.hpp"

namespace pith {

// Owned active PH (RedZeD idea, not the vendor copy). Shape-agnostic.
// H0: Kruskal. H1: leftover youngest-face triangles + R/Ri resolve_bar
// (I232). Empty face-XOR is an H2 birth. I233 live-star generation is
// reverted — it invented H1 bars on real clouds (dead-partner cofaces).
// H2: annotation reduce of tets on those empty-XOR triangles.
inline Result persist_active_h1(const Graph& g, int maxdim, value_t threshold,
                                value_t ratio) {
    Result r;
    Counters& c = r.counters;
    c.n_vertices = g.n;
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    c.pipeline = (maxdim >= 2) ? "pith:active-h012" : "pith:active-h1";
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
    std::vector<std::vector<int>> R(static_cast<size_t>(m)), Ri(static_cast<size_t>(m));
    for (int i = 0; i < m; ++i) {
        R[static_cast<size_t>(i)] = {i};
        Ri[static_cast<size_t>(i)] = {i};
    }

    struct H2Tri {
        index_t a, b, c;
        value_t t;
    };
    std::vector<H2Tri> h2_births;
    if (maxdim >= 2) h2_births.reserve(static_cast<size_t>(m));

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

    auto resolve_bar = [&](std::vector<std::vector<int>>& Rd, std::vector<std::vector<int>>& Rid,
                           const std::vector<value_t>& birth_t, int dim, std::vector<int>& bar,
                           value_t td) {
        if (bar.empty()) return;
        const int j = bar.back();
        if (td > birth_t[static_cast<size_t>(j)] * ratio)
            r.pairs.push_back({dim, birth_t[static_cast<size_t>(j)], td});
        ++c.n_columns_reduced;
        std::vector<int> touched = Rid[static_cast<size_t>(j)];
        if (bar.size() == 1) {
            Rid[static_cast<size_t>(j)].clear();
            for (int z : touched) {
                remove_elem(Rd[static_cast<size_t>(z)], j);
                if (Rd[static_cast<size_t>(z)].empty()) Rid[static_cast<size_t>(z)].clear();
            }
            return;
        }
        std::vector<int> others;
        others.reserve(bar.size() - 1);
        for (int y : bar)
            if (y != j) others.push_back(y);
        for (int z : touched) {
            xor_sorted(Rd[static_cast<size_t>(z)], bar);
            ++c.n_additions;
            if (Rd[static_cast<size_t>(z)].empty()) Rid[static_cast<size_t>(z)].clear();
        }
        for (int y : others) xor_sorted(Rid[static_cast<size_t>(y)], touched);
        Rid[static_cast<size_t>(j)].clear();
    };

    std::vector<value_t> leftover_t(static_cast<size_t>(m));
    for (int i = 0; i < m; ++i) leftover_t[static_cast<size_t>(i)] = leftover[static_cast<size_t>(i)].t;

    auto leftover_of = [&](index_t a, index_t b) -> int {
        auto it = edge_id.find(pack2(a, b));
        return it == edge_id.end() ? -1 : it->second;
    };

    auto reduce_tri = [&](int e0, int e1, int e2, value_t td, index_t a, index_t b,
                          index_t w) -> bool {
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
            ++c.n_columns_apparent;
            if (maxdim >= 2) h2_births.push_back({a, b, w, td});
            return false;
        }
        resolve_bar(R, Ri, leftover_t, 1, bar, td);
        return true;
    };

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
                if (twu <= threshold && twv <= threshold && e_youngest(e, w, twu, twv))
                    reduce_tri(e.id, leftover_of(e.u, w), leftover_of(e.v, w), e.t, e.u, e.v, w);
            }
            ++i;
            ++j;
        }
    }

    for (int i = 0; i < m; ++i) {
        if (!Ri[static_cast<size_t>(i)].empty())
            r.pairs.push_back({1, leftover[static_cast<size_t>(i)].t, kInf});
    }

    if (maxdim >= 2 && !h2_births.empty()) {
        std::sort(h2_births.begin(), h2_births.end(), [](const H2Tri& a, const H2Tri& b) {
            if (a.t != b.t) return a.t < b.t;
            return pack3(a.a, a.b, a.c) < pack3(b.a, b.b, b.c);
        });
        const int nt = static_cast<int>(h2_births.size());
        std::unordered_map<std::uint64_t, int> tri_id;
        tri_id.reserve(static_cast<size_t>(nt) * 2);
        std::vector<value_t> h2_t(static_cast<size_t>(nt));
        for (int i = 0; i < nt; ++i) {
            const H2Tri& tr = h2_births[static_cast<size_t>(i)];
            tri_id[pack3(tr.a, tr.b, tr.c)] = i;
            h2_t[static_cast<size_t>(i)] = tr.t;
        }
        std::vector<std::vector<int>> R2(static_cast<size_t>(nt)), Ri2(static_cast<size_t>(nt));
        for (int i = 0; i < nt; ++i) {
            R2[static_cast<size_t>(i)] = {i};
            Ri2[static_cast<size_t>(i)] = {i};
        }

        auto reduce_tet = [&](int f0, int f1, int f2, int f3, value_t td) {
            int ids[4];
            int n_left = 0;
            if (f0 >= 0) ids[n_left++] = f0;
            if (f1 >= 0) ids[n_left++] = f1;
            if (f2 >= 0) ids[n_left++] = f2;
            if (f3 >= 0) ids[n_left++] = f3;
            if (!n_left) return;
            ++c.n_simplices_enumerated;
            ++c.n_columns_assembled;
            std::vector<int> bar;
            for (int k = 0; k < n_left; ++k) {
                const int f = ids[k];
                if (R2[static_cast<size_t>(f)].empty()) continue;
                xor_sorted(bar, R2[static_cast<size_t>(f)]);
            }
            if (bar.empty()) {
                ++c.n_columns_apparent;
                return;
            }
            resolve_bar(R2, Ri2, h2_t, 2, bar, td);
        };

        auto pack4 = [](index_t a, index_t b, index_t c, index_t d) {
            index_t v[4] = {a, b, c, d};
            std::sort(v, v + 4);
            return (static_cast<std::uint64_t>(static_cast<std::uint16_t>(v[0]))) |
                   (static_cast<std::uint64_t>(static_cast<std::uint16_t>(v[1])) << 16) |
                   (static_cast<std::uint64_t>(static_cast<std::uint16_t>(v[2])) << 32) |
                   (static_cast<std::uint64_t>(static_cast<std::uint16_t>(v[3])) << 48);
        };
        std::unordered_set<std::uint64_t> seen_tet;
        seen_tet.reserve(static_cast<size_t>(nt));
        struct TetCol {
            value_t t;
            int f[4];
        };
        std::vector<TetCol> tets;
        tets.reserve(static_cast<size_t>(nt));
        auto id_of = [&](index_t x, index_t y, index_t z) -> int {
            auto it = tri_id.find(pack3(x, y, z));
            return it == tri_id.end() ? -1 : it->second;
        };

        for (int ti = 0; ti < nt; ++ti) {
            const H2Tri& tr = h2_births[static_cast<size_t>(ti)];
            const auto& na = g.neighbors[static_cast<size_t>(tr.a)];
            const auto& nb = g.neighbors[static_cast<size_t>(tr.b)];
            const auto& nc = g.neighbors[static_cast<size_t>(tr.c)];
            size_t i = 0, j = 0;
            std::vector<index_t> cab;
            while (i < na.size() && j < nb.size()) {
                if (na[i].first < nb[j].first) ++i;
                else if (nb[j].first < na[i].first) ++j;
                else {
                    cab.push_back(na[i].first);
                    ++i;
                    ++j;
                }
            }
            size_t k = 0, p = 0;
            while (k < cab.size() && p < nc.size()) {
                if (cab[k] < nc[p].first) ++k;
                else if (nc[p].first < cab[k]) ++p;
                else {
                    const index_t w = cab[k];
                    ++c.n_cofacet_probes;
                    if (w != tr.a && w != tr.b && w != tr.c) {
                        const value_t tw = std::max({tr.t, edge_time(g, tr.a, w),
                                                     edge_time(g, tr.b, w), edge_time(g, tr.c, w)});
                        if (tw <= threshold && seen_tet.insert(pack4(tr.a, tr.b, tr.c, w)).second) {
                            tets.push_back({tw,
                                            {id_of(tr.a, tr.b, tr.c), id_of(tr.a, tr.b, w),
                                             id_of(tr.a, tr.c, w), id_of(tr.b, tr.c, w)}});
                        }
                    }
                    ++k;
                    ++p;
                }
            }
        }
        std::sort(tets.begin(), tets.end(), [](const TetCol& a, const TetCol& b) { return a.t < b.t; });
        for (const TetCol& tet : tets) reduce_tet(tet.f[0], tet.f[1], tet.f[2], tet.f[3], tet.t);
        for (int i = 0; i < nt; ++i) {
            if (!Ri2[static_cast<size_t>(i)].empty())
                r.pairs.push_back({2, h2_t[static_cast<size_t>(i)], kInf});
        }
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
