# -*- coding: utf-8 -*-
"""
dp_sync_books.py — 汇总生成 app/public/books.json（PDF 入库后同步）
规则:
  - 扫描 F:/philosophy 东方/西方（new 不管）
  - 合并规则（一书多作者分居两文件夹）: 副文件跳过, 主文件 author 合并
  - 大问题 epub 两份: 留 mtime 新的
  - detail 存在 → chapterCount/rank/tags/summary 从 detail 取
  - txt = 佚失占位（file_size 0, chapterCount 0）
排序: rank 降序（无 rank 排最后）
输出: app/public/books.json + backend/data/books_catalog.json
"""
import os, sys, io, json, hashlib, re

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # DeepPhilosophy/
PHILOSOPHY_DIR = os.getenv("PHILOSOPHY_BOOKS_DIR", "F:/philosophy")
BOOKS_FILE = os.path.join(BASE, "app", "public", "books.json")
# 唯一数据源 = backend/data/book_detail（dp_pdf_import / dp_epub_covers / gen_summaries 都写这里）
DETAIL_DIR = os.path.join(BASE, "backend", "data", "book_detail")
PUBLIC_DETAIL_DIR = os.path.join(BASE, "app", "public", "book_detail")
CATALOG_FILE = os.path.join(BASE, "backend", "data", "books_catalog.json")
RANK_FILE = os.path.join(BASE, "backend", "data", "book_rankings.json")

# 书名修复: 文件名(stem) → 显示名（Windows 不允许 / 等字符, 如 S/Z）
TITLE_FIX = {"SZ": "S/Z", "哲学与人生 (1)": "哲学与人生"}

# rank 按 (title, author) 匹配（score_item 输出 + git 备份兜底, 比 detail.rank 权威）
_ranks = {}
_ranks_title_only = {}
for src in [RANK_FILE, BOOKS_FILE, os.path.join(BASE, "backend", "data", "rank_backup.json")]:
    if not os.path.exists(src):
        continue
    data = json.load(open(src, encoding="utf-8"))
    if isinstance(data, dict) and "books" in data:
        data = data.get("books", [])
    if isinstance(data, list):
        for r in data:
            t, a, rk = r.get("title", ""), r.get("author", ""), r.get("rank")
            if rk:
                _ranks[(t, a)] = rk
                _ranks_title_only.setdefault(t, rk)
    elif isinstance(data, dict):
        # rank_backup.json 格式: "title||author" → rank, "T:title" → rank
        for k, v in data.items():
            if k.startswith("T:"):
                _ranks_title_only.setdefault(k[2:], v)
            elif "||" in k:
                t, a = k.split("||", 1)
                _ranks[(t, a)] = v

