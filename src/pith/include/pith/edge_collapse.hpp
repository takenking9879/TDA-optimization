#pragma once

#include "graph.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstring>

namespace pith {

struct DenseTimes {
    int n = 0;
    std::vector<value_t> a;
    explicit DenseTimes(int n_) : n(n_), a(static_cast<size_t>(n_) * n_, kInf) {
        for (int i = 0; i < n; ++i) a[static_cast<size_t>(i) * n + i] = kNegInf;
    }
    value_t operator()(int i, int j) const { return a[static_cast<size_t>(i) * n + j]; }
    void set(int i, int j, value_t t) {
        a[static_cast<size_t>(i) * n + j] = t;
        a[static_cast<size_t>(j) * n + i] = t;
    }
    void erase(int i, int j) { set(i, j, kInf); }
};

// True iff some c in C_now is adjacent (at time t) to every other vertex in C_now.
inline bool dominated_by(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                         index_t cand, value_t t) {
    for (index_t w : C_now) {
        if (Tm(cand, w) > t) return false;
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
                                  value_t t, const std::vector<std::vector<index_t>>& nbr,
                                  int budget = -1) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) return C_now[0];
    const size_t need = C_now.size() - 1;
    int tried = 0;
    for (index_t cand : C_now) {
        if (nbr[cand].size() < need) continue;
        if (dominated_by(Tm, C_now, cand, t)) return cand;
        if (budget > 0 && ++tried >= budget) return -1;
    }
    return -1;
}

// I101: progressive intersection. Survivors of ∧_w N_t[w] ∩ C are exactly the
// dominators. Early abort when S empties (the expensive "not dominated" case).
inline index_t first_dominator_prog(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                   value_t t, const std::vector<std::vector<index_t>>& nbr,
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

// Backward filtration-preserving edge collapse (Glisse–Pritam / GUDHI).
// I044: sticky dominator across C_later shifts + lazy heap (GUDHI L237–264).
inline Graph collapse_edges(Graph g, int iterations, Counters& c, int dom_budget = -1) {
    const auto t0 = std::chrono::steady_clock::now();
    if (c.n_edges_in == 0) c.n_edges_in = static_cast<std::int64_t>(g.edges.size());

    std::vector<index_t> C_now;
    std::vector<std::pair<value_t, index_t>> C_later;
    C_now.reserve(static_cast<size_t>(g.n));
    C_later.reserve(static_cast<size_t>(g.n));
    const auto later_cmp = [](const std::pair<value_t, index_t>& a,
                              const std::pair<value_t, index_t>& b) {
        return a.first > b.first;  // min-time at front after make_heap
    };

    for (int pass = 0; pass < iterations; ++pass) {
        if (g.edges.empty()) break;

        std::vector<Edge>& E = g.edges;
        for (Edge& e : E) normalize_edge(e);
        std::sort(E.begin(), E.end(), [](const Edge& a, const Edge& b) {
            if (a.t != b.t) return a.t > b.t;
            if (a.u != b.u) return a.u < b.u;
            return a.v < b.v;
        });

        const int n = g.n;
        DenseTimes Tm(n);
        std::vector<std::vector<index_t>> nbr(n);
        for (const Edge& e : E) {
            Tm.set(e.u, e.v, e.t);
            nbr[e.u].push_back(e.v);
            nbr[e.v].push_back(e.u);
        }

        auto drop_nbr = [&](index_t a, index_t b) {
            auto& row = nbr[a];
            for (size_t i = 0; i < row.size(); ++i) {
                if (row[i] == b) {
                    row[i] = row.back();
                    row.pop_back();
                    return;
                }
            }
        };

        std::vector<Edge> kept;
        kept.reserve(E.size() / 4 + 8);

        for (const Edge& e_in : E) {
            const index_t u = e_in.u;
            const index_t v = e_in.v;
            value_t t = e_in.t;
            const value_t t_in = e_in.t;

            C_now.clear();
            C_later.clear();
            const auto& src = nbr[u].size() <= nbr[v].size() ? nbr[u] : nbr[v];
            for (index_t w : src) {
                if (w == u || w == v) continue;
                const value_t tu = Tm(u, w);
                const value_t tv = Tm(v, w);
                if (tu >= kInf / 2 || tv >= kInf / 2) continue;
                const value_t tau = std::max(tu, tv);
                if (tau <= t) C_now.push_back(w);
                else C_later.push_back({tau, w});
            }

            bool heapified = false;
            bool ever_shifted = false;
            bool dead = false;
            while (true) {
                const index_t dominator = first_dominator_deg(Tm, C_now, t, nbr, dom_budget);
                if (dominator < 0) break;
                // Sticky: keep shifting while this apex still dominates newcomers.
                bool still = true;
                while (still) {
                    if (C_later.empty()) {
                        dead = true;
                        break;
                    }
                    if (!heapified) {
                        std::make_heap(C_later.begin(), C_later.end(), later_cmp);
                        heapified = true;
                    }
                    t = C_later.front().first;
                    ever_shifted = true;
                    while (!C_later.empty() && C_later.front().first <= t) {
                        const index_t w = C_later.front().second;
                        const value_t tw = C_later.front().first;
                        if (Tm(dominator, w) > tw) still = false;
                        C_now.push_back(w);
                        std::pop_heap(C_later.begin(), C_later.end(), later_cmp);
                        C_later.pop_back();
                    }
                }
                if (dead) break;
                // Newcomers broke the apex; outer loop finds another or keeps.
            }

            if (dead) {
                Tm.erase(u, v);
                drop_nbr(u, v);
                drop_nbr(v, u);
                ++c.n_collapse_trims;
            } else {
                Edge out = e_in;
                out.t = ever_shifted ? t : t_in;
                kept.push_back(out);
                if (ever_shifted) {
                    Tm.set(u, v, out.t);
                    ++c.n_collapse_shifts;
                }
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

}  // namespace pith
