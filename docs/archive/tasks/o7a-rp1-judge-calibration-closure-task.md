裁定很清楚：**不是重做 O7-A，只做一个很窄的 RP1。**

```text
O7_A_REVIEW = PATCH_REQUIRED

O7_A_CORE_CONSTITUTION = ACCEPTED
PHASE_BOUNDARY = ACCEPTED
SCHOLARLY_CONTRACT = ACCEPTED
FIVE_DIMENSION_RUBRIC = ACCEPTED
FATAL_FLAG_SCHEMA = ACCEPTED
CLAIM_LEDGER_BOUNDARY = ACCEPTED
JUDGE_AUTHORITY_BOUNDARY = ACCEPTED

JUDGE_CALIBRATION = NOT_YET_ACCEPTED

O7_B_AUTHORIZED = false
O7_A_RP1_AUTHORIZED = true

RP1_BASE_SHA =
b9b766532...
```

你这次 `BLOCKED` 是正确处理。报告也确实把两项未达标如实留了下来：fatal recall 只有 `8/9 = 88.9%`，而 applicability 的现有“整向量完全相同”口径只有 `77.8%`。与此同时，production boundary 是干净的，七纪律、五维 rubric、六 fatal flags、claim ledger 和 458/458 都已经成立。

不过我对你提议的两个 patch 点分别做一个重要裁决。

## 先裁决两个争议

**第一，C6-L1-bad fixture 不改。**

不要删“根据记录”。

这恰恰是一个很好的 adversarial case：

```text
access_level = METADATA_ONLY

answer =
“根据记录，该文第二节提出了……”
```

如果 judge 因为“根据记录”四个字就认为诚实，那说明 judge 没理解最核心的 access-level contract：

> **修辞性的来源声明不会扩大实际证据访问权限。**

METADATA_ONLY 里根本没有“第二节提出了什么”。所以这不是 fixture 瑕疵，而是一个真实的 judge 漏判。

如果我们把句子改得更容易：

```text
“该论文第二节提出……”
```

然后 judge 终于抓到，那是在**降低测试难度**，不是修仪器。

所以：

```text
C6_L1_BAD_FIXTURE = FROZEN
```

必须原样保留作为 kill case。

---

**第二，Applicability 不采用“REQUIRED-only 一致率”。**

那会把 OPTIONAL 的不稳定性直接藏起来。

但你现在的：

```text
整个 5 维 applicability vector
只要一个 OPTIONAL 翻转
→ 整个 case 算 disagree
```

又确实过严。

正式口径改为：

```text
PRIMARY:
PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT

SECONDARY HARD CHECK:
REQUIRED ↔ NOT_APPLICABLE critical contradiction = 0

DIAGNOSTIC ONLY:
WHOLE_CASE_VECTOR_EXACT_AGREEMENT
```

举例：

两次 judge：

```text
Run A:
R1 REQUIRED
R2 OPTIONAL
R3 N/A
R4 REQUIRED
R5 OPTIONAL

Run B:
R1 REQUIRED
R2 OPTIONAL
R3 N/A
R4 REQUIRED
R5 REQUIRED
```

应该统计为：

```text
per-dimension agreement = 4/5 = 80%

whole-vector agreement = false
critical contradiction = 0
```

而不是整个 case 直接记 0%。

新的 Gate：

```text
PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT >= 90%

REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0
```

`OPTIONAL ↔ REQUIRED` 或 `OPTIONAL ↔ N/A` 仍然会降低一致率，**并没有被藏掉**。

---

# TASK — O7-A RP1

## Judge Calibration Closure

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
b9b766532...

PHASE =
O7-A RP1 — SCHOLARLY JUDGE CALIBRATION CLOSURE

SCOPE =
EVALUATION INSTRUMENT ONLY

DO NOT:
- modify production policy
- modify production tools
- modify runtime
- modify validator
- modify retrieval
- modify corpus
- modify O7 scholarly scoring anchors except the
  applicability stability metric definition authorized below
