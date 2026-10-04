# I07 顺世论 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I07`（coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查/主会话直研，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **证据结构是本包的方法论核心**：原典佚失、学说经论敌（佛教/正理/耆那）转述——这写进了 overview 首末段、conclusion 与 cihai/9（"论敌转述层"名目）。所有非直接证据均标注转述层（Billington 二手转述、Acharya 1894 转引、Kamal 例示转述）。
2. **名实关系不裁断**：Cārvāka 与 Lokāyata 两名并陈（S2 明载《利论》清单用 Lokāyata 而非 Charvaka）；Bṛhaspati 创立者说按来源原文保留"有争议"限定；relations/0 定为"归属争议"的编辑说明，不写成师承。
3. **不夸大不贬抑**：不写"印度最早唯物论/科学先驱"类无据评价；同样如实呈现其对印度认识论的建构性参与（SEP：归纳批判被转化为可错论——顺世论作为"被系统反驳的对象"参与塑造主流）。
4. **查重**：mentions-only 成立；无同名条目或分支。
5. **与姊妹包分工**：正理侧反驳由 I01 承载、佛教侧由 B04/T01 承载、学案序列与 I02/I03 一致。

## 二、分歧与证据限度（本包证据面最窄，处理从紧）

- 学术级来源仅 SEP 印度认识论条目（顺世论为配角段落）；Charvaka/Ānvīkṣikī 为维基 reference 级。断言密度已压至最低：一切"四大元素""及时行乐颂""伦理学细节"等通行内容因未获可引定位而**不写入**。
- 首批12项经验（引文回查）显示维基转引二手文献（Billington 1997:43、Acharya 1894:2）属"转引层"，已在 works/timeline/evidence 逐处标注；未把二手转述冒充一手来源。
- IEP 两候选 URL 404 实测；Jayarāśi 年代、汉译名目、《利论》成书年、Vidyāraṇya 14世纪定位均未核实、不系年或标注通行口径。

## 三、复核方法与结果

1. 主会话直研：SEP indiaepi + 维基两页 curl 全文 + grep 定位（sep_indiaepi 为同日 T01/I03 已用文件，本包另行提取顺世论段落）。
2. evidence.json 40 条：thinkers 3、relations 3、timeline 6、cihai 10、works 4、引语 4、coverage/books 2，locator 均含 verbatim 引文。
3. 人物：站内无顺世论人物（python 子串查证），thinkers 全部站外标注；books.json 无相关藏书，建议为空。
4. 两个 JSON 经 `python3 -m json.tool` 校验。

## 四、仍缺证据

- 顺世论伦理学/意识/ pleasure 各节细节、《实有坏灭狮子》梵文本（GRETIL 未探测）、现代专书（Chattopadhyaya 1959 等）——均未核读，不写。
- 建议补强批：寻找 Jayarāśi 论书的学术译注与 SEP/Stanford 之外的学术专文以升级 reference 级来源。

## 五、实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/epistemology-india/ （curl 全文，顺世论段落提取）
2. https://en.wikipedia.org/wiki/Charvaka （curl 全文+定位）
3. https://en.wikipedia.org/wiki/Ānvīkṣikī （curl 全文+定位）
- 探测后放弃：IEP /charvaka/、/indian-materialism/ → 404；Wikipedia /Chārvāka/（含长音符）→ 404（正确题名为 Charvaka，已用）。
