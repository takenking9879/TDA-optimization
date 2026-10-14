// I228: translation unit that owns the vendored RedZeD driver.
// redzed.cpp is MIT and compiled with REDZED_NO_MAIN so only the library
// entry is visible. Do not edit third_party/redzed/redzed.cpp.

#define REDZED_NO_MAIN
#include "../../../third_party/redzed/redzed.cpp"

#include "pith/redzed_bridge.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <functional>
#include <iterator>
#include <new>
#include <numeric>
#include <thread>
#include <unordered_map>
#include <unordered_set>
#include <utility>
#include <vector>

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

// I258: sparse d≤T lookup. Miss → VINF so a leaked far-read cannot
// invent a diameter-0 edge. Dense keeps the DistanceMatrix.
// I259: open-address hash. I258's lower-tri CSR binary search taxed
// leftover-coface: low-id rows held every higher neighbor.
// I260: occupancy bitmap + malloc (no eager Slot zero).
// I261: load 0.5 again (I259 probe length) without tab.assign(16M).
struct SparseDist {
    struct Slot {
        uint64_t k;
        value_t v;
    };
    int n = 0;
    uint64_t mask = 0;
    Slot* tab = nullptr;
    std::vector<uint64_t> occ;

    SparseDist() = default;
    SparseDist(const SparseDist&) = delete;
    SparseDist& operator=(const SparseDist&) = delete;
    ~SparseDist() { std::free(tab); }

    bool taken(uint64_t h) const { return (occ[h >> 6] >> (h & 63)) & 1ull; }
    void mark(uint64_t h) { occ[h >> 6] |= 1ull << (h & 63); }

    static uint64_t pack(int i, int j) {
        if (i > j) std::swap(i, j);
        return (static_cast<uint64_t>(static_cast<uint32_t>(i)) << 32) |
               static_cast<uint32_t>(j);
    }
    static uint64_t mix(uint64_t x) {
        x ^= x >> 30;
        x *= 0xbf58476d1ce4e5b9ULL;
        x ^= x >> 27;
        x *= 0x94d049bb133111ebULL;
        x ^= x >> 31;
        return x;
    }
    value_t get(int i, int j) const {
        if (i == j) return 0;
        const uint64_t k = pack(i, j);
        uint64_t h = mix(k) & mask;
        const Slot* t = tab;
        for (;;) {
            if (!taken(h)) return VINF;
            if (t[h].k == k) return t[h].v;
            h = (h + 1) & mask;
        }
    }
};

static thread_local const SparseDist* g_sparse = nullptr;

static value_t face_diam_any(const int32_t* v, int m, int omit, const State& st) {
    value_t diam = 0;
    for (int a = 1; a <= m; ++a) {
        if (a == omit) continue;
        for (int b = a + 1; b <= m; ++b) {
            if (b == omit) continue;
            const value_t d = g_sparse ? g_sparse->get(v[a - 1], v[b - 1])
                                       : st.dist(v[a - 1], v[b - 1]);
            if (d > diam) diam = d;
        }
    }
    return diam;
}

static bool coface_ready_any(int32_t* cand, const int32_t* xverts, int m, int32_t w, comb_t xidx,
                             value_t xdiam, State& st) {
    const int total = m + 1;
    const int wpos = merge_vertex(cand, xverts, m, w);
    for (int omit = 1; omit <= total; ++omit) {
        if (omit == wpos) continue;
        const comb_t f = face_index_without(cand, total, omit, st.binom);
        if (f < xidx) continue;
        if (!(face_diam_any(cand, total, omit, st) < xdiam)) return false;
    }
    return true;
}

// Vendor has_leftover_coface always masks ~seenbits. On the 97% no-seed
// skip that mask is a no-op memory tax. Same coface_ready, same rbit AND.
// I253 coface_ready_h1 was exact but no pith cut (wave n=5000 0.36s was
// noise; standalone reduce 207≈I252 206 ms). Reverted.
// I255 unique-diam rbit-AND skip was exact 14/14 but no pith cut
// (n=5000 reduce 211 vs I252 206 ms). Reverted.
// I258: coface_ready_any so the spatial path can omit the C(n,2) matrix.
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
            if (coface_ready_any(cbuf, xv, 2, (int32_t)cand, xidx, r, st))
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
            if (coface_ready_any(cbuf, xverts, m, (int32_t)cand, xidx, r, st))
                return true;
        }
    }
    return false;
}

