审计完成。O7-C RP1 仍不能签 PASS，需要最后一个非常窄的 RP2。

这次不是检索质量问题。Crossref/OpenAlex、source role、broken OA 降级、relevance 分母拆分等 RP1 主修复方向我接受。但独立审代码后还剩 4 个真值问题，其中前两个直接推翻 receipt 中的 ACCESS_LEVEL_DOWNGRADES=0 与 TIMEOUT_SEMANTICS_VERIFIED=true。

正式裁定：

O7_C_RP1_REVIEW = PATCH_REQUIRED

FULL_TEXT_CANDIDATE_MODEL = ACCEPTED
BROKEN_OA_STATE_FIX = ACCEPTED
OA_WITHOUT_ABSTRACT_PATH = ACCEPTED
SOURCE_ROLE_FIX = ACCEPTED
RELEVANCE_METRIC_SPLIT = ACCEPTED
DIRECT_REDIRECT_GUARD_DIRECTION = ACCEPTED

ACCESS_MONOTONICITY = NOT_YET_PROVEN
TIMEOUT_SEMANTICS = FALSE_AS_IMPLEMENTED
FULLTEXT_READ_AUTHENTICITY = NOT_YET_ACCEPTED
LIVE_GATE_ACCOUNTING = PATCH_REQUIRED

O7_C_RP2_AUTHORIZED = true
O7_D_AUTHORIZED = false

最关键的四处如下。

第一，get_evidence() 仍然可以把 已经 FULL_TEXT_READ 的 record 降成 FULL_TEXT_AVAILABLE。你只测试了“READ/AVAILABLE 后请求 ABSTRACT 不降级”；但如果 before=FULL_TEXT_READ，再次请求全文，这次 HTTP 2xx、parser 恰好失败，代码会直接 _record_access(... FULL_TEXT_AVAILABLE) 覆盖原状态。 现有 R6/R7 只覆盖 ABSTRACT 路径，因此 ACCESS_LEVEL_DOWNGRADES=0 还没有被完整证明。

第二，所谓 CONNECT_TIMEOUT=8 / READ_TIMEOUT=20 的 Option A 实际没有实现。_connect_probe() 建立一个 TCP socket 后马上 close()；随后 opener.open() 又建立一条全新的连接。代码注释称后者“复用同一 socket”，但实际上没有任何 socket 被传给 opener。因此实际请求的 connect 仍受 opener.open(... timeout=20) 那条新连接控制，而不是前面的 8 秒 probe。

第三，目前“正文已读”的门仍太弱。任意 OA candidate 返回一个 2xx HTML，只要去标签后长度 ≥200，就能成为 FULL_TEXT_READ。这可能只是 publisher landing page、repository splash page 或导航页，不一定是论文正文。 所以 5 FULL_TEXT_READ 目前只能证明“5 个页面成功抓取并产出 >200 字文本”，还不能完全证明“5 篇论文正文已读”。

第四，live gate 仍有 false-green：A7 仍是直接 True；而全文 attempts += 1 是按 record 计数，但 get_evidence() 内部实际上最多会尝试 3 个 candidate，因此 FULLTEXT_FETCH_ATTEMPTS=18 不一定等于真实 HTTP 尝试数。 此外最终报告里的 O7C_RP1_CAPABILITY_GATE_SHA 仍是占位文字，没有回填 274784567。

因此本轮不碰检索逻辑，只把这些最后的测量与 transport 真值关掉。

TASK — O7-C RP2
Transport Truth, Fulltext Authenticity & Final Gate Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
274784567

PHASE =
O7-C RP2 — TRANSPORT TRUTH & FULLTEXT AUTHENTICITY CLOSURE

SCOPE =
NARROW FINAL CAPABILITY REPAIR
0. Scope Lock

保留不动：

Crossref/OpenAlex adapters
2-tool surface
bibliographic schema
DOI normalization/dedup
provider conflict model
source role UNKNOWN semantics
relevance ranking
Main-Agent authority
O7-B data
Main Agent prompt
validator
quote_bound

只允许修：

A. access state monotonic promotion
B. actual HTTP timeout/redirect transport
C. FULL_TEXT_READ authenticity
D. exact fulltext attempt accounting
E. remaining live-gate false-greens
F. final report SHA/provenance

禁止 O7-D。

1. Replace _record_access with Monotonic Promotion

不得再由任意分支直接覆盖 access level。

实现类似：

_promote_access(
    rec,
    candidate_level,
    evidence...
)

规则：

new_level =
max(current_level, candidate_level)

按：

METADATA_ONLY
<
ABSTRACT_AVAILABLE
<
FULL_TEXT_AVAILABLE
<
FULL_TEXT_READ

