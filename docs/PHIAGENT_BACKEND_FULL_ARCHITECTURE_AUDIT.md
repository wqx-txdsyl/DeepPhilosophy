# PHIAGENT BACKEND FULL ARCHITECTURE AUDIT（AUDIT-01）

- 性质：架构审计（ARCHITECTURE AUDIT ONLY）。未修改任何 production code；本文档为唯一新增产物之一。
- 审计立场：DELETE-FIRST——任何 orchestration 层默认是 DELETE_CANDIDATE，除非能证明其存在价值。
- 核心问题：**"如果今天从零设计 PhiAgent，在保留现有数据库、语料、工具实现、Persona、Conversation、Evidence 与前端协议的情况下，我们还会不会设计出当前这套 backend orchestration？"**
- 本报告只给证据与可行性，最终裁决留给 Reviewer（见 §17）。

---

## 0. 结论速览（TL;DR）

**答案是否定的：以 DELETE-FIRST 立场重建证据后，今天从零设计不会得出当前这套 orchestration。**

当前 runtime 的事实形态是：**一个 LLM Agent + 一个由 ~6,100 行纯规则 Python 构成的影子 Agent**。后者在同一请求内：

- 用 **7 个独立子系统**分类同一个"这是什么问题"（§5）；
- 用 **7 个所有者**决定"什么时候停止检索"（§5）；
- 用 **4 条路径**代替 Main Agent 强制/自动调用工具，其中自动读取被要求"以第一人称陈述为你自己的核验动作"（§9, §15-E）；
- 在 LLM 定稿后通过 **16 段后处理管线、14 个正文修改器**继续写答案——其中 12 个可增删改语义内容（§8）；
- 维护 **5 套重叠的预算/充分性/准入记账**（RetrievalState / ObligationLedger / ToolBudget / no_gain_streak / sufficiency，§10）。

与此同时，runtime 中真正不可替代的部分恰好是**机械性的**：确定性逐字引文核验（quote_bound.verify_quote）、确定性引用核验（LiveCitationSanitizer 的查证池）、硬预算与去重缓存、安全替换、流式协议。这些是"LLM 无法自我核验记忆引文"这一真实约束的唯一解。

三方案可行性均已给出（§16）：A（保守简化）/ B（Main-Agent 持权）可行；C（整体重写 Agent loop）技术可行但性价比存疑。删除/重写候选清单见配套文档 `PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md`。

---

## 1. 冻结基线（GIT_BASELINE / CURRENT_WORKTREE）

| 项 | 值 |
|---|---|
| HEAD | `ec09e04da914d55ba3904fc5812785b2f81729f6` |
| Branch | `master` |
| WORKTREE modified files | 40（`+3890 / −521`） |
| backend modified files | 21（`+2734 / −361`，含 4 个测试文件） |
| backend 未跟踪运行时模块 | `reasoning_plan.py`(868)、`tool_contracts.py`(654)、`quote_bound.py`(429) |
| backend 未跟踪测试 | `test_patch1.py`、`test_patch1_1.py`、`test_phase_t.py`、`test_phase_t1.py` |
| backend 未跟踪文档 | `docs/PHIAGENT_*.md` 共 9 份 |
| backend Python LOC（`*.py` + `routes/*.py`） | 15,977 |
| 运行时路径 LOC（stream_lg 可达模块） | ≈12,731 |
| 工作树聚合 SHA256 digest | `716d7175ac9901ae3f57e74fcb28205739f84b0bda194606142da4c68dc000a8`（对全部 backend 跟踪+未跟踪文件逐一 sha256sum 后再聚合；仅记录，未生成 patch） |

**三个基线的区分**（禁止混淆）：

- **GIT_BASELINE**（HEAD `ec09e04da`）≈ H1 后期：已含 Phase 1-4 / Phase S / Phase A / UI-C / Thinking 管线；**不含** Patch1/1.1/T/T.1 的核心模块（reasoning_plan / tool_contracts / quote_bound 均未跟踪）。
- **CURRENT_WORKTREE**（本审计对象）= GIT_BASELINE + Patch1 + Patch1.1 + Phase T + Phase T.1。**"当前实现"只存在于工作树**，一次误操作 checkout 即丢失全部 T 系列成果。
- **HISTORICAL_RUNTIME_ARTIFACTS**：H0 事故原始现场（老人与海/西西弗对话记录、`backend/tools/_tmp/` 复现 JSONL）不在仓库中，NOT_RECONSTRUCTABLE（§2）。

---

## 2. 历史演化重建（以证据为准，非记忆）

### H0 —— Main-Agent 全权期（2026-08-14 合并 → ~08-29）

- **控制流**：LangGraph 两节点环 `agent → (tools ↔ agent)`，模型宣告工具即执行，不宣告即结束。检索 `RETRIEVAL_LIMIT=5`（柔性）/ `RETRIEVAL_HARD=8`（硬截断，曾直接丢弃已宣告调用——`ef88fde7c` 修复）。
- **Main Agent 权限**：完全自治。全部纪律只存在于 system prompt 铁律（"必须先 search_books…不得凭记忆编造引文"）——**荣誉系统，无执法**。
- **证据政策**：不存在运行时证据层。citations 面板把 search_books 前 N 条命中当作引用展示（evidence_contract.py 模块 docstring 自述的第三个核心问题）。
- **最终答案后处理**：极薄——`_strip_markers` + 安全检查 + 空答兜底 + 打字机重放。
- **已知失败**：《老人与海》87/84 天前提错误（化石：`epistemic_guard.py:170` `oldman_84_days` 规则 + `regression_oldman_sea.py` "永久保留"回归集）；《西西弗神话》越级断言（interpretation_engine docstring："太擅长证明一个漂亮观点，不够擅长检验这个观点"）；引用面板误导；流程腔与"完全正确/毫无疑问"强化措辞。
- **已知强度**：结构极简、延迟低；SSE 事件协议自 H0 起稳定沿用至今。
- 原始事故现场 NOT_RECONSTRUCTABLE（仅有护栏规则与回归集可反向佐证）。

### H1 —— 护栏+治理期（Phase 1-4 → Phase S（`fceced752`, 08-30）→ Phase A（`80cc10ccc`）→ Patch1/Patch1.1/QG2/Phase T（未提交，08-31~09-03））

- **控制流**：同一图，但权力三角化：**规则规划层（reasoning_plan）+ 准入执法层（ObligationLedger/SkillReentry）+ 模型**。
- **Main Agent 权限**：最终推理仍归模型（Phase T 宪法："Main Agent owns final reasoning"，`docs/PHIAGENT_TOOL_ARCHITECTURE.md` §0）；但**规划权上收运行时**（problem_type/complexity/核验约束由纯规则裁定并注入）。
- **工具执行政策**：宣告即执行 → 三层执法（DuplicateGuard 复用 / ObligationLedger 准入 / SkillReentryTracker 重入≤1）。
- **停止政策**：复杂度期望 sufficiency + no_gain_streak warn/force + 分项配额 + `ADMISSION_REJECT_FORCE`。
- **已知失败**：Patch1 Final Gate F01/F07/F12 配额 FAIL；《论语》事故——准入拒绝被模型误读为"库中未收录"（`PATCH1_1_REGRESSION.md` §9）；QG2 暴露专用工具"成品化"刚性（Q08/Q10/Q11/Q13/Q14）与义务台账双向错位（Q01/Q16）。
- **已知强度**：QG2 判定"机制在全新题型下泛化良好"；工具总数 63→26（−59%）；P50 延迟 25.0s。

### H2 —— T.1 运行时（当前工作树，09-03）

