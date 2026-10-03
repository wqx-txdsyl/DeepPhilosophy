裁定选 **(α)**。不接受带偏差直接签发。

```text id="x7l1v9"
O7_A_JR1_REVIEW = PATCH_REQUIRED

JUDGE_BAKEOFF_DIRECTION = ACCEPTED
GLM_4_6 = PROVISIONAL_WINNER
GLM_4_6_OFFICIAL = false

OPTION_ALPHA = AUTHORIZED
OPTION_BETA = REJECTED

O7_B_AUTHORIZED = false
```

原因很简单：现在已经定位出 **C6-L3-good 本身是坏尺子**——答案声称“第一节……”，但 supplied full-text evidence 只覆盖第二/三节；glm-4.6 判 F6 在语义上反而是对的。远端报告也明确记录了这一点。

因此如果现在选 β，相当于：

> 明知测试夹具有错，却用“书面豁免”绕过自己刚建立的 Constitution Gate。

没必要。现在 glm-4.6 已经非常接近 qualified，花一轮干净复验把证据闭环，比留下永久例外更值。

但我独立审 Git 时发现了一个**额外必须先处理的问题**：`33a34bb26 → 7dfbcde50` 这个号称“docs report”的最后提交，实际上还一次性加入了大量 `backend/tools/_tmp/` 内容，包括旧 O2/O3/O6 task brief、历史 gate dump、OCR 文本、cover 图片等，与 JR1 报告无关。`7dfbcde50` 的 commit message 虽然是记录 JR1 bakeoff，但 diff 明显夹带了这些临时资产。

这**不推翻** JR1 的实验结果，因为你 Stage-2 冻结的是 `33a34bb26`，而污染发生在后续 report commit；但 `7dfbcde50` 不能直接作为下一轮干净 gate base。

所以 α 要加一个 **Git hygiene pre-gate**。

# TASK — O7-A JR1-R1

## Fixture Integrity Repair + glm-4.6 Final Qualification

```text id="x8g4aw"
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
7dfbcde50...

PROVISIONAL_JUDGE =
glm-4.6

STATUS =
JR1 BAKEOFF COMPLETE
GLM-4.6 = SOLE SURVIVOR
OFFICIAL JUDGE = NOT YET SIGNED
```

## 0. Scope

只允许三件事：

```text id="aswe8z"
1. 清理 JR1 report commit 的 git 临时文件污染
2. 修正 C6-L3-good 的 evidence supply/claim mismatch
3. 用 glm-4.6 完整重跑 Stage-2 qualification
```

禁止：

```text id="o25pws"
- 改 judge semantic prompt
- 改 rubric
- 改 fatal definitions
- 改 answer fixture text
- 改 C6-L3-good 的 claim
- 降 gate
- 把 96.9% agreement 改成“够用了”
- 重跑已淘汰模型
- 改 production
- 开 O7-B
```

---

## 1. Git Hygiene First — Mandatory

先审计 commit：

```text id="tbzf8f"
7dfbcde50
```

输出：

```text id="5qhufs"
JR1_REPORT_COMMIT_FILES
INTENDED_FILES
UNINTENDED_TMP_FILES
UNINTENDED_BINARY_FILES
UNRELATED_HISTORICAL_FILES
```

我已确认远端存在大量不应随 JR1 report 进入版本树的 `_tmp` 历史资产。

必须用**新的 forward cleanup commit**处理：

```text id="777fqs"
NO HISTORY REWRITE
NO FORCE PUSH
```

对于错误提交进 Git 的临时文件：

```text id="ng2rkx"
untrack/remove from repository tree
```

不要求删除本机原始 evaluation artifact。

若确实需要持久化某些 JR1 raw results，只保留明确属于：

```text id="blak37"
O7-A / JR1 / current calibration provenance
```

的最小集合。

旧：

```text id="s8m0ti"
O1/O2/O3/O4/O5/O6 dumps
OCR batch
cover images
unrelated build scripts
```

不得以 JR1 report 的名义留在新增 tree 中。

完成后：

```text id="h3b1ax"
GIT_HYGIENE_SHA=
```

并证明：

```text id="8k2tkf"
UNRELATED_TMP_FILES_TRACKED_FROM_7DF = 0
```

---

# 2. C6-L3 修复原则

