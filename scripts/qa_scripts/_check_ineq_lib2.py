# -*- coding: utf-8 -*-
"""看库 9e4f98733f0b 各章首尾段"""
import sys, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = r"f:\program\Python\PhiAgent\backend\data\book_chapters\9e4f98733f0b"
for i in range(11):
    j = json.load(open(os.path.join(base, f"{i}.json"), encoding="utf-8"))
    c = j.get("content")
    # 递归取字符串
    def flat(x):
        if isinstance(x, str): return x
        if isinstance(x, list): return "\n".join(flat(v) for v in x)
        if isinstance(x, dict): return json.dumps(x, ensure_ascii=False)
        return str(x)
    s = flat(c)
    paras = [p.strip() for p in s.split("\n") if p.strip()]
    total = sum(len(p) for p in paras)
    print(f"== {i}.json 字={total} 段数={len(paras)}")
    print(f"  首: {paras[0][:70] if paras else ''!r}")
    print(f"  尾: {paras[-1][:70] if paras else ''!r}")
