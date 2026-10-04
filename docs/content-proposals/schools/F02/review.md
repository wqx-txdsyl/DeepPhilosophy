# F02 形而上学（领域总览包）· 复核记录

- 复核日期：2026-10-04（全部 accessedAt/reviewedAt 均为真实访问日期）
- 复核方法：每个候选来源先检索、后逐个以 WebFetch 打开并读到相关段落才算核实；检索结果片段一律不作为已核实依据。人物姓名对照 `app/public/philosophers.json`，书籍 ID 对照 `app/public/books.json`（均为 worktree 内只读 grep）。两个 JSON 以 `python3 -m json.tool` 校验通过。本复核为研究员自检，非独立同行评审。

## 边界决定

1. **形而上学 ≠ 唯心主义**。thinkers 覆盖实在论者（亚里士多德）、否定实体的中观（龙树）、整体论理学（朱熹）、批判观念论（康德）、物理主义倾向的自然主义者（蒯因）与模态实在论者（刘易斯）——overview 明确写"不是唯心主义"，依据 S1 对该领域议题清单的中性呈现。
2. **形而上学 ≠ 神秘主义**。正文强调方法均为公开论证（中观归谬、康德二律背反推演、可能世界语义学），不以体验为准。注意：SEP Metaphysics 条目本身几乎不谈 mysticism（核读确认），故正文这一定位由"论证方法"的来源证据支持，而不是由某条目直接断言——已在措辞上避免"某某百科说它不是神秘主义"的伪引用。
3. **与科学假说的边界**。不写成"科学尚未解答的问题清单"：正文呈现两端——蒯因式连续论（S1 方法论节、S7 自然主义）与实证主义断裂论（S1，且注明 SEP 评其自指不融贯）。形而上学与科学的关系被处理为领域内部的争论，而非给读者一个伪结论。
4. **与既有子项的关系（查重）**。`app/public/schools/data/` 下无名为"形而上学/存在论/本体论"的条目（grep 核验）；分析哲学条目 subSchools[4]"模态、指称与形而上学"（kind=研究方向）已存在——本包为领域总览，proposal 只建议互链，不重复其内容。任务 evidence.mentionFiles 列出的 59 个含"形而上学"字样的条目一律不动，proposal 建议本包作为枢纽单向导流。
5. **跨传统比较**。共三处（亚里士多德—朱熹、亚里士多德—龙树、康德—蒯因），relations 中 type 全部标注"编辑比较"（除两条师承）；不写成历史影响或师承。亚里士多德—朱熹比较有 S5"has been compared broadly to…"的直接佐证；亚里士多德—龙树比较有 S4"svabhāva as substance 是批判目标"+ S1"substance 是旧形而上学核心"的结构性依据。未凑"一个西方+一个东方"配额：印度与宋儒各只收一位有 SEP 条目支撑的代表。
6. **师承仅两处且同源核实**（蒯因→刘易斯、蒯因→克里普克，S7 原句"students of Quine's"；刘易斯任教经历 S8）。
7. **coverage=related-branches-only**：未修改任何既有条目；主仓库 `/Users/sen/DeepPhilosophy` 全程未触碰。

## 分歧记录

- **模态实在论**：S8 呈现为刘易斯的辩护立场，S1 列出 Kripke–Plantinga vs Lewis 的对峙；正文不定胜负，subSchools 与 conclusion 均以"进行中的争论"呈现。
- **朱熹理气论**：S5 明确反对"粗糙二元论"读法，主张整体论；正文采该读法并注明这是条目立场（学界另有实体论/二元论式解读的争论空间，已入 conclusion 的"对译损耗"段）。
- **逻辑实证主义之失败**："自指地不融贯"是 SEP 条目作者的评断，正文一律写作"SEP 评价"，不作为无主观点。

## 查重与本地核对

- philosophers.json 命中：亚里士多德、龙树、朱熹、伊曼努尔·康德、威拉德·范·奥曼·蒯因、索尔·克里普克（均用站内精确姓名）；戴维·刘易斯（David Kellogg Lewis）不在站内，用通行译名并在 sub 字段注明。
- books.json 命中（ID 已核）：f11f1b13c278《形而上学》、8c0c6955c793《纯粹理性批判》、07f28f142bdc《从逻辑的观点看》、6b68595de71f《命名与必然性》——仅写入 proposal.suggestedBookLinks。

