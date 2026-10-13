# 来源门禁纠偏与剩余资料补全——执行报告

任务书：`../2026-10-12-source-gate-repair.md`；授权名单：`../2026-10-12-source-gate-repair-queues.json`。
执行者：ZCode。执行分支：`codex/zcode-author-quality-20261009`（锁定工作区）。

## 阶段A：门禁加固与精确授权（2026-10-13 提交）

### 工作区核对

- 目录/分支核对通过：`codex/zcode-author-quality-20261009`，起点 `a9f79614f`（交接快照，无新增提交）。
- 交接时工作区已有上一执行段落的未提交成果（门禁脚本、guard、测试、锁文件授权登记、标准/研究简报模板更新、W66合并包及其草稿/检查点、鲍曼与合并包的released claim）。本段对其逐项验证后继续，未重置、未清理。
- `git fetch origin master` 完成；`merge-base(HEAD, origin/master) = a9f79614f`，主线（master）已前进，合并时按任务书第8节处理。

### 门禁修复内容（`scripts/check_author_source_evidence.py`）

- `packet_is_gated()` 改为按**包身份**判定：本轮授权名单（从锁文件 `roundAuthorization` 读取）∪ 不在冻结基线的包（新建）∪ 内容摘要与 `frozenEditorialHashes` 不符的包（被修订）一律门禁；仅字节级未变的基线包豁免并显式记为「历史基线兼容」。锁文件缺失/不可解析 → `SystemExit` 硬错误，不自动全免。
- 来源必填字段 `id/title/url/type/accessedAt/accessScope` 逐条校验，缺失报 `missing-required-field:<field>`。
- `abstract-or-catalog` 只支撑书目题名/版本/年代：出现在 life/concepts/people/relations/readingRoutes/overview/debate 的 `sourceRefs` 报 `abstract-catalog-supports-bibliography-only:<id>`。
- `confirmed/corrected/inferred` 的证据 checks 引用不可读来源报 `verdict-source-not-readable:<id>`。
- 命令入口（逐人与全量）、`audit_author_assets.assess()`（编译状态）、测试套件使用同一 `evaluate()`；`main()` 输出 `historicalCompatibilityExempt` 计数，历史兼容不再是静默豁免。

### 权限登记（`worktree-lock.json` + `scripts/guard_author_quality_worktree.py`）

- 锁文件新增 `roundAuthorization`：73 人修复名单（72漏检包+胡汉民）、`contextApplicationNames=[汉谟拉比]`、任务书路径、名单SHA256；原有 `repairExistingPackets` 11 人原样保留；`workspace/branch/baseCommit/baseline/frozenEditorialHashes` 未动。
- guard 新增 `round_authorization()`：读取锁文件授权表并与授权队列文件核对（名单集合、两个SHA256、任务书路径、原11人名单），任何不一致即 fail——锁表只能收窄不能扩权。
- guard 的 editorial 检查改用 `catalog_key_for_stem()` 解码文件名编码（`/`→`-`），修复了交接时 `GUARD FAILED: 正式资料包不是目录人物：让-弗朗索瓦何维勒-马修理查德.json` 的误报根因（文件名编码 vs 目录键），未放宽任意姓名校验。
- 修复白名单合并登记名单与原11人；冻结哈希保护仅对白名单内人物开放，其余已发布包维持原保护。

### 回归（任务书第3节负例清单 → `scripts/test_author_assets.py`）

| 负例 | 结果 |
|---|---|
| 阅读字段全缺的新包 | ✅ `missing-required-field:accessScope` |
| 基线包修订后继承豁免 | ✅ 修订即门禁（摘要不符） |
| 本轮名单中的包即使与冻结摘要一致 | ✅ 名单优先门禁 |
| 锁文件缺基线 | ✅ 硬错误/空冻结表→新包必门禁 |
| 未变基线单列兼容 | ✅ `historicalCompatibilityExempt` 显式计数 |
| search-summary/维基支撑正文 | ✅（原有负例保留并通过） |
| 书目层只支撑编目事实 | ✅ `abstract-catalog-supports-bibliography-only` |
| confirmed 引用未读来源 | ✅ `verdict-source-not-readable` |
| 编译状态一致性 | ✅ 编译测试改为「level 与 gaps/errors 一致；needs-review 必须给出可定位错误」 |

