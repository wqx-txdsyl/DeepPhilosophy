Reviewer Final Verdict
REVIEW_VERDICT=PASS

O9_UI_DESIGN=PASS
O9_R1_UI_WIRING=PASS
O9_FINAL=PASS

CURRENT_GATE_PASSED=true
NEXT_PHASE_DISPATCH=O10
USER_DECISION_REQUIRED=false
METASO_BLOCKS_MAINLINE=false

O9 可以正式关闭。

我独立核对到：

Research Phase 已实际接入 MessageList 的 tool start、merged、单 tool、展开行，而不是只存在一个未调用函数。

五态纯函数完整存在，SOURCE_VERIFY 有确定性路径，且核验文本优先于普通工具映射。

Depth Controls 已从 lang={undefined} 改为真实 lang，中英文 prompt 分开。

测试覆盖五态、双语、layer 回归和真实 wiring 源码断言。

R1 UAT 7 项及 production build PASS 已归档。

正式远端分支 HEAD 为 8f529480e3b0bdedb864da1afb5f7da83407f03b，并包含此前 state commit。

Vercel 在最新 O9 reviewed HEAD 上仍失败，继续作为 O14 deployment carryover，不影响 O9 终签。

下面直接进入 O10。

PhiAgent O10 — Core Repair + Final Requalification
O10 — Core Repair + Final Requalification

Builder: ZCode / GLM-5.3
Reviewer: GPT-5.6 Sol
BASE: 8f529480e3b0bdedb864da1afb5f7da83407f03b

Goal

修复 O8 Final Issue Ledger 中所有 O10-owned core issues，然后用冻结基准重新资格认证并冻结 PhiAgent Core。

目标：

O10_CORE_REPAIR=PASS
O10_FINAL_REQUALIFICATION=PASS
PHIAGENT_CORE_FROZEN=true
Scope
P0 — 必修
P0-01 Over-research
P0-02 Duplicate Retrieval / Convergence
P0-03 Tool Selection Discipline

要求：

简单题默认不检索。

明确“看原典”才走 primary retrieval。

学术研究问题才升级 scholarly path。

exact duplicate retrieval 必须阻止。

similar/no-new-information retrieval 必须收敛。

research/repair spinning 必须有 deterministic stop。

不得为了压 TOOL_CALLS 牺牲证据需求。

P1 — 必修
P1-01 philosopher_debate speakers robustness
P1-02 search_books empty-query + relevance floor
P1-03 FULL_REWRITE safety parity
P1-04 repair transient regression
P1-05 comparison primary-text anchoring
P1-06 scholarly second-hop
P1-07 paper_review routing
search_books

不得拍脑袋把 0.35 改成另一个常量。

建立正/负 calibration cases，依据实际分布确定 relevance policy。

必须：

empty query -> explicit invalid/empty semantics
irrelevant query -> no misleading useful hit
relevant query -> recall 不发生明显倒退
FULL_REWRITE

达到 Local Patch 等价安全合同：

post-repair semantic validation
GENUINELY_NEW evidence-family detection
AMBIGUOUS fail-closed
rollback
pre-repair candidate preservation

Local Patch 原合同不得回退。

Repair transient

任何会引入新 fatal/evidence-family issue 的 repair candidate：

reject before acceptance
rollback immediately

不得靠下一轮再修回来。

Scholarly second-hop

当最终回答实际依赖某 scholarly result：

search_scholarship
→ select source
→ get_scholarly_source
→ evidence

“只发现标题然后直接写答案”不得视为完整 scholarly research。

P2 — Core fixes

修：

P2-01 empty-input silent defaults
P2-02 empty-result semantics

禁止：

空输入 -> 默认柏拉图
不存在目标 -> 全集/模糊伪命中
Policy-only

P2-03 / P2-04 本轮只形成 policy，不扩 corpus：

LOCAL_CURATED metadata policy
primary-text 410 / placeholders policy

交付：

O10_POLICY_DECISIONS.json

