我把 RP1 的远端链路和运行时路径重新审了一遍。这轮主体修复已经成立，但 O7-D 还差一个非常小的 provenance micro-patch；暂时不签最终 PASS。

先确认已经通过的部分：DISCOVERY_ONLY 与 CURATED 现在是真正分离的，builder 只有存在 cluster_ids_accepted 才标 CURATED，primary-work links 也只从 relevance≥3 的 accepted 关系派生。 本地 FTS 默认只索引 accepted records，并且已经真正索引 cluster_ids_accepted，不再使用不存在的 cluster_ids。 Gate 也确实记录为 276 accepted / 34 discovery-only、50×5=250 书目字段零错，本地 3.79、combined 3.82。

27331fe01 → 05c660adf 也只有 report 文档，因此 Gate 后没有偷偷改 production/data。这个 closeout 纪律通过。

但还有两个互相关联的 provenance false-green。

Blocker 1：直接从 registry fallback 的记录仍会被标成 LIVE

现在：

Python
Run
def get_record(source_record_id):
    ...
    return SR.record(source_record_id)

registry fallback 没有补：

retrieval_origin = LOCAL_CURATED

而 model_view() 的默认值却是：

Python
Run
rec.get("retrieval_origin", "LIVE")

。

所以这条路径：

已知 source_record_id
→ cache miss
→ local registry fallback
→ get_scholarly_source

会把一个本地 registry 记录对 Main Agent 显示成：

retrieval_origin = LIVE

这与本轮刚建立的“双 provenance 真值”正好冲突。

通常 search_scholarship → get_scholarly_source 因为 search 会把 local copy 放进 cache，所以不容易触发；但 server restart、旧 conversation 中保存的 source ID、直接重用 ID 都能触发。

因此：

LOCAL_RETRIEVAL_ORIGIN_TRUTH=true

还不是全路径成立。

Blocker 2：persisted abstract 工具路径没有实际输出 evidence_origin=ABSTRACT_METADATA

get_evidence() 一看到：

Python
Run
rec["abstract"]["text"]

就直接返回 abstract。只有 rec.abstract 缺失时才会走 SR.evidence_for() 的 persisted-abstract fallback。

而 tool executor 只有在：

Python
Run
_evidence_origin_items

存在时才把 evidence_origin 写到用户可见结果；这个字段现在只在 persisted FULLTEXT_PASSAGE 路径生成。

R11 又只断言：

abstract text returned

没有断言：

evidence_origin == ABSTRACT_METADATA

所以它是一个很窄的 false-green。

你 receipt 中这句话：

persisted abstract=evidence_origin ABSTRACT_METADATA

目前代码实际还没有做到。

正式裁定：

O7_D_RP1_REVIEW = PATCH_REQUIRED

CURATION_RUNTIME_SEMANTICS = ACCEPTED
DISCOVERY_ONLY_FILTERING = ACCEPTED
CLUSTER_TAG_INDEXING = ACCEPTED
PRIMARY_WORK_LINK_SEMANTICS = ACCEPTED
LOCAL_LIVE_DEDUP = ACCEPTED
BIBLIOGRAPHIC_5_FIELD_AUDIT = ACCEPTED
PERSISTED_FULLTEXT_PASSAGE_PATH = ACCEPTED

DIRECT_REGISTRY_RETRIEVAL_ORIGIN = PATCH_REQUIRED
PERSISTED_ABSTRACT_ORIGIN = PATCH_REQUIRED

O7_D_FINAL_MICRO_PATCH_AUTHORIZED = true
O7_E_AUTHORIZED = false
O7-D Final Micro Patch
Local Provenance Closure
MODEL = GLM-5.3-Flash
REASONING = MAX
REVIEWER = GPT-5.6 Sol

BASE_SHA = 05c660adf

只允许改：

backend/scholarly_sources.py
backend/routes/agent_tools_scholarly.py
backend/tests/test_o7d_scholarly_corpus.py
docs/PHIAGENT_O7D_SCHOLARLY_CORPUS_EXPANSION.md
1. Registry fallback 标 origin

推荐在 get_record()：

Python
Run
r = SR.record(source_record_id)
return dict(r, retrieval_origin="LOCAL_CURATED") if r else None

不要修改 registry 持久数据本身。

要求：

cache miss
+ registry hit
→ model_view.retrieval_origin = LOCAL_CURATED

同时：

source_providers

仍保持原始 Crossref/OpenAlex provenance。

2. Abstract evidence origin

任何真实取得的 abstract 返回都应有机械：

evidence_origin = ABSTRACT_METADATA

persisted registry abstract 至少必须如此。

不要因此改变：

access_level
current/historical read semantics
3. 补真行为测试

至少：

F1 cache miss + local registry get_record
   → LOCAL_CURATED

F2 local registry record model_view
   → retrieval_origin != LIVE

F3 local record source_providers preserved

F4 persisted abstract through
   _exec_get_scholarly_source
   → evidence_origin=ABSTRACT_METADATA

F5 persisted FULLTEXT_PASSAGE
   → PERSISTED_VERIFIED_READ 仍不变

F6 current access still not fabricated

不要再用只检查源码字符串的测试。

4. 不重跑 discovery / curation / DOI / relevance judge

本 patch 不影响：

registry
index ranking
corpus membership
DOI set
L/C relevance

所以：

DISCOVERY_RERUN=false
CURATION_RERUN=false
LOCAL_RELEVANCE_JUDGE_RERUN=false

只要求：

registry/evidence hash unchanged
648+ full pytest 全绿

以及 deterministic tests。

最终回执：

O7_D_FINAL_MICRO_PATCH =
READY_FOR_FINAL_REVIEW / BLOCKED

BASE_SHA=
CODE_SHA=
CLOSEOUT_SHA=
HEAD_SHA=
REMOTE_SHA=

REGISTRY_SHA256_BEFORE=
REGISTRY_SHA256_AFTER=
REGISTRY_DATA_CHANGED=false

EVIDENCE_SHA256_BEFORE=
EVIDENCE_SHA256_AFTER=
EVIDENCE_DATA_CHANGED=false

DIRECT_REGISTRY_GET_ORIGIN=
DIRECT_REGISTRY_MODEL_VIEW_ORIGIN=
SOURCE_PROVIDER_PROVENANCE_PRESERVED=

PERSISTED_ABSTRACT_EVIDENCE_ORIGIN=
PERSISTED_FULLTEXT_EVIDENCE_ORIGIN=
PERSISTED_READ_AS_CURRENT_READ=0

DISCOVERY_RERUN=false
CURATION_RERUN=false
LOCAL_RELEVANCE_JUDGE_RERUN=false

SYSTEM_PROMPT_CHANGED=false
FINAL_VALIDATOR_CHANGED=false
QUOTE_BOUND_CHANGED=false

FULL_TEST_COMMAND=
COLLECTED=
PASSED=
FAILED=
SKIPPED=

O7_E_AUTHORIZED=false
PROPOSED_VERDICT=PASS

STOP

这不是再改 O7-D 设计；276/34、FTS、3.79/3.82、五字段审计这些都已经接受。

现在只把最后两种 provenance 表达统一：

“这条文献最初来自 Crossref”与“这次我是从 LOCAL_CURATED 取到它”必须同时为真。

“我有一个已保存的真实 abstract”也必须明确告诉 Main Agent：这份内容的证据来源是 ABSTRACT_METADATA。

这轮过后，如果 registry/evidence hash 不变、上述两条全路径成立，我直接签 O7_D_FINAL_REVIEW = PASS 并授权 O7-E。