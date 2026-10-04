# U01 程朱理学 —— review.md

- 任务：U01 程朱理学（school 资料包）
- 交付日期：2026-10-04
- 状态：ready-for-review
- 工作目录：`/Users/sen/.zcode/worktrees/zcode-school-content/docs/content-proposals/schools/U01/`（本目录为开工时新建）

## 1. 旧稿处置

开工前 `ls` 目标目录：**U01 目录不存在**，无同日草稿需要处置。四个交付文件均为本次全新撰写。任务条目本身 status=pending，本包交付后建议协调方改为 ready-for-review。

## 2. 实际核读 URL 清单（全部于 2026-10-04 打开读到相关段落）

外部来源（packet.json sources S1—S17 与之完全一致）：

| id | URL | 方式 | 核读要点 |
|---|---|---|---|
| S1 | https://plato.stanford.edu/entries/zhu-xi/ | WebFetch | 生平年份、李侗师承、理气诠释、gewu qiongli、居敬、朱陆之争、元代科举 |
| S2 | https://iep.utm.edu/neo-conf/ | WebFetch | 北宋五子生卒、liyi fenshu、陆九渊/陈亮批评、朝鲜四七之辩、1905 |
| S3 | https://www.britannica.com/biography/Zhu-Xi | webReader | 生卒日期、1175 两事、1172/1177/1189 著作年、1241 入祀、朝鲜日本 |
| S4 | https://www.britannica.com/biography/Cheng-Hao | webReader | 程颢生卒、理想主义/理性主义对比、反对王安石、1606 二程全书 |
| S5 | https://zh.wikisource.org/wiki/%E5%AE%8B%E5%8F%B2/%E5%8D%B7427 | WebFetch | 师承原文、二程享年、周敦颐著述与从祀 |
| S6 | https://zh.wikisource.org/wiki/%E5%AE%8B%E5%8F%B2/%E5%8D%B7429 | WebFetch | 1196 党禁原文、1200 卒年、1241 从祀、四书立于学官 |
| S7 | https://zh.wikisource.org/wiki/%E5%9B%9B%E6%9B%B8%E7%AB%A0%E5%8F%A5%E9%9B%86%E6%B3%A8/%E5%A4%A7%E5%AD%B8%E7%AB%A0%E5%8F%A5 | WebFetch | 格物补传全文、经传结构；补传首句二次核对确认页作『言欲至吾之知』 |
| S8 | https://zh.wikisource.org/wiki/%E8%BF%91%E6%80%9D%E9%8C%84 | WebFetch | 淳熙乙未题词、十四卷卷次、朱吕合编 |
| S9 | https://zh.wikisource.org/wiki/%E4%BA%8C%E7%A8%8B%E9%81%BA%E6%9B%B8 | WebFetch | 乾道四年编定、二十五卷、三段卷次 |
| S10 | https://zh.wikisource.org/wiki/%E4%BA%8C%E7%A8%8B%E9%81%BA%E6%9B%B8/%E5%8D%B702 | WebFetch | 『天理云者』段定位与开头结尾确认 |
| S11 | https://zh.wikisource.org/wiki/%E4%BA%8C%E7%A8%8B%E9%81%BA%E6%9B%B8/%E5%8D%B722 | WebFetch | 『性即理』问答与气禀问答逐字 |
| S12 | https://zh.wikisource.org/wiki/%E6%9C%B1%E5%AD%90%E8%AA%9E%E9%A1%9E/001 | WebFetch | 理气、太极、理一分殊诸条逐字 |
| S13 | https://zh.wikisource.org/wiki/%E6%9C%B1%E5%AD%90%E8%AA%9E%E9%A1%9E/013 | WebFetch | 饮食/美味、天理存人欲亡两条逐字 |
| S14 | https://zh.wikisource.org/wiki/%E8%B1%A1%E5%B1%B1%E5%85%88%E7%94%9F%E5%85%A8%E9%9B%86_(%E5%9B%9B%E9%83%A8%E5%8F%A2%E5%88%8A%E6%9C%AC)/%E5%8D%B7%E7%AC%AC%E4%B8%89%E5%8D%81%E5%85%AD | WebFetch | 鹅湖年谱原文（朱亨道书、和诗） |
| S15 | https://zh.wikisource.org/wiki/%E4%BA%8C%E7%A8%8B%E9%81%BA%E6%9B%B8/%E5%8D%B711 | WebFetch | 『天者理也』；确认天理云者长段不在卷 11 |
| S16 | https://zh.wikisource.org/wiki/%E6%9C%B1%E5%AD%90%E8%AA%9E%E9%A1%9E | WebFetch | 黎靖德咸淳庚午编定、140 卷 |
| S17 | https://zh.wikisource.org/wiki/%E5%A4%AA%E6%A5%B5%E5%9C%96%E8%AA%AA | WebFetch | 首句、五行段、主静段逐字 |

未采信：SEP 无二程专门条目（/entries/cheng-brothers/ 返回 404，已实测）；Britannica Cheng Yi 条目因 web_reader 限流未单独核读，程颐信息由 IEP（生卒）+宋史（卒年）+SEP（性即理英译）+维基文库卷 22（原文）交叉覆盖，已在 evidenceLimits/review 记录。

## 3. 边界决定

