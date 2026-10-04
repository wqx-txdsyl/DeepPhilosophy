# B08 宁玛派思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B08`（proposedKind=school，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查/主会话直研——初版研究代理因内容过滤（错误1301）中断，无产出，本包由主会话以 curl 直研完成；非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **传承叙事与批判史学分层**：莲花生"创立"、极喜金刚"约665"——来源原文自带 founded by / purportedly / traditionally held 限定，本包照录并在 thinkers/timeline 标注"叙事层"；朗达玛灭佛与后弘期起点未获来源，不写。
2. **宗教宣称与文献学处理分开**：伏藏的埋藏-掘出叙事按 S4 原文照录（quotes/1），不对其真伪作断言；正文的文本结构分析（Kama/Terma 双线、8—11世纪 Kama 主流期）与之明确区分。
3. **不按五派配额造分支**（scopeAndCautions 原文）：subSchools 仅 3 项——口传线、伏藏线、大圆满三系列（节标级），全部有直接来源定位。
4. **他空论辩不作宁玛立场断言**：S5（SEP Tsongkhapa）只提供 gzhan stong 定义作背景；该条目内 Nyingma/Dzogchen 均 0 命中（实测），宁玛侧立场无来源、不写。
5. **与姊妹包分工**：T01 藏传节点仅四派年代（参考级），本包承担宁玛深度；与 B09（萨迦）、B04（格鲁-宗喀巴）互为三极。

## 二、分歧与证据限度（本批来源等级最弱者，显式声明）

- **来源等级**：SEP 无 dzogchen/nyingma 专条（404 实测）；学术级来源仅 S5 的背景句；实质来源全部为维基 reference 级。断言密度已压至来源可承受范围：核心术语"本净（ka dag）/任运（lhun grub）"、大圆满"三系列"内容、Nyingma Gyubum 编成史均未获定位，不写。
- **人物收录从紧**：站内实查有 4 位宁玛人物（莲花生大士/龙钦巴/麦彭仁波切/顶果钦哲仁波切），但麦彭仅见于 S1 节标语境、顶果未见于核读来源——只收前 2 位（有直接来源），另收站外极喜金刚、益西措嘉。
- **待补强**：以 Germano、Dorje 等学术专研究升级来源等级——这是本包为后续工作划出的任务。

## 三、复核方法与结果

1. 主会话直研：维基四页 + SEP Tsongkhapa 以 curl 全文抓取+grep 定位；SEP dzogchen 404 实测。
2. evidence.json 40 条：thinkers 4、relations 3、timeline 6、cihai 10、works 4、subSchools 3、引语 4、coverage/books 2，locator 均含 verbatim 短引文。
3. 人物：站内 python 子串实查（莲花生大士/龙钦巴用站内姓名纪年）；books.json 无相关藏书，建议为空。
4. 两个 JSON 经 `python3 -m json.tool` 校验；closingQuote 初稿占位残句已修正为 S1 原句。

## 四、仍缺证据（与 packet.evidenceLimits 对应）

- 本净/任运、三系列内容、Nyingma Gyubum 编成史、朗达玛灭佛与后弘期、宁玛与他空论辩的立场史、麦彭/顶果的学理贡献——均未获可引定位，不写。

## 五、实际核读 URL 清单（2026-10-04）

1. https://en.wikipedia.org/wiki/Nyingma （curl 全文+定位）
2. https://en.wikipedia.org/wiki/Dzogchen （同上）
3. https://en.wikipedia.org/wiki/Longchenpa （同上）
4. https://en.wikipedia.org/wiki/Terma_(religion) （同上）
5. https://plato.stanford.edu/entries/tsongkhapa/ （curl 全文，仅 gzhan stong 语境句）
- 探测后放弃：SEP /entries/dzogchen/ → 404。
- 初版代理因错误 1301（内容过滤）中断（142秒，无产出）——藏传政治史相关词汇疑似触发，本包改道主会话直研完成。
