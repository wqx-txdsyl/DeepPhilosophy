# B11 净土思想 资料包审读记录（2026-10-04）

## 一、范围与边界

- **条目定位**：tradition-overview（任务条目 proposedKind 同）。净土在印度是无宗派归属的大乘佛土愿生思想（S1），在中国前近代多为依附诸宗的"法门（dharma-gate）"（S1 Principles 节引 Jones），只有日本镰仓期才出现独立教团（S1 §Independent sects、S5）——故以传统总览呈现，宗派史由 subSchools 分层承载（慧远流／善导流／禅净合一／日本净土宗／净土真宗／藏传实践），任一单点"school"命名都会截断其余语境。
- **地域/传承边界**：南亚源头（三经成立、二论归署）—中国化（昙鸾—道绰—善导的他力化论证；结社与称名的民间组织化；宋以后禅净合一）—日本宗派（法然、亲鸾）—藏传实践取向（一句定位）。朝鲜（元晓/憬兴仅作《无量寿经》注疏背景）、越南净土史、天台净土学专深、日莲对念佛教的批评战不展开。
- **不写的内容**：中国"净土宗"作为制度教团的叙事（S1 Jones 说：前近代无独立宗团，'十三祖'为宋以后层层追认、印光定型的建构）；慧远"净土初祖"作定论（S1 Jones 质疑 + S7"不能证实也"双存疑）；善导柳树舍身传说（S7 已考订"其非信史"）；道绰住玄中寺细节（未获独立来源）；站内《隋唐佛学》quotes 中署名善导的"念佛一声，罪灭河沙"（本包全部来源均无此句，不继承，见第四节）。
- **任务边界纪律自查**：中国传承（慧远—庐山结社／昙鸾—道绰—善导法门系）与日本传承（法然净土宗、亲鸾净土真宗）分立呈现，未统一写成无差别宗派；实践与论证（念佛形态史、二道二门判教、别时意论辩、心土之争、自他二力）与宗派组织史分层叙述；人物年代一律用来源给出的证据范围（慧远 334—416、昙鸾 476—542、道绰 562—645、善导 613—681、法然 1133—1212、亲鸾 1173—1263），无据年代不伪造（三经成立只写"约5世纪前"）。

## 二、与既有条目的查重和分工

- **站内 catalog**（app/public/schools/catalog.json，schools 111 项 python 实查）：无净土同名顶级条目——本包为净土思想首条，无同题重复。
- **《隋唐佛学》**（app/public/schools/data/school_隋唐佛学.json 实查）：thinkers 已有善导（613-681，sub"净土宗"，key"持名念佛"，works《观无量寿经疏》）、works 已有《观经疏》、timeline 已有"682 善导圆寂……后尊为净土宗二祖"、cihai 已有"净土""念佛""称名念佛"三词条、quotes 有署名善导《观经疏》的"念佛一声，罪灭河沙"（kind=paraphrase，站内自标）。**分工**：该条目在八宗框架内给净土位置；本包承担跨朝代全景与他力化论证结构，善导思想深度由本包展开。既有条目不修改；"罪灭河沙"一句建议 Codex 复核（本包 7 源含蒋维乔对《观经疏》的详述均无此句）。
- **《宋明理学》**（同目录实查）：relations 有一处 {from:'善导', to:'净土宗', type:'开创', label:'创立'}——善导属《隋唐佛学》人物，此条疑似串位，净土宗亦非理学谱系内条目。本包不修改，建议 Codex 复核归位。
- **T01 佛教哲学包**：其 evidenceLimits 已声明净土、律、真言（汉传）三宗未获直接来源未写、由站内既有覆盖承接——本包即该承接的净土专门深度，T01 只保留大乘通史中的一句定位即可，两包互补。
- **B05 天台包**：天台净土学（智者《净土十疑论》托名问题、四明知礼与净土）本包不展开；S1 记五部天台净土著作托名智顗（'attributed to Zhiyi, but cannot be by him according to Jones'）已作文献节点保留，深度归天台侧。
- **B01/B02/B03/B10 接口**：早期六随念归 B01；龙树中观正面归 B02（本包只取《易行品》接受史）；唯识体系归 B03（本包只写"唯心净土"论辩）；世亲俱舍/唯识归 B03/B10（本包只取《往生论》署名传统归属一层）。

## 三、来源与核读方法

七个来源分三层，互不转抄：

