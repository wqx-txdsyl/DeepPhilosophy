# PhiAgent O7-E V8-F1 Root-Cause Analysis 任务书（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 在会话 chatgpt.com/c/6aa3e455-ae50-83ee-a4af-359574391bb7 随 V8_REVIEW=FAIL_CONFIRMED 一并签发。

---

## Reviewer Verdict（V8）

```
V8_REVIEW=FAIL_CONFIRMED
V8_FORMAL_QUALIFICATION=FAIL_FROZEN
V8_QUALIFICATION_RUN_CLOSED=true
V8_CASES_CONSUMED=true
FRESH_CASES=CONFIRMED
DELIVERY_GATE=PASS_CONFIRMED
SEMANTIC_TRANSITION_ACCOUNTING=PASS_CONFIRMED
SCHOLARLY_GATE=FAIL_CONFIRMED
FINAL_GATE=FAIL_CONFIRMED
QUALIFICATION_HARNESS_CHANGED=true
FROZEN_PRODUCTION_CHANGED=false
SCHOLARLY_JUDGE_SCORING_SEMANTICS_CHANGED=false
O7_E_COMPLETE=false
V8_F1_AUTHORIZED=true
```

V8 的 FAIL 成立，而且这次 Builder 正确遵守了「失败即停」的 qualification discipline。12 case freshness 机械证据成立（max Jaccard 0.1696 < 0.45）。最终 gate 与回执一致：11/12 发布，DELIVERY PASS / SCHOLARLY FAIL / SCHOLARLY_GATE_NOT_MET。V7 的 delivery 问题确实没有在 V8 fresh set 上复现。Semantic Transition Accounting 真正通过。V8-10 不是 repair regression（PERSISTED=4 全程，无新指纹）。

唯一程序性异常：QUALIFICATION_HARNESS_CHANGED=true——e0818327 为 judge driver 增加 manifest_path，254ee0ec 又加 cases unwrap；未改评分 prompt/rubric/阈值/vote 逻辑，不推翻 FAIL，但属 qualification topology 程序性瑕疵，V8-F1 必须正式解释。859 passed 为 Builder execution evidence（无 GitHub CI 独立重跑）。

V7: SCHOLARLY PASS / DELIVERY FAIL；V8: SCHOLARLY FAIL / DELIVERY PASS + SEMANTIC ACCOUNTING PASS——V7-F2 解决的 delivery/measurement 链已在 fresh formal data 上站住；现在暴露的是 scholarly quality 未在新题型分布上稳定复现。V8 12 case 从现在起全部 consumed，不允许重跑。

---

## V8-F1 任务书

**MODEL：** GLM-5.3　**Reviewer：** GPT-5.6 Sol

**BASE：** `d64ac0a504a87900b34800f0e8accaa21cbee223`

先执行 `git rev-parse HEAD`、`git status --short`。V8 已冻结为 DELIVERY_GATE=PASS / SEMANTIC_TRANSITION_ACCOUNTING=PASS / SCHOLARLY_GATE=FAIL / FINAL_GATE=FAIL。本任务**只定位 scholarly failure 与 V8-10 non-publication 的根因，不修 production，不重跑 V8**。

### 分析规则

**1. V8-11 fatal**：追踪 最终回答中的 scholar attribution → scholarly retrieval/tool output → source record → content evidence → judge fatal。裁定为 `SUPPORTED_ATTRIBUTION / UNSUPPORTED_MODEL_ATTRIBUTION / RETRIEVAL_CONTAMINATION / JUDGE_FALSE_POSITIVE / UNRESOLVED`。必须给出 bounded provenance；禁止 CoT。

**2. V8-12 极低 scholarly score**：逐维分析（textual grounding / argument reconstruction / historical discipline / interpretive plurality / literature orientation）。区分 `CORPUS_COVERAGE / RETRIEVAL_FAILURE / EVIDENCE_DISCIPLINE_FAILURE / PHILOSOPHICAL_REASONING_FAILURE / LITERATURE_ORIENTATION_FAILURE / JUDGE_APPLICATION_FAILURE / MIXED / UNRESOLVED`。

