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
# ── 引文意图边界（O6-RP1 F1 单一真源）──────────────────────────────
# blockquote 逐字 / 行内逐字 / lead-in 逐字（中英文引号形式）共享同一套边界:
# 引号前紧邻的是"把后文标为原文/言语"的引导语（通用句法结构判定）——
#   ① 原文指示词（原文/原句/原话/原言, 可后接 是/为/如下/中）;
#   ② 言说/书写动词（写道/说道/曾说/曰/云/所言/引述… 及 他/她/它/其/又/曾/所+说）;
#   ③ 英文言语动词与 original 指示语（says/said/writes/states/put it/reads/quoted…）,
# 可带冒号, 且必须紧邻开引号（$ 锚定）。
# 不做用户任务意图推断——边界只由候选文本自身的句法结构决定;
# 也不依赖"原文是"这类单一措辞黑名单。副词性固定短语（一般来说/换句话说/
# In general）以"说"结尾但无言语主体, 不构成边界（E 类不误伤护栏）。
LEADIN_RE = re.compile(
    r"(?:"
    r"原文|原句|原话|原言"                                   # 原文指示词
    r"|(?:他|她|它|其|又|曾|所)说(?:道)?"                     # 言说动词（限定主体, 防"来说"误命中）
    r"|写道|说道|曾言|有言|所言|所云|所写|所记"
    r"|引述|引作|记作|云|曰"
    r"|答曰|答道|问道|叹道|喊道|念道|吟道|提道|反驳道|补充道|解释道|回答道"
    r"|\bthe\s+original(?:\s+(?:text|passage|source|version|wording))?\b"
    r"|\boriginal\s+(?:text|passage|source|version|wording)\b"
    r"|\b(?:says|said|writes|wrote|written|states|stated|notes|noted|puts\s+it|put\s+it"
    r"|reads|quotes|quoted|asks|asked|replies|replied|declares|declared"
    r"|affirms|asserts|asserted|proclaims|proclaimed)\b"
    r"|\bquote\b"
    r")(?:是|为|如下|中)?\s*[:：]?\s*$",
    re.IGNORECASE)
# 可见的核验披露标记（已声明未核验的引文 → 记为 DISCLOSED 而非隐瞒）
DISCLOSED_RE = re.compile(r"未经.{0,10}(核验|核对)|未在.{0,12}库.{0,6}(核验|定位|找到)|凭记忆|根据记忆|记忆引述|未逐字核验|NOT_FOUND")


# ═══════════════════════════════════════════════════════
# 1. 引文提取
# ═══════════════════════════════════════════════════════
def _split_quote_citation_suffix(body):
    """Separate trailing formal source labels from quoted words, never interior labels.

    Labels still undergo final_validator.check_citations against the unchanged
    answer. Removing an interior label could accidentally join non-contiguous
    fragments into a verified sentence, so only a complete terminal run counts.
    """
    suffix = re.search(
        rf"(?:\s*(?:{EC._CITE_RE.pattern}|{EC._CITE_AUTHOR_WORK_RE.pattern}))+\s*$",
        body)
    if suffix is None:
        return body, []
    labels = []
    tail = suffix.group(0)
    for match in EC._CITE_RE.finditer(tail):
        book, chapter = EC._split_book_chapter(match.group(1), match.group(2))
        labels.append({"book": book, "chapter": chapter})
    for match in EC._CITE_AUTHOR_WORK_RE.finditer(tail):
        labels.append({"book": match.group(2), "chapter": ""})
    return body[:suffix.start()].rstrip(), labels


def _inline_quote_citation_labels(tail):
    """Only labels immediately following a quoted span can attribute that span."""
    match = re.match(
        rf"(?:\s*(?:{EC._CITE_RE.pattern}|{EC._CITE_AUTHOR_WORK_RE.pattern}))+", tail)
    if match is None:
        return []
    return _split_quote_citation_suffix(match.group(0))[1]


