我审完 6644a054d → 953ce0d96 → 75a980672 这条远端链路了。O7-D 方向整体成立，但现在还不能签 PASS；需要一个范围很窄的 RP1。

这次不是 provider 单一、FULLTEXT_PASSAGE=0 或 OpenAlex 429 的问题。这三项你都如实披露了，而且任务本身没有要求必须凑出全文证据或双 provider corpus，所以我不拿它们卡 Gate。

真正的问题是：“curation 结果”目前没有真正约束本地研究语料的运行时暴露，而且 LOCAL_CURATED 的 provenance 也没有按契约呈现。

O7_D_REVIEW = PATCH_REQUIRED

DISCOVERY_SNAPSHOT = ACCEPTED
COVERAGE_MANIFEST = ACCEPTED
CROSSREF_ONLY_RUN = ACCEPTED_WITH_LIMITATION
CURATION_JUDGE = ACCEPTED
REGISTRY_FOUNDATION = ACCEPTED
COPYRIGHT_BOUNDARY = ACCEPTED
FTS5_DIRECTION = ACCEPTED
OFFLINE_CAPABILITY = ACCEPTED
ZERO_RESULT_DENOMINATOR_FIX = ACCEPTED

CURATION_RUNTIME_SEMANTICS = NOT_ACCEPTED
LOCAL_CURATED_PROVENANCE = NOT_ACCEPTED
PERSISTED_EVIDENCE_TOOL_PATH = NOT_ACCEPTED
BIBLIOGRAPHIC_AUDIT_COMPLETENESS = PATCH_REQUIRED

O7_D_RP1_AUTHORIZED = true
O7_E_AUTHORIZED = false
Blocker 1：34 条 DISCOVERY_ONLY 实际仍和 accepted records 一样进入本地搜索

你的 corpus manifest 正确地区分了：

records_with_accepted_cluster = 276
records_discovery_only = 34

但是 builder 对所有 record 都无条件写：

Python
Run
"association_status": "CURATED"

哪怕 cluster_ids_accepted=[]。

更关键的是，build_index() 把整个 _registry 全部写进 FTS5，search_local() 也没有按 accepted/discovery-only 过滤。于是那 34 条经过 glm-4.6 判定为 <3、本应只保留作 discovery provenance 的记录，仍然能够作为普通本地研究结果返回给 Main Agent。

换句话说，目前：

curation
→ 影响 coverage 统计

但不影响 runtime scholarly corpus exposure

那么 O7-D 的 curation 实际上只是一层评测标签，不是真正的 curated corpus。

这与任务书中：

relevance >= 3
→ cluster accepted set

低相关
→ DISCOVERY_ONLY

的含义不一致。

而且 model_view() 不暴露 association_status，所以如果 discovery-only record 被搜出来，Main Agent 连“这条只是 discovery candidate”都不知道。

这是本轮主要 blocker。

Blocker 2：cluster tags 实际根本没进 FTS index

registry.jsonl 的字段是：

cluster_ids_accepted
cluster_ids_discovery_only

但 scholarly_registry.build_index() 读取的是：

Python
Run
r.get("cluster_ids")

这个字段不存在。

因此报告里：

FTS5（title/authors/abstract/passages/cluster tags/book ids）

目前并不成立。

Gate 之所以还能拿 3.66，是因为 title 本身已经足够强；这正是一个典型的 false-green：检索质量分数过门，不代表声明的索引字段真的存在。

Blocker 3：LOCAL_CURATED 目前并没有作为 record provenance 暴露

任务书要求：

provider = LOCAL_CURATED
+
保留 Crossref/OpenAlex 原始 provenance

但 registry record 仍只有：

JSON
"provenance": {
  "providers": ["crossref"]
}

例如实际 registry 第一批记录就是如此。

search_local() 只是复制 record，并没有增加 local retrieval origin。

而 model_view() 又直接：

