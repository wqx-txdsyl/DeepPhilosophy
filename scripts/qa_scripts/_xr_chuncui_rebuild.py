# -*- coding: utf-8 -*-
"""纯粹理性批判(注释本) eca1899561c4 修复（一次性，篇/章两级重建 + 标题补全）
旧数据 61 章 = 三大部平铺（先验感性论/先验逻辑/先验方法论），分析论/辩证论层级缺失。
修复:
 1) part 三层嵌套：先验感性论 / 先验逻辑(分析论[概念分析论+原理分析论]+辩证论[概念卷+推论卷+篇]) / 先验方法论(训练/法规/建筑术/历史)
 2) 标题补全: [10]第二章 论知性在判断中的逻辑功能 / [11]第三章 论纯粹的知性概念或者范畴
    / [13]第一章 论一般先验演绎的原则（按各章首块第9/10/13节标题）
 3) 标题修正: [48-51]训练四节 第一~四章→第一节~第四节 / [52-54]法规三节 第一~三章→第一节~第三节
    / [55]第三篇→第三章 建筑术 / [56]第四篇→第四章 历史
 4) 删 [0] 版权页（题词/献词保留）
正文内容不动，只改结构
用法: python _xr_chuncui_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/eca1899561c4"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/eca1899561c4"

# (原始 index, 标题, level) —— 同一 index 可挂多个（嵌套）
PARTS = [
    (6, "先验感性论", 0),
    (8, "先验逻辑", 0),
    (8, "第一部分　先验分析论", 1),
    (8, "第一卷　概念分析论", 2),
    (8, "第一篇　论发现一切纯粹知性概念的导线", 3),
    (12, "第二篇　论纯粹知性概念的演绎", 3),
    (16, "第二卷　原理分析论", 2),
    (17, "第一篇　论纯粹知性概念的图型法", 3),
    (18, "第二篇　纯粹知性的一切原理的体系", 3),
    (22, "第三篇　所有一般对象区分为现象和本体的根据", 3),
    (23, "附录　论反思概念的歧义", 3),
    (25, "第二部分　先验辩证论", 1),
    (25, "第一卷　论纯粹理性的概念", 2),
    (28, "第二卷　论纯粹理性的辩证推论", 2),
    (28, "第一篇　论纯粹理性的谬误推理", 3),
    (29, "第二篇　纯粹理性的二论背反", 3),
    (39, "第三篇　纯粹理性的理想", 3),
    (47, "附录　先验辩证论的附录", 2),
    (48, "先验方法论", 0),
    (48, "第一章　纯粹理性的训练", 1),
    (52, "第二章　纯粹理性的法规", 1),
    (55, "第三章　纯粹理性的建筑术", 1),
    (56, "第四章　纯粹理性的历史", 1),
]
# 标题补全/修正（原始 index → 新标题）
TITLES = {
    10: "第二章　论知性在判断中的逻辑功能",
    11: "第三章　论纯粹的知性概念或者范畴",
    13: "第一章　论一般先验演绎的原则",
    48: "第一节　纯粹理性在独断应用中的训练",
    49: "第二节　纯粹理性在其争辩应用方面的训练",
    50: "第三节　纯粹理性在假说方面的训练",
    51: "第四节　纯粹理性在其证明方面的训练",
    52: "第一节　论我们理性的纯粹应用的终极目的",
    53: "第二节　论作为纯粹理性终极目的之规定根据的至善理想",
    54: "第三节　论意见、知识和信念",
    55: "第三章　纯粹理性的建筑术",
    56: "第四章　纯粹理性的历史",
}
DELETE = {0}  # 版权页

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(61)]

toc = []
files = {}
ch_index = 0
n_del = 0
for i, ch in enumerate(old):
    for a, title, lv in PARTS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": lv, "index": ch_index})
    if i in DELETE:
        n_del += 1
        continue
    if i in TITLES:
        ch['title'] = TITLES[i]
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 61 → 新章 {len(files)}（删 {n_del} 版权页）| toc {len(toc)}")
for t in toc:
    if t['type'] == 'part':
        print(("  " * t['level']) + t['title'])

if '--dry' in sys.argv:
    sys.exit(0)

if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or "eca1899561c4",
    "title": old_meta.get("title") or "纯粹理性批判（注释本）",
    "author": old_meta.get("author") or "伊曼努尔·康德",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
