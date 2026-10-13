#pragma once

#include "graph.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstring>
#include <cstdlib>
#include <thread>
#include <unordered_set>

namespace pith {

struct DenseTimes {
    int n = 0;
    std::vector<value_t> a;
    explicit DenseTimes(int n_) : n(n_), a(static_cast<size_t>(n_) * n_, kInf) {
        for (int i = 0; i < n; ++i) a[static_cast<size_t>(i) * n + i] = kNegInf;
    }
    value_t operator()(int i, int j) const { return a[static_cast<size_t>(i) * n + j]; }
    const value_t* row(int i) const { return a.data() + static_cast<size_t>(i) * n; }
    value_t* row(int i) { return a.data() + static_cast<size_t>(i) * n; }
    void set(int i, int j, value_t t) {
        a[static_cast<size_t>(i) * n + j] = t;
        a[static_cast<size_t>(j) * n + i] = t;
    }
    void erase(int i, int j) { set(i, j, kInf); }
};

// Live adjacency: (neighbor, current filtration time). Times stay in sync
// with Tm on shift (I155) so C-build gathers only the other endpoint's row.
using LiveNbr = std::pair<index_t, value_t>;
using LiveAdj = std::vector<std::vector<LiveNbr>>;

// True iff some c in C_now is adjacent (at time t) to every other vertex in C_now.
inline bool dominated_by(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                         index_t cand, value_t t) {
    const value_t* row = Tm.row(cand);
    for (index_t w : C_now) {
        if (row[w] > t) return false;
    }
    return true;
}

inline index_t first_dominator(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                               value_t t) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) return C_now[0];
    for (index_t cand : C_now) {
        if (dominated_by(Tm, C_now, cand, t)) return cand;
    }
    return -1;
}

// I082: skip apexes whose live degree cannot cover C_now.
// I106 max-degree-first was exact but slower (circle2000 T=1.5: 6.2× vs 7.2×).
// I107: budget>0 keeps the edge after that many failed exact checks (still
// filtration-safe: fewer trims, same PH as the thicker residual).
inline index_t first_dominator_deg(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                  value_t t, const LiveAdj& nbr,
                                  int budget = -1, Counters* ctr = nullptr) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) {
        if (ctr) ++ctr->n_collapse_dom_hits;
        return C_now[0];
    }
    const size_t need = C_now.size() - 1;
    int tried = 0;
    for (index_t cand : C_now) {
        if (nbr[cand].size() < need) continue;
        if (ctr) ++ctr->n_collapse_dom_tests;
        if (dominated_by(Tm, C_now, cand, t)) {
            if (ctr) ++ctr->n_collapse_dom_hits;
            return cand;
        }
        if (budget > 0 && ++tried >= budget) return -1;
    }
    return -1;
}

// I101: progressive intersection. Survivors of ∧_w N_t[w] ∩ C are exactly the
// dominators. Early abort when S empties (the expensive "not dominated" case).
inline index_t first_dominator_prog(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                   value_t t, const LiveAdj& nbr,
                                   std::vector<index_t>& S) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) return C_now[0];
    const size_t need = C_now.size() - 1;
    bool possible = false;
    for (index_t cand : C_now) {
        if (nbr[cand].size() >= need) {
            possible = true;
            break;
        }
    }
    if (!possible) return -1;
    S = C_now;
    for (index_t w : C_now) {
        size_t k = 0;
        for (index_t s : S) {
            if (Tm(s, w) <= t) S[k++] = s;
        }
        S.resize(k);
        if (S.empty()) return -1;
    }
    return S[0];
}

// I145: keep the cheap "first apex works" path (I102: progressive-only was
// 136 s vs 4.5 s). After a few failed exact checks, prove emptiness / find
// a later apex via progressive ∩ — that is the leftover-edge O(k²) tail.
inline index_t first_dominator_hybrid(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                      value_t t, const LiveAdj& nbr,
                                      std::vector<index_t>& S, int quick = 2) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) return C_now[0];
    const size_t need = C_now.size() - 1;
    int tried = 0;
    for (index_t cand : C_now) {
        if (nbr[cand].size() < need) continue;
        if (dominated_by(Tm, C_now, cand, t)) return cand;
        if (++tried >= quick) break;
    }
    if (tried == 0) return -1;
    return first_dominator_prog(Tm, C_now, t, nbr, S);
}

// Fraction of the `samples` youngest (largest-t) edges that are dominated
// in the static graph. Used as a cheap incompressibility probe (I047).
inline double probe_domination(const Graph& g, int samples = 64) {
    if (g.edges.empty()) return 0;
    std::vector<Edge> E = g.edges;
    const int m = std::min(samples, static_cast<int>(E.size()));
    std::partial_sort(E.begin(), E.begin() + m, E.end(),
                      [](const Edge& a, const Edge& b) { return a.t > b.t; });
    DenseTimes Tm(g.n);
    for (const Edge& e : g.edges) Tm.set(e.u, e.v, e.t);

    int hit = 0;
    std::vector<index_t> C;
    for (int i = 0; i < m; ++i) {
        const index_t u = E[i].u, v = E[i].v;
        const value_t t = E[i].t;
        C.clear();
        for (int w = 0; w < g.n; ++w) {
            if (w == u || w == v) continue;
            const value_t tu = Tm(u, w);
            const value_t tv = Tm(v, w);
            if (tu <= t && tv <= t) C.push_back(w);
        }
        if (first_dominator(Tm, C, t) >= 0) ++hit;
    }
    return static_cast<double>(hit) / static_cast<double>(m);
}

