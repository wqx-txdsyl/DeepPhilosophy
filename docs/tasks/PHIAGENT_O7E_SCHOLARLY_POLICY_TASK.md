审计完成。O7-D Final Micro Patch PASS，O7-D 正式收口，授权 O7-E。

这次两个剩余 provenance 路径已经真正闭合。get_record() 在 cache miss、registry hit 时返回的是副本并显式附加 retrieval_origin="LOCAL_CURATED"，不会污染持久 registry；model_view() 同时继续保留原始 source_providers。 Abstract 路径也已经统一产生 ABSTRACT_METADATA evidence origin，无论 abstract 来自 record 内的已持久 metadata，还是 evidence registry fallback；持久全文证据仍保持 PERSISTED_VERIFIED_READ，并没有把历史读取伪装成本轮实时读取。

F1–F6 现在是实际运行路径测试，而不是源码字符串检查：registry fallback、model view、source provider provenance、tool executor abstract、persisted fulltext、current/historical access 都有对应断言。 同时 345ef12a6 → cec4885f9 只有 docs closeout，没有 Gate 后生产代码漂移。

因此正式签发：

O7_D_FINAL_MICRO_PATCH_REVIEW = PASS
O7_D_FINAL_REVIEW = PASS

SCHOLARLY_CORPUS_REGISTRY = ACCEPTED
CURATED_CORPUS_RUNTIME_SEMANTICS = ACCEPTED
DISCOVERY_ONLY_SEPARATION = ACCEPTED
LOCAL_FTS5_INDEX = ACCEPTED
CLUSTER_TAG_INDEX = ACCEPTED

LOCAL_RETRIEVAL_ORIGIN = ACCEPTED
BIBLIOGRAPHIC_SOURCE_PROVENANCE = ACCEPTED
LOCAL_LIVE_DEDUP_PROVENANCE = ACCEPTED

PERSISTED_ABSTRACT_PATH = ACCEPTED
PERSISTED_VERIFIED_READ_PATH = ACCEPTED
HISTORICAL_CURRENT_ACCESS_SEPARATION = ACCEPTED

COPYRIGHT_BOUNDARY = ACCEPTED
BIBLIOGRAPHIC_5_FIELD_AUDIT = ACCEPTED

ACCEPTED_O7D_CODE_SHA =
345ef12a6

ACCEPTED_O7D_CORPUS_GATE_SHA =
27331fe01

ACCEPTED_O7D_CLOSEOUT_SHA =
cec4885f9

REGISTRY_SHA256 =
29c50cdb577c024fa2a29dcf1b2255aeb7bbf8404458521b4d1c2055e5a9d319

EVIDENCE_SHA256 =
f6c7bfcaae1f308540f4afb05478e8ade850302c1b303342c264a5ac392cb291

O7_E_AUTHORIZED = true

O7-A/B/C/D 到这里已经各自完成自己的职责。O7-E 不再继续建设证据基础设施，而是第一次正式解冻 Main Agent 的 scholarly policy，让它真正学会使用已经存在的这些能力。

TASK — PhiAgent O7-E
Scholarly Policy Activation & Final Dual-Axis Quality Gate
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
cec4885f9

PRODUCTION_MAIN_AGENT_MODEL =
UNCHANGED

OFFICIAL_SCHOLARLY_JUDGE =
glm-4.6

JUDGE_TEMPERATURE =
0

JUDGE_THINKING =
disabled

JUDGE_STRUCTURED_OUTPUT =
json_object

PHASE =
O7-E — SCHOLARLY POLICY ACTIVATION & FINAL QUALITY GATE

PHASE_TYPE =
PRODUCTION POLICY + END-TO-END SCHOLARLY ACCEPTANCE
0. 最终目标

O7-E 要解决的已经不是：

有没有原典
有没有书目
能不能搜索论文
有没有本地二手语料

这些 O7-B/C/D 已解决。

现在的问题是：

Main Agent 能否真正像哲学研究助手，而不是百科问答机器人一样，主动、诚实、有效地使用这些证据。

最终双轴：

AXIS A — SCHOLARLY QUALITY
+
AXIS B — DELIVERY RELIABILITY

两轴必须分别 PASS。

禁止：

