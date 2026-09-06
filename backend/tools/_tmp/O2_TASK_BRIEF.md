# O2 TASK BRIEF — Final Answer Ownership / Validator → Main-Agent Repair Loop
(从 ChatGPT 对话抓取，仅本地参考，不提交 git)

MODEL=GLM-5.3-Flash REASONING=MAX REVIEWER=GPT-5.6 Sol
BRANCH=refactor/phiagent-main-agent-orchestration
BASE_SHA=c7dc4c7c940d5af2fcb0909b5e66fd8fe7c882f4
PRECONDITION=O1_FINAL_REVIEW=PASS
DO NOT: merge master / modify preservation / start O3 / add semantic regex / new obligation / new intent classifier / replace one runtime ghostwriter with another

## 0. Objective
O2 解决：谁写用户最终看到的自然语言答案 → Main Agent only
目标架构：Main Agent → Final Candidate → Deterministic Validation → PASS publish / FAIL → structured issues → SAME Main Agent → repair/research → new final → validate
Runtime 可：VALIDATE / REJECT / mechanical FORMAT / safety / transport
Runtime 不得：semantic rewrite / factual append / philosophical append / quote→paraphrase / certainty hedge / correction-note / verified-source prose append
最终目标：FINAL_TEXT_OWNER=MAIN_AGENT; SEMANTIC_MUTATORS_AFTER=0; RUNTIME_FACTUAL_APPENDS_AFTER=0; MAIN_AGENT_FINAL_OWNERSHIP_RATE=100%; safety 单列

## 1. BEFORE — Final Mutation Trace（先复现后改，禁止先改代码）
F1 言必有中出处 F2 MEMORY_ONLY exact quote F3 NEAR quote F4 unverified formal citation F5 strong-certainty interpretive F6 ordinary zero-tool
捕获 candidate → processors → published；每步记 MODULE/FUNCTION/OWNER/DELETE/REPLACE/APPEND/CHANGE_SEMANTICS/INPUT/OUTPUT
重点审计活跃路径：LiveCitationSanitizer / QuoteBoundSanitizer / TermClaimGate / scan_final_consistency / VERIFY_LATER correction / verified quote visibility append / epistemic factual+counterfactual tails / scan_interpretation / scan_composition / short-answer fallback / answer_retract / safety replacement / mechanical formatting
产出：POST_LLM_MUTATORS_BEFORE / SEMANTIC_MUTATORS_BEFORE / RUNTIME_FACTUAL_APPENDS_BEFORE / FINAL_RETRACTS_BEFORE（必须基于真实 production path，不只 grep）

## 2. Ownership Boundary
MECHANICAL_MUTATORS（允许）：XML/internal tag removal、control-char stripping、markdown normalization、citation-link rendering、SSE framing、safety enforcement
SEMANTIC_MUTATORS（必须=0）：事实/哲学/claim certainty/quote-paraphrase 区分/correction content 的任何修改

## 3. Validation Schema（thin，复用已有 Evidence/QuoteBound）
ValidationResult(ok, issues[]); ValidationIssue(code, locator, evidence_ref?, detail?)
允许 code：UNVERIFIED_CITATION / UNSUPPORTED_EXACT_QUOTE / NEAR_QUOTE_NOT_MARKED / STITCHED_QUOTE / INVALID_SOURCE_BINDING
禁止新增认知治理 code（SOURCE_ATTRIBUTION_REQUIRED 等）

## 4. QuoteBound — keep verify, delete ghostwriting
保留：quote extraction / verify_quote / stitch detection / audit_quotes / evidence span binding
删除：MEMORY_ONLY→runtime paraphrase；NEAR→runtime appended disclaimer；stitched→runtime replacement；scan_final_consistency→runtime correction prose
新行为：MEMORY_ONLY→validator UNSUPPORTED_EXACT_QUOTE；NEAR 当 exact→NEAR_QUOTE_NOT_MARKED；stitched→STITCHED_QUOTE；反馈给 Main Agent 自行决定

## 5. Citation Ownership
保留 evidence pool/binding/verification；final citation 无 verified evidence → UNVERIFIED_CITATION → repair（禁止自动 downgrade 为 plain mention）；citation markdown 语法错误可机械修正

## 6. TermClaimGate
删除 semantic rewrite（改写句子/追加"该固定措辞未核验"）；机械可验证信息→ValidationIssue；纯 Patch1 遗产→直接删除；禁止换名 regex rewriter

## 7. Post-hoc Semantic Tails 全部处理
scan_final_consistency 尾补 / VERIFY_LATER correction / verified quote visibility append / epistemic correction tail / counterfactual boundary tail / interpretation hedge append / composer hedge append
机械可验证→ValidationIssue；哲学/语义判断→删除；禁止旧 tail 删除→新 RepairSanitizer tail（视为 FAIL）

## 8. Short Answer Fallback
删除 60 字 semantic heuristic；仅保留 empty/whitespace/transport failure 机械 fallback → SAME Main Agent retry，不得独立第二 writer

## 9. Validator → Same-Agent Repair Loop
FAIL 反馈中性（列 issues），不得命令具体动作；repair invocation 绑定完整 tool set，允许继续调工具；遵守 O1 causal contract（top-level tools 必须由 Main Agent 宣告）

## 10. Repair Ceiling
MAX_VALIDATION_REPAIRS=2（机械上限）；达上限不 ghostwrite；宁可无 formal quote/citation 也不伪造

## 11. Final Streaming
Thinking/tool activity 实时；Final Candidate 内部缓冲，validator PASS 后才公开 stream/replay；INVALID_FINAL_PUBLICLY_STREAMED=false；禁止 publish→retract→correct