// Seeded leftover-coface: same as vendor has_leftover_coface but goes
// through coface_ready_any so a CSR spatial matrix is enough.
static bool has_leftover_coface_any(State& st, const int32_t* xverts, int m, comb_t xidx,
                                    value_t r) {
    if (!g_sparse) return has_leftover_coface(st, xverts, m, xidx, r);
    const uint64_t* rb = st.rbits.data();
    const int words = st.words, nv = st.nv;
    int wlo = 0, whi = words - 1;
    for (int i = 0; i < m; ++i) {
        const int v = xverts[i];
        if (st.rlo[v] > wlo) wlo = st.rlo[v];
        if (st.rhi[v] < whi) whi = st.rhi[v];
    }
    for (int w = wlo; w <= whi; ++w) {
        uint64_t acc = rb[(size_t)xverts[0] * words + w];
        if (!acc) continue;
        for (int i = 1; i < m; ++i) {
            acc &= rb[(size_t)xverts[i] * words + w];
            if (!acc) break;
        }
        if (!acc) continue;
        acc &= ~st.seenbits[w];
        while (acc) {
            const int bp = redzed_ctz64(acc);
            acc &= acc - 1;
            const int cand = w * 64 + bp;
            if (cand >= nv) break;
            if (coface_ready_any(st.coface_buf.data(), xverts, m, (int32_t)cand, xidx, r, st))
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
// I288 equal-set seeded_is_noop was exact 10/10 but figure8 n=4000 reduce
// 848≈866 ms — do not retry (I266 3% precedent).
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
        if (coface_ready_any(st.coface_buf.data(), verts, m, w, xidx, sdiam, st))
            dirty |= process_seeded(st, xslot, sdw, sdiam);
    }
    if (!dirty) {
        if (has_leftover_coface_any(st, verts, m, xidx, sdiam)) {
            Rn.erase(xrank);
            Rin.erase(xrank);
            return;
        }
        register_active(st, xrank, xslot, verts);
        return;
    }
    xslot = Rn.slot(xrank);
    if (xslot) {
        if (has_leftover_coface_any(st, verts, m, xidx, sdiam)) process_leftover(st, xslot, sdiam);
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

// I301: H2 triangle stream on a sparse 1-skeleton. Same growing-G_<e
// common-neighbor triangles as vendor generate_stream (d=2, need=1),
// but adj-list intersection instead of an n×n bit graph. Exact flag PH.
// Used when |E|≤16n (Delaunay flag). Do not use on dense G_T.
template <class F>
static void generate_stream_h2_adj(const EdgeList& edges, int nv, const BinomialTable& bt, F&& emit) {
    if (edges.count == 0 || nv <= 0) return;
    std::vector<std::vector<int>> adj(static_cast<size_t>(nv));
    for (auto& a : adj) a.reserve(16);
    auto add_undirected = [&](int u, int v) {
        auto ins = [](std::vector<int>& a, int x) {
            auto it = std::lower_bound(a.begin(), a.end(), x);
            if (it == a.end() || *it != x) a.insert(it, x);
        };
        ins(adj[static_cast<size_t>(u)], v);
        ins(adj[static_cast<size_t>(v)], u);
    };
    std::vector<comb_t> akey;
    std::vector<int32_t> avert;
    std::vector<uint32_t> ord;
    int32_t tri[3];
    const size_t E = edges.count;
    size_t i = 0;
    while (i < E) {
        const value_t r = edges.diam[i];
        size_t jend = i;
        while (jend < E && edges.diam[jend] == r) ++jend;
        const bool acc = (jend != i + 1);
        akey.clear();
        avert.clear();
        for (size_t k = i; k < jend; ++k) {
            const int u = edges.verts[2 * k];
            const int v = edges.verts[2 * k + 1];
            const auto& au = adj[static_cast<size_t>(u)];
            const auto& av = adj[static_cast<size_t>(v)];
            size_t p = 0, q = 0;
            while (p < au.size() && q < av.size()) {
                if (au[p] < av[q]) {
                    ++p;
                } else if (av[q] < au[p]) {
                    ++q;
                } else {
                    const int x = au[p];
                    ++p;
                    ++q;
                    if (x == u || x == v) continue;
                    tri[0] = u;
                    tri[1] = v;
                    tri[2] = x;
                    std::sort(tri, tri + 3);
                    if (acc) {
                        akey.push_back(comb_index(tri, 3, bt));
                        avert.insert(avert.end(), tri, tri + 3);
                    } else {
                        emit(r, tri);
                    }
                }
            }
            add_undirected(u, v);
        }
        if (acc && !akey.empty()) {
            const size_t c = akey.size();
            ord.resize(c);
            for (size_t t = 0; t < c; ++t) ord[t] = static_cast<uint32_t>(t);
            std::sort(ord.begin(), ord.end(), [&](uint32_t a, uint32_t b) { return akey[a] < akey[b]; });
            for (size_t t = 0; t < c; ++t) emit(r, &avert[static_cast<size_t>(ord[t]) * 3]);
        }
        i = jend;
    }
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
    // I257: empty prebuilt is a valid G_T (no d≤T edges). Do not fall
    // through to build_edges on a zero-initialized matrix — far 0s would
    // be read as diameter-0 edges.
    if (prebuilt) {
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

            auto emit_simp = [&](value_t sdiam, const int32_t* cv) {
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
            };
            // I301: sparse H2 uses adj intersection; dense / H≥3 keep vendor.
            if (d == 2 && st.edges.count <= static_cast<size_t>(nv) * 16) {
                generate_stream_h2_adj(st.edges, nv, st.binom, emit_simp);
            } else {
                // Vendor EdStream stores F*; a named lambda is an lvalue
                // and F becomes a reference (I267). Pass a temporary.
                generate_stream(st.edges, st.dist, d, st.binom,
                                [&](value_t sdiam, const int32_t* cv) { emit_simp(sdiam, cv); });
            }

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
// I257: grid is built once (read-only after), then the neighbor scan
// runs on a thread pool. Same (u,v,d) set as the sequential walk.
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
    const int z1 = (d == 3) ? 1 : 0;
    auto scan_i = [&](int i, std::vector<SpatEdge>& dest) {
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
                        if (dist <= T) dest.push_back({dist, i, j});
                    }
                }
    };
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    if (nth <= 1 || n < 256) {
        out.reserve(static_cast<size_t>(n) * 8);
        for (int i = 0; i < n; ++i) scan_i(i, out);
        return true;
    }
    std::vector<std::vector<SpatEdge>> local(static_cast<size_t>(nth));
    std::vector<std::thread> pool;
    pool.reserve(static_cast<size_t>(nth));
    const int span = (n + nth - 1) / nth;
    for (int t = 0; t < nth; ++t) {
        const int i0 = t * span;
        const int i1 = std::min(n, i0 + span);
        if (i0 >= i1) break;
        pool.emplace_back([&, i0, i1, t]() {
            auto& dest = local[static_cast<size_t>(t)];
            dest.reserve(static_cast<size_t>(i1 - i0) * 8);
            for (int i = i0; i < i1; ++i) scan_i(i, dest);
        });
    }
    for (auto& th : pool) th.join();
    size_t tot = 0;
    for (const auto& v : local) tot += v.size();
    out.reserve(tot);
    for (auto& v : local) {
        out.insert(out.end(), std::make_move_iterator(v.begin()), std::make_move_iterator(v.end()));
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

// I263: 250 evenly spaced points, |{d≤T}| / C(m,2). Cheap predictor
// of G_T density on hollow / manifold supports where π(T/L)^d over-
// estimates (tight bbox) or under-shoots the I256 volume gate.
// ~31k distances; not a collapse residual (see probe_residual_frac_points).
double probe_edge_frac_points(const std::vector<std::vector<value_t>>& pts, value_t T,
                             int sample) {
    const int n = static_cast<int>(pts.size());
    if (n < 8 || !(T > 0) || !std::isfinite(T)) return 1.0;
    const int s = std::min(sample, n);
    std::int64_t hits = 0;
    std::int64_t tot = 0;
    auto hit = [&](int i, int j) {
        ++tot;
        if (point_dist(pts, i, j) <= T) ++hits;
    };
    if (s == n) {
        for (int j = 1; j < n; ++j)
            for (int i = 0; i < j; ++i) hit(i, j);
    } else {
        std::vector<int> id(static_cast<size_t>(s));
        for (int i = 0; i < s; ++i)
            id[static_cast<size_t>(i)] =
                static_cast<int>((static_cast<std::int64_t>(i) * (n - 1)) / (s - 1));
        for (int j = 1; j < s; ++j)
            for (int i = 0; i < j; ++i) hit(id[static_cast<size_t>(i)], id[static_cast<size_t>(j)]);
    }
    return tot ? static_cast<double>(hits) / static_cast<double>(tot) : 1.0;
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

// I261: load 0.5, occupancy bitmap, malloc (untouched empty slots).
// Same pairs as SE. Occupied bit = present; miss → VINF.
static void spat_to_hash(const std::vector<SpatEdge>& se, int n, SparseDist& S) {
    S.n = n;
    std::free(S.tab);
    S.tab = nullptr;
    size_t cap = 1024;
    const size_t need = se.size() * 2 + 1;
    while (cap < need) cap <<= 1;
    S.tab = static_cast<SparseDist::Slot*>(std::malloc(cap * sizeof(SparseDist::Slot)));
    if (!S.tab) throw std::bad_alloc();
    S.occ.assign(cap / 64, 0);
    S.mask = cap - 1;
    for (const SpatEdge& e : se) {
        const uint64_t k = SparseDist::pack(e.u, e.v);
        uint64_t h = SparseDist::mix(k) & S.mask;
        while (S.taken(h)) h = (h + 1) & S.mask;
        S.tab[h].k = k;
        S.tab[h].v = e.t;
        S.mark(h);
    }
}

// I270: Euclidean MST ⊆ 2D Delaunay, so VR H0 is Kruskal on Delaunay
// edges with d≤T. Avoids listing G_T (blobs n=4000: 2.6M pairs).
// I271: walk-locate + cavity flood (expected O(n log n) incircle)
// instead of scanning every live triangle. Morton order shortens walks.
// Scan remains the n≤12000 fallback. n≥256, d=2.
static double delaunay_orient(double ax, double ay, double bx, double by, double cx, double cy) {
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax);
}

static bool delaunay_incircle(double ax, double ay, double bx, double by, double cx, double cy,
                              double dx, double dy) {
    const double adx = ax - dx, ady = ay - dy;
    const double bdx = bx - dx, bdy = by - dy;
    const double cdx = cx - dx, cdy = cy - dy;
    const double ad2 = adx * adx + ady * ady;
    const double bd2 = bdx * bdx + bdy * bdy;
    const double cd2 = cdx * cdx + cdy * cdy;
    const double det = adx * (bdy * cd2 - bd2 * cdy) - ady * (bdx * cd2 - bd2 * cdx) +
                       ad2 * (bdx * cdy - bdy * cdx);
    return det > 0.0;
}

static uint32_t delaunay_morton_part(uint32_t n) {
    n &= 0x0000ffffu;
    n = (n | (n << 8)) & 0x00ff00ffu;
    n = (n | (n << 4)) & 0x0f0f0f0fu;
    n = (n | (n << 2)) & 0x33333333u;
    n = (n | (n << 1)) & 0x55555555u;
    return n;
}

static bool delaunay_edges_2d_scan(const std::vector<std::vector<value_t>>& pts,
                                   std::vector<SpatEdge>& out) {
    const int n = static_cast<int>(pts.size());
    if (n < 3 || static_cast<int>(pts[0].size()) != 2) return false;
    std::vector<double> xs(static_cast<size_t>(n) + 3), ys(static_cast<size_t>(n) + 3);
    double xmin = static_cast<double>(pts[0][0]), xmax = xmin;
    double ymin = static_cast<double>(pts[0][1]), ymax = ymin;
    for (int i = 0; i < n; ++i) {
        xs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][0]);
        ys[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][1]);
        if (xs[static_cast<size_t>(i)] < xmin) xmin = xs[static_cast<size_t>(i)];
        if (xs[static_cast<size_t>(i)] > xmax) xmax = xs[static_cast<size_t>(i)];
        if (ys[static_cast<size_t>(i)] < ymin) ymin = ys[static_cast<size_t>(i)];
        if (ys[static_cast<size_t>(i)] > ymax) ymax = ys[static_cast<size_t>(i)];
    }
    const double dx = std::max(xmax - xmin, 1e-9);
    const double dy = std::max(ymax - ymin, 1e-9);
    const double mid_x = 0.5 * (xmin + xmax);
    const double mid_y = 0.5 * (ymin + ymax);
    const double span = 20.0 * (dx + dy);
    xs[static_cast<size_t>(n)] = mid_x - span;
    ys[static_cast<size_t>(n)] = mid_y - span;
    xs[static_cast<size_t>(n) + 1] = mid_x + span;
    ys[static_cast<size_t>(n) + 1] = mid_y - span;
    xs[static_cast<size_t>(n) + 2] = mid_x;
    ys[static_cast<size_t>(n) + 2] = mid_y + span;
    if (delaunay_orient(xs[static_cast<size_t>(n)], ys[static_cast<size_t>(n)],
                        xs[static_cast<size_t>(n) + 1], ys[static_cast<size_t>(n) + 1],
                        xs[static_cast<size_t>(n) + 2], ys[static_cast<size_t>(n) + 2]) <= 0.0)
        return false;

    struct Tri {
        int v[3];
        bool live;
    };
    std::vector<Tri> tris;
    tris.push_back({{n, n + 1, n + 2}, true});

    auto add_edge = [](std::unordered_map<uint64_t, int>& cnt, std::unordered_map<uint64_t, std::pair<int, int>>& dir,
                       int a, int b) {
        const int lo = std::min(a, b), hi = std::max(a, b);
        const uint64_t key = (static_cast<uint64_t>(static_cast<uint32_t>(lo)) << 32) |
                             static_cast<uint32_t>(hi);
        cnt[key] += 1;
        if (dir.find(key) == dir.end()) dir[key] = {a, b};
    };

    for (int p = 0; p < n; ++p) {
        const double px = xs[static_cast<size_t>(p)], py = ys[static_cast<size_t>(p)];
        std::vector<int> bad;
        for (int t = 0; t < static_cast<int>(tris.size()); ++t) {
            if (!tris[static_cast<size_t>(t)].live) continue;
            const int* v = tris[static_cast<size_t>(t)].v;
            const double o = delaunay_orient(xs[static_cast<size_t>(v[0])], ys[static_cast<size_t>(v[0])],
                                             xs[static_cast<size_t>(v[1])], ys[static_cast<size_t>(v[1])],
                                             xs[static_cast<size_t>(v[2])], ys[static_cast<size_t>(v[2])]);
            if (o <= 0.0) continue;
            if (delaunay_incircle(xs[static_cast<size_t>(v[0])], ys[static_cast<size_t>(v[0])],
                                  xs[static_cast<size_t>(v[1])], ys[static_cast<size_t>(v[1])],
                                  xs[static_cast<size_t>(v[2])], ys[static_cast<size_t>(v[2])], px, py))
                bad.push_back(t);
        }
        if (bad.empty()) return false;
        std::unordered_map<uint64_t, int> ecnt;
        std::unordered_map<uint64_t, std::pair<int, int>> edir;
        ecnt.reserve(bad.size() * 3);
        for (int t : bad) {
            tris[static_cast<size_t>(t)].live = false;
            const int* v = tris[static_cast<size_t>(t)].v;
            add_edge(ecnt, edir, v[0], v[1]);
            add_edge(ecnt, edir, v[1], v[2]);
            add_edge(ecnt, edir, v[2], v[0]);
        }
        for (const auto& kv : ecnt) {
            if (kv.second != 1) continue;
            const auto ab = edir[kv.first];
            int a = ab.first, b = ab.second;
            if (delaunay_orient(xs[static_cast<size_t>(a)], ys[static_cast<size_t>(a)],
                                xs[static_cast<size_t>(b)], ys[static_cast<size_t>(b)], px, py) <= 0.0)
                std::swap(a, b);
            tris.push_back({{a, b, p}, true});
        }
    }

    std::unordered_set<uint64_t> seen;
    seen.reserve(static_cast<size_t>(n) * 6);
    out.clear();
    out.reserve(static_cast<size_t>(n) * 3);
    for (const Tri& tr : tris) {
        if (!tr.live) continue;
        const int v[3] = {tr.v[0], tr.v[1], tr.v[2]};
        for (int e = 0; e < 3; ++e) {
            int a = v[e], b = v[(e + 1) % 3];
            if (a >= n || b >= n) continue;
            if (a > b) std::swap(a, b);
            const uint64_t key = (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
                                 static_cast<uint32_t>(b);
            if (!seen.insert(key).second) continue;
            out.push_back({point_dist(pts, a, b), a, b});
        }
    }
    return out.size() >= static_cast<size_t>(n - 1);
}

// I271: incremental Bowyer–Watson with Lawson walk + adjacency flood.
// Same Delaunay edges as the scan (unique in general position). Expected
// O(n log n) incircle tests; Morton order keeps walks local.
static bool delaunay_edges_2d_walk(const std::vector<std::vector<value_t>>& pts,
                                   std::vector<SpatEdge>& out) {
    const int n = static_cast<int>(pts.size());
    if (n < 3 || static_cast<int>(pts[0].size()) != 2) return false;
    std::vector<double> xs(static_cast<size_t>(n) + 3), ys(static_cast<size_t>(n) + 3);
    double xmin = static_cast<double>(pts[0][0]), xmax = xmin;
    double ymin = static_cast<double>(pts[0][1]), ymax = ymin;
    for (int i = 0; i < n; ++i) {
        xs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][0]);
        ys[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][1]);
        if (xs[static_cast<size_t>(i)] < xmin) xmin = xs[static_cast<size_t>(i)];
        if (xs[static_cast<size_t>(i)] > xmax) xmax = xs[static_cast<size_t>(i)];
        if (ys[static_cast<size_t>(i)] < ymin) ymin = ys[static_cast<size_t>(i)];
        if (ys[static_cast<size_t>(i)] > ymax) ymax = ys[static_cast<size_t>(i)];
    }
    const double dx = std::max(xmax - xmin, 1e-9);
    const double dy = std::max(ymax - ymin, 1e-9);
    const double mid_x = 0.5 * (xmin + xmax);
    const double mid_y = 0.5 * (ymin + ymax);
    const double span = 20.0 * (dx + dy);
    xs[static_cast<size_t>(n)] = mid_x - span;
    ys[static_cast<size_t>(n)] = mid_y - span;
    xs[static_cast<size_t>(n) + 1] = mid_x + span;
    ys[static_cast<size_t>(n) + 1] = mid_y - span;
    xs[static_cast<size_t>(n) + 2] = mid_x;
    ys[static_cast<size_t>(n) + 2] = mid_y + span;
    if (delaunay_orient(xs[static_cast<size_t>(n)], ys[static_cast<size_t>(n)],
                        xs[static_cast<size_t>(n) + 1], ys[static_cast<size_t>(n) + 1],
                        xs[static_cast<size_t>(n) + 2], ys[static_cast<size_t>(n) + 2]) <= 0.0)
        return false;

    struct Tri {
        int v[3];
        int nbor[3];
    };
    std::vector<Tri> tris;
    std::vector<int> stamp;
    tris.push_back({{n, n + 1, n + 2}, {-1, -1, -1}});
    stamp.push_back(0);
    int gen = 1;

    auto orient_v = [&](int a, int b, int c) {
        return delaunay_orient(xs[static_cast<size_t>(a)], ys[static_cast<size_t>(a)],
                               xs[static_cast<size_t>(b)], ys[static_cast<size_t>(b)],
                               xs[static_cast<size_t>(c)], ys[static_cast<size_t>(c)]);
    };
    auto incircle_t = [&](int t, double px, double py) {
        const int* v = tris[static_cast<size_t>(t)].v;
        return delaunay_incircle(xs[static_cast<size_t>(v[0])], ys[static_cast<size_t>(v[0])],
                                 xs[static_cast<size_t>(v[1])], ys[static_cast<size_t>(v[1])],
                                 xs[static_cast<size_t>(v[2])], ys[static_cast<size_t>(v[2])], px, py);
    };
    auto walk = [&](int hint, double px, double py) -> int {
        int t = hint;
        const int guard = n * 4 + 32;
        for (int step = 0; step < guard; ++step) {
            const Tri& tr = tris[static_cast<size_t>(t)];
            bool moved = false;
            for (int i = 0; i < 3; ++i) {
                const int a = tr.v[i], b = tr.v[(i + 1) % 3];
                if (delaunay_orient(xs[static_cast<size_t>(a)], ys[static_cast<size_t>(a)],
                                    xs[static_cast<size_t>(b)], ys[static_cast<size_t>(b)], px, py) <
                    0.0) {
                    const int nb = tr.nbor[i];
                    if (nb < 0) return -1;
                    t = nb;
                    moved = true;
                    break;
                }
            }
            if (!moved) return t;
        }
        return -1;
    };

    std::vector<int> order(static_cast<size_t>(n));
    std::iota(order.begin(), order.end(), 0);
    {
        std::vector<uint32_t> code(static_cast<size_t>(n));
        const double invx = 65535.0 / dx, invy = 65535.0 / dy;
        for (int i = 0; i < n; ++i) {
            const uint32_t qx = static_cast<uint32_t>(
                std::lround(std::min(65535.0, std::max(0.0, (xs[static_cast<size_t>(i)] - xmin) * invx))));
            const uint32_t qy = static_cast<uint32_t>(
                std::lround(std::min(65535.0, std::max(0.0, (ys[static_cast<size_t>(i)] - ymin) * invy))));
            code[static_cast<size_t>(i)] = delaunay_morton_part(qx) | (delaunay_morton_part(qy) << 1);
        }
        std::sort(order.begin(), order.end(),
                  [&](int a, int b) { return code[static_cast<size_t>(a)] < code[static_cast<size_t>(b)]; });
    }

    std::vector<SpatEdge> extra;
    int hint = 0;
    std::vector<int> cavity, q, newids;
    cavity.reserve(16);
    q.reserve(16);
    struct BEdge {
        int a, b, outer, oedge;
    };
    std::vector<BEdge> bedges;
    bedges.reserve(16);
    std::unordered_map<uint64_t, std::pair<int, int>> pending;
    pending.reserve(32);

    for (int pi = 0; pi < n; ++pi) {
        const int p = order[static_cast<size_t>(pi)];
        const double px = xs[static_cast<size_t>(p)], py = ys[static_cast<size_t>(p)];
        const int t0 = walk(hint, px, py);
        if (t0 < 0) return false;
        if (!incircle_t(t0, px, py)) {
            const int* v = tris[static_cast<size_t>(t0)].v;
            int best = -1;
            double best2 = 1e300;
            for (int k = 0; k < 3; ++k) {
                if (v[k] >= n) continue;
                const double ddx = xs[static_cast<size_t>(v[k])] - px;
                const double ddy = ys[static_cast<size_t>(v[k])] - py;
                const double d2 = ddx * ddx + ddy * ddy;
                if (d2 < best2) {
                    best2 = d2;
                    best = v[k];
                }
            }
            if (best >= 0) extra.push_back({point_dist(pts, p, best), std::min(p, best), std::max(p, best)});
            continue;
        }
        ++gen;
        if (gen == 0x7fffffff) {
            std::fill(stamp.begin(), stamp.end(), 0);
            gen = 1;
        }
        cavity.clear();
        q.clear();
        q.push_back(t0);
        stamp[static_cast<size_t>(t0)] = gen;
        cavity.push_back(t0);
        for (size_t qi = 0; qi < q.size(); ++qi) {
            const int t = q[qi];
            for (int i = 0; i < 3; ++i) {
                const int nb = tris[static_cast<size_t>(t)].nbor[i];
                if (nb < 0 || stamp[static_cast<size_t>(nb)] == gen) continue;
                if (!incircle_t(nb, px, py)) continue;
                stamp[static_cast<size_t>(nb)] = gen;
                q.push_back(nb);
                cavity.push_back(nb);
            }
        }
        bedges.clear();
        for (int t : cavity) {
            for (int i = 0; i < 3; ++i) {
                const int nb = tris[static_cast<size_t>(t)].nbor[i];
                if (nb >= 0 && stamp[static_cast<size_t>(nb)] == gen) continue;
                int oedge = -1;
                if (nb >= 0) {
                    for (int k = 0; k < 3; ++k)
                        if (tris[static_cast<size_t>(nb)].nbor[k] == t) {
                            oedge = k;
                            break;
                        }
                    if (oedge < 0) return false;
                }
                bedges.push_back({tris[static_cast<size_t>(t)].v[i], tris[static_cast<size_t>(t)].v[(i + 1) % 3],
                                  nb, oedge});
            }
        }
        if (bedges.size() != cavity.size() + 2) return false;

        newids.clear();
        newids.reserve(bedges.size());
        for (size_t i = 0; i < bedges.size(); ++i) {
            int id;
            if (i < cavity.size()) {
                id = cavity[i];
            } else {
                id = static_cast<int>(tris.size());
                tris.push_back({{0, 0, 0}, {-1, -1, -1}});
                stamp.push_back(0);
            }
            newids.push_back(id);
        }
        pending.clear();
        auto ek = [](int u, int v) -> uint64_t {
            if (u > v) std::swap(u, v);
            return (static_cast<uint64_t>(static_cast<uint32_t>(u)) << 32) | static_cast<uint32_t>(v);
        };
        auto link = [&](int t, int eidx, int u, int v) {
            const uint64_t k = ek(u, v);
            const auto it = pending.find(k);
            if (it == pending.end()) {
                pending.emplace(k, std::pair<int, int>{t, eidx});
                return true;
            }
            const int t2 = it->second.first, e2 = it->second.second;
            tris[static_cast<size_t>(t)].nbor[eidx] = t2;
            tris[static_cast<size_t>(t2)].nbor[e2] = t;
            pending.erase(it);
            return true;
        };
        for (size_t i = 0; i < bedges.size(); ++i) {
            int a = bedges[i].a, b = bedges[i].b;
            if (orient_v(a, b, p) <= 0.0) std::swap(a, b);
            const int id = newids[i];
            tris[static_cast<size_t>(id)].v[0] = a;
            tris[static_cast<size_t>(id)].v[1] = b;
            tris[static_cast<size_t>(id)].v[2] = p;
            tris[static_cast<size_t>(id)].nbor[0] = bedges[i].outer;
            tris[static_cast<size_t>(id)].nbor[1] = -1;
            tris[static_cast<size_t>(id)].nbor[2] = -1;
            if (bedges[i].outer >= 0) {
                int oe = bedges[i].oedge;
                if (oe < 0) return false;
                // Boundary was collected as the cavity's (a,b). After a possible
                // swap the outer still adjoins the same undirected edge.
                const int ov0 = tris[static_cast<size_t>(bedges[i].outer)].v[oe];
                const int ov1 = tris[static_cast<size_t>(bedges[i].outer)].v[(oe + 1) % 3];
                const int lo0 = std::min(a, b), hi0 = std::max(a, b);
                const int lo1 = std::min(ov0, ov1), hi1 = std::max(ov0, ov1);
                if (lo0 != lo1 || hi0 != hi1) {
                    oe = -1;
                    for (int k = 0; k < 3; ++k) {
                        const int xa = tris[static_cast<size_t>(bedges[i].outer)].v[k];
                        const int xb = tris[static_cast<size_t>(bedges[i].outer)].v[(k + 1) % 3];
                        if (std::min(xa, xb) == lo0 && std::max(xa, xb) == hi0) {
                            oe = k;
                            break;
                        }
                    }
                    if (oe < 0) return false;
                }
                tris[static_cast<size_t>(bedges[i].outer)].nbor[oe] = id;
            }
            if (!link(id, 1, b, p) || !link(id, 2, p, a)) return false;
        }
        if (!pending.empty()) return false;
        hint = newids[0];
    }

    std::unordered_set<uint64_t> seen;
    seen.reserve(static_cast<size_t>(n) * 6);
    out.clear();
    out.reserve(static_cast<size_t>(n) * 3 + extra.size());
    for (const Tri& tr : tris) {
        const int v[3] = {tr.v[0], tr.v[1], tr.v[2]};
        for (int e = 0; e < 3; ++e) {
            int a = v[e], b = v[(e + 1) % 3];
            if (a >= n || b >= n) continue;
            if (a > b) std::swap(a, b);
            const uint64_t key = (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
                                 static_cast<uint32_t>(b);
            if (!seen.insert(key).second) continue;
            out.push_back({point_dist(pts, a, b), a, b});
        }
    }
    for (const SpatEdge& e : extra)
        if (seen.insert((static_cast<uint64_t>(static_cast<uint32_t>(e.u)) << 32) |
                        static_cast<uint32_t>(e.v))
                .second)
            out.push_back(e);
    return out.size() >= static_cast<size_t>(n - 1);
}

