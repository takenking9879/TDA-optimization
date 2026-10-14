"""Stable Python wrapper around the PITH binary.

This is not a new persistent-homology algorithm. It calls the same
``--mode exact|scale|sparse|auto`` interface as the CLI. Iteration
numbers live in RESEARCH_LOG.md, not here.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIN = ROOT / "src" / "pith" / "build" / "pith"

MODES = ("exact", "scale", "sparse", "auto")
ENGINES = ("auto", "redzed", "implicit")


class PithError(RuntimeError):
    """The PITH binary failed or refused the request."""

    def __init__(self, message: str, returncode: int = 1, stderr: str = "") -> None:
        super().__init__(message)
        self.returncode = returncode
        self.stderr = stderr


class Refused(PithError):
    """``--mode auto`` refused (exit 3): fat H2 sparse on d∉{2,3}."""


def binary() -> Path:
    env = os.environ.get("PITH_BIN")
    path = Path(env) if env else DEFAULT_BIN
    if not path.exists():
        raise PithError(f"PITH binary missing: {path} (build src/pith or set PITH_BIN)")
    return path


def _write_points(path: Path, points) -> None:
    with path.open("w") as f:
        for row in points:
            f.write(",".join(f"{float(x):.8f}" for x in row) + "\n")


def _run(args: list[str], timeout: float | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(binary()), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


def _cmd(
    path: Path,
    *,
    maxdim: int,
    threshold: float | None,
    mode: str,
    engine: str,
    threads: int | None,
    estimate: bool = False,
) -> list[str]:
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    if engine not in ENGINES:
        raise ValueError(f"engine must be one of {ENGINES}")
    cmd = ["--points", str(path), "--maxdim", str(maxdim), "--format", "json"]
    if threshold is not None and math.isfinite(threshold):
        cmd.extend(["--threshold", str(threshold)])
    if estimate:
        cmd.append("--estimate")
    else:
        cmd.extend(["--mode", mode, "--engine", engine])
    if threads is not None:
        cmd.extend(["--threads", str(threads)])
    return cmd


def estimate(
    points,
    *,
    maxdim: int = 1,
    threshold: float | None = None,
    timeout: float | None = 30,
) -> dict[str, Any]:
    """Feasibility probe. Same JSON as ``pith --estimate --format json``."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cloud.csv"
        _write_points(path, points)
        proc = _run(_cmd(path, maxdim=maxdim, threshold=threshold, mode="exact", engine="auto", threads=1, estimate=True), timeout)
    if proc.returncode != 0:
        raise PithError(proc.stderr.strip() or "estimate failed", proc.returncode, proc.stderr)
    return json.loads(proc.stdout)


def rips(
    points,
    *,
    maxdim: int = 1,
    threshold: float | None = None,
    mode: str = "exact",
    engine: str = "auto",
    threads: int | None = 1,
    timeout: float | None = 60,
) -> dict[str, Any]:
    """Compute persistence. ``mode='scale'`` is not exact VR.

    Returns the binary JSON: ``pairs``, ``pipeline``, ``counters``.
    ``--mode auto`` raises :class:`Refused` on fat H2 sparse when
    ``d`` is not 2 or 3 (CLI exit 3).
    """
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cloud.csv"
        _write_points(path, points)
        proc = _run(
            _cmd(path, maxdim=maxdim, threshold=threshold, mode=mode, engine=engine, threads=threads),
            timeout,
        )
    if proc.returncode == 3:
        raise Refused(proc.stderr.strip() or "auto refused", 3, proc.stderr)
    if proc.returncode != 0:
        raise PithError(proc.stderr.strip() or "pith failed", proc.returncode, proc.stderr)
    out = json.loads(proc.stdout)
    pairs = out.get("pairs") or []
    ess = {d: 0 for d in range(maxdim + 1)}
    finite = {d: 0 for d in range(maxdim + 1)}
    for p in pairs:
        d = int(p["dim"])
        if d > maxdim:
            continue
        death = p.get("death")
        if death is None or (isinstance(death, float) and not math.isfinite(death)):
            ess[d] = ess.get(d, 0) + 1
        else:
            finite[d] = finite.get(d, 0) + 1
    out["ess"] = ess
    out["n_finite"] = finite
    out["mode"] = mode
    out["stderr"] = proc.stderr
    return out


__all__ = ["MODES", "ENGINES", "PithError", "Refused", "binary", "estimate", "rips"]
