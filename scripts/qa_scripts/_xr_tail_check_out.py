# -*- coding: utf-8 -*-
"""抽查导入结果：第十一章段落衔接 + 第三部分访谈页分流质量"""
import json, sys
sys.path.insert(0, 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts')
# 直接 import 脚本重算（与入库逻辑一致）
import importlib.util
spec = importlib.util.spec_from_file_location("imp", "f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xr_96df36369f8b_road_import.py")
m = importlib.util.module_from_spec(spec)
import os
# 脚本顶层会读 checkpoint + 构建 chs；--dry 时退出。手动模拟：先置 sys.argv
sys.argv = ["_xr_96df36369f8b_road_import.py", "--dry"]
# dry 分支会 sys.exit，改用 exec 前替换
import types
class Exit(Exception): pass
_old_exit = sys.exit
sys.exit = lambda *a: (_ for _ in ()).throw(Exit())
try:
    spec.loader.exec_module(m)
except Exit:
    pass
finally:
    sys.exit = _old_exit
chs = m.chs
ch11 = chs[13]
ch12 = chs[14]
print("===== 第十一章 段落检查 =====")
for i, b in enumerate(ch11["content"]):
    v = b["value"].replace("\n", " ")
    print(f"[段{i}] {len(v)}字 | {v[:45]} ... {v[-25:]}")
print()
print("===== 第三部分 首3段 + 末2段 =====")
for i in (0, 1, 2, -2, -1):
    b = ch12["content"][i]
    v = b["value"].replace("\n", " ")
    print(f"[段{i}] {len(v)}字 | {v[:50]} ... {v[-30:]}")
