
我审完 c54692308 → bc3ae2400，远端分支也确实停在 bc3ae24009f70f433245c874163813ba6c8cce01。

CAL1 的 5/8 + 0.571 以及 Local Patch 机械门全绿都和正式 summary 一致，因此 DELIVERY_GATE_NOT_MET 本身成立，按 §G 停止、不跑 academic judge 是正确动作。

但我不能接受回执里的“3 个失败全部只是 Flash 方差、生产路径 delta=0”。独立审计发现了一个真正的 production blocker，而且它很可能就是本轮可靠性波动的一部分来源。

O7_E_PRODUCTION_FREEZE_CAL1_REVIEW = PATCH_REQUIRED

PRODUCTION_ADAPTER_PROMOTION = PASS
LOCAL_PATCH_ADAPTER_OWNER = PASS
GENERAL_AGENT_ONLY_ENABLEMENT = PASS

CAL1_DELIVERY_GATE = FAIL
STOP_BEFORE_ACADEMIC_JUDGE = PASS

LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true
LOCAL_PATCH_CORRECTNESS_REGRESSION = NOT_OBSERVED

FLASH_RUN_VARIANCE = REAL
FLASH_VARIANCE_AS_SOLE_ROOT_CAUSE = NOT_PROVEN

SYSTEM_ACTION_CONTRACT_DRIFT = CONFIRMED
PUBLIC_ACCESS_OVERCLAIMS_METRIC = FALSE_GREEN
CANONICAL_JUDGE_INPUT = PATCH_REQUIRED
CANONICAL_JUDGE_AGGREGATION = PATCH_REQUIRED

CURRENT_FREEZE_SHA = INVALIDATED
PRODUCTION_RELEASE_AUTHORIZED = false
V3_HOLDOUT_AUTHORIZED = false
1. 最重要的 blocker：System protocol 还停留在 RCA-1 时代

现在生产真正注入 Main Agent 的 LOCAL_PATCH_SYSTEM_PROTOCOL 仍然写着：

每条 patch 二选一：

COPY_SLICE
或
REPLACE_TEXT

REPLACE_TEXT = 你自己的转述/引用修正文本
并且只替换引文内容本身、保留外层引用格式

可是 RCA-2 之后，真正的 Human patch contract 和 applier 已经变成：

quote:
  COPY_SLICE
  PARAPHRASE_CLAIM

citation:
  COPY_SLICE
  REPLACE_TEXT

quote + REPLACE_TEXT = INVALID
PARAPHRASE_CLAIM = replace whole claim_span

也就是说，当前生产调用里又出现了我们以前专门修过的高优先级冲突：

SYSTEM:
quote 可以 REPLACE_TEXT；
REPLACE_TEXT 做转述并保留引号。

HUMAN:
quote 禁止 REPLACE_TEXT；
转述必须 PARAPHRASE_CLAIM 并移除逐字 claim。

APPLIER:
quote REPLACE_TEXT 直接拒绝。

这不是小文案问题。

这是：

System 告诉模型做一件 runtime 明确判非法的事情。

尤其对 Flash，这完全足以放大 INVALID_JSON / INVALID_ACTION / repair 不稳定。

所以本轮：

S9 INVALID_JSON ×2
H04 3→1→1
S4 9→2→2

不能全部归因成“纯 run-to-run variance”。

Flash 方差确实存在，但当前实验仍有 system-contract confound。

而 freeze manifest 已经把这个旧 System protocol 的 SHA 写进冻结件，所以 63b964d88 从发现此 blocker 起就不能再作为最终 production freeze。

2. Adapter 晋升本身我接受

这部分没有问题。

生产 General Agent 默认拿 local_patch_runtime.production_adapter()，评测 runner 也直接 import 同一个 LocalPatchAdapter，所以 LOCAL_PATCH_ADAPTER_OWNER=1 的方向成立。

因此：

