# F04 心灵哲学（field）— 复核记录

- 状态：ready-for-review
- 复核日期：2026-10-04（首次编写与当日二次复核同日完成）
- 复核人：zcode 研究员（内容研究自检，非独立同行评审）

## 一、边界决定

1. **不等同于心理学 / 精神分析**：契约任务明确要求此划界。overview 第二段与 conclusion 落实为具体表述——心理学是研究记忆、注意、情绪如何实际运作的经验科学；精神分析是关于无意识动机的临床解释传统；心灵哲学追问心智「是什么」与心理/物理描述如何挂钩。此划界为编辑综述（SEP 无 umbrella 式「Philosophy of Mind」条目，/entries/mind/ 返回 404），已在 evidenceLimits 与 evidence.json 中标注。
2. **与站内「现象学」条目的边界**：意向性概念的胡塞尔/布伦塔诺源流按任务要求写入 proposal.relations（师承 + 《逻辑研究》修正，S2/S10 支持，"who was both the founder of phenomenology and a student of Brentano's" 经逐字核读），只作互链接口，不重复展开现象学内容。
3. **佛教心识论**：只作教义层面的平行陈述（S9：Vaibhāṣika "all types of consciousness are intentional"、《三十颂》"threefold transformation of consciousness"、阿赖耶识 "the basis or support of that which is cognizable"、§3.5 意向性专节 / §7.3 反身意识与意向性专节，均逐字核读），明确「不主张历史影响或师承」。与布伦塔诺/胡塞尔的直接比较研究（Lusthaus、Coseru 等）仅检索见题、未逐页核读，故不写入正文，见 evidenceLimits。
4. **与人工智能哲学条目的分工**：本包保留论证的哲学结构（中文屋原论证、图灵测试的功能主义 §2.2 脉络），技术—伦理向度归人工智能哲学条目（proposal.relatedEntries）。
5. **图灵**：站内有人（艾伦·图灵），但 1950 年论文未单独核读，故时间线不设图灵测试节点，人也不入 thinkers（8 人上限内优先直接塑造学科论证的人物）。

## 二、主要分歧（按证据呈现，不裁断）

- 物理主义主流 vs 查默斯自然主义二元论 vs 丹尼特对难问题直觉基础的拒斥：三者并存于 S1/S7，conclusion 以「僵持本身是学科现状」表述；丹尼特一方的表述已按 S1 实际内容收敛为「拒斥感受质传统直觉（intrinsic/private/ineffable, 1990）」，不断言其否认难问题存在。
- 塞尔 vs 丹尼特（「直觉泵」之争）：S5（"Daniel Dennett in his original 1980 response to Searle's argument called it 'an intuition pump'"，逐字核读）+ S1（丹尼特 1990/1991 反感受质刻画）。
- 功能主义与其反驳（倒转感受质、中国国民、僵尸、知识论证、因果排除—金在权 1989/1998）：S3 §5，全部逐字核读。
- 注意区分：布洛克的「Chinese nation」≠ 塞尔的「Chinese room」，S3 与 S5 分述，词条与 subSchools 均未混用。
- 查默斯与笛卡尔的关系为编辑比较（type=编辑比较）：SEP Functionalism 记僵尸论证衍自第六沉思论证、SEP Dualism 记可分离性论证源自第五沉思，两条目沉思序号著录不同，packet 关系条目分别照录，不作调和。

## 三、查重

- 任务 evidence 字段：exactTopLevelEntries / exactBranches / relatedBranches 均为空 → 无同名条目、无既有分支结构，属 mentions-only 新建。
- mentionFiles 七处提及相关：太平洋原住民哲学、凯尔特哲学、罗马哲学、北欧哲学、实在论（字样提及）；分析哲学、人工智能哲学（实质相关条目）。处理方式见 proposal.relatedExistingEntries。
- 未发现站内已有「心灵哲学」schools/data 条目或 philosopher 词条（grep philosophers.json：心灵哲学主题人物部分在站、部分不在，见 evidence.json 最后一条）。

## 四、复核结果（本轮重启后的二次全文复核）

