# W01 柏拉图主义 — review.md（2026-10-04）

## 1. 任务与目录处置

- 任务取自 `docs/tasks/school-content-gap-tasks-2026-10-04.json` 的 `W01`（tradition-overview，P1，coverage=related-branches-only）。
- 开工前 `ls docs/content-proposals/schools/W01/`：**目录不存在，无同日旧草稿**，本次为全新写作，无"保留/重写"处置需要。
- 仅在 `docs/content-proposals/schools/W01/` 下创建四个契约文件；未改动其他任何文件；无任何 git 写操作；主仓库 `/Users/sen/DeepPhilosophy` 未触碰。

## 2. 边界决定（scope 与排除）

| 决定 | 说明 |
|---|---|
| 本包范围 | 柏拉图型相论 → 古代学园谱系（老学园/学园怀疑论/新学园/第四·第五学园）→ 中期柏拉图主义（约前1世纪—公元3世纪），止于普罗提诺接口 |
| 新柏拉图主义 | **不复制为本包**。站内已有 `school_新柏拉图主义.json`（含雅典/亚历山大里亚分支）；正文仅保留一个接口时间线节点（努梅尼乌斯—普罗提诺，IEP 明言中期柏拉图主义"终于普罗提诺"、普罗提诺被指"剽窃努梅尼乌斯"），关系建议走 proposal 互链 |
| 现代数学柏拉图主义 | 仅按 SEP 'Platonism in the Philosophy of Mathematics' 作定义与哥德尔关联提示；**不展开**，建议由次轮备忘录提议的数学哲学任务（R04）承载 |
| 犹太/凯尔特/拜占庭相关分支 | 站内既有（犹太柏拉图主义、凯尔特新柏拉图主义、晚期拜占庭柏拉图主义等）一律**互链不代述**，路径照任务 evidence 字段登记于 proposal.relatedExistingEntries。站内"斐洛"（school=犹太教-柏拉图主义）因此不收为本包 thinker |
| "学园于 529 年被查士丁尼关闭" | **未写入**——本次核实的 10 个来源均未出现此说，不做无据陈述 |

## 3. 查重

- `grep -l '"柏拉图主义"' app/public/schools/data/*.json` → 无命中；目录中唯一含"柏拉图"的条目文件为 `school_新柏拉图主义.json`。**"柏拉图主义"顶层条目确为缺口**，与任务文件 `exactTopLevelEntries: []` 一致。
- 站内 `philosophers.json` 中普鲁塔克的 `school` 字段已写"中期柏拉图主义"——本包建成后该指向有了承接条目。

## 4. 来源核实记录（全部实开实读，2026-10-04）

| id | URL | 结果 |
|---|---|---|
| S1 | plato.stanford.edu/entries/plato/ | 已读：型相论核心表述（§1—2）、第七信间接性（§5）、生年 429?—347 |
| S2 | plato.stanford.edu/entries/arcesilaus/ | 已读：前315/4—241/40、前268/7 接任、epochê peri pantôn、实践标准 |
| S3 | plato.stanford.edu/entries/carneades/ | 已读：前214—129/8、"New or Third Academy"、to pithanon、前155 使团（各环节存疑） |
| S4 | plato.stanford.edu/entries/antiochus-ascalon/ | 已读：约前130—69/8、与斐洛决裂（前79前）、老学园复兴、PH 1.220 第四/五学园、西塞罗前79受教 |
| S5 | plato.stanford.edu/entries/speusippus/ | 已读：约前410、波托涅之子、前348/347 继任八年、拒型相论、一与多、佚著 |
| S6 | iep.utm.edu/midplato/ | 已读：时段界定（安提奥库斯—普罗提诺）、未成文学说、系统化、三元阶、努梅尼乌斯→普罗提诺 |
| S7 | plato.stanford.edu/entries/plutarch/ | 已读：约45/47—119后、《蒂迈欧》字面读法两原理、学园统一佚著、反斯多亚 |
| S8 | classics.mit.edu/Plato/republic.7.vi.html | 已读：太阳喻与 509b 段 Jowett 原文（页面无斯特凡页码，位置按通行编号核定） |
| S9 | plato.stanford.edu/entries/platonism-mathematics/ | 已读：三论题定义、哥德尔仅涉 1944、弗雷格论证——仅作关联提示 |
| S10 | iep.utm.edu/plato/ | 已读：阿卡德穆斯圣林建校（无年份）、生卒 428/7—348/7、对话分类 |

失败尝试（未引用）：
- `plato.stanford.edu/entries/middleplatonism/` → **404**（SEP 无此条目），改用 IEP 'Middle Platonism'。
- `britannica.com/topic/Platonism` → **403**（反爬），弃用 Britannica。
- `scaife.perseus.org`（《理想国》希腊原文 509b）→ 页面 JS 渲染、无正文内容；改用 MIT Classics 英译核对引语。**Perseus 希腊原文未核成**，已在 evidenceLimits 声明。
- `perseus.tufts.edu` 1999.01.0057 → 实为亚里士多德《政治学》，非《理想国》，弃用。

来源独立性：SEP 各条为不同作者独立条目，IEP 为独立百科，MIT Classics 为 Jowett 英译原典——无互相转抄。类型构成：学术百科 8 + 原典 1（另 S10 学术百科），满足"≥1 学说范围/人物归属 + ≥1 原典/论证"。

## 5. 人名核对（站内 vs 站外）

