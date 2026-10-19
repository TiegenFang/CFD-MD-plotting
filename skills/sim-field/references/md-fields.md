# MD fields and molecular scenes

This route adapts useful VMD/MDAnalysis workflow ideas without importing protein-
centric defaults. Raw-trajectory adapters are project-specific and not bundled as a
universal, validated reader. Existing verified LAMMPS/GROMACS post-processing wins.

## Decide what is being visualized

A particle snapshot, an instantaneous coarse-grained field, a time-averaged density,
a residence map and an emitted-species histogram represent different observables.
State the selection, species level, coordinate frame, periodic axes, spatial bins,
time window, weights and normalization before converting trajectories.

Do not infer molecule identity from a render color or residue naming convention.
Use actual topology and atom/molecule IDs. Static topology can be invalid when
atoms are deleted, reactions change connectivity or dump atom ordering changes.
LAMMPS variable-particle-number/open-boundary output needs per-frame IDs and a reader
that supports this case. Missing/deleted atoms are not zero-position observations.

## PBC and coordinate processing

Making a molecule whole, wrapping it into a spatial cell, and temporally unwrapping
a trajectory are different operations. Prefer a physically correct coordinate frame
for the observable rather than always unwrapping first.

For xy-periodic/z-open slabs, periodic correction applies only to x/y. This is an
example, not an assumed setting for every simulation. Read each case's flags.
MSD requires displacement-continuous coordinates and explicit reference/COM drift
handling. Bulk structural distances often use minimum-image distances instead.
A comoving frame may be appropriate for a jet, but its construction and velocity
subtraction must be reported. Do not erase the physical emission drift silently.

MDAnalysis commonly converts positions to Angstrom and time to ps. Reader-specific
options and source unit styles must still be checked. LAMMPS units=real and metal
have different time units. Do not label a plot ns by merely renaming a ps column.

## Binned physical quantities

For frame f, bin b, bin-accessible volume V_bf and time weight w_f, a time-mean number
density is

    n_b = sum_f[w_f N_bf / V_bf] / sum_f[w_f]

A charge density replaces N_bf with sum_i q_i. A mass density uses sum_i m_i.
These are not particle counts normalized to the largest bin. Empty accessible bins
are zero number/charge/mass density, not missing. Solid/excluded volume is a mask.
For varying volumes, mean(N/V) is not generally sum(N)/sum(V); choose the estimator.
Equal frame weights require uniform temporal sampling or an explicitly frame-based
rather than time-based average. Document interval weighting for irregular output.

For an x-z map averaged through thickness Ly:

    V_b = Delta_x * Delta_z * Ly

Without dividing by Ly, the displayed quantity is an areal projection with different
units. For axisymmetric r-z annuli:

    V_b = pi * (r_outer**2 - r_inner**2) * Delta_z

Never use constant dr*dz as a cylindrical bin volume. Partial solid occupancy
requires a geometry-derived accessible volume or an explicit geometric-volume
convention. Verify that density times its chosen volume integrates to the selected
particle/mass/charge total under the same weighting. Cropped particles are recorded.

A conditional mean velocity in a bin must specify number-weighted or mass-weighted
sampling. Velocity is undefined in an empty bin, so mask it instead of inserting
zero. A time-average of per-frame mean velocities and a pooled particle-weighted
mean can differ. Streaming subtraction for temperature is a physical operation,
not a visual filter. Low-occupancy temperature bins need a justified estimator.

The naive bulk RDF normalization includes an isotropic shell and reference density.
A slab with vacuum, a pore wall or an emitting nonstationary jet does not generally
satisfy those assumptions. Do not compute a “bulk RDF” with the entire vacuum-box
volume simply because a library accepts the input.

For time-z maps, record time-bin edges and spatial-bin edges. Preserve frame weights,
physical units and missing intervals. Use a layout aspect for unlike time/length
axes, not geometric equal aspect. Smoothing/bin-size changes require physical
justification and sensitivity evaluation when they affect conclusions.

## Optional VMD snapshot route

Load only for explicit molecular images/animations. Check the available VMD/vmd-
python renderer at runtime. Do not assume TachyonInternal exists or that a Python
wrapper is preinstalled. Run batch Tcl or an established vmd-python workflow without
a GUI by default, but honor a requested interactive GUI.

Define selections from the actual system. For an ionic liquid, use molecule/ion
species and material regions rather than protein/cartoon/secondary-structure rules.
A useful scene separates solid substrate, cations, anions and water, then uses
geometry/opacity to reduce occlusion without omitting physically important species.
The semantic palette is an explicit project registry, not an elemental rainbow.

Use topology-defined intramolecular bonds. Do not infer ionic coordination or
clusters with an arbitrary universal bond cutoff. A cluster definition requires a
separate physical graph criterion and PBC-aware distances. A displayed sphere
radius is a graphical choice unless explicitly an atomic/van der Waals radius.

Use orthographic geometry and fixed camera across comparison frames. Apply a
consistent clipping plane to expose the pore only when requested and label it.
Show orientation/scale from the actual simulation box. Frame time comes from the
trajectory, not the video frame rate. Playback fps and physical sampling interval
must remain separate. Ray-traced images are raster, not editable quantitative data.

## Scope and validation

This kit does not perform production RDF, MSD, current, viscosity or conductivity
analysis. It carries plotting safeguards and field contracts. New estimators need
an appropriate scientific test once; a later color/font edit must not rerun them.
Use streaming/chunked trajectory access where supported. Do not load terabytes into
memory to select a single frame, and do not create duplicate full trajectories for
scene styling. Keep backend and scientific validation claims separate.
