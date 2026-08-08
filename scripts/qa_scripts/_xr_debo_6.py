# -*- coding: utf-8 -*-
"""哲学的慰藉 8a451d16f1b4：补缺失第六章"困难中的慰藉"（尼采）
源 epub 有第六章（index_split_031.html 起），入库时丢失。
从源提取 031 之后全部段落组装为 10.json，更新 meta，同步 DP。"""
import zipfile, re, html as h, json, shutil, os

BID = "8a451d16f1b4"
EPUB = "F:/philosophy/西方/阿兰·德波顿/哲学的慰藉.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

z = zipfile.ZipFile(EPUB)
splits = sorted(n for n in z.namelist() if 'index_split_' in n)
i6 = splits.index("index_split_031.html")
files6 = splits[i6:]
print("第六章文件:", files6)

paras = []
for n in files6:
    t = z.read(n).decode("utf-8", "ignore")
    ps = re.findall(r"<p[^>]*>(.*?)</p>", t, re.S)
    for p in ps:
        v = re.sub(r"<[^>]+>", "", p)
        v = h.unescape(v).replace("\u00a0", " ").strip()
        v = re.sub(r"[ \t]+", " ", v)
        if v:
            paras.append({"type": "text", "value": v})

print("段落数:", len(paras))
print("首段:", paras[0]["value"][:40])
print("尾段:", paras[-1]["value"][:40])

data = {"title": "第六章　困难中的慰藉", "content": paras}
json.dump(data, open(os.path.join(SRC, "10.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)

mp = os.path.join(SRC, "meta.json")
m = json.load(open(mp, encoding="utf-8"))
m["chapterCount"] = 11
m["toc"] = m.get("toc", []) + [{"type": "chapter", "index": 10, "title": "第六章　困难中的慰藉"}]
json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("✓ meta chapterCount =", m["chapterCount"])

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP:", DST)
