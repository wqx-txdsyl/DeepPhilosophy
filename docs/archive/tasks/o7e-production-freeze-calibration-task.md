
我审完 c45e87b8f → c54692308。这次可以签了。

GitHub compare 确认只有两个文件变化：backend/repair_context.py 和对应 lead-in 回归测试，没有 engine、Quote Bound、validator、slice catalog 的额外改动；远端 refactor/phiagent-main-agent-orchestration 也确实位于 c54692308d18996b58a53dde5b9540d5e8d37fc2。

代码层面，那个危险的任意 \w backward expansion 已经被完全删掉，现在 claim_start 严格等于 bounded window 内 LEADIN_RE 的匹配起点；同时只新增了我们授权的“replacement 要与保留左上下文语法衔接”说明。 测试也明确覆盖了 孔子、对此孔子、在《论语》中孔子 三类前缀，以及 5 种前缀下 claim_start == regex match start 的 invariant。

因此正式裁定：

O7_E_RP2_RCA2_RP1A_REVIEW = PASS

LEADIN_BOUNDARY_BLOCKER = CLOSED
ARBITRARY_WORD_BACKSCAN = REMOVED

LEADIN_CLAIM_START =
EXACT_LEADIN_RE_MATCH_START

SUBJECT_CONTEXT_PRESERVATION = PASS
DISCOURSE_CONTEXT_PRESERVATION = PASS
BOOK_CONTEXT_PRESERVATION = PASS

COPY_SLICE_LEADIN_SEMANTICS = PASS
PARAPHRASE_CLAIM_LEADIN_SEMANTICS = PASS

QUOTE_BOUND_CHANGED = false
VALIDATOR_CHANGED = false
SLICE_CATALOG_CHANGED = false

LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true
RCA1_DIAGNOSTIC_PHASE = CLOSED
RCA2_ACTION_SEMANTICS_PHASE = CLOSED

PRODUCTION_FREEZE_AUTHORIZED = true

MAX_VALIDATION_REPAIRS = 2
V3_HOLDOUT_RUN = false

O7_E_PRODUCTION_FREEZE_AUTHORIZED = true

到这里停止 RCA patch 链。 不再有 RP1B、RP2、H2E 之类的东西。

接下来进入我们之前约定的两个动作：Production Freeze → Canonical Academic Calibration。

O7-E Production Freeze + Academic Calibration
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = c54692308

GENERAL_AGENT_ONLY = true
V3_HOLDOUT_RUN = false
MAX_VALIDATION_REPAIRS = 2
A. 把 Local Patch 从 evaluation seam 正式晋升为 production capability

目前生产默认仍是：

_evaluation_repair_adapter = None

所以架构虽然 qualify，线上其实还没启用。

这一步不要让生产去 import：

tools/evaluation/o7e_rca1_hook_eval.py

把 LocalPatchAdapter 晋升到生产模块，建议：

backend/local_patch_runtime.py

职责只能是：

prepare()
parse_and_apply()
mechanical telemetry

认知权仍全部属于 Main Agent。

要求：

LOCAL_PATCH_ADAPTER_OWNER = 1

evaluation runner 改为 import 同一个 production adapter。

B. General Agent 正式启用，哲学家 Agent 继续零改

生产路径：

general
  ↓
deterministic validator
  ↓
ALL-local + anchors safe
  ↓
LOCAL_PATCH

otherwise
  ↓
FULL_REWRITE

哲学家 agent：

LOCAL_PATCH_PRODUCTION_ENABLED = false

本阶段：

PHILOSOPHER_AGENT_DIFF = 0
C. Production freeze

一旦启用后冻结这些 owner：

repair_context.py
local_patch_runtime.py
final_validator.py
quote_bound.py
LOCAL_PATCH_SYSTEM_PROTOCOL
REPAIR_SYSTEM_PROTOCOL
MAX_VALIDATION_REPAIRS
candidate config

建立一个明确的 freeze SHA：

O7E_PRODUCTION_FREEZE_SHA

后续 academic calibration、V3 均以它为 base。

不得在跑分途中修改。

D. 先修 canonical academic judge 的两个已知 blocker

这个必须在 calibration 前完成，不能拿旧 judge 跑。

D1. REQUIRED score 不得从分母消失

当前 o7e_bakeoff_judge2.py 对 REQUIRED dimension 的逻辑仍是：

Python
Run
if applicability == "REQUIRED" and median is not None:
    dim_scores.append(median)

因此 REQUIRED + median=null 仍然会静默从 denominator 消失。

改成：

manifest REQUIRED
AND no valid numeric score
→ EVALUATION_INVALID

Hard：

REQUIRED_DIMENSION_MISSING_SCORE = 0

禁止把它当 0 分，也禁止忽略。

D2. 给 judge 真正的 primary evidence

当前 canonical judge2 仍然只给：

Python
Run
primary_ev = [{
    "source": "read_chapters",
    "chapters": facts.get("read_chapters")
}]

也就是 chapter identity，没有足够 primary text evidence。

必须从已有安全机械证据构建，不新增检索，不改 Agent：

PRIMARY_TEXT_EVIDENCE =
  verified QuoteBound entries
  + used primary evidence excerpts
  + read chapter identities
  + formal citation provenance

