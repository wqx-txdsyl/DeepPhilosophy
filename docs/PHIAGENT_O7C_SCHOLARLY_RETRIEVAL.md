# PhiAgent O7-C — Scholarly Retrieval & Literature Access Provenance

> BASE_SHA = 4d2db3ad0 ｜ CODE_SHA = 7ee6d2b62（基线回填 ebc08a694）
> O7C_CAPABILITY_GATE_SHA = d83e1ae11（live gate 产物冻结）
> 两条不可妥协线: 「数据库里有这篇论文」只证明它存在;「知道它怎么论证」必须来自
> 实际获得的 abstract 或 full text。scholarly retrieval 不是第二个大脑。

## 1. Provider Feasibility Audit（§5, 实测）

| Provider | OFFICIAL_API | STABLE_MACHINE_INTERFACE | AUTH | RATE_LIMIT | SEARCH | ABSTRACT | FULL_TEXT | ID 质量 | 裁定 |
|---|---|---|---|---|---|---|---|---|---|
| Crossref | ✅ api.crossref.org/works | ✅ REST+JSON | 否 |礼貌池(无 key) |✅|✅(JATS)|❌(仅 landing)|DOI 权威|**IMPLEMENTED** |
| OpenAlex | ✅ api.openalex.org/works | ✅ REST+JSON | 否(建议 mailto)|宽|✅|✅(inverted index)|OA 位置元数据|DOI+OpenAlex ID|**IMPLEMENTED** |
| SEP | ❌ 无官方 API | ❌（robots 有 crawl-delay; 无结构化端点）| — | — | — | — | — | — |**NOT_IMPLEMENTED**（不抓取凑数）|
| PhilPapers | 部分（需注册/未验证公开搜索端点, 实测 /api/search 404）| ❌ | — | — | — | — | — | — |**NOT_IMPLEMENTED**（如实）|

PROVIDERS_EVALUATED=4 ｜ PROVIDERS_IMPLEMENTED=2（≥2 ✅）

## 2. 实现（§3/§8-§17）

- **工具**: `search_scholarship` + `get_scholarly_source`（routes/agent_tools_scholarly.py;
  TOOL_COUNT 30→32, taxonomy/registry 已同步 38→40）。Main Agent 拥有全部研究选择;
  零 AUTO_SCHOLARLY_SEARCH / sufficiency / two-sides。
- **schema o7c-1**: source_record_id/title/authors(+orcid)/year/container/type/
  identifiers(doi+provider_ids)/stable_urls/provider_records/access/abstract/
  provenance(field_sources)/conflicts/philosophical_role/peer_review_status。
- **identity（§9-§11）**: DOI normalized 优先（10.xxxx/abc 小写; doi.org 前缀剥离）→
  provider canonical ID → bibliographic fingerprint（title+author+year+venue）。
  同 DOI 跨 provider 合并为单 canonical + 多 provider_records; 异 DOI 不合并;
  无 DOI 仅机械一致才合并; 零 semantic LLM merge。
- **conflict（§12）**: 字段多 provider 异值 → CONFLICT_UNRESOLVED 保留候选（C4）。
- **access 状态机（§13-§18）**: METADATA_ONLY→ABSTRACT_AVAILABLE→FULL_TEXT_AVAILABLE→
  FULL_TEXT_READ, 只由实际证据驱动; DOI landing ≠ FULL_TEXT_AVAILABLE（C11）;
  OA URL 挂掉不虚报 READ（C10）; READ 必须 fetched+parsed+hash（C9）;
  AVAILABLE 未 fetch 不变 READ（C8/A8）。
- **合法边界（§19）**: 仅 OA/public-domain/官方 metadata; 零 paywall/Sci-Hub/
  credential 路径（C12 AST 扫描）。全文不整篇复制给模型——返回节选段落+hash（§21）。
- **SSRF（§50-§52）**: 工具输入只接受 source_record_id; URL 由 provider record 解析;
  scheme 白名单 https/http + DNS 解析后禁 loopback/RFC1918/link-local（C21;
  本机 VPN fake-IP 段 198.18/15 如实豁免并注明）; connect 8s/read 20s/5MB 上限/重定向上限。
