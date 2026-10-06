我审完 4cfb60491 → b90d87644 了。这次我授权测试第 3 次 repair，但只授权为 evaluation-only 对照实验，还不允许把生产 MAX_VALIDATION_REPAIRS 从 2 改成 3。

先给正式裁定：

O7_E_BAKEOFF_V2_1_REVIEW = PATCH_REQUIRED

MATCHED_REPAIR_CONFIG_FIELDS = ACCEPTED
RP_A_STAGE_A = PASS
RP_B_STAGE_A = PASS

RP_B_E2E_RUN1 =
5/8 published
4/7 repair converged
0.571 convergence
EMPTY=0

RP_B_E2E_HARD_GATE = FAIL

FULL_CONTEXT_REPAIR_BOTTLENECK =
STRONGLY_SUPPORTED_NOT_FINAL

THIRD_REPAIR_ABLATION = AUTHORIZED
PRODUCTION_MAX_REPAIRS_3 = NOT_AUTHORIZED

REPAIR_INPUT_ARCHITECTURE_CHANGE = NOT_AUTHORIZED_YET
RUN2_CONFIRMATION = NOT_REQUIRED

V3_STAGE_B_AUTHORIZED = false

有三个地方我要校正回执中的表述。

第一，RUN2 没跑完全正确，而且没有边界歧义。我们冻结的早停条件是：

published <= 5/8
OR
(triggered >= 3 AND convergence < 0.60)

实际是：

published = 5
triggered = 7
convergence = 0.571

所以两条都命中早停。不是“5 稍微高于边界”，5 <= 5 本身就成立。正式 artifact 也确实是 5/8、4/7、0.571。

第二，“配置漂移已完全排除”我只接受到参数层，不接受到 client path 层。

现在单一配置对象确实冻结了：

temperature
max_tokens
thinking
reasoning_effort

RP-B 是 0 / 8000 / disabled / None。

但 Stage A 实际走的是：

build_candidate_client()
→ urllib.request
→ raw HTTP

而 Stage B 并没有调用这个 client，它重新构造了：

ChatDeepSeek(...)

。

所以现在准确说法是：

CONFIG FIELD DRIFT = CLOSED
CLIENT / SERIALIZATION PATH DRIFT = STILL PRESENT

这个差异未必是主因，但既然我们要开始动“第 3 次 repair”这种架构参数，就应该先把这个最后的小 confound 处理干净。

第三，也是决定我为什么允许做第三次 repair 实验、但还不允许生产改 3 次的关键：

你说三个失败例都是“issue 单调缩减到 1–2 个”，方向基本对，但实际轨迹比这个弱一些。

三个最终失败 case 的 final 状态是：

H02 → 1 × NEAR_QUOTE_NOT_MARKED
H03 → 1 × NEAR_QUOTE_NOT_MARKED
H07 → 2 × NEAR_QUOTE_NOT_MARKED

而 repair trace 可以看到典型轨迹是：

2 issues → 1 issue → final 1 issue
2 issues → 1 issue → final 1 issue
4 issues → 2 issues → final 2 issues

也就是说：

第一轮 repair 明显有效，第二轮在这些失败例上出现 plateau。

例如真实 trace 已出现：

attempt 1:
UNSUPPORTED_EXACT_QUOTE
NEAR_QUOTE_NOT_MARKED

attempt 2:
NEAR_QUOTE_NOT_MARKED

以及另一例：

4 issues
→
2 × NEAR_QUOTE_NOT_MARKED

。

所以第三轮值得测，因为只剩机械型 near-quote，而且只需要救回 3 个失败例中的 2 个，就会同时把：

publication:
5/8 → 7/8

repair convergence:
4/7 → 6/7 = 0.857

推过两条硬门。

这是目前第一次真正满足“第三轮有一个明确、可证伪的产品价值假设”。

但我们不能先假设它一定成功。

O7-E RP2 REPAIR-DEPTH ABLATION
2 vs 3 Repair Counterfactual
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = b90d87644

MODEL = deepseek-v4-pro
CONFIG = RP-B

NORMAL:
temperature=0.7
max_tokens=8000
thinking=enabled
reasoning_effort=low

REPAIR:
temperature=0
max_tokens=8000
thinking=disabled

