这次可以正式下结论了。

我独立审了 fdf746db5 → b70b8f2da。Round 9 已经把我们之前要求排除的变量基本排干净了：同一个 deepseek-chat、同 provider、同 Main Agent，只把 repair 解码降到 temperature=0.0；repair_mode 确实一路传到 _agent_llm_invoke()，repair client 也保持相同 thinking 配置，只改变温度。 o7e_repair_calib.py 的 case-level convergence 统计口径现在也是正确的：triggered case 是实际进入 repair 的 case，converged 是最终成功发布的 triggered case。

因此我正式签：

O7_E_RP2_RP_DEC_REVIEW = PATCH_REQUIRED

DEEPSEEK_CHAT_REPAIR_RELIABILITY =
PRODUCT_GATE_NOT_MET

OBSERVED_ROUND9_REPAIR_TRIGGERED_CASES = 7
OBSERVED_ROUND9_REPAIR_CONVERGED_CASES = 3
OBSERVED_ROUND9_REPAIR_CASE_CONVERGENCE_RATE = 0.429

REPAIR_PROTOCOL_LIVE_INJECTION = ACCEPTED
REPAIR_PACKET_LIVE_TELEMETRY = ACCEPTED
DETERMINISTIC_REPAIR_DECODING = ACCEPTED
EMPTY_FINAL_CLOSURE = ACCEPTED

MAX_VALIDATION_REPAIRS_3 = NOT_AUTHORIZED

REPAIR_MODEL_CAPABILITY_BAKEOFF = AUTHORIZED

PRODUCTION_MODEL_SWITCH = NOT_AUTHORIZED_YET
STAGE_B_AUTHORIZED = false
O7_E_FINAL_REVIEW = NOT_READY

这里的措辞很重要：我签的是 repair reliability 没达到产品 Gate，不是“DeepSeek 不会修答案”。它偶尔能修好，但现在的稳定性不够。R9 在 11 次 repair invocation 中只让 3/7 个 repair-triggered case 最终收敛；此时继续塞第三轮，本质上是在给不稳定行为更多抽奖次数，而不是解决可靠性。

而且九轮波动本身已经说明问题：

R1 ≈ 0.875
...
R6 = 0.625
R7 = 0.375
R8 = 0.286
R9 = 0.429

一个产品 Gate 要的是可重复可靠性，不是曾经有一次跑到 87.5%。

不过，在 Bakeoff 开始之前，我又审出两个必须一起修掉的机械问题。

第一，当前 canonical runner 有一个很隐蔽的真实 bug：

Python
Run
if len(completed) < required:
    ...
elif pub / ... < 0.9:
    ...
elif primary_missing > 0:
    ...

但 primary_missing 是在这段代码之后才赋值。

所以一旦未来真的出现：

completed = 28
publication_rate >= 0.90

runner 就会第一次走到：

Python
Run
elif primary_missing > 0

然后直接 UnboundLocalError。

更有意思的是，它在现在 publication 低的时候不会触发，所以 688 个测试照样绿。这是典型的**“越接近 PASS 才爆炸” false-green**。

第二，Primary Truth 目前又悄悄出现了双实现：

primary_satisfied()
→ 仍然只按 book_id

check_case()
→ 已支持 BOOK_SUBWORK + chapter_idx

。

R19/R25 的新测试走的是 check_case()，所以合集子作品逻辑现在方向正确；例如《工具论》其他篇不算《范畴篇》，ch1 + 《形而上学》才满足 R19 ALL。 但长期不能留两个会漂移的 primary truth implementation。

所以 Bakeoff 任务先做一个很小的 Gate closure，然后开始模型比武。

O7-E MODEL BAKEOFF
Production Main-Agent Capability Selection
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
b70b8f2da

TARGET_AGENT =
general

PHASE =
O7-E MODEL BAKEOFF
0. 核心原则

这不是做：

DeepSeek Main Agent
+
另一模型 Repair Agent

