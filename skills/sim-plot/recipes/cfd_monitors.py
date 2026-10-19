"""OpenFOAM monitors: residuals, force coefficient history, Cl spectrum (Strouhal).

Reads postProcessing-style .dat files through scivis.io_foam.read_foam_dat. When run
standalone it first FABRICATES two files in the same header format so the pipeline is
exercised end to end. Point FORCES/RES at your own files to use real output.
"""
from _common import OUT
import numpy as np
import matplotlib.pyplot as plt

from scivis import style, layout, palettes as P
from scivis.io_foam import read_foam_dat


def fabricate(dirpath, seed=5):
    rng = np.random.default_rng(seed)
    n, dt = 4000, 0.05
    t = np.arange(1, n + 1) * dt
    St = 0.2
    cl = 0.9 * (1 - np.exp(-t / 15)) * np.sin(2 * np.pi * St * t) + 0.02 * rng.standard_normal(n)
    cd = 1.35 + 0.1 * (1 - np.exp(-t / 15)) * np.sin(4 * np.pi * St * t + 0.6) - 0.3 * np.exp(-t / 8)
    with open(dirpath / "forceCoeffs.dat", "w") as f:
        f.write("# Force coefficients\n# magUInf     : 1\n# lRef        : 1\n#\n")
        f.write("# Time          Cd              Cs              Cl\n")
        for a, b, c_ in zip(t, cd, cl):
            f.write(f"{a:.4f}  {b:.6f}  0.000000  {c_:.6f}\n")
    it = np.arange(1, 801)
    with open(dirpath / "residuals.dat", "w") as f:
        f.write("# Residuals\n# Time    Ux    Uy    p\n")
        for i in it:
            ux = 10 ** (-1.2 - 3.2 * (1 - np.exp(-i / 250)) + 0.08 * rng.standard_normal())
            uy = 10 ** (-1.0 - 3.6 * (1 - np.exp(-i / 280)) + 0.08 * rng.standard_normal())
            p = 10 ** (-0.6 - 3.0 * (1 - np.exp(-i / 300)) + 0.10 * rng.standard_normal())
            f.write(f"{i}  {ux:.6e}  {uy:.6e}  {p:.6e}\n")
    return dirpath / "forceCoeffs.dat", dirpath / "residuals.dat"


def main():
    style.apply_style("paper")
    FORCES, RES = fabricate(OUT)
    F, R = read_foam_dat(FORCES), read_foam_dat(RES)

    c = layout.make_canvas("double", 52, ncols=3, margins=(11.5, 10.5, 3.0, 6.5), wgap=15.0)
    a, b, d = (c.ax(0, j) for j in range(3))
    cols = P.redundant_encoding(3)

    # (a) residuals ---------------------------------------------------------------
    for key, lab, st in zip(("Ux", "Uy", "p"), (r"$U_x$", r"$U_y$", r"$p$"), cols):
        a.semilogy(R["Time"], R[key], color=st["color"], lw=0.8, rasterized=True, label=lab)
    a.axhline(1e-5, color=P.GREY_DARK, lw=0.5, ls=(0, (2, 2)))
    a.text(30, 1.5e-5, "target", color=P.GREY_DARK, fontsize=6, va="bottom")
    a.set_xlim(0, 800); a.set_ylim(1e-6, 1)
    a.set_xticks([0, 400, 800]); a.set_yticks([1e-6, 1e-3, 1])
    a.set_xlabel("Iteration"); a.set_ylabel("Initial residual")
    a.minorticks_off()
    a.legend(loc="upper right")

    # (b) Cd(t): averaging window shaded, mean as a labelled level ------------------
    t, cd = F["Time"], F["Cd"]
    t0 = 0.5 * t[-1]
    m = t >= t0
    b.axvspan(t0, t[-1], color=P.GREY_PALE, lw=0, zorder=0)
    b.plot(t, cd, color=cols[0]["color"], lw=0.8, rasterized=True, label=r"$C_d$")
    b.axhline(cd[m].mean(), color=P.INK, lw=0.5, ls=(0, (3, 2)),
              label=rf"$\overline{{C_d}}={cd[m].mean():.2f}$")
    b.set_xlim(0, t[-1]); b.set_ylim(1.0, 1.75)
    b.set_xticks([0, 100, 200]); b.set_yticks([1.0, 1.3, 1.6])
    b.set_xlabel(r"$t\,U/D$"); b.set_ylabel(r"$C_d$")
    from matplotlib.patches import Patch
    h, l = b.get_legend_handles_labels()
    h.append(Patch(fc=P.GREY_PALE, ec="none")); l.append("averaging window")
    b.legend(h, l, loc="upper left")

    # (c) spectrum of Cl over the averaging window ------------------------------------
    cl = F["Cl"][m]
    dt = np.median(np.diff(t))
    w = np.hanning(cl.size)
    spec = np.abs(np.fft.rfft((cl - cl.mean()) * w)) ** 2
    f = np.fft.rfftfreq(cl.size, dt)
    d.semilogy(f, spec / spec.max(), color=cols[1]["color"], lw=0.8)
    fp = f[np.argmax(spec)]
    d.annotate(rf"$St={fp:.2f}$", xy=(fp, 1), xytext=(8, -2), textcoords="offset points",
               ha="left", va="top", fontsize=6.5,
               arrowprops=dict(arrowstyle="-", lw=0.5, color=P.INK, shrinkA=0, shrinkB=1))
    d.set_xlim(0, 1.0); d.set_ylim(1e-9, 3)
    d.set_xticks([0, 0.5, 1.0]); d.set_yticks([1e-8, 1e-4, 1])
    d.minorticks_off()
    d.set_xlabel(r"$f D/U$"); d.set_ylabel(r"$|\hat{C}_l|^2$ (normalised)")

    layout.panel_labels(c.fig, [a, b, d], titles=["Convergence", "Drag history", "Lift spectrum"])
    issues = layout.qa(c.fig)
    return c.save(OUT / "cfd_monitors"), issues


if __name__ == "__main__":
    print(main())
