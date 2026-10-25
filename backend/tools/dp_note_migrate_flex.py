#!/usr/bin/env python3
"""dp_note_migrate_flex.py — 续块/合注/多标记风格感知的柔性迁注（note-contract v1）

适用：正文标记 [n] / （n） / (n)（纯数字，不会误配 (80d) 类页码），章末注文块链；
注文块之间允许夹"续块"（不以句末标点收尾的短块，拼回前一条注文）；
一条注文可挂多个标记（印本合注），正文多个锚点映射到同一条注释。

安全：label 集合与正文引用集合必须完全一致，否则拒绝；孤注（无锚点）可选保留。
"""
import json
import re
import sys
from pathlib import Path

REF = re.compile(r"(?:\[(\d{1,3})\]|（(\d{1,3})）|\((\d{1,3})\))")
LABEL = re.compile(r"^\s*((?:\[\d{1,3}\]\s*|（\d{1,3}）\s*|\(\d{1,3}\)\s*)+)")
END_PUNCT = tuple("。！？”’」』】】:；")


def _num(m):
    return int(m.group(1) or m.group(2) or m.group(3))


def migrate_flex(path, dry=False, allow_orphans=True, cont_max=400):
    d = json.loads(path.read_text())
    if d.get("notes"):
        return {"ch": path.stem, "status": "already"}
    c = d["content"]
    entries = []
    idx = len(c) - 1
    in_notes = False
    pending = []   # 前挂续块：续行被 OCR 排到其标签块之后（walk 顺序中先遇续行后遇标签）
    while idx >= 0:
        b = c[idx]
        if not (isinstance(b, dict) and b.get("type") == "text"):
            break
        v = b.get("value") or ""
        m = LABEL.match(v.strip())
        if m:
            labels = [_num(REF.search(tok)) for tok in re.findall(r"\[\d{1,3}\]|（\d{1,3}）|\(\d{1,3}\)", m.group(1))]
            text = v.strip()[len(m.group(1)):].strip()
            ids = [idx]
            if pending:
                text = text + "".join(pending)
                ids.extend(range(idx + 1, idx + 1 + len(pending)))
                pending = []
            entries.append({"labels": labels, "text": text, "ids": ids})
            in_notes = True
        elif in_notes and entries:
            # 续块判定：回扫最近≤5条注文，找到文本未以句末标点收尾（被页缝截断）的那条吸收
            target = None
            if len(v) < cont_max:
                for e in reversed(entries[-5:]):
                    if not e["text"].rstrip().endswith(END_PUNCT):
                        target = e
                        break
            if target is not None:
                target["text"] = v + target["text"]
                target["ids"].append(idx)
            elif LABEL.match((c[idx - 1].get("value") or "").strip()) if idx >= 1 else False:
                pending.append(v)   # 前挂：下一（更低索引）标签块的续行
                idx -= 1
                continue
            else:
                break
        else:
            break
        idx -= 1
    if not entries:
        return {"ch": path.stem, "status": "no_notes"}
    entries.reverse()
    label2entry = {}
    for ei, e in enumerate(entries):
        for lb in e["labels"]:
            if lb in label2entry:
                return {"ch": path.stem, "status": "DUP_LABEL", "label": lb}
            label2entry[lb] = ei
    body_refs = []
    note_ids = {i for e in entries for i in e["ids"]}
    for bi, b in enumerate(c):
        if bi in note_ids or not (isinstance(b, dict) and b.get("type") == "text"):
            continue
        for mm in REF.finditer(b.get("value") or ""):
            body_refs.append((bi, _num(mm)))
    ref_labels = {n for _, n in body_refs}
    if ref_labels - set(label2entry):
        return {"ch": path.stem, "status": "MISMATCH", "missing": sorted(ref_labels - set(label2entry)),
                "refs": len(ref_labels), "notes": len(entries)}
    orphans = sorted(set(label2entry) - ref_labels)
    if orphans and not allow_orphans:
        return {"ch": path.stem, "status": "ORPHANS", "orphans": orphans}
    entry_order = []
    for _, n in body_refs:
        ei = label2entry[n]
        if ei not in entry_order:
            entry_order.append(ei)
    for ei in range(len(entries)):
        if ei not in entry_order:
            entry_order.append(ei)
    note_of_entry = {ei: k + 1 for k, ei in enumerate(entry_order)}
    for bi, old in body_refs:
        b = c[bi]
        b["value"] = REF.sub(lambda mm: "{{n:%d}}" % note_of_entry[label2entry[_num(mm)]], b["value"], count=0)
    notes = [{"n": note_of_entry[ei], "text": entries[ei]["text"]} for ei in entry_order]
    notes.sort(key=lambda x: x["n"])
    d["notes"] = notes
    d["content"] = [b for i, b in enumerate(c) if i not in note_ids]
    d["paragraphMode"] = "source"
    if not dry:
        path.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"ch": path.stem, "status": "migrated", "notes": len(notes),
            "multiLabel": sum(1 for e in entries if len(e["labels"]) > 1),
            "continuations": sum(len(e["ids"]) - 1 for e in entries),
            "orphans": orphans}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    dry = "--dry" in sys.argv
    for a in sys.argv[1:]:
        if a.startswith("--"):
            continue
        r = migrate_flex(Path(a), dry=dry)
        print(json.dumps(r, ensure_ascii=False))