1. **与儒家条目分工**：儒家包处理通史与『程朱理学为官学』制度节点（school_儒家.json 已有该表述）；本包只做程朱一系的学派内部结构与论证，不重复儒家总览。
2. **与父包『宋明理学』分工**：本包是其 subSchools[1] 同名子项的深化扩展，建议父包子项保留一句话索引并指向本包；『濂洛关闽』『关学』『湖湘学』子项不在本包展开（张载仅出现在谱系与从祀语境，不立 thinker 条目——他是气学/关学一侧，站内父包已有『关学』子项）。
3. **与 U02 陆王心学包接口**：已接住。鹅湖之会引文以《象山先生全集》卷三十六年谱朱亨道书为对齐基准（本次独立核读原页，与 U02 packet 引文逐字一致）；程朱侧立场写清三件事——朱熹教人之法（泛观博览而后归约）、朱陆互评（太简/支离）、朱熹归后三年和诗（旧学商量加邃密，论辩之外的学术敬意）。陆九渊不列入本包 thinkers（契约 from/to 约束），只在 timeline/quotes/conclusion 接触；心学一侧（心即理、格竹、晚年定论之争）明确移交 U02。
4. **程颢/程颐分系**：明道下开心学、伊川下开理学是后世学术史回溯（Britannica 表述 + IEP 参考文献 Graham 专著），不写成当时已有的组织分派；overview 与 conclusion 均按回溯判断措辞。
5. **跨传统/跨地域**：朝鲜四七之辩、日本德川接受按 IEP/Britannica 接受史呈现，列为 subSchools『分支（跨地域接受）』，不写成师承或影响链；未凑『东方+西方』配额。
6. **时间线性质**：以学派内部文献与争论节点组织（受业、编书、论辩、党禁、卒、从祀、科举采行），政治事件（庆元党禁）以宋史明文为限，不混编 general 政治史。

## 4. 查重与站内核对记录

- 站内人名核对：`app/public/philosophers.json`（dict 按中文名索引）含朱熹、程颢、程颐、周敦颐、张载、陆九渊（thinkers 全部使用站内精确姓名）；邵雍、吕祖谦、张栻、罗钦顺等不在库（本包未为其立条目）。
- 站内父包核对：`app/public/schools/data/school_宋明理学.json` subSchools 索引 0—4（濂洛关闽/程朱理学/陆王心学/关学/湖湘学），『程朱理学』现为一句简介。
- 站内提及相关：school_儒家.json、school_明清实学.json、school_乾嘉朴学.json、school_现代新儒家.json 均有『程朱理学』字样（任务 evidence.mentionFiles 一致），已在 proposal.existingEntries 逐条说明关系。
- 藏书核对：`app/public/books.json` 检索朱熹/二程相关，命中《大学章句集注》（id 4c5aaf145298，朱熹，epub，13 章，epub 原著非占位），已写入 proposal.bookSuggestions；未发现二程原著藏书，未虚构任何站内书籍 ID。
- 与同日其他包：U02（陆王心学）已核读其 packet.json，接口见上；U03 目录存在但与本任务无涉，未读取其余内容。

## 5. 复核方法与来源冲突处置

- 方法：WebSearch 仅用于找候选 URL（SEP 二程条目 404 的确认）；所有入 sources 的 URL 均实际打开核读；汉文原典引文逐字抄录并保留繁体与记录者名（如『節』『椿』『唐棣彦思编』）；英文百科核对关键短语与章节标题供 locator。
- 冲突处置（3 处）：
  1. 格物补传首句：维基文库作『言欲至吾之知』，通行整理本作『致』——引文避开该句（evidenceLimits）。
  2. 朱熹中进士年龄：SEP 19 岁 vs Britannica 18 岁（中西纪年差异）——不写具体年龄。
  3. 《近思录》条目数：提要页作 662 条，通行计数常作 622 条——不写条数。
- 引用纪律：SEP 对『理先气后』的诠释、Britannica 对兄弟差异的概括均明确归属来源，不冒充哲学家原话；『居敬』未在已核原典页定位到字面出处，该 cihai 条目 def 只依 SEP 叙述并注明。

## 6. 仍缺证据（不阻塞交付，均已入 evidenceLimits）

- 『天理二字却是自家体贴出来』（《二程外书》）未核得可靠在线文本，未采用。
- 『月印万川』喻的原始出处（《朱子语类》某卷）未定位，未采用。
- 元代恢复科举具体年份（1313/1315）未核，时间线只写『14 世纪起』。
- 道南谱系中罗从彦环节未核，只写『程颐—杨时一系的李侗』。
- Britannica Cheng Yi 条目未单独核读（限流），现有交叉覆盖足以支撑本包结论。

## 7. 数量自检

术语 10（契约 6—10）、时间线 10（6—10）、著述 6（4—8）、人物 4（4—8）、关系 5、子项 6、引文 5+主引+closing。来源 17 个（≥3，含学术百科 2、参考百科 2、原典 13；学说范围与人物归属由 S2/S5 支撑，原典与论证由 S7—S17 支撑，互不转抄）。evidence.json 46 条，覆盖全部时间线节点、术语、著述、人物、关系与关键引文；fieldPath 均为 JSON Pointer；sourceRefs 无悬空引用（脚本校验）。
