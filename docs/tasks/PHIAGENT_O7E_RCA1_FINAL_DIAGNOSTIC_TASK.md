
我审完 78221c5ed → 93ee99c56。这轮我选 (d)：不跑 RUN2，不改 COPY_SLICE claim-span，不加“introduced”提示，不再调 prompt。先做最后一次纯机械的 Final Diagnostic Closure。

这不是再开一个 H2E/H2F 无限补丁链。我把它定为 RCA-1 最后一次测量闭环：修完下面这些 false-green 后再跑一次 RUN1；如果仍不过，我下一轮直接做 repair action semantics 的最终架构裁决，不再允许继续补 telemetry/harness 小洞。

O7_E_RP2_RCA1_H2D_REVIEW = PATCH_REQUIRED

MECHANICAL_PROGRESS = ACCEPTED
PATCH_PROTOCOL_ERRORS = 0
VALIDATOR_EMPTY_FINAL = 0

RUN1_COMPLETED = 8
RUN1_PUBLISHED = 6
RUN1_REPAIR_TRIGGERED = 7
RUN1_REPAIR_CONVERGED = 5
RUN1_REPAIR_CONVERGENCE = 0.714

RUN1_HARD_GATE = FAIL

LOCAL_PATCH_ARCHITECTURE = PROMISING_NOT_QUALIFIED

RUN2_AUTHORIZED = false
CLAIM_SPAN_COPY_CHANGE = NOT_AUTHORIZED
INTRODUCED_ISSUE_PROMPT_TUNING = NOT_AUTHORIZED
MAX_REPAIRS_CHANGE = NOT_AUTHORIZED

FINAL_DIAGNOSTIC_CLOSURE = AUTHORIZED

PRODUCTION_LOCAL_PATCH_AUTHORIZED = false
V3_STAGE_B_AUTHORIZED = false

先校正两个回执事实。

当前 6 个 published case 中，H03 是初检即过，并没有触发 LOCAL_PATCH；真正由 LOCAL_PATCH 修复成功的是 H04、H13、S7、H02、H07，共 5/7 repair-triggered case。Artifact 对 H03 明确是 repairs=0 / LOCAL_PATCH_TRIGGERED=false。

另外，H13 这轮也没有“被 preflight 转去 FULL_REWRITE”。它实际上是：

H13
repairs=1
issue_counts=[3,0]
LOCAL_PATCH_TRIGGERED=true
lp_applied=1

也就是这次随机生成出的候选刚好能够正常 localize，然后 LOCAL_PATCH 一轮通过。

所以“H13 证明 unresolved-anchor preflight 生效”这个结论不能成立。

Blocker 1：preflight 仍然没有真正控制 repair_output_mode

这是本轮最直接的 false-green。

Adapter 现在：

Python
Run
def can_handle(self, validation):
    return RC.all_issues_localizable(validation)

而这个函数仍然只检查 issue code 是否都属于 LOCAL_PATCH_CODES。真正检查 anchor/prompt 的是后面的 prepare_local_patch()。

但是 engine 的实际控制流是：

Python
Run
if adapter.can_handle(validation):
    _lp_meta = adapter.build(...)
    _fb = _lp_meta["prompt"]

...

repair_output_mode=(
    "LOCAL_PATCH" if _lp_meta else "FULL_REWRITE"
)

也就是说：

codes 全 local
→ can_handle=true
→ prepare_local_patch.supported=false
→ build 返回 prompt=""
→ _lp_meta 仍然不是 None
→ 仍然进入 LOCAL_PATCH System protocol
→ Human prompt 却是空的

。

这与我们冻结的合同：

ALL codes local
AND ALL anchors resolved
AND prompt complete
→ LOCAL_PATCH

否则在 LLM invocation 之前
→ FULL_REWRITE

并不一致。

而所谓 I1/I2 也没有真正覆盖 engine：I2 只断言 prep["prompt"] == ""，并没有调用 stream_agent() 验证实际 repair_output_mode=FULL_REWRITE。

所以：

LOCAL_PATCH_REQUIRES_ALL_ANCHORS_RESOLVED=true

我目前不接受。

Blocker 2：finalization 虽然“走了 _stream_graph”，但候选收集方式是错的

H2D 把 direct get_repair_llm().invoke() 删除了，这个方向正确。

但现在 finalization 是：

Python
Run
_fin_candidate = ""

async for _fev in _stream_graph(...):
    if _fev.get("type") == "token":
        _fin_candidate += ...

。

问题是 _stream_graph() 本身的设计就是：

未验证 candidate 不向外 yield token，而是写进闭包里的 pending["text"]。

这正是 O2 的核心架构。

所以 finalization 不能靠监听：

type == token

取得 candidate；它应该和普通 candidate 收口一样，在 _stream_graph() 完成以后从：

