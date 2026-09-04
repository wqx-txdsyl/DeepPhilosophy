# PhiAgent Conversation Workspace Design Specification v1.0

> 文档类型：UI/UX Reconstruction PRD + Engineering Design Specification  
> 适用范围：PhiAgent 前端 Conversation Workspace  
> 目标基准：Codex 当前桌面会话工作区的交互结构、视觉密度与状态行为  
> 产品约束：保留 PhiAgent 自身哲学 Agent、Evidence、Citation、Reader Context、Tool Trace 等能力  
> 仓库存放位置：`~/docs/PhiAgent_Conversation_Workspace_Design_Spec_v1.0.md`  
> 状态：IMPLEMENTATION-READY  
> 版本：v1.0

---

# 0. 文档定位

本文件不是普通产品 PRD，而是 PhiAgent Conversation Workspace 的**唯一 UI/UX 设计规范（Single Source of Truth）**。

其用途是：

1. 约束 Coding Agent 的实现边界；
2. 统一页面结构、组件行为、视觉密度和状态模型；
3. 避免每次 UI 开发重新解释“像 Codex”；
4. 将“设计目标”与“执行任务”分离；
5. 为后续 General / Nietzsche / Kant / Camus / 多作者会话提供稳定的共享前端框架。

若临时任务书与本文件冲突，以**最新明确任务书中的范围约束**优先；若只是实现细节不一致，以本文件为准。

# 1. 产品目标

PhiAgent 的主界面从“智能体广场式聊天页”升级为：

> **Conversation-first Philosophical Workspace**

用户主要面对的是“我正在进行的对话”，而不是“我正在浏览的 Agent 列表”。

核心信息架构：

```text
PhiAgent
├── Conversations
│   ├── Conversation A
│   ├── Conversation B
│   └── Conversation C
├── Agents
│   ├── General / 深哲
│   ├── Nietzsche / 尼采
│   └── Future Agents
├── Context
│   ├── Reader Context
│   ├── Attachments
│   └── Evidence
├── Settings
└── Agent Plaza
```

一级对象：

- Conversation：用户“之前聊了什么”
- Agent：这一轮“想和谁说”
- Context：这一轮“基于什么”
- Agent Plaza：发现“还可以和谁聊”

# 2. 设计原则

## 2.1 Quiet UI

界面必须克制。内容优先于装饰。

禁止大面积渐变、夸张阴影、大卡片堆叠、品牌色轰炸、每个模块都套边框，以及让 Tool / Evidence 比最终回答更抢眼。

## 2.2 Content First

哲学文本本身是主角。回答区必须有合理最大宽度、舒适中文行高、稳定 Markdown、低干扰引用与弱化 Tool Trace。

## 2.3 Progressive Disclosure

默认只展示用户真正需要的信息。Tool execution 默认只显示动作名、状态、简短结果；展开后才显示参数摘要、来源与 evidence summary。禁止显示 raw chain-of-thought。

## 2.4 Conversation First

主导航对象必须是 Conversation。不得继续把左侧栏做成“深哲 / 尼采 / 康德 / 加缪”列表。

## 2.5 Message-level Agent Identity

同一 Conversation 允许：

```text
User → Nietzsche
User → General
User → future Kant
```

每条 assistant message 必须持久化自身 `agent_id`。禁止依赖全局 `currentAgent` 渲染历史消息。

## 2.6 Evidence Without Noise

Evidence Contract 保留，但不能产生“来源按钮墙”。正文引用应精确、轻量；详细 Evidence 信息按需展开。

硬约束：

```text
visible formal citations ⊆ verified used_evidence
```

## 2.7 Codex-Parity, Not Codex Impersonation

高保真对齐 Codex 的页面结构、视觉密度、输入框结构、附件卡片、设置入口、会话历史、消息阅读体验和状态行为；不得复制 OpenAI/Codex 商标、Logo、专有品牌文案，也不得添加 PhiAgent 不具备的假设置。

# 3. Codex Reference Protocol

Coding Agent 不得凭记忆做“像 ChatGPT 的界面”。若执行环境可以直接观察用户本机 Codex，至少记录：新会话空状态、有历史消息、Sidebar、Conversation hover、Composer 空状态、多行输入、附件上传前、单附件、多附件、Streaming、Stop、Tool/Work、长回答、Settings、窄窗口、Sidebar 收起/展开（若存在）。

