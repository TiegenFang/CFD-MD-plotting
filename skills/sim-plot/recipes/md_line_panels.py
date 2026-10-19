"""MD figure: g(r) with uncertainty bands, MSD (log-log, slope guides), and a monitored
quantity with raw data in grey and the running mean in colour.

DATA IS SYNTHETIC. Contract with real data: r, g(r) (+ std over blocks); t, MSD;
t, T(t). Standard framed legends; curves also carry
linestyle redundancy so they survive grayscale printing.
"""
from _common import OUT
import numpy as np
import matplotlib.pyplot as plt

from scivis import style, layout, scales, palettes as P


def synthetic_md(seed=3):
    rng = np.random.default_rng(seed)
    r = np.linspace(0.8, 4.0, 400)
    states = {}
    for T, lam, amp in ((0.8, 1.8, 1.0), (1.2, 1.1, 0.75), (2.0, 0.6, 0.5)):
        g = 1 + amp * np.exp(-(r - 1.0) / lam) * np.cos(2 * np.pi * (r - 0.95) / 1.05)
        g[r < 0.92] *= np.clip((r[r < 0.92] - 0.8) / 0.12, 0, 1) ** 3
        states[T] = (g, 0.015 + 0.03 * np.exp(-(r - 1) / 2))
    t = np.logspace(-1, 3, 120)
    D = {0.8: 0.04, 1.2: 0.11, 2.0: 0.3}
    msd = {T: 6 * D[T] * t * (1 - np.exp(-t / 0.3)) + 3 * (t < 0.3) * t**2 * 0.02 for T in D}
    tt = np.linspace(0, 50, 2500)
    temp = 1.2 + 0.05 * rng.standard_normal(tt.size).cumsum() * 0.2
    temp = 1.2 + 0.12 * rng.standard_normal(tt.size) + 0.06 * np.sin(tt / 6)
    return r, states, t, msd, tt, temp


def main():
    style.apply_style("paper")
    r, states, t, msd, tt, temp = synthetic_md()
    cols = P.redundant_encoding(3)

    c = layout.make_canvas("double", 52, ncols=3, margins=(11.5, 10.5, 3.0, 6.5),
                           wgap=14.5, width_ratios=[1, 1, 1])
    a, b, d = (c.ax(0, j) for j in range(3))

    # (a) g(r): bands + end labels ---------------------------------------------
    for (T, (g, sd)), st in zip(states.items(), cols):
        a.fill_between(r, g - sd, g + sd, color=st["color"], alpha=0.18, lw=0)
        a.plot(r, g, color=st["color"], ls=st["linestyle"], label=rf"$T^*={T}$")
    a.axhline(1, color=P.GREY, lw=0.5, zorder=0)
    a.set_xlim(0.8, 4.0); a.set_ylim(0, 3.2)
    a.set_xticks([1, 2, 3, 4]); a.set_yticks([0, 1, 2, 3])
    a.set_xlabel(r"$r/\sigma$"); a.set_ylabel(r"$g(r)$")
    a.legend(loc="upper right")

    # (b) MSD log-log + slope guides ---------------------------------------------
    for (T, y), st in zip(msd.items(), cols):
        b.loglog(t, y, color=st["color"], ls=st["linestyle"], label=rf"$T^*={T}$")
    scales.slope_guide(b, 20.0, 400.0, 0.9, 1, r"$\propto t$", side="end")      # diffusive reference slope
    b.set_xlim(0.1, 1e3); b.set_ylim(1e-4, 1e4)
    b.set_xticks([1e-1, 1e1, 1e3]); b.set_yticks([1e-3, 1e0, 1e3])
    b.minorticks_off()
    b.set_xlabel(r"$t\,/\,\tau$"); b.set_ylabel(r"$\langle \Delta r^2\rangle\,/\,\sigma^2$")
    b.legend(loc="lower right")

    # (c) raw in grey, mean in colour (rule 6: colour only where it carries meaning) --
    w = 100
    mean = np.convolve(temp, np.ones(w) / w, mode="valid")
    d.plot(tt, temp, color=P.GREY, lw=0.5, rasterized=True, label="raw")
    d.plot(tt[w // 2: w // 2 + mean.size], mean, color=P.categorical(2)[1], lw=1.3,
           label="running mean")
    d.set_xlim(0, 50); d.set_ylim(0.6, 2.1)
    d.set_xticks([0, 25, 50]); d.set_yticks([0.6, 1.2, 1.8])
    d.set_xlabel(r"$t\,/\,\tau$"); d.set_ylabel(r"$T^*$")
    d.legend(loc="upper right", ncol=2, columnspacing=1.0, handlelength=1.4)

    layout.panel_labels(c.fig, [a, b, d], titles=["Structure", "Dynamics", "Thermostat"])
    issues = layout.qa(c.fig)
    return c.save(OUT / "md_line_panels"), issues


if __name__ == "__main__":
    print(main())
