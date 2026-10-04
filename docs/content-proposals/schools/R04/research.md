# R04 数学哲学（Philosophy of Mathematics）——次轮候选研究备忘录

日期：2026-10-04 ｜ 任务组：次轮候选研究（P2-research-only，只研究不建正式条目）

## 1. 候选概述

数学哲学（Philosophy of Mathematics，检索别名含"数学基础"）是一个以数学本身为反思对象的**哲学分支/领域（field）**，而非数学史。它研究三类独特问题：(1) **本体论**——数学对象（数、集合、函数、结构）是否存在、以何种方式存在？它们不在时空中、无因果效力，如何"存在"；(2) **认识论**——数学知识为何可能？为何比经验科学知识更确定？我们如何"知道"抽象对象的事实；(3) **证明与公理的地位**——证明是否给作物级的确定性、公理是否有确定的真假。SEP 总论条目指出，数学对象"显然不在时空之中"、数学靠演绎而非归纳推进、数学知识似乎比科学理论更可靠，这三点使数学对哲学构成"相当独特的难题"（Horsten, SEP）。

围绕这些问题的代表性立场谱系：**柏拉图主义**（Platonism，哥德尔诉诸准感知的数学直觉、Quine–Putnam 不可或缺性论证）；**逻辑主义**（Logicism，弗雷格/罗素试图"把数学还原为逻辑"）；**形式主义**（Formalism，希尔伯特把高级数学视为证明算术命题的工具性"形式游戏"，即希尔伯特纲领）；**直觉主义**（Intuitionism，布劳威尔认为数学是"心智的创造"，拒 completed infinity 与排中律，海廷给出形式化）；此外还有**结构主义**（Structuralism，Benacerraf/Resnik/Shapiro，数是结构中的"空位"）、**直谓主义**（Predicativism，庞加莱/外尔/Feferman）与**虚构主义等唯名论方案**（Field/Hellman/Yablo）。20 世纪的关键争论事件：1902 罗素悖论击溃弗雷格第五公理、1931 哥德尔不完备定理"导致希尔伯特纲领失败"、Benacerraf 1965（数不可无歧义地还原为集合）与 1973（因果知识论下柏拉图主义者的认知可靠性无法解释）双重挑战、连续统假设独立性、计算机辅助证明是否仍是"纯先验"证明。

按 PhilPapers 2009 初轮调查（全体受访者），在"抽象对象：柏拉图主义还是唯名论"问题上，接受或倾向柏拉图主义约 39.3%、唯名论约 37.7%，说明这些基础立场在当代职业哲学界仍是活的、近乎势均力敌的争论——不是已结案的历史话题。

## 2. 已有覆盖定位

任务 JSON 的 evidence 显示 R04 为 **mentions-only** 覆盖，且检索面很薄：

- **exactTopLevelEntries / exactBranches / relatedBranches：全部为空**——站内没有任何顶层条目、分支或关联分支承载"数学哲学"。
- **mentionFiles 仅 1 处**：`app/public/schools/data/school_北欧哲学.json`，哲学家列表中「托尔·尼尔森，sub：逻辑哲学/数学哲学，1916-2008，非经典逻辑、可能性理论」——只是给北欧哲学家贴的领域标签，无任何立场/争论内容。

复核（grep 全站 schools/data 与 content-proposals）确认"数学哲学"字样仅此一处。相关邻域的承载情况：

- **W01 柏拉图主义**（tradition-overview）：任务 JSON 明确要求"现代数学柏拉图主义**另作关联**"——即 W01 的设计本身就把数学柏拉图主义排除在外并预留了关联接口，但该接口当前没有落点。
- **F03 逻辑与逻辑哲学**（field，related-branches-only）：覆盖逻辑系统与逻辑哲学，其任务边界是"区分形式逻辑、有效性及逻辑哲学"——数学哲学不是它的子题。