inline std::uint64_t edge_key(index_t u, index_t v) {
    if (u > v) std::swap(u, v);
    return (static_cast<std::uint64_t>(v) << 32) | static_cast<std::uint32_t>(u);
}

inline void drop_live_nbr(LiveAdj& nbr, index_t a, index_t b) {
    auto& row = nbr[a];
    for (size_t i = 0; i < row.size(); ++i) {
        if (row[i].first == b) {
            row[i] = row.back();
            row.pop_back();
            return;
        }
    }
}

inline void set_live_time(LiveAdj& nbr, index_t a, index_t b, value_t t) {
    for (auto& p : nbr[a]) {
        if (p.first == b) {
            p.second = t;
            return;
        }
    }
}

struct BwScratch {
    std::vector<index_t> C_now;
    std::vector<std::pair<value_t, index_t>> C_later;
};

// One backward edge (Glisse–Pritam). t_in is the start filtration (may be t_*
// on a D&C merge replay). Returns true if the edge is kept.
inline bool process_one_backward(const Edge& e_in, value_t t_in, DenseTimes& Tm,
                                 LiveAdj& nbr, BwScratch& S,
                                 int dom_budget, Edge& out, Counters& c) {
    const index_t u = e_in.u, v = e_in.v;
    value_t t = t_in;
    S.C_now.clear();
    S.C_later.clear();
    const bool walk_u = nbr[u].size() <= nbr[v].size();
    const auto& src = walk_u ? nbr[u] : nbr[v];
    const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
    c.n_collapse_c_probes += static_cast<std::int64_t>(src.size());

    // I156: fuse first-apex verify into the C walk. If the first common
    // dominates and there is no C_later, trim without materializing C
    // (I155: 1.07M trims vs 2k shifts on circle2000).
    index_t first = -1;
    const value_t* r_first = nullptr;
    bool fused_ok = true;
    bool any_later = false;
    bool later_a = false;
    bool later_b = false;
    std::int64_t commons = 0;
    std::int64_t fail_at = -1;
    for (const LiveNbr& p : src) {
        const index_t w = p.first;
        if (w == u || w == v) continue;
        if (p.second > t) ++c.n_collapse_tau_late;
        const value_t t_other = r_other[w];
        if (t_other >= kInf / 2) continue;
        ++commons;
        if (p.second > t) ++c.n_collapse_tau_late_common;
        const value_t tau = p.second > t_other ? p.second : t_other;
        if (tau <= t) {
            if (first < 0) {
                first = w;
                r_first = Tm.row(w);
            } else if (fused_ok && r_first[w] > t) {
                fused_ok = false;
                fail_at = commons;
            }
        } else {
            any_later = true;
            if (p.second > t) later_a = true;
            else later_b = true;
        }
    }
    c.n_collapse_last_fail_at = fail_at;
    c.n_collapse_last_any_later = any_later ? 1 : 0;
    c.n_collapse_last_later_a = later_a ? 1 : 0;
    c.n_collapse_last_later_b = later_b ? 1 : 0;
    c.n_collapse_c_size_sum += commons;

    if (first >= 0 && fused_ok && !any_later) {
        Tm.erase(u, v);
        drop_live_nbr(nbr, u, v);
        drop_live_nbr(nbr, v, u);
        ++c.n_collapse_trims;
        ++c.n_collapse_fast_trims;
        ++c.n_collapse_dom_hits;
        return false;
    }

    for (const LiveNbr& p : src) {
        const index_t w = p.first;
        if (w == u || w == v) continue;
        const value_t t_other = r_other[w];
        if (t_other >= kInf / 2) continue;
        const value_t tau = p.second > t_other ? p.second : t_other;
        if (tau <= t) S.C_now.push_back(w);
        else S.C_later.push_back({tau, w});
    }

    const auto later_cmp = [](const std::pair<value_t, index_t>& a,
                              const std::pair<value_t, index_t>& b) {
        return a.first > b.first;
    };
    bool heapified = false;
    bool ever_shifted = false;
    bool dead = false;
    while (true) {
        const index_t dominator = first_dominator_deg(Tm, S.C_now, t, nbr, dom_budget, &c);
        if (dominator < 0) break;
        const value_t* rd = Tm.row(dominator);
        bool still = true;
        while (still) {
            if (S.C_later.empty()) {
                dead = true;
                break;
            }
            if (!heapified) {
                std::make_heap(S.C_later.begin(), S.C_later.end(), later_cmp);
                heapified = true;
            }
            t = S.C_later.front().first;
            ever_shifted = true;
            while (!S.C_later.empty() && S.C_later.front().first <= t) {
                const index_t w = S.C_later.front().second;
                const value_t tw = S.C_later.front().first;
                ++c.n_collapse_shift_lookups;
                if (rd[w] > tw) still = false;
                S.C_now.push_back(w);
                std::pop_heap(S.C_later.begin(), S.C_later.end(), later_cmp);
                S.C_later.pop_back();
            }
        }
        if (dead) break;
    }

    if (dead) {
        Tm.erase(u, v);
        drop_live_nbr(nbr, u, v);
        drop_live_nbr(nbr, v, u);
        ++c.n_collapse_trims;
        return false;
    }
    out = e_in;
    out.t = ever_shifted ? t : t_in;
    c.n_collapse_last_commons = commons;
    c.n_collapse_last_mindeg = static_cast<std::int64_t>(
        std::min(nbr[u].size(), nbr[v].size()));
    if (ever_shifted) {
        Tm.set(u, v, out.t);
        set_live_time(nbr, u, v, out.t);
        set_live_time(nbr, v, u, out.t);
        ++c.n_collapse_shifts;
    }
    return true;
}