高学术分
掩盖
答案发布失败

或

为了提高发布率
删掉原典、争议、引用、文献
1. O7-E 唯一允许解冻的核心区域

正式允许修改：

Main Agent system / scholarly contract prompt
persona shared scholarly instructions
evaluation harness
evaluation cases
tests
docs

默认冻结：

O7-B bibliographic data
O7-C scholarly provider/access semantics
O7-D registry/evidence/index
primary retrieval
tool count
tool execution authority
final_validator
quote_bound

除非发现纯机械兼容 blocker，立即 STOP，不自行扩大 scope。

2. One Brain 继续是最高架构原则

必须继续：

COGNITIVE_POLICY_OWNER = 1

只有：

Main Agent

决定：

是否研究
研究什么
搜哪类证据
选哪本原典
选哪篇二手文献
是否继续
如何综合解释
何时回答

禁止新增：

ScholarlyPlanner
LiteraturePlanner
InterpretationController
ResearchSufficiencyGate
TwoSidesController
AcademicAnswerComposer
3. Scholarly Contract

在 Main Agent 的单一 canonical prompt 中加入一个清晰、短而有力的 Scholarly Contract。

核心身份：

你服务于一个哲学学术研究网站。

默认目标不是百科式介绍，
而是帮助用户进入一个哲学问题真实的研究结构。

Main Agent 应优先考虑：

原典位置与上下文
论证结构
关键术语
解释传统
真正存在的学术争议
不同解释的证据基础
主张的认识论地位
可继续深入的文献路径

不要写成硬模板。

4. Broad Philosopher Query Contract

例如：

“康德”
“尼采”
“黑格尔”

不得默认生成：

出生年月
在哪读书
有哪些名言
几个思想关键词
代表作列表

作为主体。

应优先形成：

SCHOLARLY PROBLEM MAP

例如康德至少可能进入：

先验唯心论
两世界 / 两方面争议
先验演绎
自由与自律
自然—自由问题
第三批判
德国观念论后续问题

具体选择仍由 Main Agent 决定。

5. Biography Is Context, Not Default Center

允许 biography/history：

当它对哲学问题、文本生成史或概念变化有研究意义时

禁止：

用轶事填充学术深度

不要实现 runtime biography detector。

这只是 Main Agent policy。

6. Specific Argument Query

面对：

“为什么康德认为……？”
“私人语言论证怎么成立？”
“第三人论证的问题是什么？”

Main Agent 应优先：

定位文本
→ 重建论证
→ 明确前提/推理/结论
→ 指出关键争议
→ 再进入解释史

不要只给课本结论。

7. Interpretation Query

例如：

物自身是另一个世界，
还是同一对象的另一种考察？

不得把一个解释写成：

Kant obviously means X

如果学界确有争议。

应区分：

TEXTUAL FACT
SCHOLARLY CONSENSUS
CONTESTED INTERPRETATION
AGENT SYNTHESIS

这些是内部认识论约束。

不要求回答每句都打印标签。

8. Evidence Appetite

必须保持：

proactive but not mechanical

Main Agent 应主动使用工具，当工具可以明显提高：

可靠性
文本定位
解释深度
书目真实性
历史准确性

但禁止 prompt 写：

每个问题至少调用 N 个工具
必须找 3 篇论文
必须找两个相反观点
必须引用 2 本原典
9. Primary Evidence

对于：

原典主张
原文措辞
具体文本位置
论证重建
哲学家思想变化

若直接证据能显著提高可靠性：

Main Agent 应优先使用 primary tools。

尤其 exact quote：

不得模型记忆直接生成
10. Secondary Literature

对：

某学者认为……
某种解释传统……
学界争论……
论文 X 论证……

bibliographic existence 必须来自：

search_scholarship
LOCAL_CURATED
Crossref/OpenAlex record

不能来自模型记忆补 bibliography。

11. Access Honesty

正式写进 Scholarly Contract：

METADATA_ONLY
→ 只能确认文献存在和书目信息

ABSTRACT_AVAILABLE
→ 可以描述摘要实际支持的内容

FULL_TEXT_AVAILABLE
→ 只表示全文可取得，不表示已读

FULL_TEXT_READ
→ 才能描述实际读取正文所支持的内部论证