**只修 evidence fixture，不改被评 answer。**

Before：

```text id="qdpu63"
ANSWER CLAIM:
“第一节界定……”
```

而 supplied evidence：

```text id="u5e7s9"
only section 2/3
```

这是 fixture bug。

After：

```text id="my6ghx"
same answer
+
supplied FULL_TEXT_READ evidence genuinely includes
the first-section passage supporting that claim
```

必须记录：

```text id="3q6or1"
C6_L3_ANSWER_HASH_BEFORE=
C6_L3_ANSWER_HASH_AFTER=
```

要求完全一致。

同时：

```text id="tgbe0v"
SEMANTIC_JUDGE_PROMPT_HASH_BEFORE
=
SEMANTIC_JUDGE_PROMPT_HASH_AFTER
```

---

# 3. 不允许“补一个看起来支持的假 passage”

新增的第一节 evidence 必须来自 fixture 原本意图模拟的同一文献/同一 source universe，并与 claim 对齐。

如果当前 calibration fixture 本身使用的是合成学术材料，则要遵守其既有 synthetic-fixture provenance；如果基于真实文本，则必须用真实对应文本。

不能为了过 gate 临时写一句：

```text id="i8b0vd"
“第一节界定了语言游戏的描写性进路。”
```

然后当证据。

报告必须说明：

```text id="j9evft"
C6_L3_EVIDENCE_PROVENANCE=
WHY_NEW_EVIDENCE_IS_VALID=
```

---

# 4. Freeze New Qualification Tree

修完：

```text id="gdw4mu"
git hygiene
+
C6-L3 evidence only
```

以后 freeze：

```text id="fe6y4z"
JR1_R1_QUALIFICATION_GATE_SHA=
```

从此开始不得修改：

```text id="8c36ui"
fixture
expected labels
judge prompt
quote probe
aggregator
schema
glm-4.6 config
```

---

# 5. 不需要重跑 Stage-1

Stage-1 结果保留：

```text id="xxgjms"
glm-4.6 = PASS
glm-4.5-air = ELIMINATED
glm-4-flash = ELIMINATED
```

原因：

C6-L3-good 是 Stage-2 fixture 修复，不影响 Stage-1 淘汰逻辑。

不得浪费时间重新 bakeoff。

---

# 6. 重新跑完整 Stage-2

必须重新：

```text id="ymc39g"
32 fixtures
×
k=3
×
2 independent ensembles
```

仍然：

```text id="kn2ppm"
provider = bigmodel
model = glm-4.6
temperature = 0
thinking = disabled
response_format = json_object
max_tokens = 8000
```

不得只重跑 C6-L3。

我们需要验证：

> 修掉坏 fixture 后，整套 measurement system 仍然过门。

---

# 7. Anti-Luck Confirmation 仍必须跑

Stage-2 全 PASS 后：

```text id="se5gwz"
semantic kill cases
+
2 clean negatives
×
k3
```

再跑一轮。

要求：

```text id="qd4xlg"
CONFIRM_FATAL_RECALL=100%
CONFIRM_FALSE_FATAL=0
```

---

# 8. C6-L3 Specific Acceptance

修复后必须：

```text id="r57emg"
C6_L3_GOOD_F6_A = false
C6_L3_GOOD_F6_B = false
```

并且每个 ensemble 内：

```text id="350bsh"
F6 votes
```

完整报告。

如果 glm-4.6 在 evidence 已真正补齐后仍 3/3 判 F6：

那才是真正的 model false positive。

---

# 9. 96.9% Fatal Agreement 不豁免

当前唯一 disagreement：

```text id="eb21tt"
F6-M4-bad
Ensemble A additionally emits F2
Ensemble B does not
```

这个不能因为：

> “反正 F6 是真的”

就忽略。

学术 judge 若把：

```text id="09nj22"
没有伪造 scholar attribution
```

误报成：

```text id="q1upg1"
FABRICATED_SCHOLAR_ATTRIBUTION
```

仍然属于实质错误。

所以正式 Gate 继续要求：

```text id="j3iamh"
ENSEMBLE_FATAL_FLAG_AGREEMENT = 100%
```

如果重跑后仍出现同类额外 fatal disagreement：

```text id="yanb5e"
GLM_4_6 = NOT QUALIFIED
```

不再开 prompt patch。

---

