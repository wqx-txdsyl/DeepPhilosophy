# -*- coding: utf-8 -*-
"""Quote Bound（Phase T.1, T1.1-D/E/F/G/H）——逐字引文绑定与渲染约束

真实回归（Phase T 后）: Citation Sanitizer 只约束 formal citation（【《书》·章】）,
模型可以输出一整段"原文" blockquote 然后写"根据记忆，未经核验"——未核验的逐字文本
照样进入用户可见正文，甚至把相邻章句拼接（A 段开头 + B 段结尾）。

组件（纯规则 + 数据驱动, 不联网、不调 LLM、不新增工具）:

  extract_quotes         用户可见文本 → verbatim-like 引文清单
                         （markdown blockquote / 引导词引文「原文是/写道/原话…」/
                          中文引号长文本）
  evidence_spans         raw_tool_log → 可核验证据 span 池
                         （get_chapter 全文按行分段; search snippet; 语料回响）
  verify_quote           引文 ↔ 证据 span 逐字核验:
                           VERIFIED_EXACT   归一后连续出现在单一 span（拼接在此即失败）
                           VERIFIED_NEAR    覆盖率 ≥ NEAR_THRESHOLD（近似措辞）
                           MEMORY_ONLY      无证据支撑（不得渲染为原文 blockquote）
                         + stitched 标志: 前半/后半分别命中不同 span（T1.1-F 跨段拼接）
  QuoteBoundSanitizer    流式渲染约束: MEMORY_ONLY blockquote → 转换为 paraphrase +
                         核验边界声明; NEAR → 标注"近似，非逐字"; EXACT → 原样保留
  audit_quotes           最终正文审计（done 事件 + 回归断言用）
  scan_final_consistency T1.1-G/H 收口扫描: 置信度升级与 verify-later 反模式补正

边界: MEMORY_HINT 不是 EVIDENCE（T1.1-E）——检索片段命中只能定位，不能支撑逐字引用；
span 池里 get_chapter 全文与片段同池，但逐字核验天然由连续包含判定兜底。
"""
import re

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

# T1.1-G: 强确定性措辞（verification_state 必须约束 claim strength）
STRONG_CERTAINTY_RE = re.compile(
    r"可以确认|可以肯定|确凿|确切出处|学界一致|毫无疑义|毫无疑问|判断.{0,8}可靠|"
    r"是可靠的|可靠——|确凿无疑|千真万确|铁证")