static bool delaunay_edges_2d(const std::vector<std::vector<value_t>>& pts,
                              std::vector<SpatEdge>& out) {
    if (delaunay_edges_2d_walk(pts, out)) return true;
    const int n = static_cast<int>(pts.size());
    if (n <= 12000) return delaunay_edges_2d_scan(pts, out);
    return false;
}

// I274/I275: Euclidean MST ⊆ 3D Delaunay. Walk-locate + circumsphere flood.
// Same H0 identity as I271 in the plane. Fall back to spatial Kruskal.
static double delaunay_orient3(double ax, double ay, double az, double bx, double by, double bz,
                               double cx, double cy, double cz, double dx, double dy, double dz) {
    const double adx = ax - dx, ady = ay - dy, adz = az - dz;
    const double bdx = bx - dx, bdy = by - dy, bdz = bz - dz;
    const double cdx = cx - dx, cdy = cy - dy, cdz = cz - dz;
    return adx * (bdy * cdz - bdz * cdy) - ady * (bdx * cdz - bdz * cdx) +
           adz * (bdx * cdy - bdy * cdx);
}

static bool delaunay_insphere(double ax, double ay, double az, double bx, double by, double bz,
                              double cx, double cy, double cz, double dx, double dy, double dz,
                              double px, double py, double pz) {
    const double aex = ax - px, aey = ay - py, aez = az - pz;
    const double bex = bx - px, bey = by - py, bez = bz - pz;
    const double cex = cx - px, cey = cy - py, cez = cz - pz;
    const double dex = dx - px, dey = dy - py, dez = dz - pz;
    const double ae2 = aex * aex + aey * aey + aez * aez;
    const double be2 = bex * bex + bey * bey + bez * bez;
    const double ce2 = cex * cex + cey * cey + cez * cez;
    const double de2 = dex * dex + dey * dey + dez * dez;
    const double det =
        aex * (bey * (cez * de2 - ce2 * dez) - bez * (cey * de2 - ce2 * dey) + be2 * (cey * dez - cez * dey)) -
        aey * (bex * (cez * de2 - ce2 * dez) - bez * (cex * de2 - ce2 * dex) + be2 * (cex * dez - cez * dex)) +
        aez * (bex * (cey * de2 - ce2 * dey) - bey * (cex * de2 - ce2 * dex) + be2 * (cex * dey - cey * dex)) -
        ae2 * (bex * (cey * dez - cez * dey) - bey * (cex * dez - cez * dex) + bez * (cex * dey - cey * dex));
    const double o = delaunay_orient3(ax, ay, az, bx, by, bz, cx, cy, cz, dx, dy, dz);
    return det * o > 0.0;
}

