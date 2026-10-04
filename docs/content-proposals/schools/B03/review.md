# B03 唯识 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B03`（proposedKind=school，P1-content-packet，coverage=related-branches-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、与 T01 的分工

T01（佛教哲学总览）对唯识只保留了三处：'唯了别'术语一条（cihai/7）、瑜伽行派概览定位（subSchools/2，注明标签争议存在）、世亲条目。B03 是专门深化，主题互不重复：

|主题|T01|B03|
|---|---|---|
|唯了别定义与'唯识'译名|一句定义|专节：四名并举（Yogācāra/vijñānavāda/cittamātra/vijñaptimātra）+ 汉译宗名考 + 观念论标签争议展开|
|八识体系|未展开|核心章节：染污意、藏识（种子/习气/业力连续）、转识与潜隐层面|
|三性三无性|总览级提及|三性定义 + 《三十颂》颂文逐字对勘 + 三无性接口|
|《二十论》论证|作品条目一行|四难与三喻逐点答辩 + 极微破 + 论敌引佛说诘难（中英文本对读）|
|唯识—中观论辩|'两大路线并立'的编辑比较|双向论辩：《解深密经》第三转法轮判教 vs 早期中观破斥、月称批判、后期会通|
|汉传传入|仅玄奘西行+译经基本事实|新旧两译、十家糅译、窥基建制、圆测九识之争、东传日本|

衔接点：T01 的 evidenceLimits 明记"玄奘与唯识宗建制的专文细节（如译场组织、《成唯识论》糅译）未获核读来源，本包仅载西行与译经基本事实"——B03 即补此缺。SEP vasubandhu、madhyamaka 两条 T01 与本包各自独立 curl 抓取，当日两遍结论一致（非单向转抄）。

## 二、边界决定

1. **三重区分**（任务条目 scopeAndCautions）：印度瑜伽行 / 中国法相（汉传新旧两译）/ 现代唯心论解释（熊十力《新唯识论》等）——现代诠释按边界划给站内《现代新儒家》，本包不作"唯识=唯心主义"式叙述。
2. **同名异实排除**：瑜伽行派（Yogācāra）≠ 帕坦伽利瑜伽派。站内《印度哲学》 subSchools 同时存在"瑜伽派（帕坦伽利）"与世亲"佛教唯识派"，检索别名"瑜伽行"必须人工分辨；此点为站内数据定位+任务警示，packet 已注明层级。
3. **传记与史实分开**：无著—世亲兄弟传承、弥勒五论传受按"传记叙述"呈现；Frauwallner 两个世亲假说、转宗故事质疑、《瑜伽师地论》编纂说如实并陈，不作调和。
4. **论辩不作个人对辩**：月称批判的是瑜伽行学派整体（SEP 口径），月称→护法关系标为"学派论辩（编辑定位）"，不写成两人直接对辩；中观批判与瑜伽行判教两个方向都呈现，不预判胜负。
5. **唯识与西方观念论不作比较**：'唯识家=观念论者'在 SEP 本身就是争议专节，任何东西比较须专门证据另行处理（relationSuggestions 已写明不建议直接与"唯心主义"条目互设关系）。

## 三、查重与既有内容

- **coverage=related-branches-only 核实**：无同名顶级条目、无同名分支；相关分支即《韩国哲学》subSchools/3"韩国华严与唯识学（和诤思想）"（元晓、义湘、圆测）；mentionFiles 5 项（印度哲学、隋唐佛学、西藏哲学、韩国哲学、现代新儒家）经 python 逐文件复核属实。
- **既有内容定位**（python 提取，本包全部导流不重复）：《印度哲学》thinkers/3 世亲（唯识无境/阿赖耶识/《唯识三十颂》《摄大乘论》）；《隋唐佛学》玄奘（法相唯识宗）+《成唯识论》书目 + 唯识/阿赖耶识/转识成智/唯识无境术语 + "三界唯心，万法唯识"引语；《西藏哲学》relations/1"印度瑜伽行派（无著）"；《现代新儒家》熊十力《新唯识论》。B03 补足站内未深化的：八识模型细节、三性三无性、四分说谱系、十家糅译与圆测分歧、二十论论证结构、中观论辩。
- **人物**：philosophers.json（737 人）python 实查——站内有**世亲**（"约公元4世纪至5世纪"，归"瑜伽行派（唯识宗）"）、**玄奘**（"602-664年"，归"隋唐佛学"），姓名纪年从站内；无著、陈那、护法、窥基、月称、圆测站内均无，保留准确姓名并标注站外（圆测另见站内《韩国哲学》正文）。窥基站内无——与任务提示"站内有世亲、玄奘"一致。
- **书籍**：books.json（409 种）python 实查，唯识/瑜伽/成唯识/俱舍/三十颂/二十论/解深密/百法/因明/阿赖耶等关键词零命中；佛学专门藏书仅《中国佛教史》（1201d003be31，T01 已建议关联）。故 suggestedBookLinks 留空，不造站内书 ID。
- **站内既有术语沿用**："唯识无境""转识成智""三界唯心，万法唯识"等《隋唐佛学》既有表述本包未逐字重考，只导流不重复立目（evidenceLimits 已声明）。

## 四、分歧与争议的处理

