#pragma once

#include "graph.hpp"

#include <numeric>
#include <vector>

namespace pith {

// Def 2.28 of Koyama–Mémoli–Robins–Turner (arXiv:2307.16333), restricted
// to 1-simplices: diameter, then lex on sorted vertex labels. Dimension
// is equal so it does not appear.
inline bool edge_before(index_t y, index_t z, value_t tyz, index_t a, index_t b, value_t tab) {
    if (tyz < tab) return true;
    if (tyz > tab) return false;
    if (y > z) std::swap(y, z);
    if (a > b) std::swap(a, b);
    if (y != a) return y < a;
    return z < b;
}

// Reduced VR 2-simplices (Def 3.7): for every edge ⟨yz⟩, one vertex per
// connected component of lune(⟨yz⟩). Same code path for every metric —
// not a circle/sphere/torus special case. Size is O(|E|) triangles when
// the lune-component count is bounded (Euclidean doubling, Lemma 3.9).
// PH₁ of this 2-complex is claimed isomorphic to VR; I224 checks that.
inline std::vector<Triangle> build_reduced_triangles(const Graph& g, value_t T) {
    std::vector<Triangle> tris;
    if (g.n <= 2) return tris;
    tris.reserve(g.edges.size());

    const int n = g.n;
    std::vector<index_t> lune;
    lune.reserve(64);
    std::vector<int> idx(static_cast<size_t>(n), -1);
    std::vector<char> in_lune(static_cast<size_t>(n), 0);
    std::vector<index_t> parent, rnk, comp_min;

    auto find = [&](auto&& self, index_t x) -> index_t {
        return parent[static_cast<size_t>(x)] == x
                   ? x
                   : parent[static_cast<size_t>(x)] = self(self, parent[static_cast<size_t>(x)]);
    };
    auto unite = [&](index_t a, index_t b) {
        a = find(find, a);
        b = find(find, b);
        if (a == b) return;
        if (rnk[static_cast<size_t>(a)] < rnk[static_cast<size_t>(b)]) std::swap(a, b);
        parent[static_cast<size_t>(b)] = a;
        if (rnk[static_cast<size_t>(a)] == rnk[static_cast<size_t>(b)]) ++rnk[static_cast<size_t>(a)];
    };

    for (const Edge& e : g.edges) {
        if (e.t > T) continue;
        const index_t y = e.u;
        const index_t z = e.v;
        const value_t t = e.t;
        lune.clear();
        const auto& ny = g.neighbors[static_cast<size_t>(y)];
        const auto& nz = g.neighbors[static_cast<size_t>(z)];
        size_t i = 0, j = 0;
        while (i < ny.size() && j < nz.size()) {
            if (ny[i].first < nz[j].first) {
                ++i;
                continue;
            }
            if (nz[j].first < ny[i].first) {
                ++j;
                continue;
            }
            const index_t x = ny[i].first;
            if (x != y && x != z) {
                const value_t tyx = ny[i].second;
                const value_t tzx = nz[j].second;
                if (edge_before(y, x, tyx, y, z, t) && edge_before(z, x, tzx, y, z, t))
                    lune.push_back(x);
            }
            ++i;
            ++j;
        }
        if (lune.empty()) continue;

        const int L = static_cast<int>(lune.size());
        parent.resize(static_cast<size_t>(L));
        rnk.assign(static_cast<size_t>(L), 0);
        std::iota(parent.begin(), parent.end(), 0);
        for (int k = 0; k < L; ++k) {
            idx[static_cast<size_t>(lune[static_cast<size_t>(k)])] = k;
            in_lune[static_cast<size_t>(lune[static_cast<size_t>(k)])] = 1;
        }

        // Connectivity of the lune graph (Def 3.3): {p,q} iff ⟨pq⟩ < ⟨yz⟩.
        // Neighbor walk is O(|lune|·deg); all-pairs would need a dense matrix.
        for (int k = 0; k < L; ++k) {
            const index_t p = lune[static_cast<size_t>(k)];
            for (const auto& nw : g.neighbors[static_cast<size_t>(p)]) {
                const index_t q = nw.first;
                if (q <= p || !in_lune[static_cast<size_t>(q)]) continue;
                if (edge_before(p, q, nw.second, y, z, t))
                    unite(k, idx[static_cast<size_t>(q)]);
            }
        }

        comp_min.assign(static_cast<size_t>(L), n);
        for (int k = 0; k < L; ++k) {
            const index_t r = find(find, k);
            const index_t x = lune[static_cast<size_t>(k)];
            if (x < comp_min[static_cast<size_t>(r)]) comp_min[static_cast<size_t>(r)] = x;
        }
        for (int k = 0; k < L; ++k) {
            const index_t x = comp_min[static_cast<size_t>(k)];
            if (x >= n) continue;
            // x ∈ lune(⟨yz⟩) ⇒ both spokes precede ⟨yz⟩, so diam = t.
            if (t <= T) tris.push_back({x, y, z, t});
        }

        for (int k = 0; k < L; ++k) {
            idx[static_cast<size_t>(lune[static_cast<size_t>(k)])] = -1;
            in_lune[static_cast<size_t>(lune[static_cast<size_t>(k)])] = 0;
        }
    }
    return tris;
}

}  // namespace pith
