# PhiAgent O7-E V6-F1-R1 V6-09 Record Audit Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 给出的 V6-F1 RCA PATCH_REQUIRED + R1 record audit 任务书。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V6-F1 RCA PATCH_REQUIRED

方向大概率是对的（V6-09 更像中文二手语料覆盖不足，而非「模型看见了好文献却没 READ」），但缺的恰好是证明 PRIMARY ROOT CAUSE 的那层证据。

```
V6_MEASUREMENT_UNCHANGED=true
RCA_SCOPE_INTEGRITY=PASS
CORPUS_COVERAGE_GAP=LIKELY_BUT_NOT_YET_FORMALLY_CLOSED
READ_ORCHESTRATION_FAILURE=NOT_DEMONSTRATED
EVIDENCE_PROMOTION_FAILURE=NOT_DEMONSTRATED
PRIMARY_ROOT_CAUSE=NOT_YET_CLOSED
V6_F1_RCA_REVIEW=PATCH_REQUIRED
V6_F1_CLOSED=false
PRODUCTION_REPAIR_AUTHORIZED=false
V7_AUTHORIZED=false
```

一、Scope 没问题（base→HEAD 2 commits, docs-only, PRODUCTION_DRIFT=0, SCOPE_INTEGRITY=PASS）。

二、真正 blocker：没有保存 returned records 明细。任务书要求 returned_source_record_ids → title/relevance → retrieval_origin → access_level，但 8-call audit 只有 returned=8/readable=4/direct_relevant=0 + note。「0 个直接相关记录」本身必须可独立复核——64 条证据要交出来，而不是「我看过了，0 条相关」。

三、内部数字矛盾：27 ≠ 32（per-call abstract_available 之和 = 32；正文写 27 条 ABSTRACT_AVAILABLE）。若 27 是 unique 则明确写 32 occurrences / 27 unique。

四、Query #5 不能再写「8/8 构造零缺陷」：`Dong Zhongshu righteousness profit Ming dynasty Neo-Confucianism` 的 Ming dynasty 与董仲舒时代不匹配（QUERY_05_FORMULATION_DEFECT=CONFIRMED）。「search 行为本身优秀」等表述必须收回。QUERY_FORMULATION_FAILURE_AS_PRIMARY=NOT_DEMONSTRATED 维持。

五、核心方向暂时保留：READ_ORCHESTRATION_FAILURE / EVIDENCE_PROMOTION_FAILURE 的 NOT_DEMONSTRATED 锁定；corpus/discovery side 是当前首要嫌疑。

---

## R1 任务书

**MODEL:** GLM-5.3　**BASE:** `6016321222445bd4e41fb4eb0caf009aed55fc93`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

Objective：补齐 V6-F1 唯一 blocker——把 V6-09 原始 8 次 search 实际返回的每条 record 固化为可独立复核证据。RCA evidence closure only。

Freeze：禁止 V6 rerun/rejudge；新 production answer；修改任何 V6 canonical artifact；修改 production/retrieval/corpus/registry/ranking；实施任何 repair；用 post-run 新搜索结果冒充 V6-time exposure。保留原 V6_F1_V6_09_SECONDARY_EVIDENCE_RCA.json 为历史文件不覆盖。新增 docs/evidence/V6_F1_R1_V6_09_RECORD_AUDIT.json。

### §1 Frozen per-record audit

只使用 frozen V6_FINAL_HOLDOUT_RUN.json 中 V6-09 当时实际返回的 8 次 search。对每个 returned occurrence 记录：tool_call_id / exact_query / rank / source_record_id / title / retrieval_origin / access_level / readable / relevance（DIRECT|SUPPORTING|IRRELEVANT|UNCERTAIN）/ relevance_reason / was_read / content_evidence。不得只给 aggregate。

### §2 Dedup reconciliation

报告 SEARCH_CALLS=8 / RESULT_OCCURRENCES=64 / UNIQUE_RECORDS / READABLE_RESULT_OCCURRENCES / UNIQUE_READABLE_RECORDS / DIRECT_UNIQUE_RECORDS / SUPPORTING_UNIQUE_RECORDS / DIRECT_OR_SUPPORTING_READABLE_UNIQUE_RECORDS / RELEVANT_READABLE_BUT_UNREAD。必须明确解释 32 vs 27。

### §3 Query-05 correction

明确记录 Ming dynasty 时代错配（QUERY_05_FORMULATION_DEFECT=CONFIRMED）。重新裁定 QUERY_FORMULATION_FAILURE；区分单条 defect 与 primary/systemic root cause；不得再声称 8/8 零缺陷。

### §4 Root-cause closure

只有当 frozen original results 的逐条证据证明 DIRECT_OR_SUPPORTING_READABLE_UNIQUE_RECORDS=0 且 supplemental registry diagnostics 同样支持 corpus 缺失时，才可 CORPUS_COVERAGE_GAP=CONFIRMED / PRIMARY_ROOT_CAUSE=CORPUS_COVERAGE_GAP。结论范围只能是「当前 local registry + 当前 reachable scholarly provider universe」，不得扩大为「中国学界不存在此类文献」。若发现任何 DIRECT/SUPPORTING + 可读 + was_read=false → 重新打开 READ_ORCHESTRATION_FAILURE 并如实裁定。Post-run diagnostic probes 必须单独标记 SUPPLEMENTAL_ONLY。

Exit：不实施 repair。最终仅 READY_FOR_V6_F1_R1_RCA_REVIEW。STOP.

Milestone：V6=CONSUMED/SCHOLARLY FAIL；V6-F1: RCA_DIRECTION=PLAUSIBLE, EVIDENCE_CLOSURE=INCOMPLETE, REVIEW=PATCH_REQUIRED；V6-F1-R1=AUTHORIZED；V6-F2/V7=NOT AUTHORIZED。

「这次 R1 不需要再『研究一遍』。把现有 64 个 frozen result occurrence 摊平、逐条标 relevance、去重并把 27/32 对齐即可。做完这一层，如果确实还是 0 relevant readable，我就可以正式把 CORPUS_COVERAGE_GAP 签成 primary，然后直接下 V6-F2。」
