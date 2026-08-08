# -*- coding: utf-8 -*-
"""书签重建收尾: DP 端同步 + books.json chapterCount + ckpt books src
用法: python _bm_sync.py <bid> <chapterCount>
"""
import sys, os, shutil, json, re

sys.stdout.reconfigure(encoding="utf-8")

BID, CC = sys.argv[1], int(sys.argv[2])
SRC = os.path.join(r"f:/program/Python/PhiAgent/backend/data/book_chapters", BID)
DPC = os.path.join(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters", BID)

# 1) DP book_chapters（rename 备份 + copytree）
if os.path.isdir(DPC):
    bak = DPC + "_old"
    if not os.path.isdir(bak):
        os.rename(DPC, bak)
    print("旧 DP 目录 →", os.path.basename(bak))
shutil.copytree(SRC, DPC)
print("book_chapters → DP ✓")

# 2) book_detail（backend + app/public 两端镜像）
dd = BID + ".json"
shutil.copy(os.path.join(r"f:/program/Python/PhiAgent/backend/data/book_detail", dd),
            os.path.join(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_detail", dd))
pub_d = os.path.join(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail", dd)
if os.path.isdir(os.path.dirname(pub_d)):
    shutil.copy(os.path.join(r"f:/program/Python/PhiAgent/backend/data/book_detail", dd), pub_d)
print("book_detail → DP（backend + app/public）✓")

# 3) books.json chapterCount（两端）
for bj in [r"f:/program/Python/PhiAgent/app/public/books.json",
           r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"]:
    books = json.load(open(bj, encoding="utf-8"))
    tag = os.path.basename(os.path.dirname(os.path.dirname(bj)))
    for b in books:
        if b.get("id") == BID:
            print(f"books.json[{tag}] chapterCount: {b.get('chapterCount')} → {CC}")
            b["chapterCount"] = CC
    json.dump(books, open(bj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# 4) ckpt books src 更新（books key = 原始 rel, bid = md5(rel)[:12]）
import hashlib
ckp = r"f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
ck = json.load(open(ckp, encoding="utf-8"))
for k, v in list(ck.get("books", {}).items()):
    if hashlib.md5(k.encode()).hexdigest()[:12] == BID:
        if isinstance(v, dict):
            v["src"] = "text_layer"
        print("ckpt books src → text_layer:", k, "→", v if isinstance(v, dict) else v)
json.dump(ck, open(ckp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("全部完成")
