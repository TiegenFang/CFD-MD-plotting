"""Single source of truth for typography, rcParams and the style state.

Everything comes from ``assets/theme.json``. Two entry points:

* ``style_context(profile, ...)``  context manager, restores rcParams on exit (CLI renderers)
* ``apply_style(medium, ...)``     scripts/notebooks; keeps the style until ``reset_style()``

Neither resets unrelated rcParams (no ``rcParams.update(rcParamsDefault)``).
The same numbers are exported as ``assets/styles/*.mplstyle`` by
``export_mplstyle.py`` so a plain ``plt.style.use`` gives the same base style.
"""
from __future__ import annotations

import contextlib
import json
import os
import warnings
from pathlib import Path
from typing import Any, Iterator

import matplotlib as mpl
from cycler import cycler
from matplotlib import font_manager as fm

ASSETS = Path(__file__).resolve().parents[2] / "assets"
THEME_PATH = ASSETS / "theme.json"
FONT_DIR = Path(__file__).resolve().parent / "fonts"
MM = 1.0 / 25.4

#: current style state (read by layout/qa/export). Replaced on entry/exit of a style.
STATE: dict[str, Any] = {}
_STACK: contextlib.ExitStack | None = None


def get(key: str, default=None):
    """Value from the active style state (font sizes, spine width, ...)."""
    return STATE.get(key, default)


# ----------------------------------------------------------------------------- theme
def load_theme(override: str | Path | None = None) -> dict[str, Any]:
    """Installed theme; an optional project JSON overrides *known* keys only."""
    theme = json.loads(THEME_PATH.read_text(encoding="utf-8"))

    def merge(dst: dict, src: dict, prefix: str = "") -> None:
        for key, val in src.items():
            if key not in dst:
                raise ValueError(f"Unknown style key: {prefix}{key}")
            if isinstance(dst[key], dict):
                if not isinstance(val, dict):
                    raise ValueError(f"Expected mapping: {prefix}{key}")
                if key in ("palettes", "profiles"):      # open registries: new names allowed
                    dst[key].update(val)
                else:
                    merge(dst[key], val, prefix + key + ".")
            else:
                dst[key] = val

    if override is not None:
        merge(theme, json.loads(Path(override).read_text(encoding="utf-8")))
    return theme


def media_of(theme: dict, profile: str) -> dict:
    """Merged medium sizes + canvas defaults for a profile name (or medium name)."""
    profiles = theme["profiles"]
    if profile in profiles:
        p = profiles[profile]
        medium = p["medium"]
    elif profile in theme["media"]:
        p, medium = {}, profile
    else:
        raise ValueError(f"Unknown profile {profile!r}. Choose {sorted(profiles)}.")
    m = dict(theme["media"][medium])
    m["medium"] = medium
    m["profile"] = profile if profile in profiles else medium
    m["width_mm"] = float(p.get("width_mm", theme["widths_mm"].get(
        {"paper": "single", "slide": "slide", "poster": "poster"}[medium])))
    m["height_mm"] = float(p.get("height_mm", m["width_mm"] * 0.7))
    return m


# ----------------------------------------------------------------------------- fonts
def register_fonts() -> list[str]:
    """Make bundled optional fonts (Roboto*, Apache-2.0) visible. Arial is never bundled."""
    added = []
    if FONT_DIR.is_dir():
        for f in sorted(FONT_DIR.glob("*.ttf")):
            try:
                fm.fontManager.addfont(str(f))
                added.append(f.name)
            except Exception as exc:  # pragma: no cover
                warnings.warn(f"could not register font {f.name}: {exc}")
    return added


def family_present(family: str) -> bool:
    try:
        fm.findfont(fm.FontProperties(family=family), fallback_to_default=False)
        return True
    except ValueError:
        return False


def _fallback_allowed(flag: bool | None) -> bool:
    if flag is not None:
        return bool(flag)
    return os.environ.get("SCIVIS_ALLOW_FONT_FALLBACK", "") not in ("", "0", "false", "False")


