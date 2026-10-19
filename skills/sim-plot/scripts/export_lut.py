"""Export exact Crameri/Matplotlib samples as a ParaView RGB preset on [0,1]."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from simviz import get_cmap, load_theme


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cmap", default=load_theme()["colors"]["sequential"])
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    if args.cmap.endswith("S"):
        raise ValueError("Categorical maps are not continuous scalar-field LUTs.")
    if args.output.exists() and not args.overwrite:
        raise FileExistsError(args.output)
    cmap = get_cmap(args.cmap)
    t = np.linspace(0, 1, cmap.N)
    points = np.column_stack((t, cmap(t)[:, :3])).ravel().tolist()
    preset = [{"Name": "simviz-" + args.cmap, "ColorSpace": "RGB",
               "RGBPoints": points, "NanColor": [0.9, 0.9, 0.9]}]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(preset, indent=2), encoding="utf-8")
    print(f"Saved {cmap.N} samples as {preset[0]['Name']}. "
          "Only the normalized linear LUT is exported, not a nonlinear scalar norm.")

if __name__ == "__main__":
    main()
