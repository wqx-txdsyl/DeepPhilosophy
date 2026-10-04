# U07 义务论伦理学（立场包）审读记录

- 日期：2026-10-04（reviewedAt 同）
- 研究员：zcode（内容研究员）
- 状态：ready-for-review

## 1. 旧稿处置

2026-10-04 开工前 `ls docs/content-proposals/schools/`：**U07/ 目录不存在**（A01–U06 等其他任务目录在），无同日旧稿问题。本目录四文件均为本次新建，无"保留/重写"处置事项。检索过程中一次失败尝试照实记录：SEP 无 `/entries/wd-ross/`（404）、`/entries/jeremy-bentham/`（404），Britannica W-D-Ross 条目返回 403（拒绝抓取），均未采信其内容。

## 2. 任务理解与覆盖（相对任务条目）

任务 evidence 字段核实的现状（2026-10-04 复核一致）：`school_伦理学.json` subSchools[1] 即"义务论伦理学"（一行简介，era 标"18世纪—现代"，以康德为单一代表）；"义务论"字样另见于 罗马哲学/功利主义/环境哲学 三条目（mentionFiles）。本包为立场深化包，proposal.relatedEntries 已给出三处挂接建议（伦理学 subSchools[1] 为主挂点、功利主义为对照立场、伦理学 subSchools[0] 德性伦理为接口立场），不接管 mentionFiles 的改写。

任务范围逐项落实：

- **立场类型定位（≠康德伦理学）**：S1 §2.4"如果有哪位哲学家被视为义务论核心，那无疑是康德"+ 三支（行为者中心/患者中心/契约主义）皆可认领康德——overview 首尾两处明确"义务论是家族而非一人一派"。
- **康德定言令式**：S2（SEP Kant's Moral Philosophy）+ S7（IEP Kant's Ethics）双源互证，全部公式附 Akademie 页码（4:402/421/428/432/433/439）；著作年份（1785/1788/1797）由 S3+S7 双证（S2 条目本身不给年份，已避开）。
- **罗斯显见义务**：S4（SEP William David Ross）逐字核读 §4.1。**关键分歧如实呈现**：通行说法为七种清单；SEP 现行条目把正义与自我完善两项视为可归并、以五种基础义务呈现。packet 按 SEP 现行条目呈现并注明"通行七种"，原书第二章未直接核读（版权），原始页码未定位——写入 evidenceLimits。
- **诺齐克权利约束**：S5（SEP Nozick's Political Philosophy）含 ASU 页码定位（ix/31/33/xiv）；与"权利的功利主义"之别（S1 §2）已写。
- **行为者相对限制**：S1 §2.1（agent-relative reasons 定义、父母救子例、"各人守好自家门户"）；Scheffler "agent-centered prerogatives" 术语未在已核来源逐字出现——packet 不使用该术语作断言，timeline 只著录《拒斥后果主义》书目事实（S8 书目：1982 初版、Oxford: Clarendon Press、1994 修订）。
- **主要挑战与回应**：义务论悖论两种形态（S1 §2.2/§3，virulent form 引 Scheffler 1988/Heuer 2011）、冲突义务（康德"不可设想" vs 罗斯方案及其两难、specificationism、avoision）、阈值义务论（S1 §3，Moore 1997 定义原文）——均已入 overview/conclusion/subSchools。后果主义反转一侧：S8 书目 Cummiskey 1996《康德式后果主义》仅作书目与对手清单定位，论证内部未核不展开。
- **与 U06 边界接口**：见下节。

## 3. 分包边界（与 U06 的接口；U08 不涉及）

U06 review.md（2026-10-04 同日交付）已声明："安斯康姆对'道德应当/义务'概念的批判……在本包是德性立场的立论环节；**康德立场与义务论体系的一切展开归 U07，本包 thinkers 不含康德**。"本包对等声明：

