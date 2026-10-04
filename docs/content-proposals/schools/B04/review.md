# B04 佛教逻辑与认识论 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B04`（proposedKind=research-tradition，P1-content-packet，coverage=mentions-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员两遍自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、查重与同日姊妹包的分工（首要项）

coverage=mentions-only：无同名顶级条目；任务清单 mentionFiles 仅 2 项（印度哲学、西藏哲学，均命中"因明"）。但同日多个资料包与站内数据有量论相关提及，本包经 python 实查后逐一定界：

| 既有内容 | 粒度 | 本包（B04）对应处理 |
|---|---|---|
| T01"量论逻辑"论证线索（陈那/法称一句定位、年代从 SEP 约数） | 概览级 | 本包承载全部量论内部谱系：二量/因三相/九句因/三类因/apoha/自证的全部学说细节与原典定位 |
| I01 正理派（scope 含"与佛教论师（陈那、法称）及弥曼差派的论辩"） | 正理侧 | 本包写佛教侧同一论战：Uddyotakara 批评因三相与法称 eva 重述、"正理哲学家几乎把一切都归功于其佛教论敌"；正理五支论式/四量正面体系不代写 |
| I03 弥曼差派（scope 含 svataḥ prāmāṇya 与量论） | 弥曼差侧 | 本包写不可得因之争（Bhāṭṭa 独立量 vs 法称比量）与 svataḥ prāmāṇya 的佛教版本；声常说等正面体系不代写 |
| B03 唯识（陈那三分 svasaṃvitti-bhāga；显式留白"量论在格鲁课程中的地位、《释量论》藏传注疏"） | 唯识识体面 | 本包接手该留白：svasaṃvedana 作为认识论机制与量果问题（非识体结构），藏传课程传统（桑普/萨迦/格鲁三线+诠释分歧） |
| 站内《印度哲学》cihai"因明"条 + quotes"正理派系统发展了因明学" | 一条术语+一句引 | 本包深化；口径提示：S1 证据把"印度古典逻辑最伟大的两个名字"定为佛教论师陈那/法称，现有"正理派系统发展因明学"的表述侧重偏早，留给 Codex 取舍 |
| 站内《西藏哲学》萨迦班智达（key"量论与因明"）+ works《量理宝藏论》 | 一行条目 | 本包补 S4 来源侧证（萨迦量论传统以其著作为基础）与格鲁对置线；派别建制不代写 |
| 站内 philosophers.json 世亲/玄奘/萨迦班智达/宗喀巴条目正文的陈那/法称/量论叙述 | 站内自有叙述 | 只作注记不作来源引用；本包人物姓名纪年采用站内，站外人物标"站外人物" |

**本包独有内容**：SEP Dharmakīrti 专条全文核读（命名史"梵文误名"、七部著作定序、格鲁/萨迦诠释分歧原文、svasaṃvedana 两主题、apoha 因果化改写、nigrahasthāna）；SEP Logic 条的陈那三部著作存世形态（正理门西藏梵本未刊）与九句因矩阵；SEP Tsongkhapa 条的藏传课程证据；维基文库两部汉译原典逐字核读（八门二益总颂、因三相、九句因总颂、"諸自證分"、他比量两支、"慧毒藥"结颂）。这些内容 T01/I01/I03/B03 均无或仅一句带过。

## 二、边界决定

1. **学派范围**：任务 scopeAndCautions"不能把全部佛教认识论都归为唯识的单一分支"的处理——(a) 早期佛教与中观的认识论问题（龙树《回诤论》倒退追问）只作 overview 背景一句，由 T01/B02 承载；(b) S1 称陈那/法称属"佛教 Yogācāra school"与 S2 称其为无梵文名的"认识论学派"是两个层次（宗派归属 vs 传统自名），并陈不裁决；(c) 经量部关联未核读，不写。
2. **kind 建议**：任务条 proposedKind=research-tradition；本包按证据建议 kind=school（S2 原文"a school of Buddhist thought that actually had no name in Sanskrit"），命名史如实附注，最终归类由 Codex 决定。
3. **汉传一线**：只写传播事实层（玄奘译入正理論、义净译正理門論、法称无汉译、现代日本线）；窥基疏释建制与日本因明课程未核读专文，不展开。
4. **藏传一线**：写至课程建制（S4：课程含 pramāṇa、两大传统、纳塘辩经）与诠释分歧（S2：格鲁/萨迦两派评语原文）；"《释量论》在格鲁课程中的地位"教科书细节、blo rig 等次第课程未核读，一律不写（任务要点明确此为深化需求，已按"需新来源"处理：本包以 S4+S2 的新抓取内容覆盖了课程与分歧两级，但教科书级细节仍缺专文，如实留白）。
5. **论敌人物的立目**：Uddyotakara 与鸠摩利罗作为 thinkers 收入并标"论敌侧"，理由是任务要点"与正理-弥曼差的论辩"需要具体端点（relations 端点必须在本包 thinkers 内）；两人正面体系分别由 I01/I03 承载，thinkers 条与 subSchools 均已声明分工。Uddyotakara 无通行汉译名，以梵文名立目；"鸠摩利罗"为学界通行音译，均已在 evidenceLimits 声明。
6. **不进行跨传统比较**：法称三类因与西方因果推理、apoha 与现代指称理论等比较一律不做；S1/S2 中的西方哲学类比（a priori、causal theory of reference、Gettier）只作为来源叙述出现在 evidence locator，不写入 packet 正文当主张。

