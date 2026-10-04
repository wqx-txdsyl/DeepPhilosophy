# P01 唯物主义（Materialism）— review.md

- 日期：2026-10-04（accessedAt / reviewedAt 同日）
- 研究员：zcode（P01 资料包）
- status：ready-for-review

## 1. 目录处置（开工前检查）

`docs/content-proposals/schools/P01/` 开工时不存在（`ls` 确认：No such file or directory），无同日旧稿，不存在"保留/重写"问题；四个文件均为本次新建。schools/ 下已有 A01、B01—B11、F01—F06、I01、I02 等其他任务目录，未触碰。

## 2. 范围与边界决定

1. **立场总览，不是学派史**：按任务 coverage=related-branches-only，本包是"唯物主义"这一哲学立场的入口条目；马克思主义谱系（辩证唯物主义阐释派、历史唯物主义深化派、实践唯物主义派、本雅明的历史唯物主义、实践唯物主义、历史唯物主义中国化等 7 个站内既有分支）全部只在 `proposal.relatedExistingEntries` 与 overview 第 3 段作辨析与互链建议，不重写其内部内容。
2. **三组"近似名称"的辨析全部落到内容里**：
   - 唯物主义 vs 物理主义：术语史分立（17 世纪末 vs 1930 年代；形而上学论题 vs 原初的语言论题）与互换条件，依据 SEP Physicalism §1.1（已实读）。
   - 唯物主义 vs 机械唯物论：霍布斯（SEP Hobbes §3 实读）单列为 17 世纪形态；18 世纪法国唯物论仅作谱系节点（单段证据，见 §5 证据限度）。
   - 唯物主义 vs 历史唯物主义：依 SEP Karl Marx（"an influential theory of history—often called historical materialism"）明确写成"关于历史与社会的特定理论 ≠ '一切皆物理'的形而上学论题"，并在 conclusion 第 3 段提醒中文语境常见混同。
3. **政治敏感内容处理**：马克思、恩格斯相关内容只写学术来源可考的学说定位（《提纲》批评要点、《德意志意识形态》"唯物主义方法"前提），不作褒贬；霍布斯宗教立场（无神论—正统基督教的归属之争）在 evidence.json 中记录为未决争议，本包不采信任一方。
4. **原子论 ≠ 唯物主义**：SEP Ancient Atomism 导言指出古典印度原子论（正理—胜论、佛教、耆那教）可能最早且未必承诺唯物主义；本包据此拒绝"西方+东方"配额式并列，印度材料只用于这一辨析，未展开具体学说（证据限度见 §5）。

## 3. 来源与查重

8 个来源，全部于 2026-10-04 用 curl 实际抓取全文并通读相关章节（WebSearch/WebReader 后端当日限流，返回的"摘要"一律未采用为依据）：

| id | 来源 | 实读范围 |
|---|---|---|
| S1 | SEP Physicalism（2026-09-16 修订版） | 导言、§1.1、§1.2、§2.1—2.2、§3.1—3.2、§4.3、§4.5、§5 目录与 5.1、参考文献（Lange/Smart 条目） |
| S2 | SEP Democritus（2023-01-07 修订版） | 导言、§1 |
| S3 | SEP Ancient Atomism（2022-10-18 修订版） | 导言、§2.5 Epicurean Atomism、章节目录 |
| S4 | SEP Karl Marx（2025-03-27 修订版） | 导言、§2.2、§2.3 |
| S5 | IEP Identity Theory | 导言、§1、§3（Putnam 1967 论证与回应策略） |
| S6 | IEP Propositional Attitudes | 导言、§4a、§4b（Churchland 1981 引文 p.67） |
| S7 | SEP Thomas Hobbes（2025-03-01 修订版） | 导言、§1、§3 Materialism、§4、§5（宗教争议部分） |
| S8 | SEP Lucretius（2023-09-22 首发） | 导言、章节目录 |

- 互相转抄检查：SEP 五个条目作者与分工不同（Stoljar / Democritus 条目 / Ancient Atomism 条目 / Marx 条目 / Hobbes 条目 / Lucretius 条目），IEP 两篇亦独立成文；S1 与 S3 同时覆盖伽桑狄但角度不同（复兴史 vs 创世化改造），无转抄关系。
- 门槛核对：≥3 来源（8）；≥1 支撑学说范围与人物归属（S1 §1.2、S2、S3、S7）；≥1 支撑原典/具体论证（S3 论《论自然》与书信、S4 论《提纲》《德意志意识形态》、S1 论知识论证与亨佩尔困境、S5 论 Putnam 1967）。
- Britannica materialism 条目：Cloudflare 验证页拦截，未能读到正文 → 不列入 sources（URL 未引用）；IEP 的 physicalism / eliminative materialism / materialism / marx 等直接 slug 均 404（经 WordPress REST API 核实站点确无这些独立条目），故消除主义改由 IEP Propositional Attitudes 支撑。

