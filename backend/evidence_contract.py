# -*- coding: utf-8 -*-
"""Evidence Contract（Phase 3）——检索到的 ≠ 回答用的

解决第三个核心问题: 检索命中了 20 条 ≠ 最终回答真的用了 20 条。
此前"引用来源"面板把 search_books 命中的前 N 条全部当作引用展示——用户会把
retrieval candidates 误解为 answer evidence。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  EvidenceExtractor        从 tool_log 提取证据候选 → retrieved_evidence
                            （search_books 命中 / get_chapter 阅读 / 语料回响 入池;
                             websearch 等 secondary 仅审计, 不进引用面板）
  EvidenceUsageVerifier    回答正文 ↔ 证据的确定性对齐（引用标注精确匹配 + 片段
                            shingle 重叠）→ used_evidence（retrieved 且 used）
  ClaimEvidenceBinder      Claim 抽取与知识论定级（复用 epistemic_guard 分级线索）+
                            claim → evidence 绑定; SPECULATION 绝不绑定 DIRECT evidence
  CitationValidity         引用【《书名》·章节】必须能映射到 used_evidence;
                            仅"检索过"没有资格进入引用面板; 未核验引用单列
                            unverified_citations（不入面板）

Phase 3 边界（见任务书）:
  - 不改 Graph / Memory / Persona Snapshot / 矢量库 / 工具注册表 / 流式协议
  - done 事件新增 evidence 字段; citations 字段改投影 used_evidence（面板向后兼容）
  - 纯规则生效, 异常只降级为跳过, 绝不影响主流程（与 Phase 1/2 同机制）

用法（engine_langgraph.stream_agent 内, 应答完成后）:
  contract = build_evidence_contract(tool_log, full_answer, agent, language)
  citations = contract["citations"]     # 仅 used_evidence 的投影
"""
import json
import re
import threading
import time
from pathlib import Path

from epistemic_guard import EpistemicClaimClassifier   # 复用 Claim 知识论分级线索（单一真源）

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


def _extract_candidates(tool_log):
    """tool_log → 证据候选列表（保持检索顺序; 仅白名单工具的结果入池）"""
    cands = []
    for i, tc in enumerate(tool_log or []):
        name = tc.get("name") or ""
        rf = tc.get("result_full")
        if name not in PRIMARY_TOOLS and name not in SECONDARY_TOOLS:
            continue
        if not isinstance(rf, dict):
            continue
        if name == "search_books":
            for item in rf.get("results") or []:
                if not isinstance(item, dict) or not item.get("book_title"):
                    continue
                ev = _base_evidence(len(cands) + 1, f"src_search_{i}")
                ev.update({
                    "book": item.get("book_title") or "",
                    "chapter": item.get("chapter_title") or "",
                    "book_id": item.get("book_id") or "",
                    "chapter_idx": item.get("chapter_idx", -1),
                    "author": item.get("author") or "",
                    "snippet": (item.get("snippet") or "")[:220],
                    "score": float(item.get("score") or 0),
                })
                cands.append(ev)
        elif name == "get_chapter" and rf.get("book_id"):
            try:
                from routes.agent import book_by_id
                b = book_by_id(rf.get("book_id")) or {}
            except Exception:
                b = {}
            ev = _base_evidence(len(cands) + 1, f"src_chapter_{i}")
            ev.update({
                "book": b.get("title", "") or rf.get("book_title") or "",
                "chapter": rf.get("title") or rf.get("chapter_title") or "",
                "book_id": rf.get("book_id", ""),
                "chapter_idx": rf.get("chapter_idx", -1),
                "author": b.get("author", ""),
                "snippet": (rf.get("text") or "")[:220],
                "score": 1.0,
            })
            cands.append(ev)
        elif name in ("philosopher_corpus", "philosopher_quote"):
            for echo in (rf.get("echoes") or rf.get("quotes") or []):
                if not isinstance(echo, dict) or not echo.get("book"):
                    continue
                ev = _base_evidence(len(cands) + 1, f"src_corpus_{i}")
                ev.update({
                    "book": echo.get("book") or "",
                    "chapter": echo.get("chapter") or "",
                    "author": "",
                    "snippet": (echo.get("text") or echo.get("snippet") or "")[:220],
                    "score": float(echo.get("score") or 0),
                })
                cands.append(ev)
        elif name in SECONDARY_TOOLS:
            # 外网结果仅审计: 无《书名》定位能力, 永远不进引用面板
            ev = _base_evidence(len(cands) + 1, f"src_web_{i}", source_type="secondary")
            ev.update({
                "snippet": (rf.get("content") or rf.get("text") or str(rf))[:220],
            })
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
# Patch 1.1 (P3) 语义重定义:
#   retrieved_evidence  = 检索到（候选全集）
#   candidate_evidence  = 可能支持 claim（正文对齐: 引用标注/片段重叠命中）
#   used_evidence       = 最终可见 claim 实际依赖（candidate ∩ 来源约束可admissible）
#   visible_citation    ⊆ used_evidence（引用面板/正式引用只从 used 投影）
#   请求 PRIMARY_ONLY / AUTHOR_ONLY 时: 二手研究可存在于 retrieved/candidate,
#   但 used=false / visible=false——不是靠 renderer 隐藏, 而是契约层排除。
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


