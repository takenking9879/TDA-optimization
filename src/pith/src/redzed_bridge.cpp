// I228: translation unit that owns the vendored RedZeD driver.
// redzed.cpp is MIT and compiled with REDZED_NO_MAIN so only the library
// entry is visible. Do not edit third_party/redzed/redzed.cpp.

#define REDZED_NO_MAIN
#include "../../../third_party/redzed/redzed.cpp"

#include "pith/redzed_bridge.hpp"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <cmath>
#include <functional>
#include <numeric>
#include <thread>
#include <unordered_map>
#include <utility>

// I245: same buckets / finish_buckets as vendor build_edges, but the two
// n² scans and the per-bucket sorts run on a thread pool. Final order is
// still (diam, comb_index) so VR≤T is unchanged.
static void finish_buckets_parallel(std::vector<value_t>& diam, std::vector<int32_t>& verts, int vpc,
                                    const std::vector<rank_t>& starts, int nb,
                                    const BinomialTable& bt) {
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    if (nth <= 1 || nb < 8) {
        SortScratch sc;
        finish_buckets(diam, verts, vpc, starts, nb, bt, sc);
        return;
    }
    std::atomic<int> next{0};
    auto worker = [&]() {
        SortScratch sc;
        while (true) {
            const int b = next.fetch_add(1, std::memory_order_relaxed);
            if (b >= nb) break;
            const size_t a = static_cast<size_t>(starts[b]) + 1;
            const size_t e = static_cast<size_t>(starts[b + 1]);
            if (e > a) sort_slice(diam, verts, vpc, a, e, bt, sc, 1);
        }
    };
    std::vector<std::thread> pool;
    pool.reserve(static_cast<size_t>(nth));
    for (int t = 0; t < nth; ++t) pool.emplace_back(worker);
    for (auto& th : pool) th.join();
}

static void build_edges_parallel(const DistanceMatrix& dist, value_t threshold,
                                 const BinomialTable& bt, EdgeList& out) {
    const int n = dist.n;
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    if (nth <= 1 || n < 256) {
        SortScratch sc;
        build_edges(dist, threshold, bt, sc, out);
        return;
    }
    const int64_t cap = (int64_t)n * (n - 1) / 2;
    int nb = (int)(cap >> 2);
    if (nb < 1024) nb = 1024;
    if (nb > (1 << 16)) nb = 1 << 16;
    const value_t dmin = 0.0;
    const value_t inv = (std::isfinite(threshold) && threshold > 0) ? 1.0f / threshold : 0.0f;

    auto stripe = [&](int t) {
        const int span = (n - 1 + nth - 1) / nth;
        const int j0 = 1 + t * span;
        const int j1 = std::min(n, j0 + span);
        return std::pair<int, int>{j0, j1};
    };

    std::vector<std::vector<rank_t>> local(static_cast<size_t>(nth),
                                           std::vector<rank_t>(static_cast<size_t>(nb) + 1, 0));
    {
        std::vector<std::thread> pool;
        pool.reserve(static_cast<size_t>(nth));
        for (int t = 0; t < nth; ++t) {
            pool.emplace_back([&, t]() {
                const auto [j0, j1] = stripe(t);
                auto& cnt = local[static_cast<size_t>(t)];
                for (int j = j0; j < j1; ++j) {
                    for (int i = 0; i < j; ++i) {
                        const value_t d = dist(i, j);
                        if (d <= threshold) cnt[bucket_of(d, dmin, inv, nb) + 1] += 1;
                    }
                }
            });
        }
        for (auto& th : pool) th.join();
    }

    std::vector<rank_t> cnt(static_cast<size_t>(nb) + 1, 0);
    for (int t = 0; t < nth; ++t)
        for (int b = 1; b <= nb; ++b) cnt[static_cast<size_t>(b)] += local[static_cast<size_t>(t)][static_cast<size_t>(b)];
    for (int t = 1; t <= nb; ++t) cnt[static_cast<size_t>(t)] += cnt[static_cast<size_t>(t) - 1];
    const size_t count = static_cast<size_t>(cnt[static_cast<size_t>(nb)]);
    out.count = count;
    if (count == 0) return;
    const std::vector<rank_t> starts = cnt;

    std::vector<std::vector<rank_t>> head(static_cast<size_t>(nth),
                                          std::vector<rank_t>(static_cast<size_t>(nb), 0));
    for (int b = 0; b < nb; ++b) {
        rank_t p = starts[static_cast<size_t>(b)];
        for (int t = 0; t < nth; ++t) {
            head[static_cast<size_t>(t)][static_cast<size_t>(b)] = p;
            p += local[static_cast<size_t>(t)][static_cast<size_t>(b) + 1];
        }
    }

    out.diam.resize(count);
    out.verts.resize(2 * count);
    {
        std::vector<std::thread> pool;
        pool.reserve(static_cast<size_t>(nth));
        for (int t = 0; t < nth; ++t) {
            pool.emplace_back([&, t]() {
                const auto [j0, j1] = stripe(t);
                auto& hd = head[static_cast<size_t>(t)];
                for (int j = j0; j < j1; ++j) {
                    for (int i = 0; i < j; ++i) {
                        const value_t d = dist(i, j);
                        if (d <= threshold) {
                            const int b = bucket_of(d, dmin, inv, nb);
                            const rank_t p = hd[static_cast<size_t>(b)]++;
                            out.diam[static_cast<size_t>(p)] = d;
                            out.verts[2 * static_cast<size_t>(p)] = i;
                            out.verts[2 * static_cast<size_t>(p) + 1] = j;
                        }
                    }
                }
            });
        }
        for (auto& th : pool) th.join();
    }
    finish_buckets_parallel(out.diam, out.verts, 2, starts, nb, bt);
}

