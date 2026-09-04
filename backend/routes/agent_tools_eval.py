# -*- coding: utf-8 -*-
"""评估/分析工具域——agent 拆分模块 5/6（R2-2/S21, 2026-08-18 复审）

工具: phti_test / compare_views / socratic_tutor / advisor_council / paper_review /
analyze_argument / profile / conceptual_map / essay_outline / life_coach / dialectic /
history_timeline / confrontation / school_arena / agent_council（15 个）。
代码从 routes/agent.py 原样搬移（不改逻辑）; 注册到 agent_core.TOOLS（import 本模块即注册）。
"""
import json, os, re
from concurrent.futures import ThreadPoolExecutor

from routes.agent_core import (
    TOOLS, register_tool, _int_arg, PUBLIC, SCHOOLS_DIR,
    _mem_slot, _save_agent_memory,
)
from routes.agent_llm import llm_chat
from routes.agent_tools_memory import _debate_map_text   # school_arena 演变图（memory 域共享）

# ── 工具 10: phti_test（哲学人格测试——游戏化, 对话中触发）──
PHTI_QUESTIONS = None
def _load_phti():
    global PHTI_QUESTIONS
    if PHTI_QUESTIONS is None:
        p = PUBLIC.parent / "src" / "data" / "phti_questions.json"
        if p.exists():
            PHTI_QUESTIONS = json.load(open(p, encoding="utf-8"))
        else:
            PHTI_QUESTIONS = []
    return PHTI_QUESTIONS

def _exec_phti_test(args):
    import random
    qs = _load_phti()
    if not qs:
        return {"error": "题库缺失"}
    picked = random.sample(qs, min(5, len(qs)))
    out = []
    for i, q in enumerate(picked):
        out.append({"no": i + 1, "text": q.get("text", ""),
                    "dimension": q.get("dimension", ""), "direction": q.get("direction", "")})
    return {"questions": out, "instruction": "请依次回答每题的倾向（A=非常同意 B=同意 C=中立 D=不同意 E=非常不同意）"}

register_tool(
    "phti_test",
    "哲学人格测试（PHTI）——出 5 道维度题, 用于判断用户哲学倾向（斯多葛/存在主义/功利主义等）。",
    {"type": "object", "properties": {}, "required": []},
    _exec_phti_test,
)

# ── 高级工具（V2+）──
# Phase T（T3）: compare_views 从"一次调用生成完整对比成品"重构为 comparison scaffold——
# 工具只产出比较结构/轴线/候选主张, 最终结论由主 Agent 结合 Evidence Contract 二次综合。
def _exec_compare(args):
    from tool_contracts import scaffold_result, extract_json
    a = (args.get("a") or "").strip()
    b = (args.get("b") or "").strip()
    if not a or not b:
        return {"error": "需要两个对比对象"}
    focus = (args.get("focus") or "").strip()   # 可选: 对比焦点（问题维度）
    # 检索双方 + 合检（三方材料; 结构化引用随产物返回, 供主 Agent 核验后进入 Evidence Contract）
    r1 = TOOLS["search_books"]["execute"]({"query": a, "limit": 4})
    r2 = TOOLS["search_books"]["execute"]({"query": b, "limit": 4})
    r3 = TOOLS["search_books"]["execute"]({"query": f"{a} {b}", "limit": 4})
    ctx = json.dumps({"a_materials": r1.get("results", [])[:4],
                      "b_materials": r2.get("results", [])[:4],
                      "both_materials": r3.get("results", [])[:4]},
                     ensure_ascii=False)[:6000]
    # 内部 LLM 只产生 scaffold（JSON 结构）, 不产生 ready-to-render essay
    prompt = (f"为「{a}」与「{b}」的比较分析生成结构脚手架（comparison scaffold）。"
              f"{('用户指定的比较焦点: ' + focus + '。') if focus else ''}"
              f"只输出 JSON（不要 markdown 围栏, 不要解释文字）, 结构:\n"
              f'{{"shared_problem": "二者共同面对的哲学问题（1-2句）",\n'
              f' "comparison_axes": [{{"axis": "比较维度名", "side_a": "{a}在此维度（≤50字）", "side_b": "{b}在此维度（≤50字）", "why_it_matters": "该维度为何关键（1句）"}}],\n'
              f' "side_a_claims": [{{"claim": "{a}的可辩护主张", "basis": "检索材料/哲学史依据（不编造引文, 没有就写 reasoning）", "strength": "强在何处"}}],\n'
              f' "side_b_claims": [同上结构, 属于{b}],\n'
              f' "strongest_divergence": "最根本的分歧点（1-2句, 指向不可通约处而非表面差异）",\n'
              f' "evidence_needs": ["主 Agent 综合前最好补核的证据/原典定位（可空）"],\n'
              f' "candidate_consequences": ["若接受某一方, 会引出的理论后果（各1句, 不下最终结论）"]}}\n'
              f"要求: 2-4 个 comparison_axes; 每侧 2 条 claims; 各字段文字务必紧凑（防输出截断）;\n"
              f"严格基于检索材料与可靠哲学史, 不编造引文;\n"
              f"你不得给出最终胜负判断——那是主 Agent 的职责。\n\n检索材料:\n{ctx}")
    scaffold = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=2200)
        scaffold = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        scaffold = None
    if not isinstance(scaffold, dict):
        # 兜底: 检索材料直接给最小脚手架（无 LLM 成品）
        scaffold = {"shared_problem": f"{a} 与 {b} 在「{focus or '相关哲学问题'}」上的立场差异与各自依据",
                    "comparison_axes": [], "side_a_claims": [], "side_b_claims": [],
                    "strongest_divergence": "",
                    "evidence_needs": ["LLM scaffold 生成失败——请主 Agent 直接基于两侧检索材料自行建构比较轴线"],
                    "candidate_consequences": []}
    # 引用（结构化, 供主 Agent 核验后使用——不自动生成成品引用文案; 携带 snippet
    # 使引擎侧证据入池后可参与 used_evidence 片段对齐, 否则正式引用无法通过终检）
    citations, seen = [], set()
    for r in (r1, r2, r3):
        for item in r.get("results", [])[:3]:
            k = (item.get("book_title"), item.get("chapter_title"))
            if k not in seen:
                seen.add(k)
                citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx"),
                                  "author": item.get("author", ""),
                                  "snippet": (item.get("snippet") or "")[:220]})
    axes = scaffold.get("comparison_axes") or []
    ret = scaffold_result(
        "comparison_scaffold",
        f"{a} vs {b} 的比较脚手架: {len(axes)} 条比较轴线 + 双方候选主张; 最终判断由主 Agent 综合",
        confidence=0.65 if axes else 0.4,
        presentation_hint="结构化中间产物——主 Agent 须结合证据契约与用户问题二次综合后作答, 不得直接照搬为最终对比表",
        shared_problem=scaffold.get("shared_problem", ""),
        comparison_axes=axes[:6],
        side_a_claims=(scaffold.get("side_a_claims") or [])[:4],
        side_b_claims=(scaffold.get("side_b_claims") or [])[:4],
        strongest_divergence=scaffold.get("strongest_divergence", ""),
        evidence_needs=(scaffold.get("evidence_needs") or [])[:5],
        candidate_consequences=(scaffold.get("candidate_consequences") or [])[:5],
        side=a, side_a=a, side_b=b,
        citations=citations[:8])
    return ret

