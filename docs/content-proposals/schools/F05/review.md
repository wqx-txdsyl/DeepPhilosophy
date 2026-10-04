# F05 语言哲学 —— 资料包复核记录

- taskId: F05（field，基础研究领域总览，coverage: related-branches-only）
- status: ready-for-review
- reviewedAt: 2026-10-04
- 复核方式：研究员自检（非独立同行评审）。全部来源经 WebFetch 实际打开并读取相关段落；引语逐字核对维基文库原文；站内姓名与书目 ID 逐一实查。

## 一、边界决定（与既有条目的关系）

1. **与「分析哲学」条目**：其子项（逻辑分析与逻辑原子主义 / 逻辑经验主义 / 日常语言哲学 / 自然主义与整体论 / 模态、指称与形而上学 / 伦理、政治与应用研究，实查 `app/public/schools/data/school_分析哲学.json`）从历史—学派维度收录本包同一批人物。F05 是问题域总览（意义/指称/语用/言语行为），正文不重复学派史；proposal 建议两处互链。
2. **与「北欧哲学」条目**：其子项「语言哲学与日常语言分析」（维特根斯坦后期思想与冯·赖特，实查 `school_北欧哲学.json` 第 3 子项）是语言哲学在北欧语境的接受史。F05 不收北欧人物，边界互补。
3. **与「名家」条目**：先秦名辩的历史脉络（惠施历物十事、离坚白、辩者、形名、悖论诸派，实查 `school_名家.json`）属名家。F05 只引《白马论》《正名》两处文本作问题对照；惠施、墨辩刻意不入，避免重复建设。
4. **语言哲学 vs 语言学**：以 S8 的直接对比为界——语言学的哲学是科学哲学应用于经验语言学；语言哲学传统关注意义与指称。边界话题（言语行为、隐含义、语言相对论）的归类取决于答案类型而非话题本身（S8 原文要点）。
5. **跨传统纪律**：公孙龙—弗雷格、荀子—蒯因一律标「编辑比较（跨传统，非历史影响）」；荀子对公孙龙是同一传统内的「批评」（《正名》斥白马非马为无用之辩，S10）。全包无任何跨传统师承/影响断言，也未凑「一西一东」配额——名辩对照只占五分之一篇幅。
6. **thinkers 取 8 人上限的取舍**：塞尔未入 thinkers（让位给荀子以覆盖任务要求的名实之辨维度）。塞尔的发展（成功条件、施事分类、构成性规则）在 overview/conclusion 与 S4 证据中呈现；因 relations 的 from/to 限本包 thinkers，未单列奥斯汀—塞尔关系条目，此为已知取舍。
7. **领域主线取 1879—1980**：以代表性争论与文献节点组织（研究纪律第 5 条），1980 之后的形式语义学、真值条件路线（戴维森—塔斯基）、实验语用学等留待补包，已在 evidenceLimits 声明。

## 二、分歧与争论（如实呈现，不作裁决）

- 描述论 vs 新指称论：克里普克模态/认知论证 vs 簇理论；空名问题与元语言理论复兴使争论开放，SEP《名称》条目把认知显著性归为「僵局」（S3）。
- 罗素—斯特劳森之争（1905/1950/1957）未裁决；后续研究表明真值判断对细微语境变化敏感（S2 引 Neale 1990、Lasersohn 等）。
- 维特根斯坦前后期：正统「断裂」解读 vs 「坚决解读」（resolute reading），S5 并陈。
- 蒯因翻译不确定性：晚年自称为「猜想」，无严格证明；与卡尔纳普的深层分歧在宽容原则（S6）。

## 三、查重