Python
Run
"provider": "/".join(rec["provenance"]["providers"])

所以一个完全离线从 registry 返回的结果，模型看到的仍可能是：

provider = crossref

而不是：

retrieval_origin = LOCAL_CURATED
source_provenance = crossref

顶层 offline note 虽然说“来自本地 registry”，但逐 record provenance 仍然把“我是从哪里取到这条 evidence”与“这条 bibliographic record 最初来自哪里”混在了一起。

O7-C 花了很大力气做 access provenance，O7-D 这里不能重新模糊。

Blocker 4：报告声称 persisted full-text evidence 已接入 get_scholarly_source，实际上只实现了 storage

报告写：

get_scholarly_source 对本地记录……持久化证据带 PERSISTED_VERIFIED_READ

builder 确实能把未来的 FULLTEXT_PASSAGE 存进 evidence.jsonl，这部分没问题。

但 runtime 路径：

get_scholarly_source
→ SS.get_record()
→ SS.get_evidence()

完全没有调用：

SR.evidence_for(source_record_id)

。

D17/D18 也只证明：

SR.evidence_for()

本身能存/读 synthetic historical evidence；并没有证明 get_scholarly_source 会把它返回给 Main Agent。

当前真实 corpus 的 passage 数是 0，所以产品暂时没触发这个 bug；但这属于已经宣称实现的 O7-D capability 实际没接通，而不是未来 feature。

Audit gap：authors 没有纳入书目抽审

任务书要求 50 条抽审：

title
authors
year
venue
DOI

实际 phase_b() 只检查：

Python
Run
title
publication_year
container_title
doi

所以才会得到：

50 × 4 = 200 fields

。

这不表示 authors 有错——它们基本是直接从 provider record 复制的——但 BIBLIOGRAPHIC_WRONG_FIELDS=0 的覆盖范围少了一项。

这一起修掉即可，不需要重新 discovery。

TASK — O7-D RP1
Curated-Corpus Truth & Local Evidence Runtime Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BRANCH =
refactor/phiagent-main-agent-orchestration

BASE_SHA =
75a980672

PHASE =
O7-D RP1 — CURATED CORPUS TRUTH CLOSURE

O7_E_AUTHORIZED = false
0. 范围锁死

不重新 discovery。

冻结并复用：

PHIAGENT_O7D_DISCOVERY_SNAPSHOT.json
discovery_snapshot_hash =
e607bfffb9e74d018474e29cd8294400eabacadffbe7ad53aa9f3b85486bd587

PHIAGENT_O7D_CURATION_DECISIONS.json
coverage manifest
glm-4.6 scores

默认：

DISCOVERY_RERUN = false
CURATION_RERUN = false

只修：

1. accepted vs discovery-only runtime semantics
2. cluster-tag indexing
3. LOCAL_CURATED retrieval provenance
4. persisted evidence → get_scholarly_source
5. authors bibliographic audit

禁止：

- 新 provider
- OpenAlex 补跑
- 新 cluster
- 改 relevance threshold
- 改 judge
- Main Agent prompt
- validator
- quote_bound
- O7-E
1. 修 association status

builder 必须：

if cluster_ids_accepted non-empty:
    association_status = CURATED

else:
    association_status = DISCOVERY_ONLY

要求：

CURATED_RECORDS = 276
DISCOVERY_ONLY_RECORDS = 34
MISLABELED_DISCOVERY_ONLY = 0

数字如果 rebuild 后因原数据定义产生合理变化可以如实报告，但不得通过改 curation score 达成。

2. Local research index 默认只索引 accepted records

推荐：

search_local()
→ CURATED records only

DISCOVERY_ONLY 仍保留在 registry，供：

audit
future recuration
explicit bibliographic lookup

但不得和 accepted scholarly corpus 一样进入普通 search_scholarship()。

也可以设计显式：

include_discovery_only=False

的内部参数，但 Main-Agent tool 不新增这个开关。

硬门：

