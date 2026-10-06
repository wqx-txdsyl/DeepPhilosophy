我审完远端后，O7-C 这轮不能直接签 PASS，需要一个窄 RP1。不是 scholarly retrieval 架构方向错了；相反，Crossref/OpenAlex 双源、DOI 去重、provider conflict、PAPER_EXISTS != PAPER_READ、两个 Main-Agent tools 和没有重新长出 Shadow Agent，这些方向都成立。问题集中在 access-level 真值、SSRF 重定向边界、source role 诚实性，以及 live gate 自己的 false-green。

正式裁定：

O7_C_REVIEW = PATCH_REQUIRED

SCHOLARLY_RETRIEVAL_ARCHITECTURE = ACCEPTED
TWO_PROVIDER_FOUNDATION = ACCEPTED
BIBLIOGRAPHIC_IDENTITY_MODEL = ACCEPTED
DOI_DEDUP = ACCEPTED
PROVIDER_CONFLICT_MODEL = ACCEPTED
MAIN_AGENT_TOOL_AUTHORITY = ACCEPTED
NO_SHADOW_SCHOLARLY_AGENT = ACCEPTED
MECHANICAL_F5/F6_EVALUATION_DIRECTION = ACCEPTED

ACCESS_STATE_MACHINE = PATCH_REQUIRED
NETWORK_SECURITY_BOUNDARY = PATCH_REQUIRED
SOURCE_ROLE_HONESTY = PATCH_REQUIRED
LIVE_GATE_TRUTHFULNESS = PATCH_REQUIRED

O7_C_RP1_AUTHORIZED = true
O7_D_AUTHORIZED = false
Blocker 1：FULL_TEXT_AVAILABLE 现在并不代表“真的可用”

当前 _mk_canonical() 只要 OpenAlex provider record 给了一个 oa_pdf_url，就直接把状态升为 FULL_TEXT_AVAILABLE；它没有验证 URL 真能访问。更关键的是，它只在已有 abstract 时升级，所以“有合法可达全文但没有 abstract”的记录反而不会成为 AVAILABLE。

然后 C10 明确把一个 404/broken URL 在 fetch 失败后仍保留为：

FULL_TEXT_AVAILABLE

而你原任务 A6 的定义恰恰是：

broken OA URL
→ NOT FULL_TEXT_AVAILABLE

当前测试实际锁死了相反的语义。

更隐蔽的一处：如果记录已经是 FULL_TEXT_AVAILABLE 或 FULL_TEXT_READ，此时调用：

requested_access = ABSTRACT

get_evidence() 会在返回的 access_level_after 中写成 ABSTRACT_AVAILABLE。record 本身没降级，但 ToolMessage 对 Main Agent 声称 after 变低了。

所以目前这条还没真正成立：

access state is monotonic and evidence-driven.

Blocker 2：SSRF 只保护了初始 URL，没有保护 redirect target

_http_get() 在调用 urlopen() 前只执行一次 _url_guard(url)。而 urllib.request.urlopen() 默认会自动跟随 HTTP redirect。当前没有对重定向目标重新执行 _url_guard()。

这意味着理论路径：

provider OA URL
https://public.example/foo

302 →
http://169.254.169.254/...

初始域名通过检查后，redirect target 可以绕过你自己的 SSRF guard。

而且代码定义了：

MAX_REDIRECTS = 4
READ_TIMEOUT = 20

但当前 _http_get() 实际没有实现自己的 redirect counter；READ_TIMEOUT 也没有作为独立 read timeout 使用。

现有 7/7 SSRF tests 只测了直接传入 localhost/RFC1918/link-local/file/ftp，没有覆盖 redirect SSRF。

这是安全 blocker，必须修。

Blocker 3：philosophical_role=UNKNOWN，但模型看到的却是 SCHOLARLY_SECONDARY

数据层做的是对的：

philosophical_role = UNKNOWN
peer_review_status = UNVERIFIED

但是 model_view() 又写了：

Python
Run
source_category =
    "SCHOLARLY_SECONDARY"
    if publication_type == "JOURNAL_ARTICLE"
    else "UNKNOWN"

也就是说，只要 provider 说它是 journal article，Main Agent 就会看到：

