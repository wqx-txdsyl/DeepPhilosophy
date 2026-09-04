# PhiAgent O2 — Final Answer Ownership / Validator → Main-Agent Repair Loop

> 阶段: O2（Orchestration Reset 第 2 刀）
> 分支: `refactor/phiagent-main-agent-orchestration`
> BASE_SHA: `c7dc4c7c940d5af2fcb0909b5e66fd8fe7c882f4`（O1 Final PASS 收口点）
> Reviewer: GPT-5.6 Sol ｜ 模型: GLM-5.3-Flash (Reasoning Max)
> 前置: O1_FINAL_REVIEW = PASS（O1 已解决"谁决定下一步行动"——本阶段解决"谁写最终答案"）

---

## 0. 核心命题

O2 把最终答案的自然语言所有权归还 Main Agent：

```
Main Agent
   ↓ Final Candidate（内部缓冲, 不公开）
Deterministic Validator（final_validator.py, 纯检测）
   ├─ PASS  → publish（候选文本此刻才首次公开）
   └─ FAIL  → 结构化 ValidationIssue[] → 中性反馈 → 同一个 Main Agent
                ↓ repair invocation（绑定完整工具集, 可继续研究——仍遵守 O1 因果契约）
              新 Final Candidate → 再校验（机械上限 MAX_VALIDATION_REPAIRS = 2）
```

不变量（AUTOMATED 断言）:

| 不变量 | 值 | 断言位置 |
|---|---|---|
| FINAL_TEXT_OWNER | main_agent | done.final_ownership（T5/T7） |
| SEMANTIC_MUTATORS_AFTER | 0 | 引擎无任何改写路径（结构保证）+ T1/T5/T7 |
| RUNTIME_FACTUAL_APPENDS_AFTER | 0 | emit_append 已删除 + T7 |
| FINAL_RETRACT_SEMANTIC_USE | 0 | 引擎零 answer_retract 发射点 + T10 |
| INVALID_FINAL_PUBLICLY_STREAMED | false | 缓冲发布架构 + T1/T8 |
| MAX_VALIDATION_REPAIRS | 2 | T10 |
| MAIN_AGENT_FINAL_OWNERSHIP_RATE | 100% | T5/T7（发布文本逐字 == 模型候选） |

---

## 1. BEFORE — Final Mutation Trace（BASE_SHA 实测路径清单）

BASE 上 final 文本从 LLM 产生到公开, 途经以下 runtime 改写/追加通道（逐项核实于
production path, 非 grep）:

| # | 通道 | 位置（BASE） | 行为 | 分类 |
|---|---|---|---|---|
| 1 | `LiveCitationSanitizer.push` | evidence_contract.py:609 | 未核验 formal citation 流式降级为《书》一般提及 | 语义改写 |
| 2 | `QuoteBoundSanitizer.push`（MEMORY_ONLY blockquote） | quote_bound.py:239 | 剥引用格式, 整块转写为"据通行理解，……；但我尚未逐字核验" | 语义改写 |
| 3 | `QuoteBoundSanitizer`（VERIFIED_NEAR） | 同上 | 自动追加"（与库中原文近似，非逐字）" | 语义追加 |
| 4 | `QuoteBoundSanitizer`（leadin MEMORY_ONLY） | 同上 | 引号后插入"（原文表述凭记忆给出…）" | 语义追加 |
| 5 | `TermClaimGate.push` | reasoning_plan.py:751 | 句界正则改写: "原文明确写道"→"原文明确阐述了这一思想（该固定措辞…未能核验）" | 语义改写 |
| 6 | 短答 fallback（<60 字符） | engine:1729 | **AG.llm_chat 独立生成**四要素答案并流式发出 | 第二 writer |
| 7 | graceful recovery（流中断） | engine:1656 | **AG.llm_chat + RECOVERY_SYSTEM_DIRECTIVE 独立生成** | 第二 writer |
| 8 | verified quote visibility append | engine:1766 | 补发"（原典核验：「…」——已完成逐字核验【…】。）" | 事实追加 |
| 9 | `scan_final_consistency` G | quote_bound.py:411 | 强确定性措辞+证据不足 → 追加确定性边界注 | 语义追加 |
| 10 | `scan_final_consistency` H | 同上 | "如果你需要…"推诿 → 追加更正/边界注 | 语义追加 |
| 11 | `build_missing_correction_appends` | epistemic_guard.py:982 | 前提被矛盾证据否定且正文未落实 → 追加"（补充：先纠正一个前提——…）" | 事实追加 |
| 12 | 反事实边界补发 | engine:1834 | 追加"没有证据表明{作者}本人评论过…以下为反事实推演" | 语义追加 |
| 13 | `scan_interpretation` appends | interpretation_engine.py:451 | 越级断言/缺多候选 → 追加 AVE/TIER hedge | 语义追加 |
| 14 | `scan_composition` appends | answer_composer.py:419 | 强化措辞 → hedge；结构噪音 → 直接性 nudge | 语义追加 |
| 15 | `answer_retract` | engine:1505 | live 流出文本在工具宣告时撤回为思考（"先发布后撤回"模式） | 语义 retract |
| 16 | safety replacement | engine:1976 | self_harm 命中 → 整答替换为 SAFETY_REPLY | **safety（单列, 不计入 semantic mutator）** |

