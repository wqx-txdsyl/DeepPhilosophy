# DeepPhilosophy 哲学家资料资产补全任务书

交接对象：zcode + GLM 5.3。日期：2026-10-03。基线提交：`9fde01017afd65fd93c601319b1387d86838b2a7`。

目标：在现有作者详情页面上，持续补全剩余人物的可靠资料，按地域均衡推进，兼顾非西方思想者。完成逐项核实、资料编写、合成、验收与发布，不重新设计页面。**不能把字段齐全、来源网址存在或构建成功当作事实已核实。**

## 1. 可直接复制给执行代理的启动指令

> 请执行本仓库 `docs/tasks/philosopher-assets-completion-zcode-glm53.md`。先阅读 AGENTS.md、资料标准和交接清单，在不覆盖其他未提交工作的前提下建立工作台账，然后实际补充资料、验证并按既有流程发布。交接时有 621 位主名单人物待补全、26 条身份待核实、59 条历史文化或文本传统资料待审读，另有 31 份已有资料包须保护。按地域均衡分批，不能只做欧美名人。每个事实必须实际查阅合适来源；无法核实的内容保留不确定性，不允许凭模型记忆补齐、编造出处或降低验收门槛。先交付一批 15 位的完整成果并记录进度，再按同一标准持续推进剩余队列。每次中断前保存逐人状态、出处记录、检查结果和下一批名单，恢复时继续台账。发布必须同时核验 Cloudflare 与 OSS；没有发布条件时明确报告待发布。不要把“已经遍历全部记录”表述为“全部内容达标”。

此任务书及清单是仓库内文件。如果在另一台机器接手，需一并传递这两个文件，并取得上述基线或包含该基线的更新代码；只发送聊天摘要不足以接手。

## 2. 当前范围与完成定义

| 队列 | 数量 | 处理目标 |
|---|---:|---|
| `thinkersToComplete` | 621 | 对主名单人物逐人核实并补成可审读的带出处资料包 |
| `identitiesToResolve` | 26 | 确认身份、错译、重名、重复或证据不足，再决定分类；不能直接套模板写传记 |
| `contextToReview` | 59 | 35 条历史文化人物、24 条神话／集体／文本传统，按其性质审读 |
| `existingPacketsToPreserve` | 31 | 保留已编写资料与页面能力；发现确切错误时有据修订 |
| 合计 | 737 | 全部 canonical 记录都有明确的处置与证据状态 |

主名单共 652 位，目前 31 份资料包达到来源引用与结构标准，剩余 621 位尚未达标。现有 31 份也不意味着肖像身份、旧影响力分数和所有历史判断已完成外部学术审查。不得在报告里笼统声称“其余 700 多位已核实”。

主名单剩余缺项统计：来源标准 621、阅读路径 621、编辑审核记录 621、时间节点 593、概念 471、书目 473、相关人物 123、概述 6。这里是**低于相应标准的记录数**，并非完全空白的记录数；一个人可同时出现在多项中。

完成需要同时满足：实质资料审读、结构验证、生成数据一致、页面可用、发布核验。证据不足的人可进入带说明的阻塞清单，但仍不计入“补全完成”；若留有阻塞项，最终报告必须说明任务仍有未完成部分。确有证据需要合并或重新分类时记录前后映射，不为降低待办人数而改分类。

### 逐人清单与台账

- 交接快照：[philosopher-assets-remaining-2026-10-03.json](philosopher-assets-remaining-2026-10-03.json)。四个队列包含全部 737 条记录，提供姓名、原状态、逐项数量／缺项、详情路径、资料包路径、已有书籍 ID。
- 最新生成审计：`docs/author-assets-audit.json`。接手时与交接快照比较，识别此后已完成的工作，避免覆盖。
- 清单里的 `legacyMetadata` **尚待核实**，不能把旧国别、年代、流派和 rank 当作事实。`proposedCohort` 特意留空，须在核实语境后填写工作台账。
- 交接快照和 `docs/author-assets-baseline-2026-10-03.json` 均不覆盖。新建 `docs/tasks/philosopher-assets-progress.json` 作为可更新台账。
- 台账逐人至少保存 `name`、`queue`、`cohort`、`batch`、`status`、`evidenceLogPath`、`packetPath`、`reviewedAt`、`blocker`、`validation`、`commit`、`releaseEvidence`。状态顺序：`pending → researching → drafted → reviewed → validated → published`；受阻用 `blocked` 并填写缺什么证据，已有资料用 `preserved`。任务状态与审计质量状态分开。
- 每批落盘后记录已完成、受阻、尚未开始三类，禁止仅在对话记忆中保存进度。

