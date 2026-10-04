# F01 认识论 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `F01`（proposedKind=field，cohort=跨传统问题，P1-content-packet，coverage=related-branches-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。

## 一、边界决定

1. **学科名晚出 ≠ 问题晚出**。SEP（S1）只支持两条：词源为 episteme+logos、术语"不过两个世纪老"而领域与哲学同样古老。overview 首段即据此声明本条目不设"创始人/成立年份"，以核心问题（知识定义、辩护结构、怀疑论、知识来源）与文献节点组织。通说的"费里尔1854年造词"未获核读来源，不写（evidenceLimits 第1条）。
2. **领域总览，不代述各传统内部认识论**。本条目只做领域骨架：泰阿泰德—JTB—盖梯尔（知识定义）、基础主义/融贯论（辩护结构）、古代与近代怀疑论（对手）、蒯因自然化与社会认识论/认识不义（20世纪两转向）。印度量论与墨家三表以核读过的原典/学术来源入场，kind 均标"主题（跨传统对照）"，relations 中墨子—柏拉图 type 为"编辑比较"；量论的派系之争、墨辩《经》上下的名辩体系明确声明不代述，交由站内《印度哲学》《墨家》专门条目。跨传统不凑配额：只有这两条有可核读来源，其余（口述知识论等）只建议"参见"。
3. **与5个既有相关子项的关系（逐一说明）**：均为其他父页下的子项，本包一律不改动，仅在 relationSuggestions 建议"参见"：
   - 北极原住民哲学→「口述智慧与叙事知识论」（index 3）：口述传承作为知识来源，属"知识来源"问题在特殊传统的延伸——建议从本领域入口参见；
   - 南岛哲学→「去殖民认识论」（index 2）：属社会/政治化知识论方向，与认识不义（S10）同属"知识与权力"问题域——建议参见；
   - 科学哲学→「无政府主义认识论」（index 4）：费耶阿本德方案属科学知识论内部激进立场，本包未核读相关来源，不代述——建议由《科学哲学》承载、从本领域入口参见；
   - 宗教哲学→「改革宗认识论」（index 4）：属"证言/基本信念"争论的特殊方案，本包未核读来源，不代述——建议参见；
   - 澳洲原住民哲学→「口述叙事认识论」（index 1）：同北极项，建议参见。
   - 上述5项与"正理/墨辩不得简单归为西方立场"同为本包 scopeAndCautions 的执行结果：包内跨传统材料仅 S11（量论）、S14（三表）两处，均有逐字核读。
4. **mentions-only 的处理**：任务 JSON 列 65 个 mention 文件。本包抽查 5 个（怀疑论/墨家/印度哲学/实用主义/分析哲学，python 计数为 1—4 次），均为正文级提及、不构成领域入口；未逐一语义审读 65 个文件（evidence.json 末条 uncertainty 已声明）。
5. **研究领域规范执行**：timeline 10 个节点全部是文献、文献编订/出版或学科制度事件（期刊创刊），无一虚构"成立于某年"；塞克斯都条目明确"具体成书年份不在来源内，不作系年"。

## 二、分歧与争议的处理

- **JTB 的地位**：S2 原文即带保留——"it's a bit of a convenient fiction to say that this so-called 'traditional' analysis was ever widely accepted"。overview 与词条均照录这层限定，不把 JTB 写成"传统定论"。
- **知识分析无解论**：Zagzebski 1994"不可逃逸"论证与"知识优先"转向并存于 S2，conclusion 写成"仍是活的争论"，不站队。
- **自然化的规范性难题**：S8 载"辩护是评价性的"这一传统特征陈述及对蒯因的批评章节，conclusion 写"温和自然主义仍在修补"，不作裁决。
- **休谟—皮浪关系**：只按 S4 原文（"Hume takes himself to engage with Pyrrhonian skepticism"）与 EHU §12 写，"天性总是强于原则"逐字有据。
- **蒯因—笛卡尔、笛卡尔—休谟两条关系**为条目框架层面的对接，S8 只支持"传统认识论以笛卡尔为自然起点"与"NE 纠正传统方案缺陷"，两条 relations 的 detail 与 type 均自注"编辑概括"，evidence.json uncertainty 同步。
- **justified 译名**：包内统一作"确证"，词条注明通行又译"证成""正当"，避免同义异译误读。

## 三、查重结论

- exactTopLevelEntries / exactBranches 均空 → 无同名顶级条目、无同名分支，无查重冲突。
- 5 个 relatedBranches 的关系建议见上节第3条；均不动原文。
- 65 个 mentions-only 条目列入 proposal.relatedExistingEntries 的代表项（19项），不逐条立传。

## 四、人物与书籍核对结果