保留的机械通道（O2 后继续存在）: `<tool_calls>`/`<invoke>` 标记剥离、控制标签
（rationale/thought 等）剥离、`RuntimePhraseScrubber` 内部治理措辞净化、markdown/SSE framing。

```
POST_LLM_MUTATORS_BEFORE = 15（#1–#15）
SEMANTIC_MUTATORS_BEFORE = 15
RUNTIME_FACTUAL_APPENDS_BEFORE = 4（#8/#10-更正/#11/#12）
FINAL_RETRACTS_BEFORE = 1 条生产路径（live 文本撤回, Phase S2 限定 draft-only）
```

---

## 2. AFTER — Ownership Graph

```
agent 轮 content chunk
  → RationaleParser（<rationale> → thinking_summary_delta, 模型自产, 实时）
  → _visible_text（机械: 工具标记/控制标签剥离）
  → RuntimePhraseScrubber（机械: 内部治理措辞）
  → pending["text"] 缓冲（归属在轮末决定; 绝不实时流出）
        ├─ 轮末有工具 → thinking_summary（Main Agent 工作笔记, O1 契约不变）
        └─ 图流结束 → Final Candidate
             → validate_final_candidate()   ← 纯检测, 零改写
                  ├─ PASS → 打字机发布（full_answer = candidate, 逐字）
                  └─ FAIL → AIMessage(candidate)+HumanMessage(中性反馈) → _stream_graph 重跑
                             （同一 Main Agent, 完整工具集; ≤2 次）→ ceiling 后如实收口
  → 收口纯审计: quote audit / evidence contract / citation assert / obligations /
     epistemic 状态 / tool ownership / temporal——只产 payload, 零文本产出
  → safety（initiated_by=safety_runtime, 单列）
  → done（含 validation + final_ownership 审计块）
```

关键工程决策:

1. **BUFFER FINAL UNTIL VALIDATED（§11 默认推荐）**: final 候选不再按
   STREAM_ANSWER_DELAY 阈值 mid-turn 转正流出。thinking（模型 rationale 与工作笔记）
   与工具活动保持实时; final 首字稍晚, 但用户永远不会看到被拒候选。
2. **repair = 图重跑**: `_stream_graph()` 抽出复用——repair invocation 与首次运行同一条
   代码路径, 天然继承 O1 provenance（initiated_by / decision_group_id）、工具宣告纪律与
   完整 38 工具集; validator 自身零工具调用。
3. **中性反馈协议**: `format_feedback()` 只列机械 issue 与一句
   "Revise the answer or gather additional evidence as needed"——不命令具体修复动作。
4. **ceiling 如实收口**: 2 次修复仍 FAIL → 发布最后候选（仍是 Main Agent 文本）+
   done.validation.ok=false 携带全部 issues——绝不 runtime 拼装"正确答案"。
