# -*- coding: utf-8 -*-
"""抽查21：自然辩证法（aa21ac425e87）细目 33/34 章排版修复
病因: 细目页 OCR 行合并——一段内塞多个条目（'［1］毕希纳……60［2］自然科学的辩证法……121'），
  且条目跨段断裂（段22尾'［107］两极性…' + 段23'子……85'）。
修复: 全段合并 → 按条目头切分（'［' 前切，'（\d)' 前切）→ 非条目头残渣并入前一条目 →
  每条目独立成 content 段（'［N］标题……页码' 每行一条）。
用法: python _xr_ck21_ximu.py
"""
import json, re, os, shutil

bid = "aa21ac425e87"
CHAP = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{bid}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{bid}"

def split_items(text):
    """按条目头切分。条目头 = '［' 前切 或 '（数字' 前切；非头残渣并入前一条目"""
    parts = re.split(r"(?=［|（[0-9０-９]|\([0-9])", text)
    merged = []
    for p in parts:
        if not p.strip():
            continue
        if p[0] == "［":
            # 手稿号残渣（'［164］' 纯数字 ≤6 字符，且下一 part 是新条目头 '［'）→ 并入前条目
            is_handno = re.match(r"^［\d{1,3}］$", p.strip()) is not None
            if merged and merged[-1].endswith("＿JOIN＿"):
                merged[-1] = merged[-1][:-6] + p.strip()
            elif is_handno and merged:
                merged[-1] += p.strip()
            else:
                merged.append(p.strip())
        elif p[0] in "（(" and len(p) > 1 and p[1] in "0123456789０１２３４５６７８９":
            # '（1)' 条目标记：并入下一个 part（'（1)［计划草案］……'）
            merged.append(p.strip() + "＿JOIN＿")
        elif merged:
            if merged[-1].endswith("＿JOIN＿"):
                merged[-1] = merged[-1][:-6] + p.strip()
            else:
                merged[-1] += p.strip()   # 跨段残渣（'子……85'/'119'/'……282'）并入前条目
        else:
            merged.append(p.strip())
    return [m.replace("＿JOIN＿", "") for m in merged if m.strip()]

for idx, title in ((33, "《自然辩证法》细目（按手稿写作时间编排）"),
                   (34, "《自然辩证法》细目（按手稿内容编排）")):
    p = f"{CHAP}/{idx}.json"
    c = json.load(open(p, encoding="utf-8"))
    vals = [b.get("value", "") for b in c["content"] if b.get("value", "").strip()]
    full = "".join(vals)                     # 合并修复跨段条目
    items = split_items(full)
    new_content = [{"type": "text", "value": v} for v in items]
    c["content"] = new_content
    json.dump(c, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    n = sum(len(v) for v in items)
    print(f"✓ 章{idx} {title}: {len(vals)} 段 → {len(items)} 条 ({n}字)")
    print(f"  样例: {items[0][:60]!r}")
    print(f"        {items[1][:60]!r}")

# 三处同步
for p in (f"{SRC}/{idx}.json", f"{DST2}/{idx}.json"):
    shutil.copy2(f"{CHAP}/{idx}.json", p)
print("✓ 三处同步（PhiAgent backend + DP app/public）")
