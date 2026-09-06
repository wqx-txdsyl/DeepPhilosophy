我已经按 Reviewer 口径把这次 Stage-B 的代码、runner、失败样本和 repair 路径重新审了一遍。结论不是简单的“prompt 不够好”。

这轮确实 PATCH_REQUIRED，但我现在不授权直接调 scholarly prompt。先修两个更基础的问题：repair 的机械兼容性 + Gate 统计真值。 另外还有一个我们刚刚已经重新明确的产品边界：O7-E 只管通用 Agent，哲学家 Agent 从这一阶段退出。

正式裁定：

O7_E_STAGE_B_FIRST_HOLDOUT_REVIEW = PATCH_REQUIRED

STAGE_B_FREEZE_DISCIPLINE = PASS
GENERAL_SCHOLARLY_POLICY_DIRECTION = ACCEPTED
CALIBRATION_RESULT = ACCEPTED_AS_DIAGNOSTIC

SCHOLARLY_AXIS_PUBLISHED_SUBSET = DIRECTIONALLY_ACCEPTED
DELIVERY_AXIS = FAIL

REPAIR_RUNTIME_COMPATIBILITY = BLOCKER
DELIVERY_EVALUATOR_ACCOUNTING = BLOCKER

PERSONA_SCOPE_IN_O7E = REVOKED
PHILOSOPHER_AGENT_CHANGES = REVERT_REQUIRED

SCHOLARLY_PROMPT_TUNING = NOT_AUTHORIZED_YET

O7_E_RP1_AUTHORIZED = true
O7_E_FINAL_REVIEW = NOT_READY
一、Stage-B 的失败是真的，但目前“18 次 repair”这个指标并没有被 Gate runner 正确记录

这是我审出来的第一个独立问题。

生产 validator 明确：

Python
Run
MAX_VALIDATION_REPAIRS = 2

而 repair 是：

initial candidate FAIL
→ repair 1
→ validate
→ repair 2
→ validate
→ exhausted

。

但当前 O7-E runner 是这么算的：

Python
Run
val_fails = [event for event if type == "validation_failed"]

"validation_rejections": len(val_fails),
"repair_attempts": len(val_fails),

。

问题在于，engine 不是每次 validator FAIL 都发 validation_failed。

它只是在两轮 repair 全部耗尽、最终仍失败时才发一次：

validation_failed

。

所以 tracked artifact 会出现这种情况：

H03
published=false
validation_rejections=1
repair_attempts=1

但你这次 receipt 又正确地从诊断运行里得到：

9 cases × 2 repair = 18

两者冲突。

所以：

19/28 publication rate 是可信的；但当前正式 artifact 的 repair/rejection telemetry 不可信。

这个必须先修，否则下一轮即使 PASS，我们也没法审计 repair success rate。

二、EMPTY_FINAL 很可能不是单纯 prompt 问题，我找到了一个真实的机械失配路径

这一点更重要。

当前 hard budget 是：

hard_retrieval = 20
hard_total = 24

。

而 repair 会继承初始回答已经消耗掉的同一个 ToolBudget。

当预算 hard reached 后，agent_node() 会进入：

forced = true

并告诉 Main Agent 必须收尾。

如果此时 repair Agent 仍然因为：

“引用没核验”
“需要再查一个 source”

而宣告工具：

第一轮工具会被：

RESOURCE_CEILING_REACHED

拒绝。

随后再回 Main Agent。

如果它再次宣告工具，forced_tools_done=true 后：

Python
Run
should_continue(...)
→ end

。

而 _stream_graph() 收尾时，如果当前 invocation 仍是：

pending["has_tools"] == true

就会把 pending candidate 清掉。

最终：

candidate = ""
→ EMPTY_FINAL

这和你诊断运行发现的：

EMPTY_FINAL

高度一致。

而且 H03 已经给了一个很有价值的例子：

20 tool calls
primary_text_read = true
却最终 published=false

。

所以至少一部分失败并不是：

Agent 根本不会研究。

而可能是：

Agent 已经研究了很多 → validator 要求 repair → repair 想继续查 → 机械 hard ceiling 与 repair protocol 互相打架 → 最终空候选。

这属于 engine delivery compatibility bug。

因此现在直接改 Scholarly Contract，会把真正的 runtime bug藏起来。

三、为什么我现在不授权 prompt tuning

19 个已发布 Holdout 的学术分实际上不差：

APPLICABLE ≈ 3.56

