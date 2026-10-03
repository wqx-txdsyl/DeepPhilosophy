# PHIAGENT O1 — Single-Agent Causal Loop / Thinking Truth

Phase: **O1**（Orchestration Reset 第 1 阶段）
Branch: `refactor/phiagent-main-agent-orchestration`
Baseline: `phiagent-pre-orchestration-reset`（PRESERVATION_SHA = `a69149b7288766f43fcc4be1bc822da2f59027bd`）
状态: **READY_FOR_REVIEW**（O1 架构已获 ACCEPTED; §10 为 RP1 thinking-safety 闭合记录,
最终 PASS 由独立 Reviewer 签发）

---

## 0. 架构目标与结果

恢复真实因果链：

```
Main Agent invocation → 公开工作笔记（thinking_summary, initiated_by=main_agent）
  → tool declaration → tool_start → tool result → observation
  → NEW Main Agent invocation → next decision → final
```

| 指标 | BEFORE | AFTER |
| --- | --- | --- |
| ENGINE_COGNITIVE_AUTO_TOOLS | 1（R1 单次请求内：引擎代执行 get_chapter ×1） | **0**（结构性: auto-read / auto-websearch 代码已删除） |
| RUNTIME_IMPERSONATION_PATHS | 4 条活跃路径 | **0**（全部删除） |
| TOP_LEVEL_TOOL_WITHOUT_AGENT_DECISION | 1（get_chapter, R1 实测） | **0**（U1–U6 + T1–T8 实测） |
| THINKING_AFTER_TOOL_BEFORE_NEXT_TOOL | 无（tool result → 直接引擎代执行） | 合法（tool_result → 新 invocation → 新笔记 → 下一工具; T3 断言） |

### 汇总指标行

```text
ENGINE_COGNITIVE_AUTO_TOOLS_BEFORE=1   # R1: _ensure_primary_read 代执行 get_chapter
ENGINE_COGNITIVE_AUTO_TOOLS_AFTER=0

RUNTIME_IMPERSONATION_PATHS_BEFORE=4
  P1  _ensure_primary_read（agent_node 内）——代执行 locate+read, 注入"这就是你自己的核验动作"
  P2  stream_agent 收口 _ensure_primary_read 终局安全网——代执行 + "原典核验补正"正文补发
  P3  auto-read tool 事件回放 + "已完成主文本核验读取" 注记——runtime 文案表现为 Agent 核验行为
  P4  引擎摘要生成器 _gen_summary（独立 mini-LLM 以"思考摘要器"人设代笔）+ _INTENT_THINKING
      第一人称意图模板 —— runtime 冒充 Main Agent thinking（R1 实测 227 条事件）
  附: auto-websearch（search_books 空结果后 runtime 自行执行 websearch）——认知代执行,
      不带身份注入文案, 单列于隐藏路径
RUNTIME_IMPERSONATION_PATHS_AFTER=0

TOP_LEVEL_TOOL_WITHOUT_AGENT_DECISION=0   # AFTER; BEFORE=1（R1 get_chapter）
THINKING_AFTER_TOOL_BEFORE_NEXT_TOOL=OK   # causal order 由 decision_group_id + T3 保证
```

---

## 1. BEFORE causal trace（先复现, 不准先改）

复现方式: baseline 分支原代码, 真实 DeepSeek LLM, 提问 **"言必有中出处"**（R1 生产反例）。
采集器: `backend/tools/_tmp/o1_trace_harness.py`（临时脚本, 不入库）, 输出
`backend/tools/_tmp/o1_before_r1.json`（1345 事件, 全程 54.2s）。

事件流关键序列（EVENT_SOURCE 判定见采集器 classify()）:

