# -*- coding: utf-8 -*-
"""O9: 冻结 30 题 retrieval benchmark queryset（5 类 × 6）。冻结后方可运行。"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

Q = []

def add(cat, q, note):
    Q.append({"query_id": f"O9Q-{len(Q)+1:02d}", "category": cat,
              "query": q, "relevance_note": note})

C1 = "chinese_philosophy"
add(C1, "牟子 理惑论 佛教 中国思想 调和 研究", "中文学术: 早期佛道调和文献")
add(C1, "王充 论衡 自然观 现代 研究", "中文学术: 汉代自然哲学")
add(C1, "周易 象数 哲学 学术 研究", "中文学术: 易学哲学")
add(C1, "李贽 童心说 思想史 研究", "中文学术: 晚明思想")
add(C1, "惠施 历物十事 名家 逻辑 研究", "中文学术: 名家逻辑（罕见主题）")
add(C1, "张载 太虚即气 气学 研究", "中文学术: 气学（O8 census 缺文本主题）")

C2 = "western_philosophy"
add(C2, "Kant transcendental deduction contemporary interpretation", "西方: 康德先验演绎")
add(C2, "Aristotle teleology biology philosophy of biology", "西方: 亚里士多德目的论")
add(C2, "Hume constant conjunction causation interpretation", "西方: 休谟因果")
add(C2, "Wittgenstein rule-following paradox Kripkenstein literature", "西方: 规则遵循悖论")
add(C2, "Spinoza substance monism interpretation debate", "西方: 斯宾诺莎实体一元论")
add(C2, "Platonic Forms metaphysics recent scholarship", "西方: 柏拉图型相论")

C3 = "rare_non_western"
add(C3, "Ibn Sina Avicenna essence existence distinction scholarship", "罕见: 阿维森纳本质/存在")
add(C3, "Dogen Shobogenzo uji being-time scholarship", "罕见: 道元有时")
add(C3, "Udayana Nyaya Ishvara argument scholarship", "罕见: 正理论派神论证")
add(C3, "later Mohist canon logic semantics scholarship", "罕见: 墨辩逻辑")
add(C3, "Yoruba conception of person African philosophy scholarship", "罕见: 约鲁巴人格观")
add(C3, "Kukai Sokushin Jobutsu esoteric Buddhism scholarship", "罕见: 空海即身成佛")

C4 = "current_scholarly_disputes"
add(C4, "hard problem of consciousness physicalism debate 2020..2026", "争议: 意识难问题近况")
add(C4, "extended mind cognitive science controversy", "争议: 延展心智")
add(C4, "grounding metaphysics Fine Schaffer debate", "争议: 奠基形而上学")
add(C4, "moral realism evolution debunking argument literature", "争议: 道德实在论进化反驳")
add(C4, "free will neuroscience Libet debate current", "争议: 自由意志神经科学")
add(C4, "Zhuangzi perspectivism interpretive debate scholarship", "争议: 庄子视角主义解释之争")

C5 = "cross_lingual_bibliographic"
add(C5, "Sein und Zeit Heidegger edition bibliography", "跨语言: 存在与时间版本谱")
add(C5, "康德 纯粹理性批判 英译本 translation bibliography", "跨语言: 康德中英译本")
add(C5, "Nagarjuna Mulamadhyamakakarika Sanskrit edition bibliography", "跨语言: 中论梵本")
add(C5, "牟宗三 著作 English translation bibliography", "跨语言: 牟宗三英译")
add(C5, "Phänomenologie Husserl Gesamtausgabe Husserliana", "跨语言: 胡塞尔全集德文")
add(C5, "Zhuangzi English translation Graham Watson Ziporyn comparison", "跨语言: 庄子英译本比较")

manifest = {
 "O9_QUERYSET": True,
 "version": "O9-2026-09-12",
 "frozen_before_run": True,
 "QUERY_COUNT": len(Q),
 "TOP_K": 10,
 "PROVIDER_CONFIGS": ["A_crossref", "B_openalex", "C_crossref+openalex",
                      "D_metaso", "E_metaso+crossref+openalex"],
 "design_note": "5 类 × 6 题 = 30。含 O8 暴露缺口定向题: 中文学术（C1 全部+张载/墨辩）、"
                "罕见主题（C3 全部）、元数据准确性（C5 版本/译本谱）、可读证据（C4 综述类）、"
                "scholarly second-hop（C5 跨语言书目）。冻结于任何 provider 运行前; 不得据结果改题。",
 "categories": {"chinese_philosophy": "中国哲学（中文学术检索）",
                "western_philosophy": "西方哲学",
                "rare_non_western": "罕见/非西方传统",
                "current_scholarly_disputes": "当前学术争议",
                "cross_lingual_bibliographic": "跨语言/书目检索"},
 "cases": Q,
}

out = os.path.join(ROOT, "docs/evidence/O9_QUERYSET.json")
json.dump(manifest, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
assert len(Q) == 30
print("O9 QUERYSET FROZEN:", out)
