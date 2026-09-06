审计完成。**O7-B RP2 PASS，O7-B 正式收口，授权 O7-C。**

我独立对远端 `d4e97d10a → 4d2db3ad0` 做了 compare：本轮只新增/修改 evaluator、tests、audit artifact、task/report，**没有改 `dp_biblio_build.py`、routes 或 `book_bibliography.json`**，与 `RUNTIME_DATA_HASH_CHANGED=false` 和 `PRODUCTION_METADATA_LOGIC_CHANGED=false` 一致。

独立审计器也确实不再复用 production extractor：它自己实现 translator token boundary、publisher token、ISBN 和年份 evidence-class 判定；`上海 + 上海译文出版社` 与合法责任陈述是由独立逻辑区分的。 测试层已经把真实 synthetic 双 edition 构造出来，并有明确 `len(rs)==2` 非空转断言；同时清除了 R9 永真断言，22 个 verified fields 全部重新经独立 auditor 校验。

报告也保留了 RP1“覆盖完整但不独立”的历史，而没有改写成首次即正确；当前 clean-checkout、数据 hash 和 production freeze 都保持成立。

正式签发：

```text
O7_B_RP2_REVIEW = PASS
O7_B_FINAL_REVIEW = PASS

BIBLIOGRAPHIC_METADATA_FOUNDATION = ACCEPTED
WORK_EDITION_SOURCE_MODEL = ACCEPTED
FIELD_LEVEL_PROVENANCE = ACCEPTED
CONFLICT_SEMANTICS = ACCEPTED
MISSINGNESS_SEMANTICS = ACCEPTED
CITATION_CAPABILITY_MODEL = ACCEPTED

INDEPENDENT_METADATA_AUDIT = ACCEPTED
CLEAN_CHECKOUT_REPRODUCIBILITY = ACCEPTED
DETERMINISTIC_METADATA_BUILD = ACCEPTED

ACCEPTED_O7B_DATA_SHA =
47641e54022298126ba6ab15d3832d64a779a571

ACCEPTED_O7B_FINAL_SHA =
4d2db3ad0

KNOWN_LIMITATION:
WORK_IDENTITY_CURRENTLY_TITLE_AUTHOR_DERIVED = true
CROSS_TITLE_WORK_RECONCILIATION = NOT_IMPLEMENTED

O7_C_AUTHORIZED = true
```

现在进入 O7-C。这里开始解决第二个真正的学术基础设施缺口：**不是“知道有哪些书”，而是能真正找到、辨认、读取并诚实描述二手学术文献。**

# TASK — PhiAgent O7-C

## Scholarly Retrieval & Literature Access Provenance

```text
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
4d2db3ad0

OFFICIAL_SCHOLARLY_JUDGE =
glm-4.6

PHASE =
O7-C — SCHOLARLY RETRIEVAL & LITERATURE ACCESS PROVENANCE

PHASE_TYPE =
CAPABILITY + SOURCE PROVENANCE
```

## 0. Phase Objective

O7-C 回答：

> PhiAgent 如何找到真实存在的哲学研究文献，并精确知道自己究竟只看到了 metadata、abstract、可获取全文，还是已经真正读取全文？

目标不是：

```text
“让回答多引用几个学者。”
```

而是：

```text
真实 scholarly record
→ 可验证 bibliographic identity
→ access level
→ actual evidence obtained
→ Main Agent
```

锁死：

```text
PAPER_EXISTS
!=
PAPER_READ

FULL_TEXT_AVAILABLE
!=
FULL_TEXT_READ
```

---

# 1. No Production Scholarly Prompt Yet

O7-C **仍然不改 Main Agent 的 Scholarly Contract prompt**。

必须：

```text
SYSTEM_PROMPT_CHANGED = false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false
```

允许：

```text
new scholarly retrieval capability
tool schema/descriptions
mechanical provider adapters
source provenance
access-level state
```

原因：

> B/C 把证据能力造出来以后，再让 Agent 学会如何使用；不能先 prompt 它“引用学者”，逼它在没有文献的情况下编。

