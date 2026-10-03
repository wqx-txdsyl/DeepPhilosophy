# PhiAgent O7-E V5 Fresh Scholarly Qualification Task Book（Reviewer 原文存档）

> 存档说明：以下为 GPT-5.6 Sol 于 2026-09-07 在 ChatGPT 会话「检索恢复任务书」中给出的
> V4_F1_PASS 终审结论 + V5 Fresh Scholarly Qualification 任务书，逐字存档。
> 会话 URL: https://chatgpt.com/c/6aa2519d-8d94-83ea-b219-feef7e566b43

---

## Reviewer Final Verdict: V4_F1_PASS

本轮我签 **PASS**。V4-F1 repair line 正式关闭。

| Gate | 结论 |
|---|---|
| BASE → CONTENT topology | **PASS** |
| CONTENT → ARCHIVE evidence-only | **PASS** |
| Generic primary lexical repair | **PASS** |
| EN primary retrieval | **PASS** |
| CN primary retrieval | **PASS** |
| Latin primary retrieval | **PASS** |
| search_books → get_chapter real regression | **PASS** |
| q48/q49/q93/q94/q95 read | **PASS** |
| Primary-body purity | **PASS** |
| RP3 curation-script cleanup | **PASS** |
| V4 holdout drift | **PASS / false** |
| V4 run/judge drift | **PASS / false** |
| Final-gate/judge/threshold freeze | **PASS** |
| Evidence consistency | **PASS** |
| V4-F1 FINAL | **PASS** |

关键实现已经真正落库：production lexical search 通用读取 `tags`、大小写统一，并允许书级 metadata 命中后进入章节结果，没有 Aquinas/V4-03 特判。

新的 regression 也确实走真实 `TOOLS["search_books"] → TOOLS["get_chapter"]`，覆盖两条 EN、两条 CN、四条 Latin queries，并真实读取 q48/q49/q93/q94/q95；唯一 monkeypatch 是任务书明确允许的关闭外部 embedding，搜索结果、book ID 和章节内容没有被 mock。

冻结基线前移发生在单独的 `ec01f517d` test commit 中，对应这次已经授权的 retrieval change；没有把 final-gate、judge、validator 等额外生产修改混进去。

两阶段证据模型也成立：`53bcbf72d → 98c8972a6 → ec01f517d → 34657e6e`。其中 `34657e6e` 的直接 parent 是 `ec01f517d`，且 archive commit 只修改 `V4_F1_PRIMARY_CORPUS_COVERAGE.json`。Evidence 已记录 8/8 retrieval、五章 READ、V4 零漂移以及 `826 passed / 0 failed / 0 skipped`。

因此正式状态为：

```
V4_F1_PASS=true
V4_F1_CLOSED=true
V4_HISTORICAL_SCHOLARLY_RESULT=V4_SCHOLARLY_GATE_NOT_MET
V4_RERUN=NOT_AUTHORIZED
V4_REJUDGE=NOT_AUTHORIZED
V5_AUTHORIZED=true
V5_QUALIFICATION_BASE=34657e6ed66fc789e3932e42162ec07c0345c8c5
```

注意：**V4-F1 PASS 不会改写 V4 的历史 FAIL**。它意味着导致 V4 尾部失败的 corpus/retrieval repair 已经完成，现在可以用全新未消费样本进行 V5 qualification。

---

## V5 Fresh Scholarly Qualification 任务书

**MODEL:** GLM-5.3　**PRODUCTION_MODEL:** deepseek-v4-flash　**QUALIFICATION_BASE:** `34657e6ed66fc789e3932e42162ec07c0345c8c5`　**REVIEWER:** GPT-5.6 Sol

### 目标

执行一次全新的 O7-E scholarly qualification。

V3、V4 均已消费，永久保持历史结果。V5 必须是新的 qualification run，不得重跑、重判或修补旧 holdout。

### §1 Freeze

从 `QUALIFICATION_BASE` 开始冻结 production。

禁止修改：
- production agent/runtime
- primary retrieval
- scholarly retrieval / LOCATE→READ
- corpus / registry / aliases
- Local Patch
- validator / final_validator
- quote_bound
- repair_context
- scholarly judge
- rubric
- thresholds
- final-gate logic

本阶段只允许：
- V5 fresh holdout manifest
- V5 lock
- qualification harness 所需的非语义 observability
- V5 run artifacts
- V5 judge artifacts
- V5 mechanical/final summary

若 V5 失败，V5 即永久消费；不得依据结果修改后重新运行 V5。

### §2 Fresh Holdout

建立全新、未消费的 12-case V5 holdout。

必须在任何 V5 production run 之前完成 manifest freeze + SHA256 lock。

