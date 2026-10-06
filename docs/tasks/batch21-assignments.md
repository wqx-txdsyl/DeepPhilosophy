# 批次21 人物要点（2026-10-03-balanced-21）

通用：先读 `docs/tasks/research-agent-brief.md` 严格照做；工作目录 `/Users/sen/.codex/worktrees/genealogy-atlas/DeepPhilosophy`（git worktree，绝不碰 /Users/sen/DeepPhilosophy）；只写证据记录+草稿两个文件；**wikipedia 不得作为包内正式来源**（可作线索，证据记录里须标 wiki-lead-only）；所有关系候选先查 `app/public/philosophers.json` 键与既有 `editorial/` 包（315 包），跨包一律同向同语义；**relation 端点必须出现在本包 people[] 里**（站内人 era 用 canonical）；在世人物只写有直接可靠来源的事实。

## 欧洲组（regionCohort「古希腊与欧洲思想」）

1. **弗吉尼亚·伍尔夫**（1882—1941）：思想史定位=「女性主义」列于 canonical school。来源建议：British Library/Wikipedia 线索+学术版（Cambridge UP《A Room of One's Own》出版页）、学术长文。须核：《一间自己的房间》（1929，原题 A Room of One's Own，出自 1928 剑桥两讲）、《三几内亚》（1938）、《达洛维夫人》/《到灯塔去》作为思想载体还是文学著作——书目 kind 从严（小说 kind=authored 但概念归属须指明散文/论说文出处）。关系候选：站内女性主义链（波伏娃/巴特勒）一律 editorial-comparison，无接触不写影响。
2. **卡伦·霍妮**（1885—1952，德/美，精神分析）：来源：IEP/学术传记/出版页。须核：柏林精神分析研究所任职、《我们时代的神经症人格》（1937 英译/1932 起 American Journal of Psychoanalysis 主编）、《自我分析》（1942）、与弗洛伊德路线分歧（女性心理学/子宫嫉妒批评）。关系：弗洛伊德（historical-contact 受训+editorial 分歧，查弗洛伊德包端点；镜像必须同向）。
3. **阿恩·内斯**（Arne Næss，1912—2009，挪威）：SEP 有专条。须核：奥斯陆大学教授任期（1939–1970）、深层生态学论文（1973《The Shallow and the Deep》）、斯宾诺莎研究（《Freedom, Emotion and Self-Subsistence》1975；译斯宾诺莎《伦理学》入挪威语——版本页核实）。关系：斯宾诺莎包（reading，镜像核对）、甘地（editorial-comparison，若键存在）。
4. **冯·赖特**（Georg Henrik von Wright，1916—2003，芬兰）：canonical era 仅「20世纪」，须落为 1916—2003（SEP/MacTutor 核）。须核：剑桥接任维特根斯坦教席（1948–1951）、维特根斯坦遗著三位遗嘱执行人之一、《规范与行动》（1963）道义逻辑。关系：维特根斯坦（historical-contact：师承+遗著执行人；查维特根斯坦包端点，镜像同向）、胡塞尔（键核实，early Freiburg? 无据不写）。
5. **英伽登**（Roman Ingarden，1893—1970，波兰）：SEP 有专条。须核：哥廷根/弗莱堡受教于胡塞尔（1912 起，博士 1918）、《文学的艺术作品》（1931 德文初版）、层次结构理论/未定点。关系：胡塞尔（teacher，镜像核对胡塞尔包）、海德格尔（editorial-comparison 或同门，有据才写）。

## 东亚组（regionCohort「东亚思想」）

