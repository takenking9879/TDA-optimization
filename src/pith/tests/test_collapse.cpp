#include "pith/edge_collapse.hpp"
#include "pith/persist.hpp"

#include <cassert>
#include <cmath>
#include <iostream>

using namespace pith;

static Graph from_edges(int n, std::initializer_list<Edge> es) {
    Graph g;
    g.n = n;
    g.edges.assign(es.begin(), es.end());
    rebuild_neighbors(g);
    return g;
}

static bool has_edge(const Graph& g, index_t u, index_t v) {
    if (u > v) std::swap(u, v);
    for (const auto& e : g.edges)
        if (e.u == u && e.v == v) return true;
    return false;
}

int main() {
    // C4: no common neighbors, all four edges remain.
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}});
        Counters c;
        Graph h = collapse_edges(g, 1, c);
        assert(h.edges.size() == 4);
        assert(c.n_collapse_trims == 0);
        std::cout << "ok C4 keep-4\n";
    }

    // C4 + late diagonals: later diagonal is dominated and trimmed.
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}, {0, 2, 2}, {1, 3, 2.1f}});
        Counters c;
        Graph h = collapse_edges(g, 1, c);
        assert(has_edge(h, 0, 1));
        assert(has_edge(h, 1, 2));
        assert(has_edge(h, 2, 3));
        assert(has_edge(h, 0, 3));
        assert(has_edge(h, 0, 2));
        assert(!has_edge(h, 1, 3));
        std::cout << "ok C4+diagonals trim later\n";
    }

    // Triangle: H1 should die at the last edge (zero-length bar if ratio=1 may be kept).
    {
        Graph g = from_edges(3, {{0, 1, 1}, {1, 2, 1}, {0, 2, 1}});
        Result r = persist_sparse(g, 1, 10, 1);
        int h0_ess = 0, h1 = 0;
        for (const auto& p : r.pairs) {
            if (p.dim == 0 && !std::isfinite(p.death)) ++h0_ess;
            if (p.dim == 1) ++h1;
        }
        assert(h0_ess == 1);
        std::cout << "ok triangle h0_ess=" << h0_ess << " h1_bars=" << h1 << "\n";
    }

    // Chordless C4: essential H1.
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}});
        Result r = persist_sparse(g, 1, 10, 1);
        int h1_ess = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++h1_ess;
        assert(h1_ess == 1);
        std::cout << "ok C4 essential H1\n";
    }

    // Implicit cohomology must match homology on triangle and C4 (I045).
    {
        Graph g = from_edges(3, {{0, 1, 1}, {1, 2, 1}, {0, 2, 1}});
        Result a = persist_sparse(g, 1, 10, 1);
        Result b = persist_implicit_coh(g, 1, 10, 1);
        int h1a = 0, h1b = 0;
        for (const auto& p : a.pairs)
            if (p.dim == 1) ++h1a;
        for (const auto& p : b.pairs)
            if (p.dim == 1) ++h1b;
        assert(h1a == h1b);
        std::cout << "ok implicit triangle H1 bars=" << h1b << "\n";
    }
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}});
        Result a = persist_sparse(g, 1, 10, 1);
        Result b = persist_implicit_coh(g, 1, 10, 1);
        int ea = 0, eb = 0;
        for (const auto& p : a.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ea;
        for (const auto& p : b.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++eb;
        assert(ea == 1 && eb == 1);
        std::cout << "ok implicit C4 essential H1\n";
    }

    std::cout << "all collapse/persist unit tests passed\n";
    return 0;
}
