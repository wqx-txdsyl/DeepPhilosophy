这次我不接受继续“教 glm-4-plus 更仔细一点”的方向。RP1 已经给出了足够清楚的诊断：**F6 的原则修复成功了，但 judge 本身仍有系统性盲点和随机翻转。**

远端报告也和回执一致：原 C6 kill case 保持不变、一般 access-level 上限规则已经生效，但最终两轮仍只有 `10/12 = 83.3%` fatal recall，F5 两轮一致漏、F3/F6 跨轮翻转，per-dimension applicability 也只有 `83.8%`。

所以裁定：

```text
O7_A_RP1_REVIEW = PATCH_REQUIRED

O7_A_CORE_CONSTITUTION = ACCEPTED
RP1_ACCESS_LEVEL_PRINCIPLE_FIX = ACCEPTED
RP1_F6_KILL_CASE = ACCEPTED
RP1_APPLICABILITY_METRIC = ACCEPTED

PURE_LLM_JUDGE_RELIABILITY = NOT_ACCEPTED

O7_A_RP2_AUTHORIZED = true
O7_B_AUTHORIZED = false
```

而你提的三个候选里：

```text
(a) k-of-3 ensemble
    = ACCEPTED, but not sufficient alone

(b) deterministic F5 precheck
    = ACCEPTED, with a stricter boundary defined below

(c) switch judge model
    = DEFERRED
```

因为 `k=3` 可以压随机翻转，却治不了“两轮都稳定漏掉 F5”这种**系统错误**；换模型现在又太早，会把“仪器设计问题”和“模型能力问题”混在一起。

这次 RP2 的核心原则是：

> **不要让 LLM 判断本来就可以机械确定的东西。机械事实用机械测量；语义学术判断才交给 LLM。**

---

# TASK — O7-A RP2

## Hybrid Scholarly Judge Final Calibration Closure

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
d1d281902...

PHASE =
O7-A RP2 — HYBRID JUDGE FINAL CALIBRATION CLOSURE

SCOPE =
EVALUATION INSTRUMENT ONLY

STATUS:
O7-A CORE = ACCEPTED
RP1 F6 PRINCIPLE = ACCEPTED
O7-B = NOT AUTHORIZED
```

## 0. RP2 是最后一次“仪器收口”

本轮禁止继续：

```text
- 给 LLM judge 加更多哲学例子
- 围绕 C2/C8/M4 写专门 prompt
- 改 rubric anchors
- 改 scholarly contract
- 改 fatal flag 定义
- 改 production
- 换 judge model
```

除非本任务明确授权，否则：

```text
JUDGE_SEMANTIC_PROMPT_CHANGED = false
```

如果 RP2 后仍达不到 Gate：

```text
DO NOT CREATE RP3 PROMPT PATCH
```

届时结论应是：

```text
CURRENT_JUDGE_MODEL_NOT_RELIABLE_ENOUGH
```

然后 Reviewer 决定更换 judge 模型。

---

# 1. 正式改成 Hybrid Evaluation Instrument

O7 evaluator 不再被定义为：

```text
one LLM decides everything
```

而是：

```text
Mechanical Evidence Checks
        +
Independent LLM Scholarly Judge
        ↓
Deterministic Aggregator
        ↓
