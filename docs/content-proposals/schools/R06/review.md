# R06 社会认识论——完整资料包审读记录

研究日期：2026-10-04。本文件由 R06 研究备忘录（research.md，同日，原样保留）升级而来：备忘录记录候选定位与初轮核读；本包（packet.json / evidence.json / review.md / artwork-brief.md）为其完整化。工作树：/Users/sen/.zcode/worktrees/zcode-school-content。

## 1. 边界决定

- **类型**：`field-branch`（领域之下的分支条目）。建议作为 F01《认识论》之下的分支挂载，路由归属由 Codex 决断（任务 JSON routingAndParentDecisionOwner=Codex）。分工：F01 管领域骨架，本条管社会维度四块问题域（证言、分歧、群体/制度、认识不义）的深化；F01 原"社会认识论"与"女性主义认识论与认识不义研究"两个 subSchools 摘要保留为门户级概述并加"参见"。依据：F01 review.md 第 2 条自我定位（"只做领域骨架"）+ F01 对"无政府主义认识论"的先例（子领域单独成条、父领域做门户）。
- **应覆盖**：定义与"社会转向"（含 1660 皇家学会背景、1987/2004 两条期刊制度线、富勒—戈德曼两条进路之别）；证言（休谟—里德轴及 Coady/Burge/Fricker 1994 当代前线）；同侪分歧（EWV 及反方、深层分歧）；群体信念与群体证成（四方案+三方案）；集体意向性交界（只在吉尔伯特处）；制度与信用经济（Merton/Kitcher/Strevens、系统取向、民主三模型、专家识别）；形式进路一节（判断聚合、孔多塞定理、网络、多样性）；认识不义专节（两类不义+扩展谱系+相邻论题）。
- **不应覆盖**（写入包内 conclusion 与 evidenceLimits）：女性主义认识论整体史与性别科学批判细节；集体意向性的社会本体论细节（塞尔、图奥梅拉一系，属心灵哲学）；印度量论 śabda 与弥曼差声量证言传统（可比性未核，不作任何跨传统断言、不设关系）；费耶阿本德"认识论无政府主义"（属科学哲学，按任务 JSON 既定口径）；知识社会学史（曼海姆等）——富勒进路与之相邻，仅按 SEP 条目作最简交代。
- **学科史与问题史分轨**：1987 年创刊是学科制度节点，问题史起点（休谟 1748 / 里德 1764）早近一个半世纪；timeline 与 conclusion 均按此分轨表述，不把 1987 写成问题起点。

## 2. 分歧与争议的处理

- **富勒 vs 戈德曼两条纲领**：SEP 注明 Collin (2013) 专文对勘；该文未核读，包内只转述其存在与两条期刊线的事实，不转述其论点（relations/2、evidenceLimits/2）。
- **群体信念四方案是活争论**：Quinton 加总论、吉尔伯特共同承诺、Wray"群体接受"批评、Bird 分布式、Lackey 群体行动者并陈，不预设裁决；各原文未核读，一律按 SEP 条目转述。
- **同侪分歧**：EWV 与 Kelly/Lackey 两线并陈；"分歧证据是否对象层证据"写为分水岭而非定论。
- **优先权规则与多样性结果的批评**（Higginson & Munafo 2016、Romero 2017；Thompson 2014、Singer 2019）：写入 conclusion 作为"形式进路内部的反噬"，只表述批评存在，不代述论证。
- **认识不义译名**：epistemic injustice 有"认识不义/认识不公/认知不义"诸译（任务标题用"认识不公"、F01 包用"认识不义"）；本包以"认识不义"为主，cihai 词条注明异译。testimony 译"证言"，注明有"见证"之译。
- **政治—伦理敏感材料**（白人无知、煤气灯效应、性骚扰例证等）：一律按已核来源（IEP、SEP §5）转述其学术表述，不加赞誉或污点性评价。

## 3. 查重

