---
name: sim-plot
description: >-
  Create figures to the user's own layout and requirements (panel grid, size in mm, colour roles, axis ranges, labels), or restyle an existing figure without changing its data, for quantitative CFD/MD results: 折线、散点、工况对比、柱状、误差带、小多图、RDF/MSD curves, residual/force monitors, parity plots; also the shared style, colour and layout layer (scivis) used by sim-field. Scientific colours, Arial/math labels, mm-exact multi-panel layout. Trigger on an explicit plotting, layout, restyling (enhance/beautify/重绘) or figure-review task. Do not trigger on scientific discussion, simulation debugging, solver setup, trajectory reduction, physical-field contours or molecular snapshot rendering. Route fields and trajectories to sim-field.
---

# Simulation quantitative plotting + shared style layer

## When to use this skill (calling rules)

Use `sim-plot` for requested line / scatter / bar / condition-comparison / small-multiples figures, residual and
force monitors, parity plots, a custom multi-panel layout the user specifies, or restyling of already-computed CFD/MD
curves. Use `sim-field` for physical fields, contours, streamlines, mesh-aware slices, MD density construction or
explicitly requested molecular snapshots. Pure scientific discussion, solver debugging and simulation setup trigger
neither. A field panel plus a quantitative plot may use the two routes in sequence; do not duplicate their analysis.

- Load only the relevant skill and its on-demand reference. `sim-plot` owns `scivis`; `sim-field` imports it.
- Before code: state the message and the medium (paper / slide / poster), and say what each colour encodes.
- Reuse the shared style and an existing script, recipe or template; never paste rcParams or layout code into a
  figure script.
- For these tasks the sim-plot / sim-field visual rules take precedence over a generic Nature or visualization skill.
  Run a journal-specific audit only when submission checking is requested; do not load competing style guides.
- Keep data reduction separate from visual edits; do not rerun trajectories or CFD because a colour or font changed.
- One focused render review (the `qa` gate plus a look at the PNG), fix observed issues in the same source, finish the
  caption stub, stop. No redundant smoke tests, copied plotting scripts, per-case forks or leftover validation files.

## Two modes: pick one first

| The user has... | Mode | Read |
|---|---|---|
| data/results and a figure to make, with or without a specified layout | **Create** | `references/create-mode.md` |
| an existing figure ("enhance / beautify / restyle my plot", 美化已有图) whose data must not change | **Restyle** | `references/restyle-mode.md` |

**Create mode:** the user's layout and requirements are the specification. Read what they already gave you (layout,
size, colour meaning, ranges), ask at most four questions about what is missing in one batch with a recommended
answer each (`create_layout`, `create_size`, `create_encoding`, `create_requirements`), then render through
`render_plot.py`, a recipe, or `recipes/custom_layout_template.py` (any rows x columns, ratios, panel letters).
The brief is recorded in `.viz.json`.

**Restyle mode:** find the original plotting code yourself; ask at most four questions, only about what you could not
find (`restyle_scope`, `restyle_size`, `restyle_frames`). Data, smoothing, interpolation, colour limits, extend, colour
map, axis limits and units are frozen; only presentation changes (`scivis.restyle`). Use the restyle templates in
the user's project, not `render_field.py`/`render_plot.py`. Never overwrite the original figure, data or script.

## Scope and precedence

Render already-defined quantitative data. This is not a solver, statistical-analysis
or research-criticism skill. Current user instructions and project figure rules take
precedence over defaults. Do not replace an existing verified plotting backend just
for style. Python/Matplotlib is the default only when no workflow is established.

This skill owns **scivis**, the colour / typography / layout layer for the whole kit
(`scripts/scivis/`, theme in `assets/theme.json`). `sim-field` imports it. Never copy
rcParams or helpers into a figure script; import `scivis`.

## What to read (narrowly)

1. `references/rules-to-checks.md` once: the ten decisions that precede any code.
2. `references/visual-system.md` for fonts, sizes and colour semantics.
3. Only as needed: `chart-rules.md` (the requested chart), `data-contracts.md`
   (CSV columns, uncertainty), `colormap-decision.md` (picking a map),
   `recipes.md` (multi-panel figures), `layout.md` (canvas contract).

## Workflow

1. **Message and medium (before code).** One sentence: what must the reader see?
   Medium: `paper` (default) / `slide` / `poster`. A slide is rebuilt, not scaled.
2. Inspect supplied data/code and project style. Reuse earlier decisions.
3. Resolve quantity, units, sampling/replication, missing values. Unknown statistical
   definitions are not permission to invent uncertainty.
