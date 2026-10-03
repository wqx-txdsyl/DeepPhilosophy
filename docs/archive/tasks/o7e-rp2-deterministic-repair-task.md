我审完 ceee83dc1 → fdf746db5 了。

这次不再继续堆 prompt，也不授权 2→3 repair。我的裁决是：先把 DeepSeek 同一模型的 repair invocation 改成确定性解码，再跑一次。 如果这样仍低于 0.80，我就把它正式判成生产模型级 repair reliability bottleneck，直接进入模型选择，而不是加第三轮。

原因很简单：这一轮 7 个进入 repair 的 case 只有 2 个收敛。要靠第三轮直接达到 0.80，5 个 exhausted case 里至少还要有 4 个在第三次突然成功，最终达到 6/7=85.7%。而本轮 13 次 repair invocation 只产生 2 个 case convergence，没有证据支持“第三次会发生质变”。此时加一轮更像烧 token，而不是解决问题。

同时，我独立审计又抓到 3 个 Gate blocker，必须一起修掉。

Reviewer 裁定
O7_E_RP2_RP_SYS_REVIEW = PATCH_REQUIRED

REPAIR_MODE_STATE = ACCEPTED
REPAIR_SYSTEM_PROTOCOL = ACCEPTED
SYSTEM_PROTOCOL_INJECTION_OWNER = ACCEPTED
DUAL_EVIDENCE_NAMESPACE = ACCEPTED
E2E_SPY_PACKET_TO_MODEL = ACCEPTED
MAX_VALIDATION_REPAIRS_2 = RETAIN

CASE_UNIVERSE_SINGLE_SOURCE = ACCEPTED
RP2_HOLDOUT_SCOPE = ACCEPTED
R19_WORK_IDENTITY_DIRECTION = ACCEPTED

PRIMARY_GATE_HELPER = ACCEPTED
PRIMARY_GATE_AGGREGATOR = FALSE_GREEN

LIVE_REPAIR_TRACE_PERSISTENCE = BLOCKER
COLLECTION_WORK_READ_IDENTITY = BLOCKER

MAX_VALIDATION_REPAIRS_3 = NOT_AUTHORIZED
PRODUCTION_MODEL_SWITCH = NOT_AUTHORIZED_YET
REPAIR_ONLY_DETERMINISTIC_DECODING = AUTHORIZED

STAGE_B_AUTHORIZED = false

第一个 false-green 很明确：runner 现在确实计算了

Python
Run
primary_missing = ...

但 FINAL_GATE_STATUS 仍然只看：

completed count
publication rate

primary_missing 只是打印出来，完全没有参与 PASS/FAIL。所以 receipt 中的 PRIMARY_GATE_AGGREGATOR_INTEGRATED=true 我不能接受。

也就是说当前可能发生：

28/28 completed
27/28 published
PRIMARY_REQUIRED_MISSING = 8

→ FINAL_GATE_STATUS = PASS_RATE

这是明显的 Gate false-green。

第二个问题是你虽然已经把 repair_trace 放进 done.validation，记录 protocol SHA、packet refs、packet chars 等，生产 engine 这一层做得是对的。

但是 canonical o7e_runner.run_case() 没有把 validation.repair_trace 持久化进 run artifact。它只保存 delivery、citations、quote_bound、evidence_digest 等。

所以 Round 8 artifact 里，我们可以看到 H04 最终 NEAR_QUOTE_NOT_MARKED、2 repairs exhausted，却看不到两轮 repair 当时到底：

protocol_injected?
packet_present?
qb_read_X resolved?
packet_context_chars?

。

目前只能由 scripted spy 证明“代码路径可以把 packet + protocol 送到模型”，不能证明这 8 个真实 DeepSeek 校准 case 每轮实际都送到了。测试本身确实只证明了 spy path。

第三个问题是 primary work identity 还差最后一层。

现在 check_case() 只把：

book_id#chapter_idx

先降成：

book_id

然后只要 book ID 命中 target 就认为 read 成功。

对于单行本没问题，但对合集就会 false-green。

例如 R19 现在已经正确把：

范畴篇 → 工具论 b471f41a78de
形而上学 → f11f1b13c278
mode=ALL

分开了。

但如果 Agent 对 b471f41a78de 读到的是《工具论》里不是《范畴篇》的另一篇，当前 evaluator 仍然会把“范畴篇已读”判成 true。

R25 同理：

传习录
→ 王阳明全集 909e887aac01

manifest 只证明全集 TOC 中包含《传习录》，还不能证明这次实际 get_chapter 读到的就是《传习录》部分。

所以真正的 primary truth 应该是：

单作品 book
→ book_id read 足够

合集 / collection
→ book_id + target-work chapter locator

而不是仅 book_id。

O7-E RP2 RP-DEC
Repair Deterministic Decoding & Final Gate Wiring
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
fdf746db5

TARGET_AGENT =
general

PHASE =
O7-E RP2 RP-DEC
— REPAIR DETERMINISTIC DECODING
— FINAL GATE WIRING CLOSURE

