# PHIAGENT BACKEND DECISION AUTHORITY MAP（AUDIT-01 配套文档）

配套：`PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md`（完整论证与证据）。
本文档只放五类硬信息：**运行时决策图 / 权威碰撞矩阵 / 30 项决策点全字段清单 / 模块分类 / 删除候选**。
基线：HEAD `ec09e04da` + 未提交工作树（Patch1/1.1/T/T.1）。CODE_MODIFIED=false。

---

## 1. RUNTIME DECISION GRAPH（简版；带条件与决策所有者标注）

```
[ingress] agent_sse.agent_stream_lg
   ├─ guard.agent_guard            决策: 限流/配额            类型: 规则-机械
   └─ stream_agent
       ├─ [context] prompt 组装 + history[-20:]
       ├─ [D-FORCE-1] ⟦C: MAP_HINTS⟧ 强制 conceptual_map 注入        engine:1400
       ├─ [D-PRE-1]  epistemic_guard 前置裁决 → 注入                 epistemic_guard:846
       ├─ [D-PRE-2]  interpretation_engine 前置裁决 → 注入            interpretation_engine:407
       ├─ [D-PRE-3]  answer_composer 前置裁决（结构+预算）→ 注入      answer_composer:526
       ├─ [D-PLAN]   reasoning_plan.build_plan → 形态/链/角色/约束/VERIFY_NOW/附录抑制 注入   reasoning_plan:814
       ├─ [D-FORCE-2] ⟦C: COMPARISON⟧ compare_views 路由注入          engine:1464
       │
       └─ [loop: agent ⇄ tools, recursion=60]
           agent_node:
             ├─ [D-STOP-1..7] 预算/拒绝/无增益/充分性 → warn|force 注入   engine:296-386
             ├─ [D-AUTO-1] ⟦C: vi+已定位+零读取⟧ _ensure_primary_read
             │      └─ 代执行 locate_exact_phrase + get_chapter → 注入"你自己的核验动作"   engine:451
             └─ LLM invoke（A4 重试 → graceful）
           tools_node:
             ├─ [D-ADMIT]  ObligationLedger.admit（义务/族/配额/包络/forced）  agent_runtime:765
             ├─ [D-REENTRY] SkillReentryTracker.admit                        tool_contracts:192
             ├─ [D-DUP]    DuplicateGuard.decide → CACHE/REUSE               agent_runtime:199
             ├─ [D-AUTO-2] ⟦C: search_books 空⟧ 自动 websearch（结果不回灌模型）  engine:1794
             ├─ [D-STATE]  RetrievalState/ObligationLedger.record → low_gain/义务三态置位
             └─ [D-POOL]   T9 伪 search_books 条目入核验池                    engine:779
       │
       └─ [closeout: engine:1914-2353]（16 段后处理, 见审计报告 §8）
           ├─ [D-MUT-1..5] 流式净化链（机械→语义改写）
           ├─ [D-MUT-6] ⟦C: <60 字符⟧ 短答兜底再生成
           ├─ [D-AUTO-3] ⟦C⟧ 终局安全网补读 → user_note 尾补
           ├─ [D-MUT-7] ⟦C⟧ 已核验引用可见性补发
           ├─ [D-MUT-8] QB.scan_final_consistency 尾补（G/H）
           ├─ [D-MUT-9] epistemic 校正/反事实边界尾补
           ├─ [D-MUT-10] scan_interpretation 尾补
           ├─ [D-MUT-11] scan_composition 尾补
           ├─ [D-EVID]  build_evidence_contract（retrieved⊇candidate⊇used）
           ├─ [D-SAFE]  safety 整答替换
           └─ [done] + 并行 LLM 后处理（summary/suggestions, 失败→确定性兜底）
```

---

## 2. DECISION POINTS（30 项全字段）

字段：QUESTION / OWNER_MODULE / OWNER_FUNCTION / INPUT / OUTPUT / TYPE（DET=规则, LLM=模型, MIX）/ BLOCK / FORCE / CHANGE_FINAL / RETRACT / APPEND_AFTER / DOWNGRADE / TERMINATE / OVERRIDE_MAIN。

