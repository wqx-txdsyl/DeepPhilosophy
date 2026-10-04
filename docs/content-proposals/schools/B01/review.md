# B01 早期佛教思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B01`（proposedKind=historical-phase，P1-content-packet，coverage=no-match-in-reviewed-school-files）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员两遍自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **类型取 historical-phase，不取 school**。任务条目 proposedKind=historical-phase，证据支持：这一时期是口传共同体，没有建制、没有可归属个人的创派文献；Wikipedia Pre-sectarian Buddhism 条目本身以"部派前"命名，且明言现存诸藏"全都已经部派化"（"already sectarian collections"）。packet.proposal.kindRationale 写明理由，并注明若 Codex 决定按 school 型接入，本包内容可整体作为该条目早期阶段的深化材料。
2. **与 T01《佛教哲学》的分工**：T01 是跨地区总览枢纽，其 subSchools 首项"早期佛教与部派阿毗达磨"（约前5世纪—前3世纪起）只有一句阶段定位。本包是该阶段的专门深化——核心教义的文本根据、平行文本对读（以《转法轮经》SN 56.11 / SĀ 379 为标本）、口传—结集—书面化文献史、重构方法论（最小核心说之争）。T01 对天台/华严之与《隋唐佛学》的分工逻辑，此处同样适用；两包建议互设导流，本包不重复 T01 的地区与宗派内容。
3. **与 B10《阿毗达磨思想》的分工**：本包止于部派分裂（约前3世纪初，SEP Abhidharma："公元前3世纪初"上座/大众分立，注意其谨慎措辞"广为接受的传统说法"）。SEP Abhidharma 开篇的体裁划界是边界根据：'Abhidharma is to be contrasted with Sūtrānta, the system of the Buddha's discourses'，且早期佛典"口语化性质"（colloquial in nature）与阿毗达磨的技术化定义相对——本包对象是口语化的 sūtrānta 层，部派论书归 B10。
4. **叙事人物与文本人物分开**。阿难、摩诃迦叶、优波离只以结集传说叙事出场（timeline/relations 一律标"结集传说（口传叙事）"，era 标"传统叙事人物"）；憍陈如只以两系《转法轮经》文本的记载出场（标"文本所载（平行本一致）"）。不作任何生平断言。结集叙事本身的传说性质按来源标注（"现代学者已质疑其历史性"；"很可能是夸大"）。
5. **克制写法三例**：①"如是我闻"开篇公式两系文本共见（S4/S6 原文核读），但本包所核来源未直接把该公式归名阿难，此联结不写；②Anālayo 引 T 1428 的迦叶责阿难语，本包只见其英译，汉文原文字句未核读——packet 中明确标注"汉文原文字句未核读，不冒充原文"；③五蕴的逐项枚举（色受想行识）未在核读来源逐字出现，cihai 不枚举。
6. **不做跨传统比较**。无我/自我与西方哲学的比较、"早期佛教与斯多亚"之类一律不做；无我诠释之争（佛陀是否断然否认自我）按 SEP 并陈，不采边。

## 二、分歧与争议的处理（按来源呈现，不裁断）

- **佛陀年代**：SEP 载两说（旧说约前560—480；今多数学者主"必死于约前405"）并标注 floruit（"fl. circa 450 BCE"）；站内沿用"约前5世纪（具体生卒年有争议）"，两说并陈。
- **"最早的佛陀教说"与"部派化之前共同底本"之辨**：这是任务书点名的文献学难题，本包的处理是把重构诸立场完整呈现——Schmithausen 归纳的三立场（同质性/怀疑/谨慎乐观）、Lamotte 的"尼柯耶—阿含基本一致"标准、中村元的"无一词可确考"立场与最早层判断（经集伽陀等）、Vetter 的约前270年上限与禅那优先说、Conze/Warder 的"两部共有"标准、"core within this core"（最早层诗句）。不做裁断。
- **四谛是否最早层**：Norman（"圣"字后加）、Schmithausen（四谛较晚发展）、Anderson（"大约是从律藏进入经藏的"）vs Anālayo（诸平行本一致在场支持传统说法，不确定的只是"圣"之限定）。另收 Thanissaro 译注1的方法论反批评（巴利语法异常不能证明早晚）。两说并陈于 overview/cihai/evidenceLimits。
- **缘起十二支**：SEP 明言"现代研究已经确定这份清单是较晚的编纂"（两个略异版本+更短表述并存）——本包把该警示与十二支定义并置呈现，不把十二支当"佛陀原话"。
- **结集史**：第一次结集传说与学界保留并置（六部律典均有记述 vs 历史性质疑、《薄拘罗经》MN 124 内证）；第二次结集仅"佛灭百年"一句级定位，细节未核读不展开。