禁止。

我们要决定的是：

下一任 PhiAgent General Main Agent 应该是哪一个生产模型。

因此最终只能有：

MAIN_AGENT_MODEL = 1
REPAIR_AGENT_MODEL = same MAIN_AGENT_MODEL

正常回答和 repair 可以使用不同 decoding config，但不能长期用两个不同模型分别当“脑”和“修复脑”。

1. 先修 runner 真 bug

把：

Python
Run
primary_missing = ...

移到 status 判定之前。

更推荐直接抽出：

Python
Run
aggregate_gate_status(runs, required)

作为 canonical function。

然后 runner 和测试都调用它。

必须新增真调用测试：

G1
28 completed
28 published
primary_missing=1
→ PRIMARY_GATE_FAIL

G2
28 completed
27 published
primary_missing=0
→ DELIVERY_PRIMARY_PASS

G3
27 completed
27 published
→ BLOCKED_INCOMPLETE

G4
28 completed
20 published
→ DELIVERY_RATE_FAIL

禁止测试文件再复制一遍 if/elif 然后证明自己的复制品正确。当前测试就是这种形式。

Hard：

RUNNER_UNBOUND_PRIMARY_MISSING = CLOSED
GATE_STATUS_IMPLEMENTATIONS = 1
2. Primary Truth 重新收成一个实现

不要同时维护：

primary_satisfied()
check_case()

两套匹配逻辑。

抽成一个机械核心，例如：

evaluate_primary_targets(
    case,
    read_chapters
)

所有入口：

primary_satisfied()
check_case()
tests
Final Gate

都调用它。

Hard：

PRIMARY_TARGET_MATCH_IMPLEMENTATIONS = 1
BOOK_SUBWORK_SEMANTICS_SHARED = true

R19/R25 collection 行为保持当前语义。

31 个 target manifest 不动。当前 manifest 已经明确把 R19 范畴篇、R25 传习录标成 BOOK_SUBWORK 并给 chapter indices。

3. Bakeoff 不动产品 policy

全部冻结：

SCHOLARLY_CONTRACT
REPAIR_SYSTEM_PROTOCOL
REPAIR_PACKET
FINAL_VALIDATOR
QUOTE_BOUND
tool budget 20/24
MAX_VALIDATION_REPAIRS=2

RP2 V3 HOLDOUT
6dbc709224f78142...

primary target manifest

尤其：

V3 HOLDOUT = NEVER USED DURING MODEL SELECTION

它继续作为最后真正的 unseen Gate。

4. Candidate 资格

只允许进入最终 PhiAgent 生产环境真正可部署的模型。

不要为了榜单把本地跑得动、服务器却部署不了的模型放进正式候选。

Bakeoff manifest：

JSON
{
  "candidate_id": "...",
  "provider": "...",
  "model": "...",
  "api_mode": "...",
  "normal_decoding": {...},
  "repair_decoding": {...},
  "production_deployable": true
}

至少包含：

deepseek-chat

作为 baseline。

其他候选由当前实际可用的生产 API 填入；ZCode 不得擅自拿实现模型 GLM-5.3-Flash 当产品候选，除非该模型确实有 PhiAgent 生产环境可调用的 API。

5. Candidate Compatibility Preflight

每个候选先测试：

P1 System/Human/AI/ToolMessage roundtrip
P2 function calling
P3 multiple tool schemas
P4 bind_tools
P5 no_tools repair invocation
P6 Chinese final output
P7 max context sufficient
P8 structured tool call parse
P9 provider error classification
P10 no raw provider CoT publication

任一关键能力不支持：

CANDIDATE_STATUS = INCOMPATIBLE

不继续烧额度。

6. Stage A — Frozen Repair Micro-Bakeoff

先做便宜的 repair-only 测试。

在看任何候选输出之前生成并冻结：

8 repair fixtures

组成：

