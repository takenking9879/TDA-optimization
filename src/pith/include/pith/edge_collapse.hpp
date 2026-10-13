#pragma once

#include "graph.hpp"

#include <chrono>
#include <cstring>

namespace pith {

// Dense symmetric filtration matrix: missing = +inf, diagonal = -inf.
struct DenseTimes {
    int n = 0;
    std::vector<value_t> a;  // n*n row-major
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

// Backward filtration-preserving edge collapse (Glisse–Pritam / GUDHI).
// Exact for the flag filtration of the input 1-skeleton.
inline Graph collapse_edges(Graph g, int iterations, Counters& c) {
    const auto t0 = std::chrono::steady_clock::now();
    c.n_edges_in = static_cast<std::int64_t>(g.edges.size());

    for (int pass = 0; pass < iterations; ++pass) {
        if (g.edges.empty()) break;

        std::vector<Edge> E = g.edges;
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
        // neighbor lists need not stay sorted; we filter by Tm

        auto is_dominated_by = [&](const std::vector<index_t>& C, index_t cand, value_t t) {
            for (index_t w : C) {
                if (Tm(cand, w) > t) return false;
            }
            return true;
        };
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

            std::vector<index_t> C_now;
            std::vector<std::pair<value_t, index_t>> C_later;
            const auto& src = nbr[u].size() <= nbr[v].size() ? nbr[u] : nbr[v];
            C_now.reserve(src.size());
            for (index_t w : src) {
                if (w == u || w == v) continue;
                const value_t tu = Tm(u, w);
                const value_t tv = Tm(v, w);
                if (tu >= kInf / 2 || tv >= kInf / 2) continue;
                const value_t tau = std::max(tu, tv);
                if (tau <= t) C_now.push_back(w);
                else C_later.push_back({tau, w});
            }
            std::sort(C_later.begin(), C_later.end());

            size_t later_i = 0;
            bool ever_shifted = false;
            while (true) {
                bool dominated = false;
                if (C_now.size() == 1) {
                    dominated = true;  // singleton common neighborhood is always a cone
                } else {
                    for (index_t cand : C_now) {
                        if (is_dominated_by(C_now, cand, t)) {
                            dominated = true;
                            break;
                        }
                    }
                }
                if (!dominated) {
                    Edge out = e_in;
                    out.t = ever_shifted ? t : e_in.t;
                    kept.push_back(out);
                    if (ever_shifted) {
                        Tm.set(u, v, out.t);
                        ++c.n_collapse_shifts;
                    }
                    break;
                }
                if (later_i >= C_later.size()) {
                    Tm.erase(u, v);
                    drop_nbr(u, v);
                    drop_nbr(v, u);
                    ++c.n_collapse_trims;
                    break;
                }
                t = C_later[later_i].first;
                ever_shifted = true;
                while (later_i < C_later.size() && C_later[later_i].first <= t) {
                    C_now.push_back(C_later[later_i].second);
                    ++later_i;
                }
            }
        }

        g.edges.swap(kept);
    }

    rebuild_neighbors(g);
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    const auto t1 = std::chrono::steady_clock::now();
    c.collapse_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return g;
}

}  // namespace pith