AR = 4.0
IP ≈ 3.67
HD ≈ 3.42
LO ≈ 3.29
fatal = 0

虽然：

REQUIRED_DIMENSION_MEDIAN_LT_2 = 1

还没过最终门，但现在最大的失败不是“回答太差”。

而是：

9 / 28 根本没有发布

先把“会不会稳定产出完整候选”修好，再看剩余质量差距。

否则非常容易走回我们之前一直反对的路径：

publication 差
↓
减少引用
↓
减少工具
↓
减少争议
↓
写得更像课本
↓
publication 上升

那是假的优化。

四、还有一个必须现在纠正的 scope：哲学家 Agent 不再属于 O7-E

这个是我之前 O7-E 任务书写错了，现在按照你刚刚重新明确的产品设计修正。

当前代码确实在 O7-E 给 philosopher persona 新增了：

search_scholarship
get_scholarly_source

。

而 SCHOLARLY_CONTRACT 现在也是：

Python
Run
所有 agent
→ _build_context_messages
→ 都 append 同一个 Scholarly Contract

。

Holdout 里也正式放了四个 Nietzsche persona case：

H26
H27
H28
H29

，Calibration 还有 S11。

这与我们现在明确的产品边界不符：

DeepPhilosophy 主站
        +
PhiAgent 通用 Agent   ← 当前主线
        +
哲学家 Agent          ← 你以后单独设计

所以 O7-E RP1 必须顺手把这个误入 scope 的部分撤回。

O7-E RP1
General-Agent Delivery Closure & Gate Truth Repair
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
1cfb820c3

PHASE =
O7-E RP1 — GENERAL AGENT DELIVERY CLOSURE

PRIMARY_TARGET =
GENERAL AGENT ONLY

SCHOLARLY_PROMPT_TUNING =
NOT AUTHORIZED

FINAL_VALIDATOR_CHANGE =
NOT AUTHORIZED
0. 原 Stage-B 冻结保存

不得覆盖：

O7E_POLICY_SHA =
a3afddaf7

OLD_HOLDOUT_CASE_UNIVERSE_HASH =
135ef3b7e40d46df...

OLD_HOLDOUT_RESULT =
19 / 28

原失败 artifact 永久作为：

STAGE_B_FIRST_RUN

保存。

不能重写成“后来通过了”。

1. 哲学家 Agent scope rollback

撤回：

cb6af371f

所引入的 O7-E persona scholarly tool exposure：

PHILO_SHARED_TOOLS
- search_scholarship
- get_scholarly_source

恢复 O7-E 前状态。

只撤这两项，不碰你原来的哲学家 Agent 系统。

要求：

PHILOSOPHER_AGENT_O7E_DIFF = 0

以：

cec4885f9

为 O7-E 前哲学家行为基线。

2. Scholarly Contract 只属于 General Agent

保持：

SCHOLARLY_CONTRACT

单一 canonical owner。

但：

Python
Run
if agent == "general":
    inject SCHOLARLY_CONTRACT
else:
    do not inject O7-E scholarly policy

所以：

SCHOLARLY_POLICY_OWNER = 1
GENERAL_AGENT_SCHOLARLY_POLICY = true
PHILOSOPHER_AGENT_SCHOLARLY_POLICY_INJECTION = 0

这不意味着哲学家 Agent 永远不能学术检索。

只是：

O7-E 不替你设计它。

3. 新 General-only Gate Universe

旧 28 Holdout 中有 4 persona case。

正式 O7-E General Gate 改为：

旧 24 个 general holdout
+
4 个全新 general holdout
=
28

这 4 个新 case 必须在任何 RP1 engine 修改之前写入并冻结。

建议四题：

G25
罗尔斯的原初状态和无知之幕分别在论证中起什么作用？

G26
福柯的“权力—知识”是否意味着所有知识都只是权力的产物？

G27
《庄子》的庖丁解牛应如何从原文理解，
而不是把它简单解释成“熟能生巧”？

G28
亚里士多德在《范畴篇》和《形而上学》中谈“实体”时，
概念有没有发生变化？

不得拿这四题做 prompt calibration。

先冻结：

O7E_RP1_GENERAL_HOLDOUT_CASE_UNIVERSE_HASH

然后再改 engine。

Calibration 的 S11 persona 也换成一个 General case。

4. 修 Gate telemetry

runner 不得再从：

validation_failed SSE count

推导 repair 次数。

正式真值改为：

done.validation.repairs_used

至少记录：

