# PhiAgent O7-E V5-F1-R1 Relevance RCA Task Book（Reviewer 原文存档）

> 存档说明：以下为 GPT-5.6 Sol 于 2026-09-07 给出的 V5_F1_RCA_PATCH_REQUIRED
> 审计结论 + R1 补充任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Verdict：V5_F1_RCA_PATCH_REQUIRED

这份 RCA **方向基本抓对了，但还不能正式关闭 root cause**。我确认 `READ_ORCHESTRATION_FAILURE` 是真实存在的 failure mode；我**不接受目前把它直接定为唯一 PRIMARY_ROOT_CAUSE**。

```
V5_MEASUREMENT_UNCHANGED=true
RCA_SCOPE_INTEGRITY=PASS
READ_ORCHESTRATION_FAILURE=CONFIRMED
QUERY_LOG_HARNESS_DEFECT=CONFIRMED
ENVIRONMENT_PROVIDER_BLOCKAGE=CONFIRMED
BIBLIOGRAPHY_GROUNDING_GUARD_GAP=CONFIRMED
PRIMARY_ROOT_CAUSE=NOT_YET_CLOSED
CORPUS_COVERAGE_GAP=UNRESOLVED
QUERY_FORMULATION_FAILURE=UNRESOLVED
RELEVANCE_RANKING_FAILURE=UNRESOLVED
V5_F1_RCA_REVIEW=PATCH_REQUIRED
PRODUCTION_REPAIR_AUTHORIZED=false
V6_AUTHORIZED=false
```

### 审计结果

| 项目 | Reviewer |
|---|---|
| cee81cf → bf0b9ff 仅 RCA/task docs | **PASS** |
| V5 production / canonical artifacts 未动 | **PASS** |
| 63 search → 5 READ | **PASS** |
| 六个 LO_REQUIRED：45 search → 0 READ | **PASS** |
| access_level 对模型可见 | **PASS** |
| LOCATE→READ 工具合同存在 | **PASS** |
| V5-03 ABSTRACT→READ→content evidence 对照链 | **PASS** |
| query logging harness 缺陷 | **CONFIRMED** |
| live provider 环境阻断 | **CONFIRMED** |
| V5-12 bibliography grounding guard gap | **CONFIRMED** |
| "118 条相关且可读文献" | **FAIL** |
| 据此排除 corpus/relevance/query 问题 | **FAIL** |
| READ_ORCHESTRATION_FAILURE 定为最终 primary root cause | **NOT YET** |

### blocker：118 的语义被放大了

RCA 实际统计的是六个 case 中：`ABSTRACT_AVAILABLE result occurrences = 118`。它**不是** `118 distinct relevant readable scholarly sources`。

同一个 source 会因不同 search 重复进入结果。例如 frozen V5-06 中相同的 `Kant on Autonomy and Moral Evil`、`Moral Personhood and Personal Identity` 等记录重复出现；同时候选里还有 `Spinoza's Substance Monism`、王阳明、孟子、模态本体论等对 moral luck 问题明显不直接相关的 ABSTRACT_AVAILABLE 条目。

因此当前链条「118 ABSTRACT_AVAILABLE → 118 relevant readable → corpus gap 不成立」中间第二个箭头**没有证据**。

而这不是小措辞问题，它决定 root cause。本地 registry 的搜索本身采用 **OR semantics**：多词 query 被拆成 `term1 OR term2 OR ...`，再按 BM25 排序。也就是说，"搜索有命中"绝不等于"语义上覆盖该 scholarly controversy"。production 又是 local results 先进入列表，然后与 live results 合并并按 limit 截断；它并没有按 `access_level` 或 scholarly relevance 二次排序。

所以：`registry_topic_coverage > 0` **不能推出** `CORPUS_COVERAGE_GAP=false`。这是本轮唯一真正阻止 RCA PASS 的核心问题。

### READ orchestration 本身确实坏了

这一点我接受。（harness args 缺陷、access_level 可见性、工具说明等论证完全成立。）

因此六个 literature-required case **45 次 search 后一次 READ 都没有**，本身足够确认：`READ_ORCHESTRATION_FAILURE=CONFIRMED`。只是还不足以确认 `READ_ORCHESTRATION_FAILURE=THE_PRIMARY_ROOT_CAUSE`——因为如果模型看到的可读结果多数离题，那么"即使 READ 了也救不了回答"。

### 另外两个修正

