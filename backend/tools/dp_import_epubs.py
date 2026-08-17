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

# S12（audit 2026-08-17）: 不再按字面量 "count=0" 切片后 exec 源码——
# rebuild_spine 主循环已包进 if __name__ == "__main__"（可安全 import 且只加载函数定义）,
# 这里用 importlib 显式加载该已知文件并只调用 extract()。
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("rebuild_spine", os.path.join(TOOLS, "rebuild_spine.py"))
_spine_mod = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_spine_mod)
# 路径重定向到 backend/ 数据目录（rebuild_spine 自身常量基于其文件位置, 修正为仓库实际布局）
_spine_mod.BASE_DIR = BASE
_spine_mod.CDIR = CDIR
_spine_mod.DDIR = DDIR
_spine_mod.EXTRACTED_IMG_DIR = os.path.join(BASE, "data", "book_images")
extract = _spine_mod.extract


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
            meta = {"bookId": bid, "title": os.path.splitext(os.path.basename(rel))[0],
                    "author": rel.split("/")[1].replace("###", "").strip(),
                    "toc": toc_titles, "cover": cover, "chapterCount": len(chs),
                    "chapterTitles": [c.get("title") for c in chs]}
            json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"),
                      ensure_ascii=False)
            for i, c in enumerate(chs):
                c["index"] = i
                json.dump(c, open(os.path.join(bd, f"{i}.json"), "w", encoding="utf-8"),
                          ensure_ascii=False)
            # detail（迁移 summary/tags）
            detail = {k: meta[k] for k in ["bookId", "title", "author", "cover", "toc",
                                           "chapterCount", "chapterTitles"]}
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
