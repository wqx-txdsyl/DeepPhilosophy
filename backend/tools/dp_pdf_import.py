# -*- coding: utf-8 -*-
"""
dp_pdf_import.py — PDF 入库（2026-08-05）
功能:
  1. 扫描 F:/philosophy 东方/西方 全部 PDF（126 本）
  2. 应用合并规则（一书多作者分居两文件夹 → 只入库主文件, 作者合并; 见 MERGE_RULES）
  3. 正文提取: 有文本层 → pymupdf 直接提取; 无 → PaddleOCR（页级断点续传）
  4. 章节化: 强模式标题检测（第X章/序/前言/§ 等）, 无命中整本一章
  5. 输出: book_chapters/{bid}/{i}.json + meta.json + book_detail/{bid}.json（含 summary/tags 匹配）
  6. 封面: PDF 首页渲染 → WebP → app/public/covers/
断点: OCR 页级 checkpoint + 书级 checkpoint（dp_pdf_import_ckpt.json）
"""
import sys, io, os, json, re, time, hashlib, shutil
from pathlib import Path

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_book_json import save_as_webp

import fitz
from paddleocr import PaddleOCR

BOOKS_DIR = r"F:/philosophy"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
CDIR = os.path.join(BASE_DIR, "data/book_chapters")
DDIR = os.path.join(BASE_DIR, "data/book_detail")
IMG_DIR = os.path.join(BASE_DIR, "data/book_images")
COVERS_DIR = os.path.join(BASE_DIR, "../app/public/covers")
SDIR = os.path.join(BASE_DIR, "data/book_summaries.json")
# 并行分片: python dp_pdf_import.py [shard] [total]（shard 0-based, total 默认 1）
# shard 0 用主 ckpt（保留既有进度）; shard>0 用独立 ckpt 文件, 全部完成后用 dp_merge_ckpt.py 合并
SHARD = int(sys.argv[1]) if len(sys.argv) > 1 else 0
SHARD_TOTAL = int(sys.argv[2]) if len(sys.argv) > 2 else 1
CKPT_FILE = os.path.join(BASE_DIR, "data",
                         f"dp_pdf_import_ckpt_s{SHARD}.json" if SHARD_TOTAL > 1 and SHARD > 0
                         else "dp_pdf_import_ckpt.json")
os.makedirs(CDIR, exist_ok=True); os.makedirs(DDIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True); os.makedirs(COVERS_DIR, exist_ok=True)

summaries = json.load(open(SDIR, "r", encoding="utf-8")) if os.path.exists(SDIR) else {}

