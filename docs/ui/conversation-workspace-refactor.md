# PhiAgent Conversation Workspace 重构设计文档

## 1. 目标

把当前 PhiAgent 从“左侧智能体列表 + 右侧单 Agent 聊天”改为“会话优先”的工作区：

- 左侧：Conversation History
- 右侧：Active Conversation
- 输入区：Composer + Agent Selector
- 智能体广场：从主导航降级为独立发现入口
- 同一 Conversation 内允许切换 Agent
- 每条 Assistant Message 独立记录 `agent_id`
- Streaming / Tool / Citation 必须绑定 Conversation 与 Message，不能依赖全局 `currentAgent`

本阶段只做 Conversation Architecture 与 Agent Selection UX，不修改 RAG、Graph、Memory、Persona、LoRA、Epistemic Guard。

## 2. 页面结构

```text
┌──────────────────────┬───────────────────────────────────────────────┐
│ DeepPhilosophy       │ Conversation Header                           │
│ PhiAgent             │ 尼采与永恒轮回                         ···   │
│                      ├───────────────────────────────────────────────┤
│ ＋ 新对话            │                                               │
│ ◇ 探索智能体         │                  Messages                     │
│                      │                                               │
│ 今天                 │ User                                          │
│ 尼采与永恒轮回       │ ……                                            │
│ 老人与海 × 加缪      │                                               │
│                      │ Nietzsche                                     │
│ 昨天                 │ ……                                            │
│ 康德的自由问题       │                                               │
│                      │ [工具] [引用]                                 │
│ 过去 7 天            │                                               │
│ 道德谱系第三章       │ 可继续探索                                    │
│                      │ [问题 A] [问题 B] [问题 C]                    │
│                      │                                               │
│ ⚙ 设置               │ ┌─────────────────────────────────────────┐  │
│ 登录 / 用户          │ │ [尼采 ▾] 问一个哲学问题……          ↑ │  │
│                      │ └─────────────────────────────────────────┘  │
└──────────────────────┴───────────────────────────────────────────────┘
```

视觉原则：沿用现有黑白灰、克制、阅读型产品气质；不做 Coding IDE、Discord、彩色 SaaS 模板风；Conversation 是视觉主体。

## 3. Sidebar

顶部显示 DeepPhilosophy / PhiAgent，操作为 `＋ 新对话`、`◇ 探索智能体`。

历史会话按“今天 / 昨天 / 过去 7 天 / 更早”分组，空分组不显示。Conversation item 主要显示 `conversation.title`，当前会话只用轻微背景差异表示 active。Hover 显示 `···`，至少支持重命名、删除，删除需确认。

Conversation list 独立滚动；设置、登录/用户信息固定底部。

### 空会话防污染

点击“新对话”只创建临时 Draft：

```text
new draft
→ 用户发送第一条消息
→ persist conversation
→ 出现在 Sidebar
```

连续点击“新对话”不得产生多个永久空记录。

## 4. Conversation Header 与标题

右侧顶部显示 `conversation.title`，而不是当前 Agent 名。右侧 `···` 至少支持重命名、删除。

第一条消息后生成标题，优先 deterministic 规则，不为标题强制新增一次昂贵 LLM 调用。建议中文约 8~20 字，允许用户手动重命名。

## 5. 数据模型

Conversation 不永久绑死某个 Agent：

```json
{
  "conversation_id": "conv_1",
  "title": "尼采与永恒轮回",
  "default_agent_id": "nietzsche",
  "last_used_agent_id": "nietzsche",
  "created_at": "...",
  "updated_at": "...",
  "reading_context": {}
}
```

Assistant Message 必须保存 `agent_id`：

```json
{
  "message_id": "msg_1",
  "conversation_id": "conv_1",
  "role": "assistant",
  "agent_id": "nietzsche",
  "content": "...",
  "citations": [],
  "tool_events": [],
  "created_at": "..."
}
```

历史回答身份只能来自 `message.agent_id`，绝不能由当前 `selectedAgent/currentAgent` 推断。

## 6. Composer + Agent Selector

输入区改为：

```text
┌──────────────────────────────────────────────────────┐
│ [ 尼采 ▾ ]    问一个哲学问题……                 ↑  │
└──────────────────────────────────────────────────────┘
```

Agent Selector 属于 Composer。Popover 至少有：

