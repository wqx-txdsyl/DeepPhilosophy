# O9 UI Audit — PhiAgent agent-app 现状审计

> 审计对象: agent-app/（React 18 + Vite 6, react-router, lucide-react, mermaid, react-drawio）
> 审计基线: 59496c81f（O8 Final Issue Ledger 之后）
> 结论: 现有前端已具备 Conversation-First 工作区骨架与 Phase-3 evidence 前端配套，
> O9 增量为「设计定型」而非重建：补深度控件、现实哲学入口、来源抽屉、分层来源、
> 研究相位与响应式收口，全部落在既有 design tokens 体系内。

## 1. 现有结构清单

| 模块 | 文件 | 现状 |
|---|---|---|
| 会话工作区 | src/pages/AgentPage.jsx（636 行） | 路由 /agent 与 /agent/c/:id；SSE 流式所有权（convId,messageId 冻结）；会话 store；草稿隔离 |
| 消息流 | components/conversation/MessageList.jsx（571 行） | memo 气泡、AgentActivity（思考摘要+工具时间流，自动折叠，无 raw CoT）、EvidenceChips、followups、QUESTION_BANK 空态 |
| 引用 | markdown.jsx CiteLink + EvidenceChips/CiteChip | 【《书》·章】内联链接（resolveCite→平台阅读器）；chips 预览/展开；used 过滤 |
| 输入 | Composer.jsx（207 行） | 自动伸缩、IME 防误发、多附件上传（25MB 预检）、Agent 选择 |
| 侧栏/设置 | ConversationSidebar/SettingsPanel | 会话列表、主题/语言/个性化/数据管理 |
| 数据 | data/conversationStore.js、chatSessions.js | 会话优先持久化（localStorage 系） |
| 样式 | conversation.css（624 行） | CSS 变量 tokens（--bg/--border/--text/--accent/--soft）；Quiet UI / Content First 原则已成文 |

## 2. 与 O9 目标态的差距（Gap → 处置）

| # | Gap | O9 处置 |
|---|---|---|
| G1 | 引用只有尾部 chips + 【】内联链接，无编号上标与全量来源详情 | ✓ 已实现：编号 chips（[1]..[n]）+ 分层（原典/学术/网络）+ SourceDrawer 抽屉（全字段/摘录/核验状态/阅读器深链） |
| G2 | 工具行为 raw 工具名 + 参数摘要，缺用户视角的相位措辞 | ✓ 已实现 researchPhase 五态映射（理解问题/查找原典/核验出处/查阅学术/整理论证），供研究状态展示（O9 相位合同） |
| G3 | 无深度控件（简单一点/深入一点/看原典/看学术研究） | ✓ 已实现 DepthControls（回答附近 chips → 措辞化追问；O11 映射 Reader State） |
| G4 | 无现实生活哲学入口 | ✓ 已实现 EpStarter（O8-R3 冻结 EP 六题为设计样例；空态卡片网格） |
| G5 | 无来源抽屉（引用点开只见跳转） | ✓ 已实现 SourceDrawer（含核验状态与「在阅读器中打开原典」） |
| G6 | 论证结构视图缺失 | 交互合同已定义（O9_INTERACTION_SPEC §6）：「论证结构」追问措辞 → Claim/Reason/Objection/Reply 结构化展开；O10/O11 可升级为一等视图 |
| G7 | 响应式有移动抽屉但未系统验证 | ✓ UAT 覆盖 390×844（无横向溢出/抽屉全宽/chips 可用）+ 1280×800 |
| G8 | design tokens 未文档化 | ✓ O9_DESIGN_SYSTEM.md 固化 |

## 3. 明确不做（O9 边界）

- 不动 backend core（retrieval/repair/validator/corpus）。
- 不暴露 raw CoT/raw validator/raw repair traces/内部 telemetry。
- 不实现 O11 Reader State / O12 persistence（仅预留交互合同）。
- 不改 O8 evidence。
