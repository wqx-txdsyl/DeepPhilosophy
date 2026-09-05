裁定：**授权 `JUDGE_MODEL_REPLACEMENT_EVALUATION`，不再碰 glm-4-plus prompt。**

这次 RP2 的证据已经足够强。远端报告与回执一致：Hybrid 架构本身工作正常，F5 机械层两轮全中且零误报；真正失败的是语义 judge——F1 两个 ensemble 都只有 0.5、F3 在 `1.0 ↔ 0.0` 间翻转、F6 两轮只有 0.8，最终 fatal agreement 96.9%，而 applicability 和 dimension stability 已经过线。

所以：

```text
O7_A_RP2_REVIEW = PASS_AS_DIAGNOSIS
O7_A_FINAL_REVIEW = BLOCKED_BY_JUDGE_MODEL

HYBRID_JUDGE_ARCHITECTURE = ACCEPTED
MECHANICAL_F5_AUTHORITY = ACCEPTED
K3_AGGREGATION = ACCEPTED
APPLICABILITY_METRIC = ACCEPTED

GLM_4_PLUS_AS_SCHOLARLY_JUDGE = REJECTED

JUDGE_MODEL_REPLACEMENT_EVALUATION_AUTHORIZED = true
O7_B_AUTHORIZED = false
```

注意这里的 `PASS_AS_DIAGNOSIS` 不是 O7-A PASS；它表示 RP2 已经完成了自己的任务——证明问题确实在 judge 模型，而不是继续猜。

# TASK — O7-A JR1

## Scholarly Judge Model Replacement Evaluation

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
6cfe1181c...

PHASE =
O7-A JR1 — JUDGE MODEL REPLACEMENT EVALUATION

PHASE_TYPE =
EVALUATION-INSTRUMENT MODEL BAKEOFF ONLY
```

## 0. 目标

这轮**不修任何 evaluator 逻辑**。

只回答：

> 在已经冻结的 Hybrid Scholarly Judge 架构下，哪个独立模型有资格成为 O7 的正式 semantic judge？

冻结：

```text
QuoteSupportProbe
fatal definitions
rubric
fixtures
expected labels
aggregation
k=3
two-ensemble protocol
access-level rules
claim ledger
review manifest
```

禁止：

```text
- 修改 glm-4-plus prompt 来救它
- 为新模型写专属 prompt
- 修改 fixture
- 修改 expected labels
- 修改 fatal definitions
- 修改 rubric anchors
- 修改 mechanical F5 probe
- 修改 ensemble aggregation
- 修改 production
- 进入 O7-B
```

---

## 1. Preserve Exact Evaluation Constitution

从：

```text
HYBRID_CALIBRATION_GATE_SHA =
3f0049577...
```

提取并冻结所有 model-independent evaluator assets。

生成：

```text
EVALUATOR_CONSTITUTION_HASH
FIXTURE_SET_HASH
EXPECTED_LABELS_HASH
QUOTE_PROBE_HASH
SEMANTIC_JUDGE_PROMPT_HASH
AGGREGATOR_HASH
```

每个候选 judge 必须吃**完全一样**的：

```text
system prompt
user payload
schema
fixtures
evidence
temperature policy
aggregation
```

除了 provider/model invocation adapter，不允许模型特化。

---

# 2. Candidate Eligibility

候选必须满足：

```text
CANDIDATE_MODEL != deepseek-chat
```

因为 DeepSeek 是被评 Main Agent。

同时要求：

```text
structured JSON output usable
temperature=0 or lowest supported deterministic setting
same prompt can be supplied verbatim
no hidden web/retrieval/tool use
no prior fixture answer injection
```

不能用 Main Agent 自评。

---

# 3. 不预设“最强模型一定赢”

本轮做 **bakeoff**，而不是先认定某个模型。

优先测试 **2–3 个当前实际上可调用的强模型**。

候选选择顺序：

```text
Tier A:
现有环境中可通过 API / local inference
稳定批量调用的强模型

Tier B:
同样可稳定批量调用、但能力/成本略低的备选

Rejected:
只能人工聊天调用、
没有稳定批量接口、
或无法固定配置的模型
```

不得为了凑候选数临时购买/接入不稳定 provider。

---

# 4. 建议候选策略

如果当前环境可用，优先考虑：

```text
Candidate 1:
GLM-5.3-Flash
但前提是 evaluator 能通过稳定 API/endpoint 批量调用，
而不是只能在 ZCode harness 里交互使用。

