# O9 Interaction Spec — 交互合同

> 每个交互 = 触发 → 系统 反馈 → 结果态。本文件为 O9 实现依据与 UAT 验收口径。

## 1. 提问（空态）

- 触发：点击 EP 卡（现实哲学六题）| 点击 starter chip | 在 Composer 输入并 Enter。
- 反馈：立即出现用户气泡 + Assistant 折叠研究状态头（「正在思考」点动画）。
- 结果：流式回答; 研究头在开始输出正文时自动折叠为「思考了 Xs · 已查阅 N 项」。
- 约束：中文 IME 组合中 Enter 不误发；切会话清 draft；流式期间可 Stop。

## 2. 研究状态（Research State）

- 五态相位措辞：正在理解问题 / 正在查找原典 / 正在核验出处 / 正在查阅学术研究 / 正在整理论证。
- 映射（toolName→phase）：search_books·get_chapter·get_book_detail·list_books·concept_trace→查找原典；
  search_scholarship·get_scholarly_source·websearch→查阅学术；query_*·get_philosopher·get_school→理解问题；
  其他（quote/validator 类）→核验出处/整理论证。
- 禁止：raw 工具参数默认展开、raw CoT、内部 prompt。折叠展开仅显示安全摘要行（既有行为保留）。

## 3. 引用交互（Citation UX）

- 正文行内【《书》·章】：点击 → resolveCite → 新窗口打开平台阅读器对应章节；未匹配 → 标记失败态不静默跳 0 章。
- Evidence Panel：默认每回答最多 5 个 chips，按层分组（原典/学术/网络），带编号 [n]；「+n」展开全部。
- 点击 chip → SourceDrawer（右侧滑出，Esc/遮罩关闭）：书目字段 + 摘录 + 核验状态 + 「在阅读器中打开原典」。
- 原则：正文阅读永不被引用元数据挤压；DOI/venue 等只在抽屉出现。

## 4. 深度控件（Depth Controls）

- 位置：回答正文之后、followups 之前；仅非流式且有正文时渲染。
- 四键：简单一点 / 深入一点 / 看原典 / 看学术研究。
- 行为（O9 合同）：点击 → 以冻结措辞发起追问（例：看原典 →「请针对上面的回答，引用相关原典原文（给出书名与章节），并解释原文语境。」）。
- O11 映射：四键将改写 Reader State 的 desired_depth / reading_mode，而非一次性措辞；组件 API（onPick(prompt)）不变。

## 5. 现实哲学入口（EP）

- 空态（general agent）显示六卡；点击卡片 = 直接发送该问题全文。
- EP 回答的体验合同（不依赖 UI 特判，靠 prompt/模型行为）：拆前提 → 概念区分 → 多解释 → 必要引用 → 回到处境。

## 6. 论证视图（Argument View，交互合同）

- 入口：回答 followups 区追加「请展开论证结构」类措辞（复用 Depth 通道）。
- 目标形态：Claim / ├─ Reason 1 / ├─ Reason 2 / ├─ Objection / └─ Reply 的层级展示。
- O9 交付：措辞合同 + 展示样式约定（缩进层级列表）; 一等树视图留 O13。

## 7. 原典阅读（Primary Text UX）

- 入口：行内【】链接、chips 抽屉「在阅读器中打开原典」。
- 行为：resolveCite 定位 book_id+chapter → 平台阅读器 `?ch=` 深链，新窗口; 未匹配 → 失败态提示，不静默跳第 0 章。
- 未来 Reader Context（O11）：记录 read work/chapter/current passage——本阶段仅保留深链合同。

## 8. 会话连续性（Continuity）

- 侧栏会话列表 + 稳定 URL 回访; 流式所有权保证切换不串流（既有）。
- 预留：current topic / previous question / reader context 展示位（O11/O12 填充）。

## 9. 键盘与可达性

- Composer：Enter 发送 / Shift+Enter 换行 / IME 保护。
- SourceDrawer：Esc 关闭、遮罩点击关闭、role=dialog + aria-modal。
- Depth/EP/chips 均为真实 button（键盘可达, aria-label 完整）。
