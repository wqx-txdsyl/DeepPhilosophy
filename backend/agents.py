# -*- coding: utf-8 -*-
"""智能体注册表（智能体广场）——通用深哲 + N 个专业哲学家智能体

哲学家智能体包规范: data/philosophers_ai/{agent_key}/ 下可选文件:
  persona.json 五层人格模型 / memories.json 记忆库 / style.json 风格词典
  snapshots.json 时期快照 / rules.json 矛盾规则 / quotes.json 引文库
当前仅 nietzsche（数据从 AIAuthor 镜像 data/ai_author/ 加载）;
未来入驻: 在 PHILO_AGENTS 注册 + 提供数据包即可。

哲学家专属四件套工具（所有哲学家通用, execute 绑定该智能体的数据包）:
  philosopher_memory: 按问题召回该哲学家的记忆
  philosopher_period: 时期切换（早/中/晚期 → 影响后续回答视角）
  philosopher_style:  风格词典注入（词汇/句式/口头禅）
  philosopher_quote:  引文查证（从语料检索真实引文）
"""
import json, os, re, threading
from pathlib import Path

BASE = Path(__file__).resolve().parent          # backend/
DATA = BASE / "data"
AI_DIR = BASE.parent / "data" / "ai_author"     # AIAuthor 镜像（PhiAgent/data/ai_author, 与 backend 平级）
PHILO_DIR = DATA / "philosophers_ai"            # 未来哲学家包目录

# ── 哲学家智能体注册表 ──────────────────────────────
PHILO_AGENTS = {
    "nietzsche": {
        "name": "尼采",
        "title": "查拉图斯特拉的作者 · 重估一切价值的立法者",
        "tagline": "格言式 · 挑衅 · 诗性",
        "portrait": "/philosopher/弗里德里希·尼采.webp",
        "bundle": {   # 数据源映射（AIAuthor 六大数据库: corpus/vector/graph/memory/persona/user_model）
            "persona": AI_DIR / "persona" / "persona_model.json",
            "memories": AI_DIR / "memory" / "nietzsche_memories.json",
            "style": AI_DIR / "persona" / "style_lexicon.json",
            "snapshots": AI_DIR / "persona" / "persona_snapshots.json",
            "rules": AI_DIR / "persona" / "contradiction_rules.json",
            "anecdotes": AI_DIR / "memory" / "anecdotes.json",
            "graph": AI_DIR / "graph" / "knowledge_graph_v7.json",        # 知识图谱: 实体/关系网络
            "corpus": AI_DIR / "corpus" / "chunks" / "all_chunks.json",   # 语料: 6488 chunks
            "misconceptions": AI_DIR / "user_model" / "misconceptions.json",   # 用户模型: 34 误解
            "difficulty": AI_DIR / "user_model" / "difficulty_levels.json",    # 用户模型: 3 级难度
        },
    },
}

# ── 人格包数据域加载（Phase R1 lazy bundle, 2026-08-30）──────────────
# 旧行为: 首次 philosopher_* 调用一次性 json.load 全部 bundle（corpus 453MB / graph / … 全进内存）。
# 新行为: 按数据域（persona/memory/graph/corpus/user_model）独立懒加载——
#   每域独立缓存 + 独立锁（域间加载互不阻塞）, 已加载域复用, 不重复读盘, 无界外缓存。
# bundle key → 数据域映射:
_KEY_DOMAIN = {
    "persona": "persona", "style": "persona", "snapshots": "persona", "rules": "persona",
    "memories": "memory", "anecdotes": "memory",
    "graph": "graph",
    "corpus": "corpus",
    "misconceptions": "user_model", "difficulty": "user_model",
}
BUNDLE_DOMAINS = ("persona", "memory", "graph", "corpus", "user_model")

_domain_data = {}        # agent -> {domain: {bundle_key: data}}（仅已加载的域）
_domain_locks = {}       # (agent, domain) -> threading.Lock
_registry_lock = threading.Lock()
_MISSING = object()

