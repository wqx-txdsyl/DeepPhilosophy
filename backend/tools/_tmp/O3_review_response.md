```text
O3_REVIEW = PASS
O3_FINAL_REVIEW = PASS

TOOL_AUTHORITY = ACCEPTED
MAIN_AGENT_RESEARCH_CONTROL = ACCEPTED
SEMANTIC_ADMISSION_CONTROL = REMOVED

ACCEPTED_SHA =
e54a7f7c38dd83394390763bd1684485935e61f0

O4_AUTHORIZED = true
```

O3 核心目标已经达到：

```text
Main Agent declares tool
        ↓
Runtime checks only mechanical constraints
        ↓
execute / exact-reuse / mechanical failure
        ↓
result returned to Main Agent
```

而旧的：

```text
sufficiency
no_gain
verification quota
problem type
obligation satisfied
forced closeout
preferred tool
```

已经失去执行控制权。

特别重要的是，O2 的 repair round 现在也不再被旧 admission governance 卡死，这关闭了 O2 遗留的那个架构债。

U2 的 `PASS*` 我不当 O3 blocker。它实际上暴露了一个很有价值的下一阶段问题：

```text
Runtime 不再替 Agent 刹车
→ Agent 获得真实研究自由
→ 于是模型自己的研究策略质量开始裸露出来
→ 20 次执行 + 6 次复用 + 最终 validator 拒绝
```

这正说明我们现在终于看到了**模型本身**的问题，而不是 Shadow Runtime 在替模型做决定。不要回头加 semantic gate。

另外，`950be0a7e` 这种 report SHA 回填以后不要再写进“FINAL_SHA”语义里。后续统一：

```text
CODE_SHA = 实现 commit
HEAD_SHA = 当前 branch head
REMOTE_SHA = remote head
```

Reviewer 认 branch HEAD。不要再制造“代码 SHA / 文档 SHA / FINAL_SHA”三套口径。

---

# TASK — PhiAgent Orchestration Reset O4
## Cognitive Layer Collapse / Delete the Shadow Agent

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
e54a7f7c38dd83394390763bd1684485935e61f0

PRECONDITIONS:

O1_FINAL_REVIEW = PASS
O2_FINAL_REVIEW = PASS
O3_FINAL_REVIEW = PASS

DO NOT:
- merge master
- modify preservation branch/tag
- start O5
- redesign retrieval/ranking/embedding
- redesign Persona
- redesign 38 tools wholesale
- reintroduce semantic runtime control
```

## 0. Goal

O1–O3 已经把三种核心权力还给 Main Agent：

```text
O1:
next cognitive action ownership

O2:
final answer ownership

O3:
tool execution authority
```

现在大量旧 cognitive modules 仍然存在，但已经只剩：

```text
telemetry
prompt injection
dead branches
compatibility fields
tests protecting dead architecture
```

O4 的目标是：

> **删除已经失去权力的 Shadow Agent，而不是继续供养它。**

目标架构：

```text
Conversation / Persona / User context
        ↓
Context Builder
        ↓
Main Agent LLM
        ↕
Tool Executor
        ↕
Evidence Store
        ↓
Final Validator
        ↘ repair to same Main Agent
```

Runtime 不再需要：

```text
independent reasoning planner
problem-type cognitive controller
semantic obligation ledger
evidence sufficiency controller
interpretive hedge engine
answer-form controller
semantic stop planner
```

---

## 1. FIRST — Authority/Dependency Audit

不要先删。

从 BASE_SHA 建立：

```text
O4_COGNITIVE_LAYER_INVENTORY
```

逐模块审计至少：

```text
reasoning_plan.py
semantic_obligations.py
interpretation_engine.py
answer_composer.py
epistemic_guard.py
agent_runtime.py
engine_langgraph.py
tool_contracts.py
```

对每个 public class/function/field 分类：

```text
A = REQUIRED_MECHANICAL
B = REQUIRED_DATA/TELEMETRY
C = MAIN_AGENT_CONTEXT_INPUT
D = DEAD_COGNITIVE_CONTROL
E = COMPATIBILITY_ONLY
F = UNKNOWN
```

输出：

```text
MODULE
SYMBOL
CURRENT_CALLERS
CURRENT_EFFECT
USER_VISIBLE_EFFECT
CONTROL_EFFECT
DELETE/KEEP/MOVE
```

禁止只按文件名判断。

---

## 2. Delete-First Rule

如果某段逻辑已经：

```text
CONTROL_EFFECT = 0
```

且：

```text
没有独立数据价值
没有 validator 价值
没有 frontend protocol 价值
```

默认：

```text
DELETE
```

不是：

```text
“先留着以后可能有用”
```

O4 是 delete-first。

---

## 3. reasoning_plan.py

重点审计并拆除：

```text
problem_type
complexity
verification_intent
source_constraint