DISCOVERY_ONLY_IN_DEFAULT_LOCAL_SEARCH = 0
3. cluster tags 修正

FTS index 的 cluster field 改成：

cluster_ids_accepted

不是不存在的：

cluster_ids

至少增加 synthetic/test：

title 无 cluster 关键词
abstract 无 cluster 关键词
cluster_ids_accepted 包含 "kant-schematism"

query = "kant-schematism"
→ record found

再测：

cluster_ids_discovery_only only
→ default local search 不因该 tag 暴露
4. Primary work links 只能从 accepted cluster 派生

当前 builder 会对 cluster 的所有 candidate应用 manifest 的 related_primary_book_ids。

改为：

accepted relevance >= 3
→ may inherit related_primary_book_ids

discovery-only relation
→ must NOT become curated primary-work link

如需保留候选关系：

discovery_candidate_primary_book_ids

可以，但不是必须。

硬门：

DISCOVERY_ONLY_CURATED_PRIMARY_LINKS = 0
5. Retrieval origin 与 source provenance 分开

不要破坏 O7-C provenance.providers。

保��：

provenance.providers = ["crossref", ...]

表示 bibliographic origin。

local retrieval 返回时 additive：

retrieval_origin = LOCAL_CURATED

live：

retrieval_origin = LIVE_CROSSREF
LIVE_OPENALEX
或 LIVE_COMBINED

具体 enum 可以更简单，只要语义清楚。

model_view() 至少给 Main Agent：

retrieval_origin
source_providers

而不是只有一个混合的 provider 字符串。

兼容旧字段可保留。

6. Offline truth

双 provider 失败、本地返回时，每条结果必须：

retrieval_origin = LOCAL_CURATED

同时：

source_providers

仍显示原始 Crossref/OpenAlex provenance。

测试：

offline local Crossref-derived record:

retrieval_origin = LOCAL_CURATED
source_providers = ["crossref"]

NOT:
retrieval_origin = crossref
7. Local/live duplicate merge provenance

同 DOI local+live：

仍一个 canonical result。

至少记录：

retrieval_origin = LOCAL_CURATED+LIVE

或等价结构。

同时不得丢：

original source provider provenance

不要求做复杂字段 reconciliation；O7-C conflict 逻辑仍冻结。

8. Persisted Evidence Runtime Path

实现真正的 local evidence fallback。

当 get_record(sid) 来自 registry，且存在：

SR.evidence_for(sid)

时：

ABSTRACT

已有 persisted abstract：

requested_access=ABSTRACT
→ 可直接返回 persisted abstract
→ evidence_origin=ABSTRACT_METADATA
FULLTEXT_PASSAGE

若：

ingest.access_level_at_ingest = FULL_TEXT_READ
+
stored FULLTEXT_PASSAGE exists

则：

requested_access=FULL_TEXT_IF_LEGALLY_AVAILABLE

允许先返回：

stored evidence_passages
evidence_origin=PERSISTED_VERIFIED_READ

并明确：

“此前验证读取并持久化的证据节选；
本轮未重新获取全文。”

不得因此声称当前 URL 仍可访问。

9. Historical/current access 分开

对 persisted verified read：

不要把 runtime record 虚构成：

current access = FULL_TEXT_READ

除非当前已实际重新读取。

保留：

access_level_at_ingest = FULL_TEXT_READ
evidence_origin = PERSISTED_VERIFIED_READ

而 current：

access.level

仍按当前已知状态。

需要的话增加：

historical_evidence_level

机械字段。

10. Synthetic fulltext evidence test 必须走真实 tool executor

不要再只：

SR.evidence_for()

。

新增 synthetic/temporary registry evidence fixture，通过：

_exec_get_scholarly_source(...)

或公开等价 runtime path。

要求返回：

evidence_passages
evidence_origin=PERSISTED_VERIFIED_READ

且：

LIVE_CURRENT_READ = false
11. Authors Audit

