# U04 逻辑经验主义（逻辑实证主义）资料包 — 复核记录

- 复核日期：2026-10-04（全部 URL 于当日实际打开并读取相关段落）
- 复核人：zcode 研究员（单包自检，非独立同行评审）
- 输出目录：`docs/content-proposals/schools/U04/`（本次全新创建）

## 1. 目录处置记录（开工前检查）

按任务要求先 ls 目标目录：`docs/content-proposals/schools/U04/` **不存在**（同日其他任务目录 U02、U03 已存在，U04 无同日旧稿）。因此不存在"保留/重写"处置问题，本包四文件均为当日从零写出。

## 2. 查重结论（对照任务 evidence 字段）

- **exactBranches（3 处既有分支子项）**：已逐一用 python3 读取原文对照——
  - `school_实证主义.json` 分支 index 2「逻辑实证主义」：一句话 desc（石里克、卡尔纳普发起、证实原则）；
  - `school_分析哲学.json` 分支 index 1「逻辑经验主义」：一句话 desc，已含"维也纳与柏林等地""内部意见并不一致"的表述，与本包术语结论一致；
  - `school_科学哲学.json` 分支 index 0「逻辑实证主义」：一句话 desc。
  - 三处均为浅层子项，无时间线、无书目、无引语可继承；本包按"深化包"写，未继承任何未核实内容。
- **mentionFiles（8 处提及）**：仅在正文中出现术语，无独立条目，无去重动作。
- **边界决定**：本包只交一个包，内部用 subSchools 区分维也纳学圈／柏林学派／左翼／统一科学运动；三个术语（逻辑实证主义／逻辑经验主义／维也纳学圈）的差异有专门 cihai 条目（依据 SEP Logical Empiricism、SEP Neurath）。

## 3. 范围与人物边界决定

1. **维特根斯坦**：按任务范围作为"前史（影响与疏离）"写入 thinkers，sub 明确标"前史：《逻辑哲学论》的影响源与疏离者"，不冒充学圈成员；与石里克、哈恩、卡尔纳普的三条 relation 分别标为历史接触/阅读/影响与批评，未写成师承。
2. **蒯因**：作为外部批判者（1951 两个教条）不入 thinkers（避免把批判者写成学派成员），以 timeline 终点节点、works 第 8 条、quotes、overview/conclusion 承载；蒯因与卡尔纳普的私人关系（1934 布拉格会面、自认弟子数年）写在 overview 与 evidence，不造 relation（因 relations 的 to 必须是本包 thinkers）。
3. **波普尔**：仅按 SEP Vienna Circle 明文（"was never a member or associate"）作边界注记，不入 thinkers；站内藏书《科学发现的逻辑》只作对照阅读建议。
4. **艾耶尔**：明确标为"非学圈成员"的单向传播者（1933 旁听）。
5. **人名**：以站内 philosophers.json 精确姓名为准——莫里茨·石里克、鲁道夫·卡尔纳普、阿尔弗雷德·艾耶尔、威拉德·范·奥曼·蒯因、路德维希·维特根斯坦、亨佩尔（站内即单名"亨佩尔"）。纽拉特、赖兴巴赫、哈恩站内无条目（已用多种译名变体检索确认：诺伊拉特/莱欣巴哈/赖欣巴哈/纳拉特等均无），thinkers 用通行译名并已在 packet.evidenceLimits 声明。
6. **跨传统比较**：本包无东方配额凑数；与休谟/马赫/孔德的区别仅按 Britannica 逻辑实证主义条目一笔带过。

## 4. 来源核读清单（全部实际打开）

已核实并引用（15 个，均当日读取相关段落）：

| # | URL | 结果 |
|---|-----|------|
| S1 | plato.stanford.edu/entries/vienna-circle/ | 读到编年、成员、争论、流散；正文 3.3 节后截断，参考文献未读到 |
| S2 | plato.stanford.edu/entries/logical-empiricism/ | 全条目，含书目卷页（T&M、Two Dogmas、LTL） |
| S3 | plato.stanford.edu/entries/carnap/ | 正文已读；书目节截断 |
| S4 | plato.stanford.edu/entries/reichenbach/ | 全条目要点 |
| S5 | plato.stanford.edu/entries/neurath/ | 全条目要点（水手比喻定本 1932b） |
| S6 | plato.stanford.edu/entries/schlick/ | 全条目要点（1924-12-12 信、1927 初见、1936-06-22 遇刺 Johann Nelböck） |
| S7 | plato.stanford.edu/entries/wittgenstein/ | 出版史与 1931"教条"自评 |
| S8 | en.wikisource.org/wiki/Tractatus_Logico-Philosophicus（含 /4 /5 /6 /7 子页） | 命题 4.0031、4.116、5.6、6.53、6.54、7 逐字核对 |
| S9 | iep.utm.edu/carnap/ | 全条目，含书目 |
| S10 | iep.utm.edu/vienna-circle/ | 全条目（1907 前史、会议年表、Erkenntnis 1930–1940） |
| S11 | ditext.com/quine/quine.html | 全文逐字核对（两个教条命名、§V 两句、出处页眉） |
| S12 | britannica.com/topic/Vienna-Circle（经 web_reader 读取） | 全文 |
| S13 | britannica.com/topic/logical-positivism（经 web_reader 读取） | 全文（哈恩 1922、1970 终结） |
| S14 | britannica.com/biography/A-J-Ayer（经 web_reader 读取） | 全文（生卒、1933 维也纳、可证实性表述） |
| S15 | marxists.org Carnap《Philosophical Foundations of Physics》ch.23–26 | 全文读取（观察/理论词项连续谱、对应规则、拉姆塞句） |

