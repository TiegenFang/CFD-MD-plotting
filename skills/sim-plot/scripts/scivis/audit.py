"""Numerical colour audit: turns the uploaded standard into pass/fail checks.

Standards implemented (from the uploaded colour-palette skill):
  1. perceptual uniformity   -> evenness of CAM02-UCS step size along the map
  2. CVD safety              -> deutan / protan / tritan simulation (severity 100)
  3. grayscale monotonicity  -> J' (CAM02-UCS lightness) monotone along sequential maps
  4. diverging maps          -> centre is the lightness extreme, halves monotone to it
  5. categorical sets        -> minimum pairwise distance, also under CVD

The numeric thresholds below are *engineering* thresholds chosen so that the Crameri
and Tol maps recommended here pass and jet/turbo/rainbow fail. The uploaded standard
states the criteria qualitatively; it gives no numbers.

    python -m scivis.audit              # table to stdout
    python -m scivis.audit --png out/color_audit.png
"""
from __future__ import annotations

import argparse
import itertools

import numpy as np
from colorspacious import cspace_convert
from matplotlib.colors import to_rgb

from . import palettes as P

CVD = {"deutan": "deuteranomaly", "protan": "protanomaly", "tritan": "tritanomaly"}

# thresholds ---------------------------------------------------------------
T_MONO_TOL = 0.15      # J' decreases of up to this per step still count as monotone
T_UNIFORM_CV = 0.45    # CV of lightness step (J') along the interior 5-95 % of a sequential map
T_CVD_RETAIN = 0.55    # path length under CVD / normal path length
T_SYM = 12.0           # max |J'(x)-J'(1-x)| for a diverging map
T_CENTER_J = 3.0       # centre must be within this of the lightness extreme
T_CAT_MIN_DE = 15.0    # min pairwise CAM02-UCS distance (normal vision)
T_CAT_MIN_DE_CVD = 8.0 # ... under deutan and protan simulation (tritan reported, not gated)
T_END_SEP_CVD = 15.0   # diverging: the two arms must stay at least this far apart under CVD
T_CAT_GRAY_DJ = 10.0   # pairs closer than this in J' need redundant encoding


def _ucs(rgb, cvd=None):
    rgb = np.clip(np.asarray(rgb, float)[..., :3], 0, 1)
    if cvd:
        rgb = cspace_convert(rgb, {"name": "sRGB1+CVD", "cvd_type": CVD[cvd], "severity": 100},
                             "sRGB1")
        rgb = np.clip(rgb, 0, 1)
    return cspace_convert(rgb, "sRGB1", "CAM02-UCS")


def _path(lab):
    return np.linalg.norm(np.diff(lab, axis=0), axis=1)


def _mono(J, tol=T_MONO_TOL):
    d = np.diff(J)
    return bool((d >= -tol).all() or (d <= tol).all())


def audit_sequential(cmap, n=256):
    rgb = cmap(np.linspace(0, 1, n))[:, :3]
    lab = _ucs(rgb)
    J = lab[:, 0]
    step = _path(lab)
    dJ = np.abs(np.diff(J))[int(0.05 * n): int(0.95 * n)]
    out = dict(kind="sequential",
               J_start=J[0], J_end=J[-1], J_range=abs(J[-1] - J[0]),
               J_monotone=_mono(J), uniform_cv=float(dJ.std() / dJ.mean()))
    ret = {}
    mono_cvd = {}
    for c in CVD:
        lc = _ucs(rgb, c)
        ret[c] = float(_path(lc).sum() / step.sum())
        mono_cvd[c] = _mono(lc[:, 0])
    out.update(cvd_retention=ret, cvd_J_monotone=mono_cvd)
    out["pass"] = dict(
        grayscale=out["J_monotone"] and out["J_range"] > 50,
        uniform=out["uniform_cv"] <= T_UNIFORM_CV,
        cvd=min(ret.values()) >= T_CVD_RETAIN and all(mono_cvd.values()),
    )
    return out


