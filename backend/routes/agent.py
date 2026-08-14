"""哲学智能体核心: 可插拔工具集 + DeepSeek 编排（function calling）
核心开放点: TOOLS 注册表——新增能力 = 注册一个新工具（一行注册 + execute 函数）
V1 工具: search_books / get_book_detail / get_chapter / query_graph / get_philosopher / list_books
"""
import json, os, re, time, hashlib, urllib.request, threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from typing import Optional, List

import guard

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

def llm_chat(messages, tools=None, temperature=0.7, max_tokens=2000, thinking=False):
    """DeepSeek chat 调用（支持 function calling + 思考模式）
    思考模式: reasoning_content 思维链 + 工具调用必须完整回传 reasoning_content（否则 400）
    """
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens}
    if thinking:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "medium"   # 思考模式不支持 temperature（high 思考期过长: 30-90s 无输出）
    else:
        body["temperature"] = temperature
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
            print(f"[llm] HTTP {e.code}: {err_body[:200]}", flush=True)   # 细节只进日志
            if attempt == 2:
                # 2026-08-14 脱敏: 客户端不携带上游响应体（可能含请求/密钥细节）
                raise Exception(f"DeepSeek API HTTP {e.code}")
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

def _safe_bid(bid):
    """bid 白名单校验（2026-08-14 安全加固: 防 LLM 注入 bid 拼路径读任意 JSON）"""
    if not isinstance(bid, str) or not re.fullmatch(r"[0-9a-f]{10,16}", bid):
        return None
    return bid if book_by_id(bid) else None

def chapter_meta(bid):
    bid = _safe_bid(bid)
    if not bid:
        return None
    mp = CHAPTERS_DIR / bid / "meta.json"
    if mp.exists():
        return json.load(open(mp, encoding="utf-8"))
    return None

def read_chapter(bid, idx):
    bid = _safe_bid(bid)
    if not bid:
        return None
    try:
        idx = int(idx)
    except Exception:
        return None
    if idx < 0:
        return None
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

# ── 向量检索（智谱 embedding-2, numpy 余弦; 构建完成自动启用, 失败降级关键词）──
_vectors = None
_vector_index = None
def _load_vectors():
    global _vectors, _vector_index
    if _vectors is None:
        p = DATA / "embeddings"
        if (p / "vectors.npy").exists() and (p / "index.json").exists():
            try:
                import numpy as np
                _vectors = np.load(p / "vectors.npy")
                _vector_index = json.load(open(p / "index.json", encoding="utf-8"))
            except Exception:
                pass
    return _vectors, _vector_index

def _embed_query(q):
    try:
        from openai import OpenAI
        cli = OpenAI(api_key=os.environ.get("ZHIPU_API_KEY", ""),
                     base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=15)
        r = cli.embeddings.create(model="embedding-2", input=[q[:500]])
        return r.data[0].embedding
    except Exception:
        return None

def _exec_search_books(args):
    query = args.get("query", "")
    limit = min(int(args.get("limit", 5)), 10)
    # 向量优先（索引就绪时）
    vec = _embed_query(query)
    if vec is not None:
        _vectors, _vector_index = _load_vectors()
        if _vectors is not None and len(_vectors) > 0:
            import numpy as np
            v = np.array(vec, dtype="float32")
            norm = np.linalg.norm(v)
            if norm > 0:
                v = v / norm
                vv = _vectors / np.linalg.norm(_vectors, axis=1, keepdims=True)
                sims = vv @ v
                top = np.argsort(-sims)[:limit * 3]
                results = []
                for ti in top:
                    if sims[ti] < 0.35:
                        continue
                    it = _vector_index[ti]
                    ch = read_chapter(it["bid"], it["idx"])
                    if not ch or not ch.get("text"):
                        continue
                    b = book_by_id(it["bid"])
                    text = ch["text"]
                    results.append({
                        "book_id": it["bid"], "book_title": b.get("title") if b else it["bid"],
                        "author": b.get("author", "") if b else "",
                        "chapter_idx": it["idx"], "chapter_title": ch.get("title", ""),
                        "snippet": text[:220].replace(chr(10), " "), "score": round(float(sims[ti]), 3),
                    })
                if results:
                    return {"results": results[:limit * 3], "query": query, "method": "vector"}
    # 关键词兜底
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
            "toc": [t.get("title") if isinstance(t, dict) else t for t in (meta.get("toc") or [])][:30]}

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

# ── 工具 7: write_essay（学生作文——注册为工具, 对话流意图触发; 支持多轮修改）──
# 多轮修改记忆: 持久化到文件（进程重启不丢）; 作文按题目记忆（避免跨主题串味）
# 2026-08-14 per-user 加固（P0）: 记忆按用户隔离（guard.user_memory_key）,
#   原子写（tmp+rename）防并发损坏; 旧单用户格式自动迁移到 default 槽
MEM_FILE = DATA / "agent_memory.json"
_mem_lock = threading.Lock()
_mem_all = None   # 全量缓存: {user_key: {"essays":{}, "image":None, "experiment":None, "debate":None}}

def _mem_slot():
    """当前用户的记忆槽 dict（懒加载全量缓存）"""
    global _mem_all
    if _mem_all is None:
        _mem_all = {}
        try:
            raw = json.load(open(MEM_FILE, encoding="utf-8"))
            if isinstance(raw, dict):
                if raw and any(str(k).startswith(("u", "ip")) for k in raw):
                    _mem_all = raw
                else:
                    _mem_all["default"] = raw   # 兼容旧单用户格式 → default 槽
        except Exception:
            _mem_all = {}
    key = guard.user_memory_key()
    if key not in _mem_all:
        _mem_all[key] = {"essays": {}, "image": None, "experiment": None, "debate": None}
    return _mem_all[key]

def _save_agent_memory():
    """原子写全量记忆（tmp+rename; 失败静默——记忆非关键数据）"""
    global _mem_all
    if _mem_all is None:
        return
    with _mem_lock:
        try:
            tmp = MEM_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps(_mem_all, ensure_ascii=False), encoding="utf-8")
            tmp.replace(MEM_FILE)
        except Exception:
            pass

def _exec_write_essay(args):
    topic = args.get("topic") or args.get("query") or ""
    if not topic:
        return {"error": "缺少作文题目"}
    try:
        word_count = int(args.get("word_count", 800))
    except Exception:
        word_count = 800
    modify = (args.get("modify") or "").strip()
    # 自动检测修改意图（LLM 未显式传 modify 时）: 修改词 + 存在对应题目记忆 → 对上次作文修改
    if not modify:
        intent_text = f"{topic} {args.get('extra', '')} {args.get('genre', '')}"
        if any(w in intent_text for w in ("修改", "改一下", "重写", "调整", "改成", "换一个",
                                          "增加", "减少", "删掉", "美化", "润色", "改写", "扩展", "精简")):
            hit = _find_essay_topic(topic)
            if hit:
                modify = topic
                topic = hit
    reply, citations, tcl = _essay_pipeline(topic, args.get("genre", "议论文"),
                                            word_count, args.get("extra", ""), modify)
    _save_agent_memory()   # 持久化多轮修改记忆
    return {"essay": reply, "citations": citations, "steps": tcl}

register_tool(
    "write_essay",
    "根据题目写一篇哲学作文（议论文/读后感等）。自动检索原典原文支撑论据, 带引用标注。用户说'修改/重写/改一下作文'时传 modify='修改要求', 工具自动基于上次作文修改。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "作文题目（修改请求时可为修改要求）"},
        "genre": {"type": "string", "description": "文体: 议论文/读后感/论述"},
        "word_count": {"type": "integer", "description": "目标字数"},
        "extra": {"type": "string", "description": "附加要求"},
        "modify": {"type": "string", "description": "修改要求（修改上次作文时传, 如: 改成800字/换个开头/论点再强化）"}},
     "required": ["topic"]},
    _exec_write_essay,
)

# ── 工具 8: generate_image（生图——Agnes Image 2.1 Flash, 文生图; 免费档 $0/张; 支持多轮修改）──
AGNES_API_URL = "https://apihub.agnes-ai.com/v1/images/generations"
AGNES_MODEL = "agnes-image-2.1-flash"
AGNES_IMG_DIR = BASE.parent / "agent-app" / "public" / "agent_images"
# 内置哲学风格系统提示词: 全局视觉规范（象征/色彩/构图/质感）
AGNES_PHILO_STYLE = (
    "这是哲学概念可视化图像, 必须遵循哲学插图美学: "
    "①象征与隐喻优先——光、阶梯、深渊、圆环、面具、闪电等意象承载思想; "
    "②色彩克制而深刻——低饱和暖调或黑白基调, 至多一个强调色; "
    "③构图庄重——对称或纵深透视, 适当留白, 像古典思想史铜版画或书籍插页; "
    "④质感写实——布面油画颗粒、铜版画刻线、黑白木刻或电影级写实; "
    "⑤拒绝直白图解——保留可诠释的暗示与张力。高信息密度, 细节丰富。"
)
# 主题→风格方向匹配（哲学概念 → 艺术风格; 未命中用默认哲学插图风）
AGNES_STYLE_HINTS = [
    (["洞穴", "理想国", "寓言", "囚徒"], "古典主义油画, 明暗对比, 柏拉图式光影寓言"),
    (["永恒轮回", "轮回", "圆环", "环"], "衔尾蛇与循环几何, 超现实主义, 神秘象征"),
    (["超人", "查拉图斯特拉", "山峰", "闪电", "攀登"], "浪漫主义崇高风景画, 垂直构图, 剪影与光"),
    (["存在", "荒诞", "虚无", "西西弗", "孤独", "荒原"], "表现主义, 粗粝笔触, 存在主义的孤寂感"),
    (["权力意志", "尼采", "酒神", "日神", "悲剧"], "德国浪漫主义铜版画, 深色基调金色勾勒"),
    (["辩证法", "正反合", "扬弃", "黑格尔"], "三重视觉结构与螺旋构图, 抽象几何"),
    (["斯多葛", "节制", "坚忍", "罗马"], "古典雕塑与静物, 大理石质感, 平静庄重"),
    (["虚空", "禅", "道家", "无为", "老子", "庄子"], "水墨画, 留白意境, 极简山水的空灵"),
    (["仁", "礼", "孔子", "儒家"], "宋代山水与文人画, 卷轴构图, 温润墨色"),
    (["启蒙", "理性", "光", "自由", "卢梭"], "新古典主义, 晨光穿透云层, 崇高理性之光"),
]

