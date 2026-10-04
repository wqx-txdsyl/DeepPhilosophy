# B05 天台宗思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B05`（proposedKind=school，P1-content-packet，coverage=related-branches-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定与 T01 分工

1. **T01 总览 → B05 专条的明确分工**。T01《佛教哲学》是跨地区问题地图：其天台内容仅三处（三谛节标目、一念三千节标目、三位代表年代句），且 T01 的 evidenceLimits 明言"天台'性具''性恶'、华严'四法界''六相'等术语未在本次核读来源中逐字出现，cihai 不收"。B05 恰好补齐：本包独立重抓 SEP buddhism-tiantai 全文（184KB，未复用 T01 片段），多轮提取新增覆盖——性恶与无情有性（§4.1）、化法四教全节（§3.2）、开权显实（§3）、法华中心地位（§5.1）、《摩訶止觀》为 locus classicus（§5.2）。建议 Codex 接入时两包互设导流：跨传统脉络归 T01，天台自身义理、文本与传承史归本包。
2. **宗派组织史与哲学论证分开**。subSchools 的 kind 分别标为"学说阵营"（山家/山外——争论双方不是两个新教团）与"地域传统"（日本 Tendai、高丽 Cheontae）；timeline 只收有独立证据的人物与事件节点，不设"某年开五时"一类判教性"年代"。
3. **判教按解释框架处理，不按编年处理**（S4 引 Peter Gregory／关口真大考证：成熟五时八教体系出湛然之手，智顗从未一次给全）——这是本包最重要的防误读决定，cihai 与 conclusion 均显式声明。

## 二、山家/山外年代问题与审校任务书的衔接

任务书第7节点名："现有学术归属修复，例如……隋唐佛学下的宋代山家／山外分支，由 Codex 处理。若本包涉及这些内容，给出正确的关系建议和出处。"

本包核实结果与处置：

1. **站内实查**（2026-10-04 python 读 `app/public/schools/data/school_隋唐佛学.json`）：subSchools[0] 天台宗山家派、subSchools[1] 天台宗山外派，两分支 **era 字段本身已是"北宋"**，描述（知礼/妄心观/性具善恶 vs 真心观）与来源一致；错置点在于**父级条目**——北宋争论挂于《隋唐佛学》名下。因此"错置年代"应理解为父级归属错置，而非 era 字段错误。
2. **本包如实按宋代处理**：subSchools 两条均标"北宋"；timeline 节点年份作"约10世纪末—11世纪前半（北宋）"（争论起讫年两源均只到"宋"，不造精确年份）；争论世系按 S4＝义通（927—988）→ 知礼（960—1028）/遵式（964—1032），钱塘悟恩（Wu'en）为山外之源；S5 补仁岳（992—1064，师事知礼十余年后转倡山外，后山外代表）。
3. **给 Codex 的关系建议**（packet.proposal.relationSuggestions）：以本包来源化表述替换/深化旧两分支文本；kind 建议标"学说阵营"；父级归属（隋唐→宋）调整与《隋唐佛学》cihai 中"一念三千"重复条目的清理由 Codex 一并处理，本包不代改旧条目。

## 三、分歧与争议的处理

- **祖师世数**：S4（英文维基）以龙树＝初祖、慧文＝第二代、慧思＝第三代、智顗＝第四代，且明言世系"由后世佛教徒提出，不反映当时僧众实际声望"；S5（中文维基）称慧思为二祖。本包不采单一世数，行文作"龙树—慧文—慧思—智顗递传（世数各谱不一）"，两处 locator 均录原句。
- **世系的历史性**：packet 在 overview 与 relations[0]（龙树→智顗）两处显式声明：尊龙树为初祖是传统尊奉＋文本所依关系，不是历史师承。
- **传灯卒年**：S4 作 1554-1628，S5 作 1554-1627，相差一年——timeline 取 1554—1627 并在 evidence 记录并陈。
- **慧文生卒**：两源均无载，timeline 只作"6世纪（北齐）"，不造年代。
- **最澄具体日期（本包最重要的来源质量决定）**：en.wikipedia Saichō 条目已打开核读，载最澄 767—822、804 年入唐、822 年（身后）得大戒之允等；但该条目 2026 年 7 月带有"可能含 LLM 生成文本"（may incorporate text from a large language model）的活跃维护横幅。**本包不采其任何具体日期**，最澄条目纪年仅作"9世纪初在世"，东传节点仅依 S4 两句（"branched off from Tiantai during the 9th century"；Daosui 为其师）。该条目已列 review.md URL 清单并注明弃用原因。
- **SEP 与维基文库一字异文**：SEP 转写一念三千段作「若無心而己」，维基文库（大正藏底本）作「若無心而已」（己/已）。本包中文引文一律从维基文库，异文已入 evidenceLimits 与 evidence.json。
- **《大乘止观法门》**：S4 明言它是"一部可能影响了智顗的6世纪著作"（托名之疑），不列为智顗著作。

