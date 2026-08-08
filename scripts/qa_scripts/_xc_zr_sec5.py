# -*- coding: utf-8 -*-
"""临时: 确认 p18/p44 书信正文空行结构 + p132/p166/p208/p245/p248/p251 + 前置章标题页"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

for k in (3, 5, 8):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"=== p{k} 前4行: {ls[:4]}")

print("\n=== p18 全文（看空行结构）===")
for i, l in enumerate(pages["18"].split("\n")):
    print(f"p18 行{i}: [{l}]")

print("\n=== p44 全文（看空行结构）===")
for i, l in enumerate(pages["44"].split("\n")):
    print(f"p44 行{i}: [{l}]")

print("\n=== p132 行14-22 ===")
for i, l in enumerate([l.strip() for l in pages["132"].split("\n") if l.strip()][14:23], 14):
    print(f"p132 行{i}: {l}")

print("\n=== p248 行0-8（第六卷大节三）===")
for i, l in enumerate([l.strip() for l in pages["248"].split("\n") if l.strip()][:9]):
    print(f"p248 行{i}: {l}")

print("\n=== p245 行3-7 ===")
ls = [l.strip() for l in pages["245"].split("\n") if l.strip()]
for i, l in enumerate(ls[3:8], 3):
    print(f"p245 行{i}: {l}")

print("\n=== p251 行0-4 ===")
for i, l in enumerate([l.strip() for l in pages["251"].split("\n") if l.strip()][:5]):
    print(f"p251 行{i}: {l}")

print("\n=== p166 行20-26 ===")
ls = [l.strip() for l in pages["166"].split("\n") if l.strip()]
for i, l in enumerate(ls[20:27], 20):
    print(f"p166 行{i}: {l}")

print("\n=== p208 行0-5 ===")
for i, l in enumerate([l.strip() for l in pages["208"].split("\n") if l.strip()][:6]):
    print(f"p208 行{i}: {l}")

print("\n=== p93 行18-22（四宇宙无限）===")
ls = [l.strip() for l in pages["93"].split("\n") if l.strip()]
for i, l in enumerate(ls[18:23], 18):
    print(f"p93 行{i}: {l}")