register_tool("compare_views",
    "生成两个哲学家/概念的比较分析结构（comparison scaffold: 共同问题/比较轴线/双方候选主张/最根本分歧/证据需求/候选后果），供主 Agent 结合证据二次综合——不直接产出最终对比成品或胜负结论。用于'休谟和康德对因果的看法有何不同'类问题。",
    {"type": "object", "properties": {
        "a": {"type": "string", "description": "对比对象一（哲学家/概念）"},
        "b": {"type": "string", "description": "对比对象二"},
        "focus": {"type": "string", "description": "比较焦点（用户强调的问题维度, 可选）"}},
     "required": ["a", "b"]},
    _exec_compare)

# Phase T（T6）: socratic_tutor 从"一次生成 4 轮追问"重构为 stateful one-turn skill——
# ONE CALL = ONE QUESTION。会话状态存 per-user 记忆槽 _mem_slot()["socratic"]。
SOCRATIC_TURN_PROMPT = """你是苏格拉底（Socrates）——只提问, 不直接给答案。

对话进展:
- 话题: 「{topic}」
- 本轮序号: 第 {round_no} 问
{user_reply_line}{history_line}
任务: 基于对方{target_phrase}推进一步——诊断其隐含假设, 只设计下一个问题。

要求:
① 恰好一个问题（一个问号; 可以有简短的铺垫语, 但核心追问只能有一个）;
② 问题必须逼近对方{target_phrase2}的一个具体前提, 拒绝泛泛而问;
③ 禁止说教、禁止给答案、禁止心灵鸡汤、禁止预告后面几轮要问什么;
④ 输出 JSON（不要 markdown 围栏）:
{{"diagnosed_assumption": "对方当前立场的隐含假设（1句）",
  "next_question": "下一个问题（含 ≤40 字铺垫）",
  "question_purpose": "这个问题要逼出什么（1句）"}}

原典背景（可参考, 若无命中则不引用）:
{retrieval}"""

def _exec_socratic(args):
    from tool_contracts import scaffold_result, extract_json
    topic = args.get("topic", "").strip()
    user_reply = (args.get("user_reply") or args.get("answer") or "").strip()
    if not topic:
        return {"error": "缺少话题"}
    result = TOOLS["search_books"]["execute"]({"query": topic[:50], "limit": 3})
    retrieval = json.dumps(result, ensure_ascii=False)[:3000]
    # 会话状态（per-user）: 记录话题/已问问题/用户最新回答——下一问必须依赖用户真实回答
    slot = _mem_slot()
    sess = slot.get("socratic") or {}
    if sess.get("topic") != topic:
        sess = {"topic": topic, "round": 0, "asked": [], "last_reply": ""}
    round_no = int(sess.get("round", 0)) + 1
    prev_asked = sess.get("asked", [])[-3:]
    if user_reply:
        sess["last_reply"] = user_reply[:400]
    reply_line = (f"- 对方最新回答: 「{sess['last_reply'][:300]}」\n" if sess.get("last_reply") else "- 对方尚未回答（这是第一问）\n")
    history_line = ""
    if prev_asked:
        history_line = ("- 已问过的问题（不得重复问）:\n" +
                        "\n".join(f"  {i+1}. {q[:80]}" for i, q in enumerate(prev_asked)) + "\n")
    prompt = SOCRATIC_TURN_PROMPT.format(topic=topic, round_no=round_no,
                                         user_reply_line=reply_line, history_line=history_line,
                                         target_phrase=(f"的最新回答「{sess.get('last_reply', '')[:200]}」"
                                                        if sess.get("last_reply") else "的立场"),
                                         target_phrase2=("在本次回答中" if sess.get("last_reply") else ""),
                                         retrieval=retrieval)
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.75, max_tokens=600)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict) or not data.get("next_question"):
        # 兜底: 从纯文本中提取第一个问句, 保证"恰好一个问题"
        raw = ""
        try:
            raw = (resp["choices"][0]["message"].get("content") or "").strip()
        except Exception:
            pass
        m = re.search(r"[^。！？\n]{4,160}[？?]", raw)
        data = {"diagnosed_assumption": "", "next_question": m.group(0).strip() if m else "你说这话时, 心里把它当作什么?",
                "question_purpose": "暴露隐含前提"}
    nq = data.get("next_question", "").strip()
    # 硬约束: 只保留第一个问号及其所在句（防止模型齐发多问）
    qm = re.search(r"[？?]", nq)
    if qm:
        tail = nq[qm.end():]
        if tail.strip():
            nq = nq[:qm.end()]   # 截掉第一问之后的所有内容
    sess["round"] = round_no
    sess["asked"] = (sess.get("asked", []) + [nq])[-6:]
    sess["awaiting_reply"] = True
    slot["socratic"] = sess
    _save_agent_memory()
    return scaffold_result(
        "socratic_turn",
        f"第 {round_no} 问——用户可见内容只有 next_question; 用户回答后再次调用并传 user_reply 推进下一问",
        confidence=0.7,
        presentation_hint="只向用户展示 next_question（可带极简铺垫）; 不展示 diagnosed_assumption/question_purpose; 严禁预生成后续轮次",
        diagnosed_assumption=data.get("diagnosed_assumption", ""),
        next_question=nq,
        question_purpose=data.get("question_purpose", ""),
        state_update={"round": round_no, "topic": topic,
                      "awaiting_user_reply": True,
                      "note": "用户回答后再次调用本工具并传 user_reply=用户的回答"})

register_tool("socratic_tutor",
    "苏格拉底式思辨引导（每次调用只返回一个问题）——诊断对方隐含假设并给出下一个追问; 用户回答后再次调用并传 user_reply=用户的回答以推进。ONE CALL = ONE QUESTION, 不预生成后续轮次（用于'不要告诉我答案, 只问我一个问题'类请求）。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "话题/对方的观点"},
        "user_reply": {"type": "string", "description": "用户对上一问的回答（第二轮起必须传, 下一问必须依赖它）"}},
     "required": ["topic"]},
    _exec_socratic)

