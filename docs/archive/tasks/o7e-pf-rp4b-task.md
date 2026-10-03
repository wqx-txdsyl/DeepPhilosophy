
我审完 7b57e0c6b → 27f1ddc50。这轮最大的结论不是“只差 HD 0.15”，而是：SCHOL_CAL3 已经非常接近 Gate，但实际上有两个学术轴未过，而且 judge evidence parity 还剩一个明确的 legacy-key 缺口。

先正式修正回执里的一个关键算术错误：

LITERATURE_ORIENTATION_REQUIRED_MEAN = 3.0
GATE = 3.20

3.0 < 3.20

所以并不是“仅 HD 一项未达”。正式 summary 也明确记录 historical_discipline=3.25、literature_orientation=3.0。

我的裁定是：

O7_E_PF_RP4A_REVIEW =
PASS_FOR_PRODUCT_PROGRESS
+
MEASUREMENT_MICRO_PATCH_REQUIRED

DELIVERY_GATE = PASS

SCHOLARLY_SEARCH_ACTIVATION = PASS
SCHOLARLY_READ_ACTIVATION = PASS

LOCAL_PATCH_ARCHITECTURE = FROZEN
RP_B = RETAIN

ACADEMIC_GATE = FAIL

FAILED_REQUIRED_AXES =
  HISTORICAL_DISCIPLINE
  LITERATURE_ORIENTATION

HISTORICAL_DISCIPLINE = 3.25 < 3.40
LITERATURE_ORIENTATION = 3.00 < 3.20

ALL_FATAL_FLAGS = 0
REQUIRED_DIMENSION_MISSING_SCORE = 0
REQUIRED_DIMENSION_MEDIAN_LT_2 = 0

LITERATURE_PRODUCT_WEAKNESS = CONFIRMED
HISTORICAL_PRODUCT_WEAKNESS = NOT_YET_FINAL

V3_HOLDOUT_AUTHORIZED = false

Contract V3 本身我接受。现在 System 和 tool description 都明确建立了 search=LOCATE / get=READ，并且明确规定 ABSTRACT_AVAILABLE ≠ 已读摘要、不得靠 metadata 推断学者的具体主张；这正是我们需要的 one-brain scholarly policy。

而 SCHOL_CAL3 也证明它不再只是纸面合同：8/8 发布、8/8 repair 收敛，4 个 case 发起 scholarly search，2 个 case 进入 source fetch。

不过这里还有两个 reviewer 必须纠正的 measurement 问题。

第一，CAL3 真正的 content evidence 是 2，不是 4。

现在 calibration runner 的：

Python
Run
SCHOLARLY_EVIDENCE_COUNT

仍然只是：

Python
Run
len(SCHOLARLY_EVIDENCE_RECORD_IDS)

也就是 fetch 后产生的 evidence-record 数，并没有使用我们已经在 Evidence Contract 中建立的：

scholarly_content_evidence_count

。

而 Evidence Contract 本身明明已经区分了：

scholarly_fetch_result_count
scholarly_content_evidence_count

。

查看 CAL3 原始 artifact 可以直接确认四个 fetch result 的真实组成：

H02:
2 × METADATA_ONLY
2 × content_evidence=false

H07:
2 × ABSTRACT_AVAILABLE
2 × content_evidence=true

。

因此准确口径应该是：

SCHOLARLY_FETCH_RESULT_COUNT = 4
SCHOLARLY_CONTENT_EVIDENCE_COUNT = 2

这不会推翻 read activation——因为 2 > 0，READ 确实激活了——但说明“读深度”仍然比回执里的 EVIDENCE_COUNT=4 更有限。

第二，也是我现在不直接授权 Historical Contract patch 的原因：primary evidence replay 仍没有完全闭合。

CAL3 judge artifact 里：

S9:
READ_CHAPTERS_RECORDED = 3
MATERIALIZED = 0
FAILED = 3

精神现象学#1
法哲学原理#2
精神现象学#4

而 H03：

RECORDED = 1
MATERIALIZED = 0
FAILED = 1

存在与时间#0

。

也就是说我们修掉了“前 12 个 scare quotes 挤掉真 evidence”的问题，但旧 run 中存在两类 read_chapters identity：

canonical:
c5013f33fe01#4

legacy:
存在与时间#0
精神现象学#1

当前 replay 只认识前者。

这尤其重要，因为 HD 只差：

3.40 - 3.25 = 0.15

在 measurement 尚有 4 个已读章节未进入 judge 的情况下，我不会先假定这 0.15 一定是 Agent 的历史纪律缺陷。

相反，Literature weakness 已经可以确认。 H04 的 primary replay 是完整的，但 literature median 仍只有 2，因为它自己明确表示没有实际检索二手文献；judge 指出的缺项也是“笛卡尔循环/争论没有具体二手研究支撑”。 H13 同样已经有完整 primary replay，却仍是 literature=2，理由仍是具体二手研究不足。

所以现在的根因树应该改成：

search scholarship                  ✅
read scholarly source               ✅ 已激活
content evidence                    ✅ 但覆盖不足

primary judge evidence parity       ⚠ legacy keys 未闭合

literature orientation              ❌ confirmed
historical discipline               ? 先完成 parity

