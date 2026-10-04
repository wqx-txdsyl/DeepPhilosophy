# R10 研究备忘录：无政府主义（Anarchism / 安那其主义）

任务：次轮候选研究（P2-research-only），只研究不建正式条目。检索别名：无政府主义 / Anarchism / 安那其主义。日期：2026-10-04。

## 1. 候选概述

无政府主义（Anarchism，又译安那其主义）是一种政治理论传统兼历史运动。斯坦福哲学百科（SEP）安德鲁·菲亚拉（Andrew Fiala）条目将其定义为"a political theory that is skeptical of the justification of authority and power"（对权威与权力之正当性持怀疑论的政治理论），其道德根基是"免于支配的自由"（freedom from domination），并持有"平等、共同体与非强制共识构建"（equality, community, and non-coercive consensus building）的正面理想。词源上来自希腊语 archē（兼有"本原、根基与统治权力"多义），故 anarchy 可解作"无人统治/非统治"（rule by no one or non-rule）。其核心否定命题是：集中的、垄断性的强制权力（典型即国家）不具正当性——SEP §1.1 引巴枯宁"没有奴役就无所谓国家"一语为典型表述。

核心问题与代表性争论有四层。其一，国家权威的正当性与政治义务：国家是否道德上可证成、公民是否有服从义务，这是哲学无政府主义（philosophical anarchism）的战场——西蒙斯（A. John Simmons）式的哲学无政府主义者"并不认为国家不合法就蕴含了反对或消灭国家的强烈道德义务"，而沃尔夫（Robert Paul Wolff）的先验论证则断言"法律上有正当性的国家这一概念是空洞的"（SEP §2–2.2）。其二，国家之外的秩序是否可能：从蒲鲁东互助主义、巴枯宁集体主义到克鲁泡特金无政府共产主义，给出的社会组织方案各不相同（SEP §2.4）。其三，手段之争：改良性的直接行动、工团组织还是革命，以及著名的暴力污名问题——克鲁泡特金在 1911 年《大英百科》条目中明确反驳"暴力是无政府主义的实质"这一公众印象，指出暴力只是镇压下行动受阻的产物，"哲学无政府主义者会否认这种关联"。其四，内部的两极张力：社会主义方向（克鲁泡特金"一切人为了一切人"）与个人主义方向（施蒂纳"每个国家都是专制"）构成传统内部的轴线（SEP §2.4），无政府资本主义（罗特巴德）能否归入此传统至今有争议。

内部差异（本候选条目的重点）至少包括五支加一个运动形态：蒲鲁东（Pierre-Joseph Proudhon）的互助主义（mutualism，1840 年《什么是所有权》首次自名"无政府主义"）；巴枯宁（Mikhail Bakunin）的集体主义无政府主义与第一国际联邦派；克鲁泡特金（Peter Kropotkin）的无政府共产主义（anarcho-communism，其自述"共产主义与无政府是彼此成全的演进两极"）；施蒂纳（Max Stirner）、沃伦、斯普纳、塔克（Benjamin R. Tucker，《自由》杂志）一线的个人无政府主义（individualist anarchism）；托尔斯泰（Leo Tolstoy）的基督教无政府主义（Christian anarchism）；以及作为运动形态的无政府工团主义（anarcho-syndicalism）——克鲁泡特金记载部分无政府主义者"加入了所谓工团主义运动"（joined the so-called Syndicalist movement），戈德曼（Emma Goldman）的实践与论辩亦与此相连（SEP §3.1 触及）。当代延伸还包括生态无政府主义（布克钦 Bookchin）、无政府女性主义与后无政府主义（SEP §1.4–1.5）。

## 2. 已有覆盖定位

按任务 JSON evidence 并实际核读两份文件：

- **exactTopLevelEntries / exactBranches / relatedBranches 均为空数组**：全库没有任何顶层条目或分支承载"无政府主义"这一政治传统本身。
- **excludedLexicalMatches（词形排除，共 1 条）**：科学哲学包 `app/public/schools/data/school_科学哲学.json` 的 `subSchools[4]` "无政府主义认识论"。实测确认该文件中全部"无政府主义"字样均属费耶阿本德语境：`overview`（"费耶阿本德以'方法论无政府主义'将库恩的洞见推到极端……'怎么都行'"）、`thinkers[2].sub`（"方法论无政府主义"）、`timeline[8].detail`（"提出无政府主义认识论"）、`conclusion`、`works[2].desc`、`cihai[5]/[24]`。全部是科学方法论立场，不是政治传统，不计为已有分支。
- **mentionFiles（提及，共 2 处）**：(a) 科学哲学包如上，纯词形提及；(b) 政治哲学包 `app/public/schools/data/school_政治哲学.json` 实测仅有两类提及——诺齐克《无政府、国家与乌托邦》（`overview`、`thinkers[1].works[0]`、`works[1].title`、`cihai[22].source`；且这是以最小国家立场对无政府主义起点的"反驳"，不是无政府主义本身），以及阿伦特语录 `quotes[16]`"无政府不是自由，而是任意"（对无政府主义的回应，捍卫共和自由传统）。