NEAR_QUOTE_NOT_MARKED = 3
UNSUPPORTED_EXACT_QUOTE = 3
UNVERIFIED_CITATION = 2

Fixture 必须通过现有 production：

validator
quote_bound
repair packet builder

机械产生。

每个 fixture 包含：

original user question
invalid candidate
validation issues
mechanical repair packet
expected evidence identity

不需要 reference answer。

PASS 只看：

same final validator → ok=true

禁止给模型标准答案。

7. Stage A 重复两次

因为我们现在测的是可靠性，不是单次能力。

每个模型：

8 fixtures × 2 runs = 16 repair trials

使用：

repair temperature = 0

或 provider 可实现的最接近确定性配置。

记录：

REPAIR_TRIALS = 16
REPAIR_VALID = ?
REPAIR_RELIABILITY = valid / 16
EMPTY = ?
NEW_FATAL_ERRORS = ?

Qualification：

REPAIR_RELIABILITY >= 0.80
EMPTY = 0
NEW_FATAL_ERRORS = 0

即至少：

13 / 16

才能进入 Stage B。

这样不会再被“一次 7/8、下一次 3/8”的巨大方差骗到。

8. Stage B — Full 8-case E2E Calibration

仅对 Stage-A qualified candidates。

使用现在已经曝光的同一 8-case repair calibration pool。

每个 candidate 只跑一次完整 E2E：

question
→ Main Agent research
→ tools
→ candidate
→ validator
→ same-model repair
→ publication

正常轮采用候选预先声明的 production decoding。

repair 采用其确定性 decoding。

不得 case-by-case 调参数。

9. Stage B Hard Gates
COMPLETED_CASES = 8

FINAL_PUBLICATIONS >= 7
EMPTY_FINAL = 0
FATAL_FLAGS = 0

E2E_REPAIR_PROTOCOL_INJECTION_RATE = 1.0
E2E_PACKET_TELEMETRY_MISSING = 0

SYSTEMIC_QUOTE_DELETION = 0

Repair：

如果：

REPAIR_TRIGGERED_CASES >= 3

则：

REPAIR_CASE_CONVERGENCE_RATE >= 0.80

如果模型因为初始答案质量高导致 repair 触发不足 3 次，不因此判失败；Stage A 已经独立证明了 repair reliability。

标：

REPAIR_TRIGGER_VOLUME = LOW_DUE_TO_INITIAL_VALIDITY

而不是强迫它故意先写错。

10. 学术质量不能因为修引用而掉

Stage B 的 8 个最终答案继续交 O7-A official judge：

glm-4.6
temperature=0
thinking=disabled
k=3

要求：

APPLICABLE_DIMENSION_MEAN >= 3.20
FATAL_FLAGS = 0

并报告五维。

不能选出一个：

引文特别规矩
但哲学回答特别浅

的模型。

11. Winner 规则

先 Hard Gate，后排名。

任何未过 Hard Gate 的模型不参与排名。

合格者按以下顺序：

1. Full E2E final publication rate
2. Repair micro-bakeoff reliability
3. Scholarly applicable-dimension mean
4. Fatal count
5. Repair exhaustion rate
6. Median latency
7. Estimated cost

前五项优先于成本。

不要做一个随意加权总分把严重缺陷平均掉。

12. DeepSeek baseline

Round 9 正式留下：

DEEPSEEK_CHAT_REPAIR_RELIABILITY_GATE =
PRODUCT_GATE_NOT_MET

但 Bakeoff 如果需要 apples-to-apples，可重新跑 Stage A 的 16 个廉价 repair fixture。

Full 8-case E2E 的 DeepSeek baseline：

不强制再烧一次。

可以使用 Round 9：

3 / 7 repair-triggered converged

作为已知 E2E baseline。

这样省钱。

