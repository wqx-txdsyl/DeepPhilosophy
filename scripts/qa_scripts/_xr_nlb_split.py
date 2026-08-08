# -*- coding: utf-8 -*-
"""你的第一本哲学书 b2fbc225f414：EPUB 切分错位重切（一次性）
问题: 章节文件错位（每文件开头含上一章标题），缺第5/7/9章名义文件。
实际内容完整: 第二章尾部在 5.json、第3-7章在 6-10.json 开头带上一章标题、
10.json 内含第7-10章+译后记。
修复: 按"第X章"标题段重新切割，重编号 0-14，同步 PhiAgent + DP。"""
import json, shutil, os, re

BID = "b2fbc225f414"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

def load(f):
    return json.load(open(os.path.join(SRC, f), encoding="utf-8"))

def dump(fname, data, idx):
    data["title"] = fname
    p = os.path.join(SRC, f"{idx}.json")
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"  {idx}.json = {fname} | {len(data['content'])}段")

# 1) 第二章 = 原4.json + 原5.json 全部（5.json 实为第二章尾部"三个问题"）
c2 = load("4.json")["content"] + load("5.json")["content"]
# 2) 第三~六章 = 原6-9.json 去掉首段（上一章标题行）
c3 = load("6.json")["content"][1:]   # 去掉"第三章　他人的意识"
c4 = load("7.json")["content"][1:]   # 去掉"第四章　身—心问题"
c5 = load("8.json")["content"][1:]   # 去掉"第五章　词语的意义"
c6 = load("9.json")["content"][1:]   # 去掉"第六章　自由意志"
# 3) 第七~十章+译后记 = 原10.json 按标题段切割
c10 = load("10.json")["content"]
bounds = [0, 44, 67, 86, 102]
for i, b in enumerate(bounds):
    if 0 < i < 4:
        assert (c10[b]["value"] or "").strip().startswith("第" + "七八九十"[i] + "章"), (i, c10[b]["value"][:20])
c7 = c10[0:44]; c8 = c10[44:67]; c9 = c10[67:86]; c10a = c10[86:102]; c10b = c10[102:]

new = [
    ("扉页", load("0.json")["content"]),
    ("目录", load("1.json")["content"]),
    ("致中国读者", load("2.json")["content"]),
    ("第一章 导言", load("3.json")["content"]),
    ("第二章 外部世界是否存在？", c2),
    ("第三章 他人的意识", c3),
    ("第四章 身—心问题", c4),
    ("第五章 词语的意义", c5),
    ("第六章 自由意志", c6),
    ("第七章 对与错", c7),
    ("第八章 正义", c8),
    ("第九章 死亡", c9),
    ("第十章 人生的意义", c10a),
    ("译后记", c10b),
    ("版权页", load("11.json")["content"]),
]
# 删除旧文件（保留 meta.json）
for f in os.listdir(SRC):
    if f != "meta.json":
        os.remove(os.path.join(SRC, f))
for idx, (title, content) in enumerate(new):
    dump(title, {"title": title, "content": content}, idx)

# meta.json 更新
mp = os.path.join(SRC, "meta.json")
m = json.load(open(mp, encoding="utf-8"))
m["chapterCount"] = len(new)
m["toc"] = [{"type": "chapter", "index": i, "title": t} for i, (t, _) in enumerate(new)]
json.dump(m, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("✓ meta.json chapterCount =", m["chapterCount"])

# 同步 DP
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP:", DST)
