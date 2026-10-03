
Reviewer 裁定如下：

ROOT_CAUSE = MIXED，成立，但需要重新分层。

PRIMARY — QUERY_FORMULATION_FAILURE：CONFIRMED。 R25 实际发生 3 次 search_scholarship，却取得 28 条高度无关结果；与此同时，离线 registry 用 Wang Yangming / Wang Shouren / Zhu Xi / unity of knowledge and action / gewu 等英文查询可以命中。这足以证明“当前 scholarly retrieval planning 没把可检索资源召回”。但由于 per-call query/args 已不可恢复，不能进一步声称某个具体 query 字符串写错了。

SECONDARY — CORPUS_COVERAGE_GAP：CONFIRMED，但应精确命名为 MULTILINGUAL_ALIAS_INDEX_COVERAGE_GAP。 这不是“库里没有王阳明”，因为英文查询已有命中；真正的问题是中文实体名、概念名、英译/罗马字与 registry 索引之间存在断层。可以继续映射到现有 CORPUS_COVERAGE_GAP 大类。

ACCESS_DEPTH_GAP：OBSERVED / CONTRIBUTING，不裁为本次 primary root cause。 FETCH_CALLS=0 是事实，但在 search 已经返回无关材料的情况下，继续 fetch 那 28 条反而是错误行为。因此它是下一阶段必须补齐的 retrieval pipeline 缺口，不是造成 R25 首次召回失败的首因。

SAFE_FALLBACK：继续 PASS。 Agent 在无相关内容证据时没有伪造“学界两派”，而是明确说明限制并回到原典，这是正确行为，不得作为修复对象。

因此你的 PROPOSED_NEXT = COMBINED 方向通过，但我将 CORPUS_EXPANSION 收窄为：先 alias/index enrichment，只有确证内容记录本身不足时才补 corpus。V3 已消费，禁止拿 28-case holdout 做调参或再判分。

下面直接下阶段任务书。

Edit
PhiAgent O7-E — V3-RP3 Scholarly Retrieval Recovery

MODEL: GLM-5.3（Builder）
PRODUCTION_MODEL: deepseek-v4-flash，不得更改。
BASE: 5835da17a
Reviewer: GPT-5.6 Sol
目标: 修复 scholarly retrieval 的召回、双语 alias/index 覆盖和 READ 深度；不得重开 V3 measurement chain。

0. Frozen / 禁止事项

以下继续 FROZEN：

measurement chain

Local Patch / validator

quote_bound

replay

alias resolver

RP-B

PRODUCTION_MODEL=deepseek-v4-flash

V3 28-case holdout 与全部既有 V3 evidence

禁止：

重跑/改写 V3 28 case；

修改 V3 judge 分数或 final-gate 结果；

用 V3 holdout 调 prompt；

将 search/fetch 写成 runtime 强制循环；

为了过门而伪造 scholarship evidence；

破坏当前 SAFE_FALLBACK。

1. RCA 固化

新增 canonical RCA 结论，引用：

docs/evidence/V3_R25_RETRIEVAL_RCA.json

记录：

PRIMARY_ROOT_CAUSE=
QUERY_FORMULATION_FAILURE

SECONDARY_ROOT_CAUSE=
CORPUS_COVERAGE_GAP:
MULTILINGUAL_ALIAS_INDEX_COVERAGE_GAP

CONTRIBUTING_GAP=
ACCESS_DEPTH_GAP

SAFE_FALLBACK=
PASS

必须注明：

per-call query/args unavailable because done.result_full stripped them

所以不得声称恢复出了 R25 的真实 query 文本。

2. Query Formulation Patch

只修改 scholarly-search 使用说明 / tool contract / Main Agent retrieval guidance，不得硬编码 R25 答案。

加入通用规则：

对于非英语哲学家、术语、经典或学派，Main Agent 在 scholarly retrieval 时应自主考虑：

原语言名称；

通行英文名；

罗马化/别名；

核心概念的通行英译；

人物 + 概念；

作品 + 概念；

首轮结果明显离题时，更换语言或关键词重新 formulation。

例如测试可以覆盖：

王阳明 / Wang Yangming / Wang Shouren

但实现不得专门 if 王阳明 then ...。

