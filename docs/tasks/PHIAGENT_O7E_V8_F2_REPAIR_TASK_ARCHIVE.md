# PhiAgent O7-E V8-F2 Production Failure-Class Repair 任务书（Reviewer 原文存档）

> 存档说明：GPT-5.6 Sol 于 2026-09-11 在会话 chatgpt.com/c/6aa3e455-ae50-83ee-a4af-359574391bb7 随 V8_F1_REVIEW=PASS 一并签发。

---

## Reviewer Verdict（V8-F1）

```
V8_F1_REVIEW=PASS
V8_F1_PASS=true
V8_F1_CLOSED=true
REVIEWED_BASE=d64ac0a504a87900b34800f0e8accaa21cbee223
REVIEWED_HEAD=43056684b6e1f3b50bbd44e2d73320ad0645e4d2
V8_FAILURE_EVIDENCE_PRESERVED=true
V8_RERUN=false
PRODUCTION_CHANGED=false
V8_MEASUREMENT_VALID=true
HARNESS_PROCEDURAL_DEVIATION=true
SCORING_SEMANTICS_CHANGED=false
V8_11_FATAL_ROOT_CAUSE=UNSUPPORTED_MODEL_ATTRIBUTION
V8_11_JUDGE_FALSE_POSITIVE=false
V8_12_LOW_SCORE_ROOT_CAUSE=MIXED
V8_12_PRIMARY_CAUSE=CORPUS_COVERAGE
V8_12_SECONDARY_CAUSE=RETRIEVAL_FAILURE
DIMENSION_FAILURE_CONCENTRATION=CONCENTRATED
V8_10_PERSISTENCE_ROOT_CAUSE=NO_OP_REPAIR(MODEL_NONCOMPLIANCE)+SOURCE_GAP
V8_F2_AUTHORIZED=true
V9_AUTHORIZED=false
O7_E_COMPLETE=false
```

我独立复核后，V8-F1 可以正式关闭。V8-11：最终发布的是只有 282 字符的操作性前言，该轮 scholarly search/fetch/records/citations 全为 0，却包含具体学者归因；judge fatal 不是误判。真正暴露的是两个相连的问题：**Main Agent 把「接下来要检索」当成了终局答案，以及 validator 没有阻止这种 plan-only terminal candidate**。V8-12 支持 MIXED 判定（核心原典不可用 + 10 次 search/66 条记录 0 次相关 fetch），模型反而诚实暴露证据不足，非证据伪装、非 judge 误判。最关键：failure concentration 机械成立（excl 两案例后 required means arg=4.0/textual=3.75/interp=3.0/hist=3.875/lit=3.25，applicable mean=3.622 全达标；6 个 median<2 全集中于两 case）→ **少数明确失败模式破坏总体 gate，不是 11 case 普遍学术退化**。绝不意味着可删除 case 或重算 V8；V8 永久 FAIL。V8-10 根因名称收紧为 `NO_OP_REPAIR(MODEL_NONCOMPLIANCE)+SOURCE_GAP`——工程上真正需要生产代码保证的是：**validator 仍有问题时，repair 返回逐字节相同候选不能再被当作一次正常修复继续浪费轮次**。Judge harness 程序性问题解释闭合（HARNESS_PROCEDURAL_DEVIATION=true 与 V8_MEASUREMENT_VALID=true 同时成立）。d64ac0a→43056684 恰 1 提交仅 3 个文档/evidence 文件，无 production diff。

现在不需要 measurement patch，也不需要再调查。直接修三种已被证明的 production failure class；**不允许碰 V8，不允许提前跑 V9**。

---

## V8-F2 任务书

**MODEL：** GLM-5.3　**Reviewer：** GPT-5.6 Sol

**BASE：** `43056684b6e1f3b50bbd44e2d73320ad0645e4d2`

只修 V8-F1 已证明的三个 production failure class：

```
A. plan-only terminal publication
B. scholarly retrieval coverage/fallback failure
C. no-op repair under source gap
```

禁止重跑 V8。V8-01~12 永久 consumed。

### 修复规则

**1. Plan-only terminal**

修真实 Main Agent / production orchestration，不得只修 qualification harness。

合同：

```
想检索 → 本轮实际 tool call 不调用 tool → 必须给用户实质回答
禁止: "下一步我会检索……" 然后直接作为 final answer 发布
```

V8-11 类输入下：

- 不得发布纯操作计划前言；
- 不得在 0 scholarly evidence 时把具体 scholar attribution 当已支持事实；
- 可做**一次有界 continuation/recovery**；
- 若仍无法取得证据，输出实质性的受限回答并明确证据边界，而不是工具计划。

保持 Main Agent sovereignty。禁止新增第二个 LLM judge、通用「答案质量分类器」或大规模规则 shadow Agent。

同时加回归：如果用户**真的要求「给我研究计划」**，正常计划回答不能被误拦。

**2. Scholarly retrieval fallback**

针对 corpus 缺口 + provider failure + irrelevant-only retrieval：

```
author/work/concept query
↓ provider search
↓ 相关性不足 / provider error
↓ 一次有界 query reformulation / provider fallback
↓ 取得 relevant source_record
↓ 需要内容归因时必须 fetch content evidence
```

要求：

