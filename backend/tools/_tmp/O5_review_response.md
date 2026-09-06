```text
O5_REVIEW = PASS
O5_FINAL_REVIEW = PASS

THIN_RUNTIME = ACCEPTED
MECHANICAL_CORE_CONSOLIDATION = ACCEPTED
OBLIGATION_LEDGER = REMOVED
LEGACY_RUNTIME_POLICY = REMOVED

ACCEPTED_SHA =
e3692ec1de5b860787a5093a889de159cb0f10d7

O6_AUTHORIZED = true
```

O5 可以正式关闭。`4/7` publication rate **不挡 O5**：三次失败都是 validator 真阳性且零泄漏，这证明机械核心在做它该做的事。现在问题已经清楚地暴露为 Main Agent 的研究/引用/格式质量，而不是 Runtime 架构权责问题。

下一阶段不再继续重构。

# TASK — PhiAgent Orchestration Reset O6
## Integrated Final Quality Gate / Architecture Reset Closeout

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
e3692ec1de5b860787a5093a889de159cb0f10d7

PRECONDITIONS:

O1_FINAL_REVIEW = PASS
O2_FINAL_REVIEW = PASS
O3_FINAL_REVIEW = PASS
O4_FINAL_REVIEW = PASS
O5_FINAL_REVIEW = PASS

PHASE_TYPE =
EVIDENCE-ONLY FINAL GATE

DO NOT:
- modify production behavior
- patch failing cases
- tune prompts during the gate
- weaken validator
- change tool descriptions
- change tests to make gate green
- add semantic runtime rules
- merge master
- modify preservation branch/tag
- begin a new architecture phase

If a material failure is found:
REPORT IT.
DO NOT FIX IT IN O6.
Reviewer decides whether a narrow patch is required.
```

## 0. O6 Question

O6 不是问：

```text
“代码是不是更少了？”
```

而是问：

> **在把 Shadow Agent 拆掉之后，PhiAgent 是否已经成为一个真实由 Main Agent 驱动、证据充分、研究专业、答案可靠、可实际使用的哲学 Agent？**

最终必须同时验证：

```text
ARCHITECTURE TRUTH
+
RESEARCH QUALITY
+
ANSWER QUALITY
+
SOURCE/CITATION INTEGRITY
+
PERSONA QUALITY
+
MULTI-TURN QUALITY
+
THINKING UX
+
RUNTIME STABILITY
```

---

# 1. Freeze Gate SHA

开始前：

```bash
git status --short
git rev-parse HEAD
git rev-parse origin/refactor/phiagent-main-agent-orchestration
```

要求：

```text
LOCAL_HEAD == REMOTE_HEAD == BASE_SHA
SOURCE_WORKTREE_CLEAN = true
```

允许已有明确排除的 `_tmp/` runtime artifacts。

从此记录：

```text
GATE_SHA =
e3692ec1de5b860787a5093a889de159cb0f10d7
```

整个 Gate 中 production/source/test 不得变化。

Gate 结束再重新 hash/status。

若 production/test 文件漂移：

```text
O6 = INVALIDATED
STOP
```

---

# 2. Architecture Truth Gate

通过运行时 trace + 静态结构确认最终架构确实是：

```text
Request
 ↓
Context Builder
 ↓
Main Agent
 ↕
Tool Executor
 ↕
EvidenceState
 ↓
Final Validator
 ├─ PASS → Publisher
 └─ FAIL → same Main Agent repair ≤2
```

必须证明不存在生产控制权：

```text
Planner
Obligation system
Sufficiency controller
No-gain controller
Semantic admission
Interpretation judge
Answer composer
Premise verifier
Runtime final writer
Auto-read
Auto-websearch
```

Gate：

```text
ENGINE_COGNITIVE_AUTO_TOOLS = 0
SEMANTIC_TOOL_CONTROL_EFFECTS = 0
RUNTIME_SEMANTIC_MUTATORS = 0
RUNTIME_FACTUAL_APPENDS = 0
RAW_REASONING_PUBLIC = 0
RUNTIME_GENERATED_THINKING = 0
INVALID_FINAL_PUBLIC = 0
FAKE_TOP_LEVEL_TOOL_RECORDS = 0
```

全部必须为 0。

---

# 3. Authority Matrix Final Audit

生成最终 authority 表：

```text
DECISION                      OWNER

