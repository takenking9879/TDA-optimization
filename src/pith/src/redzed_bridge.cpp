// I228: translation unit that owns the vendored RedZeD driver.
// redzed.cpp is MIT and compiled with REDZED_NO_MAIN so only the library
// entry is visible. Do not edit third_party/redzed/redzed.cpp.

#define REDZED_NO_MAIN
#include "../../../third_party/redzed/redzed.cpp"

#include "pith/redzed_bridge.hpp"

#include <chrono>

namespace pith {

Result persist_redzed(const std::vector<std::vector<value_t>>& dist, int maxdim,
                      value_t threshold) {
    Result r;
    Counters& c = r.counters;
    const int n = static_cast<int>(dist.size());
    c.n_vertices = n;
    if (n <= 0 || maxdim < 0) return r;

    DistanceMatrix D;
    D.resize_lower(n);
    for (int j = 1; j < n; ++j) {
        for (int i = 0; i < j; ++i) {
            D.mat[DistanceMatrix::offset(i, j)] = dist[static_cast<size_t>(i)][static_cast<size_t>(j)];
        }
    }

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

}  // namespace pith