# 作者不明/集体署名（无法建立二手性 → 保留可admissible, 防过度排除）
_UNKNOWN_AUTHOR_RE = re.compile(r"^\s*(佚名|无名氏|匿名|unknown|compiled|编)\s*$", re.I)


def _author_matches_subject(author, subject_authors):
    """证据作者是否为提问对象本人 → True(本人) / False(确定非本人=二手) / None(无法判定)"""
    a = _norm(author)
    if not a or _UNKNOWN_AUTHOR_RE.match(author or ""):
        return None
    for s in subject_authors or []:
        sn = _norm(s)
        if sn and (sn in a or a in sn):
            return True
    return False


def _admissible(ev, source_constraint, subject_authors):
    """P3: 来源约束下的 used 准入。PRIMARY_ONLY/AUTHOR_ONLY 时, 已知作者与提问对象
    不符的证据 = 二手研究 → 不得进入 used_evidence（retrieved/candidate 可保留）。
    提问对象未知（subject_authors 为空）时不做排除——无法建立二手性, 防过度排除。"""
    if source_constraint not in ("PRIMARY_ONLY", "AUTHOR_ONLY"):
        return True, ""
    if not subject_authors:
        return True, ""
    m = _author_matches_subject(ev.get("author") or "", subject_authors)
    if m is False:
        return False, "secondary_source"
    return True, ""


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