Interpret user request        Main Agent
Research strategy             Main Agent
Tool selection                Main Agent
Research continuation         Main Agent
Research stop                 Main Agent
Interpretation                Main Agent
Answer structure              Main Agent
Final natural-language text   Main Agent

Tool execution                Runtime
Hard resource ceiling         Runtime
Exact duplicate reuse         Runtime
Permission / safety           Runtime
Timeout / cancellation        Runtime

Evidence recording            EvidenceState
Quote verification            Validator
Citation verification         Validator

Repair content                Main Agent
Repair tool calls              Main Agent
Repair ceiling                Runtime mechanical
```

任何重复 cognitive owner：

```text
FAIL
```

---

# 4. Full Automated Regression

运行 EXACT：

```bash
pytest backend/tests -q
```

不得排除任何 test。

然后单独运行：

```text
O1 causal suite
O1 thinking-safety suite
O2 final-ownership suite
O3 tool-authority suite
O4 cognitive-collapse suite
O5 thin-runtime suite
```

记录：

```text
COLLECTED
PASSED
FAILED
SKIPPED
DURATION
```

要求：

```text
FAILED = 0
```

同时运行：

```text
regression_oldman_sea
```

无论它是否默认 pytest discover。

记录完整结果。

---

# 5. Evaluation Dataset

建立一组 **不在 prompt 中泄露期待工具序列** 的 O6 live set。

至少 24 个独立单轮问题。

分为 8 类，每类 3 题：

```text
A. Source Attribution / Exact Wording
B. Concept Explanation
C. Argument Analysis
D. Comparison
E. Historical / Genealogical
F. Textual Interpretation
G. Deep Synthesis
H. Philosopher Persona / Temporal
```

不得为了过关选全部已跑过的题。

要求：

```text
>= 12 个 fresh questions
<= 12 个 historical regression questions
```

历史回归可包括：

```text
言必有中
过犹不及
老人与海类误引
尼采深渊
Kant/Mill
QG2 representative cases
```

fresh cases 应覆盖不同哲学家/传统。

---

# 6. Source Attribution Gate

A 类至少 3 个 live cases，另外从全数据集中统计所有 source-sensitive cases。

每题检查：

```text
Did Agent research when warranted?
Did it read primary/local source when available?
Did it distinguish memory from evidence?
Did quote validator behave correctly?
Did citation map to retrieved evidence?
Did it avoid adjacent-passage stitching?
Did invalid candidate remain hidden?
```

指标：

```text
SOURCE_ATTRIBUTION_PUBLICATION_RATE
PRIMARY_READ_RATE
EXACT_QUOTE_VERIFIED_RATE
UNVERIFIED_QUOTE_PUBLIC_RATE
UNVERIFIED_CITATION_PUBLIC_RATE
STITCHED_QUOTE_PUBLIC_RATE
```

硬门：

```text
UNVERIFIED_QUOTE_PUBLIC_RATE = 0
UNVERIFIED_CITATION_PUBLIC_RATE = 0
STITCHED_QUOTE_PUBLIC_RATE = 0
```

注意：

publication failure 不等于 hallucination。

必须区分：

```text
SAFE_REJECT
vs
WRONG_PUBLIC_ANSWER
```

---

# 7. Publication Failure Taxonomy

O5 已暴露一个核心质量问题：

```text
validator 真阳性
+
Main Agent repair 失败
→ 安全但无答案
```

O6 必须系统统计。

每个不发布 case 分类：

```text
Q1 BLOCKQUOTE_MISUSE
Q2 MEMORY_WORDING_AS_EXACT
Q3 NEAR_TRANSLATION_NOT_MARKED
Q4 CITATION_CHAPTER_MISMATCH
Q5 SEARCH_LOCALIZATION_FAILURE
Q6 REPAIR_STRATEGY_FAILURE
Q7 HARD_CEILING
Q8 OTHER
```

输出：

```text
SAFE_REJECT_COUNT
SAFE_REJECT_RATE
REPAIR_ATTEMPT_COUNT
REPAIR_SUCCESS_RATE
REPAIR_EXHAUSTION_RATE
```

这会决定 reset 后是否还需 **Main-Agent Quality Patch**。

不要在 Gate 中修。

---

# 8. Research Quality Gate

对所有有工具题记录：

```text
declared tools
executed tools
exact reuse
tool errors
search/read progression
new evidence gained
```

人工/规则化审计：

### Good research

```text
locate
→ inspect useful evidence
→ read context
→ compare/interpret as needed
→ answer
```

### Search churn

```text
query synonym
→ query synonym
→ query synonym
→ same source
→ no new understanding
```

指标：

```text
AVG_TOOLS
MEDIAN_TOOLS
P95_TOOLS

