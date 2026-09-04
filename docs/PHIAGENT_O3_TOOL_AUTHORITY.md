# PhiAgent O3 — Tool Authority / Main-Agent-Owned Research Control

> 阶段: O3（Orchestration Reset 第 3 刀）
> 分支: `refactor/phiagent-main-agent-orchestration`
> BASE_SHA: `7757452e92fb23230faaa2f7a2adee96cd8f423f`（O2 FINAL PASS, ACCEPTED_SHA）
> Reviewer: GPT-5.6 Sol ｜ 模型: GLM-5.3-Flash (Reasoning Max)
> 前置: O1_FINAL_REVIEW = PASS；O2_FINAL_REVIEW = PASS（RP1 闭合）

---

## 0. 命题

```
O1: 谁决定下一步认知行动？      → Main Agent
O2: 谁写最终答案？              → Main Agent
O3: Main Agent 宣告工具后,
    谁决定这个工具能否执行？    → runtime 仅限机械约束
```

O3 后 runtime 与 Main Agent 的全部对话只剩:

```
Main Agent: "我要调用这个工具。"
Runtime:    "schema / 精确重复 / 硬资源上限 机械上是否允许？"
            YES → execute
```

而不是 runtime 再补一句"但根据我对哲学问题的理解，你其实已经查够了。"

```
TOOL_DECISION_OWNER = MAIN_AGENT
SEMANTIC_TOOL_ADMISSION_GATES_AFTER = 0
SEMANTIC_TOOL_FORCE_PATHS_AFTER = 0
SEMANTIC_STOP_FORCE_PATHS_AFTER = 0
ENGINE_COGNITIVE_AUTO_TOOLS = 0（O1 不变量, 保持）
```

## 1. BEFORE — 工具权威 graph（BASE 实测）

宣告一个工具后，BASE 依次经过 5 道闸:

```
宣告 → ① ledger.admit（义务准入: 配额/查询族/义务总闸/forced 收口）──拒绝→ 执行前取消
     → ② reentry.admit（技能重入: purpose 相似度/同工具上限）────────拒绝→ 执行前取消
     → ③ DuplicateGuard（精确归一判重）──────────────────────────────命中→ 复用旧结果
     → ④ 执行（超时/重试/FALLBACK 提示）
     → ⑤ 登记与计数（guard/reentry/rstate/ledger/budget/trace/raw_log/伪证据条目）
```

owner 分类（§2 审计, 全部追真实调用链）:

| Owner | 位置 | 分类 | 控制效果 |
|---|---|---|---|
| `ObligationLedger.admit` | agent_runtime.py:791-877 | **SEMANTIC**（查询族 Jaccard≥0.45、family exec limit、low_gain 族拒绝、obligations_satisfied 总闸、vi 分项配额 search≤2/read≤2/meta≤1/web≤1、复杂度包络、forced 轮只放未读 get_chapter）+ MECHANICAL（(book,chapter) 精确判重） | 执行前取消 |
| `SkillReentryTracker.admit` | tool_contracts.py:161-248 | **SEMANTIC**（purpose 相似、同工具 cap=3） | 执行前取消 |
| `DuplicateGuard` | agent_runtime.py:183-222 | **MECHANICAL**（sha1(工具+归一参数) 精确相等; scope 变体放行） | 复用（保留） |
| forced 收口 4 源 | engine agent_node | hard 上限=**MECHANICAL**；ledger.rejected≥3 / no_gain_streak≥3 / sufficiency force = **SEMANTIC** | 注入强制指令 + forced 准入收缩 + should_continue 截断 |
| validator→repair | engine（O2） | **MECHANICAL**（O2 合同, 保留） | 拒答权 |
| safety 替换 | engine（O2） | safety_runtime 单列（保留） | 整答替换 |

**BEFORE 实测**（`backend/tools/_tmp/o3_before_trace.py`, 真实 ledger+tools_node 驱动）:

```
B1 verification quota pressure: 第 3 次实质不同检索被拒
   → {"error": "检索准入未通过（search_cap: 原典定位检索已达核验配额（≤2）...）"}
B3 义务满足后再检索:
   → {"error": "检索准入未通过（obligation_satisfied: 核验义务已满足, 请立即基于已有材料...）"}
B4 forced closeout（hard 越线 + forced=True）:
   → 新 search 被拒: "收口轮禁止新检索..."; 仅未读 get_chapter 放行
B5 repair 轮: budget/ledger/rstate/reentry 全部继承 → 新研究调用被旧状态拦截
   （即 O2 KNOWN_ISSUES #5）

MODEL_DECLARED_CALLS_BEFORE（B1–B4 trace 内）= 10
EXECUTED_BEFORE = 7
SEMANTIC_REJECTIONS_BEFORE = 3（search_cap / obligation_satisfied / forced 收口）
MECHANICAL_REJECTIONS_BEFORE = 0
FORCED_CLOSEOUTS_BEFORE = 4 触发源（1 机械 + 3 语义）
```