def _agnese_enhance_prompt(prompt):
    """哲学风格增强: 主题风格匹配 + 全局视觉规范 + 高密度要求"""
    style = None
    for keywords, hint in AGNES_STYLE_HINTS:
        if any(k in prompt for k in keywords):
            style = hint
            break
    head = f"主题: {prompt}。风格: {style or '哲学概念插图, 古典与现代融合'}。"
    return f"{head}{AGNES_PHILO_STYLE}"

# 无代理 opener（避免 urllib 代理检测触发反向 DNS 11s 超时——与 admin.py 同款修复）
_NO_PROXY = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def _download_image(url, save_to):
    req = urllib.request.Request(url, headers={"User-Agent": "PhiAgent/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:   # 走系统代理（Agnes 存储域国内需代理）
        data = r.read()
    with open(save_to, "wb") as f:
        f.write(data)
    return len(data)

def _wiki_search_image(query):
    """维基百科搜参考图（pageimages 原创图 URL）——中文优先, 英文兜底"""
    import urllib.parse as _up
    for lang in ("zh", "en"):
        url = (f"https://{lang}.wikipedia.org/w/api.php?action=query&generator=search"
               f"&gsrsearch={_up.quote(query)}&gsrlimit=4&gsrnamespace=0"
               f"&prop=pageimages&piprop=original&format=json&origin=*")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "PhiAgent/1.0"})
            with _NO_PROXY.open(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            for pid, page in (data.get("query", {}).get("pages", {}) or {}).items():
                for key in ("original", "thumbnail"):
                    src = page.get(key, {}).get("source")
                    if src:
                        return src
        except Exception:
            continue
    return None

PHILOSOPHER_DIR = PUBLIC / "philosopher"

def _local_reference_image(name):
    """本地哲学家肖像（DP 数据 617 张）: 括号前基础名或包含匹配"""
    if not PHILOSOPHER_DIR.exists():
        return None
    for f in os.listdir(PHILOSOPHER_DIR):
        if not f.endswith((".webp", ".jpg", ".png")):
            continue
        base = Path(f).stem.split(" (")[0].strip()
        if base and (base == name or (name and base in name) or (name and name in base)):
            return str(PHILOSOPHER_DIR / f)
    return None

def _detect_reference(prompt):
    """自动判断是否需要参考图: 本地肖像文件名匹配 > 常见别名 > 明确参考意图"""
    # 1) 本地哲学家肖像（DP 数据, 617 张——比网络搜索更可靠的参考图源）
    if PHILOSOPHER_DIR.exists():
        for f in os.listdir(PHILOSOPHER_DIR):
            if not f.endswith((".webp", ".jpg", ".png")):
                continue
            base = Path(f).stem.split(" (")[0].strip()
            if base and len(base) <= 12 and base in prompt:
                return base
    # 2) 常见别名（本地无文件时, 用于 wiki 兜底检索）
    for alias in ("苏格拉底", "柏拉图", "亚里士多德", "尼采", "康德", "黑格尔", "叔本华", "马克思",
                  "维特根斯坦", "海德格尔", "萨特", "笛卡尔", "斯宾诺莎", "休谟", "卢梭",
                  "老子", "庄子", "孔子", "孟子", "福柯", "德里达", "克尔凯郭尔"):
        if alias in prompt:
            return alias
    # 3) 明确参考意图（非人物, 概念图带参考词）
    if any(w in prompt for w in ("参考", "肖像", "写真", "画像", "写实人像", "长相")):
        return prompt[:60]
    return None

def _exec_generate_image(args):
    slot = _mem_slot()
    prompt = (args.get("prompt") or "").strip()
    if not prompt:
        return {"error": "缺少图像描述 prompt"}
    api_key = os.environ.get("AGNES_API_KEY", "")
    if not api_key:
        return {"error": "服务端未配置 AGNES_API_KEY"}
    size = args.get("size") or "1K"
    ratio = args.get("ratio") or "1:1"
    enhanced = _agnese_enhance_prompt(prompt)   # 内置哲学风格 system prompt
    body = {"model": AGNES_MODEL, "prompt": enhanced, "size": size, "ratio": ratio,
            "extra_body": {"response_format": "url"}}
    reference = {"used": False}
    # 多轮修改: 修改意图词 + 存在上次生成图 → 图生图修改（直接对上一轮结果改）
    MODIFY_HINTS = ("修改", "改成", "换成", "调整", "重画", "美化", "换个", "加上", "去掉",
                    "放大", "缩小", "夜景", "日景", "换个角度", "重新画", "优化", "调色", "改一下")
    if slot["image"] and any(w in prompt for w in MODIFY_HINTS):
        prev_path = PUBLIC / slot["image"]["local"].lstrip("/")
        if prev_path.exists():
            try:
                with open(prev_path, "rb") as f:
                    prev_data = f.read()
                if prev_data and len(prev_data) < 8 * 1024 * 1024:
                    import base64
                    body["extra_body"]["image"] = ["data:image/jpeg;base64," + base64.b64encode(prev_data).decode()]
                    reference = {"used": True, "query": f"修改上一张图（{slot['image']['local']}）",
                                 "source": slot["image"]["local"]}
            except Exception:
                pass  # 读取上次图失败 → 降级文生图
    # 参考图绑定: 哲学家肖像/参考意图 → 本地肖像优先, 维基百科兜底 → Agnes 图生图（形象准确）
    ref_q = _detect_reference(prompt)
    if ref_q and not body["extra_body"].get("image"):
        img_data = None
        ref_src = None
        # 1) 本地哲学家肖像（DP 数据, 离线可靠）
        local_path = _local_reference_image(ref_q)
        if local_path:
            try:
                with open(local_path, "rb") as f:
                    img_data = f.read()
                ref_src = local_path
            except Exception:
                img_data = None
        # 2) 维基百科兜底（本地无肖像时）
        if not img_data:
            src = _wiki_search_image(ref_q)
            if src:
                try:
                    img_req = urllib.request.Request(src, headers={"User-Agent": "PhiAgent/1.0"})
                    with _NO_PROXY.open(img_req, timeout=30) as r:
                        img_data = r.read()
                    ref_src = src
                except Exception:
                    img_data = None
        if img_data and len(img_data) < 8 * 1024 * 1024:
            import base64
            body["extra_body"]["image"] = ["data:image/jpeg;base64," + base64.b64encode(img_data).decode()]
            reference = {"used": True, "query": ref_q, "source": ref_src}
    req = urllib.request.Request(AGNES_API_URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {api_key}"})
    try:
        # Agnes 需走系统代理（国内直连被 RST）; 首次代理检测有 ~1s 开销, 可接受
        with urllib.request.urlopen(req, timeout=300) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": f"Agnes HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:200]}"}
    except Exception as e:
        return {"error": f"Agnes 请求失败: {str(e)[:120]}", "hint": "Apihub 需网络代理（国内直连被墙）——请开启系统代理后重试"}
    items = resp.get("data") or []
    if not items or not items[0].get("url"):
        return {"error": "Agnes 未返回图像", "raw": str(resp)[:200]}
    url = items[0]["url"]
    AGNES_IMG_DIR.mkdir(parents=True, exist_ok=True)
    fn = hashlib.md5(f"{prompt}|{time.time()}".encode()).hexdigest()[:12] + ".png"
    save_to = AGNES_IMG_DIR / fn
    try:
        size_bytes = _download_image(url, save_to)
    except Exception as e:
        return {"error": f"图像下载失败: {str(e)[:120]}", "remote_url": url}
    local = f"/agent_images/{fn}"
    slot["image"] = {"prompt": prompt, "local": local}
    _save_agent_memory()   # 持久化多轮修改记忆（per-user）
    return {"image_url": local, "prompt": prompt, "size": f"{size} {ratio}", "bytes": size_bytes,
            "reference": reference,
            "note": f"生成成功。回答中请以 ![{prompt[:20]}]({local}) 引用该图"}

