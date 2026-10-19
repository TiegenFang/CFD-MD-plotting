"""Explicit palette-selection aid. Never run automatically for ordinary figure jobs."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'skills/sim-plot/scripts'))
from simviz import style_context, get_palette, export_figure


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--allow-font-fallback', action='store_true')
    ap.add_argument('--overwrite', action='store_true')
    args = ap.parse_args()
    with style_context(allow_font_fallback=args.allow_font_fallback) as state:
        fig, ax = plt.subplots(figsize=(183/25.4, 102/25.4))
        fig.subplots_adjust(left=.025, right=.98, bottom=.07, top=.98)
        ax.set(xlim=(0, 8.2), ylim=(0, 4.3))
        ax.set_axis_off()  # Swatch legend only, not a quantitative data plot.
        ax.text(0, 4.1, 'LOW-SATURATION PALETTES', fontsize=12, weight='bold', va='top')
        descriptions = {'muted': 'Balanced / default', 'cool': 'Cool grey tones', 'earth': 'Warm grey tones'}
        for j, name in enumerate(descriptions):
            y = 3.10 - j*1.08
            ax.text(0, y+.17, name, fontsize=11, weight='bold')
            ax.text(0, y-.12, descriptions[name], fontsize=7.5)
            for i, color in enumerate(get_palette(name, state['theme'])):
                x = 2.1 + i*1.0
                ax.add_patch(Rectangle((x, y-.01), .84, .34, facecolor=color, linewidth=0))
                ax.plot([x+.07, x+.77], [y-.19, y-.19], color=color, linewidth=1.3)
                ax.plot([x+.42], [y-.19], marker=state['theme']['markers'][i], markersize=4.4,
                        markerfacecolor='white', markeredgecolor=color, markeredgewidth=.8)
                ax.text(x+.42, y-.40, color, fontsize=7.5, ha='center', va='top')
        ax.text(0, .06, 'Custom categorical palettes. Use shape or line-style redundancy; no CVD certification implied.', fontsize=7.5)
        export_figure(fig, ROOT/'previews/palette-guide', state,
                      provenance={'purpose':'palette selection guide', 'data':'no scientific data',
                                  'palettes':['muted','cool','earth']}, allow_overwrite=args.overwrite)
        plt.close(fig)

if __name__ == '__main__':
    main()
