# Colour system: standards, roles, audit results

Source standards (from the uploaded colour-palette skill, Python parts only; R code and ggsci removed):
1. perceptual uniformity, 2. colour-vision-deficiency (CVD) safety, 3. grayscale monotonicity,
4. match the palette type to the data type, 5. symmetric bounds on signed data, 6. few categorical hues.
Implementation basis: **cmcrameri** (continuous), **Paul Tol** (categorical, plus his continuous maps as alternatives), viridis/cividis as the standard's fallbacks.

## Data type -> palette type

| Type | Palette | Rule |
|---|---|---|
| sequential (>= 0) | batlow, lipari, oslo, devon, lajolla, bilbao, turku | luminance must be monotone |
| diverging (signed about a reference) | vik (default), broc, bam, Tol sunset / BuRd | reference value on the centre; symmetric limits |
| cyclic | romaO, vikO, brocO, corkO, bamO | never a linear map for angles |
| categorical | Tol bright / vibrant / muted / high_contrast | <= 6-9 hues, then facet |
| qualitative with too many classes | none | aggregate, facet, or add markers |

## Audit (python -m scivis.audit)

CAM02-UCS lightness J' for the grayscale test; colorspacious CVD simulation (severity 100) for deutan/protan/tritan. Thresholds are *engineering* choices (the standard is qualitative): J' monotone within 0.15/step; lightness-step CV <= 0.45 on the interior 5-95 %; CVD path-length retention >= 0.55; diverging: centre is the lightness extreme, halves monotone, arm asymmetry <= 12 J', arm separation under CVD >= 15; categorical: min pairwise distance >= 15 (normal) and >= 8 (deutan, protan; tritan reported only).

| Map | Result |
|---|---|
| batlow, lipari, oslo, devon, bilbao, turku, lajolla, cividis, viridis | pass all three checks |
| vik, broc, bam, Tol sunset, Tol BuRd, roma | pass (vik arm asymmetry 11.7 J': the blue arm is darker than the red) |
| berlin, vanimo, managua | pass, but the centre is *dark*: dark-background use only |
| cork | **CVD risk**: arm separation about 8 under deutan/protan; warns in `get_cmap` |
| jet, turbo | **fail** grayscale monotonicity and lightness uniformity |
| Tol rainbow_PuRd | **fail** (non-monotone) |
| matplotlib seismic | fails symmetry (28.5 J'), so the threshold is discriminating |
| Tol bright / vibrant / muted / high_contrast / medium_contrast | pass normal + deutan/protan (bright: 23.7 / 16.2 / 15.6; tritan 7.4) |
| Tol light, dark | fail: meant for fills / text on fills, not for lines (`categorical` warns) |

Most hue-based categorical sets have pairs that are close in lightness (bright: 4 pairs, vibrant: 7, muted: 6): they are distinguishable in colour but not in grayscale, so use `redundant_encoding(n)` (linestyle + marker) whenever the figure may be printed in black and white.

## Where the uploaded standard was corrected

Checked numerically in this skill's build; the uploaded text is otherwise followed.
- **"turbo: jet-like but perceptually uniform"** (failure-modes section): false. Turbo's lightness runs 16 -> 91 -> 29 (non-monotone). It is banned here.
- **"vik: blue -> white -> red equivalent", "roma: slightly warmer than vik"**: the raw maps do not have a white centre. vik's centre is #ECE5E0, bam #F6F1F0, Tol sunset #EAECCB, roma #C0EAC3 (pale green; roma is a red-yellow-green-blue geoscience scheme, not a blue-red map). The standard's rule "midpoint pure white, not light grey" therefore cannot hold for the raw maps. `get_cmap` applies `white_center=True` to light-centred diverging maps: a Gaussian blend toward #FFFFFF that is exactly white at the centre and leaves the map unchanged beyond about +/-12 % of its range. Pass `white_center=False` for the published maps.
- **Okabe-Ito as the categorical default**: replaced by Tol sets, per the project brief. Okabe-Ito and Tol bright are both CVD-oriented; Tol's sets are what `categorical()` ships.
- **Brand palettes (ggsci)**: excluded by design; `get_cmap` rejects npg/aaas/lancet/jama/jco/nejm.

## Normalisation (the other half of a correct mapping)

- Diverging: `diverging_norm(data, center=0, q=99.5)` -> limits `center +/- vmax`. The alternative `mode="twoslope"` keeps an asymmetric range but gives different colour-per-unit on the two sides; say so in the caption if used.
- Sequential: `sequential_norm(data, q=(0.5, 99.5))`; colour bar `extend=` from `robust_limits`.
- Mention any clipping percentile in the caption.

## Role guidance for CFD / MD

- Velocity magnitude, TKE, concentration: batlow / lipari.
- Cp, vorticity, velocity perturbation, signed error: vik with a symmetric norm. Cp has a physical reference (0 = freestream static pressure), so the centre is 0 even though the Cp range is asymmetric.
- Temperature: lajolla (warm-toned, still luminance-monotone). Do not swap in a blue-red diverging map unless the quantity is a deviation from a reference.
- MD density maps: oslo (light = high). On white paper use `P.truncate(cmap, 0, 0.88)` for scatter, or batlow.
- Atomic species colours: not covered by the audit; if you use CPK/Jmol colours for snapshots, note that their red-green pairs are not CVD-safe and add labels.

## Colour system notes

- `get_cmap(..)` accepts roles, bare names, the `cmc.` prefix and `_r` suffix (`cmc.oslo_r`); oslo and vik come from archived hash-checked tables and work without cmcrameri, all other Crameri names need the package.
- Categorical: `tol-bright` (default, max 6) and the other Tol sets, plus the soft project families `muted`, `cool`, `earth`, `okabe-ito` by name (`palettes.palette(name, theme)`).
- The `density` role trims the near-white top of oslo (segment 0-0.88) so it never merges with paper or the masked grey `#DDDDDD`.
- Extra tools from the book's colour chapter: `lab_ramp` (Lab interpolation), `colour_stack` (hue per group, lightness within), see `colormap-decision.md`.
