"""哲学智能体核心: 可插拔工具集 + DeepSeek 编排（function calling）
核心开放点: TOOLS 注册表——新增能力 = 注册一个新工具（一行注册 + execute 函数）
V1 工具: search_books / get_book_detail / get_chapter / query_graph / get_philosopher / list_books
"""
import json, os, re, time, urllib.request, threading
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# ── 路径 ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent          # backend/
DATA = BASE / "data"
PUBLIC = BASE.parent / "app" / "public"                 # app/public
BOOKS_FILE = PUBLIC / "books.json"
CHAPTERS_DIR = DATA / "book_chapters"
NETWORK_FILE = PUBLIC / "philosopher_network.json"
PHILOSOPHERS_FILE = PUBLIC / "philosophers.json"

# ── LLM 客户端（DeepSeek, 云端）───────────────────────
def _load_env():
    env_path = BASE.parent / ".env"
    if env_path.exists():
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = os.environ.get("DP_API_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")

def llm_chat(messages, tools=None, temperature=0.7, max_tokens=2000):
    """DeepSeek chat 调用（支持 function calling）"""
    body = {"model": MODEL, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if tools:
        body["tools"] = tools
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{API_URL}/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {API_KEY}"})
    for attempt, wait in enumerate([5, 10, 15]):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "ignore")[:500]
            if attempt == 2:
                raise Exception(f"HTTP {e.code}: {err_body}")
            time.sleep(wait)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(wait)

# ── 数据加载（带缓存）────────────────────────────────
_books_cache = None
_network_cache = None
_philosophers_cache = None
_cache_lock = threading.Lock()

def get_books():
    global _books_cache
    if _books_cache is None:
        with _cache_lock:
            if _books_cache is None:
                _books_cache = json.load(open(BOOKS_FILE, encoding="utf-8"))
    return _books_cache

def get_network():
    global _network_cache
    if _network_cache is None:
        with _cache_lock:
            if _network_cache is None and NETWORK_FILE.exists():
                _network_cache = json.load(open(NETWORK_FILE, encoding="utf-8"))
    return _network_cache or {}

def get_philosophers():
    global _philosophers_cache
    if _philosophers_cache is None:
        with _cache_lock:
            if _philosophers_cache is None:
                _philosophers_cache = json.load(open(PHILOSOPHERS_FILE, encoding="utf-8"))
    return _philosophers_cache

def book_by_id(bid):
    for b in get_books():
        if b.get("id") == bid:
            return b
    return None

def chapter_meta(bid):
    mp = CHAPTERS_DIR / bid / "meta.json"
    if mp.exists():
        return json.load(open(mp, encoding="utf-8"))
    return None

def read_chapter(bid, idx):
    cp = CHAPTERS_DIR / bid / f"{idx}.json"
    if cp.exists():
        ch = json.load(open(cp, encoding="utf-8"))
        texts = [b.get("value", "") for b in ch.get("content", []) if b.get("type") == "text"]
        return {"title": ch.get("title", ""), "text": "\n".join(texts), "blocks": ch.get("content", [])}
    return None

# ═══════════════════════════════════════════════════════
# 工具注册表（核心开放点: register_tool 一行接入新能力）
# ═══════════════════════════════════════════════════════
TOOLS = {}  # name -> {"description", "parameters", "execute"}

def register_tool(name, description, parameters, execute):
    TOOLS[name] = {"description": description, "parameters": parameters, "execute": execute}

# ── 工具 1: search_books（书级过滤 + 章级关键词扫描）──
def _match_score(text, terms):
    """简单关键词评分: 命中数 + 位置权重"""
    score = 0
    low = text.lower()
    for t in terms:
        c = low.count(t)
        score += c * 2 if c else 0
    return score

def _exec_search_books(args):
    query = args.get("query", "")
    limit = min(int(args.get("limit", 5)), 10)
    terms = [t for t in re.split(r"[\s,，。；;：:、]+", query) if len(t) >= 2]
    if not terms:
        return {"error": "查询词过短"}
    # 1) 书级过滤（书名/作者/简介命中）
    books = get_books()
    hits = []
    for b in books:
        hay = f"{b.get('title','')} {b.get('author','')} {b.get('summary','')}"
        s = _match_score(hay, terms)
        if s > 0:
            hits.append((s, b))
    hits.sort(key=lambda x: -x[0])
    # 2) 章级扫描（前 limit 本书的章节）
    results = []
    for s, b in hits[:limit]:
        meta = chapter_meta(b["id"])
        if not meta or not meta.get("chapterCount"):
            continue
        best = []
        for i in range(min(meta["chapterCount"], 300)):
            ch = read_chapter(b["id"], i)
            if not ch or not ch.get("text"):
                continue
            cs = _match_score(ch["text"][:2000] + ch.get("title", ""), terms)
            if cs > 0:
                best.append((cs, i, ch))
        best.sort(key=lambda x: -x[0])
        for cs, i, ch in best[:3]:
            text = ch["text"]
            # 提取命中片段
            pos = 0
            low = text.lower()
            for t in terms:
                p = low.find(t)
                if p >= 0:
                    pos = p
                    break
            snippet = text[max(0, pos - 80): pos + 180].replace("\n", " ")
            results.append({
                "book_id": b["id"], "book_title": b.get("title"), "author": b.get("author"),
                "chapter_idx": i, "chapter_title": ch.get("title", ""),
                "snippet": snippet, "score": s + cs,
            })
    results.sort(key=lambda x: -x["score"])
    return {"results": results[:limit * 3], "query": query}

