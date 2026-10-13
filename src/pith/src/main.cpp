#include "pith/edge_collapse.hpp"
#include "pith/persist.hpp"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>

using namespace pith;

static void usage() {
    std::cerr
        << "PITH — Preprocessed Implicit Topology Homology\n"
        << "Usage: pith --points FILE.csv [options]\n"
        << "  --maxdim K          homology dimension (default 1)\n"
        << "  --threshold T       VR diameter threshold (default inf)\n"
        << "  --collapse N        backward edge-collapse passes (default 1; -1 = adaptive)\n"
        << "  --ratio R           skip pairs with death <= birth*R (default 1)\n"
        << "  --no-enclosing      do not cap T by enclosing radius\n"
        << "  --sparse-only       write residual edges and exit\n"
        << "  --format text|json  output format (default text)\n";
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
              << " cols_cleared=" << c.n_columns_cleared
              << " additions=" << c.n_additions
              << " cofacet_probes=" << c.n_cofacet_probes
              << " collapse_trims=" << c.n_collapse_trims
              << " collapse_shifts=" << c.n_collapse_shifts
              << " metric_ms=" << c.metric_ms
              << " collapse_ms=" << c.collapse_ms
              << " reduce_ms=" << c.reduce_ms
              << " rss=" << c.rss_bytes_peak << "\n";
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
              << "    \"n_columns_cleared\": " << c.n_columns_cleared << ",\n"
              << "    \"n_additions\": " << c.n_additions << ",\n"
              << "    \"n_cofacet_probes\": " << c.n_cofacet_probes << ",\n"
              << "    \"n_collapse_trims\": " << c.n_collapse_trims << ",\n"
              << "    \"n_collapse_shifts\": " << c.n_collapse_shifts << ",\n"
              << "    \"metric_ms\": " << c.metric_ms << ",\n"
              << "    \"collapse_ms\": " << c.collapse_ms << ",\n"
              << "    \"reduce_ms\": " << c.reduce_ms << ",\n"
              << "    \"rss_bytes_peak\": " << c.rss_bytes_peak << "\n"
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

int main(int argc, char** argv) {
    std::string points_path;
    int maxdim = 1;
    value_t threshold = kInf;
    int collapse_iters = -1;  // adaptive: extra passes if residual is thick
    value_t ratio = 1;
    bool use_enclosing = true;
    bool sparse_only = false;
    std::string format = "text";

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
        else if (a == "--maxdim") maxdim = std::stoi(need("--maxdim"));
        else if (a == "--threshold") threshold = std::stof(need("--threshold"));
        else if (a == "--collapse") collapse_iters = std::stoi(need("--collapse"));
        else if (a == "--ratio") ratio = std::stof(need("--ratio"));
        else if (a == "--no-enclosing") use_enclosing = false;
        else if (a == "--sparse-only") sparse_only = true;
        else if (a == "--format") format = need("--format");
        else if (a == "--help" || a == "-h") {
            usage();
            return 0;
        } else {
            std::cerr << "unknown arg " << a << "\n";
            usage();
            return 2;
        }
    }
    if (points_path.empty()) {
        usage();
        return 2;
    }

    try {
        Counters c;
        const auto pts = read_points(points_path);
        auto dist = pairwise(pts, c);
        if (use_enclosing) {
            const value_t R = enclosing_radius(dist);
            if (R < threshold) threshold = R;
        }
        Graph g = graph_from_distance(dist, threshold);
        c.n_vertices = g.n;
        c.n_edges_in = static_cast<std::int64_t>(g.edges.size());
        if (collapse_iters < 0) {
            g = collapse_edges(std::move(g), 1, c);
            const double mean_deg = g.n ? (2.0 * static_cast<double>(g.edges.size()) / g.n) : 0;
            if (mean_deg > 6.0) g = collapse_edges(std::move(g), 2, c);
        } else if (collapse_iters > 0) {
            g = collapse_edges(std::move(g), collapse_iters, c);
        } else {
            c.n_edges_out = c.n_edges_in;
        }

        if (sparse_only) {
            for (const auto& e : g.edges) std::cout << e.u << " " << e.v << " " << e.t << "\n";
            return 0;
        }

        Result r = persist_sparse(g, maxdim, threshold, ratio);
        r.counters.n_distances = c.n_distances;
        r.counters.n_edges_in = c.n_edges_in;
        r.counters.n_collapse_trims = c.n_collapse_trims;
        r.counters.n_collapse_shifts = c.n_collapse_shifts;
        r.counters.collapse_ms = c.collapse_ms;
        r.counters.metric_ms = c.metric_ms;
        r.counters.n_vertices = g.n;
        r.counters.pipeline = "pith:threshold+collapse" + std::to_string(collapse_iters) +
                              "+implicit_coh";
        std::sort(r.pairs.begin(), r.pairs.end(), [](const PersistencePair& a, const PersistencePair& b) {
            if (a.dim != b.dim) return a.dim < b.dim;
            if (a.birth != b.birth) return a.birth < b.birth;
            return a.death < b.death;
        });
        if (format == "json") print_json(r);
        else print_text(r);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "error: " << ex.what() << "\n";
        return 1;
    }
}