## 3. 接手前必须阅读与保护的文件

本次交接文件所在的工作区是 `/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`，分支为 `codex/genealogy-atlas`；上述基线已推送到生产分支。`/Users/sen/DeepPhilosophy` 是另一个可能包含未提交工作的检出，不能因为目录名相同就假定两处代码一致。在当前机器执行时优先核实交接工作区；在其他环境执行时从包含基线的干净检出开始。此说明是交接时快照，接手仍须读取实时 Git 状态。

先执行 `git status --short`、核对分支和基线；工作区有他人改动时使用干净的独立工作区，不执行 reset、clean 或覆盖式 checkout。新分支采用 `codex/` 前缀，遵守仓库 Git LFS 配置；JSON 若还是 LFS 指针，先取得实际内容。

按顺序阅读：

1. `AGENTS.md`；`docs/author-data-standard.md`；`docs/author-assets-report-2026-10-03.md`。
2. 本任务书、交接清单、`docs/author-assets-audit.json`。
3. `scripts/sync_author_catalog.py`、`scripts/audit_author_assets.py`、`scripts/test_author_assets.py`。
4. `scripts/author-curation/roster.json`、`scripts/author-curation/corrections.json`。
5. 资料包样例：`app/public/philosopher/editorial/马丁·海德格尔.json`、`荀子.json`、`苏格拉底.json`、`玛丽·格雷厄姆（Mary Graham）.json`。样例用于理解结构，不能把其具体判断和通用措辞直接复制给其他人。
6. 渲染与书籍关联：`app/src/pages/AuthorDetailPage.jsx`、`app/src/data/authorContent.js`、`app/src/data/bookTitles.js`。

已上线且须保持的成果：谱系与流派详情设计、作者详情各模块、旧名入口、站内书籍链接、重复书名号修复、图片与代码分包的 OSS 加速。不要把这个任务扩展为 UI 改版、重新设计排名、扩建书库或批量生成肖像。

## 4. 地域与批次安排

用户明确要求“按地域均衡推进，兼顾非西方思想者”。以 15 人为一个可完整验收的小批次：古希腊与欧洲传统 5 人、东亚传统 5 人、其他世界传统 5 人。资料量大时允许拆小批，不牺牲证据质量。

其他世界传统必须轮换南亚、伊斯兰思想、非洲、拉美、原住民与大洋洲等，不可一直只覆盖其中一类。跨地域人物按本轮主要思想语境分组，并记录理由。逐批检查女性思想者和较少进入传统经典名单的思想者的覆盖；不以旧 rank 决定全部次序。

原目录的 `region` 是旧产品分组，不是准确的策展分组。例如澳大利亚原住民思想者可能标在“西方”；日本思想者可能标在“世界”。不能直接按这个字段自动平分。

每批先在台账公布确定姓名和分组，再研究写入。既有批次 `2026-10-03-balanced-01` 恰好 30 人，测试保护其 10／10／10 分布；新资料使用**新 batch ID**，不得塞入原批次。海德格尔为独立基准批次。

当某个地区的剩余队列确已处理完，按实际剩余情况重排，报告原因；不为保持比例新增无关人物，不跳过难查人物。没有联网检索／原典读取能力时先记录能力缺口，不能用模型记忆替代实地查阅。

## 5. 每位人物的实质质量要求

### 5.1 身份先行

核对姓名、原文名、常见译名、生卒年或活动年代、思想传统、与现有条目是否重复。搜索结果片段只能定位材料，不能当作已阅读原文。重名必须通过著作、年代、机构或地域等交叉确认。

旧传记中的学历、奖项、家庭、任职、旅行、政治经历均不自动可信。没有证据支持的细节应撤除或明确不确定，不为了“更生动”增加戏剧化生平。

古代人物区分历史存在、传说形象和作品署名。口述传统区分讲述者、记录者、翻译者与编订者，尊重社群自身的称谓；不得把集体知识改写成一个人的原创体系。

