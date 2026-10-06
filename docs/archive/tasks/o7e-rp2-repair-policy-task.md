审完了。这一轮我签 PASS，并正式授权 O7-E RP2。

ffbb21530 → 500bb8e88 的 production 变化范围是干净的：AgentState 现在正式声明了 no_tools: bool；hard-budget repair 进入 no_tools 后，agent_node 会跳过 hard-budget tool 提示，并且 _agent_llm_invoke(..., no_tools=True) 直接调用 get_llm().invoke()，不再 bind_tools()。这条链路现在从 State schema 到模型调用已经闭合。

canonical O7-E runner 也已经真正切换到 done.validation.history 与 repairs_used，并把 402/余额不足分类为 BLOCKED_MODEL_BILLING、排除 publication denominator；同时只要 completed cases 少于要求数量，最终状态就是 BLOCKED_INCOMPLETE，不会靠缩小分母偷过 Gate。

两代 Stage-B 产物也已经分开保存：首次 28-case 的 19/28 被独立归档，RP1 的 14 completed / 9 published / 14 billing-blocked 也明确标成 BLOCKED_INCOMPLETE。 500bb8e88 → 250500ee0 没有 production 改动，只有冻结测试切换到 committed-tree comparison，因此没有 Gate 后代码漂移。

正式裁定：

O7_E_RP1_FINAL_CLOSURE_REVIEW = PASS

REPAIR_STATE_CONTRACT = ACCEPTED
NO_TOOLS_REPAIR_PATH = ACCEPTED
HARD_BUDGET_COMPATIBILITY = ACCEPTED

CANONICAL_GATE_RUNNER = ACCEPTED
VALIDATION_HISTORY_ACCOUNTING = ACCEPTED
REPAIR_ATTEMPT_ACCOUNTING = ACCEPTED
BILLING_BLOCK_SEMANTICS = ACCEPTED
INCOMPLETE_GATE_PROTECTION = ACCEPTED

STAGE_B_FIRST_RUN_ARCHIVE = ACCEPTED
RP1_PARTIAL_ARCHIVE = ACCEPTED

ACCEPTED_RP1_CLOSURE_CODE_SHA =
500bb8e88dc4c2cd4087f66d498176147777cc24

ACCEPTED_RP1_CLOSURE_HEAD_SHA =
250500ee0e2c144490268532e20ff11284465e60

O7_E_RP2_AUTHORIZED = true
O7_E_FINAL_REVIEW = NOT_READY

有一个我在这次独立审计里额外发现的问题，不回头卡 RP1 Closure，但它必须在 O7-E 最终 Gate 前处理掉：

当前 evidence_contract 把 search_books/get_chapter/... 按“工具属于原典库”统称为 primary evidence；_base_evidence() 默认也是 source_type="primary"。 所以像哲学史、导论、二手讲解书，只要从 search_books 命中，也可能在 evidence contract 中被标成 primary；get_chapter 则固定成为 primary_read，并不判断“这本书是否真的是当前问题对象的原著”。

这会造成一种最终 Gate false-green：

search_books
→ 一本讨论柏拉图的二手书
→ source_type = primary
→ evaluator 误以为满足 PRIMARY_REQUIRED

生产 runtime 不需要为此重新引入“谁是问题对象”的 semantic router；RP2 在 evaluation layer 把 primary-source truth 校正即可。

TASK — O7-E RP2
Scholarly Repair Convergence & Primary-Evidence Integrity
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
250500ee0

TARGET_AGENT =
general

PHASE =
O7-E RP2 — SCHOLARLY REPAIR CONVERGENCE
           + PRIMARY EVIDENCE INTEGRITY
0. 目标

这一轮只解决两个已经被真实 Gate 证明存在的问题：

A.
Main Agent 已取得证据
但面对
NEAR_QUOTE_NOT_MARKED
UNSUPPORTED_EXACT_QUOTE
UNVERIFIED_CITATION
时，两轮 repair 经常不收敛

B.
evaluation 中“primary evidence”
目前可能把普通书库二手著作误算成原典

不做：

Growth
Whole-Book
Hermes
秘塔
新工具
哲学家 Agent
1. 冻结区

严格禁止修改：

