"""restyle: change how an existing figure LOOKS without touching what it SHOWS.

Use when the user already has a figure (and the code that made it) and asks to
"enhance / beautify / restyle / make it publication-ready".  The data layer is FROZEN:
arrays, coordinates, colour map, norm (vmin/vmax/centre), extend, interpolation, axis
limits/scales, label and annotation text, contour geometry.  Only the presentation layer
is replaced: canvas size, fonts, frame, ticks, colour-bar geometry, line widths, halos.

Workflow
    with intercept_savefig() as got:          # runs the ORIGINAL code, never writes its files
        runpy.run_path(script, run_name="__main__")
    old = got.figs[-1]
    spec = harvest(old)                       # every artist -> plain data (raises on unknown artists)
    canvas = make_canvas(..., cell_aspect=panel_aspect(spec[0]))
    replay(spec[0], canvas.ax(field=True), cbar_label=...)
    changes = compare(harvest(old), harvest(canvas.fig))   # [] means the frozen layer is identical

When the original code cannot be run or is not matplotlib, paste its data-preparation
code verbatim into the template's FROZEN block instead (templates/restyle_field_template.py).
"""
from __future__ import annotations

import contextlib
import copy
import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import matplotlib as mpl
import numpy as np
import matplotlib.patheffects as pe
from matplotlib import contour as _mcontour
from matplotlib import collections as _mcoll
from matplotlib.figure import Figure

from . import layout
from .theme import STATE as S, get as _g

FROZEN = (
    "array values, masks and coordinates", "colour map (unless the user opts in)",
    "norm: vmin / vmax / centre / extend", "interpolation and smoothing",
    "axis limits and scales", "axis, colour-bar and annotation text", "contour geometry",
    "units (no Angstrom -> nm conversion unless asked)",
)
PRESENTATION = (
    "canvas size and margins", "fonts and sizes", "frame, tick style and tick count",
    "colour-bar geometry", "line widths and halos", "panel labels", "export formats / dpi",
)


SIGNED_IF_DIVERGING = "signed-if-diverging"


def is_diverging(cmap) -> bool:
    """Lightness profile test: pale centre, two darker ends of similar lightness (RdBu_r, coolwarm, bwr, ...)."""
    from .palettes import rgb_to_lab
    if str(getattr(cmap, "name", "")).split("_")[0] in {"jet", "rainbow", "turbo", "hsv", "nipy", "gist"}:
        return False          # rainbow maps are not diverging; never swap them silently
    L = rgb_to_lab(np.asarray(cmap(np.array([0.0, 0.5, 1.0])))[:, :3])[:, 0]
    return bool(L[1] > max(L[0], L[2]) + 25 and abs(L[0] - L[2]) < 30)


class UnsupportedArtist(RuntimeError):
    """The original figure contains an artist that cannot be rebuilt losslessly."""


# --------------------------------------------------------------------------
# Running the original code safely
# --------------------------------------------------------------------------
class _Got:
    def __init__(self):
        self.figs: list[Figure] = []
        self.blocked: list[str] = []


@contextlib.contextmanager
def intercept_savefig():
    """Capture every figure the original code saves, without writing the file or closing it.

    The original code may still write other files (CSV, manifests). Run it on a copy of the
    project, or call its plotting function directly, when that matters.
    """
    got = _Got()
    orig_savefig = Figure.savefig

    def fake(self, fname, *a, **k):
        if not any(self is f for f in got.figs):
            got.figs.append(self)
        got.blocked.append(str(fname))

    import matplotlib.pyplot as plt
    orig_close, orig_show = plt.close, plt.show
    Figure.savefig = fake
    plt.close = lambda *a, **k: None
    plt.show = lambda *a, **k: None
    try:
        yield got
    finally:
        Figure.savefig = orig_savefig
        plt.close, plt.show = orig_close, orig_show


# --------------------------------------------------------------------------
# Spec
# --------------------------------------------------------------------------
@dataclass
class Layer:
    kind: str                       # mesh | image | contour | linecoll | line | scatter | text
    d: dict = field(default_factory=dict)


