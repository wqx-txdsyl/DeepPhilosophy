这轮我不能按回执直接进入 RP2。我独立审完后，发现 RP1 的方向对了，但还有两个真正的 blocker，而且都是可复现性/机械闭环问题，不是“再抠细节”。

先给裁定：

O7_E_RP1_REVIEW = PATCH_REQUIRED

PERSONA_SCOPE_ROLLBACK = PASS
GENERAL_ONLY_SCHOLARLY_SCOPE = PASS
GENERAL_SCHOLARLY_CONTRACT_BYTES = ACCEPTED
HARD_BUDGET_UNCHANGED = PASS
VALIDATION_HISTORY_ENGINE_TELEMETRY = ACCEPTED

EMPTY_FINAL_DIRECTIONAL_FIX = ACCEPTED
ZERO_TOOL_REPAIR_GUARANTEE = NOT_ACCEPTED

FORMAL_GATE_RUNNER_TELEMETRY = NOT_ACCEPTED
MODEL_BILLING_BLOCK_CLASSIFICATION = NOT_ACCEPTED

STAGE_B_FIRST_RUN_PRESERVATION = PATCH_REQUIRED

O7_E_RP2_AUTHORIZED = false
O7_E_RP1_FINAL_CLOSURE_AUTHORIZED = true
1. 最大的问题：no_tools 根本没进入 LangGraph 的 State schema

你现在确实实现了：

Python
Run
_stream_graph(..., no_tools=True)

然后：

Python
Run
APP.astream({
    ...
    "no_tools": no_tools,
})

并且 agent_node() 会读：

Python
Run
state.get("no_tools")

。

但是当前 AgentState 里根本没有：

Python
Run
no_tools: bool

这个 channel。现在声明的 state 到 raw_tool_log 就结束了。

也就是说，代码宣称建立了：

hard reached
→ repair no_tools=True
→ LLM 不 bind tools

但 LangGraph 的正式 state contract 并没有这条状态。

我不会靠“当前某版本也许把未知 key 临时透传”来签架构 Gate。

更重要的是，R2/R3 也没有真的证明：

bind_tools 没被调用
tool_start = 0
tool execution = 0

R2 只证明最终出了候选；R3 只证明最终没有因为 EMPTY_FINAL 死掉。

所以这是一个典型 false-green：

测试证明“结果碰巧成功”，没有证明“零工具 repair 协议实际生效”。

这个必须补。

2. 更直接的 blocker：正式 o7e_runner.py 根本没改

这个问题比 receipt 里的 402 更重要。

你回执说：

telemetry 已改用 done.validation.repairs_used/history，不再从 SSE 推导。

但 HEAD 上正式 runner 现在仍然是旧实现：

Python
Run
val_fails = [
    e for e in events
    if e.get("type") == "validation_failed"
]

"validation_rejections": len(val_fails),
"repair_attempts": len(val_fails),

而 error 也仍然读取：

Python
Run
e.get("message", "")

不是 content。

也就是说：

ENGINE
done.validation.history ✅

正式 Gate runner
完全没有消费它 ❌

但 RP1 artifact 里面却已经出现：

validation_attempts
validation_failures
repair_attempts
repair_exhaustion
...

例如 H01。

这意味着这些新字段是通过未跟踪脚本 / 临时处理 / 手工后处理得到的，至少不是当前仓库里的 canonical runner 可以重现。

所以：

DELIVERY_TELEMETRY_MISMATCH=0

我现在不能接受为 reproducible Gate claim。

3. 402 也需要正式分类，而不是算成 terminal pending

这一点你的回执自己已经意识到了。

当前：

9 / 28 = 0.321

不是一个有效产品指标，因为后 14 个根本没有得到一次正常的 Main Agent execution。

正确语义应该是：

COMPLETED
BLOCKED_MODEL_BILLING
RUN_ERROR

例如：

completed holdout = 14
published among completed = 9
publication rate = 9/14 = 64.3%

