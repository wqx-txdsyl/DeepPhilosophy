# R11 研究备忘录：道德实在论（Moral Realism）

> 任务：次轮候选研究（P2-research-only，coverage: mentions-only）。只研究，不建正式条目。
> 日期：2026-10-04。工作仓库：zcode-school-content worktree。边界要求：候选元伦理学立场；不可直接套用站内一般实在论总览；注意自然主义/非自然主义实在论内部差异。

## 1. 候选概述

道德实在论（Moral Realism）是元伦理学（metaethics）内部关于道德本体问题的核心立场之一，而非一个学派或运动。按 Sayre-McCord 在斯坦福哲学百科（SEP）《Moral Realism》条目中的界定，它包含两层最小主张：（一）道德命题确实旨在报告事实，其真假取决于事实是否如其所称；（二）至少某些道德命题实际为真。条目特别强调，常见的附加承诺——道德事实"独立于人类思想与实践"或以某种方式"客观"——是部分版本才有的**额外承诺**，不属于最起码的界定。这个"最小定义优先"的要点对本条目至关重要：若把定义直接建立在"客观道德事实"上，会把最小实在论与强实在论（robust realism）混为一谈，也会误伤极简真理论（minimalism about truth）下"廉价的真"带来的边界模糊。

其实质对立面构成一条清晰的立场谱系。SEP《Moral Anti-Realism》（Joyce 撰）把道德反实在论（moral anti-realism）明确为三个论题的析取：**非认知主义**（noncognitivism：道德判断不以求真为务——艾耶尔 A. J. Ayer 的情感主义、黑尔 R. M. Hare 的规定主义、布莱克本 Simon Blackburn 的准实在论、吉伯德 Allan Gibbard 的规范表达主义）、**错误论**（error theory：道德判断以求真为务但系统性失败，因为世界上没有使之为真的"材料"——麦凯 J. L. Mackie 1977，以及 Joyce、Olson 等当代继承者）、**非客观主义**（non-objectivism：道德事实存在但不客观，含建构主义 constructivism 与理想观察者论等）。由此，道德实在论的内部结构与外部边界都可精确勾画。

内部差异是本候选的第二个关键面（任务边界要求特别提示）。SEP《Moral Realism》§3 区分两条主线：**自然主义实在论**（naturalist moral realism）主张道德事实即自然事实或至少与科学图景相容，代表为博伊德（Richard Boyd, 1988）、布林克（David Brink, 1989）、雷尔顿（Peter Railton, 1986）的"康奈尔实在论"路线（该名称由 Sayre-McCord 命名，IEP 明言），外加 Jackson、Finlay 的语义分析还原路线与富特（Philippa Foot）、赫斯特豪斯（Rosalind Hursthouse）的新亚里士多德主义自然主义；**非自然主义实在论**（non-naturalist moral realism）承认道德事实不是自然事实，代表为 Shafer-Landau（2002）、帕菲特（Derek Parfit, 2011）、Enoch（2011）、Scanlon（2014），其思想渊源常被追溯到摩尔（G. E. Moore）对"自然主义谬误"的拒斥。两条路线共享上述最小定义，却在道德属性的本体地位、认识通路与"科学是否是万物的尺度"上针锋相对——站内若只写一张词卡会完全抹平这一差异。

主要争论构成条目的论证史骨架：麦凯的**怪异性论证**（argument from queerness：客观价值要求"内在于世界的行动规则"之类形而上学怪异物）、Harman 的**解释力挑战**（道德属性在最佳解释中无所作为）与 Sturgeon 的道德解释回应（希特勒的道德败坏解释其行为）、**演化揭穿论证**（evolutionary debunking：Joyce 2001、Street 2006 的达尔文两难，回应见 Enoch、Clarke-Doane、Vavova）、历史最悠久的**道德分歧论证**，以及 Moore 开放问题论证、Horgan & Timmons 的道德孪生地球对自然主义还原的打击等。另需记录 Joyce 在《Moral Anti-Realism》§4 的谨慎结语：随着极简真理论扩散（Dreier 的"creeping minimalism"），传统实在论/反实在论论辩的术语本身可能瓦解——这提示条目应以谱系地图而非站队宣言的形态写作。

