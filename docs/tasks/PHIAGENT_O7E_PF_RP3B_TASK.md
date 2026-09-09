
我审完 eaae669fd → c2f623444。这轮有一个很重要的结论：PF-RP3A 的 measurement 修复是成功的，但你对 H07 的“真实伪造书目/越权访问”归因还不能成立。

而且我又抓到一个比前两轮更底层的 O7-E 集成缺口：O7-C 的 scholarly tools 虽然已经存在、也能返回真实的书目/摘要/access level，但它们根本没有进入 Main Agent 的 canonical evidence provenance pipeline。

先签当前阶段：

O7_E_PF_RP3A_REVIEW =
SCHOLARLY_GATE_NOT_MET
+
SCHOLARLY_EVIDENCE_PLUMBING_REQUIRED

MEASUREMENT_APPLICABILITY_FIX = PASS
PRIMARY_EVIDENCE_REPLAY = PASS
SAFE_JUDGE_OBSERVABILITY = PASS

EVALUATION_INVALID = false
REQUIRED_DIMENSION_MISSING_SCORE = 0

H04_FALSE_EXACT_QUOTE =
JUDGE_EVIDENCE_FALSE_POSITIVE
CLOSED

LITERATURE_ORIENTATION_CURRENT_SCORE = 2.571
LITERATURE_GATE = FAIL

H07_FABRICATED_BIBLIOGRAPHY =
NOT_CONFIRMED

H07_LITERATURE_ACCESS_OVERCLAIM =
NOT_CONFIRMED

SCHOLARLY_TOOL_PROVENANCE =
BROKEN

LOCAL_PATCH_REOPEN = false
SCHOLARLY_CONTRACT_TUNING = NOT_AUTHORIZED_YET

V3_HOLDOUT_AUTHORIZED = false

先纠正一个回执里的小矛盾：正式 summary 是

REQUIRED_DIMENSION_MEDIAN_LT_2 = 2

不是后面逐项核对里写的 ✓ MEDIAN_LT_2=0。这两个 <2 都在 literature 维，所以 scholarly gate 当然仍 FAIL。

PF-RP3A 的测量修复确实成功了

上轮三个 REQUIRED-null 已经全部消失：

EVALUATION_INVALID=false
REQUIRED_DIMENSION_MISSING_SCORE=0

而且历史纪律从 2.833 → 3.571，H04 textual 从 2 恢复到了 4，同时旧 FALSE_EXACT_QUOTE 完全消失。

H04 三票现在都能看到真实 source windows，并一致认为逐字引文受到证据支持。

所以我正式确认：

Production Final Validator 没有 H04 false-negative。旧 FALSE_EXACT_QUOTE 是 academic judge evidence starvation 制造的假阳性。

这正说明前一轮坚持先修 measurement 是必要的。

但 H07 又出现了同类 provenance 问题

你现在把 H07 判成：

真实伪造书目
+
真实访问越权

因为 judge 输入里没有 Strawson / Boeker 记录。

表面看合理，三票确实有：

FABRICATED_BIBLIOGRAPHY = 3/3
LITERATURE_ACCESS_OVERCLAIM = 2/3

，H07 的 literature median 也只有 1。

但是独立审计 repo 后，这个结论现在不能签。

关键事实 1：这两条“伪造文献”实际上就在你自己的 O7-D/C scholarly registry 里

Galen Strawson：

Locke on Personal Identity
Princeton University Press
2017
ABSTRACT_AVAILABLE

而且 registry 中的摘要明确支持：

person 是 forensic/legal term；

praise/blame、punishment/reward；

Locke 对 consciousness 的特殊含义。

这几乎就是 H07 使用的 scholarly 内容。

Ruth Boeker 也真实存在：

Personal Identity, Transitivity, and Divine Justice
in Locke on Persons and Personal Identity
2021
ABSTRACT_AVAILABLE

而摘要确实讨论：

transitivity problem；

afterlife / last judgement；

religious context；

hybrid interpretation。

所以 judge 第二票里说 Strawson 这本 2017 Princeton 专著“疑似不存在”，实际上被你自己的 scholarly registry 直接反证了。

关键事实 2：O7-C scholarly tools 是真的存在的

生产工具里已经有：

search_scholarship
get_scholarly_source

