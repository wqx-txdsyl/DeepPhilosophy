# P04 二元论（Dualism）— review.md

- 日期：2026-10-04（reviewedAt 同）
- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` 中 id=P04（P1-content-packet，kind=position，coverage=mentions-only）
- 输出目录：`docs/content-proposals/schools/P04/`（开档前该目录不存在，**无旧稿处置问题**——已按要求先 ls 检查，未发现同日草稿，全新撰写；I05 目录已交付包仅作接口参照，未改动其任何文件）
- status：ready-for-review（研究员自查，非独立同行评审）

## 一、范围边界决定

1. **主线收窄为西方心身二元论**：实体/属性/谓词三分 + 交互/副现象/平行/形质四因果形态，全部锚在 SEP "Dualism" 条目的小节结构上，不自创分类。
2. **笛卡尔与松果腺/交互难题**：论证层用 IEP 笛卡尔专条 + Gutenberg 拉丁原典（#23306）双重支撑；松果腺文本史用 SEP 归档条目（正条已 retire，按 Summer 2026 归档版核读）。伊丽莎白 1643 之问由 SEP 伊丽莎白专条与 IEP 互证，不采用该条目未提及的头衔（如 Lateran canoness）。
3. **当代部分**：查默斯属性二元论定义直接取其论文官网全文（consc.net），并经 SEP Dualism 条目的 Chalmers (1996) 与 2020 调查数据（Bourget & Chalmers 分析报告 2023 年出版）旁证；『任务给的可核则写』 satisfied。
4. **价值二元论 / fact-value 二分：点到为止**。SEP Dualism 条目只有『某领域两种根本类』的一般定义、无价值二元论专节；事实—价值一侧只以 SEP Hume 条目的 is–ought 段落（T 3.1.1.27）定位，进概述一句 + 术语表一条，不展开、不进时间线。Britannica "dualism (philosophy)" 两次尝试不可达（WebFetch 403；curl 过 Cloudflare 验证页），**未列为来源、其宗教二元论内容一律未采信**。
5. **与 I05 二元论吠檀多（已交付）不合并**：实查 I05/packet.json（name=二元论吠檀多，摩陀婆/Tattvavāda，svatantra/paratantra），与本包无历史传承；接口在 proposal.interfaceNotes 写为『同名异实』编辑注记，明确禁止写成同一学派或师承。
6. **与 P03 一元论（同日并行交付）**：仅按任务约定在 proposal 声明对立立场接口；P03 目录开档时尚不存在，未交叉核对，已写入 evidenceLimits。

## 二、查重

- 站内 `app/public/schools/data/` 无二元论条目（grep 二元/一元/唯物/唯心 仅见 唯心主义 等），任务 mentionFiles 的 21 个流派条目均为**提及级**，不构成本条目与现有条目的内容重复。
- 人物姓名全部经 python 子串匹配 `philosophers.json`：柏拉图、勒内·笛卡尔、伊丽莎白公主、巴鲁赫·斯宾诺莎、戈特弗里德·威廉·莱布尼茨、吉尔伯特·赖尔、卡尔·波普尔在站内且以站内名为准；**大卫·查默斯、约翰·C·埃克尔斯站外**（查默/查尔默均无匹配）， thinker 条目已标注。
- 书籍 ID 全部经 python 实查 `books.json`（409 本）：第一哲学沉思集 88b56fb4da52、谈谈方法 8c3044772b18、方法论·情志论 49c80096b16d、伦理学 32fb0956b9b1、单子论 676cac465f6f、神正论 83eb8857a597、心的概念 2110a49aec94；另《笛卡尔的错误》f6af30aab723 仅在 review 提及、不进 works。无造 ID。

## 三、来源层级与分歧记录

- 16 个来源全部实际打开读到相关段落：SEP 六条目（Dualism / Elisabeth / Pineal Gland 归档版 / Spinoza / Leibniz / Ryle / Popper）、IEP 两条目（Descartes 心身区分、Karl Popper）、consc.net 查默斯论文全文、Gutenberg 两个原典全文、Wikipedia 三词条（仅限生卒年与『机器中的幽灵』措辞定位，type=reference）。WebSearch 接口当日限流，检索改以直连权威 URL 完成，检索路径不影响核验。
- **学术分歧如实呈现**：SEP Dualism 记录的 received view（实体二元论『不再是可敬选项』、属性二元论『须认真对待』）；杰克逊放弃知识论证、查默斯 2016 转向实体二元论；is–ought 段落的解释学争议（S9 明言主流读法有困难）。未替任何一方下哲学判断。
- **引语纪律**：4 条 quotes + 1 条 quote + 1 条 closingQuote 均逐字核对（拉丁原典 python 定位；英译注明翻译层级；查默斯官网版 curl 核对）。笛卡尔—伊丽莎白信引语为 IEP 英译转引，已标 kind 并注明原文为法文。

## 四、仍缺证据 / evidenceLimits（详见 packet.json）

- 《伦理学》1677 出版年：SEP 斯宾诺莎条目仅暗示（卒年 + 身后出版），时间线措辞已收敛为『去世、遗著随即结集出版』。
- 查默斯生年未核实，era 只写『当代』。
- 『机器中的幽灵』措辞层级为 reference 型（维基）定位 + SEP 旁证，未核 1949 纸本。
- SEP Dualism 本次抓取未含 pairing problem / neural dependence 的明确表述，conclusion 未将其写成有来源支撑的独立反驳。
- 1643-05-21 信的 AT 卷页编号未在核读来源中给出，quotes/1 的 locator 只写条目与日期。

## 五、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/dualism/
2. https://iep.utm.edu/descartes/ （René Descartes: The Mind-Body Distinction, Justin Skirry）
3. https://plato.stanford.edu/entries/elisabeth-bohemia/
4. https://plato.stanford.edu/entries/pineal-gland/ （正条已归档）→ https://plato.stanford.edu/archives/sum2026/entries/pineal-gland/
5. https://plato.stanford.edu/entries/spinoza/
6. https://plato.stanford.edu/entries/leibniz/
7. https://plato.stanford.edu/entries/ryle/
8. https://plato.stanford.edu/entries/popper/
9. https://plato.stanford.edu/entries/hume-moral/
10. https://www.gutenberg.org/files/23306/23306-h/23306-h.htm （Meditationes 拉丁原典）
11. https://www.gutenberg.org/files/70091/70091-h/70091-h.htm （Six Metaphysical Meditations, Molyneux 1680）
12. https://consc.net/papers/nature.html （Chalmers, Consciousness and its Place in Nature）
13. https://en.wikipedia.org/wiki/The_Concept_of_Mind
14. https://en.wikipedia.org/wiki/Ren%C3%A9_Descartes
15. https://en.wikipedia.org/wiki/Plato
16. https://iep.utm.edu/karl-popper/ （仅生卒年；该条目无《自我及其大脑》内容，已记录）

尝试未成功（不列为来源）：https://www.britannica.com/topic/dualism-philosophy （403 / Cloudflare 验证页）；https://iep.utm.edu/gilbert-ryle/ 与 https://iep.utm.edu/ryle/ （404）。

## 六、数量自检

术语 10、时间线 10、著述 8、人物 8、关系 7、subSchools 6、quotes 4——均在契约『通常』区间；两个 JSON 已过 `python3 -m json.tool`。
