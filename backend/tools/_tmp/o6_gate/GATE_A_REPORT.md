# O6 Integrated Final Quality Gate — GATE A REPORT
（自动化 / 静态 / 脚本化取证部分）

## 0. Gate Freeze

```text
BRANCH        = refactor/phiagent-main-agent-orchestration
HEAD_SHA      = b6e656bd9858137eabd0d30510a269038440bef0
REMOTE_SHA    = b6e656bd9858137eabd0d30510a269038440bef0  (origin 同步)
BASE_SHA(任务书 GATE_SHA) = e3692ec1de5b860787a5093a889de159cb0f10d7
HEAD vs BASE  = 仅 docs/PHIAGENT_O5_THIN_RUNTIME.md 3 行文档差异（生产代码 0 差异）
O0 对照锚点   = tag phiagent-pre-orchestration-reset → a69149b7288766f43fcc4be1bc822da2f59027bd（annotated tag）
WORKTREE      = 干净，唯一额外未跟踪路径:
                ?? backend/tools/_tmp/            （任务书明确允许的 evaluation-only 产物）
                ?? backend/tests/test_o5_thin_runtime.py   ← 见 Anomaly N1
GATE 结束复核 = git rev-parse HEAD == b6e656bd9（无漂移）; 生产/测试文件零修改、零 commit
```

原始数据（全部在 `backend/tools/_tmp/o6_gate/gate_a/`）:
`full_regression.log` `suites.log` `static_analysis.json` `static_analysis_summary.txt`
`runtime_tool_surface.json` `runtime_tool_surface_smoke2.json` `tool_surface.log`
`validator_matrix.json` `repair_matrix.json` `error_gate.json` `ram_probe.json` `ram_probe.log`

---

## 1. G16 + §4 Full Automated Regression — PASS

`仓库根 .venv/Scripts/python.exe -m pytest backend/tests -q`

```text
COLLECTED = 350      （含未跟踪的 test_o5_thin_runtime.py 18 条——pytest 按磁盘收集）
PASSED    = 350
FAILED    = 0
SKIPPED   = 0
DURATION  = 71.81s        EXIT = 0
```

单跑各套件（全部 PASSED）:

| Suite | Tests | Duration |
|---|---|---|
| test_o1_causal_loop.py | 13 passed | 15.18s |
| test_o1_rp1_thinking_safety.py | 4 passed | 5.16s |
| test_o2_final_ownership.py | 23 passed | 11.99s |
| test_o3_tool_authority.py | 15 passed | 5.40s |
| test_o4_cognitive_collapse.py | 20 passed | 8.62s |
| test_o5_thin_runtime.py | 18 passed | 11.39s |

非 test_* 命名回归:
`pytest backend/tests/regression_oldman_sea.py -q` → **13 passed in 4.25s**
（pytest 默认 discover 不收集它，已单独跑；另以纯脚本方式 `python regression_oldman_sea.py` 运行，正常结束输出 DONE。）

---

## 2. G1 + §2 Architecture Truth Gate — PASS

方法: `tokenize` 剥除 `#` 注释后对全部生产源码（backend 顶层 + routes/，含 engine_langgraph/agent_runtime/final_validator/evidence_contract/quote_bound/tool_contracts/routes/agent*）grep 11 类被禁控制者符号（脚本 `gate_a_static.py`，输出 `static_analysis.json`）。

### 剥注释后 code 级命中 = 0（生产控制权零残留）

全部命中逐条归类（`static_analysis_summary.txt` 有 file:line）:
- **docstring/注释性字符串**（历史说明，非执行代码）: engine_langgraph.py:10（auto_read 词表删除说明）、:434（"语义准入（obligation admission）…已删除"）、agent_runtime.py:24/27（同类删除说明）。
- **system prompt 字符串**（对模型的措辞禁令，非 runtime 行为）: engine_langgraph.py:156（铁律 15 明令禁止模型使用"检索已收口/准入未通过/系统收敛"等内部措辞）。
- **offline 评估套件** `evaluation_suite.py`（PremiseVerifier/scan_interpretation/AnswerComposer 名称）: 仅被 `backend/tests/*` 导入（grep 证实 main.py / routes/ 零引用）——离线评分副本，不在生产服务路径。见 Anomaly N2。
- **机械层合法保留**: HARD_BUDGET_DIRECTIVE（agent_runtime.py:383，仅表达资源约束）、tool_cancel 文案（engine:1383）、EXACT_DUPLICATE_REUSED 注记（engine:1303，显式声明"不涉及证据充分性判断"）、sanitize_citations（evidence_contract.py:647，O5 后只读断言+日志，sanitized_text 无消费者）、RuntimePhraseScrubber（tool_contracts.py:289+，机械删除内部治理措辞，不改写语义）。

