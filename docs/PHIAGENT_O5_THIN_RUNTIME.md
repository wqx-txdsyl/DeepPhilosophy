# PhiAgent O5 — Thin Runtime / Mechanical Core Consolidation

> 阶段: O5（Orchestration Reset 第 5 刀——不再改变"谁做决定"，把失去认知职责的
> Runtime 压缩成薄、可解释、可维护的机械执行层）
> 分支: `refactor/phiagent-main-agent-orchestration`
> BASE_SHA: `2de12b4ecbd5372ecba6258f99a7f3ca5ded14e1`（O4 FINAL PASS, ACCEPTED_SHA）
> Reviewer: GPT-5.6 Sol ｜ 模型: GLM-5.3-Flash (Reasoning Max)
> 前置: O1/O2/O3/O4 FINAL REVIEW 全 PASS

---

## 0. 目标架构（§21 AFTER Runtime Graph，按真实代码）

```
Request
  ↓
Context Builder（_build_context_messages, 单源一条 SystemMessage；hard 预算 = 机械状态位）
  ↓
Main Agent LLM
  ↕
Tool Executor（五道机械闸：硬上限 / EXACT_DUPLICATE_REUSED / 未知工具 / 超时 / 重试+FALLBACK）
  ↕        ── EvidenceState（纯事实登记: read_chapters / primary_text_read /
  ↕          source_candidate_found / search_execs / read_execs）
Final Validator（final_validator: EMPTY + check_citations + check_quotes, intent-free）
  ├─ PASS → Publisher（token 逐字发布）
  └─ FAIL → same Main Agent repair（≤2, 耗尽零发布）
  ↓
SSE Publisher（12 类事件词表）
```

图中已不存在：ObligationLedger / Planner / Sufficiency / InterpretationJudge /
Composer / PremiseVerifier（§21 验收 ✓）。

## 1. Runtime Residual Inventory（§1, 9 文件全文审计）

分类口径 M/D/P/L/C/X, 全表见执行记录。核心发现:

- **13+ 死符号**: `_derive_read_info`(31 行孤儿)、engine `TOOLS_BY_NAME`、engine `_sse`、
  `RATIONAL_STATS`(write-only)、`pending["reasoned"]`(旧 thought_stream 门控残骸)、
  `AgentState.model_retries`(write-only)、`VERIFY_LATER_RE/_OPEN_RE`(零消费者)、
  `_CITE_REPLACE_ZH/EN`(零消费者)、routes/agent.py `SYSTEM_PROMPT+_SYS_TOOL_LIST`
  (~165 行死 prompt, **本次最大单体死代码**)、openai_compat thought 死映射、
  `ObligationLedger.term`(失去生产喂入口)、`_QUOTE_NORM`(与 norm_q 逐字节重复)、
  `RetrievalState.mark_round` 组(引擎从未调用)
- **8 处 legacy 兼容分支**: docstring 陈旧闸门声明、done.live_citation_sanitize 静态
  审计 dict、NIETZSCHE_PROMPT 铁律 9(与铁律 0 工作笔记纪律**直接冲突**——哲学家智能体
  拿不到 SYSTEM_PROMPT_LG 的铁律 0)、SYSTEM_PROMPT_LG 规则 14"会被系统拦截"
  (宣称已删除的 SkillReentryTracker, 失实)、openai_compat thought 死映射等
- **验证逻辑重复 9 处**(D1–D9): 归一化/证据池构建/句切/使用判定/引用 regex 副本

## 2. 执行清单落地

### DELETE（16 项全清, DEAD_PRODUCTION_SYMBOLS 16 → 0）
上表全部死符号 + NIETZSCHE_PROMPT 铁律 9 删除(编号错乱顺手修复——philosopher 轮
自此走通 thinking_summary 工作笔记通道, O1 契约对哲学家生效) + SYSTEM_PROMPT_LG
规则 14"会被系统拦截"失实宣称收敛 + tools_node/flush_agent/模块 docstring 修正 +
done `live_citation_sanitize` 字段(静态审计 dict, 前端零消费)。