- **控制流**：引擎首次获得**主动执行权**——`agent_node` 内 `_ensure_primary_read`（`engine_langgraph.py:328,451`）代模型执行 locate_exact_phrase + get_chapter；图流结束另有终局安全网补读（`:1994`）与确定性补正文本。
- **证据政策**：义务三态 `SOURCE_CANDIDATE_FOUND ≠ PRIMARY_TEXT_READ ≠ EXACT_QUOTE_VERIFIED`（`agent_runtime.py:717`）；Quote Bound 逐字绑定（拼接检测、MEMORY_ONLY 不得渲染为原文）。
- **已知失败（本阶段入口）**：言必有中出处——裸「X出处」词型未命中 `_VI_ATTRIBUTION_RE` → vi=None → 核验路径整体缺席 → 模型凭记忆输出 blockquote（`PHIAGENT_PHASE_T1_SOURCE_VERIFICATION_REGRESSION.md` §0）。
- **已知强度**：R1–R8 全 PASS（含拼接诱骗、R7 零伪造）；407 tests（当时）全绿。
- **修复手段的形态**：**继续加正则**——`_VI_ATTRIBUTION_RE` 扩充 + `_ATTR_CUE_TAIL_RE` 兜底 + term 剥虚词填充词清单。这正是 Smell Gate C（Semantic Regex Accretion）的现场证据：事故的根因是"用正则理解用户意图"，修复也是再加正则。

**演化的净效果**：H0 的问题（无证据纪律）被真实修复了；但每次修复都以"新增一个规则模块/一层后处理"为形态，六轮叠加（Phase1-4 → S → A → Patch1 → 1.1 → T → T.1）后，治理层本身成了第二复杂度中心。H0→H2 的控制权迁移轨迹：**模型全权 → 模型+提示 → 运行时规划 → 运行时代执行**——最后一步（引擎代跑核验）已经越过了"治理"进入"代行"。

---

## 3. Production Runtime Decision Graph（POST /api/agent/stream_lg → SSE done）

以下是真实 production 路径（非 import 图）。`⟦C: 条件⟧` 标注条件性步骤；粗体为可改变 Agent 行为的决策点。

```
POST /api/agent/stream_lg
└─ agent_sse.agent_stream_lg
   ├─ guard.agent_guard ──────────── 限流/配额（机械拒绝）
   ├─ auth: profile → custom_instructions, language
   └─ engine_langgraph.stream_agent
      ├─ MCP 工具预热
      ├─ System prompt 组装（SYSTEM_PROMPT_LG + persona 提醒 + 语言覆盖 + 个性化指令）
      ├─ history[-20:] 回放 + user message
      ├─ ⟦C: MAP_HINTS 命中⟧ **注入"第一轮必须调 conceptual_map"**（强制工具）
      ├─ ⟦C⟧ **epistemic_guard.run_epistemic_guards** ── 前提规则表/反事实/认知层级 → 注入
      ├─ ⟦C⟧ **interpretation_engine.run_interpretation_engine** ── 解释型识别 → 多候选/类比≠等同/深度惩罚注入
      ├─ ⟦C⟧ **answer_composer.run_answer_composer** ── 结构约束 + 篇幅预算注入（生成类跳过）
      ├─ **reasoning_plan.build_plan** ── 问题类型/复杂度/核验意图/时序/关系链 → 形态+链+主张角色+来源约束+VERIFY_NOW+附录抑制 注入
      ├─ ⟦C: COMPARISON⟧ **注入"优先直接调 compare_views"**（强制工具）
      ├─ 治理状态实例化：DuplicateGuard / ToolBudget / ToolLoopTrace / RetrievalState /
      │                   ObligationLedger / raw_tool_log / verif_box / LiveCitationSanitizer /
      │                   QuoteBoundSanitizer / TermClaimGate / RuntimePhraseScrubber / SkillReentryTracker
      └─ APP.astream（LangGraph: agent ⇄ tools 环, recursion_limit=60）
         │
         ├─ agent_node（每轮）:
         │   ├─ 语言提醒注入
         │   ├─ **hard budget → HARD_BUDGET_DIRECTIVE（forced）**
         │   ├─ **soft budget → SOFT_BUDGET_HINT**
         │   ├─ ⟦C: rejected≥3⟧ **ADMISSION_REJECT_FORCE 收口注入（forced）**
         │   ├─ **no_gain_streak≥3 → 强制收口 / ≥2 → 提醒**
         │   ├─ ⟦C: 核验意图+已定位+零读取⟧ **_ensure_primary_read：代执行 locate_exact_phrase + get_chapter**
         │   │        → 结果注入 + "这就是你自己的核验动作…以第一人称陈述"
         │   ├─ ⟦C⟧ **sufficiency_verdict → warn/force 注入**（核验路径由 obligation 台账驱动；force 时可发"最后核验机会"读章引导）
         │   ├─ ⟦C⟧ **verification_injection（verif_box 状态 → 措辞约束）**
         │   ├─ ⟦C: retrieval_count≥8⟧ 旧柔性检索提示
         │   └─ LLM invoke（bind_tools, A4 重试; 耗尽→ModelCallError→graceful）
         │
         └─ tools_node（每批宣告调用）:
             ├─ **ObligationLedger.admit**（按宣告顺序逐个判定：义务满足/族耗尽/分项配额/总包络/forced 收口）
             │    └─ 拒绝 → 伪造 ToolMessage"检索准入未通过…（未执行≠库中无此书）"
             ├─ **SkillReentryTracker.admit**（13 个 reasoning/generation 技能重入治理）
             │    └─ 拒绝 → 伪造 ToolMessage"技能重入被拦截"
             ├─ **DuplicateGuard.decide**（同参只读 → reuse 缓存结果）
             ├─ 工具执行（TOOL_TIMEOUT=90s, 轮内重试 1; 失败→FALLBACK_MAP 提示换工具）
             ├─ **⟦C: search_books 空⟧ 自动 websearch**（经 admit 准入；结果不回灌模型上下文）
             ├─ RetrievalState.register（low_gain 语义重复判定）
             ├─ ObligationLedger.record（read_execs/义务满足/EXACT_QUOTE_VERIFIED 置位）
             ├─ raw_tool_log 登记（含 T9 伪条目：专用工具 citations 伪装 search_books 入池）
             ├─ budget/trace 计数；⟦C⟧ verif_box 状态一次性计算
             └─ 工具结果流式事件 + interpret_thinking tool_note

      图流结束后（stream_agent 收口区, engine_langgraph.py:1914-2353）:
      ├─ synthesis thinking 摘要（LLM 生成, ≤3 条/invocation）
      ├─ 尾部 flush：phrase→term→citation→quote→rationale 净化器残余按链序补发
      ├─ ⟦C: 正文<60字符⟧ **短答兜底再生成**（_final_answer_directive 四要素, 再调一次 LLM）
      ├─ ⟦C⟧ auto-read 事件补发 + tool_note
      ├─ ⟦C: 核验义务未满足+零读取⟧ **终局安全网：再跑一次 _ensure_primary_read → user_note 尾补**
      ├─ ⟦C: 义务满足+逐字命中+正文无引用⟧ **补发"（原典核验：「…」已核验【《书》·章】。）"**
      ├─ 净化器残留二次放行
      ├─ **QB.audit_quotes + scan_final_consistency**（G 强确定性降级 / H verify-later 更正）→ 尾补
      ├─ **epistemic 重消费**（S2：校正随 retract 丢失 → 重新尾补"（补充：先纠正一个前提——…）"; 反事实边界缺失 → 补发）
      ├─ 预算扫描（超预算 → 抑制后续结构提示）
      ├─ **scan_interpretation** → 措辞级尾补（类比≠等同 / tier hedge）
      ├─ **scan_composition** → 措辞级尾补（强化措辞 hedge / 结论先行 nudge）
      ├─ **build_evidence_contract**（retrieved⊇candidate⊇used; citations=used 投影; P3 二手排除）
      ├─ sanitize_citations 终检（log-only 断言）
      ├─ semantic_obligations assess（义务台账随 done 输出）
      ├─ **safety 整答替换**（self_harm → SAFETY_REPLY, citations 清零）
      ├─ **done 事件**（citations/evidence/tool_calls/suggestions/plan/verification/obligation_ledger/
      │   quote_bound/tool_ownership/temporal/retrieval_state/… 20+ 字段）
      └─ 并行后处理：LLM reasoning_summary（失败→确定性兜底）+ LLM suggestions（失败→规则模板 _suggest_next）
```

---

## 4. Decision Authority Inventory（决策点清单）

> 完整 30 项决策点矩阵（含全部字段）见配套 `PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md` §2。此处列最承重的 12 项。