@dataclass
class PanelSpec:
    layers: list
    xlim: tuple
    ylim: tuple
    xscale: str = "linear"
    yscale: str = "linear"
    xlabel: str = ""
    ylabel: str = ""
    title: str = ""
    aspect: Any = "auto"
    box_aspect: float = 1.0         # height/width of the original axes box
    colorbar: dict | None = None
    unsupported: list = field(default_factory=list)


def _masked(a):
    a = np.ma.asarray(a)
    return np.ma.array(np.array(a.data, dtype=float, copy=True) if a.dtype.kind in "fiu" else a.data,
                       mask=np.ma.getmaskarray(a).copy())


def _cbar_info(m):
    cb = getattr(m, "colorbar", None)
    if cb is None:
        return None
    ax = cb.ax
    label = ax.get_ylabel() or ax.get_xlabel()
    if not label:   # scivis puts the label in an annotation
        label = getattr(ax, "_scivis_cbar_label", "") or ""
    return {"label": label, "extend": cb.extend, "orientation": cb.orientation,
            "ticks": [float(t) for t in np.asarray(cb.get_ticks(), float)], "ax": ax}


def harvest(fig: Figure) -> list[PanelSpec]:
    """Turn a drawn figure into plain data. Unknown artists are listed, never silently dropped."""
    fig.canvas.draw()
    cbar_axes = set()
    for ax in fig.axes:
        for m in list(ax.images) + list(ax.collections):
            cb = getattr(m, "colorbar", None)
            if cb is not None:
                cbar_axes.add(id(cb.ax))
    out = []
    for ax in fig.axes:
        if id(ax) in cbar_axes:
            continue
        spec = PanelSpec(layers=[], xlim=tuple(map(float, ax.get_xlim())), ylim=tuple(map(float, ax.get_ylim())),
                         xscale=ax.get_xscale(), yscale=ax.get_yscale(), xlabel=ax.get_xlabel(),
                         ylabel=ax.get_ylabel(), title=ax.get_title(), aspect=ax.get_aspect())
        pos = ax.get_position()
        W, H = fig.get_size_inches()
        spec.box_aspect = float((pos.height * H) / (pos.width * W))
        for im in ax.images:
            im.norm.autoscale_None(im.get_array())
            spec.layers.append(Layer("image", dict(
                arr=_masked(im.get_array()), extent=tuple(map(float, im.get_extent())), origin=im.origin,
                interpolation=im.get_interpolation(), stage=getattr(im, "get_interpolation_stage", lambda: "auto")(),
                norm=copy.deepcopy(im.norm), cmap=copy.copy(im.get_cmap()), alpha=im.get_alpha(), mappable=im)))
            spec.colorbar = spec.colorbar or _cbar_info(im)
        for c in ax.collections:
            if isinstance(c, _mcontour.ContourSet):
                if c.filled:
                    spec.unsupported.append("filled contour (contourf): use the FROZEN-block template")
                    continue
                cols = c.get_edgecolor()
                segs = [[np.array(s, float) for s in lev] for lev in c.allsegs]
                spec.layers.append(Layer("contour", dict(
                    segs=segs, levels=np.array(c.levels, float), colors=np.array(cols, float),
                    lw=[float(w) for w in np.atleast_1d(c.get_linewidths())])))
            elif isinstance(c, mpl.collections.QuadMesh):
                c.norm.autoscale_None(c.get_array())
                coords = np.array(c.get_coordinates(), float)
                arr = _masked(c.get_array())
                if arr.ndim == 1:
                    arr = arr.reshape(coords.shape[0] - 1, coords.shape[1] - 1) if getattr(c, "_shading", "flat") != "gouraud" \
                        else arr.reshape(coords.shape[:2])
                spec.layers.append(Layer("mesh", dict(
                    coords=coords, arr=arr, shading=getattr(c, "_shading", "flat"),
                    norm=copy.deepcopy(c.norm), cmap=copy.copy(c.get_cmap()), alpha=c.get_alpha(), mappable=c)))
                spec.colorbar = spec.colorbar or _cbar_info(c)
            elif isinstance(c, _mcoll.PathCollection):
                arr = c.get_array()
                spec.layers.append(Layer("scatter", dict(
                    offsets=np.array(c.get_offsets(), float), sizes=np.array(c.get_sizes(), float),
                    fc=np.array(c.get_facecolor(), float), ec=np.array(c.get_edgecolor(), float),
                    arr=None if arr is None else _masked(arr),
                    norm=copy.deepcopy(c.norm) if arr is not None else None,
                    cmap=copy.copy(c.get_cmap()) if arr is not None else None, alpha=c.get_alpha(), mappable=c)))
                if arr is not None:
                    spec.colorbar = spec.colorbar or _cbar_info(c)
            elif isinstance(c, _mcoll.LineCollection) and hasattr(c, "_scivis_levels"):
                spec.layers.append(Layer("contour", dict(
                    segs=[[np.array(s_, float) for s_ in c.get_segments()]], levels=np.array(c._scivis_levels, float),
                    colors=np.array(c.get_colors(), float), lw=[float(w) for w in np.atleast_1d(c.get_linewidths())])))
            elif isinstance(c, _mcoll.LineCollection):
                spec.layers.append(Layer("linecoll", dict(
                    segs=[np.array(s, float) for s in c.get_segments()],
                    colors=np.array(c.get_colors(), float), lw=[float(w) for w in np.atleast_1d(c.get_linewidths())])))
            else:
                spec.unsupported.append(type(c).__name__)
        for ln in ax.lines:
            if ln.get_label().startswith("_") and ln.get_xdata().size == 0:
                continue
            spec.layers.append(Layer("line", dict(
                x=np.array(ln.get_xdata(), float), y=np.array(ln.get_ydata(), float), color=ln.get_color(),
                ls=ln.get_linestyle(), lw=float(ln.get_linewidth()), marker=ln.get_marker(),
                ms=float(ln.get_markersize()), label=ln.get_label(), zorder=ln.get_zorder())))
        for t in ax.texts:
            xy = t.xy if hasattr(t, "xy") else t.get_position()
            spec.layers.append(Layer("text", dict(
                s=t.get_text(), xy=tuple(map(float, xy)), ha=t.get_ha(), va=t.get_va(),
                xyc=getattr(t, "xycoords", "data") if hasattr(t, "xy") else "data")))
        if ax.patches:
            spec.unsupported.append("patches: " + ",".join(sorted({type(p).__name__ for p in ax.patches})))
        out.append(spec)
    return out


