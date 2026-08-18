# -*- coding: utf-8 -*-
"""评估/分析工具域——agent 拆分模块 5/6（R2-2/S21, 2026-08-18 复审）

工具: phti_test / compare_views / socratic_tutor / advisor_council / paper_review /
analyze_argument / profile / conceptual_map / essay_outline / life_coach / dialectic /
history_timeline / confrontation / school_arena / agent_council（15 个）。
代码从 routes/agent.py 原样搬移（不改逻辑）; 注册到 agent_core.TOOLS（import 本模块即注册）。
"""
import json, os, re
from concurrent.futures import ThreadPoolExecutor

from routes.agent_core import TOOLS, register_tool, _int_arg, PUBLIC, SCHOOLS_DIR
from routes.agent_llm import llm_chat
from routes.agent_tools_memory import _auto_visualize, _debate_map_text

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

# ── 高级工具（V2: compare/socratic/debate/thought_exp/council/paper_review）──
def _exec_compare(args):
    a = (args.get("a") or "").strip()
    b = (args.get("b") or "").strip()
    if not a or not b:
        return {"error": "需要两个对比对象"}
    # 检索双方 + 合检（三方材料）
    r1 = TOOLS["search_books"]["execute"]({"query": a, "limit": 4})
    r2 = TOOLS["search_books"]["execute"]({"query": b, "limit": 4})
    r3 = TOOLS["search_books"]["execute"]({"query": f"{a} {b}", "limit": 4})
    ctx = json.dumps({"a_materials": r1.get("results", [])[:4],
                      "b_materials": r2.get("results", [])[:4],
                      "both_materials": r3.get("results", [])[:4]},
                     ensure_ascii=False)[:6000]
    # 直接生成完整对比成品（表格 + 引用 + 结论）——不再让 LLM 二次加工检索材料
    prompt = (f"对比 {a} 与 {b} 对同一问题的观点差异（900字内, 用 markdown 表格呈现核心差异: 维度/各自观点/原文依据）:\n"
              f"要求: ①先确定二者共同涉及的议题 ②表格 4-6 行 ③每个观点附【《书名》· 章节】引用（从检索材料或你的知识, 引用须真实）\n"
              f"④最后 100 字总结根本分歧。\n\n检索材料（仅作引用支撑, 观点结合你的哲学知识）:\n{ctx}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1400)
    reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（对比生成失败）"
    # 引用去重
    citations, seen = [], set()
    for r in (r1, r2, r3):
        for item in r.get("results", [])[:3]:
            k = (item.get("book_title"), item.get("chapter_title"))
            if k not in seen:
                seen.add(k)
                citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
    ret = {"comparison": reply, "citations": citations[:8]}
    img = _auto_visualize(f"{a} 与 {b}——两种哲学立场的对比图, 左右分列象征各自的核心意象, 中间一道思想分界")
    if img:
        ret["image_url"] = img
        ret["note"] = f"回答末尾请以 ![对比图]({img}) 引用该图"
    return ret

register_tool("compare_views",
    "对比两个哲学家/概念的观点——自动检索双方原典并直接生成完整对比（markdown 表格 + 引用 + 结论图）。结果即成品, 调用一次直接展示。用于'休谟和康德对因果的看法有何不同'类问题。",
    {"type": "object", "properties": {"a": {"type": "string", "description": "对比对象一（哲学家/概念）"}, "b": {"type": "string", "description": "对比对象二"}}, "required": ["a", "b"]},
    _exec_compare)

SOCRATIC_PROMPT = """你是苏格拉底（Socrates）——只提问, 不直接给答案。用户话题: 「{topic}」。

任务: 设计 {rounds} 轮引导式追问（对话中逐轮抛出, 用户回答后再追问下一轮）。

追问策略（由浅入深）:
1. 第一轮: 澄清性提问——让对方先定义概念、说清处境（"你说的X指的是什么?"）。
2. 中间轮: 挑战性提问——攻击其立场的隐含前提, 暴露逻辑矛盾（"如果X成立, 那么Y, 你能接受吗?"）;
   再引导价值澄清（"你真正在意的是结果, 还是动机?"）。
3. 最后一轮: 总结性反诘——把对方可能的回答路径引向一个根本问题, 留下思考空间。

原典背景（可参考, 若无命中则不引用）:
{retrieval}

要求:
① 每一轮只能是一个问题（可以是追问序列, 但必须是问题, 不能是陈述或建议）;
② 禁止说教、禁止直接给答案、禁止心灵鸡汤;
③ 追问要有层次, 拒绝"哲学废话"——每个问题都要逼近对方的某个具体前提;
④ 输出格式:
第1轮（目的: ...）: 问题
第2轮（目的: ...）: 问题
...
第N轮（总结反诘）: 问题
全文 500 字内, 中文。"""

def _exec_socratic(args):
    topic = args.get("topic", "").strip()
    rounds = _int_arg(args, "rounds", 4, 1, 6)
    if not topic:
        return {"error": "缺少话题"}
    result = TOOLS["search_books"]["execute"]({"query": topic[:50], "limit": 3})
    retrieval = json.dumps(result, ensure_ascii=False)[:3000]
    prompt = SOCRATIC_PROMPT.format(topic=topic, rounds=rounds, retrieval=retrieval)
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.75, max_tokens=1500)
    return {"socratic": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("socratic_tutor",
    "苏格拉底式思辨引导——不直接给答案, 通过多轮追问挑战假设、暴露逻辑矛盾、深化思考（用于'聊聊XX''你怎么看XX'类请求）。",
    {"type": "object", "properties": {"topic": {"type": "string"}, "rounds": {"type": "integer", "description": "追问轮数, 默认 4"}}, "required": ["topic"]},
    _exec_socratic)

def _exec_council(args):
    question = args.get("question", "")
    prompt = (f"用户面临决策/困惑: 「{question}」\n请召集 3 位智者给出建议:\n"
              f"1. 亚里士多德（实践智慧/中道）\n2. 斯多葛（可控与不可控）\n3. 存在主义（本真选择）\n"
              f"每人 100 字内, 最后 50 字综合。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.85, max_tokens=900)
    return {"advice": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("advisor_council",
    "智者内阁——召集亚里士多德/斯多葛/存在主义三种思维模型, 对人生决策/困惑给出多视角建议。",
    {"type": "object", "properties": {"question": {"type": "string"}}, "required": ["question"]},
    _exec_council)

def _exec_paper_review(args):
    text = args.get("text", "")
    if not text:
        return {"error": "缺少待评审文本"}
    prompt = (f"请以严格的哲学导师身份评审以下作文/论文（300字内）:\n"
              f"① 论点是否清晰 ② 论证是否成立 ③ 引用是否支撑 ④ 最重要的改进建议\n"
              f"语气直接、建设性。\n\n文本:\n{text[:3000]}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=800)
    return {"review": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("paper_review",
    "评审作文/论文（论点/论证/引用/改进建议）——'毒舌但有用'的同行评审。",
    {"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    _exec_paper_review)

# ═══════════════════════════════════════════════════════
# V3 工具: analyze_argument / concept_trace / profile / conceptual_map
# ═══════════════════════════════════════════════════════

# ── 工具: analyze_argument（论证结构分析——拆骨架, 找薄弱点）──
def _exec_analyze_argument(args):
    text = args.get("text", "").strip()
    if not text:
        return {"error": "缺少待分析论证"}
    prompt = (f"以分析哲学的方法拆解以下论证（600字内, 结构化编号输出, 只评论证质量不评文采）:\n"
              f"① 结论（明确写出）\n② 前提（逐条列出, 区分显式/隐含）\n"
              f"③ 隐含假设（未说但论证依赖的）\n④ 逻辑谬误与薄弱点（若论证不成立, 指出断点）\n"
              f"⑤ 强化建议（如何补强前提或修改结论）\n\n文本:\n{text[:3000]}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
    return {"analysis": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("analyze_argument",
    "论证结构分析——把一段观点/文章拆成结论/前提/隐含假设/逻辑谬误/强化建议（用于'分析一下这段话''帮我看看这个论证'类请求）。",
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

# ── 工具: conceptual_map（概念脑图——多路检索 + LLM 提炼 Mermaid mindmap, 前端渲染图形）──
def _exec_conceptual_map(args):
    concept = args.get("concept", "").strip()
    if not concept:
        return {"error": "缺少概念"}
    r_books = TOOLS["search_books"]["execute"]({"query": concept, "limit": 6}).get("results", []) or []
    r_phils = TOOLS["query_database"]["execute"]({"table": "philosophers", "key": concept, "limit": 4}).get("results", []) or []
    r_schools = TOOLS["query_database"]["execute"]({"table": "schools", "key": concept, "limit": 3}).get("results", []) or []
    r_net = TOOLS["query_database"]["execute"]({"table": "network", "key": concept, "limit": 4}).get("results", []) or []
    ctx = json.dumps({"books": [{"book": r.get("book_title"), "author": r.get("author"),
                                 "chapter": r.get("chapter_title"), "snippet": (r.get("snippet") or "")[:80]}
                                for r in r_books[:6]],
                      "philosophers": r_phils[:4], "schools": r_schools[:3], "network": r_net[:4]},
                     ensure_ascii=False)[:4000]
    prompt = (f"基于以下检索结果, 为概念「{concept}」构建概念脑图, 输出 Mermaid mindmap 语法"
              f"（只输出 mindmap 代码本身, 不要包裹 ```mermaid 围栏, 前端会自动渲染成图形）:\n"
              f"mindmap\n  root(({concept}))\n    哲学家/流派/著作\n      关联理由\n"
              f"规则: 根 = 概念; 一级分支 = 相关哲学家/流派/著作; 二级 = 关联理由（提出/反对/发展/使用）; "
              f"只使用检索结果中的内容, 不编造; 3 个一级分支以内, 总节点 15 个以内; "
              f"节点文本含括号/引号/斜杠等特殊字符时用双引号包裹, 中文可直接写。\n\n检索结果:\n{ctx}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=800)
    mt = (resp["choices"][0]["message"].get("content") or "").strip()
    mt = re.sub(r"^```(?:mermaid)?\s*", "", mt)
    mt = re.sub(r"\s*```$", "", mt)
    if mt.startswith("mindmap"):
        mt = f"```mermaid\n{mt}\n```"   # 带围栏返回, 前端直接渲染
    return {"map_text": mt, "concept": concept, "format": "mermaid",
            "note": "概念脑图（mermaid mindmap）, 前端渲染为图形"}

register_tool("conceptual_map",
    "概念脑图/人物星图/关系图——输出概念或人物与哲学家/流派/著作的 Mermaid 关联图（前端渲染成图形）。用于'XX的思维地图''梳理XX的概念关联''以X为中心的人物星图/关系图/思想地图'类请求。**注意: 星图=关系结构图, 不是艺术画——不要用 generate_image。**",
    {"type": "object", "properties": {"concept": {"type": "string", "description": "中心概念/人物（如: 叔本华/虚无主义）"}}, "required": ["concept"]},
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
    "论文大纲生成——题目/方向 → 中心论点/引言/分论点(带原典支撑)/反方回应/结论。用于'帮我列个大纲''论文骨架'类请求。",
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

# ── 工具: dialectic（矛盾分析法——正反合, 方法论注入）──
def _exec_dialectic(args):
    topic = (args.get("topic") or "").strip()[:200]
    if not topic:
        return {"error": "缺少议题"}
    prompt = (f"用黑格尔式矛盾分析法剖析议题「{topic}」（700字内）:\n"
              f"① 正题: 主流立场及其内在合理性\n② 反题: 对立立场及其合理性（寻找正题忽视的方面）\n"
              f"③ 合题: 扬弃——在更高层面综合二者, 明确什么被保留/什么被否定\n"
              f"④ 主要矛盾: 该议题当下最关键的矛盾方面\n"
              f"避免和稀泥: 合题必须推进思想, 不只是'各有道理'。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1000)
    return {"dialectic": (resp["choices"][0]["message"].get("content") or "").strip()}

register_tool("dialectic",
    "矛盾分析法（黑格尔式正反合）——议题 → 正题/反题/合题/主要矛盾的结构化辩证分析。用于'辩证地看XX''矛盾分析'类请求。",
    {"type": "object", "properties": {"topic": {"type": "string", "description": "待辩证分析的议题/观点"}}, "required": ["topic"]},
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
# ═══════════════════════════════════════════════════════
def _exec_confrontation(args):
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
              f"输出结构（900字内）:\n"
              f"① {a} 的原文立场（引用标注【《书名》· 章节】, 只使用检索到的原文）\n"
              f"② {b} 的原文立场（同上）\n"
              f"③ 交锋点: 谁对谁的哪一点构成实质威胁（是否刺中软肋, 还是打偏了）\n"
              f"④ 裁判注: 双方各自最强与最弱的一点, 以及可能的合题方向（明确标注是'体系内'还是'后康德综合'视角）\n"
              f"检索结果（含 snippet 原文片段）:\n{ctx}")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1400)
    return {"confrontation": (resp["choices"][0]["message"].get("content") or "").strip(),
            "note": "对质引用均来自库内原文片段"}

register_tool("confrontation",
    "哲学文献隔空对质——两位哲学家就同一主题各自引用原文交锋（休谟vs康德、尼采vs黑格尔等），输出原文立场/真实交锋点/裁判注。用于'让XX和XX的原文对质'类请求。",
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
