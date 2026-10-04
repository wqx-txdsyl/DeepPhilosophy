# R14 文艺复兴人文主义 — 资料包审读笔记

审读日期：2026-10-05（包与 evidence 当日编写；research.md 为 2026-10-04 备忘录，原样保留）。
性质：编辑自查（非独立同行评审）。

## 一、复核结果

备忘录的 6 个已核来源于 2026-10-05 全部重新实抓、复核相关段落，全部通过，并新增核得：

- **SEP《Desiderius Erasmus》（2025-09-19 修订）已给出确定生年 1469-10-28，引 Goudriaan 2019**；IEP 仍作"1468?"。包内正文从 SEP，分歧写入 evidenceLimits。这是对备忘录证据限度的更新。
- 备忘录遗留的两处"先核实"事项由新增来源补核通过：
  1. **studia humanitatis 五学科清单**（语法、诗学、修辞、历史、道德哲学）——Britannica《Humanism》条目原文给出（"consisting essentially of grammar, poetry, rhetoric, history, and moral philosophy"），此前 SEP 两条只有"古典语言、修辞与文学"式的窄表述；
  2. **humanismus 为 19 世纪德国学者回溯造词、umanisti 至迟 15 世纪末**——Britannica《Humanism》词源部分原文给出。
- Britannica 两条经 WebFetch 返回 403，改用 web_reader 实读全文后引用；引用内容均以实际读到的段落为准。

## 二、实际核读 URL 清单（2026-10-05，全部实抓）

| # | 来源 | URL | 方法 |
|---|------|-----|------|
| S1 | SEP, Lorenzo Valla (rev. 2026-03-06) | https://plato.stanford.edu/entries/lorenzo-valla/ | WebFetch |
| S2 | SEP, Giovanni Pico della Mirandola (rev. 2024-08-21) | https://plato.stanford.edu/entries/pico-della-mirandola/ | WebFetch |
| S3 | SEP, Desiderius Erasmus (rev. 2025-09-19) | https://plato.stanford.edu/entries/erasmus/ | WebFetch |
| S4 | IEP, Desiderius Erasmus (1468?—1536), Eric MacPhail | https://iep.utm.edu/erasmus/ | WebFetch |
| S5 | SEP, Civic Humanism (rev. 2024-01) | https://plato.stanford.edu/entries/humanism-civic/ | WebFetch |
| S6 | Catholic Encyclopedia, Humanism (1910, New Advent) | http://www.newadvent.org/cathen/07538b.htm | WebFetch |
| S7 | Britannica, Petrarch | https://www.britannica.com/biography/Petrarch | WebFetch 403 → web_reader 实读 |
| S8 | Britannica, Humanism | https://www.britannica.com/topic/humanism | WebFetch 403 → web_reader 实读 |

站内核查（当日，python JSON 解析 + 文件名/关键词核查，工作树副本）：

- `app/public/philosopher/data/`：命中 贝萨里翁、马尔西利奥·费奇诺、托马斯·莫尔；**彼特拉克/瓦拉/皮科/伊拉斯谟均无条目**（"素拉·西瓦拉克"为"瓦拉"子串误报，同备忘录所见类型）。`philosophers.json`（dict 结构，键为姓名）解析同样无四家。
- `app/public/schools/data/school_拜占庭哲学.json`：**悬空关系边仍在**——`{from: 贝萨里翁, to: 文艺复兴人文主义, label: 主题比较, type: 主题关联}`；timeline 含 1453（君士坦丁堡陷落）与 1460-1500（遗产西传）两条，conclusion 提及文艺复兴。
- `app/public/schools/data/school_高加索哲学.json`：未重开文件，沿用备忘录 2026-10-04 核读（"文艺复兴人文诗学"子学派，同名异实），已在该条 evidence 的 uncertainty 注明。

## 三、边界（包内/包外）

**覆盖**：studia humanitatis 课程与语文学方法；彼特拉克奠基；公民人文主义（标注史学建构争议）；瓦拉辨伪与圣经校勘、对经院逻辑的语言重构；柏拉图主义复兴（外围支线）；皮科论题之争与标题修正主义；北方/基督教人文主义与伊拉斯谟。

**不覆盖（及理由）**：
- 文艺复兴艺术史通述——非哲学包范围；
- 费奇诺的形而上学细节（柏拉图学园诸说）——归站内既有费奇诺人物条目或将来可能的"文艺复兴柏拉图主义"包；本包只作外围支线挂接；
- 高加索"文艺复兴人文诗学"——区域诗歌—伦理传统，同名异实，不建立关系边；
- 哈莱姆文艺复兴——无关；
- 宗教改革史本体——伊拉斯谟—路德论战仅作运动限度的案例（时间线止于 1557 年标题史节点，不入宗教改革事件）；
- 人文主义→近代科学的传导线索——八个来源均未展开，不作断言（evidenceLimits 明示）。

