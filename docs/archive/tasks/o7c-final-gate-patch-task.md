我审完这轮远端实现了。O7-C RP2 仍然不能签最终 PASS，但现在只剩一个非常窄的 Final Gate Patch；检索能力本身已经成立。

正式裁定：

O7_C_RP2_REVIEW = PATCH_REQUIRED

SCHOLARLY_RETRIEVAL_CAPABILITY = ACCEPTED
BIBLIOGRAPHIC_PROVENANCE = ACCEPTED
ACCESS_MONOTONICITY = ACCEPTED
SOURCE_ROLE_HONESTY = ACCEPTED
RELEVANCE_GATE = ACCEPTED
F6_ACCESS_HONESTY = ACCEPTED
FULLTEXT_CANDIDATE_SEPARATION = ACCEPTED
ATTEMPT_ACCOUNTING_DIRECTION = ACCEPTED

NETWORK_TRUST_BOUNDARY = PATCH_REQUIRED
DIRECT_PDF_BODY_VERIFICATION = PATCH_REQUIRED
REDIRECT_PINNING_CORRECTNESS = PATCH_REQUIRED
LIVE_GATE_METRIC_TRUTH = PATCH_REQUIRED

O7_C_FINAL_GATE_PATCH_AUTHORIZED = true
O7_D_AUTHORIZED = false

这次我不再要求新的 RP 架构阶段。问题已经收缩到 transport/security 的三个具体代码点。

第一处是 DIRECT_PDF 仍存在“HTML 被误判为 READ”的代码路径。现在代码把下面任一条件都算 is_pdf：

Python
Run
PDF magic
OR Content-Type contains pdf
OR URL endswith .pdf

随后 _extract_text() 却只根据 URL 后缀或 PDF magic 决定走 pdftotext；否则会按 HTML 解标签。如果一个 DIRECT_PDF URL 没有 .pdf 后缀，服务器却返回 Content-Type: application/pdf + 一段 >200 字 HTML，那么 is_pdf=true、HTML 解析成功，最后仍会升级为 FULL_TEXT_READ。也就是说当前 READ 并没有在代码层真正要求“verified PDF document body”。

这也意味着 live gate 的：

FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=0

实际上只检查了 candidate_kind == DIRECT_PDF，没有检查 PDF magic / document-body verification，所以这个 0 仍可能 false-green。

第二处是 DNS rebinding 防线在代理模式下并没有 PASS，而是被委托给代理了。_http_get() 只要 urllib.request.getproxies() 非空，就直接使用默认 opener，完全绕开 _PinnedHTTP/_PinnedHTTPS。代码自己也明确写着“出网边界由代理解决；此分支不做 pinning”。

所以回执中的：

DNS_REBINDING_GUARD=PASS

不能无条件成立。更准确的是：

DIRECT_NETWORK:
DNS_REBINDING_GUARD=PINNED

PROXY_NETWORK:
DNS_RESOLUTION_BOUNDARY=DELEGATED_TO_TRUSTED_PROXY

而当前代码甚至是自动检测任何系统 proxy 就委托，没有“trusted proxy”这个显式信任边界。

还有一个相关安全点：198.18.0.0/15 目前在 _url_guard() 和 _pinned_addr_for() 中被无条件豁免，理由是你当前机器的 VPN fake-IP。 这个豁免不能变成 DeepPhilosophy 在普通直连部署环境里的永久规则。直连机器上，198.18/15 应当仍按 reserved/non-global network 拒绝；只有显式 trusted fake-IP proxy/TUN mode 才能允许。

第三处是 直连模式 redirect 的 pinning 地址没有随目标主机变化。当前 _http_get() 在初始 URL 上算一次：

addr = _pinned_addr_for(initial_url)

再把这个 addr 固定进 HTTP/HTTPS handler。redirect handler 虽然检查新 URL，但后续 redirect request 仍然经过带着初始地址的 pinned handler。

所以：

https://host-A
302 → https://host-B

可能实际仍连接 host-A 的 IP，只是 Host/SNI 已变成 host-B。安全上通常会失败而不是绕过，但功能语义是错的；真正应该是每一跳都 guard + 对该跳自己的 host/IP 做 pin。

