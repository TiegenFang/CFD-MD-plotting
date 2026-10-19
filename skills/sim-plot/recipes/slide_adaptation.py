"""Rule 3 (adapt to the medium): the SAME MD data as md_line_panels, rebuilt for a slide.

Not a scaled paper figure: two panels instead of three, 14 pt type, thicker lines, no minor
ticks, DIRECT end labels instead of a legend box in panel b (opt-in; the paper default stays a framed
legend); panel a keeps a frameless legend because its curves converge. Build for the final physical size of the slide region (here 254 x 100 mm).
"""
from _common import OUT
import numpy as np

from scivis import style, layout, palettes as P
from md_line_panels import synthetic_md


def main():
    style.apply_style("slide")
    r, states, t, msd, tt, temp = synthetic_md()
    cols = P.redundant_encoding(3)
    c = layout.make_canvas("slide", 105, ncols=2, margins=(25.0, 20.0, 24.0, 10.0), wgap=34.0)
    a, b = c.ax(0, 0), c.ax(0, 1)
    items_a, items_b = [], []
    for (T, (g, sd)), st in zip(states.items(), cols):
        a.fill_between(r, g - sd, g + sd, color=st["color"], alpha=0.18, lw=0)
        a.plot(r, g, color=st["color"], ls=st["linestyle"], label=rf"$T^*={T}$")
    for (T, y), st in zip(msd.items(), cols):
        b.loglog(t, y, color=st["color"], ls=st["linestyle"])
        items_b.append((t[-1], y[-1], rf"$T^*={T}$", st["color"]))
    a.set_xlim(0.8, 4.0); a.set_ylim(0, 3.2); a.set_xticks([1, 2, 3, 4]); a.set_yticks([0, 1, 2, 3])
    a.set_xlabel(r"$r/\sigma$"); a.set_ylabel(r"$g(r)$")
    b.set_xlim(0.1, 1e3); b.set_ylim(1e-4, 1e4)
    b.set_xticks([1e-1, 1e1, 1e3]); b.set_yticks([1e-3, 1e0, 1e3]); b.minorticks_off()
    b.set_xlabel(r"$t\,/\,\tau$"); b.set_ylabel(r"$\langle \Delta r^2\rangle\,/\,\sigma^2$")
    a.legend(loc="upper right", frameon=False)       # curves converge: direct labels would collide
    layout.end_labels(b, items_b, pad_pt=6)
    layout.panel_labels(c.fig, [a, b], titles=["Structure", "Dynamics"])
    issues = layout.qa(c.fig, expect_width_mm=254)
    return c.save(OUT / "slide_adaptation"), issues


if __name__ == "__main__":
    print(main())
