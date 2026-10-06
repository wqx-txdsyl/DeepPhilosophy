我把最终 Gate 又按代码路径审了一遍。这轮仍差一个很小的 reviewer patch，暂时不能签 O7-C FINAL PASS。

不是 retrieval、access、PDF body、relevance 或 F6 的问题——这些主体我接受。现在只剩 1 个真正的 transport blocker + 1 个 closeout 纪律问题。

正式裁定：

O7_C_FINAL_GATE_PATCH_REVIEW = PATCH_REQUIRED

SCHOLARLY_RETRIEVAL_CAPABILITY = ACCEPTED
ACCESS_STATE_MACHINE = ACCEPTED
VERIFIED_PDF_READ_SEMANTICS = ACCEPTED
FULLTEXT_ATTEMPT_ACCOUNTING = ACCEPTED
SOURCE_ROLE_HONESTY = ACCEPTED
RELEVANCE_GATE = ACCEPTED
LITERATURE_ACCESS_HONESTY = ACCEPTED

EXPLICIT_PROXY_TRUST_BOUNDARY = NOT_YET_ACCEPTED
FINAL_GATE_SHA_DOCUMENTATION = NOT_ACCEPTED

O7_C_FINAL_GATE_PATCH_2_AUTHORIZED = true
O7_D_AUTHORIZED = false
Blocker：AUTO/DIRECT_PINNED 实际仍可能使用系统代理

你已经删掉了：

Python
Run
if urllib.request.getproxies():
    trust proxy

这个显式分支，这个方向是对的。

但当前 direct 分支：

Python
Run
hh = _PinnedHTTPHandler()
hs = _PinnedHTTPSHandler()
opener = urllib.request.build_opener(hs, hh, rh)

本身并没有禁用 urllib 的默认 ProxyHandler。build_opener() 会自动补充没有被显式替代的默认 handlers；你传了 HTTP/HTTPS/Redirect handler，却没有传 ProxyHandler({})。所以环境里如果存在 HTTP_PROXY/HTTPS_PROXY，direct/AUTO 路径仍可能被默认 ProxyHandler 接管。

也就是说现在这句：

AUTO 检测到系统代理也不静默信任——按 DIRECT_PINNED 安全直连

还没有在 transport 层真正成立。

而 T28 目前只做了源码字符串检查：

Python
Run
assert "getproxies()" not in ...

它证明的是“代码没主动调用 getproxies()”，不是 urllib 没有自动装载环境代理。

因此：

UNTRUSTED_PROXY_AUTO_DELEGATION=0

现在还不能签。

这其实很好修。

O7-C Final Gate Patch 2
Explicit Proxy Disable + Closeout SHA
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 42d88fc19
SCOPE = TRANSPORT MICRO-PATCH + DOC CLOSEOUT ONLY
1. Direct mode 显式禁代理

AUTO / DIRECT_PINNED opener 必须显式带：

Python
Run
urllib.request.ProxyHandler({})

类似：

Python
Run
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    hs,
    hh,
    rh,
)

要求：

AUTO + HTTP_PROXY present
→ proxy NOT used

DIRECT_PINNED + HTTPS_PROXY present
→ proxy NOT used

只有：

SCHOLARLY_NETWORK_MODE=TRUSTED_PROXY

才允许使用系统 proxy configuration。

2. 真行为测试，不要再源码字符串测试

替换/加强 T28。

至少：

P1 AUTO + HTTP_PROXY set
   → opener proxy map empty / direct pinned transport used

P2 DIRECT_PINNED + HTTPS_PROXY set
   → proxy not used

P3 TRUSTED_PROXY + proxy set
   → proxy delegation enabled

P4 AUTO + env proxy + target resolves private
   → still URL_BLOCKED, never delegated

P5 AUTO + env proxy + public target
   → actual direct pinned address is target validated IP

最好把 opener 构造提成一个很薄的：

Python
Run
_build_network_opener(...)

方便直接检查，而不是 monkeypatch 一大片 urllib。

这只是 mechanical transport helper，不是新架构。

3. 保持现有逐跳 repin

这部分已经成立：

redirect host-A
→ handler receives host-B request
→ _pinned_addr_for(host-B)

代码现在确实是在 do_open() 时按当前 request URL 重新 pin。

不要重做。

4. PDF READ 不要再碰

这一块我接受。

当前 READ 已经要求：

body[:4] == %PDF
DIRECT_PDF
parsed text >= 200

并写入：

verified_document_kind=PDF
body_signature_verified=true
parser=pdftotext
content_hash

Gate 也已经不是只看 candidate_kind，而是逐项核验 signature/parser/hash/parsed length。

所以禁止顺手“优化 PDF parser”。

5. 第二个问题：最终 report 仍有 Gate SHA 占位符

当前远端报告实际还是：

O7C_FINAL_CAPABILITY_GATE_SHA= 本节 gate 产物 commit