blocked_model_billing = 14

FINAL_GATE_STATUS = BLOCKED_INCOMPLETE

而不是：

publication rate = 32.1%

也不能把这 14 个记成产品层的：

TERMINAL_PENDING

因为它们并不是 Agent 做完后无法发布，而是生产模型根本没钱跑。

4. Stage-B first run 也没有真正“永久保存为 artifact”

我要求：

原 19/28 Stage-B first run 永久保留，不覆盖。

但本轮仍然修改了同一个：

docs/evidence/o7e_runs_HOLDOUT.json

，compare 里没有增加一个独立的 first-run archive。

Git 历史里当然还能回到 1cfb820c3 看，但那不等同于：

STAGE_B_FIRST_RUN artifact

在当前 Gate 包中显式存在。

这个很好修，但应该修，因为我们后面已经开始出现：

First Stage B
RP1 Stage B
RP2 Stage B

再复用一个文件名，很快会失去审计链。

但有一件事我接受了：RP2 确实已经被“产品事实”触发

虽然还不能正式授权 RP2，但我已经不要求你充值后把这一版 RP1 28 题补跑完。

因为我们已经有足够证据：

General calibration:
7 / 12 published

RP1 completed holdout:
9 / 14 published

而且 EMPTY_FINAL 已经从观察结果中消失，剩下主要是：

NEAR_QUOTE_NOT_MARKED
UNSUPPORTED_EXACT_QUOTE
UNVERIFIED_CITATION

反复两轮不收敛。

这已经足够证明：

修完剩余机械 audit blocker 后，下一步应该是 RP2，而不是继续浪费余额跑一个已知失败的旧 policy。

所以流程是：

RP1 Final Closure
        ↓
不重跑 RP1 28-case full Gate
        ↓
直接授权 RP2
        ↓
RP2 用全新 holdout universe

这样最省钱。

O7-E RP1 Final Closure
Repair State & Gate Reproducibility
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = ffbb21530

NO_DEEPSEEK_GATE_RUN_REQUIRED = true
NO_SCHOLARLY_PROMPT_CHANGE = true
NO_VALIDATOR_CHANGE = true

只修四件事。

A. 把 no_tools 纳入正式 State contract
Python
Run
class AgentState(TypedDict):
    ...
    no_tools: bool

并确保：

_stream_graph(no_tools=True)
→ APP state
→ agent_node state["no_tools"] == true
→ _agent_llm_invoke(no_tools=True)
→ get_llm().invoke(...)
→ bind_tools never called

新增真测试：

C1 no_tools channel exists in graph schema

C2 hard-budget repair:
   bind_tools_calls = 0

C3 hard-budget repair:
   tool_start_after_repair = 0

C4 hard-budget repair:
   executed_tool_calls_after_repair = 0

C5 normal repair with remaining budget:
   bind_tools still works

不要只断言最终 answer 非空。

B. 正式修 o7e_runner.py

必须改 canonical runner。

从：

validation_failed SSE

切到：

done.validation.history
done.validation.repairs_used
done.validation.result

正式计算：

validation_attempts =
len(history)

validation_failures =
count(history.ok == false)

repair_attempts =
done.validation.repairs_used

repair_success =
repair_attempts > 0
AND published
AND final_validation_result == true

repair_exhaustion =
repair_attempts == max_validation_repairs
AND final_validation_result == false

并增加测试，直接调用：

o7e_runner.run_case()

不是单测 engine 后自己另算数字。

C. 修 error / run status

runner 正式读取：

error.content

定义：

run_status =
COMPLETED
BLOCKED_MODEL_BILLING
RUN_ERROR

如果出现：

Insufficient Balance
402
余额不足

则：

BLOCKED_MODEL_BILLING

要求：

published = N/A
terminal_pending = false
publication_denominator_member = false

但最终 Gate：

completed_cases < required_cases
→ GATE = BLOCKED_INCOMPLETE

