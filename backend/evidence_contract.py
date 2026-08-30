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

# 引用标注提取: 【《书名》·章节】/ 【《书名》】/ 【《书名》 · 章节】
_CITE_RE = re.compile(r"【《([^》]+)》·?([^】]*)】")

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


def _chapter_match(ev_ch, cited_ch):
    """章节双向包含（引用【《书》·前言】而库内章节"前言·1"亦然; 一方缺失=书名级匹配）"""
    a, b = _norm(ev_ch), _norm(cited_ch)
    if not a or not b:
        return True
    if len(a) < 2 or len(b) < 2:
        return a == b
    return a in b or b in a


def _cite_markers(text):
    """从文本抽取全部引用标注 → [(book, chapter)]"""
    return [(m.group(1), m.group(2)) for m in _CITE_RE.finditer(text or "")]


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
    """回答正文 → Claim 列表: {claim_id, text, epistemic_type, evidence_ids, direct_evidence}
    SPECULATION 一律不绑定 DIRECT evidence（不得伪装拥有文本直接支持）"""
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
            "evidence_ids": bind_ids,
            "direct_evidence": bool(bind_ids),
        })
    return claims


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

    返回:
      retrieved_evidence: 检索候选全集（含 used=False 的未用候选）
      used_evidence:      回答实际引用的证据（retrieved & used）
      claims:             Claim 列表（知识论分级 + evidence_ids 绑定）
      citations:          引用面板内容 = used_evidence 投影（前端只消费这里）
      unverified_citations: 回答中出现但检索池无法定位的引用（单列, 不入面板）
      retrieved_count / used_count
    """
    ans = answer or ""
    ans_norm = _norm(ans)
    markers = _cite_markers(ans)
    retrieved = _dedup(_extract_candidates(tool_log))
    for ev in retrieved:
        ev["used"] = _evidence_used(ev, ans_norm, markers, ans)
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
                 "claim_count": len(claims),
                 "speculation_claims": sum(1 for c in claims if c["epistemic_type"] == "SPECULATION"),
                 "unverified_citations": len(unverified),
                 "answer_len": len(ans)})
    return {
        "retrieved_evidence": retrieved,
        "used_evidence": used,
        "claims": claims,
        "citations": citations,
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
    markers = list(_CITE_RE.finditer(ans))
    actions, verified, unverified = [], [], []
    new_text = ans
    for m in reversed(markers):   # 从后往前替换, 保索引稳定
        book, chapter = m.group(1), m.group(2)
        ok = any(_book_match(ev["book"], book) and _chapter_match(ev["chapter"], chapter)
                 for ev in used)
        if ok:
            actions.append({"book": book, "chapter": chapter, "action": "verified"})
            verified.append({"book": book, "chapter": chapter})
            continue
        unverified.append({"book": book, "chapter": chapter})
        # ① 重新绑定: 同书检索片段 + 句中引号摘引命中 → 降级为书级引用【《书》】(仍可核验)
        sent = _sentence_around(ans, m.start())
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
                new_text = new_text[:m.start()] + f"【《{book}》】" + new_text[m.end():]
                actions.append({"book": book, "chapter": chapter,
                                "action": "rebound_book_level", "reason": "quote_matches_retrieved_snippet"})
                rebound = True
                break
        if rebound:
            continue
        # ② 移除正式引用格式（降级为一般书名提及）
        new_text = new_text[:m.start()] + f"《{book}》" + new_text[m.end():]
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