backend/final_validator.py
backend/quote_bound.py

O7-B data
O7-C access semantics
O7-D registry/evidence/index

tool count
hard budget 20/24

philosopher agent behavior

要求：

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

HARD_RETRIEVAL_BUDGET=20
HARD_TOTAL_BUDGET=24

PHILOSOPHER_AGENT_RP2_DIFF=0
2. RP1 历史结果变成 calibration material

允许使用已经暴露过的：

STAGE_B_FIRST failures
RP1 calibration failures
RP1 partial failures

作为：

REPAIR_CALIBRATION_POOL

它们不再有 holdout 身份。

尤其收集至少：

NEAR_QUOTE_NOT_MARKED >= 3
UNSUPPORTED_EXACT_QUOTE >= 3
UNVERIFIED_CITATION >= 2

用于调 repair。

3. 真正的问题：Repair 当前没有足够的 evidence context

RP2 必须首先检查并修复这一点。

当前 repair message 主要是：

original request
+
old candidate
+
validator feedback

但本轮已经实际取得的 primary evidence，并不天然完整地重新出现在 repair context 中。

因此增加一个：

MECHANICAL_REPAIR_EVIDENCE_PACKET

必须是纯机械构造。

禁止 LLM 摘要。

4. Repair Evidence Packet

推荐结构：

JSON
{
  "issue_code": "...",
  "locator": "...",
  "evidence_ref": "...",

  "available_evidence": [
    {
      "evidence_id": "...",
      "book": "...",
      "chapter": "...",
      "author": "...",
      "retrieved_text_excerpt": "...",
      "match_state": "..."
    }
  ]
}

必须复用现有 evidence normalization / validator 已经形成的 evidence references。

禁止另造一套：

SemanticEvidenceMatcher
QuoteRepairRetriever
SourceRelevanceAgent
5. Packet 必须有界
MAX_EVIDENCE_PER_ISSUE <= 3
MAX_REPAIR_EVIDENCE_PACKET_CHARS <= 6000

只提供 validator issue 机械关联的材料。

禁止把 20 次 tool result 全塞回 prompt。

6. evidence_ref 命中时必须给真实文本

如果 issue 有：

evidence_ref

且已有 retrieved text，则 repair invocation 必须能看到相应原始文本片段。

硬测试：

issue.evidence_ref = ev_X

→ repair packet contains ev_X
→ contains actual retrieved text

否则 NEAR_QUOTE repair 仍然只能猜。

7. Repair Contract

保留：

Produce a complete replacement final candidate.

再加入通用证据纪律：

A verified exact quotation must reproduce the retrieved wording exactly.

If the available evidence supports the meaning but not the exact wording,
do not present a reconstructed sentence as a verbatim quotation.

A formal book/chapter citation must use a book/chapter identity actually
present in retrieved evidence.

If only book-level provenance is available, do not invent a chapter-level
citation.

这是静态 repair contract。

禁止：

if NEAR_QUOTE → 自动删引用
if UNVERIFIED_CITATION → 自动改某格式

Runtime 不做语义策略。

8. Scholarly Contract 允许最小修改

正式授权 RP2 修改 General Agent 的 canonical SCHOLARLY_CONTRACT。

只增加一小节：

H. 引文与出处纪律

语义必须覆盖：

逐字引文
→ 实际复制已取得文本

只有意思/近似措辞
→ 转述，不冒充逐字

正式章节引用
→ 使用实际取得的书名/章节身份

只有书级证据
→ 不伪造精确章节

同时必须写进 anti-gaming 原则：

当精确引文本身有研究价值且证据已经取得时，应正常使用；不得为了规避 validator 而系统性删除引文、出处或文本细节。

9. 不允许“少引用保平安”

报告必须统计：

EXACT_QUOTE_CASES
VERIFIED_EXACT_QUOTE_CASES

TEXTUAL_CASES
TEXTUAL_CASES_WITH_PRIMARY_READ

FORMAL_CITATION_USE_CASES
SECONDARY_EVIDENCE_USE_CASES

这些是 anti-gaming diagnostic。

10. Primary Evidence Gate 重新定义

不要再相信：

evidence.source_type == "primary"

就代表真正原典。

