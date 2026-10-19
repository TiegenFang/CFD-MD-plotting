# Quantitative chart rules

## Lines and parameter sweeps

Connect points only when order has a scientific meaning. Preserve hysteresis or
trajectory order. Do not sort x automatically. Missing y values remain breaks.
No spline, rolling mean, filtering or model fitting solely for aesthetic polish.
A moving average requested for noisy MD signals must be a separately labeled layer
with its window and edge treatment, not a replacement for the original trace.

Time traces normally have lines without a marker at every integration output.
Discrete experiments normally have markers. Model predictions normally have lines.
For visible markers on a dense trace, use `markevery`; never decimate the data line
unless the user approves a scientifically suitable reduction.

For one varying parameter, color by that parameter using fixed numeric limits.
For two variables, prefer color=parameter and line style=model, or facets. Avoid
simultaneously encoding every physical factor in color, shape, size and alpha.
Use an explicit registry when the same case appears across figures. Input row order
is only a single-figure convenience, not a project-wide identity.

Only use a line through isolated parameter values if it is described as a guide
to the eye or justified interpolation. An analytic/theory curve must be generated
by the actual model, not a beautification spline.

## Scatter

Default moderate-size datasets: hollow colored markers with transparent centers.
The paper preset uses about 20 pt² and a 0.8 pt edge. Transparent centers do not
erase earlier observations, unlike white-filled disks. `soft-filled` adds a pale
opaque fill plus a colored edge. `dense` uses small unoutlined marks with alpha 0.4.
These are explicitly selected display presets, not statistical estimators.
Small datasets: visible marker edges and honest uncertainty. Dense datasets:
smaller marks, controlled alpha or rasterized points. Overplotting may justify
hexbin/count/KDE, but these are changed estimators with explicit bins/bandwidth.
Do not introduce KDE just to hide outliers. In log plots, binning in log-coordinate
space and transforming a density require explicit statistical interpretation.

`scatter(s=...)` specifies marker area in points squared; `plot(markersize=...)`
specifies a length in points. The default helper squares the nominal marker size.
Do not encode a quantity with radius when claiming area encoding. No random jitter
for a physical coordinate without permission. No decorative 3D for 2D quantitative data.

## Grouped bars

Use bars for genuinely categorical quantities or compositions. Prefer point and
interval plots for parameter sweeps or small differences in large absolute means.
Bar baseline is zero. Do not crop it to emphasize a trend. Error ranges must be
supplied and named. A log-valued comparison should normally use points, not bars
extending toward an undefined log-zero baseline.

The CSV bar template accepts precomputed values and refuses duplicate group/category
rows. It does not silently calculate replicate means. Width is divided by group
count, avoiding overlapping bars. Hatching is an optional redundant category cue.
Raw replicate observations may be overlaid with declared deterministic jitter on
an explicitly categorical x axis only. Do not invent replicates or significance.

## Uncertainty and comparisons

Name SD, SE, CI, quantile or posterior interval. State whether independent runs,
time blocks, particles or frames are the sampling units. Adjacent MD frames are
not automatically independent replicates. The renderer displays supplied intervals;
it does not repair an invalid estimator or equate a temporal fluctuation envelope
to uncertainty in the mean. Missing uncertainties never become zero-length errors.

Use uncertainty bands for ordered continuous x. Isolated observations need error
bars or interval marks. Keep uncertainty lighter than the estimate without making
it disappear. Do not hide a negative lower CI because the observed mean is positive.
A log-axis failure should prompt a method/axis decision, not clipping.

Comparable panels share the relevant axes. Different physical observables do not
need artificial identical scales. A residual or relative-error axis must give its
reference and denominator. Record how zeros in that denominator are handled.

## Scientific task examples

- Current vs time: preserve startup, mode-switch times and data gaps unless a named
  analysis window was explicitly selected.
- Current/Isp vs E: ordered E mapping, a separate visual cue for polarity/model,
  repeated runs shown as supplied uncertainty rather than extra arbitrary colors.
- RDF: dimensionless y, length-unit x, consistent pair definitions. Plot a verified
  RDF; do not infer bulk normalization inside this skill.
- MSD: explicit atom/molecule/COM and coordinate-frame definitions from analysis.
  Plot and annotate a supplied fit range; do not select diffusion fits for appearance.
- Emission-species bars: atom, molecule, ion and cluster counts are different.
  A percentage denominator must identify particles/events/mass/charge.

## Current configuration examples

```json
{"color_encoding": {"mode": "categorical", "palette": "muted"},
 "scatter": {"preset": "hollow", "area": 20, "edge_width": 0.8}}
```

For a filled scatter replace `hollow` with `soft-filled`. For dense points use
`dense` and consider `rasterize_points: true`. No automatic outlier hiding, drawing
order randomization, jitter, smoothing or regression is permitted.

Grouped bars have a small internal separation, a thin neutral boundary and a zero
baseline. A horizontal legend can sit above the complete boxed data axes using
`legend_columns` and `legend_bbox`. Do not enlarge the y range purely to hide a
legend over data when the legend fits outside the panel within the same canvas.

## Small multiples with ghost series (kind `multiples`)

Use when cases exceed the categorical cap (6) or lines overprint. One panel per case, the case in
colour, every other case as a pale ghost, shared limits computed from all data. Colour encodes the
ordered parameter (`color_encoding.mode: "ordered"`) or one accent. Config: `ncols`, `cell_aspect`,
`multiples_colors: "categorical"` (optional). No uncertainty bands in this kind: draw them per case with `kind: "line"`.

## Dense scatter and scales

Alpha below 0.01 or more than 20 000 points raises: use `layout.density_scatter`, hexbin or hist2d.
`xscale`/`yscale: "symlog"` requires `<axis>_linthresh` and `<axis>_linthresh_reason`
(noise floor or smallest meaningful magnitude); the threshold goes to the caption.
