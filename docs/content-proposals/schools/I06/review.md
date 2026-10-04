# I06 耆那教哲学（Jain Philosophy）—— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I06`（proposedKind=school，P1-content-packet，cohort=南亚，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。

## 一、边界决定

1. **范围锁定：多面论、认识论、伦理与生命观，宗教实践分开**。按任务 scopeAndCautions，本包以 anekāntavāda（多面论）、七支谓词（syādvāda/saptabhaṅgī，附"非七个真值"辨析，S2 逐字）、nayavāda（视角论）、ahiṃsā 与业物质说为主干；教派组织（Digambara/Śvetāmbara 的僧团形态、女性观、正典范围之争）按 S5/S7 写为**组织与文献背景**，不与哲学主张混写；造像、斋戒、朝圣等仪轨完全不展开。subSchools 前两条标 `kind: 教派`，后两条标 `kind: 文本传统/主题`、`kind: 学说传统`——避免把主题当组织分支。
2. **不写"七值判断/七值逻辑"**。任务提示用"七值判断"，但 S2 明辨"这七种谓词不该被理解为七个真值，因为它们全部七者都被认为是真的"（逐字）；本包统一用"七支谓词"，syāt 的三种译法并列（evidenceLimits 第8条）。
3. **不拔高"科学性"**。S1 原文只说经卷"被一些耆那教徒视为科学论著"——这是社群自我理解的记录而非本百科背书；本包明写此限定（conclusion），拒绝"最古老的生态哲学""古代科学"类无据赞誉（任务规范点）。
4. **大雄与祖师传统的证据边界**。所有年代标注"传统纪年"：S1 "traditional dates 599–527/510 BCE"、S6 "599 BCE...some modern scholars prefer 540 BCE, or even later"；"创始人"措辞被两条来源否定（S6："He is sometimes wrongly called 'the founder of Jainism'"；S2："According to its own traditions...have no founder"）。Pārśva 传统（大雄父母为其 follower、四原则＋大雄加贞洁，S6）按"前史（传统叙事）"入时间线，不系年、不写序数。
5. **甘地—ahiṃsā 只写到有据处**。S3 逐字："Mohandas Gandhi is perhaps the most famous adherent of ahimsa of the last century"＋三教共享 ahiṃsā；直接师承渠道（通说的 Śrīmad Rājacandra）**不在核读来源内，不作断言**。站内甘地小传只提印度教非暴力与托尔斯泰、梭罗、未提耆那教——两条记载兼容但各为侧影，处置建议提交 Codex（evidenceLimits 第7条）。
6. **站内"凯格姆尼"条目不采用**（详见"五、重要纠错与存疑"）。
7. **与 I01（正理派）的关系**：只写"同处南亚辩论厅生态"的共同背景与编辑对勘；两派具体人物会面不在来源内，不写（relations/subSchools 已注明"编辑比较"）。

## 二、查重结论

- **学派条目**：任务 JSON 的 exactTopLevelEntries / exactBranches 均为空；python3 复查 `app/public/schools/catalog.json`（无"耆那"）与 `app/public/schools/data/`（无同名文件）。mentions-only 成立：`school_印度哲学.json` 一处来源，"耆那"15处（11个字段：subtitle、overview、thinkers/4、relations/3、timeline/2、timeline/9、quotes/3、cihai/12、cihai/18、cihai/22、cihai/29），"耆那教哲学"整词1处，"大雄"6处、"筏驮摩那"1处、"Ahimsa/ahimsa"6处。
- **人物**：`app/public/philosophers.json`（737人）python3 检索：**无** 大雄／筏驮摩那／Mahavira／Kundakunda／Umāsvāti／Samantabhadra／Siddhasena／Akalaṅka 等条目——本包主要人物为**站外人物**（契约允许）。有两条站内关联人物：**甘地**（school=印度哲学，1869-1948年）与**商羯罗**（约7—8世纪，站内纪年有争议），本包按"接受史人物""对手方"收录并沿用站内姓名与纪年。另有站内条目"**凯格姆尼**"（school="耆那教/非暴力哲学"）自称耆那教人物——见"五、重要纠错与存疑"，本包不采用。
- **书籍**：`app/public/books.json`（409种）python3 检索"耆那/Jain/筏驮摩那/Mahavira/大雄/甘地/Gandhi"：无耆那教相关藏书（含"印度"的4种书为《悉达多》、叔本华两种、《世界哲学简史》，均不相关）。故 `relatedBookIds` 为**空数组**，readingRoutes 全部指向站外来源。
- **旧正文处理**：站内《印度哲学》的 mentions 不继承为学理依据；其时间线"公元前599"纪年与传统纪年相容但"创始人"措辞、"works《阿含经》"归属、cihai"耆那教 source《阿含经》"、quotes"非暴力是最高的法"（原句不在来源内）均不入本包，处置建议见 evidenceLimits 第10—12条。

