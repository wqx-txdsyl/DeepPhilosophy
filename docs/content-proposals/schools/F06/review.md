# F06 美学 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `F06`（proposedKind=field，P1-content-packet，coverage=mentions-only）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md，共四个文件；未改动其他任何文件，未做任何 git 写操作。

## 一、边界决定

1. **学科史 ≠ 思想史**。"aesthetica"作为学科名是18世纪的发明：SEP（S2）确认鲍姆嘉通 1735 年已使用该词、康德第三批判后流行；对美的反思（柏拉图对话、亚里士多德《诗学》、《庄子》《论语》）则早得多。overview 首段与时间线节点"约1735"均显式区分两者。
2. **不把美学缩为欧洲艺术史**。时间线以争论与文献节点组织（柏拉图对话 →《诗学》→ 1712 艾迪生 → 约1735 鲍姆嘉通 → 1757 休谟 → 1790 康德 → 1835 黑格尔讲演录 → 1934 杜威 → 1964 迪基 → 1970 阿多诺）；跨传统内容只收"有据者"：《庄子·知北游》与《论语·泰伯》两处原典（维基文库逐字核读），并标注为**编辑比较**（relations/4 的 type 即"编辑比较"）。日本物哀、阿兹特克"花与歌"因无可核读来源而**未写入**（见"仍缺证据"），建议由站内《日本哲学》《阿兹特克哲学》专门条目承载。
3. **与站内既有条目的边界**。任务 evidence 的 exactTopLevelEntries / exactBranches 均为空 → 无同名条目，无查重冲突；mentionFiles 21 项列为 proposal.relatedExistingEntries。抽查 `app/public/schools/data/school_道家.json`、`school_德国古典哲学.json` 均含"美学"2 处，mentions-only 判断成立。本条目只做领域总览，不代述道家属美学、法兰克福学派美学等专题细节。
4. **人物姓名**。thinkers 全部用 grep `app/public/philosophers.json` 核得的站内精确姓名与纪年：柏拉图（约前428/427—前348/347）、亚里士多德、大卫·休谟、伊曼努尔·康德、格奥尔格·威廉·弗里德里希·黑格尔、庄子（约前4世纪）、约翰·杜威、西奥多·阿多诺。鲍姆嘉通、迈尔、霍托、贝尔、迪基、丹托、韦茨、古德曼、艾迪生、博克、哈奇森等站内无条目者只出现在时间线/词条/分支中，不设 thinker 条目。
5. **书籍关联**。仅建议已核实存在于 `app/public/books.json` 的 9 个 ID（见 evidence.json 末条）。阿多诺《美学理论》正文主张以 SEP 为据，不依赖站内书籍内容；《文心雕龙》仅作关联建议、内容未核实（evidenceLimits 有声明）。

## 二、分歧与争议的处理

- **美的客观性/主观性**：S1 称之为"这个领域被反复审理得最多的分歧"，且记载20世纪"美"的退场与1980年代（尤其女性主义哲学）的回潮——conclusion 据此写"未裁决"，不站队。
- **康德对两大传统的综合**（S3）：按条目原文写"既基于情感又要求普遍有效"为其最独特之处。
- **黑格尔"艺术终结"**：S5 原文即带保留——"his own thesis of the end of art (or what has been taken to be that thesis)"。本包全文对该命题一律用"（或通常被当作该命题的主张）"式表述，conclusion 末段明示解释之争。
- **阿多诺自律论**：按 S7 写成"必要而又虚幻的自律"、艺术是"社会的社会对立面"（1970[1997,8]），不引申。
- **净化（katharsis）**：只写 Bywater 译注层面的"purification or purgation"，不裁决疏泄/澄清之争（evidence.json cihai/8 uncertainty 字段注明）。
- **杜威—康德关系**（relations/5）：S6 只直接支持"反对把审美限于美术"，对康德的直接批评未核实——detail 内已自注"编辑概括"，uncertainty 字段同步。

## 三、查重与既有内容

- 无同名顶级条目、无同名分支（任务 JSON 两个 exact 数组为空）。
- mentions-only：21 个文件（道家、魏晋玄学、阿兹特克哲学、日本哲学、唯心主义、浪漫主义、德国古典哲学、功利主义、生命哲学、北欧哲学、东欧斯拉夫哲学、黑人哲学、实用主义、现象学、过程哲学、西方马克思主义、法兰克福学派、批判理论、哲学诠释学、环境哲学、哲学入词）。
- 旧正文未作依据来源：本包引语全部重新核读（庄子、孔子章句、康德 §2、贝尔、迪基等均回到原文页面），未继承任何未核实引语。

