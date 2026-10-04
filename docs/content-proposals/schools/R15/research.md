# R15 康德主义 —— 次轮候选研究备忘录

日期：2026-10-04 ｜ 任务组：次轮候选研究（P2-research-only，coverage=mentions-only，只研究不建正式条目）
工作树：`/Users/sen/.zcode/worktrees/zcode-school-content`（主仓库 `/Users/sen/DeepPhilosophy` 未触碰）。本文档不写 packet.json，未获发布授权。

> 检索别名：康德主义 / Kantianism / 新康德主义 / Neo-Kantianism。

## 1. 候选概述

"康德主义"（Kantianism）不是单一学说，而是至少三个必须分开的层次，本候选只研究后两层、以第三层为核心：

- **（a）康德本人的批判哲学**：先验观念论、范畴、物自体（Ding an sich）等——站内已有独立人物条目（伊曼努尔·康德），不属本候选范围。
- **（b）早期后继接受与改造**（1786–1790 年代）：莱因霍尔德（Karl Leonhard Reinhold）《论康德哲学的书信》（Briefe über die Kantische Philosophie, 1786）普及康德并于 1787 年获耶拿专设康德哲学教席，随后以"表象能力"为第一原理的基础哲学（Elementarphilosophie）偏离康德；费希特（J. G. Fichte）1792 年《试评一切天启》曾被误当作康德所作，1794 年接掌耶拿教席，1799 年被康德公开决裂。这一层在哲学史上归属德国古典哲学，站内已由"德国古典哲学"包承载。
- **（c）狭义康德主义＝新康德主义（Neo-Kantianism）**：约 1865/1870 年至第一次世界大战期间德国占主导地位的哲学运动（SEP："Neo-Kantianism was the dominant philosophical movement in Germany from roughly 1870 until the First World War"），以"回到康德"（"Zurück zu Kant!"，利普曼 Otto Liebmann《康德与后继者》1865）为口号，在思辨形而上学与唯物主义/心理主义之间走"第三条道路"。

**核心问题与争论**：(1) 先天（das Apriori）的地位——是随科学发展而相对化（马堡派），还是普遍有效的规范（西南派）；(2) 先验方法（transzendentale Methode）能否摆脱康德固定不变的范畴表，把批判方案扩展到康德排除在科学之外的历史学；(3) 自然科学与历史科学的方法论分界——文德尔班的"立法的"（nomothetic）与"表意的"（idiographic）之分；(4) 价值在知识构成中的角色（西南派视哲学为价值论/有效性理论）；(5) 解释学立场之争——文德尔班名言"理解康德就是超越康德"（"Kant verstehen, heißt über ihn hinausgehen"），而那托普明言马堡学派内部"从未有过正统康德主义"（"Talk of an orthodox Kantianism within the Marburg School was never justified"）：两派都拒斥物自体学说（视之为"不自贯且多余"），都在"以康德命名"与"改造康德"之间工作。

**两大分支**：

- **马堡学派（Marburger Schule）**：柯亨（Hermann Cohen）、那托普（Paul Natorp）、卡西尔（Ernst Cassirer）。从"科学之事实"出发追问客观有效性的条件；泛逻辑主义（Panlogismus），彻底拒绝"被给予者"（the given）与直观/概念二分——"思维产生被认定为存在的东西"（"Thinking produces that which is held to be"，柯亨）。衍生态度：柯亨的伦理社会主义（ethischer Sozialismus）、社会理想主义与晚期"理性宗教"（犹太教作为理性宗教）；卡西尔《符号形式的哲学》（1923–29）以"符号形式"综合语言、神话与科学并回应相对论。
- **西南学派／巴登学派（Südwestdeutsche / Badische Schule）**：文德尔班（Wilhelm Windelband）、李凯尔特（Heinrich Rickert）、拉斯克（Emil Lask）。哲学是价值论/有效性理论，先天规范是目的论意义的；李凯尔特以"价值相关性"解释历史概念构成，反对把自然科学方法当作唯一思维规则；拉斯克的范畴理论与价值逻辑影响了韦伯（Max Weber）、卢卡奇（Georg Lukács）与海德格尔。边缘成员：费英格（Hans Vaihinger，《仿佛的哲学》"as-if"虚构主义）、狄尔泰（Verstehen 传统）等。