| ID | 问题 | Owner | 类型 | 可阻断工具 | 可强制工具 | 可改终文 | 可撤回终文 | 可在 LLM 后加文本 |
|---|---|---|---|---|---|---|---|---|
| D01 | 这是什么问题？ | reasoning_plan.classify_problem | 规则 | — | 间接 | 间接（形态注入） | — | — |
| D02 | 这是什么问题？（同一问题的第二裁决） | interpretation_engine.InterpretationChallenger | 规则 | — | — | 间接 | — | — |
| D03 | 这是什么问题？（第三裁决） | answer_composer.classify_complexity | 规则 | — | — | 间接 | — | — |
| D04 | 这是什么问题？（第四裁决） | epistemic_guard（前提/反事实检测） | 规则 | — | — | 注入+尾补 | — | YES |
| D05 | 需要什么证据？ | reasoning_plan + engine MAP/COMPARISON 注入 | 规则 | — | **YES**（MAP/compare_views 强制提示） | — | — | — |
| D06 | 能不能调用这个工具？ | ObligationLedger.admit | 规则 | **YES** | — | 间接 | — | — |
| D07 | 能不能重复这个技能？ | SkillReentryTracker.admit | 规则 | **YES** | — | — | — | — |
| D08 | 现在证据够了吗？ | sufficiency_verdict + ObligationLedger + ToolBudget + no_gain + LLM | 规则+LLM | YES | — | — | — | — |
| D09 | 什么时候停止？ | LLM + 7 个运行时所有者（见 §5.2） | 混合 | YES | — | — | — | — |
| D10 | 这个说法可信到什么程度？ | LLM + EpistemicClaimClassifier + ConfidenceCalibrator + verif_box + TermClaimGate + QuoteBound + STRONG_CERTAINTY 尾补 | 规则+LLM | — | — | **YES（可改写句子）** | — | YES |
| D11 | 最终答案应该是什么形态？ | FORM_DIRECTIVES + composer + interpretation + epistemic + _final_answer_directive | 规则 | — | — | 注入+尾补 | — | YES |
| D12 | 最终答案能不能原样显示？ | 14 个 mutator（§8） | 规则 | — | — | **YES** | **YES（answer_retract）** | **YES（9 处 append）** |

**确定性标注**：除 D08/D09/D10 含 LLM 参与外，全部决策点为 DETERMINISTIC 纯规则。整个治理层没有一次 LLM 调用——它是一个确定性决策系统在治理一个概率性系统。

**同一问题被重复决定的最严重实例**：D01-D04（意图），D08-D09（停止），D10（主张强度，7 个所有者），D11-D12（形态与终文）。

---

## 5. Authority Collision Matrix（权威碰撞矩阵）

图例：`0`=无所有者，`1`=单一所有者，`**2+**`=多所有者。→=冲突时赢家（按代码调用序，非声明）。

| 认知决定 | LLM | Plan(reasoning_plan) | Obligation(ledger+reentry) | Admission(budget/no_gain/suff) | Evidence(evidence_contract) | Composer | Sanitizer | QuoteBound | 赢家与真实冲突案例 |
|---|---|---|---|---|---|---|---|---|---|
| intent（问题类型） | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | **2+ owners（LLM+3 个规则分类器）**。赢家=reasoning_plan（vi 命中时强制改写 problem_type/complexity，`reasoning_plan.py:829`）。冲突案例：句长≥60 的出处题曾被抬为 DEEP_SYNTHESIS（P2 修复记录） |
| tool choice（选哪个工具） | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | **2+**。赢家=模型，但 MAP_HINTS/COMPARISON 注入构成软强制；Q08（compare_views 被绕开）是模型与注入路由的真实冲突 |
| tool necessity（要不要调） | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | **2+**。赢家=ObligationLedger（执行前取消）。真实冲突：《论语》事故——admission 判"不必要"，事实是必要 |
| tool stop（何时停） | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | **2+（5 个所有者）**。赢家=最先触发的强制收口；T.1 事故即"收口决策只看预算不看义务"的结构盲区 |
| forced tool（必须调什么） | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | **2+**。赢家=引擎（_ensure_primary_read 直接代执行，模型无否决权） |
| source need（需要什么来源） | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | **2+**。P3 约束（PRIMARY_ONLY）在契约层否决模型的引用选择 |
| claim strength（可信度） | 1 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | **2+（最多所有者的关注点）**。赢家=QuoteBound/TermGate（流式改写）。真实冲突：Q01/Q16 台账错位（正文已表达仍判 UNSATISFIED → 重复尾补）→ T13-C 引入 UNKNOWN 态 |
| answer shape（答案形态） | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | **2+**。赢家=后注入者（注入顺序：composer→plan→…，同批 SystemMessage 叠加 7 个来源） |
| final text（终文） | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | **2+**。赢家=sanitizer 链（模型无知情权）；answer_retract 可撤回已流出文本 |
| citation（引用） | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 0 | **2+**。赢家=LiveCitationSanitizer（流式降级），evidence_contract 终检 |
| quote（逐字引文） | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | **2+**。赢家=QuoteBoundSanitizer（MEMORY_ONLY → 强制转 paraphrase） |
| evidence 用量（检索≠使用） | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 1 owner（唯一干净的关注点） |

**汇总**：12 个关注点中 **10 个为 MULTIPLE_AUTHORITY**。

- 为什么多个 owner？历史叠加：每个 Phase 只对自己_phase 的问题负责，没有一次全局权威重划（各模块 docstring 可证）。
- 谁是最终 owner？**按代码执行序**：流内=Sanitizer 链，流外=引擎收口区；模型只在"强制收口不触发且净化器放行"时才是终owner。
- 冲突时谁赢？结构性答案：**确定性规则永远赢**——它不需要"决定"，它直接改写。
- 是否已有真实冲突案例？有，四个已文档化：《论语》准入误判（1.1 §9）、《老人与海》反向误纠（S1 referent）、F06 反事实误触发、Q01/Q16 义务台账错位。

---

## 6. 模块级审计

> 逐模块完整表见配套 AUTHORITY_MAP §4。此处为核心 12 模块摘要。分类：KEEP / THIN / MERGE / DELETE_CANDIDATE / REWRITE_CANDIDATE。