def resolve_font(theme: dict, *, font: str = "journal", allow_fallback: bool | None = None):
    """Return (family, requested, fell_back, metric_compatible).

    Arial is required unless a fallback is authorised (argument or the environment
    variable SCIVIS_ALLOW_FONT_FALLBACK=1). The fallback is always recorded.
    ``font="rougier"`` selects the book's Roboto Condensed (bundled, opt-in).
    """
    register_fonts()
    cfg = theme["font"]
    if font == "rougier":
        for fam in cfg["alt_stack"]:
            if family_present(fam):
                return fam, cfg["alt_stack"][0], fam != cfg["alt_stack"][0], False
        raise RuntimeError("font='rougier' needs the bundled Roboto files in scivis/fonts/.")
    if font != "journal":
        raise ValueError("font must be 'journal' (Arial) or 'rougier'.")
    preferred = cfg["preferred"]
    if family_present(preferred):
        return preferred, preferred, False, True
    if not _fallback_allowed(allow_fallback):
        raise RuntimeError(
            f"Font {preferred!r} is unavailable. Install a licensed local copy, or authorise a "
            "recorded draft fallback (allow_font_fallback=True / --allow-font-fallback / "
            "SCIVIS_ALLOW_FONT_FALLBACK=1).")
    for fam in cfg["fallbacks"]:
        if family_present(fam):
            warnings.warn(f"Draft font fallback: {preferred} -> {fam}", stacklevel=3)
            return fam, preferred, True, fam in cfg["metric_compatible"]
    raise RuntimeError("No permitted fallback font is installed.")


# ----------------------------------------------------------------------------- rcParams
def build_rc(theme: dict, m: dict, family: str, *, cjk: bool = False, boxed: bool | None = None,
             legend_box: bool | None = None, usetex: bool = False, preview_dpi: int = 150) -> dict:
    from . import palettes as P
    ax = theme["axes"]
    if ax["frame"] not in {"box", "left-bottom"}:
        raise ValueError("axes.frame must be box or left-bottom.")
    boxed = (ax["frame"] == "box") if boxed is None else boxed
    legend_box = ax["legend_frame"] if legend_box is None else legend_box
    outline = theme["colors"]["outline"]
    cycle = P.palette(theme["colors"]["categorical"], theme)[:6]
    chain = [family] + [f for f in (theme["font"]["cjk"] if cjk else []) if family_present(f)]
    if cjk and len(chain) == 1:
        warnings.warn("cjk=True but no CJK font is installed; Chinese glyphs will be missing")
    sp = m["spine"]
    tdir = ax["tick_direction"] if boxed else "out"
    mirror = boxed and ax["mirror_ticks"]
    rc = {
        "font.family": chain, "font.sans-serif": chain, "font.size": m["base"], "font.weight": "normal",
        "axes.labelsize": m["base"], "axes.titlesize": m["title"], "axes.titleweight": "bold",
        "axes.titlelocation": "left", "axes.titlepad": 3.5, "axes.labelpad": 2.0,
        "xtick.labelsize": m["tick"], "ytick.labelsize": m["tick"],
        "legend.fontsize": m["legend"], "legend.title_fontsize": m["legend"],
        "text.usetex": usetex,
        "mathtext.fontset": "custom", "mathtext.default": "it", "mathtext.rm": family,
        "mathtext.it": f"{family}:italic", "mathtext.bf": f"{family}:bold", "mathtext.sf": family,
        "mathtext.cal": "STIXGeneral:italic", "mathtext.tt": "DejaVu Sans Mono",
        "mathtext.fallback": theme["font"]["math_fallback"], "axes.unicode_minus": True,
        "axes.formatter.use_mathtext": True,
        "axes.linewidth": sp, "axes.spines.top": boxed, "axes.spines.right": boxed,
        "axes.spines.left": True, "axes.spines.bottom": True, "axes.axisbelow": True,
        "axes.grid": False, "grid.color": theme["colors"]["neutrals"]["grey_pale"],
        "grid.linewidth": sp * 0.6, "axes.edgecolor": outline, "axes.labelcolor": outline,
        "axes.prop_cycle": cycler(color=cycle), "contour.negative_linestyle": "solid",
        "xtick.color": outline, "ytick.color": outline, "xtick.direction": tdir, "ytick.direction": tdir,
        "xtick.top": mirror, "ytick.right": mirror, "xtick.bottom": True, "ytick.left": True,
        "xtick.labeltop": ax["label_top"], "ytick.labelright": ax["label_right"],
        "xtick.major.size": m["tick_major"], "ytick.major.size": m["tick_major"],
        "xtick.major.width": sp, "ytick.major.width": sp,
        "xtick.minor.size": m["tick_minor"], "ytick.minor.size": m["tick_minor"],
        "xtick.minor.width": sp * 0.7, "ytick.minor.width": sp * 0.7,
        "xtick.minor.visible": bool(m["minor"] and ax["minor_ticks"]),
        "ytick.minor.visible": bool(m["minor"] and ax["minor_ticks"]),
        "xtick.major.pad": 2.0, "ytick.major.pad": 2.0,
        "lines.linewidth": m["line"], "lines.markersize": m["marker"], "lines.solid_capstyle": "round",
        "patch.linewidth": sp,
        "legend.frameon": legend_box, "legend.fancybox": False, "legend.framealpha": 1.0,
        "legend.edgecolor": outline, "legend.facecolor": "white", "legend.handlelength": 1.8,
        "legend.borderaxespad": 0.5, "legend.borderpad": 0.45, "legend.labelspacing": 0.3,
        "legend.handletextpad": 0.55,
        "figure.dpi": preview_dpi, "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.dpi": theme["export"]["dpi"], "savefig.facecolor": "white", "savefig.bbox": None,
        "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none",
        "figure.constrained_layout.use": False, "path.simplify": False,
    }
    if "mathtext.bfit" in mpl.rcParams:
        rc["mathtext.bfit"] = f"{family}:bold:italic"
    rc["image.cmap"] = "viridis"                   # default image map follows the colour role
    try:
        nm = P.get_cmap(theme["colors"]["sequential"]).name.split("_")[0]
        for cand in (f"cmc.{nm}", nm):
            if cand in mpl.colormaps:
                rc["image.cmap"] = cand
                break
    except Exception:                              # pragma: no cover
        pass
    return rc