# Phase T（T2）: advisor_council 从"成品建议文"改为 perspectives scaffold——
# 各视角作为候选材料, 综合判断与呈现由主 Agent 完成。
def _exec_council(args):
    from tool_contracts import scaffold_result, extract_json
    question = args.get("question", "")
    prompt = (f"用户面临决策/困惑: 「{question}」\n请召集 3 位智者给出多视角建议, 只输出 JSON（不要围栏）:\n"
              f'{{"perspectives": [{{"advisor": "亚里士多德（实践智慧/中道）", "advice": "100字内的建议", "assumes": "该建议预设了用户在乎什么"}},\n'
              f'  {{"advisor": "斯多葛（可控与不可控）", "advice": "…", "assumes": "…"}},\n'
              f'  {{"advisor": "存在主义（本真选择）", "advice": "…", "assumes": "…"}}],\n'
              f' "tensions": ["三种视角之间真实的张力点（各1句, 不和稀泥）"],\n'
              f' "synthesis_hint": "综合的可能方向（1句, 只是提示不下结论）"}}\n'
              f"你不得替用户做最终决定——那是主 Agent 结合语境的职责。用中文。")
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict):
        data = {"perspectives": [], "tensions": [], "synthesis_hint": "多视角生成失败——请主 Agent 自行展开三种视角"}
    return scaffold_result(
        "perspectives_scaffold",
        "三种思维模型的多视角建议脚手架: 视角/预设/张力点/综合提示; 最终建议由主 Agent 综合",
        confidence=0.65,
        presentation_hint="结构化中间产物——主 Agent 按用户处境裁剪呈现, 不得原样罗列了事",
        council=data)

register_tool("advisor_council",
    "智者内阁——召集亚里士多德/斯多葛/存在主义三种思维模型, 对人生决策/困惑生成多视角建议脚手架（视角/预设/张力点/综合提示）, 供主 Agent 结合语境综合。",
    {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    _exec_council)

# Phase T（T8）: paper_review 与 analyze_argument 职责切分——
#   analyze_argument = 单个论证的逻辑结构（短论证的"评审"可合法路由到此）;
#   paper_review     = 完整 essay/paper 的整体同行评审（thesis/结构/证据/反驳/写作/贡献）。
# paper_review 不再做"300字毒舌模板", 返回 structured review, 展示深度由主 Agent 决定。
def _exec_paper_review(args):
    from tool_contracts import scaffold_result, extract_json
    text = args.get("text", "")
    if not text:
        return {"error": "缺少待评审文本"}
    prompt = (f"以严格的哲学同行评审（peer review）身份评审以下文本, 只输出 JSON（不要围栏）:\n"
              f'{{"genre_judgment": "这是完整论文/短论证/片段——一句话判断",\n'
              f' "thesis": {{"statement": "作者的核心论点（忠实重构）", "clarity": "清晰/含混+一句说明", "originality": "贡献点"}}\n'
              f' "structure": {{"strengths": ["结构上成立之处"], "weaknesses": ["结构性弱点（章节衔接/比重/递进）"]}},\n'
              f' "evidence": {{"use": "引用与证据的使用质量", "gaps": ["缺了哪些关键证据或反例"]}},\n'
              f' "strongest_objection": "对论文整体最强的外部反驳（1-2句）",\n'
              f' "writing": "表达层面一句话（不评文采上下）",\n'
              f' "contribution": "若修改到位, 该文可能的价值（1句）",\n'
              f' "priority_actions": ["按重要性排序的 2-3 条修改动作"]}}\n'
              f"注意: thesis/structure/evidence 等键放在同一层（上面的换行只是排版）; 语气直接但建设性; 不替作者重写。\n\n"
              f"文本:\n{text[:3000]}")
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.6, max_tokens=1000)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict):
        data = {"genre_judgment": "评审结构化生成失败", "thesis": {"statement": "", "clarity": "", "originality": ""},
                "structure": {"strengths": [], "weaknesses": []}, "evidence": {"use": "", "gaps": []},
                "strongest_objection": "", "writing": "", "contribution": "",
                "priority_actions": ["评审生成失败——请主 Agent 直接基于文本自行评审"]}
    return scaffold_result(
        "structured_review",
        "完整论文的结构化同行评审: thesis/结构/证据/最强反驳/修改优先级; 展示深度由主 Agent 按用户请求决定",
        confidence=0.7,
        presentation_hint="结构化中间产物——主 Agent 按用户要求裁剪展示（'评审'二字≠全文照搬）",
        review=data)

register_tool("paper_review",
    "完整论文/文章的整体同行评审（thesis/结构/证据/最强反驳/修改优先级的结构化产物）——输入为较完整 essay/paper 时使用; 只给一个短论证时 analyze_argument 更合适。展示深度由主 Agent 决定。",
    {"type": "object", "properties": {"text": {"type": "string", "description": "待评审的完整论文/文章"}}, "required": ["text"]},
    _exec_paper_review)

# ═══════════════════════════════════════════════════════
# V3 工具: analyze_argument / concept_trace / profile / conceptual_map
# ═══════════════════════════════════════════════════════

# ── 工具: analyze_argument（论证结构分析——拆骨架, 找薄弱点; Phase T: 结构化产物）──
def _exec_analyze_argument(args):
    from tool_contracts import scaffold_result, extract_json
    text = args.get("text", "").strip()
    if not text:
        return {"error": "缺少待分析论证"}
    prompt = (f"以分析哲学方法拆解以下论证, 只输出 JSON（不要围栏）:\n"
              f'{{"conclusion": "结论（明确写出）",\n'
              f' "premises": [{{"premise": "前提内容", "kind": "explicit/implicit"}}],\n'
              f' "hidden_assumptions": ["未说出但论证依赖的假设"],\n'
              f' "fallacies": [{{"name": "谬误/弱点名称", "where": "落在哪个前提", "why": "一句话"}}],\n'
              f' "weakest_point": "最薄弱的一步（1句, 指明断点位置）",\n'
              f' "strengthening": ["如何补强前提或修改结论（1-2条）"]}}\n'
              f"只评论证质量不评文采; 你不做最终'评分/裁决'——评价语由主 Agent 结合语境给出。\n\n文本:\n{text[:3000]}")
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.6, max_tokens=900)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict):
        data = {"conclusion": "", "premises": [], "hidden_assumptions": [], "fallacies": [],
                "weakest_point": "", "strengthening": ["结构化生成失败——请主 Agent 直接拆解"]}
    return scaffold_result(
        "argument_structure",
        "论证的逻辑结构脚手架: 结论/前提(显隐)/隐含假设/谬误/最薄弱一步/补强建议",
        confidence=0.7,
        presentation_hint="结构化中间产物——主 Agent 按用户指令重排（如'先最致命问题, 再加强方法'）, 不照搬编号模板",
        argument=data)

