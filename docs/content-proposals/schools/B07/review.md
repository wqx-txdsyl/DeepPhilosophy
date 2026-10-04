# B07 禅宗思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B07`（name 禅宗思想，proposedKind=school，P1-content-packet，coverage=related-branches-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定与 T01 分工

1. **T01 总览 → B07 专条的明确分工**。T01《佛教哲学》是跨地区问题地图，禅宗内容仅四处：thinkers 慧能（638—713）、works《六祖大师法宝坛经》、cihai「自性（禅宗义，坛经语）」、subSchools「禅（坛经传统）」；其 evidenceLimits 未涉禅宗史。B07 恰好补齐整个历史—义理纵深：达摩传记层、东山法门、南顿北渐、洪州宗、五家七宗、公案与看话/默照、不立文字的哲学问题。建议 Codex 接入时两包互设导流：跨传统脉络归 T01，禅宗自身的传承、文本与实践归本包。T01 已核的《坛经》定位（S9）本包全部复用有效——**本日 T01 复核中经 curl 逐字核读**（第二研究员曾改正一字：「何期自性能生万法」，无「性」字），本包另做了**独立重抓**，两次结果逐字一致，可放心互引。
2. **传记层与历史层分开**。达摩的一切具体事迹按「传说层」呈现（S1：inventions of tradition；S2 Ferguson「传说期存世文献极少」）；《坛经》两偈相对、传衣叙事按「宗教叙事」呈现；timeline 只设「传说期」一个模糊节点，不给达摩任何具体年份。
3. **学说阵营／修行进路／宗派／地域传统分开标注 kind**。北宗/南宗标宗派，看话/默照标学说进路，日本禅标地域传统——避免读者把神会的论争建构（「南顿北渐」）误读为客观的教义分类学。
4. **「宗风」描述不写**。任务条目明示五家「宗风」描述多为晚期溯构；本包来源（S2）只有五家的名号、人物与年代，无一家提供宗风概括的原始文献。本包 subSchools 对五家只写名号、世系、年代与建制命运，宗风铺陈（临济痛快、云门函盖之类）一律不写，evidenceLimits 有对应声明。

## 二、查重与既有内容

1. **任务 JSON 核对**：exactTopLevelEntries／exactBranches 均空；relatedBranches 2 项（隋唐佛学 → 禅宗南宗 subSchools[3]、禅宗北宗 subSchools[4]）；站内无同名顶级条目。**coverage=related-branches-only 处置成立**，本包为禅宗主题的首个专门深度条目。
2. **站内《隋唐佛学》实查**（2026-10-04 python 读 `app/public/schools/data/school_隋唐佛学.json`）：subSchools[3] 禅宗南宗（era 唐至五代）、subSchools[4] 禅宗北宗（era 唐），另有 cihai「禅宗」「顿悟」——**「顿悟」重复两条**（一条带英文名 "Sudden Enlightenment" 一条不带），属旧数据清理点，已在 packet.proposal.relatedExisting 与 evidence.json 记录定位，由 Codex 清理。两分支描述（南顿北渐对峙）可用本包 S2「论争性夸张」的学术定性深化。
3. **T01 实查**（python 读 `docs/content-proposals/schools/T01/packet.json`）：禅宗内容如上四处，无冲突、无重复造页风险。
4. **mentionFiles 词形命中排除**：任务 JSON 列了 15 个 mentionFiles，绝大多数是检索词形误命中，逐一判断如下——「Chan」在北极原住民哲学、玛雅哲学、贝叶斯主义、维新派、法兰克福学派等条目为英文转写或人名片段（如 Chan 兽名/人名），与禅宗无关；「Zen」在德国古典哲学、东欧斯拉夫哲学、现象学、哲学人类学等为引用语境；「禅宗」在日本哲学、韩国哲学、马克思主义哲学的中国化、哲学入词等为跨条目提述。以上均不构成禅宗的既有专门覆盖。
5. **书籍查重与词形排除**（books.json python 实查）：站内**没有任何禅宗原典或研究书**。任务提示的查重线索中，《禅与摩托车维修艺术》（ba0977da0443，tags 含「禅宗」）是波西格哲学小说，属**词形相近误归类**，本包不作关联并在 evidenceLimits 声明；南怀瑾合集（a26240ee8f45）、洞见（958d02ba12f5）、僧侣与哲学家（077532e4515e）均非禅宗专门藏书，不关联。唯一建议关联为《中国佛教史》（1201d003be31，蒋维乔，佛学通史，未核读内容，仅作通史关联）。

## 三、分歧与争议的处理

- **弘忍生卒**：S2 作 601—674，S3 作 602—675，差一年——timeline 并陈两说，不采单一。
- **神会生卒**：仅 S2 作 670—762（生年学界本有异说）；S3 无生卒。本包按 S2 记并在 evidenceLimits 声明。
- **神会大会年份（本包最重要的纪年发现）**：zh.wiki 原文作「唐玄宗開元二年（730年）」，但**开元二年当 714 年，与括注 730 年自相矛盾**（学界通说的滑台无遮大会在开元二十年前后，本包来源未核及，不作此断言）。本包 timeline 只作「8世纪前中期」，不采任何具体年份。
- **道元入宋年份**：S3 作 1223 年入宋（从天童如净），S2 作 1215 年 journeyed to China——两源矛盾，timeline 依 S3 作 1223 并注明 S2 异说。
- **「平常心是道」归属**：本包两个已核原典（《景德傳燈錄》卷十、《無門關》第十九则）均为**南泉普願答赵州从谂**语；通行说法常直接归马祖，本包无马祖亲说此语的逐字来源，不作此归属，行文以「马祖门下传承」呈现。
- **「不执文字不离文字而为道用」**：在《景德傳燈錄》卷三中是**门人道副**的回答（得「汝得吾皮」之评），不是达摩亲语；本包以之证宗门「不废文字」的态度，行文已按此呈现，evidence.json note 有记录。
- **「大慧烧毁碧岩录刻板」**：S2 原文为 "is even said to have burned"——传说性表述，本包照此呈现（「被说为烧毁」），不作事实断言。
- **两原典异文**：「平常心是道」对话在《景德傳燈錄》（廓然虛豁）与《無門關》（廓然洞豁）文字小异；「不思善恶」段在两本亦有语序差异——引文各从其本，不作底本校勘结论。
- **「达摩」同名核对**：philosophers.json 全表（737 人）python 实查**无任何条目含「达摩/達摩」**，无同名冲突；站内禅宗相关人物为慧能（638-713年）、神秀（约606-706年）、道元（1200–1253，曹洞宗（禅宗）），另有龙树、智顗可作背景关联。