## 三、分歧与争议的处理

- **《谛义证得经》年代与作者**：S1 作"归名 Umāsvāmin、很可能多作者、约150—400年"，注（Umāsvāti）400—450年。任务提示的"约2—5世纪有争论"与之相容；本包从 S1 并并录两名（经主/注主是否同一人不在来源讨论内，evidenceLimits 第4条）。
- **大雄年代**：S1（599–527/510）与 S6（599–527，另有"540 BCE, or even later"之说）并存，一律写"传统纪年"并注明（evidenceLimits 第1条）。
- **Kundakunda 个人 vs 传统**：S1 采集体作者权说（"'Kundakunda' is actually not a single author..."，逐字），与通说个人传记不同——本包从 S1；其教派归属（通说天衣派）未在 S1 文本标注，不作断言（evidenceLimits 第6条）。
- **Siddhasena 年代**：S1 作 710–780 CE；通说"约5—6世纪 Siddhasena Divākara 与约7世纪 Siddhasena Mahāmati 之分"不在来源内，本包从 S1 不作两 Siddhasena 之辨（evidenceLimits 第13条）。
- **Kundakunda"接近数论"**：S1 逐字 "close to Sāṃkhya conceptions, while keeping the Jaina specificity of an essentially active self"——写为学理相似，非影响或师承。
- **syāt 译法**：S2 用 perhaps 并注或译 "from a perspective"/"somehow"——并列照录，不裁决。

## 四、译名政策

- 站内已用写法："大雄""筏驮摩那"（school_印度哲学.json）、"商羯罗""甘地"（philosophers.json）——直接沿用。
- 站外人物 Umāsvāmin/Umāsvāti、Kundakunda、Samantabhadra、Siddhasena Mahāmati、Akalaṅka Bhaṭṭa、Haribhadrasūri、Prabhācandra：**通行汉译未获核实，主名用梵文拉丁转写**（evidenceLimits 第16条）。
- 作品题名：《谛义证得经》（Tattvārthasūtra）为学界通行译法（任务单同用；未见于核读来源，已注明）；其余（"御注""逻辑入门""非一边论胜利幢""自我之精华""权威之研究""中洲辑要""所知莲之日"）为依 SEP 英文 gloss 的**编辑意译**，works.desc 或 evidence 均注明性质，梵文原名并列。

## 五、重要纠错与存疑（提请 Codex，本包不改站内数据）