硬约束：

```
NO_V3_CASE_REUSE=true
NO_V4_CASE_REUSE=true
NO_V4_03_REUSE=true
NO_V4_03_NEAR_PARAPHRASE=true
NO_R25_REUSE=true
NO_RP3_DEV_PROBE_REUSE=true
CASE_CONTENT_UNSEEN_BEFORE_FREEZE=true
```

不得仅改写旧问题措辞形成"新 case"。

覆盖至少：
- Western classical
- Western medieval
- Western modern
- Western contemporary
- Chinese philosophy
- ≥1 other non-Western tradition
- primary-text interpretation
- concept distinction
- philosopher comparison
- interpretive controversy
- secondary-scholarship controversy
- secondary-source content-evidence case

至少若干 case 必须实际需要 scholarly secondary evidence，而不是全部可仅靠 primary text 完成。

### §3 Frozen Run

冻结 manifest 后，仅运行 `deepseek-v4-flash`。

每个 case 保存完整：
- prompt
- final answer
- complete tool trace
- tool call IDs
- tool names
- tool arguments
- `search_books`
- `get_chapter`
- `search_scholarship`
- `get_scholarly_source`
- selected scholarly record IDs
- evidence levels
- content availability
- repair trace
- validator result
- final publication result

禁止剥离 query/tool args。

Scholarship 使用必须保持：`LOCATE → relevance check → READ/FETCH → content evidence`。

若内容不可获得，必须安全降级并明确披露；不得把 metadata 当作已读内容。

### §4 Mechanical Summary

至少报告：

```
PUBLISHED_COUNT
REPAIR_TRIGGERED
REPAIR_CONVERGED
REPAIR_CONVERGENCE
REPAIR_CREATES_NEW_FATAL_ERROR
TERMINAL_PENDING
TOOL_LOOP_ABORTS
VALIDATOR_FATAL_COUNTS
UNVERIFIED_PUBLIC_EXACT_QUOTES
STITCHED_PUBLIC_QUOTES
PUBLIC_INVALID_CITATIONS
SCHOLARLY_SEARCH_CASES
SCHOLARLY_SEARCH_CALLS
SCHOLARLY_READ_CASES
SCHOLARLY_READ_CALLS
CONTENT_EVIDENCE_CASE_COUNT
SAFE_FALLBACK_CASE_COUNT
```

Local Patch frozen mechanical metrics 继续报告。

### §5 Canonical Scholarly Judge

只运行一次 frozen canonical judge。

使用与 V4 完全相同的 rubric / thresholds。

报告：

```
JUDGE_CASES_EXPECTED
JUDGE_CASES_VALID
JUDGE_CASES_MISSING
EVALUATION_INVALID
```

以及：

```
applicable_mean
textual_grounding
argument_reconstruction
interpretive_plurality
historical_discipline
literature_orientation
REQUIRED_DIMENSION_MEDIAN_LT_2
REQUIRED_DIMENSION_MISSING_SCORE
```

六类 fatal counts 全量报告。

禁止 Builder 修改 judge output。

### §6 Final Gate

使用当前冻结的 version-neutral final gate。

输出：

```
DELIVERY_GATE
SCHOLARLY_GATE
FAILED_GATES
FATAL_COUNTS
FINAL_V5_VERDICT
```

不得使用 V3/V4 verdict label。

Builder **不得自行宣布**：`O7_E_PASS` / `FINAL_PASS`。

即使所有机械 gate 为绿，也只能结束于：`READY_FOR_V5_SCHOLARLY_REVIEW`

### §7 Evidence

建议 canonical artifacts：

```
docs/evidence/V5_FRESH_HOLDOUT_MANIFEST.json
docs/evidence/V5_HOLDOUT_LOCK.json
docs/evidence/V5_FINAL_HOLDOUT_RUN.json
docs/evidence/V5_FINAL_HOLDOUT_SUMMARY.json
docs/evidence/V5_FINAL_HOLDOUT_JUDGE.json
docs/evidence/V5_FINAL_HOLDOUT_JUDGE_SUMMARY.json
docs/evidence/V5_FINAL_GATE.json
```

最终回执包含：

```
QUALIFICATION_BASE
MANIFEST_FREEZE_SHA
HEAD_SHA
REMOTE_SHA
NEW_AGENT_RUN=true
NEW_JUDGE_RUN=true
NO_V3_V4_REUSE=true
12-case coverage summary
mechanical metrics
judge metrics
fatal counts
final-gate output
full pytest result
READY_FOR_V5_SCHOLARLY_REVIEW
```

STOP.

**V5 从 `34657e6e` 正式授权。** 下一次你把 V5 回执给我，我直接做独立最终 scholarly review。
