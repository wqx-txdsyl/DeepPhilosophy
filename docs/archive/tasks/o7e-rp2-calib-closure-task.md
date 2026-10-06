我审完了。这次 Stage B STOP 是正确的，但我不同意现在直接在 (a) 加第 3 次 repair / (b) 上 repair system prompt / (c) 降门槛 / (d) 换模型 里四选一。

因为我独立审计后发现：当前“0.636 < 0.80”这个结论本身混了两种不同指标，而且 RP2 Holdout 还有一处会导致未来必败的 evaluation false-green。

正式裁定：

O7_E_RP2_CALIBRATION_REVIEW = PATCH_REQUIRED

STAGE_B_STOP_DISCIPLINE = PASS
CASE_TEXT_FREEZE_DISCIPLINE = PASS
VALIDATOR_FREEZE = PASS
QUOTE_BOUND_FREEZE = PASS
BUDGET_FREEZE = PASS
PHILOSOPHER_SCOPE_FREEZE = PASS

REPAIR_INFORMATION_SUFFICIENCY_DIAGNOSIS = PARTIALLY_ACCEPTED
MODEL_COMPLIANCE_ROOT_CAUSE = NOT_YET_PROVEN

REPAIR_SUCCESS_METRIC = INVALIDLY_MIXED
PRIMARY_TARGET_GATE_FEASIBILITY = BLOCKED
REPAIR_EVIDENCE_REF_RESOLUTION = FALSE_GREEN
PRIMARY_GATE_CANONICAL_IMPLEMENTATION = MISSING

MAX_VALIDATION_REPAIRS_3 = NOT_AUTHORIZED
REPAIR_SYSTEM_PROMPT = NOT_AUTHORIZED_YET
GATE_THRESHOLD_REDUCTION = REJECTED
PRODUCTION_MODEL_CHANGE = NOT_AUTHORIZED

O7_E_RP2_CALIBRATION_CLOSURE_AUTHORIZED = true
STAGE_B_AUTHORIZED = false

最关键的第一个问题是：你现在拿 successful cases / repair invocations 算 REPAIR_SUCCESS_RATE，量纲不对。

RP1 canonical runner 里 repair_success 本来就是case-level boolean：一次回答只要进入 repair 后最终成功发布，就是这个 case 的 repair success；repair_attempts 则是这个 case 实际用了几轮 repair。

所以像 R1：

8 个 calibration cases
7 个最终修复成功
11 次 repair invocations

应该同时得到两个指标：

REPAIR_CASE_CONVERGENCE_RATE = 7 / 8 = 87.5%

REPAIR_INVOCATION_EFFICIENCY = 7 / 11 = 63.6%

87.5% 才是在回答“这个 repair subsystem 能不能在允许的两轮内把失败答案修好”。

63.6% 回答的是：

每一次 repair invocation 有多大概率恰好成为最终成功的那一次？

第二次 repair 才成功的 case 会被后者天然罚成 1 success / 2 attempts，尽管用户最终正常拿到了答案。

我们真正关心的 hard gate 应该是：

进入 repair 的 case
→ 在 MAX_VALIDATION_REPAIRS 内最终是否收敛

而不是要求几乎每一次 repair invocation 都一次成功。

所以 R1 的 7/8 实际已经是很强的信号。后面 R2–R5 不但没改善，反而随着 packet / instruction 越堆越复杂持续恶化。

第二个问题更严重：现在冻结的 RP2 Holdout 有几道题按现有 primary gate 根本不可能通过。

例如当前冻结 universe 里：

R03 Spinoza → book_ids=[]
R11 Nietzsche → book_ids=[]
R20 Xunzi side → book_ids=[]
R21 Mozi side → book_ids=[]
R22 Mozi → book_ids=[]
R25 Wang Yangming → book_ids=[]
R28 Xunzi → book_ids=[]

而这些 case 默认仍是 PRIMARY_REQUIRED，其中 R20/R21 甚至是 mode="ALL"。

与此同时，现在所谓 primary-truth evaluator 其实只存在于 test file：

