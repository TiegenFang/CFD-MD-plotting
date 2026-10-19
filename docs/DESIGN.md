# Design decisions

## Decisions
1. `scivis` is the architecture layer shared by both skills; `simviz.py` stays as a facade so existing scripts keep working.
2. One theme file (schema 3). Two parallel style definitions removed.
3. Colour: cmcrameri + Paul Tol by role; no ggsci. The soft families (muted, cool, earth, okabe-ito) remain as named palettes.
4. Layout: Rougier as benchmark. Boxed axes, framed legend; direct end labels are opt-in (`end_labels`).
5. Font: Arial standard, strict unless fallback authorised; Roboto Condensed optional.
6. Rules from the book become executable checks or recipes (`rules-to-checks.md`); prose is not copied.

## Not adopted
- Rougier `Streamlines` class (MIT) and curved TextPath contour labels: a `streamplot` wrapper and haloed `clabel` instead.
- Drop-shadow and decorative effects; book figures and prose (CC BY-NC-SA).
- ggsci palettes; rainbow/jet-like maps (BANNED list).

## Not verified
- Real OpenFOAM / ParaView data paths and restyle mode on a wide range of real projects.
- Rendering was done with Liberation Sans (metric-compatible), not Arial.

## Restyle mode
Enhancing an existing figure is a different job from creating one. Display choices of the author (smoothing,
percentile limits, colour map, units) are frozen and audited; only presentation changes. An intake gate with
recorded answers prevents the agent from guessing. See `skills/sim-plot/references/restyle-mode.md`.
