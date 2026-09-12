# O8 Comprehensive Capability & Tool Audit — PhiAgent

> 审计头: 6209efed870efb82b6668eaefa0cd13a18743c6a（O7-E 封存后首件）
> 授权: V12-M1 裁定正式指令——能力地图 / 30 工具 / Main Agent orchestration /
> 检索阅读闭环 / repair-validator / 交互能力与缺口全量盘点。
> 机器可读版: docs/evidence/O8_CAPABILITY_AUDIT.json

## 1. 生产模型层

| 角色 | 模型 | 通道 | 状态 |
|---|---|---|---|
| **canonical production** | `deepseek-flash`（DeepSeek V4.1 Flash） | api.deepseek.com（routes/agent_llm.MODEL，repo 默认即 canonical） | V12-M1 起生效 |
| scholarly judge（冻结） | `glm-4-plus` | open.bigmodel.cn | O7A 冻结件，独立计费 |
| 图像生成 | `agnes-image-2.1-flash` | apihub.agnes-ai.com | generate_image 工具 |
| embeddings | zhipu /embeddings | open.bigmodel.cn | 检索向量层 |

旧 id 清理：`deepseek-v4-flash` 已在 production-active 代码清零（V12-M1）；`deepseek-chat` 仅存于 `config.DEEPSEEK_MODEL`（服务非 agent 链的独立常量）与历史 artifacts。

## 2. 工具注册表（实数 32，任务书"30"为约数）

| 域 | 数 | 工具 |
|---|---|---|
| eval（思辨脚手架/教育学） | 15 | phti_test, compare_views, socratic_tutor, advisor_council, paper_review, analyze_argument, profile, conceptual_map, essay_outline, life_coach, dialectic, history_timeline, confrontation, school_arena, agent_council |
| retrieval（原典/知识查询） | 10 | search_books, get_book_detail, get_chapter, query_graph, get_philosopher, list_books, get_school, concept_trace, websearch, query_database |
| memory/writing（生成类） | 5 | write_essay, generate_image, role_play, philosopher_debate, thought_experiment |
| scholarly（学术双链） | 2 | search_scholarship, get_scholarly_source |

运行时实测：`routes.agent.TOOLS` 注册 32 个，与四域文件 register_tool 调用逐一对账一致。

## 3. Main Agent orchestration

- **引擎**：`engine_langgraph.py`（2716 行）LangGraph `StateGraph`：`START → agent →(conditional)→ tools → agent` 单脑循环，无独立规划节点（规划即 Main Agent 工具选择本身）。
- **入口**：`stream_agent`（SSE 事件流）→ `routes/agent_sse` → agent-app 前端。
- **韧性**：A4 模型重试（2 次，backoff 1.5/4.0s）；repair 确定性解码（temp=0）；资源上限 `no_tools` 变体。
- **双 agent**：general（深哲，全工具）+ nietzsche（人格包，AIAuthor 记忆召回）；`PHILO_AGENTS` 支撑哲学家广场。
- **安全**：三类输出安全模式（self_harm/violence/hate），中英双语回复。

## 4. 检索/阅读闭环

1. **原典链**：409 本原典（章节 git 源 + OSS/jsDelivr 双轨）→ `search_books`（FTS）→ `get_chapter`（全文阅读）→ 引用核验。`concept_trace` 提供概念分布追踪。
2. **scholarly 链**：`search_scholarship`（Crossref+OpenAlex+LOCAL_CURATED，relevance gate → readability ordering → 一次有界 reformulation，strict_only fail-empty）→ `get_scholarly_source`（access 四态状态机，SSRF 边界）。
3. **诚实性合同**（V7-F2/F5 系遗产）：引用必须可核验；原文不在库 → 干净拒绝或诚实降级，不伪造（V12-14 为典型形态）。

## 5. repair/validator 链

`final_validator`(369 行，问题码封闭集) ← `quote_bound`(311) ← `local_patch_runtime`(190，COPY/PARAPHRASE/CITATION_REPLACE) ← `repair_context`(717) ← `o7e_semantic_transition`(227，7 标签记账)。repair ≤2 轮确定性解码；frozen final gate（blob 22ea181c）唯一裁决。

## 6. 交互层

- **服务**：FastAPI `main.py` 12 routers（health/auth/user/admin/sync/knowledge/ai/history/text/agent/books/authors）+ SPA 托管；`routes/` 共 24 模块。
- **前端**：`app/`（平台 React+Vite，CF Pages）+ `agent-app/`（智能体 :5201）。
- **生产 API 独立轨**：Cloudflare 双 Worker（auth/api）+ D1。

## 7. 缺口与债务（盘点结论）

### 本次已顺手修复
- ✅ agent_llm.py 顶部旧注释「缺省 → deepseek-chat」文档债（M1 裁定移交 O8）。

### 卫生类（需用户决定，不改行为）
- 未跟踪孤儿文件（零引用、不断链）：`backend/jwt_verify.py`、`backend/upstream.py`、`backend/user_profile_store.py`、`backend/routes/agent_history.py`、`backend/routes/auth_proxy.py`、`agent-app/src/data/conversationSync.js` —— 入库或删除待定。
- 未跟踪肖像资产：`app/public/philosopher/José Martí.webp`、黑塞 portrait —— 疑似 scripts 产物漏提交。
- `.zcode/`、`backend/data/scholarly_cache.json` 为本地/运行时文件，不应入库（维持现状）。

### 能力缺口（需 Reviewer/用户决策，均不擅自动工）
1. **原典缺口的逐字引文**：原文不在库时只能诚实降级（V12-14 形态，textual grounding 必然受损）。可选补强：扩大合法 OA 全文源 / 引入可核验原文片段库——涉及 corpus 政策，需单独授权。
2. **repair 引入新问题无预检**：repair-1 生成后才被 semantic 分类（V12-08 形态，5 个 transient 空转）。预检机制涉及 repair semantics（冻结区），需单独任务书。
3. **LOCAL_CURATED 学术覆盖未量化**：建议后续做一次 coverage 统计（纯只读小任务）。
4. **conversationSync.js 悬空**：agent-app 多轮会话同步功能半成品，需决定去留。

### 明确不动
V12 三项冻结失败不修；judge / final gate / qualification thresholds 不动；V13 不存在。

## 8. 结论

PhiAgent 当前是一个**以 32 工具为手、LangGraph 单脑为骨、双检索闭环（原典+scholarly）为耳目、诚实性 validator 为闸**的完整哲学问答系统，production base 已迁移至 deepseek-flash。已知失败项（V12 三项）均属「诚实性合同的代价」或「冻结阈值的历史计入」，非工程缺陷。真正需要补什么的决策权在用户/Reviewer：上表第 7 节四项能力缺口按投入从「只读统计」到「corpus 政策变更」递增，建议按此顺序逐项裁定。