preferred tool routing
map hints
comparison hints
research planning
answer-form directives
tool budget semantics
source obligations
```

如果这些字段已经不控制：

```text
tool
stop
final
validator
```

则删除 production dependency。

Main Agent 不需要 Python 先告诉它：

```text
“这是 comparison”
“这是 source attribution”
“这是 deep synthesis”
```

再决定怎么思考。

允许保留的只有真正必要的 mechanical/context metadata。

目标：

```text
REASONING_PLAN_RUNTIME_AUTHORITY = 0
REASONING_PLAN_PRODUCTION_DEPENDENCY → ideally 0
```

若整个文件最终无必要 production caller：

删除文件。

---

## 4. semantic_obligations.py

O3 已把 obligation admission 权力归零。

现在审计：

```text
ObligationLedger
PRIMARY_SOURCE_READ
verification obligations
required tools
completion state
satisfaction state
```

如果只剩 telemetry：

问：

> 用户或 Main Agent 真正需要这个 telemetry 吗？

若答案否：

删除。

不要保留一个 500 行 ledger 只为了：

```text
done.obligations_satisfied=true
```

允许 Evidence Store 自己记录：

```text
what was retrieved
what was read
what was verified
```

但不需要“义务系统”。

目标：

```text
SEMANTIC_OBLIGATION_RUNTIME = REMOVED
```

---

## 5. RetrievalState Simplification

审计：

```text
no_gain
low_gain
sufficiency
round_all_low
semantic overlap
mark_round
forced state
```

O3 已使其 control effect=0。

区分：

### Useful observational evidence metadata

例如：

```text
retrieved source count
result source ids
exact duplicate
latency
```

可以保留。

### Shadow cognition telemetry

例如：

```text
evidence sufficient
query low semantic gain
all current evidence enough
```

默认删除。

尤其不要为了 dashboard 继续计算昂贵 semantic policy。

目标：

```text
RETRIEVAL_COGNITIVE_STATE_FIELDS_AFTER ≈ 0
```

保留真实 retrieval facts，不保留 runtime “判断”。

---

## 6. interpretation_engine.py

当前报告说：

```text
append = []
但 overclaim / tier detection 留在 done
```

现在问：

这些检测结果还有谁消费？

如果：

```text
只有 tests
只有 done telemetry
没有用户功能
没有 validator mechanical basis
```

删除 production path。

不要保存一个 Shadow Philosopher 只为了告诉我们：

```text
“模型可能解释过强”
```

这种判断应由 Main Agent 本身承担。

如果文件仍有其他实际独立用途，保留那部分。

目标：

```text
POST_LLM_INTERPRETIVE_JUDGE = 0
```

---

## 7. answer_composer.py

同样审计：

```text
answer form
shape
noise detection
strong wording
adaptive structure
fallback composition
```

O2 已把 final ownership 交给 Main Agent。

因此 runtime 不应再定义：

```text
“comparison 应该怎么组织”
“deep synthesis 应该有几部分”
“答案应该多长”
```

如果 composer 只剩 telemetry：

删除 production dependency。

机械 Markdown formatter 不属于 AnswerComposer；
若需要则移至 thin formatting helper。

目标：

```text
ANSWER_COMPOSER_COGNITIVE_ROLE = 0
```

---

## 8. epistemic_guard.py

谨慎拆。

必须区分两类：

### Mechanical verification

可能仍值得保留：

```text
citation binding facts
quote evidence facts
source provenance facts
```

这些应该迁入：

```text
FinalValidator / EvidenceStore
```

### Semantic judgment

删除：

```text
claim too strong
counterfactual interpretation too assertive
needs epistemic hedge
missing correction sentence
```

Runtime 不再判断哲学陈述“应该更谨慎”。

目标：

```text
EPISTEMIC_GUARD_SEMANTIC_JUDGMENT = 0
```

若机械部分迁移完：

删除/大幅瘦身该模块。

---

## 9. Tool Contracts

Phase T 的 tool contracts 有价值，但边界重新定义：

Keep:

```text
tool name
input schema
output schema
capability
side effects
interaction type
permission
```

Delete/neutralize:

```text
preferred cognitive route
answer ownership
main-agent override instructions
fallback reasoning strategy
semantic priority
```

Tool contract 是：

```text
CAPABILITY CONTRACT
```

不是：

```text
COGNITIVE POLICY ENGINE
```

---

## 10. Context Builder — One Place for Main-Agent Policy

把真正需要告诉 Main Agent 的原则收敛到一个清晰 Context Builder / system policy。

不要散落：

```text
reasoning_plan prompt
semantic_obligation directive
engine hint
tool-node hint
final repair hint
answer composer directive
```

Main Agent policy 应简洁包含：

```text
1. role/persona
2. available tools + capability descriptions
3. Evidence Appetite
4. source-grounding expectations
5. quote/citation truthfulness
6. public working-note behavior
7. same-agent repair feedback when applicable
```

目标：

```text
COGNITIVE_POLICY_INJECTION_SITES_BEFORE=
COGNITIVE_POLICY_INJECTION_SITES_AFTER=
```

尽量收敛到：

```text
1 primary builder
+ repair feedback
```

Repair feedback 是 validation event，不算第二套 cognitive planner。

---

## 11. Evidence Appetite Must Survive

删除 Planner 后不能变成：

```text
“模型随便答，不研究也行”
```

保留 Main Agent 的研究伦理：

```text
Use tools proactively when they improve reliability,
depth, or source grounding.