inline void init_collapse_graph(const std::vector<Edge>& E, int n, DenseTimes& Tm,
                                LiveAdj& nbr) {
    Tm = DenseTimes(n);
    nbr.assign(n, {});
    std::vector<int> deg(n, 0);
    for (const Edge& e : E) {
        ++deg[e.u];
        ++deg[e.v];
    }
    for (int i = 0; i < n; ++i) nbr[i].reserve(static_cast<size_t>(deg[i]));
    for (const Edge& e : E) {
        Tm.set(e.u, e.v, e.t);
        nbr[e.u].push_back({e.v, e.t});
        nbr[e.v].push_back({e.u, e.t});
    }
}

// Backward filtration-preserving edge collapse (Glisse–Pritam / GUDHI).
// I044: sticky dominator across C_later shifts + lazy heap (GUDHI L237–264).
inline Graph collapse_edges(Graph g, int iterations, Counters& c, int dom_budget = -1) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());

    BwScratch scratch;
    scratch.C_now.reserve(static_cast<size_t>(g.n));
    scratch.C_later.reserve(static_cast<size_t>(g.n));

    for (int pass = 0; pass < iterations; ++pass) {
        if (g.edges.empty()) break;

        std::vector<Edge>& E = g.edges;
        for (Edge& e : E) normalize_edge(e);
        std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
            if (a.t != b.t) return a.t > b.t;
            if (a.u != b.u) return a.u < b.u;
            return a.v < b.v;
        });

        DenseTimes Tm(g.n);
        LiveAdj nbr;
        init_collapse_graph(E, g.n, Tm, nbr);

        std::vector<Edge> kept;
        kept.reserve(E.size() / 4 + 8);
        const size_t mE = E.size();
        const size_t step = std::max<size_t>(mE / 8, 1);
        int early_n = 0;
        for (size_t i = 0; i < mE; ++i) {
            Edge out;
            if (process_one_backward(E[i], E[i].t, Tm, nbr, scratch, dom_budget, out, c)) {
                if (c.n_collapse_first_keep < 0)
                    c.n_collapse_first_keep = static_cast<std::int64_t>(i);
                if (mE > 0) {
                    const size_t b = std::min<size_t>(15, i * 16 / mE);
                    ++c.n_collapse_keep_hist[b];
                }
                if (early_n < 8) c.n_collapse_early_keeps[early_n++] = static_cast<std::int64_t>(i);
                if (mE > 0 && i * 16 < 15 * mE) {
                    ++c.n_collapse_early_keep_n;
                    if (c.n_collapse_last_commons == 0) ++c.n_collapse_early_empty_c;
                    if (c.n_collapse_last_fail_at > c.n_collapse_early_fail_max)
                        c.n_collapse_early_fail_max = c.n_collapse_last_fail_at;
                    if (c.n_collapse_last_any_later) ++c.n_collapse_early_any_later;
                    if (c.n_collapse_last_later_a) ++c.n_collapse_early_later_a;
                    if (c.n_collapse_last_later_b) ++c.n_collapse_early_later_b;
                    if (std::getenv("PITH_EARLY_KEEP")) {
                        std::fprintf(stderr, "# EARLY_KEEP i=%zu/%zu u=%d v=%d commons=%lld fail_at=%lld later=%lld laterA=%lld laterB=%lld mindeg=%lld t_in=%g t_out=%g\n",
                                     i, mE, (int)out.u, (int)out.v,
                                     static_cast<long long>(c.n_collapse_last_commons),
                                     static_cast<long long>(c.n_collapse_last_fail_at),
                                     static_cast<long long>(c.n_collapse_last_any_later),
                                     static_cast<long long>(c.n_collapse_last_later_a),
                                     static_cast<long long>(c.n_collapse_last_later_b),
                                     static_cast<long long>(c.n_collapse_last_mindeg),
                                     static_cast<double>(E[i].t),
                                     static_cast<double>(out.t));
                    }
                }
                kept.push_back(out);
            }
            if ((i == mE - 1 || (i % step) == 0) && std::getenv("PITH_COLLAPSE_TRACE")) {
                std::int64_t live = 0;
                for (const auto& row : nbr) live += static_cast<std::int64_t>(row.size());
                std::fprintf(stderr, "# COLLAPSE_TRACE i=%zu/%zu live=%lld kept=%zu trims=%lld\n",
                             i + 1, mE, static_cast<long long>(live / 2), kept.size(),
                             static_cast<long long>(c.n_collapse_trims));
            }
        }
        g.edges.swap(kept);
    }

    rebuild_neighbors(g);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I165: keep the oldest mult·n edges (I164 suffix observation). No domination.
