# I01 正理派（Nyāya）—— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I01`（proposedKind=school，P1-content-packet，cohort=南亚，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审；含同日草稿的第二轮逐源复核，见第八节）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。

## 一、边界决定

1. **范围锁定：量、推理与论辩**。按任务 scopeAndCautions，本包只展开正理的量论（现量/比量/譬喻量/圣言量，S2 逐一定义核读）、推理学说（五支论式、遍充、似因、择他 tarka）与论辩理论（宽容规则、默认信任、对怀疑论的回应）。正理的美学、语言哲学与价值论不作展开——IEP 该条目亦明言因篇幅略去这些主题（packet.json conclusion 末段已声明）。
2. **早期正理 vs 新正理**。以两个可核读的分期节点组织：11—12世纪正理与胜论合流（S3 逐字："at some point in the 11th or 12th century, they merged to form a new school"）、约1325年 Gaṅgeśa《真理如意珠》奠基（S2 逐字）。subSchools 按"历史阶段/学派阶段/主题/前史"分列四项，其中两项标 `kind: 主题`（自然神学、论辩术前史），避免把主题当组织分支。
3. **不移植数论内容**。Sāṃkhya 只在 overview 首段作为"非本条目范围"的边界出现一次；本包无任何数论术语、人物或谱系。与正理有真实亲缘的是胜论（姊妹学派，S3），二者关系按来源写"并行发展—合流"。
4. **学说与宗教实践之分**。这是本包刻意处理的规范点：正理属"正统六派"（承认吠陀权威）但《正理经》"压倒性地关注理论问题而非修行"（S2 逐字），瑜伽实践与解脱仅在个别经文（4.2.42、4.2.44–5）；Īśvara 论证写成"哲学的自然神学"（S2："India's most sophisticated natural theologians"），subSchools 第3条明注"不等于教团仪轨"。站内《印度哲学》"专注于逻辑学和辩论术"的既有定位与此一致。
5. **"新正理＝印度的分析哲学"是编辑框架**。Ganeri 条目（S3）把新正理与弗雷格、盖梯尔、休谟等并置比较；本包所有此类表述都标"学术比较/编辑比较，非影响关系"（relations/3、conclusion、readingRoutes/2）。

## 二、查重结论

- **学派条目**：任务 JSON 的 exactTopLevelEntries / exactBranches 均为空；另以 python3 复查 `app/public/schools/catalog.json`（不含"正理"）与 `app/public/schools/data/` 目录（无同名文件）。mentions-only 成立：仅 `school_印度哲学.json` 一处来源，"正理"12处（概述、时间线、works、quotes、cihai"因明"条），"Nyaya"1处。
- **人物**：`app/public/philosophers.json`（737人）python3 检索：**无** 乔答摩／乔达摩／足目／答摩／陈那／法称／伐差／乌地／Udayana／Jayanta 等条目——本包全部人物为**站外人物**（契约允许，此处声明）。注意两个"乔答摩"：站内《印度哲学》时间线里佛陀作"乔达摩·悉达多"（达），正理经作者作"乔答摩"（答）——站内数据已自行区分写法，本包沿用"乔答摩"以免与佛陀混淆；此写法差异已在 evidence（thinkers/0 note）说明。另有 7 位站内哲人简介含"正理"字样（宗喀巴、伊壁鸠鲁等），经查均为他义（如藏传"正理"课程语境），与正理派无人物重叠。
- **书籍**：`app/public/books.json`（409种）python3 检索"正理/Nyaya/Nyāya/因明/量论/印度逻辑"等：无正理相关藏书（"正理"2处为胡塞尔/德里达书名的子串误命中）。故 `relatedBookIds` 为**空数组**，readingRoutes 全部指向站外学术来源；无 TXT 占位书可关联。
- **旧正文处理**：站内《印度哲学》的 works 条目《正理经》（乔答摩，公元前2-公元2世纪）与时间线"公元前300 正理派和胜论派兴起"**未继承为本包依据**（见"分歧"）。

## 三、分歧与争议的处理