---

# 2. Do Not Redesign Existing Primary Retrieval

不得修改：

```text
search_books
get_book_detail
get_chapter
vector ranking
embedding
KG
primary corpus
O7-B bibliography
```

除非为了 additive source identity 做极小兼容。

O7-C 聚焦：

```text
SCHOLARLY SECONDARY / REFERENCE RETRIEVAL
```

---

# 3. Minimal Tool Surface

不要工具爆炸。

新增最多两个 Main-Agent tools：

```text
search_scholarship
get_scholarly_source
```

推荐：

### `search_scholarship`

输入类似：

```json
{
  "query": "...",
  "philosopher": null,
  "work": null,
  "year_from": null,
  "year_to": null,
  "limit": 8
}
```

职责：

```text
发现真实 scholarly records
+
bibliographic identity
+
source provenance
+
currently known access level
```

### `get_scholarly_source`

输入：

```json
{
  "source_record_id": "...",
  "requested_access": "ABSTRACT | FULL_TEXT_IF_LEGALLY_AVAILABLE"
}
```

职责：

```text
取得实际可读 evidence
+
更新 access level
```

不得再加：

```text
find_best_interpretation
find_two_sides
verify_scholar_opinion
literature_sufficiency
```

这些属于 Shadow Cognition。

---

# 4. Main Agent Owns Research Choice

必须继续：

```text
Main Agent decides:
- 是否搜索二手文献
- 搜什么
- 选哪篇
- 是否读 abstract
- 是否继续取 full text
- 是否继续研究
- 何时停止
```

Runtime 只负责：

```text
execute
normalize
deduplicate
cache
timeout/retry
provenance
access honesty
```

禁止：

```text
AUTO_SCHOLARLY_SEARCH
AUTO_SECOND_OPINION
AUTO_TWO_INTERPRETATIONS
AUTO_LITERATURE_SUFFICIENCY
```

---

# 5. Provider Feasibility Audit First

实施前先调查当前实际可用 provider。

必须至少评估：

```text
Crossref
OpenAlex
SEP
PhilPapers
```

并可评估其它合法稳定来源。

对每个记录：

```text
OFFICIAL_API =
STABLE_MACHINE_INTERFACE =
AUTH_REQUIRED =
RATE_LIMIT =
SEARCH_CAPABILITY =
ABSTRACT_CAPABILITY =
FULL_TEXT_CAPABILITY =
IDENTIFIER_QUALITY =
LEGAL_ACCESS_NOTES =
IMPLEMENTED =
WHY =
```

重要：

```text
DO NOT INVENT A PHILPAPERS API
DO NOT SCRAPE A SITE JUST TO CHECK A BOX
```

如果 PhilPapers 没有合适稳定公开接口：

```text
PHILPAPERS_ADAPTER = NOT_IMPLEMENTED
REASON = ...
```

这是允许的。

---

# 6. Minimum Provider Foundation

O7-C 至少实现两个**独立 scholarly metadata providers**。

推荐优先：

```text
Crossref
OpenAlex
```

但 Agent 应根据真实 feasibility audit 决定。

目标：

```text
PROVIDER_COUNT >= 2
```

避免一个 provider 成为单点真相。

---

# 7. SEP / PhilPapers Semantics

正式记录：

```text
SEP =
SCHOLARLY_REFERENCE

PhilPapers =
SCHOLARLY_DISCOVERY_INDEX
```

SEP 本身不是普通 peer-reviewed article。

PhilPapers 的 index record：

```text
“文献存在/被索引”
```

不意味着：

```text
“已阅读论文”
```

若 O7-C 无法合法、稳定地实现它们：

不伪装成已接入。

---

# 8. Canonical Scholarly Source Record

建立单一 normalized schema：

