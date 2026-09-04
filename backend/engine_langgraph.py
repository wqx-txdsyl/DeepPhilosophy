# -*- coding: utf-8 -*-
"""LangGraph 引擎（PhiAgent v2）——替代自研流式 ReAct 循环

Claude Code 风格: 思考 → 工具调用（多工具并行）→ 观察 → 最终回答
前端协议不变: SSE 事件 thought_stream / token / tool / done
工具: 复用 routes.agent 的 TOOLS 注册表（23 个工具平移为 StructuredTool, 零逻辑改动）
"""
import asyncio, json, re, time, inspect
from typing import Annotated, Any, TypedDict

from loguru import logger
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

import routes.agent as AG   # 复用 TOOLS 注册表 / SYSTEM_PROMPT 铁律 / API 配置
import agents as AGENTS     # 智能体注册表（智能体广场: 通用 + 哲学家）
import agent_runtime as AR  # Phase A: tool loop 治理（观测/去重/预算/重试/终止）单一真源
import reasoning_plan as RP  # Patch 1: 问题结构规划（B1/B3/B5/B6/B7 纯规则）
import tool_contracts as TC  # Phase T: 工具架构（taxonomy/重入/mermaid/措辞净化/所有权审计）
import quote_bound as QB     # Phase T.1: 逐字引文绑定（Quote Bound / T1.1-D~H）

# ── LLM（OpenAI 兼容; 智谱 glm-4-flash 免费 / DeepSeek 思考模式）──
_llm = None
def get_llm():
    global _llm
    if _llm is None:
        if "bigmodel.cn" in AG.API_URL or "glm" in AG.MODEL.lower():
            # 智谱 glm-4-flash（免费）: 无 thinking 模式, extra_body 不传 DeepSeek 专属参数
            from langchain_openai import ChatOpenAI
            _llm = ChatOpenAI(model=AG.MODEL, api_key=AG.API_KEY, base_url=AG.API_URL,
                              temperature=0.7, max_tokens=4000)
        else:
            from langchain_deepseek import ChatDeepSeek
            _llm = ChatDeepSeek(model=AG.MODEL, api_key=AG.API_KEY, base_url=AG.API_URL,
                                temperature=0.7, max_tokens=4000,
                                extra_body={"thinking": {"type": "enabled"}, "reasoning_effort": "low"})
    return _llm

# ── 检索纪律（Phase A: 预算与终止条件收编到 agent_runtime, 本处只保留引用）──
RETRIEVAL_TOOLS = {"search_books", "get_chapter", "get_philosopher", "query_graph", "websearch",
                   "get_school", "get_book_detail", "list_books", "query_database", "compare_views",
                   "role_play", "concept_trace"}
# 柔性提示阈值（soft 预算, 检索达到后提示评估材料充分性）——Phase A 起由 agent_runtime 配置驱动
RETRIEVAL_LIMIT = AR.TOOL_BUDGET["soft_retrieval"]
# 硬上限已取消（2026-08-28）→ Phase A 恢复为"有界 hard 预算"（agent_runtime 配置, 默认 20）:
# 不再是"静默取消检索调用"（旧 8 次硬截断的信息丢失问题）, 而是预算用尽后强制进入
# graceful answer completion（模型先被告知再作答, 已取得 evidence 全部保留）。
RETRIEVAL_HARD = AR.TOOL_BUDGET["hard_retrieval"]

# 实时流式回答阈值（2026-08-29）: agent 轮 content 缓冲超过该字符数且本轮未见工具调用 →
# 判定为最终回答, 缓冲文本与后续分块立即实时流出。替代原"整轮缓冲→graph 结束后 8ms/字
# 打字机重放"的假流式（思考结束后到回答出现之间空窗数十秒）。
# O1: 48 → 240——铁律 0 要求工具轮先写 1~4 句公开工作笔记（Main Agent 自己的
# thinking_summary 数据源）, 阈值必须高于常规笔记长度, 否则笔记会先以回答形态流出再撤回。
STREAM_ANSWER_DELAY = 240
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
0. 【公开工作笔记（每轮工具调用前必须）】凡是还要调用工具的轮次, 先用 1~4 个自然句写下
   给用户看的工作判断: ①当前暂时知道什么; ②还有什么不确定; ③为什么下一步做这个动作;
   ④（若有）新证据改变了之前的哪个假设。尚未核验的内容用"可能/我记得/待核验"的口吻表述,
   不得把记忆当作已确认事实。写完工作笔记后再宣告本轮工具调用。这段笔记不是最终答案——
   不得在此提前输出完整回答或结论; 不再调用工具的那一轮直接输出最终回答, 无需工作笔记。
1. 【研究纪律: 检索—阅读闭环】凡涉及具体哲学主张/概念/出处/原话, 必须以真实的检索与阅读
   支撑结论, 不得凭记忆作答:
   - 先 search_books 定位; 命中候选后, 下一步就是 get_chapter 读取对应篇章原文,
     确认措辞与上下文, 然后才下结论——检索片段只是定位线索, 不是核验本身;
   - 不因"自己已经知道一个看似合理的答案"就停止研究; 记忆只是工作假设,
     未经原文核验前不得以确定口吻陈述;
   - 若原文核验修正了你的工作假设（如记忆中出处/对象有误、与相邻章句混淆）,
     最终回答必须明确指出修正了什么;
   - 重要不确定性未解决时继续检索研究; 避免重复检索, 但不追求最少工具——以核验完成为准。
2. 回答标注引用来源: 【《书名》· 章节名】。
3. 涉及哲学家关系用 query_graph; 流派用 get_school; 哲人资料用 get_philosopher; 概念溯源用 concept_trace。
4. 用户要求对比可用 compare_views; 写作文用 write_essay; 辩论用 philosopher_debate; 决策求助用 advisor_council;
   扮演/以哲学家口吻回答用 role_play; 苏格拉底式追问用 socratic_tutor; 论证分析用 analyze_argument;
   用户要求"画脑图/思维地图/概念地图/概念图/关系图/梳理XX的概念关联/画图展示论证链条"时调用 conceptual_map
   （它返回结构化 graph 与已验证的 mermaid 图形——直接采用, 不要自己手写 ASCII 树或改写节点）。
   对比两位哲学家/两个流派在同一问题上的立场差异时, **首选直接调用 compare_views**——它内部已检索
   双方材料并返回比较脚手架（共同问题/比较轴线/双方主张/证据需求）; 不要先自行多轮手工检索再补一个
   compare_views（那是重复劳动）; 调用后按需补 ≤2 次针对性检索即可。
4''. 论文大纲/骨架用 essay_outline; 焦虑/迷茫/人生困惑疏导用 life_coach; 辩证分析/矛盾分析用 dialectic
   （用户对形式的约束——如"不要用正反合标签"——必须经 constraints 参数原样传入工具）;
   流派/概念的历史脉络与时间线用 history_timeline; 思想实验用 thought_experiment（仅用户明确要求变体时才迭代传变化点）;
   "让XX和XX的原文对质/交锋" → confrontation（双方各引原文互驳）;
   "流派PK/随机对决/让两个流派辩论" → school_arena（随机双流派 × 当代热点对抗, 可指定 topic/school_a/school_b）;
   "让深哲和尼采讨论/协作" → agent_council（双智能体协议协作: 通用视角 + 人格视角 + 综合）。
4'''. 辩论交互: 用户说"继续/下一轮"（逐轮辩论中）→ philosopher_debate(action=continue); "结束辩论/总结" → philosopher_debate(action=summary);
   用户参与辩论（说"我要和XX辩论"）→ philosopher_debate(mode=vs_user), 之后用户每次发言 → philosopher_debate(user_reply=用户发言)。
4'. 多轮修改: 用户说"修改/重写/改一下刚才的作文" → 调 write_essay 并传 modify; 说"修改/换成/调整刚才的图" → 调 generate_image（工具自动基于上次结果修改, 无需额外参数）。
4''''. 工具选择的关键区分: "画星图/关系图/脑图/思想地图/论证依赖图/以X为中心的图" → **conceptual_map**（关系结构图）; "生成图片/插画/画像/艺术图" → generate_image（AI 艺术图像）。星图是结构图不是画——选错会答非所问。
   评审仲裁: 输入是单个论证/短文本说"评审" → analyze_argument（逻辑结构）; 输入是完整论文/文章 → paper_review（整体同行评审）——按输入形态与工具能力匹配选择, 不按关键词机械匹配。
5. 检索纪律: 避免无意义重复——同一关键词不重复查; 检索覆盖不足时换新关键词补充; 材料充分后停止检索直接回答。检索次数不受限制, 以回答质量为准。
5'. 工具结果所有权（Phase T, 重要）: reasoning 类专用工具（compare_views/dialectic/analyze_argument/
   paper_review/advisor_council/thought_experiment/conceptual_map/socratic_tutor/confrontation）返回的是
   **结构化脚手架**（比较轴线/辩证运动字段/论证结构/图结构/单个问题）——不是最终答案。你必须结合证据契约、
   对话语境与用户指令**二次综合**后再作答, 不得把工具产物原样照搬充当最终回答。
   例外（USER_REQUESTED_ARTIFACT）: write_essay/generate_image/essay_outline 的产物本身就是用户请求的对象, 可较完整呈现。
5''. 输出 mermaid 图（mindmap/flowchart）的规范: ①每个节点一行, 不写一行式图（mindmap 用缩进层级, flowchart 每行一条边）; ②节点文本内换行用 <br/> 而非换行符; ③节点文本含特殊字符（括号/引号/斜杠）时用双引号包裹; ④全图节点 ≤ 15 个。
6. 若原典库检索无结果或覆盖不足, **先调用 websearch 上网补充（1~2 次, 换关键词重试）**, 仍无结果才如实说明"库中未检索到"——不硬答、不编造。
6'. 【主动上网搜索】websearch 不是兜底摆设, 遇到以下情形**应当主动调用**:
   ① 问题超出 403 本原典库范围（现当代哲学研究、其他文化传统、跨学科内容、时事引用）;
   ② 库内检索多轮仍找不到关键事实（著作年代/版本/学界共识/人物生平细节）;
   ③ 对自己的记忆有怀疑、需要交叉验证的论断。
   但 websearch 结果只作背景语境与事实参考——**不得**把网上内容包装成【《书名》·章节】原典引用
   （引用标注仍只给库内实际检索到并核验的原文, 见规则 9）。
7. 回答使用中文, 严谨、清晰、有层次; 适度苏格拉底式反问, 但不回避问题。
8. 避免"哲学废话": 每个论断要么有原文依据, 要么明确标注为分析/推测。
9. 【证据分级·引用可信度】只有实际检索到、能在库中定位的原文, 才用【《书名》· 章节】标注;
   凭记忆或仅间接确认的关键表述, 必须降低确定性措辞——例如"通常归于《哲学研究》§371 的一句表述,
   但我未能在原典库中直接定位到该节原文"——并显式标注"（记忆, 未经库中核验）",
   严禁把记忆伪装成已核验原文引用。检索不足时宁可明说"该论点我尚未检索到原典支撑", 也不要降级隐瞒。
   【《书》·章】正式引用所支撑的引句必须是检索片段中的原文措辞; 只是对某书观点的转述时,
   用一般提及（《书名》）即可, 不要挂正式引用标注。
10. 【区分层次】做哲学辨析时, 明确区分: ①原文事实（带【《书名》·章节】可跳转引用）;
   ②解释（对原文的解读, 用"我的理解/通常解读"标注）; ③学界争议（存在不同解读时如实点出）;
   ④综合判断（Agent 自己的结论, 用"我认为/综合来看"标注）。四层不得混同。
11. 【原典路径】「📖 原典路径」不是默认结构——仅当来源导航本身对用户有价值时才附:
   深度文本分析、用户明确要求阅读路径/书单、或多个原典之间存在明确递进关系。
   普通概念解释、出处核验类问题不要附加原典路径（系统会按问题类型明确提示是否允许）。
   附时按论证顺序列出 3~6 个关键原文段落（每个都带【《书名》·章节】可跳转标注），
   并用一两句话说明各段落之间的关系。仅当确实检索到这些段落时才列出; 未核验的段落不得放入原典路径。
12. 【跨哲人关联】当问题涉及一个概念在不同哲学家/流派中的处理差异时, 优先调用
    compare_views / confrontation / history_timeline 展开思想史脉络; 至少点明其他哲学家的立场差异
    （如"亚里士多德追问'事物的本质是什么', 黑格尔讨论本质与现象, 维特根斯坦则质疑'寻找隐藏本质'
    这一哲学活动本身"），把单点问答变成概念的思想史导航。
13. 【路由原则（Phase T）】调用专用工具前按 能力匹配 × 信息增益 × 输出合同匹配 判断:
    ① 这个能力你自己能否高质量完成? ② 该工具是否提供你当前缺失的信息/结构/状态/产物?
    ③ 用户要的输出是否就是该工具的原生产物? ④ 工具的约束是否兼容用户的约束?
    若调用只会重复生成你自己也能生成的成品 prose, 且不带来新证据/结构/状态/产物——允许不调用。
    专用工具的"调用量"不是目标, **有效**专用工具率才是。
14. 【技能重入纪律（Phase T）】同一 reasoning/generation 技能对同一议题的重入受治理:
    只有用户明确要求迭代（参数体现变化点）/上次调用失败/出现实质新议题时才可再次调用,
    退化重复（只把上次输入缩短再调一次）会被系统拦截。socratic_tutor 一次只返回一个问题——
    用户回答后再次调用并传 user_reply=用户的回答, 绝不预生成后续轮次;
    向用户展示时只呈现该 next_question（至多加一句铺垫）, **不得在它之外再追加你自己的新问题**。