def audit_diverging(cmap, n=257):
    rgb = cmap(np.linspace(0, 1, n))[:, :3]
    lab = _ucs(rgb)
    J = lab[:, 0]
    mid = n // 2
    lightest = J[mid] >= J.max() - T_CENTER_J
    darkest = J[mid] <= J.min() + T_CENTER_J
    half_ok = (_mono(J[: mid + 1]) and _mono(J[mid:]))
    sym = float(np.abs(J - J[::-1]).max())
    out = dict(kind="diverging", J_center=J[mid], J_ends=(J[0], J[-1]),
               center_extreme="light" if lightest else "dark" if darkest else "none",
               halves_monotone=half_ok, J_asymmetry=sym)
    ret, sep = {}, {}
    step = _path(lab)
    for c in CVD:
        lc = _ucs(rgb, c)
        ret[c] = float(_path(lc).sum() / step.sum())
        sep[c] = float(np.linalg.norm(lc[int(0.1 * n)] - lc[int(0.9 * n)]))
    out.update(cvd_retention=ret, cvd_end_separation=sep)
    out["pass"] = dict(
        centre=lightest or darkest,
        halves=half_ok,
        symmetry=sym <= T_SYM,
        cvd=min(ret.values()) >= T_CVD_RETAIN and min(sep.values()) >= T_END_SEP_CVD,
    )
    return out


def audit_cyclic(cmap, n=256):
    rgb = cmap(np.linspace(0, 1, n))[:, :3]
    lab = _ucs(rgb)
    wrap = float(np.linalg.norm(lab[0] - lab[-1]))
    step = _path(lab)
    return {"kind": "cyclic", "wrap_gap": wrap, "mean_step": float(step.mean()),
            "pass": {"closes": bool(wrap <= 3 * step.mean())}}


def audit_categorical(colors):
    rgb = np.array([to_rgb(c) for c in colors])
    res = {}
    for label, cvd in [("normal", None)] + [(k, k) for k in CVD]:
        lab = _ucs(rgb, cvd)
        d = [(np.linalg.norm(lab[i] - lab[j]), i, j)
             for i, j in itertools.combinations(range(len(colors)), 2)]
        res[label] = min(d)
    J = _ucs(rgb)[:, 0]
    gray_pairs = [(colors[i], colors[j]) for i, j in itertools.combinations(range(len(colors)), 2)
                  if abs(J[i] - J[j]) < T_CAT_GRAY_DJ]
    ok_cvd = all(res[k][0] >= T_CAT_MIN_DE_CVD for k in ("deutan", "protan"))
    return {"kind": "categorical", "min_de": {k: round(v[0], 1) for k, v in res.items()},
            "gray_close_pairs": gray_pairs,
            "needs_redundant_encoding": bool(gray_pairs),
            "pass": {"normal": bool(res["normal"][0] >= T_CAT_MIN_DE), "cvd": bool(ok_cvd)}}


# -------------------------------------------------------------------------
def _fmt(ok):
    return "PASS" if ok else "FAIL"