Reviewer
```

仍然：

```text
RUNTIME = untouched
```

---

# 2. 新增 evaluation-only QuoteSupportProbe

实现一个纯 evaluation-only 机械探针，例如：

```text
QuoteSupportProbe
```

输入：

```text
ANSWER
PRIMARY_TEXT_EVIDENCE
RETRIEVED_EVIDENCE_DIGEST
EVIDENCE_SCOPE
```

输出每一个 quote-like span：

```json
{
  "span": "...",
  "asserts_exact_wording": true,
  "support_status": "EXACT | NEAR | NONE | UNDETERMINED",
  "matched_evidence_ref": null,
  "evidence_scope": "COMPLETE | PARTIAL"
}
```

它只做**机械文本关系**。

禁止判断：

```text
这个解释是否正确
这个译法是否哲学上等价
作者是不是“真正想表达”这个意思
```

---

# 3. Quote Span Syntax

至少支持通用：

```text
“...”
"..."
blockquote
明确的原文/原话 lead-in 后的被引文本
```

不得把：

```text
《纯粹理性批判》
```

这种作品名括号当 exact quote。

不得包含：

```text
C2
某个 fixture ID
“直觉是对象直接呈现于心灵……”
```

这种专门规则。

---

# 4. Evidence Scope 是关键边界

新增：

```text
EVIDENCE_SCOPE =
COMPLETE_FOR_FIXTURE
PARTIAL_RUNTIME_EVIDENCE
```

校准 fixtures 全部明确指定。

### COMPLETE_FOR_FIXTURE

意味着：

> 当前 supplied evidence 就是这个 fixture 允许使用的完整证据宇宙。

因此若答案明确声称 exact wording，而：

```text
support = NEAR
or
support = NONE
```

则：

```text
F5_FALSE_EXACT_QUOTE = true
```

这是机械事实。

### PARTIAL_RUNTIME_EVIDENCE

如果证据包本来就不是完整宇宙：

```text
NONE
```

只能成为：

```text
UNSUPPORTED_BY_SUPPLIED_EVIDENCE
```

不能机械推导现实世界中该引文一定不存在。

留给 judge / reviewer。

---

# 5. F5 在 COMPLETE fixture 中改为 Mechanical Authority

对 calibration fixture：

```text
evidence_scope = COMPLETE_FOR_FIXTURE
```

F5 最终值由 QuoteSupportProbe 决定。

不是：

```text
LLM majority decides F5
```

而是：

```text
F5_FINAL =
mechanical exact-wording support result
```

理由：

> **字符串是否被当前完整证据支持，不需要一个语言模型猜。**

如果 quote 在证据中 EXACT：

```text
F5=false
```

如果明确 exact claim 但只有 NEAR/NONE：

```text
F5=true
```

误归属给错误学者另归：

```text
F2 / F3
```

不要混进 F5。

---

# 6. 不要复制 production validator

QuoteSupportProbe 是 evaluation instrument。

不得：

```text
import runtime final validator
invoke production repair
invoke quote_bound publication logic
```

可以借鉴已经确定的机械原则，但保持：

```text
EVALUATION_ONLY
PRODUCTION_AUTHORITY=0
```

并静态证明 production 对它零依赖。

---

# 7. LLM Judge 改为 k-of-3 Ensemble

对每一个 fixture：

```text
JUDGE_CALLS_PER_ENSEMBLE = 3
```

同一：

```text
model = glm-4-plus
temperature = 0.0
prompt
schema
fixture
```

三次独立调用。

保存三个完整 raw verdict。

---

# 8. Aggregation Contract

### Numeric dimension

```text
aggregate_score = median(3 scores)
```

### Applicability

```text
aggregate_applicability = majority label
```

若出现：

```text
REQUIRED / OPTIONAL / NOT_APPLICABLE
```

三票各一：

```text
aggregate = AMBIGUOUS
REVIEW_REQUIRED = true
```

不得随机选一个。

### Semantic fatal flags

以下由三次 LLM majority：

```text
F1 FABRICATED_BIBLIOGRAPHY
F2 FABRICATED_SCHOLAR_ATTRIBUTION
F3 PRIMARY_TEXT_MISREPRESENTATION
F4 MAJOR_ANACHRONISM
F6 LITERATURE_ACCESS_OVERCLAIM
```

即：

```text
>=2/3 true → true
```

### F5

按 §5 的机械规则。

---

# 9. Preserve Individual Judge Failure Visibility

Ensemble 不能把单次错误藏掉。

每个 aggregated verdict 仍输出：

```text
vote_distribution
raw_judgments
minority_flags
applicability_disagreement
```

例如：

```text
F3 votes = [true, false, true]
aggregate = true
```

Reviewer 能看到：

```text
1/3 judge miss
```

这对未来 judge 模型评估很重要。

---

# 10. Two Independent Ensembles

最终 Gate 不是只跑 3 次。

必须：

```text
Ensemble A = 3 calls / fixture
Ensemble B = 3 calls / fixture
```

即两个独立的 `k=3` 聚合结果。

冻结 tree 后：

```text
NO CHANGE BETWEEN A AND B
```

稳定性比较的是：

```text
aggregate A
vs
aggregate B
```

不是六个单次输出彼此全等。

---

# 11. F5 Kill Matrix

除了已有 C2-bad，至少建立机械 F5 metamorphic matrix：

```text
Q5-M1
exact quote + exact evidence
→ false

Q5-M2
exact quote + NEAR evidence
→ true

Q5-M3
exact quote + NONE
→ true

Q5-M4
paraphrase normal prose + semantically similar evidence
→ false

Q5-M5
book title in 《》
→ false

Q5-M6
blockquote containing agent's own explanation
+ no evidence
→ true

Q5-M7
PARTIAL evidence + no match
→ mechanical status unsupported/undetermined,
   NOT automatically globally false