保留 Main Agent 自主判断；不得规定“必须搜索 N 次”。

3. Registry Alias / Index Recovery

检查 O7-D curated registry。

优先修复 alias/index coverage，而不是无差别扩充 corpus。

至少使同一相关记录能够被合理查询族召回：

王阳明
Wang Yangming
Wang Shouren

朱熹
Zhu Xi

知行合一
unity of knowledge and action

格物
gewu
investigation of things

Neo-Confucianism
新儒家/宋明理学相关规范名称

如现有记录内容不足以支撑 scholarly READ，再增加最小必要 curated records。

所有新增记录必须保持现有 O7-D provenance/evidence contract，不得加入来源不明内容。

4. Access Depth Patch

目标链：

SEARCH
  ↓
relevance judgment
  ↓
relevant candidate exists
  ↓
READ/FETCH content
  ↓
content evidence
  ↓
scholarly synthesis

要求：

search result 相关时，guidance 应明确鼓励进入 READ/FETCH；

search result 不相关时，不得为了制造 FETCH_CALLS>0 而读取垃圾结果；

无相关证据时，SAFE_FALLBACK 仍允许且必须明确无内容证据；

不得把“search metadata / title / snippet”自动当成完整 scholarship content evidence。

Contract V4 已有 READ obligation 的部分应复用，不建立第二套冲突规则。

5. Tests

新增 regression/dev tests，不得使用 V3 holdout 作为调参集。

A. Offline registry tests

CN/EN alias families 均须验证。

Gate：

EN_RELEVANT_RETRIEVAL=PASS
CN_RELEVANT_RETRIEVAL=PASS
ALIAS_EQUIVALENCE=PASS
UNRELATED_TOP_RESULT_REGRESSION=PASS
B. Search → Read contract tests

覆盖：

有相关搜索结果 → 可进入 READ/FETCH；

首轮无关 → 可以 reformulate；

第二语言/alias 可取得相关结果；

无任何相关材料 → SAFE_FALLBACK；

不允许把 irrelevant search result fetch 后伪装成 evidence。

C. R25 regression probe

R25 只能作为已知开发 regression probe：

目标是证明修复后的路径现在可以找到 registry 中已经存在的王阳明相关候选并读取内容。

不得：

R25_REJUDGE_V3=true
V3_SCORE_UPDATE=true
V3_FINAL_GATE_UPDATE=true
6. Evidence

新增独立 evidence artifact，例如：

docs/evidence/V3_RP3_RETRIEVAL_RECOVERY.json

至少记录：

BASE / HEAD

changed files

query-family probe

CN/EN hit results

relevant vs irrelevant判定

search calls

read/fetch calls

content evidence count

SAFE_FALLBACK regression

V3 frozen artifact hashes / drift result

要求：

V3_EVIDENCE_DRIFT=false
7. Exit Gate

RP3 只有满足全部以下条件才可交 Reviewer：

QUERY_FORMULATION_GUIDANCE=PASS
MULTILINGUAL_ALIAS_COVERAGE=PASS
RELEVANT_SEARCH_RESULT_AVAILABLE=PASS
SEARCH_TO_READ_PATH=PASS
CONTENT_EVIDENCE_PATH=PASS
SAFE_FALLBACK_REGRESSION=PASS
V3_EVIDENCE_DRIFT=false
PRODUCTION_MODEL_UNCHANGED=true
FROZEN_COMPONENT_DIFF=0

本阶段不得宣称：

V3_SCHOLARLY_GATE_MET
O7-E_PASS
FINAL_PASS

完成后唯一允许状态：

READY_FOR_V3_RP3_REVIEW

并提交 commit SHA、测试结果、evidence artifact 路径及简短回执后 STOP。

这里还有一个关键 Reviewer 决定：RP3 通过后也不直接改 V3 的 FAIL。 V3 的 V3_SCHOLARLY_GATE_NOT_MET 是已经发生的、合法的历史测量结果，必须永久保留。RP3 如果通过，我下一步会签发的是 V4 fresh scholarly qualification / fresh holdout，用未消费的新 case 判断修复后的系统，而不是“把 V3 修成 PASS”。这能保证整个 evidence chain 干净。