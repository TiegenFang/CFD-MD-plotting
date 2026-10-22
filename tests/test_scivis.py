"""Run: python -m pytest tests -q   (SCIVIS_ALLOW_FONT_FALLBACK=1 on machines without Arial)."""
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "sim-plot" / "scripts"
sys.path.insert(0, str(SCRIPTS))
os.environ.setdefault("SCIVIS_ALLOW_FONT_FALLBACK", "1")     # CI/Linux: draft fonts are fine for logic tests

import matplotlib
matplotlib.use("Agg")
import matplotlib as mpl

import scivis
from scivis import palettes as P, audit, theme, layout, scales, fields, captions, io_foam, encodings
from scivis.norms import make_norm, field_status


@pytest.fixture(autouse=True)
def _quiet_and_reset():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield
    scivis.reset_style()


# ------------------------------------------------------------------ colour
@pytest.mark.parametrize("bad", ["jet", "rainbow", "turbo", "hsv", "Spectral", "npg", "jco", "nejm"])
def test_banned(bad):
    with pytest.raises(ValueError):
        P.get_cmap(bad)


def test_tol_rainbow_restricted():
    with pytest.raises(ValueError):
        P.get_cmap("rainbow_PuRd")
    assert P.get_cmap("rainbow_PuRd", allow_restricted=True) is not None


def test_categorical_limits_and_palette_names():
    assert len(P.categorical(6)) == 6
    with pytest.raises(ValueError):
        P.categorical(7, "bright")
    th = theme.load_theme()
    assert len(P.palette("tol-bright", th)) == 6 and len(P.palette("muted", th)) == 6
    with pytest.raises(ValueError):
        P.palette("nope", th)


def test_signed_centre_white_and_symmetric_norm():
    cm = P.get_cmap("signed")
    assert np.allclose(cm(0.5)[:3], 1.0, atol=1e-3)
    n = P.diverging_norm(np.array([-3.0, 0.5, 1.0]), center=0.0)
    assert n.vmin == -3.0 and n.vmax == 3.0 and abs(n(0.0) - 0.5) < 1e-9
    assert not np.allclose(P.get_cmap("signed", white_center=False)(0.5)[:3], 1.0, atol=1e-3)


def test_norm_guards_constant_and_empty():
    with pytest.raises(ValueError):
        P.diverging_norm(np.zeros(5))
    with pytest.raises(ValueError):
        P.diverging_norm(np.full(4, np.nan))
    with pytest.raises(ValueError):
        P.sequential_norm(np.ones(5))
    assert P.sequential_norm(np.ones(5), vmin=0, vmax=2).vmax == 2


def test_density_role_trims_top_and_records_source():
    cm = P.get_cmap("density")
    assert cm._source["segment"] == [0.0, 0.88] and cm._source["role"] == "density"
    assert cm(1.0)[:3] != (1.0, 1.0, 1.0)


def test_archived_tables_work_without_package_and_are_hash_checked():
    cm = P.get_cmap("cmc.oslo_r")
    assert cm.N == 256 and cm._source["provider"] == "archived cmcrameri RGB table"
    assert cm._source["reversed"] is True


def test_roles_pass_audit():
    for role, r in P.ROLES.items():
        fn = {"sequential": audit.audit_sequential, "diverging": audit.audit_diverging,
              "cyclic": audit.audit_cyclic}[r.kind]
        res = fn(P._lookup(r.default) if r.kind != "diverging" else P.get_cmap(r.default))
        assert all(res["pass"].values()), (role, r.default, res["pass"])


def test_tol_hex_matches_package():
    assert audit.check_tol_hex_against_package() == []


def test_lab_ramp_and_colour_stack():
    cm = P.lab_ramp(["#08306B", "#F7FBFF"])
    L = P.rgb_to_lab(cm(np.linspace(0, 1, 50))[:, :3])[:, 0]
    assert np.all(np.diff(L) > -0.5) and L[0] < 25 and L[-1] > 95
    stacks = P.colour_stack(["#4477AA", "#EE6677"], 3)
    assert len(stacks) == 2 and all(len(s) == 3 for s in stacks)
    assert len({c for s in stacks for c in s}) == 6


