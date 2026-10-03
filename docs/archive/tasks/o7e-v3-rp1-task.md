
我审完 bfbc12e04 → 2c224d7c3。这次不能签 O7_E_PASS。问题不是边缘解释，而是最终仓库里的 canonical judge summary 与回执有一个直接决定 Gate 的冲突。

实际 V3_FINAL_HOLDOUT_JUDGE_summary.json 写的是：

REQUIRED_DIMENSION_MEDIAN_LT_2 = 2

不是回执中的 0。而我们冻结的 Scholarly Gate 明确要求：

REQUIRED_DIMENSION_MEDIAN_LT_2 = 0

所以 V3 的 scholarly hard gate 失败。

更值得警惕的是，HEAD commit message 本身还写着 MEDIAN_LT_2=0 → PASS，但同一个 commit 加进去的 summary 明明是 2。也就是说这次不是 judge 算错，而是最终回执/结论层读错了 canonical artifact。

正式裁定：

O7_E_V3_FINAL_HOLDOUT_REVIEW = V3_SCHOLARLY_GATE_NOT_MET

V3_DELIVERY_GATE = PASS
V3_PUBLICATION = 28/28
V3_REPAIR_CONVERGENCE = 27/27

JUDGE_CASES_VALID = 28
EVALUATION_INVALID = false

APPLICABLE_DIMENSION_MEAN = 3.572           PASS
TEXTUAL_GROUNDING_REQUIRED_MEAN = 3.893     PASS
ARGUMENT_RECONSTRUCTION_REQUIRED_MEAN = 4.0 PASS
INTERPRETIVE_PLURALITY_REQUIRED_MEAN = 3.235 PASS
HISTORICAL_DISCIPLINE_REQUIRED_MEAN = 3.786 PASS
LITERATURE_ORIENTATION_REQUIRED_MEAN = 3.321 PASS

ALL_FATAL_FLAGS = 0

REQUIRED_DIMENSION_MISSING_SCORE = 0
REQUIRED_DIMENSION_MEDIAN_LT_2 = 2           FAIL

O7_E_PASS = false
O7_E_STATUS = NOT_CLOSED

其余大的链路我接受。V3 delivery summary 确实是 28/28、repair convergence 1.0、所有 Local Patch 机械门为绿。 Freeze V3.1 也确实补进了 evidence_contract.py，而且生产冻结集完整。 Preflight gate audit 在 holdout 调用前记录了 HOLDOUT_MODEL_CALLS_AT_AUDIT=0，最终 artifact commit 的父提交也正是 freeze/preflight commit efdefbb8d，所以没有看到中途 product patch 的迹象。

另外两个回执数字也要纠正，但不影响 Gate：真实 V3 summary 是

SCHOLARLY_FETCH_RESULT_COUNT = 24
SCHOLARLY_CONTENT_EVIDENCE_COUNT = 13

不是 FETCH_RESULT_COUNT=13。

Freeze V3.1 还有一个 docs-only provenance typo：SUPERSEDES 写成了 O7E_PRODUCTION_FREEZE_V3 (72b553dec manifest)；72b553dec 实际是旧 V2 freeze，真正 V3 是 ad1bca77d。这不改变运行结果，但最终 closeout 前要修。

现在不能直接 patch 后重跑这 28 题

这一点很重要。

这 28 个 V3 case 已经被看过结果，因此：

V3_HOLDOUT_CONSUMED = true

后面根据其中两个 tail failure 修改产品之后，不能再把同一 28 题称作 untouched final holdout。

所以先做一个完全离线、零 API 的 tail audit，找出那两个 <2 的 REQUIRED 维到底是哪两个 case、为什么低。然后我再根据真实失败模式决定 product patch；修完后必须用新的 untouched holdout 做最终资格测试。

下一任务：O7-E V3-RP1 — Tail Failure Audit
IMPLEMENTATION_MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 2c224d7c3

