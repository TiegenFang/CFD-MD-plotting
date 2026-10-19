"""Render tidy CSV line/scatter/bar/small-multiples data using one canonical plotting script."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scivis import layout, scales
from scivis.theme import style_context
from scivis.encodings import categorical_styles, ordered_colors, scatter_style
from scivis.export import export_figure


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", type=Path)
    ap.add_argument("--allow-font-fallback", action="store_true", help="Explicit draft-only fallback.")
    ap.add_argument("--overwrite", action="store_true", help="Replace only the configured output files.")
    args = ap.parse_args()
    cfg = json.loads(args.config.read_text(encoding="utf-8"))
    base = args.config.resolve().parent
    data_path = base / cfg["data"]
    with data_path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise ValueError("Empty CSV.")
    xcol, ycol = cfg["x"], cfg["y"]
    gcol = cfg.get("group")
    for name in (xcol, ycol, *([gcol] if gcol else [])):
        if name not in rows[0]:
            raise ValueError(f"Missing column {name!r}")
    label_of = lambda r: r[gcol] if gcol else cfg.get("series_label", "Data")
    groups = list(dict.fromkeys(label_of(r) for r in rows))
    order = cfg.get("order", groups)
    if set(order) != set(groups) or len(order) != len(groups):
        raise ValueError("Group order must contain each observed group exactly once.")
    kind = cfg.get("kind", "line")
    if kind not in {"line", "scatter", "bar", "multiples"}:
        raise ValueError("kind must be line, scatter, bar or multiples.")
    def num(value):
        return float(value) if str(value).strip() else float("nan")
    uncertainty = cfg.get("uncertainty")
    if uncertainty and not uncertainty.get("definition"):
        raise ValueError("Name the uncertainty estimator and unit of replication.")
    style_file = base / cfg["style_override"] if cfg.get("style_override") else None
    report_rows = {}
    with style_context(cfg.get("profile", "paper"), override=style_file,
                       allow_font_fallback=True if args.allow_font_fallback else None,
                       font=cfg.get("font", "journal"), cjk=cfg.get("cjk", False)) as state:
        w_mm = cfg.get("width_mm", state["width_mm"])
        h_mm = cfg.get("height_mm", state["height_mm"])
        canvas = None
        fig = ax = None
        collected = {}
        if kind != "multiples":
            canvas = layout.make_canvas(w_mm, h_mm, autofit="margins_mm" not in cfg,
                                        margins=cfg.get("margins_mm"))
            fig, ax = canvas.fig, canvas.ax(0, 0)
        encoding = dict(cfg.get("color_encoding", {"mode": "categorical"}))
        if encoding["mode"] not in {"categorical", "ordered"}:
            raise ValueError("color_encoding.mode must be categorical or ordered.")
        if encoding["mode"] == "ordered":
            vals = [encoding["values"][g] for g in order]
            defaults = state["theme"]["colors"]["ordered"]
            encoding.setdefault("cmap", defaults["cmap"])
            encoding.setdefault("segment", defaults["segment"] if encoding["cmap"] == defaults["cmap"] else [0.0, 1.0])
            cs = ordered_colors(vals, cmap=encoding["cmap"], limits=tuple(encoding["limits"]), segment=encoding["segment"])
            styles = {g: {"color": cs[i], "marker": state["theme"]["markers"][i % 6], "linestyle": "-"}
                      for i, g in enumerate(order)}
        elif kind == "multiples" and cfg.get("multiples_colors") != "categorical":
            styles = {g: {} for g in order}          # one accent colour, ghost the rest
        else:
            styles = categorical_styles(order, state, cfg.get("style_registry"),
                                        palette=encoding.get("palette"))
        bar_categories = cfg.get("categories", list(dict.fromkeys(r[xcol] for r in rows)))
        if kind == "bar" and (len(set(bar_categories)) != len(bar_categories) or
                              set(bar_categories) != {r[xcol] for r in rows}):
            raise ValueError("categories must contain each CSV x category exactly once.")
        for i, group in enumerate(order):
            subset = [r for r in rows if label_of(r) == group]
            if kind == "bar":
                lookup = {r[xcol]: r for r in subset}
                if len(lookup) != len(subset):
                    raise ValueError("Bars require one precomputed value per group/category. "
                                     "Do not silently aggregate replicates.")
                if set(lookup) != set(bar_categories):
                    raise ValueError("Missing grouped-bar cells. Supply explicit missing cells, not silent omission.")
                subset = [lookup[c] for c in bar_categories]
                x = np.arange(len(bar_categories), dtype=float)
            else:
                x = np.array([num(r[xcol]) for r in subset])
                if not np.isfinite(x).all():
                    raise ValueError("x contains invalid values. Resolve missing coordinates explicitly.")
                if kind == "line" and np.any(np.diff(x) < 0):
                    if not cfg.get("preserve_path_order", False):
                        raise ValueError("x is not monotone. Explicitly choose path order for hysteresis/trajectories. "
                                         "The renderer never silently sorts or changes connectivity.")
            y = np.array([num(r[ycol]) for r in subset])
            if np.isinf(y).any():
                raise ValueError("Infinite y values are not valid observations.")
            finite = np.isfinite(y)
            if not finite.any():
                raise ValueError(f"No finite observations for group {group}")
            report_rows[group] = {"rows": len(subset), "missing_y": int((~finite).sum())}
            if cfg.get("xscale") == "log" and np.any(x <= 0):
                raise ValueError("Logarithmic x axis requires positive x values.")
            if cfg.get("yscale") == "log" and np.any(y[finite] <= 0):
                raise ValueError("Logarithmic y axis would hide nonpositive data.")
            if kind == "multiples":
                if uncertainty:
                    raise ValueError("kind=multiples does not draw uncertainty; use kind=line per case.")
                collected[group] = (x, y)
                continue
            lo = hi = None
            if uncertainty:
                lo = np.array([num(r[uncertainty["lower"]]) for r in subset])
                hi = np.array([num(r[uncertainty["upper"]]) for r in subset])
                if not np.isfinite(lo[finite]).all() or not np.isfinite(hi[finite]).all():
                    raise ValueError("Missing uncertainty for a displayed observation.")
                if np.any(lo[finite] > y[finite]) or np.any(hi[finite] < y[finite]):
                    raise ValueError("Errorbar intervals must bracket the estimate. Use an interval plot otherwise.")
                if cfg.get("yscale") == "log" and np.any(lo[finite] <= 0):
                    raise ValueError("An uncertainty interval crosses zero on a log axis.")
            sty = styles[group]
            color = sty["color"]
            if kind == "line":
                ax.plot(x, y, label=group, color=color, linestyle=sty.get("linestyle", "-"),
                        marker=sty.get("marker", "o") if cfg.get("markers", False) else None,
                        markerfacecolor="white", markeredgewidth=0.8,
                        markevery=cfg.get("markevery", 1))
            elif kind == "scatter":
                options = dict(cfg.get("scatter", {}))
                if "alpha" in cfg:
                    options.setdefault("alpha", cfg["alpha"])
                kw = scatter_style(color, state, options, n_points=len(subset))
                marker = sty.get("marker", "o")
                if marker in {"x", "+", "1", "2", "3", "4", "|", "_"}:
                    # Line-only markers have no face to make hollow.
                    kw.pop("facecolors")
                    kw.pop("edgecolors")
                    kw["color"] = color
                    kw["linewidths"] = max(0.6, kw["linewidths"])
                ax.scatter(x, y, label=group, marker=marker, **kw, zorder=3,
                           rasterized=cfg.get("rasterize_points", False))
            else:
                pitch = 0.72 / len(order)
                width = 0.86 * pitch
                x = x + (i - (len(order) - 1) / 2) * pitch
                ax.bar(x, y, width=width, label=group, color=color,
                       edgecolor=state["theme"]["colors"]["outline"], linewidth=0.35, hatch=sty.get("hatch"))
            if uncertainty:
                if kind == "line" and uncertainty.get("display", "band") == "band":
                    ax.fill_between(x, lo, hi, where=finite, color=color, alpha=0.12, linewidth=0, zorder=1)
                else:
                    ax.errorbar(x, y, yerr=np.vstack([y - lo, hi - y]), fmt="none", zorder=2,
                                ecolor=color if kind != "bar" else "#303030",
                                elinewidth=0.8, capsize=2.0, capthick=0.8)
        if kind == "multiples":
            ncols = int(cfg.get("ncols", 3))
            colors = None
            if encoding["mode"] == "ordered":
                colors = dict(zip(order, [mcolor for mcolor in cs]))
            elif cfg.get("multiples_colors") == "categorical":
                colors = [styles[g]["color"] for g in order]
            canvas, axes_ = layout.small_multiples(
                {g: collected[g] for g in order}, ncols=ncols, width=w_mm,
                cell_aspect=cfg.get("cell_aspect", 0.75), xlabel=cfg["xlabel"], ylabel=cfg["ylabel"],
                colors=colors, xscale=cfg.get("xscale", "linear"), yscale=cfg.get("yscale", "linear"),
                xlim=cfg.get("xlim"), ylim=cfg.get("ylim"))
            fig = canvas.fig
        else:
            if kind == "bar":
                ax.set_xticks(np.arange(len(bar_categories)), bar_categories)
                if cfg.get("yscale") == "log":
                    raise ValueError("This bar template uses a zero baseline. Choose a point/interval plot for log data.")
                bottom, top = ax.get_ylim()
                ax.set_ylim(min(0, bottom), max(0, top))
            for axis in ("x", "y"):
                scale = cfg.get(axis + "scale", "linear")
                if scale not in {"linear", "log", "symlog"}:
                    raise ValueError("CSV renderer supports linear/log/symlog axes. Use the shared API for other scales.")
                if scale == "symlog":
                    scales.set_symlog(ax, axis, cfg.get(axis + "_linthresh"), note=cfg.get(axis + "_linthresh_reason"))
                    if not cfg.get(axis + "_linthresh_reason"):
                        raise ValueError("symlog needs a recorded physical reason: " + axis + "_linthresh_reason.")
                elif getattr(ax, "get_" + axis + "scale")() != scale:
                    getattr(ax, "set_" + axis + "scale")(scale)
                if axis + "lim" in cfg:
                    getattr(ax, "set_" + axis + "lim")(cfg[axis + "lim"])
            layout.style_axes(ax, categorical_x=(kind == "bar"))
            if kind == "bar":
                lo_axis, hi_axis = sorted(ax.get_ylim())
                if not lo_axis <= 0 <= hi_axis:
                    raise ValueError("A bar chart must include its zero baseline.")
            ax.set(xlabel=cfg["xlabel"], ylabel=cfg["ylabel"])
            if cfg.get("title"):
                ax.set_title(cfg["title"], loc="left")
            if cfg.get("legend", True):
                legend_kwargs = {"loc": cfg.get("legend_loc", "best"),
                                 "ncol": cfg.get("legend_columns", 1)}
                if "legend_bbox" in cfg:
                    legend_kwargs["bbox_to_anchor"] = tuple(cfg["legend_bbox"])
                if kind == "scatter":
                    legend_kwargs.update(handlelength=1.0, handletextpad=0.4)
                ax.legend(**legend_kwargs)
        metadata = {"input": data_path.name, "input_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
                    "config": cfg, "row_counts": report_rows, "uncertainty": uncertainty,
                    "transformations": "none in renderer", "color_encoding": encoding,
                    "synthetic": cfg.get("synthetic", False), "resolved_styles": styles,
                    "scatter_preset": cfg.get("scatter", {}).get("preset", state["theme"]["scatter"]["default"]) if kind == "scatter" else None}
        report = export_figure(fig, base / cfg["output"], state, provenance=metadata,
                               formats=cfg.get("formats"), allow_overwrite=args.overwrite, kind=kind)
        print(json.dumps({"outputs": report["outputs"], "font": report["font_resolved"],
                          "row_counts": report_rows}, ensure_ascii=False))

if __name__ == "__main__":
    main()