def test_nice_ticks_include_centre():
    t = P.nice_symmetric_ticks(2.7, nbins=4)
    assert 0.0 in t and np.allclose(t, -t[::-1])


# ------------------------------------------------------------------ norms / encodings
def test_make_norm_guards():
    np.testing.assert_allclose(make_norm("symmetric", -2, 2)([-2, 0, 2]), [0, .5, 1])
    for bad in (lambda: make_norm("log", 0, 100), lambda: make_norm("linear", 1, 1),
                lambda: make_norm("symlog", -1, 1), lambda: make_norm("symmetric", -1e-12, 2e-12)):
        with pytest.raises(ValueError):
            bad()
    s = field_status([-2, 0, 2, np.nan], make_norm("linear", -1, 1))
    assert s["extend"] == "both" and s["n_masked"] == 1 and s["clipped_fraction"] == pytest.approx(2 / 3)


def test_scatter_guards_and_registry():
    with theme.style_context("paper") as st:
        assert encodings.scatter_style("#5B7C99", st)["facecolors"] == "none"
        with pytest.raises(ValueError):
            encodings.scatter_style("#5B7C99", st, {"preset": "dense", "alpha": 0.005})
        with pytest.raises(ValueError):
            encodings.scatter_style("#5B7C99", st, n_points=50000)
        assert encodings.scatter_style("#5B7C99", st, {"preset": "dense"}, n_points=50000)["edgecolors"] == "none"
        reg = {"A": {"color": "#112233", "marker": "o"}}
        assert encodings.categorical_styles(["A"], st, reg)["A"]["color"] == "#112233"
        with pytest.raises(ValueError, match="multiples"):
            encodings.categorical_styles([f"c{i}" for i in range(7)], st)


# ------------------------------------------------------------------ theme / style
def test_style_defaults_boxed_framed_legend_and_font_record():
    st = scivis.apply_style()
    rc = mpl.rcParams
    assert st["requested"] == "Arial" and st["font_ok"]
    assert rc["axes.spines.top"] and rc["axes.spines.right"] and rc["xtick.top"] and rc["ytick.right"]
    assert rc["xtick.direction"] == "in" and rc["legend.frameon"] and not rc["legend.fancybox"]
    scivis.apply_style(boxed=False, legend_box=False)
    assert not rc["axes.spines.top"] and not rc["legend.frameon"]


def test_style_does_not_reset_unrelated_rc_and_restores():
    mpl.rcParams["grid.alpha"] = 0.37
    before = mpl.rcParams["font.size"]
    with theme.style_context("paper"):
        assert mpl.rcParams["grid.alpha"] == 0.37
        assert mpl.rcParams["font.size"] == 7.0
    assert mpl.rcParams["font.size"] == before
    mpl.rcParams["grid.alpha"] = mpl.rcParamsDefault["grid.alpha"]


def test_strict_font_policy(monkeypatch):
    monkeypatch.delenv("SCIVIS_ALLOW_FONT_FALLBACK", raising=False)
    if theme.family_present("Arial"):
        pytest.skip("Arial installed: strict failure cannot be provoked")
    with pytest.raises(RuntimeError):
        with theme.style_context("paper"):
            pass
    with theme.style_context("paper", allow_font_fallback=True) as st:
        assert st["font_fallback_used"]


def test_theme_override_unknown_key_rejected(tmp_path):
    p = tmp_path / "o.json"
    p.write_text(json.dumps({"nonsense": 1}))
    with pytest.raises(ValueError):
        theme.load_theme(p)
    p.write_text(json.dumps({"media": {"paper": {"line": 2.0}}}))
    assert theme.load_theme(p)["media"]["paper"]["line"] == 2.0