static uint32_t delaunay_morton3(uint32_t x, uint32_t y, uint32_t z) {
    auto part = [](uint32_t n) {
        n &= 0x3ffu;
        n = (n | (n << 16)) & 0x030000FFu;
        n = (n | (n << 8)) & 0x0300F00Fu;
        n = (n | (n << 4)) & 0x030C30C3u;
        n = (n | (n << 2)) & 0x09249249u;
        return n;
    };
    return part(x) | (part(y) << 1) | (part(z) << 2);
}

static uint64_t tet_face_key(int a, int b, int c) {
    if (a > b) std::swap(a, b);
    if (b > c) std::swap(b, c);
    if (a > b) std::swap(a, b);
    return (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 42) |
           (static_cast<uint64_t>(static_cast<uint32_t>(b)) << 21) | static_cast<uint32_t>(c);
}

// I275: incremental Bowyer–Watson, no cavity-slot reuse. I274 walk fell
// off the mesh (nbor=-1 at Morton p=183) because a reused index is a
// different tet than the live outers still point at. Dead tets stay
// dead; walk only follows live neighbors. If walk returns -1, scan
// live tets for containment (p on the same side of each face as the
// opposite vertex) and flood from there.
static bool delaunay_edges_3d_walk(const std::vector<std::vector<value_t>>& pts,
                                   std::vector<SpatEdge>& out) {
    const int n = static_cast<int>(pts.size());
    if (n < 4 || static_cast<int>(pts[0].size()) != 3) return false;
    std::vector<double> xs(static_cast<size_t>(n) + 4), ys(static_cast<size_t>(n) + 4),
        zs(static_cast<size_t>(n) + 4);
    double xmin = static_cast<double>(pts[0][0]), xmax = xmin;
    double ymin = static_cast<double>(pts[0][1]), ymax = ymin;
    double zmin = static_cast<double>(pts[0][2]), zmax = zmin;
    for (int i = 0; i < n; ++i) {
        xs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][0]);
        ys[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][1]);
        zs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][2]);
        xmin = std::min(xmin, xs[static_cast<size_t>(i)]);
        xmax = std::max(xmax, xs[static_cast<size_t>(i)]);
        ymin = std::min(ymin, ys[static_cast<size_t>(i)]);
        ymax = std::max(ymax, ys[static_cast<size_t>(i)]);
        zmin = std::min(zmin, zs[static_cast<size_t>(i)]);
        zmax = std::max(zmax, zs[static_cast<size_t>(i)]);
    }
    const double dx = std::max(xmax - xmin, 1e-9);
    const double dy = std::max(ymax - ymin, 1e-9);
    const double dz = std::max(zmax - zmin, 1e-9);
    const double mid_x = 0.5 * (xmin + xmax), mid_y = 0.5 * (ymin + ymax),
                 mid_z = 0.5 * (zmin + zmax);
    const double span = 30.0 * (dx + dy + dz);
    xs[static_cast<size_t>(n)] = mid_x - span;
    ys[static_cast<size_t>(n)] = mid_y - span;
    zs[static_cast<size_t>(n)] = mid_z - span;
    xs[static_cast<size_t>(n) + 1] = mid_x + span;
    ys[static_cast<size_t>(n) + 1] = mid_y - span;
    zs[static_cast<size_t>(n) + 1] = mid_z - span;
    xs[static_cast<size_t>(n) + 2] = mid_x;
    ys[static_cast<size_t>(n) + 2] = mid_y + span;
    zs[static_cast<size_t>(n) + 2] = mid_z - span;
    xs[static_cast<size_t>(n) + 3] = mid_x;
    ys[static_cast<size_t>(n) + 3] = mid_y;
    zs[static_cast<size_t>(n) + 3] = mid_z + span;
    auto o3 = [&](int a, int b, int c, int d) {
        return delaunay_orient3(xs[static_cast<size_t>(a)], ys[static_cast<size_t>(a)], zs[static_cast<size_t>(a)],
                                xs[static_cast<size_t>(b)], ys[static_cast<size_t>(b)], zs[static_cast<size_t>(b)],
                                xs[static_cast<size_t>(c)], ys[static_cast<size_t>(c)], zs[static_cast<size_t>(c)],
                                xs[static_cast<size_t>(d)], ys[static_cast<size_t>(d)], zs[static_cast<size_t>(d)]);
    };
    if (o3(n, n + 1, n + 2, n + 3) <= 0.0) {
        std::swap(xs[static_cast<size_t>(n) + 2], xs[static_cast<size_t>(n) + 3]);
        std::swap(ys[static_cast<size_t>(n) + 2], ys[static_cast<size_t>(n) + 3]);
        std::swap(zs[static_cast<size_t>(n) + 2], zs[static_cast<size_t>(n) + 3]);
    }
    if (o3(n, n + 1, n + 2, n + 3) <= 0.0) return false;

    struct Tet {
        int v[4];
        int nbor[4];
        bool live;
    };
    std::vector<Tet> tets;
    std::vector<int> stamp;
    tets.reserve(static_cast<size_t>(n) * 8 + 8);
    stamp.reserve(static_cast<size_t>(n) * 8 + 8);
    tets.push_back({{n, n + 1, n + 2, n + 3}, {-1, -1, -1, -1}, true});
    stamp.push_back(0);
    int gen = 1;

    auto face_opp = [](const int* v, int i, int f[3]) {
        int k = 0;
        for (int j = 0; j < 4; ++j)
            if (j != i) f[k++] = v[j];
    };
    auto live = [&](int t) {
        return t >= 0 && t < static_cast<int>(tets.size()) && tets[static_cast<size_t>(t)].live;
    };
    auto insphere_t = [&](int t, double px, double py, double pz) {
        const int* v = tets[static_cast<size_t>(t)].v;
        return delaunay_insphere(xs[static_cast<size_t>(v[0])], ys[static_cast<size_t>(v[0])],
                                 zs[static_cast<size_t>(v[0])], xs[static_cast<size_t>(v[1])],
                                 ys[static_cast<size_t>(v[1])], zs[static_cast<size_t>(v[1])],
                                 xs[static_cast<size_t>(v[2])], ys[static_cast<size_t>(v[2])],
                                 zs[static_cast<size_t>(v[2])], xs[static_cast<size_t>(v[3])],
                                 ys[static_cast<size_t>(v[3])], zs[static_cast<size_t>(v[3])], px, py, pz);
    };
    auto contains = [&](int t, double px, double py, double pz) {
        if (!live(t)) return false;
        const Tet& tr = tets[static_cast<size_t>(t)];
        for (int i = 0; i < 4; ++i) {
            int f[3];
            face_opp(tr.v, i, f);
            const double ov = delaunay_orient3(
                xs[static_cast<size_t>(f[0])], ys[static_cast<size_t>(f[0])], zs[static_cast<size_t>(f[0])],
                xs[static_cast<size_t>(f[1])], ys[static_cast<size_t>(f[1])], zs[static_cast<size_t>(f[1])],
                xs[static_cast<size_t>(f[2])], ys[static_cast<size_t>(f[2])], zs[static_cast<size_t>(f[2])],
                xs[static_cast<size_t>(tr.v[i])], ys[static_cast<size_t>(tr.v[i])],
                zs[static_cast<size_t>(tr.v[i])]);
            double op = delaunay_orient3(
                xs[static_cast<size_t>(f[0])], ys[static_cast<size_t>(f[0])], zs[static_cast<size_t>(f[0])],
                xs[static_cast<size_t>(f[1])], ys[static_cast<size_t>(f[1])], zs[static_cast<size_t>(f[1])],
                xs[static_cast<size_t>(f[2])], ys[static_cast<size_t>(f[2])], zs[static_cast<size_t>(f[2])],
                px, py, pz);
            if (ov < 0.0) op = -op;
            if (op < 0.0) return false;
        }
        return true;
    };
    auto locate_scan = [&](double px, double py, double pz) -> int {
        for (int t = 0; t < static_cast<int>(tets.size()); ++t)
            if (contains(t, px, py, pz)) return t;
        return -1;
    };
    auto walk = [&](int hint, double px, double py, double pz) -> int {
        int t = hint;
        if (!live(t)) t = locate_scan(px, py, pz);
        if (t < 0) return -1;
        const int guard = n * 8 + 64;
        for (int step = 0; step < guard; ++step) {
            if (!live(t)) return locate_scan(px, py, pz);
            const Tet& tr = tets[static_cast<size_t>(t)];
            bool moved = false;
            bool hole = false;
            for (int i = 0; i < 4; ++i) {
                int f[3];
                face_opp(tr.v, i, f);
                const double ov = delaunay_orient3(
                    xs[static_cast<size_t>(f[0])], ys[static_cast<size_t>(f[0])], zs[static_cast<size_t>(f[0])],
                    xs[static_cast<size_t>(f[1])], ys[static_cast<size_t>(f[1])], zs[static_cast<size_t>(f[1])],
                    xs[static_cast<size_t>(f[2])], ys[static_cast<size_t>(f[2])], zs[static_cast<size_t>(f[2])],
                    xs[static_cast<size_t>(tr.v[i])], ys[static_cast<size_t>(tr.v[i])],
                    zs[static_cast<size_t>(tr.v[i])]);
                double op = delaunay_orient3(
                    xs[static_cast<size_t>(f[0])], ys[static_cast<size_t>(f[0])], zs[static_cast<size_t>(f[0])],
                    xs[static_cast<size_t>(f[1])], ys[static_cast<size_t>(f[1])], zs[static_cast<size_t>(f[1])],
                    xs[static_cast<size_t>(f[2])], ys[static_cast<size_t>(f[2])], zs[static_cast<size_t>(f[2])],
                    px, py, pz);
                if (ov < 0.0) op = -op;
                if (op < 0.0) {
                    const int nb = tr.nbor[i];
                    if (live(nb)) {
                        t = nb;
                        moved = true;
                        break;
                    }
                    hole = true;
                }
            }
            if (!moved) return hole ? locate_scan(px, py, pz) : t;
        }
        return locate_scan(px, py, pz);
    };

    std::vector<int> order(static_cast<size_t>(n));
    std::iota(order.begin(), order.end(), 0);
    {
        std::vector<uint32_t> code(static_cast<size_t>(n));
        const double invx = 1023.0 / dx, invy = 1023.0 / dy, invz = 1023.0 / dz;
        for (int i = 0; i < n; ++i) {
            const uint32_t qx = static_cast<uint32_t>(
                std::lround(std::min(1023.0, std::max(0.0, (xs[static_cast<size_t>(i)] - xmin) * invx))));
            const uint32_t qy = static_cast<uint32_t>(
                std::lround(std::min(1023.0, std::max(0.0, (ys[static_cast<size_t>(i)] - ymin) * invy))));
            const uint32_t qz = static_cast<uint32_t>(
                std::lround(std::min(1023.0, std::max(0.0, (zs[static_cast<size_t>(i)] - zmin) * invz))));
            code[static_cast<size_t>(i)] = delaunay_morton3(qx, qy, qz);
        }
        std::sort(order.begin(), order.end(),
                  [&](int a, int b) { return code[static_cast<size_t>(a)] < code[static_cast<size_t>(b)]; });
    }

    std::vector<SpatEdge> extra;
    int hint = 0;
    std::vector<int> cavity, q, newids;
    cavity.reserve(32);
    q.reserve(32);
    struct BFace {
        int a, b, c, outer, oface;
    };
    std::vector<BFace> bfaces;
    bfaces.reserve(32);
    std::unordered_map<uint64_t, std::pair<int, int>> pending;
    pending.reserve(64);

    for (int pi = 0; pi < n; ++pi) {
        const int p = order[static_cast<size_t>(pi)];
        const double px = xs[static_cast<size_t>(p)], py = ys[static_cast<size_t>(p)],
                     pz = zs[static_cast<size_t>(p)];
        int t0 = walk(hint, px, py, pz);
        if (t0 < 0 || !contains(t0, px, py, pz)) t0 = locate_scan(px, py, pz);
        if (t0 < 0) return false;
        {
            const int* v = tets[static_cast<size_t>(t0)].v;
            int best = -1;
            double best2 = 1e300;
            for (int k = 0; k < 4; ++k) {
                if (v[k] >= n) continue;
                const double ddx = xs[static_cast<size_t>(v[k])] - px;
                const double ddy = ys[static_cast<size_t>(v[k])] - py;
                const double ddz = zs[static_cast<size_t>(v[k])] - pz;
                const double d2 = ddx * ddx + ddy * ddy + ddz * ddz;
                if (d2 < best2) {
                    best2 = d2;
                    best = v[k];
                }
            }
            if (best >= 0 && (best2 < 1e-24 || !insphere_t(t0, px, py, pz))) {
                extra.push_back({point_dist(pts, p, best), std::min(p, best), std::max(p, best)});
                continue;
            }
        }
        ++gen;
        if (gen == 0x7fffffff) {
            std::fill(stamp.begin(), stamp.end(), 0);
            gen = 1;
        }
        cavity.clear();
        q.clear();
        q.push_back(t0);
        stamp[static_cast<size_t>(t0)] = gen;
        cavity.push_back(t0);
        for (size_t qi = 0; qi < q.size(); ++qi) {
            const int t = q[qi];
            for (int i = 0; i < 4; ++i) {
                const int nb = tets[static_cast<size_t>(t)].nbor[i];
                if (!live(nb) || stamp[static_cast<size_t>(nb)] == gen) continue;
                if (!insphere_t(nb, px, py, pz)) continue;
                stamp[static_cast<size_t>(nb)] = gen;
                q.push_back(nb);
                cavity.push_back(nb);
            }
        }
        bfaces.clear();
        for (int t : cavity) {
            for (int i = 0; i < 4; ++i) {
                const int nb = tets[static_cast<size_t>(t)].nbor[i];
                if (live(nb) && stamp[static_cast<size_t>(nb)] == gen) continue;
                int oface = -1;
                if (live(nb)) {
                    for (int k = 0; k < 4; ++k)
                        if (tets[static_cast<size_t>(nb)].nbor[k] == t) {
                            oface = k;
                            break;
                        }
                    if (oface < 0) return false;
                }
                int f[3];
                face_opp(tets[static_cast<size_t>(t)].v, i, f);
                bfaces.push_back({f[0], f[1], f[2], live(nb) ? nb : -1, oface});
            }
        }
        // 3-ball: F_b = 4T - 2I, so F_b < T is normal for a large cavity.
        // I274 required F_b >= T and aborted (sphere n=512: 20 faces / 21 tets).
        if (bfaces.size() < 4) return false;

        for (int t : cavity) {
            tets[static_cast<size_t>(t)].live = false;
            tets[static_cast<size_t>(t)].nbor[0] = -1;
            tets[static_cast<size_t>(t)].nbor[1] = -1;
            tets[static_cast<size_t>(t)].nbor[2] = -1;
            tets[static_cast<size_t>(t)].nbor[3] = -1;
        }
        newids.clear();
        newids.reserve(bfaces.size());
        pending.clear();
        auto link = [&](int t, int eidx, int a, int b, int c) {
            const uint64_t k = tet_face_key(a, b, c);
            const auto it = pending.find(k);
            if (it == pending.end()) {
                pending.emplace(k, std::pair<int, int>{t, eidx});
                return true;
            }
            const int t2 = it->second.first, e2 = it->second.second;
            tets[static_cast<size_t>(t)].nbor[eidx] = t2;
            tets[static_cast<size_t>(t2)].nbor[e2] = t;
            pending.erase(it);
            return true;
        };
        for (size_t i = 0; i < bfaces.size(); ++i) {
            int a = bfaces[i].a, b = bfaces[i].b, c = bfaces[i].c;
            if (o3(a, b, c, p) <= 0.0) std::swap(a, b);
            if (o3(a, b, c, p) <= 0.0) return false;
            const int id = static_cast<int>(tets.size());
            tets.push_back({{a, b, c, p}, {-1, -1, -1, bfaces[i].outer}, true});
            stamp.push_back(0);
            newids.push_back(id);
            if (bfaces[i].outer >= 0) {
                int oe = bfaces[i].oface;
                if (oe < 0) return false;
                tets[static_cast<size_t>(bfaces[i].outer)].nbor[oe] = id;
            }
            if (!link(id, 0, b, c, p) || !link(id, 1, a, c, p) || !link(id, 2, a, b, p)) return false;
        }
        if (!pending.empty()) return false;
        hint = newids[0];
    }

    std::unordered_set<uint64_t> seen;
    seen.reserve(static_cast<size_t>(n) * 8);
    out.clear();
    out.reserve(static_cast<size_t>(n) * 4 + extra.size());
    for (const Tet& tr : tets) {
        if (!tr.live) continue;
        const int eij[6][2] = {{0, 1}, {0, 2}, {0, 3}, {1, 2}, {1, 3}, {2, 3}};
        for (const auto& e : eij) {
            int a = tr.v[e[0]], b = tr.v[e[1]];
            if (a >= n || b >= n) continue;
            if (a > b) std::swap(a, b);
            const uint64_t key = (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
                                 static_cast<uint32_t>(b);
            if (!seen.insert(key).second) continue;
            out.push_back({point_dist(pts, a, b), a, b});
        }
    }
    for (const SpatEdge& e : extra)
        if (e.u != e.v &&
            seen.insert((static_cast<uint64_t>(static_cast<uint32_t>(e.u)) << 32) | static_cast<uint32_t>(e.v))
                .second)
            out.push_back(e);
    return out.size() >= static_cast<size_t>(n - 1);
}

