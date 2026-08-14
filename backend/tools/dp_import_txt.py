# -*- coding: utf-8 -*-
"""
dp_import_txt.py — ⚠️ 勿运行: txt 91 本是占位符（2026-08-05 用户确认: 无内容, 仅证明书存在）
txt 文件全部 0 字节; 书架保留元数据（封面/简介/标签/评分）, 章节永远为空。
本脚本保留仅作记录; 2026-08-05 曾误跑导入 90 本空章节, 已全部回滚。
  - 扫描 F:/philosophy 东方/西方 *.txt
  - 字符集: UTF-8 → GBK → gb18030 → UTF-16 fallback（CLAUDE.md: Windows GBK/UTF-8 高频问题）
  - 章节化: 强模式标题检测（第X章/序/前言/§ 等, 与 dp_pdf_import 一致）; 无命中整本一章
  - 输出: book_chapters/{bid}/{i}.json + meta.json; detail 补 chapterCount/toc
  - 断点: txt_import_ckpt.json（书级）
"""
import sys, os, json, re, hashlib, shutil
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
CDIR = os.path.join(BASE_DIR, "data/book_chapters")
DDIR = os.path.join(BASE_DIR, "data/book_detail")
BOOKS_DIR = r"F:/philosophy"
CKPT_FILE = os.path.join(BASE_DIR, "data/txt_import_ckpt.json")
# 与 dp_pdf_import 一致的书名修复
TITLE_FIX = {"SZ": "S/Z", "哲学与人生 (1)": "哲学与人生"}
# 神圣家族 txt 双份: 只导入马克思版
SKIP_REL = {"西方/弗里德里希·恩格斯/神圣家族.txt"}
os.makedirs(CDIR, exist_ok=True)
os.makedirs(DDIR, exist_ok=True)

_LOG = os.path.join(BASE_DIR, "data", "txt_import.log")
def _log(msg):
    try:
        sys.__stdout__.write(msg + "\n"); sys.__stdout__.flush()
    except Exception:
        pass
    try:
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

# ── 复用 dp_pdf_import 的章节化逻辑（拷贝, 避免 import 加载 paddleocr）──
def _is_cjk(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF

def merge_lines(text):
    lines = text.split("\n")
    merged = []
    for line in lines:
        s = line.strip()
        if not s:
            merged.append("")
            continue
        if merged and merged[-1] and _is_cjk(merged[-1][-1]) and _is_cjk(s[0]):
            merged[-1] += s
        else:
            merged.append(s)
    return "\n".join(merged)

CH_PAT = re.compile(
    r"^(第[一二三四五六七八九十百千\d]+[章节卷篇部]|"
    r"章[一二三四五六七八九十百\d]+|"
    r"[一二三四五六七八九十]{1,3}[、．.]|"
    r"(?:自?序|序[言文]?|前言|导[言论]|引[言论]|跋|后记|附[录记]|结[论语]|参考文献|"
    r"出版说明|译者序|代序|题记|致谢|附录[一二三四五六七八九十\d]*)\s*$|"
    r"^§\s*\d+)"
)

def chapterize(text):
    from collections import deque
    lines = text.split("\n")
    chapters = []
    cur_title = None
    cur_lines = []
    recent = deque(maxlen=50)
    def flush():
        if cur_title and cur_lines:
            para = merge_lines("\n".join(cur_lines))
            chapters.append({"title": cur_title, "text": para})
    for line in lines:
        s = line.strip()
        if not s:
            cur_lines.append("")
            continue
        if len(s) < 40 and CH_PAT.match(s):
            if s in recent:
                continue
            recent.append(s)
            flush()
            cur_title = s
            cur_lines = []
        else:
            cur_lines.append(s)
    flush()
    if not chapters:
        chapters = [{"title": "正文", "text": text}]
    return chapters

def to_blocks(ch_text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", ch_text) if p.strip()]
    return [{"type": "text", "value": p} for p in paras]

def read_txt(fp):
    """字符集探测: UTF-8 → GBK → gb18030 → UTF-16"""
    for enc in ("utf-8", "gbk", "gb18030", "utf-16"):
        try:
            with open(fp, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            continue
    return None


def main():
    ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
    done = ckpt.get("books", {})
    txts = []
    for region in ["东方", "西方"]:
        rp = os.path.join(BOOKS_DIR, region)
        for author in sorted(os.listdir(rp)):
            ap = os.path.join(rp, author)
            if not os.path.isdir(ap):
                continue
            for fn in sorted(os.listdir(ap)):
                fp = os.path.join(ap, fn)
                if not os.path.isfile(fp) or not fn.lower().endswith(".txt"):
                    continue
                rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
                if rel in SKIP_REL:
                    continue
                txts.append({"rel": rel, "fp": fp, "region": region, "author": author, "file": fn})
    _log(f"txt 待处理: {len(txts)}")
    for i, b in enumerate(txts):
        rel = b["rel"]
        if rel in done:
            continue
        bid = hashlib.md5(rel.encode()).hexdigest()[:12]
        _log(f"[{i+1}/{len(txts)}] {rel}")
        text = read_txt(b["fp"])
        if text is None:
            _log(f"  ✗ 字符集全失败: {rel}")
            continue
        title = TITLE_FIX.get(Path(b["file"]).stem, Path(b["file"]).stem)
        chapters = chapterize(text)
        blocks_chs = [{"title": c["title"], "content": to_blocks(c["text"])} for c in chapters]
        bd = os.path.join(CDIR, bid)
        if os.path.exists(bd):
            shutil.rmtree(bd)
        os.makedirs(bd, exist_ok=True)
        for idx, ch in enumerate(blocks_chs):
            ch["index"] = idx
            json.dump(ch, open(os.path.join(bd, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False)
        toc = [c["title"] for c in blocks_chs]
        meta = {"bookId": bid, "title": title, "author": b["author"], "toc": toc,
                "cover": None, "chapterCount": len(blocks_chs), "chapterTitles": toc}
        json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
        # detail 补 chapterCount/toc（保留已有 cover/summary/tags）
        dp = os.path.join(DDIR, f"{bid}.json")
        det = {}
        if os.path.exists(dp):
            try:
                det = json.load(open(dp, encoding="utf-8"))
            except Exception:
                det = {}
        det["bookId"] = bid
        det["title"] = title
        det["author"] = b["author"]
        det["region"] = b["region"]
        det["file_type"] = "txt"
        det["chapterCount"] = len(blocks_chs)
        det["toc"] = toc
        det["chapterTitles"] = toc
        json.dump(det, open(dp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        done[rel] = {"chapters": len(blocks_chs), "src": "txt"}
        ckpt["books"] = done
        json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        _log(f"  ✓ {len(blocks_chs)}章")
    _log(f"===== 完成: {len(done)}/{len(txts)} =====")


if __name__ == "__main__":
    main()
