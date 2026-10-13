#pragma once

#include "graph.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <numeric>
#include <queue>
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

// Implicit persistent *cohomology* on a flag graph (Ripser-style).
// Columns = leftover (non-MST) edges, youngest first.
// Rows = triangles (packed keys). Never stores the 2-skeleton.
// Exact PH of Flag(G)≤T — the I003 bug was projecting coboundaries onto
// leftover *edges*; rows here are triangles. I045.
struct CohEntry {
    value_t t = kNegInf;
    std::uint64_t key = 0;
};

struct CohYounger {
    bool operator()(CohEntry a, CohEntry b) const {
        if (a.t != b.t) return a.t < b.t;
        return a.key < b.key;
    }
};

inline CohEntry pop_pivot_f2(std::priority_queue<CohEntry, std::vector<CohEntry>, CohYounger>& h) {
    while (!h.empty()) {
        const CohEntry p = h.top();
        h.pop();
        if (h.empty() || h.top().t != p.t || h.top().key != p.key) return p;
        h.pop();
    }
    return {kNegInf, 0};
}

template <class Fn>
inline void for_cofacets_edge(const Graph& g, index_t u, index_t v, value_t te, value_t T, Fn&& fn) {
    const auto& nu = g.neighbors[u];
    const auto& nv = g.neighbors[v];
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
        if (w != u && w != v) {
            const value_t td = std::max({te, nu[i].second, nv[j].second});
            if (td <= T) fn(CohEntry{td, pack3(u, v, w)});
        }
        ++i;
        ++j;
    }
}

inline void f2_xor_into(std::vector<int>& a, int x) { a.push_back(x); }

inline void f2_xor_into(std::vector<int>& a, const std::vector<int>& b) {
    a.insert(a.end(), b.begin(), b.end());
}

inline void f2_normalize(std::vector<int>& a) {
    if (a.size() < 2) return;
    std::sort(a.begin(), a.end(), std::greater<int>());
    std::vector<int> out;
    out.reserve(a.size());
    for (int x : a) {
        if (!out.empty() && out.back() == x) out.pop_back();
        else out.push_back(x);
    }
    a.swap(out);
}

inline bool zero_apparent_edge(const Graph& g, index_t u, index_t v, value_t te, value_t T,
                               CohEntry* out_tau) {
    // Apparent pair (Bauer): youngest cofacet τ of e, and e is the oldest facet of τ.
    CohEntry youngest{kNegInf, 0};
    bool any = false;
    for_cofacets_edge(g, u, v, te, T, [&](CohEntry tau) {
        if (!any || tau.t > youngest.t || (tau.t == youngest.t && tau.key > youngest.key)) {
            youngest = tau;
            any = true;
        }
    });
    if (!any || youngest.t != te) return false;
    const index_t a = static_cast<index_t>(youngest.key & ((1ull << 21) - 1));
    const index_t b = static_cast<index_t>((youngest.key >> 21) & ((1ull << 21) - 1));
    const index_t c = static_cast<index_t>(youngest.key >> 42);
    struct F {
        index_t x, y;
        value_t t;
        std::uint64_t k;
    };
    const F f[3] = {{a, b, edge_time(g, a, b), pack2(a, b)},
                    {a, c, edge_time(g, a, c), pack2(a, c)},
                    {b, c, edge_time(g, b, c), pack2(b, c)}};
    F oldest = f[0];
    for (int k = 1; k < 3; ++k) {
        if (f[k].t < oldest.t || (f[k].t == oldest.t && f[k].k < oldest.k)) oldest = f[k];
    }
    if (oldest.t == te && oldest.k == pack2(u, v)) {
        if (out_tau) *out_tau = youngest;
        return true;
    }
    return false;
}

// I111: a triangle may be Bauer-apparent with an MST facet. Ripser still
// uses that facet as a reduction partner (get_zero_apparent_facet).
inline bool apparent_facet_of_tri(const Graph& g, std::uint64_t tri_key, value_t t_tri,
                                  value_t T, index_t* ou, index_t* ov, value_t* ot) {
    const index_t a = static_cast<index_t>(tri_key & ((1ull << 21) - 1));
    const index_t b = static_cast<index_t>((tri_key >> 21) & ((1ull << 21) - 1));
    const index_t c = static_cast<index_t>(tri_key >> 42);
    struct F {
        index_t x, y;
        value_t t;
        std::uint64_t k;
    };
    const F f[3] = {{a, b, edge_time(g, a, b), pack2(a, b)},
                    {a, c, edge_time(g, a, c), pack2(a, c)},
                    {b, c, edge_time(g, b, c), pack2(b, c)}};
    F oldest = f[0];
    for (int k = 1; k < 3; ++k) {
        if (f[k].t < oldest.t || (f[k].t == oldest.t && f[k].k < oldest.k)) oldest = f[k];
    }
    if (oldest.t != t_tri) return false;
    CohEntry tau;
    if (!zero_apparent_edge(g, oldest.x, oldest.y, oldest.t, T, &tau)) return false;
    if (tau.key != tri_key) return false;
    *ou = oldest.x;
    *ov = oldest.y;
    *ot = oldest.t;
    return true;
}

