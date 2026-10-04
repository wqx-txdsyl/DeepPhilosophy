# I05 二元论吠檀多 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I05`（P1-content-packet，coverage=no-match-in-reviewed-school-files，proposedKind=school，cohort=南亚）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查/子代理直研，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **范围严格限定摩陀婆传统**：按任务条目 scopeAndCautions（"限定为摩陀婆传统；与泛称的哲学二元论分开建包"），本包不写数论、不写笛卡尔式二元论；"二元论"一词在站内已有数论义占用（见二），故 packet 副标题与 quote 层以 Tattvavāda（"实在论之声"）为准名，"Dvaita"按来源口径标注为后加名。
2. **毗湿奴神学面向与哲学主张分开呈现**：packet 的 overview 第 5 段明确分层——哲学论证层（两界实在、五别、三量、神恩解脱）与神学/圣传层（Vayu 化身说、奇迹传、圣传传记）与建制层（黑天道场、八僧团/Paryaya、Mathatraya、哈里达萨）。化身说按"自述+四百年批判链"并陈；奇迹传只按维基"is said to have"层备案；subSchools 的三个条目均标 kind=建制/文学，非学说分派。不夸大"科学性"：未使用维基 Sastri 引言中"scientific"字样，Ṭīkācārya 尊号按"复注传统权威"本义呈现。
3. **与 I04（吠檀多总览）的分工**（承接 I04 包已留接口："摩陀婆学说的深度内容归 I05，本包只立总览框架与关系"）：
   - I04 包 thinkers 已有"摩陀婆"接口条（实在论自称+三注+对两家批评+Mesquita 质疑）；本包将其展开为五别/taratamya/三量/三类灵魂/著作清单/两代复注的完整学案。
   - I04 包 timeline 第 5 节点"摩陀婆与二元论建制"由本包 timeline 全链条深化。
   - 两包互不修改对方文件；接入时建议互链（packet.relationSuggestions 第一条）。
4. **与 U03（不二论吠檀多）的分工**：本包商羯罗条目为"批判对象"接口层，只引 IEP 一句定位（"argued that the atman is completely identical with brahman"）与批判行为（vociferously attacked、"伪装佛教"指控、atat tvam asi 重读）；不代述 māyā—avidyā—adhyāsa 机制、不二论内部争论等，均归 U03。
5. **对限定不二论（罗摩奴阇）同样只立接口**：本包未核读罗摩奴阇专页，其立场定位取自 Dvaita 专条的一句概括；总览层内容归 I04 包。
6. **任务提示条目的逐项处置**：
   - "Taratham?"：经核读判定为 **Taratamya**（维基 Madhvacharya Metaphysics 节 verbatim："Madhva calls it Taratamya (gradation in pluralism)"）——已核实写入 cihai 与 overview。
   - "linga/svarupa"：svarūpa 一词在全部缓存文本中 grep 未见；实际核得 **svabhava**（自性，维基 Dvaita 三处 verbatim）与 **liṅga-deha**（细身，"shedding of all coils including the last—the linga deha"）——cihai 第 10 条按此落地，并在 evidenceLimits 备案。
   - "māyāvāda 不可救药"类名言：**梵文原句未核到一手文本**（GRETIL 摩陀婆条目外链、维基无引、Wikiquote 质量低弃用）——按"写前必须核到来源"的硬性要求不写；只写已核实的转述层（"accusing Shankara and the Advaitins of teaching Buddhism under the cover of Vedanta"，维基 Madhvacharya verbatim），并将 Māyāvāda-khaṇḍana（幻论破）的著述落点（经维基 Vyasatirtha 页 Mandara Manjari 节核得）写入 works/3。
   - "哈达瑜伽与摩陀婆传承的关联争议"：**未核到**——Achyuta Preksha 维基页 404、Wikipedia 站内全文检索无果、六来源均无相关陈述。按"有争议就注明；不写不确定内容"原则：写入 evidenceLimits 备案，正文不写，留待补强批。
   - "乌马拉蒂（Jayatirtha）"：任务条目中的"乌马拉蒂"与 Jayatirtha 通行译名不符且查无对应来源——按规范译名"阇耶提尔塔"写入，此处备案。
7. **维基 Madhvacharya 页的僧团表述张力**：导言"1285 建乌迪皮黑天道场"、Monasteries 节"建八僧团"、Career 节"never established a matha dedicated to Dvaita philosophy"三条并存。本包处理：黑天道场（1285）单独立节点；八僧团按"传统追溯至摩陀婆"口径（"established... with his eight disciples as its head"照录）；"never established"句原样引入 relations/6 的 detail 与 evidenceLimits——不强行调和，由 Codex 接入时定夺表述。

## 二、查重结论

