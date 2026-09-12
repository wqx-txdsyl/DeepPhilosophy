# -*- coding: utf-8 -*-
"""O8-R2 caseset 冻结生成器（12 类 × 6 题 = 72）。运行一次后 caseset 即冻结,
不得根据运行结果改题。产出 docs/evidence/O8_R2_CASESET.json。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

C = []


def add(cat, q, cap, tools, note="", history=None):
    C.append({
        "case_id": f"O8R2-{len(C)+1:02d}",
        "category": cat,
        "question": q,
        "expected_capability": cap,
        "tool_expectation": {"expected_tools": tools, "note": note},
        **({"history": history} if history else {}),
    })


# ── 01 基础概念解释（概念讲清楚, 不需重度研究）─────────────────────────
G1 = "01_basic_concept"
add(G1, "哲学里的「先验」（a priori）和「后验」（a posteriori）到底怎么区分？请用一两个例子说明。",
    "概念准确、区分清晰、有恰当例子", ["conceptual_map|无工具也可"],
    "基础概念题, 不应触发重度检索")
add(G1, "功利主义的「最大幸福原则」是什么意思？它与「利己主义」的根本区别在哪里？",
    "概念准确, 能区分规范理论层次", ["conceptual_map|无工具也可"], "")
add(G1, "什么是哲学意义上的「决定论」？它和「宿命论」（fatalism）是一回事吗？",
    "概念区分准确（决定论≠宿命论）", ["conceptual_map|无工具也可"], "")
add(G1, "「存在先于本质」这句萨特的名言是什么意思？请通俗解释。",
    "准确通俗解释存在主义核心命题", ["conceptual_map|无工具也可"], "")
add(G1, "认识论里的「基础主义」和「融贯论」各自主张什么？它们争的是什么？",
    "结构化呈现知识证成两阵营", ["conceptual_map|无工具也可"], "")
add(G1, "「他心问题」（problem of other minds）是什么？它为什么被认为难以解决？",
    "问题刻画准确, 能说明认识论困难", ["conceptual_map|无工具也可"], "")

# ── 02 中等哲学分析（单论证重构+评估）───────────────────────────────
G2 = "02_intermediate_analysis"
add(G2, "休谟在《人性论》中提出的「是—应当」（is-ought）问题：他到底论证了什么？这个论证对规范伦理学构成多大威胁？",
    "论证重构准确, 能区分「逻辑禁止」与「动机空缺」两种解读", ["search_books|get_chapter"],
    "《人性论》在库, 期望原典检索支撑")
add(G2, "罗尔斯的「无知之幕」设计如何同时排除功利主义与直觉主义？请重构其论证并给出一个有代表性的批评。",
    "论证重构+批评有据", ["search_scholarship|无工具也可"], "")
add(G2, "普特南的「缸中之脑」论证如何利用语义外在论得出「我不是缸中之脑」的结论？请逐步重构。",
    "自我反驳结构重构准确", ["无工具"], "纯论证分析题")
add(G2, "塞尔「中文屋」论证的目标到底是反驳「图灵测试」还是反驳「强AI」？请分析论证结构及其「理解」概念的歧义。",
    "区分论证目标层次, 指出系统回应等", ["无工具"], "")
add(G2, "内格尔「成为一只蝙蝠是什么感觉」论证了什么？它对物理主义构成的是反驳还是挑战？",
    "区分「反驳」与「不可还原性挑战」", ["无工具"], "")
add(G2, "帕菲特在《理与人》中用「裂变案例」支持人格同一性的「还原论」，这如何动摇「同一性最重要」的信念？",
    "案例-结论推理链完整", ["无工具"], "")

# ── 03 高难原典问题（在库原典细读, 期望真实检索+引用核验）────────────────
G3 = "03_hard_primary"
add(G3, "康德《纯粹理性批判》「先验辩证论」中「先验幻相」（transzendentaler Schein）的结构是什么？它与经验性错误、逻辑错误的关键区别何在？为什么说形而上学冲突不可避免？",
    "原典结构细读准确, 三个层次区分清楚", ["search_books", "get_chapter"],
    "纯粹理性批判在库, 期望章节阅读+引用核验")
add(G3, "亚里士多德《形而上学》Z 卷探讨「本体」（ousia）的四条候选标准（本质、普遍、种、载体），它们各自遇到什么困难？",
    "Z 卷论证脉络准确", ["search_books", "get_chapter"], "形而上学在库")
add(G3, "《庄子·齐物论》「吾丧我」与「天地与我并生，万物与我为一」段落的文本层次如何组织？「丧我」丧的是哪个层面的「我」？",
    "文本细读+不伪造逐字引文", ["search_books", "get_chapter"], "庄子在库")
add(G3, "休谟《人性论》第一卷中「因果信念」的习惯性解释：观察到的恒常联结（constant conjunction）如何经「习惯」产生必然性的「观念」？请按文本顺序重构。",
    "Treatise 因果论证序列准确", ["search_books", "get_chapter"], "人性论在库")
add(G3, "海德格尔《存在与时间》中「在世界之中存在」（In-der-Welt-sein）的建构：「打交道」（Umgang）与「寻视」（Umsicht）如何构成日常照面的优先性？",
    "术语体系内部关系准确", ["search_books", "get_chapter"], "存在与时间在库")
add(G3, "维特根斯坦《逻辑哲学论》的「图像论」如何同时为「可说者」划界并为「不可说者」留位？4.0031 与 7 命题的关系是什么？",
    "编号命题体系理解准确, 引用编号规范", ["search_books|get_chapter"], "逻辑哲学论在库")

# ── 04 哲学家比较 / 论证分析 ────────────────────────────────────────
G4 = "04_comparison_argument"
add(G4, "康德式义务论与功利主义在「能否说谎救人」（如凶手追杀时说谎）上的对立：双方各自的决策程序是什么？这一案例暴露了两种理论各自的什么代价？",
    "对比结构清晰, 代价分析到位", ["无工具|websearch"], "")
add(G4, "柏拉图与亚里士多德灵魂观的关键分歧：灵魂三部分 vs 植物性-动物性-理性三层，这种差异如何导致政治哲学分歧？",
    "学说谱系与推理链准确", ["无工具|websearch"], "")
add(G4, "伊丽莎白公主对笛卡尔身心交互论的质疑是什么？笛卡尔的回答（松果腺说）为何被认为未能解决她的挑战？",
    "历史论辩重构准确", ["search_books", "get_chapter|websearch"], "第一哲学沉思集在库可辅助")
add(G4, "萨特与加缪在「自由」与「荒谬」上的分歧：从《存在与虚无》到《反抗者》论战，两人的根本分歧点在哪里？",
    "思想史论战脉络准确", ["websearch|search_scholarship"], "")
add(G4, "老子的「无为」与庄子的「逍遥」：「无为」偏治理姿态而「逍遥」偏精神境界，这一区分成立吗？请结合文本辨析两者分歧。",
    "概念辨析有文本依据", ["search_books|get_chapter"], "道德经/庄子在库")
add(G4, "分析传统与现象学传统处理「意向性」的不同进路：布伦塔诺-胡塞尔的「意向对象」与语言分析的「内涵性」处理，各自的长短板是什么？",
    "跨传统比较不漫画化", ["search_scholarship|无工具"], "")

# ── 05 错误前提 / 伪引文 / 出处核验（核验纪律重点）────────────────────
G5 = "05_verification"
add(G5, "黑格尔说过「存在即合理」吗？这句话的原文、真实出处和常见误读分别是什么？",
    "指出误译/误读+给出真实出处（《法哲学原理》序言）", ["search_books|websearch|get_scholarly_source"],
    "核验纪律: 不伪造逐字原文")
add(G5, "「康德否认外部世界的存在」——这个常见说法错在哪里？请纠正这一错误前提并解释先验观念论的实际主张。",
    "识别并纠正错误前提, 不迎合", ["无工具|search_books"], "错误前提题")
add(G5, "「知识就是力量」这句话是培根《新工具》里的逐字原文吗？请核实其真实出处。",
    "不伪造精确出处（scientia potentia est 实出自早期《沉思录》; 《新工具》为相关但非逐字表述）", ["websearch|search_books"],
    "伪出处核验题")
add(G5, "尼采「凡杀不死我的，必使我更强大」出自《偶像的黄昏》哪一部分？请核实并说明语境。",
    "定位真实章节（Maxims and Arrows §8）, 引用可核验", ["search_books", "get_chapter"], "偶像的黄昏在库")
add(G5, "「休谟证明了因果性不存在」——请分析这个说法对休谟《人性论》立场的扭曲之处。",
    "纠正误读: 习惯性解释≠否认因果", ["search_books", "get_chapter"], "错误前提题")
add(G5, "「人是万物的尺度」这一命题的原始出处在哪里？普罗泰戈拉的原作还在吗？我们今天从哪里读到它？",
    "诚实说明原作失传、出处系柏拉图《泰阿泰德》转述", ["websearch|search_books|get_scholarly_source"],
    "文献链核验题")

# ── 06 中国哲学（避免已用主题: 嵇康/二程/郭象/王弼/朱陈之辩/墨子）──────────
G6 = "06_chinese_philosophy"
add(G6, "《孟子》「四端说」如何从心性论推出性善论？「孺子入井」案例在论证中承担什么功能？",
    "论证功能分析准确", ["search_books", "get_chapter"], "孟子在库")
add(G6, "《荀子·性恶》「化性起伪」的「伪」字含义及其与礼义起源论的关系：荀子是「性恶论者」还是「无善无恶论者」？",
    "文本训释+论证结构", ["search_books", "get_chapter"], "荀子在库")
add(G6, "《韩非子》「刑名参同」术论如何组织君主-官僚的信息关系？它与「法」论、「势」论的分工是什么？",
    "法家体系三分准确", ["search_books", "get_chapter"], "韩非子在库")
add(G6, "王阳明「知行合一」说的论证结构：「知」与「行」在什么意义上「本一」？「一念发动处便是行」如何被批评为混淆知行？",
    "心学论证重构+批评史意识", ["websearch|search_scholarship"], "传习录不在库, 研究路径合法")
add(G6, "请给出《正蒙》「太虚即气」一条的逐字原文并解释张载的气本论。——若原文不在库，请诚实说明并给出可核验的文献出处。",
    "诚实降级: 不伪造逐字原文", ["search_books", "get_chapter|websearch"],
    "正蒙不在库, 期望干净拒绝或外链核验")
add(G6, "《论语》「克己复礼为仁」章：「克己」训「约束自身」还是「凭自己」？这一训诂分歧如何影响仁论整体理解？",
    "训诂-义理关联意识", ["search_books", "get_chapter"], "论语在库")

# ── 07 印度 / 伊斯兰 / 小众传统（避免: 伊本·西那/西田/宗喀巴/道元/杜塞尔）──────
G7 = "07_non_western"
add(G7, "龙树中观学「二谛论」如何处理「空」与「缘起」的关系？「若不依俗谛，不得第一义」在论证中起什么作用？",
    "中观结构准确", ["websearch|search_scholarship"], "中论不在库")
add(G7, "《薄伽梵歌》中三条解脱之道（业瑜伽/智瑜伽/信瑜伽）如何被组织为一个整体？克里希那对阿周那的两难劝解运用了哪些论证？",
    "文本结构+论证重构", ["websearch|search_scholarship"], "薄伽梵歌不在库")
add(G7, "伊本·赫勒敦《历史绪论》的「asabiyya」（社会凝聚力）理论如何解释文明兴衰周期？它为何被视为社会科学的先声？",
    "小众传统刻画准确", ["websearch|search_scholarship"], "")
add(G7, "佛教量论传统（pramāṇavāda）中法称对「现量」的规定：无分别、自相、己行境三特征如何排除概念化？",
    "佛教知识论精确", ["websearch|search_scholarship"], "")
add(G7, "非洲哲学中 Kwasi Wiredu 对 Akan「共识认识论」的重构：它如何回应「真理是主体间的吗」这一批评？",
    "小众当代传统不漫画化", ["websearch|search_scholarship"], "")
add(G7, "迈蒙尼德《迷途指津》的否定神学：为什么说「对上帝说肯定命题反而更远离真理」？这一立场与亚里士多德主义的关系是什么？",
    "否定神学逻辑清晰", ["websearch|search_scholarship"], "")

# ── 08 跨语言检索（外文术语/原文语言对勘）─────────────────────────────
G8 = "08_cross_lingual"
add(G8, "德语「Aufhebung」在黑格尔辩证法中的三重含义（否定/保存/提升）是什么？中译「扬弃」是否充分？请给出《精神现象学》相关用例。",
    "术语三义+对勘意识", ["search_books", "get_chapter|websearch"], "精神现象学在库")
add(G8, "希腊文「phronēsis」在《尼各马可伦理学》第六卷中与「sophia」「technē」的区别是什么？中译「实践智慧」丢失了什么？",
    "术语对勘+原典定位", ["search_books", "get_chapter"], "尼各马可伦理学在库")
add(G8, "梵文「śūnyatā」汉译为「空」的译解史：从「无」到「空」的译词选择反映了什么理解分歧？",
    "译名史意识", ["websearch|search_scholarship"], "")
add(G8, "拉丁文「cogito, ergo sum」与笛卡尔法文原文「je pense, donc je suis」的差异：拉丁版为何更易被误读为三段论？",
    "语言层次+误读史意识", ["websearch|search_books", "get_chapter"], "方法论在库")
add(G8, "德语「Dasein」的日常语义（「此在/缘在/存在」译名之争）与海德格尔术语化改造：各译名分别凸显什么、丢失什么？",
    "译名光谱分析", ["search_books|websearch"], "存在与时间在库")
add(G8, "希腊文「logos」从赫拉克利特到斯多亚学派的语义漂移：尺度、理性、原则诸义项如何叠加？",
    "语义史脉络清晰", ["websearch|search_scholarship"], "")

# ── 09 学术争议 / 现代研究综述（研究纪律+不 plan-only）──────────────────
G9 = "09_research_survey"
add(G9, "当代自由意志之争的三大阵营（相容论/自由意志论/硬不相容论）各自的代表人物与核心论证是什么？近十年有何新进展？",
    "阵营地图+人物-论证对位", ["search_scholarship", "websearch"], "研究现状题, 防 plan-only")
add(G9, "「意识的难问题」（hard problem of consciousness）提出三十年来的主要回应路线有哪些？还原物理主义的最新辩护策略是什么？",
    "研究综述分层+时效性", ["search_scholarship", "websearch"], "")
add(G9, "「延展心智」（extended mind）论题 1998 年提出后的争论焦点经历了哪些转移？批评者（如 Adams & Aizawa）的「认知标记」论证现状如何？",
    "争论史+文献时效", ["search_scholarship", "websearch"], "")
add(G9, "元伦理学之外，康德式「道德建构主义」（Korsgaard, Street）与实在论的争论现状：Street 的「分布式满足」论证构成多大威胁？",
    "当代论证精确", ["search_scholarship", "websearch"], "")
add(G9, "分析形而上学中「grounding」（奠基）概念的研究现状：Fine 与 Schaffer 的进路分歧是什么？纯逻辑化方案遇到了什么困难？",
    "前沿概念梳理准确", ["search_scholarship", "websearch"], "")
add(G9, "「中国哲学合法性」之争的谱系：从「中国哲学史」学科建立到当代「以中国解释中国」立场，争论的实质分歧是什么？",
    "思想史+当代争论", ["search_scholarship", "websearch"], "")

# ── 10 简单题 SHOULD_NOT_OVERRESEARCH（效率纪律: 过度研究=失败）─────────────
G10 = "10_simple_not_overresearch"
add(G10, "「哲学」（philosophy）这个词的字面含义是什么？", "词源简答, 不应多轮检索", ["无工具"],
    "效率题: TOOL_CALLS 应为 0-1, LLM_CALLS 应低")
add(G10, "笛卡尔生活在哪个世纪？他最广为人知的著作是什么？", "事实简答", ["无工具"], "效率题")
add(G10, "「犬儒学派」（Cynics）这个名字的由来是什么？", "词源+姿态简答", ["无工具"], "效率题")
add(G10, "「美学」（Aesthetics）作为学科名称是谁提出的？", "事实简答（鲍姆嘉通）", ["无工具"], "效率题")
add(G10, "《论语》一共有多少篇？分上下还是不分？", "轻量事实（20 篇）", ["search_books|无工具"],
    "允许 0-1 次轻检索")
add(G10, "「doctor of philosophy」（PhD）这个学位名称为什么叫「哲学」博士？", "词源简答", ["无工具"], "效率题")

# ── 11 深度研究 / 多来源（多轮检索+跨来源整合）───────────────────────────
G11 = "11_deep_research"
add(G11, "亚里士多德「四因说」在当代生物学哲学中的命运：目的论语言的复兴（如 Mayr 的目的性、生物自组织理论）在多大程度上为「形式因/目的因」平反？",
    "跨时代整合+文献支撑", ["search_scholarship", "websearch", "search_books"], "多来源整合题")
add(G11, "现象学「生活世界」（Lebenswelt）概念从胡塞尔《欧洲科学的危机》到舒茨社会现象学的发展：两人对「生活世界」的客观性地位有何分歧？",
    "概念发展史+分歧点", ["search_scholarship", "websearch"], "")
add(G11, "唯识学与现象学比较研究的代表性进路（如『识』与『意向性』对勘）有哪些主要成果与方法论批评？",
    "跨传统文献综述", ["search_scholarship", "websearch"], "")
add(G11, "技术哲学中 Albert Borgmann 的「装置范式」（device paradigm）与 Langdon Winner「人造物的政治性」：两种技术批判的分歧与互补是什么？",
    "双理论重构+比较", ["search_scholarship", "websearch"], "")
add(G11, "二十世纪初数学基础三大学派（逻辑主义/形式主义/直觉主义）的争论如何塑造了当代数学哲学？哥德尔不完备定理对三派各构成什么冲击？",
    "历史-论证整合", ["search_scholarship", "search_books", "websearch"], "")
add(G11, "《爱弥儿》中卢梭的「消极教育」（éducation négative）主张的结构及其与当代儿童教育哲学（如自主性教育观）的对话可能。",
    "原典+当代研究双链", ["search_books", "get_chapter", "search_scholarship"], "爱弥儿在库")

# ── 12 产品交互（多轮/Reader Context/工具模式）────────────────────────────
G12 = "12_product_interaction"
add(G12, "那康德是如何用先验观念论回应休谟的因果怀疑论的？请接着我们刚才的话题展开。",
    "多轮连续性: 正确挂靠首轮「先验」概念", ["search_books", "get_chapter"],
    "多轮题, history 提供首轮",
    history=[{"role": "user", "content": "什么是「先验」（a priori）知识？"},
             {"role": "assistant", "content": "「先验」指独立于特定经验观察即可成立的知识：其证成来自理性自身的形式（如逻辑与数学的构造、范畴的先验条件），而不来自对事实的归纳概括。注意「先验」不等于「先天具备、无需学习」，它讨论的是证成来源而非获得时间。"}])
add(G12, "不对，我问的不是这个——我想知道的是「义务论伦理学」里「义务」概念的来源，不是「责任」的日常用法。请重新回答。",
    "多轮纠错: 识别用户澄清并修正理解", ["无工具"],
    "纠错题, history 模拟误答",
    history=[{"role": "user", "content": "请解释伦理学里「义务」（Pflicht/duty）概念。"},
             {"role": "assistant", "content": "「责任」在日常语言中指个体对其角色或承诺所负担的后果承担，比如职业责任、家庭责任，它强调事后追责与角色期待。"}])
add(G12, "请用苏格拉底式提问的方式（不要直接给我答案，一步一步提问引导我）帮我思考「什么是勇敢」。",
    "交互模式切换: 调用 socratic_tutor 或等价引导式交互", ["socratic_tutor"],
    "期望调用苏格拉底工具或逐轮提问")
add(G12, "请组织一场休谟与康德关于「因果必然性」的短辩论，双方各三轮，最后给出裁判总结。",
    "调用 philosopher_debate 或等价多角色辩论", ["philosopher_debate"], "")
add(G12, "帮我写一篇约 600 字的哲学短文，主题是「习惯是第二自然」，要求有论点、有论证、有例证。",
    "调用 write_essay 或等价写作流程", ["write_essay"], "")
add(G12, "下面这段话出自哪部书？大概在讲什么？请指出它讨论的核心概念：「我们做公正的事情才能成为公正的人，练成勇敢的品格才能成为勇敢的人。」如可行请给出原文所在章节定位。",
    "阅读上下文+原文定位（尼各马可伦理学 II 卷）", ["search_books", "get_chapter"],
    "Reader Context 定位题")

CATS = {
    "01_basic_concept": "基础概念解释",
    "02_intermediate_analysis": "中等哲学分析",
    "03_hard_primary": "高难原典问题",
    "04_comparison_argument": "哲学家比较/论证分析",
    "05_verification": "错误前提/伪引文/出处核验",
    "06_chinese_philosophy": "中国哲学",
    "07_non_western": "印度/伊斯兰/小众传统",
    "08_cross_lingual": "跨语言检索",
    "09_research_survey": "学术争议/现代研究综述",
    "10_simple_not_overresearch": "简单题 SHOULD_NOT_OVERRESEARCH",
    "11_deep_research": "深度研究/多来源问题",
    "12_product_interaction": "产品交互: 多轮/Reader Context/工具模式",
}

manifest = {
    "O8_R2_CASESET": True,
    "version": "O8R2-2026-09-12",
    "frozen_before_run": True,
    "REVIEWED_BASE": "63732e09da98363b15b89e3954f47842c2c6c563",
    "PRODUCTION_MODEL": "deepseek-flash@RP-B",
    "CASE_COUNT": len(C),
    "DESIGN": "12 类 × 6 题 = 72。 froze before run; 不得根据运行结果改题。",
    "categories": CATS,
    "no_reuse_screening": {
        "avoided_prior_themes": [
            "西塞罗/蒙田/帕斯卡/费希特/狄尔泰/奎因/麦金太尔/嵇康/二程/元伦理实在论争论(V12-10)/宗喀巴/道元/杜塞尔/柏拉图会饮(V12-14)",
            "恩培多克勒/塞克斯都/库萨/斯宾诺莎伦理学V/维柯/谢林/戴维森/威廉斯/洪堡/郭象/伊本·西那/西田/斯密引文(V10-14)",
            "霍布斯/莱布尼茨/叔本华/克尔凯郭尔/朱陈之辩/墨子/奥古斯丁忏悔录/安瑟伦/伯林/王弼老子注/理想国洞穴喻(历史候选排除集)",
        ],
        "fresh_theme_check": "全部 72 题主题经与 V3-V12 manifest 及设计说明主题清单人工比对, 零同题、零近似改写",
        "degradation_probe_cases": ["O8R2-34(正蒙不在库→期望诚实降级)", "O8R2-30(传习录不在库→研究路径)"],
        "CASE_CONTENT_UNSEEN_BEFORE_FREEZE": True,
    },
    "cases": C,
}

out = os.path.join(ROOT, "docs/evidence/O8_R2_CASESET.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
# 校验
assert len(C) == 72, len(C)
from collections import Counter
cnt = Counter(c["category"] for c in C)
assert all(v == 6 for v in cnt.values()), cnt
assert len({c["case_id"] for c in C}) == 72
print("CASESET FROZEN:", out)
print("categories:", dict(cnt))
