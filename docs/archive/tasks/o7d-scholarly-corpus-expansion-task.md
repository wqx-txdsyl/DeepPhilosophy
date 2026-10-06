TASK — PhiAgent O7-D
Scholarly Corpus Expansion & Research Evidence Layer
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
6644a054d

OFFICIAL_SCHOLARLY_JUDGE =
glm-4.6

PHASE =
O7-D — SCHOLARLY CORPUS EXPANSION

PHASE_TYPE =
CURATED SECONDARY CORPUS + LOCAL EVIDENCE INDEX
0. 目标

O7-D 不再继续造“检索 API”。

目标是：

把 O7-C 能实时找到的真实学术文献，建设成一个可持续、可验证、可本地检索的哲学研究语料层。

最终结构：

Primary Corpus
O7-B Bibliography
        ↕
Scholarly Source Registry
        ↕
Local Scholarly Evidence Index
        ↕
O7-C Live Providers
        ↓
Main Agent

必须保持：

Main Agent = 唯一研究决策者
Corpus = evidence infrastructure
1. 禁止事项

不得：

- 修改 Main Agent scholarly prompt
- 加入“必须引用几个学者”规则
- 自动决定“两个解释够了”
- 自动决定争议双方
- 新增 LiteraturePlanner
- 新增 ScholarlySufficiencyGate
- 新增 InterpretationController
- 修改 final_validator
- 修改 quote_bound
- 添加第三个认知主体
- 开 O7-E

同时：

NO MASS COPYRIGHTED_FULLTEXT_ARCHIVE
NO PAYWALL BYPASS
NO SHADOW LIBRARY
2. 修掉 O7-C evaluator denominator

先做一个极窄 evaluation-only 修复。

固定查询宇宙必须来自：

QUERIES

而不是：

queries which happened to return records

正确：

SUBSTANTIVE_QUERY_COUNT =
count(non-N queries in QUERIES)

ZERO_RESULT_SUBSTANTIVE_QUERIES
也必须进入分母

最终：

relevant rate =
relevant substantive queries /
all substantive queries

新增 regression：

14 substantive
1 returns zero records
13 relevant
→ rate = 13/14

不得重新跑 O7-C full gate；只修 deterministic evaluator test，并将 reviewer correction 记入 O7-D report provenance。

3. Scholarly Source Registry

建立持久 canonical registry，例如：

backend/data/scholarly_sources/
    registry.jsonl
    evidence.jsonl
    corpus_manifest.json

具体目录可根据 repo 结构调整。

每条 canonical record 必须复用 O7-C identity：

source_record_id
title
authors
publication_year
publication_type
container_title
identifiers
provider_records
provenance
conflicts
peer_review_status
philosophical_role
access

禁止另造：

O7DSourceRecordV2

与 O7-C 平行。

4. Registry ≠ Search Cache

当前：

scholarly_cache.json

是机械 runtime cache。

O7-D registry 是：

CURATED
VERSIONED
REPRODUCIBLE
AUDITABLE

两者必须分开。

Cache 可失效。

Registry 是 corpus asset。

5. Corpus Unit

持久语料的最小单位不是：

整篇 PDF

而是：

SOURCE RECORD
+
ACCESS PROVENANCE
+
OPTIONAL ABSTRACT
+
OPTIONAL VERIFIED EVIDENCE PASSAGES

推荐：

JSON
{
  "source_record_id": "...",
  "evidence_id": "...",
  "evidence_type": "ABSTRACT | FULLTEXT_PASSAGE",
  "text": "...",
  "locator": null,
  "source_url": "...",
  "content_hash": "...",
  "access_level_at_ingest": "...",
  "extracted_at": "..."
}
6. Copyright Boundary

默认允许长期保存：

bibliographic metadata
provider identifiers
provenance
access facts
content hashes
short evidence passages

全文：

只有：

PUBLIC_DOMAIN
or
explicit reusable licence
or
user-owned/user-provided corpus with permission

才能持久保存正文。

