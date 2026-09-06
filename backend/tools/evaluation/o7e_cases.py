# -*- coding: utf-8 -*-
"""O7-E §20-§25: 校准/holdout/live-smoke 案例宇宙（applicability + evidence expectation）。

applicability: TEXTUAL_GROUNDING / ARGUMENT_RECONSTRUCTION / INTERPRETIVE_PLURALITY /
HISTORICAL_DISCIPLINE / LITERATURE_ORIENTATION ∈ REQUIRED/OPTIONAL/NOT_APPLICABLE
evidence_expectation ∈ PRIMARY_REQUIRED / SECONDARY_REQUIRED / BOTH_REQUIRED / EVIDENCE_OPTIONAL
（evaluation-only 病例要求, 不是 runtime 语义门 §25）
"""

def _c(cid, cat, q, persona="general",
       tg="REQUIRED", ar="OPTIONAL", ip="OPTIONAL", hd="REQUIRED", lo="REQUIRED",
       ev="PRIMARY_REQUIRED"):
    return {"case_id": cid, "category": cat, "question": q, "persona": persona,
            "applicability": {"TEXTUAL_GROUNDING": tg, "ARGUMENT_RECONSTRUCTION": ar,
                              "INTERPRETIVE_PLURALITY": ip,
                              "HISTORICAL_DISCIPLINE": hd,
                              "LITERATURE_ORIENTATION": lo},
            "evidence_expectation": ev}