// Exact iff the true residual pairs are among those oldest edges *and* their
// unshifted times already realize the VR≤T barcode (likely false if deaths
// need high-t shifts). Cheapest reject: identity vs Ripser.
inline Graph collapse_edges_oldest_prefix(Graph g, double mult, Counters& c,
                                         std::int64_t keep = -1) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
    for (Edge& e : g.edges) normalize_edge(e);
    std::sort(g.edges.begin(), g.edges.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t < b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    size_t k;
    if (keep > 0) {
        k = static_cast<size_t>(keep);
    } else {
        k = static_cast<size_t>(std::max(0.0, mult) * static_cast<double>(g.n));
        if (g.n > 0) k = std::max(k, static_cast<size_t>(g.n - 1));
    }
    if (k > g.edges.size()) k = g.edges.size();
    c.n_collapse_trims += static_cast<std::int64_t>(g.edges.size() - k);
    g.edges.resize(k);
    rebuild_neighbors(g);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I166: oldest prefix, then real backward collapse on that subgraph.
inline Graph collapse_edges_oldest_then_back(Graph g, double mult, Counters& c, int dom_budget,
                                            std::int64_t keep = -1) {
    g = collapse_edges_oldest_prefix(std::move(g), mult, c, keep);
    return collapse_edges(std::move(g), 1, c, dom_budget);
}

inline void add_collapse_counters(Counters& c, const Counters& t) {
    c.n_collapse_trims += t.n_collapse_trims;
    c.n_collapse_shifts += t.n_collapse_shifts;
    c.n_collapse_c_probes += t.n_collapse_c_probes;
    c.n_collapse_dom_tests += t.n_collapse_dom_tests;
    c.n_collapse_dom_hits += t.n_collapse_dom_hits;
    c.n_collapse_c_size_sum += t.n_collapse_c_size_sum;
    c.n_collapse_shift_lookups += t.n_collapse_shift_lookups;
    c.n_collapse_fast_trims += t.n_collapse_fast_trims;
    c.n_collapse_tau_late += t.n_collapse_tau_late;
    c.n_collapse_tau_late_common += t.n_collapse_tau_late_common;
    c.collapse_ms += t.collapse_ms;
}

inline bool same_residual(const Graph& a, const Graph& b) {
    if (a.n != b.n || a.edges.size() != b.edges.size()) return false;
    std::vector<Edge> ea = a.edges, eb = b.edges;
    for (Edge& e : ea) normalize_edge(e);
    for (Edge& e : eb) normalize_edge(e);
    const auto cmp = [](const Edge& x, const Edge& y) {
        if (x.u != y.u) return x.u < y.u;
        if (x.v != y.v) return x.v < y.v;
        return x.t < y.t;
    };
    std::sort(ea.begin(), ea.end(), cmp);
    std::sort(eb.begin(), eb.end(), cmp);
    for (size_t i = 0; i < ea.size(); ++i) {
        if (ea[i].u != eb[i].u || ea[i].v != eb[i].v) return false;
        if (std::fabs(ea[i].t - eb[i].t) > 1e-5f) return false;
    }
    return true;
}

inline Graph suffix_back_keep(const Graph& g, size_t keep, Counters& c, int dom_budget) {
    Graph attempt;
    attempt.n = g.n;
    attempt.edges = g.edges;
    Counters tmp;
    Graph out = collapse_edges_oldest_then_back(std::move(attempt), 0, tmp, dom_budget,
                                               static_cast<std::int64_t>(keep));
    add_collapse_counters(c, tmp);
    return out;
}

inline Graph suffix_full_bail(Graph g, Counters& c, int dom_budget, const std::chrono::steady_clock::time_point& t0) {
    Counters full;
    Graph out = collapse_edges(std::move(g), 1, full, dom_budget);
    add_collapse_counters(c, full);
    c.n_edges_out = static_cast<std::int64_t>(out.edges.size());
    c.n_collapse_first_keep = -1;
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return out;
}

// I168/I169: double oldest-keep until the residual plateaus, then confirm on a
// strictly larger keep. I168 false-plateaued on circle3000/4000: 64n and 12.5%
// agreed on the same *wrong* residual. Confirm at 2k (or k+m/8) catches that.
inline Graph collapse_edges_suffix_stabilize(Graph g, Counters& c, int dom_budget) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
    const size_t m = g.edges.size();
    const size_t n = static_cast<size_t>(std::max(g.n, 1));
    if (m <= n) return collapse_edges(std::move(g), 1, c, dom_budget);

    const size_t k_cap = std::min(m, std::max(n * 128, m / 2));
    size_t k = std::min(k_cap, std::max(n * 8, n));
    Graph prev;
    bool have_prev = false;
    Graph cur;
    size_t used = k;
    while (k <= k_cap) {
        cur = suffix_back_keep(g, k, c, dom_budget);
        used = k;
        if (have_prev && same_residual(prev, cur)) {
            const size_t k_v = std::min(m, std::max(k * 2, k + m / 8));
            if (k_v <= k) break;
            Graph ver = suffix_back_keep(g, k_v, c, dom_budget);
            if (same_residual(cur, ver)) {
                used = k_v;
                break;
            }
            // False plateau (I168 n=3000/4000). Keep growing from the verify keep.
            prev = std::move(ver);
            have_prev = true;
            if (k_v >= k_cap) return suffix_full_bail(std::move(g), c, dom_budget, t0);
            k = (k_v > k_cap / 2) ? k_cap : std::min(k_cap, k_v * 2);
            continue;
        }
        prev = cur;
        have_prev = true;
        if (k >= k_cap) return suffix_full_bail(std::move(g), c, dom_budget, t0);
        k = (k > k_cap / 2) ? k_cap : k * 2;
    }
    c.n_edges_out = static_cast<std::int64_t>(cur.edges.size());
    c.n_collapse_first_keep = static_cast<std::int64_t>(used);
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return cur;
}

