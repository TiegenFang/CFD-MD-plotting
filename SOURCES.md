# Sources and licences

- N. P. Rougier, *Scientific Visualization: Python + Matplotlib* (2021), github.com/rougier/scientific-visualization-book.
  Book text: CC BY-NC-SA 4.0; code: BSD 2-clause. This repository restates the book's ideas in its own words and code and
  copies no text, figures or code verbatim; the book's `Streamlines` class (MIT) and drop-shadow effects are not used.
  Mapping of the book's rules to checks: `skills/sim-plot/references/rules-to-checks.md`.
- Paul Tol, *Colour schemes*, SRON technical note: categorical sets are embedded and checked against the `tol_colors`
  package by the audit.
- F. Crameri et al. (2020), scientific colour maps, via `cmcrameri` (MIT). The oslo and vik tables are archived with a
  SHA-256 check under `skills/sim-plot/assets/colormaps/` (see `SOURCES.json`, `LICENSE.txt`).
- Roboto and Roboto Condensed (Apache-2.0), optional, bundled in `skills/sim-plot/scripts/scivis/fonts/` for
  `font="rougier"`; licence text included. Arial is never bundled.
- Matplotlib, NumPy: runtime dependencies, not redistributed.

This repository's own code has no licence file yet.
