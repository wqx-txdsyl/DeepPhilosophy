# -*- coding: utf-8 -*-
"""《原型与集体无意识》（荣格/冯川·苏克等译）5dcede8a79a6 重建（一次性，ckpt ocr 页级文本）
pdf: F:/philosophy/西方/卡尔·古斯塔夫·荣格/原型与集体无意识.pdf（384 页，无文本层，OCR 已完成）
本书从 ckpt 的 ocr 键直接读页级文本重建（370/384 页成功，14 失败页待全量后补，本脚本打印缺口警告）。
旧数据 66 章 toc 全乱：页码残片当章名（"第一部分25"）、页眉残片（"第六部分219"）、空标题（"一、"）。
真实结构（目录 p5-6 + 六个部分标题页 p9/67/95/125/169/223 + 页眉页码逐页核对，ckpt 页 = 印 + 6）:
  [ch] 英译者按 p7-9（印1-3）
  [part] 第一部分（标题页 p9）
    [ch] 集体无意识的原型 p11-41（印5-35，无节）
    [ch] 集体无意识的概念 p42-51（印36-45，4 节: 一定义/二意义/三方法/四例子）
    [ch] 关于原型，特别涉及阿尼玛概念 p52-66（印46-60，无节）
  [part] 第二部分（标题页 p67）
    [ch] 母亲原型的心理学面向 p69-94（印63-88，5 节: 一~五）
  [part] 第三部分（标题页 p95）
    [ch] 关于轮回 p97-124（印91-118，3 节: 形式/心理学/典型象征）
  [part] 第四部分（标题页 p125）
    [ch] 儿童原型心理学 p127-149（印121-143，4 节: 引言/原型/现象学/结论）
    [ch] "柯尔"的心理学面向 p150-168（印144-162，1 节: 方法本身的正确性）
  [part] 第五部分（标题页 p169）
    [ch] 童话中灵魂的现象学 p171-207（印165-201，6 节: 一~六）
    [ch] 论魔法师的心理学 p208-222（印202-216，无节）
  [part] 第六部分（标题页 p223）
    [ch] 意识、无意识和个体化 p225-235（印219-229，无节）
    [ch] 个体化过程的个案研究 p236-299（印230-293，1 节: 结论）
    [ch] 关于曼茶罗符号象征 p300-358（印294-352，2 节: 结论/附录 曼茶罗）
  [ch] 参考文献 p359-384（印353-378，无节）
SKIP: p0-4 封面/CIP、p5-6 目录、p10/68/96/126/170/224 部分间空白页（失败页）
剥除: 页眉（每页首行: 数字开头=偶数页"页码+原型与集体无意识"OCR 变体 / 汉字开头≤10字+尾数字=奇数页"第X部分+页码"变体 / 标题页"第X部分"）、
      边码+页码独立行（^[JlI|]{0,3}\d{1,4}$）、垃圾子标题行（"1. #"）、章标题行（norm 命中，含 OCR 变体）、节标题行（norm 命中 SEC_MAP，含 OCR 变体）。
用法: python _xr_yuanxing_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "5dcede8a79a6"
CKPT = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OCR_KEY = '西方_卡尔_古斯塔夫_荣格_原型与集体无意识.pdf'
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 页眉（每页首行）----
HEAD_PATS = [
    re.compile(r'^\d{1,4}\s*[^，。；：！？]{0,12}$'),   # 偶数页眉: 页码+书名 OCR 变体（"36原型与基体元患识"）
    re.compile(r'^[^，。；：！？]{0,10}\d{1,3}$'),        # 奇数页眉: 第X部分/附录/参考文献+页码 变体（"基五邮分165"）
    re.compile(r'^第[一二三四五六]部分$'),               # 部分标题页首行
]
def is_head(s):
    return any(p.match(s) for p in HEAD_PATS)

def page_lines(pi):
    return [l.strip() for l in pages.get(pi, '').split('\n') if l.strip()]

# ---- 章标题（norm 命中 toc 标题，含 OCR 变体）----
CH_MAP = {
    "英译者按": "英译者按",
    "集体无意识的原型": "集体无意识的原型",
    "集体无意识的概念": "集体无意识的概念",
    "关于原型，特别涉及阿尼玛概念": "关于原型，特别涉及阿尼玛概念",
    "母亲原型的心理学面向": "母亲原型的心理学面向",
    "关于轮回": "关于轮回",
    "儿童原型心理学": "儿童原型心理学",
    "柯尔的心理学面向": "“柯尔”的心理学面向",        # p125 标题页无引号变体
    "“柯尔”的心理学面向": "“柯尔”的心理学面向",
    "童话中灵魂的现象学": "童话中灵魂的现象学",
    "论魔法师的心理学": "论魔法师的心理学",
    "意识、无意识和个体化": "意识、无意识和个体化",
    "意识、无意识和个体化”": "意识、无意识和个体化",   # p225 正文页尾引号变体
    "个体化过程的个案研究": "个体化过程的个案研究",
    "关于曼茶罗符号象征": "关于曼茶罗符号象征",
    "参考文献": "参考文献",
}

# ---- 节标题（norm 命中剥除；值 = toc 标准标题）----
SEC_MAP = {
    "一、定义": "一、定义",
    "二、集体无意识的心理学意义": "二、集体无意识的心理学意义",
    "三、证明的方法": "三、证明的方法",
    "四、一个例子": "四、一个例子",
    "一、关于原型概念": "一、关于原型概念",
    "二、母素原型": "二、母亲原型",
    "二、母亲原型": "二、母亲原型",
    "三、母隶情结": "三、母亲情结",
    "三、母亲情结": "三、母亲情结",
    "四、母亲情结的积极面向": "四、母亲情结的积极面向",
    "五、继论": "五、结论",
    "五、结论": "五、结论",
    "、轮国的形式": "一、轮回的形式",
    "一、轮回的形式": "一、轮回的形式",
    "二、轮周的心理学": "二、轮回的心理学",
    "二、轮回的心理学": "二、轮回的心理学",
    "三、阐明转变过程的一组典型象径": "三、阐明转变过程的典型象征",
    "三、阐明转变过程的典型象征": "三、阐明转变过程的典型象征",
    "一、引言": "一、引言",
    "二、儿童原型心理学": "二、儿童原型心理学",
    "三、儿童原型的特殊现象学": "三、儿童原型的特殊现象学",
    "四、结论": "四、结论",
    "方法本身的正确性": "方法本身的正确性",
    "、关于“SPIRIT”一词": "一、关于“SPIRIT”一词",
    "一、关于“SPIRIT”一词": "一、关于“SPIRIT”一词",
    "二、精神在梦中的自我表征": "二、精神在梦中的自我表征",
    "三、童语中的灵魂": "三、童话中的灵魂",
    "三、童话中的灵魂": "三、童话中的灵魂",
    "四、童话中的善形精灵符号象征": "四、童话中的兽形精灵符号象征",
    "四、童话中的兽形精灵符号象征": "四、童话中的兽形精灵符号象征",
    "五、附秉": "五、附录",
    "五、附录": "五、附录",
    "六、结论": "六、结论",
    "结论": "结论",
    "附录": "附录 曼茶罗",      # p356 附录节首行
    "曼茶罗": "附录 曼茶罗",    # p356 附录节次行
}

PAGE_NUM = re.compile(r'^[JlI|]{0,3}\d{1,4}$')      # 页码+边码（OCR 变体 J44）
JUNK_SUB = re.compile(r'^[1-9][.．]\s*[^一-龥]*$')   # "1. #" 子标题残片
GARB = re.compile(r'^(?=.*\d)[\dA-Za-z$%#&@*+\[\](),.．:：;；?？·°…~—\-_\s]{1,16}$')  # 含数字的页眉/边码残片 ≤16 字（无汉字）
SEC_REF_TITLE = "参考文献"

ck = json.load(open(CKPT, encoding='utf-8'))
pages = {int(x): t for x, t in ck['ocr'][OCR_KEY].items()}
n_fail = sum(1 for t in pages.values() if t == '__FAILED__')
print(f"ckpt 页数: {len(pages)} | 失败页: {n_fail}")

# ---- 章节表（title, part, 页区间 [sp,ep), 节标题列表） ----
CHS = [
    ("英译者按", None, 7, 9, []),
    ("集体无意识的原型", "第一部分", 11, 42, []),
    ("集体无意识的概念", "第一部分", 42, 52, [
        "一、定义", "二、集体无意识的心理学意义", "三、证明的方法", "四、一个例子"]),
    ("关于原型，特别涉及阿尼玛概念", "第一部分", 52, 67, []),
    ("母亲原型的心理学面向", "第二部分", 69, 95, [
        "一、关于原型概念", "二、母亲原型", "三、母亲情结",
        "四、母亲情结的积极面向", "五、结论"]),
    ("关于轮回", "第三部分", 97, 125, [
        "一、轮回的形式", "二、轮回的心理学", "三、阐明转变过程的典型象征"]),
    ("儿童原型心理学", "第四部分", 127, 150, [
        "一、引言", "二、儿童原型心理学", "三、儿童原型的特殊现象学", "四、结论"]),
    ("“柯尔”的心理学面向", "第四部分", 150, 169, ["方法本身的正确性"]),
    ("童话中灵魂的现象学", "第五部分", 171, 208, [
        "一、关于“SPIRIT”一词", "二、精神在梦中的自我表征", "三、童话中的灵魂",
        "四、童话中的兽形精灵符号象征", "五、附录", "六、结论"]),
    ("论魔法师的心理学", "第五部分", 208, 223, []),
    ("意识、无意识和个体化", "第六部分", 225, 236, []),
    ("个体化过程的个案研究", "第六部分", 236, 300, ["结论"]),
    ("关于曼茶罗符号象征", "第六部分", 300, 359, ["结论", "附录 曼茶罗"]),
    ("参考文献", None, 359, 385, []),
]

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
pending_part = None
for title, pt, sp, ep, secs in CHS:
    if pt and pt != pending_part:
        toc.append({"type": "part", "title": pt, "index": ch_index, "level": 0})
        pending_part = pt
    blocks = []
    junk = 0
    missing = []
    ref_ch = (title == SEC_REF_TITLE)  # 参考文献是英文书目，不做数字/符号行剥除
    for pi in range(sp, ep):
        t = pages.get(pi)
        if t == '__FAILED__' or t is None:
            missing.append(pi)
            continue
        for li, s in enumerate(page_lines(pi)):
            if li == 0 and is_head(s):
                junk += 1
                continue
            if not ref_ch:
                if PAGE_NUM.match(s):
                    junk += 1
                    continue
                if JUNK_SUB.match(s) or GARB.match(s):
                    junk += 1
                    continue
            nv = norm(s)
            if nv in CH_MAP:
                junk += 1
                continue
            if nv in SEC_MAP:
                junk += 1
                continue
            blocks.append({"type": "text", "value": s})
    if missing:
        warns.append(f"⚠ 缺失页 {title}: {missing}")
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    for si, st in enumerate(secs, 1):
        toc.append({"type": "section", "title": st, "index": ch_index, "sec": si, "level": 2})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"章节总数: {len(files)} | part: {sum(1 for t in toc if t['type']=='part')} | "
      f"section: {sum(1 for t in toc if t['type']=='section')} | 剥除: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print(w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:36]:38s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 66 章 277135）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
print("首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])

if '--dry' in sys.argv:
    n_res = 0
    for idx, ch in files.items():
        ref_ch = (ch['title'] == SEC_REF_TITLE)
        for b in ch['content']:
            v = b['value']
            nv = norm(v)
            if nv in CH_MAP or nv in SEC_MAP:
                print(f"⚠ 残留标题 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
                continue
            if ref_ch:
                continue  # 参考文献: 书目行形态自由，仅查标题
            if is_head(v) and not re.search(r'[一-鿿]', v):
                print(f"⚠ 残留页眉/短行 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
            elif PAGE_NUM.match(v) or GARB.match(v):
                print(f"⚠ 残留数字/垃圾行 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
    print(f"残留: {n_res}")
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
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "原型与集体无意识",
    "author": old_meta.get("author") or "卡尔·古斯塔夫·荣格",
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
