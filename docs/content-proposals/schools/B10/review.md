# B10 阿毗达磨思想 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `B10`（proposedKind=tradition-overview，coverage=mentions-only，cohort 南亚／东亚／藏传）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **kind 维持 tradition-overview**：任务条目 proposedKind=tradition-overview；证据同向——阿毗达磨是跨部派的文献工程（论藏体裁）与论证方法，S1 明言"不同学派的阿毗达磨提出了不同的法分类"（82 与 75 只是存世两套），任务 scopeAndCautions"不要把所有阿毗达磨归为同一哲学学派"在文献层面有直接支撑。故不建议 kind=school，packet.proposal.kindNote 已说明，最终归类由 Codex 定。
2. **部派/立场/文献传统分层**：subSchools 仅 4 项且各自标 kind——有部（部派·哲学立场）、经量部（论师立场/学派，其教团组织史未获来源，不写）、上座部阿毗达磨（文献传统/立场）、汉传俱舍学（研习传统）。不虚构分支、不按配额凑数。
3. **三世实有之争为包内主线**：有部四论证、四大师说、世亲评破、经量部三层回应（滥收/两难/种子）均有一手学术转引定位；世友（位异）入 thinkers，法救/妙音/觉天仅概述转述（"大毗婆沙编纂主持""〈异部宗轮论〉作者"等传统说法未获本次来源，不写）。
4. **传记叙事层与史实层分开**：世亲生平按 S4 照录（真谛《婆薮槃豆法师传》"含传说甚至神话成分"、与玄奘《西域记》差异严重、"两世亲"假说已被近期研究排除）；众贤辩论挑战按 S2 标注"reported in Chinese and Tibetan sources"叙事层。
5. **原典可读性如实声明**：Gutenberg 两次检索 0 结果、en/zh 维基文库均无《俱舍论》正文页（实测）；所有 AKBh 引文均为 SEP/IEP 学术转引并逐条标注。站内《中国佛教史》关联仅标"通史研究书"，不标"可在线阅读原典"。

## 二、与姊妹包及既有条目的分工（查重）

| 包/条目 | 已有内容 | 本包边界 |
| --- | --- | --- |
| T01 佛教哲学 | subSchools 仅"早期佛教与部派阿毗达磨"一句阶段定位；世亲条目带《俱舍论》一句 | 本包承担阿毗达磨专门深度；建议互链导流 |
| B01 早期佛教 | 已声明"（阿毗达磨）不写，归 B10"；以 SEP 之 Sūtrānta 对比为划界句 | 本包起点恰接 B01 终点（部派分裂后论藏形成） |
| B02 中观 | 已载阿毗达磨二谛（世俗有/胜义有）与龙树的对照 | 本包给被批评方正面学说；中观破 svabhāva 仅按 S3 一句定位 |
| B03 唯识 | 已载世亲转宗、俱舍+唯识两线、六识→八识对照 | 本包只写论辩链前段（种子→阿赖耶识前驱）；成唯识论一线归 B03（S2 条目内 Xuanzang 0 命中实测） |
| B04 佛教逻辑 | 已载陈那/法称"经量部关联未核读不写" | 本包经量部表征主义只作知觉模型定位，量论正面展开归 B04 |
| 站内《印度哲学》 | 世亲 works 列表提及"《阿毗达磨俱舍论》"（mentions-only） | 本包不修改既有条目，建议互链 |

查重结论：现有目录无"阿毗达磨"同名顶级条目或分支（任务条目 exactTopLevelEntries/exactBranches/relatedBranches 均空）；无重复造页。

## 三、分歧与证据限度（摘要，全文见 packet.evidenceLimits 12 条）

- **世亲系年三源不一致**：S2 传 4 世纪笈多朝 / S1《俱舍论》"五世纪" / S4 列 270—350 至 420—500 诸说——照录不调和。
- **词源两解**、"刹那"长度诸师不一（0.13—13 毫秒）、上座部与有部刹那学说互异——均照录。
- **svabhāva 解释的学术警告**（Gethin 经 S1 转引；Cox 的分类学→本体论流变研究经 S1 转引）：本包未核读 Cox/Gethin 原文，转引层级已标明。
- **人物收录从紧**：站内实查仅世亲、玄奘两位相关人物入站（世友/众贤/觉音为站外，材料充分；无著站内无，不入本包 thinkers，转宗叙事以世亲为中心转述）。
- **books.json 无阿毗达磨藏书**：《中国佛教史》为唯一相关藏书，已实读章节（第十四章/第十八章俱舍段落逐字摘引入 S6）。

