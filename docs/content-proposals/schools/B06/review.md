# B06 华严宗思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B06`（proposedKind=school，P1-content-packet，coverage=related-branches-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定与 T01 分工

1. **T01 总览 → B06 专条的明确分工**。T01《佛教哲学》是跨地区问题地图；其 evidenceLimits 明言"华严'四法界''六相'等术语未在本次核读来源中逐字出现，cihai 不收"。B06 恰好补齐：本包独立重抓 SEP buddhism-huayan 全文（104KB HTML→85KB 文本，未复用 T01 片段），多轮提取新增覆盖——四法界（SEP §6 澄观节全节）、六相（§4.3 六名英译＋定义）、五教与顿教争论（§4.4）、杜顺 li/shi 创新（§2）、李通玄一真法界（§5）、宗密《原人论》三教会通（§7）、会昌法难与理学挪用（§8）。建议两包互设导流：跨传统脉络归 T01，华严自身义理、文本与传承史归本包。
2. **宗派组织史与哲学论证分开**。subSchools 四条（新罗浮石宗／海东宗、日本 Kegon、高丽圆融宗）kind 均标"地域传统"；元晓"和诤"论系站内《韩国哲学》已有分支内容，本包不代为展开；timeline 只收有独立证据的人物与事件，不设"某年判教"类节点。
3. **判教按解释框架处理**。《分齐章》第三门自列古今十家判教（天台四教在内），表明判教是宗派立场的设计而非文献编年；SEP §4.4 记慧苑对顿教的批评与澄观的回护，说明判教名目本身即内部争讼之地。cihai 五教条与 conclusion 均显式声明。

## 二、五祖世系的追溯性建构问题（本包核心防误读决定）

任务提示"前两祖的追溯性建构问题，按来源呈现"。本包核实结果与分层处置：

1. **来源措辞本身分层**。SEP 对五祖用了三档不同的措辞：杜顺初祖是 **posthumous honor**（"身后的荣誉"，且其人"没有宗派归属"）；智俨、澄观、宗密之位均系 **Tradition identifies**（传统认定）；宗门祖师整体是 **allegedly transmitted**（"据说"传授正统）。这三档措辞在 evidence.json 中逐条留有 verbatim 定位。
2. **近代学术异议**（中文维基世系考證节整段收录）：境野哲考初传为智正—智现—贤首三代、"杜顺初祖说是后人杜撰"；铃木宗忠主张起自智俨；宇井伯寿主张智正—智俨—贤首；常盘大定支持杜顺传统说。四家并陈，不采单一说。
3. **文本归属问题**：题名杜顺的《华严法界观门》，en 维基明言"现代学者质疑此归属"；SEP 记原书已无独立传本、文字存于澄观（T45.1883）与宗密（T45.1884）注疏。本包一律作"题杜顺"。
4. **谱系会被回溯改写**：en 维基记慧苑因改易师说被澄观一系"retroactively sidelined"（回溯性排除）出祖师谱系；中文维基记宋代加马鸣、龙树为西天始祖后宗密成七祖。以上均入 packet 的 overview/conclusion 与 evidenceLimits。

## 三、五教十宗的核来源（任务提示"写前核来源"）

五教十宗未取二手转述，而以维基文库《华严一乘教义分齐章》全文为文本凭据：

1. **五教**：第四门"分教开宗"原文——"初就法分教。教类有五。后以理开宗。宗乃有十。……一小乘教。二大乘始教。三终教。四顿教。五圆教。"全文逐字命中。
2. **十宗**：同门十宗名目逐字命中（一我法俱有宗／二法有我无宗／三法无去来宗／四现通假实宗／五俗妄真实宗／六诸法但名宗／七一切法皆空宗／八真德不空宗／九相想俱绝宗／十圆明具德宗）。
3. **与 SEP 的对应**：SEP 记法藏判教与三性、六相诸义出 Treatise on the Five Teachings of Huayan（Huayan Wujiao Zhang；T45.1866，判教在前九章、独特教义在第十章）；《分齐章》十门结构（第四门判教、第十门义理分齐含六义六相）与之吻合。**题名对应关系未核版本目录专书**，packet 按两源题名分别标注并在 evidenceLimits 声明——这是诚实的处理，不冒充已证同书。

