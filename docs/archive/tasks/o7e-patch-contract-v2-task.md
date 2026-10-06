我审完 bec914247 → f3b0634b7。这次 不继续调模型、不加 repair 轮数，也不改 validator。方向确定：继续做 LOCAL_PATCH，但要先把 patch 协议本身从“让模型当 JSON/offset 工程师”改成真正的机械契约。

而且我独立审计又抓到了两个比 slice offset 更根本的问题。

O7_E_RP2_RCA1_H1_REVIEW = PATCH_REQUIRED

FULL_ENGINE_EVALUATION_HOOK = PASS
PRODUCTION_DEFAULT_NONE = PASS
REAL_TOOL_LOOP = PASS

LOCAL_PATCH_ARCHITECTURE = STILL_VIABLE
CURRENT_PATCH_PROTOCOL = NOT_RELIABLE

PATCH_CONTRACT_V2 = AUTHORIZED

OFFSET_BASED_COPY = REJECTED
MODEL_ECHOED_ANCHOR_SHA = REJECTED
MODEL_ECHOED_EVIDENCE_REF = REJECTED

INNER_QUOTE_BLANKET_BAN = NOT_AUTHORIZED

PATCH_PROTOCOL_ERROR_SEMANTICS = BLOCKER
LOCAL_PATCH_SYSTEM_PROTOCOL_CONFLICT = BLOCKER
LATEST_EVIDENCE_REBIND = FALSE_GREEN

LOCAL_PATCH_PRODUCTION_AUTHORIZED = false
RUN2_AUTHORIZED = false
V3_STAGE_B_AUTHORIZED = false

你这轮最有价值的结果不是 3/8 本身，而是终于让真实 engine、真实工具循环、真实 repair path 行使了 LOCAL_PATCH。正式 artifact 确认 7/8 case 进入 repair，7 个都触发 LOCAL_PATCH，工具调用也确实存在；两个 case 真正靠 local patch 收敛，说明这条架构不是空想。

但现在这 3/8 不能拿来判 Local Patch 架构失败，因为协议层还有三个 blocker。

1. 最严重的新发现：System 层现在在命令“整篇重写”，Human 层却命令“只输出 patch JSON”

当前 repair invocation 仍然走：

_stream_graph(... repair_mode=True)

于是 Context Builder 每一个 repair agent turn 都会注入原来的：

REPAIR_SYSTEM_PROTOCOL

而这个 System protocol 明确写的是：

直接为用户的原始问题产出一个完整的替换最终回答
...
只输出完整的替换候选

。

但 LOCAL_PATCH 的 Human prompt 又在说：

Instead of rewriting the whole answer,
output ONLY a JSON patch object

。

也就是说模型当前收到的是：

SYSTEM:
输出完整替换答案

HUMAN:
不要输出完整答案，只输出 JSON patch

而 System 优先级更高。

这足以单独解释相当一部分：

invalid slice
wrong evidence_ref
anchor stale
甚至不稳定 patch JSON

所以当前协议错误不能简单归因为“模型不会算 offset”。

LOCAL_PATCH 必须有自己的 system-level execution contract，并且与 FULL_REWRITE protocol 互斥。

这仍然不是第二个 Agent，只是同一个 Main Agent 的机械输出模式。

2. PATCH_PROTOCOL_ERROR 现在违反了我们冻结的语义

我上一轮明确要求：

PATCH_PROTOCOL_ERROR
→ 消耗本次 repair attempt
→ candidate 保持原样
→ 下一 repair 仍然 LOCAL_PATCH
→ 附机械错误重新尝试

不得 silently fallback FULL_REWRITE

但当前 engine：

Python
Run
if _apply_errs:
    candidate = ""

。

下一轮 validator 得到：

EMPTY_FINAL

而 EMPTY_FINAL 不在 LOCAL_PATCH_CODES 中，于是 adapter 不再 handle，后续就会进入原 full-rewrite 路径。

也就是实际链路：

LOCAL_PATCH protocol error
↓
candidate = ""
↓
EMPTY_FINAL
↓
LOCAL_PATCH disabled
↓
FULL_REWRITE

