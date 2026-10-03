# O7-A JR1-R1 Final Receipt（glm-4.6 全量资格复验）

> 运行环境说明（如实披露）: 本轮 Stage-2 重验因换机中断后在 **macOS 新机器**上重启执行
> （Windows → macOS 迁移）。代码树与 QUALIFICATION_GATE 冻结点完全一致
> （HEAD=021675bfc，含 JR1-R1 修复 a59ff74cb；evaluation 文件自冻结后零改动，
> pytest 494 全绿含 T19/R15/T21 production-diff 断言）。旧一轮（中断前）原始产物已归档
> `backend/tools/_tmp/o7a_jr1_full_glm46.json.win-migrated-bak`（未跟踪）。

```text
O7_A_JR1_R1 = READY_FOR_FINAL_REVIEW

BASE_SHA=7dfbcde50

GIT_HYGIENE_SHA=9f9e293dd
JR1_R1_CODE_SHA=a59ff74cb
JR1_R1_QUALIFICATION_GATE_SHA=a59ff74cb
HEAD_SHA=43bd1e2b8
REMOTE_SHA=43bd1e2b8
(回执正文所在 commit；本行回填为后续一笔 docs commit，不改变任何 Gate 数据)

UNRELATED_TMP_FILES_TRACKED_BEFORE=0
UNRELATED_TMP_FILES_TRACKED_AFTER=0
(git ls-files backend/tools/_tmp | wc -l = 0)

C6_L3_ANSWER_HASH_BEFORE=b90f608f089914467d15d2d90e4b4cf15ec0739dd0f8a688dfc8d4a641622329
C6_L3_ANSWER_HASH_AFTER=b90f608f089914467d15d2d90e4b4cf15ec0739dd0f8a688dfc8d4a641622329
C6_L3_ANSWER_UNCHANGED=true

C6_L3_EVIDENCE_BEFORE=supply/claim 失配——fixture 证据宇宙不含 answer 所引 section 的原文支撑（judge 无从核验 → 误报 F6）
C6_L3_EVIDENCE_AFTER=supply/claim 对齐——证据宇宙含所引 section 的原始记录（SECONDARY_SOURCE_RECORDS=1，覆盖 claimed span）
C6_L3_EVIDENCE_PROVENANCE=a59ff74cb fixture evidence supply 修复（evaluation-only fixture 数据补全；semantic judge prompt 零改动）

SEMANTIC_JUDGE_PROMPT_HASH_BEFORE=ab8165fb3a15dfdbfc4afbfc7fe78632f5c68dd6c82cfd6d92411bf18e53751a
SEMANTIC_JUDGE_PROMPT_HASH_AFTER=ab8165fb3a15dfdbfc4afbfc7fe78632f5c68dd6c82cfd6d92411bf18e53751a
(sha256(JUDGE_SYSTEM_PROMPT)，逐字节相等)

STAGE1_RERUN=false

FATAL_RECALL_A=100% (12/12)
FATAL_RECALL_B=100% (12/12)

F1_RECALL=100% (FABRICATED_BIBLIOGRAPHY)
F2_RECALL=100% (FABRICATED_SCHOLAR_ATTRIBUTION)
F3_RECALL=100% (PRIMARY_TEXT_MISREPRESENTATION)
F4_RECALL=100% (MAJOR_ANACHRONISM)
F5_RECALL=100% (FALSE_EXACT_QUOTE, mechanical authority)
F6_RECALL=100% (LITERATURE_ACCESS_OVERCLAIM)

FALSE_FATAL_A=0 (false_fatal_assertions=[]，no-fatal 断言池 21)
FALSE_FATAL_B=0 (false_fatal_assertions=[]，no-fatal 断言池 21)

C6_L3_F6_A=False (majority 0/3，上轮误报未复现)
C6_L3_F6_B=False (majority 0/3)

FATAL_FLAG_AGREEMENT=100% (32/32 repeat pairs；上轮 F6-M4 上 A 多报 F2 的分歧本轮未复现——A/B 均 F6=F2=植入且仅植入)

DIMENSION_DIFF_LE1=100% (32/32；max_dim_abs_diff>0 仅 C3-mid/C6-mid/F6-M5-good 各 1)
PER_DIM_APPLICABILITY=98.1% (per-dimension applicability exact agreement)
REQUIRED_NA_CONTRADICTIONS=0

ANTI_LUCK_FATAL_RECALL=100% (7/7)
ANTI_LUCK_FALSE_FATAL=0 (false_fatal_fixtures=[])

SCHEMA_FAILURES=0
MECHANICAL_F5_FALSE_POSITIVE=0

PRODUCTION_DIFF=0 (pytest T19/R15/T21 git-diff 断言全过)

FULL_TEST_COMMAND=.venv/bin/python -m pytest backend/tests -q
COLLECTED=494
PASSED=494
FAILED=0
SKIPPED=0

RECOMMENDED_JUDGE_MODEL=glm-4.6

O7_B_AUTHORIZED=false

PROPOSED_VERDICT=PASS
STOP
```

## 附：GOOD/MID/BAD 排序与稳定性诊断（如实全量）

- Ensemble A: good_mean=3.389, mid_mean=2.229, bad_mean=0.222, ordering_ok=true
- Ensemble B: good_mean=3.542, mid_mean=2.250, bad_mean=0.222, ordering_ok=true
- whole_vector_exact_agreement_diagnostic=0.906（诊断值，非 Gate 项）

原始产物: `backend/tools/_tmp/o7a_jr1_full_glm46.json`（未跟踪，本机唯一副本+换机归档 bak）。
