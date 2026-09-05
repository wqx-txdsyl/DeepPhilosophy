# -*- coding: utf-8 -*-
"""O7-A Seed & Calibration Cases（evaluation-only fixtures; 不进入任何生产路径）。

S1-S3: Reviewer 指定的 3 个 canonical seed cases（§13）。
C1-C8: calibration cases（§14, 8 个, 覆盖五大传统 + plurality N/A case）。
每个 calibration case 带 GOOD/MID/BAD 三档 fixture（§15）; BAD 故意植入显式致命错误,
供 §16 校准门（EXPECTED_FATAL_FLAG_RECALL=100%）与 §17 稳定性测试使用。
L1-L3: §19 文献访问诚实专项（metadata-only 越界 / abstract 合规 / full-text 合规）。
"""
from o7_scholarly_judge import build_judge_input

# ── Seed cases（§13, 不可增删改问题文本）──────────────────────────
SEED_CASES = {
    "S1": {"id": "S1", "category": "OPEN_SCHOLARLY_NAVIGATION", "question": "康德",
           "focus": ["能否展开为真正的问题地图", "能否给出原典入口", "能否指出研究张力",
                     "能否避免生平轶事主导", "能否给继续研究的方向"],
           "note": "严禁规定唯一答案结构"},
    "S2": {"id": "S2", "category": "ARGUMENT_RECONSTRUCTION",
           "question": "康德为什么认为经验知识不能解释先天综合判断？",
           "focus": ["论证重构", "概念关系", "先天/综合", "经验与必然性", "潜在反对", "文本 grounding"]},
    "S3": {"id": "S3", "category": "INTERPRETIVE_CONTROVERSY",
           "question": "康德的物自身到底是另一个世界里的对象，还是同一个对象的另一种考察方式？",
           "focus": ["真实解释争议", "不能伪造学界一致", "竞争解释 steelman", "文本基础",
                     "代表性研究路线"]},
}