PRODUCTION_MAX_VALIDATION_REPAIRS = 2
EVALUATION_MAX_VALIDATION_REPAIRS = 3

V3_HOLDOUT_RUN = false
1. 先关闭最后一个 client-path confound

不要再让 Stage A：

urllib

而 Stage B：

ChatDeepSeek

。

建立真正单源：

build_candidate_langchain_client(cfg, mode)

Stage A RP-B 再用与 Stage B repair 完全相同的 ChatDeepSeek client跑一次 16 fixture。

要求：

CLIENT_IMPLEMENTATION_STAGE_A =
CLIENT_IMPLEMENTATION_STAGE_B =
ChatDeepSeek

REPAIR_CONFIG_HASH_STAGE_A ==
REPAIR_CONFIG_HASH_STAGE_B

只跑 RP-B，不重跑 RP-A。

门：

>=13/16
EMPTY=0
MODEL_MISMATCH=0

如果这都突然掉下去：

STOP
CLIENT_PATH_CONFOUND_CONFIRMED

不要测试第 3 次 repair。

2. 第 3 次 repair 只能 evaluation-only

禁止现在改：

Python
Run
MAX_VALIDATION_REPAIRS = 3

生产常量。

评价 harness 临时：

Python
Run
final_validator.MAX_VALIDATION_REPAIRS = 3

或等价的 evaluation-only override。

要求退出时恢复。

Hard：

PRODUCTION_MAX_REPAIRS_CHANGED = false
3. 不要做“2 次跑一遍、3 次再跑一遍”

这样 normal temperature=0.7 会重新生成不同 initial answer，又混入随机性。

正确实验是：

一个 E2E run
↓
同一个 initial candidate
↓
repair 1
↓
repair 2
↓
记录 WOULD_STOP_AT_2
↓
如果仍 invalid
↓
repair 3
↓
记录 RESULT_AT_3

由于 RP-B repair 是 deterministic，这样可以在同一次 trajectory中得到真正的：

2-repair counterfactual
vs
3-repair outcome

而不是两次不配对实验。

4. 必须记录每次 validator 状态

每个 triggered case：

INITIAL_ISSUES
AFTER_REPAIR_1_ISSUES
AFTER_REPAIR_2_ISSUES
AFTER_REPAIR_3_ISSUES

ISSUE_COUNT_0
ISSUE_COUNT_1
ISSUE_COUNT_2
ISSUE_COUNT_3

VALID_AFTER_2
VALID_AFTER_3

以及：

candidate_sha_after_1
candidate_sha_after_2
candidate_sha_after_3

不保存 rejected candidate 正文。

5. 第三轮的真正指标

增加：

REPAIR3_ELIGIBLE_CASES
REPAIR3_RESCUED_CASES
REPAIR3_RESCUE_RATE

定义：

eligible =
repair2 后仍 FAIL

rescued =
repair2 FAIL
AND repair3 PASS

这就是我们真正要测的东西。

6. 仍用同一 8-case calibration pool

这次只跑一次。

不是 Stage B，不碰 V3。

最终从同一条 trajectory 同时算：

PUBLICATIONS_AT_2
PUBLICATIONS_AT_3

REPAIR_CONVERGENCE_AT_2
REPAIR_CONVERGENCE_AT_3
7. 第三轮授权进入生产的 Hard Gate

必须全部满足：

PUBLICATIONS_AT_3 >= 7/8

REPAIR_CONVERGENCE_AT_3 >= 0.80

EMPTY_FINAL_AT_3 = 0

NEW_FATAL_ERROR_AT_3 = 0

SYSTEMIC_QUOTE_DELETION = 0

并且：

REPAIR3_ELIGIBLE_CASES >= 2
REPAIR3_RESCUED_CASES >= 2

以当前形态来说就是：

3 个 repair2-exhausted 中至少救回 2 个。

8. 还要看第三轮是不是在做“有意义的收敛”

不能只看结果。

要求：

ISSUE_COUNT_AFTER_REPAIR3
<
ISSUE_COUNT_AFTER_REPAIR2

至少在 rescued case 上成立。

如果出现：

1 个 NEAR
→ 第三轮
→ 又换成另外 1 个 NEAR

即使偶然 publication 变好，也要审。

9. 成本也记录

因为第三轮是用户真实延迟。

记录：

