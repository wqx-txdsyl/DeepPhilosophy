# F03 逻辑与逻辑哲学 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `F03`（proposedKind=field，cohort=跨传统问题，P1-content-packet，coverage=related-branches-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查·两轮核读，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。
- 版本说明：本包经两轮独立核读（同日 2026-10-04）。首轮以 WebFetch 核读 10 个来源成稿；二轮复核以 curl 抓取全文逐字比对，修正两处结构问题、新增 8 个来源（S11–S18），详见「八、二轮复核记录」。

## 一、边界决定

1. **形式逻辑与逻辑哲学分两层写，且互相咬合**。这是任务 scopeAndCautions 的核心要求。包内安排：overview 第1段与 subSchools[5][6] 承载逻辑哲学（后承的必然性/形式性、证明 vs 模型、一元/多元/虚无、规范性），时间线与 thinkers 主线承载形式逻辑的文献节点；conclusion 把两层的遗留问题（挤榨论证、collapse、元逻辑自反）合并交代，避免写成互不相干的两个学科（S1、S3）。
2. **领域无『创始人/成立年』**。仅按 S10 写『系统研究始于亚里士多德』的通行定位及其史前线索；时间线 10 节全部是著作/翻译/建制/论文节点，无一虚构『成立于某年』；《前分析篇》与《墨经》均写证据区间（『公元前4世纪』『前4世纪末—前3世纪中叶』），不写单一年份。
3. **跨传统：平行发展 + 编辑比较，绝不写师承或虚构传播**。任务给出的三大传统（希腊、印度因明/正理、墨辩）中，包内只写入有逐字核读来源的三处：墨经（S5 + 维基文库四章 S12–S15）、正理经与筏蹉衍那（S9）、陈那—法称（S4）。relations 中跨传统一对（亚里士多德—法称）type=『编辑比较』，detail 自注『无传播关系证据』。唯一有据的跨文明传导照实写：《工具论》830s—10世纪初译入阿拉伯世界（S7）；佛教量论入藏、在中国几乎未传（S4）。希腊—印度—中国三者之间：两轮核读的全部来源均无接触/传播线索，一律不写（二轮复核重抓 logic-india 全文确认其东传叙述仅指向中国—朝鲜—日本）。波尔-罗亚尔逻辑、维特根斯坦、蒯因只标边界不代述（斯多葛与拉丁中世纪逻辑经二轮复核已补入领域层骨架，见「八」）。
4. **与既有相关子项的边界（逐一说明，均不改动）**：
   - 理性主义 → 「波尔-罗亚尔逻辑学派」（subSchools[4]，任务 relatedBranches 唯一项）：本包未核读其相关来源，不代述；仅在 subSchools[0] 与 proposal.relationSuggestions 中建议从本领域入口互设『参见』。
   - 任务 mentionFiles 共 22 个文件：二轮复核将 proposal.relatedExistingEntries 修正为与任务清单完全一致的 22 项（印度哲学、古希腊哲学、墨家、名家、斯多葛学派、怀疑论、伊斯兰哲学、阿拉伯哲学、唯名论、理性主义、经验主义、唯心主义、德国古典哲学、北欧哲学、高加索哲学、天演论、实用主义、分析哲学、过程哲学、后现代主义、伦理学、蒙古中亚哲学）；抽查确认均为『逻辑学/逻辑哲学』字样级提及，不构成领域入口。
5. **研究领域规范执行**：timeline 全部为文献、翻译、建制或论文事件；术语、著述、人物条均给出著述定位（如『《前分析篇》I.2』『SEP 条目某节』），不写页码。
6. **配额不凑数**：跨传统仅印度（2 处来源）、中国（1 处来源）入正文，其他传统（如蒙古中亚哲学 mention）因无可核读来源一律不写。

## 二、分歧与争议的处理