## 四、复核方法与结果

1. 独立重抓（不复用 T01/B03 结论）：SEP Abhidharma（110KB）与 SEP Vasubandhu（145KB）curl 全文 + python 多轮 grep（momentariness/sarvāstivāda/sautrāntika/svabhāva/kośa/Kośa/seeds/ākāra/kāritra/Xuanzang 等），逐字定位并摘录；SEP 两条目系年差异即由此复核发现。
2. IEP Sarvāstivāda Buddhism 与 IEP Vasubandhu 两条目全文深挖：四大师三世说、AKBh 6.4 二谛定义、经量部两难、传记文献学（"两世亲"排除句、系年诸说、"狂象"语）均取得 verbatim 定位。
3. 原典探测：Gutenberg（2 查询 0 结果）、维基文库（en/zh 无正文页；zh 有丁福保《佛學大辭典/俱舍論》条目，实测可读并逐字核读，另见《俱舍論頌疏論本》卷014/015、《俱舍論疏》卷017 等疏释页）。
4. 站内核对：philosophers.json（dict 结构 python 子串实查：世亲'约公元4世纪至5世纪'/玄奘'602-664年'在站；无著/觉音/世友/众贤 0 命中）；books.json 409 本实查；蒋维乔《中国佛教史》经 backend/data/book_chapters（git 跟踪源）第十四章/第十八章实读。
5. evidence.json 77 条：thinkers 5、relations 4、timeline 7、cihai 10、works 6、subSchools 4、引语 4、coverage/books/原典探测/分工 5，locator 均含 verbatim 短引文，fieldPath 与 sourceRefs 全部解析通过（脚本核验 0 坏点）。
6. packet.json 两个 JSON 经 `python3 -m json.tool` 校验；readingRoutes/evidenceLimits 在顶层（未放 school 内）；relations 4 条 from/to 与 thinkers.name 精确相等（脚本核验）。
7. **内容复核（交付后重读原文一遍）**：逐条回对抓取文本，确认三处易错点已按原文处理——(a) 上座部七论英译范围按原文"all but the Yamaka"（除《双对》外）呈现；(b) S2 系年（Chandragupta II 在位 380—415，即 4 世纪）与 S1"五世纪"并存，timeline/work 条目均以"4—5世纪（系年有差）"呈现并注明三源差异；(c) SEP Vasubandhu 条目内 "Xuanzang" 0 命中经 grep 复测，成唯识论一线确认归 B03。

## 五、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/abhidharma/ （curl 全文+多轮 grep 定位）
2. https://plato.stanford.edu/entries/vasubandhu/ （同上）
3. https://iep.utm.edu/sarvastivada/ （curl 全文深挖）
4. https://iep.utm.edu/vasubandhu/ （curl 全文深挖）
5. https://zh.wikisource.org/wiki/佛學大辭典/俱舍論 （实测可读，逐字核读）
- 探测后放弃：iep.utm.edu/abhidharma/ 等 3 个 IEP 猜测路径 → 404；Gutenberg /ebooks/search/?query=Abhidharmakosa 与 ?query=Abhidharma → 0 结果；en.wikisource "Abhidharmakosa" → 页面不存在；zh.wikisource "俱舍論" 正文页 → 页面不存在（有疏释与辞书条目）。
- 站内源：app/public/philosophers.json、app/public/books.json、app/public/schools/data/school_印度哲学.json、backend/data/book_chapters/1201d003be31/（全章节 grep 定位：16.json=第十四章与 20.json=第十八章含俱舍段落，两章详读摘引）。

## 六、仍缺证据 / 阻塞

- 无阻塞。待补强（非本包任务）：Cox《Disputation and Transformation》、von Rospatt《刹那灭》专著、Dhammajoti《Sarvastivada Abhidharma》（IEP 评为英文最详）、Gold《Paving the Great Way》等学术专著——升级本包来源等级的下一批任务。
- 世友系年、《俱舍论》/玄奘译年份、经量部教团组织史、两部论藏成书层积——未获可引定位，均不写。
