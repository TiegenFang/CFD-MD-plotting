"""Near-wake zoom: vorticity field with a magnified inset (placed in empty space), solid body.

The inset REDRAWS the same artist with the same norm: the zoom never introduces a second
colour mapping. DATA IS SYNTHETIC (see cfd_field_panels.synthetic_cylinder).
"""
from _common import OUT
import numpy as np
from matplotlib.patches import Circle

from scivis import style, layout, fields, palettes as P
from cfd_field_panels import synthetic_cylinder


def main():
    style.apply_style("paper")
    X, Y, U, V, speed, Cp, omega = synthetic_cylinder()
    xl, yl = (-1.5, 4.5), (-1.5, 1.5)
    c = layout.make_canvas("one_half", cell_aspect=fields.cell_aspect(xl, yl), margins=(10.5, 9.0, 12.5, 6.0))
    ax = c.ax(0, 0, field=True)
    cm = P.get_cmap("signed")
    norm = P.diverging_norm(omega, center=0.0, q=99.0)

    def draw(a):
        m = a.pcolormesh(X, Y, omega, cmap=cm, norm=norm, shading="auto", rasterized=True)
        a.add_patch(Circle((0, 0), 0.5, fc=P.GREY_PALE, ec=P.INK, lw=0.45, zorder=5))
        return m

    m = draw(ax)
    layout.field_axes(ax, xl, yl, r"$x/D$", r"$y/D$", xticks=[-1, 0, 1, 2, 3, 4], yticks=[-1, 0, 1])
    # the inset sits in the empty band above the wake, never on top of data
    ins = layout.zoom_inset(ax, (0.6, 2.2), (-0.45, 0.45), draw, width_mm=24.0, anchor="upper right")
    layout.halo(ax.text(4.42, -1.42, "synthetic data", fontsize=6.0, ha="right", va="bottom", color=P.GREY_DARK))
    layout.add_colorbar(ax, m, r"$\omega_z D/U_\infty$", ticks=P.nice_symmetric_ticks(norm.vmax), extend="both")
    layout.panel_labels(c.fig, [ax], titles=["Spanwise vorticity, near wake"])
    issues = layout.qa(c.fig)
    return c.save(OUT / "wake_zoom"), issues


if __name__ == "__main__":
    print(main())
