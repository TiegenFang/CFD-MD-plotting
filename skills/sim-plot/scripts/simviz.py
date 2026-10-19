"""Compatibility facade for the original sim-plot API; the implementation lives in ``scivis``.

Existing project scripts that import ``simviz`` keep working. New code should import
``scivis`` directly (``scivis.theme`` / ``palettes`` / ``layout`` ...).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from scivis import theme as _theme, palettes as _P, layout as _layout            # noqa: E402
from scivis.export import export_figure, VERSION                                  # noqa: E402,F401
from scivis.encodings import categorical_styles, ordered_colors, scatter_style    # noqa: E402,F401
from scivis.norms import make_norm, field_status                                  # noqa: E402,F401
from scivis.theme import load_theme, THEME_PATH, style_context                    # noqa: E402,F401


def get_palette(name_or_colors, theme):
    return _P.palette(name_or_colors, theme)


def get_cmap(name: str, *, missing: str = "#DDDDDD"):
    return _P.get_cmap(name, missing=missing, white_center=None if not name.startswith("cmc.") else False)


def configure_axes(ax, state: dict, *, categorical_x: bool = False) -> None:
    _layout.style_axes(ax, categorical_x=categorical_x)


def new_figure(state: dict, *, width_mm: float | None = None, height_mm: float | None = None):
    """Single-axes figure at an exact mm size; margins auto-fit to the furniture on export."""
    w = state["width_mm"] if width_mm is None else width_mm
    h = state["height_mm"] if height_mm is None else height_mm
    c = _layout.make_canvas(w, h, autofit=True)
    ax = c.ax(0, 0)
    return c.fig, ax
