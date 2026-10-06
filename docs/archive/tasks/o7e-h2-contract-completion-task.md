我审完 f3b0634b7 → 5c42f8b3f。这轮 Local Patch V2 的方向成立，而且提升是真实的，但我不选 (a)，也不直接选你说的 (b)。

我选 (c)：先完成 H2 自己尚未落地的机械合同，再重跑一次 RUN1。 不是继续调 prompt。

正式裁定：

O7_E_RP2_RCA1_H2_REVIEW = PATCH_REQUIRED

PATCH_CONTRACT_V2_DIRECTION = ACCEPTED
LOCAL_PATCH_ARCHITECTURE = PROMISING

RUN1 =
6/8 published
6/8 repair-triggered converged
0.750 convergence

RUN1_HARD_GATE = FAIL

RUN2_AUTHORIZED = false
PRODUCTION_LOCAL_PATCH_AUTHORIZED = false

INVALID_JSON_PROMPT_TUNING = NOT_AUTHORIZED_YET

H2_CONTRACT_COMPLETION = REQUIRED
H2_REGRESSION_SUITE = REQUIRED
LATEST_EVIDENCE_FINALIZATION = BLOCKER
MIXED_ISSUE_ROUTING = BLOCKER
PATCH_PROTOCOL_RETRY_FEEDBACK = BLOCKER
CANONICAL_RUN_METRICS = BLOCKER

V3_STAGE_B_AUTHORIZED = false
先纠正回执里的一个事实

正式 artifact 里：

REPAIR_TRIGGERED = 8
PUBLISHED = 6

而且六个发布成功的 case 都经过了 LOCAL_PATCH：

H04  [1,0]
H13  [1,0]
S7   [3,0]
S9   [2,0]
H02  [2,0]
H07  [4,0]

H03 不是初检即过；它是失败 case：

H03 [5,5,5]
lp_applied = 1
lp_errors = INVALID_JSON

S4 则是：

S4 [5,5,5]
lp_applied = 0
INVALID_JSON ×2

所以更准确的结果其实很好看：

6 个成功 case 全部由 LOCAL_PATCH 在第一轮直接清零。

这比“5 个 local + 1 个初检通过”更有价值。

但也意味着 H03 不能简单归类成“只是 JSON 格式失败”：它有一轮 patch 成功机械应用了，但 5 个 issue 一个没少，第二轮才 INVALID_JSON。S4 才是纯粹的两轮 serialization failure。

因此现在直接微调 “ONLY JSON!!!” 之类 prompt，会把两个不同问题混在一起。

我接受的 V2 改进

System 冲突确实已经关闭。Context Builder 现在根据 repair_output_mode 在 REPAIR_SYSTEM_PROTOCOL 与 LOCAL_PATCH_SYSTEM_PROTOCOL 之间二选一，不再同时告诉模型“整篇重写”和“只出 JSON”。

COPY_SLICE 方向也正确：模型不再负责 SHA、offset、evidence_ref，只需选择 issue_id + slice_id；runtime 再机械应用。

这很可能就是为什么：

V1: 3/8, convergence .286
V2: 6/8, convergence .750

而且旧的：

anchor stale
invalid slice offset
evidence_ref mismatch

都消失了。

所以 不要回滚 Local Patch。

但“H2 全部落地”我不能接受

最明显的一条你已经自己披露：

H2-01 ~ H2-25
尚未系统编写

而 compare 也确认本轮根本没有修改 test_o7e_repair_context_arch.py；测试数仍然是此前的 712。也就是说：

H2 contract code exists
≠
H2 contract regression-locked

这本身就足以挡 production。

但我又在实现里发现了几个更重要的问题。

Blocker 1：我们明确要求的 latest-evidence finalization 根本没有实现

H2 §I 的合同是：

repair 内没调用新工具
→ 原 bundle/catalog 应用

repair 内调用了新工具
→ raw_tool_log version changed
→ rebuild latest bundle + catalog
→ same Main Agent 再做一次 no-tools patch finalization
→ 不增加 repairs_used
→ apply latest catalog

当前实现仍然是：

Python
Run
_rebind = adapter.build(... latest raw_tool_log)

parse_and_apply(
    ...,
    {
        "bundles": _lp_meta["bundles"],
        "catalog": _lp_meta["catalog"],
        "rebind_bundles": _rebind["bundles"]
    }
)

真正 apply 的仍然是 旧 bundle + 旧 catalog；rebind_bundles 没被消费。

所以：

LATEST_EVIDENCE_REBUILD_EXECUTED = true
LATEST_EVIDENCE_USED_FOR_PATCH = false
PATCH_FINALIZATION_INVOCATIONS = 0

H03 / S4 又恰好是高工具活动 case，因此这不是理论洁癖，而是实际可能影响失败结果的 confound。