最后一个只是 instrumentation：live gate 当前把所有 AVAILABLE 成功都算进 FULLTEXT_PARSE_FAILURES。但 OA_LOCATION HTML 成功获取后本来就按设计只能 AVAILABLE，不一定发生了“parse failure”。 这个名称需要拆开，否则 4+3 的“parse_ok/parse_fail”含义不精确。

所以只做下面这个 Final Gate Patch。

TASK — O7-C Final Gate Patch
Network Trust Boundary & Verified Document Body
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
fd7ca8709

PHASE =
O7-C FINAL GATE PATCH

SCOPE =
TRANSPORT + BODY VERIFICATION + METRIC TRUTH ONLY

只允许修改：

backend/scholarly_sources.py
backend/tests/test_o7c_scholarly_retrieval.py
backend/tools/evaluation/o7c_live_gate.py
docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md
docs/evidence/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL_GATE.json

禁止：

provider ranking
Main Agent prompt
tool count
bibliographic schema
source-role policy
O7-B
validator
quote_bound
O7-D
A. FULL_TEXT_READ 必须要求 verified PDF body

对 DIRECT_PDF：

candidate_kind = DIRECT_PDF
AND HTTP success
AND body starts with %PDF
AND pdftotext succeeds
AND meaningful parsed text >= threshold

→ FULL_TEXT_READ

以下全部不得 READ：

Content-Type=application/pdf + HTML body
URL ends .pdf + HTML body
DIRECT_PDF + arbitrary text body
PDF Content-Type without PDF magic

可以：

body is valid PDF
Content-Type wrong/missing
→ still READ if PDF parser succeeds

也就是说，document body beats header/URL naming。

新增：

VERIFIED_DOCUMENT_KIND = PDF
BODY_SIGNATURE_VERIFIED = true

写进 READ access provenance 和 manifest。

B. 修 FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY

Gate 不再只检查：

candidate_kind == DIRECT_PDF

而检查每个 READ：

candidate_kind == DIRECT_PDF
body_signature_verified == true
parser == pdftotext
content_hash != null
parsed_length >= threshold

要求：

FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=0
C. Proxy trust boundary 必须显式

禁止：

Python
Run
if urllib.request.getproxies():
    automatically trust proxy

改成显式运行模式，例如：

DIRECT_PINNED

TRUSTED_PROXY

环境/config 名自行合理设计。

默认安全策略：

proxy exists
but not explicitly trusted
→ do not silently delegate SSRF boundary

可以选择：

reject scholarly fulltext network operation

或走可安全直连的 pinned mode。

D. Trusted proxy 模式必须说真话

如果用户明确启用：

TRUSTED_PROXY

则：

DNS_REBINDING_MODE =
TRUSTED_PROXY_DELEGATED

不要报告：

DNS_REBINDING_GUARD=PINNED

在 direct 模式才允许：

DNS_REBINDING_MODE =
DIRECT_IP_PINNED

这不是降低安全标准，而是让 trust model 显式。

E. 198.18/15 豁免只能存在于 trusted fake-IP mode

直连默认：

198.18.0.0/15
→ BLOCK

只有：

TRUSTED_PROXY/TUN_FAKE_IP=true

才允许该段。

新增 regression：

direct mode + hostname→198.18.0.1
→ blocked

explicit trusted fake-IP mode
→ allowed
F. Redirect 每一跳重新 pin

直连 handler 不得持有整个请求链固定的：

initial_addr

应对每个实际 request：

request target URL
→ URL guard
→ resolve
→ validate
→ pin this target IP
→ connect

因此：

host-A → host-B

第二跳必须 pin host-B，不是 host-A。

新增：

redirect A(public IP1)
→ B(public IP2)

actual second connect target = IP2
G. Proxy 与 redirect 测试

至少：

N1 direct A→B pins B IP
N2 direct redirect→private blocked
N3 direct 198.18 blocked
N4 trusted fake-IP mode allows 198.18
N5 untrusted detected proxy not silently trusted
N6 trusted proxy reports DELEGATED mode
N7 redirect limit remains 4
H. Metric rename

当前：

FULLTEXT_PARSE_FAILURES

拆成至少：

DIRECT_PDF_PARSE_FAILURES
AVAILABLE_ONLY_SUCCESS

因为：

HTML OA_LOCATION → AVAILABLE

