# -*- coding: utf-8 -*-
"""第三部分全段落首尾目检"""
import sys
sys.argv = ["_xr_96df36369f8b_road_import.py", "--dry"]
class Exit(Exception): pass
_old = sys.exit
sys.exit = lambda *a: (_ for _ in ()).throw(Exit())
import importlib.util
spec = importlib.util.spec_from_file_location("imp", "f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xr_96df36369f8b_road_import.py")
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except Exit:
    pass
finally:
    sys.exit = _old
ch12 = m.chs[14]
for i, b in enumerate(ch12["content"]):
    v = b["value"].replace("\n", " ")
    print(f"[{i:2d}] {len(v):4d} | {v[:28]} … {v[-24:]}")