Candidate 2:
一个强 Qwen 本地模型
前提是本地服务可以固定版本、固定采样参数、严格 JSON。

Candidate 3:
其他已经配置好的非 DeepSeek 强 judge
```

**不要把“我日常 coding 用它很强”当作 judge 资格。**

这里测的是：

```text
semantic fatal classification
rubric consistency
applicability stability
structured evidence following
```

和 coding 能力不是一回事。

如果实际只有一个合格候选可调用：

```text
CANDIDATE_COUNT=1
```

也允许执行；不要假装有多个。

---

# 5. glm-4-plus 作为 Control，不再竞争

保留 RP2 数据：

```text
glm-4-plus
```

作为：

```text
CONTROL_REJECTED_MODEL
```

不用重新跑。

其冻结基线：

```text
fatal recall A/B = 83.3% / 75%
fatal agreement = 96.9%
per-dim applicability = 90.6%
dimension diff<=1 = 100%
false fatal = 0
```

新候选必须明显优于这个 control 的致命错误表现。

---

# 6. Stage 1 — Cheap Screening

不要一开始每个候选就跑完整 `2 × k3 × 32`。

先跑固定 screening subset。

必须包含最难的历史 kill cases：

```text
S-F1:
C1-bad — fabricated bibliography

S-F2:
C3-bad — scholar attribution

S-F3:
C8-bad — primary-text misrepresentation

S-F4:
existing major anachronism fixture

S-F6:
C6-L1-bad
F6-M2
F6-M4
```

F5 不用作为 semantic model 主筛，因为它已经 mechanical-authoritative；但保留一个 mechanical/LLM conflict case用于观察。

另加：

```text
2 GOOD negative fixtures
2 MID/neutral fixtures
2 applicability-sensitive fixtures
```

总 screening 建议：

```text
12–16 fixtures
```

---

# 7. Screening Protocol

每 candidate：

```text
k=3
```

一次 ensemble 即可用于第一阶段。

筛除条件，任一满足即淘汰：

```text
seeded semantic fatal recall < 100%

false fatal > 0

JSON/schema failure > 0 after normal transport retry

fatal majority misses any F1/F2/F3/F4/F6 kill case
```

同时记录：

```text
raw single-call recall
vote distributions
latency
provider failures
token usage if available
```

只有通过 screening 的 candidate 进入 Full Gate。

---

# 8. 不允许 Candidate-Specific Prompt Tuning

如果某候选：

```text
C8-bad F3 miss
```

不得给它加：

> “特别注意作者原典误述……”

因为别的 judge 没有这条专属补丁。

允许的只有：

```text
transport adapter
JSON extraction adapter
provider-specific API formatting
```

语义输入必须等价。

---

# 9. Stage 2 — Full Qualification

每个 screening PASS candidate 运行完整：

```text
all frozen scholarly fixtures
+
all F6 metamorphic fixtures
+
all Q5 mechanical fixtures
```

semantic judge 部分保持原集合。

每 candidate：

```text
Ensemble A = k3
Ensemble B = k3
```

冻结候选 model/version/config 后，两 ensemble 间零修改。

---

# 10. Candidate Hard Qualification Gates

一个 judge 要成为正式 O7 judge，必须单独达到：

```text
GOOD > MID > BAD

ENSEMBLE_EXPECTED_FATAL_RECALL = 100%
in A AND B

F1_RECALL = 100%
F2_RECALL = 100%
F3_RECALL = 100%
F4_RECALL = 100%
F6_RECALL = 100%

F5 mechanical = 100%

ENSEMBLE_FALSE_FATAL_ASSERTIONS = 0
in A AND B

ENSEMBLE_FATAL_FLAG_AGREEMENT = 100%

DIMENSION_DIFF_LE1_RATE >= 90%

PER_DIMENSION_APPLICABILITY_AGREEMENT >= 90%

REQUIRED_NA_CRITICAL_CONTRADICTIONS = 0

schema failures = 0