```text
source_record_id

title

authors:
  name
  orcid?

publication_year
publication_date?

container_title
publisher?

publication_type:
  JOURNAL_ARTICLE
  BOOK
  BOOK_CHAPTER
  REFERENCE_ENTRY
  DISSERTATION
  PROCEEDINGS
  OTHER

identifiers:
  doi?
  isbn?
  openalex_id?
  provider_ids[]

stable_urls[]

provider_records[]

access:
  level
  evidence
  checked_at
  full_text_url?
  content_hash?

abstract:
  text?
  source?
  hash?

provenance:
  providers[]
  field_sources{}

conflicts[]

philosophical_role:
  PRIMARY
  SCHOLARLY_SECONDARY
  SCHOLARLY_REFERENCE
  UNKNOWN
```

不要为了填满而猜。

---

# 9. Stable Source Record ID

优先：

```text
DOI normalized
```

若无 DOI：

使用：

```text
provider canonical ID
```

再无：

```text
normalized bibliographic fingerprint
```

但 fingerprint 必须包含足够字段避免：

```text
same title
different publication
```

被合并。

---

# 10. DOI Normalization

机械统一：

```text
https://doi.org/10.xxxx/abc
doi:10.xxxx/abc
10.xxxx/ABC
```

→

```text
10.xxxx/abc
```

但：

```text
DOI_STRING_PRESENT
!=
DOI_VERIFIED
```

只有 provider record 明确绑定或 resolver 验证后：

```text
doi_verified=true
```

---

# 11. Cross-Provider Dedup

相同 DOI：

```text
one canonical source record
+
multiple provider_records
```

不同 DOI：

不得因 title 很像就强合并。

无 DOI 时的 fuzzy merge：

只能：

```text
MERGE_CANDIDATE
```

除非：

```text
title + authors + year + venue
```

足够一致。

禁止 semantic LLM 自动 merge。

---

# 12. Bibliographic Conflict Semantics

复用 O7-B 精神。

例如：

```text
Crossref year = 1998
OpenAlex year = 1999
```

必须：

```text
conflict retained
```

不得 silent overwrite。

字段：

```text
candidate_values
provider
resolution_status
```

若无权威 resolution：

```text
UNKNOWN / CONFLICT
```

---

# 13. Access-Level State Machine

严格实现：

```text
METADATA_ONLY
ABSTRACT_AVAILABLE
FULL_TEXT_AVAILABLE
FULL_TEXT_READ
```

状态只能来自实际证据。

---

# 14. METADATA_ONLY

仅有：

```text
title
author
year
DOI
venue
provider record
```

则：

```text
access_level = METADATA_ONLY
```

即使：

```text
title 看起来已经告诉你论文观点
```

也不能升级。

---

# 15. ABSTRACT_AVAILABLE

只有实际取得 abstract text：

```text
abstract_text != empty
abstract_source known
```

才能：

```text
ABSTRACT_AVAILABLE
```

OpenAlex reconstructed abstract 可以用，但必须标：

```text
abstract_source=OPENALEX_INVERTED_INDEX
```

不得假装来自 publisher full abstract 页面。

---

# 16. FULL_TEXT_AVAILABLE

只在有**合法可访问的 full-text location** 时。

至少满足：

```text
open/licensed/user-provided/public-domain
+
resolvable location
```

不得因为 DOI landing page 存在就：

```text
FULL_TEXT_AVAILABLE
```

不得因为：

```text
OpenAlex has a URL
```

就默认全文存在。

---

# 17. FULL_TEXT_READ

这是最严格状态。

必须发生：

```text
full text successfully fetched
+
body successfully parsed
+
meaningful content obtained
+
content hash recorded
```

才能：

```text
FULL_TEXT_READ
```

必须保存：

```text
read_at
content_hash
content_length
source_url
parser
```

---

# 18. FULL_TEXT_AVAILABLE Is Not READ

测试锁死：

```text
reachable OA PDF
but get_scholarly_source not called/read
→ FULL_TEXT_AVAILABLE

after successful fetch+parse
→ FULL_TEXT_READ
```

---

# 19. Legal Access Boundary

禁止：