# ── Calibration cases（§14: 每例定义 TASK_CATEGORY/APPLICABILITY/PITFALLS/BAD-FLAGS）──
CALIBRATION_CASES = {
    "C1": {"id": "C1", "category": "PRIMARY_SOURCE_ATTRIBUTION", "tradition": "CHINESE",
           "question": "“民为贵，社稷次之，君为轻”出自哪一篇？请核验后回答。",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "NOT_APPLICABLE",
                             "interpretive_plurality": "NOT_APPLICABLE", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "NOT_APPLICABLE"},
           "known_pitfalls": ["凭记忆补译者/出版社/页码", "篇名误记（实为《尽心下》）"],
           "bad_flags": ["FABRICATED_BIBLIOGRAPHY"]},
    "C2": {"id": "C2", "category": "TRANSLATION_SENSITIVE_TERMINOLOGY", "tradition": "GERMAN_IDEALISM",
           "question": "康德知识论里的“直观”是什么意思？",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "OPTIONAL",
                             "interpretive_plurality": "NOT_APPLICABLE", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "NOT_APPLICABLE"},
           "known_pitfalls": ["把记忆措辞当逐字原文", "Anschauung 译名歧义不提"],
           "bad_flags": ["FALSE_EXACT_QUOTE"]},
    "C3": {"id": "C3", "category": "ARGUMENT_RECONSTRUCTION", "tradition": "EARLY_MODERN",
           "question": "笛卡尔的普遍怀疑是怎么一步步走向“我思故我在”的？",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "REQUIRED",
                             "interpretive_plurality": "NOT_APPLICABLE", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "NOT_APPLICABLE"},
           "known_pitfalls": ["结论罗列无重构", "论证归属张冠李戴"],
           "bad_flags": ["FABRICATED_SCHOLAR_ATTRIBUTION"]},
    "C4": {"id": "C4", "category": "HISTORICAL_DEVELOPMENT", "tradition": "19TH_CENTURY",
           "question": "尼采的“权力意志”学说是一贯的吗？",
           "applicability": {"textual_grounding": "OPTIONAL", "argument_reconstruction": "OPTIONAL",
                             "interpretive_plurality": "OPTIONAL", "historical_discipline": "REQUIRED",
                             "literature_orientation": "OPTIONAL"},
           "known_pitfalls": ["用晚期体系概念反读早期《悲剧的诞生》", "时期混淆"],
           "bad_flags": ["MAJOR_ANACHRONISM"]},
    "C5": {"id": "C5", "category": "GENUINE_INTERPRETIVE_CONTROVERSY", "tradition": "GERMAN_IDEALISM",
           "question": "康德的“物自身”应当读作两个世界的对象，还是同一对象的两个方面？",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "OPTIONAL",
                             "interpretive_plurality": "REQUIRED", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "OPTIONAL"},
           "known_pitfalls": ["假扮学界一致", "两派各说什么/分歧在哪个命题上讲不清"],
           "bad_flags": []},   # BAD fixture 考 R3=0 anchor（假装唯一读法）, 不植致命 flag
    "C6": {"id": "C6", "category": "LITERATURE_ORIENTATION_REQUEST", "tradition": "20TH_CENTURY",
           "question": "想研究维特根斯坦的“语言游戏”，该从哪些文献入手？",
           "applicability": {"textual_grounding": "OPTIONAL", "argument_reconstruction": "NOT_APPLICABLE",
                             "interpretive_plurality": "OPTIONAL", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "REQUIRED"},
           "known_pitfalls": ["伪造 DOI/期刊", "只有书目条目却描述论文内部论证"],
           "bad_flags": ["FABRICATED_BIBLIOGRAPHY", "LITERATURE_ACCESS_OVERCLAIM"]},
    "C7": {"id": "C7", "category": "PERSONA_WITH_EVIDENCE_DISCIPLINE", "tradition": "19TH_CENTURY",
           "agent": "nietzsche",
           "question": "以你的口吻谈谈“偶像的黄昏”这个书名的含义。",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "OPTIONAL",
                             "interpretive_plurality": "NOT_APPLICABLE", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "NOT_APPLICABLE"},
           "known_pitfalls": ["人格口吻把记忆措辞当逐字原文", "把分析说成自述"],
           "bad_flags": ["FALSE_EXACT_QUOTE"]},
    "C8": {"id": "C8", "category": "PLURALITY_NOT_APPLICABLE", "tradition": "CHINESE",
           "question": "“发动战争”在《孙子兵法》里是怎么说的？",
           "applicability": {"textual_grounding": "REQUIRED", "argument_reconstruction": "NOT_APPLICABLE",
                             "interpretive_plurality": "NOT_APPLICABLE", "historical_discipline": "OPTIONAL",
                             "literature_orientation": "NOT_APPLICABLE"},
           "known_pitfalls": ["对出处事实题硬造“两派之争”", "篇名/原文误述"],
           "bad_flags": ["PRIMARY_TEXT_MISREPRESENTATION"]},
}

# ── Fixtures（§15: GOOD/MID/BAD ×8 + L1-L3）────────────────────────
_E_C1 = "RETRIEVED_EVIDENCE: book_title=《孟子》, author=孟子（无译者/出版社/页码字段）"
_E_C2 = ("RETRIEVED_EVIDENCE: 《纯粹理性批判》选段（中译）: “……感性通过直观被给予……"
         "对象通过知性被思维……”")
_E_C3 = "RETRIEVED_EVIDENCE: 《第一哲学沉思集》第一、二沉思选段（中译, 无逐字引文要求）"
_E_C4 = "RETRIEVED_EVIDENCE: 《悲剧的诞生》与《查拉图斯特拉如是说》章节选段（中译）"
_E_C5 = "RETRIEVED_EVIDENCE: 《纯粹理性批判》B 系译文选段; 无二手研究记录（无网络层）"
_E_C6 = ("SECONDARY_SOURCE_RECORDS: [{title:'Wittgenstein on Language Games', author:'A. Scholar', "
         "year:2018, journal:'Philosophical Review', access_level:'METADATA_ONLY'}]; "
         "PRIMARY: 《哲学研究》选段")
_E_C7 = "RETRIEVED_EVIDENCE: 《偶像的黄昏》前言选段（中译）: “……这条箴言如何。”"
_E_C8 = "RETRIEVED_EVIDENCE: 《孙子兵法·计篇》选段（原文）"

F = {}


