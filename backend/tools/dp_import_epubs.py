# -*- coding: utf-8 -*-
"""
dp_import_epubs.py — 补入库 chapterCount<=1 的 epub（2026-08-05 用户报告无分章）
背景: 80 本 epub 是骨架 detail（dp_epub_covers 建的占位）——rebuild_spine 漏跑/失败的
修复:
  1. 从 F:/philosophy 反查所有 epub 的 rel → fp（bid = md5(rel)[:12] 匹配 books.json id）
  2. 目标 = books.json 中 file_type==epub 且 chapterCount<=1
  3. 复用 rebuild_spine.extract() 入库（exec 函数定义段 + 路径注入, 不跑全量主循环）
  4. 每本写 chapters/{bid}/meta.json + {i}.json + detail（迁移旧 summary/tags）
  5. 失败记录 traceback 到日志, 不中断
  6. 幂等: meta.json 存在且 chapterCount>0 → 跳过（中断重跑安全）
封面/rank/summary 由既有管线补: dp_epub_covers.py → dp_score_books.py → gen_summaries.py
"""
import sys, io, os, json, hashlib

ALL = "--all" in sys.argv  # --all: 全量重入库（锚点切割后重跑全部 epub）; 默认: 只补 ch<=1

# 双通道日志: sys.__stdout__（不受 exec 的 stdout 包装影响）+ 日志文件
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_import_epubs.log")
def _log(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    try:
        sys.__stdout__.write(msg + "\n")
        sys.__stdout__.flush()
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)  # backend/
PHILO = r"F:/philosophy"
CDIR = os.path.join(BASE, "data", "book_chapters")
DDIR = os.path.join(BASE, "data", "book_detail")
BOOKS_FILE = os.path.join(BASE, "..", "app", "public", "books.json")

# exec rebuild_spine 函数定义段（主循环在 'count=0' 之后, 不执行）
_src = open(os.path.join(TOOLS, "rebuild_spine.py"), encoding="utf-8").read()
_ns = {"__file__": os.path.join(TOOLS, "rebuild_spine.py")}
exec(_src.split("count=0")[0], _ns)
# 重定向 rebuild_spine 的路径常量到正确位置（其 BASE_DIR 基于注入的 __file__）
_ns["BASE_DIR"] = BASE
_ns["CDIR"] = CDIR
_ns["DDIR"] = DDIR
_ns["EXTRACTED_IMG_DIR"] = os.path.join(BASE, "data", "book_images")
extract = _ns["extract"]


def find_epubs():
    """F:/philosophy 全量扫描 epub: rel → fp（东方/西方, 不含 new）"""
    found = {}
    for region in ("东方", "西方"):
        rp = os.path.join(PHILO, region)
        for root, dirs, files in os.walk(rp):
            for fn in files:
                if fn.lower().endswith(".epub"):
                    rel = os.path.relpath(os.path.join(root, fn), PHILO).replace("\\", "/")
                    found[rel] = os.path.join(root, fn)
    return found


