# O8 Comprehensive Capability & Tool Audit — PhiAgent

> 审计头: 6209efed870efb82b6668eaefa0cd13a18743c6a（O7-E 封存后首件）
> 授权: V12-M1 裁定正式指令——能力地图 / 30 工具 / Main Agent orchestration /
> 检索阅读闭环 / repair-validator / 交互能力与缺口全量盘点。
> 机器可读版: docs/evidence/O8_CAPABILITY_AUDIT.json
> 修订: 2026-09-12 O8-R1 Correction Patch（Reviewer 裁定 PATCH_REQUIRED 后修正）
> ——gap② 事实纠正 / V12 三项失败拆分重分类 / 删除「非工程缺陷」总括 / 落定 P0-P2 缺口顺序。

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

**Local Patch post-patch 语义安全门**：`evaluate_repair_safety`（engine_langgraph.py:1488，V9-F2-R2 §1）在 production Local Patch 成功 apply 后实际调用（:2378）；AMBIGUOUS 无条件拒绝（family unknown 不逃逸，fail-closed）；GENUINELY_NEW 且 family ∈ {QUOTE,CITATION,BIBLIOGRAPHIC} 拒绝；REKEY/SHIFT/RELABEL/PERSISTED 不误杀；拒绝即回滚 pre-patch candidate；门内任何异常 fail-closed（SAFETY_GATE_ERROR）。该门当前**仅覆盖 Local Patch 路径**——FULL_REWRITE / non-local-patch repair 无等价 global semantic safety + rollback parity（真实 gap，见第 7 节）。

## 6. 交互层

- **服务**：FastAPI `main.py` 12 routers（health/auth/user/admin/sync/knowledge/ai/history/text/agent/books/authors）+ SPA 托管；`routes/` 共 24 模块。
- **前端**：`app/`（平台 React+Vite，CF Pages）+ `agent-app/`（智能体 :5201）。
- **生产 API 独立轨**：Cloudflare 双 Worker（auth/api）+ D1。

## 7. 缺口与债务（盘点结论）

### 本次已顺手修复
- ✅ agent_llm.py 顶部旧注释「缺省 → deepseek-chat」文档债（M1 裁定移交 O8）。

### 卫生类（2026-09-12 Reviewer C 项裁定：全部不删除、不入库）
- 未跟踪孤儿文件（零引用、不断链）：`backend/jwt_verify.py`、`backend/upstream.py`、`backend/user_profile_store.py`、`backend/routes/agent_history.py`、`backend/routes/auth_proxy.py` —— 保持 untracked，O8-R2 仅证明 ownership/reference/build impact 后分类（「零引用」≠「可安全删除」）。
- `agent-app/src/data/conversationSync.js` —— 单独进入 O8-R2 interaction ownership audit，先判 KEEP/DEPRECATE/DELETE。
- 未跟踪肖像资产：`app/public/philosopher/José Martí.webp`、黑塞 portrait —— 属站点资产卫生，不纳入 PhiAgent O8 production scope。
- `.zcode/`、`backend/data/scholarly_cache.json` 为本地/运行时文件，不应入库（维持现状）。

### 能力缺口（2026-09-12 Reviewer B 项裁定后修正；P0-P2 顺序为 Reviewer 推荐序）
1. **P0 operational — autonomous Builder↔Reviewer handoff**：已落地 `docs/agent/AUTONOMOUS_HANDOFF_CONTRACT.json`（本 patch）。
2. **P1 measurement — LOCAL_CURATED coverage census**：只读统计，直接进入 O8-R2 执行。
3. **P1 repair — full-rewrite/non-local repair safety parity**：Local Patch 路径已存在 post-patch semantic safety gate（`evaluate_repair_safety`：AMBIGUOUS fail-closed、QUOTE/CITATION/BIBLIOGRAPHIC 家族 GENUINELY_NEW 拒绝、拒绝即回滚 pre-patch）；**真实 gap 是 FULL_REWRITE / non-local-patch repair 缺少与 Local Patch 等价的 global semantic safety + rollback parity**。O8-R2 测量，O10 修复（改动触及冻结 repair semantics，本 patch 不动）。
4. **P2 interaction — conversationSync ownership**：agent-app 多轮会话同步半成品，O8-R2 ownership audit 裁定去留。
5. **P2 corpus — verifiable primary-text coverage expansion policy**：原文不在库时只能诚实降级（V12-14 形态）。当前不扩库；O8-R2 先量化 primary-text coverage 与缺口、形成 expansion policy，实际 corpus 改动留待 O9/O10 证据之后。

### V12 三项冻结失败的拆分重分类（Reviewer 裁定，替代任何总括归类）
- **V12-08 = REPAIR_SAFETY_ENGINEERING_GAP**
- **V12-14 = HONEST_CAPABILITY_CORPUS_LIMITATION**
- **V12-09 = REPAIR_CONVERGENCE_CITATION_QUOTE_RELIABILITY_GAP**

### 明确不动
V12 三项冻结失败不修；judge / final gate / qualification thresholds 不动；V13 不存在。

## 8. 结论

PhiAgent 当前是一个**以 32 工具为手、LangGraph 单脑为骨、双检索闭环（原典+scholarly）为耳目、诚实性 validator 为闸**的完整哲学问答系统，production base 已迁移至 deepseek-flash。V12 三项冻结失败已按 Reviewer 裁定拆分重分类（V12-08=REPAIR_SAFETY_ENGINEERING_GAP / V12-14=HONEST_CAPABILITY_CORPUS_LIMITATION / V12-09=REPAIR_CONVERGENCE_CITATION_QUOTE_RELIABILITY_GAP），其中 repair-safety 属工程缺口（O10 统一修复），corpus 限制属诚实性合同下的能力边界。缺口优先级按第 7 节 P0→P2 执行：O8-R2 做测量与分类（72 题 benchmark + 32 工具双 Gate + efficiency audit），production repair 统一留给 O10。
