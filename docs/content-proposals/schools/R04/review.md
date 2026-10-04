# R04 数学哲学 — review.md（审读记录）

日期：2026-10-04 ｜ 复核人：包研究员（自查，非独立同行评审）

## 1. 查重结论

- **站内覆盖**：R04 为 mentions-only——任务 JSON evidence 三类精确匹配全空；`grep -r "数学哲学" app/public/schools/data/ docs/content-proposals/` 复核全站仅 `app/public/schools/data/school_北欧哲学.json` 一处标签级提及（哲学家列表「托尔·尼尔森，sub：逻辑哲学/数学哲学」，无任何立场/争论内容）。现有材料不足以承载本领域，立项为 **field 类新建**，与备忘录结论一致。
- **与 W01 柏拉图主义**：W01 packet（同批已完成）proposal.scope 原文「现代数学柏拉图主义（哥德尔等，仅作关联提示，建议由站内数学哲学内容任务承载——次轮备忘录已建议新建 R04」——本包即该预留接口的自然落点。切分依据：Linnebo（S2）§1.1 明言现代 platonism『如今独立于其原始历史灵感被定义和争论』。建议两包双向互链。
- **与 F03 逻辑与逻辑哲学**：F03 packet（同批已完成）kind=field，scope 已把『形式化的内在界限（不完备性、真不可定义性）』列为自己的问题。分工：F03 从形式系统与后承角度讲不完备性，本包从基础危机与希尔伯特纲领命运角度讲同一批定理；直觉主义排中律之拒——本包讲数学基础动机、F03 讲非经典逻辑系统性质。两包 thinkers 在弗雷格、哥德尔上重叠，各写各的角度、互链不重复。
- **与《分析哲学》**（school_分析哲学.json）：蒯因、弗雷格、哥德尔为分析传统核心人物，建议互链；本包只写其数学哲学面。
- **与北欧哲学**：本包不把「托尔·尼尔森」写入正文（原名与生平未核实），仅建议该条目将标签级提及改为互链。

## 2. 学术分歧与处理

- **Quine 的归属**：不径称蒯因为「数学柏拉图主义者」，一律写「蒯因—普特南不可或缺性论证」；其立场按 Linnebo §1.1 表述为「接受形而上学立场、拒绝直接把握类认识论与必然性模态论题」。
- **哥德尔定理的哲学意涵**：严格区分三件事——定理内容（相对特定形式系统的不可判定/不自证一致）、对希尔伯特纲领的冲击（依赖「有穷推理可形式化」前提，S5 记哥德尔与贝尔奈斯本人的保留）、流行误读（「存在不可证明的真理」，S6 §1.1 明文警告）。时间线与结论段均按此口径。
- **希尔伯特是否「形式主义者」**：S5 记多数评论者读作工具主义而 Hallett 异议；thinker.key 以「工具性辩护」措辞规避强断言。
- **布劳威尔退出《数学年刊》编委会**：S3 未标年份，正文不写年份（备忘录曾引「退出」，本包统一为「被逐出编委会」并按 S3 原文措辞，不注年份）。
- **贝纳塞拉夫年份纠正**：任务提示中「贝纳塞拉夫《数不可能是什么》1967」与全部已核来源冲突——S1 文献表明确 1965 年发表、1967 年为另一篇《上帝、魔鬼与哥德尔》（The Monist 51，Lucas/Penrose 相关）。本包按来源用 1965，并在时间线 detail 中留痕。
- **直觉主义为何可取**：布劳威尔心智构造路线与达米特意义理论路线的内部争论，本包仅在 subSchools 注边界，不展开（达米特细节未直接核读）。
- **维特根斯坦**：受布劳威尔 1928-03-10 维也纳讲演影响的程度 S3 明文 disputed（Hacker/Hintikka vs Marion），本包只在 evidenceLimits 提及，不展开。

## 3. 复核方法与结果

两轮（同日 2026-10-04）：

