# R01 法哲学 —— 资料包审读报告（2026-10-04）

> 本报告是 packet.json 的审读配套：边界辨析、查重结果、证据限度与实际核读 URL 清单。research.md（立项备忘录）原样保留，本报告在其基础上覆盖 packet 阶段的新增核实。

## 1. 边界辨析

**（一）法家 ≠ 法哲学。** 站内《法家》条目 overview 自述："法家是后世对若干先秦政治思想家的分类，通常包括商鞅、申不害、慎到和韩非等……并不构成一所有固定师承、统一教义的学校"（本包阶段重读原文核对一致）。它是先秦政治思想传统的事后分类，处理的是统治术与国家竞争问题；法哲学（一般法理学）处理的是"法是什么、效力从何而来、如何解释"的分析性问题。二者只在"法与道德、法与权力"话题上有比较价值。**建议：跨传统比较话题互加"参见"，正文明确声明不把任一传统等同于法哲学整体；不凑"一个西方 + 一个东方"配额。**

**（二）与《政治哲学》包分工。** 《政治哲学》的组织轴是 20 世纪 70 年代以来的正义/权利论战（罗尔斯、诺齐克、阿伦特、伯林、哈贝马斯、桑德尔）。德沃金在该包仅以《认真对待权利》引文与辞条出现，拉兹仅见"多元主义"辞条；法律效力来源、承认规则、法律解释等本领域核心问题未被任何包承载。划界依据是外部的：SEP《The Nature of Law》以"律师式局部问题 vs 法的本性问题"划出一般法理学（S1 导言）。**建议：互加关联，正义理论归彼、法的效力—正当性—解释归此。**

**（三）与其他条目。**
- 《伦理学》：守法义务、恶法抵抗是连接点（拉兹"连初显的守法义务也不存在"即跨界论题），但概念工具独立；守法义务展开归 SEP《Legal Obligation and Authority》条目群，本包不展开。
- R07 元伦理学：SEP 把一般法理学定位为"元规范探究"（metanormative inquiry），与元伦理学互为方法论平行物，宜互加"参见"（S1 §2.3）。
- 《德国古典哲学》《伦理学》：黑格尔《法哲学原理》属德国观念论法权哲学，细节留原包，加跨链。
- 《罗马哲学》：罗马法学家（乌尔比安正义定义）作自然法语汇古代源头的双向历史关联，不讲成"法哲学是罗马产物"。
- "阿卡德法哲学""马来阿达特习惯法哲学"：区域个案 subschool，各加"属跨传统比较话题"指向本包，本包不吸收。

## 2. 查重结果（结论：新建 field 条目）

- **顶层无同名条目**：`app/public/schools/data/` 共 111 个 school_*.json（本包阶段当日重数），无论文/法理学领域总览。
- **关键术语站内分布**（本包阶段当日重跑 grep）：「法理学」「凯尔森」「菲尼斯」零提及；「法律实证主义」仅《北欧哲学》一处（乌普萨拉学派影响表述）；「德沃金」见《自由主义》《政治哲学》两处（对备忘录"仅在政治哲学"的细化）；「拉兹」仅《政治哲学》；「富勒」唯一命中是《超验主义》的玛格丽特·富勒（同名异人）；「哈特」命中均为哈特曼/哈特莱类人名巧合。全部 16 处"法哲学"字样提及均为思想家著作、年代记或区域个案粒度，无一可扩展为领域总览。
- **relatedBranches 不能承载**：两个均为 subschool 个案（见上），只能单向加关联。
- **哲人库核对**（philosophers.json 键名脚本匹配）：托马斯·霍布斯、杰里米·边沁、托马斯·阿奎那在库，可作人物关联；其余七人无条目；**「J.L. 奥斯汀」「玛格丽特·富勒」「尼古拉·哈特曼」为同名异人，严禁按姓氏自动关联**。
- **命名建议**：主名"法哲学"，别名收"法理学 / Jurisprudence / Philosophy of Law"（中文界对 Jurisprudence 与 Philosophy of Law 的译名分工无定论，正文首段说明）。

## 3. 立场与写法上的分歧处理

- **两说关系的元分歧**：菲尼斯条目（SEP，2025-03 修订）断言实证主义的对立主张 "pointless, that is redundant"；格林—亚当斯条目仍以对峙结构叙述。packet 并存呈现（overview 第 4 段、relations/6），不择一为定论。
- **富勒的道德地位**：哈特"投毒术的道德性"之讽、拉兹/克雷默"道德上中性如手术刀"之评，与富勒"内在道德"说并置（cihai/8、subSchools/5 关联条目），由读者见其争。
- **恶法非法**：按菲尼斯条目 §4 写成"变体（perversion）+ 三组类比"的考辨式定义，不沿用"恶法非法=自然法否认恶法是法"的通行简化。

## 4. 证据限度（摘要，完整版见 packet.json evidenceLimits）