实现完成后做逐状态 side-by-side visual audit。

# 4. 页面总体结构

```text
┌────────────────────────────────────────────────────────────┐
│ Sidebar        │                 Workspace                  │
│ New chat       │            Conversation Stream             │
│ Today          │                                            │
│  Conversation  │                                            │
│ Yesterday      │                                            │
│  Conversation  │                                            │
│ Settings/User  │             Composer                       │
└────────────────────────────────────────────────────────────┘
```

避免传统 SaaS 的 Top Navbar + Left Nav + Huge Header + Content Card。

# 5. Sidebar Specification

Sidebar 首要功能：新建对话、历史对话、Workspace 管理、Settings、Agent Plaza。

推荐结构：

```text
Workspace / Product mark
New conversation

Today
  Conversation title
  Conversation title
Yesterday
  Conversation title
Previous 7 days
  ...

Agent Plaza
Settings
Account / Login
```

Conversation Item 状态：default / hover / active / focus / menu-open。单行标题优先，超长 ellipsis，hover 后显示 more，active 清晰但克制，不做大卡片，不显示冗余 metadata。

New Conversation：点击后进入空白 draft workspace，并 focus composer。若项目采用 lazy creation，第一次发送后再持久化 conversation。

# 6. Conversation Header

不要使用巨大页面标题。只显示必要的 conversation title、上下文状态和少量会话操作。Agent 不应作为固定大标题，因为 responder 可按轮切换。

# 7. Message Data Model

推荐最小契约：

```json
{
  "conversation_id": "conv_xxx",
  "message_id": "msg_xxx",
  "role": "assistant",
  "agent_id": "nietzsche",
  "content": "...",
  "attachments": [],
  "tool_events": [],
  "evidence": [],
  "status": "final"
}
```

User message 同样需要 message_id 与 conversation_id。

# 8. User Message Rendering

与 assistant 清晰区分，但不要做“微信式巨大气泡”。支持纯文本、Markdown、附件；长文本不破版。

# 9. Assistant Message Rendering

以正文为主体，支持 paragraph / heading / blockquote / list / inline code / fenced code / table / links / citations / evidence / tool summary / Mermaid（若现有功能支持）。长哲学回答必须有舒适 max-width。

# 10. Agent Identity Rendering

单 Agent 连续对话时身份标识应弱化；多 Agent 同一 Conversation 时必须可辨识。可用小型 label、icon、subtle header 或 hover identity。禁止每条回复都显示巨大 Agent 标题。

# 11. Composer Specification

Composer 是最高优先级组件。

推荐 anatomy：

```text
┌──────────────────────────────────────────────────┐
│ Attachment Card   Attachment Card                │
│                                                  │
│  问一个哲学问题…                                 │
│                                                  │
│  [+]  [回答者：尼采 ▾]                 [Send]   │
└──────────────────────────────────────────────────┘
```

Textarea 必须自动增高，达到最大高度后内部滚动；Shift+Enter 换行；Enter 发送（若项目当前约定如此）；中文 IME composition 时 Enter 不误发送；切 Agent 不清空 draft；Settings 打开不丢 draft；Conversation draft 隔离。

Composer states：empty / typing / multiline / has_attachment / uploading / streaming / disabled / error。

# 12. Attachment System

附件入口位于 Composer bottom controls，icon-only + tooltip + hover/focus，尺寸与其他 controls 统一。

Attachment Card 至少显示：file type icon/preview、filename、extension/type、upload state、success/error、remove button。可选 size/retry/image thumbnail。

发送前附件属于 `draft.attachments`；发送瞬间 snapshot → user message immutable metadata → composer draft clear。禁止跨 Conversation 串附件。

若后端支持 Drag & Drop，则显示轻量 drop target，不做夸张全屏遮罩，并在发送前校验类型与大小。

# 13. Agent Selector

用户选择的是“回答者”，不是底层模型。建议标签：`回答者：尼采`。

下拉：

```text
General / 深哲
Nietzsche / 尼采
────────────
探索更多智能体
```

未来兼容 search / groups / favorites / Agent Plaza。

# 14. Agent Switching Semantics

