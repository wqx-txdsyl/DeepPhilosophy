# -*- coding: utf-8 -*-
"""哲学智能体核心共享层——agent 拆分模块 2/6（R2-2/S21, 2026-08-18 复审）

职责: 路径常量 / 数据加载（带缓存）/ 工具注册表（TOOLS）/ per-user 记忆槽 /
S13 检索索引与文本 LRU / embedding 缓存与向量索引。
全部代码从 routes/agent.py 原样搬移（不改逻辑），供各工具域模块与 agent.py 共用。
"""
import json, os, re, time, hashlib, threading
from collections import OrderedDict
from pathlib import Path

import guard

# ── 路径 ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent          # backend/
DATA = BASE / "data"
PUBLIC = BASE.parent / "app" / "public"                 # app/public
BOOKS_FILE = PUBLIC / "books.json"
CHAPTERS_DIR = DATA / "book_chapters"
NETWORK_FILE = PUBLIC / "philosopher_network.json"
PHILOSOPHERS_FILE = PUBLIC / "philosophers.json"
SCHOOLS_DIR = PUBLIC / "schools" / "data"               # 工具: get_school / query_database / school_arena
PHILOSOPHER_DIR = PUBLIC / "philosopher"                # 工具: generate_image 本地肖像参考图
AGNES_IMG_DIR = BASE.parent / "agent-app" / "public" / "agent_images"   # 工具: generate_image 输出目录
AI_DIR = BASE.parent / "data" / "ai_author"             # 工具: role_play（AIAuthor 人格包数据）

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

def _int_arg(args, key, default, lo=None, hi=None):
    """统一 int 解析（2026-08-14: LLM 传非数字/越界不再抛 ValueError 或产生怪结果）"""
    try:
        v = int(args.get(key, default))
    except (TypeError, ValueError):
        v = default
    if lo is not None and v < lo:
        v = lo
    if hi is not None and v > hi:
        v = hi
    return v

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

# ── S13: 检索索引 + 缓存（audit 2026-08-17）────────────────
# 关键词兜底原实现每请求: 读 meta.json + 逐章读 JSON（最多 300 文件/书）;
# embedding 每次外部 HTTP。改为:
#   _CHAPTER_INDEX  书 → 章节文件路径索引（惰性构建一次, 后续请求零磁盘扫描/meta 读取）
#   _CHAPTER_TEXTS  书 → [(idx, title, text)] LRU 文本缓存（128MB 上限, 淘汰最久未用书, 防长运行内存无限增长）
#   _EMBED_CACHE    query md5 → embedding 向量（外部 HTTP 结果按文本 hash 缓存）
_CHAPTER_INDEX = {}                     # bid -> {"chapterCount": n, "paths": [(idx, Path), ...]}
_CHAPTER_TEXTS = OrderedDict()          # bid -> [(idx, title, text), ...]
_CHAPTER_TEXTS_BYTES = 0
_CHAPTER_TEXTS_MAX = 128 * 1024 * 1024  # 128MB 文本缓存上限
_EMBED_CACHE = {}                       # md5(query) -> embedding
_INDEX_LOCK = threading.RLock()         # RLock: _book_chapter_texts 内会再调 _chapter_index
_EMBED_CACHE_MAX = 2048


