# -*- coding: utf-8 -*-
"""O7-B RP2 §2-5 — 独立语义审计器（Independent Metadata Audit）。

与生产 extractor（dp_biblio_build.py）零共享: 不 import 其任何 regex/函数;
自建一套基于 token 边界与字符分类的独立判定逻辑。

原则: 验证 evidence semantics（证据本身是不是该字段的 bibliographic 语义类）,
不重新跑 extraction。每行输出 audit_rule_id / audit_reason /
supporting_spans / rejected_spans。

用法: .venv/bin/python backend/tools/dp_biblio_audit.py
产出: docs/evidence/PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json（覆盖为独立版）
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_PATH = os.path.join(ROOT, "backend", "data", "book_bibliography.json")
OUT_PATH = os.path.join(ROOT, "docs", "evidence", "PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json")

# ── 独立词法（刻意采用与生产不同的实现思路: 逐字符 token 边界, 非共享 regex 对象）──
_PUB_SUFFIX = ("出版社", "出版公司", "出版集团", "书馆")
_YI = "译譯"
# 「译」后若紧跟这些字, 则「译」属于词的一部分（译文/译本/译丛…）, 不是职责标记
_YI_WORD_NEXT = set("文本版丛书社者")


def _name_before_yi(span):
    """独立责任陈述判定: 取 span 中「译」前的连续汉字名。

    返回 (name, ok):
      ok=False 当 「译」属于词的一部分（译文/译本…）或名字为空/单字重复。
    实现方式: 手工扫描字符, 不调用生产 regex。"""
    for i, ch in enumerate(span):
        if ch in _YI:
            nxt = span[i + 1] if i + 1 < len(span) else ""
            if nxt and (nxt in _YI_WORD_NEXT or ('\u4e00' <= nxt <= '\u9fa5' and nxt == "文")):
                continue  # 该「译」是词成分, 找下一个
            j = i - 1
            # 名与「译」之间允许至多一个空白（含全角 \u3000）——「卫茂平　译」
            if j >= 0 and span[j] in (" ", "\u3000", "\t"):
                j -= 1
            while j >= 0 and '\u4e00' <= span[j] <= '\u9fa5':
                j -= 1
            name = span[j + 1:i]
            if name and name[-1] in (" ", "\u3000"):
                name = name[:-1]
            # 去掉「等」
            name = name[:-1] if name.endswith("等") else name
            if not (2 <= len(name) <= 4):
                return None, False
            if name and len(set(name)) == 1:   # 「一一」式噪声
                return None, False
            return name, True
    return None, False


def audit_translator(value, spans):
    """独立规则: 每个 span 内存在职责「译」标记, 其前紧邻名字 == value,
    且「译」不是词成分; name 不得来自出版社 token。"""
    supporting, rejected = [], []
    for s in spans:
        if any(s.endswith(suf) or (suf in s and _publisher_token(s)) for suf in _PUB_SUFFIX):
            if _publisher_token(s) and value in _publisher_token(s):
                rejected.append((s, "name 来自出版社 token"))
                continue
        name, ok = _name_before_yi(s)
        if ok and name == value:
            supporting.append(s)
        else:
            rejected.append((s, f"无匹配责任陈述（独立解析 name={name!r}）"))
    return len(supporting) >= 2, supporting, rejected


def _publisher_token(s):
    for suf in _PUB_SUFFIX:
        i = s.find(suf)
        if i != -1:
            j = i - 1
            while j >= 0 and ('\u4e00' <= s[j] <= '\u9fa5' or s[j] in "·A-Za-z"):
                j -= 1
            return s[j + 1:i + len(suf)]
    return None


def audit_publisher(value, spans):
    supporting, rejected = [], []
    for s in spans:
        tok = _publisher_token(s)
        if tok and tok.endswith(value):
            supporting.append(s)
        else:
            rejected.append((s, "span 非出版社陈述形态"))
    return len(supporting) >= 2, supporting, rejected


def audit_isbn(value, spans):
    digits = re.sub(r"[^0-9Xx]", "", value)   # 独立: 仅用于归一化, 非生产 regex
    supporting, rejected = [], []
    for s in spans:
        if "ISBN" in s.upper() and re.sub(r"[^0-9Xx]", "", s).startswith(digits[:9]):
            supporting.append(s)
        else:
            rejected.append((s, "span 不含匹配的 ISBN 陈述"))
    return len(supporting) >= 2, supporting, rejected


def audit_publication_year(value, spans_with_class):
    """spans_with_class: [(raw_span, semantic_class)]。
    支持: ≥2 独立 EDITION_YEAR / CIP_BIBLIOGRAPHIC_YEAR 且值可导出;
    PRINTING_YEAR / CIP_REGISTRATION_YEAR 一律归 ignored。"""
    supporting, ignored, rejected = [], [], []
    for s, cls in spans_with_class:
        if cls in ("EDITION_YEAR", "CIP_BIBLIOGRAPHIC_YEAR"):
            if value in s:
                supporting.append((s, cls))
            else:
                rejected.append((s, cls, "支持类但值不导出"))
        elif cls in ("PRINTING_YEAR", "CIP_REGISTRATION_YEAR"):
            ignored.append((s, cls))
        else:
            rejected.append((s, cls, "未知语义类"))
    return len(supporting) >= 2, supporting, ignored, rejected


def audit_original_title(value, spans):
    supporting, rejected = [], []
    for s in spans:
        if "书名原文" in s and value and value.strip() and value.strip() in s:
            supporting.append(s)
        else:
            rejected.append((s, "非「书名原文」陈述"))
    return len(supporting) >= 2, supporting, rejected


RULE_IDS = {
    "translator": "AUD-TR-01 independent responsibility-statement parse",
    "publisher": "AUD-PUB-01 independent publisher-token parse",
    "isbn": "AUD-ISBN-01 independent ISBN statement check",
    "publication_year": "AUD-YR-01 support-class separation (EDITION/CIP_BIBLIO vs PRINTING/REG)",
    "original_title": "AUD-OT-01 original-title statement",
}


def audit_row(field, value, evidence):
    """evidence: field_provenance.candidates 中 selected 候选的 evidence 列表。"""
    rid = RULE_IDS.get(field, "AUD-UNKNOWN")
    if field == "publication_year":
        swc = [(e["raw_span"], e.get("semantic_source_type", "?")) for e in evidence]
        ok, sup, ign, rej = audit_publication_year(value, swc)
        return {"ok": ok, "audit_rule_id": rid,
                "audit_reason": f"supporting={len(sup)} ignored={len(ign)} rejected={len(rej)}",
                "supporting_spans": [f"{s} [{c}]" for s, c in sup],
                "ignored_spans": [f"{s} [{c}]" for s, c in ign],
                "rejected_spans": [str(r) for r in rej]}
    spans = [e["raw_span"] for e in evidence]
    fn = {"translator": audit_translator, "publisher": audit_publisher,
          "isbn": audit_isbn, "original_title": audit_original_title}.get(field)
    if fn is None:
        return {"ok": False, "audit_rule_id": "AUD-NA", "audit_reason": "无独立规则",
                "supporting_spans": [], "rejected_spans": spans}
    ok, sup, rej = fn(value, spans)
    return {"ok": ok, "audit_rule_id": rid,
            "audit_reason": f"supporting={len(sup)} rejected={len(rej)}",
            "supporting_spans": sup, "rejected_spans": [str(r) for r in rej]}


def run_audit(data=None):
    data = data or json.load(open(DATA_PATH, encoding="utf-8"))
    rows, unsupported = [], []
    for bid, r in data["books"].items():
        for f, v in r["field_provenance"].items():
            if not (v.get("verified") and not v.get("conflict")):
                continue
            cand = next((c for c in v["candidates"] if c["value"] == v["selected_value"]), None)
            ev = cand["evidence"] if cand else []
            res = audit_row(f, v["selected_value"], ev)
            row = {"book_id": bid, "field": f, "value": v["selected_value"],
                   "raw_evidence_spans": [e["raw_span"] for e in ev],
                   "semantic_evidence_class": "/".join(sorted({e.get("semantic_source_type", "?") for e in ev})),
                   "audit_implementation": "INDEPENDENT",
                   "SUPPORTS_FIELD_SEMANTICS": res["ok"], **{k: v2 for k, v2 in res.items() if k != "ok"}}
            rows.append(row)
            if not res["ok"]:
                unsupported.append(f"{bid}.{f}")
    return {"audit_scope": "ALL_VERIFIED_FIELDS",
            "audit_implementation": "INDEPENDENT",
            "shared_extraction_rules": 0,
            "fields_audited": len(rows),
            "SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS": unsupported,
            "rows": rows}


def main():
    out = run_audit()
    json.dump(out, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    return 0 if not out["SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS"] else 1


if __name__ == "__main__":
    sys.exit(main())