// I246: vendor AE inserts R/Ri singleton then often erases it (no seeds +
// leftover coface = (n+1)-birth / zero bar). Skip that insert. When seeds
// exist, insert once and finish AE without re-advance / re-collect.
// set_side is a no-op unless side_vpc is set (H2+).
// I247 leftover_coface_fast was exact but slower (9.24× vs I246 9.56×) — reverted.
// I250: collect_candidates only reads ActiveReg. If no actives, reset any
// leftover seen from a prior seeded leftover and skip the face-slot walk.
// Uniform2 n=5000: 3.37M / 3.46M leftovers have empty ActiveReg.
// I252: leftover-coface on the no-seed path does not need seenbits
// (seedverts empty ⇒ seenbits is zero). H1 unrolls m=2. Do not add
// I247's extra dist() before coface_ready.
static void clear_seeds(State& st) {
    for (int32_t w : st.seedverts) {
        st.seen[w] = 0;
        st.seedlists[w].clear();
        st.seenbits[w >> 6] = 0;
    }
    st.seedverts.clear();
}

// Vendor has_leftover_coface always masks ~seenbits. On the 97% no-seed
// skip that mask is a no-op memory tax. Same coface_ready, same rbit AND.
// I253 coface_ready_h1 was exact but no pith cut (wave n=5000 0.36s was
// noise; standalone reduce 207≈I252 206 ms). Reverted.
// I255 unique-diam rbit-AND skip was exact 14/14 but no pith cut
// (n=5000 reduce 211 vs I252 206 ms). Reverted.
static bool leftover_coface_h1_noseen(State& st, const int32_t* xv, comb_t xidx, value_t r) {
    const uint64_t* rb = st.rbits.data();
    const int words = st.words, nv = st.nv;
    const int u = xv[0], v = xv[1];
    int wlo = st.rlo[u], whi = st.rhi[u];
    if (st.rlo[v] > wlo) wlo = st.rlo[v];
    if (st.rhi[v] < whi) whi = st.rhi[v];
    int32_t* cbuf = st.coface_buf.data();
    for (int w = wlo; w <= whi; ++w) {
        uint64_t acc = rb[(size_t)u * words + w] & rb[(size_t)v * words + w];
        while (acc) {
            const int bp = redzed_ctz64(acc);
            acc &= acc - 1;
            const int cand = w * 64 + bp;
            if (cand >= nv) break;
            if (coface_ready(cbuf, xv, 2, (int32_t)cand, xidx, r, st.dist, st.binom))
                return true;
        }
    }
    return false;
}

// H2+ no-seed leftover-coface: same skip of the empty seenbits mask.
static bool leftover_coface_noseen(State& st, const int32_t* xverts, int m, comb_t xidx,
                                    value_t r) {
    if (m == 2) return leftover_coface_h1_noseen(st, xverts, xidx, r);
    const uint64_t* rb = st.rbits.data();
    const int words = st.words, nv = st.nv;
    int wlo = 0, whi = words - 1;
    for (int i = 0; i < m; ++i) {
        const int v = xverts[i];
        if (st.rlo[v] > wlo) wlo = st.rlo[v];
        if (st.rhi[v] < whi) whi = st.rhi[v];
    }
    int32_t* cbuf = st.coface_buf.data();
    for (int w = wlo; w <= whi; ++w) {
        uint64_t acc = rb[(size_t)xverts[0] * words + w];
        if (!acc) continue;
        for (int i = 1; i < m; ++i) {
            acc &= rb[(size_t)xverts[i] * words + w];
            if (!acc) break;
        }
        if (!acc) continue;
        while (acc) {
            const int bp = redzed_ctz64(acc);
            acc &= acc - 1;
            const int cand = w * 64 + bp;
            if (cand >= nv) break;
            if (coface_ready(cbuf, xverts, m, (int32_t)cand, xidx, r, st.dist, st.binom))
                return true;
        }
    }
    return false;
}

static void ae_prepare(State& st, const int32_t* verts, value_t sdiam) {
    advance_rbits(st, sdiam);
    if (st.act.slot_of.count == 0) clear_seeds(st);
    else collect_candidates(st, verts);
}

