# PhiAgent O7-E V5-F1 Scholarly Content RCA Task Book（Reviewer 原文存档）

> 存档说明：以下为 GPT-5.6 Sol 于 2026-09-07 在 ChatGPT 会话「检索恢复任务书」中给出的
> V5 终审结论（V5_SCHOLARLY_GATE_NOT_MET）+ V5-F1 定位型 RCA 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Final Verdict：V5_SCHOLARLY_GATE_NOT_MET

我完成了独立审计。**V5 measurement 有效，V5 已正式消费，但 O7-E scholarly qualification 失败。**

```
V5_MEASUREMENT_VALID=true
V5_CONSUMED=true
DELIVERY_GATE=PASS
SCHOLARLY_GATE=FAIL
O7-E_FINAL_PASS=false
V5_FINAL_VERDICT=V5_SCHOLARLY_GATE_NOT_MET
V5_RERUN=NOT_AUTHORIZED
V5_REJUDGE=NOT_AUTHORIZED
V6_AUTHORIZED=false
```

### 1. Qualification 本身有效，没有 measurement 污染

V5 holdout 明确记录了全部 no-reuse 条件，并覆盖 12 个新 case；lock 中的 manifest hash 为 `6bd9febd...540c4`，12 cases，且明确 `frozen_before_run=true`。

我独立比较了 `34657e6e → cee81cf4` 期间只有 V5 manifest、lock、run、judge、summary、final-gate 和 task artifacts，没有 production/runtime/retrieval/judge implementation 改动。因此没有"看完 V5 再偷偷调系统"的问题。

Canonical judge 也是完整的：12 expected / 12 valid / 0 missing / `EVALUATION_INVALID=false`。所以这不是 judge 缺失或 evaluation invalid 导致的假 FAIL。

**`V5_MEASUREMENT_VALID=true` 可以正式确认。**

### 2. Canonical FAIL 比回执里的缩写更具体

最终 canonical failed gates 是：

```
APPLICABLE_DIMENSION_MEAN
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN_MIN
HISTORICAL_DISCIPLINE_REQUIRED_MEAN_MIN
INTERPRETIVE_PLURALITY_REQUIRED_MEAN_MIN
LITERATURE_ORIENTATION_REQUIRED_MEAN_MIN
REQUIRED_DIMENSION_MEDIAN_LT_2
FABRICATED_BIBLIOGRAPHY
```

对应：

```
applicable_mean = 2.712                        FAIL
textual_grounding = 3.750                      PASS
argument_reconstruction = 2.667                FAIL
historical_discipline = 3.286                  FAIL
interpretive_plurality = 1.571                 FAIL
literature_orientation = 1.500                 FAIL
REQUIRED_DIMENSION_MEDIAN_LT_2 = 12
FABRICATED_BIBLIOGRAPHY = 1
```

Frozen final gate 因此正确给出：`DELIVERY_GATE=PASS / SCHOLARLY_GATE=FAIL / FINAL_V5_VERDICT=SCHOLARLY_GATE_NOT_MET`。

这不是 V4 那种只剩一个 tail gate 的情况。**V5 是多维、宽幅 scholarly failure。**

### 3. 系统性问题已经确认：不是"不搜索"，而是"搜索无法变成内容证据"

这是这轮最有价值的结论。

Canonical run：
- 12/12 case 都调用 scholarly search
- `SCHOLARLY_SEARCH_CALLS=63`
- 只有 3 个 case 进入 scholarly READ、仅 1 个 case 得到 content evidence
- manifest 中 **6 个 `LITERATURE_ORIENTATION=REQUIRED` case（05/06/09/10/11/12）全部是 `content_ev=0`**

```
EVIDENCE_PIPELINE_FAILURE=CONFIRMED
PATTERN: SEARCH_HIGH → READ_LOW → CONTENT_EVIDENCE_NEAR_ZERO
         → MEMORY_BASED_ANSWER → LOW_LO/IP/AR
```

但我**暂时不会把更底层根因直接定为 `CORPUS_COVERAGE_GAP` 或 `READ_ORCHESTRATION_FAILURE`**。因为现在还没逐 search-call 区分：
- 搜索结果本身是否相关；
- 相关结果是否只有 metadata；
- 有可读结果但模型没有 READ；
- READ 发生后是否被 evidence contract 丢掉；
- query formulation 是否持续跑偏。

也就是说，**系统层故障已确认，底层故障位置还需一次 RCA。**

### 4. V5-12 的 fatal：canonical 成立，但需要精确定义

V5-12 三个 judge vote 中，只有 **1 个 vote** 标记了 `FABRICATED_BIBLIOGRAPHY=true`；另外两个认为，因为回答明确声明这些是"未经本次核验的记忆性线索"，所以不应算 fatal。Canonical aggregation 最终仍记录：

```
fatal = [FABRICATED_BIBLIOGRAPHY]
fatal_vote_counts: FABRICATED_BIBLIOGRAPHY = 1
```

触发 fatal 的那个 vote 指向的是：
- `J. L. Mackie, Ethics: Inventing Right and Wrong, 1977`
- `Derek Parfit, On What Matters, Vol. 2 (OUP, 2011)`
- `David Enoch, Taking Morality Seriously ... (OUP, 2011)`

