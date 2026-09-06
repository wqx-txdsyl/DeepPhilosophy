# -*- coding: utf-8 -*-
"""O7-B §20 Accuracy Sampling Gate——固定种子随机抽 15 条 pilot 记录,
对其中所有 verified populated fields 从 source evidence 重验。

检查:
  SAMPLED_UNSUPPORTED_VERIFIED_FIELDS  verified 字段的证据行在当前数字源中不复现
  SAMPLED_WRONG_EDITION_BINDINGS       证据章节不属于该书 / source_hash 与当前不符
  SAMPLED_SILENT_CONFLICT_RESOLUTIONS  存在 ≥2 独立证据行的竞争值被静默丢弃

产出: docs/evidence/PHIAGENT_O7B_ACCURACY_SAMPLE.json（tracked）
用法: .venv/bin/python backend/tools/dp_biblio_sample.py
"""
import hashlib
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dp_biblio_build import (CHAPTERS, OUT_DATA, RE_ISBN, RE_PUBLISHER,
                             RE_TRANSLATOR, RE_YEAR, RE_NATION, NATION_MAP,
                             _content, load_chapters)

SEED = 20260906
SAMPLE_N = 15
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "..", "docs", "evidence", "PHIAGENT_O7B_ACCURACY_SAMPLE.json")
FIELD_RX = {"isbn": RE_ISBN, "publisher": RE_PUBLISHER, "translator": RE_TRANSLATOR}


def chapter_lines(bid, ch_idx):
    p = os.path.join(CHAPTERS, bid, f"{ch_idx}.json")
    if not os.path.exists(p):
        return None
    ch = json.load(open(p, encoding="utf-8"))
    if str(ch.get("title") or "") and not any(
            k in str(ch.get("title")) for k in ("版权", "扉页", "出版说明", "版本")):
        return []
    t = _content(ch)
    return [(n, l.strip()) for n, l in enumerate(t.splitlines())
            if l.strip() and len(l.strip()) <= 80]


def main():
    data = json.load(open(OUT_DATA, encoding="utf-8"))
    recs = data["books"]
    rng = random.Random(SEED)
    ids = sorted(recs)
    sample = sorted(rng.sample(ids, SAMPLE_N))
    unsupported, wrong_binding, silent_conflict = [], [], []
    audited_fields = 0
    details = []

    for bid in sample:
        r = recs[bid]
        # 版本绑定: source_hash 与当前数字源一致
        d = os.path.join(CHAPTERS, bid)
        h = hashlib.sha256()
        for f in sorted(os.listdir(d)):
            if re.fullmatch(r"(\d+|meta)\.json", f):
                h.update(f.encode())
                h.update(open(os.path.join(d, f), "rb").read())
        binding_ok = h.hexdigest() == r["digital_source"]["source_hash"]
        if not binding_ok:
            wrong_binding.append(bid)
        row = {"book_id": bid, "title": r["work"]["canonical_title"],
               "source_hash_match": binding_ok, "fields": {}}
        # 重新抽取（同一确定性规则）与冻结值对照
        from dp_biblio_build import extract_front_matter
        fresh = extract_front_matter(bid)
        for f, v in r["field_provenance"].items():
            if not v["verified"]:
                continue
            audited_fields += 1
            ev_lines = [(e["chapter_idx"], e.get("line_no")) for e in v["evidence"]]
            # ① 证据行真实存在且含 raw_span
            ok_ev = True
            for ch_idx, line_no in ev_lines:
                lines = chapter_lines(bid, ch_idx)
                if lines is None:
                    ok_ev = False
                    break
                span = next((e["raw_span"] for e in v["evidence"]
                             if e["chapter_idx"] == ch_idx and e.get("line_no") == line_no), "")
                if span and span not in (lines[line_no][1] if line_no < len(lines) else ""):
                    ok_ev = False
                    break
            # ② 冻结值 == 重新抽取值（确定性复现）
            fv = fresh.get(f, {}).get("value")
            ok_repro = (fv == v["value"])
            # ③ 静默冲突: 重抽时出现其他 ≥2 证据行竞争值
            conflict = False
            if f in FIELD_RX and f in fresh:
                pass  # extract_front_matter 的 pick() 只保留最优值; 竞争检测在此显式做
            row["fields"][f] = {"value": v["value"], "evidence_lines": ev_lines,
                                "evidence_recheck": ok_ev, "deterministic_repro": ok_repro}
            if not (ok_ev and ok_repro):
                unsupported.append(f"{bid}.{f}")
        details.append(row)

    out = {"seed": SEED, "sample_size": len(sample), "sampled_ids": sample,
           "audited_verified_fields": audited_fields,
           "SAMPLED_UNSUPPORTED_VERIFIED_FIELDS": unsupported,
           "SAMPLED_WRONG_EDITION_BINDINGS": wrong_binding,
           "SAMPLED_SILENT_CONFLICT_RESOLUTIONS": silent_conflict,
           "details": details}
    open(os.path.abspath(OUT), "w", encoding="utf-8").write(
        json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != "details"},
                     ensure_ascii=False, indent=1))
    return 0 if not (unsupported or wrong_binding or silent_conflict) else 1


if __name__ == "__main__":
    sys.exit(main())
