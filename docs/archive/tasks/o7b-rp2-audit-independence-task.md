我审完了。**这轮比首轮扎实很多，核心数据错误已经修掉，clean-checkout 和 conflict model 也真正落地了；但我仍不能签 O7-B PASS。需要一个很窄的 RP2，原因不是生产数据已发现新错，而是“证明这些数据正确”的两项关键 instrumentation 仍有 false-green。**

正式裁定：

```text
O7_B_RP1_REVIEW = PATCH_REQUIRED

TRANSLATOR_FALSE_POSITIVE_FIX = ACCEPTED
NATIONALITY_LANGUAGE_SEPARATION = ACCEPTED
CONFLICT_MODEL_RUNTIME_BEHAVIOR = ACCEPTED
TRACKED_RUNTIME_REFERENCE_DATA = ACCEPTED
CLEAN_CHECKOUT_REPRODUCIBILITY = ACCEPTED
DETERMINISTIC_REBUILD = ACCEPTED
TOOL_ADDITIVE_EXPOSURE = ACCEPTED
PRODUCTION_BOUNDARY = ACCEPTED

SEMANTIC_AUDIT_INDEPENDENCE = NOT_ACCEPTED
MULTI_EDITION_IDENTITY_PROOF = NOT_ACCEPTED
TEST_TRUTHFULNESS = PATCH_REQUIRED

O7_B_RP2_AUTHORIZED = true
O7_C_AUTHORIZED = false
```

先说已经通过的部分。你的 conflict 实现现在确实不是首轮那个 `conflicts=[]` 空壳了：字段保留 candidates，只有唯一 eligible value 才 verified；多个 eligible 异值会 `CONFLICT_UNRESOLVED → selected=null`。年份逻辑也明确只让 `EDITION_YEAR / CIP_BIBLIOGRAPHIC_YEAR` 参与 publication-year 资格，printing / CIP registration 不参与。

clean-checkout 这一项也是真门：脚本从指定 SHA 建 detached worktree，确认 `book_bibliography.json` 已跟踪，然后直接在 clean tree import 工具、验证 pilot metadata/non-pilot compatibility，再从该 tree 重建并比较哈希。这项我接受。

模型-facing exposure 也符合边界：冲突字段只给 null + `conflict_fields`，没有把 competing candidates 塞给 Main Agent；citation label 没变。

而且当前 22 个 verified 字段的审计产物，从肉眼抽看来看已经比上一轮健康得多：例如卫茂平、张竹明、王柯平、涂又光这些 translator 的 evidence span 都是真正的“姓名+译”责任陈述，`单向度的人` 已经不再把“上海”列为 verified translator。

但下面两个问题不能放过去。

---

## Blocker 1：所谓“独立语义审计”实际上复用了 extractor 自己的 regex

这是本轮最关键的问题。

`dp_biblio_sample.py` 文档写的是：

> 语义支持判定不是「regex 能重新抽出来」

但代码直接：

```python
from dp_biblio_build import
    RE_TRANSLATOR,
    RE_ISBN,
    RE_PUBLISHER
```

然后 translator audit 又用：

```python
RE_TRANSLATOR.search(...)
```

publisher 也用同一 production extractor regex。

这意味着：

```text
Extractor 有系统性错误
        ↓
Audit 使用同一规则
        ↓
Audit 很可能复现同一错误
        ↓
“22/22 semantic audit PASS”
```

这正是上一轮 `上海译文出版社 → 上海译 → translator=上海` 会暴露的问题类型。

所以现在的：

```text
SEMANTIC_AUDIT_RATE=100%
```

是真的——覆盖率确实 100%。

但：

```text
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS=0
```

还不能被我视为**独立证据**。

它目前更像：

```text
second deterministic consistency check
```

而不是真正的：

```text
independent semantic audit
```

---

## Blocker 2：R10 名称写着 synthetic multi-edition test，实际没有 synthetic case

测试代码：

```python
def test_r10_two_editions_distinct():
    """synthetic: 同 work_id 两个 edition/source 必须独立存在。"""
```

但下面根本没有构造两个 edition。

它只是读取当前真实库：

```python
recs = list(_load()["books"].values())
```

然后按 `work_id` 分组检查 ID 唯一。

而你自己又正确披露：