| 模块 | LOC | 状态拥有 | 决策拥有 | 历史理由 | 当前价值 | DELETE 难度 | 分类 |
|---|---:|---|---|---|---|---|---|
| `engine_langgraph.py` | 2353 | pending/live 流状态、full_answer、全部治理对象实例化 | 流式归属判定、收口管线编排、auto-read、auto-websearch、安全替换 | H0 唯一引擎 | 流式协议+工具环不可替代；但 2353 行中约 40% 是 6 个 Phase 的接线与收口补丁 | 极难（协议核心） | **REWRITE_CANDIDATE**（保协议，重排内部） |
| `agent_runtime.py` | 961 | ToolBudget/DuplicateGuard/Trace/RetrievalState/ObligationLedger | 预算、去重、重试、终止、准入、核验义务 | Phase A + Patch1/1.1 | Trace/重试/去重=高价值；**5 套记账重叠**（见 §10） | 中 | **MERGE**（保 3，并 2，删 2） |
| `reasoning_plan.py` | 868 | plan dict、verif_box 语义 | 意图分类×2、复杂度、时序、关系、核验、措辞门 | Patch1（B 系） | 部分注入（VERIFY_NOW/来源约束）有效；分类器与 answer_composer/interpretation 三重重叠 | 中 | **MERGE**（单一 profiler） |
| `semantic_obligations.py` | 221 | 义务台账 | 义务履行判定（词表法） | Phase S S3 | T13-C 已承认词表法不可靠（引入 UNKNOWN）；现在主要产出审计状态 | 低 | **DELETE_CANDIDATE**（并入 profiler 或降为审计） |
| `interpretation_engine.py` | 547 | 解释裁决、置信度 | 解释型识别、多候选、类比≠等同、深度惩罚 | Phase 2 | 注入部分=好 prompt；**数值置信度引擎只喂尾补 hedge，从不到达用户** | 中 | MERGE（注入保留、数值引擎 THIN） |
| `evidence_contract.py` | 707 | 证据契约 | 引用核验、used 语义、claim 绑定 | Phase 3 | **引用面板=产品行为，KEEP**；LiveCitationSanitizer 是 T.1 止血核心 | 难（有 wire 测试+前端） | KEEP（sanitize_citations 终检降为断言已正确） |
| `answer_composer.py` | 575 | 结构裁决、篇幅预算 | 结构注入、强化措辞尾补、预算扫描 | Phase 4 | 预算注入可保留；**尾补 hedge 与 interpretation 尾补重叠**（scan_composition 自己都有跳过逻辑） | 中 | MERGE（注入并入 profiler，尾补列 DELETE_CANDIDATE） |
| `tool_contracts.py` | 654 | taxonomy、重入、map 渲染 | 重入准入、措辞净化、所有权审计 | Phase T | mermaid renderer/extract_json=纯机械 KEEP；RuntimePhraseScrubber 是"注入泄漏"的症状药；ownership audit=观测 | 中 | KEEP + 内部 THIN |
| `quote_bound.py` | 429 | 引文审计 | 逐字核验、拼接检测、流式转写、终检尾补 | Phase T.1 | **verify_quote/audit_quotes=全系统唯一能对抗"凭记忆引原文"的确定性机制，KEEP**；Sanitizer 的强制转写与 scan_final_consistency 尾补为语义改写（REWRITE） | 难 | KEEP（核验）+ REWRITE_CANDIDATE（改写部分） |
| `epistemic_guard.py` | 1036 | 前提裁决 | 3+2+8 条硬编码事实规则、反事实门、claim 分级 | Phase 1/4 | claim 分级被 evidence_contract 复用（KEEP）；**13 条硬编码事实规则对 403 本书语料是零规模化能力**；反事实门 F06 误触发史 | 中 | REWRITE_CANDIDATE（数据驱动化或交还模型+工具） |
| `routes/agent_core.py` + `agent_llm.py` + `agent_sse.py` + `agent.py` | 797 | 数据缓存/向量索引/限流外（guard.py） | 无认知决策 | 拆分重构 R2-2 | 干净的基础设施 | — | **KEEP** |
| 工具域（retrieval/memory/eval, 30 工具）+ agents.py | 2681 | 工具内会话状态 | 工具内路由（修改意图词等） | 原生 | 工具实现本身是资产（任务要求保留） | — | KEEP（工具内部 auto-retrieval 见 §9 备注） |

**分类计数**：KEEP 7 组 / THIN 4 / MERGE 4 / DELETE_CANDIDATE 6（多数是"某模块内的路径"而非整文件）/ REWRITE_CANDIDATE 3。整文件可安全删除的：无——但**可删除的代码路径合计约 1,800–2,400 行**（详见 MAP §5）。

---

## 7. 规则增长审计（Rule Growth）

| 指标 | 值 |
|---|---:|
| REGEX_POLICY_COUNT | **227**（MECHANICAL ≈118 / SEMANTIC ≈109） |
| KEYWORD_POLICY_COUNT | **≈62**（SEMANTIC ≈48，含 ≈170 词的关系词表、≈110 别名的跨体系表、≈170 主题的 DOCUMENTED_TOPICS） |
| ENUM_DECISION_COUNT | **30** 个行为枚举 |
| AUTO_TOOL_PATHS | **12**（引擎级 3 + 工具内部 9，另有 1 处伪日志注入） |
| FINAL_TEXT_MUTATORS | **14** |
| POST_LLM_CORRECTION_PATHS | **16** 段 |
| FALLBACK_PATHS | **26** 条静默替代分支 |
| "if … contains …" 判定分支 | ≈72 |

语义类正则的完整 pattern 原文清单见子审计留档（本文档压缩引用最关键 10 条）：

- 认知类（问题在哪）：`_VI_WORDING_RE`、`_VI_ATTRIBUTION_RE`（T.1 事故修复即扩此正则）、`_ATTR_CUE_TAIL_RE`、`_TERM_PRESENCE_RE`、`_YESNO_RE`/`_NARROW_RE`；
- 决策类（行为随句子变）：`_VI_PRIMARY_RE`（决定二手证据是否被契约层排除）、`_NAV_ASK_RE`（决定是否允许原典路径附录）、`_ITERATION_MARKS`（决定技能能否重入）、`_MAP_HINTS`（决定是否强制 conceptual_map）；
- 改写类（直接改正文）：`_UNCONDITIONAL_CONFIRM`×3（TermClaimGate 句界改写）、`VERIFY_LATER_RE`（触发"更正/边界"尾补）、`STRONG_CERTAINTY_RE`（触发确定性降级尾补）。

**MECHANICAL vs SEMANTIC 的分界结论**：HTML 转义、围栏剥离、引用标记解析 = 机械，应保留。**"出处$ → SOURCE_ATTRIBUTION"类 = 认知**，它们在用词法模拟语义理解。109 条语义正则的存在本身就是 Smell Gate C 的定量证据：系统的自然语言理解边界 = 正则库的边界，每次事故都在加宽这条边界而非更换机制（T.1 的修复方式是最直接的证据）。

**"不要因为测试存在就认为规则合理"**：`test_patch1_1.py` 用 8 条短语级测试锁定 `_VI_*` 正则行为——测试锁死的是正则的现行为，不是"用户问出处会得到正确核验"这个行为本身（后者由 4 条真实语料测试覆盖）。正则的召回漏洞（言必有中事故）正是在测试全绿的状态下进入生产的。

---

## 8. Final Answer Ownership Audit（用户最后看到的答案是谁写的？）

从 LLM final draft 到用户屏幕的完整变更链：

```
LLM final draft
→ [流式, 每 token] _visible_text（XML/控制标签剥离 — 机械）
→ RuntimePhraseScrubber（15 个治理短语删除 — 防泄漏, 字面删除）
→ LiveCitationSanitizer（未核验【《书》·章】→《书》一般提及 — 语义降级改写）
→ QuoteBoundSanitizer（MEMORY_ONLY blockquote → "据通行理解，…；但我尚未逐字核验。" — 语义改写+追加）
   （NEAR → 追加"（与库中原文近似，非逐字）"）
→ TermClaimGate（含目标术语句 → 句界改写为"…（该固定措辞是否逐字出现，未能核验）" — 语义改写）
→ [轮界] answer_retract（撤回已流出文本 — 删除）
→ [收口区, 按序] 短答兜底再生成（<60字符 → 整段重新生成）
   → auto-read user_note 尾补 / 已核验引用可见性补发（确定性 APPEND 含【《书》·章】正文）
   → QB.scan_final_consistency 尾补（确定性边界/更正文本）
   → epistemic 校正尾补 + 反事实边界尾补
   → interpretation hedge 尾补 / composer hedge 尾补
→ safety 整答替换（唯一可整体替换）
→ done + openai_compat 传输层【《书》·章】→ markdown 链接（格式）
```

| 层 | CAN_DELETE | CAN_REPLACE | CAN_APPEND | CAN_CHANGE_MEANING |
|---|---|---|---|---|
| XML/控制标签剥离 | YES | — | — | NO（机械） |
| RuntimePhraseScrubber | YES | 悬挂标点 | — | 边际（删除即改变句读） |
| LiveCitationSanitizer | 引用格式 | 引用→一般提及 | — | 间接（正式引用资格=语义） |
| QuoteBoundSanitizer | blockquote 格式 | 原文→paraphrase | YES（核验边界句） | **YES** |
| TermClaimGate | — | 句界改写 | YES（括注） | **YES** |
| answer_retract | YES（整段） | — | — | — |
| 9 处收口尾补 | — | — | **YES** | **YES（新增实质结论，如"已读取《X》核验完成"）** |
| 短答兜底再生成 | 整段 | **整段重写** | — | **YES** |
| safety 替换 | 整段 | **整段替换** | — | YES（安全动机，可辩护） |

**POST_LLM_SEMANTIC_MUTATORS = 12**（14 个 mutator 中扣除纯机械 3 个——filter_xml/strip_markers/strip_control_tags——再加兜底再生成与传输层不计）。

