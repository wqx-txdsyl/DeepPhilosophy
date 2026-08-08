# -*- coding: utf-8 -*-
"""检查 ckpt books 记录：哪些"未开始"书已被登记"""
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
ck = json.load(open(r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json", encoding="utf-8"))
books = ck.get("books", {})
print("books 记录数:", len(books))
srcs = {}
for k, v in books.items():
    s = v.get("src", "?") if isinstance(v, dict) else "?"
    srcs[s] = srcs.get(s, 0) + 1
print("src 分布:", srcs)
print()
probes = ["新大西岛", "语词和对象", "理想国", "精神现象学", "哲学研究", "人性论", "思想录",
          "柏拉图对话集", "极权主义", "叔本华", "存在与虚无", "论演说家", "塞涅卡", "普通语言学",
          "过程与实在", "忏悔录", "生存哲学", "性经验史", "逻辑哲学论", "快乐的科学"]
for probe in probes:
    hits = [k for k in books if probe in k]
    for k in hits:
        v = books[k]
        s = v.get("src", "?") if isinstance(v, dict) else "?"
        print("  {:<12s} {}".format(s, k))
