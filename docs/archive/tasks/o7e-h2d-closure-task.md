我审完 5c42f8b3f → 78221c5ed。这轮结论不是继续 RUN2，也不是马上调 INVALID_JSON。

我选 (d)：再做一次纯机械 H2D 收口。因为独立审计发现：H2C 虽然把很多合同补齐了，但仍有 4 个会直接污染 RUN1 结论的 false-green / 未闭合点。

O7_E_RP2_RCA1_H2C_REVIEW = PATCH_REQUIRED

RUN1_COMPLETED = 8
RUN1_PUBLISHED = 5/8
RUN1_REPAIR_CONVERGENCE = 0.625
RUN1_HARD_GATE = FAIL

LOCAL_PATCH_ARCHITECTURE = STILL_PROMISING

RUN2_AUTHORIZED = false
INVALID_JSON_PROMPT_TUNING = NOT_AUTHORIZED
MAX_VALIDATION_REPAIRS_CHANGE = NOT_AUTHORIZED

LOCAL_PATCH_ELIGIBILITY_PREFLIGHT = BLOCKER
RUNTIME_IDENTITY_VERIFICATION = BLOCKER
LATEST_EVIDENCE_FINALIZATION_CANONICALITY = BLOCKER
LIVE_ISSUE_TELEMETRY = BLOCKER

PRODUCTION_LOCAL_PATCH_AUTHORIZED = false
V3_STAGE_B_AUTHORIZED = false

当前 5/8 数据本身成立：H04、S4、S7、S9、H07 发布；H02/H03/H13 失败。 汇总的 5/8、0.625、VALIDATOR_EMPTY_FINAL=0 也一致。

但有几处需要纠正。

1. H13 的 FINALIZATION_NO_ANCHOR 其实暴露了 eligibility gate 没做完

现在：

Python
Run
def all_issues_localizable(validation):
    return all(issue.code in LOCAL_PATCH_CODES ...)

它只检查 issue code，没有检查 anchor 是否真的能解析。虽然函数 docstring 写着“ALL issues 必须可局部化且可锚定”，实现没有“可锚定”这一半。

因此可能发生：

所有 code 都在 LOCAL_PATCH_CODES
→ can_handle = true
→ build 后 anchor_ok=false
→ 仍然进入 LOCAL_PATCH invocation

H13 的：

FINALIZATION_NO_ANCHOR

正是这种路径的真实信号。

我们之前冻结的合同其实是：

ALL issue codes local
AND
ALL anchors resolvable
→ LOCAL_PATCH

otherwise
→ 在 repair invocation 开始前 FULL_REWRITE

这个必须修。

2. 最严重的 blocker：latest-evidence finalization 又绕出了 canonical Main-Agent path

H2C 的 finalization 现在直接：

Python
Run
_final_client = get_repair_llm()
...
_fin_resp = await asyncio.to_thread(
    lambda: _final_client.invoke(_fin_msgs)
)

。

这意味着 finalization 没有经过：

_stream_graph
→ AgentState.repair_mode
→ repair_output_mode=LOCAL_PATCH
→ Context Builder
→ LOCAL_PATCH_SYSTEM_PROTOCOL
→ _agent_llm_invoke retry/trace

更关键的是 _fin_msgs 基于最初的 messages，所以里面没有 LOCAL_PATCH 的 system-level protocol；只有 HumanMessage 在说“output patch JSON only”。

这实际上重新制造了一个我们前面刚刚消灭的弱化版问题：

正式 repair：
System = LOCAL_PATCH protocol

finalization：
System = 普通 Main Agent system
Human = 请输出 patch JSON

所以 H13 的 finalization INVALID_JSON 现在还不能归因于模型不服从 JSON。

必须改成：

latest bundle
↓
same Main Agent
↓
_stream_graph(
    repair_mode=true,
    repair_output_mode=LOCAL_PATCH,
    no_tools=true
)
↓
patch JSON

并且：

repairs_used 不增加
PATCH_FINALIZATION_INVOCATIONS +1

这之后才能评价 finalization reliability。

3. “runtime 仍验 SHA 身份”这个 H2-05 是 false-green

当前 H2-05 测的是：

错误 issue_id
→ UNKNOWN_ISSUE_ID

然后把它称作 “runtime still verifies identity”。

但 apply_main_agent_patches_v2() 实际没有重新计算并核对：

candidate_sha
anchor content sha

它直接相信 bundle 里的 start/end，然后执行 replacement。

我们删除的是：

模型回显 SHA

不是：

runtime 不再校验 SHA

正确合同仍应是：

MODEL_ECHO_CANDIDATE_SHA = false
MODEL_ECHO_ANCHOR_SHA = false

