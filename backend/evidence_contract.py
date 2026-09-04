# -*- coding: utf-8 -*-
"""Evidence Contract（Phase 3）——检索到的 ≠ 回答用的

解决第三个核心问题: 检索命中了 20 条 ≠ 最终回答真的用了 20 条。
此前"引用来源"面板把 search_books 命中的前 N 条全部当作引用展示——用户会把
retrieval candidates 误解为 answer evidence。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  EvidenceExtractor        从 tool_log 提取证据候选 → retrieved_evidence
                            （search_books 命中 / get_chapter 阅读 / 语料回响 入池;
                             websearch 等 secondary 仅审计, 不进引用面板; 字段映射
                             单一真源 = build_evidence_pool, quote_bound 经它做
                             逐字核验 span 池的形状适配）
  EvidenceUsageVerifier    回答正文 ↔ 证据的确定性对齐（引用标注精确匹配 + 片段
                            shingle 重叠）→ used_evidence（retrieved 且 used）
  EpistemicClaimClassifier Claim 知识论分级（9 类, O4-RP1 起由本文件本地定义
                            本文件——只做 claim → quote/citation/source-bound claim 的
                            deterministic evidence binding 分类, 无 runtime 控制效果）
  ClaimEvidenceBinder      Claim 抽取与证据绑定; SPECULATION 绝不绑定 DIRECT evidence
  CitationValidity         引用【《书名》·章节】必须能映射到 used_evidence;
                            仅"检索过"没有资格进入引用面板; 未核验引用单列
                            unverified_citations（不入面板）
  EvidenceState            执行事实登记（O5 并入 agent_runtime 旧义务台账: 只记
                            WHAT HAPPENED, 随 done.evidence.facts 输出; 无任何义务/准入判定）

Phase 3 边界（见任务书）:
  - 不改 Graph / Memory / Persona Snapshot / 矢量库 / 工具注册表 / 流式协议
  - done 事件新增 evidence 字段; citations 字段改投影 used_evidence（面板向后兼容）
  - 纯规则生效, 异常只降级为跳过, 绝不影响主流程（与 Phase 1/2 同机制）

O4-RP1: build_evidence_contract 不再接收 source_constraint/subject_authors——
契约只描述"检索到的 ↔ 回答用的"确定性关系, 不按用户意图分类排除证据。

用法（engine_langgraph.stream_agent 内, 应答完成后）:
  contract = build_evidence_contract(tool_log, full_answer, agent, language)
  citations = contract["citations"]     # 仅 used_evidence 的投影
"""
import json
import re
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
LOG_FILE = BASE / "data" / "evidence_contract.jsonl"   # 运行时记录（backend/data 已 gitignore）

# 引用标注提取（Phase T/T13-A: 统一覆盖 canonical + 全部已知变体）:
#   canonical   【《书名》·章节】 / 【《书名》】 / 【《书名》 · 章节】
#   variant ①   【《书名·章节》】（·在《》内 → _split_book_chapter 拆分）
#   variant ②   【《书名》47】（节数/页码, 无·; 落在区间章节内即核验通过）
#   variant ③   【作者·《作品》】（作者署名格式——书名级核验, 章节未知）
_CITE_RE = re.compile(r"【《([^》]+)》·?([^】]*)】")
_CITE_AUTHOR_WORK_RE = re.compile(r"【([^·《】]{2,16})\s*·\s*《([^》]+)》】")

# 章节名尾段（供《书·章》变体拆分: 仅当 · 后是这类词才拆, 防含·真书名被误拆）
_CHAPTER_TAIL_RE = re.compile(
    r"^(第[^·]{0,10}(章|节|卷|部|篇)|序|序言|导言|引言|前言|附录|结语|后记|跋|[上下中]篇|[0-9]{1,4})$")


def _split_book_chapter(book, chapter):
    """章节写进书名的变体归一（2026-08-31）: 模型常写【《康德著作集·序言》】（·在《》内）,
    解析得 book='康德著作集·序言' → 书名查不到。仅当章节参数为空且尾段形如章节名时拆分。"""
    b, c = (book or "").strip(), (chapter or "").strip()
    if c or "·" not in b:
        return b, c
    head, _, tail = b.rpartition("·")
    head, tail = head.strip(), tail.strip()
    if head and tail and _CHAPTER_TAIL_RE.match(tail):
        return head, tail
    return b, c

