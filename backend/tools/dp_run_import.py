# -*- coding: utf-8 -*-
"""
dp_run_import.py — 未入库书逐本处理管线（2026-08-07, 精细模式）
每本: 提取(文本层 pymupdf / 扫描件 PaddleOCR 断点) → 新清洗(奇偶页眉/编章/§修复/页码) →
      质量检查(页眉残留/数字残留/章节数/空页/字数) → 回灌 book_chapters → 同步 DP 静态 → 标记 done

用法: python dp_run_import.py [--only 书名] [--txt-only] [--ocr-only] [--no-ocr]
日志行格式（供 Monitor 汇报）:
  [i/n] 《书名》 - 作者 | 提取中(text-layer)
  [i/n] 《书名》 | OCR 43% (310/723页)
  [i/n] 《书名》 | 清洗中 / 检查中
  [i/n] ✓ 《书名》 | 入库 23章 12.3万字 | 检查PASS(残留页眉0 数字0 空页2)
  [i/n] ⚠ 《书名》 | 入库 3章 2.1万字 | 检查WARN: 章节数偏少(3)
"""
import sys, io, os, json, re, time, hashlib, shutil

# 注意: 不在此包装 stdout —— dp_clean_book import 时会包装, 双重包装导致 I/O on closed file
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dp_clean_book as dcb

import fitz

BOOKS_DIR = r"F:/philosophy"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CKPT_FILE = os.path.join(BASE_DIR, "data", "dp_pdf_import_ckpt.json")
DP_PUBLIC = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")

MERGE_RULES = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf": None,
    "西方/弗里德里希·恩格斯/共产党宣言.pdf": None,
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf": None,
    "西方/弗里德里希·恩格斯/马克思恩格斯文集.epub": None,
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf": None,
    "西方/让-保罗·萨特/存在与虚无.pdf": None,
    "西方/柏拉图/理想国.pdf": None,
}
FORCE_OCR = {
    "西方/路易·阿尔都塞/读《资本论》.pdf",
    "西方/雅克·朗西埃/美学中的不满.pdf",
    "西方/弗里德里希·尼采/悲剧的诞生.pdf",
    "西方/亚里士多德/政治学.pdf",
    "西方/索伦·克尔凯郭尔/恐惧与战栗.pdf",
    "西方/让·鲍德里亚/擬仿物與擬像.pdf",
}

# ── OCR（PaddleOCR 2.8.1 + paddlepaddle 2.6.2, 页级断点, 单路慢跑）──
ZOOM = 1.2
RESTART_EVERY = 100
_ocr, _ocr_pages = None, 0


def get_ocr():
    global _ocr, _ocr_pages
    if _ocr is None or _ocr_pages >= RESTART_EVERY:
        if _ocr is not None:
            del _ocr
            import gc; gc.collect()
        import paddleocr
        # paddleocr.py 顶层 `from tools.infer import ...` → 把包目录加入 sys.path
        sys.path.insert(0, os.path.dirname(paddleocr.__file__))
        from paddleocr import PaddleOCR
        _ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)
        _ocr_pages = 0
    return _ocr


def ocr_pdf_pages(fp, safe, ckpt, progress=None):
    """页级 OCR 断点续传 → 页文本数组; progress: 回调(i, total) 供进度日志"""
    global _ocr_pages
    doc = fitz.open(fp)
    total = doc.page_count
    done = ckpt.get("ocr", {}).get(safe, {})
    pages_map = {int(k): v for k, v in done.items() if v and v != "__FAILED__"}
    tmp = os.path.join(os.environ.get("TEMP", "."), "dp_paddle")
    os.makedirs(tmp, exist_ok=True)
    last_report = [time.time()]  # 时间驱动进度: 每 180 秒报一次
    for i in range(total):
        if i in pages_map:
            continue
        doc = fitz.open(fp)
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
        img = os.path.join(tmp, f"{safe}_p{i:04d}.png")
        pix.save(img)
        doc.close()
        text = ""
        try:
            res = get_ocr().ocr(img)
            text = "\n".join(l[1][0] for l in res[0]) if res and res[0] else ""
        except Exception as e:
            print(f"    OCR 页{i} 异常: {e}", flush=True)
        done[str(i)] = text or "__FAILED__"
        _ocr_pages += 1
        if i % 10 == 0:
            ckpt.setdefault("ocr", {})[safe] = done
            json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
        if progress and (time.time() - last_report[0] >= 180 or i == total - 1):
            progress(i + 1, total)
            last_report[0] = time.time()
        time.sleep(0.1)
    ckpt.setdefault("ocr", {})[safe] = done
    json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    return [pages_map.get(i, "") for i in range(total)]


