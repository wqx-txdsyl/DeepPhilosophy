# -*- coding: utf-8 -*-
"""全库内容级扫描: 找出 ncx 错位/截断/注释混入类内容损坏
特征(不需要源即可机器判定):
  A. 章首段以 [数字] / [卢梭注X] 注释标记开头 (注释切入章首 = ncx 锚点错位典型)
  B. 章首段以 章标题 开头但后续是另一章的内容? 难判, 跳过
  C. 章尾段不以句号/感叹号/问号/省略号结尾且 <60 字 (半句截断)
  D. 章首段 = 纯标题残留(等于其他章标题)
  E. 章内段落数极少的正文章 (内容丢失)
"""
import sys, re, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
books = sorted(os.listdir(D))
bids = [b for b in books if os.path.isdir(os.path.join(D, b)) and os.path.exists(os.path.join(D, b, "meta.json"))]
print(f"共 {len(bids)} 本")

END = "。！？…；—\"”』」"
def first_block(content):
    for b in content:
        if b.get("type") == "text":
            return b["value"]
    return ""

def paras_of(content):
    return [b["value"] for b in content if b.get("type") == "text"]

susp_A, susp_C, susp_D, susp_E = [], [], [], []
for bid in bids:
    meta = json.load(open(os.path.join(D, bid, "meta.json"), encoding="utf-8"))
    title = meta.get("title", bid)
    n = meta.get("chapterCount", 0)
    titles = set()
    for t in meta.get("toc", []):
        if isinstance(t, dict) and t.get("type") == "chapter":
            titles.add(t.get("title", ""))
    for i in range(n):
        p = os.path.join(D, bid, f"{i}.json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p, encoding="utf-8"))
        content = j.get("content", [])
        ps = paras_of(content)
        if not ps:
            continue
        fb = first_block(content)
        lb = ps[-1]
        # A: 首段注释标记切入
        if re.match(r"^\[(\d+|卢梭注\d+)\]\s*[；;，]?\s*\S", fb) or re.match(r"^\[\d+\][、,]", fb):
            susp_A.append((title, i, fb[:40]))
        # C: 尾段半句截断 (无结束标点, 短)
        if not lb.endswith(tuple(END)) and len(lb) < 60 and len(ps) > 1:
            # 排除合法短尾(如落款/签章: 含日期/致/署名特征)
            susp_C.append((title, i, lb[:40]))
        # D: 首段=其他章标题(标题残留)
        if fb in titles and i != 0:
            pass  # 章首段=自身标题是正常格式, 等于其他章标题才可疑
        # E: 正文章段落极少 (<5 段且 >50 字? 短章节合法如"关于附注的说明"2段)
        if len(ps) <= 5 and sum(len(x) for x in ps) > 800:
            susp_E.append((title, i, f"段数={len(ps)} 字={sum(len(x) for x in ps)}"))

print(f"\n== A. 章首段注释标记切入: {len(susp_A)} 处 ==")
for t, i, s in susp_A[:60]:
    print(f"  [{t}] ch{i}: {s}")
print(f"\n== C. 尾段疑似半句截断: {len(susp_C)} 处 ==")
for t, i, s in susp_C[:60]:
    print(f"  [{t}] ch{i}: {s!r}")
print(f"\n== E. 段落极少的大章节: {len(susp_E)} 处 ==")
for t, i, s in susp_E[:60]:
    print(f"  [{t}] ch{i}: {s}")