```text
paywall bypass
credential bypass
Sci-Hub
shadow libraries
CAPTCHA bypass
login-session scraping
robots circumvention
```

O7-C 仅允许：

```text
open access
public-domain
official abstract/metadata
user-provided accessible material
legitimately licensed source
```

---

# 20. No Persistent Full-Text Corpus Expansion

O7-C 不是 O7-D。

不得把：

```text
fetched journal PDFs
book chapters
article bodies
```

大批量塞入 permanent vector DB。

允许：

```text
runtime evidence
small cache
hash/provenance
temporary parsed content
```

O7-D 才处理 corpus expansion。

---

# 21. Copyright-Safe Retrieval Design

工具返回 Main Agent 的全文内容不得默认整个全文。

推荐：

```text
metadata
abstract
relevant extracted passages
source locator
content hash
```

全文可在内部临时解析以检索，但不要把整篇论文复制到 ToolMessage。

---

# 22. Source Existence Rule

硬原则：

> **Bibliographic existence must come from a retrieved record, never model memory.**

若 Main Agent 自己说：

```text
“Smith 2014 有一篇论文……”
```

但 tool evidence 没有这个 record：

O7-C runtime 不自动删除它——最终学术 judge 后续会检查。

但 scholarly tool 绝不能自己生成不存在的 record。

---

# 23. Metadata Pass-Through

Provider 返回：

```text
title
authors
year
doi
venue
```

normalizer 只能：

```text
normalize
```

不能：

```text
LLM-fill missing year
LLM-complete author
LLM-invent DOI
```

要求：

```text
LLM_METADATA_COMPLETION_CALLS = 0
```

---

# 24. Peer Review Honesty

禁止：

```text
Crossref type=journal-article
→ peer_reviewed=true
```

因为它不一定证明 peer review。

用：

```text
peer_review_status =
VERIFIED
UNVERIFIED
NOT_APPLICABLE
```

只有实际 evidence 明确支持才 VERIFIED。

---

# 25. Philosophical Role Honesty

不要仅因来源在 Crossref：

```text
SCHOLARLY_SECONDARY
```

一刀切。

例如哲学家本人发表的论文可能是 primary text。

默认可：

```text
philosophical_role=UNKNOWN
```

只有明确 metadata/context 支持时再分类。

---

# 26. Model-Facing Result

`search_scholarship` 每条结果至少：

```text
source_record_id
title
authors
year
publication_type
venue
doi
source_category
access_level
provider
bibliographic_verified_fields
```

不要把大 provenance tree 全塞 ToolMessage。

---

# 27. `get_scholarly_source` Result

至少：

```text
source_record_id
bibliographic_record

access_level_before
access_level_after

abstract?

full_text_status

evidence_passages[]
passage_locators[]

source_url
content_hash?

access_notes
```

明确：

```text
what was actually read
```

---

# 28. Evidence Store Provenance

Tool result 进入现有 Evidence Store 时 additive 标记：

```text
source_record_id
source_category
publication_type
access_level
provider
doi
```

不要新增：

```text
ScholarlySufficiencyState
InterpretationController
LiteratureObligation
```

---

# 29. Search Cache

允许：

```text
exact query cache
provider metadata cache
DOI record cache
```

只做机械优化。

不能：

```text
“已有三篇文献，所以够了”
```

---

# 30. Provider Failure Semantics

Provider 出错：

```text
PROVIDER_TIMEOUT
PROVIDER_RATE_LIMIT
PROVIDER_UNAVAILABLE
MALFORMED_PROVIDER_RESPONSE
```

不得转换成：

```text
“没有相关文献”
```

再次强调：

> retrieval failure ≠ scholarly absence.

---

# 31. Search Result Empty Semantics

```text
0 results
```

只表示：

```text
this provider/query returned no records
```

不得写：

```text
“学界没有研究”
```

---

# 32. Direct Tool Evaluation Corpus

建立至少 16 个 retrieval queries。

覆盖：

