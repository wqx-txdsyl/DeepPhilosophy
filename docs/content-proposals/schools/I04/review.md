# I04 吠檀多 —— 资料包复核记录

- 任务：`docs/tasks/school-content-gap-tasks-2026-10-04.json` → `I04`（P1-content-packet，coverage=related-branches-only；任务 JSON 的 proposedKind 为 tradition-overview）
- 状态：ready-for-review（reviewedAt 2026-10-04；研究员自查/子代理直研，非独立同行评审）
- 输出：packet.json / evidence.json / review.md / artwork-brief.md 四件；未改动其他任何文件，未做 git 写操作。

## 一、边界决定

1. **吠檀多=注释传统群，不是单一学说**。IEP 总括句（"nominally a school... in reality a label for any hermeneutics"）与维基"多传统各自解释三始"句双源支持本包的呈现方式；timeline 与 overview 按注释竞争（以注立派）而非学说演化来组织。
2. **"梵我一如"严格归属不二论**（SEP 该命题句在不二论名下；限定不二论"差异永不消解"、二元论"永不同一"为其对立表述）。packet 的 cihai、quote 层与 conclusion 均按此边界写。
3. **幻论（māyā）归属不二论而非吠檀多全体**：SEP 记 māyāvādin 为论敌贬称且商羯罗本人少用 māyā；新吠檀多甚至拒绝"世界为幻"（维基引 Gier）。全包未把"世界是幻"写成吠檀多通说。
4. **与姊妹任务的分工（本包核心接口）**：
   - **I03 弥曼差**：'前—后弥曼差'称谓史由 I03 交代，本包只在定位与 cihai"后弥曼差"条承接引用，不重复；另收维基梵经页"Badarayana 是阇弥尼之师"的传统说法作为两包的人物接触线索（不采信为定论）。
   - **U03 不二论吠檀多**：乔荼波陀—商羯罗师承细节、māyā—avidyā—adhyāsa 机制、不二论内部诸阶段与争论，归 U03；本包商羯罗条只立"最早现存完整注释+托名问题+māyāvādin 贬称"的接口层。
   - **I05 二元论吠檀多**：摩陀婆学说本体（五差异、灵魂等级、永恒受诅咒说等）归 I05；本包只立"实在论自称+三注+对两家批评"的接口层。涉及"部分灵魂永恒受诅咒"仅以维基转述层备案，不代述。
   - **限定不二论无对应任务**：罗摩奴阇的总览层（人物、经注、四异议、bhakti）由本包 thinkers/relations/works 承载；是否另立条目由 Codex 决定（已在 proposal.relationSuggestions 建议）。
5. **proposedKind 口径**：任务 JSON 作 tradition-overview，派发指令作 school；本包按指令以 `proposal.kind="school"` 交付，内容仍为传统总览；最终归类由 Codex 定夺。
6. **站内已有"不二论吠檀多"分支**（《印度哲学》条目下）与站内商羯罗页：本包不修改任何既有条目/分支/人物数据；商羯罗条目在 thinkers 中标"站内人物"并核对其 era/school/sources 与本包口径相容（并陈不裁决）；吠檀多总览学案是否与该分支互链由 Codex 接入时决定。

## 二、查重结论

- 任务 JSON：exactTopLevelEntries 与 exactBranches 均空；relatedBranches 仅《印度哲学》→"不二论吠檀多"；mentionFiles 同条目正文提及（'吠檀多/吠檀多哲学/Vedanta'）。python 实查 `app/public/schools/data/school_印度哲学.json` 证实：分支"不二论吠檀多"存在（含"公元788 商羯罗出生"时间线），正文"正统六派"句提及吠檀多。
- 判定：**related-branches-only 成立**。无"吠檀多"同名入口；现有覆盖是一支（不二论）而非吠檀多整体。本包补总览学案、不改既有分支；与 U03（不二论深度）无重复建设风险（分工见上）。

## 三、分歧与证据限度

1. **年代学分歧是本包最大证据面问题**，全部并陈不裁决：
   - 商羯罗：SEP"flourished during the eighth century CE" vs 维基 Vedanta 学派小节"Adi Shankara (9th century)" vs 站内页"约7—8世纪（具体纪年有争议）"（站内 timeline 作 788 生）。
   - 乔荼波陀：SEP 6世纪 vs 维基 7世纪。
   - 《梵经》：最古层前500—前200（最可能约前200）、现存形态约400—450 CE（维基）vs 传承口径"ca. first century BCE"（SEP）。
   - 罗摩奴阇：传统 1017–1137 vs 现代研究约 1077–1157（寿命 120 年 vs 80 年，维基自注质疑）。
   - 摩陀婆：1199–1278 或 1238–1317（维基）。
