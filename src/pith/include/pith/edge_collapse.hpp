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

// I182: live existence bits, lockstep with Tm. Generate C by row AND
// instead of walking src and gathering misses (~49% of probes).
struct LiveBits {
    int n = 0;
    int W = 0;
    std::vector<std::uint64_t> a;
    LiveBits() = default;
    explicit LiveBits(int n_)
        : n(n_), W((n_ + 63) >> 6), a(static_cast<size_t>(std::max(n_, 0)) * std::max(W, 1), 0) {}
    std::uint64_t* row(int i) { return a.data() + static_cast<size_t>(i) * W; }
    const std::uint64_t* row(int i) const { return a.data() + static_cast<size_t>(i) * W; }
    void set_edge(int i, int j) {
        row(i)[static_cast<unsigned>(j) >> 6] |= 1ull << (j & 63);
        row(j)[static_cast<unsigned>(i) >> 6] |= 1ull << (i & 63);
    }
    void clear_edge(int i, int j) {
        row(i)[static_cast<unsigned>(j) >> 6] &= ~(1ull << (j & 63));
        row(j)[static_cast<unsigned>(i) >> 6] &= ~(1ull << (i & 63));
    }
};

// Live adjacency: (neighbor, current filtration time). Times stay in sync
// with Tm on shift (I155) so C-build gathers only the other endpoint's row.
using LiveNbr = std::pair<index_t, value_t>;
using LiveAdj = std::vector<std::vector<LiveNbr>>;

// True iff cand is adjacent (at time t) to every vertex in C_now.
// Optional: resume from `from` (I214 prefix already verified at a smaller t);
// on failure write the first obstruction grade and its C_now index.
// I219: `hint` is the last failing vertex (still in C — C only grows). If
// Tm(cand, hint) > t the cover already fails; skip the rest of C.
inline bool dominated_by(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                         index_t cand, value_t t, value_t* fail_t = nullptr,
                         int* fail_i = nullptr, int from = 0,
                         index_t hint = -1, index_t* fail_w = nullptr) {
    const value_t* row = Tm.row(cand);
    if (hint >= 0 && row[hint] > t) {
        if (fail_t) *fail_t = row[hint];
        if (fail_w) *fail_w = hint;
        return false;
    }
    const int nC = static_cast<int>(C_now.size());
    for (int i = from; i < nC; ++i) {
        const index_t w = C_now[static_cast<size_t>(i)];
        if (w == hint) continue;
        if (row[w] > t) {
            if (fail_t) *fail_t = row[w];
            if (fail_i) *fail_i = i;
            if (fail_w) *fail_w = w;
            return false;
        }
    }
    return true;
}

// I214: generation-stamped obstruction for the shift loop.
// C_now only grows by push_back. If cand failed at C_now[i] with
// Tm(cand, C[i]) = tau, it cannot dominate any later C' ⊇ C while t < tau
// (larger C is a harder cover; raising t past tau is the only way the
// known obstruction lifts). Boolean cannot_dom across t increases would
// be inexact. Stamp resets per process_one_backward.
struct CannotDom {
    std::vector<int> gen;
    std::vector<value_t> until;
    std::vector<int> idx;
    int stamp = 0;
    void ensure(int n) {
        if (static_cast<int>(gen.size()) == n) return;
        gen.assign(static_cast<size_t>(std::max(n, 0)), 0);
        until.assign(static_cast<size_t>(std::max(n, 0)), kNegInf);
        idx.assign(static_cast<size_t>(std::max(n, 0)), 0);
    }
    void next() {
        ++stamp;
        if (stamp == 0) {
            std::fill(gen.begin(), gen.end(), 0);
            ++stamp;
        }
    }
    bool blocked(index_t v, value_t t) const {
        const size_t k = static_cast<size_t>(v);
        return k < gen.size() && gen[k] == stamp && t < until[k];
    }
    int resume_at(index_t v) const {
        const size_t k = static_cast<size_t>(v);
        if (k < gen.size() && gen[k] == stamp) return idx[k];
        return 0;
    }
    void mark(index_t v, value_t t_need, int i) {
        const size_t k = static_cast<size_t>(v);
        if (k >= gen.size()) return;
        gen[k] = stamp;
        until[k] = t_need;
        idx[k] = i;
    }
};

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
                                  int budget = -1, Counters* ctr = nullptr,
                                  const std::vector<int>* deg = nullptr) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) {
        if (ctr) ++ctr->n_collapse_dom_hits;
        return C_now[0];
    }
    const size_t need = C_now.size() - 1;
    int tried = 0;
    for (index_t cand : C_now) {
        const size_t cand_deg = deg ? static_cast<size_t>((*deg)[cand]) : nbr[cand].size();
        if (cand_deg < need) continue;
        if (ctr) ++ctr->n_collapse_dom_tests;
        if (dominated_by(Tm, C_now, cand, t)) {
            if (ctr) ++ctr->n_collapse_dom_hits;
            return cand;
        }
        if (budget > 0 && ++tried >= budget) return -1;
    }
    return -1;
}

