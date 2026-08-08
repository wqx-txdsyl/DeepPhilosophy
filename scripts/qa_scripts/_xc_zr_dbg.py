# -*- coding: utf-8 -*-
"""临时 debug: 复现 定位阶段 keep 集合（不写盘）"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.abspath(__file__))
ns = {"__file__": os.path.join(BASE, "_xc_zr_rebuild.py")}
src = open(os.path.join(BASE, "_xc_zr_rebuild.py"), encoding="utf-8").read()
# 只加载函数+数据部分（到 "# ── 1)" 为止）
exec(compile(src.split("# ── 1)")[0], "x", "exec"), ns)
PAGES, CHS = ns["PAGES"], ns["CHS"]
keep = {}
def mark(pg, li):
    if li >= 0:
        keep.setdefault(pg, set()).add(li)
for ch_title, pg_s, pg_e, mode, secs in CHS:
    i, j = ns["find_ch_block"](PAGES.get(str(pg_s), "").split("\n"), ch_title)
    for li in range(i, j + 1):
        mark(pg_s, li)
    for kind, sec_title, exp_pg in secs:
        hit = (-1, -1)
        for pg in range(max(pg_s, exp_pg - 2), min(pg_e, exp_pg + 3) + 1):
            lines = PAGES.get(str(pg), "").split("\n")
            if kind == "major":
                rng = ns["find_major_block"](lines, sec_title)
            else:
                li = ns["find_sec_line"](lines, sec_title)
                rng = (li, li) if li >= 0 else (-1, -1)
            if rng[0] >= 0:
                hit = (pg, rng)
                break
        if hit[0] >= 0:
            for li in range(hit[1][0], hit[1][1] + 1):
                mark(hit[0], li)
print("keep[18] =", sorted(keep.get(18, set())))
print("keep[34] =", sorted(keep.get(34, set())))
print("keep[70] =", sorted(keep.get(70, set())))
print("keep[74] =", sorted(keep.get(74, set())))
print("keep[100] =", sorted(keep.get(100, set())))
p18 = ns["clean_page"](PAGES["18"], keep.get(18, set()), "prose")
print("clean 后 p18 前 3 行:", p18.split("\n")[:3])
