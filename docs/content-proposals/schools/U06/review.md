# U06 德性伦理学（立场包）审读记录

- 日期：2026-10-04（reviewedAt 同）
- 研究员：zcode（内容研究员）
- 状态：ready-for-review

## 1. 旧稿处置

2026-10-04 开工前 `ls docs/content-proposals/schools/`：**U06/ 目录不存在**（A01–U04 等其他任务目录在，U05 亦未建），无同日旧稿问题。本目录四文件均为本次新建，无"保留/重写"处置事项。

## 2. 任务理解与覆盖（相对任务条目）

任务 evidence 字段核实的现状（2026-10-04 复核一致）：

- `school_伦理学.json` subSchools[0] 即"德性伦理学"（一行简介），thinkers 有"亚里士多德""麦金太尔"简条——本包为立场深化包，不重复主条目的通史框架。
- `school_社群主义.json` subSchools[1]"德性伦理社群主义"（以麦金太尔为代表）——相关分支，本包在其 detail 与 subSchools[4] 注明亲缘与边界。
- `school_古希腊哲学.json`、`school_功利主义.json` 含"德性伦理"字样提及——分别对应古典源头与安斯康姆对后果主义的批判，proposal 已建议衔接。

任务范围逐项落实：

- 复兴起点（安斯康姆 1958 三条论纲）：S5 原刊全文逐段核对（开篇论纲、consequentialism 造词、论亚里士多德诸段、律法式伦理观历史诊断）。
- 成熟形态（foot/Hursthouse，德性作为品格特质、phronesis、eudaimonia）：S3（SEP 福特）+ S1/S4；站内无此二人条目，译名见 §4。
- 对规则伦理学的批评（行动者中心 vs 行动中心）：S1（该口号在现行 SEP 中被作为需纠正的误解处理）+ S4（right-person vs right-action 框架）。overview 与 conclusion 如实呈现这一变化，未把口号当作定论。
- 应用扩展（德性政治、德性认识论可提及）：S7（德性认识论专条）+ S1（未来方向节提及 virtue politics、character education）；均只作方向性提及，未展开成节。
- 跨传统比较必须有据、不把"概念相似"算历史传承：儒家用 S8（SEP 中西比较哲学：Yu 2007、May Sim 2007、Van Norden 等）+ S9（SEP 孔子：德性框架之现代性、role ethics 竞争解读）；佛教用 S6（SEP 印度佛教伦理：Keown 德性伦理解读 vs 后果主义解读）。亚里士多德↔孔子关系 type 明确写"编辑比较"；佛教比较不设人物关系条目，只以传统层面的研究争论呈现。

## 3. 分包边界（U07 / U08）

- **U07 义务论**：安斯康姆对"道德应当/义务"概念的批判（律法式伦理观的世俗遗留）在本包是德性立场的立论环节；康德立场与义务论体系的一切展开归 U07。本包 thinkers 不含康德。
- **U08 关怀伦理**：SEP《德性伦理学》现行版（2026-05-03 修订，S1 抓取核实）的变体分类（幸福主义／基于行动者与典范／目标中心／柏拉图主义）**已不列关怀伦理**；吉利根等人归 U08。本包仅在分包边界处提及此分类事实。
- 与站内"情感主义伦理学"分支：麦金太尔的情感主义诊断涉及休谟—斯蒂文森一线，本包只在 detail 转述其诊断，不展开情感主义史。

## 4. 站内译名核对（grep philosophers.json，737 键）

站内已有人物条目（本包 thinkers 直接沿用其精确姓名）：

- 亚里士多德（前384—前322）、孔子（前551—前479（传统纪年））、玛莎·努斯鲍姆（20世纪-21世纪）。

站内**无**条目、本包首次引入的站外人物（建议译名，请编辑部核定）：

- 格·伊·摩·安斯康姆（G. E. M. Anscombe，1919–2001；通译"安斯康姆"）
- 菲利帕·福特（Philippa Foot，1920–2010；**又译"富特"**，两译均通行，请编辑部定夺，本包正文以"菲利帕·福特（又译富特）"首现）
- 罗莎琳德·赫斯特豪斯（Rosalind Hursthouse）
- 阿拉斯代尔·麦金太尔（Alasdair MacIntyre）——注意：**站内藏书《德性之后》（books.json 2131abc93fdc）署名"阿拉斯戴尔·麦金泰尔"**，与本包通行译名异文；thinker 的 sub 字段已注明，建议关联书籍时保留原署名。
- 仅在 subSchools 出现的站外人名（斯洛特、斯旺顿、默多克、亚当斯、基翁、古德曼等）均附英文原名。

## 5. 藏书关联（已核 ID，未造任何 ID）

- `e574c8e7f515`《尼各马可伦理学[注释导读本]》（亚里士多德）→ works[0] 与 proposal.linkageSuggestions
- `2131abc93fdc`《德性之后》（阿拉斯戴尔·麦金泰尔）→ works[5] 与 proposal.linkageSuggestions

## 6. 分歧、争议与取舍