## 12. answer_retract
FINAL_RETRACT_SEMANTIC_USE=0；仅允许 transport/rendering 恢复

## 13. Safety
保留，initiated_by=safety_runtime，不计入普通 semantic mutator 指标

## 14. Tests T1–T10
T1 unsupported exact quote→validator FAIL+repair+发布文本来自 Main Agent
T2 NEAR 当 exact→fail+模型自行标注/转述，runtime 不加 disclaimer
T3 unverified citation→fail→repair，禁止自动 downgrade
T4 stitched→捕获+never public+repair
T5 first-pass valid→repair_invocations=0，语义文本不变（机械格式除外）
T6 repair can research→fail→repair 宣告 get_chapter→new final PASS，validator 自己不调工具
T7 no runtime factual append→public semantic text 全部 source=main_agent
T8 invalid final never public→sentinel 不出现在任何 public answer event
T9 mechanical formatter 保留，语义不变
T10 repair ceiling≤2，无无限循环无 ghostwriting

## 15. Preserve O1 Tests
test_o1_causal_loop.py / test_o1_rp1_thinking_safety.py 全绿；ENGINE_COGNITIVE_AUTO_TOOLS=0; TOP_LEVEL_TOOL_WITHOUT_AGENT_DECISION=0; RAW_PROVIDER_REASONING_PUBLIC=0; RUNTIME_GENERATED_THINKING=0

## 16. Live UAT U1–U6
U1 言必有中出处（self-research+primary read+validator PASS+零 runtime append+零 semantic retract）
U2 伪引文诱骗（fail→repair→不伪造）
U3 拼接诱骗（stitched never public）
U4 深哲综合题（删 runtime hedge 后深度不退化）
U5 zero-tool（无无意义 repair/延迟爆炸）
U6 Nietzsche persona（persona final voice 不受损）

## 17. Metrics
POST_LLM_MUTATORS_BEFORE/AFTER; SEMANTIC_MUTATORS_BEFORE/AFTER; RUNTIME_FACTUAL_APPENDS_BEFORE/AFTER; FINAL_RETRACTS_BEFORE/AFTER; FINAL_RETRACT_SEMANTIC_USE; VALIDATOR_REPAIR_INVOCATIONS; MAIN_AGENT_FINAL_OWNERSHIP_RATE; INVALID_FINAL_PUBLICLY_STREAMED
目标：SEMANTIC_MUTATORS_AFTER=0; RUNTIME_FACTUAL_APPENDS_AFTER=0; FINAL_RETRACT_SEMANTIC_USE=0; OWNERSHIP_RATE=100%; INVALID_FINAL_PUBLICLY_STREAMED=false

## 18. Quality
对比 O1：PRIMARY_READ_RATE / CITATION_INTEGRITY / QUOTE_INTEGRITY / RESEARCH_DEPTH / ANSWER_DEPTH / TOOL_COUNT / P50_LATENCY / P95_LATENCY；validator fail→修好是正常工作

## 19. Scope Guard
禁止：reasoning_plan 全面删除 / semantic_obligations 全面删除 / admission+sufficiency 全面重构 / tool-internal authority / 38 tools redesign / retrieval ranking / embedding / KG / Persona / frontend

## 20. Automated Gate
pytest backend/tests -q 全量不得排除任何测试；FAILED=0；单列 O1 causal / O1 thinking safety / O2 ownership

## 21. Documentation
docs/PHIAGENT_O2_FINAL_ANSWER_OWNERSHIP.md：BEFORE mutation chain / AFTER ownership graph / schema / repair loop / deleted semantic mutators / kept mechanical validators / stream buffering / retract audit / T1–T10 / U1–U6 / metrics / known issues

## 22. Git
branch refactor/phiagent-main-agent-orchestration；commit "refactor(phiagent): return final answer ownership to main agent"；push；不得 merge master / 改 preservation / 开 O3

## FINAL RECEIPT 模板
O2=READY_FOR_REVIEW/NOT_READY; BASE_SHA=; FINAL_SHA=; CHANGED_FILES=; POST_LLM_MUTATORS_BEFORE/AFTER=; SEMANTIC_MUTATORS_BEFORE/AFTER=; RUNTIME_FACTUAL_APPENDS_BEFORE/AFTER=; FINAL_RETRACTS_BEFORE/AFTER=; FINAL_RETRACT_SEMANTIC_USE=; MAIN_AGENT_FINAL_OWNERSHIP_RATE=; INVALID_FINAL_PUBLICLY_STREAMED=; VALIDATOR_SCHEMA=; VALIDATION_REPAIR_LOOP=; MAX_VALIDATION_REPAIRS=; QUOTE_VALIDATOR=; CITATION_VALIDATOR=; TERMCLAIMGATE=; INTERPRETATION_TAIL=; COMPOSER_TAIL=; EPISTEMIC_TAIL=; VERIFY_LATER_TAIL=; VERIFIED_QUOTE_APPEND=; SHORT_ANSWER_FALLBACK=; FINAL_BUFFERING=; T1..T10=; U1..U6=; PRIMARY_READ_RATE=; CITATION_INTEGRITY=; QUOTE_INTEGRITY=; RESEARCH_DEPTH=; AVG_TOOLS=; P50_LATENCY=; P95_LATENCY=; O1_CAUSAL_TESTS=; O1_THINKING_SAFETY_TESTS=; O2_OWNERSHIP_TESTS=; FULL_TEST_COMMAND=; COLLECTED=; PASSED=; FAILED=; SKIPPED=; REMOTE_SHA=; REPORT=docs/PHIAGENT_O2_FINAL_ANSWER_OWNERSHIP.md; KNOWN_ISSUES=; STOP
