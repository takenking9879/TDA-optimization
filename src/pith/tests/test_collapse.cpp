#include "pith/edge_collapse.hpp"
#include "pith/persist.hpp"

#include <algorithm>
#include <cassert>
#include <cmath>
#include <iostream>
#include <utility>
#include <vector>

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

    // I111: dense enough that MST-apparent triangles appear. Homology vs implicit
    // H1 barcodes must match (the I045 leftover-only apparent map failed here).
    {
        const int n = 8;
        Graph g;
        g.n = n;
        for (int i = 0; i < n; ++i) {
            for (int j = i + 1; j < n; ++j) {
                const int steps = std::min(j - i, n - (j - i));
                const float ang = static_cast<float>(2 * 3.14159265 * steps / n);
                g.edges.push_back({i, j, 2.f * std::sin(ang / 2.f)});
            }
        }
        rebuild_neighbors(g);
        Result a = persist_sparse(g, 1, 10, 1);
        Result b = persist_implicit_coh(g, 1, 10, 1);
        auto bars = [](const Result& r) {
            std::vector<std::pair<float, float>> out;
            for (const auto& p : r.pairs) {
                if (p.dim != 1) continue;
                out.push_back({p.birth, std::isfinite(p.death) ? p.death : 1e9f});
            }
            std::sort(out.begin(), out.end());
            return out;
        };
        auto ba = bars(a), bb = bars(b);
        assert(ba.size() == bb.size());
        for (size_t i = 0; i < ba.size(); ++i) {
            assert(std::fabs(ba[i].first - bb[i].first) < 1e-5);
            assert(std::fabs(ba[i].second - bb[i].second) < 1e-5);
        }
        std::cout << "ok implicit C8 vs homology H1 bars=" << ba.size() << "\n";
    }

    // I137: dense K6 with distinct times — I045 leftover-as-cohomology killer class.
    {
        Graph g;
        g.n = 6;
        int t = 1;
        for (int i = 0; i < 6; ++i) {
            for (int j = i + 1; j < 6; ++j) {
                g.edges.push_back({i, j, static_cast<float>(t++)});
            }
        }
        rebuild_neighbors(g);
        Result a = persist_sparse(g, 1, 100, 1);
        Result b = persist_implicit_coh(g, 1, 100, 1);
        auto bars = [](const Result& r) {
            std::vector<std::pair<float, float>> out;
            for (const auto& p : r.pairs) {
                if (p.dim != 1) continue;
                out.push_back({p.birth, std::isfinite(p.death) ? p.death : 1e9f});
            }
            std::sort(out.begin(), out.end());
            return out;
        };
        auto ba = bars(a), bb = bars(b);
        assert(ba.size() == bb.size());
        for (size_t i = 0; i < ba.size(); ++i) {
            assert(std::fabs(ba[i].first - bb[i].first) < 1e-5);
            assert(std::fabs(ba[i].second - bb[i].second) < 1e-5);
        }
        std::cout << "ok implicit K6 vs homology H1 bars=" << ba.size() << "\n";
    }

    // I149/I150: DC and forward keep PH of C4+diagonals (later diagonal trimmed
    // or barcode-equivalent). Compare H1 of collapsed graphs.
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}, {0, 2, 2}, {1, 3, 2.1f}});
        Counters cb, cd, cf;
        Graph hb = collapse_edges(g, 1, cb);
        Graph hd = collapse_edges_dc(g, 1, cd);
        Graph hf = collapse_edges_forward(g, 1, cf);
        Result rb = persist_sparse(hb, 1, 10, 1);
        Result rd = persist_sparse(hd, 1, 10, 1);
        Result rf = persist_sparse(hf, 1, 10, 1);
        auto h1 = [](const Result& r) {
            int ess = 0, fin = 0;
            for (const auto& p : r.pairs) {
                if (p.dim != 1) continue;
                if (std::isfinite(p.death)) ++fin;
                else ++ess;
            }
            return std::pair<int, int>{ess, fin};
        };
        assert(h1(rb) == h1(rd));
        assert(h1(rb) == h1(rf));
        std::cout << "ok dc/forward C4+diagonals H1 match backward\n";
        Counters cs;
        Graph hs = collapse_edges_suffix_stabilize(g, cs, -1);
        Result rs = persist_sparse(hs, 1, 10, 1);
        assert(h1(rb) == h1(rs));
        std::cout << "ok suffix-stab C4+diagonals H1 match backward\n";
        Counters cr;
        Graph hr = collapse_edges_suffix_rescue(g, cr, -1);
        Result rr = persist_sparse(hr, 1, 10, 1);
        assert(h1(rb) == h1(rr));
        std::cout << "ok suffix-rescue C4+diagonals H1 match backward\n";
        Counters ck;
        Graph hk = collapse_edges_suffix_sample(g, ck, -1, 0);
        Result rk = persist_sparse(hk, 1, 10, 1);
        assert(h1(rb) == h1(rk));
        std::cout << "ok suffix-k0 C4+diagonals H1 match backward\n";
        Counters cl;
        Graph hl = collapse_edges_suffix_later(g, cl, -1, 8);
        Result rl = persist_sparse(hl, 1, 10, 1);
        assert(h1(rb) == h1(rl));
        std::cout << "ok suffix-later C4+diagonals H1 match backward\n";
        Counters clb;
        Graph hlb = collapse_edges_suffix_later(g, clb, -1, 8, true);
        Result rlb = persist_sparse(hlb, 1, 10, 1);
        assert(h1(rb) == h1(rlb));
        std::cout << "ok suffix-later-B C4+diagonals H1 match backward\n";
        Counters cle;
        Graph hle = collapse_edges_suffix_later(g, cle, -1, 2, true, 8);
        Result rle = persist_sparse(hle, 1, 10, 1);
        assert(h1(rb) == h1(rle));
        std::cout << "ok suffix-later-esc C4+diagonals H1 match backward\n";
    }

    std::cout << "all collapse/persist unit tests passed\n";
    return 0;
}
