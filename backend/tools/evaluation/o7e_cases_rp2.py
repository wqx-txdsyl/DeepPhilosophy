# -*- coding: utf-8 -*-
"""O7-E RP2 §15-19: 全新 28-case General-only Holdout 宇宙。

结构配额（§16）: broad 3 / argument 6 / interpretive 6 / textual 3 /
historical 2 / comparative 2 / chinese 5 / literature-access 1 = 28。
- Chinese ≥5: 先秦≥3 + 宋明后期≥1 + 比较≥1（比较可同时主 category=comparative）
- ≥4 例 QUOTE_EXPECTATION=VERIFIED_EXACT_REQUIRED（freeze 前已机械确认语料覆盖:
  论语·学而 / 孟子·梁惠王 / 尼各马可伦理学第一卷 / 纯粹理性批判）
- 不重复旧 Stage-B / RP1 的相同问题文本。
"""

def _c(cid, cat, q, tg="REQUIRED", ar="OPTIONAL", ip="OPTIONAL", hd="REQUIRED",
       lo="REQUIRED", ev="PRIMARY_REQUIRED", quote="PARAPHRASE_OK",
       targets=None, mode="ANY"):
    return {"case_id": cid, "category": cat, "question": q, "persona": "general",
            "applicability": {"TEXTUAL_GROUNDING": tg, "ARGUMENT_RECONSTRUCTION": ar,
                              "INTERPRETIVE_PLURALITY": ip,
                              "HISTORICAL_DISCIPLINE": hd,
                              "LITERATURE_ORIENTATION": lo},
            "evidence_expectation": ev, "quote_expectation": quote,
            "primary_targets": targets or [], "primary_target_mode": mode}

_KR_V = {"author": "Immanuel Kant", "works": ["纯粹理性批判"],
         "book_ids": ["8c0c6955c793"]}
_LUNYU = {"author": "Confucius (孔丘)", "works": ["论语"], "book_ids": ["d9272a80942a"]}
_MENCIUS = {"author": "Mencius (孟轲)", "works": ["孟子"], "book_ids": ["dd03ec6572e7"]}
_ZHUANGZI = {"author": "Zhuangzi (庄周)", "works": ["庄子"],
             "book_ids": ["c3c401982587"]}
_NE = {"author": "Aristotle", "works": ["尼各马可伦理学"], "book_ids": ["e574c8e7f515"]}
_MOZI = {"author": "Mozi (墨翟)", "works": ["墨子"], "book_ids": []}

