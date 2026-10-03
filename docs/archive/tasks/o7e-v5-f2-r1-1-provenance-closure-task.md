# PhiAgent O7-E V5-F2-R1.1 Provenance Closure Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-07 给出的 V5_F2_R1_PATCH_REQUIRED 裁定 +
> R1.1 provenance closure 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V5_F2_R1_PATCH_REQUIRED（仅剩 1 blocker）

Bibliography guard / SAFE_FALLBACK behavioral proof / F2 six-probe regression / Full test (838/0/0) 全部 PASS 且锁定不再重审。唯一 blocker：per-call provenance 保存的是"事后重放"，不是"原调用快照"。

R1 任务书写得很死：「在 result_full 被剥离前建立 ... scholarly call trace」+「不得依赖 scholarly_cache.json」。

当前 harness 在 run 完成后对已记录 search args 再次调用 search_scholarship 重放补字段；READ 也是事后从 case-level scholarly_evidence 按 SID 反查。而 search_scholarship 有 cache fast-path、READ 路径会 _promote_access 原地修改 rec["access"]——存在完全正常的执行：SEARCH t1: source X access=METADATA_ONLY → READ t2: X 晋升 FULL_TEXT_* → POST-RUN replay SEARCH 显示 upgraded state——archive 会把 t2 之后的状态冒充 t1 当时的状态。这不是形式主义，是真实 provenance 污染。

```
V5_F2_R1_PATCH_REQUIRED=true
BIBLIOGRAPHY_GUARD=PASS_FROZEN
SAFE_FALLBACK_BEHAVIOR=PASS_FROZEN
F2_DEV_REGRESSION=PASS_FROZEN
PER_CALL_PROVENANCE=FAIL
ORIGINAL_CALL_CAPTURE=FAIL
POST_RUN_SEARCH_REPLAY=true
READ_POSTHOC_RECONSTRUCTION=true
V5_F2_PASS=false
V6_AUTHORIZED=false
```

---

## R1.1 任务书（只补这一个点）

**MODEL:** GLM-5.3　**BASE:** `0f4b04516307beafae58f2922441850a5af9c098`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

目标：仅关闭 per-call scholarly provenance。其他 F2/R1 gate 已冻结 PASS。

### §1 禁止范围扩大

不得修改：corpus / retrieval / ranking；bibliography guard；scholarly behavioral contract；judge / rubric / threshold / final-gate；quote_bound / evidence_contract；V5 canonical artifacts。不得新增 dev topic，不得运行 V6。

### §2 原调用即时快照

在每个 scholarly tool 的**真实返回时刻**、result_full 被剥离或后续状态可能变更之前，生成 immutable / bounded / no-CoT provenance snapshot，并绑定 tool_call_id。

search_scholarship：tool_call_id / args / returned_source_record_ids / access_levels / retrieval_origins / provider_errors / offline_mode

get_scholarly_source：tool_call_id / args / source_record_id / access_before / access_after / returned_evidence_level / content_hash

只保留上述安全字段；不得保存 passage 正文或 CoT。

### §3 禁止事后重构

删除 qualification harness 中为了 provenance 再次执行 SS.search_scholarship(...) 的 replay 路径。必须：POST_RUN_REPLAY=false。不得依赖 scholarly_cache.json 重构原调用结果。

READ provenance 也不得仅从 case-level scholarly_sources 按 SID 反查；必须来自对应原始 READ tool call snapshot。

### §4 Mutation-immunity regression

增加确定性 regression：
- SEARCH 返回 source X，原始 access=METADATA_ONLY
- 后续 READ 将同 source 晋升到更高 access
- 最终 archive 中：SEARCH snapshot 仍必须是 METADATA_ONLY；READ snapshot 正确显示 before→after transition
- 修改 cache/current record 后不得反向改变已经生成的 SEARCH snapshot

即：MUTATION_IMMUNITY=PASS

### §5 Repeated-call identity

增加 regression：同 query 搜索两次、同 source READ 两次。每个调用必须拥有独立 tool_call_id 和对应 snapshot，不得按 SID/query 合并造成历史歧义。

即：REPEATED_CALL_IDENTITY=PASS

### §6 Closure

运行相关 provenance tests + full backend tests。如需要，可重跑现有 F2-R1 7 probes 作 regression；不得修改 probe 内容。

先提交 CONTENT_HEAD。再单独 evidence-only commit：ARCHIVE_HEAD.parent == CONTENT_HEAD。

新增：docs/evidence/V5_F2_R1_1_PROVENANCE_CLOSURE.json。不得覆盖既有 F2 / F2-R1 evidence。

最终回执仅报告：

```
BASE_SHA
CONTENT_HEAD
ARCHIVE_HEAD
REMOTE_SHA
ORIGINAL_CALL_CAPTURE=PASS
POST_RUN_REPLAY=false
CACHE_DEPENDENCE=false
MUTATION_IMMUNITY=PASS
SEARCH_SNAPSHOT_PRE_READ_ACCESS=PASS
READ_SNAPSHOT_TRANSITION=PASS
REPEATED_CALL_IDENTITY=PASS
F2_R1_REGRESSION
FULL_TEST
READY_FOR_V5_F2_R1_1_REVIEW
```

STOP.

R1.1 过后不会再开新的 F2 修复线。这一项满足原任务书的 original-call capture 后，我就签 V5_F2_PASS，然后开放 fresh V6。