RUNTIME_CANDIDATE_SHA_CHECK = true
RUNTIME_ANCHOR_SHA_CHECK = true

所以这项必须真正落地。

4. fingerprint 现在只有“函数存在”，没有 live classification

函数已经正确升级成：

code
+ normalized locator
+ evidence_ref

。

但 engine 没有把 repair 前后的 fingerprints 做：

RESOLVED
PERSISTED
INTRODUCED

分类；evaluation runner 也完全没有把这些信息持久化。当前 canonical runner 最后只保存：

issue_counts
final_issues
lp_applied
lp_errors
tool_starts

。

因此 receipt 对 H02 的：

“patch 后新引文主张产生”

目前没有证据支持。

H02 实际只证明：

[2,2,2]

。

它可能是：

A,B → A,B → A,B

也可能：

A,B → C,D → E,F

甚至：

A,B → A,C → A,D

现在不知道。

所以我不会授权针对“新引文主张”设计新规则，直到 fingerprint 真正进入运行 artifact。

还有一点：你说这次 5/8 相比 V2 6/8 的下降主要来自 ALL-local 路由，我也不接受作为已证实归因。当前这次 artifact 本身是 LOCAL_PATCH_TRIGGERED=8/8。

两轮 normal generation 本来就是 temperature=0.7，初始候选不同。最多能说“不可直接比较”，不能把差值明确归因给 routing。

O7-E RCA-1 H2D
Eligibility, Canonical Finalization & Live Telemetry Closure
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 78221c5ed

MODEL_UNDER_TEST = deepseek-v4-pro
REPAIR_CONFIG = RP-B

MAX_VALIDATION_REPAIRS = 2
PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false

只做机械收口，不调模型，不调 scholarly prompt，不改 validator。

§1 LOCAL_PATCH preflight 真正闭合

不要只：

can_handle(validation)

改成类似：

adapter.prepare(candidate, validation, raw_tool_log)

结果必须带：

supported
unsupported_reason
bundles
catalog
prompt
candidate_sha

只有：

all issue codes local
AND
all bundles have exact anchors
AND
prompt structurally complete

才：

repair_output_mode = LOCAL_PATCH

否则在 LLM repair invocation 之前：

FULL_REWRITE

Hard：

LOCAL_PATCH_BLANK_PROMPT_INVOCATIONS = 0
LOCAL_PATCH_UNRESOLVED_ANCHOR_INVOCATIONS = 0
§2 runtime identity verification

每个 patch context 内部保存：

candidate_sha256

但不展示给模型。

apply 前：

sha(current_candidate)
==
context.candidate_sha256

每个 anchor：

sha(candidate[content_start:content_end])
==
bundle.anchor.content_sha256

否则：

STALE_CANDIDATE
STALE_ANCHOR

机械拒绝。

新增真测试，不许再拿 UNKNOWN_ISSUE_ID 代替 identity test。

§3 finalization 禁止 direct LLM invoke

删除 evaluation finalization 中的：

get_repair_llm().invoke(...)

必须复用 canonical graph path：

_stream_graph(
    finalization_messages,
    no_tools=true,
    repair_mode=true,
    repair_output_mode="LOCAL_PATCH"
)

要求 spy 真实证明模型输入中存在：

LOCAL_PATCH_SYSTEM_PROTOCOL

且不存在：

REPAIR_SYSTEM_PROTOCOL / full-rewrite directive

Hard：

FINALIZATION_DIRECT_LLM_INVOKE = 0
FINALIZATION_CANONICAL_CONTEXT_BUILDER = true
FINALIZATION_TOOL_CALLS = 0
FINALIZATION_INCREMENTS_REPAIRS_USED = false
§4 顺手消掉 no-tools 的 System/Human 冲突

现在 LOCAL_PATCH System 仍写：

“工具仍可正常使用”

。

然后 Human 层再补：

tool_execution_available=false

System 优先级高，所以这不算真正消解。

把 system 文案机械中性化成：

若本 invocation 允许工具执行，你可以继续检索；
若提供了 tool_execution_available=false，则不得宣告工具。

不是 policy tuning，只是消灭矛盾。

§5 live fingerprint classification

每一 validation state：

issue_fingerprints

真正进入 _val_history。

每个 successful patch 后下一 validation：

resolved
persisted
introduced

由集合差机械计算。

例如：

before={A,B}
after={B,C}

resolved={A}
persisted={B}
introduced={C}

不得存 issue 正文。

§6 canonical evaluation artifact 必须真的带 hard-gate telemetry

当前 runner 没做到。

每 case 至少持久化：

repair_trace_safe
issue_fingerprint_trajectory

anchor_total
anchor_resolved

prompt_issue_total
prompt_issue_visible

linked_evidence_required
linked_evidence_present

unknown_slice_ids

