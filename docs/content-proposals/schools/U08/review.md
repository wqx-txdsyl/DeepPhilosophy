# U08 关怀伦理学（立场包）审读记录

- 日期：2026-10-04（reviewedAt 同）
- 研究员：zcode（内容研究员）
- 状态：ready-for-review

## 1. 旧稿处置

2026-10-04 开工前 `ls docs/content-proposals/schools/`：**U08/ 目录不存在**（A/B/F/I/J/R/T 组及 U01–U06 在），无同日旧稿。本目录四文件均为本次新建，无"保留/重写"处置事项。

## 2. 任务 evidence 字段复核（2026-10-04 实查）

- `exactBranches`：`school_伦理学.json` branches[3] 确为『关怀伦理学』（era 20世纪晚期；desc 一行，提吉利根不提诺丁斯/特隆托）——与任务清单一致；本包 status 用 ready-for-review，proposal 建议直接以本包充其 detail。
- `mentionFiles` 五个文件（南岛哲学、北欧哲学、女性主义、环境哲学、澳洲原住民哲学）grep 全部命中，次数与任务清单一致（1/2/2/1/2）；未逐一读上下文，已入 evidenceLimits。
- `researchLeadIds`（philpapers/stanford-research）：stanford 线落实为 SEP《Feminist Ethics》；philpapers 当日 web_search/web_reader 多次 429 限流未达，未引用。

## 3. 来源与核读方法

- **S1** SEP《Feminist Ethics》（https://plato.stanford.edu/entries/feminism-ethics/ ，注意 slug 是 feminism-ethics 而非 feminist-ethics）：2019-05-27 首发、2025-08-22 实质性修订（页面头部实查）。curl 全文抓取后按小节解析 §1.3/§2.2/§2.4 及书目。
- **S2** IEP《Care Ethics》（https://iep.utm.edu/care-ethics/ ，作者 Maureen Sander-Staudt，ASU——Author Information 节实查）：全文抓取解析 §1—§8 与参考书目。
- **S3** OpenStax《Psychology 2e》§9.2 Lifespan Theories（莱斯大学开放教科书）：全文抓取，科尔伯格三水平、海因茨困境原文（Kohlberg 1969, p.379）、吉利根研究助手身份与批评均逐句核对。
- 另抓 SEP《Virtue Ethics》（2026-05-03 修订）与《Deontological Ethics》（2024-12-11 修订）核对分类与对照（见 §5c/§5d）。
- 阻断记录：Britannica 的 Gilligan/Kohlberg 词条 curl 与 WebFetch 均被 403 拒绝，未采用；SEP 旧 slug `feminist-ethics`、IEP 旧 slug `fem-eth` 均 404（正确 slug 见上）。

## 4. 任务范围的逐项落实

- 吉利根起点与科尔伯格批评：S1 §2.2 + S2 §1a + S3 §9.2 三源互证；批评要点锁定为①样本（白人中上层男性与男孩）②评分把关系/责任取向误判为发展不足③"权利道德优先于责任道德"的错误排序（S1 转述 1982, 18–19, 30）。**不写**"84 名男孩""六阶段"（来源未核，见 evidenceLimits）。
- 诺丁斯哲学化：one-caring/cared-for、engrossment、natural caring、拒斥普遍原则、偏倚论及后期修正，S2 §1b/§3d 为准。
- 理论与实践关系之争：落实为两条线——①定位之争（独立框架 vs 德性伦理子集，S1 §2.4 + S2 §5，两说并录）；②"关怀之声是女性的还是人的"（吉利根"主题而非性别"→2023"人的声音/父权之声"，S2 §1a + S1 §2.2）。全球照护链的理论—实践落差另入 conclusion。
- 政治延伸：特隆托（三边界、四阶段/四要素、特权者的免责，S2 §1c.v/§2/§8）、赫尔德 2006、基泰 1999（dependency workers/doula）、罗宾逊 1999/2013（IR）全部实核；Sevenhuijsen/Bubeck/Engster 只在 subSchools/detail 提及，不设条目。

## 5. 关键边界决定

a. **非本质主义（任务红线）**：吉利根的差异定性按原文谱系呈现——"theme, however, rather than of gender"（S2 §1a）→ 后期"人的声音"（S1 §2.2 转引 2023）。S3 教科书的"两性推理方式不同"框架如实注明为教科书转述，并与 S1/S2 的修正并陈；全文无一处"女性天生善于关怀"式概括；timeline/quotes 均不使用性别本质化措辞。
b. **科尔伯格不入 thinkers**：他是批评对象而非立场成员；其框架细节入 overview 与 S3 证据行，Gilligan→Kohlberg 批评因 relations[] 限定"本包 thinkers 之间"而改由 overview/timeline/证据行承担。
c. **与 U06 德性伦理包（同日已交付）**：SEP《Virtue Ethics》现行版（2026-05-03 修订）变体四分类**不含关怀伦理**——本包另行抓取复核，与 U06/review.md §3 的记录一致。任务问"SEP 2026 修订版是否将 care ethics 列为 virtue ethics 变体"：实查答案为**否**；"关怀伦理是德性伦理的一种/子集"是文献中另一说（S1 §2.4 转述 Groenhout 1998/Slote 1998/McLaren 2001/Halwani 2003；S2 §5），本包**两说如实并录**于 subSchools[4]、overview 第四段与 conclusion 第二段。另实查：SEP 现无独立 Ethics of Care 条目（`/entries/ethics-of-care/` 及 2024 夏/2021 冬两处存档路径均 404），关怀伦理的百科覆盖在《Feminist Ethics》§2.2。
d. **与 U07 义务论包**：2026-10-04 时 U07 目录未建（尚未交付）。对照暂以 SEP《Deontological Ethics》（2024-12-11 修订，全文无 care ethics 字样）+ S1 §2.4.1（关怀伦理对康德式义务论三点批评：绝对主义原则压倒处境、切割理性与情感、理想化行动者）+ S2 §5（兼容论）呈现，已入 evidenceLimits 提示 U07 建包后需回核。
e. **站内同名子项**：本包是立场深化包，不重复"伦理学"主条目通史；proposal 给出父子关系与五个 mention 文件的衔接建议。

