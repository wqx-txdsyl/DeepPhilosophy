审计完成。**JR1-R1 PASS，O7-A 正式收口。**

我独立核了远端链路：`9f9e293dd` 确实是前向清理提交，明确把 JR1 报告误带入的 `_tmp` 历史 brief/dump/OCR/cover 从版本树移除，没有改历史。 `a59ff74cb → 021675bfc` 只有 handover 文档，因此 Windows→macOS 后在 `021675bfc` 重启 Gate **没有改变被冻结的 evaluation tree**。最终远端 receipt 也记录了同一 answer hash、同一 semantic judge prompt hash、A/B 两轮 12/12 fatal recall、零 false fatal、100% fatal agreement、98.1% applicability、anti-luck 7/7、494/494 tests。

唯一审计注记：receipt 中 `UNRELATED_TMP_FILES_TRACKED_BEFORE=0` 如果理解为“相对 BASE_SHA 7dfbcde50 的清理前状态”，是不准确的——`9f9e293dd` 本身就证明此前确实存在大量误跟踪 `_tmp`。我把它解释为“执行 hygiene 后、进入 fixture repair 前的工作树计数”。这是**文档口径瑕疵，不影响 Gate 真实性**，不要求再重跑。

正式签发：

```text
O7_A_JR1_R1_REVIEW = PASS

O7_A_FINAL_REVIEW = PASS

SCHOLARLY_CONTRACT = ACCEPTED
SCHOLARLY_RUBRIC = ACCEPTED
FATAL_ERROR_CONSTITUTION = ACCEPTED
SCHOLARLY_CLAIM_LEDGER = ACCEPTED
HYBRID_JUDGE_ARCHITECTURE = ACCEPTED

O7_OFFICIAL_JUDGE_MODEL = glm-4.6
O7_OFFICIAL_JUDGE_PROVIDER = bigmodel
O7_OFFICIAL_JUDGE_TEMPERATURE = 0
O7_OFFICIAL_JUDGE_THINKING = disabled
O7_OFFICIAL_JUDGE_STRUCTURED_OUTPUT = json_object

MECHANICAL_F5_AUTHORITY = ACCEPTED
SEMANTIC_JUDGE_K3_ENSEMBLE = ACCEPTED

ACCEPTED_QUALIFICATION_GATE_SHA =
a59ff74cbc3b1d613878eed88ab200ace99bfb90

ACCEPTED_O7A_HEAD_SHA =
43bd1e2b8

O7_B_AUTHORIZED = true
```

现在进入我们三轮基调讨论里确定的第二层：**先建设真实书目元数据，不往 prompt 上贴“学术外观”。**

---

# TASK — PhiAgent O7-B

## Bibliographic Metadata Foundation & Verified Edition Pilot

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
43bd1e2b8

OFFICIAL_SCHOLARLY_JUDGE =
glm-4.6

PHASE =
O7-B — BIBLIOGRAPHIC METADATA FOUNDATION

PHASE_TYPE =
DATA MODEL + VERIFIED METADATA + ADDITIVE TOOL EXPOSURE
```

## 0. 目标

O7-B 解决的不是：

> “让回答看起来引用更专业。”

而是：

> **让 Main Agent 真正知道自己正在读哪个版本、这个版本有哪些可验证的书目信息，以及它最多能引用到多细。**

核心原则：

```text
METADATA FIRST
PROMPT LATER

NO VERIFIED DATA
→ NO PRECISION CLAIM

