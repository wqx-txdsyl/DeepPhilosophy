# B09 萨迦派思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B09`（proposedKind=school，P1-content-packet，coverage=mentions-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定与 T01／B04 分工

1. **T01 总览 → B09 专条**。T01《佛教哲学》藏传部分仅参考级（en.wiki Tibetan Buddhism：四派年代"萨迦 1073"等），其 evidenceLimits 明言藏传细节"一律不展开，留给地区条目"。B09 为萨迦的首个专门深度条目，全部外部来源为本日新抓（SEP Tsongkhapa 106KB 独立重抓，未复用 T01/B04 缓存片段）。1073 年建寺年份两包一致。
2. **与 B04（佛教量论）的分工**。B04 承载印藏量论通线，其中两句涉及萨迦（"萨迦量论传统主要以萨迦班智达著作为基础"；格鲁/萨迦对法称推断诠释的分歧）。B09 独立重抓 SEP Tsongkhapa 全文并深挖萨迦侧新增覆盖：热达瓦（1349—1412）为宗喀巴"未来的主要上师"、spros bral"后来被立为萨迦正统观点"、果让巴论战及近代研究书目。两包互为导流，不重复。
3. **与站内《西藏哲学》的关系**。该条目已有萨迦的一行式内容（thinker 行、两条"道果法"cihai、works《量理宝藏论》、quotes 一条 paraphrase、relations"萨迦派→噶举派 对立"）——本包属"已有子项复用并深化"，为其补齐出处与逐字定位，不重复造页面。"萨迦派→噶举派 对立"建议按证据细化为**义理批判**（Sapan 对 dkar po chig thub 的抨击，点名冈波巴/张·察巴）＋**寺际竞争**（蒙哥护止贡、1252 诏令），非全派对立。
4. **范围约束执行**：道果、量论、批判哲学、支派经院传统为主体；萨迦—蒙古政治史压缩为 timeline 两个节点（1244–1247、1264）一笔带过；不与整个西藏哲学混同（宁玛/噶举/格鲁各归其条）；宁玛、噶举人物一律不入 thinkers。

## 二、任务要点逐项核对

| 任务要点 | 处置与证据 |
|---|---|
| 道果（Lam 'bras）教法 | S4 全文核读：定义（果在道中、summum bonum）、《金刚句》根本文本、口传保密性质、tshogs bshad/slobs bshad 两线、扎巴坚赞五阶段；S2 补两线与喜金刚续宗依 |
| 萨迦班智达量论与《萨迦格言》 | S1（萨迦量论传统定位）、S3（批判智军、五部大论、白法批判）、S8（量理宝藏论第四章三喻藏文＋英译逐字）、S11（Leh 2003 版《Treasury of Good Sayings》：扎什伦布版底本、Dmar ston 注、十章目录、偈[10]英译逐字） |
| 与止贡派论战 | ⚠ 本轮来源的"止贡"材料有限：S3 仅见 1240 年入侵中止贡寺"ostensibly"得免、Petech/Chang 两说、蒙哥改护止贡与 1252 诏令。义理侧改用 S3+S9 可靠支撑的对**噶举"白法"**的批判（点名冈波巴 1079–1153、张·察巴 1123–93；第 161 颂逐字）。"三律仪论为止贡所请而作"与 1290 年止贡之乱**未核到来源，不写**（evidenceLimits 第 8、9 条） |
| 俄尔钦与鄂尔寺量论课程传统 | S5（Ngorchen 1382–1456/57、1429 建 Ngor Ewaṃ Choden、文集近 200 题、《鄂尔文集》20 卷）；量论课程线由 S1"两大主导传统"句承载；鄂尔寺具体课程科目未核到，不写 |
| 萨迦-蒙古关系一笔带过 | timeline 两节点＋overview 末段一句；**致蕃人书真伪之争**如实记录（S3：1977 年研究断 Godan 召书为后世伪造；S7：Jackson 1986《A Late and Dubious Addition》）——站内 philosophers.json 萨迦班智达条以《致蕃人书》为定论叙述，接入时建议加注 |
| 昆氏家族传承 | S2 世袭句＋S3"abbotship on a hereditary basis since 1073"＋五祖名单；八思巴为站内人物（实查） |

## 三、查重与既有内容