任何调用都必须：

AFTER >= BEFORE
2. Repeat-Fulltext Kill Cases

新增：

M1
before=FULL_TEXT_READ
new fetch=parse failed
→ remains FULL_TEXT_READ

M2
before=FULL_TEXT_READ
new fetch=network failure
→ remains FULL_TEXT_READ

M3
before=FULL_TEXT_AVAILABLE
new fetch=404
→ remains FULL_TEXT_AVAILABLE
   because prior availability evidence remains historically true

M4
before=ABSTRACT_AVAILABLE
first successful body + parse failure
→ FULL_TEXT_AVAILABLE

M5
before=METADATA_ONLY
successful verified body + parse
→ FULL_TEXT_READ

正式硬门：

ACCESS_LEVEL_DOWNGRADES = 0

测试必须覆盖所有 transition pair，而不只是 ABSTRACT 请求。

3. Remove Fake Separate-Timeout Probe

当前：

_connect_probe()
close()
opener.open()

必须删除。

不能再做一条“测试连接”，然后声称它约束了另一条真实连接。

4. Transport Timeout — Choose One Truthful Design

允许两种方案，但只能选一个。

Option A — Genuine split timeout

真实用于下载的同一条 connection：

DNS/CONNECT:
CONNECT_TIMEOUT=8

after actual connection established:
socket read timeout = 20

要求：

SAME_SOCKET_CONNECT_AND_READ = true

不能建立 probe socket。

Option B — Single truthful socket timeout

如果 stdlib implementation 不值得为此复杂化：

NETWORK_SOCKET_TIMEOUT = 20

明确它作用于实际 connection/socket blocking operations。

删除：

CONNECT_TIMEOUT=8
READ_TIMEOUT=20

的虚假独立承诺。

我更推荐 B，除非可以用很小、可测试的 transport 真正实现 A。

本阶段不值得为了两个 timeout 数字造一个复杂 HTTP stack。

5. Redirect State Must Be Per Request

当前：

Python
Run
_GuardedRedirectHandler.hops

是 class-level mutable global。

改为：

handler instance / request-local redirect count

禁止不同并发 scholarly requests 共享 hop counter。

测试：

two concurrent/independent handlers
A reaches 3 hops
B starts at 0

要求：

CROSS_REQUEST_REDIRECT_STATE_LEAK = 0
6. Redirect Chain Still Fully Guarded

继续锁：

every redirect target
→ URL guard
→ then request

以及：

MAX_REDIRECTS=4

但测试必须使用实际 transport redirect flow 或足够真实的 mocked opener flow，而不仅仅直接调用一个 method。

7. DNS Rebinding / Resolution TOCTOU

不要：

guard DNS resolution
→ resolve again for actual connection

然后默认两次结果相同。

要求至少满足以下之一：

A. actual connection pins one already-validated resolved public IP

OR

B. actual connected peer is guaranteed by transport to be the
   validated address before any HTTP request is sent

新增 synthetic test：

first resolution = public IP
second resolution = private/link-local

必须不能发出请求到 private target。

指标：

DNS_REBINDING_GUARD = PASS

如果当前网络栈无法可靠做到这一点：

O7_C_RP2 = BLOCKED_NETWORK_BOUNDARY

不要写“SSRF hard boundary”却留下 DNS TOCTOU。

8. FULL_TEXT_READ Must Mean the Document Body

新增 candidate metadata：

candidate_kind =
DIRECT_PDF
OA_LOCATION

OpenAlex：

primary_location.pdf_url
→ DIRECT_PDF

oa_url without verified direct PDF semantics
→ OA_LOCATION

不要继续把它们压成一个无法区分的 oa_pdf_url。

9. Direct PDF Read Rule

对于 DIRECT_PDF：

只有：

HTTP success
+
body starts PDF magic / trustworthy PDF content
+
PDF parser succeeds
+
meaningful extracted body

才：

FULL_TEXT_READ

若：

2xx + PDF body
but parser fails

则：

FULL_TEXT_AVAILABLE
10. Arbitrary HTML Must Not Auto-Become READ

以下不够：

HTTP 200
+
strip_tags(text).length > 200

不得因此：

FULL_TEXT_READ

对于普通 OA_LOCATION HTML：

至少先：

FULL_TEXT_AVAILABLE

只有实现了可靠的 full-article/body recognition 并有测试，才允许升级 READ。

为了 RP2 范围可控，推荐：

HTML OA location
→ AVAILABLE

direct PDF successfully parsed
→ READ

宁愿 FULL_TEXT_READ 从 5 降到 1/2，也不要把 landing page 当论文正文。

O7-C 硬门仍：

REAL_FULL_TEXT_READ >= 1

