# -*- coding: utf-8 -*-
"""检索工具域——agent 拆分模块 3/6（R2-2/S21, 2026-08-18 复审）

工具: search_books / get_book_detail / get_chapter / query_graph / get_philosopher /
list_books / get_school / concept_trace / websearch / query_database（10 个）。
代码从 routes/agent.py 原样搬移（不改逻辑）; 注册到 agent_core.TOOLS（import 本模块即注册）。
"""
import json, os, re, time, urllib.request, threading

from routes.agent_core import (
    TOOLS, register_tool, _int_arg,
    get_books, get_network, get_philosophers, book_by_id, chapter_meta, read_chapter,
    _book_chapter_texts, _load_vectors,
    PUBLIC, SCHOOLS_DIR,
)

# ── O6-Q1 §5: canonical 引用标签——由结果字段机械派生, 模型无需逆向 validator
# 的标注语法（无任何"应引用这个"类语义文案）。章节缺失时只给书级标签, 不发明位置。
def _cite_label(book_title, chapter_title):
    bt = (book_title or "").strip()
    ct = (chapter_title or "").strip()
    if not bt:
        return ""
    return f"【《{bt}》·{ct}】" if ct else f"【《{bt}》】"


# ── O7-B §14-17: 书目元数据 additive 暴露（work/edition/digital_source 三分离）──
# 数据源 = backend/data/book_bibliography.json（dp_biblio_build.py 产出, 仅 pilot 书）。
# 模型可见精简视图（verified/source_type/granularity）; 完整 provenance 留在数据层。
# 缺失字段保持 null——不生成「未知出版社/第?页」类占位文本（§16）。
_BIBLIO_PATH = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "data", "book_bibliography.json")
_biblio_cache = None

def _load_biblio():
    global _biblio_cache
    if _biblio_cache is None:
        try:
            with open(_BIBLIO_PATH, encoding="utf-8") as f:
                _biblio_cache = json.load(f).get("books", {})
        except FileNotFoundError:
            _biblio_cache = {}
    return _biblio_cache

def _biblio_payload(bid):
    """pilot 书 → 模型可见书目元数据（additive）; 非 pilot 书 → None（零改动）。"""
    rec = _load_biblio().get(bid)
    if not rec:
        return None
    ed, wk = rec.get("edition", {}), rec.get("work", {})
    return {
        "work": {"author": wk.get("author"),
                 "canonical_title": wk.get("canonical_title"),
                 "original_language": wk.get("original_language")},
        "edition": {"translator": ed.get("translator"),       # null = 未验证/未收录
                    "publisher": ed.get("publisher"),
                    "publication_year": ed.get("publication_year"),
                    "isbn": ed.get("isbn"),
                    "edition_identity": ed.get("edition_identity")},
        "citation_capability": rec.get("citation_capability"),
        "metadata_status": {
            "source_type": "embedded_front_matter",   # 数据层 Tier1（版权页/扉页内嵌于数字源）
            "verified_fields": [k for k, v in rec.get("field_provenance", {}).items()
                                if v.get("verified")],
            "note": "字段为 null 表示当前数字源未提供或未通过双重证据核验; 不得臆测补全"},
    }


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
    limit = _int_arg(args, "limit", 5, 1, 10)
    # 向量优先（索引就绪时）; 经 routes.agent 门面运行时取回 _embed_query——
    # 保持拆分前的 monkeypatch 契约（tests/test_agent.py 以 agent._embed_query 强制走关键词兜底路径）
    from routes.agent import _embed_query, _embed_status
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
                    _bt = b.get("title") if b else it["bid"]
                    _ct = ch.get("title", "")
                    results.append({
                        "book_id": it["bid"], "book_title": _bt,
                        "author": b.get("author", "") if b else "",
                        "chapter_idx": it["idx"], "chapter_title": _ct,
                        # O6-Q1 §5: canonical 引用标签（机械派生, 见 _cite_label）
                        "citation_label": _cite_label(_bt, _ct),
                        "snippet": text[:220].replace(chr(10), " "), "score": round(float(sims[ti]), 3),
                    })
                if results:
                    return {"results": results[:limit * 3], "query": query, "method": "vector"}
    # 关键词兜底（S6: embedding 不可用/熔断 → 词法检索; 记录 retrieval_mode 与 degraded_reason）
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
    # 2) 章级扫描（前 limit 本书的章节; S13: 走内存索引+文本缓存, 不再每请求逐章读 JSON）
    results = []
    for s, b in hits[:limit]:
        best = []
        for i, title, text in _book_chapter_texts(b["id"]):
            if not text:
                continue
            cs = _match_score(text[:2000] + title, terms)
            if cs > 0:
                best.append((s + cs, i, b, title, text))
        best.sort(key=lambda x: -x[0])
        results.extend(best[:3])
    results.sort(key=lambda x: -x[0])
    clean = []
    for score, i, b, title, text in results[:limit * 3]:
        # 提取命中片段
        pos = 0
        low = text.lower()
        for t in terms:
            p = low.find(t)
            if p >= 0:
                pos = p
                break
        snippet = text[max(0, pos - 80): pos + 180].replace("\n", " ")
        clean.append({
            "book_id": b["id"], "book_title": b.get("title"), "author": b.get("author"),
            "chapter_idx": i, "chapter_title": title,
            # O6-Q1 §5: canonical 引用标签（机械派生自本条结果的 书名/章节 字段）
            "citation_label": _cite_label(b.get("title"), title),
            "snippet": snippet, "score": score,
        })
    return {"results": clean[:limit * 3], "query": query, "method": "lexical",
            "degraded_reason": _embed_status.get("degraded_reason") or "embedding_unavailable"}