## 四、澄观与宗密的转折（任务要点）

- **澄观**：SEP §6 全节核读——历九朝；四法界理论为其"最有特色贡献"（事／理／理事无碍／事事无碍，后两界与杜顺三观对应，"理事无碍是事事无碍的基础"）；其华严疏"取代了法藏注疏的权威与影响"；以顿教配禅门回护法藏判教；安史之乱后"借词不借义"引儒典化导士人。生卒两源不一（SEP/en 维基 738—839 vs 中文维基 737—838），并陈不采定论。
- **宗密**：SEP §7 全节核读——先从遂州道圆（750—820）得法为**荷泽宗祖师**、后从澄观学《华严》（华严与禅合流的枢纽）；《原人论》（T45.1886）或回应韩愈《原道》，自设五等判教并把儒道纳入会通；en 维基记其以《起信论》"一心"为最高教旨、"把《华严经》置换为《大乘起信论》"。生卒两源不一（780—841 vs 784—841），并陈。
- **《原人论》已全文核读**（维基文库）：序＋四篇目录、序文三教会通纲领句、斥偏浅第二五等判教句均逐字定位（S3）。

## 五、《华严经》与《大乘起信论》的关系（任务要点）

1. **经的层面**：华严宗名与义理所系为《华严经》；SEP 记华严兼取《起信论》之教；en 维基记《起信论》为法藏、宗密共作注的"另一关键经典"，宗密且以之置换《华严》的至高地位。
2. **义理层面**：SEP 记法藏《大乘起信论义记》（T44.1846）"把一心等同于如来藏"，并以《起信论》的体用两分（不变／随缘两重性格）调停瑜伽行与中观的三性之争——此即华严受起信论塑造的核心机制。
3. **文本凭据的限度**：维基文库《大乘起信论（真谛译）》为**未完成页**（页面自标"此文档未完成"），仅智恺序与归敬偈可逐字核读；一心二门等义理正文无文本凭据，本包只按 SEP／en 维基转述；起信论成书与译者之争（学界"疑伪"讨论）未在本次核读来源中出现，不作断言。已入 works[7] desc 与 evidenceLimits。

## 六、查重与既有内容

- 任务 JSON：exactTopLevelEntries／exactBranches 均空；relatedBranches 2 项（隋唐佛学 subSchools[2] 华严宗五教判释系、韩国哲学 subSchools[3] 韩国华严与唯识学（和诤思想））；mentionFiles 2 项（两文件命中词均"华严宗"）。站内无同名顶级条目，本包为该主题首个专门深度条目，coverage=related-branches-only 处置成立。
- **人物**：philosophers.json 实查（python，键名子串）——站内 3 人：**法藏**（643-712年，与本包一致，直接采用）、**义湘**（era 仅"7世纪"；本包从 en 维基/SEP 作 625—702 并声明）、**元晓 (Wonhyo)**（617–686，站内条目键名带英文括注，本包用"元晓"简称并在 sub 注明）。站外 5 人：杜顺、智俨、李通玄、澄观、宗密——按契约保留准确姓名、在 sub 标注站外，不改动哲学家名单。
- **书籍**：books.json 实查（python，华严/華嚴/起信/金师子/探玄/杜顺/法藏/澄观/宗密/原人论 等关键词）——无华严专门藏书；唯一佛学通史书蒋维乔《中国佛教史》1201d003be31 仅作通史关联建议（与 B05 同），未核读内容、不写"华严原著可在线阅读"。
- **既有子项复用**：《隋唐佛学》subSchools[2] 华严宗五教判释系（era"唐至宋"，desc 与本包证据一致但无出处）、works《华严经探玄记》、cihai 词目（华严/法界缘起/六相圆融）——本包为其补齐来源与逐字定位，属"已有子项要复用并深化"，不重复造页面。

## 七、分歧与争议的处理

