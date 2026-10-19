"""Series encodings: categorical styles, ordered sweeps, scatter mark presets."""
from __future__ import annotations

from typing import Any, Sequence

import numpy as np
from matplotlib import colors as mcolors

from . import palettes as P
from .norms import make_norm


def categorical_styles(labels: Sequence[str], state: dict,
                       registry: dict[str, dict[str, Any]] | None = None,
                       palette: str | Sequence[str] | None = None) -> dict:
    """An explicit per-series registry has precedence over the selected palette.

    More groups than colours/markers raises: facet with ``layout.small_multiples`` (ghost
    series) instead of adding hues.
    """
    labels = list(labels)
    if len(labels) != len(set(labels)):
        raise ValueError("Category labels must be unique.")
    if registry is not None:
        missing = set(labels) - registry.keys()
        if missing:
            raise ValueError(f"Missing categories in style registry: {sorted(missing)}")
        return {key: dict(registry[key]) for key in labels}
    theme = state["theme"]
    cols = P.palette(palette if palette is not None else theme["colors"]["categorical"], theme)
    if len(labels) > min(len(cols), len(theme["markers"])):
        raise ValueError("Too many categories (%d > %d): supply an explicit registry, or use "
                         "kind='multiples' / layout.small_multiples to split the figure."
                         % (len(labels), min(len(cols), len(theme["markers"]))))
    return {name: {"color": cols[i], "marker": theme["markers"][i],
                   "linestyle": theme["line_styles"][i % len(theme["line_styles"])]}
            for i, name in enumerate(labels)}


def ordered_colors(values: Sequence[float], *, cmap: str = "cmc.oslo_r",
                   limits: tuple[float, float], segment: Sequence[float] = (0.0, 1.0)) -> list:
    """Numeric sweep (Re, T, mesh size) -> colours through one shared map."""
    values = np.asarray(values, float)
    if not np.isfinite(values).all():
        raise ValueError("Ordered values must be finite.")
    norm = make_norm("linear", *limits)
    if np.any((values < limits[0]) | (values > limits[1])):
        raise ValueError("Ordered parameter values exceed the declared color domain.")
    segment = np.asarray(segment, dtype=float)
    if segment.shape != (2,) or not np.isfinite(segment).all() or not 0 <= segment[0] < segment[1] <= 1:
        raise ValueError("Require 0 <= ordered palette segment[0] < segment[1] <= 1.")
    u = segment[0] + (segment[1] - segment[0]) * norm(values)
    return list(P.get_cmap(cmap, white_center=False, segment=(0.0, 1.0))(u))


def scatter_style(color, state: dict, options: dict | None = None, *, n_points: int | None = None) -> dict:
    """Choose mark rendering only. No sampling, jitter, fitting or data-dependent hiding.

    ``n_points`` enables the dense-data guard: an alpha below the theme floor, or very many
    points, raises with the hist2d/hexbin recommendation (Rougier optimisation chapter).
    """
    options = dict(options or {})
    allowed = {"preset", "area", "edge_width", "alpha"}
    if set(options) - allowed:
        raise ValueError(f"Unknown scatter options: {sorted(set(options) - allowed)}")
    theme = state["theme"]
    preset = options.get("preset", theme["scatter"]["default"])
    if preset not in theme["scatter"]["presets"]:
        raise ValueError("scatter.preset must be hollow, soft-filled or dense.")
    p = theme["scatter"]["presets"][preset]
    nominal = state["marker"]
    area = float(options.get("area", nominal ** 2 * p["area_scale"]))
    width = float(options.get("edge_width", p["edge_width"]))
    alpha = float(options.get("alpha", p["alpha"]))
    if not np.isfinite([area, width, alpha]).all() or area <= 0 or width < 0 or not 0 < alpha <= 1:
        raise ValueError("Require positive marker area, nonnegative edge width, and 0 < alpha <= 1.")
    if alpha < theme["scatter"]["alpha_floor"]:
        raise ValueError(f"alpha={alpha} is below the readable floor ({theme['scatter']['alpha_floor']}): "
                         "8-bit stacking saturates. Use layout.density_scatter / hexbin / hist2d.")
    if n_points is not None and n_points > theme["scatter"]["hexbin_above_n"] and preset != "dense":
        raise ValueError(f"{n_points} points: use preset 'dense', or layout.density_scatter / hexbin.")
    face = p["face"]
    if face == "series":
        face = color
    elif face == "tint":
        rgb = np.asarray(mcolors.to_rgb(color))
        face = tuple(1 - p["tint_fraction"] * (1 - rgb))
    edge = color if p["edge"] == "series" else "none"
    return {"s": area, "facecolors": face, "edgecolors": edge, "linewidths": width, "alpha": alpha}
