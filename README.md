# CFD-MD-plotting

Publication-quality figures for CFD and molecular-dynamics results, as two cooperating agent skills that share one
colour, typography and layout system.

| Skill | Use it for |
|---|---|
| [`sim-plot`](skills/sim-plot) | Line, scatter, bar, condition comparison, small multiples, residual and force monitors, parity plots. Hosts the shared `scivis` layer. |
| [`sim-field`](skills/sim-field) | Physical fields: contours, streamlines, slices, mesh-aware fields, MD density and charge maps. Imports `scivis` from `sim-plot`. |

Both skills have two modes:

- **Create** a figure from prepared data (`render_plot.py`, `render_field.py`, recipes).
- **Restyle** a figure you already have ("enhance my plot"): the data layer is frozen and audited, only the
  presentation changes. See [Restyle mode](#restyle-mode).

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
python -m pytest tests -q          # 57 tests
python verify.py                   # end-to-end check (run without SCIVIS_ALLOW_FONT_FALLBACK)
```

Previews of every example and recipe are in [`previews/`](previews). All example data are synthetic.

## Restyle mode

For an existing figure and the code that made it:

1. The agent finds the plotting code and runs the template once. It reads, and prints, what the original does:
   colour map, limits, extend arrows, fraction of cells beyond the limits, smoothing and interpolation, size.
2. It asks at most four questions with recommended answers, quoting those facts. A script gate
   (`CONTRACT["confirmed"]`) prevents rendering before this is done; unattended runs use `--assume-defaults`
   and are recorded as such.
3. It rebuilds the panel with `scivis`. Values, smoothing, interpolation, colour limits, extend, axis limits, units
   and text are **frozen**; fonts, size, frame, ticks, colour bar and halos are replaced. Export is refused when the
   frozen layer differs from the original. Changing the colour map is an explicit opt-in (signed fields use vik).
4. Outputs: figure (pdf/png/svg), `.viz.json` with the audit, caption stub, and a before/after image.

Templates: [`skills/sim-field/templates/`](skills/sim-field/templates). Protocol:
[`skills/sim-plot/references/restyle-mode.md`](skills/sim-plot/references/restyle-mode.md).

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
Bundled third-party assets keep their licences (cmcrameri colour tables: MIT; Roboto fonts: Apache-2.0).
A licence for this repository's own code has not been chosen yet.