- **澄观生卒**：738—839（SEP/en 维基）vs 737—838（中文维基）——thinkers 主纪年从 SEP，差异并陈。
- **宗密生卒**：780—841（SEP/en 维基）vs 784—841（中文维基）——同上。
- **会昌法难年份**：842—846（SEP）vs 841—845（en 维基）vs 845（中文维基）——timeline 取 842—846 并三说并陈。
- **四法界的著作归属张力**：S1 记原书题杜顺、澄观作注；en 维基一句把四法界框架系于"Chengguan's meditation manual (Huayan Fajie Guanmen)"——两说并陈，本包从 SEP 的分层表述（理论定型于澄观、文本托名杜顺）。
- **四种缘起分判**：中文维基该句自带 [來源請求] 维护标记——只作背景提及，不入 cihai 断言。
- **海印/华严两种三昧、义天赠书单、审祥—良弁线**：部分为单源（中文维基），已逐条在 evidence uncertainty 标注。

## 八、复核方法与结果

1. curl 全文抓取：SEP buddhism-huayan（104KB）、维基文库《華嚴一乘教義分齊章》（196KB，全文）、《原人論》（81KB，全文）、《大乘起信論（真諦）》（59KB，未完成页——如实降级使用）、《大乘起信論》版本页（55KB）、en.wikipedia Huayan（843KB）、zh.wikipedia 华严宗（184KB）。检索摘要一律不作为依据；所有关键引文（中英文）均在全文中逐字定位命中（含 SEP 全部人名纪年、Rafter Dialogue 论证、四法界全节、宗密两难论证；分齐章五教十宗六相全文；原人论序与五等判教）。
2. evidence.json 共 74 条记录（overview/conclusion 9、thinkers 8、relations 7、timeline 13、cihai 13、works 8、subSchools 4、引语 7、proposal/coverage/书籍/relatedExisting 与当代研究等 5——其中查站内文件者无站外来源，sourceRefs 留空并在 locator 注明实查文件），每条含 verbatim 定位；全部 fieldPath 均经脚本回解析到 packet.json 对应节点（74/74 通过）。
3. 数量：来源 6（学术百科 1 ＋ 原典 3（其一为未完成页，降级为书目/序偈凭据）＋ reference 2）——S1 支持学说范围与归属，S2/S3 支持原典与论证，S4 为书目级，S5/S6 为 reference 级并声明用途；人物 8（站内 3＋站外 5）、时间线 13、术语 13、著述 8、分支 4——在契约参考区间内。
4. 结构契约自检（脚本实查）：两个 JSON 经 `python3 -m json.tool` 校验通过；relations 七条 from/to 端点逐一比对等于 thinkers[].name 精确字符串；sourceRefs 全部可解析至 sources[].id；packet 顶层与 school 内均有 readingRoutes 与 evidenceLimits。
5. **引语逐字回验（脚本实查）**：quote、quotes[0]—[4]、closingQuote 共 7 条引文，全部经脚本对维基文库全文回验为**连续逐字子串**（复核中发现两处与页面原貌的标点差异并当场修正：closingQuote'张大教网置生死海。漉人天鱼置涅槃岸。'页面'网''鱼'后本无句读，从页面原貌；quotes[4]补还原原文括注'(上四在此篇中)(此一在第三篇中)'）。无 paraphrase 冒充引文；十玄门/六相/十宗等术语条目均以原始文献定位为凭，无凭空子派。

## 九、仍缺证据（与 packet.evidenceLimits 对应）

- 《大乘起信论》一心二门正文：维基文库未完成页，无文本凭据；成书与译者之争未核。
- 《分齐章》第二藏经对勘未做（CBETA 在线版 JS 渲染无法抓取）；维基文库该页正文为简体转写。
- 《华严一乘教义分齐章》＝《华严五教章》的题名对应：按内容结构吻合处理，未核版本目录专书。
- 李通玄、义湘、元晓的中文/韩文专门研究未核；元晓"和诤"论只按站内已有分支保留，不展开。
- 华严与密教、华严念佛（中文维基仅空标题）；澄观《华严经疏》卷帙、宗密《圆觉经》疏、《华严金狮子章》全文（金狮喻仅按 SEP 英文段转述）均未核。
- 华严对禅宗五家、对宋明理学的具体影响机制：按 en 维基/SEP 转述其结论，未核禅宗原典与理学原书（Priest 2015、牟宗三仅记其存在）。