**判断**：政治哲学包的 `subSchools` 实为五项（自由主义平等主义、自由至上主义、社群主义、审议民主理论、多元主义与价值冲突论），六位思想家（罗尔斯、诺齐克、阿伦特、伯林、哈贝马斯、桑德尔）均非无政府主义者；科学哲学包的"无政府主义认识论"是另一种立场（见第 3 节边界）。即：现有材料全部是 mentions-only，且多为"对无政府主义的反驳或回应"，不足以承载本条目。缺了无政府主义，政治理论谱系也不完整——它是与自由主义、社会主义并列的十九世纪以来三大政治思潮之一，主流学术百科（SEP、大英百科）均设独立条目。

## 3. 范围建议（若立项）

**建议类型**：`movement`（兼有 `tradition-overview` 性质——无政府主义既是政治理论又是社会运动，建议以运动/传统为主轴、理论内核为骨架）。

**应覆盖**：
- 定义与核心问题：对权威正当性的怀疑论；archē 词源；否定命题（国家/垄断强制权力不合法）与正面理想（平等、共同体、非强制共识）。
- 奠基史：戈德温（Godwin）《政治正义论》（1793）首次系统阐发（克鲁泡特金称其"first to formulate"）；蒲鲁东 1840 年《什么是所有权》首次自名（"first to use… the name of Anarchy"）。
- 五支内部差异：互助主义（蒲鲁东）/集体主义（巴枯宁，第一国际联邦派、与马克思的冲突）/无政府共产主义（克鲁泡特金）/个人无政府主义（施蒂纳—塔克）/基督教无政府主义（托尔斯泰），加无政府工团主义（戈德曼、劳工组织实践）。
- 哲学无政府主义 vs 政治无政府主义的分界（西蒙斯的弱承诺立场、沃尔夫的先验论证、乔姆斯基的举证责任论证——SEP §2）。
- 暴力污名与手段之争（克鲁泡特金 1911 年的公开反驳是很好的原典材料）。
- 当代延伸简述：生态（布克钦）、无政府女性主义、后无政府主义。

**不应覆盖**：
- 费耶阿本德的（认识论/方法论）无政府主义——归科学哲学包，本条目只设交叉关联。
- 无政府资本主义的内部归属争论写成定论——应作为"分歧"呈现。
- 暗杀事件编年、中国安那其主义运动史等史事细节——仅在"污名化"问题上点到即止。

**边界辨析（三条）**：
1. **与科学哲学包"无政府主义认识论"（费耶阿本德）**：SEP 无政府主义条目把费耶阿本德放在 §1.3 "Theoretical Anarchism" 下，其名言"Science is an essentially anarchic enterprise"是关于科学方法的主张；SEP 费耶阿本德条目确认该词指其《反对方法》（副标题即"Outline of an Anarchist Theory of Knowledge"）中的方法论立场，通篇从未把他归入有组织的政治无政府主义运动（§5.2 只是说他把认识论立场引申出政治—文化含义）。两包互设关联即可，绝不能因词形相近互相替代——这正是任务 JSON 明确排除的误归类。
2. **与政治哲学包诺齐克/自由至上主义**：诺齐克《无政府、国家与乌托邦》（1974）从无政府状态出发论证最小国家的正当性，是对无政府主义的回应而非其内部立场；罗特巴德式的无政府资本主义与"自由至上主义"的亲缘关系要与此区分。政治哲学包已有的阿伦特语录恰好可作反向关联素材。
3. **哲学无政府主义 vs 政治无政府主义（本条目内部边界）**：沃尔夫式的哲学无政府主义（仅否认国家正当性、不含行动纲领）与作为运动的政治无政府主义须在条目内明确分层，避免与政治哲学包关于政治义务的讨论（罗尔斯等）混淆。

**归属建议**：作为政治哲学簇下的新增独立学派条目，与政治哲学、科学哲学两包互设关联。

## 4. 来源

