# -*- coding: utf-8 -*-
"""
dp_fix_titles.py — 修复 8 本错误标题 epub（2026-08-05 严谨检查发现）
正确书名来自 scripts/_review_books.csv（用户确认权威来源）
步骤:
  1. 重命名文件（书名还原；作者目录不动）
  2. 复用 rebuild_spine.extract() 重入库章节（只 exec 函数定义段, 不跑全量主循环）
  3. 迁移旧 detail 的 summary/tags 到新 detail
  4. 清理旧 bid 孤儿（chapters/detail/public detail/covers 文件/covers.json 条目）
封面由 dp_epub_covers.py 重跑补; rank 由 dp_score_books.py 重评; summary 缺口由 gen_summaries.py 补
"""
import sys, io, os, json, hashlib, shutil

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass  # 管道/无控制台时 buffer 可能已关闭, 保留默认 stdout

# 全量 print 走 _log: 双通道（sys.__stdout__ + 日志文件）
# 背景: exec rebuild_spine 顶部代码时其 stdout 包装（line 7）会替换 sys.stdout,
# 旧 wrapper 被 GC 后底层管道被关闭 → 后续 print 抛 "I/O operation on closed file"
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_fix_titles.log")
import builtins

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

builtins.print = _log

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)  # backend/
PHILO = r"F:/philosophy"
CDIR = os.path.join(BASE, "data", "book_chapters")
DDIR = os.path.join(BASE, "data", "book_detail")
PUB_COVERS = os.path.join(BASE, "..", "app", "public", "covers")
PUB_DETAIL = os.path.join(BASE, "..", "app", "public", "book_detail")
COVERS_JSON = os.path.join(BASE, "..", "app", "public", "covers.json")
SDIR = os.path.join(BASE, "data", "book_summaries.json")

# 只 exec rebuild_spine 的函数定义段（主循环在 'count=0' 之后, 不执行）
_src = open(os.path.join(TOOLS, "rebuild_spine.py"), encoding="utf-8").read()
_ns = {"__file__": os.path.join(TOOLS, "rebuild_spine.py")}
exec(_src.split("count=0")[0], _ns)
extract = _ns["extract"]
# exec 时 rebuild_spine 的 BASE_DIR 基于注入的 __file__（backend/tools）,
# 其 CDIR/DDIR/EXTRACTED_IMG_DIR 会指向废弃的 backend/tools/data/ —— 重定向到正确位置
_ns["BASE_DIR"] = BASE
_ns["CDIR"] = CDIR
_ns["DDIR"] = DDIR
_ns["EXTRACTED_IMG_DIR"] = os.path.join(BASE, "data", "book_images")

# 正确书名（csv 权威）; 文件名用全角冒号（Windows 不允许半角 :）, 引号去掉
RENAME = {
    "东方/徐英瑾/2024-03《哲学的二十个夜晚》.epub": "东方/徐英瑾/哲学的二十个夜晚.epub",
    "东方/李浩然/2024-03《哲学进化论》.epub": "东方/李浩然/哲学进化论：一场关于世界、意识、道德的无止境追问.epub",
    "东方/郁喆隽/50Tang Jing Dian Zhe Xue Si Wei - Yu Zhe Jun.epub": "东方/郁喆隽/50堂经典哲学思维课.epub",
    "西方/赵林/2022-01《西方哲学史讲演录》.epub": "西方/赵林/西方哲学史讲演录.epub",
    "西方/威廉·B. 欧文/2018-09《像哲学家一样生活》斯多葛哲学的生活艺术.epub": "西方/威廉·B. 欧文/像哲学家一样生活：斯多葛哲学的生活艺术.epub",
    "西方/约翰·史崔勒基/Zhong Fan Shi Jie Jin Tou De Ka - Yue Han _Shi Cui Le Ji.epub": "西方/约翰·史崔勒基/重返世界尽头的咖啡馆.epub",
    "西方/萨姆·哈里斯/_Huo Zai Dang Xia _Zhi Nan (She - Sa Mu _Ha Li Si.epub": "西方/萨姆·哈里斯/活在当下指南.epub",
    "西方/卡尔·雅斯贝尔斯/2024-03《写给每个人的哲学书》.epub": "西方/卡尔·雅斯贝尔斯/写给每个人的哲学书：雅斯贝尔斯的14堂哲学思维课.epub",
}


