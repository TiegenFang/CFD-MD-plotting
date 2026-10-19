# Shared visual system

This is a proposed engineering/physics house style, not an official journal preset.
Defaults live only in `../assets/theme.json`. See the kit's `SOURCES.md` for primary
references and limits of the upstream community examples.

## Color semantics

The distinction is not “discrete chart versus continuous chart”. Sampled electric
fields 1, 1.5 and 3 V/nm are ordered values even when plotted as three lines.
Different chemical species are categories even when they appear in a continuous
image. Select the encoding before selecting the palette.

| Meaning | Default | Required constraint |
| --- | --- | --- |
| Unordered species/models/cases | Paul Tol `tol-bright` (<= 6; the 7th grey is reserved) | Persistent category registry and marker/line redundancy |
| Ordered parameter sweep | `ordered_colors` through cmc.oslo_r, segment [0.35, 0.82] | Same physical parameter limits across related figures |
| Positive magnitude field | `magnitude` (batlow); `positive` (lipari); `temperature` (lajolla); `density` (oslo, trimmed) | Units and linear/log normalization declared |
| Signed deviation | `signed` (vik, pure-white centre) | Physically defined centre, symmetric spans |
| Cyclic phase/angle | `phase` (romaO) | Full declared period and consistent phase origin |
| Baseline/reference/masked | Neutral grey `#555555` / `#DDDDDD` | Meaning stable across figures |

The soft project families (`muted`, `cool`, `earth`, `okabe-ito`) from theme.json remain available by
name (`color_encoding.palette: "muted"`), e.g. to keep an established species registry. Earlier releases used
`muted` and `cmc.oslo_r` as defaults; this release follows the Tol + role-based decision
(see `docs/DESIGN.md`).

Crameri names ending in `S`, such as `batlowS`, are categorical sequences.
Take the first N listed colors in their supplied order. Do not evenly resample a
categorical list as if it were a sequential gradient. Large N still needs a
rendered distinction check and often facets instead of more colors.

The default custom `muted` palette balances cool blue, warm clay, sage, violet,
ochre and teal. `cool` and `earth` offer narrower cool/warm families. These are
house designs, not CVD-certified or official journal palettes. Hue differences
become less discriminable as chroma is reduced; use the fixed marker and line-style
encoding. Reserve very pale versions for fill layers, not thin foreground strokes.

Choose a palette through color_encoding.palette, a project theme override, or the
global theme. An explicit per-series registry wins. A global change must not silently
recolor an already established species registry. `colors.categorical` still accepts
an explicit color list for compatibility with v0.1. The old colors remain under
`okabe-ito` as an opt-in alternative.

Do not assume batlow, vik, roma, or a journal-branded palette is automatically
appropriate for every field. Diverging/cyclic maps are not globally lightness-
monotonic like sequential maps. Grayscale alone cannot prove sign or category
readability. Use redundant labels, line styles or markers and inspect the result.
The referenced community palette skill's blanket “turbo is perceptually uniform”
claim is not adopted. Do not call turbo/jet quantitative defaults.

For an ordered sweep, `ordered_colors(values, limits=(lo,hi))` uses numeric values,
not equally spaced category indices. A chosen clipped segment of a color map is a
new explicit design transform and must be recorded. Thin-line contrast is checked
at final size. Do not automatically use an almost-white endpoint on white.

## Fonts and mathematical notation

Text: Arial. Math: custom Mathtext with Arial regular/italic/bold where supported,
STIX sans fallback for missing mathematical glyphs. `text.usetex=False` by default.
This avoids making a LaTeX distribution a hidden dependency.

The renderer detects missing Arial. Final rendering stops instead of silently
renaming another font Arial. `--allow-font-fallback` explicitly permits a draft
with Liberation Sans or DejaVu Sans and records that fact. No font files are
bundled or downloaded by this kit. The regular family check does not prove that
every mathematical glyph or style variant used Arial.

Examples:

```python
xlabel = r'$t$ / ns'
ylabel = r'$I$ / $\mathrm{nA}$'
field_label = r'$E_z$ / $\mathrm{V\,nm^{-1}}$'
charge_label = r'$\rho_{\mathrm{e}}$ / $\mathrm{C\,m^{-3}}$'
isp_label = r'$I_{\mathrm{sp}}$ / s'
ratio_label = r'$r/r_0$'
```

Variables and variable indices are italic. Units, operators and descriptive
subscripts such as sp, rms and max are upright. Do not turn every letter upright
with `mathtext.default='regular'`. Vectors may use a consistent bold convention.
Choose a clear single-line axis label rather than putting a long governing
equation in a tick label. Use “/” or a consistent unit bracket convention.

Arial does not supply Chinese glyphs. For Chinese figure text, add a locally
available CJK family as an explicit project override/workflow and visually inspect
mixed strings. Do not claim full CJK coverage from the default Latin-only helper.

`pdf.fonttype=42` changes font embedding, not the font family. `svg.fonttype='none'`
preserves text but does not embed fonts in SVG; another viewer may substitute.
Mathtext is not equivalent to a fully editable equation object. Complex math or
special alphabets can use additional fonts. Inspect the exported result.

## Dimensions and weight

| Profile | Canvas mm | Panel / title / label / tick / legend pt | Line / spine pt | Marker pt |
| --- | --- | --- | --- | --- |
| paper | 89 x 66 | 9 bold / 7 / 7 / 6.5 / 6.5 | 1.1 / 0.6 | 3.2 |
| paper-wide | 183 x 80 | same | same | same |
| presentation | 160 x 110 | 18 / 14 / 14 / 12 / 12 | 2.4 / 1.2 | 7 |
| slide | 254 x 143 | same as presentation | same | same |
| poster | 400 x 280 | 26 / 20 / 20 / 18 / 18 | 3.4 / 1.8 | 10 |

Widths for multi-panel work: `single` 89, `one_half` 120, `double` 183 mm (edit `widths_mm`). These are starting points, not Nature compliance. The Nature final-artwork page
has its own smaller text/stroke requirements. Verify the exact target journal and
submission phase only for an actual submission audit. A physical-width change
must not inadvertently shrink fonts after export. Never start with 28-inch plots
and hope a later downscale fixes the hierarchy.

## Layout

Single and multi-panel figures use `scivis.layout.make_canvas`: a GridSpec with explicit mm margins
and gaps, built at the final size (see `layout.md`). Single-axes figures (`render_plot.py`) fit their
margins to the actual furniture on export while the canvas stays exact; multi-panel figures keep their
designed margins so panels align. Do not call `tight_layout` or `bbox_inches="tight"`.
Colour bars, legends outside the axes and insets are excluded from equal-panel checks. Direct labels
are useful only if they remain separated after scaling (opt-in).

Default quantitative axes have all four spines, inward mirrored ticks, and number labels only on
left/bottom. The frame does not introduce secondary axes. Preserve square physical cells and actual
aspect. Scalar bars show labels on one side only. Fields use `set_axisbelow(False)` semantics so
inward ticks are not hidden by the opaque layer. Dense layers may be rasterized; text/axes stay vector.

## Practical review

Inspect normal view and intended publication scale for overlapping labels, small
subscripts, too-heavy markers, weak curve contrast and a misleading legend. A
thumbnail is not a glyph audit. Review CVD/gray behavior if colors carry essential
information. Do not claim automatic accessibility or journal validation.

## Archived Crameri maps

oslo and vik (and their `_r` reversals) are read from the original 256-row RGB tables in
`assets/colormaps/` (MIT, SHA-256 checked) whether or not cmcrameri is installed. Every other
Crameri name (batlow, lipari, lajolla, bilbao, romaO ...) needs `pip install cmcrameri`; a missing
package raises, it never substitutes a look-alike. The map source is recorded for fields. A diverging
map with a tinted centre gets a Gaussian blend to pure white around the centre (`white_center=True`);
`white_center=False` returns the published map. A role may trim a map's end (`density` uses 0-0.88);
the segment is recorded in the provenance. No alpha wash or RGB desaturation is applied to field data.