1. **站内哲学家条目"凯格姆尼"（Keśin？）疑误**。该条目（school="耆那教/非暴力哲学"，era 约公元前6—前5世纪）称其为"早期耆那教思想体系中的关键人物、非暴力哲学（ahiṃsā）的重要奠基者之一"，并载"灵魂平等的系统化论证""与同时代思想家（包括佛教僧侣）的辩论""业力物质说的独特解释""最重要的文献是《经造支》（Sūtrakṛtāṅga）中保留的论述"等。核查结果：本包三个学术来源（SEP Jaina Philosophy 2023、IEP Jain Philosophy、BBC Religion）**均无此人**；所述学说形态（在 Mahāvīra"改革前"已成体系的"灵魂平等"论证、与佛教僧侣辩论）与来源中的任何人物不合。存疑线索：耆那正典中确有 Kesi 其人——《上支经》（Uttarādhyayana）中 Kesi（Pārśva 传统弟子）与 Gautama（大雄弟子）的对话，检索线索指向 Lecture 23（herenow4u.net 译文页与 sacred-texts.com Jacobi 译本页均返回 403，未能核到原文）；站内条目或为对这一正典传统的讹变（年代、事迹、师承均被改写）。**处置建议**：该条目按站外人物核对流程复核，核对前不宜在站内学理页面引用。
2. **站内《印度哲学》"大雄 works《阿含经》"与 cihai"耆那教 source《阿含经》"**：'阿含'为佛教早期经典通名，耆那教正典通称 Āgamas（S7 逐字："The texts containing the teachings of Mahavira are called the Agamas, and are the canonical literature - the scriptures - of Svetambara Jainism."）。建议改指"耆那教阿含（Āgama）"。
3. **站内 timeline"耆那教创始人筏驮摩那出生"**：纪年（前599）与传统纪年相容；"创始人"措辞与 S6/S2 相悖（见"一、4"），建议改为"此世劫最后一位祖师大雄（传统纪年）"。
4. **站内 timeline"公元788 商羯罗出生"与 philosophers.json 商羯罗条目"约7—8世纪（具体纪年有争议）"不一致**；且时间线"复兴印度教，对抗佛教和耆那教"的"对抗耆那教"仅与 IEP 所载商羯罗对七支谓词的批评方向一致、细节未核。均留 Codex 处置，本包不裁断。
5. **站内 quotes/3"非暴力是最高的法"（author 耆那教经典，paraphrase）**：与教义一致，但对应原句（通传 ahiṃsā paramo dharmaḥ）不在核读来源内，本包不引。

## 六、复核方法与结果

1. 七个网络来源 2026-10-04 实际抓取并读到相关段落（curl 全文缓存＋python 去标签转文本；SEP 搜索接口用于确认 SEP 无 /entries/jainism/ 且存在 /entries/jaina-philosophy/，Gorisse 署名经 DC.creator 元数据确认）。evidence locator 所引英文 verbatim 文本经脚本对缓存文本**两轮逐字比对：共105处检查，6处按原文措辞修正后命中**（含七式句原文语法形态 "exist and does not exists" 照录、BBC "Svetamabara" 拼写笔误照录、上标数字抓取形态说明），未命中即修正或不用。
2. evidence.json 共 76 条记录，JSON Pointer 对位 packet.json：overview 19、conclusion 3、thinkers 9、relations 7、timeline 10、cihai 10、works 8、subSchools 4、quote/quotes/closingQuote 4、relatedBookIds 1、coverageGap 1。
3. 数量：人物 9（含对手方商羯罗、接受史人物甘地；超出 4—8 参考区间，因甘地关联是任务明示要点、商羯罗批评是来源明载的古典批判节点，故保留并说明）、时间线 10、术语 10、著述 8、分支 4、关系 7、阅读路线 2。
4. 两个 JSON 以 `python3 -m json.tool` 校验通过；来源 ID（S1—S7）唯一且所有 sourceRefs 可解析（脚本核对）。
5. 边界自检：仅写入 `docs/content-proposals/schools/I06/`；未动 app/、backend/、现有 schools 数据、进度台账；未运行 git 命令。

## 七、仍缺证据（与 packet.json evidenceLimits 对应）

- 大雄年代的可考纪年（现只有传统纪年与"更晚"之说）。
- 《谛义证得经》经主/注主（Umāsvāmin/Umāsvāti）同一人问题的文献学讨论。
- 天衣/白衣分派的年代与过程（两来源均未给出）。
- Kundakunda 的教派归属与个人传记（S1 采集体作者权说）。
- 甘地受耆那教影响的直接文献渠道（导师、文本、社群）。
- 耆那教对佛教"一切皆无常/刹那灭"的直接论战文本（本包只写正面命题"一切存在者同时恒住且变化"与反对"唯非复合统一者为实在"，未写论战形态）。
- 《上支经》Kesi—Gautama 对话原文（Jacobi 译本页 sacred-texts 403；herenow4u 403）——用于"凯格姆尼"条目复核。
- Umāsvāti/Kundakunda 等的通行汉译名核实。
- 无阻塞：七来源全部可核读，本项可进入 Codex 审读。