def panel_aspect(spec: PanelSpec) -> float:
    """Height/width for make_canvas(cell_aspect=...). Equal-aspect panels follow the data window."""
    if spec.aspect == "equal" or (isinstance(spec.aspect, (int, float)) and spec.aspect == 1):
        return abs(spec.ylim[1] - spec.ylim[0]) / abs(spec.xlim[1] - spec.xlim[0])
    return spec.box_aspect


# --------------------------------------------------------------------------
# Replay
# --------------------------------------------------------------------------
def replay(spec: PanelSpec, ax, *, cmap=None, cbar=True, cbar_label=None, cbar_kw=None,
           keep_ticks=False, outline_halo=True, labels: dict | None = None,
           allow_unsupported=False) -> dict:
    """Draw ``spec`` on ``ax`` with the scivis presentation layer and the original data layer.

    cmap       None keeps the ORIGINAL colour map. Pass a name only when the user opted in;
               the result then lists it under ``changes``.
    labels     {"xlabel":..., "ylabel":..., "cbar":...}: explicit overrides (e.g. LaTeX-ify a
               label); text is otherwise copied unchanged.
    """
    if spec.unsupported and not allow_unsupported:
        raise UnsupportedArtist("Cannot rebuild losslessly: " + "; ".join(spec.unsupported)
                                + ". Use the FROZEN-block template, or pass allow_unsupported=True "
                                  "and list the omission in the report.")
    changes = []
    labels = labels or {}
    mappable = None
    lw_line = _g("line", 1.1)
    for L in spec.layers:
        d = L.d
        cm = d.get("cmap")
        target = cmap
        if cmap == SIGNED_IF_DIVERGING:          # standing opt-in: diverging maps become vik, others untouched
            target = "signed" if (cm is not None and is_diverging(cm)) else None
        if cm is not None and target is not None:
            from .palettes import get_cmap
            cm = get_cmap(target)
            changes.append(f"cmap: {d['cmap'].name} -> {cm.name} (user opt-in)")
        if L.kind == "mesh":
            xs, ys = d["coords"][..., 0], d["coords"][..., 1]
            m = ax.pcolormesh(xs, ys, d["arr"], cmap=cm, norm=copy.deepcopy(d["norm"]), shading=d["shading"],
                              alpha=d["alpha"], rasterized=True, linewidth=0, antialiased=False)
            mappable = mappable or m
        elif L.kind == "image":
            m = ax.imshow(d["arr"], extent=d["extent"], origin=d["origin"], interpolation=d["interpolation"],
                          interpolation_stage=d["stage"], cmap=cm, norm=copy.deepcopy(d["norm"]),
                          alpha=d["alpha"], aspect=spec.aspect if spec.aspect in ("equal", "auto") else spec.aspect)
            mappable = mappable or m
        elif L.kind == "contour":
            cols = d["colors"]
            segs, colors = [], []
            for li, lev in enumerate(d["segs"]):
                for s_ in lev:
                    segs.append(s_)
                    colors.append(cols[min(li, len(cols) - 1)] if len(cols) else (0, 0, 0, 1))
            lc = _mcoll.LineCollection(segs, colors=colors, linewidths=lw_line * 0.7, capstyle="round")
            lc._scivis_levels = np.array(d["levels"], float)       # lets harvest() recognise it again
            if outline_halo:
                lc.set_path_effects([pe.Stroke(linewidth=lw_line * 0.7 + 1.6, foreground="white"), pe.Normal()])
            ax.add_collection(lc)
        elif L.kind == "linecoll":
            lc = _mcoll.LineCollection(d["segs"], colors=d["colors"], linewidths=lw_line * 0.7)
            ax.add_collection(lc)
        elif L.kind == "line":
            ax.plot(d["x"], d["y"], color=d["color"], ls=d["ls"], lw=lw_line * (d["lw"] / 1.5 if d["lw"] else 1),
                    marker=d["marker"], ms=_g("marker", 3.2) * 0.6 if d["marker"] not in ("None", None, "") else 0,
                    label=d["label"] if not d["label"].startswith("_") else None, zorder=d["zorder"])
        elif L.kind == "scatter":
            kw = {}
            if d["arr"] is not None:
                kw = dict(c=d["arr"], cmap=cm, norm=copy.deepcopy(d["norm"]))
            else:
                kw = dict(facecolors=d["fc"], edgecolors=d["ec"])
            m = ax.scatter(d["offsets"][:, 0], d["offsets"][:, 1], s=d["sizes"] if len(d["sizes"]) else 8,
                           alpha=d["alpha"], linewidths=0.6, **kw)
            if d["arr"] is not None:
                mappable = mappable or m
        elif L.kind == "text":
            t = ax.annotate(d["s"], xy=d["xy"], xycoords=d["xyc"], ha=d["ha"], va=d["va"],
                            fontsize=_g("annot", 6.0))
            layout.halo(t, lw=2.0)
    ax.set_xscale(spec.xscale)
    ax.set_yscale(spec.yscale)
    ax.set_xlim(spec.xlim)
    ax.set_ylim(spec.ylim)
    if spec.aspect == "equal":
        ax.set_aspect("equal", adjustable="box")
    xl, yl = labels.get("xlabel", spec.xlabel), labels.get("ylabel", spec.ylabel)
    if labels.get("xlabel") is not None or labels.get("ylabel") is not None:
        changes.append("axis label text overridden by request")
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    if spec.title:
        ax.set_title(spec.title)
    spine = _g("spine", 0.6)
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(spine * 0.8)
    ax.tick_params(direction="in", top=True, right=True, length=_g("tick_major", 2.6) * 0.8, width=spine * 0.8,
                   labelsize=_g("tick", 6.5))
    ax.minorticks_off()
    cb = None
    if cbar and mappable is not None and spec.colorbar is not None:
        info = spec.colorbar
        kw = dict(extend=info["extend"], ticks=(info["ticks"] if keep_ticks else None))
        kw.update(cbar_kw or {})
        label = cbar_label if cbar_label is not None else labels.get("cbar", info["label"])
        cb = layout.add_colorbar(ax, mappable, label, **kw)
    return {"mappable": mappable, "colorbar": cb, "changes": changes}