SEARCH_CALLS
READ_CALLS

EXACT_DUPLICATE_REUSE_RATE
SEARCH_CHURN_CASE_RATE
HARD_CEILING_HIT_RATE
```

不要建立“工具越少越好”评分。

核心评价：

```text
EPISTEMIC_GAIN_PER_RESEARCH_CHAIN
```

可采用 Reviewer qualitative：

```text
HIGH / MEDIUM / LOW
```

并提供证据。

---

# 9. Evidence Appetite Gate

检查 Main Agent 没有因为去掉 Runtime Planner 退化成“凭模型记忆直接答”。

对：

```text
exact quotations
source attribution
historical facts
specific textual claims
```

检查是否主动寻证。

同时对普通概念题检查：

```text
zero-tool remains possible
```

目标不是：

```text
EVERY QUESTION USES TOOLS
```

而是：

```text
TOOLS WHEN THEY MATERIALLY IMPROVE THE ANSWER
```

---

# 10. Answer Depth Gate

C/D/E/F/G 类重点评估。

每题 0–4：

```text
0 = wrong / unusable
1 = shallow summary
2 = competent
3 = strong philosophical analysis
4 = expert-like structured analysis
```

评价维度：

```text
concept precision
argument reconstruction
dependency/tension analysis
counter-position quality
historical placement
primary-text grounding
interpretive nuance
limitations/uncertainty
```

输出：

```text
ANSWER_DEPTH_MEAN
ANSWER_DEPTH_MEDIAN
DEEP_CASES_SCORE_3_PLUS
```

不要用长度代替深度。

---

# 11. Adaptive Answer Form Gate

O4 已删除 AnswerComposer。

验证 Main Agent 是否自然根据问题改变形态。

检查 24 题是否仍全部塌缩成：

```text
“直接结论
理由一
理由二
反方
总结”
```

记录：

```text
DISTINCT_ANSWER_STRUCTURES
FORMAT_COLLAPSE = true/false
```

要求：

```text
FORMAT_COLLAPSE = false
```

例如：

出处题应短而证据化；
论证题应拆论证；
谱系题应体现历史转化；
深综合题可长；
苏格拉底式应互动。

---

# 12. Persona / Temporal Gate

至少：

```text
Nietzsche early/mid/late × 3
General control × 1
```

验证：

```text
persona isolation
period grounding
temporal differences
no General→Nietzsche leakage
no Nietzsche→General leakage
author voice does not override evidence truth
```

特别检查：

```text
late Nietzsche
→ period/context really different
```

而不是只有语气变化。

---

# 13. Multi-Turn Gate

至少 5 条 conversation，每条 4–6 turns。

### M1 Progressive refinement

```text
概念
→ 追问
→ 反例
→ 修正
→ 深化
```

### M2 User correction

用户指出：

```text
“你刚才把 X 和 Y 搞混了”
```

Agent 应处理 correction，不固守错误。

### M3 Agent switching

同一 conversation：

```text
General
→ Nietzsche
→ General
```

验证 message-level identity / context isolation。

### M4 Source follow-up

```text
“刚才那段原文再给上下文”
```

应正确利用 conversation + evidence。

### M5 Ambiguous reference

```text
“那他这里为什么又这样说？”
```

验证上下文解析。

记录：

```text
CONTEXT_CONTINUITY
CORRECTION_HANDLING
AGENT_ISOLATION
SOURCE_FOLLOWUP
REFERENCE_RESOLUTION
```

---

# 14. Thinking UX Gate

O1 的结构不仅要技术正确，还要实际可用。

抽取至少 10 个工具型 invocation。

检查：

```text
thinking appears before cognitive tool decision where model emits note
thinking reflects current uncertainty/evidence state
thinking is not mini-final answer
thinking is not raw CoT
thinking is not runtime prose
thinking updates after important evidence
tool activity fills execution wait honestly
```

禁止：

```text
fake “I am thinking...”
raw provider reasoning
runtime-generated cognition
```

输出：

```text
THINKING_CAUSAL_TRUTH_RATE
RAW_COT_PUBLIC = 0
RUNTIME_THINKING = 0
DUPLICATE_THINKING_EVENTS
DUPLICATE_TOOL_ACTIVITY_EVENTS
```

---

# 15. Event / SSE Gate

验证生产事件流：

```text
status
thinking_summary
thinking_summary_delta
tool_start
tool_note
tool
tool_cancel
token
validation_failed
error
done
suggestions
```

检查：

```text
event_id uniqueness
sequence ordering
tool_call_id binding
decision_group_id
initiated_by provenance
```

特别检查 reconnect/replay 或前端 reducer 条件若已有 harness。

要求：

```text
DUPLICATE_VISIBLE_EVENTS = 0
UNPARENTED_TOOL_RESULTS = 0
UNKNOWN_PROVENANCE_TOOL_EVENTS = 0
```

---

# 16. Final Ownership Gate

随机抽 10 个 successful answers。

证明：

```text
published semantic final
==
validated Main Agent candidate
```

允许：

```text
mechanical markdown/rendering normalization
```

不允许：

```text
runtime-added correction
runtime hedge
runtime citation downgrade
runtime factual append
```

指标：

```text
MAIN_AGENT_FINAL_OWNERSHIP_RATE = 100%
```

---

# 17. Validator Quality Gate

Validator 太松会 hallucinate；
太严会导致大量 safe reject。

所以同时测：

### Positive cases
正确 exact quote/citation → PASS

### Negative cases
unsupported / stitched / wrong citation → REJECT

至少 scripted：

```text
10 positive
10 negative
```

报告：

```text
VALIDATOR_TRUE_POSITIVE
VALIDATOR_FALSE_POSITIVE
VALIDATOR_TRUE_NEGATIVE
VALIDATOR_FALSE_NEGATIVE
```

这里定义：

```text
positive = invalid candidate
```

要求：

```text
FALSE_NEGATIVE = 0
```

False positive 如果 >0：
必须报告 blocker。

---

# 18. Repair Quality Gate

专门运行至少 8 个 controlled cases：

```text
quote failure ×2
citation failure ×2
near quote ×2
stitched quote ×1
empty candidate ×1
```

统计：

```text
REPAIR_SUCCESS_FIRST
REPAIR_SUCCESS_SECOND
REPAIR_EXHAUSTED
REPAIR_RESEARCH_USED
```

检查：

```text
repair feedback neutral
repair may use tools
runtime never tells exact cognitive action
```

---

# 19. Zero-Tool Gate

至少 5 个简单解释问题。

检查：

```text
TOOLS=0 when naturally sufficient
no hidden tool
no runtime research obligation
normal publication
latency
```

这防止 Evidence Appetite 变成强制 RAG。

---

# 20. Error / Failure Gate

至少 controlled harness：

```text
tool timeout
tool execution error
unknown tool
invalid schema
hard ceiling
model/provider error
validator exhaustion
cancel
```

要求：

```text
no stack trace to user
no false factual claim
no ghostwritten final
no invalid candidate leak
clean done/error state
```

---

# 21. Latency Gate

按类型统计：

```text
ZERO_TOOL
LIGHT_RESEARCH
DEEP_RESEARCH
REPAIR
PERSONA
```

输出：

```text
P50
P95
MAX
```

并拆：

```text
LLM_WAIT
TOOL_WAIT
VALIDATION_WAIT
REPAIR_WAIT
```

对比：

```text
O0 baseline
O1
O2
O3
O4
O5
```

不要要求恢复到最短。

判断：

```text
延迟是否由真实研究产生
还是 runtime overhead
```

---

# 22. Resource / RAM Regression

重复之前 RAM audit 核心项。

至少：

```text
idle backend
General first request
Nietzsche first request
10 sequential turns
```

记录：

```text
private working set / RSS
delta
```

检查：

```text
no per-turn monotonic leak
```

不要求和历史数字逐 MB 相同。

要求没有明显结构性回退。

---

# 23. General / Nietzsche Tool Surface

确认：

```text
General expected tool registry
Nietzsche expected tool registry
```

无 O1–O5 重构导致的：

```text
missing tool
duplicate tool
wrong agent exposure
```

Specialized tools至少 smoke：

```text
compare_views
dialectic
thought_experiment
conceptual_map
analyze_argument
essay_outline
socratic behavior
```

不用全部做深度 benchmark，但必须证明 registry/contract 没破。

---

# 24. Socratic Contract

至少两个 case。

要求用户要求：

```text
“只问我一个问题，不要直接给答案”
```

Agent：

```text
exactly one substantive question
no direct answer
```

第二轮能够继续。

不得由 Runtime 强制 route。

---

# 25. Citation / Quote UI Payload

检查：

```text
done
citation data
verified citation records
quote audit
```

确保 frontend 所需 metadata 仍存在。

尤其 O5 删掉旧 sanitize keys 后：

```text
UI contract not accidentally broken
```

若需要实际 frontend smoke：

执行。

---

# 26. Architecture Regression Search

静态扫描 production source。

禁止重新出现功能等价物：

```text
semantic admission
sufficiency force
no_gain force
verification intent routing
auto read
auto websearch
runtime semantic append
runtime answer rewrite
premise verifier
answer composer
interpretation judge
```

不要只按旧 class 名 grep。

做结构 + behavior 双审计。

---

# 27. Comparison Against Frozen O0

使用 preservation：

```text
phiagent-pre-orchestration-reset
a69149b7288766f43fcc4be1bc822da2f59027bd
```

给出最终 BEFORE / AFTER：

```text
runtime-path LOC
semantic policy LOC
decision owners
semantic regex
runtime semantic mutators
semantic tool gates
hidden cognitive tools
raw reasoning exposure

