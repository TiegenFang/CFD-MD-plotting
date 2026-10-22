"""Chinese figure README written next to every exported figure.

Part A (sections 1-3, 7) is generated from the figure itself and its provenance: figure type, axes, legend, colour
meaning, limits, processing. Nothing in it is guessed.

Part B (sections 4-6) is interpretation: physical significance, a journal-style description of preliminary results and
discussion directions. A program cannot know these. They are taken from ``interpretation`` in the provenance
(``{"physical_significance": str, "results": str | list, "discussion": list}``); when absent, the section is written
as a visible placeholder and the file says so. Facts-only prompts (clipped fraction, non-statistical uncertainty,
synthetic data, log axes) are generated for the discussion section from the provenance.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any

import numpy as np

PLACEHOLDER = "【待补充】"
_RESTYLE_ZH = {
    "array values, masks and coordinates": "数组数值、掩膜与坐标", "colour map (unless the user opts in)": "色图（除非你同意更换）",
    "norm: vmin / vmax / centre / extend": "归一化：vmin / vmax / 中心 / extend", "interpolation and smoothing": "插值与平滑",
    "axis limits and scales": "坐标范围与刻度类型", "axis, colour-bar and annotation text": "坐标轴、色标与标注文字",
    "contour geometry": "等值线几何", "units (no Angstrom -> nm conversion unless asked)": "单位（不擅自换算）",
    "canvas size and margins": "画布尺寸与边距", "fonts and sizes": "字体与字号", "frame, tick style and tick count": "边框、刻度样式与数量",
    "colour-bar geometry": "色标几何", "line widths and halos": "线宽与描边", "panel labels": "面板字母", "export formats / dpi": "导出格式与分辨率",
}
_SCALE_ZH = {"linear": "线性", "log": "对数", "symlog": "对称对数", "logit": "logit", "function": "自定义"}
_KIND_ZH = {"line": "折线图", "scatter": "散点图", "bar": "柱状图", "multiples": "小多图（ghost small multiples）",
            "field": "物理场云图", "figure": "组合图"}


def _is_cbar(ax) -> bool:
    return hasattr(ax, "_scivis_cbar_label")


def _fmt(v) -> str:
    try:
        return f"{float(v):.4g}"
    except (TypeError, ValueError):
        return str(v)


def _panel_kind(ax) -> str:
    kinds = []
    if any(c.__class__.__name__ in {"QuadMesh", "PolyQuadMesh"} for c in ax.collections) or ax.images:
        kinds.append("云图/热图")
    if any(c.__class__.__name__ == "PathCollection" for c in ax.collections):
        kinds.append("散点图")
    if any(getattr(c, "_scivis_levels", None) is not None or c.__class__.__name__ in {"QuadContourSet", "TriContourSet"}
           or c.__class__.__name__ == "LineCollection" for c in ax.collections):
        kinds.append("等值线/流线")
    if any(type(c).__name__ == "ContourSet" for c in ax.collections):
        kinds.append("等值线")
    if ax.containers and any(type(c).__name__ == "BarContainer" for c in ax.containers):
        kinds.append("柱状图")
    if [ln for ln in ax.lines if len(ln.get_xdata()) > 2]:
        kinds.append("折线/曲线")
    if getattr(ax, "_scivis_inset", False):
        kinds.append("放大插图")
    return "＋".join(dict.fromkeys(kinds)) or "（未识别）"


def harvest_panels(fig) -> list[dict[str, Any]]:
    panels = []
    for ax in fig.axes:
        if _is_cbar(ax):
            continue
        letter = next((t.get_text() for t in ax.texts if t.get_fontweight() in ("bold", 700) and len(t.get_text()) <= 2), "")
        leg = ax.get_legend()
        entries = [t.get_text() for t in leg.get_texts() if t.get_text().strip() and not t.get_text().startswith("_")] if leg else []
        panels.append({
            "letter": letter, "title": ax.get_title(loc="left") or ax.get_title(),
            "kind": _panel_kind(ax),
            "xlabel": ax.get_xlabel(), "ylabel": ax.get_ylabel(),
            "xscale": ax.get_xscale(), "yscale": ax.get_yscale(),
            "xlim": tuple(ax.get_xlim()), "ylim": tuple(ax.get_ylim()),
            "legend": entries,
        })
    cax = [c for a in fig.axes for c in [a, *a.child_axes] if _is_cbar(c)]
    cbars = [{"label": c._scivis_cbar_label,
              "lim": tuple(c.get_ylim()) if c.get_ylim() != (0.0, 1.0) else tuple(c.get_xlim())} for c in cax]
    return panels, cbars


def _interp(prov: dict) -> dict:
    for src in (prov, prov.get("brief") or {}, prov.get("config") or {}):
        if isinstance(src, dict) and isinstance(src.get("interpretation"), dict):
            return src["interpretation"]
    return {}


ORIGIN_ZH = {"data": "依据数据", "user": "依据你的说明", "label": "依据图中标签", "script": "依据原脚本",
             "suggestion": "建议，未验证"}
UNTAGGED = "未标注来源，请核对"


def _items(v, default_origin: str | None = None) -> list[tuple[str, str]]:
    """Normalise a section to [(text, origin label)]. Items are str or {"text": ..., "origin": data|user|label|script|suggestion}."""
    if not v:
        return []
    seq = [v] if isinstance(v, (str, dict)) else list(v)
    out = []
    for it in seq:
        if isinstance(it, dict):
            text, origin = str(it.get("text", "")).strip(), it.get("origin")
        else:
            text, origin = str(it).strip(), None
        if text:
            out.append((text, ORIGIN_ZH.get(origin or default_origin or "", UNTAGGED)))
    return out


def _section(interp: dict, key: str, default_origin: str | None):
    """-> (status, items, pending reason). mode: "draft" (default) | "author" | "skip"."""
    mode = interp.get("mode", "draft")
    if mode == "skip":
        return "本次跳过", [], ""
    items = _items(interp.get(key), default_origin)
    reason = (interp.get("pending") or {}).get(key, "")
    if items:
        return ("agent 草稿，待核对" if mode != "author" else "作者撰写，待核对"), items, ""
    if mode == "author":
        return "作者自行撰写", [], reason
    return ("待补充：" + reason if reason else "待补充"), [], reason


def _checks(prov: dict, panels, cbars) -> list[str]:
    cfg = prov.get("config") or {}
    out = []
    stats = prov.get("field_statistics") or {}
    if stats.get("clipped_fraction"):
        out.append(f"色标范围 [{_fmt(stats['vmin'])}, {_fmt(stats['vmax'])}] 之外有 {100 * stats['clipped_fraction']:.2f}% 的有效单元被截断显示（extend：{stats.get('extend')}）。"
                   "建议核查被截断区域是否包含关键极值，并在正文或图注中说明。")
    if (cfg.get("uncertainty") or {}).get("definition", "").lower().startswith("synthetic") or (
            cfg.get("uncertainty") and "not a statistical" in str(cfg["uncertainty"].get("definition", "")).lower()):
        out.append("图中的不确定度带不是统计置信区间。投稿前应替换为重复实验/分块平均/自助法得到的误差，并写明定义。")
    elif not cfg.get("uncertainty") and any(p["kind"].startswith("折线") or "散点" in p["kind"] for p in panels):
        out.append("图中未显示不确定度。若数据来自多次重复或分块平均，建议补充误差带或误差棒，并写明其定义（标准差、标准误或置信区间）。")
    for i, p in enumerate(panels):
        tag = p["letter"] or f"面板{i + 1}"
        if p["xscale"] != "linear" or p["yscale"] != "linear":
            out.append(f"{tag}：使用了{_SCALE_ZH.get(p['xscale'], p['xscale'])}（x）/{_SCALE_ZH.get(p['yscale'], p['yscale'])}（y）坐标，"
                       "读者易低估线性差异；建议在正文说明选择该坐标的原因，并给出关键量的数值。")
    if prov.get("synthetic"):
        out.append("数据为合成数据，仅作示意，不能用于任何物理结论。")
    if prov.get("symlog"):
        out.append(f"对称对数轴的线性阈值为 {prov['symlog']}，请在图注中说明。")
    return out


def readme_zh(fig, prov: dict, report: dict, *, kind: str, stem: str) -> str:
    panels, cbars = harvest_panels(fig)
    cfg = prov.get("config") or {}
    interp = _interp(prov)
    stats = prov.get("field_statistics") or {}
    rs = prov.get("restyle") or {}
    kind_zh = _KIND_ZH.get(cfg.get("kind") or kind, _KIND_ZH["figure"])
    st4, it4, r4 = _section(interp, "physical_significance", None)
    st5, it5, r5 = _section(interp, "results", None)
    st6, it6, r6 = _section(interp, "discussion", "suggestion")
    w, h = report["size_mm"]
    L = []
    A = L.append
    A(f"# 图说明文档：{stem.split('/')[-1].split(chr(92))[-1]}")
    A("")
    A("> 第 1–3、7 节由程序根据图本身和溯源记录自动生成。第 4–6 节为解释性内容，程序无法获知，必须由作者依据真实数据确认后再用于论文。")
    A("")
    A("| 章节 | 状态 |")
    A("|---|---|")
    A("| 1–3、7 | 自动生成 |")
    A(f"| 4 物理意义 | {st4} |")
    A(f"| 5 初步结果描述 | {st5} |")
    A(f"| 6 讨论方向 | {st6} |")
    A("")
    if prov.get("synthetic"):
        A("> ⚠ 本图使用合成数据，仅作示意。")
        A("")
    A("## 1. 图的类型与布局")
    A("")
    A(f"- 图类型：{kind_zh}" + ("（美化已有图，数据层冻结）" if rs else ""))
    A(f"- 面板数：{len(panels)}；画布 {w:.1f} mm × {h:.1f} mm；介质：{report.get('medium', '?')}；字体：{report.get('font_resolved', '?')}")
    A(f"- 输出文件：{'、'.join(report.get('outputs', []))}（栅格 {report.get('raster_dpi', '?')} dpi）")
    if prov.get("source_id") or prov.get("input"):
        A(f"- 数据来源：{prov.get('source_id') or prov.get('input')}")
    A("")
    A("| 面板 | 标题 | 内容类型 |")
    A("|---|---|---|")
    for i, p in enumerate(panels):
        A(f"| {p['letter'] or i + 1} | {p['title'] or '—'} | {p['kind']} |")
    A("")
    A("## 2. 坐标轴")
    A("")
    A("| 面板 | x 轴标签 | x 轴刻度/范围 | y 轴标签 | y 轴刻度/范围 |")
    A("|---|---|---|---|---|")
    for i, p in enumerate(panels):
        A(f"| {p['letter'] or i + 1} | `{p['xlabel'] or '—'}` | {_SCALE_ZH.get(p['xscale'], p['xscale'])}，{_fmt(p['xlim'][0])} – {_fmt(p['xlim'][1])} "
          f"| `{p['ylabel'] or '—'}` | {_SCALE_ZH.get(p['yscale'], p['yscale'])}，{_fmt(p['ylim'][0])} – {_fmt(p['ylim'][1])} |")
    A("")
    A("标签中的 `$...$` 为数学公式；单位写在括号或标签内。")
    A("")
    A("## 3. 图例与配色")
    A("")
    any_leg = False
    for i, p in enumerate(panels):
        if p["legend"]:
            any_leg = True
            A(f"- 面板 {p['letter'] or i + 1} 图例：{'；'.join(p['legend'])}")
    if not any_leg:
        A("- 图中没有图例（单一系列，或颜色由色标表示）。")
    enc = cfg.get("color_encoding")
    if enc:
        A(f"- 颜色编码：{enc.get('mode', '?')}" + (f"（调色板 {enc['palette']}）" if enc.get("palette") else "") +
          (f"（色图 {enc['cmap']}）" if enc.get("cmap") else ""))
    for c in cbars:
        A(f"- 色标：`{c['label']}`，范围 {_fmt(c['lim'][0])} – {_fmt(c['lim'][1])}" +
          (f"；色图 {prov.get('cmap')}" if prov.get("cmap") else ""))
    if stats:
        A(f"- 色标归一化：{stats.get('normalization', '?')}；截断单元比例 {100 * stats.get('clipped_fraction', 0):.2f}%，色标 extend：{stats.get('extend', '无')}。")
        if cfg.get("reference_description"):
            A(f"- 发散色图中心（白色）对应：{cfg['reference_description']}")
    if any(len({ln.get_linestyle() for ln in ax.lines if len(ln.get_xdata()) > 2}) > 1 for ax in fig.axes):
        A("- 系列之间除颜色外还以线型区分，灰度打印时仍可辨认。")
    A("")
    def body(items, status, hint, bullets=False):
        if items:
            for text, origin in items:
                A((f"- {text} 〔来源：{origin}〕" if bullets else f"{text} 〔来源：{origin}〕") + ("" if bullets else "\n"))
        elif status == "本次跳过":
            A("本次未要求撰写。")
            A("")
        elif status.startswith("作者自行"):
            A(f"【作者填写】{hint}")
            A("")
        else:
            A(f"{PLACEHOLDER}{hint}")
            A("")

    syn = bool(prov.get("synthetic"))
    A("## 4. 物理意义")
    A("")
    body(it4, st4, "说明每个坐标量的物理含义与无量纲化方式，图中所示量反映什么物理过程，与哪一个控制参数相关。只写数据和模型能够支持的内容。")
    A("## 5. 初步结果描述（按期刊投稿要求）")
    A("")
    if syn and it5:
        A("> ⚠ 数据为合成数据，以下内容仅作示例，不得用于论文。")
        A("")
    body(it5, st5, "用客观、可核对的语句描述图中看到的内容。" + (f"（待补充原因：{r5}）" if r5 else ""))
    if st5 != "本次跳过":
        A("撰写要求（投稿检查清单）：")
        A("")
        A("- 每个结论对应图中可见的证据，写出具体数值、单位和对比对象（如“峰值位于 x = …，较基准增大 …%”）。")
        A("- 区分观察与解释：先写“图 1a 显示……”，再单独写可能的原因，并使用“可能”“与……一致”等限定语，不写没有数据支持的因果。")
        A("- 说明误差或不确定度的来源与定义；没有误差时说明为何没有。")
        A("- 说明数据处理（平滑、截断、坐标变换、采样、统计窗口），与第 7 节一致。")
        A("- 图注只写“是什么”，正文写“说明了什么”；避免重复，也不要把结论写进图注。")
        A("- 对比同类研究时引用文献并比较同一量；不要夸大创新性。")
        A("")
    A("## 6. 值得进一步讨论与分析的方向")
    A("")
    body(it6, st6, "列出由本图自然引出、且可用现有或补充数据检验的问题（参数敏感性、机理、与文献的差异、局限性）。" + (f"（待补充原因：{r6}）" if r6 else ""), bullets=True)
    chk = _checks(prov, panels, cbars)
    if chk:
        A("")
        A("由图和溯源记录自动提示的核查项（程序生成）：")
        A("")
        for c in chk:
            A(f"- {c}")
    A("")
    A("## 7. 数据处理与可复现信息")
    A("")
    A(f"- 数据处理：{prov.get('transformations') or '渲染器内无数据变换'}")
    if stats:
        A(f"- 显示方式：{prov.get('interpolation', 'n/a')}")
    if rs:
        fr = "、".join(_RESTYLE_ZH.get(x, x) for x in rs.get("frozen", []))
        pr = "、".join(_RESTYLE_ZH.get(x, x) for x in rs.get("presentation", []))
        A(f"- 美化模式：冻结层（与原图一致）：{fr}；仅更改呈现层：{pr}。")
        if rs.get("opt_in_changes"):
            A(f"- 经你同意的改动：{'；'.join(rs['opt_in_changes'])}")
        A(f"- 原始脚本：{rs.get('original_script', '?')}（sha256 {str(rs.get('original_sha256', ''))[:12]}…）；原文件未被写入。")
    A(f"- 溯源文件：`{stem.split('/')[-1].split(chr(92))[-1]}.viz.json`；图注草稿：`….caption.txt`；QA：{report.get('qa', {}).get('blocking', '?')}。")
    A(f"- 生成日期：{_dt.date.today().isoformat()}（工具版本 {report.get('kit_version', '?')}）")
    A("")
    return "\n".join(x for x in L if x is not None) + "\n"
