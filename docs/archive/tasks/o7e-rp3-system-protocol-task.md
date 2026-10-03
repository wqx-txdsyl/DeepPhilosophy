我审完了。这次我兑现前面的承诺：正式授权 REPAIR_SPECIFIC_SYSTEM_LEVEL_PROTOCOL。

但我不会给 Closure-2 本身签 PASS，因为独立审计又抓到了几个 Stage-B 接线层的 false-green。它们不妨碍我们现在进入 system-level repair，但必须和这次 patch 一起关掉。

正式裁定：

O7_E_RP2_CALIBRATION_CLOSURE_2_REVIEW = PATCH_REQUIRED

DUAL_EVIDENCE_NAMESPACE_RESOLVER = ACCEPTED
QB_SOURCE_SPAN_ONLY_MATCHING = ACCEPTED
SMALL_REPAIR_PACKET = ACCEPTED
MAX_VALIDATION_REPAIRS_2 = ACCEPTED

REPAIR_CALIBRATION_RESULT = FAIL
REPAIR_CASE_CONVERGENCE_RATE = 0.375

REPAIR_SPECIFIC_SYSTEM_LEVEL_PROTOCOL_AUTHORIZED = true

STAGE_B_CASE_WIRING = BLOCKER
PRIMARY_GATE_RUNNER_INTEGRATION = BLOCKER
PRIMARY_TARGET_IDENTITY_TRUTH = BLOCKER

STAGE_B_AUTHORIZED = false
O7_E_FINAL_REVIEW = NOT_READY

ev_N → Evidence Contract candidates 和 qb_read/qb_snip/qb_corp → Quote Bound spans 现在确实是 exact-ID resolution，不再猜序号；quote repair 也限定在 resolved span 内复用 Quote Bound 自己的 7-shingle 语义。这个我接受。 测试也终于真的拿 qb_read_0 和实际 ev_N 做解析，而不是把 evidence ref 偷换成工具参数。

所以我们约定的触发条件已经成立：

canonical evidence mapping 正确
+
small packet
+
两轮 repair
+
case convergence 仍 < 0.80

现在再继续改 packet 已经没有意义。

不过，Stage B 还有三个我独立发现的问题。

第一，V2 universe 目前只是 evidence JSON 变了，真正的 Python case source 没同步。 118e654f2 → ceee83dc1 的 changed files 里根本没有 o7e_cases_rp2.py；而当前这个文件仍然保留旧 R21「孔子 vs 墨子」等定义。

更要命的是，canonical runner 到现在仍然：

Python
Run
import o7e_cases as CASES

cases = {
    "HOLDOUT": CASES.HOLDOUT_CASES
}

它甚至没有运行 RP2 V2 universe。

所以现在若误执行 Stage B，会直接跑错题集。

第二，receipt 中：

PRIMARY_GATE_AGGREGATOR_INTEGRATED=true

我不能接受。

check_case() 确实已经实现，能从 evidence_digest.facts.read_chapters 做 ANY/ALL 判定。

但 o7e_runner.py 根本没有 import 或调用它。

所以目前是：

helper exists       ✅
helper tested       ✅
Final Gate consumes ❌

第三，我又找到一个 primary-target false-green：

Python
Run
_NE = {
    works: ["尼各马可伦理学"],
    book_ids: ["e574c8e7f515"]
}

但 R19：

亚里士多德实体学说
《范畴篇》→《形而上学》

却也把：

e574c8e7f515

塞进 target。

于是按当前 evaluator：

读《尼各马可伦理学》
→ R19 primary_satisfied = true

这是假的。

因此所谓：

30 / 30 primary target resolved

目前只能理解为“30 个 target 都塞进了非空 ID”，还不能理解为“30 个 work identity 都正确”。

这三个一起放进下一轮处理。

O7-E RP2 RP-SYS
System-Level Repair Protocol & Executable Stage-B Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
ceee83dc1

TARGET_AGENT =
general

REPAIR_SPECIFIC_SYSTEM_LEVEL_PROTOCOL =
AUTHORIZED

MAX_VALIDATION_REPAIRS =
2