// I171/I172: newest-first, cheap-trim any young edge with a live common
// neighbor; leave C-empty edges in the graph; full backward on the leftover
// (early keeps ∪ oldest suffix). Exact iff every young keep has C_now empty
// and every young nonempty-C edge eventually dies.
inline Graph collapse_edges_suffix_rescue(Graph g, Counters& c, int dom_budget) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
    std::vector<Edge>& E = g.edges;
    for (Edge& e : E) normalize_edge(e);
    std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t > b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    const size_t m = E.size();
    const size_t n = static_cast<size_t>(std::max(g.n, 1));
    const size_t k_suf = std::min(m, std::max(n * 64, m / 8));
    const size_t young = m > k_suf ? m - k_suf : 0;

    DenseTimes Tm(g.n);
    LiveAdj nbr;
    init_collapse_graph(E, g.n, Tm, nbr);

    for (size_t i = 0; i < young; ++i) {
        const index_t u = E[i].u, v = E[i].v;
        const value_t t = E[i].t;
        const bool walk_u = nbr[u].size() <= nbr[v].size();
        const auto& src = walk_u ? nbr[u] : nbr[v];
        const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
        bool has_common = false;
        std::int64_t probed = 0;
        for (const LiveNbr& p : src) {
            const index_t w = p.first;
            if (w == u || w == v) continue;
            ++probed;
            const value_t t_other = r_other[w];
            if (t_other >= kInf / 2) continue;
            const value_t tau = p.second > t_other ? p.second : t_other;
            if (tau <= t) {
                has_common = true;
                break;
            }
        }
        c.n_collapse_c_probes += probed;
        if (has_common) {
            Tm.erase(u, v);
            drop_live_nbr(nbr, u, v);
            drop_live_nbr(nbr, v, u);
            ++c.n_collapse_trims;
            ++c.n_collapse_fast_trims;
        }
    }

    std::vector<Edge> leftover;
    leftover.reserve(k_suf + 64);
    for (size_t i = 0; i < m; ++i) {
        if (Tm(E[i].u, E[i].v) < kInf / 2) leftover.push_back(E[i]);
    }
    g.edges.swap(leftover);
    Counters tail;
    g = collapse_edges(std::move(g), 1, tail, dom_budget);
    add_collapse_counters(c, tail);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I174: K-sample first-apex on the young prefix. Fail or any_later → leave
