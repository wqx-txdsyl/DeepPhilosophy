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

# ── 工具 7: write_essay（学生作文——注册为工具, 对话流意图触发）──
def _exec_write_essay(args):
    topic = args.get("topic") or args.get("query") or ""
    if not topic:
        return {"error": "缺少作文题目"}
    try:
        word_count = int(args.get("word_count", 800))
    except Exception:
        word_count = 800
    reply, citations, tcl = _essay_pipeline(topic, args.get("genre", "议论文"),
                                            word_count, args.get("extra", ""))
    return {"essay": reply, "citations": citations, "steps": tcl}

register_tool(
    "write_essay",
    "根据题目写一篇哲学作文（议论文/读后感等）。自动检索原典原文支撑论据, 带引用标注。用于学生作文场景。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "作文题目"},
        "genre": {"type": "string", "description": "文体: 议论文/读后感/论述"},
        "word_count": {"type": "integer", "description": "目标字数"},
        "extra": {"type": "string", "description": "附加要求"}},
     "required": ["topic"]},
    _exec_write_essay,
)

# ── 工具 8: generate_image（生图——Agnes 接入中, 占位）──
def _exec_generate_image(args):
    return {"status": "pending", "message": "Agnes 视觉 API 接入中（网络恢复后启用）"}

register_tool(
    "generate_image",
    "生成哲学概念图像（如洞穴比喻/永恒轮回的可视化图）。",
    {"type": "object", "properties": {"prompt": {"type": "string", "description": "图像描述"}}, "required": ["prompt"]},
    _exec_generate_image,
)

# ── 工具 9: get_school（哲学流派/谱系详情）──
SCHOOLS_DIR = PUBLIC / "schools" / "data"
def _exec_school(args):
    name = args.get("name", "").strip()
    if not SCHOOLS_DIR.exists():
        return {"error": "流派数据不存在"}
    files = os.listdir(SCHOOLS_DIR)
    hit = None
    for f in files:
        if f.endswith(".json"):
            try:
                d = json.load(open(SCHOOLS_DIR / f, encoding="utf-8"))
                if name in d.get("name", "") or d.get("name", "") in name:
                    hit = d
                    break
            except Exception:
                continue
    if not hit:
        return {"error": f"未找到流派: {name}", "hint": "可尝试: 存在主义/儒家/分析哲学/现象学/斯多葛"}
    return {"name": hit.get("name"), "region": hit.get("region", ""),
            "quote": hit.get("quote", ""), "quoteAuthor": hit.get("quoteAuthor", ""),
            "subtitle": hit.get("subtitle", ""), "overview": (hit.get("overview") or "")[:800],
            "thinkers": (hit.get("thinkers") or [])[:10],
            "timeline": (hit.get("timeline") or [])[:10]}

register_tool(
    "get_school",
    "查询哲学流派/学派详情（流派介绍/代表哲人/思想时间线）。用于回答'存在主义是什么''儒家思想'类问题。",
    {"type": "object", "properties": {"name": {"type": "string", "description": "流派名（如: 存在主义/儒家/分析哲学）"}}, "required": ["name"]},
    _exec_school,
)

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

# ═══════════════════════════════════════════════════════
# 编排: /api/agent/chat
# ═══════════════════════════════════════════════════════
SYSTEM_PROMPT = """你是"深哲"——一个哲学智能体，基于 403 本哲学原著（柏拉图到德里达）回答问题。

可用工具（需要时通过工具协议调用）:
- search_books: 全文检索（参数: query 关键词, limit 可选）——查概念/原文/出处
- get_book_detail: 查书详情（book_id）
- get_chapter: 读章节全文（book_id, chapter_idx）——深入引用原文
- query_graph: 哲学家星丛（philosopher 姓名）——师承/影响/论敌
- get_philosopher: 哲人生平（name）
- list_books: 书单筛选（author/region/school 可选）

工具协议: 需要工具时, 输出且只输出一行: {TOOL:{"name":"工具名","args":{...}}}
收到工具结果后继续思考, 可多次调用; 信息足够后输出最终回答。

铁律:
1. 凡涉及具体哲学主张/概念/出处，必须先调用 search_books / get_chapter 检索原文，用真实原文支撑，不得凭记忆编造引文。
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

# ═══════════════════════════════════════════════════════
# 作文工具: /api/agent/essay（面向学生——根据题目写哲学作文）
# ═══════════════════════════════════════════════════════
class EssayRequest(BaseModel):
    topic: str                      # 作文题目（如: 论自由 / 尼采超人学说评析）
    genre: str = "议论文"            # 议论文 / 读后感 / 论述
    word_count: int = 800            # 目标字数
    extra: str = ""                  # 附加要求（如: 结合现实生活举例）

ESSAY_PROMPT = """你是一位资深的哲学教师与写作导师，为学生撰写一篇高质量的{genre}。
题目: {topic}
目标字数: 约{word_count}字
附加要求: {extra}