```text
Kant
Nietzsche
Plato
Aristotle
Descartes
Spinoza
Hegel
Wittgenstein
Heidegger
Chinese philosophy
```

其中至少：

```text
4 interpretive controversy
4 argument/topic
4 philosopher/work
2 Chinese philosophy
2 negative/rare query
```

---

# 33. Canonical O7-C Retrieval Cases

至少固定：

```text
C1
Kant thing in itself two aspect two world interpretation

C2
Kant transcendental deduction interpretation

C3
Nietzsche eternal recurrence interpretation

C4
Wittgenstein private language argument

C5
Plato Third Man argument scholarly literature

C6
Confucius ritual ren contemporary scholarship
```

注意：

不要求搜索结果必须包含预先指定某个学者。

否则会变成 cherry-picking benchmark。

---

# 34. Bibliographic Verification Sample

从 live search 得到 records 后，固定 seed 抽：

```text
>=25 canonical records
```

重新对 provider record 验证：

```text
title
author
year
DOI
venue
```

要求：

```text
FABRICATED_BIBLIOGRAPHIC_FIELDS=0
```

---

# 35. DOI Verification Sample

所有声称：

```text
doi_verified=true
```

的 pilot DOI：

100% 检查。

要求：

```text
INVALID_VERIFIED_DOI=0
```

若 provider 没给 DOI：

留 null。

---

# 36. Access-Level Audit

至少建立：

```text
10 METADATA_ONLY
5 ABSTRACT_AVAILABLE
3 FULL_TEXT_AVAILABLE
3 FULL_TEXT_READ
```

如果合法 full-text source 实际不足：

不得伪造数量。

允许：

```text
FULL_TEXT_AVAILABLE_CASES=<actual>
FULL_TEXT_READ_CASES=<actual>
```

但至少必须有：

```text
1 real FULL_TEXT_READ
```

否则：

```text
O7_C = BLOCKED_ACCESS_PIPELINE
```

---

# 37. Access-Level Kill Cases

至少：

```text
A1 metadata record only
→ METADATA_ONLY

A2 metadata + abstract
→ ABSTRACT_AVAILABLE

A3 OA link exists and verified
→ FULL_TEXT_AVAILABLE

A4 full text fetched and parsed
→ FULL_TEXT_READ

A5 DOI page only
→ NOT FULL_TEXT_AVAILABLE

A6 broken OA URL
→ NOT FULL_TEXT_AVAILABLE

A7 abstract only
→ cannot describe internal section structure

A8 FULL_TEXT_AVAILABLE without fetch
→ cannot become FULL_TEXT_READ
```

---

# 38. Provider Conflict Fixtures

至少：

```text
P1 identical DOI across two providers → merge

P2 same title but different DOI → do not merge

P3 year conflict → preserve

P4 author spelling normalization → aliases retained

P5 provider timeout → not “no literature”

P6 malformed metadata → field null / issue retained
```

---

# 39. Retrieval Relevance Evaluation

O7-C 需要测“能不能找到真的相关论文”，但不要变成 semantic runtime gate。

Evaluation-only 使用 official judge：

```text
glm-4.6
```

对固定 16 queries 的 Top-5 records 评价：

```text
TOPICAL_RELEVANCE
0–4
```

Judge 输入：

```text
query
record title
abstract if available
publication metadata
```

不得给：

```text
expected scholar names
expected score
```

---

# 40. Retrieval Quality Targets

候选：

```text
TOP5_RELEVANCE_MEAN >= 3.0/4

QUERIES_WITH_AT_LEAST_1_RELEVANT_RECORD >= 90%
```

这里 relevant 定义：

```text
judge score >=3
```

但这是 O7-C capability gate，不进入 runtime。

---

# 41. Scholarly Record Quality

另报告：

```text
records by publication_type
records with DOI
records with abstract
records with OA location
records by provider
duplicate merge rate
provider conflict rate
```

不要把 DOI coverage 当质量替代物。

---

# 42. Search Diversity

不要求：

```text
每题必须 2 个解释
```