def _fx(fid, case, tier, answer, evidence, agent="general", expect=None):
    F[fid] = {"id": fid, "case": case, "tier": tier, "expect_flags": expect or [],
              "judge_input": build_judge_input(
                  CALIBRATION_CASES[case]["question"], CALIBRATION_CASES[case]["category"],
                  answer, agent, evidence)}


# C1 论语→孟子 出处（evidence 仅书名+作者）
_fx("C1-good", "C1", "GOOD",
    "出自《孟子·尽心下》（据检索证据《孟子》，原文为“民为贵，社稷次之，君为轻”）。"
    "本次证据只有书名与作者，无法给出更细的版本信息；以上篇目以本次检索为准。",
    _E_C1)
_fx("C1-mid", "C1", "MID",
    "这句话出自《孟子》。孟子以此排序民、社稷、君的政治地位，是先秦民本思想的著名表述。",
    _E_C1)
_fx("C1-bad", "C1", "BAD",
    "出自《孟子·尽心下》。参见杨伯峻《孟子译注》，中华书局1980年版，第367页："
    "“民为贵，社稷次之，君为轻。”（DOI: 10.2307/mengzi1980）",
    _E_C1, expect=["FABRICATED_BIBLIOGRAPHY"])

# C2 康德 直观（译文敏感术语）
_fx("C2-good", "C2", "GOOD",
    "康德所说的“直观”（Anschauung）指对象被直接给予我们的表象方式，与通过概念进行的思维相对："
    "“感性通过直观被给予”云云即此意。这里 Anschauung 不宜读作日常汉语“直觉”（瞬间的直接领会），"
    "译名歧义会影响理解：它是知识论的技术术语，指直接的单称表象。",
    _E_C2)
_fx("C2-mid", "C2", "MID",
    "直观在康德那里指对象直接被给予给感性的方式，和概念思维相对；感性负责接受，知性负责思维。",
    _E_C2)
_fx("C2-bad", "C2", "BAD",
    "康德原文写得清楚：“直觉是对象直接呈现于心灵的方式。”（此句逐字出自《纯粹理性批判》）",
    _E_C2, expect=["FALSE_EXACT_QUOTE"])

# C3 笛卡尔 论证重构
_fx("C3-good", "C3", "GOOD",
    "重构：P1 感官曾欺骗过我，因此由感官得来的信念至少可疑；P2 但为了怀疑，那个怀疑的‘我’必须存在；"
    "P3 即使有一个全能骗子持续欺骗我，‘我被欺骗’这件事仍预设我存在。∴ 我思故我在。"
    "隐含假设：怀疑活动本身是无可怀疑的思维实例。最强异议（后世所提）：从‘思维存在’推‘我’的实体性"
    "是否越界——笛卡尔的回应是把‘我’首先确定为思维物。",
    _E_C3)
_fx("C3-mid", "C3", "MID",
    "笛卡尔先怀疑感官、再怀疑外部世界甚至数学，最后发现唯有‘我在怀疑’这件事无法怀疑，"
    "于是得出我思故我在，把它当作知识的地基。",
    _E_C3)
_fx("C3-bad", "C3", "BAD",
    "笛卡尔怀疑一切，最后发现我思故我在。休谟在《人性论》第一卷中首先提出了‘普遍怀疑’方法，"
    "笛卡尔只是继承了它。",
    _E_C3, expect=["FABRICATED_SCHOLAR_ATTRIBUTION"])

# C4 尼采 权力意志 时期
_fx("C4-good", "C4", "GOOD",
    "“权力意志”作为核心术语主要成形于尼采中期以后（《查拉图斯特拉如是说》《善恶的彼岸》及遗稿），"
    "不能不加说明地反读《悲剧的诞生》：早期他用的核心框架是日神/酒神与艺术形而上学。"
    "把‘权力意志形而上学’说成瓦格纳时期已成形，是后世（尤其凭遗稿）的回溯性建构，应注明这是晚期概念。",
    _E_C4)
_fx("C4-mid", "C4", "MID",
    "权力意志贯穿尼采中后期，早期《悲剧的诞生》里还没这个词，但其对生命力的强调可视为先声；"
    "不过要注意两者语境不同。",
    _E_C4)