# 归一化: 剥《》【】· 空白与常见标点（全角/半角引号括号）, 供确定性匹配
_PUNCT_RE = re.compile(r"[\s《》【】·•、,，。.;；:：!！?？()（）\[\]{}—\-_~`\"“”'‘’]+")

# 检索候选白名单（仅这些工具的结果构成本库原典证据）; websearch 等按 secondary 审计
PRIMARY_TOOLS = {"search_books", "get_chapter", "philosopher_corpus", "philosopher_quote"}
SECONDARY_TOOLS = {"websearch"}

_SHINGLE_LEN = 8          # 片段 shingle 长度（≥8 连续字符命中 → 视为回答摘引了该片段）
_MIN_CLAIM_LEN = 12       # 短句不作为 Claim


# ═══════════════════════════════════════════════════════
# 0. EvidenceState（O5: 执行事实登记, agent_runtime 旧义务台账并入 Evidence Store）
# ═══════════════════════════════════════════════════════
# 只登记"已发生什么"（WHAT HAPPENED）, 不判定"还必须做什么"（WHAT MUST HAPPEN）:
#   read_chapters / read_execs        get_chapter 成功读取过的章节与计数
#   primary_text_read                 是否实际读到过章节全文（只能由 get_chapter 置位;
#                                     检索片段/书目永远不算）
#   source_candidate_found / search_execs
#                                     检索/查询类命中过非空结果（定位线索 MEMORY_HINT）与计数
# 无 term / 无 exact_quote_verified（O5 删除: 失去生产喂入口; 逐字核验真源 =
# quote_bound.verify_quote + final_validator）/ 无 admit / 无义务满足判定——
# 是否继续检索、何时收口, 全部由 Main Agent 自主决定。
class EvidenceState:
    """invocation 级执行事实登记（生命周期 = 单次请求; 纯登记, 零控制效果）"""

    def __init__(self):
        self.read_chapters = []      # ["{book_id}#{chapter_idx}", ...] 已成功读取
        self.search_execs = 0
        self.read_execs = 0
        self.source_candidate_found = False
        self.primary_text_read = False

    def record_search(self, ok, result=None):
        """检索/查询类工具执行后登记事实（成败都计数; 命中非空结果才算定位线索成立）"""
        self.search_execs += 1
        if not self.source_candidate_found and ok and isinstance(result, dict):
            for k in ("results", "books", "items", "hits", "records"):
                v = result.get(k)
                if isinstance(v, list) and v:
                    self.source_candidate_found = True
                    break

    def record_read(self, book_id, chapter_idx):
        """get_chapter 成功读取后登记事实（失败读取不是 READ 事实——不计数;
        PRIMARY_TEXT_READ 只有 get_chapter 全文能置位, MEMORY_HINT 永远不算）"""
        self.read_execs += 1
        key = f"{book_id or ''}#{chapter_idx if isinstance(chapter_idx, int) else -1}"
        if key not in self.read_chapters:
            self.read_chapters.append(key)
        self.primary_text_read = True

    def snapshot(self):
        return {"read_chapters": list(self.read_chapters),
                "search_execs": self.search_execs,
                "read_execs": self.read_execs,
                "source_candidate_found": self.source_candidate_found,
                "primary_text_read": self.primary_text_read}

# 跳过行: mermaid/流程图代码与分隔线（不是论证性 Claim）
_SKIP_CLAIM_RE = re.compile(
    r"^\s*(flowchart|graph|mindmap|sequenceDiagram|classDiagram|erDiagram|journey|timeline)\b|"
    r"--->|```|^\s*[-*]\s+\([^)]*\)\s*$")


# ═══════════════════════════════════════════════════════
# 1. 归一化与匹配基元
# ═══════════════════════════════════════════════════════
def _norm(s):
    return _PUNCT_RE.sub("", s or "")


def _shingles(text, length=_SHINGLE_LEN):
    t = text or ""
    return {t[i:i + length] for i in range(len(t) - length + 1)} if len(t) >= length else set()


def _book_match(ev_book, cited_book):
    """书名精确/包含匹配（双向, 更长侧 ≥2 字才允许包含——防"理想国"误吞其他书名）"""
    a, b = _norm(ev_book), _norm(cited_book)
    if not a or not b:
        return False
    if a == b:
        return True
    if len(a) >= 2 and a in b:
        return True
    if len(b) >= 2 and b in a:
        return True
    return False


_APH_RANGE_RE = re.compile(r"第\s*(\d{1,4})\s*[-—–~]\s*(\d{1,4})\s*节")