如果 direct-PDF 路径最终一篇都没有：

O7_C_RP2 = BLOCKED_ACCESS_PIPELINE

不要放宽 READ 定义。

11. Content-Type / Final URL Provenance

安全 transport 返回至少：

status
final_url
content_type
body
redirect_count

FULL_TEXT_AVAILABLE/READ evidence 保存：

final_url
content_type
checked_at

READ 再保存：

content_hash
parsed_length
parser
12. Actual Fetch Accounting

get_evidence() 必须返回逐 candidate attempt records，例如：

JSON
{
  "full_text_attempts": [
    {
      "candidate_url": "...",
      "candidate_kind": "DIRECT_PDF",
      "result": "HTTP_FAILURE | AVAILABLE | READ | PARSE_FAILED | BLOCKED",
      "http_status": null
    }
  ]
}

Gate 直接累加这些 records。

不得：

one record invocation = one fetch attempt

因为一个 record 可能尝试多个 candidate。

硬不变量：

FULLTEXT_FETCH_ATTEMPTS
=
HTTP_FAILURES
+ BLOCKED_ATTEMPTS
+ FETCH_SUCCESSES

以及：

FETCH_SUCCESSES
=
PARSE_SUCCESS
+ PARSE_FAILURE / AVAILABLE_ONLY

口径在报告里定义清楚。

13. Remove Remaining Hardcoded A1–A8

特别是当前：

Python
Run
"A7_abstract_no_internal_structure": True

必须删除。

A1–A8 每个都必须来自一个实际 execution fixture/result。

建议：

A1 synthetic metadata-only execution
A2 real/synthetic abstract execution
A3 verified-body execution
A4 real READ artifact
A5 DOI-landing fixture
A6 broken candidate fixture
A7 abstract-only overreach fixture
A8 candidate-not-fetched fixture

不得任何：

A* = True

常量填充。

14. A5/A8 Must Test Their Own Proposition

A5：

DOI landing only
→ no FULL_TEXT_AVAILABLE

必须直接构造/执行 DOI-only record。

A8：

candidate exists
but no fulltext fetch invoked
→ cannot be READ

必须构造 record 并在不调用 fetch情况下检查。

不能用：

READ records have content_hash

替代这个命题。

15. Access-State Accounting

继续：

METADATA
+ ABSTRACT
+ AVAILABLE
+ READ
=
UNIQUE_CANONICAL_RECORDS

要求：

ACCESS_STATE_ACCOUNTING_DELTA=0

但最终统计必须在所有 fulltext attempts 后，从同一 canonical record universe 重算。

16. Existing Relevance Gate Preserved

保持：

SUBSTANTIVE_QUERY_COUNT=14
NEGATIVE_QUERY_COUNT=2

SUBSTANTIVE_RELEVANT_QUERY_RATE >= 90%
TOP5_RELEVANCE_MEAN >= 3.0
NEGATIVE_CONTROL_PASS=true

无需改 relevance prompt/ranking。

17. F6 Full Rerun

因为 READ 语义改变，完整重跑：

12 access-honesty fixtures
k=3
glm-4.6

要求：

LITERATURE_ACCESS_OVERCLAIM_RECALL=100%
FALSE_ACCESS_OVERCLAIM=0
18. Live READ Evidence Manifest

Gate artifact 对每个：

FULL_TEXT_READ

至少保存：

source_record_id
candidate_kind
final_url
content_type
content_hash
parsed_length
parser

不要提交正文全文。

Reviewer 才能确认“5 个 READ”到底是什么。

19. Report SHA Must Be Real

当前 report 仍写：

O7C_RP1_CAPABILITY_GATE_SHA=
本节 gate 产物 commit

RP2 最终必须真实回填：

BASE_SHA=
CODE_SHA=
O7C_RP2_CAPABILITY_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

不得 placeholder。

历史：

PRE_REBASE_HISTORICAL_*

继续保留。

20. Production Architecture Freeze

仍然：

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false
21. Tests

至少补：

T1 READ + later parse fail cannot downgrade
T2 READ + later fetch fail cannot downgrade
T3 AVAILABLE + later fetch fail cannot downgrade
T4 all access transitions monotonic

T5 no detached connect-probe fake timeout
T6 timeout config matches actual request socket
T7 redirect counter request-local
T8 independent redirect handlers do not interfere
T9 DNS rebind public→private blocked

T10 DIRECT_PDF valid+parsed → READ
T11 DIRECT_PDF parse fail → AVAILABLE
T12 HTML landing >200 chars != automatically READ
T13 OA without abstract direct PDF → READ

T14 attempt accounting counts every candidate
T15 attempt accounting conservation