def extract_text_pages(fp):
    doc = fitz.open(fp)
    pages = [doc[p].get_text() for p in range(doc.page_count)]
    doc.close()
    return pages


def has_text_layer(fp):
    best = 0.0
    doc = fitz.open(fp)
    n = doc.page_count
    for p in (5, 30, 60, 90):
        if p >= n:
            continue
        t = doc[p].get_text()
        zh = len(re.findall(r"[\u4e00-\u9fff]", t))
        total = len(re.sub(r"\s+", "", t))
        if total:
            best = max(best, zh / total)
    doc.close()
    return best > 0.6


# ── 质量检查 ──
def check_quality(clean, chapters, toc_end, appendix_start=None):
    n = len(clean)
    issues = []
    # 页眉残留: 页首行在全书页首出现≥3次且是短行
    from collections import Counter
    firsts = Counter()
    for t in clean:
        ls = [l.strip() for l in t.split("\n") if l.strip()]
        if ls:
            firsts[ls[0]] += 1
    header_resid = {k for k, c in firsts.items() if c >= 3 and len(k) <= 25}
    if header_resid:
        issues.append(f"页眉残留{len(header_resid)}({sorted(header_resid)[:3]})")
    # 孤立数字残留（正文区; 目录/前置/附录的数字不算——目录页码、索引页码是合法内容）
    end = appendix_start if appendix_start is not None else len(clean)
    num_resid = sum(1 for i in range(toc_end, end)
                    for l in clean[i].split("\n") if re.match(r"^\d{1,4}$", l.strip()))
    if num_resid:
        issues.append(f"数字残留{num_resid}")
    # 章节/字数/空页
    nch = len(chapters)
    words = sum(len(re.sub(r"\s", "", t)) for t in clean)
    empty = sum(1 for t in clean if len(t.strip()) < 10)
    if nch <= 1:
        issues.append(f"章节数偏少({nch})")
    if words < 5000:
        issues.append(f"字数过少({words})")
    if empty > n * 0.3:
        issues.append(f"空页过多({empty}/{n})")
    return (True, f"PASS 页眉{len(header_resid)} 数字{num_resid} 空页{empty}") if not issues else \
           (False, "WARN: " + "; ".join(issues))


# ── 同步 DP 静态（5173 数据源 + git 追踪源 + book_detail + books.json）──
def sync_dp(bid, chapters_count):
    from dp_clean_book import BASE_DIR as _B
    src = os.path.join(_B, "data", "book_chapters", bid)
    if not os.path.exists(os.path.join(src, "meta.json")):
        return
    for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
    meta = json.load(open(os.path.join(src, "meta.json"), encoding="utf-8"))
    det_fp = os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")
    if os.path.exists(det_fp):
        det = json.load(open(det_fp, encoding="utf-8"))
        det["toc"] = meta["toc"]
        det["chapterCount"] = meta["chapterCount"]
        det["chapterTitles"] = meta["chapterTitles"]
        json.dump(det, open(det_fp, "w", encoding="utf-8"), ensure_ascii=False)
    bf = os.path.join(DP_PUBLIC, "books.json")
    books = json.load(open(bf, encoding="utf-8"))
    b = next((x for x in books if x.get("id") == bid), None)
    if b is not None:
        b["chapterCount"] = meta["chapterCount"]
        json.dump(books, open(bf, "w", encoding="utf-8"), ensure_ascii=False)


