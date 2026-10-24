#!/usr/bin/env python3
"""dp_intro_lib.py — 书籍介绍（summary）同步工具

介绍重写后同步四处（分章标准 §5 + books 双镜像）：
  1. backend/data/book_detail/{bid}.json   （存在则更新）
  2. app/public/book_detail/{bid}.json     （前端正式源）
  3. app/src/assets/books.json             条目 summary
  4. app/public/books.json（LFS，已实体化为真实文件）条目 summary

用法（由逐书驱动脚本 import），也可命令行单本更新:
  python3 dp_intro_lib.py <bid> <summary.json路径>   # summary.json = {"summary": "…\n\n…"}
"""
import json
import re
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TASK = REPO / "docs/tasks/book-full-proofread-zcode-2026-10-24"

HAN = re.compile(r"[\u4e00-\u9fff]")


def count_han(s: str) -> int:
    return len(HAN.findall(s or ""))


def validate_summary(text: str) -> list:
    errs = []
    if not text or not text.strip():
        return ["summary 为空"]
    paras = [p for p in text.split("\n") if p.strip()]
    if not (3 <= len(paras) <= 8):
        errs.append(f"段数 {len(paras)} 不在 3—8")
    total = count_han(text)
    if total < 280:
        errs.append(f"汉字数 {total} 过少（短篇/残篇下限280）")
    if total > 1200:
        errs.append(f"汉字数 {total} 超长（上限1200）")
    banned = ["证据", "门禁", "批次", "验收", "1301", "哈希", "待核", "校对", "实读",
              "OCR", "通过率", "AI", "模型", "本任务", "本轮"]
    for w in banned:
        if w in text:
            errs.append(f"出现内部作业词汇: {w}")
    return errs


def set_summary(bid: str, summary: str, intro_meta: dict = None) -> dict:
    """返回 {updated:[路径], errs:[...]}；books.json 两镜像逐条目精准更新，保持各自结构与顺序。"""
    errs = validate_summary(summary)
    updated = []
    detail_paths = [
        REPO / "backend/data/book_detail" / f"{bid}.json",
        REPO / "app/public/book_detail" / f"{bid}.json",
    ]
    for p in detail_paths:
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        d["summary"] = summary
        p.write_text(json.dumps(d, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        updated.append(str(p.relative_to(REPO)))
    books_paths = [
        REPO / "app/src/assets/books.json",
        REPO / "app/public/books.json",
    ]
    for p in books_paths:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        arr = data if isinstance(data, list) else data.get("books", [])
        hit = [e for e in arr if e.get("id") == bid]
        if not hit:
            errs.append(f"{p.name}: 无 {bid} 条目")
            continue
        hit[0]["summary"] = summary
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        updated.append(str(p.relative_to(REPO)))
    # 介绍台账
    rec = {"bid": bid, "appliedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
           "hanCount": count_han(summary), "paragraphs": len([p for p in summary.split("\n") if p.strip()]),
           "updated": updated}
    if intro_meta:
        rec.update(intro_meta)
    led_dir = TASK / "ledgers" / "introductions"
    led_dir.mkdir(parents=True, exist_ok=True)
    (led_dir / f"{bid}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"updated": updated, "errs": errs, "hanCount": count_han(summary)}


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    spec = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    r = set_summary(sys.argv[1], spec["summary"], spec.get("meta"))
    print(json.dumps(r, ensure_ascii=False, indent=1))
    sys.exit(1 if r["errs"] else 0)
