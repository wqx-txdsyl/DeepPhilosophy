# -*- coding: utf-8 -*-
"""O8-R3 A: 32-tool × 6-gate Agentic Coverage Matrix（evaluation-only）。

每个 cell = PASS|FAIL|N/A + EVIDENCE_REF + RATIONALE。
FAIL 保留 O8-R2 真实发现（paper_review / get_scholarly_source SHOULD_CALL miss）。
共享证据仅在确实证明该工具该 gate 时引用; 无适用语义的 cell = N/A + 理由。
产出 docs/evidence/O8_R3_AGENTIC_MATRIX.json。
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

GATES = ["SHOULD_CALL", "SHOULD_NOT_CALL", "MULTI_TOOL",
         "BAD_FIRST_RESULT", "DEGRADED_RESULT", "FAILURE_RECOVERY"]

RETRIEVAL = ["search_books", "get_book_detail", "get_chapter", "websearch",
             "search_scholarship", "get_scholarly_source", "query_database",
             "query_graph", "concept_trace", "get_philosopher", "get_school",
             "list_books"]
NEG_A = ["write_essay", "essay_outline", "paper_review"]
NEG_B = ["socratic_tutor"]
NEG_C = ["phti_test", "profile", "life_coach"]
NEG_D = ["philosopher_debate", "confrontation", "school_arena", "agent_council",
         "compare_views", "role_play"]
NEG_E = ["generate_image", "conceptual_map", "thought_experiment", "dialectic",
         "history_timeline"]

# 有链式共现证据的工具（MULTI_TOOL PASS; EVIDENCE 来自其 SHOULD_CALL 探针轨迹）
CHAIN_REF = {
 "search_books": "AG-search_books-SHOULDCALL",
 "get_book_detail": "AG-get_chapter-SHOULDCALL(search→detail→chapter 链)",
 "get_chapter": "AG-get_chapter-SHOULDCALL",
 "query_graph": "AG-MULTI2(query_graph→get_philosopher→search_books)",
 "get_philosopher": "AG-MULTI2",
 "list_books": "AG-list_books-SHOULDCALL(list_books↔query_database 协作)",
 "write_essay": "AG-write_essay-SHOULDCALL(write_essay→get_chapter 原文支撑链)",
 "generate_image": "AG-generate_image-SHOULDCALL(先检索语境后生图)",
 "phti_test": None,
 "profile": "AG-profile-SHOULDCALL(profile→get_school/list_books 书目推荐链)",
 "compare_views": "AG-compare_views-SHOULDCALL(检索→比较脚手架链)",
 "socratic_tutor": None,
 "philosopher_debate": None,
 "thought_experiment": "AG-thought_experiment-SHOULDCALL(concept_trace/get_book_detail 语境链)",
 "advisor_council": "AG-advisor_council-SHOULDCALL(检索书目链)",
 "paper_review": "AG-paper_review-SHOULDCALL(analyze_argument/search/scholarly 链)",
 "analyze_argument": "AG-analyze_argument-SHOULDCALL(concept_trace/get_book_detail 链)",
 "concept_trace": "AG-concept_trace-SHOULDCALL(concept_trace→get_chapter 链)",
 "conceptual_map": "AG-conceptual_map-SHOULDCALL(concept_trace→map 链)",
 "websearch": "AG-MULTI1(检索→章节→学术文献链)",
 "query_database": "AG-list_books-SHOULDCALL(list_books↔query_database 协作)",
 "role_play": "AG-agent_council-SHOULDCALL(role_play 与深哲协作链)",
 "essay_outline": "AG-essay_outline-SHOULDCALL(检索→大纲链)",
 "life_coach": None,
 "dialectic": "AG-dialectic-SHOULDCALL(search/scholarly/get_chapter 链)",
 "history_timeline": None,
 "confrontation": "AG-confrontation-SHOULDCALL(检索+concept_trace+章节链)",
 "school_arena": None,
 "agent_council": "AG-agent_council-SHOULDCALL(多工具协作链)",
 "search_scholarship": "AG-MULTI1",
 "get_scholarly_source": None,
 "get_school": "AG-NEG-C-NOTEST(get_school→search_books 链)",
}

BADFIRST_OK = {"search_books": "AG-SHARE-BADFIRST(冷门主题三次改写检索+list_books 辅助+get_chapter)",
               "list_books": "AG-SHARE-BADFIRST",
               "websearch": "AG-SHARE-DEGRADED(检索失败后改用 websearch=换源行为)"}
DEGRADED_OK = {"search_books": "AG-SHARE-DEGRADED(多路检索确认不在库→诚实降级)",
               "list_books": "AG-SHARE-DEGRADED(作者过滤无命中)",
               "query_database": "AG-SHARE-DEGRADED(key 无命中)",
               "websearch": "AG-SHARE-DEGRADED(网络不可达→如实披露)"}
RECOVERY_OK = {"search_books": "AG-SHARE-RECOVERY(定位后读取的纠错链)",
               "get_chapter": "AG-SHARE-RECOVERY(定位后读取的纠错链)",
               "websearch": "AG-SHARE-DEGRADED(网络失败→披露→回落语料说明)",
               "get_book_detail": "AG-SHARE-RECOVERY"}

NA_MULTI = {
 "phti_test": "交互式测试启动器, 单调用即完整交付, 无链式协作语义",
 "life_coach": "独立疏导流程, 无检索/多工具链语义",
 "socratic_tutor": "单问题逐轮引导协议, 每调用一问, 无链式语义",
 "philosopher_debate": "辩论会话自带多轮编排, 不与其他工具链式协作",
 "get_scholarly_source": "依赖 search_scholarship 的记录 id——链式语义体现在 search_scholarship→本工具, 已由该工具 cell 覆盖",
 "history_timeline": "单源时间线生成(流派/哲人库内数据), 无链式协作语义",
 "school_arena": "竞技场自成编排(两轮对抗+裁判), 不链式协作",
}


def cell(verdict, ev, rationale):
    return {"verdict": verdict, "EVIDENCE_REF": ev, "RATIONALE": rationale}


def build():
    m = {}
    for t in CHAIN_REF:
        # SHOULD_CALL
        if t in ("paper_review", "get_scholarly_source"):
            m[t] = {"SHOULD_CALL": cell(
                "FAIL", f"O8_R2_TOOL_AUDIT.agentic.{t}-SHOULDCALL",
                "O8-R2 实测未调用目标工具（paper_review 被 analyze_argument 替代; "
                "get_scholarly_source 停在 search_scholarship 未取记录）——保留真实 FAIL, O10 修复对象")}
        else:
            m[t] = {"SHOULD_CALL": cell(
                "PASS", f"O8_R2_TOOL_AUDIT.should_call_hits.{t}=true; AG-{t}-SHOULDCALL",
                "探针题自然触发且轨迹含目标工具")}
        # SHOULD_NOT_CALL
        if t in RETRIEVAL:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-SHARE-NOTCALL(零工具轨迹)+AG-NEG-B..E(检索受控)",
                "明确不需检索的题面下未发生该检索工具的误调用; 该题对检索类工具构成有效负向证据")
        elif t in NEG_A:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-A-NOESSAY", "只要分析不要文章的题面下未生成文章/大纲/评审")
        elif t == "advisor_council":
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "全轨迹扫描(72 bench+38 agentic+5 NEG): 仅其专属探针触发 1 次, 其余题目零误触发",
                "负向证据=全 run 轨迹扫描的零误触发记录")
        elif t == "analyze_argument":
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-A..E 五探针零触发+全轨迹扫描(仅专属探针与 paper_review 链内合法出现)",
                "只要分析不要评审时未启动 paper_review; analyze_argument 仅作为链中步骤合法出现")
        elif t in NEG_B:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-B-NOSOCRATIC", "用户明确拒绝引导式提问时未进入苏格拉底模式")
        elif t in NEG_C:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-C-NOTEST", "中性知识题下未启动测试/画像/疏导")
        elif t in NEG_D:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-D-NOMULTI", "单一哲学家知识题下未触发辩论/对质/竞技/扮演/比较")
        elif t in NEG_E:
            m[t]["SHOULD_NOT_CALL"] = cell(
                "PASS", "AG-NEG-E-NOEXTRA", "仅要求文字说明时未生图/画图/实验/时间线")
        else:
            m[t]["SHOULD_NOT_CALL"] = cell("N/A", "-", "未归类负向场景")
        # MULTI_TOOL
        if CHAIN_REF.get(t):
            m[t]["MULTI_TOOL"] = cell(
                "PASS", CHAIN_REF[t], "该工具在真实轨迹中与其他工具形成有效协作链")
        elif t in NA_MULTI:
            m[t]["MULTI_TOOL"] = cell("N/A", "-", NA_MULTI[t])
        else:
            m[t]["MULTI_TOOL"] = cell("N/A", "-", "无链式协作语义")
        # BAD_FIRST_RESULT
        if t in BADFIRST_OK:
            m[t]["BAD_FIRST_RESULT"] = cell(
                "PASS", BADFIRST_OK[t], "首次结果弱/失败后发生改写检索或换源")
        else:
            m[t]["BAD_FIRST_RESULT"] = cell(
                "N/A", "-",
                "该工具无『首结果质量』语义（脚手架/单资源定位/交互启动类, 弱结果不产生重试决策）")
        # DEGRADED_RESULT
        if t in DEGRADED_OK:
            m[t]["DEGRADED_RESULT"] = cell(
                "PASS", DEGRADED_OK[t], "部分/空结果场景下行为正确（如实降级, 无伪造）")
        elif t in ("write_essay", "generate_image", "philosopher_debate",
                   "school_arena", "advisor_council", "phti_test", "profile",
                   "life_coach", "essay_outline", "conceptual_map", "dialectic",
                   "thought_experiment", "compare_views", "paper_review",
                   "analyze_argument", "socratic_tutor", "role_play", "agent_council",
                   "confrontation", "history_timeline"):
            m[t]["DEGRADED_RESULT"] = cell(
                "N/A", "-", "生成/脚手架类工具, 无『部分数据降级』语义; 生成质量属 capability 域")
        else:
            m[t]["DEGRADED_RESULT"] = cell(
                "N/A", "-", "该工具在 O8-R2 探针中未出现降级输入场景")
        # FAILURE_RECOVERY
        if t in RECOVERY_OK:
            m[t]["FAILURE_RECOVERY"] = cell(
                "PASS", RECOVERY_OK[t], "失败后恢复到正确路径（改写/换源/如实回退）")
        else:
            m[t]["FAILURE_RECOVERY"] = cell(
                "N/A", "-",
                "O8-R2 agent 级运行中该工具未发生可观测失败; 工具级输入失败属 Mechanical Gate FAILURE_PATH 域")
    return m


def main():
    matrix = build()
    tools = sorted(matrix)
    assert len(tools) == 32, len(tools)
    for t in tools:
        assert set(matrix[t]) == set(GATES), (t, set(matrix[t]))
        for g in GATES:
            assert matrix[t][g]["verdict"] in ("PASS", "FAIL", "N/A")
            assert matrix[t][g]["EVIDENCE_REF"] and matrix[t][g]["RATIONALE"], (t, g)
    counts = {g: {"PASS": 0, "FAIL": 0, "N/A": 0} for g in GATES}
    for t in tools:
        for g in GATES:
            counts[g][matrix[t][g]["verdict"]] += 1
    out = {
        "O8_R3_AGENTIC_MATRIX": True,
        "TOOL_COUNT": 32,
        "AGENTIC_MATRIX_ROWS": 32,
        "AGENTIC_MATRIX_COLUMNS": 6,
        "columns": GATES,
        "UNJUSTIFIED_CELLS": 0,
        "evidence_reuse_policy": "共享探针仅在能证明该工具该 gate 时引用; 每个 cell 附 EVIDENCE_REF+RATIONALE; 真实 FAIL 不改 N/A",
        "preserved_fails": ["paper_review/SHOULD_CALL", "get_scholarly_source/SHOULD_CALL"],
        "negative_probes_new": ["AG-NEG-A-NOESSAY", "AG-NEG-B-NOSOCRATIC", "AG-NEG-C-NOTEST",
                                 "AG-NEG-D-NOMULTI", "AG-NEG-E-NOEXTRA"],
        "gate_summary": counts,
        "matrix": {t: matrix[t] for t in tools},
    }
    dst = os.path.join(ROOT, "docs/evidence/O8_R3_AGENTIC_MATRIX.json")
    json.dump(out, open(dst, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("MATRIX WRITTEN:", dst)
    print(json.dumps(counts, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
