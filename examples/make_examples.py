"""Synthetic examples for the multiples and overlay features: kind=multiples and a field with streamlines + zoom."""
from __future__ import annotations
import csv
import json
from pathlib import Path
import numpy as np

BASE = Path(__file__).resolve().parent


def multiples():
    res = [40, 60, 80, 100, 150, 200, 300, 500, 1000]
    t = np.linspace(0, 120, 241)
    rng = np.random.default_rng(2)
    rows = []
    for re in res:
        St = 0.12 + 0.08 * (1 - np.exp(-re / 150))
        amp = 0.0 if re <= 47 else 0.18 * (1 - 47 / re) ** 0.5
        cd = 1.55 - 0.25 * np.log10(re / 40) + amp * np.sin(2 * np.pi * St * t) * (1 - np.exp(-t / 25))
        cd += 0.004 * rng.standard_normal(t.size) - 0.3 * np.exp(-t / 6)
        rows += [[f"Re={re}", f"{a:.4f}", f"{b:.5f}"] for a, b in zip(t, cd)]
    with (BASE / "multiples.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["case", "t", "cd"]); w.writerows(rows)
    cfg = {"profile": "paper", "synthetic": True, "formats": ["pdf", "png"], "kind": "multiples",
           "data": "multiples.csv", "x": "t", "y": "cd", "group": "case",
           "xlabel": "$t\\,U/D$", "ylabel": "$C_d$", "ncols": 3, "cell_aspect": 0.55,
           "ylim": [0.9, 1.9], "width_mm": 183, "output": "../previews/multiples",
           "color_encoding": {"mode": "ordered", "cmap": "cmc.batlow", "segment": [0.0, 0.72],
                               "limits": [40, 1000], "values": {f"Re={r}": r for r in res}}}
    (BASE / "multiples.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")


def wake():
    nx, ny = 240, 120
    xe = np.linspace(-1.5, 4.5, nx + 1); ye = np.linspace(-1.5, 1.5, ny + 1)
    xc = 0.5 * (xe[1:] + xe[:-1]); yc = 0.5 * (ye[1:] + ye[:-1])
    X, Y = np.meshgrid(xc, yc)
    R = 0.5
    r2 = X**2 + Y**2
    u = 1 - R**2 * (X**2 - Y**2) / r2**2
    v = -2 * R**2 * X * Y / r2**2
    om = np.zeros_like(X)
    for k, xv in enumerate(np.arange(0.9, 4.4, 0.95)):
        g = (-1) ** k * 2.2; yv = 0.28 * (-1) ** k; rc = 0.12 + 0.045 * (xv - 0.9)
        dx, dy = X - xv, Y - yv
        rr2 = dx**2 + dy**2 + 1e-12
        f = g / (2 * np.pi * rr2) * (1 - np.exp(-rr2 / rc**2))
        u += -dy * f; v += dx * f; om += g / (np.pi * rc**2) * np.exp(-rr2 / rc**2)
    solid = r2 <= R**2
    for a in (u, v, om):
        a[solid] = np.nan
    th = np.linspace(0, 2 * np.pi, 200)
    np.savez(BASE / "field_wake.npz", x=xe, y=ye, values=om, xc=xc, yc=yc, u=u, v=v,
             boundary_xy=np.c_[R * np.cos(th), R * np.sin(th)])
    cfg = {"profile": "paper", "synthetic": True, "formats": ["pdf", "png"],
           "source_id": "make_examples.py synthetic potential flow + Lamb-Oseen street",
           "grid": "rectilinear", "association": "cell", "method": "pcolormesh", "data": "field_wake.npz",
           "units": "U_inf/D", "coordinate_units": "D",
           "domain_description": "Rectangle with the cylinder interior (NaN) masked; synthetic, no CFD inference.",
           "xlabel": "$x/D$", "ylabel": "$y/D$", "colorbar_label": "$\\omega_z D/U_\\infty$",
           "scale": "symmetric", "limits": [-12, 12], "reference_description": "zero spanwise vorticity",
           "width_mm": 120, "streamlines": {"u": "u", "v": "v", "x": "xc", "y": "yc", "seeds": "inlet", "density": 1.0},
           "zoom": {"xlim": [0.6, 2.2], "ylim": [-0.45, 0.45], "width_mm": 24, "anchor": "upper right"},
           "halo_text": [{"x": 4.42, "y": -1.42, "text": "synthetic data", "ha": "right"}],
           "output": "../previews/field_wake"}
    (BASE / "field_wake.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")


if __name__ == "__main__":
    multiples(); wake()