- U07 thinkers **不含安斯康姆**（德性侧立论细节归 U06）；她只以三重身份出现在本包：works[5]（1958 原典条目，注明"立论细节归 U06 包"）、timeline[5]（1958 争论节点，注明两包共用接口）、overview 第五段与 conclusion（作为对义务概念的挑战者）。conclusion 末段与 proposal.relatedEntries 均已写明两包分工。
- 斯坎伦契约主义收为本包 thinker/subSchool，因 SEP 契约主义条目明文以康德式洞见为其根据（S10），属义务论内部的当代形态；帕菲特"三重理论"仅作汇聚论提及。
- U06 引入的站外译名"安斯康姆"沿用（避免同一人两个译名进站）。

## 4. 站内译名核对（grep philosophers.json，2026-10-04）

站内已有条目（本包 thinkers 直接沿用精确姓名）：

- 伊曼努尔·康德（1724—1804，德国，德国古典哲学）
- 诺齐克（1938-2002，美国，自由至上主义）——**站内姓名无"罗伯特"前缀，本包沿用"诺齐克"**
- 约翰·罗尔斯（1921-2002，美国，政治哲学）

站内**无**条目、本包首次引入的站外人物（建议译名，请编辑部核定）：

- W. D. 罗斯（William David Ross，1877-04-15 瑟索—1971-05-05 牛津；通译"威廉·大卫·罗斯"；packet 正文用"W. D. 罗斯"首现并注全名）
- 托马斯·斯坎伦（Thomas M. Scanlon；**生年未见于已核来源，thinkers 不注生年**，era 作"20世纪—21世纪"）
- 安斯康姆仅在 works/timeline 出现，译名沿用 U06 已核定建议（G. E. M. 安斯康姆，1919–2001）

## 5. 藏书关联（已核 ID，未造任何 ID）

站内 books.json（409 本，2026-10-04 读取）相关在库藏品，均入 proposal.linkageSuggestions：

- `309de54e4392`《康德著作集（套装10册）》、`390398aff8d0`《康德文集》、`10e1874c2255`《康德三大批判合集（上下）》、`aacc867ec43c`《康德〈实践理性批判〉句读》
- 罗斯《正当与善》、诺齐克《无政府、国家与乌托邦》、斯坎伦《我们彼此负有什么义务》**不在库**——不造 ID；已写入 evidenceLimits。
- 站内《道德与立法原理导论》（边沁，74ee21ced920）属功利主义对照侧、约纳斯《责任原理》（86ff548dbc1e）属环境伦理扩展，均**不**列入本包 linkage（避免立场混淆），仅在 review 留档。

## 6. 分歧、争议与取舍

1. **罗斯义务清单：七种 vs 五种**。通行文献与教科书作七种（守信、补偿、感恩、正义、行善、自我完善、不伤害）；SEP 现行罗斯条目称罗斯"最初列出表面上七种"，但正义与自我完善可被"produce as much good as possible"吸收，以五种基础义务呈现。本包：cihai[5] 与 thinkers[1] 按"通行七种 + SEP 现行归并"双轨表述，不裁断；review 留证。另：罗斯自评 prima facie 是"不幸的措辞"（两理由）已直引；罗斯首选的替代术语 SEP 未给出，本包不写。
2. **康德"fiat iustitia, pereat mundus"绝对主义**：S1 有此并提，但格言在康德著作中的原始出处未核——不写入正文，仅在 evidence 留档。
3. **冲突义务的康德主张**（"义务冲突不可设想"）：S1 转述并评论"结论想要而理由难产"；康德原典页码（通行注 MM 导论 6:224）未在本包核实——不注页码。
4. **罗尔斯"正当优先于善"**：S9 仅间接支持（基本自由对总体善诉求的特殊优先）；该口号作罗尔斯原书术语的逐字性未核——packet 只用间接表述，relations[2] type 定为"接受/定位"而非影响因果。
5. **谢弗勒**：《拒斥后果主义》1982/1994 书目事实（S8）；paradox of deontology 的 virulent form 引文出自 S1（其引 Scheffler 1988，可能指修订版或 1988 年文集导论，未核）——packet timeline 只写 1982 初版与 1994 修订，不写 1988。
6. **词源史**：deontology 希腊词源（deon+logos）出自 S1 开篇原文；Bentham 1834 遗著《Deontology》未能核实（SEP Bentham 条目 404、Britannica 403）——时间线不设该节点，写入 evidenceLimits。
7. **跨传统不凑配额**：未设任何"中国义务论"式比较；罗马哲学 mentionFile 只作提示性关联，本包不展开自然法谱系（奥古斯丁—阿奎那一线未核，不写）。
8. **"残酷玩笑"句**：S1 条目作者的论证性表述，quotes[1] 署名条目作者并标 paraphrase，不冒充哲学家原话。

