"""2-D field drawing used by sim-field, the recipes and zoom insets.

No Delaunay triangulation, no implicit cell<->point conversion, no hidden fill of NaN.
"""
from __future__ import annotations

from typing import Sequence

import matplotlib.tri as mtri
import numpy as np

from . import palettes as P
from .norms import field_status


def cell_aspect(xlim, ylim) -> float:
    """Height/width of a physical window; feed to make_canvas(cell_aspect=...)."""
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    if not (dx > 0 and dy > 0):
        raise ValueError("window needs xlim[0] < xlim[1] and ylim[0] < ylim[1]")
    return float(dy / dx)


def explicit_levels(levels, limits):
    levels = np.asarray(levels, float)
    if levels.ndim != 1 or len(levels) < 2 or not np.isfinite(levels).all() or not np.all(np.diff(levels) > 0):
        raise ValueError("Contour levels must be finite and strictly increasing.")
    if not np.isclose(levels[0], limits[0]) or not np.isclose(levels[-1], limits[1]):
        raise ValueError("Contour endpoints must match the declared shared color limits.")
    return levels


def prepare_field(data: dict, grid: str, association: str, method: str, norm, *, levels=None, limits=None):
    """Validate geometry/values; return a ``draw(ax) -> artist`` closure plus statistics.

    The closure can be called again on an inset axes: the zoom shares cmap, norm and data.
    """
    values = np.ma.masked_invalid(np.asarray(data["values"], dtype=float))
    if "mask" in data:
        mask = np.asarray(data["mask"], dtype=bool)
        if mask.shape != values.shape:
            raise ValueError("Value mask shape does not match values.")
        values = np.ma.masked_where(mask, values)
    extra = {}
    if grid == "triangular":
        if "triangles" not in data:
            raise ValueError("Native triangle connectivity required. No automatic convex-hull triangulation.")
        triangles = np.asarray(data["triangles"])
        if not np.issubdtype(triangles.dtype, np.integer) or triangles.ndim != 2 or triangles.shape[1] != 3:
            raise ValueError("triangles must be an integer array of shape (n, 3).")
        tri = mtri.Triangulation(data["x"], data["y"], triangles=triangles)
        tmask = np.asarray(data.get("triangle_mask", np.zeros(len(triangles), dtype=bool)), dtype=bool)
        if tmask.shape != (len(triangles),):
            raise ValueError("triangle_mask must have one entry per triangle.")
        if association == "cell":
            if values.shape != (len(triangles),) or method != "tripcolor":
                raise ValueError("Cell data requires one value per triangle and method=tripcolor.")
            tmask = tmask | np.ma.getmaskarray(values)
            tri.set_mask(tmask)
            stats = field_status(np.ma.array(values, mask=tmask), norm)

            def draw(ax, cmap):
                return ax.tripcolor(tri, facecolors=values.filled(0), shading="flat", cmap=cmap,
                                    norm=norm, rasterized=True)
        elif association == "point":
            if values.shape != (len(data["x"]),) or method != "tricontourf":
                raise ValueError("Point triangular fields use method=tricontourf with explicit levels.")
            tmask = tmask | np.ma.getmaskarray(values)[triangles].any(axis=1)
            tri.set_mask(tmask)
            used = np.zeros(values.size, dtype=bool)
            used[triangles[~tmask].ravel()] = True
            stats = field_status(np.ma.array(values, mask=np.ma.getmaskarray(values) | ~used), norm)
            lv = explicit_levels(levels, limits)
            ext = stats["extend"]

            def draw(ax, cmap):
                return ax.tricontourf(tri, values.filled(0), levels=lv, cmap=cmap, norm=norm, extend=ext)
        else:
            raise ValueError("association must be cell or point.")
        stats["masked_triangles"] = int(tmask.sum())
        x, y = np.asarray(data["x"], float), np.asarray(data["y"], float)
        extent = (float(x.min()), float(x.max()), float(y.min()), float(y.max()))
    elif grid == "rectilinear":
        x, y = np.asarray(data["x"], float), np.asarray(data["y"], float)
        if x.ndim != 1 or y.ndim != 1 or not np.isfinite(x).all() or not np.isfinite(y).all():
            raise ValueError("Rectilinear x/y must be finite 1D coordinates.")
        if len(x) < 2 or len(y) < 2 or not np.all(np.diff(x) > 0) or not np.all(np.diff(y) > 0):
            raise ValueError("x/y must increase strictly. Preserve orientation explicitly before rendering.")
        stats = field_status(values, norm)
        if association == "cell" and method == "pcolormesh":
            if values.shape != (len(y) - 1, len(x) - 1):
                raise ValueError("Cell values need actual edge coordinates: shape=(len(y)-1,len(x)-1).")

            def draw(ax, cmap):
                return ax.pcolormesh(x, y, values, shading="flat", cmap=cmap, norm=norm,
                                     rasterized=True, antialiased=False)
        elif association == "point" and method == "contourf":
            if values.shape != (len(y), len(x)):
                raise ValueError("Point values must match the coordinate grid.")
            lv = explicit_levels(levels, limits)
            ext = stats["extend"]

            def draw(ax, cmap):
                return ax.contourf(x, y, values, levels=lv, cmap=cmap, norm=norm, extend=ext,
                                   corner_mask=False)
        else:
            raise ValueError("Use cell+pcolormesh or point+contourf. No implicit association conversion.")
        extent = (float(x[0]), float(x[-1]), float(y[0]), float(y[-1]))
    else:
        raise ValueError("This renderer supports rectilinear and triangular 2D fields only.")
    return draw, stats, extent


def add_streamlines(ax, x, y, u, v, *, density=1.1, color=P.INK, lw=0.35, seeds="auto",
                    n_seeds=15, speed_lw: tuple[float, float] | None = None, zorder=3):
    """Streamlines of a regular-grid velocity field. NaN (solid) cells stay masked: lines stop there.

    seeds : 'auto' (matplotlib density), 'inlet' (n_seeds along the left edge) or an (n,2) array.
    speed_lw=(lo, hi) maps local speed linearly to line width (an encoding: say so in the caption).
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    u = np.ma.masked_invalid(np.asarray(u, float))
    v = np.ma.masked_invalid(np.asarray(v, float))
    if u.shape != (len(y), len(x)) or v.shape != u.shape:
        raise ValueError("streamlines need u, v on a regular grid of shape (len(y), len(x))")
    kw = {}
    if isinstance(seeds, str):
        if seeds == "inlet":
            pad = 0.01 * (x[-1] - x[0])
            kw["start_points"] = np.c_[np.full(n_seeds, x[0] + pad),
                                        np.linspace(y[0] + 0.05 * (y[-1] - y[0]), y[-1] - 0.05 * (y[-1] - y[0]), n_seeds)]
        elif seeds != "auto":
            raise ValueError("seeds must be 'auto', 'inlet' or an (n,2) array")
    else:
        kw["start_points"] = np.asarray(seeds, float)
    lwv = lw
    if speed_lw is not None:
        sp = np.hypot(u, v)
        lwv = speed_lw[0] + (speed_lw[1] - speed_lw[0]) * sp / max(float(sp.max()), 1e-300)
    sp_ = ax.streamplot(x, y, u, v, color=color, linewidth=lwv, density=density, arrowstyle="-", zorder=zorder, **kw)
    return sp_