register_tool("analyze_argument",
    "单个论证的逻辑结构分析（结论/前提显隐/隐含假设/谬误/最薄弱一步/补强建议）——针对一段论证或短文本; '分析一下这段话''帮我看看这个论证'或对短论证说'评审'时使用; 完整论文的整体评审用 paper_review。",
    {"type": "object", "properties": {"text": {"type": "string", "description": "待分析的论证文本"}}, "required": ["text"]},
    _exec_analyze_argument)

# ── 工具: profile（个性化哲学画像——基于当前问题的即时画像 + 真实推荐）──
def _exec_profile(args):
    question = (args.get("question") or "").strip()[:200]
    if not question:
        return {"error": "缺少问题"}
    book_hits = TOOLS["search_books"]["execute"]({"query": question[:50], "limit": 6}).get("results", []) or []
    book_names = ", ".join({f"《{(r.get('book_title') or '')}》·{(r.get('author') or '')}" for r in book_hits[:6]})
    prompt = (f"基于用户当前问题「{question}」输出哲学画像（450字内, 结构化）:\n"
              f"① 关注领域: 涉及哪些哲学问题域（认识论/伦理学/存在论/政治哲学…）\n"
              f"② 方法论倾向: 更像哪个传统（理性主义/经验主义/实用主义/存在主义/斯多葛…）, 一句话依据\n"
              f"③ 可能感兴趣的流派\n"
              f"④ 推荐书目: 优先从以下真实书目中选 2-3 本（可另补充必读经典）: {book_names or '（原典库命中较少, 推荐哲学入门经典）'}\n"
              f"⑤ 建议下一步深挖的问题（1 个）。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
    return {"profile_text": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("profile",
    "个性化哲学画像——分析用户当前问题的哲学倾向, 推荐真实书目与下一步方向（人生顾问/学习路径的基础）。",
    {"type": "object", "properties": {"question": {"type": "string", "description": "用户当前关注的问题/话题"}}, "required": ["question"]},
    _exec_profile)

# ── 工具: conceptual_map（Phase T/T5: 通用关系图——结构化 graph + 确定性 Mermaid renderer）──
# QG2/Q13 教训: 旧实现只会"概念→哲学家/流派/著作"关联脑图, 用户要"感性→知性→范畴…"环节图时
# 被主 Agent 整体架空（合规性调用）。新实现支持 MAP_TYPE 全谱系; Mermaid 只是 renderer——
# 由确定性 renderer 从 graph structure 生成（引号/括号 escaping、节点 id、edge syntax）,
# 不再让内部 LLM 自由手写未经验证的 Mermaid。
def _exec_conceptual_map(args):
    from tool_contracts import (scaffold_result, render_mermaid, validate_mermaid,
                                infer_map_type, MAP_TYPES, extract_json)
    concept = (args.get("concept") or args.get("focus") or "").strip()
    if not concept:
        return {"error": "缺少中心概念/焦点（focus）"}
    map_type = (args.get("map_type") or "").strip().upper()
    if map_type not in MAP_TYPES:
        map_type = infer_map_type(f"{concept} {args.get('constraints', '')}")
    directionality = (args.get("directionality") or "").strip().lower()
    constraints = (args.get("constraints") or "").strip()
    nodes_in = [n for n in (args.get("nodes") or []) if isinstance(n, (str, dict)) and n]
    rels_in = [r for r in (args.get("relations") or []) if isinstance(r, dict)]

    def _node_id(n):
        return n.get("id") or n.get("label") if isinstance(n, dict) else str(n)

    graph = None
    source = "user_specified"
    # ① 用户显式给出节点+关系 → 确定性构图（不经 LLM 手写）, LLM 仅在缺 label 时可补注
    if nodes_in and rels_in:
        seen = set()
        nodes = []
        for n in nodes_in:
            nid = _node_id(n)
            if not nid or nid in seen:
                continue
            seen.add(nid)
            label = n.get("label") or nid if isinstance(n, dict) else str(n)
            group = n.get("group") or "" if isinstance(n, dict) else ""
            note = n.get("note") or "" if isinstance(n, dict) else ""
            nodes.append({"id": nid, "label": f"{label}｜{note}" if note else label, "group": group})
        edges = []
        for r in rels_in[:20]:
            a, b = r.get("from"), r.get("to")
            if a in seen and b in seen and a != b:
                edges.append({"from": a, "to": b, "label": (r.get("label") or r.get("relation") or "").strip()})
        if nodes and edges:
            graph = {"nodes": nodes, "edges": edges}
    # ② 未给出完整结构 → 检索 + 内部 LLM 只产生 graph JSON（不产生 Mermaid 文本）
    if graph is None:
        source = "retrieval_llm"
        r_books = TOOLS["search_books"]["execute"]({"query": concept, "limit": 6}).get("results", []) or []
        r_phils = TOOLS["query_database"]["execute"]({"table": "philosophers", "key": concept, "limit": 4}).get("results", []) or []
        r_schools = TOOLS["query_database"]["execute"]({"table": "schools", "key": concept, "limit": 3}).get("results", []) or []
        r_net = TOOLS["query_database"]["execute"]({"table": "network", "key": concept, "limit": 4}).get("results", []) or []
        ctx = json.dumps({"books": [{"book": r.get("book_title"), "author": r.get("author"),
                                     "chapter": r.get("chapter_title"), "snippet": (r.get("snippet") or "")[:80]}
                                    for r in r_books[:6]],
                          "philosophers": r_phils[:4], "schools": r_schools[:3], "network": r_net[:4]},
                         ensure_ascii=False)[:4000]
        type_guide = {
            "CONCEPT_NETWORK": "概念关联网络: 中心概念与相关概念/哲学家/流派/著作的关联",
            "PROCESS_FLOW": "过程流: 按推进顺序的环节/阶段（箭头=先后/产生关系, 环节即用户给出的链条）",
            "ARGUMENT_GRAPH": "论证图: 节点=主张/论证步骤, 边=前提→结论的支持/反驳依赖",
            "HISTORICAL_GENEALOGY": "历史谱系: 按时间先后的人物/流派/著作传承",
            "PERSON_RELATION": "人物关系: 师承/论敌/影响/对话关系",
            "SYSTEM_ARCHITECTURE": "体系结构: 理论体系的组成部分与功能关系",
        }[map_type]
        prompt = (f"为「{concept}」构建{type_guide}。只输出 JSON（不要围栏, 不要输出 Mermaid——渲染由系统完成）:\n"
                  f'{{"nodes": [{{"id": "短id（中文可）", "label": "节点显示文本", "group": "可选分组"}}],\n'
                  f' "edges": [{{"from": "节点id", "to": "节点id", "label": "关系/依赖说明（可空）"}}]}}\n'
                  f"约束: 节点 ≤ 12, 边 ≤ 16; 严格基于检索结果与可靠哲学史, 不编造; "
                  f"节点 label 不要包含英文双引号。"
                  + (f"\n用户对图的约束（必须遵守）: {constraints}" if constraints else "")
                  + f"\n\n检索结果:\n{ctx}")
        data = None
        try:
            resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=900)
            data = extract_json(resp["choices"][0]["message"].get("content"))
        except Exception:
            data = None
        if isinstance(data, dict) and data.get("nodes"):
            ids = {n.get("id") for n in data.get("nodes", []) if isinstance(n, dict) and n.get("id")}
            nodes = [{"id": n["id"], "label": n.get("label") or n["id"], "group": n.get("group") or ""}
                     for n in data.get("nodes", [])[:12] if isinstance(n, dict) and n.get("id")]
            edges = [e for e in (data.get("edges") or [])[:16]
                     if isinstance(e, dict) and e.get("from") in ids and e.get("to") in ids
                     and e.get("from") != e.get("to")]
            graph = {"nodes": nodes, "edges": edges}
    if not graph or not graph.get("nodes"):
        # 兜底: 单节点最小图（主 Agent 可感知生成失败并自行处理）
        graph = {"nodes": [{"id": concept, "label": concept, "group": ""}], "edges": []}
    mermaid = render_mermaid(graph, map_type)
    vres = validate_mermaid(mermaid, graph)
    return scaffold_result(
        "graph_map",
        f"{map_type} 关系图: {len(graph['nodes'])} 节点 / {len(graph['edges'])} 边; mermaid 已由确定性 renderer 生成并 parse 验证",
        confidence=0.8 if vres["ok"] else 0.5,
        presentation_hint=("图已渲染验证通过——直接采用返回的 mermaid 渲染, 不要自行改写节点/连线/括号格式; "
                           "图后按用户要求给简短读法"),
        map_type=map_type,
        directionality=directionality or ("directed" if map_type in ("PROCESS_FLOW", "ARGUMENT_GRAPH") else "undirected"),
        graph=graph,
        mermaid=f"```mermaid\n{mermaid}\n```" if mermaid else "",
        map_text=f"```mermaid\n{mermaid}\n```" if mermaid else "",   # 兼容旧消费方字段名
        format="mermaid",
        mermaid_validation=vres,
        source=source,
        constraints_applied=constraints)

register_tool("conceptual_map",
    "通用哲学关系图（MAP_TYPE: CONCEPT_NETWORK 概念网络 / PROCESS_FLOW 过程流 / ARGUMENT_GRAPH 论证依赖图 / HISTORICAL_GENEALOGY 历史谱系 / PERSON_RELATION 人物关系 / SYSTEM_ARCHITECTURE 体系结构）——返回结构化 graph + 已验证的 Mermaid 渲染。支持传入用户给定的 nodes[]/relations[]（如'感性→知性→范畴'链条）。'画图/思维地图/概念关联/论证依赖图'类请求用本工具, 星图是结构图不是艺术画（不要用 generate_image）。",
    {"type": "object", "properties": {
        "concept": {"type": "string", "description": "中心概念/人物/主题"},
        "map_type": {"type": "string", "enum": ["CONCEPT_NETWORK", "PROCESS_FLOW", "ARGUMENT_GRAPH", "HISTORICAL_GENEALOGY", "PERSON_RELATION", "SYSTEM_ARCHITECTURE"], "description": "图类型（按用户请求选择）"},
        "nodes": {"type": "array", "items": {"type": "string"}, "description": "用户指定的节点序列（可选, 如[感性,知性,范畴]）"},
        "relations": {"type": "array", "items": {"type": "object", "properties": {"from": {"type": "string"}, "to": {"type": "string"}, "label": {"type": "string"}}}, "description": "用户指定的关系（可选）"},
        "constraints": {"type": "string", "description": "用户对图的额外约束（可选）"},
        "directionality": {"type": "string", "description": "directed/undirected（可选）"}},
     "required": ["concept"]},
    _exec_conceptual_map)

# ═══════════════════════════════════════════════════════
# V4 工具: essay_outline / life_coach / dialectic / history_timeline
# ═══════════════════════════════════════════════════════

# ── 工具: essay_outline（论文大纲——先骨架后成文）──
def _exec_essay_outline(args):
    topic = (args.get("topic") or "").strip()
    if not topic:
        return {"error": "缺少题目"}
    result = TOOLS["search_books"]["execute"]({"query": topic[:50], "limit": 6})
    retrieval = json.dumps(result, ensure_ascii=False)[:4000]
    prompt = (f"为题目「{topic}」生成论文大纲（600字内, 结构化）:\n"
              f"① 中心论点（一句话）\n② 引言思路\n③ 3-4 个分论点, 每个附: 论证要点 + 可引用的原典（从以下检索结果中选真实书目与章节）\n"
              f"④ 反方观点与回应\n⑤ 结论方向\n\n原典检索结果（用于分论点支撑）:\n{retrieval}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
    return {"outline": (resp["choices"][0]["message"].get("content") or "").strip(),
            "note": "如需按此大纲写全文, 用户说'按大纲写全文'即可"}

register_tool("essay_outline",
    "论文大纲生成（USER_REQUESTED_ARTIFACT——大纲本身就是用户请求的产物, 可输出完整结构）: 题目/方向 → 中心论点/引言/分论点(带原典支撑)/反方回应/结论。用于'帮我列个大纲''论文骨架'类请求。",
    {"type": "object", "properties": {"topic": {"type": "string", "description": "论文题目/研究方向"}}, "required": ["topic"]},
    _exec_essay_outline)

# ── 工具: life_coach（结构化人生疏导——情绪→认知→二分法→重构）──
def _exec_life_coach(args):
    question = (args.get("question") or "").strip()[:300]
    if not question:
        return {"error": "缺少困惑描述"}
    prompt = (f"作为融合斯多葛主义与认知行为疗法(CBT)的哲学人生教练, 对用户的困惑进行结构化疏导（700字内）:\n"
              f"用户困惑: 「{question}」\n\n"
              f"① 情绪识别: 用户此刻最可能的情绪与核心焦虑是什么（具体命名）\n"
              f"② 认知检测: 是否存在认知扭曲（灾难化/非黑即白/过度概括/读心术/夸大或贬低）——具体指出, 给反例\n"
              f"③ 斯多葛二分: 把问题拆成可控与不可控, 不可控的如何放下\n"
              f"④ 重构建议: 一个可立即执行的行动 + 一个可长期练习的思维习惯\n"
              f"语气温和而坚定, 不说教, 不灌鸡汤。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.75, max_tokens=1100)
    return {"coach": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("life_coach",
    "结构化人生疏导（斯多葛 + CBT）——情绪识别→认知扭曲检测→可控/不可控二分→行动重构。用于'我焦虑/迷茫/纠结'类求助。",
    {"type": "object", "properties": {"question": {"type": "string", "description": "用户的困惑/焦虑/处境描述"}}, "required": ["question"]},
    _exec_life_coach)

# ── 工具: dialectic（Phase T/T4: 矛盾运动分析——去固定正反合模板）──
# QG2/Q10 教训: 旧实现内部 prompt 强制"①正题②反题③合题"三段标题, 无视 args 中
# 传入的用户约束（contract violation）。新实现:
#   ① 用户对形式的约束经 constraints 参数真正进入执行层 prompt（主 Agent 必须透传）;
#   ② 产物字段动态存在（按问题需要）, 禁止固定 Thesis/Antithesis/Synthesis 标题;
#   ③ 工具产物本身就必须满足"不机械正反合"——不依赖主 Agent 事后救回。
DIALECTIC_FIELDS = ("initial_concept", "internal_tension", "self_negation",
                    "transformation", "new_determination", "residual_tension")

def _exec_dialectic(args):
    from tool_contracts import scaffold_result, extract_json
    topic = (args.get("topic") or "").strip()[:200]
    if not topic:
        return {"error": "缺少议题"}
    constraints = (args.get("constraints") or "").strip()
    prompt = (f"用辩证法剖析议题「{topic}」——把矛盾当作概念自身的运动, 而不是两个现成立场的并置。\n"
              f"从以下字段中选取该问题真正需要的（3-6 个; 不需要的字段不要输出, 也不要用别的名字硬凑三段式）:\n"
              f"- initial_concept: 起点概念及其素朴形态\n"
              f"- internal_tension: 概念内部自我分裂的张力（不在两个外在对立物之间）\n"
              f"- self_negation: 概念按自身逻辑走向的自我否定\n"
              f"- transformation: 否定中被保留与被颠覆的成分（扬弃的真实机制）\n"
              f"- new_determination: 更高层面的新规定\n"
              f"- residual_tension: 新规定仍未消解的剩余张力（辩证运动不设终点）\n"
              f"只输出 JSON（不要围栏）, 键名只用上述字段名。禁止输出'正题/反题/合题/Thesis/Antithesis/Synthesis'任何变体作为标题或键名。\n"
              + (f"用户对呈现形式的约束（必须逐条遵守, 优先级高于一切默认形式）: {constraints}\n" if constraints else "")
              + "避免和稀泥: 每个字段都必须推进思想的运动。用中文。")
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict) or not data:
        data = {"internal_tension": "辩证运动生成失败——请主 Agent 直接自行剖析",
                "residual_tension": ""}
    # 硬约束: 净化任何漏网的固定三段式标签（键含标签 → 整键丢弃; 值含标签 → 无条件移除）
    banned = re.compile(r"正题|反题|合题|Thesis|Antithesis|Synthesis", re.I)
    cleaned, violated = {}, []
    for k, v in data.items():
        if banned.search(str(k)):
            violated.append(str(k))
            continue
        vs = str(v)
        if k in DIALECTIC_FIELDS:
            vs = banned.sub("", vs)
            vs = re.sub(r"^[\s：:，,、.。\-—]*(第[一二三四]?[、.：:]?)?", "", vs)
            vs = re.sub(r"^[（(]\s*[）)]", "", vs)
        cleaned[k] = vs
    fields_used = [k for k in DIALECTIC_FIELDS if k in cleaned and cleaned[k]]
    return scaffold_result(
        "dialectical_movement",
        f"辩证运动分析（动态字段: {', '.join(fields_used) or '见载荷'}）——结构化中间产物, 主 Agent 须以连续论述呈现而非填空",
        confidence=0.7,
        presentation_hint="以连续的概念运动论述呈现（不是标签填空）; 用户若要求特定形式, 以 constraints 为准",
        movement=cleaned,
        fields_used=fields_used,
        constraints=constraints,
        template_labels_removed=violated)

register_tool("dialectic",
    "辩证矛盾运动分析——返回动态结构字段（initial_concept/internal_tension/self_negation/transformation/new_determination/residual_tension, 按问题需要取舍）, 不使用固定'正题—反题—合题'模板。用户对形式的约束（如'不要用正反合标签'）必须经 constraints 参数传入工具。用于'辩证地看XX''矛盾分析'类请求。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "待辩证分析的议题/观点"},
        "constraints": {"type": "string", "description": "用户对形式/标签的约束（必须原样透传, 如: 不要使用正题反题合题标签）"}},
     "required": ["topic"]},
    _exec_dialectic)

# ── 工具: history_timeline（哲学史时间线——流派/概念/哲人, 基于 DP 数据）──
def _exec_history_timeline(args):
    topic = (args.get("topic") or "").strip()[:100]
    if not topic:
        return {"error": "缺少主题"}
    school = TOOLS["get_school"]["execute"]({"name": topic})
    phils = TOOLS["query_database"]["execute"]({"table": "philosophers", "key": topic, "limit": 6})
    books = TOOLS["search_books"]["execute"]({"query": topic, "limit": 6})
    ctx = json.dumps({"school": school if not isinstance(school, dict) or "error" not in school else {},
                      "philosophers": phils.get("results", [])[:6],
                      "books": [{"book": b.get("book_title"), "author": b.get("author")}
                                for b in books.get("results", [])[:6]]},
                     ensure_ascii=False)[:4000]
    prompt = (f"基于以下数据, 为「{topic}」构建哲学史时间线（markdown 列表, 按时间先后排序, 每项格式: **时期** - 人物/事件 - 一句话说明）:\n"
              f"只使用数据中出现的内容, 不编造; 数据不足时如实说明。\n\n数据:\n{ctx}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
    return {"timeline": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("history_timeline",
    "哲学史时间线——流派/概念/哲人的历史脉络（基于哲学库流派时间线与哲人时代数据）。用于'存在主义的发展史''XX的时间线'类请求。",
    {"type": "object", "properties": {"topic": {"type": "string", "description": "流派/概念/哲人"}}, "required": ["topic"]},
    _exec_history_timeline)

# ═══════════════════════════════════════════════════════
# V5 工具: confrontation（哲学文献隔空对质——双方原文并排交锋）
# Phase T/T9 最低限度统一（QG2/Q09 表现良好, 不重写核心交互效果）:
#   ① textual claim（原文立场, 附检索依据）与 simulated reply（模拟交锋措辞）明确分离;
#   ② 结构化 citations/evidence 随产物返回 → 引擎侧入 Evidence Contract 查证池;
#   ③ 主 Agent 保留最终裁决权（裁判注只是候选, 结论由主 Agent 给出）。
# ═══════════════════════════════════════════════════════
def _exec_confrontation(args):
    from tool_contracts import scaffold_result, extract_json
    topic = (args.get("topic") or "").strip()[:80]
    a = (args.get("a") or "").strip()
    b = (args.get("b") or "").strip()
    if not (topic and a and b):
        return {"error": "需要 topic + a + b 三个参数"}
    # 各自精确检索: 作者+主题组合, 过滤出该作者的书
    ra = TOOLS["search_books"]["execute"]({"query": f"{a} {topic}", "limit": 8})
    rb = TOOLS["search_books"]["execute"]({"query": f"{b} {topic}", "limit": 8})
    fa = [r for r in ra.get("results", []) if a in (r.get("author") or "")][:3]
    fb = [r for r in rb.get("results", []) if b in (r.get("author") or "")][:3]
    ctx = json.dumps({"a": a, "a_original_texts": fa, "b": b, "b_original_texts": fb},
                     ensure_ascii=False)[:5000]
    prompt = (f"哲学文献'隔空对质': 就「{topic}」, 让 {a} 与 {b} 各自基于检索到的原文片段发表立场, 然后互相指出对方论证的软肋（哲学史上真实的交锋点, 如休谟对先验演绎的循环性指控）:\n"
              f"输出 JSON（不要围栏）, 结构:\n"
              f'{{"stance_a": {{"text": "{a} 的原文立场（引用标注【《书名》· 章节】, 只使用检索到的原文）", "basis": "支撑立场的关键原文依据（摘自检索片段, 有则填）"}},\n'
              f' "stance_b": {{"text": "{b} 的原文立场（同上）", "basis": "…"}},\n'
              f' "exchanges": ["交锋回合×2-3——模拟互驳措辞, 每条以\'模拟\'语态呈现（谁反打谁的哪一点, 是否刺中软肋）"],\n'
              f' "referee_note": "裁判注候选: 双方各自最强与最弱的一点, 以及可能的合题方向（明确标注是\'体系内\'还是\'后康德综合\'视角）——仅供主 Agent 裁决参考"}}\n'
              f"纪律: ①stance_a/stance_b 是 textual claim, 只能基于检索到的原文, 不得编造引文; "
              f"②exchanges 是模拟对话, 措辞必须让人能分辨这是构造的交锋而非原文引文; "
              f"③最终裁决由主 Agent 给出, 你不下胜负结论。\n"
              f"检索结果（含 snippet 原文片段）:\n{ctx}")
    data = None
    try:
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1400)
        data = extract_json(resp["choices"][0]["message"].get("content"))
    except Exception:
        data = None
    if not isinstance(data, dict) or not data.get("stance_a"):
        # 兜底: 沿用旧文本卡片形态（不阻断交互效果）
        reply = ""
        try:
            reply = (resp["choices"][0]["message"].get("content") or "").strip()
        except Exception:
            pass
        data = {"stance_a": {"text": reply or "对质生成失败", "basis": ""},
                "stance_b": {"text": "", "basis": ""},
                "exchanges": [], "referee_note": ""}
    evidence = []
    for r in fa + fb:
        if r.get("book_title"):
            evidence.append({"book": r.get("book_title"), "chapter": r.get("chapter_title"),
                             "book_id": r.get("book_id"), "chapter_idx": r.get("chapter_idx"),
                             "author": r.get("author", ""),
                             "snippet": (r.get("snippet") or "")[:220]})
    return scaffold_result(
        "confrontation_card",
        f"{a} 与 {b} 就「{topic}」的隔空对质卡片: textual stance + 模拟交锋 + 裁判注候选",
        confidence=0.7,
        presentation_hint="stance_a/stance_b 为 textual claim（引文须经主 Agent 核验后才能以【《书》·章】标注）; exchanges 为模拟交锋措辞, 须与原文立场分开呈现; 最终裁决由主 Agent 给出",
        stance_a=data.get("stance_a") or {}, stance_b=data.get("stance_b") or {},
        exchanges=(data.get("exchanges") or [])[:4],
        referee_note=data.get("referee_note", ""),
        citations=evidence[:8], evidence=evidence[:8],
        side_a=a, side_b=b)

register_tool("confrontation",
    "哲学文献隔空对质——两位哲学家就同一主题各自引用原文交锋（休谟vs康德、尼采vs黑格尔等），输出原文立场（textual claim）/模拟交锋/裁判注候选。用于'让XX和XX的原文对质'类请求。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "对质主题（如: 因果/自由意志）"},
        "a": {"type": "string", "description": "哲学家一"},
        "b": {"type": "string", "description": "哲学家二"}},
     "required": ["topic", "a", "b"]},
    _exec_confrontation)

