# Upgrading from the earlier sim-plot / sim-field and cfd-md-plotting skills

The earlier `sim-plot` / `sim-field` pair (with `simviz.py`) and the standalone `cfd-md-plotting` skill are replaced by
this repository. Existing scripts keep working: `simviz.py` is a compatibility facade over `scivis`.

Defaults that changed on purpose (each earlier default is still available by naming it):

| Earlier | Now |
|---|---|
| `muted` categorical palette | `tol-bright` (`palette: "muted"` keeps the old one) |
| sequential `cmc.oslo_r` | role `magnitude` = batlow (`cmap: "cmc.oslo_r"` keeps the old one) |
| diverging oslo/vik by name | role `signed` = vik with a white centre |
| 8.5 pt base text | 7 pt hierarchy (tick 6.5, panel labels 9) |
| ad hoc widths | 89 / 120 / 183 mm |
| frameless legend | framed legend (`axes.legend_frame`) |
| `render_field` with a fixed figure size | canvas from the physical aspect; tall panels narrower |

Remove old installed copies before installing; `install.py` refuses to overwrite an existing installation.
