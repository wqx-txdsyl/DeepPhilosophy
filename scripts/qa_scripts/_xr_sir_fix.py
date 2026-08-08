# -*- coding: utf-8 -*-
"""西利斯 f0bf62d7aa30：6 处标题独立成段修复（一次性）
拆分粘连标题为独立段落，同步 PhiAgent + DP 两份 book_chapters。
只动标题行/段拆分，不改正文错字。"""
import json, shutil, os

BID = "f0bf62d7aa30"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

def patch(fname, transform):
    p = os.path.join(SRC, fname)
    data = json.load(open(p, encoding="utf-8"))
    transform(data)
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ {fname} {data['title']}: {len(data['content'])}段")

# ── 0.json 译者导言 ──
def fix0(d):
    c = d["content"]
    # 先取值再重组（避免 insert 后索引错位）
    v0 = c[0]["value"]; v5 = c[5]["value"]; v6 = c[6]["value"]
    assert v0.startswith("译者导言1.贝克莱的《西利斯》简介"), v0[:30]
    assert v6.startswith("“西利斯）把它们再现出来。1.2《西利斯》的书名和结构"), v6[:30]
    nc = []
    nc.append({"type": "text", "value": "译者导言"})
    nc.append({"type": "text", "value": "1.贝克莱的《西利斯》简介"})
    nc.append({"type": "text", "value": v0[len("译者导言1.贝克莱的《西利斯》简介"):]})
    nc.extend(c[1:5])  # 原 p1-p4
    nc.append({"type": "text", "value": v5 + "“西利斯）把它们再现出来。"})  # p5 续跨页句
    v6r = v6[len("“西利斯）把它们再现出来。"):]
    assert v6r.startswith("1.2《西利斯》的书名和结构"), v6r[:30]
    nc.append({"type": "text", "value": "1.2《西利斯》的书名和结构"})
    nc.append({"type": "text", "value": v6r[len("1.2《西利斯》的书名和结构"):]})
    nc.extend(c[7:])
    d["content"] = nc

patch("0.json", fix0)

# ── 17.json 致T.普赖尔先生的第一封信 ──
def fix17(d):
    c = d["content"]
    v = c[0]["value"]
    # "附录致T.普赖尔先生的第一封信一对焦油水的功效以及制作与服用方法的进一步说明毫不利己..."
    assert v.startswith("附录致T.普赖尔先生的第一封信"), v[:30]
    rest = v[len("附录"):]  # part 标题已在 toc，正文删除
    # 信标题 + 副题拆两段；副题后接正文
    head_t = "致T.普赖尔先生的第一封信"
    assert rest.startswith(head_t), rest[:30]
    rest = rest[len(head_t):]
    sub = "一对焦油水的功效以及制作与服用方法的进一步说明"
    assert rest.startswith(sub), rest[:30]
    body = rest[len(sub):]
    c[0]["value"] = head_t
    c.insert(1, {"type": "text", "value": sub})
    c.insert(2, {"type": "text", "value": body})

patch("17.json", fix17)

# ── 18.json 致T.普赖尔先生的第二封信 ──
def fix18(d):
    c = d["content"]
    v = c[0]["value"]
    # "致T.普赖尔先生的第二封信?一一论焦油水的功效81你对..."
    head = "致T.普赖尔先生的第二封信——论焦油水的功效"  # "?一"→"—" 破折号修复
    assert v.startswith("致T.普赖尔先生的第二封信?一"), v[:30]
    c[0]["value"] = head
    c.insert(1, {"type": "text", "value": v[len("致T.普赖尔先生的第二封信?一"):]})

patch("18.json", fix18)

# ── 19.json 致T.普赖尔先生的第三封信 ──
def fix19(d):
    c = d["content"]
    v = c[0]["value"]
    # "致个.普赖尔的[第三封]信一论焦油水在治疗瘟疫中的用途，兼谈用蒸馏法提取的焦油酸配制的焦油水..."
    # OCR 错 "致个.普赖尔的[第三封]信" → 修正为 toc 标题（标题修复，正文不动）
    assert v.startswith("致个.普赖尔的[第三封]信一"), v[:30]
    head = "致T.普赖尔先生的第三封信——论焦油水在治疗瘟疫中的用途，兼谈用蒸馏法提取的焦油酸配制的焦油水在治疗瘟疫时是否优越于用通常的方法即将焦油和水混合起来然后予以搅拌制作而成的焦油水"
    c[0]["value"] = head
    c.insert(1, {"type": "text", "value": v[len("致个.普赖尔的[第三封]信一"):]})

patch("19.json", fix19)

# ── 20.json 致黑尔斯博士的信 ──
def fix20(d):
    c = d["content"]
    v = c[0]["value"]
    # "《西利斯》的作者致尊敬的黑尔斯博士的信?一论焦油水在治疗人类和家畜的热病中的用途先将..."
    assert v.startswith("《西利斯》的作者致尊敬的黑尔斯博士的信?一"), v[:30]
    head = "《西利斯》的作者致尊敬的黑尔斯博士的信——论焦油水在治疗人类和家畜的热病中的用途"
    c[0]["value"] = head
    c.insert(1, {"type": "text", "value": v[len("《西利斯》的作者致尊敬的黑尔斯博士的信?一"):]})

patch("20.json", fix20)

# ── 21.json 对焦油水的进一步思考 ──
def fix21(d):
    c = d["content"]
    v = c[0]["value"]
    # "对焦油水的进一步思考?既然关于焦油水的功效时常所作的许多实验..."
    assert v.startswith("对焦油水的进一步思考?"), v[:30]
    c[0]["value"] = "对焦油水的进一步思考"
    c.insert(1, {"type": "text", "value": v[len("对焦油水的进一步思考?"):]})

patch("21.json", fix21)

# ── 同步到 DP ──
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP:", DST)
