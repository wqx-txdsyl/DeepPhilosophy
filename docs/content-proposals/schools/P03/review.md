# P03 一元论（立场资料包）复核记录

- 复核日期：2026-10-04
- 复核人：zcode 内容研究员（自检性复核，非独立同行评审）
- 状态：ready-for-review

## 一、既有草稿处置

开工前 `ls docs/content-proposals/schools/`（2026-10-04 19:10 前后）：目录内已有 A01–U08、P01、P02 等同日包，**无 P03 目录**。本包为全新撰写，不存在旧稿取舍问题，无需逐源重开核实旧稿。

## 二、边界决定（本包最重要的三个决定）

1. **“一”必须分层**。依 SEP《Monism》§1.1–1.2（目标 target × 单位 unit 的相对性），本包明确区分：实体一元论（斯宾诺莎）、性质一元论（含马赫—詹姆斯—罗素的中立一元论）、存在计数一元论（存在一元论 vs 优先一元论；区分归于谢弗 2010）。三层面互相不蕴涵，正文、术语表、evidenceLimits 均强制注层。
2. **不与“腾格里一元论”合并**。已用 python3 解析 `app/public/schools/data/school_蒙古中亚哲学.json`：subSchools[0] 名为“腾格里一元论”，站内描述为“以永恒蓝天腾格里为核心的早期游牧宇宙观”（自然与人共生、部落忠诚伦理）。这是地域宇宙观用法，与形而上学立场家族只有名称重叠。任务 JSON 的 relatedBranches 即指此处；本包在 proposal.relatedExisting 明确“不合并、不互设父子”，理由与限度写入 evidenceLimits 末条（该分支内容未独立核实，不合并基于用法层面不同，非内容真伪判断）。
3. **与 P01/P04 的对照接口**。P01（唯物主义，同日已交付）：接口在实体一元论层面——SEP《Monism》§1.2 把唯物主义列为实体一元论之下的“种”；已核对 P01 packet.json thinkers（德谟克利特、伊壁鸠鲁、霍布斯、马克思、斯马特、普特南、丘奇兰德），与本包 7 人零重叠。P04（二元论，计划中）：接口为 SEP §1.1 的分类（二元论=多元论特例）。两包均只作编辑级导流，不改对方包。

## 三、来源核读记录（sources 全部实际打开读过）

| 来源 | 核读方式与读到的关键段落 |
|---|---|
| S1 SEP “Monism”（plato.stanford.edu/entries/monism/） | WebFetch 全条目摘要式精读：§1.1–1.2 目标/单位分类与五类一元论、§2 存在一元论（blobject、历史归属 controversial）、§3 优先一元论（谢弗出处、正反论证清单、“值得认真重新考虑”结论） |
| S2 SEP “Spinoza”（/entries/spinoza/） | 两次定位抓取：§2.1 命题块与三步证明（E1d3/E1d6/E1p5/E1p11/E1p14/E1p15）、§2.2 平行论（E2p7s）、Deus sive Natura（第四部分序言）、§1 生平（1632—1677、身后刊行） |
| S3 SEP “Neutral Monism”（/entries/neutral-monism/） | §1 定义与五种中立含义、§2.1 马赫（要素、Mach 1905: 9）、§2.2 詹姆斯（纯粹经验、James 1904b: 23、1912 文集）、§2.3 罗素（1918 采纳、1921/1927、1927b: 287、1964 访谈）、§5 新方向 |
| S4 谢弗 “Monism: The Priority of the Whole”（jonathanschaffer.org/monism.pdf） | WebFetch 不支持 PDF，改 curl 下载后以 Read 逐页读：印页 31–35、36–40 全读；卷脚印 Phil Review 119(1), 2010, DOI 10.1215/00318108-2009-025；p.31 monist/pluralist 表述与赫拉克利特题词、p.32 谱系句与脚注1–3（Joyc/Schiller/Russell/Ayer）、p.33 普罗克洛引文、pp.38–40 形式化与 covering/no-overlap 论证 |
| S5 《伦理学》Elwes 译本（Gutenberg #3800） | 全文页定位：Definition III、Definition VI、Prop. XIV、Prop. XV 原文抄录核对；页面在 Part II 处截断，Part IV 序言未直接读到（拉丁短语以 S2 为据） |
| S6 SEP “Parmenides”（/entries/parmenides/） | §1 年代（约前515年生、埃利亚、题名可能非原名、800行存160行）、§2.2–2.3 残篇引文、§3.4–3.5 严格/宽容/模态解读、麦里梭 |
| S7 SEP “Plotinus”（/entries/plotinus/） | §1 生卒（204/270）与波菲利编订、§5 两种活动与流溢、§7 太一超越存在与“彻底一元论但也是生产性的”限定 |