- generic，不得硬编码 Arendt/V8-12；
- 支持作者名、作品名、核心概念的合理别名/中英查询重构；
- 单 provider 失败不得直接使整个 scholarly path 失效；
- 「返回很多 records」不得等价于「检索成功」；
- 只有相关记录才进入后续证据链；
- 需要引用/归因二手文献内容时，metadata-only 不得冒充 content evidence；
- 保持硬预算，禁止无限 search loop。

**Primary corpus 继续冻结。** 允许修 scholarly query/failover/relevance plumbing；允许增加合法 metadata/alias。禁止加入受版权保护的阿伦特等全文、绕 paywall 或针对 V8 case 的特判。

**3. No-op repair**

在真实 production repair owner 增加：

```
pre_repair_candidate_hash
post_repair_candidate_hash
```

若：

```
hash unchanged AND validator issues remain
```

则：

```
NO_OP_REPAIR=true
```

不得把相同候选再盲跑下一轮。下一步必须有界升级：

- 明确针对仍存 issue；
- 无 evidence 的 exact quote → 删除引号/安全转述；
- 无法验证的 citation/attribution → 删除、降级或取得证据；
- source gap → 明确限制，但保留可支持的哲学论证；
- 不得通过放宽 validator 来「修绿」。

建议保留机械 telemetry：

```
PLAN_ONLY_TERMINAL_BLOCKED
SCHOLARLY_QUERY_REFORMULATION_COUNT
SCHOLARLY_PROVIDER_FAILOVER_COUNT
SCHOLARLY_IRRELEVANT_ONLY_RETRY_COUNT
REPAIR_NO_OP_COUNT
REPAIR_NO_OP_ESCALATED
```

不要让这些 telemetry 变成新的决策系统。

### 重要边界

本任务允许定点修改：

```
Main Agent production orchestration
scholarly retrieval query/fallback plumbing
production repair flow
对应 tests
```

冻结：

```
V3–V8 全部历史 evidence/verdict
V8 12 cases
primary corpus
O7A scholarly judge contract
judge rubric / prompt / thresholds / vote semantics
o7e_final_gate
semantic transition classifier semantics
validator / quote_bound 的严格性
production model = deepseek-v4-flash
```

禁止通过 lowering threshold、删除 case、放宽 validator、硬编码 V8-11/12/10 来通过。

### 测试

使用**全新 DEV-only synthetic cases**，不得复用 V8，也不得预消费未来 V9 manifest。

- **plan-only**：首次模型输出为「准备检索」的非答案；断言该文本不会公开发布；recovery 后实际 tool call 或产生实质受限答案。
- **real research-plan request**：用户明确要求研究计划；断言计划型答案可正常发布，防止 guard 误杀。
- **provider failover**：provider A error；provider B 返回 relevant records；content-required 场景必须发生 source fetch。
- **irrelevant-only**：首轮 records 全离题；触发一次 bounded reformulation；不得把 record count 当 evidence quality。
- **no-op repair**：repair 第一次返回相同 candidate；`NO_OP_REPAIR=true`；不得无差别重复；escalation 后候选发生变化或 fail-closed；validator issue 必须减少/消失，且不得制造新的 semantic issue。

全部相关 targeted tests + full backend pytest。

DEV probe 可使用 `deepseek-v4-flash` production path，但：

```
QUALIFICATION=false  FORBIDDEN_FROM_V9=true
```

### 发布

拓扑保持：

```
BASE
↓
CONTENT_HEAD   implementation + tests
↓
ARCHIVE_HEAD   evidence/docs only
```

Full pytest 必须跑在 **exact CONTENT_HEAD**。不得在 ARCHIVE_HEAD 再改代码。

### 最终回执

```
BASE_SHA=  CONTENT_HEAD=  ARCHIVE_HEAD=  REMOTE_SHA=
PLAN_ONLY_TERMINAL_FIXED=true/false
REAL_PLAN_REQUEST_NOT_BLOCKED=true/false
SCHOLARLY_QUERY_REFORMULATION=true/false
SCHOLARLY_PROVIDER_FAILOVER=true/false
IRRELEVANT_RECORDS_NOT_TREATED_AS_SUCCESS=true/false
CONTENT_ATTRIBUTION_REQUIRES_FETCH=true/false
NO_OP_REPAIR_DETECTED=true/false
NO_OP_REPAIR_ESCALATED=true/false
SOURCE_GAP_SAFE_DEGRADATION=true/false
DEV_CASES_FRESH=true/false
V8_CASES_REUSED=false
V8_RERUN=false
V8_VERDICT_UNCHANGED=true
V7_VERDICT_UNCHANGED=true
JUDGE_CHANGED=false
FINAL_GATE_CHANGED=false
VALIDATOR_SEMANTICS_LOOSENED=false
PRIMARY_CORPUS_CHANGED=false
PRODUCTION_MODEL=deepseek-v4-flash
DEV_PROBE_RESULT=
FULL_TEST_SHA=
FULL_TEST_RESULT=
ARCHIVE_PARENT_EQUALS_CONTENT_HEAD=true/false
READY_FOR_V8_F2_REVIEW=true
STOP
```

V8-F2 通过我的独立 review 后，才授权 **V9 fresh formal qualification**。V9 会使用又一批完全未消费 case；如果届时 scholarly、delivery、semantic accounting、final gate 全绿，就应进入 **O7-E closeout**，而不是继续无目的地造新 patch。