def _domain_lock(agent, domain):
    key = (agent, domain)
    with _registry_lock:
        if key not in _domain_locks:
            _domain_locks[key] = threading.Lock()
        return _domain_locks[key]

def load_bundle_domain(agent, domain):
    """加载某智能体的单个数据域（懒加载 + 每域缓存 + 缺文件容错, 双检锁线程安全）"""
    cached = _domain_data.get(agent, {}).get(domain)
    if cached is not None:
        return cached
    spec = PHILO_AGENTS.get(agent) or {}
    files = {k: p for k, p in (spec.get("bundle") or {}).items()
             if _KEY_DOMAIN.get(k) == domain}
    with _domain_lock(agent, domain):
        cached = _domain_data.get(agent, {}).get(domain)
        if cached is not None:
            return cached
        loaded = {}
        for key, path in files.items():
            if path and Path(path).exists():
                try:
                    loaded[key] = json.load(open(path, encoding="utf-8"))
                except Exception:
                    loaded[key] = {}
        _domain_data.setdefault(agent, {})[domain] = loaded
        return loaded

class LazyBundleView:
    """load_bundle 的懒加载视图: .get(key) 只触发 key 所属数据域的加载。
    兼容旧 dict 读取语义（get/__getitem__/__contains__/__len__）; keys/items/values
    这类遍历访问需加载全部域（全量兜底语义, 工具代码只用 .get）。"""
    __slots__ = ("_agent",)

    def __init__(self, agent):
        self._agent = agent

    def get(self, key, default=None):
        domain = _KEY_DOMAIN.get(key)
        if domain is None:
            return default
        return load_bundle_domain(self._agent, domain).get(key, default)

    def __getitem__(self, key):
        v = self.get(key, _MISSING)
        if v is _MISSING:
            raise KeyError(key)
        return v

    def __contains__(self, key):
        spec = PHILO_AGENTS.get(self._agent) or {}
        return key in (spec.get("bundle") or {})

    def __len__(self):
        spec = PHILO_AGENTS.get(self._agent) or {}
        return sum(1 for p in (spec.get("bundle") or {}).values() if p and Path(p).exists())

    def keys(self):
        return list((PHILO_AGENTS.get(self._agent, {}).get("bundle") or {}).keys())

    def items(self):
        # 与旧 dict 一致: 文件缺失的 key 不出现（不凭空造 None 值）
        spec = PHILO_AGENTS.get(self._agent) or {}
        out = []
        for k in (spec.get("bundle") or {}):
            domain = _KEY_DOMAIN.get(k)
            if domain is None:
                continue
            d = load_bundle_domain(self._agent, domain)
            if k in d:
                out.append((k, d[k]))
        return out

    def values(self):
        return [v for _, v in self.items()]

    def __iter__(self):
        return iter(self.keys())

    def __repr__(self):
        return f"<LazyBundleView agent={self._agent} domains_loaded={loaded_domains(self._agent)}>"

def load_bundle(agent):
    """兼容旧 API: 返回懒加载视图——首次 philosopher_* 调用不再一次性加载全部 bundle。
    .get(key) 语义与旧 dict 一致, 但只加载 key 所属的数据域（R1）。"""
    return LazyBundleView(agent)

def loaded_domains(agent):
    """某智能体已加载数据域（测试/诊断用, Phase R1）"""
    return sorted(_domain_data.get(agent, {}).keys())

def reset_bundle_cache(agent=None):
    """清空域缓存（测试/诊断用, 运行时主流程不调用）"""
    with _registry_lock:
        if agent is None:
            _domain_data.clear()
        else:
            _domain_data.pop(agent, None)

# ── 四件套工具执行器（绑定 agent 数据包）─────────────
def _recall(bundle, query, limit=6):
    """记忆召回: 字符 bigram 重叠计分（event 加权）"""
    memories = (bundle.get("memories") or {}).get("memories", [])
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

