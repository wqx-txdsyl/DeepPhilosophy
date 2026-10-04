# T02 道教哲学 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `T02`（proposedKind=tradition-overview，P1-content-packet，coverage=related-branches-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定（本包最重的决定：与站内《道家》条目的分工）

1. **道家 vs 道教：分工而非合并或割裂**。站内《道家》条目承载老庄哲学学派（老庄学派/黄老学派/魏晋玄学/道教重玄学/河上公注派五个子项），本包承载道教传统（daojiao）的哲学总览。分工的学术依据：IEP 开篇即以 daojia（汉初目录学范畴，'哲学'文本）对 daojiao（东汉末起自称 daojiao 的宗教运动）立论，并强调这一二分更多反映西方参照系（S2）；SEP 现行条目（2025-04-19 版，访问所见）则整体只写哲学面、通篇无教团内容（S1，grep 实测 Celestial Masters/Shangqing/Lingbao/alchemy 均 0 命中）。两部权威百科对同一"Daoism"划界不同——这一事实本身写进了 packet 的 overview 与 conclusion，作为本条目方法论自觉的一部分。
2. **关系按来源呈现，不混同也不完全割裂**：两者共享《老子》《庄子》文本与注解链（王弼注→成玄英疏，S19/S6），relations 以"文本接受/宗教化""文本接受/发展"呈现这条连续性；同时《想尔注》"一散形為氣，聚形為太上老君"（S15）的神格化改写与英文维基"immortality is not a significant topic in the Daodejing itself"（S4）一起，标出两传统的真实分岔点。
3. **站内既有"道教重玄学"分支（道家 subSchools[3]，任务条目指认的唯一 related branch）**：本包 subSchools 以重玄学深化之（补充成玄英生平、佛道论辩、647 梵译、受中观影响的来源），**不代改站内数据**；深化还是迁移由 Codex 决定（proposal.relationSuggestions 已写明）。
4. **《韩国哲学》"东学（天道教思想）"**：任务条目认定的语词相近排除项，本包零关联，仅在 proposal.relatedExisting 存档说明。
5. **跨传统对照只有一处且全部有来源**：佛教→道教的互动（灵宝借佛、重玄受中观、成玄英—玄奘 647 梵译合作），全部标 type/出处原句；"重玄受中观影响"只写到"influenced by Buddhist Madhyamaka thought"的粒度，不写"双遣有无"等更细义理对应（无逐字来源）。SEP Zhuangzi 记老庄自然主义塑造禅宗（S3）——佛教端点不在本包，未设 relation，只在 proposal.relationSuggestions 存档。

## 二、分歧与争议的处理

- **张道陵 142 年立教**：传统系年，IEP 明言太上老君显现授命说出自葛洪《神仙传》（传记性来源，S2）；timeline 节点 type 标"传说性来源，标注"，政体史实（蜀地神权政体，S12）分开陈述。
- **《想尔注》作者**：四说并存（张陵/张鲁/六朝初年/南北朝初年，S14；S4 主 190—220 张鲁说）；维基文库本署名"張道陵 東漢"是传统署名，引文均注明残卷性质（"原書為殘卷，由此句起，上缺"，S15）。不采单一说。
- **《周易参同契》**：托名魏伯阳、传 142 年作，维基内丹条目自身标 doubtful（S8）——列 works（性质标"托名，年代存疑"）而不设 timeline 节点。
- **《阴符经》**：撰人不详，战国黄老传说/北魏寇谦之/唐李筌三说并陈（S18 页头原文），托名黄帝。
- **站内《道家》条目系年差异**：站内作"约320 葛洪著《抱朴子》"，本包依 S11 作 317—318 成书/326—334 修订——相容但精度不同，本包不代改站内数据（evidenceLimits 末条留 Codex 审校）。
- **reference 级来源的使用**：英文维基 10 条、中文维基 2 条全部只用于定位性断言（年代/建制/书目结构），凡是学说内容的断言一律落在 SEP×2、IEP×1 或维基文库原典×5 上；S20（葛巢甫）为无来源模板条目，仅用于中文名形核对，coverage 字段已声明。

## 三、查重与既有内容

- 任务条目 coverage=related-branches-only：无同名顶级条目；唯一相关分支《道家》subSchools[3]"道教重玄学"（python 实查确认 index 3、desc"融合佛道，以'双遣双非'超越有无……"）；《道家》works/4（抱朴子）desc 含"道教哲学"、works/5（想尔注）desc 含"道教思想"，timeline 已有 142/约200/约320 三节点——均为提及级，本包不重复其站内角色而是补足道教传统自身的总览。
- 人物：philosophers.json python 实查——站内仅有 老子、庄子、河上公（另有王弼、郭象属魏晋玄学，不入本包 thinkers）；**葛洪、成玄英、李荣、张伯端、王重阳、魏伯阳、寇谦之、陆修静、陶弘景、陈抟、张道陵、吕洞宾等全部站内无**。本包 8 位 thinkers 中 3 位站内、5 位标"站外人物"，符合任务书"人物若确有材料而站内未收录，保留准确姓名并在 review.md 标明"的规则。
- 书籍：books.json python 实查可关联者——《道德经》6ef2f18cfdc9（epub 81章）、《老子道德经》dd8853676655（pdf 注译 82章）、《庄子》84adfb4d0c0b、《庄子今注今译》ea6f47b169f0（陈鼓应）、《庄子说什么》c3c401982587（韩鹏杰）、《道家与道教思想简史》219b862077e1（王卡，pdf 12章，站内唯一道教思想史专门书）。《抱朴子》《阴符经》《想尔注》《悟真篇》《参同契》等原典无站内藏书，不做关联。王卡书仅据 books.json summary 建议关联，未核读书内文本。

