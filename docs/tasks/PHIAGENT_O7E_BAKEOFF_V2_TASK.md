我审完 b70b8f2da → 30e55055a 了。这次方向已经可以定：选 (c)，扩充当前生产模型候选池。

但我不会给这份 “MODEL BAKEOFF FINAL” 签最终 PASS，因为独立审计发现两个会影响结论可信度的 blocker：学术 judge 不是我们冻结的 O7-A canonical judge contract；glm-4.6 的最终 Stage-B 数据也没有进入当前 Git HEAD 的正式 artifact。 好消息是，这两个问题都不改变“当前池没有可选 winner、应该换候选池”的方向。

正式裁定：

O7_E_MODEL_BAKEOFF_FINAL_REVIEW = PATCH_REQUIRED

CURRENT_4_MODEL_POOL =
NO_QUALIFIED_MODEL

DEEPSEEK_CHAT =
PRODUCT_GATE_NOT_MET

GLM_4_PLUS =
DELIVERY_PUBLICATION_PASS
REPAIR_RELIABILITY_FAIL

GLM_4_AIR =
DELIVERY_FAIL
REPAIR_RELIABILITY_FAIL

GLM_4_6 =
NO_QUALIFICATION_EVIDENCE_IN_CANONICAL_HEAD

ACADEMIC_JUDGE_RESULTS =
NONCANONICAL_DIAGNOSTIC_ONLY

KNOWN_LIMITATION_CLOSEOUT = REJECTED
GATE_REDUCTION = REJECTED
THIRD_REPAIR = REJECTED
DUAL_MODEL_MAIN+REPAIR_ARCHITECTURE = REJECTED

NEXT_DIRECTION =
CURRENT_MODEL CANDIDATE EXPANSION

O7_E_MODEL_BAKEOFF_V2_AUTHORIZED = true
V3_STAGE_B_AUTHORIZED = false
第一个 blocker：glm-4.6 的“4/8”没有进入当前 HEAD

你回执报告：

glm-4.6
4/8 published
repair 3/7
EMPTY=1

但我直接检查 30e55055a，被追踪的正式 summary 仍然是：

JSON
{
  "COMPLETED": 1,
  "PUBLISHED": 0,
  "REPAIR_TRIGGERED": 1,
  "REPAIR_CONVERGED": 0,
  "EMPTY_FINAL": 1
}

也就是说后 7 例的真实结果大概率还停留在 _tmp / 本地工作区，而没有进入 reviewer 能从 HEAD 重现的 evidence package。

所以：

glm-4.6 = 4/8

我接受为你的运行回执，但不能接受为 canonical Gate evidence。

不过这不妨碍下一步，因为 HEAD 上的 glm-4.6 更不可能被选为 winner，而不是更可能。

第二个 blocker更重要：当前“学术 judge”不是 O7-A judge

现在的 o7e_bakeoff_judge.py 自己重新写了一份简化的：

Python
Run
SYS = "You are a scholarly quality judge..."

并直接自行解析维度和 fatal。它只是借用了 O7A.JUDGE_BASE_URL，没有使用冻结的：

O7A.JUDGE_SYSTEM_PROMPT
O7A.build_judge_input()
O7A.render_judge_prompt()
O7A.validate_verdict()

。

而真正的 O7-A constitution 明确要求 judge 输入不能只看答案和一小段 evidence digest，它还有：

PRIMARY_TEXT_EVIDENCE
BIBLIOGRAPHIC_RECORDS
SECONDARY_SOURCE_RECORDS
ACCESS_LEVELS
CLAIM_LEDGER

以及完整六类 fatal 的严格定义。

更明显的是，新 bakeoff judge 把：

Python
Run
ANSWER[:8000]
EVIDENCE_DIGEST[:1000]

直接截断后送 judge。

所以目前：

glm-4-plus mean=2.767
FALSE_EXACT_QUOTE ×2

glm-4-air mean=2.423
FALSE_EXACT_QUOTE ×3
FABRICATED_BIBLIOGRAPHY ×1

这些数我只能标：

NONCANONICAL_DIAGNOSTIC

不能拿它们证明：

“GLM 系模型天然学术能力差。”

尤其 FALSE_EXACT_QUOTE 这种 fatal 极度依赖 judge 有没有拿到完整原典 evidence；只给 1000 字 evidence digest，可能制造 false positive。