```text
t=14.9   RUNTIME   thinking_summary/delta ×227   ← 引擎摘要生成器（mini-LLM）冒充 Agent 思考
t=16.6   MAIN_AGENT tool search_books ×2（模型并行宣告）
         MAIN_AGENT tool search_books（另一关键词）
         MAIN_AGENT tool get_book_detail → 检索准入拒绝（RUNTIME 注记）
t=33.6   MAIN_AGENT thought_stream（模型原生 reasoning）——开始凭"系统已读取"的记忆作答
t=47.2   RUNTIME   tool get_chapter              ← _ensure_primary_read 代执行（无任何模型宣告）
t=47.2   RUNTIME   tool_note「已完成主文本核验读取：候选篇章原文已读取并在全文中核对措辞。」
t=48.5   MAIN_AGENT token（最终回答, 含凭注入段落写出的 blockquote 与"已逐字核验"断言）
         VALIDATOR token（「原典核验：…已读取…完成逐字核验…」——收口引用可见性补发）
```

对任务书 A–F 问题的回答（BEFORE）:

| 问题 | 答案 |
| --- | --- |
| A. 第一次 search 是谁决定的？ | **Main Agent**（模型 tool_call 宣告） |
| B. 第二次 search 是谁决定的？ | **Main Agent**（换关键词补充, 模型宣告） |
| C. get_chapter 是谁决定的？ | **Runtime**（`_ensure_primary_read` 代执行; 模型从未宣告 get_chapter） |
| D. 第二次 search result 与 get_chapter 之间是否存在 Main LLM invocation？ | **NONE 存在declared read 的 invocation**——期间只有准入拒绝注记与模型凭记忆作答的 reasoning; get_chapter 由引擎在 agent_node 内部（LLM 之外）执行 |
| E. 「已完成主文本核验读取」是谁生成的？ | **Runtime**（stream_agent 收口阶段回放注入） |
| F. 是否存在 runtime 生成文本被表现为 Main Agent thinking？ | **是, 227 条**（`_gen_summary` mini-LLM 摘要 + 第一人称意图模板） |

附加发现: 模型自身 reasoning 中出现「系统提示已经读取过论语先进篇原文」——归因倒置被模型
在思维链中直接复述, 证实注入词污染了模型的自我叙事。

---

## 2. 删除的隐藏路径（removed hidden paths）

全部在 `backend/engine_langgraph.py` / `backend/agent_runtime.py`:

| # | 路径 | 处置 |
| --- | --- | --- |
| 1 | `_ensure_primary_read()` + `AUTO_READ_THOUGHT`（T1.1-B 引擎兜底 auto-read, agent_node 调用点 + 收口终局安全网两处调用点） | **整体删除**（~150 行）。读取改由 prompt 层引导: 铁律 1「检索—阅读闭环」+ 收口轮「最后核验机会」提示（模型仍自主宣告, admission 放行 forced 轮 read） |
| 2 | auto-read tool 事件回放 + 「已完成主文本核验读取」tool_note | **删除** |
| 3 | auto-websearch（tools-node SSE 分支中 search_books 空结果 → 引擎自行执行 websearch） | **删除**。websearch 仍对模型可用（铁律 6/6'）, 由模型自主宣告（T7） |
| 4 | `_gen_summary` 摘要生成器（独立 mini-LLM, PRE_TOOL/SUMMARY_DIRECTIVE） | **删除**。thinking_summary 只允许来自模型自己的输出 |
| 5 | `_INTENT_THINKING_ZH/EN` 第一人称意图模板（tool_note 兜底冒充意图） | **删除**, 替换为 `_activity_line()` 机械活动注记（ACTIVITY 口吻, 非思考） |
| 6 | `ObligationLedger.auto_primary_read` 标志 | **删除**（`primary_text_read` 只能由模型自己的 get_chapter 置位） |

**保留**（deterministic validation, 属 §9 允许范围）:
`quote_bound.verify_quote` / `QuoteBound` audit / `LiveCitationSanitizer` / `evidence_contract`
/ 收口一致性扫描 / 已核验引用可见性补发（其触发前提 exact_quote_verified 现在只能由模型
读取达成; 补正文本为校验声明, 不再代执行工具、不产生 thinking）。检索准入（admission）、
预算、无增益收敛等机械治理全部保留——它们不发起认知动作。

---

## 3. Event provenance contract

所有 tool activity / thinking 事件新增字段（全部 optional, 不破坏现有 SSE event type;
前端 if/else 分发忽略未知字段与未知类型）:

