"""Semantic colour system for CFD / MD figures.

Continuous maps  : cmcrameri (Crameri 2020); oslo/vik also ship as archived, hash-checked
                   RGB tables so they work without the package. Tol continuous schemes and
                   viridis/cividis are the fallbacks of the colour-palette standard.
Categorical sets : Paul Tol sets (``tol-bright`` ...) and the soft project families
                   (``muted``, ``cool``, ``earth``, ``okabe-ito`` from theme.json).
Not shipped      : ggsci / journal-brand palettes, jet, rainbow, hsv, turbo.

Rule of the module: pick colour by *what the data means* (role), never by taste.

    cmap = get_cmap("magnitude")                 # sequential, default batlow
    cmap = get_cmap("signed")                    # diverging, default vik, white centre
    norm = diverging_norm(Cp, center=0.0)        # the reference is guaranteed at the centre
    cols = categorical(4)                        # Tol bright, first 4 colours
"""
from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import dataclass

import numpy as np
from matplotlib.colors import Colormap, ListedColormap, Normalize, TwoSlopeNorm
from matplotlib import colors as mcolors

from .theme import ASSETS

_ARCHIVED = ("oslo", "vik")

# --------------------------------------------------------------------------
# Neutrals (Rougier rule 6: "is there a reason this is blue and not black?")
# --------------------------------------------------------------------------
INK = "#000000"         # text, spines, principal curve
GREY_DARK = "#555555"   # Tol 'dark' grey
GREY_MID = "#999999"
GREY = "#BBBBBB"        # Tol bright grey: de-emphasised data
GREY_PALE = "#DDDDDD"   # Tol pale grey: grid, masked / bad-data colour
PAPER = "#FFFFFF"

# --------------------------------------------------------------------------
# Categorical sets: official Paul Tol order (SRON technical note).
# audit.py asserts these equal the tol_colors package, so typos are caught.
# --------------------------------------------------------------------------
TOL = {
    "bright": ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
    "vibrant": ["#EE7733", "#0077BB", "#33BBEE", "#EE3377", "#CC3311", "#009988", "#BBBBBB"],
    "muted": ["#CC6677", "#332288", "#DDCC77", "#117733", "#88CCEE", "#882255", "#44AA99",
              "#999933", "#AA4499"],
    "high_contrast": ["#004488", "#DDAA33", "#BB5566"],
    "medium_contrast": ["#6699CC", "#004488", "#EECC66", "#994455", "#997700", "#EE99AA"],
    "light": ["#77AADD", "#EE8866", "#EEDD88", "#FFAABB", "#99DDFF", "#44BB99", "#BBCC33",
              "#AAAA00"],
    "dark": ["#222255", "#225555", "#225522", "#666633", "#663333", "#555555"],
}
# How many colours of each set may be used before the figure should be faceted.
TOL_MAX = {k: len(v) for k, v in TOL.items()}
TOL_MAX["bright"] = 6      # 7th is grey: reserve it for "other / reference"
TOL_MAX["vibrant"] = 6
TOL_MAX["muted"] = 9
TOL_FILL_ONLY = {"light", "dark"}   # neither separates lines/markers reliably


# --------------------------------------------------------------------------
# Role registry: data meaning -> colormap
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Role:
    kind: str                 # sequential | diverging | cyclic
    default: str
    alts: tuple
    use: str
    avoid: str = ""
    segment: tuple = (0.0, 1.0)   # part of the map to use (light end vs white paper)