Python
Run
def _primary_satisfied(case, tool_log):
    ...
    target_ids.update(t.get("book_ids") or [])
    ...
    hits = [
        t for t in targets
        if set(t.get("book_ids") or []) & reads
    ]

也就是说 book_ids=[] 的 target 永远不可能 hit。测试自己甚至明确证明了这一点：

荀子无 book_id
→ ALL 无法命中
→ 如实 False

。

于是如果现在真跑 Stage B：

R20 / R21
→ REQUIRED_PRIMARY_TARGETS_MISSING
→ 必败

无论 Agent 多强都没用。

这不是模型问题，是 Gate universe 的机械不可满足性。

第三个问题：当前 MECHANICAL_REPAIR_EVIDENCE_PACKET 的 P1 其实也是 false-green。

生产 validator 给出的 evidence_ref 是类似：

ev_1
ev_2
...

但最初 packet builder 是拿这个 ref 去搜索 raw tool log 的 JSON/blob：

Python
Run
if ref in blob or ref in str(t.get("args", "")):

。

真实的 ev_1 是 Evidence Contract 后生成的 ID，raw tool log 里通常并不存在这个字符串。

而 P1 测试做了这个：

Python
Run
issues = [{
    "evidence_ref": "ev_1"
}]

# 然后覆盖掉
issues[0]["evidence_ref"] = "lunyu"

再断言 packet 能找到《论语》。

所以它没有证明：

真实 validator evidence_ref=ev_1
→ 能机械解析回对应 raw evidence

只证明：

如果我人工把 evidence_ref 改成工具参数里的 lunyu
→ string search 能搜到

这必须修。

后面 best_evidence=【《书》·章】 补救了一部分，但它仍不是 canonical evidence_ref → evidence record → raw source 映射。

还有一个产品判断：R5 那个“保留近似引文 + 紧跟未逐字核验声明”的第三逃生门，我建议撤掉。

现在 repair contract 明确告诉模型：

near quote 可以继续放着，只要后面说明“这是记忆/近似，未逐字核验”，validator 就允许。

Validator 允许这种披露，是一个合理的安全兜底。

但我们的 Scholarly Agent 不应该把它变成主动推荐的 repair strategy。

尤其 RP2 后面还有：

VERIFIED_EXACT_REQUIRED

anti-gaming Gate。

正确优先级应该是：

有真实原文
→ 精确复制

没有能力精确复制
→ 转述

特殊场景才：
→ 明确披露为近似回忆

不是把第三项与前两项平级。

而且 R5 数据已经证明它没有解决问题。

O7-E RP2 Calibration Closure
Gate Semantics + Evidence Mapping Repair
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
09b8b1384d9a3cac6a573a3ea515627edd9c5e7c

TARGET_AGENT =
general

STAGE_B_AUTHORIZED =
false

这轮不再调 DeepSeek，先纯代码闭环。

只做下面这一组事情：

1. 修 repair metric
2. 修 evidence_ref canonical mapping
3. 修 primary-target feasibility
4. 把 primary truth 接入 canonical evaluator
5. 回退已经证明负收益的 R2-R5 policy complexity
6. 最后只重跑一次 8-case calibration
A. 修正 Repair Gate 统计口径

正式增加：

REPAIR_TRIGGERED_CASES
REPAIR_CONVERGED_CASES
REPAIR_CASE_CONVERGENCE_RATE

REPAIR_TOTAL_INVOCATIONS
REPAIR_INVOCATION_EFFICIENCY
MEAN_REPAIR_INVOCATIONS_PER_TRIGGERED_CASE
REPAIR_EXHAUSTED_CASES

定义：

REPAIR_TRIGGERED_CASE =
initial validator result = FAIL

REPAIR_CONVERGED_CASE =
initial FAIL
AND final validation PASS
within MAX_VALIDATION_REPAIRS

REPAIR_CASE_CONVERGENCE_RATE =
REPAIR_CONVERGED_CASES
/
REPAIR_TRIGGERED_CASES

Hard calibration gate：

REPAIR_TRIGGERED_CASES >= 5
REPAIR_CASE_CONVERGENCE_RATE >= 0.80
EMPTY_FINAL = 0

而：

REPAIR_INVOCATION_EFFICIENCY