def _chapter_match(ev_ch, cited_ch):
    """章节双向包含（引用【《书》·前言】而库内章节"前言·1"亦然; 一方缺失=书名级匹配）
    2026-08-30: 格言体著作（快乐的科学等）章节形如"第108—275节", 引用【·125】为节数——
    落在区间内即视为命中（否则区间章节永远核验不过, 全部降级为"一般提及"）。"""
    a, b = _norm(ev_ch), _norm(cited_ch)
    if not a or not b:
        return True
    m = _APH_RANGE_RE.search(ev_ch or "")
    if m and re.fullmatch(r"\d{1,4}", (cited_ch or "").strip()):
        n = int(cited_ch.strip())
        if int(m.group(1)) <= n <= int(m.group(2)):
            return True
    if len(a) < 2 or len(b) < 2:
        return a == b
    return a in b or b in a


def _cite_markers(text):
    """从文本抽取全部引用标注 → [(book, chapter)]（统一覆盖 canonical + 三种变体, T13-A）"""
    return iter_citation_markers(text)


def iter_citation_markers(text):
    """canonical + 变体的统一迭代器 → [(book, chapter)]（含《书·章》拆分; 作者·《作品》书名级）"""
    out = []
    for m in _CITE_RE.finditer(text or ""):
        out.append(_split_book_chapter(m.group(1), m.group(2)))
    for m in _CITE_AUTHOR_WORK_RE.finditer(text or ""):
        out.append((m.group(2), ""))   # 作者·《作品》: 核验对象是作品本身（章节未知）
    return out


def iter_cite_spans(text):
    """正文全部引用标注（带位置, 按出现序）→ [(start, end, book, chapter, kind)]
    kind: 'canonical'（含①②变体）| 'author_work'（③变体）——净化器替换用"""
    spans = []
    for m in _CITE_RE.finditer(text or ""):
        b, c = _split_book_chapter(m.group(1), m.group(2))
        spans.append((m.start(), m.end(), b, c, "canonical"))
    for m in _CITE_AUTHOR_WORK_RE.finditer(text or ""):
        spans.append((m.start(), m.end(), m.group(2), "", "author_work"))
    spans.sort(key=lambda x: x[0])
    return spans


# ═══════════════════════════════════════════════════════
# 2. EvidenceExtractor —— tool_log → 证据候选
# ═══════════════════════════════════════════════════════
def _base_evidence(seq, source_id, source_type="primary"):
    return {
        "evidence_id": f"ev_{seq}",
        "source_id": source_id,
        "book": "", "chapter": "",
        "book_id": "", "chapter_idx": -1,
        "author": "", "snippet": "", "score": 0.0,
        "source_type": source_type,
        "retrieved": True, "used": False,
        "supports_claim_ids": [],
    }