ROLES: dict[str, Role] = {
    "magnitude": Role(
        "sequential", "batlow", ("lipari", "oslo", "devon"),
        "Non-negative magnitude: |U|, speed, kinetic energy, scalar concentration.",
        "Do not use for signed data."),
    "positive": Role(
        "sequential", "lipari", ("bilbao", "turku", "batlow"),
        "Non-negative, a few intense features: Q-criterion>0, TKE, nu_t/nu, dissipation, |strain|.",
        "Do not use for signed data."),
    "temperature": Role(
        "sequential", "lajolla", ("batlow", "lipari"),
        "Temperature, enthalpy; warm-toned so it reads as thermal. Light = high.",
        "If the sign relative to a reference matters, use 'signed'."),
    "density": Role(
        "sequential", "oslo", ("devon", "batlow"),
        "MD number/mass density maps, 2-D histograms, scatter point density. Light = high.",
        "On dark backgrounds reverse it so high stays high-contrast.",
        segment=(0.0, 0.88)),      # the near-white top would merge with paper and with masked grey
    "error": Role(
        "sequential", "bilbao", ("lajolla", "lipari"),
        "Absolute error / residual field (always >= 0).",
        "Signed error is 'signed', not this."),
    "signed": Role(
        "diverging", "vik", ("broc", "bam", "sunset", "BuRd"),
        "Signed field about a physical reference: Cp, vorticity, velocity perturbation, "
        "signed error, charge density. Centre = reference value.",
        "Always pair with diverging_norm(): the reference must land on the centre."),
    "signed_dark_center": Role(
        "diverging", "berlin", ("vanimo", "managua"),
        "Same as 'signed' but for dark-background slides, where the zero should recede.",
        "Not for white-paper figures (dark centre reads as 'high')."),
    "phase": Role(
        "cyclic", "romaO", ("vikO", "brocO", "corkO", "bamO"),
        "Angle, phase, orientation (bond-orientational order, wave phase).",
        "Never use a linear map: the wrap-around becomes a fake discontinuity."),
    "cvd_critical": Role(
        "sequential", "cividis", ("batlow",),
        "Sequential data where CVD-identical appearance is a hard requirement.",
        ""),
}

BANNED = {
    "jet": "non-monotonic luminance (verified by audit); invents bands",
    "rainbow": "non-monotonic luminance; yellow band creates artificial edges",
    "gist_rainbow": "rainbow family",
    "nipy_spectral": "rainbow family",
    "gist_ncar": "rainbow family",
    "hsv": "cyclic hue wheel, not for sequential data; use 'phase' for angles",
    "spectral": "diverging with non-monotonic hue/luminance halves",
    "turbo": "improved rainbow but luminance still non-monotonic (verified by audit)",
    "npg": "brand palette, not CVD-audited (ggsci excluded by design)",
    "aaas": "brand palette, not CVD-audited (ggsci excluded by design)",
    "lancet": "brand palette, not CVD-audited (ggsci excluded by design)",
    "jama": "brand palette, not CVD-audited (ggsci excluded by design)",
    "jco": "brand palette, not CVD-audited (ggsci excluded by design)",
    "nejm": "brand palette, not CVD-audited (ggsci excluded by design)",
}

CVD_RISK = {
    "cork": "its blue and green arms converge under deutan/protan simulation "
            "(end separation ~8, audit threshold 15); use vik or bam",
}
_DIVERGING = {"vik", "roma", "bam", "broc", "cork", "lisbon", "tofino", "berlin", "vanimo",
              "managua", "sunset", "BuRd", "PRGn", "nightfall"}
_MPL_OK = {"viridis", "cividis", "magma", "inferno", "plasma"}


# --------------------------------------------------------------------------
# Lookup (archived tables first, packages lazily)
# --------------------------------------------------------------------------
def _archived_table(plain: str):
    directory = ASSETS / "colormaps"
    path = directory / f"{plain}.txt"
    manifest = json.loads((directory / "SOURCES.json").read_text(encoding="utf-8"))
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != manifest["tables"][plain]["sha256"]:
        raise ValueError(f"Archived colormap hash mismatch: {plain}.")
    rgb = np.loadtxt(path)
    if rgb.shape != (256, 3) or not np.isfinite(rgb).all() or np.any((rgb < 0) | (rgb > 1)):
        raise ValueError(f"Invalid archived colormap: {plain}.")
    return rgb, digest, manifest["tables"][plain]["url"]