不要回滚 Local Patch
不要重新打开 RCA-1 / RCA-2
不要改 action semantics

现在只修 canonical contract 漂移。

3. PUBLIC_ACCESS_OVERCLAIMS=0 是 false-green

CAL1 runner 现在实际上是：

Python
Run
"public_access_overclaims": 0 if published else None

也就是：

只要发布成功
→ 自动记 0

没有任何检测发生。

因此 summary 的：

PUBLIC_ACCESS_OVERCLAIMS=0

不能作为 Gate 证据。

这里我修正之前的任务设计：

access overclaim 本质上是语义学术判断，不应该伪装成 mechanical delivery gate。

O7-A canonical judge 本来就已经有：

LITERATURE_ACCESS_OVERCLAIM

并定义了：

METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ

对应的判断规则。

所以以后改成：

DELIVERY:
PUBLIC_ACCESS_OVERCLAIMS_MEASURED = false
ACCESS_OVERCLAIM_GATE = DEFERRED_TO_CANONICAL_SCHOLARLY_JUDGE

FINAL SCHOLARLY GATE:
LITERATURE_ACCESS_OVERCLAIM = 0

这不是降低 Gate，而是把 Gate 移回真正能测它的仪器。

4. D2 还没有真正给 judge “primary source text”

现在 _primary_text_evidence() 把：

Python
Run
e.get("preview")

作为：

verified_quote_bound.text

传给 judge。

问题是 preview 来自答案里的引文。

对于 VERIFIED_EXACT 还勉强可作为已核验文本表现；但对于：

VERIFIED_NEAR

它本来就是“答案措辞只近似证据”。

因此：

不能把模型自己写出的 near quote 再作为 “PRIMARY_TEXT_EVIDENCE” 交给 judge。

这会形成自证循环。

CAL artifact 里已经保存了真正的 existing-run evidence snippets，因此 D2 应该从：

evidence_digest.used_evidence
/ retrieved_evidence

中取实际 source text，而不是从答案 preview 取。

不新增检索即可。

5. Judge aggregation 还有两个 denominator blocker

D1 的 REQUIRED-null 方向是对的，但还没完全闭合。

当前如果某 case 的三个 judge vote 全部 schema-invalid，代码会写：

{"case_id": ..., "error": "all judge votes invalid"}

然后 aggregate 时这个 case 不产生 required_missing，所以仍可能：

EVALUATION_INVALID=false

。

必须有：

JUDGE_CASES_MISSING = 0

否则整个 scholarly evaluation invalid。

另一个问题是：

Python
Run
dim_scores

现在只收：

applicability == REQUIRED

然后用它计算：

applicable_mean

。

但 canonical O7-A 设计是：

NOT_APPLICABLE → 排除
REQUIRED → 必须分
OPTIONAL → 若实际涉及则有分

。

所以：

APPLICABLE_DIMENSION_MEAN

必须计算：

所有 numeric REQUIRED
+
所有 numeric OPTIONAL

只排除：

NOT_APPLICABLE / 合法 OPTIONAL null

不能把 OPTIONAL 全部从“applicable mean”中删掉。

下一步任务书
O7-E PF-RP1 — Canonical Contract & Measurement Closure
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = bc3ae2400

MODEL_UNDER_TEST = deepseek-v4-flash
MAX_VALIDATION_REPAIRS = 2

LOCAL_PATCH_ARCHITECTURE_QUALIFIED = true

NO_RCA_REOPEN = true
NO_ACTION_SEMANTICS_CHANGE = true
NO_SLICE_CATALOG_CHANGE = true
NO_VALIDATOR_CHANGE = true
NO_QUOTE_BOUND_CHANGE = true

V3_HOLDOUT_RUN = false
A. Action contract 单一真源

不要只手改两份文案。

在 repair_context.py 建机械 single source，例如：