def invalidate_agent_cache():
    """书库更新后失效进程内缓存（N6, audit 2026-08-18）:
    在 sync/upload、sync/delete、knowledge/init 成功后调用——否则 books.json /
    章节文本 LRU / query embedding / 向量索引会缓存到进程重启, 更新不生效。
    覆盖: 三个全量数据缓存（books/network/philosophers）、章节索引与文本 LRU、
    embedding 缓存与向量索引、book_scanner 列表缓存（300s TTL 兜底提前清）。
    不触碰 _tools_cache / _web_cache（工具集与网页缓存与书库内容无关）。"""
    global _books_cache, _network_cache, _philosophers_cache
    global _vectors, _vector_index
    global _CHAPTER_TEXTS_BYTES
    with _cache_lock:
        _books_cache = None
        _network_cache = None
        _philosophers_cache = None
    with _INDEX_LOCK:
        _CHAPTER_INDEX.clear()
        _CHAPTER_TEXTS.clear()
        _CHAPTER_TEXTS_BYTES = 0
        _EMBED_CACHE.clear()
        _vectors = None
        _vector_index = None
    try:  # book_scanner 进程内列表缓存（懒 import 防启动耦合; 用模块属性赋值才生效）
        import services.book_scanner as _bs
        _bs._BOOKS_CACHE_LIST = None
        _bs._BOOKS_CACHE_TIME = 0
    except Exception:
        pass


def _chapter_index(bid):
    """构建/取回 章节文件索引（惰性; 一次构建后复用, 不再每请求读 meta.json/扫目录）"""
    with _INDEX_LOCK:
        idx = _CHAPTER_INDEX.get(bid)
        if idx is not None:
            return idx
        meta = chapter_meta(bid)
        n = (meta or {}).get("chapterCount") or 0
        paths = []
        for i in range(min(n, 300)):
            p = CHAPTERS_DIR / bid / f"{i}.json"
            if p.exists():
                paths.append((i, p))
        idx = {"chapterCount": n, "paths": paths}
        _CHAPTER_INDEX[bid] = idx
        return idx


def _book_chapter_texts(bid):
    """按需加载章节文本 [(idx, title, text), ...]（LRU; 超 128MB 淘汰最久未用书）"""
    global _CHAPTER_TEXTS_BYTES
    with _INDEX_LOCK:
        cached = _CHAPTER_TEXTS.get(bid)
        if cached is not None:
            _CHAPTER_TEXTS.move_to_end(bid)
            return cached
        entries, size = [], 0
        for i, p in _chapter_index(bid)["paths"]:
            try:
                ch = json.load(open(p, encoding="utf-8"))
                title = ch.get("title", "")
                text = "\n".join(b.get("value", "") for b in ch.get("content", [])
                                 if b.get("type") == "text")
            except Exception:
                title, text = "", ""
            entries.append((i, title, text))
            size += len(text) * 2 + 128
        _CHAPTER_TEXTS[bid] = entries
        _CHAPTER_TEXTS_BYTES += size
        while _CHAPTER_TEXTS_BYTES > _CHAPTER_TEXTS_MAX and len(_CHAPTER_TEXTS) > 1:
            _old_bid, old = _CHAPTER_TEXTS.popitem(last=False)
            _CHAPTER_TEXTS_BYTES -= sum(len(t) * 2 + 128 for _, _, t in old)
        return entries