register_tool(
    "search_books",
    "在 403 本哲学原著中全文检索（书名/作者/章节内容关键词命中）。用于回答哲学问题时找原文依据、引言、概念出处。"
    "对于按格言号/节号/篇章编号组织的作品（如尼采《快乐的科学》、马基雅维利《君主论》），"
    "若检索结果无法直接定位编号，可先查询作品详情/目录确认章节结构再读取。",
    {"type": "object", "properties": {"query": {"type": "string", "description": "检索关键词（哲学概念/人名/书名/句子片段）"}, "limit": {"type": "integer", "description": "返回结果数上限"}}, "required": ["query"]},
    _exec_search_books,
)

# ── 工具 2: get_book_detail ──────────────────────────
def _resolve_book_by_name(name):
    """书名/作者模糊解析 → 最佳匹配 book 或 None。
    背景（2026-08-30）: 轻量模型（glm-4-flash）常无视"先搜后查"纪律, 直接把书名当
    book_id 传入——工具层自愈解析, 不依赖模型自觉, 对所有供应商模型生效。
    2026-09-01: "书名·篇名"变体回退（模型常传"论语·先进"式参数）——整体解析失败时
    取 ·/（ 前的主书名部分重试一次。"""
    name = (name or "").strip().strip("《》\"'“”　 ")
    if len(name) < 2:
        return None
    terms = [t for t in re.split(r"[\s,，。；;：:、]+", name) if len(t) >= 2] or [name]
    hits = []
    for b in get_books():
        hay = f"{b.get('title', '')} {b.get('author', '')}"
        s = _match_score(hay, terms)
        if s > 0:
            hits.append((s, b))
    if not hits:
        for sep in ("·", "（", "("):
            if sep in name:
                main = name.split(sep, 1)[0].strip()
                if len(main) >= 2:
                    alt = _resolve_book_by_name(main)
                    if alt:
                        return alt
        return None
    hits.sort(key=lambda x: -x[0])
    return hits[0][1]


def _exec_book_detail(args):
    bid = args.get("book_id", "")
    b = book_by_id(bid)
    if not b:
        alt = _resolve_book_by_name(bid)          # 书名宽容解析
        if alt:
            b, bid = alt, alt.get("id", bid)
    if not b:
        return {"error": f"未找到书籍 {bid}（提示: 先用 search_books 检索获取 book_id）"}
    meta = chapter_meta(bid)
    out = {"id": b.get("id"), "title": b.get("title"), "author": b.get("author"),
           "region": b.get("region"), "file_type": b.get("file_type"),
           "summary": b.get("summary", "")[:500], "rank": b.get("rank"),
           "chapterCount": meta.get("chapterCount", 0) if meta else 0,
           "toc": [t.get("title") if isinstance(t, dict) else t for t in (meta.get("toc") or [])][:30]}
    # O7-B: additive 书目元数据（pilot 书才有; 已有字段零改动）
    bib = _biblio_payload(b.get("id", bid))
    if bib:
        out["bibliographic_metadata"] = bib
    return out

register_tool(
    "get_book_detail",
    "获取一本书的详情（简介/作者/目录/章节数）。对于按格言号/节号/篇章编号组织的作品（如尼采《快乐的科学》、"
    "马基雅维利《君主论》），若检索结果无法直接定位编号，可先查询作品详情/目录确认章节结构再读取。",
    {"type": "object", "properties": {"book_id": {"type": "string", "description": "书名或 search_books 返回的 book_id"}}, "required": ["book_id"]},
    _exec_book_detail,
)

