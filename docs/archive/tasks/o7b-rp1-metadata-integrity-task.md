审计后，**O7-B 不能签 PASS，需要一个窄但必须做的 RP1。**

我先确认好的部分：`43bd1e2b8 → 9edf34775` 只有 O7-A receipt 修订和 O7-B task book，因此你把 `9edf34775` 作为执行 BASE 可以接受；`9edf → e373` 的生产改动也基本符合授权范围，只涉及 metadata builder、tool additive exposure、tests 和 manifest，没有越权去改 Main Agent/validator。

但我独立抽审数据后发现了 **3 个硬 blocker + 2 个必须一起修的 instrumentation 缺口**。

最严重的是，`单向度的人` 被写成：

```text
translator = "上海"
verified = true
```

而 provenance 两条所谓“独立证据”其实都是从 **“上海译文出版社”** 中截出的 `上海译`。manifest 明确把它当成 verified translator。 真实版权页同一行则清楚写的是 **“刘继译……上海译文出版社”**。

因此这些申报不能成立：

```text
FAKE_TRANSLATORS=0
UNSUPPORTED_VERIFIED_FIELDS=0
VERIFIED_FIELDS_WITH_PROVENANCE_RATE=100%   # provenance存在≠provenance语义正确
```

第二个 blocker 是**运行时数据没有进入冻结 tree**。builder 自己明确写着：

```text
backend/data/book_bibliography.json
（运行时数据，未跟踪）
```

而 production route 遇到这个文件不存在时直接退化成空 metadata。换句话说：**本机 pytest 可以因为本地生成文件存在而全绿，但 clean checkout 的 O7-B 功能会消失。** 这不满足 DATA_GATE 的可复现性。

第三个 blocker 是 conflict model 实际没有实现。builder 在 manifest 里直接固定：

```python
"conflicts": []
```

同时 B4 所谓“conflicts preserved”测试实际上只检查每个 provenance 里有 `evidence` 键，根本没有构造两个竞争值并验证“不静默选赢家”。B5 也只检查 `book_id` 唯一，无法证明两个 edition 不会被折叠。

另外两个一起修掉：当前代码从作者国别标记如 `（德）` 推导 `original_language_hint`，甚至在重复出现时升级为 verified 并写进 `work.original_language`。国籍不是作品原文语言，这条 provenance 逻辑本身不成立。 以及这次“15 records 仅抽到 3 个 verified fields + 同 extractor 重抽 25/25”的 audit 也被 `translator="上海"` 证明不足以发现**语义错误的 extraction**。

正式裁定：

```text
O7_B_REVIEW = PATCH_REQUIRED

SCHEMA_DIRECTION = ACCEPTED
METADATA_FIRST_DIRECTION = ACCEPTED
TOOL_ADDITIVE_EXPOSURE = ACCEPTED
PILOT_COVERAGE = ACCEPTED
ARCHITECTURE_BOUNDARY = ACCEPTED

DATA_ACCURACY_GATE = NOT_ACCEPTED
CONFLICT_MODEL = NOT_IMPLEMENTED
CLEAN_CHECKOUT_REPRODUCIBILITY = NOT_ACCEPTED

O7_B_RP1_AUTHORIZED = true
O7_C_AUTHORIZED = false
```

# TASK — O7-B RP1

## Metadata Integrity, Conflict Semantics & Reproducible Runtime Data

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
9aaef1ed3

PHASE =
O7-B RP1 — METADATA INTEGRITY CLOSURE
```

### 0. Scope

只修：

```text
1. false verified metadata
2. conflict preservation
3. work/edition/source identity proof
4. clean-checkout runtime-data reproducibility
5. independent field-level accuracy audit
```

禁止：

```text
- Main Agent prompt
- scholarly runtime policy
- validator / quote_bound
- retrieval redesign
- Tier2/3 接入
- 新 corpus
- SEP / PhilPapers
- O7-C
```

---

## 1. Freeze Known Bad Case

必须先把当前错误冻结成 regression：

```text
BOOK =
2c1a4c7d17a4

SOURCE =
“……刘继译．—上海：上海译文出版社……”

BAD_CURRENT_RESULT =
translator = 上海
verified = true
```

新增测试：

```text
“上海译文出版社”
MUST NOT produce translator="上海"

