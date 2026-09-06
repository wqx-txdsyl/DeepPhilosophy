```text
O4_REVIEW = PATCH_REQUIRED
O4_CORE_COLLAPSE = ACCEPTED
O5_AUTHORIZED = false
```

主体重构是成功的：`semantic_obligations.py / interpretation_engine.py / answer_composer.py` 已删除，runtime path -42%，O1–O3 的 ownership 全部保持，350/350 全绿。

但 O4 还没完全达到自己定义的目标。现在剩下的不是“大改”，而是 **Shadow Agent 最后几根神经**：

```text
reasoning_plan
→ verification_intent / source_constraint / VERIFY_NOW
→ Main Agent

PremiseVerifier
→ runtime 判定事实
→ correction/context injection
→ Main Agent

多个 runtime injection site
→ Main Agent
```

尤其你自己的回执里同时出现：

```text
SEMANTIC_RUNTIME_DIRECTIVE_SITES = 0
```

和：

```text
plan C 类注入：
VERIFY_NOW 纪律 + 来源约束 + 时期

PremiseVerifier 事实注入
核验状态注入
```

这两件事不能同时为真。

所以不进入 O5，先做一次很窄的 O4-RP1。

# TASK — O4-RP1
## Remove the Last Cognitive Injection Paths

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
946e9abc783d086b998f5e6bab30f5dbeb9dae15

O4_REVIEW =
PATCH_REQUIRED

DO NOT:
- start O5
- restore deleted Shadow modules
- modify retrieval/ranking
- modify tool authority
- weaken O2 validator
- remove Persona/temporal behavior
- add replacement intent classifier
```

## 0. Objective

O4-RP1 只回答一个问题：

```text
Main Agent 在收到用户请求之后，
是否还存在另一个 Python cognitive layer
先解释“这是什么问题、现在该怎么认识它”
再把自己的判断注入给模型？
```

最终目标：

```text
GENERAL_COGNITIVE_CLASSIFIER = 0
SEMANTIC_RUNTIME_DIRECTIVE_SITES = 0
PRE_LLM_FACTUAL_CORRECTION_AUTHORITY = 0