# ── 工具 3: get_chapter ──────────────────────────────
def _exec_chapter(args):
    bid = args.get("book_id", "")
    idx = _int_arg(args, "chapter_idx", 0, 0)
    ch = read_chapter(bid, idx)
    if not ch:
        alt = _resolve_book_by_name(bid)          # 书名宽容解析（同 get_book_detail）
        if alt:
            bid = alt.get("id", bid)
            ch = read_chapter(bid, idx)
    if not ch:
        return {"error": f"章节不存在 {bid}/{idx}（提示: 先用 search_books 检索获取 book_id）"}
    # O6-Q1 §5: canonical 引用标签——由读取结果的 书名/章节 机械派生
    # （置于 text 之前, 防 ToolMessage 截断丢失; 无语义文案）
    _b = book_by_id(bid) or {}
    _bt = _b.get("title") or bid
    out = {"book_id": bid, "chapter_idx": idx, "title": ch["title"],
           "book_title": _bt,
           "citation_label": _cite_label(_bt, ch["title"]),
           "text": ch["text"][:6000]}
    # O7-B: additive 书目元数据可见性（pilot 书; §16 缺失=null 不占位）
    bib = _biblio_payload(bid)
    if bib:
        out["bibliographic_metadata"] = bib
    return out

register_tool(
    "get_chapter",
    "读取某本书指定章节的全文（用于深入引用原文、分析论证）。出处/原话核验的必经步骤: "
    "search_books 只提供片段定位线索, 确认出处、措辞与上下文必须读取对应章节原文——"
    "检索命中候选后应读取该章再下结论, 不得仅凭检索片段或记忆给出原文引用。",
    {"type": "object", "properties": {"book_id": {"type": "string", "description": "书名或 search_books 返回的 book_id"}, "chapter_idx": {"type": "integer"}}, "required": ["book_id", "chapter_idx"]},
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

# ── 工具 9: get_school（哲学流派/谱系详情）──
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

# ── 工具 17: websearch（Wikipedia 中文——免费无需 key, 上网补充）──
def _exec_websearch(args):
    """联网搜索: Bing 优先（中文结果+真实链接, 国内可达）→ 英文维基 → 中文维基
    2026-08-14: 加 TTL 缓存（同 query 10 分钟内不重复联网, 防 Bing 反爬/重复抓取）"""
    query = args.get("query", "")
    if not query:
        return {"error": "缺少查询词"}
    qkey = query.strip()[:80]
    now = time.time()
    with _web_cache_lock:
        hit = _web_cache.get(qkey)
        if hit and now - hit[0] < _WEB_TTL:
            return hit[1]
    result = _websearch_inner(query)
    with _web_cache_lock:
        if len(_web_cache) > 200:   # 防无限增长
            for k in list(_web_cache.keys())[:100]:
                _web_cache.pop(k, None)
        _web_cache[qkey] = (time.time(), result)
    return result

_web_cache = {}
_web_cache_lock = threading.Lock()
_WEB_TTL = 600   # 10 分钟

def _websearch_inner(query):
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
    limit = _int_arg(args, "limit", 5, 1, 10)
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
# Phase T.1 (T1.1-B): 全库逐字定位（出处核验 search→read 升级的确定性原语）
#   - 不改 search_books 的向量/排序路径（DO NOT TOUCH: embedding/ranking 原样）
#   - 只服务于出处核验: 定位候选篇章 → get_chapter 读取原文 → 逐字核验
#   - 词法精确匹配（norm 连续包含）, 命中即真; 原典经典优先于研究汇编
# ═══════════════════════════════════════════════════════
_LOCATE_NORM_RE = re.compile(r"[^\w\u4e00-\u9fff]+")
# 经典原典书名（同为逐字命中时排序加权——「论语」应排在「南怀瑾经典合集」前面）
_CANONICAL_TITLES = {
    "论语", "孟子", "大学", "中庸", "老子", "道德经", "庄子", "周易", "易经",
    "诗经", "尚书", "礼记", "春秋", "左传", "荀子", "墨子", "韩非子", "管子",
    "理想国", "会饮篇", "斐多", "形而上学", "尼各马可伦理学", "忏悔录",
}
# 研究/汇编/合集体裁（命中优先级降低——它们只是转述或引用原典）
_LOCATE_PENALTY_RE = re.compile(
    r"合集|全集|套装|大全集|著作集|文集|文选|辞典|词典|简史|史|讲|课|教程|答案|"
    r"底层逻辑|进化论|导论|入门|读本|选读|漫话|图解|一本就懂|极简")

_locate_norm_cache = {}      # bid -> [(idx, ntext)]
_locate_cache_built = set()
_locate_lock = threading.Lock()


def _locate_norm(s):
    return _LOCATE_NORM_RE.sub("", s or "")


def _canon_score(book_title):
    t = (book_title or "").strip()
    score = 0
    if 0 < len(t) <= 6:
        score += 3
    if t in _CANONICAL_TITLES:
        score += 6
    if _LOCATE_PENALTY_RE.search(t):
        score -= 5
    return score


def _locate_passage(raw_text, term):
    """命中章内提取可读原文片段（行=章段单位优先; 长段落按句界取窗口）"""
    tn = _locate_norm(term)
    best_line = ""
    for ln in (raw_text or "").split("\n"):
        s = ln.strip()
        if not s:
            continue
        if term in s or (len(tn) >= 4 and tn in _locate_norm(s)):
            best_line = s
            break
    if not best_line:
        return ""
    if len(best_line) <= 360:
        return best_line
    pos = best_line.find(term)
    if pos < 0:
        pos = max(0, len(best_line) // 4)
    left = max(best_line.rfind("。", 0, pos), best_line.rfind("！", 0, pos),
               best_line.rfind("？", 0, pos), best_line.rfind("；", 0, pos))
    right = len(best_line)
    for punct in ("。", "！", "？", "；"):
        p = best_line.find(punct, pos + len(term) if pos >= 0 else 0)
        if 0 < p < right:
            right = p + 1
    return best_line[max(0, left + 1 if left >= 0 else 0):right].strip()[:360]


def locate_exact_phrase(term, prefer_title=None, max_hits=6):
    """全库逐字定位（T1.1-B; 同步函数——调用方放线程池）

    返回 {"term", "found", "prefer_found", "prefer_absent", "prefer_unreadable",
          "hits": [{book_id, book_title, author, chapter_idx, chapter_title,
                    passage, canonical}], "scanned_books"}
    - 词法连续包含（norm 后）, 不经 embedding; 进程级缓存 norm 文本（首扫 ~9s, 后续 ~0.2s）
    - prefer_title: 用户提到的《书》——优先在该书内定位; 明确不在时 prefer_absent=True
      （R4 类"是不是《X》里的"纠错的事实依据）; 该书文本不可读时 prefer_unreadable=True
    """
    t = (term or "").strip()
    tn = _locate_norm(t)
    out = {"term": t, "found": False, "prefer_found": None, "prefer_absent": False,
           "prefer_unreadable": False, "hits": [], "scanned_books": 0}
    if len(tn) < 2:
        return out
    books = get_books()
    by_title = {}
    for b in books:
        bt = (b.get("title") or "").replace("《", "").replace("》", "").strip()
        if bt and bt not in by_title:
            by_title[bt] = b
    prefer_book = None
    if prefer_title:
        pref_key = prefer_title.replace("《", "").replace("》", "").strip()
        prefer_book = by_title.get(pref_key) or by_title.get(_locate_norm(pref_key))
        if prefer_book is None:
            for bt, b in by_title.items():
                if pref_key and (pref_key in bt or bt in pref_key):
                    prefer_book = b
                    break

    def _scan_book(b):
        bid = b.get("id")
        if not bid:
            return []
        with _locate_lock:
            if bid not in _locate_cache_built:
                try:
                    _locate_norm_cache[bid] = [
                        (i, _locate_norm(text)) for i, _t, text in _book_chapter_texts(bid)]
                except Exception:
                    _locate_norm_cache[bid] = []
                _locate_cache_built.add(bid)
        norms = _locate_norm_cache.get(bid) or []
        hits = []
        for i, ntext in norms:
            if ntext and tn in ntext:
                # 命中才读原文（避免全库 raw 文本反复进出 LRU——实测 4s 抖动根因）
                ch = read_chapter(bid, i) or {}
                hits.append({"book_id": bid, "book_title": b.get("title") or "",
                             "author": b.get("author") or "", "chapter_idx": i,
                             "chapter_title": ch.get("title", ""),
                             "passage": _locate_passage(ch.get("text", ""), t),
                             "canonical": _canon_score(b.get("title"))})
        return hits

    hits = []
    # ① 用户提到的书优先（明确在该书内找不到 → prefer_absent, 纠错依据）
    if prefer_book is not None:
        out["scanned_books"] += 1
        ph = _scan_book(prefer_book)
        total_text = sum(len(x) for _i, x in _locate_norm_cache.get(prefer_book.get("id"), []))
        if total_text < 100:
            out["prefer_unreadable"] = True
        if ph:
            out["prefer_found"] = prefer_book.get("title")
            hits.extend(ph)
        else:
            out["prefer_absent"] = True
    # ② 全库扫描（命中按原典经典度排序; 稳定次序）
    for b in books:
        if prefer_book is not None and b.get("id") == prefer_book.get("id"):
            continue
        out["scanned_books"] += 1
        hits.extend(_scan_book(b))
    hits.sort(key=lambda h: -h["canonical"])
    out["hits"] = hits[:max_hits]
    out["found"] = bool(out["hits"])
    return out
