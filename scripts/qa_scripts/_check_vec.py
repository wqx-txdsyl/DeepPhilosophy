# -*- coding: utf-8 -*-
"""查向量库现状: index.json 条目数/尼采与哲学/重建过书目"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
# 找向量库
for root in (r"f:/program/Python/PhiAgent/backend/data", r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data", r"f:/program/Python/PhiAgent"):
    for p in (os.path.join(root, "vectors", "index.json"), os.path.join(root, "index.json")):
        if os.path.exists(p):
            print("index:", p)
            idx = json.load(open(p, encoding="utf-8"))
            print("结构:", type(idx).__name__, len(idx) if hasattr(idx, "__len__") else "?")
            if isinstance(idx, list):
                print("样例:", json.dumps(idx[:2], ensure_ascii=False)[:300])
            sys.exit(0)
print("未找到 index.json")
