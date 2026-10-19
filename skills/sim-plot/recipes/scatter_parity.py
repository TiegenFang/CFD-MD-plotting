"""Parity plot (prediction vs reference): density-coloured points with aligned marginals.

Layout: Rougier's standard-layout-2 via layout.marginal_canvas (ratio GridSpec, shared axes).
Many points -> density colouring, not alpha stacking (optimisation chapter).
DATA IS SYNTHETIC. Contract: y_true, y_pred 1-D arrays of equal length.
"""
from _common import OUT
import numpy as np

from scivis import style, layout, palettes as P


def main(seed=1, n=6000):
    style.apply_style("paper")
    rng = np.random.default_rng(seed)
    y = rng.gamma(4.0, 0.25, n)
    yp = y + rng.normal(0, 0.06 + 0.05 * y, n)

    c, ax, top, right, corner = layout.marginal_canvas("single", 89)
    lim = (0, 3.2)
    sc, dens = layout.density_scatter(ax, y, yp, lim=lim, size_pt2=layout.area_sizes(1, 1, 3.0))
    ax.plot(lim, lim, color=P.INK, lw=0.6, zorder=0, label="1:1")
    ax.set_xlim(lim); ax.set_ylim(lim); ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([0, 1, 2, 3]); ax.set_yticks([0, 1, 2, 3])
    ax.set_xlabel(r"Reference $\,U/U_\infty$")
    ax.set_ylabel(r"Prediction $\,U/U_\infty$")
    r2 = 1 - ((yp - y) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    rmse = np.sqrt(((yp - y) ** 2).mean())
    ax.text(0.04, 0.96, rf"$R^2={r2:.3f}$" + "\n" + rf"RMSE$={rmse:.3f}$",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.5)
    ax.legend(loc="lower right")

    bins = np.linspace(*lim, 33)
    grey = dict(facecolor=P.GREY, edgecolor="white", linewidth=0.4)
    top.hist(y, bins=bins, **grey)
    right.hist(yp, bins=bins, orientation="horizontal", **grey)

    cb = layout.add_colorbar(corner, sc, "point density", loc="bottom", length=0.72,
                             size_mm=2.0, pad_mm=-12.0, ticks=[dens.min(), dens.max()])
    cb.ax.set_xticklabels(["low", "high"])

    issues = layout.qa(c.fig, expect_width_mm=89)
    return c.save(OUT / "scatter_parity"), issues


if __name__ == "__main__":
    print(main())