def _lookup(name: str) -> Colormap:
    """Raw map by name. ``cmc.`` prefix and ``_r`` suffix are accepted."""
    if name.startswith("cmc."):
        name = name[4:]
    reverse = False
    if name.endswith("_r") and name[:-2] in (*_ARCHIVED, *_known_cmc()):
        name, reverse = name[:-2], True
    if name in _MPL_OK:
        import matplotlib.pyplot as plt
        cm = plt.get_cmap(name).copy()
        cm._source = {"name": name, "provider": "matplotlib"}
    elif name in _ARCHIVED:
        rgb, digest, url = _archived_table(name)
        cm = ListedColormap(rgb, name=name)
        cm._source = {"name": name, "provider": "archived cmcrameri RGB table",
                      "table_sha256": digest, "source_url": url}
    else:
        cm = _from_packages(name)
    if reverse:
        src = dict(cm._source, reversed=True)
        cm = cm.reversed()
        cm._source = src
    return cm


def _known_cmc() -> list[str]:
    try:
        from cmcrameri import cm as _cmc
        return [n for n in dir(_cmc) if not n.startswith("_") and not n.endswith("_r")]
    except ImportError:
        return []


def _from_packages(name: str) -> Colormap:
    try:
        from cmcrameri import cm as _cmc
    except ImportError:
        _cmc = None
    if _cmc is not None and hasattr(_cmc, name):
        cm = getattr(_cmc, name).copy()
        cm._source = {"name": name, "provider": "cmcrameri package"}
        return cm
    try:
        import tol_colors as _tol
        if name in _tol.colormaps:
            cm = _tol.colormaps[name].copy()
            cm._source = {"name": name, "provider": "tol_colors package"}
            return cm
    except ImportError:
        pass
    if _cmc is None:
        raise RuntimeError(f"cmcrameri is required for {name!r}: python -m pip install cmcrameri "
                           "(only oslo/vik and their reversals are bundled).")
    raise KeyError(f"unknown colormap '{name}'. Roles: {sorted(ROLES)}; or any cmcrameri / Tol name.")


def _lift_center_to_white(cmap: Colormap, width: float = 0.05, n: int = 512) -> Colormap:
    """Blend the map toward #FFFFFF around its centre (exactly white at 0.5).

    Crameri/Tol diverging maps have a light *tint* at the centre (vik: #ECE5E0,
    roma: #C0EAC3, sunset: #EAECCB). Pure white makes the reference value unambiguous.
    Outside about +/-12 % of the range the map is untouched.
    """
    x = np.linspace(0, 1, n)
    rgb = cmap(x)[:, :3]
    w = np.exp(-((x - 0.5) / width) ** 2)
    rgb = rgb + (1.0 - rgb) * w[:, None]
    out = ListedColormap(rgb, name=f"{cmap.name}_white")
    out._source = dict(getattr(cmap, "_source", {}), white_center=True)
    return out