phase_b() 改为五字段：

title
authors
publication_year
container_title
doi

authors 应做 provider-derived normalized structural comparison。

不要粗暴：

str(listA) == str(listB)

建议规范为：

[(normalized name, normalized orcid), ...]

要求：

BIBLIOGRAPHIC_AUDIT_RECORDS=50
BIBLIOGRAPHIC_FIELDS_CHECKED=250
BIBLIOGRAPHIC_WRONG_FIELDS=0

如确实发现错：

进入真实 data repair，不准从 audit 中排除 authors。

12. Registry rebuild

复用 frozen snapshot + frozen curation。

执行：

dp_o7d_registry.py

必须仍确定性。

重新记录：

REGISTRY_SHA256
EVIDENCE_SHA256

不要求保持旧 hash，因为 association/index-related corpus semantics 会变。

13. Local gate 重跑

不需要重新跑 discovery/curation。

但必须重跑：

L local-only
C combined
R registry
B bibliographic
E evidence

DOI 数据若 registry DOI 集完全不变，可以复用旧 310/0，并通过 deterministic assertion 证明 DOI set hash unchanged。

若 DOI set 变化：

完整重跑 D。

14. Combined retrieval

保持硬门：

LOCAL_QUERY_RELEVANCE_RATE >= 90%
LOCAL_TOP5_RELEVANCE_MEAN >= 3.0

COMBINED_TOP5_RELEVANCE_MEAN
>= LOCAL_TOP5_RELEVANCE_MEAN - 0.1

LOCAL_LIVE_DUPLICATES_IN_TOP5 = 0

如果 discovery-only 过滤后分数上升/下降，都如实记录。

15. Curation Semantics Audit

新增：

ACCEPTED_UNIQUE_RECORDS
DISCOVERY_ONLY_UNIQUE_RECORDS

DEFAULT_INDEXED_RECORDS

要求：

DEFAULT_INDEXED_RECORDS =
records with >=1 accepted cluster

即当前预期：

276

并：

DISCOVERY_ONLY_INDEXED_BY_DEFAULT=0
16. No false report

报告修正以下口径：

旧：

LOCAL_CURATED 是 provider

新应精确区分：

retrieval_origin = LOCAL_CURATED
bibliographic source providers = Crossref/OpenAlex

同时注明：

O7-D initial gate indexed discovery-only records;
RP1 corrected curated-corpus exposure semantics.

保留历史，不改写旧结果。

17. Tests

至少新增/修正：

R1 discovery-only association_status correct
R2 accepted association_status correct
R3 default local index excludes discovery-only
R4 accepted cluster tags actually indexed
R5 nonexistent cluster_ids field no longer used

R6 discovery-only doesn't inherit curated primary links

R7 local result retrieval_origin=LOCAL_CURATED
R8 source provider provenance preserved
R9 offline result not mislabeled as live
R10 local/live DOI dedup preserves retrieval-origin truth

R11 persisted abstract returned through tool path
R12 persisted fulltext passage returned through tool path
R13 persisted read labelled PERSISTED_VERIFIED_READ
R14 persisted read not labelled LIVE_CURRENT_READ
R15 current access not fabricated from historical read

R16 bibliographic audit includes authors
R17 50×5=250 field checks

R18 deterministic registry rebuild
R19 prompt/validator frozen
18. Hard gates
CURATED_RECORDS >= 240
DISCOVERY_ONLY_MISLABELED = 0

DISCOVERY_ONLY_IN_DEFAULT_LOCAL_SEARCH = 0
DISCOVERY_ONLY_CURATED_PRIMARY_LINKS = 0

CLUSTER_TAG_INDEX_WORKS = true

LOCAL_RETRIEVAL_ORIGIN_TRUTH = true
SOURCE_PROVIDER_PROVENANCE_PRESERVED = true

PERSISTED_EVIDENCE_TOOL_PATH = true
PERSISTED_READ_AS_CURRENT_READ = 0