# ═══════════════════════════════════════════════════════
# V6 工具: school_arena（哲学流派 PK 竞技场——随机双流派 × 当代热点对抗）
# ═══════════════════════════════════════════════════════
HOT_TOPICS = [
    "AI 是否应该拥有权利", "内卷还是躺平", "短视频让人更聪明还是更愚蠢",
    "996 是剥削还是奋斗", "虚拟现实会取代真实生活吗", "算法推荐是自由还是操控",
    "躺平是消极还是觉醒", "科技让人更孤独吗", "ChatGPT 会终结独立思考吗",
    "大数据时代还有隐私可言吗", "AI 创作是艺术吗", "消费主义是幸福陷阱吗",
]

def _school_profile(name):
    """流派档案（竞技场人格注入）: get_school 的定位/核心主张/代表哲人"""
    d = TOOLS["get_school"]["execute"]({"name": name})
    if isinstance(d, dict) and d.get("name"):
        parts = []
        if d.get("region"):
            parts.append(f"地域: {d['region']}")
        if d.get("subtitle"):
            parts.append(f"定位: {d['subtitle']}")
        if d.get("overview"):
            parts.append(f"核心主张: {d['overview'][:180]}")
        thinkers = d.get("thinkers") or []
        if thinkers:
            parts.append("代表哲人: " + "、".join(str(t) for t in thinkers[:5]))
        return "；".join(parts)
    return None