明确：

SOURCE_OF_TRUTH
KNOWN_LIMITATION
FUTURE_ACTION
CORPUS_CONTENT_CHANGED=false
Deferred
P2-05 orphan files

仍然：

DELETE_CANDIDATE
DELETE_AUTHORIZED=false
OWNER=O13/O14

不得删除。

Repair Order

按顺序执行：

1. Tool/retrieval correctness
2. Routing discipline
3. Duplicate/convergence control
4. Repair safety parity
5. Targeted regression
6. Frozen benchmark requalification
7. Core freeze

禁止一边跑 final benchmark 一边继续调参。

Pre-Qualification Freeze

进入正式 requalification 前生成：

O10_REPAIR_MANIFEST.json

冻结：

REPAIR_HEAD=
CORE_CONFIG_HASH=
PROMPT_HASH=
TOOL_REGISTRY_HASH=
RETRIEVAL_POLICY_HASH=
REPAIR_POLICY_HASH=

然后：

QUALIFICATION_CONFIG_FROZEN=true

冻结后不得根据 benchmark 结果再调 production。

Targeted Gates

必须逐项复测 15-item ledger。

输出：

O10_ISSUE_CLOSURE.json

每项：

ISSUE_ID
OWNER
BEFORE_EVIDENCE
FIX
TARGETED_TEST
RESULT
RESIDUAL_RISK
STATUS=CLOSED/POLICY_CLOSED/DEFERRED

硬门：

P0_OPEN=0
P1_OPEN=0
P2_CORE_OPEN=0
Efficiency Hard Gates

对 exact duplicate：

EXACT_DUPLICATE_CALLS=0

简单题 frozen category：

SIMPLE_CASES=6
OVERRESEARCH=0
MEAN_TOOL_CALLS<=1.0

EP 6：

EP_OVERRESEARCH<=1

对所有 case：

NO_NEW_INFORMATION_LOOP=0
UNBOUNDED_RESEARCH_LOOP=0

不要通过截断必要研究来作弊。

Tool-selection Targeted Gates

必须通过：

simple SHOULD_NOT_RESEARCH
hard-primary MUST_CONTACT_PRIMARY_TEXT
scholarly MUST_SECOND_HOP_WHEN_EVIDENCE_USED
paper review MUST_ROUTE paper_review
comparison exact quote MUST_ANCHOR verified primary evidence
Repair Safety Gates
LOCAL_PATCH_PARITY_REGRESSION=PASS
FULL_REWRITE_PARITY=PASS
AMBIGUOUS_FAIL_CLOSED=true
ROLLBACK_PARITY=true
ACCEPTED_REPAIR_NEW_FATAL_ISSUES=0
Final Requalification

使用原冻结：

O8-R2 72 cases
+
O8-R3 EP 6 cases

共：

78 cases

不得改题。

同 production path。

重新记录：

LLM_CALLS
TOOL_CALLS
RETRIEVAL_ROUNDS
DUPLICATE_CALLS
REPAIR_COUNT
TOKEN_USAGE
LATENCY
publication_state
failure_codes
judge 7 axes / 12 dimensions
Quality non-regression

相对 O8：

philosophical_depth
argument_quality
explanation_quality
evidence_discipline

不得出现明显总体下降。

硬门：

HONESTY_FATAL=0
FALSE_EXACT_QUOTE=0
UNSUPPORTED_CITATION_PUBLISHED=0

若 honest degradation 是因为真实 corpus limitation，可保留，不得为了 78/78 发布而伪造。

Tool Registry Requalification

32 tools：

Mechanical targeted regression
Agentic routing regression

至少重新验证所有 O8 曾 FAIL 的 cells。

最终：

UNUSED_TOOL_COUNT=0
KNOWN_BROKEN_TOOL_COUNT=0

如某 tool 已证明无产品价值，不能偷偷留着；必须提交 Reviewer 做 KEEP/DEPRECATE 决定。