```text
initiated_by:      main_agent | runtime_mechanical | tool_internal | validator
decision_group_id: "inv-N"（N = 本次请求内第 N 次 Main Agent invocation）
tool_call_id:      模型 tool_call 的原生 id（tool_start 来自首个 tool_call_chunk;
                   tool 事件来自 ToolMessage.tool_call_id）
parent_tool_call_id: 保留字段——引擎层暂无嵌套工具调用, tool-internal 检索明细留待后续 Phase
```

赋值规则:

| 事件 | initiated_by | 说明 |
| --- | --- | --- |
| `tool_start` | main_agent | 只在观测到模型 tool_call_chunk 时发出 |
| `tool`（结果） | main_agent | 决定（宣告）来自模型; 执行/复用/准入拦截属机械层 |
| `tool_note` | runtime_mechanical | 活动注记（宣告后立即 running 状态）/ 结果解读 / 准入中性说明 |
| `thinking_summary(_delta)` | main_agent | 内容只可能是模型 rationale 标签或工具轮公开工作笔记 |
| validator 收口补发（token） | 不打标 | 非工具活动; 阶段耗时入 `done.timing` 与 trace JSONL |

trace JSONL（`agent_runtime.ToolLoopTrace.record_call`）同步携带 `initiated_by /
decision_group / tool_call_id`; 新增 `record_phase()` 记录 `llm_invocation` 与 7 个
`validator_*` 阶段 duration_ms（§13 timing observability）。`done` 事件新增
`causal`（engine_cognitive_auto_tools=0 / main_agent_tool_decisions / agent_invocations）
与 `timing`（阶段汇总）块。

RP1 (O1-RP1) 修订: `thought_stream`（raw reasoning 透传通道）与 `reasoning_summary`
（runtime 摘要通道, mini-LLM 与确定性兜底两路）事件不再由引擎发出——用户可见
Thinking 事件只剩 `thinking_summary(_delta)`（main_agent）与 `tool_note`
（runtime_mechanical, ACTIVITY）。

---

## 4. Thinking contract（PUBLIC THINKING 定义）

`thinking_summary` = **Main Agent 主动写给用户看的工作判断摘要**。

允许的数据源（且仅限）:
1. 模型在内容通道显式写出的 `<rationale>…</rationale>`（RationaleParser 提取, 标签剥离）;
2. 模型在工具轮写出的**公开工作笔记**——系统提示铁律 0 要求: 还要调用工具的轮次, 先用
   1~4 个自然句写当前知道什么/还有什么不确定/为什么下一步做这个动作/新证据改变了哪个假设,
   尚未核验的内容用"可能/我记得/待核验"口吻。该笔记在首个工具宣告出现时归位为
   thinking_summary（causal order: invocation → thinking → declaration → tool_start）。

**provider 私有推理 ≠ public Thinking（RP1, O1-RP1 修订）**: provider reasoning_content
（raw chain-of-thought）是 provider-private 数据——引擎一律**内部丢弃**（不转发 / 不累积 /
不落盘 / 不摘要冒充）。O1 旧文「reasoning_content 只走 `thought_stream` 展示通道, 原样透传,
不进入 thinking_summary」**已废除**: `thought_stream` 不再由引擎发出（前端按事件类型分发,
该类型缺席即无此通道）; public Thinking 统一以 `thinking_summary(_delta)` 为唯一事实来源。

禁止: raw CoT / provider reasoning_content 的任何形式公开（原样展示、runtime 总结 raw CoT
后展示、mini-LLM 转写后展示——已删除的 `_post_reasoning_summary` 即 `_gen_summary` 变体,
确定性 `build_reasoning_summary` 兜底属 Python 编造, `reasoning_summary` 事件随之废除）、
Python runtime 编造的思考、tool_note 冒充思考、final answer 提前重述、policy engine 的决定。
模型没写公开内容时就允许没有 Thinking（只有 tool activity）——不伪造。