def test_mplstyle_files_in_sync_and_loadable():
    r = subprocess.run([sys.executable, str(SCRIPTS / "export_mplstyle.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    import matplotlib.pyplot as plt
    with plt.style.context(str(theme.ASSETS / "styles" / "paper.mplstyle")):
        assert mpl.rcParams["axes.spines.top"] and mpl.rcParams["font.size"] == 7.0
        assert mpl.rcParams["axes.prop_cycle"].by_key()["color"][0].lower() == "#4477aa"


# ------------------------------------------------------------------ layout
def test_canvas_exact_size_and_detached():
    import matplotlib.pyplot as plt
    n = len(plt.get_fignums())
    with theme.style_context("paper"):
        c = layout.make_canvas("double", 52, ncols=3)
        assert c.fig.get_size_inches() * 25.4 == pytest.approx([183, 52])
        assert len(plt.get_fignums()) == n
        with pytest.raises(ValueError):
            layout.make_canvas("double", 5, margins=(100, 5, 100, 5))
        with pytest.raises(ValueError):
            layout.make_canvas("huge", 50)


def test_fit_margins_contains_outside_legend():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 66, autofit=True)
        ax = c.ax(0, 0)
        ax.plot([0, 1], [0, 1], label="a")
        ax.legend(loc="upper left", bbox_to_anchor=(0, 1.15), ncol=3)
        assert any(code == "clipped" for code, _ in layout.qa(c.fig, verbose=False))
        c.fit_margins()
        assert layout.qa(c.fig, verbose=False) == []


def test_qa_flags_cjk_math_legend_and_size():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60)
        ax = c.ax(0, 0)
        x = np.linspace(0, 1, 50)
        ax.plot(x, 1 - x, label="line")
        ax.legend(loc="upper left")
        ax.set_xlabel("温度 $T$ (K)")
        codes = {k for k, _ in layout.qa(c.fig, verbose=False, expect_width_mm=100)}
        assert {"cjk-math", "legend", "size"} <= codes


def test_unlabelled_colorbar_flagged():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60, margins=(11, 9, 13, 6))
        ax = c.ax(0, 0, field=True)
        m = ax.imshow(np.random.rand(5, 5))
        layout.add_colorbar(ax, m, "")
        assert any(k == "cbar" for k, _ in layout.qa(c.fig, verbose=False))


def test_small_multiples_shared_limits_and_ghosts():
    t = np.linspace(0, 1, 30)
    data = {f"c{i}": (t, np.sin(3 * t) * (i + 1)) for i in range(7)}      # 7 > categorical cap
    with theme.style_context("paper"):
        c, axes = layout.small_multiples(data, ncols=3, xlabel="t", ylabel="y")
        assert len(axes) == 7
        assert all(a.get_ylim() == axes[0].get_ylim() for a in axes)
        assert all(len(a.get_lines()) == 7 for a in axes)                   # 1 coloured + 6 ghosts
        assert layout.qa(c.fig, verbose=False) == []
        with pytest.raises(ValueError):
            layout.small_multiples({"a": (t, t)})


def test_zoom_inset_shares_artist_and_marginals():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60)
        ax = c.ax(0, 0, field=True)
        X, Y = np.meshgrid(np.linspace(0, 1, 20), np.linspace(0, 1, 20))
        draw = lambda a: a.pcolormesh(X, Y, X + Y, vmin=0, vmax=2)
        draw(ax)
        ins = layout.zoom_inset(ax, (0.2, 0.4), (0.2, 0.4), draw, width_mm=20)
        assert ins._scivis_zoom and ins.get_xlim() == (0.2, 0.4)
        with pytest.raises(ValueError):
            layout.zoom_inset(ax, (0.4, 0.2), (0.2, 0.4), draw)
        cm, main, top, right, corner = layout.marginal_canvas("single", 89)
        assert top.get_shared_x_axes().joined(top, main) and right.get_shared_y_axes().joined(right, main)


def test_density_scatter_rejects_nan_and_area_sizes():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60)
        ax = c.ax(0, 0)
        with pytest.raises(ValueError):
            layout.density_scatter(ax, [0, np.nan], [0, 1])
    np.testing.assert_allclose(layout.area_sizes([1, 4], 1, 10), [10, 40])
    with pytest.raises(ValueError):
        layout.area_sizes([-1], 1)


def test_save_exact_size_no_tight(tmp_path):
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60)
        c.ax(0, 0).plot([0, 1], [0, 1])
        p = c.save(tmp_path / "f", formats=("png",), dpi=100)[0]
    from PIL import Image
    assert Image.open(p).size == (round(89 / 25.4 * 100), round(60 / 25.4 * 100))


