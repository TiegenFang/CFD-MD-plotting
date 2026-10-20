---
name: sim-field
description: >-
  Post-process and visualize CFD/MD physical fields to the user's own layout and requirements (panel arrangement, size, colour limits, overlays), and restyle existing field figures ("enhance/beautify/polish my X plot", 美化已有云图; restyle mode keeps data, smoothing, limits, colour map and units frozen): 云图、contour、切片、等值面、流线、非结构网格、时空密度图; optionally render molecular snapshots when explicitly requested. Preserve geometry, data association, units, masks, averaging and shared color ranges. Use ParaView/pvpython for native 3D CFD data and Matplotlib for prepared 2D fields. Do not trigger for ordinary line/scatter/bar figures, solver debugging or scientific discussion.
---

# Simulation physical-field post-processing

## When to use this skill (calling rules)

Use `sim-field` for physical fields, contours, streamlines, mesh-aware slices, MD density / charge / velocity
construction, or explicitly requested molecular snapshots. Use `../sim-plot` for line / scatter / bar /
condition-comparison / small-multiples figures, monitors and parity plots. Pure scientific discussion, solver
debugging and simulation setup trigger neither. A field panel plus a quantitative plot may use the two routes in
sequence; do not duplicate their analysis.

- Load only the relevant skill and its on-demand reference. `sim-plot` owns `scivis`; `sim-field` imports it from
  the sibling directory.
- Before code: state the message and the medium (paper / slide / poster), and say what each colour encodes.
- Reuse the shared style and an existing script, recipe or template; never paste rcParams or layout code into a
  figure script.
- For these tasks the sim-plot / sim-field visual rules take precedence over a generic Nature or visualization skill.
  Run a journal-specific audit only when submission checking is requested.
- Keep data reduction separate from visual edits; do not rerun trajectories or CFD because a colour or font changed.
- One focused render review (the `qa` gate plus a look at the PNG), fix observed issues in the same source, finish the
  caption stub, stop. No redundant smoke tests, copied plotting scripts or leftover validation files.

## Two modes: pick one first

| The user has... | Mode | Read |
|---|---|---|
| field data and a figure to make, with or without a specified layout | **Create** | `../sim-plot/references/create-mode.md` and the field route below |
| an existing field figure ("enhance my electric-field plot", 美化/优化这张图) whose data must not change | **Restyle** | `../sim-plot/references/restyle-mode.md` |

**Create mode:** the user's layout and requirements are the specification (panel arrangement, size, colour limits and
reference, overlays, zoom insets, labels). Read what they already gave you, then ask at most four questions about what
is missing, in one batch with a recommended answer each: `create_layout`, `create_size`, `create_encoding`,
`create_requirements` (ids and options in `create-mode.md`; for fields, `create_encoding` is the colour map role and
the limits/reference for signed quantities). Render with `scripts/render_field.py CONFIG.json` for one prepared field
panel (put the brief in the config as `"brief": {...}`), `recipes/cfd_field_panels.py` or `recipes/wake_zoom.py` for
near matches, and `../sim-plot/recipes/custom_layout_template.py` for any other specified layout (field panels use
`c.ax(i, j, field=True)` and `layout.add_colorbar`). Native 3D data goes through ParaView first (see the field
contract below).

## Dependency and narrow loading

Requires sibling `../sim-plot`, the single owner of colours, fonts, typography and
layout (`scivis`). Read `../sim-plot/references/visual-system.md` and
`../sim-plot/references/colormap-decision.md`, then choose exactly one route:

- Native or prepared 2D/3D CFD fields: `references/field-rules.md`.
- ParaView/pvpython or existing ParaView state: also `references/paraview.md`.
- MD-derived density/charge/velocity fields, PBC or snapshots:
  `references/md-fields.md`; load the VMD section only for a requested snapshot.

Do not load protein analysis, all ParaView APIs or all MDAnalysis modules by default.

## Restyle mode: an existing figure

If the user names, attaches or implies an existing figure ("enhance my electric-field plot", 美化/优化这张图),
do NOT re-render from raw data with `render_field.py`. Read `../sim-plot/references/restyle-mode.md` and follow it:
find the original plotting code yourself, then run the intake gate: the templates refuse to render until the user
has confirmed the plan (Step 2 of the reference). Ask at most four questions, in one batch with a recommended
answer each, and only about what you could not find in the code: `restyle_scope` (vik + layout / layout only /
also display parameters), `restyle_size` (compact / strict 89 mm / presentation; always pdf + 600 dpi png + svg),
`restyle_frames` (one representative frame / all existing frames, written to a new directory), and the original
script if unclear. Then copy `templates/restyle_harvest_template.py` (runnable matplotlib original) or
`templates/restyle_field_template.py` (paste original data code into the FROZEN block) into the user's project,
never `render_field.py`.

Frozen: values, smoothing, interpolation, colour limits/extend, colour map, axis limits, units, text.
Presentation only: canvas, fonts, frame, ticks, colour bar, halos. Colour map, unit or limit changes are opt-in
suggestions, never silent. Never overwrite the original figure, data or script; export is refused if the frozen
layer differs from the original.

## Field contract before rendering

