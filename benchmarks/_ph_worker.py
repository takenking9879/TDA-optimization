#!/usr/bin/env python3
"""In-process persistence worker (giotto-ph / GUDHI) for timeout isolation.

AGPL note: giotto-ph is called as an installed oracle only. Do not copy its
sources into this repository.
"""

from __future__ import annotations

import json
import sys
import time


def _pairs_from_dgms(dgms):
    pairs = []
    for dim, dgm in enumerate(dgms):
        for row in dgm:
            b, d = float(row[0]), float(row[1])
            pairs.append({"dim": int(dim), "birth": b, "death": d})
    return pairs


def run_giotto(path, T, maxdim, n_threads, collapse):
    import numpy as np
    from gph import ripser_parallel

    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    r = ripser_parallel(
        pts,
        maxdim=int(maxdim),
        thresh=float(T),
        n_threads=int(n_threads),
        collapse_edges=bool(collapse),
    )
    dt = time.perf_counter() - t0
    return {"ok": True, "wall_s": dt, "pairs": _pairs_from_dgms(r["dgms"])}


def run_gudhi_rips(path, T, maxdim):
    import gudhi
    import numpy as np

    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    st = gudhi.RipsComplex(points=pts, max_edge_length=float(T)).create_simplex_tree(
        max_dimension=int(maxdim) + 1
    )
    pers = st.persistence()
    dt = time.perf_counter() - t0
    pairs = []
    for dim, (b, d) in pers:
        if dim > int(maxdim):
            continue
        pairs.append(
            {
                "dim": int(dim),
                "birth": float(b),
                "death": float(d) if d != float("inf") else float("inf"),
            }
        )
    return {"ok": True, "wall_s": dt, "pairs": pairs, "n_simplices": int(st.num_simplices())}


def run_gudhi_alpha(path, maxdim):
    import gudhi
    import numpy as np

    pts = np.loadtxt(path, delimiter=",")
    t0 = time.perf_counter()
    st = gudhi.AlphaComplex(points=pts).create_simplex_tree()
    st.compute_persistence()
    dt = time.perf_counter() - t0
    pairs = []
    for dim, (b, d) in st.persistence():
        if dim > int(maxdim):
            continue
        pairs.append(
            {
                "dim": int(dim),
                "birth": float(b),
                "death": float(d) if d != float("inf") else float("inf"),
            }
        )
    return {"ok": True, "wall_s": dt, "pairs": pairs, "n_simplices": int(st.num_simplices())}


def main():
    method = sys.argv[1]
    if method == "giotto":
        path, T, maxdim, n_threads, collapse = sys.argv[2:7]
        rec = run_giotto(path, T, maxdim, n_threads, collapse == "1")
    elif method == "gudhi-rips":
        path, T, maxdim = sys.argv[2:5]
        rec = run_gudhi_rips(path, T, maxdim)
    elif method == "gudhi-alpha":
        path, maxdim = sys.argv[2:4]
        rec = run_gudhi_alpha(path, maxdim)
    else:
        rec = {"ok": False, "error": f"unknown method {method}"}
    print(json.dumps(rec, default=str))


if __name__ == "__main__":
    main()