def build_evidence_pool(raw_tool_log):
    """raw_tool_log → 全保真证据池（D4 单一真源: raw_tool_log 字段映射只维护一份）。

    每条 = 一个可核验文本来源（保持检索顺序）:
      {entry_index, kind, book, chapter, book_id, chapter_idx, author,
       text（全保真, 不截断）, score, source_type}
    kind/source_type: chapter→primary_read（get_chapter 全文）/ search→snippet
                      （检索片段）/ corpus（语料回响）/ web→secondary（仅审计）
    消费方在此池上做形状适配:
      _extract_candidates        → 证据契约候选池（snippet 截断 220; 各自准入条件）
      quote_bound.evidence_spans → 逐字核验 span 池（chapter 按行分段 units）
    """
    pool = []
    for i, tc in enumerate(raw_tool_log or []):
        name = tc.get("name") or ""
        rf = tc.get("result_full")
        if not isinstance(rf, dict) or rf.get("error"):
            continue
        if name == "search_books":
            for item in rf.get("results") or []:
                if not isinstance(item, dict):
                    continue
                pool.append({
                    "entry_index": i, "kind": "search", "source_type": "snippet",
                    "book": item.get("book_title") or "",
                    "chapter": item.get("chapter_title") or "",
                    "book_id": item.get("book_id") or "",
                    "chapter_idx": item.get("chapter_idx", -1),
                    "author": item.get("author") or "",
                    "text": item.get("snippet") or "",
                    "score": float(item.get("score") or 0),
                })
        elif name == "get_chapter":
            b = {}
            if rf.get("book_id"):
                try:
                    from routes.agent import book_by_id
                    b = book_by_id(rf.get("book_id")) or {}
                except Exception:
                    b = {}
            pool.append({
                "entry_index": i, "kind": "chapter", "source_type": "primary_read",
                # 契约口径: 目录题名优先, 回退结果自带 book_title;
                # quote_bound 逐字核验口径沿用结果自带原始字段（book_title_raw/chapter_title_raw）
                "book": b.get("title", "") or rf.get("book_title") or "",
                "book_title_raw": rf.get("book_title") or "",
                "chapter": rf.get("title") or rf.get("chapter_title") or "",
                "chapter_title_raw": rf.get("title") or "",
                "book_id": rf.get("book_id", ""),
                "chapter_idx": rf.get("chapter_idx", -1),
                "author": b.get("author", ""),
                "text": rf.get("text") or "",
                "score": 1.0,
            })
        elif name in ("philosopher_corpus", "philosopher_quote"):
            for echo in (rf.get("echoes") or rf.get("quotes") or []):
                if not isinstance(echo, dict):
                    continue
                pool.append({
                    "entry_index": i, "kind": "corpus", "source_type": "corpus",
                    "book": echo.get("book") or "",
                    "chapter": echo.get("chapter") or "",
                    "book_id": "", "chapter_idx": -1, "author": "",
                    "text": echo.get("text") or echo.get("snippet") or "",
                    "score": float(echo.get("score") or 0),
                })
        elif name in SECONDARY_TOOLS:
            # 外网结果仅审计: 无《书名》定位能力, 永远不进引用面板
            pool.append({
                "entry_index": i, "kind": "web", "source_type": "secondary",
                "book": "", "chapter": "", "book_id": "", "chapter_idx": -1, "author": "",
                "text": rf.get("content") or rf.get("text") or str(rf),
                "score": 0.0,
            })
    return pool


def _extract_candidates(tool_log):
    """（D4 薄适配）证据池 → 证据契约候选列表（保持检索顺序; 各白名单准入条件不变:
    检索项需 book_title, 章节项需 book_id, 语料项需 book; snippet 截断 220）"""
    cands = []
    for e in build_evidence_pool(tool_log):
        kind = e["kind"]
        if kind == "search":
            if not e["book"]:
                continue
            ev = _base_evidence(len(cands) + 1, f"src_search_{e['entry_index']}")
            ev.update({"book": e["book"], "chapter": e["chapter"], "book_id": e["book_id"],
                       "chapter_idx": e["chapter_idx"], "author": e["author"],
                       "snippet": e["text"][:220], "score": e["score"]})
        elif kind == "chapter":
            if not e["book_id"]:
                continue
            ev = _base_evidence(len(cands) + 1, f"src_chapter_{e['entry_index']}")
            ev.update({"book": e["book"], "chapter": e["chapter"], "book_id": e["book_id"],
                       "chapter_idx": e["chapter_idx"], "author": e["author"],
                       "snippet": e["text"][:220], "score": 1.0})
        elif kind == "corpus":
            if not e["book"]:
                continue
            ev = _base_evidence(len(cands) + 1, f"src_corpus_{e['entry_index']}")
            ev.update({"book": e["book"], "chapter": e["chapter"], "author": "",
                       "snippet": e["text"][:220], "score": e["score"]})
        else:   # web
            ev = _base_evidence(len(cands) + 1, f"src_web_{e['entry_index']}",
                                source_type="secondary")
            ev.update({"snippet": e["text"][:220]})
        cands.append(ev)
    return cands


def _dedup(cands):
    """同一 (book, chapter) 多次检索命中 → 合并为一条证据（保留最高分片段）"""
    seen, out = {}, []
    for c in cands:
        key = (c["book_id"], c["chapter_idx"]) if c["book_id"] else (_norm(c["book"]), _norm(c["chapter"]))
        if key in seen:
            prev = out[seen[key]]
            if c["score"] > prev["score"]:
                prev["score"] = c["score"]
                prev["snippet"] = c["snippet"] or prev["snippet"]
            continue
        seen[key] = len(out)
        out.append(c)
    return out