## 三、分歧与争议的处理（均按来源呈现）

1. **法称生卒**：6 vs 7世纪之争（Frauwallner 600—660"近乎默证、离定论尚远"；Krasser 2012 主张推至6世纪中叶；Balcerowicz 550—610）——S2 原文逐字核读，人物条/timeline 一律两说并陈，不给单一纪年。
2. **陈那生卒**：三口径并陈（S2 c. 480—c. 540；S3 约5—6世纪；S1 六世纪）。
3. **遍充奠基方案**：帝释慧以不可得奠基→法称驳之→法称以 tādātmya/tadutpatti 方案→SEP 直书"法称的方案并不奏效"（附 Steinkellner 2015 异见）——全链条按 S3 并陈，packet 不裁决。
4. **eva 歧义**：法称以 eva 重述三条件，但 eva 两用（强调/限定）与 sa-pakṣa 的包/排除两读使精确化受挫（Gillon 1999；"译作 necessary 无 philological 依据"）——作为"论战双方力量对峙未消解"的证据写入 conclusion。
5. **svasaṃvedana 与内在主义**：S2 记 Williams/Kellner/Arnold 的两主题重构为"seem to be"级推断，且"反思性觉知不会直接给出辩护意识"——uncertainty 已标。
6. **维基文库署名两处差异**：①《因明正理門論》页头作者栏"龍樹菩薩" vs 书目行"大域龍樹菩薩造"；②《因明入正理論》页头作者栏"南羯羅主菩薩"（商字脱）vs 书目行"商羯羅主菩薩造"。两处均按所见并陈、不擅自调和（做法同 B02 对 MMK 24.18"無/空"异读的处理）；"大域龍=陈那"的等式按书目常识声明而非来源断言（evidenceLimits 第3条）。
7. **站内《印度哲学》"因明"口径**：现有条目把因明学的发展系于正理派（quotes"该学派系统发展了因明学"），与本包 S1 证据（两大名字为佛教论师、因三相体系化出自陈那）存在侧重差——本包不代改，在 coverageNote 与本文件记录，由 Codex 取舍。

## 四、复核方法与结果

