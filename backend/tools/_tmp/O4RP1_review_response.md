```text
O4_RP1_REVIEW = PASS
O4_FINAL_REVIEW = PASS

SHADOW_COGNITIVE_LAYER = COLLAPSED
GENERAL_COGNITIVE_CLASSIFIER = REMOVED
PRE_LLM_FACTUAL_CORRECTION_AUTHORITY = REMOVED
SEMANTIC_RUNTIME_DIRECTIVE_SITES = 0

ACCEPTED_SHA =
2de12b4ecbd5372ecba6258f99a7f3ca5ded14e1

O5_AUTHORIZED = true
```

U1/U2 的耗尽我不作为 O4 blocker：两次都是 **validator 真阳性 + invalid candidate 零发布**，并没有证明 Runtime 应重新取得认知权。把 VERIFY_NOW 之类塞回来只会复活刚删掉的 Shadow Agent。

但这两次失败必须进入后续质量账本：以后要从 **Main Agent policy / tool capability / 输出格式纪律 / 模型本身**解决，而不是重新造 gate。

# TASK — PhiAgent Orchestration Reset O5
## Thin Runtime / Mechanical Core Consolidation

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
2de12b4ecbd5372ecba6258f99a7f3ca5ded14e1

PRECONDITIONS:
O1_FINAL_REVIEW = PASS
O2_FINAL_REVIEW = PASS
O3_FINAL_REVIEW = PASS
O4_FINAL_REVIEW = PASS

DO NOT:
- merge master
- modify preservation branch/tag
- start O6
- add semantic intent classifier
- add source-attribution special gate
- add sufficiency/no_gain control
- restore runtime ghostwriting
- redesign retrieval/ranking/embedding/KG
- redesign Persona
- redesign specialized tools wholesale
```

## 0. Objective

O1–O4 已完成 authority reset。

现在目标不再是改变“谁做决定”，而是：

> **把已经失去认知职责的 Runtime 真正压缩成一个薄、可解释、可维护的机械执行层。**

目标 production path：

```text
Request
  ↓
Context Builder
  ↓
Main Agent
  ↕
Tool Executor
  ↕
Evidence Store
  ↓
Final Validator
  ↘ same-agent repair
  ↓