核心决策：

NORMAL_MAIN_AGENT_MODEL = deepseek-chat
REPAIR_MAIN_AGENT_MODEL = deepseek-chat

NORMAL_TEMPERATURE = 0.7
REPAIR_TEMPERATURE = 0.0

MODEL_ID_CHANGED = false
MODEL_PROVIDER_CHANGED = false

MAX_VALIDATION_REPAIRS = 2

这仍然是：

same Main Agent
same model
same evidence
same tools
same scholarly policy

只是 repair 属于高度确定性的“按 evidence 修正输出”任务，所以 repair decoding 降到 0。

不要创建第二个 Repair Agent。

1. Repair-only decoding

让 _agent_llm_invoke() 正式知道：

repair_mode

调用关系：

agent_node
→ _agent_llm_invoke(
    ...,
    repair_mode=state.repair_mode
)

normal：

temperature = 0.7

repair：

temperature = 0.0

其他保持 byte/semantic identical：

AG.MODEL
AG.API_URL
API key
thinking config
max_tokens
tools

不允许：

换模型
换 provider
更高 reasoning
特殊 repair model
2. One-brain invariant

硬门：

NORMAL_MODEL_ID == REPAIR_MODEL_ID
NORMAL_PROVIDER == REPAIR_PROVIDER

REPAIR_AGENT_COUNT = 0
COGNITIVE_POLICY_OWNER = 1
FINAL_WRITER = MAIN_AGENT

允许内部存在两个 client instance/cache，只要：

model id identical
provider identical

那只是 decoding configuration，不是第二个 brain。

3. 不改任何 repair policy

这一轮冻结：

REPAIR_SYSTEM_PROTOCOL_CHANGED = false
SCHOLARLY_CONTRACT_CHANGED = false
REPAIR_PACKET_ALGORITHM_CHANGED = false

REPAIR_PACKET_MAX_CONTEXT_CHARS = 400

FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

Round 8 的 system protocol 已经足够，不再调字眼。它现在明确要求逐字引文只能连续复制 SOURCE_EXACT_CONTEXT，这一部分我接受。

4. Runner 必须持久化 repair telemetry

正式在 run_case() 保存：

repair_trace =
done.validation.repair_trace

只保存现有安全字段。

禁止增加：

raw source text
full packet text
rejected candidate
CoT
reasoning_content

Round artifact 至少可审计：

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
5. Calibration 增加真 E2E gate

从真实 8-case run artifact 计算：

E2E_REPAIR_ATTEMPTS
E2E_PROTOCOL_INJECTED_ATTEMPTS
E2E_REPAIR_PROTOCOL_INJECTION_RATE

E2E_PACKET_EXPECTED_ATTEMPTS
E2E_PACKET_PRESENT_ATTEMPTS
E2E_PACKET_TELEMETRY_MISSING

Hard：

E2E_REPAIR_PROTOCOL_INJECTION_RATE = 1.0
E2E_PACKET_TELEMETRY_MISSING = 0

这样以后不再需要从单元测试推断线上 DeepSeek 到底吃到了什么。

6. Primary aggregator 真正成为 Gate

runner 的状态计算改成等价于：

if completed < required:
    BLOCKED_INCOMPLETE

elif publication_rate < 0.90:
    DELIVERY_RATE_FAIL

elif REQUIRED_PRIMARY_MISSING > 0:
    PRIMARY_GATE_FAIL

else:
    DELIVERY_PRIMARY_PASS

不能：

PRIMARY missing
→ 只打印 diagnostic
→ PASS_RATE

新增真实 aggregator test：

28 completed
28 published
primary_missing = 1

→ MUST NOT PASS
7. Collection-work identity

Resolution manifest 增加机械字段，例如：

identity_scope =
BOOK
/
BOOK_SUBWORK

对于普通单行本：

identity_scope=BOOK
resolved_book_ids=[...]

对于合集：

identity_scope=BOOK_SUBWORK
resolved_book_id=...
resolved_chapter_indices=[...]

或等价的 deterministic chapter locator。

不得使用语义 LLM 判断。

8. R19

工具论 b471f41a78de 必须从 TOC 解析出：

《范畴篇》对应 chapter_idx set/range

然后：

read 工具论·其他篇
→ 范畴篇 target = false

read 工具论·范畴篇 chapter
→ true

《形而上学》单行本继续按 book ID。

R19 ALL 必须同时满足。

9. R25

同样给：

王阳明全集 909e887aac01

解析：

《传习录》上/中/下

所对应的 deterministic chapter indices。

于是：

读王阳明全集其他文献
→ false

读传习录 section
→ true
10. 全 31 target 做 identity audit

输出：

BOOK_SCOPE_TARGETS=
BOOK_SUBWORK_SCOPE_TARGETS=

UNRESOLVED_WORK_IDENTITIES=0

不是再只证明：

book_ids nonempty

而是证明 Gate 可以判断“这次读的就是目标作品”。

