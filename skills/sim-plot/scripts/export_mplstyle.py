"""Write assets/styles/{paper,slide,poster}.mplstyle from theme.json (single source of truth).

    python export_mplstyle.py            # (re)generate
    python export_mplstyle.py --check    # exit 1 if the files are stale

Use:  plt.style.use("<skill>/assets/styles/paper.mplstyle")
The files carry typography, spines, ticks, legend and colour-cycle only; canvas size, tick
locators and colourbar placement need ``scivis.layout`` (they cannot live in rcParams).
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scivis import theme as T  # noqa: E402

SKIP = {"figure.dpi", "savefig.bbox", "figure.constrained_layout.use", "path.simplify", "font.family"}


def fmt(v):
    if isinstance(v, bool):
        return str(v)
    if isinstance(v, (list, tuple)):
        return ", ".join(str(i) for i in v)
    return str(v)


def render(medium: str) -> str:
    theme = T.load_theme()
    m = T.media_of(theme, medium)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        # Not tied to the installed fonts: the .mplstyle lists the whole stack.
        rc = T.build_rc(theme, m, theme["font"]["preferred"])
    rc["font.sans-serif"] = [theme["font"]["preferred"], *theme["font"]["fallbacks"]]
    rc["font.family"] = "sans-serif"
    rc.pop("axes.prop_cycle")
    rc["image.cmap"] = "viridis"      # deterministic: batlow needs cmcrameri registered first (scivis does that)
    lines = [f"# {medium}.mplstyle - GENERATED from assets/theme.json by export_mplstyle.py. Do not edit.",
             "axes.prop_cycle: cycler('color', [" + ", ".join(
                 repr(c.lstrip('#')) for c in __import__('scivis.palettes', fromlist=['x']).palette(
                     theme['colors']['categorical'], theme)[:6]) + "])"]
    for k in sorted(rc):
        if k in SKIP:
            continue
        v = rc[k]
        if isinstance(v, str) and v.startswith("#"):
            v = v.lstrip("#")
        lines.append(f"{k}: {fmt(v)}")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    out = T.ASSETS / "styles"
    out.mkdir(exist_ok=True)
    stale = []
    for medium in ("paper", "slide", "poster"):
        text = render(medium)
        p = out / f"{medium}.mplstyle"
        if a.check:
            if not p.exists() or p.read_text(encoding="utf-8") != text:
                stale.append(p.name)
        else:
            p.write_text(text, encoding="utf-8")
    if a.check and stale:
        print("stale:", stale)
        return 1
    print("ok", "(checked)" if a.check else "(written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
