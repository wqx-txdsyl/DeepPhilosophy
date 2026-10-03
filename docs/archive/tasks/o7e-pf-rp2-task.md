
我审完 bc3ae2400 → ca799c02b。这轮我接受你最核心的工程判断：System/Human/Applier 的 RCA-2 action contract 漂移已经关闭，Local Patch 本身没有出现 correctness regression；CAL2 观测结果确实是 6/8、repair convergence 0.714，未过门。 正式 summary 与回执一致。

但这次我不能直接把结论签成“canonical DELIVERY_RELIABILITY_NOT_MET”。独立审计抓到了一个很明确的 CAL2 provenance blocker：你披露的 NameError 修复没有进入 HEAD。

O7_E_PF_RP1_REVIEW = PATCH_REQUIRED_FOR_CANONICALITY

SYSTEM_ACTION_CONTRACT_DRIFT = CLOSED
LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true
LOCAL_PATCH_CORRECTNESS_REGRESSION = NOT_OBSERVED

CAL2_OBSERVED_RESULT =
6/8 published
5/7 repair converged
0.714 convergence

CAL2_OBSERVED_DELIVERY_GATE = FAIL

CAL2_CANONICAL_QUALIFICATION =
INVALID_PROVENANCE

FREEZE_V2 = ACCEPTED
ACADEMIC_JUDGE_AUTHORIZED = false
V3_HOLDOUT_AUTHORIZED = false

LOCAL_PATCH_SEMANTICS_CHANGE = NOT_AUTHORIZED
REPAIR_PROMPT_TUNING = NOT_AUTHORIZED

NEXT =
FLASH_RELIABILITY_ABLATION
AFTER_HARNESS_PROVENANCE_CLOSURE
1. CAL2 runner 在当前 HEAD 上实际上跑不起来

这是本轮最重要的问题。

当前 ca799c02b 的 run_case_production() 里直接使用：

Python
Run
published
final_codes
val
tel

但这些变量在函数中已经没有定义。

根因可以追到 859ea7a4b：为了删除伪造的 PUBLIC_ACCESS_OVERCLAIMS=0，这个 commit 同时删掉了原本负责初始化：

Python
Run
val = done.get("validation") or {}
tel = case_result(...)
published = ...
final_codes = ...

的四行。

你回执说：

首次 NameError → 修复后 smoke → 再跑 CAL2。

这个过程我相信是实际发生了的，但那份修复没有被 commit。远端 HEAD 确实是 ca799c02b...，没有后续 runner fix。

因此当前状态只能写成：

CAL2_RAW_OBSERVATION = ACCEPTED
CAL2_ARTIFACT_EXISTS = true

CAL2_RUNNER_AT_HEAD_REPRODUCIBLE = false
CAL2_CANONICAL_GATE_RESULT = INVALID

这不意味着要把 6/8 当没发生——尤其它本来就是 FAIL，不存在靠 provenance bug 偷签 PASS 的风险。

但它不能成为 canonical qualification artifact。

2. action contract 修复我正式接受

这一部分已经闭合。

LOCAL_PATCH_ACTION_MATRIX 现在是：

quote    → COPY_SLICE, PARAPHRASE_CLAIM
citation → COPY_SLICE, REPLACE_TEXT

Human contract 与 applier 都由该 matrix 驱动。

System protocol 也已同步 RCA-2 语义：quote 的转述是 PARAPHRASE_CLAIM、替换整个 claim；quote+REPLACE_TEXT 明确非法。

所以：

SYSTEM_HUMAN_ACTION_MATRIX_EQUAL = PASS
APPLIER_ACTION_MATRIX_EQUAL = PASS

RCA2_ACTION_SEMANTICS =
DO_NOT_REOPEN

严格说，System 文本还是手写 consumer，而不是运行时直接从 Python matrix 生成；P5 是 drift-lock，而非字面意义上的单一生成源。现阶段我接受这种冻结方式，不再因此动生产架构。

