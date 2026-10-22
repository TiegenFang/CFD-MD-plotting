"""One export pass: exact canvas size, QA gate, sidecar provenance, caption stub."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
from typing import Any, Sequence

import matplotlib as mpl
import numpy as np

from . import layout
from .captions import caption_stub
from .readme_zh import readme_zh

VERSION = "1.0.0"
BLOCKING = {"clipped", "cbar", "tiny", "cjk-math", "font", "size"}


def _json_value(value):
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def export_figure(fig, stem: str | Path, state: dict, *, provenance: dict[str, Any],
                  formats: Sequence[str] | None = None, dpi: int | None = None,
                  allow_overwrite: bool = False, kind: str = "figure", fit_margins: bool = True,
                  expect_width_mm: float | None = None, readme: bool = True) -> dict:
    """Blocking QA codes (clipped/cbar/tiny/cjk-math/font/size) raise; overlap and legend
    findings are written to the sidecar for review. Never an unbounded fix loop."""
    stem = Path(stem)
    theme = state["theme"]
    formats = list(formats or theme["export"]["formats"])
    if not formats or any(f not in {"pdf", "svg", "png", "tiff"} for f in formats):
        raise ValueError("Supported export formats: pdf, svg, png, tiff.")
    dpi = dpi or theme["export"]["dpi"]
    targets = [Path(str(stem) + "." + f) for f in formats]
    sidecar = Path(str(stem) + ".viz.json")
    caption = Path(str(stem) + ".caption.txt")
    readme_path = Path(str(stem) + ".README.zh-CN.md")
    if not allow_overwrite and any(p.exists() for p in targets + [sidecar, caption] + ([readme_path] if readme else [])):
        raise FileExistsError("Output exists. Reuse the canonical output only with explicit overwrite.")
    stem.parent.mkdir(parents=True, exist_ok=True)
    canvas = getattr(fig, "_scivis_canvas", None)
    if fit_margins and canvas is not None and getattr(canvas, "autofit", False):
        canvas.fit_margins()
    issues = layout.qa(fig, verbose=False, expect_width_mm=expect_width_mm)
    blocking = [f"{c}: {d}" for c, d in issues if c in BLOCKING]
    if blocking:
        raise ValueError("Fix these final-canvas issues before export: " + " | ".join(blocking))
    for path in targets:
        fig.savefig(path, dpi=dpi, bbox_inches=None)
    versions = {"numpy": np.__version__, "matplotlib": mpl.__version__}
    try:
        versions["cmcrameri"] = importlib.metadata.version("cmcrameri")
    except importlib.metadata.PackageNotFoundError:
        versions["cmcrameri"] = "not installed"
    sizes = {p.name: p.stat().st_size for p in targets}
    report = {"kit_version": VERSION, "profile": state["profile"], "medium": state["medium"],
              "font_requested": state["font_requested"], "font_resolved": state["font_resolved"],
              "font_fallback_used": state["font_fallback_used"], "math_fallback": state["math_fallback"],
              "font_note": state["font_note"], "size_mm": (fig.get_size_inches() * 25.4).tolist(),
              "raster_dpi": dpi, "versions": versions, "axis_style": theme["axes"],
              "categorical_palette": theme["colors"]["categorical"],
              "theme_sha256": hashlib.sha256(json.dumps(theme, sort_keys=True).encode()).hexdigest(),
              "outputs": [p.name for p in targets], "file_bytes": sizes, "provenance": provenance,
              "qa": {"blocking": "passed",
                     "non_blocking": [f"{c}: {d}" for c, d in issues if c not in BLOCKING],
                     "visual_review": "not automated", "scientific_validation": "not implied",
                     "journal_compliance": "not assessed"}}
    sidecar.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False, default=_json_value),
                       encoding="utf-8")
    caption.write_text(caption_stub(provenance, kind=kind), encoding="utf-8")
    report["caption"] = caption.name
    if readme and provenance.get("readme", True) is not False and (provenance.get("config") or {}).get("readme", True) is not False:
        readme_path.write_text(readme_zh(fig, provenance, report, kind=kind, stem=str(stem)), encoding="utf-8")
        report["readme_zh"] = readme_path.name
    return report