1. **禽滑厘**（约前470—前400，墨家二传）：事迹散见《墨子》书内（《备梯》禽滑厘问守、《公孟》等）与《庄子·天下》墨者群像；生卒无早期明文——canonical era「约前470-前400年」为推定口径，须标注推定性质。来源：ctext/维基文库《墨子》原文+《史记》无传说明+孙诒让《墨子间诂》学术信息（可访问版本页）。worksPolicy：其本人无传世著作，no-autographs。关系：墨子（teacher，镜像核对墨子包 people[]/relations）。
2. **河上公**（约西汉初年—东汉？，归名人物）：《老子河上公章句》成书年代有西汉末/东汉两说，河上公其人系传说化归名（葛洪《神仙传》式记载）——identity 预案=corrected/uncertain 如实记录；worksPolicy=no-autographs（归名著作）。须核：《章句》与严遵《老子指归》、王弼本的文本关系学术争论。关系：老子（reading/注释传统，context/editorial-comparison 或 reading，不得写成历史接触）、严遵（键核实）。
3. **善导**（613—681，净土宗）：来源：CBETA 在线大正藏（《观无量寿经疏》《往生礼赞》）、《续高僧传》本传（道宣）、学术净土研究。教义按学术史框架（弥陀净土/称名念佛的本愿归命结构），不写信仰评价、不涉宗教敏感。关系：昙鸾（teacher 链，键核实：昙鸾不在站内则 people[] 站外）、道绰（teacher，键核实）。
4. **王引之**（1766—1834，高邮王氏）：canonical era「1766-1834年」。须核：《经义述闻》《经传释词》（阮元序/刻本信息）、《康熙字典》考证、官至工部尚书。关系：王念孙（teacher——父亲兼业师；王念孙包（批次20 刚上线）已有 王念孙→王引之 条，镜像必须同向同类型同语义）、阮元（键核实）、段玉裁（键核实）。
5. **黄珍奎**（황진규，当代韩国）：著作《哲学如何成为生活的武器》（철학은 어떻게 삶의 무기가 되는가）等，来源=出版社页/韩国学术检索/书评，韩文来源可用（如实记录阅读范围）。在世人物从严。关系：站内无韩国当代锚点则单边诚实记录；与韩炳哲（批次20 包）如并称当代韩国哲学可 editorial-comparison（有据才写）。

## 第三组（regionCohort「南亚、伊斯兰、非洲、拉美与原住民传统」）

1. **格列高利·帕拉马斯**（约1296—1359，拜占庭）：静修论争（1341/1347/1351 会议）与《三重屏障》——按教义论争史框架写（静修派与巴尔拉姆派的论战结构、能-体之分学说史），不写信仰评价。来源：学术拜占庭研究、Internet Medieval Sourcebook 原典、教会史百科（如 OCAB/学术条目）；wikipedia 只作线索。关系：巴尔拉姆（people[] 站外或键核实）、格里高利·帕拉马斯与阿卡基乌斯等按实读。
2. **普莱索（乔治·格弥斯托斯）**（约1355—1452，拜占庭）：SEP 有专条。须核：佛罗伦萨会议（1438–39）与《柏拉图与亚里士多德之差异》讲演、《法律篇》（Laws 手稿焚毁事件学术表述）、贝萨里翁从学、对美第奇学园的影响（费奇诺译柏拉图动因）。关系：柏拉图包（reading）、贝萨里翁（teacher，键核实——贝萨里翁无 editorial 包但为站内 thinker）、亚里士多德（editorial-comparison，其亚里士多德批评）。**注意 canonical 键是「普莱索（乔治·格弥斯托斯）」，文件名照抄。**
3. **扬·帕托契卡**（1907—1977，捷克）：SEP 有专条。须核：弗莱堡/巴黎求学（胡塞尔、海德格尔课）、《三篇论瓦解的手稿》（1975 地下自刊）、宪章七七发言人（1977，SEP 所载史实层面、学术框架，不展开政治叙述，在世已卒无在世问题）。关系：胡塞尔（teacher，镜像核对胡塞尔包）、海德格尔（teacher/reading，镜像核对海德格尔包）、哈维尔（teacher——哈维尔为站内 thinker，键核实 era；镜像核对哈维尔包）。
4. **戴维·刘易斯-威廉斯**（David Lewis-Williams，南非，1934 生？须核）：认知考古学（《洞穴中的心灵》The Mind in the Cave 2002、《Deciphering Ancient Minds》）。来源：Thames & Hudson 作者页、学术书评（Antiquity/Journal）、Wits 大学页。在世从严。关系：站内无锚点则单边；香农/神经神学批评（Lewis-Williams vs 荷尔/海姆之争）按 people[] 站外处理。
5. **马尔科·拉乌尔·梅希亚**（Marco Raúl Mejía，秘鲁？哥伦比亚？——**legacy 国别须核实**，哲学解放运动第二代，与杜塞尔合作编《The Philosophy of Liberation》？）：**身份核验是本批重点之一**（参照批次20 法尔斯·博尔达案例：legacy 阿根廷错误）。来源：杜塞尔著作编者页、CLACSO/Pensamiento Crítico latinoamericano 学术页、期刊论文。在世/卒年核实。关系：古铁雷斯（editorial-comparison 或 reading——古铁雷斯包（批次20）端点逐一核对）、杜塞尔（键核实；无包则 people[] 站外）、弗莱雷（教育学的解放脉络，键核实镜像）。
