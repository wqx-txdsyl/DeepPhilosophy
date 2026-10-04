# J01 京都学派 — 复核记录（reviewedAt 2026-10-04）

## 1. 边界决定

- **核心成员**：西田几多郎、田边元、西谷启治（Heisig 经武内义範建议的"三角"说，SEP §2.2 转述）。这三人也是站内 philosophers.json 中标注"京都学派"的三位，包内外一致。
- **边界人物如实标注**：九鬼周造（SEP：受西田带进京大、"思想与活动过于独立、不入内核"；站内标注"京都学派 / 存在主义哲学"，本包在 thinkers 中保留其边界身份）；三木清（西田门下，大橋良介曾以其马克思主义倾向排除，但今日与户坂润同被一些人列入"京都学派左翼"）；户坂润（"京都学派"命名者兼批判者，后又被追认为"左翼"成员——此反讽是学术史实况，如实呈现）；久松真一（第二代，大橋方案）；上田闲照（第三代，西谷学生）。
- **明确不列为成员**：和辻哲郎——SEP §2.3 与九鬼并述，"ideas and their activities remained too independent to count them among the inner circle"，且站内 philosophers.json 未给他标"京都学派"。本包不收。
- **不收录且不断言**：任务别名提示中的"久野收"。SEP《The Kyoto School》全文（curl 全文抓取后逐节检索）未出现该人物，无据可引；按研究纪律"拿不准就不写"，从成员表、关系、时间线中全部略去，仅在此说明。任务提示中列名的归属争议人物以三木清为代表处理。
- **未入包但有关联的人物**（防止审读者误以为遗漏=否认）：阿部正雄、高山岩男、下村寅太郎、务台理作、武内义範、辻村公一、木村敏。SEP 对其归类：高山/下村在第二代名单、辻村在第三代名单；木村敏"可视为第三代（若放宽标准）"；务台为"鲜为人知但亲近的弟子"；铃木大拙为"密切相关者"（非学院哲学家、非京大任教）。均因生卒或关键细节未逐一核实而不入包。
- **subSchools 留空**：SEP 明言该学派从未建立机构或正式组织，内部分化是世代与个人体系（西田哲学/田边哲学/西谷哲学），不是子派；不虚构分支。

## 2. 政治争议的处理

按契约第 9 条"以证据说明分歧，不加无据赞誉或污点"执行：

- 时间线与 overview 只写有定位的事实：两大战时座谈（参与者、结集年份、审查与皇道派攻击）、"大岛笔记"所载海军秘密研讨会（含三阶段议题及其证据限度——仅第二阶段见于笔记）、战后公职整肃与左右夹击、三木/户坂死于狱中。
- 正面材料也注明出处：西田 1941 年对天皇演说的"全体主义是时代错误"（SEP 转引 NKZ XII, 271）、其《世界新秩序の原理》反对民族中心主义/扩张主义/殖民主义的文本内证据（NKZ XII, 432–33）；同时保留同一文本"东亚中心只有日本"（NKZ XII, 429）与"八纮一宇"用语的问题面。
- 评价对立如实并陈：Najita & Harootunian 的严厉指控 vs Parkes/Heisig 的反驳 vs 上田闲照"输掉的意义争夺战"定性；conclusion 明言"本条目只呈现证据与分歧，不作裁断"。
- 不为任何一方添加 SEP 来源之外的溢美或贬责。

## 3. 查重与站内一致性

- 任务 coverage=mentions-only：京都学派仅作为片段出现在 `app/public/schools/data/school_日本哲学.json` 的 overview/thinkers/timeline/cihai/conclusion 中，无独立入口；本包为全新条目，不改动既有文件。
- **提请主控注意的数据不一致**：`school_日本哲学.json` 的 thinkers 数组把**和辻哲郎**标注为 sub="京都学派"，而站内人物页（philosophers.json）和辻条目 school="日本哲学·文化哲学·存在论·伦理学"。本包证据（SEP §2.3）支持后者。是否修正旧条目由主控决定。
- 旧正文的引语与断言一律不继承（契约第 7 条）：如旧条目"京都学派对海德格尔、萨特等西方哲学家产生了间接影响"（无定位）未采用；旧条目列西谷《空与即》为著作——本包未能在核实来源中定位其原刊信息，写入 evidenceLimits，不采用也不否定。
- 书籍关联：`app/public/books.json`（409 本）中无西田/田边/西谷/九鬼著作，`suggestedBookLinks` 为空数组，不编造书籍 ID。