1. **原典层（S2/S3/S4）**：中文维基文库净土三经公共领域全本。经 MediaWiki API `prop=extracts` 抓取全文（阿弥陀经 revid=2665411、分类含 PD-old 与"淨土五經一論"；无量寿经页头署名康僧铠、校记"據龍藏版和大正藏版校定"在页元数据逐字核实），全部引语用 python 子串/标点比对逐字核验。观经 URL 经重定向至"觀無量壽經"页面核读。
2. **百科层（S1/S5/S6）**：en.wikipedia 三条目经 action API explaintext 全文抓取（净土 126980 字符；法然约 4.6 万；亲鸾约 7.3 万），全部关键断言（年代、师承、著作、判语、教义归属）多轮 grep 定位到原句；S1 转述的 Jones/Nattier/Williams/Kapstein/Halkias 观点逐条回查到转述句。
3. **站内通史层（S7）**：蒋维乔《中国佛教史》（1201d003be31）第九章（11.json）、第十四章（16.json）、第十六章（18.json）、第十八章（20.json）净土段落实读；coverage 与正文所引站内语句全部回查章节文件逐字核实（含"谨案龙树菩萨《十住毗婆沙》云……"发端引文、"我已依龙树之劝发"偈引、别时意论战全链、宗晓七祖名单、"诸宗融合之归宿"结语）。

外围查证：SEP（/entries/pure-land/、/entries/pureland/）与 IEP（/pure-land/、/pure-land-buddhism/、/shinran/）2026-10-04 curl 复测均 404；Britannica 403；Met 429——英文哲学百科的空缺如实记录于 evidenceLimits，构成本包来源基座选择的原因。

## 四、修正处置记录（二次复核轮，2026-10-04）

对草稿逐源核验后，修正 packet.json 如下 16 处（全部有据可查，evidence.json 有对应条目）：

1. **overview"一相庄严三昧"句删除改写**：原句"般若类经典已说'一相庄严三昧'——摄心专念一佛名号即可见三世诸佛"在 S1 无对应文本（ekavyūha 等检索 0 命中），属无来源断言。改为 S1 明文支持的《般舟三昧经》系念见佛内容（含"不限弥陀、通于任何现前之佛"）。
2. **overview"印光斥'唯心'解为邪见"删除改写**：S1 无此内容（Yinguang 全部 6 处语境均无）。改为 S1 明文的"印光援华严教义论证净土实有"（'Yuan Hongdao and Yinguang both draw on Huayan thought to argue for the truth of Pure Land'）。cihai"他方净土与唯心净土"同句同步修正。
3. **cihai"称名念佛"末句改写**："净土之'往生'不等于彼岸灵魂论"为无来源的编辑推断，改为 S1 明文的"净土传统明确自别于有神论宗教，其立据是大乘的佛菩萨观与空、唯心教义"。
4. **quotes[2]（蒋维乔系谱引）与 quotes[5]（第十八章引）用字修正**：原稿为繁体字并自称"按站内存储用字"，站内章节文件实为简体存储——两引文按存储原文改为简体，逐字比对通过；author 注记改为"简体原文"。
5. **quotes[3]（Jones 判语）句首 While 改 while**：与 S1 原句大小写一致（源为句中引用）。
6. **closingQuote 异体字修正**：源文"為一切世間……是為甚難"，原稿"爲"改"爲→為"，逐字比对通过。
7. **quotes[1]（观经第八观）标点修正**：维基文库该页以句号断句且"是心作佛是心是佛"中间无逗号，原稿逗号按源文修正。
8. **S4 coverage 署名修正**：页面实际署名为"宋西域三藏畺良耶舍譯"（原稿作"宋　譯者：畺良耶舍，出自《大正新脩大藏經》"——后者无据），并补记 URL 重定向事实。
9. **S5 coverage 修正**："死后著作被天台众烧毁、塔被毁"为误置——S5 实文是 1227 年《选择集》印版被捣毁、1239 重刻；著作与墓被毁之记载在 S1 Japan 节，改按两源分别标注。
10. **S7 coverage 章节题名修正**："第十四章'唐之诸宗（一）念佛宗'"改为"第十四章'唐之诸宗'（16.json，（一）念佛宗节）"，与站内 meta/章节实题一致。
11. **subSchools 日本净土宗 era 修正**："1175 年立教申明"改为"1175 年下山专修念佛（传统开宗点，S5）"——S5 原文是"prompted Hōnen to leave Mt. Hiei in 1175"，无"立教申明"语。
12. **evidenceLimits 章节号修正**："站内《中国佛教史》第十一章（第十六章…）与第二十章（第十八章…）"系文件号/章号混写，改为"第十六章（章节文件 18.json）与第十八章（文件 20.json）"。
13. **evidenceLimits Met 403 表述修正**：复核实测 Met 返回 429（限流）而非草稿所记"Vercel 安全检查"，照实测改。
14. **overview 结社链修正**："省常西湖结社"两源均无"西湖"（S1 只记 Shengchang 结社、S7 记"昭庆省常"），改"省常昭庆结社"；"日本讲集"无来源，改"日本真宗门徒集会"（S6 monto）。
15. **overview 阿弥陀经引文补逗号**："阿彌陀佛與諸聖眾現在其前"补为"阿彌陀佛與諸聖眾，現在其前"（源文有逗号，原稿以逐字口径引用）。
16. **cihai"别时意"与 cihai"念佛"精确化**：别时意源文是"自真谛之弟子智恺译《摄论》始"（非"自真谛译《摄论》"），照原文改；宗密四种念佛 S1 与 S7 名单次序略异，cihai 并列照录。