expected translator candidate/value =
刘继
```

不能只给这个 book_id 特判。

---

## 2. General Translator Extractor Fix

translator parser 必须满足一般规则。

例如支持：

```text
刘继译
卫茂平 译
涂又光译
某某等译
```

但禁止从：

```text
上海译文出版社
翻译出版社
译文版
译本
```

抽名字。

建议约束：

```text
译 后必须是：
line end / punctuation / whitespace-boundary

不得紧跟：
文 / 本 / 版 / 丛 / 社
```

并利用 responsibility-statement context，而不是裸：

```regex
[\u4e00-\u9fa5]{2,5}译
```

新增至少 8 个 positive/negative metamorphic cases。

---

## 3. Rebuild All 39 Pilot Records

不能只修 `单向度的人`。

完整重建：

```text
PILOT_WORKS=39
```

然后重新计算：

```text
POPULATED_VERIFIED_FIELDS
OCR_CANDIDATE_FIELDS
EDITION_IDENTITY_*
FAKE_*
```

旧数字 25 不要求保住。

> 少几个 verified 字段完全可以；错一个不可以。

---

## 4. Delete Nationality → Original Language Inference

当前：

```text
（德）
→ de
→ original_language
```

不允许。

正式规则：

```text
AUTHOR_NATIONALITY
!=
WORK_ORIGINAL_LANGUAGE
```

只有 source 明确支持语言事实，例如：

```text
原文语种
原版语言
明确的原文 bibliographic record
```

才能：

```text
work.original_language = verified value
```

否则：

```text
null
```

可以保留一个非模型-facing：

```text
author_nationality_hint
```

但不能叫 `original_language_hint`，也不能参与 `work.original_language`。

---

## 5. Implement a Real Conflict Model

不能再：

```text
pick most frequent
discard alternatives
conflicts=[]
```

每个字段至少表达：

```json
{
  "candidates": [
    {
      "value": "...",
      "evidence": [],
      "semantic_source_type": "..."
    }
  ],
  "selected_value": null,
  "resolution_status": "NO_CONFLICT | CONFLICT_UNRESOLVED | RESOLVED",
  "resolution_basis": null
}
```

如果两个 eligible candidate 不同：

```text
CONFLICT_UNRESOLVED
→ production field = null
```

除非有明确、更高权威的 resolution basis。

禁止 majority-wins。

---

## 6. Publication Year Semantics

特别修年号混淆。

以下不是同一事实：

```text
publication / edition year
printing year
CIP registration year
copyright year
```

`edition.publication_year` 只能由明确支持出版/版次的 evidence 得出。

例如：

```text
2020年第1版
```

可支持 edition year。

```text
CIP数据核字（2020）
```

不能单独支持 publication_year。

```text
2020年第1次印刷
```

是 printing 信息，不能自动等同 edition year。

若：

```text
CIP bibliographic line = 2019
edition line = 2020
```

必须保留候选语义和差异，不能因为“2020 出现两次”就静默赢。

---

## 7. B4 Must Become a Real Test

构造 synthetic fixture：

```text
publisher candidate A
publisher candidate B
```

或：

```text
publication_year 2019
publication_year 2020
```

要求：

```text
both candidates retained
conflict recorded
selected production value = null
unless explicit resolution exists
```

删除当前“只要有 evidence key 就算 conflict preserved”的 false-green。

---

## 8. Work / Edition / Digital Source Identity

当前 B5：

```text
all book_id unique
```

不能证明三分离。

schema 至少补：

```text
work_id
edition_record_id
digital_source_id
```

这是**内部实体 identity**，不表示 edition bibliographic identity 已验证。

区分：

```text
edition_record_id exists
≠
edition_identity = VERIFIED
```

增加 synthetic test：

```text
same work_id
+
edition A
+
edition B
+
digital source A/B
```

必须保持两个 edition/source 独立存在。

不得自动按 title 合并真实 corpus。

如果当前库没有已验证的同作异版：

```text
REAL_MULTI_EDITION_CASES=0
```

如实报告。

---

## 9. Runtime Data Must Be in the Gate

正式把：

```text
backend/data/book_bibliography.json
```

作为**版本化 production reference data** 纳入 Git。

它规模很小，不属于 runtime mutation/log。

要求：

```text
git ls-files backend/data/book_bibliography.json
→ exactly 1
```

并在文件中记录：

```text
schema_version
builder_version/hash
source_snapshot_hash
pilot_manifest_hash
```

不得依赖某台机器事先手跑 builder。

---

## 10. Clean Checkout Reproduction Gate

新建临时 clean worktree/checkout，从：

```text
O7B_RP1_DATA_GATE_SHA
```

验证：

```text
book_bibliography.json exists
get_book_detail(pilot) exposes metadata
get_chapter(pilot) exposes metadata
non-pilot behavior unchanged
```

不得复制本机 untracked file进去。

指标：

```text
CLEAN_CHECKOUT_METADATA_VISIBLE=true
CLEAN_CHECKOUT_LOCAL_GENERATION_REQUIRED=false
```

---

## 11. Deterministic Rebuild Identity

在 clean tree 上运行：

```bash
python backend/tools/dp_biblio_build.py
```

重新生成到临时 path 或 compare mode。

要求：

```text
REBUILT_RUNTIME_DATA_HASH
=
TRACKED_RUNTIME_DATA_HASH

