#include "pith/edge_collapse.hpp"
#include "pith/persist.hpp"
#include "pith/persist_active.hpp"
#include "pith/reduced_vr.hpp"
#include "pith/redzed_bridge.hpp"
#include "pith/sparse_rips.hpp"
#include "pith/threads.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

using namespace pith;

static void usage() {
    std::cerr
        << "PITH — persistent homology for point clouds (CPU)\n"
        << "Usage: pith --points FILE.csv [options]\n"
        << "       pith --distances FILE [options]\n"
        << "       pith --estimate --points FILE.csv [options]\n"
        << "\n"
        << "Stable options:\n"
        << "  --maxdim K              homology dimension (default 1)\n"
        << "  --threshold T           VR diameter threshold (default inf)\n"
        << "  --mode exact|scale|sparse\n"
        << "                          exact  = exact VR≤T (default)\n"
        << "                          scale  = Euclidean Delaunay-flag path (d=2,3; not exact VR)\n"
        << "                          sparse = greedy-net sparse Rips (approx; default eps=0.6)\n"
        << "  --engine auto|redzed|implicit\n"
        << "                          exact-mode engine (default auto: pick redzed or collapse)\n"
        << "  --estimate              feasibility estimate only (no persistence)\n"
        << "  --threads N             cap worker threads (default: hardware)\n"
        << "  --format text|json      output format (default text)\n"
        << "  --no-enclosing          do not cap T by enclosing radius\n"
        << "  --help                  this message\n"
        << "  --help-experimental     research flags (not needed for normal use)\n";
}

static void usage_experimental() {
    std::cerr
        << "Experimental / compatibility flags (research ledger; not the stable API):\n"
        << "  --engine homology|active\n"
        << "  --collapse N            collapse passes (default -1 adaptive; 0 = off)\n"
        << "  --collapse-alg back|back-src|back-bits|dc|forward|suffix*\n"
        << "  --suffix-mult X  --suffix-keep N  --suffix-k K\n"
        << "  --later-b  --later-escalate K  --later-esc-until N  --later-b-cap N\n"
        << "  --dom-budget K  --ratio R  --edges FILE  --sparse-only\n"
        << "  --sparse-eps EPS  --sparse-cap max|min\n"
        << "  --witness-n M  --witness-nu K  --knn K  --gic-n M  --gic-k K\n"
        << "  --reduced-vr  --delaunay-vr  --delaunay-alpha A|auto\n"
        << "  --delaunay-adapt  --delaunay-floor F\n"
        << "  --probe-only  --probe-vertex\n"
        << "Iteration numbers live in RESEARCH_LOG.md, not this interface.\n";
}

static std::vector<std::vector<value_t>> read_points(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path);
    std::vector<std::vector<value_t>> pts;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::replace(line.begin(), line.end(), ',', ' ');
        std::istringstream ss(line);
        std::vector<value_t> row;
        value_t x;
        while (ss >> x) row.push_back(x);
        if (!row.empty()) pts.push_back(std::move(row));
    }
    return pts;
}

static std::vector<std::vector<value_t>> read_distance_matrix(const std::string& path) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path);
    std::vector<std::vector<value_t>> rows;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty() || line[0] == '#') continue;
        std::replace(line.begin(), line.end(), ',', ' ');
        std::istringstream ss(line);
        std::vector<value_t> row;
        value_t x;
        while (ss >> x) row.push_back(x);
        if (!row.empty()) rows.push_back(std::move(row));
    }
    if (rows.empty()) throw std::runtime_error("empty distance file");
    const int n = static_cast<int>(rows.size());
    // Square matrix.
    if (static_cast<int>(rows[0].size()) == n) {
        for (int i = 0; i < n; ++i) {
            if (static_cast<int>(rows[i].size()) != n)
                throw std::runtime_error("ragged square distance matrix");
        }
        return rows;
    }
    // Ripser lower-distance: line i has i entries (no diagonal). The i=0
    // line is empty and already skipped, so we see rows of length 1..n-1.
    if (static_cast<int>(rows[0].size()) == 1 &&
        static_cast<int>(rows.back().size()) == n) {
        const int N = n + 1;
        std::vector<std::vector<value_t>> dist(N, std::vector<value_t>(N, 0));
        for (int i = 0; i < n; ++i) {
            const int r = i + 1;
            if (static_cast<int>(rows[i].size()) != r)
                throw std::runtime_error("lower-distance row length != i");
            for (int j = 0; j < r; ++j) {
                dist[r][j] = dist[j][r] = rows[i][j];
            }
        }
        return dist;
    }
    if (static_cast<int>(rows[0].size()) == 0 || rows[0].size() < rows.back().size()) {
        std::vector<std::vector<value_t>> dist(n, std::vector<value_t>(n, 0));
        for (int i = 0; i < n; ++i) {
            if (static_cast<int>(rows[i].size()) != i)
                throw std::runtime_error("lower-distance row length != i");
            for (int j = 0; j < i; ++j) {
                dist[i][j] = dist[j][i] = rows[i][j];
            }
        }
        return dist;
    }
    throw std::runtime_error("unrecognized distance matrix shape");
}

// I207: '# n=N' header plus 'u v t' lines. n is required so isolated vertices
// stay in the complex.
static Graph read_edge_list(const std::string& path, value_t threshold) {
    std::ifstream in(path);
    if (!in) throw std::runtime_error("cannot open " + path);
    int n = -1;
    std::vector<Edge> edges;
    std::string line;
    while (std::getline(in, line)) {
        if (line.empty()) continue;
        if (line[0] == '#') {
            const auto pos = line.find("n=");
            if (pos != std::string::npos) n = std::stoi(line.substr(pos + 2));
            continue;
        }
        std::replace(line.begin(), line.end(), ',', ' ');
        std::istringstream ss(line);
        std::string tok;
        if (!(ss >> tok)) continue;
        if (tok == "n") {
            ss >> n;
            continue;
        }
        Edge e;
        try {
            e.u = std::stoi(tok);
        } catch (...) {
            continue;
        }
        if (!(ss >> e.v >> e.t)) continue;
        edges.push_back(e);
    }
    if (n < 0) {
        n = 0;
        for (const Edge& e : edges) n = std::max(n, std::max(e.u, e.v) + 1);
    }
    if (n <= 0) throw std::runtime_error("edge list missing n");
    return graph_from_edge_list(n, edges, threshold);
}

