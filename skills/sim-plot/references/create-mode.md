# Create mode: draw a figure to the user's layout and requirements

Use when the user wants a NEW figure ("plot X against Y in three panels", "make a 2 x 2 figure, 183 mm wide,
panel letters, same y range") from data, results or a description. For an existing figure that must keep its
data, use `restyle-mode.md` instead.

The point of this mode: the user's layout and requirements are the specification. Do not substitute a default
figure and mention the difference afterwards.

## Step 1 - read the brief from what the user already said (never ask what they answered)

| Item | Look for | Default if unstated |
|---|---|---|
| Message | what the reader must see (one sentence) | ask |
| Layout | rows x columns, which quantity in which panel, relative widths/heights, insets, panel letters | one panel, or a row if several quantities |
| Size | medium and width (`single` 89 / `one_half` 120 / `double` 183 mm / `slide` / `poster` / a number in mm), height | paper, `single` for one panel, `double` for 3 |
| Encoding | what each colour means (category, ordered parameter, signed deviation, magnitude), fixed colours per case | grey/ink + one accent |
| Hard requirements | axis ranges and scales, units, fixed limits shared across panels, labels (English / CJK), legend placement, annotations, fonts | none |
| Outputs | formats, dpi, output folder | pdf + png + svg, 600 dpi, a NEW folder |
| Data | file, columns, units, which rows | read it; never invent missing definitions |

Look at the data and any existing project script before asking (shape, columns, units, ranges, signed or not).

## Step 2 - ask only what is left, as ONE batch (AskUserQuestion, max 4), recommended answer first

Question ids (skip those already answered; quote what you found so the user can accept in one click):
- `create_layout` - panel arrangement. Options: *the layout you inferred, e.g. 1 x 3 row, equal panels, letters a-c*
  (rec) / *a single panel* / *a grid (rows x columns)* / *custom: describe it* (the user types it).
- `create_size` - medium and canvas. Options: *paper, double column 183 mm* (rec for several panels) /
  *paper, single column 89 mm* / *slide* / *custom width in mm*. Always pdf + png + svg; say the dpi (600).
- `create_encoding` - what colour encodes (only if several series, a scalar, or signed data). Options:
  *categories (Tol bright, max 6, then facet with ghost series)* / *an ordered parameter (sequential map)* /
  *signed deviation (vik, white centre, symmetric limits)* / *no colour meaning (grey + one accent)*.
- `create_requirements` - hard constraints to honour: axis limits/scales, shared ranges, fixed case colours,
  CJK labels, annotations. Options: *none beyond the layout* (rec) / *I will list them* (the user types them).

- `readme_sections` - the Chinese figure README, sections 4-6. Options: *draft them for me, tagged and marked for
  checking* (rec) / *I will write them* / *skip them*. If more than four questions remain, ask this one in a second
  call right after the others; if unattended, use the recommended answer.

Push back once on a risky answer (log axis with zeros, truncated bar axis, more than 6 hues) and say what it costs;
then follow the user's decision and record it. Unattended or "just do it": do not ask; take the recommended answers,
set `answers_source="default-unattended"`, and list the assumptions first in your report.
If the question tool is unavailable, ask in plain text and STOP the turn.

## Step 3 - map the brief to the machinery

| Requirement | How |
|---|---|
| Canvas width / height | `layout.make_canvas(width, height_mm)` (or `cell_aspect=` for equal-aspect fields) |
| Rows x columns, uneven panels | `nrows`, `ncols`, `width_ratios`, `height_ratios`, `wgap`, `hgap`; a panel may span cells with slices |
| Panel letters + titles | `layout.panel_labels(fig, axes, titles=[...])` |
| Margins for outside colour bars | `margins=(left, bottom, right, top)` in mm; `layout.add_colorbar(...)` |
| Fixed axis ranges/ticks/scales | `set_xlim/ylim`, `set_xticks`; log or symlog via `scales.set_symlog` with a recorded reason |
| Colour by role | `palettes.get_cmap("magnitude"|"signed"|...)`, `P.categorical(n)`, `P.redundant_encoding(n)` (colour + line style) |
| Too many cases | facet with ghost series (`layout.small_multiples`), not more hues |
| Inset / zoom | `layout.zoom_inset` |
| Marginals, density scatter | `layout.marginal_canvas`, `layout.density_scatter` |
| Physical field panels | `sim-field` (`render_field.py`, `recipes/cfd_field_panels.py`) |

Route, in this order of preference:
1. The layout is one of the supported kinds and one panel -> `render_plot.py` / `render_field.py` with a JSON config.
2. A recipe is close -> copy it and replace only the data function.
3. Anything else (the usual case for a specified layout) -> copy
   `recipes/custom_layout_template.py` into the USER's project, set the EDIT block (`BRIEF`, `WIDTH`,
   `NROWS/NCOLS`, ratios, `PANELS`) and replace the placeholder `draw_*` functions with real data code.
   It refuses to render until `BRIEF["confirmed"]` is True (`--assume-defaults` for unattended runs), runs the QA
   gate, and writes the brief and layout into `.viz.json`.
For configs of the first two routes, put the brief in the config as `"brief": {...}`; the config is copied into the
sidecar.

## Step 4 - render once, review, finish

Render, run the QA gate, look at the PNG at final size, fix a demonstrated problem in the same source, stop.
Check every hard requirement against the picture (ranges, letters, colours, widths) and say which ones were met.
Finish the caption stub and, per the answer to `readme_sections`, sections 4-6 of the Chinese figure README
(`<stem>.README.zh-CN.md`: physical significance, journal-style preliminary results, discussion directions, each
paragraph tagged by origin; see SKILL.md). Do not rerun data reduction because a font or colour changed, and do not write extra
variants, smoke-test projects or copied per-case scripts.