- **人物（7位，全部为站内姓名与纪年，grep philosophers.json 实查）**：柏拉图（约前428/427—前348/347）、皮浪（约前360-前270）、塞克斯都·恩披里柯（约2-3世纪；SEP作约160—210 CE，并行标注）、勒内·笛卡尔（1596—1650）、大卫·休谟（1711-1776）、威拉德·范·奥曼·蒯因（1908-2000）、墨子（约前5世纪中后期）。葛梯尔、弗里克、戈德曼、富勒、扎格泽布斯基、陈那、法称等站内无条目者只出现在 timeline/works/词条/分支，不设 thinker 条目。
- **书籍（9个ID，python 在 books.json 逐条实查）**：谈谈方法 8c3044772b18（epub/15章）、第一哲学沉思集 88b56fb4da52（epub/21章）、人性论（全4册）178e7d06d42d（pdf）、皮浪学说概要 1c67b29ec906（pdf/93章）、人类理解论 44a32441dabe（pdf/70章）、纯粹理性批判 8c0c6955c793（pdf/17章）、语词和对象 9efee732eaff（pdf/8章）、人类知识原理 06cd5ed43ffb（txt/0章）、普通认识论 81548bf7104f（txt/0章）。后两种为 TXT 占位书，reason 已注明"不可在线阅读"；洛克、康德、蒯因、贝克莱、石里克诸书内容未核实，已注明"仅作关联建议"。

## 五、重要纠错（报请 Codex 处理，本包未改正式数据）

- **《皮浪学说概要》站内署名**：`app/public/books.json` 中 id=`1c67b29ec906` 的 author 字段作"皮浪"。通行学术归属为塞克斯都·恩披里柯（SEP Ancient Skepticism：PH 为塞克斯都所著三卷本；皮浪"未留下任何文字"，见 S4 逐字引）。建议 Codex 将该书作者正为"塞克斯都·恩披里柯"；本包 packet.json 的 works[1] 已按正确归属书写并括注站内现状。
- 另提示：站内 `philosophers.json` 中"塞克斯都·恩披里柯"的 school 字段为"怀疑论"，与 S4 载其属经验派医家（"Empiricus…a medical school"）不冲突（西文 Empiricus 派名与"怀疑论者"身份并存），无需改动。

## 六、复核方法与结果

1. sources 共15项，全部于 2026-10-04 实际打开并读到相关段落（11项学术百科 + 4项原典/原始文本）；WebSearch 片段一律不作为依据（当日搜索接口限流，亦未依赖）。
2. evidence.json 共 68 条，全部 fieldPath 经 python 按 JSON Pointer 实际解析到 packet.json 对位节点；thinkers/relations/timeline/cihai/works/subSchools 六个关键数组逐条覆盖（7/7/10/11/8/8）；每条 locator 含逐字短引文；sourceRefs 全部可解析到 sources 的唯一 ID。
3. 数量：术语11、时间线10、著述8、人物7、分支8、关系7、引语3+卷首/结尾各1——均在契约参考区间（其中 cihai 11 条略超"约6—10"参考值，因跨传统两条术语不宜合并，特此说明）。
4. 两个 JSON 以 `python3 -m json.tool` 校验通过（2026-10-04 会话记录）。
5. 年代复核：1637/1641/1642（S6）、1739/1740/1748/1758（S7）、1963（S15 出处行）、1969/1987/2007（S8/S9/S10）、约前369/前399（S3）、前3世纪—2世纪（S4）均有逐字定位；无凭记忆系年处。

## 七、仍缺证据（与 packet.json evidenceLimits 对应）

- "认识论"造词人与精确年份（通说费里尔1854）——来源只支持"术语不过两个世纪老"。
- 康德《纯粹理性批判》1781/1787、洛克《人类理解论》1690——未核读相应来源，正文不设节点、不系年，书籍仅关联建议。
- 戈德曼1999书名、弗里克2007书名副题、蒯因1969文集出处——未逐字核对，不写。
- S8 中"替换论/自由化"（replacement/liberalization）与"无限主义"、S2 中威廉姆森姓名的完整表述——未逐字截取，包内以概括措辞带过并在 evidence 标注。
- 印度各派量数完整对照（弥曼差、耆那教等）——只写正理派四量与佛教人物；顺世论只写来源所载"归纳诘难"一句。
- 《墨经》名辩体系、'廢以爲刑政'句版本异文（或作"發"）——无核读来源，不代述、以维基文库本为准。
- IEP 认识论总条目不可用（/epistem/ 重定向至无关条目、/epistemology/ 404）、SEP epistemic-injustice 专条当日"Not Yet Available"——均如实弃用，改以 SEP 分条目 + IEP 认识不义条目覆盖。

## 八、实际核读 URL 清单（2026-10-04）

已核读并采为 sources：

