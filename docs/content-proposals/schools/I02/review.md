# I02 胜论派（Vaiśeṣika）—— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I02`（proposedKind=school，P1-content-packet，cohort=南亚，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。

## 一、边界决定

1. **范围锁定：范畴与本体论**。按任务 scopeAndCautions，本包只展开胜论的句义（padārtha）范畴体系（六句义及后加的第七"无"）、九实—廿四德—五业的清单结构、普遍/特殊/内属的三个关系性范畴、极微原子论与运动—动因理论（gurutva/vega/adṛṣṭa）、与正理的历史关系及佛教批判节点。正理的量论（四量、认证、五支论式、遍充、似因）**一律不移植**，属姊妹包 I01；胜论知识来源问题只写一处有据差异（不承认圣言为独立量，S4 逐字），且以否定式措辞（来源未给"二量清单"原句，不作正面清单断言）。
2. **原子论不写成近代科学先声**。这是本包刻意处理的规范点：极微论证按 S1 原样呈现（三微—二微下行情梯、"须弥山与芥子"反无限分割、以及 Ganeri 本人 "The argument seems to be question-begging" 的评语）；运动理论严格转述 S1 措辞（"took a rational and scientific interest" 为 S1 原文；"bears comparison with Philoponus' impetus theory" 标明为学术比较、非影响关系）；evidenceLimits 第13条明示"近代科学先声"一类拔高无来源支持。
3. **学说与宗教实践之分**。《胜论经》确以 dharma 开篇、以 abhyudaya/niḥśreyasa 为目标，解脱被定义为和合不再现起（S2 逐字），《摄句义法论》有 Īśvara 创世论（S3 逐字）——本包如实呈现这一框架，不回避也不拔高；Īśvara 论证（TSD 17b，S1 逐字）写为哲学论证，subSchools 第4条与 cihai 均按"主题"处理。
4. **古代人物与经典年代用证据范围**。《胜论经》系年只写 S1 一处（约公元前100年）并注明"唯一系年"；迦那陀生卒无考；Praśastapāda 用 S1 的"6世纪"；Śrīdhara 不系年；Gaṅgeśa 在本包不系年（"约1325年"仅以转引 I01 的方式出现，不重复计入本包来源）。

## 二、查重结论

- **学派条目**：任务 JSON 的 exactTopLevelEntries / exactBranches 均为空；另以 python3 复查 `app/public/schools/catalog.json`（不含"胜论/Vaiśeṣika/Vaisheshika"）与 `app/public/schools/data/` 目录（无同名文件）。mentions-only 成立：仅 `school_印度哲学.json` 一处来源，"胜论"8处（概述、relations"世亲→胜论派"条、时间线"公元前300"条、quotes"万物皆由原子构成"引语卡、cihai"胜论"词条），"迦那陀"1处，"Vaisheshika"1处。
- **人物**：`app/public/philosophers.json`（737人）python3 检索：**无** 迦那陀／迦那多／优楼佉／Kaṇāda／Praśastapāda／Śrīdhara／法称 等条目；简介全文亦无"胜论/Vaiśeṣika/Kaṇāda"字样——本包全部人物为**站外人物**（契约允许，此处声明）。
- **书籍**：`app/public/books.json`（409种）python3 检索"胜论/极微/句义/吠陀/数论"均0处；"正理"2处为胡塞尔/德里达书名的子串误命中（I01 已同记录）。故 `relatedBookIds` 为**空数组**，readingRoutes 全部指向站外来源（两部 GRETIL 梵文原典 + SEP 两个条目），无 TXT 占位书可关联。
- **旧正文处理**：站内《印度哲学》的时间线"公元前300 正理派和胜论派兴起（…迦那陀著《胜论经》…）"与引语卡"万物皆由原子构成（《胜论经》）……早于古希腊原子论"**未继承为本包依据**（见"分歧"）。

## 三、与 I01 正理派包的分工与查重（重点）

I01/I02 为姊妹任务，分工执行情况如下：