### 5.2 来源与证据记录

每位通常至少两个合适来源，优先哲学学术百科、大学／学术机构资料、可信原典版本、学术出版物。非西方资料可采用适合其传统的本土学术研究、可靠译本、社群机构资料；英语资料数量不等于可信度。两篇互相转抄的网页不视为独立佐证。

实际阅读支持断言的段落。记录于 `docs/author-research/<batch>/<安全文件名>.json`，至少包括：字段位置（例如 `profile.life[2].body`）、具体断言摘要、来源 ID／URL、章节或页码定位、核实结果、不确定性与查阅日期。采用自己的摘要和必要短引文，不整篇复制受版权保护文本。

来源打不开、付费正文无法访问或只见摘要时如实记录访问范围；不要伪造“已查阅”日期和支持范围。URL 返回 200、引用 ID 能解析、来自大学域名，都不能替代逐项事实核实。

### 5.3 内容与最低结构

| 模块 | 常规要求 | 质量重点 |
|---|---|---|
| 核心问题与概述 | 一个具体问题；至少 3 段概述 | 交代背景、主张与论证、影响／局限；避免“划时代巨人”等空泛赞词 |
| 时间轴 | 至少 4 个节点 | 区分生平、讲授、成书、出版、身后编订；内容须有意义，不堆生日凑数 |
| 概念 | 至少 4 项 | 定义、原词（适用时）、具体著述／篇章、误读边界；不得把整个流派通用词都算作此人原创 |
| 书目 | 通常至少 3 项 | 标明著者归属、文献性质、年代；不能把同一书的三种译名当作三本书 |
| 相关人物与关系 | 通常至少 2 位有证据的相关人物 | 对每条边交代依据，区分师承、阅读、接受、批评、历史接触和编辑比较 |
| 阅读路径 | 至少 2 条 | 提供具体著述／篇章与问题顺序；“先读原著，再读研究”不合格 |
| 争议评估 | 每人必须评估是否适用 | 学说、文本归属与政治史分别处理；没有依据时不编造政治争议 |
| 来源 | 至少 2 项 | 各结构化条目、概述、争议均有可解析且实际支持内容的出处 |

史料稀少者可用 `chronologyPolicy: limited-evidence`，当前结构最低 2 个时间／文本史节点，并以 `evidenceLimits` 说明具体缺口；不能编造精确年月补足 4 个节点。无亲笔著作采用 `worksPolicy: no-autographs`；仅有单一传本文献采用 `single-surviving-corpus`，书目最低 1 项。无法满足其余要求时保留待补状态，不滥用例外标签。

直接引语必须核对版本、译文与出处；无可核实出处的“金句”不保留为引语，可在有证据时改为无引号的概括。比较阅读明确标作编辑建议，不能据此声称历史影响。不可把年代上不可能见面的人画成师徒。

争议内容需区分已证实经历、争论中的解释和编辑评价。`included` 必须有实际正文与出处；`not-required` 说明未发现适用议题；`insufficient-evidence` 说明证据不足，不暗示有未揭露的丑闻。在世人物的敏感事实需要更严格、直接且可靠的支持。

避免重复模板开头／结尾、机械改写词条和“作为 AI”等话语。每份资料必须让读者理解此人的独特问题与论证，而非只有术语列表。不得照抄整篇百科。

### 5.4 肖像与书籍

对本批实际使用的肖像核对原始页面的署名、人物说明、年代与使用条件；不能仅凭相貌判断身份。古代想象肖像须如实描述其性质。无法确认时记录 `unverified`，不宣称整站肖像已核验。发现错误时通过 `portrait-audit.json` 等现有机制停止错配展示，保留既有文件路径。已停用的伊利格瑞斯芬克斯画作不得恢复为本人肖像。

书目与站内可读书是两回事：`existingLinkedBookIds` 仅说明原有链接，不保证著者归属或可读性。核对目录／detail／章节可用性再提供阅读入口；没有站内书时显示文献信息与来源即可，不造 ID，不把 TXT 占位书当成已可读内容。

## 6. 数据写入与结构契约

### 输入与生成结果

