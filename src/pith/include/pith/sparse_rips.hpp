#pragma once

#include "graph.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <unordered_map>
#include <vector>

namespace pith {

inline value_t euclid_dist(const std::vector<std::vector<value_t>>& pts, int i, int j) {
    const int d = static_cast<int>(pts[static_cast<size_t>(i)].size());
    double s = 0;
    for (int k = 0; k < d; ++k) {
        const double df = static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) -
                          static_cast<double>(pts[static_cast<size_t>(j)][static_cast<size_t>(k)]);
        s += df * df;
    }
    return static_cast<value_t>(std::sqrt(s));
}

// I210: insertion radii of a farthest-point (greedy) permutation.
// λ[p_0] is the covering radius after the first point; later λ[p] is the
// distance from p to the already-chosen net. O(n²) on a dense distance matrix.
inline std::vector<value_t> greedy_insertion_radii(const std::vector<std::vector<value_t>>& dist) {
    const int n = static_cast<int>(dist.size());
    std::vector<value_t> lam(static_cast<size_t>(n), 0);
    if (n == 0) return lam;
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<value_t> mind(static_cast<size_t>(n), kInf);
    used[0] = 1;
    value_t cover = 0;
    for (int j = 1; j < n; ++j) {
        mind[static_cast<size_t>(j)] = dist[0][static_cast<size_t>(j)];
        cover = std::max(cover, mind[static_cast<size_t>(j)]);
    }
    lam[0] = cover;
    for (int k = 1; k < n; ++k) {
        int best = -1;
        value_t best_d = -1;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            if (mind[static_cast<size_t>(j)] > best_d) {
                best_d = mind[static_cast<size_t>(j)];
                best = j;
            }
        }
        if (best < 0) break;
        used[static_cast<size_t>(best)] = 1;
        lam[static_cast<size_t>(best)] = best_d;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            mind[static_cast<size_t>(j)] =
                std::min(mind[static_cast<size_t>(j)], dist[static_cast<size_t>(best)][static_cast<size_t>(j)]);
        }
    }
    return lam;
}

// Same greedy net as greedy_insertion_radii, but distances are computed
// on the fly. Same starting vertex (0) and same tie-break (first max),
// so λ matches the dense-matrix path on a Euclidean cloud. Still Θ(n²)
// evaluations; memory is O(n) instead of O(n²).
inline std::vector<value_t> greedy_insertion_radii_points(const std::vector<std::vector<value_t>>& pts,
                                                          std::int64_t* n_dist = nullptr) {
    const int n = static_cast<int>(pts.size());
    std::vector<value_t> lam(static_cast<size_t>(n), 0);
    if (n == 0) return lam;
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<value_t> mind(static_cast<size_t>(n), kInf);
    used[0] = 1;
    value_t cover = 0;
    for (int j = 1; j < n; ++j) {
        mind[static_cast<size_t>(j)] = euclid_dist(pts, 0, j);
        if (n_dist) ++*n_dist;
        cover = std::max(cover, mind[static_cast<size_t>(j)]);
    }
    lam[0] = cover;
    for (int k = 1; k < n; ++k) {
        int best = -1;
        value_t best_d = -1;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            if (mind[static_cast<size_t>(j)] > best_d) {
                best_d = mind[static_cast<size_t>(j)];
                best = j;
            }
        }
        if (best < 0) break;
        used[static_cast<size_t>(best)] = 1;
        lam[static_cast<size_t>(best)] = best_d;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            const value_t d = euclid_dist(pts, best, j);
            if (n_dist) ++*n_dist;
            mind[static_cast<size_t>(j)] = std::min(mind[static_cast<size_t>(j)], d);
        }
    }
    return lam;
}

// I327: hierarchical s-net insertion radii (Cavanna–Jahanseir–Sheehy nets,
// not farthest-point). Euclidean d∈{2,3} only.
//
// Coarse-to-fine: at scale s, insert every unassigned p with d(p,N)>s and
// set λ[p]=d(p,N). Then L_s (points inserted at this or a coarser scale)
// is an s-net: packing d>s, covering d≤s. Neighbor-cell search uses cell
// width s, so a ball of radius s sits in the Moore neighborhood.
//
// Stated slack vs Gonzalez FPS: insertion scales are dyadic, so
// s < λ[p] ≤ 2s at the insert level. The same sparse-Rips rule with
// these λ is a net-sparse 1-skeleton whose multiplicative interleaving
// vs VR is the Sheehy/CJS constant times a factor-2 dyadic slack
// **[derivation; not exact VR]**. Distance evaluations are
// O(n log(Δ/δ)) expected, not Θ(n²).
//
// Falls back to farthest-point if d∉{2,3} or the cloud is degenerate.
enum class SparseNet { Fps, Dyadic, Approx };

