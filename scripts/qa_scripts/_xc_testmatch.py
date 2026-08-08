# -*- coding: utf-8 -*-
"""临时: 测试 match_line 对 608 标题行"""
import sys, re
sys.path.insert(0, r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts")
sys.stdout.reconfigure(encoding="utf-8")

from _xc_cpr_rebuild import match_line, norm2, norm

t = "第一节纯粹理性在独断运用中的训练"
l = "第-节纯粹理性在独断运用中的训练"
print("tn2:", repr(norm2(t)))
print("n2 :", repr(norm2(l)))
print("equal:", norm2(l) == norm2(t))
print("match var:", match_line(l, t, "var", None))
print("match exact:", match_line(l, t, "exact", None))
print()
print("字码:", [hex(ord(c)) for c in l[:8]])
print("标题码:", [hex(ord(c)) for c in t[:8]])
