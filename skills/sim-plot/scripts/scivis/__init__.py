"""scivis: the colour, typography and layout layer shared by sim-plot and sim-field.

theme      one theme.json -> rcParams, .mplstyle files, font policy, STATE
palettes   role-based colour (cmcrameri + Paul Tol), norms, Lab ramps, colour stacks
layout     mm-exact canvases, colourbars, panel labels, ghost multiples, zoom insets, QA
fields     2-D field drawing + streamlines;  scales / captions / export / audit / io_foam
"""
from . import theme, palettes, norms, encodings, layout, fields, scales, captions, export, io_foam, restyle  # noqa: F401
style = theme  # legacy alias: style.apply_style(...)
from .theme import apply_style, reset_style, style_context, load_theme  # noqa: F401
from .palettes import get_cmap, categorical, diverging_norm, sequential_norm, robust_limits, ROLES  # noqa: F401

__all__ = ["theme", "palettes", "norms", "encodings", "layout", "fields", "scales", "captions",
           "export", "io_foam", "restyle", "apply_style", "reset_style", "style_context", "load_theme",
           "get_cmap", "categorical", "diverging_norm", "sequential_norm", "robust_limits", "ROLES"]