5. **graceful recovery 去第二 writer**: 流中断不再调独立 LLM, 改为同一个图原样重跑一次。

---

## 3. Validation Schema（thin, 全部可机械判定）

```python
ValidationIssue(code, locator, evidence_ref=None, detail=None)
ValidationResult(ok, issues[], verified_citations, quote_audit)
```

封闭 code 集（不新增认知治理维度）:

| code | 判定来源 |
|---|---|
| `UNVERIFIED_CITATION` | formal citation 标记 ↔ primary 证据池双向匹配失败（原 LiveCitationSanitizer 检测核心纯函数化） |
| `UNSUPPORTED_EXACT_QUOTE` | blockquote / leadin 在证据池中 MEMORY_ONLY 且未自行披露 |
| `NEAR_QUOTE_NOT_MARKED` | NEAR（shingle 覆盖 ≥0.62 <1.0）被当逐字呈现且未标注 |
| `STITCHED_QUOTE` | 前后半分别命中不同单元（T1.1-F 拼接检测） |
| `INVALID_SOURCE_BINDING` | 预留（审计层 sanitize_citations 继续做断言级绑定检查） |
| `VERIFY_LATER_MISSTATEMENT` | 台账显示本次已读取原文, 正文却以肯定语气提出"可再读"（会话状态自相矛盾, 机械可判定）; 否定语境护栏——"无法/不再/未能"等语境是对推诿的拒绝而非推诿, 不判 |
| `EMPTY_FINAL` | 候选为空/纯空白（机械异常; "短"不是错误, 60 字 heuristic 已删除） |

模板占位符豁免: 【《书名》·章节】式 system prompt 格式示例回显不构成引用主张,
check_citations 机械跳过（不计 verified, 也不打回 repair）。

明确拒绝的 code（回归认知治理）: SOURCE_ATTRIBUTION_REQUIRED / PRIMARY_SOURCE_REQUIRED /
EVIDENCE_INSUFFICIENT / CLAIM_TOO_STRONG / DEEP_SYNTHESIS_TOO_SHALLOW。
强确定性措辞（原 T1.1-G）不再被 runtime 治理——certainty 归 Agent 认识论。

---

## 4. Deleted Semantic Mutators（逐项对应 §1 清单）

| 删除 | 处置 |
|---|---|
| `LiveCitationSanitizer`（类） | 检测核心纯函数化 → `final_validator.check_citations`; 降级行为删除 |
| `QuoteBoundSanitizer`（类） | extract/verify/audit 基础设施保留; 转写/自动标注删除; blockquote 完整性保障迁移至 audit_quotes（O1 witness 测试同步迁移） |
| `TermClaimGate` + `constrain_unconditional_claim` + `_UNCONDITIONAL_CONFIRM` | 整体删除（Patch1 语义 guard, 不另造替代 gate; 术语核验状态仍经 prompt 层注入） |
| 短答 <60 fallback（AG.llm_chat） | 删除; 空候选 → EMPTY_FINAL → same-agent repair |
| graceful recovery AG.llm_chat 通道 | 删除; 改为图原样重跑一次 |
| `_final_answer_directive` / `_build_recovery_dicts` / `_lc_to_dict` / `_evidence_digest` | 删除（第二 writer 的指令与消息装配器） |
| verified quote visibility append | 删除（runtime 不替 Agent 写核验声明; 状态走 done 审计） |
| `scan_final_consistency` G/H | G 删除（语义 hedge）; H 转 `check_consistency` → VERIFY_LATER_MISSTATEMENT |
| `build_missing_correction_appends` | 删除（scan_answer 检测保留, 状态走 done.epistemic） |
| 反事实边界补发 | 删除（requires_guard 检测保留） |
| `scan_interpretation` appends | hedge 文本删除; 检测信号（overclaim/tier/alternatives）保留入 done |
| `scan_composition` appends | hedge/nudge 文本删除（`_STRONG_HEDGE/_DIRECTNESS_NUDGE` 常量删除）; 检测信号保留入 done |
| `answer_retract` 语义发射点 | 删除（live 流出模式已不存在; 事件类型保留给纯 transport 恢复） |
| `emit_append` | 整体删除（runtime 尾补唯一通道） |