O7-E evaluator 增加 evaluation-only：

PRIMARY_TARGETS

case manifest 可写：

JSON
{
  "primary_targets": [
    {
      "author": "Immanuel Kant",
      "works": ["Critique of Pure Reason", "..."]
    }
  ],
  "primary_target_mode": "ANY"
}

中文 metadata 可使用 canonical book/work ids，优先用稳定 ID。

11. PRIMARY_REQUIRED 的真正含义

至少需要：

actual target primary author/work
+
actual text read

原则上：

get_chapter

或等价 verified primary-body evidence 才满足。

仅：

search_books snippet

不得单独满足严格的：

PRIMARY_REQUIRED

因为它只是定位候选���

12. Comparative Case

比如：

孟子 vs 荀子

允许：

primary_target_mode = ALL

则两边都必须实际具有 primary evidence。

不是读了《孟子》就算整个比较题 primary complete。

13. Broad Philosopher

例如：

柏拉图

至少要有一个真正：

Plato-authored primary work

的实际读取。

一本：

《西方哲学史》
《认识世界》
《100堂哲学课》

不能满足 Plato primary requirement。

14. Primary evaluator 不进入 production runtime

要求：

PRODUCTION_PRIMARY_SEMANTIC_ROUTER=0

这是 evaluation truth correction。

Main Agent 自己继续决定研究什么。

15. 新 Holdout 必须先冻结

RP2 必须建立全新的：

28 General-only Holdout

不得重复旧 Stage-B / RP1 的相同问题文本。

流程：

write cases
↓
commit
↓
freeze hash
↓
THEN tune policy

生成：

O7E_RP2_CASE_FREEZE_SHA
O7E_RP2_HOLDOUT_CASE_UNIVERSE_HASH
16. 28-case 结构

必须满足：

broad philosopher = 3
argument = 6
interpretive controversy = 6
textual/source = 3
historical development = 2
comparative = 2
Chinese philosophy = 5
literature/access stress = 1

总计 28。

同一 case 可同时属于 Chinese / comparative 等分析标签，但主 category 计数必须可审计。

17. Chinese

至少：

CHINESE_CASES >= 5

覆盖至少：

先秦 >= 3
宋明/后期 >= 1
比较问题 >= 1
18. Exact Quote Stress

新 Holdout 中至少 4 例预先确认 corpus 中确实存在可验证原文：

QUOTE_EXPECTATION = VERIFIED_EXACT_REQUIRED

用于阻止：

“把所有引文删掉就全绿”

这些 case 必须：

VERIFIED_EXACT_QUOTE >= 1

否则 case FAIL。

19. 其他 case

可标：

QUOTE_EXPECTATION =
PARAPHRASE_OK

不要求为了测试强塞引文。

20. Repair Calibration

在正式 policy freeze 前，对旧失败池运行 repair calibration。

要求：

REPAIR_CALIBRATION_CASES >= 8
EMPTY_FINAL = 0

如果：

REPAIR_ATTEMPTS >= 5

则：

REPAIR_SUCCESS_RATE >= 0.80

否则不得进入新 Stage B。

21. Calibration 可调范围

Stage A 可调：

SCHOLARLY_CONTRACT H
repair transport contract
mechanical repair evidence packet

禁止调：

validator
quote_bound
budget
tool behavior
22. Freeze Policy

Calibration 通过后：

freeze O7E_RP2_POLICY_SHA

从这一刻：

NO POLICY CHANGE
NO REPAIR CONTRACT CHANGE
NO CASE CHANGE
NO EVALUATOR CHANGE
23. Billing / provider 中断规则

如果 Stage-B 途中出现 402：

BLOCKED_MODEL_BILLING

可以充值后在同一 policy SHA + case hash + runner SHA 下续跑。

不用重开新 Gate。

条件：

completed outputs preserved
no production/evaluator/case change

直到：

COMPLETED_CASES = 28

才允许算 Final Gate。

24. Delivery Hard Gate
HOLDOUT_CASES = 28
COMPLETED_CASES = 28

FINAL_PUBLICATION_RATE >= 0.90

EMPTY_FINAL_AFTER_REPAIR = 0
TERMINAL_PENDING = 0
TOOL_LOOP_ABORTS = 0