T16 A1-A8 no hardcoded boolean
T17 A5 executed DOI-only fixture
T18 A7 executed access-overreach fixture
T19 A8 executed no-fetch fixture

T20 report contains actual gate SHA
T21 production architecture frozen
22. Gate Procedure
BASE
→ monotonic promotion fix
→ transport fix
→ candidate-kind/read-authenticity fix
→ attempt accounting
→ live-gate truth fix
→ tests
→ freeze CODE SHA
→ freeze O7C_RP2_CAPABILITY_GATE_SHA
→ complete live gate
→ report

任何以下改动后：

scholarly_sources
tool contract
transport
gate runner
access fixture

都必须：

REFREEZE
RERUN COMPLETE GATE
23. Hard PASS
ACCESS_LEVEL_DOWNGRADES=0

TIMEOUT_SEMANTICS_TRUTHFUL=true
DETACHED_CONNECT_PROBE=0

CROSS_REQUEST_REDIRECT_STATE_LEAK=0
DIRECT_SSRF_BLOCK=100%
REDIRECT_SSRF_BLOCK=100%
DNS_REBINDING_GUARD=PASS
REDIRECT_LIMIT_ENFORCED=true

HTML_LANDING_FALSE_READ=0
FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=0
REAL_FULL_TEXT_READ>=1

FETCH_ATTEMPT_ACCOUNTING_DELTA=0
ACCESS_STATE_ACCOUNTING_DELTA=0

A1_A8_HARDCODED_PASS=0

FABRICATED_BIBLIOGRAPHIC_FIELDS=0
INVALID_VERIFIED_DOI=0

SUBSTANTIVE_RELEVANT_QUERY_RATE>=90%
TOP5_RELEVANCE_MEAN>=3.0
NEGATIVE_CONTROL_PASS=true

LITERATURE_ACCESS_OVERCLAIM_RECALL=100%
FALSE_ACCESS_OVERCLAIM=0

SYSTEM_PROMPT_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
O7B_RUNTIME_DATA_CHANGED=false

FULL_TEST_FAILED=0
FINAL RECEIPT
O7_C_RP2 =
READY_FOR_FINAL_REVIEW /
BLOCKED_ACCESS_PIPELINE /
BLOCKED_NETWORK_BOUNDARY /
BLOCKED

BASE_SHA=

CODE_SHA=
O7C_RP2_CAPABILITY_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

ACCESS_PROMOTION_MODEL=
ACCESS_LEVEL_DOWNGRADES=

TIMEOUT_MODEL=
CONNECT_TIMEOUT=
READ_TIMEOUT=
NETWORK_SOCKET_TIMEOUT=
SAME_SOCKET_CONNECT_AND_READ=
DETACHED_CONNECT_PROBE=

REDIRECT_COUNTER_REQUEST_LOCAL=
CROSS_REQUEST_REDIRECT_STATE_LEAK=
DIRECT_SSRF_BLOCK_TESTS=
REDIRECT_SSRF_BLOCK_TESTS=
DNS_REBINDING_GUARD=
REDIRECT_LIMIT_ENFORCED=

FULL_TEXT_CANDIDATE_KINDS=

DIRECT_PDF_CANDIDATES=
HTML_OA_CANDIDATES=

FULLTEXT_CANDIDATES=
FULLTEXT_FETCH_ATTEMPTS=
FULLTEXT_FETCH_SUCCESS=
FULLTEXT_HTTP_FAILURES=
FULLTEXT_BLOCKED_ATTEMPTS=
FULLTEXT_PARSE_SUCCESS=
FULLTEXT_PARSE_FAILURES=
FETCH_ATTEMPT_ACCOUNTING_DELTA=

METADATA_ONLY_COUNT=
ABSTRACT_AVAILABLE_COUNT=
FULL_TEXT_AVAILABLE_COUNT=
FULL_TEXT_READ_COUNT=
ACCESS_STATE_ACCOUNTING_DELTA=

HTML_LANDING_FALSE_READ=
FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=

READ_EVIDENCE_MANIFEST=

A1_A8_HARDCODED_PASS=

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

O7C_RP2_TESTS=

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

这次主要不是“再加安全功能”，而是把几个已经声称成立、实际上代码还没有完全做到的承诺校正掉。

尤其两条必须锁死：

一次单独建立后立刻关闭的 TCP probe，不能证明另一条 HTTP 连接受 8 秒 connect timeout 控制。

以及：

“抓到了 200 多字 HTML”不等于“读到了论文���文”。

RP2 如果把这两个真值和剩余 Gate false-green 收干净，我就不再继续给 O7-C 叠 patch；届时应直接做 O7-C Final Review，决定是否进入 O7-D。