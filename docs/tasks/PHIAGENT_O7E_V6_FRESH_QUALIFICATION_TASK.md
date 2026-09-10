# PhiAgent O7-E V6 Fresh Qualification Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-07 签发 V5_F2_PASS + V6 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer 签字：V5_F2_PASS

这条线可以正式关了。R1.1 唯一剩余的 provenance blocker 已经闭合，不再开启任何 F2 repair line。

14 项 gate 全 PASS（topology / archive evidence-only / scope freeze / original-call capture / post-run replay removed / cache dependence removed / search pre-READ access preserved / READ before→after transition / mutation immunity / repeated-call identity / real 7-probe provenance / F2 regression / full tests 843/0/0 / V5-F2 final）。

关键确认：engine_langgraph 现在在 scholarly tool 真实返回的当下构造独立 scholarly_trace（search 保存 source IDs、当时 access level、origin/error/offline；READ 保存 before/after、evidence level、content hash），harness 的事后 replay 与 SID 反查已物理删除。97 次 scholarly call → 97 个 trace → 97 个 tool_call_id；37 组 search→READ 对账全部 pre-read access 一致。

正式状态冻结为：

```
V5_F2_R1_1_PASS=true
ORIGINAL_CALL_CAPTURE=PASS
POST_RUN_REPLAY=false
CACHE_DEPENDENCE=false
MUTATION_IMMUNITY=PASS
SEARCH_SNAPSHOT_PRE_READ_ACCESS=PASS
READ_SNAPSHOT_TRANSITION=PASS
REPEATED_CALL_IDENTITY=PASS
BIBLIOGRAPHY_GUARD=PASS_FROZEN
SAFE_FALLBACK_BEHAVIOR=PASS_FROZEN
F2_DEV_REGRESSION=PASS_FROZEN
V5_F2_PASS=true
V5_F2_CLOSED=true
V5_RERUN=NOT_AUTHORIZED
V5_REJUDGE=NOT_AUTHORIZED
V6_AUTHORIZED=true
V6_QUALIFICATION_BASE=2b6840bc2e4eaeee96bc27617e85fc57e407071d
```

注意，F2 PASS 不改写已经消费掉的 V5 qualification 历史结果；它的含义是：V5 暴露出来的 scholarly pipeline 问题已经完成产品级修复，现在可以用一个完全新的 holdout 做 V6。

---

## V6 任务书

**MODEL:** GLM-5.3　**PRODUCTION_MODEL:** deepseek-v4-flash　**QUALIFICATION_BASE:** `2b6840bc2e4eaeee96bc27617e85fc57e407071d`　**REVIEWER:** GPT-5.6 Sol

### §1 Freeze

从 QUALIFICATION_BASE 起冻结 production。

禁止修改 production agent/runtime、primary retrieval、scholarly retrieval / LOCATE→READ、corpus/registry/aliases、F2 bibliography guard、original-call provenance、Local Patch、validator/final_validator、quote_bound、repair_context、canonical judge、rubric、threshold、final-gate logic。

不得针对 V6 结果调参或修补。

**V6 一旦执行即消费。FAIL 后不得 rerun / rejudge；只能修产品后进入 fresh V7。**

### §2 Fresh Holdout

在任何 V6 production run 前生成并提交 **12-case 全新 holdout manifest + SHA lock**。

必须：

```
NO_V3_CASE_REUSE=true
NO_V4_CASE_REUSE=true
NO_V5_CASE_REUSE=true
NO_R25_REUSE=true
NO_RP3_DEV_PROBE_REUSE=true
NO_F2_DEV_PROBE_REUSE=true
NO_DP07_NONCE_REUSE=true
CASE_CONTENT_UNSEEN_BEFORE_FREEZE=true
```

不得使用旧 qualification/dev probe 的近似改写。

12 cases 总体必须覆盖：Western classical / medieval / modern / contemporary、中国哲学、至少一种其他非西方传统、primary-text interpretation、concept distinction、philosopher comparison、interpretive controversy、secondary-scholarship controversy、secondary-source content-evidence。

