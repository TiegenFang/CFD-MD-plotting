"""A deliberately plain 'original' script (synthetic data) used to test restyle mode.

It mimics a typical lab plotting script: display-only Gaussian smoothing, 4x bilinear
upsampling, percentile colour limits with extend='both', RdBu_r, a boundary contour,
default matplotlib fonts. Restyle mode must change none of the choices above.
"""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "original_rz_charge.png"   # restyle mode never lets this file be written


def gauss_smooth(a, sigma):
    k = np.arange(-int(3 * sigma) - 1, int(3 * sigma) + 2)
    w = np.exp(-0.5 * (k / sigma) ** 2)
    w /= w.sum()
    a = np.apply_along_axis(lambda v: np.convolve(np.pad(v, len(k) // 2, mode="edge"), w, "valid"), 0, a)
    return np.apply_along_axis(lambda v: np.convolve(np.pad(v, len(k) // 2, mode="edge"), w, "valid"), 1, a)


def build():
    rng = np.random.default_rng(3)
    nr, nz = 30, 80
    r = (np.arange(nr) + 0.5) * 2.5          # Angstrom
    z = (np.arange(nz) + 0.5) * 2.5
    R, Z = np.meshgrid(r, z, indexing="ij")
    inside = (R / 60) ** 2 + (Z / 110) ** 2 < 1
    field = rng.normal(0, 6, (nr, nz)) * inside * np.exp(-R / 40)      # e / nm^3
    return r, z, field.T, inside.T


def main():
    r, z, f, inside = build()
    fs = gauss_smooth(f, 0.8)
    up = np.kron(fs, np.ones((1, 1)))
    lim = float(np.percentile(np.abs(fs), 97.5))
    fig, ax = plt.subplots(figsize=(3.0, 6.0), dpi=150)
    im = ax.imshow(fs, origin="lower", extent=(0, 75, 0, 200), cmap="RdBu_r", vmin=-lim, vmax=lim,
                   interpolation="bilinear", aspect="equal")
    ax.contour(r, z, inside.astype(float), levels=[0.5], colors="#222222", linewidths=0.8)
    cb = fig.colorbar(im, ax=ax, extend="both", shrink=0.9)
    cb.set_label("Liquid charge density (e nm$^{-3}$)")
    ax.set_xlabel("r (Å)")
    ax.set_ylabel("$z_{rel}$ (Å)")
    ax.text(5, 100, "0.5 $\\rho_{ref}$", fontsize=8)
    fig.savefig(OUT, dpi=300)


if __name__ == "__main__":
    main()
