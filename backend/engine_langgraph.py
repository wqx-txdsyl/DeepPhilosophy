# -*- coding: utf-8 -*-
"""LangGraph 引擎（PhiAgent v2）——替代自研流式 ReAct 循环

Claude Code 风格: 思考 → 工具调用（多工具并行）→ 观察 → 最终回答
SSE 事件词表（O5 收敛, 实际发射 12 类）: status / thinking_summary /
thinking_summary_delta / tool_start / tool_note / tool / tool_cancel / token /
validation_failed / error / done / suggestions
（RP1, O1-RP1: thought_stream 不再由引擎发出——provider 私有推理一律内部丢弃,
 public Thinking 唯一事实来源 = thinking_summary(_delta);
 answer_retract / reasoning_summary / auto_read 同为已删词表外事件）
工具: 复用 routes.agent 的 TOOLS 注册表（30 个工具平移为 StructuredTool, 零逻辑改动）
"""
import asyncio, hashlib, json, re, time, inspect
from typing import Annotated, Any, TypedDict

from loguru import logger
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

import routes.agent as AG   # 复用 TOOLS 注册表 / API 配置
import agents as AGENTS     # 智能体注册表（智能体广场: 通用 + 哲学家）
import agent_runtime as AR  # Phase A: tool loop 治理（观测/去重/预算/重试/终止）单一真源
import tool_contracts as TC  # Phase T: 工具架构（taxonomy/mermaid/措辞净化/所有权审计）
import quote_bound as QB     # Phase T.1: 逐字引文绑定（Quote Bound / T1.1-D~H）
from evidence_contract import EvidenceState  # O5: 执行事实登记（Evidence Store）

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
# O4 Cognitive Layer Collapse: soft 预算提示 / no-gain 提醒与强制 / 充分性收敛 /
# STREAM_ANSWER_DELAY（O2 起即仅作兼容常量）全部删除——"证据是否充分/是否该收口"
# 由 Main Agent 自主判断; runtime 只保留 hard 机械资源上限（AR.HARD_BUDGET_DIRECTIVE）。
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
   - 工具是你主动使用的研究手段, 不存在配额管制: 只要 additional 检索/阅读可能实质
     提升可靠性、深度或出处根基, 就主动去做——对可外部验证的主张、引文、出处与史实,
     优先直接证据而非记忆; 对解读类问题, 应收集足以呈现最强相关解读的证据, 而不是
     停留在第一个貌似可行的读法; 只要还有证据可能实质改善回答, 就继续研究;
   - 研究校准: 获得实质证据后更新你的研究问题——后续检索应指向尚存的不确定性、
     缺失来源或冲突解读, 不要因为"还能再搜"就对同一问题反复发同义词变体检索;
     重要主张已充分落地、继续研究不太可能实质改善回答, 或问题不依赖逐字核验且
     已有知识足以可靠作答时, 就综合作答——不要为显得研究充分而持续加检;
   - 避免冗余调用与不产生新理解的机械检索（同一查询的原样重复会被机械判重并复用旧结果）;
     但注意: 未执行≠库中无此书; 检索无命中也不代表结论不成立, 如实陈述即可。
2. 回答标注引用来源: 【《书名》· 章节名】。
   引文表达纪律: 引用块（markdown blockquote, > 引用块）与逐字引号都在向读者声明
   "以下措辞是原文"——只有当检索证据确实支撑该措辞时才这样呈现; 转述、你自己的解读与综合、
   记忆中的措辞、译文变体一律写成普通正文, 并在有用时明确说明是转述/大意——
   不要把自己的解释、综合或诚实声明排成引用块, 近似措辞不得当作逐字原文呈现,
   凭记忆给出的措辞不得作为逐字原文呈现, 除非有检索支撑。
   引用标签纪律: 正式引用里的书名/章节/卷号/节号标签必须取自检索证据给出的书目信息
   （工具结果中的书名/章节字段）, 不得凭记忆补造章节号或格言号; 若只核验到书级,
   就只标书级（【《书名》】）或不给正式引用, 而不是补一个未经核验的精确位置。
   落笔前自检: 每处被呈现为原文的引号/引用块与每个正式引用标注, 都必须有本次会话
   检索证据的支撑; 精确引文对回答并非必要时, 宁用准确的普通表述, 不补造引证精度。
3. 涉及哲学家关系用 query_graph; 流派用 get_school; 哲人资料用 get_philosopher; 概念溯源用 concept_trace。
4. 用户要求对比可用 compare_views; 写作文用 write_essay; 辩论用 philosopher_debate; 决策求助用 advisor_council;
   扮演/以哲学家口吻回答用 role_play; 苏格拉底式追问用 socratic_tutor; 论证分析用 analyze_argument;
   用户要求"画脑图/思维地图/概念地图/概念图/关系图/梳理XX的概念关联/画图展示论证链条"时调用 conceptual_map
   （它返回结构化 graph 与已验证的 mermaid 图形——直接采用, 不要自己手写 ASCII 树或改写节点）。
   对比两位哲学家/两个流派在同一问题上的立场差异时可用 compare_views——它内部已检索
   双方材料并返回比较脚手架（共同问题/比较轴线/双方主张/证据需求）; 是否使用它、
   还是自行多路检索对比, 由你根据问题自行判断。
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
   普通概念解释、出处核验类问题不要附加原典路径。
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
14. 【技能重入纪律】同一 reasoning/generation 技能对同一议题避免退化重复
    （只把上次输入缩短/微调再调一次没有意义）: 只有用户明确要求迭代（参数体现变化点）/
    上次调用失败/出现实质新议题时才再次调用。socratic_tutor 一次只返回一个问题——
    用户回答后再次调用并传 user_reply=用户的回答, 绝不预生成后续轮次;
    向用户展示时只呈现该 next_question（至多加一句铺垫）, **不得在它之外再追加你自己的新问题**。
15. 【运行时措辞】不要在最终回答中出现内部过程措辞（如"检索已收口/预算已达上限/准入未通过/系统收敛"）——
    那是系统内部治理语言。材料是否充分、哪些未能核验, 用第一人称的确定性边界表述。
16. 【多轮证据边界】会话历史（包括你此前轮次的回答）是对话语境, 不是证据——逐字引用与
    正式引用必须落在本次会话检索到的证据上, 不能只靠"我前几轮说过"。已检索过的合法
    证据不会丢: 续谈需要精确措辞时, 对已知出处做一次定点重读即可, 无需把此前的检索
    链条全部重跑; 不需要逐字原文时, 用转述自然衔接即可。
17. 【修复策略·修复合同】回答被确定性校验打回时, 修复既不是原样重复也不是重写, 而是
    一次只更正失败处的收敛动作: 先逐条读校验反馈的机械数据（片段定位/不匹配类型/
    覆盖度/证据出处）, 定位每一个被打回的 span; 已成立的部分保持不动, 只修被打回的
    表达——证据支持观点但不支持精确措辞或引用标签时, 只在该处修改表达; 主张缺乏支撑且
    非必要时不补造精度, 删除或弱化即可; 该主张重要且证据可补时才做针对性研究。重新
    提交前自查: 被打回的 span 与未经支撑的精确主张已全部消除, 修复说明写成普通正文,
    未引入新的失范。"""

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

# ── O7-E §3-§16/§48: Scholarly Contract（单一 canonical owner）─────────
# 所有 agent（General 与哲学家人格）经 _build_context_messages 组合同一段契约:
# persona 只影响 voice/perspective, 不改变 source truth 与学术纪律。
SCHOLARLY_CONTRACT = """
【学术研究契约（Scholarly Contract）】你服务于一个哲学学术研究网站。默认目标不是百科式介绍,
而是帮助用户进入一个哲学问题真实的研究结构。优先考虑: 原典位置与上下文、论证结构、关键术语、
解释传统、真正存在的学术争议、不同解释的证据基础、主张的认识论地位、可继续深入的文献路径。