尝试后失败、未引用（记录以备复核）：

- gutenberg.org 的 Tractatus 两个 URL（/files/5740/…、/cache/epub/5740…）404 → 改用 Wikisource 公版。
- britannica.com 经 WebFetch 直连 403（Vienna-Circle、Rudolf-Carnap、logical-positivism 三次）→ 改经 web_reader 成功（S12/S13/S14）；Rudolf-Carnap 人物页最终未读取成功，其所需事实全部改由 SEP/IEP Carnap 承载。
- link.springer.com（Erkenntnis 原刊页）WebFetch 403、web_reader 网络错误。
- philpapers.org/rec/CARUOD 404（猜错记录号）；philpapers 检索页 web_reader 拒绝该 URL 格式。
- iep.utm.edu/ayer/、/ay-er/ 404（IEP 无艾耶尔条目可用 URL）→ 艾耶尔事实改由 Britannica A-J-Ayer 承载。
- iep.utm.edu/reichenbach/ 返回空壳页（仅导航），未引用。
- en.wikipedia.org《Elimination of Metaphysics…》词条 404（未存在该独立词条）。
- SEP Vienna Circle 与 SEP Carnap 的文末参考文献节两次尝试（含 r.jina.ai 代理）均在正文处截断，未读到。

WebSearch 仅用于发现候选 URL 与确认英译标准出处（Ayer 1959 选集 pp. 60–81），相关片段未直接采信为断言依据。

## 5. 主要证据限度（与 packet.evidenceLimits 一致的补记）

1. **柏林学会成立年份**：通行记载为 1928，但本次打开的全部页面（SEP 两条、Britannica、IEP）都只给成员与 1929 年布拉格联办事实。按"不编造成立年份"纪律，正文写"1920 年代后期–1933"，未标 1928。
2. **卡尔纳普《通过语言的逻辑分析清除形而上学》**：SEP VC 正文引作 Carnap 1932a（"纯粹逻辑的形而上学批判"，1932），SEP Carnap 给出立场概括（"伪装成知识的失败艺术"）；但德文原题拼写与 Erkenntnis 卷页未能在任何已打开页面核到（Springer/PhilPapers 均访问失败）。works 条目按通行书目标题写出、明确不标卷页，并在 evidence.json 该条 uncertainty 与 packet.evidenceLimits 双重声明。这是本包最主要的残余不确定性。
3. **艾耶尔 LTL 强/弱可证实性细则**：原书全文未核读，未写入细则，只用 Britannica 给出的原则表述。
4. **生卒年缺口**：维特根斯坦、哈恩、纽拉特出生年、赖兴巴赫出生年未在已核页面出现，era 字段一律用活动期/交往期写法，未标这些年份（宁缺毋假）。
5. **费格尔移美年份**：SEP 两条目分别记 1930 与 1931，正文写"1930 年前后"。
6. **凶手姓名**：从 SEP Schlick 作 Johann Nelböck（他源多作 Hans Nelböck）；IEP 记其为"同情纳粹的学生"，动机线索保留在 review 而非正文断言。
7. **"仿斯宾诺莎书名"**（works/0 desc）：通行说法，未在已核页面出现——编辑采用前可删此半句，不影响其余内容。
8. **记录语句之争三方原刊卷页**：只给篇名与年份，未逐一核读原刊。

## 6. 质量标准自检

