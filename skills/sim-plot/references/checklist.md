# Figure checklist (run `layout.qa(fig)` first, then look at the PNG)

Automated by `qa` (see `rules-to-checks.md`): no text or legend frame outside the canvas; no overlapping text; no font below the minimum; every colour bar labelled; no CJK inside math; requested font (or its metric-compatible substitute, with a NOTE) actually used; legend covering plotted vertices/segments is reported (approximate: review by eye).

Visual (do these every time):
1. **Message**: can a stranger state it in one sentence within 5 s?
2. **Colour = meaning**: each colour-encoded variable has a role; no rainbow; diverging data has its reference exactly at the centre colour; signed fields use a symmetric norm.
3. **Colour bar**: label with units, ticks round and symmetric for diverging, `extend` arrows if clipped, clipping percentile in the caption.
4. **Grayscale test**: convert to grayscale mentally or with `audit --png`; if series must survive print, are linestyle/marker redundant?
5. **Alignment**: panel letters on a common left edge, equal panel sizes, shared axes labelled once.
6. **Ink and furniture**: four-sided axes, framed legend in empty data space (not covering data), no grid unless it earns its place, <= 3-4 ticks per axis, no dense minor ticks on log axes, units in labels.
7. **Honesty**: size = area, bars start at zero, axis ranges stated, synthetic or smoothed data flagged in the caption.
8. **Medium**: paper at final print size; for slides regenerate with `apply_style("slide")` rather than scaling a paper figure.
9. **Export**: PDF + PNG exist at the intended mm size; fonts embedded (`pdffonts file.pdf`).
