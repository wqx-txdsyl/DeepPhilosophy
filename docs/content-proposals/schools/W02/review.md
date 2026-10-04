# W02 亚里士多德学派（逍遥学派）— 资料包复核记录

- 复核日期：2026-10-04
- 复核人：zcode 内容研究员（自检，非独立同行评审）
- 复核方法：WebSearch 定位候选来源后，逐源用 WebFetch（SEP/IEP/Perseus/MIT/Britannica）与 web_reader（Britannica Peripatetic 页）打开并摘读相关段落；站内数据用 python3 实际解析 `app/public/philosophers.json`、`app/public/books.json` 及任务 evidence 字段所列四个学校 JSON。每条正文断言在 evidence.json 有对应记录。

## 一、同日草稿处置

开工前 `ls docs/content-proposals/schools/W02/` 为空，无同日草稿，本包为全新撰写，不存在保留/重写取舍。

## 二、边界决定

1. **古代学派 vs 接受史**：本包主体为古代吕克昂（亚里士多德→特奥弗拉斯托斯→斯特拉托）+ 公元前1世纪编订 + 希腊语评注传统；阿拉伯语与拉丁语接受只作关联章节。伊斯兰逍遥派（阿维森纳、阿威罗伊）以"阅读/接受"型 relations 收入，不写成师承——从斯特拉托（卒约前268）到巴格达逍遥派（9世纪）相隔约一千二百年，overview 与 conclusion 均明示此断裂。
2. **与 R13 的分工**（写入 proposal.divisionOfLaborWithR13）：拉丁西方只写到两个入口——波爱修斯逻辑翻译（S3）与13世纪"评论家"译名及1270/1277巴黎谴责（S4）；托马斯·阿奎那的系统吸收与托马斯主义体系全部留给 R13，本包 thinkers 不收托马斯。
3. **不代述站内子项**：伊斯兰哲学"东方/西方逍遥学派"、阿拉伯哲学"东方/西方逍遥派"、犹太哲学"犹太亚里士多德主义"、波斯哲学"法尔萨法"仅作互链建议（proposal.relatedExistingEntries），subSchools 中对应条目已加"站内另有专述"注记。迈蒙尼德不收入 thinkers（其主张未逐一核源），仅作互链。
4. **站内承接**：`school_古希腊哲学.json` 的 overview 已把"亚里士多德学派（逍遥学派）"列为下属主要流派，本包即该子流的独立展开，建议双向互链。

## 三、站内/站外人名处置

已 grep `app/public/philosophers.json`（键为姓名）核对：
- **站内沿用**：亚里士多德（前384—前322）、阿维森纳（10世纪后半叶—1037，生年有争议）、阿威罗伊（1126—1198）、德米特里乌斯（era"古希腊时期（约公元前4世纪-前3世纪）"，school 已标"逍遥学派/亚里士多德学派"）。
- **站外新增**（packet 使用，站内暂无）：特奥弗拉斯托斯、斯特拉托、亚历山大·阿弗罗狄西亚斯。三人分别有 S2/S7、S7、S3 支撑，如入库建议沿用本包译名。
- 波爱修斯在站内（era 480-524）与 S3（ca. 475–526）纪年略异，正文用"约475—526"并在此说明，未改站内数据。

## 四、来源核读清单（实际打开并读到相关段落的 URL）

1. https://plato.stanford.edu/entries/aristotle/ （SEP Aristotle，§1–§2；页面较长，本次核读覆盖生平、corpus 性质与著作分类）
2. https://plato.stanford.edu/entries/theophrastus/ （SEP Theophrastus，§1–§8）
3. https://plato.stanford.edu/entries/aristotle-commentators/ （SEP Commentators on Aristotle，Falcon rev. 2025，§1–§6）
4. https://plato.stanford.edu/entries/ibn-rushd/ （SEP Ibn Rushd，§1–§9.3）
5. https://plato.stanford.edu/entries/ibn-sina/ （SEP Ibn Sina，§1–§5）
6. https://iep.utm.edu/aristotle/ （IEP Aristotle，"Life and Lost Works"）
7. http://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0258%3Abook%3D5%3Achapter%3D1 及同书 chapter=2、chapter=3（DL 卷五 ch.1–3，Hicks 译，三页均核读）
8. http://classics.mit.edu/Aristotle/nicomachaen.1.i.html （NE 卷一，W.D. Ross 译，I.1 开篇与 I.7 功能论证核对原句；复核注：该原站路径现返回站点索引页，引文经官方 GitHub 镜像 TheMITTech/classics 逐字核对无误）
9. https://www.britannica.com/topic/Peripatetic （Britannica Peripatetic 词条聚合页，经 web_reader 核读原文段落）