- 任务 JSON：exactTopLevelEntries／exactBranches／relatedBranches 均空；mentionFiles 2 项（西藏哲学命中"萨迦派、Sakya"；蒙古中亚哲学命中"萨迦派"）。站内无同名顶级条目或子项，coverage=mentions-only 处置成立，本包为首个专门条目。
- **人物**（python 实查 philosophers.json）：站内 2 人入 thinkers——**萨迦班智达**（era 1182–1251，与本包一致）、**八思巴**（条目键名"八思巴（Phags-pa）"，era 1235–1280）。**任务提示"八思巴大概率站外"与实查不符，站内实有**，已按站内键名处理并在 evidenceLimits 记录。蒋贡康楚·罗卓泰耶 school 字段含萨迦派（利美运动），属跨派运动不入本包。站外 6 人：贡噶宁波、索南孜摩、扎巴坚赞、俄尔钦·贡噶桑波、果让巴·索南僧格、热达瓦·宣奴洛追——按契约保留准确姓名并在 sub 标注。站内宗喀巴条 bio 的"师从萨迦派高僧仁达瓦·宣奴洛追"与 S1 逐字侧证（Red mda' ba，1349–1412）吻合；汉译名"仁达瓦/热达瓦"建议接线时统一。
- **书籍**（python 实查 books.json）：无萨迦/藏传专门藏书；仅建议通史关联蒋维乔《中国佛教史》1201d003be31（与 B05/B06 同例，未核读内容）。
- **人物姓名纪年精度**：站内萨迦班智达条目"13世纪"（school_西藏哲学.json thinker 行）粗于 philosophers.json 的 1182–1251，本包从后者。

## 四、分歧与争议的处理

- **生卒异说并陈**：卓弥 993–1077?（S4 正文）vs 992–1074（S4 系谱表）；Gayadhara d.1103 vs 994–1043（S4 同条内部矛盾）；萨班卒日 12 月 28 日（S3 导语/S7）vs 11 月 28 日（S3 正文）vs《漢藏史集》十一月十四日；俄尔钦 1456（S5）vs 1457（S2）；察尔钦 1496–1560 vs 1502–1556（S2）。主纪年只用到年份精度，timeline 不造精确月日。
- **支派分类两说**：en.wiki 三支 tshar/ngor/gong dkar（S5）vs zh.wiki"哦巴、總巴、察巴"（S6）——subSchools[2] 以"分类学争议"条并陈，不裁断。en.wiki"85% of the Sakyapa school [citation needed]"带维护标记，**数字不采用**。
- **zh.wikipedia 萨迦派条目带"此條目没有列出任何参考或来源（2025年10月15日）"横幅**：非 B05 式 LLM 横幅，但按同方向从严——其中白衣/红衣三祖说、花教三色墙说、宣政院"萨迦王朝"（1268–1351）、大乘法王封号等仅作参考级定位，不单独支撑断言。
- **致蕃人书与 Godan 召书的真伪**：S3"the surviving letter of summons attributed to Godan is in fact a later fabrication"（1977 年研究）；S7 Jackson 1986 伪托说整段。本包只写事件层（1244 应召、1247 会面），文献层争议入 evidenceLimits。"十三万户 temporal authority"条目自注"not entirely correct"，不写。
- **白法批判的适用范围**：S3（转述 Cabezón）点名冈波巴与张·察巴，但未区分二人体系与被批判的极端化表述——packet conclusion 显式警告"不放大为否定大手印"。
- **站内 cihai"道果法"条 source 栏"萨迦班智达《三现分》"**：《三现分》文本传统上多系后世（俄尔钦等）整理教授，站内归属表述未经本包来源证实——已在 evidence.json relatedExisting/0 uncertainty 备案，由 Codex 复核。
- **早期道果传承系谱**（S4 Early lineage 节）自带"does not cite any sources（January 2024）"横幅——该系谱表仅用于暴露内部矛盾（Gayadhara/Drogmi 生卒），不作正面证据。

## 五、原典与文本凭据的层级

1. **节偈级（藏文原文＋英译）**：Lotsawa House 三页——量理宝藏论第四章三喻（S8）、三律仪第 161/255 颂（S9）、离四贪着疏（S10），均含藏文威利/藏文原文与 Adam Pearcey 英译、CC BY-NC 4.0、ISSN 2753-4812。本包引语一律以这三页＋S2 四颂英译为 verbatim 凭据，packet 中汉文均为转述（kind=paraphrase，与站内《西藏哲学》同类处理一致）。
2. **全书扫描级**：archive.org《Treasury of Good Sayings》（Jamspal 编，Rhoton/Jamspal 译，Leh 2003，ISBN-81-901230-3-3）——书目信息与英文翻译短句可用（偈[10]逐字）；**藏文页 OCR 全部乱码，不可用作藏文文本凭据**；2003 年版权书只作短引不整篇复制。
3. **未获文本凭据**：《金刚句》《量理宝藏论》《三律仪辨别论》全书；维基文库《薩迦格言》《量理寶藏論》两页均为空壳（"此页面目前没有内容"，实查）；站内"《量理宝藏论》十一品"之说未在外部来源核到。
4. **口传限度**：S4 明言道果"some oral teachings remain unwritten, known only by lamdré lineage holders"——道果修行论没有文本是**教法特征**而非研究疏失，evidenceLimits 第一条明示。

## 六、复核方法与结果