// for the tail. After `sample_k` successful commons, cheap-trim without
// finishing the star (K=0 = require a full fused walk, I156-safe on young).
// Exact iff no young sequential-keep passes the sample (see I174 reject).
inline Graph collapse_edges_suffix_sample(Graph g, Counters& c, int dom_budget,
                                          int sample_k) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
    std::vector<Edge>& E = g.edges;
    for (Edge& e : E) normalize_edge(e);
    std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t > b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    const size_t m = E.size();
    const size_t n = static_cast<size_t>(std::max(g.n, 1));
    const size_t k_suf = std::min(m, std::max(n * 64, m / 8));
    const size_t young = m > k_suf ? m - k_suf : 0;
    const int K = sample_k < 0 ? 0 : sample_k;

    DenseTimes Tm(g.n);
    LiveAdj nbr;
    init_collapse_graph(E, g.n, Tm, nbr);

    for (size_t i = 0; i < young; ++i) {
        const index_t u = E[i].u, v = E[i].v;
        const value_t t = E[i].t;
        const bool walk_u = nbr[u].size() <= nbr[v].size();
        const auto& src = walk_u ? nbr[u] : nbr[v];
        const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
        index_t first = -1;
        const value_t* r_first = nullptr;
        bool fused_ok = true;
        bool any_later = false;
        int commons = 0;
        std::int64_t probed = 0;
        bool decided_trim = false;
        bool decided_leave = false;
        for (const LiveNbr& p : src) {
            const index_t w = p.first;
            if (w == u || w == v) continue;
            ++probed;
            const value_t t_other = r_other[w];
            if (t_other >= kInf / 2) continue;
            const value_t tau = p.second > t_other ? p.second : t_other;
            if (tau <= t) {
                ++commons;
                if (first < 0) {
                    first = w;
                    r_first = Tm.row(w);
                } else if (fused_ok && r_first[w] > t) {
                    fused_ok = false;
                    decided_leave = true;
                    break;
                }
                if (K > 0 && fused_ok && commons >= K && !any_later) {
                    decided_trim = true;
                    break;
                }
            } else {
                any_later = true;
                decided_leave = true;
                break;
            }
        }
        c.n_collapse_c_probes += probed;
        if (!decided_leave && !decided_trim) {
            if (first >= 0 && fused_ok && !any_later) decided_trim = true;
            else decided_leave = true;
        }
        if (decided_trim) {
            Tm.erase(u, v);
            drop_live_nbr(nbr, u, v);
            drop_live_nbr(nbr, v, u);
            ++c.n_collapse_trims;
            ++c.n_collapse_fast_trims;
        }
    }

    std::vector<Edge> leftover;
    leftover.reserve(k_suf + 256);
    for (size_t i = 0; i < m; ++i) {
        if (Tm(E[i].u, E[i].v) < kInf / 2) leftover.push_back(E[i]);
    }
    g.edges.swap(leftover);
    Counters tail;
    g = collapse_edges(std::move(g), 1, tail, dom_budget);
    add_collapse_counters(c, tail);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I176/I179: leave young edges that have a later common before K-sample
// trim. Because the young loop is newest-first, every live neighbor with
// time > t has already been processed: trimmed (dropped) or kept. The
// kept-later adjacency is therefore the exact high-time prefix — Case A
// (later common on src) and Case B (later common on the other star) are
// O(|kept|) instead of a full other-star scan (I178). Then K-sample
// first-apex on the p.second ≤ t commons.
inline Graph collapse_edges_suffix_later(Graph g, Counters& c, int dom_budget,
                                         int sample_k, bool case_b = false) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
    std::vector<Edge>& E = g.edges;
    for (Edge& e : E) normalize_edge(e);
    std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t > b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    const size_t m = E.size();
    const size_t n = static_cast<size_t>(std::max(g.n, 1));
    const size_t k_suf = std::min(m, std::max(n * 64, m / 8));
    const size_t young = m > k_suf ? m - k_suf : 0;
    const int K = sample_k < 0 ? 0 : sample_k;

    DenseTimes Tm(g.n);
    LiveAdj nbr;
    init_collapse_graph(E, g.n, Tm, nbr);
    // I179: high-time prefix = already-kept newer edges, not a full sort.
    std::vector<std::vector<LiveNbr>> later(n);

    for (size_t i = 0; i < young; ++i) {
        const index_t u = E[i].u, v = E[i].v;
        const value_t t = E[i].t;
        const bool walk_u = nbr[u].size() <= nbr[v].size();
        const auto& src = walk_u ? nbr[u] : nbr[v];
        const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
        const index_t src_v = walk_u ? u : v;
        const index_t other_v = walk_u ? v : u;

        bool leave = false;
        std::int64_t probed = 0;
        // Case A: later kept neighbor of src, still adjacent to other.
        for (const LiveNbr& p : later[src_v]) {
            ++probed;
            if (p.second <= t) continue;
            if (r_other[p.first] < kInf / 2) {
                leave = true;
                break;
            }
        }
        if (!leave && case_b) {
            // Case B: later kept neighbor of the other endpoint, adjacent
            // to src at time ≤ t. later[other] is tiny (I171: ~100 keeps).
            const value_t* r_src = walk_u ? Tm.row(u) : Tm.row(v);
            for (const LiveNbr& p : later[other_v]) {
                ++probed;
                if (p.second <= t) continue;
                const value_t t_src = r_src[p.first];
                if (t_src < kInf / 2 && t_src <= t) {
                    leave = true;
                    break;
                }
            }
        }
        if (!leave) {
            index_t first = -1;
            const value_t* r_first = nullptr;
            bool fused_ok = true;
            int commons = 0;
            bool trim = false;
            for (const LiveNbr& p : src) {
                const index_t w = p.first;
                if (w == u || w == v) continue;
                if (p.second > t) continue;
                ++probed;
                const value_t t_other = r_other[w];
                if (t_other >= kInf / 2) continue;
                if (t_other > t) {
                    leave = true;
                    break;
                }
                ++commons;
                if (first < 0) {
                    first = w;
                    r_first = Tm.row(w);
                } else if (fused_ok && r_first[w] > t) {
                    leave = true;
                    break;
                }
                if (K > 0 && fused_ok && commons >= K) {
                    trim = true;
                    break;
                }
            }
            if (!leave && !trim) {
                if (first >= 0 && fused_ok) trim = true;
                else leave = true;
            }
            if (trim && !leave) {
                Tm.erase(u, v);
                drop_live_nbr(nbr, u, v);
                drop_live_nbr(nbr, v, u);
                ++c.n_collapse_trims;
                ++c.n_collapse_fast_trims;
            }
        }
        if (leave) {
            later[u].push_back({v, t});
            later[v].push_back({u, t});
        }
        c.n_collapse_c_probes += probed;
    }

    std::vector<Edge> leftover;
    leftover.reserve(k_suf + 256);
    for (size_t i = 0; i < m; ++i) {
        if (Tm(E[i].u, E[i].v) < kInf / 2) leftover.push_back(E[i]);
    }
    g.edges.swap(leftover);
    Counters tail;
    g = collapse_edges(std::move(g), 1, tail, dom_budget);
    add_collapse_counters(c, tail);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I150: Glisse 2022 Lemma 6 — 2-way time-axis D&C. Same output as sequential