# ------------------------------------------------------------------ scales / fields / io / captions
def test_symlog_needs_threshold_and_slope_guide_needs_loglog():
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 60)
        ax = c.ax(0, 0)
        with pytest.raises(ValueError):
            scales.set_symlog(ax, "y", None)
        scales.set_symlog(ax, "y", 1e-3, note="noise floor")
        assert ax.get_yscale() == "symlog"
        with pytest.raises(ValueError):
            scales.slope_guide(ax, 1, 10, 1, 1)
        c2 = layout.make_canvas(89, 60)
        a2 = c2.ax(0, 0)
        a2.loglog([1, 10], [1, 10])
        ys = scales.slope_guide(a2, 1, 10, 1, 2, r"$t^2$")
        np.testing.assert_allclose(ys, [1, 100])


def test_streamlines_mask_solids_not_zero_fill():
    x = np.linspace(-1, 1, 30); y = np.linspace(-1, 1, 20)
    X, Y = np.meshgrid(x, y)
    u = np.ones_like(X); v = np.zeros_like(X)
    u[(X**2 + Y**2) < 0.1] = np.nan
    with theme.style_context("paper"):
        c = layout.make_canvas(89, 50)
        ax = c.ax(0, 0, field=True)
        sp = fields.add_streamlines(ax, x, y, u, v, seeds="inlet", n_seeds=5)
        assert len(sp.lines.get_paths()) > 0
        with pytest.raises(ValueError):
            fields.add_streamlines(ax, x, y, u[:5], v[:5])


def test_prepare_field_validates():
    xe = np.array([0., 1, 2]); ye = np.array([0., 1, 2])
    norm = make_norm("linear", 0, 1)
    draw, st, ext = fields.prepare_field({"x": xe, "y": ye, "values": np.ones((2, 2)) * .5}, "rectilinear", "cell", "pcolormesh", norm)
    assert st["extend"] == "neither" and ext == (0, 2, 0, 2)
    with pytest.raises(ValueError):
        fields.prepare_field({"x": xe[::-1], "y": ye, "values": np.ones((2, 2))}, "rectilinear", "cell", "pcolormesh", norm)
    with pytest.raises(ValueError):
        fields.prepare_field({"x": xe, "y": ye, "values": np.ones((3, 3))}, "rectilinear", "cell", "pcolormesh", norm)
    with pytest.raises(ValueError):
        fields.explicit_levels([0, .5, 2], (0, 1))
    assert fields.cell_aspect((0, 4), (0, 1)) == 0.25


def test_foam_reader_hardening(tmp_path):
    f = tmp_path / "forceCoeffs.dat"
    f.write_text("# Force coefficients\n# Time Cd Cl\n0.1 1.0 0.0\n0.2 1.1 0.1\n0.3 1.2 0.2\n")
    d = io_foam.read_foam_dat(f)
    assert list(d) == ["Time", "Cd", "Cl"] and d["Cd"].tolist() == [1.0, 1.1, 1.2]
    bad = tmp_path / "ragged.dat"
    bad.write_text("# Time a b\n1 2 3\n2 4\n")
    with pytest.raises(ValueError, match="column count"):
        io_foam.read_foam_dat(bad)
    rst = tmp_path / "restart.dat"
    rst.write_text("# Time a\n1 1\n2 2\n3 3\n1 9\n2 8\n")
    with pytest.raises(ValueError, match="strictly increasing"):
        io_foam.read_foam_dat(rst)
    assert io_foam.read_foam_dat(rst, restart="last")["a"].tolist() == [9.0, 8.0]
    vec = tmp_path / "vec.dat"
    vec.write_text("# Time Fx Fy Fz\n1 (1 2 3)\n2 (4 5 6)\n")
    assert io_foam.read_foam_dat(vec)["Fz"].tolist() == [3.0, 6.0]
    inf = tmp_path / "inf.dat"
    inf.write_text("# Time a\n1 inf\n")
    with pytest.raises(ValueError, match="infinite"):
        io_foam.read_foam_dat(inf)
    lg = tmp_path / "log.txt"
    lg.write_text("Solving for Ux, Initial residual = 1e-3, Final residual = 1e-7\nSolving for Ux, Initial residual = 5e-4\n")
    assert io_foam.read_foam_log_residuals(lg)["Ux"].tolist() == [1e-3, 5e-4]