切换 Agent 只影响下一次 invocation。发送时必须 snapshot selected_agent。正在运行的请求不能因随后切换 selector 而改变。历史消息 agent identity 永远来自 `message.agent_id`。

# 15. Send / Stop

状态：idle → Send；streaming → Stop。

Send：snapshot draft / attachments / selected agent → create user message → create assistant placeholder → create invocation → start stream。

Stop 必须真实触发已有 abort/cancel；不允许假按钮，也不得留下永久 running placeholder。

# 16. Streaming Ownership

所有流式事件至少绑定：

```text
conversation_id
message_id
agent_id
invocation_id
```

必须处理 token / tool event / answer_retract / final / error / cancelled。

Conversation A streaming → 用户切到 B → A token 绝不能渲染进 B。

# 17. answer_retract Rendering

`answer_retract` 只撤销对应 invocation 的 draft，不影响其他 conversation，不影响 tool/evidence state，不留下重复文字，final 到达后稳定替换。

# 18. Tool / Work Rendering

保留 PhiAgent ToolCard，但重构为低干扰工作轨迹。默认只显示 Tool/action、status、concise result summary。可展开 args summary、source/evidence summary、error summary。

禁止显示 raw chain-of-thought。若当前有 `tc.thought`，改为 concise execution rationale 或隐藏。

# 19. Tool States

统一：queued / running / success / error / cancelled。多个 Tool Call 应形成紧凑 trace，而不是大量独立大卡片。

# 20. Citation Rendering

Citation 必须 inline、低干扰、baseline 对齐、hover/click，支持 General 与 Nietzsche，不依赖 global currentAgent。正文 citation 必须继续服从 Evidence Contract。

# 21. Evidence Rendering

默认只展示真正用于答案的 Evidence。推荐正文 citation → click → compact evidence detail，避免回答下方堆大量来源按钮。

# 22. Follow-up Suggestions

保留“可继续探索”，但做轻量 action，不使用大卡片。默认继续当前 conversation；默认使用当前 responder。填入 Composer 或直接发送的行为必须统一。

# 23. Empty State

新 Conversation 应简洁、Composer 居中或近中心、少量引导，不展示大规模 Agent card wall。Agent Plaza 独立存在。

# 24. Settings Entry

Settings 入口的位置和交互尽量对齐 Codex reference。打开 Settings 时不得丢失 current conversation、draft、selected responder、scroll state。

# 25. Settings IA

设置交互组织参考 Codex，但内容必须是 PhiAgent 的真实能力。

建议分区：

- General：Appearance / Language / Conversation behavior
- Agent：Default responder / 真实回答风格或深度控制 / 真实工具控制项
- Reading：Reader Context / 阅读上下文自动注入 / 引用跳转行为
- Evidence：Citation display / Evidence detail / Tool disclosure
- Conversations / Data：history / archive-delete（若已实现）/ persistence
- Advanced：debug（仅开发环境）/ backend endpoint-status（若已有）
- Account：现有账户能力

禁止为了模仿 Codex 添加不存在的 SSH / sandbox / GitHub integration / devbox / fake plugin switches。

# 26. Icon System

优先复用现有 `lucide-react`。统一 14/16/18/20 等尺寸体系。覆盖 new conversation / attach / send / stop / settings / more / remove / retry / agent selector / sidebar toggle / evidence / tool status。禁止混用多套 icon library。

# 27. Design Tokens

禁止大量 magic CSS。至少统一：sidebar width、conversation max-width、composer max-width、composer radius、spacing、radius、text colors、surface、border、hover、focus ring。具体数值根据 Codex visual audit 调整。

# 28. Typography

中文自然、英文代码自然、哲学长文易读、UI 小文字清晰。不得引入未经授权的 Codex/OpenAI 私有字体，使用项目系统字体栈。

# 29. Scroll Behavior

用户在底部时 streaming auto-follow；用户主动上滚后停止 auto-follow；新 token 不得强拉；用户回到底部后恢复 follow。切 Conversation 时恢复合理历史位置或末尾，但行为必须统一。

# 30. Race Safety

BLOCKER：

- A streaming → 切 B：A token 不进 B；回 A 状态正确。
- A = Nietzsche 正在运行 → B selector = General：A invocation 仍是 Nietzsche。
- A 有 draft attachment → 切 B：B 无 A attachments。
- Settings 开关：draft 不丢。