15. 【运行时措辞】不要在最终回答中出现内部过程措辞（如"检索已收口/预算已达上限/准入未通过/系统收敛"）——
    那是系统内部治理语言。材料是否充分、哪些未能核验, 用第一人称的确定性边界表述。"""

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
    forced: bool   # 已注入"强制回答"提示（达到 hard 预算/连续无增益后, 确保最终轮产出回答）
    forced_tools_done: bool   # 强制回答后已补跑过一轮工具（防死循环烧钱; 2026-08-14）
    agent: str     # 当前智能体（general / 哲学家 key）
    language: str  # zh/en——中文模式下每轮强化语言提醒（防思考偶发英文）
    # ── Phase A: tool loop 治理状态（对象经内存态传递, 无 checkpointer 序列化）──
    guard: Any            # DuplicateGuard（A2, 单轮生命周期）
    budget: Any           # ToolBudget（A3）
    trace: Any            # ToolLoopTrace（A1）
    tool_count: int       # 本轮已执行工具调用总数（A3 total 预算口径）
    no_gain_streak: int   # 连续无信息增益检索轮数（A5）
    model_retries: int    # 本轮模型 API 重试累计（A1/A4）
    # ── Patch 1 (B1/B3): 问题计划与检索状态（对象/引用经内存态传递）──
    plan: Any             # RP.build_plan 结果（problem_type/complexity/注入/时序/核验问题）
    retrieval_state: Any  # AR.RetrievalState（B1: 语义重复/相关证据/充分性）
    obligation_ledger: Any  # Patch 1.1 (P1): evidence obligation 台账（检索准入单一真源）
    verif_box: Any        # {"state":…, "term":…, "computed":…}（B3 核验状态, 引用传递）
    raw_tool_log: Any     # 共享 raw 工具记录列表（tools_node 写入, 引擎消费; B4 引用核验用）
    round_all_low: bool   # 上一工具轮是否全部低增益（B1 sufficiency 消费）
    round_any_low: bool   # 上一工具轮是否出现低增益调用（B1 sufficiency 消费）
    # ── Phase T: 工具架构治理状态 ──
    user_message: str     # 原始用户消息（重入策略 USER_REQUESTED_ITERATION 判定用）
    reentry: Any          # TC.SkillReentryTracker（invocation 级 skill 重入治理）

async def agent_node(state):
    msgs = list(state["messages"])
    agent = state.get("agent", "general")
    # 中文模式每轮强化: 内部思考与回答都必须中文（DeepSeek 偶发英文思考的防线）
    if state.get("language", "zh") != "en":
        msgs.append(SystemMessage(
            content="（语言提醒：你的内部思考过程（thinking/reasoning）与最终回答都必须使用中文。禁止用英文思考。"))
    # ── Phase A: 预算与终止条件（A3/A5——替代原 RETRIEVAL_LIMIT/RETRIEVAL_HARD 就地判断）──
    budget = state.get("budget")
    forced = False
    if budget is not None and budget.hard_reached():
        # hard 预算（A3/T5）: 终止工具循环 → graceful answer completion。
        # 保留工具绑定（解绑会导致 LLM 退化为写 XML 文本调用）; 硬提示让 LLM 直接回答。
        msgs.append(SystemMessage(content=AR.HARD_BUDGET_DIRECTIVE))
        forced = True
    elif budget is not None and budget.soft_reached():
        # soft 预算（A3/T2）: 柔性提示, 由 LLM 判断材料是否充分（不强制停止）
        msgs.append(SystemMessage(content=AR.SOFT_BUDGET_HINT))
    streak = state.get("no_gain_streak", 0)
    verdict = AR.no_gain_verdict(streak)
    # ── Patch 1.1 (P1): 准入拒绝空转防护——模型宣告→被拒→再宣告的循环会让思考流
    # 长时间无可见进展（用户观感"卡住"）; 拒绝累计达阈值 → 强制收口直接作答。
    _ledger_for_rejects = state.get("obligation_ledger")
    if _ledger_for_rejects is not None and getattr(_ledger_for_rejects, "rejected", 0) >= AR.ADMISSION_REJECT_FORCE:
        msgs.append(SystemMessage(content=(
            "（系统检索收敛）多次检索调用已被收敛机制取消。请立即基于已取得的检索结果输出最终回答——"
            "注意：未执行≠库中无此书，请勿向用户声称'库中未收录/未检索到该书'，"
            "只能基于已成功执行的检索结果陈述库内覆盖情况。")))
        forced = True
    if verdict == "force":
        # A5/T3: 连续无增益轮 → 强制收口（比总数 hard 预算更早拦截原地打转）
        msgs.append(SystemMessage(content=AR.NO_GAIN_FORCE_DIRECTIVE))
        forced = True
    elif verdict == "warn" and not (budget is not None and budget.soft_reached()):
        msgs.append(SystemMessage(content=AR.NO_GAIN_WARN_HINT))
    # ── O1: 引擎不再代执行任何认知性工具（原 _ensure_primary_read auto-read 已删除）。
    # 主文本读取由 Main Agent 自己宣告; 引擎只保留 prompt 层引导（下方"最后核验机会"提示）
    # 与确定性校验（quote/citation validator, 见收口阶段）。──
    # ── Patch 1 (B1): 证据充分性收敛（复杂度期望 + 信息增益; 非硬上限）──
    try:
        plan = state.get("plan") or {}
        rstate = state.get("retrieval_state")
        ledger = state.get("obligation_ledger")
        if plan and rstate is not None and budget is not None:
            complexity = plan.get("complexity") or "NORMAL_EXPLANATION"
            key_terms = plan.get("key_terms") or []
            rel_met = bool(rstate.relevant_ids) and any(
                t and any(t in (c.get("query") or "") for c in rstate.calls)
                for t in key_terms[:2])
            if plan.get("verification_intent") and ledger is not None:
                # ── Patch 1.1 (P2): 核验路径收口由 obligation 台账驱动 ──
                # 分项配额（search≤2/read≤2/web≤1/meta≤1）是真正的执行上限; 达 4 或义务
                # 满足 → force。force 时若尚未读任何原文, 额外引导模型补跑一次 get_chapter
                # （forced 轮 read 放行）——避免"检索到位却没读原文就作答"（真实回归: F12）。
                if ledger.obligations_satisfied or budget.total_executed >= 4:
                    suff = "force"
                    if (not ledger.obligations_satisfied and ledger.read_execs == 0
                            and not getattr(ledger, "_read_hint_sent", False)):
                        ledger._read_hint_sent = True
                        msgs.append(SystemMessage(content=(
                            "（检索收敛·最后核验机会）你现在仍允许补跑最多 1 次 get_chapter，"
                            "直接阅读上面检索结果中已定位到的章节原文（用它返回的 book_id），"
                            "以完成措辞级核验；其余一切检索/书目查询均已禁止。读完或放弃后，"
                            "立即基于已有材料输出最终核验回答。")))
                else:
                    suff = "none"
            else:
                suff = AR.sufficiency_verdict(
                    complexity, budget.total_executed, bool(state.get("round_all_low")),
                    len(rstate.relevant_ids), rel_met,
                    round_any_low=bool(state.get("round_any_low")))
            hint = AR.sufficiency_hint(suff, complexity, state.get("language", "zh"))
            if hint:
                msgs.append(SystemMessage(content=hint))
            if suff == "force":
                forced = True
    except Exception as _e:
        logger.warning(f"[sufficiency] skipped: {str(_e)[:120]}")
    # ── Patch 1 (B3): 术语核验措辞约束（核验状态已知后每轮注入）──
    try:
        vbox = state.get("verif_box")
        if vbox and vbox.get("state"):
            vtext = RP.verification_injection(vbox, state.get("language", "zh"))
            if vtext:
                msgs.append(SystemMessage(content=vtext))
    except Exception as _e:
        logger.warning(f"[verification-inject] skipped: {str(_e)[:120]}")
    if state.get("retrieval_count", 0) >= RETRIEVAL_LIMIT and not forced and not (
            budget is not None and budget.soft_reached()):
        # 既有柔性检索提示（预算未达 soft 时的等效提示, 保留原文案以最小化行为变化）
        msgs.append(SystemMessage(
            content="（已进行多次检索。请评估现有材料是否足以回答: 充分则停止检索直接作答; 确有必要再用新关键词补充检索, 但避免无意义重复。）"))
    # 2026-08-14: 同步 LLM 调用移入线程池, 防阻塞事件循环（并发会话卡死）
    # Phase A (A4): 有限重试——可恢复错误（连接中断/超时/429/5xx）按配置退避重试;
    # 耗尽抛 ModelCallError → stream_agent 的 graceful completion（用已取得 evidence 收口）
    # O1: 机械 timing observability——Main Agent invocation 的起止时长入 trace;
    # 每次模型调用开启一个新的 decision group（本组内宣告的工具归属该组）。
    _trace_ref = state.get("trace")
    _llm_t0 = time.time()
    if _trace_ref is not None:
        try:
            _trace_ref.begin_group()
        except Exception:
            pass
    resp, retries = await _agent_llm_invoke(agent, msgs, trace=_trace_ref)
    if _trace_ref is not None:
        try:
            _trace_ref.record_phase("llm_invocation", _llm_t0, msgs_len=len(msgs))
        except Exception:
            pass
    return {"messages": [resp], "forced": forced,
            "model_retries": state.get("model_retries", 0) + retries}

async def _agent_llm_invoke(agent, msgs, trace=None):
    """agent 轮 LLM 调用（线程池防阻塞）+ A4 有限重试。返回 (resp, retry_count)。"""
    def _call(m):
        return get_llm().bind_tools(get_tools(agent)).invoke(m)
    def _on_retry(attempt, exc):
        # A1: model retry 计数入 trace（trace 经 state 共享引用, 单轮生命周期内安全）
        if trace is not None:
            trace.model_retries += 1
        logger.warning(f"[model-retry {attempt + 1}/{AR.MODEL_RETRY['attempts']}] {str(exc)[:160]}")
    return await asyncio.to_thread(AR.invoke_llm_with_retry, _call, msgs, _on_retry)


# ── O1: 主文本读取保障改策 ─────────────────────────────────────────────
# 原 Phase T.1 (T1.1-B) 的引擎兜底 auto-read（_ensure_primary_read）已整体删除:
# 它绕过 Main Agent 直接 locate_exact_phrase → get_chapter, 并注入"这就是你自己的
# 核验动作"式归因倒置——runtime 决定了认知动作却表现为 Agent 的行为（AUDIT-01/R1 反例）。
# O1 后的等价能力全部在合法层:
#   ① prompt 层: 铁律 1（检索—阅读闭环）+ 收口轮"最后核验机会"读章提示（模型仍自主宣告）;
#   ② 确定性校验层: 收口阶段 quote/citation validator 保留（只校验与补正措辞,
#      不再代执行任何工具, 也不产生 Main Agent thinking）。

def _derive_read_info(raw_tool_log, term):
    """模型自主 get_chapter 读取后, 从 raw_tool_log 推导已读章节信息（含含 term 的原文段）"""
    tn = re.sub(r"[^\w\u4e00-\u9fff]+", "", term or "")
    best = None
    for tc in raw_tool_log or []:
        if (tc.get("name") or "") != "get_chapter":
            continue
        rf = tc.get("result_full") or {}
        text = str(rf.get("text") or "")
        if not text:
            continue
        passage = ""
        for ln in text.split("\n"):
            s = ln.strip()
            if not s:
                continue
            sn = re.sub(r"[^\w\u4e00-\u9fff]+", "", s)
            if (term and term in s) or (len(tn) >= 4 and tn in sn):
                passage = s[:360]
                break
        if passage:
            try:
                from routes.agent import book_by_id
                b = book_by_id(rf.get("book_id")) or {}
            except Exception:
                b = {}
            best = {"book": b.get("title") or rf.get("book_title") or "",
                    "chapter": rf.get("title") or "", "book_id": rf.get("book_id"),
                    "chapter_idx": rf.get("chapter_idx"), "passage": passage}
            break
    return best

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
    自愈: 失败工具按 TOOL_RETRY 配置重试, 仍失败附备选工具提示。
    Phase A: A2 重复调用防护（同参只读工具 → 复用结果, 不再执行）;
             A3 预算分类计数（useful/retry/duplicate/no_gain）;
             A1 逐调用观测（时长/成败/结果 hash/info gain）;
             A5 连续无增益轮统计（no_gain_streak）。
    Patch 1.1 (P1): 检索准入（obligation admission）——每个 retrieval 在真正执行前
    按宣告顺序判定: 义务是否已满足 / query_family 是否已有充分证据 / 是否预计产生
    新证据类 / 是否同义改写。无新义务 → 执行前取消（非 hard max_tools）。"""
    last = state["messages"][-1]
    calls = last.tool_calls or []
    agent = state.get("agent", "general")
    tools_map = {t.name: t for t in get_tools(agent)}
    guard = state.get("guard")
    budget = state.get("budget")
    trace = state.get("trace")
    retrieval_state = state.get("retrieval_state")
    plan = state.get("plan") or {}
    raw_log = state.get("raw_tool_log")
    ledger = state.get("obligation_ledger")
    retrieval_set = set(RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    TOOL_TIMEOUT = AR.TOOL_TIMEOUT   # 工具执行超时（防挂起; Phase A 收编为配置）
    forced = bool(state.get("forced"))
    complexity = plan.get("complexity") or "NORMAL_EXPLANATION"

    # ── Patch 1.1 (P1): 批前准入——按宣告顺序逐个判定（同批内后面的调用可见前面的宣告）──
    # Phase T (T7): reasoning/generation skill 追加 invocation 级重入准入——
    # 同 purpose 无依据（用户迭代要求/前次失败/实质新议题）的重复调用在执行前取消。
    def _is_retrieval(name):
        return name in retrieval_set

    reentry = state.get("reentry")
    user_message = state.get("user_message", "") or ""

    admissions = []
    for c in calls:
        name = c.get("name", "")
        cargs = c.get("args", {}) or {}
        ok, reason, kind = True, "", ""
        if ledger is not None and _is_retrieval(name):
            ok, reason = ledger.admit(name, cargs, complexity, forced)
            kind = "retrieval"
        if ok and reentry is not None and name in TC.SKILL_REENTRY_TOOLS:
            # USER_REQUESTED_ITERATION 可来自工具参数或用户消息本身（如"再来一个变体"）;
            # 工具真实入参不改写, 用户消息单独传入判定
            rok, rreason = reentry.admit(name, cargs, user_message=user_message)
            if not rok:
                ok, reason, kind = False, rreason, "reentry"
        admissions.append((ok, reason, kind))

    async def run_one(call, call_index, admitted, admit_reason="", admit_kind=""):
        name = call.get("name", "")
        args = call.get("args", {}) or {}
        tool = tools_map.get(name)
        thought_label = f"执行 {name}"
        # ── Patch 1.1 (P1) / Phase T (T7): 准入/重入拒绝 → 执行前取消 ──
        # （仍回 ToolMessage, DeepSeek 要求每个 id 有响应）
        if not admitted:
            if admit_kind == "reentry":
                skip_res = {"error": f"技能重入被拦截（{admit_reason}）。"
                                     "请基于该工具此前返回的结构化结果直接综合作答;"
                                     "若用户确实要求新变体, 请在参数中体现具体迭代意图。"}
            else:
                skip_res = {"error": f"检索准入未通过（{admit_reason}），此调用在执行前取消。"
                                     "请基于已有材料作答，或宣告实质不同的检索。"}
            if trace:
                trace.record_call(call_index, name, args, 0.0, False, None,
                                  json.dumps(skip_res, ensure_ascii=False)[:200],
                                  AR.result_hash(skip_res), "duplicate", "repeat", 0,
                                  executed=False, thought=(admit_reason or "")[:40],
                                  decision_group=getattr(trace, "current_group", None),
                                  tool_call_id=call.get("id"))
            return ToolMessage(content=json.dumps(skip_res, ensure_ascii=False)[:4000], name=name,
                               tool_call_id=call.get("id", ""),
                               additional_kwargs={"_args": args, "_result_full": skip_res,
                                                  "_budget_class": "duplicate", "_info_gain": "repeat",
                                                  "_admitted": False,
                                                  "_dg": getattr(trace, "current_group", None)})
        # ── A2: 重复调用防护 ──
        decision = guard.decide(name, args) if guard else {"action": "execute", "cls": "unique", "reason": ""}
        if decision["action"] == "reuse":
            prev = decision.get("prev")
            if budget:
                budget.count(name, "duplicate", executed=False)
            if trace:
                trace.record_call(call_index, name, args, 0.0, True, None,
                                  json.dumps(prev, ensure_ascii=False)[:200] if prev is not None else "",
                                  AR.result_hash(prev), "duplicate", "repeat", 0,
                                  executed=False, thought="复用本轮早前结果",
                                  decision_group=getattr(trace, "current_group", None),
                                  tool_call_id=call.get("id"))
            content = json.dumps(prev, ensure_ascii=False) if isinstance(prev, (dict, list)) else str(prev)
            return ToolMessage(content=content[:4000], name=name,
                               tool_call_id=call.get("id", ""),
                               additional_kwargs={"_args": args, "_result_full": prev,
                                                  "_budget_class": "duplicate", "_reused": True,
                                                  "_info_gain": "repeat",
                                                  "_dg": getattr(trace, "current_group", None)})
        # ── A3/A1: 执行（带预算口径的轮内重试）──
        res = None
        inner_attempts = AR.TOOL_RETRY["attempts"]
        attempts_used = 0
        t0 = time.time()
        for attempt in range(inner_attempts + 1):
            attempts_used = attempt + 1
            try:
                if tool is None:
                    res = {"error": f"未知工具 {name}"}
                elif inspect.iscoroutinefunction(getattr(tool, "func", None)):
                    res = await asyncio.wait_for(tool.func(**args), timeout=TOOL_TIMEOUT)   # async 工具（MCP 等）
                else:
                    res = await asyncio.wait_for(asyncio.to_thread(tool.func, **args), timeout=TOOL_TIMEOUT)
                if isinstance(res, dict) and res.get("error") and attempt < inner_attempts:
                    continue
                break
            except asyncio.TimeoutError:
                res = {"error": f"工具 {name} 执行超时（>{TOOL_TIMEOUT}s）"}
                if attempt < inner_attempts:
                    continue
            except Exception as e:
                res = {"error": str(e)}
                if attempt < inner_attempts:
                    continue
        duration_ms = (time.time() - t0) * 1000
        is_err = isinstance(res, dict) and res.get("error")
        # 仍失败 → 附备选工具提示（LLM 可据此换工具）
        if is_err:
            fb = FALLBACK_MAP.get(name)
            if fb:
                res["fallback_hint"] = f"此工具失败, 可改用 {fb} 查询"
        if budget and attempts_used > 1:
            budget.inner_retries += attempts_used - 1   # A1/A3: 轮内自愈重试计入观测
        # ── A2 记录结果（成功可复用; 失败放行跨轮重试）──
        if guard:
            guard.record(name, args, not is_err, res)
        # ── Phase T (T7): 重入治理登记（成败都登记——失败后重试合理）──
        if reentry is not None and name in TC.SKILL_REENTRY_TOOLS:
            try:
                reentry.record(name, args, not is_err)
            except Exception:
                pass
        # ── A1 information gain / A3 预算分类（可靠实现: 结果 hash + 空命中判定）──
        # Patch 1 (B1): 语义重复判定（query 改写但结果高度重合 → low_gain）——检索状态登记
        rh = AR.result_hash(res)
        info_gain = ""
        rec = None
        if not is_err and name in retrieval_set:
            info_gain = "empty" if AR.result_is_empty(res) else "new"
            if retrieval_state is not None and isinstance(res, dict) and not res.get("error"):
                rec = retrieval_state.register(name, args, res, plan.get("key_terms") or [])
                if rec["low_gain"] and info_gain == "new":
                    info_gain = "low_gain"
        # ── Patch 1.1 (P1): obligation 台账登记（成败都登记——失败释放 pending-read, 同章可重试）──
        if ledger is not None and name in retrieval_set:
            try:
                ledger.record(name, args, not is_err, res, plan.get("key_terms") or [])
                if rec is not None:
                    ledger.mark_result(name, args, low_gain=bool(rec.get("low_gain")),
                                       relevant_new=int(rec.get("new_relevant") or 0))
            except Exception as _le:
                logger.warning(f"[obligation-ledger] skipped: {str(_le)[:120]}")
        cls = decision.get("cls", "unique")
        if budget:
            budget.count(name, cls, executed=True, info_gain=info_gain)
        if trace:
            ev_items = _evidence_item_count(name, res)
            trace.record_call(call_index, name, args, duration_ms, not is_err,
                              (res or {}).get("error") if isinstance(res, dict) else None,
                              json.dumps(res, ensure_ascii=False)[:200] if isinstance(res, (dict, list)) else str(res)[:200],
                              rh, cls, info_gain, ev_items, executed=True,
                              thought=thought_label,
                              decision_group=getattr(trace, "current_group", None),
                              tool_call_id=call.get("id"))
        # ── Patch 1 (B4): 共享 raw 工具记录（LiveCitationSanitizer 引用核验 / 证据契约用）──
        if isinstance(raw_log, list) and name in retrieval_set and not is_err:
            raw_log.append({"name": name, "args": args,
                            "result_summary": str(res)[:200], "result_full": res,
                            "thought": thought_label})
        # ── Phase T (T9): 专用工具自带的原典证据进入 Evidence Contract 查证池 ──
        #（confrontation/compare_views 等内部检索的结构化 citations/evidence——最小接口适配:
        #  只进 raw_log（引用核验/证据契约池, 使主 Agent 的正式引用可被核验）,
        #  不进 tool_log/预算/trace, 不改变检索口径）
        if isinstance(raw_log, list) and isinstance(res, dict) and not is_err:
            _ev_items = res.get("citations") or res.get("evidence")
            if isinstance(_ev_items, list) and _ev_items:
                _pseudo = [{"book_title": e.get("book"), "chapter_title": e.get("chapter"),
                            "book_id": e.get("book_id"), "chapter_idx": e.get("chapter_idx"),
                            "author": e.get("author", ""),
                            "snippet": (e.get("snippet") or e.get("basis") or "")[:220],
                            "score": 0.5}
                           for e in _ev_items if isinstance(e, dict) and e.get("book")]
                if _pseudo:
                    raw_log.append({"name": "search_books",
                                    "args": {"query": f"[{name} 内部检索证据]"},
                                    "result_summary": f"{name} 内部检索证据 x{len(_pseudo)}",
                                    "result_full": {"results": _pseudo},
                                    "thought": f"{name} 结构化证据入池（契约核验用）"})
        content = json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
        return ToolMessage(content=content[:4000], name=name,
                           tool_call_id=call.get("id", ""),
                           additional_kwargs={"_args": args, "_result_full": res,
                                              "_budget_class": cls, "_info_gain": info_gain,
                                              "_dg": getattr(trace, "current_group", None)})

    base_index = state.get("tool_count", 0)
    results = await asyncio.gather(*[run_one(c, base_index + i, admissions[i][0], admissions[i][1],
                                             admissions[i][2])
                                     for i, c in enumerate(calls)])
    # ── A5: 连续无增益轮统计（本轮全部检索调用均 repeat/empty/low_gain/duplicate → streak+1）──
    round_gains = [(getattr(r, "additional_kwargs", {}) or {}).get("_info_gain", "") for r in results]
    retrieval_round = [g for g, c in zip(round_gains, calls) if c.get("name") in retrieval_set]
    dup_round = [(getattr(r, "additional_kwargs", {}) or {}).get("_budget_class") == "duplicate" for r in results]
    all_retrieval_barren = bool(retrieval_round) and all(g in ("repeat", "empty", "low_gain") for g in retrieval_round)
    all_dup = calls and all(dup_round)
    if all_retrieval_barren or all_dup:
        streak = state.get("no_gain_streak", 0) + 1
    else:
        streak = 0
    inc = sum(1 for c in calls if c.get("name") in retrieval_set)
    executed = sum(1 for r in results
                   if (getattr(r, "additional_kwargs", {}) or {}).get("_budget_class") != "duplicate")
    # ── Patch 1 (B1): 记录本轮低增益状态（agent_node sufficiency 消费）──
    round_all_low = bool(retrieval_round) and all(
        g in ("repeat", "empty", "low_gain") for g in retrieval_round)
    round_any_low = bool(retrieval_round) and any(
        g in ("repeat", "empty", "low_gain") for g in retrieval_round)
    return {"messages": results, "retrieval_count": state.get("retrieval_count", 0) + inc,
            "tool_count": base_index + executed,
            "no_gain_streak": streak,
            "round_all_low": round_all_low,
            "round_any_low": round_any_low,
            "forced_tools_done": state.get("forced", False)}

def _evidence_item_count(tool_name, res):
    """单次调用的证据候选数（可靠口径: evidence_contract 白名单工具的结果条目数）"""
    try:
        from evidence_contract import PRIMARY_TOOLS
        if tool_name not in PRIMARY_TOOLS or not isinstance(res, dict):
            return 0
        for k in ("results", "echoes", "quotes", "hits"):
            v = res.get(k)
            if isinstance(v, list):
                return len(v)
        return 1 if res else 0
    except Exception:
        return 0

def should_continue(state):
    last = state["messages"][-1]
    if not getattr(last, "tool_calls", None):
        return "end"
    # A5/T5-T6: 强制回答轮（hard 预算或连续无增益触发）——模型仍宣告工具调用
    # （DeepSeek 常见"任务规划残留"）: 已补跑过一轮 → 截断（防死循环烧钱）; 未补跑过 →
    # 再执行一轮, 把已宣告的工具调用跑完并回传结果, 下一轮强制结束
    # （2026-08-14 修复: 此前直接丢弃, 导致"工具调用未完成就回答/凭记忆作答"）
    if state.get("forced"):
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


# ── Patch 1 (B4-A): 内部控制标签剥离（final-output 断言）──
# <rationale> 等内部标签只能走对应 stream event, 绝不允许进入最终可见正文。
# 完整标签对连同内容一起剥离（内容只走事件通道）; 孤立标签只剥标签本身。
_CONTROL_PAIR_RE = re.compile(r"<(rationale|reasoning|scratchpad|thought|analysis|plan)\b[^>]*>.*?</\1>", re.S | re.I)
_CONTROL_STRAY_RE = re.compile(r"</?(rationale|reasoning|scratchpad|thought|analysis|plan)\b[^>]*>", re.I)


def _strip_control_tags(text):
    """剥离残留内部控制标签（含未闭合）; 完整对连内容一起移除"""
    t = _CONTROL_PAIR_RE.sub("", text or "")
    t = _CONTROL_STRAY_RE.sub("", t)
    return t


def _visible_text(text):
    """所有进入用户可见正文的文本统一净化: 工具标记剥离 + 内部控制标签剥离"""
    return _strip_control_tags(_filter_xml_chars(text or ""))


# ── Patch 1.1 (P5): 最终兜底回答指令——兜底不要求长, 但必须保留 question obligations ──
# 核验类问题至少输出: ①verdict ②verified exact text / closest text
# ③edition/translation distinction（若相关）④confidence boundary。
# 不能让 reasoning plan 已满足的关键义务全部消失在 final answer（F02 四层区分）。
def _final_answer_directive(plan=None, verif_box=None, language="zh"):
    generic = "请直接输出最终回答正文。禁止任何工具调用标记/XML/JSON 格式。只输出回答文本。"
    vi = (plan or {}).get("verification_intent") or {}
    if not vi:
        return generic
    state = (verif_box or {}).get("state") or "UNKNOWN"
    term = (verif_box or {}).get("term") or vi.get("term") or "该表述"
    if language == "en":
        return (
            "Output the final verification answer now (concise, but ALL verification obligations "
            f"must survive into the final answer; no tool-call markers, answer text only):\n"
            f"1) Verdict for \"{term}\" (verification state: {state}): yes / no / cannot confirm;\n"
            "2) Verified text: the closest original passage from the retrieved material "
            "(with 【《Book》· chapter】; if no verbatim hit, give the nearest proposition/section and its location);\n"
            "3) Layer distinction: the user's phrasing vs the original text (original-language / proposition number) "
            "vs the Chinese translation or popular paraphrase — say which layer each belongs to;\n"
            "4) Confidence boundary: what can be confirmed and what cannot (edition/translation/verbatim).\n"
            "Do not reduce the answer to a one-line verdict.")
    return (
        "请直接输出最终核验回答（简洁，但问题的全部核验义务必须保留在最终回答里；"
        "禁止任何工具调用标记/XML/JSON 格式，只输出回答文本）：\n"
        f"1) 核验结论：基于「{term}」的核验状态（{state}）给出 是/否/不能确认；\n"
        "2) 已核验原文：给出检索材料中最接近的原句（带【《书》·章节】标注；"
        "若未逐字命中，给出最接近的命题/段落及其在书中的位置）；\n"
        "3) 层次区分：明确 用户所给表述 vs 原著文本（原著语言措辞/命题编号） vs 中文翻译或通俗概括 "
        "——各自属于哪一层，不得混同；\n"
        "4) 确定性边界：哪些层面能确认、哪些不能（版本/译本/逐字层面如实说明）。\n"
        "不得只输出一行结论而丢掉上述义务。")

# ── Phase A (A4): graceful completion 辅助 ──────────────
def _lc_to_dict(m):
    """LangChain 消息 → dict（llm_chat 期望 dict; 含 tool_calls 的 assistant 帧剔除）"""
    if isinstance(m, SystemMessage):
        return {"role": "system", "content": m.content}
    if isinstance(m, HumanMessage):
        return {"role": "user", "content": m.content}
    if isinstance(m, AIMessage):
        return {"role": "assistant", "content": m.content or ""}
    return None

def _evidence_digest(tool_log, max_items=12):
    """已取得 evidence 的有界摘要（graceful completion 用; 防恢复请求上下文膨胀）"""
    lines = []
    for t in (tool_log or [])[-max_items:]:
        a = t.get("args") or {}
        q = a.get("query") or a.get("concept") or a.get("topic") or a.get("question") or ""
        lines.append(f"- {t.get('name', '')}（{str(q)[:60]}）: {(t.get('result_summary') or '')[:150]}")
    return "\n".join(lines)

def _build_recovery_dicts(messages, tool_log, directive):
    """恢复调用消息: 原对话（去工具帧）+ 指令 + 已取得 evidence 摘要（有界）"""
    fb_msgs = [m for m in messages if not (isinstance(m, AIMessage) and m.tool_calls)]
    digest = _evidence_digest(tool_log)
    fb_msgs.append(SystemMessage(content=directive + ("\n\n【已取得的检索材料】\n" + digest if digest else "")))
    return [d for d in (_lc_to_dict(m) for m in fb_msgs) if d]

# ── Thinking UI（2026-08-31; O1 收敛）──
# 工具结果解读 = ACTIVITY 通道（tool_note 事件, initiated_by=runtime_mechanical）:
# 完全确定性模板, 描述"这一步结果如何影响下一步核实"——绝不引用内部思维链/system prompt/
# 隐藏状态; 绝不输出内部字段（book_id 等）与结果正文; 不冒充 Main Agent thinking
# （O1: 原 _INTENT_THINKING 意图模板——以第一人称宣称 Agent 意图——已删除,
#  意图只能由模型自己的公开工作笔记表达, 空窗由 _activity_line 机械注记填补）。
_RETRIEVAL_THINK_TOOLS = {"search_books", "get_chapter", "get_philosopher", "get_book_detail",
                          "query_graph", "list_books", "websearch"}


def _count_result(result):
    """安全计数: 只取结果列表长度/命中标记, 不读取内部字段与正文内容。"""
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        for k in ("results", "items", "data", "books", "sources", "matches"):
            v = result.get(k)
            if isinstance(v, list):
                return len(v)
        for k in ("content", "text", "snippet", "body", "chapter"):
            if result.get(k):
                return 1
    return 0


def _safe_args(args):
    if not isinstance(args, dict):
        args = {}
    for k in ("book", "book_title", "query", "q", "name", "philosopher", "topic", "question", "keyword"):
        v = args.get(k)
        if isinstance(v, str) and v.strip():
            return str(v).strip()[:40]
    return ""


# ── Thinking 数据源契约（O1 重定义）────────────────────────────────
# thinking_summary 只承载 Main Agent 主动写给用户看的公开工作判断:
#   ① 模型在内容通道显式写出的 <rationale>…</rationale> 摘要（RationaleParser 提取）;
#   ② 模型在工具轮写出的公开工作笔记（铁律 0）——轮末由 flush 归入 thinking_summary。
# 它不是: raw chain-of-thought / reasoning_content 原样透传 / Python runtime 编造的思考 /
#   tool_note 冒充思考 / final answer 提前重述 / policy engine 的决定。
# O1: 原"引擎侧摘要生成器"（独立 mini-LLM 以"思考摘要器"人设代笔）已删除——
#   那是 runtime 冒充 Main Agent thinking 的路径（R1 BEFORE trace: 227 条事件）。
#   模型没写就没有 thinking; 空窗由机械活动注记（tool_note, ACTIVITY 通道）填补。
_RAT_OPEN = "<rationale>"
_RAT_CLOSE = "</rationale>"

RATIONAL_STATS = {"count": 0, "first": "", "longest": 0}


# ── O1 (§13): 工具开始执行后的机械活动注记 ──
# ACTIVITY 通道（tool_note 事件, initiated_by=runtime_mechanical）:
# 描述"正在发生什么", 让工具执行立即有 running 状态——不冒充模型思考, 不用第一人称认知表述,
# 不为填补空白伪造 thinking。确定性模板, 失败静默。
def _activity_line(name, args, language="zh"):
    zh = language != "en"
    a = args if isinstance(args, dict) else {}
    q = str(a.get("query") or a.get("keyword") or "").strip()
    if name == "search_books":
        if q:
            return f"正在检索「{q[:24]}」…" if zh else f"Searching \"{q[:24]}\"…"
        return "正在检索原典库…" if zh else "Searching the corpus…"
    if name == "get_chapter":
        bid = str(a.get("book_id") or "").strip()
        title = ""
        try:
            from routes.agent import book_by_id as _bbi
            title = ((_bbi(a.get("book_id")) or {}).get("title")) or ""
        except Exception:
            title = ""
        if not title and bid:
            title = bid[:20]
        if title:
            return f"正在读取《{title}》章节原文…" if zh else f"Reading {title} chapter…"
        return "正在读取章节原文…" if zh else "Reading the chapter…"
    if name == "websearch":
        if q:
            return f"正在上网搜索「{q[:24]}」…" if zh else f"Searching the web for \"{q[:24]}\"…"
        return "正在上网搜索…" if zh else "Searching the web…"
    if name == "query_graph":
        e = str(a.get("philosopher") or a.get("concept") or "").strip()
        if e:
            return f"正在查询思想星丛「{e[:20]}」…" if zh else f"Querying the constellation of {e[:20]}…"
        return "正在查询思想星丛…" if zh else "Querying the constellation…"
    if name == "get_philosopher":
        ent = _safe_args(a)
        return f"正在查证「{ent}」资料…" if ent and zh else ("正在查证哲人资料…" if zh else "Looking up philosopher info…")
    if name == "get_book_detail":
        ent = _safe_args(a)
        return f"正在核对《{ent}》书目信息…" if ent and zh else ("正在核对书目信息…" if zh else "Checking book details…")
    return "正在核实相关材料…" if zh else "Verifying relevant material…"


class RationaleParser:
    """流式解析 <rationale>…</rationale>（跨 chunk; 非贪婪; 未闭合安全回退）。
    产出 (emit_text, rationale_list)——标签从对外文本中剥离,
    摘要经事件通道单独转发; 绝不把 reasoning_content 引入。"""

    def __init__(self, max_hold=900):
        self.buf = ""
        self.max_hold = max_hold

    def push(self, chunk):
        emit = ""
        rats = []
        self.buf += chunk
        while True:
            o = self.buf.find(_RAT_OPEN)
            c = self.buf.find(_RAT_CLOSE, o + len(_RAT_OPEN)) if o >= 0 else -1
            if o >= 0 and c >= 0:
                inner = self.buf[o + len(_RAT_OPEN):c].strip()
                if inner:
                    rats.append(inner[:300])
                self.buf = self.buf[:o] + self.buf[c + len(_RAT_CLOSE):]
                continue
            break
        o = self.buf.find(_RAT_OPEN)
        if o >= 0:
            # open 已见但未闭合: 之前部分吐出, 含 open 之后的部分挂起
            if len(self.buf) - o > self.max_hold:
                emit += self.buf[:o] + self.buf[o:]
                self.buf = ""
                return emit, rats
            emit += self.buf[:o]
            self.buf = self.buf[o:]
            return emit, rats
        # 无 open: 尾部可能被 chunk 切碎的 open 前缀 → hold 尾部
        hold = 0
        for k in range(min(len(_RAT_OPEN), len(self.buf)) + 1, 1, -1):
            if self.buf.endswith(_RAT_OPEN[:k]):
                hold = k
                break
        end = len(self.buf) - hold
        emit += self.buf[:end]
        self.buf = self.buf[end:]
        return emit, rats

    def finish(self):
        """流结束: 未闭合挂起文本全部释放（宁可展示原文, 不丢内容）"""
        out, self.buf = self.buf, ""
        return out


def interpret_thinking(name, args, result, language):
    """工具完成后的安全 thinking 片段（结果如何影响下一步）; 无内容返回 None。"""
    if name not in _RETRIEVAL_THINK_TOOLS:
        return None
    zh = language != "en"
    ent = _safe_args(args)
    n = _count_result(result)
    if n == 0:
        if name == "websearch":
            return ("原典库仍无直接材料，需要换个检索方向。" if zh
                    else "Still no direct material—try another angle.")
        return ("这一步没有检索到直接材料，需要换个方向核实。" if zh
                else "No direct material here—will verify from another angle.")
    if name == "search_books":
        return (f"原典检索命中 {n} 项相关资料，先看与问题直接相关的部分。" if zh
                else f"Found {n} relevant passages—focus on the ones closest to the question.")
    if name == "get_chapter":
        if ent:
            return (f"已调取《{ent}》对应章节原文，用于核对语境。" if zh
                    else f"Chapter {ent} retrieved to check the wording in context.")
        return ("已调取对应章节原文，用于核对语境。" if zh
                else "Chapter text retrieved for context.")
    if name == "get_philosopher":
        return (f"已确认「{ent}」的基本信息。" if ent
                else "已确认哲人基本信息。" if zh
                else "Philosopher info confirmed.")
    if name == "get_book_detail":
        return (f"已核对《{ent}》的基本信息。" if ent
                else "已核对著作基本信息。" if zh
                else "Book details checked.")
    if name == "query_graph":
        return (f"星丛查询返回 {n} 项关联，用于第二字核对概念源流。" if zh
                else f"Constellation query returned {n} links for cross-checking.")
    if name == "list_books":
        return (f"书目筛选返回 {n} 项。" if zh else f"Book list filtered to {n} items.")
    if name == "websearch":
        return (f"网上检索返回 {n} 项材料，作为补充证据核验。" if zh
                else f"Web search returned {n} items for cross-checking.")
    return None


async def stream_agent(req_message, history, agent="general", custom_instructions=None, language="zh",
                       conversation_id=None, message_id=None):
    """LangGraph 引擎 SSE 事件流（async generator, 事件协议与自研版一致）
    agent: general=通用深哲; 其他=哲学家智能体（提示词+工具集按注册表切换）
    custom_instructions: 用户自定义指令（个性化, 追加到 system prompt）
    language: zh/en——输出与思考流语言（覆盖 system 内的语言要求）
    conversation_id/message_id: Phase A (A1) 观测上下文（可选, 缺省自动生成）"""
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
    # Patch 1 (B2/B4-A): 不再要求模型在内容通道写 <rationale> 标签（该指令是泄漏压力源）——
    # 思考摘要由引擎侧生成器（安全通道）产出; 模型若自行写出 <rationale> 仍会被解析转发/剥离。
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
    # 确定性预判: 图/关系图请求走 conceptual_map（LLM 常跳过工具直接手写）——
    # Phase T (T5): 注入 MAP_TYPE 预判; 用户已给节点链条时要求经 nodes/relations 传入
    MAP_HINTS = ["脑图", "思维地图", "概念地图", "概念关联", "思维导图", "mindmap",
                 "概念图谱", "概念图", "关系图", "画图", "图展示", "论证依赖", "依赖图"]
    if any(h in req_message for h in MAP_HINTS):
        _mt = TC.infer_map_type(req_message)
        messages.append(SystemMessage(
            content=f"用户明确要求图/关系图。第一轮必须调用 conceptual_map 工具获取结构化 graph 与已验证的 mermaid, 禁止跳过工具直接手写图形文本。"
                    f"根据请求选择最贴合的 map_type（当前判断: {_mt}）; 若用户已给出明确的节点链条（如 A→B→C）, "
                    f"把节点与关系作为 nodes/relations 参数传入。工具返回的 mermaid 已经过渲染验证——直接采用, 不要自行改写节点/连线。"))
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
    # ── Patch 1: 问题结构规划（B1/B3/B5/B6/B7）——类型/复杂度/形态/依赖链/时序/核验问题 ──
    plan = RP.build_plan(req_message, agent, language)
    for _inj in plan.get("injections", []):
        if _inj:
            messages.append(SystemMessage(content=_inj))
    # Phase T (T11): 比较类问题的确定性路由提示（与 MAP_HINTS 同机制的轻量注入, 非强制）——
    # QG2/Q08 教训: 模型倾向先手工多路检索再自己写对比（或调用沦为合规动作）。
    # compare_views 内部自带双方检索与比较脚手架——首选直接调用, 避免重复劳动。
    if plan.get("problem_type") == "COMPARISON":
        messages.append(SystemMessage(
            content="（比较类问题路由）优先直接调用 compare_views 获取比较脚手架"
                    "（它内部已检索双方材料, 返回共同问题/比较轴线/双方候选主张/证据需求）——"
                    "不要先自行多路手工检索再写对比; 拿到脚手架后按需补 ≤2 次针对性检索, "
                    "再结合证据做你的二次综合（脚手架不是最终答案）。"))
    tool_log = []
    # ── Phase A: tool loop 治理状态（A1 观测 / A2 去重 / A3 预算——单轮生命周期对象）──
    guard = AR.DuplicateGuard()
    budget = AR.ToolBudget(retrieval_tools=set(RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS))
    trace = AR.ToolLoopTrace(conversation_id, message_id, agent, question_chars=len(req_message or ""))
    # ── Patch 1: B1 检索状态 / B3 核验盒 / B4 引用核验器 + 术语断言门 ──
    retrieval_state = AR.RetrievalState()
    # ── Patch 1.1 (P1): evidence obligation 台账（检索准入; P2 意图驱动核验义务）──
    obligation_ledger = AR.ObligationLedger(plan)
    raw_tool_log = []   # 共享 raw 工具记录（tools_node 写入; 引用核验/证据契约消费; result_full 保留到收口）
    verif_box = {"state": None, "term": "", "computed": False}
    _vq = plan.get("verification_question") or {}
    if not _vq.get("term") and (plan.get("verification_intent") or {}).get("term"):
        # P2: 核验意图携带的待核验表述（引号句）→ 术语核验机制复用
        _vq = {"term": plan["verification_intent"]["term"], "quoted": True}
    if _vq.get("term"):
        verif_box["term"] = _vq["term"]
        obligation_ledger.vi = dict(plan.get("verification_intent") or {}) or None
        if obligation_ledger.vi:
            obligation_ledger._term_norm = re.sub(r"[的是之其所\s]", "", verif_box["term"])
    from evidence_contract import LiveCitationSanitizer
    # Patch 1.1 (P3): PRIMARY_ONLY/AUTHOR_ONLY 约束下, 二手书的正式引用同样被流式降级
    # （visible_citation ⊆ used_evidence 的流式侧保证; 契约层再做终检）
    _vi = plan.get("verification_intent") or {}
    _sc = _vi.get("constraint") if _vi.get("constraint") in ("PRIMARY_ONLY", "AUTHOR_ONLY") else None
    _subjects = [_vi["subject_author"]] if _vi.get("subject_author") else []
    _citation_san = LiveCitationSanitizer(raw_tool_log, language, fallback_log=tool_log,
                                          source_constraint=_sc, subject_authors=_subjects)
    # Phase T.1 (T1.1-D): Quote Bound 流式净化器——verbatim blockquote/引导词引文
    # 绑定 evidence 核验; MEMORY_ONLY 不得渲染为原文（转 paraphrase + 核验边界）。
    _quote_san = QB.QuoteBoundSanitizer(raw_tool_log, language)
    _term_gate = RP.TermClaimGate(
        verif_box.get("term"),
        (lambda s: RP.constrain_unconditional_claim(s, verif_box.get("state")))
        if verif_box.get("term") else None)
    # Phase T (T13-B): 运行时措辞净化器——内部治理语言（"检索已被收口/预算已达上限/…"）
    # 不得进入 Final prose; 流式安全（跨 chunk 缓冲）。
    _phrase_scr = TC.RuntimePhraseScrubber()
    # Phase T (T7): invocation 级 skill 重入治理器
    _reentry_tracker = TC.SkillReentryTracker()
    # 2026-08-28: 递归上限 18 → 60（检索硬上限已取消, 需给足长会话空间——~29 轮工具;
    # 仍是有界兜底, 防失控烧钱）。Phase A: 数值收编 agent_runtime.RECURSION_LIMIT 配置
    config = {"recursion_limit": AR.RECURSION_LIMIT}
    # 当前 agent 轮缓冲（live: 已进入实时流式回答; live_text: 已作为 token 流出的文本——
    # 若本轮后续宣告了工具调用, 需以 answer_retract 事件撤回为思考;
    # note_emitted: 本轮公开工作笔记已作为 thinking_summary 发出, flush 不再重复）
    pending = {"text": "", "has_tools": False, "reasoned": False, "started": set(),
               "live": False, "live_text": "", "note_emitted": False}
    pending_tools = set()   # 本轮已发 tool_start 但尚未执行的工具名（2026-08-14: 用于截断时发 tool_cancel 解除前端"调用中"卡片）
    full_answer = ""   # 已转发的所有回答文本（最终校验用）
    reasoning_text = ""   # 累积推理链（o1 风格摘要用）
    _rat_parser = RationaleParser()   # <rationale>…</rationale> 流式解析（安全摘要通道）
    _rat_tools_done = 0   # phase 推断: 已完成的工具数
    _rat_phase = "analysis"
    # O1 因果观测: Main Agent invocation 组计数（tools→agent 每次回到 agent 节点 +1）
    _agent_invocations = 1
    _saw_tools_result = False
    _main_agent_tool_decisions = 0

    def _phase_for():
        """phase 推断: 首轮 analysis; 有工具结果后 evidence; 无后续工具时 synthesis"""
        if _rat_tools_done == 0:
            return "analysis"
        return "evidence" if pending_tools else "synthesis"

    def _dg():
        """当前 decision group 标识（O1 provenance: 本组工具由该次 Main Agent invocation 宣告）"""
        return f"inv-{_agent_invocations}"

    def _note_event(content, phase, delta=False):
        """Main Agent 公开工作笔记事件（thinking_summary / thinking_summary_delta）。
        initiated_by=main_agent: 内容只能来自模型自己的输出（rationale 标签 / 工作笔记）。"""
        if not delta:
            RATIONAL_STATS["count"] += 1
            if not RATIONAL_STATS["first"]:
                RATIONAL_STATS["first"] = content[:80]
            RATIONAL_STATS["longest"] = max(RATIONAL_STATS["longest"], len(content))
        return {"type": "thinking_summary_delta" if delta else "thinking_summary",
                "content": content if delta else content[:280],
                "phase": phase,
                "initiated_by": "main_agent",
                "decision_group_id": _dg(),
                "conversation_id": conversation_id,
                "message_id": message_id,
                "invocation_id": f"{conversation_id}:{message_id}"}

    def _flush_working_note():
        """O1 (§5): 工具宣告前的公开工作笔记归位——模型本轮写在内容通道的工作判断
        在首个工具宣告出现时立即转为 thinking_summary（causal order:
        MAIN_AGENT_INVOCATION → thinking → tool declaration → tool_start）。"""
        evs = []
        txt = pending.get("text", "").strip()
        if txt and not pending.get("note_emitted") and not pending.get("live"):
            evs.append(_note_event(txt, _phase_for()))
            pending["note_emitted"] = True
        return evs
    
    async def emit_append(text):
        """尾部补发（token 事件）: 追加到 full_answer——补正文本计入最终可见正文,
        证据契约/安全审查/审计均以补正后的完整正文为准（Phase S）。
        Patch 1 (B4): 补发文本同样经过 控制标签剥离 + 引用实时核验 + 术语断言门。
        Phase T (T13-B): 补发文本同样经过运行时措辞净化。"""
        nonlocal full_answer
        if not text:
            return
        vis = _visible_text(text)
        vis = _phrase_scr.push(vis)
        vis = _citation_san.push(vis)
        vis = _quote_san.push(vis)
        vis = _term_gate.push(vis)
        if not vis:
            return
        full_answer += "\n\n" + vis
        for ch in "\n\n" + vis:
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
            # O1: 工具轮公开工作笔记（模型内容通道原文）→ thinking_summary。
            # 这是 Main Agent 自己写给用户的工作判断——不是 runtime 代笔。
            _txt = text.strip()[:280]
            if _txt and not pending.get("note_emitted"):
                yield _note_event(_txt, _phase_for())
                pending["note_emitted"] = True
            return
        for ch in _filter_xml_chars(text):
            full_answer += ch
            yield {"type": "token", "content": ch}
            await asyncio.sleep(0.002)
    # ══ Phase A (A4/A5): 图流执行与异常恢复分离 ══
    # 此前整轮（图流 + 收口 + done）包在同一个 try 里, 图流中任何异常（如模型侧
    # 流式连接中断"peer closed connection..."）直接以 error 事件终止整轮——已完成的
    # 全部工具调用取得的 evidence 一并丢弃（RAM audit 第 9 轮"约 13 次工具调用后
    # 模型侧 error"的真实路径）。现在: 图流异常先走 graceful completion（用已取得
    # evidence 完成回答）, 恢复成功/已有部分正文 → 继续正常收口（citations/done 照常）。
    stream_error = None
    try:
        async for chunk, metadata in APP.astream(
                {"messages": messages, "retrieval_count": 0, "agent": agent, "language": language,
                 "guard": guard, "budget": budget, "trace": trace,
                 "tool_count": 0, "no_gain_streak": 0, "model_retries": 0,
                 "plan": plan, "retrieval_state": retrieval_state,
                 "obligation_ledger": obligation_ledger, "verif_box": verif_box,
                 "raw_tool_log": raw_tool_log, "round_all_low": False, "round_any_low": False,
                 "user_message": req_message, "reentry": _reentry_tracker},
                config, stream_mode="messages"):
            node = metadata.get("langgraph_node", "")
            # O1 因果观测: tools→agent 回到 agent 节点 = 一次新的 Main Agent invocation
            # （tool batch 结束后若再有认知工具, 必须由这次新 invocation 宣告——T3 断言依据）
            if node == "agent" and _saw_tools_result:
                _agent_invocations += 1
                _saw_tools_result = False
            if node == "tools":
                _saw_tools_result = True
            if node == "agent":
                if not chunk:
                    continue
                # 工具调用帧（content 为空）→ 标记本轮有工具, 并立即发"调用中"事件（CC 风格: 先显示再执行）
                # 防御（2026-08-30 三连错误修复）: stream_mode="messages" 下偶发完整 AIMessage
                # （无 tool_call_chunks 属性）——一律 getattr 取, 非工具帧按文本处理
                tool_call_chunks = getattr(chunk, "tool_call_chunks", None)
                if tool_call_chunks:
                    pending["has_tools"] = True
                    # O1 (§5) causal order: 模型本轮写在内容通道的公开工作笔记
                    # （thinking_summary, initiated_by=main_agent）必须先于 tool_start 事件。
                    for _nv in _flush_working_note():
                        yield _nv
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
                    for tcc in tool_call_chunks:
                        nm = tcc.get("name")
                        if nm and nm not in pending.get("started", ()):
                            pending.setdefault("started", set()).add(nm)
                            pending_tools.add(nm)
                            _main_agent_tool_decisions += 1
                            # O1 provenance: 工具宣告来自 Main Agent 本轮 invocation
                            yield {"type": "tool_start", "name": nm,
                                   "initiated_by": "main_agent", "decision_group_id": _dg(),
                                   "tool_call_id": tcc.get("id") or None}
                            # O1 (§13): 宣告后立即给机械活动注记（ACTIVITY, 非 thinking）
                            try:
                                yield {"type": "tool_note",
                                       "content": _activity_line(nm, tcc.get("args") or {}, language),
                                       "initiated_by": "runtime_mechanical", "activity": True,
                                       "decision_group_id": _dg()}
                            except Exception:
                                pass
                elif chunk.content:
                    # Thinking 数据源（真实化）: 先过 rationale 解析器——
                    # 模型在内容通道显式生成的 <rationale> 摘要在标签闭合后以
                    # thinking_summary 事件转发（phase 随时间推进）, 标签剥离;
                    # 其余文本按原正文逻辑（工具轮规划文本→pending, 轮末降级为
                    # thinking_summary 兜底; 无工具轮→打字机回答）。
                    # Patch 1 (B4): 进入 pending/可见正文前统一净化——
                    #   控制标签剥离 + 引用实时核验（未核验 formal citation 降级为一般提及）
                    #   + 术语断言门（B3: 含目标术语句在句界处约束无条件断言）。
                    _emit_text, _rats = _rat_parser.push(chunk.content)
                    for _rat in _rats:
                        _rat_phase = _phase_for()
                        yield _note_event(_rat, _rat_phase)
                    if not _emit_text:
                        continue
                    _vis = _visible_text(_emit_text)
                    _vis = _phrase_scr.push(_vis)
                    _vis = _citation_san.push(_vis)
                    _vis = _quote_san.push(_vis)
                    _vis = _term_gate.push(_vis)
                    if not _vis:
                        continue
                    chunk.content = _vis
                    # 只累积本轮文本——归属（思考 or 回答）在轮结束 flush 时决定:
                    # 有工具调用 → 降级为思考; 无工具（最终回答轮）→ 打字机输出。
                    # 防止 LLM 在工具轮输出的规划文字（"让我补充检索…"）泄漏为回答。
                    pending["text"] += _vis
                    # 实时流式回答: 缓冲超过阈值仍未见工具调用 → 本轮大概率是最终回答,
                    # 立即流出缓冲文本, 后续分块实时转发（2026-08-29: 替代假流式——
                    # 此前整轮缓冲到 graph 结束才一次性重放, 思考结束后长时间空窗）
                    if pending.get("live"):
                        full_answer += _vis
                        pending["live_text"] += _vis
                        # 逐字流出: 不直接转发大分块, 保证打字机节奏（生成快的部分由连接缓冲）
                        for ch in _vis:
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
                # （只节流转发给前端展示, 不落盘——A1: 禁止记录原始 chain-of-thought）
                rc = (getattr(chunk, "additional_kwargs", None) or {}).get("reasoning_content")
                if rc:
                    pending["reasoned"] = True
                    reasoning_text += rc
                    for i in range(0, len(rc), 40):
                        yield {"type": "thought_stream", "content": rc[i:i + 40]}
                        await asyncio.sleep(0.005)
            elif node == "tools":
                # agent 输出结束 → flush（工作笔记/工具卡片穿插节奏; O1: 笔记已在宣告前归位）
                async for ev in flush_agent():
                    yield ev
                pending = {"text": "", "has_tools": False, "reasoned": False, "live": False,
                           "live_text": "", "note_emitted": False}
                extra = chunk.additional_kwargs or {}
                name = chunk.name or ""
                args = extra.get("_args", {})
                result = extra.get("_result_full", {})
                reused = extra.get("_reused", False)
                admitted = extra.get("_admitted", True)
                # O1: 引擎 auto-websearch 已删除——search_books 空结果后是否上网补充
                # 由 Main Agent 下一轮自主宣告（websearch 对模型可用且不受隐性配额挤压）,
                # runtime 不再代执行认知性工具（T7 断言依据）。
                _thought = ("复用本轮早前结果（重复调用已拦截）" if reused
                            else "检索准入未通过，执行前取消" if not admitted
                            else f"执行 {name}")
                tool_log.append({"name": name, "args": args,
                                 "result_summary": str(result)[:200], "result_full": result,
                                 "thought": _thought})
                # O1 provenance: 工具执行结果——决定（宣告）来自 Main Agent;
                # 执行/复用/准入拦截属机械层, 不改变发起者归属。
                yield {"type": "tool", "name": name, "args": args,
                       "result": str(result)[:300], "thought": _thought,
                       "initiated_by": "main_agent",
                       "decision_group_id": extra.get("_dg") or _dg(),
                       "tool_call_id": getattr(chunk, "tool_call_id", None)}
                # Thinking UI: 工具结果解读（ACTIVITY 注记, runtime_mechanical; 不确定时静默）。
                # Patch 1.1: 准入拒绝的调用不发"没有检索到直接材料"式解读——
                # 那会让用户/模型误读为"库中无此书"（真实事故: 《论语》案例）, 改发中性说明。
                try:
                    if not admitted:
                        yield {"type": "tool_note",
                               "content": "（检索收敛）该调用与已有检索重合或超出预算，未执行——这不代表库中无相关内容。",
                               "initiated_by": "runtime_mechanical",
                               "decision_group_id": extra.get("_dg") or _dg()}
                    else:
                        _th_line = interpret_thinking(name, args, result, language)
                        if _th_line:
                            yield {"type": "tool_note", "content": _th_line,
                                   "initiated_by": "runtime_mechanical",
                                   "decision_group_id": extra.get("_dg") or _dg()}
                except Exception as _e:
                    logger.warning(f"[thinking-event] skipped: {str(_e)[:120]}")
                # 本轮工具已处理完 → 清空待执行标记（下一 agent 轮重新计; 2026-08-14）
                _rat_tools_done += 1
                pending_tools.clear()
                # Patch 1 (B3): 术语核验状态计算（首个工具轮后一次性完成; 结果经 verif_box
                # 引用传递, 下一 agent 轮注入措辞约束）——不再逐工具生成 evidence 摘要
                # （工具结果解读已由 interpret_thinking 的 tool_note 覆盖, 避免空卡片噪音）
                if verif_box.get("term") and not verif_box.get("computed"):
                    try:
                        _v = RP.verify_term_presence(verif_box.get("term"), raw_tool_log)
                        verif_box["state"] = _v["state"]
                        verif_box["computed"] = True
                        logger.info(f"[verify-term] '{verif_box.get('term')}' → {_v['state']} "
                                    f"(texts={_v.get('texts_searched')}, exact={_v.get('exact_hits')})")
                    except Exception as _e:
                        logger.warning(f"[verify-term] skipped: {str(_e)[:120]}")
    except Exception as e:
        # A4/A5: 图流异常（模型侧流式连接中断/重试耗尽/递归上限/工具帧异常）不再直接终止整轮
        stream_error = e
        logger.error(f"[agent-stream-error] {type(e).__name__}: {str(e)[:300]}")

    # ══ Phase A (A4): graceful recovery ══
    #   ① 无正文 → 用已取得 evidence（工具结果摘要, 有界）调一次无工具 LLM 完成回答
    #   ② 已有部分正文（中断发生在最终回答流中）→ 保留, 直接继续收口
    #   ③ 恢复也失败且无任何 evidence → 友好错误（不暴露内部细节/stack trace）
    # 恢复成功 → 落到正常收口: 已取得 evidence 不丢, citations/done 照常发出。
    if stream_error is not None:
        _recovered = False
        if not _strip_markers(full_answer):
            try:
                fb_dicts = _build_recovery_dicts(messages, tool_log, AR.RECOVERY_SYSTEM_DIRECTIVE)
                resp = await asyncio.to_thread(AG.llm_chat, fb_dicts, thinking=False, max_tokens=2000)
                reply = _visible_text(_strip_markers(resp["choices"][0]["message"].get("content") or ""))
                if reply:
                    note = AR.RECOVERY_NOTE_EN if language == "en" else AR.RECOVERY_NOTE_ZH
                    for piece in (note, reply):
                        # Patch 1 (B4): 恢复回答同样经 措辞净化 + 引用实时核验 + quote bound + 术语断言门
                        _vis = _phrase_scr.push(piece)
                        _vis = _citation_san.push(_vis)
                        _vis = _quote_san.push(_vis)
                        _vis = _term_gate.push(_vis)
                        for i in range(0, len(_vis), 60):
                            seg = _vis[i:i + 60]
                            full_answer += seg
                            yield {"type": "token", "content": seg}
                            await asyncio.sleep(0.002)
                    _recovered = True
            except Exception as _re:
                logger.warning(f"[graceful-completion] failed: {str(_re)[:200]}")
        if not _recovered and not _strip_markers(full_answer):
            _fail_ct = sum(1 for tc in tool_log
                           if isinstance(tc.get("result_full"), dict) and tc["result_full"].get("error"))
            _log_stats(agent, req_message, time.time() - _t_start, [t["name"] for t in tool_log],
                       _fail_ct, str(stream_error)[:200], 0)
            if trace:
                trace.finalize(time.time() - _t_start, error=stream_error, answer_chars=0,
                               budget_snapshot=budget.snapshot() if budget else {})
            if "Insufficient Balance" in str(stream_error) or "402" in str(stream_error):
                yield {"type": "error",
                       "content": "DeepSeek API 余额不足——请充值后重试" if language != "en"
                       else "DeepSeek API balance insufficient—please top up and retry"}
            else:
                # 脱敏: 客户端只给通用提示, 细节写日志（异常文本可能含 API 细节）
                yield {"type": "error",
                       "content": "智能体暂时出错，请重试或换个问法" if language != "en"
                       else "Agent error—please retry or rephrase"}
            return
    try:
        # 最终 flush: 最后一轮 agent 输出（最终回答）在 done 前以打字机发出（XML 标记已剥离）
        # O1: 原 synthesis 摘要生成器（runtime mini-LLM 代笔 thinking）已删除——
        # 最终回答前的 thinking 只能是模型自己在内容通道写下的工作笔记。
        _gtail = _term_gate.flush()
        _stail = _citation_san.flush()
        _qtail = _quote_san.flush()
        _ptail = _phrase_scr.flush()
        _tail = _visible_text(_rat_parser.finish())   # Patch 1 (B4-A): 未闭合 rationale 残留剥离标签后释放
        # Patch 1 (B4): 尾部释放——运行时措辞净化 → 术语断言门 → 引用核验器 → quote bound
        #   → rationale 残留, 全部净化后补发; 门/缓冲器持有的都是流的后缀,
        #   前置到 pending 可保持顺序（live 模式直接流出）
        _tails = _ptail + _gtail + _stail + _qtail + _tail
        if _tails:
            if pending.get("live"):
                for ch in _tails:
                    full_answer += ch
                    yield {"type": "token", "content": ch}
                    await asyncio.sleep(0.002)
            else:
                pending["text"] = _tails + pending["text"]
        async for ev in flush_agent():
            yield ev
        pending = {"text": "", "has_tools": False, "reasoned": False, "live": False, "live_text": ""}
        # 被截断的已宣告工具调用（宣告了 tool_start 但最终未执行, 如 hard 预算强制轮的
        # 二次残留宣告）: 逐名发 tool_cancel, 前端据此解除对应"调用中"卡片（2026-08-14）
        for nm in sorted(pending_tools):
            yield {"type": "tool_cancel", "name": nm, "reason": "工具预算已达上限，该调用未执行"}
        # 最终回答校验: 剥离工具标记后为空或过短 → 强制兜底生成正文（硬上限轮 LLM 可能
        # 只输出标记或半句标题就停——真实回归: F02 final 仅 12 字符的截断标题, 兜底因
        # "非空"未触发）。Phase A: 兜底调用同样携带已取得 evidence 摘要（与 graceful 同机制）
        # Patch 1.1 (P5): 核验类问题兜底指令携带四要素（verdict/最近原文/层次区分/确定性边界）
        if len(_strip_markers(full_answer).strip()) < 60:
            try:
                fb_dicts = _build_recovery_dicts(
                    messages, tool_log, _final_answer_directive(plan, verif_box, language))
                resp = await asyncio.to_thread(AG.llm_chat, fb_dicts, thinking=False, max_tokens=2000)
                reply = _visible_text(_strip_markers(resp["choices"][0]["message"].get("content") or ""))
                if reply:
                    # Patch 1 (B4): 兜底回答同样经 措辞净化 + 引用实时核验 + quote bound + 术语断言门;
                    # 并计入 full_answer（证据契约/安全审查/审计以最终可见正文为准）
                    reply = _phrase_scr.push(reply)
                    reply = _citation_san.push(reply)
                    reply = _quote_san.push(reply)
                    reply = _term_gate.push(reply)
                    for i in range(0, len(reply), 60):
                        full_answer += reply[i:i + 60]
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
        # ══ O1: 引擎兜底读取的回放与终局安全网已删除 ══
        # 原此处的 ① auto-read tool 事件回放 + "已完成主文本核验读取" 注记
        # 和 ② 收口前 _ensure_primary_read 终局补读（含"原典核验补正"正文补发）
        # 均为 runtime 代执行认知工具 / runtime 文本冒充 Agent 核验行为——按 O1 契约删除。
        # 主文本读取现在只能来自 Main Agent 宣告; 核验不足时模型会在收口轮收到
        # "最后核验机会"读章提示（prompt 层）, 由模型自己决定是否补读。
        # ══ Phase T.1 (T1.1-A): 已核验引用可见性保障（确定性 validator, 不依赖模型自觉）══
        # 义务满足 + 逐字命中（只能由模型自己的 get_chapter 达成）, 但最终正文没有任何
        # 指向已读章节的正式引用 → 补发一条带原文与【《书》·章】标注的核验说明。
        # validator 行为: initiated_by=runtime_mechanical（校验补正, 非 Agent 认知动作）。
        try:
            _vi_check = (plan.get("verification_intent") or {})
            if _vi_check.get("kind") and obligation_ledger is not None \
                    and obligation_ledger.obligations_satisfied \
                    and obligation_ledger.exact_quote_verified:
                _info = getattr(obligation_ledger, "primary_read_info", None) \
                    or _derive_read_info(raw_tool_log, verif_box.get("term") or _vi_check.get("term"))
                if _info and _info.get("passage"):
                    from evidence_contract import iter_citation_markers, _book_match, _chapter_match
                    _has_cite = any(_book_match(_info.get("book") or "", b)
                                    and _chapter_match(_info.get("chapter") or "", ch)
                                    for b, ch in iter_citation_markers(full_answer))
                    if not _has_cite:
                        _bk, _ch = _info.get("book") or "", _info.get("chapter") or ""
                        _cite_note = (f"（原典核验：「{_info['passage']}」——已读取"
                                      f"《{_bk}》·{_ch}原文完成逐字核验【《{_bk}》·{_ch}】。）")
                        async for _ev in emit_append(_cite_note):
                            yield _ev
        except Exception as _e:
            logger.warning(f"[verified-citation append] skipped: {str(_e)[:160]}")
        # ══ Phase T.1: 收口补正文本经净化链后的残留释放 ══
        # emit_append 的补正文本可能被 citation/quote/term 门持有后缀（如引句中的句读
        # 触发 term gate 缓冲）——真实回归: 引用补发只流出了前半句。此处按链序二次放行。
        try:
            _d1 = _citation_san.flush()          # citation 持有后缀（已过 phrase; 未过 quote/term）
            _d1 = _quote_san.push(_d1)
            _d1 += _quote_san.flush()            # quote 持有后缀（已过 phrase+citation; 未过 term）
            _d1 = _term_gate.push(_d1)
            _d3 = _term_gate.flush()             # term 持有后缀
            _resid = (_d1 or "") + (_d3 or "")
            if _resid:
                for i in range(0, len(_resid), 60):
                    _seg = _resid[i:i + 60]
                    full_answer += _seg
                    yield {"type": "token", "content": _seg}
                    await asyncio.sleep(0.002)
        except Exception as _e:
            logger.warning(f"[postloop drain] skipped: {str(_e)[:160]}")
        # ══ Phase T.1 (T1.1-D/G/H): Quote Bound 审计 + 收口一致性扫描 ══
        _quote_audit = None
        _vt0 = time.time()
        try:
            _quote_audit = QB.audit_quotes(full_answer, raw_tool_log)
            _q_satisfied = bool(obligation_ledger is None or obligation_ledger.obligations_satisfied)
            _q_read = bool(obligation_ledger is None or obligation_ledger.primary_text_read)
            for _qs in QB.scan_final_consistency(full_answer, _quote_audit, _q_satisfied,
                                                 primary_text_read=_q_read, language=language):
                async for _ev in emit_append(_qs):
                    yield _ev
            _quote_audit = QB.audit_quotes(full_answer, raw_tool_log)   # 补正后终态
        except Exception as _e:
            logger.warning(f"[quote-bound post] skipped: {str(_e)[:160]}")
        finally:
            if trace:
                trace.record_phase("validator_quote_bound", _vt0)
        # ══ Phase S (S2): Epistemic findings 重消费——answer_retract 不撤销 findings ══
        # 前提校正/反事实边界是结构化 epistemic state; 若最终可见正文未落实
        # （校正随 draft 被撤回 / LLM 忽略注入 / 回答被工具轮打断）→ 此处尾补,
        # 使 high-importance 校正必然出现在最终正文。
        _epistemic_state = None
        _vt0 = time.time()
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
        finally:
            if trace:
                trace.record_phase("validator_epistemic", _vt0)
        # ══ Phase S (S5): 预算扫描（先于 composer 扫描——超预算时抑制非必要结构提示）══
        _budget_scan = None
        _vt0 = time.time()
        try:
            if _composition_verdict:
                from answer_composer import scan_budget
                _budget_scan = scan_budget(_composition_verdict, full_answer)
        except Exception as _e:
            logger.warning(f"[answer-budget scan] skipped: {str(_e)[:200]}")
        finally:
            if trace:
                trace.record_phase("validator_budget_scan", _vt0)
        # Interpretation Engine 应答后校验: 解释型回答缺多候选/越级断言 → 措辞级补正
        # （确定性兜底, 仍是 token 事件; 置信度数字仅内部记录, 不发送给前端）
        _interpretation_scan = None
        _vt0 = time.time()
        try:
            if _interpretation_verdict:
                _interpretation_scan = scan_interpretation(_interpretation_verdict, full_answer, language, tool_log)
                for _ins in _interpretation_scan.get("appends", []):
                    if _ins:
                        async for _ev in emit_append(_ins):
                            yield _ev
        except Exception as _e:
            logger.warning(f"[interpretation-engine post] skipped: {str(_e)[:200]}")
        finally:
            if trace:
                trace.record_phase("validator_interpretation", _vt0)
        # Answer Composer 应答后校验: 结构信号 / 强化措辞 / 推理噪音 → 措辞级补正
        # （解释型问题已由 interpretation_scan 补正过则不再重复; 仍是 token 事件）
        _composition_scan = None
        _vt0 = time.time()
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
        finally:
            if trace:
                trace.record_phase("validator_composer", _vt0)
        # ── Phase 3: Evidence Contract（2026-08-30）────────────────────────────
        # 检索命中了什么 ≠ 回答用了什么。此前引用面板直接取 search_books 前 4 条命中
        # （retrieval candidates), 用户会误读为 answer evidence。现在统一抽取:
        #   retrieved_evidence（检索候选全集）→ used_evidence（回答实际引用/对齐的）
        #   → citations 只投影 used_evidence（引用面板新协议）; claims 携带知识论
        #   分级与证据绑定（SPECULATION 不绑定 DIRECT evidence）。
        # 尽力而为——任何异常只降级为空引用面板, 绝不影响主流程。
        evidence_payload = None
        _vt0 = time.time()
        try:
            from evidence_contract import build_evidence_contract
            # Patch 1.1 (P3): 来源约束传递——PRIMARY_ONLY/AUTHOR_ONLY 时二手不得进入
            # used_evidence/citations（retrieved/candidate 保留, excluded 单列审计）
            evidence_payload = build_evidence_contract(
                tool_log, full_answer, agent, language,
                source_constraint=_sc, subject_authors=_subjects)
            citations = evidence_payload["citations"]
        except Exception as _e:
            logger.warning(f"[evidence-contract] skipped: {str(_e)[:200]}")
            citations = []
        finally:
            if trace:
                trace.record_phase("validator_evidence_contract", _vt0)
        # ══ Patch 1 (B4-B): Citation Sanitizer——最终输出硬约束的断言层 ══
        # 未核验 formal citation 已在流式阶段被 LiveCitationSanitizer 降级为一般书名提及
        # （正文里不存在未验证的【《书》·章】）; 此处 sanitize_citations 仅作 final-output
        # assertion——unverified_before 应为 0, 命中则记日志; 不再追加"引用核验说明"补丁尾注。
        _citation_sanitize = None
        _vt0 = time.time()
        try:
            if evidence_payload is not None:
                from evidence_contract import sanitize_citations
                _citation_sanitize = sanitize_citations(full_answer, contract=evidence_payload)
                if _citation_sanitize and _citation_sanitize.get("unverified_before"):
                    logger.warning(
                        f"[citation-sanitizer] {len(_citation_sanitize.get('unverified_before'))} "
                        f"unverified citation(s) reached final text: "
                        f"{_citation_sanitize.get('unverified_before')[:3]}")
        except Exception as _e:
            logger.warning(f"[citation-sanitizer] skipped: {str(_e)[:200]}")
        finally:
            if trace:
                trace.record_phase("validator_citation_sanitize", _vt0)
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
        # ══ Phase T (T12): Tool Result Ownership 审计（须在 result_full 剥离前）══
        # tool_value: NEW_EVIDENCE/NEW_STATE/NEW_STRUCTURE/NEW_ARTIFACT/PRESENTATION/REDUNDANT
        # final_use : USED/PARTIALLY_USED/BYPASSED——REDUNDANT/BYPASSED 进入 observability anomaly
        _tool_ownership = None
        try:
            _tool_ownership = TC.tool_ownership_audit(tool_log, full_answer)
            if _tool_ownership and (_tool_ownership.get("bypassed_specialized_tools")
                                    or _tool_ownership.get("redundant_specialized_tools")):
                logger.info(f"[tool-ownership] bypassed={_tool_ownership['bypassed_specialized_tools']} "
                            f"redundant={_tool_ownership['redundant_specialized_tools']} "
                            f"detail={[e for e in _tool_ownership['entries'] if e['final_use'] == 'BYPASSED' or e['tool_value'] == 'REDUNDANT'][:4]}")
        except Exception as _e:
            logger.warning(f"[tool-ownership] skipped: {str(_e)[:160]}")
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
        # ══ Phase A (A1): 单轮 invocation 轨迹汇总落盘（evidence ids 关联证据契约）══
        _evidence_ids = []
        if evidence_payload:
            _evidence_ids = [ev.get("evidence_id") for ev in (evidence_payload.get("used_evidence") or [])
                             if ev.get("evidence_id")]
        if trace:
            if stream_error is not None:
                trace.finalize(time.time() - _t_start, error=stream_error,
                               answer_chars=len(full_answer), evidence_ids=_evidence_ids,
                               budget_snapshot=budget.snapshot() if budget else {})
            else:
                trace.finalize(time.time() - _t_start, error=None,
                               answer_chars=len(full_answer), evidence_ids=_evidence_ids,
                               budget_snapshot=budget.snapshot() if budget else {})
        # ══ Patch 1 (B5): 时期路由状态（哲学家智能体 + 时序问题; 审计/回归断言用）══
        _temporal_state = None
        try:
            if agent != "general" and plan.get("temporal", {}).get("detected"):
                _names = [t.get("name") for t in tool_log]
                _period_used = {y: RP.year_to_period(agent, y)
                                for y in (plan["temporal"].get("years") or [])}
                _corpus_periods = []
                for tc in raw_tool_log:
                    rf = tc.get("result_full") or {}
                    for e in (rf.get("echoes") or []):
                        if isinstance(e, dict) and e.get("period") and e["period"] not in _corpus_periods:
                            _corpus_periods.append(str(e["period"]))
                _temporal_state = {
                    "detected": True,
                    "years": plan["temporal"].get("years") or [],
                    "words": plan["temporal"].get("words") or [],
                    "periods_mapped": {str(y): p for y, p in _period_used.items() if p},
                    "period_tool_called": "philosopher_period" in _names,
                    "corpus_periods": _corpus_periods,
                }
        except Exception as _e:
            logger.warning(f"[temporal-state] skipped: {str(_e)[:120]}")
        yield {"type": "done", "citations": citations, "evidence": evidence_payload,
               "tool_calls": tool_log,
               "suggestions": suggestions, "safety": safety_flag,
               "composition": _composition_scan,
               # Phase A: tool loop 治理状态（UAT/审计断言用; 前端可忽略）
               "tool_loop": {"invocation_id": trace.invocation_id if trace else None,
                              "budget": budget.snapshot() if budget else None,
                              "model_retries": trace.model_retries if trace else 0,
                              "recovered_after_error": bool(stream_error),
                              "no_gain_calls": budget.no_gain if budget else 0},
               # O1: 单智能体因果链审计块——
               # engine_cognitive_auto_tools 恒为 0（引擎不再代执行任何认知性工具;
               # 全部 top-level 工具由 Main Agent 宣告, UAT/回归断言用）。
               "causal": {"provenance": "o1",
                          "engine_cognitive_auto_tools": 0,
                          "main_agent_tool_decisions": _main_agent_tool_decisions,
                          "agent_invocations": _agent_invocations,
                          "thinking_sources": "main_agent_only"},
               # O1 (§13): 机械 timing observability（llm_invocation / validator_* 阶段时长;
               # 工具级时长见 trace.calls 与 tool 事件, 此处为阶段汇总）
               "timing": {"phases": (list(trace.phases) if trace else []),
                          "total_ms": round((time.time() - _t_start) * 1000, 1)},
               # Phase S: 结构化状态随 done 输出（审计/前端可用, 不改变主协议）
               "epistemic": _epistemic_state,
               "obligations": _obligations_state,
               "budget": _budget_scan,
               "citation_sanitize": ({k: _citation_sanitize.get(k) for k in
                                      ("verified_citations", "unverified_before", "actions")}
                                     if _citation_sanitize else None),
               # Patch 1: 问题计划 / 核验状态 / 时期路由 / 检索充分性 / 引用净化统计
               # Patch 1.1: verification_intent / source_navigation / obligation 台账随 done 输出（审计）
               "plan": {"problem_type": plan.get("problem_type"),
                        "complexity": plan.get("complexity"),
                        "relations": plan.get("relations"),
                        "form_directive": bool(plan.get("form_directive")),
                        "chain_directive": bool(plan.get("chain_directive")),
                        "verification_intent": ({"kind": _vi.get("kind"),
                                                 "constraint": _vi.get("constraint"),
                                                 "term": _vi.get("term")}
                                                if _vi else None),
                        "source_navigation": bool(plan.get("source_navigation"))},
               "verification": ({"term": verif_box.get("term"),
                                 "state": verif_box.get("state"),
                                 "computed": verif_box.get("computed")}
                                if verif_box.get("term") else None),
               "obligation_ledger": (obligation_ledger.snapshot()
                                     if obligation_ledger is not None else None),
               # Phase T.1: Quote Bound 审计（引文核验状态 / 拼接检测 / 未核验 blockquote 计数）
               "quote_bound": (_quote_audit or {}),
               "temporal": _temporal_state,
               "retrieval_state": (retrieval_state.snapshot()
                                   if retrieval_state is not None else None),
               # Phase T (T12): 工具结果所有权审计（tool_value/final_use + anomaly 计数）
               "tool_ownership": _tool_ownership,
               "live_citation_sanitize": _citation_san.snapshot(),
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
        # 收口阶段异常（图流异常已在上方恢复处理; 此处兜底不丢观测）——
        # 2026-08-30 修复: 旧代码 error 路径把工具数硬编码记 0, 掩盖了"13 次调用后 error"的真实形态
        _fail_ct = sum(1 for tc in tool_log
                       if isinstance(tc.get("result_full"), dict) and tc["result_full"].get("error"))
        _log_stats(agent, req_message, time.time() - _t_start, [t["name"] for t in tool_log],
                   _fail_ct, str(e)[:200], len(full_answer))
        if trace:
            trace.finalize(time.time() - _t_start, error=e, answer_chars=len(full_answer),
                           budget_snapshot=budget.snapshot() if budget else {})
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