def test_caption_stub_mentions_choices():
    prov = {"config": {"colorbar_label": "p", "units": "Pa", "reference_description": "ambient"},
            "field_statistics": {"normalization": "Normalize", "vmin": -1, "vmax": 1, "below_range": 3,
                                 "above_range": 0, "clipped_fraction": 0.03, "extend": "min", "n_masked": 2},
            "cmap": "signed", "synthetic": True, "interpolation": "none"}
    txt = captions.caption_stub(prov, kind="field")
    for needle in ("3.00%", "ambient", "SYNTHETIC", "2 cells masked"):
        assert needle in txt


# ------------------------------------------------------------------ renderers (end to end)
def _run(script, cfg, *extra):
    return subprocess.run([sys.executable, str(ROOT / "skills" / script), str(cfg), "--allow-font-fallback", *extra],
                          capture_output=True, text=True)


@pytest.mark.parametrize("name,script", [
    ("line", "sim-plot/scripts/render_plot.py"), ("scatter", "sim-plot/scripts/render_plot.py"),
    ("bars", "sim-plot/scripts/render_plot.py"), ("multiples", "sim-plot/scripts/render_plot.py"),
    ("field_cell", "sim-field/scripts/render_field.py"), ("field_contour", "sim-field/scripts/render_field.py"),
    ("field_wake", "sim-field/scripts/render_field.py")])
def test_example_configs_render(name, script, tmp_path):
    import shutil
    ex = tmp_path / "examples"
    shutil.copytree(ROOT / "examples", ex)
    cfg = json.loads((ex / f"{name}.json").read_text())
    cfg["output"] = f"out/{name}"
    cfg["formats"] = ["png"]
    (ex / f"{name}.json").write_text(json.dumps(cfg))
    r = _run(script, ex / f"{name}.json")
    assert r.returncode == 0, r.stderr[-800:]
    side = json.loads((ex / "out" / f"{name}.viz.json").read_text())
    assert side["qa"]["blocking"] == "passed" and (ex / "out" / f"{name}.caption.txt").exists()
    assert side["kit_version"] == "1.0.0"


def test_renderer_refuses_unsafe_inputs(tmp_path):
    import shutil
    ex = tmp_path / "examples"
    shutil.copytree(ROOT / "examples", ex)
    cfg = json.loads((ex / "line.json").read_text())
    cfg.update(yscale="symlog", output="out/x")
    (ex / "bad.json").write_text(json.dumps(cfg))
    r = _run("sim-plot/scripts/render_plot.py", ex / "bad.json")
    assert r.returncode != 0 and "linthresh" in r.stderr
    cfg = json.loads((ex / "field_cell.json").read_text())
    cfg["scale"] = "symmetric"
    cfg["limits"] = [0, 1]
    (ex / "bad2.json").write_text(json.dumps(cfg))
    assert _run("sim-field/scripts/render_field.py", ex / "bad2.json").returncode != 0


def test_simviz_compat_facade():
    import simviz
    with simviz.style_context(allow_font_fallback=True) as st:
        fig, ax = simviz.new_figure(st)
        assert all(sp.get_visible() for sp in ax.spines.values())
        assert simviz.get_cmap("cmc.vik").N == 256
        assert simviz.get_palette("muted", st["theme"])[0] == "#5B7C99"
        assert simviz.make_norm("linear", 0, 1).vmax == 1


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))


# ---------------------------------------------------------------- restyle mode
def _original_fig():
    import runpy
    from scivis import restyle
    root = Path(__file__).resolve().parents[1]
    with restyle.intercept_savefig() as got:
        runpy.run_path(str(root / "examples" / "original_rz_charge.py"), run_name="__main__")
    return got


def test_restyle_never_writes_original_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    got = _original_fig()
    assert got.figs and not list(tmp_path.iterdir())


def test_restyle_frozen_layer_identical():
    from scivis import restyle, layout
    from scivis.theme import style_context
    got = _original_fig()
    old = restyle.harvest(got.figs[-1])
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=restyle.panel_aspect(old[0]), margins=(11.5, 9, 13, 6))
        ax = c.ax(0, 0, field=True)
        restyle.replay(old[0], ax)
        assert restyle.compare(old, restyle.harvest(c.fig)) == []
        assert not layout.qa(c.fig, verbose=False)