struct DyadicCell {
    int x = 0, y = 0, z = 0;
    bool operator==(const DyadicCell& o) const { return x == o.x && y == o.y && z == o.z; }
};

struct DyadicCellHash {
    std::size_t operator()(const DyadicCell& k) const {
        std::size_t h = static_cast<std::size_t>(static_cast<std::uint32_t>(k.x));
        h ^= static_cast<std::size_t>(static_cast<std::uint32_t>(k.y)) + 0x9e3779b97f4a7c15ull +
             (h << 6) + (h >> 2);
        h ^= static_cast<std::size_t>(static_cast<std::uint32_t>(k.z)) + 0x9e3779b97f4a7c15ull +
             (h << 6) + (h >> 2);
        return h;
    }
};

inline std::vector<value_t> dyadic_insertion_radii_points(const std::vector<std::vector<value_t>>& pts,
                                                          std::int64_t* n_dist = nullptr) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n == 0) return {};
    if (d < 2 || d > 3) return greedy_insertion_radii_points(pts, n_dist);

    std::vector<value_t> lam(static_cast<size_t>(n), 0);
    std::vector<char> used(static_cast<size_t>(n), 0);
    used[0] = 1;
    value_t cover = 0;
    for (int j = 1; j < n; ++j) {
        const value_t dj = euclid_dist(pts, 0, j);
        if (n_dist) ++*n_dist;
        cover = std::max(cover, dj);
    }
    lam[0] = cover;
    if (!(cover > 0) || !std::isfinite(static_cast<double>(cover))) return lam;

    int left = n - 1;
    double s = static_cast<double>(cover);
    std::unordered_map<DyadicCell, std::vector<int>, DyadicCellHash> grid;
    auto cell_of = [&](int i, double inv) {
        DyadicCell c;
        c.x = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][0]) * inv));
        c.y = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][1]) * inv));
        if (d == 3)
            c.z = static_cast<int>(
                std::floor(static_cast<double>(pts[static_cast<size_t>(i)][2]) * inv));
        return c;
    };
    auto min_net = [&](int i, double inv) -> value_t {
        const DyadicCell c0 = cell_of(i, inv);
        value_t best = kInf;
        const int z1 = (d == 3) ? 1 : 0;
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                for (int dz = -z1; dz <= z1; ++dz) {
                    DyadicCell c = c0;
                    c.x += dx;
                    c.y += dy;
                    c.z += dz;
                    const auto it = grid.find(c);
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        const value_t dd = euclid_dist(pts, i, j);
                        if (n_dist) ++*n_dist;
                        if (dd < best) best = dd;
                    }
                }
        return best;
    };

    for (int level = 0; level < 64 && left > 0; ++level) {
        s *= 0.5;
        if (!(s > 0) || !std::isfinite(s)) break;
        const double inv = 1.0 / s;
        grid.clear();
        grid.reserve(static_cast<size_t>(n - left + 1) * 2);
        for (int i = 0; i < n; ++i) {
            if (used[static_cast<size_t>(i)]) grid[cell_of(i, inv)].push_back(i);
        }
        for (int i = 1; i < n; ++i) {
            if (used[static_cast<size_t>(i)]) continue;
            const value_t md = min_net(i, inv);
            if (md > static_cast<value_t>(s)) {
                used[static_cast<size_t>(i)] = 1;
                lam[static_cast<size_t>(i)] = md;
                grid[cell_of(i, inv)].push_back(i);
                --left;
            }
        }
    }
    if (left > 0) {
        const double inv = (s > 0 && std::isfinite(s)) ? 1.0 / s : 0;
        if (inv > 0 && grid.empty()) {
            for (int i = 0; i < n; ++i) {
                if (used[static_cast<size_t>(i)]) grid[cell_of(i, inv)].push_back(i);
            }
        }
        for (int i = 1; i < n; ++i) {
            if (used[static_cast<size_t>(i)]) continue;
            value_t md = (inv > 0) ? min_net(i, inv) : kInf;
            if (!(md < kInf)) md = static_cast<value_t>(s > 0 ? s : 0);
            used[static_cast<size_t>(i)] = 1;
            lam[static_cast<size_t>(i)] = md;
            --left;
        }
    }
    return lam;
}