SSE Publisher
```

Runtime 只拥有：

```text
context assembly
tool schema/execution
hard ceilings
exact duplicate reuse
timeouts/cancel
permissions/safety
evidence recording
quote/citation validation
repair orchestration
SSE/provenance/timing
```

不得重新拥有：

```text
intent classification
research strategy
semantic sufficiency
answer composition
philosophical correction
semantic tool routing
```

---

## 1. FIRST — Runtime Residual Inventory

不要先删。

对当前 production request path 建立：

```text
O5_RUNTIME_RESIDUAL_INVENTORY
```

至少审计：

```text
engine_langgraph.py
agent_runtime.py
final_validator.py
evidence_contract.py
quote_bound.py
tool_contracts.py
agents.py
routes/agent_core.py
routes/agent_tools_*.py
```

对每个 production symbol 分类：

```text
M = REQUIRED_MECHANICAL
D = REQUIRED_DATA
P = PROTOCOL/OBSERVABILITY
L = LEGACY/DEAD
C = COGNITIVE_RESIDUE
X = DUPLICATED RESPONSIBILITY
```

输出：

```text
MODULE
SYMBOL
CALLERS
STATE_OWNED
SIDE_EFFECT
KEEP/MOVE/MERGE/DELETE
```

---

## 2. Collapse `ObligationLedger`

当前它已经不是 obligation system，只剩事实登记：

```text
read_chapters
primary_text_read
exact_quote_verified
term（已失去生产喂入口）
```

不要继续叫 `ObligationLedger`。

目标：

```text
ObligationLedger = REMOVED
```

将真正有价值的事实迁入现有：

```text
Evidence Store / EvidenceState
```

例如：

```text
read_sources
read_chapters
quote_verifications
citation_bindings
```

这些是：

```text
WHAT HAPPENED
```

不是：

```text
WHAT MUST HAPPEN
```

删除：

```text
term dead field
obligation naming
satisfied flags
required-tool semantics
legacy counters without consumer
```

不得创建 `EvidenceObligationLedger` 之类换皮对象。

---

## 3. Remove Dead `VERIFY_LATER` Machinery

当前已知：

```text
quote_bound.VERIFY_LATER_RE
```

无生产消费者。

审计所有：

```text
VERIFY_LATER
VERIFY_NOW
verification legacy fields
source_constraint leftovers
obligation terminology
```

若无 production value：

DELETE。

不要保留“以后可能用”。

目标：

```text
DEAD_VERIFICATION_POLICY_SYMBOLS_AFTER = 0
```

---

## 4. Simplify `agent_runtime.py`

重点找是否仍存在旧时代遗产：

```text
semantic counters
legacy rational stats
soft budget state
no_gain/sufficiency remnants
old obligation fields
compatibility-only trace fields
unused state transitions
```

保留真正需要：

```text
ToolLoopTrace
provenance
timing
exact duplicate state/cache
hard resource counters
tool outcome recording
EvidenceState
```

目标：

```text
AgentRuntime = EXECUTION STATE
```

不是：

```text
AgentRuntime = hidden policy state
```

---

## 5. Simplify `engine_langgraph.py`

O5 不要求重写 engine。

要求删除已经不再有价值的：

```text
dead branches
legacy compatibility branches
semantic telemetry calculations
unused prompt assembly paths
obsolete event transformations
old fallback comments/constants
shadow-era state variables
```

最终主循环应肉眼可读：

```text
build context
invoke agent

if tools:
    mechanically execute
    return results
    loop

if final:
    validate
    if pass:
        publish
    else if repair budget:
        return validation issues to same agent
    else:
        failure closeout