否则：

FULL_TEXT_READ
→ persist evidence passages + provenance/hash
→ discard full body after processing

不得因为：

OPEN_ACCESS

就自动假设：

redistribution licence
7. License State

新增机械字段：

reuse_status =
PUBLIC_DOMAIN
OPEN_LICENSE_VERIFIED
ACCESSIBLE_BUT_REUSE_UNVERIFIED
METADATA_ONLY
UNKNOWN

以及：

license
license_source
license_verified

缺失：

UNKNOWN

不猜 CC-BY。

8. Expansion Coverage Manifest

不要按“哲学史最伟大人物排行榜”。

建立：

O7D_RESEARCH_COVERAGE_MANIFEST

至少覆盖：

Ancient Greek
Late Antiquity / Medieval
Early Modern
Kant / German Idealism
19th Century
20th Analytic
20th Continental
Chinese Philosophy

至少：

8 PERIOD/TRADITION GROUPS
30 RESEARCH CLUSTERS
9. Research Cluster

每个 cluster 是学术问题，不只是人名。

例如：

Kant:
- thing-in-itself interpretation
- transcendental deduction
- schematism
- autonomy/freedom

Nietzsche:
- eternal recurrence
- genealogy
- perspectivism

Plato:
- Third Man
- forms / participation

Wittgenstein:
- private language
- rule following

Chinese:
- ren / li
- Zhuangzi skepticism

30 个 cluster 必须写在 manifest 中。

10. Primary Work Linking

每个 cluster 可显式关联：

related_primary_book_ids[]
related_work_ids[]

来源必须是 manifest curation。

不得 LLM 静默决定：

“这篇论文应该属于哪本书”

后再写成事实。

允许：

association_status =
CURATED
DISCOVERY_CANDIDATE
11. Current Work-ID Limitation

继承 O7-B：

WORK_IDENTITY_CURRENTLY_TITLE_AUTHOR_DERIVED = true
CROSS_TITLE_WORK_RECONCILIATION = NOT_IMPLEMENTED

O7-D 不顺手解决 authority control。

若同一原典不同题名无法统一：

leave explicit unresolved mapping
12. Discovery Pipeline

每 cluster：

query manifest
↓
Crossref + OpenAlex
↓
canonical dedup
↓
candidate pool
↓
evaluation-only relevance
↓
accepted registry

禁止：

LLM 生成 bibliography

所有 bibliographic identity 必须来自 provider。

13. Official Judge 只能做 Corpus Curation

允许 glm-4.6 evaluation-only 判：

TOPICAL_RELEVANCE

输入：

cluster question
title
abstract if available
metadata

不得：

补作者
补 DOI
补年份
改 title
14. Acceptance Threshold

候选 source：

relevance >= 3

才能进入：

cluster accepted set

但 bibliographic registry 可以保留：

DISCOVERY_ONLY

记录。

不要删除真实但低相关文献，只是不把它计入 research coverage。

15. Target Scale

最低：

RESEARCH_CLUSTERS >= 30
CANONICAL_SCHOLARLY_RECORDS >= 240

并要求：

CLUSTERS_WITH_3PLUS_RELEVANT_SOURCES >= 90%

即至少 27/30。

另外：

NO_SINGLE_SOURCE_CLUSTER

作为诊断；若个别冷门 cluster 只能找到 1–2 篇，允许如实记录，但不得虚构补足。

16. Source Diversity

整个 accepted corpus 不应被一个 publisher/journal/provider identity 淹没。

报告：

RECORDS_BY_PROVIDER
RECORDS_BY_PUBLICATION_TYPE
RECORDS_BY_YEAR_BUCKET
RECORDS_BY_CLUSTER
RECORDS_BY_PERIOD

不设机械“每类必须一样多”。

17. Abstract Layer

对实际取得 abstract 的记录：

ABSTRACT_AVAILABLE

可持久索引 abstract。

必须保存：

abstract_source
abstract_hash

若 provider abstract 冲突：

不拼接。