NEW_AGENT_RUN = false
NEW_JUDGE_RUN = false

PRODUCTION_CHANGE = false
PROMPT_CHANGE = false
JUDGE_CHANGE = false
REPLAY_CHANGE = false
GATE_CHANGE = false

只做离线机械提取：

SOURCE =
docs/evidence/V3_FINAL_HOLDOUT_JUDGE.json
docs/evidence/V3_FINAL_HOLDOUT_JUDGE_summary.json
docs/evidence/o7e_calib_V3_HOLDOUT.json

必须生成：

docs/evidence/V3_TAIL_FAILURE_AUDIT.json

对所有：

applicability == REQUIRED
and median < 2

逐项记录：

case_id
question
dimension
median

vote_scores[3]
vote_rationales[3]
supporting_spans
missing_requirements

answer_relevant_spans

scholarly_search_calls
scholarly_fetch_calls
content_evidence_count
access_levels

read_chapters_recorded
read_chapters_materialized
read_chapters_materialize_failed

fatal_flags

Hard：

TAIL_FAILURE_COUNT = 2

SOURCE_SUMMARY_REQUIRED_DIMENSION_MEDIAN_LT_2 = 2

NO_POSTHOC_REJUDGE = true
NO_NEW_RETRIEVAL = true

同时新增一个evaluation-only deterministic final-gate check，避免以后再出现“artifact=2、receipt=0”：

tools/evaluation/o7e_final_gate.py

它只读取 summary，不做任何语义判断，按冻结阈值输出：

DELIVERY_GATE
SCHOLARLY_GATE
FINAL_VERDICT
FAILED_GATES[]

对当前 V3 必须机械得到：

DELIVERY_GATE = PASS
SCHOLARLY_GATE = FAIL
FAILED_GATES = ["REQUIRED_DIMENSION_MEDIAN_LT_2"]
FINAL_VERDICT = V3_SCHOLARLY_GATE_NOT_MET

并加 regression：

artifact MEDIAN_LT_2=2
→ 无论 commit message / receipt 写什么
→ final gate 必须 FAIL

顺手修正 Freeze V3.1 的 SUPERSEDES 文案，但不得改历史 V3 artifact 的数值。

回执只要：

O7_E_V3_RP1 = READY_FOR_REVIEW

BASE_SHA=2c224d7c3

TAIL_AUDIT_SHA=
FINAL_GATE_CHECK_SHA=
FREEZE_DOC_FIX_SHA=

HEAD_SHA=
REMOTE_SHA=

NEW_AGENT_RUN=false
NEW_JUDGE_RUN=false

V3_HOLDOUT_CONSUMED=true

TAIL_FAILURE_COUNT=2

TAIL_1_CASE=
TAIL_1_DIMENSION=
TAIL_1_MEDIAN=

TAIL_2_CASE=
TAIL_2_DIMENSION=
TAIL_2_MEDIAN=

FINAL_GATE_CHECK_DELIVERY=PASS
FINAL_GATE_CHECK_SCHOLARLY=FAIL
FINAL_GATE_CHECK_FAILED_GATES=REQUIRED_DIMENSION_MEDIAN_LT_2

CANONICAL_FETCH_RESULT_COUNT=24
CANONICAL_CONTENT_EVIDENCE_COUNT=13

PRODUCTION_CHANGED=false
PROMPT_CHANGED=false
JUDGE_CHANGED=false

PROPOSED_VERDICT=V3_SCHOLARLY_GATE_NOT_MET

STOP

这次其实已经很接近成功了：所有均值、全部 fatal、28/28 delivery 都过了，失败只藏在两个 REQUIRED tail cell 里。 但 REQUIRED_DIMENSION_MEDIAN_LT_2 这个门当初就是专门为了防止“总体平均很好，却有个别必需维度塌掉”而设的，所以现在不能把它跳过去。

先把这两个 tail failure 精确剖出来。之后我们只修真实问题，不再动 measurement。