Resolve source identity, quantity and units, mesh topology, point/cell association,
coordinate system/units, physical domain and exclusions, PBC by axis, spatial/time
reduction, field/color limits, and physical reference for signed quantities.
Reuse verified metadata. Do not invent a missing length, time conversion, array
association, mask, molecule identity or normalization formula.

Separate data extraction/reduction from visualization. Native solver files and
trajectories are read-only. Write derived arrays once, with their units, masks,
connectivity and provenance; style changes must not rerun expensive reductions.
A sampled slice and a depth-integrated or depth-averaged projection are not the
same physical quantity. State which one is displayed.

## Backend

For NEW figures from prepared rectilinear or triangular 2D data, use
`scripts/render_field.py CONFIG.json` (not for restyling an existing figure). It imports `scivis` from the sibling skill and
builds an mm-exact canvas whose height follows the physical aspect. Cell-constant data use pcolormesh/tripcolor. Point data may use native
contour interpolation with explicit levels and masks.

For OpenFOAM/VTK/composite 3D datasets, preserve native readers and filters via
ParaView/pvpython or an existing PyVista workflow. COMSOL exports require coordinate,
unit and topology verification; a CSV is not automatically a mesh.
Do not install every backend. Missing packages block only the relevant route.
Never fabricate a rendering result when a renderer was unavailable.

## Non-negotiable visualization rules

- No convex-hull filling through pore walls, vacuum exclusions or disconnected phases.
- No implicit CellData-to-PointData conversion. Record any authorized interpolation.
- Same physical field comparisons share limits, normalization, colormap, camera,
  slice plane and aspect unless the user explicitly asks for relative contrasts.
- Choose a sequential map for magnitude, a diverging map about a meaningful
  reference for signed deviations, and a cyclic map only for a cyclic variable.
- Log scales must not erase zero/negative data. SymLog needs an explicit threshold.
- Do not default to rainbow/jet, quantile clipping, Gaussian smoothing or unlimited
  contour levels in NEW figures. In restyle mode the author's existing choices are kept and
  disclosed in the caption and sidecar. A polished color map must not imply finer simulated resolution.
- Set geometry aspect only after compatible coordinate units are established.
  Time-space axes need a deliberate, documented layout aspect instead.
- Preserve interface definitions. A VOF alpha=0.5 contour is a stated convention,
  not an exact molecular surface or automatically the model's free boundary.
- Keep quantitative 2D fields unlit. Lighting and transparency in 3D alter perceived
  scalar colors; describe them and use an unlit companion when exact reading matters.
- Reuse the shared palette numerically across backends, not a similar-looking preset.

## MD-specific boundary

Molecular make-whole, spatial wrapping and temporal unwrapping solve different
problems. Never wrap/unwrap all three axes by habit. Do not infer chemical bonds
from a universal distance cutoff for an ionic liquid. Atom, ion, molecule and
cluster counts are distinct. Track identities if particles leave or are deleted.
Read the MD reference before density, MSD or trajectory operations.

## Export, checks and stop rule

Use one source, one config and the shared style. Validate counts/units/domain,
inspect the physical geometry and scalar bar, then inspect final typography.
Correct observed defects without inventing a smoke-test project or many variants.
Run the full optional backend only when needed and available. Do not auto-start a
GUI/server, kill unrelated jobs, reset the camera each frame or rescale each frame.
A user-requested GUI is allowed; batch rendering is the default, not an absolute ban.

Keep raw pixels/mesh data separate from editable text overlays. A ParaView or VMD
screenshot stays raster inside a PDF/SVG. Do not claim vector field geometry merely
because the container is PDF/SVG. Record tested and untested runtime paths honestly.

## House style inherited from sim-plot (scivis)

Quantitative 2D field axes use `layout.field_axes`: equal physical aspect, thin four-sided
frame, no minor ticks. The canvas height is derived from the data window (`cell_aspect`), so
the panel fills its cell and the scalar bar has exactly the panel height. Masked/solid cells
use the pale-grey missing colour, never white. Colour by role: magnitude -> `batlow`,
positive/intense -> `lipari`, temperature -> `lajolla`, density -> `oslo` (top end trimmed),
signed -> `vik` with a pure-white centre and a symmetric norm, phase -> `romaO`; an explicit
`cmap` in the config always wins (`cmc.oslo_r` reproduces the v0.2 sequential default).
Do not lower field alpha or desaturate to mimic a pastel palette. Record the map source.

## Overlays and recipes (explicit in the config, never implicit)

- `streamlines`: `{"u": "u", "v": "v", "x": "xc", "y": "yc", "seeds": "inlet", "density": 1.1}`
  on a regular grid; NaN (solid) cells stay masked and lines stop there.
- `zoom`: `{"xlim": [..], "ylim": [..], "width_mm": 24, "anchor": "upper right"}` redraws the
  same artist with the same cmap/norm in a magnified inset. Put it in empty space, never over data.
- `halo_text`: annotations over the field get an outline, not a box.
- `recipes/cfd_field_panels.py` (|u| + streamlines, Cp, vorticity), `recipes/wake_zoom.py`.
- Export also writes `<stem>.caption.txt`: limits, clipped fraction, reference, masks, display mode.

Layout details: `../sim-plot/references/layout.md`. Rules to checks: `../sim-plot/references/rules-to-checks.md`.