这正是我们明确禁止的 fallback。

因此 receipt 里的：

EMPTY_FINAL=5

大量其实不是模型真的生成空答案，而是 evaluation seam 自己把 protocol error 人为转换成 EMPTY_FINAL。

这会严重污染 Run 1。

下一轮必须改成：

patch apply fail
→ candidate 保持 pre_patch_candidate
→ repair attempt +1
→ same local validation issues remain
→ next LOCAL_PATCH attempt

绝不制造假 EMPTY_FINAL。

3. LATEST_EVIDENCE_REBUNDLE=true 目前也是 false-green

现在 engine 的确重新：

Python
Run
_rebind = adapter.build(
    pre_candidate,
    validation,
    raw_tool_log
)

但随后 apply 仍然使用：

Python
Run
ctx["bundles"]   # 模型最初看到的旧 bundles

新的：

rebind_bundles

根本没有参与 patch 应用。

而 adapter 的 rebind_ok 实际上只是：

anchor_ok

并不是“所有 evidence_ref 在最新 evidence store 仍可解析”。

所以准确状态应该是：

LATEST_RAW_TOOL_LOG_REBUILD_EXECUTED = true
LATEST_EVIDENCE_ACTUALLY_EXPOSED_TO_PATCH = false

这轮要一起闭合。

你提的两个方向里，我这样裁

你提的方向 1：

offset 提示 / slice_id 简式

授权，但直接跳过“更好的 offset 提示”，采用 slice_id。

不要再让模型算字符位置。

你提的方向 2：

COPY slice 不得含内层引号域

暂不授权。

原因是目前 S9 artifact 只证明：

2 issues → patch applied → 2 issues → patch applied → 2 issues

它没有记录 issue identity/fingerprint，因此还不能证明“新的 issue 是由内层引号产生的”。

而且原典本身完全可能合法包含对话引号。粗暴禁止：

slice 中有 “ ”
→ 不得 COPY

会误伤真实原文。

先把“旧 issue / 持续 issue / 新引入 issue”测清楚，再决定是否需要 quote-domain 约束。

O7-E RCA-1 H2
Local Patch Contract V2
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = f3b0634b7

MODEL = deepseek-v4-pro
REPAIR_CONFIG = RP-B

MAX_VALIDATION_REPAIRS = 2

PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false

这轮不碰学术 prompt，不碰 validator，不碰 Quote Bound matching semantics。

只修 LOCAL_PATCH 执行协议。

A. 增加明确 repair output mode

AgentState 增加机械字段：

Python
Run
repair_output_mode:
    "FULL_REWRITE"
    | "LOCAL_PATCH"

normal：

repair_mode=false
repair_output_mode=None

传统 repair：

repair_mode=true
repair_output_mode=FULL_REWRITE

evaluation LOCAL_PATCH：

repair_mode=true
repair_output_mode=LOCAL_PATCH

它不是语义路由。

选择依据只是：

evaluation adapter present
AND deterministic validator issue codes localizable
B. Context Builder 中两个 protocol 必须互斥

保留现有：

REPAIR_SYSTEM_PROTOCOL

只用于：

FULL_REWRITE

新增：

LOCAL_PATCH_SYSTEM_PROTOCOL

只用于：

LOCAL_PATCH

绝不能同时出现。

Hard：

FULL_REWRITE_PROTOCOL_PRESENT_IN_LOCAL_PATCH = false
LOCAL_PATCH_PROTOCOL_PRESENT_IN_FULL_REWRITE = false

REPAIR_SYSTEM_PROTOCOL_OWNERS = 1
CONTEXT_BUILDER_INJECTION_OWNER = 1

LOCAL_PATCH system protocol 核心语义：

You are the same Main Agent repairing your own candidate.

This invocation does not ask for a replacement answer.
Your final non-tool output must be only the requested patch JSON.

You may use tools normally when more evidence is useful.

Do not rewrite untouched parts of the candidate.
Do not output explanatory prose around the patch object.

Choose the repair actions.
The runtime only applies the exact actions you select mechanically.

注意：仍由 Main Agent 决定：

copy exact evidence
vs
replace with paraphrase
vs
citation correction