## 四、复核方法与结果

1. sources 全部于 2026-10-04 实际打开并读到相关段落（清单见下节）；WebSearch 片段一律不作为依据。
2. 每个关键断言在 evidence.json 有 JSON Pointer 对位条目（时间线 10、词条 10、著述 8、人物 8、关系 6、引语 4、书籍关联 1、coverageGap 1）。
3. 数量：术语 10、时间线 10、著述 8、人物 8、分支 8、关系 6，均在契约标准区间。
4. 两个 JSON 以 `python3 -m json.tool` 校验通过（见会话记录）。

## 五、仍缺证据（与 packet.json evidenceLimits 对应）

- 鲍姆嘉通《Aesthetica》成书年份（1750/1758）——来源只支持"1735 已用词"。
- 丹托（1964）、韦茨（1956）、布洛（1912）等年份——S8 只给出迪基 1964。
- 博克《崇高与美》出版年份。
- 《诗学》成书年代（仅作"公元前4世纪"）。
- 黑格尔"象征型—古典型—浪漫型"三形态术语未逐字核对，正文不展开。
- 汉语"美学"译名史（西周等）未核实，不写。
- 物哀、阿兹特克"花与歌"：来源不可核读（见下），未入正文。
- 席勒仅作为黑格尔自述影响者出现（S5），不设 thinker。

## 六、实际核读 URL 清单（2026-10-04）

已核读并采为 sources：

1. https://plato.stanford.edu/entries/beauty/ （S1，curl 全文 + 关键段摘读）
2. https://plato.stanford.edu/entries/aesthetic-concept/ （S2，同上；Baumgarten 1735 段逐字）
3. https://plato.stanford.edu/entries/kant-aesthetics/ （S3，同上；两大传统段逐字）
4. https://plato.stanford.edu/entries/aesthetic-judgment/ （S4，导言读毕，用于审美判断词条与结论）
5. https://plato.stanford.edu/entries/hegel-aesthetics/ （S5，导言/出版史/end of art 段逐字）
6. https://plato.stanford.edu/entries/dewey-aesthetics/ （S6，Art as Experience 与 an experience 段逐字）
7. https://plato.stanford.edu/entries/adorno/ （S7，第6节 Aesthetic Theory 逐字）
8. https://iep.utm.edu/aesthet/ （S8，WebFetch 通读 + curl 原文逐字核对 1712/1757/Bell/Dickie 1964）
9. https://www.gutenberg.org/ebooks/48433 （S9 元数据页）+ 全文 https://www.gutenberg.org/cache/epub/48433/pg48433.txt （1790 段、§2、free play、purposiveness、崇高目录、天才目录逐字）
10. https://www.gutenberg.org/ebooks/6763 （S12 元数据页）+ 全文 https://www.gutenberg.org/cache/epub/6763/pg6763.txt （katharsis 译注、imitation、Bywater）
11. https://zh.wikisource.org/wiki/%E8%8E%8A%E5%AD%90/%E7%9F%A5%E5%8C%97%E9%81%8A （S10，"天地有大美"句逐字）
12. https://zh.wikisource.org/wiki/%E8%AB%96%E8%AA%9E/%E6%B3%B0%E4%BC%AF%E7%AC%AC%E5%85%AB （S11，经 MediaWiki API extract 逐字核得"興於詩，立於禮，成於樂"）

尝试后放弃（不可核读，未列入 sources）：

- https://plato.stanford.edu/entries/aesthetics/ → 确认 404（SEP 无"美学"总条目，改用上述分条目）。
- https://www.britannica.com/topic/aesthetics 与 /topic/mono-no-aware → Cloudflare JS 挑战（curl 仅得"Just a moment..."），弃用。
- https://ctext.org/zhuangzi/knowledge-wandered-north/zhs → 反爬声明页；api.ctext.org 需认证，弃用（改维基文库）。
- https://iep.utm.edu/japanese-aesthetics/ 、https://iep.utm.edu/baumgarten/ → 404，弃用。
- https://plato.stanford.edu/entries/judgment-aesthetic/ 、/entries/aztec-philosophy/ → 404（正确 slug 已改用 aesthetic-judgment；阿兹特克条目未获得，不写）。