1. **福特是不是"德性伦理学家"**：SEP 福特条目明确说她本人 disavowed 该标签、且不把她的转向归因于安斯康姆 1958 一文。本包处理：定位为"复兴的核心建构者"，关系条目只写同侪（1946 年起同在萨默维尔；福特自认由安斯康姆引入维特根斯坦），不写影响因果；conclusion 第二段专写"自我否认与学科追认"。
2. **"行动者中心 vs 行动中心"**：这是批评者的概括口号，SEP 现行版把它当误解处理。本包如实写口号与其被批评的经过，不用它作定义。
3. **安斯康姆"三条论纲"**：IEP 的转述顺序与原文不同（IEP 先列 Sidgwick 论纲）；本包一律以 S5 原刊开篇顺序与措辞为准。
4. **麦金太尔卒年**：IEP 条目仍作"1929—"（未更新）；卒年 2025-05-21 采用 Daily Nous 讣闻（S11，已实际抓取），并写入 evidenceLimits 建议双注。
5. **After Virtue 年份**：SEP/IEP 书目分别引 1985（Penguin 版）与 1981/1984/2007；本包以初版 1981 为准（S10+S11 双证）。
6. **儒学、佛教比较**：严守"编辑比较"；S8 明列"illicit assimilation"为头号方法论陷阱，S9 明言以 virtue 框架读儒学是现代学术做法——两句均已入 overview 与 evidenceLimits，防止读者把比较读成传承。

## 7. 仍缺证据 / 证据限度（与 packet.evidenceLimits 同步）

- 赫斯特豪斯生年（通行作 1943）未见于已核来源；SEP 无其独立条目（/entries/hursthouse/ 404，2026-10-04 实测），IEP 条目无生年。
- 余纪元（Jiyuan Yu）中文名与《德性之镜》中译书名：仅据检索记录（台湾期刊书评著录），未核读中译本版权页；英文姓名与 2007 著作、对勘方案由 S8 确认。
- Keown 1992《佛教伦理的性质》、Yu 2007、Sim 2007 原书未核读，仅据 SEP 条目著录转述。
- 《善的脆弱性》仅核书目（Open Library）+ S1 间接覆盖，未通读全书。
- 本包所有中文引文为编译者译文（quote/quotes/closingQuote 均已标注），未与苗力田译本等既有中译比对；英文原文逐句核对自 S5 原刊 PDF。
- 《尼各马可伦理学》成书/编定年代无定论，时间线用"约前4世纪"；未写具体年份。

## 8. 实际核读 URL 清单（全部真实打开并读到相关段落）

| # | URL | 用途 | 方式 |
|---|-----|------|------|
| S1 | https://plato.stanford.edu/entries/ethics-virtue/ | 定义、变体、批评、扩展 | WebFetch 全文摘要 |
| S2 | https://iep.utm.edu/anscombe/ | 安斯康姆生平与三条论纲转述 | WebFetch 全文摘要 |
| S3 | https://plato.stanford.edu/entries/philippa-foot/ | 福特生平、年表、自然善性、标签问题 | WebFetch 全文摘要 |
| S4 | https://iep.utm.edu/virtue/ | 亚里士多德框架、赫斯特豪斯/福特/麦金太尔概要 | WebFetch 全文摘要 |
| S5 | https://sites.pitt.edu/~mthompso/readings/mmp.pdf | 安斯康姆 1958 原刊全文 | curl 下载 + pdftotext + 字体解码后通读、关键段 grep |
| S6 | https://plato.stanford.edu/entries/ethics-indian-buddhism/ | 佛教伦理分类之争（Keown vs 后果主义） | WebFetch 全文摘要 |
| S7 | https://plato.stanford.edu/entries/epistemology-virtue/ | 德性认识论扩展 | WebFetch 全文摘要 |
| S8 | https://plato.stanford.edu/entries/comparphil-chiwes/ | 比较方法论警示与儒学—亚氏比较文献 | WebFetch 全文摘要 |
| S9 | https://plato.stanford.edu/entries/confucius/ | 孔子德目、习惯化、框架限定 | WebFetch 全文摘要 |
| S10 | https://iep.utm.edu/mac-over/ | 麦金太尔生平与《追寻美德》 | WebFetch 全文摘要 |
| S11 | https://dailynous.com/2025/05/22/alasdair-macintyre-1929-2025/ | 麦金太尔卒年 | WebFetch 全文摘要 |
| S12 | https://openlibrary.org/search.json?q=fragility+of+goodness+nussbaum | 《善的脆弱性》书目 | curl 获取 JSON |

辅助核对（非 sources，不入引用链）：Crossref API（Anscombe 1958 卷期页码与 DOI）；站内 philosophers.json / books.json / 四个 school_*.json 直接读文件。

未采信：WebSearch 结果片段仅用于定位 URL（如 IEP MacIntyre 条目真实 slug、SEP 佛教伦理条目 slug），其内容性表述（如 MacIntyre 卒年）在采信前均以可抓取来源复核。Cambridge Core 文章页（429 限流）、PhilPapers（403）、Guardian/NPR 推测 URL（404）等未能打开的候选来源未写入 sources。

## 9. 复核方法自评

reviewMethod 已在 packet.json 声明：多源独立（SEP 与 IEP 互不转抄；原刊 PDF 独立于两百科）；关键断言（三条论纲、造词、卒年、书目）均有≥1 个一手或一手性来源；自检为本研究员自查，非独立同行评审。