架构真实形态（engine_langgraph.py 生产代码）:
`Request → Context Builder（:284-322 单源）→ Main Agent（agent_node :346）↔ Tool Executor（tools_node :426，仅机械门）→ EvidenceState（:536-547 登记）→ Final Validator（:1389）→ PASS 发布（:1425-1429 逐字）/ FAIL → 同一 Main Agent repair ≤2（:1394-1419）`

### 8 项零指标（代码锚点 + 测试断言双证）

| 指标 | 值 | 代码锚点 | 回归断言 |
|---|---|---|---|
| ENGINE_COGNITIVE_AUTO_TOOLS | 0 | engine:1597 `"engine_cognitive_auto_tools": 0` | test_o1_causal_loop / test_o2 T6 / test_o3 / test_o4（44 处 O 套件断言） |
| SEMANTIC_TOOL_CONTROL_EFFECTS | 0 | tools_node 仅 3 个机械门: 未知工具(:502)/精确判重复用(:474)/硬上限(:457)；MAP_HINTS/COMPARISON 路由注入已删(:1080-1083) | test_o3（15 条） |
| RUNTIME_SEMANTIC_MUTATORS | 0 | engine:1606 `"semantic_mutators": 0`；emit_append/LiveCitationSanitizer/QuoteBoundSanitizer/TermClaimGate 全删 | test_o2 T3/T5/T7 |
| RUNTIME_FACTUAL_APPENDS | 0 | engine:1607；O2 §7 删除的 runtime 代写通道（:1447-1453 注释锚） | test_o2 T7 |
| RAW_REASONING_PUBLIC | 0 | `thought_stream` 零 yield（静态计数 0）；reasoning_content 一律内部丢弃（engine:1267-1271） | test_o1_rp1（4 条） |
| RUNTIME_GENERATED_THINKING | 0 | thinking 唯一来源 = 模型 `<rationale>`/公开工作笔记（engine:906-914 数据源契约）；mini-LLM 摘要器已删 | test_o1_rp1 |
| INVALID_FINAL_PUBLIC | 0 | 发布唯一入口 `if candidate.strip() and validation.ok`（engine:1425）；耗尽路径只发 validation_failed+error（:1431-1439） | test_o2 T8/T10（kill test） |
| FAKE_TOP_LEVEL_TOOL_RECORDS | 0 | 工具内部检索入池强制 `initiated_by="tool_internal"` + `pseudo=True` + parent_tool_call_id（engine:569-589） | test_o3 T11（:325-338） |

事件词表（engine:5-7）实测收敛为 12 类，scripted 全流程中 `thought_stream` / `answer_retract` / `reasoning_summary` 零出现（§18/§20 各 stream 原始记录）。

---

## 3. §3 Authority Matrix Final Audit — PASS（无重复 cognitive owner）

| DECISION | OWNER | 代码证据 |
|---|---|---|
| Interpret user request | Main Agent | `_build_context_messages`（engine:284-322）只组装提示+用户消息；无意图分类（AgentState 无 plan/verif_box/user_message，engine:336-344 删除注释锚） |
| Research strategy | Main Agent | 铁律 1 检索—阅读闭环（engine:75-88，prompt 层）；runtime 无 planner/strategy 模块（静态扫描 0 命中） |
| Tool selection | Main Agent | 工具只由模型 tool_calls 进入执行（engine:437-438 `calls = last.tool_calls or []`）；O3 §14 强制路由删除（engine:1080-1083） |
| Research continuation | Main Agent | 循环继续仅因模型宣告工具（`should_continue` engine:621-632） |
| Research stop | Main Agent | 无 tool_calls → end（同上）；runtime 停止仅剩机械硬上限（engine:354-367） |
| Interpretation | Main Agent | interpretation_engine.py 已删（生产路径 0 引用；离线副本见 N2）；解读分层归 prompt 铁律 10（engine:134-136） |
| Answer structure | Main Agent | answer_composer.py 已删；结构由模型自组织（§11 FORMAT_COLLAPSE 属 Gate B live 评估） |
| Final natural-language text | Main Agent | 候选缓冲→validator→逐字发布（engine:1425-1429）；`final_text_owner: "main_agent"`、`main_agent_final_ownership_rate: 1.0`（engine:1604-1611）；test_o2 T5/T7 断言逐字一致 |
| Tool execution | Runtime | tools_node 线程池执行/重试/超时（engine:493-526）；provenance 不改变发起者（engine:1292-1298） |
| Hard resource ceiling | Runtime | `ToolBudget.hard_reached`（agent_runtime:242-244）+ HARD_BUDGET_DIRECTIVE（:383）+ 机械拒绝 RESOURCE_CEILING_REACHED（engine:457-472）；§20 E5 实测 |
| Exact duplicate reuse | Runtime | DuplicateGuard（agent_runtime:176-188）+ 复用路径（engine:474-492）——同参只读工具机械复用 |
| Permission / safety | Runtime | `_safety_check`（engine:649-667）+ `safety_enforcement.initiated_by="safety_runtime"`（engine:1633-1636）；O2 §13 将其定性为安全执行层而非语义 mutator |
| Timeout / cancellation | Runtime | AR.TOOL_TIMEOUT + asyncio.wait_for（engine:447,504-511）；tool_cancel（engine:1382-1383） |
| Evidence recording | EvidenceState | 纯事实登记 record_read/record_search（evidence_contract:95-131；engine:536-547）；done.evidence.facts（engine:1575-1579）；无任何准入/义务判定（模块 docstring 明示） |
| Quote verification | Validator | `final_validator.check_quotes`（final_validator:138-166）→ quote_bound.verify_quote（quote_bound:154-214，只检测） |
| Citation verification | Validator | `final_validator.check_citations`（final_validator:95-132，只检测不降级） |
| Repair content | Main Agent | 修复 = 同一 Main Agent 新 invocation（engine:1401-1410 原样重入同一图路径）；反馈中性（final_validator:70-76） |
| Repair tool calls | Main Agent | repair 绑定完整工具集、可自主宣告（_stream_graph 共用路径 engine:1185-1188）；§18 R2 实测 repair 轮宣告 get_chapter |
| Repair ceiling | Runtime mechanical | MAX_VALIDATION_REPAIRS=2（final_validator:41）+ engine 循环（:1392）；绝不由 runtime 代写（engine:1421-1424 注释锚 + T10 kill test） |