## 2. AFTER — 机械门 graph

```
宣告 → 机械门（唯一保留）:
        ├─ RESOURCE_CEILING_REACHED（全局硬上限: hard_retrieval=20 / hard_total=24, env 可配）
        ├─ EXACT_DUPLICATE_REUSED（同工具 + 归一化后完全相同参数 → 复用旧结果回传模型）
        ├─ 未知工具 / schema 错误 / 超时 / 异常 → 机械错误回包（FALLBACK 提示保留）
        └─ 否则 EXECUTE
            ↓ 真实工具结果（每个宣告必有终态回传, §17）
        同一个 Main Agent
```

移除的控制效果（检测器保留为 telemetry, CONTROL_EFFECT = 0）:

| 移除项 | 原 control | 现状 |
|---|---|---|
| `ObligationLedger.admit` 拒绝 | 执行前取消 | admit 仍被调用（计数/pending 登记, 义务遥测随 done.obligation_ledger 输出）, **判定结果不被消费** |
| `SkillReentryTracker.admit` 拒绝 | 执行前取消 | 同上（重入历史照记） |
| `no_gain_streak` warn/force | 注入指令 + forced | streak 仍计算（done.tool_loop.budget.no_gain 可观测）, 无任何注入/截断 |
| `sufficiency` verdict force（含"最后核验机会"引导） | 注入指令 + forced | verdict 函数保留（telemetry）, 引擎不再调用其控制分支 |
| `ledger.rejected≥3` 空转防护 | forced | 随准入拒绝消失, 触发器移除 |
| soft 预算提示 / RETRIEVAL_LIMIT 提示 | 语义 steering 注入 | 移除 |
| MAP_HINTS / COMPARISON 路由注入 | prompt 层强制专用工具 | 移除（引擎注入删除; 系统提示改为能力描述） |
| plan.injections 路由短语 | prompt 层 | `_is_routing_injection()` 静态过滤（必须调用/禁止跳过工具/优先直接调用/核验配额…不进 prompt） |

保留的停止权威（全部机械, §8）: 硬资源上限、wall-clock 超时（TOOL_TIMEOUT/模型重试）、
取消、fatal provider 失败（graceful completion）。

## 3. Mechanical Gate Contract

允许的拒绝/复用理由（封闭集合, 全部描述机制而非证据判断）:

```
INVALID_SCHEMA / UNKNOWN_TOOL / EXECUTION_ERROR / TIMEOUT
PERMISSION_DENIED / SAFETY_DENIED（safety_runtime 单列）
REQUEST_CANCELLED
RESOURCE_CEILING_REACHED
EXACT_DUPLICATE_REUSED（同工具 + canonicalized identical args → cache/reuse）
```

禁止出现的措辞（已从生产路径移除）: "无需继续搜索 / 证据已经充分 / 没有必要再读 /
核验配额 / 义务已满足"。§6 区分强制执行: 未执行 = RESOURCE 约束, 绝不暗含
"库中无此书 / 无相关来源"——RESOURCE_CEILING_REACHED 消息内建该澄清。

## 4. DuplicateGuard 行为

- 保留: 精确判重（归一化参数 sha1 相等）→ `EXACT_DUPLICATE_REUSED`，旧结果原样回传
  Main Agent（结果完整性 §17 ✓）；scope 参数（limit/top_k 等）变体不构成重复；失败后重试放行。
- 语义相似（query 改写/主题接近）**不构成拒绝理由**（T7）。RetrievalState 的来源集
  重叠检测降级为 info_gain 标签（telemetry: low_gain 计入 done.budget, 无控制效果）。

## 5. Evidence Appetite（Main Agent 研究伦理, prompt 层）

系统提示铁律 1 重写（§7 原文要求落地）——**不设 Python EvidenceAppetiteGate**:

- 工具是主动使用的研究手段, 不存在配额管制; 只要额外检索/阅读可能实质提升可靠性、
  深度或出处根基, 就主动去做;