```

如果核心控制流仍要跨几百行寻找：
继续收敛。

但：

不要为追求漂亮而做全新 orchestration rewrite。
这是 in-place simplification。

---

## 6. Final Validator Consolidation

审计：

```text
final_validator.py
evidence_contract.py
quote_bound.py
```

目标不是强行合成一个巨型文件，而是明确职责：

### `quote_bound`

```text
extract quote-like spans
verify exact/near/stitched against evidence
```

### `evidence_contract`

```text
evidence provenance
citation/source binding facts
claim/evidence representation where mechanically required
```

### `final_validator`

```text
orchestrate deterministic validation
return ValidationResult
```

禁止三处各自重复：

```text
same regex
same citation parser
same quote classification
same evidence lookup
```

输出：

```text
DUPLICATED_VALIDATION_LOGIC_BEFORE=
DUPLICATED_VALIDATION_LOGIC_AFTER=
```

---

## 7. `EpistemicClaimClassifier` Naming / Scope Cleanup

当前已迁入 `evidence_contract.py`。

审计它是否仍包含非机械 cognitive taxonomy。

如果它确实只为：

```text
citation
quote
source-bound evidence
provenance
```

服务：

保留，但重命名可以考虑更准确的机械名称。

如果还会推断：

```text
scholarly interpretation
persona inference
claim strength
philosophical certainty
```

且这些结果没有机械消费者：

删除对应部分。

不要因为旧 evidence class taxonomy 在数据库/展示层有价值就误删 schema。

区分：

```text
stored provenance taxonomy
```

与：

```text
runtime philosophical judgment
```

目标：

```text
RUNTIME_EPISTEMIC_JUDGMENT = 0
```

---

## 8. Tool Internal Provenance Cleanup

O3 已把：

```text
tool_internal
parent_tool_call_id
```

建立起来。

现在删除旧的：

```text
pseudo=True fake top-level search records
fake search_books entries
兼容性伪日志
```

如果 Evidence Store 需要 internal retrieval：

记录真实结构：

```text
source = tool_internal
parent_tool_call_id = ...
tool = actual helper
```

禁止为了旧 citation UI 再伪造：

```text
Main Agent called search_books
```

目标：

```text
FAKE_TOOL_RECORDS_AFTER = 0
```

---

## 9. One Event Vocabulary

审计当前 SSE / trace 是否还有重复或旧事件：

```text
thinking_summary
thinking_summary_delta
tool_start
tool
tool_note
validation_failed
error
done
legacy reasoning_summary
thought_stream
answer_retract
auto-read pseudo events
```

O1/O2 已删除部分生产发射。

O5 目标：

```text
PUBLIC_EVENT_TYPES
```

收敛成真正使用的集合。

不要为了兼容保留永远不会再发出的生产代码路径。

前端可以继续容忍旧类型，但 backend 不必继续生成 dead types。

保持 backward-compatible payload where useful。

---

## 10. Thinking / Activity Separation Must Stay Clean

最终：

```text
thinking_summary = Main Agent public working note
tool_activity/tool_note = runtime mechanical status
answer = validated Main Agent final
```

禁止：

```text
activity → thinking
validator → thinking
runtime → answer prose
```

O5 不得破坏 O1/O2。

---

## 11. Hard Ceiling Behavior Cleanup

当前：

```text
hard_retrieval = 20
hard_total = 24
```

先不做性能调参。

审计：

```text
hard ceiling reached
→ extra invocation
```

O3 known issue #1 提到硬上限后可能多一轮 invocation。

若可以机械简化：

```text
tool declaration
→ RESOURCE_CEILING_REACHED returned
→ Main Agent gets outcome once
→ next decision
```

不要产生无意义额外 closeout invocation。

但不得：

```text
hard ceiling
→ runtime writes final
```

报告：

```text
HARD_CEILING_INVOCATIONS_BEFORE=
HARD_CEILING_INVOCATIONS_AFTER=
```

---

## 12. Main-Agent Formatting Discipline

O4-RP1 U1 暴露：

```text
模型把评注段落排成 blockquote
→ validator 正确当逐字主张拒绝
```

允许在核心 Main Agent policy 做**一个通用格式规则**：

```text
Use blockquote formatting only for text you intend to present
as a quotation/source text.

For your own analysis or paraphrase, use ordinary prose rather
than quote formatting.
```

这不是 source-attribution classifier。

这是：

```text
output format semantics
```

不根据问题类型触发。

同时保留：

```text
Never present remembered wording as an exact quotation
without supporting evidence.
```

不要扩成几十条 quote policy。

---

## 13. Tool Capability Guidance

保留 O4-RP1 对编号型作品的通用说明。

审计 tool descriptions：

确保：

```text
search_books = locate candidate text/sources
get_book_detail = inspect work metadata/directory
get_chapter = read primary chapter/content
websearch = external web retrieval
```

描述清楚即可。

禁止描述变成 routing policy：

```text
For task X MUST use A then B then C
```

---

## 14. Remove Dead Test Implementation Locks

继续使用 O4 mapping 原则。

对所有因 O5 删除 state/class/event 而失败的旧测试：

```text
OLD ASSERTION
USER-VISIBLE/ARCHITECTURAL VALUE
REPLACEMENT BEHAVIOR
```

不能只改到 green。

特别审计：

```text
ObligationLedger tests
verification legacy tests
pseudo tool-log tests
deprecated SSE event tests
legacy runtime stats tests
```

---

## 15. Structural Complexity Metrics

统计 BEFORE / AFTER：

```text
RUNTIME_PATH_LOC

ENGINE_LANGGRAPH_LOC
AGENT_RUNTIME_LOC

RUNTIME_STATE_CLASSES
RUNTIME_POLICY_CLASSES

PUBLIC_EVENT_TYPES_EMITTED

LEGACY_COMPAT_BRANCHES