1. **独立重抓**（未复用 T01/I01/B03/I03 缓存）：2026-10-04 由本任务 curl 直抓 6 个来源全文——SEP Epistemology in Classical Indian Philosophy（133KB）、SEP Dharmakīrti（146KB）、SEP Logic in Classical Indian Philosophy（136KB）、SEP Tsongkhapa（106KB）、维基文库《因明正理門論》（86KB）、《因明入正理論》（79KB）；HTML 去 tag 转文本后以 python 逐字定位，全部被引句逐字命中（locator 见 evidence.json）。检索摘要一律不作为依据。
2. **URL 探测记录**：/entries/dharmakirti/ 与 /entries/dignaga/、/entries/apoha/ 均为 404（不存在或非此名）；法称实际条目为 /entries/dharmakiirti/（双写 ii，200）。IEP 无 Dignaga/Dharmakirti/indian-logic 专条（404）。SEP Tsongkhapa（/entries/tsongkhapa/，200）为本任务探测所得，替代任务清单 researchLeadIds 中不可用的建议项。
3. **原典核读**：《因明入正理論》（玄奘译）开篇总颂、宗因喻定义、因三相、同品异品、现比二量定义、量果句、六不定与"聲常所量性故"双例；《因明正理門論》（义净译）开篇论纲与颂、合离喻颂、九句因总颂与"唯有二種名因"判定、现量颂与散文定义、"諸自證分"两句、唯二量句、他比量两支颂与散文、"說因宗所隨"颂、似能破与"足目"句、结颂——全部逐字命中（两遍核读：第一遍引前脚本验证 65 个关键片段一次通过；第二遍交付前对全部引文重跑，见四.5）。
4. **英文引句复核**：交付前对本包引用的 103 条 SEP 英文关键引句逐条与抓取原文做空白/标点归一后的全文比对（同日sep_*抓取文本），96 条一次命中；7 条差异逐条核查后确认 5 条为测试脚本自身伪影（藏文转写撇号断句、B02 引句误入测试集），2 条为本包真实缺陷并已修正；连同另 2 处于复核中发现的缺陷，共 4 处修正：①三类因例句 locator 中"śiṃśapā oak"后与"smoke is there"后的两处逗号为误加（原文无逗号，列表分行排版所致），已删；②"the Bhāṭṭa argues"应为句首"The Bhāṭṭa argues"，已改；③"In texts like the Hetucakra"应为"True, in texts like the Hetucakra"（小写、含前导词），已改；④Garfield 2006 参考文献条目经 grep 确认在 SEP Tsongkhapa 条（抓取文本命中 8 处）而 sep_dharm 文本为 0 命中，相关归属（packet cihai/7、evidenceLimits 第9条、evidence cihai/7 sourceRefs）已由 S2 更正为 S4。另：量-果同一句按源 HTML 实文核读作"pramāṇa and pramā."（原页面即此形），初稿误写为重构形"pramāṇa-result"，已改回源文原样并复核命中。汉译原典 65 片段与 packet 四处引语在两遍中均逐字命中。
4. **数量**：来源 6（学术百科 4 + 汉文原典 2）；evidence 记录 88 条（fieldPath 全部解析、locator 全部非空；其中 3 条本地数据核对记录——coverageNote/suggestedBookLinks/站内人物核对——sourceRefs 为空、locator 指向本地文件，与 B02 同例）；人物 8（站内 3：世亲、萨迦班智达、宗喀巴·罗桑扎巴；站外 5：陈那、商羯罗主、法称、Uddyotakara、鸠摩利罗；玄奘入 timeline 而不入 thinkers）；关系 9（端点全部为本包 thinkers，脚本核验通过）；时间线 10；术语 10；著述 8；分支 5；引语 4（quote 1 + quotes 2 + closingQuote 1）；readingRoutes 2；evidenceLimits 14。两个 JSON 经 python3 -m json.tool 校验通过；来源 ID 唯一、全部 sourceRefs 可解析、accessedAt 均为 2026-10-04（脚本核验）。
5. **写作中自行发现并改正的风险点**：①法称 URL 双写 ii 问题（见四.2）；②维基文库两处署名差异（见三.6）；③站内"商羯罗"（吠檀多）与商羯罗主（Śaṅkarasvāmin）同名异人——已在 evidenceLimits 与本文件声明，避免接入时误链；④玄奘译《入正理論》的"647年"等具体译年属模型常识而非本次来源，已从 timeline 剔除，只系于"唐"；⑤帝释慧（Īśvarasena）因材料仅两级且年代不明，未入 thinkers，只作 relations/陈那→法称 detail 中的中介呈现——避免了为凑人物数而立无据条目；⑥英文引句两遍复核发现的 4 处缺陷（三类因逗号×2、The Bhāṭṭa 大写、Garfield 归属 S2→S4）与 1 处 locator 按源文改回（"pramāṇa and pramā"），见四.4。
6. **任务要点覆盖自查**：现量/比量二量（cihai 1/2、S5/S6 原典）；自证（cihai 7，含汉译"諸自證分"原典层与 S2 两主题）；三类因（cihai 5，S1 例句逐字）；排除他指 apoha（cihai 8，S2 两节）；与正理-弥曼差论辩（subSchools 2、relations 2/3/5）；藏传量论课程传统（subSchools 4、relations 6/7/8、timeline 6/7/8）——任务列出的六项学说要点全部有来源与 locator 支撑。

## 五、仍缺证据（与 packet.evidenceLimits 对应）

- "《释量论》在格鲁课程中的地位"的教科书细节（辨析课次第、blo rig 前行等）：需藏传课程史专文（Dreyfus 1997 类专题仅确认存在，未核读内容）。
- 《量理宝藏论》内容与藏文书名构拟的文献学确认。
- "大域龍=陈那"等价关系与两部汉译译年的专书书目确认（大正藏校注类）。
- 汉传因明疏释建制（窥基等）与日本因明课程：需专文。
- Dharmottara（法上）注疏的年代与文本；帝释慧的独立传记材料。
- Kumārila 的直接定年（本包仅有 S1 侧记：普拉帕迦罗之师，后者属7世纪晚期）。

## 六、实际核读 URL 清单（2026-10-04，全部本任务独立抓取）

1. https://plato.stanford.edu/entries/epistemology-india/ （curl 全文 + python 去 tag 逐字定位）
2. https://plato.stanford.edu/entries/dharmakiirti/ （同上；注意 /entries/dharmakirti/ 为 404，正确 URL 双写 ii）
3. https://plato.stanford.edu/entries/logic-india/ （同上）
4. https://plato.stanford.edu/entries/tsongkhapa/ （同上）
5. https://zh.wikisource.org/wiki/因明正理門論 （curl 逐字；义净译本）
6. https://zh.wikisource.org/wiki/因明入正理論 （curl 逐字；玄奘译本）
- 探测后确认不可用：/entries/dharmakirti/、/entries/dignaga/、/entries/apoha/、/entries/logic-indian/、iep.utm.edu/dignaga|dharmakirti|buddhist-epistemology|indian-logic|apoha|tsongkhapa（均 404）。
- 本地实读（未修改）：app/public/philosophers.json、app/public/books.json、app/public/schools/data/school_印度哲学.json、app/public/schools/data/school_西藏哲学.json、docs/tasks/school-content-gap-tasks-2026-10-04.json、docs/content-proposals/schools/{T01,I01,I03,B03}/packet.json（查重对读）。