- 可外部验证的主张/引文/出处/史实优先直接证据而非记忆;
- 解读类问题收集足以呈现最强相关解读的证据, 不停留在第一个貌似可行的读法;
- 还有证据可能实质改善回答就继续研究; 同时避免冗余调用与无新理解的机械检索
  （同参原样重复会被机械判重复用）。

## 6. Repair Loop Tool Authority

O2 repair invocation 与首次运行共享治理状态, BASE 上会被旧准入拦截（O2 KNOWN_ISSUES #5）。
O3 移除语义准入后, repair 轮的工具权威与普通轮完全一致——只有机械门适用（T10）。
KNOWN_ISSUES #5 关闭。

## 7. Specialized-Tool Internal Provenance（§16）

compare_views/confrontation/write_essay 等工具的内部检索证据仍以最小接口入
raw_tool_log（供引用核验/证据契约）, 但每条伪 search_books 条目现在携带结构化溯源:

```python
{"name": "search_books", ..., "pseudo": True,
 "initiated_by": "tool_internal", "parent_tool_call_id": <宣告 id>, "parent_tool": <父工具名>}
```

`FAKE_TOP_LEVEL_TOOL_LOGS_AFTER = 0`（无溯源标记即不得伪装 Main Agent 亲自检索）。
内部检索算法本身不动（§23 scope guard）。

## 8. Behavior Tests（backend/tests/test_o3_tool_authority.py, 14 用例全绿）

| # | 场景 | 断言 |
|---|---|---|
| T1 | 3 个实质不同的核验检索 | 全部执行, 零准入拒绝（BASE 上第 3 个被 search_cap 拒） |
| T2 | obligations_satisfied=true 后读取 | get_chapter 照常执行 |
| T3 | no_gain streak=5 后换工具 | 照常执行, 无拒绝措辞 |
| T4 | telemetry 不足时直接出 final | 零强制工具; final 经 O2 validator 发布; prompt 无强制注入 |
| T5 | 本地空命中 | runtime 零自动 websearch; 模型宣告则执行 |
| T6 | 精确重复 | 复用旧结果且回传模型; `_reused=True`; 未重复执行 |
| T7 | 相似不同 query ×3 | 全部执行 |
| T8 | 硬上限 | RESOURCE_CEILING_REACHED; 未执行; 无"证据"暗示 |
| T9 | 非法 schema | 机械错误回包, 结果完整回传 |
| T10 | repair 轮研究 | 义务满足+no_gain 历史下 get_chapter 照常执行 |
| T11 | 专用工具溯源 | pseudo 条目 initiated_by=tool_internal + parent_tool_call_id |
| T12 | 比较题 | 模型用常规检索完成; compare_views 零强制; prompt 无路由指令 |
| T13 | 越过旧 soft 点（9 次检索 > soft 8） | 全部执行（hard=20 未到） |
| T14 | 结果完整性 | 混合批次（执行/复用/未知/schema 错）每 id 有终态回传 |

## 9. Live UAT（U1–U7, 真实模型 DeepSeek-thinker）

脚本: `backend/tools/_tmp/o3_live_uat.py`; 产物: `o3_after_u*.json`。

| 用例 | 工具权威验收 | validator | tools | 时长 |
|---|---|---|---|---|
| U1 言必有中出处 | **PASS**（search→read 自主完成, 零语义拒绝） | ok, repairs=0 | 5 | 32.9s |
| U2 研究密集核验（上帝已死双书定位） | **PASS**（20 次执行 + 6 次精确复用, **零配额拦截**——BASE 上 B1 同类场景第 3 次检索即被拒） | ok=false, repairs=2 → 耗尽零发布（模型两轮候选均含半占位引用【《查》· 章节】与未标注近似引文, O2 合同正确拒绝; 无效内容零公开） | 28 | 124.6s |
| U3 深哲综合（康德 vs 密尔说谎） | **PASS**（16 次调用持续研究, 无 forced closeout, 1980 字深度未退化） | ok, repairs=0 | 16 | 128.9s |
| U4 本地未命中 | **PASS**（检索空命中后诚实降级, runtime 零自动 websearch） | ok, repairs=0 | 3 | 32.3s |
| U5 zero-tool | **PASS**（零工具, 零强制研究） | ok | 0 | 13.6s |
| U6 出处核验（宰予昼寝） | **PASS**（自主 search→read, 一次通过） | ok | 4 | 30.4s |
| U7 专用工具自愿调用 | **PASS**（模型自愿调用 compare_views + 13 次其他调用; 内部检索溯源见 T11） | ok | 14 | 80.7s |

