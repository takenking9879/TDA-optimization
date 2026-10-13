#!/usr/bin/env python3
"""H07 prototype: Reduced Vietoris–Rips 2-complex (arXiv:2307.16333) vs Ripser H1.

Not a flag complex. Exact H1 claimed by the paper. n<=40.
"""

from __future__ import annotations

import math
from typing import Iterable


def diam(verts: Iterable[int], D) -> float:
    vs = list(verts)
    m = 0.0
    for i, a in enumerate(vs):
        for b in vs[i + 1 :]:
            m = max(m, float(D[a][b]))
    return m


def cmp_simplex(sig, tau, D) -> bool:
    ds, dt = diam(sig, D), diam(tau, D)
    if ds != dt:
        return ds < dt
    if len(sig) != len(tau):
        return len(sig) < len(tau)
    return tuple(sorted(sig)) < tuple(sorted(tau))


def lune(y: int, z: int, D, n: int) -> list[int]:
    yz = (y, z)
    out = []
    for x in range(n):
        if x in (y, z):
            continue
        if cmp_simplex((y, x), yz, D) and cmp_simplex((z, x), yz, D):
            out.append(x)
    return out


def lune_function(y: int, z: int, D, n: int) -> list[int]:
    V = lune(y, z, D, n)
    parent = {v: v for v in V}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    yz = (y, z)
    for i, p in enumerate(V):
        for q in V[i + 1 :]:
            if cmp_simplex((p, q), yz, D):
                parent[find(p)] = find(q)
    comps: dict[int, list[int]] = {}
    for v in V:
        comps.setdefault(find(v), []).append(v)
    return [min(c) for c in comps.values()]


def build_reduced_2_complex(D, T: float):
    n = len(D)
    edges = [(i, j) for i in range(n) for j in range(i + 1, n) if D[i][j] <= T]
    triangles = set()
    for y, z in edges:
        for x in lune_function(y, z, D, n):
            if diam((x, y, z), D) <= T:
                triangles.add(tuple(sorted((x, y, z))))
    return edges, triangles


def persist_h1(n: int, D, edges, triangles):
    edges = sorted(edges, key=lambda e: (D[e[0]][e[1]], e[0], e[1]))
    parent = list(range(n))
    rank = [0] * n

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    leftover = []
    h0_deaths = []
    for u, v in edges:
        a, b = find(u), find(v)
        t = D[u][v]
        if a != b:
            if rank[a] < rank[b]:
                a, b = b, a
            parent[b] = a
            if rank[a] == rank[b]:
                rank[a] += 1
            h0_deaths.append(t)
        else:
            leftover.append((u, v, t, len(leftover)))

    id_of = {(min(u, v), max(u, v)): i for i, (u, v, _, i) in enumerate(leftover)}
    # rebuild leftover ids
    leftover = [(u, v, t, k) for k, (u, v, t, _) in enumerate(leftover)]
    id_of = {(min(u, v), max(u, v)): k for k, (u, v, t, _) in enumerate(leftover)}

    cols = []
    for a, b, c in triangles:
        t = max(D[a][b], D[a][c], D[b][c])
        faces = []
        for e in ((a, b), (a, c), (b, c)):
            key = (min(e), max(e))
            if key in id_of:
                faces.append(id_of[key])
        if faces:
            cols.append((t, tuple(sorted((a, b, c))), faces))
    cols.sort(key=lambda x: (x[0], x[1]))

    m = len(leftover)
    pivot = [-1] * m
    reduced = []
    paired = [False] * m
    h1 = []

    def xor_sorted(a, b):
        out = []
        i = j = 0
        a = sorted(a, reverse=True)
        b = sorted(b, reverse=True)
        while i < len(a) and j < len(b):
            if a[i] == b[j]:
                i += 1
                j += 1
            elif a[i] > b[j]:
                out.append(a[i])
                i += 1
            else:
                out.append(b[j])
                j += 1
        out.extend(a[i:])
        out.extend(b[j:])
        return out

    def choose_pivot(col):
        best, bt = -1, -1.0
        for i in col:
            t = leftover[i][2]
            if t > bt or (t == bt and i > best):
                bt = t
                best = i
        return best

    for t, _key, faces in cols:
        col = list(faces)
        guard = 0
        while col and guard < 20000:
            guard += 1
            p = choose_pivot(col)
            if p < 0 or pivot[p] < 0:
                break
            col = xor_sorted(col, reduced[pivot[p]])
        if not col:
            continue
        p = choose_pivot(col)
        if p < 0:
            continue
        h1.append((leftover[p][2], t))
        pivot[p] = len(reduced)
        paired[p] = True
        reduced.append(col)

    h1_ess = [leftover[i][2] for i in range(m) if not paired[i]]
    h0_ess = n - len(h0_deaths)
    return {
        "n_edges": len(edges),
        "n_triangles": len(triangles),
        "h0_deaths": h0_deaths,
        "h0_ess": h0_ess,
        "h1_finite": h1,
        "h1_ess": h1_ess,
    }


def pairwise(pts):
    import numpy as np

    x = np.asarray(pts, dtype=float)
    d = ((x[:, None, :] - x[None, :, :]) ** 2).sum(-1)
    return np.sqrt(d)