在关掉它之前，我不会把剩余 2 例归因于 prompt。

Blocker 2：上一轮 protocol error 并没有真的反馈给下一轮

render_patch_prompt_v2() 已支持：

Python
Run
prev_errors

但 adapter build 的调用链没有持久化并传入上一 repair attempt 的错误。

当前 engine 遇到 apply error 后确实正确地：

保留原 candidate
不制造 EMPTY_FINAL

这点已经修好了。

但下一轮并没有真正收到：

previous_patch_protocol_errors = ["INVALID_JSON"]

所以“第二轮据机械错误修正格式”的 H2 §G 只完成了一半。

S4 两轮连续 INVALID_JSON 恰好说明这个缺口值得先关。

Blocker 3：mixed local/non-local issue 路由会产生不可能任务

当前：

Python
Run
can_handle()

逻辑是：

只要存在任意一个 LOCAL_PATCH_CODES
→ LOCAL_PATCH

。

但 build_repair_issue_bundles() 会把 所有 validator issues 都放进 bundles，apply_main_agent_patches_v2() 又要求：

every bundle must be patched

。

于是若未来出现：

NEAR_QUOTE_NOT_MARKED     ← local
+
某个 non-local issue

会发生：

can_handle = true
↓
LOCAL_PATCH
↓
non-local bundle 无合法 anchor
↓
但协议要求必须 patch
↓
永远无法满足

正确合同应该是我们之前定的：

ALL issues localizable
AND ALL anchors resolvable
→ LOCAL_PATCH

otherwise
→ FULL_REWRITE

不是 ANY local。

Blocker 4：issue fingerprint 也没有按冻结合同完成

我们要求：

sha256(
  code
  + normalized locator
  + evidence_ref
)

现在实现只有：

Python
Run
code + normalized locator

。

而且 canonical RUN artifact 也没有：

RESOLVED_ISSUES
PERSISTED_ISSUES
INTRODUCED_ISSUES

所以 H03 的：

5 → 5

究竟是：

五个原 issue 全部 persisted

还是：

修掉若干旧 issue
同时造出等量新 issue

现在仍无法回答。

这正是我上轮要求 fingerprint 的原因。

Blocker 5：slice ranking 不是 per-issue

adapter 现在：

Python
Run
locators = [...]
catalog = build_slice_catalog(
    bundles,
    " ".join(locators)
)

。

也就是说每个 issue 的 slice 都用所有 issue locator 拼起来后的同一个 query排序。

五 issue case 尤其容易受影响。

应该是：

vi_1 slices
→ rank against vi_1 locator

vi_2 slices
→ rank against vi_2 locator
...

这不改变 Main Agent 的 slice 选择权，只是让机械候选排序真正对应 issue。

Blocker 6：no-tools 机械事实被 LOCAL_PATCH 覆盖掉了

engine 先给 _fb 加：

NO_MORE_TOOL_EXECUTION_AVAILABLE

随后如果走 LOCAL_PATCH：

Python
Run
_fb = _lp_meta["prompt"]

前面的机械事实就没了。

同时 LOCAL_PATCH System protocol 还在说：

工具仍可正常使用。

所以 hard budget 下会出现：

System: 可以继续用工具
Human: 没告诉你工具已经没了
Runtime: no_tools=True

这也是协议不一致。

需要把：

tool_execution_available

作为机械事实进入 LOCAL_PATCH context。

Blocker 7：RUN1 还缺大量 hard-gate telemetry

当前 canonical summary 只有：

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

但我们冻结的 Gate 还包括：

ANCHOR_RESOLUTION_RATE
PROMPT_ISSUE_COVERAGE
LINKED_EVIDENCE_STARVATION
UNKNOWN_SLICE_ID
QUOTE_WRAPPER_LOSS
NON_TARGET_TEXT_CHANGED_CHARS
SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE

现在 artifact 根本没有这些数。

所以即使今天是 7/8，我也没法签生产 PASS。

裁决：不是 RUN2，也不是继续调 prompt

下一步做一个很小的：

O7-E RCA-1 H2-C
Contract Completion & Canonical Evaluation Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 5c42f8b3f

MODEL_UNDER_TEST = deepseek-v4-pro
REPAIR_CONFIG = RP-B

MAX_VALIDATION_REPAIRS = 2

PRODUCTION_LOCAL_PATCH_ENABLED = false
V3_HOLDOUT_RUN = false

只做以下闭环：

1. 写完 H2-01 ~ H2-25
2. mixed issue route 改为 ALL-local
3. prev_patch_protocol_errors 真正跨 attempt 传递
4. latest-evidence finalization 真正实现
5. per-issue slice ranking
6. fingerprint 加 evidence_ref + 真 telemetry
7. no_tools mechanical fact 进入 LOCAL_PATCH
8. canonical RUN metrics 补齐
9. INVALID_JSON 只加诊断，不改 prompt
latest-evidence finalization 必须按这个落

