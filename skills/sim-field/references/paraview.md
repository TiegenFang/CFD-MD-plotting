# ParaView adapter recipe

Status: workflow guidance, not a backend tested in the kit's build environment.
Use an existing project state/script where possible. Query the installed ParaView
version and available properties rather than enforcing a community recipe's version.
ParaView's bundled `pvpython` is normally the appropriate interpreter. Do not
assume a pip-installed Python imports the same ParaView modules.

## Pipeline

Read native data -> UpdatePipeline -> select region/block and array association ->
requested Slice/Clip/Contour -> bind fixed transfer function -> fixed camera ->
render one representative image -> export the requested case set.

OpenFOAM multi-block data may contain patches and internal mesh. Select deliberately.
Do not allow a wall patch to obscure the liquid interface. Check POINTS vs CELLS
before ColorBy and before deciding whether a filter requires interpolation.
Derive gradients, current densities or stresses only with a validated physical
formula and appropriate field discretization, not a guessed array expression.

## Transfer functions

In the analysis Python environment, run:

```bash
python <sim-plot>/scripts/export_lut.py --cmap cmc.oslo_r --output oslo_r.json
```

This creates a normalized [0,1] RGB transfer function from exact palette samples.
Import it in ParaView. Disable automatic rescaling after selecting the field.
The following is a recipe with named project variables, not a runnable case:

```python
from paraview.simple import (
    ColorBy, GetColorTransferFunction, ImportPresets,
    GetScalarBar, ResetCamera, SaveScreenshot,
)
ImportPresets(filename=palette_json)
ColorBy(display, (association, array_name))  # 'CELLS' or 'POINTS' after inspection
lut = GetColorTransferFunction(array_name)
lut.ApplyPreset(preset_name, True)
lut.RescaleTransferFunction(vmin, vmax)
lut.AutomaticRescaleRangeMode = 'Never'
scalar_bar = GetScalarBar(lut, view)
scalar_bar.Title = field_title
scalar_bar.ComponentTitle = ''
ResetCamera(view)               # fit once, BEFORE setting the chosen camera
view.CameraParallelProjection = 1
view.CameraPosition = camera_position
view.CameraFocalPoint = focal_point
view.CameraViewUp = view_up
view.CameraParallelScale = parallel_scale
SaveScreenshot(output_png, view, ImageResolution=[width_px, height_px])
```

Verify names against the local runtime. This recipe fixes a linear color mapping.
For log mapping, explicitly configure the LUT for log space and a positive domain.
A Matplotlib TwoSlope/SymLog norm cannot be reproduced by a plain linear ParaView
rescale. Generate scalar-value RGB control points from the actual normalization or
use a supported equivalent and verify numeric samples at endpoints, zero/threshold
and interior values. Keep colorbar coordinates consistent with physical values.
Do not apply logarithms twice.

Scalar-bar font labels in ParaView are not governed by Matplotlib rcParams. Set
available font families or an approved local font file in that backend, or assemble
a final panel with editable Matplotlib labels. No font is distributed by the kit.
A raster scene may be placed at known physical dimensions; calculate pixel size as
`width_mm / 25.4 * dpi`. Text superimposed in the screenshot remains raster.
Do not claim vector editability of a VMD/ParaView screenshot after PDF export.

## Headless and resource handling

Default to batch only for the current job. No automatic GUI/pvserver start. Headless
rendering depends on the installed OpenGL/EGL/OSMesa build and host environment.
A missing renderer is not evidence that a scientific scene is empty. Read the error
once, identify the runtime issue, and do not repeatedly change colors/camera blindly.
A user-requested GUI is allowed. Track and terminate only child processes created
for this job. Never kill simulation processes or all Python/Qt processes by name.

## Comparison state

Save array association, region/block, slice definition, limits/normalization, RGB
samples, opacity, camera, aspect and pixel/physical output size in the project config.
Time stepping updates data only; it must not reset camera or automatic color ranges.