| # | QUESTION | OWNER | FUNCTION | INPUT→OUTPUT | TYPE | BLOCK | FORCE | CHANGE_FINAL | RETRACT | APPEND | DOWNGRADE | TERMINATE | OVERRIDE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D01 | 这是什么问题（9 类） | reasoning_plan | classify_problem | msg→problem_type | DET | — | 间接 | 间接 | — | — | — | — | 覆盖 LLM 自分类 |
| D02 | 复杂度档（4 档） | reasoning_plan | classify_complexity | msg→complexity | DET | — | — | 间接（预算） | — | — | — | — | — |
| D03 | 核验意图（3 kind） | reasoning_plan | detect_verification_intent | msg→vi dict | DET | — | 间接 | 间接 | — | — | — | — | vi 命中强制改写 D01/D02 |
| D04 | 来源约束（5 档） | reasoning_plan | 同上 constraint 分支 | msg→constraint | DET | — | — | 间接 | — | — | YES（二手排除） | — | — |
| D05 | 术语核验（B3） | reasoning_plan | detect_term_presence / verify_term_presence | msg+tool_log→state | DET | — | — | 间接 | — | — | — | — | — |
| D06 | 时序路由（B5） | reasoning_plan | detect_temporal / temporal_directive | msg→period 注入 | DET | — | 软（要求调 period 工具） | — | — | — | — | — | — |
| D07 | 推理关系链（B6） | reasoning_plan | derive_relations | msg→13 关系 | DET | — | — | 间接 | — | — | — | — | — |
| D08 | 解释型激活（4 类） | interpretation_engine | InterpretationChallenger.check | msg→categories | DET | — | — | 间接 | — | — | — | — | 与 D01 平行（第二分类器） |
| D09 | 解释置信度（4 tier） | interpretation_engine | ConfidenceCalibrator.calibrate | answer→conf/tier | DET | — | — | 间接（尾补选模板） | — | — | — | — | — |
| D10 | 复杂度/篇幅档（composer 版） | answer_composer | classify_complexity | msg→5 档 | DET | — | — | 间接 | — | — | — | — | 与 D02 平行（第三分类器） |
| D11 | 生成类豁免 | answer_composer | GENERATIVE_SKIP | msg→bool | DET | — | — | — | — | — | — | — | — |
| D12 | 用户前提对错 | epistemic_guard | PremiseVerifier.check | msg→contradictions | DET | — | — | 注入+尾补 | — | YES | — | — | 命令模型"第一句先纠正" |
| D13 | 反事实 vs 史料 | epistemic_guard | CounterfactualAuthorGuard.check | msg→mode | DET | — | — | 注入+尾补 | — | YES | — | — | 命令开头措辞 |
| D14 | claim 知识论分级（9 类） | epistemic_guard | EpistemicClaimClassifier.classify | 句→type | DET | — | — | 间接 | — | — | YES（SPECULATION 禁绑） | — | — |
| D15 | claim 角色（5 类） | evidence_contract | _claim_role | 句→role | DET | — | — | — | — | — | — | — | 审计/语气 |
| D16 | 义务履行（6 类×4 态） | semantic_obligations | assess_obligations | obligations+answer→status | DET | — | — | 间接（允许尾补） | — | 间接 | — | — | — |
| D17 | 检索准入 | agent_runtime | ObligationLedger.admit | tool+args→(ok,reason) | DET | **YES** | — | 间接 | — | — | — | 间接（拒满 3 次→force） | **覆盖模型宣告** |
| D18 | 技能重入 | tool_contracts | SkillReentryTracker.admit | tool+args→(ok,reason) | DET | **YES** | — | — | — | — | — | — | **覆盖模型宣告** |
| D19 | 重复调用 | agent_runtime | DuplicateGuard.decide | tool+args→reuse/execute | DET | YES（转 CACHE） | — | — | — | — | — | — | — |
| D20 | 预算 soft/hard | agent_runtime | ToolBudget.soft/hard_reached | 计数→bool | DET | — | — | — | — | — | — | hard→**YES** | forced 轮只放行 read |
| D21 | 无增益收口 | agent_runtime | no_gain_verdict | streak→warn/force | DET | — | — | — | — | — | — | **YES** | — |
| D22 | 充分性收口 | agent_runtime | sufficiency_verdict | complexity+计数→force | DET | — | — | — | — | — | — | **YES** | — |
| D23 | 核验义务三态 | agent_runtime | ObligationLedger.record | 结果→三态+obligations_satisfied | DET | YES（满足后全拒） | — | — | — | — | — | 间接 | — |
| D24 | 自动主文本读取 | engine_langgraph | _ensure_primary_read | state→locate+get_chapter | DET | — | **YES（代执行）** | YES（user_note/引用补发） | — | YES | — | — | **完全绕过模型** |
| D25 | 自动 websearch | engine_langgraph | tools_node 内联 | 空结果→websearch | DET | — | **YES（代执行）** | — | — | — | — | — | 模型不可见 |
| D26 | 强制路由（图/比较） | engine_langgraph | MAP_HINTS / COMPARISON 注入 | msg→SystemMessage | DET | — | 软强制 | — | — | — | — | — | — |
| D27 | 引用核验 | evidence_contract | LiveCitationSanitizer.push | 流→降级/保留 | DET | — | — | **YES（改写）** | — | — | YES | — | **覆盖模型引用** |
| D28 | 逐字引文绑定 | quote_bound | verify_quote / QuoteBoundSanitizer | 引文+span 池→state→改写 | DET | — | — | **YES（改写+追加）** | — | YES | YES | — | **覆盖模型引文** |
| D29 | 术语断言门 | reasoning_plan | TermClaimGate.push | 含术语句→改写 | DET | — | — | **YES（改写）** | — | YES（括注） | YES | — | **覆盖模型断言** |
| D30 | 终文安全 | engine_langgraph | _safety_check | 全文→替换 | DET | — | — | **YES（整答替换）** | — | — | — | — | — |