static std::vector<std::vector<value_t>> pairwise(const std::vector<std::vector<value_t>>& pts,
                                                 Counters& c) {
    const auto t0 = std::chrono::steady_clock::now();
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    std::vector<std::vector<value_t>> dist(n, std::vector<value_t>(n, 0));
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            double s = 0;
            for (int k = 0; k < d; ++k) {
                const double df = static_cast<double>(pts[i][k]) - static_cast<double>(pts[j][k]);
                s += df * df;
            }
            const value_t t = static_cast<value_t>(std::sqrt(s));
            dist[i][j] = dist[j][i] = t;
            ++c.n_distances;
        }
    }
    const auto t1 = std::chrono::steady_clock::now();
    c.metric_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    return dist;
}

static void print_text(const Result& r) {
    std::cout << std::setprecision(8);
    int cur = -1;
    for (const auto& p : r.pairs) {
        if (p.dim != cur) {
            cur = p.dim;
            std::cout << "persistence intervals in dim " << cur << ":\n";
        }
        std::cout << " [" << p.birth << ",";
        if (std::isfinite(p.death)) std::cout << p.death << ")\n";
        else std::cout << " )\n";
    }
    const auto& c = r.counters;
    std::cout << "# COUNTERS pipeline=" << c.pipeline
              << " n=" << c.n_vertices
              << " edges_in=" << c.n_edges_in
              << " edges_out=" << c.n_edges_out
              << " distances=" << c.n_distances
              << " simplices=" << c.n_simplices_enumerated
              << " cols_assembled=" << c.n_columns_assembled
              << " cols_reduced=" << c.n_columns_reduced
              << " cols_apparent=" << c.n_columns_apparent
              << " cols_cleared=" << c.n_columns_cleared
              << " additions=" << c.n_additions
              << " cofacet_probes=" << c.n_cofacet_probes
              << " cofacet_apparent_probes=" << c.n_cofacet_apparent_probes
              << " collapse_trims=" << c.n_collapse_trims
              << " collapse_shifts=" << c.n_collapse_shifts
              << " collapse_c_probes=" << c.n_collapse_c_probes
              << " collapse_dom_tests=" << c.n_collapse_dom_tests
              << " collapse_dom_hits=" << c.n_collapse_dom_hits
              << " collapse_dom_skips=" << c.n_collapse_dom_skips
              << " collapse_killer_hits=" << c.n_collapse_killer_hits
              << " collapse_c_size=" << c.n_collapse_c_size_sum
              << " collapse_shift_lookups=" << c.n_collapse_shift_lookups
              << " collapse_fast_trims=" << c.n_collapse_fast_trims
              << " collapse_vertex_trims=" << c.n_collapse_vertex_trims
              << " collapse_first_keep=" << c.n_collapse_first_keep
              << " collapse_tau_late=" << c.n_collapse_tau_late
              << " collapse_tau_late_common=" << c.n_collapse_tau_late_common
              << " collapse_early_keep_n=" << c.n_collapse_early_keep_n
              << " collapse_early_empty_c=" << c.n_collapse_early_empty_c
              << " collapse_early_fail_max=" << c.n_collapse_early_fail_max
              << " collapse_early_any_later=" << c.n_collapse_early_any_later
              << " collapse_early_later_a=" << c.n_collapse_early_later_a
              << " collapse_early_later_b=" << c.n_collapse_early_later_b
              << " collapse_keep_hist=" << c.n_collapse_keep_hist[0];
    for (int b = 1; b < 16; ++b) std::cout << "," << c.n_collapse_keep_hist[b];
    std::cout << " collapse_early_keeps=" << c.n_collapse_early_keeps[0];
    for (int b = 1; b < 8; ++b) std::cout << "," << c.n_collapse_early_keeps[b];
    std::cout << " metric_ms=" << c.metric_ms
              << " collapse_ms=" << c.collapse_ms
              << " reduce_ms=" << c.reduce_ms
              << " residual_frac=" << c.residual_frac
              << " rss=" << c.rss_bytes_peak
              << " threads=" << c.n_threads << "\n";
}