| 重叠点 | I01（正理派） | I02（本包） | 处置 |
|---|---|---|---|
| 合流事件（11—12世纪） | 时间线节点+概述 | 时间线节点+概述 | 两包措辞一致（同出 S1 逐字句），各自服务其主线，互指不重复展开 |
| Gaṅgeśa | 思想家卡（量论侧：四量、tātparya、tarka 反怀疑论） | 思想家卡（本体论侧：胜论形而上学载体、Diṅnāga 式文本结构、无之感知的新定义） | 内容不重叠；本包不系年，不重复计入 I01 的 IEP 线索 |
| Annambhaṭṭa《推理撮要》 | works 卡（新正理手册史、盖梯尔式反例） | works 卡+思想家卡（胜论范畴呈现：TS 10–14、82、83） | 分工已在双方 desc 注明 |
| 法称 | 思想家卡（推理三分类） | 思想家卡（anupalabdhi 批判、刹那论对照） | 各引其来源段落，无重复内容 |
| Udayana | 思想家卡（设计论） | 不设卡，仅时间线节点（"胜论—正理两边的大家"，S4 系年+ S1 "great Nyāya-Vaiśeṣika author"） | 避免双包重复立卡 |
| Tarkasaṃgraha 的"初学者指南"绰号 | 未用（I01 用了"初学者的 Gadādhara 指南"于手册条目） | 本包不用绰号作正文素材，仅在 relations/4 引 S1 原文 | 原文引用注明出处 |

两包对《胜论经》系年、合流年代等共享事实的表述一致，未出现互相矛盾的建议。

## 四、分歧与争议的处理

- **《胜论经》系年**：本包核读来源中仅 S1 一处系年（"c. 100 B.C.E."），照实写"约公元前100年（S1 唯一系年）"；站内"公元前300"未获支持，提交复核建议（evidenceLimits 第10条）。比照 I01（两来源约100年/约200年分歧），本包《胜论经》与《正理经》的相对年代关系（胜论早于正理约两百年）仅由两包各自来源并置可得，正文不作断言。
- **S1 的 anitya 疑误**：S1 极微定义句 "An atom (paramāṇu) is indestructible (anitya)" 中括注与原典相抵——S3 明言 "paramāṇulakṣaṇā nityā"（以极微为相者恒常）。本包正文从原典（极微恒常），引 S1 处保留原文并在 evidence（overview 第9条）注明疑误。
- **胜论得名义**：S1 为"some claim"一说，副标题与正文保持"或谓/一说"。
- **站内"世亲→胜论派：批判"关系**：世亲与胜论的直接论辩文献（如《二十论》相关段落）不在本包核读来源内，未写入本包 relations；在 evidenceLimits 第9条与 proposal.relationSuggestions 提交 Codex 另行复核。
- **站内引语卡"万物皆由原子构成"**：与原典结构不符（仅地水火风为极微所成）；其 exp 中"早于古希腊原子论"与 S1 系年不相容且无来源。本包引语另选原典定位明确的句子，不继承该卡。

## 五、译名政策

- 仅采用站内已用的"迦那陀"（《印度哲学》时间线写法），附梵文 Kaṇāda。
- "普拉沙斯塔帕达（Praśastapāda）"为常见音译，采用并随附梵文；Śrīdhara、Annambhaṭṭa、Gaṅgeśa Upādhyāya 主名用梵文拉丁转写（同 I01 政策；Gaṅgeśa 沿用 I01 已用写法）。
- 《摄句义法论》为学界通行汉译题名，沿用并附梵文 Padārthadharmasaṃgraha；文本自称 Praśastapādabhāṣya 已并列。Nyāyakandalī 的"正理甘露"为编辑意译，已注明性质。
- quote/quotes/closingQuote 中文均非通行汉译：两条自 GRETIL 梵文直译、一条自 S1 英译回译，kind 与署名均注明转译性质。

## 六、复核方法与结果