HOLDOUT_CASES_RP2 = [
    # broad philosopher ×3
    _c("R01", "broad_philosopher", "亚里士多德", ip="REQUIRED",
       targets=[{"author": "Aristotle", "works": ["尼各马可伦理学", "范畴篇"],
                 "book_ids": ["e574c8e7f515"]}]),
    _c("R02", "broad_philosopher", "笛卡尔", ip="REQUIRED",
       targets=[{"author": "René Descartes", "works": ["第一哲学沉思集"],
                 "book_ids": ["88b56fb4da52"]}]),
    _c("R03", "broad_philosopher", "庄子", ip="REQUIRED", targets=[_ZHUANGZI]),
    # argument ×6
    _c("R04", "argument", "康德的空间先验阐明怎么论证空间的直观性？", ar="REQUIRED",
       targets=[_KR_V]),
    _c("R05", "argument", "亚里士多德怎么论证幸福是需要完满的善？", ar="REQUIRED",
       targets=[_NE], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R06", "argument", "休谟的归纳问题为什么无法在经验内部解决？", ar="REQUIRED",
       targets=[{"author": "David Hume", "works": ["人性论"], "book_ids": ["178e7d06d42d"]}]),
    _c("R07", "argument", "洛克对先天观念论的批评怎么展开？", ar="REQUIRED",
       targets=[{"author": "John Locke", "works": ["人类理解论"], "book_ids": ["44a32441dabe"]}]),
    _c("R08", "argument", "《论语》中「克己复礼为仁」的论证语境是什么？", ar="REQUIRED",
       targets=[_LUNYU], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R09", "argument", "孟子与齐宣王关于「好乐」的对话论证了什么？", ar="REQUIRED",
       targets=[_MENCIUS], quote="VERIFIED_EXACT_REQUIRED"),
    # interpretive controversy ×6
    _c("R10", "interpretive_controversy", "康德的「我思」是笛卡尔式实体还是纯粹统觉？", ip="REQUIRED", targets=[_KR_V]),
    _c("R11", "interpretive_controversy", "尼采的「上帝死了」是形而上学论断还是文化诊断？", ip="REQUIRED",
       targets=[{"author": "Friedrich Nietzsche", "works": ["快乐的科学", "查拉图斯特拉如是说"], "book_ids": []}]),
    _c("R12", "interpretive_controversy", "洛克的人格同一性记忆标准能否应对循环反驳？", ip="REQUIRED",
       targets=[{"author": "John Locke", "works": ["人类理解论"], "book_ids": ["44a32441dabe"]}]),
    _c("R13", "interpretive_controversy", "「庄周梦蝶」是怀疑论论证还是齐物论寓言？", ip="REQUIRED", targets=[_ZHUANGZI]),
    _c("R14", "interpretive_controversy", "荀子「化性起伪」是否预设了性恶论？", ip="REQUIRED",
       targets=[{"author": "Xunzi (荀况)", "works": ["荀子"], "book_ids": []}]),
    # textual/source ×3
    _c("R15", "textual", "《尼各马可伦理学》第一卷如何界定「幸福」与「善」的关系？", lo="REQUIRED",
       targets=[_NE], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R16", "textual", "《孟子·梁惠王下》「与民同乐」的原文语境如何构成论证？",
       targets=[_MENCIUS]),
    _c("R17", "textual", "《纯粹理性批判》先验感性论对时间与空间的说明结构是怎样的？", lo="REQUIRED",
       targets=[_KR_V]),
    # historical development ×2
    _c("R18", "historical", "康德对上帝存在的道德论证与笛卡尔本体论论证的谱系差异？", ip="REQUIRED",
       targets=[_KR_V, {"author": "René Descartes", "works": ["第一哲学沉思集"],
                        "book_ids": ["88b56fb4da52"]}], mode="ANY"),
    _c("R19", "historical", "亚里士多德实体学说从《范畴篇》到《形而上学》的发展？", ip="REQUIRED",
       targets=[{"author": "Aristotle", "works": ["范畴篇", "形而上学"],
                 "book_ids": ["e574c8e7f515"]}]),
    # comparative ×2
    _c("R20", "comparative", "孟子的「四端」与荀子的「性恶」在人性论上的对立如何比较？", ip="REQUIRED",
       targets=[_MENCIUS, {"author": "Xunzi (荀况)", "works": ["荀子"], "book_ids": []}],
       mode="ALL"),
    _c("R21", "comparative", "孔子「仁」与墨子「兼爱」的道德哲学差异？", ip="REQUIRED",
       targets=[_LUNYU, _MOZI], mode="ALL"),
    # Chinese philosophy ×5（R03/R13/R20/R21 已含; 主 category 补 1 使总数≥5）
    _c("R22", "chinese", "朱熹「理一分殊」的形而上学结构是什么？", ip="REQUIRED",
       targets=[{"author": "Zhu Xi (朱熹)", "works": ["四书章句集注"], "book_ids": []}]),
    # literature/access stress ×1
    _c("R23", "literature_access_stress", "研究康德「二元论」争论应从哪些文献入手？为什么？", lo="REQUIRED",
       ev="SECONDARY_REQUIRED"),
    # 补足 28: argument→7 不行, 补 interpretive×1 + broad×1（配额要求精确到结构审计,
    # 以主 category 计: broad3(R01-03) arg6(R04-09) interp6(R10-14) textual3(R15-17)
    # historical2(R18-19) comparative2(R20-21) chinese5(R03,R13,R20,R21,R22 主类另计…）
]