- **任务 JSON（S9，本包直接核对）**：exactTopLevelEntries、exactBranches、relatedBranches 均为空——站内无同名顶级条目、无同名分支；mentionFiles 仅贝叶斯主义、实用主义两父页。
- **两处提及均为正文级顺带提及（S10、S11，本包直接抽取原句核对）**：贝叶斯主义页"贝叶斯认识论与形式认识论、社会认识论融合，研究群体信念聚合和网络传播中的理性问题"；实用主义页"为后来的建构主义和社会认识论提供了先声"。均不构成领域入口，不构成并入障碍。
- **F01 包（S7、S8）**：已有骨架级覆盖——两个 subSchools 摘要（各两三句）、timeline 1987/2007 两节点；thinkers 无戈德曼、富勒、弗里克、吉尔伯特；群体认识与知识制度两块完全缺席，形式社会认识论与认识不义扩展谱系亦无覆盖。本包承接四块问题域，F01 子项降为门户摘要+参见，两包不重复维护细节。
- **F01 review.md 第 3 条先例**："无政府主义认识论"由《科学哲学》承载、从本领域入口参见——子领域单独成条、父领域做门户是既有分工方式，本包建议与之一致。

## 4. 复核结果

- **外部来源 6 个，全部于 2026-10-04 由本包研究员实际核读**（WebFetch 定向抽取原句；休谟原典经 curl 取 373KB 全文后本地 python 逐字抽取第十节）：
  1. SEP "Social Epistemology"（三轮定向抽取：定义/学科史/证言/分歧；群体/证成/制度/专家；形式进路/应用各节）；
  2. IEP "Epistemic Injustice"（两轮：定义/两类不义/例证/扩展/权力；书目行——书名副题 Epistemic Injustice: Power and The Ethics of Knowing 与牛津出版社经此补足，F01 包当年未核得）；
  3. SEP "Collective Intentionality"（塞尔 1990 完整书目、吉尔伯特 2006: 134/145 原句、定向义务句）；
  4. SEP "Thomas Reid"（1764 书名、生卒 1710—1796；该条目明确声明不展开证言论题——里德立场因此只系于 SEP 社会认识论条目转述）；
  5. SEP "David Hume"（1748 出版史、初名/改名、生卒 1711—1776、"Hume's Maxim"）；
  6. Project Gutenberg #9662《人类理解研究》（1777 身后定本，Selby-Bigge 1902 第二版）：第十节 "OF MIRACLES"（Part I/II）、"A wise man, therefore, proportions his belief to the evidence."、§91 神迹格言逐字核得。
- **本地来源 5 个**：F01 packet.json、F01 review.md、任务 JSON（R06 条目 evidence 字段）、school_贝叶斯主义.json 与 school_实用主义.json（两处"社会认识论"唯一出现处原句直接抽取）。
- **站内核对**：philosophers.json 关键词检索——站内在册：柏拉图、大卫·休谟、托马斯·里德、孔多塞、约翰·塞尔；消歧：玛格丽特·富勒（超验主义者）≠史蒂夫·富勒、吉尔伯特·赖尔≠玛格丽特·吉尔伯特；戈德曼/弗里克/玛格丽特·吉尔伯特/史蒂夫·富勒/基彻不在站内人物库，用通行译名。books.json 检索：站内休谟著作为《人性论》（178e7d06d42d）、《自然宗教对话录》（9c9e77918c07），无《人类理解研究》单行本——suggestedBookIds 按此如实建议。
- **校验**：packet.json 与 evidence.json 均通过 python3 -m json.tool。evidence.json 共 71 条，以 JSON Pointer 对位 packet.json（脚本核验全部 fieldPath 可解析；timeline 10 节点、cihai 10 词条、works 7 部、thinkers 7 人、relations 5 条、quotes 4 条、subSchools 6 项、proposal 关键主张、readingRoutes、closingQuote 及 evidenceLimits 关键条目均有对位记录）。规模区间全部达标：术语 10、时间线 10、著述 7、人物 7。
- **承继说明**：SEP "Epistemic Injustice" 专条当日 "Not Yet Available" 一事承同日备忘录核读记录，本次未重复访问该页，包内只在 conclusion 与 evidenceLimits 如实标注；其余全部断言为本包独立核读（非转抄备忘录，两处 school JSON 与任务 JSON 为本包直接核对）。

