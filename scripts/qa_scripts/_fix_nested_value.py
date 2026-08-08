# -*- coding: utf-8 -*-
"""修复 15.json 双层嵌套 value 结构 (64056c6623ee 后记)
content: {"type":"text","value":{"type":"text","value":"正文"}} → {"type":"text","value":"正文"}
用法: python _fix_nested_value.py
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "64056c6623ee"
D = os.path.join(ra.CH, BID)
fp = os.path.join(D, "15.json")
ch = json.load(open(fp, encoding="utf-8"))

fixed = 0
for x in ch["content"]:
    v = x.get("value")
    if isinstance(v, dict):
        x["value"] = v["value"]
        fixed += 1
print(f"解包 {fixed} 段")
total = sum(len(x["value"]) for x in ch["content"])
print(f"后记总字数: {total}")
print(f"首段: {ch['content'][0]['value'][:40]!r}")
print(f"尾段: {ch['content'][-1]['value'][-40:]!r}")

json.dump(ch, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("15.json 已写回")

ra.sync_three(BID)
print("sync_three 完成")
