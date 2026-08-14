# -*- coding: utf-8 -*-
"""
rebuild_auto.py — 全库通用重建 v2（2026-08-07 全库核查 A2/A4）
旧书段落压扁（每章 1-2 大段）→ 用已修复的 dp_clean_book 全自动重建（do_rebuild=True）
安全: 重建前备份旧目录 → 字数守恒校验（新旧差 <10% 才接受, 否则回滚备份）
用法: python rebuild_auto.py [bid ...]  （无参数 = 全部 A2 名单）
"""
import sys, os, json, re, shutil, hashlib

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import dp_clean_book as dcb

CH = os.path.join(BASE, "data", "book_chapters")
PHI_DET = os.path.join(BASE, "data", "book_detail")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
CKPT = json.load(open(os.path.join(BASE, "data", "dp_pdf_import_ckpt.json"), encoding="utf-8"))
BAK = os.path.join(BASE, "data", "_rebuild_bak")
PHILO = "F:/philosophy"

A2_DEFAULT = ("00fadd7de47c 0ed8c0c49e2f 1085686cbd33 17c85f942c78 17fda3378628 "
              "21d51965ccbb 221f09d04944 2321fab7e032 2cbf90eb6f69 2e66606c2854 "
              "302d32b2975c 309de54e4392 324c13db486e 343df8697039 3e85310c7179 "
              "4be7b72cf01d 536c2b9338e5 53d1b4ff90d2 60eed962806b 64056c6623ee "
              "6bcbc6a5904f 7729ccdecb0f 8ae083851bd8 a04933b82f3c a26240ee8f45 "
              "a3e1832a509d a44cb4c8f8d9 a6d6def88c3b a9955bc4ee64 aa21ac425e87 "
              "aa614e2cf92d aacc867ec43c ad61ed0fd976 add6c213fde8 b43aeb7ccc57 "
              "bbac1be0bb4b bcc83fdfca5e bedc9c78dfdf c13b139d1db3 d0c5ade4fcbd "
              "d54046539e0d d54981640212 d8bcc10d42ff dd03ec6572e7 e3a52553c303 "
              "e574c8e7f515 ef76ae88994f f08c1ead3164 f11f1b13c278 f9549bd811f6").split()


def bid2rel(bid):
    for k in (CKPT.get("books") or {}):
        if hashlib.md5(k.encode()).hexdigest()[:12] == bid:
            return k, re.sub(r"[^\w\-.]", "_", k)
    return None, None


def words_of(bd):
    meta = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
    w = 0
    for i in range(meta["chapterCount"]):
        fp = os.path.join(bd, f"{i}.json")
        if os.path.exists(fp):
            ch = json.load(open(fp, encoding="utf-8"))
            w += sum(len(x.get("value", "")) for x in ch.get("content", []) if x.get("type") == "text")
    return w, meta


def sync_three(bid):
    bd = os.path.join(CH, bid)
    meta = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
    for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(bd, dst)
    for det_pa in (os.path.join(PHI_DET, f"{bid}.json"),
                   os.path.join(DP_BACKEND, "data", "book_detail", f"{bid}.json"),
                   os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")):
        if os.path.exists(det_pa):
            det = json.load(open(det_pa, encoding="utf-8"))
            for k in ("toc", "chapterCount", "chapterTitles"):
                det[k] = meta[k]
            det["title"] = meta["title"]
            json.dump(det, open(det_pa, "w", encoding="utf-8"), ensure_ascii=False)


def rebuild_one(bid, force_fitz=False):
    rel, safe = bid2rel(bid)
    if not rel:
        print(f"✗ {bid}: 不在 ckpt books", flush=True)
        return False
    bd = os.path.join(CH, bid)
    if not os.path.exists(os.path.join(bd, "meta.json")):
        print(f"✗ {bid}: 无 meta", flush=True)
        return False
    d = CKPT["ocr"].get(safe)
    if not d or force_fitz:
        # text-layer 书未写 ocr 段 → 直接从 PDF 文本层提取
        pdf = os.path.join(PHILO, rel.replace("/", os.sep))
        if not os.path.exists(pdf):
            print(f"✗ {bid}: ckpt 无 ocr 且 PDF 不存在 {pdf}", flush=True)
            return False
        import fitz
        doc = fitz.open(pdf)
        pages = [doc[i].get_text() or "" for i in range(doc.page_count)]
        doc.close()
        print(f"  {bid}: PDF 文本层 {len(pages)} 页", flush=True)
    else:
        pages_map = {int(k): v for k, v in d.items() if v and v != "__FAILED__"}
        pages = [pages_map.get(i, "") for i in range(max(pages_map) + 1)]
    old_words, old_meta = words_of(bd)
    # 备份旧目录（防丢内容回滚）
    bak_dir = os.path.join(BAK, bid)
    if os.path.exists(bak_dir):
        shutil.rmtree(bak_dir)
    shutil.copytree(bd, bak_dir)
    try:
        dcb.process_pages(pages, safe, do_rebuild=True, rel=rel)
    except Exception as e:
        print(f"✗ {bid}: 重建异常 {e} → 回滚", flush=True)
        shutil.rmtree(bd)
        shutil.copytree(bak_dir, bd)
        return False
    new_words, new_meta = words_of(bd)
    ratio = new_words / old_words if old_words else 0
    n_old = old_meta["chapterCount"]
    n_new = new_meta["chapterCount"]
    # 膨胀检测: >150% 说明切分重复（b43 217% 历史事故: fall-through 重复 append）→ 回滚
    if ratio < 0.90 or ratio > 1.50 or n_new < 2:
        print(f"✗ {bid} {old_meta.get('title','')[:18]!r}: 字数 {old_words}→{new_words} ({ratio:.0%}) 或章节 {n_old}→{n_new} 异常 → 回滚", flush=True)
        shutil.rmtree(bd)
        shutil.copytree(bak_dir, bd)
        return False
    # 保留旧 title/author（rebuild_chapters 生成的是文件名格式）
    mfp = os.path.join(bd, "meta.json")
    meta = json.load(open(mfp, encoding="utf-8"))
    if old_meta.get("title"):
        meta["title"] = old_meta["title"]
    if old_meta.get("author"):
        meta["author"] = old_meta["author"]
    json.dump(meta, open(mfp, "w", encoding="utf-8"), ensure_ascii=False)
    sync_three(bid)
    print(f"✓ {bid} {old_meta.get('title','')[:18]!r}: 字数 {old_words}→{new_words} ({ratio:.0%}) 章节 {n_old}→{n_new}", flush=True)
    return True


def main():
    force = "--fitz" in sys.argv
    bids = [b for b in sys.argv[1:] if not b.startswith("--")] or A2_DEFAULT
    ok = fail = 0
    for bid in bids:
        if rebuild_one(bid, force_fitz=force):
            ok += 1
        else:
            fail += 1
    print(f"\n完成: 成功 {ok} 失败 {fail}", flush=True)


if __name__ == "__main__":
    main()