static void ae_keep_singleton(State& st, rank_t xrank, const int32_t* verts, value_t sdiam) {
    SetDict& Rn = st.R[st.n];
    SetDict& Rin = st.Ri[st.n];
    const slot_t s1 = Rn.singleton(xrank, xrank);
    const slot_t s2 = Rin.singleton(xrank, xrank);
    Rn.set_side(s1, sdiam, verts);
    Rin.set_side(s2, sdiam, verts);
    register_active(st, xrank, s1, verts);
}

// Seeded leftover: insert, process_seeded, maybe leftover-coface / register.
static void ae_seeded(State& st, rank_t xrank, comb_t xidx, const int32_t* verts, value_t sdiam) {
    const int m = st.n + 1;
    SetDict& Rn = st.R[st.n];
    SetDict& Rin = st.Ri[st.n];
    const slot_t s1 = Rn.singleton(xrank, xrank);
    const slot_t s2 = Rin.singleton(xrank, xrank);
    Rn.set_side(s1, sdiam, verts);
    Rin.set_side(s2, sdiam, verts);
    slot_t xslot = s1;
    bool dirty = false;
    for (size_t t = 0; t < st.seedverts.size(); ++t) {
        const int32_t w = st.seedverts[t];
        const std::vector<slot_t>& sdw = st.seedlists[w];
        if (seeded_is_noop(Rn, xslot, sdw)) continue;
        if (coface_ready(st.coface_buf.data(), verts, m, w, xidx, sdiam, st.dist, st.binom))
            dirty |= process_seeded(st, xslot, sdw, sdiam);
    }
    if (!dirty) {
        if (has_leftover_coface(st, verts, m, xidx, sdiam)) {
            Rn.erase(xrank);
            Rin.erase(xrank);
            return;
        }
        register_active(st, xrank, xslot, verts);
        return;
    }
    xslot = Rn.slot(xrank);
    if (xslot) {
        if (has_leftover_coface(st, verts, m, xidx, sdiam)) process_leftover(st, xslot, sdiam);
        xslot = Rn.slot(xrank);
    }
    if (xslot) register_active(st, xrank, xslot, verts);
}

static void active_enum_lazy(State& st, rank_t xrank, comb_t xidx, const int32_t* verts,
                             value_t sdiam) {
    const int m = st.n + 1;
    ae_prepare(st, verts, sdiam);
    if (st.seedverts.empty()) {
        if (leftover_coface_noseen(st, verts, m, xidx, sdiam)) return;
        ae_keep_singleton(st, xrank, verts, sdiam);
        return;
    }
    ae_seeded(st, xrank, xidx, verts, sdiam);
}

