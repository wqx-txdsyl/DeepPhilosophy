# -*- coding: utf-8 -*-
"""
dp_verify_dual.py — 双端入库一致性校验（2026-08-07, 最高规则）
校验: ① PhiAgent data vs DP public(5173) vs DP backend(git/CDN) 三份 book_chapters 一致
      ② book_detail / books.json 元数据一致
      ③ agent 向量库覆盖（每本书有向量）
      ④ cite 可索引性: toc 每个 chapter 的 index 有块文件（编/卷 part 不可索引）
输出: 差异清单 + 通过/失败汇总
"""
import sys, io, os, json, hashlib

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE_DIR, "data", "book_chapters")
DETAIL = os.path.join(BASE_DIR, "data", "book_detail")
DP_PUBLIC = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "backend")
EMB = os.path.join(BASE_DIR, "data", "embeddings")


def file_hash(fp):
    h = hashlib.md5()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_hash(bid):
    bd = os.path.join(CH, bid)
    if not os.path.exists(bd):
        return None
    h = hashlib.md5()
    for fn in sorted(os.listdir(bd)):
        h.update(fn.encode())
        h.update(file_hash(os.path.join(bd, fn)).encode())
    return h.hexdigest()


def main():
    problems = []
    total = 0
    # 向量索引
    emb_ix = set()
    if os.path.exists(os.path.join(EMB, "index.json")):
        for e in json.load(open(os.path.join(EMB, "index.json"), encoding="utf-8")):
            emb_ix.add(e["bid"])
    else:
        problems.append("⚠ embeddings/index.json 缺失")

    for bid in sorted(os.listdir(CH)):
        mp = os.path.join(CH, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        total += 1
        meta = json.load(open(mp, encoding="utf-8"))
        title = (meta.get("title") or "")[:20]
        # ① 三份 book_chapters 一致（DP-public 下挂 backend/data; DP-backend 本身就是 backend 根）
        src_hash = dir_hash(bid)
        for name, root, sub in (("DP-public", DP_PUBLIC, os.path.join("backend", "data", "book_chapters")),
                                ("DP-backend", DP_BACKEND, os.path.join("data", "book_chapters"))):
            other = os.path.join(root, sub, bid)
            if not os.path.exists(other):
                problems.append(f"{title}: {name} book_chapters 缺失")
                continue
            h = hashlib.md5()
            for fn in sorted(os.listdir(other)):
                h.update(fn.encode())
                h.update(file_hash(os.path.join(other, fn)).encode())
            if h.hexdigest() != src_hash:
                problems.append(f"{title}: {name} book_chapters 不一致")
        # ② book_detail 一致（PhiAgent vs DP public）
        det_fp = os.path.join(DETAIL, f"{bid}.json")
        det_public = os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")
        if os.path.exists(det_fp) and os.path.exists(det_public):
            if file_hash(det_fp) != file_hash(det_public):
                problems.append(f"{title}: book_detail 不一致")
        # books.json chapterCount
        # ③ 向量覆盖
        if bid not in emb_ix:
            problems.append(f"{title}: 无向量")
        # ④ cite 可索引性: toc chapter index 有块文件
        toc = meta.get("toc") or []
        n = meta.get("chapterCount", 0)
        if toc and isinstance(toc[0], dict):
            for t in toc:
                if t.get("type") == "chapter":
                    ix = t.get("index")
                    if ix is None or ix < 0 or ix >= n or not os.path.exists(os.path.join(CH, bid, f"{ix}.json")):
                        problems.append(f"{title}: toc chapter index {ix} 无块文件")
                        break
        elif toc and len(toc) != n:
            problems.append(f"{title}: 扁平 toc {len(toc)}≠块数{n}")

    # books.json 汇总检查
    bf = os.path.join(DP_PUBLIC, "books.json")
    if os.path.exists(bf):
        books = json.load(open(bf, encoding="utf-8"))
        for b in books:
            bid = b.get("id")
            mp = os.path.join(CH, bid, "meta.json")
            if os.path.exists(mp):
                meta = json.load(open(mp, encoding="utf-8"))
                if b.get("chapterCount") != meta.get("chapterCount"):
                    problems.append(f"{meta.get('title','')[:20]}: books.json chapterCount {b.get('chapterCount')}≠meta {meta.get('chapterCount')}")

    print(f"扫描 {total} 本书, 发现 {len(problems)} 个问题:")
    for p in problems:
        print("  -", p)
    if not problems:
        print("  ✓ 全部通过")
    return problems


if __name__ == "__main__":
    main()