repair attempt 开始：

raw_log_hash_before

真实 _stream_graph() 结束：

raw_log_hash_after

若：

before == after

直接使用模型原 patch：

original bundle/catalog
→ apply

若：

before != after

则：

丢弃这一 invocation 的 patch serialization
↓
latest raw_tool_log
↓
rebuild fresh bundles
↓
rebuild fresh slice catalog
↓
same Main Agent
↓
LOCAL_PATCH finalization
↓
no_tools=true
↓
不增加 repairs_used
↓
apply latest bundle/catalog

记录：

PATCH_FINALIZATION_INVOCATIONS
INVALID_JSON 这轮不要“修”

先只加无正文 telemetry：

PATCH_OUTPUT_CHARS
PATCH_JSON_PARSE_OK
PATCH_OUTPUT_STARTS_WITH_OBJECT
PATCH_OUTPUT_FENCE_WRAPPED
PATCH_OUTPUT_HAS_TRAILING_NON_JSON
PATCH_OUTPUT_EMPTY

不要保存 raw patch 文本。

这样下一次才能知道 INVALID_JSON 是：

Markdown fence
自然语言前缀
被截断
空输出
真正语法错误

再决定是 transport normalization、structured output 还是 protocol wording。

现在猜“模型可能加了解释”不够。

H2-01 ~ H2-25 必须全部落测试

不接受“约一半旧 A 测试覆盖”。

至少新增：

H2_REGRESSION_TESTS = 25

特别要有：

mixed local + nonlocal → FULL_REWRITE
5 local issues → LOCAL_PATCH

protocol error attempt1
→ candidate unchanged
→ attempt2 LOCAL_PATCH
→ prev_errors visible

repair tool call
→ latest bundle rebuilt
→ no extra repairs_used

no_tools local repair
→ no tool availability claim

fingerprint same code+locator but different evidence_ref
→ different fingerprint
然后重跑 RUN1

注意：这不是“调 prompt 后重考”。

这是把上一份 H2 任务本身没实现完的合同闭合后重新取得有效数据。

Gate 不变：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

VALIDATOR_EMPTY_FINAL=0

PATCH_PROTOCOL_ERROR_TO_EMPTY_FINAL=0
PATCH_PROTOCOL_ERROR_TO_FULL_REWRITE=0

ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0

UNKNOWN_SLICE_ID=0
QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

如果 PASS：

自动跑 RUN2

如果 FAIL：

STOP

这次才根据 INVALID_JSON shape / fingerprint / latest-evidence telemetry 决定下一刀。

最终回执：

O7_E_RP2_RCA1_H2C =
READY_FOR_REVIEW /
PATCH_REQUIRED

BASE_SHA=

CONTRACT_COMPLETION_SHA=
TEST_SHA=
RUN1_SHA=
HEAD_SHA=
REMOTE_SHA=

H2_REGRESSION_TESTS=
H2_01_25_ALL_PASS=

LOCAL_PATCH_REQUIRES_ALL_ISSUES_LOCAL=
MIXED_LOCAL_NONLOCAL_ROUTE=

PREV_PATCH_PROTOCOL_ERRORS_PERSISTED=

RAW_LOG_VERSIONING=true
LATEST_EVIDENCE_FINALIZATION=true
PATCH_FINALIZATION_INVOCATIONS=
FINALIZATION_INCREMENTS_REPAIRS_USED=false

PER_ISSUE_SLICE_RANKING=true

ISSUE_FINGERPRINT_INCLUDES_EVIDENCE_REF=true
RESOLVED_ISSUES=
PERSISTED_ISSUES=
INTRODUCED_ISSUES=

NO_TOOLS_LOCAL_FACT_PROPAGATED=true

PATCH_OUTPUT_EMPTY=
PATCH_OUTPUT_FENCE_WRAPPED=
PATCH_OUTPUT_TRAILING_NON_JSON=
PATCH_OUTPUT_OTHER_INVALID_JSON=

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
PROMPT_ISSUE_COVERAGE=
LINKED_EVIDENCE_STARVATION=
QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=

SOURCE_CONTEXT_HAS_LOCATOR_OVERLAP_RATE=

RUN2_EXECUTED=
RUN2_PUBLISHED=
RUN2_REPAIR_CONVERGENCE=

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

所以这轮最重要的判断是：

6/8 不是 Local Patch 的失败，反而是目前最强的正向信号；但它也还不是“只差一句 JSON prompt”的证据。

尤其 H03：正式 artifact 已经证明它有一轮 patch 成功应用但 5→5 完全没改善。

先把 H2 自己承诺的 latest-evidence finalization、fingerprint、25 项测试和完整 Gate telemetry 补齐。RUN2 现在没有意义。