tests
tool behavior
source integrity
latency
answer quality
```

不要为了证明重构成功而美化 O0。

也不要只用 LOC 宣称成功。

---

# 28. Gate Verdict Matrix

每个维度：

```text
PASS
PASS_WITH_NOTE
FAIL
```

至少：

```text
G1 Architecture ownership
G2 Tool authority
G3 Final ownership
G4 Thinking truth
G5 Validator integrity
G6 Source verification
G7 Research quality
G8 Deep answer quality
G9 Persona/temporal
G10 Multi-turn
G11 SSE/provenance
G12 Error behavior
G13 Latency
G14 RAM/resource
G15 Tool/specialized capabilities
G16 Regression suite
```

---

# 29. Final Verdict Rules

### PASS

只有当：

```text
no architecture blocker
no invalid evidence leak
no validator false-negative
no major persona/multi-turn regression
no production runtime failure
```

并且整体 publication quality 可用于正式产品。

### PASS_WITH_REQUIRED_QUALITY_PATCH

允许架构完全成功，但出现：

```text
safe reject rate too high
repair success too low
search churn too high
Main Agent quote-format discipline unreliable
```

这种情况下：

```text
ARCHITECTURE RESET = PASS
PRODUCT QUALITY CLOSEOUT = REQUIRED
```

后续 patch 只能针对：

```text
Main Agent policy
tool capability clarity
evidence presentation clarity
model-facing context quality
```

禁止重新增加 Runtime semantic gate。

### FAIL

若出现：

```text
invalid final leaks
runtime cognitive authority returns
raw CoT leaks
tool results disappear
validator false-negative
serious persona/context corruption
```

---

# 30. No Cherry-Picking

24 单轮 + 5 multi-turn 必须全部列出。

失败案例不能从统计中删除。

不得重复跑直到挑最好的一次。

如果 provider 随机异常：

记录：

```text
PROVIDER_ERROR
```

可单独重跑一次用于判断基础设施，
但原始失败必须保留在报告。

---

# 31. Deliverables

生成：

```text
docs/PHIAGENT_O6_INTEGRATED_FINAL_QUALITY_GATE.md
```

若使用 evaluation harness：

仅允许：

```text
backend/tools/_tmp/
或明确 evaluation-only 文件
```

不得修改 production。

报告包含：

```text
gate SHA
test results
24 single-turn cases
5 multi-turn cases

