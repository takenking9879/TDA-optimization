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
        b.bars = redzed(S, dim, threshold);
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
        auto bars = redzed(D, dim, threshold);
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
            for (int i = 0; i < j; ++i) D.mat[DistanceMatrix::offset(i, j)] = point_dist(pts, i, j);
        auto bars = redzed(D, dim, threshold);
        append_bars(r, bars, dim);
        c.pipeline = "pith:redzed";
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

    DistanceMatrix D;
    D.resize_lower(n);
    const auto tfill0 = std::chrono::steady_clock::now();
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
    const auto tfill1 = std::chrono::steady_clock::now();
    Result r = finish_redzed(std::move(D), maxdim, threshold);
    r.counters.n_distances = static_cast<std::int64_t>(n) * (n - 1) / 2;
    r.counters.metric_ms = std::chrono::duration<double, std::milli>(tfill1 - tfill0).count();
    return r;
}

}  // namespace pith