- **《正理经》编成年代**：S2（IEP）作 "attributed to Gautama (c. 200 C.E.)"，S3（SEP）作 "c. 100 C.E."——同一日核读的两个学术来源相差约百年。本包照实并列（时间线写"约公元1—2世纪（来源有分歧）"），并以两来源的年代差作为"可能多阶段编成"的证据；任务提示的"约公元前2世纪—公元2世纪间多阶段编成"这类宽范围**无来源支持，未采用**。
- **站内旧系年**：站内《印度哲学》时间线作"公元前300 正理派和胜论派兴起（乔答摩著《正理经》…）"、works 作"公元前2-公元2世纪"。两者均早于本次来源给出的归名年代约300年以上，未获核读来源支持。本包不改站内数据（所有权边界），在 evidenceLimits 第9条与 proposal.relationSuggestions 向 Codex 提交复核建议。
- **伐差耶那年代**：S1 "fourth century" vs S2 "约450年"——并存写出，不裁决（evidenceLimits 第3条）。
- **Udayana 年代**：S2 约975 vs S1 的11世纪——正文从 S2（更精确），evidence（thinkers/4）注明差异。
- **陈那—法称与正理的关系**：只有"乌地衍那吸收陈那学说"（S1 逐字）这类有据的阅读/批判关系入 relations；陈那—法称的师承细节来源未载，relation 措辞降为"前后相继"；法称—正理的分类对照为学派层面，标"编辑比较"。
- **量的"可靠主义先驱"与"可比于弗雷格"**：均为学术类比，正文处处注明非历史影响。

## 四、译名政策

- 仅采用站内已用的"乔答摩"（school_印度哲学 works 条目写法）。
- "伐差耶那（Vātsyāyana）""乌地衍那（Uddyotakara）"为常见汉译，本包采用并随附梵文；"足目"作为 Akṣapāda 的传统意译采用时注明"汉译本身未见于核读来源"（S3 只给梵文别号 Gautama Akṣapāda）。
- 其余人物（Jayanta Bhaṭṭa、Udayana、Vācaspati Miśra、Gaṅgeśa Upādhyāya、Annambhaṭṭa、Bhāsarvajña）的传统汉译未获核实，**主名用梵文拉丁转写**，不以臆测译名入条目（evidenceLimits 第6条）。
- 作品中文题名中"正理花束""推理撮要""正理蔓"等为编辑意译，works.desc 或 evidence 已注明性质；梵文原名均并列。

## 五、复核方法与结果

1. 三来源于 2026-10-04 实际抓取并读到相关段落；evidence locator 所引英文 verbatim 文本经缓存 HTML 去标签后逐字比对（含弯引号形态）：S1 核对15处、S2 核对27处、S3 核对14处另补验7处长句（手册、四部分、盖梯尔、第七范畴等），除4处长句以 WebFetch 抓取摘要为准（relations/3、subSchools/1、cihai/3、cihai/9）外全部直接命中，该4处的关键词与词列已在缓存文本逐字复核并在对应 uncertainty 字段注明。WebSearch 因服务端限流仅用于 URL 确认，未作依据。
2. evidence.json 共 60 条记录，JSON Pointer 对位 packet.json：overview 8、conclusion 2、thinkers 8、relations 5、timeline 10、cihai 10、works 7、subSchools 4、quote/quotes/closingQuote 4、relatedBookIds 1、coverageGap 1。
3. 数量：人物 8（含2位对手方）、时间线 10、术语 10、著述 7、分支 4、关系 5、阅读路线 2——在契约参考区间内（分支少于6是按证据如实分列：其中两项为 `kind: 主题/前史`，非组织分支，本派历史分期只有"早期/新正理"两段）。
4. 两个 JSON 以 `python3 -m json.tool` 校验通过；来源 ID（S1—S3）唯一且所有 sourceRefs 可解析（脚本核对见会话记录）。
5. 边界自检：仅写入 `docs/content-proposals/schools/I01/`；未动 app/、backend/、现有 schools 数据、进度台账。

## 六、仍缺证据（与 packet.json evidenceLimits 对应）

- 《正理经》编成年代的更精确分期（多阶段编纂的具体阶段划分）。
- 十六句义逐项名目（pramāṇa、prameya……nigrahasthāna 十六项的完整列举）。
- 陈那、法称著作名目及其与正理论师会面的直接文献证据（本包 works 对二人留空）。
- Jayanta、Udayana、Gaṅgeśa、Annambhaṭṭa 等的通行汉译名。
- 新正理在 Mithila／Navadvipa 学院制度中的传播史（S3 抓取文本未含）。
- 站内旧系年（公元前300／公元前2-公元2世纪）与《正理经》归名年代差（约百年）的调和——需另一层来源（如带文献学的原典导论）。
- 无阻塞：三来源全部可核读，本项可进入 Codex 审读。

## 七、实际核读 URL 清单（2026-10-04，两轮）

已核读并采为 sources：

