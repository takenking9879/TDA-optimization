#pragma once

#include "graph.hpp"

#include <chrono>
#include <cstdint>
#include <numeric>
#include <queue>
#include <tuple>
#include <unordered_map>
#include <unordered_set>

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

inline std::uint64_t pack4(index_t a, index_t b, index_t c, index_t d) {
    index_t v[4] = {a, b, c, d};
    std::sort(v, v + 4);
    return (static_cast<std::uint64_t>(v[3]) << 48) |
           (static_cast<std::uint64_t>(v[2]) << 32) |
           (static_cast<std::uint64_t>(v[1]) << 16) |
           static_cast<std::uint16_t>(v[0]);
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

// F2 column as a max-heap of keys with cancellation (Ripser-style pop_pivot).
struct HeapColumn {
    std::priority_queue<std::uint64_t> heap;
    void push(std::uint64_t k) { heap.push(k); }
    bool empty() const { return heap.empty(); }
    std::uint64_t pop_pivot() {
        while (!heap.empty()) {
            const std::uint64_t k = heap.top();
            heap.pop();
            int c = 1;
            while (!heap.empty() && heap.top() == k) {
                heap.pop();
                ++c;
            }
            if (c & 1) return k;
        }
        return ~std::uint64_t{0};
    }
    std::uint64_t peek_pivot() {
        const std::uint64_t k = pop_pivot();
        if (k != ~std::uint64_t{0}) heap.push(k);
        return k;
    }
};

inline value_t edge_time(const Graph& g, index_t a, index_t b) {
    return lookup_time(g.neighbors[a], b);
}

inline std::vector<index_t> common_neighbors(const Graph& g, const std::vector<index_t>& verts,
                                            value_t threshold, Counters& c) {
    if (verts.empty()) return {};
    // Start from the lowest-degree vertex.
    int best = 0;
    for (size_t i = 1; i < verts.size(); ++i) {
        if (g.neighbors[verts[i]].size() < g.neighbors[verts[best]].size()) best = static_cast<int>(i);
    }
    std::vector<index_t> cand;
    cand.reserve(g.neighbors[verts[best]].size());
    for (const auto& [w, t] : g.neighbors[verts[best]]) {
        ++c.n_cofacet_probes;
        if (t > threshold) continue;
        bool skip = false;
        for (index_t v : verts) {
            if (v == w) {
                skip = true;
                break;
            }
        }
        if (skip) continue;
        bool ok = true;
        for (index_t v : verts) {
            if (v == verts[best]) continue;
            const value_t tw = edge_time(g, v, w);
            ++c.n_cofacet_probes;
            if (tw > threshold) {
                ok = false;
                break;
            }
        }
        if (ok) cand.push_back(w);
    }
    return cand;
}

inline value_t triangle_diam(const Graph& g, index_t a, index_t b, index_t c) {
    return std::max({edge_time(g, a, b), edge_time(g, a, c), edge_time(g, b, c)});
}

inline value_t tet_diam(const Graph& g, index_t a, index_t b, index_t c, index_t d) {
    return std::max({triangle_diam(g, a, b, c), edge_time(g, a, d), edge_time(g, b, d),
                     edge_time(g, c, d)});
}

struct Cofacet {
    std::uint64_t key = 0;
    value_t diam = 0;
    // sort: larger diameter first (younger), then larger key
    bool operator<(const Cofacet& o) const {
        if (diam != o.diam) return diam < o.diam;
        return key < o.key;
    }
};

inline bool cofacet_greater(const Cofacet& a, const Cofacet& b) {
    if (a.diam != b.diam) return a.diam > b.diam;
    return a.key > b.key;
}

inline void xor_column(std::vector<Cofacet>& col, const std::vector<Cofacet>& add) {
    std::vector<Cofacet> out;
    out.reserve(col.size() + add.size());
    size_t i = 0, j = 0;
    while (i < col.size() && j < add.size()) {
        if (col[i].key == add[j].key) {
            ++i;
            ++j;
        } else if (cofacet_greater(col[i], add[j])) {
            out.push_back(col[i++]);
        } else {
            out.push_back(add[j++]);
        }
    }
    while (i < col.size()) out.push_back(col[i++]);
    while (j < add.size()) out.push_back(add[j++]);
    col.swap(out);
}

inline std::vector<Cofacet> coboundary_edge(const Graph& g, index_t u, index_t v, value_t threshold,
                                           Counters& c) {
    std::vector<Cofacet> col;
    const auto ws = common_neighbors(g, {u, v}, threshold, c);
    col.reserve(ws.size());
    for (index_t w : ws) {
        Cofacet f;
        f.key = pack3(u, v, w);
        f.diam = triangle_diam(g, u, v, w);
        if (f.diam <= threshold) {
            col.push_back(f);
            ++c.n_simplices_enumerated;
        }
    }
    std::sort(col.begin(), col.end(), [](const Cofacet& a, const Cofacet& b) {
        if (a.diam != b.diam) return a.diam > b.diam;
        return a.key > b.key;
    });
    return col;
}

inline std::vector<Cofacet> coboundary_triangle(const Graph& g, index_t a, index_t b, index_t vc,
                                               value_t threshold, Counters& c) {
    std::vector<Cofacet> col;
    const auto ws = common_neighbors(g, {a, b, vc}, threshold, c);
    for (index_t w : ws) {
        Cofacet f;
        f.key = pack4(a, b, vc, w);
        f.diam = tet_diam(g, a, b, vc, w);
        if (f.diam <= threshold) {
            col.push_back(f);
            ++c.n_simplices_enumerated;
        }
    }
    std::sort(col.begin(), col.end(), [](const Cofacet& a, const Cofacet& b) {
        if (a.diam != b.diam) return a.diam > b.diam;
        return a.key > b.key;
    });
    return col;
}

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
    std::vector<Edge> h1_births;
    h1_births.reserve(edges.size());
    int components = g.n;
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        if (uf.unite(e.u, e.v)) {
            --components;
            r.pairs.push_back({0, 0, e.t});
            ++c.n_columns_cleared;
        } else {
            h1_births.push_back(e);
        }
    }
    for (int i = 0; i < components; ++i) r.pairs.push_back({0, 0, kInf});

    if (maxdim < 1) {
        const auto t1 = std::chrono::steady_clock::now();
        c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        c.rss_bytes_peak = peak_rss_bytes();
        return r;
    }

    // Reduce leftover edges (H1 cohomology / coboundaries = triangles).
    std::vector<std::vector<Cofacet>> reduced;
    reduced.reserve(h1_births.size());
    std::unordered_map<std::uint64_t, int> pivot;  // triangle key -> column
    pivot.reserve(h1_births.size() * 2);

    std::vector<int> h1_unpaired;
    std::vector<std::tuple<index_t, index_t, index_t, value_t>> h1_deaths;  // triangle + death

    for (const Edge& e : h1_births) {
        ++c.n_columns_assembled;
        auto col = coboundary_edge(g, e.u, e.v, threshold, c);
        ++c.n_columns_reduced;
        int guard = 0;
        while (!col.empty() && guard++ < 100000) {
            const std::uint64_t pk = col.front().key;
            auto it = pivot.find(pk);
            if (it == pivot.end()) break;
            xor_column(col, reduced[it->second]);
            ++c.n_additions;
        }
        if (col.empty()) {
            r.pairs.push_back({1, e.t, kInf});
            h1_unpaired.push_back(static_cast<int>(reduced.size()));
            reduced.push_back(std::move(col));
        } else {
            const Cofacet p = col.front();
            if (p.diam > e.t * ratio) r.pairs.push_back({1, e.t, p.diam});
            // unpack triangle vertices from key for dim-2 clearing
            const index_t a = static_cast<index_t>(p.key & ((1u << 21) - 1));
            const index_t b = static_cast<index_t>((p.key >> 21) & ((1u << 21) - 1));
            const index_t cc = static_cast<index_t>(p.key >> 42);
            h1_deaths.push_back({a, b, cc, p.diam});
            pivot[p.key] = static_cast<int>(reduced.size());
            reduced.push_back(std::move(col));
        }
    }

    if (maxdim >= 2) {
        // H2: triangles that were not H1 death pivots.
        std::unordered_set<std::uint64_t> killed;
        killed.reserve(h1_deaths.size() * 2);
        for (const auto& [a, b, cc, d] : h1_deaths) killed.insert(pack3(a, b, cc));

        struct Tri {
            index_t a, b, c;
            value_t t;
        };
        std::vector<Tri> h2_births;
        for (const Edge& e : edges) {
            if (e.t > threshold) continue;
            const auto ws = common_neighbors(g, {e.u, e.v}, threshold, c);
            for (index_t w : ws) {
                if (w < e.v) continue;  // emit each triangle once: w > max(u,v) after sort...
            }
        }
        // Enumerate each triangle once from its longest edge? Safer: from each edge with w > both.
        std::vector<Tri> all_tris;
        for (const Edge& e : edges) {
            if (e.t > threshold) continue;
            for (index_t w : common_neighbors(g, {e.u, e.v}, threshold, c)) {
                if (w <= e.u || w <= e.v) continue;
                const value_t td = triangle_diam(g, e.u, e.v, w);
                if (td > threshold) continue;
                const std::uint64_t key = pack3(e.u, e.v, w);
                if (killed.count(key)) {
                    ++c.n_columns_cleared;
                    continue;
                }
                all_tris.push_back({e.u, e.v, w, td});
            }
        }
        std::sort(all_tris.begin(), all_tris.end(), [](const Tri& a, const Tri& b) {
            if (a.t != b.t) return a.t < b.t;
            return pack3(a.a, a.b, a.c) < pack3(b.a, b.b, b.c);
        });

        std::vector<std::vector<Cofacet>> red2;
        std::unordered_map<std::uint64_t, int> pivot2;
        for (const Tri& tr : all_tris) {
            ++c.n_columns_assembled;
            auto col = coboundary_triangle(g, tr.a, tr.b, tr.c, threshold, c);
            ++c.n_columns_reduced;
            int guard = 0;
            while (!col.empty() && guard++ < 100000) {
                const std::uint64_t pk = col.front().key;
                auto it = pivot2.find(pk);
                if (it == pivot2.end()) break;
                xor_column(col, red2[it->second]);
                ++c.n_additions;
            }
            if (col.empty()) {
                r.pairs.push_back({2, tr.t, kInf});
                red2.push_back(std::move(col));
            } else {
                const Cofacet p = col.front();
                if (p.diam > tr.t * ratio) r.pairs.push_back({2, tr.t, p.diam});
                pivot2[p.key] = static_cast<int>(red2.size());
                red2.push_back(std::move(col));
            }
        }
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
