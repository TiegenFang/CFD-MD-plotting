---
name: sim-field
description: >-
  Post-process and visualize CFD/MD physical fields, and restyle existing field figures ("enhance/beautify/polish my X plot", 美化已有云图; restyle mode keeps data, smoothing, limits, colour map and units frozen): 云图、contour、切片、等值面、流线、非结构网格、时空密度图; optionally render molecular snapshots when explicitly requested. Preserve geometry, data association, units, masks, averaging and shared color ranges. Use ParaView/pvpython for native 3D CFD data and Matplotlib for prepared 2D fields. Do not trigger for ordinary line/scatter/bar figures, solver debugging or scientific discussion.
---

# Simulation physical-field post-processing

## Dependency and narrow loading

Requires sibling `../sim-plot`, the single owner of colours, fonts, typography and
layout (`scivis`). Read `../sim-plot/references/visual-system.md` and
`../sim-plot/references/colormap-decision.md`, then choose exactly one route:

- Native or prepared 2D/3D CFD fields: `references/field-rules.md`.
- ParaView/pvpython or existing ParaView state: also `references/paraview.md`.
- MD-derived density/charge/velocity fields, PBC or snapshots:
  `references/md-fields.md`; load the VMD section only for a requested snapshot.

Do not load protein analysis, all ParaView APIs or all MDAnalysis modules by default.

## Existing figure? Use restyle mode first

If the user names, attaches or implies an existing figure ("enhance my electric-field plot", 美化/优化这张图),
do NOT re-render from raw data with `render_field.py`. Read `../sim-plot/references/restyle-mode.md` and follow it:
find the original plotting code yourself, run the intake gate (templates refuse to render until the user confirmed the plan; Step 2 of the reference) (what to improve, keep smoothing/limits/
units/colour map frozen?, target medium), then copy `templates/restyle_harvest_template.py` (runnable matplotlib
original) or `templates/restyle_field_template.py` (paste original data code into the FROZEN block) into the
user's project. Frozen: values, smoothing, interpolation, colour limits/extend, colour map, axis limits, units,
text. Presentation only: canvas, fonts, frame, ticks, colour bar, halos. Colour map, unit or limit changes are
opt-in suggestions, never silent.

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
