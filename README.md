# CFD-MD-plotting

**English** | [简体中文](README.zh-CN.md)

Publication-quality figures for CFD and molecular-dynamics results, as two cooperating agent skills that share one
colour, typography and layout system.

| Skill | Use it for |
|---|---|
| [`sim-plot`](skills/sim-plot) | Line, scatter, bar, condition comparison, small multiples, residual and force monitors, parity plots. Hosts the shared `scivis` layer. |
| [`sim-field`](skills/sim-field) | Physical fields: contours, streamlines, slices, mesh-aware fields, MD density and charge maps. Imports `scivis` from `sim-plot`. |

Both skills have two modes:

- **Create** a figure from prepared data **to your layout and requirements** (panel grid, size in mm, colour roles, axis
  ranges, labels): `render_plot.py`, `render_field.py`, recipes, or the custom-layout template. See [Create mode](#create-mode).
- **Restyle** a figure you already have ("enhance my plot"): the data layer is frozen and audited, only the
  presentation changes. See [Restyle mode](#restyle-mode) and [Usage workflows](#usage-workflows).

## What you get

- **Layout in millimetres.** Figures are built at their final size (89 / 120 / 183 mm for paper, slide and poster
  profiles). Field panels follow the physical aspect ratio; tall panels become narrow figures instead of stretched ones.
- **Typography.** Arial by default, a fixed size hierarchy per medium, mathtext, optional CJK labels. A fallback font is
  used only when explicitly authorised and is recorded.
- **Colour by role.** Crameri maps for sequential and diverging data (batlow, vik with a white centre, lajolla, oslo,
  bilbao, romaO), Paul Tol sets for categories, a CAM02-UCS audit, guards against constant or NaN colour ranges.
- **Boxed axes, framed legends, outside colour bars** with an automatic label placement for long labels.
- **Recipes:** CFD monitors, MD line panels, parity plots with marginals, ghost small multiples, slide adaptation,
  field panels with streamlines, wake zoom insets.
- **QA gate on export.** Clipped text, tiny fonts, unlabeled colour bars, font substitution, CJK inside math and
  wrong canvas width block the export. Every figure also gets a `.viz.json` provenance file and a caption stub.
- **A Chinese README for every figure** (`<stem>.README.zh-CN.md`): axes, legend, figure type, colour meaning, processing, and
  the physical significance, journal-style preliminary results and discussion directions. See [Figure README](#figure-readme-chinese).
- **OpenFOAM helpers:** hardened `postProcessing` `.dat` reader and log residual reader.

## Install

Copy the two folders into the skills directory of your agent, keeping them side by side:

```
<skills dir>/
├── sim-plot/
└── sim-field/
```

`python install.py --target codex|claude|omp --scope user` does this for you (dry run by default, add `--apply`).
Then `pip install -r requirements.txt` (numpy, matplotlib, cmcrameri; tol-colors and colorspacious are optional).
Arial is not bundled; install it, or pass `--allow-font-fallback` for draft output.
No `AGENTS.md` changes are needed: each `SKILL.md` carries its own calling rules (when to use it, when not to, which mode).

## Quick start

```bash
python skills/sim-plot/scripts/render_plot.py examples/line.json --out out/line
python skills/sim-field/scripts/render_field.py examples/field_wake.json --overwrite
python -m pytest tests -q          # 64 tests
python verify.py                   # end-to-end check (run without SCIVIS_ALLOW_FONT_FALLBACK)
```

Previews of every example and recipe are in [`previews/`](previews). All example data are synthetic.

## Create mode

For a new figure with a layout and requirements of your own ("three panels, 183 mm wide, letters a-c, same y range,
case A always blue"):

1. The agent reads what you already specified (layout, size, colour meaning, ranges, outputs) and the data.
2. It asks at most four questions with recommended answers, only about what is missing: `create_layout`,
   `create_size`, `create_encoding`, `create_requirements` (plus `readme_sections`). Unattended runs use the recommended answers and record that
   nobody confirmed them.
3. It builds the figure on the shared canvas: `render_plot.py` / `render_field.py` for one prepared panel, a recipe for a
   near match, or [`custom_layout_template.py`](skills/sim-plot/recipes/custom_layout_template.py) for any other layout
   (rows x columns, width and height ratios, spanning cells, panel letters, outside colour bars).
4. QA gate, then pdf / png (600 dpi) / svg, a `.viz.json` that records your brief and layout, and a caption stub.

Protocol and the requirement-to-API table: [`skills/sim-plot/references/create-mode.md`](skills/sim-plot/references/create-mode.md).

## Restyle mode

For an existing figure and the code that made it:

1. The agent finds the plotting code and runs the template once. It reads, and prints, what the original does:
   colour map, limits, extend arrows, fraction of cells beyond the limits, smoothing and interpolation, size.
2. It asks at most four questions (`restyle_scope`, `restyle_size`, `restyle_frames`, `readme_sections`, and the original script if unclear) with recommended answers, quoting those facts. A script gate
   (`CONTRACT["confirmed"]`) prevents rendering before this is done; unattended runs use `--assume-defaults`
   and are recorded as such.
3. It rebuilds the panel with `scivis`. Values, smoothing, interpolation, colour limits, extend, axis limits, units
   and text are **frozen**; fonts, size, frame, ticks, colour bar and halos are replaced. Export is refused when the
   frozen layer differs from the original. Changing the colour map is an explicit opt-in (signed fields use vik).
4. Outputs: figure (pdf/png/svg), `.viz.json` with the audit, caption stub, and a before/after image.

Templates: [`skills/sim-field/templates/`](skills/sim-field/templates). Protocol:
[`skills/sim-plot/references/restyle-mode.md`](skills/sim-plot/references/restyle-mode.md).

## Figure README (Chinese)

Every exported figure comes with `<stem>.README.zh-CN.md` (switch off with `"readme": false` in a config). Example:
[`previews/field_wake.README.zh-CN.md`](previews/field_wake.README.zh-CN.md).

| Section | Content | Source |
|---|---|---|
| 1 Figure type and layout | type, panels, canvas size, medium, outputs | generated from the figure |
| 2 Axes | x and y label, linear/log/symlog, range, per panel | generated from the figure |
| 3 Legend and colour | legend entries, what colour encodes, colour-bar label, limits, clipped fraction, extend | generated from the figure and provenance |
| 4 Physical significance | what the quantities mean, normalisation | written by the agent from the real data |
| 5 Preliminary results | journal-style description with numbers and units, plus a submission checklist | written by the agent |
| 6 Discussion directions | analyses the figure invites, plus automatic checks (clipped cells, non-statistical error bands, log axes, synthetic data) | agent + generated |
| 7 Processing and reproducibility | transformations, restyle audit (frozen vs changed), original script hash | generated from provenance |

Sections 4-6 are interpretation, which a program cannot know. The agent asks once (`readme_sections`): *draft them for me*
(recommended), *I will write them*, or *skip*. When drafting, it follows these rules:

- Every paragraph carries its origin: *from the data*, *from the axis labels*, *from your description*, *from the original
  script*, or *suggestion, unverified*. The file shows a per-section status (draft to verify / pending / author writes / skipped).
- Section 5 contains observations with numbers computed from the data; section 6 contains questions and checks to run, not
  conclusions about mechanism.
- It does not write what it cannot support. With only an image, no data or script, an unclear question or synthetic data, the
  section stays `【待补充】` with the reason given.

The text goes in `interpretation` in the config or `INTERPRETATION` in the templates.

## Usage workflows

The prompts below are what you type; the cards are what the agent asks (as multiple-choice question cards in agents
that support them, otherwise as plain text, and it then waits). Wording and layout of the cards depend on your agent
client; the question ids, options and defaults are fixed by the skill.

### Workflow 1: enhance an existing figure (restyle)

```text
You   > Use /sim-field to help me enhance this electric field image.

Agent > Found the plotting code results/figures/plot_rz_charge.py. Ran it once with saving blocked.
        The original uses: RdBu_r, limits +-2.8 (97.5th percentile, 2% of cells clipped, extend both),
        Gaussian sigma 0.8 + bilinear x4, r/z in Angstrom, 600x1100 px. These stay frozen unless you say otherwise.

─── [restyle_scope] Which scope should this round use?
    ◉ White-centre vik + layout (recommended)
    ○ Layout only (keep RdBu_r)
    ○ Also adjust display parameters
─── [restyle_size] Which figure size? All three write PDF, 600 dpi PNG and SVG.
    ◉ Compact paper figure (recommended)
    ○ Strict 89 mm wide
    ○ Presentation figure
─── [restyle_frames] One representative frame or every existing frame? Output goes to a new, separate directory.
    ◉ One representative frame (recommended)
    ○ All 30 frames
─── [readme_sections] Sections 4-6 of the Chinese figure README (physical significance, results, discussion)?
    ◉ Draft them for me, tagged by origin and marked for checking (recommended)
    ○ I will write them
    ○ Skip them

You   > (accepts the recommended answers)

Agent > Rendering. Frozen-layer audit: identical (values, smoothing, limits, extend, axes, units, text).
        Changed on request: RdBu_r -> vik (white centre). The original files were not written.
        restyle_out/rz_charge_restyled.pdf | .png (600 dpi) | .svg
        restyle_out/rz_charge_restyled.viz.json        (audit + the answers above)
        restyle_out/rz_charge_restyled.caption.txt     (mentions the percentile limits and smoothing)
        restyle_out/rz_charge_restyled.before_after.png
        restyle_out/rz_charge_restyled.README.zh-CN.md (axes, legend, colour, frozen/changed lists; sections 4-6 from the original script's labels and what you told me)
```

What the options do in the harvest template ([`restyle_harvest_template.py`](skills/sim-field/templates/restyle_harvest_template.py)):

| Question | Option | Template setting |
|---|---|---|
| `restyle_scope` | vik + layout / layout only / adjust display parameters | `OPT_IN["cmap"]` = `"signed-if-diverging"` / `None` / plus `OPT_IN["vlim"]` etc. |
| `restyle_size` | compact / strict 89 mm / presentation | `SIZE_MODE` = `"compact"` (panel ≤ 80 mm tall, tall panels become narrow figures) / `"strict-89"` / `"presentation"` (160 mm wide, panel ≤ 110 mm tall); `DPI = 600` |
| `restyle_frames` | one frame / all frames | `FRAMES` with one entry, or one entry per existing frame; files go to `OUT_DIR` |
| `readme_sections` | draft / I write / skip | `INTERPRETATION["mode"]` = `"draft"` / `"author"` / `"skip"` |

Unattended runs skip the cards: `--assume-defaults` uses the recommended answers and records that nobody confirmed them.

### Workflow 2: create a figure to your layout and requirements

```text
You   > Use /sim-plot to make a 3-panel figure for a paper: (a) velocity profiles for cases 1-3, (b) parity of
        predicted vs reference Cp, (c) pressure drop of the three geometries as bars. Same height, 183 mm wide,
        panel letters. Cases keep their colours from the earlier figure.

Agent > Read results/profiles.csv, cp_parity.csv, dp.csv (units: m/s, -, kPa). Message: the model reproduces Cp and
        geometry C has the lowest pressure drop. Medium: paper. Colour: cases are categories, bars carry no colour meaning.

─── [create_layout] Which panel arrangement?
    ◉ 1 x 3 row, equal panels, letters a-c (recommended)
    ○ 2 x 2 grid with one empty cell
    ○ Custom: I will describe it
─── [create_size] Which canvas? All write PDF, 600 dpi PNG and SVG.
    ◉ Paper, double column 183 mm x 52 mm (recommended)
    ○ Paper, single column 89 mm
    ○ Slide
─── [create_encoding] What does colour encode?
    ◉ Cases are categories; keep the colours of the earlier figure (recommended)
    ○ Cases are an ordered parameter (sequential map)
    ○ No colour meaning (grey + one accent)
─── [create_requirements] Hard constraints to honour?
    ◉ None beyond the layout (recommended)
    ○ I will list them (axis ranges, shared limits, labels)
─── [readme_sections] (asked right after, as a fifth question)
    ◉ Draft sections 4-6 of the Chinese README for me, tagged and marked for checking (recommended)
    ○ I will write them
    ○ Skip them

You   > (accepts the recommended answers)

Agent > Copied recipes/custom_layout_template.py to results/figures/make_fig3.py, filled BRIEF, WIDTH, PANELS
        and the three data functions, then ran it.
        QA: passed (clipping, font size, canvas width 183.0 mm). Requirements checked against the picture:
        three panels, same height, letters a-c, case colours as before.
        figures_out/fig3.pdf | .png (600 dpi) | .svg
        figures_out/fig3.viz.json       (brief, layout, answers)
        figures_out/fig3.caption.txt
        figures_out/fig3.README.zh-CN.md (axes, legend, colour; physical significance, results, discussion written from your data)
```

The agent's wording will differ. What the skill enforces is the sequence: read the brief, ask only what is missing, state
the message and colour meaning, render through the shared canvas, QA gate, record the brief in the sidecar. The
three-panel example above is what the template produces with its synthetic placeholder data (see the gallery).

## Gallery

All images are in [`previews/`](previews) and were produced by the scripts in [`examples/`](examples) from synthetic
data.

**Field panels with streamlines** (`cfd_field_panels`): speed, pressure coefficient and vorticity on one canvas.
Signed fields use vik with a white centre.

![Field panels](previews/cfd_field_panels.png)

**Restyle before/after** (`restyle_demo`): left, the original; right, the restyled version. Data, smoothing, limits
and units are identical; colour map (vik), fonts, frame and colour bar changed.

![Restyle before and after](previews/restyle_demo/rz_charge_restyled.before_after.png)

| | |
|---|---|
| ![Wake field](previews/field_wake.png)<br>**Wake field** (`field_wake`) | ![Wake zoom](previews/wake_zoom.png)<br>**Zoom inset** (`wake_zoom`) |
| ![CFD monitors](previews/cfd_monitors.png)<br>**Residual and force monitors** (`cfd_monitors`) | ![MD line panels](previews/md_line_panels.png)<br>**MD line panels** (`md_line_panels`) |
| ![Ghost multiples](previews/ghost_multiples.png)<br>**Ghost small multiples** (`ghost_multiples`) | ![Parity plot](previews/scatter_parity.png)<br>**Parity plot with marginals** (`scatter_parity`) |
| ![Slide adaptation](previews/slide_adaptation.png)<br>**Paper figure adapted to a slide** (`slide_adaptation`) | ![Colour audit](previews/color_audit.png)<br>**Colour audit** (`color_audit`) |
| ![Custom layout](previews/custom_layout.png)<br>**Custom 1 x 3 layout from the template** (`custom_layout`) | |

## Repository layout

```
skills/sim-plot/    SKILL.md (calling rules), scripts/scivis (shared layer), scripts/render_plot.py, recipes/ (incl. custom_layout_template.py), references/ (create-mode, restyle-mode, ...), assets/
skills/sim-field/   SKILL.md, scripts/render_field.py, recipes/, templates/, references/
examples/           synthetic configs, data and an example "original" script
previews/           rendered examples
tests/              pytest suite
docs/               DESIGN.md (decisions), UPGRADING.md
```

## Status and limits

- Developed and tested on synthetic data and on one real field export; the OpenFOAM, ParaView and restyle paths
  have not yet been exercised on a wide range of real projects. Please report problems as issues.
- Rendering in this repository's previews used a metric-compatible substitute for Arial.
- Not included: curved contour labels, the book's `Streamlines` class (a `streamplot` wrapper is provided),
  journal-specific compliance checks.
- Scientific validity of the data is out of scope; the sidecar records what was drawn, not whether it is right.

## Credits and licences

Design ideas follow N. P. Rougier, *Scientific Visualization: Python + Matplotlib*; see [`SOURCES.md`](SOURCES.md).
This repository is released under the [MIT License](LICENSE). Bundled third-party assets keep their own licences
(cmcrameri colour tables: MIT; Roboto fonts: Apache-2.0).
