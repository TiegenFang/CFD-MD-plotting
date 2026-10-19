"""CFD field figure: |U| with streamlines, Cp, spanwise vorticity (flow past a cylinder).

DATA HERE IS SYNTHETIC (potential flow + a Lamb-Oseen vortex street) so the recipe runs
standalone. Replace `synthetic_cylinder()` with your reader and keep the rest.
Contract with real data: X, Y regular grid in units of D; U, V velocity / U_inf;
Cp; omega = omega_z * D / U_inf; NaN inside solid bodies.
"""
from _common import OUT
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

from scivis import style, layout, fields, palettes as P


def synthetic_cylinder(nx=480, ny=240):
    R = 0.5
    x = np.linspace(-1.5, 4.5, nx)
    y = np.linspace(-1.5, 1.5, ny)
    X, Y = np.meshgrid(x, y)
    r2 = X**2 + Y**2
    # potential flow past a cylinder (U_inf = 1)
    u = 1 - R**2 * (X**2 - Y**2) / r2**2
    v = -2 * R**2 * X * Y / r2**2
    # alternating Lamb-Oseen vortices in the wake
    omega = np.zeros_like(X)
    for k, xv in enumerate(np.arange(0.9, 4.4, 0.95)):
        g = (-1) ** k * 2.2
        yv = 0.28 * (-1) ** k
        rc = 0.12 + 0.045 * (xv - 0.9)
        dx, dy = X - xv, Y - yv
        rr2 = dx**2 + dy**2 + 1e-12
        f = g / (2 * np.pi * rr2) * (1 - np.exp(-rr2 / rc**2))
        u += -dy * f
        v += dx * f
        omega += g / (np.pi * rc**2) * np.exp(-rr2 / rc**2)
    speed2 = u**2 + v**2
    Cp = 1 - speed2
    solid = r2 <= R**2
    for a in (u, v, speed2, Cp, omega):
        a[solid] = np.nan
    return X, Y, u, v, np.sqrt(speed2), Cp, omega


def main():
    style.apply_style("paper")
    X, Y, U, V, speed, Cp, omega = synthetic_cylinder()

    c = layout.make_canvas("double", cell_aspect=0.5, ncols=3,
                           margins=(10.5, 9.0, 11.5, 6.5), wgap=14.5)
    axes = [c.ax(0, j, field=True) for j in range(3)]
    xl, yl = (-1.5, 4.5), (-1.5, 1.5)
    xt, yt = [-1, 0, 1, 2, 3, 4], [-1, 0, 1]

    # (a) |U|/U_inf: sequential 'magnitude' + streamlines ---------------------
    cm_seq = P.get_cmap("magnitude")
    m0 = axes[0].pcolormesh(X, Y, speed, cmap=cm_seq, norm=P.sequential_norm(speed),
                            shading="auto", rasterized=True)
    fields.add_streamlines(axes[0], X[0], Y[:, 0], U, V, density=1.1, seeds="inlet", n_seeds=15)  # NaN solid stays masked

    # (b) Cp: signed about 0 -> diverging, symmetric bounds ------------------
    cm_div = P.get_cmap("signed")
    nCp = P.diverging_norm(Cp, center=0.0, q=99.5)
    m1 = axes[1].pcolormesh(X, Y, Cp, cmap=cm_div, norm=nCp, shading="auto", rasterized=True)
    # (c) vorticity: signed, robust clip with extend arrows ------------------
    nW = P.diverging_norm(omega, center=0.0, q=99.0)
    m2 = axes[2].pcolormesh(X, Y, omega, cmap=cm_div, norm=nW, shading="auto", rasterized=True)

    for j, ax in enumerate(axes):
        layout.field_axes(ax, xl, yl, r"$x/D$", r"$y/D$", xticks=xt, yticks=yt,
                          outer_y=(j == 0))
        ax.add_patch(Circle((0, 0), 0.5, fc=P.GREY_PALE, ec=P.INK, lw=0.45, zorder=5))

    layout.add_colorbar(axes[0], m0, r"$|\mathbf{u}|/U_\infty$", ticks=[0, 0.5, 1.0, 1.5])
    tk = P.nice_symmetric_ticks(nCp.vmax, nbins=4)
    layout.add_colorbar(axes[1], m1, r"$C_p$", ticks=tk, extend="both")
    tw = P.nice_symmetric_ticks(nW.vmax, nbins=4)
    layout.add_colorbar(axes[2], m2, r"$\omega_z D/U_\infty$", ticks=tw, extend="both")

    layout.panel_labels(c.fig, axes, titles=["Speed and streamlines", "Pressure coefficient",
                                              "Spanwise vorticity"])
    issues = layout.qa(c.fig)
    paths = c.save(OUT / "cfd_field_panels")
    return paths, issues


if __name__ == "__main__":
    print(main())