**结论：现有材料完全不足以承载本候选**——正文提及量为 1 个标签级提及，且预留关联的 W01 无处可挂。

## 3. 范围建议（若立项）

- **建议类型：field（哲学分支/领域）**，名"数学哲学"（Philosophy of Mathematics）。
- **应覆盖**：三大核心问题（数学对象的本体论、数学知识的认识论、证明与公理的地位）；主要立场各设一节——柏拉图主义（三论题：存在/抽象性/独立性，哥德尔、Quine–Putnam 不可或缺性）、逻辑主义（弗雷格—罗素—新逻辑主义）、形式主义（希尔伯特纲领及其被不完备定理挫败）、直觉主义/构造主义（布劳威尔—海廷，拒排中律与实无穷）、结构主义（Benacerraf 1965 → Shapiro *ante rem*）、唯名论/虚构主义与 Benacerraf 1973 认识论挑战；基础危机诸事件（罗素悖论、哥德尔、CH 独立性）只作为立场交锋的**背景**简述。
- **不应覆盖**：数学史本身（数学家与定理的编年叙事）；集合论/证明论的技术细节；逻辑学系统本身；柏拉图理念论与古代学园；科学哲学的一般问题（可与科学哲学条目互链）。
- **边界辨析**：
  - **与 W01 柏拉图主义**：古代柏拉图的形式论归 W01；现代数学柏拉图主义是数学哲学内部的一个立场（Linnebo, SEP 明言其"独立于原始历史灵感被定义和争论"），作为 R04 内部一节 + 与 W01 双向关联。这正好兑现 W01 任务 JSON 预留的"另作关联"。
  - **与 F03 逻辑与逻辑哲学**：逻辑研究有效推理的形式系统与逻辑常项的地位；数学哲学借用逻辑成果（哥德尔定理、二阶逻辑语义学）但问题是本体论/认识论的。直觉主义对排中律的拒斥两边都涉及——归 R04 讲其数学基础动机，F03 讲逻辑系统性质，交叉引用即可。
  - **与站内"结构主义"相关候选**（若有）：科学哲学中的结构实在论与数学结构主义是不同论题，条目中需显式区分以免合并错误。

## 4. 来源

1. **Horsten, Leon, "Philosophy of Mathematics", Stanford Encyclopedia of Philosophy**
   https://plato.stanford.edu/entries/philosophy-mathematics/ （访问日期 2026-10-04，WebFetch 实读全文摘要）
   支持：领域的核心问题界定（本体论+认识论+证明地位）；逻辑主义/形式主义/直觉主义/柏拉图主义/结构主义的代表人物归属；Benacerraf 1965 与 1973 两个挑战的区分；罗素悖论 1902、哥德尔 1931 挫败希尔伯特纲领、Quine 不可或缺性。
2. **Linnebo, Øystein, "Platonism in the Philosophy of Mathematics", Stanford Encyclopedia of Philosophy**
   https://plato.stanford.edu/entries/platonism-mathematics/ （访问日期 2026-10-04，WebFetch 实读）
   支持：数学柏拉图主义三论题的标准表述（存在/抽象性/独立性）；Fregean 论证与不可或缺性论证；Benacerraf/Field 反对意见；"现代 platonism 独立于柏拉图理念论被定义与争论"——直接支撑与 W01 的边界判断。
3. **Iemhoff, Rosalie, "Intuitionism in the Philosophy of Mathematics", Stanford Encyclopedia of Philosophy**
   https://plato.stanford.edu/entries/intuitionism/ （访问日期 2026-10-04，WebFetch 实读）
   支持：布劳威尔"数学是心智的创造"、拒实无穷与排中律、海廷 BHK 解释；直觉主义"既不预设我们之外的数学实在，也不是按固定规则玩符号"——即它同时区别于柏拉图主义与形式主义；Grundlagenstreit 与希尔伯特的冲突。
