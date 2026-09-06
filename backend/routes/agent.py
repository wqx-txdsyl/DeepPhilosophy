# -*- coding: utf-8 -*-
"""哲学智能体核心（R2-2/S21 复审拆分后聚合层, 2026-08-18）

2026-08-18 复审 R2-2/S21: 按域拆分（只搬移不改逻辑, 本文件由 1987 行变薄为聚合层）:
  agent_core.py                共享基础设施: 路径/数据加载缓存/TOOLS 注册表/
                               per-user 记忆槽/S13 检索索引与文本 LRU/embedding 缓存
  agent_llm.py                 DeepSeek LLM 客户端（env 加载 + llm_chat）
  agent_tools_retrieval.py     检索工具域（10 个: search_books/get_chapter/query_graph/
                               get_school/concept_trace/websearch/query_database…）
  agent_tools_memory.py        记忆/创作工具域（5 个: write_essay/generate_image/
                               philosopher_debate/thought_experiment/role_play）
  agent_tools_eval.py          评估/分析工具域（15 个: compare_views/socratic_tutor/
                               advisor_council/conceptual_map/school_arena/agent_council…）
  agent_sse.py                 SSE 流式路由（/api/agent/stream_lg）

本文件职责: 聚合 import（工具模块 import 即注册到 TOOLS）→ 路由注册 →
边缘路由（/api/agents /api/cite /api/drawio）。
main.py 的 router 引用不变（from routes.agent import router）。
外部消费者保持兼容: engine_langgraph（AG.TOOLS/llm_chat/MODEL/API_KEY/API_URL/DATA）、
agents（TOOLS）、sync/knowledge（invalidate_agent_cache）、tests（_safe_bid/_int_arg/
_embed_query/_exec_search_books/_exec_query_db…）均经本模块 re-export。
（O5: SYSTEM_PROMPT / _SYS_TOOL_LIST 死常量已删除——引擎唯一主策略真源 =
engine_langgraph.SYSTEM_PROMPT_LG, 经 AGENTS.AGENT_PROMPTS / get_system_prompt 分发。）
"""
import re

from fastapi import APIRouter

# ── 聚合 import（顺序即加载顺序: env → 核心 → 工具域 → SSE）──
from routes.agent_llm import llm_chat, API_KEY, API_URL, MODEL, _load_env
from routes.agent_core import (
    TOOLS, register_tool,
    get_books, get_network, get_philosophers, book_by_id,
    _safe_bid, chapter_meta, read_chapter, invalidate_agent_cache,
    _int_arg, _embed_query, _embed_status,
    _mem_slot, _save_agent_memory, _find_essay_topic,
    BASE, DATA, PUBLIC, BOOKS_FILE, CHAPTERS_DIR, NETWORK_FILE, PHILOSOPHERS_FILE,
    SCHOOLS_DIR, PHILOSOPHER_DIR, AGNES_IMG_DIR, AI_DIR,
)
# 工具域模块（import 即注册到 TOOLS; 下划线符号仅测试/内部使用, 显式 re-export）
from routes.agent_tools_retrieval import _exec_search_books, _exec_query_db
import routes.agent_tools_retrieval  # noqa: F401  注册检索域工具
import routes.agent_tools_scholarly  # noqa: F401  注册 O7-C 二手文献检索域（2 工具）
import routes.agent_tools_memory     # noqa: F401  注册记忆/创作域工具
import routes.agent_tools_eval       # noqa: F401  注册评估/分析域工具
from routes.agent_sse import router as _sse_router, AgentChatRequest  # noqa: F401

# ═══════════════════════════════════════════════════════
# 路由注册（main.py: from routes.agent import router as agent_router）
# ═══════════════════════════════════════════════════════
router = APIRouter()
router.include_router(_sse_router)