validation_attempts
validation_failures
repair_attempts
repair_success
repair_exhaustion
final_validation_result
final_validation_issue_codes

定义：

repair_attempts =
实际 same-main-agent repair invocation 数

validation_failures =
实际 validator 返回 ok=false 的次数

repair_success =
repair_attempts > 0
AND final published=true
5. 增加 validation history

Engine 可增加纯机械 telemetry：

done.validation.history

每次保存：

attempt_index
ok
issue_codes
candidate_chars
candidate_sha256

禁止保存：

hidden reasoning
raw CoT

不要求把 rejected candidate 正文公开给用户。

6. 修 error telemetry

runner 当前读：

Python
Run
e.get("message")

但 engine error event 实际主要放：

content

所以必须改成：

content
fallback message

不能再出现：

JSON
"error_messages": [""]

这种假观测。

7. Repair hard-budget compatibility

这是 RP1 主修。

保持：

hard_retrieval = 20
hard_total = 24

禁止通过提高预算掩盖问题。

正确协议
当 repair 开始时预算尚未 hard reached

保持：

same Main Agent
+
full tool set

Agent 可以继续研究。

当 repair 开始时已经 hard reached

这是机械事实：

NO_MORE_TOOL_EXECUTION_AVAILABLE

此时允许 runtime 机械进入：

REPAIR_NO_MORE_TOOLS

但它不能替 Agent 写答案。

Main Agent 仍然是 writer。

推荐：

same Main Agent
+
existing messages/evidence
+
validator issues
+
mechanical resource-ceiling notice
+
tool_choice = none

或者等价的：

bind no executable tools

仅限 hard ceiling 已经成立的 repair invocation。

这是资源控制，不是认知决策。

8. Repair contract 必须要求完整 replacement candidate

当前 feedback：

Revise the candidate or gather more evidence as appropriate.

太容易让 repair turn 只产生工具宣告。

允许把协议措辞改为类似：

This is a validation repair of the same answer.

Produce a complete replacement final candidate.

The validator issues below are mechanical evidence problems.
You may gather additional evidence only if tool resources remain available.
If the tool resource ceiling has been reached, revise using the evidence
already obtained.

Do not return an empty candidate.

这不是 scholarly 内容 prompt。

它只是：

repair transport contract

不得告诉 Agent：

删哪些观点
必须弱化哪个争议
必须删引用

那些仍由 Main Agent 自主决定。

9. 必须新增机械回归

至少覆盖：

R1
invalid candidate
+ budget available
→ repair may call tool
→ valid final candidate

R2
invalid candidate
+ hard budget already reached
→ repair cannot execute cognitive tools
→ same Main Agent still returns complete candidate

R3
hard budget
+ model attempts tool declaration
→ must NOT end as EMPTY_FINAL solely because forced_tools_done

R4
repair candidate empty
→ counted faithfully
→ never published

R5
MAX_VALIDATION_REPAIRS=2
→ runner reports repair_attempts=2

R6
initial fail + repair1 fail + repair2 fail
→ validation_failures=3
→ repair_attempts=2
→ repair_exhaustion=true

R7
initial fail + repair1 PASS
→ validation_failures=1
→ repair_attempts=1
→ repair_success=true

R8
error content captured

R9
no budget increase

R10
no validator semantic change
10. 不改 scholarly prompt

General Agent 的：

SCHOLARLY_CONTRACT

正文这一轮保持 byte-identical。

只允许改：

injection scope

即：

all agents
→ general only

因此：

GENERAL_SCHOLARLY_CONTRACT_HASH_UNCHANGED = true
11. RP1 Calibration

机械修复完成后：

General-only calibration = 12

这里只检查：

publication
validator/repair
architecture regression

不能再调 Scholarly Contract。

如果机械层仍大面积失败：

STOP

不要动 prompt。

12. RP1 Formal Stage-B

然后对新冻结的：

28 General holdout

第一次完整运行。

这才是新的正式 Gate。

要求继续：

FINAL_PUBLICATION_RATE >= 0.90

并新增：

EMPTY_FINAL_AFTER_REPAIR = 0
DELIVERY_TELEMETRY_MISMATCH = 0
13. 如果这次仍失败怎么办

非常重要。

如果 RP1 后：

publication < 90%

但机械 EMPTY_FINAL 已经消失，剩下是真正的：

UNVERIFIED_CITATION
UNSUPPORTED_EXACT_QUOTE
NEAR_QUOTE
...

反复不收敛，

那我才授权：