register_tool(
    "search_books",
    "在 403 本哲学原著中全文检索（书名/作者/章节内容关键词命中）。用于回答哲学问题时找原文依据、引言、概念出处。",
    {"type": "object", "properties": {"query": {"type": "string", "description": "检索关键词（哲学概念/人名/书名/句子片段）"}, "limit": {"type": "integer", "description": "返回结果数上限"}}, "required": ["query"]},
    _exec_search_books,
)

# ── 工具 2: get_book_detail ──────────────────────────
def _exec_book_detail(args):
    bid = args.get("book_id", "")
    b = book_by_id(bid)
    if not b:
        return {"error": f"未找到书籍 {bid}"}
    meta = chapter_meta(bid)
    return {"id": b.get("id"), "title": b.get("title"), "author": b.get("author"),
            "region": b.get("region"), "file_type": b.get("file_type"),
            "summary": b.get("summary", "")[:500], "rank": b.get("rank"),
            "chapterCount": meta.get("chapterCount", 0) if meta else 0,
            "toc": (meta.get("toc") or [])[:30]}

register_tool(
    "get_book_detail",
    "获取一本书的详情（简介/作者/目录/章节数）。",
    {"type": "object", "properties": {"book_id": {"type": "string"}}, "required": ["book_id"]},
    _exec_book_detail,
)

# ── 工具 3: get_chapter ──────────────────────────────
def _exec_chapter(args):
    bid = args.get("book_id", "")
    idx = int(args.get("chapter_idx", 0))
    ch = read_chapter(bid, idx)
    if not ch:
        return {"error": f"章节不存在 {bid}/{idx}"}
    return {"book_id": bid, "chapter_idx": idx, "title": ch["title"],
            "text": ch["text"][:6000]}

register_tool(
    "get_chapter",
    "读取某本书指定章节的全文（用于深入引用原文、分析论证）。",
    {"type": "object", "properties": {"book_id": {"type": "string"}, "chapter_idx": {"type": "integer"}}, "required": ["book_id", "chapter_idx"]},
    _exec_chapter,
)

# ── 工具 4: query_graph（哲学家星丛/师承/论敌/影响）──
def _exec_graph(args):
    name = args.get("philosopher", "").strip()
    net = get_network()
    # 图谱格式: {哲学家名: {rank, region, connections: [{name, type, note}]}}
    target_key = None
    for k in net:
        if name in k or k in name:
            target_key = k
            break
    if not target_key:
        return {"error": f"图谱中未找到哲学家: {name}", "hint": "可尝试: 尼采/康德/海德格尔/柏拉图"}
    node = net[target_key]
    relations = []
    for c in node.get("connections", []):
        relations.append({"relation": c.get("type", "关联"), "other": c.get("name"),
                          "note": c.get("note", "")})
    return {"philosopher": target_key, "region": node.get("region", ""),
            "rank": node.get("rank"), "relations": relations[:30]}

register_tool(
    "query_graph",
    "查询哲学家星丛图谱关系（师承/论敌/影响/思想关联）。用于回答'谁影响了谁'、'思想传承脉络'、'对立观点'类问题。",
    {"type": "object", "properties": {"philosopher": {"type": "string", "description": "哲学家姓名（如: 尼采/康德/海德格尔）"}}, "required": ["philosopher"]},
    _exec_graph,
)

# ── 工具 5: get_philosopher（生平/流派/时期）─────────
def _exec_philosopher(args):
    name = args.get("name", "").strip()
    phils = get_philosophers()
    entries = phils if isinstance(phils, list) else list(phils.values())
    for p in entries:
        pn = p.get("name", "") if isinstance(p, dict) else ""
        if name in pn or pn in name:
            return {"name": pn, "period": p.get("period", ""), "century": p.get("century", ""),
                    "school": p.get("school", ""), "region": p.get("region", ""),
                    "works": (p.get("works") or [])[:8], "bio": (p.get("bio") or "")[:500]}
    return {"error": f"未找到哲学家: {name}"}

register_tool(
    "get_philosopher",
    "获取哲学家生平资料（时期/流派/代表作/简介）。",
    {"type": "object", "properties": {"name": {"type": "string"}}, "required": ["name"]},
    _exec_philosopher,
)

