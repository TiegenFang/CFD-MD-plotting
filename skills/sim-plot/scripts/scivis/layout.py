"""Canvas, multi-panel alignment and figure furniture, after Rougier's layout chapters.

Taken from the book, and where it shows up here
  * Build the figure at its final physical size; never rescale it (typography chapter:
    font sizes are physical).                                  -> make_canvas(width mm)
  * GridSpec with ratios beats subplots/add_axes.              -> make_canvas(... ratios)
  * Equal panels: titles, labels and colourbars live OUTSIDE the axes cell.
                                                    -> add_colorbar, panel_labels
  * Standard layouts: image + colourbar of equal height; scatter + aligned marginals.
                                                    -> add_colorbar, marginal_canvas
  * Small multiples with ghost series (rule 8).      -> small_multiples
  * Zoom annotation with connectors (ornaments).     -> zoom_inset
  * Do not mislead (rule 7): marker AREA encodes the value.  -> area_sizes
  * Text over images needs a thin outline, not a box.        -> halo, halo_clabel
  * Dense data (optimisation chapter): alpha floor, hist2d/hexbin.   -> density_scatter
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import matplotlib as mpl
import matplotlib.patheffects as pe
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ticker import AutoMinorLocator, MaxNLocator, NullLocator

from . import palettes as P
from . import theme as S

MM = 1.0 / 25.4


def mm(x: float) -> float:
    """millimetres -> inches"""
    return x * MM


# --------------------------------------------------------------------------
# Axes dressing shared by every axes the kit creates
# --------------------------------------------------------------------------
def style_axes(ax, *, categorical_x: bool = False, nbins: int | None = None) -> None:
    """House tick policy for a data axes: ~5 intervals, nice steps, mirrored minor ticks.

    rcParams already carry spines/tick direction; locators cannot live in rcParams.
    """
    st = S.STATE
    theme = st.get("theme") or S.load_theme()
    a = theme["axes"]
    nb = nbins or a["major_intervals"]
    for key, axis in (("x", ax.xaxis), ("y", ax.yaxis)):
        if key == "x" and categorical_x:
            axis.set_minor_locator(NullLocator())
            continue
        if getattr(ax, f"get_{key}scale")() == "linear":
            axis.set_major_locator(MaxNLocator(nbins=nb, steps=[1, 2, 2.5, 5, 10], min_n_ticks=3))
            minor_on = bool(st.get("minor", True) and a["minor_ticks"])
            axis.set_minor_locator(AutoMinorLocator(2) if minor_on else NullLocator())


# --------------------------------------------------------------------------
# Canvas
# --------------------------------------------------------------------------
@dataclass
class Canvas:
    fig: Figure
    gs: mpl.gridspec.GridSpec
    W: float          # mm
    H: float          # mm
    margins: tuple    # (left, bottom, right, top) mm
    hgap: float
    wgap: float
    axes: list = field(default_factory=list)
    autofit: bool = False

    def ax(self, i=0, j=0, *, field: bool = False, style: bool = True, **kw):
        """Axes in grid cell [i, j]; i, j may be slices. ``field=True`` skips tick locators."""
        ax = self.fig.add_subplot(self.gs[i, j], **kw)
        if style and not field:
            style_axes(ax)
        self.axes.append(ax)
        return ax

    def size_mm(self, ax):
        b = ax.get_position()
        return b.width * self.W, b.height * self.H

    def fit_margins(self, pad_mm: float = 1.0, iterations: int = 5) -> tuple:
        """Shrink/grow margins so all axes furniture fits with ``pad_mm`` to spare.

        The canvas size stays exact. Intended for single-axes figures (sim-plot); multi-panel
        figures keep their designed margins so panels stay aligned.
        """
        fig = self.fig
        for _ in range(iterations):
            fig.canvas.draw()
            r = fig.canvas.get_renderer()
            k = fig.dpi * MM        # px per mm
            boxes = []
            for ax in self.axes:
                bb = ax.get_tightbbox(r)
                leg = ax.get_legend()
                if leg is not None and leg.get_visible():
                    bb = mpl.transforms.Bbox.union([bb, leg.get_window_extent(r)])
                boxes.append(bb)
            pos = [ax.get_window_extent(r) for ax in self.axes]
            x0 = min(b.x0 for b in boxes if b is not None)
            y0 = min(b.y0 for b in boxes if b is not None)
            x1 = max(b.x1 for b in boxes if b is not None)
            y1 = max(b.y1 for b in boxes if b is not None)
            ax_x0 = min(p.x0 for p in pos)
            ax_y0 = min(p.y0 for p in pos)
            ax_x1 = max(p.x1 for p in pos)
            ax_y1 = max(p.y1 for p in pos)
            l = (ax_x0 - x0) / k + pad_mm
            b_ = (ax_y0 - y0) / k + pad_mm
            r_ = (x1 - ax_x1) / k + pad_mm
            t_ = (y1 - ax_y1) / k + pad_mm
            self.margins = (l, b_, r_, t_)
            self.gs.update(left=l / self.W, right=1 - r_ / self.W, bottom=b_ / self.H, top=1 - t_ / self.H)
            for ax in self.axes:                  # GridSpec.update no longer moves existing axes
                ss = ax.get_subplotspec()
                if ss is not None:
                    ax.set_position(ss.get_position(fig))
        return self.margins

    def save(self, stem, formats=("pdf", "png"), dpi=None):
        return save(self.fig, stem, formats, dpi)


def make_canvas(width="double", height=None, *, cell_aspect=None, nrows=1, ncols=1,
                margins=None, hgap=None, wgap=None, width_ratios=None,
                height_ratios=None, pyplot: bool = False, autofit: bool = False) -> Canvas:
    """Create a figure at its final size with an explicit mm layout.

    width       'single' | 'one_half' | 'double' | 'slide' | 'poster' | mm
    height      mm; or None when `cell_aspect` is given
    cell_aspect height/width of the (first) axes cell. The canvas height is then derived,
                so equal-aspect field plots fill their cell exactly (no white bands).
    margins     (left, bottom, right, top) in mm; defaults scale with the medium
    pyplot      False (default): a detached Figure, nothing accumulates in pyplot's registry
    autofit     export_figure() fits the margins to the actual furniture (single-axes figures)
    """
    W = S.width_mm(width)
    k = S.get("base", 7.0) / 7.0
    l, b, r, t = margins or (11.5 * k, 9.0 * k, 3.0 * k, 6.0 * k)
    hgap = (11.0 * k) if hgap is None else hgap
    wgap = (12.0 * k) if wgap is None else wgap
    wr = np.asarray(width_ratios if width_ratios is not None else [1] * ncols, float)
    hr = np.asarray(height_ratios if height_ratios is not None else [1] * nrows, float)
    avail_w = W - l - r - (ncols - 1) * wgap
    if height is None:
        if cell_aspect is None:
            raise ValueError("give height (mm) or cell_aspect")
        w0 = avail_w * wr[0] / wr.sum()
        h0 = w0 * cell_aspect
        avail_h = h0 * hr.sum() / hr[0]
        H = t + b + avail_h + (nrows - 1) * hgap
    else:
        H = float(height)
        avail_h = H - t - b - (nrows - 1) * hgap
    if not np.isfinite([W, H]).all() or min(W, H) <= 0 or avail_w <= 0 or avail_h <= 0:
        raise ValueError("margins/gaps leave no room for the axes")
    if pyplot:
        import matplotlib.pyplot as plt
        fig = plt.figure(figsize=(mm(W), mm(H)))
    else:
        fig = Figure(figsize=(mm(W), mm(H)))
        FigureCanvasAgg(fig)
    gs = mpl.gridspec.GridSpec(
        nrows, ncols, figure=fig,
        left=l / W, right=1 - r / W, bottom=b / H, top=1 - t / H,
        wspace=wgap / (avail_w / ncols), hspace=hgap / (avail_h / nrows),
        width_ratios=wr, height_ratios=hr)
    canvas = Canvas(fig, gs, W, H, (l, b, r, t), hgap, wgap, autofit=autofit)
    fig._scivis_canvas = canvas
    return canvas


def fit_width(width, aspect, margins, max_panel_h_mm=None):
    """Canvas width (mm) for a panel of height/width ``aspect``: tall panels become NARROW figures
    instead of a full-column-wide, very tall one, so type, colour bar and panel keep the proportions
    of a normal figure. Returns ``width`` unchanged when the panel is not tall."""
    W = S.width_mm(width)
    l, b, r, t = margins
    medium = S.get("medium", "paper")
    hmax = max_panel_h_mm or {"paper": 80.0, "slide": 110.0, "poster": 200.0}.get(medium, 80.0)
    pw = W - l - r
    if pw * aspect <= hmax:
        return W
    return float(hmax / aspect + l + r)


# --------------------------------------------------------------------------
# Axes dressing for fields and curves
# --------------------------------------------------------------------------
def field_axes(ax, xlim, ylim, xlabel=None, ylabel=None, *, xticks=None, yticks=None,
               outer_x=True, outer_y=True, frame=True):
    """Axes for a 2-D field (contour, streamlines, snapshot): equal aspect, thin frame."""
    m = S.get("spine", 0.6)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)
    ax.set_aspect("equal", adjustable="box")
    for sp in ax.spines.values():
        sp.set_visible(frame)
        sp.set_linewidth(m * 0.8)
    ax.minorticks_off()
    if xticks is not None:
        ax.set_xticks(xticks)
    if yticks is not None:
        ax.set_yticks(yticks)
    ax.tick_params(length=S.get("tick_major", 2.6) * 0.8, width=m * 0.8)
    if xlabel and outer_x:
        ax.set_xlabel(xlabel)
    if ylabel and outer_y:
        ax.set_ylabel(ylabel)
    if not outer_x:
        ax.tick_params(labelbottom=False)
    if not outer_y:
        ax.tick_params(labelleft=False)
    return ax


def range_frame(ax, offset_pt=2.5, x=True, y=True, minor=False):
    """Trim left/bottom spines to the first/last tick (open-axes style only).

    Incompatible with the boxed default; kept for ``apply_style(boxed=False)``.
    """
    if S.get("boxed", True):
        raise ValueError("range_frame needs open axes: apply_style(boxed=False)")
    if not minor:
        ax.minorticks_off()
    ax.figure.canvas.draw()
    if y:
        t = [v for v in ax.get_yticks() if ax.get_ylim()[0] - 1e-12 <= v <= ax.get_ylim()[1] + 1e-12]
        if len(t) >= 2:
            ax.spines["left"].set_bounds(min(t), max(t))
        ax.spines["left"].set_position(("outward", offset_pt))
    if x:
        t = [v for v in ax.get_xticks() if ax.get_xlim()[0] - 1e-12 <= v <= ax.get_xlim()[1] + 1e-12]
        if len(t) >= 2:
            ax.spines["bottom"].set_bounds(min(t), max(t))
        ax.spines["bottom"].set_position(("outward", offset_pt))
    return ax


def light_grid(ax, axis="y"):
    ax.grid(True, axis=axis, color=P.GREY_PALE, linewidth=S.get("spine", 0.6) * 0.6)
    ax.set_axisbelow(True)
    return ax


def halo(text, lw=2.0, color="white"):
    """Thin outline for text drawn over images/fields (typography chapter: legibility)."""
    text.set_path_effects([pe.withStroke(linewidth=lw, foreground=color)])
    return text


def halo_clabel(ax, contour_set, fmt="%g", *, inline=True, spacing=6, fontsize=None, color=None, lw=2.0):
    """Contour labels with a halo: readable on top of any field colour (clabel + outline)."""
    texts = ax.clabel(contour_set, fmt=fmt, inline=inline, inline_spacing=spacing,
                      fontsize=fontsize or S.get("annot", 6.0), colors=color or P.INK)
    for t in texts:
        halo(t, lw=lw)
    return texts


def area_sizes(values, ref_value, ref_area_pt2=20.0):
    """Marker sizes for scatter(s=...) with AREA proportional to the value (rule 7)."""
    if not ref_value > 0:
        raise ValueError("ref_value must be > 0")
    v = np.asarray(values, float)
    if np.any(v < 0):
        raise ValueError("area encoding needs non-negative values")
    return ref_area_pt2 * v / ref_value


# --------------------------------------------------------------------------
# Colour bar
# --------------------------------------------------------------------------
def add_colorbar(ax, mappable, label, *, loc="right", size_mm=None, pad_mm=1.6,
                 length=None, ticks=None, extend="neither", fmt=None, label_mode="auto"):
    """Thin colour bar placed OUTSIDE the axes cell so panel size is untouched.

    loc='right'  : vertical bar, label horizontal above it (no rotated text)
    loc='bottom' : horizontal bar under the axes, label centred below
    A label (with units) is mandatory; pass label="" only for qualitative legends.
    """
    fig = ax.figure
    W, H = fig.get_size_inches() / MM
    pos = ax.get_position()
    aw, ah = pos.width * W, pos.height * H
    if size_mm is None:        # thickness follows the panel (2.4-4 mm) so tall panels do not get a hairline bar
        size_mm = float(np.clip(0.05 * ah, 2.4, 4.0)) if loc == "right" else 2.4
    if length is None:         # never thinner than 1:18; very tall panels get a shorter, centred bar
        length = min(1.0, 18.0 * size_mm / ah) if loc == "right" else 1.0
    off = (1 - length) / 2
    if loc == "right":
        bounds = [1 + pad_mm / aw, off, size_mm / aw, length]
        orient = "vertical"
    elif loc == "bottom":
        bounds = [off, -(pad_mm + size_mm) / ah, length, size_mm / ah]
        orient = "horizontal"
    else:
        raise ValueError("loc must be 'right' or 'bottom'")
    cax = ax.inset_axes(bounds)
    cb = fig.colorbar(mappable, cax=cax, orientation=orient, extend=extend, ticks=ticks, format=fmt)
    cb.outline.set_linewidth(S.get("spine", 0.6) * 0.7)
    cax.tick_params(length=S.get("tick_major", 2.6) * 0.7, width=S.get("spine", 0.6) * 0.7,
                    labelsize=S.get("tick", 6.5), direction="out")
    if loc == "right":
        cax.tick_params(left=False, right=True, labelleft=False, labelright=True, top=False, bottom=False)
    else:
        cax.tick_params(top=False, bottom=True, left=False, right=False)
    cax.minorticks_off()
    if getattr(cb, "solids", None) is not None:
        cb.solids.set_rasterized(True)
        cb.solids.set_edgecolor("face")
    if loc == "right":
        up = 2.0 + (4.0 if extend in ("max", "both") else 0.0)   # clear the extend arrow
        avail_mm = W - (pos.x1 * W + pad_mm) - 0.5
        wide = _text_width_mm(label, S.get("base", 7.0)) > avail_mm
        if label_mode == "side" or (label_mode == "auto" and wide):
            # long label: rotated beside the tick labels (never clipped, never over the arrow)
            cax.yaxis.set_label_position("right")
            cax.set_ylabel(label, rotation=90, labelpad=1.5, fontsize=S.get("base", 7.0))
        else:
            cax.annotate(label, xy=(0, 1), xycoords="axes fraction", xytext=(0, up),
                         textcoords="offset points", ha="left", va="bottom",
                         fontsize=S.get("base", 7.0), annotation_clip=False)
    else:
        cax.set_xlabel(label, labelpad=1.5)
    cax._scivis_cbar_label = label
    return cb


def _text_width_mm(text, size_pt) -> float:
    """Rendered width of a (math) string in mm, measured on a scratch figure."""
    f = Figure(figsize=(2, 1))
    FigureCanvasAgg(f)
    t = f.text(0, 0, text, fontsize=size_pt)
    w = t.get_window_extent(f.canvas.get_renderer()).width / f.dpi / MM
    return float(w)


# --------------------------------------------------------------------------
# Panel labels + titles (fixed hierarchy, aligned across panels)
# --------------------------------------------------------------------------
def panel_labels(fig, axes, labels=None, *, titles=None, fmt="{}", gap_mm=1.2):
    """Bold panel letters on a common left edge per column, left-aligned titles."""
    labels = labels or "abcdefghijklmnopqrstuvwxyz"
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    info = []
    for ax in axes:
        axbb = ax.get_window_extent(r)
        ybb = ax.yaxis.get_tightbbox(r)
        x0 = axbb.x0 if ybb is None else min(axbb.x0, ybb.x0)
        info.append((ax, axbb, x0))
    tol = 3 * MM * fig.dpi
    groups = []
    for it in sorted(info, key=lambda v: v[1].x0):
        for g in groups:
            if abs(g[0][1].x0 - it[1].x0) < tol:
                g.append(it)
                break
        else:
            groups.append([it])
    col_x0 = {}
    for g in groups:
        gx = min(v[2] for v in g)
        for v in g:
            col_x0[id(v[0])] = gx
    size_p = S.get("panel", 9.0)
    pad = mpl.rcParams["axes.titlepad"]
    out = []
    for n, (ax, axbb, x0) in enumerate(info):
        label = fmt.format(labels[n])
        dx_pt = (col_x0[id(ax)] - axbb.x0) * 72.0 / fig.dpi
        t = ax.annotate(label, xy=(0, 1), xycoords="axes fraction", xytext=(dx_pt, pad),
                        textcoords="offset points", ha="left", va="baseline", fontsize=size_p,
                        fontweight="bold", annotation_clip=False)
        ttl = None if titles is None else titles[n]
        if ttl:
            indent = 0.0
            if abs(dx_pt) < 2 * gap_mm:
                wlab = t.get_window_extent(r).width
                indent = (wlab + gap_mm * MM * fig.dpi) / axbb.width
            ax.set_title(ttl, loc="left", pad=pad, x=indent, fontsize=S.get("title", 7.0), fontweight="normal")
        out.append(t)
    return out


def end_labels(ax, items, *, pad_pt=3.0, fontsize=None, min_sep=1.15, ha="left"):
    """OPT-IN direct labels at curve ends (the default is a framed legend).

    items : list of (x, y, text, color) in data coordinates; de-overlapped vertically.
    """
    fs = fontsize or S.get("legend", 6.5)
    fig = ax.figure
    fig.canvas.draw()
    pts = np.array([ax.transData.transform((x, y)) for x, y, *_ in items])
    order = np.argsort(pts[:, 1])
    ys = pts[order, 1].astype(float)
    sep = fs * min_sep * fig.dpi / 72.0
    for i in range(1, len(ys)):
        if ys[i] - ys[i - 1] < sep:
            ys[i] = ys[i - 1] + sep
    ys += (pts[order, 1].mean() - ys.mean())
    outs = []
    for k, idx in enumerate(order):
        x, y, text, color = items[idx]
        dy_pt = (ys[k] - pts[idx, 1]) * 72.0 / fig.dpi
        outs.append(ax.annotate(text, xy=(x, y), xytext=(pad_pt, dy_pt), textcoords="offset points",
                                ha=ha, va="center", color=color, fontsize=fs, annotation_clip=False))
    return outs


# --------------------------------------------------------------------------
# Standard layouts from the book
# --------------------------------------------------------------------------
def marginal_canvas(width="single", height=None, *, ratio=5, gap_mm=1.6,
                    margins=(12.0, 10.0, 4.0, 5.0)):
    """Main axes + top/right marginals aligned on a ratio GridSpec (book: standard-layout-2).

    Returns ``(canvas, main, top, right, corner)``. Marginals share the main axes' limits and
    carry no ticks; the empty corner cell is free for a colourbar or an annotation.
    """
    c = make_canvas(width, height if height is not None else S.width_mm(width), nrows=2, ncols=2,
                    margins=margins, hgap=gap_mm, wgap=gap_mm,
                    width_ratios=[ratio, 1], height_ratios=[1, ratio])
    main = c.ax(1, 0)
    top = c.ax(0, 0, sharex=main, style=False)
    right = c.ax(1, 1, sharey=main, style=False)
    corner = c.ax(0, 1, style=False)
    for a_ in (top, right):
        a_.tick_params(bottom=False, top=False, left=False, right=False, labelbottom=False, labelleft=False)
        a_.minorticks_off()
    top.set_yticks([])
    right.set_xticks([])
    corner.set_xticks([])
    corner.set_yticks([])
    for sp in corner.spines.values():
        sp.set_visible(False)
    corner.patch.set_visible(False)
    return c, main, top, right, corner


def density_scatter(ax, x, y, *, lim=None, bins=90, smooth=3, size_pt2=3.0, cmap=None,
                    rasterized=True):
    """Scatter coloured by local density (2-D histogram lookup), densest points on top.

    Right tool for >~10^4 points where alpha stacking fails. Returns (PathCollection, density).
    """
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = np.isfinite(x) & np.isfinite(y)
    if not ok.all():
        raise ValueError("density_scatter received non-finite points; mask them explicitly.")
    rng = lim if lim is not None else [[x.min(), x.max()], [y.min(), y.max()]]
    if lim is not None and np.ndim(lim) == 1:
        rng = [list(lim), list(lim)]
    H, xe, ye = np.histogram2d(x, y, bins=bins, range=rng)
    k1 = np.array([1.0, 2.0, 1.0]) / 4
    for _ in range(smooth):
        H = np.apply_along_axis(lambda v: np.convolve(v, k1, "same"), 0, H)
        H = np.apply_along_axis(lambda v: np.convolve(v, k1, "same"), 1, H)
    ix = np.clip(np.digitize(x, xe) - 1, 0, bins - 1)
    iy = np.clip(np.digitize(y, ye) - 1, 0, bins - 1)
    dens = H[ix, iy]
    o = np.argsort(dens)
    cm = cmap or P.get_cmap("density")
    sc = ax.scatter(x[o], y[o], c=dens[o], s=size_pt2, cmap=cm, linewidths=0, rasterized=rasterized)
    return sc, dens


def zoom_inset(ax, xlim, ylim, plot_fn: Callable, *, width_mm=28.0, anchor="upper right",
               offset_mm=(1.5, 1.5), connect=True, edge=P.INK, lw=None, equal_aspect=True):
    """Magnified inset of a sub-region with dashed box + connectors (book: annotation-zoom).

    ``plot_fn(inset_ax)`` redraws the *same* artists (same cmap/norm) in the inset: the zoom
    must not introduce a second colour mapping. Size is in mm, aspect follows the data window.
    """
    fig = ax.figure
    W, H = fig.get_size_inches() / MM
    pos = ax.get_position()
    aw, ah = pos.width * W, pos.height * H
    dx, dy = xlim[1] - xlim[0], ylim[1] - ylim[0]
    if dx <= 0 or dy <= 0:
        raise ValueError("zoom window needs xlim[0] < xlim[1] and ylim[0] < ylim[1]")
    h_mm = width_mm * dy / dx if equal_aspect else width_mm * 0.75
    ox, oy = offset_mm
    fx, fy = width_mm / aw, h_mm / ah
    x0 = {"left": ox / aw, "right": 1 - fx - ox / aw}[anchor.split()[1]]
    y0 = {"lower": oy / ah, "upper": 1 - fy - oy / ah}[anchor.split()[0]]
    ins = ax.inset_axes([x0, y0, fx, fy])
    plot_fn(ins)
    ins.set_xlim(xlim)
    ins.set_ylim(ylim)
    if equal_aspect:
        ins.set_aspect("equal", adjustable="box")
    ins.set_xticks([])
    ins.set_yticks([])
    lw = lw or S.get("spine", 0.6) * 0.9
    for sp in ins.spines.values():
        sp.set_linewidth(lw)
        sp.set_edgecolor(edge)
    if connect:
        ax.indicate_inset_zoom(ins, edgecolor=edge, linewidth=lw, alpha=1.0, linestyle="--")
    ins._scivis_zoom = True
    return ins


def small_multiples(series: dict, *, ncols=3, width="double", cell_aspect=0.75, xlabel="", ylabel="",
                    colors=None, accent=None, ghost_color=P.GREY_PALE, ghost_lw=None, lw=None,
                    xlim=None, ylim=None, xscale="linear", yscale="linear",
                    margins=None, titles=True, share_labels=True):
    """One panel per case, every other case as a pale ghost behind it (Rougier rule 8).

    series : {name: (x, y)} or {name: dict(x=..., y=...)}; panels follow dict order.
    colors : None -> one accent colour for all (colour only where it carries meaning); a list
             or dict of colours per case (e.g. ordered_colors for a Re sweep) otherwise.
    Axes limits are shared and computed from ALL data, so panels are comparable.
    Returns ``(canvas, axes)``. Replaces the 6-category cap for parameter sweeps.
    """
    names = list(series)
    n = len(names)
    if n < 2:
        raise ValueError("small_multiples needs at least two cases")
    data = {}
    for k, v in series.items():
        x, y = (v["x"], v["y"]) if isinstance(v, dict) else v
        x, y = np.asarray(x, float), np.asarray(y, float)
        if x.shape != y.shape or x.ndim != 1:
            raise ValueError(f"case {k!r}: x and y must be 1-D arrays of equal length")
        data[k] = (x, y)
    nrows = int(np.ceil(n / ncols))
    k_ = S.get("base", 7.0) / 7.0
    m = margins or (11.0 * k_, 9.0 * k_, 2.5 * k_, 6.0 * k_)
    c = make_canvas(width, cell_aspect=cell_aspect, nrows=nrows, ncols=ncols, margins=m,
                    hgap=10.0 * k_, wgap=7.0 * k_)
    allx = np.concatenate([d[0][np.isfinite(d[0])] for d in data.values()])
    ally = np.concatenate([d[1][np.isfinite(d[1])] for d in data.values()])
    xl = xlim or (allx.min(), allx.max())
    yl = ylim or ((ally.min(), ally.max()) if yscale == "linear" else (ally[ally > 0].min(), ally.max()))
    if yscale == "linear" and ylim is None:
        pad = 0.04 * (yl[1] - yl[0])
        yl = (yl[0] - pad, yl[1] + pad)
    accent = accent or P.TOL["bright"][0]
    if colors is None:
        col = {k: accent for k in names}
    elif isinstance(colors, dict):
        col = colors
    else:
        col = dict(zip(names, colors))
    gl = ghost_lw or S.get("line", 1.1) * 0.6
    lw = lw or S.get("line", 1.1)
    axes = []
    for i, name in enumerate(names):
        r_, c_ = divmod(i, ncols)
        ax = c.ax(r_, c_)
        for other in names:
            if other != name:
                ax.plot(*data[other], color=ghost_color, lw=gl, zorder=1, solid_capstyle="butt")
        ax.plot(*data[name], color=col[name], lw=lw, zorder=3)
        ax.set_xscale(xscale)
        ax.set_yscale(yscale)
        ax.set_xlim(xl)
        ax.set_ylim(yl)
        last_row = (r_ == nrows - 1) or (i + ncols >= n)
        if share_labels:
            ax.tick_params(labelleft=(c_ == 0), labelbottom=last_row)
            if last_row:
                ax.set_xlabel(xlabel)
            if c_ == 0:
                ax.set_ylabel(ylabel)
        else:
            ax.set_xlabel(xlabel)
            ax.set_ylabel(ylabel)
        axes.append(ax)
    panel_labels(c.fig, axes, titles=[str(k) for k in names] if titles else None)
    return c, axes


# --------------------------------------------------------------------------
# Output + self-check
# --------------------------------------------------------------------------
def save(fig, stem, formats=("pdf", "png"), dpi=None, *, close=True):
    """Save at the exact canvas size (no bbox_inches='tight'). Warns on very large vector files."""
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    paths = []
    warn_mb = (S.get("theme") or {}).get("export", {}).get("pdf_size_warn_mb", 8.0)
    for f in formats:
        p = stem.with_suffix("." + f)
        kw = {"dpi": dpi or mpl.rcParams["savefig.dpi"]} if f in ("png", "tif", "tiff", "jpg") else {}
        fig.savefig(p, bbox_inches=None, **kw)
        paths.append(p)
        if f in ("pdf", "svg") and p.stat().st_size > warn_mb * 1e6:
            import warnings
            warnings.warn(f"{p.name} is {p.stat().st_size/1e6:.1f} MB: rasterize dense layers "
                          "(rasterized=True) or reduce points; text/axes stay vector.")
    if close and fig in _pyplot_figs():
        import matplotlib.pyplot as plt
        plt.close(fig)
    return paths


def _pyplot_figs():
    try:
        import matplotlib.pyplot as plt
        return [plt.figure(n) for n in plt.get_fignums()]
    except Exception:       # pragma: no cover
        return []


def _all_axes(fig):
    """fig.axes plus inset/child axes (colour bars and zoom insets live there)."""
    out, stack = [], list(fig.axes)
    while stack:
        a = stack.pop(0)
        out.append(a)
        stack.extend(getattr(a, "child_axes", []))
    return out


def _has_cjk(s: str) -> bool:
    return any("　" <= ch <= "鿿" or "＀" <= ch <= "￯" for ch in s)


def qa(fig, min_font_pt=None, verbose=True, expect_width_mm=None):
    """Automated figure checks. Returns a list of (code, detail); empty means clean.

    clipped    text extends beyond the canvas
    overlap    two visible text objects overlap
    tiny       font below the legible minimum for the medium
    cbar       colour bar without a label
    font       primary font is not the requested one nor a metric-compatible substitute
    cjk-math   CJK characters inside a mathtext string (renders missing-glyph boxes)
    legend     legend box covers plotted data points
    size       canvas width differs from expect_width_mm
    """
    min_font_pt = min_font_pt or S.get("min_font", 5.0)
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    Wp, Hp = fig.bbox.width, fig.bbox.height
    issues = []
    skip = set()
    for ax in _all_axes(fig):
        for axis in (ax.xaxis, ax.yaxis):
            allt = axis.get_majorticklabels() + axis.get_minorticklabels()
            try:
                drawn = {id(x) for tk in axis._update_ticks() for x in (tk.label1, tk.label2)}
            except Exception:
                drawn = {id(x) for x in allt}
            skip |= {id(x) for x in allt} - drawn
            # tick labels whose location lies outside the view interval are never visible
            lo, hi = sorted(axis.get_view_interval())
            eps = 1e-9 * max(1.0, abs(hi - lo))
            for loc, lab in zip(axis.get_majorticklocs(), axis.get_majorticklabels()):
                if loc < lo - eps or loc > hi + eps:
                    skip.add(id(lab))
    texts = []
    for t in fig.findobj(mpl.text.Text):
        if id(t) in skip:
            continue
        if t.get_visible() and t.get_text().strip():
            try:
                bb = t.get_window_extent(r)
            except Exception:
                continue
            if bb.width > 0 and bb.height > 0:
                texts.append((t, bb))
    for t, bb in texts:
        s = t.get_text()
        if bb.x0 < -1 or bb.y0 < -1 or bb.x1 > Wp + 1 or bb.y1 > Hp + 1:
            issues.append(("clipped", s[:40]))
        if t.get_fontsize() < min_font_pt - 1e-6:
            issues.append(("tiny", f"{s[:30]!r} {t.get_fontsize():.1f}pt"))
        if "$" in s and _has_cjk(s):
            issues.append(("cjk-math", f"{s[:30]!r}: split Chinese text and $math$ into separate strings"))
    shrink = 0.08
    for (a, ba), (b, bb) in itertools.combinations(texts, 2):
        ax_, ay, bx, by = (ba.x0 + shrink * ba.width, ba.y0 + shrink * ba.height,
                           ba.x1 - shrink * ba.width, ba.y1 - shrink * ba.height)
        cx, cy, dx, dy = (bb.x0 + shrink * bb.width, bb.y0 + shrink * bb.height,
                          bb.x1 - shrink * bb.width, bb.y1 - shrink * bb.height)
        if ax_ < dx and cx < bx and ay < dy and cy < by:
            issues.append(("overlap", f"{a.get_text()[:25]!r} x {b.get_text()[:25]!r}"))
    for ax in _all_axes(fig):
        if hasattr(ax, "_scivis_cbar_label") and not ax._scivis_cbar_label.strip():
            issues.append(("cbar", "colour bar has no label/units"))
        leg = ax.get_legend()
        if leg is not None and leg.get_visible():
            lb = leg.get_window_extent(r)
            if lb.x0 < -1 or lb.y0 < -1 or lb.x1 > Wp + 1 or lb.y1 > Hp + 1:
                issues.append(("clipped", "legend frame extends beyond the canvas"))
            hit = 0
            for ln in ax.get_lines():
                xy = np.asarray(ln.get_xydata(), float)
                if not ln.get_visible() or xy.ndim != 2 or not len(xy):
                    continue
                ok = np.isfinite(xy).all(axis=1)
                if not ok.any():
                    continue
                px = ax.transData.transform(xy[ok])
                mid = (px[1:] + px[:-1]) / 2 if len(px) > 1 else px[:0]
                pts = np.vstack([px, mid]) if len(mid) else px
                hit += int(((pts[:, 0] > lb.x0) & (pts[:, 0] < lb.x1) &
                            (pts[:, 1] > lb.y0) & (pts[:, 1] < lb.y1)).sum())
            for coll in ax.collections:
                try:
                    off = np.asarray(coll.get_offsets(), float)
                    if off.ndim == 2 and len(off):
                        px = ax.transData.transform(off[np.isfinite(off).all(axis=1)])
                        hit += int(((px[:, 0] > lb.x0) & (px[:, 0] < lb.x1) &
                                    (px[:, 1] > lb.y0) & (px[:, 1] < lb.y1)).sum())
                except Exception:
                    pass
            if hit:
                issues.append(("legend", f"legend covers {hit} plotted points/segments; move it or add headroom"))
    st = S.STATE
    note = ""
    if st and st.get("primary") and st["primary"] != st.get("requested"):
        if st.get("font_ok"):
            note = (f", NOTE: '{st['requested']}' not installed here, rendered with the "
                    f"metric-compatible '{st['primary']}'")
        else:
            issues.append(("font", f"requested {st['requested']}, using {st['primary']}"))
    w, h = fig.get_size_inches() / MM
    if expect_width_mm is not None and abs(w - expect_width_mm) > 0.5:
        issues.append(("size", f"canvas is {w:.1f} mm wide, expected {expect_width_mm:.1f} mm"))
    if verbose:
        print(f"[qa] canvas {w:.0f} x {h:.0f} mm, font={st.get('primary')}, "
              f"{len(texts)} text objects, issues={len(issues)}{note}")
        for c, d in issues:
            print(f"     - {c}: {d}")
    return issues