- 编写源：`app/public/philosopher/editorial/<安全文件名>.json`。文件名按现有逻辑 `name.replace('/', '-').replace(':', '：') + '.json'`，不私自更改 canonical key。
- 身份修订：放入资料包 `identity` 或核实后更新 `scripts/author-curation/corrections.json`；分类与别名在 `scripts/author-curation/roster.json`。只手改生成详情，下次同步会丢失。
- 前端目录正式源：`app/public/philosophers.json`。合成脚本会读写它，不能丢弃未关联资料包的原有记录。结构化资料优先由上述编辑源驱动更新。
- 合成结果：`philosopher/data/*.json`、`philosopher/catalog.json`、`schools/catalog.json`；审计生成 `philosopher/editorial-index.json` 与 `docs/author-assets-audit.json`。
- `catalog.json` 保持轻量，不塞入整篇概述和资料包。保留既有来源优先级、别名和书籍合并逻辑。

以下为字段契约。以真实样例和代码为准，不把占位文字或空数组写入正式资料包。

| 位置 | 字段 |
|---|---|
| 顶层 | `schemaVersion: 1`、`name`、`reviewedAt`、`reviewMethod`、`batch`、`regionCohort` |
| 顶层证据策略 | `chronologyPolicy`（`documented`／`limited-evidence`）、`worksPolicy`（`authored`／`no-autographs`／`single-surviving-corpus`）、`evidenceLimits`、`overviewSourceRefs`、`debateAssessment: {status, scope}` |
| 身份 | `identity` 仅列有据修正的字段；有修订时附 `identitySourceRefs`，同时在研究记录定位证据 |
| `profile` | `englishName`、`question`、`overview`、`life`、`concepts`、`bibliography`、`people`、`relations`、`readingRoutes`、`sources`；适用时包含 `debate` |
| `sources[]` | `id`、`title`、`url`（有效 HTTPS）、`type`、`accessedAt`、`coverage`；ID 在资料包内唯一 |
| `life[]` | `year`、`title`、`body`、`sourceRefs`；允许约年／年代范围／有意义的文献史时期 |
| `concepts[]` | `name`、`original`（适用时）、`definition`、`source`（具体著述／篇章）、`sourceRefs` |
| `bibliography[]` | `title`、`originalTitle`（适用时）、`year`、`kind`、`description`、`sourceRefs` |
| `people[]` | `name`、`era`、`eraSource`、`role`、`summary`、`sourceRefs`；按需加 `entityType`、`evidenceKind` |
| `relations[]` | `from`、`to`、`type`、`label`、`detail`、`sourceRefs`；必要时加 `evidenceKind` |
| `readingRoutes[]` | `title`、`description`、`sourceRefs`、`evidenceKind: editorial-reading-guide` |
| `debate` | `title`、`year`、`paragraphs`、`sourceRefs`；与顶层评估一致 |

书目 `kind` 使用已有 `authored / coauthored / edited / testimony / posthumous / attributed`；无自著者的弟子记录不能误标 authored。关系 `type` 参考现有 `teacher / influence / reading / context`，具体性质写清楚；比较与共属传统不能冒充真实影响。

相关人物优先用目录精确姓名；确有证据的站外人物也可保留并走来源入口，不为了星图凑节点新增主名单人物。`eraSource` 区分 `editorial-peer / existing-catalog / unspecified`，引用尚未审读目录的年代不能伪装为新核实结论。

**两个实现陷阱：**海德格尔样例中的 `concept.book: true` 目前会触发《存在与时间》的特定入口，不要复制到其他人物；概念可选的 `year` 需对应真实的时间节点，不把每个概念强塞一个“诞生年”。

## 7. 两条特殊队列

### 26 条身份待核实

逐人检索原文名、译名与可识别经历，并记录查证过程。结果分为：确认真实且适合主名单、确认但应为背景材料、确认重复／错译、仍无法确认。前两类提供证据后修订源数据和分类；重复条目保留旧名别名入口；无法确认者维持 `review`、不明身份提示与肖像停用，不凭空恢复传记。

“没有搜到”不等于证明此人不存在。报告具体检索线索和仍缺信息。不得为精简目录直接删除详情文件或断开旧链接。

### 59 条背景／文本传统资料