18. Fulltext Evidence Layer

对于：

FULL_TEXT_READ

只持久：

short passages
document hash
source URL
parser
verified document kind
passage locator if real

不默认存整文。

19. Passage Length

每 passage：

compact
research-useful

建议上限：

<= 1200 chars

每篇默认最多：

3–5 passages

不要让 Local Corpus 变成全文复制仓。

20. Passage Selection

O7-D ingestion 可以采用机械：

query-term relevance
BM25
section proximity

不得由一个隐藏 LLM 自动写“这篇文章最重要的论证”。

如需 LLM passage relevance：

仅 evaluation/curation 阶段，必须留下：

judge model
score
raw input refs
21. Local Index

建立 secondary-only local index。

优先简单、透明：

SQLite FTS5 / BM25

或复用 repo 中已有非认知性索引基础设施。

禁止为了 O7-D 新造复杂 embedding/reranker stack。

索引：

title
authors
abstract
evidence passages
cluster tags
primary-work links
22. 不修改 primary retrieval

必须：

PRIMARY_RETRIEVAL_BEHAVIOR_CHANGED=false

Secondary index 独立。

23. O7-C Tool Integration

保持工具数：

search_scholarship
get_scholarly_source

不增加第三个 tool。

search_scholarship 可 additive 查询：

LOCAL_CURATED
+
Crossref
+
OpenAlex

然后 canonical dedup。

24. Local Corpus Is a Provider, Not Authority

标：

provider = LOCAL_CURATED

但每条结果必须保留原始：

Crossref/OpenAlex/provider provenance

LOCAL_CURATED 不能成为：

“因为我们库里有，所以是真的”
25. Local / Live Dedup

同 DOI：

one canonical source

Local 与 live 重复不能在 top results 中出现两遍。

要求：

LOCAL_LIVE_DUPLICATES_IN_TOP5=0
26. Offline Capability

O7-D 后：

在 Crossref/OpenAlex 临时不可用时：

search_scholarship

仍能返回 curated local corpus。

必须明确：

providers_live_failed
local_results_available

不能把 offline local result 冒充 live provider result。

27. Offline Failure Semantics

例如：

Crossref timeout
OpenAlex timeout
LOCAL_CURATED returns 5

工具说明：

“外部 provider 当前失败；以下结果来自已验证的本地学术 registry。”

不得：

“实时检索得到……”
28. Registry Rebuild

必须有：

deterministic rebuild

从：

coverage manifest
+
frozen provider candidate records
+
curation decisions
+
evidence manifests

重建 registry/index。

网络结果本身当然会随时间变化，因此：

DISCOVERY RUN

与：

REGISTRY BUILD

分离。

29. Snapshot Discipline

Discovery 后冻结：

DISCOVERY_SNAPSHOT_SHA/HASH

之后 corpus gate 使用该 snapshot。

不得：

测试时又实时搜索一遍，
然后拿变化后的数据和旧 Gate 混用
30. Data Files

建议：

docs/evidence/
  PHIAGENT_O7D_COVERAGE_MANIFEST.json
  PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json
  PHIAGENT_O7D_CORPUS_GATE.json

backend/data/scholarly/
  registry.jsonl
  evidence.jsonl

大文件控制。

不得 commit journal PDFs。

31. Canonical Registry Integrity

硬门：

DUPLICATE_SOURCE_RECORD_ID=0
DUPLICATE_VERIFIED_DOI=0
SILENT_BIBLIOGRAPHIC_CONFLICT=0
FABRICATED_BIBLIOGRAPHIC_FIELDS=0
32. DOI Audit

所有：

doi_verified=true

在 frozen discovery snapshot 中 100% 校验。

要求：

INVALID_VERIFIED_DOI=0
33. Bibliographic Audit

固定 seed 抽：

>=50 records

校：

title
authors
year
venue
DOI

对 provider provenance。

要求：

BIBLIOGRAPHIC_WRONG_FIELDS=0
34. Evidence Audit