2. **来源层级**：学术级仅 SEP Śaṅkara 与 IEP Advaita Vedanta 两条（SEP 无 Rāmānuja/Madhva 条目，404 实测）；罗摩奴阇、摩陀婆、《梵经》、Vedanta 总览四页均为维基 reference 级。断言密度已随层级压缩：纯不二论与不可思议不一不异论仅立名目；"部分灵魂永恒受诅咒""化身说"等仅作转述层备案并注明 Mesquita 质疑。
3. **原典层**：GRETIL《梵经》明文本核读了首四经转写与文本存在性，但该文本自带"THE TEXT IS NOT PROOF-READ!"声明——经义一律经学术引述层使用；另记 GRETIL 索引猜测路径（vedsutr.htm）404，真实路径经索引页 #Vedanta 锚点定位。
4. **维韦卡南达**：任务提示"写前核来源"——已核 IEP（18—21 世纪植根不二论的圣者名单）与维基 Vedanta（新吠檀多推广者、经吠檀多协会西传）两处；其专页未核读，故不系具体生卒、不引其著述。
5. **新吠檀多的"统一吠檀多"叙事**：按维基所引 King 的批评（"contra-factual... diversity of traditions"）保持警惕——本包以"传统群"呈现正是对该批评的回应。

## 四、复核方法与结果

1. 7 个来源全部 curl 全文抓取后 python 剥离标签提取正文，逐条以 grep/find 定位 verbatim 句（/tmp/vedanta_research/ 缓存：sep_shankara.txt 85,987 字符、iep_advaita.txt 27,678、wiki_vedanta.txt 164,758、wiki_brahmasutras.txt 78,700、wiki_ramanuja.txt 59,934、wiki_madhva.txt 59,778、gretil_brahmasutra.txt 28,691）。
2. evidence.json 75 条：overview 19、thinkers 6、relations 8、timeline 8、cihai 10、works 8、subSchools 6、引语 5（卷首/三条 quotes/结尾）、readingRoutes 2、coverage/books/站内人物核对 3——locator 均含亲眼核读的 verbatim 短引文（跨条目引用以"/school/..."指针复用，避免转抄失真）；另以脚本对 51 个 verbatim 片段逐一与抓取原文比对，0 失配。
3. 结构契约自检：readingRoutes 与 evidenceLimits 位于 packet.json **顶层**（未嵌进 school，注意 I03 包为嵌套式，本包按硬性指令改为顶层）；relations 8 条的 from/to 端点全部是本包 thinkers 六人（跋达罗衍那/乔荼波陀/商羯罗/罗摩奴阇/摩陀婆/维韦卡南达）；无站内书 ID 伪造（suggestedBookLinks 为空）。
4. 人物核对：philosophers.json（737 人，python 子串匹配）仅"商羯罗"在站内；其余五人均为站外人物并逐条标注。书籍核对：books.json（409 本，python 查 title/author/summary/tags）"吠檀多/奥义书/梵经/薄伽梵歌/Upanishad/Vedanta" 0 命中——建议为空数组。
5. 两个 JSON 经 `python3 -m json.tool` 校验通过；sourceRefs 引用的 S1—S7 在 sources 中唯一且可解析。

## 五、仍缺证据

- 罗摩奴阇与摩陀婆的学术级专文（SEP 无条目；IEP 未检索到专条）——若 Codex 认为需要，可在补强批寻找（如 SEP "Bhakti" 相关条目、大学印度学机构页或 Routledge/Brill 专论书评）。
- 《梵经》经号的分章结构细目（四篇章名与各章 adhikaraṇa 计数）未核读，works/0 未写。
- 伐拉巴（Śuddhādvaita）与柴坦尼亚系（Acintya-bheda-abheda）的学说内容：仅维基 Vedanta 一页名目，未核读专页，不代述。
- 维底罗尼耶（Vidyāraṇya）与维韦卡南达的专页核读；商羯罗"四道院（maṭha）建制"传说未获本次核读来源，未写入。
- 《薄伽梵歌》独立系年、奥义书编纂层年代：未获核读来源，均不系年。

## 六、实际核读 URL 清单（2026-10-04，均 curl 全文+定位）

1. https://plato.stanford.edu/entries/shankara/ （SEP，学术级）
2. https://iep.utm.edu/advaita-vedanta/ （IEP，学术级）
3. https://en.wikipedia.org/wiki/Vedanta
4. https://en.wikipedia.org/wiki/Brahma_Sutras
5. https://en.wikipedia.org/wiki/Ramanuja
6. https://en.wikipedia.org/wiki/Madhvacharya
7. https://gretil.sub.uni-goettingen.de/gretil/corpustei/transformations/plaintext/sa_bAdarAyaNa-brahmasUtra.txt （原典库明文本；经 https://gretil.sub.uni-goettingen.de/gretil.html 索引 #Vedanta 锚点定位）
- 探测后放弃/404 备案：SEP /entries/ramanuja/、/entries/madhva/ → 404 实测；GRETIL /gretil/1_sanskr/6_sastra/3_phil/vedanta/vedsutr.htm → 404（猜测路径）；Britannica 历来反爬拦截（沿用 F02/I02/I03 备案，未尝试）。