**3. 全 11 个 judged case 分布**：生成 case × dimension 表（applicable/required mask、三票结果、median/aggregate、fatal flags）。计算原始 dimension means、每维 <2 case 数、leave-one-out means（分别排除 V8-11、V8-12、同时排除二者）作为诊断值。只用于 root-cause，不得改写 V8 verdict。最终分类 `DIMENSION_FAILURE_CONCENTRATION= BROAD / CONCENTRATED / MIXED`。

**4. V8-10**：追踪四个 persisted fingerprint 在 attempt 0/1/2：repair prompt 是否明确覆盖；evidence 是否足够；model 是否实际修改目标 span；validator 为什么仍返回同 fingerprint。分类 `REPAIR_CONTEXT_INSUFFICIENCY / MODEL_NONCOMPLIANCE / SOURCE_GAP / VALIDATOR_LOCATOR_ISSUE / MIXED / UNRESOLVED`。

**5. Judge harness 程序性审计**：核对 e0818327 / 254ee0ec 中 o7e_bakeoff_judge2.py 的两个 diff。分别报告 `MANIFEST_IO_CHANGED / SCORING_PROMPT_CHANGED / RUBRIC_CHANGED / THRESHOLDS_CHANGED / VOTE_SEMANTICS_CHANGED`，并确定 production run、judge run、final gate 各自使用的代码状态。若发现任何 score-affecting semantics 改动：`V8_MEASUREMENT_VALID=false`；否则 `V8_MEASUREMENT_VALID=true, HARNESS_PROCEDURAL_DEVIATION=true`。

### 重要边界

只分析，不修复。禁止：重跑 V8；换 case；修改 corpus / retrieval / scholarly sources / Agent runtime / validator / quote_bound / Local Patch / repair strategy / semantic classifier / judge-rubric / final gate / V3–V8 历史 evidence-verdict。可新增 deterministic analysis script、分析 evidence 和任务归档。

### 核验

- V8-11 fatal provenance 可机械追踪。
- V8-12 五维失败有逐维证据。
- 11 case × dimensions 完整，无漏 case。
- leave-one-out 计算可重复。
- V8-10 四 fingerprint 三轮身份一致性核验。
- judge-driver diff 与 scoring semantics 分离。
- production diff 相对 BASE 为零。

### 最终回执

```
BASE_SHA=  HEAD_SHA=  V8_FAILURE_EVIDENCE_PRESERVED=true
V8_11_FATAL_ROOT_CAUSE=  V8_11_JUDGE_FALSE_POSITIVE=true/false/unresolved
V8_12_LOW_SCORE_ROOT_CAUSE=  DIMENSION_FAILURE_CONCENTRATION=BROAD/CONCENTRATED/MIXED
FAILED_GATE_ROOT_CAUSE_MAP={ APPLICABLE_DIMENSION_MEAN / HISTORICAL_DISCIPLINE / INTERPRETIVE_PLURALITY / LITERATURE_ORIENTATION / REQUIRED_DIMENSION_MEDIAN_LT_2 / FABRICATED_SCHOLAR_ATTRIBUTION }
V8_10_PERSISTENCE_ROOT_CAUSE=
MANIFEST_IO_CHANGED=  SCORING_PROMPT_CHANGED=  RUBRIC_CHANGED=  THRESHOLDS_CHANGED=  VOTE_SEMANTICS_CHANGED=
HARNESS_PROCEDURAL_DEVIATION=  V8_MEASUREMENT_VALID=  PRODUCTION_CHANGED=false  V8_RERUN=false
READY_FOR_V8_F1_REVIEW=true  STOP
```

O7-E 现在还不能关闭。V8-F1 先回答「学术门为什么掉了」；只有根因成立后，Reviewer 再决定是 V8-F2 repair，还是测量链 patch，之后才会授权使用另一批 fresh、未消费 case 做 V9。