# 31. Responsive

至少测试 1920 / 1440 / 1280 / 1024 / narrow desktop。Sidebar 合理 collapse/drawer；Composer 不被挤爆；Attachment 不溢出；code/table 内部滚动；长 filename 截断。

# 32. Accessibility

icon-only button 必须有 aria-label、tooltip、keyboard focus；Tab 可导航；Escape 关闭 dropdown/dialog；focus visible；状态不只依赖颜色；中文 IME 专项测试。

# 33. Performance

禁止为了视觉重构引入大型 UI framework。重点控制 streaming 重渲染、Markdown 渲染粒度、Mermaid lazy、Object URL revoke、Settings/Dropdown 不重挂整个 Conversation、长对话可用性。

# 34. Recommended Component Architecture

```text
ConversationWorkspace
├── Sidebar
│   ├── NewConversationButton
│   ├── ConversationList
│   ├── ConversationItem
│   ├── AgentPlazaEntry
│   └── SettingsEntry
├── ConversationPane
│   ├── ConversationHeader
│   ├── MessageList
│   │   ├── UserMessage
│   │   ├── AssistantMessage
│   │   ├── ToolTrace
│   │   ├── EvidenceInline
│   │   └── FollowupSuggestions
│   └── Composer
│       ├── AttachmentTray
│       ├── AttachmentCard
│       ├── AutoGrowTextarea
│       ├── AttachButton
│       ├── AgentSelector
│       └── SendStopButton
└── Settings
    ├── SettingsNav
    └── SettingsSection
```

不得继续把所有逻辑堆进单一 `AgentPage.jsx`，但也不要制造几十个无意义一行组件。

# 35. State Ownership

Conversation Store：conversation_id / title / created_at / updated_at / messages。

Draft State：conversation_id / text / attachments / selected_agent。

Message State：message_id / conversation_id / role / agent_id / content / attachments / tool_events / evidence / status。

Invocation State：invocation_id / conversation_id / assistant_message_id / agent_id / status / abort_controller。

UI State：active_conversation / sidebar_state / settings_state / composer_focus / scroll_follow。

# 36. Persistence

Conversation persistence 应通过统一 abstraction，不得散落组件中。可采用 `ConversationStore.list/get/create/update/delete/persist`。后端已有真实能力则接后端；没有则使用项目现有本地 persistence，并明确边界。

# 37. Error UX

覆盖 network error / model error / attachment upload error / unsupported file / stream disconnect / tool error / citation fetch error / conversation load error。不得显示 stack trace，不把整个页面变红，优先局部恢复，retry 不得复制 user message。

# 38. Scope Preservation

必须完整保留：General、Nietzsche、message-level agent identity、streaming、answer_retract、Tool Trace、Evidence Contract、Citation、Reader Context、Follow-up、Markdown、Mermaid、Login、Conversation persistence、Stop/Retry、error handling。

# 39. Explicit Non-Goals

本 PRD 不允许顺带修改：RAG、Hybrid Retrieval、Graph、Memory、Persona、LoRA、Prompt、PremiseVerifier、Evidence Contract 语义、Answer Composer 策略、Agent loop、哲学家数据、无关主站页面。

UI 必须依赖缺失后端 contract 时，只允许实现最小必要 contract，并在最终回执报告。

# 40. Visual Acceptance Checklist

```text
[ ] Sidebar width / density
[ ] New conversation
[ ] Conversation row
[ ] Conversation hover
[ ] Active conversation
[ ] Message max-width
[ ] User message
[ ] Assistant message
[ ] Agent identity
[ ] Composer width
[ ] Composer radius
[ ] Composer padding
[ ] Textarea
[ ] Attach button
[ ] Agent selector
[ ] Send button
[ ] Stop button
[ ] Attachment card
[ ] Multi-attachment
[ ] Tool trace
[ ] Citation
[ ] Evidence
[ ] Follow-up
[ ] Settings entry
[ ] Settings layout
[ ] Dropdown
[ ] Focus states
[ ] Empty state
[ ] Streaming
[ ] Retract
[ ] Error
[ ] Long answer
[ ] Narrow window
```

明显偏离 reference 的项目必须继续调整。

# 41. Functional UAT

