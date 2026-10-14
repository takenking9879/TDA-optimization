#!/usr/bin/env python3
"""One receipt per README scale/sparse accuracy claim. No new PH runs."""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "results" / "consolidation"


def _load(name: str) -> dict | list:
    p = OUT / name
    return json.loads(p.read_text()) if p.exists() else {}


def main() -> int:
    wass = _load("wasserstein.json")
    sl = _load("sparse_limits.json")
    sparse_rows = sl.get("sparse") if isinstance(sl, dict) else sl
    sparse_rows = sparse_rows or []
    claims = []

    def wass_row(name: str):
        for r in wass if isinstance(wass, list) else []:
            if r.get("name") == name:
                return r
        return {}

    def sparse_row(name: str, n: int):
        for r in sparse_rows:
            if r.get("name") == name and r.get("n") == n:
                return r
        return {}

    for name in ("figure8", "circle_noisy", "nested_loops", "many_loops"):
        w = wass_row(name)
        s = sparse_row(name, 400)
        claims.append(
            {
                "readme_row": "2D loops ≈ VR",
                "name": name,
                "n": 400,
                "source": ["wasserstein.json", "sparse_limits.json"],
                "exact_match_ripser": (s.get("exact_vs_ripser") or {}).get("exact_match"),
                "scale_unmatched": (s.get("scale_vs_ripser") or {}).get("unmatched"),
                "scale_bn_h1": w.get("scale_bn_h1"),
                "scale_w1_h1": w.get("scale_w1_h1"),
                "sparse_unmatched": (s.get("sparse_vs_ripser") or {}).get("unmatched"),
                "sparse_w1_h1": (s.get("sparse_vs_ripser") or {}).get("wasserstein1_h1"),
                "ess_scale": (s.get("scale_vs_ripser") or {}).get("ess"),
                "ess_sparse": (s.get("sparse_vs_ripser") or {}).get("ess"),
            }
        )

    s = sparse_row("sphere", 400)
    w = wass_row("sphere")
    claims.append(
        {
            "readme_row": "sphere",
            "name": "sphere",
            "n": 400,
            "source": ["wasserstein.json", "sparse_limits.json"],
            "exact_match_ripser": (s.get("exact_vs_ripser") or {}).get("exact_match"),
            "scale_unmatched": (s.get("scale_vs_ripser") or {}).get("unmatched"),
            "scale_bn_h1": w.get("scale_bn_h1"),
            "scale_w1_h1": w.get("scale_w1_h1"),
            "scale_ess_h2": ((s.get("ess_scale") or {}).get("2")),
        }
    )

    s = sparse_row("nested_loops", 400)
    claims.append(
        {
            "readme_row": "sparse nested_loops W1",
            "name": "nested_loops",
            "n": 400,
            "source": ["sparse_limits.json"],
            "sparse_unmatched": (s.get("sparse_vs_ripser") or {}).get("unmatched"),
            "sparse_w1_h1": (s.get("sparse_vs_ripser") or {}).get("wasserstein1_h1"),
            "sparse_ess_h1": ((s.get("ess_sparse") or {}).get("1")),
            "ripser_ess_h1": ((s.get("ess_ripser") or {}).get("1")),
        }
    )

    # multi_cavities / mixed / held-out live in limits + report tables.
    lim = _load("limits.json")
    for name, n, note in (
        ("multi_cavities", 300, "ess H2=3, unmatched 52, bn H1 0.041"),
        ("mixed_1d2d3d", 300, "exact RedZeD-cc 33 ms vs Ripser 0.14 s; scale unmatched 35"),
        ("disconnected_circles", 400, "held-out ess H0=2 H1=2"),
        ("grid_holes", 400, "post-freeze ess H1=2"),
        ("two_spheres_apart", 400, "post-freeze ess H2=2 unmatched 45"),
    ):
        hits = [
            r
            for r in (lim.get("receipts") or [])
            if r.get("name") == name and r.get("n") == n
        ]
        claims.append(
            {
                "readme_row": note,
                "name": name,
                "n": n,
                "source": ["limits.json"],
                "n_limit_rows": len(hits),
                "methods": sorted({r.get("method") for r in hits if r.get("method")}),
            }
        )

    dest = OUT / "topology_claims.json"
    dest.write_text(
        json.dumps(
            {
                "note": "README accuracy table ↔ existing receipts. No new PH.",
                "claims": claims,
            },
            indent=2,
        )
    )
    print("wrote", dest, "n=", len(claims))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
