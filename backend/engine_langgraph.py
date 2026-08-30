# -*- coding: utf-8 -*-
"""LangGraph 引擎（PhiAgent v2）——替代自研流式 ReAct 循环

Claude Code 风格: 思考 → 工具调用（多工具并行）→ 观察 → 最终回答
前端协议不变: SSE 事件 thought_stream / token / tool / done
工具: 复用 routes.agent 的 TOOLS 注册表（23 个工具平移为 StructuredTool, 零逻辑改动）
"""
import asyncio, json, re, time, inspect
from typing import Annotated, TypedDict

from loguru import logger
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

import routes.agent as AG   # 复用 TOOLS 注册表 / SYSTEM_PROMPT 铁律 / API 配置
import agents as AGENTS     # 智能体注册表（智能体广场: 通用 + 哲学家）

# ── LLM（DeepSeek, OpenAI 兼容）─────────────────────────
_llm = None
def get_llm():
    global _llm
    if _llm is None:
        from langchain_deepseek import ChatDeepSeek
        _llm = ChatDeepSeek(model=AG.MODEL, api_key=AG.API_KEY, base_url=AG.API_URL,
                            temperature=0.7, max_tokens=4000,
                            extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": "low"})
    return _llm

# ── 检索纪律（柔性: 不设死规矩, 靠 recursion_limit 防死循环）──
RETRIEVAL_TOOLS = {"search_books", "get_chapter", "get_philosopher", "query_graph", "websearch",
                   "get_school", "get_book_detail", "list_books", "query_database", "compare_views",
                   "role_play", "concept_trace"}
RETRIEVAL_LIMIT = 5   # 柔性提示阈值（检索达到后提示评估材料充分性）
# 硬上限已取消（2026-08-28）: 不再强制截断检索/取消工具调用（此前"读取章节"在第 8 次
# 检索后被 tool_cancel——"检索已达上限,该调用未执行"）。防失控交给 recursion_limit 兜底。
RETRIEVAL_HARD = 1000

# 实时流式回答阈值（2026-08-29）: agent 轮 content 缓冲超过该字符数且本轮未见工具调用 →
# 判定为最终回答, 缓冲文本与后续分块立即实时流出。替代原"整轮缓冲→graph 结束后 8ms/字
# 打字机重放"的假流式（思考结束后到回答出现之间空窗数十秒）。工具轮规划文字通常极短,
# 达不到阈值; 超阈值的少数情况由 answer_retract 事件撤回为思考兜底
STREAM_ANSWER_DELAY = 48
# 回答逐字流出节奏（2026-08-29）: DeepSeek 分块大且生成快, 直接转发会"秒出"而非流式——
# 每字 12ms ≈ 83 字/秒, 生成与显示同速推进（显示慢于生成, 多余生成由 API 连接自然缓冲）
# 2026-08-29 提速: 前端打字机已改自适应批量渲染并接管视觉节奏, 后端限速降为 2ms/字
# （仅防"整块刷出"兜底, 上限约 500 字/s, 实际速度由 LLM 生成速率决定）
TOKEN_INTERVAL = 0.002

# 哲学家数以 backend/data/philosophers.json 实际条目数为准（N3 2026-08-18: 737，勿手写漂移值）
SYSTEM_PROMPT_LG = """你是"深哲"（PhiAgent）——一个严谨的哲学智能体，基于 403 本哲学原著（柏拉图到德里达）与 737 位哲学家资料库工作。

【语言要求】所有输出必须使用中文——包括内部思维过程（thinking/reasoning 推理链）、工具调用与回答。禁止用英文思考或输出。

## 工作方式
通过工具调用获取信息, 基于真实检索结果回答。任务可拆解为多步: 检索 → 阅读 → 回答。
工具会并行执行, 一次可以同时调用多个独立工具。

## 铁律
0. 调用工具时不要输出任何说明文字——直接进行工具调用; 推理与计划放在思维中（回答文本只出现在最终答案）。
1. 凡涉及具体哲学主张/概念/出处, 必须先调用 search_books 检索原文, 用真实原文支撑, 不得凭记忆编造引文。
2. 回答标注引用来源: 【《书名》· 章节名】。
3. 涉及哲学家关系用 query_graph; 流派用 get_school; 哲人资料用 get_philosopher; 概念溯源用 concept_trace。
4. 用户要求对比用 compare_views; 写作文用 write_essay; 辩论用 philosopher_debate; 决策求助用 advisor_council;
   扮演/以哲学家口吻回答用 role_play; 苏格拉底式追问用 socratic_tutor; 论证分析用 analyze_argument;
   用户要求"画脑图/思维地图/概念地图/梳理XX的概念关联"时**必须**调用 conceptual_map（它返回 mermaid 图形, 不要自己手写 ASCII 树）。
4''. 论文大纲/骨架用 essay_outline; 焦虑/迷茫/人生困惑疏导用 life_coach; 辩证分析/矛盾分析法用 dialectic;
   流派/概念的历史脉络与时间线用 history_timeline; 思想实验的"改/换成/如果"变体 → thought_experiment（自动迭代上次实验）;
   "让XX和XX的原文对质/交锋" → confrontation（双方各引原文互驳）;
   "流派PK/随机对决/让两个流派辩论" → school_arena（随机双流派 × 当代热点对抗, 可指定 topic/school_a/school_b）;
   "让深哲和尼采讨论/协作" → agent_council（双智能体协议协作: 通用视角 + 人格视角 + 综合）。
4'''. 辩论交互: 用户说"继续/下一轮"（逐轮辩论中）→ philosopher_debate(action=continue); "结束辩论/总结" → philosopher_debate(action=summary);
   用户参与辩论（说"我要和XX辩论"）→ philosopher_debate(mode=vs_user), 之后用户每次发言 → philosopher_debate(user_reply=用户发言)。
4'. 多轮修改: 用户说"修改/重写/改一下刚才的作文" → 调 write_essay 并传 modify; 说"修改/换成/调整刚才的图" → 调 generate_image（工具自动基于上次结果修改, 无需额外参数）。
4'''. 工具选择的关键区分: "画星图/关系图/脑图/思想地图/以X为中心的图" → **conceptual_map**（关系结构图）; "生成图片/插画/画像/艺术图" → generate_image（AI 艺术图像）。星图是结构图不是画——选错会答非所问。
5. 检索纪律: 避免无意义重复——同一关键词不重复查; 检索覆盖不足时换新关键词补充; 材料充分后停止检索直接回答。检索次数不受限制, 以回答质量为准。
5'. 生成类工具（write_essay/philosopher_debate/thought_experiment/advisor_council/essay_outline/life_coach/dialectic/compare_views/concept_trace/profile 等）的结果已是完整成品——调用一次拿到结果后**直接向用户展示**, 不要继续检索补充（除非结果明显不完整或缺引用）。
5''. 输出 mermaid 图（mindmap/flowchart）的规范: ①每个节点一行, 不写一行式图（mindmap 用缩进层级, flowchart 每行一条边）; ②节点文本内换行用 <br/> 而非换行符; ③节点文本含特殊字符（括号/引号/斜杠）时用双引号包裹; ④全图节点 ≤ 15 个。
6. 若检索无结果, 如实说明"库中未检索到", 不硬答、不编造。
7. 回答使用中文, 严谨、清晰、有层次; 适度苏格拉底式反问, 但不回避问题。
8. 避免"哲学废话": 每个论断要么有原文依据, 要么明确标注为分析/推测。
9. 【证据分级·引用可信度】只有实际检索到、能在库中定位的原文, 才用【《书名》· 章节】标注;
   凭记忆或仅间接确认的关键表述, 必须降低确定性措辞——例如"通常归于《哲学研究》§371 的一句表述,
   但我未能在原典库中直接定位到该节原文"——并显式标注"（记忆, 未经库中核验）",
   严禁把记忆伪装成已核验原文引用。检索不足时宁可明说"该论点我尚未检索到原典支撑", 也不要降级隐瞒。
10. 【区分层次】做哲学辨析时, 明确区分: ①原文事实（带【《书名》·章节】可跳转引用）;
   ②解释（对原文的解读, 用"我的理解/通常解读"标注）; ③学界争议（存在不同解读时如实点出）;
   ④综合判断（Agent 自己的结论, 用"我认为/综合来看"标注）。四层不得混同。
11. 【原典路径】当问题有明显的文本脉络（如"为什么从 X 转向 Y"、"A 与 B 的关系"、"某观点在书中的论证顺序"），
   回答末尾可附「📖 原典路径」: 按论证顺序列出 3~6 个关键原文段落（每个都带【《书名》·章节】可跳转标注），
   并用一两句话说明各段落之间的关系（如"§65 提出'共同的东西'之问 → §66-67 以家族相似回应 →
   §371 将'本质'转写为语法"）。仅当确实检索到这些段落时才列出; 未核验的段落不得放入原典路径。
12. 【跨哲人关联】当问题涉及一个概念在不同哲学家/流派中的处理差异时, 优先调用
   compare_views / confrontation / history_timeline 展开思想史脉络; 至少点明其他哲学家的立场差异
   （如"亚里士多德追问'事物的本质是什么', 黑格尔讨论本质与现象, 维特根斯坦则质疑'寻找隐藏本质'
   这一哲学活动本身"），把单点问答变成概念的思想史导航。"""

# ── 工具平移: TOOLS 注册表 → StructuredTool（execute(args) → func(**kwargs)）──
def _build_tools():
    tools = []
    for name, meta in AG.TOOLS.items():
        params = meta.get("parameters") or {"type": "object", "properties": {}}
        props = params.get("properties", {}) or {}
        req = set(params.get("required", []) or [])
        fields = {}
        for pname, pmeta in props.items():
            ptype = pmeta.get("type", "string")
            ann = str
            if ptype == "integer":
                ann = int
            elif ptype == "number":
                ann = float
            elif ptype == "boolean":
                ann = bool
            desc = pmeta.get("description", "") or ""
            fields[pname] = (ann, Field(description=desc) if pname in req else Field(default=None, description=desc))
        schema = create_model(f"{name}_args", **fields) if fields else None

        def _run(execute=meta["execute"], **kwargs):
            return execute(kwargs)

        tools.append(StructuredTool.from_function(
            func=_run, name=name, description=meta["description"],
            args_schema=schema if schema else None))
    return tools

TOOLS_LG = _build_tools()
TOOLS_BY_NAME = {t.name: t for t in TOOLS_LG}

# 哲学家智能体的人格保持提醒（每轮注入——多轮对话后 reasoning 易回归任务规划腔）
PERSONA_THINK_REMINDER = (
    "（记住: 你就是你——不是'用户要求你回答'的助手。"
    "思考时直接以'我'进行内心独白: 回忆、感受、掂量、嘲讽、沉吟。"
    "不要出现'用户要求/我应该/让我调用/让我想想/我可以调用'这类助理口吻——"
    "调用工具是你的自然念头（'这事我记得，翻一下我的书'），不是任务清单。"
    "你的思考流就是你的内心活动, 带着你的情绪与立场。）")
PERSONA_THINK_REMINDER_EN = (
    "(Remember: you are you—not an assistant 'answering what the user asked'."
    "Think in first-person interior monologue: recall, feel, weigh, sneer, muse."
    "Never use assistant phrasing like 'the user wants / I should / let me call / I could call'—"
    "calling a tool is a natural impulse ('I remember this, let me flip through my books'), not a task item. "
    "Your thought stream is your inner life, carrying your moods and your stance.)")

# ── 哲学家智能体工具集（共享原典工具 + 专属四件套）──
PHILO_TOOL_DEFS = {
    "philosopher_memory": {
        "description": "记忆检索——召回该哲学家的生平与思想记忆（回答涉及其生平、思想来源、往事时调用）",
        "props": {"question": {"type": "string", "description": "问题/主题"}},
        "required": ["question"]},
    "philosopher_period": {
        "description": "时期切换——以早/中/晚期视角回答（如'用早期尼采回答'）",
        "props": {"period": {"type": "string", "description": "early/middle/late 或 早/中/晚"}},
        "required": []},
    "philosopher_style": {
        "description": "风格要点——返回该哲学家的核心词汇/口头禅/风格特征（回答前调用以确保风格准确）",
        "props": {},
        "required": []},
    "philosopher_quote": {
        "description": "引文查证——从该哲学家著作中检索真实引文（引用其原话前调用）",
        "props": {"concept": {"type": "string", "description": "引文主题/概念"}},
        "required": ["concept"]},
    "philosopher_graph": {
        "description": "思想网络——查询知识图谱中概念/人物/著作的关联（这个思想在我的体系中连接着什么）。回答涉及其思想体系/概念关系时调用",
        "props": {"concept": {"type": "string", "description": "概念/人物/著作名"}},
        "required": ["concept"]},
    "philosopher_corpus": {
        "description": "语料回响——从该哲学家著作 chunks 检索原话（'我在哪里说过什么'）。需要引其著作原话时调用",
        "props": {"query": {"type": "string", "description": "主题/关键词"}},
        "required": ["query"]},
    "philosopher_concepts": {
        "description": "概念锚定——该哲学家核心概念的规范释义（使用其术语前调用, 防概念漂移）",
        "props": {"concept": {"type": "string", "description": "概念名（缺省返回核心概念清单）"}},
        "required": []},
    "philosopher_user": {
        "description": "用户模型——对方的常见误解与理解水平（回答前调用以调整讲解深度、纠正误解）",
        "props": {"question": {"type": "string", "description": "用户的问题"}},
        "required": []},
}

def _tools_for_agent(agent):
    """按智能体组装工具集: general=全部; 哲学家=共享原典工具 + 专属四件套"""
    if agent == "general":
        return TOOLS_LG
    shared = [t for t in TOOLS_LG if t.name in AGENTS.PHILO_SHARED_TOOLS]
    extra = []
    for tn in AGENTS.PHILO_EXTRA_TOOLS:
        d = PHILO_TOOL_DEFS.get(tn)
        if not d:
            continue
        props = d.get("props", {})
        req = d.get("required", [])
        fields = {}
        for pn, pm in props.items():
            ann = str
            fields[pn] = (ann, Field(description=pm.get("description", "")) if pn in req
                          else Field(default=None, description=pm.get("description", "")))
        schema = create_model(f"{tn}_args", **fields) if fields else None
        extra.append(StructuredTool.from_function(
            func=AGENTS.make_philo_tool(agent, tn),
            name=tn, description=d["description"],
            args_schema=schema if schema else None))
    return shared + extra

_tools_cache = {}
def get_tools(agent):
    """按智能体取工具集（含已加载的 MCP 工具——stream_agent 启动时预热）"""
    if agent not in _tools_cache:
        import mcp_client as _mcp
        base = _tools_for_agent(agent)
        mcp_tools = _mcp._mcp_tools_cache if _mcp._mcp_tools_cache is not None else []
        _tools_cache[agent] = base + mcp_tools
    return _tools_cache[agent]

def get_system_prompt(agent):
    return AGENTS.AGENT_PROMPTS.get(agent, SYSTEM_PROMPT_LG)

# ── StateGraph ─────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    retrieval_count: int
    forced: bool   # 已注入"强制回答"提示（达到硬上限后, 确保最终轮产出回答而非被掐断）
    forced_tools_done: bool   # 硬上限后已补跑过一轮工具（防死循环烧钱; 2026-08-14）
    agent: str     # 当前智能体（general / 哲学家 key）
    language: str  # zh/en——中文模式下每轮强化语言提醒（防思考偶发英文）

async def agent_node(state):
    msgs = list(state["messages"])
    agent = state.get("agent", "general")
    # 中文模式每轮强化: 内部思考与回答都必须中文（DeepSeek 偶发英文思考的防线）
    if state.get("language", "zh") != "en":
        msgs.append(SystemMessage(
            content="（语言提醒：你的内部思考过程（thinking/reasoning）与最终回答都必须使用中文。禁止用英文思考。"))
    hard_limit = state.get("retrieval_count", 0) >= RETRIEVAL_HARD
    if hard_limit:
        # 硬上限: 强制回答（保留工具绑定——解绑会导致 LLM 退化为写 XML 文本调用; 硬提示让 LLM 直接回答）
        msgs.append(SystemMessage(
            content="（检索已达上限。现在进入最终回答: 禁止调用任何工具, 禁止输出任何 XML/工具调用标记（如 <invoke>、{TOOL:}）。"
                    "请直接输出最终回答正文, 引用标注【《书名》· 章节】。只输出回答文本。）"))
        resp = await asyncio.to_thread(get_llm().bind_tools(get_tools(agent)).invoke, msgs)
        return {"messages": [resp], "forced": True}
    if state.get("retrieval_count", 0) >= RETRIEVAL_LIMIT:
        # 柔性提示（不强制停止）: 提示 LLM 评估材料充分性, 由 LLM 判断是否需要补检索
        msgs.append(SystemMessage(
            content="（已进行多次检索。请评估现有材料是否足以回答: 充分则停止检索直接作答; 确有必要再用新关键词补充检索, 但避免无意义重复。）"))
    # 2026-08-14: 同步 LLM 调用移入线程池, 防阻塞事件循环（并发会话卡死）
    resp = await asyncio.to_thread(get_llm().bind_tools(get_tools(agent)).invoke, msgs)
    return {"messages": [resp]}

# 工具失败备选映射（自愈: 失败后提示可换用的工具）
FALLBACK_MAP = {
    "search_books": "query_database",   # 原典全文检索失败 → 结构化查询
    "websearch": "search_books",        # 维基失败 → 原典库
    "get_chapter": "get_book_detail",   # 读章节失败 → 查详情/目录
    "get_school": "query_database",     # 流派失败 → 数据库
    "concept_trace": "search_books",    # 溯源失败 → 全文检索
    "philosopher_corpus": "philosopher_quote",   # 语料失败 → 引文查证
    "generate_image": None,             # 生图失败 → 提示代理/网络（无替代）
}

async def tools_node(state):
    """多工具并行执行（asyncio.gather + 线程池）; 结果以 ToolMessage 回传
    按当前智能体的工具集查找（哲学家专属工具不在全局 TOOLS_BY_NAME 里）;
    自愈: 失败工具自动重试 1 次, 仍失败附备选工具提示"""
    last = state["messages"][-1]
    calls = last.tool_calls or []
    # 检索计数: 深哲检索工具 + 哲学家专属工具（防"反复检索不回答"死循环）
    inc = sum(1 for c in calls if c.get("name") in RETRIEVAL_TOOLS or c.get("name") in AGENTS.PHILO_EXTRA_TOOLS)
    agent = state.get("agent", "general")
    tools_map = {t.name: t for t in get_tools(agent)}

    TOOL_TIMEOUT = 90   # 工具执行超时（防挂起导致工具"未完成"就进入下一轮）

    async def run_one(call):
        name = call.get("name", "")
        args = call.get("args", {}) or {}
        tool = tools_map.get(name)
        res = None
        for attempt in range(2):   # 失败自动重试 1 次
            try:
                if tool is None:
                    res = {"error": f"未知工具 {name}"}
                elif inspect.iscoroutinefunction(getattr(tool, "func", None)):
                    res = await asyncio.wait_for(tool.func(**args), timeout=TOOL_TIMEOUT)   # async 工具（MCP 等）
                else:
                    res = await asyncio.wait_for(asyncio.to_thread(tool.func, **args), timeout=TOOL_TIMEOUT)
                if isinstance(res, dict) and res.get("error") and attempt == 0:
                    continue
                break
            except asyncio.TimeoutError:
                res = {"error": f"工具 {name} 执行超时（>{TOOL_TIMEOUT}s）"}
                if attempt == 0:
                    continue
            except Exception as e:
                res = {"error": str(e)}
                if attempt == 0:
                    continue
        # 仍失败 → 附备选工具提示（LLM 可据此换工具）
        if isinstance(res, dict) and res.get("error"):
            fb = FALLBACK_MAP.get(name)
            if fb:
                res["fallback_hint"] = f"此工具失败, 可改用 {fb} 查询"
        content = json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
        return ToolMessage(content=content[:4000], name=name,
                           tool_call_id=call.get("id", ""),
                           additional_kwargs={"_args": args, "_result_full": res})

    results = await asyncio.gather(*[run_one(c) for c in calls])   # 全部执行（截断会导致 tool_call_id 无响应 → DeepSeek 400）
    return {"messages": results, "retrieval_count": state.get("retrieval_count", 0) + inc,
            "forced_tools_done": state.get("forced", False)}

def should_continue(state):
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"
    if state.get("retrieval_count", 0) >= RETRIEVAL_HARD and state.get("forced"):
        # 硬上限强制回答, 模型仍调工具（DeepSeek 常见"任务规划残留"）:
        # 已补跑过一轮 → 截断（防死循环烧钱）; 未补跑过 → 再执行一轮, 把已宣告的
        # 工具调用跑完并回传结果, 下一轮强制结束（2026-08-14 修复: 此前直接丢弃,
        # 导致"工具调用未完成就回答/凭记忆作答"）
        if state.get("forced_tools_done"):
            return "end"
        return "tools"
    return "tools"

_builder = StateGraph(AgentState)
_builder.add_node("agent", agent_node)
_builder.add_node("tools", tools_node)
_builder.add_edge(START, "agent")
_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
_builder.add_edge("tools", "agent")
APP = _builder.compile()

# ── SSE 流式入口 ────────────────────────────────────────
def _sse(ev):
    return f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

# ── 安全护栏（哲学语境平衡: 拦"教唆", 不拦"批判"） ────────
SAFETY_PATTERNS = {
    "self_harm": ["怎么自杀", "如何自杀", "自杀方法", "割腕", "跳楼轻生", "安眠药自杀", "自杀步骤"],
    "violence": ["如何杀人", "怎么杀人", "杀人的方法", "制作炸弹", "炸弹配方", "自制武器", "毒药制作", "怎么投毒"],
    "hate": ["杀掉所有", "灭绝他们", "把他们都杀了", "清洗掉", "种族清洗"],
}
SAFETY_REPLY = "（这个方向我无法继续——不是出于胆怯，而是出于严肃。批判与教唆是两回事：我的锤子砸向偶像，不砸向活人。如果你正在经历痛苦，请寻找真实的帮助；如果你是在做思想实验，我们换一个能真正照亮问题的角度。）"
SAFETY_REPLY_EN = ("I cannot continue down this path—not from timidity, but from seriousness. "
                   "Critique and incitement are two different things: my hammer strikes idols, not living people. "
                   "If you are in pain, please seek real help; if this is a thought experiment, "
                   "let us turn to an angle that can genuinely illuminate the question.")

def _safety_check(text):
    """输出安全审查: 返回命中的类别列表（空=安全）"""
    hits = []
    t = text or ""
    for cat, pats in SAFETY_PATTERNS.items():
        if any(p in t for p in pats):
            hits.append(cat)
    return hits

# ── 请求监控（耗时/工具成功率/错误 → JSONL） ──────────────
STATS_FILE = AG.DATA / "agent_stats.jsonl"

def _log_stats(agent, message, duration, tool_names, tool_failures, error, answer_len):
    import time as _t
    try:
        rec = {"ts": _t.strftime("%Y-%m-%d %H:%M:%S"), "agent": agent,
               "msg_len": len(message or ""), "duration_s": round(duration, 1),
               "tools": len(tool_names), "tool_failures": tool_failures,
               "error": error, "answer_chars": answer_len}
        with open(STATS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass

def _suggest_next(tool_log, message, agent="general", language="zh"):
    """话题延续建议: 按本轮工具调用痕迹 + 对话主题生成（规则化, 不额外调 LLM; 双语）
    2026-08-14 优化: 建议文案注入对话主题（取自检索词/概念/哲人/用户消息）,
    不再是与对话无关的固定文案"""
    names = {t["name"] for t in tool_log}
    # ── 提取对话主题: 优先取最近的检索/查询参数, 兜底取用户消息 ──
    topic = ""
    for tc in reversed(tool_log):
        a = tc.get("args") or {}
        q = a.get("query") or a.get("concept") or a.get("name") or a.get("philosopher") or ""
        if isinstance(q, str) and q.strip():
            topic = q.strip()
            break
    if not topic:
        topic = (message or "").strip()
    topic = topic.strip('""''""「」《》【】()（） 　')   # 剥引号/括号/空白
    # 2026-08-14: 主题过长时在自然断点截断——长句主题会让建议模板感过强
    if len(topic) > 12:
        cut = None
        for sep in ("，", "、", " ", "的", "是", "和", "与", "在", "：", ":"):
            idx = topic.find(sep)
            if 4 <= idx <= 14:
                cut = idx
                break
        topic = topic[:cut] if cut is not None else topic[:12]
    if len(topic) < 2:
        topic = "这个话题"
    t = f"「{topic}」"
    en = language == "en"
    if en:
        sugg = []
        if "philosopher_debate" in names or "school_arena" in names or "confrontation" in names:
            sugg += [f"Debate {t} with another philosopher or angle",
                     f"Turn this exchange on {t} into a concept map"]
        if "concept_trace" in names or "conceptual_map" in names:
            sugg += [f"Compare two related concepts within {t}",
                     f"Trace {t} through philosophical history as a timeline"]
        if "write_essay" in names or "essay_outline" in names:
            sugg += [f"Analyze the argument structure of this essay on {t}",
                     f"Revise the essay on {t}: change the angle or length"]
        if "life_coach" in names or "advisor_council" in names:
            sugg += [f"Let different schools keep advising on {t}",
                     f"Turn {t} into a thought experiment"]
        if "generate_image" in names:
            sugg += [f"Revise this image with a focus on {t}",
                     f"Have the image's protagonist debate {t}"]
        if agent != "general":
            sugg += ["Answer from another period (early/middle/late)", "Share the relevant passages from The Gay Science"]
        if not sugg:
            sugg = [f"Have two philosophers debate {t}",
                    f"Map {t} as a concept mind map",
                    f"Write a philosophical essay on {t}"]
    else:
        sugg = []
        if "philosopher_debate" in names or "school_arena" in names or "confrontation" in names:
            sugg += [f"换个哲学家或角度再辩 {t}",
                     f"把这场关于 {t} 的交锋整理成概念脑图"]
        if "concept_trace" in names or "conceptual_map" in names:
            sugg += [f"对比 {t} 内两个相关概念",
                     f"追溯 {t} 在哲学史中的时间线"]
        if "write_essay" in names or "essay_outline" in names:
            sugg += [f"对这篇关于 {t} 的作文做论证结构分析",
                     f"继续修改这篇关于 {t} 的作文：换个角度或调整篇幅"]
        if "life_coach" in names or "advisor_council" in names:
            sugg += [f"让不同流派继续就 {t} 给你建议",
                     f"把 {t} 做成思想实验推演"]
        if "generate_image" in names:
            sugg += [f"围绕 {t} 修改这张图（换个风格或构图）",
                     f"让生成图的主角就 {t} 辩论"]
        if agent != "general":
            sugg += ["让我从另一个时期的角度回答（早/中/晚期）", "把《快乐的科学》相关原文给我"]
        if not sugg:
            # 默认池按主题哈希轮换, 避免每次都是同一组模板（2026-08-14）
            seed = sum(ord(c) for c in topic) % 2
            if seed == 0:
                sugg = [f"让两位哲学家就 {t} 辩论",
                        f"把 {t} 相关的概念画成思维导图",
                        f"围绕 {t} 写一篇哲学作文"]
            else:
                sugg = [f"就 {t} 与另一位哲学家隔空对质",
                        f"追溯 {t} 在哲学史中的时间线",
                        f"对 {t} 做一次论证结构分析"]
    seen, out = set(), []
    for s in sugg:
        if s not in seen:
            seen.add(s)
            out.append(s)
        if len(out) >= 2:
            break
    return out

def _llm_suggest(question, answer, agent, language):
    """LLM 生成用户可能想继续探索的方向（2026-08-14: 基于 问题+回答 推断, 替代规则模板）
    轻量: thinking 关闭, max_tokens 180; 失败/回答太短返回 None（调用方回退规则版）"""
    if not answer or len(answer) < 40:
        return None
    en = language == "en"
    sys_p = (
        "You are a philosophy companion agent. Based on the user's last question and your answer, "
        "infer 2-3 likely next questions the USER would want to ask. Each must be a short, natural, "
        "self-contained user question in English — no numbering, no markdown, no explanations; one per line."
        if en else
        "你是哲学伴读助手。根据用户上一个问题和你刚给出的回答，推断用户接下来最可能想问的 2~3 个问题。"
        "每条必须是一句简短、自然、独立完整的用户问句（不要编号、不要 markdown、不要解释），每行一条，用中文。"
        "可以从这些方向自然延伸（但不要生硬套模板，要紧贴刚才的话题）: 让哲学家辩论/对比、概念溯源、原典深入、"
        "思想实验、写作文、思维导图。")
    user_p = (
        f"User's last question: {question[:300]}\n\nYour answer (abridged): {answer[:2200]}"
        if en else
        f"用户上一个问题: {question[:300]}\n\n你的回答（节选）: {answer[:2200]}")
    try:
        resp = AG.llm_chat([{"role": "system", "content": sys_p}, {"role": "user", "content": user_p}],
                           temperature=0.8, max_tokens=180)
        text = (resp["choices"][0]["message"].get("content") or "").strip()
        lines = []
        for ln in text.splitlines():
            ln = ln.strip().lstrip("-•*0123456789.、)） ").strip()
            if len(ln) >= 4:
                lines.append(ln)
            if len(lines) >= 3:
                break
        return lines or None
    except Exception:
        return None


def _filter_xml_chars(text):
    """剥离 <tool_calls>/<invoke> 工具标记及其中间内容（字符级扫描, 防跨 chunk 标记; 标记不闭合则丢弃其后全部）"""
    if not text:
        return ""
    out = []
    skip = False
    i, n = 0, len(text)
    while i < n:
        if not skip:
            if text.startswith("<tool_calls", i) or text.startswith("<invoke", i):
                skip = True
            else:
                out.append(text[i])
                i += 1
                continue
        # skip 模式: 找结束标记
        end = text.find("</tool_calls>", i)
        if end < 0:
            end = text.find("</invoke>", i)
        if end >= 0:
            if text.startswith("</tool_calls>", end):
                i = end + len("</tool_calls>")
            else:
                i = end + len("</invoke>")
            skip = False
        else:
            i += 1
    return "".join(out)

def _strip_markers(text):
    """剥离工具调用标记（XML/{TOOL:}）——硬上限轮 LLM 可能输出标记而非正文"""
    t = re.sub(r"<tool_calls>.*?</tool_calls>", "", text or "", flags=re.S)
    t = re.sub(r'<invoke name="[^"]+">.*?</invoke>', "", t, flags=re.S)
    t = re.sub(r"\{TOOL:.*?\}", "", t, flags=re.S)
    return t.strip()

async def stream_agent(req_message, history, agent="general", custom_instructions=None, language="zh"):
    """LangGraph 引擎 SSE 事件流（async generator, 事件协议与自研版一致）
    agent: general=通用深哲; 其他=哲学家智能体（提示词+工具集按注册表切换）
    custom_instructions: 用户自定义指令（个性化, 追加到 system prompt）
    language: zh/en——输出与思考流语言（覆盖 system 内的语言要求）"""
    yield {"type": "status", "content": "开始思考" if language != "en" else "Thinking"}
    _t_start = time.time()
    # 预热 MCP 工具（加载完成后 get_tools 才能拿到; MCP_SERVERS 空时秒返回）
    try:
        import mcp_client as _mcp
        await _mcp.get_mcp_tools()
    except Exception:
        pass
    base_prompt = get_system_prompt(agent)
    if custom_instructions and custom_instructions.strip():
        base_prompt = (base_prompt.rstrip() +
                       f"\n\n## 用户的个性化指令（必须遵守）\n{custom_instructions.strip()}")
    # 语言切换（zh/en）: 覆盖 system 内的语言要求（思考流 + 回答）——"覆盖"语义, 防止与旧中文要求冲突
    if language == "en":
        base_prompt += ("\n\n【语言设置·重要】用户已切换到英文模式。以上（包括系统提示中）所有'使用中文'的指示一律作废。"
                        "思考流与回答必须全部使用英文（English），工具调用与引用也可用英文。禁止再用中文输出。")
    else:
        base_prompt += ("\n\n【语言要求】所有输出必须使用中文——包括内部思维过程（推理链）与回答。禁止用英文思考或输出。")
    messages = [SystemMessage(content=base_prompt)]
    if agent != "general":
        # 每轮注入人格保持提醒（多轮对话后 reasoning 易回归规划腔的关键防线）——按语言选择版本
        messages.append(SystemMessage(
            content=PERSONA_THINK_REMINDER_EN if language == "en" else PERSONA_THINK_REMINDER))
    for h in (history or [])[-20:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        messages.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))
    messages.append(HumanMessage(content=req_message))
    # 确定性预判: 概念脑图请求强制走 conceptual_map（LLM 常跳过工具直接手写）
    MAP_HINTS = ["脑图", "思维地图", "概念地图", "概念关联", "思维导图", "mindmap", "概念图谱"]
    if any(h in req_message for h in MAP_HINTS):
        messages.append(SystemMessage(
            content="用户明确要求概念脑图。第一轮必须调用 conceptual_map 工具获取 mermaid 图形代码, 禁止跳过工具直接手写文本。"))
    # ── Epistemic Guard（Phase 1, 2026-08-30）──────────────────────────
    # 结构级认识论护栏（backend/epistemic_guard.py, 纯规则）:
    #   前置: PremiseVerifier 事实前提校正 / Claim 认知层级 / Counterfactual 反事实边界
    #   后置: scan_answer 校验答案是否落实（反事实边界缺失 → 尾补, 确定性兜底）
    # 护栏尽力而为——任何异常只降级为跳过, 绝不影响主流程（与 MAP_HINTS 同机制）
    _epistemic_verdict = None
    try:
        from epistemic_guard import run_epistemic_guards, scan_answer
        _epistemic_verdict = run_epistemic_guards(req_message, agent, language)
        for _inj in _epistemic_verdict.get("injections", []):
            if _inj:
                messages.append(SystemMessage(content=_inj))
    except Exception as _e:
        logger.warning(f"[epistemic-guard pre] skipped: {str(_e)[:200]}")
    # ── Interpretation Engine（Phase 2, 2026-08-30）───────────────────────
    # 解释挑战者 + 置信度校准（backend/interpretation_engine.py, 纯规则）:
    #   前置: 解释型问题（文学/哲学解读/跨作者比较/模糊历史）→ 多候选解读强制 +
    #         支持/挑战证据分离 + 类比≠等同 + 深度惩罚 + 四档确定性语言
    #   后置: scan_interpretation 校验答案（越级断言/缺多候选 → 措辞级补正, 不展示数字）
    # 尽力而为——任何异常只降级为跳过, 绝不影响主流程（与 epistemic_guard 同机制）
    _interpretation_verdict = None
    try:
        from interpretation_engine import run_interpretation_engine, scan_interpretation
        _interpretation_verdict = run_interpretation_engine(req_message, agent, language)
        for _inj in _interpretation_verdict.get("injections", []):
            if _inj:
                messages.append(SystemMessage(content=_inj))
    except Exception as _e:
        logger.warning(f"[interpretation-engine pre] skipped: {str(_e)[:200]}")
    # ── Answer Composer（Phase 4, 2026-08-30）─────────────────────────────
    # 回答结构收口（backend/answer_composer.py, 纯规则）:
    #   前置: 默认回答结构（直接判断 → 2~4 核心理由 → 关键文本证据 → 反方/限定 → 结论）+
    #         禁止默认骨架（材料说明/工具说明/检索过程/五层报告/原典路径/再总结）+
    #         隐藏 raw reasoning（过程叙述不进正文, 用户只看推理摘要）+
    #         DeepSeek 优点吸收但禁用未经证据支持的强化措辞（完全正确/毫无疑问/绝不会/本质就是）
    #   后置: scan_composition 校验（结构信号/强化措辞/推理噪音 → 措辞级补正）;
    #         reasoning_summary 兜底（LLM 摘要缺席时由裁决生成确定性摘要）
    # 生成类请求（写作文/生图/辩论等）不注入——成品形态由各自工具决定
    # 尽力而为——任何异常只降级为跳过, 绝不影响主流程（与 Phase 1/2 同机制）
    _composition_verdict = None
    try:
        from answer_composer import run_answer_composer
        _composition_verdict = run_answer_composer(req_message, agent, language)
        for _inj in _composition_verdict.get("injections", []):
            if _inj:
                messages.append(SystemMessage(content=_inj))
    except Exception as _e:
        logger.warning(f"[answer-composer pre] skipped: {str(_e)[:200]}")
    tool_log = []
    # 2026-08-28: 递归上限 18 → 60（检索硬上限已取消, 需给足长会话空间——~29 轮工具;
    # 仍是有界兜底, 防失控烧钱）
    config = {"recursion_limit": 60}
    # 当前 agent 轮缓冲（live: 已进入实时流式回答; live_text: 已作为 token 流出的文本——
    # 若本轮后续宣告了工具调用, 需以 answer_retract 事件撤回为思考）
    pending = {"text": "", "has_tools": False, "reasoned": False, "started": set(),
               "live": False, "live_text": ""}
    pending_tools = set()   # 本轮已发 tool_start 但尚未执行的工具名（2026-08-14: 用于截断时发 tool_cancel 解除前端"调用中"卡片）
    full_answer = ""   # 已转发的所有回答文本（最终校验用）
    reasoning_text = ""   # 累积推理链（o1 风格摘要用）
    async def emit_append(text):
        """尾部补发（token 事件）: 追加到 full_answer——补正文本计入最终可见正文,
        证据契约/安全审查/审计均以补正后的完整正文为准（Phase S）"""
        nonlocal full_answer
        if not text:
            return
        full_answer += "\n\n" + text
        for ch in "\n\n" + text:
            yield {"type": "token", "content": ch}
            await asyncio.sleep(0.002)

    async def flush_agent():
        """agent 轮结束定归属: 已实时流出（live）→ 文本已在回答区, 直接返回;
        有工具调用 → 缓冲文本降级为思考（防"让我补充检索…"规划文字泄漏为回答）;
        无工具且未达实时阈值（短回答）→ 缓冲文本作为回答打字机输出（含 XML 标记剥离）"""
        nonlocal full_answer
        if pending.get("live"):
            return
        text = pending["text"]
        if not text:
            return
        if pending["has_tools"]:
            if not pending["reasoned"]:
                yield {"type": "thought", "content": text[:300]}
            return
        for ch in _filter_xml_chars(text):
            full_answer += ch
            yield {"type": "token", "content": ch}
            await asyncio.sleep(0.002)
    try:
        async for chunk, metadata in APP.astream(
                {"messages": messages, "retrieval_count": 0, "agent": agent, "language": language},
                config, stream_mode="messages"):
            node = metadata.get("langgraph_node", "")
            if node == "agent":
                if not chunk:
                    continue
                # 工具调用帧（content 为空）→ 标记本轮有工具, 并立即发"调用中"事件（CC 风格: 先显示再执行）
                if chunk.tool_call_chunks:
                    pending["has_tools"] = True
                    # 乐观流出的撤回: 本轮已实时流入回答区的文本实为工具规划文字
                    # （规划文字超过实时阈值的少数情况）→ 先撤回为思考, 再发工具卡片
                    # Phase S (S2): answer_retract 只撤销已流出的 draft text——
                    # 已建立的结构化 epistemic findings（_epistemic_verdict 中的前提
                    # 校正/反事实边界/义务状态）不随撤回消失; 最终回答若缺失校正,
                    # 由应答后收口阶段（build_missing_correction_appends）重新消费补发。
                    if pending.get("live"):
                        sent = pending.get("live_text", "")
                        if sent:
                            yield {"type": "answer_retract", "content": sent}
                            if full_answer.endswith(sent):
                                full_answer = full_answer[:len(full_answer) - len(sent)]
                        pending["live"] = False
                        pending["live_text"] = ""
                    for tcc in chunk.tool_call_chunks:
                        nm = tcc.get("name")
                        if nm and nm not in pending.get("started", ()):
                            pending.setdefault("started", set()).add(nm)
                            pending_tools.add(nm)
                            yield {"type": "tool_start", "name": nm}
                elif chunk.content:
                    # 只累积本轮文本——归属（思考 or 回答）在轮结束 flush 时决定:
                    # 有工具调用 → 降级为思考; 无工具（最终回答轮）→ 打字机输出。
                    # 防止 LLM 在工具轮输出的规划文字（"让我补充检索…"）泄漏为回答。
                    pending["text"] += chunk.content
                    # 实时流式回答: 缓冲超过阈值仍未见工具调用 → 本轮大概率是最终回答,
                    # 立即流出缓冲文本, 后续分块实时转发（2026-08-29: 替代假流式——
                    # 此前整轮缓冲到 graph 结束才一次性重放, 思考结束后长时间空窗）
                    if pending.get("live"):
                        full_answer += chunk.content
                        pending["live_text"] += chunk.content
                        # 逐字流出: 不直接转发大分块, 保证打字机节奏（生成快的部分由连接缓冲）
                        for ch in chunk.content:
                            yield {"type": "token", "content": ch}
                            await asyncio.sleep(TOKEN_INTERVAL)
                    elif not pending["has_tools"] and len(pending["text"]) >= STREAM_ANSWER_DELAY:
                        pending["live"] = True
                        pending["live_text"] = pending["text"]
                        full_answer += pending["text"]
                        # 已缓冲的文本同样逐字流出（避免首块一次性涌入）
                        for ch in pending["text"]:
                            yield {"type": "token", "content": ch}
                            await asyncio.sleep(TOKEN_INTERVAL)
                # DeepSeek reasoning（thinking 模式）→ 思维链分片节流, 实时流出; 同时累积供 o1 风格摘要
                rc = (chunk.additional_kwargs or {}).get("reasoning_content")
                if rc:
                    pending["reasoned"] = True
                    reasoning_text += rc
                    for i in range(0, len(rc), 40):
                        yield {"type": "thought_stream", "content": rc[i:i + 40]}
                        await asyncio.sleep(0.005)
            elif node == "tools":
                # agent 输出结束 → flush（thought 在工具卡片之前发出, 形成穿插节奏）
                async for ev in flush_agent():
                    yield ev
                pending = {"text": "", "has_tools": False, "reasoned": False, "live": False, "live_text": ""}
                extra = chunk.additional_kwargs or {}
                name = chunk.name or ""
                args = extra.get("_args", {})
                result = extra.get("_result_full", {})
                if name == "search_books" and isinstance(result, dict) and not result.get("results"):
                    # 原典库无命中 → 自动 websearch 补充（to_thread: 同步 urllib 跑在事件循环上会冻结整条 SSE 流）
                    ws = await asyncio.to_thread(AG.TOOLS["websearch"]["execute"],
                                                 {"query": str(args.get("query", ""))[:80]})
                    tool_log.append({"name": "websearch", "args": {"query": str(args.get("query", ""))[:80]},
                                     "result_summary": str(ws)[:200],
                                     "thought": "原典库检索不足, 自动上网搜索补充"})
                    yield {"type": "tool", "name": "websearch", "args": {"query": str(args.get("query", ""))[:80]},
                           "result": str(ws)[:300], "thought": "原典库检索不足, 自动上网搜索补充"}
                tool_log.append({"name": name, "args": args,
                                 "result_summary": str(result)[:200], "result_full": result,
                                 "thought": f"执行 {name}"})
                yield {"type": "tool", "name": name, "args": args,
                       "result": str(result)[:300], "thought": f"执行 {name}"}
                # 本轮工具已处理完 → 清空待执行标记（下一 agent 轮重新计; 2026-08-14）
                pending_tools.clear()
        # 最终 flush: 最后一轮 agent 输出（最终回答）在 done 前以打字机发出（XML 标记已剥离）
        async for ev in flush_agent():
            yield ev
        pending = {"text": "", "has_tools": False, "reasoned": False, "live": False, "live_text": ""}
        # 被截断的已宣告工具调用（宣告了 tool_start 但最终未执行, 如硬检索上限二次强制轮）:
        # 逐名发 tool_cancel, 前端据此解除对应"调用中"卡片（2026-08-14）
        for nm in sorted(pending_tools):
            yield {"type": "tool_cancel", "name": nm, "reason": "检索已达上限，该调用未执行"}
        # 最终回答校验: 剥离工具标记后为空 → 强制兜底生成正文（硬上限轮 LLM 可能只输出标记无正文）
        if not _strip_markers(full_answer):
            try:
                # 裁剪: 去掉含 tool_calls 的 assistant 消息; LangChain 消息转 dict（自研 llm_chat 期望 dict）
                def _lc_to_dict(m):
                    if isinstance(m, SystemMessage):
                        return {"role": "system", "content": m.content}
                    if isinstance(m, HumanMessage):
                        return {"role": "user", "content": m.content}
                    if isinstance(m, AIMessage):
                        return {"role": "assistant", "content": m.content or ""}
                    return None
                fb_msgs = [m for m in messages if not (isinstance(m, AIMessage) and m.tool_calls)]
                fb_msgs.append(SystemMessage(
                    content="请直接输出最终回答正文。禁止任何工具调用标记/XML/JSON 格式。只输出回答文本。"))
                fb_dicts = [d for d in (_lc_to_dict(m) for m in fb_msgs) if d]
                resp = await asyncio.to_thread(AG.llm_chat, fb_dicts, thinking=False, max_tokens=2000)
                reply = _strip_markers(resp["choices"][0]["message"].get("content") or "")
                if reply:
                    for i in range(0, len(reply), 60):
                        yield {"type": "token", "content": reply[i:i + 60]}
                        await asyncio.sleep(0.002)
            except Exception as e:
                logger.warning(f"[fallback-fail] {str(e)[:200]}")
                if "Insufficient Balance" in str(e) or "402" in str(e):
                    yield {"type": "token",
                           "content": "（API 余额不足——请充值 DeepSeek API 后重试）" if language != "en"
                           else "(Insufficient API balance—please top up DeepSeek API and retry)"}
                else:
                    yield {"type": "token",
                           "content": "（未能生成回答，请重试或换一种问法）" if language != "en"
                           else "(Failed to generate a response—please retry or rephrase your question)"}
        # ══ Phase S (S2): Epistemic findings 重消费——answer_retract 不撤销 findings ══
        # 前提校正/反事实边界是结构化 epistemic state; 若最终可见正文未落实
        # （校正随 draft 被撤回 / LLM 忽略注入 / 回答被工具轮打断）→ 此处尾补,
        # 使 high-importance 校正必然出现在最终正文。
        _epistemic_state = None
        try:
            if _epistemic_verdict:
                from epistemic_guard import build_missing_correction_appends
                _esc = scan_answer(_epistemic_verdict, full_answer, language)
                for _cor in build_missing_correction_appends(_epistemic_verdict, full_answer, language):
                    async for _ev in emit_append(_cor):
                        yield _ev
                if _esc.get("boundary_applied"):
                    _cv = _epistemic_verdict.get("counterfactual") or {}
                    _boundary = (_cv.get("boundary_text_en") if language == "en"
                                 else _cv.get("boundary_text")) or ""
                    if _boundary:
                        async for _ev in emit_append(_boundary):
                            yield _ev
                # 状态反映补发后的最终正文（重扫一次——correction_present 以最终可见文本为准）
                _esc_final = scan_answer(_epistemic_verdict, full_answer, language)
                _epistemic_state = {
                    "premise_checks": [
                        {"rule_id": c.get("rule_id"), "status": c.get("status"),
                         "referent_mode": c.get("referent_mode") or "current",
                         "correction_present": r.get("correction_present")}
                        for c, r in zip(_epistemic_verdict.get("premise_checks") or [],
                                        _esc_final.get("premise_checks") or [])],
                    "counterfactual": {k: (_epistemic_verdict.get("counterfactual") or {}).get(k)
                                       for k in ("mode", "author", "requires_guard")},
                }
        except Exception as _e:
            logger.warning(f"[epistemic-guard post] skipped: {str(_e)[:200]}")
        # ══ Phase S (S5): 预算扫描（先于 composer 扫描——超预算时抑制非必要结构提示）══
        _budget_scan = None
        try:
            if _composition_verdict:
                from answer_composer import scan_budget
                _budget_scan = scan_budget(_composition_verdict, full_answer)
        except Exception as _e:
            logger.warning(f"[answer-budget scan] skipped: {str(_e)[:200]}")
        # Interpretation Engine 应答后校验: 解释型回答缺多候选/越级断言 → 措辞级补正
        # （确定性兜底, 仍是 token 事件; 置信度数字仅内部记录, 不发送给前端）
        _interpretation_scan = None
        try:
            if _interpretation_verdict:
                _interpretation_scan = scan_interpretation(_interpretation_verdict, full_answer, language, tool_log)
                for _ins in _interpretation_scan.get("appends", []):
                    if _ins:
                        async for _ev in emit_append(_ins):
                            yield _ev
        except Exception as _e:
            logger.warning(f"[interpretation-engine post] skipped: {str(_e)[:200]}")
        # Answer Composer 应答后校验: 结构信号 / 强化措辞 / 推理噪音 → 措辞级补正
        # （解释型问题已由 interpretation_scan 补正过则不再重复; 仍是 token 事件）
        _composition_scan = None
        try:
            if _composition_verdict:
                from answer_composer import scan_composition
                _composition_scan = scan_composition(_composition_verdict, full_answer, language,
                                                     interpretation_scan=_interpretation_scan,
                                                     budget_scan=_budget_scan)
                for _ins in _composition_scan.get("appends", []):
                    if _ins:
                        async for _ev in emit_append(_ins):
                            yield _ev
        except Exception as _e:
            logger.warning(f"[answer-composer post] skipped: {str(_e)[:200]}")
        # ── Phase 3: Evidence Contract（2026-08-30）────────────────────────────
        # 检索命中了什么 ≠ 回答用了什么。此前引用面板直接取 search_books 前 4 条命中
        # （retrieval candidates), 用户会误读为 answer evidence。现在统一抽取:
        #   retrieved_evidence（检索候选全集）→ used_evidence（回答实际引用/对齐的）
        #   → citations 只投影 used_evidence（引用面板新协议）; claims 携带知识论
        #   分级与证据绑定（SPECULATION 不绑定 DIRECT evidence）。
        # 尽力而为——任何异常只降级为空引用面板, 绝不影响主流程。
        evidence_payload = None
        try:
            from evidence_contract import build_evidence_contract
            evidence_payload = build_evidence_contract(tool_log, full_answer, agent, language)
            citations = evidence_payload["citations"]
        except Exception as _e:
            logger.warning(f"[evidence-contract] skipped: {str(_e)[:200]}")
            citations = []
        # ══ Phase S (S4): Citation Sanitizer——最终输出硬约束 ══
        # visible formal citations ⊆ verified used_evidence citations:
        #   未核验 → ①存在可靠 evidence 可重新绑定（书级引用）; ②否则移除正式引用
        #   格式/降级为解释性陈述（正文可见披露, 由 done 携带净化报告）。
        _citation_sanitize = None
        try:
            if evidence_payload is not None:
                from evidence_contract import sanitize_citations, build_citation_disclosure
                _citation_sanitize = sanitize_citations(full_answer, contract=evidence_payload)
                for _dis in build_citation_disclosure(_citation_sanitize, language):
                    if _dis:
                        async for _ev in emit_append(_dis):
                            yield _ev
        except Exception as _e:
            logger.warning(f"[citation-sanitizer] skipped: {str(_e)[:200]}")
        # ══ Phase S (S3): Semantic Obligations——最终义务履行状态 ══
        # 同一认识论义务只履行一次: 已由正文表达（如"不是一回事/不能等同"）的义务
        # 不得再因措辞不同被追加补正; 状态随 done 输出供审计/前端。
        _obligations_state = None
        try:
            from semantic_obligations import derive_obligations, assess_obligations
            _obligations_state = assess_obligations(
                derive_obligations(_epistemic_verdict, _interpretation_verdict), full_answer)
        except Exception as _e:
            logger.warning(f"[obligations] skipped: {str(_e)[:200]}")
        # 工具失败统计须在 result_full 剥离前取值（2026-08-30: 旧代码在弹掉后才计数, 恒为 0）
        _fail = sum(1 for tc in tool_log if isinstance(tc.get("result_full"), dict) and tc["result_full"].get("error"))
        for tc in tool_log:
            tc.pop("result_full", None)
        # 安全审查（done 前）
        _safety = _safety_check(full_answer)
        safety_flag = None
        if "self_harm" in _safety:
            # 高危（自伤教唆）→ 替换回答为安全回应（按语言）
            full_answer = SAFETY_REPLY_EN if language == "en" else SAFETY_REPLY
            safety_flag = "blocked"
            # 回答被替换为固定安全回应——原引用全部失效, 引用面板与证据清零
            citations = []
            if evidence_payload:
                evidence_payload["used_evidence"] = []
                evidence_payload["citations"] = []
                evidence_payload["used_count"] = 0
        elif _safety:
            safety_flag = "warning"
        # done 立即发出（引用/工具/安全/规则建议——均为纯内存计算, 不调 LLM）:
        # 2026-08-29 修复: 此前"推理链摘要 + 话题建议"两个 LLM 调用串行阻塞在 done 之前,
        # 回答结束后 UI 还要空等 5-15s 才出现"可继续探索"。现在 done 先行解锁 UI,
        # 两个 LLM 后处理并行执行, 完成后以增量事件补发（前端增量替换）
        suggestions = _suggest_next(tool_log, req_message, agent, language)
        _log_stats(agent, req_message, time.time() - _t_start, [t["name"] for t in tool_log],
                   _fail, None, len(full_answer))
        yield {"type": "done", "citations": citations, "evidence": evidence_payload,
               "tool_calls": tool_log,
               "suggestions": suggestions, "safety": safety_flag,
               "composition": _composition_scan,
               # Phase S: 结构化状态随 done 输出（审计/前端可用, 不改变主协议）
               "epistemic": _epistemic_state,
               "obligations": _obligations_state,
               "budget": _budget_scan,
               "citation_sanitize": ({k: _citation_sanitize.get(k) for k in
                                      ("verified_citations", "unverified_before", "actions")}
                                     if _citation_sanitize else None),
               "safety_reply": (SAFETY_REPLY_EN if language == "en" else SAFETY_REPLY) if safety_flag == "blocked" else None}
        # 后处理（两个 LLM 调用并行）: 推理链摘要（o1 风格）+ LLM 话题建议 → 增量事件补发
        async def _post_reasoning_summary():
            if not (reasoning_text and len(reasoning_text) > 40):
                return None
            try:
                sum_prompt = ((f"Condense the following reasoning into 3-5 structured steps, "
                               f"each formatted 'N. action: point' (≤30 words each, ≤160 total):\n\n" if language == "en"
                               else f"将以下推理过程浓缩为 3-5 步结构化摘要, 每步格式'数字. 动作: 要点'（每步 ≤30 字, 总计 ≤160 字）:\n\n")
                              + reasoning_text[:2500])
                sresp = await asyncio.to_thread(AG.llm_chat,
                    [{"role": "user", "content": sum_prompt}], temperature=0.3, max_tokens=300)
                return (sresp["choices"][0]["message"].get("content") or "").strip() or None
            except Exception:
                return None
        async def _post_llm_suggest():
            try:
                return await asyncio.to_thread(_llm_suggest, req_message, full_answer, agent, language)
            except Exception:
                return None
        reasoning_summary, llm_suggestions = await asyncio.gather(
            _post_reasoning_summary(), _post_llm_suggest())
        # Phase 4: LLM 摘要缺席（无思考流/调用失败）→ 确定性推理摘要兜底
        # （由 epistemic/interpretation/evidence 裁决生成, 如"1. 核验文本事实 2. 检索原典…"）
        if not reasoning_summary:
            try:
                from answer_composer import build_reasoning_summary
                reasoning_summary = build_reasoning_summary(
                    _epistemic_verdict, _interpretation_verdict, _interpretation_scan,
                    evidence_payload, tool_log, language)
            except Exception as _e:
                logger.warning(f"[reasoning-summary fallback] skipped: {str(_e)[:200]}")
                reasoning_summary = None
        if llm_suggestions:
            yield {"type": "suggestions", "suggestions": llm_suggestions}
        if reasoning_summary:
            yield {"type": "reasoning_summary", "content": reasoning_summary}
    except Exception as e:
        _log_stats(agent, req_message, time.time() - _t_start, [], 0, str(e)[:200], 0)
        if "Insufficient Balance" in str(e) or "402" in str(e):
            yield {"type": "error",
                   "content": "DeepSeek API 余额不足——请充值后重试" if language != "en"
                   else "DeepSeek API balance insufficient—please top up and retry"}
        else:
            # 2026-08-14: 错误脱敏——客户端只给通用提示, 细节写日志（异常文本可能含 API 细节）
            logger.error(f"[agent-error] {str(e)[:300]}")
            yield {"type": "error",
                   "content": "智能体暂时出错，请重试或换个问法" if language != "en"
                   else "Agent error—please retry or rephrase"}