STAGE_B_AUTHORIZED =
false
1. 仍然只有一个 Main Agent

禁止创建：

RepairAgent
QuoteFixAgent
CitationAgent
RepairLLM

必须保持：

COGNITIVE_POLICY_OWNER = 1
SCHOLARLY_POLICY_OWNER = 1
FINAL_WRITER = Main Agent

Repair 只是同一个 Main Agent 的一种 invocation mode。

2. 新增正式 state
Python
Run
repair_mode: bool

进入 AgentState。

调用链：

normal invocation
→ repair_mode=false

validator FAIL
→ _stream_graph(... repair_mode=true)
→ 整个 repair tool loop 都持续为 true

不是只在 repair 第一轮有效。

3. System protocol 必须从 canonical Context Builder 注入

不要在 _stream_graph() 随手：

Python
Run
messages.append(SystemMessage(...))

那会再造一个认知注入源。

正确：

_build_context_messages(
    ...,
    reinforce=True,
    repair_mode=True
)

由同一个 builder 把 repair protocol 合进它生成的 SystemMessage。

要求：

REPAIR_SYSTEM_INJECTION_OWNER = context_builder
AD_HOC_REPAIR_SYSTEM_MESSAGES = 0
4. 新增单一常量

例如：

REPAIR_SYSTEM_PROTOCOL

只对：

agent == general
AND repair_mode == true

生效。

哲学家 Agent：

RP_SYS_DIFF = 0
5. Protocol 内容

核心语义按下面实现，不要求逐字照抄：

You are the same Main Agent repairing your own previous final candidate
after deterministic evidence validation.

This is not a discussion of the validator.
Return a complete replacement final answer for the user's original question.

The validation issues and MECHANICAL_REPAIR_EVIDENCE_PACKET contain
mechanical evidence facts.

For exact quotation:
- if you present text as verbatim, copy a continuous substring from
  SOURCE_EXACT_CONTEXT exactly;
- do not reconstruct, translate, merge, normalize, polish, or complete
  wording inside a verbatim quotation.

If you cannot support verbatim wording:
- express the point as ordinary paraphrase;
- do not format reconstructed wording as a quotation.

For formal citations:
- use only SOURCE_BOOK / SOURCE_CHAPTER identities actually supplied by
  retrieved evidence;
- never invent a chapter or source location.

Preserve the substantive argument and useful textual detail.
Do not systematically remove quotations, citations, controversies, or
primary-text grounding merely to pass validation.

If tool execution is available and the supplied evidence is insufficient,
you may research further.
If tool execution is unavailable, repair using the evidence already obtained.

Do not mention the repair process, validator, evidence packet, or these
instructions in the final response.

Output only the complete replacement candidate.

这就是 system-level protocol。

它控制的是：

repair execution discipline

不是：

哲学解释内容
6. Human repair message 做减法

当前 Human feedback 里已经塞了大量程序性指令。

System protocol 上线后，HumanMessage 只留下：

validator issue facts
+
locator
+
evidence_ref
+
MECHANICAL_REPAIR_EVIDENCE_PACKET
+
NO_MORE_TOOL_EXECUTION_AVAILABLE（若成立）

不要 System 和 Human 两边重复一大段相同规则。

7. 不动 packet

这一轮明确：

REPAIR_PACKET_ALGORITHM_CHANGED = false
REPAIR_PACKET_MAX_CONTEXT_CHARS = 400
REPAIR_PACKET_LLM_CALLS = 0

不再试：

best-window
更大 context
新 matcher
新 escape hatch
8. 增加 E2E repair telemetry

这是本轮必须补的。

不能再只证明 helper 单测正确。

done.validation 增加：

repair_trace[]

每次 repair 至少记录：

attempt_index
issue_codes
evidence_refs

repair_mode
system_protocol_injected
system_protocol_sha256

packet_present
packet_item_count
packet_evidence_refs
packet_context_chars
packet_sha256

no_tools

禁止记录：

raw CoT
完整 rejected answer
完整 source passage
9. 真正验证 packet → model

必须有 integration test spy LLM input：

