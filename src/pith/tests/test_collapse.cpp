#include "pith/edge_collapse.hpp"
#include "pith/persist.hpp"
#include "pith/persist_active.hpp"
#include "pith/reduced_vr.hpp"
#include "pith/redzed_bridge.hpp"
#include "pith/sparse_rips.hpp"

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
    // I214: obstruction stamp is per-edge; raising t past tau unblocks.
    {
        CannotDom cd;
        cd.ensure(4);
        cd.next();
        cd.mark(2, 1.5f, 3);
        assert(cd.blocked(2, 1.4f));
        assert(!cd.blocked(2, 1.5f));
        assert(cd.resume_at(2) == 3);
        assert(!cd.blocked(1, 0.f));
        cd.next();
        assert(!cd.blocked(2, 1.4f));
        assert(cd.resume_at(2) == 0);
        std::cout << "ok I214 CannotDom stamp\n";
    }

    // I219: a hint vertex with Tm > t rejects without needing the rest of C.
    {
        DenseTimes Tm(3);
        Tm.set(0, 1, 1);
        Tm.set(0, 2, 3);
        Tm.set(1, 2, 1);
        std::vector<index_t> C = {1, 2};
        index_t fail_w = -1;
        const bool rejected = !dominated_by(Tm, C, 0, 1.5f, nullptr, nullptr, 0, 2, &fail_w);
        if (!rejected || fail_w != 2) {
            std::cerr << "I219 hint reject failed\n";
            return 1;
        }
        if (!dominated_by(Tm, C, 0, 3.5f)) {
            std::cerr << "I219 full cover at t=3.5 failed\n";
            return 1;
        }
        std::cout << "ok I219 killer-first hint\n";
    }

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
        Counters cbits;
        Graph hbits = collapse_edges(g, 1, cbits, -1, true);
        Result rbits = persist_sparse(hbits, 1, 10, 1);
        assert(h1(rb) == h1(rbits));
        std::cout << "ok back-bits C4+diagonals H1 match backward\n";
    }

    // I207: 1-skeleton constructor keeps isolated vertices and C4 H1.
    {
        Graph g = graph_from_edge_list(5, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}}, 10);
        assert(g.n == 5);
        assert(g.edges.size() == 4);
        Result r = persist_implicit_coh(g, 1, 10, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        assert(ess1 == 1);
        std::cout << "ok edge-list C4+isolated H1\n";
    }

    // I210: sparse Rips on C4 keeps the essential loop and drops nothing
    // needed for H1; on a complete K4 it is a subgraph of G_T.
    {
        const value_t inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = 1;
        dist[1][2] = dist[2][1] = 1;
        dist[2][3] = dist[3][2] = 1;
        dist[3][0] = dist[0][3] = 1;
        dist[0][2] = dist[2][0] = 1.5f;
        dist[1][3] = dist[3][1] = 1.5f;
        Graph full = graph_from_distance(dist, inf);
        Graph sp = sparse_rips_graph(dist, inf, 0.5f, SparseCap::Max);
        Graph spmin = sparse_rips_graph(dist, inf, 0.5f, SparseCap::Min);
        assert(sp.n == 4);
        assert(sp.edges.size() <= full.edges.size());
        assert(spmin.edges.size() <= sp.edges.size());
        Result r = persist_implicit_coh(sp, 1, inf, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        assert(ess1 >= 1);
        std::cout << "ok sparse-rips C4 H1 edges=" << sp.edges.size() << "\n";
    }

    // I216: lazy witness on all 4 square vertices keeps essential H1.
    {
        const value_t inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = 1;
        dist[1][2] = dist[2][1] = 1;
        dist[2][3] = dist[3][2] = 1;
        dist[3][0] = dist[0][3] = 1;
        dist[0][2] = dist[2][0] = 1.5f;
        dist[1][3] = dist[3][1] = 1.5f;
        Graph lw = lazy_witness_graph(dist, inf, 4, 0);
        assert(lw.n == 4);
        Result r = persist_implicit_coh(lw, 1, inf, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        assert(ess1 >= 1);
        std::cout << "ok lazy-witness C4 H1 edges=" << lw.edges.size() << "\n";
    }

    // I220: kNN K=2 on C4 keeps the 4-cycle (each vertex has two neighbors).
    {
        const value_t inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = 1;
        dist[1][2] = dist[2][1] = 1;
        dist[2][3] = dist[3][2] = 1;
        dist[3][0] = dist[0][3] = 1;
        dist[0][2] = dist[2][0] = 1.5f;
        dist[1][3] = dist[3][1] = 1.5f;
        Graph kn = knn_flag_graph(dist, inf, 2);
        assert(kn.n == 4);
        assert(kn.edges.size() == 4);
        Result r = persist_implicit_coh(kn, 1, inf, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        assert(ess1 >= 1);
        std::cout << "ok knn-flag C4 H1 edges=" << kn.edges.size() << "\n";
    }

    // I222: GIC on all 4 C4 vertices with k=2 keeps a 1-cycle.
    {
        const value_t inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = 1;
        dist[1][2] = dist[2][1] = 1;
        dist[2][3] = dist[3][2] = 1;
        dist[3][0] = dist[0][3] = 1;
        dist[0][2] = dist[2][0] = 1.5f;
        dist[1][3] = dist[3][1] = 1.5f;
        Graph gic = gic_graph(dist, inf, 4, 2);
        assert(gic.n == 4);
        Result r = persist_implicit_coh(gic, 1, inf, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        assert(ess1 >= 1);
        std::cout << "ok gic C4 H1 edges=" << gic.edges.size() << "\n";
    }

    // I224: reduced VR on the unit square (distilled-VR counterexample).
    // At T just above the side length, H1 is essential. After the
    // diagonals enter, that class dies. Same path as any other metric.
    {
        const value_t s = 1, d = 1.41421356f, inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = s;
        dist[1][2] = dist[2][1] = s;
        dist[2][3] = dist[3][2] = s;
        dist[3][0] = dist[0][3] = s;
        dist[0][2] = dist[2][0] = d;
        dist[1][3] = dist[3][1] = d;
        Graph g = graph_from_distance(dist, inf);
        auto tris = build_reduced_triangles(g, inf);
        Result r = persist_triangles(g, tris, 1, inf, 1);
        int ess1 = 0, fin1 = 0;
        value_t birth = 0, death = 0;
        for (const auto& p : r.pairs) {
            if (p.dim != 1) continue;
            if (!std::isfinite(p.death)) ++ess1;
            else if (p.death - p.birth > 1e-5f) {
                ++fin1;
                birth = p.birth;
                death = p.death;
            }
        }
        if (ess1 != 0) {
            std::cerr << "reduced-vr unit square: expected 0 essential H1, got " << ess1 << "\n";
            return 1;
        }
        if (fin1 != 1) {
            std::cerr << "reduced-vr unit square: expected 1 finite H1, got " << fin1
                      << " tris=" << tris.size() << "\n";
            return 1;
        }
        if (std::fabs(birth - s) > 1e-3f || std::fabs(death - d) > 1e-3f) {
            std::cerr << "reduced-vr unit square: bar [" << birth << "," << death << ")\n";
            return 1;
        }
        Result full = persist_implicit_coh(g, 1, inf, 1);
        int full_fin = 0;
        for (const auto& p : full.pairs)
            if (p.dim == 1 && std::isfinite(p.death) && p.death - p.birth > 1e-5f) ++full_fin;
        if (full_fin != 1) {
            std::cerr << "unit square implicit finite H1=" << full_fin << "\n";
            return 1;
        }
        std::cout << "ok reduced-vr unit square H1 tris=" << tris.size() << "\n";
    }

    // I224: C4 without diagonals — essential H1, empty lunes, no triangles.
    {
        Graph g = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}});
        auto tris = build_reduced_triangles(g, 10);
        Result r = persist_triangles(g, tris, 1, 10, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "reduced-vr C4 ess H1=" << ess1 << " tris=" << tris.size() << "\n";
            return 1;
        }
        std::cout << "ok reduced-vr C4 essential H1 tris=" << tris.size() << "\n";
    }

    // I225: all-pairs-with-dist and neighbor-walk (no dist) emit the same
    // unit-square triangles (same lune components).
    {
        const value_t s = 1, d = 1.41421356f, inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = s;
        dist[1][2] = dist[2][1] = s;
        dist[2][3] = dist[3][2] = s;
        dist[3][0] = dist[0][3] = s;
        dist[0][2] = dist[2][0] = d;
        dist[1][3] = dist[3][1] = d;
        Graph g = graph_from_distance(dist, inf);
        auto a = build_reduced_triangles(g, inf, &dist);
        auto b = build_reduced_triangles(g, inf, nullptr);
        if (a.size() != b.size() || a.size() != 3) {
            std::cerr << "I225 triangle mismatch dist=" << a.size() << " nodist=" << b.size() << "\n";
            return 1;
        }
        std::cout << "ok reduced-vr I225 dist vs walk tris=" << a.size() << "\n";
    }

    // I228: vendored RedZeD on the unit square — same H1 as implicit / reduced VR.
    {
        const value_t s = 1, d = 1.41421356f, inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = s;
        dist[1][2] = dist[2][1] = s;
        dist[2][3] = dist[3][2] = s;
        dist[3][0] = dist[0][3] = s;
        dist[0][2] = dist[2][0] = d;
        dist[1][3] = dist[3][1] = d;
        Result rz = persist_redzed(dist, 1, inf);
        int ess1 = 0, fin1 = 0;
        value_t birth = 0, death = 0;
        for (const auto& p : rz.pairs) {
            if (p.dim != 1) continue;
            if (!std::isfinite(p.death)) ++ess1;
            else if (p.death - p.birth > 1e-5f) {
                ++fin1;
                birth = p.birth;
                death = p.death;
            }
        }
        if (ess1 != 0 || fin1 != 1) {
            std::cerr << "redzed unit square ess=" << ess1 << " fin=" << fin1 << "\n";
            return 1;
        }
        if (std::fabs(birth - s) > 1e-3f || std::fabs(death - d) > 1e-3f) {
            std::cerr << "redzed unit square bar [" << birth << "," << death << ")\n";
            return 1;
        }
        std::cout << "ok redzed unit square H1\n";
    }

    // I231: owned active H1 on the unit square and C4.
    {
        const value_t s = 1, d = 1.41421356f, inf = 10;
        std::vector<std::vector<value_t>> dist(4, std::vector<value_t>(4, 0));
        dist[0][1] = dist[1][0] = s;
        dist[1][2] = dist[2][1] = s;
        dist[2][3] = dist[3][2] = s;
        dist[3][0] = dist[0][3] = s;
        dist[0][2] = dist[2][0] = d;
        dist[1][3] = dist[3][1] = d;
        Graph g = graph_from_distance(dist, inf);
        Result ra = persist_active_h1(g, 1, inf, 1);
        int ess1 = 0, fin1 = 0;
        value_t birth = 0, death = 0;
        for (const auto& p : ra.pairs) {
            if (p.dim != 1) continue;
            if (!std::isfinite(p.death)) ++ess1;
            else if (p.death - p.birth > 1e-5f) {
                ++fin1;
                birth = p.birth;
                death = p.death;
            }
        }
        if (ess1 != 0 || fin1 != 1) {
            std::cerr << "active unit square ess=" << ess1 << " fin=" << fin1 << "\n";
            return 1;
        }
        if (std::fabs(birth - s) > 1e-3f || std::fabs(death - d) > 1e-3f) {
            std::cerr << "active unit square bar [" << birth << "," << death << ")\n";
            return 1;
        }
        Graph c4 = from_edges(4, {{0, 1, 1}, {1, 2, 1}, {2, 3, 1}, {0, 3, 1}});
        Result rc = persist_active_h1(c4, 1, 10, 1);
        int cess = 0;
        for (const auto& p : rc.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++cess;
        if (cess != 1) {
            std::cerr << "active C4 ess H1=" << cess << "\n";
            return 1;
        }
        std::cout << "ok active-h1 unit square + C4\n";
    }

    // I234: regular octahedron, T between √2 and 2 — essential H2, no H1.
    {
        const value_t T = 1.5f;
        std::vector<std::vector<value_t>> pts = {
            {1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1},
        };
        std::vector<std::vector<value_t>> dist(6, std::vector<value_t>(6, 0));
        for (int i = 0; i < 6; ++i)
            for (int j = i + 1; j < 6; ++j) {
                value_t d = 0;
                for (int k = 0; k < 3; ++k) {
                    const value_t u = pts[i][k] - pts[j][k];
                    d += u * u;
                }
                d = std::sqrt(d);
                dist[i][j] = dist[j][i] = d;
            }
        Graph g = graph_from_distance(dist, T);
        Result ra = persist_active_h1(g, 2, T, 1);
        int ess0 = 0, ess1 = 0, ess2 = 0, fin2 = 0;
        for (const auto& p : ra.pairs) {
            if (!std::isfinite(p.death)) {
                if (p.dim == 0) ++ess0;
                if (p.dim == 1) ++ess1;
                if (p.dim == 2) ++ess2;
            } else if (p.dim == 2 && p.death - p.birth > 1e-5f) {
                ++fin2;
            }
        }
        if (ess0 != 1 || ess1 != 0 || ess2 != 1 || fin2 != 0) {
            std::cerr << "active octahedron H0/H1/H2 ess=" << ess0 << "/" << ess1 << "/"
                      << ess2 << " fin2=" << fin2 << "\n";
            return 1;
        }
        std::cout << "ok active-h012 octahedron\n";
    }

    // I239: two unit squares far apart — G_T has 2 components; PH is the sum.
    {
        const value_t T = 2.0f;
        std::vector<std::vector<value_t>> pts = {
            {0, 0}, {1, 0}, {1, 1}, {0, 1}, {10, 0}, {11, 0}, {11, 1}, {10, 1},
        };
        std::vector<std::vector<value_t>> dist(8, std::vector<value_t>(8, 0));
        for (int i = 0; i < 8; ++i) {
            for (int j = i + 1; j < 8; ++j) {
                const value_t dx = pts[i][0] - pts[j][0];
                const value_t dy = pts[i][1] - pts[j][1];
                dist[i][j] = dist[j][i] = std::sqrt(dx * dx + dy * dy);
            }
        }
        Result rz = persist_redzed(dist, 1, T);
        int ess0 = 0, ess1 = 0, fin1 = 0;
        for (const auto& p : rz.pairs) {
            if (!std::isfinite(p.death)) {
                if (p.dim == 0) ++ess0;
                if (p.dim == 1) ++ess1;
            } else if (p.dim == 1 && p.death - p.birth > 1e-5f) {
                ++fin1;
            }
        }
        if (ess0 != 2 || ess1 != 0 || fin1 != 2) {
            std::cerr << "I239 two-squares ess0/ess1/fin1=" << ess0 << "/" << ess1 << "/" << fin1
                      << "\n";
            return 1;
        }
        if (rz.counters.n_collapse_trims != 2) {
            std::cerr << "I239 two-squares cc=" << rz.counters.n_collapse_trims << "\n";
            return 1;
        }
        Graph g = graph_from_distance(dist, T);
        Result im = persist_implicit_coh(g, 1, T, 1);
        int iess0 = 0, ifin1 = 0;
        for (const auto& p : im.pairs) {
            if (p.dim == 0 && !std::isfinite(p.death)) ++iess0;
            if (p.dim == 1 && std::isfinite(p.death) && p.death - p.birth > 1e-5f) ++ifin1;
        }
        if (iess0 != 2 || ifin1 != 2) {
            std::cerr << "I239 implicit two-squares " << iess0 << " " << ifin1 << "\n";
            return 1;
        }
        Result rzp = persist_redzed_from_points(pts, 1, T);
        int pess0 = 0, pfin1 = 0;
        for (const auto& p : rzp.pairs) {
            if (p.dim == 0 && !std::isfinite(p.death)) ++pess0;
            if (p.dim == 1 && std::isfinite(p.death) && p.death - p.birth > 1e-5f) ++pfin1;
        }
        if (pess0 != 2 || pfin1 != 2 || rzp.counters.n_collapse_trims != 2) {
            std::cerr << "I239 from-points two-squares\n";
            return 1;
        }
        // I240: two 4-point blocks → 2*(4 choose 2)=12, not 8 choose 2=28.
        if (rzp.counters.n_distances != 12) {
            std::cerr << "I240 two-squares n_distances=" << rzp.counters.n_distances << "\n";
            return 1;
        }
        Result h0 = persist_redzed_from_points(pts, 0, T);
        int h0ess = 0, h0fin = 0;
        for (const auto& p : h0.pairs) {
            if (p.dim != 0) continue;
            if (!std::isfinite(p.death)) ++h0ess;
            else if (p.death - p.birth > 1e-5f) ++h0fin;
        }
        if (h0ess != 2 || h0fin != 6) {
            std::cerr << "I241 H0 two-squares ess/fin=" << h0ess << "/" << h0fin << "\n";
            return 1;
        }
        std::cout << "ok I239 two-squares cc-split\n";
        std::cout << "ok I241 two-squares H0 Kruskal\n";
    }

    // I239: two octahedra far apart — H0=2 and H2=2 (wedge of voids).
    {
        const value_t T = 1.5f;
        const value_t oct[6][3] = {
            {1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1},
        };
        std::vector<std::vector<value_t>> pts;
        pts.reserve(12);
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0], oct[i][1], oct[i][2]});
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0] + 8, oct[i][1], oct[i][2]});
        Result rz = persist_redzed_from_points(pts, 2, T);
        int ess0 = 0, ess1 = 0, ess2 = 0, fin2 = 0;
        for (const auto& p : rz.pairs) {
            if (!std::isfinite(p.death)) {
                if (p.dim == 0) ++ess0;
                if (p.dim == 1) ++ess1;
                if (p.dim == 2) ++ess2;
            } else if (p.dim == 2 && p.death - p.birth > 1e-5f) {
                ++fin2;
            }
        }
        if (ess0 != 2 || ess1 != 0 || ess2 != 2 || fin2 != 0) {
            std::cerr << "I239 two-octahedra H0/H1/H2 ess=" << ess0 << "/" << ess1 << "/" << ess2
                      << " fin2=" << fin2 << "\n";
            return 1;
        }
        if (rz.counters.n_collapse_trims != 2) {
            std::cerr << "I239 two-octahedra cc=" << rz.counters.n_collapse_trims << "\n";
            return 1;
        }
        std::cout << "ok I239 two-octahedra H012 cc-split\n";
    }

    std::cout << "all collapse/persist unit tests passed\n";
    return 0;
}