## 5. 仍缺证据（全部写入 evidenceLimits）

1. SEP "Epistemic Injustice" 专条未上线——上线后复核原句与谱系。
2. 戈德曼 1999 专著书名未在核读来源逐字出现（只写"1999 年的专著"）。
3. Collin (2013)、Quinton 1976、Wray 2001、Bird 2014/2022、Lackey 2010/2016/2021、Schmitt 1994、Goldman 2001/2010/2014、Anderson 2006/2012、Kitcher 1990（期刊出处亦未核）、Strevens 2003、Merton 1968、Hong & Page 2004、Kornhauser & Sager 1986、Bikhchandani et al. 1992、Fogelin 1985、Kelly 2005/2010、Christensen 2007、Elga 2007、Feldman 2006/2007、Coady 1990、Fricker 1994、Medina 2011、Dotson 2012、Pohlhaus 2012、Mills 2007、Nguyen 2020、Searle 1990、Gilbert 2006/2009、List & Pettit 2011——均未核读原文，全部按 SEP/IEP 条目转述表述。
4. 里德 1764 年原书未核读；里德是否逐句针对休谟文本不作断言。
5. 印度量论 śabda、弥曼差声量与当代证言之争的可比性无任何一手来源，包内零断言。
6. 生卒年缺失：戈德曼、弗里克、吉尔伯特（玛格丽特）、富勒（史蒂夫）、基彻五人均不在核读来源内，thinkers.era 以"活跃期"表述并注明。
7. 孔多塞 1785 年定理表述按 SEP 转述，原书未核。
8. 汉语译名史（"认识论/证言/认识不义"）未核实，全文只注明异译存在，不写译名源流。

## 6. 实际核读 URL 清单（2026-10-04）

1. https://plato.stanford.edu/entries/epistemology-social/ （SEP Social Epistemology，WebFetch 三轮）
2. https://iep.utm.edu/epistemic-injustice/ （IEP Epistemic Injustice，WebFetch 两轮）
3. https://plato.stanford.edu/entries/collective-intentionality/ （SEP Collective Intentionality）
4. https://plato.stanford.edu/entries/reid/ （SEP Thomas Reid）
5. https://plato.stanford.edu/entries/hume/ （SEP David Hume）
6. https://www.gutenberg.org/cache/epub/9662/pg9662.txt （休谟《人类理解研究》，curl 全文 373KB，本地抽取第十节逐字核对）
7. file:docs/content-proposals/schools/F01/packet.json （F01 已交付包）
8. file:docs/content-proposals/schools/F01/review.md （F01 审读记录）
9. file:docs/tasks/school-content-gap-tasks-2026-10-04.json （R06 任务条目）
10. file:app/public/schools/data/school_贝叶斯主义.json （提及处原句抽取）
11. file:app/public/schools/data/school_实用主义.json （提及处原句抽取）

（辅以 python3 对 app/public/philosophers.json、app/public/books.json 的关键词检索，用于站内姓名与书目核对；两者不作为断言来源，仅作消歧与在库确认。）

## 7. 结论

R06 由备忘录升级为完整资料包：packet.json（kind=field-branch，overview 5 段、conclusion 3 段、thinkers 7、relations 5、timeline 10、cihai 10、works 7、subSchools 6、quotes 4、readingRoutes 2、evidenceLimits 13）+ evidence.json（44 条对位）+ 本审读记录 + artwork-brief.md。状态 ready-for-review。三个术语 6—10、时间线 6—10、著述 4—8、人物 4—8 的规模区间全部达标；无编造引语（4 条引语均逐字核得英文原句、中译标注为本包转写）；跨传统与生卒年等无据之处全部落入 evidenceLimits。