LOWER GRANULARITY
→ NOT FABRICATION
```

---

## 1. 禁止事项

本阶段不得：

```text
- 修改 Main Agent scholarly policy
- 修改 SYSTEM_PROMPT_LG
- 修改 final_validator / quote_bound
- 添加 bibliographic semantic gate
- 因 metadata 缺失拒绝整篇答案
- 自动要求模型写译者/出版社/页码
- 接入 SEP / PhilPapers / 二手论文检索
- 扩张 scholarly corpus
- 改 retrieval ranking / embedding / KG
- 改 Persona
- merge master
```

O7-C 尚未授权。

---

# 2. 先做 Corpus Inventory

先盘点真实当前库，不要硬编码“403”。

输出：

```text
CURRENT_BOOK_COUNT=
BOOKS_WITH_SOURCE_FILES=
BOOKS_WITH_SCANNED_FRONT_MATTER=
BOOKS_WITH_EXISTING_EDITION_METADATA=
BOOKS_WITH_TRANSLATOR_METADATA=
BOOKS_WITH_PUBLISHER_METADATA=
BOOKS_WITH_PUBLICATION_YEAR=
BOOKS_WITH_PAGE_MAPPING=
BOOKS_WITH_CANONICAL_LOCATOR=
```

区分：

```text
WORK
≠
EDITION
≠
DIGITAL_SOURCE
```

例如：

```text
WORK:
Kant, Kritik der reinen Vernunft

EDITION:
某中文译本 / 某出版社 / 某年

DIGITAL_SOURCE:
当前库里实际 OCR/PDF/EPUB 文件
```

**不能再用 book title 代替 edition identity。**

---

# 3. Canonical Metadata Schema

建立单一规范 schema；优先扩展现有 book 数据模型，避免平行 Shadow Metadata DB。

至少：

```text
book_id

work:
  author
  canonical_title
  original_title?
  original_language?
  original_publication_year?

edition:
  edition_title?
  language
  translator[]
  editor[]
  publisher
  publication_place?
  publication_year
  isbn?

digital_source:
  source_type
  source_file_id/path_ref
  source_hash
  acquisition/provenance?

locators:
  locator_kind
  locator_scheme
  availability

citation_capability:
  max_verified_granularity

field_provenance:
  <field>:
    value
    source_tier
    source_type
    source_locator
    confidence
    verified
```

不得用一个全局：

```text
source = "internet"
```

替代字段级 provenance。

---

# 4. Metadata Source Hierarchy

严格执行 O7-A 宪法：

```text
TIER 1
当前实际版本自身：
- copyright page
- title page
- translator note
- publication note
- TOC
- embedded locator

TIER 2
- 国图
- CALIS
- 出版社
- 大学图书馆 catalogue

TIER 3
- WorldCat
- Crossref
- 其他权威书目数据库