# 保持 TOOLS 注册顺序与拆分前一致（拆分前按域分组注册会打乱顺序;
# 此处按原始注册序重建, 消费方依赖注册序稳定）
_TOOL_REGISTER_ORDER = [
    "search_books", "get_book_detail", "get_chapter", "query_graph", "get_philosopher",
    "list_books", "write_essay", "generate_image", "get_school", "phti_test",
    "compare_views", "socratic_tutor", "philosopher_debate", "thought_experiment",
    "advisor_council", "paper_review", "analyze_argument", "concept_trace", "profile",
    "conceptual_map", "websearch", "query_database", "role_play", "essay_outline",
    "life_coach", "dialectic", "history_timeline", "confrontation", "school_arena",
    "agent_council",
]
_TOOLS_BY_NAME = dict(TOOLS)
TOOLS.clear()
for _n in _TOOL_REGISTER_ORDER:
    if _n in _TOOLS_BY_NAME:
        TOOLS[_n] = _TOOLS_BY_NAME[_n]
for _n in _TOOLS_BY_NAME:      # 未来新增工具兜底（保持注册表完整, 追加在末尾）
    if _n not in TOOLS:
        TOOLS[_n] = _TOOLS_BY_NAME[_n]
del _TOOLS_BY_NAME, _TOOL_REGISTER_ORDER

# ═══════════════════════════════════════════════════════
# 编排: /api/agent/stream_lg（LangGraph 引擎, engine_langgraph.py; 旧 chat/stream 已删除 2026-08-14）
# 主策略提示词唯一真源 = engine_langgraph.SYSTEM_PROMPT_LG（O5: 本文件旧
# SYSTEM_PROMPT 死常量已删除——自研 ReAct 循环退役后即无任何消费者）。
# ═══════════════════════════════════════════════════════
# 智能体广场: 列出可用智能体（通用深哲 + 哲学家注册表）
# ═══════════════════════════════════════════════════════
@router.get("/api/agents")
async def list_agents():
    import agents as agents_mod
    out = [{"key": "general", "name": "深哲", "subtitle": "通用哲学智能体 · 全工具",
            "tagline": "检索/思辨/辩论/生图/写作/疏导", "portrait": None}]
    for key, spec in agents_mod.PHILO_AGENTS.items():
        out.append({"key": key, "name": spec.get("name", key),
                    "subtitle": spec.get("title", ""), "tagline": spec.get("tagline", ""),
                    "portrait": spec.get("portrait")})
    return {"agents": out}