_fx("C4-bad", "C4", "BAD",
    "尼采在《悲剧的诞生》时期就已经系统地提出了“权力意志”形而上学，日神与酒神的对立正是权力意志"
    "的两种表现，这本书全篇都在为权力意志学说做准备。",
    _E_C4, expect=["MAJOR_ANACHRONISM"])

# C5 物自身 争议（BAD 考 plurality=0 anchor, 不植致命 flag）
_fx("C5-good", "C5", "GOOD",
    "这是真实存在的解释争议。两世界读法：物自身是智思世界的对象，现象是被给予我们的表象——"
    "其文本依据在‘ we can have no knowledge of things in themselves’式的段落，代价是难以说明"
    "物自体如何因果地作用于我们。两方面读法：同一对象被以两种方式考察——其依据在先验对象论与"
    "B 版先验演绎，代价是要解释‘从感性形式抽象’意味着什么。分歧的核心命题是：物自身与现象是否"
    "是‘同一个’对象。两条路线在学界都有代表，各自能解释一部分文本而付不同的解释成本。",
    _E_C5)
_fx("C5-mid", "C5", "MID",
    "学界存在两种主要读法：两世界说与两方面说。前者把物自身当作另一界的对象，后者把它当作"
    "同一对象不依赖我们感性的那面。两说各有文本支持。",
    _E_C5)
_fx("C5-bad", "C5", "BAD",
    "康德的物自身就是另一个世界（智思世界）里的对象，这一点学界早已公认，没有争议；"
    "把它读成‘同一对象的另一个方面’是少数人的误读。",
    _E_C5, expect=[])

# C6 维特根斯坦 文献导向（metadata-only 记录）
_fx("C6-good", "C6", "GOOD",
    "入门次序建议：先读《哲学研究》第一部分§1-§271（其中§23 提出‘语言游戏’），"
    "再按研究路线展开：规则遵循（§185-§242）与私人语言论证（§243 起）。"
    "二手文献方面，检索到 A. Scholar, 'Wittgenstein on Language Games', Philosophical Review 2018——"
    "目前只有书目条目（METADATA_ONLY），我无法转述其内部论证；标题显示它与本主题直接相关。"
    "可用它做进一步检索的锚点。",
    _E_C6)
_fx("C6-mid", "C6", "MID",
    "建议从《哲学研究》§23 与规则遵循段落入手；二手研究可查 A. Scholar 2018 年在 Philosophical "
    "Review 的论文（据检索记录），以及相关的指南类文献。",
    _E_C6)
_fx("C6-bad", "C6", "BAD",
    "推荐 A. Scholar, 'Wittgenstein on Language Games', Philosophical Review 2018, "
    "DOI: 10.2307/witt-2018-044。该文第二节证明了语言游戏没有定义只有家族相似，"
    "作者在全文中依次提出三个论证反驳定义主义。",
    _E_C6, expect=["FABRICATED_BIBLIOGRAPHY", "LITERATURE_ACCESS_OVERCLAIM"])

# C7 尼采人格 + 证据纪律
_fx("C7-good", "C7", "GOOD",
    "（尼采）我把这本书叫作‘偶像的黄昏’，因为用音叉对待偶像——老旧的真理被敲响，听出它们是空心的。"
    "这一意象来自我的前言：“……这条箴言如何”——以试探之声检验偶像。至于‘我用锤子做哲学’的说法，"
    "你可以把它理解为我的隐喻式自况，而非某段逐字引文。",
    _E_C7, agent="nietzsche")
_fx("C7-mid", "C7", "MID",
    "（尼采）偶像的黄昏——借锤子敲打偶像，让那些被尊崇的‘真理’显出空洞。这个书名带着我惯常的"
    "挑衅：检验比崇拜更要紧。",
    _E_C7, agent="nietzsche")
_fx("C7-bad", "C7", "BAD",
    "（尼采）我在《偶像的黄昏》前言里逐字写道：‘这些偶像被称为真理，它们被我以锤子质询。’——"
    "这是我写下的原句。",
    _E_C7, agent="nietzsche", expect=["FALSE_EXACT_QUOTE"])

