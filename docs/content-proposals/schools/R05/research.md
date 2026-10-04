# R05 行动哲学 —— 次轮候选研究备忘录

任务来源：`docs/tasks/school-content-gap-tasks-2026-10-04.json`（id=R05，P2-research-only，coverage=mentions-only，cohort=混合；先研究边界）。本文档只做研究判断，不建正式条目，未获发布授权。

## 1. 候选概述

行动哲学（Philosophy of Action，亦译"行为哲学"）是研究行动（action）的本质、结构与解释方式的哲学领域，属 20 世纪分析哲学确立的核心分支之一。SEP"Action"条目（2023）开宗明义："The central question in philosophy of action is standardly taken to be: 'What makes something an action?'"（行动哲学的中心问题通常被认为是："是什么使某事成为一个行动？"）。这一问题要在行动与单纯身体事件之间划界：最常用的对照来自维特根斯坦——"举起手臂"与"手臂自己抬了起来"（被人在睡梦中挠痒抬起的情形）差在哪里。SEP 进一步区分被动性/主动性（火烧木头）、动物行动与人类有意行动，后者被界定为我们"理性能力的实践显现"（practical manifestations of our rational capacities）。

该领域的现代奠基通常归於两部著作：安斯康姆（G. E. M. Anscombe）的《意向》（Intention，1957）与戴维森（Donald Davidson）的《行动、理由与原因》（"Actions, Reasons, and Causes"，1963）。戴维森一系（SEP 沿用 Velleman 1992 的命名称之为"行动的标准图景"/the 'standard story' of action）主张两个核心论题：行动解释诉诸"初始理由"（primary reason，即信念—欲望对）；且"初始理由也是行动的原因"——合理化（rationalization）是因果解释的一个种。IEP 戴维森条目（作者 Vladimir Kalugin）概括其动机：一个人"可以有某个行动的理由、做出了该行动，而这个理由却不是他做该行动的理由"，故只有把生效的理由当作原因，才能解释"多个理由中为何恰是这个理由起了作用"。戴维森由此把行动归结为身体移动："we never do more than move our bodies: the rest is up to nature"（我们做的从来不超过移动我们的身体：其余交给自然）。安斯康姆一系则是因果论的主要对手：她以特殊的"为什么？"问法界定有意行动，主张"实践知识"（practical knowledge）是"其所理解之物的 cause"（the cause of what it understands），行动者对自身行动的认知"无需观察"（without observation），并提出了"描述下的行动"（action under a description）这一标志性概念——同一动作（拨动开关/开灯/惊动窃贼）在不同描述下意图性不同（SEP 引费恩伯格〔Feinberg〕所谓"手风琴效应"）。

核心争论集中在四组：(a) **理由是否原因**——梅尔登（Melden）以"逻辑关联"论证反对休谟式原因进入行动解释，戴维森以"晒伤"例反驳：描述间的逻辑依赖不推翻事件因果；非因果替代方案有齐硕姆（Chisholm）的行动者因果（agent-causation）与舒勒（Schueler）、塞昂（Sehon）的目的论解释；(b) **基本行动**（basic action）——丹托（Danto）所谓"不通过做别的事而做"的行动，为避免无穷倒退而设；SEP 区分知技能性、因果性、目的论性三种"基本性"，并记录了汤普森（Thompson）与拉文（Lavin）对目的论基本性的批评；(c) **意图的地位**——意图作为心理状态与行动的关系、意图与实践知识的分工；(d) 与**自由意志**问题的接壤。就本站定位而言，行动哲学是"理论性"领域：它解释行动是什么、如何被说明，而不规范行动应当如何——这正是它与伦理学、实践哲学划界的关键（见第 3 节）。

## 2. 已有覆盖定位

任务 JSON evidence：exactTopLevelEntries/exactBranches/relatedBranches 均为空，仅 4 处 mentionFiles。站内核读（grep/python 检索，2026-10-04）确认：

- **北欧哲学包有唯一的实质承载**：`app/public/schools/data/school_北欧哲学.json` 中冯·赖特（G. H. von Wright，1916–2003）thinker 条标注"分析哲学/行动哲学"，关键词"行动的逻辑、规范与价值、维特根斯坦遗产"，著作列《规范与行动》《解释与理解》；works[4] 为《规范与行动》（1963，"在行动哲学与规范逻辑领域的代表作，系统分析了行动、规范与因果性之间的关系"）；词海词条另有一条"由芬兰哲学家 G.H.冯·赖特发展的"行动逻辑分析（行动的逻辑结构、意图、因果关系与伦理责任）。这是站内唯一触及分析行动哲学真实脉络的内容，但它是**流派包内的人物条目**，不能替代领域总览。
- **其余三处均为宽泛用法**：`school_道家.json` quotes[3].exp "此句凝练了道家行动哲学的精髓"（指无为）——是把"行动哲学"当作一家实践态度的修辞性说法；`school_旧民主主义.json` cihai[27] "体现旧民主主义时期行动哲学的务实倾向"（指知行观）；`school_后殖民哲学.json` cihai[26] 弗莱雷"连接后殖民理论与行动哲学"。三处都不在做行动哲学作为哲学分支的意义上使用该词。
- **关联散点**：grep 全部 111 个条目文件，"戴维森"仅见于 `school_北美哲学.json`；"实践哲学"散见北欧、北美、马克思主义、韩国哲学等包（多为泛指）；"意图"命中面广但均为泛用。**catalog（111 个条目）中无"行动哲学"条目，也无"心灵哲学"条目**——即该领域在站内既无归属包，也无同级领域条目。

