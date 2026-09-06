# -*- coding: utf-8 -*-
"""MIA 三本批量构建: 爬取 JSON → 章节 JSON + meta + 镜像 + detail×2 + books.json + catalog。
按 docs/分章标准规范.md。bids: 英国工人阶级状况/狱中书简/神圣家族
"""
import re, os, json, glob, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TMP = os.path.join(os.path.dirname(os.path.abspath(__file__)))

BOOKS = [
    {
        'bid': 'e6bdf6706fda', 'title': '英国工人阶级状况', 'author': '弗里德里希·恩格斯',
        'src': os.path.join('mia_batch', 'uk_workers.json'),
        'chapters': None,  # 每信/每章一个 chapter, 标题用爬取的 title
    },
    {
        'bid': 'ee6b604ffa02', 'title': '狱中书简', 'author': '安东尼奥·葛兰西',
        'src': os.path.join('mia_batch', 'gramsci_letters.json'),
        'chapters': None,
    },
    {
        'bid': 'c309f9dd4214', 'title': '神圣家族', 'author': '卡尔·马克思/弗里德里希·恩格斯',
        'src': os.path.join('mia_batch', 'holy_family.json'),
        'chapters': [
            ('序言', '001.htm'),
            ('第一章 以订书匠的姿态出现的批判的批判或赖哈特先生所体现的批判的批判（恩格斯）', '002.htm'),
            ('第二章 体现为《缪斯》的批判的批判或茹尔·法赫尔先生所体现的批判的批判（恩格斯）', '003.htm'),
            ('第三章 “批判的批判的彻底性”或荣（荣格尼茨？）先生所体现的批判的批判（恩格斯）', '004.htm'),
            ('第四章 体现为认识的宁静的批判的批判或埃德加尔先生所体现的批判的批判（马克思）', '005.htm'),
            ('第五章 贩卖秘密的商人所体现的批判的批判或施里加先生所体现的批判的批判（马克思）', '006.htm'),
            ('第六章 绝对的批判的批判或布鲁诺先生所体现的批判的批判（马克思）', '007.htm'),
            ('第七章 批判的批判的通讯（马克思）', '008.htm'),
            ('第八章 批判的批判之周游世界和变服微行，或盖罗尔施坦公爵鲁道夫所体现的批判的批判（马克思）', '009.htm'),
            ('第九章 批判的末日的审判（马克思）', '010.htm'),
        ],
    },
]

MERGE_ENDERS = set('，、；：（“·—')
TERM = set('。！？”’…—？：')

def to_blocks(text):
    """正文 → 段落块; 句中截断的段并入下一段(章内)。"""
    paras = [p.strip() for p in text.split('\n') if p.strip()]
    merged = []
    for p in paras:
        if merged and p and (merged[-1][-1] in MERGE_ENDERS or
                             (re.match(r'[\u4e00-\u9fff]', merged[-1][-1]) and merged[-1][-1] not in TERM)):
            merged[-1] = merged[-1] + p
        else:
            merged.append(p)
    return merged

results = []
for book in BOOKS:
    bid = book['bid']
    data = json.load(open(os.path.join(TMP, book['src']), encoding='utf-8'))
    if book['chapters'] is None:
        # 每条一个 chapter
        chap_list = [(item['title'], item['text']) for item in data]
    else:
        by_file = {item['file']: item['text'] for item in data}
        chap_list = [(t, by_file[f]) for t, f in book['chapters']]

    chapters, toc, chapter_titles = [], [], []
    total = 0
    for idx, (t, text) in enumerate(chap_list):
        blocks = [{'type': 'text', 'value': p} for p in to_blocks(text)]
        chapters.append({'index': idx, 'title': t, 'content': blocks})
        chapter_titles.append(t)
        toc.append({'type': 'chapter', 'title': t, 'index': idx})
        total += sum(len(b['value']) for b in blocks)

    meta = {
        'bookId': bid, 'title': book['title'], 'author': book['author'], 'region': '西方',
        'toc': toc, 'cover': f'/covers/{bid}_cover.webp',
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles,
    }
    src_dir = os.path.join(BASE, 'backend', 'data', 'book_chapters', bid)
    if os.path.exists(src_dir):
        shutil.rmtree(src_dir)
    os.makedirs(src_dir)
    for ch in chapters:
        json.dump(ch, open(os.path.join(src_dir, f"{ch['index']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(src_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    mirror = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters', bid)
    if os.path.exists(mirror):
        shutil.rmtree(mirror)
    shutil.copytree(src_dir, mirror)

    # detail ×2: 保留壳的 cover/summary/tags, 更新章节信息, file_type→epub
    fe_detail = os.path.join(BASE, 'app', 'public', 'book_detail', f'{bid}.json')
    d = json.load(open(fe_detail, encoding='utf-8'))
    d['chapterCount'] = len(chapters)
    d['chapterTitles'] = chapter_titles
    d['toc'] = toc
    d['file_type'] = 'epub'
    for p in [fe_detail, os.path.join(BASE, 'backend', 'data', 'book_detail', f'{bid}.json')]:
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    # books.json + catalog
    size = sum(len(b['value'].encode('utf-8')) for ch in chapters for b in ch['content'])
    for path, key in [(os.path.join(BASE, 'app', 'public', 'books.json'), None),
                      (os.path.join(BASE, 'backend', 'data', 'books_catalog.json'), 'books')]:
        data2 = json.load(open(path, encoding='utf-8'))
        items = data2 if isinstance(data2, list) else data2[key]
        hit = next(it for it in items if it['id'] == bid)
        hit['chapterCount'] = len(chapters)
        hit['file_size'] = size
        hit['file_type'] = 'epub'
        json.dump(data2, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

    results.append((bid, book['title'], len(chapters), total, size))

for r in results:
    print(f'{r[0]} {r[1]}: {r[2]}章 {r[3]}字 {r[4]}B')
print('构建完成 ×', len(results))