### MERGE（§2 ObligationLedger → EvidenceState）
`ObligationLedger` 整类删除（不再叫 obligation——存的是 WHAT HAPPENED, 不是
WHAT MUST HAPPEN; 未造 EvidenceObligationLedger 换皮）。新建 `EvidenceState`
（evidence_contract.py）: `record_search()/record_read()` 纯事实登记 + `snapshot()`;
done 删 `obligation_ledger` 键, 事实并入 **done.evidence.facts**（前端只读
retrieved_count, 加键安全）。`_QUOTE_NORM` 删除（归一真源 = quote_bound.norm_q）。

### 去重（§6, VALIDATION_DUPLICATION_SITES 4 → 0）
- **D1** 归一化: 单一真源 quote_bound.norm_q ✓（随 _QUOTE_NORM 删除）
- **D4** raw_tool_log 解析: evidence_contract 新增唯一 `build_evidence_pool()`
  （全保真: entry_index/kind/text 不截断）, `_extract_candidates` 与
  `quote_bound.evidence_spans` 均改为对池的薄适配（准入条件/snippet 截断/units
  分段逐字段保真）——字段映射只维护一份
- **D6** 句切: 分类器 method 版删除, 统一模块级 `_split_sentences`
- sanitize_citations 裁剪为**只读 audit**（rebind/downgrade 改写分支删除,
  sanitized_text 本就被丢弃; actions 词表收敛为 verified/unverified）
- 其余 5 处为口径漂移风险（/api/cite._norm、evaluation_suite 离线副本等）, 记录不强制

### MOVE
`_match_philosopher` 族 + `EPISTEMIC_LANGUAGE/language_bound` → evaluation_suite
（离线评分专用, 生产模块内零调用）。

## 3. SSE 事件词表（§9/§10）

生产实际发射 **12 类**: `status / thinking_summary / thinking_summary_delta /
tool_start / tool_note / tool / tool_cancel / token / validation_failed / error /
done / suggestions`。

```
thought_stream / thought / answer_retract / reasoning_summary / auto_read
→ 引擎零发射（T7 实证; 前端兼容分支属前端侧清理）
```

三通道归属干净（§10）: thinking_summary = Main Agent 公开工作笔记;
tool_note = runtime 机械状态（initiated_by=runtime_mechanical）; answer =
校验后的 Main Agent 终稿。`validation_failed` 保留发射（repair 耗尽的干净收口通道）。

## 4. 硬上限行为（§11）

审计结论: BASE 上硬上限到达 → 1 次机械 forced 补跑（新宣告被
RESOURCE_CEILING_REACHED 拒绝并回传）→ 截断, `HARD_CEILING_INVOCATIONS BEFORE =
AFTER = 1`, 无额外 closeout invocation 可省——维持现状（T9 断言无 ghostwrite、
无语义 closeout）。

## 5. Main-Agent Formatting Discipline（§12, 已入主策略）

SYSTEM_PROMPT_LG 铁律 2 新增: blockquote（> 引用块）只用于打算作为原文/出处文本
呈现的内容; 自己的分析/转述/小结用普通正文——引用块里每句话都会被当逐字原文核对。
凭记忆的措辞不得作为逐字原文呈现。**通用格式语义, 不按问题类型触发**（T10）。

## 6. Tool Capability Guidance（§10, O4-RP1 延续）

search_books/get_book_detail 的编号型作品定位指引保持在位（capability description,
无 MUST 式措辞）。

## 7. Tests

新增 `backend/tests/test_o5_thin_runtime.py`（18 用例, T1–T12 全覆盖 + 补充）:
EvidenceState 事实登记 / 死 term 状态 / 死验证策略符号 / validator 完好 / 工具权威
完好 / 无伪工具记录 / 事件词表 / 三通道归属 / 硬上限机械回包 / 格式纪律 / persona
完好 / repair 完好。