pending["text"]
+
phrase/rationale tail

取得最终 patch JSON。

当前 RUN1 又恰好：

FINALIZATION_INVOCATIONS = 0

八个 case 全部为 0。

因此这个路径实际上一次都没被真实 RUN1 行使。

更关键的是所谓 I5-I8 仍然只是：

打开 engine_langgraph.py
搜索 "_stream_graph"
搜索 "no_tools=True"
搜索 "repair_output_mode=LOCAL_PATCH"

这属于 source-presence test，不是 integration test。

所以：

FINALIZATION_CANONICAL_CONTEXT_BUILDER = directionally yes
FINALIZATION_EXECUTABLE_CORRECTNESS = NOT_PROVEN
Blocker 3：fingerprint 还没有覆盖“第二次 repair → terminal validation”

这直接影响你这次最重要的诊断。

现在 engine 把：

issue_fps

放在每个 repair_trace attempt 上。

Runner 则用：

Python
Run
for t in trace:
    fp_traj.append(t["issue_fps"])

然后比较相邻 repair attempts。

于是两次 repair 的 case 最多只能得到：

initial validation
→ after repair1

的 fingerprint 差分。

after repair2 的 terminal validation 没有 fingerprint。

所以 artifact 里 S4 / S9 都只有：

"R1": {
  "resolved": ...,
  "introduced": ...
}

根本没有 R2。

因此你现在可以严格证明：

S4:
第一轮修掉 4 个旧 fingerprint
同时出现 1 个新 fingerprint

S9:
第一轮修掉 1 个旧 fingerprint
同时出现 1 个新 fingerprint

但还不能 fingerprint-level 证明：

“这个 introduced issue 在第二轮持续存在。”

第二轮最后虽然仍有 1 个 UNSUPPORTED_EXACT_QUOTE，但是否就是同一个 fingerprint，目前 artifact 不知道。

这就是为什么我仍然不授权你的 (a)。

Blocker 4：TERMINAL_EMPTY_ANSWER 的定义仍然错

Runner 现在定义：

Python
Run
TERMINAL_EMPTY_ANSWER =
    not answer.strip()
    and "EMPTY_FINAL" not in final_codes

。

但 answer 是真正公开给用户的 token。

O2 本来就规定：

validator FAIL
→ 不发布 candidate

所以任何最终 validation fail 的 case：

公开 token = 0

都会被当前 runner 记成：

TERMINAL_EMPTY_ANSWER=true

哪怕内部 terminal candidate 实际有 2500 字。

这就是为什么 summary 现在显示：

TERMINAL_EMPTY_ANSWER=2

。

这两个其实只是 S4/S9 被 validator 拒绝发布，不是“Main Agent 最终产生了空 candidate”。

正确字段应该是：

TERMINAL_CANDIDATE_EMPTY
=
validation.history[-1].candidate_chars == 0

而：

PUBLIC_RESPONSE_EMITTED

另算。

Blocker 5：repair trace 的 protocol SHA 对 LOCAL_PATCH 是错的

现在 _repair_trace 在决定 _lp_meta 之前就写：

Python
Run
"system_protocol_sha256":
    sha256(REPAIR_SYSTEM_PROTOCOL)

。

但是实际 LOCAL_PATCH invocation 使用的是：

LOCAL_PATCH_SYSTEM_PROTOCOL

Context Builder 的互斥注入本身是对的。

于是当前 trace 会出现这种自相矛盾：

实际模型看到 LOCAL_PATCH_SYSTEM_PROTOCOL

但 telemetry 说：
system_protocol_sha = FULL_REWRITE protocol

这是 provenance false-green。

必须记录：

repair_output_mode
actual_system_protocol_sha256

在 mode 决定之后。

最后，Hard Gate telemetry 仍没真正齐

当前 canonical summary 还是只有：

COMPLETED
PUBLISHED
REPAIR_TRIGGERED
REPAIR_CONVERGENCE
LOCAL_PATCH_TRIGGERED
TOOL_LOOP_REAL
VALIDATOR_EMPTY_FINAL
TERMINAL_EMPTY_ANSWER
PATCH_PROTOCOL_ERRORS

。

没有我们冻结的：

PROMPT_ISSUE_COVERAGE
LINKED_EVIDENCE_STARVATION
QUOTE_WRAPPER_LOSS
NON_TARGET_TEXT_CHANGED_CHARS
SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE

所以即使这轮碰巧是 7/8，我仍然不能签 production qualification。

下一步：O7-E RCA-1 FINAL DIAGNOSTIC CLOSURE

这是最后一次纯机械 closure。

IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 93ee99c56

MODEL_UNDER_TEST = deepseek-v4-pro
REPAIR_CONFIG = RP-B

MAX_VALIDATION_REPAIRS = 2

PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false

本轮硬冻结：