# ═══════════════════════════════════════════════════════
# 3. EvidenceUsageVerifier —— 回答正文 ↔ 证据的确定性对齐
# ═══════════════════════════════════════════════════════
# 语义定义:
#   retrieved_evidence  = 检索到（候选全集）
#   candidate_evidence  = 可能支持 claim（正文对齐: 引用标注/片段重叠命中）
#   used_evidence       = 最终可见 claim 实际依赖（candidate 且可核验）
#   visible_citation    ⊆ used_evidence（引用面板/正式引用只从 used 投影）
# O4-RP1: 来源约束排除（PRIMARY_ONLY/AUTHOR_ONLY 二手过滤）已删除——
# "该用哪些来源"由 Main Agent 自主判断, 契约只登记确定性使用事实。
def _evidence_used(ev, ans_norm, markers, ans_raw):
    """used = ①回答含该证据的引用标注【《书》·章】 ②回答摘引了检索片段（shingle 重叠）;
    引号内短引文（10 字以上连续摘引）也计入"""
    for b, ch in markers:
        if _book_match(ev["book"], b) and _chapter_match(ev["chapter"], ch):
            return True
    sn = _norm(ev["snippet"])
    if len(sn) >= _SHINGLE_LEN + 4:
        for s in _shingles(sn):
            if s in ans_norm:
                return True
        for q in re.findall(r"[“\"]([^”\"]{10,80})[”\"]", ans_raw or ""):
            qn = _norm(q)
            if qn and qn in sn:
                return True
    return False


# ═══════════════════════════════════════════════════════
# 3.5 Claim 知识论分级（O4-RP1 起由本文件本地定义——
#     evidence provenance taxonomy: claim → quote/citation/source-bound 分类,
#     只服务 deterministic evidence binding, 无任何 runtime 控制效果）
# ═══════════════════════════════════════════════════════
def _strip_marks(s):
    return (s or "").replace("《", "").replace("》", "").replace(" ", "").strip()


# O5 MOVE: _norm_author / _load_philosophers / PHILOSOPHER_ALIASES / _match_philosopher
# 与 EPISTEMIC_LANGUAGE / language_bound 已迁至 evaluation_suite（离线评估自带副本——
# 本模块内部零调用; 运行时不再持有哲学家名匹配与表达强度模板层）。


EPISTEMIC_TYPES = [
    "SOURCE_FACT",                # 文本明确写到的事实（带可核验出处）
    "DIRECT_QUOTE",              # 原文直接引语
    "TEXTUAL_INFERENCE",         # 对文本的解释性推断（文学/哲学解读）
    "CROSS_TEXT_INTERPRETATION", # 借用另一思想家框架的跨文本解读
    "SCHOLARLY_INTERPRETATION",  # 学界/研究界的解释
    "AUTHOR_COUNTERFACTUAL",     # 关于作者本人会怎么想的反事实推演
    "USER_PREMISE",              # 用户提出的前提/假设
    "SPECULATION",               # 推测（作者未表、亦无研究共识）
    "UNKNOWN",                   # 现有材料不足以判断
]

# 具体 → 一般 顺序匹配（首个命中即定级; 全部未中 → UNKNOWN）
_CLAIM_CUES = [
    ("DIRECT_QUOTE", r"原文写道|原文说|书上原话|引文\s*[\"“]|直接引用|原文是|今引|原话是"),
    ("SOURCE_FACT", r"文本明确写道|明确记载|书中明确|文本明确|原文明确|史料记载|史实是"),
    ("CROSS_TEXT_INTERPRETATION", r"若采用.{0,12}的框架|以.{0,10}的(视角|框架|立场).{0,8}(读作|来解|看)|用.{0,10}的框架"),
    ("SCHOLARLY_INTERPRETATION", r"某种研究解释认为|有研究(表明|认为|指出)|学界(普遍|一般认为|认为)|有学者(认为|指出)|学术研究认为"),
    ("AUTHOR_COUNTERFACTUAL", r"会(怎么|如何|怎样)(看|想|评价|说)|如果.{0,10}(活到|活在|来到|穿越|见到).{0,8}(今天|今日|现代|当世|当代|现在)|活到今天|想必会|一定会认为|绝不会认为"),
    ("USER_PREMISE", r"你(提出|提到|说|认为|假设|的前提|说的前提)|正如你(所说|认为|提到)|你问的是"),
    ("SPECULATION", r"一种可能的解释是|或许是|也许|可能|大概|猜测|推测|不妨设想"),
    ("UNKNOWN", r"无法(确定|判断|知道)|现有材料(不足|无法)|尚无定论|没有证据表明|不清楚|无从判断"),
]

