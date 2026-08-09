# -*- coding: utf-8 -*-
"""抽查页137 修正后拼接（第三部分前4段）"""
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
print("===== 第三部分 前5段（尾段修正后） =====")
for i in (0, 1, 2, 3, 4):
    b = ch12["content"][i]
    v = b["value"].replace("\n", " ")
    print(f"[段{i}] {len(v)}字\n  {v[:60]}\n  …{v[-45:]}\n")
