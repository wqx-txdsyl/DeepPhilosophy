# -*- coding: utf-8 -*-
"""CHKLIST 38 本段内 \n 修复备注追加：按 bid 匹配行追加；未匹配列出"""
import io, json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

P = 'f:/program/Python/PhiAgent/backend/tools/CHKLIST.md'
lines = io.open(P, encoding='utf-8').read().split('\n')

NOTE = ('；2026-08-09 段内\\n病修复（_xr_nl_fix.py，全书扫描39本）：块值内源物理\\n清除'
        '（散文行断点→右半空白根因，与自然与快乐同病）；\\n\\n段落分隔拆独立块'
        '（神学大全6卷28章→2669段、7卷23章→1817段，toc纯chapter索引拆块安全）；'
        '行式块保留（诗/偈语/对排栏/索引条目，纯理批正题反题对排/南怀瑾律诗/王阳明脚注行/叔本华引诗/康德文集拉丁诗表格）；'
        '修复索引误判（4/5分数斜杠触发含/判定）；'
        '顺带对齐 detail.toc=meta.toc 9本、detail.chapterCount 11本历史不一致')

bids = ['10c315f073ef', '10e1874c2255', '274c59617693', '278a154690ce', '309de54e4392',
        '327e5a1db152', '37e1e8e2842b', '390398aff8d0', '3a23c3ec0466', '48f7bf321598',
        '4e1a78c6f009', '523a7333343f', '53d1b4ff90d2', '75efcbb151b7', '7729ccdecb0f',
        '7bb94a203c8c', '86ed11857f43', '8b12ed2d593d', '8c0c6955c793', '96df36369f8b',
        '98e830eac187', '9aea99ccb525', '9dc98919ade8', '9ed36aca09c5', 'a04933b82f3c',
        'a26240ee8f45', 'a494d6365a42', 'cd1c72bf7f81', 'd036e1e712eb', 'd0c5ade4fcbd',
        'd1a2be0b5837', 'd3f79625368c', 'd54046539e0d', 'e1fabd8e802c', 'e63a26081cb9',
        'e7c27b39a87c', 'f08c1ead3164', 'f184edd21ac7', 'f52ed83b99d9']

found, missing = [], []
for bid in bids:
    hit = None
    for i, l in enumerate(lines):
        if ('| ' + bid + ' ') in l or ('|' + bid + '|') in l:
            hit = i
            break
    if hit is not None:
        if '段内\\n病修复' not in lines[hit]:
            lines[hit] = lines[hit].rstrip() + NOTE
            found.append((bid, hit + 1))
        else:
            found.append((bid, hit + 1, '已备注'))
    else:
        missing.append(bid)

io.open(P, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
print('已追加 %d 本' % len(found))
for f in found: print('  ', f)
print('未匹配 %d 本:' % len(missing), missing)