```text
通用
- 深哲：跨哲学家研究、原典检索、比较分析

作者
- 尼采：著作、思想、生平、原典

探索更多智能体 →
```

打开旧会话时 Composer Agent 优先级：`last_used_agent_id` → `default_agent_id` → `general`。切换 selector 只影响下一轮发送，不改变历史消息。

## 7. Agent Plaza

保留智能体广场，但从 Navigation 改为 Discovery。点击“探索智能体”优先打开大 Modal / Drawer。

每张 Agent Card：Avatar、Name、Description、Capabilities/Tags、开始对话。

点击“开始对话”应创建临时 Conversation，并把所选 Agent 设为默认 Composer Agent，而不是进入永久 `/nietzsche` 聊天孤岛。

## 8. 同一 Conversation 切换 Agent

必须支持：

```text
User: 永恒轮回是什么？
[Nietzsche] ……

User: 深哲，你评价一下尼采刚才的回答。
[General] ……
```

共享：Conversation messages、用户问题、Reading Context、公开历史回答。

隔离：Agent-specific persona、private runtime state、memory namespace、tools/config。

## 9. Streaming Ownership

不得破坏现有 Streaming Contract。Invocation 创建时冻结：

```json
{
  "invocation_id": "...",
  "conversation_id": "...",
  "assistant_message_id": "...",
  "agent_id": "nietzsche",
  "status": "streaming"
}
```

所有 token/tool/citation/completion/error event 都必须可归属 `conversation_id + assistant_message_id + agent_id`。

关键行为：

- Nietzsche Streaming 时切 selector 到 General：当前回答仍属于 Nietzsche，下一轮才 General。
- Conversation A Streaming 时打开 B：A 后续 token 只能写回 A，不能进入 B。
- 删除正在 Streaming 的会话：优先禁止删除或先 abort；Late Event 不得复活已删除会话。

## 10. ToolCard / Citation / Suggested Follow-up

Tool event 必须归属于 `assistant_message_id`，不能只是页面级 transient state。

Citation 必须属于 Assistant Message：`message → citation → source`。不得根据全局 `currentAgent` 决定历史 citation 是否显示。复核并修复任何类似 `agent !== 'general' ? null : <CiteLink />` 的逻辑。General 与 Nietzsche Citation 都必须可见、可点击。

保留“可继续探索”。若用户未主动切 Agent，可沿用来源回答的 `message.agent_id`；如果用户已主动切换 Agent，则尊重当前 Composer Agent。规则必须稳定并有测试。

## 11. Empty State 与 Reading Context

新 General Conversation 可显示：

```text
深哲
今天想探索什么？
[一个哲学概念] [一本正在阅读的书] [比较两位哲学家]
```

从 Agent Plaza 选择 Nietzsche 后显示克制的 Nietzsche 空状态，不做夸张角色扮演欢迎词。

Reader Context 必须保留/兼容现有接口，逻辑上支持：

```json
{
  "reading_context": {
    "book_id": null,
    "chapter_id": null,
    "selected_text": null
  }
}
```

## 12. Routing / Persistence

Conversation 应成为稳定 identity。推荐：

```text
/agent
/agent/c/:conversationId
```

刷新后应恢复 title、messages、每条 Assistant 的 agent identity、citations、允许持久化的 tool info、default/last used agent、reading context（若已有）。

匿名用户可继续使用 localStorage；登录用户复用现有 persistence。本阶段不要为了历史记录引入大型数据库。

建立统一 `ConversationStore` 抽象，至少提供：

```text
listConversations()
getConversation(id)
createConversation()
updateConversation()
deleteConversation()
appendMessage()
updateMessage()
setConversationTitle()
setDefaultAgent()
setLastUsedAgent()
```

避免 React 组件到处直接操作 localStorage。未来应能从 `LocalConversationStore` 平滑替换为 `APIConversationStore`。

## 13. Responsive / Loading / Error

桌面优先。窄屏 Sidebar 收起为 Drawer，Composer 始终可用，无横向溢出。

至少处理：Conversation list loading、会话加载失败+重试、会话不存在、Agent 不可用。Agent 不可用时禁止静默切换其他 Agent 回答。

## 14. Race Conditions 必须覆盖

1. A Streaming → 打开 B → A token 不进入 B。
2. Nietzsche Streaming → Selector 切 General → 当前仍 Nietzsche。
3. 连续 New Conversation → 不产生空历史污染。
4. Delete Conversation → Late Event 不得复活。
5. Refresh → 已完成消息一致恢复。
6. 当前 Agent 改变 → 历史 Message/Citation/Tool 身份不变。