Do not stop merely because a plausible answer is already known.

Prefer direct evidence for verifiable claims, quotations,
source attribution, and historical claims.

For interpretation, seek enough evidence to represent the
strongest relevant readings.

Continue while additional evidence is likely to materially
improve the answer.

Avoid redundant mechanical searching.
```

不要把它实现成 runtime gate。

---

## 12. Prompt Injection Audit

枚举当前所有会向 Main Agent 注入 cognitive prose 的路径：

```text
system prompt
reasoning_plan directives
tool budget hints
sufficiency hints
no_gain hints
obligation hints
forced closeout hints
repair hints
specialized routing hints
epistemic hints
composer hints
```

O4 之后目标：

```text
SEMANTIC_RUNTIME_DIRECTIVE_SITES ≈ 0
```

允许：

```text
mechanical resource status
tool errors
validator issues
conversation/persona/context
```

---

## 13. Preserve Deterministic Core

绝对不要误删：

```text
FinalValidator
quote verification
citation verification
Evidence Store
conversation state
persona/temporal state
tool schemas
tool executor
permissions/safety
hard resource ceiling
exact duplicate reuse
timeouts/cancel
SSE framing
public Thinking provenance
```

O4 是删 Shadow Agent，不是删可靠性核心。

---

## 14. Test Migration Philosophy

AUDIT-01 已发现大量测试锁 implementation。

O4 允许删除/改写旧测试，但必须：

```text
OLD IMPLEMENTATION ASSERTION
→ map to actual behavior guarantee
→ preserve behavior test if still needed
```

不要因为模块删除就机械删测试。

建立：

```text
OLD_TEST
OLD_CONTRACT
CURRENT_USER_VALUE
KEEP/REPLACE/DELETE
NEW_TEST
```

尤其：

```text
reasoning_plan tests
semantic_obligation tests
answer_composer tests
interpretation_engine tests
epistemic_guard tests
```

---

## 15. Architecture Size Metrics

在 BEFORE / AFTER 统计：

```text
runtime-path LOC
cognitive-governance LOC
semantic regex count
decision points
cognitive authority owners
prompt injection sites
production runtime modules
```

不要追求 LOC 数字本身。

目标是：

```text
authority collapse
dependency collapse
```

报告：

```text
RUNTIME_PATH_LOC_BEFORE/AFTER
COGNITIVE_GOVERNANCE_LOC_BEFORE/AFTER