A. 宽泛哲学家提问（如仅问"康德/尼采/黑格尔"）: 不要以生卒年月、轶事、名言、关键词列表、
代表作罗列为主体; 应形成真实研究入口——核心问题地图（如康德: 先验唯心论/两世界与两方面争议/
先验演绎/自由与自律/自然—自由问题/第三批判/德国观念论后续）、主要原典路线、解释争议与后续
阅读路径。具体切入点由你根据问题判断。生平仅当对哲学问题、文本生成史或概念变化有研究意义时
才作为语境使用, 不用轶事填充学术深度。

B. 具体论证问题（"为什么X认为…/某论证怎么成立"）: 优先 路径 = 定位文本 → 重建论证
（前提/推理/结论）→ 指出关键争议 → 进入解释史; 不只给课本结论。

C. 解释类问题: 学界确有争议时, 不得把一个解释写成"X 显然意指…"。内部区分四类认识论地位:
文本事实 / 学界共识 / 有争议的解释 / 你的综合判断——不必每句打印标签, 但表述要如实反映地位。

D. 证据使用: 主动但不机械。当工具能明显提高可靠性/文本定位/解释深度/书目真实性/历史准确性时
主动使用; 不设任何工具数量或文献数量配额。原典主张、原文措辞、论证重建优先用原典工具; 逐字
引文必须来自实际检索证据, 不得凭记忆生成。

E. 二手文献: "某学者认为/某种解释传统/学界争论/论文X论证"类的文献存在性, 必须来自
search_scholarship / get_scholarly_source 的真实检索记录（本地 curated registry 或
Crossref/OpenAlex）, 不得凭记忆补书目。文献不是答案末尾的装饰, 应服务: 这个问题为什么有
争议、不同立场如何分叉、下一步读什么、为什么读它。

F. 访问诚实: METADATA_ONLY 只能确认文献存在与书目信息; ABSTRACT_AVAILABLE 只能描述摘要
实际支持的内容; FULL_TEXT_AVAILABLE 只表示全文可取得不表示已读; FULL_TEXT_READ 才能描述
实际读取正文所支持的内部论证。禁止从标题推断论文观点。使用持久化历史证据时, 不得暗示"刚刚
重新打开并阅读了全文"。

