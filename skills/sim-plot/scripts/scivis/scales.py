"""Axis scales for CFD/MD data: explicit, justified, labelled (Rougier: scales chapter)."""
from __future__ import annotations

import numpy as np
from matplotlib.ticker import FixedLocator, LogLocator, NullFormatter

from . import palettes as P
from . import theme as S
from .layout import halo


def set_symlog(ax, axis: str, linthresh: float, *, linscale: float = 1.0, note: str | None = None):
    """Signed data spanning decades (residual changes, dp, forces): linear inside +/-linthresh.

    ``linthresh`` has no automatic default on purpose: it is a physical choice (the noise
    floor / smallest meaningful magnitude) and must be stated in the caption.
    """
    if axis not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'")
    if linthresh is None or not np.isfinite(linthresh) or linthresh <= 0:
        raise ValueError("Supply a positive, physically justified linthresh.")
    getattr(ax, f"set_{axis}scale")("symlog", linthresh=linthresh, linscale=linscale)
    ax._scivis_symlog = {"axis": axis, "linthresh": float(linthresh), "note": note}
    return ax


def decade_ticks(ax, axis: str = "y", step: int = 3, minor: bool = False):
    """Label every ``step``-th decade on a log axis (3-4 ticks, no dense minor clutter)."""
    a = getattr(ax, f"{axis}axis")
    lo, hi = sorted(getattr(ax, f"get_{axis}lim")())
    if lo <= 0:
        raise ValueError("log axis needs positive limits")
    e0, e1 = int(np.ceil(np.log10(lo) - 1e-9)), int(np.floor(np.log10(hi) + 1e-9))
    ticks = [10.0 ** e for e in range(e0, e1 + 1, step)]
    a.set_major_locator(FixedLocator(ticks))
    if not minor:
        a.set_minor_locator(LogLocator(subs=(), numticks=0))
        a.set_minor_formatter(NullFormatter())
    return ticks


def slope_guide(ax, x0, x1, y0, slope, label=None, *, color=P.GREY_DARK, lw=None, label_dy_pt=3.0,
                side="end"):
    """Dashed reference line y = y0 (x/x0)**slope on a log-log axis, with a haloed label.

    Use to show scaling laws (t, t^2 in MSD; k^-5/3 in spectra) without a legend entry.
    """
    if ax.get_xscale() != "log" or ax.get_yscale() != "log":
        raise ValueError("slope_guide expects a log-log axes")
    if not (x0 > 0 and x1 > 0 and y0 > 0 and x0 != x1):
        raise ValueError("slope_guide needs positive, distinct x0/x1 and y0 > 0")
    xs = np.array([x0, x1], float)
    ys = y0 * (xs / x0) ** slope
    ax.plot(xs, ys, color=color, lw=lw or S.get("spine", 0.6), ls=(0, (2, 2)), zorder=2)
    if label:
        i = 1 if side == "end" else 0
        t = ax.annotate(label, xy=(xs[i], ys[i]), xytext=(2.0, label_dy_pt), textcoords="offset points",
                        ha="left" if side == "end" else "right", va="bottom", color=color,
                        fontsize=S.get("annot", 6.0), annotation_clip=False)
        halo(t, lw=1.6)
    return ys