// I244: VR≤T does not need enclosing (cone). Finite T → thr=T is exact.
// I245: parallel build_edges when no prebuilt EdgeList.
// I246: lazy R/Ri insert on top-dimension AE.
static std::vector<std::vector<std::pair<value_t, value_t>>>
redzed_vr(DistanceMatrix& distIn, int n, value_t threshold, EdgeList* prebuilt) {
    int nv = distIn.n;
    value_t thr = threshold;
    if (!std::isfinite(threshold)) {
        value_t cone = VINF;
        for (int j = 0; j < nv; ++j) {
            value_t mx = -VINF;
            for (int i = 0; i < nv; ++i) mx = std::max(mx, distIn(i, j));
            cone = std::min(cone, mx);
        }
        thr = cone;
    }

    State st;
    st.nv = nv;
    st.n = n;
    st.dist = std::move(distIn);
    st.binom = BinomialTable(nv, n + 2);
    if (prebuilt && prebuilt->count) {
        st.edges = std::move(*prebuilt);
    } else {
        build_edges_parallel(st.dist, thr, st.binom, st.edges);
    }

    st.words = (nv + 63) / 64;
    st.R.resize(n + 1);
    st.Ri.resize(n + 1);
    st.pairs.assign(n + 1, {});
    st.sbirth.assign(n + 1, {});
    st.sdeath.assign(n + 1, {});
    st.want_spx = false;
    UnionFind uf(nv);
    st.uf = &uf;
    st.act.m = n + 1;
    {
        comb_t fu = st.binom(nv, n);
        st.act.face_slot.init(fu);
    }
    st.seen.assign(nv, 0);
    st.seenbits.assign(st.words, 0);
    st.seedlists.assign(nv, {});
    st.rbits.assign((size_t)st.words * nv, 0);
    st.rlo.assign(nv, st.words);
    st.rhi.assign(nv, -1);
    st.coface_buf.assign(n + 2, 0);
    st.top_buf.assign(n + 1, 0);

    {
        const bool want_h1 = n >= 1;
        SetDict* R1 = want_h1 ? &st.R[1] : nullptr;
        SetDict* Ri1 = want_h1 ? &st.Ri[1] : nullptr;
        const EdgeList& ed = st.edges;
        for (size_t e = 1; e <= ed.count; ++e) {
            int lo = ed.verts[2 * (e - 1)];
            int hi = ed.verts[2 * (e - 1) + 1];
            int32_t a = uf.find(lo), b = uf.find(hi);
            value_t ediam = ed.diam[e - 1];
            if (a == b) {
                if (want_h1) {
                    rank_t er = (rank_t)e;
                    if (n == 1) {
                        // I251: inline the 97% empty-seed leftover-coface skip so
                        // those leftovers do not enter active_enum_lazy.
                        // I254 skip-prepare on empty ActiveReg was exact but
                        // no pith cut (n=5000 0.31≈I252 0.30 s). Reverted.
                        st.top_buf[0] = lo;
                        st.top_buf[1] = hi;
                        const int32_t* xv = &ed.verts[2 * (e - 1)];
                        ae_prepare(st, st.top_buf.data(), ediam);
                        if (st.seedverts.empty()) {
                            const comb_t xidx = comb_index(xv, 2, st.binom);
                            if (leftover_coface_h1_noseen(st, xv, xidx, ediam)) continue;
                            ae_keep_singleton(st, er, st.top_buf.data(), ediam);
                        } else {
                            const comb_t xidx = comb_index(xv, 2, st.binom);
                            ae_seeded(st, er, xidx, st.top_buf.data(), ediam);
                        }
                    } else {
                        R1->singleton(er, er);
                        Ri1->singleton(er, er);
                    }
                }
            } else {
                int32_t jj = std::max(a, b), oo = std::min(a, b);
                uf.parent[jj] = oo;
                if (ediam != 0.0) st.pairs[0].push_back({0.0, ediam});
            }
        }
    }

    if (n >= 2) {
        for (int d = 2; d <= n; ++d) {
            comb_t uni = st.binom(nv, d);
            st.csmap.init(uni);
            {
                std::vector<rank_t> live;
                st.R[d - 1].keys(live);
                for (rank_t z : live)
                    st.csmap.set(comb_index(lvl_verts_of(st, d - 1, z), d, st.binom),
                                 st.R[d - 1].slot(z));
            }
            st.cson = true;
            st.csdim = d - 1;

            int m = d + 1;
            SetDict& Rd = st.R[d];
            SetDict& Rid = st.Ri[d];
            SetDict& Rprev = st.R[d - 1];
            Rd.side_vpc = m;
            Rid.side_vpc = m;
            rank_t next_rank = 0;

            generate_stream(st.edges, st.dist, d, st.binom, [&](value_t sdiam, const int32_t* cv) {
                rank_t sr = ++next_rank;
                st.bar.clear();
                for (int omit = 1; omit <= m; ++omit) {
                    comb_t f = face_index_without(cv, m, omit, st.binom);
                    slot_t fs = st.csmap.get(f);
                    if (fs) sset_xor(st.bar, Rprev.at(fs), st.buf);
                }
                if (st.bar.empty()) {
                    if (d == n) {
                        comb_t xidx = comb_index(cv, m, st.binom);
                        active_enum_lazy(st, sr, xidx, cv, sdiam);
                    } else {
                        slot_t s1 = Rd.singleton(sr, sr);
                        slot_t s2 = Rid.singleton(sr, sr);
                        Rd.set_side(s1, sdiam, cv);
                        Rid.set_side(s2, sdiam, cv);
                    }
                } else {
                    resolve_bar(st, d, st.bar, sdiam);
                }
            });

            st.cson = false;
            st.csmap.init(0);
            emit_infinite(st, d - 1);
            st.R[d - 1] = SetDict();
            st.Ri[d - 1] = SetDict();
        }
    }

    for (int v = 0; v < nv; ++v)
        if (uf.find(v) == v) st.pairs[0].push_back({0.0, VINF});
    emit_infinite(st, n);
    return st.pairs;
}

namespace pith {

static void append_bars(Result& r, const std::vector<std::vector<std::pair<value_t, value_t>>>& bars,
                        int dim) {
    const int up = std::min(dim, static_cast<int>(bars.size()) - 1);
    for (int d = 0; d <= up; ++d) {
        for (const auto& p : bars[static_cast<size_t>(d)]) {
            r.pairs.push_back({d, p.first, p.second});
        }
    }
}

static value_t point_dist(const std::vector<std::vector<value_t>>& pts, int i, int j) {
    const int d = static_cast<int>(pts[static_cast<size_t>(i)].size());
    double s = 0;
    for (int k = 0; k < d; ++k) {
        const double df = static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) -
                          static_cast<double>(pts[static_cast<size_t>(j)][static_cast<size_t>(k)]);
        s += df * df;
    }
    return static_cast<value_t>(std::sqrt(s));
}

static void fill_submatrix_from_points(DistanceMatrix& S, const std::vector<std::vector<value_t>>& pts,
                                       const std::vector<int>& verts) {
    const int m = static_cast<int>(verts.size());
    S.resize_lower(m);
    for (int j = 1; j < m; ++j)
        for (int i = 0; i < j; ++i)
            S.mat[DistanceMatrix::offset(i, j)] =
                point_dist(pts, verts[static_cast<size_t>(i)], verts[static_cast<size_t>(j)]);
}

static void fill_submatrix_from_D(DistanceMatrix& S, const DistanceMatrix& D,
                                  const std::vector<int>& verts) {
    const int m = static_cast<int>(verts.size());
    S.resize_lower(m);
    for (int j = 1; j < m; ++j)
        for (int i = 0; i < j; ++i)
            S.mat[DistanceMatrix::offset(i, j)] =
                D(verts[static_cast<size_t>(i)], verts[static_cast<size_t>(j)]);
}