## 四、复核方法与结果

1. curl 全文抓取（全部独立重抓，未复用 T01 片段）：SEP buddhism-chan（84KB）、en.wikipedia Chan Buddhism（1.4MB）、zh.wikipedia 禪宗（876KB）、维基文库《六祖大師法寶壇經》（103KB）、《景德傳燈錄》目录页＋卷003/005/006/010/012（共约 670KB）、《碧巖錄》目录页＋卷第一（180KB）、《無門關》（112KB）。检索摘要一律不作为依据；所有关键引文（中英文）均在抓取文本中逐字定位命中。
2. evidence.json 共 90 条记录，覆盖 overview 13、conclusion 3、thinkers 9、relations 8、timeline 13、cihai 10、works 7、subSchools 12、主引语 1、quotes 7、结引语 1、proposal/coverage/书籍/人物核对 5；每条含 verbatim 定位；查站内文件者 sourceRefs 留空并在 locator 注明实查文件。全部 fieldPath 经脚本回解析到 packet.json 对应节点（NONE unresolved）。
3. 数量：来源 7（学术百科 1＋reference 2＋原典 4）、人物 9、时间线 13、术语 10、著述 7、分支 12、关系 8——S1 支持学说范围与学术定性，S4—S7 支持原典与具体论证，符合「至少1个来源支持学说范围、1个支持原典/论证」的硬性要求。
4. 两个 JSON 经 `python3 -m json.tool` 校验通过；relations 八条端点经脚本逐一比对，均精确等于 thinkers[].name 字符串（NONE mismatch）；sourceRefs 全部可解析（NONE unresolved）；accessedAt 全为 2026-10-04。

## 五、站外人物

philosophers.json python 实查后，以下 7 名 thinker 为站外人物，按契约保留准确姓名、sub 字段标注「站外人物」，未改动哲学家名单：菩提达摩、弘忍、神会、马祖道一、临济义玄、大慧宗杲、宏智正觉。另有站外原典人物（南泉普願、赵州从谂、圆悟克勤、无门慧开、雪窦、荣西、如净等）仅在 timeline/cihai/works/quotes 中出现，未设 thinker 条目，个人生卒凡无来源一律不写（见 evidenceLimits 第 10 条）。

## 六、仍缺证据（与 packet.evidenceLimits 对应）

- 敦煌本《坛经》原文：未核读（两偈有无异同等版本学问题不作断言）。
- 《景德傳燈錄》维基文库本「未完成」：仅卷 003/005/006/010/012 已录入，其余未读；CBETA JS 渲染抓取失败，未做第二藏经对勘。
- 《临济录》《大慧语录》《默照铭》《五灯会元》原文：未核读；大慧两段引语系经 zh.wiki 转手（packet quotes[6].exp 与 evidence 已声明）。
- 黄龙慧南、杨岐方会、圆悟克勤、雪窦、永明延寿、知讷、荣西等生卒：无核读来源，不写。
- 五家「宗风」概括（《人天眼目》一类文献）：未核读，不写。
- 禅净合流机制、禅儒道互动、禅的西方接受与日本哲学化：超出本包范围，不展开。

## 七、实际核读 URL 清单（2026-10-04，全部 curl 全文＋逐字定位）

1. https://plato.stanford.edu/entries/buddhism-chan/ （SEP Chan Buddhism, Hershock；84KB；注：/entries/chan-buddhism/ 为 404，实际 slug 为 buddhism-chan）
2. https://en.wikipedia.org/wiki/Chan_Buddhism （1.4MB）
3. https://zh.wikipedia.org/wiki/禪宗 （876KB）
4. https://zh.wikisource.org/wiki/六祖大師法寶壇經 （103KB；T01 同日复核曾 curl 逐字核读并改正一字，本日独立重抓一致）
5. https://zh.wikisource.org/wiki/傳燈錄 （重定向自景德傳燈錄；目录页，核载道原/北宋/1004年/三十卷）
6. https://zh.wikisource.org/wiki/傳燈錄/003 、/005 、/006 、/010 、/012 （達磨、慧能、馬祖、趙州南泉、臨濟五章全文）
7. https://zh.wikisource.org/wiki/碧巖錄 （目录页，核载圓悟克勤/宋朝/1125年）＋ /碧巖錄/卷第一 （第一、二则全文）
8. https://zh.wikisource.org/wiki/無門關 （全文；第一/十九/廿三则逐字命中）
- 探测后未用：https://plato.stanford.edu/entries/japanese-zen/ （已抓 130KB，通篇为日本禅人物，Chan 史内容极少，不作核心来源）；SEP 无 slug "chan-buddhism"（404）；站内链接勘验仅用本地文件。