// backward under a strict total order. Parallel schedule, not less work.
inline Graph collapse_edges_dc(Graph g, int iterations, Counters& c, int dom_budget = -1) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());

    auto dec_cmp = [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t > b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    };

    for (int pass = 0; pass < iterations; ++pass) {
        if (g.edges.size() < 8) {
            // Tiny leftover: sequential is cheaper than thread spawn.
            Counters tmp;
            g = collapse_edges(std::move(g), 1, tmp, dom_budget);
            c.n_collapse_trims += tmp.n_collapse_trims;
            c.n_collapse_shifts += tmp.n_collapse_shifts;
            continue;
        }

        std::vector<Edge> E = g.edges;
        for (Edge& e : E) normalize_edge(e);
        std::sort(E.begin(), E.end(), dec_cmp);
        const int m = static_cast<int>(E.size());
        const int nR = m - m / 2;  // high-t half processed first (backward)
        const int nL = m - nR;
        const value_t t_star = E[nR > 0 ? nR - 1 : 0].t;

        std::vector<Edge> E_L(E.begin() + nR, E.end());  // older half
        Graph gL;
        gL.n = g.n;
        gL.edges = E_L;

        Graph left_out;
        Counters cL;
        DenseTimes Tm_R(0);
        LiveAdj nbr_R;
        std::vector<Edge> kept_R;
        Counters cR;
        BwScratch scratch_R;
        scratch_R.C_now.reserve(static_cast<size_t>(g.n));
        scratch_R.C_later.reserve(static_cast<size_t>(g.n));

        std::thread th_left([&] { left_out = collapse_edges(std::move(gL), 1, cL, dom_budget); });
        {
            init_collapse_graph(E, g.n, Tm_R, nbr_R);
            kept_R.reserve(static_cast<size_t>(nR) / 4 + 8);
            for (int i = 0; i < nR; ++i) {
                Edge out;
                if (process_one_backward(E[i], E[i].t, Tm_R, nbr_R, scratch_R, dom_budget, out, cR))
                    kept_R.push_back(out);
            }
        }
        th_left.join();

        std::unordered_set<std::uint64_t> left_kept;
        left_kept.reserve(left_out.edges.size() * 2);
        for (const Edge& e : left_out.edges) left_kept.insert(edge_key(e.u, e.v));

        std::vector<Edge> Er_L;
        Er_L.reserve(E_L.size());
        for (const Edge& e : E_L) {
            if (!left_kept.count(edge_key(e.u, e.v))) Er_L.push_back(e);
        }
        std::sort(Er_L.begin(), Er_L.end(), dec_cmp);

        std::unordered_set<std::uint64_t> replayed;
        replayed.reserve(Er_L.size() * 2);
        std::vector<Edge> kept = std::move(kept_R);
        kept.reserve(kept.size() + static_cast<size_t>(nL));

        for (const Edge& e : Er_L) {
            Tm_R.set(e.u, e.v, t_star);
            // Ensure live adjacency: right pass never dropped E_L.
            Edge out;
            if (process_one_backward(e, t_star, Tm_R, nbr_R, scratch_R, dom_budget, out, cR))
                kept.push_back(out);
            replayed.insert(edge_key(e.u, e.v));
        }
        for (const Edge& e : E_L) {
            if (replayed.count(edge_key(e.u, e.v))) continue;
            Edge out;
            if (process_one_backward(e, e.t, Tm_R, nbr_R, scratch_R, dom_budget, out, cR))
                kept.push_back(out);
        }

        c.n_collapse_trims += cL.n_collapse_trims + cR.n_collapse_trims;
        c.n_collapse_shifts += cL.n_collapse_shifts + cR.n_collapse_shifts;
        g.edges.swap(kept);
    }

    rebuild_neighbors(g);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

