# PhiAgent Phase T — Tool Architecture Final Report

> QG2_REVIEW = PASS_WITH_REQUIRED_NEXT_PHASE → 本 Phase 只治理 Tool Architecture。
> Patch1/Patch1.1 主体冻结未动。基线与审计全集见 `docs/PHIAGENT_TOOL_ARCHITECTURE.md`（T1）,
> 测试与回归证据见 `docs/PHIAGENT_PHASE_T_REGRESSION.md`。

# 0. 定案

**Main Agent owns final reasoning。** 工具只提供 DATA / CAPABILITY / STRUCTURE / STATE /
PRESENTATION; reasoning/generation skill 一律返回结构化脚手架（`tool_contracts.scaffold_result`,
带 `reasoning_authority=MAIN_AGENT` 标记）, 最终综合、裁决与展示深度由主 Agent 完成。
仅 USER_REQUESTED_ARTIFACT（write_essay / essay_outline / generate_image）与交互体裁
（辩论/竞技场/对质卡片/疏导）保留成品形态。

# 1. 逐工具处置（对照任务书 RECEIPT 字段）

| 工具 | 处置 | 要点 |
|---|---|---|
| compare_views | **重构** | 完整对比成品 → comparison scaffold（shared_problem/comparison_axes/side_a_claims/side_b_claims/strongest_divergence/evidence_needs/candidate_consequences）; 内部 LLM 只产 scaffold JSON 且被明令"不得给出最终胜负判断"; citations 带 snippet 入证据池; description 由"结果即成品, 调用一次直接展示"改为"供主 Agent 二次综合" |
| dialectic | **重构** | 去固定正反合: 输出动态字段 initial_concept/internal_tension/self_negation/transformation/new_determination/residual_tension（按问题需要 3-6 个）; constraints 参数逐字进入执行层 prompt; 确定性净化兜底（标签键丢弃/标签值移除）; 工具产物自身满足"不机械正反合", 不依赖主 Agent 事后救回 |
| conceptual_map | **重构** | 只会"概念→哲学家/流派/著作"脑图 → 六类 MAP_TYPE 通用关系图（CONCEPT_NETWORK/PROCESS_FLOW/ARGUMENT_GRAPH/HISTORICAL_GENEALOGY/PERSON_RELATION/SYSTEM_ARCHITECTURE）; 接受用户 nodes[]/relations[]/constraints/directionality; 输出结构化 graph + 确定性 renderer 生成的 Mermaid（quote/括号 escaping、稳定节点 id、edge syntax）+ validate_mermaid parse 对账; 内部 LLM 只产 graph JSON, 违规手写 Mermaid 不被采信 |
| socratic_tutor | **重构** | 4 轮齐发 → stateful one-turn（ONE CALL = ONE QUESTION）; per-user 状态（topic/round/asked/last_reply）; 第二问生成必须输入用户真实回答（user_reply 参数）; 硬截断保证单问; presentation_hint 声明只展示 next_question |
| thought_experiment | **重构+治理** | 产物结构化（setting/stance_projections/revealed_problem）; invocation 级重入策略生效（见 §2）; description 声明重入约束 |
| paper_review / analyze_argument | **仲裁定界（T8）** | analyze_argument = 单论证逻辑结构（argument_structure: 结论/前提显隐/隐含假设/谬误/最薄弱一步/补强）; paper_review = 完整论文整体评审（structured_review: thesis/结构/证据/最强反驳/贡献/修改优先级）——"300 字毒舌模板"移除; 两 description 互相写明能力边界; 系统提示 4'''' 声明"按输入形态与工具能力匹配选择"; Q15 型（短论证+说"评审"）analyze_argument 合法胜出 |
| confrontation | **最低限度统一（T9）** | 核心交互效果保留; 产物结构化: stance_a/stance_b（textual claim, 只基于检索原文）与 exchanges（明确标注"模拟"的互驳措辞）与 referee_note（裁判候选, 结论归主 Agent）分离; citations/evidence 结构化随产物返回并入证据契约查证池; 移除"对质引用均来自库内原文片段"的单方面声称 |
| essay_outline | **保留（T10）** | USER_REQUESTED_ARTIFACT 例外——大纲即用户请求对象; 完整结构输出不降级; description 声明属性 |
| advisor_council | **重构** | 成品建议文 → perspectives scaffold（视角/预设/张力点/综合提示） |
| 其余 25 项 | 分类标注 | 见 T1 审计表; 未改变行为（真工具域 + 交互体裁 + profile/life_coach 低频保持现状并标注） |

# 2. 横切机制

- **重入策略（T7）**: `SkillReentryTracker`（invocation 级, engine tools_node 批前准入）。
  作用域 13 项 skill; 同 purpose `MAX_SAME_SKILL_REENTRY=1`; justification ∈
  {USER_REQUESTED_ITERATION(参数/用户消息), FIRST_RESULT_INVALID, NEW_OBLIGATION(jaccard<0.45)};
  退化包含检测（Q11 形态: 短输入几乎被先前 purpose 包含→同 purpose）; 总量硬上限=2+MAX。
  Q11 回归: thought_experiment 3 连调 → 1 次。
- **路由原则（T11）**: 系统提示铁律 13——能力匹配 × 信息增益 × 输出合同匹配四问; "工具只会
  重复生成主 Agent 自己也能生成的成品 prose 且不带来新证据/结构/状态/产物 → 允许不调用"。
  成功指标 = USEFUL_SPECIALIZED_TOOL_RATE（本轮回归 11/11）, 弃用 EXPECTED_TOOL_NAME_MATCH_RATE。
  确定性辅助: MAP_HINTS 扩展（画图/关系图/论证依赖）+ map_type 预判注入; COMPARISON 类型
  路由提示（compare_views 首选, 杜绝 QG2/Q08 手工 6 检索形态）。
- **所有权审计（T12）**: done 载荷新增 `tool_ownership`——逐调用 tool_value
  （NEW_EVIDENCE/NEW_STATE/NEW_STRUCTURE/NEW_ARTIFACT/PRESENTATION/REDUNDANT）与 final_use
  （USED/PARTIALLY_USED/BYPASSED, paraphrase 感知: 6 字片段采样×归一化正文重叠; 实质产物
  转述综合→PARTIALLY_USED, 空薄产物无视→BYPASSED）; BYPASSED/REDUNDANT 计数即 observability
  anomaly。本轮回归: BYPASSED=0, REDUNDANT_SPECIALIZED=0。
- **证据契约接口适配（T9 配套）**: 专用工具结构化 citations/evidence 由引擎注入契约查证池
  （仅进 raw_tool_log——引用核验/证据契约可对齐; 不进 tool_log/预算/trace, 检索口径零变化）。
- **T13 顺手关闭**: ①引用变体统一迭代器（canonical/《书》/《书名·章节》合写/《书》节数/
  作者·《作品》新增——流式净化与终检双路径）; ②RuntimePhraseScrubber + 铁律 15
  （内部治理措辞零入 Final; 回归中发现并修复流式逗号吞噬 bug——见回归报告 §3.1）;
  ③高层义务未命中→UNKNOWN（不再错误 UNSATISFIED）, 补正触发改结构性信号
  （overclaim/alternatives_offered）, 零新增正文 Guard。

# 3. 冻结清单核对（DO NOT TOUCH）

Answer Composer 大架构 / Thinking pipeline / Claim role taxonomy / Evidence Contract 主体 /
Temporal Persona / Conversation state / Memory / Knowledge Graph / Embedding / corpus——
未触碰。最小必要适配仅: tools_node 重入准入批前判定 + 结构化证据入池（raw_tool_log only）、
文本路径串接 scrubber、done 新增 tool_ownership 审计字段、SYSTEM_PROMPT_LG 铁律
4/4''/4''''/5'/9/13/14/15、AgentState 增加 user_message/reentry 通道字段、_mem_slot setdefault
加固（新增 socratic 状态键所需）。Retrieval ranking 零修改; COMPARISON 检索配额收紧属
准入治理（QG2 报告 Patch 候选 5 明确背书）, 非 ranking。