但直接 tool retrieval 不应 Top-5 全是同一 record 的 provider duplicates。

要求：

```text
DUPLICATE_RECORDS_IN_TOP5 = 0
```

canonical dedup 后再呈现。

---

# 43. SEP Reference Handling

如果实现 SEP：

记录：

```text
source_category=SCHOLARLY_REFERENCE
publication_type=REFERENCE_ENTRY
```

它可以作为：

```text
orientation / bibliography discovery
```

但不能冒充：

```text
peer-reviewed secondary article
```

---

# 44. PhilPapers Handling

如果只能通过合法 discovery 获得：

```text
title/author/record URL
```

则：

```text
access_level=METADATA_ONLY
```

除非实际取得 abstract/full text。

---

# 45. Literature Access Honesty Evaluation

用 O7-A official judge + deterministic checks 做 12 个 fixtures。

必须达到：

```text
LITERATURE_ACCESS_OVERCLAIM_RECALL=100%

FALSE_ACCESS_OVERCLAIM=0
```

沿用 O7-A F6 语义。

---

# 46. No Main-Agent Final Quality Gate Yet

不要在 O7-C 就要求：

```text
“康德回答达到 3.5/4”
```

因为 production Scholarly Policy 尚未启用。

可以做：

```text
NON_GATING_AGENT_OBSERVATION
```

看看模型是否自然发现新 tools。

但不能因此改 prompt。

---

# 47. Tool Causal Contract

若 Agent 调用：

```text
search_scholarship
get_scholarly_source
```

必须满足 O3：

```text
top-level call originates from Main Agent
```

零：

```text
ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS
```

---

# 48. Tool Count

如果最终新增两个工具：

```text
TOOL_COUNT_BEFORE=
TOOL_COUNT_AFTER=+2
```

必须更新 canonical tool inventory。

不要让历史文档继续声称 38，如果实际已经 40。

---

# 49. Latency

记录：

```text
P50_SEARCH_SCHOLARSHIP
P95_SEARCH_SCHOLARSHIP

P50_GET_ABSTRACT
P95_GET_ABSTRACT

P50_GET_FULLTEXT
P95_GET_FULLTEXT
```

Provider timeout 必须有硬上限。

---

# 50. Network Safety

至少：

```text
connect timeout
read timeout
max redirects
max response bytes
allowed schemes=https/http
```

full text 不能无界下载。

---

# 51. SSRF / URL Boundary

`get_scholarly_source` 不接受 Main Agent 随意传任意 URL。

输入必须：

```text
source_record_id
```

工具自己从已检索 provider record 解析允许的 URL。

禁止访问：

```text
localhost
private IP
file://
ftp://
169.254.*
```

---

# 52. No Arbitrary Browser

`get_scholarly_source` 不是：

```text
generic_url_fetch
```

仅允许访问该 scholarly record 已验证 provenance 中的 source URLs。

---

# 53. Evidence Passage Boundaries

如果全文成功读取：

返回 evidence passages 时必须记录：

```text
passage_id
locator if available
source_record_id
content_hash
```

不要造页码。

如果 HTML 无页码：

```text
page=null
```

---

# 54. PDF Page Locator

若合法 OA PDF 且 parser 保留页号：

```text
locator_kind=PDF_PAGE
```

这只是该 digital artifact 的 page：

```text
EDITION_SPECIFIC / DIGITAL_SOURCE
```

不得冒充 canonical locator。

---

# 55. Abstract Provenance

每个 abstract：

```text
abstract_source
abstract_hash
```

如果不同 provider abstract 冲突：

保留 provider-specific records。

不要拼接出一个“更完整 abstract”。

---

# 56. Evaluation Artifact

输出：

```text
docs/evidence/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL_GATE.json
```

包含：

```text
provider configs
queries
normalized records
dedup decisions
bibliographic sample
access sample
judge relevance scores
hard-integrity counters
```

不要提交大量 full text。

---

# 57. Tests

新增：