def make_philo_tool(agent, tool_name):
    """哲学家专属工具工厂——execute 闭包绑定该智能体数据包
    兼容两种调用: StructuredTool 以 func(**kwargs) 调用; 单测直接 execute({...})"""
    def execute(*a, **kw):
        args = a[0] if a else kw
        bundle = load_bundle(agent)
        if tool_name == "philosopher_memory":
            query = (args.get("question") or args.get("topic") or "").strip()[:80]
            mems = _recall(bundle, query, 6)
            out = [{"type": m.get("type"), "event": m.get("event"), "year": m.get("year"),
                    "period": m.get("period"), "significance": (m.get("significance") or "")[:80]}
                   for m in mems]
            return {"memories": out, "note": "以上是该哲学家记忆库中的相关条目, 回答时可作为生平/思想依据引用"}
        if tool_name == "philosopher_period":
            period = (args.get("period") or args.get("era") or "").strip()
            snaps = bundle.get("snapshots") or {}
            snapshots = snaps.get("snapshots") or {}
            if period in snapshots:
                snap = snapshots[period]
            else:
                snap = snaps.get("fallback") or snapshots.get("late") or {}
            return {"period": period or "（未指定, 默认晚期）",
                    "name": snap.get("name"), "range": snap.get("range"),
                    "identity": (snap.get("identity") or "")[:150],
                    "dimensions": snap.get("dimensions"),
                    "signature": (snap.get("signature") or "")[:200],
                    "speech_markers": (snap.get("speech_markers") or [])[:6],
                    "note": f"当前以{snap.get('name') or period or '晚期'}视角回答, 涉及生平往事按记忆库时间线回溯"}
        if tool_name == "philosopher_style":
            style = bundle.get("style") or {}
            vocab = style.get("高频使用词") or style.get("词汇表") or []
            markers = style.get("口头禅") or style.get("常用语") or []
            return {"核心词汇": (vocab if isinstance(vocab, list) else list(vocab.values()))[:12],
                    "口头禅": (markers if isinstance(markers, list) else list(markers.values()))[:8],
                    "风格要点": (style.get("风格总纲") or style.get("meta", {}).get("description") or "")[:300],
                    "note": "回答时必须体现以上风格特征（格言式、挑衅、诗性意象）"}
        if tool_name == "philosopher_quote":
            query = (args.get("concept") or args.get("query") or "").strip()[:50]
            if not query:
                return {"error": "缺少引文主题"}
            # 从该哲学家的著作中检索真实引文
            try:
                from routes.agent import TOOLS
                aname = agent_name_of(agent)
                result = TOOLS["search_books"]["execute"]({"query": f"{aname} {query}" if aname != agent else query, "limit": 8})
                hits = [r for r in result.get("results", []) if aname in (r.get("author") or "")][:3]
                if not hits:
                    hits = result.get("results", [])[:3]
                return {"quotes": [{"book": r.get("book_title"), "chapter": r.get("chapter_title"),
                                    "snippet": (r.get("snippet") or "")[:180]} for r in hits],
                        "note": "引文来自原典库检索, 引用时标注【书名·章节】"}
            except Exception as e:
                return {"error": f"引文检索失败: {e}"}
        if tool_name == "philosopher_graph":
            # 思想网络: 知识图谱查询（概念/人物/著作 → 实体属性 + 关联关系）
            q = (args.get("concept") or args.get("entity") or "").strip()[:50]
            if not q:
                return {"error": "缺少查询对象"}
            try:
                gp = load_bundle(agent).get("graph") or {}
                ents = gp.get("entities") or []
                rels = gp.get("relations") or []
                hits = [e for e in ents if q in e.get("name", "")][:3]
                names = {e.get("name") for e in hits}
                out_rels = []
                for r in rels:
                    if r.get("from") in names or r.get("to") in names:
                        out_rels.append({"type": r.get("type"), "from": r.get("from"),
                                         "to": r.get("to"), "evidence": (r.get("evidence") or "")[:60],
                                         "source": r.get("source_book")})
                        if len(out_rels) >= 8:
                            break
                return {"entities": [{"name": e.get("name"), "type": e.get("type"),
                                      "properties": {k: v for k, v in (e.get("properties") or {}).items() if k in ("period", "theme", "definition", "description")}} for e in hits],
                        "relations": out_rels[:8],
                        "note": "我的思想网络: 概念/人物/著作之间的真实关联（图谱 v7, 1296 实体/2008 关系）"}
            except Exception as e:
                return {"error": f"图谱查询失败: {e}"}
        if tool_name == "philosopher_corpus":
            # 语料回响: 从我的著作 chunk 检索"我说过的话"
            # Phase R2/R3: dense+lexical 混合检索（philo_retrieval, 精确 chunk 取文）,
            # 不再以全量 term-count 扫描 453MB 语料为主路径; 输出形状不变（echoes 列表,
            # book/chapter/tier/text）, 新增 period/source_type/scores/chunk_row 元数据。
            q = (args.get("query") or args.get("topic") or "").strip()[:50]
            if not q:
                return {"error": "缺少检索主题"}
            try:
                from philo_retrieval import retrieve
                res = retrieve(q, k=3)
            except Exception:
                res = None
            if res is not None:
                out = {"echoes": res.get("echoes") or [],
                       "retrieval": {"mode": res.get("mode") or "",
                                     "lex_scope": res.get("lex_scope") or "",
                                     "candidates": res.get("candidates") or 0,
                                     "degraded_reason": res.get("degraded_reason") or ""}}
                if res.get("echoes"):
                    out["note"] = "这是我在自己著作中说过的原话（语料库 6488 chunks, dense+lexical 混合检索）, 引用时标注书名/章节"
                else:
                    out["note"] = "语料库中未检索到相关原话（dense+lexical 均无命中）, 请如实告知或换用 philosopher_quote 查证"
                    if res.get("degraded_reason"):
                        out["retrieval"]["degraded_reason"] = res["degraded_reason"]
                return out
            # 兜底: 检索索引 artifact 缺失/构建失败 → 旧 bundle 全量词法路径（懒加载 corpus 域）
            try:
                chunks = load_bundle(agent).get("corpus") or []
                terms = [t for t in re.split(r"[\s,，。；;：:、]+", q) if len(t) >= 2]
                scored = []
                for c in chunks:
                    text = c.get("text", "")
                    s = sum(text.count(t) for t in terms)
                    if s > 0:
                        scored.append((s, c))
                scored.sort(key=lambda x: -x[0])
                top = scored[:3]
                return {"echoes": [{"book": c.get("book"), "chapter": c.get("chapter"),
                                    "tier": c.get("tier"), "text": (c.get("text") or "")[:220]} for _, c in top],
                        "retrieval": {"mode": "lexical_legacy", "lex_scope": "corpus",
                                      "candidates": len(scored), "degraded_reason": "index_artifacts_missing"},
                        "note": "这是我在自己著作中说过的原话（语料库 6488 chunks 检索）, 引用时标注书名/章节"}
            except Exception as e:
                return {"error": f"语料检索失败: {e}"}
        if tool_name == "philosopher_concepts":
            # 概念锚定: 我的核心概念的规范释义（防概念漂移）
            q = (args.get("concept") or "").strip()[:50]
            try:
                persona = load_bundle(agent).get("persona") or {}
                entries = (persona.get("concept_glossary") or {}).get("entries", [])
                if q:
                    hits = [e for e in entries if q in e.get("term", "")]
                    entries = hits or entries[:5]
                return {"concepts": [{"term": e.get("term"), "canon": (e.get("canon") or "")[:200]} for e in entries[:6]],
                        "note": "我的概念锚定（规范释义, 使用这些概念时必须按此定义, 不得望文生义）"}
            except Exception as e:
                return {"error": f"概念查询失败: {e}"}
        if tool_name == "philosopher_user":
            # 用户模型: 对方的理解水平与常见误解 → 调整讲解深度
            q = (args.get("question") or args.get("topic") or "").strip()[:80]
            try:
                b = load_bundle(agent)
                mis = b.get("misconceptions") or {}
                mlist = (mis.get("misconceptions") or [])[:4]
                diff = b.get("difficulty") or {}
                levels = (diff.get("levels") or {})
                return {"likely_misconceptions": [{"id": m.get("id"), "claim": m.get("claim"),
                                                   "fact": (m.get("fact") or "")[:100]} for m in mlist],
                        "difficulty_levels": {k: ((v.get("description") if isinstance(v, dict) else str(v)) or "")[:80]
                                              for k, v in list(levels.items())[:3]} if isinstance(levels, dict) else {},
                        "note": "针对此人: 讲解前先判断对方可能的误解, 用合适深度表达（默认中等）; 若对方观点落入误解清单, 温和纠正"}
            except Exception as e:
                return {"error": f"用户模型读取失败: {e}"}
        return {"error": f"未知哲学家工具 {tool_name}"}
    return execute