配套流式阈值调整: `STREAM_ANSWER_DELAY` 48 → 240——工作笔记（1~4 句）不再超过
实时回答阈值而以回答形态泄出再撤回; 撤回机制保留为超长规划文字的兜底。

模型没有写笔记时, UI 空窗由机械活动注记填补（「正在检索「言必有中」…」/「正在读取《论语》
章节原文…」）——ACTIVITY, 不是思考; 绝不伪造「我正在深入思考」。

---

## 5. Causal order contract（§5）实现要点

- 每次回到 agent 节点（tools→agent）计为新 invocation, `decision_group_id` 递增;
- 工具宣告只能来自当前 invocation 的 tool_call_chunks（架构上 LangGraph 图保证:
  tools_node 只执行 last message 上声明的 calls; O1 删除了图外的两条代执行路径）;
- tool batch N 结束后出现下一批认知工具 ⇒ 中间必有新 invocation（T3 用 decision_group
  数值断言; U1 实测 get_chapter 的组号严格大于 search 的组号）;
- 一个 thinking/decision 可并行宣告多个工具（T4: 同组多工具不算缺 thinking）。

---

## 6. 行为测试（backend/tests/test_o1_causal_loop.py, 13 项全绿）

测试走 production path（真实 LangGraph 图 + 真实工具桩 + ScriptedChat 假 LLM 按 DeepSeek
流形输出 content 分片 + tool_call_chunk）, 断言对象是 SSE 事件流的 provenance 字段,
不是 grep 源码:

| 测试 | 内容 |
| --- | --- |
| **Streaming Blockquote Split Behavior**（O0 S5 witness 转正式） | chunk A=`> 「`, chunk B=`鲁人为长府…` → blockquote 完整保留（`> 「鲁人为长府…`）; MEMORY_ONLY 跨 chunk 整块转 paraphrase; production 流末验证未裂 |
| T1 No hidden primary read | 脚本 search→read→final: 工具事件 = 宣告集合（无额外）, 全部 initiated_by=main_agent, `causal.engine_cognitive_auto_tools==0`, locate 桩零调用; 台账 primary_text_read 由模型读取置位且无 auto_primary_read 键 |
| T2 No runtime impersonation | 事件层禁词（「这就是你自己的核验动作」/「已完成主文本核验读取」/「原典核验补正」等）零命中; thinking_summary 全部 main_agent; 结构护栏 `not hasattr(EG, "_ensure_primary_read")` |
| T3 Main-Agent Between Tool Batches | get_chapter 的 decision_group_id 严格大于 search 的; agent_invocations ≥ 3 |
| T4 Parallel Batch Allowed | 同一 decision 内并行两工具 → 同组, 两个 tool 事件齐全 |
| T5 Runtime Mechanical Action | tool_note 全部 runtime_mechanical; 无第一人称认知表述; 每个 tool_start 后立即有 activity 注记（running 状态） |
| T6 Event Provenance | tool/tool_start/tool_note/thinking_summary 事件全部携带合法 initiated_by + decision_group_id |
| T7 No auto-websearch | search_books 空结果后 websearch 桩零调用、零事件（模型保留自主选择权） |
| T8 No auto-read | 模型只 search 不宣告 read → 无 get_chapter 事件, locate 桩零调用, primary_text_read=False |
| Timing | done.timing.phases 含每次 invocation 的 llm_invocation 计时 + validator_* 计时, 均带 duration_ms |

回归: `tests/` 全套 **392 passed**（含更新后的 `test_phase_t1.py`——原 auto-read 触发用例
替换为删除一致性用例; `test_phase_s.py` S2 撤回场景 fixture 按 O1 阈值修正）。

---

## 7. LIVE UAT（真实 DeepSeek LLM, 采集器同 BEFORE）