def run(verbose=True):
    rows = []
    seen = set()

    def add(label, cmap, kind):
        fn = dict(sequential=audit_sequential, diverging=audit_diverging, cyclic=audit_cyclic)[kind]
        r = fn(cmap)
        r["name"] = label
        rows.append(r)

    # recommended maps
    for role, spec in P.ROLES.items():
        for nm in (spec.default,) + tuple(spec.alts):
            if (nm, spec.kind) in seen:
                continue
            seen.add((nm, spec.kind))
            add(nm, P.get_cmap(nm, allow_restricted=True), spec.kind)
    # reference failures (bypass the ban list on purpose)
    import matplotlib.pyplot as plt
    for nm in ("jet", "turbo", "viridis"):
        add(nm, plt.get_cmap(nm), "sequential")
    add("Tol rainbow_PuRd", P._lookup("rainbow_PuRd"), "sequential")
    for nm in ("seismic", "coolwarm", "RdBu_r"):
        add(nm, plt.get_cmap(nm), "diverging")
    add("vik (raw)", P.get_cmap("vik", white_center=False), "diverging")

    cats = []
    for name, cols in P.TOL.items():
        r = audit_categorical(cols[: P.TOL_MAX[name]])
        r["name"] = f"Tol {name}"
        cats.append(r)

    if verbose:
        print(f"\n{'colormap':<18}{'kind':<11}{'checks':<40}notes")
        print("-" * 100)
        for r in rows:
            checks = "  ".join(f"{k}:{_fmt(v)}" for k, v in r["pass"].items())
            if r["kind"] == "sequential":
                note = (f"J' {r['J_start']:.0f}->{r['J_end']:.0f}, cv={r['uniform_cv']:.2f}, "
                        f"cvd-retain>={min(r['cvd_retention'].values()):.2f}")
            elif r["kind"] == "diverging":
                note = (f"centre {r['center_extreme']} (J'={r['J_center']:.0f}), "
                        f"asym={r['J_asymmetry']:.1f}, ends-sep(cvd)>={min(r['cvd_end_separation'].values()):.0f}")
            else:
                note = f"wrap gap={r['wrap_gap']:.1f}"
            print(f"{r['name']:<18}{r['kind']:<11}{checks:<40}{note}")
        print(f"\n{'categorical set':<18}{'checks':<40}min dE (normal/deutan/protan/tritan)")
        print("-" * 100)
        for r in cats:
            checks = "  ".join(f"{k}:{_fmt(v)}" for k, v in r["pass"].items())
            m = r["min_de"]
            print(f"{r['name']:<18}{checks:<40}{m['normal']}/{m['deutan']}/{m['protan']}/{m['tritan']}"
                  + (f"  -> use redundant_encoding ({len(r['gray_close_pairs'])} pairs close in J')" if r["needs_redundant_encoding"] else ""))
    return rows, cats


def check_tol_hex_against_package():
    """Guards against typos in palettes.TOL (compares with the tol_colors package)."""
    import tol_colors as tc
    bad = []
    for name, cols in P.TOL.items():
        pkg = {c.upper() for c in tc.colorsets[name]}
        mine = {c.upper() for c in cols}
        # package may add black/white/pale extras; ours must be a subset
        if not mine <= pkg:
            bad.append((name, sorted(mine - pkg)))
    return bad


def swatch_png(path, names=None):
    """Contact sheet: every map in colour / deutan / protan / grayscale (J') strips."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = names or ["batlow", "lipari", "oslo", "lajolla", "bilbao", "cividis", "iridescent",
                      "vik", "broc", "sunset", "berlin", "romaO",
                      "viridis", "turbo", "jet"]
    import matplotlib.pyplot as plt
    g = np.linspace(0, 1, 256)
    fig, axes = plt.subplots(len(names), 4, figsize=(8.2, 0.42 * len(names) + 0.6))
    heads = ["normal", "deutan", "protan", "grayscale"]
    for r, nm in enumerate(names):
        cm = plt.get_cmap(nm) if nm in ("jet", "turbo", "viridis") else P._lookup(nm)
        rgb = cm(g)[:, :3]
        strips = [rgb,
                  np.clip(cspace_convert(rgb, {"name": "sRGB1+CVD", "cvd_type": CVD["deutan"], "severity": 100}, "sRGB1"), 0, 1),
                  np.clip(cspace_convert(rgb, {"name": "sRGB1+CVD", "cvd_type": CVD["protan"], "severity": 100}, "sRGB1"), 0, 1)]
        J = _ucs(rgb)[:, 0] / 100
        gray = np.repeat(np.clip(J, 0, 1)[:, None], 3, axis=1)
        strips.append(gray)
        for c, s in enumerate(strips):
            ax = axes[r, c]
            ax.imshow(s[None, :, :], aspect="auto")
            ax.set_xticks([]); ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            if r == 0:
                ax.set_title(heads[c], fontsize=7)
            if c == 0:
                ax.set_ylabel(nm, rotation=0, ha="right", va="center", fontsize=7)
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--png", help="write a swatch contact sheet")
    a = ap.parse_args()
    bad = check_tol_hex_against_package()
    print("Tol hex check vs tol_colors package:", "OK" if not bad else f"MISMATCH {bad}")
    run()
    if a.png:
        print("wrote", swatch_png(a.png))


if __name__ == "__main__":
    main()