# 10. Hard Gates

必须全部：

```text id="jxx26n"
EXPECTED_FATAL_RECALL_A = 100%
EXPECTED_FATAL_RECALL_B = 100%

F1 = 100%
F2 = 100%
F3 = 100%
F4 = 100%
F5 = 100%
F6 = 100%

FALSE_FATAL_ASSERTIONS_A = 0
FALSE_FATAL_ASSERTIONS_B = 0

FATAL_FLAG_AGREEMENT = 100%

DIMENSION_DIFF_LE1 >= 90%

PER_DIM_APPLICABILITY >= 90%

REQUIRED_NA_CONTRADICTIONS = 0

ANTI_LUCK_FATAL_RECALL = 100%
ANTI_LUCK_FALSE_FATAL = 0

SCHEMA_FAILURES = 0

MECHANICAL_F5_FALSE_POSITIVE = 0
```

以及：

```text id="zsj80w"
PRODUCTION_DIFF = 0
```

---

# 11. Outcome Rules

### 全过

回：

```text id="30w22p"
O7_A_JR1_R1 = READY_FOR_FINAL_REVIEW
RECOMMENDED_JUDGE_MODEL = glm-4.6
```

然后我签：

```text id="3u24as"
O7_OFFICIAL_JUDGE_MODEL = glm-4.6
O7_A_FINAL_REVIEW = PASS
```

之后才会发 O7-B。

### 任一 semantic gate 不过

回：

```text id="3pm0dm"
O7_A_JR1_R1 = BLOCKED_JUDGE_MODEL
```

不要再调 glm-4.6 prompt。

---

# 12. Tests

至少增加/更新：

```text id="2z9r80"
T1 C6-L3 answer hash unchanged
T2 C6-L3 evidence now covers claimed section
T3 semantic judge prompt hash unchanged
T4 Stage-1 results preserved
T5 unrelated JR1 tmp files not tracked
T6 production diff zero
T7 full Stage-2 required after fixture change
T8 fatal agreement still hard 100%
```

全量：

```text id="xkun8l"
pytest backend/tests -q
```

要求：

```text id="nxekhm"
FAILED=0
SKIPPED=0
```

---

# 13. Receipt

```text id="dsd9zd"
O7_A_JR1_R1 =
READY_FOR_FINAL_REVIEW / BLOCKED_JUDGE_MODEL

BASE_SHA=

GIT_HYGIENE_SHA=
JR1_R1_CODE_SHA=
JR1_R1_QUALIFICATION_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

UNRELATED_TMP_FILES_TRACKED_BEFORE=
UNRELATED_TMP_FILES_TRACKED_AFTER=

C6_L3_ANSWER_HASH_BEFORE=
C6_L3_ANSWER_HASH_AFTER=
C6_L3_ANSWER_UNCHANGED=

C6_L3_EVIDENCE_BEFORE=
C6_L3_EVIDENCE_AFTER=
C6_L3_EVIDENCE_PROVENANCE=

SEMANTIC_JUDGE_PROMPT_HASH_BEFORE=
SEMANTIC_JUDGE_PROMPT_HASH_AFTER=

STAGE1_RERUN=false

FATAL_RECALL_A=
FATAL_RECALL_B=

F1_RECALL=
F2_RECALL=
F3_RECALL=
F4_RECALL=
F5_RECALL=
F6_RECALL=

FALSE_FATAL_A=
FALSE_FATAL_B=

C6_L3_F6_A=
C6_L3_F6_B=

FATAL_FLAG_AGREEMENT=

DIMENSION_DIFF_LE1=
PER_DIM_APPLICABILITY=
REQUIRED_NA_CONTRADICTIONS=

ANTI_LUCK_FATAL_RECALL=
ANTI_LUCK_FALSE_FATAL=

SCHEMA_FAILURES=
MECHANICAL_F5_FALSE_POSITIVE=

PRODUCTION_DIFF=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

RECOMMENDED_JUDGE_MODEL=

O7_B_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / JUDGE_MODEL_REJECTED

STOP
```

所以不是 β。

**glm-4.6 已经证明自己值得最后一次正式资格复验，但“很像合格”不等于“已经合格”。**尤其我们刚花这么大力气建立学术评审宪法，现在正是最不应该在最后两条硬门上写 waiver 的时候。