```text
REAL_MULTI_EDITION_CASES=0
```

于是这个测试很可能是**vacuous pass**：

```text
现实库没有同 work_id 两条记录
→ 每组只有 1 条
→ edition_record_id 当然 unique
→ test PASS
```

它并没有证明：

```text
same work
edition A + edition B
digital source A + B
```

真的不会被 builder/data model 折叠。

这不是说当前 schema 一定坏了，而是你 receipt 里的：

> “R10 合成双 edition 不折叠已验证”

与代码事实不一致。

---

## 另外一个明确的 test smell

R9 里面有：

```python
assert "PRINTING_YEAR" not in classes or True
```

这个 assertion 永远为真。

好消息是，R9 前面的行为断言已经间接证明 printing-year 没影响 selected year，所以我**不把它单独升级成第三个功能 blocker**。

但这种：

```text
assert condition or True
```

必须清掉。

我们的 Gate 现在已经走到学术数据层了，不能允许测试看起来检查了一个 invariant，实际上永远 PASS。

---

# TASK — O7-B RP2

## Independent Metadata Audit & Test-Truth Closure

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
d4e97d10a

PHASE =
O7-B RP2 — INDEPENDENT AUDIT & TEST TRUTH CLOSURE

SCOPE =
EVALUATION / TEST / DATA-INTEGRITY ONLY
```

### 0. 本轮原则

**不要再改已经工作的 production extractor，除非独立审计真的发现新数据错误。**

默认：

```text
PRODUCTION_METADATA_LOGIC_CHANGED = false
ROUTES_CHANGED = false
SCHEMA_CHANGED = false
PILOT_SELECTION_CHANGED = false
```

只解决：

```text
A. semantic audit independence
B. real multi-edition synthetic proof
C. false-green assertions
```

---

## 1. Freeze RP1 Data First

先记录：

```text
RP1_RUNTIME_DATA_HASH =
bf7ad52559f32a791d1cd5ed9030c6a0ee4cb93c5f009346a522949d6e2dc543

RP1_VERIFIED_FIELDS =
22
```

RP2 默认不得修改：

```text
backend/data/book_bibliography.json
```

如果 independent audit 发现实际错字段，则进入 §8 数据修复流程，否则 runtime data hash 必须保持不变。

---

# 2. Independent Audit Must Not Import Extractor Rules

新增/重写 audit validator。

禁止：

```python
from dp_biblio_build import RE_TRANSLATOR
from dp_biblio_build import RE_PUBLISHER
from dp_biblio_build import RE_ISBN
```

也禁止间接调用：

```text
extract_front_matter()
_field_from_found()
production candidate classifier
```

来证明它们自己正确。

要求：

```text
AUDIT_IMPORTS_PRODUCTION_EXTRACTOR_RULES = 0
```

---

# 3. Audit 原则：验证 evidence semantics，不重新跑 extraction

对每个 verified field，audit 输入直接取：

```text
field
selected_value
raw evidence spans
semantic source types
```

然后做**独立字段契约验证**。

例如 translator：

不是：

```text
“production regex 能再次匹配这个 span”
```

而是独立检查：

```text
1. evidence span 明确包含 selected name
2. name 后存在独立的“译”职责标记
3. “译”不是另一个词的一部分
4. selected name 不来自 publisher/title token
5. 至少两个独立 source positions
```

实现可以用另一套简单 parser / token boundary logic，但不得共享 production regex object。

---

# 4. Independence Sentinel

必须增加一个专门证明“独立 audit 能抓到 production-style bug”的 fixture。

例如人为构造 audit row：

```text
field = translator
value = 上海
evidence =
[
  "上海译文出版社",
  "上海译文出版社"
]
```

Independent audit 必须：

```text
SUPPORTS_FIELD_SEMANTICS=false
```

再构造：

```text
value = 刘继
evidence =
[
  "刘继译",
  "刘继 译"
]
```

必须 true。

这次不要通过 production extractor 先生成 row。

---

# 5. Independent Audit Coverage

继续审：

```text
ALL VERIFIED FIELDS
```

当前预期：

```text
22/22
```

输出：

```text
AUDIT_IMPLEMENTATION =
INDEPENDENT