**测试迁移**: 零删除——全部按 §14 OLD→behavior 映射（死符号用例改负断言/
`TOOLS_BY_NAME`→`TOOLS_LG`/`model_retries`→`trace.model_retries`/ledger 断言→
EvidenceState.facts）。

## 8. §15/§16 Metrics

```
RUNTIME_PATH_LOC            BEFORE 3762 → AFTER 3576（engine 1697→1672 /
  agent_runtime 468→391 / quote_bound 257→251 / evidence_contract 731→691 /
  routes/agent 237→201 / openai_compat 181→179; final_validator 191 不变;
  evaluation_suite[离线] +108 接收迁移副本）
ENGINE_LANGGRAPH_LOC        1697 → 1672
AGENT_RUNTIME_LOC           468 → 391
RUNTIME_STATE_CLASSES       4（DuplicateGuard/ToolBudget/ToolLoopTrace/EvidenceState
  + AgentState TypedDict/RationaleParser/PhraseScrubber; 义务语义 = 0）
RUNTIME_POLICY_CLASSES      0
PUBLIC_EVENT_TYPES_EMITTED  12（零 dead 发射）
LEGACY_COMPAT_BRANCHES      8 → 0
DEAD_PRODUCTION_SYMBOLS     16 → 0
VALIDATION_DUPLICATION_SITES 4 → 0

IRREDUCIBLE_CORE_ESTIMATE   ≈ 1000–1250 LOC（tool executor/流式/validator/
  evidence/事实登记/AR 机械治理/safety）
CURRENT_RUNTIME_OVERHEAD    ≈ 2000–2200 LOC——构成: ~30% 注释/docstring、
  ~350 行 UAT 审计块与双语 prompt 文本（necessary complexity）、
  EpistemicClaimClassifier 离线化（future cleanup, 唯一值得立项项）
```

## 9. Tests

`pytest backend/tests -q` → **350 passed / 0 failed**（331 基线 + 18 O5 新用例 +
1 用例拆分; 零测试删除, 全部 §14 映射）。单跑: O1 causal 13 / O1-RP1 thinking 4 /
O2 ownership 23 / O3 authority 15 / O4 collapse 20 / O5 thin runtime 18 — 全绿。

## 10. Live UAT

见 §12 RECEIPT（复用七用例脚本; U1 重点观察 blockquote 格式失败是否改善）。

## 11. O6 Preparation（§22 冻结指标清单）

O6 = 整次 reset 的综合质量验收（非架构开发）。建议冻结:

```
架构真相: AFTER_RUNTIME_GRAPH（本文档 §0）+ CONTEXT_BUILDER 单源 + 事件词表 12 类
工具/研究行为: AVG_TOOLS / 工具序列形态 / churn 率（对照 O3-U2/O4-RP1-U1 基线）
出处核验: PRIMARY_READ / CITATION_INTEGRITY / QUOTE_INTEGRITY / blockquote 误用率
深度综合: U2/U3 类 2000+ 字答案例 ANSWER_DEPTH
persona: U3/U5 尼采/时期上下文
多轮: 追问/修改场景回归
延迟: P50/P95（各阶段对照: O2 46.5/68.6 → O3 32.9/128.9 → O4 35.9/184.4）
引用/引文完整性: validator 真阳性率 + 误报率
错误行为: 耗尽零发布 / transport error / 安全替换
thinking UX: 工作笔记/活动注记/终稿三通道渲染
```

### O5 build 实测（n=7, 同脚本）

