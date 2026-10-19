# Data and configuration contracts

## Tidy CSV renderer

A row is one observation or one externally computed summary. Required numeric
columns are chosen by `x` and `y`. Optional `group` identifies a case/species.
For bars, x is a category string. Empty y cells are missing values, never zero.
The renderer keeps line gaps and records missing counts. Infinite values fail.

A JSON config defines `data`, `output`, `kind`, `x`, `y`, `xlabel`, `ylabel`.
Optional keys include `group`, `order`, `style_registry`, `profile`, `width_mm`,
`height_mm`, `markers`, `markevery`, `legend_loc`, `legend_columns`, `xlim`, `ylim`,
`xscale`, `yscale`, `uncertainty`, `color_encoding`, `style_override`, `formats`,
`scatter`, `legend_bbox`.
Paths are relative to the JSON file. See the root examples for executable configs.

`uncertainty` supplies `lower`, `upper`, `definition` and optional `display`.
Its bounds are already computed data, not SD values to be multiplied by a hidden
factor. `lower <= estimate <= upper` is required by this errorbar template; use a
separate interval representation if the estimator does not lie inside the interval.

A persistent `style_registry` maps every group name to `color`, `marker`,
`linestyle` and optional bar `hatch`. A single registry should own semantic meaning.
The renderer does not infer that every cation is red or every baseline is weak.

For a numeric sweep use:

```json
{"color_encoding": {"mode": "ordered", "cmap": "cmc.oslo_r", "segment": [0.35, 0.82],
  "limits": [1.0, 3.0], "values": {"E1": 1.0, "E1.5": 1.5, "E3": 3.0}}}
```

The current script is deliberately not a declarative grammar for every conceivable
chart. A custom Matplotlib script may import the same shared helpers for hexbin,
interval-only figures, complex legends or requested multipanel compositions.
Do not build a second framework to handle a one-off annotation.

## Field NPZ renderer

NPZ files use `allow_pickle=False`. Arrays are copied as supplied, without a hidden
unit transform. Record actual field units and coordinate units in the config.
`mask=True` means excluded/invalid, not a numerical zero.

Rectilinear, cell-centered:
- `x`, `y`: actual 1D cell-edge coordinates, strictly increasing.
- `values`: shape `[len(y)-1, len(x)-1]`.
- `mask`: optional same shape.
- config: `grid=rectilinear`, `association=cell`, `method=pcolormesh`.

Rectilinear, point-centered:
- `x`, `y`: 1D node coordinates.
- `values`: shape `[len(y), len(x)]`.
- config: `association=point`, `method=contourf`, explicit physical `levels`.

Triangular mesh:
- `x`, `y`: node coordinates.
- `triangles`: actual integer connectivity, zero-based `[ntri,3]`.
- `triangle_mask`: optional one Boolean per triangle.
- cell data: one value per triangle, `method=tripcolor`.
- point data: one value per node, `method=tricontourf`, explicit `levels`.
- triangles touching invalid nodes are excluded, not interpolated across.

Optional `boundary_xy` is an actual boundary polyline `[n,2]`; separate multiple
segments with NaN rows. Never draw an illustrative boundary as measured geometry.
Curvilinear quadrilateral, general polyhedral and composite meshes are outside this
small renderer; use the original solver mesh in ParaView/PyVista rather than force
it into the NPZ contract.

Required field config:
`data`, `source_id`, `grid`, `association`, `units`, `coordinate_units`,
`domain_description`, `limits`, `xlabel`, `ylabel`, `colorbar_label`, `output`.
Signed scales also require `reference_description`.
Optional: `cmap`, `scale`, `center`, `linthresh`, `boundaries`, `levels`, `ticks`,
`aspect`, `aspect_reason`, figure style and export options.
`limits` always means a pair `[vmin,vmax]`, preferably established for the complete
comparison set. No hidden min/max scaling per frame. For a constant field, provide
a meaningful physical interval; the helper does not invent epsilon differences.

## Provenance

Every export has one `.viz.json`: resolved font, size, software versions, style
hash, data/config identity, reductions supplied by the user, limits, masks and
under/over-range counts. CSV files are hashed; large field/trajectory data use
`source_id` so style edits do not repeatedly hash terabytes. Supply an upstream
checksum/manifest identifier when archival integrity matters.

Raw data are not copied or modified. Do not call a sidecar a validated scientific
record merely because it contains JSON. The user's analysis and unit provenance
remain authoritative. For a stand-alone archive, include required helpers once,
configs and an environment lock made from the tested environment, not an unrelated
server-wide package dump.

## Version 0.2 style keys

```json
{
  "color_encoding": {"mode": "categorical", "palette": "muted"},
  "scatter": {"preset": "hollow"}
}
```

Palette names are `muted`, `cool`, `earth`, `okabe-ito`. A palette may also be an
explicit color list. A supplied style_registry retains precedence. For ordered
encoding, use `values`, `limits`, `cmap` and `segment`, not a categorical name.
Default ordered mapping is cmc.oslo_r with segment [0.35,0.82]. Other explicit maps
default to their full range unless a segment is supplied. Resolved parameters are
recorded in provenance.color_encoding. No points are clipped by segment selection.

Scatter presets: `hollow`, `soft-filled`, `dense`. Optional overrides: `area` in
pt², `edge_width` in pt, `alpha` in (0,1]. Top-level alpha remains supported for
old configs, with scatter.alpha taking precedence. Figure dimensions do not alter
these physical mark sizes. `legend_bbox` is an optional Axes-coordinate anchor.

To change a project's palette without editing installed skills, save:

```json
{"colors": {"categorical": "earth"}}
```

as `style.json`, and set `"style_override": "style.json"` in the figure config.
Remove any more specific color_encoding.palette or registry only deliberately.
The renderers never overwrite either config automatically.

## Multiples and overlays

- `kind: "multiples"`, `ncols`, `cell_aspect`, `multiples_colors`
- `font` (`journal` | `rougier`), `cjk` (bool), `margins_mm` (disables margin auto-fit)
- `xscale`/`yscale: "symlog"` with `x_linthresh`/`y_linthresh` and `*_linthresh_reason`
- Outputs: `<stem>.{pdf,svg,png}`, `<stem>.viz.json` (now includes `qa.non_blocking`, file sizes), `<stem>.caption.txt`