DEAD_PRODUCTION_SYMBOLS

VALIDATION_DUPLICATION_SITES
```

不要为了 LOC 强拆小文件。

成功指标：

```text
fewer concepts
fewer state owners
shorter causal path
```

---

## 16. Runtime Irreducible Core Estimate

AUDIT-01 曾估：

```text
~600–900 LOC mechanical core
```

O5 不要求现在硬砍到 900。

需要重新估算当前真正不可约部分：

```text
tool executor
streaming
validation
evidence
safety
state/provenance
```

输出：

```text
IRREDUCIBLE_CORE_ESTIMATE=
CURRENT_RUNTIME_OVERHEAD=
```

告诉 Reviewer 剩下的 overhead 是：

```text
necessary complexity
or
future cleanup
```

---

## 17. Behavior Tests

新增：

```text
backend/tests/test_o5_thin_runtime.py
```

至少：

### T1 Evidence facts replace ObligationLedger

search/read/quote verification 后：

EvidenceState 正确记录事实。

无 ObligationLedger。

### T2 Dead term removed

不存在失去 producer 的 `term` legacy state。

### T3 No dead verification policy

无 production `VERIFY_NOW / VERIFY_LATER / source_constraint` control/policy symbol。

### T4 Final validator intact

unsupported quote/citation 仍拒绝。

### T5 Tool authority intact

Main Agent declared tool 仍只有机械门。

### T6 No fake tool record

tool-internal retrieval 不伪装成 main-agent top-level call。

### T7 Event vocabulary

生产正常请求不会产生：

```text
thought_stream
reasoning_summary
answer_retract
auto_read
```

### T8 Public ownership

thinking / activity / answer 三种 ownership 正确。

### T9 Hard ceiling

到 ceiling 后机械结果返回且无 ghostwrite/semantic closeout。

### T10 Format discipline

Main Agent base context 包含通用：

```text
blockquote == intended quotation
```

规则。

不要锁 exact wording。

### T11 Temporal persona intact

Persona Context 不受 runtime cleanup 影响。

### T12 Repair intact

validator→same-agent repair 正常。

---

## 18. Live UAT

### U1 — 言必有中出处

要求：

```text
自主 search/read
validator PASS
runtime thin path
无 legacy obligation state
```

重点观察 blockquote 格式失败是否改善。

### U2 — Source verification hard case

使用 O4-RP1 失败案例或同等难度。

记录：

```text
tools
repairs
publication status
```

不要为通过而加 special route。

### U3 — Deep synthesis

研究深度保持。

### U4 — zero-tool

简单题保持快速。

### U5 — Nietzsche temporal

Persona context 保持。

### U6 — repair

invalid candidate → same-agent repair。

### U7 — hard ceiling harness

确认 mechanical closeout。

---

## 19. Quality / Performance

与 O4 对照：

```text
PUBLICATION_SUCCESS_RATE
VALIDATOR_REPAIR_RATE

AVG_TOOLS
P50
P95

PRIMARY_READ
CITATION_INTEGRITY
QUOTE_INTEGRITY
ANSWER_DEPTH
```

尤其把：

```text
source-attribution UAT success
```

记录下来。

但：

失败不能通过恢复 semantic gate 修。

---

## 20. Full Regression

运行：

```bash
pytest backend/tests -q
```

不得 exclude。

单独报告：

```text
O1 causal
O1 thinking safety
O2 ownership
O3 authority
O4 collapse
O5 thin runtime
```

全部 green。

---

## 21. AFTER Runtime Graph

必须根据真实代码输出。

目标：

```text
Request
 ↓
Context Builder
 ↓
Main Agent
 ↕
Tool Executor ── EvidenceState
 ↓
Final Validator
 ├─ PASS → Publisher
 └─ FAIL → same Main Agent repair