REBUILT_MANIFEST_SEMANTIC_HASH
=
TRACKED_MANIFEST_SEMANTIC_HASH
```

不得因为时间戳等非语义字段产生漂移。

---

## 12. Replace the Weak Accuracy Audit

因为当前：

```text
15 records
→ only 3 verified fields sampled
```

而且同 extractor 重跑没抓出 `"上海"`。

RP1 对当前规模直接做：

```text
ALL VERIFIED FIELDS
```

的 semantic evidence audit。

如果 rebuild 后 verified fields ≤ 40：

```text
AUDIT_RATE = 100%
```

每个 verified field 必须记录：

```text
book_id
field
value
raw evidence spans
semantic evidence class
SUPPORTS_FIELD_SEMANTICS = true/false
```

不是“regex 能重新抽出来”就算支持。

---

## 13. Specific Semantic Audit Rules

至少：

```text
ISBN
→ evidence 真的是 ISBN field

translator
→ evidence 真的是 responsibility statement

publisher
→ evidence 真的是 publisher statement

publication_year
→ evidence 真的是 publication/edition year

original_language
→ evidence 真的是语言事实

locator
→ evidence 真正符合对应 locator scheme
```

要求：

```text
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS = 0
```

---

## 14. Reviewer Pool

重新输出，至少包含：

```text
translator positive
translator publisher-collision negative
publication-year semantic case
conflict case
UNKNOWN edition
canonical locator
OCR candidate
verified ISBN
```

如果 Tier2 和 edition-page 本阶段仍不存在：

继续如实写 `N/A`，不补假样本。

---

## 15. Runtime Tool Exposure

保持：

```text
get_book_detail
get_chapter
```

additive。

不得修改 citation label。

如果 metadata field 有 conflict：

模型-facing：

```text
field = null
verified = false / unavailable
```

不要把 competing candidate 猜一个给模型。

---

## 16. Original Language Exposure Regression

测试：

```text
（德）某作者
```

不能单独产生：

```text
original_language=de
```

如果未来 source 明确说：

```text
原文为德语
```

才可验证。

---

## 17. Conflict Regression Matrix

至少：

```text
C1 no conflict → verified candidate
C2 two equal evidence values → no conflict
C3 two different eligible values → unresolved
C4 lower-quality OCR candidate vs verified explicit source
C5 edition year vs printing year → not treated as same fact
C6 CIP registration year != publication year
```

---

## 18. Production Freeze

继续要求：

```text
SYSTEM_PROMPT_DIFF=0
SCHOLARLY_RUNTIME_POLICY_DIFF=0
FINAL_VALIDATOR_DIFF=0
QUOTE_BOUND_DIFF=0

ENGINE_COGNITIVE_AUTO_TOOLS=0
SEMANTIC_TOOL_CONTROL_EFFECTS=0
RUNTIME_SEMANTIC_MUTATORS=0
RUNTIME_FACTUAL_APPENDS=0
COGNITIVE_POLICY_OWNER=1
```

---

## 19. Tests

新增/修正至少：

```text
R1 上海译文出版社 != translator 上海
R2 real “刘继译” extracts 刘继
R3 translator whitespace case
R4 publisher negative variants

R5 nationality != original_language

R6 candidate conflicts preserved
R7 unresolved conflict publishes null
R8 no majority-wins
R9 year semantic types separated

R10 same work / two editions remain distinct
R11 work/edition/source IDs distinct