```text
backend/tests/test_o7c_scholarly_retrieval.py
```

至少覆盖：

```text
C1 DOI normalization
C2 same DOI cross-provider merge
C3 different DOI no merge
C4 provider conflict retained
C5 missing fields remain null

C6 metadata only state
C7 abstract available state
C8 fulltext available != read
C9 fulltext read requires parsed body
C10 broken OA URL not available

C11 DOI landing != full text
C12 no paywall bypass path

C13 timeout != no literature
C14 zero results != scholarly absence

C15 peer review not inferred
C16 philosophical role defaults honestly

C17 no LLM metadata completion
C18 no semantic sufficiency
C19 no auto scholarly tool

C20 source_record_id stable
C21 SSRF/private URL blocked
C22 arbitrary URL input impossible

C23 PDF page != canonical locator
C24 abstract provenance preserved
C25 tool result compact model-facing view

C26 access-overclaim fixtures
C27 raw provider provenance retained
C28 exact duplicate cache mechanical

C29 existing primary retrieval unchanged
C30 O7-B bibliography unchanged
```

---

# 58. Architecture Invariants

继续要求：

```text
ENGINE_COGNITIVE_AUTO_TOOLS=0
SEMANTIC_TOOL_CONTROL_EFFECTS=0
RUNTIME_SEMANTIC_MUTATORS=0
RUNTIME_FACTUAL_APPENDS=0
COGNITIVE_POLICY_OWNER=1

SCHOLARLY_AUTO_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0
```

---

# 59. Production Freeze

允许：

```text
tool registry
tool executor
scholarly provider modules
additive evidence metadata
```

禁止：

```text
SYSTEM_PROMPT
Main Agent scholarly policy
final validator
quote_bound
answer composer
```

---

# 60. Capability Gate SHA

使用：

```text
O7C_CAPABILITY_GATE_SHA
```

流程：

```text
BASE
→ provider feasibility audit
→ normalized source schema
→ provider adapters
→ 2 tools
→ access state machine
→ provenance
→ tests
→ freeze
→ live retrieval gate
→ access gate
→ relevance judge
→ report
```

Gate 后：

```text
provider/config/prompt/schema/tool change
→ REFREEZE
→ rerun complete live gate
```

---

# 61. Provider Live Gate

必须用真实网络完成。

如果主要 provider 整轮不可用：

```text
O7_C = BLOCKED_PROVIDER
```

不得拿 mock 结果冒充 live gate。

Unit tests 可以 mock。

Capability acceptance 必须有真实 records。

---

# 62. Hard PASS Gates

```text
PROVIDER_COUNT >= 2

FABRICATED_BIBLIOGRAPHIC_FIELDS = 0
INVALID_VERIFIED_DOI = 0

DUPLICATE_RECORDS_IN_TOP5 = 0
SILENT_PROVIDER_CONFLICT_RESOLUTION = 0

ACCESS_LEVEL_OVERCLAIM = 0
FULL_TEXT_READ_WITHOUT_PARSED_TEXT = 0

LITERATURE_ACCESS_OVERCLAIM_RECALL = 100%
FALSE_ACCESS_OVERCLAIM = 0

QUERIES_WITH_RELEVANT_RECORD >= 90%
TOP5_RELEVANCE_MEAN >= 3.0

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS = 0
SCHOLARLY_SUFFICIENCY_GATES = 0

SYSTEM_PROMPT_CHANGED = false
FINAL_VALIDATOR_CHANGED = false

O7B_RUNTIME_DATA_CHANGED = false

FULL_TEST_FAILED = 0
```

---

# 63. Report

```text
docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md
```

必须至少包含：

```text
1 provider feasibility
2 implemented providers
3 source schema
4 identity/dedup
5 conflict semantics
6 access-level state machine
7 legal access boundary
8 tool contracts
9 Evidence Store integration
10 provider failure semantics
11 retrieval query gate
12 bibliographic verification
13 access audit
14 relevance evaluation
15 latency/cost
16 security/SSRF
17 architecture invariants
18 tests
19 limitations
20 O7-D readiness
```

