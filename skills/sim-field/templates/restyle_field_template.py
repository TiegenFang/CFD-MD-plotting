#!/usr/bin/env python
"""RESTYLE TEMPLATE A  (sim-field): FROZEN-block route for 2-D field figures.

Use when the original plotting code cannot simply be run (it also writes data, needs a cluster path,
is not matplotlib, uses filled contours...). Copy this file INTO THE USER'S PROJECT and:

  1. Replace the body of frozen_field() with the user's ORIGINAL data code, copied verbatim:
     loading, masking, unit handling, smoothing, interpolation, limit computation (percentiles
     included), colour map name, contour/boundary computation. Put `# FROZEN from <file>:<lines>`
     above every pasted block. Do not "clean up", rename or re-derive anything.
  2. Return a FrozenField with exactly what the original passed to imshow / pcolormesh.
  3. Edit only the PRESENTATION block. Run. Check the printed frozen summary against the original
     figure's numbers (limits, extend, cmap, interpolation) before trusting the picture.

The template never smooths, clips, rescales or converts units on its own.
"""
import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ============================ PRESENTATION (editable) =========================
OUT_STEM = Path("restyle_out/field_restyled")
SOURCE_ID = "synthetic demo"
WIDTH, PROFILE, FORMATS = "single", "paper", ["pdf", "png", "svg"]
XLABEL = "$r$ (Å)"            # typography of the SAME label text/units; see restyle-mode.md
YLABEL = "$z_{\\mathrm{rel}}$ (Å)"
CBAR_LABEL = "Liquid charge density (e nm$^{-3}$)"
MAX_PANEL_HEIGHT_MM = None    # None: 80 mm paper / 110 slide / 200 poster; tall panels become narrow figures
# Standing decision (user, 2026-10-19): signed fields use vik with a white centre. Set to "signed" for a signed
# field; None keeps the original map (e.g. a sequential field the user did not ask to recolour).
CMAP_OPT_IN = "signed"
# ==============================================================================


# ---- INTAKE CONTRACT: the script refuses to render until the user has confirmed the plan -------------
# First run prints the frozen summary only. Quote it in the questions (restyle-mode.md, Step 2), then set
# confirmed=True and answers_source="user". `--assume-defaults` is for unattended runs and is recorded as such.
# Chinese figure README (<stem>.README.zh-CN.md): sections 4-6. Fill from the REAL data after viewing the figure,
# or leave empty and the file marks them as pending. Only claims the displayed data support; numbers from the data.
INTERPRETATION = {
    "physical_significance": "",   # what the axes/quantities mean physically, normalisation
    "results": "",                 # journal-style description of preliminary results (str or list of paragraphs)
    "discussion": [],              # directions worth discussing/analysing (list of strings)
}

CONTRACT = {"confirmed": False, "answers_source": "", "improve": "typography+layout", "keep_frozen": True,
            "target": "paper, single column"}


@dataclass
class FrozenField:
    """Exactly what the original code handed to matplotlib. All fields are FROZEN."""
    Z: np.ndarray                         # array as drawn (after the ORIGINAL smoothing/interpolation)
    extent: tuple                         # (x0, x1, y0, y1) in the ORIGINAL units
    cmap: str                             # original colour-map name, e.g. "RdBu_r"
    vmin: float
    vmax: float
    extend: str = "neither"               # colour-bar extend arrows of the original
    interpolation: str = "nearest"        # original imshow interpolation
    origin: str = "lower"
    contours: list = field(default_factory=list)   # [(x_array, y_array)] polylines, original coordinates
    texts: list = field(default_factory=list)      # [(x, y, "text")] original annotations
    notes: dict = field(default_factory=dict)      # e.g. {"smoothing": "gaussian sigma 0.8 bins"}


def frozen_field() -> FrozenField:
    # >>>>>>>>>>>>>>>>>>>>>>>>>> REPLACE WITH THE ORIGINAL CODE <<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    # FROZEN from <original_script.py>:<first>-<last>     (demo body below)
    rng = np.random.default_rng(0)
    Z = rng.normal(0, 1, (80, 30))
    return FrozenField(Z=Z, extent=(0, 75, 0, 200), cmap="RdBu_r", vmin=-2.5, vmax=2.5, extend="both",
                       interpolation="bilinear", notes={"demo": True})
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