1. https://plato.stanford.edu/entries/epistemology-india/ （S1；WebFetch + curl 全文缓存，DC.creator=Phillips, Stephen 与 Vaidya, Anand（2024-03-13 修订版起合著，packet S1 题名已补）；两轮逐字引文核验）
2. https://iep.utm.edu/nyaya/ （S2；WebFetch 超时后 curl 成功，86KB；作者信息：Matthew R. Dasti, Bridgewater State University；两轮逐字引文核验）
3. https://plato.stanford.edu/entries/early-modern-india/ （S3；WebFetch + curl 全文缓存，DC.creator=Ganeri, Jonardon；2023-11-05 修订；两轮逐字引文核验，初轮4处"据抓取摘要"的句子第二轮全部缓存逐字命中）

站内核对（python3，非网络来源）：

- `app/public/philosophers.json`（查重：无本包人物）
- `app/public/books.json`（查重：无正理相关藏书）
- `app/public/schools/data/school_印度哲学.json`（mentions-only 复核，"正理"12处定位；第二轮再核：时间线"公元前300"、works"公元前2-公元2世纪"、乔答摩3处/乔达摩1处（佛陀）逐条确认）
- `app/public/schools/catalog.json` 与 `app/public/schools/data/` 目录（无同名条目）
- `docs/tasks/school-content-gap-tasks-2026-10-04.json`（I01 条目）

## 八、同日草稿的第二轮处置记录（2026-10-04）

- **发现**：开工 `ls` 显示输出目录已有同日草稿（08:47–08:49，packet/evidence/review/artwork 四件齐）。按任务纪律不盲信，全部四文件重读，并对三个 sources 逐源重开核验。
- **方法**：WebFetch 对每源按断言清单逐点质询；再以 curl 抓全文缓存去标签，对 evidence.json 全部 locator 中的英文引文逐字 `str.find` 比对（含弯引号形态与 HTML 去标签后的空格粘连带，如 IEP 书目行 "JanakiVallabhaBhattacaryya"）；站内 books.json/philosophers.json/印度哲学.json 以 python3 重查。
- **处置决定：保留草稿主体，修正 6 处，不重写**。三来源真实、互不转抄、与断言对得上；草稿证据纪律总体良好（"拿不准就写进 evidenceLimits"执行到位）。修正项：
  1. **cihai/9（avacchinna）例句中译误置**：S3 原例为 "the property being-in-contact-with-the-monkey in the tree, is delimited by (avacchinna) the branch"——'与猴相触'的属性在树中被枝限定；初稿误作"与枝相触的出现，被枝所限定"。已改并写入 evidence 对应 note。
  2. **overview 默认信任句的 Matilal 归属精度**：S1 原文是正理原则 "Innocent until reasonably challenged"，Matilal 1986, 314 系证言语境的 "innocent until proven guilty"，S1 明言前者是其轻微弱化。初稿把该语直接系于 Matilal，已改写归属链。
  3. **overview 年代出入表述**：两来源系年差约一个世纪（c. 100／c. 200），初稿"近两个世纪的出入"失准，改为"约一个世纪的出入"。
  4. **S1 题名补合著者**：DC.creator 证实 2024 修订版起 Phillips 与 Vaidya 合著，packet S1 题名已补。
  5. **conclusion"约六百年的注疏链"**：来源不支持该具体时长（自伐差耶那 c. 450 至 Udayana c. 975 约 525 年，自经文 c. 200 计约 775 年），改为"绵延数百年的注疏链"。
  6. **圣言量经号分歧入 limits**：S2 系 śabda 定义于 NS 1.1.5，S1 系 āpta 定义于 NS 1.1.7——新增 evidenceLimits 第13条，works/0 与 cihai/6 相应注明。
- **另核**：初轮 4 处标注"据抓取摘要"的关系/分支/词条长句（relations/3、subSchools/1、cihai/3、cihai/9）第二轮全部在缓存文本逐字命中，uncertainty 已清或改注"已逐字核对"；thinkers/3 补记 S1 称 Jayanta 为"eighth-century"与 S2 c. 875 的年代小异；"a position taken by Gautama himself, the 'sūtra-maker'"（thinkers/0 的经文作者归属）已逐字验证成立。artwork-brief 无事实性断言，未改。
- **结论**：packet 仍为 ready-for-review；evidence.json 同步更新（cihai/3、cihai/9、relations/3、subSchools/1、thinkers/3、overview 事实性条目共 6 条 locator/note/uncertainty 修订）；两个 JSON 已重过 `python3 -m json.tool`。


## 主控修订记录（2026-10-04）

- 结构校验发现 overview 含未完全转述的'最伟大'措辞，已改为带出处的间接转述（SEP 原话经主控二次 WebFetch 核实）。