# --------------------------------------------------------------------------
# Frozen-layer audit
# --------------------------------------------------------------------------
def _h(a) -> str:
    a = np.ma.asarray(a)
    filled = np.ma.filled(a.astype(float), np.nan) if a.dtype.kind in "fiu" else np.ma.filled(a)
    return hashlib.sha256(np.ascontiguousarray(filled, dtype=float).tobytes()
                          + np.ma.getmaskarray(a).tobytes()).hexdigest()[:16]


def _norm_key(n):
    return (type(n).__name__, None if n.vmin is None else float(n.vmin), None if n.vmax is None else float(n.vmax),
            getattr(n, "vcenter", None), getattr(n, "linthresh", None))


def _cmap_key(c):
    return hashlib.sha256(np.round(c(np.linspace(0, 1, 256)), 5).tobytes()).hexdigest()[:12]


def fingerprint(specs: list[PanelSpec]) -> list[dict]:
    out = []
    for p in specs:
        fp = {"xlim": p.xlim, "ylim": p.ylim, "xscale": p.xscale, "yscale": p.yscale,
              "xlabel": p.xlabel, "ylabel": p.ylabel, "title": p.title, "layers": []}
        if p.colorbar:
            fp["colorbar"] = {"label": p.colorbar["label"], "extend": p.colorbar["extend"]}
        for L in p.layers:
            d = L.d
            e = {"kind": L.kind}
            if "arr" in d and d["arr"] is not None:
                e["values"] = _h(d["arr"])
            if "coords" in d:
                e["coords"] = _h(d["coords"])
            for k in ("extent", "origin", "interpolation", "shading"):
                if k in d:
                    e[k] = d[k]
            if d.get("norm") is not None:
                e["norm"] = _norm_key(d["norm"])
            if d.get("cmap") is not None:
                e["cmap"] = _cmap_key(d["cmap"])
            if L.kind == "contour":
                e["geometry"] = hashlib.sha256(b"".join(np.ascontiguousarray(s).tobytes()
                                                        for lev in d["segs"] for s in lev)).hexdigest()[:16]
                e["levels"] = tuple(map(float, d["levels"]))
            if L.kind == "linecoll":
                e["geometry"] = hashlib.sha256(b"".join(np.ascontiguousarray(s).tobytes() for s in d["segs"])).hexdigest()[:16]
            if L.kind == "line":
                e["x"], e["y"] = _h(d["x"]), _h(d["y"])
            if L.kind == "scatter":
                e["offsets"] = _h(d["offsets"])
            if L.kind == "text":
                e["s"], e["xy"] = d["s"], d["xy"]
            fp["layers"].append(e)
        out.append(fp)
    return out