| 用例 | 结果 | validator 拒因（真阳性） | tools | 时长 |
|---|---|---|---|---|
| U1 言必有中出处 | **PASS 一次通过** | —（§12 格式纪律生效: O4-RP1 同题耗尽 → 本次首轮通过） | 5 | 30.7s |
| U2 康德vs密尔 | 耗尽零发布（repairs=2） | NEAR 未标注 ×4（覆盖率 0.63–0.75, 语料译本与流行措辞有差）+ blockquote 误用 ×2 | 27 | 153.1s |
| U3 尼采 persona | **PASS**（repairs=1 后发布 3083 字; philosopher 工作笔记通道已走通） | ok | 23 | 197.6s |
| U4 生造词出处 | 耗尽零发布（repairs=2） | 模型绕引《哲学研究》语言批判段落作答: NEAR 未标注 ×2 + blockquote 误用/未支持引用 ×2（章节范围标注不匹配证据池） | 17 | 74.9s |
| U5 zero-tool | **PASS** | ok | 0 | 13.1s |
| U6 宰予昼寝 | **PASS** 一次通过 | ok | 7 | 24.4s |
| U7 柏拉图vs尼采真理观 | 耗尽零发布（repairs=2） | UNVERIFIED_CITATION（「真实的世界」章节名不匹配）+ blockquote 误用（自有小结排成引用块） | 23 | 140.6s |

```
PUBLICATION_SUCCESS_RATE = 4/7（U1/U3/U5/U6）
VALIDATOR_REPAIR_RATE = 3/7 走入 repair（全部真阳性拒绝, 零误报, 零泄漏, 零 retract）
语义拒绝 = 0; 语义 retract = 0（全用例）

§19 source-attribution UAT success = U1 PASS（且 O4-RP1 同题耗尽 → 本轮一次通过,
  §12 blockquote 格式纪律直接见效）; U2/U7 的出处密集场景仍暴露
  "记忆措辞当逐字呈现"的模型策略问题——按裁定记录, 不加 gate
```

## 12. FINAL RECEIPT