# T1.1-H: verify-later 反模式（把核验推给后续轮次, 替代本次应完成的核验）
# 开场词型需覆盖: 如果你需要 / 若你需要 / 你若需要 / 如果您需要 / 需要的话 / 如需…
VERIFY_LATER_OPEN_RE = re.compile(r"(?:如果|若是?|要是|倘若|如)?(?:你|您)?(?:若是?|的话)?需要")
VERIFY_LATER_RE = re.compile(
    VERIFY_LATER_OPEN_RE.pattern + r"[^。！？\n]{0,24}"
    r"(读取|查阅|查一下|检索|核实|查证|核验|读原文|读取原文|再作|再查)"
    r"|(我可以|让我|我可)(再去?|进一步|接着|再作)?[^。！？\n]{0,10}"
    r"(读取|读|查阅|核实|检索|查证|核验)[^。！？\n]{0,10}(原文|章节|全文|《|逐字)")


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
    source_type, units: [完整原文单元（行=章段）]}]"""
    spans = []
    for i, tc in enumerate(raw_tool_log or []):
        name = tc.get("name") or ""
        rf = tc.get("result_full")
        if not isinstance(rf, dict) or rf.get("error"):
            continue
        if name == "get_chapter":
            text = rf.get("text") or ""
            if not text:
                continue
            units = [ln.strip() for ln in text.split("\n") if ln.strip()]
            spans.append({"evidence_id": f"qb_read_{i}", "book": rf.get("book_title") or "",
                          "chapter": rf.get("title") or "", "book_id": rf.get("book_id", ""),
                          "chapter_idx": rf.get("chapter_idx", -1), "source_type": "primary_read",
                          "units": units or [text]})
        elif name == "search_books":
            for item in rf.get("results") or []:
                if isinstance(item, dict) and item.get("snippet"):
                    spans.append({"evidence_id": f"qb_snip_{i}_{len(spans)}",
                                  "book": item.get("book_title") or "",
                                  "chapter": item.get("chapter_title") or "",
                                  "book_id": item.get("book_id", ""),
                                  "chapter_idx": item.get("chapter_idx", -1),
                                  "source_type": "snippet",
                                  "units": [item["snippet"]]})
        elif name in ("philosopher_corpus", "philosopher_quote"):
            for e in (rf.get("echoes") or rf.get("quotes") or []):
                if isinstance(e, dict) and (e.get("text") or e.get("snippet")):
                    spans.append({"evidence_id": f"qb_corp_{i}_{len(spans)}",
                                  "book": e.get("book") or "",
                                  "chapter": e.get("chapter") or "", "book_id": "",
                                  "chapter_idx": -1, "source_type": "corpus",
                                  "units": [e.get("text") or e.get("snippet")]})
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
# 4. 流式渲染约束（T1.1-D）
# ═══════════════════════════════════════════════════════
_PARAPHRASE_HEAD_ZH = "据通行理解，"
_PARAPHRASE_TAIL_ZH = "；但我尚未在当前原典库中逐字核验。\n\n"
_PARAPHRASE_HEAD_EN = "As commonly understood, "
_PARAPHRASE_TAIL_EN = " — though I have not verified this verbatim in the corpus.\n\n"
_NEAR_MARK_ZH = "（与库中原文近似，非逐字）"
_NEAR_MARK_EN = "(close to the retrieved text, not verbatim)"
_VERIFIED_MARK_ZH = ""    # EXACT 不加标记——正式引用交给 Citation Sanitizer


class QuoteBoundSanitizer:
    """流式 quote bound（生命周期 = 单次 invocation 最终回答阶段）

    push(text) 逐段处理: blockquote 行被缓冲到引用块闭合, 整块核验后按状态渲染:
      VERIFIED_EXACT → 原样保留
      VERIFIED_NEAR  → 保留 + 追加"近似，非逐字"标注
      MEMORY_ONLY    → 剥 blockquote 格式, 转换为 paraphrase + 核验边界声明
    leadin 引文（同一行内闭合）MEMORY_ONLY 时在闭合引号后插入披露标记。
    非 blockquote 文本即时放行（不增加逐句延迟）; blockquote 行缓冲至引用块闭合。
    """

    def __init__(self, raw_tool_log_ref, language="zh"):
        self._log_ref = raw_tool_log_ref
        self._lang = "en" if language == "en" else "zh"
        self._spans = None
        self._buf = ""
        self._bq_lines = []      # 当前未闭合 blockquote 的行
        self.stats = {"quotes_seen": 0, "verified_exact": 0, "verified_near": 0,
                      "memory_only": 0, "stitched": 0, "converted": 0}

    def _sources(self):
        if self._spans is None:
            try:
                self._spans = evidence_spans(self._log_ref if isinstance(self._log_ref, list) else [])
            except Exception:
                self._spans = []
        return self._spans

    def _close_blockquote(self):
        """闭合当前 blockquote → 核验 → 按状态渲染（返回渲染文本, 恒以换行结尾）"""
        lines, self._bq_lines = self._bq_lines, []
        if not lines:
            return ""
        body = "".join(lines).strip()
        # 空体（流式 chunk 把 ">" 与内容劈开 / 纯装饰性引用线）→ 原样放行, 绝不转换
        if len(norm_q(body)) < QUOTE_MIN_NORM:
            rendered = "".join(f"> {ln}\n" for ln in lines if ln.strip())
            return rendered
        self.stats["quotes_seen"] += 1
        v = verify_quote(body, self._sources())
        if v["state"] == "VERIFIED_EXACT":
            self.stats["verified_exact"] += 1
            rendered = "".join(f"> {ln}\n" for ln in lines if ln.strip())
            return rendered
        if v["state"] == "VERIFIED_NEAR":
            self.stats["verified_near"] += 1
            mark = _NEAR_MARK_EN if self._lang == "en" else _NEAR_MARK_ZH
            rendered = "".join(f"> {ln}\n" for ln in lines if ln.strip())
            return rendered + f"\n{mark}\n"
        # MEMORY_ONLY → 不得冒充逐字原文（T1.1-D 渲染规则）
        if v["stitched"]:
            self.stats["stitched"] += 1
        self.stats["memory_only"] += 1
        self.stats["converted"] += 1
        if self._lang == "en":
            return f"{_PARAPHRASE_HEAD_EN}{body}{_PARAPHRASE_TAIL_EN}"
        return f"{_PARAPHRASE_HEAD_ZH}{body}{_PARAPHRASE_TAIL_ZH}"

    def _process_line(self, line):
        if BLOCKQ_LINE_RE.match(line):
            self._bq_lines.append(BLOCKQ_LINE_RE.sub("", line, count=1))
            return ""
        # 孤立 ">"（仅一个空 blockquote 行）+ 紧随的非空普通行 → 吸收为该行引用
        #（流式 chunk 常把 "> " 与内容劈开; markdown 意图上它们是同一个 blockquote）
        if len(self._bq_lines) == 1 and self._bq_lines[0].strip() == "" \
                and line.strip() and not BLOCKQ_LINE_RE.match(line):
            self._bq_lines.append(line)
            return ""
        out = self._close_blockquote() if self._bq_lines else ""
        base = len(out)          # line 在 out 中的起始偏移（out = 闭合块 + line）
        out += line
        # leadin 引文（同行闭合）: MEMORY_ONLY 时插入披露标记（不重写正文, 最小干预）
        for m in re.finditer(r"[“\"]([^“”\"]{10,240})[”\"]", line):
            body = m.group(1)
            if len(norm_q(body)) < QUOTE_MIN_NORM:
                continue
            head = line[:m.start()]
            if LEADIN_RE.search(head[-40:]):
                self.stats["quotes_seen"] += 1
                v = verify_quote(body, self._sources())
                if v["state"] in ("MEMORY_ONLY",):
                    self.stats["memory_only"] += 1
                    if v["stitched"]:
                        self.stats["stitched"] += 1
                    mark = ("（原文表述凭记忆给出，未经本次库中逐字核验）" if self._lang != "en"
                            else "(quoted from memory, not verified verbatim in the corpus)")
                    pos = base + m.end()
                    out = out[:pos] + mark + out[pos:]
                    break
        return out

    def push(self, text):
        self._buf += text or ""
        if not self._buf:
            return ""
        out = ""
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            out += self._process_line(line) + "\n"
        # 尾部残余: 普通文本即时放行（保流式节奏）; blockquote 行残余必须留在缓冲等下一块拼接。
        # chunk 可能把 "> 「…" 从中间劈开（无换行符）——若把残余当完整行处理, 引用行会被腰斩成
        # "> 「\n正文"（引用块只剩半个引号、正文掉出引用块; 真实回归: 言必有中 R 系列渲染断裂）。
        if self._buf and not BLOCKQ_LINE_RE.match(self._buf):
            line, self._buf = self._buf, ""
            out += self._process_line(line)
        return out

    def flush(self):
        out = ""
        if self._buf:
            out += self._process_line(self._buf)
            self._buf = ""
        out += self._close_blockquote()
        return out

    def snapshot(self):
        return dict(self.stats)


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


# ═══════════════════════════════════════════════════════
# 6. 收口一致性扫描（T1.1-G/H）
# ═══════════════════════════════════════════════════════
_BOUNDARY_G_ZH = ("（确定性边界：以上出处判断的证据不足以支撑其确定性措辞——本次未能在原典库中"
                  "完成逐字核验，相关结论不应视为已核验结论。）")
_BOUNDARY_G_EN = ("(Confidence boundary: the evidence above does not support the certainty of the "
                  "wording — verbatim verification in the corpus was not completed, so treat this "
                  "attribution as unverified.)")
_CORRECT_H_ZH = ("（更正：相关原文已在本次回答中读取并核验，无需另行查阅。）")
_CORRECT_H_EN = ("(Correction: the relevant original text was already read and verified in this "
                 "answer — no further lookup is needed.)")
_BOUNDARY_H_ZH = ("（核验边界：本次调用的原典核验未能完成，上述内容不得视为已核验出处。）")
_BOUNDARY_H_EN = ("(Verification boundary: corpus verification could not be completed in this "
                  "turn; the above must not be treated as a verified attribution.)")


def scan_final_consistency(answer, audit, obligations_satisfied, primary_text_read=None,
                           language="zh"):
    """T1.1-G/H 收口扫描 → 需要尾补的文本列表

    G 置信一致性: 引文核验存在 MEMORY_ONLY / 义务未满足 时, 强确定性措辞必须降级;
    H verify-later: 核验完成后出现的"我可以再读"是虚假许诺（应更正）;
                    核验未完成时出现则是反模式（应声明边界）。
    """
    ans = answer or ""
    out = []
    en = language == "en"
    mem_only = bool((audit or {}).get("summary", {}).get("memory_only"))
    # T1.1-G
    if STRONG_CERTAINTY_RE.search(ans) and (mem_only or not obligations_satisfied):
        out.append(_BOUNDARY_G_EN if en else _BOUNDARY_G_ZH)
    # T1.1-H
    if VERIFY_LATER_RE.search(ans):
        if obligations_satisfied or primary_text_read:
            out.append(_CORRECT_H_EN if en else _CORRECT_H_ZH)
        else:
            out.append(_BOUNDARY_H_EN if en else _BOUNDARY_H_ZH)
    return out