def get_cmap(spec: str, *, n: int | None = None, reverse: bool = False,
             allow_restricted: bool = False, bad: str | None = None, missing: str | None = None,
             white_center: bool | None = None, segment: tuple | None = None) -> Colormap:
    """Colormap by role ('magnitude', 'signed', ...) or by explicit name.

    n            discretise into n bands (contourf levels, banded legends)
    reverse      reversed copy
    bad/missing  colour for NaN / masked cells (default Tol pale grey, never white)
    white_center diverging maps only: pure #FFFFFF at the centre (default True)
    segment      (lo, hi) part of the map to use; roles may carry their own
    The returned map records its provenance in ``cmap._source`` (and ``_simviz_source``).
    """
    key = spec.lower()
    if key in BANNED or spec in BANNED:
        raise ValueError(f"'{spec}' is not allowed: {BANNED.get(key, BANNED.get(spec))}. "
                         f"Use 'batlow' (sequential) or 'vik' (diverging).")
    role = ROLES.get(spec)
    name = role.default if role else spec
    base = name[4:] if name.startswith("cmc.") else name
    if base.startswith("rainbow") and not allow_restricted:
        raise ValueError(f"Tol '{base}' is a rainbow-type map and its luminance is not "
                         "monotonic (audit). Pass allow_restricted=True only for banded "
                         "categorical-like contours, and say so in the caption.")
    plain = base[:-2] if base.endswith("_r") else base
    if plain in CVD_RISK:
        warnings.warn(f"'{plain}': {CVD_RISK[plain]}")
    cmap = _lookup(name)
    src = dict(cmap._source)
    if role:
        src["role"] = spec
    if reverse:
        cmap = cmap.reversed()
        src["reversed"] = not src.get("reversed", False)
    if white_center is None:
        white_center = plain in _DIVERGING
    if white_center and plain in _DIVERGING:
        c = cmap(0.5)[:3]
        if 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2] > 0.75:
            cmap = _lift_center_to_white(cmap)
            src["white_center"] = True
    seg = segment if segment is not None else (role.segment if role else (0.0, 1.0))
    if tuple(seg) != (0.0, 1.0):
        cmap = truncate(cmap, *seg)
        src["segment"] = list(seg)
    if n is not None:
        cmap = cmap.resampled(n)
    cmap = cmap.with_extremes(bad=bad or missing or GREY_PALE)
    cmap._source = src
    cmap._simviz_source = src          # legacy attribute name used by older provenance code
    return cmap


def role_info(role: str) -> Role:
    return ROLES[role]


def describe_roles() -> str:
    lines = []
    for k, r in ROLES.items():
        lines.append(f"{k:<20s} {r.kind:<10s} default={r.default:<8s} alts={', '.join(r.alts)}\n"
                     f"{'':<20s} {r.use}")
    return "\n".join(lines)


def truncate(cmap: Colormap, lo: float = 0.0, hi: float = 1.0, n: int = 256) -> Colormap:
    """Use only the [lo, hi] part of a map (e.g. so a white end does not vanish on paper)."""
    if not 0.0 <= lo < hi <= 1.0:
        raise ValueError("truncate needs 0 <= lo < hi <= 1")
    cols = cmap(np.linspace(lo, hi, n))
    out = ListedColormap(cols, name=f"{cmap.name}_{lo:.2f}_{hi:.2f}")
    out._source = dict(getattr(cmap, "_source", {}))
    return out.with_extremes(bad=GREY_PALE)


# --------------------------------------------------------------------------
# Normalisation: the other half of a correct colour mapping
# --------------------------------------------------------------------------
def _finite(data, what="data"):
    a = np.asarray(np.ma.filled(np.ma.masked_invalid(np.ma.asarray(data, float)), np.nan), float)
    a = a[np.isfinite(a)]
    if not a.size:
        raise ValueError(f"{what}: no finite values")
    return a


def robust_limits(data, q=(0.5, 99.5)):
    """Percentile limits that stop one outlier cell from flattening the map.

    Returns (vmin, vmax, extend) ready for colorbar(extend=...). Report the percentile
    in the caption whenever you clip.
    """
    a = _finite(data)
    lo, hi = np.percentile(a, q)
    extend = ("both" if a.min() < lo and a.max() > hi else
              "min" if a.min() < lo else "max" if a.max() > hi else "neither")
    return float(lo), float(hi), extend


def sequential_norm(data=None, vmin=None, vmax=None, q=None):
    """Normalize for sequential data. q=(lo,hi) percentiles for robust clipping."""
    if data is not None and (vmin is None or vmax is None):
        if q is None:
            a = _finite(data)
            vmin, vmax = a.min(), a.max()
        else:
            vmin, vmax, _ = robust_limits(data, q)
    if vmin is None or vmax is None or not np.isfinite([vmin, vmax]).all() or not vmin < vmax:
        raise ValueError("Constant or empty field: declare physical vmin < vmax explicitly.")
    return Normalize(vmin=vmin, vmax=vmax)