def test_restyle_detects_changed_limits():
    import copy
    from scivis import restyle, layout
    from scivis.theme import style_context
    got = _original_fig()
    old = restyle.harvest(got.figs[-1])
    bad = copy.deepcopy(old)
    bad[0].layers[0].d["norm"].vmax = bad[0].layers[0].d["norm"].vmax * 8      # a 'helpful' rescale
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=restyle.panel_aspect(bad[0]), margins=(11.5, 9, 13, 6))
        restyle.replay(bad[0], c.ax(0, 0, field=True))
        diffs = restyle.compare(old, restyle.harvest(c.fig))
    assert diffs and "norm" in diffs[0]


def test_restyle_cmap_change_is_explicit():
    from scivis import restyle, layout
    from scivis.theme import style_context
    old = restyle.harvest(_original_fig().figs[-1])
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=restyle.panel_aspect(old[0]), margins=(11.5, 9, 13, 6))
        r = restyle.replay(old[0], c.ax(0, 0, field=True), cmap="signed")
        assert r["changes"] and "opt-in" in r["changes"][0]
        assert restyle.compare(old, restyle.harvest(c.fig)), "cmap change must be visible to compare()"
        assert restyle.compare(old, restyle.harvest(c.fig), allow=("cmap",)) == []


def test_restyle_unsupported_artist_raises():
    import matplotlib.pyplot as plt
    from scivis import restyle, layout
    from scivis.theme import style_context
    fig, ax = plt.subplots()
    ax.contourf(np.random.rand(5, 5))
    spec = restyle.harvest(fig)
    plt.close(fig)
    assert spec[0].unsupported
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", height=60)
        with pytest.raises(restyle.UnsupportedArtist):
            restyle.replay(spec[0], c.ax(0, 0, field=True))


def test_qa_ignores_ticks_outside_view():
    import matplotlib.colors as mc
    from scivis import layout
    from scivis.theme import style_context
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=2.0, margins=(11.5, 9, 13, 6))
        ax = c.ax(0, 0, field=True)
        im = ax.imshow(np.random.randn(20, 10), norm=mc.Normalize(-2.5, 2.5), cmap="RdBu_r")
        layout.add_colorbar(ax, im, "q (e nm$^{-3}$)", extend="both")
        assert not [i for i in layout.qa(c.fig, verbose=False) if i[0] == "clipped"]


def test_long_colorbar_label_goes_to_side():
    import matplotlib.colors as mc
    from scivis import layout
    from scivis.theme import style_context
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=2.0, margins=(11.5, 9, 15, 6))
        ax = c.ax(0, 0, field=True)
        im = ax.imshow(np.random.randn(20, 10), norm=mc.Normalize(-2, 2), cmap="RdBu_r")
        cb = layout.add_colorbar(ax, im, "Liquid charge density (e nm$^{-3}$)", extend="both")
        assert cb.ax.get_ylabel().startswith("Liquid")
        assert not layout.qa(c.fig, verbose=False)


def test_signed_if_diverging():
    import matplotlib
    from scivis import restyle, layout
    from scivis.theme import style_context
    assert restyle.is_diverging(matplotlib.colormaps["RdBu_r"]) and restyle.is_diverging(matplotlib.colormaps["coolwarm"])
    assert not restyle.is_diverging(matplotlib.colormaps["viridis"]) and not restyle.is_diverging(matplotlib.colormaps["jet"])
    old = restyle.harvest(_original_fig().figs[-1])
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=restyle.panel_aspect(old[0]), margins=(11.5, 9, 15, 6))
        r = restyle.replay(old[0], c.ax(0, 0, field=True), cmap=restyle.SIGNED_IF_DIVERGING)
    assert r["changes"] and "vik" in r["changes"][0]


def _run_template(name, *extra):
    root = Path(__file__).resolve().parents[1]
    return subprocess.run([sys.executable, str(root / "skills" / "sim-field" / "templates" / name),
                           "--allow-font-fallback", "--overwrite", *extra], cwd=root,
                          capture_output=True, text=True, env={**os.environ, "SCIVIS_ALLOW_FONT_FALLBACK": "1"})


def test_intake_gate_blocks_until_confirmed():
    root = Path(__file__).resolve().parents[1]
    r = _run_template("restyle_harvest_template.py")
    assert r.returncode == 3 and "INTAKE NOT CONFIRMED" in r.stdout and "RdBu_r" in r.stdout
    assert not (root / "restyle_out").exists()