不过同样，这不会救 glm-4-plus。它在学术 judge 之前就已经因为：

repair = 2 / 3 = 0.667 < 0.80

违反我们冻结的机械 hard gate。它没有资格靠学术分翻盘。

这轮真正得到的产品结论

不是：

“学术能力与 repair 能力天然负相关”

这个证据还不够。

真正可以签的是：

当前被测的四个 production configurations
没有一个满足 PhiAgent 的交付要求。

DeepSeek 的问题是完整上下文中的 repair reliability；glm-4-plus 离门最近，但 2/3 repair convergence 仍不够；glm-4-air 交付就没过；glm-4.6 目前没有 canonical 完整证据。

所以 (a) 我拒绝。4/8 发布不是适合拿 KNOWN_LIMITATION 收口的“小债”，而是产品主路径缺陷。

(d) 当然拒绝。

(b) 也不再优先。我们已经从 packet、system protocol、temperature 0.7→0，把同一个 DeepSeek configuration 能合理试的主要 repair 变量都试了一遍。继续在这里局部调参已经开始变成 fit calibration pool。

更重要的是：当前候选池本身已经过时

我顺手查了今天的官方模型状态。

DeepSeek 官方已经在 2026-07-24 淘汰 deepseek-chat / deepseek-reasoner 旧模型名；当前正式 API 模型是：

deepseek-v4-flash
deepseek-v4-pro

V4-Pro 最新 GA 是 8 月 13 日版本，V4-Flash 是 7 月 31 日版本；两者都支持 tool calling、thinking/non-thinking 和 1M context。
DeepSeek API Docs
+2
DeepSeek API Docs
+2

这意味着我们这九轮一直测的：

deepseek-chat

即使你当前 gateway 还能调用，也已经不是一个应该继续作为 2026 年 9 月生产选型真源的明确模型 ID。

下一轮必须记录：

REQUESTED_MODEL_ID
RESPONSE_MODEL_ID

否则 compatibility alias 到底映射谁都不知道。

GLM 这边也一样。Z.ai 当前已经正式推 GLM-5.3，GLM-5.3-Flash 也已经上线；但你的 Coding Plan endpoint 不能直接假定可用于 PhiAgent 生产服务。官方文档明确区分 Coding 专用 endpoint 与一般 API endpoint，并说明其他用途推荐 general API。
Z.ai
+2
ZCode
+2

所以新的生产候选应当来自真正的 general API key 权限，而不是因为 ZCode 里能用 GLM-5.3 就自动算 production-deployable。

O7-E MODEL BAKEOFF V2
Current Production Model Selection
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
30e55055a

TARGET_AGENT =
general

V3_HOLDOUT_RUN =
false

这次不要再开大工程。核心就是：

修 canonical evidence
→ 换成 2026-09 当前模型
→ 同一套擂台重新选
A. 先关闭上一轮 artifact

把现有结果正式生成：

docs/evidence/
PHIAGENT_O7E_MODEL_BAKEOFF_V1_RESULTS.json

docs/
PHIAGENT_O7E_MODEL_BAKEOFF_V1_REPORT.md

明确写：

deepseek-chat = FAIL_REPAIR
glm-4-plus = FAIL_REPAIR
glm-4-air = FAIL_DELIVERY + FAIL_REPAIR
glm-4.6 = NONCANONICAL_COMPLETION_ARTIFACT

当前 GLM 学术 judge：

ACADEMIC_RESULTS_STATUS =
NONCANONICAL_DIAGNOSTIC_ONLY

不要删除历史。

B. 修 canonical academic judge

o7e_bakeoff_judge.py 不得再拥有自己的 judge constitution。

必须复用：

O7A.JUDGE_SYSTEM_PROMPT
O7A.build_judge_input
O7A.render_judge_prompt
O7A.validate_verdict
O7A.DIMENSIONS
O7A.FATAL_FLAGS

只允许 O7-E 固定：

JUDGE_MODEL = glm-4.6
temperature = 0
thinking = disabled
k = 3

不要重写 rubric。

同时建立 8-case：

BAKEOFF_EVALUATION_MANIFEST

恢复它们原来的：

category
applicability
evidence_expectation

不能再让 judge 自己猜 REQUIRED/OPTIONAL/N/A。

C. 新候选池