AUDIT_SHARED_EXTRACTION_RULES =
0
```

每条 row 最好增加：

```text
audit_rule_id
audit_reason
supporting_spans
rejected_spans
```

尤其 publication year 应明确：

```text
supporting spans:
CIP_BIBLIOGRAPHIC_YEAR / EDITION_YEAR

ignored spans:
PRINTING_YEAR / CIP_REGISTRATION_YEAR
```

不要再把一整组 mixed evidence 用：

```text
semantic_evidence_class = CIP_BIBLIOGRAPHIC_YEAR
```

一个标签概括掉。

---

# 6. 真正实现 Synthetic Multi-Edition Test

这次 R10 必须真的构造：

```text
work_id = work-same

record A:
  edition_record_id = ed-A
  digital_source_id = ds-A

record B:
  edition_record_id = ed-B
  digital_source_id = ds-B
```

验证：

```text
same work_id
different edition IDs
different digital source IDs

records count = 2
no overwrite
no merge
```

如果需要增加一个 evaluation-only helper 来验证 entity model，可以。

禁止把 synthetic fixture 写进 production bibliography。

---

# 7. 再加一个 Work Identity Boundary Case

由于当前：

```text
work_id = hash(author + canonical_title)
```

至少测试：

```text
same author + same canonical_title
→ same work_id

same work + edition metadata changes
→ work_id unchanged

edition_record_id changes
→ work_id unchanged
```

不要求 O7-B RP2 解决：

```text
不同译名如何 canonicalize 到同一 work
```

那是后续 bibliographic authority / reconciliation 问题。

但把 limitation 写清：

```text
WORK_IDENTITY_CURRENTLY_TITLE_AUTHOR_DERIVED = true
CROSS_TITLE_WORK_RECONCILIATION = NOT_IMPLEMENTED
```

不要假装已经解决。

---

# 8. If Independent Audit Finds a Real Error

如果新的 audit 得出：

```text
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS > 0
```

立即：

```text
RP2_DATA_REPAIR_REQUIRED = true
```

然后才允许：

```text
fix extractor
rebuild 39 pilot
update runtime data
re-freeze DATA_GATE_SHA
rerun clean checkout
rerun deterministic rebuild
rerun complete independent audit
```

若发现错误，不能只修改 audit 让它 PASS。

---

# 9. Remove False-Green R9

删掉：

```python
assert "PRINTING_YEAR" not in classes or True
```

换成真正行为断言。

例如：

```text
CIP=2019
EDITION=2019
PRINTING=2020

→ selected publication_year = 2019
→ no conflict caused by PRINTING_YEAR
```

以及：

```text
only PRINTING_YEAR + CIP_REGISTRATION_YEAR
→ publication_year must NOT verify
```

这两个比检查集合字符串更直接。

---

# 10. Static Test-Truth Scan

对 O7-B test 文件扫描以下危险模式：

```text
or True
if False
assert True
pass-only branch
vacuous loop over possibly-empty required fixture
```

不是禁止 Python 合法使用这些语法，而是必须证明：

```text
NO_KNOWN_ALWAYS_TRUE_GATE_ASSERTIONS
```

---

# 11. R10 Non-Vacuity Assertion

Synthetic test 内明确：

```python
assert len(records_for_same_work) == 2
```

然后再测 uniqueness。

这样以后不能再：

```text
0/1 条数据
→ 自动 PASS
```

---

# 12. Report RP1 Audit Limitation Honestly

在现有 closeout 或 RP2 report 中记录：

```text
RP1 semantic audit covered 100% fields
but reused production extraction regex for some field types,
therefore coverage was complete but independence was not.

RP2 replaces this with independent evidence-semantic validation.
```

不改写 RP1 历史。

---

# 13. Clean Checkout

如果 runtime data hash **没有变化**：

无需再做完整 DATA rebuild gate 两遍。

但仍跑一次现有：

```text
dp_biblio_cleancheck.py <RP2_GATE_SHA>
```

确认 tests/evaluation 改动没破坏 reproducibility。

如果 runtime data 变化：

完整重跑 O7-B RP1 data gate。

---

# 14. Production Freeze

仍要求：

```text
SYSTEM_PROMPT_DIFF=0
SCHOLARLY_RUNTIME_POLICY_DIFF=0
FINAL_VALIDATOR_DIFF=0
QUOTE_BOUND_DIFF=0