## 八、实际核读 URL 清单（2026-10-04）

已核读并采为 sources：

1. https://plato.stanford.edu/entries/jaina-philosophy/ （S1；curl 全文缓存，DC.creator=Gorisse, Marie-Hélène；First published Mon Feb 13, 2023；逐字引文约30处）
2. https://iep.utm.edu/jain/ （S2；curl 全文缓存，38KB；作者信息：Mark Owen Webb, Texas Tech University；逐字引文约20处）
3. https://plato.stanford.edu/entries/pacifism/ （S3；curl 全文缓存，DC.creator=Fiala, Andrew；逐字引文6处）
4. https://plato.stanford.edu/entries/perception-india/ （S4；curl 全文缓存，DC.creator=Chadha, Monima；题名 "Perceptual Experience and Concepts in Classical Indian Philosophy"；耆那教定位句1处——任务 researchLead 之一，限度如实记录）
5. https://www.bbc.co.uk/religion/religions/jainism/subdivisions/subdivisions.shtml （S5；页面归档，Last updated 2009-09-11；教派事实）
6. https://www.bbc.co.uk/religion/religions/jainism/history/mahavira.shtml （S6；页面归档，Last updated 2009-09-10；大雄传统传）
7. https://www.bbc.co.uk/religion/religions/jainism/texts/texts.shtml （S7；页面归档，Last updated 2009-09-11；正典传承，文末引 Paul Dundas）

查证但未获采（403/404）：

- https://plato.stanford.edu/entries/jainism/ （404——SEP 无此 URL，正条目为 jaina-philosophy）
- https://iep.utm.edu/jainism/ 、https://iep.utm.edu/mahavir/ 、https://iep.utm.edu/gandhi/ 、https://iep.utm.edu/anekantavada/ （404）
- https://www.sacred-texts.com/jai/sbe22/ 、https://www.sacred-texts.com/jai/sbe45/ （403——Jacobi 译本，Kesi 对话原文未获）
- https://www.herenow4u.net/index.cfm?id=71514 （403——Uttarādhyayana 译文，Kesi 线索未核到原文）
- https://www.britannica.com/topic/Jainism 、https://pluralism.org/jainism （403，未用）
- https://www.jainpedia.org/themes/principles/jain-sects.html （404，未用）
- SEP 搜索接口（searcher.py，query=jain / gandhi）：用于确认条目存在性，不作内容依据。

站内核对（python3，非网络来源）：

- `app/public/philosophers.json`（737人查重：无本包主要人物；甘地/商羯罗条目细读；"凯格姆尼"条目存疑记录）
- `app/public/books.json`（409种查重：无耆那教藏书）
- `app/public/schools/data/school_印度哲学.json`（mentions-only 复核，"耆那"15处定位）
- `app/public/schools/catalog.json` 与 `app/public/schools/data/`（无同名条目）
- `docs/tasks/school-content-gap-tasks-2026-10-04.json`（I06 条目提取）

## 九、同日草稿处置记录（2026-10-04 第二轮独立复核）

按流程要求，发现目录内已有同日草稿（10:26—10:32 写成）后未盲信，换用独立会话对全部七个来源逐源重开核实，再决定保留/重写。

**逐源复核结果（2026-10-04，全部命中，保留采信）：**

