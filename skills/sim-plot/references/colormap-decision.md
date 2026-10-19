# Colormap decision tree

Answer in order; the first match wins. Roles map to maps in `scivis/palettes.py`.

1. **Is the value a category (species, case, model)?** -> categorical: `categorical(n)`
   (Tol bright, n <= 6) or the soft families by name. More than 6? Facet
   (`layout.small_multiples`) or merge into grey "other". Always add linestyle/marker redundancy
   if the figure may be printed in grey (`redundant_encoding`).
2. **Is it an ordered sweep drawn as a few lines (Re, T, mesh size)?** -> `ordered_colors` with one
   shared domain across related figures; clip the near-white end (segment). With more than ~6 cases,
   ghost multiples with the ordered colour on the highlighted case.
3. **Is it an angle/phase/orientation?** -> `phase` (romaO). Never a linear map.
4. **Is there a physical reference with meaningful sign?** (Cp about freestream, vorticity about 0,
   signed error, charge density) -> `signed` (vik) + `diverging_norm(center=ref)`; symmetric limits;
   `extend="both"` when percentile-clipped; state the percentile. Asymmetric `twoslope` only with a caption note.
5. **Is it non-negative?**
   - generic magnitude (speed, TKE, concentration) -> `magnitude` (batlow)
   - few intense features on a quiet background (Q>0, nu_t/nu, dissipation) -> `positive` (lipari)
   - temperature/enthalpy -> `temperature` (lajolla)
   - density / histogram / point density -> `density` (oslo, top trimmed so it never merges with paper or masked grey)
   - absolute error/residual -> `error` (bilbao)
   - CVD-identical appearance is mandatory -> `cvd_critical` (cividis)
6. **Nothing fits?** Build a ramp with `palettes.lab_ramp([...])` (interpolates in Lab; sRGB
   interpolation goes muddy and uneven), then run `python -m scivis.audit`. Do not invent a rainbow.

Why gradients are interpolated in a perceptual space: sRGB values are not linear in light, and
equal RGB steps do not look equal. Lab/CAM02-UCS steps do, which is what the audit measures.

Masked/NaN cells and solids: pale grey `#DDDDDD` (set as the map's bad colour and as the field
axes' face colour), never white.

Dense scatter: the "density" role + `layout.density_scatter`. Below alpha 0.01 stacking saturates
in 8-bit colour: use `hist2d`/`hexbin`.

Alpha vs opaque bands: a translucent SD band over a line darkens where bands overlap and shifts
hue on grey; for >2 overlapping bands use a lighter opaque tint (`colour_stack`) or facet.