**判定**：理想状态是"post-processing 只做 mechanical validation / formatting / safe removal"。当前状态偏离：runtime 会（a）把模型的原文献定改写为 paraphrase 并替模型声明核验边界；（b）在答案尾部以系统措辞追加实质结论（包括替模型宣告"已读取并核验"）；（c）改写含术语的断言句。**这些是哲学内容层面的代笔**，不是格式净化。其中（b）最危险：它把"谁完成了核验"的归因从系统转移到模型（注入词："这就是你自己的核验动作……以第一人称陈述，不得提及系统消息"）。**标 HIGH_RISK_ARCHITECTURE（针对语义改写子集；机械核验子集不在此列）。**

---

## 9. Tool Authority Audit（38 工具执行链）

Main LLM 宣告 tool call 后，执行链上的全部处置能力：

```
宣告 → [ObligationLedger.admit] DENY（执行前取消, 伪造 ToolMessage）
     → [SkillReentryTracker.admit] DENY（同 purpose 重入）
     → [DuplicateGuard] CACHE/REUSE（同参只读复用, 不执行）
     → [ToolBudget hard] CANCEL（forced 轮只放行 get_chapter, FORCED_READ_CAP=2）
     → 执行（TOOL_TIMEOUT=90s; 重试 1; 失败 → FALLBACK_MAP 提示）
     → [RetrievalState.register] 标记 low_gain（影响后续 admit 与 sufficiency）
     → [ObligationLedger.record] 置位义务状态（影响后续一切准入与收口）
     → [T9 伪条目] 专用工具 citations 伪装 search_books 注入 raw_tool_log（REPLACE_RESULT 的证据池版本）
```

**REWRITE_ARGS：无**（T7 明确"工具真实入参不改写"）。**AUTO_CALL：引擎 3 条 + 工具内部 9 条**（§7）。**REPLACE_RESULT：1 条**（伪日志注入；另有 DuplicateGuard 缓存回放）。

MECHANICAL vs SEMANTIC DENIAL 统计：

- **MECHANICAL DENIAL（可辩护）**：无效参数（`_safe_bid`/`_int_arg`）、未知工具、超时、exact-duplicate 复用、失败重试限制、hard 预算总量天花板、限流（guard.py）≈ **7 类**。
- **SEMANTIC DENIAL（认知判断）**：`obligation_satisfied`（"证据已够"）、`query_family_exhausted`（"同义改写无新证据"）、`low_gain`（"信息增益不足"）、`search_cap/read_cap/meta_cap/websearch_cap` 按复杂度分档（"这类问题不需要这么多检索"）、`skill_reentry_undeclared`（"没有依据再调一次"）、forced 轮非读取禁入 ≈ **7 类**。

**结论**：语义拒绝与机械拒绝 1:1。语义拒绝的每一个都有真实事故的双面记录：拒得太松→F01/F07/F12 配额 FAIL；拒得太紧→《论语》"库中未收录"误报、拒后空转（ADMISSION_REJECT_FORCE 是为治理拒后空转而生的第三层）。一个需要第三层来治理第二层副作用的机制，是补偿栈的典型形态（§15-H）。

---

## 10. Evidence Architecture Audit（证据状态图）

当前系统中同一 invocation 内并存 ≥16 种证据相关状态：

```
                    ┌─ 描述工具执行（B 类） ─────────────────────────────┐
retrieved（evidence_contract 候选池）   budget.cls（unique/duplicate/retry）
candidate（与正文对齐）                 info_gain（new/empty/low_gain/repeat）
used / used_count                      trace.calls（执行轨迹）
secondary_excluded                     read_chapters / search_execs / read_execs
                                       family.execs / family.low_gain
                    ┌─ 描述模型解释（C 类） ─────────────────────────────┐
claim.epistemic_type（9 类）            claim.role（5 角色）
claim.direct_evidence / SPECULATION 禁绑
tier（strong/moderate/tentative/analogical, 数值置信度）
                    ┌─ 控制模型行为（D 类） ─────────────────────────────┐
obligations_satisfied ──控制 admit 拒绝 + 收口 force + 兜底安全网
verification_state（VERIFIED_EXACT/SEMANTIC/NOT_FOUND）──控制措辞注入 + TermClaimGate 改写
quote state（EXACT/NEAR/MEMORY_ONLY）──控制流式改写 + 终检尾补
source_candidate_found / primary_text_read / exact_quote_verified ──控制 auto-read 触发
low_gain ──控制 no_gain_streak ──控制强制收口
relevant_ids / rel_met ──控制 sufficiency
```

**COUPLING_SMELL 标记**（同一状态同时承担 B/C/D）：

1. **`obligations_satisfied`**：既是事实描述（读到原文了吗=B），又是解释判定（`_wording_evidence_in` 用归一词法判定"措辞证据在手"=C），又直接控制准入拒绝、强制收口、终局安全网（=D）。**这是全系统耦合最重的单一布尔**——T.1 事故的根因（"收口决策只看预算不看义务"）和 T.1 修复的副作用（义务满足后一切检索禁入）都压在它身上。
2. **`low_gain`**：由 2-gram shingle 重叠（B/C 混合——"结果重合"是事实，"无信息增益"是解释）直接决定族准入拒绝与 no_gain 强制收口（D）。
3. **`quote state`**：逐字核验（B）驱动正文改写（D）。

理想架构中 B/C/D 应分离：事实状态（读没读、命中没命中）可供任何消费者查询；但"够不够"（D）应归属单一收口所有者。

---

## 11. "Agent 本来就会做"功能审计（核心）

对每个认知控制模块回答：如果删除它、只在 system prompt 里告诉 Main Agent 研究纪律，能否完成 80%+ 功能？

| 模块/机制 | 纯 prompt 能替代？ | 证据 | remaining 20% 值得复杂度吗？ |
|---|---|---|---|
| 问题分类→形态注入（B7/COMPOSER/INTERP 三套） | **YES** | 全部产物是 SystemMessage 文本；LLM 自分类能力远强于 `_YESNO_RE`；三套分类器互相重叠本身就是冗余证明 | 不值得三套。值得一套收敛的 profiler（或直接并入 system prompt） |
| 预算/停止（soft/hard/no_gain/sufficiency/admission 五层） | **基本 YES（成本上限除外）** | H0 观测：成功回合中位 0-2 工具；长尾 21-26 次——问题真实存在，但 hard budget 一个数就能截断长尾 | hard ceiling + duplicate 复用值得；sufficiency 期望表+族阈值+分项配额的精细度未被证据支持（每层都有误伤事故） |
| 引用核验（LiveCitationSanitizer/evidence contract） | **NO** | 模型无法自我核验记忆引用——H0 事故本体；deterministic 查证是唯一解 | **值得。这是 runtime 不可让渡的核心 20%** |
| 逐字引文绑定（quote_bound 核验+拼接检测） | **NO** | R8 拼接诱骗通过；R7 零伪造——只有确定性扫描能做到 | **值得（核验部分）**；改写部分可交还模型 |
| 引擎 auto-read（_ensure_primary_read + 终局安全网） | **大体 YES（换机制）** | T.1 事故根因是"义务无人兜底"；但兜底≠代执行。admission 已有 read 配额——拒绝收口直到 read_execs≥1 即可，模型会自己调 get_chapter | 代执行不值得：代价是归因混淆+伪日志+终局安全网两层复杂度；**用"不许收口"替代"替你做"可删两条 auto 路径** |
| 自动 websearch（search 空时） | **YES** | 模型已有 websearch 工具+prompt 规则 6' 明示主动调用；自动版结果**不回灌模型上下文**——对当轮推理零贡献，只喂前端卡片与证据池 | 不值得。DELETE_CANDIDATE |
| Epistemic 前提规则（3+2+8 条硬编码） | **YES（泛化问题上）** | 13 条规则只覆盖 3 个数字+2 个书名+8 个概念；语料 403 本。T3/S1 两轮补丁都为同一条 87 天规则 | 不值得代码形态。可数据化为一个 verify_fact 工具 |
| 反事实门 | **YES（注入部分）** | F06 误触发史；触发判定靠 `_CONTEMPORARY_OBJECT_RE` 词表 | 注入保留（prompt 价值），误触发治理不值得独立门 |
| 术语核验门 TermClaimGate（改写句） | **YES** | verif_box 状态注入已告诉模型"不得说原文明确写道"；改写是第二保险，产出的是系统腔文本 | 不值得：改写文本是"（该固定措辞是否逐字出现，未能核验）"——这句话由模型说出与由 runtime 替它说出，用户信任度不同 |
| semantic_obligations 词表判定 | **YES** | T13-C 自己承认词表不可靠（UNSATISFIED→UNKNOWN） | 不值得 |
| interpret/composer 尾补 hedge | **YES** | 注入已含同样要求；尾补只触发于模型无视注入时——此时追加一句"（补充：…）"是弱修复 | 边际。 DELETE_CANDIDATE |
| 篇幅预算注入 | **YES** | 纯 prompt 引导 | 一条注入可保留（THIN） |
| skill 重入治理 | **大体 YES** | Q11 三连调是真实问题；但 `_ITERATION_MARKS` 含"如果/假设"——用户说"如果换一个前提"即触发 USER_REQUESTED_ITERATION，词表法脆弱 | 简单计数上限值得；justification 词表不值得 |
| DuplicateGuard / trace / 重试 / graceful | **NO** | 成本与可靠性基础设施 | 值得（KEEP） |