def _embed_query(q):
    key = hashlib.md5(q.encode("utf-8", "ignore")).hexdigest()
    cached = _EMBED_CACHE.get(key)
    if cached is not None:
        _embed_status["mode"] = "vector"
        _embed_status["degraded_reason"] = ""
        return cached
    # Phase S (S6): 限流熔断——429 双失败后打开 circuit breaker,
    # 冷却期内后续 embedding 调用不再撞同一限流 API, 直接走关键词/词法兜底。
    now = time.time()
    with _EMBED_CIRCUIT_LOCK:
        if _EMBED_CIRCUIT["open"]:
            if now - _EMBED_CIRCUIT["opened_at"] < _EMBED_CIRCUIT_COOLDOWN:
                _embed_status["mode"] = "lexical"
                _embed_status["degraded_reason"] = _EMBED_CIRCUIT["reason"]
                return None
            _EMBED_CIRCUIT["open"] = False     # 冷却期结束, 允许试探一次
    try:
        from openai import OpenAI
        # max_retries=0: 关闭 SDK 默认的 429 重试链（默认 2 次指数退避重试——正是
        # "429 多轮重试拖慢真实回答"的来源）。限流重试由本函数显式控制: 最多 1 次短退避。
        cli = OpenAI(api_key=os.environ.get("ZHIPU_API_KEY", ""),
                     base_url="https://open.bigmodel.cn/api/paas/v4/", timeout=15,
                     max_retries=0)
        try:
            r = cli.embeddings.create(model="embedding-2", input=[q[:500]])
        except Exception as e:
            if _is_rate_limit(e):
                # ① 首次 429 立即开闸（并发 search_books 在 gather 中共享熔断器——
                #    先开闸, 同轮其他查询直接跳过, 不再撞同一限流 API）
                with _EMBED_CIRCUIT_LOCK:
                    _EMBED_CIRCUIT["open"] = True
                    _EMBED_CIRCUIT["opened_at"] = time.time()
                    _EMBED_CIRCUIT["reason"] = "embedding_429_retry_exhausted"
                time.sleep(_EMBED_429_BACKOFF)     # ② 最多 1 次短退避重试
                r = cli.embeddings.create(model="embedding-2", input=[q[:500]])
                with _EMBED_CIRCUIT_LOCK:
                    _EMBED_CIRCUIT["open"] = False     # 重试成功 → 解除熔断（限流是瞬时的）
            else:
                raise
        vec = r.data[0].embedding
        if len(_EMBED_CACHE) > _EMBED_CACHE_MAX:  # S13: 缓存上限, 防长运行内存无限增长
            _EMBED_CACHE.clear()
        _EMBED_CACHE[key] = vec
        _embed_status["mode"] = "vector"
        _embed_status["degraded_reason"] = ""
        return vec
    except Exception as e:
        reason = "embedding_429_retry_exhausted" if _is_rate_limit(e) else "embedding_error"
        with _EMBED_CIRCUIT_LOCK:
            _EMBED_CIRCUIT["open"] = True
            _EMBED_CIRCUIT["opened_at"] = time.time()
            _EMBED_CIRCUIT["reason"] = reason
        _embed_status["mode"] = "lexical"
        _embed_status["degraded_reason"] = reason
        _log_embed_degraded(reason)
        return None

# ── S6: 请求级熔断 + 降级状态（进程级, 冷却期内全局生效）──
_EMBED_CIRCUIT = {"open": False, "opened_at": 0.0, "reason": ""}
_EMBED_CIRCUIT_LOCK = threading.Lock()
_EMBED_CIRCUIT_COOLDOWN = 120.0     # 冷却期: 熔断后 120s 内不再调用 embedding API
_EMBED_429_BACKOFF = 0.5            # 429 后单次短退避时长（秒）
_EMBED_LOG_FILE = DATA / "embedding_guard.jsonl"   # 运行时记录（gitignore）
_embed_status = {"mode": "vector", "degraded_reason": ""}   # 最近一次 embedding 状态（检索工具读取）


def _is_rate_limit(exc):
    """429 / 限流判定（openai SDK 异常带 status_code; 兜底文本匹配）"""
    sc = getattr(exc, "status_code", None)
    if sc is None:
        sc = getattr(getattr(exc, "response", None), "status_code", None)
    if sc == 429:
        return True
    s = str(exc).lower()
    return "429" in s or "rate limit" in s or "too many requests" in s or "请求过于频繁" in s


def _log_embed_degraded(reason):
    try:
        with open(_EMBED_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "reason": reason,
                                "circuit_open": _EMBED_CIRCUIT["open"]},
                               ensure_ascii=False) + "\n")
    except Exception:
        pass

# ── per-user 记忆槽（write_essay/generate_image/thought_experiment/philosopher_debate 共用）──
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

def _find_essay_topic(text):
    """在按题目记忆中找与修改请求相关的作文（题目包含匹配）"""
    for t in _mem_slot()["essays"]:
        if not t:
            continue
        if t in text or (text[:10] and text[:10] in t):
            return t
    return None