def _list_schools():
    """读取全部流派名（111 个）"""
    names = []
    if SCHOOLS_DIR.exists():
        for f in os.listdir(SCHOOLS_DIR):
            if f.endswith(".json"):
                try:
                    d = json.load(open(SCHOOLS_DIR / f, encoding="utf-8"))
                    if d.get("name"):
                        names.append(d["name"])
                except Exception:
                    pass
    return names

def _exec_school_arena(args):
    import random
    topic = (args.get("topic") or "").strip() or random.choice(HOT_TOPICS)
    schools = _list_schools()
    school_a = (args.get("school_a") or "").strip() or (random.choice(schools) if schools else "存在主义")
    pool = [s for s in schools if s != school_a] or schools
    school_b = (args.get("school_b") or "").strip() or (random.choice(pool) if pool else "功利主义")
    pa, pb = _school_profile(school_a), _school_profile(school_b)
    # 两轮对抗（流派代表发言人）
    debate = []
    for r in range(2):
        for name, profile in ((school_a, pa), (school_b, pb)):
            ctx = "\n".join(debate[-3:])
            inject = f"\n流派档案（发言必须体现该流派的核心主张与代表人物思想）:\n{profile}" if profile else ""
            prompt = (f"你是{name}学派的代表发言人。针对当代议题「{topic}」，发表你的立场与论证（200字内）。{inject}"
                      f"这是对抗第{r+1}轮。{'可回应对方发言, 指出其主张在当代的适用局限。' if ctx else '请先亮明核心立场。'}"
                      + (f"\n已有发言:\n{ctx}" if ctx else ""))
            resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=400)
            speech = (resp["choices"][0]["message"].get("content") or "").strip()
            debate.append(f"{name}: {speech}")
    # 裁判总结
    d_text = "\n".join(debate)
    sum_prompt = (f"作为哲学裁判, 总结「{school_a}」与「{school_b}」就「{topic}」的对抗（350字内）:\n"
                  f"①各自核心立场 ②交锋点（谁对谁的哪一点构成威胁）③哪个流派更贴合当代现实 ④可借鉴的综合（区分体系内/综合视角）。\n\n辩论:\n{d_text[:3000]}")
    sresp = llm_chat([{"role": "user", "content": sum_prompt}], temperature=0.7, max_tokens=800)
    summary = (sresp["choices"][0]["message"].get("content") or "").strip()
    return {"arena": {"topic": topic, "schools": [school_a, school_b], "debate": debate,
                      "summary": summary, "map_text": _debate_map_text(d_text)},
            "note": f"随机对决: {school_a} vs {school_b} · 议题: {topic}"}