# 文本意义类解读词（"意味着/象征/隐喻/转变" 等 → 解释性推断, 不是文本事实）
_INTERPRETIVE_RE = re.compile(r"意味着|象征着|隐喻|象征|暗示|反映出|体现了|代表了|说明了|表明|表达了|完成了(?=.*转变)|转变|寓意|读作|解读为|可以理解为")
# 强模态（"一定/必然/毫无疑问" → 即便涉及文本, 也降级为解释/推测, 禁止 SOURCE_FACT）
_STRONG_MODAL_IN_TEXT = re.compile(r"一定|必然|毫无疑问|绝对|无疑|显然是")


class EpistemicClaimClassifier:
    """Claim 分级器（规则版; confidence 恒 None）

    classify(text) → {"claim", "epistemic_type", "confidence": None, "evidence_ids": []}
    """

    def classify(self, text, extra=False):
        t = (text or "").strip()
        ctype = self._cue_match(t)
        strong_modal = bool(_STRONG_MODAL_IN_TEXT.search(t)) and bool(_INTERPRETIVE_RE.search(t))
        # 强模态的文本解读 → 解释性判断, 而非文本事实（"一定完成了转变" ≠ 原文所说）
        if ctype in ("TEXTUAL_INFERENCE",) and strong_modal:
            ctype = "TEXTUAL_INFERENCE"
        evidence_ids = self._evidence_ids(t)
        out = {"claim": t, "epistemic_type": ctype, "confidence": None, "evidence_ids": evidence_ids}
        if extra:
            out["strong_modal"] = strong_modal
        return out

    def _cue_match(self, t):
        if not t:
            return "UNKNOWN"
        for ctype, pat in _CLAIM_CUES:
            if re.search(pat, t):
                return ctype
        # 文本意义类解读（无引文/出处标记, 但有"意味着/隐喻/象征…"）→ 解释性推断
        if _INTERPRETIVE_RE.search(t):
            return "TEXTUAL_INFERENCE"
        return "UNKNOWN"

    def _evidence_ids(self, t):
        """从文本提取可核验出处锚点（《书名》/章节引号块）"""
        ids = []
        for m in re.finditer(r"《([^》]{1,40})》", t):
            ids.append(f"book:{_strip_marks(m.group(1))}")
        for m in re.finditer(r"[“\"]([^”\"]{4,80})[”\"]", t):
            ids.append(f"quote:{m.group(1)[:20]}")
        return ids[:8]
    # O5 (D6): split_sentences method 已删——与模块级 _split_sentences 重复,
    # 唯一消费者 evaluation_suite 改用模块函数。


# ═══════════════════════════════════════════════════════
# 4. ClaimEvidenceBinder —— Claim 定级 + claim → evidence 绑定
# ═══════════════════════════════════════════════════════
def _split_sentences(text):
    return [s.strip() for s in re.split(r"[。！？；!?;\n]+", text or "") if s.strip()]


def _bind_claim(sent, retrieved):
    """claim → evidence_ids: 引用标注精确匹配 + 片段重叠（TEXTUAL_INFERENCE 允许多条）"""
    ids = []
    snorm = _norm(sent)
    markers = _cite_markers(sent)
    for ev in retrieved:
        if ev.get("source_type") != "primary" or not ev.get("evidence_id"):
            continue
        hit = any(_book_match(ev["book"], b) and _chapter_match(ev["chapter"], ch)
                  for b, ch in markers)
        if not hit and len(_norm(ev.get("snippet") or "")) >= 10:
            sn = _norm(ev["snippet"])[:160]
            hit = any(s in snorm for s in _shingles(sn))
        if hit:
            ids.append(ev["evidence_id"])
    return ids


def _claims_from_answer(answer, retrieved):
    """回答正文 → Claim 列表: {claim_id, text, epistemic_type, role, evidence_ids, direct_evidence}
    SPECULATION 一律不绑定 DIRECT evidence（不得伪装拥有文本直接支持）
    role（Patch 1.1 P6）: 主张角色（TEXTUAL_CLAIM/RECONSTRUCTION/INTERPRETIVE_CLAIM/
    LATER_CRITICISM/AGENT_SYNTHESIS）——内部语义, 供语气校准与审计, 不是正文标题。"""
    classifier = EpistemicClaimClassifier()
    claims = []
    seq = 0
    for sent in _split_sentences(answer):
        if len(sent) < _MIN_CLAIM_LEN or _SKIP_CLAIM_RE.search(sent):
            continue
        seq += 1
        cid = f"claim_{seq}"
        ctype = classifier.classify(sent, extra=False)["epistemic_type"]
        # 回答侧无语境线索但带引用标注 → 文本事实断言（定位来源的陈述）
        if ctype == "UNKNOWN" and _CITE_RE.search(sent):
            ctype = "SOURCE_FACT"
        bind_ids = _bind_claim(sent, retrieved)
        if ctype == "SPECULATION":
            bind_ids = []   # 推测不得伪装拥有 DIRECT evidence（citation 虽在正文, 不作直接支撑）
        claims.append({
            "claim_id": cid,
            "text": sent[:200],
            "epistemic_type": ctype,
            "role": _claim_role(sent, ctype),
            "evidence_ids": bind_ids,
            "direct_evidence": bool(bind_ids),
        })
    return claims


