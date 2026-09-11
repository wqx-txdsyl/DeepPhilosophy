# PhiAgent O7-E V7-F2 Repair Transition Observability + Metric Contract Versioning Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 签发 V6_F2_R1 PASS / V6_F1 CLOSED + V7-F2 任务书。
> 会话 URL: chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V7_F1_R1 PASS，V7_F1 CLOSED

这次可以正式关线。两个 content blocker 都闭合了。

```
V7_F1_R1_PASS=true
V7_F1_CLOSED=true
V7_MEASUREMENT_UNCHANGED=true
V7_SCHOLARLY_GATE=PASS_FROZEN
V7_DELIVERY_GATE=FAIL_FROZEN
TRANSIENT_INTRODUCED_FINGERPRINTS=CONFIRMED
SEMANTIC_NOVELTY=NOT_RECOVERABLE_FROM_V7_ARCHIVE
SET_DIFFERENCE_TELEMETRY_INTENT=CONFIRMED
FROZEN_IMPLEMENTATION_ANY_INTRODUCED=CONFIRMED
FROZEN_FINAL_GATE_ZERO_TOLERANCE=CONFIRMED
HISTORICAL_INTENT_ANY_INTRODUCED_AUTO_FATAL=NOT_ESTABLISHED
METRIC_IMPLEMENTATION_MATCHES_INTENDED_CONTRACT=UNRESOLVED
METRIC_NAME_ONLY_MISNOMER=UNRESOLVED
MEASUREMENT_SEMANTIC_BUG=UNRESOLVED
SEMANTIC_ROOT_CAUSE=NOT_RECOVERABLE
PRODUCT_ROOT_CAUSE=UNRESOLVED
```

V7-F1 = PASS / CLOSED。V8 = 暂不放行。

---

## V7-F2 任务书

**MODEL:** GLM-5.3　**BASE:** `a52678fc8fc4ce5dab100b63e8206f82ccc2d75c`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

### Objective

关闭 V8 前唯一剩余问题：
- 让每轮 repair transition 可恢复语义身份，不再只有单向 fingerprint
- 用 DEV evidence 区分：genuine new validator issue / same issue rekeyed / locator shift / issue-code relabel
- 为未来 qualification 提出显式、版本化的 Delivery Metric V2 contract

### §1 Historical freeze

永久保持 V7_SCHOLARLY_GATE=PASS、V7_DELIVERY_GATE=FAIL、V7_FINAL_VERDICT=DELIVERY_GATE_NOT_MET。不得修改/覆盖 V7 artifact。旧 REPAIR_CREATES_NEW_FATAL_ERROR 的 V3–V7 历史值全部保持原义、原 verdict。

### §2 Per-round semantic observability

在 validator 每个真实状态（INITIAL → R1 → R2 → ... → TERMINAL）即时持久化 bounded structured issue snapshot。每个 issue 至少：

round_id / fingerprint / issue_code / semantic_family / normalized_locator / evidence_ref / source_record_id / citation_or_quote_target_id

字段不存在时显式 null。禁止保存 CoT / 整篇 candidate / repair prompt / 大段 evidence 正文。

### §3 Semantic transition classifier

新增 deterministic classifier，至少输出：RESOLVED / PERSISTED / GENUINELY_NEW_ISSUE / SAME_ISSUE_REKEYED / LOCATOR_SHIFT_ONLY / ISSUE_CODE_RELABEL / AMBIGUOUS。

要求：fingerprint set-difference telemetry 继续保留；semantic classifier 是新增第二层；AMBIGUOUS 必须 fail-closed；不允许 LLM judge transition identity。

确定性 unit tests A-E：
A. 完全相同 issue → PERSISTED
B. 同 issue 仅文本位置合理移动 → LOCATOR_SHIFT_ONLY
C. 同 semantic target 但 fingerprint 改变 → SAME_ISSUE_REKEYED
D. repair 真正制造另一 violation → GENUINELY_NEW_ISSUE
E. 无法可靠匹配 → AMBIGUOUS

### §4 V7-04/V7-06 DEV probes

V7 已消费，只允许标记 DEV_ONLY=true / QUALIFICATION=false / FORBIDDEN_FROM_V8=true。允许使用 V7-04/V7-06 prompts 验证新 observability。必须报告 NEW_FINGERPRINT_COUNT / GENUINELY_NEW_ISSUE_COUNT / REKEY_COUNT / LOCATOR_SHIFT_COUNT / RELABEL_COUNT / AMBIGUOUS_COUNT。

### §5 Delivery Metric V2 proposal

新增 docs/evidence/O7E_DELIVERY_METRIC_V2_PROPOSAL.json。Legacy telemetry：REPAIR_INTRODUCED_FINGERPRINT_CASES（不再使用 fatal 模糊表达）。Proposed semantic safety metric：REPAIR_INTRODUCED_GENUINELY_NEW_ISSUE_CASES / REPAIR_TRANSITION_AMBIGUOUS_CASES。兼容性/migration 注记。V3–V7 verdict 绝不回写。不得在本任务修改 o7e_final_gate.py gate 语义。

### §6 No scope creep

冻结：scholarly corpus/retrieval、primary retrieval、bibliography guard、judge、model、Local Patch 策略本身。本轮先观测，不修 repair strategy。

### §7 Tests & topology

完成 observability + classifier + tests 后 CONTENT_HEAD → 在 exact CONTENT_HEAD 运行 full tests → evidence-only ARCHIVE_HEAD（parent==CONTENT_HEAD）。新增 docs/evidence/V7_F2_REPAIR_TRANSITION_OBSERVABILITY.json + docs/evidence/O7E_DELIVERY_METRIC_V2_PROPOSAL.json。

### Exit

最终只报告：BASE_SHA / CONTENT_HEAD / ARCHIVE_HEAD / REMOTE_SHA / PER_ROUND_SEMANTIC_OBSERVABILITY / SEMANTIC_TRANSITION_CLASSIFIER / AMBIGUOUS_FAIL_CLOSED / V7_04_DEV_RESULT / V7_06_DEV_RESULT / LEGACY_FINGERPRINT_METRIC_DEFINED / V2_SEMANTIC_METRIC_PROPOSED / FINAL_GATE_CHANGED=false / FULL_TEST_SHA / FULL_TEST_RESULT / ARCHIVE_PARENT_EQUALS_CONTENT_HEAD / READY_FOR_V7_F2_REVIEW. STOP.

Milestone：V6-F2 = PASS / CLOSED；V7 = CONSUMED / SCHOLARLY PASS ← 首次正式通过 / DELIVERY = FAIL；V7 OVERALL = FAIL；V7-F2 = AUTHORIZED；V8 = NOT YET AUTHORIZED。