不是 parser failure。

保持守恒：

FETCH_ATTEMPTS
=
HTTP_FAILURES
+ BLOCKED
+ FETCH_SUCCESSES

FETCH_SUCCESSES
=
READ_SUCCESS
+ AVAILABLE_ONLY_SUCCESS

然后单独：

DIRECT_PDF_PARSE_FAILURES

作为 AVAILABLE_ONLY 的子集。

I. Live gate

代码冻结后完整重跑一次：

16 queries
bibliographic audit
DOI audit
fulltext access
relevance
F6 k3

不要求 READ 数仍为 4。

硬门只要求：

REAL_VERIFIED_FULL_TEXT_READ >= 1

如果从 4 降成 1：

完全可以接受。

J. Tests

至少新增：

T22 DIRECT_PDF + content-type PDF + HTML body != READ
T23 DIRECT_PDF URL .pdf + HTML body != READ
T24 PDF magic + parser success = READ
T25 READ provenance has body_signature_verified

T26 direct mode 198.18 blocked
T27 trusted fake-IP mode explicit allow

T28 auto-detected proxy is not automatically trusted
T29 trusted proxy reports delegated DNS boundary

T30 cross-host redirect repins target host
T31 redirect private still blocked

T32 live READ verifier checks body signature
T33 metrics distinguish AVAILABLE_ONLY vs parse failure
Hard PASS
ACCESS_LEVEL_DOWNGRADES=0

FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=0
HTML_OR_MISLABELED_BODY_FALSE_READ=0
REAL_VERIFIED_FULL_TEXT_READ>=1

DIRECT_MODE_RESERVED_FAKE_IP_BYPASS=0
UNTRUSTED_PROXY_AUTO_DELEGATION=0

DIRECT_REDIRECT_TARGET_REPIN=true

DIRECT_SSRF_BLOCK=100%
REDIRECT_SSRF_BLOCK=100%
REDIRECT_LIMIT_ENFORCED=true

FETCH_ATTEMPT_ACCOUNTING_DELTA=0
ACCESS_STATE_ACCOUNTING_DELTA=0

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

最终回执：

O7_C_FINAL_GATE_PATCH =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7C_FINAL_CAPABILITY_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

NETWORK_BOUNDARY_MODE=
PROXY_TRUST_EXPLICIT=
UNTRUSTED_PROXY_AUTO_DELEGATION=

DIRECT_198_18_BLOCKED=
TRUSTED_FAKE_IP_MODE=

DIRECT_REDIRECT_TARGET_REPIN=
DNS_REBINDING_MODE=

ACCESS_LEVEL_DOWNGRADES=

FULLTEXT_FETCH_ATTEMPTS=
FULLTEXT_HTTP_FAILURES=
FULLTEXT_BLOCKED_ATTEMPTS=
FULLTEXT_FETCH_SUCCESS=
FULLTEXT_AVAILABLE_ONLY_SUCCESS=
DIRECT_PDF_PARSE_FAILURES=
FULLTEXT_READ_COUNT=

VERIFIED_PDF_READ_COUNT=
HTML_OR_MISLABELED_BODY_FALSE_READ=
FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=

FETCH_ATTEMPT_ACCOUNTING_DELTA=
ACCESS_STATE_ACCOUNTING_DELTA=

READ_EVIDENCE_MANIFEST=

SUBSTANTIVE_RELEVANT_QUERY_RATE=
TOP5_RELEVANCE_MEAN=
NEGATIVE_CONTROL_PASS=

FABRICATED_BIBLIOGRAPHIC_FIELDS=
INVALID_VERIFIED_DOI=

LITERATURE_ACCESS_OVERCLAIM_RECALL=
FALSE_ACCESS_OVERCLAIM=

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
O7B_RUNTIME_DATA_CHANGED=false

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

有一点我明确认可：RP2 已经把“200 字 HTML = 全文已读”这个大问题基本切掉了，而且 access 单调性、逐候选记账、source role 和 relevance 指标都已经走到正确形态。

现在最后缺的不是“更聪明”，而是让 security boundary 和 FULL_TEXT_READ 这个词在所有代码路径上都百分之百按字面成立。这一小补丁过后，我会直接做 O7_C_FINAL_REVIEW；不再开启新的 O7-C 设计阶段。