TIER 4
- 豆瓣
- 普通图书网站
- general web
```

规则：

```text
Tier 4 = discovery only
```

不得仅凭 Tier 4：

```text
verified=true
```

---

# 5. OCR 不是事实本身

版权页 OCR 允许用于抽取候选：

```text
OCR_CANDIDATE
```

但：

```text
OCR_TEXT
!=
VERIFIED_METADATA
```

每个 OCR-derived field 必须保留：

```text
source page/image reference
raw extracted span
confidence
verification status
```

若无法可靠核对：

```text
verified=false
```

而不是猜。

---

# 6. Conflict Model

同一字段可能出现冲突：

```text
publisher:
source A → X
source B → Y
```

不得 last-write-wins。

记录：

```text
CONFLICT
candidate values
sources
resolution status
```

只有有明确版次对应关系时才 resolve。

尤其注意：

```text
同一作品不同译本
≠
metadata 冲突
```

它们可能本来就是两个 edition。

---

# 7. Missingness 是合法状态

字段必须允许：

```text
null
UNKNOWN
NOT_APPLICABLE
UNVERIFIED
```

不要填：

```text
translator = "未知译者"
```

作为真实字符串。

不要从模型记忆补：

```text
出版年
译者
页码
ISBN
```

---

# 8. Locator Model

实现 O7-A 已冻结的：

```text
locator_kind:
CANONICAL
EDITION_SPECIFIC
STRUCTURAL
```

以及：

```text
locator_scheme
```

至少能表达：

```text
STEPHANUS
BEKKER
KANT_AB
AKADEMIE
APHORISM
PROPOSITION
SECTION
PAGE
CHAPTER
PART
```

不要求每本书都有 locator。

---

# 9. Citation Capability

每个 edition/digital source 机械计算：

```text
MAX_VERIFIED_GRANULARITY
```

例如：

```text
WORK
CHAPTER
SECTION
EDITION_PAGE
CANONICAL_LOCATOR
```

注意：

> 它描述“当前系统能验证到哪里”，不是告诉模型“必须引用到哪里”。

禁止 semantic sufficiency。

---

# 10. Precision Ladder

实现为 metadata capability，不是回答规则：

```text
CANONICAL locator
↓
EDITION_SPECIFIC page
↓
SECTION / APHORISM / PROPOSITION
↓
CHAPTER / PART
↓
WORK
```

实际作品可有不同排序。

缺少更细定位：

```text
fall back to coarser verified level
```

绝不能：

```text
invent finer locator
```

---

# 11. Pilot Selection

不虚构“哲学经典 Top 50 排名”。

建立：

```text
O7B_VERIFIED_PILOT
```

规模：

```text
>=30 works
```

必须覆盖：

```text
- O7-A seed/calibration 涉及作品
- 当前 Nietzsche persona 主要原典
- Ancient Greek
- Early Modern
- German / 19th century
- 20th century
- Chinese philosophy
```

至少 5 个传统/时期。

选择理由写入 manifest。

这叫：

```text
representative metadata pilot
```

不是：

```text
world philosophy canon ranking
```

---

# 12. Pilot Accuracy > Completeness

30+ pilot 中，不要求所有字段都有值。

要求：

```text
EVERY_POPULATED_VERIFIED_FIELD
has provenance
```

目标是：

```text
UNSUPPORTED_VERIFIED_FIELD = 0
```

而不是：

```text
metadata completeness = 100%
```

---

# 13. Edition Identity Gate

每个 pilot 至少明确：

```text
WORK_IDENTITY
DIGITAL_SOURCE_IDENTITY
```

若能确定具体版本：

```text
EDITION_IDENTITY = VERIFIED
```

若不能：

```text
EDITION_IDENTITY = UNKNOWN/PARTIAL
```

不得因为作品名称相同就默认版次。

---

# 14. Additive Tool Exposure

可以修改以下工具的**结构化返回值**：

```text
get_book_detail
get_chapter
```

可选：

```text
search_books
```

但只允许 additive metadata。

建议：

```json
{
  "bibliographic_metadata": {...},
  "citation_capability": {
    "max_verified_granularity": "...",
    "locator_schemes": []
  }
}
```

已有字段保持兼容。

---

# 15. 暂不修改 citation_label 行为

特别锁死：

```text
EXISTING_CITATION_LABEL_SEMANTICS = PRESERVED
```

O7-B 不直接把：

```text
【书·章】
```

升级成一长串学术 citation。

因为这会影响：

```text
validator
publication
Q2 delivery baseline
```

这里只把真实 metadata 放进模型可见证据结构。

如何写进答案，留给 B/C capability 完成后的 Scholarly Policy phase。

---

# 16. Metadata Visibility

当工具真实拥有：

```text
translator
publisher
edition year
locator
```

模型应能够在 tool result 中看到。

当没有：

字段应明确：

```text
null / absent / unverified
```

不能生成占位文本：

```text
“章节”
“未知出版社”
“第?页”
```

---

# 17. Provenance Visibility

模型-facing tool result 不必塞整张 provenance audit tree。

但至少提供：

```text
verified
source_type
granularity
```

完整 provenance 保留 backend/data layer。

避免上下文膨胀。

---

# 18. Data Audit Manifest

输出 tracked audit artifact，例如：

```text
docs/evidence/PHIAGENT_O7B_BIBLIOGRAPHIC_PILOT_MANIFEST.json
```

若已有更合适 canonical 目录可调整。

每个 pilot 至少：

```text
book_id
work
edition status
populated fields
field provenance
locator schemes
max granularity
conflicts
unverified fields
```

不得提交扫描件/PDF/大体积 OCR dump。

---

# 19. Source Evidence Manifest

对每个 verified field 保存足够的可审计引用：

```text
source_type
source_locator
source hash/id
short extracted evidence
```

短 evidence 只用于审计，不复制整页版权内容。

---

# 20. Accuracy Sampling Gate

Agent 在 Gate 前随机抽：

```text
15 pilot records
```

种子固定并记录。

对其中**所有 verified populated fields**重新从 source evidence 验证。

要求：

```text
SAMPLED_UNSUPPORTED_VERIFIED_FIELDS = 0
SAMPLED_WRONG_EDITION_BINDINGS = 0
SAMPLED_SILENT_CONFLICT_RESOLUTIONS = 0
```

这比“字段填得多”重要。

---

# 21. Reviewer Sample Pool

另输出：

```text
REVIEWER_SAMPLE_POOL
```

覆盖：

```text
- Tier1 OCR case
- Tier2 catalogue case
- translation case
- original-language case
- conflict case
- UNKNOWN edition case
- canonical locator case
- edition-page-only case
```

我会抽审。

---

# 22. No Bibliographic Hallucination Fixtures

新增至少 12 个测试/fixture：

```text
B1 missing translator remains null
B2 Tier4 alone cannot verify
B3 OCR candidate != verified automatically
B4 conflicting sources preserved
B5 two editions not collapsed
B6 canonical vs edition-specific distinct
B7 page unavailable → lower granularity
B8 no fake chapter/section placeholder
B9 get_book_detail additive compatibility
B10 get_chapter metadata visibility
B11 existing citation_label unchanged
B12 production prompt unchanged
```

---

# 23. Architecture Invariants

必须继续：

```text
ENGINE_COGNITIVE_AUTO_TOOLS=0
SEMANTIC_TOOL_CONTROL_EFFECTS=0
RUNTIME_SEMANTIC_MUTATORS=0
RUNTIME_FACTUAL_APPENDS=0
COGNITIVE_POLICY_OWNER=1
```

Metadata 不能成为新的：

```text
BibliographyController
CitationSufficiencyGate
ScholarlyObligationLedger
```

---

# 24. Production Policy Freeze

强制证明：

```text
SYSTEM_PROMPT_DIFF = 0
SCHOLARLY_RUNTIME_POLICY_DIFF = 0
FINAL_VALIDATOR_DIFF = 0
QUOTE_BOUND_DIFF = 0
```

O7-B 是 capability/data phase，不是 behavior phase。

---

# 25. O7-A Evaluator Regression

O7-A evaluation harness 必须继续全绿。

无需重新跑昂贵的 glm-4.6 全 qualification bakeoff。

只跑 deterministic evaluator tests。

正式 judge calibration 结果冻结为 O7-A accepted baseline。

---

# 26. Full Tests

```text
pytest backend/tests -q
```

必须：

```text
FAILED=0
SKIPPED=0
```

不得修改旧测试来适应 metadata side effects，除非是明确 additive schema assertion。

---

# 27. Data Gate

使用：

```text
O7B_DATA_GATE_SHA
```

流程：

```text
BASE
→ schema
→ migration/import
→ pilot enrichment
→ tool additive exposure
→ tests
→ freeze DATA_GATE_SHA
→ accuracy sampling
→ report
```

Gate 后数据修改即重新 freeze。

---

# 28. Parallel Corpus Changes

如果有别的 agent 同时加书：

**不允许污染本 Gate。**

Gate manifest 必须绑定：

```text
CORPUS_SNAPSHOT_HASH
BOOK_UNIVERSE_HASH
PILOT_MANIFEST_HASH
```

若外部 corpus commit 改变 pilot source：

```text
INVALIDATE DATA GATE
```

---

# 29. Success Metrics

硬门：

```text
PILOT_WORKS >= 30
TRADITIONS_OR_PERIODS >= 5