runtime 不决定内容。

C. Patch V2：模型不再回显任何 SHA

当前让模型输出：

candidate_sha256
anchor_sha256

没有产品价值。

这些 SHA 是 runtime 自己已经知道的机械绑定事实，让模型重新抄一遍只增加失败概率。

删除模型输出中的：

candidate_sha256
anchor_sha256

Runtime 内部仍然必须验证：

context.candidate_sha256
==
sha(current_candidate)

context.anchor_sha256
==
sha(current_anchor)

也就是说：

安全绑定继续存在，但不再让模型负责 echo。

Hard：

MODEL_ECHOES_CANDIDATE_SHA = false
MODEL_ECHOES_ANCHOR_SHA = false

RUNTIME_CANDIDATE_SHA_CHECK = true
RUNTIME_ANCHOR_SHA_CHECK = true
D. COPY_EVIDENCE_SLICE 改成 COPY_SLICE_ID

彻底删除：

source_start
source_end
evidence_ref

从模型输出合同中。

新输出：

JSON
{
  "patches": [
    {
      "issue_id": "vi_1",
      "action": "COPY_SLICE",
      "slice_id": "vi_1:s2"
    }
  ]
}

Runtime 自己已有：

slice_id
→ evidence_ref
→ exact source bytes
→ source start/end

所以模型只负责：

选哪一段。

不负责：

数 offset / 抄 hash / 抄 evidence ID。

这会直接消灭本轮 4 类 protocol error 中的三类：

invalid evidence slice
evidence_ref mismatch
anchor stale

当前 artifact 确实出现了这三种。

E. Slice Catalog 必须机械生成

每个有 source 的 issue 生成：

JSON
{
  "copy_slices": [
    {
      "slice_id": "vi_1:s1",
      "text": "……"
    },
    {
      "slice_id": "vi_1:s2",
      "text": "……"
    }
  ]
}

模型能看到 text，但输出只填 slice_id。

生成规则：

resolved source.exact_context
↓
按原始标点/换行机械切成 contiguous atoms
↓
允许相邻 atom 的有限 contiguous combinations
↓
全部 slice 都必须是原 evidence 的连续原始子串

限制：

MAX_COPY_SLICES_PER_ISSUE = 12
MAX_COPY_SLICE_NORM_LENGTH = 240

如果候选很多，用现有 Quote Bound 7-shingle overlap 只做候选排序。

禁止：

runtime 自动选择 slice
runtime 自动把最高分 slice 应用

即：

SLICE_SELECTION_OWNER = MAIN_AGENT
F. 不要重新引入“best slice 自动修复”

可以机械生成：

overlap_score

给模型参考。

但：

highest overlap
≠ automatically chosen

Main Agent 仍可以决定：

COPY_SLICE
REPLACE_TEXT
G. Patch protocol error 不得再变 EMPTY_FINAL

新状态：

last_patch_protocol_errors

例如：

UNKNOWN_ISSUE_ID
UNKNOWN_SLICE_ID
INVALID_JSON
DUPLICATE_PATCH
OVERLAP

发生时：

repair attempt consumed = true

candidate_after_attempt =
candidate_before_attempt

validation candidate =
original unchanged candidate

next repair_output_mode =
LOCAL_PATCH

下一轮 prompt 附：

JSON
{
  "previous_patch_protocol_errors": [...]
}

但只给机械错误，不给 runtime 修复建议。

Hard：

PATCH_PROTOCOL_ERROR_TO_EMPTY_FINAL = 0
PATCH_PROTOCOL_ERROR_TO_FULL_REWRITE = 0
H. 只有“本身不可 localize”才 fallback FULL_REWRITE

允许：

anchor unresolved
unsupported multi-line content span
non-local validation code

在 进入第一次 local repair 之前判：

LOCAL_PATCH_UNSUPPORTED
→ FULL_REWRITE

但是一旦该 repair attempt 已进入：

LOCAL_PATCH

模型协议错误不得改模式。

I. Fresh bundle 与 tool-call evidence：真正修正

不要再使用现在这个假的：

build latest bundle
→ 但 apply old bundle

