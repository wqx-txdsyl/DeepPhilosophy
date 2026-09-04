# -*- coding: utf-8 -*-
"""Quote Bound（Phase T.1, T1.1-D/E/F/G/H）——逐字引文绑定与渲染约束

真实回归（Phase T 后）: Citation Sanitizer 只约束 formal citation（【《书》·章】）,
模型可以输出一整段"原文" blockquote 然后写"根据记忆，未经核验"——未核验的逐字文本
照样进入用户可见正文，甚至把相邻章句拼接（A 段开头 + B 段结尾）。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  extract_quotes         用户可见文本 → verbatim-like 引文清单
                         （markdown blockquote / 引导词引文「原文是/写道/原话…」/
                          中文引号长文本）
  evidence_spans         raw_tool_log → 可核验证据 span 池（D4: 薄委托
                         evidence_contract.build_evidence_pool——raw_tool_log
                         字段映射单一真源; 此处只组装 quote 核验需要的
                         units/source_type 形状: get_chapter 全文按行分段）
  verify_quote           引文 ↔ 证据 span 逐字核验:
                           VERIFIED_EXACT   归一后连续出现在单一 span（拼接在此即失败）
                           VERIFIED_NEAR    覆盖率 ≥ NEAR_THRESHOLD（近似措辞）
                           MEMORY_ONLY      无证据支撑（不得渲染为原文 blockquote）
                         + stitched 标志: 前半/后半分别命中不同 span（T1.1-F 跨段拼接）
  audit_quotes           最终正文审计（done 事件 + 回归断言用）

边界: MEMORY_HINT 不是 EVIDENCE（T1.1-E）——检索片段命中只能定位，不能支撑逐字引用；
span 池里 get_chapter 全文与片段同池，但逐字核验天然由连续包含判定兜底。
O5: verify-later 反模式检测正则已删除（生产零消费者——该检查随 O4-RP1
check_consistency 一并移除）。
"""
import re

import evidence_contract as EC

# ── 归一化（逐字比对口径: 只保留文字/数字, 剥全部标点空白——连续性是硬条件）──
_PUNCT_RE = re.compile(r"[^\w\u4e00-\u9fff]+")


def norm_q(s):
    return _PUNCT_RE.sub("", s or "")


# 引文进入 quote bound 管控的最短归一长度（更短的普通短语引用不受限）
QUOTE_MIN_NORM = 8
# VERIFIED_NEAR 覆盖率阈值（引文 shingle 在单一 span 的最大覆盖率）
NEAR_THRESHOLD = 0.62
_SHINGLE = 7

BLOCKQ_LINE_RE = re.compile(r"^\s{0,3}>\s?")
# 引导词: 明确把后文标为"原文"的措辞
LEADIN_RE = re.compile(
    r"(原文(?:是|为|如下)|原句(?:是|为|如下)|原话(?:是|为)|写道|写道：|说道|他说|她说道?)\s*[:：]?\s*[“\"]")
# 可见的核验披露标记（已声明未核验的引文 → 记为 DISCLOSED 而非隐瞒）
DISCLOSED_RE = re.compile(r"未经.{0,10}(核验|核对)|未在.{0,12}库.{0,6}(核验|定位|找到)|凭记忆|根据记忆|记忆引述|未逐字核验|NOT_FOUND")