REPAIR3_CASES
REPAIR3_MEDIAN_LATENCY
REPAIR3_P95_LATENCY
REPAIR3_TOKEN_USAGE

不作为当前 hard gate，但用于最后产品裁决。

10. 如果第三轮成功

如果得到比如：

AT_2:
5/8
4/7 = .571

AT_3:
7/8
6/7 = .857

那我会授权：

MAX_VALIDATION_REPAIRS:
2 → 3

作为一个非常窄的 runtime mechanical change。

然后冻结 policy/config，再进入 V3 Stage B。

不再改 repair input architecture。

11. 如果第三轮失败

例如：

5/8 → 6/8

或者：

4/7 → 5/7

仍不到门：

我就正式签：

FULL_CONTEXT_REPAIR_ARCHITECTURE_BOTTLENECK = CONFIRMED

然后下一步不是：

3 → 4 repairs

也不是继续换模型。

而是进入：

REPAIR CONTEXT ARCHITECTURE

重点审：

完整候选如何被标注 offending spans
多 issue 是否一次性一一对应 evidence
repair 是否在修改一个 issue 时重新破坏另一个
candidate / evidence / issue 的局部编辑目标是否表达得足够机械

特别是现在 packet builder 有一个值得后续审的事实：

Python
Run
max_evidence = 3

是整个 repair packet 总上限，不是每个 issue 3 条。

当 initial candidate 有 4 个 quote issues 时，第一个 repair 最多只给 3 条 linked evidence。

它未必是当前最后 1–2 个 issue 的根因——因为第二轮已经只剩 1–2 个时 packet 足够——但如果第三轮仍救不回来，这会成为下一阶段真正值得研究的 input-architecture 点，而不是继续堆 prompt。

最终回执：

O7_E_REPAIR_DEPTH_ABLATION =
READY_FOR_REVIEW /
CLIENT_PATH_CONFOUND /
REPAIR3_NOT_QUALIFIED

BASE_SHA=

CLIENT_PARITY_SHA=
ABLATION_CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

MODEL=deepseek-v4-pro
CONFIG=RP-B

STAGE_A_CLIENT=
STAGE_B_CLIENT=
CLIENT_PATH_EQUAL=

STAGE_A_PARITY_VALID=/16
STAGE_A_PARITY_EMPTY=

PRODUCTION_MAX_VALIDATION_REPAIRS=2
EVALUATION_MAX_VALIDATION_REPAIRS=3
PRODUCTION_MAX_REPAIRS_CHANGED=false

CASES=8
REPAIR_TRIGGERED=

PUBLICATIONS_AT_2=/8
REPAIR_CONVERGED_AT_2=
REPAIR_CONVERGENCE_AT_2=

PUBLICATIONS_AT_3=/8
REPAIR_CONVERGED_AT_3=
REPAIR_CONVERGENCE_AT_3=

REPAIR3_ELIGIBLE_CASES=
REPAIR3_RESCUED_CASES=
REPAIR3_RESCUE_RATE=

REPAIR3_RESCUED_CASE_IDS=

ISSUE_TRAJECTORIES=
case:
initial →
repair1 →
repair2 →
repair3

EMPTY_FINAL_AT_3=
NEW_FATAL_ERROR_AT_3=
SYSTEMIC_QUOTE_DELETION=

REPAIR3_MEDIAN_LATENCY=
REPAIR3_P95_LATENCY=

MAX_VALIDATION_REPAIRS_PRODUCTION_CHANGE_AUTHORIZED=false

V3_HOLDOUT_RUN=false

FULL_TESTS=

PROPOSED_VERDICT=
AUTHORIZE_MAX_REPAIRS_3 /
REPAIR_ARCHITECTURE_REQUIRED /
CLIENT_PATH_CONFOUND

STOP

所以我的选择是 (a)，但不是直接把生产改成 3 次。

我们现在终于有了一个适合测试第三次 repair 的局面：5/8、4/7，三个失败里两个最终只剩一个 NEAR issue；只要第三轮救回两例，两条 Gate 会同时翻过。

同时也别把当前证据说得比它实际更强：失败轨迹是“第一轮明显下降、第二轮 plateau”，而不是持续每轮下降。

这个实验跑完，我们基本就能结束“到底是次数不够还是 repair architecture 不对”这场拉锯了。