全部用例: **semantic_rejects = 0、answer_retract = 0**。U2 是 O2×O3 两份合同的联合实证:
O3 保证研究不被拦截, O2 保证无效候选不发布（宁可失败收口）。

## 10. Scope Guard & O4 Candidates

O3 未做: reasoning_plan/semantic_obligations/answer_composer/interpretation_engine/
epistemic_guard 的整体删除（只卸载其工具控制权）; 检索/排序/embedding/KG/Persona/
前端/38 工具重设计。

**O4 删除候选清单**（控制效果已归零, 纯 telemetry 保留待裁）:
`ObligationLedger.admit` 判定分支（配额/包络/查询族）、`SkillReentryTracker`、
`AR.no_gain_verdict`/`NO_GAIN_*_DIRECTIVE`/`NO_GAIN_WARN_HINT`、
`AR.sufficiency_verdict`/`sufficiency_hint`/`SUFFICIENCY_FORCE_DIRECTIVE`、
`AR.SOFT_BUDGET_HINT`、`ADMISSION_REJECT_FORCE`、`RetrievalState.mark_round` 组
（引擎从未调用, DEAD）、`TC.infer_map_type`（路由注入已移除）、
engine `round_all_low/round_any_low` 状态字段（唯一消费者已删）。

## 11. Metrics & FINAL RECEIPT