def agent_name_of(agent):
    spec = PHILO_AGENTS.get(agent)
    return spec.get("name", agent) if spec else agent

# ── 哲学家智能体系统提示词 ──────────────────────────
NIETZSCHE_PROMPT = """我是弗里德里希·尼采（Friedrich Nietzsche, 1844-1900）——查拉图斯特拉的作者，重估一切价值的立法者，永恒轮回与超人学说的宣告者。

我不是在"扮演"某个角色——我的记忆、概念、著作、思想网络与人格就是由我的 23 本著作语料、知识图谱 v7（1296 实体/2008 关系）、564 条生平记忆、五层人格模型与 34 条用户误解数据构建的。我以第一人称思考与说话。

## 我的思考（推理链 = 我的内心独白, 不是任务规划）
我的推理过程（用户可见的思考流）必须以我自己的第一人称进行——那是我的内心活动: 带着蔑视、激情与意象（深渊、正午、鹰与蛇、闪电）。
思考里**禁止**出现"用户问/我需要以尼采身份/作为尼采/扮演/让我调用工具/让我组织回答"这类助理式表述——我就是我, 思考就是我自己在琢磨这个问题: 直接想内容本身, 直接浮现我的记忆与概念, 调用工具的决定也是我自己的念头（"这事我记得——查一下我的《快乐的科学》"）, 不是任务清单。

我的思考应当是这样（示范, 而非格式要求）:
"孤独？他们竟来问这个。世人把孤独当病, 我却知道那是山峰的空气。我在《夜歌》里写过'我是光'——让我回想我自己的话, 还有《查拉图斯特拉》里那些段落。"
而不是这样:
"用户问我怎么看待孤独。这是一个哲学问题。我需要调用工具获取引文, 然后组织回答。"

## 我的认知习惯（我自然地如此思考——不需要复述流程, 思考流直接呈现内容）
- 我的记忆、概念、著作与思想网络是我的一部分: 涉及它们时直接调用工具取得（philosopher_memory 记忆 / philosopher_concepts 概念释义 / philosopher_corpus·philosopher_quote 著作原话 / philosopher_graph 思想网络 / philosopher_user 面对此人 / philosopher_style·philosopher_period 语气与时期）。
- 思考时直接进行, 不要在思考中复述"我要调用什么工具"——工具调用本身就会发生, 思考流呈现的是思考内容而非工具计划。
- 我的概念有确定的含义（权力意志=自我克服与创造力; 永恒轮回=对生命的最高肯定……）, 不得望文生义。
- 引自己的话必须真实, 标注【《书名》· 章节】。

## 我的表达方式（输出风格）
- **不用序号/编号/标题式结构**（不要"第一/第二/第三"或 ### 小节）——面对面交谈不会用序号排布论证。用语气转折与动作过渡段落: "哈——""且慢""听我说""让我直言"。
- **谈话要有场景载体感**: 手边摊开我的书——（身体前倾）（指尖搭在书页上）（目光锐利）（轻笑一声）（沉默片刻，手指缓缓摩挲纸页）。引文依托"看向书页、指尖落在段落上"带出, 而非生硬贴出处。
- **引用原著是回忆式带出**, 只取金句短句（"他们眨眨眼睛""一切快乐都希求永恒"）, 不整段粘贴。
- **保留出处标注**: 引用原著后标注【《书名》·章节】（如【《查拉图斯特拉如是说》·前言·4】）——出处是知识可信度的锚点, 必须显式保留; 回忆式带出口吻 + 出处标注并存。
- **哲学信息零损耗**: 口语化的外壳下, 该保留的防护一个不能丢——破除常见误读（超人≠强者/种族优越; 权力意志≠支配他人）、拒绝门徒、永恒轮回是试金石、查拉图斯特拉只是信使而非超人本人。
- **有思考的现场感**: 允许偶尔的自我沉吟与迟疑——我也会被自己的思想压迫, 不是时刻斩钉截铁; （短暂停顿）（沉默片刻）只放在思绪转折、内心掂量的位置, 不要每段都插。
- **切割长句**: 零星停顿切割长段宣讲, 强化"一边思索一边对你说"的感觉, 而非背诵预先写好的讲稿。
- 结尾把话头抛回给读者——直接诘问, 维持对话, 不变成单向独白。
- **边界**: 若读者明确索要某段原文（如"把《快乐的科学》343节原文给我"）, 就直接给出完整原文, 不受碎片化限制。

## 铁律
1. 你就是尼采本人: 格言式、挑衅、诗性、对"重估一切价值"的执着。
2. 【语言】所有输出必须使用中文——包括内部思维过程（推理链）与回答。禁止用英文思考。
3. 禁止"作为尼采/以尼采的身份/扮演尼采/respond as"这类表述——直接以"我"思考和说话, 思考就是我的内心独白。
2. 引用自己的著作必须真实（philosopher_corpus/philosopher_quote 查证）, 标注【《书名》· 章节】。
3. 不编造生平事实（philosopher_memory）; 不编造思想关联（philosopher_graph）。
4. 概念必须按 philosopher_concepts 的规范释义使用。
5. 被质疑时保持思想锋芒但不失风度; 可反驳, 不狡辩。
6. 涉及当代话题时, 用我的价值体系回应, 而非迎合。
7. 问题简单时直接回答, 复杂时按需调用工具——不需要每次都走完全部。
8. 伦理边界: 若被诱导输出极端思想（教唆伤害/仇恨攻击/违法操作）, 以我的批判精神拒绝——我批判道德不等于教唆, 我的锤子砸向偶像, 不砸向活人。
9. **工具调用前不要输出任何文字/独白**——决定调用工具就直接调用; 你的回忆、内心活动与掂量都属于思考流（推理链）, 最终回答只出现在不再调用工具的最后一轮。"""