**影响与衰落**：其学生与受影响者横跨欧陆与分析两个传统——卡纳普（Carnap）、伽达默尔（Gadamer）、海德格尔（Heidegger）、赖欣巴哈（Reichenbach）皆出其门下；1929 年达沃斯之辩（卡西尔 vs 海德格尔）常被视为象征性转折；1918 年后因与旧秩序绑定而声誉剧变，1933 年纳粹上台后许多犹太裔、社会自由派成员流亡，制度记忆几近中断。20 世纪末以来出现研究复兴（Luft & Makkreel 编《Neo-Kantianism in Contemporary Philosophy》2010；Michael Friedman 等），并辐射出分析康德主义与当代康德式建构主义（柯斯嘉德 Korsgaard——IEP 将其列入"广义"用法）。IEP 结语概括其地位："人可以借着康德做哲学，或反着康德做哲学，但不能没有康德做哲学"（"one can philosophize with Kant, or against Kant; but one cannot philosophize without Kant"）。

## 2. 已有覆盖定位

任务 JSON evidence：`exactTopLevelEntries`、`exactBranches`、`relatedBranches` 均为空；coverage=mentions-only。mentionFiles 两处：

1. `app/public/schools/data/school_德国古典哲学.json`（matched "康德主义"）：人物列表中**莱因霍尔德**条目（sub="康德主义传播"，era="1757-1823"，works 含《论康德哲学的书信》《人类表象能力新论》）——即上述（b）层"早期接受"已由该包以成员条目方式承载。
2. `app/public/schools/data/school_西方马克思主义.json`（matched "康德主义""新康德主义"）：卢卡奇年表事件"早年受新康德主义和黑格尔哲学影响"——单向背景提及，无任何新康德主义解释性内容。方向上与 IEP"拉斯克影响卢卡奇"可互证。
3. 另查 `app/public/philosophers.json`：**伊曼努尔·康德**人物条目存在（school=德国古典哲学，rank 49.6，含《康德文集》《康德三大批判合集》等书目）——（a）层已有承载。

**判断**：现有材料完整覆盖了（a）康德本人与（b）早期接受两层，但（c）新康德主义运动本身（1865–1930s）在站内**零承载**——两处提及均为一句话级别的背景交代，无法支撑卢卡奇、韦伯、卡西尔等多次出场时的解释需求，不足以承载本候选。

## 3. 范围建议（若立项）

- **建议类型**：tradition-overview（传统概览）；**条目名建议直接用"新康德主义"**，检索别名并列 Kantianism / Neo-Kantianism；不建一个宽泛无差的"康德主义"大包（任务 scopeAndCautions 明确要求分层）。
- **应覆盖**：兴起背景（对思辨观念论与唯物主义的双重反动；术语史——"Neo-Kantianer"1862 年米歇莱特批评策勒时首见，利普曼 1865 使口号定型）；马堡/西南两派纲领、代表人物与分野；先天问题两派差异；伦理社会主义与社会科学影响（柯亨→德国社会民主党的伦理社会主义话语；拉斯克→韦伯、卢卡奇）；衰落（1918/1929/1933 三重节点）与 20 世纪末复兴；对分析哲学（卡纳普、Friedman）与当代康德式建构主义（柯斯嘉德，广义用法）的辐射。
- **不应覆盖**：康德本人学说细节（→人物条目）；黑格尔—费希特—谢林线（→德国古典哲学包，本条目只在导语处一笔带过"回到康德"是对观念论的反弹）；现象学自身发展（海德格尔、胡塞尔仅在"受其训练/反叛"处提及，如达沃斯之辩）；当代建构主义的正面展开（→ R07）。
- **与相邻条目的边界辨析**：
  - 与"德国古典哲学"包：以 1865 年"回到康德"口号为史期分界；莱因霍尔德、费希特留原地，新条目不重复、不收编。
  - 与 **R01 法哲学**：新康德主义法理论（施塔姆勒 Rudolf Stammler 的"正当法"学说、凯尔森 Hans Kelsen 纯粹法学的新康德主义根基）属 R01 素材，本条目只做交叉链接（本次两来源未逐段核实施塔姆勒/凯尔森细节，立项后须补查）。
  - 与 **R02 历史哲学**：文德尔班 nomothetic/idiographic、李凯尔特价值相关性是 R02 的直接素材，两处互引。
  - 与 **R07 元伦理学**：柯斯嘉德等康德式建构主义的正面讨论归 R07；本条目仅在"现代复兴"处提示。
  - 与 **R11 道德实在论**：建构主义 vs 实在论之争是 R07/R11 的战场，本条目不站队、不展开。

## 4. 来源

1. **Stanford Encyclopedia of Philosophy, "Neo-Kantianism"** — https://plato.stanford.edu/entries/neo-kantianism/ （访问 2026-10-04）。
   支持：1870–一战主导地位与"第三条道路"定位；马堡派（先验方法、泛逻辑主义、拒斥被给予者）与西南派（价值有效性、nomothetic/idiographic）纲领及两派互批；对物自体与双干（感性/知性）学说的拒斥；文德尔班英译名言；那托普反"正统康德主义"原句；先天问题两派差异；衰落（1918 后与旧秩序绑定、1933 制度记忆中断）；学生名单（Carnap、Gadamer、Heidegger、Reichenbach）。