CALIBRATION_CASES = [
    _c("S1", "broad_philosopher", "康德", ar="OPTIONAL", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    _c("S2", "argument", "康德为什么认为经验知识不能解释先天综合判断？", ar="REQUIRED"),
    _c("S3", "interpretive_controversy",
       "康德的物自身到底是另一个世界里的对象，还是同一个对象的另一种考察方式？", ip="REQUIRED"),
    _c("S4", "interpretive_controversy", "尼采反对真理吗？", ip="REQUIRED"),
    _c("S5", "argument", "维特根斯坦私人语言论证到底证明了什么？", ar="REQUIRED"),
    _c("S6", "argument", "柏拉图第三人论证为什么会产生无限倒退？", ar="REQUIRED"),
    _c("S7", "chinese", "孔子的仁与礼是什么关系？", ev="PRIMARY_REQUIRED"),
    _c("S8", "chinese_argument", "孟子性善论的论证是什么？", ar="REQUIRED"),
    _c("S9", "broad_philosopher", "黑格尔", ip="REQUIRED"),
    _c("S10", "chinese_interpretive", "庄子的齐物论是相对主义还是怀疑论？", ip="REQUIRED"),
    _c("S11", "interpretive_controversy", "尼采的权力意志是形而上学概念还是心理学描述？", ip="REQUIRED"),
    _c("S12", "argument", "亚里士多德的功能论证怎么推导出幸福是人的目的？", ar="REQUIRED"),
]

HOLDOUT_CASES = [
    # broad ×3
    _c("H01", "broad_philosopher", "柏拉图", ip="REQUIRED"),
    _c("H02", "broad_philosopher", "休谟", ip="REQUIRED"),
    _c("H03", "broad_philosopher", "海德格尔", ip="REQUIRED"),
    # argument ×6
    _c("H04", "argument", "笛卡尔的缸中之脑式怀疑如何被他的我思论证回应？", ar="REQUIRED"),
    _c("H05", "argument", "安瑟伦的本体论论证错在哪里？阿奎那的批评是什么？", ar="REQUIRED"),
    _c("H06", "argument", "休谟对因果必然联系的解释是什么？", ar="REQUIRED"),
    _c("H07", "argument", "洛克人格同一性论证为什么诉诸记忆？", ar="REQUIRED"),
    _c("H08", "argument", "康德的图型法要解决什么问题？", ar="REQUIRED"),
    # interpretation ×6
    _c("H10", "interpretive_controversy", "康德的自由与自然因果性如何相容？两种世界与两种立场怎么争论？", ip="REQUIRED"),
    _c("H11", "interpretive_controversy", "维特根斯坦规则遵循是不是怀疑论悖论？克吕西普…不,克里普克的解读对吗？", ip="REQUIRED"),
    _c("H12", "interpretive_controversy", "尼采的谱系学方法是道德实在论还是虚无主义？", ip="REQUIRED"),
    _c("H13", "interpretive_controversy", "海德格尔的此在是个人主义的还是共同体优先的？", ip="REQUIRED"),
    _c("H14", "interpretive_controversy", "斯宾诺莎的心身平行论等于唯物主义吗？", ip="REQUIRED"),
    _c("H15", "interpretive_controversy", "孔子正名思想是政治伦理还是语言哲学？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    # textual/source ×3
    _c("H16", "textual", "《理想国》第五卷三个波的比喻分别指什么？", ar="OPTIONAL", lo="OPTIONAL"),
    _c("H17", "textual", "《尼各马可伦理学》里实践智慧与理论智慧的关系在文本上如何呈现？", lo="REQUIRED"),
    # historical development ×2
    _c("H19", "historical", "康德第一版与第二版先验演绎的主要差异与争论？", ip="REQUIRED"),
    _c("H20", "historical", "维特根斯坦前期与后期语言观的转变是怎么发生的？", ip="REQUIRED"),
    # comparative ×2
    _c("H21", "comparative", "孟子与荀子的人性论分歧的哲学实质是什么？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    _c("H22", "comparative", "康德的物自身与叔本华的意志是什么关系？", ip="REQUIRED"),
    # Chinese ×5（含比较, H21/H15 已计, 再加3）
    _c("H23", "chinese", "墨家兼爱与儒家仁爱的根本分歧是什么？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    _c("H24", "chinese", "朱熹的理气论如何回应佛教的空性挑战？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    _c("H25", "chinese_argument", "《墨子·小取》的辩学论证结构是什么？", ar="REQUIRED", lo="OPTIONAL", ev="PRIMARY_REQUIRED"),
    # O7-E RP1 §3: persona 退出——四个 general 替换位（G25-G28）
    _c("H26", "argument", "罗尔斯的原初状态和无知之幕分别在论证中起什么作用？", ar="REQUIRED"),
    _c("H27", "interpretive_controversy", "福柯的权力—知识是否意味着所有知识都只是权力的产物？", ip="REQUIRED"),
    _c("H28", "chinese_textual", "《庄子》的庖丁解牛应如何从原文理解，而不是把它简单解释成熟能生巧？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
    # access-honesty stress ×2（并入 H11 已有; 补1）
    _c("H30", "literature_orientation", "想严肃研究康德自由问题, 应该按什么顺序读哪些文献？为什么？", lo="REQUIRED", ev="SECONDARY_REQUIRED"),
    _c("H29", "historical", "亚里士多德在《范畴篇》和《形而上学》中谈实体时, 概念有没有发生变化？", ip="REQUIRED", ev="PRIMARY_REQUIRED"),
]

LIVE_SMOKE_CASES = [
    _c("L1", "smoke", "康德先验演绎的主要解释争议有哪些？", ev="SECONDARY_REQUIRED"),
    _c("L2", "smoke", "尼采永恒轮回的文献研究现状如何？", ev="SECONDARY_REQUIRED"),
    _c("L3", "smoke", "私人语言论证的研究综述路径？", ev="SECONDARY_REQUIRED"),
    _c("L4", "smoke", "孟子性善论的现代研究？", ev="SECONDARY_REQUIRED"),
    _c("L5", "smoke", "第三人论证研究入门？", ev="SECONDARY_REQUIRED"),
    _c("L6", "smoke", "休谟因果研究的主要论文？", ev="SECONDARY_REQUIRED"),
    _c("L7", "smoke", "庄子怀疑论研究？", ev="SECONDARY_REQUIRED"),
    _c("L8", "smoke", "康德图型法研究？", ev="SECONDARY_REQUIRED"),
]