1. **Fiala, Andrew, "Anarchism", Stanford Encyclopedia of Philosophy（斯坦福哲学百科）**，https://plato.stanford.edu/entries/anarchism/ ，访问日期 2026-10-04。实际核读：支持定义（"skeptical of the justification of authority and power"）、archē 词源与否定命题（§1.1）、宗教/理论/应用等分类（§1.2–1.6）、社会主义—个人主义轴线与互助主义、施蒂纳、罗特巴德"non-archism"（§2.4）、哲学/政治无政府主义之分与西蒙斯、沃尔夫、乔姆斯基引语（§2–2.2）、费耶阿本德定位（§1.3，"Science is an essentially anarchic enterprise"）、"toothless"批评（§4.5）。
2. **克鲁泡特金（Peter Kropotkin），"Anarchism"，《大英百科全书》第 11 版（1911），Wikisource 原文**，https://en.wikisource.org/wiki/1911_Encyclop%C3%A6dia_Britannica/Anarchism ，访问日期 2026-10-04。实际核读：开篇定义（"society is conceived without government……by free agreements"）、戈德温首创说（Political Justice 1793）、蒲鲁东 1840 首名与 Mutuellisme、巴枯宁集体主义与第一国际联邦派、无政府共产主义"chiefly"主导及"Communism and Anarchy are therefore two terms of evolution which complete each other"、施蒂纳"association of the egotists"与塔克《自由》、托尔斯泰"Christian-Anarchism"、部分无政府主义者"joined the so-called Syndicalist movement"、对暴力污名的公开反驳。此为当事人自撰原典（条目署名 P. A. K.），反映该传统自我理解，与 SEP 的当代学术综述互补，两者非转抄关系。
3. **"Paul Feyerabend", Stanford Encyclopedia of Philosophy**，https://plato.stanford.edu/entries/feyerabend/ ，访问日期 2026-10-04。实际核读：支持边界排除——《反对方法》副标题"Outline of an Anarchist Theory of Knowledge"、1970 年论文"endorses 'epistemological anarchism' and the slogan 'Anything goes!'"、§5.2 标题"The Political Consequences of Epistemological Anarchism"；条目将认识论无政府主义呈现为科学哲学立场，从未将其归入政治无政府主义运动。

（IEP 无独立 Anarchism 条目、Britannica 当代版反爬不可达、Pitzer Anarchy Archives 连接失败，均已在检索中实测，不影响来源数达标。）

## 5. 立项判断

**结论：新建。**

理由：(1) 任务 evidence 三类覆盖数组全空，实测两份 mentionFiles 均为词形提及或反驳性提及，零承载；(2) 科学哲学包"无政府主义认识论"是词形相近的不同立场（任务已明确排除），不能借它安放政治传统；(3) 无政府主义在主流学术百科中拥有独立条目、内部谱系丰富（五支 + 工团主义），规模与地位足以独立成条，且是政治理论谱系目前缺失的一块；(4) 建议类型 movement/tradition-overview，挂政治哲学簇，与政治哲学包（诺齐克、阿伦特）和科学哲学包（费耶阿本德认识论无政府主义）互设关联。

## 6. 证据限度与分歧

- **译名**：Anarchism 通译"无政府主义"，民国文献与部分学术史作"安那其主义"；anarchy 之 archē 兼有"本原/根基/统治"多义（SEP §1.1），"无政府"译名未能覆盖"非统治"义，条目宜交代词源。
- **起点归属之争**：克鲁泡特金 1911 称戈德温"first to formulate"其政治经济观念，又称蒲鲁东 1840"first to use the name"——"首个阐发者"与"首个自名者"是两个不同断言，写条目时应并列表述；宗教无政府主义脉络（SEP §1.2）还会把先声推得更早。本轮未核读戈德温原典，"first"表述引用克鲁泡特金原话并注明出处即可，不作独立断言。
- **无政府资本主义归属分歧**：SEP §2.4 记罗特巴德本人建议以"non-archism"称其立场；该流派是否属无政府主义在运动内部与学界均有争议，须以分歧呈现。
- **工团主义细节未充分核读**：SEP 条目未给 anarcho-syndicalism 设独立分类标题（仅在戈德曼 sabotage 讨论中触及 syndicalism），克鲁泡特金原文亦只有一句"joined the so-called Syndicalist movement"；CNT-FAI、西班牙内战等细节本轮无已核来源，写正式条目时须补核专门文献（此为本备忘录最大的证据缺口）。
- **第一国际分裂细节**：克鲁泡特金原文只及巴枯宁为"联邦派之主导精神"，1872 年海牙大会驱逐巴枯宁等具体史实本轮未核读，先不作断言。
- **原典的时代局限**：克鲁泡特金 1911 年文本是当事人自辩性综述，其"无政府共产主义为主流"的判断反映二十世纪初的自我理解，当代定评以 SEP 为准；两者在条目中应分层引用（原典引语 + 当代学术定位）。
- **政治争议材料的处理**：暴力问题（"行动宣传"、暗杀编年）是公众认知与运动自我辩护冲突最尖锐处；克鲁泡特金明确反驳"暴力是实质"说。条目应如实呈现"运动内部与外界对暴力手段的分歧"，既不沿用污名也不加美化。
- **费耶阿本德再强调**：他本人拒绝被归入任何固定"主义"，其"无政府主义"是方法论修辞上借用政治词汇；任何把 R10 条目与"无政府主义认识论"子项合并或互相引申的做法都应禁止。