2. **Internet Encyclopedia of Philosophy, "Neo-Kantianism"（Anthony K. Jensen，Providence College）** — https://iep.utm.edu/neo-kant/ （访问 2026-10-04）。
   支持：广义/狭义双定义（广义＝任何实质性介入先验观念论者，含柯斯嘉德等）；术语史（1862 Michelet "Neo-Kantianer"；1865 Liebmann "Zurück zu Kant!"）；柯亨"思维构成对象"句、数学规则取代先验统觉、伦理社会主义与理性宗教；文德尔班德语原文名言；拉斯克影响 Weber/卢卡奇/海德格尔；边缘成员 Vaihinger、Dilthey；1929 达沃斯之辩与纳粹迫害致衰落；当代复兴（Luft & Makkreel 2010、Friedman）；结语名句。
3. **Stanford Encyclopedia of Philosophy, "Immanuel Kant"（§1 Life and works；§3 Transcendental idealism）** — https://plato.stanford.edu/entries/kant/ （访问 2026-10-04）。
   支持：莱因霍尔德《书信》(1786)"popularized Kant's moral and religious ideas"、1787 年耶拿康德哲学教席及其后对康德的批评偏离；费希特 1792《试评一切天启》"initially mistaken for a work by Kant himself"、1799 年康德公开决裂；§3 明言先验观念论"没有标准解读"（"there is no such thing as the standard interpretation"）——支撑"康德文本/早期接受/新康德主义"三层边界。

（三条来源相互独立、非互相转抄：1 与 2 为两个百科的不同撰稿传统，3 为人物条目，本次逐条打开读到相关段落。Britannica "Neo-Kantianism" 返回 403 未能核读，已弃用；SEP/IEP 均无独立 Reinhold 条目，相关内容取自 SEP Kant 条目。）

## 5. 立项判断

**结论：新建（作为狭义"新康德主义"tradition-overview 条目）。**

理由：(1) 运动本身在站内零承载（§2），而它是 1865–1930s 德国主导性哲学流派，站内卢卡奇、韦伯、卡西尔、海德格尔、卡纳普等条目均需回指它，一句话提及不足以支撑；(2) 不能**并入**"德国古典哲学"包——新康德主义在史期（后黑格尔）与问题意识（反思辨形而上学、拒物自体）上恰以德国观念论为反对对象，并入会把任务要求的三层边界重新搅成无差别包；(3) 人物条目（康德）已存在且不冲突，按 §3 边界与"德国古典哲学"包、R01/R02/R07 做交叉链接即可，无须**仅加关联**的保守方案；(4) 双百科独立条目 + SEP Kant 条目接受史三来源充分，无阻塞，不属于**暂缓**情形。

## 6. 证据限度与分歧

- **术语与命名**：中文"康德主义"常泛指一切康德式思路；IEP 的广义用法甚至把叔本华、胡塞尔、库恩、柯斯嘉德都算作宽义"新康德主义者"。若立项，标题建议"新康德主义"并在导语交代广狭义，避免与人物条目重叠。Südwestdeutsche Schule 译名有"西南学派/西南德意志学派"，别称"巴登学派"（Badische Schule），条目需并列。
- **莱因霍尔德生卒年分歧（先核实类）**：站内"德国古典哲学"包作 1757–1823；SEP Kant 条目相关段落的检索摘录作 1758–1823。本次 WebFetch 摘要未逐字核到年生段，动站内数据前须单独核实（多数权威资料作 1757 年 10 月 26 日生）。
- **费希特"康德化解读"细节**：SEP Kant 条目只叙述"接受—偏离—公开决裂"脉络，未展开费希特对先验观念论的重构细节；本备忘录对此不做断言，留待"德国古典哲学"包处理。
- **年代起讫**：运动起点有 1855/1860s（费舍 Kuno Fischer 康德评注、朗格《唯物主义史》1866、特伦德伦堡—费舍之争）与 1865（利普曼）两种写法；终点有 1914（一战）、1929（达沃斯）、1933（流亡）多种标法——条目应表述为约数（"约 1870 至一战"）。
- **卢卡奇受新康德主义影响**：站内年表说法与 IEP"拉斯克影响卢卡奇"方向互证，但卢卡奇早期著作（《心灵与形式》《小说理论》）中具体新康德主义成分未在本次来源中逐段核实，写入正式条目时需补查（可延及西方马克思主义包的相应表述）。
- **新康德主义与社会科学**：IEP 提及韦伯与西南派的关联，但"韦伯受李凯尔特影响"的经典论题本次未单独核源，立项后补。