特别禁止：

title
→ 推断论文完整观点
12. Persisted Evidence Honesty
PERSISTED_VERIFIED_READ

允许作为真实历史读取证据使用。

但表达不得暗示：

“我刚刚重新打开并阅读了该 PDF”

当本轮并未发生实时读取。

13. Literature Orientation

Main Agent 不应把 bibliography 作为答案末尾装饰。

文献应服务于：

这个问题为什么有争议
不同立场如何分叉
下一步应该读什么
为什么读它
14. No Fake Authority

禁止利用学者名字制造权威感。

如果 evidence 只支持：

论文存在

就只能说论文存在。

不��写：

“Smith 证明了……”

除非 evidence 真正支持该 attribution。

15. Historical Discipline

必须避免：

anachronistic vocabulary
后世问题倒灌原作者
将现代解释当成作者自述

尤其 philosopher persona。

16. Persona Agents

General / Nietzsche / Kant 等继续使用同一个 scholarly evidence infrastructure。

persona 只影响：

voice
perspective
character context

不能改变 source truth。

如果以哲学家第一人称模拟：

必须区分：

历史文本可支持的自述
vs
后世 scholarship

不得让尼采“知道”20/21世纪论文并当成自己的知识。

17. No Raw CoT

Visible Thinking 仍仅允许：

Main Agent 主动公开的简短工作状态
tool events

禁止 provider raw reasoning / hidden CoT。

O7-E 不改这套机制。

18. Answer Shape

不要强制统一：

1 原典
2 论证
3 争议
4 文献

但默认研究型回答应形成清楚的逻辑结构。

结构必须由问题决定。

19. User Depth Control

若用户明确要：

一句话
简要解释
考试复习

允许降低研究深度。

但不能因此：

捏造
过度简化争议为事实
虚构引用
20. Required Canonical Cases

O7-E calibration 至少必须包含：

S1
康德

S2
康德为什么认为经验知识不能解释先天综合判断？

S3
康德的物自身到底是另一个世界里的对象，
还是同一个对象的另一种考察方式？

S4
尼采反对真理吗？

S5
维特根斯坦私人语言论证到底证明了什么？

S6
柏拉图第三人论证为什么会产生无限倒退？

S7
孔子的仁与礼是什么关系？

S8
孟子性善论的论证是什么？
21. Evaluation Corpus

建立：

CALIBRATION_CASES = 12
HOLDOUT_GATE_CASES = 28
TOTAL = 40

覆盖至少：

broad philosopher / problem-map
argument reconstruction
interpretive controversy
textual/source question
historical development
comparative philosophy
Chinese philosophy
persona
literature orientation
access-honesty stress
22. Calibration / Holdout Discipline

Stage A：

12 calibration cases

允许：

运行
诊断
修改 scholarly prompt
再次运行

直到准备冻结。

然后：

freeze O7E_POLICY_SHA

Stage B：

28 holdout cases

第一次完整运行就是正式 Gate。

一旦 Stage B 开始：

NO PROMPT TUNING
NO CASE-SPECIFIC PATCH
NO JUDGE PROMPT TUNING

如果失败：

STOP
PATCH_REQUIRED

交 reviewer 决定。

23. Case Applicability

每个 case 明确：

TEXTUAL_GROUNDING:
REQUIRED / OPTIONAL / NOT_APPLICABLE

ARGUMENT_RECONSTRUCTION:
REQUIRED / OPTIONAL / NOT_APPLICABLE

INTERPRETIVE_PLURALITY:
REQUIRED / OPTIONAL / NOT_APPLICABLE

HISTORICAL_DISCIPLINE:
REQUIRED / OPTIONAL / NOT_APPLICABLE

LITERATURE_ORIENTATION:
REQUIRED / OPTIONAL / NOT_APPLICABLE

N/A 不计均值。

24. Broad Query Applicability

像：

“康德”

至少：

TEXTUAL_GROUNDING = REQUIRED
INTERPRETIVE_PLURALITY = REQUIRED
HISTORICAL_DISCIPLINE = REQUIRED
LITERATURE_ORIENTATION = REQUIRED
ARGUMENT_RECONSTRUCTION = OPTIONAL