PRIMARY_COGNITIVE_POLICY_OWNER =
Context Builder + Main Agent system policy
```

允许：

```text
raw conversation context
persona state
temporal persona state
available tool descriptions
mechanical resource status
retrieved evidence
validator repair issues
```

禁止：

```text
“这是出处核验题”
“这是 comparison”
“现在必须 VERIFY_NOW”
“你应该按这种哲学结构作答”
“Runtime 判断用户前提错误，因此你必须这样纠正”
```

---

## 1. Audit `reasoning_plan.py` Remaining Production Dependency

当前回执：

```text
REASONING_PLAN_RUNTIME_AUTHORITY = 0
```

但仍保留：

```text
verification_intent
source_constraint
verification state
temporal detection
```

并进入 Main Agent context。

逐个列出：

```text
SYMBOL
CALLER
OUTPUT
WHERE_INJECTED
CONSUMER
WHY_NEEDED
CAN_BE_DERIVED_WITHOUT_PLANNER
```

重点：

```text
detect_verification_intent
source_constraint
VERIFY_NOW
SOURCE_NAV
term extraction
verification state
```

必须判断：

A. validator deterministic input  
B. persona/context state  
C. cognitive interpretation of user request

C 类全部删除。

---

## 2. Remove General Verification-Intent Classification

目标：

```text
GENERAL_VERIFICATION_INTENT_CLASSIFIER = REMOVED
```

Main Agent自己从用户请求理解：

```text
“言必有中出处”
```

不需要 Python 先生成：

```text
verification_intent=SOURCE_ATTRIBUTION
VERIFY_NOW=true
```

Evidence Appetite system policy 已经告诉 Main Agent：

```text
quotes / source attribution / externally verifiable claims
应主动优先核直接证据
```

因此不要用：

```text
regex → intent → special instruction
```

再帮模型理解一次。

禁止替代为：

```text
new_source_attribution_detector.py
```

---

## 3. Validator Must Not Depend on User Intent Classification

审计 `FinalValidator`。

对：

```text
UNSUPPORTED_EXACT_QUOTE
NEAR_QUOTE_NOT_MARKED
STITCHED_QUOTE
UNVERIFIED_CITATION
```

验证应依赖：

```text
final candidate content
+
retrieved evidence
```

而不是：

```text
verification_intent
problem type
user question classification
```

例如：

无论用户有没有问“出处”，

只要 final 写：

```text
“孔子说：‘……’”
```

validator 都应按证据验证。

目标：

```text
FINAL_VALIDATOR_GENERAL_INTENT_DEPENDENCY = 0
```

---

## 4. `VERIFY_LATER_MISSTATEMENT` Re-Audit

O2 留下：

```text
VERIFY_LATER_MISSTATEMENT
```

现在检查它是不是依赖：

```text
verification_intent
VERIFY_NOW
source-attribution regex
```

如果是：

重新判断其存在价值。

Runtime 可以机械判断：

```text
模型声称“我已经读取了 X”
但 evidence store 没有任何 read
```

这是 evidence-consistency validation。

Runtime 不应该判断：

```text
“这道题本来就应该现在查，所以说以后查是不对的”
```

后一类是 semantic policy。

原则：

```text
evidence/action consistency → KEEP
task-intent discipline → DELETE
```

---

## 5. PremiseVerifier Authority Audit

这是本轮第二个 blocker。

当前：

```text
PremiseVerifier 事实校正
→ pre-LLM injection
```

必须回答：

```text
WHO DECIDES THAT THE USER'S PREMISE IS FALSE?
```

逐条分类其规则表：

```text
A. mechanically derived from retrieved/current evidence
B. static product metadata
C. hard-coded philosophical/historical knowledge
D. semantic interpretation
```

允许：

A/B 作为 Context Data。

C/D 不得作为独立 cognitive authority 注入 Main Agent。

尤其禁止：

```text
Runtime:
“用户的哲学前提错了，正确结论是……”
→ inject SystemMessage
```

如果事实可验证：

让 Main Agent：

```text
research
→ evidence
→ decide correction
```

或由 O2 validator 对 final 中机械可验证的 contradiction 处理。

目标：

```text
PRE_LLM_FACTUAL_CORRECTION_AUTHORITY = 0
```

可以保留纯：

```text
metadata lookup
evidence facts
```

但不要叫“Verifier”然后替 Agent 下结论。

---

## 6. EpistemicClaimClassifier Re-Audit

当前保留：

```text
EpistemicClaimClassifier
→ evidence_contract production dependency
```

确认它到底做什么。

如果只是把 final claims 分类为：

```text
quote
citation
source-bound claim
```

用于 deterministic evidence binding：

可保留或迁入 EvidenceContract。

如果它判断：

```text
TEXTUAL_INFERENCE
SCHOLARLY_INTERPRETATION
PERSONA_INFERENCE
claim too strong
claim certainty
```

并影响 runtime 行为：

删除 control / directive effect。

目标：

```text
EPISTEMIC_CLASSIFIER_COGNITIVE_AUTHORITY = 0
```

不要为了删文件而删 evidence provenance taxonomy；
只删 runtime cognitive judgment。

---

## 7. Temporal Persona Is NOT General Reasoning Plan

Nietzsche temporal behavior 必须保留。

但应从：

```text
reasoning_plan
```

概念上分离。

允许一个很小的：

```text
PersonaTemporalContextResolver
```

如果当前架构确实需要 deterministic persona-period selection。

它只能决定：

```text
persona/context snapshot
```

不能决定：

```text
research strategy
tool
answer form
evidence sufficiency
final content
```

如果 temporal parsing 已经可以由 philosopher agent/context layer 持有：

迁过去。

目标：

```text
TEMPORAL_PERSONA_OWNER =
Persona/Context layer
```

不是 Reasoning Planner。

---

## 8. Collapse Runtime Cognitive Injection Sites

当前 AFTER 仍报 7 个 injection points。

建立完整表：

```text
SITE
MODULE
MESSAGE_ROLE
CONTENT_TYPE
COGNITIVE_OR_CONTEXT
KEEP/MOVE/DELETE
```

当前已知：

```text
main system policy
persona reminder
language reminder
hard budget status
verification status
PremiseVerifier injection
plan C injection
```

目标架构：

```text
build_context()
    ↓