- **法称年代**：S4 原文列出 Frauwallner（600—660）、Krasser 2012（推前至六世纪中）、Balcerowicz 2016（约550—610）并主张『谨慎乃至不可知』。包内时间线写『6—7世纪之际（年代有争议）』，thinker 条不写生卒，仅写活动期诸说。
- **亚里士多德模态三段论**：S2 载『两个 Barbara』难题与诸家重构（Becker、McCall、Nortmann、Thom、Rini、Malink 2013），包内只说『自古代起即争论不休』，不选边。
- **阿维森纳三段论体系的成败**：S7 同时给出『13世纪学者认其系统性混乱』与『学者仍在争论是失败还是复杂体系』两层，包内写成『既承袭又批评』，不下判决。
- **一元/多元/虚无主义**：S3 的赞同论证与四类反驳（generality、collapse、change-of-meaning、metalogic）并陈，overview 与 conclusion 均不站队；卡尔纳普句逐字引录（S3）。
- **『第二导师』称号**：S7 明确该称号是阿维森纳对法拉比的尊称；包内 relations[0] 严格照此写，未把『第二导师』误安在阿维森纳头上（常见讹误，已规避）。
- **真/可证之分**：S8 澄清『存在绝对不可证的真理』是误读；thinkers[5] 与 conclusion 照录这层限定，不传播流行误读。
- **译名统一**：validity=有效性；logical consequence=逻辑后承；trairūpya=因三相；vyāpti=遍充；bian=辩。『因明』一词因汉译源流未获来源支持而不用于正文（见 evidenceLimits 第6条）。

## 三、查重结论

- exactTopLevelEntries / exactBranches 均空（任务 JSON）；python 实查 `app/public/schools/data/` 全部 111 个 JSON，无『逻辑』类顶级条目 → 无同名冲突，本包为净增领域入口。
- relatedBranches 唯一项「波尔-罗亚尔逻辑学派」（理性主义 subSchools[4]）关系建议见上节第4条；未动原文。本包为领域总览，不重复该子项内容（波尔-罗亚尔仅出现在 subSchools[0] 边界指引、works 边界与 relationSuggestions）。
- 22 个 mention 文件不逐条立传，proposal.relatedExistingEntries 已与任务清单逐一对齐（22/22）。

## 四、人物与书籍核对结果（grep/python 实查，两轮各自独立执行）

- **站内人物（4位，姓名与纪年均照录 philosophers.json）**：亚里士多德（前384—前322）、阿维森纳（10世纪后半叶—1037，生年有争议）、戈特洛布·弗雷格（1848-1925；卒年 1925-07-26 亦见 S6）、克律西波斯（约前279-前206年，二轮复核新增，S16 载其约前230—前206主持学园）。
- **站外人物（4位设 thinker，均 grep 实查 NOT FOUND，包内已标注）**：陈那（约480—540，S4）、法称（年代争议，S4）、库尔特·哥德尔（era 仅写『20世纪』）、阿尔弗雷德·塔尔斯基（era 仅写『20世纪』）。站外且不设 thinker 者仅出现在 timeline/works：乔达摩（足目）、筏蹉衍那（S9）。『因明』相关汉传人物（玄奘等）因无来源支持一律未写。
- **书籍（6 个 ID，python 在 books.json 逐条实查，2026-10-04）**：工具论 b471f41a78de（16章）、算术基础 c0fc56d645dc（4章）、逻辑哲学论 5d906139d1b2（11章）、从逻辑的观点看 07f28f142bdc（0章占位）、数学原理 e6c890fcd84e（0章占位，二轮复核新增；S18 支撑其定位，站内署名仅罗素、实为合著）、逻辑大全 ad4153e66d7e（0章占位，二轮复核新增；S17 支撑其定位）。0 章占位书目 reason 均已注明不可在线阅读；在库译本内容均未核实。

## 五、实际核读 URL 清单（2026-10-04）

首轮（WebFetch 打开并读相关段落）：

| id | URL | 核读范围 |
|---|---|---|
| S1 | https://plato.stanford.edu/entries/logical-consequence/ | 全条目要点（定义、必然性/形式性、Tarski 1936、证明论、规范性、多元） |
| S2 | https://plato.stanford.edu/entries/aristotle-logic/ | 全条目要点（Organon、I.2 定义、三格、化归、模态难题、现代解读） |
| S3 | https://plato.stanford.edu/entries/logical-pluralism/ | 全条目要点（GTT、诸反驳、虚无主义、Carnap） |
| S4 | https://plato.stanford.edu/entries/dharmakiirti/ | 全条目要点（年代之争、著作、两支论式、因三相、影响） |
| S5 | https://plato.stanford.edu/entries/mohist-canons/ | 条目主体（年代、结构、辩、名实；『小取』论证法部分在首轮抓取中被截断，未采用——二轮已由 S14 原典补足） |
| S6 | https://plato.stanford.edu/entries/frege/ | 全条目要点（1879、Grundlagen、Grundgesetze、罗素来信、1892） |
| S7 | https://plato.stanford.edu/entries/arabic-islamic-language/ | 全条目要点（翻译运动、法拉比、阿维森纳、madrasa、13世纪教科书） |
| S8 | https://plato.stanford.edu/entries/goedel-incompleteness/ | 全条目要点（两定理、年表、希尔伯特纲领、真/可证、反机械论；文献表抓取截断） |
| S9 | https://iep.utm.edu/nyaya/ | 全条目要点（正理经、筏蹉衍那、四量、五支、新正理） |
| S10 | https://www.britannica.com/topic/history-of-logic | 仅开篇希腊起源段（订阅墙截断），coverage 已如实收窄 |