```
================================================================
O5 FINAL RECEIPT — Thin Runtime / Mechanical Core Consolidation
================================================================
O5 = READY_FOR_REVIEW
BASE_SHA = 2de12b4ecbd5372ecba6258f99a7f3ca5ded14e1
CODE_SHA = （随本提交回填）
HEAD_SHA = （= REMOTE_SHA, push 后回填）
REMOTE_SHA = （push 后回填）
CHANGED_FILES = engine_langgraph.py / agent_runtime.py / quote_bound.py /
  evidence_contract.py / routes/agent.py / routes/openai_compat.py /
  routes/agent_tools_retrieval.py(描述) / agents.py(铁律 9)/ evaluation_suite.py(离线副本)
  + tests 适配 + 新增 backend/tests/test_o5_thin_runtime.py

TOOL_DECISION_OWNER = MAIN_AGENT（不变）
AFTER_RUNTIME_GRAPH = Request → Context Builder(单源) → Main Agent ↕ Tool Executor
  (机械五闸) ── EvidenceState(事实) → Final Validator → PASS Publisher / FAIL
  same-agent repair(≤2, 耗尽零发布) → SSE Publisher(12 类事件)
  ——图中无 ObligationLedger/Planner/Sufficiency/InterpretationJudge/Composer/PremiseVerifier ✓

RUNTIME_PATH_LOC = 3762 → 3576
ENGINE_LANGGRAPH_LOC = 1697 → 1672
AGENT_RUNTIME_LOC = 468 → 391
RUNTIME_STATE_CLASSES = 4（+TypedDict/RationaleParser/PhraseScrubber; 义务语义=0）
RUNTIME_POLICY_CLASSES = 0
PUBLIC_EVENT_TYPES_EMITTED = 12（零 dead 发射）
LEGACY_COMPAT_BRANCHES = 8 → 0
DEAD_PRODUCTION_SYMBOLS = 16 → 0
VALIDATION_DUPLICATION_SITES = 4 → 0（D1 归一单源 / D4 证据池单源 build_evidence_pool /
  D6 句切统一 / sanitize 裁剪为只读 audit）

EXACT_DUPLICATE_GUARD = KEEP   GLOBAL_HARD_CEILING = KEEP(20/24, 机械)
HARD_CEILING_INVOCATIONS_BEFORE = 1   HARD_CEILING_INVOCATIONS_AFTER = 1（无额外
  closeout invocation 可省——T9 实证机械回包无 ghostwrite）
FAKE_TOOL_RECORDS_AFTER = 0（pseudo 条目均带 tool_internal 溯源, T6）
MAIN_AGENT_FORMAT_DISCIPLINE = 铁律 2 新增"blockquote == 拟呈现原文"通用格式规则
  （§12 授权, 不按问题类型触发）——U1 实证生效（O4-RP1 同题耗尽 → 本次一次通过）
IRREDUCIBLE_CORE_ESTIMATE = 1000–1250 LOC
CURRENT_RUNTIME_OVERHEAD = 2000–2200 LOC（~30% 注释/docstring、~350 行 UAT 审计块与
  双语 prompt = necessary; EpistemicClaimClassifier 离线化 = future cleanup）

T1..T12 = 全 PASS（test_o5_thin_runtime.py 18 用例）
U1 = PASS 一次通过（blockquote 纪律生效, 5 tools, 30.7s）
U2 = 耗尽零发布（NEAR 未标注 ×4 + blockquote 误用 ×2, 全真阳性）
U3 = PASS（尼采 persona, philosopher 工作笔记通道走通, 3083 字）
U4 = 耗尽零发布（模型绕引《哲学研究》语言批判——引用/标注全不匹配证据池, 真阳性）
U5 = PASS（zero-tool 13.1s）
U6 = PASS（一次通过）
U7 = 耗尽零发布（UNVERIFIED_CITATION + blockquote 误用, 真阳性）
PUBLICATION_SUCCESS_RATE = 4/7（U1/U3/U5/U6）; VALIDATOR_REPAIR_RATE = 3/7（全部
  真阳性拒绝, 零误报零泄漏零 retract; 语义拒绝 = 0）
source-attribution UAT success = U1 PASS（§12 纪律直接见效; U2/U7 出处密集场景
  仍暴露"记忆措辞当逐字"模型策略问题——记录, 不加 gate）

ENGINE_COGNITIVE_AUTO_TOOLS = 0
SEMANTIC_TOOL_CONTROL_EFFECTS = 0
RUNTIME_SEMANTIC_MUTATORS = 0
RAW_REASONING_PUBLIC = 0

O1_CAUSAL_TESTS = 13/13   O1_THINKING_SAFETY_TESTS = 4/4
O2_OWNERSHIP_TESTS = 23/23   O3_TOOL_AUTHORITY_TESTS = 15/15
O4_COLLAPSE_TESTS = 20/20   O5_THIN_RUNTIME_TESTS = 18/18
FULL_TEST_COMMAND = pytest backend/tests -q（未排除任何测试）
COLLECTED = 350  PASSED = 350  FAILED = 0  SKIPPED = 0
增量解释: 331 → 350 = +18 O5 新用例 + 1 用例拆分（零删除, 全部 §14 映射迁移）

AFTER_RUNTIME_GRAPH = 见文档 §0（无 ObligationLedger/Planner/Sufficiency/
  InterpretationJudge/Composer/PremiseVerifier ✓）

O6_PREPARATION = 文档 §11 冻结指标清单（架构真相/工具研究行为/出处核验/深度/
  persona/多轮/延迟/引用完整性/错误行为/thinking UX）

REPORT = docs/PHIAGENT_O5_THIN_RUNTIME.md
KNOWN_ISSUES = 3 条（文档 §13）: ①publication rate 本轮 4/7——三例耗尽均真阳性,
  模型"记忆措辞当逐字 + blockquote 误用"策略问题, 走 prompt 层迭代不加 gate
  ②EpistemicClaimClassifier 离线化为 future cleanup ③部分验证口径漂移风险
  （/api/cite._norm、evaluation_suite 离线副本）已记录

STOP —— O5 边界内工作完成, 未开始 O6。最终 PASS 由独立 Reviewer（GPT-5.6 Sol）签发。
```