| # | 场景 | 结果 | 关键证据 |
| --- | --- | --- | --- |
| U1 | 言必有中出处 | **PASS** | trace: thinking → search×2 → thinking → get_book_detail → thinking → get_chapter → final。MAIN_AGENT_TOOL_DECISIONS=3 ≥2; ENGINE_COGNITIVE_AUTO_TOOLS=0; 正确篇章《论语·先进篇》; primary_read=true; exact_quote_verified=true; 正式引用【《论语》·先进篇】已核验; blockquote 渲染为 NEAR 并诚实标注（模型措辞与原文标点差异）; stitching=0。工作笔记示范: 首轮「我记忆里此语出自《论语·先进篇》…让我查目录并读取原文」（工作假设≠已核验事实）, 读后确认 |
| U2 | “过犹不及”出处+上下文 | **PASS** | 模型主动 3×search + list_books + 2×get_chapter; quote near-verified 诚实标注, unverified_blockquote=0, stitched=0; 义务满足 |
| U3 | 深哲综合题（康德 vs 功利主义说谎） | **PASS** | 深度未因笔记缩短而下降: compare_views + 2×search + get_chapter + list_books; 3 条引文（2 exact / 1 near）, stitched=0; 回答 3999 字 |
| U4 | zero-tool（直接解释思想实验） | **PASS** | 0 工具、1 次 invocation——不为制造 thinking 凭空调用工具; 无伪造思考 |
| U5 | Nietzsche temporal（晚期·永恒轮回） | **PASS** | philosopher_period 由模型**首先**宣告, 随后 concepts/quote/corpus/graph 全部自主选择 |
| U6 | 检索失败（杜撰伪引文“存在即合理的彼岸性原则”） | **PASS** | 模型自主 5×search + 2×get_chapter + get_book_detail（运行时未代决）; 最终诚实降级: 无法逐字核验、辨析"存在即合理"误读、二手来源标注转述层级 |

AFTER 各场景 runtime 发起工具数 / 冒充事件数: **0 / 0**（全部六场）。

---

## 8. 质量对照（vs O0 baseline, 单跑口径, LLM 方差存在）

| 指标 | BEFORE（R1 复现） | AFTER（U1） | 说明 |
| --- | --- | --- | --- |
| RESEARCH_DEPTH | search×2 + 引擎代读 | search×2 + 目录确认 + 模型自主读 | 阅读从"代执行"变为"模型决策" |
| PRIMARY_READ_RATE | 1（但为引擎代执行） | 1/1（U1、U2 均模型自读） | 归因真实 |
| CITATION_INTEGRITY | 通过（补发撑起） | 通过（模型自给 + validator 兜底） | 未退化 |
| QUOTE_INTEGRITY | NEAR 被当作已核验渲染 | NEAR 诚实标注, MEMORY_ONLY 转写 | 未退化（更诚实） |
| STITCHING | 0 | 0（U1/U2/U3 全部） | 持平 |
| TOOL_ERRORS | 0 | 0 | 持平 |
| LATENCY | 54.2s（R1） | 38.0s（U1） | -30%（摘要生成器删除减少 227 事件与 1 次 mini-LLM 串行调用; 单跑口径仅供参考） |
| TOOL_COUNT | 4 事件（含 1 引擎代执行） | 4（全部模型宣告） | TOOL_COUNT 未作为成功指标; 本轮成功标准是 CAUSAL_TRUTH |

AFTER 六场汇总（n=6）: AVG_TOOLS=5.3; P50_LATENCY≈39.2s; P95_LATENCY≈101.4s（U3 综合题,
n 小取最大值）。

---

## 9. Known issues / 后续 Phase 边界

1. **tool-internal 检索未拆**: compare_views/confrontation 等内部检索 helper 仍以
   `tool_internal`/伪 search_books 日志进证据池（§7 允许, 后续 Phase 处理工具权威边界）;
   `parent_tool_call_id` 预留未启用。
2. **`main_agent_tool_decisions` 口径**: 按"每 invocation 内去重工具名"计数（并行同名宣告
   记 1 次）; 审计需要精确到 call id 时以 trace JSONL 为准。
3. **完整 AIMessage 帧**: stream_mode="messages" 偶发完整 AIMessage（无 tool_call_chunks）
   时, 该帧宣告不产生 tool_start（基线既有行为, 保留未改; 工具仍执行, 结果事件用
   `_dg()` 兜底归组）。