def _illustrative_speech(head, tail):
    """A generic participant's example dialogue makes no literary quote claim.

    Only the general parser opts in. Explicit source labels, works, original
    wording claims and literary attribution always retain evidence checking.
    A bare historical/pronominal attribution is deliberately not exempted.
    """
    local = head.rsplit("\n\n", 1)[-1][-240:]
    if (_inline_quote_citation_labels(tail)
            or re.search(r"《|原文|原句|原话|原言|逐字|写道|曾说|曾言|曰|引述|\b(?:original|verbatim|wrote|writes|quoted)\b",
                         local, re.IGNORECASE)):
        return False
    role = r"(?:伴侣|朋友|父母|孩子|病人|学生|老师|同事|照顾者|被照顾者|陌生人|顾客|店员)"
    return bool(re.search(
        rf"(?:{role}|(?:某个|一个|某位|一位)人)[^。！？\n“”\"]{{0,60}}"
        r"(?:说|说道|问道|答道|回答道)\s*[:：]?\s*$", local)
        or re.search(
            r"\b(?:suppose|imagine|for example)\b[^.!?\n]{0,120}"
            r"\b(?:someone|a friend|a partner|a child|a student|they|he|she)\b"
            r"[^.!?\n]{0,40}\b(?:says|said)\s*:?\s*$", local, re.IGNORECASE))