1. **第一轮（WebFetch 8 次）**：SEP 七条目（philosophy-mathematics / platonism-mathematics / intuitionism / hilbert-program / goedel-incompleteness / structuralism-mathematics / kant-mathematics）+ PhilPapers 调查页，逐页核读相关段落。
2. **第二轮（curl 原文比对）**：抓取 SEP philosophy-mathematics、intuitionism、goedel、frege 四页全文，grep 逐字比对关键引语、书目与生卒（Brouwer 1881–1966；Gödel b.1906 d.1978；Frege b.1848 d.1925；1931 论文原题与 Monatshefte 38: 173–198；Benacerraf 1965/1967/1973 文献表行；Quine 1969/Putnam 1972 引注位置）；另以 Wikipedia REST API 核贝纳塞拉夫生卒（仅用于 era 字段，S11）。
3. **结构核对**：packet.json / evidence.json 经 `python3 -m json.tool` 校验；philosophers.json（737 键）核对站内人名（柏拉图、伊曼努尔·康德、戈特洛布·弗雷格、威拉德·范·奥曼·蒯因为站内名；希尔伯特、布劳威尔、哥德尔、贝纳塞拉夫站内无人名键，用通行译名）；F03/W01 packet 以脚本读取对齐接口。

## 4. 仍缺证据（已写入 evidenceLimits，正文未使用相关内容）

1. 贝纳塞拉夫 1965/1973 两文的原刊期刊名（Philosophical Review / Journal of Philosophy 之通行说法未在核读页面逐字出现），works 条目不注期刊。
2. 贝纳塞拉夫生卒仅 reference 级来源（S11），宜再核普林斯顿讣告级来源。
3. PhilPapers 调查页无年份明文（通称 2009 初轮调查）；分群体细分与 2020 Survey 结果未核。
4. Britannica（403）与 IEP（无总论条目）受阻沿用备忘录记录，本次未重试；REP 未核。
5. 布劳威尔 1912 就职演讲的荷兰文原题、Kolmogorov 的 BHK 贡献年代、夏皮罗/雷斯尼克两部专著的出版社，均未获来源支持，条目不注。
6. 连续统假设独立性（科恩 1963）未核，不设节点；直谓主义仅在 S1 目录确认存在，未设 subSchool。

## 5. 实际核读 URL 清单（全部 2026-10-04）

| # | URL | 方式 |
|---|-----|------|
| S1 | https://plato.stanford.edu/entries/philosophy-mathematics/ | WebFetch 全文 + curl/grep 比对 |
| S2 | https://plato.stanford.edu/entries/platonism-mathematics/ | WebFetch 全文 |
| S3 | https://plato.stanford.edu/entries/intuitionism/ | WebFetch 全文 + curl/grep 比对 |
| S4 | https://philpapers.org/surveys/results.pl | WebFetch（数据行逐字核录） |
| S5 | https://plato.stanford.edu/entries/hilbert-program/ | WebFetch 全文 |
| S6 | https://plato.stanford.edu/entries/goedel-incompleteness/ | WebFetch 全文 |
| S7 | https://plato.stanford.edu/entries/structuralism-mathematics/ | WebFetch 全文（slug 经 SEP 目录确认） |
| S8 | https://plato.stanford.edu/entries/kant-mathematics/ | WebFetch 全文 |
| S9 | https://plato.stanford.edu/entries/goedel/ | curl/grep（生卒、1931 文献表、柏拉图主义表述） |
| S10 | https://plato.stanford.edu/entries/frege/ | WebFetch 全文 |
| S11 | https://en.wikipedia.org/api/rest_v1/page/summary/Paul_Benacerraf | curl REST API（仅生卒） |

访问失败记录：https://plato.stanford.edu/entries/structuralism-in-philosophy-of-mathematics/（404，slug 错误，已改用 S7 正确 slug）；https://www.britannica.com/topic/philosophy-of-mathematics（403，沿用备忘录记录）。