Frontend Regression

O9 不得回退：

EP UX
Depth Controls
Research Phase
Citation layering
SourceDrawer
mobile 390px

执行：

agent-app tests
production build
Boundaries

不得：

扩 corpus
做 MetaSo/OpenAlex 集成
实现 O11 Reader State
实现 O12 persistence
删除 orphan files
做 O13 全产品 polish
修 Vercel deployment

Vercel carryover更新为：

O14_DEPLOYMENT_CARRYOVER=
VERCEL_STATUS_FAILURE_AT_O9_REVIEWED_HEAD_8f529480e
Deliverables
O10_REPAIR_MANIFEST.json
O10_ISSUE_CLOSURE.json
O10_POLICY_DECISIONS.json
O10_REQUALIFICATION_RESULTS.json
O10_EFFICIENCY_COMPARISON.json
O10_TOOL_REQUALIFICATION.json
O10_FINAL_REPORT.md
Final Gate

只有全部满足：

P0_OPEN=0
P1_OPEN=0
P2_CORE_OPEN=0

QUALIFICATION_CONFIG_FROZEN=true

EXACT_DUPLICATE_CALLS=0
SIMPLE_OVERRESEARCH=0
EP_OVERRESEARCH<=1

FULL_REWRITE_PARITY=PASS
ACCEPTED_REPAIR_NEW_FATAL_ISSUES=0

78_CASE_REQUALIFICATION_COMPLETE=true
QUALITY_NON_REGRESSION=true

KNOWN_BROKEN_TOOL_COUNT=0
HONESTY_FATAL=0

BACKEND_TESTS=PASS
FRONTEND_TESTS=PASS
FRONTEND_BUILD=PASS

CORPUS_CONTENT_CHANGED=false
O9_UI_REGRESSION=false

才允许：

O10_FINAL_STATUS=PASS
PHIAGENT_CORE_FROZEN=true

之后自动：

→ O11 Adaptive Reader

不得询问用户。

Final Receipt
BASE_SHA=
REPAIR_HEAD=
QUALIFICATION_HEAD=
ARCHIVE_HEAD=
REMOTE_SHA=

O10_ISSUES_TOTAL=15
P0_CLOSED=
P1_CLOSED=
P2_CORE_CLOSED=
P2_POLICY_CLOSED=
P2_DEFERRED=

QUALIFICATION_CONFIG_FROZEN=true

REQUALIFICATION_CASES=78
REQUALIFICATION_EXECUTED=
REQUALIFICATION_PUBLISHED=

LLM_CALLS=
TOOL_CALLS=
RETRIEVAL_ROUNDS=
EXACT_DUPLICATE_CALLS=
REPAIR_COUNT=
TOKEN_USAGE=

SIMPLE_MEAN_TOOL_CALLS=
SIMPLE_OVERRESEARCH=
EP_OVERRESEARCH=

FULL_REWRITE_PARITY=
ACCEPTED_REPAIR_NEW_FATAL_ISSUES=

QUALITY_NON_REGRESSION=
HONESTY_FATAL=

TOOL_COUNT=32
KNOWN_BROKEN_TOOL_COUNT=
UNUSED_TOOL_COUNT=

BACKEND_TESTS=
FRONTEND_TESTS=
FRONTEND_BUILD=

CORPUS_CONTENT_CHANGED=false
O9_UI_REGRESSION=false

PHIAGENT_CORE_FROZEN=true/false
O10_FINAL_STATUS=PASS/NOT_READY
READY_FOR_O10_REVIEW=true

STOP_FOR_REVIEW

所以当前主线状态正式变成：

O8 Audit                 PASS
O9 UI/UX Design          PASS
O10 Core Repair          ACTIVE
O11 Adaptive Reader      PENDING
O12 Persistence          PENDING
O13 Integration/Polish   PENDING
O14 Production Gate      PENDING

这次 O10 是真正的核心收口：把 O8 找出来的问题全部修掉，再冻结 Core。