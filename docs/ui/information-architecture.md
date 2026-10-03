# O9 Information Architecture — PhiAgent 用户信息架构

## 1. 顶层结构

```
App Shell（.cw-root）
├── ConversationSidebar（会话列表 / 新对话 / 智能体广场入口 / 设置入口）
├── ConversationHeader（会话标题 / 侧栏开关 / 回答者标识）
├── MessageStream（唯一主角）
│   ├── User Bubble（结构化附件卡 + 用户文本）
│   └── Assistant Bubble
│       ├── AgentIdentity（回答者是谁）
│       ├── AgentActivity（研究状态: 思考摘要 + 相位化工具流, 可折叠）
│       ├── Answer Body（markdown + 行内引用【】+ mermaid）
│       ├── Evidence Panel（分层: 原典/学术/网络; 编号 [n]; 点击 → SourceDrawer）
│       ├── Depth Controls（简单一点/深入一点/看原典/看学术研究）
│       └── Followups（可继续探索）
├── Composer（附件 / Agent 选择 / 发送）
└── Overlays（SourceDrawer / Settings / AgentPlaza / Drawio）
```

## 2. 用户默认看到（信息最小集）

问题 → 回答 → 关键引用（分层编号 chips）→ 研究状态（一句话折叠头）→ 继续深入入口（Depth + Followups）。

**默认不可见**（渐进披露）：raw 工具参数与结果全文、核验计数细节、retrieved-vs-cused 差值、
思考摘要正文（折叠内）、validator/repair 痕迹、CoT。

## 3. 导航与身份模型

- 会话身份：/agent/c/:conversationId（稳定 URL，可回访）；/agent = 草稿。
- 回答者身份：消息级 agent_id（与当前选择解耦——历史回答永远显示其真实回答者）。
- 流所有权：流式期间切 Agent/开会话不影响进行中的回答写入（既有 §9 契约保留）。

## 4. 现实哲学入口（Everyday Philosophy）

- 空态默认呈现 EP 六题卡（🧭🪞🎁🔋🌙🤖），点击即提问。
- 体验合同：提出问题 → 拆隐藏前提 → 区分概念 → 展示不同解释 → 必要时引哲学资源 → 回到现实处境。
- EP 问题**不走**「学术检索器」心智模型：无 DOI 表格、无强检索态；研究状态一句话即可。

## 5. 引用信息架构

```
回答正文（行内【书·章】链接 + 引用标记）
  └── Evidence Panel（默认: 分层 chips, 最多 5 个 + +n 展开）
        └── SourceDrawer（点击单个来源）
              ├── 书目字段（作者/著作/章节页/出版/年份/DOI——有则显示）
              ├── 原文摘录（quote/passage/abstract, 有则显示）
              ├── 核验状态（已核验=本回答实际引用 / 检索到未引用）
              └── 在阅读器中打开原典（resolveCite 深链）
```

层级规则：`layerOf(citation)` = primary（有 book）/ scholarly（doi/record/期刊容器）/ web（其余）。

## 6. 未来扩展锚点（本阶段不实现）

- O11 Adaptive Reader：Depth Controls 映射 Reader State（同用户同域多状态）。
- O12 Persistence：会话/消息/reader-state 快照上云；本地 store 为其子集。
- O13：Argument View 一等化（Claim/Reason/Objection/Reply 树渲染）。