def extract_quotes(text, *, strict_quote_spans=False):
    """用户可见文本 → verbatim-like 引文清单
    kind: blockquote（markdown 引用块）| leadin（引导词+引号, 逐字主张）|
          quoted（中文引号长文本, 无引导词——scare-quote 契约豁免类）
    每条: {quote_claim_id, kind, text, line_count}

    O6-RP1 F1: 行内扫描同时覆盖弯引号（“ ”）与直引号（" "）形态——
    直引号此前完全不被提取, `原文是："…"` 式行内逐字引文整体逃过校验（FN）;
    且旧 LEADIN_RE 要求引导语自带结尾引号字符, 与 head 截取口径互斥,
    leadin 分类从未触发。现在两种引号形式共用 LEADIN_RE 同一意图边界:
    引导词命中 → leadin（逐字主张, validator 强制核验）; 弯引号无引导词 →
    quoted（既有豁免）; 直引号无引导词 → 不提取（scare quotes 契约不变）。

    strict_quote_spans 由深哲调用方显式启用：引用块尾部完整的来源标签不是
    原文词句，单独记录并核验。默认关闭，既有哲学家路径与修复定位保持兼容。
    char_start/char_end 仍定位原候选中的完整引用块，绝不重写候选。"""
    out = []
    seq = 0
    _text = text or ""
    if strict_quote_spans:
        import deep_web_quotes as web_quotes
    lines = _text.split("\n")
    # 行起始偏移表（O7-E RCA-1 §2: 引文 char_start/char_end——只加 metadata,
    # EXACT/NEAR/MEMORY_ONLY 判定语义与 NEAR_THRESHOLD 零改动）
    _line_off, _acc = [], 0
    for _l in lines:
        _line_off.append(_acc)
        _acc += len(_l) + 1
    i = 0
    while i < len(lines):
        if BLOCKQ_LINE_RE.match(lines[i]):
            buf = []
            i0 = i
            while i < len(lines) and BLOCKQ_LINE_RE.match(lines[i]):
                buf.append(BLOCKQ_LINE_RE.sub("", lines[i], count=1).strip())
                i += 1
            body = "".join(buf).strip()
            citation_labels = []
            citation_urls = []
            if strict_quote_spans:
                body, web_labels, citation_urls = web_quotes.split_suffix(body)
                body, citation_labels = _split_quote_citation_suffix(body)
                citation_labels.extend(web_labels)
                following = _text[_line_off[i]:] if i < len(lines) else ""
                citation_urls.extend(web_quotes.inline_urls(following))
                citation_labels.extend(web_quotes.inline_labels(following))
            if body:
                seq += 1
                # end = 末块行结尾（i 是块后首行; 块行 = i0..i-1）
                _last = max(i0, min(i - 1, len(lines) - 1))
                out.append({"quote_claim_id": f"quote_{seq}", "kind": "blockquote",
                            "text": body, "line_count": len(buf),
                            "char_start": _line_off[i0],
                            "char_end": _line_off[_last] + len(lines[_last])})
                if citation_labels:
                    out[-1]["citation_labels"] = citation_labels
                if citation_urls:
                    out[-1]["citation_urls"] = citation_urls
            continue
        i += 1
    src = text or ""
    taken = []   # 已捕获区间（弯/直两次扫描防重复捕获同一闭合域）
    # 弯引号长文本: 引导词命中 → leadin; 否则 quoted（契约豁免）
    # 口径: 弯引号 “ ” 内的长文本即视为 verbatim-like——模型大量用弯引号做
    # 提及/强调（讨论"某个概念"）, 无引导词时不作逐字承诺（E 类不误伤）。
    for m in re.finditer(r"[“]([^“”]{10,240})[”]", src):
        body = m.group(1).strip()
        if len(norm_q(body)) < QUOTE_MIN_NORM:
            continue
        head = src[:m.start()]
        leadin = bool(LEADIN_RE.search(head[-40:]))
        urls = web_quotes.inline_urls(src[m.end():]) if strict_quote_spans else []
        if strict_quote_spans and leadin and _illustrative_speech(head, src[m.end():]):
            leadin = False
        leadin = leadin or bool(urls)
        seq += 1
        out.append({"quote_claim_id": f"quote_{seq}",
                    "kind": "leadin" if leadin else "quoted",
                    "text": body, "line_count": 1,
                    "char_start": m.start(), "char_end": m.end()})
        if strict_quote_spans and leadin:
            labels = web_quotes.inline_labels(src[m.end():])
            if labels:
                out[-1]["citation_labels"] = labels
            if urls:
                out[-1]["citation_urls"] = urls
        taken.append((m.start(), m.end()))
    # 直引号长文本: 仅引导词命中才提取（无引导词的成对直引号多为 scare quotes,
    # 逐对直引号之间的正文曾被误捕获为假引文——真实回归 R1 的 3 条 MEMORY_ONLY 噪声）
    for m in re.finditer(r"[\"]([^\"]{10,240})[\"]", src):
        if any(s <= m.start() < e for s, e in taken):
            continue
        body = m.group(1).strip()
        if len(norm_q(body)) < QUOTE_MIN_NORM:
            continue
        head = src[:m.start()]
        urls = web_quotes.inline_urls(src[m.end():]) if strict_quote_spans else []
        if not LEADIN_RE.search(head[-40:]) and not urls:
            continue
        seq += 1
        illustrative = strict_quote_spans and not urls and _illustrative_speech(head, src[m.end():])
        out.append({"quote_claim_id": f"quote_{seq}", "kind": "quoted" if illustrative else "leadin",
                    "text": body, "line_count": 1,
                    "char_start": m.start(), "char_end": m.end()})
        if strict_quote_spans:
            labels = web_quotes.inline_labels(src[m.end():])
            if labels:
                out[-1]["citation_labels"] = labels
            if urls:
                out[-1]["citation_urls"] = urls
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
def audit_quotes(answer, raw_tool_log, *, strict_quote_spans=False):
    """最终可见正文 → 引文核验审计（逐条 + 汇总）"""
    spans = evidence_spans(raw_tool_log)
    web_spans = []
    if strict_quote_spans:
        from deep_web_quotes import read_spans
        web_spans = read_spans(raw_tool_log)
        # Prefer an actually read passage over an equal search excerpt. This
        # preserves context in repair feedback instead of selecting the first
        # lexical hit merely because the search happened earlier.
        spans = sorted(spans, key=lambda span: span.get("source_type") != "primary_read")
    entries = []
    for q in extract_quotes(answer, strict_quote_spans=strict_quote_spans):
        labels = q.get("citation_labels") or []
        urls = q.get("citation_urls") or []
        if labels or urls:
            # Every attached attribution must support these exact words. A true
            # quote from another retrieved book cannot validate a false label.
            checks = [verify_quote(q["text"], [
                sp for sp in spans
                if EC._book_match(sp.get("book"), label["book"])
                and EC._chapter_match(sp.get("chapter") or "", label["chapter"])
            ]) for label in labels]
            checks.extend(verify_quote(q["text"], [sp for sp in web_spans if url in sp["urls"]]) for url in urls)
            v = min(checks, key=lambda item: {
                "MEMORY_ONLY": 0, "VERIFIED_NEAR": 1,
                "SHORT": 2, "VERIFIED_EXACT": 3,
            }[item["state"]])
        else:
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
            **({"citation_urls": urls} if urls else {}),
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