LOCAL_PATCH_SYSTEM_PROTOCOL wording
PATCH actions
COPY_SLICE semantics
REPLACE_TEXT semantics
slice catalog algorithm
validator
quote_bound
model config
temperature
repair count

不允许为了成绩修改任何 repair 行为。

只做下面 6 件机械工作。

1. 把 adapter 接口改成 candidate-aware prepare

建议直接消掉这组分裂：

can_handle(validation)
build(candidate,...)

改成：

Python
Run
prep = adapter.prepare(
    candidate,
    validation,
    raw_tool_log,
    prev_errors,
)

只有：

Python
Run
if prep["supported"]:
    _lp_meta = prep
else:
    _lp_meta = None

才能进入 LOCAL_PATCH。

Hard：

UNSUPPORTED_PREP_TO_LOCAL_PATCH = 0
BLANK_LOCAL_PATCH_PROMPT_INVOCATIONS = 0

如果 unsupported，必须使用原有 FULL_REWRITE _fb，不能使用空字符串。

2. 修 finalization candidate capture

必须继续使用：

_stream_graph(
  no_tools=true,
  repair_mode=true,
  repair_output_mode=LOCAL_PATCH
)

但不要从 SSE token 收 patch。

在 graph 完成后，用与正常 candidate 相同的机械收口：

phrase_scr.flush
rationale_parser.finish
pending["text"]

取得 finalization patch。

然后清理 pending。

Hard：

FINALIZATION_DIRECT_LLM_INVOKE=0
FINALIZATION_PATCH_FROM_TOKEN_EVENTS=false
FINALIZATION_PATCH_FROM_PENDING_CANDIDATE=true
3. 写一个真的 finalization integration test

不能再 grep 源码。

构造一个 deterministic fake Main Agent/tool path：

repair attempt
→ 宣告一个真实 tool
→ raw_tool_log hash 改变
→ latest bundle rebuild
→ finalization _stream_graph
→ no_tools=true
→ fake model 返回有效 patch JSON
→ patch 真正 apply

测试必须断言：

PATCH_FINALIZATION_INVOCATIONS=1
LOCAL_PATCH_SYSTEM_PROTOCOL actually in model messages
FULL_REWRITE protocol absent
FINALIZATION_TOOL_CALLS=0
repairs_used unchanged
patch applied=true

这是必须执行代码的 integration test。

4. fingerprint 改以 _val_history 为真源

每一个 validation state 都保存：

issue_fingerprints

包括：

initial
after repair1
after repair2
terminal

runner 从 validation.history 做：

R1
R2

集合差，不再从 repair_trace 猜 terminal state。

于是 S4/S9 才能真正回答：

introduced at R1
→ persisted at R2 ?

还是
→ resolved and replaced by another new issue ?
5. 记录 patch action，不记录 patch 正文

为了下一轮真的做最终 action-semantics 裁决，每条 patch 只保存：

issue_fingerprint
issue_code
anchor_kind
action = COPY_SLICE / REPLACE_TEXT
slice_id   # COPY 时可记

禁止记录：

replacement_text
source text
CoT

这一项很关键。

因为我现在已经看到一个值得高度怀疑的合同问题：

REPLACE_TEXT
= Main Agent 自己的“paraphrase”

但 quote issue 上
runtime 仍然只替换 content_span
并保留外层 「」 / >

也就是说，如果模型真的选择 REPLACE_TEXT 做转述，那么：

“转述文本”仍然待在引号里面，validator 当然可能把它当新的逐字引文。

这非常可能就是 S4/S9 这种：

旧 quote issue 消失
→ 新 UNSUPPORTED_EXACT_QUOTE 出现

的根因。

但现在 artifact 没记录 action，所以我还不签这个诊断。

下一轮拿到 action + terminal fingerprint 后，如果失败新 issue 确实来自 quote-issue 的 REPLACE_TEXT，我会直接修改 action semantics，而不是再调 prompt。

6. 把 Hard Gate telemetry 真正落 artifact

每 case + summary 必须有：

ANCHOR_RESOLUTION_RATE
PROMPT_ISSUE_COVERAGE
LINKED_EVIDENCE_STARVATION

UNKNOWN_SLICE_ID

QUOTE_WRAPPER_LOSS
NON_TARGET_TEXT_CHANGED_CHARS

SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE

PATCH_FINALIZATION_INVOCATIONS

TERMINAL_CANDIDATE_EMPTY
PUBLIC_RESPONSE_EMITTED

TERMINAL_EMPTY_ANSWER 这个混淆字段删除或 deprecated。

并修 protocol provenance：

REPAIR_OUTPUT_MODE
ACTUAL_REPAIR_SYSTEM_PROTOCOL_SHA

LOCAL_PATCH 不能再记录 FULL_REWRITE SHA。