二轮复核（curl 抓取全文后 grep/python 定位逐字比对）：

| id | URL | 核读范围 |
|---|---|---|
| S11 | https://en.wikisource.org/wiki/The_Works_of_Aristotle/Prior_Analytics/Book_I | I.1–2 定义、完全三段论定义逐字；页面头部译者/编者信息（Jenkinson 译、Ross 编 1928、Bekker 页码） |
| S12 | https://zh.wikisource.org/wiki/%E5%A2%A8%E5%AD%90/%E7%B6%93%E4%B8%8A | 『故，所得而後成也』『辯，爭彼也。辯勝，當也』『名，達、類、私』逐字 |
| S13 | https://zh.wikisource.org/wiki/%E5%A2%A8%E5%AD%90/%E7%B6%93%E8%AA%AA%E4%B8%8A | 小故/大故句逐字 |
| S14 | https://zh.wikisource.org/wiki/%E5%A2%A8%E5%AD%90/%E5%B0%8F%E5%8F%96 | 辩之功能句、『以名舉實……以類予』逐字 |
| S15 | https://zh.wikisource.org/wiki/%E5%A2%A8%E5%AD%90/%E5%A4%A7%E5%8F%96 | 『夫辭以故生，以理長，以類行者也』逐字 |
| S16 | https://plato.stanford.edu/entries/stoicism/ | 逻辑节与克律西波斯年表（五式/themata、lekta、三分、宽范围句逐字） |
| S17 | https://plato.stanford.edu/entries/medieval-syllogism/ | vetus/nova 划分、阿伯拉尔前三文本、奥卡姆、布里丹诸句逐字 |
| S18 | https://plato.stanford.edu/entries/principia-mathematica/ | 1910–1913、逻辑主义定位、拉姆齐悖论分组诸句逐字 |

二轮另对 S2/S5/S6/S8/S9 的关键句以 curl 重抓逐字复核（见 evidence.json 各条 locator 的『二轮复核』注）。S4、S7、S1、S3、S10 仍以首轮 WebFetch 核读为准。

检索与试错记录（未采用 URL）：SEP /entries/nyaya、/entries/dignaga、/entries/logic-language-chinese、/entries/epistemology-indian、/entries/george-boole、/entries/syllogism-medieval（错误 slug，404；正确 slug 经 SEP contents.html 索引实查为 /entries/mohist-canons、/entries/logic-india、/entries/medieval-syllogism 等）；IEP /port-royal-logic、/history-of-logic、/george-boole、/bool、/boole、/alg-logic、/algebra-of-logic-tradition（404）；Gutenberg 无英文《前分析篇》（/ebooks/search 实查，仅德文 Organon III #78423）；MIT Classics Archive prior.1.i.html 不可得；Archive.org 布尔《思维规律的研究》1854 年版元数据核得（india.history.resource.53518 等），因包内未写布尔内容而未列入 sources。

## 六、仍缺证据与后续建议

1. **波尔-罗亚尔逻辑**：任务唯一 relatedBranch，本包未核读其相关来源，不代述；建议由《理性主义》条目自行扩写或在后续包中以 SEP『Antoine Arnauld』入场。二轮试探性核读确认该条目存在并载 La Logique ou l'Art de penser（与 Nicole 合著）及开篇立场，但全文未逐字核完，本包故仍未采用；注意该条目未给出《逻辑或思维术》初版年份（通作1662，不得凭记忆写入）。
2. **汉传因明史**（玄奘译场、《因明正理门论》）：本次来源不含；SEP logic-india 仅载论式『经佛教传播传入中国、朝鲜与日本』而无玄奘其人，包内东传节点不系年、不写玄奘。若站内补建需另核《大正藏》或学术研究。
3. **量词-变元的独立发明者**（皮尔士—米切尔路线）：S6 仅覆盖弗雷格；站内有皮尔士条目，若后续扩写该线索需另核 SEP『Peirce's Logic』。
4. **19世纪代数逻辑线**（布尔《思维规律的研究》1854、德摩根、文恩）：二轮已核得 Archive.org 布尔1854年版元数据与 SEP『Algebraic Propositional Logic』开篇（'George Boole was the first to present logic as a mathematical theory in algebraic style'），因包内现代叙事以弗雷格为起点，此线未写入；后续扩写时注意 SEP 该条目正文未给出布尔著作年份与书名。
5. **真与悖论线**（说谎者悖论、塔斯基真定义、二值原则与卢卡西维奇1920三值逻辑）：本包以 S8/S1 的真/可证与后承问题承载逻辑哲学，悖论—多值一线未展开；后续扩写可入场 SEP『Liar Paradox』『Many-Valued Logic』（二轮已确认两条目存在）。