### 新规则全量诊断与真实状态重编译（2026-10-13）

- 门禁：gated 159 / 历史兼容 428 / **失败 94**。
- `sync_author_catalog.py --date 2026-10-13` + `audit_author_assets.py --date 2026-10-13` 重编译：索引 **source-backed 493 / needs-review 94**（652 thinkers）。586→493 的下降是门禁修复后的真实口径，非内容回滚；正文与路由全部保留可用。
- 94 = 授权73 + 原11人中仍缺阅读元数据的6（佩吉·坎芙、卡罗琳·汉弗莱、马库伊尔肖奇特尔、比尔·尼布利特、黑麋鹿、科林·豪森）+ 无本轮授权但被更严规则新揪出的15（伏尔泰、布莱兹·帕斯卡尔、布鲁诺·德·菲内蒂、歌德、托马斯·内格尔、托马斯·马尔萨斯、威廉·巴特勒·叶芝、弗里德里希·施莱尔马赫、彼得·厄巴哈、赫伯特·马尔库塞、加塔里、杨献珍、爱尔维修、汉斯·约纳斯、詹姆斯·科恩）。
- **无授权的15份按任务书如实保持待审，未擅改**；建议下轮授权按同一补证据方式处理。
- `audit_author_assets.py` 在存在待审包时按设计 exit=1 响铃；全部授权包修复后应回到0。

### W66 合并人物包（让-弗朗索瓦何维勒/马修理查德）的保全与隔离

- 该包为上一段落未提交成果，实体裁决（两人/对话组/集合记录）未完成，且22项门禁错误（全部正文引用建立在普通维基线索上）。按任务书第5节：**不提交其 source-backed 状态**。
- 处置：正式包文件移至研究区 `docs/author-research/author-quality-2026-10-09/2026-10-11-batch-w66/drafts/让-弗朗索瓦何维勒-马修理查德.editorial-packet.json`（连同草稿/检查点/编译快照四份副本完整保留）；公共路径 `philosopher/data/让-弗朗索瓦何维勒-马修理查德.json` 回退到 HEAD 遗留条目（正文与路由保持可用）；目录键不动。编译测试中「马修·理查德 关系端点不可解析」随包移出而消除；实体裁决进入待办（见阶段D）。

### 交接时遗留缺陷（不在本轮授权内，如实记录）

1. `安提斯泰尼` 包（W9批次，本任务产物）：`worksPolicy=no-autographs` 但书目两条佚失演说辞标 `kind=authored`——`test_no_autographs_are_not_invented_to_fill_the_bibliography` 在 HEAD 即失败。修复需将其加入修复授权，本轮不得擅动；**待办：下一轮授权单列**。
2. 胡汉民 `invalid-source-metadata`（jds-hu http URL）在授权名单内，阶段C处理。

### 检查快照

- `test_author_assets.py`：30 测试，唯一失败=上述预存安提斯泰尼项。
- `check_author_source_evidence.py`：gated 159 / exempt 428 / failures 94（=索引 needs-review，两口径一致）。
- `guard_author_quality_worktree.py --check`：`ok: true`。

## 阶段B：两个贯穿样本（2026-10-13 完成）

### 样本1：齐格蒙特·鲍曼（提交 93b1d5c67）

