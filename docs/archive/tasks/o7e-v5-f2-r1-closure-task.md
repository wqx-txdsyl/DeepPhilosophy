# PhiAgent O7-E V5-F2-R1 Closure Task Book（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-07 给出的 V5_F2_PATCH_REQUIRED 裁定 + R1 closure 任务书。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V5_F2_PATCH_REQUIRED

主体修复是成功的：corpus、retrieval relevance、LOCATE→READ、provider preflight 和 6 个 dev probes 都已经从 V5 的系统性失效状态拉起来了。但不能签 V5_F2_PASS，还有 2 个明确 acceptance blocker + 1 个 observability closure。

```
V5_F2_CORPUS_REPAIR=PASS
V5_F2_RETRIEVAL_RELEVANCE=PASS
V5_F2_LOCATE_READ=PASS
V5_F2_DEV_BEHAVIOR=PASS
V5_F2_PROVIDER_PREFLIGHT=PASS
BIBLIOGRAPHY_GROUNDING_GUARD=FAIL
SAFE_FALLBACK_BEHAVIORAL_GATE=NOT_TESTED
HARNESS_PER_CALL_PROVENANCE=PARTIAL
V5_F2_FINAL=PATCH_REQUIRED
V6_AUTHORIZED=false
```

### Blocker 1（P0）：bibliography guard 没有兑现任务书语义

当前代码 `if not pool: return issues` —— 恰恰在完全没有 scholarly evidence 时，精确书目可以直接绕过 guard。而 F2 gate 是「无证据时至少产生 UNGROUNDED_BIBLIOGRAPHIC_DETAIL」。

第二个更隐蔽的问题：grounded 判定只要求同年+上下文作者姓，就把整个 "Clarendon Press, 1977" 放行——record 根本没有 publisher 字段。pool 只保存 doi/year/authors，没用 bibliographic_verified_fields 做逐字段验证。这会重新留下 V5-12 同类型漏洞。

### Blocker 2：SAFE_FALLBACK acceptance 没有执行

Builder 自己写了「未在本次 probe 单独诱导」。F2 acceptance 明确要求 SAFE_FALLBACK correct when evidence unavailable。SAFE_FALLBACK_CONTRACT=PASS 但 SAFE_FALLBACK_BEHAVIORAL_PROOF=MISSING。

### Closure：harness 只修好了 args

每 300-char result 不构成 per-call provenance：search/read call 与其返回 records/evidence 的映射仍不完整。

---

## R1 Closure 任务书

**MODEL:** GLM-5.3　**BASE:** `c6974fbf3470871d737e9703c1a4db272d5ab904`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

目标：只关闭 F2 剩余三个 gate。禁止重做 corpus/retrieval；禁止 V5 rerun/rejudge；禁止 judge/rubric/threshold/final-gate 改动。

### P0 — Bibliography grounding guard

修正 UNGROUNDED_BIBLIOGRAPHIC_DETAIL：

- **无 scholarly record 不得自动 PASS。** 存在明确 scholarly bibliography 形式但无 retrieved record 支撑时必须 flag。
- 必须加入 V5-12 风格 regression：
  - `J. L. Mackie, Ethics: Inventing Right and Wrong, 1977`
  - `Parfit, On What Matters, Vol. 2 (OUP, 2011)`
  - `Enoch, Taking Morality Seriously (OUP, 2011)`
  - 无对应 retrieved verified fields → UNGROUNDED_BIBLIOGRAPHIC_DETAIL。
- **逐字段 grounding。** 检测到的精确字段必须分别匹配同一 retrieved scholarly record，并且该字段存在于 bibliographic_verified_fields：author / title / publication_year / DOI / publisher / volume / pages。
- 未被当前 scholarly provider/record 验证的字段，宁可要求 Agent 删除该细节，也不得借「作者+同年」放行。例如 retrieved record 只有 Mackie + title + 1977、没有 verified publisher：(Clarendon Press, 1977) → 必须 FAIL。
- 不得只因年份相同或作者姓出现就认为 publisher grounded。
- 避免把普通历史年份/正文年份误判成 bibliography；触发面保持 conservative，但上述明确书目形式必须覆盖。

### P1 — SAFE_FALLBACK behavioral proof

新增一个永久 dev-only nonce case，禁止进入 V6。使用真实 production agent path，目标设计为当前 scholarly corpus 中不存在的虚构 scholarly target，使实际检索无法取得 DIRECT relevant content evidence。

必须证明：

```
SEARCH_OCCURRED=true
DIRECT_RELEVANT_CONTENT_EVIDENCE=0
SAFE_FALLBACK_DISCLOSED=true
MEMORY_SCHOLAR_ATTRIBUTION_AS_VERIFIED=false
PRECISE_UNGROUNDED_BIBLIOGRAPHY=0
PUBLISHED=true
```

不得 mock search result 或 final answer。

### P1 — per-call scholarly trace

在 result_full 被剥离前建立安全、bounded、无 CoT 的 scholarly call trace。每次：

- search_scholarship 至少保存 tool_call_id / args / returned_source_record_ids / access_levels / retrieval_origins / provider_errors / offline_mode
- get_scholarly_source 至少保存 tool_call_id / args / source_record_id / access_before / access_after / returned_evidence_level / content_hash

qualification harness 将该结构写入 canonical run artifact。不得只保存 300-char result string；不得依赖 scholarly_cache.json。

### Closure

提交 production/tests：CONTENT_HEAD。运行 full backend tests，并重新跑现有六个 F2 dev probes 作 regression：6/6 published、≥5/6 content evidence、bibliography fatal/grounding issue=0。另跑 SAFE_FALLBACK nonce probe。

然后 evidence-only：ARCHIVE_HEAD.parent == CONTENT_HEAD。新增 docs/evidence/V5_F2_R1_CLOSURE.json，不得覆盖旧 F2 evidence。

最终只报告：

```
BASE_SHA
CONTENT_HEAD
ARCHIVE_HEAD
REMOTE_SHA
BIBLIOGRAPHY_GUARD=PASS
NO_TRACE_BIBLIOGRAPHY_BLOCKED=PASS
FIELD_LEVEL_GROUNDING=PASS
SAFE_FALLBACK_BEHAVIOR=PASS
PER_CALL_PROVENANCE=PASS
F2_DEV_REGRESSION
FULL_TEST
READY_FOR_V5_F2_R1_REVIEW
```

STOP.

当前状态：主体 scholarly pipeline 已经修起来了，R1 不再碰 corpus。只要这三个 closure gate 过，我就可以签 V5_F2_PASS，届时再正式开放 fresh V6。