1. 德沃金、拉兹、富勒、菲尼斯、霍布斯的生卒年未在已核来源读到（Britannica 传记页 403 不可达），一律只给世纪；哈特（1907–1992）有 Internet Archive 编目依据。
2. 《法律的道德性》版次年份在两个 SEP 书目间侧重不一（1964 vs 1969 修订），以"1964 初版 + 1969 修订"并列。
3. "开放结构"（open texture）未见于本次核读的 SEP/IEP 条目原文，未设辞条；"law as integrity"未见于 SEP《The Nature of Law》原文，未当作用语引用。
4. 哈特—富勒论战的所刊载体（通行说法《哈佛法律评论》1958）与富勒回应文篇名未核，只写"1958 年论战"与哈特文篇名（有据）。
5. 法律现实主义与批判法学未被 SEP 列为主传统，不设分支；站内《北欧哲学》"法律实证主义"指称乌普萨拉学派的术语出入（通行文献多称斯堪的纳维亚法律现实主义）本次未做外部核实，仅此提示。
6. 非来源平台限度：Britannica 403、web_reader/搜索 429、IEP jurisprudence 猜测路径 404；非 SEP 平衡靠 IEP《Legal Positivism》与两条 Internet Archive 编目记录。
7. 跨传统限度：法家、阿卡德（公元前 24—前 22 世纪系站内标注）、马来阿达特年代未做外部核实，正文不复述。
8. mentionFiles 16 处提及中备忘录阶段精读 7 个、11 个仅据任务 JSON 转述；packet 正文不引用那 11 个文件的具体表述。
9. 本包为研究者同日两阶段自检，非独立同行评审；引语以英文原文逐字核读为准，中文均标注为本包译文/转述。

## 5. 实际核读 URL 清单

**备忘录阶段（2026-10-04，继承自 research.md）：**
1. https://plato.stanford.edu/entries/lawphil-nature/ （通读）
2. https://plato.stanford.edu/entries/legal-positivism/ （通读）
3. https://plato.stanford.edu/entries/natural-law-theories/ （通读）
4. https://plato.stanford.edu/search/search?query=philosophy+of+law （检索定位 + Related Entries 区）
5. 站内：app/public/schools/data/ 111 个文件全量 grep；精读美索不达米亚、犹太、罗马、德国古典、伦理学、北欧、政治哲学、法家 8 包相关字段（备忘录记 7 个精读 + 法家，本包阶段重验法家与政治哲学）

**Packet 阶段（2026-10-04，本包新增）：**
6. https://plato.stanford.edu/entries/lawphil-theory/ （通读：凯尔森版本史、基本规范）
7. https://plato.stanford.edu/entries/hobbes-moral/ （定向问答：Leviathan 1651/1668、17 世纪表述、转引句）
8. https://iep.utm.edu/legalpos/ （先 curl 探测 200，再通读：分离命题、富勒八原则与 poisoning 回应、语义刺、渊源命题；作者 Himma）
9. https://plato.stanford.edu/entries/legal-positivism/ （定向复核：书目年份 Austin 1832 [1995]、Bentham 1782 [1970]、Hart 1961 [2012]、Fuller 1964、Raz 1979 [2009]；§3 包容/排他；§4.2 分离命题与哈特文篇名；确认全条目无 "open texture"）
10. https://plato.stanford.edu/entries/natural-law-theories/ （定向复核：§1.3 富勒接续阿奎那、§1.5 determinatio、§4 恶法考辨与三组类比、导论 pointless/redundant 原句、书目 Finnis 1980/2011）
11. https://plato.stanford.edu/entries/lawphil-nature/ （定向复核：§1.1 理论版图与 Dworkin 1977/1986、Greenberg 2014；§1.1 霍布斯谱系；§2.3 元规范探究；现实主义/批判法学定位；导言与 §2.3 原句）
12. https://archive.org/metadata/conceptoflaw0000hart （编目记录：Hart 1907–1992；OUP 2012）
13. https://archive.org/metadata/takingrightsseri0000dwor （编目记录：Dworkin，1977；另核对 takingrightsseri00dwor 1978 印本）
14. https://iep.utm.edu/legal-positivism/ 与 https://iep.utm.edu/legal-po/ （404，排除）；https://www.law.cornell.edu/wex/legal_positivism 等三个 Wex 路径（404，排除）
15. https://www.britannica.com/biography/Ronald-Dworkin （403 Forbidden，不可用，如实排除）
16. 站内：app/public/philosophers.json（脚本全量键名匹配）；schools/data/ 术语 grep 重跑

**访问失败记录**：Britannica 各页 403（WebFetch）；web_reader 两次 429；搜索服务 429（IEP URL 由 curl 探测替代搜索确认）。

## 6. 复核结论

- 结论维持备忘录判断：**新建 field 级条目**，status=ready-for-review。
- 来源 11 项（S1–S11）：SEP 五目 + IEP 一目 + Internet Archive 两条 + SEP 检索页 + 站内两项核查；≥3 且不互相转抄（IEP 与 SEP 组织结构、书目路径均不同；archive 编目为独立实物记录）。
- 计量：辞条 10、时间线 10、著述 8、人物 8、分支 6、关系 7——均在契约区间内。
- 无阻塞项：所有新增内容均有当日实读来源支撑；未核实项全部降级为"不写"并记入 evidenceLimits。