1. 四来源于 2026-10-04 实际抓取并读到相关段落：S1、S4 以 curl 抓取全文缓存后去标签逐字比对（WebSearch 因服务端限流不可用，未作依据；限流发生时改用直接抓取）；S2、S3 为 GRETIL 明文转换文件，逐字核读。比对规范化约定（已在 packet.json reviewMethod 与 evidenceLimits 第14条披露）：SEP 弯引号（单/双）统一转写为直双引号、标签边界空格（含引号与破折号内侧）规整、GRETIL 词界点'.'规整为空格；{5...} 校勘记夹注、avagraha（'）与 `iha' 标记字符照录。写成后另以脚本对全部 locator 片段做原文回查，修正了三处转录偏差（navaiveti 被截为 navaiva、(6 th century C.E.) 的空格 ×3、两处 GRETIL 标记字符）与 4 处转义伪影。evidence 记录的 verbatim 引文共核：S1 约 26 处、S2 约 16 处、S3 约 14 处、S4 约 6 处。
2. 备选来源的排除过程（如实记录）：IEP 无独立胜论条目（以其站内 REST API `wp-json/wp/v2/posts?search=vaisesika` 检索确认，仅 Substance/Properties/Hindu Philosophy/Nyaya 等条目提及）；Britannica 'Vaisheshika' 条目 curl 与 WebFetch 均返回 HTTP 403；GRETIL 的 alt 版《胜论经》文件头自注 'THE TEXT IS NOT PROOF-READ!'，未采用。以上均入 evidenceLimits 第12条与 works/0 note。
3. evidence.json 共 62 条记录，JSON Pointer 对位 packet.json：overview 14、conclusion 5、quote/closingQuote 2、quotes 2、thinkers 6、relations 5、timeline 8、cihai 10、works 4、subSchools 4、relatedBookIds 1、coverageGap 1。
4. 数量：人物 6（含 1 位对手方法称；另 Udayana 以时间线节点收录）、时间线 8、术语 10、著述 4、分支 4、关系 5、阅读路线 2——在契约参考区间内（分支 4 项中两项标 `kind: 主题`/`文献传统`，非组织分支，本派无组织性分裂的证据，不虚构分支）。
5. 边界自检：仅写入 `docs/content-proposals/schools/I02/`；未动 app/、backend/、现有 schools 数据、进度台账；未运行任何 git 写命令。

## 七、仍缺证据（与 packet.json evidenceLimits 对应）

- 《胜论经》编成的文献学分层（多阶段编成的具体阶段）与更宽系年范围（如带文献学导论的原典校勘本所定范围）。
- 廿四德后七德的可靠名目清单（GRETIL 明文该处疑有讹形；需对照校勘本）。
- Śrīdhara 年代与《Nyāyakandalī》成书年代。
- 世亲与胜论直接论辩的文献证据（站内旧 relations 的复核依据）。
- '无'范畴的确立者与确立年代（S1 只说"后期学派的独特增补"，未指认文本节点）。
- Gaṅgeśa 生卒的直接系年（本包不重复 I01 的 IEP 线索）。
- 无阻塞：四来源全部可核读，本项可进入 Codex 审读。

## 八、实际核读 URL 清单（2026-10-04）

已核读并采为 sources：

1. https://plato.stanford.edu/entries/early-modern-india/ （S1；curl 全文缓存，DC.creator=Ganeri, Jonardon；2009-03-10 初版，2023-11-05 实质修订；逐字引文约 26 处）
2. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_kaNAda-vaizeSikasUtra.txt （S2；curl 全文，Nozawa Masanobu 录入，2020-07-31 版；逐字引文约 16 处；alt 版另抓取后排除）
3. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_prazastapAda-pAdArthadharmasaMgraha.txt （S3；curl 全文，Tokunaga & Muroya 录入，2020-07-31 版；据 Dvivedin 1895 编本；逐字引文约 14 处）
4. https://plato.stanford.edu/entries/epistemology-india/ （S4；curl 全文缓存，DC.creator=Phillips, Stephen；2024-03-13 修订；逐字引文约 6 处）

尝试后未采用（有据排除）：

- https://iep.utm.edu/vaisesika/ 及 IEP 站内检索（REST API）——无独立胜论条目
- https://www.britannica.com/topic/Vaisheshika —— HTTP 403（curl 与 WebFetch 皆然）
- https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_kaNAda-vaizeSikasUtra-alt.txt —— 文件头自注 NOT PROOF-READ，排除

站内核对（python3，非网络来源）：

- `app/public/philosophers.json`（737人，查重：无本包人物）
- `app/public/books.json`（409种，查重：无胜论相关藏书）
- `app/public/schools/data/school_印度哲学.json`（mentions-only 复核："胜论"8处定位，"迦那陀"1处）
- `app/public/schools/catalog.json` 与 `app/public/schools/data/` 目录（无同名条目）
- `docs/tasks/school-content-gap-tasks-2026-10-04.json`（I02 条目）

## 九、第二轮：同日草稿处置与合并记录（2026-10-04 下午）

> 本节由第二轮研究员追加。上文一至八节为第一轮草稿原貌（其中"唯一系年""仅 S1 一处系年"等表述已被本轮合并修正，见 9.3/9.4；第六节的"62 条记录"为第一轮数字，合并后为 71 条）。

### 9.1 时间线与发现