其理由并不是"这些现实世界书目一定是假的"，而是：**当前 evidence records 根本没有支持这些精确的年份、卷次、出版社信息，却仍然输出了这些具体 bibliographic metadata。**

因此更准确的 RCA 是：

```
REAL_WORLD_BIBLIOGRAPHY_FALSEHOOD = NOT_ESTABLISHED
EVIDENCE_UNGROUNDED_BIBLIOGRAPHIC_SPECIFICITY = CONFIRMED
CANONICAL_FATAL = CONFIRMED
```

而且无需重判：**即使把这个唯一 fatal 完全拿掉，V5 仍然同时失败于 6 个其他 scholarly gates。** 所以 V5 FAIL 对这个 1/3 vote 的争议是**鲁棒的**，没有任何重新 judge 的理由。

### 5. 一个非阻塞归档小问题：不要修 V5

`V5_FINAL_GATE.json` 的 `label_mapping_note` 还说 frozen checker 会输出 `V3_...`，然后再去前缀。但实际 qualification base 上的 checker 早已经是版本中性的：`DELIVERY_GATE_NOT_MET / SCHOLARLY_GATE_NOT_MET`。

这是**历史说明文字过期**，不影响任何 gate 或 measurement。我的处理是：

```
NON_BLOCKING_ARCHIVE_NOTE_DEFECT=true
ACTION=DO_NOT_EDIT_CONSUMED_V5_ARTIFACTS
```

不值得为了改一句注释污染已经消费的 V5。

---

## 下一步：暂不授权 V6 —— V5-F1 定位型 RCA

现在直接做 V6 没意义——六个真正要求文献内容的 case 是 **6/6 content-evidence failure**，换一套新 holdout 很可能只是再消耗一次 qualification。

下一步只做一次**定位型 RCA**，不先拍脑袋改 production。

**MODEL:** GLM-5.3　**BASE:** `cee81cf46513937e864c9da430068ad712a32605`　**PRODUCTION_MODEL:** deepseek-v4-flash　**REVIEWER:** GPT-5.6 Sol

目标：定位 V5 已确认的 `SEARCH_HIGH → READ_LOW → CONTENT_EVIDENCE_NEAR_ZERO` 故障链。**本任务只做 RCA，不修改 production。**

V5 已永久消费。禁止：
- V5 agent rerun
- V5 judge rerun/rejudge
- 修改 V5 artifacts
- 修改 judge/rubric/threshold/final-gate
- 修改 primary retrieval / Local Patch / validator / quote_bound
- production patch

使用已消费的 `V5-05/06/09/10/11/12` 作为 dev trace。

对 V5 中全部 scholarly calls 建立逐调用审计表：

```
case_id → query → returned records → relevance → source_record_id
→ access_level → content availability → 是否 READ → READ result
→ 是否形成 content_evidence
```

对六个 secondary-required case 分别分类，允许多标签：

```
QUERY_FORMULATION_FAILURE
RELEVANCE_RANKING_FAILURE
CORPUS_COVERAGE_GAP
CONTENT_AVAILABILITY_GAP
ACCESS_DEPTH_GAP
READ_ORCHESTRATION_FAILURE
EVIDENCE_PROMOTION_FAILURE
MODEL_TOOL_USE_FAILURE
```

必须回答：
- 为什么 63 次 search 只产生 5 次 READ？
- 六个 LO_REQUIRED case 为什么全部 content_ev=0？
- 搜索结果中是否实际存在"相关且可 READ"的记录却未读取？
- 若没有，可读内容缺失发生在 registry/corpus、provider access 还是 query/ranking？
- V5-12 的三个具体书目条目是否来自任何 retrieved record；若否，确认 bibliography grounding guard gap。
- `search_scholarship → get_scholarly_source` 的现有 LOCATE→READ contract 是否被模型遵循、无法触发，还是工具没有提供足够候选信号。

允许：
- 离线分析 V5 frozen trace
- 对 consumed query 做 deterministic tool-level diagnostic probe
- READ 已存在的 scholarly records

禁止生成新的 V5 answer 或 judge。

产物：`docs/evidence/V5_F1_SCHOLARLY_CONTENT_RCA.json`

至少包含：
```
V5_MEASUREMENT_UNCHANGED=true
SECONDARY_REQUIRED_CASES=6
SECONDARY_CONTENT_EVIDENCE_CASES=0
每 case 的 failure classification
每个 search→read 决策链
V5-12 bibliography provenance audit
PRIMARY_ROOT_CAUSE
SECONDARY_ROOT_CAUSES[]
REPAIR_SURFACE_RECOMMENDATION[]
```

只有证据能区分时才宣布 root cause；不得把未知项猜成 corpus gap。

不得实施 repair。

最终状态只能：`READY_FOR_V5_F1_RCA_REVIEW`

STOP.

**当前正式里程碑：**

```
V3    = CONSUMED / SCHOLARLY FAIL
V4    = CONSUMED / SCHOLARLY FAIL
V4-F1 = PASS / CLOSED
V5    = CONSUMED / SCHOLARLY FAIL
V5-F1 = RCA AUTHORIZED
V6    = NOT YET AUTHORIZED
```

这次 V5 很有价值：它已经把问题从"某一本书没进 primary corpus"明确收缩成了 **scholarly secondary-content acquisition 整条链的问题**。下一轮 RCA 回执回来后，我会直接决定具体 repair surface，而不是再让 Builder 盲修。