// I331: c-approximate greedy permutation (not batched s-nets, not exact FPS).
// Euclidean d∈{2,3} only.
//
// Gonzalez picks the unused point farthest from the current net. That is
// Θ(n²) distance evaluations. Here each insertion takes a deterministic
// stride sample of unused indices, |S|=min(left, max(48, ⌈2.5√n⌉)), and
// picks the sample point with largest exact d(·, net). λ[p] is that
// distance — a valid insertion radius for this order.
//
// If every step is a c-approx farthest, the prefixes are (2c)-approx
// k-centers and the same sparse-Rips rule has Sheehy interleaving times
// c **[derivation; sample-farthest is c-approx when the leftover set is
// well spread, otherwise empirical]**. One insert per step, so λ tracks
// Gonzalez instead of a dyadic bucket (I327 densified because many
// points shared a coarse s).
//
// Nearest-net queries use a grid of inserted points (cell width tracks
// the last λ). Falls back to farthest-point if d∉{2,3}.
inline value_t approx_net_nn(const std::vector<std::vector<value_t>>& pts, int p,
                             const std::vector<int>& net,
                             const std::unordered_map<DyadicCell, std::vector<int>, DyadicCellHash>& grid,
                             double w, int d, std::int64_t* n_dist) {
    if (net.empty()) return kInf;
    auto cell_of = [&](int i) {
        DyadicCell c;
        const double inv = 1.0 / w;
        c.x = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][0]) * inv));
        c.y = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][1]) * inv));
        if (d == 3)
            c.z = static_cast<int>(
                std::floor(static_cast<double>(pts[static_cast<size_t>(i)][2]) * inv));
        return c;
    };
    if (static_cast<int>(net.size()) <= 24 || !(w > 0) || !std::isfinite(w) || grid.empty()) {
        value_t best = kInf;
        for (int j : net) {
            const value_t dd = euclid_dist(pts, p, j);
            if (n_dist) ++*n_dist;
            if (dd < best) best = dd;
        }
        return best;
    }
    const DyadicCell c0 = cell_of(p);
    value_t best = kInf;
    const int z1 = (d == 3) ? 1 : 0;
    for (int r = 0; r <= 48; ++r) {
        if (r >= 1 && best < kInf) {
            const double mind = static_cast<double>(r - 1) * w;
            if (mind >= static_cast<double>(best)) break;
        }
        for (int dx = -r; dx <= r; ++dx)
            for (int dy = -r; dy <= r; ++dy)
                for (int dz = -z1 * r; dz <= z1 * r; ++dz) {
                    if (r > 0 && std::max(std::abs(dx), std::max(std::abs(dy), std::abs(dz))) != r)
                        continue;
                    DyadicCell c = c0;
                    c.x += dx;
                    c.y += dy;
                    c.z += dz;
                    const auto it = grid.find(c);
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        const value_t dd = euclid_dist(pts, p, j);
                        if (n_dist) ++*n_dist;
                        if (dd < best) best = dd;
                    }
                }
    }
    if (!(best < kInf)) {
        for (int j : net) {
            const value_t dd = euclid_dist(pts, p, j);
            if (n_dist) ++*n_dist;
            if (dd < best) best = dd;
        }
    }
    return best;
}