# ── 工具 6: list_books（书单筛选）────────────────────
def _exec_list_books(args):
    author = args.get("author", "")
    region = args.get("region", "")
    school = args.get("school", "")
    out = []
    for b in get_books():
        if author and author not in b.get("author", ""):
            continue
        if region and region not in b.get("region", ""):
            continue
        if school and school not in json.dumps(b.get("tags", []), ensure_ascii=False):
            continue
        out.append({"id": b.get("id"), "title": b.get("title"), "author": b.get("author"),
                    "region": b.get("region"), "rank": b.get("rank"),
                    "summary": (b.get("summary") or "")[:150]})
    out.sort(key=lambda x: -(x.get("rank") or 0))
    return {"books": out[:20], "total": len(out)}

register_tool(
    "list_books",
    "按作者/地区/流派筛选书籍列表（用于推荐阅读、书目检索）。",
    {"type": "object", "properties": {"author": {"type": "string"}, "region": {"type": "string"}, "school": {"type": "string"}}, "required": []},
    _exec_list_books,
)

# ═══════════════════════════════════════════════════════
# 编排: /api/agent/chat
# ═══════════════════════════════════════════════════════
SYSTEM_PROMPT = """你是"深哲"——一个哲学智能体，基于 403 本哲学原著（柏拉图到德里达）回答问题。

铁律:
1. 凡涉及具体哲学主张/概念/出处，必须先调用工具检索原文（search_books / get_chapter），用真实原文支撑，不得凭记忆编造引文。
2. 回答标注引用来源: 【《书名》· 章节名】。
3. 涉及哲学家关系（师承/影响/论敌）时调用 query_graph。
4. 回答使用中文，严谨、清晰、有层次。可适度苏格拉底式反问，但不回避问题。
5. 若检索无结果，如实说明"库中未检索到"，不硬答。
6. 引用原文时用引号，并说明是原典原文还是概括。"""

class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    book_id: Optional[str] = None  # 阅读语境（来自阅读器的提问）

class AgentChatResponse(BaseModel):
    reply: str
    citations: List[dict] = []
    tool_calls: List[dict] = []

@router.post("/api/agent/chat")
async def agent_chat(req: AgentChatRequest):
    if not API_KEY:
        return AgentChatResponse(reply="服务端未配置 DEEPSEEK_API_KEY", citations=[], tool_calls=[])
    # 组装消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in req.history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    if req.book_id:
        b = book_by_id(req.book_id)
        if b:
            messages.append({"role": "system", "content": f"用户正在阅读《{b.get('title')}》（{b.get('author')}），回答可优先结合此书。"})
    messages.append({"role": "user", "content": req.message})

    # 工具 schema
    tools = []
    for name, t in TOOLS.items():
        tools.append({"type": "function", "function": {
            "name": name, "description": t["description"], "parameters": t["parameters"]}})

    tool_calls_log = []
    try:
        resp = llm_chat(messages, tools=tools)
        msg = resp["choices"][0]["message"]
        # 工具调用循环（最多 4 轮）
        for _ in range(4):
            if not msg.get("tool_calls"):
                break
            messages.append(msg)  # ⚠️ assistant(tool_calls) 必须先入 messages, tool 消息才能跟随
            for tc in msg["tool_calls"]:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except Exception:
                    args = {}
                tool = TOOLS.get(name)
                if not tool:
                    result = {"error": f"未知工具 {name}"}
                else:
                    try:
                        result = tool["execute"](args)
                    except Exception as e:
                        result = {"error": str(e)}
                tool_calls_log.append({"name": name, "args": args, "result_summary": str(result)[:200]})
                messages.append({"role": "tool", "tool_call_id": tc.get("id", f"call_{len(tool_calls_log)}"),
                                 "content": json.dumps(result, ensure_ascii=False)[:4000]})
            resp = llm_chat(messages, tools=tools)
            msg = resp["choices"][0]["message"]
        # 循环截断后若仍有 tool_calls → 强制无工具总结（不 append 截断消息, 避免 tool 消息缺失 400）
        if msg.get("tool_calls"):
            resp = llm_chat(messages)
            msg = resp["choices"][0]["message"]
        reply = msg.get("content") or "（无回答）"
        # 提取引用
        citations = []
        for tc in tool_calls_log:
            if tc["name"] == "search_books":
                try:
                    r = tc.get("result_summary")
                    if r and "book_title" in r:
                        for item in json.loads(r).get("results", [])[:3]:
                            citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                              "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
                except Exception:
                    pass
        return AgentChatResponse(reply=reply, citations=citations, tool_calls=tool_calls_log)
    except Exception as e:
        return AgentChatResponse(reply=f"智能体出错: {e}", citations=[], tool_calls=tool_calls_log)
