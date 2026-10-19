"""Colour normalisation and field bookkeeping (no implicit data changes)."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from matplotlib import colors as mcolors


def make_norm(scale: str, vmin: float, vmax: float, *, center: float = 0.0,
              linthresh: float | None = None, boundaries: Sequence[float] | None = None,
              ncolors: int = 256):
    """Explicit-limit norms. Limits are physical choices that must be declared, not guessed."""
    if not np.isfinite([vmin, vmax]).all() or not vmin < vmax:
        raise ValueError("Require finite vmin < vmax. Declare physical limits for a constant field.")
    if scale == "linear":
        return mcolors.Normalize(vmin, vmax, clip=False)
    if scale == "log":
        if vmin <= 0:
            raise ValueError("LogNorm requires vmin > 0 and strictly positive valid data.")
        return mcolors.LogNorm(vmin, vmax, clip=False)
    if scale == "symmetric":
        if not vmin < center < vmax or not np.isclose(center - vmin, vmax - center, rtol=1e-9, atol=0):
            raise ValueError("Symmetric scale requires equal physical spans about the center.")
        return mcolors.Normalize(vmin, vmax, clip=False)
    if scale == "two-slope":
        if not vmin < center < vmax:
            raise ValueError("Two-slope scale requires vmin < center < vmax.")
        return mcolors.TwoSlopeNorm(vcenter=center, vmin=vmin, vmax=vmax)
    if scale == "symlog":
        if linthresh is None or not np.isfinite(linthresh) or linthresh <= 0:
            raise ValueError("Supply a physically justified positive linthresh.")
        if not vmin < 0 < vmax or not np.isclose(-vmin, vmax, rtol=1e-9, atol=0):
            raise ValueError("This signed symlog helper requires a symmetric domain about zero.")
        return mcolors.SymLogNorm(linthresh, vmin=vmin, vmax=vmax, base=10, clip=False)
    if scale == "boundary":
        b = np.asarray(boundaries, float)
        if b.ndim != 1 or b.size < 2 or not np.isfinite(b).all() or not np.all(np.diff(b) > 0):
            raise ValueError("Supply strictly increasing finite boundaries.")
        if not np.isclose(b[0], vmin) or not np.isclose(b[-1], vmax):
            raise ValueError("Boundary endpoints must match vmin/vmax.")
        return mcolors.BoundaryNorm(b, ncolors=ncolors, clip=False)
    raise ValueError(f"Unknown scale {scale!r}")


def field_status(values, norm) -> dict[str, Any]:
    """Counts of valid/masked/out-of-range cells -> colorbar extend + caption numbers."""
    a = np.ma.masked_invalid(np.ma.asarray(values, dtype=float))
    valid = a.compressed()
    if not valid.size:
        raise ValueError("No valid field values.")
    if isinstance(norm, mcolors.LogNorm) and np.any(valid <= 0):
        raise ValueError("LogNorm cannot silently hide zeros/negative values. "
                         "Choose another scale or provide a documented exclusion mask.")
    lo, hi = int(np.sum(valid < norm.vmin)), int(np.sum(valid > norm.vmax))
    extend = "both" if lo and hi else "min" if lo else "max" if hi else "neither"
    return {"n_total": int(a.size), "n_valid": int(valid.size),
            "n_masked": int(a.size - valid.size), "data_min": float(valid.min()),
            "data_max": float(valid.max()), "below_range": lo, "above_range": hi,
            "clipped_fraction": float((lo + hi) / valid.size),
            "vmin": float(norm.vmin), "vmax": float(norm.vmax), "extend": extend,
            "normalization": type(norm).__name__}