R12 runtime bibliography is git-tracked
R13 clean checkout metadata works
R14 deterministic rebuild hash equal

R15 all verified fields semantic-audited
R16 citation_label unchanged
R17 production policy frozen
```

---

## 20. Data Gate

流程：

```text
BASE
→ extractor fixes
→ conflict model
→ identity schema
→ rebuild 39 pilot
→ track runtime data
→ tests
→ freeze O7B_RP1_DATA_GATE_SHA
→ clean-checkout reproduction
→ full semantic field audit
→ report
```

任何 metadata/data 变动后：

```text
REFREEZE
```

---

## 21. Hard PASS Gates

```text
PILOT_WORKS >= 30

FAKE_TRANSLATORS=0
FAKE_PUBLISHERS=0
FAKE_YEARS=0
FAKE_LOCATORS=0
FAKE_PAGES=0

SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS=0

UNRESOLVED_CONFLICTS_EXPOSED_AS_VERIFIED=0
SILENT_CONFLICT_RESOLUTIONS=0

NATIONALITY_AS_ORIGINAL_LANGUAGE=0

RUNTIME_BIBLIO_DATA_TRACKED=true
CLEAN_CHECKOUT_METADATA_VISIBLE=true
DETERMINISTIC_REBUILD_MATCH=true

WORK_EDITION_SOURCE_IDENTITY_MODEL=true

EXISTING_CITATION_LABEL_CHANGED=false

PRODUCTION_DIFF_UNAUTHORIZED=0

FULL_TEST_FAILED=0
```

---

# FINAL RECEIPT

```text
O7_B_RP1 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7B_RP1_DATA_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

PILOT_WORKS=

TRANSLATOR_FALSE_POSITIVE_CASE_FIXED=
MARCUSЕ_TRANSLATOR_VALUE=

ORIGINAL_LANGUAGE_FROM_NATIONALITY_REMOVED=
NATIONALITY_AS_ORIGINAL_LANGUAGE=

WORK_ID_FIELD=
EDITION_RECORD_ID_FIELD=
DIGITAL_SOURCE_ID_FIELD=
REAL_MULTI_EDITION_CASES=

METADATA_CONFLICTS=
UNRESOLVED_CONFLICTS=
SILENT_CONFLICT_RESOLUTIONS=
UNRESOLVED_CONFLICTS_EXPOSED_AS_VERIFIED=

POPULATED_VERIFIED_FIELDS=
SEMANTIC_AUDIT_FIELDS=
SEMANTIC_AUDIT_RATE=
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS=

FAKE_TRANSLATORS=
FAKE_PUBLISHERS=
FAKE_YEARS=
FAKE_LOCATORS=
FAKE_PAGES=

RUNTIME_BIBLIO_DATA_TRACKED=
TRACKED_RUNTIME_DATA_HASH=

CLEAN_CHECKOUT_METADATA_VISIBLE=
CLEAN_CHECKOUT_LOCAL_GENERATION_REQUIRED=

REBUILT_RUNTIME_DATA_HASH=
DETERMINISTIC_REBUILD_MATCH=

GET_BOOK_DETAIL_METADATA_VISIBLE=
GET_CHAPTER_METADATA_VISIBLE=
EXISTING_CITATION_LABEL_CHANGED=false

SYSTEM_PROMPT_DIFF=0
SCHOLARLY_RUNTIME_POLICY_DIFF=0
FINAL_VALIDATOR_DIFF=0
QUOTE_BOUND_DIFF=0

ENGINE_COGNITIVE_AUTO_TOOLS=0
SEMANTIC_TOOL_CONTROL_EFFECTS=0
RUNTIME_SEMANTIC_MUTATORS=0
RUNTIME_FACTUAL_APPENDS=0
COGNITIVE_POLICY_OWNER=1

O7B_RP1_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7B_BIBLIOGRAPHIC_METADATA_FOUNDATION.md

O7_C_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP
```

这次最关键的发现不是“正则写错了一个名字”，而是：

> **“两行 OCR 一致”只能证明提取结果重复出现，不能证明它在语义上就是那个 bibliographic field。**

`上海译文出版社 → 上海译 → translator=上海` 正好把这个区别暴露出来了。

所以 O7-B 的 RP1 不该继续追求字段数量，而是把 **字段语义、冲突语义和 clean-checkout 可复现性**真正做实。做完这轮，我们再决定是否授权 O7-C。