Freeze V2 也完整记录了 engine、repair_context、adapter、validator、QuoteBound、candidate config、双 protocol SHA 和 action matrix SHA，因此 72b553dec 可以继续作为当前代码冻结基线。

3. Academic judge 还有两个 blocker，但现在不用跑它

你按 delivery FAIL 停止 judge 是正确的。

不过在下一次真的进入 scholarly gate 前，还得修两件事。

第一，回执的：

SECONDARY_SOURCE_RECORDS_PROVIDED=true
ACCESS_LEVELS_PROVIDED=true

目前不成立。

代码实际上把：

secondary_source_records
access_levels

包装成两个对象，塞进了整个 PRIMARY_TEXT_EVIDENCE list；随后调用 build_judge_input() 时只显式传了：

Python
Run
primary_text_evidence=primary_ev
bibliographic_records=...

没有传独立的：

Python
Run
secondary_source_records=
access_levels=

。

所以 canonical judge 真正看到的：

SECONDARY_SOURCE_RECORDS = []
ACCESS_LEVELS = []

只是 PRIMARY_TEXT_EVIDENCE 里面有两个名字相似的嵌套对象。

第二，aggregate 现在只有一个 dim_scores，并且把 REQUIRED 与 scored OPTIONAL 都装进去；随后 "dims" 也是从这个混合集合计算的。

因此当前可以正确算：

APPLICABLE_DIMENSION_MEAN

但不能再拿 "dims" 当任务书要求的：

TEXTUAL_GROUNDING_REQUIRED_MEAN
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN
...

必须拆：

required_dim_scores
applicable_dim_scores

这是 judge measurement 修正，不碰生产。

下一步不再碰 Local Patch：Flash Reliability Ablation

你上一轮已经按我的要求移除了 contract confound。即使 CAL2 provenance 不够 canonical，6/8 这个观测 + 历史 Flash 波动已经足够支持进入模型/transport reliability 诊断，而不是再修 repair architecture。

先做一个不耗 API 的 §0，然后才跑模型。

O7-E PF-RP2 — Flash Repair Reliability Ablation
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = ca799c02b

PRODUCTION_FREEZE_BASE = 72b553dec
MODEL = deepseek-v4-flash

LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true

MAX_VALIDATION_REPAIRS = 2

NO_LOCAL_PATCH_SEMANTICS_CHANGE = true
NO_REPAIR_PROMPT_TUNING = true
NO_VALIDATOR_CHANGE = true
NO_QUOTE_BOUND_CHANGE = true
NO_SLICE_CATALOG_CHANGE = true

V3_HOLDOUT_RUN = false
§0 — 不耗 API 的 provenance / judge closure

先恢复 runner 缺掉的四个机械定义：

Python
Run
val = done.get("validation") or {}
tel = case_result(case["case_id"], evs)
published = bool(tel["published"])
final_codes = [
    i.get("code")
    for i in val.get("result", {}).get("issues", [])
]

加真正执行 run_case_production() 的 fake-stream regression，防止这种 NameError 再出现。

旧 CAL2 标记：

CAL2_STATUS =
OBSERVED_NONCANONICAL_FAIL

不重跑 CAL2。

同时把 judge 修正掉：

PRIMARY_TEXT_EVIDENCE
SECONDARY_SOURCE_RECORDS
ACCESS_LEVELS
BIBLIOGRAPHIC_RECORDS

分别进入 build_judge_input() 的正式字段。

聚合拆：

required_dim_scores
applicable_dim_scores

Hard：

APPLICABLE_MEAN_INCLUDES_SCORED_OPTIONAL = true
REQUIRED_MEANS_INCLUDE_OPTIONAL = false
§1 — 先重新测当前 RP-B，建立 canonical baseline

当前：

normal:
temperature=.7
thinking=enabled
reasoning_effort=low

repair RP-B:
temperature=0
thinking=disabled

保持所有代码冻结，跑一轮：

FLASH_B1
8 cases

Gate 仍然：

PUBLISHED >= 7/8