register_tool("school_arena",
    "哲学流派 PK 竞技场——随机抽取两个流派就当代热点议题对抗（也可指定 topic/school_a/school_b）。输出两轮交锋 + 裁判总结 + 演变图。用于'流派PK/随机对决/让两个流派辩论'类请求。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "议题（缺省随机热点）"},
        "school_a": {"type": "string", "description": "流派一（缺省随机）"},
        "school_b": {"type": "string", "description": "流派二（缺省随机）"}},
     "required": []},
    _exec_school_arena)

# ═══════════════════════════════════════════════════════
# V7 工具: agent_council（多智能体协作——深哲×尼采协议对话）
# 深哲（通用 29 工具视角, 检索原典）与尼采（人格视角）就议题各自发言,
# 再由第三方综合两种视角的交汇与分歧——多智能体经"协议"协作的展示
# ═══════════════════════════════════════════════════════
def _exec_agent_council(args):
    topic = (args.get("topic") or "").strip()[:100]
    if not topic:
        return {"error": "缺少议题"}
    # ① 深哲发言（通用视角 + 原典检索）
    def _deep_speech():
        from engine_langgraph import get_system_prompt
        r = TOOLS["search_books"]["execute"]({"query": topic[:50], "limit": 4})
        mat = json.dumps(r, ensure_ascii=False)[:2500]
        r1 = llm_chat([{"role": "system", "content": get_system_prompt("general")},
                       {"role": "user", "content": f"议题: 「{topic}」。基于以下检索材料给出你的分析立场（250字内, 引用标注出处）:\n{mat}"}],
                      temperature=0.7, max_tokens=600)
        return (r1["choices"][0]["message"].get("content") or "").strip()
    # ② 尼采发言（人格视角）
    def _nietzsche_speech():
        import agents as agents_mod
        r2 = llm_chat([{"role": "system", "content": agents_mod.AGENT_PROMPTS.get("nietzsche", "")},
                       {"role": "user", "content": f"议题: 「{topic}」。以你的人格回应（250字内, 格言式, 不贴出处标注）"}],
                      temperature=0.85, max_tokens=600)
        return (r2["choices"][0]["message"].get("content") or "").strip()
    # ①② 并行执行（2026-08-14: 两次独立 LLM 调用并发, 总延迟减半）
    deep_speech = nietzsche_speech = ""
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1, f2 = ex.submit(_deep_speech), ex.submit(_nietzsche_speech)
        try:
            deep_speech = f1.result()
        except Exception as e:
            deep_speech = f"（深哲发言失败: {e}）"
        try:
            nietzsche_speech = f2.result()
        except Exception as e:
            nietzsche_speech = f"（尼采发言失败: {e}）"
    # ③ 综合（第三方视角的交汇与分歧; 依赖①②, 串行）
    synthesis = ""
    try:
        r3 = llm_chat([{"role": "user", "content": f"两位智能体就「{topic}」发言如下, 请综合（300字内）: ①各自立场 ②分歧的本质 ③可互补处。\n\n深哲: {deep_speech[:800]}\n\n尼采: {nietzsche_speech[:800]}"}],
                      temperature=0.6, max_tokens=800)
        synthesis = (r3["choices"][0]["message"].get("content") or "").strip()
    except Exception as e:
        synthesis = f"（综合失败: {e}）"
    return {"council": {"topic": topic, "deep": deep_speech, "nietzsche": nietzsche_speech, "synthesis": synthesis},
            "note": "深哲（通用·原典检索视角）与尼采（人格视角）的协议协作"}

register_tool("agent_council",
    "多智能体协作——深哲（通用视角, 检索原典）与尼采（人格视角）就同一议题各自发言, 再综合两种视角的交汇与分歧。用于'让深哲和尼采讨论XX'类请求。",
    {"type": "object", "properties": {"topic": {"type": "string", "description": "议题"}}, "required": ["topic"]},
    _exec_agent_council)
