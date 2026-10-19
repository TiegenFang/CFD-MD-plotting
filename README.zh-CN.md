# CFD-MD-plotting

面向 CFD 与分子动力学结果的出版级绘图，由两个共享同一套配色、字体与排版系统的 agent skill 组成。

| Skill | 用途 |
|---|---|
| [`sim-plot`](skills/sim-plot) | 折线、散点、柱状、工况对比、小多图、残差/受力监控、parity 图；内含共享层 `scivis`。 |
| [`sim-field`](skills/sim-field) | 物理场：云图、等值线、流线、切片、网格场、MD 密度/电荷图；从 `sim-plot` 引用 `scivis`。 |

两种模式：

- **新建**：从已处理好的数据出图（`render_plot.py`、`render_field.py`、recipes）。
- **美化已有图**（"帮我优化这张图"）：数据层冻结并被审计，只改呈现层。

## 主要能力

- 以毫米为单位按最终尺寸建画布（89 / 120 / 183 mm）；场图按物理纵横比出图，细长面板自动变窄而不是拉大。
- 默认 Arial，按介质（论文/幻灯片/海报）固定字号层级；仅在明确允许时才回退字体，并写入记录。
- 按"物理含义"选色：序列/发散用 Crameri（batlow、白心 vik 等），分类用 Paul Tol；带 CAM02-UCS 审计与色标范围保护。
- 全框坐标轴、带框图例、位于面板外侧的色标；过长的色标标签自动改为侧向。
- 导出前 QA：文字被裁切、字号过小、色标缺标签、字体替代、画布宽度不符等会阻止导出；同时生成 `.viz.json` 溯源文件和图注草稿。

## 美化已有图（restyle 模式）

1. agent 先找到原绘图代码并运行模板一次，读出并打印原图的实际设置（色图、范围、extend、超出范围比例、平滑与插值、尺寸）。
2. 引用这些事实，一次最多问 4 个带推荐答案的问题；脚本中的 `CONTRACT["confirmed"]` 会阻止未确认就出图；无人值守时用 `--assume-defaults`，并被记录。
3. 用 `scivis` 重建面板。数值、平滑、插值、色标范围、extend、坐标范围、单位和文字**冻结**；字体、尺寸、边框、刻度、色标、描边等被替换。冻结层与原图不一致时拒绝导出。更换色图需明确同意（带符号场使用 vik）。
4. 输出：图（pdf/png/svg）、带审计的 `.viz.json`、图注草稿、前后对比图。

## 安装

将 `sim-plot` 与 `sim-field` 两个文件夹并列放入 agent 的 skills 目录；`python install.py --target codex --scope user --apply` 可代为复制。
再执行 `pip install -r requirements.txt`。不附带 Arial，请自行安装，或用 `--allow-font-fallback` 出草稿。
将 `AGENTS.snippet.md` 的内容手动粘贴进你的 `AGENTS.md` 以启用路由。

## 状态与限制

- 已在合成数据与一份真实场数据导出上测试；OpenFOAM、ParaView 与 restyle 路径尚未在大量真实项目中验证，欢迎提 issue。
- 预览图使用与 Arial 度量兼容的替代字体渲染。
- 未包含：沿曲线的等值线标注、书中的 `Streamlines` 类、期刊合规性检查。
- 本仓库自身代码的许可证尚未选定；随附的第三方资源（cmcrameri 色表 MIT，Roboto 字体 Apache-2.0）保留各自许可证。