inline std::vector<value_t> approx_insertion_radii_points(const std::vector<std::vector<value_t>>& pts,
                                                          std::int64_t* n_dist = nullptr) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n == 0) return {};
    if (d < 2 || d > 3) return greedy_insertion_radii_points(pts, n_dist);

    std::vector<value_t> lam(static_cast<size_t>(n), 0);
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<int> net;
    net.reserve(static_cast<size_t>(n));
    used[0] = 1;
    net.push_back(0);
    value_t cover = 0;
    for (int j = 1; j < n; ++j) {
        const value_t dj = euclid_dist(pts, 0, j);
        if (n_dist) ++*n_dist;
        cover = std::max(cover, dj);
    }
    lam[0] = cover;
    if (!(cover > 0) || !std::isfinite(static_cast<double>(cover))) return lam;

    double grid_w = static_cast<double>(cover);
    std::unordered_map<DyadicCell, std::vector<int>, DyadicCellHash> grid;
    auto cell_of = [&](int i, double w) {
        DyadicCell c;
        const double inv = 1.0 / w;
        c.x = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][0]) * inv));
        c.y = static_cast<int>(std::floor(static_cast<double>(pts[static_cast<size_t>(i)][1]) * inv));
        if (d == 3)
            c.z = static_cast<int>(
                std::floor(static_cast<double>(pts[static_cast<size_t>(i)][2]) * inv));
        return c;
    };
    auto rebuild = [&](double w) {
        grid.clear();
        grid.reserve(net.size() * 2);
        for (int i : net) grid[cell_of(i, w)].push_back(i);
    };
    rebuild(grid_w);

    const int s_cap = std::max(48, static_cast<int>(std::ceil(2.5 * std::sqrt(static_cast<double>(n)))));
    std::vector<int> unused;
    unused.reserve(static_cast<size_t>(n));
    for (int k = 1; k < n; ++k) {
        unused.clear();
        for (int i = 1; i < n; ++i)
            if (!used[static_cast<size_t>(i)]) unused.push_back(i);
        const int left = static_cast<int>(unused.size());
        if (left <= 0) break;
        const int s = std::min(left, s_cap);
        const int stride = std::max(1, left / s);
        const int phase = k % stride;
        int best = unused[static_cast<size_t>(phase % left)];
        value_t best_d = -1;
        for (int t = 0; t < s; ++t) {
            const int p = unused[static_cast<size_t>((phase + static_cast<long long>(t) * stride) % left)];
            const value_t md = approx_net_nn(pts, p, net, grid, grid_w, d, n_dist);
            if (md > best_d) {
                best_d = md;
                best = p;
            }
        }
        if (best < 0) break;
        used[static_cast<size_t>(best)] = 1;
        lam[static_cast<size_t>(best)] = (best_d > 0) ? best_d : 0;
        net.push_back(best);
        if (best_d > 0 && static_cast<double>(best_d) < 0.5 * grid_w) {
            grid_w = static_cast<double>(best_d);
            if (!(grid_w > 0) || !std::isfinite(grid_w)) grid_w = static_cast<double>(best_d);
            rebuild(grid_w);
        } else {
            grid[cell_of(best, grid_w)].push_back(best);
        }
    }
    return lam;
}

// How the insertion-radius cap is combined. I210 used Max (looser, denser).
// I212 tries Min (closer to GUDHI's thinner 1-skeleton).
enum class SparseCap { Max, Min };

inline bool sparse_rips_keep(value_t d, value_t T, value_t li, value_t lj, value_t c,
                             SparseCap cap) {
    if (d > T) return false;
    const value_t rad = (cap == SparseCap::Min) ? std::min(li, lj) : std::max(li, lj);
    return d <= c * rad;
}