11. 只跑一次 Round 9

修完机械 Gate + repair temperature 后：

REPAIR_CALIBRATION_CASES = 8

同一旧 calibration pool。

禁止再改 protocol / packet / validator。

Hard gate：

REPAIR_TRIGGERED_CASES >= 5

REPAIR_CASE_CONVERGENCE_RATE >= 0.80
EMPTY_FINAL = 0

SYSTEMIC_QUOTE_DELETION = 0

E2E_REPAIR_PROTOCOL_INJECTION_RATE = 1.0
E2E_PACKET_TELEMETRY_MISSING = 0
12. Round 9 PASS 怎么办

如果达到：

>= 0.80

则冻结：

O7E_RP2_POLICY_SHA
REPAIR_SYSTEM_PROTOCOL_SHA
REPAIR_DECODING_CONFIG_SHA
CASE_UNIVERSE_HASH
PRIMARY_TARGET_RESOLUTION_HASH
RUNNER_SHA
EVALUATOR_SHA

然后：

STOP
STAGE_B_AUTHORIZED=false

回给我，我签 PASS_TO_STAGE_B。

13. Round 9 仍 FAIL 怎么办

如果：

repair temperature = 0
protocol live injection = 100%
packet telemetry complete
evidence mapping canonical
case convergence < 0.80

我会正式签：

DEEPSEEK_CHAT_REPAIR_RELIABILITY =
PRODUCT_GATE_NOT_MET

然后进入：

REPAIR MODEL CAPABILITY BAKEOFF

注意，不是把 Main Agent拆成两个模型长期运行。

而是先比较：

当前生产候选模型
vs
可替代生产 Main Agent 模型

谁整体更适合 PhiAgent。

我不会再优先尝试第 3 次 repair。

第三次 repair 只有一个重新授权条件：

Round 9 已明显接近 Gate
例如 5/6、6/7，
且 repair_trace 显示 issue 在两轮中持续单调缩减，
只是在第二轮耗尽时剩单个机械 issue

否则 2→3 没有产品意义。

最终回执：

O7_E_RP2_RP_DEC =
READY_FOR_REVIEW /
PATCH_REQUIRED /
BLOCKED_PRIMARY_IDENTITY

BASE_SHA=

CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

NORMAL_MODEL_ID=
REPAIR_MODEL_ID=
NORMAL_PROVIDER=
REPAIR_PROVIDER=

NORMAL_TEMPERATURE=0.7
REPAIR_TEMPERATURE=0.0

MODEL_ID_CHANGED=false
MODEL_PROVIDER_CHANGED=false

REPAIR_SYSTEM_PROTOCOL_CHANGED=false
SCHOLARLY_CONTRACT_CHANGED=false
REPAIR_PACKET_ALGORITHM_CHANGED=false

MAX_VALIDATION_REPAIRS=2

RUNNER_PERSISTS_REPAIR_TRACE=
REPAIR_TRACE_RAW_SOURCE_TEXT_STORED=false
REPAIR_TRACE_RAW_COT_STORED=false

E2E_REPAIR_ATTEMPTS=
E2E_PROTOCOL_INJECTED_ATTEMPTS=
E2E_REPAIR_PROTOCOL_INJECTION_RATE=
E2E_PACKET_EXPECTED_ATTEMPTS=
E2E_PACKET_PRESENT_ATTEMPTS=
E2E_PACKET_TELEMETRY_MISSING=

PRIMARY_GATE_STATUS_AFFECTS_FINAL_STATUS=
PRIMARY_MISSING_CAN_PASS=false

PRIMARY_REQUIRED_TARGETS=31
BOOK_SCOPE_TARGETS=
BOOK_SUBWORK_SCOPE_TARGETS=
UNRESOLVED_WORK_IDENTITIES=

R19_CATEGORIES_BOOK_ID=
R19_CATEGORIES_CHAPTER_INDICES=
R19_METAPHYSICS_BOOK_ID=
R19_OTHER_ORGANON_CHAPTER_COUNTS=false
R19_TARGET_CHAPTER_COUNTS=true

R25_COLLECTION_BOOK_ID=
R25_CHUANXILU_CHAPTER_INDICES=
R25_OTHER_COLLECTION_CHAPTER_COUNTS=false
R25_CHUANXILU_CHAPTER_COUNTS=true

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

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false
BUDGET_INCREASED=false
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
MODEL_RELIABILITY_GATE_NOT_MET

STOP

所以这次我的选择不是 (a) 2→3，也不是立刻 (b) 换生产模型。

是先做一个更干净、成本也最低的实验：

DeepSeek 仍然是 DeepSeek，但正常研究可以有随机性；validator repair 这种“照着已有证据把错误修正确”的任务，temperature 直接降到 0。

现在它的生产配置本来就是 temperature=0.7。 对开放式哲学研究这没问题，但对“一字不差复制已给出的原文”未必是合理的 repair decoding。

Round 9 如果还不行，我就不再怪 prompt、packet、第三次机会了——直接判模型。