// I201: after sticky fails on witness w, a new dominator must lie in
// C_now ∩ N_t[w] (including w). Skip the rest of C_now.
inline index_t first_dominator_witness(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                      value_t t, const LiveAdj& nbr, int budget, Counters* ctr,
                                      const std::vector<int>* deg, index_t witness) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) {
        if (ctr) ++ctr->n_collapse_dom_hits;
        return C_now[0];
    }
    const size_t need = C_now.size() - 1;
    const value_t* rw = Tm.row(witness);
    int tried = 0;
    for (index_t cand : C_now) {
        if (cand != witness && rw[cand] > t) continue;
        const size_t cand_deg = deg ? static_cast<size_t>((*deg)[cand]) : nbr[cand].size();
        if (cand_deg < need) continue;
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

// I192: count vertices v with some u such that N[v] ⊆ N[u] in G_T
// (closed neighborhoods; Boissonnat–Pritam 2018/2019 strong collapse).
// Cheap falsify: if frac << 0.3, batch star-trim will not cut blobs.
struct VertexDomProbe {
    int n = 0;
    int n_dom = 0;
    std::int64_t star_edges = 0;
    double frac = 0;
};

inline VertexDomProbe probe_vertex_domination(const Graph& g) {
    VertexDomProbe p;
    p.n = g.n;
    if (g.n <= 0) return p;
    LiveBits bits(g.n);
    std::vector<int> deg(static_cast<size_t>(g.n), 0);
    for (const Edge& e : g.edges) {
        bits.set_edge(e.u, e.v);
        ++deg[e.u];
        ++deg[e.v];
    }
    const int W = bits.W;
    std::vector<std::uint64_t> Nv(static_cast<size_t>(W), 0);
    std::vector<char> dominated(static_cast<size_t>(g.n), 0);
    for (int v = 0; v < g.n; ++v) {
        std::memcpy(Nv.data(), bits.row(v), static_cast<size_t>(W) * sizeof(std::uint64_t));
        Nv[static_cast<unsigned>(v) >> 6] |= 1ull << (v & 63);
        bool hit = false;
        const std::uint64_t* rv = bits.row(v);
        for (int w0 = 0; w0 < W && !hit; ++w0) {
            std::uint64_t word = rv[w0];
            while (word) {
                const int tz = __builtin_ctzll(word);
                word &= word - 1;
                const int u = w0 * 64 + tz;
                if (u == v || u >= g.n) continue;
                const std::uint64_t* ru = bits.row(u);
                bool covers = true;
                for (int k = 0; k < W; ++k) {
                    std::uint64_t have = ru[k];
                    if (k == (u >> 6)) have |= 1ull << (u & 63);
                    if ((have & Nv[static_cast<size_t>(k)]) != Nv[static_cast<size_t>(k)]) {
                        covers = false;
                        break;
                    }
                }
                if (covers) {
                    hit = true;
                    break;
                }
            }
        }
        if (hit) {
            dominated[static_cast<size_t>(v)] = 1;
            ++p.n_dom;
            p.star_edges += deg[v];
        }
    }
    p.frac = g.n ? static_cast<double>(p.n_dom) / static_cast<double>(g.n) : 0;
    return p;
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
    std::vector<std::uint64_t> cover;   // I189: bits[first] minus later[first]
    std::vector<std::uint64_t> cwords;  // I191: C = bits[u] & bits[v]
};

inline void bits_clear_index(std::vector<std::uint64_t>& words, index_t i) {
    words[static_cast<unsigned>(i) >> 6] &= ~(1ull << (i & 63));
}

inline bool bits_test(const std::vector<std::uint64_t>& words, index_t i) {
    return (words[static_cast<unsigned>(i) >> 6] >> (i & 63)) & 1ull;
}

// I199: Tm walk when later[cand] is long; bits cover when later[cand] < |C|.
// I198's blanket AND-eq paid later[] masks on every torus shift rescan.
inline index_t first_dominator_adapt(const DenseTimes& Tm, const std::vector<index_t>& C_now,
                                    value_t t, const LiveAdj& nbr, int budget, Counters* ctr,
                                    const std::vector<int>* deg, LiveBits* bits, LiveAdj* later,
                                    std::vector<std::uint64_t>& cover) {
    if (C_now.empty()) return -1;
    if (C_now.size() == 1) {
        if (ctr) ++ctr->n_collapse_dom_hits;
        return C_now[0];
    }
    const size_t need = C_now.size() - 1;
    int tried = 0;
    for (index_t cand : C_now) {
        const size_t cand_deg = deg ? static_cast<size_t>((*deg)[cand]) : nbr[cand].size();
        if (cand_deg < need) continue;
        if (ctr) ++ctr->n_collapse_dom_tests;
        bool ok = false;
        if (bits && later && (*later)[cand].size() < C_now.size()) {
            const int W = bits->W;
            if (cover.size() != static_cast<size_t>(W))
                cover.assign(static_cast<size_t>(W), 0);
            std::memcpy(cover.data(), bits->row(cand),
                        static_cast<size_t>(W) * sizeof(std::uint64_t));
            for (const LiveNbr& p : (*later)[cand]) {
                if (p.second > t) bits_clear_index(cover, p.first);
            }
            ok = true;
            for (index_t w : C_now) {
                if (w == cand) continue;
                if (!bits_test(cover, w)) {
                    ok = false;
                    break;
                }
            }
            if (ctr) ctr->n_collapse_c_probes += W;
        } else {
            ok = dominated_by(Tm, C_now, cand, t);
        }
        if (ok) {
            if (ctr) ++ctr->n_collapse_dom_hits;
            return cand;
        }
        if (budget > 0 && ++tried >= budget) return -1;
    }
    return -1;
}

inline bool bits_nonzero(const std::vector<std::uint64_t>& words) {
    for (std::uint64_t w : words) {
        if (w) return true;
    }
    return false;
}

template <class Fn>
inline void bits_for_each(const std::vector<std::uint64_t>& words, Fn&& fn) {
    for (size_t w0 = 0; w0 < words.size(); ++w0) {
        std::uint64_t word = words[w0];
        while (word) {
            const int tz = __builtin_ctzll(word);
            word &= word - 1;
            fn(static_cast<index_t>(w0 * 64 + tz));
        }
    }
}

// I198: N_t domination via bits[cand] (minus later[cand]>t) covering C bits.
// Used in the shift heap so we do not rebuild Tm walks of C_now at each grade.
inline index_t and_eq_first_in_bits(const LiveBits& bits, const LiveAdj& later, value_t t,
                                   const std::vector<std::uint64_t>& cwords, size_t nC,
                                   const std::vector<int>* deg,
                                   std::vector<std::uint64_t>& cover, Counters& c) {
    if (nC == 0) return -1;
    const int W = bits.W;
    if (cover.size() != static_cast<size_t>(W))
        cover.assign(static_cast<size_t>(W), 0);
    if (nC == 1) {
        for (int w0 = 0; w0 < W; ++w0) {
            const std::uint64_t word = cwords[static_cast<size_t>(w0)];
            if (word) {
                ++c.n_collapse_dom_hits;
                return static_cast<index_t>(w0 * 64 + __builtin_ctzll(word));
            }
        }
        return -1;
    }
    const size_t need = nC - 1;
    for (int w0 = 0; w0 < W; ++w0) {
        std::uint64_t word = cwords[static_cast<size_t>(w0)];
        while (word) {
            const int tz = __builtin_ctzll(word);
            word &= word - 1;
            const index_t cand = static_cast<index_t>(w0 * 64 + tz);
            if (deg && static_cast<size_t>((*deg)[cand]) < need) continue;
            ++c.n_collapse_dom_tests;
            std::memcpy(cover.data(), bits.row(cand),
                        static_cast<size_t>(W) * sizeof(std::uint64_t));
            for (const LiveNbr& p : later[cand]) {
                if (p.second > t) bits_clear_index(cover, p.first);
            }
            bool covers = true;
            for (int k = 0; k < W; ++k) {
                std::uint64_t mask = cwords[static_cast<size_t>(k)];
                if (k == (cand >> 6)) mask &= ~(1ull << (cand & 63));
                if ((cover[static_cast<size_t>(k)] & mask) != mask) {
                    covers = false;
                    break;
                }
            }
            c.n_collapse_c_probes += W;
            if (covers) {
                ++c.n_collapse_dom_hits;
                return cand;
            }
        }
    }
    return -1;
}

// One backward edge (Glisse–Pritam). t_in is the start filtration (may be t_*
// on a D&C merge replay). Returns true if the edge is kept.
inline bool process_one_backward(const Edge& e_in, value_t t_in, DenseTimes& Tm,
                                 LiveAdj& nbr, BwScratch& S,
                                 int dom_budget, Edge& out, Counters& c,
                                 LiveBits* bits = nullptr,
                                 std::vector<int>* deg = nullptr,
                                 LiveAdj* later = nullptr,
                                 std::vector<index_t>* vdom = nullptr) {
    const index_t u = e_in.u, v = e_in.v;
    value_t t = t_in;
    S.C_now.clear();
    S.C_later.clear();
    std::int64_t commons = 0;
    index_t known_dom = -1;
    const bool walk_u = nbr[u].size() <= nbr[v].size();
    const auto& src = walk_u ? nbr[u] : nbr[v];
    const value_t* r_other = walk_u ? Tm.row(v) : Tm.row(u);
    const value_t* r_src = walk_u ? Tm.row(u) : Tm.row(v);

    auto drop_uv = [&]() {
        Tm.erase(u, v);
        if (bits) bits->clear_edge(u, v);
        if (deg) {
            --(*deg)[u];
            --(*deg)[v];
        }
        // I186: bits path does not need LiveAdj for C; skip star scans.
        if (!bits) {
            drop_live_nbr(nbr, u, v);
            drop_live_nbr(nbr, v, u);
        }
    };

    // I194: if an endpoint is strongly dominated at grade t
    // (N_t[a] ⊆ N_t[apex]), then {a,other} is edge-dominated by apex
    // (unless apex is the other endpoint). Sticky apex per vertex;
    // discover once, recheck O(W). Valid with or without later-commons.
    if (bits && later && vdom) {
        const int W = bits->W;
        auto nt_subset = [&](index_t a, index_t apex) -> bool {
            if (apex < 0 || apex == a) return false;
            S.cwords.assign(static_cast<size_t>(W), 0);
            std::memcpy(S.cwords.data(), bits->row(a),
                        static_cast<size_t>(W) * sizeof(std::uint64_t));
            S.cwords[static_cast<unsigned>(a) >> 6] |= 1ull << (a & 63);
            for (const LiveNbr& p : (*later)[a]) {
                if (p.second > t) bits_clear_index(S.cwords, p.first);
            }
            S.cover.assign(static_cast<size_t>(W), 0);
            std::memcpy(S.cover.data(), bits->row(apex),
                        static_cast<size_t>(W) * sizeof(std::uint64_t));
            S.cover[static_cast<unsigned>(apex) >> 6] |= 1ull << (apex & 63);
            for (const LiveNbr& p : (*later)[apex]) {
                if (p.second > t) bits_clear_index(S.cover, p.first);
            }
            for (int k = 0; k < W; ++k) {
                if ((S.cover[static_cast<size_t>(k)] & S.cwords[static_cast<size_t>(k)]) !=
                    S.cwords[static_cast<size_t>(k)])
                    return false;
            }
            c.n_collapse_c_probes += 2 * W;
            return true;
        };
        auto try_vertex = [&](index_t a, index_t other) -> bool {
            index_t apex = (*vdom)[a];
            if (apex == -1) {
                const std::uint64_t* ra = bits->row(a);
                for (int w0 = 0; w0 < W && apex < 0; ++w0) {
                    std::uint64_t word = ra[w0];
                    while (word) {
                        const int tz = __builtin_ctzll(word);
                        word &= word - 1;
                        const index_t w = static_cast<index_t>(w0 * 64 + tz);
                        if (w == a || w == other) continue;
                        ++c.n_collapse_dom_tests;
                        if (nt_subset(a, w)) {
                            apex = w;
                            break;
                        }
                    }
                }
                (*vdom)[a] = apex >= 0 ? apex : -2;
            }
            if (apex < 0 || apex == other) return false;
            if (!nt_subset(a, apex)) {
                (*vdom)[a] = -2;
                return false;
            }
            drop_uv();
            ++c.n_collapse_trims;
            ++c.n_collapse_fast_trims;
            ++c.n_collapse_vertex_trims;
            ++c.n_collapse_dom_hits;
            return true;
        };
        if (try_vertex(u, v) || try_vertex(v, u)) return false;
    }

    // I193: AND-eq every common when later[] says no later-common.
    // I189 is the first candidate; later apexes use the same cover test
    // and stop at the first hit. No hit => keep (no N_t dominator).
    // any_later falls through to consider() + shift heap.
    // I191 progressive ∩ was exact but slower on fused-fail trims
    // (blobs 809→1309 ms): it cannot early-abort the dominated case.
    if (bits && later) {
        bool any_later_fast = false;
        for (const LiveNbr& p : (*later)[u]) {
            if (p.second > t && Tm(v, p.first) < kInf / 2) {
                any_later_fast = true;
                break;
            }
        }
        if (!any_later_fast) {
            for (const LiveNbr& p : (*later)[v]) {
                if (p.second > t && Tm(u, p.first) < kInf / 2) {
                    any_later_fast = true;
                    break;
                }
            }
        }
        if (!any_later_fast) {
            const int W = bits->W;
            const std::uint64_t* bu = bits->row(u);
            const std::uint64_t* bv = bits->row(v);
            S.cwords.assign(static_cast<size_t>(W), 0);
            std::int64_t nC = 0;
            for (int w0 = 0; w0 < W; ++w0) {
                std::uint64_t word = bu[w0] & bv[w0];
                if (w0 == (u >> 6)) word &= ~(1ull << (u & 63));
                if (w0 == (v >> 6)) word &= ~(1ull << (v & 63));
                S.cwords[static_cast<size_t>(w0)] = word;
                nC += __builtin_popcountll(word);
            }
            c.n_collapse_c_probes += W;
            c.n_collapse_c_size_sum += nC;
            c.n_collapse_last_any_later = 0;
            commons = nC;
            if (nC == 0) {
                out = e_in;
                return true;
            }
            const size_t need = static_cast<size_t>(nC) - 1;
            S.cover.assign(static_cast<size_t>(W), 0);
            for (int w0 = 0; w0 < W; ++w0) {
                std::uint64_t word = S.cwords[static_cast<size_t>(w0)];
                while (word) {
                    const int tz = __builtin_ctzll(word);
                    word &= word - 1;
                    const index_t cand = static_cast<index_t>(w0 * 64 + tz);
                    if (deg && static_cast<size_t>((*deg)[cand]) < need) continue;
                    ++c.n_collapse_dom_tests;
                    std::memcpy(S.cover.data(), bits->row(cand),
                                static_cast<size_t>(W) * sizeof(std::uint64_t));
                    for (const LiveNbr& p : (*later)[cand]) {
                        if (p.second > t) bits_clear_index(S.cover, p.first);
                    }
                    bool covers = true;
                    for (int k = 0; k < W; ++k) {
                        std::uint64_t mask = S.cwords[static_cast<size_t>(k)];
                        if (k == (cand >> 6)) mask &= ~(1ull << (cand & 63));
                        if ((S.cover[static_cast<size_t>(k)] & mask) != mask) {
                            covers = false;
                            break;
                        }
                    }
                    c.n_collapse_c_probes += W;
                    if (covers) {
                        drop_uv();
                        ++c.n_collapse_trims;
                        ++c.n_collapse_fast_trims;
                        ++c.n_collapse_dom_hits;
                        c.n_collapse_last_fail_at = -1;
                        return false;
                    }
                }
            }
            out = e_in;
            return true;
        } else {
            // I197: any_later — strip later-commons via later[], AND-eq C_now.
            // No dominator of C_now => keep at t (shift only starts if dominated
            // at t). Hit => fall through to the shift heap with C_now/C_later.
            const int W = bits->W;
            const std::uint64_t* bu = bits->row(u);
            const std::uint64_t* bv = bits->row(v);
            S.cwords.assign(static_cast<size_t>(W), 0);
            for (int w0 = 0; w0 < W; ++w0) {
                std::uint64_t word = bu[w0] & bv[w0];
                if (w0 == (u >> 6)) word &= ~(1ull << (u & 63));
                if (w0 == (v >> 6)) word &= ~(1ull << (v & 63));
                S.cwords[static_cast<size_t>(w0)] = word;
            }
            auto take_later = [&](index_t a, index_t b) {
                for (const LiveNbr& p : (*later)[a]) {
                    if (p.second <= t) continue;
                    const index_t w = p.first;
                    if (w == u || w == v) continue;
                    if (!bits_test(S.cwords, w)) continue;
                    const value_t tw = Tm(b, w);
                    if (tw >= kInf / 2) continue;
                    const value_t tau = p.second > tw ? p.second : tw;
                    S.C_later.push_back({tau, w});
                    bits_clear_index(S.cwords, w);
                }
            };
            take_later(u, v);
            take_later(v, u);
            bits_for_each(S.cwords, [&](index_t w) { S.C_now.push_back(w); });
            commons = static_cast<std::int64_t>(S.C_now.size() + S.C_later.size());
            c.n_collapse_c_probes += W;
            c.n_collapse_c_size_sum += commons;
            c.n_collapse_last_any_later = S.C_later.empty() ? 0 : 1;
            if (S.C_now.empty()) {
                out = e_in;
                return true;
            }
            const size_t need = S.C_now.size() - 1;
            S.cover.assign(static_cast<size_t>(W), 0);
            bool hit = false;
            for (int w0 = 0; w0 < W && !hit; ++w0) {
                std::uint64_t word = S.cwords[static_cast<size_t>(w0)];
                while (word) {
                    const int tz = __builtin_ctzll(word);
                    word &= word - 1;
                    const index_t cand = static_cast<index_t>(w0 * 64 + tz);
                    if (deg && static_cast<size_t>((*deg)[cand]) < need) continue;
                    ++c.n_collapse_dom_tests;
                    std::memcpy(S.cover.data(), bits->row(cand),
                                static_cast<size_t>(W) * sizeof(std::uint64_t));
                    for (const LiveNbr& p : (*later)[cand]) {
                        if (p.second > t) bits_clear_index(S.cover, p.first);
                    }
                    bool covers = true;
                    for (int k = 0; k < W; ++k) {
                        std::uint64_t mask = S.cwords[static_cast<size_t>(k)];
                        if (k == (cand >> 6)) mask &= ~(1ull << (cand & 63));
                        if ((S.cover[static_cast<size_t>(k)] & mask) != mask) {
                            covers = false;
                            break;
                        }
                    }
                    c.n_collapse_c_probes += W;
                    if (covers) {
                        hit = true;
                        known_dom = cand;
                        ++c.n_collapse_dom_hits;
                        break;
                    }
                }
            }
            if (!hit) {
                out = e_in;
                return true;
            }
            if (S.C_later.empty()) {
                drop_uv();
                ++c.n_collapse_trims;
                ++c.n_collapse_fast_trims;
                return false;
            }
            // Dominated at t with later-commons: shift heap uses C_now/C_later.
        }
    }

    const bool skip_consider = bits && later && !S.C_later.empty() && !S.C_now.empty();
    if (!skip_consider) {
    // I156: fuse first-apex verify into the C walk. If the first common
    // dominates and there is no C_later, trim without materializing C
    // (I155: 1.07M trims vs 2k shifts on circle2000).
    index_t first = -1;
    const value_t* r_first = nullptr;
    bool fused_ok = true;
    bool any_later = false;
    bool later_a = false;
    bool later_b = false;
    std::int64_t fail_at = -1;
    auto consider = [&](index_t w, value_t t_src_w, value_t t_other_w) {
        if (w == u || w == v) return;
        if (t_other_w >= kInf / 2) return;
        ++commons;
        if (t_src_w > t) ++c.n_collapse_tau_late_common;
        const value_t tau = t_src_w > t_other_w ? t_src_w : t_other_w;
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
            if (t_src_w > t) later_a = true;
            else later_b = true;
        }
    };
    if (bits) {
        const std::uint64_t* bu = bits->row(u);
        const std::uint64_t* bv = bits->row(v);
        const int W = bits->W;
        c.n_collapse_c_probes += W;
        for (int w0 = 0; w0 < W; ++w0) {
            std::uint64_t word = bu[w0] & bv[w0];
            while (word) {
                const int tz = __builtin_ctzll(word);
                word &= word - 1;
                const index_t w = static_cast<index_t>(w0 * 64 + tz);
                consider(w, r_src[w], r_other[w]);
            }
        }
    } else {
        c.n_collapse_c_probes += static_cast<std::int64_t>(src.size());
        for (const LiveNbr& p : src) {
            if (p.second > t) ++c.n_collapse_tau_late;
            consider(p.first, p.second, r_other[p.first]);
        }
    }
    c.n_collapse_last_fail_at = fail_at;
    c.n_collapse_last_any_later = any_later ? 1 : 0;
    c.n_collapse_last_later_a = later_a ? 1 : 0;
    c.n_collapse_last_later_b = later_b ? 1 : 0;
    c.n_collapse_c_size_sum += commons;

    if (first >= 0 && fused_ok && !any_later) {
        drop_uv();
        ++c.n_collapse_trims;
        ++c.n_collapse_fast_trims;
        ++c.n_collapse_dom_hits;
        return false;
    }

    auto push_common = [&](index_t w, value_t t_src_w, value_t t_other_w) {
        if (w == u || w == v) return;
        if (t_other_w >= kInf / 2) return;
        const value_t tau = t_src_w > t_other_w ? t_src_w : t_other_w;
        if (tau <= t) S.C_now.push_back(w);
        else S.C_later.push_back({tau, w});
    };
    if (bits) {
        const std::uint64_t* bu = bits->row(u);
        const std::uint64_t* bv = bits->row(v);
        const int W = bits->W;
        for (int w0 = 0; w0 < W; ++w0) {
            std::uint64_t word = bu[w0] & bv[w0];
            while (word) {
                const int tz = __builtin_ctzll(word);
                word &= word - 1;
                const index_t w = static_cast<index_t>(w0 * 64 + tz);
                push_common(w, r_src[w], r_other[w]);
            }
        }
    } else {
        for (const LiveNbr& p : src) {
            push_common(p.first, p.second, r_other[p.first]);
        }
    }
    }  // !bits_filled

    const auto later_cmp = [](const std::pair<value_t, index_t>& a,
                              const std::pair<value_t, index_t>& b) {
        return a.first > b.first;
    };
    bool heapified = false;
    bool ever_shifted = false;
    bool dead = false;
    index_t witness = -1;
    while (true) {
        // I201: reuse I197's apex; after sticky fail, only scan N_t[witness] ∩ C.
        index_t dominator;
        if (known_dom >= 0) {
            dominator = known_dom;
            known_dom = -1;
        } else if (witness >= 0 && S.C_now.size() >= 32) {
            dominator = first_dominator_witness(Tm, S.C_now, t, nbr, dom_budget, &c, deg,
                                                witness);
        } else {
            dominator = first_dominator_deg(Tm, S.C_now, t, nbr, dom_budget, &c, deg);
        }
        if (dominator < 0) break;
        const value_t* rd = Tm.row(dominator);
        bool still = true;
        witness = -1;
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
                if (rd[w] > tw) {
                    still = false;
                    witness = w;
                }
                S.C_now.push_back(w);
                std::pop_heap(S.C_later.begin(), S.C_later.end(), later_cmp);
                S.C_later.pop_back();
            }
        }
        if (dead) break;
    }

    if (dead) {
        drop_uv();
        ++c.n_collapse_trims;
        return false;
    }
    out = e_in;
    out.t = ever_shifted ? t : t_in;
    c.n_collapse_last_commons = commons;
    if (deg) {
        c.n_collapse_last_mindeg = static_cast<std::int64_t>(
            std::min((*deg)[u], (*deg)[v]));
    } else {
        c.n_collapse_last_mindeg = static_cast<std::int64_t>(
            std::min(nbr[u].size(), nbr[v].size()));
    }
    if (ever_shifted) {
        Tm.set(u, v, out.t);
        if (!bits) {
            set_live_time(nbr, u, v, out.t);
            set_live_time(nbr, v, u, out.t);
        }
        ++c.n_collapse_shifts;
    }
    return true;
}