SCHOLARLY_SECONDARY

这正好违反 O7-C §25：

journal article
≠
automatically scholarly secondary

例如一个哲学家本人发表的论文完全可能是 primary。

所以 receipt 里的：

PHILOSOPHICAL_ROLE_OVERCLASSIFICATION=0

我不能接受。

C16 只检查了内部 philosophical_role == UNKNOWN，却没有检查 model_view()["source_category"]，因此这里也是一个 test blind spot。

Blocker 4：Live Gate 有至少一个明确 false-green

phase_d() 里面：

Python
Run
"A6_broken_url_not_available": True

是直接硬编码的。

注释说：

# C10 单测锁死

但 C10 实际锁死的是：

broken URL
→ still FULL_TEXT_AVAILABLE

不是 A6 要求的行为。

所以：

A1-A8 全真

当前不能作为可信 Gate 证据。

另外 relevance gate 这里：

Python
Run
q_relevant = sum(
    ... if q.startswith("N")
    or max(score) >= 3
)

把 negative-control 查询自动算进：

QUERIES_WITH_RELEVANT_RECORD

于是 N1/N2 即使没有 relevant record，仍然给分子 +2。

它们本来应该是两个不同指标：

SUBSTANTIVE_QUERIES_WITH_RELEVANT_RECORD
NEGATIVE_QUERY_FALSE_POSITIVE_CONTROL

不能合成一个“16/16 relevant”。

好消息是你报告同时写了 substantive 14/14，因此这不会改变当前能力结论，只是 metric 命名和计算不诚实。

最后还有一个文档 provenance 问题：远端当前 report 仍写着旧 rebase 前 SHA：

CODE_SHA = 7ee6d2b62
O7C_CAPABILITY_GATE_SHA = d83e1ae11

而本轮 receipt 是：

68ed56d07
9a5735fa6

所以“冻结基线引用已同步更新”并没有在最终 report 中完全落实。

TASK — O7-C RP1
Access Truth, Redirect Security & Gate Integrity Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
43978eb49

PHASE =
O7-C RP1 — ACCESS TRUTH & SECURITY CLOSURE

SCOPE =
NARROW CAPABILITY REPAIR
0. 不重做 O7-C

保留：

Crossref
OpenAlex
source schema
DOI identity
provider conflicts
2-tool surface
Main-Agent authority
cache
bibliographic normalization
O7-B metadata
O7-A evaluator

禁止：

- 改 Main Agent scholarly prompt
- 添加 semantic scholarly router
- 添加 sufficiency gate
- 添加 auto scholarly search
- 接 SEP / PhilPapers
- 扩 corpus
- 改 retrieval relevance ranking
- 开 O7-D

RP1 只修：

A. access state truth
B. redirect/network safety
C. source-role honesty
D. live-gate truthfulness
E. report SHA/provenance
1. 引入 FULL_TEXT_CANDIDATE 概念，但不要增加第五 access level

四态仍保持：

METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ

provider 只给了：

oa_pdf_url

时：

不得立即升级 FULL_TEXT_AVAILABLE。

保存为机械候选，例如：

full_text_candidates = [
  {
    url,
    provider,
    access_claim = OPEN_ACCESS
  }
]

但当前 access level 仍由真正已取得的证据决定。

也就是说：

provider says OA
!=
URL verified reachable
2. FULL_TEXT_AVAILABLE 的新定义

只有实际 network attempt 已证明：

URL passed SSRF guard
+
redirect chain passed guard
+
final response successful
+
body actually retrievable

才能：

FULL_TEXT_AVAILABLE

如果同时成功解析正文：

直接：

FULL_TEXT_READ

如果：

HTTP 2xx
body obtained
but parser cannot produce meaningful text

则：

FULL_TEXT_AVAILABLE

是合理的——我们已经证明内容确实可取得，只是当前 parser 没读懂。

3. Broken URL 必须降回真实状态

例如记录已有 abstract：

ABSTRACT_AVAILABLE
+
provider OA candidate
+
fetch = 404

最终：

ABSTRACT_AVAILABLE

不是：

FULL_TEXT_AVAILABLE

只有 metadata：

METADATA_ONLY

则保持 metadata。

