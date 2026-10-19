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

### Tooling
- 57 tests, `verify.py`, `install.py` (dry run by default), `export_mplstyle.py`, `export_lut.py`, rendered previews.