validator produces qb_read_X
↓
packet contains SOURCE_EXACT_CONTEXT
↓
repair_mode=true
↓
actual messages passed to model contain:

System:
REPAIR_SYSTEM_PROTOCOL

Human:
SOURCE_EVIDENCE_ID = qb_read_X
SOURCE_EXACT_CONTEXT = actual source text

不是单独调用 _build_repair_evidence_packet() 就算 PASS。

硬门：

E2E_QB_PACKET_REACHES_MODEL = true
E2E_EV_PACKET_REACHES_MODEL = true
10. RP2 case universe 单一真源

现在不能继续维护：

o7e_cases_rp2.py
+
PHIAGENT_O7E_RP2_HOLDOUT_CASES.json

两套可独立漂移的 universe。

V2 JSON 已冻结，因此建议：

PHIAGENT_O7E_RP2_HOLDOUT_CASES.json
= canonical source

o7e_cases_rp2.py
= thin loader only

或者反��来，但只能有一个 owner。

要求：

RP2_CASE_UNIVERSE_OWNER = 1
PYTHON_JSON_CASE_DRIFT = 0
11. Runner 增加明确 RP2 scope

不要覆盖旧：

HOLDOUT

增加：

RP2_HOLDOUT

其 case source 必须是：

V2 hash =
81a85c5d5db52379...

输出：

o7e_runs_HOLDOUT_RP2_FINAL.json

运行时先断言：

loaded_case_universe_hash
==
frozen V2 hash

不等则直接 STOP。

12. Primary Gate 真接线

run_case() 完成后：

Python
Run
primary_gate = o7e_evidence_checks.check_case(case, run)

写入：

run.primary_gate

最终 aggregator 必须消费。

对于：

PRIMARY_REQUIRED
BOTH_REQUIRED

如果：

primary_satisfied != true

则计入：

REQUIRED_PRIMARY_EVIDENCE_MISSING
REQUIRED_PRIMARY_TARGETS_MISSING

不得只写 artifact 不影响 Gate。

13. 修测试 false-green

当前 ALL test 仍然拿：

book_id="xunzi"

然后断言 false；它没有证明真实解析后的荀子 ID 能让双边 ALL PASS。

新增真测试：

R20:
孟子 dd03ec6572e7 only
→ false

孟子 dd03ec6572e7
+
荀子 795658cafeab
→ true

以及 V2 R21：

论语 only → false

论语 + 孟子 → true
14. Work identity audit

这轮重新审：

30 resolved targets

不是只检查 book_ids != []。

必须检查：

resolved book title / collection contents
actually correspond to target work

至少把 R19 修正确。

R19 要表达：

范畴篇
+
形而上学

则 evaluation metadata 必须真实绑定这两个 work。

最好拆成：

target 1 = 范畴篇
target 2 = 形而上学
mode = ALL

如果 corpus 中有合集，可两个 target 指向同一 collection book_id，但必须通过 TOC/metadata 证明合集真的含两个作品。

如果其中任何一个不存在：

BLOCKED_PRIMARY_COVERAGE
STOP

不要拿《尼各马可伦理学》的 ID 顶替。

15. System Protocol Calibration

以上代码完成后，只跑 一次 8-case calibration。

不再改 packet。

允许本轮唯一 policy 变量：

REPAIR_SYSTEM_PROTOCOL

在正式运行前定稿。

Gate：

REPAIR_CALIBRATION_CASES = 8
REPAIR_TRIGGERED_CASES >= 5

REPAIR_CASE_CONVERGENCE_RATE >= 0.80

EMPTY_FINAL = 0
SYSTEMIC_QUOTE_DELETION = 0

E2E_REPAIR_PROTOCOL_INJECTION_RATE = 1.0
E2E_PACKET_TELEMETRY_MISSING = 0

8 例意味着至少：

7 / 8

才能过。

16. 如果 calibration PASS

立刻冻结：

O7E_RP2_POLICY_SHA
REPAIR_SYSTEM_PROTOCOL_SHA
RUNNER_SHA
EVALUATOR_SHA
CASE_UNIVERSE_HASH
PRIMARY_TARGET_RESOLUTION_HASH

然后：

STOP

