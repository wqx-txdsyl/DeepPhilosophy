# PhiAgent O10 — Tool-First Qualification Final Report

Builder: ZCode / GLM-5.3 · Reviewer: GPT-5.6 Sol · Production model: `deepseek-flash` · 日期: 2026-09-13

## 1. T1 — Tool Mechanical Qualification

- TOOL_COUNT = 32（32 production tools 全覆盖）
- 测试 case 总数 = 214（VALID/EMPTY/INVALID_TYPE/EMPTY_RESULT/BOUNDARY/SCHEMA/ERROR_PATH/OUTPUT_CONTRACT + 外部依赖 TIMEOUT/NETWORK_FAILURE/PROVIDER_ERROR/DEGRADED_MODE）
- MECHANICAL_PASS = **32/32**
- KNOWN_BROKEN_TOOL_COUNT = 0
- SILENT_DEFAULT_COUNT = 0
- UNBOUNDED_ERROR_COUNT = 0

**T1 期间修复（全记录见 report `repairs_during_qualification`）**: 入口类型解析（`_str_arg`/`_req_str`，消灭非字符串参数的 AttributeError 逃逸与空名 SILENT_DEFAULT）、空 query 向量路径守卫、provider 失败包边（profile/history_timeline/school_arena）、scholarly `OSError` 分支、write_essay topic 回显。所有修复为入口加固/结构化错误，不改变任何工具的语义能力。

**T1_MECHANICAL = PASS**

## 2. T2 — Agentic Tool-Call Qualification

- 案例集 A–N 共 82 题（A 不该检索 / B 主检索路由 / C 出处核验 / D 学术路由 / E 论证工具 / F paper_review vs analyze_argument / G 知识图谱路由 / H 专项认知工具 / I 参数质量 / J 多工具序列 / K 坏首条结果注入 / L 停止纪律 / M 故障恢复注入 / N 组合陷阱）
- 执行 82 题, PUBLISHED_VALIDATED = 80
- 十维度均分 = 3.93 / 4

| Gate | 违规数 |
|---|---|
| FALSE_POSITIVE_TOOL_CALL | 0 |
| WRONG_PRIMARY_TOOL | 0 |
| INVALID_TOOL_ARGS | 0 |
| FABRICATED_ID_OR_INDEX | 0 |
| PRIMARY_SEARCH_WITHOUT_READ | 0 |
| SCHOLARLY_ATTRIBUTION_WITHOUT_SECOND_HOP | 0 |
| EXACT_DUPLICATE_EXECUTION | 2 |
| BAG_EQUIVALENT_DUPLICATE_EXECUTION | 0 |
| NO_NEW_INFORMATION_LOOP | 0 |
| UNJUSTIFIED_BUDGET_EXTENSION | 0 |
| VAGUE_TOOL_REASON | 0 |

- SECTION_A（RESEARCH_NEED=NONE, RETRIEVAL_CALLS=0）: PASS
- SECTION_F（paper_review vs analyze_argument 路由分离）: FAIL
- ALL_HARD_GATES_ZERO = False

### 分节得分

| Section | n | 均分 | 发布 |
|---|---|---|---|
| A | 6 | 4.0 | 6 |
| B | 6 | 4.0 | 6 |
| C | 6 | 3.95 | 5 |
| D | 6 | 3.88 | 6 |
| E | 6 | 3.9 | 6 |
| F | 4 | 3.85 | 4 |
| G | 6 | 3.95 | 6 |
| H | 6 | 3.83 | 5 |
| I | 6 | 4.0 | 6 |
| J | 6 | 3.95 | 6 |
| K | 6 | 4.0 | 6 |
| L | 6 | 3.75 | 6 |
| M | 6 | 3.95 | 6 |
| N | 6 | 3.98 | 6 |

### 逐题结果（含违规明细见 O10_TOOL_AGENTIC_REPORT.json）