architecture matrix
quality metrics
validator confusion matrix
repair metrics
publication metrics
latency
RAM
tool registry
thinking/SSE audit

O0 vs O6 comparison
all anomalies
final verdict proposal
```

Agent 不得自行签发最终 PASS。

---

# 32. Git

O6 是 evidence gate。

允许提交：

```text
docs/PHIAGENT_O6_INTEGRATED_FINAL_QUALITY_GATE.md
```

以及明确 evaluation-only harness（若必要）。

禁止 production/test behavior changes。

如果 commit：

```text
docs(phiagent): record O6 integrated final quality gate
```

统一：

```text
GATE_SHA = e3692ec1...
HEAD_SHA =
REMOTE_SHA =
```

`GATE_SHA` 永远表示实际被测 production SHA。

---

# FINAL RECEIPT

```text
O6 = READY_FOR_FINAL_REVIEW / BLOCKED

GATE_SHA=

HEAD_SHA=
REMOTE_SHA=

PRODUCTION_CODE_CHANGED=false
TEST_BEHAVIOR_CHANGED=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REGRESSION_OLDMAN_SEA=

SINGLE_TURN_CASES=
FRESH_CASES=
HISTORICAL_REGRESSION_CASES=

MULTI_TURN_CONVERSATIONS=
MULTI_TURN_TOTAL_TURNS=