production diff = 0
```

**不得用候选之间平均成绩弥补。**

模型要么 qualified，要么不 qualified。

---

# 11. 增加一个 Anti-Luck Gate

由于之前出现过：

```text
四轮都能命中
第五轮突然双漏
```

这次不能仅靠两个 ensemble 就宣布 judge 永远稳定。

对 Full Gate PASS 的候选，追加一个小型 adversarial confirmation：

只用：

```text
F1/F2/F3/F4/F6 kill cases
+
2 clean negatives
```

再跑：

```text
one additional k3 ensemble
```

不改任何配置。

要求：

```text
fatal recall = 100%
false fatal = 0
```

否则：

```text
CANDIDATE = UNSTABLE
```

这不是第三套完整 gate，成本可控。

---

# 12. 版本必须钉死

不能只记录：

```text
qwen
glm
```

必须尽可能记录：

```text
provider
model_id
model_version/revision if exposed
endpoint
temperature
top_p
seed if supported
max_tokens
structured-output mode
```

本地模型还记录：

```text
weights/version/hash
serving backend
quantization
```

否则以后无法复现 judge。

---

# 13. Judge Selection Rule

如果只有一个 QUALIFIED：

```text
SELECTED_JUDGE = that model
```

如果多个 QUALIFIED：

优先级：

```text
1. fatal correctness/stability
2. applicability stability
3. dimension stability
4. lower false-positive risk
5. reproducibility/version pinning
6. latency
7. cost
```

**成本不能压过正确性。**

例如：

```text
Model A:
100% fatal, 100% agreement, slower

Model B:
98% fatal, much cheaper
```

必须选 A。

---

# 14. Reviewer 保留最终选型权

Agent 只能输出：

```text
RECOMMENDED_JUDGE_MODEL
```

不能自行写：

```text
OFFICIAL_O7_JUDGE = ...
```

正式锁定由我签：

```text
O7_OFFICIAL_JUDGE_MODEL = ...
```

---

# 15. 不要把 Mechanical Layer 撤掉

哪怕新 judge 对 F5 自己也能做到 100%，仍然保持：

```text
F5 = mechanical authority on COMPLETE evidence
```

因为这是架构上更正确的职责分工。

Judge replacement 不是回到：

```text
one giant LLM judge
```

---

# 16. Judge Disagreement 继续暴露

新 judge 依旧保存：

```text
raw_judgments
vote_distribution
minority_flags
mechanical_llm_conflict
applicability disagreement
```

不能因为换了强模型就只保存 aggregate。

---

# 17. 成本与时延

每个候选报告：

```text
SCREEN_CALLS
FULL_CALLS
TOTAL_CALLS

P50_LATENCY
P95_LATENCY

INPUT_TOKENS
OUTPUT_TOKENS
COST
```

无法拿到 token/cost：

写：

```text
NOT_AVAILABLE
```

不要估。

---

# 18. Qualification Result Matrix

报告至少给：

| Metric          | glm-4-plus control | Candidate A | Candidate B | Candidate C |
| --------------- | -----------------: | ----------: | ----------: | ----------: |
| Screening pass  |           rejected |             |             |             |
| Fatal recall A  |              83.3% |             |             |             |
| Fatal recall B  |                75% |             |             |             |
| Fatal agreement |              96.9% |             |             |             |
| False fatal     |                  0 |             |             |             |
| Applicability   |              90.6% |             |             |             |
| Dimension ≤1    |               100% |             |             |             |
| Confirmation    |                  — |             |             |             |
| Qualified       |                 NO |             |             |             |

不要只给“综合分”。

---

# 19. 如果没有任何模型通过

如果：

```text
QUALIFIED_JUDGE_COUNT = 0
```

立即：

```text
O7_A_JR1 = BLOCKED_NO_QUALIFIED_JUDGE
```

不要继续调 prompt。

返回各候选 failure signature。

Reviewer 再决定：

```text
- 引入新的 judge provider
- 双模型 adjudication
- 人工 Reviewer 比例提高
- 修改 O7-E measurement design
```

但这些都不是本轮自行决定。

---

# 20. 如果至少一个模型通过

回执：

```text
O7_A_JR1 = READY_FOR_FINAL_REVIEW
```

但：

```text
O7_B_AUTHORIZED = false
```

我会先做：

```text
Judge Replacement Review
→ O7-A Final Constitution Review
```

只有我签：

```text
O7_A_FINAL_REVIEW = PASS
```

才授权 O7-B。

---

# 21. Production Boundary

必须继续保持：

```text
PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false
NO_PRODUCTION_IMPORTS=true
```

这次只允许 evaluation adapter / config / result / docs 变动。

---

# 22. Tests

新增至少：

```text
T1 candidate config isolated from semantic prompt
T2 tested model cannot equal judge
T3 control baseline frozen
T4 screening subset fixed

T5 screening fatal miss rejects candidate
T6 screening false fatal rejects candidate

T7 qualified candidate requires A and B full pass
T8 fatal recall per flag
T9 confirmation ensemble required

T10 candidate-specific prompt forbidden
T11 model/version metadata persisted
T12 raw judgments retained