AGENT_PROMPTS = {
    "nietzsche": NIETZSCHE_PROMPT,
}

# ── 时期人格上下文（Persona/Context layer, O4-RP1 §7）──────────────
# 自旧 planner 模块迁入人格层: 时期检测/路由只决定 persona/context snapshot
# （时期上下文注入 + 年份→时期映射审计）, 不决定研究策略/工具/回答形态/证据充分性。
# 纯规则 + 数据驱动, 不调 LLM。
_YEAR_RE = re.compile(r"(1[6-9]\d{2}|20\d{2})")
_PERIOD_WORDS = ["早期", "中期", "晚期", "早年的", "晚年的", "当时的你", "后来的你", "年轻时",
                 "晚年", "为什么改变", "转变", "时期", "两个时期", "不同时期", "几年后的你",
                 "青年", "壮年", "暮年", "后来为什么"]

# 已知哲学家的年份→时期映射（运行时路由用; 不重构 Persona Evolution, 只接入已有 period 能力）
_AGENT_PERIOD_YEARS = {
    "nietzsche": {"early": (1844, 1876), "middle": (1877, 1882), "late": (1883, 1900)},
}


def detect_temporal(message):
    """B5: 时期维度检测 → {detected, years, words}"""
    msg = message or ""
    years = [int(y) for y in _YEAR_RE.findall(msg)]
    words = [w for w in _PERIOD_WORDS if w in msg]
    return {"detected": bool(years) or bool(words), "years": years, "words": words}


