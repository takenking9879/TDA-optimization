#pragma once

#include "persist.hpp"

namespace pith {

// I231–I233: owned H1 active enumeration (RedZeD idea, not the vendor copy).
// I232: F₂ annotations R / Ri skip empty-XOR (H₂-birth) reduce.
// I233: do not walk every common neighbor. Apparent 1-leftover triangles
// are the leftover + two MST edges (tree-star intersection, O(deg_T)).
// Multi-leftover triangles come from the *active* leftover star (R nonempty).
// Same path on every flag graph — shape-agnostic.
inline Result persist_active_h1(const Graph& g, int maxdim, value_t threshold,
                                value_t ratio) {
    Result r;
    Counters& c = r.counters;
    c.n_vertices = g.n;
    c.n_edges_out = static_cast<std::int64_t>(g.edges.size());
    c.pipeline = "pith:active-h1";
    const auto t0 = std::chrono::steady_clock::now();

    std::vector<Edge> edges = g.edges;
    std::sort(edges.begin(), edges.end(), [](const Edge& a, const Edge& b) {
        if (a.t != b.t) return a.t < b.t;
        if (a.u != b.u) return a.u < b.u;
        return a.v < b.v;
    });

    UnionFind uf(g.n);
    struct BirthEdge {
        index_t u, v;
        value_t t;
        int id;
    };
    std::vector<BirthEdge> leftover;
    leftover.reserve(edges.size());
    std::vector<std::vector<std::pair<index_t, value_t>>> tree_nbr(
        static_cast<size_t>(g.n));
    int components = g.n;
    for (const Edge& e : edges) {
        if (e.t > threshold) continue;
        if (uf.unite(e.u, e.v)) {
            --components;
            r.pairs.push_back({0, 0, e.t});
            ++c.n_columns_cleared;
            tree_nbr[static_cast<size_t>(e.u)].push_back({e.v, e.t});
            tree_nbr[static_cast<size_t>(e.v)].push_back({e.u, e.t});
        } else {
            leftover.push_back({e.u, e.v, e.t, static_cast<int>(leftover.size())});
        }
    }
    for (int i = 0; i < components; ++i) r.pairs.push_back({0, 0, kInf});

    if (maxdim < 1) {
        const auto t1 = std::chrono::steady_clock::now();
        c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
        c.rss_bytes_peak = peak_rss_bytes();
        return r;
    }

    std::unordered_map<std::uint64_t, int> edge_id;
    edge_id.reserve(leftover.size() * 2);
    for (const auto& e : leftover) edge_id[pack2(e.u, e.v)] = e.id;

    const int m = static_cast<int>(leftover.size());
    // I232: R[x] = annotation of leftover x; Ri[y] = leftovers whose R
    // contains y. Live birth ⇔ Ri nonempty (RedZeD emit_infinite). R may
    // stay after pairing so a later triangle can XOR the transferred
    // annotation — clearing R[j] on pair missed the unit-square death
    // (I231: 023 after 012 dead still reduces onto the older leftover).
    std::vector<std::vector<int>> R(static_cast<size_t>(m)), Ri(static_cast<size_t>(m));
    // I233: leftover ids with nonempty R, incident to each vertex.
    std::vector<std::vector<int>> star(static_cast<size_t>(g.n));
    std::vector<int> star_pos(static_cast<size_t>(m) * 2, -1);
    auto star_add = [&](int id) {
        const BirthEdge& e = leftover[static_cast<size_t>(id)];
        star_pos[static_cast<size_t>(id) * 2] = static_cast<int>(star[static_cast<size_t>(e.u)].size());
        star[static_cast<size_t>(e.u)].push_back(id);
        star_pos[static_cast<size_t>(id) * 2 + 1] = static_cast<int>(star[static_cast<size_t>(e.v)].size());
        star[static_cast<size_t>(e.v)].push_back(id);
    };
    auto star_del_at = [&](index_t v, int id, int which) {
        const int p = star_pos[static_cast<size_t>(id) * 2 + static_cast<size_t>(which)];
        if (p < 0) return;
        auto& row = star[static_cast<size_t>(v)];
        const int last = row.back();
        row[static_cast<size_t>(p)] = last;
        const BirthEdge& le = leftover[static_cast<size_t>(last)];
        const int last_which = (le.u == v) ? 0 : 1;
        star_pos[static_cast<size_t>(last) * 2 + static_cast<size_t>(last_which)] = p;
        row.pop_back();
        star_pos[static_cast<size_t>(id) * 2 + static_cast<size_t>(which)] = -1;
    };
    auto star_del = [&](int id) {
        const BirthEdge& e = leftover[static_cast<size_t>(id)];
        star_del_at(e.u, id, 0);
        star_del_at(e.v, id, 1);
    };
    for (int i = 0; i < m; ++i) {
        R[static_cast<size_t>(i)] = {i};
        Ri[static_cast<size_t>(i)] = {i};
        star_add(i);
    }

    auto xor_sorted = [](std::vector<int>& a, const std::vector<int>& b) {
        std::vector<int> out;
        out.reserve(a.size() + b.size());
        size_t i = 0, j = 0;
        while (i < a.size() && j < b.size()) {
            if (a[i] == b[j]) {
                ++i;
                ++j;
            } else if (a[i] < b[j]) {
                out.push_back(a[i++]);
            } else {
                out.push_back(b[j++]);
            }
        }
        while (i < a.size()) out.push_back(a[i++]);
        while (j < b.size()) out.push_back(b[j++]);
        a.swap(out);
    };

    auto remove_elem = [](std::vector<int>& a, int y) {
        auto it = std::lower_bound(a.begin(), a.end(), y);
        if (it != a.end() && *it == y) a.erase(it);
    };

    auto resolve_bar = [&](std::vector<int>& bar, value_t td) {
        if (bar.empty()) return;
        const int j = bar.back();
        if (td > leftover[static_cast<size_t>(j)].t * ratio)
            r.pairs.push_back({1, leftover[static_cast<size_t>(j)].t, td});
        ++c.n_columns_reduced;
        std::vector<int> touched = Ri[static_cast<size_t>(j)];
        if (bar.size() == 1) {
            Ri[static_cast<size_t>(j)].clear();
            for (int z : touched) {
                remove_elem(R[static_cast<size_t>(z)], j);
                if (R[static_cast<size_t>(z)].empty()) {
                    Ri[static_cast<size_t>(z)].clear();
                    star_del(z);
                }
            }
            return;
        }
        std::vector<int> others;
        others.reserve(bar.size() - 1);
        for (int y : bar)
            if (y != j) others.push_back(y);
        for (int z : touched) {
            xor_sorted(R[static_cast<size_t>(z)], bar);
            ++c.n_additions;
            if (R[static_cast<size_t>(z)].empty()) {
                Ri[static_cast<size_t>(z)].clear();
                star_del(z);
            }
        }
        for (int y : others) xor_sorted(Ri[static_cast<size_t>(y)], touched);
        Ri[static_cast<size_t>(j)].clear();
        // R[j] stays if nonempty — annotation carrier for later cofaces.
    };

    auto reduce_tri = [&](int e0, int e1, int e2, value_t td) -> bool {
        int ids[3];
        int n_left = 0;
        if (e0 >= 0) ids[n_left++] = e0;
        if (e1 >= 0) ids[n_left++] = e1;
        if (e2 >= 0) ids[n_left++] = e2;
        if (!n_left) return false;
        ++c.n_simplices_enumerated;
        ++c.n_columns_assembled;
        std::vector<int> bar;
        for (int k = 0; k < n_left; ++k) {
            const int f = ids[k];
            if (f < 0 || R[static_cast<size_t>(f)].empty()) continue;
            xor_sorted(bar, R[static_cast<size_t>(f)]);
        }
        if (bar.empty()) {
            ++c.n_columns_apparent;  // I232: empty XOR = H2 birth, skip
            return false;
        }
        resolve_bar(bar, td);
        return true;
    };

    auto leftover_of = [&](index_t a, index_t b) -> int {
        auto it = edge_id.find(pack2(a, b));
        return it == edge_id.end() ? -1 : it->second;
    };

    // e is a youngest face of ⟨uvw⟩ (diameter, then later leftover id).
    auto e_youngest = [&](const BirthEdge& e, index_t w, value_t twu, value_t twv) {
        if (twu > e.t || twv > e.t) return false;
        if (twu == e.t) {
            const int oid = leftover_of(e.u, w);
            if (oid > e.id) return false;
        }
        if (twv == e.t) {
            const int oid = leftover_of(e.v, w);
            if (oid > e.id) return false;
        }
        return true;
    };

    auto tree_time = [&](index_t a, index_t b) -> value_t {
        for (const auto& p : tree_nbr[static_cast<size_t>(a)])
            if (p.first == b) return p.second;
        return kInf;
    };

    // 1-leftover apparent: leftover + two MST edges (unique tree path of
    // length 2). Full G_T common-neighbor scan would be Θ(|E|·deg).
    auto apparent_apex = [&](const BirthEdge& e) -> bool {
        for (const auto& pu : tree_nbr[static_cast<size_t>(e.u)]) {
            const index_t w = pu.first;
            if (w == e.v) continue;
            ++c.n_cofacet_probes;
            const value_t twv = tree_time(e.v, w);
            if (twv > threshold) continue;
            if (e_youngest(e, w, pu.second, twv)) return true;
        }
        return false;
    };

    auto consider_w = [&](const BirthEdge& e, index_t w, int id_uw, int id_vw) {
        if (w == e.u || w == e.v) return;
        if (id_uw < 0 && id_vw < 0) return;
        const value_t twu = (id_uw >= 0) ? leftover[static_cast<size_t>(id_uw)].t
                                         : edge_time(g, e.u, w);
        const value_t twv = (id_vw >= 0) ? leftover[static_cast<size_t>(id_vw)].t
                                         : edge_time(g, e.v, w);
        if (twu > threshold || twv > threshold) return;
        if (!e_youngest(e, w, twu, twv)) return;
        reduce_tri(e.id, id_uw, id_vw, e.t);
    };

    for (const BirthEdge& e : leftover) {
        // Pair e as apparent before multi-leftover triangles so a later
        // coface can XOR onto an older leftover (unit square).
        if (!Ri[static_cast<size_t>(e.id)].empty() && apparent_apex(e) &&
            !R[static_cast<size_t>(e.id)].empty()) {
            std::vector<int> bar = R[static_cast<size_t>(e.id)];
            resolve_bar(bar, e.t);
        }
        // Snapshot: resolve_bar mutates star.
        const std::vector<int> su = star[static_cast<size_t>(e.u)];
        const std::vector<int> sv = star[static_cast<size_t>(e.v)];
        for (int fid : su) {
            if (fid == e.id) continue;
            ++c.n_cofacet_probes;
            const BirthEdge& f = leftover[static_cast<size_t>(fid)];
            const index_t w = (f.u == e.u || f.u == e.v) ? f.v : f.u;
            consider_w(e, w, leftover_of(e.u, w), leftover_of(e.v, w));
        }
        for (int fid : sv) {
            if (fid == e.id) continue;
            ++c.n_cofacet_probes;
            const BirthEdge& f = leftover[static_cast<size_t>(fid)];
            const index_t w = (f.u == e.u || f.u == e.v) ? f.v : f.u;
            const int id_uw = leftover_of(e.u, w);
            if (id_uw >= 0) continue;  // already seen from u's star
            consider_w(e, w, id_uw, leftover_of(e.v, w));
        }
    }

    for (int i = 0; i < m; ++i) {
        if (!Ri[static_cast<size_t>(i)].empty())
            r.pairs.push_back({1, leftover[static_cast<size_t>(i)].t, kInf});
    }

    const auto t1 = std::chrono::steady_clock::now();
    c.reduce_ms = std::chrono::duration<double, std::milli>(t1 - t0).count();
    c.rss_bytes_peak = peak_rss_bytes();
    return r;
}

}  // namespace pith