任务书：

```text
docs/tasks/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL_TASK.md
```

---

# 64. STOP Conditions

立即停止并回报：

```text
only one usable scholarly provider exists
provider requires prohibited scraping/bypass
metadata must be invented to normalize records
full text requires paywall bypass
FULL_TEXT_READ cannot be made truthful
source identity cannot deduplicate DOI safely
new semantic scholarly gate appears
Main Agent prompt must be modified to make capability work
```

不得自行进入 O7-D。

---

# FINAL RECEIPT

```text
O7_C =
READY_FOR_FINAL_REVIEW /
BLOCKED_PROVIDER /
BLOCKED_ACCESS_PIPELINE /
BLOCKED

BASE_SHA=

CODE_SHA=
O7C_CAPABILITY_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

TOOL_COUNT_BEFORE=
TOOL_COUNT_AFTER=

PROVIDERS_EVALUATED=
PROVIDERS_IMPLEMENTED=

CROSSREF_STATUS=
OPENALEX_STATUS=
SEP_STATUS=
PHILPAPERS_STATUS=

SEARCH_SCHOLARSHIP=
GET_SCHOLARLY_SOURCE=

SOURCE_SCHEMA_VERSION=

SOURCE_RECORDS_RETRIEVED=
UNIQUE_CANONICAL_RECORDS=

DOI_RECORDS=
DOI_VERIFIED=
INVALID_VERIFIED_DOI=

CROSS_PROVIDER_MERGES=
MERGE_CANDIDATES_UNRESOLVED=
SILENT_PROVIDER_CONFLICT_RESOLUTION=

METADATA_ONLY_COUNT=
ABSTRACT_AVAILABLE_COUNT=
FULL_TEXT_AVAILABLE_COUNT=
FULL_TEXT_READ_COUNT=

FULL_TEXT_READ_WITHOUT_PARSED_TEXT=
ACCESS_LEVEL_OVERCLAIM=

FABRICATED_BIBLIOGRAPHIC_FIELDS=
LLM_METADATA_COMPLETION_CALLS=

PEER_REVIEW_INFERRED_WITHOUT_EVIDENCE=
PHILOSOPHICAL_ROLE_OVERCLASSIFICATION=

LIVE_QUERY_COUNT=
QUERIES_WITH_RELEVANT_RECORD=
QUERIES_WITH_RELEVANT_RECORD_RATE=
TOP5_RELEVANCE_MEAN=

DUPLICATE_RECORDS_IN_TOP5=

BIBLIOGRAPHIC_AUDIT_RECORDS=
BIBLIOGRAPHIC_WRONG_FIELDS=

ACCESS_KILL_CASES=
LITERATURE_ACCESS_OVERCLAIM_RECALL=
FALSE_ACCESS_OVERCLAIM=

P50_SEARCH_SCHOLARSHIP=
P95_SEARCH_SCHOLARSHIP=
P50_GET_ABSTRACT=
P95_GET_ABSTRACT=
P50_GET_FULLTEXT=
P95_GET_FULLTEXT=

PROVIDER_TIMEOUTS=
PROVIDER_RATE_LIMITS=
PROVIDER_ERRORS=

SSRF_BLOCK_TESTS=
PAYWALL_BYPASS_PATHS=0

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7B_RUNTIME_DATA_CHANGED=false

O7C_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL.md

O7_D_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP
```

这阶段有两条不可妥协的线：

> **“数据库里有这篇论文”只能证明它存在；“我知道这篇论文怎么论证”必须来自实际获得的 abstract 或 full text。**

以及：

> **不要让 scholarly retrieval 变成新的 Shadow Agent。它负责把真实文献和访问边界摆到 Main Agent 面前，研究判断仍然只属于 Main Agent。**

等 O7-C 回执，我会重点审三件事：**文献有没有真的存在、access_level 有没有说真话、以及为了“做学术”有没有偷偷重新长出第二个大脑。**