- 任务 JSON：exactTopLevelEntries/exactBranches/relatedBranches/excludedLexicalMatches/mentionFiles **全部为空**（no-match-in-reviewed-school-files）。
- python 实查站内唯一相关命中页 `app/public/schools/data/school_印度哲学.json`：**"摩陀婆" 0 命中、"Dvaita/Madhva" 0 命中、"罗摩奴阇" 0 命中**；"二元论" 3 处命中**全部指数论**（"迦毗罗创立，以原初物质与精神原理的二元论解释宇宙演化"等）；"吠檀多"15 处提及均挂在不二论名下（与 I04 查重结论一致）。
- 判定：**no-match 成立，本包为全新学案**。与 U03（不二论深度）、I04（吠檀多总览）无重复建设风险（分工见一.3/一.4）。唯一风险是**"二元论"译名与站内数论用例的词形冲突**——已在 packet.relationSuggestions 建议接入时以全名+Dvaita/Tattvavāda 别名防混（Codex 决定）。

## 三、分歧与证据限度

1. **年代学多系并陈，全部不裁决**：
   - 摩陀婆：1199–1278 或 1238–1317（维基，且正文明言生年不明）；IEP 标题只用 1238—1317。
   - 阇耶提尔塔：约1345–约1388（维基正文）；Dandekar 引文以 1365–1388 为其著述期。
   - 毗耶娑提尔塔：**同一维基页内三说并存**（正文 infobox 1447–1539；页内导航模板 1460–1539；柴坦尼亚传承句 1469–1539）；IEP 另作 "Vyasaraya (1478–1589)"——寿逾百岁显系异常值，录以备考不采用。此为本包年代面最混乱处，已全部写进 packet.thinkers/2 与 evidenceLimits。
   - 商羯罗（接口层）：IEP 摩陀婆条作 9 世纪；站内页作"约7—8世纪"——并陈，与 I04 包口径一致。
2. **来源层级**：学术级为 IEP 摩陀婆专条（Valerie Stoker，Wright State University）与 SEP 印度认识论条目（仅 Vyāsatīrtha 一句）；SEP 无 Madhva/Ramanuja 条目（404 一手实测）；摩陀婆、阇耶提尔塔、毗耶娑提尔塔、Dvaita 专条四页均为维基 reference 级。断言密度已随层级调整：哈里达萨人物（普兰达拉达萨）不作哲学评价；"Carnatic 音乐之父"等通行评价因未见于核读来源而不写。
3. **原典层不可及**：GRETIL 索引有 "Madhva (Anandatirtha): Mahabharatatatparyanirnaya" 与 "Krsnamrtamaharnava" 名目，但条目实为外链（京都服务器）、corpustei 猜测路径 404（4 个变体实测）——摩陀婆经义一律经 IEP/维基引述层，本包无一手梵文核读。这与 I04 包用 GRETIL 核读《梵经》首经的情况不同：摩陀婆文本在 GRETIL 无可直读本。
4. **引文不可考问题按争议并陈**：Appayya Dīkṣita（16世纪）→ Venkatasubbhiah（1933）→ Mesquita（250 页系统研究，"likely composed by Madhva himself"）→ Sharma/Shrisha Rao 反驳（写本旁证）——本包不裁决，化身说、奇迹传、"亲见毗湿奴为权威"自述句全部按圣传层标注。
5. **著作对外限阅之争**（Sarma vs Bartley）：两说照录并陈。
6. **高迪耶毗湿奴系**：学术影响层（Sharma：影响最著处）与师承自称层（维基 "is said to be"）两层层级不同，subSchools 第 4 条分开表述，师承链不作断言。
7. **"王座摄政两年"传说**：维基自标 "According to a legend"——不写入 packet。
8. **恶的问题**：Buchta 批评与 Sharma 辩护两说并陈（conclusion 第一段），不裁决。

## 四、复核方法与结果