## 6. 站内译名核对（grep philosophers.json）

- **站内已有**：吉利根（name 即「吉利根」，条目含 Carol Gilligan 全文简介）——thinkers[0] 直接沿用站内精确姓名。
- **站外人物（本包首引，建议编辑部核定译名）**：内尔·诺丁斯（Nel Noddings）、萨拉·拉迪克（Sara Ruddick）、安内特·拜尔（Annette Baier）、弗吉尼亚·赫尔德（Virginia Held）、伊娃·费德·基泰（Eva Feder Kittay）、琼·特隆托（Joan Tronto）、菲奥娜·罗宾逊（Fiona Robinson）；仅提及者：迈克尔·斯洛特（Michael Slote）、塞尔玛·塞文赫伊森（Selma Sevenhuijsen）、迪埃穆特·布贝克（Diemut Bubeck）、丹尼尔·恩格斯特（Daniel Engster）、塞拉·本哈比（Seyla Benhabib，通行译名"塞拉·本哈比"）。所有外文名在 thinkers/sub/works 保留原文。

## 7. 藏书关联

books.json grep『不同的声音/吉利根/诺丁斯』零命中，『关怀』命中皆为"人文关怀"类泛词——**无可挂书籍 ID，未造任何 ID**（proposal.linkageEvidence）。

## 8. 分歧、误差与取舍

1. **书目异文三处**：IEP 参考书目作 Noddings《Caring》1982、Tronto《Moral Boundaries》1994、书名 Starting *From* Home；SEP 书目与两源正文均作 1984 / 1993 / Starting *at* Home。本包从 SEP+正文（1984/1993/at），works 描述内注明冲突。
2. **拉迪克 1989 出版社两说**（The Women's Press / Ballantine Books），疑英美两版；正文不注出版社。
3. **术语纪律**：motivational displacement 与 ethical caring 未在 S1/S2 以原词出现（IEP 仅 engrossment、natural caring 原词），故**不列词条**，只在 engrossment 词条内描述机制——避免无据的"原典术语"呈现。
4. **引语全部为转引**：四条引语（特隆托定义、吉利根 1982 p.8、赫尔德 2006 p.168、诺丁斯"不同的门"）均经 S1/S2 转引核对，kind 字段如实标注转引链条，未核对原书版本页码。
5. **海因茨困境出处**：S3 标注 Kohlberg 1969, p.379；本包只在 works[0]/timeline 描述案例本身，页码不入正文。
6. IEP 书目中 Gilligan 1979 论文卷号"29"显系排印误（该刊 1979 年为 vol.49），timeline 只写年份与刊名，不写卷号。

## 9. 仍缺证据 / 建议

- 原典（Caring、Moral Boundaries、Globalizing Care、The Ethics of Care）原版未读，全部概念经 S1/S2 百科转述定位；若编辑部需要页码级引注，需图书馆核原书。
- Britannica 两条传记词条（403）与 PhilPapers 分类页（当日限流）建议复核时补。
- 吉利根生年 1936 仅据站内条目，外部来源未核。
- 科尔伯格"六阶段"完整名称、"84 名男孩"样本规模：常见转述，本包来源未核，正文刻意不写。
- U07 建包后：本包 §2.4.1 三点批评与 U07 的康德部分应互相引用对表。

## 10. 实际核读 URL 清单

成功核读（抓取全文/相关小节）：
1. https://plato.stanford.edu/entries/feminism-ethics/ （S1，全文）
2. https://iep.utm.edu/care-ethics/ （S2，全文）
3. https://openstax.org/books/psychology-2e/pages/9-2-lifespan-theories/ （S3，全文）
4. https://plato.stanford.edu/entries/ethics-virtue/ （分类与修订日期核对）
5. https://plato.stanford.edu/entries/ethics-deontological/ （修订日期与 care 字样核对）
6. https://iep.utm.edu/c/ 、https://iep.utm.edu/f/ （A–Z 目录定位条目）
7. https://iep.utm.edu/?s=care+ethics （搜索，仅导航命中）

404/被拒探针（未采用）：
- https://plato.stanford.edu/entries/ethics-of-care/ （404）
- https://plato.stanford.edu/entries/feminist-ethics/ （404，slug 误）
- https://iep.utm.edu/fem-eth/ 、/feminist-ethics/ 、/noddings/ 、/nel-noddings/ 、/gilligan/ 、/kohlberg/ （404）
- https://plato.stanford.edu/archives/sum2024/entries/ethics-of-care/ 、/archives/win2021/… （404）
- https://www.britannica.com/biography/Carol-Gilligan 、/biography/Lawrence-Kohlberg （403）
- 站内核对：app/public/philosophers.json、app/public/books.json、app/public/schools/data/school_{伦理学,女性主义,南岛哲学,北欧哲学,环境哲学,澳洲原住民哲学}.json、U06/packet.json、U06/review.md（只读）
