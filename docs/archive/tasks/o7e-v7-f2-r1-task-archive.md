# PhiAgent O7-E V7-F2-R1 Semantic Observability Closure 任务书（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 在会话 chatgpt.com/c/6aa3e455-ae50-83ee-a4af-359574391bb7（「V7 F2 审查结论」）签发。
> 前置裁定：V7_F2_REVIEW=PATCH_REQUIRED / V7_F2_CLOSED=false / V8_AUTHORIZED=false。
> 本文为逐字存档（自 Reviewer 会话转录）。

---

## Verdict 块

```
V7_F2_REVIEW=PATCH_REQUIRED
V7_F2_PASS=false
V7_F2_CLOSED=false
V7_MEASUREMENT_UNCHANGED=true
V7_SCHOLARLY_GATE=PASS_FROZEN
V7_DELIVERY_GATE=FAIL_FROZEN
V7_OVERALL=FAIL_FROZEN
V8_AUTHORIZED=false
REVIEWED_REMOTE_SHA=e1b7c8457266e732a748af9546d4a4749a2a79c9
R1_BASE=e1b7c8457266e732a748af9546d4a4749a2a79c9
```

这轮不是小型 docs 勘误，而是有 **3 个 P0 功能/证据 blocker + 2 个收口问题**。不过边界很清楚，不需要推倒重来。

| 项 | 裁定 | Reviewer 核验 |
|---|---|---|
| V7 历史 verdict 冻结 | PASS | task 明确冻结 V7 scholarly/delivery/final verdict；当前 final-gate 文件在 BASE 与 archive 的 blob SHA 均为 22ea181c...，未修改。 |
| bounded per-round history 基础链 | PARTIAL | engine 确实逐轮保存 issue_details，并保留 fingerprints；但实际只有 code / locator / evidence_ref。 |
| §2 semantic identity schema | P0 FAIL | 任务要求每 issue 至少持久化 round_id / fingerprint / issue_code / semantic_family / normalized_locator / evidence_ref / source_record_id / citation_or_quote_target_id，缺失字段还必须显式 null。当前实现明显不足。 |
| deterministic transition classifier | P0 FAIL | canonical evidence 宣称 backend/o7e_semantic_transition.py 已实现，但 e1b7c8457 对该文件直接读取为 404，递归 tree 中也不存在；代码搜索同样找不到 classifier labels。canonical artifact 的 IMPLEMENTED 声明与实际 pushed tree 不一致。证据文件自己还声称该 module 存在。 |
| A–E unit tests | P0 FAIL | frozen task 要求五类确定性测试；实际测试提交 8453e3b3 只改了 engine freeze baseline 一行，没有新增 A–E classifier tests。 |
| V7-04 / V7-06 semantic probe accounting | FAIL | task 要求分别报告 NEW_FINGERPRINT_COUNT / GENUINELY_NEW_ISSUE_COUNT / REKEY_COUNT / LOCATOR_SHIFT_COUNT / RELABEL_COUNT / AMBIGUOUS_COUNT。当前 DEV summary 没有这些字段；observability artifact 甚至把 V7-06 的新 fingerprint 标成 NEEDS_CLASSIFICATION。 |
| Metric V2 proposal | PARTIAL / evidence overclaim | V2 三个指标方向正确，但 proposal 写成"V7-F1 RCA 确认 fatal 是名称误称"；已冻结的 V7-F1 裁定实际上是 METRIC_NAME_ONLY_MISNOMER=UNRESOLVED、MEASUREMENT_SEMANTIC_BUG=UNRESOLVED。可以 prospectively 改名，但不能把历史未决问题升级成 CONFIRMED。 |
| commit topology / receipt | FAIL | 回执给的 CONTENT=338e5132 实际只是 Builder 执行计划 docs commit；remote archive e1b7c8457 的直接 parent 是 1493542a。canonical evidence 自己也把 CONTENT_HEAD 写成 1493542a。 |

有一件事我**不要求回滚**：a4eede928 里的 repair minimal-change discipline。它确实修改了 repair policy，但它是在更早的、明确授权"production-side correction"的 V7-F2 Delivery Repair 授权下实施的；R1 从现在的 e1b7c8457 向前修即可，**不要再扩大或调整 repair strategy**。该旧授权明确要求修复 transient regression 并补 observability。

---

# PhiAgent O7-E — V7-F2-R1 Semantic Observability Closure

**MODEL:** GLM-5.3　**REVIEWER:** GPT-5.6 Sol　**BASE:** `e1b7c8457266e732a748af9546d4a4749a2a79c9`　**PRODUCTION_MODEL:** `deepseek-v4-flash`

## Verdict

`V7-F2 = PATCH_REQUIRED`

V7 historical measurement/verdict remains frozen.
V8 remains unauthorized.

## R1 scope

- **Complete per-round semantic snapshot**

Every persisted validator issue must contain at least:

`round_id` `fingerprint` `issue_code` `semantic_family` `normalized_locator` `evidence_ref` `source_record_id` `citation_or_quote_target_id`

Unavailable values must be explicit `null`.

Keep snapshots bounded. No CoT, candidate body, repair prompt, or large evidence text.

Legacy fields may remain for compatibility.

- **Actually implement deterministic classifier**

Add `backend/o7e_semantic_transition.py`.

Required outputs:

`RESOLVED` `PERSISTED` `GENUINELY_NEW_ISSUE` `SAME_ISSUE_REKEYED` `LOCATOR_SHIFT_ONLY` `ISSUE_CODE_RELABEL` `AMBIGUOUS`

No LLM classification.

Weak/incomplete semantic identity must not be guessed into GENUINELY_NEW; unresolved matching → `AMBIGUOUS`.

`AMBIGUOUS` must be fail-closed.

Keep legacy fingerprint set-difference telemetry unchanged.

- **Add real deterministic tests A–E**

A identical issue → `PERSISTED`
B same issue, locator movement only → `LOCATOR_SHIFT_ONLY`
C same semantic target, fingerprint changed → `SAME_ISSUE_REKEYED`
D genuinely different violation created → `GENUINELY_NEW_ISSUE`
E insufficient/competing identity → `AMBIGUOUS`

Also test issue-code relabel and AMBIGUOUS fail-closed behavior.

- **Re-run V7-04 / V7-06 as DEV_ONLY**

Must remain:

`DEV_ONLY=true` `QUALIFICATION=false` `FORBIDDEN_FROM_V8=true`

For each case report:

`NEW_FINGERPRINT_COUNT` `GENUINELY_NEW_ISSUE_COUNT` `REKEY_COUNT` `LOCATOR_SHIFT_COUNT` `RELABEL_COUNT` `AMBIGUOUS_COUNT`

Persist the actual per-transition classifier output, not `NEEDS_CLASSIFICATION`.

Do not reinterpret or overwrite V7.

- **Correct Metric V2 evidence boundary**

Do not claim V7-F1 established that the legacy name was merely a misnomer.

Preserve:

`HISTORICAL_INTENT_ANY_INTRODUCED_AUTO_FATAL=NOT_ESTABLISHED`
`METRIC_IMPLEMENTATION_MATCHES_INTENDED_CONTRACT=UNRESOLVED`
`METRIC_NAME_ONLY_MISNOMER=UNRESOLVED`
`MEASUREMENT_SEMANTIC_BUG=UNRESOLVED`

Prospective V2 may still propose:

`REPAIR_INTRODUCED_FINGERPRINT_CASES`
`REPAIR_INTRODUCED_GENUINELY_NEW_ISSUE_CASES` — hard gate, zero tolerance
`REPAIR_TRANSITION_AMBIGUOUS_CASES` — hard gate, fail-closed

V3–V7 values/verdicts remain untouched.

- **Freeze scope**

Do not modify:

- scholarly corpus/retrieval
- primary retrieval
- bibliography guard
- judge
- production model
- Local Patch strategy / repair strategy
- `o7e_final_gate.py`

Expected `o7e_final_gate.py` blob SHA remains:

`22ea181ce652276234f59a96d2b5c5f1a66ef2d8`

- **Clean R1 topology**

From BASE create one real `CONTENT_HEAD` containing implementation + tests.

Run full pytest on **exact CONTENT_HEAD**.

Then create one direct child `ARCHIVE_HEAD` containing evidence/docs only.

Required:

`ARCHIVE_PARENT == CONTENT_HEAD`
`REMOTE_SHA == ARCHIVE_HEAD`

Do not report an earlier docs-only SHA as CONTENT_HEAD.

Create R1 evidence rather than presenting the failed-review artifact as if it had passed.

## R1 receipt

Return only:

`BASE_SHA` `CONTENT_HEAD` `ARCHIVE_HEAD` `REMOTE_SHA` `SEMANTIC_SNAPSHOT_SCHEMA_COMPLETE` `SEMANTIC_TRANSITION_CLASSIFIER` `CLASSIFIER_A_E_TESTS` `AMBIGUOUS_FAIL_CLOSED` `V7_04_DEV_COUNTS` `V7_06_DEV_COUNTS` `V2_HISTORICAL_BOUNDARY_CORRECTED` `V7_MEASUREMENT_UNCHANGED=true` `FINAL_GATE_CHANGED=false` `FINAL_GATE_BLOB_SHA` `FULL_TEST_SHA` `FULL_TEST_RESULT` `ARCHIVE_PARENT_EQUALS_CONTENT_HEAD` `READY_FOR_V7_F2_R1_REVIEW`

STOP.

这次 R1 不需要再碰 scholarly pipeline，也不需要重新做 RCA；把这几个缺失的**真实实现与证据闭环**补齐即可。