## 4. 实际核读的 URL 清单（全部 2026-10-04 实读）

| # | URL | 方式 | 读到的内容 |
|---|-----|------|-----------|
| S1 | https://plato.stanford.edu/entries/kyoto-school/ | curl 全文（260KB）+ 本地解析 | 定义、§2 命名与成员、§3 绝对无诸形态、§4 战时政治全部正文（4.1–4.5）、全部书目、"Other Internet Resources" |
| S2 | https://plato.stanford.edu/entries/nishida-kitaro/ | curl 全文（160KB）+ 本地解析 | 生平年代、著作清单与年份、全部核心概念、师承与影响、汤川秀树、"miner of ore" |
| S3 | https://plato.stanford.edu/entries/japanese-philosophy/ | WebFetch（相关小节） | §4.4.2 近现代学术哲学（西田定位、田边/九鬼/和辻处境）、§4.4.3 战后攻击与学派国际化 |
| S4 | https://www.aozora.gr.jp/index_pages/person182.html | curl | 西田生卒、作品清单、站方解题（纯粹经验→场所逻辑→絶対矛盾的自己同一） |
| S5 | https://www.aozora.gr.jp/cards/000182/card946.html | curl | 《善的研究》初出（弘道馆 1911-02-06 发行；解题言 1911 年 1 月刊行）、底本岩波文库 |
| S11 | https://www.aozora.gr.jp/cards/000182/files/946_74853.html | curl（Shift_JIS 解码） | 序与第一编第一章原文逐字（三处直接引语出处） |
| S6 | https://www.aozora.gr.jp/cards/000182/card1755.html | curl | 《絶対矛盾的自己同一》初出《思想》202 号 1939 年 3 月、西田自评 |
| S7 | https://ci.nii.ac.jp/books/search?q=懺悔道としての哲学 | curl | 岩波 1946.4（132 馆藏）、1950 四版、UC Press 1986 英译、岩波文库 2010 |
| S8 | https://ci.nii.ac.jp/books/search?q=宗教とは何か+西谷 | curl | 創文社 1961.2（222 馆藏）、著作集 1986–1995、各语译本 |
| S9 | https://ci.nii.ac.jp/books/search?q=種の論理の辯證法+田辺 | curl | 秋田屋 1947.11（112 馆藏） |
| S10 | https://ci.nii.ac.jp/books/search?q=いきの構造&year_from=1930&year_to=1940 | curl | 岩波書店 1930（150 馆藏） |

WebSearch 仅用于发现候选来源；所有进入 sources 的 URL 均为上表实读页面，未以搜索片段充当核实。

未采用/失败的来源：Britannica "Kyoto school"（403 拒绝抓取，放弃）；UC Press《Philosophy as Metanoetics》书页（只返回站点模板，放弃）；京都大学日本哲学史研究室页面（两次抓取超时，放弃）；mcp web_reader 与搜索工具间歇限流，未影响上述实读来源。

## 5. 仍缺证据 / 后续建议

- 西田任教授年份（1913 vs 1914）：需一个日文权威来源（如京都大学文学部沿革、吉泽传三郎或藤田正胜的日文专著）仲裁；现按 SEP 表述 + evidenceLimits 处理。
- 西谷〈空と即〉（1948？）原刊定位：需日文原典来源；核实后可补入 works 与 cihai（"空与即"术语）。
- "久野收"（任务别名）：若主控确有此人依据（或为他人之名），需另行提供来源，本包无从核起。
- 田边"种的逻辑"诸论文的最初发表年份（1930 年代中期诸篇）：本次仅核实 1947 年结集本，单篇初出未定位，works 只写结集本。
- 直接引语仅覆盖《善的研究》；田边"忏悔道"定义、西谷"三场域"目前为转述（符合契约 paraphrase 规则），如需原句引文应查岩波文库/创文社纸本。

## 6. 交付物自检

- packet.json / evidence.json 均以 `python3 -m json.tool` 校验通过（见最终报告）。
- 字段契约核对：schemaVersion=1；顶层无 sub_schools（在 school.subSchools）；sources id 唯一且日期真实；relations 的 from/to 全部在本包 thinkers 名单内；timeline 无伪造年代（范围年份均标注证据限度）；quote/quotes/closingQuote 仅含逐字核对或明确标为 paraphrase 者；reviewMethod 如实声明为自检复核。
- 本包未改动 J01 目录以外任何文件，未执行任何 git 写操作。


## 主控修订记录（2026-10-04）

- 补齐契约要求的顶层 evidenceLimits（内容取自本文件复核记录）。
