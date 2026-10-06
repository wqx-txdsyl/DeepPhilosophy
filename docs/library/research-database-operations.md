# 研究数据库操作说明

## 数据位置与职责

- 数据库：`backend/data/research/library.sqlite3`，SQLite 3 + FTS5 trigram，schema version 1。
- 数据库及其备份/报告/导出在 `.gitignore` 中，不提交二进制资料或密钥。
- 正式书目仍是 `app/public/books.json` 与 `app/public/book_detail/`；章节正式源仍是 `backend/data/book_chapters/`。数据库是可重建的派生索引，不修改这些源文件或前端路径。
- 构建时保留源文件SHA-256；段落保留原章节字符范围、块索引及文本哈希。缺失或不一致的内嵌编号按阅读器实际使用的数字文件名建立索引，原值记入审计，源文件不重写。
- `sources` 保存规范书目，`provider_records` 保存去重后的各供应商快照；`access_checks` 保存每次网络验证；`evidence` 与 `evidence_checks` 保存实际片段、定位和对应验证关系。
- 历史摘要/旧访问状态不自动变成“当前可访问”。最新检查失败不会抹去此前确实取得的片段，但返回时说明是历史证据。

## 构建与验证

从仓库根目录运行，报告文件必须是新文件：

```sh
.venv/bin/python backend/tools/build_research_database.py \
  --report backend/data/research/build-new.json

.venv/bin/python backend/tools/research_database_admin.py status

.venv/bin/python backend/tools/research_database_admin.py check \
  --report backend/data/research/integrity-new.json

.venv/bin/python backend/tools/research_database_admin.py backup \
  backend/data/research/backups/library-new.sqlite3

.venv/bin/python backend/tools/research_database_admin.py export \
  backend/data/research/export-new
```

`build` 可重复执行：未变章节按哈希跳过，改动章节重建派生片段，坏输入移出当前索引并留审计；书籍源文件不变。每本书事务提交，意外中断后可重跑。`--skip-books` / `--skip-scholarly` 可单独处理一部分。

`check` 检查 SQLite 完整性、外键、全部章节源哈希与全部片段字符范围。`backup` 使用 SQLite 一致性备份，先写临时文件，成功后发布；已有目标文件不会覆盖。

`export` 输出标准 JSONL 书目、来源、访问检查和证据记录。原典正文从正式章节JSON重建，不在元数据导出中另复制一套。

## 多源发现与可达性验证

```sh
.venv/bin/python backend/tools/verify_research_sources.py \
  --query 'Confucian ethics' \
  --providers crossref openalex semantic_scholar metaso \
  --limit 5 --verify-limit 10 \
  --report backend/data/research/access-new.json

.venv/bin/python backend/tools/verify_research_sources.py \
  --query 'Stoic philosophy' --providers openalex --open-access-only \
  --limit 8 --verify-limit 8 \
  --report backend/data/research/access-oa-new.json

.venv/bin/python backend/tools/verify_research_sources.py \
  --source-id 'doi:10.1007/s13347-011-0021-z' \
  --verify-limit 1 --report backend/data/research/recheck-new.json
```

供应商配置从现有根 `.env` 加载：`OPENALEX_API_KEY`、`SEMANTIC_SCHOLAR_API_KEY`、`METASO_API_KEY`。不输出或入库密钥。Crossref 可直接查询；OpenAlex/Semantic Scholar 无密钥时使用公共配额；秘塔无密钥记 `AUTHENTICATION_REQUIRED`，不进行无效付费请求。

发现工具会保存原始书目候选，并单独记录与本次查询未通过词项匹配的候选。相关性筛选只表示可进一步审读，不等于学术审校。特别注意“free”不能让自由基、免费软件或无标度网络论文被当作“free will”研究。

可达性检查最多尝试3个来源地址，每次网络请求有45秒总期限、15MB体积上限；PDF最多解析前80页，持久化的证据总量每次最多1200字符。明确记录是片段，不声称人工读完全文。

状态含义：

| 状态 | 实际含义 |
|---|---|
| PDF_PASSAGES_VERIFIED / HTML_PASSAGES_VERIFIED | 实际取得正文、通过文献身份匹配并保存可定位片段 |
| ABSTRACT_VERIFIED | 实际网页取得摘要，不等于全文 |
| LANDING_PAGE_ONLY | 到达文献页面，未获得正文证据 |
| IDENTITY_UNVERIFIED | 取得内容，但不能确认属于目标文献；不保存为其正文证据 |
| ACCESS_DENIED / HTTP_UNAVAILABLE | 请求被拒或失败；403不能直接解释为一定要登录 |
| RATE_LIMITED | 供应商限流；不是“没有文献” |
| AUTHENTICATION_REQUIRED | 明确缺少接口凭证或收到401 |
| PERSISTED_ABSTRACT_ONLY | 只有历史摘要，本轮未验证远程可达性 |

公网地址逐跳校验、DNS固定和TLS验证沿用已有网页读取边界，合成DNS通过公共DoH取得实际公网IP。不开启环境代理，不传Cookie，不绕过登录、付费墙或访问挑战。带凭证的API请求拒绝重定向，数据库中的URL会遮盖API key等参数。

## 运行时接入

环境变量：

```text
PHI_RESEARCH_DB_ENABLED=1
PHI_RESEARCH_DB_PATH=/Users/sen/DeepPhilosophy/backend/data/research/library.sqlite3
```

- 开启后，通用 `search_books` 在源文件清单与构建快照一致时使用SQLite；索引过时或不可用时回到原JSON路径。
- `search_scholarship` 合并本地研究数据库、旧登记表和在线来源，在线新记录进入数据库；10分钟内缓存明确标记，不冒充重新联网。
- `get_scholarly_source` 可读取数据库中的已验证历史片段，附最新访问检查结果；没有缓存证据时保留原在线读取回退。
- 原典和二级文献工具均保持有界完整JSON传输，不静默截掉书目、阅读参数或片段尾部。
- Mac生产环境通过 `com.deepphilosophy.backend` 的LaunchAgent环境变量启用；其他服务配置与密钥不变。

只读接口：

```text
GET /api/research/status
GET /api/research/books/search?q=人不知而不愠
GET /api/research/sources/search?q=Confucian%20ethics
GET /api/research/sources/doi:10.1007/s13347-011-0021-z
GET /api/research/passages/{passage_id}
```

无公网写入/抓取入口。批量发现、验证、备份仍由本机CLI执行。

## 回滚与后续更新

关闭 `PHI_RESEARCH_DB_ENABLED` 并重新加载后端LaunchAgent，即回到既有检索路径；研究数据库仍保留。应用代码可按Git提交回滚，数据库备份是独立一致性快照。

修改正式书籍数据后重跑构建。需要恢复数据库时先停止使用该库的服务，保留当前文件与WAL/SHM现场，再从一致性备份恢复，检查完整性后启动。

这些记录尚不等于全库学术校订：来源身份、可达性、相关性与学术权威是不同维度；题名规则推断的导言/编者角色必须保持待审标记。
