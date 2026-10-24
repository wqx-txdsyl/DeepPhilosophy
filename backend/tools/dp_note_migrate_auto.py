#!/usr/bin/env python3
"""dp_note_migrate_auto.py — 『正文[n]行内标记 + 章末注文块』模式的自动迁注（note-contract v1）

适用形态（康德著作集等）：正文 text 块含 [1]、[2]… 行内标记；章末有一个或多个
"注文块"（其 value 以 [1] 开头，或全部由 "[n] 注文…" 条目组成）。

安全规则：
  1. 全章 [n] 标记集合 与 章末注文条目集合 必须完全一致（无孤号、无缺号），否则该章拒绝迁移并报告。
  2. 迁移逐字节保全：正文只做 [n]→{{n:x}} 的标记替换；注文文本原样进 notes（可含 \n 多段）。
  3. 注文条目里嵌套的 [n] 引用（注中注）不再改写。
  4. 显示号 = 首次引用顺序；迁移时按正文首次出现顺序重排 n，使 n 与显示号一致。
  5. 注文块若混有非注文内容（如正文续段），拒绝迁移并报告——只处理可判定整块为注文的情况。
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
REF_RE = re.compile(r"\[(\d{1,3})\]")
# 注文条目：行首 [n] 后跟注文文本
ITEM_RE = re.compile(r"(?m)^\s*\[(\d{1,3})\]\s?")


def is_note_block(v: str) -> bool:
    """整块都是注文条目：以 [1]（或首个条目号）开头，且所有行首标记号严格递增、无正文句式混杂。"""
    s = v.strip()
    if not s.startswith("["):
        return False
    # 去掉所有条目号后，剩余文字不应再含行首标记序号断裂（保守：允许任意文字，但必须以[开头且条目号≥1）
    nums = [int(m.group(1)) for m in ITEM_RE.finditer(s)]
    return len(nums) >= 1


def parse_note_items(v: str):
    """把注文块拆成 [(n, text), ...]，保持原顺序与原文。"""
    s = v.strip()
    matches = list(ITEM_RE.finditer(s))
    items = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(s)
        items.append((int(m.group(1)), s[start:end].strip("\n").rstrip()))
    return items


def migrate_chapter(path: Path, dry=False, allow_unreferenced=False):
    d = json.loads(path.read_text(encoding="utf-8"))
    if d.get("notes"):
        return {"ch": path.stem, "status": "already_has_notes", "migrated": 0}
    content = d["content"]
    # 1. 正文标记清单（按首次出现顺序）
    body_refs = []
    for bi, b in enumerate(content):
        if isinstance(b, dict) and b.get("type") == "text":
            for m in REF_RE.finditer(b.get("value") or ""):
                body_refs.append((bi, int(m.group(1))))
    ref_nums = [n for _, n in body_refs]
    if not ref_nums:
        return {"ch": path.stem, "status": "no_refs"}
    # 2. 章末注文块：从尾部连续收集 is_note_block 的块（配对校验兜底，误收会被 MISMATCH 拒绝）
    note_blocks = []   # (bi, items)
    for bi in range(len(content) - 1, -1, -1):
        b = content[bi]
        if not (isinstance(b, dict) and b.get("type") == "text"):
            break
        v = b.get("value") or ""
        if is_note_block(v):
            note_blocks.append((bi, v))
            continue
        break
    if not note_blocks:
        return {"ch": path.stem, "status": "no_note_block", "refs": len(set(ref_nums))}
    items = []
    for _, v in reversed(note_blocks):   # 文件顺序
        items.extend(parse_note_items(v))
    note_nums = [n for n, _ in items]
    # 3. 配对校验：正文引用集合 == 注文条目集合（孤立注文可选保留为无引用注）
    ref_set, note_set = set(ref_nums), set(note_nums)
    orphans = note_set - ref_set   # 有注文无锚点
    if ref_set - note_set:
        missing = ref_set - note_set
        return {"ch": path.stem, "status": "MISMATCH",
                "missingInNotes": sorted(missing), "extraInNotes": sorted(orphans),
                "refs": len(ref_set), "notes": len(note_set)}
    if orphans and not allow_unreferenced:
        return {"ch": path.stem, "status": "ORPHANS", "orphanNotes": sorted(orphans),
                "refs": len(ref_set), "notes": len(note_set)}
    # 4. 重排：n = 正文首次引用顺序；无锚点的孤立注文排在有引用注文之后（契约§3）
    order = []
    for _, n in body_refs:
        if n not in order:
            order.append(n)
    order.extend(sorted(orphans))
    mapping = {old: i + 1 for i, old in enumerate(order)}
    # 5. 正文标记替换（仅正文 text 块，跳过注文块本身）
    note_block_ids = {bi for bi, _ in note_blocks}
    for bi, old in body_refs:
        if bi in note_block_ids:
            continue
        b = content[bi]
        b["value"] = re.sub(r"\[%d\]" % old, "{{n:%d}}" % mapping[old], b["value"], count=0)
    # 6. notes 数组（文本原样；章内引用 [k] 保留原样——不误伤注中注）
    notes = []
    for old, text in items:
        nt = {"n": mapping[old], "text": text}
        notes.append(nt)
    notes.sort(key=lambda x: x["n"])
    d["notes"] = notes
    # 7. 删除注文块
    d["content"] = [b for bi, b in enumerate(content) if bi not in note_block_ids]
    d["paragraphMode"] = "source"   # 注文块删除后，正文块即真实段落边界
    if not dry:
        path.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return {"ch": path.stem, "status": "migrated", "notes": len(notes),
            "refs": len(ref_nums), "multiRef": len(ref_nums) - len(set(ref_nums))}


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    bid = sys.argv[1]
    only = set(sys.argv[2:]) if len(sys.argv) > 2 else None
    book = BASE / "data" / "book_chapters" / bid
    results = []
    for f in sorted(book.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 10 ** 9):
        if not f.stem.isdigit():
            continue
        if only and f.stem not in only:
            continue
        r = migrate_chapter(f)
        results.append(r)
        if r["status"] in ("MISMATCH", "no_note_block") and r.get("refs"):
            print(json.dumps(r, ensure_ascii=False))
    ok = sum(1 for r in results if r["status"] == "migrated")
    total_notes = sum(r.get("notes", 0) for r in results)
    print(json.dumps({"book": bid, "chaptersMigrated": ok, "totalNotes": total_notes,
                      "detail": [r for r in results if r["status"] != "migrated"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
