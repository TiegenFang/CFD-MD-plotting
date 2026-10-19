#!/usr/bin/env python
"""RESTYLE TEMPLATE B  (sim-field / sim-plot): re-present an existing matplotlib figure.

Copy this file INTO THE USER'S PROJECT (e.g. results/figures/restyle_<name>.py) and edit only
the EDIT block. Never edit the skill's copy and never paste rcParams here.

What it does
  1. runs the user's ORIGINAL plotting script with savefig blocked (the original PNG/SVG is
     never overwritten) and captures the figure it would have saved;
  2. harvests every artist as data: arrays, coordinates, colour map, norm, extend,
     interpolation, limits, labels, contour geometry, annotation text;
  3. rebuilds the panel on a mm-exact scivis canvas: fonts, frame, ticks, colour bar, line widths;
  4. compares the harvested frozen layer of old and new figure. Any difference stops the export.

FROZEN (never changed unless the user opted in, listed in OPT_IN):
  values, smoothing, interpolation, colour limits, extend, colour map, axis limits, units, text.
PRESENTATION (changed freely): size, fonts, frame, ticks, colour-bar geometry, halos, formats.

Run:  python restyle_<name>.py [--allow-font-fallback] [--overwrite]
"""
import argparse
import json
import runpy
import sys
from pathlib import Path

# ============================== EDIT ==========================================
ORIGINAL_SCRIPT = Path(r"examples/original_rz_charge.py")   # the user's plotting script
ORIGINAL_ARGV = []                                           # its command-line arguments
FIGURE_INDEX = -1                                            # which saved figure (last by default)
OUT_STEM = Path("restyle_out/rz_charge_restyled")            # new files only; never the original path
SOURCE_ID = "synthetic demo"                                 # data identity for the provenance
WIDTH = "single"                      # single 89 | one_half 120 | double 183 | slide | poster | mm
PROFILE = "paper"                     # paper | slide | poster
FORMATS = ["pdf", "png", "svg"]
# Anything listed here is CHANGED ON PURPOSE (ask the user first, then record it):
OPT_IN = {
    # Standing decision (user, 2026-10-19): signed fields use vik with a white centre. "signed-if-diverging"
    # swaps ONLY diverging maps (RdBu_r, coolwarm, bwr...) for vik and leaves sequential maps untouched.
    # None keeps the original map; any other name is a one-off request.
    "cmap": "signed-if-diverging",
    "labels": {},                     # e.g. {"xlabel": "$r$ (Å)", "ylabel": "$z_{rel}$ (Å)",
                                      #       "cbar": "$\\rho_q$ (e nm$^{-3}$)"}  typography only
    "keep_ticks": False,              # True keeps the original tick values
}
# ---- INTAKE CONTRACT -------------------------------------------------------------------------------
# The script refuses to render until this is confirmed. First run (confirmed=False) only PRINTS what the original
# does; quote those facts in the questions you ask the user (restyle-mode.md, Step 2). Set confirmed=True and fill
# the answers ONLY after the user answered, or after they said "just do it". `--assume-defaults` is for unattended
# runs and is recorded in the sidecar as such.
CONTRACT = {
    "confirmed": False,
    "answers_source": "",                    # "user" | "default-unattended"
    "improve": "typography+layout",          # typography+layout | +colour | +annotations | +other medium
    "keep_frozen": True,                     # smoothing, limits, units, interpolation stay as in the original
    "target": "paper, single column",
}
CBAR_SIDE = "right"
MAX_PANEL_HEIGHT_MM = None   # None: 80 mm paper / 110 slide / 200 poster. Tall panels become NARROW
                             # figures (the type stays 7 pt, so it keeps the original's proportions).
# ==============================================================================