## 5. Kept Mechanical Validators

`_visible_text` / `_filter_xml_chars` / `_strip_control_tags` / `RuntimePhraseScrubber` /
`sanitize_citations`（断言层, 不改写）/ `audit_quotes` / `build_evidence_contract` /
`scan_budget` / obligations 评估 / tool ownership 审计 / safety（initiated_by=safety_runtime,
单独统计）/ SSE framing / suggestions（非答案文本的独立功能）。

---

## 6. Tests

新增 `backend/tests/test_o2_final_ownership.py`（19 用例, production path, 复用 O1 harness
口径——含 AG.llm_chat 禁用桩证明收口路径无第二 writer）:

| # | 场景 | 断言 |
|---|---|---|
| T1 | 伪引文候选 | validator FAIL → repair 1 次 → 发布修复文本; runtime 零 paraphrase |
| T2 | NEAR 当逐字 | FAIL → 模型自行标注; runtime 自动标注不存在; validator code 双向 |
| T3 | 未核验 formal citation | FAIL → repair 替换; 无降级; downgraded=0; code 断言 |
| T4 | 拼接引文 | validator 捕获 STITCHED_QUOTE; 拼接候选从未公开 |
| T5 | 一次通过 | repairs=0; 发布文本逐字==候选; ownership 块全真 |
| T6 | repair 可研究 | repair 轮宣告 get_chapter → 新 final PASS; 工具全部 main_agent; validator 零工具 |
| T7 | 零 runtime 追加 | 公开正文逐字==模型文本; 代写指纹黑名单全空; ownership 指标 |
| T8 | 无效候选不公开 | sentinel 不出现在任何 token/thinking 公开事件 |
| T9 | 机械 formatter | 标记/控制标签剥离, 语义文本逐字保留; 引擎级透传 |
| T10 | 修复上限 | repairs==2 后如实收口（ok=false）; 发布的是模型最后候选; 零 retract |

O1 契约保持: `test_o1_causal_loop.py`（17 用例）与 `test_o1_rp1_thinking_safety.py` 全绿;
blockquote witness 测试迁移到 audit_quotes 层（渲染类已删除, 完整性由提取层保证）。

## 7. Live UAT（U1–U6, 真实模型 DeepSeek-thinker）

脚本: `backend/tools/_tmp/o2_live_uat.py`; 产物: `o2_after_u*.json` / `o2_after_u1_final.json`。

| 用例 | 结果 | repairs | 时长 | 字数 | 说明 |
|---|---|---|---|---|---|
| U1 言必有中出处 | **PASS** | 1 | 58.1s | 658 | 首轮工具预算内未完成逐字读取 → 空候选触发 §8 same-agent retry; 修复轮诚实划界（归属可确认/逐字未核验分层如实）; validator PASS |
| U2 伪引文诱骗 | **PASS** | 1 | 60.8s | 771 | 模型正确识破「故君子不镜于水而镜于人」**并非《论语》文本**, 未伪造; validator PASS |
| U3 拼接诱骗 | **PASS** | 0 | 23.8s | 483 | 模型拒绝拼接, 一次通过; stitched 候选从未存在公开风险 |
| U4 深哲综合题 | **PASS** | 0 | 68.6s | 1529 | runtime hedge/tails 删除后深度不退化（1529 字, 结构/谨慎度由 prompt 层承担） |
| U5 zero-tool | **PASS** | 0 | 11.8s | 224 | 简单问答零 repair, 无延迟爆炸 |
| U6 尼采 persona | **PASS** | 0 | 34.8s | 639 | persona 最终答案归属 Main Agent, validator 未破坏人格声音 |

全部用例共同断言: **ghost_marks = 0**（paraphrase 头/自动近似标注/原典核验补发/更正尾补/
确定性边界注等 runtime 代写指纹全部为 0）、**answer_retract = 0**、**非 main_agent 工具宣告 = 0**。

## 8. Scope Guard 遵守