**未能核读、已弃用的候选**：
- https://www.britannica.com/topic/Aristotelianism — WebFetch 403。
- https://www.britannica.com/biography/Strato-of-Lampsacus — Cloudflare"Just a moment"拦截页（curl 与 web_reader 均未过）。
- https://plato.stanford.edu/entries/ancient-commentators/ — 404（该 URL 不存在；正确条目为 aristotle-commentators，已核读）。
- Britannica 上"吕克昂讲座向公众免费开放"一句虽在已核读的 Peripatetic 页内，但与 SEP 表述层次不同，正文未采用该细节（见 evidenceLimits）。

## 五、分歧与不确定（详见 evidence.json uncertainty 与 packet.evidenceLimits）

- **编订前史**：涅琉斯承书、藏匿失散等出自斯特拉波/普鲁塔克晚期追记；本包只采 DL 章2（遗赠涅琉斯）与 SEP 评论家条目（阿佩利孔→提兰尼翁→安德罗尼柯）可证环节；"地窖藏书"不作事实陈述。
- **年代浮动**：特奥弗拉斯托斯两套纪年并存（约前371—前287 / 约370—前286）；斯特拉托掌门18年（阿波罗多罗斯）与 Perseus 导航标 286–268 有一两年出入，正文用"约"。
- **斯特拉托学说**：其"神=无意识自然力"等具体主张未在本次核读页面出现，未写入正文，仅保留 DL 可证的"物理学家"绰号与自然研究取向。
- **书名词源**：《形而上学》"置于《物理学》之后"的得名说未核得来源，未采；"Organon"中世纪标签有 S1 支撑。
- **文本性质**：存世论著是讲稿/工作稿、外传失传——S1/S6 双源支撑；"亚里士多德何时离开柏拉图主义"（Jäger/Owen）只作争论呈现，不作定论。
- **叙利亚语中转**：具体译者与书目未核得，正文只写"希腊典籍阿拉伯译本"（S5），不展开叙利亚路线。

## 六、质量标准核对

- 来源 9 个，类型覆盖 academic-encyclopedia（5 SEP + 1 IEP）、reference（Britannica）、primary-text（DL/Perseus、NE/MIT Classics），不互相转抄（SEP 五条目为独立撰写的不同条目）。
- 学说范围与人物归属：S1/S2/S3/S7 支撑；原典与具体论证：S8（功能论证原句）+ S4/S5（阿威罗伊、阿维森纳的原典工程）。
- 术语 8（6—10 ✓）、时间线 10（6—10 ✓）、著述 8（4—8 ✓）、人物 7（4—8 ✓）。
- 引语 2 条均核对到版本与位置（DL Hicks；SEP 转引 LongPhys proem），closingQuote 标 paraphrase。
- 两个 JSON 均通过 `python3 -m json.tool` 校验（见下）。

## 七、仍缺证据 / 待审读人定夺

1. 希腊语原文（1094a1 等）未直接核希腊文本，以通行英译为准；如需希腊语引文须另核 Burnet/OCT 版。
2. 斯特拉托生年、吕克昂建制的实质终结时点，史料不足以给出纪年，建议保持 evidenceLimits 表述。
3. 站内书《工具论》(b471f41a78de)《形而上学》(f11f1b13c278)《尼各马可伦理学》(e574c8e7f515)《政治学》(53b09f03e24e) 的 chapterCount 已从 books.json 核实，readingRoutes 已引用；是否以"站内可读书籍"卡片形式在条目页露出，由编辑定夺。
4. 互链落地（古希腊哲学 overview 内文、四个跨语种子项的反向链接）属编辑改动，超出本包文件权限，未执行。
