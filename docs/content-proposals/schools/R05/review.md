# R05 行动哲学 — review.md（审读记录）

日期：2026-10-04 ｜ 复核人：包研究员（自查，非独立同行评审）

## 1. 查重结论

- **站内覆盖**：R05 为 mentions-only——任务 JSON evidence 三类精确匹配全空，mentionFiles 4 处。备忘录当日（2026-10-04）grep/python 全量检索 111 个条目文件确认：北欧哲学包冯·赖特条（sub=分析哲学/行动哲学，works 含《规范与行动》《解释与理解》）为唯一实质承载；道家包 quotes[3].exp、旧民主主义包 cihai[27]、后殖民哲学包 cihai[26] 为『行动哲学』的修辞借用（无为/知行观/解放教育学）；无『行动哲学』条目、无『心灵哲学』条目；『戴维森』仅见北美哲学包。本包撰写时以脚本复核：相关 school_*.json 文件均在（伦理学/北欧哲学/社会学/道家/旧民主主义/后殖民/北美哲学）；philosophers.json（737 键）核对——冯·赖特、路德维希·维特根斯坦、亚里士多德为站内名（packet 沿用），安斯康姆/戴维森/齐硕姆/丹托/梅尔登无站内键（用通行译名）。未重做全量逐字检索（已记 evidenceLimits）。
- **立项判断**：field 类**新建**（继承备忘录结论）。『行动哲学』作为标准哲学分支站内零覆盖，唯一实质内容（冯·赖特）是流派包内人物条目，无法替代领域总览；三处修辞借用恰需领域条目正名；站内已有伦理学等 field 型条目同型，无结构障碍。
- **与《伦理学》**（school_伦理学.json，field 型）：理论—规范分工。本包写行动的结构与解释；伦理学条目以行动为评价对象。安斯康姆两包各写各面（本包行动理论/彼包德性论），建议互链。与次轮元伦理学类候选（R07 等）在『道德理由是否也是行动理由』处相邻，交叉链接即可。
- **与北欧哲学冯·赖特子项**：分工与互链。站内称《规范与行动》（1963）为『行动哲学与规范逻辑领域的代表作』——本包经 SEP《Deontic Logic》书目独立核实该书题名/副题/出版社/年份，**但冯·赖特行动理论立场的具体内容站内外均未核实**，两包在此均不作立场断言（本包 evidenceLimits 第 1 条为备忘录『先核实』项的处理结果记录）。
- **与《社会学》**：韦伯『社会行动』归社会学条目，本包仅作概念区分提示，不写影响或师承。
- **与道家/旧民主主义/后殖民三处宽泛用法**：本包承担正名功能，站内原文不回改（各包语境自足），可在页内提示学科义区别。
- **与未来心灵哲学条目**：站内现无心灵哲学条目（grep 确认）；意图的本体论、心灵因果与异常一元论为其预留接口，本包 scope 已留白。

## 2. 学术分歧与处理

- **『反因果传统』与冯·赖特**：通行叙述常把冯·赖特与安斯康姆、梅尔登并列为反因果传统，但本轮全部可达来源（SEP Action/practical-reason/history/intention/hempel/scientific-explanation、IEP、SEP Deontic Logic）均未讨论其行动理论立场，Britannica 专页被反爬拦截。处理：packet 对冯·赖特只写国籍生卒、道义逻辑奠基地位与两书书目定位，不写反因果论证；relations 中与戴维森的关系标注『立场对照未核』。
- **安斯康姆与因果论的关系**：SEP 把她的构成性说明立为『标准图景』的主要对手传统，但 IEP《Anscombe》第 4 节的立场是『意图不是先在致动事件』而非『行动无原因』（她 1971 年《因果性与决定论》恰论因果）。处理：subSchools『非因果论』条注明她『常被归入广义反因果阵营』并声明按 S1/S3 口径以两传统并立呈现，不写强断言。
- **IEP《Davidson》与 SEP《Action》的文献纪年口径**：S2 不给 ARC 原刊年份与期刊（只记收入 1980 文集），S1 记 Davidson 1963 但不给刊名——两处口径一致地不支持『1963 年刊于某刊』的完整表述，works 条目只写 1963 并注『原刊期刊未核』。
- **戴维森对《意向》的评价**：出处是 IEP 的转述句（'has called it...'），非戴维森文本直引——quotes[2] 标 kind=paraphrase。
- **『实践三段论』史述**：安斯康姆—冯·赖特一系对亚里士多德实践三段论的重构是通行史述，但已核来源无逐字支持，cihai『实践推理』条未用『结论是行动而非命题』一语，只写有据部分。
- **亚里士多德的地位**：NE 引注（3.1/6.2/6.4/6.5）来自 S1 的引用清单，原典未直读；『古代源头』的定位由戴维森评价（S3）与 SEP 引注结构共同支撑，thinker 条不写未经来源的具体学说阐释细节。

## 3. 复核方法与结果

两轮（同日 2026-10-04）：

1. **第一轮（复用+复核备忘录 4 来源）**：WebFetch 重读 SEP《Action》（关键引语逐字再核：中心问题、§621 英译、rational capacities、standard story/Velleman 1992、Davidson 两论题与 1971, 23 引文、Anscombe §48/§8、Feinberg 1965、Melden/晒伤、Chisholm 1964、Danto 1979 三种基本性、Thompson 2008/Lavin 2013、NE 引注清单）；WebFetch 重读 IEP《Davidson》（ARC/1980 文集/合理化/反例论证/事件同一性/异常一元论/生年 1917）；IEP《Anscombe》WebFetch 超时后改 **curl 抓全文（73KB）逐节 grep 核读**（生卒、师承、遗产执行人、1953 英译、1956 杜鲁门事件与次年成书、1971 就职讲座、登山者三例、无需观察引文、戴维森评价）；Britannica 冯·赖特页 WebFetch 与 curl 双双被反爬拦截（403/挑战页），沿用备忘录当日核读记录（芬兰哲学家、道义逻辑奠基 1951）。
2. **第二轮（新增来源实读）**：curl 抓 SEP《Deontic Logic》全文（183KB），逐字核录冯·赖特书目三行（1951a Mind 60(237): 1–15；1963 Norm and Action: A Logical Enquiry, Humanities Press；1968 An Essay in Deontic Logic and the General Theory of Action, Acta Philosophica Fennica 21）与 'central early figure' 表述；为核冯·赖特立场另探测 SEP 五条目（practical-reason/history/scientific-explanation/intention/hempel，curl，von Wright 命中均为 0）与 IEP 三个 slug（404）；Wikipedia REST API 核戴维森（philosopher 页 description: 1917–2003）与冯·赖特（description: Finnish philosopher (1916–2003)，仅用于 era 字段）。
3. **结构核对**：packet.json / evidence.json 经 python3 -m json.tool 校验；站内人名与条目文件以脚本核对；R04（数学哲学）packet 格式对齐（字段结构、quote 标注、evidenceLimits 体例）。

## 4. 仍缺证据（已写入 evidenceLimits，正文未使用相关内容）

1. **冯·赖特行动理论的具体立场**（反因果/逻辑关联论证）：全部可达来源未命中，本包不展开——这是备忘录『先核实』项的结论：未核原书即不展开。若未来补读《规范与行动》原书或专门研究文献，可扩写 thinkers/relations 并在时间线加节点。
2. 安斯康姆《意向》原典未直读：§8/§48 引文与页码（Anscombe 2000, p. 14）均为转引；《意向》出版社/版本信息不注。
3. 戴维森 ARC（1963）原刊期刊、1971 年文题名、《行动语句的逻辑形式》发表年份未核；戴维森卒年仅 reference 级（S6）。
4. Velleman 1992『standard story』原文、梅尔登/齐硕姆/丹托/费恩伯格/汤普森/拉文/舒勒/塞昂等原始文献均未直读（经 S1 转述），著作仅注来源明示年份。
5. 《尼各马可伦理学》成书年代未专门核证（从通说公元前 4 世纪）；Bekker 引注为转引。
6. SEP《Action》条目作者名（Author and Citation 单独页）未读取，全包不写作者名。
7. Britannica『philosophy of action』专条是否存在仍不明（备忘录两次拦截，本轮未重试）。

## 5. 实际核读 URL 清单（全部 2026-10-04）

| # | URL | 方式 |
|---|-----|------|
| S1 | https://plato.stanford.edu/entries/action/ | WebFetch 全文两轮（备忘录一轮+本包一轮），关键引语逐字比对 |
| S2 | https://iep.utm.edu/davidson/ | WebFetch 全文（备忘录+本包）+ curl 全文 grep（/tmp/dav.txt） |
| S3 | https://iep.utm.edu/anscombe/ | 本轮 WebFetch 超时 → curl 全文（73KB）逐节核读；备忘录当日 curl 全文核读 |
| S4 | https://plato.stanford.edu/entries/logic-deontic/ | curl 全文（183KB），书目三行与正文表述逐字核录 |
| S5 | https://www.britannica.com/biography/G-H-von-Wright | 备忘录当日 WebFetch 成功核读；本包 WebFetch/curl 复抓均被拦截（403/挑战页），沿用记录 |
| S6 | https://en.wikipedia.org/api/rest_v1/page/summary/Donald_Davidson_(philosopher) | curl REST API（仅生卒，era 字段） |
| S7 | https://en.wikipedia.org/api/rest_v1/page/summary/Georg_Henrik_von_Wright | curl REST API（仅生卒与国籍佐证） |

探测未命中记录（冯·赖特立场核实尝试，2026-10-04）：https://plato.stanford.edu/entries/practical-reason/ 、/entries/history/ 、/entries/scientific-explanation/ 、/entries/intention/ 、/entries/hempel/（均 200 但 von Wright 命中 0）；https://iep.utm.edu/von-wright/ 、/vonwright/ 、/georg-henrik-von-wright/（均 404）。
访问失败记录：https://www.britannica.com/biography/G-H-von-Wright（本包轮次 403，沿用备忘录记录）；IEP《Anscombe》WebFetch 首次超时（改 curl 成功）。