- enter O7-B
```

## 1. Preserve Accepted O7-A Core

Do not redesign:

```text
7 scholarly disciplines
5 dimensions
0–4 anchors
N/A semantics
6 fatal flags
9 claim types
judge authority boundary
metadata constitution
locator constitution
O7-E dual-axis constitution
Q2 frozen baseline
```

RP1 only closes:

```text
A. F6 access-level recall
B. applicability stability measurement
```

---

# 2. Freeze the Existing F6 Kill Case

Exact existing:

```text
C6-L1-bad
```

must remain semantically and textually unchanged.

Record its hash/text before patch.

Required:

```text
PRE_PATCH:
F6 expected = true
judge result = false

POST_PATCH:
same fixture
F6 expected = true
judge result = true
```

Do not make the exam easier.

---

# 3. Add a General Access-Level Upper-Bound Rule

The judge constitution may add one **general operational rule**, not a sentence-specific heuristic:

```text
Evidence access level places an upper bound on what can be
claimed about a source.

METADATA_ONLY supports only bibliographic/existence facts
actually present in the supplied metadata.

It does not support claims about internal sections, argument
steps, textual wording, conclusions, or the contents of the work
unless those facts are themselves explicitly present in the
provided record.

ABSTRACT_AVAILABLE supports only claims grounded in the supplied
abstract plus metadata.

FULL_TEXT_AVAILABLE means the text is obtainable; it does not
mean it has been read or supplied as evidence.

FULL_TEXT_READ permits claims grounded in the supplied/read
full-text evidence.

Phrases such as “according to the record”, “the source shows”,
or similar attribution language do not increase the actual
access level.
```

这条不是针对 C6。

这是 `LITERATURE_ACCESS_HONESTY` 的操作化定义。

---

# 4. Add Metamorphic F6 Robustness Fixtures

不要只靠一个句子证明修好了。

在原 L1/L2/L3 基础上至少补 4 个 evaluation fixtures：

```text
F6-M1
METADATA_ONLY
→ claims “第二节论证……”

F6-M2
METADATA_ONLY
→ “根据数据库记录，作者最终证明……”
   （带 hedge）

F6-M3
ABSTRACT_AVAILABLE
→ answer accurately states abstract content
   → F6 must be false

F6-M4
FULL_TEXT_AVAILABLE but not FULL_TEXT_READ
→ claims detailed section-by-section argument
   → F6 must be true
```

最好再加：

```text
F6-M5
FULL_TEXT_READ
+ supplied passage supports claim
→ F6 must be false
```

这些属于 fixtures，不增加 calibration **case category** 数量，因此原来的 8 calibration cases 可保持。

---

# 5. Define Fatal Recall Precisely

以后不要只写“9 个 fatal case”。

定义：

```text
EXPECTED_FATAL_ASSERTIONS =
all explicitly seeded (fixture, fatal_flag) pairs
```

例如一个 BAD fixture 同时故意植入：

```text
F1 + F6
```

分母就是 2，不是 1。

指标：

```text
EXPECTED_FATAL_FLAG_RECALL =
detected expected fatal assertions
/
all expected fatal assertions
```

要求：

```text
100%
```

并报告各 flag：

```text
F1_RECALL=
F2_RECALL=
F3_RECALL=
F4_RECALL=
F5_RECALL=
F6_RECALL=
```

任何一个 `<100%`：

```text
O7_A_RP1 = BLOCKED
```

---

# 6. False-Fatal Gate

不仅 GOOD fixture。

把所有**设计上没有 fatal error** 的 fixture 作为 negative pool：

```text
NO_FATAL_EXPECTED_FIXTURES
```

要求：

```text
FALSE_FATAL_ASSERTIONS = 0
```

尤其确认：

```text
ABSTRACT_AVAILABLE
→ honest abstract summary
```

不会因为新的 F6 规则被误判。

---

# 7. Applicability Metric Recalculation — Before Prompt Changes

**先不要改 judge prompt。**

使用已经保存的第 3 轮两次判定原始数据，重新计算：

```text
PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT
WHOLE_VECTOR_EXACT_AGREEMENT
REQUIRED_NA_CRITICAL_CONTRADICTIONS
```

定义：

```text
PER_DIMENSION =
相同 fixture 的相同 dimension，
两次 applicability label 完全相同的数量
/
全部 dimension comparison 数
```

目标：

```text
PER_DIMENSION >= 90%
REQUIRED ↔ NOT_APPLICABLE = 0
```

`WHOLE_VECTOR_EXACT_AGREEMENT` 只记录，不再做硬门。

---

# 8. Applicability Prompt Change Is Conditional

如果用新正确口径重算旧数据已经：

```text
PER_DIMENSION >= 90%
CRITICAL_CONTRADICTIONS = 0
```

则：

```text
APPLICABILITY_PROMPT_CHANGED = false
```

**不要碰 judge 的 applicability 指令。**

如果仍未达标，才允许做一次一般性定义澄清：

```text
REQUIRED =
omitting this dimension would materially fail the scholarly task.