- **站内（以站内写法为准）**：柏拉图（约前428/427—前348/347）、普鲁塔克（约46—约119）、西塞罗（前106—前43）。
- **站外新增（philosophers.json 无，已如实标注"站外人物"）**：斯彪西波、克塞诺克拉底、波勒蒙、阿尔克西劳、卡尔涅阿德斯、克莱托马库斯、拉里萨的斐洛、安提奥库斯、欧多鲁斯、特拉绪罗斯、阿尔基努斯/阿尔比努斯、努梅尼乌斯、普罗提诺（站内另有其人条目但属新柏拉图主义，不在本包 thinkers）。
- 译名从学术通行中译（斯彪西波=Speusippus、阿尔克西劳=Arcesilaus、卡尔涅阿德斯=Carneades、安提奥库斯=Antiochus），站内无既有写法可循。

## 6. 分歧与存疑处理

1. **未成文学说（agrapha dogmata）**：亚里士多德报告+第七信 vs 只认对话文本的争论，两说并陈于 cihai/overview/conclusion，不裁决；"图宾根学派"命名未单独核实，正文只以描述性语言提及（见 evidence.json 对 /school/cihai/9 的 uncertainty）。
2. **阿尔基努斯 vs 阿尔比努斯**：IEP 页以 Albinus 称《教本》作者（fl. 149–157），通行研究多区分二人；本包用"阿尔基努斯"通名并在 evidenceLimits 标注归属之争。
3. **卡尔涅阿德斯双日演讲**：SEP 明言故事每个环节皆有疑问；按"传统叙事+存疑"书写。
4. **学园分期计数**：老/中/新学园及第四、第五学园的计数是后世编纂学惯例（塞克斯都 PH 1.220 记载计数不一），subSchools 各条已声明。
5. **建园年份**：核实来源（IEP）未给年份，时间线用"约前4世纪80年代"证据范围，未写"前387"。
6. **西塞罗《学园》成书年（前45年）**：通行断代，非本次来源明文，evidence.json 已挂 uncertainty。

## 7. 质量标准自查

- 术语 10（6—10 满额）、时间线 8、著述 8、人物 8、分支 5、关系 10：均在标准区间。
- 引语仅 1 条（509b），经 Jowett 英译核对后转译，标 `paraphrase`；无冒名引语。
- 时间线无伪造年代；不确定处均用区间/约数并在 evidenceLimits 说明。
- packet.json / evidence.json 均以 `python3 -m json.tool` 校验通过。
- 自检性质：本人逐源核读+双重 JSON 校验，**非独立同行评审**。

## 8. 仍缺证据 / 交审读注意

- 《理想国》509b 希腊原文（epekeina tēs ousias）未在原文页面核对（Scaife 未渲染）——如需希腊文引用，审读时可补 Perseus/Shorey 校验。
- "老学园"下限（前268/7）取自 S2 的克勒斯卒年，为合理衔接而非古代分期原文。
- 欧多鲁斯、特拉绪罗斯仅见于 IEP 一源（§3—4），未支撑独立人物卡，只进时间线聚合节点。
- 安提奥库斯佚著（Canonica、Sosus）仅存目；works 未单列，避免凑数。
- 建议后续任务（不属本包）：R04 数学柏拉图主义内容包；本包与新柏拉图主义条目的互链落地需路由负责人（Codex）定夺。

## 9. 结构修正处置（2026-10-04，审读反馈后）

- 首版误将 readingRoutes / evidenceLimits 放在 `/school/` 下，且 routes 字段不符合契约格式；已按反馈重构：两者移至 packet.json **顶层**，readingRoutes 改为 `{title,path,order,note,sourceRefs}` 两条（作品顺序 / 问题顺序，sourceRefs 均指向已核实 sources id），evidenceLimits 扩为 14 条数组（并入 review.md 第 8 节的实质项：老学园下限推断、欧多鲁斯/特拉绪罗斯单源、《学园》成书年断代、"图宾根学派"标签未核实）。evidence.json 的 fieldPath 均不受影响（原无指向这两键的条目），重构后已重跑解析校验。

## 10. 实际核读 URL 清单（2026-10-04）

以下 10 个 URL 在研究期内逐个真实打开并读到相关段落，全部进入 sources：

1. Stanford Encyclopedia of Philosophy: Plato — https://plato.stanford.edu/entries/plato/
2. Stanford Encyclopedia of Philosophy: Arcesilaus — https://plato.stanford.edu/entries/arcesilaus/
3. Stanford Encyclopedia of Philosophy: Carneades — https://plato.stanford.edu/entries/carneades/
4. Stanford Encyclopedia of Philosophy: Antiochus of Ascalon — https://plato.stanford.edu/entries/antiochus-ascalon/
5. Stanford Encyclopedia of Philosophy: Speusippus — https://plato.stanford.edu/entries/speusippus/
6. Internet Encyclopedia of Philosophy: Middle Platonism — https://iep.utm.edu/midplato/
7. Stanford Encyclopedia of Philosophy: Plutarch — https://plato.stanford.edu/entries/plutarch/
8. Plato, Republic, Book VI (tr. Jowett), MIT Internet Classics Archive — https://classics.mit.edu/Plato/republic.7.vi.html
9. Stanford Encyclopedia of Philosophy: Platonism in the Philosophy of Mathematics — https://plato.stanford.edu/entries/platonism-mathematics/
10. Internet Encyclopedia of Philosophy: Plato — https://iep.utm.edu/plato/

尝试但未采用（不在 sources）：plato.stanford.edu/entries/middleplatonism/（404）、britannica.com/topic/Platonism（403）、scaife.perseus.org 理想国 509b（JS 渲染无正文）、perseus.tufts.edu text 1999.01.0057（实为亚里士多德《政治学》）。