## 2. 已有覆盖定位

任务 JSON evidence：`exactTopLevelEntries`/`exactBranches`/`relatedBranches` 均为空（站内无任何独立的道德实在论条目或分支），仅两处 mentions 级提及。经实际 grep 核读两个文件确认：

- **伦理学包**（`app/public/schools/data/school_伦理学.json`）：辞海区已有四张相邻术语卡——"道德实在论"（"主张道德事实和道德属性独立于人类信念而客观存在，道德判断可以有真假值，与道德反实在论相对"，来源标布林克《道德实在论与伦理学基础》）、"道德反实在论"（标艾耶尔）、"元伦理学"（标摩尔）、"情感主义"（标斯蒂文森）；timeline 记摩尔 1903《伦理学原理》"开创元伦理学领域"与艾耶尔 1936；quotes[15] 为艾耶尔情感主义释义。
- **实在论包**（`app/public/schools/data/school_实在论.json`）：词卡"道德实在论"定位为"实在论在伦理学中的延伸"，正文提及麦基（麦凯）错误理论与"'道德判断有真值，并且有些道德判断是真的'的中立表述"。

**判断**：两处覆盖都是单张词卡级（各约 60–100 字），且视角不一——实在论包从"一般实在论家族"外侧把道德实在论当作伦理学延伸，伦理学包则给出标准元伦理学表述。二者互不引用，反实在论三分谱系（非认知主义/错误论/非客观主义）、自然主义/非自然主义内部差异、全部论证史（怪异性、解释力、演化揭穿、孪生地球）在站内均缺席。现有材料只够充当新建条目的关联锚点，远不足以承载该立场；也不存在可"并入"的已有内容包。

## 3. 范围建议（若立项）

**建议类型：position（立场条目）**，作为 R07 元伦理学包的子条目（分支）挂接，见第 5 节对安排的评估。

**应覆盖**：

1. 最小定义（求真抱负 + 部分为真）与附加承诺（mind-independence、客观性）的区分——条目开篇即立此标准，避免把最小实在论与强实在论混同；
2. 内部两大路线分节：自然主义实在论（康奈尔实在论：Boyd/Brink/Railton/Sturgeon；语义还原：Jackson/Finlay；新亚里士多德主义：Foot/Hursthouse）与非自然主义实在论（摩尔渊源、Shafer-Landau/Parfit/Enoch/Scanlon），并交代两路线在认识论与"科学图景兼容性"上的分歧；
3. 对立谱系简表：非认知主义—规定主义—准实在论—错误论—非客观主义/建构主义，各配一人一书（艾耶尔、黑尔、布莱克本、麦凯、罗尔斯/科斯嘉德），细节留给 R07 或未来反实在论子条目；
4. 论证史精选：怪异性论证及其自败反驳、Harman–Sturgeon 解释力之争、演化揭穿与 companions-in-guilt 回应、道德分歧论证、道德孪生地球（针对自然主义还原）；
5. 极简真理论带来的边界松动（准实在论是否塌缩回实在论、"creeping minimalism"）作为收尾的当代议题。

**不应覆盖**：

- 元伦理学领域总览本身（四大问题域、Frege-Geach 问题、动机内在/外在主义等——归属 R07）；
- 一阶规范伦理学（功利主义、义务论、美德伦理学——站内已有独立包）；
- 一般实在论总览（科学实在论、数学实在论、指称实在论——属实在论包谱系，任务明确禁止套用）；
- 道德相对主义作为独立立场展开（与反实在论相关但不同：SEP《Moral Anti-Realism》§1 明确提醒不要把反实在论混同于道德相对主义/道德怀疑论/道德自然主义）；
- 表达主义/准实在论的全幅细节（可留作未来子条目）。

**与相邻条目的边界辨析**：