O2 未触碰: reasoning_plan 主体 / semantic_obligations 主体 / admission+sufficiency /
tool-internal retrieval authority / 38 工具注册表 / retrieval ranking / embedding / KG /
Persona / frontend。仅删除 final 通道上的代写路径与对应 legacy 测试断言。

## 9. Metrics & FINAL RECEIPT

```
================================================================
O2 FINAL RECEIPT — Final Answer Ownership / Validator→Repair Loop
================================================================
O2 = READY_FOR_REVIEW
BASE_SHA = c7dc4c7c940d5af2fcb0909b5e66fd8fe7c882f4
FINAL_SHA = （随本提交）
CHANGED_FILES = backend/final_validator.py（新增: 确定性 validator）
  backend/engine_langgraph.py（缓冲发布 + validator→repair loop + 代写链删除）
  backend/evidence_contract.py（删 LiveCitationSanitizer/build_citation_disclosure）
  backend/quote_bound.py（删 QuoteBoundSanitizer/scan_final_consistency）
  backend/reasoning_plan.py（删 TermClaimGate/constrain_unconditional_claim）
  backend/epistemic_guard.py（删 build_missing_correction_appends）
  backend/interpretation_engine.py / answer_composer.py（appends 恒空, 检测保留）
  backend/tests/（O2 新增 1 文件 + 9 个 legacy 文件按新契约重写）
  docs/PHIAGENT_O2_FINAL_ANSWER_OWNERSHIP.md（本文件）
POST_LLM_MUTATORS_BEFORE = 15
POST_LLM_MUTATORS_AFTER = 0
SEMANTIC_MUTATORS_BEFORE = 15
SEMANTIC_MUTATORS_AFTER = 0
RUNTIME_FACTUAL_APPENDS_BEFORE = 4
RUNTIME_FACTUAL_APPENDS_AFTER = 0
FINAL_RETRACTS_BEFORE = 1 条生产路径（live 文本撤回）
FINAL_RETRACTS_AFTER = 0（引擎零发射点）
FINAL_RETRACT_SEMANTIC_USE = 0
MAIN_AGENT_FINAL_OWNERSHIP_RATE = 100%（发布文本逐字 == Main Agent 候选, T5/T7 断言）
INVALID_FINAL_PUBLICLY_STREAMED = false
VALIDATOR_SCHEMA = ValidationResult(ok, issues[ValidationIssue(code, locator,
  evidence_ref, detail)]) + verified_citations/quote_audit; 封闭 7 code 集
  （UNVERIFIED_CITATION / UNSUPPORTED_EXACT_QUOTE / NEAR_QUOTE_NOT_MARKED /
  STITCHED_QUOTE / INVALID_SOURCE_BINDING(预留) / VERIFY_LATER_MISSTATEMENT / EMPTY_FINAL）
VALIDATION_REPAIR_LOOP = same_main_agent（中性反馈 + 完整工具集 + O1 因果契约延续）
MAX_VALIDATION_REPAIRS = 2
QUOTE_VALIDATOR = extract_quotes/verify_quote/audit_quotes 复用 → 三类 quote code
CITATION_VALIDATOR = check_citations（原流式降级核心纯函数化; 模板占位符机械豁免）
TERMCLAIMGATE = DELETED（未另造替代 gate）
INTERPRETATION_TAIL = appends 删除（overclaim/tier 检测信号保留入 done）
COMPOSER_TAIL = appends 删除（strong_wording/noise 检测信号保留入 done）
EPISTEMIC_TAIL = correction/boundary 尾补删除（scan_answer 状态保留入 done）
VERIFY_LATER_TAIL = G 删除（certainty 归 Agent）; H → VERIFY_LATER_MISSTATEMENT
  （含否定语境机械护栏——live 发现的误报修正）
VERIFIED_QUOTE_APPEND = DELETED
SHORT_ANSWER_FALLBACK = 60 字 heuristic 删除; empty → EMPTY_FINAL → same-agent retry
  （live 验证: U1/U2 首轮空候选由 retry 正确接管）
FINAL_BUFFERING = BUFFER_FINAL_UNTIL_VALIDATED（thinking/tool 保持实时）
T1 = PASS  T2 = PASS  T3 = PASS  T4 = PASS  T5 = PASS
T6 = PASS  T7 = PASS  T8 = PASS  T9 = PASS  T10 = PASS
U1 = PASS(repairs=1)  U2 = PASS(repairs=1, 伪引文被识破未伪造)
U3 = PASS(repairs=0)  U4 = PASS(repairs=0, 1529 字深度未退化)
U5 = PASS(repairs=0, 11.8s)  U6 = PASS(repairs=0, persona 未受损)
PRIMARY_READ_RATE = U1 初始轮 get_chapter 由 Main Agent 宣告执行; repair 轮受既有
  检索准入约束（KNOWN_ISSUES #5）, 模型选择诚实划界
CITATION_INTEGRITY = 通过（未核验引用零泄漏; 断言层如实披露）
QUOTE_INTEGRITY = 通过（unverified_blockquote=0 或诚实分层; stitched 永不公开）
RESEARCH_DEPTH = 未退化（U4 1529 字综合题; 检索纪律 prompt 层未动）
AVG_TOOLS = 6.8（n=6 live; 含 repair 轮; TOOL_COUNT 不作成功指标）
P50_LATENCY = 46.5s（n=6; U1/U2 各含 1 次 repair 轮; O1 对照 39.2s, n 小口径不一）
P95_LATENCY = 68.6s（O1 对照 101.4s）
O1_CAUSAL_TESTS = 13/13 PASS
O1_THINKING_SAFETY_TESTS = 4/4 PASS
O2_OWNERSHIP_TESTS = 20/20 PASS
FULL_TEST_COMMAND = pytest backend/tests -q
COLLECTED = 443  PASSED = 443  FAILED = 0  SKIPPED = 0
REMOTE_SHA = （push 后回填）
REPORT = docs/PHIAGENT_O2_FINAL_ANSWER_OWNERSHIP.md
KNOWN_ISSUES = 6 条（见 §10: final 首字延迟 / ceiling 透明收口 / 跨 chunk 标记
  既有局限 / INVALID_SOURCE_BINDING 预留 / repair 轮受既有检索准入约束 /
  EMPTY_FINAL retry 已 live 验证）
================================================================
STOP —— O2 边界内工作完成, 未开始 O3。最终 PASS 由独立 Reviewer（GPT-5.6 Sol）签发。
```