每个认知决策 owner 唯一（Main Agent）；Runtime 仅持机械权力；Validator 仅持 VALIDATE/REJECT。**重复 cognitive owner = 0 → 不触发 FAIL 条件。**

---

## 4. §17 Validator Quality Gate — **FAIL（narrow，Finding F1）**

直接驱动 `final_validator.validate_final_candidate`（脚本 `gate_a_validator_matrix.py`，合成证据池 = get_chapter 全文（行分段）+ search 片段 + 第二书章节，与 test_o2 同构造口径）。

```text
positive（=invalid candidate，期望 REJECT）: 10 例
negative（=valid candidate，期望 PASS）:     10 例

VALIDATOR_TRUE_POSITIVE  = 9
VALIDATOR_FALSE_NEGATIVE = 1   ← 要求 = 0，未达标
VALIDATOR_TRUE_NEGATIVE  = 10
VALIDATOR_FALSE_POSITIVE = 0   （无 blocker）
```

| case | expect | actual | 判定 | validator codes |
|---|---|---|---|---|
| P1 伪逐字 blockquote | REJECT | REJECT | TP | UNSUPPORTED_EXACT_QUOTE |
| P2 `原文是：“伪引文”` 行内引导词 | REJECT | **PASS** | **FN (F1)** | （无） |
| P3 NEAR 未标注（夫人→其人） | REJECT | REJECT | TP | NEAR_QUOTE_NOT_MARKED |
| P4 NEAR 变体（何必改作→何必复作） | REJECT | REJECT | TP | NEAR_QUOTE_NOT_MARKED |
| P5 同章两行单元拼接 | REJECT | REJECT | TP | UNSUPPORTED_EXACT_QUOTE * |
| P6 跨书拼接 | REJECT | REJECT | TP | NEAR_QUOTE_NOT_MARKED |
| P7 未核验 citation（韩非子·五蠹） | REJECT | REJECT | TP | UNVERIFIED_CITATION |
| P8 真实书名+占位章节（绕过尝试） | REJECT | REJECT | TP | UNVERIFIED_CITATION |
| P9 空候选 | REJECT | REJECT | TP | EMPTY_FINAL |
| P10 纯空白候选 | REJECT | REJECT | TP | EMPTY_FINAL |
| N1 已核验 blockquote+citation | PASS | PASS | TN | — |
| N2 纯解释零引用 | PASS | PASS | TN | — |
| N3 书名一般提及 | PASS | PASS | TN | — |
| N4 NEAR+模型自带披露 | PASS | PASS | TN | — |
| N5 零工具简单回答 | PASS | PASS | TN | — |
| N6 模板占位符回显 | PASS | PASS | TN | — |
| N7 已核验引导词引文 | PASS | PASS | TN | — |
| N8 多来源已核验组合 | PASS | PASS | TN | — |
| N9 凭记忆 leadin+披露标记 | PASS | PASS | TN | — |
| N10 检索片段支撑的正式引用 | PASS | PASS | TN | — |

\* P5/P6 均被 REJECT（正确），但 code 落在 UNSUPPORTED_EXACT_QUOTE/NEAR 而非 STITCHED_QUOTE——STITCHED 专用 code 已由 test_o2 T4 的等长对半构造覆盖，属构造差异非缺陷。

