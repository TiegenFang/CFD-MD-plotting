"""Shared bootstrap for the recipes: import path to scivis (lives in sim-plot), output folder."""
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "sim-plot" / "scripts"
sys.path.insert(0, str(SCRIPTS))
OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(exist_ok=True)

import matplotlib
matplotlib.use("Agg")