inline Result persist_implicit_coh(const Graph& g, int maxdim, value_t threshold, value_t ratio) {
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
    struct LEdge {
        index_t u, v;
        value_t t;
    };
    std::vector<LEdge> leftover;
    leftover.reserve(edges.size());
    int components = g.n;
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        if (uf.unite(e.u, e.v)) {
            --components;
            r.pairs.push_back({0, 0, e.t});
            ++c.n_columns_cleared;
        } else {
            leftover.push_back({e.u, e.v, e.t});
        }
    }
    for (int i = 0; i < components; ++i) r.pairs.push_back({0, 0, kInf});

    if (maxdim < 1) {
        const auto t1 = std::chrono::steady_clock::now();
        c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        c.rss_bytes_peak = peak_rss_bytes();
        return r;
    }

    // Youngest leftover first (cohomology).
    std::sort(leftover.begin(), leftover.end(), [](const LEdge& a, const LEdge& b) {
        if (a.t != b.t) return a.t > b.t;
        return pack2(a.u, a.v) > pack2(b.u, b.v);
    });

    struct AEdge {
        index_t u, v;
        value_t t;
    };
    std::unordered_map<std::uint64_t, int> pivot;
    pivot.reserve(leftover.size() * 2);
    // Apparent pairs on EVERY edge, including MST facets (I111 / Ripser L769).
    std::unordered_map<std::uint64_t, AEdge> apparent;
    apparent.reserve(edges.size() * 2);
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        CohEntry tau;
        if (zero_apparent_edge(g, e.u, e.v, e.t, threshold, &tau)) {
            apparent.emplace(tau.key, AEdge{e.u, e.v, e.t});
        }
    }

    std::vector<std::vector<CohEntry>> reduced(leftover.size());

    auto xor_entry = [](std::unordered_map<std::uint64_t, value_t>& cob, CohEntry x) {
        auto it = cob.find(x.key);
        if (it == cob.end()) cob.emplace(x.key, x.t);
        else cob.erase(it);
    };
    auto dump_cob = [](const std::unordered_map<std::uint64_t, value_t>& cob) {
        std::vector<CohEntry> out;
        out.reserve(cob.size());
        for (const auto& kv : cob) out.push_back({kv.second, kv.first});
        return out;
    };
    auto youngest_in = [](const std::unordered_map<std::uint64_t, value_t>& cob) -> CohEntry {
        CohEntry best{kNegInf, 0};
        for (const auto& kv : cob) {
            if (kv.second > best.t || (kv.second == best.t && kv.first > best.key))
                best = {kv.second, kv.first};
        }
        return best;
    };
    auto xor_edge_cob = [&](std::unordered_map<std::uint64_t, value_t>& cob, index_t u, index_t v,
                            value_t te) {
        for_cofacets_edge(g, u, v, te, threshold, [&](CohEntry x) {
            ++c.n_cofacet_probes;
            xor_entry(cob, x);
        });
        ++c.n_additions;
    };

    for (int i = 0; i < static_cast<int>(leftover.size()); ++i) {
        CohEntry tau;
        if (zero_apparent_edge(g, leftover[i].u, leftover[i].v, leftover[i].t, threshold, &tau)) {
            ++c.n_columns_apparent;
            continue;
        }
        ++c.n_columns_assembled;
        std::unordered_map<std::uint64_t, value_t> cob;
        cob.reserve(64);
        for_cofacets_edge(g, leftover[i].u, leftover[i].v, leftover[i].t, threshold, [&](CohEntry x) {
            ++c.n_cofacet_probes;
            xor_entry(cob, x);
        });
        ++c.n_columns_reduced;
        int guard = 0;
        while (!cob.empty() && guard++ < 200000) {
            const CohEntry piv = youngest_in(cob);
            auto it = pivot.find(piv.key);
            if (it != pivot.end()) {
                for (const CohEntry& x : reduced[it->second]) xor_entry(cob, x);
                ++c.n_additions;
                continue;
            }
            auto ap = apparent.find(piv.key);
            if (ap != apparent.end()) {
                xor_edge_cob(cob, ap->second.u, ap->second.v, ap->second.t);
                continue;
            }
            index_t au = 0, av = 0;
            value_t at = 0;
            if (apparent_facet_of_tri(g, piv.key, piv.t, threshold, &au, &av, &at) &&
                pack2(au, av) != pack2(leftover[i].u, leftover[i].v)) {
                apparent.emplace(piv.key, AEdge{au, av, at});
                xor_edge_cob(cob, au, av, at);
                continue;
            }
            pivot[piv.key] = i;
            reduced[i] = dump_cob(cob);
            if (piv.t > leftover[i].t * ratio) r.pairs.push_back({1, leftover[i].t, piv.t});
            break;
        }
        if (cob.empty()) r.pairs.push_back({1, leftover[i].t, kInf});
    }

    // H2: fall back to homology on the residual (tiny after collapse).
    if (maxdim >= 2) {
        Result h = persist_sparse(g, maxdim, threshold, ratio);
        for (const auto& p : h.pairs) {
            if (p.dim >= 2) r.pairs.push_back(p);
        }
        c.n_simplices_enumerated += h.counters.n_simplices_enumerated;
        c.n_columns_assembled += h.counters.n_columns_assembled;
        c.n_columns_reduced += h.counters.n_columns_reduced;
        c.n_additions += h.counters.n_additions;
        c.n_cofacet_probes += h.counters.n_cofacet_probes;
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith

