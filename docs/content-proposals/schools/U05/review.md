# U05 日常语言哲学 · 资料包复核记录

- 任务：`school-content-gap-tasks-2026-10-04.json` id=U05（group「已有分支扩展」，proposedKind=school）
- 交付目录：`docs/content-proposals/schools/U05/`（本目录为 2026-10-04 新建）
- 复核日期：2026-10-04（reviewedAt 与全部 accessedAt 一致，均为真实查阅日期）

## 0. 开工前检查与旧稿处置

- 开工前 `ls docs/content-proposals/schools/`：全部 51 个任务目录中 **无 U05**（同日草稿不存在），无需处置旧稿；目录由本包新建。
- 同日交付的 `F05/`（语言哲学领域总览包，11:31 定稿）已通读：其 proposal `relatedExistingEntries`/`relationSuggestions` 确认建议互链；本包按分工写「学派的方法与人物谱系」，不复述 F05 的问题地图。F05 的 subSchools「日常语言哲学与言语行为理论」只作领域内学说定位，正文展开留给本包，两包无正文重复。

## 1. 边界决定

1. **学派深化包，不是领域总览**（任务 scope 原文边界）：范围 = 后期维特根斯坦（语言游戏/家族相似/遵守规则/私人语言）→ 牛津学派（赖尔、奥斯汀、斯特劳森）→ 塞尔系统化 + 格赖斯会话含义；经线 = 治疗性进路 vs 系统化进路。理想语言方案、蒯因/戴维森后续、北欧接受史均不入包（F05、站内「北欧哲学」已涉）。
2. **与站内「分析哲学」条目的关系**：实查 `app/public/schools/data/school_分析哲学.json`，其 `subSchools[2]`「日常语言哲学」仅一句概述，本包即该子项的深化；thinkers 维特根斯坦/赖尔/奥斯汀在该条目已收录（姓名核对来源：`app/public/philosophers.json` 精确名为「路德维希·维特根斯坦」「吉尔伯特·赖尔」「J.L. 奥斯汀」「约翰·塞尔」；「经验主义」条目正文提及「日常语言哲学」属 mentionFile 级交叉，只建议 see-also 互链）。
3. **站内无哲学家条目的人物**：斯特劳森（P.F. Strawson）、格赖斯（H.P. Grice）grep `philosophers.json`（737 人）无独立条目，两人作为学派结构必需人物保留在包内并在 thinker.sub 注明站内暂无条目，供派页建人物卡时参考。
4. **师承与影响纪律**：「赖尔教过奥斯汀」「奥斯汀指导塞尔博士论文」均为通行说法但本次核读来源未确认，一律不写；赖尔—维特根斯坦定为编辑比较（SEP 原文「平行道路」）；赖尔—斯特劳森定为「历史接触（讲席继任）」。无跨传统内容，不设东西配额。

## 2. 来源与实际核读清单（全部 WebFetch 实际打开并读到相关段落）

| id | URL | 类型 | 核读要点 |
|---|---|---|---|
| S1 | https://plato.stanford.edu/entries/wittgenstein/ | SEP 条目 | 1929 重返剑桥、蓝皮书 1933、蓝棕皮书 1933—35/1958 出版、PI 693 段/1946 撤回/1953 安斯康姆与里斯编辑出版/2009 PPF、§2/23/65/66/185—243/201/243/261/133/309/109、克里普克 1982 与巴克—哈克等 |
| S2 | https://plato.stanford.edu/entries/ryle/ | SEP 条目 | 范畴错误类型错误定义、《心的概念》1949「最后一颗钉子」、「逻辑地理」、「形式主义者的梦」、1945 韦恩弗利特讲席、1947—71 主编 Mind、《系统性误导的表达》被乌姆森（1967）称为最早与维特根斯坦当时独立发展出的哲学紧密相近的版本（原句照录） |
| S3 | https://plato.stanford.edu/entries/austin-jl/ | SEP 条目 | 1911—1960、1952 怀特讲席、1955 詹姆斯讲座、1962 出版 HTDTWW、施为/记述之分及其瓦解、三分「近乎经典」、例句 1962: 5、《感觉与可感物》1962a |
| S4 | https://iep.utm.edu/ord-lang/ | IEP 条目 | 方法论定义、剑桥约1929—1945/牛津约1945—1970、追随者名单、内部多样性、退潮原因（格赖斯意向论、形式语义学、自然主义）、蒯因批评与斯/格辩护、批评者名单 |
| S5 | https://plato.stanford.edu/entries/strawson/ | SEP 条目 | 《论指称》1950 Mind 59: 320—344、真值间隙与预设、《个体》1959 描述形而上学、「没有历史的巨大核心」、1948 研究员、1968 继任、《感觉的界限》1966 |
| S6 | https://plato.stanford.edu/entries/speech-acts/ | SEP 条目 | 奥斯汀五分类、塞尔批评「过于词汇学」、1969 构成性规则引文与选票之喻、弱约定论（狗例）、1975 新分类原则、塞尔—范德维肯 1985 七分量 |
| S7 | https://plato.stanford.edu/entries/chinese-room/ | SEP 条目 | 塞尔 1932—2025、伯克利、1980「Minds, Brains and Programs」刊 BBS、中文屋设定、图灵测试不充分 |
| S8 | https://plato.stanford.edu/entries/implicature/ | SEP 条目 | 格赖斯 1913—1988、1957「Meaning」、1975「Logic and Conversation」、合作原则与四准则、可取消性、格赖斯剃刀 |