## 15. 推荐组件结构

```text
AgentWorkspace
├── ConversationSidebar
│   ├── NewConversationButton
│   ├── ExploreAgentsButton
│   ├── ConversationGroup
│   ├── ConversationItem
│   └── UserFooter
├── ConversationView
│   ├── ConversationHeader
│   ├── MessageList
│   │   ├── UserMessage
│   │   └── AssistantMessage
│   │       ├── AgentIdentity
│   │       ├── AnswerContent
│   │       ├── ToolCards
│   │       ├── Citations
│   │       └── SuggestedFollowups
│   └── Composer
│       ├── AgentSelector
│       ├── Input
│       └── SendButton
└── AgentPlaza
    └── AgentCard
```

不要继续把所有状态堆进巨大 `AgentPage.jsx`，但也不要借机做无关大重构。

## 16. 本阶段禁止扩大范围

禁止修改：Nietzsche 六库、Knowledge Graph、Memory Architecture、Persona Evolution、Epistemic Guard、LoRA、LLM、RAG、哲学内容 Prompt。禁止为了 UI 重写整个 LangGraph。必须保留 ToolCard、Citation、“可继续探索”和现有 Streaming。

## 17. UAT

- UAT-01：新对话 → Nietzsche → 提问 → Streaming → 首条消息后进入 Sidebar。
- UAT-02：完成对话 → Refresh → title/messages/agent/citation 正确恢复。
- UAT-03：同一会话 Nietzsche → General，历史身份正确。
- UAT-04：Streaming 中切 Selector，当前 invocation 不换 Agent。
- UAT-05：Streaming 中切 Conversation，不串 token。
- UAT-06：General/Nietzsche Citation 均可见可点击。
- UAT-07：ToolCard 切会话后仍正确归属。
- UAT-08：“可继续探索”行为与 Agent 规则正确。
- UAT-09：Agent Plaza → Nietzsche → 临时 Conversation + 默认 Nietzsche。
- UAT-10：删除会话无 Ghost History。
- UAT-11：空 Draft 不污染历史。
- UAT-12：窄屏 Sidebar/Composer 可用，无横向溢出。

## 18. Regression

必须验证：General Agent、Nietzsche Agent、Streaming、Tool calls、ToolCard、Citations、Suggested Follow-ups、Auth State、Reader Context（若已有）、Markdown、Code Block、Error Handling。

执行仓库当前实际存在的 backend tests / frontend tests / lint / build，不要猜命令。

## 19. 完成 Gate

```text
conversation_first_architecture = true
message_level_agent_identity = true
same_conversation_agent_switch = true
historical_agent_identity_preserved = true
stream_bound_to_conversation = true
stream_bound_to_message = true
stream_bound_to_agent = true
conversation_switch_race_safe = true
agent_switch_race_safe = true
citation_not_dependent_on_global_agent = true
tool_events_not_dependent_on_active_page = true
agent_plaza_is_discovery_not_navigation = true
suggested_followups_preserved = true
refresh_recovery = true
empty_conversation_pollution_prevented = true
```

## 20. 开工与回执

开工前记录：

```bash
git rev-parse HEAD
git status --short
git log -5 --oneline
```

禁止 reset / clean / checkout 覆盖用户工作。

最终回执至少包含：

```text
PHIAGENT_CONVERSATION_WORKSPACE = PASS / PARTIAL / FAIL
BASE_SHA:
FINAL_SHA:
CHANGED_FILES:

conversation_first:
message_level_agent_identity:
composer_agent_selector:
agent_plaza:
same_conversation_agent_switch:
stream_contract_preserved:
stream_race_safe:
citations_preserved:
nietzsche_citations_visible:
tool_cards_preserved:
suggested_followups_preserved:
refresh_recovery:
legacy_migration:
responsive:

TESTS:
backend:
frontend:
lint:
build:

UAT_01..UAT_12:
KNOWN_LIMITATIONS:
SCOPE_VIOLATIONS:

git diff --stat BASE_SHA..FINAL_SHA
git status --short
```

关键未完成项存在时禁止写 PASS。完成后停止，不开始 Epistemic Guard / RAG / Graph / Memory / Persona 下一阶段。
