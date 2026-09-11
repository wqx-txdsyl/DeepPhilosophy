# PhiAgent O7-E V8 Fresh Formal Qualification 任务书（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 在会话 chatgpt.com/c/6aa3e455-ae50-83ee-a4af-359574391bb7 随 V7_F2_R1_REVIEW=PASS 一并签发。

---

## Reviewer Verdict（V7-F2-R1）

```
V7_F2_R1_REVIEW=PASS
V7_F2_R1_PASS=true
V7_F2_R1_CLOSED=true
V7_F2_PASS=true
V7_F2_CLOSED=true
REVIEWED_REMOTE_SHA=33243d0d19f9c49bf7bc813532f5e612ea20f5ec
CONTENT_HEAD=8a0fb23a2e777d787a0239053766a1bc9a78517d
ARCHIVE_HEAD=33243d0d19f9c49bf7bc813532f5e612ea20f5ec
V7_MEASUREMENT_UNCHANGED=true
V7_SCHOLARLY_GATE=PASS_FROZEN
V7_DELIVERY_GATE=FAIL_FROZEN
V7_OVERALL=FAIL_FROZEN
V8_AUTHORIZED=true
```

V7-F2-R1 正式通过。（独立核验要点：远端拓扑一致；真实实现已提交且为纯确定性七类分类器、弱身份/灰区导向 AMBIGUOUS、无 LLM；8 字段语义快照已进入真实 validation history；V7-04/V7-06 DEV probe 是真实 production-path 重跑且无 NEEDS_CLASSIFICATION 占位；A–E/relabel/fail-closed/production-path integration tests 均已落盘；V2 历史边界已纠正且四个冻结结论保持；final gate blob 仍为 22ea181c…；ARCHIVE_HEAD 纯 docs/evidence；旧 failed-review artifact 与 V7 formal verdict 未被改写。透明限制（非 blocker）：GitHub Actions 无该 CONTENT_HEAD run，859 passed 未在 CI 亲自重跑，接受为 execution evidence。）

V7 裁定保持原样：V7_SCHOLARLY_GATE=PASS / V7_DELIVERY_GATE=FAIL / V7_OVERALL=FAIL，不会改成 PASS。

---

## V8 任务书：O7-E V8 fresh formal qualification

**MODEL：** DeepSeek v4 Flash（Production）　**Builder：** GLM-5.3　**Reviewer：** GPT-5.6 Sol

**BASE：** `33243d0d19f9c49bf7bc813532f5e612ea20f5ec`　V7-F2 已 CLOSED。

注意：这个 V8 是 O7-E 内部 qualification 版本，不是路线图中 O7 完成后的 Phase O8 综合能力测评。

### 目标

使用**全新、未消费 qualification cases**，在当前冻结 production pipeline 上执行 V8，证明：

```
SCHOLARLY_GATE  DELIVERY_GATE  SEMANTIC_TRANSITION_ACCOUNTING  FINAL_GATE
```

能够同时成立。

**不得利用 V7-04 / V7-06 DEV probe 作为 V8 qualification 数据。**

### 修复规则

本任务默认是 **qualification-only**。

必须：

- 使用 fresh / unconsumed formal cases；
- 使用 `deepseek-v4-flash` production path；
- Local Patch 保持当前冻结配置；
- 每轮保留：legacy fingerprint telemetry；8-field `issue_details`；`semantic_transition`；
- Delivery 同时报告：introduced fingerprints；genuinely new issues；rekey；locator shift；relabel；ambiguous；
- `AMBIGUOUS > 0` 必须 fail-closed；
- scholarly judge 使用当前冻结 judge / rubric / thresholds。

如果 V8 暴露失败：**停止 qualification，提交真实失败证据给 Reviewer。不得在同一任务中自行修改 production 再重跑到绿。**

### 重要边界

禁止：

- 修改 corpus；
- 修改 primary retrieval；
- 修改 scholarly retrieval；
- 修改 bibliography guard；
- 修改 judge；
- 修改 production model；
- 修改 Local Patch；
- 修改 validator；
- 修改 quote_bound；
- 修改 replay；
- 修改 alias resolver；
- 修改 repair strategy；
- 修改 semantic classifier；
- 修改 final gate；
- 修改 V3–V7 任何历史 verdict/evidence；
- 消费 V7-F2-R1 DEV probe 作为 formal data；
- 为通过 V8 调参或挑 case。

V7 永久保持：

```
V7_SCHOLARLY_GATE=PASS_FROZEN  V7_DELIVERY_GATE=FAIL_FROZEN  V7_OVERALL=FAIL_FROZEN
```

### 测试

- fresh-case provenance / 未消费性检查。
- production model / production path 身份检查。
- formal run 全 case 完整执行。
- scholarly judge 全量。
- delivery metrics 全量。
- semantic transition accounting 守恒检查。
- `AMBIGUOUS` fail-closed。
- final gate。
- full backend regression。
- 确认 frozen production blobs 未变化。

### 最终回执

```
V8_FORMAL_QUALIFICATION = PASS/FAIL
BASE_SHA:
QUALIFICATION_HEAD:
REMOTE_SHA:
FRESH_CASES=true/false
PREVIOUSLY_CONSUMED_CASES=0/<n>
PRODUCTION_MODEL:
PRODUCTION_PATH=true/false
CASE_COUNT:
PUBLISHED:
REPAIR_CONVERGENCE:
SCHOLARLY_GATE=PASS/FAIL
DELIVERY_GATE=PASS/FAIL
SEMANTIC_TRANSITION_ACCOUNTING=PASS/FAIL
FINAL_GATE=PASS/FAIL
REPAIR_INTRODUCED_FINGERPRINT_CASES:
REPAIR_INTRODUCED_GENUINELY_NEW_ISSUE_CASES:
REPAIR_REKEY_CASES:
REPAIR_LOCATOR_SHIFT_CASES:
REPAIR_RELABEL_CASES:
REPAIR_TRANSITION_AMBIGUOUS_CASES:
REPAIR_CREATES_NEW_FATAL_ERROR:
V7_MEASUREMENT_UNCHANGED=true/false
V7_VERDICT_UNCHANGED=true/false
FROZEN_PRODUCTION_CHANGED=false/true
FULL_TEST_SHA:
FULL_TEST_RESULT:
READY_FOR_V8_REVIEW=true/false
```

若任一 formal gate FAIL：

```
READY_FOR_V8_REVIEW=true  V8_FORMAL_QUALIFICATION=FAIL
```

保留失败证据，交 Reviewer 决定下一步。

**STOP。**

如果 V8 经独立审计 PASS，才是 **O7-E 正式完成**。之后按我们刚冻结的长期路线进入 **Phase O8：综合问题集 + 思考/工具/回答全链能力测评 + 全工具统一审计**，而不是立即宣布 PhiAgent Core Frozen。