- **实读来源**：Guardian讣闻全文 + Britannica传记全文（均2026-10-13）；Bauman Institute纪念文保留2026-10-11原读事实。
- **真实元数据补正**：纪念文=full-text（初读+复核）；search-bauman=search-summary（检索摘要层，正文引用清零，20处正文引用改由实读来源承接）。
- **实读纠错**：原包「妻子安娜·鲍曼(1932—2009)」系女儿名与生年错置——讣闻明确结发妻子为雅尼娜（Janina，1948结婚，《冬晨》1986塑造大屠杀一书，2009去世），2015再婚亚历山德拉（社会学家）；people/relations 已按讣闻改正。
- **有据缩减**：LSE深造（《卫报》《不列颠》均无载）、《立法者与阐释者》(1987)（两份全文来源无载）、争议段史学批评谱系句——均记入证据 uncertainties。
- **替换补强**：书目以《现代性与含混》(1991)替换无据的1987年书；概念以「消费者社会与个体化」「权力与政治的分离」替换无据的「无关地方的地方」（引文与定位均出自实读来源）。
- **链路**：门禁 --name 0失败 → sync+audit（494/158）→ 提交 → 推送 branch+master（fast-forward a9f79614f→93b1d5c67）→ OSS 增量上传 → OSS==提交字节一致、索引三端集合一致（/tmp/dp-gate-repair-20261013/verify_publish.py ALL PASS）。

### 样本2：弗里德里克·格鲁（提交 6b8c63f97）

- **实读来源**：Sciences Po CEVIPOF官方人员页 + English PEN书页 + 卫报2014-04-20专访（均2026-10-13全文）+ Persée 2002书评（保留2026-10-11全文读事实并复核）；新增 Persée 权威著录页（abstract-or-catalog，仅书目题名/年份）。
- **维基正文引用清零**：wiki-en 30余处正文引用全部替换为实读来源或缩减；9个检索摘要层来源正文引用清零（保留于sources作发现线索记录，字段齐全）。
- **实读纠错**：《暴力状态》2006→2005（Persée权威著录）；《行走》初版「2008/2009分歧」收束为2009（Carnets Nord，2011起Flammarion再版）。
- **有据缩减**：出生日期/生地、导师（师承不得由目录支撑）、布尔丁奖、七星文库「并非全集」、1996/97出版事件年份（正文不引、书目层保留）——全部记入 uncertainties。
- **门禁精化（对齐标准既有规则）**：confirmed/corrected/inferred 在书目字段（profile.bibliography）上可引用 abstract-or-catalog 支撑题名/版本/年份；负例回归新增（书目字段放行、生平字段仍拒绝）。**布鲁诺·德·菲内蒂**（无授权名单）因此合法复归 source-backed——其唯一错误即书目字段引用 IA 著录被过严实现误拒，包内容未改动一字。
- **链路**：门禁 --name 0失败 → sync+audit（496/156）→ 提交 6b8c63f97 → 推送 branch+master → OSS 增量（5传/1359跳过）→ verify ALL PASS → 双样本 claim 释放。

### 样本阶段说明

- 样本期间未发布新增资料包（仅纠偏），符合任务书暂停要求。
- OSS 同步脚本与验证脚本存于仓库外 /tmp/dp-gate-repair-20261013/（guard 将 backend/tools/_tmp/ 列为越界路径，随用随删）；发布回执 oss-sync-receipt.json 同目录。
- philosophers.json 为 LFS：上传前以工作树内容 sha256 对照已提交指针校验通过。

## 阶段C：73份授权名单逐项纠偏（进行中）

- 已完成（3）：齐格蒙特·鲍曼、弗里德里克·格鲁 + 布鲁诺·德·菲内蒂（门禁精化复归，非名单成员但属实现误拒纠正）。
- 剩余（70）：按「已有阅读证据→补正元数据；无阅读证据→实读或缩减；维基正文引用→实际替换」分批处理。
- 胡汉民（invalid-source-metadata）与10人维基问题在此阶段处理。

## 阶段C：73份纠偏的执行进度（截至 2026-10-13）

### 已完成（40包复归 source-backed，539/48）

| 批次 | 提交 | 内容 |
|---|---|---|
| 样本1-2 | 93b1d5c67 / 6b8c63f97 | 鲍曼（实读纠错）、格鲁（维基引用清零+实读替换）；德·菲内蒂因门禁精化复归 |
| 批次1 | 287be809d | 77份授权包 accessScope 按既载阅读事实补正（full/partial/catalog/search/unread 五级分类规则见上）；冗余线索引用清理413处；26包复归 |
| 批次2 | ae7f2d2c4 | 17包逐项处置：4个误判著录层的实读页升级（hpr/sup-book/oll-ferguson/cp-douban）；勒庞证据补登；checks 重指向（黑麋鹿立熊、波西格On Quality、弗洛姆生年/卒年）；无实读 checks 降级 uncertain（桑德尔/弗洛姆/梯利/埃文斯/尼布利特/史崔勒基）；诚实缩减并记 uncertainties（海特生年、巴什拉“巴特并称”、保罗中译条、拉库《纳粹神话》、哈里斯概念与生年） |

