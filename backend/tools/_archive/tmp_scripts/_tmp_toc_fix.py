# -*- coding: utf-8 -*-
"""toc 问题书统一修复 (2026-08-09 全量验证):
  1. 康德句读 aacc867ec43c: 裁 toc 到 2 章 (去掉 13 个越界 section)
  2. 资本论 53d1b4ff90d2: 删 2 个越界 section (内容不存在)
  3. 南怀瑾 a26240ee8f45: 越界 section index 685 -> 684 (内容在 684 章附录)
  4. 维特根斯坦 c0e78ea6f80a: 补齐 23 个缺失 index 项
双端写回 (backend + public), 修复后跑 verify_book.py
"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'

def write_both(bid, m):
    for pre in (os.path.join(BASE, 'backend/data/book_chapters'),
                os.path.join(BASE, 'app/public/backend/data/book_chapters')):
        json.dump(m, open(os.path.join(pre, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def write_detail_both(bid, d):
    for pre in (os.path.join(BASE, 'backend/data/book_detail'),
                os.path.join(BASE, 'app/public/book_detail')):
        json.dump(d, open(os.path.join(pre, bid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def load_meta(bid):
    return json.load(open(os.path.join(BASE, 'backend/data/book_chapters', bid, 'meta.json'), encoding='utf-8'))

def sync_detail(bid, m):
    fp = os.path.join(BASE, 'backend/data/book_detail', bid + '.json')
    if not os.path.exists(fp):
        print('  !! detail 缺失:', bid)
        return
    d = json.load(open(fp, encoding='utf-8'))
    d['toc'] = m['toc']
    d['chapterCount'] = m['chapterCount']
    d['chapterTitles'] = m['chapterTitles']
    write_detail_both(bid, d)

# ── 1. 康德句读: 裁 toc 到 2 章 (只留 index 0/1) ──
bid = 'aacc867ec43c'
m = load_meta(bid)
n = m['chapterCount']
new_toc = [t for t in m['toc'] if isinstance(t.get('index'), int) and t['index'] < n]
print('%s %s: toc %d -> %d 项 (越界 %d 项裁掉)' % (bid, m['title'][:18], len(m['toc']), len(new_toc), len(m['toc']) - len(new_toc)))
m['toc'] = new_toc
write_both(bid, m)
sync_detail(bid, m)

# ── 2. 资本论: 删 2 个越界 section ──
bid = '53d1b4ff90d2'
m = load_meta(bid)
n = m['chapterCount']
new_toc = [t for t in m['toc'] if not (isinstance(t.get('index'), int) and t['index'] >= n)]
print('%s %s: toc %d -> %d 项 (越界 %d 项删)' % (bid, m['title'][:18], len(m['toc']), len(new_toc), len(m['toc']) - len(new_toc)))
m['toc'] = new_toc
write_both(bid, m)
sync_detail(bid, m)

# ── 3. 南怀瑾: 越界 section 改 index 684 (内容在 684 章附录) ──
bid = 'a26240ee8f45'
m = load_meta(bid)
n = m['chapterCount']
changed = 0
for t in m['toc']:
    if isinstance(t.get('index'), int) and t['index'] >= n:
        print('  %s: %s index %d -> %d' % (bid, t.get('title', '')[:16], t['index'], n - 1))
        t['index'] = n - 1
        changed += 1
print('%s %s: 修正 %d 项' % (bid, m['title'][:18], changed))
write_both(bid, m)
sync_detail(bid, m)

# ── 4. 维特根斯坦: 补齐缺失 index 项 (从章节文件标题) ──
bid = 'c0e78ea6f80a'
m = load_meta(bid)
n = m['chapterCount']
toc = m['toc']
have = {t.get('index') for t in toc if isinstance(t.get('index'), int)}
missing = sorted(set(range(n)) - have)
if missing:
    # 从章节文件读缺失标题
    D = os.path.join(BASE, 'backend/data/book_chapters', bid)
    added = 0
    for idx in missing:
        fp = os.path.join(D, '%d.json' % idx)
        if os.path.exists(fp):
            title = json.load(open(fp, encoding='utf-8')).get('title', '第%d节' % (idx + 1))
        else:
            title = '第%d节' % (idx + 1)
        toc.append({'type': 'chapter', 'title': title, 'index': idx})
        added += 1
    # 保持 index 顺序
    toc.sort(key=lambda t: t.get('index', -1))
    print('%s %s: 补 %d 项 (缺 %s)' % (bid, m['title'][:18], added, missing[:8]))
    m['toc'] = toc
    write_both(bid, m)
    sync_detail(bid, m)
else:
    print('%s %s: 无缺失' % (bid, m['title'][:18]))

print()
print('全部修复完成 — 逐个跑 verify_book.py')
