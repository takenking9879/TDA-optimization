// I228: translation unit that owns the vendored RedZeD driver.
// redzed.cpp is MIT and compiled with REDZED_NO_MAIN so only the library
// entry is visible. Do not edit third_party/redzed/redzed.cpp.

#define REDZED_NO_MAIN
#include "../../../third_party/redzed/redzed.cpp"

#include "pith/redzed_bridge.hpp"

#include <chrono>
#include <cmath>
#include <thread>

namespace pith {

static Result finish_redzed(DistanceMatrix&& D, int maxdim, value_t threshold) {
    Result r;
    Counters& c = r.counters;
    const int n = D.n;
    c.n_vertices = n;
    if (n <= 0 || maxdim < 0) return r;
    const int dim = maxdim < 1 ? 0 : maxdim;
    const auto t0 = std::chrono::steady_clock::now();
    auto bars = redzed(D, dim, threshold);
    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.pipeline = "pith:redzed";
    const int up = std::min(dim, static_cast<int>(bars.size()) - 1);
    for (int d = 0; d <= up; ++d) {
        for (const auto& p : bars[static_cast<size_t>(d)]) {
            r.pairs.push_back({d, p.first, p.second});
        }
    }
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
