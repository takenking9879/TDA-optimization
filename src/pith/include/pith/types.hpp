#pragma once

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <limits>
#include <string>
#include <vector>

namespace pith {

using value_t = float;
using index_t = int32_t;

static constexpr value_t kInf = std::numeric_limits<value_t>::infinity();
static constexpr value_t kNegInf = -std::numeric_limits<value_t>::infinity();

enum class Fidelity { Exact, ApproxGuaranteed, Empirical, Unverified };

struct Edge {
    index_t u = 0;
    index_t v = 0;
    value_t t = 0;
};

inline void normalize_edge(Edge& e) {
    if (e.u > e.v) std::swap(e.u, e.v);
}

struct PersistencePair {
    int dim = 0;
    value_t birth = 0;
    value_t death = kInf;
};

struct Counters {
    std::int64_t n_vertices = 0;
    std::int64_t n_edges_in = 0;
    std::int64_t n_edges_out = 0;
    std::int64_t n_distances = 0;
    std::int64_t n_simplices_enumerated = 0;
    std::int64_t n_columns_assembled = 0;
    std::int64_t n_columns_apparent = 0;
    std::int64_t n_columns_cleared = 0;
    std::int64_t n_columns_reduced = 0;
    std::int64_t n_additions = 0;
    std::int64_t n_cofacet_probes = 0;
    std::int64_t n_collapse_shifts = 0;
    std::int64_t n_collapse_trims = 0;
    std::int64_t n_collapse_c_probes = 0;
    std::int64_t n_collapse_dom_tests = 0;
    std::int64_t n_collapse_dom_hits = 0;
    std::int64_t n_collapse_c_size_sum = 0;
    std::int64_t n_collapse_shift_lookups = 0;
    std::int64_t n_collapse_fast_trims = 0;
    std::int64_t n_collapse_first_keep = -1;
    std::int64_t n_collapse_tau_late = 0;
    std::int64_t n_collapse_tau_late_common = 0;
    double collapse_ms = 0;
    double reduce_ms = 0;
    double metric_ms = 0;
    std::int64_t rss_bytes_peak = 0;
    std::string pipeline;
};

struct Result {
    std::vector<PersistencePair> pairs;
    Counters counters;
};

inline value_t enclosing_radius(const std::vector<std::vector<value_t>>& dist) {
    const int n = static_cast<int>(dist.size());
    value_t best = kInf;
    for (int i = 0; i < n; ++i) {
        value_t farthest = 0;
        for (int j = 0; j < n; ++j) farthest = std::max(farthest, dist[i][j]);
        best = std::min(best, farthest);
    }
    return best;
}

inline std::int64_t peak_rss_bytes() {
    FILE* f = std::fopen("/proc/self/status", "r");
    if (!f) return 0;
    char line[256];
    std::int64_t kb = 0;
    while (std::fgets(line, sizeof line, f)) {
        if (std::sscanf(line, "VmHWM: %ld", &kb) == 1) break;
    }
    std::fclose(f);
    return kb * 1024;
}

}  // namespace pith
