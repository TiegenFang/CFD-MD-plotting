# Rules -> workflow -> checks

Derived from the ten rules and the chapters on defaults, layout, colours, ornaments and
optimisation of N. P. Rougier, *Scientific Visualization: Python + Matplotlib* (CC BY-NC-SA 4.0;
the rules are restated here in our own words and bound to code). A rule is only useful when
something fails if it is broken.

| # | Decision (ask before coding) | Where it is enforced |
|---|---|---|
| 1 | Who reads this, and what must they conclude in five seconds? | Workflow step 1; the caption stub starts from the label/title |
| 2 | Is the data ready? (units, missing values, replication) | `data-contracts.md`; renderers raise on missing metadata |
| 3 | Which medium? Rebuild for it, never scale | `apply_style("paper"/"slide"/"poster")`, `recipes/slide_adaptation.py`, `qa(expect_width_mm=...)` |
| 4 | Is there a caption that states every choice that changes appearance? | `export_figure` writes `<stem>.caption.txt` (limits, clipped %, reference, masks, smoothing, synthetic) |
| 5 | Which defaults did you override, and why? | `assets/theme.json` is the only place; `.mplstyle` files generated from it |
| 6 | Does each colour carry meaning? If not: ink + grey + one accent | role-based `get_cmap`, `categorical` caps, `highlight`, ghost multiples |
| 7 | Could this mislead? (area vs radius, truncated bars, asymmetric diverging limits, log with zeros, hidden clipping) | `area_sizes`, `make_norm`/`diverging_norm` guards, `field_status.clipped_fraction`, bar zero-baseline and no-log-bar errors |
| 8 | What can be removed? (grid, extra ticks, rainbow, legend duplicates) | 3-5 ticks, no grid by default, `small_multiples` instead of a spaghetti plot |
| 9 | Message over beauty: stop when the message is clear | stop rule in `SKILL.md`; one render + one fix |
| 10 | Is it reproducible? | `.viz.json` (theme hash, versions, input hash, fonts, colour-map source) |

## What `layout.qa` / `export_figure` check

| Code | Meaning | Blocks export |
|---|---|---|
| clipped | text or legend frame outside the canvas | yes |
| cbar | colour bar without a label | yes |
| tiny | font below the medium's minimum (5 / 10 / 14 pt) | yes |
| cjk-math | Chinese characters inside a `$...$` string | yes |
| font | requested font absent and substitute not metric-compatible | yes |
| size | canvas width differs from `expect_width_mm` | yes (if requested) |
| overlap | two text objects overlap | recorded in sidecar, review |
| legend | legend covers plotted points/segments | recorded in sidecar, review |

Not automated: message clarity, colour meaning, physical validity, journal compliance.

## Deliberately not adopted from the book

- Decorative effects (drop-shadowed contours, 3D flourishes): they add ink, not information.
- Open L-shaped axes and direct labels as the **default**: the project chose boxed axes and framed
  legends. Both remain available as opt-ins (`boxed=False`, `layout.end_labels`).
- Roboto Condensed as the default face (project default is Arial); available as `font="rougier"`.
- Curved text-path contour labels: replaced by `layout.halo_clabel` (clabel with an outline),
  which is robust on high-curvature contours.
- The book's `Streamlines` class (uniform spacing, tapering): `fields.add_streamlines` wraps
  Matplotlib's `streamplot` with explicit seeding and masked solids instead.
