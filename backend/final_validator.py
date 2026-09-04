# -*- coding: utf-8 -*-
"""O2 Final Answer Ownership —— 确定性 Final Validator（thin）

架构契约（O2）:
    Main Agent → Final Candidate → Deterministic Validation
        ├─ PASS → publish
        └─ FAIL → structured issues → 同一个 Main Agent repair → 新 candidate

Runtime 只保留三种权力: VALIDATE / REJECT / mechanical FORMAT。
本模块把原 LiveCitationSanitizer（未核验引用流式降级）、QuoteBoundSanitizer
（MEMORY_ONLY 引文转写 paraphrase / NEAR 自动加注）的"检测能力"保留为
结构化 ValidationIssue，彻底删除它们对正文文本的一切改写与追加——修复由
同一个 Main Agent 自主完成（它可以继续调用工具研究，也可以改写、标注、删除
引文或重写答案）。

允许的 issue code 全部限于"可用本次 evidence 机械判断的对象"，
禁止出现 SOURCE_ATTRIBUTION_REQUIRED / CLAIM_TOO_STRONG 等认知治理维度
（那是 Agent 的认识论义务，不是 deterministic validation）。

O4-RP1: validator 只依赖 candidate + evidence（FINAL_VALIDATOR_GENERAL_INTENT_DEPENDENCY = 0）
—— 不接收任何用户意图分类（来源约束/提问对象/核验状态）参数: 无论用户是否在问"出处",
只要正文出现引用/引文, 一律按证据校验。
原 check_consistency（VERIFY_LATER_MISSTATEMENT, task-intent discipline）已删除——
evidence/action consistency 类检查如后续需要再立项。
"""
from dataclasses import dataclass, field, asdict

import quote_bound as QB
from evidence_contract import (_CITE_RE, _CITE_AUTHOR_WORK_RE, _split_book_chapter,
                               _dedup, _extract_candidates, _book_match, _chapter_match)

# ── 机械可验证 issue code（封闭集合）──────────────────────────────
UNVERIFIED_CITATION = "UNVERIFIED_CITATION"        # formal citation 无本次 evidence 支持
UNSUPPORTED_EXACT_QUOTE = "UNSUPPORTED_EXACT_QUOTE"  # 以逐字形态呈现、库中无原文（含 leadin 未披露）
NEAR_QUOTE_NOT_MARKED = "NEAR_QUOTE_NOT_MARKED"    # 仅近似命中却被当作逐字且未自行标注
STITCHED_QUOTE = "STITCHED_QUOTE"                  # 跨段落拼接引文
EMPTY_FINAL = "EMPTY_FINAL"                        # 候选为空/纯空白（机械异常，非"太短"）

# 修复上限（O2 §10）——纯机械 ceiling, 不是语义判断; 达到后宁可如实以
# validation failure 收口, 也不由 runtime 代写"正确答案"
MAX_VALIDATION_REPAIRS = 2

# system prompt 引用格式示例的模板词——模型回显它们不构成引用主张（机械跳过）
_PLACEHOLDER_BOOKS = {"书名", "作品", "书名·", "Book", "book"}
_PLACEHOLDER_CHAPTERS = {"章节", "篇名", "章名", "Chapter", "chapter"}


@dataclass
class ValidationIssue:
    code: str
    locator: str = ""          # 命中位置的可读定位（标记/引文预览）
    evidence_ref: str = None   # 关联 evidence_id（如有）
    detail: str = ""

    def as_dict(self):
        return asdict(self)


@dataclass
class ValidationResult:
    ok: bool
    issues: list = field(default_factory=list)
    verified_citations: int = 0   # 通过核验的 formal citation 数（done 审计用）
    quote_audit: dict = field(default_factory=dict)  # QB.audit_quotes 结果（done 审计复用）

    def as_dict(self):
        return {"ok": self.ok, "issues": [i.as_dict() for i in self.issues]}


def format_feedback(result: ValidationResult) -> str:
    """validator → Main Agent 的中性修复反馈（不命令具体动作——修什么、怎么修由 Agent 决定）"""
    lines = [f"- {i.code}" + (f" at \"{i.locator}\"" if i.locator else "")
             + (f": {i.detail}" if i.detail else "") for i in result.issues]
    return ("The candidate response failed deterministic evidence validation. Issues:\n"
            + "\n".join(lines)
            + "\nRevise the answer or gather additional evidence as needed.")


# ═══════════════════════════════════════════════════════
# 1. formal citation 校验（原 LiveCitationSanitizer 的检测核心，纯函数化）
# ═══════════════════════════════════════════════════════
def _primary_sources(tool_log, fallback_log=None):
    """本次调用取得的 primary 证据池 → [(book, chapter)] 归一化候选"""
    merged = list(tool_log) if tool_log else []
    if fallback_log:
        merged += [t for t in fallback_log if t not in merged]
    try:
        cands = _dedup(_extract_candidates(merged))
        return [(c["book"], c.get("chapter") or "") for c in cands
                if c.get("source_type") == "primary" and c.get("book")]
    except Exception:
        return []


