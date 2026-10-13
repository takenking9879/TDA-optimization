// I228: translation unit that owns the vendored RedZeD driver.
// redzed.cpp is MIT and compiled with REDZED_NO_MAIN so only the library
// entry is visible. Do not edit third_party/redzed/redzed.cpp.

#define REDZED_NO_MAIN
#include "../../../third_party/redzed/redzed.cpp"

#include "pith/redzed_bridge.hpp"

#include <atomic>
#include <chrono>
#include <cmath>
#include <functional>
#include <numeric>
#include <thread>

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

// I239: VR≤T of a disconnected G_T is the wedge of the components.
// Split, run RedZeD on each block, merge bars. Exact. Superadditive
// reduce (blobs = 3 clusters at T=1). One component → same as I228.
static Result finish_redzed(DistanceMatrix&& D, int maxdim, value_t threshold) {
    Result r;
    Counters& c = r.counters;
    const int n = D.n;
    c.n_vertices = n;
    if (n <= 0 || maxdim < 0) return r;
    const int dim = maxdim < 1 ? 0 : maxdim;

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
    std::vector<std::vector<int>> buckets(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) buckets[static_cast<size_t>(find(i))].push_back(i);
    std::vector<std::vector<int>> comps;
    comps.reserve(static_cast<size_t>(n));
    for (auto& b : buckets)
        if (!b.empty()) comps.push_back(std::move(b));
    c.n_collapse_trims = static_cast<std::int64_t>(comps.size());

    const auto t0 = std::chrono::steady_clock::now();
    if (comps.size() <= 1) {
        auto bars = redzed(D, dim, threshold);
        append_bars(r, bars, dim);
        c.pipeline = "pith:redzed";
    } else {
        c.pipeline = "pith:redzed-cc";
        struct Block {
            std::vector<int> verts;
            std::vector<std::vector<std::pair<value_t, value_t>>> bars;
        };
        std::vector<Block> blocks(comps.size());
        for (size_t i = 0; i < comps.size(); ++i) blocks[i].verts = std::move(comps[i]);
        auto run_block = [&](Block& b) {
            const int m = static_cast<int>(b.verts.size());
            if (m <= 1) return;
            DistanceMatrix S;
            S.resize_lower(m);
            for (int j = 1; j < m; ++j)
                for (int i = 0; i < j; ++i)
                    S.mat[DistanceMatrix::offset(i, j)] =
                        D(b.verts[static_cast<size_t>(i)], b.verts[static_cast<size_t>(j)]);
            b.bars = redzed(S, dim, threshold);
        };
        // Bounded pool: one thread per component would explode on a
        // dust cloud (many size-1 / tiny blocks). Size-1 is H0-only.
        std::vector<Block*> work;
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
            for (Block* b : work) run_block(*b);
        }
        for (auto& b : blocks) {
            if (b.verts.size() <= 1) r.pairs.push_back({0, 0, kInf});
            else append_bars(r, b.bars, dim);
        }
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
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    DistanceMatrix D;
    D.resize_lower(n);
    const auto tm0 = std::chrono::steady_clock::now();
    const int nth = std::max(1, static_cast<int>(std::thread::hardware_concurrency()));
    auto fill_range = [&](int j0, int j1) {
        for (int j = j0; j < j1; ++j) {
            for (int i = 0; i < j; ++i) {
                double s = 0;
                for (int k = 0; k < d; ++k) {
                    const double df = static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) -
                                      static_cast<double>(pts[static_cast<size_t>(j)][static_cast<size_t>(k)]);
                    s += df * df;
                }
                D.mat[DistanceMatrix::offset(i, j)] = static_cast<value_t>(std::sqrt(s));
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
    const auto tm1 = std::chrono::steady_clock::now();
    Result r = finish_redzed(std::move(D), maxdim, threshold);
    r.counters.n_distances = static_cast<std::int64_t>(n) * (n - 1) / 2;
    r.counters.metric_ms = std::chrono::duration<double, std::milli>(tm1 - tm0).count();
    return r;
}

}  // namespace pith
