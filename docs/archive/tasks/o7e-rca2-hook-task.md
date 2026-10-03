我审了 b14646b15 → bec914247。结论是：你对 RUN1 无效的判断正确，我授权方案 (a)，但不采用 env var 门控，而采用显式 evaluation-only hook 注入。

不过在把 hook 接进完整 engine 前，我又抓到了 3 个会让 LOCAL_PATCH 未来出现 false-green 的 blocker，必须和 harness 一起修。否则我们可能跑出一个漂亮的 7/8，但其实是 patch 机制把“引文格式本身”删掉了。

正式裁定：

O7_E_RP2_RCA1_REVIEW = PATCH_REQUIRED

BOOKKEEPING_CORRECTION = PASS
LOCAL_REPAIR_FOUNDATION = DIRECTIONALLY_ACCEPTED
PRODUCTION_DISABLED = PASS
MINI_LOOP_RUN1 = INVALID_AS_EXPECTED

FULL_ENGINE_EVALUATION_HOOK = AUTHORIZED

ENV_VAR_PRODUCTION_GATE = REJECTED
EXPLICIT_EVALUATION_ONLY_INJECTION = REQUIRED

EV_N_RESOLVER = BLOCKER
QUOTE_CONTENT_ANCHOR_SEMANTICS = BLOCKER
PATCH_PROMPT_ISSUE_COMPLETENESS = BLOCKER

LOCAL_PATCH_PRODUCTION_AUTHORIZED = false
V3_STAGE_B_AUTHORIZED = false

你这次 bookkeeping 修正是成立的：正式归档已经明确写成 AT_2=4/8、AT_3=4/8、两者 repair convergence 都是 3/7=0.429，第三轮增益为零。 mini-loop 也确实没有测试到任何 repair：8/8 初检通过，REPAIR_TRIGGERED=0，因此这个 RUN1 不能拿来判断 LOCAL_PATCH。

Blocker 1：ev_N resolver 现在实际上坏了

这里是一个很隐蔽的 Python bug。

_resolve_evidence() 对 ev_N 命中时返回：

Python
Run
return {"kind": "citation", "payload": c}

但调用方是：

Python
Run
kind, payload = _resolve_evidence(...)

于是 Python 解包 dict 得到的是：

kind    = "kind"
payload = "payload"

而不是：

kind    = "citation"
payload = c

。

因此真实：

UNVERIFIED_CITATION
evidence_ref = ev_N

路径目前不会填充 citation source。

A11 没抓住它，是因为测试里的错误 citation 并没有构造出真实 ev_N citation evidence_ref；主要覆盖到了 quote evidence。

这是标准 false-green。

必须统一：

Python
Run
return "citation", c

并增加真实：

UNVERIFIED_CITATION
→ evidence_ref=ev_1
→ bundle.source != null

测试。

Blocker 2：当前 COPY_EVIDENCE_SLICE 有“删掉引文形式而过 validator”的风险

这是最重要的一个。

现在 Quote Bound 给 blockquote 的 anchor 是：

整条 markdown blockquote 行

包括 >；给弯引号 leadin 的 anchor 则是：

从开引号到闭引号

包括引号本身。

而 patch applier 的：

Python
Run
COPY_EVIDENCE_SLICE

会把整个 anchor直接替换成：

Python
Run
ctx[source_start:source_end]

。

所以完全可能发生：

原候选：

> 「何必改造……」

LOCAL PATCH：

COPY_EVIDENCE_SLICE = "何必改作"

结果：

何必改作

Validator 再跑时：

blockquote 消失
引号消失
→ 不再被识别为逐字引文
→ PASS

这不是“把引文修准确”。

这是：

patch 机制机械地取消了 verbatim claim。

A7 当前甚至会奖励这种行为：它只检查 "何必改作" in new、"何必改造" not in new，并没有检查 quote wrapper 仍存在。

这会直接破坏我们一直坚持的：

不是少引用保平安
而是正确引用
正确修法

Quote anchor 必须区分：

claim_span
content_span

例如：

JSON
{
  "claim_start": 100,
  "claim_end": 140,

  "content_start": 103,
  "content_end": 138
}

COPY_EVIDENCE_SLICE 只能替换：

content_span

而不是整个 quote claim。

要求：

blockquote marker preserved
quote delimiters preserved
leadin preserved

例如：

> 「错误原文」

修后必须仍然是：

> 「正确原文」

不能变成普通正文。

多行 blockquote 如果无法安全得到单一 contiguous content span：

LOCAL_PATCH_UNSUPPORTED
→ fallback FULL_REWRITE

先别为了覆盖率把 anchor 复杂化。