- **与 R07 元伦理学（父领域）**：道德实在论是元伦理学内部本体之争的一极，不是元伦理学的同义词。IEP 的《Metaethics》条目即把"Moral Realisms"作为其第 4a 节；SEP 两条目同属 metaethics 条目群。R07 立项后在"道德本体"节以小结概述实在论并指向 R11；R11 反向挂接父领域，不自建领域性内容。
- **与实在论包（站内 `school_实在论.json`）**：保留交叉关联而非收编。站内词卡把道德实在论定位为"实在论在伦理学中的延伸"，这个家族相似定位可作导览性关联，但新条目内容必须按元伦理学框架组织（最小定义 → 内部两路线 → 对立谱系），不得从一般实在论总览（柏拉图式理念、数学对象等）平移论证结构——两个领域面对的问题（道德规范性 vs. 指称/存在模态）并不相同。
- **与道德反实在论**：R11 条目内以"对立谱系简表"带过，不建独立包；若未来反实在论独立立项，再拆分。

## 4. 来源

1. **Sayre-McCord, Geoff, "Moral Realism", Stanford Encyclopedia of Philosophy**
   URL: https://plato.stanford.edu/entries/moral-realism/
   访问日期：2026-10-04。
   支持：两层最小定义与"附加承诺"之分（导言）；反对者二分（非认知主义否认事实性抱负、错误论承认抱负否认有真）；自然主义/非自然主义内部划分及全部代表人物归属（§3：Boyd/Brink/Railton/Jackson/Finlay/Foot/Hursthouse；Shafer-Landau/Parfit/Enoch/Scanlon）；道德分歧（§1）、解释力挑战与 Sturgeon 回应（§2）、演化揭穿及回应（§2）、怪异性论证及其自败反驳（§4）、极简真理论与准实在论塌缩问题（§6）。作者 Geoff Sayre-McCord，2005-10-03 首发，substantive revision 2026-07-31。
2. **Joyce, Richard, "Moral Anti-Realism", Stanford Encyclopedia of Philosophy**
   URL: https://plato.stanford.edu/entries/moral-anti-realism/
   访问日期：2026-10-04。
   支持：反实在论三论题析取结构（非认知主义/错误论/非客观主义，§1）；"不要把反实在论混同于道德怀疑论/相对主义/自然主义"的辨析提醒（§1）；代表人物谱（Ayer/Carnap/Hare/Stevenson/Blackburn/Gibbard/Mackie/Joyce/Kalderon/Firth/Rawls/Street，§3.1–3.3）；举证责任之争与揭穿论证（§2）；Frege-Geach 问题与塌缩异议（§3.1）；结语"传统实在论/反实在论论辩可能瓦解"（§4）。作者 Richard Joyce，2021 年修订版。
3. **"Metaethics", Internet Encyclopedia of Philosophy（IEP）**
   URL: https://iep.utm.edu/metaethi/
   访问日期：2026-10-04。
   支持：元伦理学为二阶（second-order）理论、与一阶规范理论的划界（引言）；"Moral Realisms"作为该条目第 4a 节的**领域内立场**结构——这是 R07/R11 父子安排的直接结构依据；康奈尔实在论（"Cornell Realism / New Wave Moral Realism"名称由 Sayre-McCord 命名；Boyd 的稳态簇、Sturgeon、Brink、Railton）与非自然主义一系（Moore、Ross、Shafer-Landau）的内部划分（§4a）；Horgan & Timmons 道德孪生地球、Blackburn 借随附性（supervenience）的质疑（§4a）；动机之争与 Mackie"形而上学怪异性"（§5a）、Harman–Sturgeon 解释力之争（§6b）。

三来源互不转抄：SEP《Moral Realism》与 SEP《Moral Anti-Realism》为不同作者独立撰写（且立场互为论敌两侧），IEP 为另一机构独立条目；三者在定义与人物归属上相互印证而无字面依赖。站内两个 JSON 文件与任务 JSON 为本地核读（grep 原文摘录），见 evidence.json 对应条目。

## 5. 立项判断

**结论：新建（position 立场条目，作为 R07 元伦理学的子条目跟进；若 R07 最终不立项，则 R11 降级为暂缓，不单独抢建）。**