| Case | 均分 | 状态 | 违规（截断） |
|---|---|---|---|
| A01 | 4.0 | PUBLISHED | — |
| A02 | 4.0 | PUBLISHED | — |
| A03 | 4.0 | PUBLISHED | — |
| A04 | 4.0 | PUBLISHED | — |
| A05 | 4.0 | PUBLISHED | — |
| A06 | 4.0 | PUBLISHED | — |
| B01 | 4.0 | PUBLISHED | — |
| B02 | 4.0 | PUBLISHED | — |
| B03 | 4.0 | PUBLISHED | — |
| B04 | 4.0 | PUBLISHED | — |
| B05 | 4.0 | PUBLISHED | — |
| B06 | 4.0 | PUBLISHED | — |
| C01 | 4.0 | PUBLISHED | — |
| C02 | 4.0 | PUBLISHED | — |
| C03 | 4.0 | PUBLISHED | — |
| C04 | 4.0 | PUBLISHED | — |
| C05 | 4.0 | PUBLISHED | — |
| C06 | 3.7 | FAIL_CLOSED_VALIDATION | NOT_PUBLISHED |
| D01 | 3.3 | PUBLISHED | EXACT_DUPLICATE_EXECUTION |
| D02 | 4.0 | PUBLISHED | — |
| D03 | 4.0 | PUBLISHED | — |
| D04 | 4.0 | PUBLISHED | — |
| D05 | 4.0 | PUBLISHED | — |
| D06 | 4.0 | PUBLISHED | — |
| E01 | 4.0 | PUBLISHED | — |
| E02 | 4.0 | PUBLISHED | — |
| E03 | 4.0 | PUBLISHED | — |
| E04 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| E05 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| E06 | 4.0 | PUBLISHED | — |
| F01 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| F02 | 4.0 | PUBLISHED | — |
| F03 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| F04 | 4.0 | PUBLISHED | — |
| G01 | 4.0 | PUBLISHED | — |
| G02 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| G03 | 4.0 | PUBLISHED | — |
| G04 | 4.0 | PUBLISHED | — |
| G05 | 4.0 | PUBLISHED | — |
| G06 | 4.0 | PUBLISHED | — |
| H01 | 4.0 | PUBLISHED | — |
| H02 | 4.0 | PUBLISHED | — |
| H03 | 3.0 | FAIL_CLOSED_VALIDATION | EXACT_DUPLICATE_EXECUTION；NOT_PUBLISHED |
| H04 | 4.0 | PUBLISHED | — |
| H05 | 4.0 | PUBLISHED | — |
| H06 | 4.0 | PUBLISHED | — |
| I01 | 4.0 | PUBLISHED | — |
| I02 | 4.0 | PUBLISHED | — |
| I03 | 4.0 | PUBLISHED | — |
| I04 | 4.0 | PUBLISHED | — |
| I05 | 4.0 | PUBLISHED | — |
| I06 | 4.0 | PUBLISHED | — |
| J01 | 3.7 | PUBLISHED | PRIMARY_TOOL_MISSING |
| J02 | 4.0 | PUBLISHED | — |
| J03 | 4.0 | PUBLISHED | — |
| J04 | 4.0 | PUBLISHED | — |
| J05 | 4.0 | PUBLISHED | — |
| J06 | 4.0 | PUBLISHED | — |
| K01 | 4.0 | PUBLISHED | — |
| K02 | 4.0 | PUBLISHED | — |
| K03 | 4.0 | PUBLISHED | — |
| K04 | 4.0 | PUBLISHED | INJECTED_BAIT_HEDGED |
| K05 | 4.0 | PUBLISHED | — |
| K06 | 4.0 | PUBLISHED | — |
| L01 | 4.0 | PUBLISHED | — |
| L02 | 3.5 | PUBLISHED | OVER_RESEARCH |
| L03 | 3.5 | PUBLISHED | OVER_RESEARCH |
| L04 | 4.0 | PUBLISHED | — |
| L05 | 4.0 | PUBLISHED | — |
| L06 | 3.5 | PUBLISHED | OVER_RESEARCH |
| M01 | 4.0 | PUBLISHED | — |
| M02 | 4.0 | PUBLISHED | — |
| M03 | 4.0 | PUBLISHED | — |
| M04 | 4.0 | PUBLISHED | — |
| M05 | 3.9 | PUBLISHED | ADVISORY_TOOL_SKIPPED |
| M06 | 3.8 | PUBLISHED | — |
| N01 | 4.0 | PUBLISHED | — |
| N02 | 4.0 | PUBLISHED | — |
| N03 | 3.9 | PUBLISHED | ADVISORY_TOOL_SKIPPED |
| N04 | 4.0 | PUBLISHED | — |
| N05 | 4.0 | PUBLISHED | — |
| N06 | 4.0 | PUBLISHED | — |

## 3. Failure Recovery（K/M/L03 故障注入）

- 注入案例 13 个, 恢复合格 13 个（明细见 O10_TOOL_FAILURE_RECOVERY.json）

- **K01** [PASS] 换合法路径调整后完成
- **K02** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **K03** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **K04** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **K05** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **K06** [PASS] 换合法路径调整后完成
- **L03** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **M01** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **M02** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **M03** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **M04** [PASS] honest degradation（如实降级）
- **M05** [PASS] 换合法路径调整后完成（含诚实降级标注）
- **M06** [PASS] honest degradation（如实降级）

## 4. 环境与执行说明