**与相邻条目的关系**（均写入 packet.proposal）：
- **拜占庭哲学（站内）**：本包上线可落地其悬空关系边；建议同时复核该包"文艺复兴桥梁"词条与"直接催化文艺复兴"的因果措辞；
- **R13 托马斯主义**：经院哲学对照极，张力是本包叙事线之一，内容不重复；
- **R08 共和主义**：公民人文主义是其前史，建议互加关系边；SEP 明言 civic humanism 与 republicanism "常被混淆而必须区分"；
- **费奇诺/贝萨里翁/莫尔（站内人物条目）**：人物挂接与未来关联点。

## 四、分歧及其处理

1. **瓦拉生年**：SEP 约1406 vs CE 1407 → 正文从 SEP，分歧存 evidenceLimits。
2. **伊拉斯谟生年**：SEP 1469-10-28（Goudriaan 2019）vs IEP 1468? → 正文从 SEP；两源同有 MacPhail 参与，独立性有限，已注明。
3. **皮科《论人的尊严》**：SEP（Copenhaver）修正主义立场——标题 1557 年始见、演说未宣讲未发表、"dignitas was not his subject"。包内全部采用修正主义措辞并带版本史（works 条目明写"不得径以《论人的尊严》为皮科自题"），同时注明该解读本身仍是学界争议。
4. **公民人文主义**：SEP 明言"史学建构"；巴伦 1402 年年表有 Seigel/Hankins 等批评与 1402 年前共和先例 → 只作佛罗伦萨一支（subSchools），不作运动定义。
5. **"彼特拉克奠基"**：CE（1910，护教立场）的惯例叙述；本包以 Britannica Petrarch 与 SEP 公民人文主义条目侧面互证，并在 evidenceLimits 标明其为惯例而非定论。CE 仅用于可与 SEP/Britannica 互证的事项（彼特拉克事迹、瓦拉事迹、美第奇赞助、费奇诺卒年）。
6. **费奇诺归类**：站内条目自称"人文主义者"，学术惯例多视为运动外围 → 本包采"外围支线"的保守划法，归为编辑决断事项。

## 五、查重（站内覆盖）

- 站内 schools/data 层面无"文艺复兴人文主义"条目；唯一直接引用即拜占庭包的悬空关系边（2026-10-05 复核仍在）——**新建可同时修复数据完整性缺口**。
- 人物条目层面：费奇诺/贝萨里翁/莫尔已有；彼特拉克/瓦拉/皮科/伊拉斯谟均无——本包 thinkers 七人无一与站内人物条目重名（费奇诺用站内名"马尔西利奥·费奇诺"以对齐）。
- 与同轮候选：R13（托马斯主义，对照极）、R08（共和主义，前史互链）——均为关系边而非内容重叠；R14 目录内仅 research.md/evidence.json（备忘录版）与本轮四件，无他包同题。

## 六、仍缺证据 / 未覆盖（继承+更新）

1. 备忘录的"先核实"事项已全部补核（五学科清单、humanismus 词源）——已关闭。
2. 《阿非利加》完稿情况、彼特拉克抄本发现的完整清单——来源未详，不写。
3. 瓦拉《Livy Emendationes》等次要著作细节——SEP 条目未展开，不写。
4. 萨卢塔蒂与彼特拉克的私人交往（书信）——来源未及，relations 不作师承/接触断言，只设阶段比较边。
5. 人文主义→近代科学（库萨、哥白尼语境）——无来源，不写。
6. "柏拉图学园"的建制成疑——CE（1910）孤证层面仅作关联点（贝萨里翁、普莱索），不作"成立于某年"表述。
7. 站内他条（昆体良、西塞罗、普塞洛斯等）正文级提及未逐条核读——不作覆盖依据；正式建条时如引用站内他条需再核。

## 七、给审读者的提示

- 本包是**运动总述型**：SEP 无通用 humanism 条目（404），叙述为四条 SEP 条目 + 两条 Britannica + CE（仅互证）的多源综合，段落权重见 sources[].coverage。
- 全部时间线节点、书目、术语、人物归属与关系边在 evidence.json 均有 fieldPath 定位；直接引语仅四条（idem esse philosophum...、"译者非先知"、蛋谚、SEP 皮科转述），其中三条标注意译、一条为学术转述，均未冒充哲学家原话。
- 上线后的站内动作清单（非本轮执行）：① 落地拜占庭包悬空边并复核其因果措辞；② 决定费奇诺条目与本包的挂接方式；③ 与 R08/R13 互加关系边；④ 考虑彼特拉克/伊拉斯谟等人物条目的后续立项。