PUBLIC_INVALID_CITATIONS = 0
UNVERIFIED_PUBLIC_EXACT_QUOTES = 0
STITCHED_PUBLIC_QUOTES = 0
PUBLIC_ACCESS_OVERCLAIMS = 0
25. Repair Convergence Gate

如果 RP2 Holdout：

QUOTE_OR_CITATION_REPAIR_ATTEMPTS >= 5

要求：

QUOTE_OR_CITATION_REPAIR_SUCCESS_RATE >= 0.80

并：

REPAIR_CREATES_NEW_FATAL_ERROR = 0
26. Primary Truth Gate
FALSE_PRIMARY_EVIDENCE_CREDITS = 0

REQUIRED_PRIMARY_EVIDENCE_MISSING = 0
REQUIRED_PRIMARY_TARGETS_MISSING = 0

SECONDARY_BOOK_MISCOUNTED_AS_TARGET_PRIMARY = 0
27. Exact Quote Gate

对 4+ VERIFIED_EXACT_REQUIRED cases：

EXACT_QUOTE_REQUIRED_CASES >= 4
EXACT_QUOTE_REQUIRED_PASS_RATE = 1.0

不是：

“找不到就删掉引文”

因为这些 case 在 freeze 前必须先机械确认 corpus coverage。

28. 学术质量门保持不变
APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0
29. Fatal flags 不改
FABRICATED_BIBLIOGRAPHY = 0
FABRICATED_SCHOLAR_ATTRIBUTION = 0
PRIMARY_TEXT_MISREPRESENTATION = 0
MAJOR_ANACHRONISM = 0
FALSE_EXACT_QUOTE = 0
LITERATURE_ACCESS_OVERCLAIM = 0
30. Secondary Evidence

继续：

METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ

原 O7-C access contract 不变。

要求：

UNBACKED_NAMED_SCHOLARLY_ATTRIBUTIONS = 0
REQUIRED_SECONDARY_EVIDENCE_MISSING = 0
31. Judge

仍然：

glm-4.6
temperature=0
thinking=disabled
json_object
k=3

不重做 bakeoff。

32. Live Smoke

正式 Holdout 双轴 PASS 后才运行：

LIVE_SMOKE_CASES = 8

检查：

Crossref/OpenAlex
local/live dedup
retrieval_origin
access honesty

provider outage 可 BLOCKED，不得造数据。

33. Runner / Artifact

Final artifact 必须明确包含：

policy_sha
case_universe_hash
runner_sha
evaluator_sha
gate_sha

这次补上 archive 中缺失的 runner provenance。

输出：

docs/evidence/
  PHIAGENT_O7E_RP2_HOLDOUT_CASES.json
  PHIAGENT_O7E_RP2_FINAL_GATE.json
  o7e_runs_HOLDOUT_RP2_FINAL.json

旧 artifact 一律不覆盖。

34. Tests

至少新增：

P1 repair packet includes referenced evidence
P2 repair packet uses real retrieved text
P3 repair packet bounded
P4 no LLM builds repair packet
P5 no unrelated evidence flood

P6 near quote repair can converge
P7 unsupported quote repair can converge
P8 unverified citation repair can converge
P9 exact-required quote not deleted to game validator

P10 secondary commentary book cannot satisfy target-primary
P11 target author's get_chapter satisfies primary
P12 search snippet alone does not satisfy strict PRIMARY_REQUIRED
P13 comparative ALL requires both sides
P14 broad philosopher target-primary works

P15 no production primary router
P16 validator unchanged
P17 quote_bound unchanged
P18 budget unchanged
P19 philosopher agent unchanged

P20 Stage-B incomplete cannot pass
P21 billing resume preserves same universe/policy
P22 runner/evaluator SHAs recorded
35. 最终报告
docs/PHIAGENT_O7E_SCHOLARLY_FINAL_QUALITY_GATE.md

继续使用原 O7-E report，不另造冲突 final report。

明确保留：

Stage-B First = 19/28
RP1 Partial = 9/14 completed, billing blocked 14
RP2 Final = ...

三代历史。

