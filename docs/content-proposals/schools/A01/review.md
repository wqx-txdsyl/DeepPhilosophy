# A01 非洲智者哲学 — 复核记录（review）

- 日期：2026-10-04
- 状态：ready-for-review
- 研究员：zcode（本包为资料包交付，未经独立同行评审；reviewMethod 见 packet.json）

## 1. 边界决定

1. **总览—专门分工**：站内已有 `school_非洲哲学.json`（把智者哲学列为四大流派之一，并已引用 SEP 同名条目）与 `school_后殖民哲学.json`（正文一句提及）。本条目只做奥鲁卡项目与受访智者的专门化呈现；民族哲学（坦佩尔斯一系）仅作对照靶标，不做完整展开，避免与总览条目重复。
2. **不含**：泛非主义（其他任务）、埃及哲学、柏柏尔哲学——与本条目无重叠。
3. **呈现口述与访谈的限度**：所有智者言论标注“经 SEP 转引、中译为转述”；观察者效应、翻译不确定性、Oruka 自认的项目过渡性均写入 overview/conclusion，不做无据拔高。
4. **受访智者的主体性**：阿科科、昌戈、巴拉萨作为思想者呈现（各有可引用的论证），并在 works 中收录阿科科本人的著作（Luo Kitgi gi Timbegi），避免把智者写成单纯的“资料来源”。
5. **奥戈特梅利与 onisegun 定位为对照案例**：按奥鲁卡自己的分类（民间智者）呈现，明确标注“编辑比较/批评性分类”，不与智者构成师承或影响关系。

## 2. 查重结果

- `school_非洲哲学.json`：overview 提及奥鲁卡、works 已有《智者哲学》条目、cihai 已有“智者哲学”词条、quotes 已有一条 Oruka paraphrase。措辞与本包不冲突；若主控同时采用，建议总览条目的相应词条改为指向本条目的交叉链接。
- `school_后殖民哲学.json`：仅一句提及，无需改动。
- `philosophers.json`（键名核对）：无奥鲁卡、阿科科、昌戈、巴拉萨、沙班·宾·罗伯特、奥戈特梅利、博敦林条目——**本包人物除“普拉西德·坦佩尔斯”（站内已有精确名）外均为站外人物**。另有“维雷杜·维雷杜”条目疑为夸西·维雷杜（Kwasi Wiredu）的异常键名（站内总览条目正文用“夸西·维雷杜”），与本包相关，供主控知悉。

## 3. 分歧与批评的呈现

- 博敦林（能力≠系统反思；观察者效应）、范胡克（十二位智者的“未受现代影响”设定不成立）、蒯因式翻译不确定性、普雷斯比（“谁算智者”的性别/年龄偏见；奥鲁卡样本12人中仅1位女性、1位年轻人）——均据 S1/S2 如实呈现，并保留奥鲁卡自己的回应（思想先于书写；访谈是“原材料”）。
- 奥鲁卡的自评矛盾（项目“起于对欧洲人断言的反动”、又自视为未来哲学的“基础”）按 S2 呈现，不调和。

## 4. 证据限度（与 packet.json evidenceLimits 一致的要点）

- 四趋势论文（《第欧根尼》1983）的卷期页码未核实，不给。
- 生卒精确日期、1980年建系、肯尼亚哲学协会等传记细节仅维基（带维护横幅）支持；死因未写。
- 阿科科/昌戈/巴拉萨/沙班/奥戈特梅利/坦佩尔斯的个人生卒年未核实，不给。
- 奥廷加访谈成书书名与年份、哈伦—索迪波项目年份未核实，不给。
- “philosophia sagax”拉丁形式未核实，未使用。
- 沙班两书中文书名（基萨迪基卡、乌图博拉·姆库利马）为音译，语义描述以 SEP 的内容概述为准。

## 5. 实际核读 URL 清单（2026-10-04）

成功打开并通读相关段落：
1. https://plato.stanford.edu/entries/african-sage/ （WebFetch 摘要 + curl 全文提取，含参考文献页）
2. https://www.bu.edu/wcp/Papers/Afri/AfriPres.htm （curl 全文：Presbey 1998 论文）
3. https://archive.org/metadata/sagephilosophyin0000unse （curl：书目记录，Brill 1990, ISBN 9004092838）
4. https://api.crossref.org/works/10.1163/9789004452268 （curl：BRILL 1990 注册记录）及 https://api.crossref.org/works?query.bibliographic=… （章节“Philosophic Sagacity in African Philosophy” pp.41–51）
5. https://en.wikipedia.org/api/rest_v1/page/html/Henry_Odera_Oruka （curl 全文；对应 https://en.wikipedia.org/wiki/Henry_Odera_Oruka）

尝试后失败/排除（未计入 sources）：
- https://brill.com/display/book/9789004452268/front-1.pdf — 403
- https://www.britannica.com/topic/African-philosophy — 403
- https://iep.utm.edu/african-philosophy/ — 实为重定向到“拟撰条目”（desired articles）清单，非正式文章；https://iep.utm.edu/sage-philosophy/ 、/odera-oruka/ 、/oruka/ 、/ethnophilosophy/ — 404
- https://plato.stanford.edu/entries/african-philosophy/ 、/entries/africana-philosophy/ — 404（SEP 无此 slug）
- https://journals.sagepub.com/doi/10.1177/039219218303112203 （奥鲁卡四趋势论文疑为 Diogenes 1983）— 连接失败，故该文卷期未写入正文
- https://philpapers.org/browse/henry-odera-oruka — category not found
- https://archive.org/metadata/sagephilosophyin0000oruk — 空记录（误识 ID），改用 sagephilosophyin0000unse
- WebSearch 全程 429 限流，未采信任何搜索摘要

## 6. 仍缺证据 / 建议

- 若可访问 JSTOR/Brill 全文，可补：范胡克 1995 与卡伦巴 2004 的正文核读（本包仅给书目与转述）、Oruka 1983 Diogenes 四趋势论文的出处确认。
- 受访智者生卒年、奥廷加访谈书名、哈伦—索迪波年份：需《智者哲学》原书或 Graness & Kresse 1997 纸本方可补齐。
- 主控可采用本包（status=ready-for-review）；书籍关联维持为空（books.json 409 种中无相关书籍）。