// I274: 3D Bowyer–Watson scan (I270-style). I275 walk is preferred;
// scan is the n≤8000 fallback if walk still fails. Same MST ⊆ Delaunay.
static bool delaunay_edges_3d_scan(const std::vector<std::vector<value_t>>& pts,
                                   std::vector<SpatEdge>& out) {
    const int n = static_cast<int>(pts.size());
    if (n < 4 || static_cast<int>(pts[0].size()) != 3) return false;
    std::vector<double> xs(static_cast<size_t>(n) + 4), ys(static_cast<size_t>(n) + 4),
        zs(static_cast<size_t>(n) + 4);
    double xmin = static_cast<double>(pts[0][0]), xmax = xmin;
    double ymin = static_cast<double>(pts[0][1]), ymax = ymin;
    double zmin = static_cast<double>(pts[0][2]), zmax = zmin;
    for (int i = 0; i < n; ++i) {
        xs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][0]);
        ys[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][1]);
        zs[static_cast<size_t>(i)] = static_cast<double>(pts[static_cast<size_t>(i)][2]);
        xmin = std::min(xmin, xs[static_cast<size_t>(i)]);
        xmax = std::max(xmax, xs[static_cast<size_t>(i)]);
        ymin = std::min(ymin, ys[static_cast<size_t>(i)]);
        ymax = std::max(ymax, ys[static_cast<size_t>(i)]);
        zmin = std::min(zmin, zs[static_cast<size_t>(i)]);
        zmax = std::max(zmax, zs[static_cast<size_t>(i)]);
    }
    const double dx = std::max(xmax - xmin, 1e-9);
    const double dy = std::max(ymax - ymin, 1e-9);
    const double dz = std::max(zmax - zmin, 1e-9);
    const double mid_x = 0.5 * (xmin + xmax), mid_y = 0.5 * (ymin + ymax),
                 mid_z = 0.5 * (zmin + zmax);
    const double span = 30.0 * (dx + dy + dz);
    xs[static_cast<size_t>(n)] = mid_x - span;
    ys[static_cast<size_t>(n)] = mid_y - span;
    zs[static_cast<size_t>(n)] = mid_z - span;
    xs[static_cast<size_t>(n) + 1] = mid_x + span;
    ys[static_cast<size_t>(n) + 1] = mid_y - span;
    zs[static_cast<size_t>(n) + 1] = mid_z - span;
    xs[static_cast<size_t>(n) + 2] = mid_x;
    ys[static_cast<size_t>(n) + 2] = mid_y + span;
    zs[static_cast<size_t>(n) + 2] = mid_z - span;
    xs[static_cast<size_t>(n) + 3] = mid_x;
    ys[static_cast<size_t>(n) + 3] = mid_y;
    zs[static_cast<size_t>(n) + 3] = mid_z + span;
    if (delaunay_orient3(xs[static_cast<size_t>(n)], ys[static_cast<size_t>(n)], zs[static_cast<size_t>(n)],
                         xs[static_cast<size_t>(n) + 1], ys[static_cast<size_t>(n) + 1],
                         zs[static_cast<size_t>(n) + 1], xs[static_cast<size_t>(n) + 2],
                         ys[static_cast<size_t>(n) + 2], zs[static_cast<size_t>(n) + 2],
                         xs[static_cast<size_t>(n) + 3], ys[static_cast<size_t>(n) + 3],
                         zs[static_cast<size_t>(n) + 3]) <= 0.0) {
        std::swap(xs[static_cast<size_t>(n) + 2], xs[static_cast<size_t>(n) + 3]);
        std::swap(ys[static_cast<size_t>(n) + 2], ys[static_cast<size_t>(n) + 3]);
        std::swap(zs[static_cast<size_t>(n) + 2], zs[static_cast<size_t>(n) + 3]);
    }
    if (delaunay_orient3(xs[static_cast<size_t>(n)], ys[static_cast<size_t>(n)], zs[static_cast<size_t>(n)],
                         xs[static_cast<size_t>(n) + 1], ys[static_cast<size_t>(n) + 1],
                         zs[static_cast<size_t>(n) + 1], xs[static_cast<size_t>(n) + 2],
                         ys[static_cast<size_t>(n) + 2], zs[static_cast<size_t>(n) + 2],
                         xs[static_cast<size_t>(n) + 3], ys[static_cast<size_t>(n) + 3],
                         zs[static_cast<size_t>(n) + 3]) <= 0.0)
        return false;

    struct Tet {
        int v[4];
        bool live;
    };
    std::vector<Tet> tets;
    tets.push_back({{n, n + 1, n + 2, n + 3}, true});

    auto add_face = [](std::unordered_map<uint64_t, int>& cnt,
                       std::unordered_map<uint64_t, std::array<int, 3>>& dir, int a, int b, int c) {
        const uint64_t key = tet_face_key(a, b, c);
        cnt[key] += 1;
        if (dir.find(key) == dir.end()) dir[key] = {a, b, c};
    };

    for (int p = 0; p < n; ++p) {
        const double px = xs[static_cast<size_t>(p)], py = ys[static_cast<size_t>(p)],
                     pz = zs[static_cast<size_t>(p)];
        std::vector<int> bad;
        for (int t = 0; t < static_cast<int>(tets.size()); ++t) {
            if (!tets[static_cast<size_t>(t)].live) continue;
            const int* v = tets[static_cast<size_t>(t)].v;
            if (delaunay_insphere(xs[static_cast<size_t>(v[0])], ys[static_cast<size_t>(v[0])],
                                  zs[static_cast<size_t>(v[0])], xs[static_cast<size_t>(v[1])],
                                  ys[static_cast<size_t>(v[1])], zs[static_cast<size_t>(v[1])],
                                  xs[static_cast<size_t>(v[2])], ys[static_cast<size_t>(v[2])],
                                  zs[static_cast<size_t>(v[2])], xs[static_cast<size_t>(v[3])],
                                  ys[static_cast<size_t>(v[3])], zs[static_cast<size_t>(v[3])], px, py, pz))
                bad.push_back(t);
        }
        if (bad.empty()) return false;
        std::unordered_map<uint64_t, int> fcnt;
        std::unordered_map<uint64_t, std::array<int, 3>> fdir;
        fcnt.reserve(bad.size() * 4);
        for (int t : bad) {
            tets[static_cast<size_t>(t)].live = false;
            const int* v = tets[static_cast<size_t>(t)].v;
            add_face(fcnt, fdir, v[0], v[1], v[2]);
            add_face(fcnt, fdir, v[0], v[1], v[3]);
            add_face(fcnt, fdir, v[0], v[2], v[3]);
            add_face(fcnt, fdir, v[1], v[2], v[3]);
        }
        for (const auto& kv : fcnt) {
            if (kv.second != 1) continue;
            auto abc = fdir[kv.first];
            int a = abc[0], b = abc[1], c = abc[2];
            if (delaunay_orient3(xs[static_cast<size_t>(a)], ys[static_cast<size_t>(a)], zs[static_cast<size_t>(a)],
                                 xs[static_cast<size_t>(b)], ys[static_cast<size_t>(b)], zs[static_cast<size_t>(b)],
                                 xs[static_cast<size_t>(c)], ys[static_cast<size_t>(c)], zs[static_cast<size_t>(c)],
                                 px, py, pz) <= 0.0)
                std::swap(a, b);
            tets.push_back({{a, b, c, p}, true});
        }
    }

    std::unordered_set<uint64_t> seen;
    seen.reserve(static_cast<size_t>(n) * 8);
    out.clear();
    out.reserve(static_cast<size_t>(n) * 4);
    for (const Tet& tr : tets) {
        if (!tr.live) continue;
        const int eij[6][2] = {{0, 1}, {0, 2}, {0, 3}, {1, 2}, {1, 3}, {2, 3}};
        for (const auto& e : eij) {
            int a = tr.v[e[0]], b = tr.v[e[1]];
            if (a >= n || b >= n) continue;
            if (a > b) std::swap(a, b);
            const uint64_t key = (static_cast<uint64_t>(static_cast<uint32_t>(a)) << 32) |
                                 static_cast<uint32_t>(b);
            if (!seen.insert(key).second) continue;
            out.push_back({point_dist(pts, a, b), a, b});
        }
    }
    return out.size() >= static_cast<size_t>(n - 1);
}