Blocker 3：render_patch_prompt() 又重新引入了“尾部 issue 饥饿”

你已经正确把 bundle builder 从：

全局最多 3 evidence

改成 issue-complete。

但最后渲染 prompt 时又做了：

Python
Run
json.dumps(bundles, ... )[:MAX_TOTAL_REPAIR_CONTEXT_CHARS]

。

这意味着当：

多个 issue
+
每项 metadata
+
source context

总长度超过 6000 时，JSON 会被直接从中间截断。

后果包括：

最后几个 issue 完全看不到
JSON 本身变成残缺文本
anchor_sha / evidence_ref 可能被截半

所以：

bundle issue-complete

不等于：

model-visible issue-complete

必须新增 hard gate：

PROMPT_ISSUE_COVERAGE = 1.0
PROMPT_JSON_TRUNCATED = false

正确方式不是整段 JSON [:6000]。

应该：

所有 issue metadata 永远保留
↓
先计算 metadata 固定开销
↓
剩余预算分给 source exact_context
↓
需要时缩短 context

也就是：

裁 evidence text，不能裁 issue identity。

Harness 方案：选 (a)，但改成显式 injection seam

我不同意：

env var → engine 开 LOCAL_PATCH

因为 env var 很容易以后被误带到生产。

更干净的是给 stream_agent() 增加一个私有 evaluation seam：

Python
Run
stream_agent(
    ...,
    _evaluation_repair_adapter=None
)

生产所有调用：

不传
→ None
→ 现有 full-rewrite 行为 byte/semantic unchanged

Evaluation harness：

显式传 LocalPatchRepairAdapter

这样：

PRODUCTION_LOCAL_PATCH_ENABLED=false

不是靠环境变量保证，而是 API 默认值保证。

O7-E RCA-1 H1
Full-Engine Local Patch Evaluation Hook
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = bec914247

PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false
MAX_VALIDATION_REPAIRS = 2

这一轮只做 4 件事：

1. 修 ev_N resolver
2. 修 quote content anchor
3. 修 model-visible issue completeness
4. 把 LOCAL_PATCH 作为 evaluation adapter 接入真实 engine repair loop
1. Resolver

统一返回类型：

_resolve_evidence() -> tuple[str, payload|None]

硬测：

ev_1
qb_read_*
qb_snip_*
qb_corp_*

全部真实命名空间。

2. Quote anchor 新合同

对 quote bundle：

JSON
{
  "anchor": {
    "claim_start": 100,
    "claim_end": 140,

    "content_start": 103,
    "content_end": 138,

    "claim_sha256": "...",
    "content_sha256": "..."
  }
}

Patch：

REPLACE_TEXT

和：

COPY_EVIDENCE_SLICE

默认只操作 content_span。

Citation 仍然可用单 span。

硬门：

QUOTE_WRAPPER_PRESERVED = true
BLOCKQUOTE_MARKER_PRESERVED = true
LEADIN_PRESERVED = true

并新增：

A7b
COPY_EVIDENCE_SLICE 后仍被 Quote Bound extract_quotes() 提取为同 kind

这是 anti-gaming 测试。

3. Duplicate citation anchor

顺手再补一个我发现的边缘问题：

_citation_anchor() 现在只是：

Python
Run
candidate.find(locator)

。

若相同错误 citation 出现两次，两条 issue 都可能锚到第一次。

Quote anchor 已经有 exclude_spans，citation 也要一样。

Hard：

IDENTICAL_DUPLICATE_CITATION_OCCURRENCES
→ distinct anchors
4. Prompt budget

要求：

MAX_TOTAL_REPAIR_CONTEXT_CHARS=6000

继续不变，但定义成：

evidence context budget

而不是整个 JSON 粗暴截断。

Hard：

ALL_ISSUE_IDS_VISIBLE = true
ALL_ANCHOR_HASHES_VISIBLE = true
ALL_RESOLVED_EVIDENCE_REFS_VISIBLE = true
PROMPT_STRUCTURALLY_COMPLETE = true
5. Full-engine evaluation adapter

建议接口：

Python
Run
class EvaluationRepairAdapter:
    def can_handle(validation) -> bool
    def build(candidate, validation, raw_tool_log) -> context
    def parse_and_apply(candidate, model_output, context) -> result

engine 只在：

_evaluation_repair_adapter is not None

时调用。

生产：

None

永远走原路径。

6. 必须复用真实 _stream_graph

这是 harness 是否可信的核心。

LOCAL_PATCH repair 必须继续通过��

同一个 Main Agent
→ _stream_graph
→ repair_mode=true
→ real tool loop
→ same budget
→ no_tools semantics
→ final non-tool output

不能 adapter 自己直接：