- 09:56 第一轮研究员开工，`ls` 检查输出目录 I02/ 为**空**，无既有草稿。
- 10:01—10:15 期间，目录出现另一研究员写入的**同日全量草稿**四个文件（packet.json 10:01 / artwork-brief.md 10:09 / review.md 10:10 / evidence.json 10:15；review.md 于 10:26 有最后一次润色），来源架构为 SEP×2 + GRETIL 梵文原典×2。
- 第二轮研究员按任务纪律**不盲信草稿**，先读其全部四个文件，再对其 4 个来源**逐源重开核实**，最后决定处置并于 10:27—10:28 完成合并写入。

### 9.2 草稿来源逐源复核结果（4/4 通过）

1. **S1** `plato.stanford.edu/entries/early-modern-india/`（Ganeri）：WebFetch 逐句核验 10 项主张，9 项逐字命中；唯"学派得名于 viśeṣa 一说（'some claim'）"一句摘要器称未见于页面——改用 curl 抓原始 HTML 后 grep，**该句逐字命中**（"…from which, some claim, they derive their name."），系摘要器漏检而非草稿误引。
2. **S2** GRETIL《胜论经》明文：文件头（Nozawa Masanobu 录入、2020-07-31 版、GRETIL/SUB Göttingen）与关键经文逐字命中：开篇 `athāto dharmaṃ vyākhyāsyāmaḥ`、`yato 'bhyudayaniḥśreyasasiddhiḥ sa dharmaḥ`、九实经、十七德经、五业经、`sad akāraṇavat tan nityam`、`adravyavattvāt paramāṇāv anupalabdhiḥ`、`saṃyogābhāve gurutvāt patanam`、`maṇigamanaṃ sūcyabhisarpaṇam ity adṛṣṭakāritāni`、`agner ūrdhvajvalanaṃ…adṛṣṭakāritāni`、解脱经、u/v/bhv/c 异读体例——全部与草稿引文一致。
3. **S3** GRETIL《摄句义法论》明文：文件头（Tokunaga & Muroya、2020-07-31、据 Dvivedin 1895 Benares 编本、题注 commentary on Kaṇāda's Vaiśeṣikasūtra、附 Śrīdhara《Nyāyakandalī》）与关键句逐字命中：首词 `praśastapādabhāṣyam`、归敬偈 `praṇamya hetuṃ īśvaraṃ munim kaṇādam anvataḥ`、六句义总纲、`kaṇṭhoktāḥ saptadaśa`＋加七＝`caturviṃśatir guṇāḥ`、`paramāṇulakṣaṇā nityā / kāryalakṣaṇā tv anityā`、`dharmaḥ puruṣaguṇaḥ…mokṣahetuḥ`。
4. **S4** `plato.stanford.edu/entries/epistemology-india/`（Phillips）：与第二轮独立核读为同一页面，草稿对其的引述（胜论不立圣言为独立量、法称7世纪初、Udayana 11世纪）与独立核读结果一致。

### 9.3 处置决定：保留草稿为主干，合并第二轮来源（非重写）

草稿以梵文原典为锚、引用纪律严格、evidence 覆盖完整，质量高于第二轮研究员的独立初稿，故**保留为主干**；第二轮独立核读到的 5 个来源合并为 S5—S9，用于：

- **把任务要求的"证据范围定年"落到实处**：草稿《胜论经》仅 S1 一处系年（约前100年），现并陈 S6（IEP 约1世纪，逐字）与 S5（Britannica 2—3世纪且条目自带存疑问号，转述），proposal.period、timeline/0、thinkers/0、works/0、subSchools/0、conclusion 第二段、evidenceLimits 第1条同步改为范围"约公元前1世纪—公元3世纪"；普拉沙斯塔帕达并陈 S1（6世纪，逐字）与 S9（约4世纪末），改范围"约公元4—6世纪"（timeline/1、thinkers/1、works/1、subSchools/1、evidenceLimits 第6条）。
- **补正 evidenceLimits 第12条**：草稿因 WebFetch/curl 均获 Britannica 403 而未核读该条目；第二轮经 web_reader 抓到正文并核读，采为 S5（其引文均标"转述"）。
- **补入 IEP 两条目（S6/S7）**：草稿确认"IEP 无独立胜论条目"属实，但未使用其《Hindu Philosophy》《Nyāya》条目中的实质胜论内容（第二轮 curl 抓原文逐字核验）；据此新增 thinkers/6（Śaṅkara Miśra，约15世纪，《光释》）、relations/5、works/4（辛哈译本）与 works/5（Halbfass 1992，S7 书目逐字）。
- **补入可读英译原典（S8）**：Sinha 1923 逐经页七则经文逐页核对（1.1.1、1.1.2、1.1.4、4.1.1、4.1.2、4.1.3、4.1.6），并入 works 与阅读路线 1，服务无梵文基础的读者。
- **timeline/3（Udayana）年代改范围**：并陈 S7（c. 975，逐字）与 S4（11世纪）；timeline/4（合流）补 S5 的"11世纪完成"（与之相容，并记）。