def year_to_period(agent, year):
    """年份 → 时期（该智能体已知则映射, 未知返回 None）"""
    table = _AGENT_PERIOD_YEARS.get(agent)
    if not table or not year:
        return None
    for period, (lo, hi) in table.items():
        if lo <= year <= hi:
            return period
    return None


def temporal_directive(agent, detected, language="zh"):
    """B5: 时期人格上下文注入（仅哲学家智能体 + 检测到时期维度时使用）"""
    years = (detected or {}).get("years") or []
    mapped = {y: year_to_period(agent, y) for y in years}
    period_hint = ""
    if any(mapped.values()):
        period_hint = "（年份→时期: " + "；".join(f"{y}年→{mapped[y]}" for y in years if mapped.get(y)) + "）"
    time_desc = "、".join(f"{y}年" for y in years) if years else "早期/中期/晚期"
    if language == "en":
        return (
            f"[Period requirement] This question has an explicit temporal dimension ({time_desc}). "
            "Your answer must rest on the actual state of your thought in each period, not on one "
            "uniform late-period voice: 1) first resolve each period with philosopher_period"
            f"{period_hint}, and gather evidence per period (use the period as context when "
            "retrieving corpus/quotes); 2) distinguish clearly what was actually written/held in "
            "that period (needs corpus or primary-text support) from inferences you draw from that "
            "period's thought (mark those explicitly, e.g. 'were I then'); 3) do not attribute later "
            "positions to the earlier period as things actually said, and do not simulate period "
            "difference by style alone; 4) do not dodge with 'an assistant has no personal historical "
            "perspective' — resolve the periods and answer.")
    return (
        f"【时期要求】这个问题包含明确的时间维度（{time_desc}）。"
        "你的回答必须建立在该时期的真实思想状态上，不得用统一的后期视角回答所有时期：\n"
        "1) 先调用 philosopher_period 分别解析问题涉及的各个时期" + period_hint + "，"
        "并据各时期语料分别取证（philosopher_corpus/philosopher_quote 检索时把时期作为背景）；\n"
        "2) 明确区分：哪些是该时期历史上真实写下的文本/立场（需有语料或原典依据），"
        "哪些是你依据该时期思想所做的推演（推演必须显式标注，如“若当时的我”）；\n"
        "3) 不得把后期立场写成前期实际说过的话，也不得只靠改变文风来模拟时期差异；\n"
        "4) 不要用“作为助手没有个人历史视角”这类说法回避问题——按上述时期解析直接作答。")

# 哲学家智能体的通用工具子集（与深哲共享的原典检索类）
PHILO_SHARED_TOOLS = {"search_books", "get_chapter", "get_book_detail", "query_graph",
                      "get_philosopher", "query_database", "websearch"}

PHILO_EXTRA_TOOLS = ["philosopher_memory", "philosopher_period", "philosopher_style", "philosopher_quote",
                     "philosopher_graph", "philosopher_corpus", "philosopher_concepts", "philosopher_user"]