## 7. 仍缺证据 / 证据限度（与 packet.evidenceLimits 同步）

- 罗斯《正当与善》第二章原书文本（版权所限）未直接核读；七种清单的原始页码未定位。
- 康德公式中译为编译（quoteKind 全部标 paraphrase），未与邓晓芒/杨祖陶等既定中译本逐字比对。
- 斯坎伦生年；Scheffler 1988 具体文献；Moore 1997 具体文献（通行注 Placing Blame）；Cummiskey 1996 论证内部；Taurek/Raz/Sen 1982/Katz 1996 等被引文献——均未逐一核读，相关断言严格限于来源条目的框架性转述。
- 安斯康姆 1958 原刊未在本包直接核读（U06 已核原刊 PDF 并逐段核对；本包转述以 SEP 条目为据）。
- deontology 一词的近代用法史（Bentham 1834 或更早）缺失。

## 8. 实际核读 URL 清单（全部真实打开并读到相关段落，2026-10-04）

| # | URL | 用途 | 结果 |
|---|-----|------|------|
| S1 | https://plato.stanford.edu/entries/ethics-deontological/ | 定义/词源/悖论/冲突义务/阈值/康德定位/诺齐克/罗斯 | WebFetch 全文，两次核读 |
| S2 | https://plato.stanford.edu/entries/kant-moral/ | 定言令式诸公式与页码、善良意志、完全/不完全义务 | WebFetch 全文（首次超时，重试成功） |
| S3 | https://plato.stanford.edu/entries/kant/ | 康德生平与著作年表（1785/1788/1797）、Reinhold 传播 | WebFetch 全文 |
| S4 | https://plato.stanford.edu/entries/william-david-ross/ | 罗斯生平、义务清单（七种 vs 五种分歧）、prima facie 术语、RG/FE 差异、直觉主义 | WebFetch 全文，两次核读（§4.1 逐字） |
| S5 | https://plato.stanford.edu/entries/nozick-political/ | 诺齐克生平、side constraints、ASU 页码、权利功利主义之别 | WebFetch 全文 |
| S6 | https://plato.stanford.edu/entries/anscombe/ | 1958 三论纲、律法式诊断、consequentialism 造词、绝对排除 | WebFetch 全文 |
| S7 | https://iep.utm.edu/kantview/ | 康德伦理学非 SEP 独立核读（公式互证、年份、义务论定位） | WebFetch 全文 |
| S8 | https://plato.stanford.edu/entries/consequentialism/ | 后果主义定义、Ross 反例、Scheffler/Cummiskey 书目、agent-neutrality | WebFetch 全文 |
| S9 | https://plato.stanford.edu/entries/rawls/ | 罗尔斯 1971/1993、契约传统定位、自由优先 | WebFetch 全文 |
| S10 | https://plato.stanford.edu/entries/contractualism/ | 斯坎伦 p.153 原则原文、与康德关系、帕菲特三重理论 | WebFetch 全文 |
| — | https://plato.stanford.edu/entries/wd-ross/ | 罗斯条目候选 URL | **404**（改用 william-david-ross） |
| — | https://plato.stanford.edu/entries/jeremy-bentham/ | 边沁 Deontology 1834 词源 | **404**（词源节点放弃） |
| — | https://www.britannica.com/biography/W-D-Ross | 罗斯 Britannica 补充源 | **403**（拒绝抓取，未采信） |

来源构成：SEP 8 条目 + IEP 1 条目，3 个独立成文群（Alexander & Moore 义务论 / Kant 系 / Ross-Nozick-Rawls-Contractualism 系），均无互相转抄关系；学术百科占比 100%，满足契约来源优先级。