struct RedzedBlock {
    std::vector<int> verts;
    std::vector<std::vector<std::pair<value_t, value_t>>> bars;
};

template <class Fill>
static void run_blocks_parallel(std::vector<RedzedBlock>& blocks, int dim, value_t threshold,
                                Fill&& fill) {
    auto run_block = [&](RedzedBlock& b) {
        const int m = static_cast<int>(b.verts.size());
        if (m <= 1) return;
        DistanceMatrix S;
        fill(S, b.verts);
        b.bars = redzed_vr(S, dim, threshold, nullptr);
    };
    std::vector<RedzedBlock*> work;
    work.reserve(blocks.size());
    for (auto& b : blocks)
        if (b.verts.size() > 1) work.push_back(&b);
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    const int nworkers = std::min(nth, static_cast<int>(work.size()));
    if (nworkers > 1) {
        std::atomic<size_t> next{0};
        auto worker = [&]() {
            while (true) {
                const size_t i = next.fetch_add(1, std::memory_order_relaxed);
                if (i >= work.size()) break;
                run_block(*work[i]);
            }
        };
        std::vector<std::thread> pool;
        pool.reserve(static_cast<size_t>(nworkers));
        for (int t = 0; t < nworkers; ++t) pool.emplace_back(worker);
        for (auto& th : pool) th.join();
    } else {
        for (RedzedBlock* b : work) run_block(*b);
    }
}

static void merge_block_bars(Result& r, std::vector<RedzedBlock>& blocks, int dim) {
    for (auto& b : blocks) {
        if (b.verts.size() <= 1) r.pairs.push_back({0, 0, kInf});
        else append_bars(r, b.bars, dim);
    }
}

static std::vector<std::vector<int>> comps_from_parent(const std::vector<int>& parent_in, int n) {
    std::vector<int> parent = parent_in;
    auto find = [&](int x) {
        while (parent[static_cast<size_t>(x)] != x) {
            parent[static_cast<size_t>(x)] = parent[static_cast<size_t>(parent[static_cast<size_t>(x)])];
            x = parent[static_cast<size_t>(x)];
        }
        return x;
    };
    std::vector<std::vector<int>> buckets(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) buckets[static_cast<size_t>(find(i))].push_back(i);
    std::vector<std::vector<int>> comps;
    comps.reserve(static_cast<size_t>(n));
    for (auto& b : buckets)
        if (!b.empty()) comps.push_back(std::move(b));
    return comps;
}

static std::int64_t intra_pairs(const std::vector<std::vector<int>>& comps) {
    std::int64_t s = 0;
    for (const auto& c : comps) {
        const std::int64_t m = static_cast<std::int64_t>(c.size());
        s += m * (m - 1) / 2;
    }
    return s;
}

// I240: cell size T, Moore neighborhood. If d≤T then |Δcell_k|≤1.
static inline uint64_t pack_cell(const int* c, int d) {
    uint64_t k = 0;
    for (int i = 0; i < d; ++i) {
        const uint64_t w = static_cast<uint32_t>(c[i]) & 0x1FFFFFu;
        k |= w << (21 * i);
    }
    return k;
}

static bool spatial_components(const std::vector<std::vector<value_t>>& pts, value_t T,
                               std::vector<std::vector<int>>& comps) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n <= 0 || d < 2 || d > 3 || !(T > 0) || !std::isfinite(T)) return false;

    std::vector<int> parent(static_cast<size_t>(n));
    std::iota(parent.begin(), parent.end(), 0);
    auto find = [&](int x) {
        while (parent[static_cast<size_t>(x)] != x) {
            parent[static_cast<size_t>(x)] = parent[static_cast<size_t>(parent[static_cast<size_t>(x)])];
            x = parent[static_cast<size_t>(x)];
        }
        return x;
    };
    auto unite = [&](int i, int j) {
        const int a = find(i), b = find(j);
        if (a != b) parent[static_cast<size_t>(b)] = a;
    };

    const double inv = 1.0 / static_cast<double>(T);
    auto cell_of = [&](int i, int* c) {
        for (int k = 0; k < d; ++k)
            c[k] = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) * inv));
    };

    std::unordered_map<uint64_t, std::vector<int>> grid;
    grid.reserve(static_cast<size_t>(n) * 2);
    for (int i = 0; i < n; ++i) {
        int c[3] = {0, 0, 0};
        cell_of(i, c);
        grid[pack_cell(c, d)].push_back(i);
    }

    auto visit_neighbors = [&](int i, const int* c0) {
        int c[3] = {0, 0, 0};
        const int z1 = (d == 3) ? 1 : 0;
        for (int dx = -1; dx <= 1; ++dx) {
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dz = -z1; dz <= z1; ++dz) {
                    c[0] = c0[0] + dx;
                    c[1] = c0[1] + dy;
                    c[2] = (d == 3) ? c0[2] + dz : 0;
                    const auto it = grid.find(pack_cell(c, d));
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        if (j <= i) continue;
                        if (point_dist(pts, i, j) <= T) unite(i, j);
                    }
                }
            }
        }
    };

    for (int i = 0; i < n; ++i) {
        int c0[3] = {0, 0, 0};
        cell_of(i, c0);
        visit_neighbors(i, c0);
    }
    comps = comps_from_parent(parent, n);
    return true;
}

