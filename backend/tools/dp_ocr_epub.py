# -*- coding: utf-8 -*-
"""
dp_ocr_epub.py — 图片型 epub OCR 入库（2026-08-07, 地下室手记 252 图）
解 epub 图片 → PaddleOCR 页级识别（页级断点续传 dp_epub_ocr_ckpt.json）
→ dp_clean_book.process_pages(do_rebuild=True) 重建 book_chapters
→ 同步 DP 双端 + detail + books.json chapterCount

v2 (页序修复): epub 阅读顺序由 OPF spine 决定（index-1..index-251 数字序），
  文件名 dict 序会把 index-100 排在 index-9 前导致正文页序错乱。
  现按 spine 顺序收集图片; ckpt 键 = spine 页序（旧字典序键段保留不冲突）。
  cover.jpeg 不在 spine 中 → 剔除不进正文。
"""
import sys, os, json, re, time, zipfile, hashlib, shutil
from pathlib import Path
from bs4 import BeautifulSoup
from paddleocr import PaddleOCR

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
# 注意: dp_clean_book 内部已包装 stdout（勿重复包装）
import dp_clean_book as dcb

EPUB = r"F:\philosophy\西方\费奥多尔·陀思妥耶夫斯基\地下室手记.epub"
REL = "西方/费奥多尔·陀思妥耶夫斯基/地下室手记.epub"
CKPT_FILE = os.path.join(BASE, "data", "dp_epub_ocr_ckpt.json")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")
CH = os.path.join(BASE, "data", "book_chapters")

RESTART_EVERY = 100
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


def spine_images(z, rootfile):
    """OPF spine 顺序的图片路径列表（不含 cover）"""
    names = z.namelist()
    opf_dir = os.path.dirname(rootfile) if "/" in (rootfile or "") else ""
    opf = BeautifulSoup(z.read(rootfile).decode("utf-8", "ignore"), "xml")
    manifest = {it.get("id"): it.get("href") for it in opf.find_all("item")}
    imgs = []
    for idref in [s.get("idref") for s in opf.find_all("itemref")]:
        href = manifest.get(idref)
        if not href:
            continue
        p = (opf_dir + "/" + href) if opf_dir else href
        p = p.replace("\\", "/")
        html = BeautifulSoup(z.read(p).decode("utf-8", "ignore"), "html.parser")
        for im in html.find_all("img"):
            if im.get("src"):
                fp = os.path.normpath(os.path.join(os.path.dirname(p), im["src"])).replace("\\", "/")
                if fp in z.namelist():
                    imgs.append(fp)
    return imgs


def sync_dp(bid, meta):
    src = os.path.join(CH, bid)
    for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
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
    z = zipfile.ZipFile(EPUB)
    # OPF 定位
    rootfile = None
    for n in z.namelist():
        if n.endswith("container.xml"):
            m = re.search(r'full-path="([^"]+)"', z.read(n).decode("utf-8", "ignore"))
            if m:
                rootfile = m.group(1)
                break
    imgs = spine_images(z, rootfile)
    print(f"spine 顺序图片: {len(imgs)} 张（不含 cover）", flush=True)
    if not imgs:
        print("✗ spine 无图片", flush=True)
        return

    # 旧字典序段（v1 已 OCR 的文本）→ 按文件名映射到新页序, 缺失/FAILED 补 OCR
    ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
    old_done = ckpt.get(REL, {})  # 旧键: dict 序位置 → 文本
    old_names = sorted(n for n in z.namelist()
                       if n.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".webp")))
    name_to_old = {n: str(i) for i, n in enumerate(old_names)}
    key = REL + "#spine"
    done = ckpt.get(key, {})

    tmp = Path(os.environ.get("TEMP", ".")) / "dp_epub_paddle"
    tmp.mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(imgs):
        if str(i) in done and done.get(str(i)) != "__FAILED__":
            continue
        text = old_done.get(name_to_old.get(name, ""), "")
        if text and text != "__FAILED__":
            done[str(i)] = text
            continue
        # 补 OCR（含 v1 FAILED 页重试）
        data = z.read(name)
        ext = os.path.splitext(name)[1] or ".png"
        fp = tmp / f"p{i:04d}{ext}"
        fp.write_bytes(data)
        text = ""
        try:
            text = ocr_page(str(fp))
        except Exception as e:
            print(f"  页{i} 异常: {e}", flush=True)
        done[str(i)] = text or "__FAILED__"
        if i % 5 == 0:
            ckpt[key] = done
            json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"OCR 进度: {i + 1}/{len(imgs)}", flush=True)
        time.sleep(0.1)
    ckpt[key] = done
    json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    fails = [k for k, v in done.items() if v == "__FAILED__"]
    print(f"OCR 完成 {len(imgs)} 页, FAILED {len(fails)} 页", flush=True)
    if fails:
        print("  失败页:", [f"index-{int(k)+1}_1.png" for k in sorted(fails)], flush=True)

    pages_map = {int(k): v for k, v in done.items() if v and v != "__FAILED__"}
    if not pages_map:
        print("✗ 无 OCR 文本", flush=True)
        return
    total = max(pages_map) + 1
    pages = [pages_map.get(i, "") for i in range(total)]
    safe = re.sub(r"[^\w\-.]", "_", REL)
    clean, chapters, toc_end, appendix_start = dcb.process_pages(pages, safe, do_rebuild=True, rel=REL)
    words = sum(len(re.sub(r"\s", "", t)) for t in clean)
    bid = hashlib.md5(REL.encode()).hexdigest()[:12]
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    sync_dp(bid, meta)
    print(f"✓ {meta.get('title')}: {len(chapters)} 段 → {meta['chapterCount']} 块 {words/10000:.1f}万字, 已同步双端", flush=True)
    print("下一步: 向量重建（build_embeddings.py 或 dp_embed_missing.py " + bid + "）", flush=True)


if __name__ == "__main__":
    main()