// Cavanna–Jahanseir–Sheehy / GUDHI-style sparse Rips 1-skeleton.
// Keep (i,j) iff d(i,j) ≤ T and d(i,j) ≤ ((1+ε)/ε) · cap(λ_i, λ_j).
// This is exact PH of the *flag* of that subgraph, not of VR(G_T).
inline Graph sparse_rips_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                               value_t eps, SparseCap cap = SparseCap::Max) {
    if (eps <= 0 || eps >= 1) return graph_from_distance(dist, T);
    const int n = static_cast<int>(dist.size());
    Graph g;
    g.n = n;
    const auto lam = greedy_insertion_radii(dist);
    const value_t c = (1 + eps) / eps;
    g.edges.reserve(static_cast<size_t>(n) * 8);
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            const value_t d = dist[static_cast<size_t>(i)][static_cast<size_t>(j)];
            if (sparse_rips_keep(d, T, lam[static_cast<size_t>(i)], lam[static_cast<size_t>(j)], c, cap))
                g.edges.push_back({i, j, d});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I240-style cell pack (21 bits / axis). Same Moore neighborhood as
// spatial_edges: every Euclidean pair with d≤T is visited when the cell
// width is T.
inline uint64_t sparse_pack_cell(const int* c, int d) {
    uint64_t k = 0;
    for (int i = 0; i < d; ++i) {
        const uint64_t w = static_cast<uint32_t>(c[i]) & 0x1FFFFFu;
        k |= w << (21 * i);
    }
    return k;
}

template <class Fn>
inline bool for_each_tball_pair(const std::vector<std::vector<value_t>>& pts, value_t T, Fn&& fn) {
    const int n = static_cast<int>(pts.size());
    const int d = n ? static_cast<int>(pts[0].size()) : 0;
    if (n <= 1 || d < 2 || d > 3 || !(T > 0) || !std::isfinite(T)) return false;
    const double inv = 1.0 / static_cast<double>(T);
    std::unordered_map<uint64_t, std::vector<int>> grid;
    grid.reserve(static_cast<size_t>(n) * 2);
    std::vector<int> cell0(static_cast<size_t>(n) * 3, 0);
    for (int i = 0; i < n; ++i) {
        int c[3] = {0, 0, 0};
        for (int k = 0; k < d; ++k)
            c[k] = static_cast<int>(
                std::floor(static_cast<double>(pts[static_cast<size_t>(i)][static_cast<size_t>(k)]) * inv));
        cell0[static_cast<size_t>(i) * 3 + 0] = c[0];
        cell0[static_cast<size_t>(i) * 3 + 1] = c[1];
        cell0[static_cast<size_t>(i) * 3 + 2] = c[2];
        grid[sparse_pack_cell(c, d)].push_back(i);
    }
    const int z1 = (d == 3) ? 1 : 0;
    for (int i = 0; i < n; ++i) {
        int c[3] = {0, 0, 0};
        const int* c0 = &cell0[static_cast<size_t>(i) * 3];
        for (int dx = -1; dx <= 1; ++dx)
            for (int dy = -1; dy <= 1; ++dy)
                for (int dz = -z1; dz <= z1; ++dz) {
                    c[0] = c0[0] + dx;
                    c[1] = c0[1] + dy;
                    c[2] = (d == 3) ? c0[2] + dz : 0;
                    const auto it = grid.find(sparse_pack_cell(c, d));
                    if (it == grid.end()) continue;
                    for (int j : it->second) {
                        if (j <= i) continue;
                        fn(i, j);
                    }
                }
    }
    return true;
}

// Euclidean constructor: same edge set as sparse_rips_graph(pairwise(pts), T, ε)
// when net=Fps. Farthest-point insertion is still Θ(n²). `--sparse-net dyadic`
// (I327) replaces FPS with hierarchical s-nets in d∈{2,3}; the edge set
// then differs and the interleaving constant picks up a factor-2 slack.
// `--sparse-net approx` (I331) is a sample-farthest greedy permutation:
// one insert per step, λ = d(p, prefix net), stated slack is the
// approx-farthest factor (not a dyadic bucket).
// Emit uses a T-ball spatial hash when d∈{2,3} and T is finite; otherwise
// an on-the-fly all-pairs walk. Does not allocate an n×n matrix.
inline Graph sparse_rips_graph_points(const std::vector<std::vector<value_t>>& pts, value_t T,
                                      value_t eps, SparseCap cap = SparseCap::Max,
                                      std::int64_t* n_dist = nullptr,
                                      SparseNet net = SparseNet::Fps) {
    const int n = static_cast<int>(pts.size());
    Graph g;
    g.n = n;
    if (n <= 1) return g;
    g.edges.reserve(static_cast<size_t>(n) * 8);
    auto emit_pair = [&](int i, int j, value_t li, value_t lj, value_t cfac, bool use_eps) {
        const value_t dist = euclid_dist(pts, i, j);
        if (n_dist) ++*n_dist;
        if (use_eps) {
            if (sparse_rips_keep(dist, T, li, lj, cfac, cap)) g.edges.push_back({i, j, dist});
        } else if (dist <= T) {
            g.edges.push_back({i, j, dist});
        }
    };
    const bool use_eps = (eps > 0 && eps < 1);
    std::vector<value_t> lam;
    value_t cfac = 0;
    if (use_eps) {
        if (net == SparseNet::Dyadic)
            lam = dyadic_insertion_radii_points(pts, n_dist);
        else if (net == SparseNet::Approx)
            lam = approx_insertion_radii_points(pts, n_dist);
        else
            lam = greedy_insertion_radii_points(pts, n_dist);
        cfac = (1 + eps) / eps;
    }
    auto visit = [&](int i, int j) {
        const value_t li = use_eps ? lam[static_cast<size_t>(i)] : 0;
        const value_t lj = use_eps ? lam[static_cast<size_t>(j)] : 0;
        emit_pair(i, j, li, lj, cfac, use_eps);
    };
    if (!for_each_tball_pair(pts, T, visit)) {
        for (int i = 0; i < n; ++i)
            for (int j = i + 1; j < n; ++j) visit(i, j);
    }
    rebuild_neighbors(g);
    return g;
}

// I220: undirected kNN 1-skeleton. Keep (i,j) iff d≤T and i is among j's
// K nearest (or vice versa). Flag PH of this graph is not exact VR.
// |E| ≤ nK. Shape-agnostic. I021 rejected k=16 as exact-VR.
inline Graph knn_flag_graph(const std::vector<std::vector<value_t>>& dist, value_t T, int K) {
    const int n = static_cast<int>(dist.size());
    Graph g;
    g.n = n;
    if (n < 2 || K <= 0) return g;
    std::vector<char> keep(static_cast<size_t>(n) * static_cast<size_t>(n), 0);
    std::vector<std::pair<value_t, int>> row;
    row.reserve(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        row.clear();
        const value_t* di = dist[static_cast<size_t>(i)].data();
        for (int j = 0; j < n; ++j) {
            if (j == i) continue;
            const value_t d = di[j];
            if (d <= T) row.push_back({d, j});
        }
        const int k = std::min(K, static_cast<int>(row.size()));
        if (k > 0 && k < static_cast<int>(row.size()))
            std::nth_element(row.begin(), row.begin() + k, row.end());
        for (int t = 0; t < k; ++t) {
            const int j = row[static_cast<size_t>(t)].second;
            keep[static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j)] = 1;
        }
    }
    g.edges.reserve(static_cast<size_t>(n) * static_cast<size_t>(std::max(K, 1)));
    for (int i = 0; i < n; ++i) {
        for (int j = i + 1; j < n; ++j) {
            const size_t ij = static_cast<size_t>(i) * static_cast<size_t>(n) + static_cast<size_t>(j);
            const size_t ji = static_cast<size_t>(j) * static_cast<size_t>(n) + static_cast<size_t>(i);
            if (keep[ij] || keep[ji])
                g.edges.push_back({static_cast<index_t>(i), static_cast<index_t>(j),
                                   dist[static_cast<size_t>(i)][static_cast<size_t>(j)]});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I216: first `m` vertices of a farthest-point (greedy) permutation.
inline std::vector<index_t> greedy_landmarks(const std::vector<std::vector<value_t>>& dist, int m) {
    const int n = static_cast<int>(dist.size());
    if (m > n) m = n;
    std::vector<index_t> L;
    if (n <= 0 || m <= 0) return L;
    L.reserve(static_cast<size_t>(m));
    std::vector<char> used(static_cast<size_t>(n), 0);
    std::vector<value_t> mind(static_cast<size_t>(n), kInf);
    L.push_back(0);
    used[0] = 1;
    for (int j = 1; j < n; ++j) mind[static_cast<size_t>(j)] = dist[0][static_cast<size_t>(j)];
    for (int k = 1; k < m; ++k) {
        int best = -1;
        value_t best_d = -1;
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            if (mind[static_cast<size_t>(j)] > best_d) {
                best_d = mind[static_cast<size_t>(j)];
                best = j;
            }
        }
        if (best < 0) break;
        used[static_cast<size_t>(best)] = 1;
        L.push_back(static_cast<index_t>(best));
        for (int j = 0; j < n; ++j) {
            if (used[static_cast<size_t>(j)]) continue;
            mind[static_cast<size_t>(j)] =
                std::min(mind[static_cast<size_t>(j)],
                         dist[static_cast<size_t>(best)][static_cast<size_t>(j)]);
        }
    }
    return L;
}

// de Silva–Carlsson lazy witness 1-skeleton on farthest-point landmarks.
// Edge {a,b} ⊂ L enters at t = min_w max(0, max(d(w,a), d(w,b)) − m_ν(w)),
// where m_0 = 0 and m_ν (ν≥1) is the distance from w to its ν-th nearest
// landmark. Flag PH of this graph is a different complex than VR≤T.
// Construction O(n m²); PH is on m vertices (not n). Shape-agnostic.
inline Graph lazy_witness_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                                int nland, int nu) {
    const int n = static_cast<int>(dist.size());
    const auto L = greedy_landmarks(dist, nland);
    const int m = static_cast<int>(L.size());
    Graph g;
    g.n = m;
    if (m < 2) return g;
    std::vector<value_t> tpair(static_cast<size_t>(m) * static_cast<size_t>(m), kInf);
    std::vector<value_t> dw(static_cast<size_t>(m));
    std::vector<value_t> tmp(static_cast<size_t>(m));
    for (int w = 0; w < n; ++w) {
        for (int i = 0; i < m; ++i)
            dw[static_cast<size_t>(i)] = dist[static_cast<size_t>(w)][static_cast<size_t>(L[static_cast<size_t>(i)])];
        value_t mnu = 0;
        if (nu > 0 && m > 0) {
            tmp = dw;
            const int kth = std::min(nu, m);
            std::nth_element(tmp.begin(), tmp.begin() + (kth - 1), tmp.end());
            mnu = tmp[static_cast<size_t>(kth - 1)];
        }
        for (int i = 0; i < m; ++i) {
            for (int j = i + 1; j < m; ++j) {
                value_t t = std::max(dw[static_cast<size_t>(i)], dw[static_cast<size_t>(j)]) - mnu;
                if (t < 0) t = 0;
                value_t& slot = tpair[static_cast<size_t>(i) * static_cast<size_t>(m) + static_cast<size_t>(j)];
                if (t < slot) slot = t;
            }
        }
    }
    g.edges.reserve(static_cast<size_t>(m) * 4);
    for (int i = 0; i < m; ++i) {
        for (int j = i + 1; j < m; ++j) {
            const value_t t = tpair[static_cast<size_t>(i) * static_cast<size_t>(m) + static_cast<size_t>(j)];
            if (t <= T) g.edges.push_back({static_cast<index_t>(i), static_cast<index_t>(j), t});
        }
    }
    rebuild_neighbors(g);
    return g;
}

// I222: graph-induced 1-skeleton (Dey–Fan–Wang style, flag of the quotient).
// Farthest-point landmarks L; each point maps to its nearest landmark;
// a kNN edge that crosses two cells gives a landmark edge at that length.
// PH is on |L| vertices. Not exact VR — quantify loss.
inline Graph gic_graph(const std::vector<std::vector<value_t>>& dist, value_t T,
                       int nland, int K) {
    const int n = static_cast<int>(dist.size());
    const auto L = greedy_landmarks(dist, nland);
    const int m = static_cast<int>(L.size());
    Graph g;
    g.n = m;
    if (m < 2 || K <= 0) return g;
    std::vector<int> assign(static_cast<size_t>(n), 0);
    for (int i = 0; i < n; ++i) {
        int best = 0;
        value_t bd = dist[static_cast<size_t>(i)][static_cast<size_t>(L[0])];
        for (int a = 1; a < m; ++a) {
            const value_t d = dist[static_cast<size_t>(i)][static_cast<size_t>(L[static_cast<size_t>(a)])];
            if (d < bd) {
                bd = d;
                best = a;
            }
        }
        assign[static_cast<size_t>(i)] = best;
    }
    std::vector<value_t> tpair(static_cast<size_t>(m) * static_cast<size_t>(m), kInf);
    std::vector<std::pair<value_t, int>> row;
    row.reserve(static_cast<size_t>(n));
    for (int i = 0; i < n; ++i) {
        row.clear();
        const value_t* di = dist[static_cast<size_t>(i)].data();
        for (int j = 0; j < n; ++j) {
            if (j == i) continue;
            if (di[j] <= T) row.push_back({di[j], j});
        }
        const int k = std::min(K, static_cast<int>(row.size()));
        if (k > 0 && k < static_cast<int>(row.size()))
            std::nth_element(row.begin(), row.begin() + k, row.end());
        const int ai = assign[static_cast<size_t>(i)];
        for (int t = 0; t < k; ++t) {
            const int j = row[static_cast<size_t>(t)].second;
            const int aj = assign[static_cast<size_t>(j)];
            if (ai == aj) continue;
            const int a = std::min(ai, aj);
            const int b = std::max(ai, aj);
            value_t& slot = tpair[static_cast<size_t>(a) * static_cast<size_t>(m) + static_cast<size_t>(b)];
            if (di[j] < slot) slot = di[j];
        }
    }
    g.edges.reserve(static_cast<size_t>(m) * 4);
    for (int a = 0; a < m; ++a) {
        for (int b = a + 1; b < m; ++b) {
            const value_t t = tpair[static_cast<size_t>(a) * static_cast<size_t>(m) + static_cast<size_t>(b)];
            if (t <= T) g.edges.push_back({static_cast<index_t>(a), static_cast<index_t>(b), t});
        }
    }
    rebuild_neighbors(g);
    return g;
}

}  // namespace pith