**净结论**：runtime 的不可让渡核心 = **确定性证据核验（引用+逐字引文）+ 成本/可靠性基础设施 + 机械净化 + 安全**。认知控制（分类/充分性/措辞/形态/尾补）的 80% 可由 prompt + 单一收口规则实现；当前以 ~6,100 行规则代码持有它，其复杂度未被 remaining 20% 证明。（本审计未运行新实验——证据来自既有 traces/QG2/R 系列回归与代码事实；未做 production 修改。）

---

## 12. 真实案例 Decision Trace（C1–C6）

> 每例：Main Agent wanted / Runtime allowed / denied / auto-called / rewrote / final mutation / 有益干预 / 有害干预 / 多余干预 / 删层后果。依据：代码路径 + 已文档化回归（R/QG2/F 系列记录）。

### C1 言必有中出处（SOURCE_ATTRIBUTION，T.1 入口事故 + R1-R8 回归）
- **Main Agent wanted**：检索→（H0/H1 形态）凭记忆给 blockquote。
- **Runtime allowed**：search≤2、read≤2、web≤1、meta≤1（分项配额）。
- **Runtime denied**：义务满足后一切检索；forced 轮非读取调用。
- **Runtime auto-called**：locate_exact_phrase 全库逐字扫描 + get_chapter（若模型未读）→ 注入原文段落 + "这就是你自己的核验动作"。
- **Runtime rewrote**：无（正文）；但未读时尾补 user_note、已读无引用时补发"（原典核验：「…」【《书》·章】。）"。
- **有益**：R1 阻止记忆 blockquote；R7 零伪造；R8 拒拼接。
- **有害**：归因混淆（模型被要求把系统动作说成自己的）；locate 冷启动 ~9s；R4 型 prefer_absent 依赖用户提到《书》。
- **多余**：终局安全网与 agent_node 内 auto-read 是同一机制的两份（工作树内两处调用）。
- **若删 auto-read 层（保留 read 配额+义务收口）**：SAME→WORSE 风险有限——R1 型事故的直接根因是"义务可为空"，配额+禁收口已封死该路径；UNKNOWN（需 UAT 验证模型是否稳定服从"不读不许收口"）。

### C2 深度哲学综合题（DEEP_SYNTHESIS）
- wanted：多轮检索+长论证。allowed：search≤6、总≤10、soft 8/10、hard 20/24；sufficiency 在 executed≥8 且无增益时 force；深题豁免提前低增益收口。
- 注入叠加：form+chain+claim_role+composer×2+budget+（若解释型）interp×3 ≈ **最多 9 条 SystemMessage**。
- final mutation：composer/interp hedge 尾补、（若含引文）QuoteBound、（若强确定性+MEMORY_ONLY）G 边界尾补。
- **有益**：结构不散（QG2 12/13 全局门通过）。**有害**：注入堆叠稀释注意力（DIAGNOSTIC 曾记录"思考块出现于工具执行之后"）。**多余**：interpretation 与 composer 的 hedge 双保险。
- **若删 composer/interp 尾补层**：SAME（注入仍在）；若连注入并删：WORSE（无替代纪律）→ 建议 MERGE 而非裸删。

### C3 compare_views 比较题（QG2 Q08 / QG2 案例）
- wanted：H1 形态自检索再自写对比；T 后被路由注入"首选直接调 compare_views"。
- allowed：compare_views 计入 COMPARISON search 配额 3；重入受 tracker 管辖。
- auto-called：compare_views 内部 3× search_books（模型只宣告 1 次）；其 citations 以伪 search_books 条目入核验池（T9）。
- rewrote：工具产物内删除"正题/反题/合题"标签（eval:563）。
- **有益**：Q08 合规性调用被 scaffold 化修复；类比≠等同注入+AVE_HEDGE 拦"本质完全一样"。
- **有害**：模型视角的"一次调用=三次检索"不可见，预算口径双重记账。
- **多余**：analogy_boundary 在注入、 obligation 词表、AVE_HEDGE 三处各有实现。
- **若删 compare_views 强制路由注入**：WORSE（Q08 回归风险）——此注入是少数有 A/B 证据（QG2 前后）支持的干预。

### C4 Socratic 单问（QG2 Q14 / T6）
- wanted：旧工具一次生成 4 轮。Runtime：ONE CALL = ONE QUESTION（工具内部重构）+ form 注入 + prompt 铁律 14"不得在 next_question 之外追加自己的问题"。
- **注意**：这条纪律只有 prompt 执法——runtime 不校验最终回答的问题数（tool_ownership_audit 只审使用度）。是全部案例中 runtime 退出、模型自治的唯一一例，也是运行良好的一例（**"prompt 执法足够"的正面证据**）。
- 兜底：JSON 解析失败 → 正则抽第一问 → 固定问题模板（fallback #14）。
- **若删 socratic 相关治理**：SAME（本来就只有 prompt 在管）。

### C5 Nietzsche temporal persona（B5/Patch1 T 系列）
- wanted：以某时期视角答。Runtime：temporal 正则检测（年份/时期词）→ temporal_directive 注入（要求调 philosopher_period、分期取证、禁文风模拟、禁"助手无历史视角"推脱）→ done 输出 temporal_state 审计（period_tool_called 只记录不执法）。
- fallback：philosopher_period 未指定时期 → 默认晚期 snapshot。
- **有益**：时期路由从"文风扮演"升为"分期取证"。**多余**：`_AGENT_PERIOD_YEARS` 只有 nietzsche 一行——为单智能体建了一层检测-路由-审计机制。
- **若删检测层只留注入模板**：SAME→UNKNOWN（检测同时服务审计字段）。

### C6 无需工具的简单解释（CONCEPT_EXPLANATION, 零工具）
- wanted：直接回答。Runtime 全链仍然运转：分类→form 注入→composer×2+budget 注入→（若词表误触）epistemic/interp 注入→回答→流式净化链→composer scan→obligations assess→done 20+ 字段。
- **有害**：一个"什么是存在主义"级问题可承受最多 ~8 条系统注入；`_INTERP_CUES_EXT` 含"本质/意义"——日常词即可触发解释型管线。
- **多余**：零工具回合的 evidence/quote/obligation 全套 machinery 空转（异常面=fallback #20/#21 所在）。
- **若删全部认知治理**：BETTER（此 case 无任何一层产生正价值）；**通用化警告**：这正是"分层治理对简单问题的税"。

---

## 13. Complexity Metrics

