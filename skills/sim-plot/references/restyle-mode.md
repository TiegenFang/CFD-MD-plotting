# Restyle mode: "enhance my figure"

Applies to sim-field AND sim-plot whenever the user already has a figure ("enhance / beautify / restyle /
polish / make publication-ready my ... plot", 美化、优化、重绘已有图). It is the DEFAULT whenever an
existing figure or its plotting code is mentioned. New figures from raw data use `render_field.py` /
`render_plot.py`; restyle mode never does.

## The one rule
Change how the figure looks, never what it shows.

| FROZEN (copy exactly, report as unchanged) | PRESENTATION (replace) |
|---|---|
| array values, masks, coordinates, units | canvas size, margins, aspect box |
| smoothing (e.g. Gaussian sigma), upsampling, interpolation | font family and sizes, math typesetting of the same label |
| colour limits (also percentile rules), norm, centre, extend arrows | frame, tick style and density |
| colour map | colour-bar geometry and label placement |
| axis limits, scales | line widths, halos, marker sizes |
| contour/boundary geometry, annotation text and position | formats, dpi, file names |

Why: display choices such as "97.5th pooled percentile limits + extend both + sigma 0.8 smoothing" are
the author's scientific presentation decisions (often shared across 30 comparable frames). Re-deriving
them from raw data, widening the scale to the data min/max or converting units makes the picture
different, usually worse, and silently incomparable with the other figures of the paper.
The "no smoothing, no clipping" rules of the visual system govern NEW figures; in restyle mode they are
**disclosed, not overridden**: write the author's smoothing/limits/clipping into the caption and the
`.viz.json` and flag them in the report; change them only if the user explicitly asks.

Opt-in changes (ask first, record each in `restyle.opt_in_changes`): colour map, unit conversion
(Å -> nm), different limits, removing smoothing, adding insets/streamlines, new annotations.

## Step 1 - find the original (do not ask if you can look)
1. The figure the user named or attached; its neighbours: `*.viz.json`, `figure_manifest.json`,
   `*.caption*`, `source_record` entries (they often list data files, `display_smoothing`,
   `color_limits`, `colormap`).
2. Search the project for the plotting code: `grep -rl "<figure basename>\|<metric folder name>" --include=*.py`;
   look in `scripts/`, `plot*/`, notebooks, `git log -- <figure path>`.
3. Open the candidate and confirm it produces THIS figure (same file name pattern, same labels).
   Rank candidates; several or none -> Step 2.

## Step 2 - intake gate (a short grilling, mandatory, before any rendering)
"Ask if unsure" was skipped in practice, so this is a gate, not advice: the templates refuse to render while
`CONTRACT["confirmed"]` is False. Do it in this order.

1. **Look first.** Run the template once unconfirmed. It prints what the ORIGINAL really does (colour map, limits,
   extend, fraction of cells beyond the limits, smoothing/interpolation, shape, labels, original size). Everything
   you can read, you do not ask. Never ask what the code or manifest already answers.
2. **Ask what is left, as ONE batch (AskUserQuestion, max 4), each with your recommended answer first**, quoting the
   detected facts so the user can say yes in one click. Use these question ids; skip any the user already answered:
   - `restyle_scope` - what may change. Options: *vik with white centre + layout* (rec; frozen layer stays,
     only signed diverging maps are swapped) / *layout only* (keep the original colour map) / *also adjust display
     parameters* (user names them, e.g. colour range `OPT_IN["vlim"]`; warn what share of cells it clips).
     Name each frozen item with its real value (smoothing, limits, extend, units).
   - `restyle_size` - canvas, always pdf + 600 dpi png + svg. Options: *compact paper figure* (rec;
     `SIZE_MODE="compact"`, panel <= 80 mm tall) / *strict 89 mm wide* (`"strict-89"`) / *presentation figure*
     (`"presentation"`, 160 mm wide, panel <= 110 mm tall).
   - `restyle_frames` - how many figures. Options: *one representative frame* (rec) / *all existing frames*
     (`FRAMES` = one entry per frame with its own argv; outputs go to a NEW directory, `OUT_DIR`).
   - Only if unresolved: *Original* ("Is `<script>` the code that produced this figure?").
3. **Push back once on a risky answer** (e.g. "make the scale tighter" -> say what percentage gets clipped and
   what that hides), then follow the user's decision.
4. **Record it**: set `CONTRACT` (`confirmed=True`, `answers_source="user"`, the answers). It is written into
   `.viz.json` next to the original facts, so a skipped Q&A is visible afterwards.
5. **Unattended / "just do it"**: do not ask; run with `--assume-defaults` (recorded as `default-unattended`),
   and put the assumptions in the first lines of your report.
If the question tool is unavailable, ask in plain text and STOP the turn; do not continue on a guess.

## Step 3 - choose the route
- **Template B** `sim-field/templates/restyle_harvest_template.py`: the original is runnable matplotlib.
  The template runs it with `savefig` blocked, harvests the artists and replays them; it refuses to export if
  the frozen layer differs. Preferred.
- **Template A** `sim-field/templates/restyle_field_template.py`: paste the original data code verbatim in the
  FROZEN block (not runnable as-is, not matplotlib, filled contours, writes other files, needs cluster paths).
Copy the template into the USER's project (e.g. `results/figures/`), never edit the skill's copy, never write
over the original figure/data/script. Reuse one restyle script per figure family; do not fork per case.

## Step 4 - deliver
- new files only: figure (pdf/png/svg), `.viz.json` (contains the frozen fingerprint and the audit result),
  `.caption.txt` (complete it; mention smoothing/limits/clipping that the original used), `.before_after.png`.
- report: what changed (presentation list), what was kept (frozen list with the actual values: vmin/vmax,
  extend, sigma, interpolation, cmap), opt-in changes, what could not be verified.
- then, separately and clearly labelled, optional suggestions the user may adopt later (e.g. SymLog, a
  diverging map about a stated reference, density-of-evidence shading, shared limits across frames,
  more informative contour). Suggestions are never applied silently.

## Checks that must pass
`restyle.compare(harvest(old), harvest(new)) == []`, `layout.qa` clean, original files untouched
(hashes before/after), font = Arial (or the recorded fallback).

## Standing decisions (user, 2026-10-19; apply unless the user says otherwise)
- Signed / diverging fields: **vik with a white centre** (`cmap="signed"`). In restyle mode this is a standing
  opt-in: the harvest template uses `"signed-if-diverging"`, which swaps only diverging maps (RdBu_r, coolwarm,
  bwr...) for vik and leaves sequential maps and rainbow maps alone. Record the swap in the report.
- Percentile colour limits (e.g. pooled 97.5th) and extend arrows are a **clarity aid, not a policy**. Keep the
  original limits when restyling; state them (value, percentile, clipped fraction) in the caption and sidecar. If
  clipping hides structure that matters, say so as a suggestion - do not change it silently.
- Display-only smoothing / bilinear upsampling is **cosmetic**. Keep it, label it "display only" in the caption,
  and never use the smoothed array for numbers. A raw-cell version is an optional extra, only when asked.
- Colour: cmcrameri for sequential/diverging, Paul Tol for categories; Arial; boxed axes (unchanged).