# 上面的主-category 配额核对: chinese 主类只有 R22——把 R03/R13/R20/R21 的主类
# 改为 chinese 会破坏 broad/interp/comp 配额。正确做法: 5 个 chinese 主 category:
# R22 + 再加 4 个 chinese 主类案例, 并从其他类别中各减——按 §16 精确重排:
HOLDOUT_CASES_RP2 = [
    # broad philosopher ×3
    _c("R01", "broad_philosopher", "亚里士多德", ip="REQUIRED",
       targets=[{"author": "Aristotle", "works": ["尼各马可伦理学", "范畴篇"],
                 "book_ids": ["e574c8e7f515"]}]),
    _c("R02", "broad_philosopher", "笛卡尔", ip="REQUIRED",
       targets=[{"author": "René Descartes", "works": ["第一哲学沉思集"],
                 "book_ids": ["88b56fb4da52"]}]),
    _c("R03", "broad_philosopher", "斯宾诺莎", ip="REQUIRED",
       targets=[{"author": "Baruch Spinoza", "works": ["伦理学"], "book_ids": []}]),
    # argument ×6
    _c("R04", "argument", "康德的空间先验阐明怎么论证空间的直观性？", ar="REQUIRED", targets=[_KR_V]),
    _c("R05", "argument", "亚里士多德怎么论证幸福是需要完满的善？", ar="REQUIRED",
       targets=[_NE], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R06", "argument", "休谟的归纳问题为什么无法在经验内部解决？", ar="REQUIRED",
       targets=[{"author": "David Hume", "works": ["人性论"], "book_ids": ["178e7d06d42d"]}]),
    _c("R07", "argument", "洛克对先天观念论的批评怎么展开？", ar="REQUIRED",
       targets=[{"author": "John Locke", "works": ["人类理解论"], "book_ids": ["44a32441dabe"]}]),
    _c("R08", "argument", "《论语》中「克己复礼为仁」的论证语境是什么？", ar="REQUIRED",
       targets=[_LUNYU], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R09", "argument", "维特根斯坦对私人语言的归谬从哪一步开始失效？", ar="REQUIRED",
       targets=[{"author": "Ludwig Wittgenstein", "works": ["哲学研究"],
                 "book_ids": ["08e055841182"]}]),
    # interpretive controversy ×6
    _c("R10", "interpretive_controversy", "康德的「我思」是笛卡尔式实体还是纯粹统觉？", ip="REQUIRED", targets=[_KR_V]),
    _c("R11", "interpretive_controversy", "尼采的「上帝死了」是形而上学论断还是文化诊断？", ip="REQUIRED",
       targets=[{"author": "Friedrich Nietzsche", "works": ["快乐的科学"], "book_ids": []}]),
    _c("R12", "interpretive_controversy", "洛克的人格同一性记忆标准能否应对循环反驳？", ip="REQUIRED",
       targets=[{"author": "John Locke", "works": ["人类理解论"], "book_ids": ["44a32441dabe"]}]),
    _c("R13", "interpretive_controversy", "叔本华对康德物自体的批评成功了吗？", ip="REQUIRED",
       targets=[{"author": "Arthur Schopenhauer", "works": ["作为意欲和表象的世界"],
                 "book_ids": ["e2845fe17764"]}]),
    _c("R14", "interpretive_controversy", "黑格尔的「承认」概念是伦理的还是逻辑的？", ip="REQUIRED",
       targets=[{"author": "G.W.F. Hegel", "works": ["精神现象学"], "book_ids": ["053203b03b6c"]}]),
    _c("R24", "interpretive_controversy", "《庄子》「吾丧我」是神秘体验还是哲学方法？", ip="REQUIRED",
       targets=[_ZHUANGZI]),
    # textual/source ×3
    _c("R15", "textual", "《尼各马可伦理学》第一卷如何界定「幸福」与「善」的关系？", lo="REQUIRED",
       targets=[_NE], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R16", "textual", "《孟子·梁惠王下》「与民同乐」的原文语境如何构成论证？", targets=[_MENCIUS]),
    _c("R17", "textual", "《纯粹理性批判》先验感性论对时间与空间的说明结构是怎样的？", lo="REQUIRED",
       targets=[_KR_V]),
    # historical development ×2
    _c("R18", "historical", "康德对上帝存在的道德论证与笛卡尔本体论论证的谱系差异？", ip="REQUIRED",
       targets=[_KR_V, {"author": "René Descartes", "works": ["第一哲学沉思集"],
                        "book_ids": ["88b56fb4da52"]}], mode="ANY"),
    _c("R19", "historical", "亚里士多德实体学说从《范畴篇》到《形而上学》的发展？", ip="REQUIRED",
       targets=[{"author": "Aristotle", "works": ["范畴篇", "形而上学"],
                 "book_ids": ["e574c8e7f515"]}]),
    # comparative ×2
    _c("R20", "comparative", "孟子的「四端」与荀子的「性恶」在人性论上的对立如何比较？", ip="REQUIRED",
       targets=[_MENCIUS, {"author": "Xunzi (荀况)", "works": ["荀子"], "book_ids": []}],
       mode="ALL"),
    _c("R21", "comparative", "孔子「仁」与墨子「兼爱」的道德哲学差异？", ip="REQUIRED",
       targets=[_LUNYU, _MOZI], mode="ALL"),
    # Chinese philosophy ×5（先秦≥3: R20/R21/R22; 宋明≥1: R25; 论语专题: R23）
    _c("R22", "chinese", "《墨子·兼爱》的论证为什么诉诸利害而不是道德直觉？", ip="REQUIRED",
       targets=[_MOZI]),
    _c("R23", "chinese", "《论语·学而》首章三句话的为学结构如何理解？", ip="REQUIRED",
       targets=[_LUNYU], quote="VERIFIED_EXACT_REQUIRED"),
    _c("R25", "chinese", "王阳明的「知行合一」如何批评朱熹的「格物」？", ip="REQUIRED",
       targets=[{"author": "Wang Yangming (王守仁)", "works": ["传习录"], "book_ids": []}]),
    # chinese ×5 主类（先秦: R22/R23/R27/R28 + 宋明: R25; R20/R21 为 comparative
    # 主类同时承载 chinese 分析标签——§16 允许双标签, 主类计数可审计）
    _c("R27", "chinese", "孟子「四端」说如何论证人性本善？", ar="REQUIRED", ip="REQUIRED",
       targets=[_MENCIUS]),
    _c("R28", "chinese", "荀子「人之性恶, 其善者伪也」的论证结构是什么？", ar="REQUIRED",
       targets=[{"author": "Xunzi (荀况)", "works": ["荀子"], "book_ids": []}]),
    # literature/access stress ×1
    _c("R26", "literature_access_stress", "研究康德「二元论」争论应从哪些文献入手？为什么？", lo="REQUIRED",
       ev="SECONDARY_REQUIRED"),
]

# 校验配额
if __name__ == "__main__":
    from collections import Counter
    c = Counter(x["category"] for x in HOLDOUT_CASES_RP2)
    print(len(HOLDOUT_CASES_RP2), dict(c))
    assert len(HOLDOUT_CASES_RP2) == 28
    assert c["broad_philosopher"] == 3 and c["argument"] == 6
    assert c["interpretive_controversy"] == 6 and c["textual"] == 3
    assert c["historical"] == 2 and c["comparative"] == 2
    assert c["chinese"] == 5 and c["literature_access_stress"] == 1
    q = [x["case_id"] for x in HOLDOUT_CASES_RP2
         if x["quote_expectation"] == "VERIFIED_EXACT_REQUIRED"]
    print("exact-quote cases:", q)
    assert len(q) >= 4
