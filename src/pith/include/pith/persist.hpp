#pragma once

#include "graph.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <numeric>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace pith {

inline std::uint64_t pack2(index_t a, index_t b) {
    if (a > b) std::swap(a, b);
    return (static_cast<std::uint64_t>(b) << 21) | static_cast<std::uint32_t>(a);
}

inline std::uint64_t pack3(index_t a, index_t b, index_t c) {
    index_t v[3] = {a, b, c};
    std::sort(v, v + 3);
    return (static_cast<std::uint64_t>(v[2]) << 42) |
           (static_cast<std::uint64_t>(v[1]) << 21) |
           static_cast<std::uint32_t>(v[0]);
}

struct UnionFind {
    std::vector<index_t> p, r;
    explicit UnionFind(int n) : p(n), r(n, 0) { std::iota(p.begin(), p.end(), 0); }
    index_t find(index_t x) { return p[x] == x ? x : p[x] = find(p[x]); }
    bool unite(index_t a, index_t b) {
        a = find(a);
        b = find(b);
        if (a == b) return false;
        if (r[a] < r[b]) std::swap(a, b);
        p[b] = a;
        if (r[a] == r[b]) ++r[a];
        return true;
    }
};

inline value_t edge_time(const Graph& g, index_t a, index_t b) {
    return lookup_time(g.neighbors[a], b);
}

