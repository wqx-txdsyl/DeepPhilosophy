# -*- coding: utf-8 -*-
"""存在与虚无 (274c59617693) 分章重建 (2026-08-08)
按 PDF 目录（OCR 页 13-15）重建三级 toc: 4 part + 17 chapter + 22 section
页映射: PDF 页 = 书页码 + 15
源: dp_pdf_import_ckpt_sartre.json ocr['西方_萨特_存在与虚无.pdf']（779/779 页完成）
用法: python _rebuild_sartre.py [--write]
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
BID = "274c59617693"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
D = os.path.join(CH, BID)
CKPT = json.load(open(r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt_sartre.json", encoding="utf-8"))
PAGES = CKPT["ocr"]["西方_萨特_存在与虚无.pdf"]
NPAGE = 779

def norm(s):
    return re.sub(r"\s+", "", s or "")

def pages_range(a, b, offset=15):
    """书页 [a,b] → PDF 页列表 (每页 1 段); 前置章 offset=0 直接用 PDF 页"""
    return [PAGES[str(p + offset)].strip() for p in range(a, b + 1)]

# ══ toc 结构: (type, title, 起, 止, [sections], offset) ══
# 前置章 a/b = PDF 页(offset=0); 正文章 = 书页(offset=15)
# sections: (title, 书页起)
STRUCT = [
    ("chapter", "现代西方学术文库总序与献词", 3, 4, None, 0),   # PDF 3 总序 + 4 献词
    ("chapter", "中译本前言", 5, 10, None, 0),
    ("chapter", "中译本修订版说明", 11, 11, None, 0),
    ("chapter", "2007年中译本再版说明", 12, 12, None, 0),
    ("chapter", "导言 对存在的探索", 1, 27, [
        ("一、现象的观念", 1), ("二、存在的现象和现象的存在", 5),
        ("三、反思前的我思和感知的存在", 7), ("四、被感知物的存在", 14),
        ("五、本体论证明", 18), ("六、自在的存在", 21)], 15),
    ("part", "第一卷 虚无的问题", None, None, None, None),
    ("chapter", "第一章 否定的起源", 28, 76, [
        ("一、考问", 28), ("二、否定", 31), ("三、虚无的辩证法概念", 38),
        ("四、虚无的现象学概念", 44), ("五、虚无的起源", 50)], 15),
    ("chapter", "第二章 自欺", 77, 106, [
        ("一、自欺和说谎", 77), ("二、自欺的行为", 87), ("三、自欺的“相信”", 102)], 15),
    ("part", "第二卷 自为的存在", None, None, None, None),
    ("chapter", "第一章 自为的直接结构", 107, 144, [
        ("一、面对自我的在场", 107), ("二、自为的人为性", 114),
        ("三、自为和价值的存在", 121), ("四、自为和可能的存在", 134),
        ("五、自我和唯我性的圈子", 142)], 15),
    ("chapter", "第二章 时间性", 145, 223, [
        ("一、三维时间的现象学", 145), ("二、时间性的本体论", 175),
        ("三、原始的时间性和心理的时间性：反思", 200)], 15),
    ("chapter", "第三章 超越性", 224, 281, [
        ("一、作为自为与自在关系类型的认识", 226), ("二、作为否定的规定", 235),
        ("三、质与量、潜在性、工具性", 242), ("四、世界的时间", 263),
        ("五、认识", 277)], 15),
    ("part", "第三卷 为他", None, None, None, None),
    ("chapter", "第一章 他人的存在", 282, 376, [
        ("一、难题", 282), ("二、唯我论的障碍", 284),
        ("三、胡塞尔，黑格尔，海德格尔", 295), ("四、注视", 319)], 15),
    ("chapter", "第二章 身体", 377, 442, [
        ("一、作为自为的存在的身体：人为性", 380), ("二、为他的身体", 419),
        ("三、身体的本体论第三维", 433)], 15),
    ("chapter", "第三章 与他人的具体关系", 443, 525, [
        ("一、对待他人的第一种态度：爱、语言、受虐色情狂", 446),
        ("二、对待他人的第二种态度：冷漠、情欲、增恨、性虐待狂", 465),
        ("三、“共在”（mitsein）和“我们”", 504)], 15),
    ("part", "第四卷 拥有、作为和存在", None, None, None, None),
    ("chapter", "第一章 存在与作为：自由", 526, 674, [
        ("一、行动的首要条件便是自由", 527), ("二、自由和人为性：处境", 585),
        ("三、自由与责任", 671)], 15),
    ("chapter", "第二章 作为和拥有", 675, 744, [
        ("一、存在的精神分析法", 675), ("二、作为和拥有：占有", 696),
        ("三、论揭示了存在的性质", 726)], 15),
    ("chapter", "结论", 745, 757, [
        ("一、自在和自为：形而上学概要", 745), ("二、道德的前景", 754)], 15),
    ("chapter", "附录", 758, 762, [
        ("萨特生平、著作年表", 758), ("主要术语译名对照表（法一汉）", 760)], 15),
]

# ══ 生成 toc + 章节 ══
toc = []
chapter_index = 0
n_chapter = 0
for typ, title, a, b, secs, offset in STRUCT:
    if typ == "part":
        toc.append({"type": "part", "title": title, "level": 0, "index": chapter_index})
        continue
    if WRITE:
        paras = pages_range(a, b, offset)
        ch = {"index": chapter_index, "title": title, "content": [{"type": "text", "value": p} for p in paras]}
        json.dump(ch, open(os.path.join(D, f"{chapter_index}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    toc.append({"type": "chapter", "title": title, "index": chapter_index, "level": 1})
    if secs:
        start = a
        for st, sp in secs:
            toc.append({"type": "section", "title": st, "index": chapter_index, "sec": sp - start, "level": 2})
    chapter_index += 1
    n_chapter += 1
    print(f"  {'WRITE' if WRITE else 'DRY '} #{chapter_index-1} {title[:24]:24s} 书页{a}-{b}")

meta = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
meta["toc"] = toc
meta["chapterCount"] = n_chapter
meta["chapterTitles"] = [t["title"] for t in toc if t.get("type") == "chapter"]
print(f"\nchapter {n_chapter} 个 / part {sum(1 for t in toc if t['type']=='part')} 个 / section {sum(1 for t in toc if t['type']=='section')} 个")

if WRITE:
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ra.sync_three(BID)
    print("meta 写入 + sync_three 完成")
else:
    print("dry-run（未写入）")