def test_assume_defaults_is_recorded():
    import shutil
    root = Path(__file__).resolve().parents[1]
    try:
        r = _run_template("restyle_harvest_template.py", "--assume-defaults")
        assert r.returncode == 0, r.stderr[-400:]
        side = json.loads((root / "restyle_out" / "rz_charge_restyled.viz.json").read_text())
        assert side["provenance"]["restyle"]["intake"]["answers_source"] == "default-unattended"
        assert side["provenance"]["restyle"]["original_facts"]["panels"][0]["layers"][0]["cmap"] == "RdBu_r"
    finally:
        shutil.rmtree(root / "restyle_out", ignore_errors=True)


def test_vlim_is_opt_in_and_recorded():
    from scivis import restyle, layout
    from scivis.theme import style_context
    old = restyle.harvest(_original_fig().figs[-1])
    with style_context("paper", allow_font_fallback=True):
        c = layout.make_canvas("single", cell_aspect=restyle.panel_aspect(old[0]), margins=(11.5, 9, 15, 6))
        r = restyle.replay(old[0], c.ax(0, 0, field=True), vlim=(-0.5, 0.5))
    assert any("colour limits" in x and "user opt-in" in x for x in r["changes"])
    assert restyle.compare(old, restyle.harvest(c.fig))                      # frozen audit sees it ...
    assert not restyle.compare(old, restyle.harvest(c.fig), allow=("norm",))  # ... unless allowed


def test_template_size_mode_dpi_and_frames():
    import shutil
    root = Path(__file__).resolve().parents[1]
    tdir = root / "skills" / "sim-field" / "templates"
    src = (tdir / "restyle_harvest_template.py").read_text()
    src = src.replace('SIZE_MODE = "compact"', 'SIZE_MODE = "strict-89"').replace("DPI = 600", "DPI = 300")
    src = src.replace('FRAMES = [{"name": "", "argv": []}]',
                      'FRAMES = [{"name": "a", "argv": []}, {"name": "b", "argv": []}]')
    src = src.replace('OUT_DIR = Path("restyle_out")', 'OUT_DIR = Path("restyle_out_test")')
    tmp = tdir / "_tmp_restyle_modes.py"
    tmp.write_text(src)
    try:
        r = _run_template("_tmp_restyle_modes.py", "--assume-defaults")
        assert r.returncode == 0, r.stderr[-500:]
        out = root / "restyle_out_test"
        for n in ("a", "b"):
            side = json.loads((out / f"{n}.viz.json").read_text())
            assert abs(side["size_mm"][0] - 89.0) < 0.5 and side["raster_dpi"] == 300
            assert side["provenance"]["restyle"]["size_mode"] == "strict-89"
    finally:
        tmp.unlink(missing_ok=True)
        shutil.rmtree(root / "restyle_out_test", ignore_errors=True)


def _run_recipe(*extra, cwd):
    root = Path(__file__).resolve().parents[1]
    return subprocess.run([sys.executable, str(root / "skills" / "sim-plot" / "recipes" / "custom_layout_template.py"),
                           "--allow-font-fallback", *extra], cwd=cwd, capture_output=True, text=True,
                          env={**os.environ, "SCIVIS_ALLOW_FONT_FALLBACK": "1"})


def test_custom_layout_template_gate_and_brief(tmp_path):
    r = _run_recipe(cwd=tmp_path)
    assert r.returncode == 3 and "BRIEF NOT CONFIRMED" in r.stdout
    assert not (tmp_path / "figures_out").exists()
    r = _run_recipe("--assume-defaults", cwd=tmp_path)
    assert r.returncode == 0, r.stderr[-400:]
    side = json.loads((tmp_path / "figures_out" / "custom_layout.viz.json").read_text())
    assert abs(side["size_mm"][0] - 183.0) < 0.5 and side["raster_dpi"] == 600
    prov = side["provenance"]
    assert prov["brief"]["answers_source"] == "default-unattended" and prov["layout"]["grid"] == [1, 3]