repair_client.invoke()

否则又回到 mini-loop 的问题。

正确链：

normal full engine
↓
candidate
↓
validator FAIL
↓
adapter builds LOCAL_PATCH prompt
↓
existing _stream_graph(repair_mode=true)
↓
工具仍可用
↓
final model output = patch JSON
↓
adapter mechanical apply
↓
whole final validator
7. Patch protocol error 语义

若模型输出：

invalid JSON
stale anchor
missing issue
bad slice

本轮 repair attempt 已消耗。

如果还有下一轮：

same Main Agent
+
机械 PATCH_PROTOCOL_ERROR
+
fresh bundle

再试。

不能：

LOCAL_PATCH error
→ 自动切 FULL_REWRITE

否则评估的是混合架构。

只有：

该 validation 本身不可 localize

才允许 fallback full rewrite。

8. 工具调用后的 evidence 刷新

这是 full engine hook 必须做到的。

如果 LOCAL_PATCH repair 里 Main Agent 又调用了工具：

raw_tool_log changes

那么最终生成 patch contract 前必须基于最新 evidence重建 bundle。

不能：

旧 bundle
→ Agent 搜到新证据
→ 仍要求 patch 旧 evidence

Hard：

BUNDLE_EVIDENCE_VERSION =
LATEST_RAW_TOOL_LOG
9. Evaluation Run 1

仍然：

deepseek-v4-pro
RP-B

8 old calibration cases

完整 engine。

输出必须证明：

TOOL_LOOP_REAL=true
LOCAL_PATCH_TRIGGERED>0

否则再次 STOP。

Hard Gate 保持：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
  REPAIR_CONVERGENCE>=0.80

EMPTY=0

ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0

QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

PATCH_PROTOCOL_FATAL_ERRORS=0
10. Run 2

还是：

RUN1 PASS
→ 才跑 RUN2

否则 STOP。

新增回归至少覆盖
H1 ev_N real resolver
H2 qb_read real resolver

H3 duplicate identical citations distinct spans

H4 blockquote COPY preserves >
H5 COPY preserves quote delimiters
H6 repaired exact quote still extracted by Quote Bound

H7 multi-line unsupported local anchor → safe fallback

H8 8 issues all IDs survive prompt rendering
H9 prompt JSON structurally complete
H10 context shrinking never removes issue metadata

H11 production stream_agent without adapter unchanged
H12 adapter path uses real _stream_graph

H13 repair tool call updates evidence before patch
H14 no_tools path still works

H15 patch protocol error consumes attempt
H16 patch protocol error does not silently full-rewrite

最终回执：

O7_E_RP2_RCA1_H1 =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

RCA_FIX_SHA=
ENGINE_EVAL_HOOK_SHA=
HEAD_SHA=
REMOTE_SHA=

EV_N_REAL_RESOLUTION=
QB_REAL_RESOLUTION=

QUOTE_CONTENT_ANCHOR=true
QUOTE_WRAPPER_PRESERVED=
DUPLICATE_CITATION_ANCHORS_DISTINCT=

PROMPT_ISSUE_COVERAGE=
PROMPT_STRUCTURALLY_COMPLETE=

PRODUCTION_EVALUATION_ADAPTER_DEFAULT=None
PRODUCTION_LOCAL_PATCH_ENABLED=false

FULL_ENGINE_TOOL_LOOP_USED=
LOCAL_PATCH_TRIGGERED=

LATEST_EVIDENCE_REBUNDLE=

RUN1_COMPLETED=8
RUN1_PUBLISHED=
RUN1_REPAIR_TRIGGERED=
RUN1_REPAIR_CONVERGED=
RUN1_REPAIR_CONVERGENCE=

ANCHOR_RESOLUTION_RATE=
LINKED_EVIDENCE_STARVATION=
QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=
PATCH_PROTOCOL_ERRORS=

RUN2_EXECUTED=
RUN2_PUBLISHED=
RUN2_REPAIR_CONVERGENCE=

MAX_VALIDATION_REPAIRS=2

FINAL_VALIDATOR_ACCEPTANCE_SEMANTICS_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false

PRODUCTION_MODEL_CHANGED=false
V3_HOLDOUT_RUN=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_LOCAL_PATCH_PRODUCTION /
PATCH_REQUIRED

STOP

所以答案是：

选 (a)，但用显式 evaluation-only hook，不用 env var。

而且这次先把 LOCAL_PATCH 自己的 3 个 false-green 洞堵上，尤其是第二个：不能把“修正引文”实现成“删掉引号，于是 validator 看不见了”。

这个如果不抓住，Local Patch 很可能会显得异常强，但其实是在作弊。