```

不得仍出现：

```text
ObligationLedger
Planner
Sufficiency
InterpretationJudge
Composer
PremiseVerifier
```

---

## 22. O6 Preparation

O5 完成后不直接继续优化。

列出 O6 Quality Gate 所需冻结指标：

```text
architecture truth
tool/research behavior
source verification
deep synthesis
persona
multi-turn
latency
citation/quote integrity
error behavior
thinking UX
```

O6 将是整次 reset 的综合验收，不是继续架构开发。

---

## 23. Git / SHA Discipline

统一：

```text
BASE_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=
```

要求：

```text
HEAD_SHA == REMOTE_SHA
```

建议 commit：

```text
refactor(phiagent): consolidate thin mechanical runtime
```

如果报告回填产生后继：

明确 CODE_SHA / HEAD_SHA。

---

# FINAL RECEIPT

```text
O5 = READY_FOR_REVIEW / NOT_READY

BASE_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

FILES_CHANGED=
FILES_DELETED=
FILES_REDUCED=

OBLIGATION_LEDGER=
EVIDENCE_STATE=

DEAD_VERIFICATION_POLICY_SYMBOLS_AFTER=
RUNTIME_EPISTEMIC_JUDGMENT=

FAKE_TOOL_RECORDS_AFTER=

PUBLIC_EVENT_TYPES=
DEAD_EVENT_EMISSION_PATHS=

HARD_CEILING_INVOCATIONS_BEFORE=
HARD_CEILING_INVOCATIONS_AFTER=

RUNTIME_PATH_LOC_BEFORE=
RUNTIME_PATH_LOC_AFTER=

ENGINE_LANGGRAPH_LOC_BEFORE=
ENGINE_LANGGRAPH_LOC_AFTER=

AGENT_RUNTIME_LOC_BEFORE=
AGENT_RUNTIME_LOC_AFTER=

RUNTIME_STATE_CLASSES_BEFORE=
RUNTIME_STATE_CLASSES_AFTER=

RUNTIME_POLICY_CLASSES_AFTER=

VALIDATION_DUPLICATION_SITES_BEFORE=
VALIDATION_DUPLICATION_SITES_AFTER=

IRREDUCIBLE_CORE_ESTIMATE=
CURRENT_RUNTIME_OVERHEAD=

BLOCKQUOTE_POLICY=
TOOL_CAPABILITY_DESCRIPTIONS=

T1=
T2=
T3=
T4=
T5=
T6=
T7=
T8=
T9=
T10=
T11=
T12=

U1=
U2=
U3=
U4=
U5=
U6=
U7=

SOURCE_ATTRIBUTION_PUBLICATION_RATE=
VALIDATOR_REPAIR_RATE=

PRIMARY_READ_RATE=
CITATION_INTEGRITY=
QUOTE_INTEGRITY=
ANSWER_DEPTH=

AVG_TOOLS=
P50_LATENCY=
P95_LATENCY=

ENGINE_COGNITIVE_AUTO_TOOLS=
SEMANTIC_TOOL_CONTROL_EFFECTS=
RUNTIME_SEMANTIC_MUTATORS=
RAW_REASONING_PUBLIC=
INVALID_FINAL_PUBLIC=

O1_CAUSAL_TESTS=
O1_THINKING_SAFETY_TESTS=
O2_OWNERSHIP_TESTS=
O3_TOOL_AUTHORITY_TESTS=
O4_COLLAPSE_TESTS=
O5_THIN_RUNTIME_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

AFTER_RUNTIME_GRAPH=

O6_GATE_CANDIDATES=

REPORT=
docs/PHIAGENT_O5_THIN_RUNTIME.md

KNOWN_ISSUES=

STOP
```

**不得开始 O6。**

O5 的判断标准不是“删了多少行”，而是：

> **当前 Runtime 中每一个还活着的状态、类和分支，都必须能回答：我到底是在执行、验证、保存事实、保障安全，还是又在偷偷替 Main Agent 思考？**

答不出前四种，就该删。