static bool delaunay_edges_3d(const std::vector<std::vector<value_t>>& pts,
                              std::vector<SpatEdge>& out) {
    if (delaunay_edges_3d_walk(pts, out)) return true;
    const int n = static_cast<int>(pts.size());
    if (n <= 8000) return delaunay_edges_3d_scan(pts, out);
    return false;
}

bool delaunay_one_skeleton(const std::vector<std::vector<value_t>>& pts, std::vector<Edge>& out) {
    if (pts.empty()) return false;
    std::vector<SpatEdge> del;
    const int d0 = static_cast<int>(pts[0].size());
    bool ok = false;
    if (d0 == 2) ok = delaunay_edges_2d(pts, del);
    else if (d0 == 3) ok = delaunay_edges_3d(pts, del);
    if (!ok) return false;
    out.clear();
    out.reserve(del.size());
    for (const SpatEdge& e : del) out.push_back({e.u, e.v, e.t});
    return true;
}

bool delaunay_thicken_extras(const std::vector<std::vector<value_t>>& pts, value_t T, value_t alpha,
                             std::vector<Edge>& out, value_t floor, bool adapt) {
    if ((!(alpha > 1.0) && !(floor > 0) && !adapt) || pts.empty()) return true;
    const int n = static_cast<int>(pts.size());
    const int d = static_cast<int>(pts[0].size());
    if (d < 2 || d > 3) return true;
    std::vector<double> rad(static_cast<size_t>(n), 0);
    std::vector<std::vector<int>> adj(static_cast<size_t>(n));
    std::unordered_set<uint64_t> have;
    have.reserve(out.size() * 2 + static_cast<size_t>(n) * 8);
    auto ek = [](int u, int v) -> uint64_t {
        if (u > v) std::swap(u, v);
        return (static_cast<uint64_t>(static_cast<uint32_t>(u)) << 32) | static_cast<uint32_t>(v);
    };
    for (const Edge& e : out) {
        have.insert(ek(e.u, e.v));
        const double dt = static_cast<double>(e.t);
        if (dt > rad[static_cast<size_t>(e.u)]) rad[static_cast<size_t>(e.u)] = dt;
        if (dt > rad[static_cast<size_t>(e.v)]) rad[static_cast<size_t>(e.v)] = dt;
        adj[static_cast<size_t>(e.u)].push_back(e.v);
        adj[static_cast<size_t>(e.v)].push_back(e.u);
    }
    std::vector<double> hop = rad;
    if (adapt) {
        for (int i = 0; i < n; ++i)
            for (int j : adj[static_cast<size_t>(i)])
                if (rad[static_cast<size_t>(j)] > hop[static_cast<size_t>(i)])
                    hop[static_cast<size_t>(i)] = rad[static_cast<size_t>(j)];
    }
    std::vector<double> rr = rad;
    std::nth_element(rr.begin(), rr.begin() + n / 2, rr.end());
    const double med = std::max(rr[static_cast<size_t>(n / 2)], 1e-9);
    const double inv = 1.0 / med;
    auto cell_of = [&](int i, int* c) {
        for (int k = 0; k < d; ++k)
            c[k] = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) * inv));
        if (d == 2) c[2] = 0;
    };
    std::unordered_map<uint64_t, std::vector<int>> grid;
    grid.reserve(static_cast<size_t>(n) * 2);
    for (int i = 0; i < n; ++i) {
        int c[3] = {0, 0, 0};
        cell_of(i, c);
        grid[pack_cell(c, d)].push_back(i);
    }
    out.reserve(out.size() + static_cast<size_t>(n) * 16);
    const int cap = (d == 2) ? 16 : 8;
    const double floorR = (floor > 0) ? static_cast<double>(floor) * med : 0;
    const double a0 = (alpha > 0) ? static_cast<double>(alpha) : 1.0;
    auto scan_vertex = [&](int i, std::vector<Edge>& local) {
        const double R = std::max(a0 * hop[static_cast<size_t>(i)], floorR);
        if (!(R > 0)) return;
        const int reach = std::min(cap, std::max(1, static_cast<int>(std::ceil(R * inv + 1e-9))));
        int c0[3] = {0, 0, 0};
        cell_of(i, c0);
        int c[3] = {0, 0, 0};
        const double R2 = R * R;
        for (int dx = -reach; dx <= reach; ++dx)
            for (int dy = -reach; dy <= reach; ++dy)
                for (int dz = (d == 3 ? -reach : 0); dz <= (d == 3 ? reach : 0); ++dz) {
                    // I292: skip cells whose nearest corner is farther than R.
                    if (dx || dy || dz) {
                        const double ax = (dx > 0 ? dx - 1 : (dx < 0 ? -dx - 1 : 0)) * med;
                        const double ay = (dy > 0 ? dy - 1 : (dy < 0 ? -dy - 1 : 0)) * med;
                        const double az =
                            (d == 3) ? (dz > 0 ? dz - 1 : (dz < 0 ? -dz - 1 : 0)) * med : 0.0;
                        if (ax * ax + ay * ay + az * az > R2) continue;
                    }
                    c[0] = c0[0] + dx;
                    c[1] = c0[1] + dy;
                    c[2] = (d == 3) ? c0[2] + dz : 0;
                    const auto it = grid.find(pack_cell(c, d));
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        // Query both ends: d≤α·r_i from i plus d≤α·r_j from j
                        // is d≤α·max(r_i,r_j). Merge dedups.
                        if (j == i) continue;
                        const value_t dist = point_dist(pts, i, j);
                        if (dist > T || static_cast<double>(dist) > R) continue;
                        local.push_back({i, j, dist});
                    }
                }
    };
    // I294: per-vertex thicken queries are independent. Dedup on merge.
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    if (nth <= 1 || n < 1024) {
        std::vector<Edge> local;
        local.reserve(static_cast<size_t>(n) * 8);
        for (int i = 0; i < n; ++i) scan_vertex(i, local);
        for (const Edge& e : local) {
            if (have.insert(ek(e.u, e.v)).second) out.push_back(e);
        }
    } else {
        std::vector<std::vector<Edge>> extras(static_cast<size_t>(nth));
        std::vector<std::thread> pool;
        pool.reserve(static_cast<size_t>(nth));
        for (int t = 0; t < nth; ++t) {
            pool.emplace_back([&, t]() {
                const int i0 = n * t / nth;
                const int i1 = n * (t + 1) / nth;
                extras[static_cast<size_t>(t)].reserve(static_cast<size_t>(std::max(i1 - i0, 0)) * 8);
                for (int i = i0; i < i1; ++i) scan_vertex(i, extras[static_cast<size_t>(t)]);
            });
        }
        for (auto& th : pool) th.join();
        for (const auto& vec : extras) {
            for (const Edge& e : vec) {
                if (have.insert(ek(e.u, e.v)).second) out.push_back(e);
            }
        }
    }
    return true;
}