struct SpatEdge {
    value_t t;
    int u, v;
};

// I241: Moore neighborhood emits every Euclidean pair with d≤T.
static bool spatial_edges(const std::vector<std::vector<value_t>>& pts, value_t T,
                          std::vector<SpatEdge>& out) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n <= 0 || d < 2 || d > 3 || !(T > 0) || !std::isfinite(T)) return false;
    const double inv = 1.0 / static_cast<double>(T);
    auto cell_of = [&](int i, int* c) {
        for (int k = 0; k < d; ++k)
            c[k] = static_cast<int>(
                std::floor(static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) * inv));
    };
    std::unordered_map<uint64_t, std::vector<int>> grid;
    grid.reserve(static_cast<size_t>(n) * 2);
    for (int i = 0; i < n; ++i) {
        int c[3] = {0, 0, 0};
        cell_of(i, c);
        grid[pack_cell(c, d)].push_back(i);
    }
    out.clear();
    out.reserve(static_cast<size_t>(n) * 8);
    const int z1 = (d == 3) ? 1 : 0;
    for (int i = 0; i < n; ++i) {
        int c0[3] = {0, 0, 0};
        cell_of(i, c0);
        int c[3] = {0, 0, 0};
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                for (int dz = -z1; dz <= z1; ++dz) {
                    c[0] = c0[0] + dx;
                    c[1] = c0[1] + dy;
                    c[2] = (d == 3) ? c0[2] + dz : 0;
                    const auto it = grid.find(pack_cell(c, d));
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        if (j <= i) continue;
                        const value_t dist = point_dist(pts, i, j);
                        if (dist <= T) out.push_back({dist, i, j});
                    }
                }
    }
    return true;
}

static double bbox_max_extent(const std::vector<std::vector<value_t>>& pts) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n <= 0 || d <= 0) return 0;
    double L = 0;
    for (int k = 0; k < d; ++k) {
        double lo = static_cast<double>(pts[0][static_cast<size_t>(k)]);
        double hi = lo;
        for (int i = 1; i < n; ++i) {
            const double x = static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]);
            if (x < lo) lo = x;
            if (x > hi) hi = x;
        }
        if (hi - lo > L) L = hi - lo;
    }
    return L;
}

// I256: EdgeList from spatial d≤T pairs. Same (diam, comb_index) buckets
// as vendor build_edges, so VR≤T order is unchanged.
static void edgelist_from_spat(const std::vector<SpatEdge>& se, value_t threshold,
                               const BinomialTable& bt, EdgeList& out) {
    const size_t m = se.size();
    if (m == 0) {
        out.count = 0;
        return;
    }
    int nb = static_cast<int>(m >> 2);
    if (nb < 1024) nb = 1024;
    if (nb > (1 << 16)) nb = 1 << 16;
    const value_t inv = (threshold > 0) ? static_cast<value_t>(1.0 / threshold) : 0.0f;
    std::vector<rank_t> cnt(static_cast<size_t>(nb) + 1, 0);
    for (const SpatEdge& e : se) cnt[static_cast<size_t>(bucket_of(e.t, 0.0f, inv, nb) + 1)] += 1;
    for (int t = 1; t <= nb; ++t) cnt[static_cast<size_t>(t)] += cnt[static_cast<size_t>(t) - 1];
    out.count = static_cast<size_t>(cnt[static_cast<size_t>(nb)]);
    const std::vector<rank_t> starts = cnt;
    out.diam.resize(out.count);
    out.verts.resize(2 * out.count);
    for (const SpatEdge& e : se) {
        const int b = bucket_of(e.t, 0.0f, inv, nb);
        const rank_t p = cnt[static_cast<size_t>(b)]++;
        out.diam[static_cast<size_t>(p)] = e.t;
        int lo = e.u, hi = e.v;
        if (lo > hi) std::swap(lo, hi);
        out.verts[2 * static_cast<size_t>(p)] = lo;
        out.verts[2 * static_cast<size_t>(p) + 1] = hi;
    }
    finish_buckets_parallel(out.diam, out.verts, 2, starts, nb, bt);
}