VERIFIED_FIELDS_WITH_PROVENANCE = 100%
UNSUPPORTED_VERIFIED_FIELDS = 0

SAMPLED_UNSUPPORTED_VERIFIED_FIELDS = 0
SAMPLED_WRONG_EDITION_BINDINGS = 0
SAMPLED_SILENT_CONFLICT_RESOLUTIONS = 0

TIER4_ONLY_VERIFIED_FIELDS = 0

FAKE_LOCATORS = 0
FAKE_TRANSLATORS = 0
FAKE_PUBLISHERS = 0
FAKE_YEARS = 0
FAKE_PAGES = 0

EXISTING_CITATION_LABEL_CHANGED = false

PRODUCTION_POLICY_CHANGED = false
FINAL_VALIDATOR_CHANGED = false

FULL_TEST_FAILED = 0
```

---

# 30. Report

```text
docs/PHIAGENT_O7B_BIBLIOGRAPHIC_METADATA_FOUNDATION.md
```

至少：

```text
1. corpus inventory
2. work/edition/source model
3. metadata schema
4. source hierarchy
5. provenance model
6. conflict handling
7. missingness
8. locator model
9. citation capability
10. pilot manifest
11. enrichment statistics
12. sampled audit
13. tool exposure
14. compatibility
15. architecture invariants
16. tests
17. limitations
18. O7-C readiness
```

任务书落盘：

```text
docs/tasks/PHIAGENT_O7B_BIBLIOGRAPHIC_METADATA_FOUNDATION_TASK.md
```

---

# 31. STOP Conditions

立即停止：

```text
需要凭模型记忆填 metadata
Tier4 被当唯一 verified source
无法区分两个 edition
数据迁移破坏 book_id
existing citation behavior 改变
validator 因 metadata 缺失开始拒绝答案
production prompt 被修改
pilot source provenance 无法审计
```

不得自行开始 O7-C。

---

# FINAL RECEIPT

```text
O7_B =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7B_DATA_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