测试要求

当前所谓 I1-I10 里 I5-I8 仍是源码字符串断言，不够。

新增真正执行式回归，至少锁死：

F1 unresolved anchor → actual stream uses FULL_REWRITE
F2 unresolved anchor → Local Patch System never reaches model

F3 finalization tool-use path actually executes
F4 finalization candidate captured from pending, not token event
F5 finalization model input has LOCAL_PATCH System
F6 finalization tool calls = 0

F7 terminal validation fingerprint recorded
F8 two repairs produce R1 and R2 classifications

F9 LOCAL patch trace hashes LOCAL protocol
F10 FULL_REWRITE trace hashes full-rewrite protocol

F11 terminal nonempty invalid candidate != empty candidate
F12 unpublished response != terminal candidate empty
然后最后再跑一次 RUN1

Gate 不变：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

VALIDATOR_EMPTY_FINAL=0
TERMINAL_CANDIDATE_EMPTY=0

ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0

UNKNOWN_SLICE_ID=0
QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

如果 PASS：

RUN2 = AUTHORIZED

如果 FAIL：

STOP

而且这次我明确承诺 reviewer 路线：

不会再批准“Final Diagnostic Closure 2”。

下一次失败后直接按照：

terminal fingerprints
+
patch action
+
anchor kind

做最终语义裁决。

如果证据显示：

quote issue
→ REPLACE_TEXT
→ old issue resolved
→ new unsupported exact quote introduced

下一刀就会是：

REPLACE_TEXT

从当前“一律 content-span replacement”拆成明确的：

COPY_EXACT_QUOTE
vs
PARAPHRASE_CLAIM

其中“是否继续作为逐字引文”由 Main Agent 显式选择 action，runtime 只机械执行。这才是符合 one-brain 原则的修法。

我现在不批准 (a) claim-span COPY，因为它可能直接移除引号形式，让 validator 看不见 verbatim claim，重新引入 anti-gaming 风险。

也不批准 (b) 给模型强调 introduced：第二轮 validator 本来已经会把新 issue 作为当前 issue 给模型，先证明 action semantics 才是根因。

更不批准 (c) RUN2：RUN1 还没过，而且 finalization / eligibility / terminal fingerprint 仍有 false-green。

最终回执：

O7_E_RP2_RCA1_FINAL_DIAGNOSTIC =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

PREP_GATE_SHA=
FINALIZATION_SHA=
TELEMETRY_SHA=
TEST_SHA=
RUN1_SHA=

HEAD_SHA=
REMOTE_SHA=

PREP_INTERFACE=
UNSUPPORTED_PREP_TO_LOCAL_PATCH=0
BLANK_LOCAL_PATCH_PROMPT_INVOCATIONS=0

FINALIZATION_DIRECT_LLM_INVOKE=0
FINALIZATION_PATCH_FROM_PENDING_CANDIDATE=true
FINALIZATION_INTEGRATION_TEST=true
PATCH_FINALIZATION_INVOCATIONS=
FINALIZATION_TOOL_CALLS=0
FINALIZATION_INCREMENTS_REPAIRS_USED=false

LIVE_VALIDATION_FINGERPRINTS=true
TERMINAL_FINGERPRINT_RECORDED=true

R1_RESOLVED=
R1_PERSISTED=
R1_INTRODUCED=

R2_RESOLVED=
R2_PERSISTED=
R2_INTRODUCED=

PATCH_ACTION_TELEMETRY=true
COPY_SLICE_ACTIONS=
REPLACE_TEXT_ACTIONS=

LOCAL_PATCH_TRACE_PROTOCOL_SHA_CORRECT=true
FULL_REWRITE_TRACE_PROTOCOL_SHA_CORRECT=true

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
SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE=

VALIDATOR_EMPTY_FINAL=
TERMINAL_CANDIDATE_EMPTY=
PUBLIC_RESPONSE_EMITTED=

RUN2_EXECUTED=false
# 仅 RUN1 PASS 后可变 true

MAX_VALIDATION_REPAIRS=2
PRODUCTION_LOCAL_PATCH_ENABLED=false

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false
PATCH_ACTION_SEMANTICS_CHANGED=false
REPAIR_PROMPT_CHANGED=false

PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_RUN2 /
REPAIR_ACTION_SEMANTICS_REQUIRED

STOP

这次的数据其实已经把问题压得非常窄了：协议错误已经归零，anchor 这轮也全解析，5/7 repair case ���正被 Local Patch 修好。

现在最值得怀疑的已经不是“大模型听不懂”，而是 REPLACE_TEXT = paraphrase 却仍把 paraphrase 塞在原来的逐字引号 wrapper 里。

但 reviewer 不能靠猜签架构修改。再把 terminal fingerprint + action telemetry 补上一次，我们就能把这一刀落得非常准。