100% 检查：

FULLTEXT_PASSAGE

必须：

source_record_id exists
content_hash exists
access at ingestion = FULL_TEXT_READ
verified_document_kind exists
passage derived from parsed document

要求：

ORPHAN_EVIDENCE=0
FAKE_PASSAGE_LOCATORS=0
35. Locator Honesty

无真实页号：

page=null

不要从 PDF viewer 序号猜书页。

若 parser 确实保留：

PDF_PAGE

标为 digital-source locator。

36. Access State Is Historical

Registry 中保存：

access_level_at_ingest
checked_at

不要因为今天 URL 404 就删掉：

“此前曾 FULL_TEXT_READ”

但新增：

current_access_status?

必须和历史阅读证据分开。

37. No Opinion Extraction Yet

O7-D 不建立：

Scholar X → supports two-aspect
Scholar Y → opposes

这种 proposition DB。

那会重新长成 interpretation knowledge engine。

持久的是：

source + evidence

不是：

runtime conclusion
38. Query Evaluation

固定至少：

20 scholarly research queries

其中包含 O7-C canonical 6。

评价：

local-only
live-only
combined

报告三种模式。

39. Local Retrieval Gate

在：

NETWORK DISABLED

条件下测 20 queries。

要求：

QUERIES_WITH_RELEVANT_LOCAL_RECORD >= 90%
LOCAL_TOP5_RELEVANCE_MEAN >= 3.0

judge：

glm-4.6

evaluation-only。

40. Combined Retrieval Gate

网络开启：

LOCAL + LIVE

要求：

COMBINED_TOP5_RELEVANCE_MEAN >= LOCAL_TOP5_RELEVANCE_MEAN - 0.1

避免加 live provider 后反而显著污染 top5。

41. Zero-Result Denominator Fix Is Mandatory

所有 retrieval gate：

query universe = manifest

零结果：

relevant=false

不得消失。

测试锁死。

42. Cluster Coverage Gate
CLUSTERS = >=30

CLUSTERS_WITH_RELEVANT_1PLUS >= 95%
CLUSTERS_WITH_RELEVANT_3PLUS >= 90%

如确实无法达到：

O7_D = BLOCKED_COVERAGE

不要把阈值改掉。

43. Chinese Philosophy

至少：

4 research clusters

不能只有：

Confucius

建议覆盖：

Confucius ren/li
Mencius human nature
Zhuangzi skepticism/perspectivism
Neo-Confucian / Daoist / Mohist

根据真实检索可用性选择。

44. Non-Western Coverage Honesty

不要把：

“global philosophy”

当成标签后只塞欧美材料。

报告每 tradition 的实际 accepted records。

45. Persona Compatibility

Nietzsche persona 的工具 surface 不另造私有 scholarly corpus。

同一：

Scholarly Registry

通过 persona context 使用。

要求：

GENERAL_AGENT_CORPUS = PHILOSOPHER_AGENT_CORPUS

只允许 persona 影响 Main Agent 如何研究，不改变 source truth。

46. Tool Output Compactness

Local corpus 返回也使用 O7-C：

model_view

不能把整个 abstract/evidence dump 都塞 search result。

需要正文：

get_scholarly_source
47. Local get_scholarly_source

对 local record：

若已有：

ABSTRACT

直接返回。

若已有持久 evidence passages：

access_level_at_ingest=FULL_TEXT_READ

允许返回：

stored evidence passages

同时必须说：

“这是此前验证读取并持久化的证据节选”

不要谎称本轮刚重新抓全文。

48. Current vs Historical Read

建议：

evidence_origin =
LIVE_CURRENT_READ
PERSISTED_VERIFIED_READ
ABSTRACT_METADATA

Main Agent 可知道证据从哪里来。

49. No Hidden Automatic Refresh

Runtime 不得：

source stale
→ 自动联网刷新

是否继续 live research 仍由 Main Agent 决定。

50. Tool Causal Contract

继续：

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0

Local corpus 不改变这一点。