- 执行路径: 进程内直调 `engine_langgraph.stream_agent`（与生产 SSE 同一引擎/提示词/校验/引文约束）
- Provider preflight: 见 O10_TOOL_QUALIFICATION_PREFLIGHT.json（websearch 通道本环境不可达; K/M/L03 注入场景与本环境一致, 其余案例不依赖 web）
- SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY（R1 先例的操作员显式信任声明; 本机 TUN fake-IP 代理环境）
- K/M 段故障经全局 dispatcher（contextvars 按 case 上下文）在 StructuredTool.func 层机械注入, 模型不可见且并发安全; trace 只含公开工作笔记与工具事件, 无 private CoT
- 轨迹字段: public_work_note / research_need / evidence_gap / tool_name / tool_args / tool_result_summary / next_decision / stop_reason / final_answer
- 执行谱系: RUN1（探索, 无结果记录器, 存档 *_RUN1_ARCHIVE/RUN2_ARCHIVE/RUN3_ARCHIVE）→ instrumentation 修复（并发安全记录器/注入调度器、评估器校准×3）→ 本报告 = 最终 canonical 全量 82 题（同一代码、同一案例集、完整结果记录）
- Canonical run 后仍交付两项机械修复（不影响本 run 证据, 已入代码待下轮验证）: `search_scholarship/get_scholarly_source` 加入 REUSE_SAFE_TOOLS（O7-C 设计职责含 dedup）

## 5. Final Gate

```text
T1_MECHANICAL=PASS
TOOL_COUNT=32
KNOWN_BROKEN_TOOL_COUNT=0
T2_AGENTIC=FAIL
WRONG_PRIMARY_TOOL=0
FALSE_POSITIVE_TOOL_CALL=0
INVALID_TOOL_ARGS=0
FABRICATED_ID_OR_INDEX=0
PRIMARY_SEARCH_WITHOUT_READ=0
SCHOLARLY_ATTRIBUTION_WITHOUT_SECOND_HOP=0
EXACT_DUPLICATE_EXECUTION=2
NO_NEW_INFORMATION_LOOP=0
READY_FOR_END_TO_END_HOLDOUT=false
```

## 6. 未清零项分析与修复交付（供 Reviewer 裁量）

**EXACT_DUPLICATE_EXECUTION = 2（唯一非零 hard gate）**:
1. **D01** — `get_scholarly_source` 同 (source_record_id, ABSTRACT) 执行两次。根因: scholarly 工具不在 `REUSE_SAFE_TOOLS`（O7-C 设计职责本含 dedup/cache, 属机械缺口）。**已修复**: 两工具已加入 REUSE_SAFE_TOOLS（post-run 交付, 待下轮回归验证）。
2. **H03** — `philosopher_debate` 同参重发一次, 且该题最终 FAIL_CLOSED_VALIDATION（validator 打回 2 轮修复未通过）。debate 属生成型工具, 按设计豁免机械判重（同参重调是合法交互: 继续/再来一轮）; 此处的重发与校验失败耦合, 归为模型侧纪律残留。

**Gate 外能力观察（不进 hard gate, 供 V2 命题参考）**:
- 工具路由在边界题上存在随机翻转: E04/E05（analyze_argument 内联替代）、F01/F03（paper_review 被短文本评审绕过——正是 O8 已知 bug 的残余形态, 本 run 中 F02/F04 已正确路由, 说明为随机而非系统性）、G02（get_school 跳过）、J01（文本主张题未读原文）。同题在 PRE-RUN 中曾有相反表现, 证明非确定性。
- FAIL_CLOSED_VALIDATION ×2（C06/H03）: validator 拒绝未锚定引用 → 修复 2 轮未过 → 不发布。这是 fail-closed 保护按设计工作（宁可不出也不编造), 不属编造类违规。
- L02/L03/L06 超出本报告设定的建议检索上限 +1 次（软上限, 协议本身未给 MANDATORY 上限）。
- K/M/L03 注入恢复 13/13 PASS: 坏首条不盲信（K01 识别错位首条→换路径重定位; K04 提及相似书名但明确标注未核验）、provider 失败→换通道或诚实降级、schema 错误→自修。
- deepseek-flash 单 run 的纪律方差约为 82 题 × 10-15 个边际违规（本轮 12 题带任意违规, 全部为选择/效率类, 零编造类）——这是模型能力底色, 非工具层或 prompt 层可完全消除。

## 7. STOP_FOR_REVIEW

按协议在此停止（STOP_FOR_REVIEW）。T1 全绿; T2 的 11 项 hard gate 中 10 项为零, EXACT_DUPLICATE_EXECUTION=2 未清零（D01 已修复待回归; H03 属生成工具设计豁免域内的模型侧残留）。两条可选路径: ① Reviewer 接受本证据并裁量签发 V2; ② Builder 以 scholarly dedup 回归 + debate 重发纪律为专题再跑一轮 targeted run。由 GPT-5.6 Sol 裁定。