## 七、复核方法声明

- packet.json / evidence.json 经 `python3 -m json.tool` 校验通过；evidence.json 共 72 条，覆盖 overview 关键断言、8 位人物、7 条关系、12 个时间线节点、12 条术语、9 部著述、9 个分支与 2 条引语，另有 proposal 查重与书目实查记录。
- 脚本校验：全部 sourceRefs（packet 与 evidence 两侧）可解析至 sources 清单（S1–S18）；全部 evidence fieldPath 可解析至 packet.json 对应节点；thinkers/relations/timeline/cihai/works/subSchools 逐条均有 evidence 记录（脚本实查，无缺漏）。
- 站内实查（philosophers.json 人名/纪年、books.json 书目、schools/data 查重、school_理性主义.json 分支索引）以 python 完成，evidence.json 对应条目 sourceRefs 留空并注明实查方式。
- 本包为研究员自查（两轮），非独立同行评审；所有不确定性均写入 evidenceLimits（11 条）与 evidence.json 的 uncertainty 字段。

## 八、二轮复核记录（2026-10-04）

二轮为对首轮成稿的独立复核：另一研究进程在同日重新执行任务（curl 抓取 SEP 条目与维基文库原典全文后逐字比对），随后与首轮成稿合并。结果如下。

**发现并已修正的结构问题（2处）**：

1. proposal.relatedExistingEntries 与任务清单不符：首轮误收『现象学』（任务 mentionFiles 22 项中无此条）且漏收怀疑论、唯心主义、德国古典哲学、高加索哲学、天演论、过程哲学、后现代主义、伦理学、蒙古中亚哲学共 9 项——已修正为与任务 JSON 完全一致的 22 项。
2. 书目键名 `suggestedBookIds` 与已交付样例（F06）及契约用语不一致——已改为 `relatedBookIds`。

**发现并已修正的内容问题（2处）**：

3. 卷首引语末尾带编者按语式后缀（『——这便是演绎。』），按契约『编者概括用 paraphrase』的精神删去，使引文止于定义本身。
4. artwork-brief 建议比例（3:2/16:9）与本任务规定的 4:3 横版不符——已改为以 4:3 为主稿比例。

**据二轮新核来源补入的内容（前次明确留白处）**：

- 斯多葛命题逻辑（S16）：thinkers 新增站内人物克律西波斯（第8位）、relations 新增与亚里士多德的学派对照（含《工具论》标题背后的逻辑地位之争）、timeline 新增『约前3世纪末』节点、cihai/subSchools 各新增一条。
- 拉丁中世纪逻辑（S17）：timeline 新增『6—14世纪』节点、subSchools 新增分支、works 新增《逻辑大全》（站内在库书目同步补入关联建议）。
- 《数学原理》（S18）：overview 第3段与 timeline 1879 节点补强，站内书目补入关联建议。
- 原典锚点（S11–S15）：《前分析篇》Jenkinson 译本与《墨经》四章逐字核读，补入三段论定义引语锚点与『以名舉實，以辭抒意，以說出故』『小故/大故』等原引文（首轮因 S5 抓取截断而按不引未核实文句处理，evidenceLimits 相应改写）。

**复核中验证为无误的首轮断言（抽样逐字）**：

- S5 的『87 explications / 86 theses』、『late 4th and mid 3rd century BCE』——curl 重抓逐字确认。
- S6 的1879年出版与全书德文题名、1902-06-16罗素来信——逐字确认。
- S8 的1931年1月发表——逐字确认。
- S9 的『attributed to Gautama (c. 200 C.E.)』与四量句——逐字确认。
- S2 的演绎定义英译、organon 六篇——逐字确认。
- 站内 philosophers.json 的克律西波斯（约前279-前206年）——二轮独立 grep 确认。

**仍以首轮核读为准（二轮未重抓）**：S1、S3、S4、S7、S10。其中 S10（Britannica）仅开篇可见，相关断言只用于领域起源一句。