写作要求:
1. 结构完整: 引言（引出题目、亮明中心论点）→ 主体（2-3 个分论点，每个分论点引用原典原文支撑）→ 结论（升华、呼应开头）。
2. 引用真实原典: 使用下方"原典检索结果"中的原文，引用标注【《书名》· 章节】，引用原文用引号——禁止编造引文。
3. 语言: 议论文风格，清晰有层次，适合学生借鉴学习；避免空洞口号。
4. 结尾可适度提出值得思考的问题，体现思辨深度。
5. 只输出作文正文（含标题），不要额外说明。

原典检索结果:
{retrieval}
"""

@router.post("/api/agent/essay")
async def agent_essay(req: EssayRequest):
    if not API_KEY:
        return AgentChatResponse(reply="服务端未配置 DEEPSEEK_API_KEY", citations=[], tool_calls=[])
    tool_calls_log = []
    try:
        # ① 检索题目相关原典（确定性）
        query = re.sub(r"[？?！!。，,、\s]+", " ", req.topic)[:50]
        result = TOOLS["search_books"]["execute"]({"query": query, "limit": 6})
        tool_calls_log.append({"name": "search_books", "args": {"query": query},
                               "result_summary": str(result)[:200], "result_full": result})
        retrieval = json.dumps(result, ensure_ascii=False)[:6000]
        prompt = ESSAY_PROMPT.format(genre=req.genre, topic=req.topic,
                                     word_count=req.word_count, extra=req.extra or "无",
                                     retrieval=retrieval)
        messages = [{"role": "user", "content": prompt}]
        resp = llm_chat(messages, temperature=0.75, max_tokens=min(req.word_count * 2 + 500, 4000))
        reply = (resp["choices"][0]["message"].get("content") or "").strip()
        if not reply:
            reply = "（生成失败，请重试）"
        # 引用
        citations = []
        for item in result.get("results", [])[:4]:
            citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                              "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
        for tc in tool_calls_log:
            tc.pop("result_full", None)
        return AgentChatResponse(reply=reply, citations=citations, tool_calls=tool_calls_log)
    except Exception as e:
        return AgentChatResponse(reply=f"作文生成失败: {e}", citations=[], tool_calls=tool_calls_log)

# ── 意图检测: 对话流中自然触发各工具（确定性规则, 不依赖 LLM 自律） ──
def detect_intent(msg):
    if any(w in msg for w in ["写作文", "写一篇", "写个", "作文", "读后感", "议论文", "论述文", "帮我写"]):
        return "essay"
    if any(w in msg for w in ["画一张", "画个", "生成图片", "生成图像", "画一下", "配图", "可视化一下", "画图", "画一幅"]):
        return "image"
    if any(w in msg for w in ["影响了", "师承", "论敌", "关系", "受谁", "继承", "思想渊源", "师从", "反对谁", "批判谁", "受谁影响", "影响谁"]):
        return "graph"
    if any(w in msg for w in ["是谁", "生平", "哪个流派", "代表作", "介绍下", "介绍一下", "资料", "哪个时期"]):
        return "philosopher"
    if re.search(r"\d\s*[A-E]", msg) and len(msg) < 60:
        return "phti_score"  # 测试答案格式（1A2B3C...）
    if any(w in msg for w in ["测试", "人格测试", "测一测", "哲学人格", "我是哪种哲学", "16型", "答题", "做个测试"]):
        return "phti"
    if any(w in msg for w in ["流派", "学派", "主义", "谱系", "思想传统", "思想脉络"]):
        return "school"
    return "chat"


def _essay_pipeline(topic, genre="议论文", word_count=800, extra=""):
    """作文生成（检索原典 + DeepSeek 撰写）——返回 (reply, citations, tool_calls_log)"""
    tool_calls_log = []
    query = re.sub(r"[？?！!。，,、\s]+", " ", topic)[:50]
    result = TOOLS["search_books"]["execute"]({"query": query, "limit": 6})
    tool_calls_log.append({"name": "search_books", "args": {"query": query},
                           "result_summary": str(result)[:200], "result_full": result,
                           "thought": f"作文需原典支撑, 检索「{query}」"})
    retrieval = json.dumps(result, ensure_ascii=False)[:6000]
    prompt = ESSAY_PROMPT.format(genre=genre, topic=topic, word_count=word_count,
                                 extra=extra or "无", retrieval=retrieval)
    messages = [{"role": "user", "content": prompt}]
    resp = llm_chat(messages, temperature=0.75, max_tokens=min(word_count * 2 + 500, 4000))
    reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（生成失败，请重试）"
    citations = [{"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")}
                 for item in result.get("results", [])[:4]]
    for tc in tool_calls_log:
        tc.pop("result_full", None)
    return reply, citations, tool_calls_log


@router.post("/api/agent/chat")
async def agent_chat(req: AgentChatRequest):
    if not API_KEY:
        return AgentChatResponse(reply="服务端未配置 DEEPSEEK_API_KEY", citations=[], tool_calls=[])
    # 意图分派: 作文/生图在对话流中自然触发（统一走注册工具）
    intent = detect_intent(req.message)
    if intent == "essay":
        result = TOOLS["write_essay"]["execute"]({"topic": req.message, "genre": "议论文", "word_count": 800})
        reply = result.get("essay") or "（作文生成失败）"
        tcl = result.get("steps") or []
        tcl.insert(0, {"name": "write_essay", "args": {"topic": req.message},
                       "result_summary": f"已生成作文 {len(reply)} 字", "thought": "识别到作文需求, 调用作文工具"})
        return AgentChatResponse(reply=reply, citations=result.get("citations", []), tool_calls=tcl)
    if intent == "image":
        result = TOOLS["generate_image"]["execute"]({"prompt": req.message[:80]})
        return AgentChatResponse(
            reply="生图工具正在接入（Agnes 视觉 API 网络恢复后启用）。当前可尝试: 作文、原典问答、哲学家关系查询。",
            citations=[], tool_calls=[{"name": "generate_image", "args": {"prompt": req.message[:80]},
                                       "result_summary": str(result)[:150], "thought": "识别到生图需求"}])
    if intent in ("graph", "philosopher"):
        # 图谱/哲人: 确定性调用 + 结果注入 → LLM 组织回答
        tool_name = "query_graph" if intent == "graph" else "get_philosopher"
        name_arg = req.message.replace("尼采", "尼采").strip()
        # 提取人名（常见哲人匹配, 子串双向: "海德格尔" 匹配 key "马丁·海德格尔"）
        import re as _re
        clean_name = _re.sub(r"(的生平|介绍一下|介绍下|是谁|的资料|的代表作|是哪个流派|的简介|的生平资料)", "", req.message).strip()
        if intent == "graph":
            cands = [k for k in get_network() if clean_name and (clean_name in k or k in clean_name)]
        else:
            phils = get_philosophers()
            cands = [k for k in phils if clean_name and (clean_name in k or k in clean_name)] if isinstance(phils, dict) else \
                    [p.get("name") for p in phils if isinstance(p, dict) and (clean_name in p.get("name", "") or p.get("name", "") in clean_name)]
        target = max(cands, key=len) if cands else None
        if not target:
            # 无匹配人名 → 走普通对话
            intent = "chat"
        else:
            args = {"philosopher": target} if intent == "graph" else {"name": target}
            result = TOOLS[tool_name]["execute"](args)
            tcl = [{"name": tool_name, "args": args, "result_summary": str(result)[:200],
                    "result_full": result, "thought": f"识别到{'关系' if intent=='graph' else '人物'}查询, 调用{tool_name}"}]
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": req.message},
                        {"role": "system", "content": f"工具「{tool_name}」返回: {json.dumps(result, ensure_ascii=False)[:4000]}\n请基于此回答。"}]
            resp = llm_chat(messages)
            reply = (resp["choices"][0]["message"].get("content") or "").strip()
            for tc in tcl:
                tc.pop("result_full", None)
            return AgentChatResponse(reply=reply, citations=[], tool_calls=tcl)
    if intent == "school":
        # 流派: 提取流派名 → get_school → 注入回答
        m = re.search(r"([一-鿿]{2,8}(?:主义|哲学|学派|学))", req.message)
        name = m.group(1) if m else req.message[:12]
        result = TOOLS["get_school"]["execute"]({"name": name})
        if "error" in result:
            intent = "chat"  # 流派未命中 → 走普通对话
        else:
            tcl = [{"name": "get_school", "args": {"name": name}, "result_summary": str(result)[:200],
                    "result_full": result, "thought": f"识别到流派查询, 调用 get_school({name})"}]
            messages = [{"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": req.message},
                        {"role": "system", "content": f"工具「get_school」返回: {json.dumps(result, ensure_ascii=False)[:4000]}\n请基于流派资料回答。"}]
            resp = llm_chat(messages)
            reply = (resp["choices"][0]["message"].get("content") or "").strip()
            for tc in tcl:
                tc.pop("result_full", None)
            return AgentChatResponse(reply=reply, citations=[], tool_calls=tcl)
    if intent == "phti":
        # 哲学人格测试: 出题 → LLM 引导答题
        result = TOOLS["phti_test"]["execute"]({})
        tcl = [{"name": "phti_test", "args": {}, "result_summary": str(result)[:200],
                "result_full": result, "thought": "识别到测试需求, 生成哲学人格测试题"}]
        q_text = "\n".join(f"{q['no']}. {q['text']}" for q in result.get("questions", []))
        messages = [{"role": "system", "content": "你是'深哲'——哲学人格测试主持者。请用温暖有趣的风格展示下面 5 道题，并引导用户依次回答（A=非常同意 B=同意 C=中立 D=不同意 E=非常不同意）。提示用户可用格式回复: 1A 2B 3C 4D 5E。\n\n题目:\n" + q_text}]
        resp = llm_chat(messages)
        reply = (resp["choices"][0]["message"].get("content") or "").strip()
        for tc in tcl:
            tc.pop("result_full", None)
        return AgentChatResponse(reply=reply, citations=[], tool_calls=tcl)
    if intent == "phti_score":
        # 测试判型: 基于答案推断哲学倾向
        messages = [{"role": "system", "content": "你是'深哲'——哲学人格测试评分者。用户给出了测试答案（数字+字母格式）。请基于答案推断其哲学倾向（如: 斯多葛/存在主义/功利主义/犬儒/理想主义等），给出: ① 匹配类型 ② 类型说明（100字内） ③ 一句有趣的点评。用中文。"},
                    {"role": "user", "content": f"我的答案是: {req.message}"}]
        resp = llm_chat(messages)
        reply = (resp["choices"][0]["message"].get("content") or "").strip()
        return AgentChatResponse(reply=reply, citations=[], tool_calls=[{"name": "phti_score", "args": {"answers": req.message},
                                                                          "result_summary": "已判型", "thought": "识别到测试答案, 进行哲学人格判型"}])
    # 组装消息
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in req.history[-6:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    if req.book_id:
        b = book_by_id(req.book_id)
        if b:
            messages.append({"role": "system", "content": f"用户正在阅读《{b.get('title')}》（{b.get('author')}），回答可优先结合此书。"})
    messages.append({"role": "user", "content": req.message})

    # 纯 JSON 工具协议（不传 tools 参数, 提示词驱动——DeepSeek 原生 function calling 多轮后不稳定）
    def extract_tool_call(content):
        """括号平衡解析 {TOOL:{...}}（嵌套 JSON 的 } 不能用非贪婪正则）"""
        start = content.find("{TOOL:")
        if start < 0:
            return None, content
        i = content.find("{", start + 6)  # 跳过 "TOOL:" 前缀, 从真实 JSON 的 { 开始
        if i < 0:
            return None, content
        depth = 0
        for j in range(i, len(content)):
            if content[j] == "{":
                depth += 1
            elif content[j] == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(content[i:j + 1]), content[:start] + content[j + 1:]
                    except Exception:
                        return None, content
        return None, content

    tool_calls_log = []
    try:
        # ① 确定性检索（后端直调, 不依赖 LLM 工具决策——LLM 的 TOOL 协议输出不稳定）
        query = re.sub(r"[？?！!。，,、\s]+", " ", req.message)[:50]
        result = TOOLS["search_books"]["execute"]({"query": query, "limit": 6})
        tool_calls_log.append({"name": "search_books", "args": {"query": query},
                               "result_summary": str(result)[:200], "result_full": result,
                               "thought": f"检索「{query}」相关原典"})
        recommend = any(w in req.message for w in ["推荐", "入门", "书目", "读什么", "书单", "哪些书"])
        if recommend:
            r2 = TOOLS["list_books"]["execute"]({"region": "西方"})
            tool_calls_log.append({"name": "list_books", "args": {"region": "西方"},
                                   "result_summary": str(r2)[:200], "result_full": r2})
        else:
            r2 = None
        # ② 注入检索结果 → LLM 生成
        retrieval_note = (f"系统已检索到以下原典片段:\n{json.dumps(result, ensure_ascii=False)[:5000]}"
                          + (f"\n\n书目数据:\n{json.dumps(r2, ensure_ascii=False)[:2500]}" if r2 else "")
                          + "\n请基于检索到的原典回答。引用标注【《书名》· 章节】, 引用原文用引号。"
                            "推荐/书目类问题给出具体书名与推荐理由。")
        messages.append({"role": "system", "content": retrieval_note})
        resp = llm_chat(messages)
        msg = resp["choices"][0]["message"]
        # ③ 可选增强: LLM 若输出 TOOL（读章节深入）→ 执行 → 再生成（最多 2 轮）
        for _ in range(2):
            content = msg.get("content") or ""
            call, rest = extract_tool_call(content)
            if call is None:
                break
            thought = content[:content.find("{TOOL:")].strip() or f"需要调用工具获取更多信息"
            name = call.get("name", "")
            args = call.get("args", {})
            tool = TOOLS.get(name)
            result2 = tool["execute"](args) if tool else {"error": f"未知工具 {name}"}
            tool_calls_log.append({"name": name, "args": args, "result_summary": str(result2)[:200],
                                   "result_full": result2, "thought": thought[:300]})
            messages.append({"role": "assistant", "content": rest[:3000]})
            messages.append({"role": "system",
                             "content": f"工具「{name}」返回: {json.dumps(result2, ensure_ascii=False)[:3000]}\n请直接给出最终回答（不要输出任何工具标记）。"})
            resp = llm_chat(messages)
            msg = resp["choices"][0]["message"]
        reply = (msg.get("content") or "").strip()
        # 清理残留 TOOL 标记
        _, reply = extract_tool_call(reply)
        reply = reply.strip()
        if not reply:
            reply = "（无回答）"
        # 提取引用（用完整结果, 非截断摘要）
        citations = []
        for tc in tool_calls_log:
            if tc["name"] == "search_books" and tc.get("result_full"):
                try:
                    for item in tc["result_full"].get("results", [])[:3]:
                        citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                          "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
                except Exception:
                    pass
            tc.pop("result_full", None)  # 大字段不入响应
        return AgentChatResponse(reply=reply, citations=citations, tool_calls=tool_calls_log)
    except Exception as e:
        return AgentChatResponse(reply=f"智能体出错: {e}", citations=[], tool_calls=tool_calls_log)