必须锁死：

BROKEN_OA_URL_FULL_TEXT_AVAILABLE = false
4. OA URL 不依赖 Abstract

修掉当前：

Python
Run
if oa_url and access == ABSTRACT_AVAILABLE:

这种绑定。

合法全文候选：

有 abstract / 无 abstract

都可以被 get_scholarly_source(...FULL_TEXT...) 尝试。

例如：

METADATA_ONLY
+ valid OA candidate
+ successful parse
→ FULL_TEXT_READ

无需先有 abstract。

5. Access State Must Be Monotonic

定义：

METADATA_ONLY < ABSTRACT_AVAILABLE < FULL_TEXT_AVAILABLE < FULL_TEXT_READ

任何一次 tool call：

access_level_after >= access_level_before

特别增加：

before = FULL_TEXT_AVAILABLE
requested = ABSTRACT
→ after = FULL_TEXT_AVAILABLE

before = FULL_TEXT_READ
requested = ABSTRACT
→ after = FULL_TEXT_READ

可以返回 abstract 内容，但不能在状态字段中谎报降级。

指标：

ACCESS_LEVEL_DOWNGRADES = 0
6. get_scholarly_source 必须区分内容请求与状态

例如：

current_access_level = FULL_TEXT_READ
returned_evidence_type = ABSTRACT

允许。

不要用：

access_level_after = ABSTRACT_AVAILABLE

表达“这次返回了摘要”。

必要时新增：

returned_evidence_level

这是 mechanical field，不是 cognition。

7. Redirect SSRF Hardening

禁止直接让 urllib 自动跟随未经检查的 redirect。

每个 redirect target 都必须：

parse
→ scheme check
→ DNS resolve
→ private/link-local/loopback/reserved check
→ then follow

并真正实现：

MAX_REDIRECTS = 4

第 5 次：

REDIRECT_LIMIT
8. Redirect Kill Cases

至少：

R1 public → public
    allowed

R2 public → localhost
    blocked

R3 public → 127.0.0.1
    blocked

R4 public → 10.0.0.1
    blocked

R5 public → 169.254.169.254
    blocked

R6 https → file://
    blocked

R7 redirect chain >4
    blocked

无需真的攻击网络，可用 mock redirect handler/server。

9. Real Timeout Semantics

当前报告写：

connect 8s / read 20s

RP1 必须二选一：

Option A — 实现真实分离 timeout
CONNECT_TIMEOUT=8
READ_TIMEOUT=20

并有测试。

Option B — 如果当前 HTTP stack 无法可靠分离

则改成一个真实的：

NETWORK_TIMEOUT=<actual>

并修改报告，不得继续声称不存在的 read=20 行为。

优先 A。

不要为了这一项引入大型新 networking framework。

10. Source Role Honesty

model_view() 改成：

source_category =
rec.philosophical_role

或者：

UNKNOWN

直到真实 evidence 支持分类。

禁止：

publication_type=JOURNAL_ARTICLE
→ SCHOLARLY_SECONDARY

新增：

PRIMARY journal article fixture
→ source_category must NOT become SCHOLARLY_SECONDARY automatically
11. Tool Description 也不要过分类

当前 tool 描述偏向：

“二手学术文献”

而 provider search 本身也可能返回 primary scholarly publication。

改为类似：

“学术文献记录（可能是 scholarly secondary、reference、
primary publication 或尚未分类）”

不要添加认知判断。

12. Peer Review 继续保持

保持：

peer_review_status = UNVERIFIED

除非 provider evidence 明确证明。

不得在 RP1 顺便扩展 peer-review classifier。

13. Live Gate A1–A8 全部变成执行式测试

删除这种：

Python
Run
"A6_broken_url_not_available": True

所有 A1–A8 必须由实际 fixture/function result 算出来。

尤其：

A5 DOI landing != FULL_TEXT_AVAILABLE
A6 broken OA != FULL_TEXT_AVAILABLE
A8 candidate/fulltext not fetched != READ

禁止 hardcoded pass。

14. 新增 Access State Accounting Invariant

每次 live gate：

METADATA_ONLY
+ ABSTRACT_AVAILABLE
+ FULL_TEXT_AVAILABLE
+ FULL_TEXT_READ
=
UNIQUE_CANONICAL_RECORDS

