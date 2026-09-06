# PhiAgent O7-D — Scholarly Corpus Expansion & Research Evidence Layer

> BASE_SHA=6644a054d ｜ CODE_SHA=953ce0d96 ｜ DISCOVERY_SNAPSHOT_SHA（hash）=e607bfffb9e74d01…
> O7D_CORPUS_GATE_SHA= 本 gate 产物 commit（=953ce0d96, gate json 已入库）
> Reviewer 注记承接: O7-C evaluator 分母修复（§2, 4e727a8a6）+ 报告 611/612 笔误更正（实际 612）

## 1. Corpus Philosophy（§0-§5）

Primary Corpus / O7-B Bibliography / **Scholarly Source Registry** / Local Evidence
Index / O7-C Live Providers 五层落位; Main Agent 仍是唯一研究决策者。
Registry（curated/versioned/reproducible）≠ runtime cache; 语料单位 =
SOURCE RECORD + ACCESS PROVENANCE + 可选 ABSTRACT + 可选 VERIFIED PASSAGES。

## 2. Coverage Manifest（§8-§10）

**38 research clusters × 8 period/tradition groups**（≥30/≥8 硬门 ✅; 中国哲学 5 簇
≥4 ✅）: Ancient Greek 5 / Late Antiquity-Medieval 4 / Early Modern 5 /
Kant-German Idealism 5 / 19th Century 5 / 20th Analytic 5 / 20th Continental 4 /
Chinese 5。每簇是学术问题（thing-in-itself interpretation / private language /
ren-li / Zhuangzi skepticism…）; primary links 为 manifest curation（CURATED）,
无 LLM 静默归类。WORK_IDENTITY 局限如实继承（title-author derived /
CROSS_TITLE_RECONCILIATION=NOT_IMPLEMENTED）。

## 3. Discovery Snapshot（§12/§28-§29）

38 簇 × manifest 查询 × Crossref+OpenAlex → canonical dedup → **310 unique
records**, snapshot 冻结（hash e607bfff…, DISCOVERY RUN 与 REGISTRY BUILD 分离,
registry 确定性重建 D6 锁定）。
**如实披露**: OpenAlex 当日 API 预算耗尽（"Insufficient budget… resets at midnight
UTC"）, 39 次调用全部 429（含 mailto 礼貌池+指数退避后仍耗尽）——本轮语料
100% 来自 Crossref provider records; retrieval failure ≠ scholarly absence,
错误全部如实保留在 snapshot.errors。

## 4. Curation（§13-§14）

glm-4.6（official judge）evaluation-only 判 312 个 (cluster, record) 对
TOPICAL_RELEVANCE 0-4（输入仅 topic+title+abstract+出版元数据; judge 无权
补/改任何书目字段）: **277 对 ≥3 → accepted**; 低相关记录保留为
DISCOVERY_ONLY（34 条, 不删除 §14）。

## 5. Registry / Evidence（§3-§7/§17-§19/§36）

`backend/data/scholarly/registry.jsonl`（310 条, git 跟踪 corpus asset）+
`evidence.jsonl`（26 条 ABSTRACT 证据: text+source+hash+origin=ABSTRACT_METADATA）
+ `corpus_manifest.json`（双 sha256）。O7-C identity 全复用（source_record_id/
identifiers/provider_records/provenance/conflicts/access）; 新增 cluster_ids_*
（accepted/discovery_only 分列）, related_primary_book_ids, access_level_at_ingest
（历史状态, 不因后续 URL 变化抹除 §36）, reuse_status（默认 UNKNOWN, 不猜 CC-BY §7）。
**FULLTEXT_PASSAGE=0**: 全文证据层机制已实现并测试（D10: 仅 FULL_TEXT_READ+
PDF body 签名+hash 可持久, ≤1200 字 ≤5 段），但本轮 310 条候选无已验证 OA PDF
（OpenAlex 耗尽 → 无 DIRECT_PDF 候选; Crossref 不提供 OA 位置）——如实为 0,
不虚构。整篇正文零持久化（D11）。

## 6. Local Index（§21-§22）

SQLite FTS5（title/authors/abstract/passages/cluster tags/book ids; OR 语义+
bm25 排序）——简单透明, 无新造 embedding/reranker stack。primary retrieval
零改动（D25）。

## 7. Local/Live Integration（§23-§27/§46-§49）

- search_scholarship = **LOCAL_CURATED + Crossref + OpenAlex** 三源合并,
  同 id/DOI 去重（LOCAL_LIVE_DUPLICATES_IN_TOP5=0, D4/D16）;
  模型视图仍走 O7-C model_view（紧凑, D29）; 工具数不变（32, 无第三工具）。
- 离线语义: 双 live provider 失败而本地有结果 → `offline_mode=true` +
  「外部 provider 当前失败…来自已验证的本地学术 registry, 非实时检索」（D13-D15）;
  provider 错误原样保留。
- get_scholarly_source 对本地记录: registry 回退（get_record）, 持久化证据
  带 evidence_origin（ABSTRACT_METADATA / PERSISTED_VERIFIED_READ——历史验证读
  ≠ 本轮实时读, D17/D18）; 无自动刷新（D23）。
- LOCAL_CURATED 是 provider 不是 authority: 每条保留原始 provider provenance（§24）。

## 8. Gates（§38-§42/§55）

固定 22 查询宇宙（O7-C canonical 6 + 14 + 负面 2; 分母含零结果, §41/D1）:

| 指标 | L（离线本地） | C（合并 live） | 硬门 |
|---|---|---|---|
| SUBSTANTIVE_QUERIES_WITH_RELEVANT | **20/20=100%** | 20/20 | ≥90% ✅ |
| TOP5_RELEVANCE_MEAN | **3.66** | **3.68** | L≥3.0 ✅; C≥3.66-0.1 ✅ |
| NEGATIVE FP / CONTROL | 0 / PASS | 0 / PASS | ✅ |
| DUPLICATE_IN_TOP5 | 0 | 0 | ✅ |

簇覆盖: **38/38 1+（100% ≥95%）, 38/38 3+（100% ≥90%）**; CANONICAL_RECORDS=310 ≥240。

审计: R（dup id/doi/silent conflict = 0/0/0）· D（310 DOI 100% doi.org 复验,
INVALID=0）· B（50 records×4 字段 seed 抽样, WRONG=0）· E（evidence 26 条,
ORPHAN=0, FAKE_LOCATOR=0）。

## 9. Architecture Invariants（§50-§52）

ENGINE_COGNITIVE_AUTO_SCHOLARLY_TOOLS=0 / SCHOLARLY_SUFFICIENCY_GATES=0 /
SCHOLARLY_SEMANTIC_ROUTERS=0 / COGNITIVE_POLICY_OWNER=1;
SYSTEM_PROMPT/FINAL_VALIDATOR/QUOTE_BOUND/O7-B data（bf7ad525…）/O7-C access
语义全部不变（D24-D27/D30）。无 proposition DB / InterpretationController（D21/D22）。

## 10. Tests

D1（o7c 套件）+ D2-D30 共 29 项新测试; 全量 **635 passed / FAILED=0 / SKIPPED=0**。

## 11. Limitations（如实）

1. 本轮语料单一 provider（Crossref）——OpenAlex 当日预算耗尽; 预算重置后可增量
   扩充（discovery 增量+curation 续跑+registry 重建管线已就绪）。
2. FULLTEXT_PASSAGE=0（无已验证 OA PDF 候选）; abstract 覆盖 26/310。
3. 簇 primary-work 关联仅显式 curated 部分; 跨题名 work 归并未实现（继承 O7-B）。

## 12. O7-E Readiness

证据基础设施齐备: 原典语料（O6）+ 书目（O7-B）+ 真实文献检索与访问真值（O7-C）+
可持续本地语料层（O7-D）。O7-E（Scholarly Quality Gate 双轴 + Scholarly Policy
activation）所需的生产 prompt 解冻在 O7-E 任务书授权后进行。


---

# O7-D RP1 — Curated-Corpus Truth & Local Evidence Runtime Closure（2026-09-06）

> BASE_SHA=75a980672 ｜ CODE_SHA=898359db7（基线回填 deedb7747）
> O7D_RP1_CORPUS_GATE_SHA=27331fe01 ｜ CLOSEOUT_SHA= 本 docs-only commit（=HEAD, ≠GATE）

## 修复对照（五项）

1. **association_status 真值**: CURATED=276（cluster_ids_accepted 非空）/
   DISCOVERY_ONLY=34; primary-work links 仅从 accepted（relevance≥3）关系派生
   （discovery-only 记录 curated primary links=0）。
2. **默认索引=curated corpus**: build_index 只索引 accepted（276）;
   search_local 默认排除 discovery-only; cluster_ids_accepted 实际进入 FTS
   （含引号短语精确命中, 修掉不存在的 cluster_ids 字段——此前 gate 3.66 只是
   title 强度的 false-green）。
3. **retrieval_origin 与 source provenance 分离**: 本地=LOCAL_CURATED /
   live=LIVE_CROSSREF|LIVE_OPENALEX|LIVE_COMBINED / 合并命中=LOCAL_CURATED+LIVE;
   model_view 暴露 retrieval_origin + source_providers（保留旧 provider 兼容字段）;
   bibliographic origin（Crossref/OpenAlex）不丢。
4. **持久证据走真实工具路径**: get_scholarly_source 对 registry 记录回退
   SR.evidence_for——persisted abstract（ABSTRACT_METADATA）与 persisted passages
   （PERSISTED_VERIFIED_READ, 附「此前验证读取并持久化…本轮未重新获取全文」）
   经 _exec_get_scholarly_source 真实返回（R11-R15 工具路径测试, 非仅 SR 层）;
   historical_evidence_level 与当前 access 分离, 历史读不虚构当前读。
5. **书目审计五字段**: title/authors/year/venue/DOI——authors 归一化结构比较
   [(name, orcid)]; 50×5=250 字段, WRONG=0。

## 冻结后重跑（复用 frozen snapshot+ curation; D 阶段 DOI 集确定性复用）

R: dup id/doi/silent=0/0/0, accepted 276 / discovery 34 ｜
B: 50 records×5=250 字段 WRONG=0 ｜
E: 26 abstract 证据, ORPHAN=0 ｜
D: DOI 集 hash 36a10440… 未变 → 复用 310/INVALID=0 ｜
**L: 20/20=100%, mean 3.79**（原 3.66——过滤 discovery-only 后上升）｜
**C: 20/20, mean 3.82 ≥ 3.79-0.1** ｜ dup=0, negatives 0 FP。

## 报告口径修正（§16）

旧「LOCAL_CURATED 是 provider」精确化为: retrieval_origin=LOCAL_CURATED（取到
证据的渠道）+ bibliographic source providers=Crossref（记录来源）。历史保留:
O7-D initial gate 曾索引 discovery-only records, RP1 修正了 curated-corpus 暴露
语义（旧数字不改写, 见上文 §8 原值）。

## 测试: R1-R19 19 项; 全量 648 passed / FAILED=0 / SKIPPED=0