补充 2 项运行时级决策（不计入 30）：**模型错误分类**（agent_runtime.classify_model_error → 重试/graceful，DET，可终止）；**流式归属判定**（engine flush_agent：思考 or 回答，DET，可撤回=answer_retract 的前置）。

---

## 3. AUTHORITY COLLISION MATRIX（同审计报告 §5，完整版）

| 关注点 | LLM | Plan | Obligation | Admission | Evidence | Composer | Sanitizer | QuoteBound | owners | 赢家 | 真实冲突案例 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| intent | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | **3+LLM** | reasoning_plan（vi 强制改写） | 句长出处题被抬为 DEEP_SYNTHESIS（P2 修复记录） |
| tool choice | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | **3+LLM** | 模型（软强制下） | Q08 compare_views 被绕开 |
| tool necessity | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | **3+LLM** | ObligationLedger | 《论语》"库中未收录"误报 |
| tool stop | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | **5** | 最先触发的 force | T.1 入口事故（收口只看预算） |
| forced tool | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | **2** | 引擎（代执行无否决） | — |
| source need | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | **4+LLM** | 契约层（P3 排除） | 普莱希特二手书面板案 |
| claim strength | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | **7+LLM** | QuoteBound/TermGate（流式改写） | Q01/Q16 台账错位→T13-C |
| answer shape | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | **3+LLM** | 后注入者 | F02 兜底丢四层区分 |
| final text | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | **5+LLM** | sanitizer 链 + 收口区 | 校正随 retract 丢失→S2 重消费 |
| citation | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | **3+LLM** | LiveCitationSanitizer | T5 假引用渲染前降级 |
| quote | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | **2+LLM** | QuoteBoundSanitizer | 言必有中 blockquote 事故 |
| evidence usage | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 | evidence_contract | —（唯一单所有者关注点） |

---

## 4. MODULE CLASSIFICATION（完整模块表）