### Finding F1（ validator false-negative，记录不修）
- **现象**: `原文是：“…”`（引导词后紧跟弯引号，最自然的行内引文形态）被 `quote_bound.extract_quotes` 归类为 `quoted`（不作逐字承诺），validator 直接放行伪引文。
- **根因**（file:line）: `quote_bound.py:49-52` LEADIN_RE 要求引导词后跟 `[“"]` 引号字符；而 `extract_quotes`（:83-88）传给它的 head 是引号之前文本——引号字符本身不在 head 内 → 单引文场景 LEADIN_RE 恒不匹配；只有 40 字符窗口内存在**前置引号对**时才误打正着（探针 V5）。
- **影响面**: blockquote 通道（主呈现形态）不受影响（V6 正常 REJECT）；弯引号无引导词长文本（probe E1）按既定 scare-quote 契约豁免（记为残余风险，非本次 FN）。
- **复核断言**: test_o2 T2 的 leadin 用例走的是 blockquote 形态 + 已覆盖样本，未触及该形态——与"FN=0 要求"冲突，故 §17 判 FAIL（narrow）。按 O6 铁律不修，交 Reviewer 决定是否窄补丁。

---

## 5. §18 Repair Quality Gate — PASS（8 controlled cases 全部符合契约）

引擎级 ScriptedChat harness（脚本 `gate_a_repair_matrix.py`，反馈经捕获的 HumanMessage 取证）。

```text
REPAIR_SUCCESS_FIRST   = 6   （R1 quote / R2 quote+research / R3 citation / R5 near / R7 stitched / R8 whitespace-empty）
REPAIR_SUCCESS_SECOND  = 1   （R4 citation 第二次修复后发布）
REPAIR_EXHAUSTED       = 1   （R6 near 恒坏 → validation_failed + error 干净收口，sentinel 零泄漏）
REPAIR_RESEARCH_USED   = 1   （R2: repair 轮自主宣告 get_chapter 补研究后发布）
```

契约断言（全部通过）:
- **repair 反馈中性**: 反馈文本仅列机械 issue code（`UNSUPPORTED_EXACT_QUOTE at "…"等`）+ "Revise the answer or gather additional evidence as needed."——命令式动作模式（必须/请+改写/删除/调用等，中英正则）0 命中。
- **repair 可用工具**: R2 repair 轮宣告并执行了 get_chapter（initiated_by=main_agent）。
- **runtime 不指定具体认知动作**: 全部公开事件（token/tool_note/thinking/validation_failed/error）0 命中命令式措辞；runtime 对 repair 的唯一定性是中性活动注记"（答案证据校验未通过——正在把结构化问题反馈给智能体重新整理回答……）"。
- **修复上限机械**: R6 恰好 2 次 repair 后停，无无限循环。
- harness 侧说明: R8 首版用真空 AIMessage("") 触发的是 transport 层"No generations"→ graceful 重试路径（干净恢复，已另行记录为行为观察）；改用纯空白候选后才走 validator EMPTY_FINAL→repair——两种路径行为均正确。

---

## 6. §20 Error / Failure Gate — PASS_WITH_NOTE（8/8 干净收口；Finding F2）

monkeypatch 进程内受控注入（脚本 `gate_a_error_gate.py`）。每例断言: 公开事件无 stack trace/秘密标记（Traceback/File"/boom-db-SECRET/429/…）、无伪造事实、无 ghostwritten final、无效候选零泄漏、done/error 恰一收口。

| case | 注入 | 结果 | 行为 |
|---|---|---|---|
| E1 tool timeout | TOOL_TIMEOUT=1.5s，stub sleep 3.5s | 干净 | 工具事件携带"执行超时（>1.5s）"→ Main Agent 据实作答 → 正常发布 |
| E2 tool execution error | stub raise（含 SECRET 标记） | 干净 | 轮内重试后 error 结果回传 + fallback 提示；SECRET 不入任何公开事件 |
| E3 unknown tool | 宣告未注册工具 | 干净 | `{"error":"未知工具 …"}` 机械拒绝 → 继续对话 → 正常发布 |
| E4 missing-param schema | 缺必需参数 | 干净 | 工具自校验 error 结果回传 → 正常发布 |
| E5 hard ceiling | hard_total=1 | 干净 | 第二轮宣告被 RESOURCE_CEILING_REACHED 机械拒绝（文案仅表达资源约束）→ forced 补跑 → repairs=0 正常发布；无"证据已充分"类语义措辞 |
| E6 provider error | get_llm 返回恒 429 | 干净 | 2 次重试（退避）→ ModelCallError → graceful 重跑一次 → 仍失败 → **脱敏** error（"智能体暂时出错，请重试或换个问法"；SECRET-PROVIDER-DETAIL 仅入日志）；零 ghostwritten final |
| E7 validator exhaustion | 恒坏候选 ×3 | 干净 | repairs=2 耗尽 → validation_failed+error；sentinel 在 token 通道计数 = 0 |
| E8 cancel + F2 | forced_tools_done 后仍宣告 websearch | 干净收口但 repair 被击穿 | tool_cancel(websearch) 正确发出解除前端"调用中"卡片；随后暴露 **Finding F2**（见下） |