# ── 合并规则: 副文件 rel_path → (主文件 rel_path, 合并作者)
# 一书多作者分居两文件夹: 只入库主文件, 作者显示为合著
MERGE_RULES = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf":
        ("西方/卡尔·马克思/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf", "卡尔·马克思、弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/共产党宣言.pdf":
        ("西方/卡尔·马克思/共产党宣言.pdf", "卡尔·马克思、弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf":
        ("西方/卡尔·马克思/德意志意识形态（节选本）.pdf", "卡尔·马克思、弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/马克思恩格斯文集.epub":
        ("西方/卡尔·马克思/马克思恩格斯文集.epub", "卡尔·马克思、弗里德里希·恩格斯"),
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf":
        ("西方/扬布里柯/哲学规劝录 哲学的慰藉.pdf", "扬布里柯、波爱修斯"),
}
# 大问题（epub 两份）: 留 mtime 最新的（在扫描时处理）

ZOOM = 1.2
RESTART_EVERY = 100  # 每 100 页重建 OCR（模型重启 ~30s, 25 页/次太频繁）
_ocr, _ocr_pages = None, 0

def get_ocr():
    global _ocr, _ocr_pages
    if _ocr is None or _ocr_pages >= RESTART_EVERY:
        if _ocr is not None:
            del _ocr
            import gc; gc.collect()
        _ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)
        _ocr_pages = 0
    return _ocr

def ocr_page(img_path):
    global _ocr_pages
    o = get_ocr()
    result = o.ocr(img_path)
    _ocr_pages += 1
    if result and result[0]:
        return "\n".join(line[1][0] for line in result[0])
    return ""

def has_text_layer(fp):
    """\u6587\u672c\u5c42\u53ef\u7528\u5224\u5b9a: \u4e2d\u6587\u91cf >100 \u4e14 \u4e2d\u6587\u5360\u6bd4 >60%\uff08\u4e71\u7801\u7387\u9ad8\u5219\u89c6\u4e3a\u574f\u6587\u672c\u5c42, \u8d70 OCR\uff09"""
    doc = fitz.open(fp)
    t = doc[min(30, doc.page_count - 1)].get_text()
    doc.close()
    zh = len(re.findall(r"[\u4e00-\u9fff]", t))
    total = len(re.sub(r"\s+", "", t))
    return zh > 100 and total > 0 and zh / total > 0.6

def extract_text_layer(fp):
    doc = fitz.open(fp)
    pages = []
    for p in range(doc.page_count):
        pages.append(doc[p].get_text())
    doc.close()
    # 页拼接: 页末无标点 → 行内断行直接拼; 否则段落分隔
    full = pages[0]
    for t in pages[1:]:
        if full and full[-1] in "。！？；：”』」）】…—-":
            full += "\n\n" + t
        else:
            full += t
    return full

def ocr_pdf(fp, ckpt, safe):
    """页级 OCR 断点续传"""
    doc = fitz.open(fp)
    total = doc.page_count
    doc.close()
    done = ckpt.get("ocr", {}).get(safe, {})
    pages_map = {int(k): v for k, v in done.items() if v and v != "__FAILED__"}
    tmp = Path(os.environ.get("TEMP", ".")) / "dp_paddle"
    tmp.mkdir(parents=True, exist_ok=True)
    for i in range(total):
        if i in pages_map:
            continue
        doc = fitz.open(fp)
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
        img = str(tmp / f"{safe}_p{i:04d}.png")
        pix.save(img)
        doc.close()
        text = ""
        try:
            text = ocr_page(img)
        except Exception as e:
            print(f"    OCR 页{i} 异常: {e}", flush=True)
        done[str(i)] = text or "__FAILED__"
        if i % 10 == 0:
            ckpt.setdefault("ocr", {})[safe] = done
            json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        time.sleep(0.1)
    ckpt.setdefault("ocr", {})[safe] = done
    json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    texts = [pages_map.get(i, "") for i in range(total)]
    return "\n\n".join(t for t in texts if t)

# ── 文本规范化 + 章节化
def _is_cjk(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF

def merge_lines(text):
    """OCR 行合并: 行尾中文+行首中文 → 拼接; 空行保留为段落"""
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
    """强模式章节切分: 命中行(短)为新章起始; 页眉重复标题不切章（最近 50 行内出现过=页眉）"""
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
                continue  # 页眉重复（每页出现）→ 丢弃, 不切章
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
    """章节文本 → DP 章节块格式 [{type:'text',value}]"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", ch_text) if p.strip()]
    return [{"type": "text", "value": p} for p in paras]

def make_cover(fp, bid):
    doc = fitz.open(fp)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    doc.close()
    png = Path(os.environ.get("TEMP", ".")) / f"{bid}_cover.png"
    pix.save(str(png))
    ofn = f"{bid}_cover.webp"
    op = os.path.join(COVERS_DIR, ofn)
    save_as_webp(png.read_bytes(), op)
    png.unlink(missing_ok=True)
    return f"/covers/{ofn}"

def main():
    ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
    done_books = ckpt.get("books", {})

    # 扫描（应用合并规则）
    pdfs = []
    for region in ["东方", "西方"]:
        rp = os.path.join(BOOKS_DIR, region)
        for author in sorted(os.listdir(rp)):
            ap = os.path.join(rp, author)
            if not os.path.isdir(ap):
                continue
            for fn in sorted(os.listdir(ap)):
                fp = os.path.join(ap, fn)
                if not os.path.isfile(fp):
                    continue
                rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
                if rel in MERGE_RULES:
                    continue  # 副文件跳过（合并到主文件）
                if fn.lower().endswith(".pdf"):
                    pdfs.append({"rel": rel, "fp": fp, "region": region, "author": author, "file": fn})

    # 文本层优先（快）, OCR 殿后（慢）
    pdfs.sort(key=lambda b: not has_text_layer(b["fp"]))
    print(f"PDF 待处理: {len(pdfs)}（已应用合并规则, 文本层优先）", flush=True)
    for i, b in enumerate(pdfs):
        if SHARD_TOTAL > 1 and i % SHARD_TOTAL != SHARD:
            continue  # 并行分片: 只处理本 shard 的书
        rel = b["rel"]
        if rel in done_books:
            print(f"[{i+1}] {b['file'][:40]} 断点跳过", flush=True)
            continue
        bid = hashlib.md5(rel.encode()).hexdigest()[:12]
        safe = re.sub(r"[^\w\-.]", "_", rel)
        t0 = time.time()
        print(f"[{i+1}/{len(pdfs)}] {rel}", flush=True)
        try:
            if has_text_layer(b["fp"]):
                text = extract_text_layer(b["fp"])
                src = "text-layer"
            else:
                text = ocr_pdf(b["fp"], ckpt, safe)
                src = "ocr"
        except Exception as e:
            print(f"    ✗ 提取失败: {e}", flush=True)
            continue
        # 合并作者（主文件时）
        author = b["author"]
        for sub, (main, merged_author) in MERGE_RULES.items():
            if rel == main:
                author = merged_author
                break
        chapters = chapterize(text)
        blocks_chs = [{"title": c["title"], "content": to_blocks(c["text"])} for c in chapters]
        # 写入章节
        bd = os.path.join(CDIR, bid)
        if os.path.exists(bd):
            shutil.rmtree(bd)
        os.makedirs(bd, exist_ok=True)
        for idx, ch in enumerate(blocks_chs):
            ch["index"] = idx
            json.dump(ch, open(os.path.join(bd, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False)
        toc_titles = [c["title"] for c in blocks_chs]
        meta = {"bookId": bid, "title": Path(b["file"]).stem, "author": author, "toc": toc_titles,
                "cover": None, "chapterCount": len(blocks_chs), "chapterTitles": toc_titles}
        json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
        # 封面
        cover = make_cover(b["fp"], bid)
        meta["cover"] = cover
        json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
        # detail
        title = Path(b["file"]).stem
        detail = {k: meta[k] for k in ["bookId", "title", "author", "cover", "toc", "chapterCount", "chapterTitles"]}
        detail["region"] = b["region"]; detail["file_type"] = "pdf"; detail["extract"] = src
        for sk in [f"{title}||{author}", f"{title}||", title]:
            s = summaries.get(sk)
            if s and s.get("summary"):
                detail["summary"] = s["summary"]
            if s and s.get("tags"):
                detail["tags"] = s["tags"]
            break
        json.dump(detail, open(os.path.join(DDIR, f"{bid}.json"), "w", encoding="utf-8"), ensure_ascii=False)
        done_books[rel] = {"chapters": len(blocks_chs), "src": src}
        ckpt["books"] = done_books
        json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"    ✓ {len(blocks_chs)}章 {src} {time.time()-t0:.0f}s", flush=True)

    print("\n===== 完成 =====")
    print(f"已入库: {len(done_books)}/{len(pdfs)}")

if __name__ == "__main__":
    main()