要求：

ACCESS_STATE_ACCOUNTING_DELTA = 0

这会防止本轮 report 中：

22 + 43 + 11 + 2

与 unique canonical 数量之间出现无法解释的口径漂移。

15. Relevance Metric 修正

正式拆成：

SUBSTANTIVE_QUERY_COUNT=14

SUBSTANTIVE_QUERIES_WITH_RELEVANT_RECORD=
SUBSTANTIVE_RELEVANT_QUERY_RATE=

NEGATIVE_QUERY_COUNT=2
NEGATIVE_QUERIES_WITH_FALSE_POSITIVE=
NEGATIVE_CONTROL_PASS=

硬门：

SUBSTANTIVE_RELEVANT_QUERY_RATE >= 90%
TOP5_RELEVANCE_MEAN >= 3.0
NEGATIVE_CONTROL_PASS = true

不得再把 negative query 自动算成“有 relevant record”。

16. Fulltext Attempt Accounting

Gate 记录：

FULLTEXT_CANDIDATES=
FULLTEXT_FETCH_ATTEMPTS=
FULLTEXT_FETCH_SUCCESS=
FULLTEXT_PARSE_SUCCESS=
FULLTEXT_HTTP_FAILURES=
FULLTEXT_PARSE_FAILURES=

报告只能使用实际记录的数据。

不要再出现：

“尝试 14+ 篇”

除非 artifact 真的记录了至少 14 次 attempt。

17. Live Gate Freeze

生产修复后：

CODE_SHA=

再冻结：

O7C_RP1_CAPABILITY_GATE_SHA=

从 freeze 开始，以下零改动：

scholarly_sources.py
agent_tools_scholarly.py
tool schema
live gate
fixtures
judge prompt
provider config

然后完整重跑：

16 live queries
bibliographic audit
DOI verification
access audit
relevance judge
F6 access honesty gate

不能只重跑 A6。

18. F6 Gate 不降标准

继续：

LITERATURE_ACCESS_OVERCLAIM_RECALL = 100%
FALSE_ACCESS_OVERCLAIM = 0

本轮 production access state 改了，所以 F6 必须完整复跑。

19. SSRF Gate

至少：

DIRECT_SSRF_BLOCK = 7/7
REDIRECT_SSRF_BLOCK = all pass
REDIRECT_LIMIT_ENFORCED = true

另外确保：

get_scholarly_source

仍然不能接任意 URL。

20. Production Architecture

必须继续：

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false
21. Test Additions

至少：

R1 OA candidate does not automatically mean AVAILABLE

R2 broken OA stays ABSTRACT/METADATA

R3 successful body + parse → READ

R4 successful body + parse failure → AVAILABLE

R5 OA without abstract can still be fetched/read

R6 ABSTRACT request cannot downgrade AVAILABLE

R7 ABSTRACT request cannot downgrade READ

R8 source_category journal article defaults UNKNOWN

R9 primary-author journal fixture not secondary automatically

R10 redirect public→private blocked

R11 redirect public→link-local blocked

R12 redirect to file scheme blocked

R13 >4 redirects blocked

R14 A6 live-gate result is computed, not constant

R15 access-state counts sum to unique records

R16 substantive relevance denominator excludes negatives

R17 negative controls separately measured

R18 production prompt/validator frozen
22. Stale SHA Documentation Fix

当前远端 report 仍保存 rebase 前：

CODE_SHA=7ee6d2b62
GATE_SHA=d83e1ae11

RP1 报告必须使用最终真实：

BASE_SHA
CODE_SHA
O7C_RP1_CAPABILITY_GATE_SHA
HEAD_SHA
REMOTE_SHA

并明确记录旧 report SHA 为：

PRE_REBASE_HISTORICAL_SHA

不要把历史删除，但不能再把旧 SHA 当当前 Gate。

23. PASS Gates
BROKEN_OA_AS_AVAILABLE = 0

ACCESS_LEVEL_DOWNGRADES = 0
ACCESS_STATE_ACCOUNTING_DELTA = 0

SOURCE_CATEGORY_OVERCLASSIFICATION = 0