上一轮会话因平台限流中断；本轮重启后对全部交付文件重新核验，方法为：curl 抓取全部 11 个来源页面全文 + python 逐字字符串匹配（verbatim 短引文逐一命中核验）。

**逐字复核修正项（本次实际改动）**：

1. **BBS 1980 评论者名单**：原稿称 27 人「含丹尼特、普特南、丘奇兰德夫妇、查默斯等」——页面只证实 27 位评论者存在，且正文仅点名证实丹尼特（"his original 1980 response"）与福多（"In his original 1980 reply to Searle…"）为 1980 年评论者；丘奇兰德夫妇的 "Could a Machine Think?" 为 1990 年《科学美国人》文章。已相应改写 S5 coverage、timeline/7、works/5、evidenceLimits[6]。
2. **僵尸论证措辞**：原稿引作「源自笛卡尔（descended from Descartes）」，实际 SEP Functionalism §5.5.2 作 "derives from Descartes's well-known argument in the Sixth Meditation (1641)"；SEP Dualism §4.2 则记 disembodiment 论证 "originating in Descartes (Meditation V)"。已照录两式。
3. **Churchland 引文**：原稿 evidence 引作 "eliminativism: P.S. Churchland 1983, Dennett"（页面无此句），实际为 "…merit elimination and replacement…(P. S. Churchland 1983)" 与 "…such as qualia (Dennett 1990…"。已改写。
4. **玛丽论证引文**：实际为 "Frank Jackson's (1982) hypothetical Mary, the super color scientist…"，原稿转写不精确，已改。
5. **Huxley 系年引文**：实际为 "Such worries have been raised…(Huxley 1874, Jackson 1982, Chalmers 1996)"，原稿引文格式不实，已改。
6. **Putnam 自我怀疑引文**：实际为 "(But see Putnam 1988, for subsequent doubts about machine functionalism…)"，原稿 "Putnam later had doubts" 为转述，已改。
7. **副现象论措辞**：原稿 cihai 引「causal idle」，页面实际作 "lack causal status"，已改。
8. **结论措辞**：丹尼特一方由「认为难问题是错误直觉的产物」收敛为「拒斥支撑难问题的感受质传统直觉」，与 S1 实际内容对齐。
9. **其他 verbatim 校正**：Elisabeth 通信（"begins at her initiative in 1643"）、雪佛兰例词序（"in a Chevrolet and a flood of tears"）、disembodiment（originating 而非 originates）、IEP 布伦塔诺参考文献（1874/1911/1973）。

**核读中发现的来源自身笔误（备查，不改来源）**：SEP Dualism 页面把伊丽莎白生卒误作 "(1596–1552)"；本包采用 SEP Elisabeth 条目的准确生卒（1618-12-26 生、1680-02-08 卒）。

**复核通过项**：布伦塔诺两句原书引文、查默斯三句原文（含期刊行 JCS 2(3):200-19）、中文屋核心句 "Syntax is not by itself sufficient for, nor constitutive of, semantics."、Searle (1932–2025)、27 评论者句、赖尔「棺材钉」句与 Mind 主编 1947–1971、笛卡尔 (1596–1650) 与第五沉思、Swinburne (1986)/Eccles (1980; 1987)/Popper & Eccles (1977)、同一论三篇奠基文献句、Armstrong "Central State Materialism"、印度佛教条目三处关键句与三个节题、Elisabeth 条目 heaviness 回应句（"appeals to the Scholastic notion of heaviness…"、response "not only evasive"）、SEP Consciousness §5.4 难问题句、传统感受质刻画句、多重草稿句、§2.1 Nagel 判据句、图灵 §2.2 正文句。