**实测打不开、不列入 sources 的候选 URL**（WebSearch 片段不作为核实依据）：
- `iep.utm.edu/ordinary-language-philosophy/` → 404（改址后经检索定位到 `/ord-lang/` 成功打开）
- `iep.utm.edu/searle/`、`iep.utm.edu/john-searle/` → 404（IEP 塞尔专条未能核得，塞尔主张改由 SEP Speech Acts 与 Chinese Room 两专条支持）
- `britannica.com/topic/analytic-philosophy` → 403（WebFetch 被拒；Britannica 全部放弃，未引）

## 3. 分歧与写作处理

- **遵守规则的解释分裂**（克里普克怀疑论解读 vs 巴克—哈克/麦金等）：S1 两侧均有载，conclusion 只陈述分裂存在，正文仅引 §201 悖论表述，不代维特根斯坦站队。
- **治疗 vs 系统化的内部差异**：以 S4（维特根斯坦否认哲学产新知识 vs 斯特劳森描述形而上学产真正新知识）+ S5/S6/S8（系统化三支）组织，这是本包的核心经线；F05 只作问题定位，本包展开为人物关系与 subSchools。
- **引语纪律**：全部引语为「核读英译的转译」（quoteKind/closingQuoteKind=paraphrase），exp 内附核对依据；PI §109「bewitchment」名句因核读页面未逐字出现而未用；一条候选的维特根斯坦「命名论」引语因命题编号定位不稳在复核中撤下（见 packet.evidenceLimits 第 11 条），未写入 quotes。

## 4. 仍缺证据（详见 packet.evidenceLimits，12 条）

要点：赖尔「参观大学」例子与《心的概念》章节定位未核得（正文不写、cihai 只到书级）；奥斯汀→塞尔师承不写；HTDTWW 编者不写；塞尔 1975 五类名称不列（只写分类原则）；蒯因条目只写退潮叙述（IEP 载斯/格辩护系年 1956，蒯因原文年份未核读）；斯特劳森生卒年与格赖斯著作版本细节以「通行系年」标注。

## 4.5 独立审计修正记录（2026-10-04）

独立审计发现三处问题，本次全部修复并四处同步（packet/evidence/review 同步）：

1. **乌姆森评语误译（实质性）**：原把 SEP Ryle 条目中乌姆森评语转述为「closely anticipating later Wittgenstein／密切预见」，原句实为 'the first…version of philosophy closely akin to that which Wittgenstein was then beginning to work out independently'——评语指向**独立平行发展**，非「预见」。已照录原句改写 packet（S2 coverage、thinkers[1].key、relations[0].detail）与 evidence（/school/thinkers/1/works/1、/school/relations/0）五处。
2. **译名相撞**：塞尔 1975 分类的第三判据 sincerity conditions 由「适切条件」改为「真诚条件」，避免与奥斯汀 felicity conditions（适切条件）撞名（packet：thinkers[4].key、relations[2].detail、timeline/8、S6 coverage、evidenceLimits；evidence：/school/thinkers/4、/school/timeline/8）。另 evidence 中引 SEP 页文 'overly lexicographic' 照录修正为 'unduly lexicographic'（中文「过于词汇学」不变）。
3. **S4 coverage 与 IEP 年份**：批评者名单删去「梅茨」（IEP 页无此人，页有 Cavell/Chisholm/Quine/Williamson 等）；「IEP 未给辩护年份」更正为 IEP 实载斯特劳森与格赖斯 1956 年为分析—综合区分辩护（packet S4 coverage、evidenceLimits；evidence /school/timeline/9）。

## 5. 自检结论

- 结构：schemaVersion=1，无顶层 `sub_schools` 键；术语 10、时间线 10、著述 8、人物 6、关系 6、子项 4、引语 3（均不设凑数条目，引语全部有核读定位）。
- 校验：`python3 -m json.tool` 通过 packet.json 与 evidence.json（见收尾记录）；evidence.json 共 47 条，fieldPath 均为 JSON Pointer 且脚本实测全部可解析到 packet.json 对应位置，sourceRefs 全部命中 sources.id；关键时间线节点、术语、书目、人物归属、关系均有 ≥1 条覆盖；书目建议逐条核对 books.json 真实 ID（不造 ID）。
- 本包为研究员自检（WebFetch 逐源核读 + 本地文件核对），不构成独立同行评审。