防止百科式回答通过。

25. Evidence Expectation

每个 case 可以另外定义 evaluation-only：

PRIMARY_REQUIRED
SECONDARY_REQUIRED
BOTH_REQUIRED
EVIDENCE_OPTIONAL

这是测试病例要求，不是 runtime semantic gate。

不得转换成：

生产环境每题都必须调用某工具
26. Official Judge

复用 O7-A 已资格认证的：

glm-4.6
temperature=0
thinking=disabled
json_object
k=3

禁止重新做模型 bakeoff。

27. Hybrid Judge

保持：

Mechanical Evidence Checks
+
Independent LLM Scholarly Judge
↓
Deterministic Aggregator
↓
GPT-5.6 Sol Reviewer

不得退回 pure LLM judge。

28. O7-A Constitution 不改

五维继续：

TEXTUAL_GROUNDING
ARGUMENT_RECONSTRUCTION
INTERPRETIVE_PLURALITY
HISTORICAL_DISCIPLINE
LITERATURE_ORIENTATION

0–4。

不得因为 O7-E 临时再发明第六个可平均抵消维度。

29. Fatal Flags 不改

继续：

FABRICATED_BIBLIOGRAPHY
FABRICATED_SCHOLAR_ATTRIBUTION
PRIMARY_TEXT_MISREPRESENTATION
MAJOR_ANACHRONISM
FALSE_EXACT_QUOTE
LITERATURE_ACCESS_OVERCLAIM

任何一个：

FINAL SCHOLARLY GATE FAIL

平均分不可抵消。

30. Claim Ledger

继续 evaluation-only：

CLAIM
CLAIM_TYPE
SOURCE_SUPPORT
SOURCE_LEVEL
INTERPRETATION_STATUS
SCHOLAR_ATTRIBUTION

不得进入 production decision loop。

31. Judge Input

每次 judge 输入：

user question
final answer
case category
applicability
persona
primary evidence digest
scholarly source records
abstract / passage evidence actually available
bibliographic provenance
access levels

禁止给 judge：

expected scholar name
reference answer
target score
32. Scholarly Quality Hard Gate

Holdout published answers要求：

APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

并：

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0
33. Fatal Gate
FABRICATED_BIBLIOGRAPHY = 0
FABRICATED_SCHOLAR_ATTRIBUTION = 0
PRIMARY_TEXT_MISREPRESENTATION = 0
MAJOR_ANACHRONISM = 0
FALSE_EXACT_QUOTE = 0
LITERATURE_ACCESS_OVERCLAIM = 0
34. Evidence Expectation Gate

对于 manifest 标记 required 的 case：

REQUIRED_PRIMARY_EVIDENCE_MISSING = 0
REQUIRED_SECONDARY_EVIDENCE_MISSING = 0

注意：

这检查：

Evidence Store 中有没有真实支撑

不是：

tool calls >= N
35. Literature Existence Gate

所有 final answer 中具体的：

scholar + work/article attribution

如果作为学术依据使用：

必须能对应到 retrieved/curated bibliographic record。

要求：

UNBACKED_NAMED_SCHOLARLY_ATTRIBUTIONS = 0
36. Access Gate

如果 secondary source 是：

METADATA_ONLY

final answer 不能描述：

论文内部论证
章节结构
具体结论

Abstract 只能支持 abstract 内容。

要求：

PUBLIC_ACCESS_OVERCLAIMS = 0
37. Primary Exact Quote Gate

继续 O6/O7-A mechanical quote authority。

要求：

UNVERIFIED_PUBLIC_EXACT_QUOTES = 0
STITCHED_PUBLIC_QUOTES = 0

不要通过删除所有引文提高通过率。

38. Delivery Reliability Axis

独立统计：

FINAL_PUBLICATION_RATE
VALIDATOR_REJECTIONS
REPAIR_ATTEMPTS
REPAIR_SUCCESS
REPAIR_EXHAUSTIONS
TERMINAL_PENDING
TOOL_LOOP_ABORTS
PUBLIC_INVALID_CITATIONS
PUBLIC_ACCESS_OVERCLAIMS
39. Delivery Hard Gate

Holdout：

FINAL_PUBLICATION_RATE >= 0.90