DECISION_POINTS_BEFORE/AFTER
COGNITIVE_AUTHORITY_OWNERS_BEFORE/AFTER

SEMANTIC_REGEX_BEFORE/AFTER
COGNITIVE_POLICY_INJECTION_SITES_BEFORE/AFTER
```

---

## 16. Dead-Code Proof

删除前后必须证明：

```text
no production import
no dynamic getattr/import
no FastAPI route dependency
no tests relying on deleted runtime API unintentionally
```

对删除文件运行：

```text
ripgrep
import graph
pytest
```

不要仅依据 IDE “0 references”。

---

## 17. O4 Behavior Tests

新增：

```text
backend/tests/test_o4_cognitive_collapse.py
```

至少：

### T1 No ReasoningPlan decision dependency

相同 scripted Main Agent output，
改变 problem_type/complexity telemetry 不得改变工具执行/answer publication。

### T2 No Obligation control dependency

改变 obligation state，
不影响 tool/stop/final。

### T3 No Sufficiency cognitive dependency

sufficiency true/false，
行为只取决于 Main Agent declaration。

### T4 No Interpretation runtime mutation

强解释性文本只经过 O2 validator；
runtime 不 hedge/rewrite。

### T5 No Composer ownership

不同 answer types 都由 Main Agent text 原样拥有。

### T6 Evidence Appetite prompt present

Main Agent core context 中仍有研究伦理。

但测试不要锁整段 prompt exact string；
检查 structured policy intent。

### T7 Single cognitive policy owner

production runtime 不存在多套 planner/directive owner。

### T8 Mechanical core intact

quote/citation validator、hard ceiling、duplicate、safety 仍工作。

### T9 Persona context intact

Nietzsche temporal context 仍进入 Main Agent。

### T10 Repair feedback intact

O2 validator issue 能返回 same Main Agent。

### T11 No semantic auto-tool

O1/O3 invariants still hold.

### T12 Zero-tool still possible

没有 planner 后简单题仍可零工具回答。

---

## 18. LIVE UAT

### U1 Source attribution

`言必有中出处`

要求：

```text
Main Agent自主 search/read
quote/citation PASS
无 Planner
无 obligation controller
无 runtime semantic directive
```

### U2 Deep synthesis

康德 vs 密尔/其他 QG2 深题。

要求：

```text
研究深度保持
无 AnswerComposer
无 InterpretationEngine 改写
```

### U3 Nietzsche temporal

要求：

```text
Persona/context 正常
philosopher tools 正常
```

### U4 Zero-tool

正常直接回答。

### U5 Repair

触发 invalid quote：

```text
validator
→ same Main Agent
→ repair
```

### U6 Research-heavy

观察删除 Shadow cognition 后：

```text
tool pattern
latency
research quality
```

特别记录是否出现 O3 U2 那种：

```text
search churn
hard-ceiling hit
```

不要用 runtime semantic gate 修。

若出现，记录为 Main-Agent research-policy/model-quality issue。

---

## 19. O3 U2 Search-Churn Audit

专项审计 O3 的：

```text
20 executions + 6 exact reuse
validator exhaustion
```

回答：

```text
WHY_DID_AGENT_KEEP_SEARCHING=
```

分类：

```text
A. poor tool descriptions
B. poor search result clarity
C. context pollution from legacy directives
D. Main Agent model behavior
E. hard-ceiling interaction
F. combination
```

O4 只能修：

```text
legacy directive pollution
duplicated/conflicting prompts
unclear capability descriptions
```

禁止恢复 semantic runtime stop gate。

若 Shadow-Agent directives 正在诱导机械搜索，
删掉后重跑对照。

这可能自然改善 latency/tool count。

---

## 20. Full Regression

运行：

```bash
pytest backend/tests -q
```

不得 exclude。

并分别：

```text
O1 causal
O1 thinking safety
O2 ownership
O3 tool authority
O4 collapse
```

全部必须 green。

---

## 21. Deleted Module Receipt

必须明确报告：

```text
FILES_DELETED=
FILES_REDUCED=
FILES_RETAINED=
```

每一个核心旧模块说明：

```text
reasoning_plan.py =
semantic_obligations.py =
interpretation_engine.py =
answer_composer.py =
epistemic_guard.py =
```

不要只说“cleaned up”。

---

## 22. Architecture Target Check

O4 后实际 production request path 应尽量接近：

```text
stream_agent
    ↓