历史人物说明其历史身份与哲学史关联；神话、集体、文本传统说明性质、文本传承和解释背景，不能虚构个人生卒、个人著作与真实肖像。完成这些资料后仍可保持 `context-material`，这表示分类，不代表未工作。

现有审计面向普通哲学家，不能直接把所有背景条目改成 thinker 来取得 `source-backed`。接手后先为这两类建立独立、可测试的审核记录／验收规则：身份性质明确、来源充分、具体断言有据、文献归属清楚、关联合理、页面无误导；分别统计类别与内容审核状态。若现有资料包机制无法表达，应做最小兼容扩展并增加有意义的测试，保留普通人物的原门槛。不要把大量不完整草稿直接塞入公开 `editorial/`。

## 8. 工作步骤与现有工具的缺口

### 阶段 A：建账与准备

核对 737 条快照与当前目录差异；记录原审计、已存在资料包校验值、别名、书籍关联及错误肖像覆盖记录。创建进度台账与第一批 15 人名单。先完成下列小范围工具改进，再大规模扩充：

1. `audit_author_assets.py` 当前审计日期和索引更新日期写死为 `2026-10-03`；`sync_author_catalog.py` 的目录整理报告写死为 `2026-10-02`。区分历史批次日期与当前执行日期，支持明确的本批日期；确保同参数再生成幂等，不改写历史基线。
2. 现有测试要求正式 `editorial/` 中每份资料完整且可通过合成。研究草稿放研究记录目录，审核通过才进入公开目录。背景资料若需独立策略，先实现与验证策略，再写入。
3. 在现有检查基础上补必要的语义约束：争议评估与正文一致、关系端点存在／可解释、别名无环、书籍 ID 确实存在、无自著者不误列自著。不要编写只重复实现的无效测试，也不要宣称这些检查能自动验证史实。

### 阶段 B：逐人研究、编写、复核

每个人按“核实身份 → 阅读来源 → 证据记录 → 编写资料包 → 对照来源复核”执行。复核应重新查看原文，而非只让模型评价自己的文风。重点复查年代、原题、文本归属、因果判断、关系与敏感历史。保存复核发现和修正。

如执行环境支持并行，最多让不同工作者负责互不重叠的研究记录与独立资料包；由一个合成者串行更新聚合 JSON、运行同步、提交与发布，避免多人互相覆盖。不要并发写 `philosophers.json`、共享目录或审计文件。

### 阶段 C：合成、检查、页面验收

仓库根目录运行以下命令，`python` 应指向已安装项目依赖的 Python 3.12+ 虚拟环境；不要把其他机器的绝对路径写进代码。依赖按现有锁文件安装，不升级整个项目。

```sh
python scripts/sync_author_catalog.py
python scripts/sync_school_catalog.py
python scripts/audit_author_assets.py
python scripts/test_author_assets.py
node --test app/tests/*.test.mjs
npm --prefix app run build
python scripts/sync_school_catalog.py --check
python scripts/sync_genealogy_catalog.py --check
git diff --check
```

如同步后无意产生其他流派／谱系改动，定位原因，不能把大面积漂移当作正常输出。再次以相同输入和日期执行合成／审计，对派生文件比较哈希，验证幂等。检查旧 31 份资料没有无据丢字段、35 个既有别名入口仍可解析、站内书籍链接保持正确。

每批在桌面与移动视口至少抽查 3 位，覆盖三个地域，并覆盖本批存在的长姓名、无图、无自著、稀少史料、站外相关人物等特殊情形。涉及身份修订的条目逐个看。检查 hero、概述、时间轴展开、概念、星图、书目／阅读入口、辨析、来源及页面已有结尾内容；不能因替换数组丢失有效内容。

重复书名号已经修复：汉谟拉比应为《汉谟拉比法典》，真正标题内嵌书名可以是《〈存在与时间〉释义》。保持 `formatBookTitle` 的统一处理，不能用全局删书名号的替换破坏正文。

### 阶段 D：逐批交付

每批交付资料包、研究记录、最新审计、进度台账、验证结果及简短批次报告。报告须写清新增／修订／受阻姓名与地域分布、关键纠错、检查结果、发布状态以及剩余数量。完成一批后继续下一批；停止或上下文中断时先保存检查点，不丢失未完成任务。

## 9. 发布与性能保护

