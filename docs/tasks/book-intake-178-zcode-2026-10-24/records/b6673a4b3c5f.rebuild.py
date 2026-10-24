# -*- coding: utf-8 -*-
"""重建《论共和国》(b6673a4b3c5f) — 卷首（译者序）+ 六卷。"""
import json
import os
import re

q = json.load(open('docs/tasks/book-intake-178-zcode-2026-10-24/queue.json'))
row = [r for r in q['rows'] if r['bookId'] == 'b6673a4b3c5f'][0]
lines = open(row['sourceCandidates'][0]['rawPath'], encoding='utf-8').read().split('\n')
d = 'backend/data/book_chapters/b6673a4b3c5f'
STARTS = [(478, '第一卷'), (4252, '第二卷'), (6904, '第三卷'), (9070, '第四卷'), (9876, '第五卷'), (10404, '第六卷')]
TAIL = len(lines)
vol_re = re.compile(r'^第\s*[一二三四五六]\s*卷$')

chapters = [('卷首（译者序）', [])] + [(t, []) for _, t in STARTS]
cur = None
cur_ch = 0


def flush():
    global cur
    if cur is not None and cur.strip():
        chapters[cur_ch][1].append(cur)
    cur = None


for i in range(0, TAIL):
    hit = None
    for ci in range(len(STARTS)):
        if i == STARTS[ci][0]:
            hit = ci + 1
            break
    if hit is not None:
        flush()
        cur_ch = hit
        chapters[cur_ch][1].append(STARTS[hit - 1][1])
        cur = None
        continue
    s = lines[i].strip()
    if not s:
        continue
    if vol_re.match(s):
        continue
    if re.fullmatch(r'\d{1,3}', s):
        continue
    if cur_ch == 0 and i < 250:
        continue
    if cur is None:
        cur = s
    else:
        cur += s
    if cur[-1] in '。！？”」；':
        flush()
flush()

os.makedirs(d, exist_ok=True)
new_titles = []
meta_toc = []
total = 0
for i, (title, blocks) in enumerate(chapters):
    content = [{'type': 'text', 'value': b} for b in blocks]
    ch = dict(index=i, title=title, paragraphMode='source', content=content)
    with open(f'{d}/{i}.json', 'w', encoding='utf-8') as f:
        json.dump(ch, f, ensure_ascii=False, indent=1)
    new_titles.append(title)
    meta_toc.append(dict(type='chapter', title=title, index=i, level=1))
    total += sum(len(b) for b in blocks)
for fn in os.listdir(d):
    if fn.endswith('.json') and fn != 'meta.json':
        stem = fn[:-5]
        if stem.isdigit() and int(stem) >= len(chapters):
            os.remove(os.path.join(d, fn))
meta = json.load(open(f'{d}/meta.json', encoding='utf-8'))
meta['chapterCount'] = len(chapters)
meta['chapterTitles'] = new_titles
meta['toc'] = meta_toc
with open(f'{d}/meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=1)
print('%d章 %d字' % (len(chapters), total))