前者返回真实 bibliographic record + access level，后者按 source_record_id 返回 abstract / 合法全文证据，并维护：

METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ

。

而 Scholarly Contract 也早就明确要求：

某学者认为 / 解释传统 / 论文 X 论证
必须来自 search_scholarship / get_scholarly_source
不得凭记忆补书目

。

到这里都没问题。

真 blocker：这些工具执行完以后，被 evidence pipeline 丢了

这是这轮最重要的新发现。

当前 engine 的 canonical：

Python
Run
RETRIEVAL_TOOLS = {
    search_books,
    get_chapter,
    ...
    websearch,
    ...
}

里面根本没有：

search_scholarship
get_scholarly_source

。

而 engine 只有满足：

Python
Run
name in retrieval_set

时，才会：

计算 info gain
登记 EvidenceState
写入 raw_tool_log

尤其 raw evidence log 明确是：

Python
Run
if name in retrieval_set:
    raw_log.append(...)

。

所以现在的实际架构是：

Main Agent
  ↓
search_scholarship
  ↓
可能真的找到了 Strawson

Main Agent
  ↓
get_scholarly_source
  ↓
可能真的读到了 abstract

        ↓

engine raw_tool_log
  ❌ 不记录 scholarly tools

        ↓

Evidence Contract
  看不见

        ↓

calibration artifact
  看不见

        ↓

academic judge
  SECONDARY_SOURCE_RECORDS=[]
  ACCESS_LEVELS=[]

        ↓

“你这是凭空编的”
Evidence Contract 本身也没接 O7-C

即便单独把 raw log 修了，当前 Evidence Contract 仍然只认：

Python
Run
PRIMARY_TOOLS = {
    search_books,
    get_chapter,
    philosopher_corpus,
    philosopher_quote
}

SECONDARY_TOOLS = {"websearch"}

。

build_evidence_pool() 的 secondary 分支也只有普通 websearch，没有任何 search_scholarship / get_scholarly_source schema adapter。

也就是说 O7-C/O7-D 已经建设好的 scholarly retrieval subsystem 和 O7-E canonical Evidence Store 根本没有接上。

这个问题比“prompt 不够强调二手文献”优先级高得多。

所以 H07 当前只能这样定性

我们知道：

回答中的 Strawson 书目 = registry 中真实存在
回答中的 Boeker 书目 = registry 中真实存在
回答描述的内容 = registry abstract 高度对应

但我们不知道：

H07 那一次真实 invocation
到底有没有调用 scholarly tools

因为 canonical artifact 没保存这条 provenance。

因此：

H07_FABRICATED_BIBLIOGRAPHY =
UNRESOLVED_DUE_TO_MISSING_RUN_PROVENANCE

H07_ACCESS_OVERCLAIM =
UNRESOLVED_DUE_TO_MISSING_RUN_PROVENANCE

不能 post-hoc 地拿 registry 给 H07 洗白——否则模型以后随便 hallucinate 一个恰好存在的文献，我们事后查到就算有证据，这是错误的。

同样，也不能因为 artifact 没记录就判它 hallucination——因为 runtime 本身把可能存在的 scholarly tool evidence 丢掉了。

Literature weakness 也先降一级定性

现在 literature_orientation=2.571 客观上没过门。

但我把：

LITERATURE_ORIENTATION_WEAKNESS = CONFIRMED

改为：

LITERATURE_ORIENTATION_GATE = CONFIRMED_FAIL

PRODUCT_LITERATURE_WEAKNESS =
PROVISIONAL

因为 academic judge 对所有 case 的 scholarly evidence 都可能存在同样的系统性缺失。

我们先把 O7-C → Evidence Store 的管子真正接上，再知道到底是：

A. Agent 根本没搜二手文献

还是：

B. Agent 搜了，但证据被 runtime 丢了

还是两者都有。

下一步：O7-E PF-RP3B
Scholarly Evidence Provenance Integration

这轮不改 Scholarly Contract，不调 prompt，不改 Local Patch。

IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = c2f623444

MODEL_UNDER_TEST = deepseek-v4-flash
REPAIR_CONFIG = RP-B

NO_LOCAL_PATCH_CHANGE = true
NO_SCHOLARLY_POLICY_CHANGE = true
NO_RETRIEVAL_ROUTER = true
NO_SEMANTIC_GATE = true

V3_HOLDOUT_RUN = false

