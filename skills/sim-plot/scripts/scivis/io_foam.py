"""Readers for OpenFOAM function-object output (postProcessing/*.dat) and residual logs."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

_NUM = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")


def _tok(v: str) -> float:
    v = v.strip()
    if v.lower() in ("n/a", "nan", "-nan"):
        return np.nan
    if v.lower() in ("inf", "+inf", "-inf"):
        raise ValueError(f"infinite value {v!r} in OpenFOAM data (diverged run?)")
    return float(v)


def read_foam_dat(path, *, columns: list[str] | None = None, restart: str = "error"):
    """Read a whitespace-separated OpenFOAM .dat file with '#' comment header.

    Column names come from the last '#' header line whose first token is Time/Iteration, or
    from ``columns``. Brackets ``(``/``)`` split vector columns (``(Fx Fy Fz)`` -> three
    columns). Rows with a different column count than the first data row raise (no silent
    truncation). If Time is not strictly increasing (restarted run, appended files) the
    behaviour is chosen by ``restart``: "error" (default) raises; "last" keeps the final monotone segment (a data reduction: state it),
    "keep" returns everything.

    Returns dict name -> 1-D array. Tested on forceCoeffs- and residuals-style files; check
    your OpenFOAM version's header if a column name differs.
    """
    names, rows = None, []
    with open(path, encoding="utf-8", errors="replace") as fh:
        for ln, line in enumerate(fh, 1):
            s = line.strip()
            if not s:
                continue
            if s.startswith("#"):
                toks = s.lstrip("#").replace("(", " ").replace(")", " ").split()
                if toks and toks[0].lower() in ("time", "iteration", "iter"):
                    names = toks
                continue
            toks = s.replace("(", " ").replace(")", " ").split()
            try:
                rows.append([_tok(v) for v in toks])
            except ValueError as exc:
                raise ValueError(f"{path}:{ln}: {exc}") from None
    if not rows:
        raise ValueError(f"no numeric rows in {path}")
    n = len(rows[0])
    bad = [i for i, r in enumerate(rows) if len(r) != n]
    if bad:
        raise ValueError(f"{path}: {len(bad)} rows have a column count different from the first "
                         f"({n}); first at data row {bad[0]}. Pass a cleaned file.")
    arr = np.array(rows, float)
    names = list(columns) if columns else (names or [f"col{i}" for i in range(n)])
    if len(names) != n:
        # header names for vector columns are usually not expanded; fall back to generic tails
        names = names[:n] + [f"col{i}" for i in range(len(names), n)]
    t = arr[:, 0]
    if restart != "keep" and np.any(np.diff(t) <= 0):
        if restart == "error":
            raise ValueError(f"{path}: first column is not strictly increasing (restart/append?)")
        cut = np.where(np.diff(t) <= 0)[0].max() + 1
        arr = arr[cut:]
    return {k: arr[:, i] for i, k in enumerate(names)}


def read_foam_log_residuals(path) -> dict[str, np.ndarray]:
    """Initial residuals per field from a solver log: 'Solving for Ux, Initial residual = ...'."""
    pat = re.compile(r"Solving for (\w+), Initial residual = ([0-9.eE+-]+)")
    out: dict[str, list[float]] = {}
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        m = pat.search(line)
        if m:
            out.setdefault(m.group(1), []).append(float(m.group(2)))
    if not out:
        raise ValueError(f"no 'Solving for ... Initial residual' lines in {path}")
    return {k: np.asarray(v) for k, v in out.items()}