// I149: Boissonnat–Pritam 2020 forward Algorithm 1. Exact PH; residual
// edge set may differ from backward under ties. O(n_e n_c k^2).
inline bool edge_dominated_in(const DenseTimes& Tm, const LiveAdj& nbr,
                              index_t u, index_t v, value_t t) {
    std::vector<index_t> C;
    const bool walk_u = nbr[u].size() <= nbr[v].size();
    const auto& src = walk_u ? nbr[u] : nbr[v];
    const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
    for (const LiveNbr& p : src) {
        const index_t w = p.first;
        if (w == u || w == v) continue;
        const value_t t_other = r_other[w];
        if (p.second <= t && t_other <= t) C.push_back(w);
    }
    return first_dominator_deg(Tm, C, t, nbr, -1) >= 0;
}

inline Graph collapse_edges_forward(Graph g, int iterations, Counters& c) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());

    for (int pass = 0; pass < iterations; ++pass) {
        if (g.edges.empty()) break;
        std::vector<Edge> E = g.edges;
        for (Edge& e : E) normalize_edge(e);
        std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
            if (a.t != b.t) return a.t < b.t;
            if (a.u != b.u) return a.u < b.u;
            return a.v < b.v;
        });
        const int m = static_cast<int>(E.size());
        const int n = g.n;
        std::vector<char> critical(m, 0);
        std::vector<int> crit_idx(m, -1);
        DenseTimes Tm(n);
        LiveAdj nbr(n);

        auto add_edge = [&](int i) {
            Tm.set(E[i].u, E[i].v, E[i].t);
            nbr[E[i].u].push_back({E[i].v, E[i].t});
            nbr[E[i].v].push_back({E[i].u, E[i].t});
        };
        auto rebuild_prefix = [&](int last_incl) {
            Tm = DenseTimes(n);
            nbr.assign(n, {});
            for (int i = 0; i <= last_incl; ++i) add_edge(i);
        };

        if (m > 0) {
            critical[0] = 1;
            crit_idx[0] = 0;
            add_edge(0);
        }
        for (int i = 1; i < m; ++i) {
            add_edge(i);
            if (!edge_dominated_in(Tm, nbr, E[i].u, E[i].v, E[i].t)) {
                critical[i] = 1;
                crit_idx[i] = i;
                ++c.n_collapse_shifts;  // primary critical
                std::unordered_set<std::uint64_t> Enbd;
                Enbd.reserve(64);
                const index_t u = E[i].u, v = E[i].v;
                const value_t ti = E[i].t;
                const value_t* ru = Tm.row(u);
                const value_t* rv = Tm.row(v);
                for (const LiveNbr& p : nbr[u]) {
                    const index_t w = p.first;
                    if (w != u && w != v && ru[w] <= ti && rv[w] <= ti) {
                        Enbd.insert(edge_key(u, w));
                        Enbd.insert(edge_key(v, w));
                    }
                }
                for (int j = i - 1; j >= 0; --j) {
                    if (critical[j]) continue;
                    const auto kj = edge_key(E[j].u, E[j].v);
                    if (!Enbd.count(kj)) {
                        Tm.erase(E[j].u, E[j].v);
                        drop_live_nbr(nbr, E[j].u, E[j].v);
                        drop_live_nbr(nbr, E[j].v, E[j].u);
                        ++c.n_collapse_trims;
                    } else if (edge_dominated_in(Tm, nbr, E[j].u, E[j].v, ti)) {
                        Tm.erase(E[j].u, E[j].v);
                        drop_live_nbr(nbr, E[j].u, E[j].v);
                        drop_live_nbr(nbr, E[j].v, E[j].u);
                        ++c.n_collapse_trims;
                    } else {
                        critical[j] = 1;
                        crit_idx[j] = i;
                        const index_t x = E[j].u, y = E[j].v;
                        const value_t* rx = Tm.row(x);
                        const value_t* ry = Tm.row(y);
                        for (const LiveNbr& p : nbr[x]) {
                            const index_t w = p.first;
                            if (w != x && w != y && rx[w] <= ti && ry[w] <= ti) {
                                Enbd.insert(edge_key(x, w));
                                Enbd.insert(edge_key(y, w));
                            }
                        }
                    }
                }
                rebuild_prefix(i);  // restore G_i after inner-loop drops
            }
        }

        std::vector<Edge> kept;
        kept.reserve(static_cast<size_t>(m) / 8 + 8);
        for (int i = 0; i < m; ++i) {
            if (!critical[i]) continue;
            Edge e = E[i];
            if (crit_idx[i] >= 0 && crit_idx[i] != i) e.t = E[crit_idx[i]].t;
            kept.push_back(e);
        }
        g.edges.swap(kept);
    }

    rebuild_neighbors(g);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms += std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

}  // namespace pith