- **观念论标签**：不预判。SEP Vasubandhu 争议专节 + SEP Yogacara 三层解读（对象/原因/终极实在）+ "并非每部瑜伽行作品都以强意义主张唯心" + "本体论 vs 认识论解读存在相当大分歧"四条如实并陈。
- **世亲年代与归属**：S2 内部即并存"4世纪笈多朝"与两论归属；Frauwallner 假说"在学界某些领域占主导"（Versions of this theory hold sway in some areas of the academy）——照录强度，不写成定论。
- **窥基声明**："护法为正义"的汉传传统声明与其现代修正（常把 Sthiramati 的解释归于护法）同条呈现，relations/4 标"存学术分歧"。
- **《成唯识论》性质**：Wikipedia CWSL 作"written by Xuanzang"，Wikipedia Kuiji 作"a redacted translation of commentaries"——两者相容（糅译），packet 按"糅译十家"表述并各引原句。
- **reference 级来源**：Wikipedia 四条（Yogacara/Cheng Weishi Lun/Kuiji/East Asian Yogācāra）仅用于定位性断言（四分谱系、糅译名单、生卒、两译系统），SEP 三条与维基文库两条承担学说与原典论证；reference 级占比与用途已在 sources.coverage 声明。

## 五、复核方法与结果

1. 主会话直接执行，全程 curl 抓取原文后 python 定位逐字核对（检索摘要一律不作依据）。SEP 四条（yogacara/vasubandhu/madhyamaka/epistemology-india）、Wikipedia 四条、维基文库三页全部实测打开。
2. **维基文库实测记录**：《唯識二十論》《唯識三十論頌》为全文页（逐字核读，含开篇标宗、四难颂、三喻颂、极微颂、三性三无性颂、真如颂）；《成唯識論》主页仅目录页（署"護法等菩薩造　三藏法師玄奘奉詔譯"），其 /卷第一 实测为空页（"此页面目前没有内容"）——成唯识论正文不可核读，如实入 evidenceLimits。
3. **中英文本对读互证**：SEP Vasubandhu 所载论敌引文（"If the images of physical forms…"，Viṃś 5）与《唯識二十論》汉译"謂若唯識似色等現無別色等。佛不應說有色等處"对应；SEP 所载《二十论》开篇英译（"In the Great Vehicle, the threefold world is only appearance"）与玄奘译"安立大乘三界唯識"对应；SEP 三性节标注的 Triṃśikā verses 23–25 与维基文库夹注本颂号吻合。
4. evidence.json 共 77 条记录（overview 19、thinkers 8、relations 8、timeline 9、cihai 10、works 8、subSchools 6、引语 5〔quote/quotes×3/closingQuote〕、proposal 2、conclusion 2），locator 均含亲眼核读的 verbatim 短引文，fieldPath 全部可解析到 packet 对应位置（脚本核对）。
5. 数量：来源 11（学术百科 4 + 原典 3〔其一为目录页并已声明〕+ reference 4）、人物 8、时间线 9、术语 10、著述 8、分支 6、阅读路径 2、证据限度 13——均在契约区间。
6. 两个 JSON 经 `python3 -m json.tool` 校验通过；relations 端点脚本核对：8 条关系 from/to 均精确等于本包 thinkers 的 name。

## 六、仍缺证据（与 packet.evidenceLimits 对应）

- 《成唯識論》正文（维基文库分卷未建；CBETA GitHub 此前代理实测 404，未再试）——本包未引其任何正文文字。
- 圆测生卒年、"唯識無境"四字格式的来源级定位、"证自证分"等汉字定名的逐字出处、玄奘 645 年归国等具体年份。
- 藏传承接（应成/自续、量论课程地位）、韩国元晓/义湘与唯识的细节、法相宗日本建制史、如来藏与唯识交涉——均未核读，分别导流站内对应条目。

## 七、放弃线索

- `https://plato.stanford.edu/entries/buddhist-mind/`（researchLead sep-buddhist-mind）→ 实测 404，不存在该 SEP 条目，已放弃；唯识心灵哲学内容改由 SEP yogacara（2024 年新条目，researchLead sep-yogacara 成立）承担。
- 维基文库《成唯識論》→ 目录页存在但分卷空页，正文放弃，改为《唯識二十論》《唯識三十論頌》两部全文承担原典功能。

## 八、实际核读 URL 清单（2026-10-04，curl 全文+定位）

1. https://plato.stanford.edu/entries/yogacara/ （2024-07-07 首发条目）
2. https://plato.stanford.edu/entries/vasubandhu/ （2021-01-07 修订版；与 T01 同日各自独立抓取）
3. https://plato.stanford.edu/entries/madhyamaka/ （2023-08-18 修订版；同上）
4. https://plato.stanford.edu/entries/epistemology-india/ （仅取两处，见 S11 coverage）
5. https://en.wikipedia.org/wiki/Yogacara （仅取 four parts 节）
6. https://en.wikipedia.org/wiki/Cheng_Weishi_Lun
7. https://en.wikipedia.org/wiki/Kuiji
8. https://en.wikipedia.org/wiki/East_Asian_Yog%C4%81c%C4%81ra
9. https://zh.wikisource.org/wiki/唯識二十論 （全文逐字）
10. https://zh.wikisource.org/wiki/唯識三十論頌 （全文逐字）
11. https://zh.wikisource.org/wiki/成唯識論 （目录页；/卷第一 实测空页）
- 状态检测：/entries/yogacara/ 200；/entries/buddhist-mind/ 404；en.wikipedia.org/wiki/Alaya-vijnana 重定向至 Eight Consciousnesses（未单独立源）。
