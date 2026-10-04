# R12 泛非主义思想 — 资料包复核记录（review）

- 日期：2026-10-05（备忘录 2026-10-04，research.md 原样保留）。
- 状态：`ready-for-review`。本包在备忘录 4 个已核来源基础上升级为完整包：sources 复用 4 项并补足 4 项（ Britannica 全文、Gutenberg 原典、history.state.gov、站内核对），全部实际读到的文本才落款。
- 复核方法：2026-10-05 经 web_reader 全文重读 SEP《Africana Philosophy》（补齐上轮截断的后半条目）与 Britannica《Pan-Africanism》；WebFetch 核读 Project Gutenberg #408 原文与 history.state.gov/countries/ghana；python 实查站内 philosophers.json 人名。自检性复核，非独立同行评审。

## 1. 边界（建包即声明）

- **最根本边界：不把非洲或黑人思想整体归入泛非主义。** 泛非主义只是非洲/散居思想史中一个特定的政治思想运动；本包只承载运动本身。
- **与 A01（非洲智者哲学）**：A01 是知识论项目（口述知识的哲学资格），泛非主义是政治思想运动；A01 review.md 边界决定第 2 条书面预留（"不含：泛非主义（其他任务）"），两包互认无重叠。本包不收奥鲁卡智者项目内容。
- **与 school_非洲哲学（field 总览）**：总览是领域地图，本包是其政治思想一支的专门化；建包后总览 overview 泛非主义段落与 cihai 词条建议改为交叉链接。
- **与 school_黑人哲学（散居一线）**：卡迈克尔/黑权属泛非主义 1960—70 年代脉络，由该包承载；本包不将其列为 thinker（外部来源未核），cihai 词条同样建议改交叉链接。
- **不展开**：Négritude（仅识别性对照）、非洲社会主义各方案、埃及中心论、埃塞俄比亚主义内容（仅作竞争命名对照）、乌班图伦理、后殖民理论、当代身份政治运动。
- **类型**：movement（历史政治思想运动综述），不作 field/school（非学科或学说体系）也不作 position（无单一立场内核，只有家族相似的纲领）。SEP 把泛非主义列为"意识形态趋势"而非哲学流派本身；奥鲁卡"民族主义—意识形态哲思"（SEP 承认为非洲哲学一支）是其哲学定位依据。

## 2. 分歧的呈现（均照录，不裁断）

1. **纪年两说**：通行叙述以 1900 伦敦会议为运动起点；Shepperson 与 SEP 以 1919—1945 五次大会为"大写"运动主体（Britannica 折中：1919 是第一次以"大会"为名的正式会议）。时间线 1900 与 1919 双起点并陈，overview 如实交代。
2. **加维归类**：1920 年代作者多视其为运动领袖；Shepperson 论断其属"文化的 pan-Africanism"、1945 年后才"平反"。学派论断非定论，以论争呈现。
3. **1921 大会会址两记**：Shepperson 记伦敦；Britannica 记伦敦、布鲁塞尔、巴黎三站。并陈。
4. **UNIA 全名两写**：SEP Africana 作 United Negro Improvement Association；Britannica 作 Universal Negro Improvement Association。本包从通行名 Universal，差异记录于此。
5. **杜波依斯晚年离美归因**：S1 归因麦卡锡迫害、S2 记恩克鲁玛之邀，两因并录，不作单一归因。
6. **泛非主义与社会主义/共产主义**：加维敌视社会主义，帕德莫尔—恩克鲁玛一线以社会主义为要素；帕德莫尔对加维评价 1931→1956 逆转。各方立场按 Shepperson 的史学记录呈现，政治内容只作学术史证据，不加赞誉或污点。

## 3. 查重与生态位

- 任务 JSON：exactTopLevelEntries / exactBranches / relatedBranches 全空，coverage=mentions-only。
- 站内 6 处提及全为标签/词条级（非洲哲学 4、黑人哲学 2），无一承载运动史与论争；两条 cihai 词条定义偏窄。
- A01 已书面让位；本包为"非洲哲学 + 黑人哲学"两包提供单一可交叉链接的总括节点。
- 与同轮其他候选（R08 共和主义、R09 保守主义等）无内容重叠：本包是本轮唯一非西方政治思想候选。