还有一个 provenance 小问题：我在 7b57e0c6b → 27f1ddc50 的最终 tracked diff 中看到了 PROBE V3、SCHOL_CAL3 和 CAL3 judge artifacts，但没有看到你所说的 SCHOL_CAL2_REJUDGE_PARITY artifact 被归档。82fef92b0 的 M1–M5 measurement 修复本身确实存在并且测试了真实 CAL2 artifact， 但回执里的 3.4 / 4.0 / 3.25 / 2.875 这组 rejudge 数字，目前不能算 repo 内 canonical evidence。这个不用重新跑 Agent。

O7-E PF-RP4B — Final Measurement Closure

模型仍然：

IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 27f1ddc50

NEW_AGENT_RUN = false
SCHOLARLY_CONTRACT_CHANGE = false
LOCAL_PATCH_CHANGE = false
PRODUCTION_MODEL_CHANGE = false

V3_HOLDOUT_RUN = false

只做一次最后的 measurement micro-patch，然后重判同一个 CAL3。不要再动产品。

_materialize_read_chapters() 支持 legacy read key，但只能机械解析。对于：

存在与时间#0
精神现象学#1

优先从同一次 run 已有 evidence records建立 exact mapping：

(book title, chapter_idx)
→
(book_id, chapter_idx)

只允许唯一 exact match。

禁止 fuzzy title matching、网络查询、post-hoc 新书库检索。

记录：

recorded_key
resolved_key
resolution_mode =
  CANONICAL_ID
  RUN_EVIDENCE_EXACT_ALIAS

CAL3 hard：

READ_CHAPTERS_MATERIALIZE_FAILED = 0
JUDGE_NEW_PRIMARY_SOURCE_IDS = 0

如果已有 read_chapters 无法机械 replay，则 scholarly evaluation 应：

EVALUATION_INVALID = true

而不是继续静默评分。

calibration summary 正式拆：

SCHOLARLY_SOURCE_FETCH_CALLS
SCHOLARLY_FETCH_RESULT_COUNT
SCHOLARLY_CONTENT_EVIDENCE_COUNT

废弃模糊的：

SCHOLARLY_EVIDENCE_COUNT

CAL3 当前 artifact 的预期机械复算是：

FETCH_RESULT_COUNT = 4
CONTENT_EVIDENCE_COUNT = 2

content_evidence 真值应来自实际 returned evidence，而不是仅凭 record existence。

把已经执行过的 SCHOL_CAL2_REJUDGE_PARITY artifact 从 _tmp 归档到 docs/evidence。如果本地 artifact 已经不存在，就如实写：

SCHOL_CAL2_REJUDGE_ARCHIVE = UNAVAILABLE

不要为历史 baseline 重跑 Agent。

对现有：

docs/evidence/o7e_calib_SCHOL_CAL3.json

重新跑一次 judge：

SCHOL_CAL3_REJUDGE_FINAL_PARITY
NEW_AGENT_RUN=false

然后才做最终轴诊断。

Gate 不变：

HISTORICAL_DISCIPLINE >= 3.40
LITERATURE_ORIENTATION >= 3.20

如果最终变成：

HD >= 3.40
LO < 3.20

下一阶段只修 literature coverage。

如果：

HD < 3.40
LO < 3.20

下一阶段同时进入：

Scholarly Coverage
+
Historical Discipline

如果两者都过且 fatal=0，则才：

V3_HOLDOUT_AUTHORIZED=true

回执：

O7_E_PF_RP4B =
READY_FOR_REVIEW /
SCHOLARLY_GATE_NOT_MET

BASE_SHA=27f1ddc50

LEGACY_REPLAY_SHA=
METRIC_CLOSURE_SHA=
CAL3_REJUDGE_SHA=

HEAD_SHA=
REMOTE_SHA=

NEW_AGENT_RUN=false

LEGACY_READ_KEY_RESOLUTION=true
FUZZY_BOOK_MATCHING=false
POSTHOC_PRIMARY_RETRIEVAL=0

READ_CHAPTERS_RECORDED=
READ_CHAPTERS_MATERIALIZED=
READ_CHAPTERS_MATERIALIZE_FAILED=

JUDGE_NEW_PRIMARY_SOURCE_IDS=0

SCHOLARLY_FETCH_RESULT_COUNT=
SCHOLARLY_CONTENT_EVIDENCE_COUNT=
LEGACY_SCHOLARLY_EVIDENCE_COUNT_REMOVED=

SCHOL_CAL2_REJUDGE_ARCHIVED=

JUDGE_CASES_VALID=8
EVALUATION_INVALID=

APPLICABLE_DIMENSION_MEAN=
TEXTUAL_GROUNDING_REQUIRED_MEAN=
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN=
INTERPRETIVE_PLURALITY_REQUIRED_MEAN=
HISTORICAL_DISCIPLINE_REQUIRED_MEAN=
LITERATURE_ORIENTATION_REQUIRED_MEAN=

REQUIRED_DIMENSION_MEDIAN_LT_2=
REQUIRED_DIMENSION_MISSING_SCORE=

ALL_FATAL_FLAGS=

LOCAL_PATCH_CHANGED=false
SCHOLARLY_CONTRACT_CHANGED=false
PRODUCTION_MODEL_CHANGED=false

V3_HOLDOUT_RUN=false

PROPOSED_VERDICT=
AUTHORIZE_V3_HOLDOUT /
SCHOLARLY_PRODUCT_PATCH_REQUIRED

STOP

这一轮已经非常接近我们要的状态了。8/8 delivery、fatal=0、argument=4、textual=3.875 都说明主干已经稳定。

但不能因为接近就把 3.0 ≥ 3.2 算过去。现在把最后这层 measurement parity 补齐，再决定究竟只补 Literature，还是 Literature + Historical。