| 指标 | 值 |
|---|---:|
| backend Python LOC | 15,977（含非 agent 路由） |
| runtime-path LOC | ≈12,731 |
| runtime 模块数 | 24（engine 1 + policy 11 + 路由 6 + 基础 6） |
| 状态对象 | 12/invocation（DuplicateGuard, ToolBudget, Trace, RetrievalState, ObligationLedger, raw_tool_log, verif_box, CitationSan, QuoteSan, TermGate, PhraseScrub, ReentryTracker） |
| 枚举 | 30 |
| 语义正则 | 109 |
| 策略表 | ≈20（预算/配额/期望/税表/白名单/税级） |
| fallback 路径 | 26 |
| 终文 mutator | 14 |
| auto-tool 路径 | 12 |
| 可终止工具循环的位置 | 7（LLM 自停、hard、no_gain force、admission-reject force、sufficiency force、recursion_limit、义务满足 admit 全拒） |
| 可强制工具执行的位置 | 5（MAP 注入、COMPARISON 注入、auto-read、终局安全网、auto-websearch） |
| 分类用户意图的位置 | **7**（classify_problem、detect_verification_intent、detect_term_presence、InterpretationChallenger、composer classify_complexity、epistemic 检测、MAP/比较路由） |

**DECISION_OWNERS_PER_CONCERN**：intent=7；tool stop=7；claim strength=8（LLM/Classifier/Calibrator/verif_box/TermGate/QuoteBound/STRONG_CERTAINTY尾补/obligation 词表）；final answer=14（mutator 数）；tool necessity=2（模型+ledger）；citation=3。

LOC 不是判断，但作为架构证据：**治理层（reasoning_plan+agent_runtime 治理半区+semantic_obligations+interpretation+composer+epistemic+tool_contracts 治理半区+quote_bound 改写半区）≈ 6,100 行，约为工具实现与数据基础设施之外全部 runtime 的一半**；而其中真正不可让渡的核验机制（LiveCitation + verify_quote + 审计）≈ 600 行。

---

## 14. Test Architecture Audit（426 tests）

| 类别 | 数量 | 占比 |
|---|---:|---:|
| BEHAVIOR（用户可观测） | 57 | 13.4% |
| CONTRACT | 233 | 54.7% |
| IMPLEMENTATION（锁内部） | 78 | 18.3% |
| REGRESSION（历史事故） | 30 | 7.0% |
| PROMPT/REGEX LOCK | 28 | 6.6% |

- 无真实 LLM 测试在 CI；真实行为验收靠文档留档的带外 UAT（27 次，QG2/R 系列）。
- **TESTS_THAT_PROTECT_BEHAVIOR**（87 条 = BEHAVIOR+REGRESSION）：老人与海永久回归集、F12/《论语》准入场景、拼接诱骗、graceful recovery 族、引用面板 used 投影、零伪造断言等。**这些测试保护的是行为，重构后应存活并迁移。**
- **TESTS_THAT_PROTECT_IMPLEMENTATION**（106 条 = IMPLEMENTATION+PROMPT LOCK）：最僵化的三处——①冻结计数/白名单（`TOOLS==30`、`TOOL_TAXONOMY==38`、图拓扑 `{agent,tools}`、SSE 事件白名单 12 种，三处文件联动）；②reasoning_plan 46+ 条短语级分类锁；③注入文案逐字锁（answer_composer 5 条 + epistemic/interp 各 1 条 + 收口提示文案等，改文案=10+ 条连锁重写）。
- 典型 PROMPT LOCK：`test_injection_bans_default_skeleton` 逐字断言六个禁用块标签；`test_four_jump_chain_detected_and_penalized` 锁死置信度减分公式 `0.50-0.10-0.05*3`；`test_ensure_primary_read_triggers_and_satisfies` 直调私有 `_ensure_primary_read`。
- **结论**：61% 的测试保护实现而非行为。任何 Option A/B 重构的测试迁移成本主要来自这 106 条 + reasoning_plan 锁；行为层 87 条可整体存活。另有 233 条 CONTRACT 要求合并模块时保留原公共签名或提供适配层。

---

## 15. Architecture Smell Gates（逐项证据）

| Gate | 判定 | 最强证据 |
|---|---|---|
| A. Distributed Cognitive Authority | **YES** | intent owners=7；stop owners=7；claim-strength owners=8（§5/§13）；10/12 关注点多所有者 |
| B. Shadow Agent | **YES** | 规则层独立完成：分类→规划→准入→强制→停止→写答案全循环，无一次 LLM 调用（engine 注入序列 + 收口区 16 段）；reasoning_plan docstring 自述"问题结构规划…驱动运行时各环节" |
| C. Semantic Regex Accretion | **YES** | 109 条语义正则；T.1 修复=再扩 `_VI_ATTRIBUTION_RE`+新增 `_ATTR_CUE_TAIL_RE`；PREMISE_RULES 逐事故硬编码 |
| D. Post-hoc Semantic Repair | **YES** | 9 处确定性尾补含实质结论（"已读取并核验…【《书》·章】"、"更正：相关原文已核验，无需再查"）；TermClaimGate/QuoteBoundSanitizer 语义改写 |
| E. Hidden Tool Execution | **YES** | auto-read 伪造成模型自己的调用（thought="出处核验：定位并读取…"+注入词"这就是你自己的核验动作"）；auto-websearch 结果不回灌模型；T9 伪 search_books 日志；工具内部 9 条隐式检索 |
| F. Policy/Evidence Coupling | **YES** | `obligations_satisfied` 一布尔兼任 B/C/D（§10）；`low_gain` 同理 |
| G. Test-Driven Ossification | **YES** | 106 条实现/文案锁；三处跨文件计数冻结；`test_ensure_primary_read_triggers_and_satisfies` 直调私有函数 |
| H. Compensation Stack | **YES** | 六栈有档：硬截断→补跑→tool_cancel→ADMISSION_REJECT_FORCE；准入拒绝→《论语》误报→措辞契约→治理语泄漏→RuntimePhraseScrubber→标点误吃→条件清理；live 流出→retract→校正丢失→S2 重消费→重复尾补→semantic_obligations 去重；rationale 标签→解析器→未闭合泄漏→引擎侧生成器替代；citation sanitizer 只管正式引用→记忆 blockquote→QuoteBound→scare-quote 误捕→口径收紧 |

**8/8 触发。** 其中 E（归因倒置）与 D（系统代笔）是用户信任层面的风险，A/H 是维护成本层面的风险。

---

## 16. Target Architecture From First Principles（三候选）

先回答第一性责任问题：**在保留 DB/语料/38 工具/Persona/Conversation/Evidence schema/SSE 协议的前提下，runtime 最少需要什么？**

最小责任集（不可让渡）：① 工具执行与资源天花板；② 会话/证据状态存储；③ **确定性引用与逐字引文核验**（模型无法自证记忆）；④ 机械净化与安全；⑤ 流式协议。

### OPTION A — Conservative Simplification（保留 LangGraph，删/并 policy）
- **KEEP**：LangGraph 环、SSE、DuplicateGuard、hard budget、trace/重试/graceful、LiveCitationSanitizer、quote_bound 核验+审计、evidence_contract、安全、工具域。
- **DELETE**：auto-websearch、终局安全网（与 auto-read 二选一）、TermClaimGate 改写、QB/interp/composer 全部尾补、ADMISSION_REJECT_FORCE（改准入为"提示而非拒绝"）、RuntimePhraseScrubber（随注入泄漏源消失）、PREMISE_RULES 硬编码（数据化）、interpretation 数值置信度、semantic_obligations（降为审计或删）。
- **REWRITE**：reasoning_plan+composer+interp+epistemic 注入 → 单一 profiler（一个模块、一套分类、一组注入）；5 套记账 → ObligationLedger+hard budget 两套。
- 风险：低-中（保留下来的机制都有回归测试）；复杂度削减 ≈ **−2,500~3,000 LOC / −40% 治理层**；能力影响：接近零（删的多为第二保险与审计）；测试迁移：改写 ~100 条（28 文案锁 + 78 实现锁的多数）+ reasoning_plan 短语锁整批迁移。