def _state(theme, m, family, requested, fell_back, metric_ok, boxed, legend_box, rc, font):
    st = dict(m)
    st.update(theme=theme, font_key=font, primary=family, requested=requested,
              font_fallback_used=fell_back, font_ok=(not fell_back) or metric_ok,
              boxed=rc["axes.spines.top"], legend_box=rc["legend.frameon"],
              math_fallback=theme["font"]["math_fallback"],
              font_note="Math glyph fallback and SVG viewer substitution need visual review.")
    return st


@contextlib.contextmanager
def style_context(profile: str = "paper", *, override: str | Path | None = None,
                  allow_font_fallback: bool | None = None, font: str = "journal",
                  cjk: bool = False, boxed: bool | None = None, legend_box: bool | None = None,
                  usetex: bool = False) -> Iterator[dict[str, Any]]:
    """Apply the house style for the ``with`` block only; rcParams are restored on exit."""
    global STATE
    theme = load_theme(override)
    m = media_of(theme, profile)
    family, requested, fell_back, metric_ok = resolve_font(theme, font=font, allow_fallback=allow_font_fallback)
    rc = build_rc(theme, m, family, cjk=cjk, boxed=boxed, legend_box=legend_box, usetex=usetex)
    state = _state(theme, m, family, requested, fell_back, metric_ok, boxed, legend_box, rc, font)
    state["profile"] = profile
    state["font_resolved"] = family
    state["font_requested"] = requested
    state["math_fontset"] = "custom"
    previous = STATE
    with mpl.rc_context(rc):
        STATE = state
        try:
            yield state
        finally:
            STATE = previous


def apply_style(medium: str = "paper", font: str = "journal", *, cjk: bool = False,
                boxed: bool | None = None, legend_box: bool | None = None, usetex: bool = False,
                override: str | Path | None = None, allow_font_fallback: bool | None = None) -> dict:
    """Install the style until ``reset_style()`` (scripts/notebooks). ``medium`` may be any profile."""
    global _STACK
    reset_style()
    _STACK = contextlib.ExitStack()
    cm = style_context(medium, override=override, allow_font_fallback=allow_font_fallback, font=font,
                       cjk=cjk, boxed=boxed, legend_box=legend_box, usetex=usetex)
    try:
        state = _STACK.enter_context(cm)
    except Exception:
        _STACK = None
        raise
    return dict(state)


def reset_style() -> None:
    global _STACK
    if _STACK is not None:
        _STACK.close()
        _STACK = None


def width_mm(name_or_mm) -> float:
    """'single' | 'one_half' | 'double' | 'slide' | 'poster' | millimetres."""
    if isinstance(name_or_mm, str):
        theme = STATE.get("theme") or load_theme()
        if name_or_mm not in theme["widths_mm"]:
            raise ValueError(f"Unknown width {name_or_mm!r}; choose {sorted(theme['widths_mm'])} or give mm.")
        return float(theme["widths_mm"][name_or_mm])
    w = float(name_or_mm)
    if not w > 0:
        raise ValueError("Width must be positive millimetres.")
    return w