TERMINAL_PENDING = 0
TOOL_LOOP_ABORTS = 0

UNVERIFIED_PUBLIC_EXACT_QUOTES = 0
STITCHED_PUBLIC_QUOTES = 0
PUBLIC_INVALID_CITATIONS = 0
PUBLIC_ACCESS_OVERCLAIMS = 0

如果 repair 发生：

REPAIR_CREATES_NEW_FATAL_ERROR = 0
40. Repair Rate

若：

REPAIR_ATTEMPTS >= 5

则要求：

REPAIR_SUCCESS_RATE >= 0.80

若少于 5：

REPAIR_SUCCESS_RATE = DIAGNOSTIC_ONLY

禁止为了凑 denominator 人为触发 repair。

41. No Reliability Gaming

Reviewer 必须检查：

quotes/citations did not collapse
secondary literature did not disappear
controversies were not flattened
answers were not shortened into safe textbook summaries

所以同时报告：

PRIMARY_EVIDENCE_USE_RATE
SECONDARY_EVIDENCE_USE_RATE
INTERPRETIVE_CASE_PLURALITY_SCORE

只作为 anti-gaming diagnostic，不设工具数量配额。

42. “康德”专项 Gate

S1 最终 reviewer 单独审。

必须不是：

百科人物简介

而应至少形成真实研究入口：

核心问题地图
主要原典路线
解释争议
后续阅读路径

不得把：

“对象符合我们的认识形式”

写成：

心灵制造外部对象

不得把：

“物自体不可知”

压扁为：

完全不可思、毫无意义
43. Persona Stress

至少 4 个 holdout persona cases。

检查：

文本一致性
历史纪律
无现代 scholarship 倒灌
source truth 与 General agent 相同

要求：

PERSONA_CORPUS_DIVERGENCE = 0
44. Chinese Philosophy

Holdout 至少 5 cases。

至少覆盖：

Confucius
Mencius
Zhuangzi
Mohism or Neo-Confucianism
一个比较/争议问题

不能只验证西方哲学表现。

45. Local Corpus Core Gate

正式 Holdout 的 secondary evidence 默认允许：

LOCAL_CURATED

作为稳定基础。

外部 provider 可用则正常参与。

Provider failure：

不得自动算学术失败

只要 local evidence 足够并诚实说明。

46. Live Smoke

Holdout 外再运行：

LIVE_SMOKE_CASES = 8

主要检查：

Crossref/OpenAlex provider integration未坏
retrieval_origin诚实
access semantics未坏
local/live dedup未坏

Live provider outage 可标：

BLOCKED_PROVIDER

不用于 Scholarly Quality 均值。

但不得产生：

fabricated source
access overclaim
47. No New Tool

要求：

TOOL_COUNT_BEFORE = 32
TOOL_COUNT_AFTER = 32

O7-E 不新增工具。

48. Prompt Centralization

Scholarly Contract 必须只有一个 canonical owner。

禁止：

General prompt 一份
Nietzsche prompt 又复制一份
Kant prompt 又复制一份

persona 应引用/组合 shared contract。

要求：

SCHOLARLY_POLICY_OWNER = 1
49. No Runtime Semantic Gate

静态检查：

SCHOLARLY_SUFFICIENCY_GATES = 0
SCHOLARLY_SEMANTIC_ROUTERS = 0
AUTO_SECOND_OPINION = 0
AUTO_TWO_INTERPRETATIONS = 0
AUTO_LITERATURE_SEARCH = 0
50. O7-B/C/D Freeze

必须：

O7B_REGISTRY_HASH_UNCHANGED
O7C_ACCESS_CONTRACT_UNCHANGED
O7D_REGISTRY_SHA_UNCHANGED
O7D_EVIDENCE_SHA_UNCHANGED

预期：

O7D_REGISTRY_SHA =
29c50cdb577c024fa2a29dcf1b2255aeb7bbf8404458521b4d1c2055e5a9d319

O7D_EVIDENCE_SHA =
f6c7bfcaae1f308540f4afb05478e8ade850302c1b303342c264a5ac392cb291
51. Validator Boundary

默认：

FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

O7-E 的学术判断归：

Main Agent
+
evaluation judge