1. 6 个来源全部 curl 全文抓取后 python 剥离标签提取正文，逐条以 grep/正则定位 verbatim 句（缓存 /tmp/dvaita_research/：iep_madhva.txt 10,504、wiki_dvaita.txt 33,033、wiki_madhva.txt 62,872、wiki_jayatirtha.txt 22,097、wiki_vyasatirtha.txt 43,307、sep_epistemology_india.txt 106,858 字符；另有 sep_perception_india.txt（核后弃用）、wiki_mayavada/wiki_achyuta（404）、wikiquote_madhva（弃用）、gretil_index.html（1,033,721）备案）。
2. evidence.json 83 条：overview 22、thinkers 10、relations 7、timeline 8、cihai 10、works 8、subSchools 4、引语 5（卷首/三条 quotes/结尾）、conclusion 3、readingRoutes 2、coverage/书籍 2、SEP 404 与 GRETIL/Wikiquote 探测备案 2——locator 均含亲眼核读的 verbatim 短引文（跨条目复用以 "/school/..." 指针）。
3. 结构契约自检：readingRoutes 与 evidenceLimits 位于 packet.json **顶层**；relations 7 条的 from/to 端点全部精确等于本包 thinkers 六人（摩陀婆/阇耶提尔塔/毗耶娑提尔塔/普兰达拉达萨/商羯罗/罗摩奴阇）；无站内书 ID 伪造（suggestedBookLinks 为空数组）；sourceRefs 引用的 S1–S6 在 sources 中唯一且可解析；sources[].accessedAt 全部为 2026-10-04。
4. 人物核对：philosophers.json（737 人，python 子串匹配全部人名键）仅"商羯罗"在站内；摩陀婆/阇耶提尔塔/毗耶娑提尔塔/普兰达拉达萨/罗摩奴阇均站外并逐条标注。书籍核对：books.json（409 本，python 查全字段）相关关键词 0 命中——建议为空数组。
5. 两个 JSON 经 `python3 -m json.tool` 校验通过。
6. **verbatim 机器比对（两轮）**：以脚本把 evidence.json 与 packet.json 全部单引号包裹的英文片段（经 Unicode NFC、引号/破折号归一、维基引用标记与注记标记剥离、标点空格归一、省略号分段）逐一与抓取原文比对。首轮发现并修正 10 处：evidence 侧 4 处（IEP 'Madhva argues' 误写作 argued、'a' 在 IEP 原文带单引号而引文脱漏、两处引号嵌套导致的边界问题）；packet 正文侧 6 处（对不二论指控句误将 Shankara 写作 Śaṅkara、Sharma 内层引语边界、'(monastery)' 脱落、两处省略号截断越界、GRETIL 名目加引号）。末轮结果：**evidence.json 125 片段 0 失配；packet.json 正文 82 片段 0 失配；卷首引语/三条 quotes/结尾引语 5 字段 0 失配**。仅两处维基页面排版伪影（"philosopher -saint"、"Viṣṇaveva \"," 引号内侧空格）按归一化规则处理。

## 五、仍缺证据

- 摩陀婆原典的任何一手文本核读（GRETIL 不可及；若 Codex 需要可试 JSTOR/Brill 专论或 dvaita.net 社区文本库——后者为本传社区站，type 须标 community/repository，本批未采用）。
- "māyāvāda 不可救药/伪装佛教"名言的梵文原句及出处（传称《Visnu-tattva-vinirnaya》，本批不可及）。
- 哈达瑜伽与摩陀婆传承的关联争议（如确有，疑似见纸质文献，本批不可及）。
- 维基 Dvaita 专条五别编号次序与 IEP 略异（两版照录未调和）；摩陀婆三十七部著作的分册年代（全部不系年）。
- "Taratamya" 作为独立术语在维基 Madhvacharya 页的用法（"calls it Taratamya"）与其在传统文献中作为灵魂等级专名（神—梵天—…序列）的细节：后者未见于核读来源，本包未写序列细节。
- 维耶沙提尔塔（毗耶娑提尔塔）三说生卒的史学裁定（涉及 Vyasayogicharita 与铭文研究，超出本批范围）。

## 六、实际核读 URL 清单（2026-10-04，均 curl 全文+定位）

1. https://iep.utm.edu/madhva/ （IEP，学术级，作者 Valerie Stoker/Wright State University）
2. https://en.wikipedia.org/wiki/Dvaita_Vedanta （维基 reference 级）
3. https://en.wikipedia.org/wiki/Madhvacharya （维基 reference 级）
4. https://en.wikipedia.org/wiki/Jayatirtha （维基 reference 级）
5. https://en.wikipedia.org/wiki/Vyasatirtha （维基 reference 级，Good Article）
6. https://plato.stanford.edu/entries/epistemology-india/ （SEP，学术级；仅用 9.2 节 Vyāsatīrtha 一句）
- 核读后弃用：https://plato.stanford.edu/entries/perception-india/ （无 Dvaita 实质内容）；https://en.wikiquote.org/wiki/Madhvacharya （页含乱码如 'school of medicine'，弃用）。
- 探测后放弃/404 备案：SEP /entries/madhva/、/entries/ramanuja/ → 404（一手实测）；https://en.wikipedia.org/wiki/Achyuta_Preksha → 404；https://en.wikipedia.org/wiki/Mayavada → 404；GRETIL corpustei 摩陀婆路径 4 个变体 → 404（索引条目为外链京都服务器）；Wikipedia 站内搜索 "Achyutapreksha"、"Hatha yoga Madhva" → 0 结果。Britannica 历来反爬拦截（沿用 I04 批备案，未尝试）。