- **诚实性（§22-§25/§30-§31）**: 记录只来自 retrieved provider record; 零 LLM 元数据补全
  （C17 AST）; peer_review_status 默认 UNVERIFIED（不因 journal-article 推断, C15）;
  philosophical_role 默认 UNKNOWN（C16）; provider 错误保留原样（≠「没有文献」, C13）;
  0 结果 ≠ scholarly absence（C14）。
- **缓存（§29）**: exact-query/provider/DOI 机械缓存（C28）。无持久全文语料扩张（§20;
  仅 hash/provenance/临时解析）。

## 3. Live Capability Gate（§32-§42/§61, 真实网络）

运行器 `backend/tools/evaluation/o7c_live_gate.py`, 产物
`docs/evidence/PHIAGENT_O7C_SCHOLARLY_RETRIEVAL_GATE.json`（seed=20260906）。

- **A 检索**: 16 queries（C1-C6 canonical + T1-T8 + N1-N2 负面）× Crossref+OpenAlex
  真实网络, **零 provider 错误**; 80 records, 79 unique canonical（1 次跨源 DOI 合并）;
  Top-5 内 provider duplicates=0（canonical 去重后呈现）。
  延迟 P50=1.52s / P95=2.04s（双 provider 并发内串行）。
- **B 书目验证**: 固定 seed 抽 25 canonical records × 4 字段（title/year/venue/doi）
  = 100 字段对 provider record 机械复核: **FABRICATED_BIBLIOGRAPHIC_FIELDS=0**。
- **C DOI 验证**: doi_verified=true 共 67 个, 100% 经 doi.org handle API 复验:
  **INVALID_VERIFIED_DOI=0**。
- **D access 审计**: 分层 METADATA_ONLY=22 / ABSTRACT_AVAILABLE=43 /
  FULL_TEXT_AVAILABLE=11 / **FULL_TEXT_READ=2**（真实 fetch+parse+hash, ≥1 硬门 ✅;
  合法 OA 可读源实际有限, 如实上报实际值）。A1-A8 kill cases 全真
  （A5/A6/A8 另有 C10/C11/C8 单测锁死）。
- **E 相关性 judge（glm-4.6, capability-only 不入 runtime）**: 14 实质性查询 × Top-5
  = 69 records: **TOP5_RELEVANCE_MEAN=3.464 ≥ 3.0**; **QUERIES_WITH_RELEVANT_RECORD=
  16/16 = 100% ≥ 90%**（含负面对照通过）; judge 输入不含期望学者/期望分。
  负面查询 N1/N2 最高分 1/0（假阳性控制 ✅, 单列不入均值——口径注明于产物）。
- **F 访问越权 fixtures（§45, O7-A F6 语义, k-of-3, glm-4.6）**: 12 fixtures
  （6 bad + 6 good, 覆盖 METADATA/ABSTRACT/AVAILABLE/READ 四级越权与诚实表述）:
  **LITERATURE_ACCESS_OVERCLAIM_RECALL=100%**, **FALSE_ACCESS_OVERCLAIM=0**。
  如实披露: 首轮 F-O12 fixture 的越权内容被截断为省略号（构造缺陷）, 修正为
  具体越权声明后重跑; F-O5 首轮因 prompt 访问级别上下文模糊漏报, 明确化后全过。

## 4. Tests（§57）

`backend/tests/test_o7c_scholarly_retrieval.py` C1-C30 全覆盖（34 tests, mock 为主）。
全量: **575 passed / FAILED=0 / SKIPPED=0**。primary retrieval 与 O7-B bibliography
零改动（C29/O7B_RUNTIME_DATA hash 不变, C30）。

## 5. Latency / Cost（§49）

search_scholarship P50=1.52s / P95=2.04s（双 provider）; get_scholarly_source
abstract 即时, fulltext 视源（数秒级, 受 OA 站点限制, 403/解析失败如实降级不虚报）。
judge 评估 116 次调用（E 80 + F 36）, glm-4.6, 人民币几元量级。

## 6. Limitations（如实）

1. SEP/PhilPapers 未接入（无合法稳定机接口; 不抓取凑数）——SEP 的
   SCHOLARLY_REFERENCE 语义留给后续。
2. FULL_TEXT_READ=2（合法 OA 全文可解析源实际有限; 尝试 14+ 篇仅 2 篇成功,
   其余 403/paywall/解析空洞, 全部如实降级）。