## 十、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/buddhism-huayan/ （curl 全文＋多轮 grep 逐字）
2. https://zh.wikisource.org/wiki/華嚴一乘教義分齊章 （全文，五教十宗/六相/一即一切/海印三昧/十钱喻逐字命中）
3. https://zh.wikisource.org/wiki/原人論 （全文，序与五等判教逐字命中）
4. https://zh.wikisource.org/wiki/大乘起信論 （版本页）
5. https://zh.wikisource.org/wiki/大乘起信論_(真諦) （已打开核读；未完成页，仅序偈可引，义理正文未采）
6. https://en.wikipedia.org/wiki/Huayan （curl 全文＋定位）
7. https://zh.wikipedia.org/wiki/華嚴宗 （curl 全文＋定位）
- 说明：SEP buddhism-huayan 本日 T01 工作曾核读数处片段（一即一切句、Fazang 生卒、Rafter Dialogue、词源、中观/瑜伽行/起信论兼取、朝鲜日本传播句）；本包按任务提示**独立重抓全文深挖**（多轮 grep：四法界、六相、五教、宗密、澄观、理学、当代诸主题），未复用 T01 片段。
- 未用：CBETA 在线版（JS 渲染抓不到正文）；未尝试 Britannica（B05 已实测反爬页无正文，本包 6 源已足）。

## 十一、二轮独立核验与修订（2026-10-04 下午，第二名研究员）

首轮交付后，任务方派第二名研究员对本包做独立二轮复核。方法：WebFetch 逐项复验六源（SEP 四轮定向提问、维基文库两原典三轮、en/zh 维基百科各两轮）＋ **en.wikipedia raw wikitext（`action=raw` 全文检索）作裁决通道**（HTML 抓取对该 843KB 页面会截断，raw wikitext 可全检）＋ python 实查 philosophers.json / books.json / 隋唐佛学 / 韩国哲学。结论分三类：

### A. 证伪并修正（13 处）

1. **timeline[3] 智俨"661 年受晋王（Prince Pei）命"**：SEP 原文作 "Prince Pei"，直译"晋王"属误译（Pei≠晋）；已改按原文直录"Prince Pei（SEP 原文如此，汉文封号不作断言）"。首轮 uncertainty 中"齐王李恪？"的猜测一并删除。
2. **李通玄"日食七枚枣椹之饼"**：SEP 原文 "a daily meal of only seven rice cakes made with dates and cypress"——枣与**柏**，非"椹"；已改。另"迷悟"无实然分离系添加（SEP 只说 sacred/secular、Buddha/sentient beings），已删。
3. **法藏"以金狮子喻教武后"**（overview＋thinkers＋artwork-brief）：SEP 只记金狮像之喻，未说为武后而设；S6 仅列《华严金獅子章》书名。已改"金狮子像为喻（《华严金狮子章》，S6）"，不再系于教武后。
4. **海印三昧条**：初版称"SEP/en 维基记华严举 haiyin sanmei 与 huayan sanmei 为两种关键三昧"并录 S5 英文原句——经 raw wikitext 全文检索，en.wikipedia **不含** ocean-seal／haiyin sanmei 字样，该句判为不成立引文；zh.wikipedia 亦无海印三昧概念性记载。词目改为仅凭《分齐章》开篇原文（S2），释义句标注"编辑释义"，sourceRefs 收缩为 [S2]。evidence.json 对应条目已改写并记录裁决过程。
5. **四法界"同一真性"**（overview＋cihai）：zh 维基逐字释义为"雖有差別，而**同一體性**"，非"同一真性"；两处已改从页面原文（四条释义均已逐字核对）。
6. **cihai 四法界"en 维基：sifajie…终成华严禅观的中心框架"**："sifajie"拼法与"中心框架"定性未在 en 维基核得；已改"en 维基设 'Meditation and the fourfold Dharmadhatu' 专节（洞山五位即基于四法界建立，S5 原句）"。
7. **overview"事法界（'conditioned, akin to an illusion'）"**：该英文短语未在 SEP 核得；改为不引号的白描（"一一差别、各有分齐的现象界"，后者恰与 zh 维基释义"各有分齊"相合）。
8. **SEP"以智俨为'法界缘起'说的建立者"**：SEP 未用单一"建立者"措辞（系于智俨 panjiao、承杜顺）；已改"系于智俨（承杜顺而阐）"并补 en 维基原句佐证。
9. **"以《起信论》的体用两分调停三性之争"**：SEP 原文为 "adapting the perspective-taking tactic of the Awakening of Faith to the three nature theory, ascribing two aspects to each nature"，"体用两分／不变随缘"是以传统名相冒充 SEP 术语；已改按原义转述。
10. **"SEP 记其历仕九朝"**：SEP 原文 "lived through the reigns of nine Tang emperors"（身历，非历仕）；已改。
11. **杜顺"俗家事功见于乡野教化"、智俨"晚年居长安"**：两处均无来源支撑；已删（分别代以 SEP 记载的活跃时段与至相寺）。
12. **义湘《法性偈》"又名华严法界图"**：en 维基原句为 "also known as the Diagram of the Realm of Reality"（无"华严"前缀），且未给出 hanja——"法性偈"三字为通译写法。thinkers/subSchools/timeline/S5 coverage 四处已改，并在 evidenceLimits 性质的说明中标注。混入的英文 "摄华严 teaching" 已统一为"摄华严教学"。
13. **overview 两处引号断言**：'独具中国特色的佛教形态'（SEP 原文未见此前提，改为编辑概括并补 intrinsic value 原句）；新儒家宣言"'圆而神'之智"（SEP 原文 rounded and spiritual wisdom，汉字回译性质已标注）；另删 "화엄" 谚文（未核）。works[0]《华严经》desc 的"五十三参"（未核）与 dragon girl 系属（龙女故事出自《法华经》，SEP 系于李通玄段）已改写。S1/S2/S5/S6 四条 sources coverage 的相应描述同步订正。