BIBLIOGRAPHIC_AUDIT_RECORDS >= 50
BIBLIOGRAPHIC_FIELDS_PER_RECORD = 5
BIBLIOGRAPHIC_WRONG_FIELDS = 0

ZERO_RESULT_QUERY_DENOMINATOR_LOSS = 0

LOCAL_QUERY_RELEVANCE_RATE >= 90%
LOCAL_TOP5_RELEVANCE_MEAN >= 3.0

COMBINED_TOP5_RELEVANCE_MEAN
>= LOCAL_TOP5_RELEVANCE_MEAN - 0.1

LOCAL_LIVE_DUPLICATES_IN_TOP5 = 0

FABRICATED_BIBLIOGRAPHIC_FIELDS = 0
INVALID_VERIFIED_DOI = 0

COPYRIGHT_UNAUTHORIZED_FULLTEXT_STORED = 0

SYSTEM_PROMPT_CHANGED = false
FINAL_VALIDATOR_CHANGED = false
QUOTE_BOUND_CHANGED = false

FULL_TEST_FAILED = 0
Final receipt
O7_D_RP1 =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=

CODE_SHA=
O7D_RP1_CORPUS_GATE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

DISCOVERY_RERUN=false
CURATION_RERUN=false

DISCOVERY_SNAPSHOT_HASH=
CURATION_DECISIONS_HASH=

REGISTRY_SHA256=
EVIDENCE_SHA256=

CURATED_RECORDS=
DISCOVERY_ONLY_RECORDS=
DISCOVERY_ONLY_MISLABELED=

DEFAULT_INDEXED_RECORDS=
DISCOVERY_ONLY_IN_DEFAULT_LOCAL_SEARCH=

CLUSTER_TAG_INDEX_WORKS=
DISCOVERY_ONLY_CURATED_PRIMARY_LINKS=

LOCAL_RETRIEVAL_ORIGIN_FIELD=
OFFLINE_LOCAL_ORIGIN_VALUE=
SOURCE_PROVIDER_PROVENANCE_PRESERVED=

PERSISTED_ABSTRACT_TOOL_PATH=
PERSISTED_FULLTEXT_PASSAGE_TOOL_PATH=
PERSISTED_READ_AS_CURRENT_READ=

BIBLIOGRAPHIC_AUDIT_RECORDS=
BIBLIOGRAPHIC_FIELDS_PER_RECORD=
BIBLIOGRAPHIC_FIELDS_CHECKED=
BIBLIOGRAPHIC_WRONG_FIELDS=

DOI_SET_HASH_CHANGED=
INVALID_VERIFIED_DOI=

LOCAL_QUERY_COUNT=
LOCAL_QUERIES_WITH_RELEVANT_RECORD=
LOCAL_QUERY_RELEVANCE_RATE=
LOCAL_TOP5_RELEVANCE_MEAN=

COMBINED_QUERY_COUNT=
COMBINED_TOP5_RELEVANCE_MEAN=
LOCAL_LIVE_DUPLICATES_IN_TOP5=

ZERO_RESULT_QUERY_DENOMINATOR_LOSS=

COPYRIGHT_UNAUTHORIZED_FULLTEXT_STORED=

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

O7-D 首轮其实已经把最难的规模问题做出来了：38 簇、310 条真实 canonical records、离线 3.66、100% DOI 验证、没有为了填量去编全文或许可，这些我都认可。

RP1 不是再扩数据，而是把最后一个语义差别钉死：

“我把一条低相关记录留在 registry 里”不等于“我已经接受它进入 curated research corpus”。

以及：

“这条记录最初来自 Crossref”与“这次回答是从本地 curated corpus 取到它”是两种不同的 provenance。

把这两层分开，O7-D 才真正配得上“Scholarly Corpus Expansion”，而不只是“一个带 relevance 标签的大书目缓存”。