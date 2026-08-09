# -*- coding: utf-8 -*-
"""全库扫描：逐行拆段（行级段落、半行宽）的书——连续短碎片块检测
判定: 连续块 ≤40字、无句尾标点、非标题/脚注/编号行 → 碎片块
碎片块数 ≥ 30 且占比 ≥ 35% → 候选（诗体/对照表也可能是, 人工甄别）
"""
import json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
END = '。！？…；：”」』）】"—'
FOOT = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]')
HAN = re.compile(r'[一-鿿]')

results = []  # (bid, title, ch_index, ch_title, total, frag, ratio, maxrun, sample)

for bid in sorted(os.listdir(ROOT)):
    d = os.path.join(ROOT, bid)
    if not os.path.isdir(d):
        continue
    mf = os.path.join(d, 'meta.json')
    if not os.path.exists(mf):
        continue
    try:
        meta = json.load(open(mf, encoding='utf-8'))
    except Exception:
        continue
    title = meta.get('title', bid)
    titles_set = {meta.get('title', ''), meta.get('bookId', '')} | set(meta.get('chapterTitles', []) or [])
    for fn in sorted(os.listdir(d), key=lambda x: int(x[:-5]) if x[:-5].isdigit() else 10 ** 9):
        if not fn.endswith('.json') or fn == 'meta.json':
            continue
        try:
            ch = json.load(open(os.path.join(d, fn), encoding='utf-8'))
        except Exception:
            continue
        blocks = [b.get('value', '') for b in ch.get('content', []) if b.get('type') == 'text']
        if len(blocks) < 30:
            continue
        frag = 0
        maxrun = run = 0
        for s in blocks:
            s = s.strip()
            if not s:
                run = 0
                continue
            if (len(s) <= 40 and s not in titles_set and s[0] not in '①②③④⑤⑥⑦⑧⑨⑩'
                    and not re.match(r'^[一二三四五六七八九十百]+、', s)
                    and not re.match(r'^\d+[.．]', s)
                    and not s[-1] in END and HAN.search(s)):
                frag += 1
                run += 1
                maxrun = max(maxrun, run)
            else:
                run = 0
        if frag >= 30 and frag / len(blocks) >= 0.35:
            sample = ' || '.join(b.strip()[:24] for b in blocks[:3])
            results.append((bid, title, ch.get('index', -1), ch.get('title', fn)[:20],
                            len(blocks), frag, round(frag / len(blocks), 2), maxrun, sample))

print('候选书（碎片块≥30 且占比≥35%%）共 %d 个章节:\n' % len(results))
cur = None
for r in results:
    if r[0] != cur:
        cur = r[0]
        print('=' * 70)
        print('📕 %s  %s' % (r[0], r[1]))
    print('  章%d %-22s 块%4d 碎片%4d 占比%.2f 最长连续%4d | %s' % (r[2], r[3], r[4], r[5], r[6], r[7], r[8]))