DIRECT_SSRF_BLOCK = 100%
REDIRECT_SSRF_BLOCK = 100%
REDIRECT_LIMIT_ENFORCED = true

FABRICATED_BIBLIOGRAPHIC_FIELDS = 0
INVALID_VERIFIED_DOI = 0

FULL_TEXT_READ_WITHOUT_PARSED_TEXT = 0
ACCESS_LEVEL_OVERCLAIM = 0

LITERATURE_ACCESS_OVERCLAIM_RECALL = 100%
FALSE_ACCESS_OVERCLAIM = 0

SUBSTANTIVE_RELEVANT_QUERY_RATE >= 90%
TOP5_RELEVANCE_MEAN >= 3.0
NEGATIVE_CONTROL_PASS = true

DUPLICATE_RECORDS_IN_TOP5 = 0
SILENT_PROVIDER_CONFLICT_RESOLUTION = 0

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS = 0
SCHOLARLY_SUFFICIENCY_GATES = 0
SCHOLARLY_SEMANTIC_ROUTERS = 0

SYSTEM_PROMPT_CHANGED = false
FINAL_VALIDATOR_CHANGED = false

O7B_RUNTIME_DATA_CHANGED = false

FULL_TEST_FAILED = 0
24. Report

更新：

docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md

新增：

O7-C RP1 — Access Truth & Security Closure

保留首轮 O7-C 数据和发现，不改写历史。

FINAL RECEIPT
O7_C_RP1 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7C_RP1_CAPABILITY_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

PRE_REBASE_HISTORICAL_CODE_SHA=
PRE_REBASE_HISTORICAL_GATE_SHA=

FULL_TEXT_CANDIDATE_MODEL=

BROKEN_OA_AS_AVAILABLE=
OA_WITHOUT_ABSTRACT_FETCHABLE=

ACCESS_LEVEL_DOWNGRADES=
ACCESS_STATE_ACCOUNTING_DELTA=

METADATA_ONLY_COUNT=
ABSTRACT_AVAILABLE_COUNT=
FULL_TEXT_AVAILABLE_COUNT=
FULL_TEXT_READ_COUNT=

FULLTEXT_CANDIDATES=
FULLTEXT_FETCH_ATTEMPTS=
FULLTEXT_FETCH_SUCCESS=
FULLTEXT_PARSE_SUCCESS=
FULLTEXT_HTTP_FAILURES=
FULLTEXT_PARSE_FAILURES=

SOURCE_CATEGORY_OVERCLASSIFICATION=
JOURNAL_ARTICLE_DEFAULT_SOURCE_CATEGORY=

DIRECT_SSRF_BLOCK_TESTS=
REDIRECT_SSRF_BLOCK_TESTS=
REDIRECT_LIMIT_ENFORCED=

CONNECT_TIMEOUT=
READ_TIMEOUT=
TIMEOUT_SEMANTICS_VERIFIED=

LIVE_QUERY_COUNT=
SUBSTANTIVE_QUERY_COUNT=
SUBSTANTIVE_QUERIES_WITH_RELEVANT_RECORD=
SUBSTANTIVE_RELEVANT_QUERY_RATE=
NEGATIVE_QUERY_COUNT=
NEGATIVE_QUERIES_WITH_FALSE_POSITIVE=
NEGATIVE_CONTROL_PASS=
TOP5_RELEVANCE_MEAN=

FABRICATED_BIBLIOGRAPHIC_FIELDS=
INVALID_VERIFIED_DOI=

LITERATURE_ACCESS_OVERCLAIM_RECALL=
FALSE_ACCESS_OVERCLAIM=

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false

O7C_RP1_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md

O7_D_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP

这轮的核心其实只有三句话：

Provider 说“这里可能有 OA 全文”，不等于我们已经证明“全文可用”。

一个公开 URL 经过 302 跳到私网，仍然是 SSRF；安全检查必须覆盖整条 redirect chain。

“journal article”是出版类型，不是认识论角色；它不能自动变成 SCHOLARLY_SECONDARY。

把这三个真值修实，再把 Gate 自己的 hardcoded PASS 清掉，O7-C 才能作为真正可靠的学术检索基础设施交给 O7-D。