Python
Run
LOCAL_PATCH_ACTION_MATRIX = {
    "quote": ("COPY_SLICE", "PARAPHRASE_CLAIM"),
    "citation": ("COPY_SLICE", "REPLACE_TEXT"),
}

再由同一 owner 驱动：

System protocol
Human patch contract
applier eligibility tests

必须锁死：

quote + REPLACE_TEXT = invalid
quote + PARAPHRASE_CLAIM = valid

citation + REPLACE_TEXT = valid
citation + PARAPHRASE_CLAIM = invalid

System 必须明确：

PARAPHRASE_CLAIM
→ whole claim_span
→ 不再是 verbatim quote

不能再出现：

REPLACE_TEXT = quote paraphrase

Hard：

LOCAL_PATCH_ACTION_CONTRACT_OWNER=1
SYSTEM_HUMAN_ACTION_MATRIX_EQUAL=true
APPLIER_ACTION_MATRIX_EQUAL=true
B. 修 access metric，不新增 semantic runtime

删除：

published → public_access_overclaims=0

改为：

PUBLIC_ACCESS_OVERCLAIMS_MEASURED=false
ACCESS_OVERCLAIM_GATE=DEFERRED_TO_CANONICAL_JUDGE

最终 Gate 仍保持：

LITERATURE_ACCESS_OVERCLAIM=0

不写 Python 语义检测器。

C. Canonical judge measurement closure

Primary evidence 改成真正 existing-run source：

优先 evidence_digest.used_evidence
source_type=primary
snippet/text 实际内容

需要时根据 evidence ID / book / chapter 与 verified QuoteBound 映射。

禁止：

VERIFIED_NEAR answer preview
→ 冒充 primary source text

可以保留 answer quote，但字段必须叫：

answer_quote

而不是 source_text。

同时把已有 secondary scholarly records 和 access states 显式送进：

SECONDARY_SOURCE_RECORDS
ACCESS_LEVELS

没有的数据保持空，不编造。

D. Judge aggregate

必须新增：

JUDGE_CASES_EXPECTED=
JUDGE_CASES_VALID=
JUDGE_CASES_MISSING=

JUDGE_CASES_MISSING > 0
→ EVALUATION_INVALID=true

以及：

APPLICABLE_DIMENSION_MEAN =
all numeric REQUIRED
+
all numeric OPTIONAL

NOT_APPLICABLE excluded
OPTIONAL null excluded

REQUIRED_*_MEAN 仍只看 REQUIRED。

E. 重新 Freeze

由于 System protocol 变化：

OLD_FREEZE_SHA=63b964d88
STATUS=INVALIDATED_BY_PROTOCOL_DRIFT

生成新：

O7E_PRODUCTION_FREEZE_V2

这次 freeze 清单补上：

backend/engine_langgraph.py
backend/repair_context.py
backend/local_patch_runtime.py
backend/final_validator.py
backend/quote_bound.py
backend/tools/evaluation/o7e_candidate_config.py

双 system protocol SHA
action matrix SHA
MAX_VALIDATION_REPAIRS
production agent set

尤其要把 整个 engine_langgraph.py blob SHA 纳入；当前旧 freeze 只记 protocol SHA，没有冻结 production adapter wiring 本身。

然后跑 CAL2

旧 CAL1 因为存在 System/Human contract drift，不再作为模型可靠性 qualification 样本使用。

不是删除——保留为历史证据。

CAL2：

same 8 calibration cases
deepseek-v4-flash
same RP-B config
real production path
no seam
one pre-registered run

Gate：

COMPLETED=8
PUBLISHED>=7

if REPAIR_TRIGGERED>=3:
    REPAIR_CONVERGENCE>=0.80

TERMINAL_PENDING=0
VALIDATOR_EMPTY_FINAL=0
TERMINAL_CANDIDATE_EMPTY=0