static Result kruskal_h0(int n, std::vector<SpatEdge>&& edges) {
    Result r;
    Counters& c = r.counters;
    c.n_vertices = n;
    c.n_distances = static_cast<std::int64_t>(edges.size());
    c.pipeline = "pith:redzed-h0";
    std::sort(edges.begin(), edges.end(), [](const SpatEdge& a, const SpatEdge& b) {
        if (a.t != b.t) return a.t < b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });
    std::vector<int> parent(static_cast<size_t>(n));
    std::iota(parent.begin(), parent.end(), 0);
    auto find = [&](int x) {
        while (parent[static_cast<size_t>(x)] != x) {
            parent[static_cast<size_t>(x)] = parent[static_cast<size_t>(parent[static_cast<size_t>(x)])];
            x = parent[static_cast<size_t>(x)];
        }
        return x;
    };
    int live = n;
    const auto t0 = std::chrono::steady_clock::now();
    for (const SpatEdge& e : edges) {
        const int a = find(e.u), b = find(e.v);
        if (a == b) continue;
        parent[static_cast<size_t>(b)] = a;
        --live;
        r.pairs.push_back({0, 0, e.t});
    }
    for (int i = 0; i < live; ++i) r.pairs.push_back({0, 0, kInf});
    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.n_collapse_trims = live;
    return r;
}

// I239: VR≤T of a disconnected G_T is the wedge of the components.
// Split, run RedZeD on each block, merge bars. Exact. Superadditive
// reduce (blobs = 3 clusters at T=1). One component → same as I228.
static Result finish_redzed(DistanceMatrix&& D, int maxdim, value_t threshold) {
    Result r;
    Counters& c = r.counters;
    const int n = D.n;
    c.n_vertices = n;
    if (n <= 0 || maxdim < 0) return r;
    if (maxdim < 1) {
        std::vector<SpatEdge> E;
        E.reserve(static_cast<size_t>(n));
        for (int j = 1; j < n; ++j)
            for (int i = 0; i < j; ++i) {
                const value_t d = D(i, j);
                if (d <= threshold) E.push_back({d, i, j});
            }
        return kruskal_h0(n, std::move(E));
    }
    const int dim = maxdim;

    std::vector<int> parent(static_cast<size_t>(n));
    std::iota(parent.begin(), parent.end(), 0);
    auto find = [&](int x) {
        while (parent[static_cast<size_t>(x)] != x) {
            parent[static_cast<size_t>(x)] = parent[static_cast<size_t>(parent[static_cast<size_t>(x)])];
            x = parent[static_cast<size_t>(x)];
        }
        return x;
    };
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            const value_t d = D(i, j);
            if (d <= threshold) {
                const int a = find(i), b = find(j);
                if (a != b) parent[static_cast<size_t>(b)] = a;
            }
        }
    }
    auto comps = comps_from_parent(parent, n);
    c.n_collapse_trims = static_cast<std::int64_t>(comps.size());

    const auto t0 = std::chrono::steady_clock::now();
    if (comps.size() <= 1) {
        auto bars = redzed_vr(D, dim, threshold, nullptr);
        append_bars(r, bars, dim);
        c.pipeline = "pith:redzed";
    } else {
        c.pipeline = "pith:redzed-cc";
        std::vector<RedzedBlock> blocks(comps.size());
        for (size_t i = 0; i < comps.size(); ++i) blocks[i].verts = std::move(comps[i]);
        run_blocks_parallel(blocks, dim, threshold, [&](DistanceMatrix& S, const std::vector<int>& verts) {
            fill_submatrix_from_D(S, D, verts);
        });
        merge_block_bars(r, blocks, dim);
    }
    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return r;
}

static Result finish_redzed_from_points(const std::vector<std::vector<value_t>>& pts,
                                        std::vector<std::vector<int>> comps, int maxdim,
                                        value_t threshold) {
    Result r;
    Counters& c = r.counters;
    const int n = static_cast<int>(pts.size());
    c.n_vertices = n;
    if (n <= 0 || maxdim < 0) return r;
    const int dim = maxdim < 1 ? 0 : maxdim;
    c.n_collapse_trims = static_cast<std::int64_t>(comps.size());
    c.n_distances = intra_pairs(comps);

    const auto t0 = std::chrono::steady_clock::now();
    if (comps.size() <= 1) {
        DistanceMatrix D;
        D.resize_lower(n);
        for (int j = 1; j < n; ++j)
            for (int i = 0; i < j; ++i)
                D.mat[DistanceMatrix::offset(i, j)] = point_dist(pts, i, j);
        auto bars = redzed_vr(D, dim, threshold, nullptr);
        append_bars(r, bars, dim);
        c.pipeline = "pith:redzed-thr";
        c.n_distances = static_cast<std::int64_t>(n) * (n - 1) / 2;
    } else {
        c.pipeline = "pith:redzed-cc";
        std::vector<RedzedBlock> blocks(comps.size());
        for (size_t i = 0; i < comps.size(); ++i) blocks[i].verts = std::move(comps[i]);
        run_blocks_parallel(blocks, dim, threshold, [&](DistanceMatrix& S, const std::vector<int>& verts) {
            fill_submatrix_from_points(S, pts, verts);
        });
        merge_block_bars(r, blocks, dim);
    }
    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return r;
}

Result persist_redzed(const std::vector<std::vector<value_t>>& dist, int maxdim,
                      value_t threshold) {
    const int n = static_cast<int>(dist.size());
    if (n <= 0 || maxdim < 0) {
        Result r;
        r.counters.n_vertices = n;
        return r;
    }
    DistanceMatrix D;
    D.resize_lower(n);
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            D.mat[DistanceMatrix::offset(i, j)] = dist[static_cast<size_t>(i)][static_cast<size_t>(j)];
        }
    }
    return finish_redzed(std::move(D), maxdim, threshold);
}

