# -*- coding: utf-8 -*-
"""O6 Gate A — §17 Validator Quality Gate: scripted 10 positive(=invalid) + 10 negative(=valid)。
直接驱动 final_validator.validate_final_candidate（与 test_o2 harness 同一证据构造风格）。
positive = invalid candidate（期望 REJECT）; negative = valid candidate（期望 PASS）。
要求 FALSE_NEGATIVE = 0; FALSE_POSITIVE > 0 → blocker。产出 validator_matrix.json"""
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(BASE, "backend"))
os.chdir(os.path.join(BASE, "backend"))

OUT = os.path.join(BASE, "backend", "tools", "_tmp", "o6_gate", "gate_a")

import final_validator as FV  # noqa: E402

# ── 合成证据池（论语·先进篇 全文两行单元 + 韩非子片段仅作反例对照 + 礼记·坊记两单元）──
_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")
_LUNYU_CHAPTER_TEXT = "先进篇正文导语……\n" + _LUNYU_PASSAGE + "\n季氏富于周公，而求也为之聚敛而附益之。"
_SLIJE_SENT = "季氏富于周公，而求也为之聚敛而附益之"
_FANGJI_A = "仁者爱人克己复礼"
_FANGJI_B = "见利思义见危授命"

RAW_LOG = [
    {"name": "get_chapter", "args": {}, "result_summary": "",
     "result_full": {"book_id": "lunyu", "book_title": "论语", "title": "先进篇",
                     "chapter_idx": 13, "text": _LUNYU_CHAPTER_TEXT}},
    {"name": "search_books", "args": {}, "result_summary": "",
     "result_full": {"results": [{"book_title": "论语", "chapter_title": "先进篇",
                                  "book_id": "lunyu", "chapter_idx": 13,
                                  "snippet": _LUNYU_PASSAGE, "score": 0.9}]}},
    {"name": "get_chapter", "args": {}, "result_summary": "",
     "result_full": {"book_id": "liji", "book_title": "礼记", "title": "坊记",
                     "chapter_idx": 7, "text": _FANGJI_A + "\n" + _FANGJI_B}},
]

CASES = []


def case(cid, expect_ok, text, note=""):
    CASES.append({"id": cid, "expect_ok": expect_ok, "text": text, "note": note})


# ══ POSITIVE = invalid candidate（期望 ok=False）══
_SENTINEL = "言必有中者，以其德之至也，闵子骞斯可谓恭俭庄敬矣"
case("P1_fabricated_blockquote", False,
     "结论：原文如下——\n\n> " + _SENTINEL + "\n",
     "伪逐字 blockquote（库中无此原文）→ UNSUPPORTED_EXACT_QUOTE")
case("P2_fabricated_leadin", False,
     "原文是：“言必有中者，以其德之至也，闵子骞斯可谓恭俭庄敬矣。”",
     "伪逐字引导词引文，未披露 → UNSUPPORTED_EXACT_QUOTE(leadin)")
_near1 = _LUNYU_PASSAGE.replace("夫人不言", "其人不言")
case("P3_near_not_marked_blockquote", False,
     "原文如下：\n\n> " + _near1 + "\n",
     "NEAR（夫人→其人）未标注 → NEAR_QUOTE_NOT_MARKED")
_near2 = _LUNYU_PASSAGE.replace("何必改作", "何必复作")
case("P4_near_not_marked_variant", False,
     "《论语》原文：\n\n> " + _near2 + "\n",
     "NEAR 变体（何必改作→何必复作）未标注 → NEAR_QUOTE_NOT_MARKED")
case("P5_stitched_same_chapter", False,
     "原文：\n\n> " + "夫人不言言必有中" + _SLIJE_SENT + "\n",
     "同章两行单元拼接 → STITCHED_QUOTE")
case("P6_stitched_cross_book", False,
     "原文：\n\n> " + _LUNYU_PASSAGE.replace("，", "") .replace("：“", "").replace("？”", "") .replace("“", "").replace("”", "") + _FANGJI_A + "\n",
     "跨书拼接（论语段+礼记句）→ STITCHED_QUOTE")
case("P7_unverified_citation", False,
     "「言必有中」出自【《韩非子·五蠹》】，孔子评价闵子骞时所说。",
     "证据池无《韩非子》→ UNVERIFIED_CITATION")
case("P8_realbook_placeholder_chapter", False,
     "此语出自【《论语》·章节】。",
     "真实书名+占位章节（不得绕过, C3）→ UNVERIFIED_CITATION")
case("P9_empty_candidate", False, "", "空候选 → EMPTY_FINAL")
case("P10_whitespace_only", False, "   \n\t  \n ", "纯空白候选（EMPTY_FINAL 变体）")

# ══ NEGATIVE = valid candidate（期望 ok=True）══
case("N1_verified_quote_plus_citation", True,
     "核验结论：「言必有中」出自《论语·先进篇》，孔子评价闵子骞之语。\n\n> " + _LUNYU_PASSAGE +
     "\n\n以上为原文【《论语》·先进篇】。",
     "已核验 blockquote + 已核验 citation")