| 模块 | LOC | 公开职责 | 拥有状态 | 拥有决策 | 调用方 | 被调方 | 测试数 | 历史创建理由 | 当前价值 | 耦合 | 分类 |
|---|---:|---|---|---|---|---|---:|---|---|---|---|
| engine_langgraph.py | 2353 | SSE 流 + 图 + 收口 | pending/full_answer/治理对象 | D20 消费、D24/D25/D26/D30、收口编排 | agent_sse | 全部 policy 模块 | ~60 wire | H0 唯一引擎 | 协议核心 | 极高 | REWRITE_CANDIDATE（保协议） |
| agent_runtime.py | 961 | 治理单一真源 | Budget/Guard/Trace/RState/Ledger | D17/D19/D20/D21/D22/D23 | engine | — | ~25 | Phase A+P1/1.1 | 高（一半） | 高（5 套记账） | MERGE |
| reasoning_plan.py | 868 | 请求规划 | plan/verif_box 语义 | D01-D07、D29 | engine/composer | epistemic_guard(_match) | ~46 | Patch1 | 中（注入有效/分类冗余） | 高（跨模块 CLAIM_ROLES 锁） | MERGE |
| semantic_obligations.py | 221 | 义务台账 | 无（纯函数） | D16 | engine/interp | — | 8 | Phase S3 | 低（T13-C 自认词表不可靠） | 低 | DELETE_CANDIDATE（降审计） |
| interpretation_engine.py | 547 | 解释挑战+置信度 | 无 | D08/D09 | engine/composer | epistemic_guard | 25 | Phase 2 | 注入高/数值低 | 中 | MERGE（注入）+THIN（数值） |
| evidence_contract.py | 707 | 证据契约+引用核验 | JSONL 日志 | D15/D27 | engine/openai_compat | epistemic_guard | ~33 | Phase 3 | **高（产品行为）** | 高（前端面板） | KEEP |
| answer_composer.py | 575 | 结构+预算 | JSONL 日志 | D10/D11、尾补 | engine | interp/plan | 28 | Phase 4 | 注入中/尾补低 | 中 | MERGE |
| tool_contracts.py | 654 | taxonomy+重入+mermaid+净化+审计 | Tracker | D18、措辞净化、T12 审计 | engine/工具域 | — | ~40 | Phase T | 高（mermaid/extract_json）/中（重入）/低（scrubber 症状药） | 中 | KEEP + THIN |
| quote_bound.py | 429 | 逐字引文绑定 | Sanitizer 状态 | D28 | engine | evidence_spans(raw_log) | ~15 | Phase T.1 | **核验高/改写争议** | 中 | KEEP（核验）+REWRITE（改写） |
| epistemic_guard.py | 1036 | 前提/反事实/分级 | books/philo 缓存 | D12/D13/D14 | engine/plan/evidence_contract | — | 22 | Phase 1/4 | 分级高/硬编码规则零规模化 | 高（被 3 模块复用） | REWRITE_CANDIDATE（规则数据化） |
| guard.py | 216 | 限流/配额/用户上下文 | 令牌桶 | 机械拒绝 | 全路由 | auth_deps | 10 | 安全 P0 | 高 | 低 | KEEP |
| routes/agent_core.py | 388 | 数据缓存/向量/记忆槽 | 三级缓存+LRU+熔断 | 机械 | 全工具域 | — | ~5 | R2-2 拆分 | 高 | 低 | KEEP |
| routes/agent_llm.py | 110 | LLM 客户端 | 无 | 机械重试 | engine/工具域 | — | — | R2-2 | 高 | 低 | KEEP |
| routes/agent_sse.py | 62 | SSE 入口 | 无 | — | main | engine | — | R2-2 | 高 | 低 | KEEP |
| routes/agent.py | 237 | 聚合+注册表+cite/drawio | TOOLS 序 | 机械 | main/engine | 四域模块 | ~7 | R2-2 | 高 | 低 | KEEP |
| routes/agent_tools_retrieval.py | 614 | 10 检索工具 | locate 缓存 | 工具内路由 | engine/eval 域 | agent_core | ~10 | 原生/R2-2/T.1(locate) | 高 | 低 | KEEP |
| routes/agent_tools_memory.py | 646 | 5 创作工具 | per-user 记忆槽 | 工具内路由 | engine | — | ~8 | 原生 | 高 | 低 | KEEP |
| routes/agent_tools_eval.py | 822 | 15 分析工具 | HOT_TOPICS 等 | 工具内路由 | engine | retrieval 域 | ~20 | 原生/T 重构 | 高 | 中 | KEEP |
| agents.py | 399 | 哲学家注册表+人格包 | 域懒加载缓存 | 工具内路由 | engine | philo_retrieval | ~19 | PhiAgent 并入 | 高 | 低 | KEEP |
| philo_retrieval.py | 401 | 人格语料检索 | artifact 缓存 | 检索模式 | agents | — | ~10 | Phase R | 高 | 低 | KEEP |
| mcp_client.py / main.py / config.py / db.py | 485 | 基础 | — | — | — | — | — | — | 高 | 低 | KEEP |

**计数**：KEEP 13 / THIN 4 / MERGE 4 / DELETE_CANDIDATE 1（整模块级；路径级 6 类见 §5）/ REWRITE_CANDIDATE 3。

---

## 5. DELETION CANDIDATES（删除候选清单；按证据强度排序）

> 每条含：删除物 / 替代机制 / 证据 / 预估削减 / 关联测试处置。**本清单是候选，不是决定。**