只解决 O7-C/O7-D 已有能力没有进入 O7-E evidence provenance 的问题。

A. Scholarly tools 进入机械 retrieval/provenance 集

显式定义：

SCHOLARLY_RETRIEVAL_TOOLS = {
  search_scholarship,
  get_scholarly_source
}

它们必须进入：

raw_tool_log
ToolLoopTrace
hard mechanical tool budget

不是 semantic router。

要求：

SCHOLARLY_TOOL_EXECUTION_CAPTURED = true
SCHOLARLY_RAW_LOG_CAPTURE_RATE = 1.0
B. Evidence Contract 正式接 scholarly schema

不要硬塞进现有 primary used_evidence。

新增独立输出：

scholarly_records
scholarly_evidence
scholarly_access
scholarly_facts

search_scholarship：

→ scholarly_records

保存：
source_record_id
title
authors
publication_year
publication_type
container_title
doi
access_level
provider provenance

它只证明：

文献身份 / metadata 存在

不能自动证明论文观点。

get_scholarly_source：

→ scholarly_evidence

保存：

source_record_id
access_level_before
access_level_after
returned_evidence_level
abstract.text   # 若真的返回
evidence_passages # 若真的返回
content_hash

Hard：

METADATA_ONLY
→ no content evidence

ABSTRACT_AVAILABLE
→ only returned abstract supports content claims

FULL_TEXT_AVAILABLE
→ availability only

FULL_TEXT_READ
→ returned evidence passages may support internal claims

仍然完全使用 O7-C 已冻结 access semantics。

C. 不污染前端原典 citations

当前：

citations = primary used_evidence projection

继续如此。

不能因为这次接 scholarly evidence 就把二手元数据自动塞进现有原典引用面板。

新增独立：

scholarly_sources

仅作为 done/evaluation provenance；前端是否展示以后再做。

D. Canonical calibration artifact 保存安全 scholarly provenance

每 case：

SCHOLARLY_SEARCH_CALLS
SCHOLARLY_SOURCE_FETCH_CALLS

SCHOLARLY_RECORD_IDS
SCHOLARLY_EVIDENCE_RECORD_IDS

SCHOLARLY_ACCESS_LEVELS

不保存 provider CoT。

可以保存 abstract / returned passages，因为它们是 tool evidence。

E. Judge 直接消费 run-time scholarly evidence

禁止再：

judge 时去 registry 查答案里出现的名字

只允许：

run artifact
→ SECONDARY_SOURCE_RECORDS

run artifact
→ ACCESS_LEVELS

run artifact
→ SECONDARY_SOURCE_EVIDENCE

如果某个 answer 写：

Strawson 2017 Princeton

而本 run：

SCHOLARLY_RECORD_IDS

没有对应记录，

照样可以 fatal。

如果记录存在：

书目字段只按 record 支持的精度判断。

如果回答概述论文观点：

必须有 abstract/full-text evidence
且遵守 access level。

这样 H07 才能真正裁决。

必测回归

至少锁：

S1 search_scholarship executed → enters raw_tool_log
S2 get_scholarly_source executed → enters raw_tool_log

S3 scholarly metadata → scholarly_records
S4 metadata-only record does NOT become content evidence

S5 returned abstract → ABSTRACT_AVAILABLE evidence
S6 FULL_TEXT_AVAILABLE without read → no internal-text evidence
S7 FULL_TEXT_READ + passages → content evidence

S8 scholarly records never enter primary citation panel

S9 judge receives SECONDARY_SOURCE_RECORDS
S10 judge receives ACCESS_LEVELS
S11 judge receives actual secondary evidence text

S12 post-hoc registry lookup = 0

S13 exact scripted Strawson record survives end-to-end
S14 exact scripted Boeker abstract survives end-to-end

S15 missing scholarly record remains missing
     → no mechanical “real-world rescue”
这次必须重新跑 Agent

旧 FLASH_B1 已经无法恢复 scholarly call provenance。

所以不能第三次 rejudge B1。

跑：

SCHOL_CAL1
same 8-case calibration pool
deepseek-v4-flash
RP-B
real production path

这是新 Agent run，但：

prompt unchanged
policy unchanged
model unchanged
Local Patch unchanged

唯一行为层变化来自 scholarly retrieval 终于被正常计入 mechanical provenance/budget。