只作为 latency/cost diagnostic。

不再用：

successful_cases / total_repair_invocations

作为 PASS/FAIL。

这不是降低门槛，是修正指标定义。

B. Canonical evidence_ref resolver

不要再：

ev_1
→ 在 raw JSON 里字符串搜索

必须沿现有 Evidence Contract 真源解析。

推荐：

raw_tool_log
↓
build_evidence_pool / _extract_candidates
↓
canonical evidence_id map
↓
ev_1
↓
对应 source_id / entry_index
↓
原 raw tool result

要求：

REAL_EVIDENCE_REF_RESOLUTION_RATE = 100%

测试必须真的：

Python
Run
issue.evidence_ref = "ev_1"

禁止再偷偷改成：

Python
Run
"lunyu"

。

C. Repair Packet 做减法

数据已经很清楚：

R1 7/8
R2 5/8
R3 6/8
R4 2/8
R5 5/8

越往 packet 里塞大段 evidence，效果越差。

所以回到：

c44b2ba19

的最小思想：

offending issue
+
canonical linked evidence
+
短而精确的 source excerpt

删除/回滚后续的：

900-char best-window heuristic
“所有 「」 都是逐字通道”的过度格式说明
第三披露逃生门作为默认 repair option

尤其不能再把 900–1200 字章节块扔给 repair 模型让它自己找。

目标：

每个 issue：
OFFENDING_SPAN
SOURCE_BOOK
SOURCE_CHAPTER
SOURCE_EVIDENCE_ID
SOURCE_EXACT_CONTEXT

其中：

SOURCE_EXACT_CONTEXT <= 400 chars

优先复用 quote_bound 已有机械匹配结果。

不要另造语义 reranker。

D. Repair SystemMessage 暂不授权

仍然使用：

same Main Agent
+
canonical system prompt
+
Human repair feedback

先看修正 metric 和 packet 后能否过。

所以：

DEDICATED_REPAIR_SYSTEM_PROMPT = false

如果这一轮仍然：

CASE_CONVERGENCE < 0.80

我下一轮才考虑授权 (b)。

E. MAX_VALIDATION_REPAIRS 继续 = 2
MAX_VALIDATION_REPAIRS = 2

不改。

原因很简单：

如果当前 R1 实际是：

7 / 8 cases

在两轮内收敛，

现在没有任何依据证明需要第三轮。

增加第三轮只会：

提高延迟
提高 token 成本
掩盖 instruction / evidence mapping 问题
F. Holdout 问题文本保持永久冻结

保持：

HOLDOUT_QUESTION_UNIVERSE_HASH =
670522673bd66e92...

28 个问题文本一个字都不要动。

但新增 evaluation-only：

PHIAGENT_O7E_RP2_PRIMARY_TARGET_RESOLUTION.json

为每一个：

PRIMARY_REQUIRED

target 在 Stage B 前解析：

case_id
author
work
resolved_book_ids[]
resolution_status
source

要求：

resolution_status =
RESOLVED
/
UNAVAILABLE_IN_CORPUS
G. 不允许空 target 进入 Stage B

Hard preflight：

PRIMARY_REQUIRED_UNRESOLVED_TARGETS = 0

尤其：

R03
R11
R20
R21
R22
R25
R28

逐个解决。

如果仓库里其实有：

《伦理学》
《快乐的科学》
《荀子》
《墨子》
《传习录》

就解析到真实 book_id。

如果确实没有：

STOP。

不能：

book_ids=[]
→ 假装可以做 PRIMARY_REQUIRED

也不能为了过门临时把它改成 OPTIONAL。

需要 Reviewer 再决定是否替换 case。

H. Primary truth 必须离开测试文件

当前 _primary_satisfied() 只存在于 test suite。

必须进入：

backend/tools/evaluation/

的 canonical mechanical evaluator。

例如：

o7e_evidence_checks.py

或者并入现有 aggregator。

要求 Final Gate 真正调用它。

测试只是调用 production-evaluation helper，不得自己复制一份逻辑。

PRIMARY_TRUTH_IMPLEMENTATIONS = 1
I. ALL semantics 修正

