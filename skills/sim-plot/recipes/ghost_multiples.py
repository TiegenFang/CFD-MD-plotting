"""Small multiples with ghost series: Cd(t) for a Reynolds-number sweep (Rougier rule 8).

Nine cases do not fit a categorical palette (cap = 6). Instead of nine hues, every panel shows
ONE case in colour and all others as pale ghosts, on shared axes. Colour here encodes the
ordered parameter (Re) through one shared map, so the panels remain comparable.
DATA IS SYNTHETIC. Contract: {case: (t, Cd)}.
"""
from _common import OUT
import numpy as np

from scivis import style, layout, palettes as P
from scivis.encodings import ordered_colors


def synthetic(seed=2):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 120, 600)
    res = [40, 60, 80, 100, 150, 200, 300, 500, 1000]
    out = {}
    for re in res:
        St = 0.12 + 0.08 * (1 - np.exp(-re / 150))
        amp = 0.0 if re <= 47 else 0.18 * (1 - 47 / re) ** 0.5
        cd = 1.55 - 0.25 * np.log10(re / 40) + amp * np.sin(2 * np.pi * St * t) * (1 - np.exp(-t / 25))
        cd += 0.004 * rng.standard_normal(t.size) * (re / 200) ** 0.5 - 0.3 * np.exp(-t / 6)
        out[f"Re={re}"] = (t, cd)
    return res, out


def main():
    style.apply_style("paper")
    res, data = synthetic()
    cols = ordered_colors(res, limits=(40, 1000), segment=(0.0, 0.72), cmap="batlow")
    c, axes = layout.small_multiples(data, ncols=3, width="double", cell_aspect=0.55,
                                     xlabel=r"$t\,U/D$", ylabel=r"$C_d$",
                                     colors=dict(zip(data, cols)), ylim=(0.9, 1.9))
    for a in axes:
        a.set_xticks([0, 60, 120])
    issues = layout.qa(c.fig, expect_width_mm=183)
    return c.save(OUT / "ghost_multiples"), issues


if __name__ == "__main__":
    print(main())