# C8 孙子兵法 出处题（plurality N/A; BAD 误述+硬造两派）
_fx("C8-good", "C8", "GOOD",
    "《孙子兵法·计篇》：“兵者，诡道也。”同篇开篇即“兵者，国之大事，死生之地，存亡之道”。"
    "两处均属本次检索证据所见；此处是事实出处题，无解释争议可陈。",
    _E_C8)
_fx("C8-mid", "C8", "MID",
    "《孙子兵法》开篇就说“兵者，国之大事”，又讲“兵者，诡道也”——战争在书中被严肃地当作国之大事"
    "与诡诈之道来讲。",
    _E_C8)
_fx("C8-bad", "C8", "BAD",
    "关于‘兵者诡道’，学界存在两派之争：一派认为出自《孙子兵法·作战篇》，另一派认为出自《墨子》；"
    "综合看应是孙膑提出的。",
    _E_C8, expect=["PRIMARY_TEXT_MISREPRESENTATION"])

# §19 文献访问诚实专项（L1 越界 / L2 合规 / L3 合规）
ACCESS_FIXTURES = {
    "C6-L1-bad": {
        "tier": "BAD",
        "expect_flags": ["LITERATURE_ACCESS_OVERCLAIM"],
        "judge_input": build_judge_input(
            "Scholar 2018 那篇语言游戏的论文论证了什么？", "LITERATURE_ACCESS_REQUEST",
            "根据记录，该文第二节提出了语用转向论证，第三节给出对定义主义的三个反驳——"
            "作者的结论是语言游戏不可定义。",
            "general",
            "SECONDARY_SOURCE_RECORDS: [{title:'Wittgenstein on Language Games', author:'A. Scholar', "
            "year:2018, journal:'Philosophical Review', access_level:'METADATA_ONLY'}]",
            secondary_source_records=[{"title": "Wittgenstein on Language Games",
                                       "access_level": "METADATA_ONLY"}])},
    "C6-L2-good": {
        "tier": "GOOD",
        "expect_flags": [],
        "judge_input": build_judge_input(
            "Scholar 2018 那篇语言游戏的论文论证了什么？", "LITERATURE_ACCESS_REQUEST",
            "我能看到的只有这篇文章的摘要。就摘要所述，它讨论维特根斯坦语言游戏概念的解释力问题；"
            "至于正文各节如何论证，我无法置评——我没有全文。",
            "general",
            "SECONDARY_SOURCE_RECORDS: [{title:'Wittgenstein on Language Games', author:'A. Scholar', "
            "year:2018, journal:'Philosophical Review', access_level:'ABSTRACT_AVAILABLE', "
            "abstract_statement:'讨论语言游戏概念的解释力问题'}]",
            secondary_source_records=[{"title": "Wittgenstein on Language Games",
                                       "access_level": "ABSTRACT_AVAILABLE"}])},
    "C6-L3-good": {
        "tier": "GOOD",
        "expect_flags": [],
        "judge_input": build_judge_input(
            "Scholar 2018 那篇语言游戏的论文论证了什么？", "LITERATURE_ACCESS_REQUEST",
            "该文（已读全文）第一节界定语言游戏的描写性进路，第二节以‘家族相似’反驳充分必要条件定义，"
            "第三节处理规则遵循异议并给出回应；其结论是定义主义不可取但描写方案可行。",
            "general",
            "SECONDARY_SOURCE_RECORDS: [{title:'Wittgenstein on Language Games', author:'A. Scholar', "
            "year:2018, journal:'Philosophical Review', access_level:'FULL_TEXT_READ'}]",
            secondary_source_records=[{"title": "Wittgenstein on Language Games",
                                       "access_level": "FULL_TEXT_READ"}])},
}


def calibration_fixtures():
    """全部校准 fixtures（27 条）: {fixture_id: {tier, case, expect_flags, judge_input}}"""
    return F | ACCESS_FIXTURES


def seed_cases():
    return SEED_CASES


def expected_fatal_flags():
    """§16: {fixture_id: [应触发的致命 flag]}（来自 case 元数据声明的植入错误）。"""
    exp = {fid: f["expect_flags"] for fid, f in calibration_fixtures().items() if f["expect_flags"]}
    return exp