# ═══════════════════════════════════════════════════════
# 1. 引文提取
# ═══════════════════════════════════════════════════════
def extract_quotes(text):
    """用户可见文本 → verbatim-like 引文清单
    kind: blockquote（markdown 引用块）| leadin（引导词+引号）| quoted（中文引号长文本）
    每条: {quote_claim_id, kind, text, line_count}"""
    out = []
    seq = 0
    lines = (text or "").split("\n")
    i = 0
    while i < len(lines):
        if BLOCKQ_LINE_RE.match(lines[i]):
            buf = []
            while i < len(lines) and BLOCKQ_LINE_RE.match(lines[i]):
                buf.append(BLOCKQ_LINE_RE.sub("", lines[i], count=1).strip())
                i += 1
            body = "".join(buf).strip()
            if body:
                seq += 1
                out.append({"quote_claim_id": f"quote_{seq}", "kind": "blockquote",
                            "text": body, "line_count": len(buf)})
            continue
        i += 1
    # 引导词引文 + 中文引号长文本（同一行内闭合才取; 跨行由 blockquote 覆盖）
    # 口径: 弯引号 “ ” 内的长文本即视为 verbatim-like; 直引号 " 只在引导词后才是引文
    #（模型大量用直引号做 scare quotes（讨论"言"的文本）——逐对直引号之间的正文
    #  会被误捕获为假引文, 真实回归: R1 审计出现 3 条 MEMORY_ONLY 噪声）
    for m in re.finditer(r"[“]([^“”]{10,240})[”]", text or ""):
        body = m.group(1).strip()
        if len(norm_q(body)) < QUOTE_MIN_NORM:
            continue
        head = (text or "")[:m.start()]
        leadin = bool(LEADIN_RE.search(head[-40:]))
        seq += 1
        out.append({"quote_claim_id": f"quote_{seq}",
                    "kind": "leadin" if leadin else "quoted",
                    "text": body, "line_count": 1})
    return out


# ═══════════════════════════════════════════════════════
# 2. 证据 span 池（raw_tool_log → 可核验文本单元）
# ═══════════════════════════════════════════════════════
def evidence_spans(raw_tool_log):
    """tool_log → span 池: [{evidence_id, book, chapter, book_id, chapter_idx,
    source_type, units: [完整原文单元（行=章段）]}]

    D4 薄委托: raw_tool_log 字段映射单一真源 = evidence_contract.build_evidence_pool;
    本函数只做 quote 核验需要的形状适配——chapter 全文按行分段 units,
    检索片段/语料回响为单单元; secondary（websearch）不进逐字核验池;
    核验算法（连续包含/覆盖率/拼接检测）不变。"""
    spans = []
    for e in EC.build_evidence_pool(raw_tool_log):
        kind = e["kind"]
        text = e["text"]
        if kind == "chapter":
            if not text:
                continue
            units = [ln.strip() for ln in text.split("\n") if ln.strip()]
            spans.append({"evidence_id": f"qb_read_{e['entry_index']}",
                          "book": e.get("book_title_raw", ""),
                          "chapter": e.get("chapter_title_raw", ""),
                          "book_id": e["book_id"], "chapter_idx": e["chapter_idx"],
                          "source_type": "primary_read",
                          "units": units or [text]})
        elif kind == "search":
            if not text:
                continue
            spans.append({"evidence_id": f"qb_snip_{e['entry_index']}_{len(spans)}",
                          "book": e["book"], "chapter": e["chapter"],
                          "book_id": e["book_id"], "chapter_idx": e["chapter_idx"],
                          "source_type": "snippet", "units": [text]})
        elif kind == "corpus":
            if not text:
                continue
            spans.append({"evidence_id": f"qb_corp_{e['entry_index']}_{len(spans)}",
                          "book": e["book"], "chapter": e["chapter"], "book_id": "",
                          "chapter_idx": -1, "source_type": "corpus",
                          "units": [text]})
    return spans


# ═══════════════════════════════════════════════════════
# 3. 逐字核验（连续包含 → EXACT; 单 span 覆盖率 → NEAR; 跨 span → 拼接失败）
# ═══════════════════════════════════════════════════════
def _shingles(s, n=_SHINGLE):
    s = s or ""
    return {s[i:i + n] for i in range(len(s) - n + 1)} if len(s) >= n else ({s} if s else set())


def _split_halves(qn):
    """引文归一文本 → 前半/后半（T1.1-F 拼接检测; 归一文本无标点, 取中点切分）"""
    if len(qn) < 12:
        return None
    mid = len(qn) // 2
    return qn[:mid], qn[mid:]