按项目现有发布权限与流程发布已验收批次。缺少凭证或 CI 阻塞时保留已验证的改动并报告“待发布”，不得声称上线，不绕过权限。只改任务书本身无需部署网站。

提交前查看差异；按实际改动精确 `git add <path...>`，禁止 `git add -A`，提交消息写入文件后 `git commit -F <message-file>`。不得提交 `.env`、本地缓存或巨大无关二进制。生产分支是 `master`，推送前 fetch 并检查远端变化，不强推，不把本地其他任务带上。

部署顺序：推送工作分支 → 等 Cloudflare 预览构建成功 → 用实际预览地址抓取 CF 构建资产并同步 OSS → 校验 → 将已验证改动按项目流程推进生产分支 → 验证生产部署的提交与页面。若合并导致构建资产哈希变化，以最终生产构建再同步并核验。Cloudflare 与 OSS 并非原子发布，JSON 结构变更需保持兼容，尽量缩短两端不一致窗口。

以下 `<实际成功的CF部署URL>` 是占位符，必须替换为本批真实部署地址：

```sh
python backend/tools/dp_grab_cf_assets.py <实际成功的CF部署URL>
python backend/tools/dp_sync_oss_static.py --only=philosophers.json,philosopher/catalog.json,philosopher/data,philosopher/editorial,philosopher/editorial-index.json,philosopher/portrait-audit.json,schools/catalog.json,app/assets
python backend/tools/dp_grab_cf_assets.py <实际成功的CF部署URL> --verify-only
```

只在确有新增／修正肖像时将对应肖像 key 加入同步范围；上述清单不自动上传新肖像。任务不改书籍章节；若另行触及章节，必须遵守 AGENTS 中独立的章节规范与 OSS 章节发布流程。

必须核验：生产 HTML 的 `dp-commit` 对应预期提交；所有本批改动 JSON 在 CF 和 OSS 两端内容与预期一致；引用的 JS、CSS、字体、图片可访问且类型正确；实际页面加载新版资料。HTTP 200 可能是 SPA 回退 HTML，不能只看状态码。保存提交号、部署 URL、核验时间、结果及页面抽查证据。

保留 `CdnImage` 的 OSS 直连、尺寸转换与一次同源兜底，作者数据并行加载与 hero 预加载，以及 Vite 懒加载 JS／CSS 的 OSS 路径。不要恢复加载原始大图，不把每人详情全部塞进首页目录，不跳过懒加载 CSS／字体上传。`dp_sync_oss_static.py` 当前存在资产目录索引依赖，修改目录数组时须查全部引用，避免顺手重排破坏部署。

历史上出现过与本任务无关的 Vercel 集成／后端 CI 失败；接手时核实实际状态，新增失败必须排查，既有失败单独说明，不得笼统写“全部 CI 通过”或直接关闭检查。

## 10. 最终交付验收

- 621 位主名单逐人有可追溯的工作结果：已完成者通过内容复核和结构检查；未完成者明确列出缺少的证据与原因，不冒充完成。
- 26 条身份问题逐条给出查证记录与分类结论，仍不明者保持清楚的未核实提示；旧链接可用。
- 59 条背景资料按性质完成审核记录，不能把神话和文本传统包装成历史哲学家的确切传记。
- 31 份原有资料包、原批次标识、页面模块、旧名入口和站内书籍关联均保留；有证据的修正附说明。
- 字段引用能解析，事实能回溯到实际阅读位置；没有模板化凑字数、伪造金句／书目／关系／经历。
- 审计、测试、构建与生成幂等性通过；抽查页面与性能无回退；改动资料已完成 CF／OSS 双端发布核验。
- 最终报告给出基线与当前总数、类别变化及理由、各地区完成数、已上线／已验证未上线／仍受阻数、关键纠错、测试与部署证据。分类不变且全部主名单完成时，可达到 652 份主名单资料；发生有据分类变化时使用真实分母并解释变化。

交付目录建议：研究记录保存在 `docs/author-research/<batch>/`，批次报告保存在 `docs/tasks/author-assets-batch-<batch>.md`，最终总报告为 `docs/author-assets-completion-report.md`。生成后的最新 `author-assets-audit.json` 与进度台账共同说明结果；不能只交一篇“已完善”的总结。