build_context
    ↓
Main Agent
    ↕
Tool Executor
    ↕
Evidence Store
    ↓
Final Validator
    ↓
publish / same-agent repair
```

输出真实 AFTER graph。

如果 graph 仍然有：

```text
Planner
→ Obligation
→ Sufficiency
→ Interpretation Judge
→ Composer
```

则 O4 未完成。

---

## 23. Git

统一 SHA 口径：

```text
BASE_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=
```

其中最终要求：

```text
HEAD_SHA == REMOTE_SHA
```

不要再把 report-only 回填 SHA 称 FINAL_SHA。

建议 commit：

```text
refactor(phiagent): collapse shadow cognitive runtime
```

可以有 report-only 后继 commit，
但 receipt 必须明确：

```text
CODE_SHA
HEAD_SHA
```

---

# FINAL RECEIPT

```text
O4 = READY_FOR_REVIEW / NOT_READY

BASE_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

FILES_CHANGED=
FILES_DELETED=
FILES_REDUCED=
FILES_RETAINED=

REASONING_PLAN=
SEMANTIC_OBLIGATIONS=
INTERPRETATION_ENGINE=
ANSWER_COMPOSER=
EPISTEMIC_GUARD=

RUNTIME_PATH_LOC_BEFORE=
RUNTIME_PATH_LOC_AFTER=

COGNITIVE_GOVERNANCE_LOC_BEFORE=
COGNITIVE_GOVERNANCE_LOC_AFTER=

DECISION_POINTS_BEFORE=
DECISION_POINTS_AFTER=

COGNITIVE_AUTHORITY_OWNERS_BEFORE=
COGNITIVE_AUTHORITY_OWNERS_AFTER=

SEMANTIC_REGEX_BEFORE=
SEMANTIC_REGEX_AFTER=

COGNITIVE_POLICY_INJECTION_SITES_BEFORE=
COGNITIVE_POLICY_INJECTION_SITES_AFTER=

SEMANTIC_RUNTIME_DIRECTIVE_SITES=

EVIDENCE_APPETITE_POLICY=
FINAL_VALIDATOR_INTACT=
EVIDENCE_STORE_INTACT=
PERSONA_CONTEXT_INTACT=

O3_U2_SEARCH_CHURN_ROOT_CAUSE=
O3_U2_AFTER_COMPARISON=

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

ENGINE_COGNITIVE_AUTO_TOOLS=
SEMANTIC_TOOL_CONTROL_EFFECTS=
RUNTIME_SEMANTIC_MUTATORS=
RAW_REASONING_PUBLIC=

O1_CAUSAL_TESTS=
O1_THINKING_SAFETY_TESTS=
O2_OWNERSHIP_TESTS=
O3_TOOL_AUTHORITY_TESTS=
O4_COLLAPSE_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

AFTER_RUNTIME_GRAPH=

O5_CANDIDATES=

REPORT=
docs/PHIAGENT_O4_COGNITIVE_LAYER_COLLAPSE.md

KNOWN_ISSUES=

STOP
```

**不得开始 O5。**

O4 的核心判断非常简单：

> 如果一个模块现在既不能决定工具、不能决定停止、不能决定最终答案、也不能做机械验证，那么它就必须证明自己还有存在价值。

证明不了，就删。