# -*- coding: utf-8 -*-
"""调试: 6 个问题节在定位循环中的实际命中情况"""
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts")

src = open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xr_kant_rebuild.py", encoding="utf-8").read()

# 截到 "# ── 1)" 之前（含基础工具/编号解析/噪声/定位/结构/预处理）
cut = src.index("# ── 1) 定位全部锚点")
head = src[:cut]

DBG = """
# ===== 调试注入 =====
_TARGETS = {
    "Ⅸ.知性和理性的各种立法通过判断力而联结": 247,
    "19.我们赋予鉴赏判断的那种主观必然性是有条件的": 284,
    "30.关于自然对象的审美判断的演绎不可针对我们在自然中称为崇高的东西，而只能针对美": 324,
    "Ⅶ.判断力的技术，作为某种自然技术之理念的根据": 538,
    "B.自然界的力学的崇高": 306,
    "45.美的艺术是一种当它同时显得像是自然时的艺术": 349,
}
_orig_sec = find_sec_range
def dbg_sec(lines, title, page, exp_pg):
    if title in _TARGETS:
        tbn = body_n2(title)
        print(f"== 定位[{title}] @{exp_pg} 扫描页 {page}:", flush=True)
        for i, l in enumerate(lines):
            tag = ""
            for k in range(0, 3):
                if i + k < len(lines) and body_n2(_join_skip_pg(lines, i, i + k)) == tbn:
                    tag = "  << body_n2拼接命中"
                    break
            if not tag and match_sec(l, title):
                tag = "  << match_sec命中"
            if not tag:
                hb, bb = split_head(title)
                ha, ba = split_head(l)
                if (ha is None) == (hb is None) and len(ba) >= 4 and len(ba) < len(bb) and bb.startswith(ba):
                    tag = "  << 前缀命中"
            print(f"   {page}:{i} {l[:70]!r}{tag}", flush=True)
    return _orig_sec(lines, title, page, exp_pg)
find_sec_range = dbg_sec

_orig_major = find_major_block
def dbg_major(lines, title):
    if title in _TARGETS:
        tbn = body_n2(title)
        print(f"== major定位[{title}]:", flush=True)
        for i, l in enumerate(lines):
            bn = body_n2(l)
            print(f"   {i} {l[:60]!r} bn={bn[:30]!r}{' << 命中' if bn == tbn else ''}", flush=True)
    return _orig_major(lines, title)
find_major_block = dbg_major

for ch_title, pg_s, pg_e, mode, secs in CHS:
    for kind, sec_title, exp_pg in secs:
        if sec_title not in _TARGETS:
            continue
        for pg in range(max(pg_s, exp_pg - 2), min(pg_e, exp_pg + 3) + 1):
            lines = PAGES.get(str(pg), "").split(chr(10))
            if kind == "major":
                rng = find_major_block(lines, sec_title)
                if rng[0] >= 0:
                    print(f"!! major[{sec_title}] 命中页 {pg} 行 {rng}", flush=True)
                    break
            else:
                a, b = find_sec_range(lines, sec_title, pg, exp_pg)
                if a >= 0:
                    print(f"!! sec[{sec_title}] 命中页 {pg} 行 {a}-{b-1}", flush=True)
                    break
"""
exec(head + DBG)