### 9.4 草稿结论的修正与保留

- 保留：Dharmakīrti→Gaṅgeśa 学派层面论题线、S1 anitya 疑误标注、站内旧数据复核建议（"公元前300"系年、"万物皆由原子构成"引语卡、"世亲→胜论派"关系）、"胜论得名于 viśeṣa 一说"的 hedge 措辞（该句已经原始 HTML grep 复核确在）、多传本不孤证依赖经号、归纳法偏移披露——第二轮复核均予确认。
- 修正：所有"唯一系年"表述（thinkers/0、works/0、timeline/0、evidenceLimits 第1条、第一节第4条所涉正文）随多源并陈改写；evidenceLimits 第12条（Britannica 403 未核读）被新表述取代；Śrīdhara 条目补 Britannica 注家名单佐证（仍无系年）；新增 evidenceLimits 第15—17条（希腊原子论比较边界、辛哈译本译名差异与核读记录、同日草稿处置声明）。

### 9.5 第二轮实际核读 URL 清单（2026-10-04）

采为来源：

1. https://www.britannica.com/topic/Vaisheshika （S5；WebFetch/curl 403 → web_reader 抓取正文核读，转述定位）
2. https://iep.utm.edu/hindu-ph/ （S6；curl 抓原文逐字核验：'Kaṇāḍa (1st cent. C.E.)'、'Śaṅkara-Misra, 15th cent. C.E.'、'Nivṛitti…tattva–jñana'、VS I.1.4/VII.1.8 引注等）
3. https://iep.utm.edu/nyaya/ （S7；curl 抓原文逐字核验：'largely adapted…from its sister school Vaiśeṣika'、'Udayana, c. 975'、'Gaṅgeśa Upādhyāya (c. 1325)'、Halbfass 1992 书目等）
4. https://www.wisdomlib.org/hinduism/book/vaisheshika-sutra-commentary 及逐经页 doc427554/427555/427557/485806/485807/485808/485811 （S8；VS 1.1.1—4.1.6 七则经文逐页核对）
5. https://www.wisdomlib.org/definition/padarthadharmasamgraha （S9；PDS 性质与"约公元4世纪末"系年）

草稿来源复核（URL 不变，见 9.2）：S1、S2、S3 重开逐字核验通过；S4 与第二轮独立核读一致。

查证后未列为来源：

- https://archive.org/details/padarthadharmasangrahaofprasastapadawiththenyayakandaliofsridharaganganathajha_202003_373_U ——Jha 英译 PDS 附 Śrīdhara 复注的书目佐证（元数据 API 核实）；扫描件 OCR 不可读，未引段落，故不入 sources（ Śrīdhara 复注的编本证据已由 S3 文件头覆盖）。
- 第一轮另曾下载 archive.org 的 Chakrabarty 2003 版权版《胜论经》译本，确认属版权出版物后弃用（不作来源、不引文字）；Sinha 1923 公有领域译本（S8）代之。

### 9.6 站外人物（更新）

本包人物全部为**站外人物**（`app/public/philosophers.json` 查无）：迦那陀、普拉沙斯塔帕达、Śrīdhara、法称、Gaṅgeśa Upādhyāya、Annambhaṭṭa、Udayana（时间线节点）、商羯罗·弥湿罗（新增）。沿用站内《印度哲学》的"迦那陀"写法并附梵文；其余以通行音译或拉丁转写为主名（同草稿译名政策，未改）。

### 9.7 合并后自检

- 数量：人物 7、关系 6、时间线 8、术语 10、著述 6、分支 4、阅读路线 2、来源 9——均在契约参考区间。
- evidence.json 71 条（第一轮 62 条全部保留，9 条新增/更新），JSON Pointer 与 packet.json 对位复核；两个 JSON 经 `python3 -m json.tool` 校验通过。
- 边界自检：仍仅写入 `docs/content-proposals/schools/I02/` 四个文件；未动站内任何数据；未做任何 git 写操作。
- 仍缺证据（在第七节基础上更新）：普氏精确定年（现两说并陈）、Śrīdhara 年代（Britannica 亦未系年）、廿四德后七德可靠名目、世亲与胜论直接论辩文献、'无'范畴确立的文本节点。无阻塞，可进入 Codex 审读。