FINAL RECEIPT
O7_E_RP2 =
READY_FOR_FINAL_REVIEW /
PATCH_REQUIRED /
BLOCKED_INCOMPLETE /
BLOCKED

BASE_SHA=

CASE_FREEZE_SHA=
HOLDOUT_CASE_UNIVERSE_HASH=

POLICY_CODE_SHA=
O7E_RP2_POLICY_SHA=

RUNNER_SHA=
EVALUATOR_SHA=

O7E_RP2_FINAL_GATE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

TARGET_AGENT=general

REPAIR_CALIBRATION_CASES=
REPAIR_CALIBRATION_ATTEMPTS=
REPAIR_CALIBRATION_SUCCESS=
REPAIR_CALIBRATION_SUCCESS_RATE=

REPAIR_EVIDENCE_PACKET=true
REPAIR_PACKET_MAX_CHARS=
REPAIR_PACKET_LLM_CALLS=0

HOLDOUT_CASES=28
COMPLETED_CASES=
BLOCKED_MODEL_BILLING=

FINAL_PUBLICATIONS=
FINAL_PUBLICATION_RATE=

VALIDATION_FAILURES=
REPAIR_ATTEMPTS=
REPAIR_SUCCESS=
REPAIR_SUCCESS_RATE=
REPAIR_EXHAUSTIONS=

QUOTE_OR_CITATION_REPAIR_ATTEMPTS=
QUOTE_OR_CITATION_REPAIR_SUCCESS=
QUOTE_OR_CITATION_REPAIR_SUCCESS_RATE=

EMPTY_FINAL_AFTER_REPAIR=

EXACT_QUOTE_REQUIRED_CASES=
EXACT_QUOTE_REQUIRED_PASS=
EXACT_QUOTE_REQUIRED_PASS_RATE=

FALSE_PRIMARY_EVIDENCE_CREDITS=
SECONDARY_BOOK_MISCOUNTED_AS_TARGET_PRIMARY=
REQUIRED_PRIMARY_EVIDENCE_MISSING=
REQUIRED_PRIMARY_TARGETS_MISSING=
REQUIRED_SECONDARY_EVIDENCE_MISSING=

APPLICABLE_DIMENSION_MEAN=

TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=

FABRICATED_BIBLIOGRAPHY=
FABRICATED_SCHOLAR_ATTRIBUTION=
PRIMARY_TEXT_MISREPRESENTATION=
MAJOR_ANACHRONISM=
FALSE_EXACT_QUOTE=
LITERATURE_ACCESS_OVERCLAIM=

UNBACKED_NAMED_SCHOLARLY_ATTRIBUTIONS=
PUBLIC_INVALID_CITATIONS=
UNVERIFIED_PUBLIC_EXACT_QUOTES=
STITCHED_PUBLIC_QUOTES=
PUBLIC_ACCESS_OVERCLAIMS=

PRIMARY_EVIDENCE_USE_RATE=
SECONDARY_EVIDENCE_USE_RATE=

LIVE_SMOKE_CASES=
LIVE_SMOKE_PROVIDER_ERRORS=
LIVE_SMOKE_FATAL_FLAGS=

HARD_RETRIEVAL_BUDGET=20
HARD_TOTAL_BUDGET=24
BUDGET_INCREASED=false

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false
O7C_ACCESS_SEMANTICS_CHANGED=false
O7D_CORPUS_CHANGED=false

PHILOSOPHER_AGENT_RP2_DIFF=0

COGNITIVE_POLICY_OWNER=1
SCHOLARLY_POLICY_OWNER=1
PRODUCTION_PRIMARY_SEMANTIC_ROUTER=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7E_SCHOLARLY_FINAL_QUALITY_GATE.md

O7_E_FINAL_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP

还有一个非阻塞审计备注：这次归档的旧 Stage-B/RP1 partial metadata 没有 runner_sha；而 RP1 partial 本来就是旧 worktree runner 产生的，所以也不可能现在诚实地伪造一个 canonical runner SHA。我不要求为历史 artifact 再打补丁，RP2 Final 从此强制把 runner_sha + evaluator_sha 写进 Gate artifact 即可。

接下来真正值得看的就是：RP2 能不能做到——不是少引用，而是会正确引用；不是少用原典，而是真的分清什么才是原典。