其中若干题必须**实质需要 secondary scholarship**，不能靠原典回答后附几个书目完成。

### §3 Frozen Production Run

只允许 deepseek-v4-flash。完整保存每 case：prompt / final answer / publication result / validator result / repair trace / complete tool trajectory。

scholarly calls 必须保存本次已冻结的 original-call provenance：tool_call_id + args + scholarly_trace。SEARCH trace 至少含 returned_source_record_ids / access_levels / retrieval_origins / provider_errors / offline_mode；READ trace 至少含 source_record_id / access_before / access_after / returned_evidence_level / content_hash。

必须保持 LOCATE → relevance check → READ/FETCH → content evidence。metadata 不得冒充 content evidence。无法取得 relevant content 时必须诚实 safe fallback。禁止 post-run search replay 或 cache reconstruction。

### §4 Mechanical Summary

至少报告：PUBLISHED_COUNT / REPAIR_TRIGGERED / REPAIR_CONVERGED / REPAIR_CONVERGENCE / REPAIR_CREATES_NEW_FATAL_ERROR / TERMINAL_PENDING / TOOL_LOOP_ABORTS / VALIDATOR_FATAL_COUNTS / UNVERIFIED_PUBLIC_EXACT_QUOTES / STITCHED_PUBLIC_QUOTES / PUBLIC_INVALID_CITATIONS / SCHOLARLY_SEARCH_CASES / SCHOLARLY_SEARCH_CALLS / SCHOLARLY_READ_CASES / SCHOLARLY_READ_CALLS / CONTENT_EVIDENCE_CASE_COUNT / SAFE_FALLBACK_CASE_COUNT。

同时增加 provenance completeness：SCHOLARLY_TRACE_CALLS / SCHOLARLY_TRACE_WITH_TOOL_CALL_ID / UNIQUE_SCHOLARLY_TOOL_CALL_IDS / SEARCH_TRACE_COMPLETE / READ_TRACE_COMPLETE。以及冻结的 Local Patch metrics。

### §5 Canonical Scholarly Judge

只运行**一次**冻结 canonical judge。不得修改 judge/rubric/threshold。报告 JUDGE_CASES_EXPECTED / VALID / MISSING、EVALUATION_INVALID、applicable_mean、五维均值、REQUIRED_DIMENSION_MEDIAN_LT_2、REQUIRED_DIMENSION_MISSING_SCORE 和全部 frozen fatal counts。Builder 不得修改 judge output。

### §6 Final Gate

运行现有冻结、version-neutral final gate。必须输出 DELIVERY_GATE / SCHOLARLY_GATE / FAILED_GATES / FATAL_COUNTS / FINAL_V6_VERDICT。Builder **不得**自行宣布 O7-E_PASS / FINAL_PASS。无论结果如何，都只能停在 READY_FOR_V6_SCHOLARLY_REVIEW。最终 PASS/FAIL 由 Reviewer 决定。

### §7 Artifacts

```
docs/evidence/V6_FRESH_HOLDOUT_MANIFEST.json
docs/evidence/V6_HOLDOUT_LOCK.json
docs/evidence/V6_FINAL_HOLDOUT_RUN.json
docs/evidence/V6_FINAL_HOLDOUT_SUMMARY.json
docs/evidence/V6_FINAL_HOLDOUT_JUDGE.json
docs/evidence/V6_FINAL_HOLDOUT_JUDGE_SUMMARY.json
docs/evidence/V6_FINAL_GATE.json
```

最终回执：QUALIFICATION_BASE / MANIFEST_FREEZE_SHA / HEAD_SHA / REMOTE_SHA / NEW_AGENT_RUN=true / NEW_JUDGE_RUN=true / NO_PRIOR_CASE_REUSE=true / 12-case coverage / mechanical metrics / provenance metrics / judge metrics / fatal counts / final-gate output / full pytest result / READY_FOR_V6_SCHOLARLY_REVIEW。STOP.

**V5_F2 到此正式 CLOSED。下一次你直接把 V6 回执给我，我按 fresh qualification gate 审。**
