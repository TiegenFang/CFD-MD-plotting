"""One focused maintainer check. Not automatically run during ordinary plotting."""
from __future__ import annotations
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "skills" / "sim-plot" / "scripts"))
from simviz import make_norm, field_status, get_cmap, style_context, new_figure, get_palette, categorical_styles, scatter_style, ordered_colors
import matplotlib.pyplot as plt


def rejects(fn, exc=ValueError):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"Expected {exc.__name__}")


def main():
    checks = []
    for p in ROOT.rglob("*.py"):
        ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
    for p in ROOT.rglob("*.json"):
        json.loads(p.read_text(encoding="utf-8"))
    checks.append("Python/JSON parse")
    np.testing.assert_allclose(make_norm("symmetric", -2, 2)([-2, 0, 2]), [0, .5, 1])
    np.testing.assert_allclose(make_norm("two-slope", -1, 3)([-1, 0, 3]), [0, .5, 1])
    np.testing.assert_allclose(make_norm("log", 1, 100)([1, 10, 100]), [0, .5, 1])
    rejects(lambda: make_norm("symmetric", -1e-12, 2e-12))
    rejects(lambda: make_norm("log", 0, 100))
    rejects(lambda: make_norm("linear", 1, 1))
    rejects(lambda: make_norm("symlog", -1, 1))
    rejects(lambda: field_status([0, 1], make_norm("log", .1, 10)))
    s = field_status([-2, 0, 2, np.nan], make_norm("linear", -1, 1))
    assert s["extend"] == "both" and s["n_masked"] == 1
    checks.append("Normalization and nonpositive/missing/range guards")
    cm_installed = importlib.util.find_spec("cmcrameri") is not None
    if cm_installed:
        assert get_cmap("cmc.batlow").N >= 100
        checks.append("cmcrameri import and palette retrieval")
    else:
        rejects(lambda: get_cmap("cmc.batlow"), RuntimeError)
        checks.append("Missing cmcrameri refuses silent replacement")
    # Validate fonts in one controlled context. This does not claim Arial exists.
    with style_context(allow_font_fallback=True) as st:
        actual_font = st["font_resolved"]
    if actual_font != "Arial":
        def strict_font():
            with style_context():
                pass
        rejects(strict_font, RuntimeError)
        checks.append("Missing Arial strict-mode guard")
    with style_context(allow_font_fallback=True) as st:
        fig, ax = new_figure(st)
        assert all(spine.get_visible() for spine in ax.spines.values())
        assert ax.xaxis.get_major_ticks()[0].tick2line.get_visible()
        assert ax.yaxis.get_major_ticks()[0].tick2line.get_visible()
        assert not ax.xaxis.get_major_ticks()[0].label2.get_visible()
        assert not ax.yaxis.get_major_ticks()[0].label2.get_visible()
        kw = scatter_style("#5B7C99", st)
        assert kw["facecolors"] == "none" and kw["alpha"] == 1
        assert scatter_style("#5B7C99", st, {"preset":"dense"})["edgecolors"] == "none"
        for name in ["muted", "cool", "earth"]:
            assert len(get_palette(name, st["theme"])) == 6
        reg = {"A":{"color":"#112233", "marker":"o"}}
        assert categorical_styles(["A"], st, reg, palette="earth")["A"]["color"] == "#112233"
        rejects(lambda: get_palette("unknown", st["theme"]))
        rejects(lambda: scatter_style("#5B7C99", st, {"preset":"hollow", "area":0}))
        plt.close(fig)
    for name in ["cmc.oslo", "cmc.oslo_r", "cmc.vik"]:
        assert get_cmap(name).N == 256
        assert get_cmap(name)._simviz_source["provider"] == "archived cmcrameri RGB table"
    c = ordered_colors([1,1.5,3], limits=(1,3), segment=(.35,.82))
    np.testing.assert_allclose(c[1], get_cmap("cmc.oslo_r")(.35+(.82-.35)*.25))
    checks.append("Boxed axes/mirrored ticks, named palettes, scatter presets, registry precedence, archived Crameri LUTs and numeric sweep mapping")
    with tempfile.TemporaryDirectory(prefix="simviz-check-") as td:
        td = Path(td)
        np.savez(td / "mesh.npz", x=[0,1,0,2,3,2], y=[0,0,1,0,0,1],
                 triangles=[[0,1,2],[3,4,5]], values=[.2,.8], triangle_mask=[True,False])
        cfg = {"source_id":"synthetic disconnected mesh", "data":"mesh.npz", "grid":"triangular",
               "association":"cell", "method":"tripcolor", "units":"dimensionless",
               "coordinate_units":"dimensionless", "domain_description":"Two disconnected triangles, first excluded",
               "limits":[0,1], "cmap":"viridis", "xlabel":"x", "ylabel":"z", "colorbar_label":"s",
               "output":"mesh", "formats":["png"], "synthetic":True}
        p = td / "case.json"
        p.write_text(json.dumps(cfg))
        cmd = [sys.executable, str(ROOT / "skills/sim-field/scripts/render_field.py"), str(p), "--allow-font-fallback"]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        report = json.loads((td / "mesh.viz.json").read_text())
        assert report["provenance"]["field_statistics"]["masked_triangles"] == 1
        checks.append("Native cell-triangle field and mask integration")
        # Same geometry, now true nodal data with a mask; no generated connectivity.
        np.savez(td / "mesh.npz", x=[0,1,0,2,3,2], y=[0,0,1,0,0,1],
                 triangles=[[0,1,2],[3,4,5]], values=[.1,.2,.3,.4,.8,.5], mask=[True,False,False,False,False,False])
        cfg.update(association="point", method="tricontourf", levels=[0,.25,.5,.75,1], output="points")
        p.write_text(json.dumps(cfg))
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        report = json.loads((td / "points.viz.json").read_text())
        assert report["provenance"]["field_statistics"]["masked_triangles"] == 1
        checks.append("Native nodal triangle contour and invalid-node masking")
        lut = td / "viridis.json"
        subprocess.run([sys.executable, str(ROOT / "skills/sim-plot/scripts/export_lut.py"),
                        "--cmap", "viridis", "--output", str(lut)], check=True, capture_output=True)
        points = json.loads(lut.read_text())[0]["RGBPoints"]
        assert len(points) == get_cmap("viridis").N * 4
        assert points[0] == 0 and points[-4] == 1
        checks.append("Normalized ParaView LUT serialization; not ParaView import execution")
        subprocess.run([sys.executable, str(ROOT / "install.py"), "--scope", "project", "--root", str(td),
                        "--apply"], check=True, capture_output=True)
        assert (td / ".omp/skills/sim-field/SKILL.md").exists()
        assert (td / ".omp/skills/sim-plot/scripts/simviz.py").exists()
        result = subprocess.run([sys.executable, str(ROOT / "install.py"), "--scope", "project", "--root", str(td),
                                 "--apply"], capture_output=True)
        assert result.returncode != 0
        checks.append("Sibling installation and non-overwrite protection")
    print(json.dumps({"checks": checks, "resolved_font": actual_font, "cmcrameri_installed": cm_installed,
                      "not_tested": ["ParaView/VMD runtime", "real CFD/MD files", "OMP/Codex live discovery", "journal compliance"]}, indent=2))

if __name__ == "__main__":
    main()
