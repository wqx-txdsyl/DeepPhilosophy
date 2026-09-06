# -*- coding: utf-8 -*-
"""论法的精神 EPUB → 严格按 docs/分章标准规范.md 注入壳 eef5ec46714f。
编=part, 章=chapter(独立文件), 节=section(sec=块号)。前后置独立成章。"""
import re, os, json, shutil, zipfile
from html import unescape

EPUB = r'F:/philosophy/西方/孟德斯鸠/论法的精神.epub'
BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
BID = 'eef5ec46714f'

z = zipfile.ZipFile(EPUB)
# spine 顺序
opf = z.read('OEBPS/content.opf').decode('utf-8', errors='ignore')
spine_refs = re.findall(r'<itemref[^>]*idref="([^"]+)"', opf)
idmap = {}
for it in re.findall(r'<item[^>]*/?>', opf):
    mid = re.search(r'id="([^"]+)"', it)
    mhref = re.search(r'href="([^"]+)"', it)
    if mid and mhref:
        idmap[mid.group(1)] = mhref.group(1)
spine = [idmap[r] for r in spine_refs if r in idmap]
print('DBGX items0:', repr(re.findall(r'<item[^>]*/?>', opf)[:1]), 'idmap:', len(idmap))
import sys as _sd
# ncx: src → 标题(取每文件第一个 navLabel 作为文件级标题)
ncx = z.read('OEBPS/toc.ncx').decode('utf-8', errors='ignore')
nav_pairs = re.findall(r'<navLabel>\s*<text>([^<]+)</text>.*?content src="([^"]+)"', ncx, re.S)
file_title = {}
for t, s in nav_pairs:
    f = s.split('#')[0]
    ft = re.sub(r'\s+', ' ', unescape(t)).strip()
    if f not in file_title:
        file_title[f] = ft

def strip_tags(html):
    html = re.sub(r'<(script|style)[\s\S]*?</\1>', '', html)
    txt = re.sub(r'<[^>]+>', '\n', html)
    txt = unescape(txt)
    lines = [l.strip() for l in txt.split('\n')]
    return [l for l in lines if l]

chapters = []  # (title, text_lines)
import sys as _s
print('DBG spine:', len(spine), 'file_title:', len(file_title), file=_s.stderr)
seen_files = set()
for f in spine:
    if f in seen_files or not f:
        continue
    seen_files.add(f)
    if len(chapters) < 3 or True: pass
    try:
        html = z.read('OEBPS/' + f).decode('utf-8', errors='ignore')
    except KeyError:
        continue
    lines = strip_tags(html)
    if not lines:
        continue
    label = file_title.get(f, '')
    # 编 文件: 内部按 章 切分
    if re.match(r'^第[一二三四五六]编', label):
        # 找到章标题行索引
        idxs = [(i, l) for i, l in enumerate(lines) if re.match(r'^第[一二三四五六七八九十]+章\b', l) and len(l) < 60]
        if idxs:
            # 编前言部分(第一个章之前)
            pre = lines[:idxs[0][0]]
            if len(''.join(pre).strip()) > 100:
                chapters.append((label, pre))
            for k, (i, head) in enumerate(idxs):
                end = idxs[k + 1][0] if k + 1 < len(idxs) else len(lines)
                chapters.append((re.sub(r'\s+', '', head)[:40], lines[i:end]))
            continue
    chapters.append((label, lines))

# 清洗: 段落化 + 去连续空段
def to_paras(lines):
    paras, cur = [], ''
    for l in lines:
        s = l.strip()
        if not s:
            if cur:
                paras.append(cur); cur = ''
            continue
        cur = (cur + s) if cur else s
        # 长段按句号自然保留为整段
    if cur:
        paras.append(cur)
    return paras

# toc 三级: 编=part(内嵌章 file 拆分后 chapter), 节=section(sec=块号)
toc, chapter_titles, chapters_out = [], [], []
part_pending = None
for idx, (title, lines) in enumerate(chapters):
    paras = to_paras(lines)
    if not paras:
        continue
    is_part = re.match(r'^第[一二三四五六]编$', title)
    if is_part:
        toc.append({'type': 'part', 'title': title, 'index': len(chapters_out), 'level': 0})
        part_pending = title
        # 编标题行不单独成章 → 把编内第一章的标题带上编号
        continue
    # 章内: 节标题行 → section 锚点
    blocks, sec_entries = [], []
    for p in paras:
        m = re.match(r'^(第[一二三四五六七八九十]+节)\s*(.*)$', p)
        if m and len(p) < 40:
            sec_entries.append({'type': 'section', 'title': p[:30], 'index': len(chapters_out), 'sec': len(blocks), 'level': 2})
        blocks.append({'type': 'text', 'value': p})
    if part_pending:
        title = f'{part_pending}　{title}'
        for se in sec_entries:
            se['title'] = f'{part_pending}　{se["title"]}'
        part_pending = None
    chapters_out.append({'index': len(chapters_out), 'title': title, 'content': blocks})
    chapter_titles.append(title)
    toc.append({'type': 'chapter', 'title': title, 'index': len(chapters_out) - 1})
    toc.extend(sec_entries)

meta = {
    'bookId': BID, 'title': '论法的精神', 'author': '孟德斯鸠', 'region': '西方',
    'toc': toc, 'cover': f'/covers/{BID}_cover.webp',
    'chapterCount': len(chapters_out), 'chapterTitles': chapter_titles,
}
src_dir = os.path.join(BASE, 'backend', 'data', 'book_chapters', BID)
if os.path.exists(src_dir):
    shutil.rmtree(src_dir)
os.makedirs(src_dir)
for ch in chapters_out:
    json.dump(ch, open(os.path.join(src_dir, f"{ch['index']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(meta, open(os.path.join(src_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
mirror = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters', BID)
if os.path.exists(mirror):
    shutil.rmtree(mirror)
shutil.copytree(src_dir, mirror)
fe_detail = os.path.join(BASE, 'app', 'public', 'book_detail', f'{BID}.json')
d = json.load(open(fe_detail, encoding='utf-8'))
d['chapterCount'] = len(chapters_out)
d['chapterTitles'] = chapter_titles
d['toc'] = toc
d['file_type'] = 'epub'
for p in [fe_detail, os.path.join(BASE, 'backend', 'data', 'book_detail', f'{BID}.json')]:
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
size = sum(len(b['value'].encode('utf-8')) for ch in chapters_out for b in ch['content'])
for path, key in [(os.path.join(BASE, 'app', 'public', 'books.json'), None),
                  (os.path.join(BASE, 'backend', 'data', 'books_catalog.json'), 'books')]:
    data = json.load(open(path, encoding='utf-8'))
    items = data if isinstance(data, list) else data[key]
    hit = next(it for it in items if it['id'] == BID)
    hit['chapterCount'] = len(chapters_out)
    hit['file_size'] = size
    hit['file_type'] = 'epub'
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
total = sum(len(b['value']) for ch in chapters_out for b in ch['content'])
print(f'论法的精神注入完成: {len(chapters_out)}章 {total}字 ({size}B)')
print('章题:', ' | '.join(chapter_titles[:12]), '...')