def build_evidence_contract(tool_log, answer, agent="general", language="zh",
                            source_constraint=None, subject_authors=None):
    """构建 Evidence Contract（纯计算, 不调 LLM）

    Patch 1.1 (P3) 语义: retrieved ⊇ candidate ⊇ used; visible_citation ⊆ used。
      retrieved_evidence: 检索候选全集（含 used=False 的未用候选）
      candidate_evidence: 与回答正文对齐、可能支持 claim 的候选
      used_evidence:      最终可见 claim 实际依赖（candidate ∩ 来源约束可admissible）
      claims:             Claim 列表（知识论分级 + claim role + evidence_ids 绑定）
      citations:          引用面板内容 = used_evidence 投影（前端只消费这里）
      secondary_excluded: PRIMARY_ONLY/AUTHOR_ONLY 约束下被排除的二手证据（审计用）
      unverified_citations: 回答中出现但检索池无法定位的引用（单列, 不入面板）
      retrieved_count / used_count
    """
    ans = answer or ""
    ans_norm = _norm(ans)
    markers = _cite_markers(ans)
    retrieved = _dedup(_extract_candidates(tool_log))
    secondary_excluded = []
    for ev in retrieved:
        cand = _evidence_used(ev, ans_norm, markers, ans)
        ev["candidate"] = cand
        ok, reason = _admissible(ev, source_constraint, subject_authors)
        ev["used"] = bool(cand and ok)
        if cand and not ok:
            ev["excluded_reason"] = reason
            ev["used"] = False
            secondary_excluded.append(ev)
    used = [e for e in retrieved if e["used"]]
    claims = _claims_from_answer(ans, retrieved)
    evmap = {e["evidence_id"]: e for e in retrieved}
    for c in claims:
        for eid in c["evidence_ids"]:
            ev = evmap.get(eid)
            if ev is not None:
                ev["supports_claim_ids"].append(c["claim_id"])
    # P3: 二手证据不得绑定任何 claim 的 direct evidence（used=false → 不作支撑）
    excluded_ids = {e["evidence_id"] for e in secondary_excluded}
    for c in claims:
        if excluded_ids:
            c["evidence_ids"] = [i for i in c["evidence_ids"] if i not in excluded_ids]
            c["direct_evidence"] = bool(c["evidence_ids"])
    citations = [_project(e) for e in used]
    unverified = _unverified_citations(ans, retrieved)
    _log_record({"phase": "post", "agent": agent, "language": language,
                 "retrieved_count": len(retrieved), "used_count": len(used),
                 "candidate_count": sum(1 for e in retrieved if e.get("candidate")),
                 "secondary_excluded": len(secondary_excluded),
                 "source_constraint": source_constraint or "NONE",
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
        "secondary_excluded": secondary_excluded,
        "unverified_citations": unverified,
        "retrieved_count": len(retrieved),
        "used_count": len(used),
    }


# ═══════════════════════════════════════════════════════
# 7. Phase S (S4): Citation Sanitizer —— 最终输出硬约束
#    visible formal citations ⊆ verified used_evidence citations
# ═══════════════════════════════════════════════════════
_CITE_REPLACE_ZH = "（引用核验说明：上文标注【《{}》·{}】的出处未能通过原典库核验，已按一般提及处理，不作为正式引用。）"
_CITE_REPLACE_EN = ("(Citation note: the passage marked 【《{b}》· {c}】 above could not be verified against "
                    "the corpus; it is treated as a general mention, not a formal citation.)")


def _sentence_around(text, pos, radius=60):
    """引用标注所在句（含引号摘引的判定窗口）"""
    lo = max(0, pos - radius)
    hi = min(len(text), pos + radius)
    return text[lo:hi]


def sanitize_citations(answer, contract=None, tool_log=None):
    """对回答正文执行引用净化（最终输出硬约束）:

    流程: 提取正文正式引用 → 与 Evidence Contract / used_evidence 对齐
      verified（used_evidence 命中）           → 保留
      未 verified:
        ① 存在可靠 evidence（同书检索片段 + 句中引号摘引命中）→ 重新绑定为书级引用
        ② 否则 → 移除正式引用格式（【】剥除, 降级为一般书名提及）

    返回:
      sanitized_text:        净化后的正文（正式引用 ⊆ verified）
      verified_citations:    保留的正式引用
      unverified_before:     净化前未核验的引用
      actions:               逐条动作（verified / rebound_book_level / downgraded_plain_mention）
    """
    ans = answer or ""
    if contract is None:
        contract = build_evidence_contract(tool_log or [], ans)
    used = contract.get("used_evidence") or []
    retrieved = contract.get("retrieved_evidence") or []
    spans = iter_cite_spans(ans)   # T13-A: canonical + 作者·《作品》变体统一覆盖
    actions, verified, unverified = [], [], []
    new_text = ans
    for start, end, book, chapter, kind in reversed(spans):   # 从后往前替换, 保索引稳定
        ok = any(_book_match(ev["book"], book) and _chapter_match(ev["chapter"], chapter)
                 for ev in used)
        if ok:
            actions.append({"book": book, "chapter": chapter, "action": "verified"})
            verified.append({"book": book, "chapter": chapter})
            continue
        unverified.append({"book": book, "chapter": chapter})
        # ① 重新绑定: 同书检索片段 + 句中引号摘引命中 → 降级为书级引用【《书》】(仍可核验)
        sent = _sentence_around(ans, start)
        rebound = False
        for ev in retrieved:
            if ev.get("source_type") != "primary" or not ev.get("book"):
                continue
            if not _book_match(ev["book"], book):
                continue
            sn = _norm(ev.get("snippet") or "")
            if len(sn) < 10:
                continue
            quotes = re.findall(r"[“\"]([^”\"]{10,80})[”\"]", sent)
            if any(_norm(q) and _norm(q) in sn for q in quotes):
                new_text = new_text[:start] + f"【《{book}》】" + new_text[end:]
                actions.append({"book": book, "chapter": chapter,
                                "action": "rebound_book_level", "reason": "quote_matches_retrieved_snippet"})
                rebound = True
                break
        if rebound:
            continue
        # ② 移除正式引用格式（降级为一般书名提及; 作者·《作品》变体保留作者署名）
        plain = f"《{book}》"
        if kind == "author_work":
            # 还原作者名（原文【作者·《作品》】→ 作者《作品》）
            am = _CITE_AUTHOR_WORK_RE.match(ans[start:end])
            plain = f"{am.group(1)}《{book}》" if am else f"《{book}》"
        new_text = new_text[:start] + plain + new_text[end:]
        actions.append({"book": book, "chapter": chapter,
                        "action": "downgraded_plain_mention", "reason": "no_reliable_evidence"})
    _log_record({"phase": "sanitize", "answer_len": len(ans),
                 "verified": len(verified), "unverified_before": len(unverified),
                 "actions": [a["action"] for a in actions]})
    return {
        "sanitized_text": new_text,
        "verified_citations": verified,
        "unverified_before": unverified,
        "actions": actions,
    }


def build_citation_disclosure(report, language="zh"):
    """净化报告 → 正文可见的降级说明（未核验引用降级为解释性陈述）; 无可降级返回 []"""
    out = []
    downgraded = [a for a in (report or {}).get("actions", [])
                  if a.get("action") == "downgraded_plain_mention"]
    for a in downgraded:
        if language == "en":
            out.append(_CITE_REPLACE_EN.format(b=a.get("book"), c=a.get("chapter")))
        else:
            out.append(_CITE_REPLACE_ZH.format(a.get("book"), a.get("chapter")))
    return out


# ═══════════════════════════════════════════════════════
# B4-B: LiveCitationSanitizer —— final render 前的引用实时核验（Patch 1, 2026-08-31）
#   visible formal citations ⊆ verified used evidence:
#   正文在进入 final render 前逐标记查证——未核验的正式引用在流式输出时即被降级为
#   一般书名提及（保留必要 paraphrase）, 正文里根本不出现未验证的【《书》·章】,
#   也不再追加"引用核验说明"式补丁尾注。
# ═══════════════════════════════════════════════════════
class LiveCitationSanitizer:
    """流式引用核验器（生命周期 = 单次 invocation 的最终回答阶段）

    push(text) 逐段处理: 完整引用标记【《书》·章】→ 与 primary 检索证据查证;
      verified（book+chapter 双向匹配）→ 保留; 未核验 → 降级为《书》一般提及。
    未闭合标记缓冲（跨 chunk）; flush() 释放残留（未闭合 = 无正式引用, 按原文保留）。
    tool_log 以引用方式传入——最终回答开始流式时检索已完成, 首次 push 时构建查证池;
    fallback_log 兜底（引擎展示用 tool_log; tools_node 直连路径两者等价）。
    """

    def __init__(self, tool_log_ref, language="zh", fallback_log=None,
                 source_constraint=None, subject_authors=None):
        self._log_ref = tool_log_ref
        self._fallback = fallback_log
        self._constraint = source_constraint or None
        self._subjects = subject_authors or []
        self._primary = None          # 懒构建: [(book, chapter)] 归一化
        self._buf = ""
        self.verified = 0
        self.downgraded = 0

    def _sources(self):
        if self._primary is None:
            try:
                merged = list(self._log_ref) if self._log_ref else []
                if self._fallback:
                    merged += [t for t in self._fallback if t not in merged]
                cands = _dedup(_extract_candidates(merged))
                # P3: PRIMARY_ONLY/AUTHOR_ONLY 约束下, 二手证据的正式引用同样降级
                # （visible_citation ⊆ used_evidence 的流式侧保证）
                self._primary = [(c["book"], c.get("chapter") or "") for c in cands
                                 if c.get("source_type") == "primary" and c.get("book")
                                 and _admissible(c, self._constraint, self._subjects)[0]]
            except Exception:
                self._primary = []
        return self._primary

    def _verified(self, book, chapter):
        return any(_book_match(ev_b, book) and _chapter_match(ev_c, chapter)
                   for ev_b, ev_c in self._sources())

    def push(self, text):
        out = ""
        self._buf += text or ""
        while True:
            # T13-A: canonical 与 作者·《作品》两种模式取最早出现者
            m1 = _CITE_RE.search(self._buf)
            m2 = _CITE_AUTHOR_WORK_RE.search(self._buf)
            m, kind = (m1, "canonical") if (m1 and (not m2 or m1.start() <= m2.start())) else (m2, "author_work")
            if not m:
                break
            out += self._buf[:m.start()]
            if kind == "author_work":
                author, book, chapter = m.group(1), m.group(2), ""
            else:
                author, book, chapter = "", *_split_book_chapter(m.group(1), m.group(2))
            if book and self._verified(book, chapter):
                out += m.group(0)
                self.verified += 1
            else:
                # 未核验 → 降级为一般书名提及（保留必要 paraphrase; 作者署名保留）;
                # 若紧邻上文已含《书》, 不重复堆叠
                plain = (f"{author}《{book}》" if author else f"《{book}》") if book else ""
                if plain and out.rstrip().endswith(plain):
                    plain = ""
                out += plain
                self.downgraded += 1
            self._buf = self._buf[m.end():]
        # 尾部可能被 chunk 切碎的未闭合标记 → 缓冲（跨 chunk; 防半截标记泄漏）
        o = self._buf.rfind("【")
        if o >= 0 and "】" not in self._buf[o:]:
            out += self._buf[:o]
            self._buf = self._buf[o:]
        else:
            out += self._buf
            self._buf = ""
        return out

    def flush(self):
        out, self._buf = self._buf, ""
        return out

    def snapshot(self):
        return {"verified": self.verified, "downgraded": self.downgraded}


# ── 运行时记录（backend/data/ 已 gitignore, 纯观察/审计用; 失败静默）──
_log_lock = threading.Lock()


def _log_record(rec):
    try:
        rec = dict(rec)
        rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with _log_lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