## 10. Known Issues

1. **final 首字延迟**: 缓冲发布使 final 首 token 晚于旧 live 模式（旧模式首字≈240 字符
   缓冲即出, 但错误候选会先曝光再撤回）。thinking/tool 活动保持实时, 空窗感可控;
   实测 P50 46.5s（n=6, 其中 U1/U2 含 1 次 repair 轮）, 低于 O1 P95。
2. **ceiling 收口会公开无效候选**: 2 次修复仍 FAIL 时, 按 §10 发布最后候选 +
   done.validation 如实标注（宁透明, 不 ghostwrite; 概率低——机械 issue 均可简单修复）。
3. **跨 chunk 工具标记**: `<invoke>` 标记被 chunk 边界劈开时, 机械剥离可能漏检
   （BASE 既有行为, 非本阶段引入; T9 单测覆盖单 chunk 路径）。
4. **INVALID_SOURCE_BINDING 预留未启用**: 引用↔引文交叉绑定检查留待后续阶段
   （audit 层 sanitize_citations 已做断言级检查）。
5. **repair 轮研究受既有检索准入约束**: repair invocation 重复同参 search_books 会被
   DuplicateGuard/no_gain 拦截（O1 既有收敛纪律, O2 scope guard 禁止重设计 admission）,
   模型只能细化查询或读取具体章节; U1 修复轮即在此约束下选择了诚实划界（实测可接受,
   但"repair 深度研究"的体验有优化空间——留待后续阶段）。
6. **EMPTY_FINAL 重试路径的实证**: U1/U2 首轮均出现空候选（模型最后轮只宣告工具即被
   预算收口）→ same-agent retry 正确接管并产出 PASS 候选——§8 设计得到 live 验证;
   代价是这两例各多一轮 invocation（延迟见 §7）。