quote_wrapper_loss
non_target_changed_chars

patch_finalization_invocations

patch_diag:
  chars
  starts_object
  fence_wrapped
  empty
  trailing_non_json

汇总才能真正输出：

ANCHOR_RESOLUTION_RATE
PROMPT_ISSUE_COVERAGE
LINKED_EVIDENCE_STARVATION
UNKNOWN_SLICE_ID
QUOTE_WRAPPER_LOSS
NON_TARGET_TEXT_CHANGED_CHARS

不能再在回执里报这些、artifact 却没有。

§7 H2 tests 必须升级成 integration，不只是 source-presence test

现在 H2-15~19 大量只是：

hash 会变化
函数能 build
源码中出现 finalization 字样

并没有证明真实 engine 行为。

新增至少 8 个 integration tests：

I1 anchor 缺失 → 首轮就是 FULL_REWRITE
I2 anchor 缺失 → LOCAL_PATCH protocol 从未注入

I3 stale candidate SHA → reject
I4 stale anchor SHA → reject

I5 repair 调工具 → finalization 走真实 _stream_graph
I6 finalization model input 含 LOCAL_PATCH System
I7 finalization no_tools → 0 tool calls
I8 finalization 不增加 repairs_used

I9 protocol error attempt1 → prev_errors 真进入 attempt2
I10 before/after fingerprint 真产生 resolved/persisted/introduced
然后只重跑 RUN1

仍是旧 8-case calibration。

Hard Gate 一个字不改：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

VALIDATOR_EMPTY_FINAL=0

ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0

UNKNOWN_SLICE_ID=0
QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

如果 PASS：

RUN2 自动授权

如果 FAIL：

STOP

然后我会根据真正的 live fingerprint + patch diag决定：

是 patch action semantics 有问题
还是 JSON transport 有问题
还是 source context / slice catalog 有问题

不再盲补协议。

最终回执：

O7_E_RP2_RCA1_H2D =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

ELIGIBILITY_SHA=
FINALIZATION_SHA=
TELEMETRY_SHA=
TEST_SHA=
RUN1_SHA=
HEAD_SHA=
REMOTE_SHA=

LOCAL_PATCH_REQUIRES_ALL_CODES_LOCAL=true
LOCAL_PATCH_REQUIRES_ALL_ANCHORS_RESOLVED=true
LOCAL_PATCH_BLANK_PROMPT_INVOCATIONS=0

MODEL_ECHO_CANDIDATE_SHA=false
MODEL_ECHO_ANCHOR_SHA=false
RUNTIME_CANDIDATE_SHA_CHECK=true
RUNTIME_ANCHOR_SHA_CHECK=true

FINALIZATION_DIRECT_LLM_INVOKE=0
FINALIZATION_CANONICAL_CONTEXT_BUILDER=true
FINALIZATION_LOCAL_PATCH_SYSTEM_PROTOCOL=true
FINALIZATION_TOOL_CALLS=0
PATCH_FINALIZATION_INVOCATIONS=
FINALIZATION_INCREMENTS_REPAIRS_USED=false

NO_TOOLS_SYSTEM_CONFLICT=0

LIVE_ISSUE_FINGERPRINTS=true
RESOLVED_ISSUES=
PERSISTED_ISSUES=
INTRODUCED_ISSUES=

RUN1_COMPLETED=8
RUN1_PUBLISHED=
RUN1_REPAIR_TRIGGERED=
RUN1_REPAIR_CONVERGED=
RUN1_REPAIR_CONVERGENCE=

ANCHOR_RESOLUTION_RATE=
PROMPT_ISSUE_COVERAGE=
LINKED_EVIDENCE_STARVATION=
UNKNOWN_SLICE_ID=
QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=

PATCH_OUTPUT_EMPTY=
PATCH_OUTPUT_FENCE_WRAPPED=
PATCH_OUTPUT_TRAILING_NON_JSON=
PATCH_OUTPUT_OTHER_INVALID_JSON=

RUN2_EXECUTED=

MAX_VALIDATION_REPAIRS=2
PRODUCTION_LOCAL_PATCH_ENABLED=false

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false
PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_LOCAL_PATCH_PRODUCTION /
PATCH_REQUIRED

STOP

所以这次我不选 (a)/(b)/(c)。

5/8 还不值得跑 RUN2；H02 的“新引文”诊断又还没被 live fingerprint 证明；H13 的 finalization 则确实有一个更直接的 engine bug：它绕过了我们刚建立好的 canonical LOCAL_PATCH system path。

把这几个机械洞关完，再跑一次。届时如果还是 5/8~6/8，我不会再允许继续无穷地补 H2E/H2F 小协议；我们会依据完整 telemetry 做一次最终架构裁决。