G. 不造假权威: 证据只支持"论文存在"就只能说存在; 不写"Smith 证明了…"除非证据真正支持该
归因。历史纪律: 避免时代错位词汇、后世问题倒灌原作者、把现代解释当成作者自述。哲学家人格
第一人称时, 区分历史文本可支持的自述与后世 scholarship——不得让尼采"知道"20/21 世纪论文。
"""


def get_system_prompt(agent):
    return AGENTS.AGENT_PROMPTS.get(agent, SYSTEM_PROMPT_LG)


# ── O4-RP1 §8: 单源 Context Builder ──────────────────────────────
# Main Agent 上下文的唯一组装点: 主系统提示（SYSTEM_PROMPT_LG / AGENT_PROMPTS）
# + 用户个性化指令 + 语言覆盖 + 人格强化提醒 + 时期人格上下文（agents 层）
# 组装为一条合并 SystemMessage——runtime 不再有任何分段认知注入
# （问题分类/核验纪律/来源约束/核验状态等注入源已随 Shadow cognition 删除）。
# 请求路径的 SystemMessage 注入点 = builder（本函数）+ hard 预算（机械状态, 允许）。
# ── O6-Q1 §10/§11: 当前 responder 身份事实（机械上下文, 非语义解析）──
# General ↔ 哲学家人格切换时, 明确"本轮谁在回答"; 会话历史消息可能出自不同 responder,
# 历史对话内容不改变当前人格, 也不自动成为证据（证据边界见铁律 16——policy 层）。
# 只包装结构化事实（当前 responder 是谁/历史可能含其他角色）, 不做指代解析。
def _identity_context(agent, language="zh"):
    if language == "en":
        if agent == "general":
            return ("[Responder identity] You are DeepPhilosophy (the general agent). "
                    "Earlier turns in this conversation may contain replies from a philosopher persona or "
                    "another role—that is conversation history: it does not change who is answering now, "
                    "and it is not evidence by itself.")
        name = (AGENTS.PHILO_AGENTS.get(agent) or {}).get("name") or agent
        return (f"[Responder identity] You are {name} (philosopher persona). Earlier turns may contain "
                "replies from the general agent or other roles—that is conversation history: it does not "
                "change your current persona, and it is not evidence by itself.")
    if agent == "general":
        return ("（本轮回答者身份：你是深哲——通用哲学智能体。会话历史中可能出现哲学家人格或其他角色的"
                "回复：那是对话历史，不改变本轮由谁回答，也不自动成为证据。）")
    name = (AGENTS.PHILO_AGENTS.get(agent) or {}).get("name") or agent
    return (f"（本轮回答者身份：你是{name}——哲学家人格。会话历史中可能出现通用深哲或其他角色的回复："
            "那是对话历史，不改变你当前的人格，也不自动成为证据。）")


def _build_context_messages(agent, language, custom_instructions=None,
                            user_message=None, reinforce=False):
    """构建 Main Agent 上下文消息（返回 list, 恒为一条 SystemMessage; 无内容时为空）。

    reinforce=False  完整上下文（每请求一次, 置于消息列表头部）
    reinforce=True   每轮强化消息: 人格 + 语言合并为一条, 不再分段（agent_node 用）
    时期上下文只随完整上下文注入（persona/context snapshot, 不逐轮重复）。"""
    if reinforce:
        parts = []
        if agent != "general":
            parts.append(PERSONA_THINK_REMINDER_EN if language == "en" else PERSONA_THINK_REMINDER)
        if language != "en":
            # 中文模式每轮强化: 内部思考与回答都必须中文（DeepSeek 偶发英文思考的防线）
            parts.append("（语言提醒：你的内部思考过程（thinking/reasoning）与最终回答都必须使用中文。禁止用英文思考。")
        return [SystemMessage(content="\n\n".join(parts))] if parts else []
    prompt = get_system_prompt(agent)
    # O7-E RP1 §2: Scholarly Contract 仅注入 General Agent（哲学家 Agent 退出 O7-E
    # scope; 其学术化留待专门设计）——单一 canonical owner 不变
    if agent == "general":
        prompt = prompt.rstrip() + "\n\n" + SCHOLARLY_CONTRACT
    if custom_instructions and custom_instructions.strip():
        prompt = (prompt.rstrip() +
                  f"\n\n## 用户的个性化指令（必须遵守）\n{custom_instructions.strip()}")
    # 语言切换（zh/en）: 覆盖 system 内的语言要求（思考流 + 回答）——"覆盖"语义, 防止与旧中文要求冲突
    if language == "en":
        prompt += ("\n\n【语言设置·重要】用户已切换到英文模式。以上（包括系统提示中）所有'使用中文'的指示一律作废。"
                   "思考流与回答必须全部使用英文（English），工具调用与引用也可用英文。禁止再用中文输出。")
    else:
        prompt += ("\n\n【语言要求】所有输出必须使用中文——包括内部思维过程（推理链）与回答。禁止用英文思考或输出。")
    # O6-Q1 §10/§11: 当前 responder 身份事实——并入同一条 SystemMessage（builder 单源）
    prompt += "\n\n" + _identity_context(agent, language)
    if agent != "general":
        # 人格保持提醒（多轮对话后 reasoning 易回归任务规划腔的关键防线）——并入同一条消息
        prompt += ("\n\n" + (PERSONA_THINK_REMINDER_EN if language == "en" else PERSONA_THINK_REMINDER))
        # 时期人格上下文（Persona/Context layer, agents 层持有）——仅哲学家智能体 + 检测到时期维度
        if user_message:
            try:
                _temporal = AGENTS.detect_temporal(user_message)
                if _temporal.get("detected"):
                    _td = AGENTS.temporal_directive(agent, _temporal, language)
                    if _td:
                        prompt += "\n\n" + _td
            except Exception as _e:
                logger.warning(f"[temporal-context] skipped: {str(_e)[:120]}")
    return [SystemMessage(content=prompt)]

# ── StateGraph ─────────────────────────────────────────
class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    forced: bool   # 已注入"强制回答"提示（hard 预算后, 确保最终轮产出回答）
    forced_tools_done: bool   # 强制回答后已补跑过一轮工具（防死循环烧钱; 2026-08-14）
    agent: str     # 当前智能体（general / 哲学家 key）
    language: str  # zh/en——中文模式下每轮强化语言提醒（防思考偶发英文）
    # ── Phase A: tool loop 治理状态（对象经内存态传递, 无 checkpointer 序列化）──
    guard: Any            # DuplicateGuard（A2, 单轮生命周期）
    budget: Any           # ToolBudget（A3; O4 后只剩 hard 资源上限 + 遥测计数）
    trace: Any            # ToolLoopTrace（A1）
    tool_count: int       # 本轮已执行工具调用总数（A3 total 预算口径）
    # ── O5: 执行事实与共享工具记录（对象经内存态传递）──
    # O4/O4-RP1 删除的 state 字段: retrieval_count / no_gain_streak / round_all_low /
    # round_any_low / retrieval_state / reentry / user_message（Shadow cognition
    # 遥测与重入治理）+ plan / verif_box（Python 先解释用户问题再下认知指令的
    # 最后残余——问题分类/核验意图/术语核验状态链已整体移除）。
    # O5 删除: model_retries（write-only; 重试计数真源 = trace.model_retries）/
    # obligation_ledger（→ evidence_state, EvidenceState 纯事实登记）。
    evidence_state: Any   # EvidenceState（evidence_contract; 纯事实登记器）
    raw_tool_log: Any     # 共享 raw 工具记录列表（tools_node 写入, 引擎消费; 引用核验用）
    # O7-E RP1 Final Closure A: 零工具 repair 的正式 State channel——
    # hard 预算已成立的 repair invocation 由 _stream_graph(no_tools=True) 置位,
    # agent_node 读取后不 bind tools（资源控制, 非认知决策）
    no_tools: bool

async def agent_node(state):
    msgs = list(state["messages"])
    agent = state.get("agent", "general")
    # ── O4-RP1 §8: 单源 Context Builder——每轮强化消息由 builder 产出
    # （人格 + 语言合并为一条, 不再分段; 无核验状态/意图类注入）──
    for _m in _build_context_messages(agent, state.get("language", "zh"), reinforce=True):
        msgs.append(_m)
    # ── Phase A: 预算与终止条件 ──
    # ══ O3 §5/§8: 停止权威归还 Main Agent——runtime 仅在机械约束下停止循环 ══
    # 保留: hard 全局资源上限（硬上限到达 → 注入机械指令 + forced 补跑一轮已宣告调用）。
    # 移除（O3 降级为 telemetry, O4 整体删除——检测器与状态链不复存在）:
    #   soft 预算提示 / no-gain 提醒与强制 / 充分性强制收口（含"最后核验机会"引导）/
    #   ledger 拒绝空转防护 / 检索次数提示。
    # "证据是否充分/是否该收口/该不该换工具"自 O3 起由 Main Agent 自主判断。
    budget = state.get("budget")
    forced = False
    if state.get("no_tools"):
        pass   # 零工具 repair 轮: 无工具可宣告, 不注入 hard 指令（防诱导工具宣告）
    elif budget is not None and budget.hard_reached():
        # hard 预算（机械资源上限）: 终止工具循环 → graceful answer completion。
        # 保留工具绑定（解绑会导致 LLM 退化为写 XML 文本调用）; 硬提示让 LLM 直接回答。
        # 后续 tools 轮中新宣告的调用将被机械拒绝（RESOURCE_CEILING_REACHED）。
        msgs.append(SystemMessage(content=AR.HARD_BUDGET_DIRECTIVE))
        forced = True
    # ── O1: 引擎不再代执行任何认知性工具（原 _ensure_primary_read auto-read 已删除）。
    # 主文本读取由 Main Agent 自己宣告; 引擎只保留确定性校验（quote/citation validator,
    # 见收口阶段）。──
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
    resp, retries = await _agent_llm_invoke(agent, msgs, trace=_trace_ref,
                                            no_tools=bool(state.get("no_tools")))
    if _trace_ref is not None:
        try:
            _trace_ref.record_phase("llm_invocation", _llm_t0, msgs_len=len(msgs))
        except Exception:
            pass
    # O5: model_retries state 字段已删（write-only）——重试计数真源 = trace.model_retries
    return {"messages": [resp], "forced": forced}

async def _agent_llm_invoke(agent, msgs, trace=None, no_tools=False):
    """agent 轮 LLM 调用（线程池防阻塞）+ A4 有限重试。返回 (resp, retry_count)。

    O7-E RP1 §7: no_tools=True 仅用于「hard 预算已成立的 repair invocation」——
    绑定零工具防 RESOURCE_CEILING×forced_tools_done 空候选死路（资源控制, 非认知决策）。"""
    def _call(m):
        if no_tools:
            return get_llm().invoke(m)
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
# O5: 引擎侧"从 raw_tool_log 推导已读章节"的函数已删除（零消费者——term 术语
#   核验状态链随 O4-RP1 移除后再无调用方; 已读章节事实现由 EvidenceState 登记）。

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
    按当前智能体的工具集查找（哲学家专属工具不在全局注册表里）;
    自愈: 失败工具按 TOOL_RETRY 配置重试, 仍失败附备选工具提示。
    Phase A: A2 重复调用防护（同参只读工具 → 复用结果, 不再执行）;
             A3 预算分类计数（useful/retry/duplicate/no_gain——纯遥测）;
             A1 逐调用观测（时长/成败/结果 hash/info gain）。
    O3/O4: 工具权威归还 Main Agent——本节点只保留机械门（未知工具/参数错误、
    精确重复复用、硬资源上限）; 语义准入（obligation admission）、
    skill 重入治理、RetrievalState 语义增益统计已全部删除。
    （安全审查在收口阶段 _safety_check; 截断取消在收口阶段 tool_cancel——均不在本节点。）"""
    last = state["messages"][-1]
    calls = last.tool_calls or []
    agent = state.get("agent", "general")
    tools_map = {t.name: t for t in get_tools(agent)}
    guard = state.get("guard")
    budget = state.get("budget")
    trace = state.get("trace")
    raw_log = state.get("raw_tool_log")
    ev_state = state.get("evidence_state")
    retrieval_set = set(RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS)
    TOOL_TIMEOUT = AR.TOOL_TIMEOUT   # 工具执行超时（防挂起; Phase A 收编为配置）
    forced = bool(state.get("forced"))

    async def run_one(call, call_index):
        name = call.get("name", "")
        args = call.get("args", {}) or {}
        tool = tools_map.get(name)
        thought_label = f"执行 {name}"
        # ── O3 §5/§8: 全局硬资源上限——唯一保留的机械拒绝门 ──
        # 只表达 RESOURCE_CEILING_REACHED（资源约束）, 绝不暗含"证据已充分/库中无此书"。
        if budget is not None and budget.hard_reached():
            skip_res = {"error": "RESOURCE_CEILING_REACHED: 全局工具执行硬上限已达"
                                 f"（本调用未执行——这是机械资源约束, 不代表库中无相关内容; "
                                 f"请立即基于已取得的材料输出最终回答）。"}
            if trace:
                trace.record_call(call_index, name, args, 0.0, False, None,
                                  json.dumps(skip_res, ensure_ascii=False)[:200],
                                  AR.result_hash(skip_res), "ceiling", "", 0,
                                  executed=False, thought="RESOURCE_CEILING_REACHED",
                                  decision_group=getattr(trace, "current_group", None),
                                  tool_call_id=call.get("id"))
            return ToolMessage(content=json.dumps(skip_res, ensure_ascii=False)[:4000], name=name,
                               tool_call_id=call.get("id", ""),
                               additional_kwargs={"_args": args, "_result_full": skip_res,
                                                  "_budget_class": "ceiling", "_info_gain": "",
                                                  "_dg": getattr(trace, "current_group", None)})
        # ── O3 §3: 精确重复复用（机械判重: 同工具 + 归一化后完全相同参数）──
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
        # ── A1 information gain / A3 预算分类（可靠实现: 空命中判定;
        #     O4: RetrievalState 语义 low_gain 统计已删——只留 empty/new 机械判定）──
        rh = AR.result_hash(res)
        info_gain = ""
        if not is_err and name in retrieval_set:
            info_gain = "empty" if AR.result_is_empty(res) else "new"
        # ── O5: EvidenceState 事实登记（纯事实: 已读章节/主文本已读/定位线索命中/
        #     执行计数——成败都登记检索计数, 只有成功读取才置位 READ; 无任何
        #     准入/配额/义务判定）──
        if ev_state is not None and name in retrieval_set:
            try:
                if name == "get_chapter":
                    if not is_err:
                        ev_state.record_read(args.get("book_id"), args.get("chapter_idx"))
                else:
                    ev_state.record_search(not is_err, res)
            except Exception as _le:
                logger.warning(f"[evidence-state] skipped: {str(_le)[:120]}")
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
        # ── Phase T (T9) + O3 §16: 专用工具自带的原典证据进入 Evidence Contract 查证池 ──
        #（confrontation/compare_views 等内部检索的结构化 citations/evidence——最小接口适配:
        #  只进 raw_log（引用核验/证据契约池, 使主 Agent 的正式引用可被核验）,
        #  不进 tool_log/预算/trace, 不改变检索口径。
        #  O3 §16: 内部检索必须如实溯源——initiated_by=tool_internal + parent_tool_call_id,
        #  不得伪装成 Main Agent 亲自宣告的 search_books（FAKE_TOP_LEVEL_TOOL_LOGS=0）。）
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
                                    "thought": f"{name} 结构化证据入池（契约核验用）",
                                    "initiated_by": "tool_internal",
                                    "parent_tool_call_id": call.get("id"),
                                    "parent_tool": name,
                                    "pseudo": True})
        content = json.dumps(res, ensure_ascii=False) if isinstance(res, (dict, list)) else str(res)
        return ToolMessage(content=content[:4000], name=name,
                           tool_call_id=call.get("id", ""),
                           additional_kwargs={"_args": args, "_result_full": res,
                                              "_budget_class": cls, "_info_gain": info_gain,
                                              "_dg": getattr(trace, "current_group", None)})

    base_index = state.get("tool_count", 0)
    results = await asyncio.gather(*[run_one(c, base_index + i) for i, c in enumerate(calls)])
    executed = sum(1 for r in results
                   if (getattr(r, "additional_kwargs", {}) or {}).get("_budget_class") != "duplicate")
    # O4: no_gain_streak / round_all_low / round_any_low / retrieval_count 状态链已删——
    # 预算快照内的 no_gain 计数（遥测）保留。
    return {"messages": results,
            "tool_count": base_index + executed,
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
    # O3 §5/§8: forced 仅剩机械硬上限一个触发源（agent_node）。强制回答轮里模型仍宣告
    # 工具（DeepSeek 常见"任务规划残留"）→ 补跑一轮: 新宣告调用在 tools_node 被机械拒绝
    # （RESOURCE_CEILING_REACHED）并回传结果, 下一轮强制结束（§17 结果完整性）。
    if state.get("forced"):
        if state.get("forced_tools_done"):
            return "end"
        return "tools"
    return "tools"

# O4: _ROUTING_PHRASE_RE / _is_routing_injection 已删除——语义路由注入源
# （interpretation/composer/MAP_HINTS/COMPARISON 路由）已整体移除;
# O4-RP1 后上下文唯一来源是 _build_context_messages（本就不含路由措辞）, 无需过滤。

_builder = StateGraph(AgentState)
_builder.add_node("agent", agent_node)
_builder.add_node("tools", tools_node)
_builder.add_edge(START, "agent")
_builder.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
_builder.add_edge("tools", "agent")
APP = _builder.compile()

# ── SSE 流式入口: stream_agent 产事件 dict, 序列化在 routes/agent_sse ──

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
# ══ O2: 原 _final_answer_directive / _build_recovery_dicts（第二 writer 的指令与
# 消息装配器）已删除——runtime 不再持有独立的"答案生成通道"。transport 异常的恢复
# 改为同一个 Main Agent 的原样重试（见 stream_agent 内 graceful 路径）。

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
    # ── O4-RP1 §8: 单源 Context Builder——主系统提示 + 个性化指令 + 语言覆盖 +
    # 人格强化 + 时期人格上下文（agents 层）合并为一条 SystemMessage。
    # 已删除的注入源: PremiseVerifier 事实校正注入（runtime 不得替 Agent 下
    # "用户前提错了"的结论——事实由 Main Agent 自主检索核验后自行纠正）、
    # 核验纪律 / 来源约束 / 术语核验状态注入（Python 先解释用户问题再教模型
    # 怎么认识它的认知层——全部移除, 任务理解归还 Main Agent）。
    messages = _build_context_messages(agent, language, custom_instructions, req_message)
    for h in (history or [])[-20:]:
        role = h.get("role", "user")
        content = h.get("content", "")
        messages.append(HumanMessage(content=content) if role == "user" else AIMessage(content=content))
    messages.append(HumanMessage(content=req_message))
    # ══ O3 §14: 强制专用工具路由已移除（ROUTING_CONTROL_EFFECT = 0）══
    # 原 MAP_HINTS（"必须调用 conceptual_map, 禁止手写"）与 COMPARISON 路由注入
    # （"优先调用 compare_views, 不要自行多路检索"）删除——工具选择权归还 Main Agent;
    # 各工具的 capability 描述（工具 schema description）已说明适用场景, 由模型自主选择。
    tool_log = []
    # ── Phase A: tool loop 治理状态（A1 观测 / A2 去重 / A3 hard 预算——单轮生命周期对象）──
    guard = AR.DuplicateGuard()
    budget = AR.ToolBudget(retrieval_tools=set(RETRIEVAL_TOOLS) | set(AGENTS.PHILO_EXTRA_TOOLS))
    trace = AR.ToolLoopTrace(conversation_id, message_id, agent, question_chars=len(req_message or ""))
    # ── O5: EvidenceState（纯事实登记器; 旧义务台账 / RetrievalState 语义统计已删）──
    evidence_state = EvidenceState()
    raw_tool_log = []   # 共享 raw 工具记录（tools_node 写入; 引用核验/证据契约消费; result_full 保留到收口）
    # ══ O2: Final Answer Ownership——runtime 只保留 VALIDATE / REJECT / mechanical FORMAT ══
    # 流式改写链（LiveCitationSanitizer 引用降级 / QuoteBoundSanitizer 引文转写 /
    # TermClaimGate 句子改写）整体删除: 未核验对象不再被 runtime 改写, 而是作为
    # 结构化 ValidationIssue 打回同一个 Main Agent 修复（final_validator.py）。
    # O4-RP1: validator 只依赖 candidate + evidence——不再接收任何来源约束/
    # 提问对象/意图分类参数（FINAL_VALIDATOR_GENERAL_INTENT_DEPENDENCY = 0）。
    from final_validator import (validate_final_candidate, format_feedback,
                                 MAX_VALIDATION_REPAIRS)
    # Phase T (T13-B): 运行时措辞净化器——内部治理语言（"检索已被收口/预算已达上限/…"）
    # 不得进入 Final prose; 流式安全（跨 chunk 缓冲）。机械净化, 不改变语义内容。
    _phrase_scr = TC.RuntimePhraseScrubber()
    # O4: _reentry_tracker（SkillReentryTracker）已随 tool_contracts 瘦身删除——
    # skill 重入治理属语义控制, 工具选择/迭代判断归 Main Agent。
    # 2026-08-28: 递归上限 18 → 60（检索硬上限已取消, 需给足长会话空间——~29 轮工具;
    # 仍是有界兜底, 防失控烧钱）。Phase A: 数值收编 agent_runtime.RECURSION_LIMIT 配置
    config = {"recursion_limit": AR.RECURSION_LIMIT}
    # 当前 agent 轮缓冲（O2: 轮文本一律只缓冲, 不再实时流出——
    # 有工具 → 轮末降级为 thinking_summary; 无工具 → Final Candidate, 校验后发布;
    # note_emitted: 本轮公开工作笔记已作为 thinking_summary 发出, flush 不再重复）
    # O5: reasoned 标志已删（只写不读——provider reasoning 一律内部丢弃, 无观察消费方）
    pending = {"text": "", "has_tools": False, "started": set(),
               "note_emitted": False}
    pending_tools = set()   # 本轮已发 tool_start 但尚未执行的工具 (name, tool_call_id)
                            # （2026-08-14: 用于截断时发 tool_cancel 解除前端"调用中"卡片;
                            #  O6-RP1 F2/F3: 携带 tool_call_id, 终态取消逐 id 绑定）
    full_answer = ""   # 已转发的所有回答文本（最终校验用）
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
        if txt and not pending.get("note_emitted"):
            evs.append(_note_event(txt, _phase_for()))
            pending["note_emitted"] = True
        return evs

    # ══ O2: emit_append 已删除——runtime 不再向正文追加任何文本 ══
    # （原通道承载: 原典核验补发 / scan_final_consistency 尾补 / epistemic 纠正与
    #  反事实边界 / interpretation·composition hedge——全部为 runtime 代写, 按 O2 §7 删除。）

    async def flush_agent():
        """agent 轮结束定归属（O2）: 有工具调用 → 本轮缓冲文本只作公开工作笔记
        （O1: 笔记已在首个工具宣告前经 _flush_working_note 归位, 此处仅兜底补发
        未发过的部分, 防规划文字泄漏为回答）; 无工具 → 缓冲保留为 Final Candidate,
        由调用方在图流结束后统一校验 + 发布（未验证候选绝不先于 validator 公开）。"""
        if not pending["has_tools"]:
            return
        text = pending["text"]
        if not text:
            return
        # O1: 工具轮公开工作笔记（模型内容通道原文）→ thinking_summary。
        # 这是 Main Agent 自己写给用户的工作判断——不是 runtime 代笔。
        _txt = text.strip()[:280]
        if _txt and not pending.get("note_emitted"):
            yield _note_event(_txt, _phase_for())
            pending["note_emitted"] = True
    # ══ Phase A (A4/A5): 图流执行与异常恢复分离 ══
    # 此前整轮（图流 + 收口 + done）包在同一个 try 里, 图流中任何异常（如模型侧
    # 流式连接中断"peer closed connection..."）直接以 error 事件终止整轮——已完成的
    # 全部工具调用取得的 evidence 一并丢弃（RAM audit 第 9 轮"约 13 次工具调用后
    # 模型侧 error"的真实路径）。现在: 图流异常先走 graceful completion（用已取得
    # evidence 完成回答）, 恢复成功/已有部分正文 → 继续正常收口（citations/done 照常）。
    stream_error = None

    async def _stream_graph(msgs, no_tools=False):
        """跑一遍图流（一组 Main Agent invocation 序列）——O2: 首次运行与 validator
        repair 运行共用同一条路径（repair 绑定完整 tool set, 遵守 O1 causal contract）。
        thinking/tool 活动实时 yield; 候选正文只进缓冲, 绝不提前公开。
        共享状态经闭包更新（nonlocal）。"""
        nonlocal pending, _agent_invocations, _saw_tools_result
        nonlocal _main_agent_tool_decisions, _rat_tools_done, _rat_phase
        # O6-RP1 (F2): 每次新 Main Agent invocation 从确定性干净 pending 起步——
        # 上一 invocation 的工具宣告状态必须已在其终态闭合中清除, 不跨轮泄漏
        # （repair/恢复轮的新候选不得被上一轮残留宣告的 has_tools 卡 True 丢弃）。
        pending = {"text": "", "has_tools": False, "started": set(), "note_emitted": False}
        pending_tools.clear()
        async for chunk, metadata in APP.astream(
                {"messages": msgs, "agent": agent, "language": language,
                 "guard": guard, "budget": budget, "trace": trace,
                 "no_tools": no_tools,
                 "tool_count": 0,
                 "evidence_state": evidence_state,
                 "raw_tool_log": raw_tool_log},
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
                    # O2 §12: answer_retract 的语义用途随"先流出后撤回"模式一并删除——
                    # 候选文本从不提前公开, 无需撤回（FINAL_RETRACT_SEMANTIC_USE=0;
                    # 事件类型保留给纯 transport/rendering 恢复场景）。
                    for tcc in tool_call_chunks:
                        nm = tcc.get("name")
                        if not nm:
                            continue
                        # O6-RP1 (F3): 去重键 = tool_call_id（缺失时退回 chunk index）——
                        # 每个真实宣告的 tool_call_id 恰发一个 tool_start。旧实现按
                        # 工具名去重: 并行同名调用（各有独立 id）只发一个 start, 其余
                        # 结果事件无可见父级（UNPARENTED_TOOL_RESULTS 根因）。
                        # 同批共享 decision_group_id, 不共享 tool_call_id。
                        _started = pending.setdefault("started", set())
                        call_key = tcc.get("id") or f"idx:{tcc.get('index')}"
                        if call_key in _started:
                            continue
                        _started.add(call_key)
                        pending_tools.add((nm, tcc.get("id")))
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
                    # O2: 机械净化（控制标签/内部治理措辞剥离）后只累积——
                    # 引用/引文的资格判断移到 final validator（结构化反馈）, 流式阶段不改写。
                    _vis = _visible_text(_emit_text)
                    _vis = _phrase_scr.push(_vis)
                    if not _vis:
                        continue
                    chunk.content = _vis
                    # 只累积本轮文本——归属（思考 or Final Candidate）在轮结束 flush 时决定;
                    # 未经验证的候选文本绝不先于 validator 到达用户
                    # （O2 §11: INVALID_FINAL_PUBLICLY_STREAMED = false）。
                    pending["text"] += _vis
                # Provider 私有推理（DeepSeek reasoning_content）→ RP1 (O1-RP1) 一律内部丢弃:
                # raw chain-of-thought 是 provider-private 数据, 绝不进入用户可见 SSE（thought_stream
                # 不再承载任何 raw 透传）; public Thinking 只能来自模型自己写的 <rationale>/
                # 公开工作笔记（thinking_summary）。不转发、不累积、不落盘（A1）、不摘要冒充。
                # （O5: 原 pending["reasoned"] 标志已删——只写不读, 无观察消费方。）
            elif node == "tools":
                # agent 输出结束 → flush（工作笔记/工具卡片穿插节奏; O1: 笔记已在宣告前归位）
                async for ev in flush_agent():
                    yield ev
                pending = {"text": "", "has_tools": False,
                           "note_emitted": False}
                extra = chunk.additional_kwargs or {}
                name = chunk.name or ""
                args = extra.get("_args", {})
                result = extra.get("_result_full", {})
                reused = extra.get("_reused", False)
                # O1: 引擎 auto-websearch 已删除——search_books 空结果后是否上网补充
                # 由 Main Agent 下一轮自主宣告（websearch 对模型可用且不受隐性配额挤压）,
                # runtime 不再代执行认知性工具（T7 断言依据）。
                # O3: 准入拒绝已不存在——reused 为唯一非执行路径（机械精确判重复用）。
                _thought = ("EXACT_DUPLICATE_REUSED（同工具+完全相同参数, 机械判重复用此前结果）" if reused
                            else f"执行 {name}")
                tool_log.append({"name": name, "args": args,
                                 "result_summary": str(result)[:200], "result_full": result,
                                 "thought": _thought})
                # O1 provenance: 工具执行结果——决定（宣告）来自 Main Agent;
                # 执行/复用属机械层, 不改变发起者归属。
                yield {"type": "tool", "name": name, "args": args,
                       "result": str(result)[:300], "thought": _thought,
                       "initiated_by": "main_agent",
                       "decision_group_id": extra.get("_dg") or _dg(),
                       "tool_call_id": getattr(chunk, "tool_call_id", None)}
                # Thinking UI: 工具结果解读（ACTIVITY 注记, runtime_mechanical; 不确定时静默）。
                try:
                    if reused:
                        yield {"type": "tool_note",
                               "content": "（EXACT_DUPLICATE_REUSED）同一工具与完全相同的参数此前已执行——直接复用此前结果（机械判重, 不涉及证据充分性判断）。",
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
                # O4-RP1: 术语核验状态计算块已删除——"这个词是否逐字出现"的判定
                # 由 Main Agent 自己读取原文后给出, runtime 不再先行核验再注入措辞约束。
        # ── O6-RP1 (F2): 工具宣告生命周期终态闭合 ──────────────────────
        # invocation 正常结束时, 任何仍处"已宣告未执行"的工具就地到达终态
        # （机械取消, 逐 id 绑定 tool_call_id）, pending 工具状态确定性清除。
        # 悬挂宣告的典型来源: 硬上限 forced 轮 forced_tools_done 已置位后模型仍
        # 宣告工具（should_continue → end, 不再进 tools 节点）——旧实现把
        # has_tools=True 留到收口区, 下一轮 repair 的 Main Agent 新文本会被当
        # 残留丢弃（O6-RP1 F2 根因: pending 状态泄漏进下一次 invocation）。
        if pending["has_tools"] or pending_tools:
            async for ev in flush_agent():
                yield ev
            for nm, tcid in sorted(pending_tools, key=lambda t: (t[0], str(t[1]))):
                yield {"type": "tool_cancel", "name": nm, "tool_call_id": tcid,
                       "reason": "工具预算已达上限，该调用未执行",
                       "initiated_by": "runtime_mechanical",
                       "decision_group_id": _dg()}
            pending = {"text": "", "has_tools": False, "started": set(),
                       "note_emitted": False}
            pending_tools.clear()

    try:
        async for _ev in _stream_graph(messages):
            yield _ev
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
        # ══ Phase A (A4) + O2 §8: graceful 恢复 = 同一个 Main Agent 原样重试一次 ══
        # 原"用 RECOVERY_SYSTEM_DIRECTIVE 调 AG.llm_chat 独立生成答案"是第二 writer——
        # 已删除。transport 异常后: 无候选正文 → 图重跑一次（evidence 全保留, 工具不重烧）;
        # 已有部分正文 → 保留, 走正常校验/收口; 重试仍无 → 如实 error。
        _recovered = False
        if not _strip_markers(pending["text"]):
            try:
                logger.info("[graceful-completion] stream error → retrying main agent once")
                async for _ev in _stream_graph(messages):
                    yield _ev
                _recovered = True
            except Exception as _re:
                logger.warning(f"[graceful-completion] retry failed: {str(_re)[:200]}")
        if not _recovered and not _strip_markers(pending["text"]):
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
        # ══ O2 §9/§10: Final Candidate → Deterministic Validator → same-agent repair loop ══
        # 图流结束 → 尾部残留释放 → 候选组装 → 确定性校验; FAIL → 结构化 issues 以中性反馈
        # 打回同一个 Main Agent（repair invocation 绑定完整工具集, 可继续研究——仍遵守
        # O1 causal contract）; 机械上限 MAX_VALIDATION_REPAIRS 次, 绝不无限循环。
        _ptail = _phrase_scr.flush()
        _tail = _visible_text(_rat_parser.finish())   # 未闭合 rationale 残留剥离标签后释放
        _tails = _ptail + _tail
        if _tails:
            pending["text"] = _tails + pending["text"]
        # 预算强制收尾的残留工具轮: 文本降级为工作笔记, 不进入候选
        if pending["has_tools"]:
            async for ev in flush_agent():
                yield ev
            pending["text"] = ""
        # 被截断的已宣告工具调用（宣告了 tool_start 但最终未执行, 如 hard 预算强制轮的
        # 二次残留宣告）: 逐 id 发 tool_cancel, 前端据此解除对应"调用中"卡片（2026-08-14）。
        # O6-RP1 (F2/F3): 正常路径下悬挂宣告已在 _stream_graph 的 invocation 终态闭合中
        # 清除（此处为防御性兜底, 仅在异常中断后仍残留时触发）; 事件逐 tool_call_id 绑定。
        for nm, tcid in sorted(pending_tools, key=lambda t: (t[0], str(t[1]))):
            yield {"type": "tool_cancel", "name": nm, "tool_call_id": tcid,
                   "reason": "工具预算已达上限，该调用未执行",
                   "initiated_by": "runtime_mechanical",
                   "decision_group_id": _dg()}

        candidate = pending["text"]
        pending["text"] = ""
        repairs_used = 0
        _val_history = []      # O7-E RP1 §5: 纯机械 validation history（无 CoT/正文）
        while True:
            validation = validate_final_candidate(
                candidate, raw_tool_log=raw_tool_log, fallback_log=tool_log,
                language=language)
            _val_history.append({
                "attempt_index": len(_val_history), "ok": bool(validation.ok),
                "issue_codes": [i.get("code") for i in validation.as_dict().get("issues", [])],
                "candidate_chars": len(candidate or ""),
                "candidate_sha256": hashlib.sha256(
                    (candidate or "").encode("utf-8")).hexdigest() if (candidate or "").strip() else None})
            if validation.ok or repairs_used >= MAX_VALIDATION_REPAIRS:
                break
            repairs_used += 1
            logger.info(f"[o2-validator] candidate FAIL ({len(validation.issues)} issues) → "
                        f"main-agent repair {repairs_used}/{MAX_VALIDATION_REPAIRS}")
            yield {"type": "tool_note",
                   "content": "（答案证据校验未通过——正在把结构化问题反馈给智能体重新整理回答……）",
                   "initiated_by": "validator", "activity": True,
                   "decision_group_id": _dg()}
            # O2 §9: 中性反馈——只列机械 issue, 不命令具体修复动作（改写/标注/删引文/
            # 补研究由 Agent 自主决定）; validator 自身绝不调用工具。
            _fb = format_feedback(validation)
            # O7-E RP1 §8: repair transport contract——完整替换候选 + 资源上限下基于
            # 已有证据修订 + 禁止空候选（传输合同, 非学术内容指令; validator 文件零改动）
            _fb = _fb.replace(
                "Revise the candidate or gather more evidence as appropriate.",
                "This is a validation repair of the same answer. Produce a complete "
                "replacement final candidate. The validator issues above are "
                "mechanical evidence problems. You may gather additional evidence "
                "only if tool resources remain available. If the tool resource "
                "ceiling has been reached, revise using the evidence already "
                "obtained. Do not return an empty candidate.")
            # §7: hard 预算已成立 → 机械资源事实并入反馈消息（不新增 SystemMessage
            # 注入点, 维持「builder 1 + hard 预算 1」注入不变量）; repair 零工具模式
            _no_tools = bool(budget is not None and budget.hard_reached())
            if _no_tools:
                _fb += ("\n\nNO_MORE_TOOL_EXECUTION_AVAILABLE（机械资源事实）: 工具执行"
                        "硬上限已达。本轮修复不可执行任何工具——直接基于已获得的证据"
                        "写出完整替换最终候选; 禁止宣告新工具, 禁止空候选。")
            _repair_msgs = list(messages) + [AIMessage(content=candidate),
                                             HumanMessage(content=_fb)]
            try:
                async for _ev in _stream_graph(_repair_msgs, no_tools=_no_tools):
                    yield _ev
            except Exception as _re:
                logger.warning(f"[o2-repair] stream failed: {str(_re)[:200]}")
                break
            # repair 轮的尾部残留 / 残留工具轮处理（与首次运行同规则）
            _ptail2 = _phrase_scr.flush()
            _tail2 = _visible_text(_rat_parser.finish())
            if pending["has_tools"]:
                async for ev in flush_agent():
                    yield ev
                pending["text"] = ""
            candidate = (_ptail2 + _tail2) + pending["text"]
            pending["text"] = ""
        # 发布（§11: BUFFER FINAL UNTIL VALIDATED）: 只有 validator PASS 的候选才允许
        # 公开。O2-RP1 (P0): repair 耗尽后绝不允许发布无效候选（含 ok=false 透传发布）——
        # validator 有权拒绝答案, 但 runtime 不会因此获得"替你把错误答案发出去"的权力。
        # 耗尽路径以非语义 failure/status 事件干净收口; done.validation 携带全部 issues。
        if candidate.strip() and validation.ok:
            full_answer = candidate
            for ch in candidate:
                yield {"type": "token", "content": ch}
                await asyncio.sleep(TOKEN_INTERVAL)
        else:
            yield {"type": "validation_failed",
                   "content": "回答未通过确定性证据校验",
                   "issues": validation.as_dict()["issues"],
                   "repairs_used": repairs_used,
                   "initiated_by": "validator",
                   "decision_group_id": _dg()}
            yield {"type": "error",
                   "content": "本轮回答未通过证据一致性校验，请重试或换一种问法" if language != "en"
                   else "This response failed deterministic evidence validation—please retry or rephrase"}
        pending = {"text": "", "has_tools": False, "note_emitted": False}
        # ══ O1: 引擎兜底读取的回放与终局安全网已删除 ══
        # 原此处的 ① auto-read tool 事件回放 + "已完成主文本核验读取" 注记
        # 和 ② 收口前 _ensure_primary_read 终局补读（含"原典核验补正"正文补发）
        # 均为 runtime 代执行认知工具 / runtime 文本冒充 Agent 核验行为——按 O1 契约删除。
        # 主文本读取现在只能来自 Main Agent 宣告; 核验不足时模型会在收口轮收到
        # "最后核验机会"读章提示（prompt 层）, 由模型自己决定是否补读。
        # ══ O2 §7: 以下 runtime 代写通道已整体删除 ══
        # ① 原典核验补发（verified quote visibility append）——runtime 不得替 Agent 写正文
        #    （含核验声明）; 核验状态经 done.evidence.facts / done.quote_bound 审计输出。
        # ② postloop drain（净化链残留释放）——净化链已不存在。
        # ③ scan_final_consistency 尾补——G（确定性降调）属语义 hedge, 按 §7 删除不转 validator;
        #    H（verify-later 矛盾）曾转为 ValidationIssue, O4-RP1 随 task-intent discipline
        #    一并移除（evidence-consistency 类检查如后续需要再立项）。
        # ══ Phase T.1: Quote Bound 审计（纯检测, 供 done payload; 不产生任何文本）══
        _quote_audit = None
        _vt0 = time.time()
        try:
            _quote_audit = QB.audit_quotes(full_answer, raw_tool_log)
        except Exception as _e:
            logger.warning(f"[quote-bound post] skipped: {str(_e)[:160]}")
        finally:
            if trace:
                trace.record_phase("validator_quote_bound", _vt0)
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
            # O4-RP1: 来源约束参数已删——契约只描述 检索候选 ↔ 回答使用的确定性关系,
            # 不再按用户意图分类排除二手证据。
            evidence_payload = build_evidence_contract(tool_log, full_answer, agent, language)
            citations = evidence_payload["citations"]
        except Exception as _e:
            logger.warning(f"[evidence-contract] skipped: {str(_e)[:200]}")
            citations = []
        finally:
            if trace:
                trace.record_phase("validator_evidence_contract", _vt0)
        # ══ Patch 1 (B4-B) → O2: Citation Sanitizer——最终输出硬约束的断言层 ══
        # O2 后未核验 formal citation 不再被流式降级——候选带着原样标记进入 validator,
        # 以 UNVERIFIED_CITATION 打回 same-agent repair; 此处 sanitize_citations 仅作
        # final-output assertion——发布文本若仍有未核验引用即为 ceiling 收口的失败披露,
        # 记日志; 不改写、不追加任何文本。
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
        # O4: semantic_obligations（derive/assess obligations）已删除——
        # "同一义务只履行一次"的语义义务台账属 Shadow cognition; done.obligations 字段随之移除。
        # 工具失败统计须在 result_full 剥离前取值（2026-08-30: 旧代码在弹掉后才计数, 恒为 0）
        _fail = sum(1 for tc in tool_log if isinstance(tc.get("result_full"), dict) and tc["result_full"].get("error"))
        # O4: tool_ownership_audit（tool_value/final_use 审计）已随 tool_contracts 瘦身删除——
        # "专用工具是否被绕过/冗余"的语义审计不改变任何行为, done.tool_ownership 字段随之移除。
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
        # ══ 时期人格状态（Persona/Context layer, agents 层; 审计/回归断言用）══
        _temporal_state = None
        try:
            if agent != "general":
                _temporal = AGENTS.detect_temporal(req_message)
                if _temporal.get("detected"):
                    _names = [t.get("name") for t in tool_log]
                    _period_used = {y: AGENTS.year_to_period(agent, y)
                                    for y in (_temporal.get("years") or [])}
                    _corpus_periods = []
                    for tc in raw_tool_log:
                        rf = tc.get("result_full") or {}
                        for e in (rf.get("echoes") or []):
                            if isinstance(e, dict) and e.get("period") and e["period"] not in _corpus_periods:
                                _corpus_periods.append(str(e["period"]))
                    _temporal_state = {
                        "detected": True,
                        "years": _temporal.get("years") or [],
                        "words": _temporal.get("words") or [],
                        "periods_mapped": {str(y): p for y, p in _period_used.items() if p},
                        "period_tool_called": "philosopher_period" in _names,
                        "corpus_periods": _corpus_periods,
                    }
        except Exception as _e:
            logger.warning(f"[temporal-state] skipped: {str(_e)[:120]}")
        if evidence_payload is not None:
            # O5 (MERGE): 执行事实并入 Evidence Store——done.evidence.facts 承载
            # EvidenceState snapshot（前端只读 evidence.retrieved_count, 加键安全;
            # done.obligation_ledger 字段已删除）。
            evidence_payload["facts"] = evidence_state.snapshot()
        yield {"type": "done", "citations": citations, "evidence": evidence_payload,
               "tool_calls": tool_log,
               "suggestions": suggestions, "safety": safety_flag,
               # O4 删除的 done 字段: composition / epistemic / obligations / budget（扫描）/
               # retrieval_state / tool_ownership——Shadow cognition 审计块随生产代码一并移除。
               # O5 删除: obligation_ledger（并入 evidence.facts）/ 引用降级静态审计 dict
               # （前端零消费; validator 审计见 validation/citation_sanitize）。
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
               # O2: Final Answer Ownership 审计块——
               # 最终可见正文的自然语言只能由 Main Agent 生成（validator FAIL 时经
               # same-agent repair 重新生成; runtime 零改写/零追加/零语义 retract）。
               "final_ownership": {"provenance": "o2",
                                   "final_text_owner": "main_agent",
                                   "semantic_mutators": 0,
                                   "runtime_factual_appends": 0,
                                   "final_retract_semantic_use": 0,
                                   "invalid_final_publicly_streamed": False,
                                   "validator_repair_invocations": repairs_used,
                                   "main_agent_final_ownership_rate": 1.0},
               # O2: 确定性校验结果（final candidate 发布前的唯一守门人）
               "validation": {"result": validation.as_dict(),
                              "repairs_used": repairs_used,
                              "history": _val_history,
                              "max_validation_repairs": MAX_VALIDATION_REPAIRS,
                              "repair_protocol": "same_main_agent"},
               # O1 (§13): 机械 timing observability（llm_invocation / validator_* 阶段时长;
               # 工具级时长见 trace.calls 与 tool 事件, 此处为阶段汇总）
               "timing": {"phases": (list(trace.phases) if trace else []),
                          "total_ms": round((time.time() - _t_start) * 1000, 1)},
               "citation_sanitize": ({k: _citation_sanitize.get(k) for k in
                                      ("verified_citations", "unverified_before", "actions")}
                                     if _citation_sanitize else None),
               # O4-RP1 删除的 done 字段: plan（verification_intent 意图分类审计块）/
               # verification（术语核验状态）——Python 对用户问题的认知解释不再存在。
               # O5: 执行事实见 done.evidence.facts（obligation_ledger 字段已并入删除）。
               # Phase T.1: Quote Bound 审计（引文核验状态 / 拼接检测 / 未核验 blockquote 计数）
               "quote_bound": (_quote_audit or {}),
               "temporal": _temporal_state,
               # O2: LiveCitationSanitizer 已删除——正式引用不再被 runtime 降级改写,
               # 未核验引用走 validator UNVERIFIED_CITATION → same-agent repair
               # （O5: done 的引用降级静态审计 dict 已删, 前端零消费）。
               # O2 §13: safety 属安全执行层（safety_runtime）, 不计入普通 semantic mutator
               "safety_enforcement": {"initiated_by": "safety_runtime",
                                      "action": "blocked" if safety_flag == "blocked"
                                      else ("warning" if safety_flag == "warning" else "none")},
               "safety_reply": (SAFETY_REPLY_EN if language == "en" else SAFETY_REPLY) if safety_flag == "blocked" else None}
        # RP1 (O1-RP1): 事后推理摘要通道整体删除——
        #   旧 _post_reasoning_summary（mini-LLM 浓缩 raw reasoning_text）= runtime 摘录
        #   provider 私有 CoT 后冒充 Agent 思考（被禁的 _gen_summary 变体）;
        #   确定性 build_reasoning_summary 兜底 = Python 编造伪思考。两者都不再出现在
        #   生产用户流。public Thinking 唯一事实来源 = thinking_summary(_delta)
        #   （模型自己写的 <rationale> / 公开工作笔记）。
        #   话题建议（suggestions）非思考内容, 保留。
        async def _post_llm_suggest():
            try:
                return await asyncio.to_thread(_llm_suggest, req_message, full_answer, agent, language)
            except Exception:
                return None
        llm_suggestions = await _post_llm_suggest()
        if llm_suggestions:
            yield {"type": "suggestions", "suggestions": llm_suggestions}
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