### OPTION B — Main-Agent-Owned Orchestration（LLM 持权，runtime 只留机械层）
- LLM 拥有：reasoning、tool choice、研究延续、停止、答案结构（现有 prompt 铁律 5/6/13/14 已含全部纪律——C4 socratic 证明 prompt 执法可以足够）。
- Runtime 只拥有：工具执行、状态、证据存储、**核验降级（流内 sanitizer 保留）**、硬天花板、安全、流式。
- **DELETE**（在 A 基础上追加）：ObligationLedger 语义拒绝（保留机械去重与 hard 上限）、SkillReentry 词表治理（保留简单计数）、sufficiency 期望表、no_gain 词表 force、MAP/COMPARISON 强制注入、auto-read（改用"未读不许收口"的收口准入——注：这是唯一保留的认知规则，因为它对应 T.1 事故的直接根因，且是"拒绝"而非"代行"）。
- 风险：中-高——H0 三大事故形态（过度检索/凭记忆引用/越级断言）中，第二个已被核验降级层封死，第一个由硬上限+重复复用封死，第三个回到 prompt+注入承担（QG2 证据：注入有效）。**能力回退风险集中在"研究主动性"**（H0 时代模型该追索不追索的对面问题）。
- 复杂度削减 ≈ **−4,000 LOC / runtime ≈ 减半**；测试迁移 ≈ 150 条改写。

### OPTION C — Orchestration Rewrite（保 API/DB/语料/38 工具/Evidence/Persona/SSE，重写 Agent loop）
- 内容 = B 的目标态 + engine_langgraph 内部重排（2353 行拆为 loop/sanitize/closeout 三段）。
- 边际收益 vs B：主要是可维护性；边际成本：60+ 条 wire 测试重接 + 8 个文件的 `_FakeApp` 适配 + 前端联调。
- **结论：技术可行，但相对 B 的增量收益不支撑其成本。B 即"C 的效果、A 的路径"。**

| 方案 | KEEP | DELETE | REWRITE | 风险 | 复杂度削减 | 能力影响 | 测试迁移 |
|---|---|---|---|---|---|---|---|
| A | 全部机械层+核验+注入 | 尾补/auto/词表 force/硬编码规则 | 注入合并为 profiler | 低-中 | −40% 治理层 | ≈0 | ~100 条 |
| B | 机械层+核验+收口准入 | +语义拒绝/强制注入/auto 执行 | 同上+loop 职责重划 | 中 | ≈−50% runtime | 回退风险集中于主动性 | ~150 条 |
| C | 协议+工具+数据 | 同 B | +engine 三段化 | 中-高 | 同 B+可维护性 | 同 B | ~150+60 wire |

---

## 17. Reviewer Decision Package

### ARCHITECTURE_FACTS（全部可在代码/文档中复核）

1. PATCH1/1.1/T/T.1 全部实现仅存在于未提交工作树（+2,734/−361 backend 行，3 个核心模块未跟踪）。
2. Runtime=LLM 环 + 确定性规则层；规则层无一次 LLM 调用，却在 12 个认知关注点中的 10 个持有多所有者权威。
3. 单请求最多叠加 ~9 条来自 7 个规则模块的 SystemMessage；每轮再叠加最多 5 条预算/核验注入。
4. LLM 定稿后存在 16 段后处理；14 个 mutator 中 12 个可增删改语义内容；1 处可整答替换；1 处可撤回已流出文本。
5. 引擎有 12 条模型未请求的工具/检索执行路径；自动读取被要求以模型第一人称复述；1 处伪 search_books 日志注入。
6. 5 套预算/充分性记账并存；`obligations_satisfied` 单布尔耦合事实/解释/控制三职责。
7. 语义正则 109 条、语义词表 48 个、行为枚举 30 个、fallback 26 条——每个数字都有 file:line 证据。
8. 测试 426 条中 61% 锁实现/文案；三处跨文件计数冻结；真实 LLM 行为验收全部在 CI 之外（文档 UAT）。
9. 8/8 Smell Gates 触发；6 条补偿栈均有文档化事故链。
10. 不可让渡核（确定性引文/逐字核验、硬预算、去重、安全、流式、机械净化）合计 ≈600-900 行，运行记录良好（R1-R8 全过、QG2 12/13、零伪造断言成立）。
11. 四个已文档化的权威冲突案例（论语准入、87 天反向误纠、F06 误触发、Q01/Q16 台账错位）中，三个的修复方式是"再加一层规则"。
12. C4（socratic）是唯一 runtime 完全退出、仅 prompt 执法的案例——运行良好。

### 可行性判定（供 Reviewer 裁决，非本审计结论）

- **OPTION_A_FEASIBLE = YES**（低-中风险；有回归测试护轨；测试迁移成本明确）。
- **OPTION_B_FEASIBLE = YES with conditions**（条件：保留核验降级层 + 收口准入替代 auto-read + 分阶段 UAT 对照 QG2/R 系列；风险集中于研究主动性回退）。
- **OPTION_C_FEASIBLE = YES but not recommended**（相对 B 增量收益 < 增量成本）。

### 遗留疑问（Reviewer 可要求补充的证据）

- Option B 下模型主动性是否回退：需要 A/B UAT（同题集对照 H0/QG2/ R 系列指标），本审计未运行新实验（遵守不改 production 约束）。
- 尾补删除对用户观感的影响：需要前端面板数据（`backend/data/*.jsonl` 有原始记录可供离线分析）。

---

## 18. 交付物

| 文件 | 内容 |
|---|---|
| `docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md` | 本文档（完整审计 §0-§19） |
| `docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md` | runtime graph / authority matrix / 30 决策点全字段清单 / 模块分类 / 删除候选清单 |

## 19. Final Receipt

```
AUDIT_01 = COMPLETE
HEAD = ec09e04da914d55ba3904fc5812785b2f81729f6
WORKTREE_CHANGED_FILES = 40 modified (+3890/−521) + 3 untracked runtime modules + 4 untracked test files + 9 untracked docs
BACKEND_LOC = 15,977 (backend/*.py + routes/*.py)
RUNTIME_PATH_LOC = ≈12,731
RUNTIME_MODULES = 24
DECISION_POINTS = 30（全字段清单见 AUTHORITY_MAP §2）
INTENT_DECISION_OWNERS = 7
TOOL_STOP_OWNERS = 7
TOOL_FORCE_OWNERS = 5
FINAL_ANSWER_MUTATORS = 14
POST_LLM_SEMANTIC_MUTATORS = 12
SEMANTIC_REGEX_POLICIES = 109
AUTO_TOOL_PATHS = 12
FALLBACK_PATHS = 26
MULTIPLE_AUTHORITY_CONCERNS = 10 / 12 关注点
SHADOW_AGENT_COMPONENTS = 4（规划器 / 准入执法 / 收口补正管线 / 引擎代执行器）
COMPENSATION_STACKS = 6
KEEP_MODULES = 7 组（基础设施/工具域/核验/安全/流式/trace可靠性/mermaid）
THIN_MODULES = 4（篇幅预算注入 / ownership audit / 数值置信度 / source_nav 抑制）
MERGE_MODULES = 4（reasoning_plan+composer+interp+epistemic 注入 → 单 profiler；RetrievalState+ToolBudget+sufficiency → 1-2 套记账；citation 三层核验口径统一）
DELETE_CANDIDATES = 6 类路径（auto-websearch / 终局安全网双份 / TermClaimGate 改写 / 全部尾补 hedge / RuntimePhraseScrubber / PREMISE_RULES 硬编码 + semantic_obligations 判定）
REWRITE_CANDIDATES = 3（engine 收口区 / epistemic 规则数据化 / quote_bound 改写半区）
BEHAVIOR_TESTS = 87（BEHAVIOR 57 + REGRESSION 30）
IMPLEMENTATION_LOCK_TESTS = 106（IMPLEMENTATION 78 + PROMPT/REGEX LOCK 28）
OPTION_A_FEASIBLE = YES
OPTION_B_FEASIBLE = YES（附条件）
OPTION_C_FEASIBLE = YES（不推荐）
CODE_MODIFIED = false
REPORT = docs/PHIAGENT_BACKEND_FULL_ARCHITECTURE_AUDIT.md
AUTHORITY_MAP = docs/PHIAGENT_BACKEND_DECISION_AUTHORITY_MAP.md
```

**STOP——按任务要求，审计到此为止，不开始重构。**