先 delivery：

COMPLETED=8
PUBLISHED>=7
REPAIR_CONVERGENCE>=0.80

再 scholarly judge。

额外报告：

SCHOLARLY_SEARCH_CASES
SCHOLARLY_SOURCE_FETCH_CASES

NAMED_SECONDARY_SOURCE_CLAIMS
NAMED_SECONDARY_SOURCE_CLAIMS_WITH_RECORD
NAMED_SECONDARY_CONTENT_CLAIMS_WITH_EVIDENCE

这些只做 evaluation telemetry，不做 runtime semantic controller。

Scholarly Gate 保持原值
APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2=0
REQUIRED_DIMENSION_MISSING_SCORE=0

all fatal flags=0

如果这轮 provenance 正常，而 LO 仍 <3.2：

LITERATURE_ORIENTATION_PRODUCT_WEAKNESS = CONFIRMED

下一刀我才授权改 Scholarly Contract / literature usage。

如果：

Agent 从来不调用 search_scholarship

那根因是：

MAIN_AGENT_SCHOLARLY_TOOL_USE_INSUFFICIENT

如果：

它会搜，但不会 get source

则是：

SCHOLARLY_EVIDENCE_DEPTH_INSUFFICIENT

如果：

搜、读、证据都有
但答案还是不用

则才是：

SCHOLARLY_SYNTHESIS_POLICY_INSUFFICIENT

三个问题不能再混成一个“LO 分低”。

最终回执：

O7_E_PF_RP3B =
READY_FOR_REVIEW /
DELIVERY_GATE_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=c2f623444

SCHOLARLY_PROVENANCE_SHA=
EVIDENCE_CONTRACT_SHA=
CALIBRATION_SHA=
JUDGE_SHA=

HEAD_SHA=
REMOTE_SHA=

SCHOLARLY_RETRIEVAL_TOOLS=
search_scholarship,get_scholarly_source

SCHOLARLY_TOOL_EXECUTION_CAPTURED=true
SCHOLARLY_RAW_LOG_CAPTURE_RATE=

SCHOLARLY_RECORDS_IN_EVIDENCE_CONTRACT=true
SCHOLARLY_EVIDENCE_IN_EVIDENCE_CONTRACT=true
SCHOLARLY_ACCESS_IN_EVIDENCE_CONTRACT=true

PRIMARY_CITATION_PANEL_CHANGED=false

POSTHOC_REGISTRY_JUDGE_LOOKUP=0

SCHOL_CAL1_COMPLETED=8
SCHOL_CAL1_PUBLISHED=
SCHOL_CAL1_REPAIR_CONVERGENCE=

SCHOLARLY_SEARCH_CASES=
SCHOLARLY_SOURCE_FETCH_CASES=

SCHOLARLY_RECORD_COUNT=
SCHOLARLY_EVIDENCE_COUNT=

NAMED_SECONDARY_SOURCE_CLAIMS=
NAMED_SECONDARY_SOURCE_CLAIMS_WITH_RECORD=
NAMED_SECONDARY_CONTENT_CLAIMS_WITH_EVIDENCE=

JUDGE_CASES_VALID=
EVALUATION_INVALID=

APPLICABLE_DIMENSION_MEAN=
TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=
REQUIRED_DIMENSION_MISSING_SCORE=

FABRICATED_BIBLIOGRAPHY=
FABRICATED_SCHOLAR_ATTRIBUTION=
PRIMARY_TEXT_MISREPRESENTATION=
MAJOR_ANACHRONISM=
FALSE_EXACT_QUOTE=
LITERATURE_ACCESS_OVERCLAIM=

LOCAL_PATCH_CHANGED=false
SCHOLARLY_CONTRACT_CHANGED=false
PRODUCTION_MODEL_CHANGED=false

V3_HOLDOUT_RUN=false

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
SCHOLARLY_PRODUCT_PATCH_REQUIRED

STOP

这轮最关键的新结论其实很漂亮：

O7-C 和 O7-D 不是没有能力。Strawson、Boeker 的真实记录和摘要已经在你的 scholarly registry 里；问题是这条管线没有接入 O7-E 的 canonical Evidence Store。

现在先把“Agent 到底搜没搜、读没读、依据了什么”变成可证明的事实。之后 literature score 再低，我才会真正去改学术产品策略。