# -*- coding: utf-8 -*-
"""通用：按现有章题在raw中顺序定位并重建章节内容（同版缺段修复）。

用法: python rebuild_by_titles.py <bid> [--head-regex '第.+章'] [--drop-heads]
读取 backend/data/book_chapters/<bid>/meta.json 的 chapterTitles，
在 raw 中顺序查找每章标题行（页眉形态：标题+页码 也算），以首次出现为章界，
重切各章内容（保留脚注行，按终结标点收段）。
"""
import json
import os
import re
import sys

q = json.load(open('docs/tasks/book-intake-178-zcode-2026-10-24/queue.json'))
bid = sys.argv[1]
head_re = re.compile(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != '--drop-heads' else None
row = [r for r in q['rows'] if r['bookId'] == bid][0]
rawp = row['sourceCandidates'][0]['rawPath']
lines = open(rawp, encoding='utf-8').read().split('\n')
d = f'backend/data/book_chapters/{bid}'
meta = json.load(open(f'{d}/meta.json', encoding='utf-8'))
TITLES = meta['chapterTitles']


def sq(s):
    return re.sub(r'[\s　，。；：、「」『』（）〔〕］［《》〈〉…·．.-]', '', s)


starts = []
pos = 0
MIN_GAP = int(os.environ.get('MIN_GAP', '30'))
for ti, t in enumerate(TITLES):
    k = sq(t)[:8]
    floor = (starts[-1] + MIN_GAP) if starts and starts[-1] is not None else pos
    found = None
    for i in range(max(pos, floor), len(lines)):
        lsq = sq(lines[i])
        if k and k in lsq and len(lsq) < len(k) + 8:
            found = i
            break
    starts.append(found)
    if found is None:
        print('NOT FOUND:', t[:20])
    else:
        pos = found + 1
print('定位:', [(i, TITLES[i][:8]) for i, s in enumerate(starts) if s is not None][:8], '...')
tail = len(lines)
for i in range(len(lines) - 1, 0, -1):
    s = lines[i]
    if 'SOURCE NOTES' in s or 'Previous' in s or re.match(r'^\s*ISBN', s):
        tail = i
        break

total = 0
meta_toc = []
prev_ok = [s for s in starts if s is not None]
for ti, t in enumerate(TITLES):
    lo = starts[ti]
    if lo is None:
        # 未定位的章保留原内容
        ch = json.load(open(f'{d}/{ti}.json', encoding='utf-8'))
        meta_toc.append(dict(type='chapter', title=t, index=ti, level=1))
        total += sum(len(b.get('value', '')) for b in ch['content'])
        continue
    his = [s for s in starts[ti + 1:] if s is not None]
    hi = his[0] if his else tail
    blocks = []
    cur = None
    for j in range(lo, hi):
        s = lines[j].strip()
        if not s:
            continue
        if j == lo:
            blocks.append(t)
            continue
        if head_re and head_re.match(s):
            continue
        if re.fullmatch(r'\d{1,3}', sq(s)):
            continue
        if cur is None:
            cur = s
        else:
            cur += s
        if cur[-1] in '。！？”」；':
            blocks.append(cur)
            cur = None
    if cur:
        blocks.append(cur)
    ch = dict(index=ti, title=t, paragraphMode='source', content=[{'type': 'text', 'value': b} for b in blocks])
    json.dump(ch, open(f'{d}/{ti}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    meta_toc.append(dict(type='chapter', title=t, index=ti, level=1))
    total += sum(len(b) for b in blocks)
meta['toc'] = meta_toc
with open(f'{d}/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
print(f'{len(TITLES)}章重切完成 {total}字')
