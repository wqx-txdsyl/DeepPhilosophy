# PhiAgent Tool Architecture（Phase T / T1 审计）

> HEAD_BEFORE = ec09e04da914d55ba3904fc5812785b2f81729f6（QG2 同基线, Patch1/1.1 主体冻结）
> 审计对象 = 生产注册表全部 38 项工具：30 项通用 TOOLS（`routes/agent.py _TOOL_REGISTER_ORDER`）
> + 8 项哲学家智能体专属 PHILO_EXTRA_TOOLS（`agents.py`，经 PHILO_TOOL_DEFS 注册）。
> 机器可读单一真源：`backend/tool_contracts.py` 的 `TOOL_TAXONOMY`（本表由其生成口径同步手写）。

# 0. 核心原则（T2 Reasoning Authority Rule）

**Main Agent owns final reasoning.**

- 工具只提供 **DATA / CAPABILITY / STRUCTURE / STATE / PRESENTATION**；
- 除用户明确请求独立 artifact（USER_REQUESTED_ARTIFACT: write_essay / generate_image /
  essay_outline）外，任何 reasoning tool **不得拥有最终答案权**；
- reasoning tool 返回 **structured intermediate result**（统一 ToolResult 形态见 §3），
  不返回 ready-to-display final answer；
- 工具不得绕开 Evidence Contract——专用工具自带的原典证据以结构化 citations/evidence
  随产物返回，由引擎入契约查证池（engine tools_node 最小接口适配），主 Agent 的正式引用
  仍须经 LiveCitationSanitizer 核验。

# 1. 工具分类总表（38 项）

字段：`TOOL_CLASS` / USES_INTERNAL_LLM（内部调 LLM）/ RETURNS_FINAL_PROSE（返回成品 prose）/
STATEFUL / EVIDENCE_PRODUCING（产物可入证据契约）/ USER_VISIBLE_ARTIFACT / SAFE_TO_REPEAT。

## 1.1 检索域（agent_tools_retrieval.py, 10）

| 工具 | TOOL_CLASS | LLM | PROSE | STATE | EVID | ARTIFACT | REPEAT |
|---|---|---|---|---|---|---|---|
| search_books | RETRIEVAL | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| get_book_detail | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| get_chapter | READ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| query_graph | STRUCTURED_DATA | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| get_philosopher | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| list_books | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| get_school | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| concept_trace | STRUCTURED_DATA | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| websearch | RETRIEVAL | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| query_database | STRUCTURED_DATA | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

## 1.2 记忆/创作域（agent_tools_memory.py, 5）

| 工具 | TOOL_CLASS | LLM | PROSE | STATE | EVID | ARTIFACT | REPEAT | 备注 |
|---|---|---|---|---|---|---|---|---|
| write_essay | GENERATION | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | USER_REQUESTED_ARTIFACT |
| generate_image | EXTERNAL_ACTION | ✗ | ✗ | ✓ | ✗ | ✓ | ✗ | 迭代=图生图修改（合法重入） |
| philosopher_debate | INTERACTION_MODE | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | 交互产物, 重入=继续交互 |
| thought_experiment | REASONING_SKILL | ✓ | ✗ | ✓ | ✗ | ✗ | ✗ | **T7** 脚手架+重入策略 |
| role_play | PERSONA_DATA | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | 返回人格包数据 |

## 1.3 评估/分析域（agent_tools_eval.py, 15）

