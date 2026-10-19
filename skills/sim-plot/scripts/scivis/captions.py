"""Caption stub from provenance (Rougier rule 4: a figure without a caption is half a figure).

The stub states what the colour encodes and every choice that changes how the data look:
limits, clipping, reference value, smoothing, synthetic flag. The author adds the message.
"""
from __future__ import annotations


def caption_stub(prov: dict, *, kind: str = "figure") -> str:
    cfg = prov.get("config", {})
    lines = []
    head = cfg.get("title") or cfg.get("colorbar_label") or cfg.get("ylabel") or "TODO: one-sentence message"
    lines.append(f"[{kind}] {head}.")
    stats = prov.get("field_statistics")
    if stats:
        unit = cfg.get("units", "")
        lines.append(f"Colour: {cfg.get('colorbar_label', '?')} ({prov.get('cmap', '?')}, "
                     f"{stats['normalization']}), limits [{stats['vmin']:.4g}, {stats['vmax']:.4g}] {unit}.")
        if stats.get("below_range") or stats.get("above_range"):
            lines.append(f"{100 * stats.get('clipped_fraction', 0):.2f}% of valid cells lie outside the limits "
                         f"(colour-bar extend: {stats['extend']}).")
        if cfg.get("reference_description"):
            lines.append(f"Reference at the diverging centre: {cfg['reference_description']}.")
        if stats.get("n_masked"):
            lines.append(f"{stats['n_masked']} cells masked ({prov.get('geometry_mask', 'mask not described')}).")
        lines.append(f"Display: {prov.get('interpolation', 'n/a')}.")
    ov = prov.get("overlays") or {}
    if ov.get("streamlines"):
        lines.append(f"Streamlines: seeded '{ov['streamlines'].get('seeds', 'auto')}' on the regular grid; "
                     "integral curves, spacing carries no magnitude information.")
    if ov.get("zoom"):
        z = ov["zoom"]
        lines.append(f"Inset magnifies x in {z['xlim']}, y in {z['ylim']} with the same colour mapping.")
    if cfg.get("uncertainty"):
        lines.append(f"Uncertainty: {cfg['uncertainty'].get('definition', '?')}.")
    if prov.get("transformations"):
        lines.append(f"Transformations: {prov['transformations']}.")
    if prov.get("symlog"):
        lines.append(f"Symmetric-log axis with linear threshold {prov['symlog']}.")
    if prov.get("synthetic"):
        lines.append("DATA ARE SYNTHETIC (illustration only).")
    src = prov.get("source_id") or prov.get("input")
    if src:
        lines.append(f"Source: {src}.")
    return "\n".join(lines) + "\n"