def main():
    books = json.load(open(BOOKS_FILE, encoding="utf-8"))
    epubs = find_epubs()
    _log(f"epub 文件: {len(epubs)}")
    # 目标: --all 全量重入库（锚点切割后重跑）; --only 书名 单本重导; 默认只补 ch<=1
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
        targets = [b for b in books if b.get("file_type") == "epub" and only in b.get("title", "")]
    else:
        targets = [b for b in books if b.get("file_type") == "epub" and (ALL or (b.get("chapterCount") or 0) <= 1)]
    _log(f"目标: {len(targets)} ({'全量重入库' if ALL else ('--only' if '--only' in sys.argv else 'ch<=1')})")
    ok, fail = 0, 0
    for b in targets:
        bid = b["id"]
        # 反查 rel: md5 匹配
        rel = None
        for r in epubs:
            if hashlib.md5(r.encode("utf-8")).hexdigest()[:12] == bid:
                rel = r
                break
        if rel is None:
            _log(f"  !! 文件未找到: {b['title']} (bid {bid})")
            fail += 1
            continue
        # 幂等: 已有章节且 >0 章（--all / --only 模式全量重跑, 不跳过）
        bd = os.path.join(CDIR, bid)
        if not ALL and "--only" not in sys.argv and os.path.exists(os.path.join(bd, "meta.json")):
            try:
                m = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
                if m.get("chapterCount", 0) > 0:
                    _log(f"  = 跳过(已入库): {b['title']} ({m['chapterCount']}章)")
                    ok += 1
                    continue
            except Exception:
                pass
        _log(f"  → {rel}")
        try:
            # 旧 detail 的 summary/tags 迁移
            old_det = {}
            dp = os.path.join(DDIR, f"{bid}.json")
            if os.path.exists(dp):
                try:
                    old_det = json.load(open(dp, encoding="utf-8"))
                except Exception:
                    pass
            os.makedirs(bd, exist_ok=True)
            chs, toc_entries, cover, images = extract(epubs[rel], bid)
            if not chs:
                raise RuntimeError("extract 返回空章节")
            # 清旧章节文件重写
            for fn in os.listdir(bd):
                os.remove(os.path.join(bd, fn))
            toc_titles = [t._text if hasattr(t, "_text") else str(t) for t in toc_entries]
            # toc 用对象数组(与 pdf 通道/人工重建一致): 前端 ChapterReader 按 item.title/item.index 渲染;
            # 章节文件标题最可靠(与 toc_titles 可能错位——epub 目录含"目录"等非章条目)
            toc_obj = [{"type": "chapter", "title": (c.get("title") or toc_titles[i] if i < len(toc_titles) else c.get("title") or f"第{i+1}章"), "index": i}
                       for i, c in enumerate(chs)]
            meta = {"bookId": bid, "title": os.path.splitext(os.path.basename(rel))[0],
                    "author": rel.split("/")[1].replace("###", "").strip(),
                    "toc": toc_obj, "cover": cover, "chapterCount": len(chs),
                    "chapterTitles": [c.get("title") for c in chs]}
            json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"),
                      ensure_ascii=False)
            for i, c in enumerate(chs):
                c["index"] = i
                json.dump(c, open(os.path.join(bd, f"{i}.json"), "w", encoding="utf-8"),
                          ensure_ascii=False)
            # public 双写（前端读取链; 与 pdf 通道一致, 避免 detail 同步时 public 章节过期）
            pub = os.path.join(BASE, "..", "app", "public", "backend", "data", "book_chapters", bid)
            os.makedirs(pub, exist_ok=True)
            for fn in os.listdir(pub):
                os.remove(os.path.join(pub, fn))
            for fn in os.listdir(bd):
                if fn.endswith(".json"):
                    import shutil
                    shutil.copy2(os.path.join(bd, fn), os.path.join(pub, fn))
            # detail（迁移 summary/tags）
            detail = {k: meta[k] for k in ["bookId", "title", "author", "cover", "toc",
                                           "chapterCount", "chapterTitles"]}
            detail["toc"] = toc_obj  # 确保 detail 也用对象 toc
            if not detail.get("cover") and old_det.get("cover"):
                detail["cover"] = old_det["cover"]  # 重导未提取到封面时保留旧封面
            detail["region"] = rel.split("/")[0]
            detail["file_type"] = "epub"
            if old_det.get("summary"):
                detail["summary"] = old_det["summary"]
            if old_det.get("tags"):
                detail["tags"] = old_det["tags"]
            json.dump(detail, open(os.path.join(DDIR, f"{bid}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=2)
            json.dump(detail, open(os.path.join(
                BASE, "..", "app", "public", "book_detail", f"{bid}.json"), "w", encoding="utf-8"),
                ensure_ascii=False, indent=2)
            _log(f"    ✓ {len(chs)}章 toc{len(toc_titles)} 摘要{'迁移' if detail.get('summary') else '缺'}")
            ok += 1
        except Exception as e:
            import traceback
            _log(f"    ✗ FAIL: {type(e).__name__}: {e}")
            for line in traceback.format_exc().splitlines()[-6:]:
                _log("      " + line)
            fail += 1
    _log(f"done: ok {ok}, fail {fail}")


if __name__ == "__main__":
    main()