UAT-01：新建 → 输入 → General → streaming → final。

UAT-02：同会话 General → Nietzsche → General；每条 assistant identity 正确，历史不被全局 selector 改写。

UAT-03：上传单附件 → card → remove；未发送、状态清理正确。

UAT-04：多附件 → send；全部绑定正确 user message。

UAT-05：A draft attachments → B；B 不出现 A 附件。

UAT-06：A streaming → B；A token 不进入 B。

UAT-07：Streaming → Stop；UI/后端一致，placeholder 不悬挂。

UAT-08：Tool Trace compact、状态正确、无 raw CoT。

UAT-09：General + Nietzsche citation 都显示、都可点击、不依赖 currentAgent。

UAT-10：answer_retract 正确撤回 draft，final 不重复。

UAT-11：Settings 打开后返回；conversation / draft / selected responder 不丢。

UAT-12：长回答主动上滚时不被强拉到底部。

UAT-13：中文 IME composition Enter 不误发送。

UAT-14：窄窗口无严重破版。

UAT-15：刷新后当前项目承诺持久化的数据正常恢复。

# 42. Regression Gate

必须运行：agent-app existing tests、frontend lint、agent-app production build、main app production build、streaming regression、citation regression、attachment tests、conversation switching race、agent switching、settings state、IME、responsive smoke test。

# 43. Completion Gate

只有同时满足：

```text
VISUAL_PARITY = PASS
FUNCTIONAL_UAT = PASS
STREAMING = PASS
ATTACHMENTS = PASS
CONVERSATION_SWITCHING = PASS
AGENT_SWITCHING = PASS
CITATION = PASS
SETTINGS = PASS
RESPONSIVE = PASS
BUILD = PASS
REGRESSION = PASS
```

才允许：

```text
PHASE_UI_C = PASS
```

“看起来差不多”不算 PASS。

# 44. Final Receipt Format

```text
PHASE_UI_C = PASS / PARTIAL / FAIL
HEAD_BEFORE=
HEAD_AFTER=
CHANGED_FILES=
NEW_COMPONENTS=

REFERENCE_BASELINE=
VISUAL_PARITY=

SIDEBAR=
MESSAGE_RENDERER=
COMPOSER=
ATTACHMENTS=
ATTACHMENT_CARD=
AGENT_SELECTOR=
SEND_STOP=
TOOL_RENDERING=
CITATION=
FOLLOWUPS=
SETTINGS=
SCROLL=
RESPONSIVE=
ACCESSIBILITY=

CONVERSATION_RACE_UAT=
AGENT_SWITCH_UAT=
ATTACHMENT_UAT=
STREAMING_UAT=

FRONTEND_TESTS=
LINT=
AGENT_APP_BUILD=
MAIN_APP_BUILD=
REGRESSION=

BACKEND_CONTRACT_CHANGES=
KNOWN_DIFFERENCES_FROM_CODEX=
KNOWN_ISSUES=
```

# 45. Repository Placement

将本文件保存为：

```text
~/docs/PhiAgent_Conversation_Workspace_Design_Spec_v1.0.md
```

建议同时保存执行提示词：

```text
~/docs/PhiAgent_UI_C_Coding_Agent_Prompt.md
```

以后任何 UI 子任务优先引用本规范，而不是重新复制整份设计要求。

# 46. Execution Strategy

推荐：

```text
UI-C0  Baseline audit
UI-C1  State ownership + Conversation model
UI-C2  Workspace / Sidebar
UI-C3  Message renderer
UI-C4  Composer
UI-C5  Attachments
UI-C6  Agent selector
UI-C7  Tool / Citation / Evidence
UI-C8  Settings
UI-C9  Race / Scroll / Responsive / Accessibility
UI-C10 Visual parity + UAT + regression
```

除非实际仓库结构强烈要求，否则不要同时大改所有模块后再一次性测试。每个子阶段完成都应保持可构建、可运行。

# 47. Final Design Principle

最终体验必须让用户感受到：

> 我在一个专注、安静、可靠的哲学工作区里持续思考。

而不是：

> 我在一个装满许多 Agent 卡片的聊天网站里不断切机器人。

Conversation 是容器。Agent 是回答者。Evidence 是支撑。Reader Context 是背景。哲学内容本身才是主角。