def test_skill_docs_carry_calling_rules_and_no_agents_snippet():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "AGENTS.snippet.md").exists()
    for name in ("sim-plot", "sim-field"):
        text = (root / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        assert "calling rules" in text and "create_layout" in text and "restyle_scope" in text
    assert (root / "skills" / "sim-plot" / "references" / "create-mode.md").exists()


def test_chinese_figure_readme_contents_and_interpretation(tmp_path):
    import matplotlib.colors as mc
    from scivis import layout
    from scivis.export import export_figure
    from scivis.theme import style_context

    def build():
        c = layout.make_canvas("single", 50)
        ax = c.ax(0, 0)
        ax.plot([0, 1, 2], [1, 2, 3], label="case A")
        ax.plot([0, 1, 2], [3, 2, 1], ls="--", label="case B")
        ax.set_xlabel(r"$t/t_0$"); ax.set_ylabel("Cd (-)"); ax.legend()
        return c.fig

    interp = {"physical_significance": "PHYS-TEXT", "results": ["RES-1", "RES-2"], "discussion": ["DISC-1"]}
    with style_context("paper", allow_font_fallback=True) as st:
        rep = export_figure(build(), tmp_path / "a", st, provenance={"source_id": "x", "interpretation": interp},
                            formats=["png"], kind="line")
        txt = (tmp_path / "a.README.zh-CN.md").read_text(encoding="utf-8")
        assert rep["readme_zh"] == "a.README.zh-CN.md"
        for needle in ("$t/t_0$", "Cd (-)", "case A", "case B", "PHYS-TEXT", "RES-2", "DISC-1", "线性", "agent 草稿，待核对"):
            assert needle in txt
        assert "【待补充】" not in txt
        export_figure(build(), tmp_path / "b", st, provenance={"source_id": "x"}, formats=["png"])
        txt = (tmp_path / "b.README.zh-CN.md").read_text(encoding="utf-8")
        assert "【待补充】" in txt and "| 4 物理意义 | 待补充 |" in txt
        export_figure(build(), tmp_path / "c", st, provenance={"source_id": "x", "config": {"readme": False}}, formats=["png"])
        assert not (tmp_path / "c.README.zh-CN.md").exists()


def test_readme_lists_colourbar_and_clipping():
    import json
    root = Path(__file__).resolve().parents[1]
    txt = (root / "previews" / "field_wake.README.zh-CN.md").read_text(encoding="utf-8")
    assert "色标：" in txt and "截断" in txt and "ω_z" in txt


def test_readme_origin_tags_status_and_modes(tmp_path):
    from scivis import layout
    from scivis.export import export_figure
    from scivis.theme import style_context

    def fig():
        c = layout.make_canvas("single", 50)
        ax = c.ax(0, 0); ax.plot([0, 1, 2], [1, 2, 3]); ax.set_xlabel("x"); ax.set_ylabel("y")
        return c.fig

    def make(name, interp, **extra):
        with style_context("paper", allow_font_fallback=True) as st:
            export_figure(fig(), tmp_path / name, st, provenance={"source_id": "s", "interpretation": interp, **extra},
                          formats=["png"])
        return (tmp_path / f"{name}.README.zh-CN.md").read_text(encoding="utf-8")

    t = make("a", {"physical_significance": [{"text": "PHYS", "origin": "label"}],
                   "results": [{"text": "RES", "origin": "data"}, "UNTAGGED-RES"],
                   "discussion": ["DISC-DEFAULT", {"text": "DISC-USER", "origin": "user"}]})
    assert "PHYS 〔来源：依据图中标签〕" in t and "RES 〔来源：依据数据〕" in t
    assert "UNTAGGED-RES 〔来源：未标注来源，请核对〕" in t and "DISC-DEFAULT 〔来源：建议，未验证〕" in t
    assert t.count("agent 草稿，待核对") == 3
    t = make("b", {"pending": {"results": "只有图片，没有数据"}})
    assert "待补充：只有图片，没有数据" in t and "| 4 物理意义 | 待补充 |" in t
    t = make("c", {"mode": "author"})
    assert "作者自行撰写" in t and "【作者填写】" in t
    t = make("d", {"mode": "skip", "results": ["SHOULD-NOT-APPEAR"]})
    assert "本次跳过" in t and "SHOULD-NOT-APPEAR" not in t and "撰写要求" not in t
    t = make("e", {"results": ["R"]}, synthetic=True)
    assert "合成数据，以下内容仅作示例" in t