## 四、查重与既有内容

- 任务 JSON：exactTopLevelEntries／exactBranches 均空；relatedBranches 2 项（隋唐佛学→山家/山外）；mentionFiles 1 项（隋唐佛学，命中词"天台宗"）。站内无同名顶级条目，本包为该主题首个专门深度条目，coverage=related-branches-only 处置成立。
- **人物**：站内 philosophers.json 实查（python）有 智顗（538-597年）、龙树（约150—250年），本包 thinkers 采用站内姓名与纪年；慧思、灌顶、湛然、知礼、仁岳、最澄站内无，按契约保留准确姓名、在 sub 字段标注，不改动哲学家名单（站外人物 6 名，已逐一如实标注）。
- **书籍**：books.json 实查（python，天台/法华/止观/摩诃/智顗等关键词）仅《中国佛教史》1201d003be31（蒋维乔，epub 21章）为佛学专门藏书；无《摩诃止观》《法华经》等原典藏书。建议关联只列该种，并声明未核读内容、不能写成"天台原著可在线阅读"。南怀瑾合集（a26240ee8f45）为国学泛选，不作天台专门关联。
- **既有子项复用**：站内《隋唐佛学》已有天台系 cihai 词目（天台/判教/一念三千/圆融三谛/止观，部分词目带英文名重复待清理）与《摩诃止观》《法华玄义》书目条目——本包为它们补齐来源与定位（大正藏编号、卷帙、注疏配套），属"已有子项要复用并深化"，不重复造页面。

## 五、复核方法与结果

1. curl 全文抓取：SEP buddhism-tiantai（184KB）、维基文库《摩訶止觀》目录页＋卷005（150KB）、维基文库《妙法蓮華經玄義》目录页、en.wikipedia Tiantai Buddhism（838KB）、zh.wikipedia 天台宗（299KB）、en.wikipedia Saichō（52KB）。检索摘要一律不作为依据；所有关键引文（中英文）均在全文中逐字定位命中。
2. evidence.json 共 68 条记录（overview 9、thinkers 8、relations 7、timeline 11、cihai 12、works 8、subSchools 4、引语 4、proposal/coverage/书籍/relatedExisting 与 conclusion 5——其中查站内文件者无站外来源，sourceRefs 留空并在 locator 注明实查文件），每条含 verbatim 定位；全部 fieldPath 均经脚本回解析到 packet.json 对应节点。
3. 数量：来源 5（学术百科 1 ＋ 原典 2 ＋ reference 2）、人物 8、时间线 11、术语 12、著述 8、分支 4——在契约参考区间（S1 支持学说范围与归属，S2/S3 支持原典；reference 级来源占比与用途已声明）。
4. 两个 JSON 经 `python3 -m json.tool` 校验通过；relations 七条端点逐一比对等于 thinkers[].name 精确字符串。

## 六、仍缺证据（与 packet.evidenceLimits 对应）

- 山外前期人物（源清、庆昭、智圆）：无核读来源，不写。
- 性恶说原典出处句（《观音玄义》系"阐提不断性善，佛不断性恶"一系文字）：未逐字核读，只按 S1/S4 转述。
- 《法华玄义》《法华文句》正文、三大部章节结构：未核读（玄义仅目录页）。
- CBETA 在线版正文 JS 渲染无法抓取，《摩訶止觀》未做第二藏经对勘，以维基文库（大正藏底本）为唯一文本凭据。
- 知礼"蜣螂例"汉文出处、六即与四种三昧操作细节、《摩訶止觀》日本传本异同、天台对禅净影响机制：均未核读，不写。

## 七、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/buddhism-tiantai/ （curl 全文＋多轮 grep 逐字）
2. https://zh.wikisource.org/wiki/摩訶止觀 （目录页，curl）
3. https://zh.wikisource.org/wiki/摩訶止觀/卷005 （全文，一念三千/一心三观/三谛句逐字命中）
4. https://zh.wikisource.org/wiki/妙法蓮華經玄義 （目录页，curl）
5. https://en.wikipedia.org/wiki/Tiantai_Buddhism （curl 全文＋定位）
6. https://zh.wikipedia.org/wiki/天台宗 （curl 全文＋定位）
7. https://en.wikipedia.org/wiki/Saich%C5%8D （已打开核读；因活跃 LLM 内容维护横幅，**仅用于 review 记录，未采入 packet**）
- 放弃：https://www.britannica.com/topic/Tiantai （反爬页，仅 5KB，无正文）；https://cbetaonline.dila.edu.tw/zh/T1911_005 （JS 渲染，抓不到正文）。
- 说明：SEP buddhism-tiantai 本日 T01 工作曾核读三处片段；本包按任务提示选择**独立重抓全文**（推荐路径），非复用。