# P6: 主张角色判定线索（句级; 顺序 = 判定优先级）。纯表示层——Answer Composer/
# 审计消费, 绝不映射为可见标题或免责声明模板。
_CLAIM_ROLE_CUES = [
    ("AGENT_SYNTHESIS", re.compile(
        r"我认为|我的判断|我的结论|综合来看|合在一起|在我看来|我会(把|认为|说|概括)"
        r"|我把它概括|付出的代价(是|在于)")),
    ("LATER_CRITICISM", re.compile(
        r"后来(如|的)?|后世|批评者|反对者|所提出的批评|对康德的批评|黑格尔(后来)?(批评|批判|指责)"
        r"|叔本华(等|后来)?|尼采(后来)?(批评|指责)|后学")),
    ("RECONSTRUCTION", re.compile(
        r"可以把这一?步?理解|不妨(把|将|重构)|重构(出来|为)|隐含前提|补(全|足)这一步"
        r"|论证(在|是)这里|这一步(是|等于)在")),
    ("INTERPRETIVE_CLAIM", re.compile(
        r"一(个|种)(有力|可行|可成立)?的?(读法|解释|理解)|另一种读法|读法(是|之一)"
        r"|可以读作|解读为|通常(被)?解读|一种常见的?误?读")),
]


def _claim_role(sent, epistemic_type):
    """句级主张角色（P6）: 先句法线索, 后知识论类型映射"""
    for role, rx in _CLAIM_ROLE_CUES:
        if rx.search(sent or ""):
            return role
    if epistemic_type in ("SOURCE_FACT", "SOURCE_QUOTE"):
        return "TEXTUAL_CLAIM"
    if epistemic_type == "SPECULATION":
        return "AGENT_SYNTHESIS"
    return "INTERPRETIVE_CLAIM"


# ═══════════════════════════════════════════════════════
# 5. CitationValidity —— 未核验引用检测（【《》】但从未检索到）
# ═══════════════════════════════════════════════════════
def _unverified_citations(answer, retrieved):
    """回答中出现的引用标注, 若在检索池中找不到对应原典 → 未核验（不入引用面板）
    reason: book_not_retrieved / chapter_not_retrieved"""
    primary = [e for e in retrieved if e.get("source_type") == "primary"]
    out = []
    for b, ch in _cite_markers(answer):
        if _norm(b) == "":
            continue
        if any(_book_match(ev["book"], b) for ev in primary):
            if not any(_book_match(ev["book"], b) and _chapter_match(ev["chapter"], ch)
                       for ev in primary):
                out.append({"book": b, "chapter": ch, "reason": "chapter_not_retrieved"})
            continue
        out.append({"book": b, "chapter": ch, "reason": "book_not_retrieved"})
    return out


# ═══════════════════════════════════════════════════════
# 6. 编排: build_evidence_contract / 日志
# ═══════════════════════════════════════════════════════
def _project(ev):
    """used_evidence → 引用面板项（向后兼容字段: book/chapter/book_id/chapter_idx）"""
    return {
        "evidence_id": ev["evidence_id"],
        "book": ev["book"], "chapter": ev["chapter"],
        "book_id": ev["book_id"], "chapter_idx": ev["chapter_idx"],
        "author": ev["author"], "source_type": ev["source_type"],
        "used": True,
        "supports_claim_ids": list(ev.get("supports_claim_ids") or []),
    }


