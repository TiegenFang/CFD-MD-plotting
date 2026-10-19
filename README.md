# CFD-MD-plotting

**English** | [简体中文](README.zh-CN.md)

Publication-quality figures for CFD and molecular-dynamics results, as two cooperating agent skills that share one
colour, typography and layout system.

| Skill | Use it for |
|---|---|
| [`sim-plot`](skills/sim-plot) | Line, scatter, bar, condition comparison, small multiples, residual and force monitors, parity plots. Hosts the shared `scivis` layer. |
| [`sim-field`](skills/sim-field) | Physical fields: contours, streamlines, slices, mesh-aware fields, MD density and charge maps. Imports `scivis` from `sim-plot`. |

Both skills have two modes:

- **Create** a figure from prepared data (`render_plot.py`, `render_field.py`, recipes).
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
To route requests to the skills, paste [`AGENTS.snippet.md`](AGENTS.snippet.md) into your `AGENTS.md`.

## Quick start

```bash
python skills/sim-plot/scripts/render_plot.py examples/line.json --out out/line
python skills/sim-field/scripts/render_field.py examples/field_wake.json --overwrite
python -m pytest tests -q          # 59 tests
python verify.py                   # end-to-end check (run without SCIVIS_ALLOW_FONT_FALLBACK)
```

Previews of every example and recipe are in [`previews/`](previews). All example data are synthetic.

## Restyle mode

For an existing figure and the code that made it:

1. The agent finds the plotting code and runs the template once. It reads, and prints, what the original does:
   colour map, limits, extend arrows, fraction of cells beyond the limits, smoothing and interpolation, size.
2. It asks at most four questions (`restyle_scope`, `restyle_size`, `restyle_frames`, and the original script if unclear) with recommended answers, quoting those facts. A script gate
   (`CONTRACT["confirmed"]`) prevents rendering before this is done; unattended runs use `--assume-defaults`
   and are recorded as such.
3. It rebuilds the panel with `scivis`. Values, smoothing, interpolation, colour limits, extend, axis limits, units
   and text are **frozen**; fonts, size, frame, ticks, colour bar and halos are replaced. Export is refused when the
   frozen layer differs from the original. Changing the colour map is an explicit opt-in (signed fields use vik).
4. Outputs: figure (pdf/png/svg), `.viz.json` with the audit, caption stub, and a before/after image.

Templates: [`skills/sim-field/templates/`](skills/sim-field/templates). Protocol:
[`skills/sim-plot/references/restyle-mode.md`](skills/sim-plot/references/restyle-mode.md).

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

You   > (accepts the recommended answers)

Agent > Rendering. Frozen-layer audit: identical (values, smoothing, limits, extend, axes, units, text).
        Changed on request: RdBu_r -> vik (white centre). The original files were not written.
        restyle_out/rz_charge_restyled.pdf | .png (600 dpi) | .svg
        restyle_out/rz_charge_restyled.viz.json        (audit + the answers above)
        restyle_out/rz_charge_restyled.caption.txt     (mentions the percentile limits and smoothing)
        restyle_out/rz_charge_restyled.before_after.png
```

What the options do in the harvest template ([`restyle_harvest_template.py`](skills/sim-field/templates/restyle_harvest_template.py)):

| Question | Option | Template setting |
|---|---|---|
| `restyle_scope` | vik + layout / layout only / adjust display parameters | `OPT_IN["cmap"]` = `"signed-if-diverging"` / `None` / plus `OPT_IN["vlim"]` etc. |
| `restyle_size` | compact / strict 89 mm / presentation | `SIZE_MODE` = `"compact"` (panel ≤ 80 mm tall, tall panels become narrow figures) / `"strict-89"` / `"presentation"` (160 mm wide, panel ≤ 110 mm tall); `DPI = 600` |
| `restyle_frames` | one frame / all frames | `FRAMES` with one entry, or one entry per existing frame; files go to `OUT_DIR` |

Unattended runs skip the cards: `--assume-defaults` uses the recommended answers and records that nobody confirmed them.

### Workflow 2: create a figure from data

```text
You   > Use /sim-field to plot the spanwise vorticity and pressure coefficient around the cylinder
        from examples/field_wake.npz for a paper.

Agent > Message: the vortex street sheds alternating-sign vortices; pressure is lowest in the wake core.
        Medium: paper, 183 mm wide, 3 panels. Colour: speed sequential; C_p and vorticity signed ->
        vik with white centre, symmetric limits. Recipe: cfd_field_panels.

Agent > python skills/sim-field/scripts/render_field.py examples/field_wake.json --overwrite
        QA: passed (clipping, font size, colour-bar labels, canvas width).
        out: field_wake.pdf | .png | .svg | .viz.json | .caption.txt
```

The agent's wording will differ; the steps (state the message, choose medium and colour role, render through the
script, QA gate, sidecar) are what the skill enforces.

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

## Repository layout

```
skills/sim-plot/    SKILL.md, scripts/scivis (shared layer), scripts/render_plot.py, recipes/, references/, assets/
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