## 四、复核方法与结果

1. 全部 20 个来源当日经 curl 直接抓取全文后逐词定位核对（未用 WebFetch 开 SEP——沿用 T01 复核中 SEP 易触内容过滤的经验）；维基文库 5 页（想尔注残卷、抱朴子卷一〈畅玄〉、卷十六〈黄白〉、黄帝阴符经、道德经王弼本）关键引文逐字命中（脚本核对 76 组中文/英文引文串全部通过，含 3 处初检字符串误差的复验）。
2. 断言级记录 78 条（evidence.json），locator 均含亲眼核读的 verbatim 短引文；`/school/overview` 层 20 条、thinkers 8、relations 6、timeline 10、cihai 10、works 8、subSchools 7、引语 5、书籍/coverage/conclusion 4。
3. 数量：来源 20（学术百科 3 + 原典 5 + reference 12）、人物 8、时间线 10、术语 10、著述 8、分支 7——除 reference 级占比偏高（道教内容在 SEP/IEP 的覆盖面有限，已在各 coverage 字段声明用途与限度）外均在契约区间。
4. 结构自检：sourceRefs 全部可解析（packet 129 处 + evidence 全部）、fieldPath 全部可解析、relations 端点全部在 thinkers 内、来源 ID 无重复；两个 JSON 经 python3 -m json.tool / json.load 校验。

## 五、仍缺证据（与 packet.evidenceLimits 对应，13 条）

- **李荣（任务建议人物）**：英文维基 "Twofold Mystery"、"Li Rong (Taoist)" 均为不存在页面（实测 404），中文维基"李榮 (道士)"亦不存在（实测），维基文库检无其注专页；WebSearch 检索连续触发限流/内容过滤，未获可用结果——**未以模型记忆充当证据**，不设 thinker、不作断言；重玄学仅以成玄英呈现（S5/S6），刘进喜、蔡子晃按 S6 原句在 subSchools 提及。
- 重玄学"双遣有无/双遣双非"具体义理无逐字来源（S5 仅一句"influenced by Madhyamaka"）；站内道家条目"双遣双非"表述未复核原始出处，不继承。
- 内丹术语系统（精炁神循环等）的唐宋层次、《坐忘论》《清静经》文本、司马承祯专文、斋醮科仪/符箓/存思体系、《太平经》三合相通术语与 Hendrischke 英译本——均未核读，不写。
- 站内无任何道教人物与道教原典藏书——这是站内数据缺口，留 Codex 与后续书目任务。

## 六、实际核读 URL 清单（2026-10-04，全部 curl 全文抓取）

1. https://plato.stanford.edu/entries/daoism/ （S1）
2. https://iep.utm.edu/daoism/ （S2）
3. https://plato.stanford.edu/entries/zhuangzi/ （S3）
4. https://en.wikipedia.org/wiki/Xiang%27er （S4）
5. https://en.wikipedia.org/wiki/Taoist_philosophy （S5）
6. https://en.wikipedia.org/wiki/Cheng_Xuanying （S6）
7. https://en.wikipedia.org/wiki/Taiping_Jing （S7）
8. https://en.wikipedia.org/wiki/Neidan （S8）
9. https://en.wikipedia.org/wiki/Wuzhen_pian （S9）
10. https://en.wikipedia.org/wiki/Ge_Hong （S10）
11. https://en.wikipedia.org/wiki/Baopuzi （S11）
12. https://en.wikipedia.org/wiki/Way_of_the_Celestial_Masters （S12）
13. https://en.wikipedia.org/wiki/Quanzhen_School （S13）
14. https://zh.wikipedia.org/wiki/老子想爾註 （S14）
15. https://zh.wikisource.org/wiki/老子想爾注 （S15，残卷本）
16. https://zh.wikisource.org/wiki/抱朴子/卷01 （S16，〈畅玄〉）
17. https://zh.wikisource.org/wiki/抱朴子/卷16 （S17，〈黄白〉）
18. https://zh.wikisource.org/wiki/黃帝陰符經 （S18，正统道藏本）
19. https://zh.wikisource.org/wiki/道德經_(王弼本) （S19）
20. https://zh.wikipedia.org/wiki/葛巢甫 （S20，无来源模板条目，仅用于名形核对）

- 放弃/不可用：https://en.wikipedia.org/wiki/Twofold_Mystery → 条目不存在；https://en.wikipedia.org/wiki/Li_Rong_(Taoist) → 不存在；https://zh.wikipedia.org/wiki/李榮_(道士) → 不存在；https://zh.wikisource.org/wiki/老子想爾註（繁体"註"）→ 空页，改用简体"注"页面；https://zh.wikisource.org/wiki/陰符經 → 消歧义页，改用黃帝陰符經专页；https://zh.wikisource.org/wiki/道德經 → 索引页，改用王弼本专页；https://zh.wikisource.org/wiki/老子河上公章句 → 仅索引无正文，未引。

## 七、其他说明

- WebSearch 工具在李荣检索中连续返回限流（429）与内容过滤错误；按任务规则如实记录并放弃该路径，未以任何模型记忆内容充当证据。
- 道教相关中文检索对内容过滤器敏感度未知的问题未实际阻碍本包（curl 直抓全程可用），此经验供后续 T 组任务参考。
- packet 的 readingRoutes 与 evidenceLimits 按 T01 样例惯例置于 school 对象内；本包无"同日已有草稿"情形，为一遍写成加当日逐源复核。


## 审计会话修订记录（2026-10-04）

- 契约修订 2026-10-04：补 readingRoutes/evidenceLimits（审计会话B）。