- 来源：15 个（≥3），互不转抄；学说范围与人物归属由 S1–S7/S10/S12–S14 支撑；原典与具体论证由 S8（Tractatus 逐条）、S11（Two Dogmas 逐句）、S15（Carnap 1966 选章）支撑。
- 数量：术语 10（契约 6–10）；时间线 10（6–10）；著述 8（4–8）；人物 8（4–8）。均在区间上限内。
- 引语：三处直接引语均逐字核对版本与位置（Ogden 命题 7/4.116；ditext §V），中译均注明"转译"；纽拉特水手比喻注明经 SEP 英译转译、1932 定本。未编造任何引语、页码、师承、子派或成立年份。
- JSON 校验：packet.json、evidence.json 均以 `python3 -m json.tool` 通过（见下）。
- git：未做任何 git 写操作；仅在本目录创建四个文件。

## 7. 结论

status = **ready-for-review**。残余风险集中在 works/3（卡尔纳普 1932 论文的书目细节）与柏林学会成立年份两处，均已按契约降级为"不写具体值 + evidenceLimits 声明"，不影响其余内容使用。

## 8. 实际核读 URL 清单（2026-10-04）

以下 15 条 URL 为 2026-10-04 当天逐一实际打开并读到相关段落的全部来源（对应 packet.json sources，均已标注 accessedAt: 2026-10-04）。标 ★ 者为经 web_reader 读取（Britannica 域名对 WebFetch 返回 403）；其余经 WebFetch 读取。

1. Stanford Encyclopedia of Philosophy: Vienna Circle — https://plato.stanford.edu/entries/vienna-circle/ （学圈编年、成员、记录语句之争、流散年表；正文 3.3 节后截断，参考文献节未读到）
2. Stanford Encyclopedia of Philosophy: Logical Empiricism — https://plato.stanford.edu/entries/logical-empiricism/ （术语差异、柏林学会、《认识》、流散与蒯因批判；含书目卷页）
3. Stanford Encyclopedia of Philosophy: Rudolf Carnap — https://plato.stanford.edu/entries/carnap/ （《构造》、宽容原则原文、1931-01-21 拒斥图式论、1936 芝大）
4. Stanford Encyclopedia of Philosophy: Hans Reichenbach — https://plato.stanford.edu/entries/reichenbach/ （柏林小组、《认识》1930、伊斯坦布尔/UCLA 行迹、发现/辩护区分）
5. Stanford Encyclopedia of Philosophy: Otto Neurath — https://plato.stanford.edu/entries/neurath/ （铸"逻辑经验主义"、纽拉特原则、水手比喻 1932 定本、百科全书与 ISOTYPE）
6. Stanford Encyclopedia of Philosophy: Moritz Schlick — https://plato.stanford.edu/entries/schlick/ （1922 讲席、1924 组圈、1924-12-12 信、1927 初见、1936-06-22 遇刺、Konstatierungen）
7. Stanford Encyclopedia of Philosophy: Ludwig Wittgenstein — https://plato.stanford.edu/entries/wittgenstein/ （《逻辑哲学论》出版史、对学圈影响、1931"教条"自评）
8. Tractatus Logico-Philosophicus（Ogden 英译，Wikisource） — https://en.wikisource.org/wiki/Tractatus_Logico-Philosophicus （公版原文；另核读其子页 /4、/5、/6、/7，逐字核对命题 4.0031、4.116、5.6、6.53、6.54、7）
9. Internet Encyclopedia of Philosophy: Rudolf Carnap — https://iep.utm.edu/carnap/ （反形而上学立场、可检验性放宽史、物理主义论文书目、移美与蒯因关系）
10. Internet Encyclopedia of Philosophy: Vienna Circle — https://iep.utm.edu/vienna-circle/ （1907 前史、宣言标题、会议年表、哥德尔哥尼斯堡 1930）
11. W.V.O. Quine, "Two Dogmas of Empiricism"（ditext.com 全文） — https://www.ditext.com/quine/quine.html （两个教条命名、§V 整体论两句、出处页眉逐字核对）
12. ★ Encyclopaedia Britannica: Vienna Circle — https://www.britannica.com/topic/Vienna-Circle （学圈形成、柏林姐妹学会、1929 宣言、1938 解散）
13. ★ Encyclopaedia Britannica: Logical positivism — https://www.britannica.com/topic/logical-positivism （术语并列、1922 哈恩讲授《逻辑哲学论》、艾耶尔传播、1970 年前后终结）
14. ★ Encyclopaedia Britannica: A.J. Ayer — https://www.britannica.com/biography/A-J-Ayer （生卒、1933 维也纳旁听、可证实性原则表述、情感主义）
15. Rudolf Carnap, Philosophical Foundations of Physics 选章 ch.23–26（Marxists Internet Archive） — https://www.marxists.org/reference/subject/philosophy/works/ge/carnap.htm （观察/理论词项连续谱、对应规则、拉姆塞句，佐证移美后的转变）

未打开成功而未引用的 URL（404/403/空壳/截断）明细见第 4 节表格。