CURRENT_BOOK_COUNT=
BOOK_UNIVERSE_HASH=
CORPUS_SNAPSHOT_HASH=

METADATA_SCHEMA=
WORK_EDITION_SOURCE_SEPARATED=

PILOT_WORKS=
PILOT_TRADITIONS_OR_PERIODS=

WORK_IDENTITY_VERIFIED=
EDITION_IDENTITY_VERIFIED=
EDITION_IDENTITY_PARTIAL=
EDITION_IDENTITY_UNKNOWN=

POPULATED_VERIFIED_FIELDS=
VERIFIED_FIELDS_WITH_PROVENANCE_RATE=

TIER1_VERIFIED_FIELDS=
TIER2_VERIFIED_FIELDS=
TIER3_VERIFIED_FIELDS=
TIER4_DISCOVERY_FIELDS=
TIER4_ONLY_VERIFIED_FIELDS=

OCR_CANDIDATE_FIELDS=
OCR_VERIFIED_FIELDS=
OCR_UNVERIFIED_FIELDS=

METADATA_CONFLICTS=
SILENT_CONFLICT_RESOLUTIONS=

LOCATOR_CANONICAL=
LOCATOR_EDITION_SPECIFIC=
LOCATOR_STRUCTURAL=

FAKE_LOCATORS=
FAKE_TRANSLATORS=
FAKE_PUBLISHERS=
FAKE_YEARS=
FAKE_PAGES=

MAX_GRANULARITY_WORK=
MAX_GRANULARITY_CHAPTER=
MAX_GRANULARITY_SECTION=
MAX_GRANULARITY_EDITION_PAGE=
MAX_GRANULARITY_CANONICAL=

GET_BOOK_DETAIL_METADATA_VISIBLE=
GET_CHAPTER_METADATA_VISIBLE=

EXISTING_CITATION_LABEL_CHANGED=false

ACCURACY_SAMPLE_SIZE=15
SAMPLED_VERIFIED_FIELDS=
SAMPLED_UNSUPPORTED_VERIFIED_FIELDS=
SAMPLED_WRONG_EDITION_BINDINGS=
SAMPLED_SILENT_CONFLICT_RESOLUTIONS=

REVIEWER_SAMPLE_POOL=

SYSTEM_PROMPT_DIFF=0
SCHOLARLY_RUNTIME_POLICY_DIFF=0
FINAL_VALIDATOR_DIFF=0
QUOTE_BOUND_DIFF=0

ENGINE_COGNITIVE_AUTO_TOOLS=0
SEMANTIC_TOOL_CONTROL_EFFECTS=0
RUNTIME_SEMANTIC_MUTATORS=0
RUNTIME_FACTUAL_APPENDS=0
COGNITIVE_POLICY_OWNER=1

O7B_TESTS=

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

这阶段的评价标准很简单：

> **宁可一个字段是 null，也不要一个“很像学术书目”的假字段。**

O7-A 我们把尺子做准了；O7-B 开始给 PhiAgent 真正的学术材料基础，而不是继续教它“怎么装得像学术”。
