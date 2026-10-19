"""Render a 2D native rectilinear or triangular field on the shared scivis layout layer.

No Delaunay or implicit cell-to-point conversion. Optional overlays (all explicit in the
config): ``streamlines`` (u,v arrays on a regular grid), ``zoom`` (magnified inset with the
same cmap/norm), ``halo_text`` annotations, ``boundary_xy`` outline.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import numpy as np

SHARED = Path(__file__).resolve().parents[2] / "sim-plot" / "scripts"
if not (SHARED / "scivis" / "layout.py").is_file():
    raise RuntimeError("Install sim-field and sim-plot as sibling skill directories.")
sys.path.insert(0, str(SHARED))
from scivis import layout, palettes as P, fields                                   # noqa: E402
from scivis.theme import style_context                                              # noqa: E402
from scivis.norms import make_norm                                                  # noqa: E402
from scivis.export import export_figure                                             # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", type=Path)
    ap.add_argument("--allow-font-fallback", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    base = args.config.resolve().parent
    if not cfg.get("units") or not cfg.get("coordinate_units"):
        raise ValueError("Declare field units and coordinate units.")
    if not cfg.get("domain_description"):
        raise ValueError("Describe the physical domain and masks.")
    if not cfg.get("source_id"):
        raise ValueError("Record a source identifier or upstream provenance path.")
    grid = cfg["grid"]
    association = cfg["association"]
    method = cfg.get("method", "pcolormesh" if grid == "rectilinear" else "tripcolor")
    scale = cfg.get("scale", "linear")
    diverging = scale in {"symmetric", "two-slope", "symlog"}
    if diverging and not cfg.get("reference_description"):
        raise ValueError("Describe the physical reference for the diverging scale.")
    style_file = base / cfg["style_override"] if cfg.get("style_override") else None
    with np.load(base / cfg["data"], allow_pickle=False) as f:
        data = {k: f[k] for k in f.files}
    with style_context(cfg.get("profile", "paper"), override=style_file,
                       allow_font_fallback=True if args.allow_font_fallback else None,
                       font=cfg.get("font", "journal"), cjk=cfg.get("cjk", False)) as state:
        cmap_name = cfg.get("cmap", state["theme"]["colors"]["diverging" if diverging else "sequential"])
        cmap = P.get_cmap(cmap_name, bad=state["theme"]["colors"]["missing"],
                          white_center=cfg.get("white_center"))
        norm = make_norm(scale, *cfg["limits"], center=cfg.get("center", 0.0),
                         linthresh=cfg.get("linthresh"), boundaries=cfg.get("boundaries"), ncolors=cmap.N)
        draw, stats, extent = fields.prepare_field(
            data, grid, association, method, norm, levels=cfg.get("levels"), limits=cfg["limits"])
        if cfg.get("aspect", "equal") != "equal" and not cfg.get("aspect_reason"):
            raise ValueError("Non-geometric aspect requires a recorded reason, e.g. time-space axes.")
        xlim = cfg.get("xlim", [extent[0], extent[1]])
        ylim = cfg.get("ylim", [extent[2], extent[3]])
        equal = cfg.get("aspect", "equal") == "equal"
        W = cfg.get("width_mm", state["width_mm"])
        k = state["base"] / 7.0
        margins = cfg.get("margins_mm", (11.5 * k, 9.0 * k, 13.0 * k, 6.0 * k))
        if equal:
            asp = fields.cell_aspect(xlim, ylim)
            if "width_mm" not in cfg:      # tall panels -> narrow figure; an explicit width_mm is never changed
                W = layout.fit_width(W, asp, margins, cfg.get("max_panel_height_mm"))
            canvas = layout.make_canvas(W, cell_aspect=asp, margins=margins)
        else:
            canvas = layout.make_canvas(W, cfg.get("height_mm", state["height_mm"]), margins=margins)
        ax = canvas.ax(0, 0, field=True)
        ax.set_facecolor(state["theme"]["colors"]["missing"])   # masked/solid cells read as 'no data', not as white
        artist = draw(ax, cmap)
        if "boundary_xy" in data:
            boundary = np.asarray(data["boundary_xy"], float)
            if boundary.ndim != 2 or boundary.shape[1] != 2:
                raise ValueError("boundary_xy must have shape (n,2), optionally separated by NaN rows.")
            ax.plot(boundary[:, 0], boundary[:, 1], color=P.INK, linewidth=0.8)
        sl = cfg.get("streamlines")
        if sl:
            if grid != "rectilinear":
                raise ValueError("streamlines need a regular rectilinear grid (cell-centre x/y).")
            xc = np.asarray(data[sl.get("x", "xc")], float)
            yc = np.asarray(data[sl.get("y", "yc")], float)
            fields.add_streamlines(ax, xc, yc, data[sl["u"]], data[sl["v"]], density=sl.get("density", 1.1),
                                   seeds=sl.get("seeds", "auto"), n_seeds=sl.get("n_seeds", 15),
                                   lw=sl.get("linewidth", 0.35))
        layout.field_axes(ax, xlim, ylim, cfg["xlabel"], cfg["ylabel"])
        if not equal:
            ax.set_aspect(cfg["aspect"])
        for note in cfg.get("halo_text", []):
            layout.halo(ax.text(note["x"], note["y"], note["text"], fontsize=state["annot"],
                                ha=note.get("ha", "left"), va=note.get("va", "bottom")))
        z = cfg.get("zoom")
        if z:
            def again(ins):
                draw(ins, cmap)
                if "boundary_xy" in data:
                    ins.plot(boundary[:, 0], boundary[:, 1], color=P.INK, linewidth=0.6)
            layout.zoom_inset(ax, z["xlim"], z["ylim"], again, width_mm=z.get("width_mm", 28.0),
                              anchor=z.get("anchor", "upper right"))
        kw = {} if method in {"contourf", "tricontourf"} else {"extend": stats["extend"]}
        ticks = cfg.get("ticks")
        if ticks is None and diverging and scale == "symmetric":
            ticks = P.nice_symmetric_ticks(norm.vmax - cfg.get("center", 0.0), center=cfg.get("center", 0.0))
        layout.add_colorbar(ax, artist, cfg["colorbar_label"], ticks=ticks, **kw)
        if cfg.get("title"):
            ax.set_title(cfg["title"], loc="left")
        metadata = {"source_id": cfg["source_id"], "config": cfg, "field_statistics": stats,
                    "cmap": cmap_name, "cmap_source": cmap._source, "interpolation": "native point contour interpolation" if
                    method in {"contourf", "tricontourf"} else "cell-constant, no interpolation",
                    "geometry_mask": cfg["domain_description"], "synthetic": cfg.get("synthetic", False),
                    "overlays": {"streamlines": sl, "zoom": z, "boundary": "boundary_xy" in data}}
        report = export_figure(canvas.fig, base / cfg["output"], state, provenance=metadata,
                               formats=cfg.get("formats"), allow_overwrite=args.overwrite, kind="field")
        print(json.dumps({"outputs": report["outputs"], "font": report["font_resolved"], "field": stats}))


if __name__ == "__main__":
    main()