## 仍缺证据（已进 packet.evidenceLimits，正文相应回避）

1. 亚里士多德/康德/蒯因通行生卒年未在核读页出现——era 一律写时代；克里普克、刘易斯生卒有据（S10/S8）。
2. 蒯因《论何物存在》1948 年首发未核读（SEP 文献表抓取截断；Wikipedia 对应页为空）——时间线与 works 改用已核实的 1953 年文集。
3. "形而上学"中文译名源自《周易·系辞上》"形而上者谓之道"——ctext.org 被反爬拦截，未找到可核读替代来源，**未写入正文**，仅此备案。
4. 鸠摩罗什译《中论》颂文（"众因缘生法……"）未核读原文页——quotes 不用，改用已核实的 SEP 英译（清辨语）与希腊原文。
5. 朱熹卒年 1200 的正文页证据仅到"1130 年 10 月生于福建"，1200 取条目首行纪年（检索摘要），已标注不确定性。
6. 克里普克全部关键事实的已核实来源为 Wikipedia（reference 级）；SEP 无其独立条目（/entries/kripke/ 404）。建议后续以学术来源升级替换。

## 未采用来源及原因

- Britannica "Metaphysics"：直接抓取 403/JS 挑战，Wayback 与 web_reader 均限流/超时——未核读，不入 sources。
- IEP：metaphys/、metaphysics/ 均已重构为分类目录页，无正文可引；Nagarjuna 条目 404——未使用。
- MIT Classics（classics.mit.edu）亚里士多德英译：两次超时——未使用，改用 Perseus 希腊文本（已核读）。
- web_search 结果片段（jstor、PhilArchive 等）一律未作为依据。

## 实际核读 URL 清单（均于 2026-10-04 打开并读取相关段落）

1. https://plato.stanford.edu/entries/metaphysics/ （S1）
2. https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0051%3Abook%3D4%3Asection%3D1003a （S2，卷四）
3. https://www.perseus.tufts.edu/hopper/text?doc=Perseus%3Atext%3A1999.01.0051%3Abook%3D1%3Asection%3D980a （S2 同源，卷一开篇）
4. https://plato.stanford.edu/entries/madhyamaka/ （S3）
5. https://plato.stanford.edu/entries/nagarjuna/ （S4）
6. https://plato.stanford.edu/entries/zhu-xi/ （S5）
7. https://plato.stanford.edu/entries/kant-metaphysics/ （S6）
8. https://plato.stanford.edu/entries/quine/ （S7，两次定向读取：正文与文献表）
9. https://plato.stanford.edu/entries/david-lewis/ （S8）
10. https://plato.stanford.edu/entries/kant/ （S9）
11. https://en.wikipedia.org/wiki/Saul_Kripke （S10，经 MediaWiki API 提取）
12. https://en.wikipedia.org/wiki/Critique_of_Pure_Reason （S11，经 MediaWiki API 提取，交叉核验）
13. https://iep.utm.edu/metaphys/ 、https://iep.utm.edu/metaphysics/ 、https://iep.utm.edu/nagarjuna/ （读取后判定不可引：目录页/404）
14. 本地只读核验：app/public/philosophers.json、app/public/books.json、app/public/schools/data/school_分析哲学.json、docs/tasks/school-content-gap-tasks-2026-10-04.json

## 质量自评（对照契约，非凑数）

- 来源 11 个（SEP×8 为不同作者独立条目 + 原典 Perseus + reference×2），无互相转抄；≥1 支持学说范围与人物归属（S1/S4/S5/S8），≥1 支持原典与具体论证（S2，另有 S6 的 A52/B76 定位引文）。
- 术语 10、时间线 10、著述 8、人物 7，均在契约区间内。
- 无造引语、造年代、造师承、造子派；无页码编造；两处不确定（朱熹卒年、Kripke 来源级别）已显式标注。


## 主控修订记录（2026-10-04）

- 补齐契约要求的顶层 readingRoutes 与 evidenceLimits（内容取自本文件仍缺证据清单与 works/timeline 已核来源）。