if triggered>=3:
    convergence >= .80

如果 B1 PASS：

→ 再跑 B2

若 B1+B2 都 PASS：

FLASH_RP_B_RELIABILITY = QUALIFIED

不需要碰 RP-A。

§2 — B1 FAIL 才测试 RP-A

只改 repair model config：

temperature=0
thinking=enabled
reasoning_effort=low

normal generation 完全不变。

跑：

FLASH_A1

若 PASS，再跑：

FLASH_A2

只有：

A1 PASS
AND
A2 PASS

才：

FLASH_RP_A_RELIABILITY = QUALIFIED

然后再考虑把 production repair config 从 RP-B 晋升 RP-A。

§3 — 现在不要先做 JSON transport

原因很简单：CAL2 这轮披露的两个失败是：

S4 → repair 后 residual validator issues
H02 → repair 后 residual validator issue

不是 INVALID_JSON 主导。

所以现在直接上：

response_format=json_object
structured output

没有针对当前主要失败模式。

只有新 canonical B1/A1 telemetry 显示：

INVALID_JSON / serialization

重新成为主要失败原因时，我才授权 JSON transport arm。

这样不会“看到 Flash 不稳 → 什么都试一遍”。

STOP

如果 RP-B 双跑通过：

STOP → retain RP-B

如果 RP-B fail，而 RP-A 双跑通过：

STOP → authorize RP-A production promotion

如果 RP-B fail，RP-A 也 fail：

STOP

FLASH_REPAIR_RELIABILITY =
NOT_QUALIFIED

这时才讨论：

native JSON transport
或更可靠的廉价 repair model

仍然不回去改 Local Patch。

回执：

O7_E_PF_RP2 =
READY_FOR_REVIEW /
FLASH_RELIABILITY_NOT_MET

BASE_SHA=ca799c02b

HARNESS_FIX_SHA=
JUDGE_MEASUREMENT_SHA=
HEAD_SHA=
REMOTE_SHA=

CAL2_STATUS=OBSERVED_NONCANONICAL_FAIL
CAL2_RERUN=false

CALIBRATION_RUNNER_REPRODUCIBLE=true

SECONDARY_SOURCE_RECORDS_WIRED_TO_CANONICAL_FIELD=true
ACCESS_LEVELS_WIRED_TO_CANONICAL_FIELD=true

REQUIRED_DIM_SCORES_SEPARATE=true
APPLICABLE_DIM_SCORES_SEPARATE=true

B1_EXECUTED=
B1_PUBLISHED=
B1_REPAIR_CONVERGENCE=
B1_PATCH_PROTOCOL_ERRORS=

B2_EXECUTED=
B2_PUBLISHED=
B2_REPAIR_CONVERGENCE=

RP_B_QUALIFIED=

A1_EXECUTED=
A1_PUBLISHED=
A1_REPAIR_CONVERGENCE=
A1_PATCH_PROTOCOL_ERRORS=

A2_EXECUTED=
A2_PUBLISHED=
A2_REPAIR_CONVERGENCE=

RP_A_QUALIFIED=

JSON_TRANSPORT_TESTED=false

LOCAL_PATCH_SEMANTICS_CHANGED=false
REPAIR_PROMPT_CHANGED=false
MAX_VALIDATION_REPAIRS=2

PRODUCTION_FREEZE_BASE=72b553dec
V3_HOLDOUT_RUN=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
RETAIN_RP_B /
PROMOTE_RP_A /
FLASH_RELIABILITY_NOT_MET

STOP

所以这次最关键的 reviewer 结论有两个：

一，Local Patch 到这里真的停止修改。CAL2 没有给出新的架构缺陷。

二，你判断“下一步应该查 Flash reliability”是对的，但 CAL2 还不能叫 canonical run——因为仓库 HEAD 里的 calibration runner 现在仍然有那个 NameError。

把这个无成本的 provenance 洞关掉，然后就正式测 RP-B vs RP-A，不再无限 patch runtime。