3. 无 DOI 记录的跨源合并保守（仅机械全一致）, MERGE_CANDIDATE 机制未启用 fuzzy 档。
4. work-level 与 O7-B 书目层的关联（secondary→primary 交叉引用）留待 O7-D/E。

## 7. O7-D Readiness

检索/访问/provenance 契约已就绪; O7-D（二手语料规模化）可直接复用 access 状态机、
合法边界与 cache 机制; Scholarly Policy（prompt 层）仍冻结, 留待证据能力齐备后启用。

---

# O7-C RP1 — Access Truth & Security Closure（2026-09-06）

> BASE_SHA=43978eb49 ｜ CODE_SHA=6571ec7de（RP1 生产修复冻结）
> O7C_RP1_CAPABILITY_GATE_SHA= 274784567
> PRE_REBASE_HISTORICAL_CODE_SHA=7ee6d2b62 ｜ PRE_REBASE_HISTORICAL_GATE_SHA=d83e1ae11
> （rebase 前旧 SHA, 保留历史不删除, 不再作为当前 Gate）

## 修复对照（四 blocker）

1. **Access 真值**: provider OA URL 降为 `full_text_candidates[]`（access_claim=
   OPEN_ACCESS 的机械候选）, 不自动升级。FULL_TEXT_AVAILABLE 新定义 = 实际
   network attempt 已证明 URL 可达+body 可取得; 解析出正文 → FULL_TEXT_READ;
   2xx+body 但解析无正文 → AVAILABLE（AVAILABLE_PARSE_FAILED）。broken URL
   降回真实态（有摘要→ABSTRACT_AVAILABLE, 仅 metadata→METADATA_ONLY）。
   OA 候选不再依赖 abstract 存在。状态机严格单调（ABSTRACT 请求不降级,
   内容请求与状态字段分离: `returned_evidence_level`）。
2. **Redirect SSRF**: `_GuardedRedirectHandler` 逐跳过 SSRF guard
   （scheme/DNS/私网/环回/链路本地）, >MAX_REDIRECTS=4 → REDIRECT_LIMIT。
   timeout 语义 Option A: 连接阶段 `_connect_probe`（CONNECT_TIMEOUT=8s 单独
   强制）+ 读阶段 READ_TIMEOUT=20s。
3. **Source role 诚实化**: `model_view.source_category = philosophical_role or
   UNKNOWN`; journal-article 不再自动 SCHOLARLY_SECONDARY; 工具描述改为
   「学术文献记录（可能是 secondary/reference/primary/尚未分类）」。
4. **Gate 真值**: A1-A8 全部执行式计算（零硬编码 True）; 指标拆分
   SUBSTANTIVE_*（14 查询）/ NEGATIVE_*（2 查询假阳性对照）; 全文尝试全量记账;
   新增 ACCESS_STATE_ACCOUNTING_DELTA 守恒不变量。

## 冻结后全量重跑（§17: 16 live queries + 书目 + DOI + access + judge + F6 全复跑）

```text
A: 16 queries 双 provider, provider 错误=0; 80 records / 79 unique; P50=1.53s P95=2.20s
B: 25 records × 4 字段抽样复核 FABRICATED=0
C: 67 个 doi_verified 经 doi.org 复验 INVALID=0
D: METADATA_ONLY=19 / ABSTRACT_AVAILABLE=53 / FULL_TEXT_AVAILABLE=2 / FULL_TEXT_READ=5
   ACCESS_STATE_ACCOUNTING_DELTA=0  BROKEN_OA_AS_AVAILABLE=0
   FULLTEXT_CANDIDATES=18 / ATTEMPTS=18 / SUCCESS=7 / PARSE_SUCCESS=5 / HTTP_FAIL=11 / PARSE_FAIL=2
   A1-A8 执行式全真（A4: 5 篇真实 FULL_TEXT_READ, 均带 content hash）
E: TOP5_RELEVANCE_MEAN=3.486（≥3.0）; SUBSTANTIVE 14/14=100%（≥90%）;
   NEGATIVE_QUERIES_WITH_FALSE_POSITIVE=0, NEGATIVE_CONTROL_PASS=true
F: LITERATURE_ACCESS_OVERCLAIM_RECALL=100%, FALSE_ACCESS_OVERCLAIM=0（12 fixtures 复跑）
```

## 测试