`ALL_CLEAN = True`（无泄漏类失败）。

### Finding F2（forced+cancel 边界路径下 repair 文本丢失，记录不修）
- **复现**: 硬上限 forced → forced 轮宣告新工具（被取消/拒绝后图终止）→ 候选为空（EMPTY_FINAL）→ repair 轮模型**已给出**完整有效新答案 → 仍以 EMPTY_FINAL 耗尽，用户得到"回答未通过证据一致性校验"。
- **根因**: 图以 `forced && forced_tools_done` 终止时，最后一次 agent 轮的声明使 `pending["has_tools"]=True`，而该路径**不再经过 tools_node**（`pending` 不会重置），repair 收尾处的 `if pending["has_tools"]: flush; pending["text"]=""`（engine_langgraph.py:1415-1418）把 repair 轮的纯文本新答案当作"预算强制收尾的残留工具轮"降级/清空（note_emitted 已置位时连 thinking 都不发）→ 候选恒空。
- **影响**: 收口是**安全**的（无无效内容发布、无泄漏、干净 error/done），但该边界下 repair 机制被击穿（REPAIR 白白耗尽、有效答案被丢弃）。触发条件窄: 需硬上限打满 + forced 轮残留宣告 + 首候选为空 + repair 纯文本。与 §7 发布失败分类的 Q7 HARD_CEILING × Q6 REPAIR_STRATEGY_FAILURE 交叉。**按 EVIDENCE-ONLY 只记录。**

---

## 7. §23 General / Nietzsche Tool Surface — PASS

实测 `EG.get_tools(...)`（脚本 `gate_a_tool_surface.py`，`runtime_tool_surface.json`）:

```text
GENERAL_TOOL_SURFACE   = 30 工具，与 O0 注册表（routes/agent._TOOL_REGISTER_ORDER）逐一比对:
                         general_minus_O0 = [] ; O0_minus_general = []  （零缺失/零多余）
                         duplicates = []
NIETZSCHE_TOOL_SURFACE = 15 工具 = 共享原典 7（search_books/get_chapter/get_book_detail/
                         query_graph/query_database/get_philosopher/websearch）
                         + 专属 8（philosopher_memory/period/style/quote/graph/corpus/concepts/user）
                         duplicates = [] ; philosopher_* 泄漏到 general = 0
```

Specialized tools 真实调用冒烟（真实 provider，7/7 结构化返回）:

| tool | 结果 | 返回结构（键） |
|---|---|---|
| compare_views | ok 14.8s | comparison_axes/side_a(_claims)/side_b(_claims)/shared_problem/evidence_needs/citations/… |
| dialectic | ok 11.4s | movement/constraints/fields_used/summary/… |
| thought_experiment | ok 7.9s | setting/stance_projections/revealed_problem/summary |
| conceptual_map | ok 9.5s | graph/map_text/mermaid(+validation)/map_type（"12 节点/16 边, parse 验证通过"） |
| analyze_argument | ok 8.0s | argument{conclusion/premises(explicit/implicit)/fallacies/…}/summary |
| essay_outline | ok 12.8s | outline/note |
| socratic_tutor（真实） | ok 6.4s | next_question/question_purpose/diagnosed_assumption/state_update/…（单问题契约） |

（首轮 3 个工具因 harness 参数名写错返回参数校验 error——修正为 schema 参数后全部通过；参数校验本身行为正确。原始两轮记录均保留。）

**socratic 行为 scripted 冒烟**（引擎级，脚本化模型 + 真实引擎路径 + 确定性 socratic execute stub）: 用户要求"只问我一个问题，不要直接给答案"→ 模型自主宣告 socratic_tutor（initiated_by=main_agent，无任何 runtime 路由注入）→ 发布答案恰含 1 个实质问题（"？"*1）→ validation ok。runtime 强制路由 = 不存在。

---

## 8. §25 Citation / Quote UI Payload — PASS（O5 删键未破坏 UI 契约）

对照 `agent-app/src/pages/AgentPage.jsx` done 处理块（:411-434）与 `MessageList.jsx`（:294-310）/`utils/evidence.js`:

| 前端消费 | done payload 现状（engine:1580-1637） | 结论 |
|---|---|---|
| `evt.citations`（CiteChip 需 evidence_id/book/chapter/used） | `done.citations` = `build_evidence_contract().citations` = used_evidence 投影，`_project()` 含 evidence_id/book/chapter/book_id/chapter_idx/author/source_type/used:true/supports_claim_ids（evidence_contract:577-589） | ✓ |
| `evt.evidence` → `evidence?.retrieved_count`（MessageList:299）+ used_count | evidence_payload 携带 retrieved_count/used_count/retrieved_evidence/used_evidence/claims（contract:637-645）；O5 MERGE 后并入 `facts`（EvidenceState snapshot，加键安全，engine:1575-1579） | ✓ |
| `evt.suggestions`（先规则后 LLM 增量） | done.suggestions（规则版即时）+ 后续 `suggestions` 事件（LLM 版，engine:1645-1652） | ✓ |
| `evt.safety === 'blocked'` → `evt.safety_reply` 替换正文、citations 清零 | engine:1515-1526（blocked 时替换 SAFETY_REPLY、citations/used_evidence/used_count 清零）+ done.safety/safety_reply/safety_enforcement（:1633-1637） | ✓ |
| 已删键（O4/O5: obligations/obligation_ledger/live_citation_sanitize/composition/epistemic/budget/tool_ownership/retrieval_state/plan/verification） | grep `agent-app/src` 零生产消费（仅 IME composition 无关命中与 reasoning_summary 历史数据兼容路径——MessageList:400 明示"仅数据保留, 不渲染"） | ✓ |
| 历史事件处理器（thought_stream/answer_retract/reasoning_summary，AgentPage:374/392/440） | 生产已不发射（O1-RP1/O5）；前端保留 dormant 分支属向后兼容，不构成契约破坏 | ✓（NOTE） |

---

## 9. §26 Architecture Regression Search — PASS

对生产源码剥注释做"结构 + 行为"双审计（`static_analysis.json` §26 扫描段），功能等价物符号与特征文案:

| 禁止项 | 剥注释命中 | 归类 |
|---|---|---|
| semantic admission / 准入 | 0 个执行点（全部为 docstring 删除说明 + prompt 禁令文案 + evidence_contract "准入条件"字样——后者指候选池白名单过滤的机械准入，无语义判断） | 无等价物 |
| sufficiency force / no_gain force | 0（no_gain 仅存遥测计数 budget.no_gain，无控制分支——agent_runtime:236-239） | 无 |
| verification intent routing | 0（verif_box/plan 状态链已删） | 无 |
| auto read / auto websearch | 0（`_ensure_primary_read` 计数 0；auto-websearch 计数 0；search_books 空结果后是否上网由 Main Agent 自主宣告，engine:1283-1285） | 无 |
| runtime semantic append / answer rewrite | 0 改写点（emit_append 0；sanitize_citations 只读断言；scrubber 仅机械删除治理措辞） | 无 |
| premise verifier / answer composer / interpretation judge | 生产路径 0（仅 evaluation_suite 离线评分副本，见 N2） | 无 |
| ghostwriting 文案（"据通行理解/（更正：/（原典核验："等） | 生产代码 0（仅 test_o2 黑名单常量） | 无 |
| raw reasoning passthrough（thought_stream/reasoning_content） | 0 yield / 0 转发（engine:1267-1271 显式丢弃） | 无 |

结构审计: 控制流仅 `agent ⇄ tools` 两节点 + 机械条件边（engine:638-644）；runtime 唯一 SystemMessage 注入点 = Context Builder + HARD_BUDGET_DIRECTIVE（engine:283 注释锚，与代码一致）。

---

## 10. §27 O0 vs O6 最终对比（preservation: phiagent-pre-orchestration-reset → a69149b7）

**不美化 O0**: O0 是一个 shadow-runtime 重度介入的系统——runtime 会代读原典（绕过 Main Agent 宣告）、自动上网、以 mini-LLM 代笔思考、透传 provider 原始思维链、并保留第二个"答案写手"与四套语义治理模块。