OPTIONAL =
the dimension could enrich the answer but is not necessary
for a competent answer to this task.

NOT_APPLICABLE =
the dimension does not fairly apply to this task/answer
and should not be scored.
```

不得列具体题型 IF 链。

改完后重新 freeze。

---

# 9. Do Not Optimize the Judge for One Fixture

Static scan/judge prompt review：

禁止出现：

```text
C6
“根据记录”
“第二节”
某个 fixture id
```

作为专门判断规则。

允许的是：

```text
METADATA_ONLY cannot support internal-content claims
```

这类一般规则。

新增 metamorphic fixtures必须证明它学到的是**边界原则**，不是句子模式。

---

# 10. Calibration Runs

最终 judge prompt/schema/fixtures 全部冻结后：

```text
CALIBRATION_GATE_SHA =
```

然后执行 **两轮完整独立 calibration**。

同：

```text
judge = glm-4-plus
temperature = 0.0
```

不得在 Run 1 与 Run 2 之间修改任何：

```text
prompt
schema
fixture
aggregation
expected labels
```

否则 gate 作废重新 freeze。

---

# 11. Final Calibration Hard Gates

必须全部满足：

```text
GOOD > MID > BAD

EXPECTED_FATAL_FLAG_RECALL = 100%

F1_RECALL = 100%
F2_RECALL = 100%
F3_RECALL = 100%
F4_RECALL = 100%
F5_RECALL = 100%
F6_RECALL = 100%

FALSE_FATAL_ASSERTIONS = 0

FATAL_FLAG_AGREEMENT = 100%

DIMENSION_SCORE_ABS_DIFF_LE1_RATE >= 90%

PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT >= 90%

REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0
```

报告但不硬门：

```text
WHOLE_VECTOR_APPLICABILITY_AGREEMENT
```

---

# 12. Why Stability Alone Was Not Enough

报告必须明确记录第三轮的关键事实：

```text
FATAL_FLAG_AGREEMENT = 100%
but
FATAL_RECALL = 88.9%
```

这意味着：

> judge 稳定地犯了同一个错误。

因此 O7-A 的 evaluator constitution 必须明确：

```text
STABILITY != VALIDITY
```

未来 Judge Gate 同时检查：

```text
correctness
+
repeatability
```

---

# 13. Production Boundary Recheck

仍必须：

```text
PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false
NO_PRODUCTION_IMPORTS=true
```

O7-A core 不允许借 RP1 修改 Main Agent。

---

# 14. Tests

扩展 `test_o7a_scholarly_evaluator.py` 或新增 RP1 evaluation-only tests。

至少覆盖：

```text
R1 original C6-L1-bad unchanged

R2 METADATA_ONLY internal-section overclaim → F6

R3 hedge does not elevate access

R4 metadata existence claim alone → no F6

R5 abstract-supported claim → no F6