第一优先级：

deepseek-v4-pro
deepseek-v4-flash

这是当前官方 production API 的明确模型。
DeepSeek API Docs
+1

第二优先级：

glm-5.3
glm-5.3-flash

但只在下面条件成立时进入：

GENERAL_API_KEY_CALL = PASS
PRODUCTION_DEPLOYABLE = true

如果只能通过 Coding Plan endpoint 用：

DO NOT INCLUDE

不要再测：

deepseek-chat
deepseek-reasoner

作为新候选。

它们只留下历史 baseline。

D. 候选 identity 必须 E2E 验真

每次 API 调用记录：

requested_model
response.model
provider
base_url_class

Hard：

REQUESTED_RESPONSE_MODEL_ID_MISMATCH = 0

如果 provider 返回 alias：

candidate_status = IDENTITY_UNRESOLVED

不能进入正式排名。

E. 不重新造 fixtures

继续使用上一轮已经冻结的 8 fixtures。

这很好，因为新候选从未参与这些结果。

继续：

8 fixtures × 2

Stage A：

>=13/16
EMPTY=0
NEW_FATAL=0

才进 E2E。

F. Stage B 完全沿用冻结门
COMPLETED = 8
FINAL_PUBLICATIONS >= 7
EMPTY_FINAL = 0

if REPAIR_TRIGGERED >= 3:
    REPAIR_CASE_CONVERGENCE >= 0.80

PROTOCOL_INJECTION = 1.0
PACKET_TELEMETRY_MISSING = 0

一个字都不降。

G. 学术 judge 只给机械 PASS 的模型跑

这样省额度。

要求：

APPLICABLE_DIMENSION_MEAN >= 3.20
FATAL_FLAGS = 0

如果一个模型机械 Gate 已经失败：

ACADEMIC_JUDGE_RUN = false
H. Winner

还是：

Hard Gate first

不做加权平均。

有一个双轴通过，就可以选。

多个通过，再按：

publication
repair reliability
scholarly quality
fatal
latency
cost

排序。

最终回执压缩成：

O7_E_MODEL_BAKEOFF_V2 =
READY_FOR_REVIEW /
NO_MODEL_QUALIFIED /
BLOCKED

BASE_SHA=

V1_CLOSEOUT_SHA=
BAKEOFF_V2_CODE_SHA=
HEAD_SHA=
REMOTE_SHA=

CANONICAL_JUDGE_CONSTITUTION_OWNER=1
O7A_BUILD_JUDGE_INPUT_USED=
O7A_VALIDATE_VERDICT_USED=

FIXTURE_HASH=
V3_HOLDOUT_RUN=false

CANDIDATES=

CANDIDATE=
REQUESTED_MODEL_ID=
RESPONSE_MODEL_ID=
PRODUCTION_DEPLOYABLE=
GENERAL_API=true/false

STAGE_A_VALID=/16
STAGE_A_RELIABILITY=

STAGE_B_COMPLETED=/8
STAGE_B_PUBLISHED=/8

REPAIR_TRIGGERED=
REPAIR_CONVERGED=
REPAIR_CONVERGENCE=

EMPTY_FINAL=
MECHANICAL_HARD_GATE=

ACADEMIC_JUDGED=
APPLICABLE_DIMENSION_MEAN=
FATAL_FLAGS=
ACADEMIC_HARD_GATE=

FINAL_HARD_GATE=

QUALIFIED_MODELS=

RECOMMENDED_MODEL=

PRODUCTION_MODEL_CHANGED=false
MAX_VALIDATION_REPAIRS=2

FULL_TESTS=

STOP

所以这次我给你的选择很明确：

选 (c)，但不要去测 deepseek-reasoner / GLM-4.5 这种已经落后于当前生产线的名字。直接把候选池升级到 DeepSeek V4 Pro / V4 Flash，以及真正可由 general API 部署的 GLM-5.3 系。

尤其我现在最想看的是 deepseek-v4-pro。

它保留了 DeepSeek 在这套系统里已经表现出来的学术长回答优势，同时官方最新 GA 又明确强化了 Agent 能力；如果它把完整链路 repair 从当前 0.4 左右拉到门线上，我们就不需要为 repair 引入第二个“大脑”。
DeepSeek API Docs

V3 继续封着。新 winner 出来之前，一题都别碰。