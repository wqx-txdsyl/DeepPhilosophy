# -*- coding: utf-8 -*-
import json, hashlib, os
bid = "b471f41a78de"
def h(p): return hashlib.md5(open(p, 'rb').read()).hexdigest()
for p in [f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json",
          f"f:/program/Python/PhiAgent/backend/data/book_chapters/{bid}/meta.json",
          f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{bid}/meta.json"]:
    print("meta", h(p))
d1 = json.load(open(f"f:/program/Python/PhiAgent/app/public/book_detail/{bid}.json", encoding="utf-8"))
d2 = json.load(open(f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{bid}.json", encoding="utf-8"))
print("detail cc:", d1["chapterCount"], d2["chapterCount"], "| toc:", len(d1["toc"]), len(d2["toc"]), "| equal:", d1["toc"] == d2["toc"])
books = json.load(open("f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json", encoding="utf-8"))
b = [x for x in books if str(x.get("id")) == bid][0]
print("books.json cc:", b["chapterCount"], "| == detail:", b["chapterCount"] == d1["chapterCount"])
fs = sorted(int(f[:-5]) for f in os.listdir(f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}") if f.endswith(".json") and f != "meta.json")
print("文件编号:", fs)