4. **Colour only with a reason.** Say what each colour encodes: category, ordered
   parameter, signed deviation, magnitude. If nothing, use ink/grey plus one accent
   (`palettes.highlight`). Persistent species/case registries win over palettes.
5. Pick the nearest route:
   - tidy CSV line / scatter / bar / small-multiples -> `scripts/render_plot.py CONFIG.json`
   - a specified multi-panel layout -> `recipes/custom_layout_template.py` (grid, ratios, letters, brief)
   - a near-match multi-panel figure -> copy the nearest file in `recipes/`, replace only
     the data function (never write layout from scratch)
6. Render once, inspect at final physical size (`layout.qa` gate + look at the PNG),
   fix a demonstrated problem in the same source, stop.
7. Keep the caption stub (`<stem>.caption.txt`, written on export) and finish it:
   it is half the figure.

## House style (defaults live in `assets/theme.json`)

- Arial; 7 pt hierarchy for paper: panel letter 9 bold > title 7 > label 7 = tick 6.5 > legend 6.5.
- Boxed axes (four spines, inward mirrored ticks, labels left/bottom), **framed legend**
  in empty data space. Direct end labels and open axes are opt-in
  (`layout.end_labels`, `apply_style(boxed=False, legend_box=False)`).
- Colour by role: `get_cmap("magnitude"|"positive"|"temperature"|"density"|"error"|"signed"|"phase")`
  (cmcrameri; diverging maps get a pure-white centre). Categorical default is Paul Tol
  `tol-bright` (max 6, grey reserved). The soft `muted` / `cool` / `earth` / `okabe-ito`
  families remain available by name. Never jet / rainbow / turbo / hsv / brand palettes.
- Canvases are built at final size in mm (`single` 89, `one_half` 120, `double` 183) and
  saved without `bbox_inches="tight"`. Titles, panel letters and colour bars live outside
  the axes cell so panels stay equal.
- Too many cases for the palette (cap 6)? **Facet with ghost series**
  (`layout.small_multiples`, or `kind: "multiples"`), do not add hues.
- Dense scatter: `density_scatter` / hexbin, not alpha stacking (alpha floor 0.01).
- Signed or multi-decade data: `scales.set_symlog` with a recorded `linthresh` reason;
  scaling-law guides with `scales.slope_guide`; bars never on log axes.

## Fonts

Missing Arial stops final rendering. A draft may pass `--allow-font-fallback` (or set
`SCIVIS_ALLOW_FONT_FALLBACK=1`): the metric-compatible Liberation Sans/Arimo keeps the
layout identical and the fallback is recorded in the sidecar. No Arial file is bundled.
Optional `font="rougier"` selects bundled Roboto Condensed. Chinese labels: `cjk=True`,
and keep Chinese text and `$math$` in separate strings (QA flags the mix).

## Integrity rules (unchanged)

No automatic smoothing, fitting, outlier removal, subsampling, aggregation, sorting,
uncertainty estimation or gap interpolation. Marker thinning changes markers only.
Rasterization changes rendering, not data. Point/interval plots instead of truncated
or log bars. Clipping percentiles, limits, synthetic flags go to the caption.

## API cheat sheet

```python
import sys; sys.path.insert(0, "<skill>/scripts")
from scivis import style, layout, scales, palettes as P
style.apply_style("paper")                       # or: with scivis.style_context("paper") as st:
c = layout.make_canvas("double", 52, ncols=3)    # mm-exact; cell_aspect= for equal-aspect fields
ax = c.ax(0, 0)
ax.plot(x, y, label="case"); ax.legend(loc="upper right")
layout.panel_labels(c.fig, c.axes, titles=["a title"])
layout.qa(c.fig); c.save("out/figure")           # PDF + PNG at the exact size
```

Legacy `from simviz import ...` still works (compat facade over scivis).

## Delivery and stop rule

Default outputs: PDF, SVG, PNG, one `.viz.json` provenance record, one `.caption.txt`.
Export raises on clipped text/legend, unlabeled colour bars, sub-minimum fonts, CJK inside
math, a non-metric font. Overlap and legend-over-data findings go to the sidecar: review them.
The helper checks canvas text, not physical validity or journal compliance.
Do not spawn plan/critic subagents or TODO lists for a small cosmetic edit; run focused
tests only after changing shared logic (`python verify.py`, `python -m pytest tests -q`).
Keep installation files unchanged unless the user explicitly asks to update the skill.

## Field routing

Physical-field contours, slices, native mesh rendering, MD density construction and
particle snapshots use `../sim-field/SKILL.md`. A previously computed 1D profile or
RDF/MSD curve comes here; a scalar-coloured scatter stays here unless it reconstructs a field.