def diverging_norm(data=None, *, vmax=None, center=0.0, q=None, mode="symmetric", vmin=None):
    """Normalize for diverging data. The centre colour is *always* `center`.

    mode='symmetric' (default): limits = center +/- vmax, with vmax = max|data-center|
        (or the q-percentile of |data-center| when q is given, e.g. q=99.5).
    mode='twoslope': keep the true asymmetric range, pin the centre with TwoSlopeNorm;
        colour-per-unit differs between the two sides: say so in the caption.
    """
    if mode == "twoslope":
        a = _finite(data) if data is not None else None
        lo = (a.min() if a is not None else None) if vmin is None else vmin
        hi = (a.max() if a is not None else None) if vmax is None else vmax
        if lo is None or hi is None or not (lo < center < hi):
            raise ValueError("twoslope needs vmin < center < vmax; use mode='symmetric'")
        return TwoSlopeNorm(vcenter=center, vmin=lo, vmax=hi)
    if vmax is None:
        a = np.abs(_finite(data) - center)
        vmax = np.percentile(a, q) if q is not None else a.max()
    if not np.isfinite(vmax) or vmax <= 0:
        raise ValueError("Field is constant at the reference: pass an explicit vmax.")
    return Normalize(vmin=center - vmax, vmax=center + vmax)


def nice_symmetric_ticks(vmax, center=0.0, nbins=4):
    """Round, symmetric ticks that include the centre: [-2,-1,0,1,2] style."""
    raw = vmax / (nbins / 2)
    mag = 10 ** np.floor(np.log10(raw))
    step = min((m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw), default=raw)
    k = int(np.floor(vmax / step + 1e-9))
    return center + step * np.arange(-k, k + 1)


# --------------------------------------------------------------------------
# Categorical
# --------------------------------------------------------------------------
def categorical(n: int, scheme: str = "bright", *, offset: int = 0) -> list[str]:
    """First n colours of a Tol set, in Tol's own order (designed to be used in order).

    n above the set's limit raises: facet, aggregate, or use markers/linestyles.
    """
    if scheme not in TOL:
        raise ValueError(f"Unknown Tol set {scheme!r}; choose {sorted(TOL)}")
    if scheme in TOL_FILL_ONLY:
        warnings.warn(f"Tol '{scheme}' is meant for filled areas, not thin lines/markers.")
    if n + offset > TOL_MAX[scheme]:
        raise ValueError(
            f"'{scheme}' supports {TOL_MAX[scheme]} categories, got {n}. Facet the figure "
            "(layout.small_multiples), merge small groups into 'other' (grey), or vary "
            "marker/linestyle.")
    return TOL[scheme][offset:offset + n]


def palette(name_or_colors, theme: dict) -> list[str]:
    """Named palette or explicit colour list.

    ``tol-bright`` etc. -> Paul Tol sets (limited to their safe count); plain names are the
    project's soft families from theme.json (muted, cool, earth, okabe-ito).
    """
    if isinstance(name_or_colors, str):
        if name_or_colors.startswith("tol-"):
            sch = name_or_colors[4:]
            if sch not in TOL:
                raise ValueError(f"Unknown palette {name_or_colors!r}.")
            cols = TOL[sch][:TOL_MAX[sch]]
        elif name_or_colors in theme["palettes"]:
            cols = theme["palettes"][name_or_colors]
        else:
            known = sorted(theme["palettes"]) + [f"tol-{k}" for k in TOL]
            raise ValueError(f"Unknown palette {name_or_colors!r}. Choose {known}.")
    else:
        cols = list(name_or_colors)
    if not cols or not all(mcolors.is_color_like(c) for c in cols):
        raise ValueError("A palette must contain valid colors.")
    return list(cols)