**判断**：现有材料是"宽泛用词 + 单点人物"的形态——术语在三处被借用作各家的实践态度，唯一实质内容（冯·赖特）嵌在北欧哲学包内。领域总览无法由任何既有包承载：(a) 作为标准哲学分支的行动哲学（安斯康姆、戴维森、理由—因果之争、基本行动）在站内零覆盖；(b) "行动哲学"一词在站内的宽泛用法恰需一个领域条目来正名划界；(c) 它横跨分析哲学、北欧哲学、心灵哲学、伦理学诸包，放进任何单一流派包都会归属错置。

## 3. 范围建议（若立项）

- **建议类型**：`field`（领域总览），与站内已有的"伦理学""政治哲学""宗教哲学""人工智能哲学""社会学"等以领域为单位的条目同型，而非流派。
- **应覆盖**：领域的界定与中心问题（行动 vs 单纯事件）；奠基史（安斯康姆《意向》1957 与戴维森 ARC 1963 双峰）；理由与因果之争（因果主义/标准图景 vs 安斯康姆—冯·赖特非因果传统、行动者因果、目的论解释）；描述下的行动与基本行动；意图与实践知识；末节点出非西方传统的对照定位（儒家知行观、道家无为可作"行动思想"对照，点到即止）。
- **不应覆盖（改为关联）**：道家无为详述（归道家包）；知行合一详述（归儒家/宋明理学相关包）；冯·赖特与规范逻辑细节（归北欧哲学包）；韦伯式社会行动理论（归社会学包）；存在主义"行动/介入"、实用主义行动观（归各自包，领域条目仅作脉络提示）；自由意志与决定论（独立大问题，只交叉链接）；戴维森的语义学/心灵哲学面（若未来立语言哲学或心灵哲学条目再展开）。
- **边界辨析**（任务 scopeAndCautions 明确要求）：
  1. **行动哲学 ≠ 实践哲学（practical philosophy）**：后者是规范学科的伞形称谓（伦理学、政治哲学、法哲学的统称），处理"应当如何"；行动哲学是理论性领域，处理"行动是什么、如何解释"。冯·赖特《解释与理解》一路的"解释学—规范"工作恰在两者接口处。
  2. **与伦理学**：伦理学以行动为评价对象（正当/不当），行动哲学提供行动的结构与解释理论，二者是"理论—规范"分工；但人物常双栖——安斯康姆即"best known to philosophers today for her work on ethics and the philosophy of action"（IEP），《现代道德哲学》与《意向》同出一人。若次轮立元伦理学类候选（如 R07），在"道德理由是否也是行动理由"一点上相邻，交叉链接即可。
  3. **与心灵哲学**：意图作为心理状态的本体论归心灵哲学；行动哲学关注意向性行动的出身、结构与解释。站内暂无心灵哲学条目，将来立条时两边互设关联。
  4. **与社会学行动理论**：韦伯"社会行动"以意义与他者取向定义，属社会科学奠基之争，站内社会学包已承载；行动哲学条目只作概念区分提示。
  5. **与站内宽泛用法的关系**：道家/旧民主主义/后殖民三处"行动哲学"是修辞借用；新建领域条目后应在那些位置保留原表述（各包语境自足），由领域条目承担正名功能，不回改站内文本。

## 4. 来源