51. Architecture Invariants

必须：

COGNITIVE_POLICY_OWNER=1

SCHOLARLY_AUTO_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0

RUNTIME_SEMANTIC_MUTATORS=0
52. Production Prompt Freeze

整个 O7-D：

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7-E 才允许 Scholarly Policy activation。

53. Tests

至少新增：

D1 zero-result query remains denominator
D2 registry IDs unique
D3 DOI dedup
D4 local/live same DOI merges

D5 cache != registry
D6 registry deterministic rebuild
D7 discovery snapshot frozen

D8 metadata-only source stores no invented content
D9 abstract provenance retained
D10 fulltext evidence requires verified READ

D11 no PDF/body committed by default
D12 reuse status UNKNOWN when licence unknown

D13 local-only search works offline
D14 external provider failure clearly reported
D15 local result not called live result

D16 local/live duplicate top5 = 0

D17 historical read evidence remains usable
D18 historical read != current live read

D19 page null when not verified
D20 no fake canonical locator

D21 source proposition DB absent
D22 no semantic sufficiency gate
D23 no auto refresh
D24 Main Agent tool authority unchanged

D25 primary retrieval unchanged
D26 O7-B data unchanged
D27 O7-C access semantics unchanged

D28 general/persona corpus same
D29 model-facing result compact
D30 no prompt/validator mutation
54. Gate Procedure
BASE
→ denominator evaluator fix
→ coverage manifest
→ live discovery
→ freeze DISCOVERY SNAPSHOT
→ corpus curation
→ registry/evidence build
→ local index
→ tool integration
→ tests
→ freeze O7D_CORPUS_GATE_SHA
→ offline local gate
→ combined retrieval gate
→ audits
→ report

Gate 后 corpus/evaluator/index 变化：

REFREEZE
55. Hard PASS
RESEARCH_CLUSTERS >= 30
PERIOD_TRADITION_GROUPS >= 8

CANONICAL_SCHOLARLY_RECORDS >= 240

CLUSTERS_WITH_RELEVANT_1PLUS_RATE >= 95%
CLUSTERS_WITH_RELEVANT_3PLUS_RATE >= 90%

ZERO_RESULT_QUERY_DENOMINATOR_LOSS = 0

DUPLICATE_SOURCE_RECORD_ID = 0
DUPLICATE_VERIFIED_DOI = 0
FABRICATED_BIBLIOGRAPHIC_FIELDS = 0
INVALID_VERIFIED_DOI = 0

ORPHAN_EVIDENCE = 0
FAKE_PASSAGE_LOCATORS = 0

LOCAL_LIVE_DUPLICATES_IN_TOP5 = 0

LOCAL_QUERY_RELEVANCE_RATE >= 90%
LOCAL_TOP5_RELEVANCE_MEAN >= 3.0

COMBINED_TOP5_RELEVANCE_MEAN
>= LOCAL_TOP5_RELEVANCE_MEAN - 0.1

COPYRIGHT_UNAUTHORIZED_FULLTEXT_STORED = 0

SYSTEM_PROMPT_CHANGED = false
FINAL_VALIDATOR_CHANGED = false

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS = 0
SCHOLARLY_SUFFICIENCY_GATES = 0
SCHOLARLY_SEMANTIC_ROUTERS = 0

FULL_TEST_FAILED = 0
56. Report
docs/PHIAGENT_O7D_SCHOLARLY_CORPUS_EXPANSION.md

必须包含：

1 corpus philosophy
2 coverage manifest
3 discovery snapshot
4 source registry
5 evidence registry
6 copyright/reuse boundary
7 primary-work links
8 local index
9 local/live integration
10 offline behavior
11 coverage results
12 relevance gates
13 bibliographic audit
14 evidence audit
15 access provenance
16 architecture invariants
17 limitations
18 O7-E readiness

任务书：

