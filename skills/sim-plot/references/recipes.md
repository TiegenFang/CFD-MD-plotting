# Recipes (copy the nearest, replace only the data function)

Every recipe runs standalone on synthetic data, builds its canvas in mm, and ends with the QA gate.
Run from the recipe's folder; set `SCIVIS_ALLOW_FONT_FALLBACK=1` on machines without Arial (draft only).

| File | Figure | Data contract |
|---|---|---|
| `sim-plot/recipes/cfd_monitors.py` | residuals, Cd history with averaging window, Cl spectrum | OpenFOAM `.dat` via `io_foam.read_foam_dat` |
| `sim-plot/recipes/md_line_panels.py` | g(r) with bands, MSD log-log with slope guide, raw vs running mean | r,g,sd; t,MSD; t,T |
| `sim-plot/recipes/scatter_parity.py` | parity, density colour, aligned marginals (standard-layout-2) | y_true, y_pred |
| `sim-plot/recipes/ghost_multiples.py` | one panel per case, others as ghosts (rule 8); ordered colour | {case: (t, y)} |
| `sim-plot/recipes/slide_adaptation.py` | the MD data rebuilt for a slide (rule 3) | as md_line_panels |
| `sim-field/recipes/cfd_field_panels.py` | \|u\| + streamlines, Cp, vorticity | regular grid, NaN in solids |
| `sim-field/recipes/wake_zoom.py` | field + magnified inset with connectors | as above |

CLI equivalents (no code): `render_plot.py` kinds `line | scatter | bar | multiples`;
`render_field.py` with optional `streamlines`, `zoom`, `halo_text`.

Library entry points: `layout.small_multiples`, `layout.zoom_inset`, `layout.marginal_canvas`,
`layout.density_scatter`, `layout.halo_clabel`, `fields.add_streamlines`, `scales.set_symlog`,
`scales.slope_guide`, `palettes.lab_ramp`, `palettes.colour_stack`, `captions.caption_stub`.

OpenFOAM data: `io_foam.read_foam_dat` (postProcessing `.dat`, vector columns, restart guard) and
`io_foam.read_foam_log_residuals`. Field extraction onto a regular grid (PyVista `sample`) is not
wrapped here.