bool delaunay_vr_skeleton(const std::vector<std::vector<value_t>>& pts, value_t T, value_t alpha,
                          std::vector<Edge>& out, value_t floor, bool adapt) {
    if (!delaunay_one_skeleton(pts, out)) return false;
    return delaunay_thicken_extras(pts, T, alpha, out, floor, adapt);
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
        bool delaunay = false;
        const int d0 = n ? static_cast<int>(pts[0].size()) : 0;
        if (std::isfinite(threshold) && n >= 256) {
            std::vector<SpatEdge> del;
            if (d0 == 2 && n <= 100000 && delaunay_edges_2d(pts, del)) {
                E.reserve(del.size());
                for (const SpatEdge& e : del)
                    if (e.t <= threshold) E.push_back(e);
                delaunay = true;
            } else if (d0 == 3 && n <= 50000 && delaunay_edges_3d(pts, del)) {
                E.reserve(del.size());
                for (const SpatEdge& e : del)
                    if (e.t <= threshold) E.push_back(e);
                delaunay = true;
            }
        }
        if (!delaunay) {
            if (!spatial_edges(pts, threshold, E)) {
                E.reserve(static_cast<size_t>(n) * 4);
                for (int j = 1; j < n; ++j)
                    for (int i = 0; i < j; ++i) {
                        const value_t dist = point_dist(pts, i, j);
                        if (dist <= threshold) E.push_back({dist, i, j});
                    }
            }
        }
        const auto tm1 = std::chrono::steady_clock::now();
        Result r = kruskal_h0(n, std::move(E));
        r.counters.metric_ms = std::chrono::duration<double, std::milli>(tm1 - tm0).count();
        if (delaunay) r.counters.pipeline += "-delaunay";
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
    // distances and pass a prebuilt EdgeList. Dense clouds (π(T/L)²≥0.2)
    // keep I238 parallel all-pairs unless a cheap edge-frac probe says
    // G_T is still sparse (hollow / manifold supports).
    // I262 always-spatial was exact (figure8 n=2000 14×) but lost the
    // dense 10× (uniform2 n=5000 7.4× / 0.46s; sphere n=2000 6.8×).
    // I263: spatial if volume < 0.20 OR 250-pt edge frac < 0.25.
    // figure8 T=1.1 is the discriminator (vol≈0.22, probe≈0.24);
    // uniform2 n=5000 probe≈0.26–0.29 and sphere ≈0.49 stay all-pairs.
    std::vector<SpatEdge> SE;
    bool spatial = false;
    if (std::isfinite(threshold) && threshold > 0 && d >= 2 && d <= 3 && n >= 256) {
        const double L = bbox_max_extent(pts);
        if (L > 0) {
            const double tL = static_cast<double>(threshold) / L;
            const double frac = (d == 2) ? (3.141592653589793 * tL * tL)
                                         : (4.188790204786391 * tL * tL * tL);
            const bool vol_sparse = frac < 0.20;
            const bool probe_sparse = !vol_sparse && probe_edge_frac_points(pts, threshold) < 0.25;
            if (vol_sparse || probe_sparse) spatial = spatial_edges(pts, threshold, SE);
        }
    }
    DistanceMatrix D;
    SparseDist csr;
    const auto tfill0 = std::chrono::steady_clock::now();
    if (spatial) {
        spat_to_hash(SE, n, csr);
        D.n = n;
    } else {
        D.resize_lower(n);
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
    struct SparseGuard {
        explicit SparseGuard(const SparseDist* p) { g_sparse = p; }
        ~SparseGuard() { g_sparse = nullptr; }
    };
    const SparseGuard guard(spatial ? &csr : nullptr);
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

Result persist_redzed_from_edges(int n, const std::vector<Edge>& edges, int maxdim,
                                 value_t threshold) {
    Result r;
    if (n <= 0 || maxdim < 0) {
        r.counters.n_vertices = n;
        return r;
    }
    std::vector<SpatEdge> SE;
    SE.reserve(edges.size());
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        SE.push_back({e.t, e.u, e.v});
    }
    if (maxdim < 1) {
        r = kruskal_h0(n, std::move(SE));
        r.counters.pipeline = "pith:redzed-edges-h0";
        return r;
    }
    SparseDist csr;
    spat_to_hash(SE, n, csr);
    DistanceMatrix D;
    D.n = n;
    EdgeList pre;
    BinomialTable bt(n, maxdim + 2);
    edgelist_from_spat(SE, threshold, bt, pre);
    struct SparseGuard {
        explicit SparseGuard(const SparseDist* p) { g_sparse = p; }
        ~SparseGuard() { g_sparse = nullptr; }
    };
    const SparseGuard guard(&csr);
    const auto t0 = std::chrono::steady_clock::now();
    auto bars = redzed_vr(D, maxdim, threshold, &pre);
    append_bars(r, bars, maxdim);
    const auto t1 = std::chrono::steady_clock::now();
    r.counters.n_vertices = n;
    r.counters.n_edges_in = static_cast<std::int64_t>(SE.size());
    r.counters.n_collapse_trims = 1;
    r.counters.n_distances = static_cast<std::int64_t>(SE.size());
    r.counters.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    r.counters.pipeline = "pith:redzed-edges";
    return r;
}

}  // namespace pith