def _find_scivis():
    here = Path(__file__).resolve()
    cands = [Path(p) for p in __import__("os").environ.get("SCIVIS_PATH", "").split(__import__("os").pathsep) if p]
    for base in (here.parents[2], Path.home() / ".agents" / "skills", Path.home() / ".omp" / "agent" / "skills",
                 Path.home() / ".claude" / "skills"):
        cands.append(base / "sim-plot" / "scripts")
        cands.append(base / "skills" / "sim-plot" / "scripts")
    for c in cands:
        if (c / "scivis" / "__init__.py").is_file():
            sys.path.insert(0, str(c))
            return c
    raise SystemExit("scivis not found. Install sim-plot next to sim-field or set SCIVIS_PATH.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-font-fallback", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--assume-defaults", action="store_true",
                    help="unattended: proceed with the defaults and record that nobody confirmed them")
    a = ap.parse_args()
    if a.assume_defaults and not CONTRACT["confirmed"]:
        CONTRACT.update(confirmed=True, answers_source="default-unattended")
    _find_scivis()
    import hashlib
    from scivis import layout, restyle
    from scivis.theme import style_context
    from scivis.export import export_figure

    # 1 -- run the original, never let it write its files
    saved_argv = sys.argv
    sys.argv = [str(ORIGINAL_SCRIPT)] + list(ORIGINAL_ARGV)
    try:
        with restyle.intercept_savefig() as got:
            runpy.run_path(str(ORIGINAL_SCRIPT), run_name="__main__")
    finally:
        sys.argv = saved_argv
    if not got.figs:
        raise SystemExit("The original script never called savefig; point ORIGINAL_SCRIPT at the plotting code "
                         "or use restyle_field_template.py (FROZEN-block route).")
    old = got.figs[FIGURE_INDEX]
    specs = restyle.harvest(old)
    if any(s.unsupported for s in specs):
        raise SystemExit("Unsupported artists: " + "; ".join(u for s in specs for u in s.unsupported)
                         + "\nUse restyle_field_template.py and paste the original data code verbatim.")

    # 1b -- intake gate: show what the original does, then stop until the user has confirmed the plan
    facts = restyle.describe(specs, old)
    if not CONTRACT["confirmed"]:
        print("INTAKE NOT CONFIRMED - nothing was rendered. The original does this:")
        print(json.dumps(facts, indent=1, default=str))
        print("Planned OPT_IN changes:", json.dumps(OPT_IN, default=str))
        print("Ask the user (AskUserQuestion; one batch, each with a recommended answer), then set CONTRACT "
              "confirmed=True/answers_source='user' and run again.")
        sys.exit(3)

    # 2 -- rebuild on the scivis canvas (one row of panels, same data windows)
    n = len(specs)
    with style_context(PROFILE, allow_font_fallback=True if a.allow_font_fallback else None) as state:
        k = state["base"] / 7.0
        right = 15.0 * k if CBAR_SIDE == "right" else 3.0 * k   # 15 mm leaves room for a rotated long colour-bar label
        margins = (11.5 * k, 9.0 * k, right, 6.0 * k)
        aspect = restyle.panel_aspect(specs[0])
        width = layout.fit_width(WIDTH, aspect, margins, MAX_PANEL_HEIGHT_MM) if n == 1 else WIDTH
        c = layout.make_canvas(width, cell_aspect=aspect, ncols=n, margins=margins)
        new_axes, changes = [], []
        for i, sp in enumerate(specs):
            ax = c.ax(0, i, field=True)
            r = restyle.replay(sp, ax, cmap=OPT_IN["cmap"], keep_ticks=OPT_IN["keep_ticks"],
                               labels=OPT_IN["labels"], cbar_kw={"loc": CBAR_SIDE})
            changes += r["changes"]
            new_axes.append(ax)
        if n > 1:
            layout.panel_labels(c.fig, new_axes)

        # 3 -- frozen-layer audit: old figure vs new figure, same harvester on both
        allow = tuple(k for k, v in (("cmap", OPT_IN["cmap"]), ("xlabel", OPT_IN["labels"].get("xlabel")),
                                     ("ylabel", OPT_IN["labels"].get("ylabel")),
                                     ("colorbar", OPT_IN["labels"].get("cbar"))) if v)
        diffs = restyle.compare(specs, restyle.harvest(c.fig), allow=allow)
        if diffs:
            raise SystemExit("FROZEN LAYER CHANGED - not exporting:\n  " + "\n  ".join(diffs))

        prov = {"source_id": SOURCE_ID,
                "restyle": {"mode": "harvest", "original_script": str(ORIGINAL_SCRIPT),
                            "original_sha256": hashlib.sha256(Path(ORIGINAL_SCRIPT).read_bytes()).hexdigest(),
                            "frozen": list(restyle.FROZEN), "presentation": list(restyle.PRESENTATION),
                            "opt_in_changes": changes or None, "frozen_layer_identical": True,
                            "intake": dict(CONTRACT), "original_facts": json.loads(json.dumps(facts, default=str)),
                            "fingerprint": json.loads(json.dumps(restyle.fingerprint(specs), default=str)),
                            "original_files_written": False}}
        rep = export_figure(c.fig, OUT_STEM, state, provenance=prov, formats=FORMATS,
                            allow_overwrite=a.overwrite, kind="field")
    review = restyle.side_by_side(old, c.fig, str(OUT_STEM) + ".before_after.png")
    print(json.dumps({"outputs": rep["outputs"], "review": str(review), "opt_in_changes": changes,
                      "frozen_layer_identical": True}, indent=1))


if __name__ == "__main__":
    main()