**抓取失败、未列入 sources 的**（供复审参考）：
- Britannica “monism”：WebFetch 403（两次），web_reader 工具 429 限流。词源（通说归于沃尔夫）因此不写，入 evidenceLimits。
- philpapers.org/rec/SCHEMA-3、philarchive.org：403。
- iep.utm.edu/monism/：404（IEP 无此专条，未强凑 IEP 来源）。
- fitelson.org/topics/schaffer.pdf：404；sites.rutgers.edu/jonathan-schaffer/：404；api.semanticscholar.org：429（多次）。
- 以上失败来源一律未引用，相关信息点或删除或入 evidenceLimits。

## 四、站内数据核对

- **姓名**（philosophers.json，dict 键名）：站内精确用名为 巴鲁赫·斯宾诺莎、伯特兰·罗素、马赫、威廉·詹姆斯、巴门尼德、普罗提诺——本包 thinkers 全部按站内用名。站外人物：乔纳森·谢弗（译名编辑拟定）、艾耶尔、普罗克洛、Horgan 与 Potrč、赫拉克利特，均在 review/limits 标注。黑格尔站内用名为“格奥尔格·威廉·弗里德里希·黑格尔”，因证据只有谱系句点名，未设 thinker 条目。
- **藏书**（books.json，409 本）：已核实 ID——32fb0956b9b1《伦理学》、39c09c0f8d09《九章集》、06e70f7483e6《论自然[残篇]》、e11d896c98e9《神学政治学》；723840d7af64《先验唯心论体系》谢林存在，但“绝对同一/优先一元论谱系”的关联未核实，未列入建议。未造任何书 ID。
- **任务 JSON evidence**：exactTopLevelEntries 与 exactBranches 为空；relatedBranches 仅蒙古中亚哲学·腾格里一元论一处（已处置，见上）；mentionFiles 11 处均为提及级，已逐类在 proposal 说明。

## 五、质量标准自查

- 来源 7 个（SEP×5 + 刊发论文×1 + 原典英译×1），互不转抄；≥1 支持学说范围与人物归属（S1/S4/S6/S7），≥1 支持原典/论证（S4/S5）。
- 术语 10（6–10 区间上限）、时间线 10（上限）、著述 8（上限）、人物 7（4–8 区间）。
- 引语 5+quote+closingQuote 全部有英文原文与定位；两处转引（艾耶尔经谢弗脚注、普罗克洛经谢弗 p.33——后者仅入综述表述未立引语）已标注。
- 伪造检查：无页码编造（所标页码均来自本次实读页面）；无生卒年超出来源（马赫、詹姆斯不给年份）；无师承编造（马赫→罗素等标为“学术史谱系，接触细节未核”）。

## 六、仍缺证据 / 移交审读的问题

1. 谢弗论文印页 41–76（量子论证展开与历史附录）未读；如审读需要该部分细节，需补读。
2. “monism”词源（沃尔夫）无来源，待补 Britannica 或学术文献后再决定是否写入。
3. 马赫 1886 原题与 1905 改题关系、詹姆斯 1904 论文篇名，待查书目数据。
4. 印度不二论等非西方一元论：本包刻意未收，建议将来单独立包，勿在本条目凑配额。
5. 站内“腾格里一元论”分支内容的史实核实不在本包范围；其与 P03 的关系句如需写入该分支条目，由该条目 owner 决定。

## 七、实际核读 URL 清单

已核读（列入 sources）：见 packet.json sources 的 7 条 URL。
尝试未成（未引用）：https://www.britannica.com/topic/monism（403×2）；https://philpapers.org/rec/SCHEMA-3（403）；https://philarchive.org/rec/SCHMTPT（403）；https://iep.utm.edu/monism/（404）；https://fitelson.org/topics/schaffer.pdf（404）；https://sites.rutgers.edu/jonathan-schaffer/（404）；https://api.semanticscholar.org/graph/v1/paper/search（429）。另：WebSearch 对 Schaffer 论文给出卷期页码与 DOI 线索（119(1): 31–76; 10.1215/00318108-2009-025），后经 S4 PDF 卷脚直接确认。