# 与 dp_pdf_import.py 一致的合并规则（副文件 → 主文件 rel）
MERGE_RULES = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf":
        ("西方/卡尔·马克思/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf", "卡尔·马克思/弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/共产党宣言.pdf":
        ("西方/卡尔·马克思/共产党宣言.pdf", "卡尔·马克思/弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf":
        ("西方/卡尔·马克思/德意志意识形态（节选本）.pdf", "卡尔·马克思/弗里德里希·恩格斯"),
    "西方/弗里德里希·恩格斯/马克思恩格斯文集.epub":
        ("西方/卡尔·马克思/马克思恩格斯文集.epub", "卡尔·马克思/弗里德里希·恩格斯"),
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf":
        ("西方/扬布里柯/哲学规劝录 哲学的慰藉.pdf", "扬布里柯/波爱修斯"),
    # epub 版已在库: pdf 版跳过, 避免书架重复
    # 存在与虚无: epub 版入库, pdf 版仅借其首页渲染做封面（epub 源无内置封面）
    "西方/让-保罗·萨特/存在与虚无.pdf": None,
    "西方/柏拉图/理想国.pdf": None,
    # 逻辑哲学论: epub 版已在库（REMOVED_PDFS.txt #13 下架, 文件留 F:/philosophy 做源）
    "西方/路德维希·维特根斯坦/逻辑哲学论.pdf": None,
    # 民主主义与教育: 1页封面渲染假pdf（无正文）: 跳过, epub 版入库
    "西方/约翰·杜威/民主主义与教育-王承绪译.pdf": None,
    # 神圣家族 txt 两份（马克思/恩格斯文件夹各一, 合著内容相同）: 只留马克思版
    "西方/弗里德里希·恩格斯/神圣家族.txt": None,
    # 双作者合著（2026-08-12 用户整理, 各作者目录一份）: 合并到第一作者, author 用 作者1/作者2
    "西方/詹姆斯·菲泽/西方哲学史（第9版）.epub": None,
    "西方/马修理查德/僧侣与哲学家.epub": None,
}
# 2026-08-12 用户整理磁盘后文件路径变化 → rel 变 → bid 变 → 旧章节成孤儿。
# 映射回旧 bid（章节数据在 book_chapters/{旧bid} 仍完好, 前端继续可读）, 副文件 None 跳过。
REL_BID_FIX = {
    "西方/撒穆尔·伊诺克·斯通普夫/西方哲学史（第9版）.epub":
        ("4a4a200536bd", "撒穆尔·伊诺克·斯通普夫/詹姆斯·菲泽"),
    "西方/詹姆斯·菲泽/西方哲学史（第9版）.epub": None,
    "西方/让-弗朗索瓦何维勒/僧侣与哲学家.epub":
        ("077532e4515e", "让-弗朗索瓦何维勒/马修·理查德"),
    "西方/马修理查德/僧侣与哲学家.epub": None,
    # 2026-08-12 用户确认: 11 本东方人写但内容为西方哲学 → 移西方区域（保 bid 保章节）
    "西方/书杰/哲学100问（套装共3册）.epub": ("a325bbdc496e", "书杰"),
    "西方/傅佩荣/哲学与人生 (1).epub": ("a8f6e375ccef", "傅佩荣"),
    "西方/刘小播/幸福的底层逻辑：关于人生的7堂哲学课.epub": ("e0b0b534b86e", "刘小播"),
    "西方/富增章成/别笑，我是正经哲学书.epub": ("a1448e164acc", "富增章成"),
    "西方/张玮/让孩子像哲学家一样会思考.epub": ("8331c039d11a", "张玮"),
    "西方/张祥龙/现象学导论七讲：从原著阐发原意.epub": ("ef76ae88994f", "张祥龙"),
    "西方/徐英瑾/哲学的二十个夜晚.epub": ("f9530a5e2ba9", "徐英瑾"),
    "西方/李浩然/哲学进化论：一场关于世界、意识、道德的无止境追问.epub": ("c10883852202", "李浩然"),
    "西方/金岳霖/逻辑：金岳霖哲学三书的理论基础.epub": ("fc835909559b", "金岳霖"),
    "西方/陈嘉映/哲学·科学·常识.epub": ("92c62220d4a3", "陈嘉映"),
    "西方/陈嘉映/走出唯一真理观.epub": ("81218d6e1646", "陈嘉映"),
}
# 大问题 epub 两份: 留 mtime 新的（旧的跳过）
DUP_GROUP = ["西方/合集&概述/大问题.epub", "西方/罗伯特•所罗门/大问题.epub"]

# 降级书（CHKLIST #261/#304, 2026-08-11 用户确认）: 源 pdf 留在 F:/philosophy,
# 内容不合格降级 txt 占位——扫描到强制生成占位条目, 不得复活为 pdf
DEMOTE_RULES = {
    "西方/威拉德·范·奥曼·蒯因/语词和对象.pdf": ("语词和对象", "威拉德·范·奥曼·蒯因"),
    "西方/莫里茨·石里克/普通认识论.pdf": ("普通认识论", "莫里茨·石里克"),
}


def main():
    # 大问题留新
    skip = set()
    if all(os.path.exists(os.path.join(PHILOSOPHY_DIR, r)) for r in DUP_GROUP):
        mt = [(r, os.path.getmtime(os.path.join(PHILOSOPHY_DIR, r))) for r in DUP_GROUP]
        keep = max(mt, key=lambda x: x[1])[0]
        skip.update(r for r in DUP_GROUP if r != keep)
        print(f"大问题: 保留 {keep}（其余跳过）", flush=True)

    entries = []
    for region in ["东方", "西方"]:
        rp = os.path.join(PHILOSOPHY_DIR, region)
        if not os.path.isdir(rp):
            continue
        # 递归扫描（2026-08-11 漏扫修复: 两人合著书区域/作者A/作者B/书 嵌套目录也要扫）
        for root, dirs, files in os.walk(rp):
            rel_root = os.path.relpath(root, rp)
            if rel_root == ".":
                continue  # region 根目录本身不放书
            author = rel_root.split(os.sep)[0]  # 顶层作者目录名（嵌套时取第一层）
            for fn in sorted(files):
                fp = os.path.join(root, fn)
                if not os.path.isfile(fp):
                    continue
                rel = os.path.relpath(fp, PHILOSOPHY_DIR).replace("\\", "/")
                if rel in skip or rel in MERGE_RULES:
                    continue
                ext = os.path.splitext(fn)[1].lower()
                if ext not in (".pdf", ".epub", ".txt"):
                    continue
                bid = hashlib.md5(rel.encode()).hexdigest()[:12]
                # rel 路径变化后映射回旧 bid（保住章节数据）, None = 副文件跳过
                rel_fix = REL_BID_FIX.get(rel)
                if rel_fix is None and rel in REL_BID_FIX:
                    continue
                if rel_fix:
                    bid = rel_fix[0]
                    author = rel_fix[1]
                demote = DEMOTE_RULES.get(rel)
                author_name = author
                if demote:
                    author_name = demote[1]
                else:
                    for sub, val in MERGE_RULES.items():
                        if not val:
                            continue  # None = 纯跳过（如理想国.pdf 副版）
                        main, merged_author = val
                        if rel == main:
                            author_name = merged_author
                            break
                entry = {
                    "id": bid,
                    "title": demote[0] if demote else os.path.splitext(fn)[0].strip(),
                    "author": author_name,
                    "region": region,
                    "file_type": "txt" if demote else ext.replace(".", ""),
                    "file_size": 0 if demote else os.path.getsize(fp),
                    "chapterCount": 0,
                    "rank": None,
                    "tags": [],
                    "cover": None,
                    "summary": "",
                }
                dp = os.path.join(DETAIL_DIR, f"{bid}.json")
                det = {}
                if os.path.exists(dp):
                    try:
                        det = json.load(open(dp, encoding="utf-8"))
                        entry["chapterCount"] = det.get("chapterCount", 0)
                        entry["tags"] = det.get("tags", [])
                        entry["cover"] = det.get("cover")
                        entry["summary"] = det.get("summary", "")
                        # author 以 detail 为准（合著/合并作者在 detail 里权威, 文件夹名只是来源）
                        if det.get("author"):
                            entry["author"] = det["author"]
                    except Exception:
                        pass
                # 书名: TITLE_FIX → detail.title（权威, 重建后为正确名）→ 文件名
                entry["title"] = TITLE_FIX.get(entry["title"]) or det.get("title") or entry["title"]
                # rank: book_rankings.json (title,author) → title → 原文件名 stem → detail
                stem = os.path.splitext(fn)[0].strip()
                entry["rank"] = _ranks.get((entry["title"], entry["author"])) or \
                    _ranks.get((stem, entry["author"])) or \
                    _ranks_title_only.get(entry["title"]) or _ranks_title_only.get(stem) or det.get("rank")
                entries.append(entry)

    # 排序: rank 降序（无 rank 排最后）; 同 rank 按 title
    entries.sort(key=lambda e: (e["rank"] is None, -(e["rank"] or 0), e["title"]))

    out = {"books": entries, "total": len(entries)}
    json.dump(entries, open(BOOKS_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(out, open(CATALOG_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    from collections import Counter
    print(f"books.json: {len(entries)} 条", flush=True)
    print("  格式:", dict(Counter(e["file_type"] for e in entries)), flush=True)

    # 同步 detail 副本 → public/book_detail（前端详情页优先读静态文件）
    if os.path.isdir(DETAIL_DIR):
        os.makedirs(PUBLIC_DETAIL_DIR, exist_ok=True)
        import shutil
        n = 0
        for fn in os.listdir(DETAIL_DIR):
            if fn.endswith(".json"):
                shutil.copy2(os.path.join(DETAIL_DIR, fn), os.path.join(PUBLIC_DETAIL_DIR, fn))
                n += 1
        print(f"public/book_detail 同步: {n} 个", flush=True)
    # 前端本地兜底副本（build 打进 bundle）
    assets = os.path.join(BASE, "app", "src", "assets", "books.json")
    if os.path.isdir(os.path.dirname(assets)):
        shutil.copy2(BOOKS_FILE, assets)
        print(f"src/assets/books.json 更新", flush=True)
    print("  有 rank:", sum(1 for e in entries if e["rank"]), flush=True)


if __name__ == "__main__":
    main()