1. **"Action"（斯坦福哲学百科，First published Wed Jan 11, 2023）** — https://plato.stanford.edu/entries/action/ ，访问日期 2026-10-04。支持：领域中心问题（"What makes something an action?"）、维特根斯坦举臂对照、理性能力的实践显现、"标准图景"命名（Velleman 1992）、戴维森两论题与"we never do more than move our bodies"、安斯康姆实践知识（"the cause of what it understands"、without observation）、描述下行动与手风琴效应（Feinberg）、理由—因果之争（Melden/晒伤/Chisholm/Schueler/Sehon）、基本行动三种基本性与 Thompson/Lavin 批评。
2. **"Donald Davidson"（互联网哲学百科 IEP，作者 Vladimir Kalugin，California State University, Northridge）** — https://iep.utm.edu/davidson/ ，访问日期 2026-10-04。支持：理由作为原因是戴维森对行动哲学的主要贡献、"rationalization is a species of causal explanation"（ARC 1963，收入 Essays on Actions and Events 1980）、"可以有一个理由且做出行动而该理由非其所为之理由"的反事例论证、行动作为事件的同一性（因果关系个殊化）、causality 的法则性特征与心灵的异常论（anomalism of the mental）。
3. **"Anscombe, G. E. M."（互联网哲学百科 IEP）** — https://iep.utm.edu/anscombe/ ，访问日期 2026-10-04（curl 全文核读）。支持：安斯康姆"best known to philosophers today for her work on ethics and the philosophy of action"；《意向》"Extremely important for understanding contemporary philosophy of action"；1956 年反 对授予杜鲁门荣誉学位之后"其书长篇研究有意行动之性质的著作于次年出版"（即 1957），次年再发《现代道德哲学》；维特根斯坦遗产执行人（1951 年指定）与《哲学研究》英译（1953）。
4. **Britannica"G. H. von Wright"专页（讨论于 applied logic: Epistemic logic 词条）** — https://www.britannica.com/biography/G-H-von-Wright ，访问日期 2026-10-04。支持：冯·赖特的芬兰哲学家身份、"generally recognized as the founder"（道义逻辑奠基，1951）。该页仅覆盖"规范逻辑"半边，未涉其行动哲学细节（见第 6 节）。

四来源独立撰写（SEP 主题式条目、IEP 两条人物专条、Britannica 逻辑词条），未互相转抄。注：Britannica 疑有"philosophy of action"专条（https://www.britannica.com/topic/philosophy-of-action），两次尝试（WebFetch 与 curl）均被 Cloudflare 拦截（403/"Just a moment"），未能核读，故不引用。

## 5. 立项判断

**结论：新建**（次轮，类型 `field`）。理由：

1. **领域空缺且无承载包**：行动哲学是标准哲学分支，站内 111 个条目无一覆盖；唯一实质内容（冯·赖特）是北欧哲学包内的人物条目，从流派视角无法替代领域总览。
2. **术语正名的实际收益**：站内三处把"行动哲学"宽泛地用作各家的实践态度；一个领域条目能澄清该词的学科含义及其与道家无为、知行观、解放教育学等语境的区别，这正是任务要求"先研究边界"的价值所在。
3. **形态匹配**：站内已有"伦理学""政治哲学""人工智能哲学""社会学"等 field 型条目，行动哲学与之同型，目录扩展无结构障碍。
4. **文献无障碍**：奠基人物（安斯康姆、戴维森、冯·赖特）、核心争论（理由与因果、基本行动、描述下行动）归属清晰、来源充足（本轮已核读 SEP + IEP×2 + Britannica），无"先核实"级阻塞，不满足"暂缓"条件。相对"仅加关联"：关联无法解决术语误用与领域总览空缺，故不取。

## 6. 证据限度与分歧

- **术语译法**：Philosophy of Action 通译"行动哲学"，亦有"行为哲学"；action 与 behavior（行为）的区分本身是领域内议题，中文条目宜首现时说明。Anscombe《Intention》通行中译《意向》（亦见《意图》），条目行文需固定其一并注原文。安斯康姆引文（"the cause of what it understands"、"without observation"）经 SEP Action 条目转述核读，非《意向》原典直读。
- **归属与年代**：《意向》出版年 1957 为通行说法；IEP 安斯康姆条目未直接给出年份数字，仅记 1956 年杜鲁门事件"次年出版"，与通行纪年吻合，作 1957 处理。"标准图景"（standard story）之名出自 Velleman 1992（SEP 转引），本条目未核读 Velleman 原文。
- **冯·赖特"先核实"项**：站内北欧哲学包称《规范与行动》（1963）为"行动哲学与规范逻辑领域的代表作"；本轮 Britannica 材料仅确证其芬兰哲学家身份与道义逻辑（deontic logic，1951）奠基地位，SEP"Action"条目抓取部分未讨论冯·赖特，其行动哲学因果论立场（反对理由作为原因、主张"逻辑联系"）**未经本轮来源独立核实**，正式建条前须补读《规范与行动》或 SEP"Deontic Logic"/相关研究文献。
- **未核读项**：SEP"Action"条目作者名位于页面 Author and Citation 区，本轮抓取内容截断，不写出作者名；Britannica"philosophy of action"专条被反爬拦截，其是否存在及内容不明；Velleman（1992）"standard story"原始表述、Feinberg"accordion effect"与 Danto 基本行动的原始文献均经 SEP 转述，未读原典。
- **跨候选交叉**：与次轮伦理学类候选（如元伦理学 R07、道德实在论 R11 若涉及行动者理由）在"道德理由与行动理由"处相邻；与任何未来心灵哲学、自由意志候选互为边界；与已立"社会学"条目在韦伯行动理论上互设区分。