ROUTES_DIFF_FROM_RP1=0
```

除非 §8 发现真实 metadata bug；即使如此 routes 仍通常不应变化。

---

# 15. Tests

至少：

```text
T1 audit does not import production extractor regex

T2 fake translator 上海 + 上海译文出版社 → audit false

T3 genuine translator 刘继 → audit true

T4 genuine publisher → audit true

T5 ISBN evidence semantics → true

T6 publication year support classes separated

T7 printing-only cannot verify publication year

T8 CIP-registration-only cannot verify publication year

T9 synthetic same-work two editions exists exactly 2

T10 two edition_record_ids distinct

T11 two digital_source_ids distinct

T12 same work_id preserved across edition differences

T13 R10 cannot vacuously pass

T14 no always-true R9 assertion

T15 all 22 verified fields independently audited

T16 clean checkout remains reproducible

T17 production frozen
```

---

# 16. PASS Gate

必须：

```text
INDEPENDENT_SEMANTIC_AUDIT = true
AUDIT_SHARED_EXTRACTION_RULES = 0

SEMANTIC_AUDIT_RATE = 100%
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS = 0

SYNTHETIC_MULTI_EDITION_CASES >= 1
SYNTHETIC_MULTI_EDITION_NON_VACUOUS = true
MULTI_EDITION_COLLAPSE = 0

ALWAYS_TRUE_GATE_ASSERTIONS = 0

RUNTIME_DATA_HASH_CHANGED = false
```

若因真实错误修了数据：

最后一项改成：

```text
RUNTIME_DATA_CHANGE_JUSTIFIED = true
NEW_DATA_GATE_COMPLETE = true
```

---

# 17. Full Regression

```bash
.venv/bin/python -m pytest backend/tests -q
```

要求：

```text
FAILED=0
SKIPPED=0
```

---

# FINAL RECEIPT

```text
O7_B_RP2 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7B_RP2_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

RP1_RUNTIME_DATA_HASH=
RP2_RUNTIME_DATA_HASH=
RUNTIME_DATA_HASH_CHANGED=

INDEPENDENT_SEMANTIC_AUDIT=
AUDIT_IMPORTS_PRODUCTION_EXTRACTOR_RULES=
AUDIT_SHARED_EXTRACTION_RULES=

SEMANTIC_AUDIT_FIELDS=
SEMANTIC_AUDIT_RATE=
SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS=

TRANSLATOR_FAKE_SENTINEL=
TRANSLATOR_GOOD_SENTINEL=

PUBLICATION_YEAR_SUPPORT_CLASS_TEST=
PRINTING_ONLY_NOT_PUBLICATION=
CIP_REG_ONLY_NOT_PUBLICATION=

SYNTHETIC_MULTI_EDITION_CASES=
SYNTHETIC_MULTI_EDITION_NON_VACUOUS=
SAME_WORK_ID_PRESERVED=
EDITION_IDS_DISTINCT=
DIGITAL_SOURCE_IDS_DISTINCT=
MULTI_EDITION_COLLAPSE=

WORK_IDENTITY_CURRENTLY_TITLE_AUTHOR_DERIVED=true
CROSS_TITLE_WORK_RECONCILIATION=NOT_IMPLEMENTED

ALWAYS_TRUE_GATE_ASSERTIONS=

CLEAN_CHECKOUT_METADATA_VISIBLE=
DETERMINISTIC_REBUILD_MATCH=

SYSTEM_PROMPT_DIFF=0
SCHOLARLY_RUNTIME_POLICY_DIFF=0
FINAL_VALIDATOR_DIFF=0
QUOTE_BOUND_DIFF=0
ROUTES_DIFF_FROM_RP1=0

O7B_RP2_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7B_RP2_AUDIT_INDEPENDENCE_CLOSEOUT.md

O7_C_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP
```

这轮不应该再很大。**RP1 的数据修复方向我已经认可；RP2 的任务只是让“证明它正确的尺子”也独立可信。**

尤其是这句话要锁住：

> **Extractor 和 auditor 如果共享同一个识别规则，它们的一致只能证明自洽，不能证明正确。**

RP2 把这两个 false-green 拆掉以后，如果没有发现新的实际 metadata 错误，我预计 O7-B 就可以正式收口并进入 O7-C。