Result persist_redzed_from_points(const std::vector<std::vector<value_t>>& pts, int maxdim,
                                 value_t threshold) {
    const int n = static_cast<int>(pts.size());
    if (n <= 0 || maxdim < 0) {
        Result r;
        r.counters.n_vertices = n;
        return r;
    }
    // I241: H0 is Kruskal. Spatial edges when d∈{2,3}; no RedZeD.
    if (maxdim < 1) {
        const auto tm0 = std::chrono::steady_clock::now();
        std::vector<SpatEdge> E;
        if (!spatial_edges(pts, threshold, E)) {
            E.reserve(static_cast<size_t>(n) * 4);
            for (int j = 1; j < n; ++j)
                for (int i = 0; i < j; ++i) {
                    const value_t dist = point_dist(pts, i, j);
                    if (dist <= threshold) E.push_back({dist, i, j});
                }
        }
        const auto tm1 = std::chrono::steady_clock::now();
        Result r = kruskal_h0(n, std::move(E));
        r.counters.metric_ms = std::chrono::duration<double, std::milli>(tm1 - tm0).count();
        return r;
    }
    // I240: spatial UF then per-component matrices. Never allocate n×n
    // when G_T has several blocks (real clustered clouds).
    const auto tm0 = std::chrono::steady_clock::now();
    std::vector<std::vector<int>> comps;
    if (spatial_components(pts, threshold, comps) && comps.size() > 1) {
        const auto tm1 = std::chrono::steady_clock::now();
        Result r = finish_redzed_from_points(pts, std::move(comps), maxdim, threshold);
        r.counters.metric_ms = std::chrono::duration<double, std::milli>(tm1 - tm0).count();
        return r;
    }

    const int dim = maxdim;
    const int d = static_cast<int>(pts[0].size());
    // I256: when the T-ball is a small fraction of the bbox, skip far
    // distances. Fill far entries with +∞, write only d≤T, pass a prebuilt
    // EdgeList. Dense clouds (π(T/L)²≥0.2) keep I238 parallel all-pairs.
    std::vector<SpatEdge> SE;
    bool spatial = false;
    if (std::isfinite(threshold) && threshold > 0 && d >= 2 && d <= 3 && n >= 256) {
        const double L = bbox_max_extent(pts);
        if (L > 0) {
            const double tL = static_cast<double>(threshold) / L;
            const double frac = (d == 2) ? (3.141592653589793 * tL * tL)
                                         : (4.188790204786391 * tL * tL * tL);
            if (frac < 0.20) spatial = spatial_edges(pts, threshold, SE);
        }
    }
    DistanceMatrix D;
    D.resize_lower(n);
    const auto tfill0 = std::chrono::steady_clock::now();
    if (spatial) {
        std::fill(D.mat.begin(), D.mat.end(), VINF);
        for (const SpatEdge& e : SE) {
            const int i = std::min(e.u, e.v), j = std::max(e.u, e.v);
            D.mat[DistanceMatrix::offset(i, j)] = e.t;
        }
    } else {
        const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
        auto fill_range = [&](int j0, int j1) {
            for (int j = j0; j < j1; ++j) {
                for (int i = 0; i < j; ++i) {
                    D.mat[DistanceMatrix::offset(i, j)] = point_dist(pts, i, j);
                }
            }
        };
        if (nth <= 1 || n < 64) {
            fill_range(1, n);
        } else {
            std::vector<std::thread> pool;
            pool.reserve(static_cast<size_t>(nth));
            const int span = (n - 1 + nth - 1) / nth;
            for (int t = 0; t < nth; ++t) {
                const int j0 = 1 + t * span;
                const int j1 = std::min(n, j0 + span);
                if (j0 >= j1) break;
                pool.emplace_back(fill_range, j0, j1);
            }
            for (auto& th : pool) th.join();
        }
    }
    const auto tfill1 = std::chrono::steady_clock::now();
    EdgeList pre;
    EdgeList* pre_ptr = nullptr;
    if (spatial) {
        BinomialTable bt(n, dim + 2);
        edgelist_from_spat(SE, threshold, bt, pre);
        pre_ptr = &pre;
    }
    const auto t0 = std::chrono::steady_clock::now();
    auto bars = redzed_vr(D, dim, threshold, pre_ptr);
    Result r;
    append_bars(r, bars, dim);
    const auto t1 = std::chrono::steady_clock::now();
    r.counters.n_vertices = n;
    r.counters.n_collapse_trims = 1;
    r.counters.n_distances = spatial ? static_cast<std::int64_t>(SE.size())
                                     : static_cast<std::int64_t>(n) * (n - 1) / 2;
    r.counters.metric_ms = std::chrono::duration<double, std::milli>(tfill1 - tfill0).count();
    r.counters.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    r.counters.pipeline = spatial ? "pith:redzed-spatial" : "pith:redzed-thr";
    return r;
}

}  // namespace pith