1. https://plato.stanford.edu/entries/epistemology/ （S1，WebFetch 通读，词源/来源五分/基础主义-融贯论/Gettier 段逐字）
2. https://plato.stanford.edu/entries/knowledge-analysis/ （S2，WebFetch，JTB史/Gettier两例/谷仓/修复谱系逐字）
3. https://plato.stanford.edu/entries/plato-theaetetus/ （S3，WebFetch，三定义/369BC/399BC/aporia 逐字）
4. https://plato.stanford.edu/entries/skepticism-ancient/ （S4，WebFetch + curl 全文 grep，运动起讫/皮浪无著述/塞克斯都/核心概念/休谟段逐字）
5. https://plato.stanford.edu/entries/descartes-epistemology/ （S5，WebFetch + curl 全文 grep，方法怀疑/我思/1641诘难段逐字）
6. https://plato.stanford.edu/entries/descartes/ （S6，curl 全文，1637/1641/1642 出版年逐字）
7. https://plato.stanford.edu/entries/hume/ （S7，curl 全文，1739/1740/1748/1758 逐字）
8. https://plato.stanford.edu/entries/epistemology-naturalized/ （S8，curl 全文，Quine 1969b:78 两句/规范性段逐字）
9. https://plato.stanford.edu/entries/epistemology-social/ （S9，WebFetch，定义/1987/1999/证言/分歧/专家段逐字）
10. https://iep.utm.edu/epistemic-injustice/ （S10，WebFetch，Fricker 2007/两形式定义逐字）
11. https://plato.stanford.edu/entries/epistemology-india/ （S11，curl 全文，pramāṇa-śāstra/四量/陈那法称/顺世论归纳段逐字）
12. https://www.gutenberg.org/ebooks/59 + 全文 https://www.gutenberg.org/cache/epub/59/pg59.txt （S12，cogito 段与 good sense 段逐字）
13. https://www.gutenberg.org/ebooks/9662 + 全文 https://www.gutenberg.org/cache/epub/9662/pg9662.txt （S13，custom/ proportions his belief/版权页逐字）
14. https://zh.wikisource.org/wiki/%E5%A2%A8%E5%AD%90/%E9%9D%9E%E5%91%BD%E4%B8%8A （S14，三表全段逐字）
15. https://www.ditext.com/gettier/gettier.html （S15，全文转录本，标题/出处行/齐硕姆条件/案例一逐字）

尝试后放弃（不可核读或不可用，未列入 sources）：

- https://iep.utm.edu/epistem/ → 重定向至无关条目"Epistemic Conditions of Moral Responsibility"，弃用。
- https://iep.utm.edu/epistemology/ → 404，弃用。
- https://plato.stanford.edu/entries/epistemic-injustice/ → 当日页面仅显示"Not Yet Available"，改用 IEP（S10）。
- https://plato.stanford.edu/entries/epistemology-indian/ 、/entries/nyaya/ 、/entries/dignaga/ → 404（正确 slug 为 epistemology-india）。
- en.wikisource.org/wiki/Meditations_on_First_Philosophy → 仅为索引页（正文在各子页），未逐页抓取；《沉思集》引文改由 S5/S6（SEP 所引英译）承载。
- Gutenberg 英译《沉思集》检得 #23306（拉丁文）与 #70091（Six metaphysical meditations），未采；#59/#9662 经全文 grep 无 1637/1748 出版年，改以 S6/S7 系年。
- https://plato.stanford.edu/entries/hume/ 之外未另觅休谟《人性论》原典（站内书 178e7d06d42d 仅作关联建议）。

## 九、二次复核补记（2026-10-04，第二名研究员；本节覆盖上文相应条目）

1. **独立重开全部 15 个旧来源**：WebFetch/web_reader 逐一重新打开并读取相关段落，全部在点、与引用断言相符（含 S4 古代怀疑论、S8 自然化、S12《谈谈方法》、S13《人类理解研究》、S14《非命上》三表段、S15 葛梯尔转录本的逐句核对；S6 笛卡尔主条目另补核 1596–1650/1637/1641/1642）。书籍 9 个 ID、evidence 全部 JSON Pointer、sourceRefs 可解析性均重新校验通过。
2. **补入康德（填平原包诚实标注的缺口）**：新增 S16（SEP Kant）、S17（SEP Kant's Transcendental Arguments）、S18（Gutenberg #52821《导论》公版英译），并在 packet 增补：thinkers 追加伊曼努尔·康德（站内姓名实查命中）、timeline 插入 1781/1787 节点、relations 追加休谟→康德（"独断迷梦"自述，引语只系于《导论》原典并在 evidenceLimits 声明转写与编排位置）、works 追加《纯粹理性批判》、overview 第三段与结论各补一句、proposal.scope 与书籍建议理由同步。第七节"康德未核读"一条自此作废；洛克 1690 一句仍维持不系年（二次复核经 SEP Locke 确认 1689/扉页1690 之别，包内仍不使用该年份，保持原状）。
3. **数量更新**：来源 18、时间线 11（插入康德后略超"约6—10"参考值，因康德为先验转向不可省的文献节点；其余参考区间不变）、evidence 74 条（timeline/6—9 指针已相应 +1 平移并全部重新解析通过）。
4. **未改动**：cihai、subSchools、quotes、引语、五个 relatedBranches 的边界决定、皮浪学说概要署名纠错建议——均维持原样。
5. 校验：packet.json / evidence.json 均以 `python3 -m json.tool` 通过（2026-10-04 二次复核记录）。


## 主控修订记录（2026-10-04）

- 结构校验发现 overview 含未完全转述的'最伟大'措辞，已改为带出处的间接转述（SEP 原话经主控二次 WebFetch 核实）。
