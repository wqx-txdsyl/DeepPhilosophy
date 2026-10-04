# T01 佛教哲学 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `T01`（proposedKind=tradition-overview，P1-content-packet，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **总览 ≠ 地区条目的重复**。本包定位为跨地区"问题地图"枢纽：论证线索（缘起/无我/空/唯识/量论/三谛/一念三千/一即一切/自性）为主，历史阶段与地域传统为纬。地区与宗派细节显式导流给站内《印度哲学》《隋唐佛学》《西藏哲学》《东南亚哲学》《日本哲学》——proposal.relatedExisting 逐条写明分工。
2. **宗派组织史与哲学论证分开**。subSchools 的 kind 分别标为历史阶段/学派/研究方向/学派传统/地域传统；timeline 以文献、论争与建制节点组织，不虚构年代。
3. **接受史关系有据才写**：二谛→三谛（SEP Tiantai 专节"From Two Truths to Three Truths"）、俱舍论对汉藏的影响（SEP Abhidharma 原句）、华严兼取中观/瑜伽行/起信论（SEP Huayan 原句）三处为来源直接支持；天台—华严的平行建制明确标为**编辑比较**。
4. **不进行东西方哲学比较**。'空 vs 反实在论''唯识 vs 观念论'等比较本包一律不做（conclusion 明示理由）；"'唯识家=观念论者'"标签在 SEP Vasubandhu 条目本身就是争议专节，正文只注明争议存在。
5. **任务书优先案例的衔接**：《隋唐佛学》下的北宋山家/山外分支由 Codex 审校处理，本包不代述隋唐宗派细节；藏传四派仅列参考级年代，中观应成/自续之争留给《西藏哲学》。

## 二、分歧与争议的处理

- **佛陀年代**：S1 载两说（旧说约前560—480；今多数学者主卒约前405）——timeline 用"约前5世纪"，thinkers 纪年两说并陈。
- **世亲年代**：SEP Vasubandhu 系于4世纪笈多朝，SEP Abhidharma 把《俱舍论》系于五世纪——两处并陈不调和；"转宗故事"被部分学者质疑（S3 原句），如实呈现。
- **量论的哲学/教义边界**：S7 开篇明言"没有作者在独立于形上学承诺的情况下写作知识论"——conclusion 据此把"以'哲学'名义重读的切分"处理为方法论决定，不冒充中性。
- **reference 级来源**：藏传（S10）、上座部（S11）、玄奘（S12）三条为 Wikipedia，仅用于定位性断言（四派年代/巴利藏/西行纪年），专文细节一律不写，已在 evidenceLimits 声明。

## 三、查重与既有内容

- 无同名顶级条目、无同名分支（任务 JSON 两个 exact 数组为空）；mentions-only 9 项（印度哲学、高加索-草原、魏晋玄学、隋唐佛学、西藏哲学、东南亚哲学、日本哲学、哲学入词、蒙古中亚）。
- 人物：站内 philosophers.json 实查有 释迦牟尼/龙树/世亲/智顗/慧能/玄奘/法藏（全部采用站内姓名与纪年）；陈那、法称、鸠摩罗什、觉音站内无——陈那/法称按来源实情收入 relations 并标注站外，其余不设条目。**宗喀巴·罗桑扎巴站内已有**（纪年"14世纪-15世纪"），本包因未核读格鲁派哲学专文不设 thinker 条目，展开建议由站内《西藏哲学》承载（初稿误记"站内无宗喀巴"，第二遍复核已更正）。
- 书籍：books.json python 检索（佛/禅/经/论/梵等关键词）仅《中国佛教史》1201d003be31 一种佛学专门藏书，建议关联只列该种；站内无《金刚经》《心经》《坛经》原典藏书，不做关联建议。

## 四、复核方法与结果

1. 研究由主会话直接执行：curl 直抓 SEP×6（buddha/abhidharma/vasubandhu/buddhism-tiantai/buddhism-huayan/epistemology-india）、Wikipedia×3（Tibetan Buddhism/Theravada/Xuanzang）、维基文库×2（心经玄奘译本、六祖坛经）全文；SEP Madhyamaka 与 Nagarjuna 两条于同日 F02 复核中经 WebFetch 逐字核读。检索摘要一律不作为依据。
2. 每条关键断言在 evidence.json 有对位记录（thinkers 7、relations 6、timeline 10、cihai 10、works 8、subSchools 9、引语 4、书籍/coverage/conclusion 3），locator 均含 verbatim 短引文。
3. 数量：来源 13（学术百科 8 + 原典 2 + reference 3）、人物 7、时间线 10、术语 10、著述 8、分支 9——均在契约区间（reference 级来源占比与用途已声明）。
4. 两个 JSON 经 `python3 -m json.tool` 校验。