register_tool(
    "generate_image",
    "生成哲学艺术图像（Agnes 生图: 概念插画/肖像/意境图）。人物肖像自动绑定本地参考图; '修改/改成/调整/重画刚才的图'时基于上次结果图生图修改。触发: '生成图片/画一张画/概念插画/画像/艺术图'。**星图/脑图/关系图/结构图/地图不是本工具职责——那是 conceptual_map 的。**",
    {"type": "object", "properties": {"prompt": {"type": "string", "description": "图像描述（可中文, 建议: 主体+场景+风格+构图）"}, "size": {"type": "string", "description": "档位 1K/2K/3K/4K（默认 1K）"}, "ratio": {"type": "string", "description": "宽高比 1:1/16:9/9:16/4:3/3:4 等（默认 1:1）"}}, "required": ["prompt"]},
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
SYSTEM_PROMPT = """你是"深哲"（PhiAgent）——一个严谨的哲学智能体，基于 403 本哲学原著（柏拉图到德里达）与 687 位哲学家资料库工作。

## 工具调用格式（重要）
需要调用工具时，在输出中嵌入工具标记（二选一）:
- JSON 格式: {TOOL:{"name":"search_books","args":{"query":"..."}}}
- XML 格式: <invoke name="search_books"><parameter name="query">...</parameter></invoke>
禁止同时输出多个标记混淆; 工具结果返回后继续思考。

## 工作方式（ReAct）
按「思考 → 行动 → 观察」循环工作：
1. 先思考：判断需要什么信息、该调用哪个工具。
2. 行动：通过 function calling 调用工具（可并行调用多个）。
3. 观察：根据工具返回结果继续思考，直到信息充分。
4. 最终：输出完整回答。信息不足时继续调用工具，绝不凭记忆编造。

## 可用工具
（工具清单由 TOOLS 注册表在模块加载时自动生成, 见文件末尾——不再手写, 防清单漂移）

## 铁律
1. 凡涉及具体哲学主张/概念/出处，必须先调用 search_books 或 get_chapter 检索原文，用真实原文支撑，不得凭记忆编造引文。
2. 回答必须标注引用来源: 【《书名》· 章节名】。
3. 涉及哲学家关系（师承/影响/论敌）时调用 query_graph；涉及流派时调用 get_school；涉及哲人资料时调用 get_philosopher。
4. 用户要求对比时调用 compare_views；写作文时调用 write_essay；辩论时调用 philosopher_debate；决策求助时调用 advisor_council。
5. 引用原文时用引号，并说明是原典原文还是概括。
6. 若检索无结果，如实说明"库中未检索到"，不硬答、不编造。
7. 回答使用中文，严谨、清晰、有层次；适度苏格拉底式反问，但不回避问题。
8. 避免"哲学废话"：每个论断要么有原文依据，要么明确标注为分析/推测。
9. 用户要求扮演/以某哲学家口吻回答时调用 role_play（人格包返回后以其第一人称作答, 不必再检索原典）。
10. 工具调用纪律: 同一检索工具不要连续重复调用; 累计检索 ≥3 次或材料已足够时, 必须停止调用工具, 直接基于已有材料输出最终回答（输出 {TOOL:...} 只用于确有必要的新检索, 禁止无意义重复）。"""

class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    book_id: Optional[str] = None  # 阅读语境（来自阅读器的提问）
    agent: str = "general"         # 智能体广场: general=深哲; nietzsche 等=哲学家智能体
    language: Optional[str] = None # zh/en——前端语言偏好（匿名用户也能生效; 登录用户以 profile 为准）

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
6. 若下方"联网检索结果"中有与题目相关的当代案例/时事/数据/学者观点，至少引用 1 处丰富论据层次，并以[标题](链接)标注来源（与原典的【《书名》·章节】标注区分开）。

原典检索结果:
{retrieval}
"""

@router.post("/api/agent/essay")
async def agent_essay(req: EssayRequest, _g: dict = Depends(guard.agent_guard)):
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
    if any(w in msg for w in ["对比", "区别", "有何不同", "异同", "比较", " vs "]):
        return "compare"
    if any(w in msg for w in ["聊聊", "讨论一下", "你怎么看", "谈谈", "如何看待", "探讨"]):
        return "socratic"
    if any(w in msg for w in ["辩论", "辩一辩", "辩驳"]):
        return "debate"
    if any(w in msg for w in ["思想实验", "电车难题", "洞穴比喻", "假设一下"]):
        return "thought_exp"
    if any(w in msg for w in ["决策", "该不该", "怎么办", "纠结", "困惑", "帮我决定", "选择困难"]):
        return "council"
    if any(w in msg for w in ["评审", "批改", "修改建议", "点评"]):
        return "paper_review"
    return "chat"


INTENT_PROMPT = """判断用户意图并只输出 JSON（无其他文字）:
{"intent": "...", "params": {...}}
意图选项与触发场景:
- compare: 对比两人/两概念观点（params: a, b 如 {"a":"休谟","b":"康德"}）
- socratic: 想探讨/聊聊某观点（params: topic）
- debate: 让哲学家们辩论（params: topic, speakers 可选）
- thought_exp: 思想实验/假设推演（params: base）
- council: 人生决策/困惑求助（params: question）
- paper_review: 评审作文/论文（params: text）
- chat: 原典问答（默认, 无需 params）
用户消息: {message}"""

def llm_detect_intent(message):
    """LLM 语义意图判断（规则未命中时的兜底——compare/socratic/debate/.../chat）"""
    try:
        resp = llm_chat([{"role": "user", "content": INTENT_PROMPT.format(message=message[:300])}],
                        temperature=0.1, max_tokens=200)
        content = (resp["choices"][0]["message"].get("content") or "").strip()
        # 提取 JSON
        import re as _re
        m = _re.search(r"\{.*\}", content, _re.S)
        if m:
            d = json.loads(m.group(0))
            if d.get("intent") in ("compare", "socratic", "debate", "thought_exp", "council", "paper_review", "chat"):
                return d.get("intent"), d.get("params") or {}
    except Exception:
        pass
    return "chat", {}


def _find_essay_topic(text):
    """在按题目记忆中找与修改请求相关的作文（题目包含匹配）"""
    for t in _mem_slot()["essays"]:
        if not t:
            continue
        if t in text or (text[:10] and text[:10] in t):
            return t
    return None

def _essay_pipeline(topic, genre="议论文", word_count=800, extra="", modify=""):
    """作文生成/修改——返回 (reply, citations, tool_calls_log)
    多轮修改: modify 非空且存在对应题目记忆 → 基于上次文本改写（沿用原论点与原典引用, 不重新检索）"""
    tool_calls_log = []
    slot = _mem_slot()
    prev = slot["essays"].get(topic)
    if modify and prev:
        prompt = (f"用户要求修改作文。修改要求: {modify}\n\n"
                  f"上次作文题目: {topic}\n"
                  f"上次作文（{prev.get('genre', '')}, 目标{prev.get('word_count', '')}字）:\n"
                  f"---\n{prev['text']}\n---\n\n"
                  f"请按要求修改: 保持原作文的论点与原典引用, 只做要求的调整; 输出修改后的完整作文（目标{word_count}字）。")
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.75,
                        max_tokens=min(word_count * 2 + 500, 4000))
        reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（修改失败，请重试）"
        slot["essays"][topic] = {"text": reply, "genre": genre, "word_count": word_count}
        return reply, [], tool_calls_log
    query = re.sub(r"[？?！!。，,、\s]+", " ", topic)[:50]
    result = TOOLS["search_books"]["execute"]({"query": query, "limit": 6})
    tool_calls_log.append({"name": "search_books", "args": {"query": query},
                           "result_summary": str(result)[:200], "result_full": result,
                           "thought": f"作文需原典支撑, 检索「{query}」"})
    retrieval = json.dumps(result, ensure_ascii=False)[:6000]
    # 联网补充论据（避免拘泥于知识库: 当代观点/时事背景/其他学者论述）
    web_text = ""
    try:
        web = TOOLS["websearch"]["execute"]({"query": query, "max_results": 5})
        if isinstance(web, dict) and web.get("results"):
            web_text = json.dumps(web["results"], ensure_ascii=False)[:2500]
            tool_calls_log.append({"name": "websearch", "args": {"query": query},
                                   "result_summary": str(web)[:200], "result_full": web,
                                   "thought": f"联网补充「{query}」的当代论据与背景"})
    except Exception:
        web_text = ""
    prompt = ESSAY_PROMPT.format(genre=genre, topic=topic, word_count=word_count,
                                 extra=extra or "无", retrieval=retrieval)
    if web_text:
        prompt += (f"\n\n联网检索结果（当代论据/时事背景/其他论述——用于丰富论据层次, "
                   f"引用时以[标题](链接)标注来源; 若与题目无关可忽略）:\n{web_text}")
    messages = [{"role": "user", "content": prompt}]
    resp = llm_chat(messages, temperature=0.75, max_tokens=min(word_count * 2 + 500, 4000))
    reply = (resp["choices"][0]["message"].get("content") or "").strip() or "（生成失败，请重试）"
    citations = [{"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")}
                 for item in result.get("results", [])[:4]]
    for tc in tool_calls_log:
        tc.pop("result_full", None)
    slot["essays"][topic] = {"text": reply, "genre": genre, "word_count": word_count}
    return reply, citations, tool_calls_log



def parse_tool_calls(msg):
    """标准 structured tool_calls + DeepSeek XML fallback（模块级, chat/stream 共用）"""
    tcs = msg.get("tool_calls") or []
    if not tcs:
        content = msg.get("content") or ""
        for m in re.finditer(r'<invoke name="([^"]+)">(.*?)</invoke>', content, re.S):
            name = m.group(1)
            args = {}
            for pm in re.finditer(r'<parameter name="([^"]+)">(.*?)</parameter>', m.group(2), re.S):
                args[pm.group(1)] = pm.group(2)
            tcs.append({"id": f"xml_{len(tcs)}",
                        "function": {"name": name, "arguments": json.dumps(args, ensure_ascii=False)}})
    return tcs


@router.post("/api/agent/chat")
# DEPRECATED（2026-08-14 标记）: 旧同步 ReAct 引擎, 前端已只用 /api/agent/stream_lg（LangGraph）。
# 保留作回滚备胎; 确认 stream_lg 稳定后删除（含 agent_stream 与同步循环助手, 仅保留 llm_chat/TOOLS）。
async def agent_chat(req: AgentChatRequest, _g: dict = Depends(guard.agent_guard)):
    if not API_KEY:
        return AgentChatResponse(reply="服务端未配置 DEEPSEEK_API_KEY", citations=[], tool_calls=[])
    # ── 组装消息（标准 ReAct: system + history + user）──
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for h in req.history[-8:]:
        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
    if req.book_id:
        b = book_by_id(req.book_id)
        if b:
            messages.append({"role": "system", "content": f"用户正在阅读《{b.get('title')}》（{b.get('author')}），回答可优先结合此书。"})
    messages.append({"role": "user", "content": req.message})

    # ── 工具 schema（function calling, LLM 自主决策）──
    tools = [{"type": "function", "function": {
        "name": n, "description": t["description"], "parameters": t["parameters"]}}
        for n, t in TOOLS.items()]

    tool_calls_log = []
    try:
        resp = llm_chat(messages, tools=tools)
        msg = resp["choices"][0]["message"]
        # ── ReAct 循环（max_steps=10; 每轮限 3 个工具防爆炸; 终止: 无 tool_calls → 最终回答）──
        for step in range(6):
            tcs = parse_tool_calls(msg)[:3]
            if not tcs:
                break
            if msg.get("tool_calls") and len(msg["tool_calls"]) > len(tcs):
                msg = {**msg, "tool_calls": msg["tool_calls"][:len(tcs)]}
            elif not msg.get("tool_calls") and tcs:
                msg = {**msg, "tool_calls": [{"id": tc["id"], "type": "function", "function": tc["function"]} for tc in tcs]}
            messages.append(msg)  # assistant（含 tool_calls）——tool 消息必须跟随
            thought = (msg.get("content") or "").strip()[:200] or f"调用工具"
            for ti, tc in enumerate(tcs):
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
                        result = {"error": str(e)}  # 标准: 错误作为工具结果返回（不吞）
                tool_calls_log.append({"name": name, "args": args,
                                       "result_summary": str(result)[:200], "result_full": result,
                                       "thought": thought if ti == 0 else ""})  # 思考只记首工具（防重复显示）
                messages.append({"role": "tool", "tool_call_id": tc.get("id", f"c{step}_{len(tool_calls_log)}"),
                                 "content": json.dumps(result, ensure_ascii=False)[:4000]})
            resp = llm_chat(messages, tools=tools)
            msg = resp["choices"][0]["message"]
        # 循环耗尽仍有 tool_calls → 强制无工具总结（best practice: forced-stop graceful degradation）
        if parse_tool_calls(msg):
            resp = llm_chat(_summary_tail(messages))  # 从最近 assistant 起裁剪（防 tool 消息 400）
            msg = resp["choices"][0]["message"]
        reply = (msg.get("content") or "").strip()
        # ── 防幻觉兜底（best practice: 概念题未检索 → 注入检索再生成; 扮演场景除外）──
        if (not any(t["name"] in ("search_books", "get_chapter") for t in tool_calls_log)
                and not any(t["name"] == "role_play" for t in tool_calls_log)
                and len(req.message) >= 4):
            query = re.sub(r"[？?！!。，,、\s]+", " ", req.message)[:50]
            result = TOOLS["search_books"]["execute"]({"query": query, "limit": 5})
            tool_calls_log.append({"name": "search_books", "args": {"query": query},
                                   "result_summary": str(result)[:200], "result_full": result,
                                   "thought": "概念题未检索, 自动检索原文防编造"})
            nl = chr(10)
            messages.append({"role": "system",
                             "content": f"系统检索「{query}」结果: {json.dumps(result, ensure_ascii=False)[:4000]}{nl}请基于检索到的原典回答, 引用标注【《书名》· 章节】。"})
            resp = llm_chat(messages)
            reply = (resp["choices"][0]["message"].get("content") or "").strip()
        # 清理残留 XML 工具调用（含 <tool_calls> 外层）
        reply = re.sub(r'<tool_calls>.*?</tool_calls>', '', reply, flags=re.S).strip()
        reply = re.sub(r'<invoke name="[^"]+">.*?</invoke>', '', reply, flags=re.S).strip()
        reply = reply or "（无回答）"
        # citations（search_books 完整结果）
        citations = []
        for tc in tool_calls_log:
            if tc["name"] == "search_books" and tc.get("result_full"):
                for item in tc["result_full"].get("results", [])[:3]:
                    citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                      "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
            tc.pop("result_full", None)
        return AgentChatResponse(reply=reply, citations=citations, tool_calls=tool_calls_log)
    except Exception as e:
        return AgentChatResponse(reply=f"智能体出错: {e}", citations=[], tool_calls=tool_calls_log)

# ── 高级工具（V2: compare/socratic/debate/thought_exp/council/paper_review）──
def _auto_visualize(prompt):
    """自动可视化: 生一张哲学风格概念图（失败不阻断主流程）"""
    try:
        img = _exec_generate_image({"prompt": prompt, "size": "1K"})
        if img and img.get("image_url"):
            return img["image_url"]
    except Exception:
        pass
    return None

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
    rounds = min(int(args.get("rounds", 4)), 6)
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

def _philosopher_profile(name):
    """哲学家思想档案（辩论人格注入层）——尼采走 AIAuthor 完整人格包, 其他哲学家走资料库。
    LoRA 接入点: 未来各哲学家 LoRA 就绪时, 在此处返回 LoRA 模型标识/加载对应模型发言。"""
    if "尼采" in name:
        b = _load_persona_bundle()
        persona = b.get("persona", {}) or {}
        snaps = b.get("snapshots", {}) or {}
        late = ((snaps.get("snapshots") or {}).get("late") or {}) if isinstance(snaps.get("snapshots"), dict) else {}
        meta = persona.get("meta", {}) or {}
        values = list(((persona.get("value_model") or {}).get("values", {}) or {}).items())[:5]
        parts = []
        if meta.get("description"):
            parts.append(f"身份: {meta['description'][:150]}")
        if late.get("identity"):
            parts.append(f"晚期尼采(1883-1888): {late['identity']}")
        if late.get("signature"):
            parts.append(f"核心思想: {late['signature']}")
        if values:
            parts.append("价值观: " + "; ".join(f"{k}(权重{v})" for k, v in values))
        return "；".join(parts) or None
    phils = get_philosophers()
    entry = None
    if isinstance(phils, dict):
        entry = phils.get(name)
        if not entry:
            for k, v in phils.items():
                if k and (name in k or k in name):
                    entry = v
                    break
    if entry and isinstance(entry, dict):
        parts = []
        if entry.get("era"):
            parts.append(f"年代: {entry['era']}")
        if entry.get("school"):
            parts.append(f"流派: {entry['school']}")
        if entry.get("bio"):
            parts.append(f"简介: {entry['bio'][:180]}")
        books = entry.get("books")
        if isinstance(books, list) and books:
            names = [b.get("title") if isinstance(b, dict) else str(b) for b in books[:3]]
            parts.append("代表作: " + "、".join(str(n) for n in names))
        return "；".join(parts) or None
    return None

# ── 交互式辩论: auto（一次性）/ step（逐轮, 用户触发）/ vs_user（用户参与）──
# 会话状态 per-user 化（2026-08-14 P0）: 存 _mem_slot()["debate"], 不再全局共享

def _debate_map_text(d_text):
    """辩论 → mermaid 观点演变图"""
    try:
        map_prompt = (f"将以下哲学辩论提炼为 mermaid flowchart 观点演变图（只输出 flowchart 代码本身, 不要 ``` 围栏）:\n"
                      f"规则: 节点=各哲学家的核心立场（10字内）; 箭头=反驳/回应关系, 用 '-->|反驳|' 或 '-->|回应|'; 最后加一个'合题/未决'节点。\n\n"
                      f"辩论:\n{d_text[:2500]}")
        mresp = llm_chat([{"role": "user", "content": map_prompt}], temperature=0.5, max_tokens=600)
        mt = (mresp["choices"][0]["message"].get("content") or "").strip()
        mt = re.sub(r"^```(?:mermaid)?\s*", "", mt)
        mt = re.sub(r"\s*```$", "", mt)
        if mt.startswith(("flowchart", "graph")):
            return f"```mermaid\n{mt}\n```"   # 带围栏返回, 前端直接渲染
        return None
    except Exception:
        return None

def _debate_round(sp_list, topic, ctx, round_no, user_speech=None):
    """生成一轮辩论发言（每人一次）; user_speech 非空时要求回应它"""
    round_out = []
    for sp in sp_list:
        profile = _philosopher_profile(sp)   # 人格注入: 思想档案（尼采=完整人格包, 其他=资料库）
        inject = f"\n思想档案（保持其真实思想与风格, 发言必须体现档案中的思想特征）:\n{profile}" if profile else ""
        prompt = (f"你是哲学家{sp}。针对论题「{topic}」，发表你的立场与论证（200字内）。{inject}"
                  f"辩论纪律（高阶）: ①反驳必须攻击对方体系的真正软肋（如先验演绎的循环性、范畴与内容的关系、必然性的根基）, "
                  f"避免打在对方体系外的无效反驳——先准确复述对方立场再攻击; ②涉及对方体系时忠实其原意, 不歪曲; "
                  f"③若为最终结论, 明确区分'体系内立场'与'后康德综合立场'。"
                  f"这是辩论第{round_no}轮。{'可回应前一位发言。' if ctx else '请先亮明核心立场。'}"
                  + (f"\n已有发言:\n{ctx}" if ctx else "")
                  + (f"\n用户的当前发言（必须正面回应, 并指出其逻辑漏洞或接受其合理处）:\n{user_speech}" if user_speech else ""))
        msgs = [{"role": "system", "content": f"你是{sp}——保持其真实思想风格, 用中文发言。"},
                {"role": "user", "content": prompt}]
        resp = llm_chat(msgs, temperature=0.9, max_tokens=400)
        speech = (resp["choices"][0]["message"].get("content") or "").strip()
        round_out.append(f"{sp}: {speech}")
    return round_out

def _exec_debate(args):
    slot = _mem_slot()
    topic = (args.get("topic") or "").strip()
    speakers = args.get("speakers") or "尼采、柏拉图"
    sp_list = [s.strip() for s in speakers.replace("和", "、").replace("与", "、").split("、") if s.strip()][:3] or ["尼采", "柏拉图"]
    mode = args.get("mode") or "auto"
    action = (args.get("action") or "start").strip().lower()
    user_speech = (args.get("user_reply") or "").strip()
    # 意图自动检测（LLM 未显式传 action 时）
    if action == "start":
        if any(w in topic for w in ("结束", "总结", "停止", "裁决", "收尾")):
            action = "summary"
        elif any(w in topic for w in ("继续", "下一轮", "接着", "再来", "加一轮", "第二轮", "第三轮")):
            action = "continue"
    # ── 结束辩论: 总结 + 演变图 ──
    if action == "summary" and slot["debate"]:
        sess = slot["debate"]
        d_text = "\n".join(sess["history"])
        prompt = (f"辩论结束, 请总结（400字内）: ①各方核心立场 ②最强交锋点（谁对谁的哪一点构成实质威胁）"
                  f"③是否达成共识/合题（明确标注'体系内'还是'后康德综合'视角）。\n\n辩论记录:\n{d_text[:4000]}")
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=900)
        summary = (resp["choices"][0]["message"].get("content") or "").strip()
        slot["debate"] = None
        _save_agent_memory()
        return {"debate_summary": summary, "map_text": _debate_map_text(d_text),
                "note": "辩论已结束。可发起新辩论。"}
    # ── 用户参与模式: 用户发言 → 哲学家回应 ──
    if user_speech and slot["debate"] and slot["debate"].get("mode") == "vs_user":
        sess = slot["debate"]
        ctx = "\n".join(sess["history"][-4:])
        round_out = _debate_round(sess["speakers"], sess["topic"], ctx, sess["rounds_done"] + 1, user_speech)
        sess["history"] += [f"用户: {user_speech}"] + round_out
        sess["rounds_done"] += 1
        _save_agent_memory()
        return {"debate": round_out, "note": "你可以继续反驳或提问, 或说'结束辩论'让我总结。"}
    # ── 逐轮模式: 继续下一轮 ──
    if action == "continue" and slot["debate"]:
        sess = slot["debate"]
        ctx = "\n".join(sess["history"][-4:])
        round_out = _debate_round(sess["speakers"], sess["topic"], ctx, sess["rounds_done"] + 1)
        sess["history"] += round_out
        sess["rounds_done"] += 1
        _save_agent_memory()
        return {"debate": round_out, "note": f"第{sess['rounds_done']}轮结束。说'继续'进入下一轮, '结束辩论'总结。"}
    # ── step / vs_user: 初始化会话 + 第一轮 ──
    if mode in ("step", "vs_user"):
        slot["debate"] = {"topic": topic, "speakers": sp_list, "mode": mode,
                           "rounds_done": 1, "history": []}
        round_out = _debate_round(sp_list, topic, "", 1)
        slot["debate"]["history"] = round_out
        _save_agent_memory()
        note = ("辩论开始（逐轮模式）。说'继续'进入下一轮, '结束辩论'总结。" if mode == "step"
                else "辩论开始（你参与）。请反驳或提问, 哲学家会回应你。")
        return {"debate": round_out, "note": note}
    # ── auto: 一次性生成全部轮次（默认, 原逻辑）──
    rounds = min(int(args.get("rounds", 2)), 3)
    debate = []
    for r in range(rounds):
        debate.extend(_debate_round(sp_list, topic, "\n".join(debate[-3:]), r + 1))
    ret = {"topic": topic, "debate": debate}
    img = _auto_visualize(f"哲学辩论: {topic}——多位思想者围绕同一论题的象征性对峙, 讲台与光影交错")
    if img:
        ret["image_url"] = img
        ret["note"] = f"回答末尾请以 ![辩论图]({img}) 引用该图"
    ret["map_text"] = _debate_map_text("\n".join(debate))
    return ret

register_tool("philosopher_debate",
    "哲学家辩论——三种模式: auto=一次性多轮（默认）; step=逐轮（用户说'继续'触发下一轮, '结束辩论'总结）; vs_user=用户参与（用户发言后传 user_reply=用户的话, 哲学家回应）。",
    {"type": "object", "properties": {
        "topic": {"type": "string", "description": "论题（'继续'/'结束辩论'等指令也放这里）"},
        "speakers": {"type": "string", "description": "哲学家, 逗号分隔"},
        "mode": {"type": "string", "enum": ["auto", "step", "vs_user"], "description": "辩论模式"},
        "action": {"type": "string", "enum": ["start", "continue", "summary"], "description": "逐轮模式: continue=下一轮, summary=结束总结"},
        "user_reply": {"type": "string", "description": "vs_user 模式: 用户的发言"}},
     "required": ["topic"]},
    _exec_debate)

def _exec_thought_exp(args):
    slot = _mem_slot()
    base = (args.get("base") or "").strip()
    if not base:
        return {"error": "缺少思想实验基础设定"}
    # 变体迭代: 修改词 + 存在上次实验 → 基于上次重推演, 对比立场变化
    if slot["experiment"] and any(w in base for w in ("改", "换成", "变体", "如果", "假设", "变化", "不同", "加", "减")):
        prompt = (f"用户对上次思想实验提出变体: 「{base}」\n"
                  f"上次实验:\n{slot['experiment']['text'][:1500]}\n\n"
                  f"请重新推演该变体（600字内）: ①新设定（100字内）②3 个哲学立场的推演（各 50 字）"
                  f"③与上次实验相比, 各立场结论发生了哪些变化。用中文。")
        resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=1000)
        reply = (resp["choices"][0]["message"].get("content") or "").strip()
        slot["experiment"] = {"base": base, "text": reply}
        _save_agent_memory()
        return {"experiment": reply}
    prompt = (f"基于「{base}」设计一个哲学思想实验或推演变体。输出: ① 实验设定（100字内）② 3 个哲学立场的推演（各 50 字）③ 它揭示的哲学问题。用中文。")
    resp = llm_chat([{"role": "user", "content": prompt}], temperature=0.9, max_tokens=800)
    reply = (resp["choices"][0]["message"].get("content") or "").strip()
    slot["experiment"] = {"base": base, "text": reply}
    _save_agent_memory()
    return {"experiment": reply}

register_tool("thought_experiment",
    "设计/推演哲学思想实验（电车难题变体/洞穴比喻现代版）——生成设定、多立场推演与启示; 用户说'改/换成/如果'时基于上次实验做变体迭代。",
    {"type": "object", "properties": {"base": {"type": "string"}}, "required": ["base"]},
    _exec_thought_exp)

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

# ── 工具: concept_trace（概念溯源——403 本书中的出现分布与演变）──
def _exec_concept_trace(args):
    concept = args.get("concept", "").strip()
    if not concept:
        return {"error": "缺少概念"}
    result = TOOLS["search_books"]["execute"]({"query": concept, "limit": 15})
    results = result.get("results", []) or []
    if not results:
        return {"concept": concept, "hits": 0, "timeline": [], "note": "库中未检索到该概念"}
    book_map = {b.get("id"): b for b in get_books()}
    entries, seen = [], set()
    for r in results[:15]:
        bid = r.get("book_id")
        b = book_map.get(bid) or {}
        title = r.get("book_title") or b.get("title") or ""
        if title in seen:
            continue
        seen.add(title)
        entries.append({
            "book": title, "author": r.get("author") or b.get("author") or "",
            "region": b.get("region") or "", "rank": b.get("rank"),
            "chapter": r.get("chapter_title"),
            "snippet": (r.get("snippet") or "")[:130],
        })
    return {"concept": concept, "hits": len(results), "timeline": entries[:10],
            "note": "按书聚合的概念出现分布; snippet 为原文命中片段, 回答时按作者/流派梳理概念用法演变"}

register_tool("concept_trace",
    "概念溯源——检索概念在 403 本原典中的出现分布与原文片段, 用于追踪概念的历史用法与演变（如'自由意志'在哪些书里出现）。",
    {"type": "object", "properties": {"concept": {"type": "string", "description": "哲学概念（如: 自由意志/存在/权力意志）"}}, "required": ["concept"]},
    _exec_concept_trace)

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
# 流式 agent: /api/agent/stream（SSE——实时思考过程 + 工具调用 + 最终回答逐 token）
# ═══════════════════════════════════════════════════════

def _summary_tail(messages):
    """强制总结裁剪: 从最近 assistant 起（tool 消息必须跟随 assistant(tool_calls), 否则 400）"""
    for i in range(len(messages) - 1, max(0, len(messages) - 20), -1):
        if messages[i].get("role") == "assistant":
            return [messages[0]] + messages[i:]
    return [messages[0]] + messages[-8:]


from fastapi.responses import StreamingResponse

def _sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

def llm_stream(messages, temperature=0.7, max_tokens=2000, thinking=False):
    """DeepSeek 流式（stream:true; 思考模式 yield ("reasoning", ...) 思维链, 普通 yield ("content", ...)）"""
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens, "stream": True}
    if thinking:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "medium"
    else:
        body["temperature"] = temperature
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{API_URL}/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        buffer = ""
        for raw in r:
            line = raw.decode("utf-8", "ignore")
            buffer += line
            while "\n" in buffer:
                ln, buffer = buffer.split("\n", 1)
                ln = ln.strip()
                if not ln.startswith("data:"):
                    continue
                payload = ln[5:].strip()
                if payload == "[DONE]":
                    return
                try:
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0].get("delta", {})
                    if delta.get("reasoning_content"):
                        yield ("reasoning", delta["reasoning_content"])
                    elif delta.get("content"):
                        yield ("content", delta["content"])
                except Exception:
                    continue

@router.post("/api/agent/stream")
# DEPRECATED（2026-08-14 标记）: 旧自研流式引擎（{TOOL:} JSON 协议）, 前端已只用 stream_lg。
# 与 agent_chat 一起在确认 stream_lg 稳定后删除。
async def agent_stream(req: AgentChatRequest, _g: dict = Depends(guard.agent_guard)):
    """流式 agent: 思考模式（思维链实时）+ JSON 工具协议（{TOOL:...}, 无 function calling 格式 400 风险）"""
    def extract_tool_call(content):
        """解析工具调用: {TOOL:JSON} 优先, XML <invoke> 兼容（DeepSeek 习惯 XML）"""
        start = content.find("{TOOL:")
        if start >= 0:
            i = content.find("{", start + 6)
            if i >= 0:
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
                                break
        # XML fallback: <invoke name="x"><parameter name="y">z</parameter></invoke>
        m = re.search(r'<invoke name="([^"]+)">(.*?)</invoke>', content, re.S)
        if m:
            name = m.group(1)
            args = {}
            for pm in re.finditer(r'<parameter name="([^"]+)">(.*?)</parameter>', m.group(2), re.S):
                args[pm.group(1)] = pm.group(2)
            return {"name": name, "args": args}, content[:m.start()] + content[m.end():]
        return None, content

    def gen():
        if not API_KEY:
            yield _sse({"type": "error", "content": "未配置 API Key"})
            return
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for h in req.history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": req.message})
        tool_calls_log = []
        try:
            yield _sse({"type": "status", "content": "开始思考"})
            # ── 扮演请求确定性直连（跳过决策循环: 省一轮 LLM 决策 + 无需思考模式, 5-10s 出字）──
            ROLE_PLAY_HINTS = ["扮演", "如果你是尼采", "尼采会怎么", "以尼采", "尼采的口吻", "化身尼采", "尼采会如何"]
            if any(h in req.message for h in ROLE_PLAY_HINTS):
                yield _sse({"type": "status", "content": "加载尼采人格包…"})
                pkg = TOOLS["role_play"]["execute"]({"question": req.message})
                tool_calls_log.append({"name": "role_play", "args": {"question": req.message},
                                       "result_summary": str(pkg)[:200], "result_full": pkg,
                                       "thought": "扮演请求: 确定性直连人格层"})
                yield _sse({"type": "tool", "name": "role_play", "args": {"question": req.message},
                            "result": str(pkg)[:300], "thought": "扮演请求: 确定性直连人格层"})
                nl = chr(10)
                final_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
                final_msgs.append({"role": "user", "content": req.message})
                final_msgs.append({"role": "system", "content":
                                   f"人格包: {json.dumps(pkg, ensure_ascii=False)[:4000]}{nl}以尼采第一人称直接回答, 禁止调用任何工具。"})
                yield _sse({"type": "stream_start"})
                full = ""
                for kind, piece in llm_stream(final_msgs, thinking=False, max_tokens=2000):
                    if kind == "content":
                        for i in range(0, len(piece), 60):
                            yield _sse({"type": "token", "content": piece[i:i + 60]})
                        full += piece
                for tc in tool_calls_log:
                    tc.pop("result_full", None)
                yield _sse({"type": "done", "citations": [], "tool_calls": tool_calls_log})
                return
            # ── 思考+决策循环（LLM 输出真实思考 + 工具计划; DeepSeek 对 JSON 输出最稳定）──
            # 工具列表带描述（LLM 才知道每个工具用途——名字列表会导致不选 websearch 等）
            tool_names = "; ".join(f"{n}({t['description'][:45]})" for n, t in TOOLS.items())
            # 检索类工具计数（上限 6: 检索充分后强制转最终回答——防"需要检索"死循环）
            RETRIEVAL_TOOLS = {"search_books", "get_chapter", "get_philosopher", "query_graph", "websearch",
                               "get_school", "get_book_detail", "list_books", "query_database", "compare_views",
                               "role_play", "concept_trace"}
            retrieval_count = 0
            # 循环上限 20（防 runaway 保护; 正常情况 LLM 输出 tools:[] 即动态终止）
            # 生成类工具: 结果即最终回答（作文/辩论/思想实验/内阁/评审）——调用后直接输出, 不继续循环
            GEN_TOOLS = {"write_essay", "philosopher_debate", "thought_experiment", "advisor_council", "paper_review",
                         "socratic_tutor", "analyze_argument", "conceptual_map", "profile"}
            generated_reply = None
            last_tool_sig = None
            stuck_count = 0
            # ══ 流式 ReAct 循环（Claude Code 风格: 思考实时流出 → 工具并行 → 答案流式）══
            full = ""
            for step in range(8):
                # 检索次数已达上限 → 强制停止检索, 本轮直接产出最终回答（确定性纪律, 不依赖 LLM 自律）
                if retrieval_count >= 3 and step > 0:
                    messages.append({"role": "system",
                                     "content": "（检索次数已达上限。现在禁止再调用任何工具, 请直接基于已有材料输出最终回答。）"})
                pending_tools = []
                tool_buf = ""
                raw_content = ""
                for kind, piece in llm_stream(messages, thinking=True, max_tokens=4000):
                    if kind == "reasoning":
                        # 思维链分片节流（API 常整段返回, 拆小片前端呈逐字流动）
                        for i in range(0, len(piece), 40):
                            yield _sse({"type": "thought_stream", "content": piece[i:i + 40]})
                            time.sleep(0.02)
                    else:
                        raw_content += piece
                        # 流式提取 {TOOL:...}（括号平衡）; 非工具文本实时转发
                        tool_buf += piece
                        flushed = ""
                        while True:
                            s = tool_buf.find("{TOOL:")
                            if s < 0:
                                flushed += tool_buf
                                tool_buf = ""
                                break
                            flushed += tool_buf[:s]
                            depth = 0
                            end = -1
                            for idx in range(s, len(tool_buf)):
                                if tool_buf[idx] == "{":
                                    depth += 1
                                elif tool_buf[idx] == "}":
                                    depth -= 1
                                    if depth == 0:
                                        end = idx
                                        break
                            if end < 0:
                                tool_buf = tool_buf[s:]
                                break
                            try:
                                call = json.loads(tool_buf[s + 6:end])
                                pending_tools.append({"name": call.get("name", ""), "args": call.get("args", {})})
                            except Exception:
                                pass
                            tool_buf = tool_buf[end + 1:]
                        if flushed:
                            full += flushed
                            yield _sse({"type": "token", "content": flushed})
                if raw_content.strip():
                    messages.append({"role": "assistant", "content": raw_content})
                # XML 工具调用兜底（跨块累积后完整出现才提取）
                if not pending_tools:
                    m = re.search(r'<invoke name="([^"]+)">(.*?)</invoke>', raw_content, re.S)
                    if m:
                        xml_args = {}
                        for pm in re.finditer(r'<parameter name="([^"]+)">(.*?)</parameter>', m.group(2), re.S):
                            xml_args[pm.group(1)] = pm.group(2)
                        pending_tools.append({"name": m.group(1), "args": xml_args})
                if not pending_tools:
                    break  # 无工具调用 → 本轮内容即最终答案（已实时输出）
                # 卡死检测: 连续 3 轮相同工具签名 → 停止
                sig = json.dumps([{"name": t["name"], "args": t["args"]} for t in pending_tools[:2]], ensure_ascii=False)
                if sig == last_tool_sig:
                    stuck_count += 1
                    if stuck_count >= 3:
                        break
                else:
                    stuck_count = 0
                last_tool_sig = sig
                # ══ 多工具并行执行（ThreadPoolExecutor, 最多 3 并发）══
                for tc in pending_tools[:3]:
                    if tc["name"] in RETRIEVAL_TOOLS:
                        retrieval_count += 1
                def _run_one(tc):
                    nm = tc["name"]
                    tool = TOOLS.get(nm)
                    try:
                        return nm, tc["args"], (tool["execute"](tc["args"]) if tool else {"error": f"未知工具 {nm}"})
                    except Exception as e:
                        return nm, tc["args"], {"error": str(e)}
                exec_results = []
                with ThreadPoolExecutor(max_workers=3) as ex:
                    for nm, ag, res in ex.map(_run_one, pending_tools[:3]):
                        exec_results.append((nm, ag, res))
                for nm, ag, res in exec_results:
                    # search_books 结果空 → 自动 websearch 补
                    if nm == "search_books" and isinstance(res, dict) and not res.get("results"):
                        ws = TOOLS["websearch"]["execute"]({"query": ag.get("query", "")[:80]})
                        tool_calls_log.append({"name": "websearch", "args": {"query": ag.get("query", "")[:80]},
                                               "result_summary": str(ws)[:200], "result_full": ws,
                                               "thought": "原典库检索不足, 自动上网搜索补充"})
                        yield _sse({"type": "tool", "name": "websearch", "args": {"query": ag.get("query", "")[:80]},
                                    "result": str(ws)[:300], "thought": "原典库检索不足, 自动上网搜索补充"})
                        nlw = chr(10)
                        messages.append({"role": "system",
                                         "content": f"websearch 返回: {json.dumps(ws, ensure_ascii=False)[:4000]}{nlw}（网络搜索结果, 用于补充原典库）"})
                    tool_calls_log.append({"name": nm, "args": ag,
                                           "result_summary": str(res)[:200], "result_full": res,
                                           "thought": f"并行执行 {nm}"})
                    yield _sse({"type": "tool", "name": nm, "args": ag,
                                "result": str(res)[:300], "thought": f"并行执行 {nm}"})
                    nl6 = chr(10)
                    _retry_note = "材料已到手, 不要重复检索同类信息; 基于现有材料继续作答。" if nm in RETRIEVAL_TOOLS else ""
                    messages.append({"role": "system",
                                     "content": f"工具「{nm}」返回: {json.dumps(res, ensure_ascii=False)[:4000]}{nl6}（以上是工具结果, 用于回答用户问题。{_retry_note}）"})
                    if nm == "role_play":
                        messages.append({"role": "system",
                                         "content": "（人格包已加载。现在请以尼采第一人称直接撰写回答, 禁止再次调用 role_play 或任何其他工具。）"})
                    # 生成类工具: 结果即回答 → 提取后终止
                    if nm in GEN_TOOLS:
                        if isinstance(res, dict):
                            nljoin = chr(10)
                            generated_reply = (res.get("essay") or res.get("advice") or res.get("review")
                                               or res.get("experiment") or res.get("analysis")
                                               or res.get("socratic") or res.get("profile_text")
                                               or nljoin.join(res.get("debate", [])) or None)
                            if not generated_reply and res.get("map_text"):
                                generated_reply = f"```mermaid{nljoin}{res['map_text']}{nljoin}```"
                            _img_url = res.get("image_url")
                            if _img_url:
                                generated_reply = f"{generated_reply or ''}{nljoin}{nljoin}![概念图]({_img_url})"
                        if generated_reply:
                            break
                if generated_reply:
                    break
            # 外部信息词自动 websearch（高考标准/政策/最新等——LLM 不自律时后端兜底）
            EXTERNAL_HINTS = ["高考", "评分标准", "评分细则", "最新", "政策", "规定", "2025", "2026", "教育部", "标准", "要求", "细则"]
            if any(h in req.message for h in EXTERNAL_HINTS) and not any(t["name"] == "websearch" for t in tool_calls_log):
                ws_q = req.message[:80]
                ws = TOOLS["websearch"]["execute"]({"query": ws_q})
                tool_calls_log.append({"name": "websearch", "args": {"query": ws_q},
                                       "result_summary": str(ws)[:200], "result_full": ws,
                                       "thought": "涉及外部标准/政策信息, 自动上网搜索"})
                yield _sse({"type": "tool", "name": "websearch", "args": {"query": ws_q},
                            "result": str(ws)[:300], "thought": "涉及外部标准/政策信息, 自动上网搜索"})
                nlw = chr(10)
                messages.append({"role": "system",
                                 "content": f"websearch 返回: {json.dumps(ws, ensure_ascii=False)[:4000]}{nlw}（网络搜索结果, 补充外部标准/政策信息）"})
            # 防幻觉兜底（未检索且无工具调用; 扮演/生成类场景除外）
            if (not any(t["name"] in ("search_books", "get_chapter") for t in tool_calls_log)
                    and not any(t["name"] == "role_play" for t in tool_calls_log)
                    and not generated_reply
                    and len(req.message) >= 4):
                query = re.sub(r"[？?！!。，,、\s]+", " ", req.message)[:50]
                result = TOOLS["search_books"]["execute"]({"query": query, "limit": 5})
                tool_calls_log.append({"name": "search_books", "args": {"query": query},
                                       "result_summary": str(result)[:200], "result_full": result,
                                       "thought": "概念题自动检索原典"})
                yield _sse({"type": "tool", "name": "search_books", "args": {"query": query},
                            "result": str(result)[:300], "thought": "概念题自动检索原典"})
                nl5 = chr(10)
                messages.append({"role": "system",
                                 "content": f"系统检索「{query}」结果: {json.dumps(result, ensure_ascii=False)[:4000]}{nl5}请基于检索到的原典回答。"})
                for kind, piece in llm_stream(messages, thinking=False, max_tokens=3000):
                    if kind == "content":
                        for i in range(0, len(piece), 60):
                            yield _sse({"type": "token", "content": piece[i:i + 60]})
                            time.sleep(0.01)
                        full += piece
            # 生成类工具结果即回答（一次性分块输出, 不再 LLM 生成）
            if generated_reply:
                for chunk in [generated_reply[i:i + 120] for i in range(0, len(generated_reply), 120)]:
                    yield _sse({"type": "token", "content": chunk})
                full = generated_reply
                gen_citations = []
                for tc in tool_calls_log:
                    if tc.get("result_full") and isinstance(tc["result_full"], dict):
                        for item in tc["result_full"].get("results", [])[:3]:
                            gen_citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                                  "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
                    tc.pop("result_full", None)
                yield _sse({"type": "done", "citations": gen_citations, "tool_calls": tool_calls_log})
                return

            full = re.sub(r"<tool_calls>.*?</tool_calls>", "", full, flags=re.S).strip()
            citations = []
            for tc in tool_calls_log:
                if tc["name"] == "search_books" and tc.get("result_full"):
                    for item in tc["result_full"].get("results", [])[:3]:
                        citations.append({"book": item.get("book_title"), "chapter": item.get("chapter_title"),
                                          "book_id": item.get("book_id"), "chapter_idx": item.get("chapter_idx")})
                tc.pop("result_full", None)
            yield _sse({"type": "done", "citations": citations, "tool_calls": tool_calls_log})
        except Exception as e:
            yield _sse({"type": "error", "content": f"智能体出错: {e}"})
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ── 工具 17: websearch（Wikipedia 中文——免费无需 key, 上网补充）──
def _exec_websearch(args):
    """联网搜索: Bing 优先（中文结果+真实链接, 国内可达）→ 英文维基 → 中文维基"""
    query = args.get("query", "")
    if not query:
        return {"error": "缺少查询词"}
    import urllib.parse
    import re as _re
    import html as _html

    def _clean(s):
        return _html.unescape(_re.sub(r"<[^>]+>", "", s or "")).strip()

    # ① Bing 网页搜索（b_algo 结果块解析）
    try:
        q = urllib.parse.quote(query)
        req = urllib.request.Request(f"https://cn.bing.com/search?q={q}", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "zh-CN,zh;q=0.9"})
        with urllib.request.urlopen(req, timeout=15) as r:
            html_content = r.read().decode("utf-8", errors="ignore")
        out = []
        for b in _re.findall(r'<li class="b_algo".*?</li>', html_content, _re.DOTALL)[:5]:
            m = _re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', b, _re.DOTALL)
            if not m:
                continue
            url = m.group(1)
            title = _clean(m.group(2))
            p = _re.search(r'<p[^>]*>(.*?)</p>', b, _re.DOTALL)
            snippet = _clean(p.group(1))[:500] if p else ""
            if title and url.startswith("http"):
                out.append({"title": title, "snippet": snippet, "url": url})
        if out:
            return {"results": out, "query": query, "source": "bing"}
    except Exception:
        pass
    # ② 英文维基百科（API, 结构化）
    try:
        url = ("https://en.wikipedia.org/w/api.php?action=query&list=search"
               f"&srsearch={urllib.parse.quote(query)}&format=json&srlimit=4")
        with urllib.request.urlopen(url, timeout=12) as r:
            d = json.loads(r.read().decode())
        titles = [it["title"] for it in d.get("query", {}).get("search", [])]
        if titles:
            out = [{"title": t, "snippet": "",
                    "url": f"https://en.wikipedia.org/wiki/{urllib.parse.quote(t.replace(' ', '_'))}"}
                   for t in titles[:4]]
            return {"results": out, "query": query, "source": "en.wikipedia.org"}
    except Exception:
        pass
    # ③ 中文维基百科（API）
    try:
        url = ("https://zh.wikipedia.org/w/api.php?action=query&list=search"
               f"&srsearch={urllib.parse.quote(query)}&format=json&srlimit=3")
        with urllib.request.urlopen(url, timeout=12) as r:
            d = json.loads(r.read().decode())
        titles = [it["title"] for it in d.get("query", {}).get("search", [])]
        if titles:
            out = [{"title": t, "snippet": "",
                    "url": f"https://zh.wikipedia.org/wiki/{urllib.parse.quote(t)}"}
                   for t in titles[:3]]
            return {"results": out, "query": query, "source": "zh.wikipedia.org"}
    except Exception:
        pass
    return {"results": [], "query": query, "note": "联网无结果（Bing 与维基百科均不可达）"}

register_tool(
    "websearch",
    "上网搜索（维基百科中文, 含摘要）。用于补充原典库之外的信息: 外部标准/政策/最新研究/现代评论/词条解释。",
    {"type": "object", "properties": {"query": {"type": "string", "description": "搜索词"}}, "required": ["query"]},
    _exec_websearch,
)

# ── 工具 18: query_database（通用数据库查询）──
def _exec_query_db(args):
    table = args.get("table", "")
    key = args.get("key", "")
    limit = min(int(args.get("limit", 5)), 10)
    if table == "books":
        data = get_books()
        hits = [b for b in data if (not key or key in f"{b.get('title','')} {b.get('author','')}")]
        return {"results": [{"title": b.get("title"), "author": b.get("author"), "region": b.get("region"),
                             "file_type": b.get("file_type"), "chapterCount": b.get("chapterCount"),
                             "rank": b.get("rank"), "summary": (b.get("summary") or "")[:200]} for b in hits[:limit]],
                "total": len(hits), "table": table}
    if table == "philosophers":
        phils = get_philosophers()
        entries = phils if isinstance(phils, dict) else phils
        hits = []
        for k, v in (entries.items() if isinstance(entries, dict) else [(e.get("name"), e) for e in entries]):
            if not key or key in k:
                hits.append({"name": k, **({kk: vv for kk, vv in v.items() if kk in ("period", "century", "school", "region")} if isinstance(v, dict) else {})})
        return {"results": hits[:limit], "total": len(hits), "table": table}
    if table == "network":
        net = get_network()
        hits = [{"name": k, "connections": len(v.get("connections", []))} for k, v in net.items() if not key or key in k]
        return {"results": hits[:limit], "total": len(hits), "table": table}
    if table == "schools":
        import os as _os
        sd = PUBLIC / "schools" / "data"
        hits = []
        if sd.exists():
            for f in _os.listdir(sd):
                if f.endswith(".json"):
                    try:
                        d = json.load(open(sd / f, encoding="utf-8"))
                        if not key or key in d.get("name", ""):
                            hits.append({"name": d.get("name"), "region": d.get("region", ""),
                                         "overview": (d.get("overview") or "")[:150]})
                    except Exception:
                        pass
        return {"results": hits[:limit], "total": len(hits), "table": table}
    return {"error": f"未知表 {table}", "tables": ["books", "philosophers", "network", "schools"]}

register_tool(
    "query_database",
    "通用数据库查询: books（书籍）/ philosophers（哲学家）/ network（星丛）/ schools（流派）。按关键词过滤。",
    {"type": "object", "properties": {"table": {"type": "string", "enum": ["books", "philosophers", "network", "schools"]}, "key": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["table"]},
    _exec_query_db,
)

# ═══════════════════════════════════════════════════════
# 工具 19: role_play（扮演——人格/记忆层: AIAuthor 数字作者数据）
# 数据源: PhiAgent/data/ai_author/（AIAuthor 六大库镜像: persona 模型 + 时期快照
#         + 风格词库 + 矛盾规则 + 564 条五维记忆 + 野史轶事）
# ═══════════════════════════════════════════════════════
AI_DIR = BASE.parent / "data" / "ai_author"
_persona_bundle = None
_persona_lock = threading.Lock()

def _load_persona_bundle():
    """加载尼采人格包（带缓存, 缺文件容错）"""
    global _persona_bundle
    if _persona_bundle is None:
        with _persona_lock:
            if _persona_bundle is None:
                b = {}
                for key, rel in {
                    "persona": "persona/persona_model.json",
                    "snapshots": "persona/persona_snapshots.json",
                    "style": "persona/style_lexicon.json",
                    "rules": "persona/contradiction_rules.json",
                    "memories": "memory/nietzsche_memories.json",
                    "anecdotes": "memory/anecdotes.json",
                }.items():
                    p = AI_DIR / rel
                    if p.exists():
                        try:
                            b[key] = json.load(open(p, encoding="utf-8"))
                        except Exception:
                            b[key] = {}
                _persona_bundle = b
    return _persona_bundle

def _recall_memories(query, limit=6):
    """记忆召回: 字符 bigram 重叠计分（event 字段加权 2×, significance/description 1×）"""
    bundle = _load_persona_bundle()
    memories = bundle.get("memories", {}).get("memories", [])
    q = (query or "").replace(" ", "").strip()
    if len(q) < 2 or not memories:
        return memories[:limit]
    def grams(t):
        t = t.replace(" ", "")
        return {t[i:i + 2] for i in range(len(t) - 1)}
    qg = grams(q)
    scored = []
    for m in memories:
        event = str(m.get("event", ""))
        sig = str(m.get("significance", ""))
        desc = str(m.get("description", ""))
        s = len(grams(event) & qg) * 2 + len(grams(sig) & qg) + len(grams(desc) & qg)
        if s > 0:
            scored.append((s, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored[:limit]] or memories[:limit]

def _exec_role_play(args):
    name = (args.get("philosopher") or args.get("persona") or args.get("name") or "").strip()
    if name and "尼采" not in name:
        return {"error": f"人格层暂未覆盖「{name}」（当前仅尼采, 数据来自 AIAuthor 数字作者系统）",
                "hint": "可改用 get_philosopher 查资料 / query_graph 查思想关联"}
    query = (args.get("question") or args.get("topic") or args.get("query") or "").strip()[:80]
    bundle = _load_persona_bundle()
    persona = bundle.get("persona", {})
    snapshots = bundle.get("snapshots", {})
    style = bundle.get("style", {})
    rules = bundle.get("rules", {})
    # 时期快照: 未指定时期 → 晚期成熟尼采（1883-1888）; fallback 仅是指示字段
    late = ((snapshots.get("snapshots") or {}).get("late") or {}) if isinstance(snapshots.get("snapshots"), dict) else {}
    snap = late or snapshots.get("fallback", {})
    memories = _recall_memories(query, 6)
    anecdotes = (bundle.get("anecdotes", {}).get("memories", []) or [])[:2]
    # 精简组装（工具结果注入 LLM 上下文截断 4000 字符, 优先保人格核心）
    reasoning = persona.get("reasoning_rules", {})
    reasoning_rules = reasoning.get("rules", []) if isinstance(reasoning, dict) else []
    style_model = persona.get("style_model", {})
    style_pref = ""
    if isinstance(style_model, dict):
        style_pref = (f"形式偏好: {json.dumps(style_model.get('形式偏好', {}), ensure_ascii=False)}; "
                      f"核心修辞: {json.dumps((style_model.get('核心修辞') or [])[:4], ensure_ascii=False)}")[:300]
    glossary = persona.get("concept_glossary", {})
    glossary_entries = (glossary.get("entries", []) if isinstance(glossary, dict) else [])[:3]
    constraints = ((persona.get("output_constraints") or {}).get("constraints", [])) if isinstance(persona.get("output_constraints"), dict) else []
    values = ((persona.get("value_model") or {}).get("values", {})) if isinstance(persona.get("value_model"), dict) else {}
    return {
        "role": "扮演人格包（弗里德里希·尼采）",
        "instruction": ("用户要求以尼采第一人称回答。以下人格包来自 AIAuthor 数字作者系统（23 本语料+图谱 v7+564 条记忆构建）。"
                        "必须: ①以'我'自称, 以尼采口吻与世界观作答; ②遵守输出约束（知识边界, 引用须诚实）; ③风格贴近 style 要点; "
                        "④可调用 memories 真实生平记忆作支撑; ⑤超范围问题以尼采的批判态度回应, 不编造事实。"),
        "identity": ((persona.get("meta") or {}).get("description") or "")[:400],
        "values": [{"v": k, "w": v} for k, v in list(values.items())[:8]],
        "reasoning_rules": [{"id": r.get("id"), "trigger": r.get("trigger"), "path": (r.get("path") or "")[:120]}
                            for r in reasoning_rules[:3]],
        "output_constraints": [{"rule": c.get("rule"), "detail": (c.get("detail") or "")[:80]} for c in constraints[:6]],
        "emotion_baseline": json.dumps((persona.get("emotional_model") or {}).get("baseline", {}), ensure_ascii=False)[:300],
        "style": style_pref,
        "concept_anchors": [{"term": e.get("term"), "canon": (e.get("canon") or "")[:80]} for e in glossary_entries],
        "period": {"name": snap.get("name"), "range": snap.get("range"), "age": snap.get("age"),
                   "identity": (snap.get("identity") or "")[:100], "dimensions": snap.get("dimensions"),
                   "signature": (snap.get("signature") or "")[:150],
                   "speech_markers": (snap.get("speech_markers") or [])[:5]},
        "contradiction_rules": [{"id": r.get("id"), "conflict": r.get("conflict")} for r in (rules.get("rules") or [])[:3]],
        "memories": [{"type": m.get("type"), "event": m.get("event"), "year": m.get("year"),
                      "period": m.get("period"), "significance": (m.get("significance") or "")[:80]} for m in memories],
        "anecdotes": [{"event": (m.get("event") or "")[:120], "credibility": m.get("credibility")} for m in anecdotes],
    }

register_tool(
    "role_play",
    "扮演哲学家（人格层）——以尼采第一人称回答。persona/记忆来自 AIAuthor 数字作者系统, 自动召回相关生平记忆。触发: 用户要求'扮演尼采/如果你是尼采/尼采会怎么看/以尼采的口吻'。",
    {"type": "object", "properties": {"philosopher": {"type": "string", "description": "哲学家名（当前人格层仅覆盖尼采）"}, "question": {"type": "string", "description": "用户的问题/话题"}}, "required": ["question"]},
    _exec_role_play,
)

# ═══════════════════════════════════════════════════════
# LangGraph 引擎路由（v2）: /api/agent/stream_lg
# Claude Code 风格: 思考 → 工具（并行）→ 最终回答; 前端协议不变
# ═══════════════════════════════════════════════════════
@router.post("/api/agent/stream_lg")
async def agent_stream_lg(req: AgentChatRequest, authorization: str = Header(None),
                          _g: dict = Depends(guard.agent_guard)):
    async def gen():
        import engine_langgraph as elg
        if not API_KEY:
            yield _sse({"type": "error", "content": "未配置 API Key"})
            return
        # 语言偏好: 请求体（前端 localStorage）优先, 登录用户以 profile.language 为准
        custom = None
        language = req.language if req.language in ("zh", "en") else "zh"
        if authorization and authorization.startswith("Bearer "):
            try:
                from auth import get_user_by_token, get_profile
                user = get_user_by_token(authorization[7:])
                if user:
                    prof = get_profile(user["id"])
                    custom = prof.get("custom_instructions")
                    if prof.get("language") in ("zh", "en"):
                        language = prof["language"]
            except Exception:
                pass
        async for ev in elg.stream_agent(req.message, req.history or [], req.agent or "general", custom, language):
            yield _sse(ev)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

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

    def _norm(s):
        # 书名归一化: 去《》/括号(全角转半角后剥除)/去空白 (AI 引用全半角不定;
        # 书名"从《理想国》到《正义论》"剥《》后无括号, 输入"(理想国)"带半角括号须同样剥除)
        return (s or "").replace("《", "").replace("》", "").replace("（", "(").replace("）", ")").replace("(", "").replace(")", "").replace(" ", "").strip()

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
    cname = (chapter or "").strip()
    idx = -1
    hit_title = ""
    base = cname.split("·")[0].strip() if cname else ""
    part_fb = -1  # part(编/卷)标题命中时的兜底: part 后第一个可索引章节
    for pos, t in enumerate(toc):
        if isinstance(t, dict) and t.get("type") == "part":
            title = t.get("title")
            if title and cname and (cname in title or title in cname or (base and base in title)) and part_fb < 0:
                for t2 in toc[pos + 1:]:
                    if not (isinstance(t2, dict) and t2.get("type") == "part"):
                        part_fb = t2.get("index", 0) if isinstance(t2, dict) else toc.index(t2)
                        break
            continue  # 编/卷分组标题不可索引（无块文件）
        title = t.get("title") if isinstance(t, dict) else t
        if cname and (cname in title or title in cname or (base and base in title)):
            # 层级 toc: 块 index 是条目自带 index（数组位置 ≠ 块序号, part 占位会错位）
            idx = t.get("index", 0) if isinstance(t, dict) else toc.index(t)
            hit_title = title
            break
    if idx < 0 and part_fb >= 0:
        idx = part_fb
        hit_title = f"{cname}（首章）"
    if idx < 0:
        idx = 0
        hit_title = toc[0].get("title") if isinstance(toc[0], dict) else toc[0]
    ch = read_chapter(hit["id"], idx)
    return {"book_id": hit["id"], "book": hit["title"], "author": hit.get("author", ""),
            "chapter": hit_title, "chapter_idx": idx,
            "text": (ch.get("text") or "")[:2500] if ch else ""}

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
    deep_speech = ""
    try:
        from engine_langgraph import get_system_prompt
        r = TOOLS["search_books"]["execute"]({"query": topic[:50], "limit": 4})
        mat = json.dumps(r, ensure_ascii=False)[:2500]
        r1 = llm_chat([{"role": "system", "content": get_system_prompt("general")},
                       {"role": "user", "content": f"议题: 「{topic}」。基于以下检索材料给出你的分析立场（250字内, 引用标注出处）:\n{mat}"}],
                      temperature=0.7, max_tokens=600)
        deep_speech = (r1["choices"][0]["message"].get("content") or "").strip()
    except Exception as e:
        deep_speech = f"（深哲发言失败: {e}）"
    # ② 尼采发言（人格视角）
    nietzsche_speech = ""
    try:
        import agents as agents_mod
        r2 = llm_chat([{"role": "system", "content": agents_mod.AGENT_PROMPTS.get("nietzsche", "")},
                       {"role": "user", "content": f"议题: 「{topic}」。以你的人格回应（250字内, 格言式, 不贴出处标注）"}],
                      temperature=0.85, max_tokens=600)
        nietzsche_speech = (r2["choices"][0]["message"].get("content") or "").strip()
    except Exception as e:
        nietzsche_speech = f"（尼采发言失败: {e}）"
    # ③ 综合（第三方视角的交汇与分歧）
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

# ═══════════════════════════════════════════════════════
# 工具清单程序化生成（2026-08-14: 消除手写清单漂移——曾"23 个" vs 注册表 30 个）
# ═══════════════════════════════════════════════════════
_SYS_TOOL_LIST = "\n".join(f"- {n}: {TOOLS[n]['description'][:90]}" for n in TOOLS)
SYSTEM_PROMPT = SYSTEM_PROMPT.replace(
    "## 可用工具\n（工具清单由 TOOLS 注册表在模块加载时自动生成, 见文件末尾——不再手写, 防清单漂移）",
    f"## 可用工具（{len(TOOLS)} 个）\n{_SYS_TOOL_LIST}\n- 读操作工具无副作用，可放心调用。")