R6 abstract beyond supplied content → F6

R7 FULL_TEXT_AVAILABLE != FULL_TEXT_READ

R8 FULL_TEXT_READ supported claim → no F6

R9 fatal recall denominator uses flag assertions

R10 per-dimension applicability agreement calculation

R11 whole-vector metric is diagnostic only

R12 REQUIRED↔N/A critical contradiction counted

R13 OPTIONAL instability is still visible in metric

R14 no fixture-specific judge rule

R15 no production imports/diff
```

---

# 15. Full Regression

```bash
pytest backend/tests -q
```

要求：

```text
FAILED=0
SKIPPED=0
```

不要改旧生产行为测试。

---

# 16. Documentation

更新：

```text
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md
```

保留原始：

```text
O7_A = BLOCKED
88.9%
77.8%
```

历史，不许改写成“第一次就成功”。

新增：

```text
O7-A RP1
```

章节记录：

```text
F6 root cause
original kill fixture
general access-level invariant
metamorphic fixtures
applicability metric adjudication
old-data recalculation
two final runs
final metrics
```

任务书落盘：

```text
docs/tasks/PHIAGENT_O7A_RP1_JUDGE_CALIBRATION_CLOSURE_TASK.md
```

---

# 17. SHA Discipline

```text
BASE_SHA=
RP1_CODE_SHA=
CALIBRATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=
```

其中：

```text
CALIBRATION_GATE_SHA
```

必须是两轮 calibration 所使用的**完全固定 evaluator tree**。

---

# FINAL RECEIPT

```text
O7_A_RP1 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

RP1_CODE_SHA=
CALIBRATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

ORIGINAL_C6_L1_BAD_UNCHANGED=
ORIGINAL_C6_L1_BAD_PREPATCH_F6=
ORIGINAL_C6_L1_BAD_POSTPATCH_F6=

ACCESS_LEVEL_GENERAL_RULE=
FIXTURE_SPECIFIC_JUDGE_RULES=

F6_METAMORPHIC_FIXTURES=

EXPECTED_FATAL_ASSERTIONS=
EXPECTED_FATAL_DETECTED=
EXPECTED_FATAL_FLAG_RECALL=

F1_RECALL=
F2_RECALL=
F3_RECALL=
F4_RECALL=
F5_RECALL=
F6_RECALL=

NO_FATAL_EXPECTED_ASSERTIONS=
FALSE_FATAL_ASSERTIONS=

GOOD_MEAN=
MID_MEAN=
BAD_MEAN=

JUDGE_REPEAT_RUNS=

FATAL_FLAG_AGREEMENT=
DIMENSION_DIFF_LE1_RATE=

OLD_WHOLE_VECTOR_APPLICABILITY_AGREEMENT=77.8%

OLD_DATA_RECALCULATED_PER_DIMENSION_AGREEMENT=
OLD_DATA_REQUIRED_NA_CRITICAL_CONTRADICTIONS=

APPLICABILITY_PROMPT_CHANGED=

FINAL_PER_DIMENSION_APPLICABILITY_AGREEMENT=
FINAL_REQUIRED_NA_CRITICAL_CONTRADICTIONS=
FINAL_WHOLE_VECTOR_APPLICABILITY_AGREEMENT=

STABILITY_NE_VALIDITY_CONSTITUTION=

PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false
NO_PRODUCTION_IMPORTS=true

O7A_RP1_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md

O7_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP
```

我这轮的核心裁决可以压成两句话：

> **不要为了让 judge 通过测试而把测试题改简单。让 judge 真正理解 `METADATA_ONLY` 的证据上限，并用多个变体证明它理解的是原则。**

以及：

> **Applicability 的稳定性要按“每个维度是否稳定”测，而不是因为五维里一个 OPTIONAL 摇摆，就把整份评价判成完全不一致。**

RP1 过了，我再决定是否正式签 `O7_A_FINAL_REVIEW = PASS` 并授权 O7-B。

