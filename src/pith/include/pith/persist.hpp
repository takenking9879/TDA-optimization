#pragma once

#include "graph.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <functional>
#include <numeric>
#include <queue>
#include <type_traits>
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

// Implicit persistent *cohomology* on a flag graph — Ripser compute_pairs
// ported onto Graph (I137). Previous leftover-as-cohomology (I045–I126) used
// the *youngest* cofacet as pivot and required the *shortest* facet to carry
// the triangle diameter (equilateral-only apparent pairs). Ripser's pivot is
// the oldest remaining cofacet after F₂ heap cancellation; a zero-apparent
// pair is a same-diameter cofacet whose first same-diameter facet (drop
// largest vertex first) is the edge. V-matrix stores added edges and
// re-enumerates coboundaries — never materializes the 2-skeleton.
struct CohEntry {
    value_t t = kNegInf;
    std::uint64_t key = 0;
};

// Ripser greater_diameter_or_smaller_index as priority_queue Compare:
// larger diameter (or same diameter + smaller key) has lower priority.
// Top = oldest remaining cofacet, tie → larger pack key.
struct CohRipserLess {
    bool operator()(CohEntry a, CohEntry b) const {
        if (a.t != b.t) return a.t > b.t;
        return a.key < b.key;
    }
};

using CohHeap = std::priority_queue<CohEntry, std::vector<CohEntry>, CohRipserLess>;

inline CohEntry pop_pivot_ripser(CohHeap& h) {
    while (!h.empty()) {
        const CohEntry p = h.top();
        h.pop();
        if (h.empty() || h.top().t != p.t || h.top().key != p.key) return p;
        h.pop();
    }
    return {kNegInf, 0};
}

inline CohEntry peek_pivot_ripser(CohHeap& h) {
    const CohEntry p = pop_pivot_ripser(h);
    if (p.t != kNegInf) h.push(p);
    return p;
}