## 三、查重与既有内容

- 任务 JSON 的 B01.evidence 五个数组（exactTopLevelEntries/exactBranches/relatedBranches/excludedLexicalMatches/mentionFiles）全空 → coverage=no-match-in-reviewed-school-files 成立；现有111项一级条目与556条子项中无"早期佛教（思想）"同名入口。
- 相邻内容两处：①T01 提案包 subSchools[0]"早期佛教与部派阿毗达磨"（阶段定位一句，提案未接入正式目录）——本包为其深化，见边界决定第2条；②站内"释迦牟尼"人物条目（philosophers.json）bio 已载"巴利尼柯耶与汉译阿含可相互参照；晚出的经典不能未经辨析便充当历史人物原话的直接记录"——本包为该原则提供文本学根据，建议互链（evidence 有对位记录）。
- 人物（philosophers.json python 键遍历实查，2026-10-04）：本阶段站内仅"释迦牟尼"（era"约前5世纪（具体生卒年有争议）"）；阿难、摩诃迦叶、优波离、憍陈如、五比丘（其余四人）、阿育王均无——前四者按契约作为站外人物收入 thinkers 并在 sub 标注"（站外人物）"，relations 端点全部等于本包 thinkers 的 name。
- 书籍（books.json python 实查，关键词：佛/阿含/巴利/佛陀/原始/印度/禅/经）：佛学专门藏书仅《中国佛教史》（1201d003be31，蒋维乔，epub，21章，非TXT占位）一种——关联建议只列该种，并注明本包未核读其内容、站内无阿含/巴利藏原典书、不作"可在线阅读"暗示。

## 四、复核方法与结果

1. **第一遍（核读写入）**：curl 直抓全部来源全文缓存后逐段定位核读——SEP×2、Wikipedia×5、Access to Insight《转法轮经》SN 56.11（Thanissaro 英译）全文、维基文库《雜阿含經（五十卷）》卷第15（三七九经）全文；SA 379 与 SN 56.11 的结构差异（汉译本无中道开篇）为本包对读观察，两个文本均在案。检索摘要一律不作为依据。
2. **第二遍（脚本复验）**：写稿后以脚本从 evidence.json 提取全部 verbatim 引文片段（统一空白与引号字形后），对 /tmp 已抓全文逐条 grep 复验。过程中发现并改正四类问题：①三处引文跨页面脚注号（Pre-sectarian 的四谛三立场清单、Middle Way/dhyana 句、转法轮经平行本清单）→ 一律拆为分引片段并在 locator 注明"原文有脚注号，分引"；②两处省略号引文改为全句连续引用；③一处标点位置错误（Schmithausen 三立场第一条的分号应在引号内）与一处"別譯雜阿含經"括号形制误记（页面两括号均为半角，已照录更正）；④一处中译转述有被误读为汉文原文的风险 → 改为引 Anālayo 英译并注明"汉文原文字句未核读"。终检结果：**134条 verbatim 片段全部命中来源全文，0 未命中**。
3. **结构校验**：两个 JSON 经 `python3 -m json.tool` 通过；packet 顶层13个必需键齐全；readingRoutes=2、evidenceLimits=12 在顶层；relations 端点全部精确等于本包 thinkers 姓名；sourceRefs 全部可解析（无未解析引用）。
4. **数量**：来源 10（学术百科 2 + 原典级 2 + reference 6）、人物 5、关系 5、时间线 9、术语 10、著述 6、子层 3、引语 4（卷首/引语×2/结尾）——在契约参考区间（早期口传传统，thinkers 取下限 5 并在 proposal/evidenceLimits 说明理由：该阶段无个人著述传统，人物多为叙事层）。