// Standard persistent homology in dimension 1: reduce triangle *boundaries*
// over leftover (non-MST) edges. Pivot = youngest leftover edge.
inline Result persist_sparse(const Graph& g, int maxdim, value_t threshold, value_t ratio) {
    Result r;
    Counters& c = r.counters;
    c.n_vertices = g.n;
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
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

    struct Tri {
        index_t a, b, c;
        value_t t;
        int e[3];
        int n_left = 0;
    };
    std::vector<Tri> tris;
    tris.reserve(leftover.size() * 4);

    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        const auto& nu = g.neighbors[e.u];
        const auto& nv = g.neighbors[e.v];
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
            if (w != e.u && w != e.v && w > e.u && w > e.v) {
                const value_t twu = nu[i].second;
                const value_t twv = nv[j].second;
                if (twu <= threshold && twv <= threshold) {
                    const value_t td = std::max({e.t, twu, twv});
                    if (td <= threshold) {
                        Tri tr;
                        tr.a = e.u;
                        tr.b = e.v;
                        tr.c = w;
                        tr.t = td;
                        const std::uint64_t k0 = pack2(e.u, e.v);
                        const std::uint64_t k1 = pack2(e.u, w);
                        const std::uint64_t k2 = pack2(e.v, w);
                        auto add = [&](std::uint64_t k) {
                            auto it = edge_id.find(k);
                            if (it != edge_id.end()) tr.e[tr.n_left++] = it->second;
                        };
                        add(k0);
                        add(k1);
                        add(k2);
                        if (tr.n_left) {
                            tris.push_back(tr);
                            ++c.n_simplices_enumerated;
                        }
                    }
                }
            }
            ++i;
            ++j;
        }
    }

    std::sort(tris.begin(), tris.end(), [](const Tri& a, const Tri& b) {
        if (a.t != b.t) return a.t < b.t;
        return pack3(a.a, a.b, a.c) < pack3(b.a, b.b, b.c);
    });

    // F2 columns on leftover-edge ids. Pivot = youngest leftover edge
    // (latest birth, then largest id) still in the reduced boundary.
    const int m = static_cast<int>(leftover.size());
    std::vector<std::vector<int>> reduced;
    reduced.reserve(tris.size());
    std::vector<int> pivot_of(m, -1);  // leftover edge -> triangle column
    std::vector<char> paired(m, 0);
    std::vector<std::uint64_t> h2_birth_keys;
    std::vector<value_t> h2_birth_t;

    auto xor_sorted = [](std::vector<int>& a, const std::vector<int>& b) {
        std::vector<int> out;
        out.reserve(a.size() + b.size());
        size_t i = 0, j = 0;
        while (i < a.size() && j < b.size()) {
            if (a[i] == b[j]) {
                ++i;
                ++j;
            } else if (a[i] > b[j]) {  // store descending so front is youngest-ish by id; we pick pivot by birth
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
            const value_t t = leftover[id].t;
            if (t > best_t || (t == best_t && id > best)) {
                best_t = t;
                best = id;
            }
        }
        return best;
    };

    for (const Tri& tr : tris) {
        ++c.n_columns_assembled;
        std::vector<int> col(tr.e, tr.e + tr.n_left);
        std::sort(col.begin(), col.end(), std::greater<int>());
        col.erase(std::unique(col.begin(), col.end()), col.end());
        ++c.n_columns_reduced;
        int guard = 0;
        while (!col.empty() && guard++ < 200000) {
            const int p = choose_pivot(col);
            if (p < 0 || pivot_of[p] < 0) break;
            xor_sorted(col, reduced[pivot_of[p]]);
            ++c.n_additions;
        }
        if (col.empty()) {
            h2_birth_keys.push_back(pack3(tr.a, tr.b, tr.c));
            h2_birth_t.push_back(tr.t);
            continue;
        }
        const int p = choose_pivot(col);
        if (p < 0) continue;
        if (tr.t > leftover[p].t * ratio) r.pairs.push_back({1, leftover[p].t, tr.t});
        pivot_of[p] = static_cast<int>(reduced.size());
        paired[p] = 1;
        reduced.push_back(std::move(col));
    }
    for (int i = 0; i < m; ++i) {
        if (!paired[i]) r.pairs.push_back({1, leftover[i].t, kInf});
    }

    if (maxdim >= 2 && !h2_birth_keys.empty()) {
        std::unordered_map<std::uint64_t, int> birth_id;
        birth_id.reserve(h2_birth_keys.size() * 2);
        for (size_t i = 0; i < h2_birth_keys.size(); ++i) birth_id[h2_birth_keys[i]] = static_cast<int>(i);
        const int nt = static_cast<int>(h2_birth_keys.size());

        struct Tet {
            value_t t;
            int faces[4];
            int n_left = 0;
        };
        std::vector<Tet> tets;
        for (const Tri& tr : tris) {
            const auto& na = g.neighbors[tr.a];
            const auto& nb = g.neighbors[tr.b];
            const auto& nc = g.neighbors[tr.c];
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
                    if (w > tr.a && w > tr.b && w > tr.c) {
                        const value_t tw = std::max({tr.t, edge_time(g, tr.a, w),
                                                     edge_time(g, tr.b, w), edge_time(g, tr.c, w)});
                        if (tw <= threshold) {
                            const std::uint64_t f[4] = {pack3(tr.a, tr.b, tr.c), pack3(tr.a, tr.b, w),
                                                        pack3(tr.a, tr.c, w), pack3(tr.b, tr.c, w)};
                            Tet tet;
                            tet.t = tw;
                            for (int u = 0; u < 4; ++u) {
                                auto it = birth_id.find(f[u]);
                                if (it != birth_id.end()) tet.faces[tet.n_left++] = it->second;
                            }
                            if (tet.n_left) {
                                tets.push_back(tet);
                                ++c.n_simplices_enumerated;
                            }
                        }
                    }
                    ++k;
                    ++p;
                }
            }
        }
        std::sort(tets.begin(), tets.end(), [](const Tet& a, const Tet& b) { return a.t < b.t; });

        std::vector<std::vector<int>> red2;
        std::vector<int> piv2(nt, -1);
        std::vector<char> paired_tri(nt, 0);
        auto choose_piv2 = [&](const std::vector<int>& col) -> int {
            int best = -1;
            value_t best_t = -1;
            for (int id : col) {
                const value_t t = h2_birth_t[id];
                if (t > best_t || (t == best_t && id > best)) {
                    best_t = t;
                    best = id;
                }
            }
            return best;
        };
        for (const Tet& tet : tets) {
            ++c.n_columns_assembled;
            std::vector<int> col(tet.faces, tet.faces + tet.n_left);
            std::sort(col.begin(), col.end(), std::greater<int>());
            col.erase(std::unique(col.begin(), col.end()), col.end());
            ++c.n_columns_reduced;
            int guard = 0;
            while (!col.empty() && guard++ < 200000) {
                const int p = choose_piv2(col);
                if (p < 0 || piv2[p] < 0) break;
                xor_sorted(col, red2[piv2[p]]);
                ++c.n_additions;
            }
            if (col.empty()) continue;
            const int p = choose_piv2(col);
            if (p < 0) continue;
            if (tet.t > h2_birth_t[p] * ratio) r.pairs.push_back({2, h2_birth_t[p], tet.t});
            piv2[p] = static_cast<int>(red2.size());
            paired_tri[p] = 1;
            red2.push_back(std::move(col));
        }
        for (int i = 0; i < nt; ++i) {
            if (!paired_tri[i]) r.pairs.push_back({2, h2_birth_t[i], kInf});
        }
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