| 维度 | O0（a69149b7） | O6（b6e656bd9） |
|---|---|---|
| runtime-path LOC（顶层+routes 生产文件合计） | 13,987 | 10,504（**-3,483**；其中纯语义策略模块 3,026 LOC 整体删除） |
| engine_langgraph.py LOC | 2,353 | 1,672 |
| agent_runtime.py LOC | 961 | 391 |
| semantic policy LOC（answer_composer 575 + interpretation_engine 547 + epistemic_guard 1036 + reasoning_plan 868） | 3,026 | **0**（文件不存在） |
| decision owners（认知决策） | 至少 9 个重叠 owner：Planner(reasoning_plan)、Obligation ledger、检索准入(admission)、Sufficiency controller、No-gain controller、Interpretation judge、Answer composer、Epistemic/Premise guard、runtime 第二 writer | 唯一 cognitive owner = Main Agent；Runtime 仅机械；Validator 仅校验 |
| semantic regex（语义治理正则） | 35（四套语义模块内） | 语义治理正则 0；机械核验/格式正则 18（quote_bound/evidence_contract/tool_contracts——引文比对、mermaid 语法、措辞净化，均确定性无认知判断） |
| runtime semantic mutators（改写/追加正文点） | 27 处命中（engine 21 + quote_bound 4 + evidence_contract 2：LiveCitationSanitizer/QuoteBoundSanitizer/TermClaimGate/scan_final_consistency/emit_append/_final_answer_directive/_build_recovery_dicts） | **0**（final_validator 仅"检测"字样 2 处） |
| semantic tool gates | admission 准入门 + MAP_HINTS/COMPARISON 强制路由 + skill 重入拦截 | 0；仅机械门（未知工具/精确判重/硬上限） |
| hidden cognitive tools | `_ensure_primary_read` 代读（3 处）+ 引擎 auto-websearch（1 处，evidence 空时代执行 websearch 并入账） | 0 / 0 |
| raw reasoning exposure | `reasoning_content → thought_stream` 透传给用户（1 处 yield + 事后 mini-LLM"思考摘要"通道=runtime 冒充 Agent 思考） | 0（provider 私有推理一律内部丢弃；thinking 唯一来源=模型自己的 rationale/工作笔记） |
| tests（backend/tests） | 18 个 test 文件 / 407 个测试函数（含已删模块的 composer/interpretation/guard 测试 75 个） | 22 个 test 文件 / 350 个测试函数（新增 O1–O5 套件 93 条；瘦身后 Phase 套件同步收敛；**注意 22 含未跟踪的 test_o5 文件，见 N1**）+ regression_oldman_sea 13 条 |
| tool behavior | 30 工具 + JSON/XML 手工解析循环 | 30 工具不变（注册表与 O0 完全一致）；LangGraph StructuredTool 平移；新增机械治理（判重复用/硬上限/超时/溯源 provenance） |
| source integrity（口径） | 引用降级改写"保全面子"、记忆 blockquote 可发布、拼接风险靠事后审计 | validator 硬门 + quote_bound 逐字绑定审计；未核验对象零发布（脚本化矩阵 FN=1 处除外，见 F1）；live 口径归 Gate B |
| latency（口径） | 多层 runtime 语义等待（admission/sufficiency/no-gain 提示注入、双 writer 恢复） | runtime 语义等待层全部删除；新增 validator/repair 等待与 2ms/字打字机兜底；done 先行解锁 UI。P50/P95 live 实测归 Gate B |
| answer quality（口径） | composer 模板化结构风险 + 影子修正 | 结构由 Main Agent 自主；发布答案=验证过的候选逐字。24 题 live 深度评估归 Gate B |

---

## 11. §22 RAM Regression — PASS（尽力而为口径）

进程内 psutil 探针（脚本 `gate_a_ram_probe.py`；脚本化 LLM + **真实生产工具** search_books/get_chapter 走生产注册表，含真实向量检索调用）:

```text
RAM_IDLE（imports 完成后）    = 266.7 MB
RAM_GENERAL（general 首题后） = 365.6 MB（+98.9 MB——检索索引/数据首载）
RAM_NIETZSCHE（首题后）       = 365.7 MB（+0.1 MB）
12 连轮（general/nietzsche 交替）: 365.7 → 365.8 MB
last10_slope  = 0.000 MB/turn
last10_drift  = 0.0 MB
no_monotonic_leak = true（14/14 轮全部正常发布、validation ok）
```
无每轮单调泄漏，无结构性回退。（口径说明: 非独立 backend 进程实测，属任务书允许的"尽力而为"进程内探针；HTTP 服务进程叠加 FastAPI/uvicorn 常驻基线，Gate B 可复跑。）

---

## 12. Findings / Anomalies 清单（只记录，未修）