## 五、仍缺证据（与 packet.evidenceLimits 对应）

- Vetter《The Ideas and Meditative Practices of Early Buddhism》（BRILL 1988）专著本身未直接核读，全部论点经 Pre-sectarian 条目转述层呈现（书名/出版社/年份经其参考文献核验）。
- 《转法轮经》的犍陀罗本、梵语残本、藏译 Toh 337 与诸律本内容未核读（S5 仅平行本清单与部派归属）。
- 第二次结集细节（毗舍离、十事）及其与部派分裂真实时间的关系未核读。
- 阿育王法敕未单列时间线节点：与分裂纪年的先后关系在本次来源中仅见于 Vetter 转述句内，法敕专文未核读，已并入"约前270年"节点转述。
- 汉译《中阿含经》Taishō 编号、《别译杂阿含经》翻译年代未在核读来源出现，不标注。
- 五蕴逐项枚举、"色受想行识"名相未获来源，不写。

## 六、实际核读 URL 清单（2026-10-04，均 curl 全文缓存后定位）

1. https://plato.stanford.edu/entries/buddha/
2. https://plato.stanford.edu/entries/abhidharma/
3. https://en.wikipedia.org/wiki/Presectarian_Buddhism
4. https://www.accesstoinsight.org/tipitaka/sn/sn56/sn56.011.than.html （SN 56.11，Thanissaro 英译全文）
5. https://en.wikipedia.org/wiki/Dhammacakkappavattana_Sutta
6. https://zh.wikisource.org/wiki/雜阿含經（五十卷）/卷第_15 （三七九经全文；译者与年代另据维基文库《雜阿含經》消歧义页与 S8 交叉核实）
7. https://en.wikipedia.org/wiki/Pali_Canon
8. https://en.wikipedia.org/wiki/Āgama_(Buddhism)
9. https://en.wikipedia.org/wiki/First_Buddhist_council
10. https://en.wikipedia.org/wiki/Gandharan_Buddhist_texts

放弃/改道记录：维基文库《雜阿含經/卷十五》（旧式 URL）与《雜阿含經（五十卷）》主页（仅存根）→ 经 MediaWiki API allpages 查得实际子页"雜阿含經（五十卷）/卷第 15"后改道成功；CBETA GitHub XML 仓库（cbeta-org/cbeta-xml）T99 路径 404 → 改用维基文库 Wikisource 文本；SuttaCentral 未采用（页面为 JS 渲染，curl 不出正文，平行本信息改由 Wikipedia Dhammacakkappavattana 条目的清单承载）。

## 七、与研究规则的逐条对照

- 至少3个不互相转抄的来源：SEP×2（原创学术条目）、Wikipedia×5（各条引用的底层学术文献不同且互不转抄，均按 reference 级使用并声明）、Access to Insight（原典英译）、维基文库（原典汉译）——共10源、2个原典级。
- 支持学说范围与归属的来源：S1/S3（学说范围与重构立场）；支持原典/具体论证的来源：S4/S6（初转法轮两系全文）。
- 古代/口述传统的层次区分（历史人物/传说/文本署名/口传/编纂/翻译）：thinkers 的 era 标注、timeline 的 type 字段（结集/口传/文献/翻译/研究）、works 的 kind 字段分层执行。
- "旧正文只作为待查线索"：站内释迦牟尼 bio 的原则性表述仅作互证记录（evidence 有对位条目），未继承任何未核引语。