1. curl 全文抓取 8 个网页＋3 个 Lotsawa House 页＋archive.org metadata/OCR＋Sakya Research Centre，全部关键引文（中英藏）在全文中逐字定位命中（脚本回验 72 处抽检：68 处连续逐字命中，4 处仅差 HTML 去标签产生的括号旁空格——如"( Sa skya )"与"(dkar po chig thub)"——属转换空白差异，内容逐字一致）；检索摘要一律不作为依据。
2. evidence.json 共 83 条记录：overview 14、conclusion 3、thinkers 8、relations 8、timeline 12、cihai 12、works 9、subSchools 4、引语 7（quote 1＋quotes 5＋closingQuote 1）、coverage/relatedExisting/书籍/人物核对/失败备案 6。每条含 verbatim locator；查站内文件者 sourceRefs 留空并在 locator 注明实查文件（B04/B06 同例）。全部 fieldPath 经脚本回解析到 packet.json 对应节点（83/83 通过）。
3. 数量：来源 12（学术百科 1 ＋ 学术数据库 1 ＋ 原典节译 3 ＋ 原典扫描 1 ＋ reference 6）——S1/S12 支持学说范围与归属，S8/S9/S10/S11 支持原典与论证，S2–S7 为 reference 级并声明用途（S6 带无来源横幅从严）。人物 8（站内 2＋站外 6）、时间线 12、术语 12、著述 9、分支 4、关系 8、引语 1+5+1——在契约参考区间内。
4. 结构契约自检（脚本实查）：两个 JSON 经 `python3 -m json.tool` 校验通过；relations 八条 from/to 端点逐一比对等于 thinkers[].name 精确字符串；sourceRefs 全部可解析至 sources[].id；accessedAt 均为 2026-10-04；readingRoutes 与 evidenceLimits 在 packet 顶层（school 内无副本）。
5. **引语性质自检**：全部引语条目（quote/quotes×5/closingQuote）kind 均为 paraphrase——因无藏汉对勘文本，不作逐字直引冒充；每条 author/quoteAuthor 字段注明英译出处与转述性质；无凭空术语、无虚构子派（总巴/宫卡两说并陈、85% 数字弃用）。

## 七、仍缺证据（与 packet.evidenceLimits 对应）

- 道果"三现分/三续"结构：站内已有名目，本轮外部来源未逐字核到（S4 未及此层），不展开。
- 《金刚句》《量理宝藏论》《三律仪辨别论》全书文本；萨迦格言通行九章/十章章数异同。
- 止贡-萨迦义理论战专文（1290 止贡之乱亦未核）；鄂尔寺课程具体科目；果让巴著作内部结构（仅记 Cabezón & Dargyay 2007、Thakchöe 2007 存在）。
- Treasury of Lives（Heimbel/Townsend 的 Sapan 与 Ngorchen 学术传记）Cloudflare 403 未读成；Rigpa Wiki 403；Study Buddhism 目标页 404。
- 热达瓦、索南孜摩的个人著述细节；萨迦班智达与 Śākyaśrībhadra 合译的版本学细节。

## 八、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/tsongkhapa/ （curl 全文 106KB；本日独立重抓，另测 /entries/tibetan-philosophy/ 为 404）
2. https://en.wikipedia.org/wiki/Sakya （curl 全文 399KB）
3. https://en.wikipedia.org/wiki/Sakya_Pandita （curl 全文 325KB）
4. https://en.wikipedia.org/wiki/Lamdre （curl 全文 217KB）
5. https://en.wikipedia.org/wiki/Ngorchen_Kunga_Zangpo （curl 全文 84KB，stub 条目如实降级）
6. https://en.wikipedia.org/wiki/Drikung_Kagyu （curl 全文，核后未用作断言来源——无萨迦论战内容）
7. https://zh.wikipedia.org/wiki/萨迦派 （curl 全文 108KB；带"没有列出任何参考或来源"横幅，从严使用）
8. https://zh.wikipedia.org/wiki/萨迦·班智达 （curl 全文 107KB）
9. https://lotsawahouse.org/tibetan-masters/sakya-pandita/tsema-rikter-quotations （全文，藏文＋英译逐字）
10. https://lotsawahouse.org/tibetan-masters/sakya-pandita/domsum-rabye-quotations （全文，两颂藏文＋英译逐字）
11. https://lotsawahouse.org/tibetan-masters/sakya-pandita/parting-four-attachments （全文）
12. https://archive.org/details/GoodSayingsOfSakyaPandita ＋ /metadata/ ＋ /download/.../GoodSayingsOfSakyaPandita_djvu.txt （metadata＋OCR 367KB；藏文 OCR 乱码如实备案）
13. https://sakyaresearch.org/persons/27 （全文，人物数据库）
- 探测未成：treasuryoflives.org（三条 URL 均 403 Cloudflare）、rigpawiki.org（403）、zh.wikisource 薩迦格言/量理寶藏論（空页）、studybuddhism.com 目标页（404）、plato.stanford.edu/entries/tibetan-philosophy/（404）。
- 说明：SEP tsongkhapa 条目 B04 工作曾核读两处片段；本包按 B06 先例当日独立重抓全文深挖（多轮 grep：萨迦量论传统、热达瓦、spros bral 正统说、果让巴、多波巴等），未复用 B04 片段。