T13 selection prioritizes correctness over cost
T14 zero-qualified returns BLOCKED
T15 agent cannot self-authorize official judge

T16 hybrid F5 authority retained
T17 production diff zero
```

---

# 23. Full Regression

```bash
pytest backend/tests -q
```

要求：

```text
FAILED=0
SKIPPED=0
```

---

# 24. Documentation

任务书：

```text
docs/tasks/PHIAGENT_O7A_JR1_JUDGE_MODEL_REPLACEMENT_EVALUATION_TASK.md
```

报告继续追加到：

```text
docs/PHIAGENT_O7A_SCHOLARLY_CONTRACT_EVALUATION_CONSTITUTION.md
```

新增：

```text
O7-A JR1 — Judge Model Replacement Evaluation
```

不得覆盖：

```text
original BLOCKED
RP1 BLOCKED
RP2 BLOCKED_JUDGE_MODEL
```

---

# 25. SHA Discipline

```text
BASE_SHA=

JR1_CODE_SHA=
JUDGE_BAKEOFF_GATE_SHA=

HEAD_SHA=
REMOTE_SHA=
```

所有 Full Gate 候选必须使用同一个：

```text
JUDGE_BAKEOFF_GATE_SHA
```

如果 evaluator/fixture/semantic prompt 改动：

```text
INVALIDATE ALL CANDIDATE COMPARISONS
REFREEZE
```

---

# FINAL RECEIPT

```text
O7_A_JR1 =
READY_FOR_FINAL_REVIEW /
BLOCKED_NO_QUALIFIED_JUDGE /
BLOCKED_INFRASTRUCTURE

BASE_SHA=

JR1_CODE_SHA=
JUDGE_BAKEOFF_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

EVALUATOR_CONSTITUTION_HASH=
FIXTURE_SET_HASH=
EXPECTED_LABELS_HASH=
SEMANTIC_JUDGE_PROMPT_HASH=
QUOTE_PROBE_HASH=
AGGREGATOR_HASH=

CONTROL_MODEL=glm-4-plus
CONTROL_STATUS=REJECTED

CANDIDATE_COUNT=

CANDIDATE_1_MODEL=
CANDIDATE_1_PROVIDER=
CANDIDATE_1_VERSION=
CANDIDATE_1_SCREEN_PASS=
CANDIDATE_1_FULL_PASS=
CANDIDATE_1_CONFIRM_PASS=
CANDIDATE_1_QUALIFIED=

CANDIDATE_2_MODEL=
...
CANDIDATE_3_MODEL=
...

QUALIFIED_JUDGE_COUNT=
QUALIFIED_MODELS=

RECOMMENDED_JUDGE_MODEL=
RECOMMENDATION_REASON=

SELECTED_MODEL_FATAL_RECALL_A=
SELECTED_MODEL_FATAL_RECALL_B=

SELECTED_F1_RECALL=
SELECTED_F2_RECALL=
SELECTED_F3_RECALL=
SELECTED_F4_RECALL=
SELECTED_F5_RECALL=
SELECTED_F6_RECALL=

SELECTED_FALSE_FATAL_A=
SELECTED_FALSE_FATAL_B=

SELECTED_FATAL_AGREEMENT=
SELECTED_DIMENSION_DIFF_LE1=
SELECTED_APPLICABILITY_AGREEMENT=
SELECTED_REQUIRED_NA_CONTRADICTIONS=

SELECTED_CONFIRM_FATAL_RECALL=
SELECTED_CONFIRM_FALSE_FATAL=

SCREEN_CALLS=
FULL_CALLS=
CONFIRM_CALLS=
TOTAL_CALLS=

P50_LATENCY=
P95_LATENCY=
TOKEN_USAGE=
COST=

PRODUCTION_POLICY_CHANGED=false
PRODUCTION_TOOLS_CHANGED=false
PRODUCTION_RUNTIME_CHANGED=false
PRODUCTION_VALIDATOR_CHANGED=false
PRODUCTION_RETRIEVAL_CHANGED=false
CORPUS_CHANGED_BY_O7A=false
NO_PRODUCTION_IMPORTS=true

JR1_TESTS=

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
NO_QUALIFIED_JUDGE /
INFRASTRUCTURE_BLOCKED

STOP
```

这一阶段最重要的是：**不要再“优化一个 judge”，而是把 judge 本身当作待测量对象。**

我们已经把尺子的结构做对了；现在要做的是换一块真正稳定的传感器。