```

全部 generic，不围绕 C2 措辞。

---

# 12. Preserve RP1 F6 Matrix

原：

```text
C6-L1-bad
F6-M1...M5
```

全部冻结。

不能因为 RP2 关注 F5 就降低 F6 测试。

---

# 13. Fatal Recall 重新定义最终口径

仍以：

```text
seeded (fixture, flag) assertions
```

为分母。

报告两层：

```text
RAW_SINGLE_CALL_FATAL_RECALL
ENSEMBLE_FINAL_FATAL_RECALL
```

Gate 看：

```text
ENSEMBLE_FINAL_FATAL_RECALL
```

但 raw 数据必须保留。

要求：

```text
F1=100%
F2=100%
F3=100%
F4=100%
F5=100%
F6=100%
```

---

# 14. False Fatal Gate

所有设计为：

```text
NO_FATAL_EXPECTED
```

的 fixtures：

```text
ENSEMBLE_FALSE_FATAL_ASSERTIONS = 0
```

QuoteSupportProbe 也必须在 GOOD / legitimate quote cases：

```text
MECHANICAL_F5_FALSE_POSITIVE = 0
```

---

# 15. Applicability Gate

沿用 RP1 已接受口径：

```text
PER_DIMENSION_APPLICABILITY_EXACT_AGREEMENT
```

现在比较：

```text
Ensemble A aggregate
vs
Ensemble B aggregate
```

要求：

```text
>=90%
```

以及：

```text
REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0
```

另报告：

```text
AMBIGUOUS_APPLICABILITY_COUNT
WHOLE_VECTOR_AGREEMENT
RAW_SINGLE_CALL_PER_DIM_AGREEMENT
```

---

# 16. Score Stability

比较两个 ensemble median：

```text
DIMENSION_ABS_DIFF_LE1_RATE >= 90%
```

另外报告：

```text
EXACT_SCORE_AGREEMENT
```

但不设硬门。

---

# 17. FATAL Stability

最终聚合：

```text
ENSEMBLE_FATAL_FLAG_AGREEMENT = 100%
```

注意：

RP1 的：

```text
90.6%
```

不能再作为可接受。

致命学术错误标志必须稳定。

---

# 18. No Judge Prompt Tuning

优先要求：

```text
SEMANTIC_JUDGE_PROMPT_SHA_BEFORE =
SEMANTIC_JUDGE_PROMPT_SHA_AFTER
```

QuoteSupportProbe 属新 mechanical component，不算 semantic prompt 修改。

如果为了把 probe 输出接入结果 schema 必须改 harness serialization：

允许。

但不要新增：

```text
“当你看到某某句式时……”
```

---

# 19. Reviewer Manifest

新 manifest 还必须加入：

```text
ANY_1_OF_3_FATAL_DISSENT
ANY_APPLICABILITY_1_1_1
ANY_SCORE_SPREAD_GT1
MECHANICAL_LLM_CONFLICT
```

例如：

```text
mechanical F5=true
LLM votes F5=false,false,false
```

最终 F5 仍按 mechanical，但必须：

```text
REVIEW_REQUIRED=true
```

这能暴露 judge 的系统盲点。

---

# 20. Calibration Gate

最终冻结：

```text
HYBRID_CALIBRATION_GATE_SHA=
```

然后才执行：

```text
Ensemble A
Ensemble B
```

中途任何：

```text
fixture
probe
aggregator
prompt
schema
expected label
```

修改：

```text
INVALIDATE
REFREEZE
RERUN BOTH
```

---

# 21. RP2 Hard Gates

全部必须满足：

```text
GOOD > MID > BAD

ENSEMBLE_EXPECTED_FATAL_RECALL = 100%

F1_RECALL = 100%
F2_RECALL = 100%
F3_RECALL = 100%
F4_RECALL = 100%
F5_RECALL = 100%
F6_RECALL = 100%

ENSEMBLE_FALSE_FATAL_ASSERTIONS = 0

MECHANICAL_F5_FALSE_POSITIVE = 0

ENSEMBLE_FATAL_FLAG_AGREEMENT = 100%

DIMENSION_DIFF_LE1_RATE >= 90%

PER_DIMENSION_APPLICABILITY_AGREEMENT >= 90%

REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0

PRODUCTION_DIFF = 0

FULL_TEST_FAILED = 0
```

---

# 22. Hard Stop after RP2

如果失败原因是：

```text
F2/F3/F4/F6 semantic flag
仍然在两个 k=3 ensemble 间无法稳定
```

或者：

```text
applicability ensemble 仍 <90%
```

则不要再 patch glm prompt。

回执：

```text
O7_A_RP2 =
BLOCKED_JUDGE_MODEL
```

Reviewer 下一步将授权：

```text
JUDGE_MODEL_REPLACEMENT_EVALUATION
```

而不是 RP3。

---

# 23. Production Boundary

继续要求：

```text
PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false

NO_PRODUCTION_IMPORTS=true
```

---

# 24. Tests

至少新增/扩展：

```text
T1 quote probe exact
T2 quote probe near
T3 quote probe none
T4 normal paraphrase not exact quote
T5 book title not quote
T6 blockquote unsupported
T7 partial evidence not globally false

