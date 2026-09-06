# -*- coding: utf-8 -*-
"""正义论 (929771a017d6) 构建: OCR 文本 → 九章 + 序言, 按分章标准注入。"""
import re, os, json, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mia_batch', 'zhengyi_ocr.txt')
BID = '929771a017d6'

t = open(SRC, encoding='utf-8').read()
L = t.split('\n')
n = len(L)

# (标题, 起行[标题行], 内容起行, 止行)
CH = [
    ('序言', 42, 44, 247),
    ('第一章　作为公平的正义', 709, 712, 2260),
    ('第二章　正义的原则', 2260, 2262, 4232),
    ('第三章　原始状态', 4232, 4234, 6546),
    ('第四章　平等的自由', 6546, 6548, 8526),
    ('第五章　分配的份额', 8526, 8528, 10828),
    ('第六章　义务和职责', 10828, 10830, 12632),
    ('第七章　作为合理性的善', 12632, 12634, 14457),
    ('第八章　正义感', 14457, 14459, 16317),
    ('第九章　正义的善', 16317, 16319, n),
]

def paras_from(a, b):
    paras, cur = [], []
    for i in range(a, min(b, n)):
        s = L[i].strip()
        if not s:
            if cur:
                paras.append(''.join(cur)); cur = []
            continue
        cur.append(s)
    if cur:
        paras.append(''.join(cur))
    # 剔页眉噪声: 行首孤立运算符/页码噪声(此书 OCR 无明显页眉, 只滤超短行)
    paras = [p for p in paras if len(p) >= 2 or re.match(r'^[①-⑳]', p)]
    return paras

chapters, toc, chapter_titles = [], [], []
for idx, (title, hl, a, b) in enumerate(CH):
    blocks = [{'type': 'text', 'value': p} for p in paras_from(a, b)]
    chapters.append({'index': idx, 'title': title, 'content': blocks})
    chapter_titles.append(title)
    toc.append({'type': 'chapter', 'title': title, 'index': idx})
    total = sum(len(bl['value']) for bl in blocks)
    print(f'{idx} {title}: {len(blocks)}段 {total}字')

meta = {
    'bookId': BID, 'title': '正义论', 'author': '约翰·罗尔斯', 'region': '西方',
    'toc': toc, 'cover': f'/covers/{BID}_cover.webp',
    'chapterCount': len(chapters), 'chapterTitles': chapter_titles,
}
src_dir = os.path.join(BASE, 'backend', 'data', 'book_chapters', BID)
if os.path.exists(src_dir):
    shutil.rmtree(src_dir)
os.makedirs(src_dir)
for ch in chapters:
    json.dump(ch, open(os.path.join(src_dir, f"{ch['index']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(meta, open(os.path.join(src_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
mirror = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters', BID)
if os.path.exists(mirror):
    shutil.rmtree(mirror)
shutil.copytree(src_dir, mirror)
fe_detail = os.path.join(BASE, 'app', 'public', 'book_detail', f'{BID}.json')
d = json.load(open(fe_detail, encoding='utf-8'))
d['chapterCount'] = len(chapters)
d['chapterTitles'] = chapter_titles
d['toc'] = toc
d['file_type'] = 'pdf'
for p in [fe_detail, os.path.join(BASE, 'backend', 'data', 'book_detail', f'{BID}.json')]:
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
size = sum(len(b['value'].encode('utf-8')) for ch in chapters for b in ch['content'])
for path, key in [(os.path.join(BASE, 'app', 'public', 'books.json'), None),
                  (os.path.join(BASE, 'backend', 'data', 'books_catalog.json'), 'books')]:
    data = json.load(open(path, encoding='utf-8'))
    items = data if isinstance(data, list) else data[key]
    hit = next(it for it in items if it['id'] == BID)
    hit['chapterCount'] = len(chapters)
    hit['file_size'] = size
    hit['file_type'] = 'pdf'
    json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'正义论注入完成: {len(chapters)}章 {size}B')