不能因为排除 denominator 就让 14/28 也 PASS。

D. Artifact 命名冻结

把已有 first run 从 commit 1cfb820c3 原样归档：

docs/evidence/
  o7e_runs_HOLDOUT_STAGE_B_FIRST.json

当前 RP1 partial：

o7e_runs_HOLDOUT_RP1_PARTIAL.json

未来 canonical final Gate 才写：

o7e_runs_HOLDOUT_FINAL.json

至少记录：

policy_sha
case_universe_hash
runner_sha
run_status

这样以后不会混。

不要做的事情

这轮禁止：

❌ 充值后补跑旧 RP1
❌ 改 Scholarly Contract
❌ 改 quote validator
❌ 调高 tool budget
❌ 改 case quality threshold
❌ 新工具
❌ 秘塔
❌ Growth
❌ Whole-book
Final Closure Gate
NO_TOOLS_STATE_DECLARED = true

HARD_REPAIR_BIND_TOOLS_CALLS = 0
HARD_REPAIR_TOOL_STARTS = 0
HARD_REPAIR_TOOL_EXECUTIONS = 0

NORMAL_REPAIR_TOOL_CAPABILITY_PRESERVED = true

CANONICAL_RUNNER_USES_VALIDATION_HISTORY = true
CANONICAL_RUNNER_USES_REPAIRS_USED = true
CANONICAL_RUNNER_READS_ERROR_CONTENT = true

BLOCKED_MODEL_BILLING_CLASSIFICATION = true
BLOCKED_MODEL_BILLING_IN_PUBLICATION_DENOMINATOR = 0

INCOMPLETE_HOLDOUT_CAN_PASS = false

STAGE_B_FIRST_RUN_ARTIFACT_PRESERVED = true
RP1_PARTIAL_ARTIFACT_SEPARATE = true

SCHOLARLY_CONTRACT_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

FULL_TEST_FAILED = 0

回执：

O7_E_RP1_FINAL_CLOSURE =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

NO_TOOLS_STATE_DECLARED=

HARD_REPAIR_BIND_TOOLS_CALLS=
HARD_REPAIR_TOOL_STARTS=
HARD_REPAIR_TOOL_EXECUTIONS=

NORMAL_REPAIR_TOOL_CAPABILITY_PRESERVED=

CANONICAL_RUNNER_USES_VALIDATION_HISTORY=
CANONICAL_RUNNER_USES_REPAIRS_USED=
CANONICAL_RUNNER_READS_ERROR_CONTENT=

RUN_STATUS_ENUMS=
BLOCKED_MODEL_BILLING_CLASSIFICATION=
BLOCKED_MODEL_BILLING_IN_PUBLICATION_DENOMINATOR=
INCOMPLETE_HOLDOUT_CAN_PASS=

STAGE_B_FIRST_RUN_ARTIFACT=
STAGE_B_FIRST_RUN_POLICY_SHA=
STAGE_B_FIRST_RUN_CASE_HASH=

RP1_PARTIAL_ARTIFACT=
RP1_PARTIAL_POLICY_SHA=
RP1_PARTIAL_CASE_HASH=

SCHOLARLY_CONTRACT_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
BUDGET_INCREASED=false

DEEPSEEK_GATE_RERUN=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7_E_RP2_AUTHORIZED=false
PROPOSED_VERDICT=PASS

STOP

这轮过了之后，我会直接授权 RP2，不要求你再为旧 RP1 烧一次 DeepSeek 额度。

而且 RP2 我已经基本知道该怎么改了：它不会去降低 validator，也不会让 Agent “少引用保平安”，而是专门解决：

Main Agent 已经拿到了证据，却不会根据 NEAR_QUOTE / UNSUPPORTED_QUOTE / UNVERIFIED_CITATION 的机械反馈，在两次 repair 内稳定产出新的合法完整答案。

那才是下一轮真正要解决的问题。