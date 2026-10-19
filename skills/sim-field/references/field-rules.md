# Physical-field rules

## Selection and geometry

Resolve whether the figure shows a point slice, interpolated slice, depth average,
line integral, volume rendering or isosurface. These quantities have different
units and meanings. A camera screenshot is not a numerical projection definition.
Preserve mesh connectivity, topology and the original solid/fluid/domain masks.
Disconnected regions do not become adjacent because their coordinates are close.

Finite-volume cell values are not nodal values. Display them with piecewise-
constant cells as the first diagnostic. A CellData-to-PointData filter is an
interpolation, not “just formatting”. Near a cone tip or discontinuity it may change
extrema and apparent gradients. If approved, record it and compare extrema/ranges
with the native field. It does not by itself establish conservation or convergence.

For COMSOL CSV exports, confirm whether connectivity survived. An unstructured
point cloud alone is not sufficient to reconstruct a hole or internal boundary.
Prefer original connectivity, native export formats or a documented spatial sampler
that applies the solver-domain mask. Never use unconstrained Delaunay/griddata to
bridge a pore wall or a narrow vacuum gap.

## Normalization and colors

`simviz.make_norm` supports linear, log, symmetric, two-slope, symlog and boundary.
Linear mapping is appropriate unless a physical/data-dynamic-range reason suggests
another scale. Nonnegative data do not automatically need logarithmic display.

Symmetric signed comparisons use equal limits about the physical center. For
example, charge density may use `[-Q,Q]`. `TwoSlopeNorm` deliberately gives the two
sides different color-per-unit slopes when spans differ. It is not equivalent to
a symmetric linear scale. Record that choice and avoid inferring equal magnitude
from equal color distance on opposite sides.

A potential field only gets a diverging map when a meaningful gauge/reference is
specified. Its numerical zero is not automatically a physical transition. Absolute
temperature, speed and number density normally use sequential maps. Temperature
change can be sequential when strictly one-sided or diverging for signed deviations.

`LogNorm` cannot accept zero/negative valid observations. Distinguish true zero,
below detection, missing, masked geometry and out-of-range values. Do not erase
these categories under a transparent background. `SymLogNorm` needs a physically
justified linear threshold, not a magic percentile. Cyclic maps require declared
full-period limits; modulo wrapping is an explicit data operation.

Across cases/times, establish a shared range once from physical limits or a named
analysis interval and record it. The renderer reports under/over counts and extends
the scalar bar. It never applies percentile clipping silently. An intentionally
separate normalized-shape comparison must be labeled as such.

## Scalar bars and contours

Scalar bar: quantity, units, meaningful ticks and declared normalization. Avoid
excessive tick decimals or a rainbow without units. Contours use a short sequence
of scientifically meaningful levels or enough bands to show the resolved structure.
Hundreds of levels are not additional resolution. Mesh-native point contours
interpolate within valid cells; this is disclosed, not confused with no interpolation.

A bin map and a smooth contour of a density estimator are not interchangeable.
Use bin maps for sparse MD counts and optional explicit smoothing only as a separate
specified estimator. Masking should not replace an inconvenient zero with “no data”.

## Geometry, camera and vectors

Use equal x/y geometric scale after coordinate units match. For axisymmetric r-z
fields, r>=0 is the native meridional domain. Mirroring to negative r is a declared
visual construction. Scalar fields may be mirrored under symmetry; the radial
vector component changes sign on the mirrored side. Do not duplicate data in totals.

Use fixed orthographic camera, crop and parallel scale across comparisons when
geometric comparison matters. ResetCamera once before setting the final camera,
not before every frame. Store a camera state. A streamline follows an instantaneous
vector field and is not a particle pathline in unsteady flow.

Arrow sampling/streamline seeds must be stable across cases. Dense glyphs can imply
higher data density than exists. Distinguish velocity, electric field and current
density vectors. Do not label an electric-field streamline as a fluid trajectory.

For 2D quantitative scalar colors, disable lighting/shadows. In 3D, depth cues are
useful but shading changes apparent scalar brightness. Exact color interpretation
may need an unlit slice companion. Distinguish transparent geometry from lower
field magnitude. Keep interface contour and a few useful vectors above the field,
without concealing the tip region.

## Focused QA

Verify source arrays and unit conversion once. Check known extrema and domain
bounds, missing/invalid mask counts, equal camera/range and intended slice. If a
reduction was newly implemented, check an integrated quantity or a synthetic
analytic case. A style-only change does not revalidate or rerun the CFD solution.

## Overlay contract

- Colour: when `cmap` is omitted the role defaults apply (`magnitude` for sequential scales, `signed`
  for `symmetric` / `two-slope` / `symlog`). `"cmap": "cmc.oslo_r"` reproduces the v0.2 default.
- `streamlines`: regular rectilinear grid; arrays `u`, `v` of shape (ny, nx) at coordinates `xc`, `yc`
  (cell centres, strictly increasing). NaN cells (solids) are masked, not zero-filled. `seeds`:
  `"auto"`, `"inlet"` or an (n, 2) array. State the seeding in the caption: streamlines are
  an integral curve visualisation, not a quantitative scale.
- `zoom`: a second view of the SAME artist (same data, cmap, norm). Not a second simulation, not a
  re-normalised panel. Keep the dashed box and connectors; place the inset where it hides no flow feature.
- `halo_text`: outlines text over the field; never a white box.
- Colour-bar `ticks` default to `nice_symmetric_ticks` for `symmetric` scales.