| # | 候选 | 替代 | 证据强度 | 削减 | 测试处置 |
|---|---|---|---|---|---|
| X1 | `scan_interpretation` + `scan_composition` 全部尾补 hedge（engine:2108-2132） | 前置注入（已在） | 强：与注入同语料；Q01/Q16 重复尾补事故；interpretation_scan 非空时 composer 自己跳过 | ~120 行 + 2 模块尾补半区 | 10+ 条 wire 测试改断言（好回答零补正类可保留） |
| X2 | `TermClaimGate` 流式改写（reasoning_plan:751-783 + engine 接线） | verif_box 状态注入（已在） | 强：注入已表达同一约束；改写产出系统腔文本 | ~50 行 | patch1 B3 测试 3-4 条重写 |
| X3 | `QuoteBoundSanitizer` 强制转写 + `scan_final_consistency` 尾补（保留 verify_quote/audit_quotes） | 降级为审计字段 + NEAR/MEMORY_ONLY 交由模型按注入措辞 | 中：R 系列证明核验有效；但转写文本是代笔 | ~120 行 | phase_t1 D/G/H 组 ~8 条改写（核验测试保留） |
| X4 | auto-websearch（engine:1794-1826） | 模型自调 websearch（prompt 规则 6' 已有） | 强：结果不回灌模型上下文，对当轮推理零贡献 | ~35 行 | 无专项测试 |
| X5 | 终局安全网第二份 `_ensure_primary_read`（engine:1994-2010；与 agent_node 内第一份二选一） | 保留图内一份；或改"收口准入"（未读不许收口） | 中：双份冗余；"配额替代代执行"论证见审计 §11 | ~30 行接线 | test_phase_t1 私有直调 1 条 |
| X6 | `ADMISSION_REJECT_FORCE`（agent_runtime:679 + engine:312） | 准入拒绝降为提示（不伪造 ToolMessage 拒绝链） | 中：它治理的是 X7 的副作用（拒后空转）——两层互为补偿 | ~20 行 | test_reject_streak_counter 1 条 |
| X7 | `RuntimePhraseScrubber`（tool_contracts:462-517 + engine 接线） | 删除注入泄漏源（X1/X6 及拒绝文案收缩）后症状消失 | 中：症状药；有自身回归（标点误吃） | ~60 行 | 无专项（运行时措辞注入文案测试会连锁） |
| X8 | `PREMISE_RULES`+`BOOK_TITLE_RULES`+`CONCEPT_OWNER_RULES` 硬编码 13 条（epistemic_guard:168-347） | 数据文件化，或一个 verify_fact 检索工具交模型调用 | 强：13 条规则 / 403 本书 = 零规模化；同一条规则已打两轮补丁（T3/S1） | ~200 行 | regression_oldman_sea 保留（改数据源） |
| X9 | `semantic_obligations` 判定消费（保留 done 审计输出可选） | 尾补删除后唯一消费者消失（T13-C 已引入 UNKNOWN 自认不可靠） | 强：消费者消失即死代码 | ~150 行（含词表） | phase_s S3/T13-C ~8 条 |
| X10 | MAP_HINTS/COMPARISON 强制路由注入（engine:1400/1464） | system prompt 铁律 4 已有同等规则 | **弱-中：C3 有 QG2 前后 A/B 证据支持保留 compare_views 注入**——此条列为"需 Reviewer 裁决" | ~15 行 | phase_t RouterPrinciple 3 条 |
| X11 | `sufficiency_verdict` 期望表（agent_runtime:554-618） | hard budget + 义务收口 | 中：四层停止所有者之一；每档阈值无独立证据 | ~70 行 | patch1 Sufficiency 真值表 2 条 |
| X12 | `_ATTR_CUE_TAIL_RE` term 兜底剥离链（reasoning_plan:322-332） | 无（属 Semantic Regex Accretion 的最新沉积） | 信息项：它是 T.1 事故的补丁而非机制修复 | —（保留至机制更换） | patch1_1 检测短语锁 |

**合计预估**：X1-X9 全删 ≈ **−800~1,000 行直接代码 + 注入合并（profiler）再 −1,000~1,500 行**，与审计报告 §16 Option A 的 −2,500~3,000 行估计一致。

---

## 6. MULTIPLE_AUTHORITY 裁决要点（供 Reviewer 提问）

1. **为什么多 owner？** 无全局权威重划事件；六个 Phase 纵向叠加，各自为自身事故加层（每层 docstring 均可溯源到单一事故）。
2. **谁是最终 owner？** 代码事实：流内=Sanitizer 链（D27-D29），流外=engine 收口区（D24/D-MUT-*），安全=D30。模型仅在上述全部放行时为终 owner。
3. **冲突时谁赢？** 确定性规则结构性获胜——它不协商，直接改写/拒绝/替换。
4. **真实冲突案例？** 4 个已文档化（论语准入 / 87 天反向误纠 / F06 误触发 / Q01-Q16 台账错位）+ 2 个结构性（auto-read 归因倒置、auto-websearch 上下文不可见）。