对于：

R20 Mencius + Xunzi
R21 Confucius + Mozi

必须：

mode=ALL

两个 target 都实际：

get_chapter / verified primary-body read

才能满足。

不能：

读孟子
+
搜到荀子 snippet
→ PASS
J. 重新跑一次 Calibration

修完以上纯机械问题后：

只跑一次：

8-case repair calibration

不要再五轮连续调 prompt。

这次 policy candidate 应尽量接近：

c44b2ba19

的最简版本 + canonical evidence-ref resolver。

Gate：

REPAIR_CALIBRATION_CASES = 8

REPAIR_TRIGGERED_CASES >= 5

REPAIR_CASE_CONVERGENCE_RATE >= 0.80

EMPTY_FINAL = 0

SYSTEMIC_QUOTE_DELETION = 0

另外报告：

REPAIR_INVOCATION_EFFICIENCY
MEAN_REPAIR_INVOCATIONS_PER_TRIGGERED_CASE

但不作为 hard failure。

K. 如果这次过

才：

freeze O7E_RP2_POLICY_SHA
freeze PRIMARY_TARGET_RESOLUTION_HASH
freeze RUNNER_SHA
freeze EVALUATOR_SHA

STAGE_B_AUTHORIZED = true

然后跑那 28 个从未执行过的新 Holdout。

L. 如果还是不过

如果：

canonical evidence mapping 正确
+
small packet
+
case convergence < 0.80

那么下一步顺序是：

1. repair-specific system-level protocol
2. 再评估第三次 repair
3. 最后才考虑生产模型选择

而不是反过来。

门槛 0.80 不降。

最终回执：

O7_E_RP2_CALIBRATION_CLOSURE =
READY_FOR_REVIEW / PATCH_REQUIRED / BLOCKED_PRIMARY_COVERAGE

BASE_SHA=

CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

HOLDOUT_QUESTION_UNIVERSE_HASH=
670522673bd66e92...

HOLDOUT_QUESTION_TEXT_CHANGED=false

PRIMARY_TARGET_RESOLUTION_MANIFEST=
PRIMARY_TARGET_RESOLUTION_HASH=

PRIMARY_REQUIRED_TARGETS=
PRIMARY_REQUIRED_RESOLVED_TARGETS=
PRIMARY_REQUIRED_UNRESOLVED_TARGETS=

R03_TARGET_STATUS=
R11_TARGET_STATUS=
R20_TARGET_STATUS=
R21_TARGET_STATUS=
R22_TARGET_STATUS=
R25_TARGET_STATUS=
R28_TARGET_STATUS=

PRIMARY_TRUTH_CANONICAL_EVALUATOR=
PRIMARY_TRUTH_IMPLEMENTATIONS=

REAL_EVIDENCE_REF_TEST_VALUE=ev_1
REAL_EVIDENCE_REF_RESOLUTION=true

REPAIR_PACKET_MAX_EVIDENCE=
REPAIR_PACKET_MAX_CONTEXT_CHARS=
REPAIR_PACKET_LLM_CALLS=0

BEST_WINDOW_HEURISTIC_REMOVED=
THIRD_NEAR_QUOTE_ESCAPE_REMOVED=
DEDICATED_REPAIR_SYSTEM_PROMPT=false

MAX_VALIDATION_REPAIRS=2

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
PRODUCTION_MODEL_CHANGED=false
PHILOSOPHER_AGENT_DIFF=0

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7_E_RP2_POLICY_SHA=
仅在 calibration 通过时填写

STAGE_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS_TO_POLICY_FREEZE /
PATCH_REQUIRED /
BLOCKED_PRIMARY_COVERAGE

STOP

所以这轮最重要的结论其实不是“DeepSeek 不听话”。

而是：

我们刚刚差点因为一个错误的 repair 分母，把一个可能已经达到 87.5% case-level 收敛的方案判成 63.6% 失败。

同时又差点带着几个 PRIMARY_REQUIRED + book_ids=[] 的必败 case 进入 Stage B。

这两个先修掉。

暂时不加第三次 repair，也不加新的 system repair brain。 先把尺子校准，再判断模型到底有没有问题。