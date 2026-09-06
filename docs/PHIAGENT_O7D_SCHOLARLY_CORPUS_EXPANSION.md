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
