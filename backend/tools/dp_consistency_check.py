# -*- coding: utf-8 -*-
"""dp_consistency_check.py — 仓库内元数据一致性校验（CI 用, 无本地依赖）

仅依赖 git 跟踪数据（GitHub Actions 可跑）:
  app/public/books.json ↔ app/src/assets/books.json ↔ app/public/book_detail/*.json
  ↔ backend/data/book_chapters/{bid}/meta.json
  backend/data/books_catalog.json（被 gitignore, 本地存在才查）

校验项:
  ① 两份 books.json 的 id 集/每条字段一致
  ② books.json ↔ book_detail: id 双向一致 + chapterCount 一致
  ③ file_type=txt ⟹ chapterCount==0
  ④ chapterCount>0 ⟹ 有 meta.json 且 chapterCount 一致
  ⑤ books_catalog.json（存在时）: total==len(books) 且 id 集与 books.json 一致

退出码: 0 全过 / 1 有问题。CI 用法: python backend/tools/dp_consistency_check.py
"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # 仓库根（CI checkout 相对路径安全）


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    problems = []
    root = BASE

    pub = load(os.path.join(root, "app", "public", "books.json"))
    assert isinstance(pub, list), "books.json 应为列表"

    # ① 两份 books.json 一致
    ast = os.path.join(root, "app", "src", "assets", "books.json")
    if os.path.exists(ast):
        ast_b = load(ast)
        pub_ids = [b["id"] for b in pub]
        ast_ids = [b["id"] for b in ast_b]
        if pub_ids != ast_ids:
            problems.append(f"assets/books.json 与 public/books.json 的 id 顺序/集合不一致 (public {len(pub_ids)} / assets {len(ast_ids)})")
        for a, b in zip(pub, ast_b):
            for k in ("title", "author", "file_type", "chapterCount"):
                if a.get(k) != b.get(k):
                    problems.append(f"assets 与 public books.json 字段不一致: {a['id']} {k} public={a.get(k)} assets={b.get(k)}")
    else:
        problems.append("app/src/assets/books.json 缺失")

    # id 唯一
    seen = set()
    for b in pub:
        if b["id"] in seen:
            problems.append(f"books.json 重复 id: {b['id']}")
        seen.add(b["id"])

    # book_detail 文件集
    det_dir = os.path.join(root, "app", "public", "book_detail")
    det_ids = set()
    if os.path.isdir(det_dir):
        det_ids = {fn[:-5] for fn in os.listdir(det_dir) if fn.endswith(".json")}
    else:
        problems.append("app/public/book_detail 缺失")

    # ② id 双向一致
    pub_ids_set = {b["id"] for b in pub}
    only_pub = sorted(pub_ids_set - det_ids)
    only_det = sorted(det_ids - pub_ids_set)
    if only_pub:
        problems.append(f"books.json 有而 book_detail 无 ({len(only_pub)}): {only_pub[:5]}{'…' if len(only_pub) > 5 else ''}")
    if only_det:
        problems.append(f"book_detail 有而 books.json 无 ({len(only_det)}): {only_det[:5]}{'…' if len(only_det) > 5 else ''}")

    # ③④ 逐本校验
    ch_root = os.path.join(root, "backend", "data", "book_chapters")
    n_meta_checked = 0
    for b in pub:
        bid = b["id"]
        detp = os.path.join(det_dir, bid + ".json")
        if os.path.exists(detp):
            det = load(detp)
            if det.get("chapterCount") != b.get("chapterCount"):
                problems.append(f"{bid} {b.get('title','')[:20]}: books.json cc={b.get('chapterCount')} ≠ detail cc={det.get('chapterCount')}")
        if b.get("file_type") == "txt" and b.get("chapterCount") != 0:
            problems.append(f"{bid} {b.get('title','')[:20]}: txt 占位 chapterCount 应为 0 (实际 {b.get('chapterCount')})")
        cc = b.get("chapterCount", 0)
        if cc > 0:
            mp = os.path.join(ch_root, bid, "meta.json")
            if not os.path.exists(mp):
                problems.append(f"{bid} {b.get('title','')[:20]}: cc={cc} 但缺 book_chapters/{bid}/meta.json")
            else:
                m = load(mp)
                if m.get("chapterCount") != cc:
                    problems.append(f"{bid} {b.get('title','')[:20]}: books.json cc={cc} ≠ meta cc={m.get('chapterCount')}")
                n_meta_checked += 1

    # ⑤ catalog（gitignored, 本地存在才查）
    catp = os.path.join(root, "backend", "data", "books_catalog.json")
    if os.path.exists(catp):
        cat = load(catp)
        cb = cat.get("books", [])
        if cat.get("total") != len(cb):
            problems.append(f"books_catalog total={cat.get('total')} ≠ books 列表 {len(cb)}")
        cids = {c["id"] for c in cb}
        if cids != pub_ids_set:
            problems.append(f"books_catalog books 与 books.json id 集不一致 (catalog {len(cids)} / books {len(pub_ids_set)})")
    # else: CI 上 gitignore 文件不存在, 跳过（本地跑才有）

    print(f"books.json {len(pub)} 条 / book_detail {len(det_ids)} 个 / 章节 meta 检查 {n_meta_checked} 本")
    if problems:
        print(f"FAIL — {len(problems)} 个问题:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("PASS — 全部一致")


if __name__ == "__main__":
    main()