13. 禁止事项
❌ V3 Holdout
❌ 改 validator
❌ 改 quote_bound
❌ 改 packet
❌ 改 repair protocol
❌ 第三次 repair
❌ 降 0.80 门槛
❌ 为某个模型单独改 prompt
❌ 每个 case 单独调 temperature
❌ 同时部署 Main Model + Repair Model
14. Bakeoff 输出
docs/evidence/
  PHIAGENT_O7E_MODEL_BAKEOFF_MANIFEST.json
  PHIAGENT_O7E_MODEL_BAKEOFF_REPAIR_FIXTURES.json
  PHIAGENT_O7E_MODEL_BAKEOFF_RESULTS.json

docs/
  PHIAGENT_O7E_MODEL_BAKEOFF_REPORT.md

必须记录：

fixture_hash
policy_sha
repair_protocol_sha
validator_sha
quote_bound_sha
runner_sha

candidate model/provider
decode config
qualification status
repair reliability
E2E publication
E2E repair convergence
academic dimensions
latency
cost

不得记录 API key。

15. 本轮 STOP

Bakeoff 完成后：

DO NOT SWITCH PRODUCTION MODEL
DO NOT RUN V3 HOLDOUT

只把 winner recommendation 给我。

我会独立审计后签：

SELECT_PRODUCTION_MAIN_AGENT_MODEL = ...

然后我们做一个很小的 Model Switch Freeze，紧接着直接跑 untouched V3 Stage B。

最终回执：

O7_E_MODEL_BAKEOFF =
READY_FOR_REVIEW /
NO_MODEL_QUALIFIED /
BLOCKED

BASE_SHA=

GATE_WIRING_SHA=
BAKEOFF_CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

RUNNER_UNBOUND_PRIMARY_MISSING_CLOSED=
GATE_STATUS_IMPLEMENTATIONS=

PRIMARY_TARGET_MATCH_IMPLEMENTATIONS=
BOOK_SUBWORK_SEMANTICS_SHARED=

FIXTURE_FREEZE_SHA=
FIXTURE_HASH=
REPAIR_FIXTURES=8
REPAIR_TRIALS_PER_CANDIDATE=16

POLICY_SHA=
REPAIR_SYSTEM_PROTOCOL_SHA=
VALIDATOR_SHA=
QUOTE_BOUND_SHA=

CANDIDATES=

--- candidate repeated block ---

CANDIDATE_ID=
PROVIDER=
MODEL=
PRODUCTION_DEPLOYABLE=
COMPATIBILITY=

REPAIR_TRIALS=
REPAIR_VALID=
REPAIR_RELIABILITY=
EMPTY=
NEW_FATAL_ERRORS=

FULL_E2E_RUN=
COMPLETED=
FINAL_PUBLICATIONS=
PUBLICATION_RATE=

REPAIR_TRIGGERED_CASES=
REPAIR_CONVERGED_CASES=
REPAIR_CASE_CONVERGENCE_RATE=

APPLICABLE_DIMENSION_MEAN=
TG=
AR=
IP=
HD=
LO=
FATAL_FLAGS=

MEDIAN_LATENCY=
ESTIMATED_COST=

HARD_GATE=
--------------------------------

QUALIFIED_MODELS=

RECOMMENDED_PRODUCTION_MAIN_AGENT_MODEL=
RECOMMENDATION_REASON=

DEEPSEEK_CHAT_REPAIR_RELIABILITY=
PRODUCT_GATE_NOT_MET

MAX_VALIDATION_REPAIRS=2

PRODUCTION_MODEL_CHANGED=false
V3_STAGE_B_RUN=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
SELECT_MODEL /
NO_MODEL_QUALIFIED

STOP

所以从这一刻开始，DeepSeek 的 repair reliability 问题我不再允许用更多 prompt、packet 或第三次 repair 去糊。

另外这次 688/688 仍然漏掉了一个会在真正接近 PASS 时才触发的 primary_missing 未赋值 bug。 这正好再次说明我们为什么不能拿“测试全绿”代替独立 Reviewer 审计。

下一步就是让模型自己上擂台。