# ═══════════════════════════════════════════════════════
# 出处跳转: 【《书名》·章节】→ 章节原文片段（前端渲染为可点击链接）
# ═══════════════════════════════════════════════════════
@router.get("/api/cite")
async def api_cite(book: str = "", chapter: str = ""):
    from routes.agent import get_books, chapter_meta, read_chapter
    from evidence_contract import _split_book_chapter

    # 《书·章》变体归一: 模型常写【《康德著作集·序言》】（·在《》内）, 不拆分则书名查不到
    book, chapter = _split_book_chapter(book, chapter)

    def _norm(s):
        # 书名归一化: 去《》/括号(全角转半角后剥除)/去空白/破折号变体归一 (AI 引用全半角不定;
        # 书名"从《理想国》到《正义论》"剥《》后无括号, 输入"(理想国)"带半角括号须同样剥除;
        # 语料章节"第108—275节"(全角破折号) 与书库 toc"第108-275节"(连字符) 须对齐, 否则永不命中)
        return ((s or "").replace("《", "").replace("》", "")
                .replace("（", "(").replace("）", ")").replace("(", "").replace(")", "")
                .replace("—", "-").replace("–", "-").replace("‐", "-").replace("－", "-")
                .replace(" ", "").strip())

    bname = _norm(book)
    if not bname:
        return {"error": "缺少书名"}
    hit = None
    for b in get_books():
        t = _norm(b.get("title"))
        if bname and (t == bname or (t and bname in t) or (len(t) >= 4 and t in bname)):
            # 反向包含需 t 足够长（防"理想国"误吞"从理想国到正义论"）
            hit = b
            break
    if not hit:
        return {"error": f"未找到《{bname}》"}
    meta = chapter_meta(hit["id"])
    if not meta:
        return {"error": "该书无章节数据"}
    toc = meta.get("toc") or []
    cname = _norm(chapter)   # 2026-08-30: 章节参数同样归一化（此前只 strip, 括号/破折号变体永不与 toc 对齐）
    idx = -1
    hit_title = ""
    matched = False   # 2026-08-14: 未匹配章节时不再静默跳第 0 章, 前端据此不渲染跳转
    base = cname.split("·")[0].strip() if cname else ""
    part_fb = -1  # part(编/卷)标题命中时的兜底: part 后第一个可索引章节
    for pos, t in enumerate(toc):
        if isinstance(t, dict) and t.get("type") == "part":
            title = t.get("title")
            t_norm = _norm(title)
            if title and cname and (cname in t_norm or t_norm in cname or (base and base in t_norm)) and part_fb < 0:
                for t2 in toc[pos + 1:]:
                    if not (isinstance(t2, dict) and t2.get("type") == "part"):
                        part_fb = t2.get("index", 0) if isinstance(t2, dict) else toc.index(t2)
                        break
            continue  # 编/卷分组标题不可索引（无块文件）
        title = t.get("title") if isinstance(t, dict) else t
        t_norm = _norm(title)
        # 2026-08-30: 目录标题同样归一化（书库 toc 存全角破折号"第108—275节",
        # 语料引用为"—"变体/半角混杂, 只归一化 cname 不归一化 title 则永不相等）
        # 节数区间: 格言体著作 toc 无逐节条目, 引用【·125】落在"第108-275节"块内即命中
        # （注意 toc 脏数据: 破折号有"-"/"—"/汉字"一"三种写法, 区间正则一并覆盖）
        m_rng = re.search(r"第\s*(\d{1,4})\s*[-—–‐－一]\s*(\d{1,4})\s*节", str(title) or "")
        if (not matched and m_rng and re.fullmatch(r"\d{1,4}", cname)
                and int(m_rng.group(1)) <= int(cname) <= int(m_rng.group(2))):
            idx = t.get("index", 0) if isinstance(t, dict) else toc.index(t)
            hit_title = title
            matched = True
            break
        if cname and (cname in t_norm or t_norm in cname or (base and base in t_norm)):
            # 层级 toc: 块 index 是条目自带 index（数组位置 ≠ 块序号, part 占位会错位）
            idx = t.get("index", 0) if isinstance(t, dict) else toc.index(t)
            hit_title = title
            matched = True
            break
    if idx < 0 and cname:
        # 2026-08-31: 合并块兜底——部分书 toc 粒度细于块文件（多目录条目共用一块）,
        # 证据章节名是块标题（如"第一部分 希腊哲学"）, toc 无同名条目 → 反查块标题定位
        try:
            from routes.agent_core import block_titles
            for n, bt in block_titles(hit["id"]).items():
                btn = _norm(bt)
                if btn and (btn in cname or cname in btn):
                    idx = n
                    hit_title = bt
                    matched = True
                    break
        except Exception:
            pass
    if idx < 0 and part_fb >= 0:
        idx = part_fb
        hit_title = f"{cname}（首章）"
        matched = True
    if idx < 0:
        idx = 0
        hit_title = toc[0].get("title") if isinstance(toc[0], dict) else toc[0]
    ch = read_chapter(hit["id"], idx)
    return {"book_id": hit["id"], "book": hit["title"], "author": hit.get("author", ""),
            "chapter": hit_title, "chapter_idx": idx, "matched": matched,
            "text": (ch.get("text") or "")[:2500] if ch else ""}

# ═══════════════════════════════════════════════════════
# draw.io 转换: mermaid → draw.io XML（前端在 draw.io 编辑器中继续编辑）
# ═══════════════════════════════════════════════════════
@router.post("/api/drawio")
async def api_drawio(req: dict):
    from drawio_convert import mermaid_to_drawio
    code = (req or {}).get("mermaid", "")
    if not code or not code.strip():
        return {"error": "缺少 mermaid 代码"}
    xml = mermaid_to_drawio(code)
    if not xml:
        return {"error": "无法转换为 draw.io 格式"}
    return {"xml": xml}