另新增 evidenceLimits 两条：宗晓祖统两源差异（S1 六祖含长芦宗赜 vs S7 七祖含延寿/省常）；亲鸾卒年两源差异（S1 作 1262、S6 作 1173-05-21—1263-01-16，本包从 S6）。

## 五、证据限度（摘要，全量见 packet.json evidenceLimits）

- 《观经》成立疑案（中国撰述说 vs 传统译署）双层照录；《无量寿经》通行本译者两源异说照录（S7/S3 康僧铠 vs S1 佛陀跋陀罗）；道绰系年两源不合（S7"陈代" vs S1 562—645）照录。
- 日本一线为来源短板：法然/亲鸾用英文维基条目，《选择集》《教行信证》《叹异钞》原文未逐字核读（"恶人正机"引文与 1224 系年均经条目转引并标层级）；亲鸾名字合成说（Seshin+Donran）仅 S6 一源。
- 龙树/世亲与净土的关联属接受史：《十住毗婆沙论》署名有学术争议（S1 引 Hirakawa），《往生论》署名有争议（S1 引 Williams），条目按"传统归属"标注。
- 藏传一线只作一句定位；敦煌文书细节、藏译版本史未核读。
- "光明大师"赐号在 S1 内为传闻级表述（'is said to have'），已按转记层级处理。
- 站内无净土原典或专书（books.json 409 本 python 实查各净土关键词 0 命中），唯一相关藏书为蒋维乔《中国佛教史》，属通史而非原典。

## 六、实际核读 URL 清单（2026-10-04）

- https://en.wikipedia.org/wiki/Pure_Land_Buddhism （action API explaintext 全文 126980 字符，多轮定位）
- https://en.wikipedia.org/wiki/H%C5%8Dnen （同上，约 4.6 万字符）
- https://en.wikipedia.org/wiki/Shinran （同上，约 7.3 万字符）
- https://zh.wikisource.org/wiki/%E4%BD%9B%E8%AA%AA%E9%98%BF%E5%BD%8C%E9%99%80%E7%B6%93 （extracts 全文 + categories + revisions；revid=2665411）
- https://zh.wikisource.org/wiki/%E4%BD%9B%E8%AA%AA%E7%84%A1%E9%87%8F%E5%A3%BD%E7%B6%93 （extracts 全文 + 页 wikitext 校记核读）
- https://zh.wikisource.org/wiki/%E8%A7%80%E7%84%A1%E9%87%8F%E5%A3%BD%E4%BD%9B%E7%B6%93 （重定向至觀無量壽經，extracts 全文 + wikitext）
- 站内：backend/data/book_chapters/1201d003be31/{11,16,18,20}.json（git 跟踪源章节全文）、meta.json；app/public/books.json；app/public/philosophers.json；app/public/schools/data/school_隋唐佛学.json；app/public/schools/data/school_宋明理学.json；app/public/schools/catalog.json
- 复测 404：https://plato.stanford.edu/entries/pure-land/ ；https://plato.stanford.edu/entries/pureland/ ；https://iep.utm.edu/pure-land/ ；https://iep.utm.edu/pure-land-buddhism/ ；https://iep.utm.edu/shinran/
- 复测 403：https://www.britannica.com/topic/Pure-Land-Buddhism ；复测 429：https://www.metmuseum.org/toah/hd/pure/hd_pure.htm
