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
#include <string>
#include <tuple>
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

    // I313: implicit cohomology H2 must match persist_sparse (homology) barcodes.
    {
        auto h2_bars = [](const Result& r) {
            std::vector<std::pair<float, float>> out;
            int ess = 0;
            for (const auto& p : r.pairs) {
                if (p.dim != 2) continue;
                if (!std::isfinite(p.death))
                    ++ess;
                else
                    out.push_back({p.birth, p.death});
            }
            std::sort(out.begin(), out.end());
            return std::pair<int, std::vector<std::pair<float, float>>>{ess, out};
        };
        auto match_h2 = [&](const Graph& g, value_t T, const char* tag) -> bool {
            Result a = persist_sparse(g, 2, T, 1);
            Result b = persist_implicit_coh(g, 2, T, 1);
            auto ba = h2_bars(a), bb = h2_bars(b);
            if (ba.first != bb.first || ba.second.size() != bb.second.size()) {
                std::cerr << "I313 " << tag << " ess/fin=" << bb.first << "/" << bb.second.size()
                          << " vs sparse " << ba.first << "/" << ba.second.size() << "\n";
                return false;
            }
            for (size_t i = 0; i < ba.second.size(); ++i) {
                if (std::fabs(ba.second[i].first - bb.second[i].first) > 1e-5f ||
                    std::fabs(ba.second[i].second - bb.second[i].second) > 1e-5f) {
                    std::cerr << "I313 " << tag << " bar mismatch\n";
                    return false;
                }
            }
            return true;
        };

        Graph k6;
        k6.n = 6;
        int t = 1;
        for (int i = 0; i < 6; ++i)
            for (int j = i + 1; j < 6; ++j)
                k6.edges.push_back({i, j, static_cast<float>(t++)});
        rebuild_neighbors(k6);
        if (!match_h2(k6, 100, "K6")) return 1;
        std::cout << "ok implicit K6 vs homology H2\n";

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
                dist[i][j] = dist[j][i] = std::sqrt(d);
            }
        Graph oct = graph_from_distance(dist, T);
        if (!match_h2(oct, T, "octahedron")) return 1;
        Result ro = persist_implicit_coh(oct, 2, T, 1);
        int ess2 = 0;
        for (const auto& p : ro.pairs)
            if (p.dim == 2 && !std::isfinite(p.death)) ++ess2;
        if (ess2 != 1) {
            std::cerr << "I313 octahedron ess H2=" << ess2 << "\n";
            return 1;
        }
        std::cout << "ok implicit octahedron vs homology H2 ess=1\n";
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

    // Euclidean points-path sparse Rips must match the dense-matrix path
    // (same FPS, same keep predicate) on C4, a noisy 2D cloud, and a 3D tet.
    {
        auto same_edges = [](Graph a, Graph b) -> bool {
            if (a.n != b.n || a.edges.size() != b.edges.size()) return false;
            auto key = [](const Edge& e) {
                Edge x = e;
                normalize_edge(x);
                return std::tuple<index_t, index_t, value_t>(x.u, x.v, x.t);
            };
            std::sort(a.edges.begin(), a.edges.end(),
                      [&](const Edge& p, const Edge& q) { return key(p) < key(q); });
            std::sort(b.edges.begin(), b.edges.end(),
                      [&](const Edge& p, const Edge& q) { return key(p) < key(q); });
            for (size_t i = 0; i < a.edges.size(); ++i) {
                if (key(a.edges[i]) != key(b.edges[i])) return false;
            }
            return true;
        };
        auto pairwise_pts = [](const std::vector<std::vector<value_t>>& pts) {
            const int n = static_cast<int>(pts.size());
            std::vector<std::vector<value_t>> dist(static_cast<size_t>(n),
                                                   std::vector<value_t>(static_cast<size_t>(n), 0));
            for (int i = 0; i < n; ++i)
                for (int j = i + 1; j < n; ++j) {
                    const value_t d = euclid_dist(pts, i, j);
                    dist[static_cast<size_t>(i)][static_cast<size_t>(j)] =
                        dist[static_cast<size_t>(j)][static_cast<size_t>(i)] = d;
                }
            return dist;
        };
        const std::vector<std::vector<value_t>> c4 = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
        const auto d4 = pairwise_pts(c4);
        // T below the diagonal: both paths keep the 4-cycle.
        Graph m4 = sparse_rips_graph(d4, 1.2f, 0.6f, SparseCap::Max);
        Graph p4 = sparse_rips_graph_points(c4, 1.2f, 0.6f, SparseCap::Max);
        if (!same_edges(m4, p4) || m4.edges.size() != 4) {
            std::cerr << "points-path C4 mismatch edges=" << p4.edges.size()
                      << " matrix=" << m4.edges.size() << "\n";
            return 1;
        }
        Result rc4 = persist_implicit_coh(p4, 1, 1.2f, 1);
        Result rm4 = persist_implicit_coh(m4, 1, 1.2f, 1);
        int ess1 = 0;
        for (const auto& p : rc4.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 < 1 || rc4.pairs.size() != rm4.pairs.size()) {
            std::cerr << "points-path C4 PH mismatch ess1=" << ess1 << "\n";
            return 1;
        }
        Graph m4b = sparse_rips_graph(d4, 2.0f, 0.6f, SparseCap::Max);
        Graph p4b = sparse_rips_graph_points(c4, 2.0f, 0.6f, SparseCap::Max);
        if (!same_edges(m4b, p4b)) {
            std::cerr << "points-path C4 T=2 mismatch\n";
            return 1;
        }
        std::vector<std::vector<value_t>> cloud;
        cloud.reserve(48);
        for (int i = 0; i < 48; ++i) {
            const value_t ang = static_cast<value_t>(0.1309 * i);
            const value_t jitter = static_cast<value_t>((i % 5) * 0.01);
            cloud.push_back({std::cos(ang) + jitter, std::sin(ang) - jitter});
        }
        const auto dc = pairwise_pts(cloud);
        {
            const auto lam_m = greedy_insertion_radii(dc);
            const auto lam_p = greedy_insertion_radii_points(cloud);
            if (lam_m.size() != lam_p.size()) {
                std::cerr << "FPS λ length mismatch\n";
                return 1;
            }
            for (size_t i = 0; i < lam_m.size(); ++i) {
                if (std::fabs(static_cast<double>(lam_m[i] - lam_p[i])) > 1e-5) {
                    std::cerr << "FPS λ mismatch i=" << i << " matrix=" << lam_m[i]
                              << " points=" << lam_p[i] << "\n";
                    return 1;
                }
            }
            std::cout << "ok FPS λ points==matrix n=" << lam_m.size() << "\n";
        }
        {
            // I327: dyadic net is cheaper than Θ(n²) FPS and still a cover.
            std::int64_t n_dy = 0, n_fps = 0;
            const auto lam_d = dyadic_insertion_radii_points(cloud, &n_dy);
            const auto lam_f = greedy_insertion_radii_points(cloud, &n_fps);
            if (lam_d.size() != cloud.size() || !(lam_d[0] > 0)) {
                std::cerr << "dyadic λ empty/cover\n";
                return 1;
            }
            const std::int64_t pairs =
                static_cast<std::int64_t>(cloud.size()) * (static_cast<std::int64_t>(cloud.size()) - 1);
            if (n_dy >= pairs / 4) {
                std::cerr << "dyadic not subquadratic n_dist=" << n_dy << " fps=" << n_fps << "\n";
                return 1;
            }
            Graph pd = sparse_rips_graph_points(cloud, 1.5f, 0.6f, SparseCap::Max, nullptr,
                                                SparseNet::Dyadic);
            Result rd = persist_implicit_coh(pd, 1, 1.5f, 1);
            int ess1 = 0;
            for (const auto& p : rd.pairs)
                if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
            if (ess1 < 1) {
                std::cerr << "dyadic noisy-circle lost ess H1 edges=" << pd.edges.size() << "\n";
                return 1;
            }
            Graph c4d = sparse_rips_graph_points(c4, 1.2f, 0.6f, SparseCap::Max, nullptr,
                                                 SparseNet::Dyadic);
            Result rc4d = persist_implicit_coh(c4d, 1, 1.2f, 1);
            int ess4 = 0;
            for (const auto& p : rc4d.pairs)
                if (p.dim == 1 && !std::isfinite(p.death)) ++ess4;
            if (ess4 < 1) {
                std::cerr << "dyadic C4 lost the 4-cycle edges=" << c4d.edges.size() << "\n";
                return 1;
            }
            std::cout << "ok dyadic-net n_dist=" << n_dy << " fps=" << n_fps
                      << " ess1=" << ess1 << "\n";
        }
        {
            // I331: n<256 falls back to exact FPS (sample overhead is a tax).
            // Medium n: fewer distances than Gonzalez, must not densify, keep ess H1.
            std::int64_t n_small = 0;
            const auto lam_s = approx_insertion_radii_points(cloud, &n_small);
            if (lam_s.size() != cloud.size() || !(lam_s[0] > 0)) {
                std::cerr << "approx small λ empty/cover\n";
                return 1;
            }
            std::vector<std::vector<value_t>> med;
            med.reserve(320);
            for (int i = 0; i < 320; ++i) {
                const value_t ang = static_cast<value_t>(0.019635 * i);
                const value_t jitter = static_cast<value_t>((i % 7) * 0.008);
                med.push_back({std::cos(ang) + jitter, std::sin(ang) - jitter});
            }
            std::int64_t n_ap = 0, n_fps = 0;
            const auto lam_a = approx_insertion_radii_points(med, &n_ap);
            const auto lam_f = greedy_insertion_radii_points(med, &n_fps);
            if (lam_a.size() != med.size() || !(lam_a[0] > 0)) {
                std::cerr << "approx λ empty/cover\n";
                return 1;
            }
            if (n_ap >= n_fps) {
                std::cerr << "approx not cheaper n_dist=" << n_ap << " fps=" << n_fps << "\n";
                return 1;
            }
            Graph pa = sparse_rips_graph_points(med, 1.5f, 0.6f, SparseCap::Max, nullptr,
                                                SparseNet::Approx);
            Graph pf = sparse_rips_graph_points(med, 1.5f, 0.6f, SparseCap::Max, nullptr,
                                                SparseNet::Fps);
            if (pa.edges.size() > pf.edges.size() * 3 + 32) {
                std::cerr << "approx densified edges=" << pa.edges.size() << " fps=" << pf.edges.size()
                          << "\n";
                return 1;
            }
            Result ra = persist_implicit_coh(pa, 1, 1.5f, 1);
            int ess1 = 0;
            for (const auto& p : ra.pairs)
                if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
            if (ess1 < 1) {
                std::cerr << "approx noisy-circle lost ess H1 edges=" << pa.edges.size() << "\n";
                return 1;
            }
            std::cout << "ok approx-net n_dist=" << n_ap << " fps=" << n_fps
                      << " edges=" << pa.edges.size() << "/" << pf.edges.size()
                      << " ess1=" << ess1 << "\n";
            // I333: prefix net is on m<<n vertices, cheaper than Θ(n²), keeps ess H1.
            std::int64_t n_pr = 0, n_fps2 = 0;
            Graph ppre = sparse_rips_graph_points(med, 1.5f, 0.6f, SparseCap::Max, &n_pr,
                                                  SparseNet::Prefix);
            Graph pf2 = sparse_rips_graph_points(med, 1.5f, 0.6f, SparseCap::Max, &n_fps2,
                                                 SparseNet::Fps);
            const int want_m = prefix_landmark_count(static_cast<int>(med.size()));
            if (ppre.n != want_m || ppre.n >= static_cast<int>(med.size())) {
                std::cerr << "prefix n=" << ppre.n << " want=" << want_m << "\n";
                return 1;
            }
            if (n_pr >= n_fps2) {
                std::cerr << "prefix not cheaper n_dist=" << n_pr << " fps=" << n_fps2 << "\n";
                return 1;
            }
            Result rp = persist_implicit_coh(ppre, 1, 1.5f, 1);
            int essp = 0;
            for (const auto& p : rp.pairs)
                if (p.dim == 1 && !std::isfinite(p.death)) ++essp;
            if (essp < 1) {
                std::cerr << "prefix noisy-circle lost ess H1 n=" << ppre.n
                          << " edges=" << ppre.edges.size() << "\n";
                return 1;
            }
            std::cout << "ok prefix-net n_dist=" << n_pr << " fps=" << n_fps2
                      << " verts=" << ppre.n << "/" << med.size()
                      << " edges=" << ppre.edges.size() << "/" << pf2.edges.size()
                      << " ess1=" << essp << "\n";
        }
        for (SparseCap cap : {SparseCap::Max, SparseCap::Min}) {
            Graph mm = sparse_rips_graph(dc, 1.5f, 0.6f, cap);
            Graph pp = sparse_rips_graph_points(cloud, 1.5f, 0.6f, cap);
            if (!same_edges(mm, pp)) {
                std::cerr << "points-path noisy circle mismatch cap="
                          << (cap == SparseCap::Min ? "min" : "max") << "\n";
                return 1;
            }
        }
        const std::vector<std::vector<value_t>> tet = {
            {0, 0, 0}, {1, 0, 0}, {0.5f, 0.866f, 0}, {0.5f, 0.289f, 0.816f}};
        const auto dt = pairwise_pts(tet);
        Graph mt = sparse_rips_graph(dt, 2.0f, 0.6f, SparseCap::Max);
        Graph pt = sparse_rips_graph_points(tet, 2.0f, 0.6f, SparseCap::Max);
        if (!same_edges(mt, pt)) {
            std::cerr << "points-path tet mismatch\n";
            return 1;
        }
        std::cout << "ok sparse-rips points==matrix C4/cloud/tet\n";
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

    // I271: n=256 2D H0 Delaunay (walk-locate) matches all-pairs Kruskal.
    {
        const int n = 256;
        const value_t T = 0.35f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        uint32_t s = 0xC0FFEEu;
        for (int i = 0; i < n; ++i) {
            s = s * 1664525u + 1013904223u;
            pts[static_cast<size_t>(i)][0] = static_cast<value_t>((s >> 8) & 0xffffu) / 65535.0f;
            s = s * 1664525u + 1013904223u;
            pts[static_cast<size_t>(i)][1] = static_cast<value_t>((s >> 8) & 0xffffu) / 65535.0f;
        }
        std::vector<std::vector<value_t>> dist(static_cast<size_t>(n), std::vector<value_t>(static_cast<size_t>(n), 0));
        for (int i = 0; i < n; ++i)
            for (int j = i + 1; j < n; ++j) {
                const value_t dx = pts[static_cast<size_t>(i)][0] - pts[static_cast<size_t>(j)][0];
                const value_t dy = pts[static_cast<size_t>(i)][1] - pts[static_cast<size_t>(j)][1];
                dist[static_cast<size_t>(i)][static_cast<size_t>(j)] =
                    dist[static_cast<size_t>(j)][static_cast<size_t>(i)] = std::sqrt(dx * dx + dy * dy);
            }
        Result del = persist_redzed_from_points(pts, 0, T);
        Result full = persist_redzed(dist, 0, T);
        auto deaths = [](const Result& r) {
            std::vector<value_t> d;
            int ess = 0;
            for (const auto& p : r.pairs) {
                if (p.dim != 0) continue;
                if (!std::isfinite(p.death)) ++ess;
                else d.push_back(p.death);
            }
            std::sort(d.begin(), d.end());
            return std::pair<int, std::vector<value_t>>{ess, d};
        };
        const auto a = deaths(del), b = deaths(full);
        if (a.first != b.first || a.second.size() != b.second.size()) {
            std::cerr << "I271 H0 Delaunay count " << a.first << "/" << a.second.size() << " vs "
                      << b.first << "/" << b.second.size() << "\n";
            return 1;
        }
        for (size_t i = 0; i < a.second.size(); ++i) {
            if (std::abs(a.second[i] - b.second[i]) > 1e-5f) {
                std::cerr << "I271 H0 Delaunay death mismatch\n";
                return 1;
            }
        }
        if (del.counters.pipeline.find("delaunay") == std::string::npos) {
            std::cerr << "I271 expected delaunay pipeline " << del.counters.pipeline << "\n";
            return 1;
        }
        std::cout << "ok I271 walk-locate Delaunay H0 n=256\n";
    }

    // I274/I275: n=256 3D H0 Delaunay matches all-pairs Kruskal.
    {
        const int n = 256;
        const value_t T = 0.55f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(3));
        uint32_t s = 0xBADC0DEu;
        for (int i = 0; i < n; ++i) {
            for (int k = 0; k < 3; ++k) {
                s = s * 1664525u + 1013904223u;
                pts[static_cast<size_t>(i)][static_cast<size_t>(k)] =
                    static_cast<value_t>((s >> 8) & 0xffffu) / 65535.0f;
            }
        }
        std::vector<std::vector<value_t>> dist(static_cast<size_t>(n),
                                              std::vector<value_t>(static_cast<size_t>(n), 0));
        for (int i = 0; i < n; ++i)
            for (int j = i + 1; j < n; ++j) {
                value_t acc = 0;
                for (int k = 0; k < 3; ++k) {
                    const value_t d = pts[static_cast<size_t>(i)][static_cast<size_t>(k)] -
                                      pts[static_cast<size_t>(j)][static_cast<size_t>(k)];
                    acc += d * d;
                }
                dist[static_cast<size_t>(i)][static_cast<size_t>(j)] =
                    dist[static_cast<size_t>(j)][static_cast<size_t>(i)] = std::sqrt(acc);
            }
        Result del = persist_redzed_from_points(pts, 0, T);
        Result full = persist_redzed(dist, 0, T);
        auto deaths = [](const Result& r) {
            std::vector<value_t> d;
            int ess = 0;
            for (const auto& p : r.pairs) {
                if (p.dim != 0) continue;
                if (!std::isfinite(p.death)) ++ess;
                else d.push_back(p.death);
            }
            std::sort(d.begin(), d.end());
            return std::pair<int, std::vector<value_t>>{ess, d};
        };
        const auto a = deaths(del), b = deaths(full);
        if (a.first != b.first || a.second.size() != b.second.size()) {
            std::cerr << "I275 H0 3D Delaunay count " << a.first << "/" << a.second.size() << " vs "
                      << b.first << "/" << b.second.size() << "\n";
            return 1;
        }
        for (size_t i = 0; i < a.second.size(); ++i) {
            if (std::abs(a.second[i] - b.second[i]) > 1e-4f) {
                std::cerr << "I275 H0 3D Delaunay death mismatch\n";
                return 1;
            }
        }
        if (del.counters.pipeline.find("delaunay") == std::string::npos) {
            std::cerr << "I275 expected delaunay pipeline " << del.counters.pipeline << "\n";
            return 1;
        }
        std::cout << "ok I275 walk-locate 3D Delaunay H0 n=256\n";
        std::vector<Edge> e0, e1;
        if (!delaunay_one_skeleton(pts, e0)) {
            std::cerr << "I328 default 3D skeleton failed\n";
            return 1;
        }
        set_delaunay_jump(true);
        if (!delaunay_one_skeleton(pts, e1)) {
            set_delaunay_jump(false);
            std::cerr << "I328 jump 3D skeleton failed\n";
            return 1;
        }
        set_delaunay_jump(false);
        if (e0.size() != e1.size()) {
            std::cerr << "I328 jump |E| " << e1.size() << " vs " << e0.size() << "\n";
            return 1;
        }
        std::cout << "ok I328 3D jump-locate |E|=" << e0.size() << "\n";
        set_delaunay_hier(true);
        std::vector<Edge> e2;
        if (!delaunay_one_skeleton(pts, e2)) {
            set_delaunay_hier(false);
            std::cerr << "I329 hier 3D skeleton failed\n";
            return 1;
        }
        set_delaunay_hier(false);
        if (e0.size() != e2.size()) {
            std::cerr << "I329 hier |E| " << e2.size() << " vs " << e0.size() << "\n";
            return 1;
        }
        std::cout << "ok I329 3D hierarchy |E|=" << e0.size() << "\n";
        set_delaunay_devillers(true);
        std::vector<Edge> e3;
        if (!delaunay_one_skeleton(pts, e3)) {
            set_delaunay_devillers(false);
            std::cerr << "I332 Devillers 3D skeleton failed\n";
            return 1;
        }
        set_delaunay_devillers(false);
        if (e0.size() != e3.size()) {
            std::cerr << "I332 Devillers |E| " << e3.size() << " vs " << e0.size() << "\n";
            return 1;
        }
        std::cout << "ok I332 3D Devillers |E|=" << e0.size() << "\n";
    }

    // I276: Delaunay-flag keeps essential H1 on a circle (not exact VR).
    {
        const int n = 16;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_one_skeleton(pts, de)) {
            std::cerr << "I276 circle Delaunay 1-skeleton failed\n";
            return 1;
        }
        Graph g = graph_from_edge_list(n, de, T);
        Result r = persist_implicit_coh(g, 1, T, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "I276 circle Delaunay-VR ess1=" << ess1 << "\n";
            return 1;
        }
        std::cout << "ok I276 Delaunay-VR circle ess H1\n";
    }

    // I276: two octahedra — Delaunay-flag keeps the two voids.
    {
        const value_t T = 1.5f;
        const value_t oct[6][3] = {
            {1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1},
        };
        std::vector<std::vector<value_t>> pts;
        pts.reserve(12);
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0], oct[i][1], oct[i][2]});
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0] + 8, oct[i][1], oct[i][2]});
        std::vector<Edge> de;
        if (!delaunay_one_skeleton(pts, de)) {
            std::cerr << "I276 two-octahedra Delaunay 1-skeleton failed\n";
            return 1;
        }
        Graph g = graph_from_edge_list(12, de, T);
        Result r = persist_implicit_coh(g, 2, T, 1);
        int ess0 = 0, ess2 = 0;
        for (const auto& p : r.pairs) {
            if (!std::isfinite(p.death)) {
                if (p.dim == 0) ++ess0;
                if (p.dim == 2) ++ess2;
            }
        }
        if (ess0 != 2 || ess2 != 2) {
            std::cerr << "I276 two-octahedra Delaunay-VR ess0/ess2=" << ess0 << "/" << ess2 << "\n";
            return 1;
        }
        std::cout << "ok I276 Delaunay-VR two-octahedra ess H2\n";
    }

    // I277: α=1.5 thicken keeps circle ess H1 and matches all-pairs H0.
    {
        const int n = 16;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_vr_skeleton(pts, T, 1.5f, de) || de.size() < 16) {
            std::cerr << "I277 thicken failed |E|=" << de.size() << "\n";
            return 1;
        }
        Graph g = graph_from_edge_list(n, de, T);
        Result r = persist_implicit_coh(g, 1, T, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "I277 circle thicken ess1=" << ess1 << "\n";
            return 1;
        }
        std::cout << "ok I277 Delaunay-VR α=1.5 circle ess H1 |E|=" << de.size() << "\n";
    }

    // I280: 2-hop adapt still keeps circle ess H1 and adds extras.
    {
        const int n = 16;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_vr_skeleton(pts, T, 1.5f, de, 0, true) || de.size() < 16) {
            std::cerr << "I280 adapt thicken failed |E|=" << de.size() << "\n";
            return 1;
        }
        Graph g = graph_from_edge_list(n, de, T);
        Result r = persist_implicit_coh(g, 1, T, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "I280 circle adapt ess1=" << ess1 << "\n";
            return 1;
        }
        std::cout << "ok I280 Delaunay-VR adapt circle ess H1 |E|=" << de.size() << "\n";
    }

    // I282: auto α formula + 16-pt circle at auto α keeps ess H1.
    {
        if (std::fabs(delaunay_auto_alpha(400) - 1.75f) > 1e-5f ||
            delaunay_auto_alpha(8000) < 2.25f || delaunay_auto_alpha(8000) > 2.35f) {
            std::cerr << "I282 auto α(400)=" << delaunay_auto_alpha(400)
                      << " α(8000)=" << delaunay_auto_alpha(8000) << "\n";
            return 1;
        }
        const int n = 16;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(n), de) || de.size() < 16) {
            std::cerr << "I282 auto thicken failed |E|=" << de.size() << "\n";
            return 1;
        }
        Graph g = graph_from_edge_list(n, de, T);
        Result r = persist_implicit_coh(g, 1, T, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "I282 circle auto ess1=" << ess1 << "\n";
            return 1;
        }
        std::cout << "ok I282 Delaunay-VR auto-α circle ess H1 α=" << delaunay_auto_alpha(n)
                  << " |E|=" << de.size() << "\n";
    }

    // I286: split H1 thicken / H2 α=1. Circle keeps ess H1; two octahedra
    // keep ess H2 from the thin flag (thicken must not fill the voids).
    {
        const int n = 16;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> thin, thick;
        if (!delaunay_vr_skeleton(pts, T, 1, thin) ||
            !delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(n), thick)) {
            std::cerr << "I286 circle split skeletons failed\n";
            return 1;
        }
        Result r1 = persist_implicit_coh(graph_from_edge_list(n, thick, T), 1, T, 1);
        Result r2 = persist_implicit_coh(graph_from_edge_list(n, thin, T), 2, T, 1);
        int ess1 = 0, ess2 = 0;
        for (const auto& p : r1.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        for (const auto& p : r2.pairs)
            if (p.dim == 2 && !std::isfinite(p.death)) ++ess2;
        if (ess1 != 1 || ess2 != 0) {
            std::cerr << "I286 circle split ess1/ess2=" << ess1 << "/" << ess2 << "\n";
            return 1;
        }
        std::cout << "ok I286 split circle ess H1 |E_thick|=" << thick.size() << "\n";
    }
    {
        const value_t T = 1.5f;
        const value_t oct[6][3] = {
            {1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1},
        };
        std::vector<std::vector<value_t>> pts;
        pts.reserve(12);
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0], oct[i][1], oct[i][2]});
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0] + 8, oct[i][1], oct[i][2]});
        std::vector<Edge> thin, thick;
        if (!delaunay_vr_skeleton(pts, T, 1, thin) ||
            !delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(12), thick)) {
            std::cerr << "I286 octahedra split skeletons failed\n";
            return 1;
        }
        Result r1 = persist_implicit_coh(graph_from_edge_list(12, thick, T), 1, T, 1);
        Result r2 = persist_implicit_coh(graph_from_edge_list(12, thin, T), 2, T, 1);
        int ess0 = 0, ess2 = 0;
        for (const auto& p : r1.pairs)
            if (p.dim == 0 && !std::isfinite(p.death)) ++ess0;
        for (const auto& p : r2.pairs)
            if (p.dim == 2 && !std::isfinite(p.death)) ++ess2;
        if (ess0 != 2 || ess2 != 2) {
            std::cerr << "I286 octahedra split ess0/ess2=" << ess0 << "/" << ess2 << "\n";
            return 1;
        }
        std::cout << "ok I286 split two-octahedra ess H0/H2 |E_thick|=" << thick.size() << "\n";
    }

    // I291: fat thicken (|E|≥8n) + collapse keeps ess H1 on a 64-pt circle.
    {
        const int n = 256;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(n), de)) {
            std::cerr << "I291 circle thicken failed\n";
            return 1;
        }
        if (!delaunay_thicken_should_collapse(n, static_cast<std::int64_t>(de.size()))) {
            std::cerr << "I291 expected fat thicken |E|=" << de.size() << " n=" << n << "\n";
            return 1;
        }
        Graph g = graph_from_edge_list(n, de, T);
        Counters cc;
        Graph h = collapse_edges(std::move(g), 1, cc);
        Result r = persist_implicit_coh(h, 1, T, 1);
        int ess1 = 0;
        for (const auto& p : r.pairs)
            if (p.dim == 1 && !std::isfinite(p.death)) ++ess1;
        if (ess1 != 1) {
            std::cerr << "I291 circle collapse ess1=" << ess1 << " |E|=" << de.size()
                      << " residual=" << h.edges.size() << "\n";
            return 1;
        }
        if (h.edges.size() >= de.size()) {
            std::cerr << "I291 collapse did not thin " << de.size() << " → " << h.edges.size()
                      << "\n";
            return 1;
        }
        std::cout << "ok I291 thicken-collapse circle ess H1 |E|=" << de.size()
                  << " residual=" << h.edges.size() << "\n";
    }

    // I297: RedZeD on the fat thicken 1-skeleton is the same flag PH as
    // implicit (ess H1=1). Gate |E|≥8n matches the CLI dispatch.
    {
        const int n = 256;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> de;
        if (!delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(n), de)) {
            std::cerr << "I297 circle thicken failed\n";
            return 1;
        }
        if (!delaunay_thicken_should_collapse(n, static_cast<std::int64_t>(de.size()))) {
            std::cerr << "I297 expected fat thicken |E|=" << de.size() << " n=" << n << "\n";
            return 1;
        }
        Result rz = persist_redzed_from_edges(n, de, 1, T);
        Result ri = persist_implicit_coh(graph_from_edge_list(n, de, T), 1, T, 1);
        int essz = 0, essi = 0, finz = 0, fini = 0;
        for (const auto& p : rz.pairs) {
            if (p.dim != 1) continue;
            if (!std::isfinite(p.death)) ++essz;
            else if (p.death - p.birth > 1e-5f) ++finz;
        }
        for (const auto& p : ri.pairs) {
            if (p.dim != 1) continue;
            if (!std::isfinite(p.death)) ++essi;
            else if (p.death - p.birth > 1e-5f) ++fini;
        }
        if (essz != 1 || essi != 1 || finz != fini) {
            std::cerr << "I297 circle redzed-edges ess/fin=" << essz << "/" << finz
                      << " implicit=" << essi << "/" << fini << " |E|=" << de.size() << "\n";
            return 1;
        }
        std::cout << "ok I297 redzed-from-edges circle ess H1 |E|=" << de.size()
                  << " fin1=" << finz << "\n";
    }

    // I298: extras on a copied Delaunay 1-skeleton match a fresh thicken.
    {
        const int n = 64;
        const value_t T = 1.4f;
        std::vector<std::vector<value_t>> pts(static_cast<size_t>(n), std::vector<value_t>(2));
        for (int i = 0; i < n; ++i) {
            const float a = 6.2831853f * static_cast<float>(i) / static_cast<float>(n);
            pts[static_cast<size_t>(i)][0] = std::cos(a);
            pts[static_cast<size_t>(i)][1] = std::sin(a);
        }
        std::vector<Edge> fresh, thin, reused;
        if (!delaunay_vr_skeleton(pts, T, delaunay_auto_alpha(n), fresh) ||
            !delaunay_one_skeleton(pts, thin)) {
            std::cerr << "I298 circle skeletons failed\n";
            return 1;
        }
        reused = thin;
        if (!delaunay_thicken_extras(pts, T, delaunay_auto_alpha(n), reused)) {
            std::cerr << "I298 extras failed\n";
            return 1;
        }
        auto key = [](const Edge& e) {
            int u = e.u, v = e.v;
            if (u > v) std::swap(u, v);
            return std::tuple<int, int, int>{u, v, static_cast<int>(e.t * 1e6f + 0.5f)};
        };
        std::vector<std::tuple<int, int, int>> a, b;
        for (const auto& e : fresh) a.push_back(key(e));
        for (const auto& e : reused) b.push_back(key(e));
        std::sort(a.begin(), a.end());
        std::sort(b.begin(), b.end());
        if (a != b || reused.size() <= thin.size()) {
            std::cerr << "I298 extras mismatch |fresh|=" << fresh.size()
                      << " |reused|=" << reused.size() << " |thin|=" << thin.size() << "\n";
            return 1;
        }
        std::cout << "ok I298 reuse-Delaunay extras |E|=" << reused.size()
                  << " thin=" << thin.size() << "\n";
    }

    // I300: RedZeD on the α=1 Delaunay flag keeps two octahedra voids.
    {
        const value_t T = 1.5f;
        const value_t oct[6][3] = {
            {1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1},
        };
        std::vector<std::vector<value_t>> pts;
        pts.reserve(12);
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0], oct[i][1], oct[i][2]});
        for (int i = 0; i < 6; ++i) pts.push_back({oct[i][0] + 8, oct[i][1], oct[i][2]});
        std::vector<Edge> de;
        if (!delaunay_one_skeleton(pts, de)) {
            std::cerr << "I300 octahedra Delaunay failed\n";
            return 1;
        }
        Result rz = persist_redzed_from_edges(12, de, 2, T);
        int ess0 = 0, ess2 = 0;
        for (const auto& p : rz.pairs) {
            if (!std::isfinite(p.death)) {
                if (p.dim == 0) ++ess0;
                if (p.dim == 2) ++ess2;
            }
        }
        if (ess0 != 2 || ess2 != 2) {
            std::cerr << "I300 redzed-edges octahedra ess0/ess2=" << ess0 << "/" << ess2 << "\n";
            return 1;
        }
        std::cout << "ok I300 redzed-from-edges two-octahedra ess H0/H2 |E|=" << de.size() << "\n";
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

    // I246: single octahedron through redzed_vr H2 lazy-insert AE.
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
                dist[i][j] = dist[j][i] = std::sqrt(d);
            }
        Result rz = persist_redzed(dist, 2, T);
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
        if (ess0 != 1 || ess1 != 0 || ess2 != 1 || fin2 != 0) {
            std::cerr << "I246 redzed octahedron H0/H1/H2 ess=" << ess0 << "/" << ess1 << "/"
                      << ess2 << " fin2=" << fin2 << "\n";
            return 1;
        }
        std::cout << "ok I246 redzed octahedron H2 lazy-insert\n";
    }

    std::cout << "all collapse/persist unit tests passed\n";
    return 0;
}
