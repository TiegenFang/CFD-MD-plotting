## Scientific figures

For requested line/scatter/bar/condition-comparison/small-multiples figures, monitors, parity
plots, or restyling of already-computed CFD/MD curves, use `sim-plot`. For physical fields,
contours, streamlines, mesh-aware slices, MD density construction or explicitly requested
molecular snapshots, use `sim-field`. Pure scientific discussion, solver debugging and
simulation setup do not trigger these skills.

`sim-plot` owns `scivis`, the shared colour / typography / layout layer; `sim-field` imports it
from the sibling directory. Load only the relevant skill and its on-demand reference. Before code:
state the message and the medium (paper / slide / poster), and say what each colour encodes.
Reuse the shared style and an existing canonical script or recipe; never paste rcParams or layout
code into a figure script. A field panel plus a quantitative plot may use the two routes
sequentially, not duplicate their analysis.

For these tasks, the project's sim-plot/sim-field visual rules take precedence over a generic
Nature/visualization skill. Invoke a journal-specific audit only when submission checking is
requested. Do not load multiple competing style guides by default.

Keep data reduction separate from visual edits. Do not rerun trajectories or CFD because colours
or fonts changed. Perform one focused render review (the `qa` gate plus a look at the PNG), fix
observed issues in the same source, finish the generated caption stub, and stop. Do not create
redundant smoke tests, copied plotting scripts, per-case code forks or persistent temporary
validation artifacts.

Existing figure ("enhance / beautify / restyle my ... plot", 美化已有图): use restyle mode
(`sim-plot/references/restyle-mode.md`). Find the original plotting code yourself; ask at most four questions and
only about what you could not find. Data, smoothing, interpolation, colour limits, extend, colour map, axis limits
and units are FROZEN; change only presentation. Use the restyle templates in the user's project, not
`render_field.py`. Never overwrite the original figure, data or script.