docs/tasks/PHIAGENT_O7D_SCHOLARLY_CORPUS_EXPANSION_TASK.md
FINAL RECEIPT
O7_D =
READY_FOR_FINAL_REVIEW /
BLOCKED_COVERAGE /
BLOCKED_DATA_INTEGRITY /
BLOCKED

BASE_SHA=

CODE_SHA=
DISCOVERY_SNAPSHOT_SHA=
O7D_CORPUS_GATE_SHA=
HEAD_SHA=
REMOTE_SHA=

O7C_ZERO_RESULT_DENOMINATOR_FIXED=

RESEARCH_CLUSTERS=
PERIOD_TRADITION_GROUPS=

CANONICAL_SCHOLARLY_RECORDS=
ACCEPTED_RELEVANT_RECORDS=

CLUSTERS_WITH_RELEVANT_1PLUS=
CLUSTERS_WITH_RELEVANT_1PLUS_RATE=
CLUSTERS_WITH_RELEVANT_3PLUS=
CLUSTERS_WITH_RELEVANT_3PLUS_RATE=

CHINESE_PHILOSOPHY_CLUSTERS=

RECORDS_METADATA_ONLY=
RECORDS_ABSTRACT_AVAILABLE=
RECORDS_FULLTEXT_AVAILABLE=
RECORDS_FULLTEXT_READ=

PERSISTED_ABSTRACT_RECORDS=
PERSISTED_FULLTEXT_EVIDENCE_RECORDS=
PERSISTED_FULLTEXT_DOCUMENTS=

PUBLIC_DOMAIN_DOCUMENTS=
OPEN_LICENSE_VERIFIED_DOCUMENTS=
REUSE_UNVERIFIED_DOCUMENTS=

COPYRIGHT_UNAUTHORIZED_FULLTEXT_STORED=

DUPLICATE_SOURCE_RECORD_ID=
DUPLICATE_VERIFIED_DOI=
INVALID_VERIFIED_DOI=
FABRICATED_BIBLIOGRAPHIC_FIELDS=

BIBLIOGRAPHIC_AUDIT_RECORDS=
BIBLIOGRAPHIC_WRONG_FIELDS=

EVIDENCE_PASSAGES=
ORPHAN_EVIDENCE=
FAKE_PASSAGE_LOCATORS=

LOCAL_INDEX=
LOCAL_ONLY_NETWORK_DISABLED_TEST=

LOCAL_QUERY_COUNT=
LOCAL_QUERIES_WITH_RELEVANT_RECORD=
LOCAL_QUERY_RELEVANCE_RATE=
LOCAL_TOP5_RELEVANCE_MEAN=

COMBINED_QUERY_COUNT=
COMBINED_TOP5_RELEVANCE_MEAN=
LOCAL_LIVE_DUPLICATES_IN_TOP5=

ZERO_RESULT_QUERY_DENOMINATOR_LOSS=

GENERAL_AGENT_CORPUS_EQ_PERSONA_CORPUS=

PRIMARY_RETRIEVAL_CHANGED=false
O7B_RUNTIME_DATA_CHANGED=false
O7C_ACCESS_SEMANTICS_CHANGED=false

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0
SCHOLARLY_SUFFICIENCY_GATES=0
SCHOLARLY_SEMANTIC_ROUTERS=0
COGNITIVE_POLICY_OWNER=1

SYSTEM_PROMPT_CHANGED=false
SCHOLARLY_MAIN_AGENT_POLICY_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

O7D_TESTS=

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

REPORT=
docs/PHIAGENT_O7D_SCHOLARLY_CORPUS_EXPANSION.md

O7_E_AUTHORIZED=false

PROPOSED_VERDICT=
PASS / PATCH_REQUIRED

STOP

O7-C 到这里正式结束。

这次最重要的结果不是“多了两个搜索工具”，而是终于把下面四句话都变成了代码真值：

文献存在 ≠ 我读过它。

能访问全文 ≠ 我已经读取全文。

URL/Content-Type 说它是 PDF ≠ body 真的是 PDF。

系统里配置了代理 ≠ 程序可以默认信任这个代理。