## 4. 证据限度（packet.evidenceLimits 的摘要与补充）

- 1900 会议精确日期（7 月 23—25 日说）与正式会议名称仅见于未核读检索结果，正文只写"1900/伦敦"。
- OAU 成立精确日期与地点（Addis Ababa 1963-05-25 说）未据一手文本核读，正文只写"1963 年"（Britannica）。
- 生卒年缺口：杜波依斯 1868—1963 已核（S1）；帕德莫尔卒年 1959 已核（S5）；加维卒年 1940/享年 53 已核（S4）而生年系推算；帕德莫尔生年、恩克鲁玛生卒（站内著录 1909—1972）未核。
- 未核读原书：《加维哲学与意见》（编者未核）、帕德莫尔 1931/1956、恩克鲁玛《加纳》1957 均经 Shepperson 转引，works 条目逐一注明；德兰尼 1861 引语为 paraphrase 级。
- 女性作者：S1 已核同代黑人女性思想者（库珀 1892、韦尔斯 1895、特雷尔）及 SEP 自陈女性贡献关注不足；但女性在历届大会中的组织角色无可核来源，不作断言，留待专项补核。
- 卡迈克尔《泛非主义：一种历史》成书年代未核，沿用站内著录。

## 5. 实际核读 URL 清单

**成功（本包来源）**：
1. https://plato.stanford.edu/entries/africana/ — 2026-10-04 抓取（截断）+ 2026-10-05 web_reader 全文
2. https://plato.stanford.edu/entries/dubois/ — 2026-10-04
3. https://iep.utm.edu/dubois/ — 2026-10-04
4. https://www.freedomarchives.org/Documents/Finder/Black%20Liberation%20Disk/Black%20Power!/SugahData/Essays/Shepperson2.S.pdf — 2026-10-04 PDF 全文 13 页（2026-10-05 复试 WebFetch 因 PDF content-type 不支持未果，引文以 2026-10-04 核读记录为准）
5. https://www.britannica.com/topic/Pan-Africanism — 2026-10-05 web_reader 全文（Britannica 直连/WebFetch 403，curl 亦被拦）
6. https://www.gutenberg.org/files/408/408-h/408-h.htm — 2026-10-05
7. https://history.state.gov/countries/ghana — 2026-10-05
8. 站内：app/public/philosophers.json（2026-10-05 实查）；app/public/schools/data/school_非洲哲学.json、school_黑人哲学.json、A01/review.md、任务 JSON（2026-10-04 grep/实查）

**失败记录（不引用其内容）**：
- https://avalon.law.yale.edu/20th_century/oau.asp — 404
- https://en.wikisource.org/wiki/Organisation_of_African_Unity_Charter 、…/Charter_of_the_Organisation_of_African_Unity — 404×2
- https://ulii.org/akn/oaun/act/oau-charter/1963/eng/ — 403
- https://credo.library.umass.edu/search?… — 反爬验证页
- https://www.bbc.com/news/world-africa-13344971 — 404
- Britannica 直连（WebFetch/curl）403；BlackPast、au.int 沿袭 2026-10-04 失败记录
- https://plato.stanford.edu/entries/panafricanism/ — 404（条目不存在）；/entries/pan-africanism/ — 200 占位页（2026-10-04 实测）

## 6. 仍缺证据（后续可补）

- 1900 会议一手文献（会议决议《To the Nations of the World》原件/可靠全文）与精确会期。
- OAU 章程签署日期/地点的一手文本（au.int 条约库或 UNTS）。
- 女性在历届泛非大会中的组织角色（需专门史学文献，如 Adi & Sherwood 一系）。
- 《加维哲学与意见》编者与卷次、帕德莫尔两书与《加纳》1957 的版本著录。
- 加维生年、帕德莫尔生年、恩克鲁玛生卒年的权威核读。