static void print_json(const Result& r) {
    const auto& c = r.counters;
    std::cout << "{\n";
    std::cout << "  \"pipeline\": \"" << c.pipeline << "\",\n";
    std::cout << "  \"counters\": {\n"
              << "    \"n_vertices\": " << c.n_vertices << ",\n"
              << "    \"n_edges_in\": " << c.n_edges_in << ",\n"
              << "    \"n_edges_out\": " << c.n_edges_out << ",\n"
              << "    \"n_distances\": " << c.n_distances << ",\n"
              << "    \"n_simplices_enumerated\": " << c.n_simplices_enumerated << ",\n"
              << "    \"n_columns_assembled\": " << c.n_columns_assembled << ",\n"
              << "    \"n_columns_reduced\": " << c.n_columns_reduced << ",\n"
              << "    \"n_columns_apparent\": " << c.n_columns_apparent << ",\n"
              << "    \"n_columns_cleared\": " << c.n_columns_cleared << ",\n"
              << "    \"n_additions\": " << c.n_additions << ",\n"
              << "    \"n_cofacet_probes\": " << c.n_cofacet_probes << ",\n"
              << "    \"n_cofacet_apparent_probes\": " << c.n_cofacet_apparent_probes << ",\n"
              << "    \"n_collapse_trims\": " << c.n_collapse_trims << ",\n"
              << "    \"n_collapse_shifts\": " << c.n_collapse_shifts << ",\n"
              << "    \"metric_ms\": " << c.metric_ms << ",\n"
              << "    \"collapse_ms\": " << c.collapse_ms << ",\n"
              << "    \"reduce_ms\": " << c.reduce_ms << ",\n"
              << "    \"rss_bytes_peak\": " << c.rss_bytes_peak << ",\n"
              << "    \"n_threads\": " << c.n_threads << "\n"
              << "  },\n";
    std::cout << "  \"pairs\": [\n";
    for (size_t i = 0; i < r.pairs.size(); ++i) {
        const auto& p = r.pairs[i];
        std::cout << "    {\"dim\": " << p.dim << ", \"birth\": " << p.birth << ", \"death\": ";
        if (std::isfinite(p.death)) std::cout << p.death;
        else std::cout << "null";
        std::cout << "}" << (i + 1 < r.pairs.size() ? "," : "") << "\n";
    }
    std::cout << "  ]\n}\n";
}

// Empirical feasibility probe. Not a theorem: uses the same 250-pt
// residual / edge-frac oracles as --engine auto, plus conservative
// |E| / residual cutoffs measured on the I227–I312 suite. Probe
// fractions are inflated (×1.25) before feasibility cuts.
static int print_estimate(const std::vector<std::vector<value_t>>* pts,
                          const std::vector<std::vector<value_t>>* dist, int maxdim, value_t T,
                          const std::string& format) {
    const int n = pts ? static_cast<int>(pts->size())
                      : (dist ? static_cast<int>(dist->size()) : 0);
    const int dim = (pts && !pts->empty()) ? static_cast<int>((*pts)[0].size()) : -1;
    double edge_frac = -1;
    double residual_frac = -1;
    if (pts && n >= 8 && std::isfinite(T) && T > 0)
        edge_frac = probe_edge_frac_points(*pts, T, 250);
    if (n >= 8) {
        residual_frac = pts ? probe_residual_frac_points(*pts, T, 250)
                            : (dist ? probe_residual_frac(*dist, T, 250) : -1);
    }
    const double all_pairs = (n > 1) ? 0.5 * static_cast<double>(n) * (n - 1) : 0;
    const double est_e = (edge_frac >= 0) ? edge_frac * all_pairs : all_pairs;
    const double edge_frac_hi = (edge_frac >= 0) ? std::min(1.0, edge_frac * 1.25) : 1.0;
    const double est_e_hi = edge_frac_hi * all_pairs;
    const double est_e_lo = (edge_frac >= 0) ? std::max(0.0, edge_frac * 0.80) * all_pairs : 0;
    const double est_r = (residual_frac >= 0 && edge_frac >= 0) ? residual_frac * est_e : -1;
    const double est_r_hi = (residual_frac >= 0) ? residual_frac * est_e_hi : -1;
    const double est_del = (dim == 2) ? 3.0 * n : (dim == 3) ? 7.0 * n : -1;
    const double tau = (maxdim >= 2) ? 0.15 : 0.04;
    const bool hollow = edge_frac >= 0 && edge_frac < 0.25;
    const bool fat = residual_frac >= 0 && residual_frac > tau;
    const bool thin = residual_frac >= 0 && residual_frac <= tau && !hollow;
    std::string regime = "unknown";
    if (maxdim < 1) regime = "h0";
    else if (hollow) regime = "hollow";
    else if (fat) regime = "fat";
    else if (thin) regime = "thin";
    std::string engine_rec = "implicit";
    if (maxdim < 1) engine_rec = "redzed";  // Kruskal / Delaunay H0
    else if (fat || hollow) engine_rec = "redzed";
    bool exact_ok = true;
    std::string reason = "exact VR looks feasible on the 250-pt probe (conservative |E| band)";
    if (maxdim >= 1 && est_e_hi > 8.0e6) {
        exact_ok = false;
        reason = "conservative |E| band exceeds 8e6; exact H1 on G_T is likely impractical";
    } else if (maxdim >= 1 && fat && est_r_hi > 1.5e6) {
        exact_ok = false;
        reason = "fat residual band exceeds 1.5e6 leftover edges; exact leftover visits explode";
    } else if (maxdim >= 1 && n > 20000 && !thin && edge_frac > 0.15) {
        exact_ok = false;
        reason = "dense G_T at n>20000 with a non-thin residual; exact H1 leaves the low-polynomial regime";
    } else if (maxdim >= 1 && fat && n > 6000 && dim >= 2 && dim <= 3) {
        reason = "fat Euclidean residual at n>6000: exact may still finish, scale is the safer option";
    } else if (maxdim >= 1 && thin && n > 8000 && dim >= 2 && dim <= 3) {
        reason = "thin residual: exact collapse+implicit is still the intended path; scale is optional";
    }
    std::string mode_rec = "exact";
    if (!exact_ok && dim >= 2 && dim <= 3) mode_rec = "scale";
    else if (!exact_ok) mode_rec = "sparse";
    else if (fat && n > 6000 && dim >= 2 && dim <= 3) mode_rec = "scale";
    const bool near_tau =
        residual_frac >= 0 && std::fabs(residual_frac - tau) < 0.02;
    const char* confidence =
        (n <= 400 && !near_tau) ? "medium" : "low";
    double est_runtime = -1;
    if (maxdim < 1 && n > 0) {
        est_runtime = 2.0e-6 * static_cast<double>(n) * std::max(1.0, std::log2(static_cast<double>(n)));
    } else if (mode_rec == "scale" && n > 0) {
        est_runtime = (dim == 3 ? 2.0e-5 : 3.5e-5) * static_cast<double>(n);
    } else if (thin && n > 0) {
        est_runtime = 4.0e-8 * static_cast<double>(n) * static_cast<double>(n);
    } else if (est_e_hi > 0) {
        est_runtime = 8.0e-8 * est_e_hi;
    }
    const char* runtime = !exact_ok ? "impractical-or-scale"
                                    : (est_runtime > 1.0 || (n >= 4000 && maxdim >= 1) ? "seconds"
                                                                                       : "sub-second");
    if (format == "json") {
        std::cout << std::setprecision(6);
        std::cout << "{\n"
                  << "  \"kind\": \"estimate\",\n"
                  << "  \"empirical\": true,\n"
                  << "  \"n\": " << n << ",\n"
                  << "  \"dim\": " << dim << ",\n"
                  << "  \"maxdim\": " << maxdim << ",\n"
                  << "  \"threshold\": " << T << ",\n"
                  << "  \"edge_frac_probe\": " << edge_frac << ",\n"
                  << "  \"residual_frac_probe\": " << residual_frac << ",\n"
                  << "  \"residual_regime\": \"" << regime << "\",\n"
                  << "  \"est_edges\": " << est_e << ",\n"
                  << "  \"est_edges_lo\": " << est_e_lo << ",\n"
                  << "  \"est_edges_hi\": " << est_e_hi << ",\n"
                  << "  \"est_residual_edges\": " << est_r << ",\n"
                  << "  \"est_residual_edges_hi\": " << est_r_hi << ",\n"
                  << "  \"est_delaunay_edges\": " << est_del << ",\n"
                  << "  \"est_runtime_s\": " << est_runtime << ",\n"
                  << "  \"engine_recommended\": \"" << engine_rec << "\",\n"
                  << "  \"mode_recommended\": \"" << mode_rec << "\",\n"
                  << "  \"exact_feasible\": " << (exact_ok ? "true" : "false") << ",\n"
                  << "  \"runtime_class\": \"" << runtime << "\",\n"
                  << "  \"confidence\": \"" << confidence << "\",\n"
                  << "  \"threads\": " << nthreads() << ",\n"
                  << "  \"reason\": \"" << reason << "\"\n"
                  << "}\n";
    } else {
        std::cout << "# ESTIMATE empirical=true n=" << n << " dim=" << dim << " maxdim=" << maxdim
                  << " T=" << T << " edge_frac=" << edge_frac << " residual_frac=" << residual_frac
                  << " regime=" << regime << " est_edges=" << est_e << " est_edges_hi=" << est_e_hi
                  << " est_residual=" << est_r << " est_delaunay=" << est_del
                  << " engine=" << engine_rec << " mode=" << mode_rec
                  << " exact_feasible=" << (exact_ok ? 1 : 0) << " runtime=" << runtime
                  << " est_runtime_s=" << est_runtime << " confidence=" << confidence
                  << " threads=" << nthreads() << "\n# " << reason << "\n";
    }
    return 0;
}

