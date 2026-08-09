# -*- coding: utf-8 -*-
"""盘点全部已入库书: 块首行纯数字(页码页眉) + 圈号行首(页脚) 混入比例"""
import json, re, os

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters'
PAT_PAGE = re.compile(r'^\d{1,4}(\.\d)?$')
PAT_NOTE = re.compile(r'^[①-⑩]')

rows = []
for bid in sorted(os.listdir(CD)):
    mp = os.path.join(CD, bid, 'meta.json')
    if not os.path.exists(mp):
        continue
    try:
        m = json.load(open(mp, encoding='utf-8'))
    except Exception:
        continue
    title = m.get('title', bid)[:22]
    n_blocks = n_hdr = n_note = 0
    for c in range(m.get('chapterCount', 0)):
        cp = os.path.join(CD, bid, '%d.json' % c)
        if not os.path.exists(cp):
            continue
        try:
            ch = json.load(open(cp, encoding='utf-8'))
        except Exception:
            continue
        for blk in ch.get('content', []):
            if not isinstance(blk, dict) or 'value' not in blk:
                continue
            n_blocks += 1
            v = str(blk['value'])
            first = v.split('\n')[0].strip()
            if PAT_PAGE.match(first):
                n_hdr += 1
            for ln in v.split('\n'):
                if PAT_NOTE.match(ln.strip()):
                    n_note += 1
                    break
    if n_blocks:
        rows.append((n_hdr, n_note, n_blocks, title, bid))

rows.sort(key=lambda r: -(r[0] + r[1]))
print('共 %d 本书, %d 块' % (len(rows), sum(r[2] for r in rows)))
print('%-24s %8s %8s %8s  说明' % ('书名', '页眉块', '页脚块', '总块'))
for hdr, note, tot, title, bid in rows[:45]:
    flag = ''
    if tot and hdr / tot > 0.3:
        flag = '← 页眉大量'
    elif tot and note / tot > 0.3:
        flag = '← 页脚大量'
    print('%-24s %8d %8d %8d  %s' % (title, hdr, note, tot, flag))