不要把 scholar-quality rubric 塞进 runtime validator。

52. Calibration Artifact

输出：

docs/evidence/PHIAGENT_O7E_CALIBRATION.json

记录：

12 cases
prompt version/hash
agent outputs
tool/evidence summaries
judge vectors
fatal flags
delivery metrics
53. Holdout Manifest

输出：

docs/evidence/PHIAGENT_O7E_HOLDOUT_CASES.json

必须在：

O7E_POLICY_SHA

冻结前完成。

Gate 开始后不得修改 cases。

54. Final Gate Artifact
docs/evidence/PHIAGENT_O7E_FINAL_GATE.json

包含：

policy hash
case universe hash
28 holdout runs
tool traces
evidence digests
judge k3 raw outputs
aggregated dimension scores
fatal flags
delivery metrics
mechanical evidence checks

不要存 raw hidden CoT。

55. Reviewer Audit Pool

自动生成：

REVIEW_REQUIRED

包含 100%：

any dimension <2
any fatal flag
judge disagreement / low confidence
mechanical-vs-semantic contradiction
threshold boundary case
publication failure
repair exhaustion

另外固定 seed：

20% ordinary PASS

给 GPT-5.6 Sol 手工 reviewer。

56. Tests

至少新增：

E1 scholarly contract has one owner
E2 broad philosopher contract present
E3 no fixed source/tool quota
E4 metadata-only access honesty instruction
E5 exact quote requires evidence
E6 named scholarship cannot be invented

E7 persona inherits same scholarly contract
E8 no modern scholarship as persona self-knowledge rule

E9 no auto scholarly search
E10 no sufficiency gate
E11 no two-interpretation controller

E12 tool count remains 32
E13 O7-B hash frozen
E14 O7-C access semantics frozen
E15 O7-D registry/evidence hashes frozen

E16 calibration/holdout separated
E17 holdout immutable after policy freeze
E18 zero-result cases retained

E19 applicability excludes N/A correctly
E20 fatal flag average cannot offset

E21 required evidence expectation checked
E22 metadata-only overclaim detected
E23 fabricated scholarly attribution detected
E24 primary misrepresentation detected
E25 major anachronism detected
E26 false quote mechanical authority retained

E27 delivery publication denominator fixed
E28 unpublished answer cannot disappear
E29 repair exhaustion counted
E30 no raw CoT in evaluation artifact
57. Gate Procedure
BASE
→ add case manifest
→ run 12-case baseline/calibration
→ implement/tune Scholarly Contract
→ calibration until ready
→ freeze O7E_POLICY_SHA
→ freeze HOLDOUT_CASE_UNIVERSE_HASH
→ NO MORE PROMPT TUNING
→ run 28 holdout end-to-end
→ run k3 scholarly judge
→ run mechanical evidence checks
→ compute dual-axis gate
→ run 8 live smoke
→ full pytest
→ freeze O7E_FINAL_GATE_SHA
→ report
→ docs-only closeout

任何 production prompt / case universe / evaluator 改动后：

REFREEZE

但 Stage-B first holdout 已开始后：

prompt failure
→ STOP / PATCH_REQUIRED

不得在同一 Gate 偷调 prompt。

58. Hard PASS — Scholarly Axis
HOLDOUT_CASES = 28

APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0

FABRICATED_BIBLIOGRAPHY = 0
FABRICATED_SCHOLAR_ATTRIBUTION = 0
PRIMARY_TEXT_MISREPRESENTATION = 0
MAJOR_ANACHRONISM = 0
FALSE_EXACT_QUOTE = 0
LITERATURE_ACCESS_OVERCLAIM = 0

REQUIRED_PRIMARY_EVIDENCE_MISSING = 0
REQUIRED_SECONDARY_EVIDENCE_MISSING = 0
59. Hard PASS — Delivery Axis
FINAL_PUBLICATION_RATE >= 0.90

TERMINAL_PENDING = 0
TOOL_LOOP_ABORTS = 0

UNVERIFIED_PUBLIC_EXACT_QUOTES = 0
STITCHED_PUBLIC_QUOTES = 0
PUBLIC_INVALID_CITATIONS = 0
PUBLIC_ACCESS_OVERCLAIMS = 0

