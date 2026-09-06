# O5 §1 RUNTIME RESIDUAL INVENTORY（审计报告，BASE=2de12b4ec + 引用块纪律 diff）
# 执行代理：以下为权威删除/合并/迁移清单，行号指当前工作区。

## 一、DELETE 清单（死符号/死分支）
1. engine `_derive_read_info`（L409–439, 31 行，零消费者）
2. engine `TOOLS_BY_NAME`（L185，生产零 caller；test_epistemic_guard:158 与 tools/dp_uat_phase_a:113 引用 → 测试改用 TOOLS_LG）
3. engine `_sse`（L667，零 caller）
4. engine `RATIONAL_STATS`（L940 定义 + L1161–1164 写入，全仓零读者）
5. engine `pending["reasoned"]`（L1135/1299/1304 只写不读）+ AgentState.model_retries（write-only）
6. quote_bound `VERIFY_LATER_RE` + `VERIFY_LATER_OPEN_RE`（L53–58，生产零消费者）
7. evidence_contract `_CITE_REPLACE_ZH/_EN`（L636–637 零消费者）+ sanitize_citations 内 rebind/downgrade 改写分支（裁剪为只读 audit 断言，~-50 LOC；sanitized_text 本就被丢弃）
8. agent_runtime `_QUOTE_NORM`（L399，随 ObligationLedger.term 删除）
9. routes/agent.py `SYSTEM_PROMPT` + `_SYS_TOOL_LIST`（~165 行，零消费者——本次最大单体死代码）
10. routes/openai_compat.py L169 `if t in ("thought_stream","thought")` 死映射分支
11. engine done 字段 `live_citation_sanitize`（静态审计 dict，前端零消费）
12. NIETZSCHE_PROMPT 铁律 9（"工具调用前不要输出任何文字"——与铁律 0 工作笔记纪律冲突，删除使 philosopher 走通 thinking_summary 通道）+ 修复 NIETZSCHE_PROMPT 铁律编号错乱（1,2,3,2,3,4…）
13. SYSTEM_PROMPT_LG 规则 14（"会被系统拦截"——SkillReentryTracker 已删，宣称失实）收敛为"避免退化重复"纪律描述
14. evidence_contract `EpistemicClaimClassifier.split_sentences` method（D6：与模块级 _split_sentences 重复；evaluation_suite 改用模块函数）
15. tools_node docstring 陈旧闸门声明（声称含安全/取消——实际无）与 flush_agent docstring 过期描述：修正
16. engine 模块 docstring L5 事件清单更新为实际 12 类

## 二、MERGE（ObligationLedger → EvidenceState）
- 删除 agent_runtime `ObligationLedger` 整类（现余 term[无喂入口]/read_chapters/primary_text_read/exact_quote_verified[生产零喂入口]/source_candidate_found/search_execs/read_execs/snapshot）
- 新建轻量 `EvidenceState`（放 evidence_contract.py，机械事实登记）：read_chapters/primary_text_read/source_candidate_found/search_execs/read_execs + record(search/execute 事实) + snapshot()；engine 构造/record/done 消费点同步
- done payload：删除 `obligation_ledger` 字段；事实并入 `done.evidence`（新增子键如 `"facts": {read_chapters, primary_text_read, source_candidate_found, search_execs, read_execs}`——build_evidence_contract 产 dict，加键安全，前端只读 retrieved_count）
- 同步测试：test_o1_causal_loop（obligation_ledger 断言位）、test_phase_t1、test_o3（ledger 构造）、test_patch1_1（事实登记断言改 EvidenceState）

## 三、MERGE/MOVE（验证重复 D1/D4/D6 + 错位迁移）
- D1：agent_runtime._QUOTE_NORM 随 term 删除（归一真源=quote_bound.norm_q）✓（见一.8）
- D4：证据池构建单一真源——evidence_contract 暴露 `evidence_spans(raw_tool_log)`（或等价）供 quote_bound 消费；quote_bound.evidence_spans 改为薄委托或直接 import（字段映射只维护一份）
- D6：删 EpistemicClaimClassifier.split_sentences method；evaluation_suite 改用 evidence_contract._split_sentences
- MOVE：evidence_contract 的 `_match_philosopher`/PHILOSOPHER_ALIASES/_norm_author/_load_philosophers（内部零调用，唯一消费者 evaluation_suite）+ `EPISTEMIC_LANGUAGE`/`language_bound`（生产零消费者）→ evaluation_suite 自带副本；`_claim_role` 若仅审计用途可留
- MOVE：`sanitize_citations` 裁剪为只读 `audit` 断言（见一.7）

## 四、KEEP（机械核心，勿动）
tools_node 五闸（硬上限/精确判重/未知工具/超时/重试+FALLBACK）、repair≤2 耗尽零发布、单源 _build_context_messages、RationaleParser/_visible_text/_strip_*/PhraseScrubber、quote_bound 核验三件套（extract/evidence_spans[或其委托]/verify/audit）+DISCLOSED_RE/LEADIN_RE/BLOCKQ_LINE_RE、DISCLOSED 豁免、evidence_contract 主流程（含 SPECULATION 不绑定 DIRECT——机械证据绑定）、DuplicateGuard/ToolBudget(hard+遥测计数)/ToolLoopTrace、safety、temporal 三件套、suggestions、TOOL_TAXONOMY/scaffold_result/mermaid/extract_json、FALLBACK_MAP。

## 五、已知事实（供测试适配）
- 引擎实际发射 12 类事件：status/thinking_summary/thinking_summary_delta/tool_start/tool_note/tool/tool_cancel/token/validation_failed/error/done/suggestions；thought_stream/thought/answer_retract/reasoning_summary/auto_read 零发射（T7 断言依据）
- 前端 agent-app 只消费 done 的 citations/evidence(retrieved_count)/suggestions/safety/safety_reply；validation_failed 前端无分支（删除发射安全，但本拍保留亦可——若保留注明）
- 前端不读 done.obligation_ledger/tool_loop/causal/final_ownership/validation/timing/...（消费者=tests/UAT）
- NIETZSCHE_PROMPT 删铁律 9 后，philosopher 轮将开始产生工作笔记（thinking_summary 通道）——O1 契约对哲学家生效，属预期修复