4. **U1 blockquote 行内拼接**: 模型把 blockquote 接在段末同一行 → sanitizer 按 leadin
   引文处理（NEAR 标注）, 未渲染为独立引用块——模型排版问题, 非引擎断裂（split witness
   测试证明跨 chunk 不裂）。
5. **原 `RATIONAL_STATS` 语义**: 现仅统计模型自产笔记条数; 引擎代笔时代的全局计数不再可比。

---

## 10. RP1 — Public Thinking Safety + Baseline Gate Closure（O1 Review Patch 1）

Reviewer 判定: O1_CORE_ARCHITECTURE=**ACCEPTED**, O1_REVIEW=**PATCH_REQUIRED**
（P0: raw provider reasoning 不得进入用户可见 SSE）。本节为 patch 1 的闭合记录。

### 10.0 Base SHA provenance（只读记录, 未改历史 / 未 rebase / 未 force push）

```text
PRESERVATION_SHA = a69149b7288766f43fcc4be1bc822da2f59027bd  # chore(phiagent): freeze pre-orchestration-reset baseline
O1_BASE          = 10ecef4effef38a019b1d46c81bd3c9d9cdd6506  # feat: 补齐空壳书《爱弥儿》全译本 + 分章规范入库
O1_COMMIT        = c7566730a96b99e9841b7c2965196829302218f9  # refactor(phiagent): restore single-agent causal tool loop
PRE_PATCH_SHA    = 4454c5b36bb0472e701bdaac6a967537eaa44bbd  # O1 之后 2 个 OSS 同步无关 commit 之后的 HEAD
```

- WHAT_IS_10ECEF: **书籍内容导入 commit**（《爱弥儿》全译本 32e4ebd33ddc 入库 + 分章规范）,
  是 preservation 的直接子代, 与编排/引擎无关。
- COMMITS_BETWEEN_PRESERVATION_AND_O1_BASE: **1**（即 10ecef4 本身）。
- FILES_CHANGED_BEFORE_O1_BASE: **13 个文件, 零代码**——`app/public/books.json`、
  `app/public/book_detail/32e4ebd33ddc.json`、`backend/data/book_chapters/32e4ebd33ddc/*`（8）、
  `docs/BOOK_SHELL_INVENTORY.md`、`AGENTS.md`。引擎/路由/工具/前端代码 diff 为空。
- WITHIN_O1_SCOPE: **true**（O1 基线代码与 preservation 代码完全一致, 差异仅为书籍数据与文档）。

### 10.1 P0 修复（结构性移除, 非字符串过滤）

`backend/engine_langgraph.py`:

1. **raw 透传删除**: agent 块中 `additional_kwargs.reasoning_content` → `thought_stream`
   逐片公开发射路径删除, 改为内部丢弃（不转发 / 不累积 / 不落盘 / 不摘要）。
2. **事后摘要通道删除**: `_post_reasoning_summary`（mini-LLM 浓缩 raw reasoning_text——
   被禁的 `_gen_summary` 变体）与确定性 `build_reasoning_summary` 兜底（Python 编造伪思考）
   一并删除; `reasoning_summary` 事件随之废除。话题建议（`suggestions`）非思考内容, 保留。

公开 Thinking 事实来源收敛为: `thinking_summary(_delta)`（仅 模型 rationale / 公开工作笔记）。

### 10.2 RP1 行为测试（backend/tests/test_o1_rp1_thinking_safety.py, 4 项全绿）

Scripted provider 在 `AIMessageChunk.additional_kwargs` 上按 DeepSeek 流形注入
`reasoning_content = PRIVATE_REASONING_SENTINEL_7F31`（sentinel 只用于测试, 不参与生产逻辑）,
断言用户可见 SSE 两个口径（按事件序拼接 + 全字段收集）sentinel 出现次数 = 0:

