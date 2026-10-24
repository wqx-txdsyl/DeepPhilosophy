#!/usr/bin/env python3
"""dp_note_check.py — 章末注释契约校验（docs/note-contract.md v1）

用法:
    python3 backend/tools/dp_note_check.py <bid>            # 校验整本书全部章节
    python3 backend/tools/dp_note_check.py <bid> <index>    # 只校验某一章

检查项:
  1. notes 字段模式: 数组、每项 n 为正整数、章内唯一、text 非空字符串
  2. kind 取值合法（author/translator/editor/original 或缺省）
  3. 正文 token {{n:x}} 与 notes 一一配对: 每个 token 有对应注; 每条注 ≥1 引用（无引用 → 警告, 迁移不得凭空造引用）
  4. token 只出现在 text 块（html/image 块内出现即失败）
  5. n 与首次引用顺序一致性（不一致 → 警告, 阅读器会重排显示号）
  6. 正文除 token 外不留未迁移的行内嵌注统计报告（信息性）

退出码: 0=通过(可含警告) 1=失败
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
TOKEN_RE = re.compile(r"\{\{n:(\d+)\}\}")
VALID_KINDS = {"author", "translator", "editor", "original"}


def check_chapter(path: Path):
    errors, warnings, info = [], [], []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"JSON 解析失败: {e}"], [], []
    if not isinstance(d, dict):
        return ["顶层不是 dict"], [], []
    notes = d.get("notes")
    content = d.get("content") or []
    if notes is None:
        # 未迁移章节: 只报告正文中的 token 残留（不该有）
        for bi, b in enumerate(content):
            if isinstance(b, dict) and b.get("type") == "text" and TOKEN_RE.search(b.get("value") or ""):
                errors.append(f"块{bi}: 无 notes 字段但正文含 token")
        return errors, warnings, ["无 notes（未迁移或无注释）"]

    if not isinstance(notes, list) or not notes:
        return ["notes 必须是非空数组"], warnings, info
    seen_n = set()
    for ni, nt in enumerate(notes):
        if not isinstance(nt, dict):
            errors.append(f"notes[{ni}] 不是对象")
            continue
        n = nt.get("n")
        if not isinstance(n, int) or isinstance(n, bool) or n <= 0:
            errors.append(f"notes[{ni}].n 非正整数: {n!r}")
        elif n in seen_n:
            errors.append(f"notes[{ni}].n 重复: {n}")
        else:
            seen_n.add(n)
        text = nt.get("text")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"notes[{ni}].text 非空字符串缺失")
        kind = nt.get("kind")
        if kind is not None and kind not in VALID_KINDS:
            errors.append(f"notes[{ni}].kind 非法: {kind!r}")
        imgs = nt.get("imgs")
        if imgs is not None and not isinstance(imgs, list):
            errors.append(f"notes[{ni}].imgs 必须是数组")

    # token 配对
    ref_count = {}
    for bi, b in enumerate(content):
        if not isinstance(b, dict):
            continue
        v = b.get("value") or ""
        btype = b.get("type")
        if TOKEN_RE.search(v) and btype != "text":
            errors.append(f"块{bi}(type={btype}): 含 token 但不是 text 块")
        if btype != "text":
            continue
        for m in TOKEN_RE.finditer(v):
            n = int(m.group(1))
            ref_count[n] = ref_count.get(n, 0) + 1
            if n not in seen_n:
                errors.append(f"块{bi}: token {{n:{n}}} 无对应 notes 条目")
    for n in sorted(seen_n):
        c = ref_count.get(n, 0)
        if c == 0:
            warnings.append(f"注{n}: 无行内引用（需登记待核, 不得凭空造引用）")
        elif c > 1:
            info.append(f"注{n}: {c} 处引用（阅读器按实例回跳）")

    # n ↔ 首次引用顺序一致性（阅读器按首次引用重排显示号, 数据顺序仅是约定）
    first_order = []
    seen = set()
    for b in content:
        if isinstance(b, dict) and b.get("type") == "text":
            for m in TOKEN_RE.finditer(b.get("value") or ""):
                n = int(m.group(1))
                if n not in seen:
                    seen.add(n)
                    first_order.append(n)
    data_order = [nt.get("n") for nt in notes if isinstance(nt.get("n"), int)]
    referenced_in_data_order = [n for n in data_order if n in seen]
    if referenced_in_data_order and referenced_in_data_order != first_order:
        warnings.append(f"notes 数组顺序与首次引用顺序不一致（阅读器将重排显示号）: 数据{referenced_in_data_order} vs 引用{first_order}")

    info.append(f"注{len(notes)}条/引用{sum(ref_count.values())}处")
    return errors, warnings, info


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    bid = sys.argv[1]
    book_dir = BASE / "data" / "book_chapters" / bid
    if not book_dir.is_dir():
        print(f"[FAIL] 章节目录不存在: {book_dir}")
        sys.exit(1)
    if len(sys.argv) > 2:
        files = [book_dir / f"{sys.argv[2]}.json"]
    else:
        files = sorted(book_dir.glob("*.json"), key=lambda p: int(p.stem) if p.stem.isdigit() else 10**9)
        files = [p for p in files if p.stem != "meta"]
    bad = 0
    total_notes = total_refs = 0
    for f in files:
        errs, warns, info = check_chapter(f)
        label = f"{bid}/{f.name}"
        for e in errs:
            print(f"[ERR] {label}: {e}")
        for w in warns:
            print(f"[WARN] {label}: {w}")
        for i in info:
            print(f"[info] {label}: {i}")
        if errs:
            bad += 1
        if f.name != "meta.json" and errs is not None:
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                total_notes += len(d.get("notes") or [])
                total_refs += sum(len(TOKEN_RE.findall((b.get("value") or "")) )
                                  for b in (d.get("content") or []) if isinstance(b, dict) and b.get("type") == "text")
            except Exception:
                pass
    print(f"== {bid}: {'FAIL' if bad else 'PASS'} ({bad} 章失败), 注{total_notes}条/引用{total_refs}处 ==")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