def bid_of(rel):
    return hashlib.md5(rel.encode("utf-8")).hexdigest()[:12]


def main():
    summaries = json.load(open(SDIR, encoding="utf-8")) if os.path.exists(SDIR) else {}
    for old_rel, new_rel in RENAME.items():
        old_fp = os.path.join(PHILO, *old_rel.split("/"))
        new_fp = os.path.join(PHILO, *new_rel.split("/"))
        renamed = os.path.exists(new_fp)  # 中断恢复: rename 已完成则幂等续跑
        if not os.path.exists(old_fp) and not renamed:
            print(f"!! 源不存在（跳过）: {old_rel}", flush=True)
            continue
        old_bid, new_bid = bid_of(old_rel), bid_of(new_rel)
        title = os.path.splitext(os.path.basename(new_rel))[0]
        author = new_rel.split("/")[1].replace("###", "").strip()
        region = "东方" if new_rel.startswith("东方") else "西方"

        # 1. 迁移旧 summary/tags
        old_dp = os.path.join(DDIR, f"{old_bid}.json")
        old_meta = {}
        if os.path.exists(old_dp):
            old_meta = json.load(open(old_dp, encoding="utf-8"))

        # 2. 重命名（已改名则跳过, 中断恢复）
        if not renamed:
            os.makedirs(os.path.dirname(new_fp), exist_ok=True)
            os.rename(old_fp, new_fp)
        print(f"[{old_rel}] → [{new_rel}]", flush=True)

        # 3. 重入库章节（extract 写图片到 book_images）
        os.makedirs(os.path.join(CDIR, new_bid), exist_ok=True)  # extract 写盘需 bid 目录已存在
        chs, toc_entries, cover, images = extract(new_fp, new_bid)
        bd = os.path.join(CDIR, new_bid)
        if os.path.exists(bd):
            shutil.rmtree(bd)
        os.makedirs(bd, exist_ok=True)
        toc_titles = [t._text if hasattr(t, "_text") else str(t) for t in toc_entries]
        meta = {"bookId": new_bid, "title": title, "author": author, "toc": toc_titles,
                "cover": cover, "chapterCount": len(chs),
                "chapterTitles": [c["title"] for c in chs]}
        json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
        # 每章一文件（jsDelivr 读取格式: {bid}/{i}.json）
        for i, c in enumerate(chs):
            json.dump(c, open(os.path.join(bd, f"{i}.json"), "w", encoding="utf-8"), ensure_ascii=False)

        # 4. detail（迁移 summary/tags, 优先旧 detail, 其次 book_summaries）
        detail = {"bookId": new_bid, "title": title, "author": author, "cover": cover,
                  "toc": toc_titles, "chapterCount": len(chs),
                  "chapterTitles": [c["title"] for c in chs],
                  "region": region, "file_type": "epub"}
        if old_meta.get("summary"):
            detail["summary"] = old_meta["summary"]
        if old_meta.get("tags"):
            detail["tags"] = old_meta["tags"]
        if not detail.get("summary"):
            for sk in (f"{title}||{author}", f"{title}||", title):
                s = summaries.get(sk)
                if s and s.get("summary"):
                    detail["summary"] = s["summary"]
                    if s.get("tags") and not detail.get("tags"):
                        detail["tags"] = s["tags"]
                    break
        json.dump(detail, open(os.path.join(DDIR, f"{new_bid}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"  → {new_bid} 章节 {len(chs)} 摘要 {'迁移' if detail.get('summary') else '缺'}", flush=True)

        # 5. 清孤儿（旧 bid）
        old_cdir = os.path.join(CDIR, old_bid)
        if os.path.exists(old_cdir):
            shutil.rmtree(old_cdir)
        for d in (DDIR, PUB_DETAIL):
            fp = os.path.join(d, f"{old_bid}.json")
            if os.path.exists(fp):
                os.remove(fp)
        for fn in os.listdir(PUB_COVERS):
            if fn.startswith(old_bid + "_"):
                os.remove(os.path.join(PUB_COVERS, fn))
        if os.path.exists(COVERS_JSON):
            cm = json.load(open(COVERS_JSON, encoding="utf-8"))
            if old_bid in cm:
                del cm[old_bid]
                json.dump(cm, open(COVERS_JSON, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"  → 旧 {old_bid} 孤儿已清", flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    main()
