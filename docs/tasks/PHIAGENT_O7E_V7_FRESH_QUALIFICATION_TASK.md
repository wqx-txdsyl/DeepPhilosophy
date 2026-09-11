# PhiAgent O7-E V7 Fresh Qualification Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 签发 V6_F2_R1 PASS / V6_F2 CLOSED + V7 任务书。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer 签字：V6_F2_R1 PASS，V6_F2 CLOSED

两个 content blocker 都闭合，提交边界恢复正常。14 项 gate 全 PASS。

```
V6_F2_R1_PASS=true
V6_F2_PASS=true
V6_F2_CLOSED=true
CHENLIANG_DIRECT_READABLE=PASS
YESHI_DIRECT_READABLE=PASS
DONGZHONGSHU_REGRESSION=PASS
THREE_CLUSTER_CONTENT_GATE=PASS
RANKING_REPAIR=PASS_FROZEN
RANKING_CHANGED_IN_R1=false
FULL_TEST_EVIDENCE=PASS（843/0/0 @ ac00aab65 == CONTENT_HEAD）
ARCHIVE_TOPOLOGY=PASS
V6_RERUN=NOT_AUTHORIZED
V6_REJUDGE=NOT_AUTHORIZED
V7_AUTHORIZED=true
V7_QUALIFICATION_BASE=482c3f2f86bfdf7ac534e6150b6111dba0e1202a
```

关键核验：陈亮记录摘要（10.17715/jme.2015.04.27.1.69）与 KCI 页面独立对照吻合；叶适记录（10.12677/acpp.2024.139332）与汉斯官方页中文摘要逐内容吻合；三簇 production-path 3/3 DIRECT → READABLE → get_scholarly_source → nonempty content evidence；FULL_TEST_SHA == CONTENT_HEAD。
两个非阻塞勘误（不开 patch）：①READ 时 access 已是 ABSTRACT_AVAILABLE（升级发生在 ingest 阶段，反而符合 gate）；②陈亮 provenance label 写 PUBLISHER_PAGE_PUBLIC 实为 OpenAlex（NON_BLOCKING_PROVENANCE_LABEL_DEFECT=true, ACTION=DO_NOT_OPEN_ANOTHER_F2_PATCH）。

---

## V7 任务书

**MODEL:** GLM-5.3　**PRODUCTION_MODEL:** deepseek-v4-flash　**QUALIFICATION_BASE:** `482c3f2f86bfdf7ac534e6150b6111dba0e1202a`　**REVIEWER:** GPT-5.6 Sol

### Freeze

从 QUALIFICATION_BASE 冻结全部 production：agent/runtime；primary + scholarly retrieval/ranking；corpus/registry；bibliography guard；LOCATE→READ contract；original-call provenance；Local Patch / validator / quote_bound；canonical judge/rubric/threshold/final gate。V7 结果出现后禁止调参。

V7 一旦产生任何有效 model/tool execution 即视为 consumed；FAIL 不得 rerun/rejudge，只能产品修复后 fresh V8。

### Fresh 12-case holdout

任何 production run 前先提交 manifest + SHA lock。必须：

```
NO_V3_CASE_REUSE=true
NO_V4_CASE_REUSE=true
NO_V5_CASE_REUSE=true
NO_V6_CASE_REUSE=true
NO_V6_09_REUSE=true
NO_V6_09_NEAR_PARAPHRASE=true
NO_R25_RP3_REUSE=true
NO_F2_DP_PROBE_REUSE=true
NO_V6_F1_F2_DEV_PROBE_REUSE=true
CASE_CONTENT_UNSEEN_BEFORE_FREEZE=true
```

禁止把董仲舒—陈亮—叶适/永嘉义利修复主题换措辞后作为 V7 holdout。

12 case 仍覆盖：Western classical / medieval / modern / contemporary；Chinese；≥1 其他非西方传统；primary-text interpretation；concept distinction；philosopher comparison；interpretive controversy；secondary-scholarship controversy；secondary-source content evidence。若干 case 必须实质要求 secondary scholarship。

### Run

仅 deepseek-v4-flash。完整保存：prompt/final answer；validator + repair trace；full tool trajectory；scholarly original-call trace；selected source IDs/access/origin；READ evidence level/content hash；safe-fallback state。严格 LOCATE → relevance → READ → content evidence。metadata 不得冒充 content。禁止 post-run replay reconstruction。

### Mechanical + provenance

报告现有冻结指标：PUBLISHED_COUNT / REPAIR_CONVERGENCE / REPAIR_CREATES_NEW_FATAL_ERROR / TERMINAL_PENDING / TOOL_LOOP_ABORTS / VALIDATOR_FATAL_COUNTS / SCHOLARLY_SEARCH_CASES/CALLS / SCHOLARLY_READ_CASES/CALLS / CONTENT_EVIDENCE_CASE_COUNT / SAFE_FALLBACK_CASE_COUNT，以及 SCHOLARLY_TRACE_CALLS / TRACE_WITH_TOOL_CALL_ID / UNIQUE_TOOL_CALL_IDS / SEARCH_TRACE_COMPLETE / READ_TRACE_COMPLETE。

### Judge

冻结 canonical judge 只运行一次。报告 JUDGE_CASES_EXPECTED/VALID/MISSING、EVALUATION_INVALID、applicable_mean、五个 required dimension means、REQUIRED_DIMENSION_MEDIAN_LT_2、REQUIRED_DIMENSION_MISSING_SCORE 及全部六类 fatal counts。不得修改 judge output。

### Final gate

运行冻结 version-neutral checker：DELIVERY_GATE / SCHOLARLY_GATE / FAILED_GATES / FATAL_COUNTS / FINAL_V7_VERDICT。Builder 不得自行声明 O7-E PASS。最终停：READY_FOR_V7_SCHOLARLY_REVIEW。STOP.

Milestone：V5-F2=PASS/CLOSED；V6=CONSUMED/SCHOLARLY FAIL；V6-F1=PASS/CLOSED；V6-F2=PASS/CLOSED；V7=AUTHORIZED；QUALIFICATION_BASE=482c3f2f...

「下一次直接给我 V7 fresh qualification 回执；我按最终 scholarly gate 独立审。」
