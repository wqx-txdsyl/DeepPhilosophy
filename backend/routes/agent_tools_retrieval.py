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
                    results.append({
                        "book_id": it["bid"], "book_title": b.get("title") if b else it["bid"],
                        "author": b.get("author", "") if b else "",
                        "chapter_idx": it["idx"], "chapter_title": ch.get("title", ""),
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
            "snippet": snippet, "score": score,
        })
    return {"results": clean[:limit * 3], "query": query, "method": "lexical",
            "degraded_reason": _embed_status.get("degraded_reason") or "embedding_unavailable"}

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
    idx = _int_arg(args, "chapter_idx", 0, 0)
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
