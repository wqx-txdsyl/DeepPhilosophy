# O8 Final Issue Ledger（PhiAgent O9-O14 唯一问题集输入）

> version 1.0 / created 2026-09-12 / authority: PhiAgent Mainline Correction Prompt（用户/Reviewer 主线修正令）
> issue_count = 15（P0×3 / P1×7 / P2×5）；O8_FINAL=PASS 保持成立

## Roadmap Correction

- METASO_EXPERIMENT=DEFERRED_OPTIONAL（BLOCKS_MAINLINE=false, USER_DECISION_REQUIRED=false）
- 新主线: O8 ✓ → **O9 UI/UX Design** → O10 Core Repair + Final Requalification → O11 Adaptive Reader → O12 Persistent Conversation → O13 Integration & UX Polish → O14 Production Release Gate → PhiAgent 1.0

## P0

### P0-01 Over-research 系统性过度检索  `OWNER=O10`

**问题**: 系统为回答哲学问题进行了明显过量检索

**证据**:
- O8-R2: 793 duplicate calls; 69/72 cases duplicated; 51/72 overresearch flags; simple cases avg TOOL_CALLS=8.83; efficiency dim mean=0.89
- O8-R3-EP: 4/6 overresearch; 84 tool calls / 6 cases; 59 duplicate calls
- refs: O8_R2_EFFICIENCY.json#aggregate, O8_R2_CAPABILITY_RESULTS.json#dimension_statistics.efficiency

### P0-02 Duplicate Retrieval / Convergence  `OWNER=O10`

**问题**: 现有 DuplicateGuard 未阻止实际重复检索模式：same tool、same/similar arguments、no-new-information retrieval、repair/research spinning

**证据**:
- O8-R2: 793 duplicate calls (same tool + same normalized args), 69/72 cases

### P0-03 Tool Selection Discipline  `OWNER=O10`

**问题**: 工具选择纪律缺失：简单问题不应检索却检索（cat10 均值 8.83 次工具调用）；hard-primary case 不接触原典（O8R2-13: 0 工具/4.1s）；get_scholarly_source second-hop 不稳定（Agentic SHOULD_CALL FAIL）；错误工具替代正确工具（paper_review 被 analyze_argument 替代）

**证据**:
- O8-R2: tool_selection mean=2.22; retrieval_strategy mean=1.61
- O8-R3: AGENTIC_MATRIX SHOULD_CALL 2 FAIL 保留

## P1

### P1-01 philosopher_debate argument robustness  `OWNER=O10`

**问题**: speakers 传 JSON 数组 → speakers.replace() → AttributeError 崩溃

**证据**:
- mechanical: agent_tools_memory.py:520; O8R2-MECH-1

### P1-02 search_books relevance / empty-query behavior  `OWNER=O10`

**问题**: empty query guard missing; vector relevance floor too low (~0.35); irrelevant result can masquerade as useful; EMPTY_RESULT semantic unreachable

**证据**:
- mechanical: O8R2-MECH-2; 空查询/伪查询实测返回不相关结果

### P1-03 FULL_REWRITE Repair Safety Parity  `OWNER=O10`

**问题**: LOCAL_PATCH 已有 post-repair semantic validation / AMBIGUOUS fail-closed / evidence-family detection / rollback / candidate preservation；FULL_REWRITE / non-local repair 无等价 parity

**证据**:
- O8-R2: engine_langgraph.py:1488 定义/:2378 调用守卫 _lp_meta is not None; REPAIR_SAFETY_AUDIT static analysis

### P1-04 Repair Transient Regression  `OWNER=O10`

**问题**: 47/50 repair cases 出现 repair 引入问题→后续再清除；需降低 repair-induced transient errors 与额外成本

**证据**:
- O8-R2: REPAIR_SAFETY_AUDIT BENCHMARK_TELEMETRY; repair 60 轮/50 案例

### P1-05 Primary-text Anchoring in Comparison  `OWNER=O10`

**问题**: 比较类问题越出已验证语料进行逐字引用；Final Gate 能挡住但 Agent 本身应更早收敛

**证据**:
- O8-R2: O8R2-23/24（04 类 2/6 未发布: UNVERIFIED_CITATION + UNSUPPORTED_EXACT_QUOTE）

### P1-06 Scholarly Second Hop  `OWNER=O10`

**问题**: search_scholarship → 没有稳定继续 get_scholarly_source；找到文献 ≠ 真正读取文献证据

**证据**:
- O8-R3: AGENTIC_MATRIX get_scholarly_source/SHOULD_CALL=FAIL（AG-FAULT-3 亦未触发 fetch）

### P1-07 paper_review Routing  `OWNER=O10`

**问题**: paper_review SHOULD_CALL=FAIL，常被 analyze_argument 替代

**证据**:
- O8-R3: AGENTIC_MATRIX paper_review/SHOULD_CALL=FAIL

## P2

### P2-01 Empty Input Defaults  `OWNER=O10`

**问题**: query_graph / get_philosopher / get_school 对空输入静默回退柏拉图

**证据**:
- mechanical: O8R2-MECH-3; FAILURE_PATH FAIL

### P2-02 Empty Result Semantics  `OWNER=O10`

**问题**: concept_trace / list_books / history_timeline 不存在目标时可能模糊命中或返回全集

**证据**:
- mechanical: O8R2-MECH-4; EMPTY_RESULT FAIL

### P2-03 LOCAL_CURATED Metadata  `OWNER=O10_POLICY`

**问题**: 587 records; DOI ~99.8%; long abstract coverage ~13.5%; language metadata missing——先记录，不自动扩 corpus

**证据**:
- O9-census 期实测: O8_R2_RETRIEVAL_CENSUS.json LOCAL_CURATED

### P2-04 Primary Text Corpus  `OWNER=O10_POLICY`

**问题**: CANONICAL_COUNT=410 vs old manifest=409；333 works with real text；77 txt placeholders——不得擅自扩库

**证据**:
- O9-census 期实测: O8_R2_RETRIEVAL_CENSUS.json PRIMARY_TEXT

### P2-05 Orphan Files  `OWNER=O13/O14 cleanup review`

**问题**: 6 个零引用孤儿文件为 DELETE_CANDIDATE 而非 DELETE_AUTHORIZED：backend/jwt_verify.py, backend/upstream.py, backend/user_profile_store.py, backend/routes/agent_history.py, backend/routes/auth_proxy.py, agent-app/src/data/conversationSync.js

**证据**:
- O8-R2: O8_R2_INTERACTION_OWNERSHIP.json 全部零引用