| 工具 | TOOL_CLASS | LLM | PROSE | STATE | EVID | ARTIFACT | REPEAT | 备注 |
|---|---|---|---|---|---|---|---|---|
| phti_test | INTERACTION_MODE | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | |
| compare_views | REASONING_SKILL | ✓ | ✗ | ✗ | ✓ | ✗ | ✗ | **T3** comparison scaffold |
| socratic_tutor | INTERACTION_MODE | ✓ | ✗ | ✓ | ✗ | ✗ | ✓ | **T6** ONE CALL = ONE QUESTION |
| advisor_council | REASONING_SKILL | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | **T2** perspectives scaffold |
| paper_review | REASONING_SKILL | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | **T8** structured review |
| analyze_argument | REASONING_SKILL | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | **T8** argument_structure |
| profile | REASONING_SKILL | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | 低频, 保持现状 |
| conceptual_map | PRESENTATION | ✓ | ✗ | ✗ | ✗ | ✓ | ✗ | **T5** 通用图+确定性 Mermaid |
| essay_outline | GENERATION | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | **T10** 保留 artifact 属性 |
| life_coach | INTERACTION_MODE | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | 疏导体裁例外, 保持现状 |
| dialectic | REASONING_SKILL | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | **T4** 动态辩证字段 |
| history_timeline | PRESENTATION | ✓ | ✓ | ✗ | ✓ | ✓ | ✗ | |
| confrontation | INTERACTION_MODE | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **T9** 最低限度统一 |
| school_arena | INTERACTION_MODE | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | |
| agent_council | INTERACTION_MODE | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | |

## 1.4 哲学家智能体专属（agents.py PHILO_EXTRA_TOOLS, 8）

| 工具 | TOOL_CLASS | LLM | PROSE | STATE | EVID | ARTIFACT | REPEAT |
|---|---|---|---|---|---|---|---|
| philosopher_memory | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| philosopher_period | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| philosopher_style | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| philosopher_quote | RETRIEVAL | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| philosopher_graph | STRUCTURED_DATA | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| philosopher_corpus | RETRIEVAL | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ |
| philosopher_concepts | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |
| philosopher_user | READ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ |

计数核对：10 + 5 + 15 + 8 = **38**（任务书 RECEIPT 口径 TOOLS_AUDITED=38；通用注册表 30 + 哲学家专属 8）。

# 2. 两类工具的职责边界

**A. 真工具（DATA/CAPABILITY/STRUCTURE/STATE/PRESENTATION）**：§1.1 全部 + role_play +
generate_image + phti_test + conceptual_map（图=结构化 graph 数据，Mermaid 只是 renderer）。

**B. Reasoning Skill（受 T2 约束）**：compare_views / dialectic / analyze_argument /
paper_review / advisor_council / thought_experiment——内部 LLM 只产生 **scaffold**（JSON 结构），
不产生成品 essay；主 Agent 结合 problem model / evidence contract / claim roles / 对话语境二次综合。

**例外（USER_REQUESTED_ARTIFACT，T10）**：write_essay / essay_outline / generate_image——
用户请求的对象就是 artifact 本身，可较完整呈现；interaction 产物（philosopher_debate /
school_arena / agent_council / confrontation 卡片 / life_coach）按交互体裁保留。

# 3. 统一 ToolResult（scaffold_result）

```json
{
  "kind": "comparison_scaffold | dialectical_movement | socratic_turn | argument_structure
         | structured_review | perspectives_scaffold | thought_experiment_scaffold | graph_map
         | confrontation_card",
  "summary": "一句话说明",
  "confidence": 0.0-1.0,
  "...kind 专属结构化字段（不要求全部存在）": {},
  "presentation_hint": "展示建议（非命令）",
  "reasoning_authority": "MAIN_AGENT"
}
```

# 4. 重入策略（T7）

`tool_contracts.SkillReentryTracker`（invocation 级，引擎 tools_node 批前准入）：

- 作用域 `SKILL_REENTRY_TOOLS`（13 项 reasoning/generation skill；交互类/生图类豁免）；
- 同一 purpose 默认 `MAX_SAME_SKILL_REENTRY=1`（env `AGENT_SKILL_REENTRY`）；
- 再次调用必须满足 justification 之一：
  **USER_REQUESTED_ITERATION**（参数/用户消息含迭代标志词）/ **FIRST_RESULT_INVALID**（上次失败）/
  **NEW_OBLIGATION**（purpose 实质变化：shingle Jaccard < 0.45 且非退化包含）；