O7-E RP2 — SCHOLARLY / REPAIR POLICY TUNING

并且 RP2 必须使用新的 holdout universe。

这样不会拿已经看过的题偷偷调 prompt。

14. O7-E 仍然不做 Growth / Wholeness

我们刚刚确定的：

Growth
Wholeness
Whole-Book Cognitive Model
认知水平匹配

都很重要。

但不要塞进这个 repair。

现在 O7-E 只完成：

Truth
+
Depth
+
delivery reliability

等 O7-E 真正收口后，我们单开通用 Agent 下一条主线：

Cognitive Growth Alignment
+
Whole-Book Understanding

Hermes 也放到那里正式 benchmark。

RP1 HARD GATE
TARGET_AGENT = GENERAL_ONLY

PHILOSOPHER_AGENT_O7E_DIFF = 0
PHILOSOPHER_AGENT_SCHOLARLY_POLICY_INJECTION = 0

GENERAL_SCHOLARLY_CONTRACT_HASH_UNCHANGED = true

HARD_RETRIEVAL_BUDGET = 20
HARD_TOTAL_BUDGET = 24
BUDGET_INCREASED = false

REPAIR_ATTEMPT_ACCOUNTING_DELTA = 0
VALIDATION_FAILURE_ACCOUNTING_DELTA = 0

EMPTY_FINAL_AFTER_REPAIR = 0

FINAL_PUBLICATION_RATE >= 0.90

TERMINAL_PENDING = 0
TOOL_LOOP_ABORTS = 0

APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0

FATAL_FLAGS = 0

FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

O7B_RUNTIME_DATA_CHANGED = false
O7C_ACCESS_SEMANTICS_CHANGED = false
O7D_CORPUS_CHANGED = false

COGNITIVE_POLICY_OWNER = 1
SCHOLARLY_POLICY_OWNER = 1

FULL_TEST_FAILED = 0

最终回执：

O7_E_RP1 =
READY_FOR_FINAL_REVIEW / PATCH_REQUIRED / BLOCKED

BASE_SHA=

SCOPE_CORRECTION_SHA=
ENGINE_REPAIR_SHA=
O7E_RP1_POLICY_FREEZE_SHA=

O7E_RP1_GENERAL_HOLDOUT_CASE_UNIVERSE_HASH=

HEAD_SHA=
REMOTE_SHA=

TARGET_AGENT=general

PHILOSOPHER_AGENT_O7E_DIFF=
PHILOSOPHER_AGENT_SCHOLARLY_POLICY_INJECTION=

GENERAL_SCHOLARLY_CONTRACT_HASH_BEFORE=
GENERAL_SCHOLARLY_CONTRACT_HASH_AFTER=

HARD_RETRIEVAL_BUDGET=
HARD_TOTAL_BUDGET=
BUDGET_INCREASED=

CALIBRATION_CASES=
CALIBRATION_PUBLICATIONS=

HOLDOUT_CASES=
FINAL_PUBLICATIONS=
FINAL_PUBLICATION_RATE=

VALIDATION_FAILURES=
REPAIR_ATTEMPTS=
REPAIR_SUCCESS=
REPAIR_EXHAUSTIONS=

REPAIR_ATTEMPT_ACCOUNTING_DELTA=
VALIDATION_FAILURE_ACCOUNTING_DELTA=

EMPTY_FINAL_AFTER_REPAIR=
TERMINAL_PENDING=
TOOL_LOOP_ABORTS=

APPLICABLE_DIMENSION_MEAN=

TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=

FATAL_FLAGS=

GENERAL_TOOL_COUNT_BEFORE=
GENERAL_TOOL_COUNT_AFTER=

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7D_REGISTRY_SHA=
29c50cdb577c024fa2a29dcf1b2255aeb7bbf8404458521b4d1c2055e5a9d319

O7D_EVIDENCE_SHA=
f6c7bfcaae1f308540f4afb05478e8ade850302c1b303342c264a5ac392cb291

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7_E_FINAL_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP

这轮我的核心判断就是：

先不要怪 Main Agent 不会修答案。当前系统存在一种“Agent 已经研究很多 → repair 正好撞 hard ceiling → runtime 把 repair 候选清空”的机械失败路径。

先把这个杀掉。

然后我们再看真正剩下的是多少“学术表达问题”。

另外，哲学家 Agent 从这里正式退出我的 O7-E 审查范围。之后我只审通用 PhiAgent；哲学家 Agent 按你自己的设计路线走。