### B. 裁决为真并保留（HTML 抓取截断曾致误疑）

- en 维基宗密句 **"displaces the Avataṃsaka in favor of the Awakening of Faith (which emphasizes the One Mind)"**——raw wikitext 证实存在，overview 与 thinkers[5] 的"置换"表述保留。
- en 维基法藏句 **"the Buddhist teacher of the Empress Wu Zetian (684–705)"**——证实存在，"武曌的佛教教师"保留（locator 已补 raw wikitext 原句）。
- 首轮自检修正的两处引文（closingQuote 标点、五等判教括注）经复验无误。

### C. 站内核对（python 实查，2026-10-04）

- philosophers.json：法藏（643-712年，隋唐佛学）、义湘（7世纪，华严宗/佛教）、元晓 (Wonhyo)（617–686）站内实有；杜顺、智俨、李通玄、澄观、宗密无条目——与本包 sub 标注一致。
- books.json：无华严专门藏书；蒋维乔《中国佛教史》1201d003be31 实有（epub 21章），仅作通史关联建议。
- 《隋唐佛学》：thinkers 有法藏（works 仅《华严经探玄记》）、cihai 有"华严/法界缘起/六相圆融/法界缘起 (Dharmadhatu Dependent Arising)"、subSchools[2] 华严宗五教判释系（era 唐至宋）——与 proposal.relatedExisting 描述一致。

### D. 二轮核读 URL 清单（均为 2026-10-04）

1. https://plato.stanford.edu/entries/buddhism-huayan/ （WebFetch 四轮定向提问，20+ 断言逐字）
2. https://zh.wikisource.org/wiki/華嚴一乘教義分齊章 （三轮：15 项逐字＋6 项精确串＋顿/终教引经）
3. https://zh.wikisource.org/wiki/原人論 （10 项逐字）
4. https://zh.wikisource.org/wiki/大乘起信論_(真諦) （未完成页性质确认）
5. https://en.wikipedia.org/wiki/Huayan （HTML 两轮＋raw wikitext 裁决一轮）
6. https://zh.wikipedia.org/wiki/華嚴宗 （16 项逐字＋四法界/三观释义补轮）
7. en.wikipedia raw 通道：https://en.wikipedia.org/w/index.php?title=Huayan&action=raw

修订后自检：packet.json / evidence.json 经 `python3 -m json.tool` 校验通过；relations 端点、sourceRefs、fieldPath 全部回解析通过（见 evidence.json 新增 12 条二轮记录，总 86 条）。