def compare(old: list[PanelSpec], new: list[PanelSpec], allow: tuple = ()) -> list[str]:
    """Differences in the FROZEN layer. [] means identical. ``allow`` lists keys the user changed
    on purpose (e.g. 'cmap', 'xlabel')."""
    a, b = fingerprint(old), fingerprint(new)
    diffs = []
    if len(a) != len(b):
        return [f"panel count {len(a)} -> {len(b)}"]
    for i, (pa, pb) in enumerate(zip(a, b)):
        for k in pa:
            if k == "layers" or k in allow:
                continue
            if pa[k] != pb.get(k):
                diffs.append(f"panel {i}: {k}: {pa[k]!r} -> {pb.get(k)!r}")
        # contour/text order can differ; compare as multisets per kind
        key = lambda e: repr(sorted(e.items(), key=lambda kv: kv[0]))
        la = sorted((key({k: v for k, v in e.items() if k not in allow}) for e in pa["layers"]))
        lb = sorted((key({k: v for k, v in e.items() if k not in allow}) for e in pb["layers"]))
        if la != lb:
            for e in pa["layers"]:
                if key({k: v for k, v in e.items() if k not in allow}) not in lb:
                    diffs.append(f"panel {i}: layer {e['kind']} changed or missing: "
                                 + ", ".join(f"{k}={v}" for k, v in e.items() if k != "kind"))
    return diffs