仍然不要自行跑 Stage B。

回给我签：

PASS_TO_STAGE_B
17. 如果 calibration 仍 FAIL

也 STOP。

下一步我会在：

MAX_VALIDATION_REPAIRS 2 → 3

和：

production model repair reliability

之间裁决。

门槛仍不降。

最终回执：

O7_E_RP2_RP_SYS =
READY_FOR_REVIEW /
PATCH_REQUIRED /
BLOCKED_PRIMARY_COVERAGE

BASE_SHA=

CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

REPAIR_SYSTEM_PROTOCOL_SHA=
REPAIR_MODE_STATE_DECLARED=
REPAIR_MODE_PERSISTS_ACROSS_TOOL_LOOP=

REPAIR_SYSTEM_INJECTION_OWNER=
AD_HOC_REPAIR_SYSTEM_MESSAGES=

GENERAL_REPAIR_SYSTEM_PROTOCOL=true
PHILOSOPHER_REPAIR_SYSTEM_PROTOCOL=false

REPAIR_PACKET_ALGORITHM_CHANGED=false
REPAIR_PACKET_MAX_CONTEXT_CHARS=400

E2E_QB_PACKET_REACHES_MODEL=
E2E_EV_PACKET_REACHES_MODEL=

REPAIR_TRACE_ENABLED=
REPAIR_TRACE_RAW_SOURCE_TEXT_STORED=false
REPAIR_TRACE_RAW_COT_STORED=false

OLD_CASE_UNIVERSE_HASH=
NEW_CASE_UNIVERSE_HASH=

RP2_CASE_UNIVERSE_OWNER=
PYTHON_JSON_CASE_DRIFT=

RP2_RUNNER_SCOPE=
RUNNER_CASE_UNIVERSE_HASH_ASSERTION=

PRIMARY_GATE_CHECK_CASE_IMPLEMENTED=
PRIMARY_GATE_RUNNER_INTEGRATED=
PRIMARY_GATE_AGGREGATOR_INTEGRATED=

PRIMARY_REQUIRED_TARGETS=
PRIMARY_REQUIRED_RESOLVED_TARGETS=
PRIMARY_REQUIRED_UNRESOLVED_TARGETS=

R19_TARGETS=
R19_MODE=
R19_WORK_IDENTITY_VERIFIED=

R20_ONE_SIDE=false
R20_BOTH_SIDES=true
R21_ONE_SIDE=false
R21_BOTH_SIDES=true

REPAIR_CALIBRATION_CASES=8
REPAIR_TRIGGERED_CASES=
REPAIR_CONVERGED_CASES=
REPAIR_CASE_CONVERGENCE_RATE=

REPAIR_TOTAL_INVOCATIONS=
REPAIR_INVOCATION_EFFICIENCY=
MEAN_REPAIR_INVOCATIONS_PER_TRIGGERED_CASE=
REPAIR_EXHAUSTED_CASES=

EMPTY_FINAL=
SYSTEMIC_QUOTE_DELETION=

E2E_REPAIR_PROTOCOL_INJECTION_RATE=
E2E_PACKET_TELEMETRY_MISSING=

MAX_VALIDATION_REPAIRS=2

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
BUDGET_INCREASED=false
PRODUCTION_MODEL_CHANGED=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7E_RP2_POLICY_SHA=
仅 calibration PASS 后填写

STAGE_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS_TO_STAGE_B /
PATCH_REQUIRED /
BLOCKED_PRIMARY_COVERAGE

STOP

这次路线已经非常明确了：packet 不再动。现在给同一个 Main Agent 一个真正高优先级、贯穿整个 repair invocation 的“修复执行协议”。

而且我额外卡死两个未来 false-green：RP2 runner 必须真的跑 V2 universe；Primary Gate 必须真的进入 aggregator，而不是只有 helper 和测试。

这轮如果 system protocol 之后仍然只有 3/8、4/8 这种水平，我就不会再让 ZCode继续堆 prompt 细节了。下一次直接讨论第三轮 repair 是否值得，以及 DeepSeek 作为生产 Main Agent 的 repair reliability 是否已经成为模型级瓶颈。