PUBLIC_INVALID_CITATIONS=0
UNVERIFIED_PUBLIC_EXACT_QUOTES=0

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=1.0
PROMPT_ISSUE_COVERAGE=1.0
LINKED_EVIDENCE_STARVATION=0
UNKNOWN_SLICE_ID=0
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=0
NON_TARGET_TEXT_CHANGED_CHARS=0

不再伪报：

PUBLIC_ACCESS_OVERCLAIMS=0

而是：

ACCESS_OVERCLAIM_GATE=DEFERRED

如果 CAL2 fail：

STOP
DELIVERY_RELIABILITY_NOT_MET

这一次我不会再允许回去改 Local Patch semantics。

下一步直接进入：

Flash transport/model reliability ablation

例如 structured JSON transport / model config，而不是 repair architecture。

如果 CAL2 pass：

立即跑修正后的 canonical scholarly judge

然后才看五轴和 fatal flags。

最终回执：

O7_E_PF_RP1 =
READY_FOR_REVIEW /
DELIVERY_RELIABILITY_NOT_MET /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=bc3ae2400

ACTION_CONTRACT_SHA=
MEASUREMENT_FIX_SHA=
JUDGE_FIX_SHA=
FREEZE_V2_SHA=
CAL2_ARTIFACT_SHA=

HEAD_SHA=
REMOTE_SHA=

LOCAL_PATCH_ACTION_CONTRACT_OWNER=1
SYSTEM_HUMAN_ACTION_MATRIX_EQUAL=
APPLIER_ACTION_MATRIX_EQUAL=

QUOTE_ACTIONS=COPY_SLICE,PARAPHRASE_CLAIM
CITATION_ACTIONS=COPY_SLICE,REPLACE_TEXT

PUBLIC_ACCESS_OVERCLAIMS_MEASURED=false
ACCESS_OVERCLAIM_GATE=DEFERRED_TO_CANONICAL_JUDGE

PRIMARY_SOURCE_TEXT_FROM_EXISTING_EVIDENCE=true
ANSWER_PREVIEW_USED_AS_PRIMARY_SOURCE_TEXT=false

SECONDARY_SOURCE_RECORDS_PROVIDED=
ACCESS_LEVELS_PROVIDED=
JUDGE_ADDITIONAL_RETRIEVAL=0

JUDGE_CASES_EXPECTED=
JUDGE_CASES_VALID=
JUDGE_CASES_MISSING=

REQUIRED_DIMENSION_MISSING_SCORE=
APPLICABLE_MEAN_INCLUDES_SCORED_OPTIONAL=true

OLD_FREEZE_SHA=63b964d88
OLD_FREEZE_INVALIDATED=true
NEW_FREEZE_SHA=

CAL2_COMPLETED=8
CAL2_PUBLISHED=
CAL2_REPAIR_TRIGGERED=
CAL2_REPAIR_CONVERGED=
CAL2_REPAIR_CONVERGENCE=

LOCAL_PATCH_ANCHOR_RESOLUTION_RATE=
PROMPT_ISSUE_COVERAGE=
LINKED_EVIDENCE_STARVATION=
UNKNOWN_SLICE_ID=
UNINTENTIONAL_QUOTE_WRAPPER_LOSS=
NON_TARGET_TEXT_CHANGED_CHARS=

ACADEMIC_JUDGE_EXECUTED=

APPLICABLE_DIMENSION_MEAN=
TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

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
DELIVERY_RELIABILITY_NOT_MET /
SCHOLARLY_GATE_NOT_MET

STOP

所以当前最关键的结论不是“Flash 今天倒霉，从 8/8 掉到了 5/8”。

而是：

我们刚刚发现 RCA-2 已经改变了 patch action semantics，但高优先级 System protocol 没同步，生产冻结实际上把一个自相矛盾的合同冻住了。

先把这个 confound 关掉，再测一次 Flash。那一轮如果还掉到 5/8~6/8，我就会接受“这是模型/transport reliability 问题”，并停止碰 Local Patch。