# 4. CHANGED_FILES（本 Phase）

```
backend/tool_contracts.py                    新增（单一真源: taxonomy/scaffold/reentry/mermaid/scrubber/audit）
backend/routes/agent_tools_eval.py           compare_views/socratic_tutor/advisor_council/paper_review/analyze_argument/conceptual_map/dialectic/confrontation/essay_outline 重构
backend/routes/agent_tools_memory.py         thought_experiment 结构化
backend/routes/agent_core.py                 _mem_slot 逐键 setdefault 加固
backend/agent_runtime.py                     COMPARISON 检索配额收紧（SEARCH 5→3 / TOTAL 7→3）
backend/engine_langgraph.py                  重入准入/证据入池/scrubber 串接/MAP_HINTS 扩展/COMPARISON 路由提示/铁律 4-15/AgentState/done.tool_ownership
backend/evidence_contract.py                 引用变体统一迭代器（含【作者·《作品》】）
backend/semantic_obligations.py              UNKNOWN 状态（T13-C）
backend/interpretation_engine.py             补正触发改结构性信号
backend/tests/test_phase_t.py                新增 68 用例
backend/tests/test_phase_s.py                2 例按 T13-C 新契约更新
backend/tests/test_interpretation_engine.py  _run_stream 密封化（stub 兜底 LLM）
docs/PHIAGENT_TOOL_ARCHITECTURE.md           新增（T1 审计）
docs/PHIAGENT_PHASE_T_TOOL_ARCHITECTURE.md   新增（本报告）
docs/PHIAGENT_PHASE_T_REGRESSION.md          新增（回归报告）
backend/tools/_tmp/phase_t_client.py         临时回归客户端（不提交）
```

# 5. VERDICT

**PHASE_T = PASS**（7/7 Hard Gate Case + 4/4 新增 Case + 全局 5 gate; 自动化 68+126+99 全绿;
冻结清单零触碰; Known Issues 5 项已记录, 均不阻塞验收）。