1. S1 SEP "Jaina Philosophy"：WebFetch 逐段核读＋curl 原始 HTML。署名经 `citation_author`/`DC.creator` 元数据确认为 "Gorisse, Marie-Hélène"；"First published Mon Feb 13, 2023" 确认。抽验命中（逐字）：`set of philosophical investigations`、`the oldest extant Jaina treatise in Sanskrit`、`karmic matter is never genuinely mixed (with the self)`、`close to Sāṃkhya conceptions`、`not two, but seven modes of predication`、`Haribhadra is deeply influenced by the Investigation on Authority (Āptamīmāṃsā [Āmī]) of Samantabhadra`、Āmī 14 四性句、vibhajya 句（`instead of answering philosophical questions in a one-sided way, the teacher was analyzing (vibhajya) them`）、七式句（原文用 `inexpressible`，非 `unspeakable`）、`considered by some Jains as scientific treatises`、TS 1.4 七谛、TSBh（Umāsvāti, 400–450, jñāna/darśana）、PKM gloss、JDS 770 CE、Siddhasena/Akalaṅka＋注疏链、Bhagavatīsūtra loka 之问与层累年代。另确认：七式展开句位于 AJP 语境，SEP 原文句为 "The Jaina author who spends the most time on elucidating… is probably Haribhadrasūri in his Victory banner… (AJP)"＋"Now, Jainas are known to go further…"——草稿将七式系统化与 AJP/Haribhadra 相系、四性溯至 Āmī 14 的写法与原文相符（且草稿已用"相系"等审慎措辞）。
2. S2 IEP "Jain Philosophy"：全要点命中，作者信息确认为 Mark Owen Webb, Texas Tech。逐字修正两处以贴原文：pramāṇa 清单句实为 `Notably absent from the list is inference`（evidence.json 本已记录正确原文，草稿中文转述无碍）；商羯罗批评实为 `obvious ground of inconsistency`（草稿译"明显不自洽"准确）；结尾句 `What begins as a laudable fallibilism ends as an untenable relativism` 命中。
3. S3 SEP "Pacifism"：命中 `Mohandas Gandhi is perhaps the most famous adherent of ahimsa of the last century.`（全句含 "Mohandas"）与 `Hindus, Jains, and Buddhists share a concern for ahimsa or nonviolence as a basic moral virtue.`；satyagraha 原文为 `the force of love or force of truth that he called satyagraha`、brahmacarya 为 self-renunciation——草稿"奠基"措辞与其相容。署名经元数据确认为 Fiala, Andrew。
4. S4 SEP "Perception…India"：分类句逐字命中（`robust realist… Nyāya-Vaiśeṣika and Mīmāṃsā… nominalist by the Buddhist schools… conceptualist by the Vedāntins and Jainas`）＋明言不展开概念论论证。署名元数据 Chadha, Monima。
5. S5 BBC subdivisions：七要点全命中；"more austere… closer in its ways to the Jains at the time of Mahavira" 系页面表述而非天衣派自述——已把 S5 coverage 中"自认更近大雄时代"改为"（BBC 页面表述）其方式更接近大雄时代"。"两派尼众皆着衣"命中（未着白色，草稿未作白色断言，正确）。
6. S6 BBC mahavira：七要点全命中（599 BCE＋"540 BCE, or even later"；kshatriya；父母为 Parshva follower；"sometimes wrongly called 'the founder of Jainism'"；12年半；527 BCE 依 Śvetāmbara 文本；14000僧/36000尼；归档 2009-09-10）。
7. S7 BBC texts：六要点全命中（Āgamas 句、口传与非持有誓、约前350年饥馑、天衣全失/白衣大部存、Purvas 失传、Dundas `beginningless, endless and fixed truths, a tradition without any origin, human or divine`；归档 2009-09-11）。

**草稿处置决定：保留主体，两处小修。**

- 修正一：packet.json 与 evidence.json 中"不自合/不自洽"混用（4+1 处 vs 4 处）→ 统一为"不自洽"（共5处替换），与 IEP 原文 `obvious ground of inconsistency` 及草稿 overview/conclusion 的主流用词一致。
- 修正二：S5 coverage 的"自认更近大雄时代"改为"（BBC 页面表述）其方式更接近大雄时代"（原文性质是 BBC 页面的比较表述，非教派自述）。
- 其余内容（overview/conclusion/人物/关系/时间线/术语/著述/分支/阅读路线/evidenceLimits/evidence.json 76 条/artwork-brief）经逐源复核与抽查均与来源相符，原样保留；evidence.json 的英文 verbatim 记录抽查未见与原文冲突（`Notably absent…` 等抽查项记录的即正确原文）。
- 复核后两个 JSON 经 `python3 -m json.tool` 校验通过；reviewMethod 已更新为两轮核验说明。
- 范围自检：本轮仅改动 I06 目录内 packet.json（2处）、review.md（本节）、此前一轮的 5 处用词替换；未动其他任何文件，未做任何 git 写操作。