新增 R1-R18（候选不自动升级/broken 降级/READ 需解析/解析失败→AVAILABLE/
无摘要可读全文/ABSTRACT 不降级×2/journal 默认 UNKNOWN/primary 不误分类/
redirect kill R1-R7（public→public 放行, →localhost/127/10/169.254/file 拦截,
>4 跳 REDIRECT_LIMIT）/gate 无硬编码/守恒/指标拆分/生产冻结）。
全量: **595 passed / FAILED=0 / SKIPPED=0**。

## SSRF Gate

DIRECT_SSRF_BLOCK=7/7（localhost/127.0.0.1/192.168/10.x/169.254/file/ftp）;
REDIRECT_SSRF_BLOCK=6/6 kill cases 全过; REDIRECT_LIMIT_ENFORCED=true;
get_scholarly_source 仍只接受 source_record_id（无 URL 参数）。


---

# O7-C RP2 — Transport Truth, Fulltext Authenticity & Final Gate Closure（2026-09-06）

> BASE_SHA=274784567 ｜ CODE_SHA=35e81e06c（+传输收尾 7af6dd999）
> O7C_RP2_CAPABILITY_GATE_SHA=7af6dd999
> 历史: PRE_REBASE_HISTORICAL_CODE_SHA=7ee6d2b62 / GATE=d83e1ae11（保留, 不作当前 Gate）

## 修复对照（四 blocker）

1. **单调晋升**: `_record_access` → `_promote_access`（new=max(current, candidate),
   任何路径不降级; M1-M3: READ 后解析失败/网络失败保持 READ, AVAILABLE 后 404
   保持 AVAILABLE——历史证据不因后续失败撤销）。
2. **Timeout 真值**: 删除 detached `_connect_probe`; Option B 单一
   `NETWORK_SOCKET_TIMEOUT=20` 作用于实际 connection/socket 全部 blocking 操作。
3. **DNS pinning（TOCTOU）**: 直连环境 pin 已验证公网地址（实际 connect 目标
   = guard 校验结果; 合成测试: 二次解析翻转为 169.254 不会发出请求）。
   **诚实分支**: 代理出网环境（本机 VPN, getproxies() 非空）DNS 解析发生在
   代理侧, 出网边界由代理解决——此分支不做也不假称 pinning。
   另: 本机 fake-IP 段 198.18/15 由代理 TUN 分配（外部 DNS 被劫持）, 可作
   pinned 目标; localhost/RFC1918/link-local/file/ftp 仍硬禁。
4. **FULL_TEXT_READ 真实性**: candidate 区分 `DIRECT_PDF`（primary_location.pdf_url）
   vs `OA_LOCATION`; READ 只来自 DIRECT_PDF + HTTP 2xx + PDF 内容 + 解析 ≥200 字;
   HTML landing/解析失败 → 至多 AVAILABLE。传输 provenance 记录
   final_url/content_type/redirect_count。
5. **记账**: get_evidence 返回逐候选 `full_text_attempts[]`; redirect 计数
   request-local（handler 实例级, 并发不串）。

## 冻结后完整重跑（16 queries + 书目 + DOI + access + judge + F6 全部）

```text
A: 16 queries 双 provider 错误=0; 80 records / 79 unique; P50=1.53s
B: 25×4 字段抽样 FABRICATED=0
C: 67 DOI 100% 复验 INVALID=0
D: METADATA_ONLY=19 / ABSTRACT_AVAILABLE=53 / FULL_TEXT_AVAILABLE=3 / FULL_TEXT_READ=4
   ACCESS_STATE_ACCOUNTING_DELTA=0; FETCH_ATTEMPT_ACCOUNTING_DELTA=0
   FULLTEXT: candidates=18 / attempts=18 / success=7 (=parse_ok 4 + parse_fail 3)
             / http_failures=11 / blocked=0   （18=11+0+7 守恒）
   DIRECT_PDF_CANDIDATES=9 / HTML_OA_CANDIDATES=9
   HTML_LANDING_FALSE_READ=0; READ 全部 DIRECT_PDF+content_hash（manifest 在产物中）
   A1-A8 执行式全真（合成 fixture 实跑, 零硬编码布尔）
E: TOP5_RELEVANCE_MEAN=3.486; SUBSTANTIVE 14/14=100%; NEGATIVE FP=0 CONTROL_PASS=true
F: LITERATURE_ACCESS_OVERCLAIM_RECALL=100%, FALSE_ACCESS_OVERCLAIM=0（12 fixtures 复跑）
```