4. **PhilPapers Surveys, Preliminary Survey results**
   https://philpapers.org/surveys/results.pl （访问日期 2026-10-04，WebFetch 实读）
   支持："抽象对象：柏拉图主义还是唯名论"全体受访者 39.3% vs 37.7%（931 人）——佐证立场之争在当代的活跃度。

来源独立性说明：三个 SEP 条目为不同作者分别撰写的独立条目（Horsten / Linnebo / Iemhoff），非互相转抄；PhilPapers 为独立调查数据。Britannica "philosophy of mathematics" 与 IEP 均尝试访问失败（详见第 6 节）。

## 5. 立项判断

**结论：新建（field 类正式候选，进入下轮正式条目队列）。**

理由：(1) **覆盖真空确凿**——evidence 三类精确匹配全空，仅 1 处标签级提及，任何现有包都无法承载；(2) **有明确挂点需求**——W01 柏拉图主义的任务定义主动把现代数学柏拉图主义"另作关联"，R04 是该关联唯一的自然落点，不建则 W01 的关联接口悬空；(3) **领域独立且结构成熟**——核心问题、立场谱系、标志性论证（Benacerraf 挑战、不可或缺性）边界清晰，与 F03 逻辑哲学可干净切分，不会造成包间重叠；(4) **当代相关性高**——PhilPapers 数据显示基础立场之争在职业哲学界近乎五五开，非纯历史题材。次轮只做研究备忘录，正式 packet 待下轮授权。

## 6. 证据限度与分歧

- **术语译法**："formalism" 译"形式主义"，与伦理学形式主义、俄国文学形式主义同形，条目需以全称"数学中的形式主义（Formalism in the Philosophy of Mathematics）"消歧；"structuralism" 译"结构主义"，须与语言学/人类学结构主义及科学哲学"结构实在论"显式区分；"intuitionism" 通行译"直觉主义"，另需注明与康德"直观（Anschauung/intuition）"非同义词。
- **归属争议**：Quine 是否算"数学柏拉图主义者"有细微分歧——Linnebo（SEP）指出 Quine 接受柏拉图主义但拒绝额外的认识论与模态论题；条目行文应写"Quine–Putnam 不可或缺性论证"而非径称 Quine 为柏拉图主义者。直觉主义为何可取（布劳威尔的心智构造 vs Dummett 的意义理论路线）是内部争论；维特根斯坦受布劳威尔 1928 维也纳讲演影响的程度"有争议"（Iemhoff, SEP）。
- **年代与表述**：Benacerraf 1965（"What Numbers Could Not Be"，同一性/还原问题）与 1973（"Mathematical Truth"，认识论挑战）是两篇不同文献的两个不同挑战，撰写时不可混为一谈。
- **数据限度**：PhilPapers 引用的百分比来自 **2009 初轮调查、全体受访者口径**（页面快照未见分群体细分，亦非 2020 Survey 结果页）；且该问题问的是"抽象对象"一般而非专指数学对象——引用时应标注这两点，不得写作"数学哲学家 39% 持柏拉图主义"。
- **来源访问受阻**：Britannica "Philosophy of Mathematics" 返回 403（改用浏览器 UA 仍 403）；IEP 未检索到数学哲学总论条目（候选 slug `phil-math/`、`mathphi/` 均 404，M 索引无相关条目）。本备忘录的实读来源为 3 个 SEP 独立条目 + PhilPapers 调查，与任务 JSON 指定的 researchLeadIds（philpapers、stanford-research）一致；若正式立项，建议下轮补核 Routledge Encyclopedia of Philosophy（REP）与大学课程讲义类来源以扩宽域。
- **站内人名核对**：北欧哲学 JSON 中"托尔·尼尔森"（1916-2008，非经典逻辑、可能性理论）的原名与生平，本次未做外部核实，正式立项时若该人物入正文须先核实（宜走 R16/R17 类先核实任务）。