one coherent Main Agent context
```

不是连续：

```text
SystemMessage
SystemMessage
SystemMessage
SystemMessage
```

由多个旧模块各插一段。

### Keep as structured context

```text
persona
language preference
mechanical hard-resource state
```

### Delete

```text
VERIFY_NOW
source-navigation strategy
problem classification
answer-shape directive
premise correction conclusion
```

### Repair feedback

仍由 O2 validation event 单独返回，不并入 base policy。

目标：

```text
COGNITIVE_POLICY_INJECTION_SITES_AFTER = 1
SEMANTIC_RUNTIME_DIRECTIVE_SITES = 0
```

这里的 `1` 指核心 Main-Agent Context Builder。

Persona/data fields 可以作为其输入，
不按独立 cognitive policy owner 计数。

---

## 9. Evidence Appetite Remains Single Research Policy

保留：

```text
Use tools proactively when they improve reliability,
depth, or source grounding.

Do not stop merely because you already know a plausible answer.

Prefer direct evidence for quotations, source attribution,
historical and externally verifiable claims.

Continue researching while additional evidence is likely
to materially improve the answer.

Avoid redundant mechanical searching.
```

不要追加：

```text
If source attribution then...
If comparison then...
If deep synthesis then...
```

Main Agent 自己理解任务。

---

## 10. Search-Churn Prompt Improvement — Allowed Narrowly

O4 已确定 churn 原因有：

```text
B = tool result / chapter navigation clarity
D = Main Agent research strategy
```

允许本轮做一个非 gate 的 capability-description 改进：

`search_books` / `get_book_detail` 描述可说明：

```text
对于按格言号、节号、篇章编号组织的作品，
如果搜索结果无法直接定位编号，
可先读取目录/作品详情确认章节结构。
```

这是：

```text
tool capability guidance
```

不是：

```text
runtime mandatory route
```

不要写：

```text
MUST call get_book_detail first
```

---

## 11. Behavior Tests

新增/扩展 O4 tests。

### T1 No Verification Intent Dependency

相同 scripted Main Agent 行为，

输入：

```text
言必有中出处
```

即使没有 `verification_intent` 对象，

模型声明 search/read 后完整执行，
validator 正常。

### T2 Validator Intent-Free

同一 invalid exact quote，

无论 user prompt 是：

```text
“出处是什么”
```

还是：

```text
“聊聊这句话”
```

validator 结果一致。

### T3 No VERIFY_NOW Injection

生产 Main Agent context 不出现 runtime 生成的：

```text
VERIFY_NOW
source attribution task
必须现在核验
```

### T4 PremiseVerifier No Cognitive Correction

构造旧 PremiseVerifier 会触发的输入。

断言：

runtime 不生成一段“正确事实”作为 cognitive directive。

Main Agent 可以自主查工具后纠正。

### T5 Temporal Persona Preserved

Nietzsche late-period query：

```text
temporal persona context present
reasoning-plan general classifier absent
```

### T6 Single Cognitive Policy Owner

生产请求路径：

```text
primary cognitive policy owner count = 1
```

validator repair feedback 单列不计。

### T7 Evidence Validator Intact

quote/citation validation 全部正常。

### T8 O1/O2/O3 invariants

继续为 0：

```text
auto tools
runtime semantic writers
semantic admission
raw reasoning
```

---

## 12. Live UAT

### U1

```text
言必有中出处
```

要求：

```text
无 verification_intent planner
无 VERIFY_NOW
Main Agent 仍自主 search/read
validator PASS
```

### U2

普通哲学解释：

```text
无任何 verification classification
可 zero-tool
```

### U3

伪引文：

```text
Main Agent research / validator repair
无 intent-dependent runtime behavior
```

### U4

Nietzsche temporal：

```text
temporal persona 保持
```

### U5

编号型著作定位：

例如尼采格言号/章节号案例。

观察 tool-description 改善是否降低 churn。

不得用 semantic stop gate。

---

## 13. Full Regression

运行：

```bash
pytest backend/tests -q
```

无排除。

另外：

```text
O1 causal
O1 thinking safety
O2 ownership
O3 authority
O4 collapse
O4-RP1
```

全部 green。

---

## 14. SHA Discipline

这轮以后统一：

```text
BASE_SHA
CODE_SHA
HEAD_SHA
REMOTE_SHA
```

如果 report 回填产生后继 commit：

```text
CODE_SHA != HEAD_SHA
HEAD_SHA == REMOTE_SHA
```

不要再使用模糊 `FINAL_SHA`。

---

## 15. Report

更新：

```text
docs/PHIAGENT_O4_COGNITIVE_LAYER_COLLAPSE.md
```

新增 O4-RP1：

```text
remaining ReasoningPlan audit
PremiseVerifier audit
EpistemicClaimClassifier audit
temporal persona ownership
context injection collapse
intent-free validator tests
live UAT
```

---

## 16. Git

建议：

```text
fix(phiagent): remove residual shadow cognitive directives
```

push 当前 refactor branch。

不得开始 O5。

---

# RECEIPT

```text
O4_RP1 = READY_FOR_REVIEW / BLOCKED

