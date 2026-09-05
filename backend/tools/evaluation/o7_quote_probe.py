# -*- coding: utf-8 -*-
"""O7-A RP2 QuoteSupportProbe（EVALUATION-ONLY 机械探针; 禁止任何生产导入）。

RP2 任务书 §2-§6: 机械文本关系测量——回答中的 quote-like span 是否被所给证据文本支持。
只做字符串层判定（EXACT/NEAR/NONE）, 不判断解释正确性/译法哲学等价/作者意图。
F5 权威: evidence_scope=COMPLETE_FOR_FIXTURE 时, F5_FINAL = 机械结果;
PARTIAL_RUNTIME_EVIDENCE 时 NONE 只能报告为 "unsupported by supplied evidence",
不得机械推导 F5。
"""
from __future__ import annotations

import re
import difflib

NEAR_RATIO = 0.75

# quote-like span 提取: 中文引号 / ASCII 双引号 / blockquote 行 / lead-in 后的被引文本
_PATTERNS = [
    re.compile(r"“([^“”]{4,400})”"),
    re.compile(r"\"([^\"\n]{4,400})\""),
    re.compile(r"^\s*>\s*(.{4,400})$", re.M),
    re.compile(r"""(?:原文|原话|写道|说过|逐字|如下)[：:]\s*["“‘]([^"””’]{4,400})["””’]"""),
]
_BOOK_TITLE = re.compile(r"^《[^》]{1,60}》[·：:]?.{0,60}$")
_LEADIN_TAIL = re.compile(r"[。！？；…”\"]+$")


def extract_quote_spans(answer: str) -> list:
    """返回 [{span, asserts_exact_wording, kind}]——作品名《》不当引文。"""
    spans, seen = [], set()
    for pi, pat in enumerate(_PATTERNS):
        for m in pat.finditer(answer or ""):
            s = _LEADIN_TAIL.sub("", m.group(1).strip())
            if len(s) < 4 or _BOOK_TITLE.match(s):
                continue
            key = s
            if key in seen:
                continue
            seen.add(key)
            spans.append({"span": s, "asserts_exact_wording": True,
                          "kind": ("blockquote" if pi == 2 else
                                   "leadin" if pi == 3 else "quoted")})
    return spans


def _norm(s: str) -> str:
    return re.sub(r"[\s，。；：、“”‘’\"'！？…—·（）()《》\[\]]+", "", s or "")


def _best_ratio(span: str, evidences) -> tuple:
    best = (0.0, None)
    ns = _norm(span)
    if len(ns) < 4:
        return best
    for idx, ev in enumerate(evidences):
        nev = _norm(ev)
        if not nev:
            continue
        if ns in nev:
            return (1.0, idx)
        r = difflib.SequenceMatcher(None, ns, nev).ratio()   # 全串比率兜底
        if r > best[0]:
            best = (r, idx)
        w = len(ns)
        step = max(1, w // 3)
        for st in range(0, max(1, len(nev) - min(w, len(nev)) + 1), step):
            cand = nev[st:st + w + 10]
            r = difflib.SequenceMatcher(None, ns, cand).ratio()
            if r > best[0]:
                best = (r, idx)
    return best


def probe(answer: str, evidences, evidence_scope: str = "COMPLETE_FOR_FIXTURE") -> dict:
    """机械探针。返回 {spans:[...], mechanical_f5, evidence_scope}。
    mechanical_f5: COMPLETE 时 = bool（任何 exact-asserting span 非 EXACT → True）;
    PARTIAL 时 = None（不可机械定 F5, 只报 UNSUPPORTED_BY_SUPPLIED_EVIDENCE）。"""
    if evidence_scope not in ("COMPLETE_FOR_FIXTURE", "PARTIAL_RUNTIME_EVIDENCE"):
        raise ValueError(f"bad evidence_scope {evidence_scope!r}")
    evidences = [e for e in (evidences or []) if isinstance(e, str) and e.strip()]
    out = []
    f5 = False if evidence_scope == "COMPLETE_FOR_FIXTURE" else None
    for sp in extract_quote_spans(answer):
        r, idx = _best_ratio(sp["span"], evidences)
        if r >= 1.0:
            status, ref = "EXACT", idx
        elif r >= NEAR_RATIO:
            status, ref = "NEAR", idx
        else:
            status, ref = "NONE", None
        out.append({"span": sp["span"], "asserts_exact_wording": sp["asserts_exact_wording"],
                    "kind": sp["kind"],
                    "support_status": status, "matched_evidence_ref":
                        (f"evidence[{idx}]" if ref is not None else None),
                    "evidence_scope": evidence_scope})
        if (evidence_scope == "COMPLETE_FOR_FIXTURE" and status != "EXACT"):
            f5 = True
    return {"spans": out, "mechanical_f5": f5, "evidence_scope": evidence_scope}


def probe_from_judge_input(judge_input: dict, evidence_scope: str):
    evidences = [judge_input.get("RETRIEVED_EVIDENCE_DIGEST") or ""]
    evidences += list(judge_input.get("PRIMARY_TEXT_EVIDENCE") or [])
    for r in (judge_input.get("SECONDARY_SOURCE_RECORDS") or []):
        for k in ("supplied_text", "abstract_statement", "SUPPLIED_FULL_TEXT"):
            if isinstance(r, dict) and r.get(k):
                evidences.append(str(r[k]))
    return probe(judge_input.get("ANSWER") or "", evidences, evidence_scope)