inline void init_collapse_graph(const std::vector<Edge>& E, int n, DenseTimes& Tm,
                                LiveAdj& nbr, LiveBits* bits = nullptr,
                                bool skip_nbr = false) {
    Tm = DenseTimes(n);
    nbr.assign(n, {});
    if (bits) *bits = LiveBits(n);
    std::vector<int> deg(n, 0);
    for (const Edge& e : E) {
        ++deg[e.u];
        ++deg[e.v];
    }
    if (!skip_nbr) {
        for (int i = 0; i < n; ++i) nbr[i].reserve(static_cast<size_t>(deg[i]));
    }
    for (const Edge& e : E) {
        Tm.set(e.u, e.v, e.t);
        if (!skip_nbr) {
            nbr[e.u].push_back({e.v, e.t});
            nbr[e.v].push_back({e.u, e.t});
        }
        if (bits) bits->set_edge(e.u, e.v);
    }
}

// Backward filtration-preserving edge collapse (Glisse–Pritam / GUDHI).
// I044: sticky dominator across C_later shifts + lazy heap (GUDHI L237–264).
inline Graph collapse_edges(Graph g, int iterations, Counters& c, int dom_budget = -1,
                            bool use_bits = true) {
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
        LiveBits bits_store;
        LiveBits* bits = nullptr;
        std::vector<int> deg;
        LiveAdj later;
        if (use_bits) {
            bits = &bits_store;
            init_collapse_graph(E, g.n, Tm, nbr, bits, true);
            deg.assign(static_cast<size_t>(g.n), 0);
            later.assign(static_cast<size_t>(g.n), {});
            scratch.cover.resize(static_cast<size_t>(bits->W));
            scratch.cwords.resize(static_cast<size_t>(bits->W));
            for (const Edge& e : E) {
                ++deg[e.u];
                ++deg[e.v];
            }
        } else {
            init_collapse_graph(E, g.n, Tm, nbr);
        }

        std::vector<Edge> kept;
        kept.reserve(E.size() / 4 + 8);
        const size_t mE = E.size();
        const size_t step = std::max<size_t>(mE / 8, 1);
        int early_n = 0;
        for (size_t i = 0; i < mE; ++i) {
            Edge out;
            if (process_one_backward(E[i], E[i].t, Tm, nbr, scratch, dom_budget, out, c, bits,
                                    use_bits ? &deg : nullptr,
                                    use_bits ? &later : nullptr,
                                    nullptr)) {
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
                if (use_bits) {
                    later[out.u].push_back({out.v, out.t});
                    later[out.v].push_back({out.u, out.t});
                }
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
    c.n_collapse_dom_skips += t.n_collapse_dom_skips;
    c.n_collapse_killer_hits += t.n_collapse_killer_hits;
    c.n_collapse_c_size_sum += t.n_collapse_c_size_sum;
    c.n_collapse_shift_lookups += t.n_collapse_shift_lookups;
    c.n_collapse_fast_trims += t.n_collapse_fast_trims;
    c.n_collapse_vertex_trims += t.n_collapse_vertex_trims;
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
                                         int sample_k, bool case_b = false,
                                         int escalate_k = 0, int escalate_until = 0,
                                         int later_b_cap = 0) {
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
    // I183: escalate only until the first fused-fail leave (I181 fired
    // seen_keep on the first empty-C / any leave). Bound the prefix so
    // n=2000 (no fused-fail) does not K=8 the whole young loop.
    const int K_esc = escalate_k > K ? escalate_k : K;
    const size_t esc_lim = escalate_until > 0
                               ? static_cast<size_t>(escalate_until)
                               : (K_esc > K ? std::min(young, n * 32) : 0);
    const int b_cap = later_b_cap > 0 ? later_b_cap : 4;
    bool got_fused = false;

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
        // I183: Case B leave only while later[other] is still a small
        // keep-support (cap). Uncapped leave cascaded (I180).
        if (!leave && case_b && later[other_v].size() <= static_cast<size_t>(b_cap)) {
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
        bool fused_leave = false;
        if (!leave) {
            index_t first = -1;
            const value_t* r_first = nullptr;
            bool fused_ok = true;
            int commons = 0;
            bool trim = false;
            const bool escalate = !got_fused && K_esc > K && i < esc_lim;
            const int K_now = escalate ? K_esc : K;
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
                    fused_leave = true;
                    break;
                }
                if (K_now > 0 && fused_ok && commons >= K_now) {
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
            if (fused_leave) got_fused = true;
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