- 未复制任何站内既有正文；仅引用既有条目的**范围与子项清单**用于 proposal 关系建议（school_北欧哲学.json、school_分析哲学.json、school_名家.json，均只取名称与一句话描述）。
- 站内姓名逐一核对 `app/public/philosophers.json` 键名：戈特洛布·弗雷格 / 伯特兰·罗素 / 路德维希·维特根斯坦 / 威拉德·范·奥曼·蒯因 / J.L. 奥斯汀 / 索尔·克里普克 / 公孙龙 / 荀子，thinkers 全部采用站内精确姓名。
- 书目建议 7 条全部为 `app/public/books.json` 实查存在的 ID（5d906139d1b2 逻辑哲学论、08e055841182 哲学研究、6b68595de71f 命名与必然性、9efee732eaff 语词和对象、920596aed622 如何以言行事、795658cafeab 荀子、c0fc56d645dc 算术基础）；未造任何 ID。
- 旧正文未作继承来源；《公孙龙子》「白马者马与白也」一段存在文本异文，本包引文一律以维基文库正文页为准。

## 四、复核结果（自检）

- 引语 3 处（白马论命形命色段、求马求白马段、荀子约定俗成段）逐字核对维基文库繁体原文，packet 内转写简体、逐字对应；closingQuote 为 paraphrase 并已标注。
- 年代纪律：只写来源支持的年份；克里普克讲座/文集年份、奥斯汀讲座年份未核实，一律不写（见 evidenceLimits）。
- 计数：术语 10、时间线 10、著述 8、人物 8、关系 10、子派 6、引语 2——符合质量标准（术语 6—10、时间线 6—10、著述 4—8、人物 4—8）。
- evidence.json 共 67 条，覆盖全部 timeline 节点、cihai 词条、works、thinkers、relations、quotes 与关键 overview/conclusion 断言，fieldPath 均指向 packet.json 内部位置（overview/conclusion 各段一证，故同一路径多条）。
- 两个 JSON 已用 `python3 -m json.tool` 校验通过。

## 五、仍缺证据 / 证据限度（详见 packet.evidenceLimits）

1. SEP 无「语言哲学」单一总览条目（/entries/philosophy-language/ 404），IEP 对应地址 404，Britannica 403；领域范围界定以 S8 的直接对比与九个专条拼合。
2. 克里普克《命名与必然性》1970 讲座、1972 文集版年份未核实，仅 1980 成书可据（S3）。
3. 奥斯汀（1911—1960）、克里普克（1940—2022）、罗素（1872—1970）生卒年为通行参考值，未在本包来源片段中直接核对；蒯因、弗雷格、格赖斯、荀子的年代有 S6/S1/S7/S10 直接支持。
4. 今本《公孙龙子》文本史有学术讨论，作者归属只写「传公孙龙」；《荀子》编排非本人审定（S10）。
5. 奥斯汀与后期维特根斯坦的影响关系证据不足，只作编辑比较。
6. 卡尔纳普—蒯因之争、格赖斯对奥斯汀的批评、戴维森—塔斯基真值条件路线未展开。

## 六、实际核读 URL 清单

已读（2026-10-04）：

1. https://plato.stanford.edu/entries/frege/
2. https://plato.stanford.edu/entries/descriptions/
3. https://plato.stanford.edu/entries/names/
4. https://plato.stanford.edu/entries/speech-acts/
5. https://plato.stanford.edu/entries/wittgenstein/
6. https://plato.stanford.edu/entries/quine/
7. https://plato.stanford.edu/entries/grice/
8. https://plato.stanford.edu/entries/linguistics/
9. https://plato.stanford.edu/entries/xunzi/
10. https://zh.wikisource.org/wiki/公孫龍子 （篇目页）
11. https://zh.wikisource.org/wiki/公孫龍子/2 （白马论正文，引文出处）
12. https://zh.wikisource.org/wiki/荀子/正名篇 （正名原文，引文出处）

不可达 / 放弃（未写入 sources）：

- https://plato.stanford.edu/entries/philosophy-language/ （404，SEP 无该单一总览条目）
- https://iep.utm.edu/phil-lang/ （404）
- https://www.britannica.com/topic/philosophy-of-language （403）
- https://ctext.org/gongsun-longzi/bai-ma-lun/zhs （反爬提示页，未获正文，改用维基文库）