| 测试 | 内容 |
| --- | --- |
| T1 私有推理+公开笔记并存 | sentinel=0; 工作笔记进 thinking_summary（main_agent）; thought_stream=0; reasoning_summary=0 |
| T2 仅有 reasoning_content 无笔记 | sentinel=0; 零伪造 Thinking（thinking_summary/delta = 0）; 允许只有 tool activity; 回答照常 |
| T3 rationale 通道（来源 B） | sentinel=0; rationale 照常进 thinking_summary; `<rationale>` 标签零泄漏 |
| T4（U4 口径）zero-tool | tools=0; 不凭空 Thinking; sentinel=0; done.causal 引擎代执行=0 |

**杀伤力验证**: 在 PRE_PATCH 引擎上同套测试 **4/4 失败**（sentinel 按序拼接口径命中
thought_stream 泄漏; 注意 sentinel 按 10 字符分片注入, 整串计数式断言抓不到劈开泄漏——
必须按用户阅读顺序拼接后断言）。另按 RP1 契约反转改写
`test_answer_composer.py::test_stream_agent_no_runtime_reasoning_summary_event`
（原断言"必须补发确定性推理摘要"与 RP1 禁令相反）。

### 10.3 Exact baseline test gate（patch 后 FINAL SHA, 未排除任何文件）

```text
FULL_TEST_COMMAND = pytest backend/tests -q
COLLECTED = 424    PASSED = 424    FAILED = 0    SKIPPED = 0    DURATION = 176.01s
pytest backend/tests/test_o1_causal_loop.py -q
CAUSAL = 13 passed in 25.59s
```

（过程记录: 首轮全量 423 passed + 1 failed, 唯一失败即上述 composer 旧契约测试,
改写为 RP1 契约后全绿; 无文件排除、无 collection 操纵。）

### 10.4 LIVE UAT 重跑（真实 DeepSeek, 采集器同 O1）

| # | 场景 | 结果 | 关键证据 |
| --- | --- | --- | --- |
| U1 | 言必有中出处 | **PASS** | trace `o1_rp1_after_u1.json`（600 事件, 29.6s）: thought_stream=**0**; reasoning_summary=**0**; thinking_summary×3 全部 MAIN_AGENT（笔记示范:「我先核实…能否定位到原文」）; tool×5 / tool_start×3 全部 MAIN_AGENT（search×3+get_book_detail+get_chapter）; tool_note×8 全部 RUNTIME; done.causal: engine_cognitive_auto_tools=0, main_agent_tool_decisions=3, agent_invocations=4; 引用/引文完整性保持（正式引用《论语·先进篇》已核验） |
| U4 | zero-tool（思想实验直接解释） | **PASS** | trace `o1_rp1_after_u4.json`: tools=0; thought_stream=0; reasoning_summary=0; thinking_summary=0（模型未写笔记 → 无任何伪造思考, 仅 token×190 + 机械事件）; engine_cognitive_auto_tools=0; main_agent_tool_decisions=0; 回答正常流出 |

### 10.5 Event source audit（最终生产用户可见）

```text
PUBLIC_THINKING_SOURCES = thinking_summary(_delta): initiated_by=main_agent
                          （仅两个来源: 模型 <rationale> / 工具轮公开工作笔记）
                          tool_note: initiated_by=runtime_mechanical（ACTIVITY, 非思考）
                          tool/tool_start: initiated_by=main_agent（top-level 认知工具）
RAW_PROVIDER_REASONING_PUBLIC = 0   # thought_stream 事件=0（U1/U4 活体实测）; 发射路径已结构性删除
RUNTIME_GENERATED_THINKING    = 0   # reasoning_summary 事件=0; mini-LLM/Python 兜底两路已删除
ENGINE_COGNITIVE_AUTO_TOOLS   = 0   # done.causal（U1/U4 活体 + T1/T4 脚本断言）
TOP_LEVEL_TOOL_WITHOUT_AGENT_DECISION = 0
```

---

## 11. Git

- Branch: `refactor/phiagent-main-agent-orchestration`（仅此分支; 未 merge master;
  未动 preservation tag/branch）
- O1 commit: `refactor(phiagent): restore single-agent causal tool loop`（c7566730a）
- RP1 commit: `fix(phiagent): close O1 thinking safety review`

STOP — O1 与 RP1 边界内工作完成, 未开始 O2。最终 PASS 由独立 Reviewer 签发。