BASE_SHA=
CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

GENERAL_VERIFICATION_INTENT_CLASSIFIER=
REASONING_PLAN_PRODUCTION_DEPENDENCY=

VERIFY_NOW_RUNTIME_INJECTION=
SOURCE_NAV_RUNTIME_INJECTION=

FINAL_VALIDATOR_GENERAL_INTENT_DEPENDENCY=
VERIFY_LATER_MISSTATEMENT_BASIS=

PREMISE_VERIFIER_BEFORE=
PREMISE_VERIFIER_AFTER=
PRE_LLM_FACTUAL_CORRECTION_AUTHORITY=

EPISTEMIC_CLASSIFIER_COGNITIVE_AUTHORITY=

TEMPORAL_PERSONA_OWNER=
TEMPORAL_PERSONA_INTACT=

COGNITIVE_POLICY_INJECTION_SITES_BEFORE=
COGNITIVE_POLICY_INJECTION_SITES_AFTER=
SEMANTIC_RUNTIME_DIRECTIVE_SITES=

EVIDENCE_APPETITE_POLICY=

SEARCH_BOOKS_DESCRIPTION_CHANGE=
SEARCH_CHURN_BEFORE=
SEARCH_CHURN_AFTER=

T1=
T2=
T3=
T4=
T5=
T6=
T7=
T8=

U1=
U2=
U3=
U4=
U5=

ENGINE_COGNITIVE_AUTO_TOOLS=
SEMANTIC_TOOL_CONTROL_EFFECTS=
RUNTIME_SEMANTIC_MUTATORS=
RAW_REASONING_PUBLIC=

O1_CAUSAL_TESTS=
O1_THINKING_SAFETY_TESTS=
O2_OWNERSHIP_TESTS=
O3_TOOL_AUTHORITY_TESTS=
O4_COLLAPSE_TESTS=
O4_RP1_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O4_COGNITIVE_LAYER_COLLAPSE.md

STOP
```

**不得开始 O5。**

这一小轮完成后，O4 才真正能叫“Shadow Cognitive Layer collapsed”——不是只让旧 Planner 失去控制权，而是连“我先替模型理解一下用户到底在问什么，然后给它下认知指令”的最后残余也一起拿掉。