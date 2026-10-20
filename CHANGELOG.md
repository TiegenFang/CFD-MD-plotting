# Changelog

## 1.0.0

First public release of the two skills with a shared styling, colour and layout layer.

### Shared layer (`skills/sim-plot/scripts/scivis`)
- One `theme.json` is the source of truth; `.mplstyle` files are generated from it and checked by tests.
- Role-based colour (Crameri + Paul Tol), archived and hash-checked oslo/vik tables, CAM02-UCS audit, Lab ramps, colour
  stacks, guards for constant, empty or NaN colour ranges, clipped-fraction statistics.
- Millimetre-exact canvases, boxed axes, framed legends, panel labels, outside colour bars (adaptive thickness; long
  labels placed beside the bar), `fit_width` for tall panels.
- Ghost small multiples, zoom insets, marginal scatter, density scatter, haloed contour labels, symlog with slope guides.
- QA on export (clipping, tiny text, colour-bar label, font, CJK in math, canvas width, legend over data), `.viz.json`
  provenance and a caption stub for every figure. Fonts are strict Arial unless a fallback is authorised and recorded.
- OpenFOAM readers for `postProcessing` `.dat` files and log residuals.

### Skills
- `sim-plot`: `render_plot.py` (line, scatter, bar, multiples), recipes for monitors, MD panels, parity plots, ghost
  multiples and slide adaptation, references (visual system, layout, colour decision, rules-to-checks, data contracts).
- `sim-field`: `render_field.py` (rectilinear and triangular fields, streamlines, zoom, boundary overlays), recipes for
  field panels and wake zoom, references for CFD, MD and ParaView routes.
- Restyle mode for existing figures: `scivis.restyle` (run the original code with saving blocked, harvest artists,
  replay on the shared layout, audit the frozen layer), two templates, an intake gate with recorded answers, and the
  protocol in `restyle-mode.md`. Standing decision: signed fields use vik with a white centre.
- Harvest template options: `SIZE_MODE` (compact / strict-89 / presentation), `DPI` (600), `FRAMES` (batch of existing
  figures into a new directory), opt-in `vlim` colour range (recorded, audited). Intake questions `restyle_scope`,
  `restyle_size`, `restyle_frames`.

- Create mode for figures to the user's own layout and requirements: `references/create-mode.md` (brief, questions
  `create_layout` / `create_size` / `create_encoding` / `create_requirements`, requirement-to-API table) and
  `recipes/custom_layout_template.py` (any grid, ratios, spanning cells, panel letters; brief gate; brief and layout
  recorded in `.viz.json`).
- Calling rules now live in each `SKILL.md`; `AGENTS.snippet.md` was removed.

### Tooling
- 57 tests, `verify.py`, `install.py` (dry run by default), `export_mplstyle.py`, `export_lut.py`, rendered previews.
