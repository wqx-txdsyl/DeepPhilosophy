# O9 Design System — 设计系统与 tokens

## 1. 设计原则（优先级即序）

1. **阅读优先**：正文是唯一主角；一切辅助信息渐进披露。
2. **克制**：无 AI 霓虹、无赛博朋克、无大面积渐变、无过度玻璃态、无 Dashboard 化。
3. **学术感**：引用可核验、来源分层清晰、字段准确。
4. **温度**：现实哲学入口有人文语气；空态是邀请而非工具面板。
5. **一致**：全部颜色/间距/圆角复用既有 CSS tokens，不引入新色值。

## 2. Tokens（既有 CSS 变量, agent-app 全局）

| token | 用途 |
|---|---|
| `--bg` | 表面底色（侧栏/卡片/抽屉） |
| `--border` | 分隔线/描边（所有 O9 组件边框） |
| `--text` / `--text-dim` | 主文/次文 |
| `--accent` | 品牌强调（光标/链接） |
| `--soft` | 弱底（代码块/摘录底） |
| `--cw-line-body` | 正文行高 |
| `--cw-sidebar-w` | 侧栏宽 |

主题（light/dark）由既有 theme.js 切换，O9 组件全部经由 tokens 自动适配，不写死色值。

## 3. O9 新增组件规格

### DepthControls（.o9-depth / .o9-depth-chip）
- 形态：胶囊 chips；12px 字号；默认 `--text-dim`，hover 提亮；圆角 999px。
- 位置：回答正文后 10px；移动端横向滚动不换行。

### EpStarter（.o9-ep / .o9-ep-grid / .o9-ep-card）
- 网格：`repeat(auto-fill, minmax(170px, 1fr))`；移动端 2 列。
- 卡片：1px 边框 10px 圆角；icon 15px + 标题 12.5px/600 + 问题截断 42 字（两行夹紧）。
- hover：边框提亮 + translateY(-1px)。

### 分层来源（.o9-layer / .o9-layer-cap / .o9-cite-numbered）
- 层帽：10.5px 字距 0.4px 胶囊（原典/学术/网络）。
- chip：编号上标 [n]（tabular-nums）+ 标题截断 46 字。

### SourceDrawer（.o9-drawer*）
- 桌面：右侧滑出 400px；移动端（≤640px）全宽。
- 结构：header（标题+关闭）/ title / 字段行（k=64px 灰）/ 摘录（左边线引块）/ 核验状态 / 阅读器链接。
- 动效：遮罩 fade .16s / 抽屉 slide .18s；Esc 与遮罩关闭。

## 4. 文字层级

| 层级 | 字号/字重 |
|---|---|
| 回答正文 | 14.5px / 400 / 行高 var(--cw-line-body) |
| 组件标题（drawer title/EP 标题） | 15px·700 / 12.5px·600 |
| 辅助（层帽/chips/相位） | 10.5–12px / 400–600 |
| 引文摘录 | 12.5px / 1.7 行高 |

## 5. 声音与语气（文案规范）

- 研究状态用人话：「正在查找原典」而非「search_books running」。
- 核验状态诚实二态：「已核验：本回答实际引用的证据」/「检索到但未被本回答引用」。
- EP 入口标题「现实生活哲学」——不是「案例库」「题库」。

## 6. 反例清单（code review 时拒绝）

- 渐变按钮 / 霓虹描边 / 玻璃卡 / 表格化 DOI 面板出现在默认视图 / 工具 raw JSON 默认展开。
