"""Generate synthetic calibration examples once. Not part of normal figure tasks."""
from __future__ import annotations
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = Path(__file__).resolve().parent


def write_json(name, config):
    p = BASE / f"{name}.json"
    p.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def write_csv(name, columns, rows):
    p = BASE / f"{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        w.writerows(rows)
    return p.name


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--portable-colors", action="store_true", help="Explicitly use built-in maps instead of cmcrameri.")
    ap.add_argument("--allow-font-fallback", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    if not args.overwrite and (BASE / "line.json").exists():
        raise FileExistsError("Demo source data already exist. Use --overwrite only for an intentional rebuild.")
    seq = "viridis" if args.portable_colors else "cmc.oslo_r"
    div = "coolwarm" if args.portable_colors else "cmc.vik"
    common = {"profile": "paper", "synthetic": True, "formats": ["pdf", "svg", "png"]}
    configs = []
    t = np.linspace(0, 4, 61)
    rows = []
    for k, name in enumerate(["Model A", "Model B", "Model C"]):
        vals = (1 + 0.28 * k) * (1 - np.exp(-t / (0.48 + 0.18 * k))) + 0.035 * np.sin(6 * t + k)
        for i, (x, y) in enumerate(zip(t, vals)):
            if k == 1 and 24 <= i <= 27:
                rows.append([x, "", name, "", ""])
            else:
                rows.append([x, y, name, y - 0.055, y + 0.055])
    data = write_csv("line", ["time", "response", "model", "lower", "upper"], rows)
    cfg = {**common, "kind": "line", "data": data, "x": "time", "y": "response", "group": "model",
           "xlabel": r'$t/t_0$', "ylabel": r'$I/I_0$', "output": "../previews/line",
           "markers": True, "markevery": 8, "legend_loc": "lower right",
           "uncertainty": {"lower": "lower", "upper": "upper", "definition": "Synthetic fixed envelope, not a statistical CI", "display": "band"}}
    configs.append(("plot", write_json("line", cfg)))
    rng = np.random.default_rng(61019)
    rows = []
    for k, name in enumerate(["Case A", "Case B", "Case C"]):
        x = rng.uniform(0.1, 1, 36)
        y = (0.7 + 0.15 * k) * x + rng.normal(0, 0.06, len(x))
        rows.extend(zip(x, y, [name] * len(x)))
    data = write_csv("scatter", ["x", "y", "case"], rows)
    cfg = {**common, "kind": "scatter", "data": data, "x": "x", "y": "y", "group": "case",
           "xlabel": r'$x/x_0$', "ylabel": r'$y/y_0$', "output": "../previews/scatter", "legend_loc": "upper left",
           "color_encoding": {"mode":"categorical", "palette":"muted"}, "scatter":{"preset":"hollow"}}
    configs.append(("plot", write_json("scatter", cfg)))
    rows = []
    for k, name in enumerate(["Model A", "Model B", "Model C"]):
        for j, c in enumerate(["Mode 1", "Mode 2", "Mode 3"]):
            val = 0.28 + 0.13 * j + 0.08 * k
            rows.append([c, val, name, val - 0.028, val + 0.028])
    data = write_csv("bars", ["mode", "response", "model", "lower", "upper"], rows)
    cfg = {**common, "kind": "bar", "data": data, "x": "mode", "y": "response", "group": "model",
           "xlabel": "Operating mode", "ylabel": r'$Q/Q_0$', "output": "../previews/bars", "ylim": [0, 0.85],
           "legend_loc": "upper left", "legend_columns": 3, "legend_bbox": [0,1.15],
           "uncertainty": {"lower": "lower", "upper": "upper", "definition": "Synthetic bounds, not an estimated CI"}}
    configs.append(("plot", write_json("bars", cfg)))
    # Cell edges are deliberately nonuniform. The circular hole is an explicit excluded domain.
    x = 2 * np.sign(np.linspace(-1, 1, 101)) * np.abs(np.linspace(-1, 1, 101)) ** 1.3
    y = np.linspace(-1.2, 1.2, 81)
    X, Y = np.meshgrid((x[1:] + x[:-1]) / 2, (y[1:] + y[:-1]) / 2)
    z = np.exp(-((X - 0.45) ** 2 / 0.3 + Y ** 2 / 0.5)) + 0.28 * np.exp(-((X + 1) ** 2 + (Y - 0.6) ** 2) / 0.35)
    mask = (X + 0.35) ** 2 + Y ** 2 < 0.27 ** 2
    theta = np.linspace(0, 2 * np.pi, 160)
    boundary = np.column_stack((-0.35 + 0.27 * np.cos(theta), 0.27 * np.sin(theta)))
    np.savez_compressed(BASE / "field_cell.npz", x=x, y=y, values=z, mask=mask, boundary_xy=boundary)
    field_common = {**common, "source_id": "make_demo.py synthetic analytic field",
                    "grid": "rectilinear", "units": "dimensionless", "coordinate_units": "dimensionless",
                    "domain_description": "Synthetic rectangle with an explicitly masked circular hole. No CFD/MD inference.",
                    "xlabel": r'$x/\ell_0$', "ylabel": r'$z/\ell_0$', "height_mm": 52,
                    "colorbar_label": r'$s/s_0$'}
    cfg = {**field_common, "data": "field_cell.npz", "association": "cell", "method": "pcolormesh",
           "limits": [0, 1], "cmap": seq, "output": "../previews/field_cell", "ticks": [0, 0.5, 1]}
    configs.append(("field", write_json("field_cell", cfg)))
    X, Y = np.meshgrid(x, y)
    z = np.exp(-((X - 0.5) ** 2 + Y ** 2) / 0.34) - np.exp(-((X + 0.6) ** 2 + Y ** 2) / 0.48)
    mask = X ** 2 + (Y + 0.45) ** 2 < 0.2 ** 2
    boundary = np.column_stack((0.2 * np.cos(theta), -0.45 + 0.2 * np.sin(theta)))
    np.savez_compressed(BASE / "field_contour.npz", x=x, y=y, values=z, mask=mask, boundary_xy=boundary)
    cfg = {**field_common, "data": "field_contour.npz", "association": "point", "method": "contourf",
           "scale": "symmetric", "reference_description": "Analytic zero of a synthetic signed scalar",
           "limits": [-1, 1], "cmap": div, "levels": np.linspace(-1, 1, 21).tolist(),
           "output": "../previews/field_contour", "ticks": [-1, 0, 1]}
    configs.append(("field", write_json("field_contour", cfg)))
    for kind, config in configs:
        script = ROOT / "skills" / ("sim-plot" if kind == "plot" else "sim-field") / "scripts" / f"render_{kind}.py"
        cmd = [sys.executable, str(script), str(config)]
        if args.allow_font_fallback:
            cmd.append("--allow-font-fallback")
        if args.overwrite:
            cmd.append("--overwrite")
        subprocess.run(cmd, check=True)

if __name__ == "__main__":
    main()