def _find_scivis():
    import os
    here = Path(__file__).resolve()
    cands = [Path(p) for p in os.environ.get("SCIVIS_PATH", "").split(os.pathsep) if p]
    for base in (here.parents[2], Path.home() / ".agents" / "skills", Path.home() / ".omp" / "agent" / "skills",
                 Path.home() / ".claude" / "skills"):
        cands += [base / "sim-plot" / "scripts", base / "skills" / "sim-plot" / "scripts"]
    for c in cands:
        if (c / "scivis" / "__init__.py").is_file():
            sys.path.insert(0, str(c))
            return
    raise SystemExit("scivis not found. Install sim-plot next to sim-field or set SCIVIS_PATH.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-font-fallback", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--assume-defaults", action="store_true")
    a = ap.parse_args()
    if a.assume_defaults and not CONTRACT["confirmed"]:
        CONTRACT.update(confirmed=True, answers_source="default-unattended")
    _find_scivis()
    import copy
    import matplotlib.colors as mcolors
    import matplotlib.patheffects as pe
    import matplotlib
    from scivis import layout, restyle
    from scivis.palettes import get_cmap
    from scivis.theme import style_context
    from scivis.export import export_figure

    F = frozen_field()
    if not np.isfinite(F.vmin) or not np.isfinite(F.vmax) or not F.vmax > F.vmin:
        raise SystemExit("Invalid frozen colour limits.")
    xl, yl = (F.extent[0], F.extent[1]), (F.extent[2], F.extent[3])
    with style_context(PROFILE, allow_font_fallback=True if a.allow_font_fallback else None) as state:
        k = state["base"] / 7.0
        margins = (11.5 * k, 9.0 * k, 15.0 * k, 6.0 * k)
        aspect = abs(yl[1] - yl[0]) / abs(xl[1] - xl[0])
        c = layout.make_canvas(layout.fit_width(WIDTH, aspect, margins, MAX_PANEL_HEIGHT_MM),
                               cell_aspect=aspect, margins=margins)
        ax = c.ax(0, 0, field=True)
        cm = matplotlib.colormaps[F.cmap] if CMAP_OPT_IN is None else get_cmap(CMAP_OPT_IN)
        norm = mcolors.Normalize(F.vmin, F.vmax)
        im = ax.imshow(F.Z, extent=F.extent, origin=F.origin, interpolation=F.interpolation,
                       cmap=cm, norm=norm, aspect="equal")
        lw = state["line"] * 0.7
        for x, y in F.contours:
            ln, = ax.plot(x, y, color="#222222", lw=lw)
            ln.set_path_effects([pe.Stroke(linewidth=lw + 1.6, foreground="white"), pe.Normal()])
        for x, y, s in F.texts:
            layout.halo(ax.annotate(s, (x, y), fontsize=state["annot"]))
        ax.set_xlim(xl); ax.set_ylim(yl)
        layout.field_axes(ax, xl, yl, XLABEL, YLABEL)
        layout.add_colorbar(ax, im, CBAR_LABEL, extend=F.extend)
        summary = {"cmap": F.cmap if CMAP_OPT_IN is None else f"{F.cmap} -> {CMAP_OPT_IN} (opt-in)",
                   "vmin": F.vmin, "vmax": F.vmax, "extend": F.extend, "interpolation": F.interpolation,
                   "extent": F.extent, "array_sha": hashlib.sha256(np.ascontiguousarray(F.Z, float).tobytes()).hexdigest()[:16],
                   "notes": F.notes}
        print("FROZEN SUMMARY (compare with the original figure):", json.dumps(summary, default=str))
        if not CONTRACT["confirmed"]:
            raise SystemExit(3)   # intake not confirmed: ask the user first, nothing was exported
        prov = {"source_id": SOURCE_ID, "interpretation": INTERPRETATION, "restyle": {"mode": "frozen-block", "frozen": list(restyle.FROZEN),
                                                    "summary": summary, "intake": dict(CONTRACT),
                                                    "original_files_written": False}}
        rep = export_figure(c.fig, OUT_STEM, state, provenance=prov, formats=FORMATS,
                            allow_overwrite=a.overwrite, kind="field")
    print(json.dumps({"outputs": rep["outputs"], "readme_zh": rep.get("readme_zh")}, indent=1))


if __name__ == "__main__":
    main()