对另一会话所提"R07 先行、R11 作为其下 position 子条目"安排的**独立评估：该安排成立**，依据有三：（一）领域—立场关系有权威结构背书——IEP 把"Moral Realisms"直接作为其 Metaethics 条目的一节，SEP 两词条同属 metaethics 条目群，可见学科自身就把道德实在论组织为元伦理学内部的立场而非平级领域；（二）任务自身的边界要求反向印证——"不可直接套用站内一般实在论总览"意味着 R11 若脱离元伦理学领域地图单独成条，最省事（也最错误）的写法恰是从一般实在论平移，只有先有 R07 的领域坐标（语义轴：认知/非认知；本体轴：实在/反实在），实在论的"实在"一侧才讲得清；（三）规模适配——道德实在论的论证史（第 1 节所列五组争论）塞进 R07 会撑爆领域总览，独立成 position 条目规模正好。

选"新建"而非其余三项的理由：**不并入已有包**——站内不存在元伦理学或道德哲学立场包，两处词卡各约百字且视角不一（第 2 节），没有可承接的宿主，硬塞进实在论包会把元伦理学框架换成一般实在论框架，正犯任务禁止的错误；**不只加关联**——两处提及均为词卡级，核心谱系与论证史全站缺席，仅加关联解决不了覆盖缺口；**不暂缓**——材料充分（三个独立权威条目核读到位）、边界清晰、与 R07 的关系可操作。

执行顺序建议：R07 先行或同批立项；R07 的"道德本体"节为实在论留小结与指向，R11 建成后反向挂接父领域，并与伦理学包（元伦理学/道德反实在论/情感主义词卡）、实在论包（"道德实在论"词卡）做导览性互链。

## 6. 证据限度与分歧

- **译法**："道德实在论/道德反实在论"为通行译名，站内词卡与本次三则英文来源的对应无歧义。"error theory"通译"错误论"或"错误理论"（站内实在论包词卡用"错误理论"，伦理学语境文献亦作"错误论"——建条目时站内两包宜统一，本次不改动）。"quasi-realism"通译"准实在论"，"non-objectivism"为 Joyce 条目的特意标签（他说明不用"主观主义"因其已被固定用于"报告自己态度"的理论），中文尚无统一译名，暂译"非客观主义"。"Cornell realism"通译"康奈尔实在论"。
- **摩尔归属的两源分歧（须在条目中谨慎处理）**：IEP《Metaethics》§4a 把 Moore 明确列为非自然主义道德实在论代表；SEP《Moral Realism》条目则主要把 Moore 作为开放问题论证的提出者讨论，其非自然主义方向代表名单（Shafer-Landau/Parfit/Enoch/Scanlon）不含 Moore，仅说该路线"源于对 Moore 的接纳"。两说并不矛盾（摩尔确持道德属性非自然存在之见），但侧重点不同；条目宜写"通常被追溯为非自然主义实在论的思想渊源"而非简单断言"非自然主义实在论者"。
- **"最小/强实在论"术语不统一**：SEP《Moral Anti-Realism》以 Rosen 1994 区分 minimal/robust，SEP《Moral Realism》未系统采用这对标签而是围绕极简真理论展开同型问题；R11 条目采用最小定义开篇的写法在两源均有依据，但"最小/强"这对词本身属一家之框架，宜作辅助而非骨架。
- **学界的松动迹象**：Joyce 在《Moral Anti-Realism》§4 明言传统实在论/反实在论论辩的术语"可能瓦解"（极简真理论使双方都能说"道德判断为真"）；这提示条目不应写成非此即彼的站队史，该判断为单源（Joyce），但与 SEP《Moral Realism》§6 的 creeping minimalism 讨论（Dreier 2005）方向一致，交叉印证可用。
- **站内译名不一致待统一**：实在论包词卡作"麦基（麦凯）"，伦理学包未见此人；R11 立项时若写麦凯（J. L. Mackie），建议统一用"麦凯"并在实在论包词卡处仅做导览互链（本次未改动任何站内文件）。
- **访问受阻记录**：IEP 的 moral realism 独立条目 URL（iep.utm.edu/mor-real/）返回 404，未能核读，未引用；Britannica 未尝试（三来源已达标且互证充分）。