。

机械记录：

raw_tool_log_hash_before_repair
raw_tool_log_hash_after_repair

如果没变化：

apply against original bundle version

如果 repair 中调用了工具、hash 变化：

DO NOT APPLY first patch yet

↓
基于 latest raw_tool_log rebuild bundle + slice catalog
↓
same Main Agent
↓
LOCAL_PATCH finalization invocation
↓
no_tools=true
↓
输出新 Patch V2 JSON
↓
apply latest bundle

这次 finalization：

不增加 repairs_used

因为它是同一 repair attempt 内、工具研究后的 patch serialization phase。

但 telemetry 要单独计：

PATCH_FINALIZATION_INVOCATIONS

这样就真正满足：

BUNDLE_EVIDENCE_VERSION = LATEST_RAW_TOOL_LOG

同时 Main Agent 的工具选择权完全保留。

J. Issue fingerprint：先搞清 S9 到底发生了什么

不要现在就禁内层引号。

每个 validator issue 生成：

issue_fingerprint =
sha256(
  code
  + normalized locator
  + evidence_ref
)

每次 patch 后输出：

RESOLVED_ISSUES
PERSISTED_ISSUES
INTRODUCED_ISSUES

例如：

before:
A B

after:
B C

→ resolved=A
→ persisted=B
→ introduced=C

Hard telemetry：

INTRODUCED_ISSUE_COUNT

这样下一次我们才有资格判断 S9 是：

A 修好了，又造 B

还是：

其实同一个 A 一直没修好
K. 对新 issue 的处理

如果 patch 应用成功但 full validator 产生新 issue：

不回滚 patch。

进入 repair2：

fresh candidate
fresh validation
fresh anchors
fresh slice catalog

并把：

introduced issue fingerprints

作为机械事实放进 prompt。

仍然是同一个 Main Agent。

L. Anti-gaming 继续保持

COPY_SLICE 必须只替换：

content_span

已有：

>
「」
“”
leadin

都保留。

Hard：

QUOTE_WRAPPER_LOSS = 0

但这一轮不增加：

SLICE_CONTAINS_QUOTE_MARK => reject

先看 issue fingerprint 数据。

M. 顺手修 source context 的观测

当前 _best_unit() 仍然：

Python
Run
best[:400]

也就是“找到最相关 unit 后取前 400 字”。

如果真正重叠处在长段落第 500 字以后，就会出现：

选对 unit
但 model-visible exact_context 根本不含匹配位置

这轮先不要改变算法，只加 telemetry：

SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP
SOURCE_CONTEXT_SHINGLE_OVERLAP
COPY_SLICE_CATALOG_SIZE

如果下一轮仍有问题，我们再单独处理 context window，不同时改两层变量。

N. 修评估摘要：EMPTY_FINAL 语义

当前 summary 的：

EMPTY_FINAL=5

其实是：

answer_len=0

的 case 数。

它不是 validator 真正产生：

EMPTY_FINAL

的数量。

下一轮必须分开：

TERMINAL_EMPTY_ANSWER
VALIDATOR_EMPTY_FINAL
PATCH_PROTOCOL_ERRORS

不能混一个字段。

O. Run 1

仍然原 8-case calibration pool：

deepseek-v4-pro
RP-B
FULL ENGINE
MAX_REPAIRS=2

这次必须报告：

LOCAL_PATCH_TRIGGERED > 0
TOOL_LOOP_REAL = true

Hard Gate：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

VALIDATOR_EMPTY_FINAL=0

PATCH_PROTOCOL_ERROR_TO_EMPTY_FINAL=0
PATCH_PROTOCOL_ERROR_TO_FULL_REWRITE=0

PROMPT_ISSUE_COVERAGE=1.0
ANCHOR_RESOLUTION_RATE=1.0
LINKED_EVIDENCE_STARVATION=0

UNKNOWN_SLICE_ID=0
QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

Run1 未过：

STOP

不再调 prompt。

P. Run 1 PASS 才 Run 2

还是双轮：

RUN1 >=7/8
RUN2 >=7/8