只提供已有 evidence。

不要给 judge 整个 raw tool log。

不要存 CoT。

Hard：

CANONICAL_JUDGE_CONSTITUTION_OWNER = 1
PRIMARY_EVIDENCE_FROM_EXISTING_RUN = true
JUDGE_ADDITIONAL_RETRIEVAL = 0
E. Academic calibration 用实际 production path

仍然使用旧的 8-case calibration pool。

模型使用当前实际生产配置；不要再用 V4-Pro。

必须真实走：

production Main Agent
→ production LocalPatchAdapter
→ production validator

不再用 evaluation-only 注入来模拟。

先做 delivery gate：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

TERMINAL_PENDING=0
VALIDATOR_EMPTY_FINAL=0
TERMINAL_CANDIDATE_EMPTY=0

PUBLIC_INVALID_CITATIONS=0
UNVERIFIED_PUBLIC_EXACT_QUOTES=0
PUBLIC_ACCESS_OVERCLAIMS=0

Local Patch freeze gates：

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0
UNKNOWN_SLICE_ID=0
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0
F. 再跑 canonical scholarly judge

8 case 只 judge published final answer。

沿用 O7-A 冻结的五轴：

TEXTUAL_GROUNDING
ARGUMENT_RECONSTRUCTION
INTERPRETIVE_PLURALITY
HISTORICAL_DISCIPLINE
LITERATURE_ORIENTATION

Hard calibration：

APPLICABLE_DIMENSION_MEAN >= 3.20

TEXTUAL_GROUNDING_REQUIRED_MEAN >= 3.40
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN >= 3.20
INTERPRETIVE_PLURALITY_REQUIRED_MEAN >= 3.00
HISTORICAL_DISCIPLINE_REQUIRED_MEAN >= 3.40
LITERATURE_ORIENTATION_REQUIRED_MEAN >= 3.20

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0
REQUIRED_DIMENSION_MISSING_SCORE = 0

ALL_FATAL_FLAGS = 0

继续要求：

FABRICATED_BIBLIOGRAPHY=0
FABRICATED_SCHOLAR_ATTRIBUTION=0
PRIMARY_TEXT_MISREPRESENTATION=0
MAJOR_ANACHRONISM=0
FALSE_EXACT_QUOTE=0
LITERATURE_ACCESS_OVERCLAIM=0
G. STOP 规则

如果 delivery 失败：

STOP
→ DELIVERY_GATE_NOT_MET

不跑 academic judge。

如果 delivery PASS、academic FAIL：

STOP
→ SCHOLARLY_QUALITY_GATE_NOT_MET

不要回去改 Local Patch。

Local Patch 已经 architecture-qualified，除非出现明确 correctness regression，否则不许把学术内容质量问题重新甩回 repair runtime。

如果双轴都 PASS：

V3_HOLDOUT_AUTHORIZED = true

然后才第一次打开 untouched 28-case V3。

最终回执：

O7_E_PRODUCTION_FREEZE_CALIBRATION =
READY_FOR_REVIEW /
DELIVERY_GATE_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=c54692308

PRODUCTION_PROMOTION_SHA=
JUDGE_FIX_SHA=
FREEZE_SHA=
CALIBRATION_ARTIFACT_SHA=
HEAD_SHA=
REMOTE_SHA=

LOCAL_PATCH_ADAPTER_OWNER=1
PRODUCTION_LOCAL_PATCH_ENABLED=true
GENERAL_AGENT_ONLY=true
PHILOSOPHER_AGENT_DIFF=0

MAX_VALIDATION_REPAIRS=2

FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_MATCHING_SEMANTICS_CHANGED=false
SLICE_CATALOG_CHANGED=false

CANONICAL_JUDGE_CONSTITUTION_OWNER=1
PRIMARY_EVIDENCE_FROM_EXISTING_RUN=true
JUDGE_ADDITIONAL_RETRIEVAL=0
REQUIRED_DIMENSION_MISSING_SCORE=

CALIBRATION_COMPLETED=8
CALIBRATION_PUBLISHED=
CALIBRATION_REPAIR_TRIGGERED=
CALIBRATION_REPAIR_CONVERGED=
CALIBRATION_REPAIR_CONVERGENCE=

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=
PROMPT_ISSUE_COVERAGE=
LINKED_EVIDENCE_STARVATION=
UNKNOWN_SLICE_ID=
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=

APPLICABLE_DIMENSION_MEAN=
TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=
REQUIRED_DIMENSION_MISSING_SCORE=

FABRICATED_BIBLIOGRAPHY=
FABRICATED_SCHOLAR_ATTRIBUTION=
PRIMARY_TEXT_MISREPRESENTATION=
MAJOR_ANACHRONISM=
FALSE_EXACT_QUOTE=
LITERATURE_ACCESS_OVERCLAIM=

V3_HOLDOUT_RUN=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
PATCH_REQUIRED

STOP

所以这次结论终于可以很明确：

Local Patch 架构验收完成，RCA-1 / RCA-2 正式结束。现在把它晋升为 General Agent 的生产能力并冻结，然后重新回到 O7-E 真正的目标：学术回答质量。

而不是继续修 repair 系统。