**诚实性说明**：accessScope 补正只转录研究记录既载阅读事实（readScope/coverage 文本），每包带 `sourceGateRepair` 标记；未新增阅读事实、未改断言与日期。降级/缩减一律写入证据记录 uncertainties 并注明可恢复条件。

### 剩余待办（33份授权名单 + 14份无授权）

- **9人维基正文引用**（格鲁已完成）：格雷林、沃伯顿、麦高恩、达马西奥、沃尔什、卡根、德波顿、朗西埃、萨林斯——需按格鲁模式以实读来源替换或缩减保持待审。
- **结构性问题包**：书目元数据源（citation-database/书目快照）支撑生平/概念条（芒福德、热奈特、卡迈克尔、麦克弗森、明斯基、德雷福斯、萨弗兰斯基、普莱希特、艾德勒、德威特、帕尔默、德波顿等）——需每包补1-2个实读来源（obituary/官方传记/书评）后重指向，或缩减。
- **胡汉民（外部阻断）**：jds.cssn.cn 已失效（http 403、https 无响应；web.archive.org、taiwan.cn、出版社页当日均不可达）。jds-hu 保留真实阅读元数据（2026-10-11 实读事实）并记录失效；其事实已由 krzzjn-hu+chinanews-hu 覆盖；包保持 needs-review，待可靠 HTTPS 替代源。
- **14份无授权包**（伏尔泰、加塔里、叶芝、帕斯卡尔、施莱尔马赫、厄巴哈、内格尔、马尔萨斯、杨献珍、歌德、约纳斯、爱尔维修、科恩、马尔库塞）：按任务书不擅改，建议下轮授权按同法处理。

### 阶段D：合并人物与身份、背景

- **合并人物包**（让-弗朗索瓦何维勒/马修理查德）：已隔离保全于研究区（editorial-packet.json + 编译快照 + 裁决记录 entity-disposition.json），公共路径回退遗留条目、正文可用；三方案（两人分立/对话作者组/合并键重写）待下轮按分类标准选定，本轮不应用无据分类变更。
- **汉谟拉比（背景应用）**：W41 审读结论已按本轮授权经 corrections.json 管线应用——era 改在位年、师承改父子继承、删“第一部成文法典/奠基人/王在法下雏形/罗马法东方参照”、法典年代改在位末期、权杖改环与杖、奴隶制帝国中性化、摩西律法改类型学比较、补石碑破损与学界争论句；pulḫu/šarrūtu 两目维持待核。已审读=1、已应用=1，其余58项背景继续独立审读。
- **身份队列**：原26项完成1（狄奥尼修斯）；埃德温·杰恩斯（zcode-w62 active）等维持不动；本轮未新增裁决。

### 检查与发布状态

- `sync_author_catalog` + `audit_author_assets`（2026-10-13）：**source-backed 539 / needs-review 113（含65条无包历史待审）**；test_author_assets 30+2项测试，唯一失败为预存安提斯泰尼（不在授权，见阶段A遗留缺陷1）；guard --check ok。
- 推送与 OSS：见提交记录；philosophers.json LFS 校验通过；OSS 增量上传并以字节一致+索引两端集合一致验收。

## 停止点（下一会话入口）

1. 继续第4节剩余33份授权纠偏（顺序建议：先9人维基，再结构性问题包）。
2. 每批5-8人，沿用本报告的处置模式（实读替换/重指向/降级uncertain/诚实缩减+uncertainties）。
3. 胡汉民替代源、合并人物实体裁决、身份25项、背景58项、肖像阶段按任务书继续。
4. 预存缺陷：安提斯泰尼 worksPolicy 修复需列入下轮授权（修复建议见 2026-10-11-release-reconciliation.md）。