def main():
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    txt_only = "--txt-only" in sys.argv
    ocr_only = "--ocr-only" in sys.argv
    no_ocr = "--no-ocr" in sys.argv
    redo = "--redo" in sys.argv

    # 扫描 + 分类
    books = []
    for region in ["东方", "西方"]:
        rp = os.path.join(BOOKS_DIR, region)
        for author in sorted(os.listdir(rp)):
            ap = os.path.join(rp, author)
            if not os.path.isdir(ap):
                continue
            for fn in sorted(os.listdir(ap)):
                fp = os.path.join(ap, fn)
                if not os.path.isfile(fp) or not fn.lower().endswith(".pdf"):
                    continue
                rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
                if rel in MERGE_RULES:
                    continue
                books.append({"rel": rel, "fp": fp, "author": author, "file": fn})
    ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
    done = set(ckpt.get("books", {}).keys())
    # 注意: 不做 title 去重——DP books.json 的 pdf 条目多为无章节数据的占位（书架可见但打开为空）;
    #        epub/txt 同名版由 MERGE_RULES 跳过（理想国/存在与虚无）
    todo = [b for b in books if b["rel"] not in done or redo]
    if only:
        todo = [b for b in todo if only in b["rel"]]
    for b in todo:
        b["txt"] = has_text_layer(b["fp"]) and b["rel"] not in FORCE_OCR
    if txt_only:
        todo = [b for b in todo if b["txt"]]
    elif ocr_only:
        todo = [b for b in todo if not b["txt"]]
    elif no_ocr:
        todo = [b for b in todo if b["txt"]]
    todo.sort(key=lambda b: (0 if b["txt"] else 1, b["rel"]))  # 文本层优先
    total = len(todo)
    print(f"待处理 {total} 本（文本层 {sum(1 for b in todo if b['txt'])} / OCR {sum(1 for b in todo if not b['txt'])}）", flush=True)

    for i, b in enumerate(todo, 1):
        rel, fp = b["rel"], b["fp"]
        safe = re.sub(r"[^\w\-.]", "_", rel)
        title = os.path.splitext(b["file"])[0]
        tag = f"[{i}/{total}]《{title}》- {b['author']}"
        try:
            if b["txt"]:
                print(f"{tag} | 提取中(text-layer)", flush=True)
                pages = extract_text_pages(fp)
                src = "text-layer"
            else:
                def progress(cur, tot):
                    print(f"[{i}/{total}]《{title}》| OCR {int(cur * 100 / tot)}% ({cur}/{tot}页)", flush=True)
                print(f"{tag} | 提取中(ocr)", flush=True)
                pages = ocr_pdf_pages(fp, safe, ckpt, progress=progress)
                src = "ocr"
            print(f"[{i}/{total}]《{title}》| 清洗中", flush=True)
            clean, chapters, toc_end, appendix_start = dcb.process_pages(pages, safe, do_rebuild=True, rel=rel)
            print(f"[{i}/{total}]《{title}》| 检查中", flush=True)
            ok, msg = check_quality(clean, chapters, toc_end, appendix_start)
            # 找 bid
            bid = hashlib.md5(rel.encode()).hexdigest()[:12]
            sync_dp(bid, len(chapters))
            # 标记 done
            done_books = ckpt.setdefault("books", {})
            done_books[rel] = {"chapters": len(chapters), "src": src}
            if not ok:
                done_books[rel]["quality"] = msg
            json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
            mark = "✓" if ok else "⚠"
            words = sum(len(re.sub(r"\s", "", t)) for t in clean)
            print(f"[{i}/{total}]{mark}《{title}》| 入库 {len(chapters)}章 {words/10000:.1f}万字 | 检查{msg}", flush=True)
        except Exception as e:
            print(f"[{i}/{total}]✗《{title}》| 失败: {e}", flush=True)
    print("\n===== 处理完成 =====", flush=True)


if __name__ == "__main__":
    main()