| # | 级别 | 内容 |
|---|---|---|
| **F1** | **Material（§17 判 FAIL 的直接原因）** | validator false-negative: 行内引导词引文最自然形态 `原文是：“…”` 被 quote_bound LEADIN_RE（quote_bound.py:49-52 与 :83-88 的 head 口径互斥）归为 `quoted` 豁免 → 伪逐字行内引文可零 issue 发布。blockquote 主通道不受影响。建议 Reviewer 评估窄补丁（修 LEADIN_RE 的 head 匹配口径即可，1-2 行） |
| **F2** | Material（边缘路径） | forced+cancel 边界: 图在 `forced && forced_tools_done` 终止时 `pending.has_tools` 卡 True（不再经过 tools_node 重置），repair 轮的新文本被 engine:1415-1418 当作残留工具轮清空 → repair 被击穿（安全收口但有效答案被丢弃）。触发窄（硬上限+残留宣告+空首候选）。建议后续 O6.x 窄修（repair 收尾不沿用首运行的 has_tools 状态） |
| N1 | 记录 | `backend/tests/test_o5_thin_runtime.py` 在工作区**未被 git 跟踪**（untracked）。pytest 按磁盘收集（本报告 350 计数含其 18 条）。不影响测试结果有效性，但与"GATE 冻结"口径需 Reviewer 知悉：建议 gate 提交时一并入库 |
| N2 | 记录 | `backend/evaluation_suite.py` 含 PremiseVerifier/scan_interpretation/AnswerComposer 同名符号——已证实为**离线评估专用副本**（仅 backend/tests 导入，main/routes 零引用），不属生产控制权；若担心误读可加模块头显式标注 |
| N3 | 记录 | 空 AIMessage("")（无内容无工具）经流式通道会触发 langgraph "No generations found"→ 引擎 graceful 同一 Main Agent 重试一次后正常恢复（行为正确，观察记录）；§18 R8 已改用纯空白候选测 EMPTY_FINAL |
| N4 | 记录 | 3 个专用工具首轮冒烟因 harness 参数名写错返回参数校验 error——属 harness 错误非工具缺陷，修正后 7/7 通过（两轮原始记录均保留） |

---

## 13. Gate A 维度初判（G1/G2/G3/G5/G11/G12/G15/G16 + 附带 G14）

| 维度 | 初判 | 依据 |
|---|---|---|
| **G16 Regression suite** | **PASS** | 350/350 全绿（FAILED=0, SKIPPED=0）；6 套件单跑全绿；oldman_sea 13 passed（+纯脚本运行） |
| **G1 Architecture ownership** | **PASS** | 剥注释 forbidden 扫描 code 级 0 命中；8 项零指标代码锚点+93 条 O 套件断言双证；唯一 cognitive owner 结构成立 |
| **G2 Tool authority** | **PASS** | 注册表与 O0 完全一致、零重复、零错误暴露；工具选择/继续/停止全在 Main Agent；runtime 仅 3 个机械门且行为实测正确（§20 E3/E4/E5） |
| **G3 Final ownership** | **PASS** | semantic mutators/factual appends=0（代码锚点+静态扫描 27→0）；候选缓冲→验证→逐字发布；repair 同一 Main Agent；invalid final 零发布（T10 kill test + §18 R6 + §20 E7 三重复证）。F2 为收口安全性完好下的边缘 repair 击穿，记录不降级本维度 |
| **G5 Validator integrity** | **FAIL（narrow）** | FP=0（无 blocker），但 FN=1（F1）违反"FALSE_NEGATIVE = 0"硬门。FN 面窄（行内引导词形态），blockquote/NEAR/拼接/citation/空候选全部正确拦截。按 §29 需 Reviewer 决定窄补丁 |
| **G11 SSE/provenance** | **PASS_WITH_NOTE** | 静态+脚本化全流程证据: 12 类事件词表收敛；tool/tool_start 全部 initiated_by=main_agent + decision_group_id/tool_call_id 绑定（O1 provenance，test_o1/o2/o3 断言）；tool_internal 伪记录显式标记；thought_stream/answer_retract/reasoning_summary 零发射。NOTE: reconnect/replay 与 24 题 live 事件流全量审计不在本 Gate A 范围（无 live harness），归 Gate B |
| **G12 Error behavior** | **PASS_WITH_NOTE** | 8/8 受控错误场景: 无 stack trace/秘密泄漏、无伪造事实、无 ghostwritten final、无效候选零泄漏、干净 done/error 收口。NOTE: F2（repair 文本丢失）发生在此类边界内——收口安全但修复有效性受损，已记录 |
| **G15 Tool/specialized capabilities** | **PASS** | 30/15 工具面完好；7/7 专用工具真实调用返回结构化产物；socratic 单问题契约（真实调用 + scripted 引擎路径）通过；无 missing/duplicate/wrong-exposure |
| （附带）G14 RAM/resource | **PASS**（尽力而为口径） | 进程内探针 slope 0.0 MB/轮、无单调泄漏（§11） |

**Gate A 总评**: 架构真相、回归、工具面、错误行为、RAM 全部达标；唯 §17 validator 质量门因 F1（1 例 false negative）未达硬门 → 按 O6 铁律仅报告不修，交 Reviewer 裁决（F1 窄补丁 / F2 边缘修复 / 接受为已知残余）。

*Live 质量维度（G4 thinking truth、G6 source attribution live、G7 research、G8 depth、G9 persona、G10 multi-turn、G13 latency 及 §15 SSE 全量审计）需 24 题 live 数据，归 Gate B。*