## 4. 复核结果（自检）

- 站内人名核对（grep philosophers.json，737 人）：德谟克利特、伊壁鸠鲁、托马斯·霍布斯、卡尔·马克思、弗里德里希·恩格斯、卢克莱修、希拉里·普特南 均为站内精确姓名；**斯马特（J.J.C. Smart）、保罗·丘奇兰德（Paul Churchland）站内无条目**，thinkers 中已注明"站内暂无此人条目"；拉美特利、霍尔巴赫、狄德罗、留基伯站内亦无，未收入 thinkers。
- 藏书核对（books.json，409 本）：proposal.suggestedSiteBooks 的 7 个 ID 均实际核对存在（利维坦 65dbe55d66df、论自然 02b0e5227f7b、自然与快乐 221f09d04944、准则学 123abf075694、德意志意识形态节选本 ae97dec227b6、MEGA 费尔巴哈篇 1085686cbd33、恩格斯《费尔巴哈论》3a23c3ec0466）。站内无《物性论》中译本，works[0] 未造 ID。
- 引语：三条直接引语（朗格、丘奇兰德、马克思）全部为"经 SEP/IEP 转引核对"并在 kind 字段声明，中译注明为本包译文；"万物皆原子与虚空"按来源的 'said or allegedly said' 标注降级为 paraphrase-attributed。无伪造页码——仅使用来源自身给出的定位（1925, 3；MECW 3:303；p.67）。
- 数量：术语 10、时间线 10、著述 8、人物 7，均在契约区间内。
- JSON 校验：packet.json 与 evidence.json 均通过 `python3 -m json.tool`（见交付检查）。

## 5. 仍缺证据 / 证据限度（与 packet.evidenceLimits 一致，择要）

- 留基伯无独立年代记载；德谟克利特卒年未定位；《大/小世界体系》与格言集归属存疑（已如实降级表述）。
- 伊壁鸠鲁"偏斜"系后世来源所记，学术解释多解，本包未采信任一解释。
- 拉美特利、霍尔巴赫仅单段证据：《人是机器》书名与 1747 年份未核实，故不写入 works/timeline（时间线节点只用"18世纪"范围）。
- 斯马特、普特南、丘奇兰德生卒年未在核读来源中定位，era 用"20世纪"。
- "辩证唯物主义"术语归属：SEP Physicalism §1.2 行文把它系于马克思名下，与常见术语史（与恩格斯/普列汉诺夫关联更紧）不一致；未另行核实，本包对马克思只用"历史唯物主义"（依 SEP Karl Marx），分歧记录于此。
- 马克思博士论文：两来源均未给出题名与年份，只写内容描述。
- 亨佩尔困境、泛心论问题、"消极进路"等依 S1 §4 转述，未逐条读其所引原始论文（超出本包需要）。

## 6. 实际核读 URL 清单

1. https://plato.stanford.edu/entries/physicalism/ （S1）
2. https://plato.stanford.edu/entries/democritus/ （S2）
3. https://plato.stanford.edu/entries/atomism-ancient/ （S3）
4. https://plato.stanford.edu/entries/marx/ （S4）
5. https://iep.utm.edu/identity/ （S5）
6. https://iep.utm.edu/prop-ati/ （S6）
7. https://plato.stanford.edu/entries/hobbes/ （S7）
8. https://plato.stanford.edu/entries/lucretius/ （S8）

尝试但未采用（404/拦截，不得引用）：https://plato.stanford.edu/entries/eliminative-materialism/ （404）、https://plato.stanford.edu/entries/atomism/ （404）、https://www.britannica.com/topic/materialism-philosophy （Cloudflare 拦截页）、https://iep.utm.edu/materialism/ physicalism/ elim-mat/ marx/ 等（404）。

## 7. 给审读者的两个提示

1. relations[1]（德谟克利特→霍布斯）与 relations[3]（霍布斯→马克思）是"传统形态"级别的谱系/批评关系，type 字段已按契约标注为编辑比较/批评，不是师承或阅读关系，请勿在编辑时改成"影响"。
2. works[1]《论自然》的"站内同名辑本"提示只写在 desc 与 proposal，未在 works 内造站内 ID；上库时若链接藏书请使用 proposal 里核对过的 ID。
