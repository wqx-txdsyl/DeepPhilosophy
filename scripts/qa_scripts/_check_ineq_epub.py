# -*- coding: utf-8 -*-
"""查 epub 结构: spine 序/章节标题/注释块位置"""
import sys, os, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
print("== 文件列表 ==")
for n in z.namelist():
    print(" ", n)
# 找 opf
opf = [n for n in z.namelist() if n.endswith(".opf")]
print("\n== OPF ==", opf)
if opf:
    c = z.read(opf[0]).decode("utf-8", errors="replace")
    print(c[:2000])