inline void unpack3(std::uint64_t key, index_t& a, index_t& b, index_t& c) {
    a = static_cast<index_t>(key & ((1ull << 21) - 1));
    b = static_cast<index_t>((key >> 21) & ((1ull << 21) - 1));
    c = static_cast<index_t>(key >> 42);
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

// High-vertex-first cofacet walk (Ripser sparse enumerator uses rbegin).
// I203: callback may return bool; false aborts the remaining merge. Void
// callbacks still walk the full intersection (used only by legacy callers).
template <class Fn>
inline bool for_cofacets_edge_hi(const Graph& g, index_t u, index_t v, value_t te, value_t T,
                                 Fn&& fn) {
    const auto& nu = g.neighbors[u];
    const auto& nv = g.neighbors[v];
    int i = static_cast<int>(nu.size()) - 1;
    int j = static_cast<int>(nv.size()) - 1;
    while (i >= 0 && j >= 0) {
        if (nu[static_cast<size_t>(i)].first > nv[static_cast<size_t>(j)].first) {
            --i;
            continue;
        }
        if (nv[static_cast<size_t>(j)].first > nu[static_cast<size_t>(i)].first) {
            --j;
            continue;
        }
        const index_t w = nu[static_cast<size_t>(i)].first;
        if (w != u && w != v) {
            const value_t td =
                std::max({te, nu[static_cast<size_t>(i)].second, nv[static_cast<size_t>(j)].second});
            if (td <= T) {
                CohEntry e{td, pack3(u, v, w)};
                using R = decltype(fn(e));
                if constexpr (std::is_same_v<R, bool>) {
                    if (!fn(e)) return false;
                } else {
                    fn(e);
                }
            }
        }
        --i;
        --j;
    }
    return true;
}

// First same-diameter facet, Ripser boundary order: drop largest vertex first.
inline bool zero_pivot_facet(const Graph& g, std::uint64_t tri_key, value_t t_tri, index_t* ou,
                             index_t* ov, value_t* ot) {
    index_t a, b, c;
    unpack3(tri_key, a, b, c);
    const index_t us[3] = {a, a, b};
    const index_t vs[3] = {b, c, c};
    for (int k = 0; k < 3; ++k) {
        const value_t t = edge_time(g, us[k], vs[k]);
        if (t == t_tri) {
            *ou = us[k];
            *ov = vs[k];
            *ot = t;
            return true;
        }
    }
    return false;
}

inline bool zero_pivot_cofacet(const Graph& g, index_t u, index_t v, value_t te, value_t T,
                               CohEntry* out, Counters* ctr = nullptr) {
    bool found = false;
    // I203: first same-diameter cofacet in hi-order is the Ripser zero-pivot.
    // Stop the merge; the tail cannot change the result.
    for_cofacets_edge_hi(g, u, v, te, T, [&](CohEntry tau) -> bool {
        if (ctr) ++ctr->n_cofacet_apparent_probes;
        if (tau.t == te) {
            *out = tau;
            found = true;
            return false;
        }
        return true;
    });
    return found;
}

inline bool zero_apparent_cofacet(const Graph& g, index_t u, index_t v, value_t te, value_t T,
                                  CohEntry* out, Counters* ctr = nullptr) {
    CohEntry tau;
    if (!zero_pivot_cofacet(g, u, v, te, T, &tau, ctr)) return false;
    index_t fu, fv;
    value_t ft;
    if (!zero_pivot_facet(g, tau.key, tau.t, &fu, &fv, &ft)) return false;
    if (pack2(fu, fv) != pack2(u, v)) return false;
    if (out) *out = tau;
    return true;
}

inline bool zero_apparent_facet(const Graph& g, std::uint64_t tri_key, value_t t_tri, value_t T,
                                index_t* ou, index_t* ov, value_t* ot, Counters* ctr = nullptr) {
    index_t u, v;
    value_t t;
    if (!zero_pivot_facet(g, tri_key, t_tri, &u, &v, &t)) return false;
    CohEntry tau;
    if (!zero_pivot_cofacet(g, u, v, t, T, &tau, ctr)) return false;
    if (tau.key != tri_key) return false;
    *ou = u;
    *ov = v;
    *ot = t;
    return true;
}

// I163: leftover-apparent rate + MST scale. Used to decide whether collapse
// can beat Ripser (circle T≈1.5: low apparent / long leftover tail).
struct RoiProbe {
    double leftover_apparent = 0;
    std::int64_t n_leftover = 0;
    std::int64_t n_sampled = 0;
    double mean_deg = 0;
    value_t mst_max = 0;
    value_t leftover_median = 0;
};

inline RoiProbe probe_roi(const Graph& g, value_t T, int samples = 160) {
    RoiProbe p;
    p.mean_deg = g.n ? 2.0 * static_cast<double>(g.edges.size()) / g.n : 0;
    std::vector<Edge> edges = g.edges;
    std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t < b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    UnionFind uf(g.n);
    std::vector<Edge> leftover;
    leftover.reserve(edges.size());
    for (const Edge& e : edges) {
        if (e.t > T) continue;
        if (uf.unite(e.u, e.v)) p.mst_max = std::max(p.mst_max, e.t);
        else leftover.push_back(e);
    }
    p.n_leftover = static_cast<std::int64_t>(leftover.size());
    if (leftover.empty()) return p;
    const int m = std::min(samples, static_cast<int>(leftover.size()));
    int hit = 0;
    for (int i = 0; i < m; ++i) {
        const size_t idx = static_cast<size_t>((i + 0.5) * leftover.size() / m);
        const Edge& e = leftover[std::min(idx, leftover.size() - 1)];
        if (zero_apparent_cofacet(g, e.u, e.v, e.t, T, nullptr)) ++hit;
    }
    p.n_sampled = m;
    p.leftover_apparent = static_cast<double>(hit) / static_cast<double>(m);
    p.leftover_median = leftover[leftover.size() / 2].t;
    return p;
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
    std::vector<LEdge> cols;
    cols.reserve(edges.size());
    int components = g.n;
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        if (uf.unite(e.u, e.v)) {
            --components;
            r.pairs.push_back({0, 0, e.t});
            ++c.n_columns_cleared;
        } else if (zero_apparent_cofacet(g, e.u, e.v, e.t, threshold, nullptr, &c)) {
            ++c.n_columns_apparent;
        } else {
            cols.push_back({e.u, e.v, e.t});
        }
    }
    for (int i = 0; i < components; ++i) r.pairs.push_back({0, 0, kInf});

    if (maxdim < 1) {
        const auto t1 = std::chrono::steady_clock::now();
        c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        c.rss_bytes_peak = peak_rss_bytes();
        return r;
    }

    // Youngest first: greater diameter, then smaller pack2 (Ripser reverse).
    std::sort(cols.begin(), cols.end(), [](const LEdge& a, const LEdge& b) {
        if (a.t != b.t) return a.t > b.t;
        return pack2(a.u, a.v) < pack2(b.u, b.v);
    });

    std::unordered_map<std::uint64_t, int> pivot;
    pivot.reserve(cols.size() * 2);
    std::vector<std::vector<LEdge>> red(cols.size());

    auto add_simplex_coboundary = [&](const LEdge& e, std::vector<LEdge>& vred, CohHeap& cob) {
        vred.push_back(e);
        for_cofacets_edge(g, e.u, e.v, e.t, threshold, [&](CohEntry x) {
            ++c.n_cofacet_probes;
            cob.push(x);
        });
    };

    auto compress_vedges = [](std::vector<LEdge>& v) {
        if (v.size() < 2) return;
        std::sort(v.begin(), v.end(), [](const LEdge& a, const LEdge& b) {
            const auto ka = pack2(a.u, a.v), kb = pack2(b.u, b.v);
            return ka < kb;
        });
        std::vector<LEdge> out;
        out.reserve(v.size());
        for (const LEdge& e : v) {
            if (!out.empty() && pack2(out.back().u, out.back().v) == pack2(e.u, e.v))
                out.pop_back();
            else
                out.push_back(e);
        }
        v.swap(out);
    };

    for (int i = 0; i < static_cast<int>(cols.size()); ++i) {
        ++c.n_columns_assembled;
        CohHeap working_cob;
        std::vector<LEdge> working_red;
        std::vector<CohEntry> collected;
        collected.reserve(16);

        bool check_emergent = true;
        bool have_emergent = false;
        CohEntry emergent{kNegInf, 0};
        // I203: if the first same-diameter cofacet is an unpaired non-apparent
        // (Ripser emergent pair), it is the pivot. Do not walk the rest of
        // the intersection and do not fill `collected`.
        for_cofacets_edge_hi(g, cols[i].u, cols[i].v, cols[i].t, threshold, [&](CohEntry tau) -> bool {
            ++c.n_cofacet_probes;
            if (have_emergent) return false;
            collected.push_back(tau);
            if (check_emergent && tau.t == cols[i].t) {
                if (pivot.find(tau.key) == pivot.end()) {
                    index_t au, av;
                    value_t at;
                    if (!zero_apparent_facet(g, tau.key, tau.t, threshold, &au, &av, &at, &c)) {
                        have_emergent = true;
                        emergent = tau;
                        collected.clear();
                        return false;
                    }
                }
                check_emergent = false;
            }
            return true;
        });

        CohEntry piv;
        if (have_emergent) {
            piv = emergent;
        } else {
            for (const CohEntry& x : collected) working_cob.push(x);
            piv = peek_pivot_ripser(working_cob);
        }
        ++c.n_columns_reduced;

        while (true) {
            if (piv.t == kNegInf) {
                r.pairs.push_back({1, cols[i].t, kInf});
                break;
            }
            auto it = pivot.find(piv.key);
            if (it != pivot.end()) {
                const int j = it->second;
                add_simplex_coboundary(cols[j], working_red, working_cob);
                for (const LEdge& e : red[j]) add_simplex_coboundary(e, working_red, working_cob);
                ++c.n_additions;
                piv = peek_pivot_ripser(working_cob);
                continue;
            }
            index_t au = 0, av = 0;
            value_t at = 0;
            if (zero_apparent_facet(g, piv.key, piv.t, threshold, &au, &av, &at, &c)) {
                add_simplex_coboundary({au, av, at}, working_red, working_cob);
                ++c.n_additions;
                piv = peek_pivot_ripser(working_cob);
                continue;
            }
            if (piv.t > cols[i].t * ratio) r.pairs.push_back({1, cols[i].t, piv.t});
            pivot[piv.key] = i;
            compress_vedges(working_red);
            red[i] = std::move(working_red);
            break;
        }
    }

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