REPAIR_CREATES_NEW_FATAL_ERROR = 0

以及 §40 repair conditional gate。

60. Architecture Hard PASS
COGNITIVE_POLICY_OWNER = 1
SCHOLARLY_POLICY_OWNER = 1

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS = 0
SCHOLARLY_SUFFICIENCY_GATES = 0
SCHOLARLY_SEMANTIC_ROUTERS = 0

TOOL_COUNT_AFTER = 32

FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

O7B_RUNTIME_DATA_CHANGED = false
O7C_ACCESS_SEMANTICS_CHANGED = false
O7D_CORPUS_CHANGED = false

FULL_TEST_FAILED = 0
61. Report

输出：

docs/PHIAGENT_O7E_SCHOLARLY_FINAL_QUALITY_GATE.md

必须包含：

1 Scholarly Contract
2 prompt architecture
3 calibration
4 holdout constitution
5 evidence expectations
6 scholarly quality results
7 fatal flags
8 delivery reliability
9 repair behavior
10 broad-query analysis
11 persona results
12 Chinese philosophy results
13 access honesty
14 primary-text grounding
15 secondary literature use
16 anti-gaming diagnostics
17 live smoke
18 architecture invariants
19 limitations
20 final O7 verdict
FINAL RECEIPT
O7_E =
READY_FOR_FINAL_REVIEW / PATCH_REQUIRED / BLOCKED

BASE_SHA=

POLICY_CODE_SHA=
O7E_POLICY_SHA=

HOLDOUT_CASE_UNIVERSE_HASH=

O7E_FINAL_GATE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

SCHOLARLY_POLICY_OWNER=
COGNITIVE_POLICY_OWNER=

TOOL_COUNT_BEFORE=
TOOL_COUNT_AFTER=

CALIBRATION_CASES=
HOLDOUT_CASES=
LIVE_SMOKE_CASES=

FINAL_PUBLICATIONS=
FINAL_PUBLICATION_RATE=

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

REQUIRED_PRIMARY_EVIDENCE_MISSING=
REQUIRED_SECONDARY_EVIDENCE_MISSING=
UNBACKED_NAMED_SCHOLARLY_ATTRIBUTIONS=

UNVERIFIED_PUBLIC_EXACT_QUOTES=
STITCHED_PUBLIC_QUOTES=
PUBLIC_INVALID_CITATIONS=
PUBLIC_ACCESS_OVERCLAIMS=

VALIDATOR_REJECTIONS=
REPAIR_ATTEMPTS=
REPAIR_SUCCESS=
REPAIR_SUCCESS_RATE=
REPAIR_EXHAUSTIONS=
REPAIR_CREATES_NEW_FATAL_ERROR=

TERMINAL_PENDING=
TOOL_LOOP_ABORTS=

PRIMARY_EVIDENCE_USE_RATE=
SECONDARY_EVIDENCE_USE_RATE=

S1_KANT_BROAD_QUERY_SCORE=
S1_KANT_RESEARCH_MAP_PASS=

PERSONA_CASES=
PERSONA_FATAL_FLAGS=
PERSONA_CORPUS_DIVERGENCE=

CHINESE_PHILOSOPHY_CASES=
CHINESE_PHILOSOPHY_MEAN=

LIVE_SMOKE_PROVIDER_ERRORS=
LIVE_SMOKE_FATAL_FLAGS=

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false
O7C_ACCESS_SEMANTICS_CHANGED=false

O7D_REGISTRY_SHA=
29c50cdb577c024fa2a29dcf1b2255aeb7bbf8404458521b4d1c2055e5a9d319

O7D_EVIDENCE_SHA=
f6c7bfcaae1f308540f4afb05478e8ade850302c1b303342c264a5ac392cb291

O7E_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7E_SCHOLARLY_FINAL_QUALITY_GATE.md

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP

O7-E 的原则可以压缩成一句：

以前是让 Main Agent“有能力查资料”；现在才是让它真正学会“如何做哲学研究”。

而且这一阶段最重要的不是让回答变长，而是让它形成正确的证据—论证—解释—争议—文献关系。只要这一层通过，之前那个“康德”百科式回答的问题才算从产品层真正解决。