两轮 repair convergence >=0.80
必测回归
H2-01 LOCAL_PATCH System 不含 full-rewrite protocol
H2-02 FULL_REWRITE System 不含 local-patch protocol

H2-03 model output 不含 candidate SHA
H2-04 model output 不含 anchor SHA
H2-05 runtime 仍验证 candidate/anchor identity

H2-06 COPY_SLICE valid id copies exact bytes
H2-07 unknown slice id rejected
H2-08 slice cannot cross evidence source
H2-09 slice selection owner = Main Agent

H2-10 patch protocol error preserves candidate
H2-11 protocol error consumes repair attempt
H2-12 second attempt remains LOCAL_PATCH
H2-13 protocol error never creates EMPTY_FINAL
H2-14 protocol error never silently full-rewrites

H2-15 tool-free local repair uses original bundle
H2-16 tool-using local repair detects raw-log version change
H2-17 latest bundle rebuilt
H2-18 finalization uses latest slice catalog
H2-19 finalization does not increment repairs_used

H2-20 issue fingerprint stable for persistent issue
H2-21 resolved/persisted/introduced classification

H2-22 quote wrapper survives COPY_SLICE
H2-23 non-target bytes remain unchanged

H2-24 production adapter default None
H2-25 philosopher diff = 0

最终回执：

O7_E_RP2_RCA1_H2 =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

PATCH_CONTRACT_SHA=
ENGINE_HOOK_SHA=
HEAD_SHA=
REMOTE_SHA=

LOCAL_PATCH_SYSTEM_PROTOCOL_SHA=
FULL_REWRITE_PROTOCOL_PRESENT_IN_LOCAL_PATCH=false
LOCAL_PATCH_PROTOCOL_PRESENT_IN_FULL_REWRITE=false

MODEL_ECHOES_CANDIDATE_SHA=false
MODEL_ECHOES_ANCHOR_SHA=false
MODEL_ECHOES_EVIDENCE_REF=false

PATCH_ACTIONS=
REPLACE_TEXT,COPY_SLICE

SLICE_SELECTION_OWNER=MAIN_AGENT
MAX_COPY_SLICES_PER_ISSUE=
COPY_SLICE_CATALOG_NONEMPTY_RATE=

PATCH_PROTOCOL_ERROR_TO_EMPTY_FINAL=
PATCH_PROTOCOL_ERROR_TO_FULL_REWRITE=

LATEST_EVIDENCE_VERSIONING=true
PATCH_FINALIZATION_INVOCATIONS=

ISSUE_FINGERPRINTS_ENABLED=true
RESOLVED_ISSUES=
PERSISTED_ISSUES=
INTRODUCED_ISSUES=

SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE=

PRODUCTION_LOCAL_PATCH_ENABLED=false

RUN1_COMPLETED=8
RUN1_PUBLISHED=
RUN1_REPAIR_TRIGGERED=
RUN1_REPAIR_CONVERGED=
RUN1_REPAIR_CONVERGENCE=

LOCAL_PATCH_TRIGGERED=
LOCAL_PATCH_APPLIED=

PATCH_PROTOCOL_ERRORS=
UNKNOWN_SLICE_ID=

VALIDATOR_EMPTY_FINAL=
TERMINAL_EMPTY_ANSWER=

ANCHOR_RESOLUTION_RATE=
LINKED_EVIDENCE_STARVATION=
PROMPT_ISSUE_COVERAGE=
QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=

RUN2_EXECUTED=
RUN2_PUBLISHED=
RUN2_REPAIR_CONVERGENCE=

MAX_VALIDATION_REPAIRS=2
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

所以这轮我批准继续迭代 patch contract，但不是简单：

“给 offset 多写点提示。”

offset 本身就不应该由模型负责。

而且当前还有一个比 offset 更大的问题：System 层正在要求“输出整篇替换答案”，Human 层同时要求“只输出 JSON patch”。

先把这个高优先级冲突关掉，再把 patch 从：

算 offset
抄 evidence_ref
抄 SHA

收缩成：

vi_2 → COPY_SLICE → vi_2:s3

这才真正符合我们从一开始的目标：

大脑负责决定修什么；runtime 只负责把决定精确执行。