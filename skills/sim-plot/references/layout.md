# Layout and typography: Rougier mapping

Primary benchmark: N. P. Rougier, *Scientific Visualization: Python + Matplotlib* (open access; source: github.com/rougier/scientific-visualization-book). What follows is taken from the book's own chapter sources (rules, defaults/style file, layout, typography) and the code under `code/layout`, `code/defaults`; the implementation lives in `scivis/theme.py` and `scivis/layout.py`.

## Rules -> mechanism

| Book | Statement (paraphrased) | Here |
|---|---|---|
| Rule 1-2 | know the audience, state the message first | workflow step 1 |
| Rule 3 | adapt the figure to the medium: thicker lines, fewer ticks, bigger text for talks | `apply_style("paper"/"slide"/"poster")` changes size, line width, minor ticks |
| Rule 4 | captions are not optional | figures carry no big titles; the caption explains clipping percentiles, synthetic data, etc. |
| Rule 5 | do not trust defaults | custom rcParams: spines, outward ticks, fonts, cycle |
| Rule 6 | use colour effectively; if no reason, keep it black | `INK/GREY` neutrals, `highlight()`, role-based maps |
| Rule 7 | do not mislead: area not radius, full ranges | `area_sizes`, `diverging_norm`, honest baselines |
| Rule 8 | avoid chartjunk: few ticks, no gratuitous grid (the book also prefers direct labels and open axes) | 3-4 ticks, pale or no grid. **Project override:** boxed axes and a framed legend are the default (`boxed`, `legend_box` in `apply_style`); `end_labels`/`range_frame` stay available |
| Rule 9 | message trumps beauty | QA before polish |
| Defaults style file | spines top/right off, outward ticks with minor ticks, line width 1-2, condensed sans | `scivis.theme.apply_style` (sizes scaled to the medium); **overridden here**: Arial, four spines, inward mirrored ticks |
| Layout chapter | prefer GridSpec with ratios; give titles/labels their own cells so panels keep equal size; colour bar width a fraction of the main axes; aligned marginal histograms | `make_canvas` (mm margins, gaps, ratios), `add_colorbar` outside the cell, `scatter_parity.py` |
| Typography chapter | one family across the figure; sizes are physical; choose a stack matching the journal; outline text over images instead of boxing it | Arial default (`journal`), Roboto Condensed opt-in (`rougier`), mm canvases, `halo`, `halo_clabel` |

## Canvas contract

- Width presets (mm): single 89, one_half 120, double 183, slide 254, poster 400. Override with a number; match your journal's template.
- `make_canvas(..., margins=(l, b, r, t), hgap, wgap)` in mm. Defaults (paper): 11.5 / 9 / 3 / 6, gaps 11-12 mm. Typical needs: colour bar to the right +8.5 mm; end labels +10 mm; range_frame offsets the spines 2.5 pt outward.
- `cell_aspect` derives the canvas height for equal-aspect fields so panels never get white bands.
- Save at exact size: PDF (vector text, TrueType embedded) + PNG at 300 dpi; no `bbox_inches="tight"`.

## Type hierarchy (paper, pt)

panel letter 9 bold | title 7 | axis label 7 | tick 6.5 | legend 6.5 | annotation 6. Floor enforced by `qa`: 5 pt (paper), 10 (slide), 14 (poster).

## Panel furniture rules

- Panel letters share a left edge per column (aligned to the widest y-axis furniture); titles start at the axes' left edge on the same baseline; if no y-furniture exists the title is indented past the letter.
- Colour bar label is horizontal above a vertical bar (no rotated text) and clears the extend arrow.
- Inner panels in a row hide y tick labels (`field_axes(outer_y=False)`).
- Every axes (curves, scatter, fields, marginals) carries all four spines; fields use a slightly thinner frame (`field_axes`).

## Fonts

Default: **Arial** (`font="journal"`), with Helvetica, then metric-compatible Liberation Sans / Nimbus Sans, then bundled Roboto, then DejaVu. `font="rougier"` selects Roboto Condensed (the book's choice, bundled, Apache-2.0). Math uses the same family via mathtext `custom` with a STIX-sans fallback for symbols. When Arial itself is missing, `apply_style` warns and `qa` prints a NOTE naming the substitute; a non-metric-compatible fallback is reported as a QA issue.

## Standard layouts from the book, as code

| Layout | Function |
| --- | --- |
| image + colour bar of equal height | `add_colorbar` (inset outside the cell) with `field_axes` / `cell_aspect` |
| scatter + aligned marginals | `layout.marginal_canvas`, `density_scatter` |
| small multiples with ghost series | `layout.small_multiples` |
| zoom annotation with connectors | `layout.zoom_inset` (same cmap/norm; place in empty space) |
| titles/letters in their own cell | `panel_labels` (outside the axes cell) |

## Output hygiene

`make_canvas` returns a detached `Figure` (no pyplot registry); `save` never uses `bbox_inches="tight"`
and warns when a vector file exceeds `export.pdf_size_warn_mb` (rasterize dense layers). Styles are
applied through `style_context` / `apply_style` without resetting unrelated rcParams;
`assets/styles/*.mplstyle` are generated from `theme.json` for plain `plt.style.use`.