def build_evidence_contract(tool_log, answer, agent="general", language="zh"):
    """构建 Evidence Contract（纯计算, 不调 LLM）

    语义: retrieved ⊇ candidate ⊇ used; visible_citation ⊆ used。
      retrieved_evidence: 检索候选全集（含 used=False 的未用候选）
      candidate_evidence: 与回答正文对齐、可能支持 claim 的候选
      used_evidence:      最终可见 claim 实际依赖的候选
      claims:             Claim 列表（知识论分级 + claim role + evidence_ids 绑定）
      citations:          引用面板内容 = used_evidence 投影（前端只消费这里）
      unverified_citations: 回答中出现但检索池无法定位的引用（单列, 不入面板）
      retrieved_count / used_count
    """
    ans = answer or ""
    ans_norm = _norm(ans)
    markers = _cite_markers(ans)
    retrieved = _dedup(_extract_candidates(tool_log))
    for ev in retrieved:
        cand = _evidence_used(ev, ans_norm, markers, ans)
        ev["candidate"] = cand
        ev["used"] = cand
    used = [e for e in retrieved if e["used"]]
    claims = _claims_from_answer(ans, retrieved)
    evmap = {e["evidence_id"]: e for e in retrieved}
    for c in claims:
        for eid in c["evidence_ids"]:
            ev = evmap.get(eid)
            if ev is not None:
                ev["supports_claim_ids"].append(c["claim_id"])
    citations = [_project(e) for e in used]
    unverified = _unverified_citations(ans, retrieved)
    _log_record({"phase": "post", "agent": agent, "language": language,
                 "retrieved_count": len(retrieved), "used_count": len(used),
                 "candidate_count": sum(1 for e in retrieved if e.get("candidate")),
                 "claim_count": len(claims),
                 "claim_roles": {r: sum(1 for c in claims if c["role"] == r)
                                 for r in ("TEXTUAL_CLAIM", "RECONSTRUCTION",
                                           "INTERPRETIVE_CLAIM", "LATER_CRITICISM",
                                           "AGENT_SYNTHESIS")},
                 "speculation_claims": sum(1 for c in claims if c["epistemic_type"] == "SPECULATION"),
                 "unverified_citations": len(unverified),
                 "answer_len": len(ans)})
    return {
        "retrieved_evidence": retrieved,
        "candidate_evidence": [e for e in retrieved if e.get("candidate")],
        "used_evidence": used,
        "claims": claims,
        "citations": citations,
        "unverified_citations": unverified,
        "retrieved_count": len(retrieved),
        "used_count": len(used),
    }


# ═══════════════════════════════════════════════════════
# 7. Citation Sanitizer（O5 裁剪: 只读 audit 断言——零改写零降级零追加）
# ═══════════════════════════════════════════════════════


def sanitize_citations(answer, contract=None, tool_log=None):
    """对最终可见正文执行引用核验断言（只读——不改写正文）:
      verified_citations   used_evidence 命中的正式引用
      unverified_before    未命中的正式引用（发布前残留披露——正常路径下 validator 已把
                           未核验引用以 UNVERIFIED_CITATION 打回 same-agent repair,
                           此处仅断言并记日志, 供 done.citation_sanitize 审计）
      actions              逐条动作（verified / unverified）
    原 rebind/downgrade 文本改写分支已删——sanitized_text 自 O2 起即被丢弃, 无消费者;
    未核验引用的处置权在 final_validator（结构化 issue）, 不在改写器。"""
    ans = answer or ""
    if contract is None:
        contract = build_evidence_contract(tool_log or [], ans)
    used = contract.get("used_evidence") or []
    actions, verified, unverified = [], [], []
    for _start, _end, book, chapter, _kind in iter_cite_spans(ans):
        if any(_book_match(ev["book"], book) and _chapter_match(ev["chapter"], chapter)
               for ev in used):
            actions.append({"book": book, "chapter": chapter, "action": "verified"})
            verified.append({"book": book, "chapter": chapter})
        else:
            actions.append({"book": book, "chapter": chapter, "action": "unverified"})
            unverified.append({"book": book, "chapter": chapter})
    _log_record({"phase": "sanitize", "answer_len": len(ans),
                 "verified": len(verified), "unverified_before": len(unverified),
                 "actions": [a["action"] for a in actions]})
    return {
        "verified_citations": verified,
        "unverified_before": unverified,
        "actions": actions,
    }


# ══ O2: 原 LiveCitationSanitizer（未核验 formal citation 流式降级为一般提及）已删除。
# 引用资格判断纯函数化为 final_validator.check_citations——只检测、不降级,
# 未核验引用以 UNVERIFIED_CITATION 打回同一个 Main Agent 修复。

def _log_record(rec):
    try:
        rec = dict(rec)
        rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with _log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
