# -*- coding: utf-8 -*-
"""单本重导: 复用 dp_pdf_import 逻辑, ckpt 用独立临时文件 (不碰主 ckpt, 与引擎并行安全)
用法: python _tmp_reimport.py <书名片段>...
"""
import sys, io, os, json, re, time, hashlib, shutil
from pathlib import Path

# 注意: 不在这里包装 stdout — dp_pdf_import 模块级已包装 (TextIOWrapper), 双重包装会 I/O closed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv_keep = sys.argv
sys.argv = ['dp_pdf_import.py']  # 模块级 SHARD/ONLY 解析会用 argv, 先清掉关键字
import dp_pdf_import as imp
sys.argv = _argv_keep

TMP_CKPT = os.path.join(imp.BASE_DIR, "data", "dp_pdf_import_ckpt_tmp.json")
imp.CKPT_FILE = TMP_CKPT  # ocr_pdf 内部 dump 目标 → 独立临时文件, 不碰主 ckpt

# ── 调试: 打印每页 OCR 输入图片 + 首行文本 (定位 OCR 污染) ──
_orig_ocr_page = imp.ocr_page
def _dbg_ocr_page(img_path):
    t = _orig_ocr_page(img_path)
    head = t.split("\n")[0][:20] if t else ""
    print("  OCR %s | %s" % (os.path.basename(img_path), head), flush=True)
    return t
imp.ocr_page = _dbg_ocr_page

# ── 污染页跳过: 源 PDF 混入的无关页 (2026-08-10 定位: 现象学的观念 p20-p27 = 论文页 4-11) ──
# 定位方法: 逐页 OCR 首行对比, 书页 1(讲座的思路) 后 8 页是'中国情境下的员工建言行为影响因素研究'论文
SKIP_PAGES = {
    '西方/埃德蒙德·胡塞尔/现象学的观念.pdf': set(range(20, 28)),
}

def reimport(rel):
    fp = os.path.join(imp.BOOKS_DIR, rel)
    if not os.path.exists(fp):
        print("  源不存在:", fp); return
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    safe = re.sub(r"[^\w\-.]", "_", rel)
    t0 = time.time()
    print(f"[{rel}]", flush=True)
    # ckpt: 独立临时文件（OCR 页级断点）
    ckpt = {}
    if os.path.exists(TMP_CKPT):
        try:
            ckpt = json.load(open(TMP_CKPT, encoding="utf-8"))
        except Exception:
            ckpt = {}
    if imp.has_text_layer(fp) and rel not in imp.FORCE_OCR:
        text = imp.extract_text_layer(fp)
        src = "text-layer"
    else:
        text = imp.ocr_pdf(fp, ckpt, safe)  # ocr_pdf 内部每 10 页 dump 到 imp.CKPT_FILE
        src = "ocr"
        skips = SKIP_PAGES.get(rel)
        if skips:
            # 按页过滤污染页 (OCR 完成后 TMP_CKPT 已含页级文本)
            ckpt2 = json.load(open(TMP_CKPT, encoding="utf-8"))
            done = ckpt2.get("ocr", {}).get(safe, {})
            n = max([int(k) for k in done] or [0]) + 1
            pages = [done.get(str(i), "") if done.get(str(i)) != "__FAILED__" else ""
                     for i in range(n) if i not in skips]
            text = "\n\n".join(p for p in pages if p)
            print("    [跳过污染页 %s, 保留 %d 页]" % (sorted(skips), len(pages)), flush=True)
    author = imp.AUTHOR_FIX.get(rel, Path(fp).parent.name)
    for sub, val in imp.MERGE_RULES.items():
        if not val: continue
        main, merged_author = val
        if rel == main:
            author = merged_author; break
    chapters = imp.chapterize(text)
    blocks_chs = [{"title": c["title"], "content": imp.to_blocks(c["text"])} for c in chapters]
    bd = os.path.join(imp.CDIR, bid)
    if os.path.exists(bd):
        shutil.rmtree(bd)
    os.makedirs(bd, exist_ok=True)
    for idx, ch in enumerate(blocks_chs):
        ch["index"] = idx
        json.dump(ch, open(os.path.join(bd, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    toc_titles = [c["title"] for c in blocks_chs]
    toc_obj = [{"type": "chapter", "title": t, "index": i} for i, t in enumerate(toc_titles)]
    meta = {"bookId": bid, "title": Path(fp).stem, "author": author, "toc": toc_obj,
            "cover": None, "chapterCount": len(blocks_chs), "chapterTitles": toc_titles}
    json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
    cover = imp.make_cover(fp, bid)
    meta["cover"] = cover
    json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
    title = Path(fp).stem
    detail = {k: meta[k] for k in ["bookId", "title", "author", "cover", "toc", "chapterCount", "chapterTitles"]}
    detail["region"] = rel.split("/")[0]; detail["file_type"] = "pdf"; detail["extract"] = src
    for sk in [f"{title}||{author}", f"{title}||", title]:
        s = imp.summaries.get(sk)
        if s and s.get("summary"): detail["summary"] = s["summary"]
        if s and s.get("tags"): detail["tags"] = s["tags"]
        break
    json.dump(detail, open(os.path.join(imp.DDIR, f"{bid}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    # 清理临时 ckpt（避免下次复用过期页）
    if os.path.exists(TMP_CKPT):
        os.remove(TMP_CKPT)
    print(f"    ✓ {len(blocks_chs)}章 {src} {time.time()-t0:.0f}s", flush=True)
    # 章节文件结构摘要
    sizes = []
    for idx, ch in enumerate(blocks_chs):
        sizes.append((idx, len(ch["content"]), ch["title"][:18]))
    print("    ", sizes, flush=True)

if __name__ == "__main__":
    for kw in sys.argv[1:]:
        for region in ["东方", "西方"]:
            rp = os.path.join(imp.BOOKS_DIR, region)
            for author in sorted(os.listdir(rp)):
                ap = os.path.join(rp, author)
                if not os.path.isdir(ap): continue
                for fn in sorted(os.listdir(ap)):
                    if kw in fn and fn.lower().endswith(".pdf"):
                        rel = os.path.relpath(os.path.join(ap, fn), imp.BOOKS_DIR).replace("\\", "/")
                        reimport(rel)