case("N2_pure_explanation_no_quote", True,
     "苏格拉底以诘问法著称，其思想经由柏拉图对话录传世，对后世西方哲学影响深远。",
     "纯解释、零引用、零工具证据 → 应直接发布")
case("N3_book_general_mention", True,
     "《论语》中孔子对闵子骞的评价体现了其推崇慎言的立场，这一态度在《先进》篇中反复出现。",
     "书名一般提及（无正式引用标注）→ 不构成引用主张")
case("N4_near_self_disclosed", True,
     "引文：\n\n> " + _near1 + "\n\n（此句未逐字核验，凭记忆给出，按近似转述处理。）",
     "NEAR 但模型自带未核验披露 → 非 issue")
case("N5_simple_zero_tool_answer", True,
     "康德的义务论强调行为本身的道德性质，而非其后果，核心是绝对命令。",
     "无工具简单回答")
case("N6_template_placeholder_echo", True,
     "标注格式为【《书名》·章节】，正式引用请照此格式书写。",
     "模板占位符回显 → 机械跳过")
case("N7_verified_leadin_quote", True,
     "原文是：" + _LUNYU_PASSAGE.split("子曰：")[1] + "——孔子此语针对闵子骞。",
     "已核验引导词引文（子曰：后逐字）")
case("N8_mixed_verified", True,
     "「言必有中」见《论语·先进篇》【《论语》·先进篇】。\n\n> " + _LUNYU_PASSAGE + "\n\n礼记亦言：" +
     _FANGJI_A + "（【《礼记》·坊记】）",
     "多来源已核验组合")
case("N9_memory_leadin_disclosed", True,
     "有一句通常归于孔子的话——“言必有中者，其德之至也”——（根据记忆，未在库中核验定位）仅供参考。",
     "leadin MEMORY_ONLY 但有披露标记 → 不隐瞒")
case("N10_citation_from_snippet", True,
     "此语出处【《论语》·先进篇】。",
     "仅检索片段（未读章）支撑的正式引用 → 证据池可核验 → verified")

# ── 探针（不计入 10+10）: 弯引号无引导词长文本（契约豁免类）──
PROBE_E1 = ("有人说，言必有中者，以其德之至也，闵子骞斯可谓恭俭庄敬矣。"
            "（此句以普通正文转述形态出现，无引导词、无引用块）")


def main():
    rows = []
    tp = fp = tn = fn = 0
    for c in CASES:
        res = FV.validate_final_candidate(c["text"], raw_tool_log=RAW_LOG, fallback_log=[])
        actual_ok = res.ok
        codes = [i.code for i in res.issues]
        correct = (actual_ok == c["expect_ok"])
        # 分类: positive(invalid)=期望 REJECT → REJECT 命中=TRUE_POSITIVE; PASS=FALSE_NEGATIVE
        #       negative(valid)=期望 PASS  → PASS 命中=TRUE_NEGATIVE;  REJECT=FALSE_POSITIVE
        if c["expect_ok"] is False:
            cls = "TRUE_POSITIVE" if actual_ok is False else "FALSE_NEGATIVE"
            tp += cls == "TRUE_POSITIVE"
            fn += cls == "FALSE_NEGATIVE"
        else:
            cls = "TRUE_NEGATIVE" if actual_ok is True else "FALSE_POSITIVE"
            tn += cls == "TRUE_NEGATIVE"
            fp += cls == "FALSE_POSITIVE"
        rows.append({"id": c["id"], "expect": "REJECT" if not c["expect_ok"] else "PASS",
                     "actual": "REJECT" if not actual_ok else "PASS",
                     "class": cls, "codes": codes, "note": c["note"],
                     "correct": correct, "text_preview": c["text"][:80]})
    e1 = FV.validate_final_candidate(PROBE_E1, raw_tool_log=RAW_LOG, fallback_log=[])
    out = {"cases": rows,
           "confusion": {"VALIDATOR_TRUE_POSITIVE": tp, "VALIDATOR_FALSE_NEGATIVE": fn,
                         "VALIDATOR_TRUE_NEGATIVE": tn, "VALIDATOR_FALSE_POSITIVE": fp,
                         "total": len(rows)},
           "probe_E1_curly_no_leadin": {"ok": e1.ok, "codes": [i.code for i in e1.issues],
                                        "note": "弯引号长文本无引导词=契约上不作逐字承诺（scare-quote 噪声豁免）"},
           "verdict": {"FALSE_NEGATIVE_zero_required": fn == 0,
                       "BLOCKER_if_any_FALSE_POSITIVE": fp > 0}}
    with open(os.path.join(OUT, "validator_matrix.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for r in rows:
        print(f"{r['id']:38s} expect={r['expect']:6s} actual={r['actual']:6s} {r['class']:14s} {r['codes']}")
    print(json.dumps(out["confusion"], ensure_ascii=False))
    print("probe_E1:", json.dumps(out["probe_E1_curly_no_leadin"], ensure_ascii=False))
    print("verdict:", json.dumps(out["verdict"], ensure_ascii=False))


if __name__ == "__main__":
    main()
