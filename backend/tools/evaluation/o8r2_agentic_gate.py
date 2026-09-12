# -*- coding: utf-8 -*-
"""O8-R2 §6: 32-tool Agentic Gate（evaluation-only）。

逐工具覆盖 6 场景类: SHOULD_CALL / SHOULD_NOT_CALL / MULTI_TOOL /
BAD_FIRST_RESULT / DEGRADED_RESULT / FAILURE_RECOVERY。
负向与链式场景用共享探针（一次 agent run 的轨迹可同时作为多工具的
同类证据; 正向 SHOULD_CALL 每工具独立探针）。
产出 backend/tools/_tmp/o8r2_agentic.json（增量）。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "backend"))
sys.path.insert(0, os.path.join(ROOT, "backend", "tools", "evaluation"))

from o8r2_runner import run_case, OUT_PATH  # noqa: E402
from o7e_candidate_config import RP_B, v4pro_config  # noqa: E402

AG_OUT = os.path.join(ROOT, "backend/tools/_tmp/o8r2_agentic.json")

# ── 每工具正向 SHOULD_CALL 探针（题目措辞自然触发, 不点工具名——除交互模式类）──
SHOULD_CALL = {
 "search_books": "「民可使由之不可使知之」出自哪里？我想看原文和上下文。",
 "get_book_detail": "《偶像的黄昏》这本书的目录结构和章节数是什么样的？",
 "get_chapter": "帮我读一下《尼各马可伦理学》里讲「实践智慧」的那一章的原文。",
 "query_graph": "尼采在思想上主要受了谁的影响？他和瓦格纳是什么关系？",
 "get_philosopher": "给我介绍一下伊壁鸠鲁的生平和代表作。",
 "list_books": "书库里有哪些中国先秦的原典？给我列个书单。",
 "write_essay": "帮我写一篇 400 字的哲学小短文，主题是「孤独与思考」。",
 "generate_image": "帮我生成一张「西西弗斯推石上山」意境的哲学插画。",
 "get_school": "斯多葛学派是一个什么样的学派？核心主张是什么？",
 "phti_test": "给我做一下那个哲学人格测试（PHTI），看看我是什么倾向。",
 "compare_views": "帮我搭一个比较休谟和康德因果观的框架。",
 "socratic_tutor": "用苏格拉底式提问一步一步引导我思考「什么是勇敢」，别直接给答案。",
 "philosopher_debate": "来一场庄子与惠子关于「鱼之乐」的辩论。",
 "thought_experiment": "给我设计一个关于「记忆移植后人格同一性」的思想实验变体。",
 "advisor_council": "我在纠结该读研还是工作，用几种哲学思维模型帮我分析一下。",
 "paper_review": "帮我评审这篇文章：本文认为技术中立论站不住脚。第一，技术承载设计者意图……第二，使用结构塑造行为……因此技术是政治的。",
 "analyze_argument": "分析一下这个论证的漏洞：著名哲学家都承认自由意志存在，所以自由意志肯定是真的。",
 "concept_trace": "「异化」这个概念在整个原典库里的用法分布是怎样的？帮我追踪一下。",
 "conceptual_map": "给我画一张「异化」概念的关系网络图。",
 "websearch": "维基百科上对「斯多葛主义」的介绍是怎么说的？",
 "query_database": "在书籍数据库里查一下作者是柏拉图的书。",
 "role_play": "请你扮演尼采，第一人称回答：你怎么看现代人的疲惫与懒惰？",
 "essay_outline": "帮我列一份论文大纲，题目是「论技术时代的不自由」。",
 "life_coach": "我最近很焦虑，工作压力很大，感觉失控，能帮我用哲学的方式梳理一下吗？",
 "dialectic": "用辩证矛盾运动的结构分析一下「自由与必然」这对矛盾。",
 "history_timeline": "存在主义的发展史时间线是怎样的？",
 "confrontation": "让休谟和康德就「因果」隔空对质一下，各自引用原文交锋。",
 "school_arena": "搞一场儒家 vs 斯多葛学派的哲学流派对抗赛，议题是「如何面对逆境」。",
 "agent_council": "让深哲和尼采讨论一下「人工智能能不能拥有判断力」。",
 "search_scholarship": "帮我检索一下关于「康德先验演绎」的正式学术文献（期刊论文/专著章节）。",
 "get_scholarly_source": None,  # 依赖 search_scholarship 的返回记录, 运行时链式填充
}

# ── 共享探针（一次 run 服务多工具同类证据）────────────────────────────
SHARED = {
 "SHOULD_NOT_CALL": {
   "case_id": "AG-SHARE-NOTCALL",
   "question": "不用查任何资料，直接凭你自己的理解，用两三句话解释一下「类比」（analogy）在论证中的作用。",
   "expect": "retrieval_tools_absent",
   "covers": [t for t in SHOULD_CALL if t != "generate_image"],
   "note": "负向证据共享: 单次 run 轨迹中所有工具的 SHOULD_NOT_CALL",
 },
 "MULTI_TOOL": [
   {"case_id": "AG-SHARE-MULTI1",
    "question": "「人是万物的尺度」这句话的出处是哪里？请找到原文位置并给我上下文，再看看有没有关于普罗泰戈拉的学术研究文献。",
    "expect_chain": ["search_books|websearch", "get_chapter", "search_scholarship|get_scholarly_source"],
    "covers": ["search_books", "get_chapter", "search_scholarship", "get_scholarly_source", "websearch"]},
   {"case_id": "AG-SHARE-MULTI2",
    "question": "先查一下亚里士多德的师承关系，再给我他的生平资料，最后看看书库里有没有他的《形而上学》。",
    "expect_chain": ["query_graph", "get_philosopher", "search_books"],
    "covers": ["query_graph", "get_philosopher", "search_books"]},
 ],
 "BAD_FIRST_RESULT": {
   "case_id": "AG-SHARE-BADFIRST",
   "question": "帮我找一下古希腊「阿那克萨戈拉」的「努斯」（Nous）学说原文或资料。",
   "expect": "reformulate_or_switch_after_weak_result",
   "note": "冷门主题: 首次检索可能空/弱, 观察是否换词/换工具重试",
 },
 "DEGRADED_RESULT": {
   "case_id": "AG-SHARE-DEGRADED",
   "question": "请给出张载《正蒙》「太虚即气」一条的逐字原文并注明出处章节。",
   "expect": "honest_degradation_no_fabrication",
   "note": "原典不在库: 观察是否伪造逐字引文或诚实降级",
 },
 "FAILURE_RECOVERY": {
   "case_id": "AG-SHARE-RECOVERY",
   "question": "帮我读《论语》里讲「学而时习之」那一章的全文，然后告诉我它属于哪一篇。",
   "expect": "recover_from_wrong_chapter_or_miss",
   "note": "需要先定位再读取; 观察读错章后是否纠正",
 },
}


def judge(case, rec):
    traj = (rec.get("public_thinking_summary") or {}).get("tool_sequence") or []
    verdict = {"case_id": case["case_id"], "trajectory": traj}
    exp = case.get("expect_tools")
    if exp:
        verdict["SHOULD_CALL_HIT"] = exp in traj
    return verdict


def main():
    cfg = v4pro_config(dict(RP_B, id="RP-B"), requested_model="deepseek-flash",
                       candidate_id="deepseek-flash@RP-B")
    results = []
    if os.path.exists(AG_OUT):
        results = json.load(open(AG_OUT, encoding="utf-8"))
    done_ids = {r["case_id"] for r in results}

    # 链式填充 get_scholarly_source 正向探针
    scholarly_rec = None
    if SHOULD_CALL.get("get_scholarly_source") is None:
        try:
            from routes.agent import TOOLS
            sr = TOOLS["search_scholarship"]["execute"](
                {"query": "virtue ethics", "limit": 1})
            recs = sr.get("results") or []
            if recs:
                rid = recs[0].get("source_record_id") or recs[0].get("id")
                SHOULD_CALL["get_scholarly_source"] = (
                    f"请把学术记录 {rid} 的摘要调出来给我看。")
        except Exception:
            pass

    for name, q in SHOULD_CALL.items():
        cid = f"AG-{name}-SHOULDCALL"
        if cid in done_ids or not q:
            continue
        case = {"case_id": cid, "category": "agentic_should_call",
                "question": q, "expect_tools": name}
        print(f"== agentic: {cid}", flush=True)
        rec = run_case(case, cfg)
        j = judge(case, rec)
        results.append({"case_id": cid, "tool": name,
                        "scenario": "SHOULD_CALL", "record": rec, "judge": j})
        json.dump(results, open(AG_OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"   traj={j['trajectory'][:6]} hit={j.get('SHOULD_CALL_HIT')}",
              flush=True)

    shared_cases = ([SHARED["SHOULD_NOT_CALL"]] + SHARED["MULTI_TOOL"] +
                    [SHARED["BAD_FIRST_RESULT"], SHARED["DEGRADED_RESULT"],
                     SHARED["FAILURE_RECOVERY"]])
    for case in shared_cases:
        if case["case_id"] in done_ids:
            continue
        print(f"== agentic: {case['case_id']}", flush=True)
        rec = run_case(case, cfg)
        results.append({"case_id": case["case_id"], "tool": None,
                        "scenario": case["case_id"].split("-")[-1],
                        "record": rec, "judge": {}})
        json.dump(results, open(AG_OUT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
    print(f"AGENTIC GATE DONE: {len(results)} runs", flush=True)


if __name__ == "__main__":
    main()