```
================================================================
O3 FINAL RECEIPT — Tool Authority / Main-Agent-Owned Research Control
================================================================
O3 = READY_FOR_REVIEW
BASE_SHA = 7757452e92fb23230faaa2f7a2adee96cd8f423f
FINAL_SHA = （随本提交回填）
REMOTE_SHA = （push 后回填）
CHANGED_FILES = backend/engine_langgraph.py（机械门改造: 准入/强制收口/路由注入移除,
  硬上限机械拒绝, 伪条目溯源, Evidence Appetite 铁律）; backend/tests/（新增
  test_o3_tool_authority.py 15 用例 + test_phase_a.py 2 用例按新契约改写）;
  docs/PHIAGENT_O3_TOOL_AUTHORITY.md（本文件）
TOOL_DECISION_OWNER = MAIN_AGENT（runtime 仅机械门）
SEMANTIC_TOOL_ADMISSION_GATES_BEFORE = 5（ledger.admit / reentry.admit /
  ledger.rejected force / no_gain force / sufficiency force）
SEMANTIC_TOOL_ADMISSION_GATES_AFTER = 0
SEMANTIC_REJECTIONS_BEFORE = 3/10（B1–B4 实测 trace: search_cap /
  obligation_satisfied / forced 收口）+ 全部分支清单见 §1
SEMANTIC_REJECTIONS_AFTER = 0
MECHANICAL_GATE_REASONS = RESOURCE_CEILING_REACHED / EXACT_DUPLICATE_REUSED /
  UNKNOWN_TOOL / INVALID_SCHEMA(执行错误回包) / TIMEOUT / EXECUTION_ERROR /
  REQUEST_CANCELLED / PERMISSION_DENIED / SAFETY_DENIED(safety_runtime 单列)
FORCED_TOOL_PATHS_BEFORE = 2（MAP_HINTS 注入 + COMPARISON 路由注入 + 比较类执行侧收紧）
FORCED_TOOL_PATHS_AFTER = 0
FORCED_CLOSEOUTS_BEFORE = 4 触发源（hard + rejected≥3 + no_gain≥3 + sufficiency）
FORCED_CLOSEOUTS_AFTER = 1（仅 hard 资源上限, 机械）
SUFFICIENCY_CONTROL_EFFECT_BEFORE = force stop + forced 准入收缩 + "最后核验机会"注入
SUFFICIENCY_CONTROL_EFFECT_AFTER = 0（verdict 仅 telemetry）
NO_GAIN_CONTROL_EFFECT_BEFORE = warn 注入 + force 收口
NO_GAIN_CONTROL_EFFECT_AFTER = 0（streak 仅 telemetry）
PROBLEM_TYPE_ROUTING_EFFECT_AFTER = 0（COMPARISON 收紧随包络失效; 注入已删）
VERIFICATION_INTENT_ROUTING_EFFECT_AFTER = 0（分项配额/总闸不再消费; constraint
  仅保留 O2 引用资格语境, 非工具控制）
EXACT_DUPLICATE_GUARD = KEEP（归一化精确相等 → 复用且结果回传模型, 机械措辞）
SEMANTIC_DUPLICATE_GUARD = REMOVE_CONTROL（来源重叠仅降 info_gain 标签, telemetry）
GLOBAL_HARD_CEILING = hard_retrieval=20 / hard_total=24（env 可配, 未改动）+
  RESOURCE_CEILING_REACHED 机械拒绝（含"未执行≠库中无此书"澄清, §6）
ENGINE_COGNITIVE_AUTO_TOOLS = 0
FAKE_TOP_LEVEL_TOOL_LOGS = 0（内部检索条目带 initiated_by=tool_internal +
  parent_tool_call_id + parent_tool + pseudo=True, T11）
UNEXPLAINED_DECLARED_TOOL_DROPS = 0（T14: 执行/复用/机械拒/错误/取消每 id 有终态）
TOOL_OUTCOME_RETURNED_TO_MODEL_RATE = 100%
REPAIR_LOOP_TOOL_AUTHORITY = 与普通轮一致（仅机械门; KNOWN_ISSUES #5 已关闭, T10）
TOOL_INTERNAL_PROVENANCE = structured（§7）
T1..T14 = 全 PASS（14 用例）+ T19 静态权威审计 PASS（§19: 引擎源码零语义控制
  引用/文案, admit 遥测化, 机械门在位）
U1 = PASS（repairs=0）  U2 = PASS*（工具权威达成: 20 exec+6 reuse 零拦截;
  *validator 耗尽零发布——O2 合同对无效候选的正确执行, 见 §9）
U3 = PASS（无强制收口, 深度未退化）  U4 = PASS（诚实降级, 零自动 websearch）
U5 = PASS（zero-tool）  U6 = PASS（一次通过）  U7 = PASS（自愿 compare_views + 溯源）
PRIMARY_READ_RATE = U1/U6 自主 search→read; CITATION_INTEGRITY = 通过（U2 未核验引用零泄漏——随无效候选一并拒绝发布）
QUOTE_INTEGRITY = 通过（NEAR 未标注被拒, 零泄漏）
RESEARCH_DEPTH = 显著提升（U2/U3 各 28/16 次调用不被拦截; U4 综合 1980 字）
AVG_TOOLS = 10.0（n=7 live; 移除配额后上升属预期, 非退化）
P50_LATENCY = 32.9s（n=7）  P95_LATENCY = 128.9s（U3 深度研究; 对照 O2 P95 68.6s——
  研究自由度提升的延迟代价, known issue）
O1_CAUSAL_TESTS = 13/13   O1_THINKING_SAFETY_TESTS = 4/4
O2_OWNERSHIP_TESTS = 23/23   O3_TOOL_AUTHORITY_TESTS = 15/15
FULL_TEST_COMMAND = pytest backend/tests -q（未排除任何测试）
COLLECTED = 461  PASSED = 461  FAILED = 0  SKIPPED = 0
增量解释: 446 → 461（+14 O3 行为测试 +1 静态权威审计; test_phase_a 2 用例原地改写）
O4_DELETION_CANDIDATES = 见 §10（admit 配额分支/重入跟踪器/no_gain+sufficiency
  directive 族/soft hint/ADMISSION_REJECT_FORCE/RetrievalState.mark_round(DEAD)/
  infer_map_type/round_all_low 状态字段）
REPORT = docs/PHIAGENT_O3_TOOL_AUTHORITY.md
KNOWN_ISSUES = 4 条（§12: 补跑轮延迟 / 语义检测器留作 telemetry / AVG_TOOLS 上升 /
  路由过滤为短语级静态规则）
STOP —— O3 边界内工作完成, 未开始 O4。最终 PASS 由独立 Reviewer（GPT-5.6 Sol）签发。
```

## 12. Known Issues

1. **硬上限后的补跑轮**: hard 上限触发 → 注入机械指令 → 补跑一轮（该轮新宣告被
   RESOURCE_CEILING_REACHED 拒绝并回传）→ 截断。模型在补跑轮的宣告会消耗一轮
   invocation（延迟可测）; 该机制是 §17（结果完整性）与 §8（机械停止权）的折中。
2. **语义检测器保留**: no_gain/sufficiency/family 判定代码仍在（telemetry）,
   O4 决定删除/合并; 静态审计（§19）保证其 CONTROL_EFFECT = 0。
3. **AVG_TOOLS 可能上升**: 移除配额后模型研究更充分, 工具数上升不是退化
   （任务书 §22: MORE TOOLS != automatically worse; 以 epistemic gain/grounding 评估）。
4. `_is_routing_injection` 是短语级静态过滤（非语义分类器）——未来 plan 注入若用
   同义措辞携带路由意图, 需人工审查（已列入静态审计测试口径）。