G1_ARCHITECTURE=
G2_TOOL_AUTHORITY=
G3_FINAL_OWNERSHIP=
G4_THINKING_TRUTH=
G5_VALIDATOR_INTEGRITY=
G6_SOURCE_VERIFICATION=
G7_RESEARCH_QUALITY=
G8_DEEP_ANSWER_QUALITY=
G9_PERSONA_TEMPORAL=
G10_MULTI_TURN=
G11_SSE_PROVENANCE=
G12_ERROR_BEHAVIOR=
G13_LATENCY=
G14_RAM_RESOURCE=
G15_TOOL_CAPABILITIES=
G16_REGRESSION=

ENGINE_COGNITIVE_AUTO_TOOLS=
SEMANTIC_TOOL_CONTROL_EFFECTS=
RUNTIME_SEMANTIC_MUTATORS=
RAW_REASONING_PUBLIC=
INVALID_FINAL_PUBLIC=
FAKE_TOP_LEVEL_TOOL_RECORDS=

MAIN_AGENT_FINAL_OWNERSHIP_RATE=

VALIDATOR_TRUE_POSITIVE=
VALIDATOR_FALSE_POSITIVE=
VALIDATOR_TRUE_NEGATIVE=
VALIDATOR_FALSE_NEGATIVE=

PUBLICATION_SUCCESS_RATE=
SAFE_REJECT_RATE=

REPAIR_SUCCESS_RATE=
REPAIR_EXHAUSTION_RATE=

SOURCE_ATTRIBUTION_PUBLICATION_RATE=
PRIMARY_READ_RATE=
UNVERIFIED_QUOTE_PUBLIC_RATE=
UNVERIFIED_CITATION_PUBLIC_RATE=
STITCHED_QUOTE_PUBLIC_RATE=

SEARCH_CHURN_CASE_RATE=
HARD_CEILING_HIT_RATE=

ANSWER_DEPTH_MEAN=
ANSWER_DEPTH_MEDIAN=
DEEP_CASES_SCORE_3_PLUS=
FORMAT_COLLAPSE=

THINKING_CAUSAL_TRUTH_RATE=
DUPLICATE_VISIBLE_EVENTS=

ZERO_TOOL_SUCCESS=

P50_ZERO_TOOL=
P50_LIGHT_RESEARCH=
P50_DEEP_RESEARCH=
P50_REPAIR=
P95_OVERALL=

RAM_IDLE=
RAM_GENERAL=
RAM_NIETZSCHE=
RAM_10_TURN_DELTA=

GENERAL_TOOL_SURFACE=
NIETZSCHE_TOOL_SURFACE=
SPECIALIZED_TOOL_SMOKE=

O0_VS_O6_SUMMARY=

ANOMALIES=

PROPOSED_VERDICT=
PASS / PASS_WITH_REQUIRED_QUALITY_PATCH / FAIL

REPORT=
docs/PHIAGENT_O6_INTEGRATED_FINAL_QUALITY_GATE.md

STOP
```

**不得自行进入任何下一 Phase。完成后只把 O6 receipt + report 交给 Reviewer。**

O6 现在最值得看的已经不是“架构还干不干净”——那部分基本完成了。真正的问题变成了：

> **没有 Shadow Agent 替它兜底之后，这个 Main Agent 自己到底够不够好。**

这正是最终 Gate 应该回答的问题。