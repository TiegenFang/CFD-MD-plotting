# CFD-MD-plotting

[English](README.md) | **简体中文**

面向 CFD 与分子动力学结果的出版级绘图。由两个相互配合的 agent skill 组成，共用同一套配色、字体与排版系统。

| Skill | 用途 |
|---|---|
| [`sim-plot`](skills/sim-plot) | 折线、散点、柱状、工况对比、小多图、残差与受力监控、parity 图。内含共享层 `scivis`。 |
| [`sim-field`](skills/sim-field) | 物理场：云图、等值线、流线、切片、网格场、MD 密度与电荷分布图。从 `sim-plot` 引用 `scivis`。 |

两个 skill 都有两种模式：

- **新建**：从已处理好的数据出图（`render_plot.py`、`render_field.py`、recipes）。
- **美化已有图**（"帮我优化这张图"）：数据层被冻结并接受审计，只改变呈现层。见[美化已有图（restyle 模式）](#美化已有图restyle-模式)。

## 主要能力

- **以毫米为单位排版。** 图按最终尺寸建立（论文、幻灯片、海报档位的宽度为 89 / 120 / 183 mm）。场图按物理纵横比绘制；细长面板会变成窄图，而不是被拉伸。
- **字体。** 默认 Arial，按介质（论文 / 幻灯片 / 海报）使用固定的字号层级，支持数学公式与可选的中文标签。仅在明确授权时才回退字体，并写入记录。
- **按物理含义选色。** 序列与发散数据使用 Crameri 色图（batlow、带白色中心的 vik、lajolla、oslo、bilbao、romaO），分类数据使用 Paul Tol 色组；带 CAM02-UCS 审计，并对常数或含 NaN 的色标范围做保护。
- **全框坐标轴、带框图例、位于面板外侧的色标**；过长的色标标签自动改为侧向放置。
- **Recipes：** CFD 监控曲线、MD 折线面板、带边缘分布的 parity 图、ghost 小多图、幻灯片改编、带流线的场图面板、尾流放大插图。
- **导出前 QA 关卡。** 文字被裁切、字号过小、色标缺少标签、字体被替代、数学公式内含中文、画布宽度不符，都会阻止导出。每张图同时生成 `.viz.json` 溯源文件和图注草稿。
- **OpenFOAM 辅助：** 健壮的 `postProcessing` `.dat` 读取器和日志残差读取器。

## 安装

把两个文件夹并列放入 agent 的 skills 目录，保持同级：

```
<skills 目录>/
├── sim-plot/
└── sim-field/
```

`python install.py --target codex|claude|omp --scope user` 可代为复制（默认只做演练，加 `--apply` 才会真正复制）。
然后执行 `pip install -r requirements.txt`（numpy、matplotlib、cmcrameri；tol-colors 与 colorspacious 为可选）。
本仓库不附带 Arial，请自行安装；也可以加 `--allow-font-fallback` 输出草稿图。
若要让 agent 把请求路由到这两个 skill，请把 [`AGENTS.snippet.md`](AGENTS.snippet.md) 的内容手动粘贴进你的 `AGENTS.md`。

## 快速开始

```bash
python skills/sim-plot/scripts/render_plot.py examples/line.json --out out/line
python skills/sim-field/scripts/render_field.py examples/field_wake.json --overwrite
python -m pytest tests -q          # 57 个测试
python verify.py                   # 端到端检查（运行时请勿设置 SCIVIS_ALLOW_FONT_FALLBACK）
```

所有示例与 recipe 的预览图在 [`previews/`](previews) 中。示例数据均为合成数据。

## 美化已有图（restyle 模式）

适用于已有图以及生成它的代码：

1. agent 先找到原绘图代码，并运行模板一次。它会读出并打印原图的实际设置：色图、色标范围、extend 箭头、超出范围的单元比例、平滑与插值、图的尺寸。
2. 它引用这些事实，一次最多提 4 个带推荐答案的问题。脚本中的关卡（`CONTRACT["confirmed"]`）会阻止未确认就出图；无人值守时使用 `--assume-defaults`，并被如实记录。
3. 它用 `scivis` 重建面板。数值、平滑、插值、色标范围、extend、坐标范围、单位与文字被**冻结**；字体、尺寸、边框、刻度、色标和描边被替换。冻结层与原图不一致时拒绝导出。更换色图需要明确同意（带符号的场使用 vik）。
4. 输出：图（pdf / png / svg）、带审计结果的 `.viz.json`、图注草稿，以及前后对比图。

模板位于 [`skills/sim-field/templates/`](skills/sim-field/templates)，完整流程见
[`skills/sim-plot/references/restyle-mode.md`](skills/sim-plot/references/restyle-mode.md)。

## 仓库结构

```
skills/sim-plot/    SKILL.md、scripts/scivis（共享层）、scripts/render_plot.py、recipes/、references/、assets/
skills/sim-field/   SKILL.md、scripts/render_field.py、recipes/、templates/、references/
examples/           合成数据的配置与数据，以及一个示例"原始"绘图脚本
previews/           示例渲染结果
tests/              pytest 测试
docs/               DESIGN.md（设计决策）、UPGRADING.md（升级说明）
```

## 状态与限制

- 已在合成数据和一份真实场数据导出上开发与测试；OpenFOAM、ParaView 以及 restyle 路径尚未在大量真实项目中验证。如遇问题，欢迎提交 issue。
- 本仓库预览图使用与 Arial 度量兼容的替代字体渲染。
- 未包含：沿曲线的等值线标注、书中的 `Streamlines` 类（提供了 `streamplot` 封装）、期刊专项合规检查。
- 数据本身的科学有效性不在范围内；`.viz.json` 记录的是"画了什么"，而不是"对不对"。

## 致谢与许可

设计思路参考 N. P. Rougier 的 *Scientific Visualization: Python + Matplotlib*，详见 [`SOURCES.md`](SOURCES.md)。
本仓库以 [MIT 许可证](LICENSE)发布。随附的第三方资源保留各自的许可证（cmcrameri 色表：MIT；Roboto 字体：Apache-2.0）。