## 五、仍缺证据（与 packet.evidenceLimits 对应）

- 汉传净土/律/真言三宗、藏地宗义（应成/自续）、《释量论》课程地位、觉音与《清净道论》、《坛经》诸本异同、天台"性具"、华严"四法界/六相"、法藏"椽喻"中文名目、玄奘译场组织与《成唯识论》糅译——均未获核读来源，一律不写。
- 《心经》梵藏对勘研究未核读。

## 六、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/buddha/ （WebFetch 逐字）
2. https://plato.stanford.edu/entries/abhidharma/ （curl 全文+grep 定位）
3. https://plato.stanford.edu/entries/vasubandhu/ （同上）
4. https://plato.stanford.edu/entries/buddhism-tiantai/ （同上）
5. https://plato.stanford.edu/entries/buddhism-huayan/ （同上）
6. https://plato.stanford.edu/entries/epistemology-india/ （同上）
7. https://plato.stanford.edu/entries/madhyamaka/ （同日 F02 复核，WebFetch 逐字）
8. https://plato.stanford.edu/entries/nagarjuna/ （同上）
9. https://zh.wikisource.org/wiki/般若波羅蜜多心經_(玄奘譯) （curl 逐字）
10. https://zh.wikisource.org/wiki/六祖大師法寶壇經 （curl 逐字）
11. https://en.wikipedia.org/wiki/Tibetan_Buddhism （curl 定位）
12. https://en.wikipedia.org/wiki/Theravada （curl 定位）
13. https://en.wikipedia.org/wiki/Xuanzang （curl 定位）
- 放弃：https://plato.stanford.edu/entries/epistemology-indian/ → 404（改用 epistemology-india）；维基文库心经消歧义页 → 改玄奘译本专页。

## 七、同日第二遍复核与处置（2026-10-04）

发现 `T01/` 目录已有当日早间（09:02–09:06）生成的完整四件草稿，未盲信，逐源重开核实后处置如下：

1. **逐源重核**（第二遍，全部当日完成）：
   - SEP×7（buddha/vasubandhu/madhyamaka/buddhism-tiantai/buddhism-huayan/epistemology-india/nagarjuna）经 WebFetch 打开并逐字核对引文——S1 年代两说句、S3 "appearance only"句、S4 hallmark 与三位注释家句、S5 三代表与三谛/一念三千节标题、S6 "one is all"与椽喻/传播/思想来源句、S7 两大名字与 pramāṇa-śāstra 句、S13 150—250 与 450 颂句全部命中。
   - SEP abhidharma：WebFetch 小模型两次误触内容过滤，改 curl 抓全文 + grep 定位，所有被引句子（前3世纪分裂句、carefully defined 句、dharma theory 句、Kośa "most influential"句、Sūtrānta 对比句、"in seeing these four truths one realizes the ultimate truth"句）逐字命中。
   - 维基文库×2、Wikipedia×3：curl 全文 + 定位核对，S10 四派年代句、S11 巴利藏句、S12 602–664/Śīlabhadra/行记句均命中。
2. **处置决定：保留草稿，改正两处硬伤后维持 ready-for-review**：
   - **引文更正**：《坛经》悟道语第五句草稿作"何期自性**性**能生万法"，维基文库原文为"何期自性**能**生万法"（多一"性"字）——packet.json overview/thinkers/quotes 与 evidence.json 两处 locator 已同步改正。
   - **事实更正**：初稿 evidenceLimits 与本文件查重节记"站内 philosophers.json 无……宗喀巴"，python 实查站内实有"宗喀巴·罗桑扎巴"（14世纪-15世纪）——两处已更正；不为其设 thinker 的决定不变（本包未核读其哲学专文，S10 仅为参考级四派年代）。
3. 其余内容（结构、边界决定、13 个来源、全部数量项）经第二遍核实无出参，予以保留；reviewMethod 字段已改写为反映两遍自查。