- 退化迭代（Q11 形态：新输入极短且几乎被先前 purpose 包含）按同 purpose 处理 → 拒绝；
- 同工具调用总量硬上限 = 2 + MAX_SAME_SKILL_REENTRY（绝对，不因用户消息解锁）。

# 5. 确定性 Mermaid（T5）

`render_mermaid(graph, map_type)`：节点 id 稳定序号（n1..nN）、label 全量双引号包裹
（内嵌双引号→全角、换行→空格、控制字符剥离、超长截断）、edge `n1 -->|"label"| n2`、
分组 subgraph、方向按 MAP_TYPE（PROCESS_FLOW/ARGUMENT_GRAPH=TD，其余 LR）。
`validate_mermaid(text, graph)`：指令行/逐行语法/引号配平/节点边计数与 graph 对账——
parse PASS 的确定性口径（Q13 回归必验）。内部 LLM 只产 graph JSON，违规输出 Mermaid 文本不被采信。

# 6. 路由原则（T11）

系统提示铁律 13：**能力匹配 × 信息增益 × 输出合同匹配**——
① 主 Agent 自己能否高质量完成？② 工具是否提供缺失的信息/结构/状态/产物？
③ 用户要的输出是否就是该工具的原生产物？④ 工具约束是否兼容用户约束？
只 会重复生成主 Agent 自己也能生成的成品 prose 且不增加 evidence/state/artifact → 允许不调用。
成功指标由 EXPECTED_TOOL_NAME_MATCH_RATE 改为 **USEFUL_SPECIALIZED_TOOL_RATE**。

# 7. 所有权审计（T12）

done 载荷新增 `tool_ownership`：逐调用 `tool_value`（NEW_EVIDENCE/NEW_STATE/NEW_STRUCTURE/
NEW_ARTIFACT/PRESENTATION/REDUNDANT）与 `final_use`（USED/PARTIALLY_USED/BYPASSED，专用工具按
结果指纹片段与 Final 正文重叠判定）。`tool_value=REDUNDANT` 或 `final_use=BYPASSED`
（Q13 式"合规性调用"）计入 `bypassed_specialized_tools` / `redundant_specialized_tools` anomaly。

# 8. T13 顺手关闭项

- **A 引用变体**：`evidence_contract` 统一迭代器覆盖 canonical【《书》·章】/【《书》】/
  【《书名·章节》】合写/【《书》节数】/【作者·《作品》】（新增，流式净化与终检双路径）。
- **B 运行时措辞**：`RuntimePhraseScrubber`（流式安全）+ 终检——"检索已被收口/工具预算已达上限/
  系统收敛/准入未通过"等内部治理语言不得进入 Final prose（thinking/tool event 不受限）；
  系统提示铁律 15 同步声明。
- **C 义务台账**：高层语义义务（alternative_interpretation / uncertainty_disclosure /
  analogy_boundary）关键词未命中 → **UNKNOWN**（不再错误 UNSATISFIED）；命中仍 SATISFIED；
  事实类义务保持两态；interpretation_engine 补正触发改为只依赖结构性信号（overclaim /
  alternatives_offered）。未新增任何正文 Guard。

# 9. 与冻结清单的关系

Answer Composer 架构 / Thinking pipeline / Claim role taxonomy / Evidence Contract 主体 /
Temporal Persona / Conversation state / Memory / Knowledge Graph / Embedding / corpus 均
未动。触碰点仅为 Tool Architecture 接口最小适配：
① engine tools_node 重入准入批前判定 + 专用工具结构化证据入契约查证池（只进 raw_tool_log，
不进预算/trace）；② engine 文本路径串接 RuntimePhraseScrubber；③ done 载荷新增 tool_ownership
（纯审计字段）；④ SYSTEM_PROMPT_LG 铁律 4/4''/4''''/5'/13/14/15（工具架构语义）；⑤ AgentState
新增 user_message/reentry 两个通道字段。Retrieval ranking 未修改。