_LINESTYLES = ["-", "--", "-.", ":", (0, (5, 1)), (0, (3, 1, 1, 1))]
_MARKERS = ["o", "s", "^", "D", "v", "P"]


def redundant_encoding(n: int, scheme: str = "bright"):
    """List of dicts (color, linestyle, marker) so series stay separable in grayscale."""
    cols = categorical(n, scheme)
    return [dict(color=c, linestyle=_LINESTYLES[i % 6], marker=_MARKERS[i % 6])
            for i, c in enumerate(cols)]


def highlight(n_total: int, highlight_idx, color=None, scheme="bright"):
    """Colours that emphasise a subset and grey out the rest (Rougier rule 6)."""
    color = color or TOL[scheme][1]
    keep = set(np.atleast_1d(highlight_idx).tolist())
    return [color if i in keep else GREY for i in range(n_total)]


# --------------------------------------------------------------------------
# Colour theory helpers (Rougier, "Colors" chapter): interpolate in a perceptual space,
# not in sRGB; group cases by hue and vary lightness inside a group.
# --------------------------------------------------------------------------
_M = np.array([[0.4124564, 0.3575761, 0.1804375],
               [0.2126729, 0.7151522, 0.0721750],
               [0.0193339, 0.1191920, 0.9503041]])
_WHITE = _M @ np.ones(3)


def _srgb_to_lin(c):
    c = np.asarray(c, float)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    c = np.clip(c, 0, None)
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * c ** (1 / 2.4) - 0.055)


def rgb_to_lab(rgb):
    xyz = _srgb_to_lin(rgb) @ _M.T / _WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab_to_rgb(lab):
    lab = np.asarray(lab, float)
    fy = (lab[..., 0] + 16) / 116
    fx, fz = fy + lab[..., 1] / 500, fy - lab[..., 2] / 200
    f = np.stack([fx, fy, fz], -1)
    xyz = np.where(f > 6 / 29, f ** 3, 3 * (6 / 29) ** 2 * (f - 4 / 29)) * _WHITE
    return np.clip(_lin_to_srgb(xyz @ np.linalg.inv(_M).T), 0, 1)


def lab_ramp(colors, n=256, name="lab_ramp") -> ListedColormap:
    """Custom ramp interpolated in CIE Lab (sRGB interpolation turns muddy and uneven).

    Use only when no Crameri/Tol map fits the message; run ``audit`` on the result.
    """
    cols = np.array([mcolors.to_rgb(c) for c in colors])
    if len(cols) < 2:
        raise ValueError("lab_ramp needs at least two colours")
    lab = rgb_to_lab(cols)
    x = np.linspace(0, 1, len(cols))
    xi = np.linspace(0, 1, n)
    out = np.stack([np.interp(xi, x, lab[:, k]) for k in range(3)], -1)
    cm = ListedColormap(lab_to_rgb(out), name=name)
    cm._source = {"name": name, "provider": "lab_ramp", "anchors": [mcolors.to_hex(c) for c in cols]}
    return cm.with_extremes(bad=GREY_PALE)


def colour_stack(base_colors, n_per_group: int, *, spread: float = 22.0) -> list[list[str]]:
    """Hue per group, lightness varies inside a group (Rougier 'colour stacks').

    Returns ``[[shade_0..shade_n-1] for each base colour]``, ordered dark -> light. Use for
    several meshes/orders per solver, several temperatures per model, etc.
    """
    if n_per_group < 1:
        raise ValueError("n_per_group must be >= 1")
    out = []
    for c in base_colors:
        L, a, b = rgb_to_lab(np.array(mcolors.to_rgb(c)))
        Ls = np.linspace(max(L - spread, 18), min(L + spread, 88), n_per_group) if n_per_group > 1 else [L]
        out.append([mcolors.to_hex(lab_to_rgb(np.array([l, a * (0.75 + 0.25 * l / 100), b * (0.75 + 0.25 * l / 100)])))
                    for l in Ls])
    return out