并不是回执声称的真实 42d88fc19。

而且这是一个结构性问题：

HEAD_SHA = GATE_SHA

时，commit 不可能在自身内容里预先写入自己的 SHA。

正确流程应该是：

code freeze
→ live gate
→ GATE_SHA = G
→ docs-only closeout commit H 写入 G
→ HEAD_SHA = H

所以这次明确分开：

CODE_SHA
O7C_FINAL_CAPABILITY_GATE_SHA
CLOSEOUT_SHA
HEAD_SHA
REMOTE_SHA

最终：

HEAD_SHA = CLOSEOUT_SHA
HEAD_SHA != O7C_FINAL_CAPABILITY_GATE_SHA

这是正常的，不要再追求 gate commit 自引用。

6. Gate 流程

因为 transport production code 会改：

42d88fc19
→ proxy-disable code
→ tests
→ freeze CODE_SHA
→ complete live gate rerun
→ freeze O7C_FINAL_CAPABILITY_GATE_SHA

完整重跑：

16 live queries
bibliographic audit
67 DOI audit
fulltext access
relevance
F6 k3

之后不得再改生产/evaluator。

最后仅：

report + receipt/provenance

docs-only commit：

CLOSEOUT_SHA
7. Hard gates

沿用全部已经通过的门，额外加入：

UNTRUSTED_PROXY_AUTO_DELEGATION = 0
DIRECT_MODE_ENV_PROXY_USAGE = 0
TRUSTED_PROXY_EXPLICIT_ONLY = true

DIRECT_REDIRECT_TARGET_REPIN = true
DIRECT_198_18_BLOCKED = true

VERIFIED_PDF_READ_COUNT >= 1
FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY = 0

FETCH_ATTEMPT_ACCOUNTING_DELTA = 0
ACCESS_STATE_ACCOUNTING_DELTA = 0

SUBSTANTIVE_RELEVANT_QUERY_RATE >= 90%
TOP5_RELEVANCE_MEAN >= 3.0
NEGATIVE_CONTROL_PASS = true

LITERATURE_ACCESS_OVERCLAIM_RECALL = 100%
FALSE_ACCESS_OVERCLAIM = 0

FULL_TEST_FAILED = 0
8. 不再新增 O7-C patch

这次我锁死：

NO_MORE_O7C_DESIGN_PATCHES = true

如果这个 micro-patch 后所有 hard gates 通过：

O7_C_FINAL_REVIEW = PASS
O7_D_AUTHORIZED = true

我不会再因为非 blocker 级 polish 拦 O7-C。

Final receipt
O7_C_FINAL_GATE_PATCH_2 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7C_FINAL_CAPABILITY_GATE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

NETWORK_MODE_DEFAULT=
DIRECT_PROXY_HANDLER=
DIRECT_MODE_ENV_PROXY_USAGE=
UNTRUSTED_PROXY_AUTO_DELEGATION=
TRUSTED_PROXY_EXPLICIT_ONLY=

AUTO_WITH_HTTP_PROXY_TEST=
DIRECT_WITH_HTTPS_PROXY_TEST=
TRUSTED_PROXY_DELEGATION_TEST=

DIRECT_198_18_BLOCKED=
DIRECT_REDIRECT_TARGET_REPIN=
REDIRECT_LIMIT_ENFORCED=

ACCESS_LEVEL_DOWNGRADES=

FULLTEXT_FETCH_ATTEMPTS=
FULLTEXT_FETCH_SUCCESS=
FULLTEXT_HTTP_FAILURES=
FULLTEXT_BLOCKED_ATTEMPTS=
FULLTEXT_AVAILABLE_ONLY_SUCCESS=
DIRECT_PDF_PARSE_FAILURES=

FULL_TEXT_READ_COUNT=
VERIFIED_PDF_READ_COUNT=
FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=

FETCH_ATTEMPT_ACCOUNTING_DELTA=
ACCESS_STATE_ACCOUNTING_DELTA=

SUBSTANTIVE_RELEVANT_QUERY_RATE=
TOP5_RELEVANCE_MEAN=
NEGATIVE_CONTROL_PASS=

FABRICATED_BIBLIOGRAPHIC_FIELDS=
INVALID_VERIFIED_DOI=

LITERATURE_ACCESS_OVERCLAIM_RECALL=
FALSE_ACCESS_OVERCLAIM=

REPORT_GATE_SHA_FIELD=
REPORT_GATE_SHA_MATCHES=true

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

O7_D_AUTHORIZED=false

PROPOSED_VERDICT=PASS

STOP

所以现在真的只剩最后一个洞：

“我没有显式调用系统代理”不等于“urllib 没有自动使用系统代理”。

把 ProxyHandler({}) 这条信任边界真正钉死，再用 docs-only successor 正确记录 Gate SHA，这一阶段就可以结束。