T8 mechanical F5 authority on COMPLETE
T9 mechanical F5 non-authority on PARTIAL

T10 median score aggregation
T11 majority applicability aggregation
T12 1/1/1 applicability -> ambiguous
T13 majority semantic fatal aggregation
T14 raw judgments preserved
T15 minority dissent preserved

T16 two-ensemble comparison
T17 fatal assertion denominator
T18 false-fatal negative pool
T19 reviewer manifest conflict
T20 no semantic prompt tuning
T21 no production imports/diff
```

---

# 25. Full Regression

```bash
pytest backend/tests -q
```

必须：

```text
FAILED=0
SKIPPED=0
```

---

# 26. Documentation

继续更新：

```text
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md
```

保留：

```text
Original O7-A BLOCKED
RP1 BLOCKED
```

不得重写历史。

新增：

```text
O7-A RP2 — Hybrid Judge Calibration
```

必须说明：

> **Mechanical authority and semantic judgment are intentionally separated.**

以及：

> **Ensembling reduces variance; it does not repair systematic semantic blindness.**

---

# 27. Git

```text
BASE_SHA=
RP2_CODE_SHA=
HYBRID_CALIBRATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=
```

建议 commit：

```text
test(phiagent): harden O7 scholarly judge with hybrid calibration
```

报告 docs-only successor。

---

# FINAL RECEIPT

```text
O7_A_RP2 =
READY_FOR_FINAL_REVIEW /
BLOCKED /
BLOCKED_JUDGE_MODEL

BASE_SHA=

RP2_CODE_SHA=
HYBRID_CALIBRATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

SEMANTIC_JUDGE_PROMPT_CHANGED=
SEMANTIC_JUDGE_PROMPT_SHA_BEFORE=
SEMANTIC_JUDGE_PROMPT_SHA_AFTER=

QUOTE_SUPPORT_PROBE=
QUOTE_PROBE_EVALUATION_ONLY=

EVIDENCE_SCOPE_COMPLETE_SUPPORTED=
EVIDENCE_SCOPE_PARTIAL_SUPPORTED=

F5_MECHANICAL_AUTHORITY_COMPLETE=
F5_PARTIAL_NOT_AUTOMATIC_FATAL=

F5_METAMORPHIC_FIXTURES=
MECHANICAL_F5_FALSE_POSITIVE=

JUDGE_MODEL=
JUDGE_CALLS_PER_ENSEMBLE=3
ENSEMBLES=2

AGGREGATE_SCORE_METHOD=median
AGGREGATE_APPLICABILITY_METHOD=majority
AGGREGATE_SEMANTIC_FATAL_METHOD=majority

AMBIGUOUS_APPLICABILITY_COUNT=

EXPECTED_FATAL_ASSERTIONS=
ENSEMBLE_FATAL_DETECTED=
ENSEMBLE_EXPECTED_FATAL_RECALL=

F1_RECALL=
F2_RECALL=
F3_RECALL=
F4_RECALL=
F5_RECALL=
F6_RECALL=

RAW_SINGLE_CALL_FATAL_RECALL=

NO_FATAL_EXPECTED_ASSERTIONS=
ENSEMBLE_FALSE_FATAL_ASSERTIONS=

GOOD_MEAN=
MID_MEAN=
BAD_MEAN=

ENSEMBLE_FATAL_FLAG_AGREEMENT=
DIMENSION_DIFF_LE1_RATE=

RAW_SINGLE_CALL_PER_DIM_APPLICABILITY_AGREEMENT=
FINAL_PER_DIM_APPLICABILITY_AGREEMENT=
FINAL_REQUIRED_NA_CRITICAL_CONTRADICTIONS=
FINAL_WHOLE_VECTOR_AGREEMENT=

MECHANICAL_LLM_CONFLICT_CASES=
REVIEW_REQUIRED_CASES=

PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false
NO_PRODUCTION_IMPORTS=true

O7A_RP2_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md

O7_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS /
PATCH_REQUIRED /
JUDGE_MODEL_REPLACEMENT_REQUIRED

STOP
```

这轮要把一个很重要的原则正式固化下来：

> **“这句话是否真的逐字存在于给定证据中”不是哲学判断，而是字符串/证据关系判断。让 LLM 来猜它，反而是不科学的。**

而 `F3 作者到底有没有被实质误述`、`F4 是否构成重大时代错置`、`F6 是否越过摘要/全文访问边界`这类真正需要语义理解的东西，才由 LLM judge + ensemble 承担。

如果这样仍然压不住 `glm-4-plus` 的语义波动，我们就不再调它，直接换测量仪器。

