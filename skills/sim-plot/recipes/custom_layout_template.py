"""Custom-layout figure: draw what the user specified, panel by panel, on the shared scivis canvas.

Copy this file into the USER's project (e.g. results/figures/make_fig3.py), edit only the EDIT block and the
panel functions, and run it. Never edit the skill's copy. Everything below the EDIT block is the fixed
pipeline: mm-exact canvas -> panels -> panel letters -> QA gate -> pdf/png/svg + .viz.json + caption stub.

The PANELS here draw SYNTHETIC placeholder data. Replace each ``draw_*`` function with code that reads the
user's real data; do not smooth, fit, subsample or clip it unless the user asked (record it in BRIEF).

    python make_fig3.py --allow-font-fallback --overwrite      # fallback = draft only; Arial is the default
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib

matplotlib.use("Agg")

# ===== EDIT: the figure brief (what the user asked for) ======================================================
BRIEF = {
    "message": "One sentence: what must the reader see?",
    "confirmed": False,                 # set True after the user answered the create_* questions
    "answers_source": "user",           # "user" or "default-unattended"
    "layout": "1 x 3 row, equal panels, letters a-c",
    "requirements": [],                 # e.g. ["x range 0-4 in all panels", "case A is always blue"]
}
# Chinese figure README (<stem>.README.zh-CN.md), sections 4-6. Set "mode" from the user's answer to `readme_sections`:
#   "draft" (default: the agent drafts, marked "待核对")  |  "author" (user writes them)  |  "skip".
# Each item is a string or {"text": ..., "origin": "data" | "user" | "label" | "script" | "suggestion"}. Tag every
# paragraph. Only claims the displayed data support, numbers computed from the data. If the agent has no data or script
# (image only), is unsure, or the data are synthetic: leave the section empty and give the reason in "pending".
INTERPRETATION = {
    "mode": "draft",
    "physical_significance": [],   # e.g. [{"text": "...", "origin": "label"}]
    "results": [],                 # journal-style, observations only: [{"text": "...", "origin": "data"}]
    "discussion": [],              # questions/checks, not conclusions: [{"text": "...", "origin": "suggestion"}]
    "pending": {},                 # e.g. {"results": "only an image was supplied, no data to compute from"}
}
WIDTH = "double"                        # single 89 | one_half 120 | double 183 | slide | poster | mm number
PROFILE = "paper"                       # paper | slide | poster
NROWS, NCOLS = 1, 3
WIDTH_RATIOS = None                     # e.g. [2, 1, 1]
HEIGHT_RATIOS = None                    # e.g. [1, 1.5]
HEIGHT_MM = 52                          # total canvas height in mm (or None and set CELL_ASPECT = h/w of cell 0)
CELL_ASPECT = None
MARGINS_MM = (11.5, 10.5, 3.0, 6.5)     # left, bottom, right, top; widen right for outside colour bars
WGAP_MM, HGAP_MM = 14.5, None           # None = default
PANEL_LETTERS = True
FORMATS = ["pdf", "png", "svg"]
DPI = 600
OUT_STEM = Path("figures_out/custom_layout")   # new files only; use --overwrite to replace your own earlier run
SOURCE_ID = "synthetic placeholder - replace with the data file/path"
# ============================================================================================================


def _find_scivis():
    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        for cand in (p / "scripts", p / "sim-plot" / "scripts", p / "skills" / "sim-plot" / "scripts"):
            if (cand / "scivis").is_dir():
                sys.path.insert(0, str(cand))
                return
    raise SystemExit("scivis not found: keep this file inside the skill kit or add sim-plot/scripts to sys.path")


# ----- panel functions: replace the bodies, keep the (ax, P) signature ------------------------------------
def draw_lines(ax, P):
    x = np.linspace(0, 4, 200)
    for i, st in enumerate(P.redundant_encoding(3)):
        ax.plot(x, np.exp(-x / (1 + i)) * np.cos(2 * x), color=st["color"], ls=st["linestyle"], label=f"case {i + 1}")
    ax.set_xlim(0, 4)
    ax.set_xlabel(r"$x/D$"); ax.set_ylabel(r"$q$")
    ax.legend(loc="upper right")


def draw_scatter(ax, P):
    rng = np.random.default_rng(1)
    t = rng.normal(size=120)
    ax.scatter(t, t + 0.2 * rng.normal(size=120), s=6, color=P.categorical(2)[1])
    ax.set_xlabel(r"$q_\mathrm{ref}$"); ax.set_ylabel(r"$q_\mathrm{pred}$")


def draw_bars(ax, P):
    ax.bar(["A", "B", "C"], [3.1, 2.4, 1.2], color=P.GREY, width=0.6)
    ax.set_ylabel(r"$\Delta p$ (kPa)")


# one entry per panel: grid cell(s) as int or (start, stop) slice, a short title, and the draw function
PANELS = [
    {"row": 0, "col": 0, "title": "Profiles", "draw": draw_lines},
    {"row": 0, "col": 1, "title": "Parity", "draw": draw_scatter},
    {"row": 0, "col": 2, "title": "Pressure drop", "draw": draw_bars},
]


def _cell(v):
    return slice(*v) if isinstance(v, (tuple, list)) else v


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-font-fallback", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--assume-defaults", action="store_true",
                    help="unattended: proceed with BRIEF as written and record that nobody confirmed it")
    a = ap.parse_args()
    if a.assume_defaults and not BRIEF["confirmed"]:
        BRIEF.update(confirmed=True, answers_source="default-unattended")
    if not BRIEF["confirmed"]:
        print("BRIEF NOT CONFIRMED - nothing was rendered.\n" + json.dumps(BRIEF, indent=1, ensure_ascii=False))
        print("Ask the create_* questions (references/create-mode.md), fill BRIEF/WIDTH/NROWS/NCOLS/PANELS, "
              "set confirmed=True and run again.")
        sys.exit(3)
    _find_scivis()
    from scivis import layout, palettes as P
    from scivis.theme import style_context
    from scivis.export import export_figure

    with style_context(PROFILE, allow_font_fallback=True if a.allow_font_fallback else None) as state:
        c = layout.make_canvas(WIDTH, HEIGHT_MM, cell_aspect=CELL_ASPECT, nrows=NROWS, ncols=NCOLS,
                               margins=MARGINS_MM, wgap=WGAP_MM, hgap=HGAP_MM,
                               width_ratios=WIDTH_RATIOS, height_ratios=HEIGHT_RATIOS)
        axes = []
        for p in PANELS:
            ax = c.ax(_cell(p["row"]), _cell(p["col"]))
            p["draw"](ax, P)
            axes.append(ax)
        if PANEL_LETTERS:
            layout.panel_labels(c.fig, axes, titles=[p.get("title", "") for p in PANELS])
        prov = {"source_id": SOURCE_ID, "brief": dict(BRIEF), "interpretation": INTERPRETATION,
                "layout": {"width": WIDTH, "grid": [NROWS, NCOLS], "width_ratios": WIDTH_RATIOS,
                           "height_ratios": HEIGHT_RATIOS, "height_mm": HEIGHT_MM, "margins_mm": list(MARGINS_MM),
                           "panels": [{"row": p["row"], "col": p["col"], "title": p.get("title", "")} for p in PANELS]},
                "transformations": "none in template; list any in BRIEF['requirements']",
                "synthetic": "placeholder" in SOURCE_ID}
        report = export_figure(c.fig, OUT_STEM, state, provenance=prov, formats=FORMATS, dpi=DPI,
                               allow_overwrite=a.overwrite, kind="figure")
    print(json.dumps({"outputs": report["outputs"], "readme_zh": report.get("readme_zh"), "font": report["font_resolved"],
                      "size_mm": report["size_mm"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