def side_by_side(old_fig: Figure, new_fig: Figure, path, dpi=160, title_old="original", title_new="restyled"):
    """Review image only (not a publication figure)."""
    import io
    from matplotlib.figure import Figure as F
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    ims = []
    for f in (old_fig, new_fig):
        buf = io.BytesIO()
        f.savefig(buf, format="png", dpi=dpi)
        buf.seek(0)
        ims.append(mpl.image.imread(buf))
    h = 1000                                         # both shown at the SAME height: what you see when fitting to a window
    ws = [int(i.shape[1] * h / i.shape[0]) for i in ims]
    w = sum(ws) + 60
    fig = F(figsize=(w / 100, (h + 40) / 100))
    FigureCanvasAgg(fig)
    x = 0
    for im, wi, t in zip(ims, ws, (title_old, title_new)):
        ax = fig.add_axes([x / w, 0, wi / w, h / (h + 40)])
        ax.imshow(im)
        ax.axis("off")
        fig.text((x + wi / 2) / w, 1 - 20 / (h + 40), t, ha="center", va="center", fontsize=9)
        x += wi + 60
    fig.savefig(path, dpi=100, facecolor="white")
    return Path(path)


def describe(specs: list[PanelSpec], fig: Figure | None = None) -> dict:
    """Facts the intake questions must quote: what the original actually does (read, not guessed)."""
    out = {"panels": []}
    if fig is not None:
        w, h = fig.get_size_inches() * 25.4
        out["original_figure_mm"] = [round(float(w), 1), round(float(h), 1)]
    for p in specs:
        e = {"xlim": p.xlim, "ylim": p.ylim, "xlabel": p.xlabel, "ylabel": p.ylabel, "aspect": str(p.aspect),
             "colorbar": None if not p.colorbar else {k: v for k, v in p.colorbar.items() if k != "ax"}, "layers": []}
        for L in p.layers:
            d = L.d
            x = {"kind": L.kind}
            if d.get("cmap") is not None:
                x["cmap"] = d["cmap"].name
                x["cmap_is_diverging"] = is_diverging(d["cmap"])
            if d.get("norm") is not None:
                n = d["norm"]
                x["norm"] = {"type": type(n).__name__, "vmin": float(n.vmin), "vmax": float(n.vmax)}
            if d.get("arr") is not None:
                a = np.ma.asarray(d["arr"]).astype(float)
                x["shape"] = list(a.shape)
                x["masked_or_nan_fraction"] = float(np.mean(np.ma.getmaskarray(a) | ~np.isfinite(np.ma.filled(a, np.nan))))
                if d.get("norm") is not None:
                    v = np.ma.compressed(np.ma.masked_invalid(a))
                    x["fraction_beyond_limits"] = float(np.mean((v < d["norm"].vmin) | (v > d["norm"].vmax))) if v.size else 0.0
                    x["data_range"] = [float(v.min()), float(v.max())] if v.size else None
            for k in ("interpolation", "shading", "extent"):
                if k in d:
                    x[k] = d[k]
            if L.kind == "text":
                x["text"] = d["s"]
            e["layers"].append(x)
        out["panels"].append(e)
    return out