int main(int argc, char** argv) {
    std::string points_path;
    std::string dist_path;
    std::string edges_path;
    int maxdim = 1;
    value_t threshold = kInf;
    int collapse_iters = -1;  // adaptive + domination probe
    int dom_budget = -1;      // I107: -1 = exhaustive exact collapse
    value_t ratio = 1;
    bool use_enclosing = true;
    bool sparse_only = false;
    bool probe_only = false;
    bool probe_vertex = false;
    std::string format = "text";
    std::string engine = "auto";
    std::string collapse_alg = "back";
    double suffix_mult = 6;
    std::int64_t suffix_keep = -1;
    int suffix_k = 8;
    value_t sparse_eps = -1;
    SparseCap sparse_cap = SparseCap::Max;
    int witness_n = 0;
    int witness_nu = 0;  // I216: ν=1 invents essential H1; I217 tests 0
    int knn_k = 0;
    int gic_n = 0;
    int gic_k = 16;
    bool reduced_vr = false;
    bool delaunay_vr = false;
    value_t delaunay_alpha = 1;
    value_t delaunay_floor = 0;
    bool delaunay_adapt = false;
    bool delaunay_alpha_auto = false;
    bool later_b = false;
    int later_escalate = 0;
    int later_esc_until = 0;
    int later_b_cap = 0;
    std::string mode = "exact";
    bool estimate_only = false;
    int thread_limit = 0;

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        auto need = [&](const char* name) -> std::string {
            if (i + 1 >= argc) {
                std::cerr << "missing value for " << name << "\n";
                std::exit(2);
            }
            return argv[++i];
        };
        if (a == "--points") points_path = need("--points");
        else if (a == "--distances") dist_path = need("--distances");
        else if (a == "--edges") edges_path = need("--edges");
        else if (a == "--sparse-eps") sparse_eps = std::stof(need("--sparse-eps"));
        else if (a == "--witness-n") witness_n = std::stoi(need("--witness-n"));
        else if (a == "--witness-nu") witness_nu = std::stoi(need("--witness-nu"));
        else if (a == "--knn") knn_k = std::stoi(need("--knn"));
        else if (a == "--gic-n") gic_n = std::stoi(need("--gic-n"));
        else if (a == "--gic-k") gic_k = std::stoi(need("--gic-k"));
        else if (a == "--reduced-vr") reduced_vr = true;
        else if (a == "--delaunay-vr") delaunay_vr = true;
        else if (a == "--delaunay-alpha") {
            const std::string v = need("--delaunay-alpha");
            if (v == "auto") delaunay_alpha_auto = true;
            else delaunay_alpha = std::stof(v);
        }
        else if (a == "--delaunay-adapt") delaunay_adapt = true;
        else if (a == "--delaunay-floor") delaunay_floor = std::stof(need("--delaunay-floor"));
        else if (a == "--sparse-cap") {
            const std::string v = need("--sparse-cap");
            if (v == "min") sparse_cap = SparseCap::Min;
            else if (v == "max") sparse_cap = SparseCap::Max;
            else {
                std::cerr << "unknown --sparse-cap " << v << "\n";
                return 2;
            }
        }
        else if (a == "--maxdim") maxdim = std::stoi(need("--maxdim"));
        else if (a == "--threshold") threshold = std::stof(need("--threshold"));
        else if (a == "--collapse") collapse_iters = std::stoi(need("--collapse"));
        else if (a == "--collapse-alg") collapse_alg = need("--collapse-alg");
        else if (a == "--suffix-mult") suffix_mult = std::stod(need("--suffix-mult"));
        else if (a == "--suffix-keep") suffix_keep = std::stoll(need("--suffix-keep"));
        else if (a == "--suffix-k") suffix_k = std::stoi(need("--suffix-k"));
        else if (a == "--later-b") later_b = true;
        else if (a == "--later-escalate") later_escalate = std::stoi(need("--later-escalate"));
        else if (a == "--later-esc-until") later_esc_until = std::stoi(need("--later-esc-until"));
        else if (a == "--later-b-cap") later_b_cap = std::stoi(need("--later-b-cap"));
        else if (a == "--dom-budget") dom_budget = std::stoi(need("--dom-budget"));
        else if (a == "--engine") engine = need("--engine");
        else if (a == "--ratio") ratio = std::stof(need("--ratio"));
        else if (a == "--no-enclosing") use_enclosing = false;
        else if (a == "--sparse-only") sparse_only = true;
        else if (a == "--probe-only") probe_only = true;
        else if (a == "--probe-vertex") probe_vertex = true;
        else if (a == "--format") format = need("--format");
        else if (a == "--mode") mode = need("--mode");
        else if (a == "--estimate") estimate_only = true;
        else if (a == "--threads") thread_limit = std::stoi(need("--threads"));
        else if (a == "--help-experimental") {
            usage_experimental();
            return 0;
        }
        else if (a == "--help" || a == "-h") {
            usage();
            return 0;
        } else {
            std::cerr << "unknown arg " << a << "\n";
            usage();
            return 2;
        }
    }
    if (mode == "scale") {
        delaunay_vr = true;
        delaunay_alpha_auto = true;
    } else if (mode == "sparse") {
        if (!(sparse_eps > 0 && sparse_eps < 1)) sparse_eps = static_cast<value_t>(0.6);
    } else if (mode != "exact") {
        std::cerr << "unknown --mode " << mode << " (use exact|scale|sparse)\n";
        return 2;
    }
    if (engine != "auto" && engine != "redzed" && engine != "implicit" && engine != "homology" &&
        engine != "active") {
        std::cerr << "unknown --engine " << engine << "\n";
        return 2;
    }
    if (thread_limit < 0) {
        std::cerr << "--threads must be >= 0 (0 = hardware)\n";
        return 2;
    }
    set_thread_limit(thread_limit);
    if (points_path.empty() && dist_path.empty() && edges_path.empty()) {
        usage();
        return 2;
    }

    try {
        Counters c;
        Graph g;
        Graph g_h2;
        bool delaunay_split = false;
        bool used_redzed_thicken = false;
        std::vector<std::vector<value_t>> dist;
        std::vector<std::vector<value_t>> pts;
        bool have_pts = false;
        bool auto_dispatch = false;
        if (!edges_path.empty()) {
            // I207: 1-skeleton input. Enclosing radius needs a full metric;
            // do not invent missing distances.
            g = read_edge_list(edges_path, threshold);
            c.n_distances = static_cast<std::int64_t>(g.edges.size());
        } else {
            if (!dist_path.empty()) {
                dist = read_distance_matrix(dist_path);
                c.n_distances = static_cast<std::int64_t>(dist.size()) * (dist.size() - 1) / 2;
            } else {
                pts = read_points(points_path);
                have_pts = true;
            }
            if (estimate_only) {
                return print_estimate(have_pts ? &pts : nullptr, dist.empty() ? nullptr : &dist,
                                      maxdim, threshold, format);
            }
            // I235/I236/I238: --engine auto. Probe first. Fat residual →
            // RedZeD without building the n×n vector<vector> (I238). Thin
            // → pairwise + collapse+implicit. H2 τ=0.15 (I236).
            const int n_metric = have_pts ? static_cast<int>(pts.size())
                                          : static_cast<int>(dist.size());
            // I241: H0 is Kruskal. Skip G_T + RedZeD on point clouds.
            if (engine == "auto" && maxdim < 1 && have_pts && gic_n == 0 && knn_k == 0 &&
                witness_n == 0 && !(sparse_eps > 0 && sparse_eps < 1) && !reduced_vr &&
                !delaunay_vr) {
                auto_dispatch = true;
                engine = "redzed";
            }
            if (engine == "auto" && maxdim >= 1 && gic_n == 0 && knn_k == 0 &&
                witness_n == 0 && !(sparse_eps > 0 && sparse_eps < 1) && !reduced_vr &&
                !delaunay_vr && n_metric >= 400) {
                auto_dispatch = true;
                c.residual_frac = have_pts ? probe_residual_frac_points(pts, threshold, 250)
                                           : probe_residual_frac(dist, threshold, 250);
                const double tau = (maxdim >= 2) ? 0.15 : 0.04;
                // I263: collapse residual on 250 pts can look thin on a
                // manifold (figure8 subsample collapses) while the full
                // G_T is still sparse enough for spatial+hash. Prefer
                // redzed when the edge-frac probe is < 0.25.
                const bool fat = c.residual_frac > tau;
                const bool hollow = have_pts && probe_edge_frac_points(pts, threshold) < 0.25;
                if (fat || hollow) engine = "redzed";
            }
            const bool skip_full_metric = ((engine == "redzed" || delaunay_vr) && have_pts &&
                                           gic_n == 0 && knn_k == 0 && witness_n == 0 &&
                                           !reduced_vr && !(sparse_eps > 0 && sparse_eps < 1));
            if (!skip_full_metric) {
                if (dist.empty() && have_pts) dist = pairwise(pts, c);
                if (use_enclosing && !dist.empty()) {
                    const value_t R = enclosing_radius(dist);
                    if (R < threshold) threshold = R;
                }
            }
            if (gic_n > 0) {
                // I222: flag of a kNN-quotient on farthest-point landmarks.
                g = gic_graph(dist, threshold, gic_n, gic_k);
                if (collapse_iters < 0) collapse_iters = 0;
            } else if (knn_k > 0) {
                // I220: flag of a symmetric kNN graph. Not exact VR.
                g = knn_flag_graph(dist, threshold, knn_k);
                if (collapse_iters < 0) collapse_iters = 0;
            } else if (witness_n > 0) {
                // I216: lazy witness on M farthest-point landmarks. PH is
                // on M vertices. Not exact VR — quantify loss vs Ripser.
                g = lazy_witness_graph(dist, threshold, witness_n, witness_nu);
                if (collapse_iters < 0) collapse_iters = 0;
            } else if (sparse_eps > 0 && sparse_eps < 1) {
                // I210: flag of a greedy-net sparse 1-skeleton. Default
                // collapse off — I207 found collapse is a tax on sparse graphs.
                g = sparse_rips_graph(dist, threshold, sparse_eps, sparse_cap);
                if (collapse_iters < 0) collapse_iters = 0;
            } else if (delaunay_vr && have_pts) {
                // I276: Delaunay 1-skeleton. I277–I282: H1 local-radius
                // thicken. I286: maxdim≥2 + thicken → H1 on the thick
                // graph, H2 on the α=1 flag (H2 thicken explodes tets).
                std::vector<Edge> de;
                auto fail_dvr = []() {
                    std::cerr << "--delaunay-vr requires Euclidean d=2 or d=3\n";
                    return 2;
                };
                if (pts.empty() || pts[0].empty()) return fail_dvr();
                const int dim_pts = static_cast<int>(pts[0].size());
                // I300: 3D + maxdim≥2 keeps the α=1 Delaunay flag. Thicken
                // H1 on a sphere is ~2 s of noise loops; the void is in H2.
                // 2D still thickens so figure8 finite H1 stays (I286).
                const bool want_thicken = (dim_pts < 3 || maxdim < 2) &&
                                          (delaunay_alpha_auto || delaunay_alpha > 1 ||
                                           delaunay_adapt || delaunay_floor > 0);
                value_t a = delaunay_alpha;
                if (delaunay_alpha_auto)
                    a = delaunay_auto_alpha(static_cast<int>(pts.size()));
                const int npts = static_cast<int>(pts.size());
                const auto t_dvr0 = std::chrono::steady_clock::now();
                if (maxdim >= 2 && want_thicken) {
                    // I298: one Delaunay; α=1 flag is that 1-skeleton;
                    // thicken extras append onto a copy.
                    std::vector<Edge> thin;
                    if (!delaunay_one_skeleton(pts, thin)) return fail_dvr();
                    de = thin;
                    if (!delaunay_thicken_extras(pts, threshold, a, de, delaunay_floor,
                                                 delaunay_adapt))
                        return fail_dvr();
                    g = graph_from_edge_list(npts, de, threshold);
                    g_h2 = graph_from_edge_list(npts, thin, threshold);
                    delaunay_split = true;
                } else {
                    if (maxdim >= 2) a = 1;
                    const value_t fl = (maxdim <= 1) ? delaunay_floor : value_t{0};
                    const bool ad = (maxdim <= 1) && delaunay_adapt;
                    if (!delaunay_vr_skeleton(pts, threshold, a, de, fl, ad)) return fail_dvr();
                    g = graph_from_edge_list(npts, de, threshold);
                }
                if (collapse_iters < 0) collapse_iters = 0;
                c.n_distances = static_cast<std::int64_t>(g.edges.size());
                const auto t_dvr1 = std::chrono::steady_clock::now();
                c.metric_ms = std::chrono::duration<double, std::milli>(t_dvr1 - t_dvr0).count();
            } else if (engine != "redzed") {
                g = graph_from_distance(dist, threshold);
            }
        }
        if (reduced_vr) collapse_iters = 0;  // I224: reduced VR is on G_T, not a residual
        if (engine == "redzed") collapse_iters = 0;  // I228: RedZeD is on the metric, not a residual
        if (engine == "active") collapse_iters = 0;  // I231: owned active H1 is on G_T
        if (delaunay_vr) collapse_iters = 0;  // I276: O(n) flag; I291 collapse is a tax at n≥4000
        c.n_vertices = g.n;
        c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
        if (probe_only) {
            const RoiProbe roi = probe_roi(g, threshold);
            const double dom = probe_domination(g, 64);
            std::cout << "# PROBE leftover_apparent=" << roi.leftover_apparent
                      << " leftover=" << roi.n_leftover
                      << " sampled=" << roi.n_sampled
                      << " mean_deg=" << roi.mean_deg
                      << " mst_max=" << roi.mst_max
                      << " leftover_median=" << roi.leftover_median
                      << " domination=" << dom
                      << " n=" << g.n
                      << " edges=" << g.edges.size()
                      << " T=" << threshold << "\n";
            return 0;
        }
        if (probe_vertex) {
            const VertexDomProbe vd = probe_vertex_domination(g);
            std::cout << "# VERTEX_DOM n=" << vd.n
                      << " n_dom=" << vd.n_dom
                      << " frac=" << vd.frac
                      << " star_edges=" << vd.star_edges
                      << " edges=" << g.edges.size()
                      << " T=" << threshold << "\n";
            return 0;
        }
        auto do_collapse = [&](Graph&& h, int iters) -> Graph {
            if (collapse_alg == "back-src")
                return collapse_edges(std::move(h), iters, c, dom_budget, false);
            if (collapse_alg == "back-bits" || collapse_alg == "back")
                return collapse_edges(std::move(h), iters, c, dom_budget, true);
            if (collapse_alg == "dc") return collapse_edges_dc(std::move(h), iters, c, dom_budget);
            if (collapse_alg == "forward") return collapse_edges_forward(std::move(h), iters, c);
            if (collapse_alg == "suffix")
                return collapse_edges_oldest_prefix(std::move(h), suffix_mult, c, suffix_keep);
            if (collapse_alg == "suffix-back")
                return collapse_edges_oldest_then_back(std::move(h), suffix_mult, c, dom_budget, suffix_keep);
            if (collapse_alg == "suffix-stab")
                return collapse_edges_suffix_stabilize(std::move(h), c, dom_budget);
            if (collapse_alg == "suffix-rescue")
                return collapse_edges_suffix_rescue(std::move(h), c, dom_budget);
            if (collapse_alg == "suffix-k")
                return collapse_edges_suffix_sample(std::move(h), c, dom_budget, suffix_k);
            if (collapse_alg == "suffix-later")
                return collapse_edges_suffix_later(std::move(h), c, dom_budget, suffix_k, later_b,
                                                  later_escalate, later_esc_until, later_b_cap);
            return collapse_edges(std::move(h), iters, c, dom_budget);
        };
        if (collapse_iters < 0) {
            if (maxdim < 1) {
                c.n_edges_out = c.n_edges_in;
            } else {
                g = do_collapse(std::move(g), 1);
                const double mean_deg = g.n ? (2.0 * static_cast<double>(g.edges.size()) / g.n) : 0;
                if (mean_deg > 6.0) g = do_collapse(std::move(g), 2);
            }
        } else if (collapse_iters > 0) {
            g = do_collapse(std::move(g), collapse_iters);
        } else {
            c.n_edges_out = c.n_edges_in;
        }

        if (sparse_only) {
            // Pin vertex count for Ripser --format sparse (i==j lines are ignored).
            int mx = 0;
            for (const auto& e : g.edges) mx = std::max(mx, std::max(e.u, e.v));
            if (g.n >= 2 && mx + 1 < g.n)
                std::cout << "0 " << (g.n - 1) << " 1e30\n";
            for (const auto& e : g.edges) std::cout << e.u << " " << e.v << " " << e.t << "\n";
            return 0;
        }

        // I137: Ripser-heap implicit is exact (8/8) and owns thick residuals
        // (torus1000 1.31× vs homology 0.20×). auto → implicit. homology stays
        // available for thin-residual A/B and H2 fallback inside implicit.
        // I224: --reduced-vr builds the Koyama–Mémoli–Robins–Turner 2-complex
        // and reduces those triangles (not the flag of G_T).
        const bool use_implicit = (engine == "implicit" || engine == "auto");
        Result r;
        if (engine == "redzed") {
            if (have_pts && dist.empty()) {
                r = persist_redzed_from_points(pts, maxdim, threshold);
                c.n_distances = r.counters.n_distances;
                c.metric_ms = r.counters.metric_ms;
            } else if (dist.empty()) {
                std::cerr << "--engine redzed requires --points or --distances\n";
                return 2;
            } else {
                r = persist_redzed(dist, maxdim, threshold);
            }
        } else if (engine == "active") {
            r = persist_active_h1(g, maxdim, threshold, ratio);
        } else if (reduced_vr) {
            const auto t_build0 = std::chrono::steady_clock::now();
            const auto rtris = build_reduced_triangles(g, threshold, dist.empty() ? nullptr : &dist);
            const auto t_build1 = std::chrono::steady_clock::now();
            c.collapse_ms = std::chrono::duration<double, std::milli>(t_build1 - t_build0).count();
            r = persist_triangles(g, rtris, maxdim, threshold, ratio);
        } else if (delaunay_split) {
            // I286: H0/H1 from the thickened 1-skeleton; H2 from the α=1
            // Delaunay flag. I297: fat thicken H1 via RedZeD (AE).
            // I300: H2 also RedZeD on the thin flag (implicit H2 on 80k
            // Delaunay edges was 1.7 s — flag tet tax).
            Result r1;
            if (delaunay_thicken_should_collapse(g.n, static_cast<std::int64_t>(g.edges.size()))) {
                r1 = persist_redzed_from_edges(g.n, g.edges, std::min(maxdim, 1), threshold);
                used_redzed_thicken = true;
            } else {
                r1 = persist_implicit_coh(g, std::min(maxdim, 1), threshold, ratio);
            }
            // 2D split only (3D maxdim≥2 no longer thickens). H2 on a
            // planar α=1 flag is cheap implicit; RedZeD H2 generate_stream
            // was a tax on figure8 n=16000 (0.76 vs 0.62 s).
            Result r2 = persist_implicit_coh(g_h2, maxdim, threshold, ratio);
            r.pairs.reserve(r1.pairs.size() + r2.pairs.size());
            for (const auto& p : r1.pairs)
                if (p.dim <= 1) r.pairs.push_back(p);
            for (const auto& p : r2.pairs)
                if (p.dim >= 2) r.pairs.push_back(p);
            r.counters = r1.counters;
            r.counters.n_simplices_enumerated += r2.counters.n_simplices_enumerated;
            r.counters.n_columns_assembled += r2.counters.n_columns_assembled;
            r.counters.n_columns_reduced += r2.counters.n_columns_reduced;
            r.counters.n_additions += r2.counters.n_additions;
            r.counters.n_cofacet_probes += r2.counters.n_cofacet_probes;
            r.counters.reduce_ms += r2.counters.reduce_ms;
            r.counters.n_vertices = g.n;
        } else if (delaunay_vr && maxdim >= 1) {
            r = persist_redzed_from_edges(g.n, g.edges, maxdim, threshold);
            used_redzed_thicken = true;
        } else {
            r = use_implicit ? persist_implicit_coh(g, maxdim, threshold, ratio)
                             : persist_sparse(g, maxdim, threshold, ratio);
        }
        const std::int64_t redzed_cc = r.counters.n_collapse_trims;
        if (!(engine == "redzed" && r.counters.n_distances > 0))
            r.counters.n_distances = c.n_distances;
        if (!(engine == "redzed" && r.counters.n_edges_in > 0))
            r.counters.n_edges_in = c.n_edges_in;
        r.counters.n_collapse_trims = (engine == "redzed" && redzed_cc > 0)
                                          ? redzed_cc
                                          : c.n_collapse_trims;
        r.counters.n_collapse_shifts = c.n_collapse_shifts;
        r.counters.n_collapse_c_probes = c.n_collapse_c_probes;
        r.counters.n_collapse_dom_tests = c.n_collapse_dom_tests;
        r.counters.n_collapse_dom_hits = c.n_collapse_dom_hits;
        r.counters.n_collapse_dom_skips = c.n_collapse_dom_skips;
        r.counters.n_collapse_killer_hits = c.n_collapse_killer_hits;
        r.counters.n_collapse_c_size_sum = c.n_collapse_c_size_sum;
        r.counters.n_collapse_shift_lookups = c.n_collapse_shift_lookups;
        r.counters.n_collapse_fast_trims = c.n_collapse_fast_trims;
        r.counters.n_collapse_vertex_trims = c.n_collapse_vertex_trims;
        r.counters.n_collapse_first_keep = c.n_collapse_first_keep;
        r.counters.n_collapse_tau_late = c.n_collapse_tau_late;
        r.counters.n_collapse_tau_late_common = c.n_collapse_tau_late_common;
        for (int b = 0; b < 16; ++b) r.counters.n_collapse_keep_hist[b] = c.n_collapse_keep_hist[b];
        for (int b = 0; b < 8; ++b) r.counters.n_collapse_early_keeps[b] = c.n_collapse_early_keeps[b];
        r.counters.n_collapse_early_keep_n = c.n_collapse_early_keep_n;
        r.counters.n_collapse_early_empty_c = c.n_collapse_early_empty_c;
        r.counters.n_collapse_early_fail_max = c.n_collapse_early_fail_max;
        r.counters.n_collapse_early_any_later = c.n_collapse_early_any_later;
        r.counters.n_collapse_early_later_a = c.n_collapse_early_later_a;
        r.counters.n_collapse_early_later_b = c.n_collapse_early_later_b;
        r.counters.collapse_ms = c.collapse_ms;
        if (!(engine == "redzed" && r.counters.metric_ms > 0))
            r.counters.metric_ms = c.metric_ms;
        r.counters.residual_frac = c.residual_frac;
        if (engine == "redzed") {
            if (maxdim < 1) {
                const bool del = r.counters.pipeline.find("delaunay") != std::string::npos;
                r.counters.pipeline = auto_dispatch ? "pith:auto-redzed-h0" : "pith:redzed-h0";
                if (del) r.counters.pipeline += "-delaunay";
            } else {
                const bool cc = r.counters.n_collapse_trims > 1;
                const bool spatial = r.counters.pipeline.find("spatial") != std::string::npos;
                r.counters.pipeline = auto_dispatch
                                          ? (cc ? "pith:auto-redzed-cc"
                                                : (spatial ? "pith:auto-redzed-spatial" : "pith:auto-redzed"))
                                          : (cc ? "pith:redzed-cc"
                                                : (spatial ? "pith:redzed-spatial" : "pith:redzed"));
            }
        } else if (engine == "active") {
            r.counters.n_vertices = g.n;
            if (r.counters.pipeline.empty()) r.counters.pipeline = "pith:active-h1";
        } else {
            r.counters.n_vertices = g.n;
            r.counters.pipeline = delaunay_vr
                                      ? (delaunay_split
                                             ? std::string("pith:delaunay-vr-split")
                                             : ((maxdim <= 1 && (delaunay_alpha_auto || delaunay_alpha > 1 ||
                                                                 delaunay_adapt || delaunay_floor > 0))
                                                    ? std::string(delaunay_alpha_auto
                                                                      ? "pith:delaunay-vr-auto"
                                                                      : (delaunay_adapt
                                                                             ? "pith:delaunay-vr-adapt"
                                                                             : "pith:delaunay-vr-alpha"))
                                                    : std::string("pith:delaunay-vr")))
                                      : (reduced_vr
                                             ? std::string("pith:reduced-vr")
                                             : (auto_dispatch
                                                    ? std::string("pith:auto-collapse")
                                                    : std::string("pith:threshold+collapse") +
                                                          std::to_string(collapse_iters) +
                                                          (use_implicit ? "+implicit_coh"
                                                                        : "+homology")));
            if (used_redzed_thicken) r.counters.pipeline += "-redzed";
        }
        std::sort(r.pairs.begin(), r.pairs.end(), [](const PersistencePair& a, const PersistencePair& b) {
            if (a.dim != b.dim) return a.dim < b.dim;
            if (a.birth != b.birth) return a.birth < b.birth;
            return a.death < b.death;
        });
        r.counters.rss_bytes_peak = peak_rss_bytes();
        r.counters.n_threads = nthreads();
        if (format == "json") print_json(r);
        else print_text(r);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }
}
