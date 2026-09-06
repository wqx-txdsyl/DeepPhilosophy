# -*- coding: utf-8 -*-
"""O7-B RP1 §12-13 — 全量 verified 字段语义审计（取代弱抽样审计）。

对每本书每个 verified 字段记录:
  book_id / field / value / raw evidence spans / semantic evidence class
  / SUPPORTS_FIELD_SEMANTICS

语义支持判定不是「regex 能重新抽出来」——而是证据 span 本身属于该字段的
bibliographic 语义类:
  isbn        → span 含 ISBN 标识
  translator  → span 匹配 responsibility statement（名+译+语义边界）
  publisher   → span 是 X出版社/出版公司/书馆 形态
  publication_year → span 语义类 ∈ {EDITION_YEAR, CIP_BIBLIOGRAPHIC_YEAR}
  original_title  → span 行为「书名原文：…」陈述

产出: docs/evidence/PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json
用法: .venv/bin/python backend/tools/dp_biblio_sample.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_biblio_build import DEFAULT_OUT_DATA as OUT_DATA, RE_TRANSLATOR, RE_ISBN, RE_PUBLISHER

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "..", "docs", "evidence", "PHIAGENT_O7B_SEMANTIC_FIELD_AUDIT.json")


def main():
    data = json.load(open(OUT_DATA, encoding="utf-8"))
    rows, unsupported = [], []
    n_fields = 0
    for bid, r in data["books"].items():
        for f, v in r["field_provenance"].items():
            if not (v.get("verified") and not v.get("conflict")):
                continue
            n_fields += 1
            cand = next((c for c in v["candidates"] if c["value"] == v["selected_value"]), None)
            ev = cand["evidence"] if cand else []
            # 责任者语义: value 必须能从每个证据 span 重导出
            ok = True
            if f == "translator":
                ok = all((m := RE_TRANSLATOR.search(e["raw_span"])) and m.group(1) == v["selected_value"]
                         for e in ev)
            elif f == "isbn":
                ok = all("ISBN" in e["raw_span"] for e in ev)
            elif f == "publisher":
                ok = all(RE_PUBLISHER.search(e["raw_span"]) for e in ev)
            elif f == "publication_year":
                # 同值证据可跨语义类聚合; 判定 = ≥2 个独立证据行的语义类
                # 属于支持 publication_year 的 {EDITION_YEAR, CIP_BIBLIOGRAPHIC_YEAR},
                # 且值可从这些 span 导出（核字/印刷类证据只是附加记录, 不参与支持）
                elig = [e for e in ev
                        if e["semantic_source_type"] in ("EDITION_YEAR", "CIP_BIBLIOGRAPHIC_YEAR")]
                ok = len({(e["chapter_idx"], e["line_no"]) for e in elig}) >= 2 and \
                    all(v["selected_value"] in e["raw_span"] for e in elig)
            elif f == "original_title":
                ok = all("书名原文" in e["raw_span"] for e in ev)
            else:
                ok = False  # 未知字段类型不支持
            cls = ev[0]["semantic_source_type"] if ev else "?"
            rows.append({"book_id": bid, "field": f, "value": v["selected_value"],
                         "raw_evidence_spans": [e["raw_span"] for e in ev],
                         "semantic_evidence_class": cls,
                         "SUPPORTS_FIELD_SEMANTICS": ok})
            if not ok:
                unsupported.append(f"{bid}.{f}")
    out = {"audit_scope": "ALL_VERIFIED_FIELDS",
           "fields_audited": n_fields,
           "SEMANTICALLY_UNSUPPORTED_VERIFIED_FIELDS": unsupported,
           "rows": rows}
    open(os.path.abspath(OUT), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"},
                     ensure_ascii=False, indent=1))
    return 0 if not unsupported else 1


if __name__ == "__main__":
    sys.exit(main())