def verify_quote(quote_text, spans):
    """引文 ↔ span 池核验（T1.1-D/F 核心）

    返回 {state: VERIFIED_EXACT|VERIFIED_NEAR|MEMORY_ONLY|SHORT,
          evidence_id, book, chapter, book_id, chapter_idx, source_type,
          coverage, stitched}
    - VERIFIED_EXACT: 归一后引文连续出现在单一 span 的单一单元——拼接天然失败
    - stitched: 前半/后半分别连续命中不同单元 且 无单一单元覆盖达标（T1.1-F）
    """
    qn = norm_q(quote_text)
    res = {"state": "MEMORY_ONLY", "evidence_id": None, "book": None, "chapter": None,
           "book_id": None, "chapter_idx": None, "source_type": None,
           "coverage": 0.0, "stitched": False}
    if len(qn) < QUOTE_MIN_NORM:
        res["state"] = "SHORT"
        return res
    best = None
    for sp in spans or []:
        for u in sp.get("units") or []:
            un = norm_q(u)
            if not un:
                continue
            if qn in un:
                res.update({"state": "VERIFIED_EXACT", "evidence_id": sp["evidence_id"],
                            "book": sp.get("book"), "chapter": sp.get("chapter"),
                            "book_id": sp.get("book_id"), "chapter_idx": sp.get("chapter_idx"),
                            "source_type": sp.get("source_type"), "coverage": 1.0})
                return res
            qsh = _shingles(qn)
            ush = _shingles(un)
            if qsh:
                cov = len(qsh & ush) / len(qsh)
                if best is None or cov > best[0]:
                    best = (cov, sp)
    if best and best[0] >= NEAR_THRESHOLD:
        sp = best[1]
        res.update({"state": "VERIFIED_NEAR", "evidence_id": sp["evidence_id"],
                    "book": sp.get("book"), "chapter": sp.get("chapter"),
                    "book_id": sp.get("book_id"), "chapter_idx": sp.get("chapter_idx"),
                    "source_type": sp.get("source_type"), "coverage": round(best[0], 2)})
        return res
    # T1.1-F: 拼接检测——前半与后半各自连续命中、但来自不同单元
    # （相邻章句常在同一章文本的两个段落单元里——比较 (span, unit) 身份而非仅 span）
    halves = _split_halves(qn)
    if halves:
        hit_units = []
        for hq in halves:
            found = None
            for sp in spans or []:
                for ui, u in enumerate(sp.get("units") or []):
                    un = norm_q(u)
                    if len(hq) >= 6 and hq in un:
                        found = (sp["evidence_id"], ui, sp.get("book"), sp.get("chapter"))
                        break
                if found:
                    break
            hit_units.append(found)
        if all(hit_units) and hit_units[0][:2] != hit_units[1][:2]:
            res["stitched"] = True
            res["state"] = "MEMORY_ONLY"
    return res


# ═══════════════════════════════════════════════════════
# 5. 最终正文审计（done 事件 + 回归断言）
# ═══════════════════════════════════════════════════════
def audit_quotes(answer, raw_tool_log):
    """最终可见正文 → 引文核验审计（逐条 + 汇总）"""
    spans = evidence_spans(raw_tool_log)
    entries = []
    for q in extract_quotes(answer):
        v = verify_quote(q["text"], spans)
        disclosed = bool(DISCLOSED_RE.search(
            (answer or "")[max(0, (answer or "").find(q["text"])):][:len(q["text"]) + 120]))
        entries.append({
            "quote_claim_id": q["quote_claim_id"], "kind": q["kind"],
            "preview": q["text"][:60],
            "verification_state": v["state"] if v["state"] != "SHORT" else "SHORT",
            "source_evidence_id": v["evidence_id"],
            "source_book": v["book"], "source_chapter": v["chapter"],
            "stitched": v["stitched"], "coverage": v["coverage"],
            "disclosed": disclosed,
            "unverified_blockquote": bool(q["kind"] == "blockquote"
                                          and v["state"] in ("MEMORY_ONLY",)
                                          and not disclosed),
        })
    summary = {
        "quotes": len(entries),
        "verified_exact": sum(1 for e in entries if e["verification_state"] == "VERIFIED_EXACT"),
        "verified_near": sum(1 for e in entries if e["verification_state"] == "VERIFIED_NEAR"),
        "memory_only": sum(1 for e in entries if e["verification_state"] == "MEMORY_ONLY"),
        "stitched": sum(1 for e in entries if e["stitched"]),
        "unverified_blockquote": sum(1 for e in entries if e["unverified_blockquote"]),
        "memory_only_exact_claim": sum(
            1 for e in entries
            if e["kind"] == "leadin" and e["verification_state"] == "MEMORY_ONLY" and not e["disclosed"]),
    }
    return {"entries": entries, "summary": summary}