`CONTENT_DEPTH_CEILING` 成立，而且比 RCA 表述还清楚：冻结 corpus manifest 是 316 records、282 accepted，但只有 **31 abstract evidence、0 passage、0 fulltext-read record**。所以 offline scholarly corpus 确实是严重的 abstract-level ceiling。

V5-12 的 `EVIDENCE_PROMOTION_FAILURE` 则不应该保留。它根本没有 scholarly READ，因此不存在"读到内容但没有 promotion"的证据。这里应该单列：`BIBLIOGRAPHY_GROUNDING_GUARD_GAP=CONFIRMED EVIDENCE_PROMOTION_FAILURE=NOT_DEMONSTRATED`。V5-12 确实输出了 Mackie / Parfit / Enoch 的精确书目信息，同时对应 claim 的 `evidence_ids=[]`、`direct_evidence=false`。这才是该问题准确的性质。

---

## R1 补充任务书

**MODEL:** GLM-5.3　**BASE:** `bf0b9ff54621d5b54321e503c53a2fb67ade03ba`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

目标：修正 V5-F1 对"可读记录=相关记录"的过度归因，最终关闭 root cause。**仍只做 RCA，禁止 production patch。**

### 1. 冻结范围

禁止 V5 rerun/rejudge、禁止修改 V5 canonical artifacts、production、judge/rubric/threshold。

仅新增：`docs/evidence/V5_F1_R1_RELEVANCE_RCA.json`。原 V5-F1 RCA 保留历史，不覆盖。

### 2. 六个 LO_REQUIRED case 去重 + relevance audit

仅使用 frozen `V5_FINAL_HOLDOUT_RUN.json` 中 **V5 当时实际返回**的 records。

对 V5-05/06/09/10/11/12，按 `source_record_id` 去重；每条记录保存：

```
case_id
source_record_id
appearance_count
title
access_level
relevance = DIRECT | SUPPORTING | IRRELEVANT | UNCERTAIN
relevance_reason
was_read
content_evidence
```

不得把 post-run diagnostic search 新发现的记录算作"V5 当时可用"。

分别报告：

```
RESULT_OCCURRENCES
UNIQUE_RECORDS
READABLE_OCCURRENCES
UNIQUE_READABLE_RECORDS
RELEVANT_UNIQUE_RECORDS
RELEVANT_READABLE_UNIQUE_RECORDS
RELEVANT_READABLE_BUT_UNREAD
```

### 3. Root-cause 纪律

`"118"` 只能称 `READABLE_RESULT_OCCURRENCES`，不得称"118 条相关可读文献"。

逐 case 判断：
- 存在相关且 `ABSTRACT_AVAILABLE+`、但模型未 READ → `READ_ORCHESTRATION_FAILURE=CONFIRMED`
- 无相关 record → 可判 discovery/corpus coverage 问题
- 有相关 record 但全 METADATA_ONLY → `CONTENT_COVERAGE_GAP`
- query args 已丢失 → `QUERY_FORMULATION_FAILURE=UNRESOLVED`，不得排除
- 无真实 per-search ranking 证据 → `RELEVANCE_RANKING_FAILURE=UNRESOLVED`

不得用"FTS 非零命中"单独证明 `CORPUS_COVERAGE_GAP=false`。

最终重新给：

```
PRIMARY_ROOT_CAUSE
PRIMARY_ROOT_CAUSE_CONFIDENCE
SECONDARY_ROOT_CAUSES
```

允许最终 primary 仍是 READ_ORCHESTRATION，但必须由**相关且可读、实际未读**的记录证明。

### 4. V5-12 taxonomy

保留：`BIBLIOGRAPHY_GROUNDING_GUARD_GAP=CONFIRMED`

除非能证明"已 READ 内容但未进入 evidence"，否则：`EVIDENCE_PROMOTION_FAILURE=NOT_DEMONSTRATED`

### 5. Provider blockage

区分 `V5_RUN_OBSERVED_PROVIDER_FAILURE` 与 `POST_RUN_DETERMINISTIC_PROVIDER_PROBE`。不得把 post-run probe 冒充原 run 的完整网络 trace。

### Exit

不得实施任何 repair。最终只输出：`READY_FOR_V5_F1_R1_RCA_REVIEW` STOP.

R1 只需要把这一个归因漏洞补严。**如果相关性去重后仍能证明多个失败 case 明明拿到了直接相关的 ABSTRACT，却 0 READ，我就会正式关闭 RCA，并进入 V5-F2 production repair；如果发现真正相关的可读内容其实很少，则 repair 必须同时处理 corpus/relevance，而不能只给模型加一个"记得 READ"的 prompt。**