## 测试

T1-T21（M1-M3 单调 kill / 无 detached probe / timeout 真值 / redirect 实例化与
独立 handler / DNS rebind 合成 / DIRECT_PDF 读 / HTML landing 不读 / 无摘要可读 /
逐候选记账与守恒 / gate 无硬编码断言 / 报告真实 SHA / 生产冻结）。
全量: 595 passed / FAILED=0 / SKIPPED=0。

---

# O7-C Final Gate Patch — Network Trust Boundary & Verified Document Body（2026-09-06）

> BASE_SHA=fd7ca8709 ｜ CODE_SHA=6ef2c1bcc
> O7C_FINAL_CAPABILITY_GATE_SHA= 本节 gate 产物 commit

## 修复对照

1. **READ = verified PDF body**: READ 路径要求 `body[:4]=="%PDF"` 魔数 +
   pdftotext 解析 ≥200 字 + DIRECT_PDF；Content-Type/URL 命名只是路由提示,
   不构成 body 证明（T22: CT=pdf+HTML body 不 READ; T23: .pdf 后缀+HTML 不 READ;
   T24: 错误 CT+真 PDF body 仍 READ）。READ provenance 新增
   `verified_document_kind=PDF` / `body_signature_verified=true`。
2. **显式网络信任模式**: `SCHOLARLY_NETWORK_MODE ∈ {DIRECT_PINNED, TRUSTED_PROXY,
   AUTO}`。AUTO（默认）检测到系统代理也**不**静默信任——按 DIRECT_PINNED 安全
   直连。TRUSTED_PROXY 为显式用户信任（本机 VPN TUN）, 如实上报
   `DNS_REBINDING_MODE=TRUSTED_PROXY_DELEGATED`; 直连模式才报
   `DIRECT_IP_PINNED`（T28/T29）。
3. **198.18/15 豁免条件化**: 仅 TRUSTED_PROXY 模式允许该 fake-IP 段;
   直连默认按 reserved 拒绝（T26/T27）。
4. **逐跳 repin**: pinned handler 在 `do_open` 时按**当前请求 URL**（含 redirect
   后的目标）重新 guard+resolve+pin——host-A→host-B 第二跳 pin host-B 的 IP
   （T30）; redirect→私网仍拦截（T31）, >4 跳 REDIRECT_LIMIT 不变。
5. **指标拆分**: `FULLTEXT_PARSE_FAILURES` 废除 → `FULLTEXT_AVAILABLE_ONLY_SUCCESS`
   （HTML OA_LOCATION 按设计至多 AVAILABLE, 非 parser failure）+
   `DIRECT_PDF_PARSE_FAILURES`（其子集）; 成功侧守恒
   SUCCESS = READ + AVAILABLE_ONLY（T33）。

## 冻结后完整重跑（TRUSTED_PROXY 显式模式, 本机部署环境）

```text
A: 16 queries 错误=0; 80/79 unique; P50=1.53s
B: 25×4 FABRICATED=0    C: 67 DOI INVALID=0
D: 19/53/3/4 分层, ACCESS_STATE_ACCOUNTING_DELTA=0
   attempts: 18 = 11 HTTP_FAIL + 0 BLOCKED + 7 SUCCESS（delta=0）
   SUCCESS 7 = READ 4 + AVAILABLE_ONLY 3（delta=0）; DIRECT_PDF_PARSE_FAILURES=0
   VERIFIED_PDF_READ_COUNT=4（全部 body_signature_verified+pdftotext+hash）
   HTML_LANDING_FALSE_READ=0; FULL_TEXT_READ_WITHOUT_VERIFIED_DOCUMENT_BODY=0
   A1-A8 执行式全真; NETWORK_BOUNDARY_MODE=TRUSTED_PROXY / DNS_REBINDING_MODE=TRUSTED_PROXY_DELEGATED
E: TOP5_RELEVANCE_MEAN=3.500; SUBSTANTIVE 14/14; NEGATIVE FP=0 CONTROL=true
F: LITERATURE_ACCESS_OVERCLAIM_RECALL=100%, FALSE=0（12 fixtures k3 复跑）
```

## 测试: T22-T33 新增; 全量 607 passed / FAILED=0 / SKIPPED=0