def check_citations(answer, tool_log, fallback_log=None):
    """正文中的 formal citation 标记逐个对照 evidence 池（只检测，绝不改写）。
    返回 (verified_count, issues)。citation 的 markdown 渲染格式问题属机械
    formatter 职责，不在此处理。
    模板占位符（【《书名》·章节】式——模型回显 system prompt 的格式示例）不构成
    引用主张，机械跳过（不算已核验, 也不打回）。"""
    issues = []
    verified = 0
    sources = _primary_sources(tool_log, fallback_log)
    ans = answer or ""
    buf = ans
    while True:
        m1 = _CITE_RE.search(buf)
        m2 = _CITE_AUTHOR_WORK_RE.search(buf)
        m, kind = (m1, "canonical") if (m1 and (not m2 or m1.start() <= m2.start())) else (m2, "author_work")
        if not m:
            break
        if kind == "author_work":
            _author, book, chapter = m.group(1), m.group(2), ""
        else:
            _author, book, chapter = "", *_split_book_chapter(m.group(1), m.group(2))
        # 占位符豁免（机械边界, 防绕过）: 仅当书名与章节都是模板词（或章节缺省）时,
        # 该标记才是格式示例回显, 不构成引用主张。真实书名 + 占位章节（如【《论语》·章节】）
        # 不豁免——照常进入证据校验（C3: 不得通过"把真实书名稍微模板化"绕过 validator）。
        book_is_template = book in _PLACEHOLDER_BOOKS
        chapter_is_template = chapter == "" or chapter in _PLACEHOLDER_CHAPTERS
        if book_is_template and chapter_is_template:
            buf = buf[m.end():]
            continue
        if book and any(_book_match(ev_b, book) and _chapter_match(ev_c, chapter)
                        for ev_b, ev_c in sources):
            verified += 1
        else:
            issues.append(ValidationIssue(
                code=UNVERIFIED_CITATION, locator=m.group(0),
                detail=f"formal citation not supported by retrieved evidence (book={book!r}, chapter={chapter!r})"))
        buf = buf[m.end():]
    return verified, issues


# ═══════════════════════════════════════════════════════
# 2. 逐字引文校验（复用 Quote Bound 的 extract/verify/audit，只检测）
# ═══════════════════════════════════════════════════════
def check_quotes(answer, raw_tool_log):
    """最终候选正文 → 引文核验 issue。
    判定范围与原渲染契约一致: blockquote（整段原文形态）与 leadin（行内「」引文）
    承担"逐字承诺"; 行内短“引述”与过短片段（SHORT）不作逐字承诺。"""
    issues = []
    audit = QB.audit_quotes(answer or "", raw_tool_log)
    for e in audit.get("entries", []):
        st, kind = e.get("verification_state"), e.get("kind")
        loc = e.get("preview") or ""
        ev = e.get("source_evidence_id")
        if st == "VERIFIED_NEAR" and not e.get("disclosed") and kind in ("blockquote", "leadin"):
            issues.append(ValidationIssue(
                code=NEAR_QUOTE_NOT_MARKED, locator=loc, evidence_ref=ev,
                detail=f"quote only approximates the retrieved text (coverage={e.get('coverage')}) "
                       f"but is presented as verbatim without an approximation note"))
        elif st == "MEMORY_ONLY" and kind == "blockquote":
            if e.get("stitched"):
                issues.append(ValidationIssue(
                    code=STITCHED_QUOTE, locator=loc, evidence_ref=ev,
                    detail="blockquote assembles non-adjacent passages; not a continuous verbatim source"))
            else:
                issues.append(ValidationIssue(
                    code=UNSUPPORTED_EXACT_QUOTE, locator=loc, evidence_ref=ev,
                    detail="blockquote not found verbatim in retrieved evidence"))
        elif st == "MEMORY_ONLY" and kind == "leadin" and not e.get("disclosed"):
            issues.append(ValidationIssue(
                code=UNSUPPORTED_EXACT_QUOTE, locator=loc, evidence_ref=ev,
                detail="in-line verbatim quote not found in retrieved evidence and not disclosed as recalled"))
    return audit, issues


# ═══════════════════════════════════════════════════════
# 3. 总入口
# ═══════════════════════════════════════════════════════
def validate_final_candidate(answer, *, raw_tool_log, fallback_log=None,
                             language="zh") -> ValidationResult:
    """对 Final Candidate 做一次性确定性校验（candidate 此刻只在内部缓冲，尚未公开）。
    纯函数式检测: 不改写、不追加、不重试——FAIL 时由调用方把结构化 issues 反馈给
    同一个 Main Agent 进入 repair。
    输入只有 candidate + evidence（raw_tool_log/fallback_log）——没有用户意图分类、
    问题类型或来源约束: 同一候选无论配什么问题, 校验结果一致。"""
    ans = answer or ""
    if not ans.strip():
        return ValidationResult(ok=False, issues=[ValidationIssue(
            code=EMPTY_FINAL, detail="candidate is empty or whitespace-only")])
    issues = []
    verified_citations, cite_issues = check_citations(
        ans, raw_tool_log, fallback_log=fallback_log)
    issues.extend(cite_issues)
    audit, quote_issues = check_quotes(ans, raw_tool_log)
    issues.extend(quote_issues)
    result = ValidationResult(ok=not issues, issues=issues,
                              verified_citations=verified_citations, quote_audit=audit)
    return result