- **来源**：11 个 URL 全部实际抓取全文（本轮 curl；上一轮 WebFetch，两轮均实际读取）；Britannica「philosophy of mind」返回反爬拦截页、IEP「/phil-mind/」返回 404、SEP「/entries/mind/」返回 404，均未收录且已记入 evidenceLimits。
- **人名**：philosophers.json 键名逐一核对（737 键）：8 位 thinker 中 7 位在站（勒内·笛卡尔、弗朗茨·布伦塔诺、吉尔伯特·赖尔、希拉里·普特南、约翰·塞尔、丹尼尔·丹尼特、托马斯·内格尔）；「大卫·查默斯」「查尔莫斯」零命中，按通行译名写入并已标注；「戴维·刘易斯-威廉斯」系考古学家，与哲学家 D. Lewis 无关，未混淆。
- **书籍**：books.json 核对 88b56fb4da52（《第一哲学沉思集》，epub，21章）、f6af30aab723（《笛卡尔的错误》，21章）两条建议，均为可读书非 TXT 占位；《方法论·情志论》（49c80096b16d）存在但内容构成未核实，故不建议。
- **JSON 校验**：packet.json、evidence.json 均通过 `python3 -m json.tool`；evidence.json 53 条 locator 全部含逐字核读的短引文（含 2 条本地文件断言的原文摘录）。
- **质量线**：来源 11 个（≥3，且 SEP/IEP/作者原页三类，互不转抄）；学说范围与人物归属有多个来源支持；原典/论证有查默斯 1995 作者页面（primary-text）与中文屋论证结构支持。术语 9、时间线 10、著述 8、人物 8，均在 6—10 / 4—8 参考区间内。

## 五、仍缺证据 / 已声明限度（详见 packet.evidenceLimits）

- 布伦塔诺、普特南、内格尔、丹尼特、查默斯生卒年取通行参考数据（笛卡尔 1596–1650、赖尔 1947–1971 主编与生卒、塞尔 1932–2025、伊丽莎白 1618–1680 经页面核实）。
- 《第一哲学沉思集》1641 系年、杰克逊 1982 论文题名、普特南 1967 论文题名、丹尼特 1991 书名、《有意识的心灵》书名、图灵 1950 论文题名等项的处理方式逐条见 evidenceLimits（原则：内容经核实者收，题名/年份未经核实者不著录或加注）。
- 「机器中的幽灵」不标原书页码（核读页面未给逐字原文）；塞尔引语以 paraphrase 标注（未核对 1980 原刊）；布伦塔诺引语经 SEP 逐字引述可作 quote；查默斯引语系作者页面直引。
- 印度佛教心识论与现象学/心灵哲学的比较研究仅检索见题，未逐页核读，正文不作比较断言。

## 六、实际核读 URL 清单（2026-10-04 访问；本轮 curl 抓全文并逐字核验）

1. https://plato.stanford.edu/entries/consciousness/ — 意识三问、Nagel/Chalmers/Jackson、理论谱系
2. https://plato.stanford.edu/entries/intentionality/ — 布伦塔诺论题与原文引述、胡塞尔修正
3. https://plato.stanford.edu/entries/functionalism/ — 定义、普特南归属、反驳清单
4. https://plato.stanford.edu/entries/dualism/ — 二元论类型、笛卡尔论证路径、伊丽莎白质疑
5. https://plato.stanford.edu/entries/chinese-room/ — 塞尔 1980、论证结构、回应与评论者
6. https://plato.stanford.edu/entries/ryle/ — 赖尔生平、《心的概念》、范畴错误
7. https://consc.net/papers/facing.html — 查默斯 1995 全文（易/难问题、Nagel 引用、期刊行）
8. https://plato.stanford.edu/entries/mind-identity/ — Place 1956 / Smart 1959 / Kripke 1980
9. https://plato.stanford.edu/entries/mind-indian-buddhism/ — 阿毘昙、瑜伽行派、意向性与反身意识专节
10. https://iep.utm.edu/intentio/ — aboutness、布伦塔诺/胡塞尔
11. https://plato.stanford.edu/entries/elisabeth-bohemia/ — 1643 通信、交互难题、heaviness 回应

未能核读（已记入 evidenceLimits）：https://www.britannica.com/topic/philosophy-of-mind （反爬拦截页）；https://plato.stanford.edu/entries/mind/ （404）；https://iep.utm.edu/phil-mind/ （404）。
